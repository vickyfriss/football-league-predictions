# 1_dataset_creation_local_fixtures.py
import os
import time
import pandas as pd
import requests
from datetime import datetime, timedelta

# -------------------------------
# Helper to get API key
def get_api_key(env_var_name, local_file=None):
    key = os.getenv(env_var_name)
    if key:
        return key
    if local_file and os.path.exists(local_file):
        from dotenv import load_dotenv
        load_dotenv(local_file)
        key = os.getenv(env_var_name)
        if key:
            return key
    raise ValueError(f"{env_var_name} not found in environment variables or {local_file}")

# -------------------------------
# Team name cleaning
TEAM_NAME_MAPPING = {
    "AAS Roma": "AS Roma",
    "OComo": "Como",
    "B04Bayer Leverkusen": "Bayer Leverkusen",
    "M05Mainz": "Mainz",
    "NLyon": "Lyon",
    "LLille": "Lille",
    "ENice": "Nice",
    "ZMetz": "Metz",
    "ORemo": "Remo",
}

def clean_team_names(df, column="team"):
    df = df.copy()
    df[column] = df[column].replace(TEAM_NAME_MAPPING)
    return df

# -------------------------------
# Scrape final standings from ESPN
def scrape_standings():
    leagues_codes = {
        "ENG.1": ("premierleague_england", 2025),
        "ENG.2": ("championship_england", 2025),
        "ITA.1": ("seriea_italy", 2025),
        "ESP.1": ("laliga_spain", 2025),
        "GER.1": ("bundesliga_germany", 2025),
        "FRA.1": ("ligue1_france", 2025),
        "BRA.1": ("seriea_brazil", 2026),
    }
    standings = {}
    for league_code, (df_name, year) in leagues_codes.items():
        url = f"https://www.espn.com/soccer/standings/_/league/{league_code}/season/{year}"
        tables = pd.read_html(url)

        teams_raw = tables[0]
        stats = tables[1]

        teams = pd.DataFrame()
        teams["position"] = teams_raw.iloc[:, 0].str.extract(r"^(\d+)").astype(int)
        teams["team"] = (
            teams_raw.iloc[:, 0]
            .str.replace(r"^\d+", "", regex=True)
            .str.replace(r"^[A-Z]{2,3}", "", regex=True)
            .str.strip()
        )

        stats.columns = ["gp", "w", "d", "l", "gf", "ga", "gd", "pts"]
        stats = stats.apply(lambda c: c.astype(str).str.replace("+", "", regex=False).astype(int))

        df = pd.concat([teams, stats], axis=1)
        df = clean_team_names(df)
        standings[df_name] = df
    return standings

# -------------------------------
# Check if standings changed
def standings_changed(new_standings, data_folder="data/league_table"):
    os.makedirs(data_folder, exist_ok=True)
    changed_leagues = {}
    for league, new_df in new_standings.items():
        file_path = f"{data_folder}/{league}.csv"
        if not os.path.exists(file_path):
            print(f"{league}: no previous standings found.")
            changed_leagues[league] = True
            continue
        old_df = pd.read_csv(file_path)
        merged = new_df[["team", "position"]].merge(
            old_df[["team", "position"]],
            on="team",
            suffixes=("_new", "_old"),
            how="outer"
        )
        changed_leagues[league] = not (merged["position_new"] == merged["position_old"]).all()
        if changed_leagues[league]:
            print(f"{league}: standings changed.")
    return changed_leagues

# -------------------------------
# Load betting odds (optional)
def load_betting_odds(leagues=None):
    API_KEY = get_api_key("ODDS_DATA_API_KEY", local_file="API_KEY.env")
    leagues_api = {
        "soccer_epl": "odds_premierleague_england",
        "soccer_efl_champ": "odds_championship_england",
        "soccer_italy_serie_a": "odds_seriea_italy",
        "soccer_spain_la_liga": "odds_laliga_spain",
        "soccer_germany_bundesliga": "odds_bundesliga_germany",
        "soccer_france_ligue_one": "odds_ligue1_france",
        "soccer_brazil_campeonato": "odds_seriea_brazil",
    }

    base_url = "https://api.the-odds-api.com/v4/sports/{}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "uk",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
        "days": 365,
    }

    odds_data = {}
    for sport_key, var_name in leagues_api.items():
        if leagues is not None and var_name not in leagues:
            continue
        try:
            url = base_url.format(sport_key)
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"{var_name}: {len(data)} matches returned")
            odds_data[var_name] = data
        except Exception:
            print(f"{sport_key}: betting odds not available, skipping.")
            odds_data[var_name] = []
    return odds_data

def flatten_odds(data):
    rows = []
    for match in data:
        match_id = match["id"]
        home = match["home_team"]
        away = match["away_team"]
        time_ = match["commence_time"]

        for book in match.get("bookmakers", []):
            bookmaker = book["title"]
            h2h = next((m for m in book["markets"] if m["key"] == "h2h"), None)
            if not h2h:
                continue
            outcomes = {o["name"]: o["price"] for o in h2h["outcomes"]}
            rows.append({
                "match_id": match_id,
                "commence_time": time_,
                "home_team": home,
                "away_team": away,
                "bookmaker": bookmaker,
                "home_odds": outcomes.get(home),
                "draw_odds": outcomes.get("Draw"),
                "away_odds": outcomes.get(away),
            })
    return pd.DataFrame(rows)

def compute_implied_probs(df):
    if df.empty:
        return df
    df = df.assign(
        p_home_raw=1/df["home_odds"],
        p_draw_raw=1/df["draw_odds"],
        p_away_raw=1/df["away_odds"]
    )
    total = df["p_home_raw"] + df["p_draw_raw"] + df["p_away_raw"]
    df = df.assign(
        p_home_book=df["p_home_raw"]/total,
        p_draw_book=df["p_draw_raw"]/total,
        p_away_book=df["p_away_raw"]/total
    )
    return df.groupby(["home_team","away_team"], as_index=False)[["p_home_book","p_draw_book","p_away_book"]].mean()

