# app.py

import streamlit as st
import pickle
import pandas as pd
import dataset_simulation
import dataset_creation  # For loading original league tables

# -------------------------------
# 1️⃣ Page config
st.set_page_config(page_title="Football League Simulation", layout="wide")
st.title("⚽ Football League Monte Carlo Simulation")

# -------------------------------
# 2️⃣ Load precomputed simulations
@st.cache_data
def load_precomputed():
    with open("data/precomputed_pos_counts.pkl", "rb") as f:
        pos_counts_all = pickle.load(f)
    with open("data/precomputed_pos_pct.pkl", "rb") as f:
        pos_pct_all = pickle.load(f)
    return pos_counts_all, pos_pct_all

position_distribution_all, position_distribution_pct_all = load_precomputed()

# -------------------------------
# 3️⃣ Load league tables for metadata (GP, PTS, etc.)
@st.cache_data
def load_tables():
    standings, _, _ = dataset_creation.create_datasets(save_csv=False)
    return standings

tables_all = load_tables()

# -------------------------------
# 4️⃣ Select league to display
leagues = list(position_distribution_all.keys())
selected_league = st.sidebar.selectbox("Select League", leagues)

# -------------------------------
# 5️⃣ Display styled table for selected league
st.header(f"🏆 {selected_league.replace('_', ' ').title()} Simulation Results")
st.write("Probability table for league positions (top rows shown). Scroll to see all.")

# Get precomputed DataFrame for selected league
pos_pct = position_distribution_pct_all[selected_league]
table = tables_all[selected_league]

# Dynamically style
styled_table = dataset_simulation.style_position_table(pos_pct, table)

# Display in Streamlit
st.dataframe(styled_table, use_container_width=True)