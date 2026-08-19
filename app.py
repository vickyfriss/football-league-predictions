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

html {
    /* Reserves the scrollbar's width permanently instead of only when a
       scrollbar happens to be showing -- otherwise centered content can sit a
       few pixels left of true-center, since the scrollbar only ever eats into
       the right edge. */
    scrollbar-gutter: stable;
}
body, .main, .stApp {
    background-color: var(--page-bg) !important;
    color: var(--text-main);
}
h1, h2, h3, .stMarkdown p, .stSelectbox label { text-align: center !important; }

/* Streamlit auto-adds an anchor-link icon to every heading (h1/h2/h3) for
   in-page linking. It's invisible until hover, but still reserves layout
   space next to the text -- which is exactly why headings specifically
   looked slightly left-of-center while plain paragraphs (no anchor icon)
   centered correctly. Removing it entirely also frees the space it reserved. */
[data-testid="stHeaderActionElements"] {
    display: none !important;
}
h1 a[href^="#"], h2 a[href^="#"], h3 a[href^="#"] {
    display: none !important;
}

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
.app-card h3 { font-size: 22px; font-weight: 700; }
.app-card p, .app-card li { color: var(--text-main); font-size: 16px; line-height: 1.7; }

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

/* Desktop: freeze the first four columns (POS, TEAM, GP, PTS) while
   scrolling horizontally through the position-percentage columns -- same
   sticky technique as the mobile block below, just extended from two
   columns to four since desktop has the width to spare and a 20-column
   table otherwise loses the team/points context off-screen to the left.
   Fixed (not min-) widths on the frozen columns are required here, not
   just cosmetic -- each one's sticky "left" offset is the running total of
   the widths before it, so if a column were allowed to grow past its
   assumed width the next one's offset would be wrong and they'd overlap. */
