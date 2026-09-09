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
# 2️⃣.5 INTERNATIONALISATION (English / Spanish / Brazilian Portuguese)
# League names (Premier League, La Liga, Bundesliga, etc.) and country codes are
# never translated -- they're proper nouns used the same way across languages
# in football media everywhere. Only page chrome (labels, headings, captions) is.

MONTH_NAMES = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "es": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
           "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
    "pt-BR": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
              "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
    "fr": ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet",
           "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
}

COLUMN_LABELS = {
    "en": {"POS": "POS", "TEAM": "TEAM", "GP": "GP", "PTS": "PTS"},
    "es": {"POS": "POS", "TEAM": "EQUIPO", "GP": "PJ", "PTS": "PTS"},
    "pt-BR": {"POS": "POS", "TEAM": "TIME", "GP": "J", "PTS": "PTS"},
    "fr": {"POS": "POS", "TEAM": "ÉQUIPE", "GP": "MJ", "PTS": "PTS"},
}

TRANSLATIONS = {
    "en": {
        "hero_title": "Football League Simulator",
        "hero_byline": "by Victoria Friss de Kereki",
        "hero_description": (
            "Data-driven forecasts for final positions across football leagues worldwide.<br>"
            "Simulates every remaining fixture <b>10,000 times</b> and aggregates results into probability tables."
        ),
        "hero_cta": "Learn more about the creator & connect →",
        "loading_spinner": "Loading simulation data...",
        "data_not_ready": "⚠️ Simulation data not ready yet. Please reload later.",
        "last_run": "Simulations last run on: {date} UTC",
        "results_header": "{league} Simulation Results",
        "table_caption": "Table shows probability (%) of each team finishing in each position based on 10,000 simulated seasons.",
        "download_button": "Download table as CSV",
        "methodology_title": "How This Simulation Works",
        "methodology_intro": (
            "This simulation combines <b>historical results</b> and <b>betting odds</b> to estimate match outcome probabilities.  "
            "We then run <b>10,000 Monte Carlo simulations</b> for all remaining fixtures to calculate how likely each team is to finish in each league position."
        ),
        "step1_title": "Historical Data:",
        "step1_desc": 'Collect current standings via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Fixtures:",
        "step2_desc": 'Historical match results and remaining fixtures obtained via the <a href="https://www.football-data.org/" target="_blank">Football-Data.org API</a>.',
        "step3_title": "Betting Odds:",
        "step3_desc": 'Incorporate market expectations from <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> to boost accuracy.',
        "step4_title": "Team Strengths:",
        "step4_desc": "Estimate attacking and defensive strengths for each team.",
        "step5_title": "Match Probabilities:",
        "step5_desc": "Generate outcome probabilities using Poisson and betting-based models.",
        "step6_title": "Monte Carlo Simulations:",
        "step6_desc": "Run 10,000 full season simulations to cover all possible scenarios.",
        "step7_title": "Final Positions:",
        "step7_desc": "Aggregate the simulation results into probability distributions.",
        "about_title": "About Me",
        "about_p1": 'Hi, I’m <b>Victoria Friss de Kereki</b>, a <b>Football Data Analyst</b> turning football data into <b>data-driven insights</b>, with a growing focus on probabilistic modelling and simulation.',
        "about_p2": "I build <b>data-driven insights</b>, <b>probabilistic simulations</b>, and <b>predictive models</b> to help sports organisations and analysts make informed decisions backed by data.",
        "about_p3": 'My work can be explored on <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, where I share projects on football analytics, player performance, and simulations.',
        "about_cta": "Interested in collaborating or discussing sports analytics? <br><b>Let’s connect!</b>",
        "footer": "© 2026 Victoria Friss de Kereki &middot; Built with Python & Streamlit",
    },
    "es": {
        "hero_title": "Simulador de Ligas de Fútbol",
        "hero_byline": "por Victoria Friss de Kereki",
        "hero_description": (
            "Pronósticos basados en datos para las posiciones finales en ligas de fútbol de todo el mundo.<br>"
            "Simula cada partido restante <b>10.000 veces</b> y agrega los resultados en tablas de probabilidad."
        ),
        "hero_cta": "Conoce más sobre la creadora y conecta →",
        "loading_spinner": "Cargando datos de la simulación...",
        "data_not_ready": "⚠️ Los datos de la simulación aún no están listos. Vuelve a cargar más tarde.",
        "last_run": "Última ejecución de las simulaciones: {date} UTC",
        "results_header": "Resultados de la Simulación: {league}",
        "table_caption": "La tabla muestra la probabilidad (%) de que cada equipo termine en cada posición, según 10.000 temporadas simuladas.",
        "download_button": "Descargar tabla como CSV",
        "methodology_title": "Cómo Funciona Esta Simulación",
        "methodology_intro": (
            "Esta simulación combina <b>resultados históricos</b> y <b>cuotas de apuestas</b> para estimar las probabilidades de resultado de cada partido.  "
            "Luego ejecutamos <b>10.000 simulaciones de Monte Carlo</b> sobre todos los partidos restantes para calcular la probabilidad de que cada equipo termine en cada posición de la liga."
        ),
        "step1_title": "Datos Históricos:",
        "step1_desc": 'Recopila la tabla de posiciones actual mediante web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Partidos:",
        "step2_desc": 'Resultados históricos y partidos restantes obtenidos a través de la <a href="https://www.football-data.org/" target="_blank">API de Football-Data.org</a>.',
        "step3_title": "Cuotas de Apuestas:",
        "step3_desc": 'Incorpora las expectativas del mercado desde <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> para mejorar la precisión.',
        "step4_title": "Fuerza de los Equipos:",
        "step4_desc": "Estima la fuerza ofensiva y defensiva de cada equipo.",
        "step5_title": "Probabilidades de Partido:",
        "step5_desc": "Genera probabilidades de resultado usando modelos de Poisson y basados en cuotas.",
        "step6_title": "Simulaciones de Monte Carlo:",
        "step6_desc": "Ejecuta 10.000 simulaciones completas de la temporada para cubrir todos los escenarios posibles.",
        "step7_title": "Posiciones Finales:",
        "step7_desc": "Agrega los resultados de la simulación en distribuciones de probabilidad.",
        "about_title": "Sobre Mí",
        "about_p1": 'Hola, soy <b>Victoria Friss de Kereki</b>, <b>analista de datos de fútbol</b> que convierte datos futbolísticos en <b>insights basados en datos</b>, con un enfoque creciente en modelado probabilístico y simulación.',
        "about_p2": "Construyo <b>insights basados en datos</b>, <b>simulaciones probabilísticas</b> y <b>modelos predictivos</b> para ayudar a organizaciones deportivas y analistas a tomar decisiones informadas respaldadas por datos.",
        "about_p3": 'Puedes explorar mi trabajo en <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, donde comparto proyectos sobre análisis de fútbol, rendimiento de jugadores y simulaciones.',
        "about_cta": "¿Interesada en colaborar o hablar sobre análisis deportivo? <br><b>¡Conectemos!</b>",
        "footer": "© 2026 Victoria Friss de Kereki &middot; Hecho con Python y Streamlit",
    },
    "pt-BR": {
        "hero_title": "Simulador de Ligas de Futebol",
        "hero_byline": "por Victoria Friss de Kereki",
        "hero_description": (
            "Previsões baseadas em dados para as posições finais em ligas de futebol de todo o mundo.<br>"
            "Simula cada partida restante <b>10.000 vezes</b> e agrega os resultados em tabelas de probabilidade."
        ),
        "hero_cta": "Saiba mais sobre a criadora e conecte-se →",
        "loading_spinner": "Carregando dados da simulação...",
        "data_not_ready": "⚠️ Os dados da simulação ainda não estão prontos. Recarregue mais tarde.",
        "last_run": "Última execução das simulações: {date} UTC",
        "results_header": "Resultados da Simulação: {league}",
        "table_caption": "A tabela mostra a probabilidade (%) de cada time terminar em cada posição, com base em 10.000 temporadas simuladas.",
        "download_button": "Baixar tabela como CSV",
        "methodology_title": "Como Esta Simulação Funciona",
        "methodology_intro": (
            "Esta simulação combina <b>resultados históricos</b> e <b>odds de apostas</b> para estimar as probabilidades de resultado de cada partida.  "
            "Em seguida, executamos <b>10.000 simulações de Monte Carlo</b> para todas as partidas restantes, calculando a probabilidade de cada time terminar em cada posição da liga."
        ),
        "step1_title": "Dados Históricos:",
        "step1_desc": 'Coleta a tabela de classificação atual via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Partidas:",
        "step2_desc": 'Resultados históricos e partidas restantes obtidos através da <a href="https://www.football-data.org/" target="_blank">API do Football-Data.org</a>.',
        "step3_title": "Odds de Apostas:",
        "step3_desc": 'Incorpora as expectativas do mercado da <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> para aumentar a precisão.',
        "step4_title": "Força dos Times:",
        "step4_desc": "Estima a força ofensiva e defensiva de cada time.",
        "step5_title": "Probabilidades de Partida:",
        "step5_desc": "Gera probabilidades de resultado usando modelos de Poisson e baseados em odds.",
        "step6_title": "Simulações de Monte Carlo:",
        "step6_desc": "Executa 10.000 simulações completas da temporada para cobrir todos os cenários possíveis.",
        "step7_title": "Posições Finais:",
        "step7_desc": "Agrega os resultados da simulação em distribuições de probabilidade.",
        "about_title": "Sobre Mim",
        "about_p1": 'Olá, sou <b>Victoria Friss de Kereki</b>, <b>analista de dados de futebol</b> que transforma dados do futebol em <b>insights orientados por dados</b>, com foco crescente em modelagem probabilística e simulação.',
        "about_p2": "Eu crio <b>insights orientados por dados</b>, <b>simulações probabilísticas</b> e <b>modelos preditivos</b> para ajudar organizações esportivas e analistas a tomar decisões informadas com base em dados.",
        "about_p3": 'Você pode conhecer meu trabalho no <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, onde compartilho projetos sobre análise de futebol, desempenho de jogadores e simulações.',
        "about_cta": "Interessado em colaborar ou discutir análise esportiva? <br><b>Vamos nos conectar!</b>",
        "footer": "© 2026 Victoria Friss de Kereki &middot; Feito com Python e Streamlit",
    },
    "fr": {
        "hero_title": "Simulateur de Ligues de Football",
        "hero_byline": "par Victoria Friss de Kereki",
        "hero_description": (
            "Prévisions basées sur les données pour les classements finaux dans les ligues de football du monde entier.<br>"
            "Simule chaque match restant <b>10 000 fois</b> et agrège les résultats dans des tableaux de probabilité."
        ),
        "hero_cta": "En savoir plus sur la créatrice et se connecter →",
        "loading_spinner": "Chargement des données de simulation...",
        "data_not_ready": "⚠️ Les données de simulation ne sont pas encore prêtes. Veuillez recharger plus tard.",
        "last_run": "Dernière exécution des simulations : {date} UTC",
        "results_header": "Résultats de la Simulation : {league}",
        "table_caption": "Le tableau montre la probabilité (%) que chaque équipe termine à chaque position, sur la base de 10 000 saisons simulées.",
        "download_button": "Télécharger le tableau en CSV",
        "methodology_title": "Comment Fonctionne Cette Simulation",
        "methodology_intro": (
            "Cette simulation combine <b>résultats historiques</b> et <b>cotes des paris</b> pour estimer les probabilités de résultat des matchs.  "
            "Nous exécutons ensuite <b>10 000 simulations de Monte-Carlo</b> pour tous les matchs restants afin de calculer la probabilité que chaque équipe termine à chaque position du classement."
        ),
        "step1_title": "Données Historiques :",
        "step1_desc": 'Récupère le classement actuel via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Calendrier :",
        "step2_desc": 'Résultats historiques et matchs restants obtenus via l\'<a href="https://www.football-data.org/" target="_blank">API Football-Data.org</a>.',
        "step3_title": "Cotes des Paris :",
        "step3_desc": 'Intègre les attentes du marché de <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> pour améliorer la précision.',
        "step4_title": "Force des Équipes :",
        "step4_desc": "Estime la force offensive et défensive de chaque équipe.",
        "step5_title": "Probabilités de Match :",
        "step5_desc": "Génère des probabilités de résultat à l'aide de modèles de Poisson et basés sur les cotes.",
        "step6_title": "Simulations de Monte-Carlo :",
        "step6_desc": "Exécute 10 000 simulations complètes de la saison pour couvrir tous les scénarios possibles.",
        "step7_title": "Positions Finales :",
        "step7_desc": "Agrège les résultats de la simulation en distributions de probabilité.",
        "about_title": "À Propos de Moi",
        "about_p1": "Bonjour, je suis <b>Victoria Friss de Kereki</b>, une <b>analyste de données football</b> qui transforme les données du football en <b>insights basés sur les données</b>, avec un intérêt croissant pour la modélisation probabiliste et la simulation.",
        "about_p2": "Je conçois des <b>insights basés sur les données</b>, des <b>simulations probabilistes</b> et des <b>modèles prédictifs</b> pour aider les organisations sportives et les analystes à prendre des décisions éclairées, appuyées par les données.",
        "about_p3": 'Vous pouvez découvrir mon travail sur <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, où je partage des projets sur l\'analyse du football, la performance des joueurs et les simulations.',
        "about_cta": "Intéressé(e) par une collaboration ou une discussion sur l'analyse sportive ? <br><b>Connectons-nous !</b>",
        "footer": "© 2026 Victoria Friss de Kereki &middot; Créé avec Python et Streamlit",
    },
}

