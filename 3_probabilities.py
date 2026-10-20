# 3_probabilities.py

import pandas as pd
import numpy as np
from scipy.stats import poisson
from scipy.optimize import least_squares

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

# === 1b. MARKET-IMPLIED TEAM STRENGTHS ===
# Bookmakers only price the next matchday or two, so on their own the odds only ever replaced the
# model for those few matches. Working backwards from recent prices to each team's attack and
# defence lets what the market knows (transfers, new managers, injuries) reach every remaining
# fixture too. Backtested in Football-analytics/"202610 - 3 - Market-Implied Team Strengths
# (Backtest).ipynb" on forecasts for matches not yet priced: the weight was chosen on March-May
# 2026 (2025/26) and confirmed, unchanged, on August-October 2026 (2026/27).
MARKET_WEIGHT = 0.25          # share of the market-implied rating in each team's final (log) rating
MARKET_WINDOW_DAYS = 42       # use prices from the last six weeks...
MARKET_HALF_LIFE_DAYS = 21    # ...with a three-week-old price counting half as much as today's
MARKET_RIDGE = 0.5            # pulls a team with little market data back towards its goals-based rating

_GOAL_RANGE = np.arange(11)

def _probs_from_rates(lam_home, lam_away):
    grid = np.outer(poisson.pmf(_GOAL_RANGE, lam_home), poisson.pmf(_GOAL_RANGE, lam_away))
    grid /= grid.sum()
    return np.array([np.tril(grid, -1).sum(), np.trace(grid), np.triu(grid, 1).sum()])

def rates_from_market_probs(p_home, p_draw, p_away, start=(0.35, 0.1)):
    """Expected goals (home, away) whose Poisson scoreline grid reproduces the market's
    home/draw/away probabilities. `start` is a first guess in log goals."""
    target = np.array([p_home, p_draw, p_away], dtype=float)
    target = target / target.sum()
    fit = least_squares(lambda x: _probs_from_rates(*np.exp(x)) - target,
                        x0=np.clip(np.asarray(start, dtype=float), -2.9, 1.5), bounds=([-3, -3], [1.6, 1.6]))
    return tuple(np.exp(fit.x))

def market_implied_ratings(odds_history, attack, defense, league_avg, home_adv, as_of,
                           window_days=MARKET_WINDOW_DAYS, half_life_days=MARKET_HALF_LIFE_DAYS, ridge=MARKET_RIDGE):
    """Attack/defence ratings implied by recent betting prices, on the same scale as `attack`/`defense`.

    `odds_history`: one row per (snapshot, match) with snap_time, homeTeam, awayTeam and the
    de-vigged p_home_book / p_draw_book / p_away_book, team names already mapped. Each match's
    latest price before `as_of` is turned into expected goals, then
    log(goals) = log(league_avg) [+ home_adv] + log(attack) + log(opponent's defence)
    is fitted by weighted ridge regression, pulled towards the goals-based ratings so a team the
    market has barely priced keeps (close to) its own rating. Returns None without recent prices."""
    if odds_history is None or odds_history.empty:
        return None
    window = odds_history[(odds_history["snap_time"] <= as_of)
                          & (odds_history["snap_time"] > as_of - pd.Timedelta(days=window_days))]
    if window.empty:
        return None
    latest = window.sort_values("snap_time").groupby(["homeTeam", "awayTeam"]).tail(1)
    log_avg = np.log(league_avg)
    log_att, log_def = np.log(attack), np.log(defense)
    teams = sorted(set(latest["homeTeam"]) | set(latest["awayTeam"]) | set(log_att.index))
    ix = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    prior = np.concatenate([[log_att.get(t, 0.0) for t in teams], [log_def.get(t, 0.0) for t in teams]])
    rows, y, w = [], [], []
    for r in latest.itertuples():
        start = (log_avg + home_adv + log_att.get(r.homeTeam, 0.0) + log_def.get(r.awayTeam, 0.0),
                 log_avg + log_att.get(r.awayTeam, 0.0) + log_def.get(r.homeTeam, 0.0))
        lam_home, lam_away = rates_from_market_probs(r.p_home_book, r.p_draw_book, r.p_away_book, start)
        weight = 0.5 ** ((as_of - r.snap_time).days / half_life_days)
        row = np.zeros(2 * n); row[ix[r.homeTeam]] = 1; row[n + ix[r.awayTeam]] = 1
        rows.append(row); y.append(np.log(lam_home) - log_avg - home_adv); w.append(weight)
        row = np.zeros(2 * n); row[ix[r.awayTeam]] = 1; row[n + ix[r.homeTeam]] = 1
        rows.append(row); y.append(np.log(lam_away) - log_avg); w.append(weight)
    A, y, w = np.array(rows), np.array(y), np.array(w)
    x = np.linalg.solve(A.T @ (w[:, None] * A) + ridge * np.eye(2 * n), A.T @ (w * y) + ridge * prior)
    return pd.Series(np.exp(x[:n]), index=teams), pd.Series(np.exp(x[n:]), index=teams)

def blend_ratings(goals_rating, market_rating, weight):
    """Geometric blend: `weight` of the market-implied rating, the rest from the goals-based one.
    A team missing from either side keeps the rating it has."""
    teams = goals_rating.index.union(market_rating.index)
    g, m = np.log(goals_rating.reindex(teams)), np.log(market_rating.reindex(teams))
    g, m = g.fillna(m), m.fillna(g)
    return np.exp((1 - weight) * g + weight * m)

