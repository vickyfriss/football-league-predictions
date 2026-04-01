# 3_probabilities.py

import pandas as pd
import numpy as np
from scipy.stats import poisson

# === 1. HELPERS ===

def normalize_columns(df, kind="fixtures"):
    """Ensure home/away columns exist and are standardized."""
    df = df.copy()
    if df.empty:
        if kind == "fixtures":
            df["homeTeam"], df["awayTeam"] = pd.Series(dtype=str), pd.Series(dtype=str)
        else:  # odds
            df["home_team"], df["away_team"] = pd.Series(dtype=str), pd.Series(dtype=str)
        return df

    if {"home_team", "away_team"}.issubset(df.columns):
        df = df.rename(columns={"home_team": "homeTeam", "away_team": "awayTeam"})
    elif not {"homeTeam", "awayTeam"}.issubset(df.columns):
        df["homeTeam"] = df.get("homeTeam", pd.Series(["Unknown"]*len(df)))
        df["awayTeam"] = df.get("awayTeam", pd.Series(["Unknown"]*len(df)))
    return df

def extract_teams(df):
    return set(df["homeTeam"]).union(set(df["awayTeam"]))

def filter_current_season(df, season_start=pd.Timestamp("2025-08-01")):
    df = df.copy()
    if "utcDate" in df.columns:
        df["utcDate"] = pd.to_datetime(df["utcDate"], errors='coerce', utc=True).dt.tz_localize(None)
        return df[df["utcDate"] >= season_start]
    return df

def match_probabilities_league(home, away, attack, defense, league_avg, home_adv, max_goals=6):
    exp_home = np.exp(np.log(league_avg) + np.log(attack.get(home, 1.0)) + np.log(defense.get(away, 1.0)) + home_adv)
    exp_away = np.exp(np.log(league_avg) + np.log(attack.get(away, 1.0)) + np.log(defense.get(home, 1.0)))
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

# === 2. MAIN FUNCTION ===

