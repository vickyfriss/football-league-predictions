import pickle
import pandas as pd
import importlib.util
import sys
import os
from datetime import datetime, UTC
import numpy as np

RUN_CREATION = True  # OFFLINE MODE

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

if RUN_CREATION:
    standings, odds_book, fixtures, past_season_results = dataset_creation.create_datasets(save_csv=True)

else:
    print("⚡ OFFLINE MODE → loading from CSV")

    def load_csv(path):
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()

    league_table_folder = "data/league_table"

    standings = {
        lg: load_csv(f"{league_table_folder}/{lg}.csv")
        for lg in dataset_processing.leagues
        if os.path.exists(f"{league_table_folder}/{lg}.csv")
    }

    odds_book = {
        lg: load_csv(f"data/odds_{lg}.csv")
        for lg in dataset_processing.leagues
        if os.path.exists(f"data/odds_{lg}.csv")
    }

    fixtures = {
        lg: load_csv(f"data/fixtures_{lg}.csv")
        for lg in dataset_processing.leagues
        if os.path.exists(f"data/fixtures_{lg}.csv")
    }

    past_season_results = {}

    for lg in dataset_processing.leagues:
        past_season_results[lg] = {}

        if not os.path.exists("data"):
            continue

        for file in os.listdir("data"):
            if file.startswith(f"past_{lg}_"):
                try:
                    season = int(file.split("_")[-1].replace(".csv", ""))
                    past_season_results[lg][season] = load_csv(f"data/{file}")
                except:
                    continue


# =========================
# 2️⃣ BUILD GLOBALS
# =========================
print("2️⃣ Processing datasets...")

globals_dict = {}

for lg in dataset_processing.leagues:

    league_results = past_season_results.get(lg, {})

    if league_results:
        latest_season = max(league_results.keys())
        past_matches_current = league_results[latest_season]
    else:
        past_matches_current = pd.DataFrame()

    if past_matches_current.empty:
        print(f"⚠️ {lg}: no past matches → skipping")
        continue

    globals_dict[f"past_matches_{lg}_all"] = past_matches_current
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

df_simulation_all = dataset_probabilities.compute_final_probabilities(
    active_leagues,
    {lg: globals_dict.get(f"past_matches_{lg}_all", pd.DataFrame()) for lg in active_leagues},
    {lg: normalize_fixtures(globals_dict.get(f"future_matches_{lg}")) for lg in active_leagues},
    {lg: normalize_odds(globals_dict.get(f"betting_odds_{lg}")) for lg in active_leagues},
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
    n_sim=10000
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