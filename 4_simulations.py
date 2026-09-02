# 4_simulations.py

import os
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
    hasn't listed yet) otherwise reaches simulate_once's points dict and
    crashes the whole run with a KeyError. Warn and skip rather than fail.
    """
    known = set(table["team"])
    mask = fixtures["homeTeam"].isin(known) & fixtures["awayTeam"].isin(known)
    dropped = fixtures.loc[~mask]
    if len(dropped):
        unknown = sorted(set(dropped["homeTeam"]) | set(dropped["awayTeam"]) - known)
        print(f"⚠️ Dropping {len(dropped)} fixture(s) with unrecognized team name(s) {unknown} -- check mappings")
    return fixtures.loc[mask].copy()


def simulate_once(fixtures, table, ratings=None, rng=None):
    """Simulate remaining fixtures once.

    `ratings` (optional): the {"attack", "defense", "league_avg", "home_adv",
    "low_trust_teams"} bundle from 3_probabilities.py's compute_final_probabilities.
    When given, any fixture involving a team still short on current-season
    data gets ONE fresh, noisy draw of that team's rating for this whole
    simulated season (every match it plays in this draw uses the same
    perturbation, not a new one per match) instead of the fixed, pre-blended
    probability everyone else uses. A first attempt perturbed each match's
    probability independently and it did nothing -- the noise just averaged
    out over a full season. It has to be correlated across a team's whole
    season to actually widen the simulated outcome, which is the point:
    the fixed probability is not wrong on average, it's just false certainty
    for any one team in any one simulated season."""
    table_sim = table.copy()
    points = dict(zip(table_sim["team"], table_sim["pts"]))
    rng = rng or np.random

    noisy_attack, noisy_defense = None, None
    low_trust_teams = ratings["low_trust_teams"] if ratings else set()
    if low_trust_teams:
        noisy_attack = ratings["attack"].copy()
        noisy_defense = ratings["defense"].copy()
        for t in low_trust_teams:
            if t not in noisy_attack.index:
                continue
            shrink = float(ratings["shrink_per_team"].get(t, 0.1))
            spread = (1 - shrink) * 0.35
            noisy_attack[t] = ratings["attack"][t] * rng.lognormal(0, spread)
            noisy_defense[t] = ratings["defense"][t] * rng.lognormal(0, spread)

    cache = {}
    for _, row in fixtures.iterrows():
        home = row["homeTeam"]
        away = row["awayTeam"]

        if low_trust_teams and (home in low_trust_teams or away in low_trust_teams):
            key = (home, away)
            if key not in cache:
                try:
                    cache[key] = match_probabilities_league(
                        home, away, noisy_attack, noisy_defense, ratings["league_avg"], ratings["home_adv"]
                    )
                except KeyError:
                    cache[key] = None  # one side has no rating at all yet (0 matches played) -- fall back below
            cached = cache[key]
            probs = np.array(cached) if cached is not None else np.array(
                [row["p_home_final"], row["p_draw_final"], row["p_away_final"]]
            )
            probs = probs / probs.sum()
        else:
            probs = [row["p_home_final"], row["p_draw_final"], row["p_away_final"]]

        outcome = rng.choice(["H", "D", "A"], p=probs)

        if outcome == "H":
            points[home] += 3
        elif outcome == "D":
            points[home] += 1
            points[away] += 1
        else:
            points[away] += 3

    table_sim["pts"] = table_sim["team"].map(points)
    table_sim = table_sim.sort_values(["pts", "gd"], ascending=[False, False])
    table_sim["position"] = np.arange(1, len(table_sim)+1)
    return table_sim

def run_simulations(fixtures, table, n_sim=10000, league_name=None, ratings=None):
    """Run multiple simulations and return position counts and percentage tables."""
    position_counts = {team: np.zeros(len(table)) for team in table["team"]}
    label = f"{league_name}: " if league_name else ""
    rng = np.random.default_rng()

    for i in range(n_sim):
        final_table = simulate_once(fixtures, table, ratings=ratings, rng=rng)
        for _, row in final_table.iterrows():
            position_counts[row["team"]][row["position"]-1] += 1
        if (i+1) % 1000 == 0:
            print(f"{label}{i+1}/{n_sim} simulations done...")

    pos_df = pd.DataFrame(position_counts, index=np.arange(1, len(table)+1))
    pos_df_pct = pos_df.T.div(pos_df.T.sum(axis=1), axis=0) * 100
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
    max_workers = min(len(leagues), os.cpu_count() or 1)
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