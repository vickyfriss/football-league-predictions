"""Rebuild one league's runs with today's model code (precompute_simulations.py,
unchanged) and only the data known at each run time (see data/simulations_rebuilt/README.md).
Run it on a separate checkout: it executes the pipeline, which writes logs and annotations.
usage: python tools/rebuild_history.py REPO LEAGUE OUT_ROOT TIMES_FILE
       (TIMES_FILE: one 'YYYY-mm-dd HH:MM:SS' run time per line, in UTC)"""
import sys, os, io, contextlib
import pandas as pd
repo, LG, out_root, times_file = sys.argv[1:5]
os.chdir(repo); sys.path.insert(0, repo)
times = [pd.Timestamp(l.strip(), tz="UTC") for l in open(times_file) if l.strip()]

import importlib.util
spec = importlib.util.spec_from_file_location("dp_recon", "2_dataset_processing.py")
dp = importlib.util.module_from_spec(spec); spec.loader.exec_module(dp)
m = dp.mappings.get(LG, {})
# Every league's results, not just this one's: telling newly promoted and
# relegated teams apart needs the other division's previous season too
all_seasons = {}
for f in os.listdir("data"):
    if f.startswith("past_") and f.endswith(".csv"):
        lg, season = f[5:-4].rsplit("_", 1)
        all_seasons.setdefault(lg, {})[int(season)] = pd.read_csv(f"data/{f}")
seasons = all_seasons[LG]
cur = max(seasons)
results = seasons[cur].copy(); results["_d"] = pd.to_datetime(results["utcDate"], utc=True)
fixtures = pd.read_csv(f"data/fixtures_{LG}.csv")
odds_hist = pd.read_csv(f"data/odds_history/{LG}.csv")
odds_hist["snap_time"] = pd.to_datetime(odds_hist["snap_time"], utc=True)
espn = pd.read_csv(f"data/league_table/{LG}.csv")
# Points deductions, read off today's table (points the results alone don't explain)
deduction = dict(zip(espn["team"], espn["pts"] - 3 * espn["w"] - espn["d"]))

src = open("precompute_simulations.py").read()
src = src.replace("RUN_CREATION = True", "RUN_CREATION = False")
src = src.replace("standings, odds_book, fixtures, past_season_results = load_cached_odds_fixtures_and_history()",
                  "standings, odds_book, fixtures, past_season_results = RECON_INPUTS")
call = "odds_history_dict={lg: load_odds_history(lg) for lg in active_leagues},"
assert call in src
src = src.replace(call, call + " as_of=RECON_AS_OF.tz_localize(None),")
src = src.split("# 8️⃣ FIXED FORMATTER")[0]
code = compile(src, "precompute_simulations.py", "exec")

for T in times:
    played = results[(results["_d"] < T) & results["homeGoals"].notna()].drop(columns="_d")
    if played.empty:
        continue
    later = results[results["_d"] >= T][["utcDate", "homeTeam", "awayTeam"]].assign(status="SCHEDULED")
    fx = fixtures[pd.to_datetime(fixtures["utcDate"], utc=True) >= T][["utcDate", "status", "homeTeam", "awayTeam"]]
    future = pd.concat([later, fx]).drop_duplicates(subset=["homeTeam", "awayTeam"]).reset_index(drop=True)
    t = {}
    for row in played.itertuples():
        h, a, hg, ag = m.get(row.homeTeam, row.homeTeam), m.get(row.awayTeam, row.awayTeam), int(row.homeGoals), int(row.awayGoals)
        for team, gf, ga in [(h, hg, ag), (a, ag, hg)]:
            s = t.setdefault(team, dict(gp=0, w=0, d=0, l=0, gf=0, ga=0))
            s["gp"] += 1; s["gf"] += gf; s["ga"] += ga
            s["w" if gf > ga else "d" if gf == ga else "l"] += 1
    table = pd.DataFrame([dict(team=k, **v) for k, v in t.items()])
    table["gd"] = table["gf"] - table["ga"]
    table["pts"] = 3 * table["w"] + table["d"] + table["team"].map(deduction).fillna(0).astype(int)
    table = table.sort_values(["pts", "gd", "gf"], ascending=False).reset_index(drop=True)
    table.insert(0, "position", range(1, len(table) + 1))
    table = table[["position", "team", "gp", "w", "d", "l", "gf", "ga", "gd", "pts"]]
    # That day's bookmaker prices: the latest saved snapshot from the 18 hours before the run
    snaps = odds_hist[(odds_hist["snap_time"] <= T) & (odds_hist["snap_time"] > T - pd.Timedelta(hours=18))]
    odds = snaps[snaps["snap_time"] == snaps["snap_time"].max()].drop(columns="snap_time") if len(snaps) else \
        pd.DataFrame(columns=["home_team", "away_team", "p_home_book", "p_draw_book", "p_away_book"])
    past = {}
    for lg, by_season in all_seasons.items():
        past[lg] = {}
        for s, df in by_season.items():
            if lg == LG and s == cur:
                past[lg][s] = played
            else:
                d = pd.to_datetime(df["utcDate"], utc=True)
                past[lg][s] = df[d < T]
    g = {"__name__": "recon", "RECON_INPUTS": ({LG: table}, {LG: odds}, {LG: future}, past), "RECON_AS_OF": T}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(code, g)
    stamp = T.strftime("%Y%m%d_%H%M%S")
    if LG not in g["position_distribution_all"]:
        print(LG, stamp, "NOT SIMULATED", flush=True); continue
    os.makedirs(f"{out_root}/{stamp}", exist_ok=True)
    g["position_distribution_all"][LG].to_csv(f"{out_root}/{stamp}/{LG}_simulation.csv", index=False)
    print(LG, stamp, "ok", len(played), "played", len(odds), "prices", g.get("counting_problems") or "", flush=True)