def compute_final_probabilities(leagues, past_matches_dict, fixtures_dict, betting_odds_dict):
    df_final_all = {}
    home_adv_by_league = {}

    for league in leagues:
        df_all = past_matches_dict[league].copy()
        if "utcDate" in df_all.columns:
            df_all["utcDate"] = pd.to_datetime(df_all["utcDate"], errors='coerce', utc=True).dt.tz_localize(None)
            df_all = df_all.sort_values("utcDate").reset_index(drop=True)
        df_all["weight"] = np.linspace(1, 2, len(df_all)) if len(df_all) > 0 else 1
        past_matches_dict[league + "_weighted"] = df_all

        # Home advantage
        home_adv = (df_all.get("homeGoals", pd.Series([0])) - df_all.get("awayGoals", pd.Series([0]))).mean()
        home_adv_by_league[league] = home_adv

        # Team attack/defense
        df_all = normalize_columns(df_all)
        teams = pd.unique(df_all[["homeTeam", "awayTeam"]].values.ravel("K")) if not df_all.empty else []
        attack = pd.Series(1.0, index=teams)
        defense = pd.Series(1.0, index=teams)
        team_stats = {}

        for team in teams:
            home_games = df_all[df_all["homeTeam"] == team]
            away_games = df_all[df_all["awayTeam"] == team]
            home_goals = home_games.get("homeGoals", pd.Series([0]*len(home_games)))
            away_goals = away_games.get("awayGoals", pd.Series([0]*len(away_games)))
            home_weight = home_games.get("weight", pd.Series([1]*len(home_games)))
            away_weight = away_games.get("weight", pd.Series([1]*len(away_games)))

            goals_scored = (home_goals * home_weight).sum() + (away_goals * away_weight).sum()
            goals_against = (home_games.get("awayGoals", pd.Series([0]*len(home_games))) * home_weight).sum() + \
                            (away_games.get("homeGoals", pd.Series([0]*len(away_games))) * away_weight).sum()
            matches = home_weight.sum() + away_weight.sum()
            matches = matches if matches > 0 else 1
            team_stats[team] = {"scored": goals_scored / matches, "against": goals_against / matches}

        # League averages
        league_avg = ((df_all.get("homeGoals", pd.Series([0])) + df_all.get("awayGoals", pd.Series([0]))).mean()) / 2
        league_avg = league_avg if league_avg > 0 else 1.0
        for team in teams:
            attack[team] = team_stats[team]["scored"] / league_avg
            defense[team] = team_stats[team]["against"] / league_avg

        # === Shrink toward mean early season (deterministic uncertainty) ===
        num_teams = len(teams)
        total_matches_season = num_teams * (num_teams - 1)
        matches_played = len(df_all)
        season_progress = matches_played / total_matches_season if total_matches_season > 0 else 1.0
        mean_attack = attack.mean()
        mean_defense = defense.mean()

        if season_progress < 0.5:
            # Flatten toward mean more strongly early season
            # Max shrink: factor = 0.5 → ratings halfway to mean. 0.3 means only 30% of the original distance from the mean remains, so the ratings are closer to the mean.
            max_shrink = 0.3  # smaller = stronger flattening
            shrink_factor = max_shrink + (1 - max_shrink) * season_progress*2  # linear up to half season
            shrink_factor = min(shrink_factor, 1.0)
            attack = mean_attack + shrink_factor * (attack - mean_attack)
            defense = mean_defense + shrink_factor * (defense - mean_defense)

        # Compute Poisson probabilities
        df_future = normalize_columns(fixtures_dict[league])
        results = []
        for _, row in df_future.iterrows():
            home = row["homeTeam"]
            away = row["awayTeam"]
            p_win, p_draw, p_loss = match_probabilities_league(home, away, attack, defense, league_avg, home_adv)
            results.append({
                "utcDate": row.get("utcDate", pd.NaT),
                "homeTeam": home,
                "awayTeam": away,
                "p_home_win": p_win,
                "p_draw": p_draw,
                "p_away_win": p_loss
            })
        df_prob = pd.DataFrame(results)

        # Combine with betting odds
        df_book = betting_odds_dict.get(league, pd.DataFrame())
        if not df_book.empty:
            df_book = df_book.rename(columns={"home_team": "homeTeam", "away_team": "awayTeam"})
            df_final = df_prob.merge(df_book, on=["homeTeam", "awayTeam"], how="left")
        else:
            df_final = df_prob.copy()

        for col_model, col_book, col_final in [
            ("p_home_win", "p_home_book", "p_home_final"),
            ("p_draw", "p_draw_book", "p_draw_final"),
            ("p_away_win", "p_away_book", "p_away_final")
        ]:
            if col_book in df_final.columns:
                df_final[col_final] = np.where(df_final[col_book].notna(), df_final[col_book], df_final[col_model])
            else:
                df_final[col_final] = df_final[col_model]

        prob_cols = ["p_home_final", "p_draw_final", "p_away_final"]
        df_final[prob_cols] = df_final[prob_cols].div(df_final[prob_cols].sum(axis=1), axis=0)

        df_final_all[league] = df_final[["utcDate", "homeTeam", "awayTeam", "p_home_final", "p_draw_final", "p_away_final"]]

    return df_final_all

# === MAIN BLOCK ===
if __name__ == "__main__":
    leagues = [
        "premierleague_england",
        "championship_england",
        "seriea_italy",
        "laliga_spain",
        "bundesliga_germany",
        "ligue1_france",
        "seriea_brazil"
    ]
    past_matches_all = {league: globals().get(f"past_matches_{league}_all", pd.DataFrame()) for league in leagues}
    fixtures_all = {league: globals().get(f"fixtures_{league}", pd.DataFrame()) for league in leagues}
    betting_odds_all = {league: globals().get(f"betting_odds_{league}", pd.DataFrame()) for league in leagues}

    df_sim_all = compute_final_probabilities(leagues, past_matches_all, fixtures_all, betting_odds_all)
    for league, df in df_sim_all.items():
        print(f"\n=== {league.replace('_', ' ').title()} ===")
        print(df.head(3))
        print(f"Number of matches: {len(df)}")