# -------------------------------
# Past season results (optional)
def fetch_past_season_results(leagues=None, data_folder="data/previous_season"):
    API_KEY = get_api_key("FOOTBALL_DATA_API_KEY", local_file="API_KEY.env")
    competitions = {
        "PL": ("premierleague_england", [2025, 2024]),
        "ELC": ("championship_england", [2025, 2024]),
        "SA": ("seriea_italy", [2025, 2024]),
        "PD": ("laliga_spain", [2025, 2024]),
        "BL1": ("bundesliga_germany", [2025, 2024]),
        "FL1": ("ligue1_france", [2025, 2024]),
        "BSA": ("seriea_brazil", [2026, 2025]),
    }

    headers = {"X-Auth-Token": API_KEY}
    past_matches = {}
    os.makedirs(data_folder, exist_ok=True)

    for comp_code, (league_name, seasons) in competitions.items():
        if leagues is not None and league_name not in leagues:
            continue
        past_matches[league_name] = {}
        previous_season = seasons[1]

        for season in seasons:
            file_path = f"{data_folder}/past_{league_name}_{season}.csv"
            if season == previous_season and os.path.exists(file_path):
                past_matches[league_name][season] = pd.read_csv(file_path)
                continue

            url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
            params = {"season": season, "status": "FINISHED"}
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                matches = response.json().get("matches")
                if matches is None:
                    raise RuntimeError(f"{league_name} season {season}: API returned no 'matches'")
            except Exception as e:
                print(f"❌ {league_name} season {season}: API call failed: {e}")
                continue

            rows = []
            for m in matches:
                rows.append({
                    "utcDate": m["utcDate"],
                    "matchday": m.get("matchday"),
                    "status": m["status"],
                    "homeTeam": m["homeTeam"]["name"],
                    "awayTeam": m["awayTeam"]["name"],
                    "homeGoals": m["score"]["fullTime"]["home"],
                    "awayGoals": m["score"]["fullTime"]["away"],
                    "winner": m["score"]["winner"],
                })

            df = pd.DataFrame(rows)
            if season == previous_season:
                df.to_csv(file_path, index=False)
            past_matches[league_name][season] = df
            time.sleep(10)

    return past_matches

# -------------------------------
# -------------------------------
# LOCAL FIXTURE GENERATOR
def normalize_columns(df):
    df = df.copy()
    if df.empty:
        df["homeTeam"] = pd.Series(dtype=str)
        df["awayTeam"] = pd.Series(dtype=str)
        return df

    rename_map = {}
    for old, new in [
        ("home_team", "homeTeam"), ("away_team", "awayTeam"),
        ("HomeTeam", "homeTeam"), ("AwayTeam", "awayTeam")
    ]:
        if old in df.columns:
            rename_map[old] = new

    if rename_map:
        df = df.rename(columns=rename_map)

    return df

def generate_fixtures(league_table, past_matches=None):
    teams = league_table["team"].tolist()
    all_matches = pd.DataFrame(
        [(h, a) for h in teams for a in teams if h != a],
        columns=["homeTeam", "awayTeam"]
    )

    if past_matches is not None:
        past_matches = normalize_columns(past_matches)
        all_matches = pd.merge(
            all_matches, past_matches[["homeTeam", "awayTeam"]],
            on=["homeTeam", "awayTeam"], how="left", indicator=True
        )
        all_matches = all_matches[all_matches["_merge"] == "left_only"].drop(columns="_merge")

    all_matches["utcDate"] = pd.NaT
    return all_matches.reset_index(drop=True)

# -------------------------------
# MASTER FUNCTION
def create_datasets(save_csv=True):
    print("Scraping league standings...")
    standings = scrape_standings()
    league_table_folder = "data/league_table"

    changed_leagues = standings_changed(standings, league_table_folder)
    if not any(changed_leagues.values()):
        print("No standings changed for any league. Skipping updates.")
        return standings, None, None, None

    print("Standings changed for leagues:", [l for l, changed in changed_leagues.items() if changed])

    odds_book = {}
    fixtures = {}
    past_results = {}

    leagues_to_update = [l for l, changed in changed_leagues.items() if changed]

    # Past results (optional)
    past_results_all = fetch_past_season_results(leagues=leagues_to_update)

    # Generate local fixtures
    for league in leagues_to_update:
        past_df = past_results_all.get(league, {}).get(max(past_results_all[league].keys(), default=0), pd.DataFrame())
        fixtures[league] = generate_fixtures(standings[league], past_matches=past_df)
        past_results[league] = past_results_all.get(league, {})

        # Odds (optional)
        odds_raw = load_betting_odds(leagues=[league])
        if league in odds_raw:
            odds_df = flatten_odds(odds_raw.get(league, []))
            odds_book[league] = compute_implied_probs(odds_df)

        # Save CSVs
        if save_csv:
            os.makedirs(league_table_folder, exist_ok=True)
            standings[league].to_csv(f"{league_table_folder}/{league}.csv", index=False)
            fixtures[league].to_csv(f"data/fixtures_{league}.csv", index=False)
            if league in odds_book:
                os.makedirs("data", exist_ok=True)
                odds_book[league].to_csv(f"data/odds_{league}.csv", index=False)
            if league in past_results:
                for season, df in past_results[league].items():
                    df.to_csv(f"data/past_{league}_{season}.csv", index=False)

    print("Datasets updated locally with generated fixtures.")
    return standings, odds_book, fixtures, past_results

# -------------------------------
if __name__ == "__main__":
    create_datasets()