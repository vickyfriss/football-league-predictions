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
    "championship_england"  # ✅ Added Championship
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
    }
}

# -------------------------------
# Helpers
def normalize_columns(df):
    df = df.copy()

    if df.empty:
        df["homeTeam"] = pd.Series(dtype=str)
        df["awayTeam"] = pd.Series(dtype=str)
        return df

    rename_map = {}
    for old, new in [
        ("home_team", "homeTeam"), ("away_team", "awayTeam"),
        ("HomeTeam", "homeTeam"), ("AwayTeam", "awayTeam")
    ]:
        if old in df.columns:
            rename_map[old] = new

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def filter_current_season(df):
    df = df.copy()
    if "utcDate" in df.columns:
        df["utcDate"] = pd.to_datetime(df["utcDate"], utc=True).dt.tz_localize(None)
        df = df[df["utcDate"] >= SEASON_START_DATE]
    return df


def season_fixtures(past_matches, future_matches):
    past_matches = normalize_columns(past_matches)
    future_matches = normalize_columns(future_matches)
    return pd.concat(
        [past_matches[["homeTeam", "awayTeam"]],
         future_matches[["homeTeam", "awayTeam"]]],
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
# VERIFICATION (upgraded)
def verify_league_schedule(globals_dict):
    print("\n==============================")
    print("🔎 VERIFYING LEAGUE SCHEDULES")
    print("==============================")

    for league in leagues:

        missing = []

        future_matches = globals_dict.get(f"future_matches_{league}")
        if future_matches is None:
            missing.append("future_matches")

        past_matches_all = globals_dict.get(f"past_matches_{league}_all")
        if past_matches_all is None:
            missing.append("past_matches_all")

        league_table = globals_dict.get(league)
        if league_table is None:
            missing.append("league table")

        if missing:
            print(f"{league}: ⚠️ Missing dataset(s) {missing}, skipping verification")
            continue

        past_matches = filter_current_season(past_matches_all)
        total_matches = len(past_matches) + len(future_matches)

        # Total teams in the league
        if "team" not in league_table.columns:
            print(f"{league}: ⚠️ 'team' column missing in league table, skipping")
            continue

        teams = set(league_table["team"])
        expected_matches_per_team = (len(teams) - 1) * 2
        print(f"\n{league}: Total teams = {len(teams)} | Expected matches per team = {expected_matches_per_team}")

        # Count home + away matches per team
        played_counts = past_matches["homeTeam"].value_counts().add(
            past_matches["awayTeam"].value_counts(), fill_value=0
        ).add(
            future_matches["homeTeam"].value_counts(), fill_value=0
        ).add(
            future_matches["awayTeam"].value_counts(), fill_value=0
        )

        missing_teams = {team: expected_matches_per_team - played_counts.get(team, 0)
                         for team in teams if expected_matches_per_team - played_counts.get(team, 0) > 0}

        print(f"Past matches (this season): {len(past_matches)} | Future matches: {len(future_matches)} | Total fixtures: {len(past_matches)+len(future_matches)}")

        if not missing_teams:
            print("✅ All teams have complete fixtures")
        else:
            print("⚠️ Teams missing fixtures:")
            for team, missing_count in missing_teams.items():
                print(f"  {team}: {missing_count} matches missing")


# -------------------------------
# MAIN PROCESS
def process_datasets(globals_dict):
    print("\n==============================")
    print("⚙️ PROCESSING DATASETS")
    print("==============================")

    missing_fixtures = []

    # Apply mappings
    for league, mapping in mappings.items():
        print(f"\n🔧 Applying team mapping: {league}")
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
    # Add fixtures from betting odds
    print("\n📊 Checking betting odds for missing fixtures")
    for league in leagues:
        future_matches = globals_dict.get(f"future_matches_{league}")
        betting_odds = globals_dict.get(f"betting_odds_{league}")
        if future_matches is None or betting_odds is None:
            continue

        future_set = set(zip(future_matches["homeTeam"], future_matches["awayTeam"]))
        odds_df = normalize_columns(betting_odds)
        book_set = set(zip(odds_df["homeTeam"], odds_df["awayTeam"]))
        missing = book_set - future_set
        print(f"{league}: {len(missing)} fixtures missing from API")

        for home, away in missing:
            future_matches.loc[len(future_matches)] = {
                "utcDate": pd.NaT,
                "homeTeam": home,
                "awayTeam": away
            }
        globals_dict[f"future_matches_{league}"] = future_matches

    # -------------------------------
    # Detect reverse fixtures
    print("\n🔎 Detecting missing reverse fixtures")
    for league in leagues:
        future_matches = globals_dict.get(f"future_matches_{league}")
        past_matches_all = globals_dict.get(f"past_matches_{league}_all")
        league_table = globals_dict.get(league)
        if future_matches is None or past_matches_all is None or league_table is None:
            continue

        past_matches = filter_current_season(past_matches_all)
        fixtures = season_fixtures(past_matches, future_matches)
        league_teams = set(league_table["team"])

        for team in league_teams:
            for opponent in league_teams - {team}:
                result = find_missing_reverse_fixture(team, opponent, fixtures)
                if result:
                    home, away = result
                    missing_fixtures.append({
                        "league": league,
                        "homeTeam": home,
                        "awayTeam": away
                    })

    # -------------------------------
    # Append missing fixtures
    missing_df = pd.DataFrame(missing_fixtures)
    future_matches_backup = {}

    if not missing_df.empty:
        missing_df = (missing_df
                      .drop_duplicates()
                      .sort_values(["league", "homeTeam"])
                      .reset_index(drop=True))
        print("\n➕ Adding reverse fixtures")
        for league in missing_df["league"].unique():
            future_matches_backup[league] = globals_dict[f"future_matches_{league}"].copy()
            future_matches = globals_dict[f"future_matches_{league}"]
            league_missing = missing_df[missing_df["league"]==league]
            print(f"{league}: adding {len(league_missing)} fixtures")
            for _, row in league_missing.iterrows():
                future_matches.loc[len(future_matches)] = {
                    "utcDate": pd.NaT,
                    "homeTeam": row["homeTeam"],
                    "awayTeam": row["awayTeam"]
                }
            globals_dict[f"future_matches_{league}"] = future_matches
    else:
        print("\n✅ No reverse fixtures missing")

    # -------------------------------
    verify_league_schedule(globals_dict)
    return missing_df, future_matches_backup