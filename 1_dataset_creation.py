# 1_dataset_creation.py
from io import StringIO
import os
import time
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
import asyncio
from playwright.async_api import async_playwright

# -------------------------------
# football-data.org rate limiting -- shared across load_fixtures() and
# fetch_past_season_results(), which together fire ~19-20 requests at that
# API back-to-back for 9 leagues. Its free tier allows ~10 requests/minute
# *total*, not per function, so without this the fixtures calls alone burn
# through the budget and the very next historical-results call gets a 429 --
# which used to cost a wasted request plus a blind 60s sleep in
# request_with_retry. Proactively spacing every call to stay just under the
# limit means that never happens.
import collections
_FOOTBALL_DATA_REQUEST_TIMES = collections.deque()
_FOOTBALL_DATA_MAX_PER_MINUTE = 9

def throttle_football_data():
    now = time.time()
    while _FOOTBALL_DATA_REQUEST_TIMES and now - _FOOTBALL_DATA_REQUEST_TIMES[0] > 60:
        _FOOTBALL_DATA_REQUEST_TIMES.popleft()
    if len(_FOOTBALL_DATA_REQUEST_TIMES) >= _FOOTBALL_DATA_MAX_PER_MINUTE:
        sleep_for = 60 - (now - _FOOTBALL_DATA_REQUEST_TIMES[0]) + 0.5
        if sleep_for > 0:
            print(f"Pacing football-data.org requests -- waiting {sleep_for:.1f}s to stay under the rate limit...")
            time.sleep(sleep_for)
    _FOOTBALL_DATA_REQUEST_TIMES.append(time.time())

# -------------------------------
# Robust API request with retry
def request_with_retry(url, headers=None, params=None, max_retries=5):

    for attempt in range(1, max_retries + 1):

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response

        except Exception as e:

            if attempt == max_retries:
                print(f"❌ Final attempt failed for {url}")
                raise

            wait_time = attempt * 60
            print(
                f"⚠️ API call failed: {e}. "
                f"Retrying in {attempt} minute(s)..."
            )
            time.sleep(wait_time)

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
    "Z Alkmaar": "AZ Alkmaar",
    # Primeira Liga: several clubs' ESPN abbreviation codes run 4 characters
    # (e.g. Santa Clara -> "CDSC"), one more than [A-Z0-9]{2,3} strips, so a
    # single leftover capital stays glued to the name (e.g. "CSanta Clara").
    "CSanta Clara": "Santa Clara",
    "CGil Vicente": "Gil Vicente",
    "CRio Ave": "Rio Ave",
    "CCasa Pia": "Casa Pia",
}

def clean_team_names(df, column="team"):
    df = df.copy()
    df[column] = df[column].replace(TEAM_NAME_MAPPING)
    return df

async def fetch_html_async(page, url, retries=5, wait_selector="table"):
    """ESPN's edge (AWS WAF Bot Control) returns HTTP 202 with an empty body and
    an `x-amzn-waf-action: challenge` header to plain HTTP clients from
    datacenter IPs (GitHub Actions' hosted runners included) -- confirmed by
    hitting the same URL directly with curl/requests from an equivalent cloud
    IP and getting the identical empty 202. No header spoofing or backoff
    fixes that; it's a JS proof-of-work challenge, so it needs a real browser
    to execute it. `page` is a Playwright page (real headless Chromium) --
    it runs the challenge JS itself and lands on the actual standings page,
    same as a human visit would."""

    for i in range(retries):

        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            await page.wait_for_selector(wait_selector, timeout=30000)
            html = await page.content()

            print(f"Attempt {i+1}: got {len(html)} bytes")

            if len(html.strip()) > 2000:
                return html

        except Exception as e:
            print(f"Request error: {e}")

        if i < retries - 1:
            await asyncio.sleep(min(5 * (2 ** i), 60))

    raise RuntimeError(f"❌ Failed to fetch valid HTML after retries for {url}")


