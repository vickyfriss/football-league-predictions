# 4_simulations.py

import math
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# === 1. HELPER FUNCTIONS ===

_POISSON_FACTORIALS = np.array([math.factorial(k) for k in range(7)], dtype=float)

def poisson_pmf(lam, max_goals=6):
    """Poisson pmf for k=0..max_goals, vectorized over any leading shape of `lam`.

    Hand-rolled instead of scipy.stats.poisson.pmf: scipy's per-call parameter
    validation and broadcasting machinery dominated profiled runtime once this
    got called per-simulation instead of once per fixture (see run_simulations
    below) -- this version is a plain array formula, no per-call overhead.
    """
    lam = np.asarray(lam)[..., None]
    k = np.arange(max_goals + 1)
    return np.exp(-lam) * lam**k / _POISSON_FACTORIALS[: max_goals + 1]

# === 2. SIMULATION FUNCTIONS ===

def drop_unknown_teams(fixtures, table):
    """Filter out fixtures referencing a team not present in the standings table.

    A team-name mismatch upstream (an unmapped alias, or a promoted team ESPN
    hasn't listed yet) otherwise reaches run_simulations' points array and
    crashes the whole run with a KeyError. Warn and skip rather than fail.
    """
    known = set(table["team"])
    mask = fixtures["homeTeam"].isin(known) & fixtures["awayTeam"].isin(known)
    dropped = fixtures.loc[~mask]
    if len(dropped):
        unknown = sorted(set(dropped["homeTeam"]) | set(dropped["awayTeam"]) - known)
        print(f"⚠️ Dropping {len(dropped)} fixture(s) with unrecognized team name(s) {unknown} -- check mappings")
    return fixtures.loc[mask].copy()