@media (min-width: 601px) {
    /* table-layout:fixed is what makes the explicit widths below (and so the
       sticky "left" offsets, which are a running total of them) reliable --
       under the default "auto" layout the browser sizes columns from their
       content instead and silently shrinks a specified width below what's
       asked for (measured: a 170px TEAM column collapsed to 83px for a short
       name like "Espanyol"), which desyncs every offset after it and makes
       the frozen columns overlap the scrolling ones. */
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    th, td { overflow: visible !important; white-space: normal !important; text-align: center !important; font-size: 14px !important; padding: 4px 6px !important; }

    /* Every column except TEAM must never wrap -- a wrapped cell makes its
       whole row taller, which looks broken for a results table. Widths below
       are sized from the actual rendered font (measured against the live
       page, 14px/600 for headers, 14px/500 for data): "100.00%" -- the
       longest a percentage cell can ever be -- needs ~71px including the
       6px+6px cell padding, so 78px leaves real headroom rather than being
       exactly on the edge like the previous 60px (which is why cells were
       wrapping to "12.26" / "%" on two lines). Same story for "POS": the
       header text alone needs ~41px, more than the previous 40px column. */
    th:nth-child(n+5), td:nth-child(n+5) { width: 78px; white-space: nowrap !important; }

    th:nth-child(1), td:nth-child(1) {
        width: 46px; white-space: nowrap !important;
        position: sticky; left: 0; z-index: 4; background-color: inherit;
    }
    th:nth-child(2), td:nth-child(2) {
        width: 170px; text-align: left !important;
        position: sticky; left: 46px; z-index: 3; background-color: inherit;
    }
    th:nth-child(3), td:nth-child(3) {
        width: 42px; white-space: nowrap !important;
        position: sticky; left: 216px; z-index: 2; background-color: inherit;
    }
    th:nth-child(4), td:nth-child(4) {
        width: 46px; white-space: nowrap !important;
        position: sticky; left: 258px; z-index: 1; background-color: inherit;
    }
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
   LEAGUE PILL BUTTONS (built from plain st.button, not st.segmented_control)
   segmented_control's internal styling proved too hard to reliably override --
   two attempts at its selected-state color and width both lost to Streamlit's
   own internal CSS. st.button is what the download button already renders
   correctly with in this exact environment, so the pill row is built from
   st.button + st.columns instead: full page width and even spacing come for
   free from st.columns (real layout, not a style override), and un/selected
   look comes from Streamlit's own long-established primary/secondary button
   "kind" attribute rather than a newer widget's internals.
================================ */
div.stButton > button[kind="secondary"] {
    background-color: #ffffff !important;
    color: #333 !important;
    border: 1px solid #e3e3e3 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    font-weight: 500 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: #e2f3e4 !important;
    color: #111 !important;
    border-color: #a5d6a7 !important;
}
/* Selected league pill */
div.stButton > button[kind="primary"] {
    background-color: #2E7D32 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #245f27 !important;
    color: #ffffff !important;
}
/* Every pill label is "League name\n\nCODE" so they're all the same shape
   regardless of how long the league name is (previously sized by whatever
   text happened to wrap to, so some pills looked bigger than others).
   Streamlit renders the \n\n as a real markdown paragraph break (confirmed --
   the two-line layout itself works), but that means each line is its own <p>
   with the browser's default paragraph margin, which showed up as a visible
   blank line between them. Zeroing that margin keeps the two lines but
   removes the gap; white-space:pre-line is a safety net for any Streamlit
   version that renders the label as plain text instead. */
div.stButton > button {
    /* Fixed (not just minimum) height, tall enough for a name that wraps to
       two lines (e.g. "Premier League" once Primeira Liga's addition
       narrowed each column) -- otherwise that one pill grows past the
       others' natural single-line height instead of them matching it.
       Flex-centering keeps shorter single-line labels looking centered in
       the taller box rather than stuck at the top. */
    height: 78px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    white-space: pre-line;
    line-height: 1.3;
    text-align: center;
}
div.stButton > button p {
    margin: 0 !important;
}
div.stButton > button p:last-child {
    margin-top: 2px !important;
    font-size: 13px;
    opacity: 0.8;
}

/* Mobile: st.columns stacks into 8 full-width rows below Streamlit's own
   responsive breakpoint by default -- that's a lot of vertical space for a
   league picker. A horizontally-scrolling row (tried first) has a real
   discoverability problem -- nothing signals there are more options off-
   screen to the right. With every pill now a fixed, uniform size, 8 leagues
   divides evenly into a 2-column grid instead -- every option visible at
   once, no scrolling, no hidden state. */
@media (max-width: 600px) {
    div[data-testid="stHorizontalBlock"]:has(div.stButton) {
        flex-wrap: wrap !important;
        gap: 8px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div.stButton) > div[data-testid="stColumn"] {
        flex: 0 0 calc(50% - 4px) !important;
        width: calc(50% - 4px) !important;
        min-width: unset !important;
    }
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

}

/* Download button -- always solid green regardless of primary/secondary kind
   (it's the only stDownloadButton on the page, no need to differentiate it). */
div[data-testid="stDownloadButton"] button {
    background-color: #2E7D32 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: background-color 0.2s ease;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #245f27 !important;
    color: #ffffff !important;
}
div.stButton > button {
    border-radius: 8px !important;
    transition: background-color 0.2s ease;
}
/* Hide Streamlit's own chrome (hamburger menu, "Deploy" button, "Made with
   Streamlit" footer) -- a polished page shouldn't visibly announce the
   dev tool it was built with. display:none (not visibility) so nothing keeps
   reserving space -- fixed-position elements like #contact-panel are
   positioned relative to the viewport, not the header, so this doesn't move them.
   Plain tag selectors AND the newer data-testid ones are both included since
   which one actually matches has changed across Streamlit versions. */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { display: none; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

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
    <h1 style="margin:0; font-size:34px; font-weight:700;">
        Football League Simulator
    </h1>
    <p style="margin:6px 0 0 0; font-size:14px; font-weight:500; color:#777;">
        by Victoria Friss de Kereki
    </p>
    <div style="height:4px; width:80px; background:#2E7D32; margin:14px auto 20px auto; border-radius:2px;"></div>
    <p style="margin:0;">
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

# (internal key, two-line pill label, clean single-line label for the header below).
# Every pill is forced into the same "name / code" shape on purpose -- before this,
# pills were sized by whatever their label happened to wrap to, which made some
# look bigger than others. "ENG2" (not "ENG 2") to match the punctuation-free,
# compact code style of the other tags.
LEAGUES = [
    ("premierleague_england", "**Premier League**\n\nENG", "Premier League (ENG)"),
    ("championship_england", "**Championship**\n\nENG2", "Championship (ENG2)"),
    ("seriea_italy", "**Serie A**\n\nITA", "Serie A (ITA)"),
    ("laliga_spain", "**La Liga**\n\nESP", "La Liga (ESP)"),
    ("bundesliga_germany", "**Bundesliga**\n\nGER", "Bundesliga (GER)"),
    ("ligue1_france", "**Ligue 1**\n\nFRA", "Ligue 1 (FRA)"),
    ("eredivisie_netherlands", "**Eredivisie**\n\nNED", "Eredivisie (NED)"),
    ("primeiraliga_portugal", "**Primeira Liga**\n\nPOR", "Primeira Liga (POR)"),
    ("seriea_brazil", "**Serie A**\n\nBRA", "Serie A (BRA)"),
]
league_header_labels = {key: header for key, pill, header in LEAGUES}

# Temporary default: most leagues haven't kicked off their 2026/27 season yet (0 games
# played), so land on a league that's already actually playing. La Liga kicked off
# 2026-08-15, while the Premier League etc. are still empty tables. Revert
# DEFAULT_LEAGUE_KEY to "premierleague_england" once the PL season is underway.
DEFAULT_LEAGUE_KEY = "laliga_spain"

# Built from plain st.button + st.columns rather than st.segmented_control --
# see the CSS comment above for why. st.columns naturally divides the full
# available width evenly, which is also what gives this the same width as the
# table below without any CSS width-fighting.
if "selected_league" not in st.session_state:
    st.session_state.selected_league = DEFAULT_LEAGUE_KEY

league_cols = st.columns(len(LEAGUES))
for col, (key, pill_label, header_label) in zip(league_cols, LEAGUES):
    with col:
        is_active = st.session_state.selected_league == key
        if st.button(
            pill_label,
            key=f"league_btn_{key}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.selected_league = key
            st.rerun()

league = st.session_state.selected_league
selected_display_name = league_header_labels[league]


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
<p>
This simulation combines <b>historical results</b> and <b>betting odds</b> to estimate match outcome probabilities.  
We then run <b>10,000 Monte Carlo simulations</b> for all remaining fixtures to calculate how likely each team is to finish in each league position.
</p>
<ul style="padding-left:0; list-style:none; border-left:3px solid #2E7D32; margin-top:20px;">
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
<div id="about-me" class="app-card" style="padding:28px 32px; max-width:900px; 
            margin:28px auto; text-align:center;">
<h3 style="margin-bottom:15px;">About Me</h3>
<p>Hi, I’m <b>Victoria Friss de Kereki</b>, a <b>Football Data Analyst</b> turning football data into <b>data-driven insights</b>, with a growing focus on probabilistic modelling and simulation.</p>
<p>I build <b>data-driven insights</b>, <b>probabilistic simulations</b>, and <b>predictive models</b> to help sports organisations and analysts make informed decisions backed by data.</p>
<p>My work can be explored on <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, where I share projects on football analytics, player performance, and simulations.</p>
<p style="margin-top:20px; font-size:17px; font-weight:600; color:var(--accent-text);">
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
    © 2026 Victoria Friss de Kereki &middot; Built with Python & Streamlit
</div>
""", unsafe_allow_html=True)