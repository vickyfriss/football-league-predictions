import pickle
import pandas as pd
import importlib.util
import sys
import os
from datetime import datetime, UTC

RUN_CREATION = False   # OFFLINE MODE

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
    print("1️⃣ Scraping league standings...")
    standings_raw = dataset_creation.scrape_standings()

    if not dataset_creation.standings_changed(standings_raw):
        print("⚠️ Standings unchanged. Exiting.")
        sys.exit(0)

    print("✅ Creating datasets...")
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
        f"odds_{lg}": load_csv(f"data/odds_{lg}.csv")
        for lg in dataset_processing.leagues
        if os.path.exists(f"data/odds_{lg}.csv")
    }

    fixtures = {
        f"fixtures_{lg}": load_csv(f"data/fixtures_{lg}.csv")
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

    globals_dict[f"future_matches_{lg}"] = fixtures.get(f"fixtures_{lg}", pd.DataFrame())
    globals_dict[f"betting_odds_{lg}"] = odds_book.get(f"odds_{lg}", pd.DataFrame())

    # IMPORTANT FIX: keep full table (not only team column)
    globals_dict[lg] = standings.get(lg, pd.DataFrame())


# =========================
# 3️⃣ PROCESS DATASETS
# =========================
missing_df, backup_futures = dataset_processing.process_datasets(globals_dict)

if missing_df is not None and not missing_df.empty:
    print(f"⚠️ Missing fixtures added:\n{missing_df}")
else:
    print("✅ No missing fixtures detected.")


# =========================
# 4️⃣ LEAGUE CLASSIFICATION (ROBUST FIX)
# =========================
active_leagues = []
finished_leagues = []

print("\n📊 Checking league status...")

for lg in dataset_processing.leagues:

    table = globals_dict.get(lg)

    if table is None or table.empty:
        continue

    required_cols = {"team", "gp"}
    if not required_cols.issubset(table.columns):
        continue

    table = table.copy()

    gp = pd.to_numeric(table["gp"], errors="coerce").fillna(0)

    teams = table["team"].nunique()
    if teams < 2:
        continue

    expected_gp = (teams - 1) * 2

    if (gp >= expected_gp).all():
        finished_leagues.append(lg)
        print(f"{lg}: 🏁 finished")
    else:
        active_leagues.append(lg)
        print(f"{lg}: ⚽ active")


print(f"\nActive leagues: {active_leagues}")
print(f"Finished leagues: {finished_leagues}")


# =========================
# 5️⃣ PROBABILITIES (ONLY ACTIVE)
# =========================
print("3️⃣ Computing match probabilities...")

simulation_leagues = active_leagues

past_matches_dict = {
    lg: globals_dict.get(f"past_matches_{lg}_all", pd.DataFrame())
    for lg in simulation_leagues
}

fixtures_dict = {
    lg: globals_dict.get(f"future_matches_{lg}", pd.DataFrame())
    for lg in simulation_leagues
}

betting_odds_dict = {
    lg: globals_dict.get(f"betting_odds_{lg}", pd.DataFrame())
    for lg in simulation_leagues
}

df_simulation_all = dataset_probabilities.compute_final_probabilities(
    simulation_leagues,
    past_matches_dict,
    fixtures_dict,
    betting_odds_dict
)

print("✅ Probabilities computed.")


# =========================
# 6️⃣ MONTE CARLO (ACTIVE ONLY)
# =========================
print("4️⃣ Running Monte Carlo simulations...")

tables_all = {
    lg: globals_dict.get(lg, pd.DataFrame())
    for lg in simulation_leagues
}

position_distribution_all, position_distribution_pct_all, _ = dataset_simulation.simulate_leagues(
    simulation_leagues,
    df_simulation_all,
    tables_all,
    n_sim=10000
)


# =========================
# 6B️⃣ FINISHED LEAGUES (FIXED CLEAN OUTPUT)
# =========================
for lg in finished_leagues:

    df = globals_dict[lg].copy()

    # final ranking
    df = df.sort_values("pts", ascending=False).reset_index(drop=True)
    df["position"] = range(1, len(df) + 1)

    n = len(df)

    # create probability columns exactly like simulation output
    for i in range(1, n + 1):
        df[f"prob_{i}"] = 0.0

    # ONLY correct deterministic mapping
    for i in range(n):
        pos = i + 1
        df.loc[i, f"prob_{pos}"] = 1.0

    position_distribution_all[lg] = df
    position_distribution_pct_all[lg] = df


print("✅ Simulations complete.")


# =========================
# 7️⃣ SAVE OUTPUTS
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