if "lang" not in st.session_state:
    st.session_state.lang = "en"

def t(key, **kwargs):
    text = TRANSLATIONS[st.session_state.lang][key]
    return text.format(**kwargs) if kwargs else text

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


def style_probabilities_table(df, column_labels=None):
    display_df = df.copy()

    # -------------------------------
    # SAFE CLEANING ONLY (non-destructive)
    # remove accidental index columns ONLY if they exist
    display_df = display_df.loc[:, ~display_df.columns.astype(str).str.match(r"^(index|Unnamed.*|level_0)$")]

    # DO NOT reset index unless it's actually needed
    display_df = display_df.reset_index(drop=True)

    # Column headers are localised for display only -- position/team/games/points
    # columns are renamed here, after the frame's real "POS"/"TEAM"/"GP"/"PTS"
    # names (set upstream from the pickled simulation output) have already done
    # their job everywhere else in the app.
    column_labels = column_labels or {"POS": "POS", "TEAM": "TEAM", "GP": "GP", "PTS": "PTS"}
    display_df = display_df.rename(columns=column_labels)

    # -------------------------------
    # TEXT / NUMERIC SPLIT
    text_cols = [column_labels["POS"], column_labels["TEAM"], column_labels["GP"], column_labels["PTS"]]
    num_cols = display_df.columns.difference(text_cols)

    vmax = max(display_df[num_cols].max().max(), 1) if not display_df[num_cols].empty else 1
    color_data = display_df[num_cols].divide(vmax).apply(lambda s: s.map(color_scale)) * vmax

    styled = (
        display_df.style
        .background_gradient(cmap=green_cmap, vmin=0, vmax=vmax, gmap=color_data, axis=None)
        .map(zero_style, subset=num_cols)
        .format({col: "{:.2f}%" for col in num_cols})
        .set_properties(subset=[column_labels["POS"], column_labels["GP"], column_labels["PTS"]], **{
            "text-align":"center","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"600","color":"#000","white-space":"nowrap"
        })
        .set_properties(subset=[column_labels["TEAM"]], **{
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

/* Top-right contact panel -- also fixed white; same black-icon reasoning.
   Sits well below the language pills (44px lower than the pills' own
   bottom edge) so the two clusters read as two distinct, deliberately
   spaced groups rather than one crowded corner. */
#contact-panel {
    position: fixed;
    top: 88px;
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
    #contact-panel { flex-direction: row; top: 64px; right: 10px; padding: 8px 10px; border-radius: 8px; }
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

/* Language switcher -- three small pill buttons (same st.button + st.columns
   pattern as the league picker above, just much smaller), pinned top-right
   via st.container(key=...). Styled like the icon-chips just below it --
   small white rounded chips with a soft shadow -- so the two rows read as
   one deliberate top-right cluster instead of a bolted-on form control. */
/* position:fixed correctly pulls the switcher itself out of the page, but
   Streamlit's vertical-block layout still reserves its normal inter-element
   gap around the now-empty slot it used to sit in, adding dead space above
   the hero card. display:contents drops that wrapping slot out of the flex
   layout entirely so no gap gets reserved for it. */
[data-testid="stLayoutWrapper"]:has(.st-key-lang_switcher) {
    display: contents;
}
.st-key-lang_switcher {
    position: fixed;
    top: 14px;
    right: 20px;
    z-index: 101;
    width: 218px;
}
.st-key-lang_switcher [data-testid="stHorizontalBlock"] {
    gap: 6px !important;
}
.st-key-lang_switcher div.stButton > button {
    height: 30px !important;
    min-height: 30px !important;
    padding: 0 4px !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    border-radius: 15px !important;
    white-space: nowrap !important;
    transition: transform 0.15s ease, background-color 0.2s ease;
}
.st-key-lang_switcher div.stButton > button[kind="secondary"] {
    background-color: #ffffff !important;
    color: #555 !important;
    border: none !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
}
.st-key-lang_switcher div.stButton > button[kind="secondary"]:hover {
    background-color: #ffffff !important;
    color: #2E7D32 !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
}
.st-key-lang_switcher div.stButton > button[kind="primary"] {
    background-color: #2E7D32 !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 2px 6px rgba(46,125,50,0.4) !important;
}
.st-key-lang_switcher div.stButton > button[kind="primary"]:hover {
    background-color: #245f27 !important;
    color: #ffffff !important;
}
@media (max-width: 600px) {
    .st-key-lang_switcher { top: 8px; right: 8px; width: 190px; }
    .st-key-lang_switcher div.stButton > button { font-size: 11px !important; height: 26px !important; min-height: 26px !important; }
}

/* This whole markdown call's own flex slot is dropped from the layout the
   same way the language switcher's is above -- everything in it is either
   invisible (the link/style tags) or already pulled out via position:fixed
   (#contact-panel), so it has no business reserving a gap of its own. */
[data-testid="stElementContainer"]:has(#contact-panel) {
    display: contents;
}
</style>
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
# 5️⃣.5 LANGUAGE SWITCHER (top right, pill toggle)

LANGUAGE_TOGGLE = [("en", "🇬🇧 EN"), ("es", "🇪🇸 ES"), ("fr", "🇫🇷 FR"), ("pt-BR", "🇧🇷 PT")]

with st.container(key="lang_switcher"):
    lang_cols = st.columns(len(LANGUAGE_TOGGLE), gap="small")
    for col, (code, label) in zip(lang_cols, LANGUAGE_TOGGLE):
        with col:
            if st.button(
                label,
                key=f"lang_btn_{code}",
                type="primary" if st.session_state.lang == code else "secondary",
                use_container_width=True,
            ) and st.session_state.lang != code:
                st.session_state.lang = code
                st.rerun()

# -------------------------------
# 6️⃣ TOP-RIGHT CONTACT PANEL
# (rendered above, merged into the same st.markdown call as the stylesheet --
# see the comment there for why)

# -------------------------------
# 7️⃣ HERO SECTION

st.markdown(f"""
<div class="app-card" style="padding:28px 32px; max-width:900px; margin:28px auto; text-align:center;">
    <h1 style="margin:0; font-size:34px; font-weight:700;">
        {t("hero_title")}
    </h1>
    <p style="margin:6px 0 0 0; font-size:14px; font-weight:500; color:#777;">
        {t("hero_byline")}
    </p>
    <div style="height:4px; width:80px; background:#2E7D32; margin:14px auto 20px auto; border-radius:2px;"></div>
    <p style="margin:0;">
        {t("hero_description")}
    </p>
    <p style="margin-top:15px; font-weight:600;">
        <a href="https://www.linkedin.com/in/victoria-friss-de-kereki/" target="_blank" style="text-decoration:none;">
        {t("hero_cta")}
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

with st.spinner(t("loading_spinner")):
    position_distribution_pct_all = load_simulation_data()

if not position_distribution_pct_all:
    st.warning(t("data_not_ready"))
else:
    pct_file = "data/precomputed_pos_pct.pkl"
    last_updated_file = "data/last_updated.txt"
    if os.path.exists(last_updated_file):
        with open(last_updated_file) as f:
            run_dt = datetime.strptime(f.read().strip(), "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
    else:
        run_dt = datetime.fromtimestamp(os.path.getmtime(pct_file), tz=timezone.utc)
    month_name = MONTH_NAMES[st.session_state.lang][run_dt.month - 1]
    formatted_date = f"{run_dt.day:02d} {month_name} {run_dt.year}, {run_dt.strftime('%H:%M')}"
    st.markdown(
        f'<div class="status-banner">{t("last_run", date=formatted_date)}</div>',
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

st.header(t("results_header", league=selected_display_name))

# -------------------------------
# 11️⃣ STYLE AND DISPLAY TABLE

styled_table, num_cols = style_probabilities_table(pos_pct_df, column_labels=COLUMN_LABELS[st.session_state.lang])
st.markdown(
    f'<div class="table-card"><div class="table-wrapper">{styled_table.to_html(escape=False)}</div></div>',
    unsafe_allow_html=True
)
st.caption(t("table_caption"))

# -------------------------------
# 12️⃣ DOWNLOAD OPTION

csv = pos_pct_df.to_csv(index=False).encode("utf-8")
st.download_button(t("download_button"), data=csv, file_name=f"{league}_final_positions.csv", mime="text/csv")

# -------------------------------
# -------------------------------
# 1️⃣4️⃣ METHODOLOGY
st.markdown(f"""
<div class="app-card" style="padding:28px 32px; max-width:900px; margin:28px auto;">
<h3 style="margin-bottom:15px;">{t("methodology_title")}</h3>
<p>
{t("methodology_intro")}
</p>
<ul style="padding-left:0; list-style:none; border-left:3px solid #2E7D32; margin-top:20px;">
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">1</div>
<div><b>{t("step1_title")}</b> {t("step1_desc")}</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">2</div>
<div><b>{t("step2_title")}</b> {t("step2_desc")}</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">3</div>
<div><b>{t("step3_title")}</b> {t("step3_desc")}</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">4</div>
<div><b>{t("step4_title")}</b> {t("step4_desc")}</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">5</div>
<div><b>{t("step5_title")}</b> {t("step5_desc")}</div>
</li>
<li style="margin-bottom:15px; display:flex; align-items:flex-start;">
<div class="step-circle">6</div>
<div><b>{t("step6_title")}</b> {t("step6_desc")}</div>
</li>
<li style="margin-bottom:0; display:flex; align-items:flex-start;">
<div class="step-circle">7</div>
<div><b>{t("step7_title")}</b> {t("step7_desc")}</div>
</li>
</ul>
</div>
""", unsafe_allow_html=True)


# -------------------------------
# 14️⃣ BOTTOM ABOUT ME

st.markdown(f"""
<div id="about-me" class="app-card" style="padding:28px 32px; max-width:900px;
            margin:28px auto; text-align:center;">
<h3 style="margin-bottom:15px;">{t("about_title")}</h3>
<p>{t("about_p1")}</p>
<p>{t("about_p2")}</p>
<p>{t("about_p3")}</p>
<p style="margin-top:20px; font-size:17px; font-weight:600; color:var(--accent-text);">
{t("about_cta")}
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
st.markdown(f"""
<div style="text-align:center; padding:10px 0 30px 0; font-size:13px; color:#999;">
    {t("footer")}
</div>
""", unsafe_allow_html=True)