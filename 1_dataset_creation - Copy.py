# 1_dataset_creation.py
import os
import time
import pandas as pd
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# -------------------------------
# 1️⃣ Team name cleaning
TEAM_NAME_MAPPING = {
    # Italy
    "AAS Roma": "AS Roma",
    "OComo": "Como",
    # Germany
    "B04Bayer Leverkusen": "Bayer Leverkusen",
    "M05Mainz": "Mainz",
    # France
    "NLyon": "Lyon",
    "LLille": "Lille",
    "ENice": "Nice",
    "ZMetz": "Metz",
}

def clean_team_names(df, column="team"):
    df = df.copy()
    df[column] = df[column].replace(TEAM_NAME_MAPPING)
    return df

# -------------------------------
# 2️⃣ Scrape final standings from ESPN
def scrape_standings(year=2025):
    leagues_codes = {
        "ENG.1": "premierleague_england",
        "ITA.1": "seriea_italy",
        "ESP.1": "laliga_spain",
        "GER.1": "bundesliga_germany",
        "FRA.1": "ligue1_france",
    }

    standings = {}
    for league_code, df_name in leagues_codes.items():
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
# 3️⃣ Load betting odds
def load_betting_odds():
    load_dotenv("API_KEY.env")
    API_KEY = os.getenv("ODDS_DATA_API_KEY")
    if API_KEY is None:
        raise ValueError("API_KEY not found in API_KEY.env")

    leagues_api = {
        "soccer_epl": "odds_premierleague_england",
        "soccer_italy_serie_a": "odds_seriea_italy",
        "soccer_spain_la_liga": "odds_laliga_spain",
        "soccer_germany_bundesliga": "odds_bundesliga_germany",
        "soccer_france_ligue_one": "odds_ligue1_france",
    }

    base_url = "https://api.the-odds-api.com/v4/sports/{}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": "uk",
        "markets": "h2h",
        "oddsFormat": "decimal",
        "dateFormat": "iso",
        "days": 365
    }

    odds_data = {}
    for sport_key, var_name in leagues_api.items():
        url = base_url.format(sport_key)
        response = requests.get(url, params=params)
        response.raise_for_status()
        odds_data[var_name] = response.json()

    return odds_data

# -------------------------------
# 4️⃣ Flatten bookmaker odds
def flatten_odds(data):
    rows = []
    for match in data:
        match_id = match["id"]
        home = match["home_team"]
        away = match["away_team"]
        time_ = match["commence_time"]

        for book in match["bookmakers"]:
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
# 5️⃣ Get fixtures from Football-Data API
def load_fixtures():
    load_dotenv("API_KEY.env")
    API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
    if API_KEY is None:
        raise ValueError("API_KEY not found in API_KEY.env")

    competitions = {
        "PL": "fixtures_premierleague_england",
        "SA": "fixtures_seriea_italy",
        "PD": "fixtures_laliga_spain",
        "BL1": "fixtures_bundesliga_germany",
        "FL1": "fixtures_ligue1_france",
    }

    headers = {"X-Auth-Token": API_KEY}
    today = datetime.utcnow().date()
    end_of_season = today + timedelta(days=365)
    params = {"status":"SCHEDULED","dateFrom":today.isoformat(),"dateTo":end_of_season.isoformat()}

    fixtures_data = {}
    for comp_code, df_name in competitions.items():
        url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()["matches"]
        df = pd.DataFrame(data)[["utcDate","status","homeTeam","awayTeam"]].copy()
        df["homeTeam"] = df["homeTeam"].apply(lambda x: x["name"])
        df["awayTeam"] = df["awayTeam"].apply(lambda x: x["name"])
        fixtures_data[df_name] = df

    return fixtures_data

# -------------------------------
# 6️⃣ Fetch past season results
def fetch_past_season_results(seasons=[2025, 2024]):
    load_dotenv("API_KEY.env")
    API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
    if API_KEY is None:
        raise ValueError("API_KEY not found in API_KEY.env")

    competitions = {
        "PL": "premierleague_england",
        "SA": "seriea_italy",
        "PD": "laliga_spain",
        "BL1": "bundesliga_germany",
        "FL1": "ligue1_france",
    }

    headers = {"X-Auth-Token": API_KEY}
    past_matches = {}

    for comp_code, league_name in competitions.items():
        past_matches[league_name] = {}
        for season in seasons:
            print(f"Fetching {league_name} season {season}...")
            url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"
            params = {"season": season, "status": "FINISHED"}

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            matches = response.json()["matches"]

            clean_rows = []
            for m in matches:
                clean_rows.append({
                    "utcDate": m["utcDate"],
                    "matchday": m.get("matchday"),
                    "status": m["status"],
                    "homeTeam": m["homeTeam"]["name"],
                    "awayTeam": m["awayTeam"]["name"],
                    "homeGoals": m["score"]["fullTime"]["home"],
                    "awayGoals": m["score"]["fullTime"]["away"],
                    "winner": m["score"]["winner"],
                })
            df_clean = pd.DataFrame(clean_rows)
            past_matches[league_name][season] = df_clean
            time.sleep(10)  # polite API request interval

    return past_matches

# -------------------------------
# 7️⃣ Master function to create all datasets
def create_datasets(save_csv=True):
    print("Scraping league standings...")
    standings = scrape_standings()

    print("Loading betting odds...")
    odds_raw = load_betting_odds()
    odds_dfs = {k: flatten_odds(v) for k,v in odds_raw.items()}
    odds_book = {k: compute_implied_probs(v) for k,v in odds_dfs.items()}

    print("Loading fixtures...")
    fixtures = load_fixtures()

    print("Fetching past season results...")
    past_results = fetch_past_season_results()

    if save_csv:
        os.makedirs("data", exist_ok=True)
        for name, df in standings.items():
            df.to_csv(f"data/{name}.csv", index=False)
        for name, df in odds_book.items():
            df.to_csv(f"data/{name}.csv", index=False)
        for name, df in fixtures.items():
            df.to_csv(f"data/{name}.csv", index=False)
        for league_name, seasons_dict in past_results.items():
            for season, df in seasons_dict.items():
                df.to_csv(f"data/past_{league_name}_{season}.csv", index=False)

    print("Datasets created and saved to 'data/' folder.")
    return standings, odds_book, fixtures, past_results

# -------------------------------
if __name__ == "__main__":
    create_datasets()