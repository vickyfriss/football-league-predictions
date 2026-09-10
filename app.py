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
        "hero_badge": "9 Leagues · Updated Daily",
        "hero_title": "Football League Simulator",
        "hero_byline": "by Victoria Friss de Kereki",
        "hero_description": (
            "This simulation combines historical results and betting odds to estimate match outcome probabilities.<br>"
            "We then run <b>10,000 Monte Carlo simulations</b> for all remaining fixtures to calculate how likely each team is to finish in each league position."
        ),
        "hero_cta": "Learn more about the creator & connect →",
        "loading_spinner": "Loading simulation data...",
        "data_not_ready": "⚠️ Simulation data not ready yet. Please reload later.",
        "last_run": "Simulations last run on: {date} UTC",
        "results_eyebrow": "Live Predictions",
        "results_header": "{league} Simulation Results",
        "table_caption": "Table shows probability (%) of each team finishing in each position based on 10,000 simulated seasons.",
        "download_button": "Download table as CSV",
        "methodology_eyebrow": "The Method",
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
        "step_home_title": "Home Advantage:",
        "step_home_desc": "Boost the home team's expected goals using each league's historical home-versus-away scoring gap.",
        "step5_title": "Match Probabilities:",
        "step5_desc": "Generate outcome probabilities using Poisson and betting-based models.",
        "step6_title": "Monte Carlo Simulations:",
        "step6_desc": "Run 10,000 full season simulations to cover all possible scenarios.",
        "step7_title": "Final Positions:",
        "step7_desc": "Aggregate the simulation results into probability distributions.",
        "about_eyebrow": "The Creator",
        "about_title": "About Me",
        "about_p1": 'Hi, I’m <b>Victoria Friss de Kereki</b>, a <b>Football Data Analyst</b> turning football data into <b>data-driven insights</b>, with a growing focus on probabilistic modelling and simulation.',
        "about_p2": "I build <b>data-driven insights</b>, <b>probabilistic simulations</b>, and <b>predictive models</b> to help sports organisations and analysts make informed decisions backed by data.",
        "about_p3": 'My work can be explored on <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, where I share projects on football analytics, player performance, and simulations.',
        "about_cta": "Interested in collaborating or discussing sports analytics? <br><b>Let’s connect!</b>",
        "footer": "© 2026 Victoria Friss de Kereki &middot; Built with Python & Streamlit",
    },
    "es": {
        "hero_badge": "9 Ligas · Actualizado a Diario",
        "hero_title": "Simulador de Ligas de Fútbol",
        "hero_byline": "por Victoria Friss de Kereki",
        "hero_description": (
            "Esta simulación combina resultados históricos y cuotas de apuestas para estimar las probabilidades de cada partido.<br>"
            "Luego ejecutamos <b>10.000 simulaciones de Monte Carlo</b> para todos los partidos restantes y calculamos la probabilidad de que cada equipo termine en cada posición de la liga."
        ),
        "hero_cta": "Conoce más sobre la creadora y conéctate →",
        "loading_spinner": "Cargando datos de la simulación...",
        "data_not_ready": "⚠️ Los datos de la simulación aún no están listos. Vuelve a intentarlo más tarde.",
        "last_run": "Última ejecución de las simulaciones: {date} UTC",
        "results_eyebrow": "Predicciones en Vivo",
        "results_header": "Resultados de la Simulación: {league}",
        "table_caption": "La tabla muestra la probabilidad (%) de que cada equipo termine en cada posición, según 10.000 temporadas simuladas.",
        "download_button": "Descargar tabla como CSV",
        "methodology_eyebrow": "El Método",
        "methodology_title": "Cómo Funciona Esta Simulación",
        "methodology_intro": (
            "Esta simulación combina <b>resultados históricos</b> y <b>cuotas de apuestas</b> para estimar las probabilidades de resultado de cada partido.  "
            "Luego ejecutamos <b>10.000 simulaciones de Monte Carlo</b> sobre todos los partidos restantes para calcular la probabilidad de que cada equipo termine en cada posición de la liga."
        ),
        "step1_title": "Datos Históricos:",
        "step1_desc": 'Recopila la clasificación actual mediante web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Calendario:",
        "step2_desc": 'Resultados históricos y partidos restantes obtenidos a través de la <a href="https://www.football-data.org/" target="_blank">API de Football-Data.org</a>.',
        "step3_title": "Cuotas de Apuestas:",
        "step3_desc": 'Incorpora las expectativas del mercado desde <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> para mejorar la precisión.',
        "step4_title": "Fuerza de los Equipos:",
        "step4_desc": "Estima la fuerza ofensiva y defensiva de cada equipo.",
        "step_home_title": "Ventaja de Local:",
        "step_home_desc": "Aumenta los goles esperados del equipo local según la diferencia histórica de goles entre local y visitante en cada liga.",
        "step5_title": "Probabilidades de Partido:",
        "step5_desc": "Genera probabilidades de resultado combinando modelos de Poisson con las cuotas del mercado.",
        "step6_title": "Simulaciones de Monte Carlo:",
        "step6_desc": "Ejecuta 10.000 simulaciones completas de la temporada para cubrir todos los escenarios posibles.",
        "step7_title": "Posiciones Finales:",
        "step7_desc": "Resume los resultados de la simulación en distribuciones de probabilidad.",
        "about_eyebrow": "La Creadora",
        "about_title": "Sobre Mí",
        "about_p1": 'Hola, soy <b>Victoria Friss de Kereki</b>, <b>analista de datos de fútbol</b> que transforma datos futbolísticos en <b>insights valiosos</b>, con un enfoque creciente en modelado probabilístico y simulación.',
        "about_p2": "Construyo <b>insights basados en datos</b>, <b>simulaciones probabilísticas</b> y <b>modelos predictivos</b> para ayudar a organizaciones deportivas y analistas a tomar decisiones más informadas.",
        "about_p3": 'Puedes explorar mi trabajo en <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, donde comparto proyectos sobre análisis de fútbol, rendimiento de jugadores y simulaciones.',
        "about_cta": "¿Interesado(a) en colaborar o hablar sobre análisis deportivo? <br><b>¡Conectemos!</b>",
        "footer": "© 2026 Victoria Friss de Kereki &middot; Hecho con Python y Streamlit",
    },
    "pt-BR": {
        "hero_badge": "9 Ligas · Atualizado Diariamente",
        "hero_title": "Simulador de Ligas de Futebol",
        "hero_byline": "por Victoria Friss de Kereki",
        "hero_description": (
            "Esta simulação combina resultados históricos e odds de apostas para estimar as probabilidades de cada partida.<br>"
            "Em seguida, executamos <b>10.000 simulações de Monte Carlo</b> para todas as partidas restantes e calculamos a probabilidade de cada time terminar em cada posição da liga."
        ),
        "hero_cta": "Saiba mais sobre a criadora e conecte-se →",
        "loading_spinner": "Carregando dados da simulação...",
        "data_not_ready": "⚠️ Os dados da simulação ainda não estão prontos. Recarregue mais tarde.",
        "last_run": "Última execução das simulações: {date} UTC",
        "results_eyebrow": "Previsões ao Vivo",
        "results_header": "Resultados da Simulação: {league}",
        "table_caption": "A tabela mostra a probabilidade (%) de cada time terminar em cada posição, com base em 10.000 temporadas simuladas.",
        "download_button": "Baixar tabela como CSV",
        "methodology_eyebrow": "O Método",
        "methodology_title": "Como Esta Simulação Funciona",
        "methodology_intro": (
            "Esta simulação combina <b>resultados históricos</b> e <b>odds de apostas</b> para estimar as probabilidades de resultado de cada partida.  "
            "Em seguida, executamos <b>10.000 simulações de Monte Carlo</b> para todas as partidas restantes, calculando a probabilidade de cada time terminar em cada posição da liga."
        ),
        "step1_title": "Dados Históricos:",
        "step1_desc": 'Coleta a tabela de classificação atual via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Calendário:",
        "step2_desc": 'Resultados históricos e partidas restantes obtidos através da <a href="https://www.football-data.org/" target="_blank">API do Football-Data.org</a>.',
        "step3_title": "Odds de Apostas:",
        "step3_desc": 'Incorpora as expectativas do mercado da <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> para aumentar a precisão.',
        "step4_title": "Força dos Times:",
        "step4_desc": "Estima a força ofensiva e defensiva de cada time.",
        "step_home_title": "Vantagem de Jogar em Casa:",
        "step_home_desc": "Aumenta os gols esperados do time mandante com base na diferença histórica de gols entre mandante e visitante em cada liga.",
        "step5_title": "Probabilidades de Partida:",
        "step5_desc": "Gera probabilidades de resultado combinando modelos de Poisson com as odds do mercado.",
        "step6_title": "Simulações de Monte Carlo:",
        "step6_desc": "Executa 10.000 simulações completas da temporada para cobrir todos os cenários possíveis.",
        "step7_title": "Posições Finais:",
        "step7_desc": "Resume os resultados da simulação em distribuições de probabilidade.",
        "about_eyebrow": "A Criadora",
        "about_title": "Sobre Mim",
        "about_p1": 'Olá, sou <b>Victoria Friss de Kereki</b>, <b>analista de dados de futebol</b> que transforma dados do futebol em <b>insights valiosos</b>, com foco crescente em modelagem probabilística e simulação.',
        "about_p2": "Eu crio <b>insights orientados por dados</b>, <b>simulações probabilísticas</b> e <b>modelos preditivos</b> para ajudar organizações esportivas e analistas a tomar decisões mais informadas.",
        "about_p3": 'Você pode conhecer meu trabalho no <a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>, onde compartilho projetos sobre análise de futebol, desempenho de jogadores e simulações.',
        "about_cta": "Interessado(a) em colaborar ou discutir análise esportiva? <br><b>Vamos nos conectar!</b>",
        "footer": "© 2026 Victoria Friss de Kereki &middot; Feito com Python e Streamlit",
    },
    "fr": {
        "hero_badge": "9 Ligues · Mis à Jour Chaque Jour",
        "hero_title": "Simulateur de Ligues de Football",
        "hero_byline": "par Victoria Friss de Kereki",
        "hero_description": (
            "Cette simulation combine résultats historiques et cotes des paris pour estimer les probabilités de chaque match.<br>"
            "Nous exécutons ensuite <b>10 000 simulations de Monte-Carlo</b> pour tous les matchs restants et calculons la probabilité que chaque équipe termine à chaque position du classement."
        ),
        "hero_cta": "En savoir plus sur la créatrice et se connecter →",
        "loading_spinner": "Chargement des données de simulation...",
        "data_not_ready": "⚠️ Les données de simulation ne sont pas encore prêtes. Veuillez recharger plus tard.",
        "last_run": "Dernière exécution des simulations : {date} UTC",
        "results_eyebrow": "Prédictions en Direct",
        "results_header": "Résultats de la Simulation : {league}",
        "table_caption": "Le tableau montre la probabilité (%) que chaque équipe termine à chaque place, sur la base de 10 000 saisons simulées.",
        "download_button": "Télécharger le tableau en CSV",
        "methodology_eyebrow": "La Méthode",
        "methodology_title": "Comment Fonctionne Cette Simulation",
        "methodology_intro": (
            "Cette simulation combine <b>résultats historiques</b> et <b>cotes des paris</b> pour estimer les probabilités de résultat des matchs.  "
            "Nous exécutons ensuite <b>10 000 simulations de Monte-Carlo</b> pour tous les matchs restants afin de calculer la probabilité que chaque équipe termine à chaque place du classement."
        ),
        "step1_title": "Données Historiques :",
        "step1_desc": 'Récupère le classement actuel via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Calendrier :",
        "step2_desc": 'Résultats historiques et matchs restants obtenus via l\'<a href="https://www.football-data.org/" target="_blank">API Football-Data.org</a>.',
        "step3_title": "Cotes des Paris :",
        "step3_desc": 'Intègre les attentes du marché de <a href="https://the-odds-api.com/" target="_blank">The Odds API</a> pour améliorer la précision.',
        "step4_title": "Force des Équipes :",
        "step4_desc": "Estime la force offensive et défensive de chaque équipe.",
        "step_home_title": "Avantage du Terrain :",
        "step_home_desc": "Augmente les buts attendus de l'équipe à domicile selon l'écart historique de buts entre domicile et extérieur pour chaque championnat.",
        "step5_title": "Probabilités de Match :",
        "step5_desc": "Génère des probabilités de résultat en combinant des modèles de Poisson et les cotes du marché.",
        "step6_title": "Simulations de Monte-Carlo :",
        "step6_desc": "Exécute 10 000 simulations complètes de la saison pour couvrir tous les scénarios possibles.",
        "step7_title": "Positions Finales :",
        "step7_desc": "Agrège les résultats de la simulation en distributions de probabilité.",
        "about_eyebrow": "La Créatrice",
        "about_title": "À Propos de Moi",
        "about_p1": "Bonjour, je suis <b>Victoria Friss de Kereki</b>, une <b>analyste de données</b> spécialisée en football, qui transforme les données du jeu en <b>insights précieux</b>, avec un intérêt croissant pour la modélisation probabiliste et la simulation.",
        "about_p2": "Je conçois des <b>insights basés sur les données</b>, des <b>simulations probabilistes</b> et des <b>modèles prédictifs</b> pour aider les organisations sportives et les analystes à prendre des décisions plus éclairées.",
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

def format_run_date(run_dt, lang):
    # Each language's date order/particles are real grammar, not just translated
    # words -- "9 de septiembre de 2026" and "9 septembre 2026" aren't the same
    # shape as "09 September 2026", and Spanish/French/Portuguese don't
    # capitalise month names in running text the way English does.
    day = run_dt.day
    time_str = run_dt.strftime("%H:%M")
    if lang == "en":
        month = MONTH_NAMES[lang][run_dt.month - 1]
        return f"{day:02d} {month} {run_dt.year}, {time_str}"
    month = MONTH_NAMES[lang][run_dt.month - 1].lower()
    if lang == "fr":
        return f"{day} {month} {run_dt.year}, {time_str}"
    return f"{day} de {month} de {run_dt.year}, {time_str}"

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
            "font-size":"12px","font-weight":"600","color":"#000","white-space":"nowrap",
            "font-variant-numeric":"tabular-nums"
        })
        .set_properties(subset=[column_labels["TEAM"]], **{
            "text-align":"left","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"600","color":"#000","white-space":"nowrap"
        })
        .set_properties(subset=num_cols, **{
            "text-align":"center","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"500","color":"#000",
            "font-variant-numeric":"tabular-nums"
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
            # Row hover: a translucent green wash over the *entire* row, via
            # box-shadow rather than background-color. box-shadow paints as its
            # own layer on top of whatever background is already there
            # (including the percentage cells' inline gradient colour) and
            # blends with it via alpha, so it tints/enhances the existing
            # colour instead of replacing it -- and needs no !important, since
            # it isn't competing with that inline style at all (different
            # property, no specificity fight). A flat background-color
            # override was tried first: full visibility everywhere, but it
            # blanked out the real gradient colour for the hovered row.
            {"selector": "tbody tr:hover td", "props":[("box-shadow","inset 0 0 0 999px rgba(46,125,50,0.18)")]},
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
    --section-band-bg: #eaf5ec;
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
        --section-band-bg: #16241a;
    }
}

