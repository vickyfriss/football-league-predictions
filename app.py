# -------------------------------
# 1️⃣ IMPORTS
import streamlit as st
import pickle
import pandas as pd
import numpy as np
import os
from datetime import datetime, timezone
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# -------------------------------
# 2️⃣ STREAMLIT APP CONFIG
st.set_page_config(page_title="Football League Simulator", layout="wide", page_icon="⚽")

# -------------------------------
# 3️⃣ HELPER FUNCTIONS FOR STYLING

greens = plt.cm.Greens
green_cmap = LinearSegmentedColormap.from_list(
    "Greens_soft",
    greens(np.linspace(0.05, 0.65, 256))
)

mid_pct = 0.14
max_pct = 0.75

def zero_style(val):
    if val < 1:
        return "background-color: white !important;"
    return ""

def color_scale(val, mid=mid_pct, max_val=max_pct):
    if val >= max_val:
        return 1.0
    elif val <= mid:
        return val / mid * 0.5
    else:
        return 0.5 + (val - mid) / (max_val - mid) * 0.5

def style_probabilities_table(df):
    display_df = df.copy().reset_index(drop=True)

    text_cols = ["POS", "TEAM", "GP", "PTS"]
    num_cols = display_df.columns.difference(text_cols)

    vmax = max(display_df[num_cols].max().max(), 1) if not display_df[num_cols].empty else 1
    color_data = display_df[num_cols].divide(vmax).apply(lambda s: s.map(color_scale)) * vmax

    styled = (
        display_df.style
        .background_gradient(cmap=green_cmap, vmin=0, vmax=vmax, gmap=color_data, axis=None)
        .map(zero_style, subset=num_cols)
        .format({col: "{:.2f}%" for col in num_cols})
        .set_properties(subset=["POS","GP","PTS"], **{
            "text-align":"center","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"600","color":"#000","white-space":"nowrap"
        })
        .set_properties(subset=["TEAM"], **{
            "text-align":"left","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"600","color":"#000","white-space":"nowrap"
        })
        .set_properties(subset=num_cols, **{
            "text-align":"center","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"500","color":"#000"
        })
        .hide(axis="index")
        .set_table_styles([
            {"selector": "th", "props":[("background-color","#e6edf4"),("color","#333"),
                                       ("text-align","center"),
                                       ("font-family","Inter, Roboto, Arial, sans-serif"),
                                       ("font-size","13px"),("font-weight","600")]},
            {"selector": "tr", "props":[("height","25px")]},
            {"selector": "th:nth-child(4), td:nth-child(4)", "props":[("border-right","2px solid #999")]},
            {"selector": "td:nth-child(-n+4)", "props":[("border-bottom","1px solid #ccc")]},
            {"selector": "tr:nth-child(odd) td:nth-child(-n+4)", "props":[("background-color","#f9f9f9")]},
            {"selector": "tr:nth-child(even) td:nth-child(-n+4)", "props":[("background-color","#f2f2f2")]},
        ])
    )

    return styled, num_cols

# -------------------------------
# 4️⃣ CACHE SIMULATION DATA LOADING

@st.cache_data
def load_simulation_data():

    pct_file = "data/precomputed_pos_pct.pkl"

    if not os.path.exists(pct_file):
        return {}

    with open(pct_file, "rb") as f:
        return pickle.load(f)

