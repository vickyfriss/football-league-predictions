import pickle
import pandas as pd
import importlib.util
import sys
import os
from datetime import datetime, UTC
import numpy as np

RUN_CREATION = True

# =========================
# 0️⃣ HELPER: dynamic import
# =========================
def import_module_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


dataset_creation = import_module_from_path("dataset_creation", "1_dataset_creation.py")
dataset_processing = import_module_from_path("dataset_processing", "2_dataset_processing.py")
dataset_probabilities = import_module_from_path("dataset_probabilities", "3_probabilities.py")
dataset_simulation = import_module_from_path("dataset_simulation", "4_simulations.py")


# =========================
# 1️⃣ LOAD DATA
# =========================
print("1️⃣ Loading datasets...")

def load_csv(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def load_cached_odds_fixtures_and_history():
    """Reload odds/fixtures/past-season-results from the CSV cache on disk.
    Used for OFFLINE MODE, and also as the fallback below when standings are
    unchanged: create_datasets() intentionally returns None for these three in
    that case (no need to re-hit the APIs), but something still has to supply
    real data for the rest of the pipeline to simulate from."""
    league_table_folder = "data/league_table"

    standings_cached = {
        lg: load_csv(f"{league_table_folder}/{lg}.csv")
        for lg in dataset_processing.leagues
        if os.path.exists(f"{league_table_folder}/{lg}.csv")
    }

    odds_book_cached = {
        lg: load_csv(f"data/odds_{lg}.csv")
        for lg in dataset_processing.leagues
        if os.path.exists(f"data/odds_{lg}.csv")
    }

    fixtures_cached = {
        lg: load_csv(f"data/fixtures_{lg}.csv")
        for lg in dataset_processing.leagues
        if os.path.exists(f"data/fixtures_{lg}.csv")
    }

    past_season_results_cached = {}
    for lg in dataset_processing.leagues:
        past_season_results_cached[lg] = {}
        if not os.path.exists("data"):
            continue
        for file in os.listdir("data"):
            if file.startswith(f"past_{lg}_"):
                try:
                    season = int(file.split("_")[-1].replace(".csv", ""))
                    past_season_results_cached[lg][season] = load_csv(f"data/{file}")
                except:
                    continue

    return standings_cached, odds_book_cached, fixtures_cached, past_season_results_cached


if RUN_CREATION:
    standings, odds_book, fixtures, past_season_results = dataset_creation.create_datasets(save_csv=True)

    if odds_book is None or fixtures is None or past_season_results is None:
        print("Standings unchanged — reloading odds/fixtures/history from the CSV cache instead of live APIs.")
        _, cached_odds, cached_fixtures, cached_history = load_cached_odds_fixtures_and_history()
        odds_book = cached_odds if odds_book is None else odds_book
        fixtures = cached_fixtures if fixtures is None else fixtures
        past_season_results = cached_history if past_season_results is None else past_season_results

else:
    print("⚡ OFFLINE MODE → loading from CSV")
    standings, odds_book, fixtures, past_season_results = load_cached_odds_fixtures_and_history()


# =========================
# 1️⃣.5 PRIOR-SEASON ROSTERS (for telling relegated teams apart from promoted ones)
# =========================
# Built from the RAW per-season history, before the active/finished filtering
# below -- a league that hasn't started yet this season (e.g. the Premier
# League in August) still needs its LAST season's roster on hand, so
# Championship can tell "just relegated from the Premier League" apart from
# "just promoted from League One" for its own newly-arrived teams. Cheap:
# just team-name sets, not full match data.
prior_rosters_by_league_season = {}
for lg in dataset_processing.leagues:
    rosters = {}
    mapping = dataset_processing.mappings.get(lg, {})
    for season, df in past_season_results.get(lg, {}).items():
        if df is None or df.empty:
            rosters[season] = set()
        else:
            # This history is raw football-data.org output (e.g. "West Ham
            # United FC") -- it needs the same name mapping every other
            # dataset gets before comparing against it, or a real relegated
            # team simply never matches its own name here. Confirmed by a
            # real test run: "West Ham United" (mapped) against a roster
            # still holding "West Ham United FC" (raw) matched nothing.
            df_norm = dataset_processing.normalize_columns(df).replace(mapping)
            cols = [c for c in ["homeTeam", "awayTeam"] if c in df_norm.columns]
            rosters[season] = set(pd.unique(df_norm[cols].values.ravel("K"))) if cols else set()
    prior_rosters_by_league_season[lg] = rosters


# =========================
# 2️⃣ BUILD GLOBALS
# =========================
print("2️⃣ Processing datasets...")

globals_dict = {}

for lg in dataset_processing.leagues:

    league_results = past_season_results.get(lg, {})

    if league_results:
        sorted_seasons = sorted(league_results.keys())
        current_season_key = sorted_seasons[-1]
        past_matches_current = league_results[current_season_key]

        # Blend the current season with the immediately preceding one, for
        # RATINGS purposes only (see past_matches_{lg}_blended below) -- a
        # handful of current-season matches alone (especially in the season's
        # first weeks) isn't enough signal to rate a team fairly, and the
        # previous season is already fetched and cached right here (e.g. PSV:
        # 1 draw so far this season -> near-zero title chance with zero credit
        # for winning the league comfortably last season, before this blend).
        # 3_probabilities.py's existing recency-weighting (sorted by actual
        # match date, linearly ramped 1x -> 2x) naturally gives the more
        # recent season more weight once both are combined here.
        #
        # Deliberately kept SEPARATE from past_matches_current (which stays
        # current-season-only): process_datasets() below compares played-match
        # counts against THIS SEASON's expected games-played to detect missing
        # reverse fixtures -- feeding it blended multi-season data made it
        # think almost every match was "missing" (comparing e.g. 35 blended
        # matches played against 1 expected). The "has this league's season
        # even started" check just below has the same requirement.
        seasons_to_blend = sorted_seasons[-2:]
        non_empty = [league_results[s] for s in seasons_to_blend if not league_results[s].empty]
        past_matches_blended = pd.concat(non_empty, ignore_index=True) if non_empty else pd.DataFrame()

        # process_datasets() below renames raw team-name spellings (e.g. "PSV" ->
        # "PSV Eindhoven") on past_matches_{lg}_all, future_matches_{lg} and
        # betting_odds_{lg} -- but it has no idea this new _blended key exists,
        # so without this, any team whose previous-season data needs renaming
        # (about half of them, typically) would silently split into two
        # unrelated "teams": their real rating sits under the raw name nobody
        # else uses, while their mapped name gets treated as brand new with
        # near-zero history. That's exactly what made Feyenoord (whose raw name
        # already matched, so no renaming needed) look artificially dominant
        # next to PSV (needs renaming, so its real history was invisible).
        if not past_matches_blended.empty:
            past_matches_blended = past_matches_blended.replace(dataset_processing.mappings.get(lg, {}))
    else:
        past_matches_current = pd.DataFrame()
        past_matches_blended = pd.DataFrame()

    if past_matches_current.empty:
        # The season genuinely hasn't started yet (zero matches played this
        # season) -- not "not much data yet", literally nothing to simulate.
        # Skip entirely, same as before the blending above was introduced.
        print(f"⚠️ {lg}: season hasn't started yet (no current-season matches) → skipping")
        continue

    globals_dict[f"past_matches_{lg}_all"] = past_matches_current
    globals_dict[f"past_matches_{lg}_blended"] = past_matches_blended
    globals_dict[f"future_matches_{lg}"] = fixtures.get(lg, pd.DataFrame())
    globals_dict[f"betting_odds_{lg}"] = odds_book.get(lg, pd.DataFrame())
    globals_dict[lg] = standings.get(lg, pd.DataFrame())


# =========================
# 3️⃣ PROCESS DATASETS
# =========================
missing_df, _ = dataset_processing.process_datasets(globals_dict)

print("\n📊 Missing fixtures:")
print(missing_df if missing_df is not None else "None")


# =========================
# 4️⃣ LEAGUE CLASSIFICATION
# =========================
active_leagues = []
finished_leagues = []

print("\n📊 Checking league status...")

for lg in dataset_processing.leagues:

    table = globals_dict.get(lg)

    if table is None or table.empty:
        continue

    if "gp" not in table.columns or "team" not in table.columns:
        continue

    table = table.copy()
    table["gp"] = pd.to_numeric(table["gp"], errors="coerce").fillna(0)

    teams = table["team"].nunique()
    expected_gp = (teams - 1) * 2 if teams > 0 else 0

    if expected_gp > 0 and (table["gp"] >= expected_gp).all():
        finished_leagues.append(lg)
        print(f"{lg}: 🏁 finished")
    else:
        active_leagues.append(lg)
        print(f"{lg}: ⚽ active")

print(f"\nActive leagues: {active_leagues}")
print(f"Finished leagues: {finished_leagues}")


# =========================
# 5️⃣ NORMALISERS
# =========================
def normalize_fixtures(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["homeTeam", "awayTeam"])

    df = df.copy()
    df = df.rename(columns={"home_team": "homeTeam", "away_team": "awayTeam"})

    if "homeTeam" not in df.columns:
        df["homeTeam"] = pd.NA
    if "awayTeam" not in df.columns:
        df["awayTeam"] = pd.NA

    return df


def normalize_odds(df):
    if df is None:
        return pd.DataFrame()

    df = df.copy()
    return df.rename(columns={"home_team": "homeTeam", "away_team": "awayTeam"})


# =========================
# 6️⃣ PROBABILITIES
# =========================
print("3️⃣ Computing match probabilities...")

df_simulation_all, ratings_by_league, _home_adv_by_league = dataset_probabilities.compute_final_probabilities(
    active_leagues,
    {lg: globals_dict.get(f"past_matches_{lg}_blended", pd.DataFrame()) for lg in active_leagues},
    {lg: normalize_fixtures(globals_dict.get(f"future_matches_{lg}")) for lg in active_leagues},
    {lg: normalize_odds(globals_dict.get(f"betting_odds_{lg}")) for lg in active_leagues},
    current_season_matches_dict={lg: globals_dict.get(f"past_matches_{lg}_all", pd.DataFrame()) for lg in active_leagues},
    prior_rosters_by_league_season=prior_rosters_by_league_season,
)

print("✅ Probabilities computed.")


# =========================
# 7️⃣ MONTE CARLO
# =========================
print("4️⃣ Running Monte Carlo simulations...")

tables_all = {lg: globals_dict.get(lg, pd.DataFrame()) for lg in active_leagues}

position_distribution_all, position_distribution_pct_all, _ = dataset_simulation.simulate_leagues(
    active_leagues,
    df_simulation_all,
    tables_all,
    n_sim=10000,
    ratings_by_league=ratings_by_league,
)


# =========================
# 8️⃣ FIXED FORMATTER (IMPORTANT FIX)
# =========================
def to_simulation_format(df):
    df = df.copy()

    # 🔥 REMOVE ANY INDEX-LIKE COLUMNS (THIS FIXES YOUR ISSUE)
    df.columns = df.columns.str.lower()
    df = df.loc[:, ~df.columns.str.contains("^unnamed|^index$")]
    df = df.drop(columns=["index"], errors="ignore")

    # 🔥 FORCE CLEAN INDEX (REMOVES LEFT COLUMN EFFECT)
    df = df.reset_index(drop=True)

    df["pts"] = pd.to_numeric(df["pts"], errors="coerce").fillna(0)
    df["gp"] = pd.to_numeric(df["gp"], errors="coerce").fillna(0)

    df = df.sort_values("pts", ascending=False).reset_index(drop=True)

    df["POS"] = np.arange(1, len(df) + 1)

    df = df.rename(columns={
        "team": "TEAM",
        "gp": "GP",
        "pts": "PTS"
    })

    df = df[["POS", "TEAM", "GP", "PTS"]]

    n = len(df)

    for i in range(1, n + 1):
        df[i] = 0.0

    for idx, row in df.iterrows():
        df.at[idx, int(row["POS"])] = 100.0

    df.columns.name = None
    df.index.name = None

    return df


# =========================
# 9️⃣ APPLY FIX
# =========================
for lg in finished_leagues:
    df = globals_dict[lg]

    position_distribution_all[lg] = to_simulation_format(df)
    position_distribution_pct_all[lg] = position_distribution_all[lg]

    print(f"✅ Finished league formatted: {lg}")


print("✅ Simulations complete.")


# =========================
# 🔟 SAVE OUTPUTS
# =========================
print("5️⃣ Saving results...")

os.makedirs("data", exist_ok=True)
os.makedirs("data/simulations", exist_ok=True)

with open("data/precomputed_pos_counts.pkl", "wb") as f:
    pickle.dump(position_distribution_all, f)

with open("data/precomputed_pos_pct.pkl", "wb") as f:
    pickle.dump(position_distribution_pct_all, f)

timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
sim_folder = os.path.join("data", "simulations", timestamp)

os.makedirs(sim_folder, exist_ok=True)

for lg, df in position_distribution_all.items():
    df.to_csv(os.path.join(sim_folder, f"{lg}_simulation.csv"), index=False)

print(f"✅ Done. Saved in '{sim_folder}'.")