/* One consistent typeface everywhere -- native Streamlit widgets included, not
   just the custom HTML sections -- so nothing looks like it belongs to a
   different page. */
.stApp, .stApp * {
    font-family: 'Inter', Roboto, Arial, sans-serif !important;
}

html {
    /* both-edges (not just stable) reserves matching gutter space on the left
       too, even though nothing ever scrolls there -- with only the right edge
       reserved, that space came out of the usable width asymmetrically, which
       is what was still pulling every calc(-50vw + 50%) full-bleed section
       (hero, methodology band, about band) a few pixels left of true center
       even after switching from "no reservation at all" to this. */
    scrollbar-gutter: stable both-edges;
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
/* A slim brand-green rule along the top edge of every card below the hero
   banner -- a small, repeated visual anchor tying the rest of the page
   back to the banner's colour without repeating its full treatment. */
.app-card { border-top: 4px solid #2E7D32; }

/* Small uppercase "kicker" label above a section heading -- editorial
   shorthand for "here's what this block is," echoing the hero banner's
   badge in spirit without repeating its pill shape everywhere. */
.section-eyebrow {
    display: block;
    color: var(--accent-text);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

/* Full-bleed hero banner -- breaks out of Streamlit's centered, padded
   content column to run edge-to-edge, the way a masthead does on a real
   sports-media site. The margin-left/right calc(-50vw + 50%) trick (not
   width:100vw + left:50%) is the version that plays nicely with
   scrollbar-gutter:stable further up this stylesheet: 100vw includes the
   reserved scrollbar gutter and would overshoot the true viewport width by
   that amount, this doesn't. Fixed brand green regardless of theme, same
   reasoning as .step-circle and the table card elsewhere: it's a deliberate
   solid-colour surface, not body text that should adapt to dark mode.
   margin-top cancels .block-container's own 2rem top padding so the colour
   actually touches the top of the page instead of leaving a grey sliver. */
.hero-banner {
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    margin-top: -2rem;
    margin-bottom: 24px;
    padding: 30px 24px 28px;
    background: linear-gradient(135deg, #2E7D32 0%, #1e5c22 100%);
    text-align: center;
}
.hero-banner-inner { max-width: 720px; margin: 0 auto; }
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.35);
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 5px 13px;
    border-radius: 999px;
    margin-bottom: 12px;
}
.hero-banner h1 {
    color: #ffffff !important;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.01em;
    margin: 0 0 5px 0;
}
.hero-banner .hero-byline {
    color: rgba(255,255,255,0.82);
    font-size: 13px;
    font-weight: 500;
    margin: 0 0 12px 0;
}
.hero-banner .hero-description {
    color: rgba(255,255,255,0.97);
    font-size: 15px;
    line-height: 1.6;
    margin: 0;
}
.hero-banner .hero-description b { color: #ffffff; }
.hero-banner-cta {
    display: inline-block;
    margin-top: 12px;
    color: #ffffff !important;
    font-weight: 700;
    font-size: 14px;
    text-decoration: none !important;
    border-bottom: 2px solid rgba(255,255,255,0.55);
    padding-bottom: 2px;
    transition: border-color 0.2s ease;
}
.hero-banner-cta:hover { border-bottom-color: #ffffff; }
@media (max-width: 600px) {
    /* Extra top padding clears the language-switcher pills (which wrap to
       two rows on narrow screens) plus the contact-icon row below them,
       both fixed-position and floating over the top of this banner. */
    .hero-banner { padding: 128px 20px 24px; }
    .hero-banner h1 { font-size: 22px; }
}
.app-card p, .app-card li { color: var(--text-main); font-size: 15px; line-height: 1.6; }

/* Numbered step badges in the methodology list -- fixed brand green (not a
   dark-mode variable): it's a solid-fill badge with guaranteed white text, so
   it doesn't need to adapt to the page theme the way body text does. */
.step-circle {
    background-color: #2E7D32; color: #fff; font-weight: 600; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    width: 30px; height: 30px; flex-shrink: 0; margin-right: 12px;
    transition: background-color 0.2s ease;
}
.method-step-card:hover .step-circle { background-color: #245f27; }

/* Full-bleed methodology band -- same edge-to-edge technique as .hero-banner,
   but a light green tint instead of solid brand green: this section needs to
   read as a distinct "zone" of the page (band / white table card / band)
   without competing with the hero for visual weight. */
.methodology-band {
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    margin-top: 18px;
    margin-bottom: 18px;
    padding: 40px 24px 48px;
    background-color: var(--section-band-bg);
    border-top: 1px solid rgba(46,125,50,0.25);
    border-bottom: 1px solid rgba(46,125,50,0.25);
    text-align: center;
}
.methodology-inner { max-width: 980px; margin: 0 auto; }
.methodology-band .section-eyebrow { text-align: center; }
/* Shared type scale for every section title on the page -- hero h1 is the one
   deliberately bigger headline, everything below it (methodology, the league
   results table, about-me) reads as the same "section title" weight/size so
   the page has one consistent two-tier heading hierarchy instead of every
   section inventing its own. Each band only supplies the colour that reads
   against its own background. */
.methodology-heading, .about-heading, .results-heading { margin: 0 0 10px; font-size: 26px; font-weight: 800; }
/* Scoped with the band ancestor (not just the bare class) on purpose --
   Streamlit injects its own ".st-emotion-cache-XXXX h1,h2,h3 { color:
   inherit }" rule per container, which is class+type (0,1,1) and silently
   outranks a bare ".methodology-heading"/".about-heading" class (0,1,0),
   even though it comes first in source order. One extra ancestor class
   brings ours to (0,2,0), which wins for real instead of by lucky
   coincidence (methodology's "inherit" happened to resolve to the same
   colour anyway; about's did not -- it inherited dark body text onto a
   green background). */
.methodology-band .methodology-heading { color: var(--text-main); }
.methodology-intro-text {
    /* !important on margin too, not just text-align -- Streamlit's own
       markdown-container rule for <p> sets margin with higher specificity
       than this bare class, collapsing "0 auto" down to "0 0" and pinning
       the box flush-left in its parent instead of centering it (each line's
       text still rendered centered *within* that mispositioned box, which is
       what made it look like a narrower, off-center paragraph rather than an
       obviously blank margin bug). */
    max-width: 640px; margin: 0 auto !important; color: var(--text-main);
    font-size: 15px; line-height: 1.6;
    text-align: center !important;
}
/* Steps as a responsive card grid instead of one long stacked list -- the
   list read as sparse and text-heavy at full page width, where a grid of
   compact cards fills the space the way a real editorial site's "how it
   works" section does. auto-fit + minmax collapses to a single column on
   mobile with no separate media query needed. */
.method-steps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 16px;
    margin-top: 28px;
    text-align: left;
}
.method-step-card {
    background-color: var(--card-bg);
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    padding: 20px;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.method-step-card:hover { box-shadow: var(--card-shadow-hover); transform: translateY(-2px); }
.method-step-card .step-circle { margin: 0 0 12px 0; }
.method-step-card p { margin: 0; color: var(--text-main); font-size: 14px; line-height: 1.55; text-align: left !important; }

/* Full-bleed "About Me" closing band -- same edge-to-edge technique as the
   hero, but the methodology band's light tint rather than a solid brand-green
   gradient, so the page closes on the same quiet register the methodology
   band opened with instead of bookending with two bold green sections. */
.about-band {
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    margin-top: 18px;
    margin-bottom: 0;
    padding: 48px 24px 44px;
    background-color: var(--section-band-bg);
    border-top: 1px solid rgba(46,125,50,0.25);
    border-bottom: 1px solid rgba(46,125,50,0.25);
    text-align: center;
}
.about-band-inner { max-width: 680px; margin: 0 auto; }
.about-band .section-eyebrow { text-align: center; }
.about-band .about-heading { color: var(--text-main); }
.about-band p { color: var(--text-main); font-size: 15px; line-height: 1.6; margin: 0 0 12px; }
.about-band .about-cta-text {
    margin: 8px 0 0; font-size: 17px; font-weight: 700; color: var(--accent-text);
}
.about-band .icon-row { margin-top: 20px; }

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
    max-width: 900px; margin: 18px auto; padding: 10px 18px;
    background-color: #eaf5ec; border-left: 2px solid #a5d6a7; border-right: 2px solid #a5d6a7;
    border-radius: 8px; color: #245f27; font-size: 13px; text-align: center;
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
    margin: 18px auto;
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

    /* left offsets below are each 1px less than the exact running-total
       width (46, 216, 258): at rest this changes nothing, since a sticky
       element's resting position comes from normal table layout, not from
       "left" (that only kicks in once actively stuck). While scrolled,
       though, Chromium occasionally rounds two adjacent stuck sticky cells
       to different device pixels and leaves a hairline gap between them
       that shows the scrolling content behind it through the seam. A
       deliberate 1px overlap, safely covered by the earlier column's
       higher z-index, absorbs that rounding error instead of exposing it. */
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

    /* Sticky second column: TEAM. 1px less than the POS column's width on
       purpose -- see the desktop block's comment above for why. */
    th:nth-child(2), td:nth-child(2) {
        position: sticky;
        left: 39px;
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
    /* :not(.st-key-lang_switcher *) matters here -- without it this also
       matched the language switcher's own row of 4 buttons (it's a
       stHorizontalBlock containing stButtons too), forcing it into the same
       2-column grid and wrapping it to two rows instead of the single
       centered line it's meant to be. */
    div[data-testid="stHorizontalBlock"]:has(div.stButton):not(.st-key-lang_switcher *) {
        flex-wrap: wrap !important;
        gap: 8px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div.stButton):not(.st-key-lang_switcher *) > div[data-testid="stColumn"] {
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
    /* On narrow screens there's no room for a permanently pinned corner
       cluster -- fixed position meant this panel stayed on screen and
       covered real content (the "last run" banner, the table's top edge)
       for the entire time the user scrolled through the page. Switching to
       absolute anchors it to the top of the document instead: it still sits
       over the hero banner exactly where it does today, but scrolls away
       with the rest of the page instead of floating over content below. */
    /* Centered to match the now-single-row, centered language switcher above
       it, rather than staying right-jammed while the switcher above it is
       centered -- top is 10px below that switcher's own bottom edge (a
       single row of 26px pills starting at top:8px ends around 34px). */
    #contact-panel { position: absolute; flex-direction: row; top: 44px; left: 50%; right: auto; transform: translateX(-50%); padding: 8px 10px; border-radius: 8px; }
    #contact-panel a { margin: 0 8px; }
    #contact-panel a:first-child { margin-left: 0; }
    #contact-panel a img { width: 24px !important; height: 24px !important; }

}

/* Centered on its own line below the caption -- the negative margin-top
   this used to pull the button up onto the caption's row broke down
   whenever the caption text wrapped to two lines (translations vary in
   length, and mobile width wraps sooner), overlapping the button on top of
   the wrapped second line instead of sitting beside it. */
[data-testid="stDownloadButton"] {
    display: flex;
    justify-content: center;
    margin-top: 8px;
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
   once it's hidden -- without this the page keeps a large empty gap up top.
   Same story at the bottom -- Streamlit's own default padding-bottom (160px,
   originally reserved for its floating toolbar) left a big block of dead grey
   space below the footer text that had nothing to do with our own footer's
   own 30px padding. */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 0 !important;
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
    flex-wrap: nowrap !important;
}
.st-key-lang_switcher [data-testid="stColumn"] {
    width: max-content !important;
    min-width: unset !important;
    flex: 0 0 auto !important;
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
/* This switcher is position:fixed, so it stays on screen after the page
   scrolls the green banner out of view too -- it ends up sitting over the
   plain grey page background just as often as over the banner. A
   translucent "glass" treatment (tried first) reads fine on green but goes
   nearly invisible on grey, so both states are solid white instead, the
   same guaranteed-visible-on-anything treatment already used for the
   contact-icon chips below. Active vs inactive is then carried entirely by
   internal contrast (green border + text vs plain grey text), which reads
   the same regardless of what's behind the pill. */
.st-key-lang_switcher div.stButton > button[kind="secondary"] {
    background-color: #ffffff !important;
    color: #555 !important;
    border: 1px solid transparent !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2) !important;
}
.st-key-lang_switcher div.stButton > button[kind="secondary"]:hover {
    background-color: #ffffff !important;
    color: #2E7D32 !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0,0,0,0.25) !important;
}
/* A white pill with a thin green ring (tried first) read too close to the
   plain white inactive pills at this size to register as "selected" at a
   glance. Solid dark-green fill with a white ring is unambiguous either
   way: the white ring keeps it readable against the banner's own green,
   and the green fill itself pops against the grey page background once
   scrolled past the banner. */
.st-key-lang_switcher div.stButton > button[kind="primary"] {
    background-color: #1e5c22 !important;
    color: #ffffff !important;
    border: 2px solid #ffffff !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3) !important;
}
.st-key-lang_switcher div.stButton > button[kind="primary"]:hover {
    background-color: #17481b !important;
    color: #ffffff !important;
}
@media (max-width: 600px) {
    /* Same reasoning as #contact-panel above: fixed position left this
       pinned over content (the results table, the run-date banner) for the
       whole scroll. Absolute keeps it in the same spot over the hero banner
       but lets it scroll away with the page instead of staying on top. */
    /* Four pills at 190px wide had no choice but to wrap into a cramped 2x2
       block, right-jammed into the corner. Centering a single row instead
       needs less width per pill (no flag+code label has to share a row with
       three others), so all four fit on one line. */
    .st-key-lang_switcher { position: absolute; top: 8px; left: 50%; right: auto; transform: translateX(-50%); width: max-content; max-width: calc(100% - 16px); }
    .st-key-lang_switcher div.stButton > button { font-size: 11px !important; height: 26px !important; min-height: 26px !important; padding: 0 8px !important; }
}

/* Three st.markdown calls on this page (font links, this stylesheet, the
   contact panel below) contain nothing but invisible tags or content already
   pulled out via position:fixed -- none of them should reserve a gap in
   Streamlit's vertical layout. display:contents on the outer element
   container alone isn't enough though: Streamlit wraps every markdown call
   in a couple of real (non-contents) div layers of its own first, and
   *those* still generate a flex item and consume a gap unless they're
   collapsed too, so every layer down to the actual content is targeted here. */
[data-testid="stElementContainer"]:has(link[rel="preconnect"]),
[data-testid="stElementContainer"]:has(link[rel="preconnect"]) [data-testid="stMarkdown"],
[data-testid="stElementContainer"]:has(link[rel="preconnect"]) [data-testid="stMarkdown"] > div,
[data-testid="stElementContainer"]:has(link[rel="preconnect"]) [data-testid="stMarkdownContainer"],
[data-testid="stElementContainer"]:has(style),
[data-testid="stElementContainer"]:has(style) [data-testid="stMarkdown"],
[data-testid="stElementContainer"]:has(style) [data-testid="stMarkdown"] > div,
[data-testid="stElementContainer"]:has(style) [data-testid="stMarkdownContainer"],
[data-testid="stElementContainer"]:has(#contact-panel),
[data-testid="stElementContainer"]:has(#contact-panel) [data-testid="stMarkdown"],
[data-testid="stElementContainer"]:has(#contact-panel) [data-testid="stMarkdown"] > div,
[data-testid="stElementContainer"]:has(#contact-panel) [data-testid="stMarkdownContainer"] {
    display: contents;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 5️⃣.6 TOP-RIGHT CONTACT PANEL

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
# 7️⃣ HERO SECTION

st.markdown(f"""
<div class="hero-banner">
    <div class="hero-banner-inner">
        <span class="hero-badge">{t("hero_badge")}</span>
        <h1>{t("hero_title")}</h1>
        <p class="hero-byline">{t("hero_byline")}</p>
        <p class="hero-description">{t("hero_description")}</p>
        <a class="hero-banner-cta" href="https://www.linkedin.com/in/victoria-friss-de-kereki/" target="_blank">
            {t("hero_cta")}
        </a>
    </div>
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

DEFAULT_LEAGUE_KEY = "premierleague_england"

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
    formatted_date = format_run_date(run_dt, st.session_state.lang)
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

st.markdown(f"""
<div style="text-align:center; margin: 0 0 0.25rem;">
    <span class="section-eyebrow">{t("results_eyebrow")}</span>
    <h2 class="results-heading">{selected_display_name.split(" (")[0]}</h2>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# 11️⃣ STYLE AND DISPLAY TABLE

styled_table, num_cols = style_probabilities_table(pos_pct_df, column_labels=COLUMN_LABELS[st.session_state.lang])
st.markdown(
    f'<div class="table-card"><div class="table-wrapper">{styled_table.to_html(escape=False)}</div></div>',
    unsafe_allow_html=True
)

# -------------------------------
# 12️⃣ DOWNLOAD OPTION

st.caption(t("table_caption"))
csv = pos_pct_df.to_csv(index=False).encode("utf-8")
st.download_button(t("download_button"), data=csv, file_name=f"{league}_final_positions.csv", mime="text/csv")

# -------------------------------
# -------------------------------
# 1️⃣4️⃣ METHODOLOGY
st.markdown(f"""
<div class="methodology-band">
<div class="methodology-inner">
<span class="section-eyebrow">{t("methodology_eyebrow")}</span>
<h2 class="methodology-heading">{t("methodology_title")}</h2>
<p class="methodology-intro-text">{t("methodology_intro")}</p>
<div class="method-steps-grid">
<div class="method-step-card">
<div class="step-circle">1</div>
<p><b>{t("step1_title")}</b> {t("step1_desc")}</p>
</div>
<div class="method-step-card">
<div class="step-circle">2</div>
<p><b>{t("step2_title")}</b> {t("step2_desc")}</p>
</div>
<div class="method-step-card">
<div class="step-circle">3</div>
<p><b>{t("step3_title")}</b> {t("step3_desc")}</p>
</div>
<div class="method-step-card">
<div class="step-circle">4</div>
<p><b>{t("step4_title")}</b> {t("step4_desc")}</p>
</div>
<div class="method-step-card">
<div class="step-circle">5</div>
<p><b>{t("step_home_title")}</b> {t("step_home_desc")}</p>
</div>
<div class="method-step-card">
<div class="step-circle">6</div>
<p><b>{t("step5_title")}</b> {t("step5_desc")}</p>
</div>
<div class="method-step-card">
<div class="step-circle">7</div>
<p><b>{t("step6_title")}</b> {t("step6_desc")}</p>
</div>
<div class="method-step-card">
<div class="step-circle">8</div>
<p><b>{t("step7_title")}</b> {t("step7_desc")}</p>
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)


# -------------------------------
# 14️⃣ BOTTOM ABOUT ME

st.markdown(f"""
<div id="about-me" class="about-band">
<div class="about-band-inner">
<span class="section-eyebrow">{t("about_eyebrow")}</span>
<h2 class="about-heading">{t("about_title")}</h2>
<p>{t("about_p1")}</p>
<p>{t("about_p2")}</p>
<p>{t("about_p3")}</p>
<p class="about-cta-text">{t("about_cta")}</p>
<div class="icon-row">
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
</div>
""", unsafe_allow_html=True)

# -------------------------------
# 15️⃣ FOOTER
st.markdown(f"""
<div style="text-align:center; padding:10px 0 30px 0; font-size:13px; color:#999;">
    {t("footer")}
</div>
""", unsafe_allow_html=True)