async def _scrape_one_league(browser, semaphore, league_code, df_name, year):
    async with semaphore:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
        )
        try:
            page = await context.new_page()
            url = f"https://www.espn.com/soccer/standings/_/league/{league_code}/season/{year}"
            html = await fetch_html_async(page, url)
            return df_name, html
        finally:
            await context.close()


async def _scrape_standings_async(leagues_codes):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            # Concurrency capped at 3 (not all 9 at once) -- ESPN's WAF is
            # already known to be sensitive to datacenter IPs (see
            # fetch_html_async's docstring); a burst of 9 simultaneous
            # challenge-solving page loads from the same IP looks more
            # bot-like than sequential requests and risks harder blocking,
            # not just a race to load faster.
            semaphore = asyncio.Semaphore(3)
            results = await asyncio.gather(
                *[
                    _scrape_one_league(browser, semaphore, code, name, year)
                    for code, (name, year) in leagues_codes.items()
                ],
                return_exceptions=True,
            )
        finally:
            await browser.close()
    return results


# -------------------------------
# Scrape standings
def scrape_standings():

    leagues_codes = {
        "ENG.1": ("premierleague_england", 2026),
        "ENG.2": ("championship_england", 2026),
        "ITA.1": ("seriea_italy", 2026),
        "ESP.1": ("laliga_spain", 2026),
        "GER.1": ("bundesliga_germany", 2026),
        "FRA.1": ("ligue1_france", 2026),
        "NED.1": ("eredivisie_netherlands", 2026),
        "BRA.1": ("seriea_brazil", 2026),  # calendar-year league, still mid-season — unchanged
        "POR.1": ("primeiraliga_portugal", 2026),
    }

    results = asyncio.run(_scrape_standings_async(leagues_codes))

    standings = {}

    for item in results:

        if isinstance(item, Exception):
            print(f"⚠️ Failed to scrape a league: {item}")
            continue

        df_name, html = item

        try:
            tables = pd.read_html(StringIO(html))
        except Exception as e:
            print(f"⚠️ Failed parsing HTML for {df_name}: {e}")
            continue

        teams_raw = tables[0]
        stats = tables[1]

        teams = pd.DataFrame()
        teams["position"] = teams_raw.iloc[:, 0].str.extract(r"^(\d+)").astype(int)

        teams["team"] = (
            teams_raw.iloc[:, 0]
            .str.replace(r"^\d+", "", regex=True)
            # Some clubs' ESPN abbreviation codes mix letters and digits (e.g.
            # Schalke 04 -> "S04"), which [A-Z]{2,3} alone doesn't match, leaving
            # the code stuck to the front of the name (e.g. "S04Schalke 04").
            .str.replace(r"^[A-Z0-9]{2,3}", "", regex=True)
            .str.strip()
        )

        stats.columns = ["gp", "w", "d", "l", "gf", "ga", "gd", "pts"]

        stats = stats.apply(
            lambda c: c.astype(str)
            .str.replace("+", "", regex=False)
            .astype(int)
        )

        df = pd.concat([teams, stats], axis=1)
        df = clean_team_names(df)

        standings[df_name] = df

    return standings


# -------------------------------
# Check standings changes
def standings_changed(new_standings, data_folder="data/league_table"):

    os.makedirs(data_folder, exist_ok=True)

    for league, new_df in new_standings.items():

        file_path = f"{data_folder}/{league}.csv"

        if not os.path.exists(file_path):
            print(f"{league}: no previous standings found.")
            return True

        old_df = pd.read_csv(file_path)
        
        merged = new_df[["team", "gp"]].merge(
            old_df[["team", "gp"]],
            on="team",
            suffixes=("_new", "_old"),
            how="outer"
        )

        if not (merged["gp_new"] == merged["gp_old"]).all():
            print(f"{league}: standings changed.")
            return True

    print("No standings changes detected.")
    return False

