# 2_dataset_processing.py
import pandas as pd

# -------------------------------
# 1️⃣ Season start date and leagues
SEASON_START_DATE = pd.Timestamp("2025-08-01")

leagues = [
    "premierleague_england",
    "seriea_italy",
    "laliga_spain",
    "bundesliga_germany",
    "ligue1_france",
]

# -------------------------------
# 2️⃣ Team name mappings per league
mappings = {
    "premierleague_england": {
        "Aston Villa FC": "Aston Villa",
        "Leeds United FC": "Leeds United",
        "Newcastle United FC": "Newcastle United",
        "Crystal Palace FC": "Crystal Palace",
        "Chelsea FC": "Chelsea",
        "Arsenal FC": "Arsenal",
        "Everton FC": "Everton",
        "Burnley FC": "Burnley",
        "Brighton & Hove Albion FC": "Brighton & Hove Albion",
        "Sunderland AFC": "Sunderland",
        "West Ham United FC": "West Ham United",
        "Manchester City FC": "Manchester City",
        "Manchester United FC": "Manchester United",
        "Fulham FC": "Fulham",
        "Liverpool FC": "Liverpool",
        "Brentford FC": "Brentford",
        "Wolverhampton Wanderers FC": "Wolverhampton Wanderers",
        "Nottingham Forest FC": "Nottingham Forest",
        "Tottenham Hotspur FC": "Tottenham Hotspur",
        # Betting odds
        "Brighton and Hove Albion": "Brighton & Hove Albion",
        "Bournemouth": "AFC Bournemouth"
    },
    "seriea_italy": {
        "US Sassuolo Calcio": "Sassuolo",
        "Cagliari Calcio": "Cagliari",
        "Atalanta BC": "Atalanta",
        "SS Lazio": "Lazio",
        "Genoa CFC": "Genoa",
        "Udinese Calcio": "Udinese",
        "FC Internazionale Milano": "Internazionale",
        "Torino FC": "Torino",
        "AC Pisa 1909": "Pisa",
        "ACF Fiorentina": "Fiorentina",
        "AS Roma": "AS Roma",
        "Juventus FC": "Juventus",
        "Como 1907": "Como",
        "US Cremonese": "Cremonese",
        "Bologna FC 1909": "Bologna",
        "Parma Calcio 1913": "Parma",
        "Hellas Verona FC": "Hellas Verona",
        "SSC Napoli": "Napoli",
        "US Lecce": "Lecce",
        # Betting odds
        "Inter Milan": "Internazionale",
        "Como": "Como"
    },
    "laliga_spain": {
        "Club Atlético de Madrid": "Atlético Madrid",
        "Rayo Vallecano de Madrid": "Rayo Vallecano",
        "Valencia CF": "Valencia",
        "Deportivo Alavés": "Alavés",
        "CA Osasuna": "Osasuna",
        "RCD Espanyol de Barcelona": "Espanyol",
        "Getafe CF": "Getafe",
        "Real Sociedad de Fútbol": "Real Sociedad",
        "Levante UD": "Levante",
        "Real Betis Balompié": "Real Betis",
        "RCD Mallorca": "Mallorca",
        "Girona FC": "Girona",
        "Villarreal CF": "Villarreal",
        "FC Barcelona": "Barcelona",
        "Elche CF": "Elche",
        "Sevilla FC": "Sevilla",
        "Real Madrid CF": "Real Madrid",
        "RC Celta de Vigo": "Celta Vigo",
        # Betting odds
        "Oviedo": "Real Oviedo",
        "Athletic Bilbao": "Athletic Club"
    },
    "bundesliga_germany": {
        "1. FC Köln": "FC Cologne",
        "TSG 1899 Hoffenheim": "TSG Hoffenheim",
        "1. FSV Mainz 05": "Mainz",
        "SV Werder Bremen": "Werder Bremen",
        "Hamburger SV": "Hamburg SV",
        "Bayer 04 Leverkusen": "Bayer Leverkusen",
        "FC St. Pauli 1910": "St. Pauli",
        "FC Bayern München": "Bayern Munich",
        # Betting odds
        "1. FC Heidenheim": "1. FC Heidenheim 1846",
        "Union Berlin": "1. FC Union Berlin",
        "Borussia Monchengladbach": "Borussia Mönchengladbach",
        "FSV Mainz 05": "Mainz",
        "Bayer Leverkusen": "Bayer Leverkusen",
        "Augsburg": "FC Augsburg",
        "FC St. Pauli": "St. Pauli"
    },
    "ligue1_france": {
        "Racing Club de Lens": "Lens",
        "OGC Nice": "Nice",
        "FC Metz": "Metz",
        "Angers SCO": "Angers",
        "Stade Brestois 29": "Brest",
        "Olympique Lyonnais": "Lyon",
        "Paris Saint-Germain FC": "Paris Saint-Germain",
        "AS Monaco FC": "AS Monaco",
        "Lille OSC": "Lille",
        "Toulouse FC": "Toulouse",
        "FC Nantes": "Nantes",
        "RC Strasbourg Alsace": "Strasbourg",
        "FC Lorient": "Lorient",
        "Olympique de Marseille": "Marseille",
        "Stade Rennais FC 1901": "Stade Rennais",
        # Betting odds
        "RC Lens": "Lens",
        "Paris Saint Germain": "Paris Saint-Germain",
        "Auxerre": "AJ Auxerre",
        "Lyon": "Lyon",
        "Le Havre": "Le Havre AC",
        "Rennes": "Stade Rennais",
        "Metz": "Metz",
        "Nice": "Nice",
        "Lille": "Lille"
    }
}

