# precompute_simulations.py

import pickle
import pandas as pd
import importlib.util
import sys
import os
from datetime import datetime, UTC

# === 0️⃣ HELPER: dynamic import for numbered modules ===
def import_module_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import modules
dataset_creation = import_module_from_path("dataset_creation", "1_dataset_creation.py")
dataset_processing = import_module_from_path("dataset_processing", "2_dataset_processing.py")
dataset_probabilities = import_module_from_path("dataset_probabilities", "3_probabilities.py")
dataset_simulation = import_module_from_path("dataset_simulation", "4_simulations.py")

# === 1️⃣ Check standings and create datasets if changed ===
print("1️⃣ Scraping league standings...")

standings = dataset_creation.scrape_standings()
changed_leagues_dict = dataset_creation.standings_changed(standings)
changed_leagues = [lg for lg, changed in changed_leagues_dict.items() if changed]

if not changed_leagues:
    print("⚠️ Standings unchanged. Skipping dataset creation and simulations.")
    sys.exit(0)

print("✅ Standings changed for leagues:", changed_leagues)
standings, odds_book, fixtures, past_season_results = dataset_creation.create_datasets(save_csv=True)

# Ensure dicts are not None
odds_book = odds_book or {}
fixtures = fixtures or {}
past_season_results = past_season_results or {}

print("✅ Datasets created.")

# === 2️⃣ Process datasets only for changed leagues ===
print("2️⃣ Processing datasets...")

globals_dict = {}

for lg in changed_leagues:

    # 1️⃣ Past matches (this season)
    league_results = past_season_results.get(lg, {})
    past_matches_current = pd.DataFrame()
    if league_results:
        latest_season = max(league_results.keys())
        past_matches_current = league_results[latest_season]

    if past_matches_current.empty:
        print(f"⚠️ {lg}: No past matches retrieved. Skipping this league.")
        continue

    globals_dict[f"past_matches_{lg}_all"] = past_matches_current

    # 2️⃣ Future matches
    df_fixtures = fixtures.get(lg, pd.DataFrame())
    for col in ["homeTeam", "awayTeam"]:
        if col not in df_fixtures.columns:
            df_fixtures[col] = pd.NA
    globals_dict[f"future_matches_{lg}"] = df_fixtures

    # 3️⃣ Betting odds
    df_odds = odds_book.get(lg, pd.DataFrame())
    for col in ["home_team", "away_team"]:
        if col not in df_odds.columns:
            df_odds[col] = pd.NA
    globals_dict[f"betting_odds_{lg}"] = df_odds

    # 4️⃣ League table for verification
    df_standings = standings.get(lg, pd.DataFrame())
    globals_dict[lg] = pd.DataFrame({"team": df_standings["team"].copy()})

missing_df, backup_futures = dataset_processing.process_datasets(globals_dict)
if not missing_df.empty:
    print(f"⚠️ Missing fixtures added:\n{missing_df}")
else:
    print("✅ No missing fixtures detected.")

# === 3️⃣ Compute probabilities only for changed leagues ===
print("3️⃣ Computing match probabilities...")

past_matches_dict = {lg: globals_dict[f"past_matches_{lg}_all"] for lg in changed_leagues}
fixtures_dict = {lg: globals_dict[f"future_matches_{lg}"] for lg in changed_leagues}
betting_odds_dict = {lg: globals_dict[f"betting_odds_{lg}"] for lg in changed_leagues}

df_simulation_all = dataset_probabilities.compute_final_probabilities(
    changed_leagues,
    past_matches_dict,
    fixtures_dict,
    betting_odds_dict
)

print("✅ Probabilities computed.")

# === 4️⃣ Run Monte Carlo simulations only for changed leagues ===
print("4️⃣ Running Monte Carlo simulations...")

tables_all = {lg: standings.get(lg, pd.DataFrame()) for lg in changed_leagues}

position_distribution_all, position_distribution_pct_all, _ = dataset_simulation.simulate_leagues(
    changed_leagues,
    df_simulation_all,
    tables_all,
    n_sim=10000
)

print("✅ Simulations complete.")

# === 5️⃣ Save precomputed results ===
print("5️⃣ Saving precomputed results...")

os.makedirs("data", exist_ok=True)
os.makedirs("data/simulations", exist_ok=True)

# Save pickle files
with open("data/precomputed_pos_counts.pkl", "wb") as f:
    pickle.dump(position_distribution_all, f)
with open("data/precomputed_pos_pct.pkl", "wb") as f:
    pickle.dump(position_distribution_pct_all, f)

# Save CSV per league in timestamped folder
timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
sim_folder = os.path.join("data", "simulations", timestamp)
os.makedirs(sim_folder, exist_ok=True)

for lg, df in position_distribution_all.items():
    csv_path = os.path.join(sim_folder, f"{lg}_simulation.csv")
    df.to_csv(csv_path, index=False)

print(f"✅ Precomputed results saved in '{sim_folder}'.")