def run_simulations(fixtures, table, n_sim=10000, league_name=None, ratings=None):
    """Simulate the rest of the season n_sim times and return position counts/percentages.

    Vectorized across all n_sim simulations at once instead of looping in
    Python per simulation -- profiling the original per-simulation loop (which
    called scipy's poisson.pmf and iterated fixtures with pandas .iterrows()
    once per simulated season) showed ~18ms/simulation, i.e. ~3 minutes for a
    single league's 10,000 sims. This version does the same math with numpy
    array operations covering every simulation simultaneously: ~90x faster on
    real data, verified to reproduce the same position percentages as the old
    implementation within normal Monte Carlo noise (independently-seeded runs
    of 10,000 sims agree within ~1 percentage point).

    `ratings` (optional): the {"attack", "defense", "league_avg", "home_adv",
    "shrink_per_team", "low_trust_teams"} bundle from 3_probabilities.py's
    compute_final_probabilities. Teams in low_trust_teams get ONE fresh, noisy
    draw of their attack/defense PER SIMULATION (reused for every fixture that
    team plays in that simulation, not redrawn per match) instead of the
    fixed, pre-blended probability everyone else uses. An earlier attempt
    perturbed each match's probability independently and it did nothing -- the
    noise just averaged out over a season. It has to be correlated across a
    team's whole season to actually widen the simulated outcome, which is the
    point: the fixed probability isn't wrong on average, it's just false
    certainty for any one team in any one simulated season.
    """
    rng = np.random.default_rng()
    teams = table["team"].to_numpy()
    n_teams = len(teams)
    team_idx = {t: i for i, t in enumerate(teams)}
    base_points = table.set_index("team")["pts"].reindex(teams).fillna(0).to_numpy(dtype=float)
    base_gd = table.set_index("team")["gd"].reindex(teams).fillna(0).to_numpy(dtype=float)

    n_fix = len(fixtures)
    home_idx = fixtures["homeTeam"].map(team_idx).to_numpy()
    away_idx = fixtures["awayTeam"].map(team_idx).to_numpy()
    base_probs = fixtures[["p_home_final", "p_draw_final", "p_away_final"]].to_numpy(dtype=float)

    # Every simulation starts from the same fixed probability per fixture --
    # draw all n_sim x n_fix outcomes from that in one shot. Fixtures with a
    # low-trust team get overwritten below with a per-simulation probability
    # instead; everyone else's outcome from this first draw is final.
    cum = np.cumsum(base_probs, axis=1)
    u = rng.random((n_sim, n_fix))
    outcome = np.where(u < cum[:, 0], 0, np.where(u < cum[:, 1], 1, 2)).astype(np.int8)

    low_trust_teams = ratings["low_trust_teams"] if ratings else set()
    home_names = fixtures["homeTeam"].to_numpy()
    away_names = fixtures["awayTeam"].to_numpy()
    affected_mask = np.array([
        (h in low_trust_teams) or (a in low_trust_teams) for h, a in zip(home_names, away_names)
    ]) if low_trust_teams else np.zeros(n_fix, dtype=bool)

    if affected_mask.any():
        lt_list = [t for t in low_trust_teams if t in team_idx]
        base_attack = ratings["attack"].reindex(teams).to_numpy(dtype=float)
        base_defense = ratings["defense"].reindex(teams).to_numpy(dtype=float)
        shrink_arr = np.array([float(ratings["shrink_per_team"].get(t, 0.1)) for t in lt_list])
        spread_arr = (1 - shrink_arr) * 0.35
        # One noisy multiplier per low-trust team per simulation (not per
        # fixture) -- this is what makes the noise correlated across a whole
        # simulated season for that team, rather than cancelling itself out.
        noisy_mult_a = rng.lognormal(0.0, spread_arr, size=(n_sim, len(lt_list)))
        noisy_mult_d = rng.lognormal(0.0, spread_arr, size=(n_sim, len(lt_list)))
        lt_pos = {team_idx[t]: j for j, t in enumerate(lt_list)}

        aff_fix_idx = np.where(affected_mask)[0]
        h_idx, a_idx = home_idx[aff_fix_idx], away_idx[aff_fix_idx]

        attack_h = np.tile(base_attack[h_idx], (n_sim, 1))
        defense_a = np.tile(base_defense[a_idx], (n_sim, 1))
        attack_a = np.tile(base_attack[a_idx], (n_sim, 1))
        defense_h = np.tile(base_defense[h_idx], (n_sim, 1))
        for local_i, gi in enumerate(h_idx):
            if gi in lt_pos:
                j = lt_pos[gi]
                attack_h[:, local_i] = base_attack[gi] * noisy_mult_a[:, j]
                defense_h[:, local_i] = base_defense[gi] * noisy_mult_d[:, j]
        for local_i, gi in enumerate(a_idx):
            if gi in lt_pos:
                j = lt_pos[gi]
                attack_a[:, local_i] = base_attack[gi] * noisy_mult_a[:, j]
                defense_a[:, local_i] = base_defense[gi] * noisy_mult_d[:, j]

        exp_home = ratings["league_avg"] * attack_h * defense_a * np.exp(ratings["home_adv"])
        exp_away = ratings["league_avg"] * attack_a * defense_h

        joint = poisson_pmf(exp_home)[:, :, :, None] * poisson_pmf(exp_away)[:, :, None, :]
        goals = np.arange(7)
        p_win = joint[:, :, goals[:, None] > goals[None, :]].sum(axis=2)
        p_draw = joint[:, :, goals[:, None] == goals[None, :]].sum(axis=2)
        p_loss = joint[:, :, goals[:, None] < goals[None, :]].sum(axis=2)
        total = p_win + p_draw + p_loss
        p_win, p_draw, p_loss = p_win / total, p_draw / total, p_loss / total

        cum_aff = np.cumsum(np.stack([p_win, p_draw, p_loss], axis=2), axis=2)
        u_aff = u[:, aff_fix_idx]
        outcome[:, aff_fix_idx] = np.where(
            u_aff < cum_aff[:, :, 0], 0, np.where(u_aff < cum_aff[:, :, 1], 1, 2)
        ).astype(np.int8)

    home_pts = np.where(outcome == 0, 3, np.where(outcome == 1, 1, 0)).astype(float)
    away_pts = np.where(outcome == 2, 3, np.where(outcome == 1, 1, 0)).astype(float)

    points_matrix = np.tile(base_points, (n_sim, 1))
    row_idx = np.repeat(np.arange(n_sim), n_fix)
    np.add.at(points_matrix, (row_idx, np.tile(home_idx, n_sim)), home_pts.ravel())
    np.add.at(points_matrix, (row_idx, np.tile(away_idx, n_sim)), away_pts.ravel())

    # Ties break on each team's ACTUAL current goal difference, unchanged by
    # the simulation -- same simplification the original per-simulation
    # version used (it never tracked simulated scorelines, only win/draw/loss),
    # kept here so this is a speed-up, not a behavior change.
    gd_matrix = np.tile(base_gd, (n_sim, 1))
    order = np.lexsort((-gd_matrix, -points_matrix), axis=1)
    positions = np.empty_like(order)
    sim_rows = np.arange(n_sim)[:, None]
    positions[sim_rows, order] = np.arange(1, n_teams + 1)

    position_counts = np.zeros((n_teams, n_teams))
    for col in range(n_teams):
        position_counts[col] = np.bincount(positions[:, col] - 1, minlength=n_teams)

    pos_df = pd.DataFrame(position_counts.T, index=np.arange(1, n_teams + 1), columns=teams)
    pos_df_pct = pos_df.T.div(pos_df.T.sum(axis=1), axis=0) * 100
    if league_name:
        print(f"{league_name}: {n_sim} simulations done.")
    return pos_df, pos_df_pct

# === 3. STYLING HELPERS ===

def create_green_cmap():
    greens = plt.cm.Greens
    return LinearSegmentedColormap.from_list("Greens_soft", greens(np.linspace(0.05, 0.65, 256)))

