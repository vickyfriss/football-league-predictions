import pandas as pd

# ===============================
# 1️⃣ Season start dates
# ===============================
SEASON_START_DATES = {
    "premierleague_england": pd.Timestamp("2025-08-01", tz="UTC"),
    "championship_england": pd.Timestamp("2025-08-01", tz="UTC"),
    "seriea_italy": pd.Timestamp("2025-08-01", tz="UTC"),
    "laliga_spain": pd.Timestamp("2025-08-01", tz="UTC"),
    "bundesliga_germany": pd.Timestamp("2025-08-01", tz="UTC"),
    "ligue1_france": pd.Timestamp("2025-08-01", tz="UTC"),
    "eredivisie_netherlands": pd.Timestamp("2025-08-01", tz="UTC"),
    "seriea_brazil": pd.Timestamp("2026-01-01", tz="UTC")
}

leagues = [
    "premierleague_england",
    "seriea_italy",
    "laliga_spain",
    "bundesliga_germany",
    "ligue1_france",
    "championship_england",
    "eredivisie_netherlands",
    "seriea_brazil"
]

# ===============================
# 2️⃣ FULL TEAM MAPPINGS
# ===============================
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
        "1. FC Heidenheim": "1. FC Heidenheim 1846",
        "Union Berlin": "1. FC Union Berlin",
        "Borussia Monchengladbach": "Borussia Mönchengladbach",
        "FSV Mainz 05": "Mainz",
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
        "RC Lens": "Lens",
        "Paris Saint Germain": "Paris Saint-Germain",
        "Auxerre": "AJ Auxerre",
        "Le Havre": "Le Havre AC",
        "Rennes": "Stade Rennais"
    },
    "championship_england": {  
        "Sheffield United FC": "Sheffield United",
        "West Bromwich Albion FC": "West Bromwich Albion",
        "Burnley FC": "Burnley",
        "Blackpool FC": "Blackpool",
        "Bristol City FC": "Bristol City",
        "Coventry City FC": "Coventry City",
        "Hull City AFC": "Hull City",
        "Luton Town FC": "Luton Town",
        "Middlesbrough FC": "Middlesbrough",
        "Millwall FC": "Millwall",
        "Nottingham Forest FC": "Nottingham Forest",
        "Queens Park Rangers FC": "Queens Park Rangers",
        "Reading FC": "Reading",
        "Rotherham United FC": "Rotherham United",
        "Stoke City FC": "Stoke City",
        "Sunderland AFC": "Sunderland",
        "Swansea City AFC": "Swansea City",
        "Watford FC": "Watford",
        "Wigan Athletic FC": "Wigan Athletic",
        "Derby County FC": "Derby County",
        "Ipswich Town FC": "Ipswich Town",
        "Southampton FC": "Southampton",
        "Wrexham AFC": "Wrexham",
        "Leicester City FC": "Leicester City",
        "Portsmouth FC": "Portsmouth",
        "Oxford United FC": "Oxford United",
        "Charlton Athletic FC": "Charlton Athletic",
        "Wrexham AFC": "Wrexham",
        "Sheffield Wednesday FC": "Sheffield Wednesday",
        "Preston North End FC": "Preston North End",
        "Blackburn Rovers FC": "Blackburn Rovers",
        "Norwich City FC": "Norwich City",
        "Birmingham City FC": "Birmingham City"
    },

    "eredivisie_netherlands": {
        "PSV": "PSV Eindhoven",
        "Feyenoord": "Feyenoord Rotterdam",
        "NEC": "NEC Nijmegen",
        "FC Twente Enschede": "FC Twente",
        "FC Twente '65": "FC Twente",
        "AFC Ajax": "Ajax Amsterdam",
        "Ajax": "Ajax Amsterdam",
        "AZ": "AZ Alkmaar",
        "SC Heerenveen": "Heerenveen",
        "Groningen": "FC Groningen",
        "FC Zwolle": "PEC Zwolle",
        "SBV Excelsior": "Excelsior",
        "Telstar 1963": "Telstar",
        "SC Telstar": "Telstar"
    },

