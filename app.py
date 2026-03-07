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

# Midpoint and max for visual scaling
mid_pct = 0.14
max_pct = 0.75

def zero_style(val):
    """Make very low probabilities white."""
    if val < 1:
        return "background-color: white !important;"
    return ""

def color_scale(val, mid=mid_pct, max_val=max_pct):
    """
    Scale values 0–max_val so that:
    - small values → very light
    - mid values (mid_pct) → mid-green
    - >= max_val → full green
    """
    if val >= max_val:
        return 1.0
    elif val <= mid:
        return val / mid * 0.5
    else:
        return 0.5 + (val - mid) / (max_val - mid) * 0.5

def style_probabilities_table(df):
    """
    Apply full custom styling like Jupyter notebook version.
    Returns a Pandas Styler object.
    """
    display_df = df.copy()
    display_df = display_df.reset_index(drop=True)

    text_cols = ["POS", "TEAM", "GP", "PTS"]
    num_cols = display_df.columns.difference(text_cols)

    # Scale numeric columns
    vmax = max(display_df[num_cols].max().max(), 1)
    color_data = display_df[num_cols].divide(vmax).apply(lambda s: s.map(color_scale)) * vmax

    styled = (
        display_df.style
        # Gradient on numeric columns
        .background_gradient(cmap=green_cmap, vmin=0, vmax=vmax, gmap=color_data, axis=None)
        .applymap(zero_style, subset=num_cols)
        .format({col: "{:.2f}%" for col in num_cols})
        # Text columns formatting
        .set_properties(subset=["POS", "GP", "PTS"], **{
            "text-align": "center",
            "font-family": "Inter, Roboto, Arial, sans-serif",
            "font-size": "12px",
            "font-weight": "600",
            "color": "#000",
            "white-space": "nowrap"
        })
        .set_properties(subset=["TEAM"], **{
            "text-align": "left",
            "font-family": "Inter, Roboto, Arial, sans-serif",
            "font-size": "12px",
            "font-weight": "600",
            "color": "#000",
            "white-space": "nowrap"
        })
        # Numeric columns formatting
        .set_properties(subset=num_cols, **{
            "text-align": "center",
            "font-family": "Inter, Roboto, Arial, sans-serif",
            "font-size": "12px",
            "font-weight": "500",
            "color": "#000"
        })
        .hide(axis="index")
        # Table headers, row height, borders, zebra striping
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#e6edf4"),
                ("color", "#333"),
                ("text-align", "center"),
                ("font-family", "Inter, Roboto, Arial, sans-serif"),
                ("font-size", "13px"),
                ("font-weight", "600")
            ]},
            {"selector": "tr", "props": [("height", "25px")]},
            {"selector": "th:nth-child(4), td:nth-child(4)", "props": [
                ("border-right", "2px solid #999")
            ]},
            {"selector": "td:nth-child(-n+4)", "props": [
                ("border-bottom", "1px solid #ccc")
            ]},
            {"selector": "tr:nth-child(odd) td:nth-child(-n+4)", "props": [
                ("background-color", "#f9f9f9")
            ]},
            {"selector": "tr:nth-child(even) td:nth-child(-n+4)", "props": [
                ("background-color", "#f2f2f2")
            ]}
        ])
    )
    return styled

# -------------------------------
# 3️⃣ STREAMLIT APP

st.set_page_config(page_title="Football League Simulation", layout="wide")
st.title("⚽ Football League Monte Carlo Simulation")

# --- Load precomputed results ---
st.info("⏳ Loading precomputed simulation results...")

try:
    with open("data/precomputed_pos_counts.pkl", "rb") as f:
        position_distribution_all = pickle.load(f)
    with open("data/precomputed_pos_pct.pkl", "rb") as f:
        position_distribution_pct_all = pickle.load(f)
    st.success("✅ Precomputed results loaded.")
except Exception as e:
    st.error(f"❌ Failed to load precomputed results: {e}")
    st.stop()

# --- Select League ---
leagues = list(position_distribution_pct_all.keys())
league = st.selectbox("Select League", leagues)

# -------------------------------
# 4️⃣ DISPLAY SELECTED LEAGUE

# Convert to DataFrame for display
pos_pct_df = position_distribution_pct_all[league].copy()
pos_pct_df = pos_pct_df.reset_index()

# Fix MultiIndex if present
if isinstance(pos_pct_df.columns, pd.MultiIndex):
    pos_pct_df.columns = [str(c) for c in pos_pct_df.columns]

# Create columns POS, TEAM, GP, PTS if missing in index
if "POS" not in pos_pct_df.columns:
    pos_pct_df["POS"] = pos_pct_df.index + 1
if "TEAM" not in pos_pct_df.columns:
    pos_pct_df["TEAM"] = pos_pct_df.index.astype(str)
if "GP" not in pos_pct_df.columns:
    pos_pct_df["GP"] = 0
if "PTS" not in pos_pct_df.columns:
    pos_pct_df["PTS"] = 0

# Ensure types
pos_pct_df["TEAM"] = pos_pct_df["TEAM"].astype(str)
pos_pct_df["POS"] = pos_pct_df["POS"].astype(int)
pos_pct_df["GP"] = pos_pct_df["GP"].astype(int)
pos_pct_df["PTS"] = pos_pct_df["PTS"].astype(int)

st.header(f"🏆 {league.replace('_',' ').title()} Simulation Results")
st.write("Styled probabilities table for league positions:")

# -------------------------------
# 5️⃣ STYLE AND DISPLAY FULL TABLE WITH GRADIENTS

styled_table = style_probabilities_table(pos_pct_df)

# Render as HTML to preserve gradient colors and full table
st.markdown(
    styled_table.to_html(escape=False),
    unsafe_allow_html=True
)