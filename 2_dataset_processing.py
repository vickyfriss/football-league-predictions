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


def is_league_active(league_table):
    if league_table is None or league_table.empty:
        return False

    if "gp" not in league_table.columns or "team" not in league_table.columns:
        return False

    gp = pd.to_numeric(league_table["gp"], errors="coerce").fillna(0)
    num_teams = league_table["team"].nunique()

    if num_teams < 2:
        return False

    expected_gp = (num_teams - 1) * 2
    return not (gp == expected_gp).all()


# ===============================
# REVERSE FIXTURE DETECTION (FIXED)
# ===============================
def detect_reverse_fixtures(past_set, future_set, teams):

    missing = []

    for team in teams:
        for opponent in teams:
            if team == opponent:
                continue

            a = (team, opponent)
            b = (opponent, team)

            a_exists = a in past_set or a in future_set
            b_exists = b in past_set or b in future_set

            if a_exists and not b_exists:
                missing.append(b)
            elif b_exists and not a_exists:
                missing.append(a)

    return list(set(missing))


# ===============================
# MAIN PIPELINE
# ===============================
def process_datasets(globals_dict):

    print("\n==============================")
    print("⚙️ PROCESSING DATASETS")
    print("==============================")

    missing_fixtures = {}

    # =========================================================
    # 1️⃣ APPLY MAPPINGS
    # =========================================================
    print("\n1️⃣ Applying mappings...")

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

    # =========================================================
    # 2️⃣ ACTIVE LEAGUES
    # =========================================================
    print("\n2️⃣ Checking league status...")

    active_leagues = []
    for league in leagues:
        if is_league_active(globals_dict.get(league)):
            active_leagues.append(league)
            print(f"{league}: ⚽ active")
        else:
            print(f"{league}: 🏁 finished")

    print(f"\nActive leagues: {active_leagues}")


    # =========================================================
    # 3️⃣ BUILD COMPLETE FIXTURE SET (FIXED)
    # =========================================================
    # =========================================================
    # 3️⃣ BUILD COMPLETE FIXTURE UNIVERSE (FIXED LOGIC)
    # =========================================================
    print("\n3️⃣ Building full fixture universe (past + future + odds + reverse)...")

    for league in active_leagues:

        future = globals_dict.get(f"future_matches_{league}")
        past = globals_dict.get(f"past_matches_{league}_all")

        if future is None or past is None:
            continue

        future = normalize_columns(future)
        past = normalize_columns(past)

        # -------------------------------------------------
        # Build sets
        # -------------------------------------------------
        future_set = set(zip(future["homeTeam"], future["awayTeam"]))
        past_set = set(zip(past["homeTeam"], past["awayTeam"]))

        all_matches = future_set | past_set

        reverse_added = 0

        # -------------------------------------------------
        # FIXED LOGIC:
        # Only complete FUTURE schedule, never touch past
        # -------------------------------------------------
        for h, a in list(all_matches):

            reverse = (a, h)

            forward_in_past = (h, a) in past_set
            forward_in_future = (h, a) in future_set
            reverse_in_past = reverse in past_set
            reverse_in_future = reverse in future_set

            # =================================================
            # CORE RULE:
            # Add reverse ONLY if:
            # - forward exists somewhere
            # - reverse does NOT exist anywhere
            # - AND reverse is NOT already in past (critical fix)
            # =================================================

            forward_exists = forward_in_past or forward_in_future
            reverse_exists = reverse_in_past or reverse_in_future

            if not forward_exists:
                continue

            if reverse_exists:
                continue

            # 🚨 IMPORTANT: avoid polluting historical structure
            # only add if forward is NOT exclusively past-only orphan edge case
            if forward_in_past and not forward_in_future:
                # likely historical completion issue → skip
                continue

            future.loc[len(future)] = {
                "homeTeam": a,
                "awayTeam": h
            }

            reverse_added += 1

        globals_dict[f"future_matches_{league}"] = future

        print(f"{league}: ➕ added {reverse_added} reverse fixtures")
        
    # =========================================================
    # 4️⃣ FINAL VALIDATION (DOUBLE ROUND ROBIN RULE)
    # =========================================================
    print("\n4️⃣ Validating double round robin structure...")

        # ===============================
    # DEBUG FUTURE SIZE CHECK
    # ===============================
    print("\nDEBUG FUTURE SIZE CHECK")
    for league in active_leagues:
        future = globals_dict.get(f"future_matches_{league}")
        if future is None:
            print(league, "❌ None")
        else:
            print(league, len(future))

    results = []

    for league in active_leagues:

        future = globals_dict.get(f"future_matches_{league}")
        past = globals_dict.get(f"past_matches_{league}_all")
        table = globals_dict.get(league)

        if future is None or past is None or table is None:
            continue

        teams = sorted(set(table["team"]))
        n = len(teams)

        expected_total = (n - 1) * 2

        played = (
            past["homeTeam"].value_counts()
            + past["awayTeam"].value_counts()
        ).reindex(teams).fillna(0)

        scheduled = (
            future["homeTeam"].value_counts()
            + future["awayTeam"].value_counts()
        ).reindex(teams).fillna(0)

        for team in teams:

            total = int(played[team] + scheduled[team])
            diff = expected_total - total

            if diff != 0:
                results.append({
                    "league": league,
                    "team": team,
                    "played": int(played[team]),
                    "scheduled": int(scheduled[team]),
                    "expected_total": expected_total,
                    "diff": diff
                })

    missing_df = pd.DataFrame(results)

    # =========================================================
    # 5️⃣ FINAL OUTPUT ONLY (CLEAN)
    # =========================================================
    print("\n==============================")
    print("📊 FINAL REPORT")
    print("==============================")

    if missing_df.empty:
        print("✅ All leagues perfectly balanced (double round robin confirmed)")
    else:
        print(missing_df.sort_values(["league", "team"]).to_string(index=False))

    return missing_df, {}