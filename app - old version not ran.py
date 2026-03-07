# -------------------------------
# 1️⃣ IMPORTS
import streamlit as st
import importlib.util
import sys
import pandas as pd

# -------------------------------
# 2️⃣ HELPER: dynamic module import
def import_module_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# -------------------------------
# 3️⃣ IMPORT NUMBERED MODULES
dataset_creation = import_module_from_path("dataset_creation", "1_dataset_creation.py")
dataset_processing = import_module_from_path("dataset_processing", "2_dataset_processing.py")
dataset_probabilities = import_module_from_path("dataset_probabilities", "3_probabilities.py")
dataset_simulation = import_module_from_path("dataset_simulation", "4_simulations.py")

# -------------------------------
# 4️⃣ STREAMLIT APP
st.set_page_config(page_title="Football League Simulation", layout="wide")
st.title("⚽ Football League Monte Carlo Simulation")

# Sidebar options
league = st.sidebar.selectbox(
    "Select League", dataset_processing.leagues
)
n_sim = st.sidebar.slider(
    "Number of Simulations", min_value=1000, max_value=20000, value=5000, step=1000
)
run_pipeline = st.sidebar.button("Run Full Simulation")

# -------------------------------
# 5️⃣ RUN PIPELINE
if run_pipeline:
    st.info("🚀 Running full simulation pipeline... This may take a few minutes.")
    styled_tables_all, pos_counts_all, pos_pct_all = None, None, None

    try:
        # 5a️⃣ Create datasets
        st.write("1️⃣ Scraping and loading datasets...")
        standings, odds_book, fixtures = dataset_creation.create_datasets(save_csv=False)
        st.success("✅ Datasets created.")

        # 5b️⃣ Process datasets
        st.write("2️⃣ Processing datasets...")
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
            st.warning(f"⚠️ Missing fixtures detected and added:\n{missing_df}")
        else:
            st.success("✅ No missing fixtures detected.")

        # 5c️⃣ Compute probabilities
        st.write("3️⃣ Computing match probabilities...")
        past_matches_dict = {lg: globals_dict[f"past_matches_{lg}_all"] for lg in dataset_processing.leagues}
        fixtures_dict = {lg: globals_dict[f"future_matches_{lg}"] for lg in dataset_processing.leagues}
        betting_odds_dict = {lg: globals_dict[f"betting_odds_{lg}"] for lg in dataset_processing.leagues}

        df_simulation_all = dataset_probabilities.compute_final_probabilities(
            dataset_processing.leagues, past_matches_dict, fixtures_dict, betting_odds_dict
        )
        st.success("✅ Probabilities computed.")

        # 5d️⃣ Run simulations
        st.write(f"4️⃣ Running {n_sim} Monte Carlo simulations per league...")
        tables_all = {lg: standings.get(lg, pd.DataFrame()) for lg in dataset_processing.leagues}
        position_distribution_all, position_distribution_pct_all, styled_tables_all = dataset_simulation.simulate_leagues(
            dataset_processing.leagues, df_simulation_all, tables_all, n_sim
        )
        st.success("✅ Simulations complete.")

        # 5e️⃣ Display selected league
        st.header(f"🏆 {league.replace('_', ' ').title()} Simulation Results")
        st.write("Styled probabilities table for league positions (top rows shown). Scroll to see all.")

        # Streamlit can render Styler objects directly
        styled_table = styled_tables_all.get(league)
        if styled_table is not None:
            st.write(styled_table)  # No .head() needed
        else:
            st.write("No data available for this league.")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")