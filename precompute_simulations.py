# precompute_simulations.py

import pickle
import pandas as pd
import importlib.util
import sys

# === 0️⃣ HELPER: dynamic import for numbered modules ===
def import_module_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import modules without renaming files
dataset_creation = import_module_from_path("dataset_creation", "1_dataset_creation.py")
dataset_processing = import_module_from_path("dataset_processing", "2_dataset_processing.py")
dataset_probabilities = import_module_from_path("dataset_probabilities", "3_probabilities.py")
dataset_simulation = import_module_from_path("dataset_simulation", "4_simulations.py")

# === 1️⃣ Create datasets ===
print("1️⃣ Creating datasets...")
standings, odds_book, fixtures = dataset_creation.create_datasets(save_csv=True)
print("✅ Datasets created.")

# === 2️⃣ Process datasets ===
print("2️⃣ Processing datasets...")
globals_dict = {}

for lg in dataset_processing.leagues:
    # Past matches / standings
    df_standings = standings.get(lg, pd.DataFrame())
    if "team" not in df_standings.columns:
        df_standings["team"] = df_standings.index.astype(str)
    globals_dict[f"past_matches_{lg}_all"] = df_standings

    # Future matches / fixtures
    df_fixtures = fixtures.get(f"fixtures_{lg}", pd.DataFrame())
    for col in ["homeTeam", "awayTeam"]:
        if col not in df_fixtures.columns:
            df_fixtures[col] = pd.NA
    globals_dict[f"future_matches_{lg}"] = df_fixtures

    # Betting odds
    df_odds = odds_book.get(f"odds_{lg}", pd.DataFrame())
    for col in ["home_team", "away_team"]:
        if col not in df_odds.columns:
            df_odds[col] = pd.NA
    globals_dict[f"betting_odds_{lg}"] = df_odds

missing_df, backup_futures = dataset_processing.process_datasets(globals_dict)
if not missing_df.empty:
    print(f"⚠️ Missing fixtures added:\n{missing_df}")
else:
    print("✅ No missing fixtures detected.")

# === 3️⃣ Compute probabilities ===
print("3️⃣ Computing match probabilities...")
past_matches_dict = {lg: globals_dict[f"past_matches_{lg}_all"] for lg in dataset_processing.leagues}
fixtures_dict = {lg: globals_dict[f"future_matches_{lg}"] for lg in dataset_processing.leagues}
betting_odds_dict = {lg: globals_dict[f"betting_odds_{lg}"] for lg in dataset_processing.leagues}

df_simulation_all = dataset_probabilities.compute_final_probabilities(
    dataset_processing.leagues, past_matches_dict, fixtures_dict, betting_odds_dict
)
print("✅ Probabilities computed.")

# === 4️⃣ Run Monte Carlo simulations ===
print("4️⃣ Running Monte Carlo simulations...")
tables_all = {lg: standings.get(lg, pd.DataFrame()) for lg in dataset_processing.leagues}

position_distribution_all, position_distribution_pct_all, _ = dataset_simulation.simulate_leagues(
    dataset_processing.leagues, df_simulation_all, tables_all, n_sim=1000
)
print("✅ Simulations complete.")

# === 5️⃣ Save precomputed results (only raw data, no Styler) ===
print("5️⃣ Saving precomputed results...")
with open("data/precomputed_pos_counts.pkl", "wb") as f:
    pickle.dump(position_distribution_all, f)

with open("data/precomputed_pos_pct.pkl", "wb") as f:
    pickle.dump(position_distribution_pct_all, f)

print("✅ Precomputed results saved in 'data/' folder.")