#    "primera_division_argentina": {},

    "seriea_brazil": {
        "CR Flamengo": "Flamengo",
        "SE Palmeiras": "Palmeiras",
        "Cruzeiro EC": "Cruzeiro",
        "Mirassol FC": "Mirassol",
        "Fluminense FC": "Fluminense",
        "Botafogo FR": "Botafogo",
        "EC Bahia": "Bahia",
        "São Paulo FC": "São Paulo",
        "Sao Paulo": "São Paulo",
        "Grêmio FBPA": "Grêmio",
        "RB Bragantino": "Red Bull Bragantino",
        "Bragantino-SP": "Red Bull Bragantino",
        "CA Mineiro": "Atlético-MG",
        "Atletico Mineiro": "Atlético-MG",
        "Santos FC": "Santos",
        "SC Corinthians Paulista": "Corinthians",
        "CR Vasco da Gama": "Vasco da Gama",
        "EC Vitória": "Vitória",
        "Vitoria": "Vitória",
        "SC Internacional": "Internacional",
        "Coritiba FBC": "Coritiba",
        "CA Paranaense": "Athletico Paranaense",
        "Atletico Paranaense": "Athletico Paranaense",
        "Chapecoense AF": "Chapecoense",
        "Clube do Remo": "Remo"
    }
}

# ===============================
# HELPERS
# ===============================
def normalize_columns(df):
    df = df.copy()

    if df.empty:
        df["homeTeam"] = pd.Series(dtype=str)
        df["awayTeam"] = pd.Series(dtype=str)
        return df

    rename_map = {}
    for old, new in [
        ("home_team", "homeTeam"),
        ("away_team", "awayTeam"),
        ("HomeTeam", "homeTeam"),
        ("AwayTeam", "awayTeam")
    ]:
        if old in df.columns:
            rename_map[old] = new

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def filter_current_season(df, league):
    df = df.copy()
    df["utcDate"] = pd.to_datetime(df["utcDate"], errors="coerce")
    df = df.dropna(subset=["utcDate"])
    df = df[df["utcDate"] >= SEASON_START_DATES[league]]
    return df


# ===============================
# 🆕 LEAGUE ACTIVE CHECK (FIX)
# ===============================
def is_league_active(league_table):
    """
    League is active if not all teams have completed all expected matches.
    Expected matches = (number of teams - 1) * 2
    """

    if league_table is None or league_table.empty:
        return False

    if "gp" not in league_table.columns or "team" not in league_table.columns:
        return False

    gp = pd.to_numeric(league_table["gp"], errors="coerce").fillna(0)

    num_teams = league_table["team"].nunique()

    if num_teams < 2:
        return False

    expected_gp = (num_teams - 1) * 2

    # league finished only if ALL teams reached expected GP
    return not (gp == expected_gp).all()


