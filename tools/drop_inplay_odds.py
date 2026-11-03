"""Remove in-play prices from data/odds_history: rows saved after that match had kicked off.
The odds API kept returning matches while they were being played, so until 3 Nov 2026 the
twice-daily run saved prices that follow the score, not the teams (1_dataset_creation.py now
skips them). Kick-off times come from the results files (data/past_*.csv).
usage: python tools/drop_inplay_odds.py [--dry-run]"""
import sys, os, importlib.util
import pandas as pd

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(repo)
spec = importlib.util.spec_from_file_location("dp", "2_dataset_processing.py")
dp = importlib.util.module_from_spec(spec); spec.loader.exec_module(dp)
dry = "--dry-run" in sys.argv

total = dropped = 0
for f in sorted(os.listdir("data/odds_history")):
    lg = f[:-4]
    hist = pd.read_csv(f"data/odds_history/{f}")
    snap = pd.to_datetime(hist["snap_time"], utc=True)
    m = dp.mappings.get(lg, {})
    played = pd.concat([pd.read_csv(f"data/{p}") for p in os.listdir("data") if p.startswith(f"past_{lg}_")])
    played = dp.normalize_columns(played).replace(m)
    kickoff = {}
    for r in played.itertuples():
        kickoff.setdefault((r.homeTeam, r.awayTeam), []).append(pd.Timestamp(r.utcDate).tz_convert("UTC"))
    home, away = hist["home_team"].replace(m), hist["away_team"].replace(m)
    # in play (or just finished): the same fixture kicked off before the snapshot, at most 3 days earlier
    inplay = [any(k <= s < k + pd.Timedelta(days=3) for k in kickoff.get((h, a), [])) for h, a, s in zip(home, away, snap)]
    inplay = pd.Series(inplay, index=hist.index)
    total += len(hist); dropped += inplay.sum()
    print(f"{lg}: {inplay.sum():,} of {len(hist):,} prices were in play")
    if not dry and inplay.any():
        # drop whole lines from the file as written, so every kept price stays byte-for-byte the same
        lines = open(f"data/odds_history/{f}").read().splitlines(keepends=True)
        keep = [lines[0]] + [l for l, bad in zip(lines[1:], inplay) if not bad]
        open(f"data/odds_history/{f}", "w").writelines(keep)
print(f"{'would drop' if dry else 'dropped'} {dropped:,} of {total:,} prices")
