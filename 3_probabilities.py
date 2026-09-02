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

def weighted_mean(values, weights):
    """Recency-weighted mean, matching the weighting already used for attack/defense
    below -- home advantage and the league scoring baseline should discount older
    (last-season) matches the same way, not treat them as equal to this week's."""
    values = values.fillna(0)
    weights = weights.reindex(values.index).fillna(0)
    total_weight = weights.sum()
    return (values * weights).sum() / total_weight if total_weight > 0 else 0.0

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

LOW_TRUST_THRESHOLD = 0.3  # shrink_per_team below this -> flagged for Option 2's simulation-time uncertainty

# Leagues with a tracked tier directly above them, for telling a relegated
# team apart from a promoted one when both arrive in a league "new" this
# season. Every other league in this pipeline is already a top flight, so
# every newly-arrived team there is a promotion by definition.
RELEGATED_FROM_ABOVE = {
    "championship_england": "premierleague_england",
}

# Historical priors for newly-arrived teams' first-season attack/defense,
# as a ratio to their new league's own mean (1.0 = league average). Fixed
# constants, not recomputed from the current season's 1-2 games played --
# an earlier attempt did that and it was too noisy to trust (a single early
# scoreline swings the ratio wildly). These come from real completed
# seasons instead, computed in the "Priors for Promoted and Relegated
# Teams" notebook (Football-analytics repo):
#   PROMOTED: every team promoted into a "big 5" league (Premier League,
#   La Liga, Bundesliga, Serie A, Ligue 1) for the one completed season
#   football-data.org's free tier exposes -- n=14, consistently below
#   average on attack, and worse than average on defense for all but a
#   couple of teams.
#   RELEGATED: the three teams relegated from the Premier League into the
#   Championship in 2024/25 (Ipswich, Leicester, Southampton), over their
#   following Championship season -- n=3. Two of three came back well
#   above the Championship average on attack; Leicester was the outlier,
#   finishing below average on attack and worse than average on defense.
#   A single point estimate will be wrong more often here than for
#   promoted teams; treat this one as the rougher of the two priors.
#   football-data.org's free tier only exposes the current season plus
#   one prior, so this is the one full cohort available for either group
#   right now -- revisit both once another promoted/relegated cohort
#   completes a season and rolls into the cached data.
PROMOTED_TEAM_ATTACK_RATIO = 0.769
PROMOTED_TEAM_DEFENSE_RATIO = 1.224
RELEGATED_TEAM_ATTACK_RATIO = 1.220
RELEGATED_TEAM_DEFENSE_RATIO = 0.811