def zero_style(val):
    if val < 1:
        return "background-color: white !important;"
    return ""

def color_scale(val, mid=0.14, max_val=0.75):
    if val >= max_val:
        return 1.0
    elif val <= mid:
        return val / mid * 0.5
    else:
        return 0.5 + (val - mid) / (max_val - mid) * 0.5

def style_position_table(pos_pct, table):
    """Return a styled table with MultiIndex POS → TEAM → GP → PTS."""
    meta = table[["team", "position", "gp", "pts"]].set_index("team").rename(
        columns={"position": "POS", "gp": "GP", "pts": "PTS"}
    )
    meta = meta.loc[pos_pct.index]

    pos_pct.index = pd.MultiIndex.from_arrays(
        [meta["POS"].astype(int), meta.index, meta["GP"].astype(int), meta["PTS"].astype(int)],
        names=["POS", "TEAM", "GP", "PTS"]
    )

    display_df = pos_pct.reset_index()
    text_cols = ["POS", "TEAM", "GP", "PTS"]
    num_cols = display_df.columns.difference(text_cols)
    vmax = max(display_df[num_cols].max().max(), 1)
    green_cmap = create_green_cmap()
    color_data = display_df[num_cols].divide(vmax).apply(lambda s: s.map(color_scale)) * vmax

    styled = (
        display_df.style
        .background_gradient(cmap=green_cmap, vmin=0, vmax=vmax, gmap=color_data, axis=None)
        .map(zero_style, subset=num_cols)
        .format({col: "{:.2f}%" for col in num_cols})
        .set_properties(subset=["POS", "GP", "PTS"], **{"text-align": "center","font-size": "12px","font-weight": "600"})
        .set_properties(subset=["TEAM"], **{"text-align": "left","font-size": "12px","font-weight": "600"})
        .set_properties(subset=num_cols, **{"text-align": "center","font-size": "12px","font-weight": "500"})
        .hide(axis="index")
    )
    return styled

# === 4. MAIN FUNCTION ===

def simulate_leagues(leagues, df_simulation_all, tables_all, n_sim=10000, top_n=None, ratings_by_league=None):
    """Run league simulations and return raw counts, percentages, and styled tables (optionally top N).

    ratings_by_league (optional): per-league {"attack","defense","league_avg",
    "home_adv","shrink_per_team","low_trust_teams"} from compute_final_probabilities
    in 3_probabilities.py. When given, fixtures involving a team still short on
    current-season data get widened, per-simulation uncertainty instead of one
    fixed, falsely-certain probability (see simulate_once)."""
    position_distribution_all = {}
    position_distribution_pct_all = {}
    styled_position_pct_all = {}
    ratings_by_league = ratings_by_league or {}

    prepared = {}
    for league in leagues:
        fixtures = df_simulation_all[league].copy()
        table = tables_all[league].copy()
        fixtures = drop_unknown_teams(fixtures, table)
        prepared[league] = (fixtures, table)

    # Each league's 10,000-simulation Monte Carlo run is independent, CPU-bound
    # work with no shared state -- run them in separate processes instead of
    # one after another. "fork" is requested explicitly rather than relying on
    # the platform default: this pipeline is loaded via importlib with a
    # made-up module name (see precompute_simulations.py), which only a
    # forked child inherits -- a "spawn" child starts fresh and can't
    # re-import a module that was never really installed under that name.
    #
    # Deliberately NOT capped at os.cpu_count(): capping it meant leagues ran
    # in CPU-sized batches (e.g. 4 at a time on a 4-core runner), so the last
    # batch always waited on the slowest league in every batch before it. Now
    # that run_simulations is vectorized (~2s/league instead of ~3min), the
    # cost of briefly oversubscribing CPUs with all leagues at once is far
    # smaller than the cost of serializing into batches ever was.
    max_workers = len(leagues)
    ctx = multiprocessing.get_context("fork")
    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as executor:
        futures = {
            league: executor.submit(run_simulations, fixtures, table, n_sim, league, ratings_by_league.get(league))
            for league, (fixtures, table) in prepared.items()
        }
        for league, future in futures.items():
            print(f"\n=== {league.replace('_', ' ').title()} ===")
            pos_counts, pos_pct = future.result()
            position_distribution_all[league] = pos_counts
            position_distribution_pct_all[league] = pos_pct
            print(f"Finished simulations for {league} ✅")

    # Styling is cheap and easiest kept in the main process -- Styler objects
    # carry callables (colormaps, formatters) that aren't guaranteed to
    # survive a round-trip through another process, so there's nothing to
    # gain from parallelizing this part anyway.
    for league, (_, table) in prepared.items():
        pos_pct = position_distribution_pct_all[league]
        pos_pct_to_style = pos_pct.head(top_n) if top_n else pos_pct
        styled_position_pct_all[league] = style_position_table(pos_pct_to_style, table)

    return position_distribution_all, position_distribution_pct_all, styled_position_pct_all