# -------------------------------
# 3️⃣ Helpers
def normalize_columns(df, kind="fixtures"):
    """Ensure home/away columns exist and are standardized."""
    df = df.copy()
    if df.empty:
        df["homeTeam"] = pd.Series(dtype=str)
        df["awayTeam"] = pd.Series(dtype=str)
        return df

    # Rename columns if needed
    if {"home_team", "away_team"}.issubset(df.columns):
        df = df.rename(columns={"home_team": "homeTeam", "away_team": "awayTeam"})
    elif {"homeTeam", "awayTeam"}.issubset(df.columns):
        pass
    else:
        df["homeTeam"] = pd.NA
        df["awayTeam"] = pd.NA
    return df

def filter_current_season(past_matches):
    df = past_matches.copy()
    if "utcDate" in df.columns:
        df["utcDate"] = pd.to_datetime(df["utcDate"], utc=True).dt.tz_localize(None)
        return df[df["utcDate"] >= SEASON_START_DATE]
    return df

def season_fixtures(past_matches, future_matches):
    past_matches = normalize_columns(past_matches)
    future_matches = normalize_columns(future_matches)
    return pd.concat(
        [past_matches[["homeTeam","awayTeam"]],
         future_matches[["homeTeam","awayTeam"]]],
        ignore_index=True
    )

def find_missing_reverse_fixture(team, opponent, fixtures):
    team_home = ((fixtures.homeTeam == team) & (fixtures.awayTeam == opponent)).any()
    team_away = ((fixtures.homeTeam == opponent) & (fixtures.awayTeam == team)).any()
    if team_home and not team_away:
        return opponent, team
    if team_away and not team_home:
        return team, opponent
    return None

# -------------------------------
# 4️⃣ Main processing function (FIXED)
def process_datasets(globals_dict):
    missing_fixtures = []

    # 4a️⃣ Apply team name mappings (unchanged)
    datasets_templates = [
        "past_matches_{}_all",
        "future_matches_{}",
        "betting_odds_{}"
    ]

    for league, mapping in mappings.items():
        for ds_template in datasets_templates:
            ds_name = ds_template.format(league)
            df = globals_dict.get(ds_name)
            if df is not None:
                df = normalize_columns(df)
                df.replace(mapping, inplace=True)
                globals_dict[ds_name] = df

    # 4b️⃣ Add missing fixtures from betting odds (only actual missing future matches)
    for league in leagues:
        future_matches = globals_dict.get(f"future_matches_{league}")
        betting_odds = globals_dict.get(f"betting_odds_{league}")
        if future_matches is None or betting_odds is None:
            continue

        future_set = set(zip(future_matches["homeTeam"], future_matches["awayTeam"]))
        book_set = set(zip(
            normalize_columns(betting_odds)["homeTeam"],
            normalize_columns(betting_odds)["awayTeam"]
        ))
        missing_matches = book_set - future_set

        for home, away in missing_matches:
            future_matches.loc[len(future_matches)] = {
                "utcDate": pd.NaT,
                "homeTeam": home,
                "awayTeam": away
            }
        globals_dict[f"future_matches_{league}"] = future_matches

    # 4c️⃣ Detect reverse fixtures (FIXED)
    # Only look at future_matches for reverse fixtures
    for league in leagues:
        future_matches = globals_dict.get(f"future_matches_{league}")
        league_table = globals_dict.get(f"past_matches_{league}_all")
        if future_matches is None or league_table is None:
            continue

        fixtures = normalize_columns(future_matches)  # 🔹 only future matches

        total_teams = len(league_table)
        matches_per_team = (total_teams - 1) * 2  # standard round-robin

        # Count future matches only
        played_counts = fixtures.homeTeam.value_counts().add(
            fixtures.awayTeam.value_counts(), fill_value=0
        )

        missing_teams = {
            team: matches_per_team - played_counts.get(team, 0)
            for team in league_table.get("team", [])
            if matches_per_team - played_counts.get(team, 0) > 0
        }

        league_teams = set(league_table.get("team", []))
        for team in missing_teams:
            for opponent in league_teams - {team}:
                result = find_missing_reverse_fixture(team, opponent, fixtures)
                if result:
                    home, away = result
                    missing_fixtures.append({
                        "league": league,
                        "homeTeam": home,
                        "awayTeam": away
                    })

    # 4d️⃣ Append missing fixtures (unchanged)
    missing_df = pd.DataFrame(missing_fixtures).drop_duplicates().sort_values(["league","homeTeam"])
    future_matches_backup = {}

    for league in missing_df["league"].unique():
        future_matches_backup[league] = globals_dict[f"future_matches_{league}"].copy()
        future_matches = globals_dict[f"future_matches_{league}"]
        league_missing = missing_df[missing_df["league"]==league]

        for _, row in league_missing.iterrows():
            future_matches.loc[len(future_matches)] = {
                "utcDate": pd.NaT,
                "homeTeam": row["homeTeam"],
                "awayTeam": row["awayTeam"]
            }
        globals_dict[f"future_matches_{league}"] = future_matches

    return missing_df, future_matches_backup