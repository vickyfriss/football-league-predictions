# -------------------------------
# 1️⃣ IMPORTS
import streamlit as st
import pickle
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# -------------------------------
# 2️⃣ HELPER FUNCTIONS FOR STYLING

# Soft green colormap
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
    vmax = max(display_df[num_cols].max().max(), 1)
    color_data = display_df[num_cols].divide(vmax).apply(lambda s: s.map(color_scale)) * vmax

    styled = (
        display_df.style
        .background_gradient(cmap=green_cmap, vmin=0, vmax=vmax, gmap=color_data, axis=None)
        .applymap(zero_style, subset=num_cols)
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
                                         ("text-align","center"),("font-family","Inter, Roboto, Arial, sans-serif"),
                                         ("font-size","13px"),("font-weight","600")]},
            {"selector": "tr", "props":[("height","25px")]},
            {"selector": "th:nth-child(4), td:nth-child(4)", "props":[("border-right","2px solid #999")]},
            {"selector": "td:nth-child(-n+4)", "props":[("border-bottom","1px solid #ccc")]},
            {"selector": "tr:nth-child(odd) td:nth-child(-n+4)", "props":[("background-color","#f9f9f9")]},
            {"selector": "tr:nth-child(even) td:nth-child(-n+4)", "props":[("background-color","#f2f2f2")]}
        ])
    )
    return styled

# -------------------------------
# 3️⃣ STREAMLIT APP

st.set_page_config(page_title="Football League Simulation", layout="wide")
st.title("⚽ Football League Monte Carlo Simulation")

# Load pickle
st.info("⏳ Loading precomputed simulation results...")
try:
    with open("data/precomputed_pos_counts.pkl","rb") as f:
        position_distribution_all = pickle.load(f)
    with open("data/precomputed_pos_pct.pkl","rb") as f:
        position_distribution_pct_all = pickle.load(f)
    st.success("✅ Precomputed results loaded.")
except Exception as e:
    st.error(f"❌ Failed to load precomputed results: {e}")
    st.stop()

# -------------------------------
# Friendly league names + mapping to pickle keys
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
# Display league table
pos_pct_df = position_distribution_pct_all[league].copy().reset_index()

if isinstance(pos_pct_df.columns, pd.MultiIndex):
    pos_pct_df.columns = [str(c) for c in pos_pct_df.columns]

for col in ["POS","TEAM","GP","PTS"]:
    if col not in pos_pct_df.columns:
        pos_pct_df[col] = pos_pct_df.index + 1 if col=="POS" else 0 if col in ["GP","PTS"] else pos_pct_df.index.astype(str)

pos_pct_df["TEAM"] = pos_pct_df["TEAM"].astype(str)
pos_pct_df["POS"] = pos_pct_df["POS"].astype(int)
pos_pct_df["GP"] = pos_pct_df["GP"].astype(int)
pos_pct_df["PTS"] = pos_pct_df["PTS"].astype(int)

st.header(f"🏆 {selected_display_name} Simulation Results")
st.write("Styled probabilities table for league positions:")

styled_table = style_probabilities_table(pos_pct_df)
st.markdown(styled_table.to_html(escape=False), unsafe_allow_html=True)