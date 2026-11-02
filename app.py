# -------------------------------
# 1️⃣ IMPORTS
import streamlit as st
import pickle
import pandas as pd
import numpy as np
import os
import time
import html
import altair as alt
import streamlit.components.v1 as st_components
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
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

# Short month names for the team-form dates ("17 Oct") -- written out rather
# than cut from MONTH_NAMES, since French juin/juillet would both become "jui"
SHORT_MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"],
    "pt-BR": ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
}

COLUMN_LABELS = {
    "en": {"POS": "POS", "TEAM": "TEAM", "GP": "GP", "PTS": "PTS", "GD": "GD"},
    "es": {"POS": "POS", "TEAM": "EQUIPO", "GP": "PJ", "GD": "DG", "PTS": "PTS"},
    "pt-BR": {"POS": "POS", "TEAM": "TIME", "GP": "J", "GD": "SG", "PTS": "PTS"},
    "fr": {"POS": "POS", "TEAM": "ÉQUIPE", "GP": "MJ", "GD": "DB", "PTS": "PTS"},
}

TRANSLATIONS = {
    "en": {
        "hero_title": "Football League Simulator",
        "hero_byline": "by Victoria Friss de Kereki",
        "contact_email": "Email",
        "hero_lead": "Every remaining fixture, played 10,000 times.",
        "hero_description": "Each team’s chance of finishing in every position, from the title to relegation, built from results and betting odds.",
        "loading_spinner": "Loading simulation data...",
        "data_not_ready": "⚠️ Simulation data not ready yet. Please reload later.",
        "last_run": "Simulations last run on: {date} UTC",
        "ago_now": "just now",
        "ago_minutes": "{n} min ago",
        "ago_hour": "1 hour ago",
        "ago_hours": "{n} hours ago",
        "ago_day": "1 day ago",
        "ago_days": "{n} days ago",
        "updated_ago": "Updated {ago}",
        "season_progress": "Matchday {md} of {total} · {left} to play",
        "results_header": "{league} Simulation Results",
        "table_caption": "Table shows probability (%) of each team finishing in each position based on 10,000 simulated seasons.",
        "cell_tooltip": "{team}: {pct} chance of finishing {pos}",
        "last_games": "Last {n} games · newest first",
        "next_games": "Next {n} games",
        "form_W": "W",
        "form_D": "D",
        "form_L": "L",
        "form_home": "H",
        "form_away": "A",
        "card_title_title": "Title race",
        "card_title_sub": "Chance of winning the league",
        "card_race_title_ucl": "Champions League race",
        "card_race_title_promotion": "Automatic promotion race",
        "card_race_title_libertadores": "Libertadores race",
        "card_playoff_title": "Play-off race",
        "card_race_sub": "Chance of a top-{n} finish, for the teams closest to the cut-off",
        "card_rel_title": "Relegation battle",
        "card_rel_sub": "Chance of finishing in the relegation places ({first}–{last})",
        "card_rel_sub_playoff": "Chance of direct relegation ({first}–{last})",
        "card_movers_title": "Biggest changes",
        "card_movers_sub": "This week’s other big moves, beyond the cards alongside",
        "zone_ucl": "Champions League",
        "zone_top_maybe": "Possible 5th Champions League place",
        "zone_promotion": "Promotion",
        "zone_libertadores": "Libertadores",
        "zone_top_playoff": "Promotion play-offs",
        "zone_rel_playoff": "Relegation play-off",
        "zone_relegation": "Relegation",
        "zones_note": "Zones based on current position",
        "card_show_more": "Show more",
        "card_show_less": "Show less",
        "card_cutoff": "Top-{n} cut-off",
        "m_title": "Title",
        "m_top_ucl": "Top {n}",
        "m_top_promotion": "Promotion",
        "m_top_libertadores": "Libertadores",
        "m_playoff": "Top {n}",
        "m_relegation": "Relegation",
        "delta_note": "▲▼ change in the last 7 days (since {date})",
        "delta_tip": "Change since {date}",
        "trend_eyebrow": "Season So Far",
        "trend_title": "How the Chances Have Moved",
        "trend_sub": "Each team’s chance after every update this season",
        "trend_teams": "Teams",
        "md_short": "MD",
        "no_games": "No games",
        "break_international": "International break",
        "break_world_cup": "World Cup 2026",
        "trend_empty": "Not enough updates yet this season to show a trend.",
        "trend_date": "Date",
        "trend_team": "Team",
        "methodology_eyebrow": "The Method",
        "methodology_title": "How This Simulation Works",
        "methodology_intro": (
            "This simulation combines <b>historical results</b> and <b>betting odds</b> to estimate match outcome probabilities.  "
            "It then runs <b>10,000 Monte Carlo simulations</b> for all remaining fixtures to calculate how likely each team is to finish in each league position."
        ),
        "step1_title": "Historical Data:",
        "step1_desc": 'Collect current standings via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Fixtures:",
        "step2_desc": 'Historical match results and remaining fixtures obtained via the <a href="https://www.football-data.org/" target="_blank">Football-Data.org API</a>.',
        "step3_title": "Betting Odds:",
        "step3_desc": 'Matches the bookmakers have already priced (<a href="https://the-odds-api.com/" target="_blank">The Odds API</a>) use their odds directly, with the margin removed.',
        "step4_title": "Team Strengths:",
        "step4_desc": "Estimate attacking and defensive strengths from goals, pulled towards the league average (or a typical promoted or relegated side) until half a season of games is in, then blend in what the last six weeks of odds imply (25% market).",
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
        "hero_title": "Simulador de Ligas de Fútbol",
        "hero_byline": "por Victoria Friss de Kereki",
        "contact_email": "Correo",
        "hero_lead": "Cada partido que queda, jugado 10.000 veces.",
        "hero_description": "La probabilidad de cada equipo de terminar en cada posición, del título al descenso, a partir de resultados y cuotas de apuestas.",
        "loading_spinner": "Cargando datos de la simulación...",
        "data_not_ready": "⚠️ Los datos de la simulación aún no están listos. Vuelve a intentarlo más tarde.",
        "last_run": "Última ejecución de las simulaciones: {date} UTC",
        "ago_now": "hace un momento",
        "ago_minutes": "hace {n} min",
        "ago_hour": "hace 1 hora",
        "ago_hours": "hace {n} horas",
        "ago_day": "hace 1 día",
        "ago_days": "hace {n} días",
        "updated_ago": "Actualizado {ago}",
        "season_progress": "Jornada {md} de {total} · quedan {left}",
        "results_header": "Resultados de la Simulación: {league}",
        "table_caption": "La tabla muestra la probabilidad (%) de que cada equipo termine en cada posición, según 10.000 temporadas simuladas.",
        "cell_tooltip": "{team}: {pct} de probabilidad de terminar {pos}",
        "last_games": "Últimos {n} partidos · el más reciente primero",
        "next_games": "Próximos {n} partidos",
        "form_W": "G",
        "form_D": "E",
        "form_L": "P",
        "form_home": "L",
        "form_away": "V",
        "card_title_title": "Carrera por el título",
        "card_title_sub": "Probabilidad de ganar la liga",
        "card_race_title_ucl": "Carrera por la Champions League",
        "card_race_title_promotion": "Carrera por el ascenso directo",
        "card_race_title_libertadores": "Carrera por la Libertadores",
        "card_playoff_title": "Carrera por el playoff",
        "card_race_sub": "Probabilidad de terminar entre los {n} primeros, para los equipos más cerca del corte",
        "card_rel_title": "Lucha por la permanencia",
        "card_rel_sub": "Probabilidad de terminar en puestos de descenso ({first}–{last})",
        "card_rel_sub_playoff": "Probabilidad de descenso directo ({first}–{last})",
        "card_movers_title": "Mayores cambios",
        "card_movers_sub": "Otros grandes cambios de la semana, además de las tarjetas de al lado",
        "zone_ucl": "Champions League",
        "zone_top_maybe": "Posible 5.ª plaza de Champions League",
        "zone_promotion": "Ascenso",
        "zone_libertadores": "Libertadores",
        "zone_top_playoff": "Playoff de ascenso",
        "zone_rel_playoff": "Playoff de descenso",
        "zone_relegation": "Descenso",
        "zones_note": "Zonas según la posición actual",
        "card_show_more": "Ver más",
        "card_show_less": "Ver menos",
        "card_cutoff": "Corte: top {n}",
        "m_title": "Título",
        "m_top_ucl": "Top {n}",
        "m_top_promotion": "Ascenso",
        "m_top_libertadores": "Libertadores",
        "m_playoff": "Top {n}",
        "m_relegation": "Descenso",
        "delta_note": "▲▼ cambio en los últimos 7 días (desde el {date})",
        "delta_tip": "Cambio desde el {date}",
        "trend_eyebrow": "La Temporada Hasta Ahora",
        "trend_title": "Cómo Han Cambiado las Probabilidades",
        "trend_sub": "La probabilidad de cada equipo tras cada actualización de esta temporada",
        "trend_teams": "Equipos",
        "md_short": "J",
        "no_games": "Sin partidos",
        "break_international": "Parón internacional",
        "break_world_cup": "Mundial 2026",
        "trend_empty": "Todavía no hay suficientes actualizaciones esta temporada para mostrar una tendencia.",
        "trend_date": "Fecha",
        "trend_team": "Equipo",
        "methodology_eyebrow": "El Método",
        "methodology_title": "Cómo Funciona Esta Simulación",
        "methodology_intro": (
            "Esta simulación combina <b>resultados históricos</b> y <b>cuotas de las casas de apuestas</b> para estimar las probabilidades de resultado de cada partido.  "
            "Luego ejecuta <b>10.000 simulaciones de Monte Carlo</b> sobre todos los partidos restantes para calcular la probabilidad de que cada equipo termine en cada posición de la liga."
        ),
        "step1_title": "Datos Históricos:",
        "step1_desc": 'Recopila la clasificación actual mediante web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Calendario:",
        "step2_desc": 'Resultados históricos y partidos restantes obtenidos a través de la <a href="https://www.football-data.org/" target="_blank">API de Football-Data.org</a>.',
        "step3_title": "Cuotas de Apuestas:",
        "step3_desc": 'Los partidos que ya tienen cuota (<a href="https://the-odds-api.com/" target="_blank">The Odds API</a>) usan directamente sus probabilidades, sin el margen.',
        "step4_title": "Fuerza de los Equipos:",
        "step4_desc": "Estima la fuerza ofensiva y defensiva a partir de los goles, acercándola a la media de la liga (o a la de un equipo ascendido o descendido típico) hasta que se ha jugado media temporada, y la combina con lo que implican las cuotas de las últimas seis semanas (25% mercado).",
        "step_home_title": "Ventaja de Local:",
        "step_home_desc": "Aumenta los goles esperados del equipo local según la diferencia histórica de goles entre local y visitante en cada liga.",
        "step5_title": "Probabilidades de Partido:",
        "step5_desc": "Genera probabilidades de resultado combinando modelos de Poisson con las cuotas de las casas de apuestas.",
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
        "hero_title": "Simulador de Ligas de Futebol",
        "hero_byline": "por Victoria Friss de Kereki",
        "contact_email": "E-mail",
        "hero_lead": "Cada jogo que falta, disputado 10.000 vezes.",
        "hero_description": "A chance de cada time terminar em cada posição, do título ao rebaixamento, a partir de resultados e odds de apostas.",
        "loading_spinner": "Carregando dados da simulação...",
        "data_not_ready": "⚠️ Os dados da simulação ainda não estão prontos. Recarregue mais tarde.",
        "last_run": "Última execução das simulações: {date} UTC",
        "ago_now": "agora mesmo",
        "ago_minutes": "há {n} min",
        "ago_hour": "há 1 hora",
        "ago_hours": "há {n} horas",
        "ago_day": "há 1 dia",
        "ago_days": "há {n} dias",
        "updated_ago": "Atualizado {ago}",
        "season_progress": "Rodada {md} de {total} · faltam {left}",
        "results_header": "Resultados da Simulação: {league}",
        "table_caption": "A tabela mostra a probabilidade (%) de cada time terminar em cada posição, com base em 10.000 temporadas simuladas.",
        "cell_tooltip": "{team}: {pct} de chance de terminar em {pos}",
        "last_games": "Últimos {n} jogos · mais recente primeiro",
        "next_games": "Próximos {n} jogos",
        "form_W": "V",
        "form_D": "E",
        "form_L": "D",
        "form_home": "C",
        "form_away": "F",
        "card_title_title": "Disputa pelo título",
        "card_title_sub": "Chance de ser campeão",
        "card_race_title_ucl": "Disputa pela Champions League",
        "card_race_title_promotion": "Disputa pelo acesso direto",
        "card_race_title_libertadores": "Disputa pela Libertadores",
        "card_playoff_title": "Disputa pelo playoff",
        "card_race_sub": "Chance de terminar entre os {n} primeiros, para os times mais perto do corte",
        "card_rel_title": "Luta contra o rebaixamento",
        "card_rel_sub": "Chance de terminar na zona de rebaixamento ({first}–{last})",
        "card_rel_sub_playoff": "Chance de rebaixamento direto ({first}–{last})",
        "card_movers_title": "Maiores mudanças",
        "card_movers_sub": "Outras grandes mudanças da semana, além dos cartões ao lado",
        "zone_ucl": "Champions League",
        "zone_top_maybe": "Possível 5ª vaga na Champions League",
        "zone_promotion": "Acesso",
        "zone_libertadores": "Libertadores",
        "zone_top_playoff": "Playoff de acesso",
        "zone_rel_playoff": "Playoff de rebaixamento",
        "zone_relegation": "Rebaixamento",
        "zones_note": "Zonas com base na posição atual",
        "card_show_more": "Ver mais",
        "card_show_less": "Ver menos",
        "card_cutoff": "Corte: top {n}",
        "m_title": "Título",
        "m_top_ucl": "Top {n}",
        "m_top_promotion": "Acesso",
        "m_top_libertadores": "Libertadores",
        "m_playoff": "Top {n}",
        "m_relegation": "Rebaixamento",
        "delta_note": "▲▼ variação nos últimos 7 dias (desde {date})",
        "delta_tip": "Variação desde {date}",
        "trend_eyebrow": "A Temporada Até Agora",
        "trend_title": "Como as Chances Mudaram",
        "trend_sub": "A chance de cada time após cada atualização desta temporada",
        "trend_teams": "Times",
        "md_short": "R",
        "no_games": "Sem jogos",
        "break_international": "Data FIFA",
        "break_world_cup": "Copa do Mundo 2026",
        "trend_empty": "Ainda não há atualizações suficientes nesta temporada para mostrar uma tendência.",
        "trend_date": "Data",
        "trend_team": "Time",
        "methodology_eyebrow": "O Método",
        "methodology_title": "Como Esta Simulação Funciona",
        "methodology_intro": (
            "Esta simulação combina <b>resultados históricos</b> e <b>odds de apostas</b> para estimar as probabilidades de resultado de cada partida.  "
            "Em seguida, executa <b>10.000 simulações de Monte Carlo</b> para todas as partidas restantes, calculando a probabilidade de cada time terminar em cada posição da liga."
        ),
        "step1_title": "Dados Históricos:",
        "step1_desc": 'Coleta a tabela de classificação atual via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Calendário:",
        "step2_desc": 'Resultados históricos e partidas restantes obtidos através da <a href="https://www.football-data.org/" target="_blank">API do Football-Data.org</a>.',
        "step3_title": "Odds de Apostas:",
        "step3_desc": 'As partidas que já têm odds (<a href="https://the-odds-api.com/" target="_blank">The Odds API</a>) usam diretamente as probabilidades das casas, sem a margem.',
        "step4_title": "Força dos Times:",
        "step4_desc": "Estima a força ofensiva e defensiva a partir dos gols, puxando-a para a média da liga (ou para a de um time promovido ou rebaixado típico) até que se tenha jogado meia temporada, e a combina com o que as odds das últimas seis semanas indicam (25% mercado).",
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
        "hero_title": "Simulateur de Ligues de Football",
        "hero_byline": "par Victoria Friss de Kereki",
        "contact_email": "E-mail",
        "hero_lead": "Chaque match restant, joué 10 000 fois.",
        "hero_description": "Les chances de chaque équipe de terminer à chaque place, du titre à la relégation, à partir des résultats et des cotes des paris.",
        "loading_spinner": "Chargement des données de simulation...",
        "data_not_ready": "⚠️ Les données de simulation ne sont pas encore prêtes. Veuillez recharger plus tard.",
        "last_run": "Dernière exécution des simulations : {date} UTC",
        "ago_now": "à l'instant",
        "ago_minutes": "il y a {n} min",
        "ago_hour": "il y a 1 heure",
        "ago_hours": "il y a {n} heures",
        "ago_day": "il y a 1 jour",
        "ago_days": "il y a {n} jours",
        "updated_ago": "Mis à jour {ago}",
        "season_progress": "Journée {md} sur {total} · {left} à jouer",
        "results_header": "Résultats de la Simulation : {league}",
        "table_caption": "Le tableau montre la probabilité (%) que chaque équipe termine à chaque place, sur la base de 10 000 saisons simulées.",
        "cell_tooltip": "{team} : {pct} de chances de finir {pos}",
        "last_games": "{n} derniers matchs · du plus récent",
        "next_games": "{n} prochains matchs",
        "form_W": "V",
        "form_D": "N",
        "form_L": "D",
        "form_home": "D",
        "form_away": "E",
        "card_title_title": "Course au titre",
        "card_title_sub": "Probabilité de remporter le championnat",
        "card_race_title_ucl": "Course à la Ligue des champions",
        "card_race_title_promotion": "Course à la montée directe",
        "card_race_title_libertadores": "Course à la Libertadores",
        "card_playoff_title": "Course aux barrages",
        "card_race_sub": "Probabilité de finir dans les {n} premiers, pour les équipes les plus proches de la limite",
        "card_rel_title": "Lutte pour le maintien",
        "card_rel_sub": "Probabilité de finir en zone de relégation ({first}–{last})",
        "card_rel_sub_playoff": "Probabilité de relégation directe ({first}–{last})",
        "card_movers_title": "Plus grands changements",
        "card_movers_sub": "Les autres grands changements de la semaine, en plus des cartes voisines",
        "zone_ucl": "Ligue des champions",
        "zone_top_maybe": "Possible 5e place en Ligue des champions",
        "zone_promotion": "Montée",
        "zone_libertadores": "Libertadores",
        "zone_top_playoff": "Barrages de montée",
        "zone_rel_playoff": "Barrage de relégation",
        "zone_relegation": "Relégation",
        "zones_note": "Zones selon le classement actuel",
        "card_show_more": "Voir plus",
        "card_show_less": "Voir moins",
        "card_cutoff": "Limite : top {n}",
        "m_title": "Titre",
        "m_top_ucl": "Top {n}",
        "m_top_promotion": "Promotion",
        "m_top_libertadores": "Libertadores",
        "m_playoff": "Top {n}",
        "m_relegation": "Relégation",
        "delta_note": "▲▼ évolution sur les 7 derniers jours (depuis le {date})",
        "delta_tip": "Évolution depuis le {date}",
        "trend_eyebrow": "La Saison Jusqu’ici",
        "trend_title": "L’Évolution des Probabilités",
        "trend_sub": "Les chances de chaque équipe après chaque mise à jour de la saison",
        "trend_teams": "Équipes",
        "md_short": "J",
        "no_games": "Pas de matchs",
        "break_international": "Trêve internationale",
        "break_world_cup": "Coupe du monde 2026",
        "trend_empty": "Pas encore assez de mises à jour cette saison pour afficher une tendance.",
        "trend_date": "Date",
        "trend_team": "Équipe",
        "methodology_eyebrow": "La Méthode",
        "methodology_title": "Comment Fonctionne Cette Simulation",
        "methodology_intro": (
            "Cette simulation combine <b>résultats historiques</b> et <b>cotes des paris</b> pour estimer les probabilités de résultat des matchs.  "
            "Elle exécute ensuite <b>10 000 simulations de Monte-Carlo</b> pour tous les matchs restants afin de calculer la probabilité que chaque équipe termine à chaque place du classement."
        ),
        "step1_title": "Données Historiques :",
        "step1_desc": 'Récupère le classement actuel via web scraping (<a href="https://www.espn.com/soccer/standings/_/league/ENG.1/season/2026" target="_blank">ESPN</a>).',
        "step2_title": "Calendrier :",
        "step2_desc": 'Résultats historiques et matchs restants obtenus via l\'<a href="https://www.football-data.org/" target="_blank">API Football-Data.org</a>.',
        "step3_title": "Cotes des Paris :",
        "step3_desc": 'Les matchs déjà cotés (<a href="https://the-odds-api.com/" target="_blank">The Odds API</a>) utilisent directement les probabilités des bookmakers, sans leur marge.',
        "step4_title": "Force des Équipes :",
        "step4_desc": "Estime la force offensive et défensive à partir des buts, en la rapprochant de la moyenne de la ligue (ou de celle d'un promu ou d'un relégué typique) jusqu'à la mi-saison, puis la combine avec ce qu'impliquent les cotes des six dernières semaines (25 % marché).",
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

# First visit opens in the language from the link (?lang=es), else the
# browser's own language (e.g. "pt-BR", "es-AR", "fr-FR") when it's one we
# have, else English; the switcher still works.
if "lang" not in st.session_state:
    url_lang = st.query_params.get("lang")
    browser_lang = (st.context.locale or "").lower()
    st.session_state.lang = url_lang if url_lang in TRANSLATIONS else next(
        (code for prefix, code in [("es", "es"), ("fr", "fr"), ("pt", "pt-BR")] if browser_lang.startswith(prefix)),
        "en",
    )

def t(key, **kwargs):
    text = TRANSLATIONS[st.session_state.lang][key]
    return text.format(**kwargs) if kwargs else text

def format_time_ago(run_dt):
    # "6 hours ago" next to the exact run time, so freshness reads at a glance
    minutes = int((datetime.now(timezone.utc) - run_dt).total_seconds() // 60)
    if minutes < 1:
        return t("ago_now")
    if minutes < 60:
        return t("ago_minutes", n=minutes)
    hours = minutes // 60
    if hours < 24:
        return t("ago_hour") if hours == 1 else t("ago_hours", n=hours)
    days = hours // 24
    return t("ago_day") if days == 1 else t("ago_days", n=days)

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


# Table zones per league, by position: "top" is the Champions League (or
# Libertadores / automatic promotion) places, the rest are play-off and
# relegation spots. Formats as of 2026/27 -- edit here if a competition changes.
# "top_maybe" is a possible extra Champions League place: UEFA gives one to the
# two countries with the best European results that season (Italy + Germany
# for 2024/25, England + Spain for 2025/26), only settled once the season ends,
# so it's marked for the four leagues that keep winning it.
LEAGUE_ZONES = {
    "premierleague_england": {"top": (1, 4), "top_kind": "ucl", "top_maybe": (5, 5), "relegation": (18, 20)},
    "championship_england": {"top": (1, 2), "top_kind": "promotion", "top_playoff": (3, 6), "relegation": (22, 24)},
    "seriea_italy": {"top": (1, 4), "top_kind": "ucl", "top_maybe": (5, 5), "relegation": (18, 20)},
    "laliga_spain": {"top": (1, 4), "top_kind": "ucl", "top_maybe": (5, 5), "relegation": (18, 20)},
    "bundesliga_germany": {"top": (1, 4), "top_kind": "ucl", "top_maybe": (5, 5), "rel_playoff": (16, 16), "relegation": (17, 18)},
    "ligue1_france": {"top": (1, 4), "top_kind": "ucl", "rel_playoff": (16, 16), "relegation": (17, 18)},
    "eredivisie_netherlands": {"top": (1, 2), "top_kind": "ucl", "rel_playoff": (16, 16), "relegation": (17, 18)},
    "primeiraliga_portugal": {"top": (1, 2), "top_kind": "ucl", "rel_playoff": (16, 16), "relegation": (17, 18)},
    "seriea_brazil": {"top": (1, 4), "top_kind": "libertadores", "relegation": (17, 20)},
}
ZONE_COLORS = {"top": "#2E7D32", "top_maybe": "#A5D6A7", "top_playoff": "#81C784", "rel_playoff": "#F0A04B", "relegation": "#D84343"}

def zone_for_pos(pos, zones):
    for zone in ZONE_COLORS:
        if zone in zones and zones[zone][0] <= pos <= zones[zone][1]:
            return zone
    return None

def style_probabilities_table(df, column_labels=None, zones=None):
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
    column_labels = column_labels or {"POS": "POS", "TEAM": "TEAM", "GP": "GP", "GD": "GD", "PTS": "PTS"}
    display_df = display_df.rename(columns=column_labels)
    # GD shown as text with a true minus sign ("−4"); the underlying data (and the CSV) stays numeric
    if column_labels.get("GD") in display_df.columns:
        display_df[column_labels["GD"]] = display_df[column_labels["GD"]].map(lambda v: "" if pd.isna(v) else str(int(v)).replace("-", "\u2212"))

    # -------------------------------
    # TEXT / NUMERIC SPLIT
    text_cols = [column_labels[c] for c in ["POS", "TEAM", "GP", "GD", "PTS"] if column_labels[c] in display_df.columns]
    num_cols = display_df.columns.difference(text_cols)

    vmax = max(display_df[num_cols].max().max(), 1) if not display_df[num_cols].empty else 1
    color_data = display_df[num_cols].divide(vmax).apply(lambda s: s.map(color_scale)) * vmax

    styled = (
        display_df.style
        .background_gradient(cmap=green_cmap, vmin=0, vmax=vmax, gmap=color_data, axis=None)
        .map(zero_style, subset=num_cols)
        .format({col: "{:.2f}%" for col in num_cols})
        .set_properties(subset=[c for c in text_cols if c not in (column_labels["TEAM"], column_labels["PTS"])], **{
            "text-align":"center","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"500","color":"#555","white-space":"nowrap",
            "font-variant-numeric":"tabular-nums"
        })
        # Points are what people read first in a league table: bold, full black
        .set_properties(subset=[column_labels["PTS"]], **{
            "text-align":"center","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"800","color":"#000","white-space":"nowrap",
            "font-variant-numeric":"tabular-nums"
        })
        .set_properties(subset=[column_labels["TEAM"]], **{
            "text-align":"left","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"600","color":"#000","white-space":"nowrap"
        })
        # nowrap so a percentage never splits over two lines ("98.18" / "%"),
        # whatever the screen width, zoom or fallback font
        .set_properties(subset=num_cols, **{
            "text-align":"center","font-family":"Inter, Roboto, Arial, sans-serif",
            "font-size":"12px","font-weight":"500","color":"#000",
            "font-variant-numeric":"tabular-nums","white-space":"nowrap"
        })
        .hide(axis="index")
        .set_table_styles([
            {"selector": "th", "props":[("background-color","#dfeee2"),("color","#333"),
                                        ("text-align","center"),
                                        ("font-family","Inter, Roboto, Arial, sans-serif"),
                                        ("font-size","13px"),("font-weight","600")]},
            {"selector": "tr", "props":[("height","25px")]},
            {"selector": "th:nth-child(5), td:nth-child(5)", "props":[("border-right","2px solid #999")]},
            {"selector": "th:nth-child(5)", "props":[("font-weight","800"),("color","#000")]},
            {"selector": "td:nth-child(-n+5)", "props":[("border-bottom","1px solid #ccc")]},
            {"selector": "tr:nth-child(odd) td:nth-child(-n+5)", "props":[("background-color","#f9f9f9")]},
            {"selector": "tr:nth-child(even) td:nth-child(-n+5)", "props":[("background-color","#f2f2f2")]},
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

    # Zone stripe down the left edge of the POS cell, painted as a background
    # image rather than a border: a border would add width and throw off the
    # frozen columns' fixed widths/sticky offsets, and a box-shadow would be
    # wiped out by the row-hover box-shadow above.
    if zones:
        def zone_stripe(pos):
            zone = zone_for_pos(pos, zones)
            return f"background-image: linear-gradient(to right, {ZONE_COLORS[zone]} 4px, transparent 4px);" if zone else ""
        styled = styled.map(zone_stripe, subset=[column_labels["POS"]])

    return styled, num_cols

def ordinal(n, lang):
    if lang == "en":
        return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
    if lang == "fr":
        return "1er" if n == 1 else f"{n}e"
    return f"{n}.º" if lang == "es" else f"{n}º"

def add_cell_tooltips(table_html, df, form=None, upcoming=None):
    # Hover text on each percentage ("Chelsea: 37.70% chance of finishing 4th").
    # A styled span inside the cell, shown instantly on hover by CSS -- the
    # browser's own title tooltips need the mouse held still for ~1s and often
    # never appeared. Styler gives every cell an id ending "_row{r}_col{c}";
    # columns 5+ are the finishing positions, in the same order as df's. The
    # top rows' tips open below the cell and the right half's open leftwards,
    # so the table's scroll box doesn't cut them off.
    pos_cols = list(df.columns[5:])
    def with_tip(m):
        r, c = int(m.group(2)), int(m.group(3))
        # Team name: its last five results and next two games. Top half of the
        # table opens below the row, bottom half above, so the taller box stays
        # in the table.
        team = df.iloc[r]["TEAM"] if c == 1 else None
        if team and ((form or {}).get(team) or (upcoming or {}).get(team)):
            games = (form or {}).get(team, [])
            # Date on every line and the newest row highlighted, so the order
            # (newest first) is obvious without reading the heading
            rows = "".join(
                f'<span class="form-game{" latest" if k == 0 else ""}">'
                f'<span class="form-date">{date.day} {SHORT_MONTHS[st.session_state.lang][date.month - 1]}</span>'
                f'<span class="form-chip {res}">{t("form_" + res)}</span>'
                f'<span class="form-score">{gf}\u2013{ga}</span>'
                f'<span>{html.escape(opp)} ({t("form_home") if home else t("form_away")})</span></span>'
                for k, (res, gf, ga, opp, home, date) in enumerate(games)
            )
            # Next games above the last ones, latest date first, so the whole
            # list runs from the furthest date down to the oldest
            nxt = list(reversed((upcoming or {}).get(team, [])))
            next_rows = "".join(
                f'<span class="form-game">'
                f'<span class="form-date">{date.day} {SHORT_MONTHS[st.session_state.lang][date.month - 1]}</span>'
                f'<span>{html.escape(opp)} ({t("form_home") if home else t("form_away")})</span></span>'
                for opp, home, date in nxt
            )
            parts = (f'<span class="form-title">{t("next_games", n=len(nxt))}</span>{next_rows}' if nxt else "")
            parts += (f'<span class="form-title{" later" if nxt else ""}">{t("last_games", n=len(games))}</span>{rows}' if games else "")
            place = " tip-below" if r < len(df) / 2 else ""
            return (f'{m.group(1)} class="{m.group(4)} has-tip team-tip{place}">{m.group(5)}'
                    f'<span class="cell-tip">{parts}</span></td>')
        if c < 5:
            return m.group(0)
        text = t("cell_tooltip", team=df.iloc[r]["TEAM"], pct=f"{df.iloc[r, c]:.2f}%",
                 pos=ordinal(int(pos_cols[c - 5]), st.session_state.lang))
        classes = "has-tip" + (" tip-below" if r < 2 else "") + (" tip-left" if c - 5 >= len(pos_cols) / 2 else "")
        return f'{m.group(1)} class="{m.group(4)} {classes}">{m.group(5)}<span class="cell-tip">{html.escape(text)}</span></td>'
    return re.sub(r'(<td id="T_\w+_row(\d+)_col(\d+)") class="([^"]*)"\s*>([^<]*)</td>', with_tip, table_html)

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

@st.cache_resource(show_spinner=False)
def load_dataset_processing():
    # The pipeline's own module, for its team-name mappings and season start dates
    import importlib.util
    spec = importlib.util.spec_from_file_location("dataset_processing", "2_dataset_processing.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@st.cache_data(show_spinner=False)
def load_recent_form(league, data_version, n=5):
    # data_version is the data's last-updated time: it only keys the cache, so
    # a data update shows on the next page load instead of waiting out a TTL.
    # Each team's last n league games this season, newest first, as
    # {team: [(result, goals_for, goals_against, opponent, is_home, date), ...]}.
    # Results files use football-data.org names ("Arsenal FC"), mapped to the
    # table's names the same way the pipeline does.
    try:
        dp = load_dataset_processing()
        files = [f for f in os.listdir("data") if f.startswith(f"past_{league}_") and f.endswith(".csv")]
        df = pd.concat([pd.read_csv(f"data/{f}") for f in files])
        df = df[df["status"] == "FINISHED"].dropna(subset=["homeGoals", "awayGoals"])
        df = df.drop_duplicates(subset=["utcDate", "homeTeam", "awayTeam"])
        df["utcDate"] = pd.to_datetime(df["utcDate"], utc=True, errors="coerce")
        df = df[df["utcDate"] >= dp.SEASON_START_DATES[league]].sort_values("utcDate", ascending=False)
        df[["homeTeam", "awayTeam"]] = df[["homeTeam", "awayTeam"]].replace(dp.mappings.get(league, {}))
    except Exception:
        return {}
    form = {}
    for row in df.itertuples():
        hg, ag = int(row.homeGoals), int(row.awayGoals)
        for team, opp, gf, ga, home in [(row.homeTeam, row.awayTeam, hg, ag, True), (row.awayTeam, row.homeTeam, ag, hg, False)]:
            games = form.setdefault(team, [])
            if len(games) < n:
                games.append(("W" if gf > ga else "D" if gf == ga else "L", gf, ga, opp, home, row.utcDate))
    return form

@st.cache_data(show_spinner=False)
def load_next_games(league, data_version, n=2):
    # Each team's next n league games, soonest first, as
    # {team: [(opponent, is_home, date), ...]}, from the fixtures saved with
    # the data (football-data.org names, mapped like the results above).
    try:
        dp = load_dataset_processing()
        df = pd.read_csv(f"data/fixtures_{league}.csv")
        df["utcDate"] = pd.to_datetime(df["utcDate"], utc=True, errors="coerce")
        df = df[df["utcDate"] >= pd.Timestamp.now(tz="UTC")].sort_values("utcDate")
        df[["homeTeam", "awayTeam"]] = df[["homeTeam", "awayTeam"]].replace(dp.mappings.get(league, {}))
    except Exception:
        return {}
    upcoming = {}
    for row in df.itertuples():
        for team, opp, home in [(row.homeTeam, row.awayTeam, True), (row.awayTeam, row.homeTeam, False)]:
            games = upcoming.setdefault(team, [])
            if len(games) < n:
                games.append((opp, home, row.utcDate))
    return upcoming

# Every run also saves its full result in data/simulations/<run time>/
# <league>_simulation.csv: one column per team, one row per finishing
# position, counts out of 10,000. Those runs are the history behind the
# "change in the last 7 days" arrows and the season trend chart.
SNAPSHOT_NAME = re.compile(r"^\d{8}_\d{6}$")

def league_metrics(league):
    """{metric: (first, last position)} tracked over time for a league."""
    zones = LEAGUE_ZONES.get(league)
    if not zones:
        return {}
    metrics = {"title": (1, 1), "top": zones["top"]}
    if "top_playoff" in zones:
        metrics["playoff"] = (1, zones["top_playoff"][1])
    metrics["relegation"] = zones["relegation"]
    return metrics

@st.cache_data(show_spinner=False)
def load_history(league, data_version):
    # data_version only keys the cache, like load_recent_form. One row per
    # day (that day's last run), team and metric, this season only.
    metrics = league_metrics(league)
    columns = ["day", "team", "metric", "pct"]
    try:
        season_start = load_dataset_processing().SEASON_START_DATES[league].tz_convert(None)
    except Exception:
        return pd.DataFrame(columns=columns)
    if not metrics:
        return pd.DataFrame(columns=columns)
    # data/simulations_rebuilt holds the season's earlier runs re-run with the
    # current model (see its README), so the whole line comes from one model:
    # where a day has a rebuilt run, it's used instead of the original
    runs = {}
    for folder in ["data/simulations", "data/simulations_rebuilt"]:
        if not os.path.isdir(folder):
            continue
        days = {}
        for snap in sorted(os.listdir(folder)):
            if not SNAPSHOT_NAME.match(snap):
                continue
            when = datetime.strptime(snap, "%Y%m%d_%H%M%S")
            path = f"{folder}/{snap}/{league}_simulation.csv"
            if when < season_start or not os.path.exists(path):
                continue
            days[when.date()] = path   # later runs on the same day overwrite earlier ones
        runs.update(days)
    frames = []
    for day, path in runs.items():
        try:
            counts = pd.read_csv(path)
        except Exception:
            continue
        # A finished league is saved as its final table instead of counts
        if counts.empty or "TEAM" in counts.columns:
            continue
        pct = counts.div(counts.sum(axis=0), axis=1) * 100
        for metric, (first, last) in metrics.items():
            chance = pct.iloc[first - 1:last].sum()
            frames.append(pd.DataFrame({"day": pd.Timestamp(day), "team": chance.index, "metric": metric, "pct": chance.values}))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)

@st.cache_data(show_spinner=False)
def load_match_days(league, data_version):
    # Days with at least one league game this season, from the saved results
    try:
        season_start = load_dataset_processing().SEASON_START_DATES[league].tz_convert(None)
    except Exception:
        return set()
    days = set()
    for file in os.listdir("data"):
        if file.startswith(f"past_{league}_") and file.endswith(".csv"):
            dates = pd.to_datetime(pd.read_csv(f"data/{file}", usecols=["utcDate"])["utcDate"], utc=True, errors="coerce")
            dates = dates.dt.tz_convert(None).dt.normalize().dropna()
            days |= set(dates[dates >= season_start])
    return days

# Why a league stops: FIFA's international windows (from 2026 the September
# and October windows are one long break) and the 2026 World Cup
WORLD_CUP_2026 = (pd.Timestamp("2026-06-11"), pd.Timestamp("2026-07-19"))
INTERNATIONAL_WINDOWS = [
    (pd.Timestamp("2026-03-23"), pd.Timestamp("2026-03-31")),
    (pd.Timestamp("2026-09-21"), pd.Timestamp("2026-10-06")),
    (pd.Timestamp("2026-11-09"), pd.Timestamp("2026-11-17")),
    (pd.Timestamp("2027-03-22"), pd.Timestamp("2027-03-30")),
]

def break_reason(start, end):
    overlaps = lambda window: start <= window[1] and end >= window[0]
    if overlaps(WORLD_CUP_2026):
        return t("break_world_cup")
    if any(overlaps(w) for w in INTERNATIONAL_WINDOWS):
        return t("break_international")
    return t("no_games")

@st.cache_data(show_spinner=False)
def load_matchday_dates(league, data_version):
    # {matchday: its middle date} this season, from the saved results. The
    # middle date, not the first, so one game brought forward doesn't move it.
    try:
        season_start = load_dataset_processing().SEASON_START_DATES[league].tz_convert(None)
        files = [f for f in os.listdir("data") if f.startswith(f"past_{league}_") and f.endswith(".csv")]
        df = pd.concat([pd.read_csv(f"data/{f}", usecols=["utcDate", "matchday"]) for f in files])
    except Exception:
        return {}
    df["day"] = pd.to_datetime(df["utcDate"], utc=True, errors="coerce").dt.tz_convert(None).dt.normalize()
    df = df[(df["day"] >= season_start) & df["matchday"].notna()]
    return {int(md): g["day"].sort_values().iloc[len(g) // 2] for md, g in df.groupby("matchday")}

def week_changes(history, days=7):
    """(change in percentage points per (team, metric) since the last run at
    least `days` days before the latest one, that run's date), or (None, None)."""
    if history.empty:
        return None, None
    latest = history["day"].max()
    earlier = history.loc[history["day"] <= latest - pd.Timedelta(days=days), "day"]
    if earlier.empty:
        return None, None
    base_day = earlier.max()
    now = history[history["day"] == latest].set_index(["team", "metric"])["pct"]
    then = history[history["day"] == base_day].set_index(["team", "metric"])["pct"]
    return (now - then).dropna(), base_day

def metric_label(league, metric):
    # "Title", "Top 4", "Promotion", "Relegation"... for one tracked metric
    zones = LEAGUE_ZONES[league]
    if metric == "top":
        return t(f"m_top_{zones['top_kind']}", n=zones["top"][1])
    if metric == "playoff":
        return t("m_playoff", n=zones["top_playoff"][1])
    return t(f"m_{metric}")

def short_date(day, lang):
    return f"{day.day} {SHORT_MONTHS[lang][day.month - 1]}"

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
    --good-text: #2E7D32;
    --bad-text: #C62828;
    --good-bg: rgba(46,125,50,0.10);
    --bad-bg: rgba(198,40,40,0.08);
    --hero-top: #e3f1e5;
    --hero-glow: rgba(102,187,106,0.22);
    --hero-ink: #16301a;
    --hero-line: rgba(46,125,50,0.28);
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
        --good-text: #7ddc84;
        --bad-text: #ff8a80;
        --good-bg: rgba(125,220,132,0.12);
        --bad-bg: rgba(255,138,128,0.12);
        --hero-top: #17281b;
        --hero-glow: rgba(102,187,106,0.14);
        --hero-ink: #f1f5f1;
        --hero-line: rgba(102,187,106,0.35);
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

/* Hero: a short, centred intro on a soft green wash that fades into the page. Colours come from the theme
   tokens, so it follows light and dark mode like the rest of the page.
   Full-bleed via margin calc(-50vw + 50%) (100vw would overshoot by the
   scrollbar gutter reserved further up); margin-top cancels
   .block-container's 2rem top padding. */
.hero-banner {
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    margin-top: -2rem;
    margin-bottom: 6px;
    padding: 30px 24px 26px;
    background:
        radial-gradient(ellipse 55% 90% at 85% 0%, var(--hero-glow), transparent 70%),
        linear-gradient(180deg, var(--hero-top) 0%, var(--page-bg) 100%);
}
.hero-inner { max-width: 760px; margin: 0 auto; text-align: center; }
.hero-banner .hero-copy h1 {
    color: var(--hero-ink) !important;
    font-size: clamp(30px, 3.2vw, 42px);
    font-weight: 800;
    line-height: 1.02;
    letter-spacing: -0.03em;
    margin: 0 0 10px;
    padding: 0 !important;
    text-align: center !important;
    text-wrap: balance;
}
.hero-banner .hero-copy .hero-lead {
    color: var(--accent-text);
    font-size: clamp(16px, 1.4vw, 19px);
    font-weight: 700;
    line-height: 1.3;
    margin: 0 0 6px;
    text-align: center !important;
}
.hero-banner .hero-copy .hero-description {
    color: var(--text-main);
    opacity: 0.8;
    font-size: 14.5px;
    line-height: 1.55;
    max-width: 560px;
    margin: 0 auto 12px;
    text-align: center !important;
}
.hero-banner .hero-copy .hero-meta {
    color: var(--text-main);
    font-size: 13px;
    margin: 0;
    text-align: center !important;
}
.hero-links a {
    color: var(--accent-text) !important;
    font-weight: 600;
    text-decoration: none !important;
    margin-left: 14px;
}
.hero-links a:hover { text-decoration: underline !important; text-underline-offset: 3px; }
.hero-links a:first-child { margin-left: 16px; }

/* Between phone and desktop, the title would run into the language pills in
   the top-right corner: start it below them */
@media (min-width: 601px) and (max-width: 1100px) {
    .hero-banner { padding-top: 56px; }
}
@media (max-width: 600px) {
    /* Extra top padding clears the language pills, which sit over the top
       of this banner on phones */
    .hero-banner { padding: 52px 16px 20px; }
    .hero-links a:first-child { margin-left: 0; }
    .hero-links { display: block; margin-top: 4px; }
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
/* 1280px rather than the original 980px -- at 980 the 4-per-row step cards
   were narrow enough that longer steps (Team Strengths) ran far taller than
   the rest. The intro paragraph keeps its own 640px cap for readability. */
.methodology-inner { max-width: 1280px; margin: 0 auto; }
.methodology-band .section-eyebrow { text-align: center; }
/* Shared type scale for every section title on the page -- hero h1 is the one
   deliberately bigger headline, everything below it (methodology, the league
   results table, about-me) reads as the same "section title" weight/size so
   the page has one consistent two-tier heading hierarchy instead of every
   section inventing its own. Each band only supplies the colour that reads
   against its own background. */
.methodology-heading, .about-heading, .results-heading { margin: 0 0 10px; font-size: 26px; font-weight: 800; }
/* Streamlit's own h2 size outranks the class above inside markdown blocks */
[data-testid="stMarkdownContainer"] h2.results-heading { font-size: 30px !important; padding: 0 !important; margin: 0 0 4px !important; letter-spacing: -0.01em; }
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
    /* 280px min keeps the 8 steps at a balanced 4 + 4 inside the 1280px band
       (230px squeezed in a fifth column, leaving a lopsided 5 + 3). */
    grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
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

/* "Last updated" status pill (replaces the old full-width st.info()-style
   box): a small centred chip with a live dot, the relative time in bold and
   the exact run time muted after it. */
.status-wrap { display: flex; justify-content: center; margin: 10px 0 14px; }
.status-banner {
    display: inline-flex; align-items: center; flex-wrap: wrap; justify-content: center; gap: 4px 8px;
    padding: 7px 16px; border-radius: 999px;
    background-color: var(--card-bg); border: 1px solid var(--border-light); box-shadow: var(--card-shadow);
    color: var(--text-main); font-size: 13px; text-align: center;
}
.status-banner b { font-weight: 600; }
.status-sep, .status-date { opacity: 0.6; font-variant-numeric: tabular-nums; }
.status-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    background-color: #2E7D32; box-shadow: 0 0 0 0 rgba(46,125,50,0.5);
    animation: status-pulse 2s ease-out infinite;
}
.status-banner.stale .status-dot { background-color: #F0A04B; animation: none; }
@keyframes status-pulse {
    0% { box-shadow: 0 0 0 0 rgba(46,125,50,0.5); }
    70% { box-shadow: 0 0 0 7px rgba(46,125,50,0); }
    100% { box-shadow: 0 0 0 0 rgba(46,125,50,0); }
}
@media (prefers-reduced-motion: reduce) { .status-dot { animation: none; } }
/* Phones: the pill doesn't fit on one line, and wrapping left the "·" dangling
   at the end of the first line -- stack it as two centred lines instead. */
@media (max-width: 600px) {
    .status-banner { flex-direction: column; gap: 2px; border-radius: 16px; padding: 8px 18px; }
    .status-banner b { display: inline-flex; align-items: center; gap: 8px; }
    .status-banner > .status-dot { display: none; }
    .status-banner b::before {
        content: ""; width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
        background-color: #2E7D32; animation: status-pulse 2s ease-out infinite;
    }
    .status-banner.stale b::before { background-color: #F0A04B; animation: none; }
    .status-sep { display: none; }
}
@media (max-width: 600px) and (prefers-reduced-motion: reduce) { .status-banner b::before { animation: none; } }

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

/* Streamlit 1.66 draws a grey keyboard-focus frame around the whole scrolling
   page (an inset box-shadow on a sticky stMain::before) as soon as you click
   and then scroll with the arrow keys or space -- it stays put while the
   content scrolls past, so it reads as stray lines across the page. */
[data-testid="stMain"]::before { box-shadow: none !important; }
/* The full-bleed bands (hero, methodology, about) size themselves with 100vw,
   which counts the scrollbar's width too, so the page came out a few px wider
   than the screen and grew a sideways scrollbar. Nothing on the page should
   scroll sideways except the table, which has its own scroll box. */
[data-testid="stMain"] { overflow-x: hidden; }

/* "Matchday 9 of 38 · 29 to play" under the league name */
.season-progress { margin: -4px 0 0; font-size: 13px; font-weight: 500; color: var(--text-main); opacity: 0.7; }

/* Instant hover explanation on each percentage cell (see add_cell_tooltips).
   z-index clears the sticky frozen columns (z-index up to 5). */
/* Team cells are sticky (frozen column), which already anchors the tip --
   position:relative here would un-freeze them. */
td.has-tip:not(.team-tip) { position: relative; }
.cell-tip {
    display: none; position: absolute; bottom: calc(100% + 6px); left: 0; z-index: 20;
    padding: 6px 10px; border-radius: 6px; background-color: #1f2a22; color: #ffffff;
    font-size: 12px !important; font-weight: 500; text-align: left; white-space: nowrap;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2); pointer-events: none;
}
td.has-tip:hover .cell-tip { display: block; }
td.tip-below .cell-tip { bottom: auto; top: calc(100% + 6px); }
td.tip-left .cell-tip { left: auto; right: 0; }
/* Team-name hover: last five results with W/D/L chips */
/* Lift the hovered team cell above the other frozen cells (z-index up to 5),
   which otherwise paint over its tip row by row. */
td.team-tip:hover { z-index: 10; text-decoration: underline dotted; text-underline-offset: 3px; }
td.team-tip .cell-tip { padding: 8px 12px; text-decoration: none; }
.form-title { display: block; margin-bottom: 5px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; opacity: 0.75; }
.form-title.later { margin-top: 9px; }
.form-game { display: flex; align-items: center; gap: 8px; padding: 2px 6px; margin: 0 -6px; border-radius: 4px; font-weight: 500; }
.form-game.latest { background-color: rgba(255,255,255,0.12); }
.form-date { min-width: 44px; opacity: 0.65; font-variant-numeric: tabular-nums; }
.form-chip {
    display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px;
    border-radius: 4px; font-size: 11px; font-weight: 700; color: #ffffff;
}
.form-chip.W { background-color: #2E7D32; }
.form-chip.D { background-color: #8A8F8B; }
.form-chip.L { background-color: #D84343; }
.form-score { min-width: 30px; font-weight: 700; font-variant-numeric: tabular-nums; }

/* Zone legend under the table -- fixed light colours, since it sits inside
   the always-white table card. */
.zone-legend { display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: 12px; font-size: 12px; color: #555; }
.zone-legend .swatch { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
.zone-legend .zone-note { font-style: italic; opacity: 0.8; }

/* Headline cards above the table: title race, race for the top places,
   relegation. Same card look as the methodology steps; three across on
   desktop, stacking to one column on phones. */
.headline-cards {
    display: grid;
    /* Explicit counts rather than auto-fit, which left a lone card on its own
       row (3 + 1, 2 + 1): three cards stay in one row, four (Championship) go
       4 across, then 2 x 2; everything stacks on narrow screens. */
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin: 18px 0 4px;
}
.headline-cards.four { grid-template-columns: repeat(4, 1fr); }
.headline-cards.five { grid-template-columns: repeat(5, 1fr); }
/* Five cards (the Championship): below 1280px, two per row with the last one
   spanning the full row, so no card is left alone */
@media (max-width: 1279px) {
    .headline-cards.five { grid-template-columns: repeat(2, 1fr); }
    .headline-cards.five > .headline-card:last-child { grid-column: 1 / -1; }
}
@media (max-width: 1279px) { .headline-cards.four { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 860px) { .headline-cards { grid-template-columns: 1fr; } }
@media (max-width: 600px) { .headline-cards.four, .headline-cards.five { grid-template-columns: 1fr; } }
.headline-card {
    background-color: var(--card-bg);
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    border-top: 3px solid #2E7D32;
    padding: 16px 18px 10px;
    text-align: left;
}
.headline-card.relegation { border-top-color: #D84343; }
.headline-title { font-size: 15px; font-weight: 700; color: var(--text-main); }
.headline-sub { margin: 2px 0 12px; font-size: 12px; color: var(--text-main); opacity: 0.7; }
.headline-row {
    display: grid; grid-template-columns: 1fr auto; gap: 3px 10px; align-items: baseline;
    margin-bottom: 9px; font-size: 13px; color: var(--text-main);
}
.headline-row .team { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.headline-row .pct { font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; }
.headline-bar { grid-column: 1 / -1; height: 4px; border-radius: 2px; background-color: var(--border-light); overflow: hidden; }
.headline-bar span { display: block; height: 100%; background-color: #2E7D32; }
.headline-card.relegation .headline-bar span { background-color: #D84343; }
/* Cards expand on click to a longer list (hidden checkbox + full-card
   label). Every card stretches to the tallest in its row, with the toggle
   pushed to the bottom, so collapsed cards always line up. */
.headline-card { display: flex; flex-direction: column; cursor: pointer; transition: box-shadow 0.2s ease; }
.headline-card:hover { box-shadow: var(--card-shadow-hover); }
.headline-check { display: none; }
.headline-label { display: flex; flex-direction: column; flex: 1; cursor: pointer; margin: 0; }
.headline-long, .headline-check:checked + .headline-label .headline-short { display: none; }
.headline-check:checked + .headline-label .headline-long { display: block; }
.headline-toggle { display: block; margin: auto 0 4px; padding-top: 2px; font-size: 12px; font-weight: 600; color: var(--accent-text); }
.headline-toggle .less, .headline-check:checked + .headline-label .headline-toggle .more { display: none; }
.headline-check:checked + .headline-label .headline-toggle .less { display: inline; }
.mover-row {
    display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 10px; align-items: baseline;
    margin-bottom: 9px; padding-bottom: 7px; border-bottom: 1px solid var(--border-light);
    font-size: 13px; color: var(--text-main);
}
.mover-row .team { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mover-row .mv-delta { font-weight: 700; font-variant-numeric: tabular-nums; white-space: nowrap; }
.mover-row .mv-delta.good { color: var(--good-text); }
.mover-row .mv-delta.bad { color: var(--bad-text); }
.mover-row .mv-what { font-size: 11.5px; opacity: 0.6; white-space: nowrap; }
.headline-card.movers { border-top-color: #8A8F8B; }
.headline-cutoff {
    margin: -2px 0 9px; padding-top: 4px; border-top: 1px dashed var(--accent-text);
    font-size: 11px; font-weight: 600; color: var(--accent-text); text-align: right;
}
/* Change over the last 7 days, before each card percentage */
.headline-row .delta { margin-right: 7px; font-size: 11px; font-weight: 700; }
.delta.good { color: var(--good-text); }
.delta.bad { color: var(--bad-text); }
.delta-note { margin: 6px 2px 0; font-size: 11.5px; color: var(--text-main); opacity: 0.6; text-align: right; }

/* Season trend: a white card around Streamlit's own radio, multiselect and chart */
.st-key-trend_card {
    background-color: var(--card-bg);
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    border-top: 3px solid #2E7D32;
    padding: 22px 24px 12px;
    margin-top: 22px;
}
.trend-head { text-align: center; }
.trend-head .trend-title { margin: 0; padding: 0; font-size: 22px; font-weight: 700; color: var(--text-main); }
.st-key-trend_card .trend-head p.trend-sub { margin: 4px 0 0; font-size: 13px; color: var(--text-main); opacity: 0.7; }
.st-key-trend_card [data-testid="stElementContainer"]:has(.stRadio) { width: 100% !important; }
.st-key-trend_card .stRadio { display: flex; justify-content: center; width: 100%; }
.st-key-trend_card [role="radiogroup"] { justify-content: center; gap: 6px 22px; }
.st-key-trend_card iframe { margin-top: 12px; }
/* Let the team picker grow to fit its tags instead of scrolling inside itself */
.st-key-trend_card [data-testid="stMultiSelect"] div { max-height: none !important; }
.st-key-trend_card [data-testid="stMultiSelect"] div:has(> span > span) { overflow-y: visible !important; height: auto !important; }
@media (max-width: 600px) { .st-key-trend_card { padding: 18px 12px 8px; } }

/* Desktop: freeze the first five columns (POS, TEAM, GP, GD, PTS) while
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
    th:nth-child(n+6), td:nth-child(n+6) { width: 78px; white-space: nowrap !important; }

    /* left offsets below are each 1px less than the exact running-total
       width (46, 258, 300, 346): at rest this changes nothing, since a sticky
       element's resting position comes from normal table layout, not from
       "left" (that only kicks in once actively stuck). While scrolled,
       though, Chromium occasionally rounds two adjacent stuck sticky cells
       to different device pixels and leaves a hairline gap between them
       that shows the scrolling content behind it through the seam. A
       deliberate 1px overlap, safely covered by the earlier column's
       higher z-index, absorbs that rounding error instead of exposing it. */
    th:nth-child(1), td:nth-child(1) {
        width: 46px; white-space: nowrap !important;
        position: sticky; left: 0; z-index: 5; background-color: inherit;
    }
    /* TEAM never wraps either: 212px fits the longest name in any of the 9
       leagues on one line ("Borussia Mönchengladbach", 188px in Inter
       600/14px, "Wolverhampton Wanderers" 186px) plus the 6px+6px padding,
       with a few px to spare. At the old 170px both wrapped onto two lines. */
    th:nth-child(2), td:nth-child(2) {
        width: 212px; text-align: left !important; white-space: nowrap !important;
        position: sticky; left: 46px; z-index: 4; background-color: inherit;
    }
    th:nth-child(3), td:nth-child(3) {
        width: 42px; white-space: nowrap !important;
        position: sticky; left: 258px; z-index: 3; background-color: inherit;
    }
    /* GD: "−100" is the widest it ever needs, same width as PTS */
    th:nth-child(4), td:nth-child(4) {
        width: 46px; white-space: nowrap !important;
        position: sticky; left: 300px; z-index: 2; background-color: inherit;
    }
    th:nth-child(5), td:nth-child(5) {
        width: 46px; white-space: nowrap !important;
        position: sticky; left: 346px; z-index: 1; background-color: inherit;
    }
}

/* Mobile: fix first two columns when scrolling horizontally */
@media (max-width: 600px) {
    table { width: 100%; border-collapse: collapse; }
    th, td { white-space: nowrap !important; }

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
   own internal CSS. st.button renders correctly in this exact environment,
   so the pill row is built from st.button + st.columns instead: full page width and even spacing come for
   free from st.columns (real layout, not a style override), and un/selected
   look comes from Streamlit's own long-established primary/secondary button
   "kind" attribute rather than a newer widget's internals.
================================ */
div.stButton > button[kind="secondary"] {
    background-color: var(--card-bg) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border-light) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    font-weight: 500 !important;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: var(--section-band-bg) !important;
    color: var(--text-main) !important;
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
    height: 60px;
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
/* Newer Streamlit (seen on 1.66; 1.61 was fine) forces button labels onto a
   single truncated line -- nowrap + ellipsis on the markdown container and
   display:inline on its <p>s -- which squashed "Premier League\n\nENG" into
   "Premier League ...". Undo that so the two-line pill layout above holds. */
div.stButton > button [data-testid="stMarkdownContainer"] {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}
div.stButton > button [data-testid="stMarkdownContainer"] p {
    display: block !important;
}
div.stButton > button p {
    font-size: 14px;
}
div.stButton > button p:last-child {
    margin-top: 1px !important;
    font-size: 11px;
    letter-spacing: 0.06em;
    opacity: 0.7;
}
/* The language pills are one-line buttons: keep their own size */
.st-key-lang_switcher div.stButton > button p {
    font-size: inherit !important;
    letter-spacing: normal !important;
    opacity: 1 !important;
    margin: 0 !important;
}

/* Laptop/tablet widths: nine pills in one row leave ~107px each at 1280px,
   less than "Championship" needs, so long names broke mid-word ("Cham pions
   hip"). Below 1440px: slightly smaller text and side padding (keeps one row
   down to 1280px); below 1280px: wrap to two rows of 5 + 4. */
@media (min-width: 601px) and (max-width: 1439px) {
    div[data-testid="stHorizontalBlock"]:has(div.stButton):not(.st-key-lang_switcher *) div.stButton > button {
        padding-left: 4px !important;
        padding-right: 4px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div.stButton):not(.st-key-lang_switcher *) div.stButton > button p:first-child {
        font-size: 13px !important;
    }
}
@media (min-width: 601px) and (max-width: 1279px) {
    div[data-testid="stHorizontalBlock"]:has(div.stButton):not(.st-key-lang_switcher *) {
        flex-wrap: wrap !important;
        gap: 8px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div.stButton):not(.st-key-lang_switcher *) > div[data-testid="stColumn"] {
        flex: 0 0 calc((100% - 32px) / 5) !important;
        width: calc((100% - 32px) / 5) !important;
        min-width: unset !important;
    }
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
    /* On a 320px phone each half-width pill leaves ~100px for text after
       Streamlit's 12px side padding -- just short of "Championship", which
       then broke mid-word ("Championshi / p"). Tighter padding gives it room. */
    div[data-testid="stHorizontalBlock"]:has(div.stButton):not(.st-key-lang_switcher *) div.stButton > button {
        padding-left: 4px !important;
        padding-right: 4px !important;
    }
}




div.stButton > button {
    border-radius: 8px !important;
    transition: background-color 0.2s ease;
}
/* Hide Streamlit's own chrome (hamburger menu, "Deploy" button, "Made with
   Streamlit" footer) -- a polished page shouldn't visibly announce the
   dev tool it was built with. display:none (not visibility) so nothing keeps
   reserving space.
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
/* absolute, not fixed: pinned to the window it floated over whatever
   scrolled underneath (league buttons, cards); now it sits in the hero and
   scrolls away with it, like the phone layout already did. */
/* stMain (the scroll container) is position:static, so without this the
   switcher anchored to a wrapper outside it and stayed put while scrolling. */
[data-testid="stMainBlockContainer"] { position: relative; }
.st-key-lang_switcher {
    position: absolute;
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
[data-testid="stElementContainer"]:has(style) [data-testid="stMarkdownContainer"] {
    display: contents;
}
</style>
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
                st.query_params["lang"] = code
                st.rerun()

# -------------------------------
# 6️⃣ LEAGUES

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

# -------------------------------
# 7️⃣ HERO SECTION

st.markdown(
    f'<div class="hero-banner">'
    f'<div class="hero-inner"><div class="hero-copy">'
    f'<h1>{t("hero_title")}</h1>'
    f'<p class="hero-lead">{t("hero_lead")}</p>'
    f'<p class="hero-description">{t("hero_description")}</p>'
    f'<p class="hero-meta">{t("hero_byline")}<span class="hero-links">'
    f'<a href="https://www.linkedin.com/in/victoria-friss-de-kereki/" target="_blank">LinkedIn</a>'
    f'<a href="https://medium.com/@vickyfrissdekereki" target="_blank">Medium</a>'
    f'<a href="https://github.com/vickyfriss" target="_blank">GitHub</a>'
    f'<a href="mailto:vicky_friss@hotmail.com">{t("contact_email")}</a></span></p>'
    f'</div></div></div>',
    unsafe_allow_html=True,
)

# -------------------------------
# 8️⃣ LEAGUE SELECTION



# Built from plain st.button + st.columns rather than st.segmented_control --
# see the CSS comment above for why. st.columns naturally divides the full
# available width evenly, which is also what gives this the same width as the
# table below without any CSS width-fighting.
# The chosen league also lives in the page URL (?league=laliga_spain), so a
# refresh keeps it and a shared link opens straight on that league.
if "selected_league" not in st.session_state:
    url_league = st.query_params.get("league")
    st.session_state.selected_league = url_league if url_league in league_header_labels else DEFAULT_LEAGUE_KEY

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
            st.query_params["league"] = key
            st.rerun()

league = st.session_state.selected_league
selected_display_name = league_header_labels[league]

# Browser tab names the league ("La Liga · Football League Simulator"), in the
# page's language, so open tabs and shared links say which league they're on.
st.set_page_config(page_title=f'{selected_display_name.split(" (")[0]} · {t("hero_title")}')


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
    # Exact time in the visitor's own time zone (from their browser), labelled
    # "BST" / "CET" where the zone has a name, "UTC−3" where it doesn't; plain
    # UTC if the browser didn't send one.
    local_dt, tz_label = run_dt, "UTC"
    try:
        local_dt = run_dt.astimezone(ZoneInfo(st.context.timezone))
        tz_label = local_dt.strftime("%Z")
        if not tz_label.isalpha():
            offset = local_dt.utcoffset().total_seconds() / 3600
            sign = "+" if offset > 0 else "\u2212"
            tz_label = "UTC" if offset == 0 else f"UTC{sign}{abs(offset):g}"
    except Exception:
        pass
    formatted_date = format_run_date(local_dt, st.session_state.lang)
    st.markdown(
        # Compact status pill: "Updated 6 hours ago" first, exact time muted after.
        # The dot turns amber once the data is over 36h old (the pipeline runs
        # daily), so a missed run is visible without reading the date.
        f'<div class="status-wrap"><div class="status-banner{" stale" if datetime.now(timezone.utc) - run_dt > timedelta(hours=36) else ""}" title="{t("last_run", date=formatted_date).replace(" UTC", " " + tz_label)}">'
        f'<span class="status-dot"></span><b>{t("updated_ago", ago=format_time_ago(run_dt))}</b>'
        f'<span class="status-sep">·</span><span class="status-date">{formatted_date} {tz_label}</span></div></div>',
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

# Goal difference isn't in the simulation output, but the league table saved alongside it has
# it. Kept numeric here; the table shows "8" / "0" / "−3" with a true minus sign, blank if a team
# can't be matched.
_table_file = f"data/league_table/{league}.csv"
if os.path.exists(_table_file) and "GD" not in pos_pct_df.columns:
    try:
        _tbl = pd.read_csv(_table_file)
        # Same name mapping the pipeline applies to the standings (e.g. ESPN's "Deportivo" -> "Deportivo La Coruña"),
        # so every team in the simulation finds its row
        try:
            import importlib.util
            _spec = importlib.util.spec_from_file_location("dataset_processing", "2_dataset_processing.py")
            _dp = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_dp)
            _tbl["team"] = _tbl["team"].replace(_dp.mappings.get(league, {}))
        except Exception:
            pass
        _gd = _tbl.drop_duplicates("team").set_index("team")["gd"]
        _gd_col = pos_pct_df["TEAM"].map(_gd)
        pos_pct_df.insert(pos_pct_df.columns.get_loc("GP") + 1, "GD", _gd_col.astype("Int64"))
    except Exception:
        pass
if "GD" not in pos_pct_df.columns:   # the frozen-column CSS assumes 5 leading columns, so always have one
    pos_pct_df.insert(pos_pct_df.columns.get_loc("GP") + 1, "GD", pd.array([pd.NA] * len(pos_pct_df), dtype="Int64"))
# Standard league-table order: games played, goal difference, then points last
_lead = ["POS", "TEAM", "GP", "GD", "PTS"]
pos_pct_df = pos_pct_df[_lead + [c for c in pos_pct_df.columns if c not in _lead]]

# How far into the season the league is: a double round-robin is 2 x (teams - 1)
# games, and the furthest-along team's games played is the current matchday.
# Tells people how much the predictions can still move.
season_progress = ""
if len(pos_pct_df):
    total_games = 2 * (len(pos_pct_df) - 1)
    matchday = int(pos_pct_df["GP"].max())
    season_progress = f'<div class="season-progress">{t("season_progress", md=matchday, total=total_games, left=total_games - matchday)}</div>'

st.markdown(f"""
<div style="text-align:center; margin: 0 0 0.25rem;">
    <h2 class="results-heading">{selected_display_name.split(" (")[0]}</h2>
    {season_progress}
</div>
""", unsafe_allow_html=True)

# -------------------------------
# 10️⃣.5 HEADLINE CARDS (title race, race for the top places, relegation)

zones = LEAGUE_ZONES.get(league, {})
pos_cols = [c for c in pos_pct_df.columns if str(c).isdigit()]

def zone_pct(first, last):
    return pos_pct_df[[c for c in pos_cols if first <= int(c) <= last]].sum(axis=1)

# Change in each card's chance over the last 7 days, from the saved runs
data_version = os.path.getmtime("data/last_updated.txt") if os.path.exists("data/last_updated.txt") else None
history = load_history(league, data_version)
changes, base_day = week_changes(history)
delta_tip = html.escape(t("delta_tip", date=short_date(base_day, st.session_state.lang))) if base_day is not None else ""

def metric_changes(metric):
    if changes is None or metric not in changes.index.get_level_values("metric"):
        return {}
    return changes.xs(metric, level="metric").to_dict()

def change_badge(delta, bad_when_up):
    # Moves under half a point are mostly simulation noise, so they get no arrow
    if delta is None or abs(delta) < 0.5:
        return ""
    good = (delta < 0) if bad_when_up else (delta > 0)
    return (f'<span class="delta {"good" if good else "bad"}" title="{delta_tip}">'
            f'{"▲" if delta > 0 else "▼"}{abs(delta):.1f}</span>')

def headline_rows(probs, cutoff_after=None, cutoff_label="", deltas=None, bad_when_up=False):
    rows = []
    for rank, (i, p) in enumerate(probs.items(), start=1):
        team = pos_pct_df.at[i, "TEAM"]
        rows.append(
            f'<div class="headline-row"><span class="team">{html.escape(team)}</span>'
            f'<span class="pct">{change_badge((deltas or {}).get(team), bad_when_up)}{"&lt;0.1" if 0 < p < 0.1 else f"{p:.1f}"}%</span>'
            f'<div class="headline-bar"><span style="width:{min(p, 100):.1f}%"></span></div></div>'
        )
        if rank == cutoff_after and rank < len(probs):
            rows.append(f'<div class="headline-cutoff">{cutoff_label}</div>')
    return "".join(rows)

# Each card shows its three teams and expands on click to a longer list. Built
# on a hidden checkbox + <label> (the whole card is the label, so a tap
# anywhere toggles it -- works on phones, where there's no hover) rather than
# <details>, which can't be stretched to match its neighbours' height. The
# expanded list replaces the short one rather than adding below it, because
# for the race cards it's a different slice: the full ranking from 1st, with
# the cut-off marked.
def headline_card(card_id, css_class, title, sub, short_probs, long_probs, cutoff_after=None, cutoff_label="", metric=None):
    deltas, bad_when_up = metric_changes(metric), metric == "relegation"
    return (
        f'<div class="headline-card {css_class}">'
        f'<input type="checkbox" id="{card_id}" class="headline-check">'
        f'<label for="{card_id}" class="headline-label">'
        f'<div class="headline-title">{title}</div><div class="headline-sub">{sub}</div>'
        f'<div class="headline-short">{headline_rows(short_probs, deltas=deltas, bad_when_up=bad_when_up)}</div>'
        f'<div class="headline-long">{headline_rows(long_probs, cutoff_after, cutoff_label, deltas, bad_when_up)}</div>'
        f'<span class="headline-toggle"><span class="more">{t("card_show_more")} ▾</span>'
        f'<span class="less">{t("card_show_less")} ▴</span></span>'
        f'</label></div>'
    )

if pos_cols and zones:
    top_first, top_last = zones["top"]
    # The race card shows the teams either side of the cut-off (e.g. the 4th,
    # 5th and 6th most likely to finish top 4), not the top three again --
    # those are usually near-certain and already in the title card.
    race = zone_pct(top_first, top_last).sort_values(ascending=False)
    title_probs = zone_pct(1, 1).sort_values(ascending=False)
    rel_probs = zone_pct(*zones["relegation"]).sort_values(ascending=False)
    cards = [
        headline_card(f"hc-{league}-title", "", t("card_title_title"), t("card_title_sub"),
                      title_probs.head(3), title_probs.head(8), metric="title"),
        headline_card(f"hc-{league}-race", "", t(f"card_race_title_{zones['top_kind']}"), t("card_race_sub", n=top_last),
                      race.iloc[top_last - 1:top_last + 2], race.head(top_last + 6),
                      cutoff_after=top_last, cutoff_label=t("card_cutoff", n=top_last), metric="top"),
    ]
    # Leagues with promotion play-offs (the Championship) also get a play-off
    # race: same edge-of-the-cut-off idea, for a top-6 finish.
    if "top_playoff" in zones:
        po_last = zones["top_playoff"][1]
        playoff_race = zone_pct(1, po_last).sort_values(ascending=False)
        cards.append(headline_card(f"hc-{league}-playoff", "", t("card_playoff_title"), t("card_race_sub", n=po_last),
                                   playoff_race.iloc[po_last - 1:po_last + 2], playoff_race.head(po_last + 6),
                                   cutoff_after=po_last, cutoff_label=t("card_cutoff", n=po_last), metric="playoff"))
    cards += [
        # Subtitle names the exact positions counted; where a relegation
        # play-off spot exists (e.g. Eredivisie 16th) it says "direct" relegation
        headline_card(f"hc-{league}-relegation", "relegation", t("card_rel_title"),
                      t("card_rel_sub_playoff", first=zones["relegation"][0], last=zones["relegation"][1])
                      if "rel_playoff" in zones else
                      t("card_rel_sub", first=zones["relegation"][0], last=zones["relegation"][1]),
                      rel_probs.head(3), rel_probs.head(8), metric="relegation"),
    ]
    # Biggest changes: news the other cards don't already show. A move counts
    # when it's at least 3 points (smaller ones are mostly simulation noise),
    # in a race that's still open (the chance is between 5% and 95% before or
    # after), and the team isn't already in that race's card with its arrow.
    # Each team appears once, with its biggest such move; a bigger relegation
    # chance is bad news, so it's red.
    if changes is not None and len(changes):
        latest = history[history["day"] == history["day"].max()].set_index(["team", "metric"])["pct"]
        shown = {(pos_pct_df.at[i, "TEAM"], metric) for metric, probs in [
            ("title", title_probs.head(3)), ("top", race.iloc[top_last - 1:top_last + 2]),
            ("relegation", rel_probs.head(3))] + ([("playoff", playoff_race.iloc[po_last - 1:po_last + 2])]
                                                  if "top_playoff" in zones else []) for i in probs.index}
        moves = []
        for team, team_changes in changes.groupby(level="team"):
            options = []
            for (_, metric), delta in team_changes.items():
                now = latest.get((team, metric))
                if now is None or abs(delta) < 3 or (team, metric) in shown:
                    continue
                if not (5 <= now <= 95 or 5 <= now - delta <= 95):
                    continue
                options.append((abs(delta), team, metric, delta, now))
            if options:
                moves.append(max(options))
        moves.sort(reverse=True)
        def mover_rows(rows):
            return "".join(
                # One line per team, like the other cards' rows; the before and
                # after chances are in the row's hover text
                f'<div class="mover-row" title="{html.escape(metric_label(league, metric))}: {now - delta:.1f}% → {now:.1f}%">'
                f'<span class="team">{html.escape(team)}</span>'
                f'<span class="mv-what">{metric_label(league, metric)}</span>'
                f'<span class="mv-delta {"bad" if (delta > 0) == (metric == "relegation") else "good"}">'
                f'{"▲" if delta > 0 else "▼"}{abs(delta):.1f}</span></div>'
                for _, team, metric, delta, now in rows
            )
        if moves:
            cards.append(
                f'<div class="headline-card movers"><input type="checkbox" id="hc-{league}-movers" class="headline-check">'
                f'<label for="hc-{league}-movers" class="headline-label">'
                f'<div class="headline-title">{t("card_movers_title")}</div><div class="headline-sub">{t("card_movers_sub")}</div>'
                f'<div class="headline-short">{mover_rows(moves[:3])}</div>'
                f'<div class="headline-long">{mover_rows(moves[:8])}</div>'
                + (f'<span class="headline-toggle"><span class="more">{t("card_show_more")} ▾</span>'
                   f'<span class="less">{t("card_show_less")} ▴</span></span>' if len(moves) > 3 else "")
                + '</label></div>'
            )
    delta_note = (f'<div class="delta-note">{t("delta_note", date=short_date(base_day, st.session_state.lang))}</div>'
                  if base_day is not None else "")
    layout = {4: " four", 5: " five"}.get(len(cards), "")
    st.markdown(f'<div class="headline-cards{layout}">{"".join(cards)}</div>{delta_note}', unsafe_allow_html=True)

# -------------------------------
# 11️⃣ STYLE AND DISPLAY TABLE

styled_table, num_cols = style_probabilities_table(pos_pct_df, column_labels=COLUMN_LABELS[st.session_state.lang], zones=zones)
zone_legend = "".join(
    f'<span><span class="swatch" style="background:{ZONE_COLORS[zone]}"></span>'
    f'{t("zone_" + zones["top_kind"]) if zone == "top" else t("zone_" + zone)}</span>'
    for zone in ZONE_COLORS if zone in zones
)
if zone_legend:
    zone_legend = f'<div class="zone-legend">{zone_legend}<span class="zone-note">{t("zones_note")}</span></div>'
st.markdown(
    f'<div class="table-card"><div class="table-wrapper">{add_cell_tooltips(styled_table.to_html(escape=False), pos_pct_df, load_recent_form(league, data_version), load_next_games(league, data_version))}</div>{zone_legend}</div>',
    unsafe_allow_html=True
)

# -------------------------------
# 12️⃣ TABLE CAPTION

st.caption(t("table_caption"))

# -------------------------------
# 1️⃣3️⃣ SEASON TREND
# Drawn in the browser with Vega-Embed rather than st.altair_chart: Streamlit
# converts chart data through pyarrow, and with NumPy pinned below 2 that
# conversion crashed the whole server (a segfault, not an error) in testing.
# The frame follows the visitor's light or dark setting like the rest of the page.
def trend_chart_html(chart_light, chart_dark):
    major = alt.SCHEMA_VERSION.lstrip("v").split(".")[0]
    vega, embed = {"5": ("5", "6"), "6": ("6", "7")}.get(major, ("6", "7"))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/vega@{vega}"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@{major}"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@{embed}"></script>
<style>
html, body {{ margin: 0; background: transparent; font-family: Inter, Roboto, Arial, sans-serif; }}
#chart {{ width: 100%; }}
#vg-tooltip-element {{ font-family: Inter, Roboto, Arial, sans-serif; font-size: 12px; border-radius: 8px; }}
#vg-tooltip-element td.key {{ padding-right: 14px; }}
#vg-tooltip-element td.value {{ text-align: right; font-variant-numeric: tabular-nums; }}
</style></head><body><div id="chart"></div><script>
const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
const ink = dark ? "#c9c9c9" : "#555555", grid = dark ? "#333333" : "#ececec";
const spec = dark ? {chart_dark.to_json()} : {chart_light.to_json()};
// Sized to the width it's drawn at: fewer date labels, a shorter chart and a
// legend that wraps on phones, so everything fits the frame
const narrow = document.body.clientWidth < 560;
if (narrow) spec.height = 290;
spec.config = Object.assign(spec.config || {{}}, {{
  background: null, font: "Inter, Roboto, Arial, sans-serif", view: {{stroke: null}},
  axis: {{labelColor: ink, labelFontSize: 12, domain: false, ticks: false, gridColor: grid}},
  axisX: {{tickCount: narrow ? 4 : 7, labelOverlap: "greedy", labelFlush: true, labelSeparation: 8, labelPadding: 10}},
  legend: {{labelColor: ink, columns: narrow ? 2 : 6, labelLimit: narrow ? 125 : 220}}, rule: {{color: ink}}, text: {{color: ink}}
}});
vegaEmbed("#chart", spec, {{actions: false, renderer: "svg", tooltip: {{theme: dark ? "dark" : "light"}}}});
</script></body></html>"""


# Each team's chance of the title, the top places or relegation after every
# day's last update this season. Starts with the teams most likely to finish
# there now; any team can be added.
TREND_COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#8C6D31", "#7F7F7F"]

# Club colours for the trend chart: (main colour, second colour). The chart uses
# the main colour unless it's hard to see on the page (white or yellow on the
# light page, black or navy on the dark one) or too close to a team already
# drawn; then the second colour; then a standard chart colour. Teams left out
# just get a standard chart colour.
TEAM_COLORS = {
    # Premier League
    "Arsenal": ("#EF0107", "#063672"), "Manchester City": ("#6CABDD", "#1C2C5B"),
    "Brighton & Hove Albion": ("#0057B8", "#FFCD00"), "Chelsea": ("#034694", "#DBA111"),
    "Liverpool": ("#C8102E", "#00B2A9"), "Brentford": ("#E30613", "#FBB800"),
    "AFC Bournemouth": ("#DA291C", "#000000"), "Tottenham Hotspur": ("#132257", "#FFFFFF"),
    "Aston Villa": ("#670E36", "#95BFE5"), "Hull City": ("#F5A12D", "#000000"),
    "Leeds United": ("#FFFFFF", "#1D428A"), "Newcastle United": ("#241F20", "#FFFFFF"),
    "Ipswich Town": ("#3A64A3", "#FFFFFF"), "Everton": ("#003399", "#FFFFFF"),
    "Fulham": ("#FFFFFF", "#000000"), "Coventry City": ("#59CBE8", "#1C1C1C"),
    "Manchester United": ("#DA291C", "#FBE122"), "Crystal Palace": ("#1B458F", "#C4122E"),
    "Nottingham Forest": ("#DD0000", "#FFFFFF"), "Sunderland": ("#EB172B", "#000000"),
    # Championship
    "Middlesbrough": ("#E11B22", "#FFFFFF"), "Swansea City": ("#FFFFFF", "#000000"),
    "Wolverhampton Wanderers": ("#FDB913", "#231F20"), "West Bromwich Albion": ("#122F67", "#FFFFFF"),
    "Southampton": ("#D71920", "#FFFFFF"), "Birmingham City": ("#1E3E8A", "#FFFFFF"),
    "Stoke City": ("#E03A3E", "#FFFFFF"), "West Ham United": ("#7A263A", "#1BB1E7"),
    "Queens Park Rangers": ("#1D5BA4", "#FFFFFF"), "Sheffield United": ("#EE2737", "#000000"),
    "Portsmouth": ("#001489", "#FFFFFF"), "Millwall": ("#001D5E", "#FFFFFF"),
    "Blackburn Rovers": ("#009EE0", "#FFFFFF"), "Bristol City": ("#E21A23", "#FFFFFF"),
    "Norwich City": ("#FFF200", "#00A650"), "Lincoln City": ("#E31B23", "#000000"),
    "Cardiff City": ("#0070B5", "#D11524"), "Wrexham": ("#C8102E", "#FFFFFF"),
    "Bolton Wanderers": ("#FFFFFF", "#263C7E"), "Charlton Athletic": ("#D4021D", "#FFFFFF"),
    "Watford": ("#FBEE23", "#ED2127"), "Burnley": ("#6C1D45", "#99D6EA"),
    "Derby County": ("#FFFFFF", "#000000"), "Preston North End": ("#FFFFFF", "#0B2C5F"),
    # Serie A
    "Lazio": ("#87D8F7", "#1B3D6D"), "Internazionale": ("#0068A8", "#000000"),
    "AS Roma": ("#8E1F2F", "#F0BC42"), "Como": ("#003DA5", "#FFFFFF"),
    "AC Milan": ("#FB090B", "#000000"), "Frosinone": ("#FBE122", "#00438C"),
    "Juventus": ("#000000", "#FFFFFF"), "Napoli": ("#12A0D7", "#003C82"),
    "Bologna": ("#A21C26", "#1A2F48"), "Torino": ("#8A1E03", "#FFFFFF"),
    "Genoa": ("#AD1919", "#002D72"), "Cagliari": ("#B01E2B", "#002350"),
    "Atalanta": ("#1E71B8", "#000000"), "Lecce": ("#F7D117", "#D31E25"),
    "Sassuolo": ("#00A752", "#000000"), "Monza": ("#E30613", "#FFFFFF"),
    "Fiorentina": ("#592C82", "#FFFFFF"), "Parma": ("#FFD200", "#003D7C"),
    "Udinese": ("#000000", "#FFFFFF"), "Venezia": ("#F37021", "#00753E"),
    # La Liga
    "Barcelona": ("#A50044", "#004D98"), "Atlético Madrid": ("#CB3524", "#272E61"),
    "Real Madrid": ("#FFFFFF", "#00529F"), "Real Betis": ("#00954C", "#FFFFFF"),
    "Real Sociedad": ("#0067B1", "#FFFFFF"), "Sevilla": ("#FFFFFF", "#D71920"),
    "Athletic Club": ("#EE2523", "#FFFFFF"), "Villarreal": ("#FFE667", "#005187"),
    "Celta Vigo": ("#8AC3EE", "#E5254E"), "Alavés": ("#0761AF", "#FFFFFF"),
    "Rayo Vallecano": ("#E53027", "#FFFFFF"), "Getafe": ("#005999", "#FFFFFF"),
    "Deportivo La Coruña": ("#1B5DAA", "#FFFFFF"), "Espanyol": ("#007FC8", "#FFFFFF"),
    "Osasuna": ("#D91A21", "#0A346F"), "Racing Santander": ("#00824A", "#FFFFFF"),
    "Elche": ("#05642C", "#FFFFFF"), "Levante": ("#B5104D", "#004B98"),
    "Valencia": ("#FFFFFF", "#F18E00"), "Málaga": ("#0D5AA7", "#FFFFFF"),
    # Bundesliga
    "Bayern Munich": ("#DC052D", "#0066B2"), "Borussia Dortmund": ("#FDE100", "#000000"),
    "SC Freiburg": ("#E3000F", "#000000"), "RB Leipzig": ("#DD0741", "#001F47"),
    "Werder Bremen": ("#1D9053", "#FFFFFF"), "Bayer Leverkusen": ("#E32221", "#000000"),
    "Eintracht Frankfurt": ("#E1000F", "#000000"), "Mainz": ("#C3141E", "#FFFFFF"),
    "FC Augsburg": ("#BA3733", "#46714D"), "VfB Stuttgart": ("#FFFFFF", "#E32219"),
    "TSG Hoffenheim": ("#1C63B7", "#FFFFFF"), "FC Cologne": ("#ED1C24", "#FFFFFF"),
    "SC Paderborn 07": ("#10206B", "#000000"), "Hamburg SV": ("#0A3F86", "#FFFFFF"),
    "1. FC Union Berlin": ("#EB1923", "#FFFFFF"), "Schalke 04": ("#004D9D", "#FFFFFF"),
    "Borussia Mönchengladbach": ("#000000", "#00A651"),
    # Ligue 1
    "Paris Saint-Germain": ("#004170", "#DA291C"), "Lille": ("#E01E13", "#1E2D5C"),
    "Lyon": ("#FFFFFF", "#14387F"), "Paris FC": ("#1D2E5C", "#FFFFFF"),
    "Stade Rennais": ("#E13327", "#000000"), "Marseille": ("#2FAEE0", "#FFFFFF"),
    "AS Monaco": ("#E51B22", "#FFFFFF"), "Nice": ("#E2001A", "#000000"),
    "Lens": ("#FFE600", "#EC1C24"), "Lorient": ("#F58113", "#000000"),
    "Toulouse": ("#5B2C83", "#FFFFFF"), "Strasbourg": ("#009FE3", "#FFFFFF"),
    "AJ Auxerre": ("#FFFFFF", "#0062A9"), "Brest": ("#E2001A", "#FFFFFF"),
    "Angers": ("#000000", "#FFFFFF"), "Troyes": ("#005CA4", "#FFFFFF"),
    "Le Mans": ("#DA291C", "#F7D117"), "Le Havre AC": ("#6CB4E4", "#1B2A4E"),
    # Eredivisie
    "Feyenoord Rotterdam": ("#E30613", "#FFFFFF"), "Ajax Amsterdam": ("#D2122E", "#FFFFFF"),
    "PSV Eindhoven": ("#ED1C24", "#FFFFFF"), "FC Twente": ("#E3000F", "#FFFFFF"),
    "AZ Alkmaar": ("#DB0021", "#FFFFFF"), "Fortuna Sittard": ("#FFE500", "#009A44"),
    "Heerenveen": ("#005FAE", "#FFFFFF"), "FC Groningen": ("#2E9B48", "#FFFFFF"),
    "SC Cambuur": ("#FFD200", "#004A9F"), "Go Ahead Eagles": ("#E30613", "#FFD700"),
    "Sparta Rotterdam": ("#E30613", "#FFFFFF"), "FC Utrecht": ("#E30613", "#FFFFFF"),
    "NEC Nijmegen": ("#D51F26", "#00843D"), "PEC Zwolle": ("#0071BC", "#00A651"),
    "Excelsior": ("#E30613", "#000000"), "Telstar": ("#E30613", "#FFFFFF"),
    "ADO Den Haag": ("#00A650", "#FFD700"), "Willem II": ("#DA291C", "#003DA5"),
    # Primeira Liga
    "FC Porto": ("#003893", "#FFFFFF"), "Benfica": ("#E83030", "#FFFFFF"),
    "Sporting CP": ("#008057", "#FFFFFF"), "Santa Clara": ("#E30613", "#FFFFFF"),
    "Arouca": ("#F5D300", "#002E6D"), "Gil Vicente": ("#D71920", "#1D428A"),
    "Braga": ("#E30613", "#FFFFFF"), "Moreirense": ("#00824A", "#FFFFFF"),
    "FC Famalicao": ("#1E4C9A", "#FFFFFF"), "Vitória de Guimaraes": ("#FFFFFF", "#000000"),
    "Maritimo": ("#00843D", "#D71920"), "Rio Ave": ("#009A49", "#FFFFFF"),
    "C.D. Nacional": ("#000000", "#FFFFFF"), "Estoril": ("#FFD700", "#003DA5"),
    # Série A (Brazil)
    "Flamengo": ("#C4161C", "#000000"), "Palmeiras": ("#006437", "#FFFFFF"),
    "Cruzeiro": ("#2F529E", "#FFFFFF"), "Fluminense": ("#870A28", "#00613C"),
    "Athletico Paranaense": ("#C8102E", "#000000"), "Bahia": ("#005BAA", "#D71920"),
    "Atlético-MG": ("#000000", "#FFFFFF"), "Santos": ("#FFFFFF", "#000000"),
    "Red Bull Bragantino": ("#DA1F3D", "#FFFFFF"), "São Paulo": ("#FFFFFF", "#D71920"),
    "Coritiba": ("#00544E", "#FFFFFF"), "Botafogo": ("#000000", "#FFFFFF"),
    "Vasco da Gama": ("#000000", "#E30613"), "Vitória": ("#E30613", "#000000"),
    "Grêmio": ("#0D80BF", "#000000"), "Mirassol": ("#FFDD00", "#00843D"),
    "Corinthians": ("#FFFFFF", "#000000"), "Internacional": ("#E5050F", "#FFFFFF"),
    "Remo": ("#1B2B6B", "#FFFFFF"), "Chapecoense": ("#00843D", "#FFFFFF"),
}

def _luminance(hex_color):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

def _lab(hex_color):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(int(hex_color[i:i + 2], 16)) for i in (1, 3, 5))
    x, y, z = ((0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.9505, 0.2126 * r + 0.7152 * g + 0.0722 * b,
               (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.089)
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))

def _too_close(a, b):
    return sum((p - q) ** 2 for p, q in zip(_lab(a), _lab(b))) ** 0.5 < 25

def team_line_colors(teams, dark):
    """One colour per team, in order: its own colours where they show up on the
    page and don't clash with another team's, then chart colours for the rest."""
    visible = (lambda c: _luminance(c) > 0.06) if dark else (lambda c: _luminance(c) < 0.55)
    chosen = [None] * len(teams)
    for i, team in enumerate(teams):
        chosen[i] = next((c for c in TEAM_COLORS.get(team, ())
                          if visible(c) and not any(o and _too_close(c, o) for o in chosen)), None)
    for i in range(len(teams)):
        if chosen[i] is None:
            chosen[i] = next((c for c in TREND_COLORS if not any(o and _too_close(c, o) for o in chosen)),
                             TREND_COLORS[i % len(TREND_COLORS)])
    return chosen


with st.container(key="trend_card"):
    st.markdown(
        f'<div class="trend-head"><span class="section-eyebrow">{t("trend_eyebrow")}</span>'
        f'<h3 class="trend-title">{t("trend_title")}</h3><p class="trend-sub">{t("trend_sub")}</p></div>',
        unsafe_allow_html=True,
    )
    metrics = league_metrics(league)
    if not metrics or history["day"].nunique() < 2:
        st.caption(t("trend_empty"))
    else:
        metric = st.radio(t("trend_title"), list(metrics), format_func=lambda m: metric_label(league, m),
                          horizontal=True, key=f"trend_metric_{league}", label_visibility="collapsed")
        data = history[history["metric"] == metric]
        now = data[data["day"] == data["day"].max()].set_index("team")["pct"].sort_values(ascending=False)
        defaults = list(now[now >= 0.5].index[:5]) or list(now.index[:2])
        options = [team for team in pos_pct_df["TEAM"] if team in now.index]
        teams = st.multiselect(t("trend_teams"), options, default=[team for team in defaults if team in options],
                               max_selections=len(TREND_COLORS), key=f"trend_teams_{league}_{metric}")
        if teams:
            data = data[data["team"].isin(teams)].sort_values(["team", "day"])
            top = min(100, max(10, np.ceil(data["pct"].max() * 1.1 / 10) * 10))
            # Between two runs, a team's chance can only change once games are
            # played. So the line stays flat at the last prediction until the next
            # league game (through Brazil's World Cup break, for example), and breaks
            # only where games were played for more than 3 days without a run.
            match_days = sorted(load_match_days(league, data_version))
            rows = []
            for team, team_rows in data.groupby("team", sort=False):
                stretch, prev = 0, None
                for day, pct in zip(team_rows["day"], team_rows["pct"]):
                    if prev is not None and (day - prev[0]).days > 1:
                        first_game = next((d for d in match_days if prev[0] < d < day), None)
                        rows.append((first_game or day - pd.Timedelta(days=1), team, prev[1], stretch))
                        if first_game is not None and (day - first_game).days > 3:
                            stretch += 1
                    rows.append((day, team, pct, stretch))
                    prev = (day, pct)
            data = pd.DataFrame(rows, columns=["day", "team", "pct", "stretch"])
            # Matchdays: a faint line on each one's middle date, labelled every 5,
            # and a shaded stretch, named by its reason, where 10 days or more
            # pass without a league game
            first_day, last_day = data["day"].min(), data["day"].max()
            matchdays = sorted((d, md) for md, d in load_matchday_dates(league, data_version).items()
                               if first_day <= d <= last_day)
            md_marks = alt.Data(values=[
                {"day": f"{d:%Y-%m-%d}T12:00:00", "label": f'{t("md_short")} {md}' if md % 5 == 0 else ""}
                for d, md in matchdays
            ])
            # Breaks come from the actual game days, not the matchdays: rearranged
            # games spread a matchday out, but a break means no game at all
            game_days = sorted(d for d in load_match_days(league, data_version) if first_day <= d <= last_day)
            breaks = alt.Data(values=[
                {"start": f"{a + pd.Timedelta(days=1):%Y-%m-%d}T00:00:00", "end": f"{b:%Y-%m-%d}T00:00:00",
                 "mid": f"{a + (b - a) / 2:%Y-%m-%d}T12:00:00", "label": break_reason(a, b)}
                for a, b in zip(game_days, game_days[1:]) if (b - a).days >= 10
            ])
            # Plain values: the chart is drawn in the browser (see below), so the
            # data goes straight into the chart spec. Noon local time keeps each
            # run on its own day in every time zone.
            data = alt.Data(values=[
                {"day": f"{d:%Y-%m-%d}T12:00:00", "team": team, "share": round(p / 100, 4), "stretch": int(k)}
                for d, team, p, k in zip(data["day"], data["team"], data["pct"], data["stretch"])
            ])
            date_format = "%-d %b" if st.session_state.lang == "en" else "%d/%m"
            def build_chart(colors):
                hover = alt.selection_point(fields=["day"], nearest=True, on="pointerover", clear="pointerout", empty=False)
                base = alt.Chart(data).encode(
                    x=alt.X("day:T", title=None, axis=alt.Axis(format=date_format, labelAngle=0, grid=False)),
                    y=alt.Y("share:Q", title=None, scale=alt.Scale(domain=[0, top / 100], clamp=True),
                            axis=alt.Axis(format=".0%", tickCount=5)),
                    color=alt.Color("team:N", scale=alt.Scale(domain=teams, range=colors),
                                    legend=alt.Legend(orient="bottom", title=None, symbolType="stroke", symbolStrokeWidth=3,
                                                      columnPadding=22, labelFontSize=12)),
                )
                # Pointing at a line highlights that team: the other lines fade, and its
                # name and latest chance appear at the end of the line. A wide, invisible
                # copy of each line makes the lines easy to hit. Anywhere else, one
                # tooltip per day lists every selected team (dots and brackets in names
                # are escaped for Vega).
                pick = alt.selection_point(fields=["team"], clear="pointerout",
                                          on="pointerover[event.item && event.item.mark.marktype === 'line']")
                escape = lambda name: re.sub(r"([.\[\]\\])", r"\\\1", name)
                chart = alt.layer(
                    alt.Chart(breaks).mark_rect(opacity=0.06, color="#888888").encode(x="start:T", x2="end:T"),
                    alt.Chart(breaks).mark_text(baseline="top", dy=16, fontSize=10, opacity=0.55)
                        .encode(x="mid:T", y=alt.value(0), text="label:N"),
                    alt.Chart(md_marks).mark_rule(opacity=0.14, strokeWidth=1).encode(x="day:T"),
                    alt.Chart(md_marks).mark_text(align="left", baseline="top", dx=3, dy=2, fontSize=10, opacity=0.55)
                        .encode(x="day:T", y=alt.value(0), text="label:N"),
                    base.mark_line(strokeWidth=2.5, interpolate="monotone").encode(
                        detail="stretch:N", opacity=alt.condition(pick, alt.value(1), alt.value(0.15))),
                    base.mark_circle(size=60).encode(opacity=alt.condition(hover, alt.value(1), alt.value(0))),
                    alt.Chart(data).transform_pivot("team", value="share", groupby=["day"]).mark_rule(strokeDash=[4, 4]).encode(
                        x="day:T",
                        opacity=alt.condition(hover, alt.value(0.5), alt.value(0)),
                        tooltip=[alt.Tooltip("day:T", title=t("trend_date"), format=date_format)]
                                + [alt.Tooltip(f"{escape(team)}:Q", title=team, format=".1%") for team in teams],
                    ).add_params(hover),
                    base.transform_filter({"param": pick.name, "empty": False})
                        .transform_window(latest="rank()", sort=[alt.SortField("day", order="descending")], groupby=["team"])
                        .transform_filter("datum.latest == 1")
                        .transform_calculate(label="datum.team + '  ' + format(datum.share, '.1%')")
                        .mark_text(align="right", dx=-4, dy=-12, fontSize=13, fontWeight="bold")
                        .encode(text="label:N"),
                    base.mark_line(strokeWidth=14, strokeOpacity=0.001, interpolate="monotone").encode(
                        detail="stretch:N", tooltip=[alt.Tooltip("team:N", title=t("trend_team"))]).add_params(pick),
                ).properties(width="container", height=340, padding={"left": 6, "right": 24, "top": 8, "bottom": 4})
                return chart
            st_components.html(trend_chart_html(build_chart(team_line_colors(teams, dark=False)),
                                                build_chart(team_line_colors(teams, dark=True))), height=440)

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