# -------------------------------
# Load betting odds
def load_betting_odds():

    API_KEY = get_api_key("ODDS_DATA_API_KEY", local_file="API_KEY.env")

    leagues_api = {
        "soccer_epl": "odds_premierleague_england",
        "soccer_efl_champ": "odds_championship_england",
        "soccer_italy_serie_a": "odds_seriea_italy",
        "soccer_spain_la_liga": "odds_laliga_spain",
        "soccer_germany_bundesliga": "odds_bundesliga_germany",
        "soccer_france_ligue_one": "odds_ligue1_france",
        "soccer_netherlands_eredivisie": "odds_eredivisie_netherlands",
        "soccer_brazil_campeonato": "odds_seriea_brazil",
        "soccer_portugal_primeira_liga": "odds_primeiraliga_portugal",
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

        try:

            url = base_url.format(sport_key)

            response = request_with_retry(url, params=params)

            data = response.json()

            print(f"{var_name}: {len(data)} matches returned")

            odds_data[var_name] = data

        except Exception:

            print(f"{sport_key}: betting odds not available")

            odds_data[var_name] = []

    return odds_data

# -------------------------------
# Flatten odds
def flatten_odds(data):

    rows = []

    for match in data:

        match_id = match["id"]
        home = match["home_team"]
        away = match["away_team"]
        time_ = match["commence_time"]

        for book in match.get("bookmakers", []):

            bookmaker = book["title"]

            h2h = next(
                (m for m in book["markets"] if m["key"] == "h2h"),
                None
            )

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

# -------------------------------
# Implied probabilities
def compute_implied_probs(df):

    if df.empty:
        return df

    df = df.assign(
        p_home_raw=1 / df["home_odds"],
        p_draw_raw=1 / df["draw_odds"],
        p_away_raw=1 / df["away_odds"]
    )

    total = df["p_home_raw"] + df["p_draw_raw"] + df["p_away_raw"]

    df = df.assign(
        p_home_book=df["p_home_raw"] / total,
        p_draw_book=df["p_draw_raw"] / total,
        p_away_book=df["p_away_raw"] / total
    )

    return df.groupby(
        ["home_team", "away_team"],
        as_index=False
    )[["p_home_book", "p_draw_book", "p_away_book"]].mean()

# -------------------------------
# Fixtures
def load_fixtures():

    API_KEY = get_api_key("FOOTBALL_DATA_API_KEY", local_file="API_KEY.env")

    competitions = {
        "PL": "fixtures_premierleague_england",
        "ELC": "fixtures_championship_england",
        "SA": "fixtures_seriea_italy",
        "PD": "fixtures_laliga_spain",
        "BL1": "fixtures_bundesliga_germany",
        "FL1": "fixtures_ligue1_france",
        "DED": "fixtures_eredivisie_netherlands",
        "BSA": "fixtures_seriea_brazil",
        "PPL": "fixtures_primeiraliga_portugal",
    }

    headers = {"X-Auth-Token": API_KEY}

    today = datetime.utcnow().date()
    end_of_season = today + timedelta(days=365)

    params = {
        "status": "SCHEDULED",
        "dateFrom": today.isoformat(),
        "dateTo": end_of_season.isoformat(),
    }

    fixtures_data = {}

    for comp_code, df_name in competitions.items():

        try:
            url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"

            throttle_football_data()
            response = request_with_retry(url, headers=headers, params=params)

            data = response.json().get("matches", [])

            # ✅ handle empty response safely
            if not data:
                print(f"{comp_code}: no upcoming fixtures returned")
                fixtures_data[df_name] = pd.DataFrame()
                continue

        except Exception as e:
            print(f"{comp_code}: fixtures not available ({e})")
            fixtures_data[df_name] = pd.DataFrame()
            continue

        df = pd.DataFrame(data)[["utcDate", "status", "homeTeam", "awayTeam"]]

        df["homeTeam"] = df["homeTeam"].apply(lambda x: x["name"])
        df["awayTeam"] = df["awayTeam"].apply(lambda x: x["name"])

        fixtures_data[df_name] = df

    return fixtures_data  # ✅ always returns dict

# -------------------------------
# Past results

# football-data.org can take hours to mark a game FINISHED, so a game counts as
# played once it kicked off PLAYED_AFTER ago and has a full-time score, whatever
# its status says. Games in NOT_PLAYED never count, score or not.
NOT_PLAYED = {"POSTPONED", "CANCELLED", "SUSPENDED"}
PLAYED_AFTER = timedelta(hours=3)

def played_matches(matches):
    now = datetime.now(timezone.utc)
    rows = []
    for m in matches:
        home, away = m["score"]["fullTime"]["home"], m["score"]["fullTime"]["away"]
        kickoff = datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00"))
        if m["status"] in NOT_PLAYED or home is None or away is None or now - kickoff < PLAYED_AFTER:
            continue
        rows.append({
            "utcDate": m["utcDate"],
            "matchday": m.get("matchday"),
            "status": "FINISHED",
            "homeTeam": m["homeTeam"]["name"],
            "awayTeam": m["awayTeam"]["name"],
            "homeGoals": home,
            "awayGoals": away,
            "winner": "HOME_TEAM" if home > away else "AWAY_TEAM" if away > home else "DRAW",
        })
    return pd.DataFrame(rows, columns=["utcDate", "matchday", "status", "homeTeam", "awayTeam", "homeGoals", "awayGoals", "winner"])

def merge_with_saved(df, file_path):
    # The feed sometimes leaves out a game it already returned as played, so
    # every game in the saved file is kept. Each pairing is played once a
    # season, so (homeTeam, awayTeam) identifies a game; the fresh row wins
    # in case the score was corrected.
    if os.path.exists(file_path):
        df = pd.concat([pd.read_csv(file_path), df]).drop_duplicates(subset=["homeTeam", "awayTeam"], keep="last")
    return df.sort_values("utcDate").reset_index(drop=True)

def fetch_past_season_results(data_folder="data/previous_season", leagues=None):

    API_KEY = get_api_key("FOOTBALL_DATA_API_KEY", local_file="API_KEY.env")

    competitions = {
        "PL": ("premierleague_england", [2026, 2025]),
        "ELC": ("championship_england", [2026, 2025]),
        "SA": ("seriea_italy", [2026, 2025]),
        "PD": ("laliga_spain", [2026, 2025]),
        "BL1": ("bundesliga_germany", [2026, 2025]),
        "FL1": ("ligue1_france", [2026, 2025]),
        "DED": ("eredivisie_netherlands", [2026, 2025]),
        "BSA": ("seriea_brazil", [2026, 2025]),  # calendar-year league, still mid-season — unchanged
        "PPL": ("primeiraliga_portugal", [2026, 2025]),
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

                print(f"Loading cached {league_name} {season}")

                past_matches[league_name][season] = pd.read_csv(file_path)

                continue

            print(f"Fetching {league_name} season {season}...")

            url = f"https://api.football-data.org/v4/competitions/{comp_code}/matches"

            # All statuses: played_matches() decides what has been played
            params = {"season": season}

            throttle_football_data()
            response = request_with_retry(url, headers=headers, params=params)

            df = played_matches(response.json().get("matches") or [])

            if season == previous_season:
                df.to_csv(file_path, index=False)
            else:
                df = merge_with_saved(df, f"data/past_{league_name}_{season}.csv")

            past_matches[league_name][season] = df

    return past_matches

# -------------------------------
# Results vs the table

# When the results hold fewer games than the scraped table says were played,
# the feed is behind: refetch those leagues every RESULTS_RETRY_WAIT seconds,
# up to RESULTS_RETRIES times, then report whatever is still missing.
RESULTS_RETRIES = 3
RESULTS_RETRY_WAIT = 15 * 60
RESULTS_BEHIND_FILE = "logs/results_behind.txt"

def results_behind(standings, past_results=None):
    # {league: (games in the table, games in the results)} for every league
    # whose current-season results are short. Without past_results, the saved
    # CSVs are checked.
    behind = {}
    for league, table in standings.items():
        if past_results is not None:
            seasons = past_results.get(league)
            if not seasons:
                continue
            df = seasons[max(seasons)]
        else:
            files = sorted(f for f in os.listdir("data") if f.startswith(f"past_{league}_") and f.endswith(".csv"))
            if not files:
                continue
            df = pd.read_csv(f"data/{files[-1]}")
        in_table = int(pd.to_numeric(table["gp"], errors="coerce").sum()) // 2
        if len(df) < in_table:
            behind[league] = (in_table, len(df))
    return behind

def write_results_behind(behind):
    # The workflow fails its last step when this file has lines, so GitHub
    # sends an email; no file means the results match the table.
    os.makedirs(os.path.dirname(RESULTS_BEHIND_FILE), exist_ok=True)
    if behind:
        with open(RESULTS_BEHIND_FILE, "w") as f:
            for league, (in_table, in_results) in behind.items():
                f.write(f"{league}: {in_results} results, table says {in_table} played\n")
    elif os.path.exists(RESULTS_BEHIND_FILE):
        os.remove(RESULTS_BEHIND_FILE)

# -------------------------------
# Master function
def create_datasets(save_csv=True):

    print("Scraping league standings...")

    standings = scrape_standings()

    if not standings or len(standings) == 0:
        raise RuntimeError("❌ No standings were scraped. Aborting pipeline.")

    league_table_folder = "data/league_table"

    # Unchanged standings skip the API calls, unless the saved results are
    # still behind the table, so a later run picks up games an earlier run missed
    if not standings_changed(standings, league_table_folder):

        if not results_behind(standings):

            print("Standings unchanged and results up to date. Skipping API calls.")

            write_results_behind({})

            return standings, None, None, None

        print("Standings unchanged, but results are behind the table. Updating datasets...")

    print("Standings changed. Updating datasets...")

    print("Loading betting odds...")

    odds_raw = load_betting_odds()

    odds_dfs = {k: flatten_odds(v) for k, v in odds_raw.items()}

    odds_book = {k: compute_implied_probs(v) for k, v in odds_dfs.items()}

    print("Loading fixtures...")

    fixtures = load_fixtures()

    print("Fetching past season results...")

    past_results = fetch_past_season_results()

    behind = results_behind(standings, past_results)

    for attempt in range(1, RESULTS_RETRIES + 1):

        if not behind:
            break

        for league, (in_table, in_results) in behind.items():
            print(f"⚠️ {league}: {in_results} results, table says {in_table} played")

        print(f"Results behind the table. Refetching in {RESULTS_RETRY_WAIT // 60} min (attempt {attempt}/{RESULTS_RETRIES})...")

        time.sleep(RESULTS_RETRY_WAIT)

        past_results.update(fetch_past_season_results(leagues=behind))

        behind = results_behind(standings, past_results)

    write_results_behind(behind)

    if save_csv:

        os.makedirs("data", exist_ok=True)

        os.makedirs(league_table_folder, exist_ok=True)

        for name, df in standings.items():
            df.to_csv(f"{league_table_folder}/{name}.csv", index=False)

        for name, df in odds_book.items():
            df.to_csv(f"data/{name}.csv", index=False)

        for name, df in fixtures.items():

            if df is None or not isinstance(df, pd.DataFrame):
                print(f"{name}: invalid or None fixture data, saving empty dataset")
                df = pd.DataFrame(columns=["utcDate", "status", "homeTeam", "awayTeam"])

            df.to_csv(f"data/{name}.csv", index=False)

        for league_name, seasons_dict in past_results.items():

            for season, df in seasons_dict.items():

                df.to_csv(f"data/past_{league_name}_{season}.csv", index=False)

    print("Datasets created and saved.")

    return standings, odds_book, fixtures, past_results


# -------------------------------
if __name__ == "__main__":
    create_datasets()