def compute_final_probabilities(leagues, past_matches_dict, fixtures_dict, betting_odds_dict,
                                 current_season_matches_dict=None, prior_rosters_by_league_season=None):
    df_final_all = {}
    home_adv_by_league = {}
    ratings_by_league = {}

    for league in leagues:
        df_all = past_matches_dict[league].copy()
        if "utcDate" in df_all.columns:
            df_all["utcDate"] = pd.to_datetime(df_all["utcDate"], errors='coerce', utc=True).dt.tz_localize(None)
            df_all = df_all.sort_values("utcDate").reset_index(drop=True)
        df_all["weight"] = np.linspace(1, 2, len(df_all)) if len(df_all) > 0 else 1
        past_matches_dict[league + "_weighted"] = df_all

        goal_diff = df_all.get("homeGoals", pd.Series([0])) - df_all.get("awayGoals", pd.Series([0]))
        home_adv = weighted_mean(goal_diff, df_all["weight"])
        home_adv_by_league[league] = home_adv

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
            matches_weighted = home_weight.sum() + away_weight.sum()
            matches_weighted = matches_weighted if matches_weighted > 0 else 1
            team_stats[team] = {
                "scored": goals_scored / matches_weighted,
                "against": goals_against / matches_weighted,
                "matches_played": len(home_games) + len(away_games),
            }

        total_goals = df_all.get("homeGoals", pd.Series([0])) + df_all.get("awayGoals", pd.Series([0]))
        league_avg = weighted_mean(total_goals, df_all["weight"]) / 2
        league_avg = league_avg if league_avg > 0 else 1.0
        for team in teams:
            attack[team] = team_stats[team]["scored"] / league_avg
            defense[team] = team_stats[team]["against"] / league_avg

        current_df = None
        if current_season_matches_dict is not None:
            current_df = normalize_columns(current_season_matches_dict.get(league, pd.DataFrame()))
        current_teams = extract_teams(current_df) if current_df is not None and not current_df.empty else set(teams)
        num_teams = len(current_teams) if current_teams else len(teams)
        target_matches = max((num_teams - 1) * 2, 1)  # one full double round-robin season
        min_shrink = 0.1  # a team with 0 matches keeps only 10% of its raw rating's distance from the mean

        # A team is "new to this league" if every one of its blended matches
        # is actually from THIS season -- i.e. it has zero matches in the
        # previous-season portion of the blend, because last season it was
        # playing somewhere else entirely (a different division).
        current_only_counts = {}
        if current_df is not None and not current_df.empty:
            for team in teams:
                current_only_counts[team] = int(
                    ((current_df["homeTeam"] == team) | (current_df["awayTeam"] == team)).sum()
                )

        # Shrinkage must track how many of THIS season's matches a team has
        # played, not its blended (current + prior season) match count --
        # otherwise an established team's last season alone (a full ~38
        # games) already clears target_matches, so shrink_per_team hits 1.0
        # before a ball's been kicked this season, silently skipping the
        # early-season uncertainty this is meant to model. Confirmed live:
        # 2 matches into 2026/27, five different Premier League teams (each
        # with a full 2025/26 season on file) came out at shrink=1.0, using
        # their blended rating completely unshrunk.
        team_matches = pd.Series({t: current_only_counts.get(t, 0) for t in teams})
        shrink_per_team = min_shrink + (1 - min_shrink) * (team_matches / target_matches).clip(upper=1.0)

        newly_arrived = {
            t for t in teams
            if team_stats[t]["matches_played"] > 0
            and current_only_counts.get(t, 0) == team_stats[t]["matches_played"]
        }

        relegated_teams = set()
        above_league = RELEGATED_FROM_ABOVE.get(league)
        if above_league and prior_rosters_by_league_season:
            above_rosters = prior_rosters_by_league_season.get(above_league, {})
            if above_rosters:
                # The OLDEST of the two seasons on file, not the newest --
                # this pipeline always fetches exactly [current, previous]
                # (see PAST_SEASONS in 1_dataset_creation.py), and the above
                # league's "current" season is very often still empty (0
                # games played) at exactly the point this detection matters
                # most, i.e. right when a newly-relegated team needs to be
                # recognised. Picking the max season number silently picked
                # that empty roster and made every relegated team fall
                # through to "promoted" instead -- confirmed by a real test
                # run where relegated teams' outlook got WORSE, not better.
                last_completed_season = sorted(above_rosters.keys())[0]
                relegated_teams = newly_arrived & above_rosters.get(last_completed_season, set())
        promoted_teams = newly_arrived - relegated_teams

        # Every other team (returning, or new but undetected as either)
        # shrinks toward the plain league mean; promoted/relegated teams
        # shrink toward the historical priors defined above the function.
        mean_attack = attack.mean()
        mean_defense = defense.mean()
        target_attack = pd.Series(mean_attack, index=teams)
        target_defense = pd.Series(mean_defense, index=teams)
        for t in promoted_teams:
            target_attack[t] = mean_attack * PROMOTED_TEAM_ATTACK_RATIO
            target_defense[t] = mean_defense * PROMOTED_TEAM_DEFENSE_RATIO
        for t in relegated_teams:
            target_attack[t] = mean_attack * RELEGATED_TEAM_ATTACK_RATIO
            target_defense[t] = mean_defense * RELEGATED_TEAM_DEFENSE_RATIO

        attack = target_attack + shrink_per_team * (attack - target_attack)
        defense = target_defense + shrink_per_team * (defense - target_defense)

        # Full post-shrink ratings, not just the low-trust subset -- the
        # simulator needs BOTH sides of a fixture to recompute a Poisson
        # probability, and a low-trust team's opponent is very often an
        # established one with no entry of its own otherwise.
        ratings_by_league[league] = {
            "attack": attack, "defense": defense, "league_avg": league_avg, "home_adv": home_adv,
            "shrink_per_team": shrink_per_team,
            "low_trust_teams": {t for t in teams if shrink_per_team[t] < LOW_TRUST_THRESHOLD},
        }

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

    return df_final_all, ratings_by_league, home_adv_by_league

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

    df_sim_all, low_trust_all, home_adv_all = compute_final_probabilities(leagues, past_matches_all, fixtures_all, betting_odds_all)
    for league, df in df_sim_all.items():
        print(f"\n=== {league.replace('_', ' ').title()} ===")
        print(df.head(3))
        print(f"Number of matches: {len(df)}")