# === 2. MAIN FUNCTION ===

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
#   football-data.org's free tier exposes -- n=14. All 14 scored below
#   their new league's average; 12 of 14 conceded more than it (Hamburg and
#   Sunderland were the exceptions). Means: attack 0.812, conceded 1.184.
#   RELEGATED: the three teams relegated from the Premier League into the
#   Championship in 2024/25 (Ipswich, Leicester, Southampton), over their
#   following Championship season -- n=3. Ipswich and Southampton came back
#   well above the Championship average on attack; Leicester was the outlier,
#   finishing below average on attack and worse than average on defense.
#   Means: attack 1.221, conceded 0.948.
#   The constants below are those measured means, rounded to 3 decimals.
#   A single point estimate will be wrong more often here than for
#   promoted teams; treat this one as the rougher of the two priors.
#   football-data.org's free tier only exposes the current season plus
#   one prior, so this is the one full cohort available for either group
#   right now -- revisit both once another promoted/relegated cohort
#   completes a season and rolls into the cached data.
PROMOTED_TEAM_ATTACK_RATIO = 0.812
PROMOTED_TEAM_DEFENSE_RATIO = 1.184
RELEGATED_TEAM_ATTACK_RATIO = 1.221
RELEGATED_TEAM_DEFENSE_RATIO = 0.948


def compute_final_probabilities(leagues, past_matches_dict, fixtures_dict, betting_odds_dict,
                                 current_season_matches_dict=None, prior_rosters_by_league_season=None,
                                 odds_history_dict=None, as_of=None, market_weight=MARKET_WEIGHT):
    # odds_history_dict: {league: recent odds snapshots} for the market-implied ratings (section 1b).
    # Without it (or with market_weight=0) the ratings are goals-only, exactly as before.
    as_of = pd.Timestamp.now(tz="UTC").tz_localize(None) if as_of is None else pd.Timestamp(as_of)
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

        # Two different shrinkage schedules. Established teams shrink toward
        # the plain league mean and get the benefit of the doubt fast: a raw
        # rating built on a real prior season is already meaningful, so it
        # keeps 50% of its own signal from kickoff. Promoted/relegated teams
        # shrink toward the historical prior instead of the mean, and start
        # from a more cautious 10% -- their raw rating this early is a
        # handful of matches at a level they've never played before, not last
        # season's form. Both schedules reach full trust at the same point,
        # half a season (one single round-robin) in.
        min_shrink_established = 0.5
        target_matches_established = max(num_teams - 1, 1)
        min_shrink_new_arrival = 0.1
        target_matches_new_arrival = max(num_teams - 1, 1)

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
                # Want the most recently COMPLETED season for the above
                # league, not its current in-progress one -- the above
                # league's "current" season is very often still empty (0
                # games played) at exactly the point this detection matters
                # most, i.e. right when a newly-relegated team needs to be
                # recognised. Excluding the current season (the max season
                # number) and taking the max of what's left gets this right
                # even when older season files pile up in the cache: an
                # earlier version just took the OLDEST season on file,
                # assuming exactly two seasons were ever cached -- confirmed
                # live to silently misclassify a team relegated only last
                # season (present in the cache's newest completed season,
                # but not its oldest) as promoted instead, once a third,
                # older season file had accumulated in data/ from a past run.
                seasons = sorted(above_rosters.keys())
                last_completed_season = seasons[-2] if len(seasons) > 1 else seasons[-1]
                relegated_teams = newly_arrived & above_rosters.get(last_completed_season, set())
        promoted_teams = newly_arrived - relegated_teams

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
        min_shrink_per_team = pd.Series(min_shrink_established, index=teams)
        target_matches_per_team = pd.Series(target_matches_established, index=teams)
        for t in newly_arrived:
            min_shrink_per_team[t] = min_shrink_new_arrival
            target_matches_per_team[t] = target_matches_new_arrival
        shrink_per_team = min_shrink_per_team + (1 - min_shrink_per_team) * (
            team_matches / target_matches_per_team
        ).clip(upper=1.0)

        # Every other team (returning, or new but undetected as either)
        # shrinks toward the plain league mean -- exactly 1.0 by definition,
        # since attack/defense are each team's own rate divided by league_avg,
        # and every goal in the dataset is scored by exactly one team, so
        # goals-scored summed back across all teams reproduces league_avg
        # exactly. attack.mean()/defense.mean() used to stand in for this,
        # but that's an UNWEIGHTED mean across teams with very unequal match
        # counts (a team present in only one of the two blended seasons
        # counts the same as one present in both), which drifts away from
        # 1.0 -- confirmed on real data at 0.978/1.028, not the intended
        # neutral midpoint. Promoted/relegated teams shrink toward the
        # historical priors defined above the function, still expressed as
        # a ratio to this same 1.0 baseline.
        mean_attack = 1.0
        mean_defense = 1.0
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

        # Blend in what recent betting prices imply about each team (section 1b)
        attack_goals, defense_goals = attack.copy(), defense.copy()
        market = None
        if odds_history_dict is not None and market_weight > 0:
            market = market_implied_ratings(odds_history_dict.get(league), attack_goals, defense_goals,
                                            league_avg, home_adv, as_of)
        if market is not None:
            attack = blend_ratings(attack_goals, market[0], market_weight)
            defense = blend_ratings(defense_goals, market[1], market_weight)

        ratings_by_league[league] = {
            "attack": attack, "defense": defense, "league_avg": league_avg, "home_adv": home_adv,
            "attack_goals": attack_goals, "defense_goals": defense_goals,
            "attack_target": target_attack, "defense_target": target_defense,
            "attack_market": market[0] if market is not None else None,
            "defense_market": market[1] if market is not None else None,
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

    df_sim_all, ratings_all, home_adv_all = compute_final_probabilities(leagues, past_matches_all, fixtures_all, betting_odds_all)
    for league, df in df_sim_all.items():
        print(f"\n=== {league.replace('_', ' ').title()} ===")
        print(df.head(3))
        print(f"Number of matches: {len(df)}")