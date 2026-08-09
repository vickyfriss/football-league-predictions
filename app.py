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
    display_df = df.copy()

    # -------------------------------
    # SAFE CLEANING ONLY (non-destructive)
    # remove accidental index columns ONLY if they exist
    display_df = display_df.loc[:, ~display_df.columns.astype(str).str.match(r"^(index|Unnamed.*|level_0)$")]

    # DO NOT reset index unless it's actually needed
    display_df = display_df.reset_index(drop=True)

    # -------------------------------
    # TEXT / NUMERIC SPLIT
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
            {"selector": "th", "props":[("background-color","#dfeee2"),("color","#333"),
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

# The CSS below referenced "Inter" as a font-family all along, but nothing ever loaded
# it -- so every element silently fell back to Roboto/Arial. This actually loads it.
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ================================
   DESIGN TOKENS
   Light mode is the deliberate default (grey page, white cards). Dark mode is a
   bonus layered on top via prefers-color-scheme -- everything below reads these
   variables, so redefining them here is the only place dark mode needs to touch.
================================ */
:root {
    --page-bg: #f2f2f2;
    --card-bg: #ffffff;
    --text-main: #222222;
    --card-shadow: 0 2px 10px rgba(0,0,0,0.06);
    --card-shadow-hover: 0 6px 18px rgba(0,0,0,0.10);
    --border-light: #e3e3e3;
    --accent-text: #2E7D32;
}
@media (prefers-color-scheme: dark) {
    :root {
        --page-bg: #121212;
        --card-bg: #1e1e1e;
        --text-main: #e6e6e6;
        --card-shadow: 0 2px 10px rgba(0,0,0,0.45);
        --card-shadow-hover: 0 6px 18px rgba(0,0,0,0.55);
        --border-light: #3a3a3a;
        --accent-text: #66bb6a;
    }
}

/* One consistent typeface everywhere -- native Streamlit widgets included, not
   just the custom HTML sections -- so nothing looks like it belongs to a
   different page. */
.stApp, .stApp * {
    font-family: 'Inter', Roboto, Arial, sans-serif !important;
}

body, .main, .stApp {
    background-color: var(--page-bg) !important;
    color: var(--text-main);
}
h1, h2, h3, .stMarkdown p, .stSelectbox label { text-align: center !important; }

/* Shared white "page section" card -- hero, methodology and about-me all use
   this for a consistent surface, radius and shadow. Each section keeps its own
   inline padding/max-width/margin so widths can still differ on purpose. */
.app-card {
    background-color: var(--card-bg);
    color: var(--text-main);
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.app-card:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-1px); }
.app-card a, .app-card h1, .app-card h3 { color: var(--accent-text); }
.app-card p, .app-card li { color: var(--text-main); }

/* Numbered step badges in the methodology list -- fixed brand green (not a
   dark-mode variable): it's a solid-fill badge with guaranteed white text, so
   it doesn't need to adapt to the page theme the way body text does. */
.step-circle {
    background-color: #2E7D32; color: #fff; font-weight: 600; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    width: 30px; height: 30px; flex-shrink: 0; margin-right: 12px;
    transition: background-color 0.2s ease;
}
li:hover .step-circle { background-color: #245f27; }

/* Small white chip behind each social icon in the About Me footer -- icons are
   fixed-black PNGs, so they need a guaranteed-light backdrop in any theme. */
.icon-chip {
    display: inline-flex; align-items: center; justify-content: center;
    width: 40px; height: 40px; margin: 0 8px;
    background: #ffffff; border-radius: 50%;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    text-decoration: none; transition: transform 0.2s ease;
}
.icon-chip:hover { transform: scale(1.08); }

/* Branded replacement for st.info() -- Streamlit's built-in info box is a fixed
   blue with no easy way to retheme it, so this is a plain styled div instead. */
.status-banner {
    max-width: 900px; margin: 28px auto; padding: 10px 18px;
    background-color: #eaf5ec; border-left: 2px solid #a5d6a7; border-right: 2px solid #a5d6a7;
    border-radius: 8px; color: #245f27; font-size: 14px; text-align: center;
}
@media (prefers-color-scheme: dark) {
    .status-banner { background-color: #1b3320; color: #a5d6a7; }
}

/* Data table: deliberately a fixed light card in any theme, same reasoning as
   the icon chips -- the pandas-rendered cells inside are colour-graded assuming
   a light background, so the frame around them stays light too. */
.table-card {
    background-color: #ffffff;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    padding: 20px 24px;
    width: 100%;
    margin: 28px auto;
}
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

/* ================================
   LEAGUE SELECTBOX
   Fixed light in any theme (deliberate, same as the table/icons above): an
   earlier fix here forced light mode to avoid a Streamlit/baseweb bug where the
   dropdown's hover state rendered pure black and illegible. Restyled to match
   the card language (radius, shadow, border) without touching that fix.
================================ */
div[data-testid="stSelectbox"] {
    max-width: 900px;
    margin: 28px auto !important;
}
div.stSelectbox label {
    color: #333 !important;
}
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    color: #111 !important;
    border-radius: 10px !important;
    border: 1px solid #e3e3e3 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

/* dropdown container + list */
div[data-baseweb="popover"],
div[data-baseweb="menu"],
div[data-baseweb="menu"] ul {
    background-color: #ffffff !important;
}

/* menu items / options */
div[data-baseweb="menu"] li,
div[data-baseweb="menu"] li *,
div[role="option"] {
    background-color: #ffffff !important;
    color: #111 !important;
}

/* hover + keyboard focus */
div[data-baseweb="menu"] li:hover,
div[data-baseweb="menu"] li:hover *,
div[data-baseweb="menu"] li:focus,
div[data-baseweb="menu"] li:focus-visible,
div[role="option"]:hover {
    background-color: #e2f3e4 !important;
    color: #111 !important;
    outline: none !important;
}

/* selected item */
div[data-baseweb="menu"] li[aria-selected="true"],
div[data-baseweb="menu"] li[aria-selected="true"] *,
div[aria-selected="true"] {
    background-color: #c8e6c9 !important;
    color: #111 !important;
    font-weight: 600;
}

/* Top-right contact panel -- also fixed white; same black-icon reasoning */
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

/* Buttons (download button uses this) -- fixed brand green, same reasoning as
   the step-circle badges: solid fill with guaranteed white text. */
div.stButton > button, div[data-testid="stDownloadButton"] button {
    background-color: #2E7D32 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: background-color 0.2s ease;
}
div.stButton > button:hover, div[data-testid="stDownloadButton"] button:hover {
    background-color: #245f27 !important;
    color: #ffffff !important;
}
/* Hide Streamlit's own chrome (hamburger menu, "Deploy" button, "Made with
   Streamlit" footer) -- a polished page shouldn't visibly announce the
   dev tool it was built with. header uses display:none (not visibility) so it
   stops reserving space -- fixed-position elements like #contact-panel are
   positioned relative to the viewport, not the header, so this doesn't move them. */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { display: none; }

/* Streamlit still pads .block-container to make room for that header even
   once it's hidden -- without this the page keeps a large empty gap up top. */
.block-container {
    padding-top: 2rem !important;
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
<div class="app-card" style="padding:28px 32px; max-width:900px; margin:28px auto; text-align:center;">
    <h1 style="margin:0; font-size:34px; font-weight:700; letter-spacing:0.4px;">
        Football League Simulator
    </h1>
    <p style="margin:6px 0 0 0; font-size:14px; font-weight:500; color:#777; letter-spacing:0.3px;">
        by Victoria Friss de Kereki
    </p>
    <div style="height:4px; width:80px; background:#2E7D32; margin:14px auto 20px auto; border-radius:2px;"></div>
    <p style="font-size:16px; line-height:1.7; margin:0;">
        Data-driven forecasts for final positions across football leagues worldwide.<br>
        Simulates every remaining fixture <b>10,000 times</b> and aggregates results into probability tables.
    </p>
    <p style="margin-top:15px; font-weight:600;">
        <a href="https://www.linkedin.com/in/victoria-friss-de-kereki/" target="_blank" style="text-decoration:none;">
        Learn more about the creator & connect →
        </a>
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# 8️⃣ LEAGUE SELECTION

league_display_names = [
    "Premier League (England)",
    "EFL Championship (England 2nd tier)",
    "Serie A (Italy)",
    "La Liga (Spain)",
    "Bundesliga (Germany)",
    "Ligue 1 (France)",
    "Eredivisie (Netherlands)",
    "Serie A (Brazil)"
]
league_key_map = {
    "Premier League (England)": "premierleague_england",
    "EFL Championship (England 2nd tier)": "championship_england",
    "Serie A (Italy)": "seriea_italy",
    "La Liga (Spain)": "laliga_spain",
    "Bundesliga (Germany)": "bundesliga_germany",
    "Ligue 1 (France)": "ligue1_france",
    "Eredivisie (Netherlands)": "eredivisie_netherlands",
    "Serie A (Brazil)": "seriea_brazil"
}

# Temporary default: most leagues haven't kicked off their 2026/27 season yet (0 games
# played), so land on a league that's already actually playing. Eredivisie is mid-season
# while the Premier League etc. are still empty tables. Revert DEFAULT_LEAGUE to
# "Premier League (England)" once the PL season is underway.
DEFAULT_LEAGUE = "Eredivisie (Netherlands)"

selected_display_name = st.selectbox(
    "Select League",
    league_display_names,
    index=league_display_names.index(DEFAULT_LEAGUE)
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
    st.markdown(
        f'<div class="status-banner">Simulations last run on: {pct_mtime.strftime("%d/%B/%Y %H:%M")} UTC</div>',
        unsafe_allow_html=True
    )

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
st.markdown(
    f'<div class="table-card"><div class="table-wrapper">{styled_table.to_html(escape=False)}</div></div>',
    unsafe_allow_html=True
)
st.caption("Table shows probability (%) of each team finishing in each position based on 10,000 simulated seasons.")

# -------------------------------
# 12️⃣ DOWNLOAD OPTION

csv = pos_pct_df.to_csv(index=False).encode("utf-8")
st.download_button("Download table as CSV", data=csv, file_name=f"{league}_final_positions.csv", mime="text/csv")

# -------------------------------
# -------------------------------
# 1️⃣4️⃣ METHODOLOGY
st.markdown("""
<div class="app-card" style="padding:28px 32px; max-width:900px; margin:28px auto;">
<h3 style="margin-bottom:15px;">How This Simulation Works</h3>
<p style="font-size:15px; line-height:1.8;">
This simulation combines <b>historical results</b> and <b>betting odds</b> to estimate match outcome probabilities.  
We then run <b>10,000 Monte Carlo simulations</b> for all remaining fixtures to calculate how likely each team is to finish in each league position.
</p>
<ul style="font-size:15px; line-height:1.8; padding-left:0; list-style:none; border-left:3px solid #2E7D32; margin-top:20px;">
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">1</div>
<div><b>Historical Data:</b> Collect current standings via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">2</div>
<div><b>Fixtures:</b> Historical match results and remaining fixtures obtained via the <a href="https://www.football-data.org/" target="_blank">Football-Data.org API</a>.</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">3</div>
<div><b>Betting Odds:</b> Incorporate market expectations from <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> to boost accuracy.</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">4</div>
<div><b>Team Strengths:</b> Estimate attacking and defensive strengths for each team.</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">5</div>
<div><b>Match Probabilities:</b> Generate outcome probabilities using Poisson and betting-based models.</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">6</div>
<div><b>Monte Carlo Simulations:</b> Run 10,000 full season simulations to cover all possible scenarios.</div>
</li>
<li style="margin-bottom:0; display:flex; align-items:flex-start;">
<div class="step-circle">7</div>
<div><b>Final Positions:</b> Aggregate the simulation results into probability distributions.</div>
</li>
</ul>
</div>
""", unsafe_allow_html=True)


# -------------------------------
# 14️⃣ BOTTOM ABOUT ME

st.markdown("""
<div id="about-me" class="app-card" style="padding:35px 25px; max-width:700px; 
            margin:28px auto; text-align:center; font-size:18px; line-height:1.8;">
<h3 style="font-size:28px; margin-bottom:15px;">About Me</h3>
<p>Hi, I’m <b>Victoria Friss de Kereki</b>, a <b>Football Data Analyst</b> turning football data into <b>data-driven insights</b>, with a growing focus on probabilistic modelling and simulation.</p>
<p>I build <b>data-driven insights</b>, <b>probabilistic simulations</b>, and <b>predictive models</b> to help sports organisations and analysts make informed decisions backed by data.</p>
<p>My work can be explored on <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, where I share projects on football analytics, player performance, and simulations.</p>
<p style="margin-top:20px; font-size:19px; font-weight:600; color:var(--accent-text);">
Interested in collaborating or discussing sports analytics? <br><b>Let’s connect!</b>
</p>
<div style="margin-top:20px;">
<a href="mailto:vicky_friss@hotmail.com" class="icon-chip">
  <img src="https://img.icons8.com/ios-filled/20/000000/new-post.png"/>
</a>
<a href="https://www.linkedin.com/in/victoria-friss-de-kereki/" target="_blank" class="icon-chip">
  <img src="https://img.icons8.com/ios-filled/20/000000/linkedin.png"/>
</a>
<a href="https://medium.com/@vickyfrissdekereki" target="_blank" class="icon-chip">
  <img src="https://img.icons8.com/ios-filled/20/000000/medium-monogram.png"/>
</a>
<a href="https://github.com/vickyfriss" target="_blank" class="icon-chip">
  <img src="https://img.icons8.com/ios-filled/20/000000/github.png"/>
</a>
</div>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# 15️⃣ FOOTER
st.markdown("""
<div style="text-align:center; padding:10px 0 30px 0; font-size:13px; color:#999;">
    © 2026 Victoria Friss de Kereki &middot; Built with Python, pandas & Streamlit
</div>
""", unsafe_allow_html=True)