# -------------------------------
# 5️⃣ PAGE STYLING
st.markdown("""
<style>
body, .main { background-color: #f8f9fa; }

h1, h2, h3, .stMarkdown p, .stSelectbox label { 
    text-align: center !important; 
    width: 100%; 
    display: block;
}

div.stSelectbox > label, div.stSelectbox > div {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
}

div.stSelectbox > div > div[role="combobox"] {
    max-width: 300px;
    min-width: 200px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 6️⃣ TITLE

st.title("⚽ Football League Simulator ⚽")

st.markdown("""
**Data-driven forecasts for final positions across Europe’s top 5 football leagues (2025-26).**

This app simulates every remaining fixture 10,000 times, producing 10,000 full season scenarios per league.  
The results are aggregated to generate probabilities for each team finishing in each league position.
""")

# -------------------------------
# 7️⃣ LOAD SIMULATION DATA

try:

    position_distribution_pct_all = load_simulation_data()

    if position_distribution_pct_all:

        pct_file = "data/precomputed_pos_pct.pkl"
        pct_mtime = datetime.fromtimestamp(os.path.getmtime(pct_file), tz=timezone.utc)
        formatted_time = pct_mtime.strftime("%d/%B/%Y %H:%M")

        st.info(f"Simulations last run on: {formatted_time} UTC")

    else:
        st.warning("⚠️ No precomputed simulation results found.")

except Exception as e:
    st.error(f"❌ Failed to load simulation results: {e}")
    position_distribution_pct_all = {}

# -------------------------------
# 8️⃣ LEAGUE SELECTION

league_display_names = [
    "Premier League (England)",
    "Serie A (Italy)",
    "La Liga (Spain)",
    "Bundesliga (Germany)",
    "Ligue 1 (France)"
]

league_key_map = {
    "Premier League (England)": "premierleague_england",
    "Serie A (Italy)": "seriea_italy",
    "La Liga (Spain)": "laliga_spain",
    "Bundesliga (Germany)": "bundesliga_germany",
    "Ligue 1 (France)": "ligue1_france"
}

selected_display_name = st.selectbox("Select League", league_display_names)
league = league_key_map[selected_display_name]

# -------------------------------
# 9️⃣ PREPARE DATAFRAME

if league in position_distribution_pct_all and not position_distribution_pct_all[league].empty:

    pos_pct_df = position_distribution_pct_all[league].copy().reset_index()

else:

    pos_pct_df = pd.DataFrame(columns=["POS","TEAM","GP","PTS"])

if isinstance(pos_pct_df.columns, pd.MultiIndex):
    pos_pct_df.columns = [str(c) for c in pos_pct_df.columns]

for col in ["POS","TEAM","GP","PTS"]:

    if col not in pos_pct_df.columns:

        if col == "POS":
            pos_pct_df[col] = np.arange(1, len(pos_pct_df)+1)

        elif col in ["GP","PTS"]:
            pos_pct_df[col] = 0

        else:
            pos_pct_df[col] = ""

pos_pct_df["TEAM"] = pos_pct_df["TEAM"].astype(str)
pos_pct_df["POS"] = pos_pct_df["POS"].astype(int)
pos_pct_df["GP"] = pos_pct_df["GP"].astype(int)
pos_pct_df["PTS"] = pos_pct_df["PTS"].astype(int)

st.header(f"🏆 {selected_display_name} Simulation Results")

# -------------------------------
# 🔟 STYLE AND DISPLAY TABLE

styled_table, num_cols = style_probabilities_table(pos_pct_df)

responsive_table_css = """
<style>

div.table-wrapper {
    width: 100%;
    overflow-x: auto;
}

table {
    width: 100% !important;
    border-collapse: collapse;
}

th, td {
    overflow: visible !important;
    white-space: normal !important;
    text-align: center !important;
    font-size: 14px !important;
    padding: 4px 6px !important;
}

th:nth-child(2), td:nth-child(2) {
    text-align: left !important;
    min-width: 150px;
}

th:nth-child(1), td:nth-child(1) { width: 40px; }
th:nth-child(3), td:nth-child(3) { min-width: 50px; }
th:nth-child(4), td:nth-child(4) { min-width: 50px; }
th:nth-child(n+5), td:nth-child(n+5) { min-width: 60px; }

@media (max-width: 600px) {
    th, td { font-size: 12px !important; }
    th:nth-child(2), td:nth-child(2) { min-width: 120px; }
}

</style>
"""

st.markdown(responsive_table_css, unsafe_allow_html=True)
st.markdown(f'<div class="table-wrapper">{styled_table.to_html(escape=False)}</div>', unsafe_allow_html=True)

st.caption("Table shows probability (%) of each team finishing in each position based on 10,000 simulated seasons.")

# -------------------------------
# 11️⃣ DOWNLOAD OPTION

csv = pos_pct_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download table as CSV",
    data=csv,
    file_name=f"{league}_final_positions.csv",
    mime="text/csv",
)

# -------------------------------
# 12️⃣ METHODOLOGY

with st.expander("📌 How this simulation works"):

    st.markdown("""

**Step 1 – Historical Data:** Compile past match results from the 2024/25 and 2025/26 seasons.  

**Step 2 – Betting Odds:** Gather betting odds for upcoming fixtures.  

**Step 3 – Team Strengths:** Estimate offensive and defensive strength.  

**Step 4 – Match Probabilities:** Use betting odds and a Poisson goal model.  

**Step 5 – Full Season Simulation:** Simulate remaining fixtures 10,000 times.  

**Step 6 – Final Probabilities:** Aggregate the simulated league tables.
""")

# -------------------------------
# 13️⃣ ABOUT ME

st.markdown("---")

st.header("About Me")

st.markdown("""
Hi, I'm **Victoria Friss de Kereki**, a Data Scientist working in sports analytics and applied modelling.

I build probabilistic football simulations and predictive models for Europe’s top leagues and write about football data and analytics.
""")

st.markdown("""
📄 [Read my Medium](https://medium.com/@vickyfrissdekereki)  
💼 [LinkedIn](https://www.linkedin.com/in/victoria-friss-de-kereki/)  
✉️ [Email](mailto:vicky_friss@hotmail.com)
""")