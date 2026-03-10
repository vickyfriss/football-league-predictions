# -------------------------------
# 1️⃣ IMPORTS
import streamlit as st
import pickle
import pandas as pd
import numpy as np
import os
import time
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
    return "background-color: white !important;" if val < 1 else ""

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
            {"selector": "th", "props":[("background-color","#dfe7ee"),("color","#333"),
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

@st.cache_data(ttl=0, show_spinner=False)
def load_simulation_data():
    pct_file = "data/precomputed_pos_pct.pkl"
    timeout = 10
    start_time = time.time()
    while not os.path.exists(pct_file) and time.time() - start_time < timeout:
        time.sleep(0.5)
    if not os.path.exists(pct_file):
        return {}
    try:
        with open(pct_file, "rb") as f:
            return pickle.load(f)
    except Exception:
        return {}

# ------------------------------- 
# 5️⃣ PAGE STYLING + SELECTBOX + CONTACT PANEL

st.markdown("""
<style>
body, .main { background-color: #f2f2f2; font-family: Inter, Roboto, Arial, sans-serif; }
h1, h2, h3, .stMarkdown p, .stSelectbox label { text-align: center !important; }

/* Table wrapper remains scrollable */
div.table-wrapper { width: 100%; overflow-x: auto; }

/* Desktop: normal table, nothing changes */
@media (min-width: 601px) {
    table { width: 100%; border-collapse: collapse; }
    th, td { overflow: visible !important; white-space: normal !important; text-align: center !important; font-size: 14px !important; padding: 4px 6px !important; }
    th:nth-child(2), td:nth-child(2) { text-align: left !important; min-width: 150px; }
    th:nth-child(1), td:nth-child(1) { width: 40px; }
    th:nth-child(3), td:nth-child(3) { min-width: 50px; }
    th:nth-child(4), td:nth-child(4) { min-width: 50px; }
    th:nth-child(n+5), td:nth-child(n+5) { min-width: 60px; }
}

/* Mobile: fix first two columns when scrolling horizontally */
@media (max-width: 600px) {
    table { width: 100%; border-collapse: collapse; }
    th, td { white-space: nowrap; }

    /* Sticky first column: POS */
    th:nth-child(1), td:nth-child(1) {
        position: sticky;
        left: 0;
        z-index: 3;
        background-color: inherit;
    }

    /* Sticky second column: TEAM */
    th:nth-child(2), td:nth-child(2) {
        position: sticky;
        left: 40px; /* match the width of the POS column */
        z-index: 2;
        background-color: inherit;
        text-align: left !important;
    }
}

/* Simulation methodology styling */
.sim-step { background-color: #ffffff; border-left: 4px solid #1f77b4; padding: 10px 15px; margin-bottom: 10px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.sim-step h4 { margin: 0 0 4px 0; font-weight: 600; color: #1f77b4; }
.sim-step p { margin: 0; font-size: 14px; line-height: 1.5; color: #333; }

/* Top-right contact panel */
#contact-panel { 
    position: fixed; 
    top: 60px;              
    right: 20px; 
    background-color: #ffffff; 
    padding: 10px 12px; 
    border-radius: 10px; 
    box-shadow: 0 2px 6px rgba(0,0,0,0.15); 
    z-index: 100; 
    display: flex; 
    flex-direction: column; 
    align-items: center; 
}
#contact-panel a { margin: 8px 0; text-decoration: none; transition: transform 0.2s; }
#contact-panel a:first-child { margin-top: 4px; }
#contact-panel a:hover img { transform: scale(1.3); }

/* Style the selectbox container like a card */
div.stSelectbox > div[role="combobox"] {
    background-color: #ffffff !important;
    padding: 12px 20px !important;
    border-radius: 10px !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
    max-width: 300px !important;
    margin: 10px auto !important;
}
div.stSelectbox > div[role="combobox"] > div {
    font-size: 16px !important;
    font-weight: 500 !important;
    color: #1f77b4 !important;
    text-align: center !important;
}
div.stSelectbox svg { fill: #1f77b4 !important; }

/* Responsive adjustments for other elements */
@media (max-width: 600px) {
    /* Horizontal top-right bar with margin from top */
    #contact-panel { flex-direction: row; top: 50px; right: 10px; padding: 8px 10px; border-radius: 8px; }
    #contact-panel a { margin: 0 8px; }
    #contact-panel a:first-child { margin-left: 0; }
    #contact-panel a img { width: 24px !important; height: 24px !important; }

    /* Selectbox smaller on mobile */
    div.stSelectbox > div[role="combobox"] {
        max-width: 220px !important;
        padding: 8px 12px !important;
    }
    div.stSelectbox > div[role="combobox"] > div { font-size: 14px !important; }
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 6️⃣ TOP-RIGHT CONTACT PANEL

st.markdown("""
<div id="contact-panel">
    <a href="mailto:vicky_friss@hotmail.com" title="Email">
        <img src="https://img.icons8.com/ios-filled/30/000000/new-post.png"/>
    </a>
    <a href="https://www.linkedin.com/in/victoria-friss-de-kereki/" target="_blank" title="LinkedIn">
        <img src="https://img.icons8.com/ios-filled/30/000000/linkedin.png"/>
    </a>
    <a href="https://medium.com/@vickyfrissdekereki" target="_blank" title="Medium">
        <img src="https://img.icons8.com/ios-filled/30/000000/medium-monogram.png"/>
    </a>
    <a href="https://github.com/vickyfriss" target="_blank" title="GitHub">
        <img src="https://img.icons8.com/ios-filled/30/000000/github.png"/>
    </a>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# 7️⃣ HERO SECTION

st.markdown("""
<div style="background: linear-gradient(90deg, #f9fbff, #ffffff); padding:25px 30px; 
            border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.1); max-width:920px; 
            margin:auto; text-align:center; font-family:Inter, Roboto, Arial, sans-serif;">
    <h1 style="margin:0; font-size:36px; font-weight:700; color:#1f77b4; letter-spacing:1px; text-transform:uppercase;">
        Football League Simulator
    </h1>
    <div style="height:4px; width:80px; background:#1f77b4; margin:10px auto 20px auto; border-radius:2px;"></div>
    <p style="font-size:16px; line-height:1.7; color:#333; margin:0;">
        Data-driven forecasts for final positions across Europe’s top 5 football leagues (2025-26).<br>
        Simulates every remaining fixture <b>10,000 times</b> and aggregates results into probability tables.
    </p>
    <p style="margin-top:15px; font-weight:600; color:#1f77b4;">
        <a href="https://www.linkedin.com/in/victoria-friss-de-kereki/" target="_blank" style="text-decoration:none; color:#1f77b4;">
        Learn more about the creator & connect →
        </a>
    </p>
</div>
""", unsafe_allow_html=True)

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

selected_display_name = st.selectbox(
    "Select League",
    league_display_names,
    index=0
)
league = league_key_map[selected_display_name]

# -------------------------------
# 9️⃣ LOAD SIMULATION DATA

with st.spinner("Loading simulation data..."):
    position_distribution_pct_all = load_simulation_data()

if not position_distribution_pct_all:
    st.warning("⚠️ Simulation data not ready yet. Please reload later.")
else:
    pct_file = "data/precomputed_pos_pct.pkl"
    pct_mtime = datetime.fromtimestamp(os.path.getmtime(pct_file), tz=timezone.utc)
    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    st.info(f"Simulations last run on: {pct_mtime.strftime('%d/%B/%Y %H:%M')} UTC")

# -------------------------------
# 10️⃣ PREPARE DATAFRAME

if position_distribution_pct_all and league in position_distribution_pct_all:
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

st.header(f"{selected_display_name} Simulation Results")

# -------------------------------
# 11️⃣ STYLE AND DISPLAY TABLE

styled_table, num_cols = style_probabilities_table(pos_pct_df)
st.markdown(f'<div class="table-wrapper">{styled_table.to_html(escape=False)}</div>', unsafe_allow_html=True)
st.caption("Table shows probability (%) of each team finishing in each position based on 10,000 simulated seasons.")

# -------------------------------
# 12️⃣ DOWNLOAD OPTION

csv = pos_pct_df.to_csv(index=False).encode("utf-8")
st.download_button("Download table as CSV", data=csv, file_name=f"{league}_final_positions.csv", mime="text/csv")

# -------------------------------
# -------------------------------
# 1️⃣4️⃣ METHODOLOGY
st.markdown("""
<div style="background-color:#fff; padding:25px 30px; border-radius:10px; box-shadow:0 3px 6px rgba(0,0,0,0.1); max-width:920px; margin:auto; margin-top:30px;">
<h3 style="color:#1f77b4; margin-bottom:15px;">📌 How This Simulation Works</h3>
<p style="font-size:15px; line-height:1.8; color:#333;">
This simulation combines <b>historical results</b> and <b>betting odds</b> to estimate match outcome probabilities.  
We then run <b>10,000 Monte Carlo simulations</b> for all remaining fixtures to calculate how likely each team is to finish in each league position.
</p>
<ul style="font-size:15px; line-height:1.8; color:#333; padding-left:0; list-style:none; border-left:3px solid #1f77b4; margin-top:20px;">
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div style='background-color:#1f77b4;color:#fff;font-weight:600;border-radius:50%;display:flex;align-items:center;justify-content:center;width:30px;height:30px;flex-shrink:0;margin-right:12px;'>1</div>
<div><b>Historical Data:</b> Collect current standings via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2025" target="_blank">ESPN</a>).</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div style='background-color:#1f77b4;color:#fff;font-weight:600;border-radius:50%;display:flex;align-items:center;justify-content:center;width:30px;height:30px;flex-shrink:0;margin-right:12px;'>2</div>
<div><b>Fixtures:</b> Historical match results and remaining fixtures obtained via the <a href="https://www.football-data.org/" target="_blank">Football-Data API</a>.</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div style='background-color:#1f77b4;color:#fff;font-weight:600;border-radius:50%;display:flex;align-items:center;justify-content:center;width:30px;height:30px;flex-shrink:0;margin-right:12px;'>3</div>
<div><b>Betting Odds:</b> Incorporate market expectations from <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> to boost accuracy.</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div style='background-color:#1f77b4;color:#fff;font-weight:600;border-radius:50%;display:flex;align-items:center;justify-content:center;width:30px;height:30px;flex-shrink:0;margin-right:12px;'>4</div>
<div><b>Team Strengths:</b> Estimate attacking and defensive strengths for each team.</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div style='background-color:#1f77b4;color:#fff;font-weight:600;border-radius:50%;display:flex;align-items:center;justify-content:center;width:30px;height:30px;flex-shrink:0;margin-right:12px;'>5</div>
<div><b>Match Probabilities:</b> Generate outcome probabilities using Poisson and betting-based models.</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div style='background-color:#1f77b4;color:#fff;font-weight:600;border-radius:50%;display:flex;align-items:center;justify-content:center;width:30px;height:30px;flex-shrink:0;margin-right:12px;'>6</div>
<div><b>Monte Carlo Simulations:</b> Run 10,000 full season simulations to cover all possible scenarios.</div>
</li>
<li style="margin-bottom:0; display:flex; align-items:flex-start;">
<div style='background-color:#1f77b4;color:#fff;font-weight:600;border-radius:50%;display:flex;align-items:center;justify-content:center;width:30px;height:30px;flex-shrink:0;margin-right:12px;'>7</div>
<div><b>Final Positions:</b> Aggregate the simulation results into probability distributions.</div>
</li>
</ul>
</div>
""", unsafe_allow_html=True)


# -------------------------------
# 14️⃣ BOTTOM ABOUT ME

st.markdown("""
<div id="about-me" style="background: #f0f7ff; padding:35px 25px; border-radius:10px; max-width:700px; 
            margin:auto; text-align:center; font-size:18px; line-height:1.8; margin-top:50px; margin-bottom:60px;">
<h3 style="color:#1f77b4; font-size:28px; margin-bottom:15px;">About Me</h3>
<p>Hi, I’m <b>Victoria Friss de Kereki</b>, an Applied Data Scientist specialising in <b>sports analytics</b> and performance insights.</p>
<p>I build <b>probabilistic simulations</b>, <b>predictive models</b>, and <b>data-driven insights</b> to help sports organisations and analysts make informed decisions backed by data.</p>
<p>My work can be explored on <a href="https://medium.com/@vickyfrissdekereki" target="_blank" style="color:#1f77b4;">Medium</a>, where I share projects on football analytics, player performance, and simulations.</p>
<p style="margin-top:20px; font-size:19px; font-weight:600; color:#1f77b4;">
Interested in collaborating, hiring, or discussing sports analytics? <br><b>Let’s connect!</b>
</p>
<div style="margin-top:20px;">
<a href="mailto:vicky_friss@hotmail.com" style="margin:0 15px; text-decoration:none;">
  <img src="https://img.icons8.com/ios-filled/30/000000/new-post.png"/>
</a>
<a href="https://www.linkedin.com/in/victoria-friss-de-kereki/" target="_blank" style="margin:0 15px; text-decoration:none;">
  <img src="https://img.icons8.com/ios-filled/30/000000/linkedin.png"/>
</a>
<a href="https://medium.com/@vickyfrissdekereki" target="_blank" style="margin:0 15px; text-decoration:none;">
  <img src="https://img.icons8.com/ios-filled/30/000000/medium-monogram.png"/>
</a>
<a href="https://github.com/vickyfriss" target="_blank" style="margin:0 15px; text-decoration:none;">
  <img src="https://img.icons8.com/ios-filled/30/000000/github.png"/>
</a>
</div>
</div>
""", unsafe_allow_html=True)