# ===============================
def season_fixtures(past_matches, future_matches):
    past_matches = normalize_columns(past_matches)
    future_matches = normalize_columns(future_matches)

    return pd.concat(
        [
            past_matches[["homeTeam", "awayTeam"]],
            future_matches[["homeTeam", "awayTeam"]]
        ],
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


# ===============================
# MAIN PROCESS (SAFE)
# ===============================
def process_datasets(globals_dict):

    print("\n==============================")
    print("⚙️ PROCESSING DATASETS")
    print("==============================")

    missing_fixtures = []

    # -------------------------------
    # Apply mappings
    for league, mapping in mappings.items():
        for dataset in [
            f"past_matches_{league}_all",
            f"future_matches_{league}",
            f"betting_odds_{league}"
        ]:
            df = globals_dict.get(dataset)
            if df is None:
                continue
            df = normalize_columns(df)
            df.replace(mapping, inplace=True)
            globals_dict[dataset] = df

    # -------------------------------
    # ACTIVE LEAGUE FILTER
    active_leagues = []

    print("\n📊 Checking league status...")
    for league in leagues:
        if is_league_active(globals_dict.get(league)):
            active_leagues.append(league)
        else:
            print(f"{league}: 🏁 finished → skipping generation")

    print(f"\nActive leagues: {active_leagues}")

    # -------------------------------
    # Betting odds fill (only active leagues)
    print("\n📊 Checking betting odds")

    for league in active_leagues:

        future_matches = globals_dict.get(f"future_matches_{league}")
        betting_odds = globals_dict.get(f"betting_odds_{league}")

        if future_matches is None or betting_odds is None:
            continue

        future_set = set(zip(future_matches["homeTeam"], future_matches["awayTeam"]))
        odds_df = normalize_columns(betting_odds)
        book_set = set(zip(odds_df["homeTeam"], odds_df["awayTeam"]))

        missing = book_set - future_set

        for home, away in missing:
            future_matches.loc[len(future_matches)] = {
                "utcDate": pd.NaT,
                "homeTeam": home,
                "awayTeam": away
            }

        globals_dict[f"future_matches_{league}"] = future_matches

    # -------------------------------
    # Reverse fixtures (only active leagues)
    print("\n🔎 Detecting reverse fixtures")

    for league in active_leagues:

        future_matches = globals_dict.get(f"future_matches_{league}")
        
        league_table = globals_dict.get(league)
        past_matches_all = globals_dict.get(f"past_matches_{league}_all")

        if league_table is None or past_matches_all is None:
            continue

        expected_gp = league_table.set_index("team")["gp"]

        if future_matches is None or past_matches_all is None or league_table is None:
            continue

        fixtures = season_fixtures(past_matches_all, future_matches)

        teams = set(league_table["team"])

        past_set = set(zip(past_matches_all["homeTeam"], past_matches_all["awayTeam"]))
        future_set = set(zip(future_matches["homeTeam"], future_matches["awayTeam"]))

        for team in teams:
            for opponent in teams - {team}:

                result = find_missing_reverse_fixture(team, opponent, fixtures)

                if result:
                    home, away = result

                    # already exists somewhere → skip
                    if (home, away) in future_set or (home, away) in past_set:
                        continue

                    home_gp = expected_gp.get(home, 0)
                    away_gp = expected_gp.get(away, 0)

                    # count how many matches each team has already played in past data
                    home_played = past_matches_all[
                        (past_matches_all["homeTeam"] == home) |
                        (past_matches_all["awayTeam"] == home)
                    ].shape[0]

                    away_played = past_matches_all[
                        (past_matches_all["homeTeam"] == away) |
                        (past_matches_all["awayTeam"] == away)
                    ].shape[0]

                    missing_fixtures.append({
                        "league": league,
                        "homeTeam": home,
                        "awayTeam": away,
                        "home_gp_expected": home_gp,
                        "away_gp_expected": away_gp,
                        "home_gp_actual": home_played,
                        "away_gp_actual": away_played,
                        "missing_in": "past" if home_played < home_gp or away_played < away_gp else "future"
                    })

    # -------------------------------
    missing_df = pd.DataFrame(missing_fixtures)

    if not missing_df.empty:

        missing_df = missing_df.drop_duplicates().reset_index(drop=True)

        print("\n➕ Adding reverse fixtures")

        for league in missing_df["league"].unique():

            future_matches = globals_dict[f"future_matches_{league}"]
            league_missing = missing_df[missing_df["league"] == league]

            for _, row in league_missing.iterrows():

                # If GP mismatch is large → likely data gap (not schedule)
                missing_in = row["missing_in"]

                if missing_in == "past":
                    target_df = past_matches_all
                else:
                    target_df = future_matches

                target_df.loc[len(target_df)] = {
                    "utcDate": pd.NaT,
                    "homeTeam": row["homeTeam"],
                    "awayTeam": row["awayTeam"]
                }

            globals_dict[f"future_matches_{league}"] = future_matches

    else:
        print("\n✅ No reverse fixtures missing")

    return missing_df, {}