# 4_simulations.py

import pandas as pd
import numpy as np
from scipy.stats import poisson
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# === 1. HELPER FUNCTIONS ===

def match_probabilities_league(home, away, attack, defense, league_avg_scored, home_advantage, max_goals=6):
    """Compute Poisson probabilities for a single match."""
    exp_home = np.exp(np.log(league_avg_scored) + np.log(attack[home]) + np.log(defense[away]) + home_advantage)
    exp_away = np.exp(np.log(league_avg_scored) + np.log(attack[away]) + np.log(defense[home]))
    p_home = poisson.pmf(range(max_goals + 1), exp_home)
    p_away = poisson.pmf(range(max_goals + 1), exp_away)

    p_win = p_draw = p_loss = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob = p_home[i] * p_away[j]
            if i > j:
                p_win += prob
            elif i == j:
                p_draw += prob
            else:
                p_loss += prob
    return p_win, p_draw, p_loss

# === 2. SIMULATION FUNCTIONS ===

def simulate_once(fixtures, table):
    """Simulate remaining fixtures once."""
    table_sim = table.copy()
    points = dict(zip(table_sim["team"], table_sim["pts"]))

    for _, row in fixtures.iterrows():
        home = row["homeTeam"]
        away = row["awayTeam"]
        probs = [row["p_home_final"], row["p_draw_final"], row["p_away_final"]]
        outcome = np.random.choice(["H", "D", "A"], p=probs)

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

def run_simulations(fixtures, table, n_sim=10000):
    """Run multiple simulations and return position counts and percentage tables."""
    position_counts = {team: np.zeros(len(table)) for team in table["team"]}

    for i in range(n_sim):
        final_table = simulate_once(fixtures, table)
        for _, row in final_table.iterrows():
            position_counts[row["team"]][row["position"]-1] += 1
        if (i+1) % 1000 == 0:
            print(f"{i+1}/{n_sim} simulations done...")

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

def simulate_leagues(leagues, df_simulation_all, tables_all, n_sim=10000, top_n=None):
    """Run league simulations and return raw counts, percentages, and styled tables (optionally top N)."""
    position_distribution_all = {}
    position_distribution_pct_all = {}
    styled_position_pct_all = {}

    for league in leagues:
        print(f"\n=== {league.replace('_', ' ').title()} ===")
        fixtures = df_simulation_all[league].copy()
        table = tables_all[league].copy()

        pos_counts, pos_pct = run_simulations(fixtures, table, n_sim)
        position_distribution_all[league] = pos_counts
        position_distribution_pct_all[league] = pos_pct

        # Slice top N positions if requested
        pos_pct_to_style = pos_pct.head(top_n) if top_n else pos_pct
        styled_position_pct_all[league] = style_position_table(pos_pct_to_style, table)

        print(f"Finished simulations for {league} ✅")

    return position_distribution_all, position_distribution_pct_all, styled_position_pct_all

# === 5. USAGE EXAMPLE ===

#if __name__ == "__main__":
    leagues = [
        "premierleague_england",
        "seriea_italy",
        "laliga_spain",
        "bundesliga_germany",
        "ligue1_france",
        "seriea_brazil"
    ]
    # tables_all should be a dict: league_name → table dataframe with 'team', 'pts', 'gd', 'gp'
    tables_all = {league: globals()[league] for league in leagues}

    # Run simulations and display top 3 positions only
    position_distribution_all, position_distribution_pct_all, styled_position_pct_all = simulate_leagues(
        leagues, df_simulation_all, tables_all, n_sim=1000, top_n=3
    )

    # Display top 3 for Premier League
    display(styled_position_pct_all["premierleague_england"])