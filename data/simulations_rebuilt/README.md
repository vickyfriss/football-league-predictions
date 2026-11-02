# Rebuilt runs

Every day of the 2026/27 season (and of Brazil's 2026 season) re-run with the
model as it was on 2 November 2026, using only what was known at the time of
that day's real run: the results played before it, a league table built from
those results (with points deductions taken from the current table), the
fixtures still to play, and that morning's bookmaker prices from
`data/odds_history`.

Why: the model changed several times during the season (the market blend, new
starting points for promoted and relegated teams, two seasons of results), so
the original runs in `data/simulations` jump wherever the code changed. The
app's trend chart and the 7-day changes on the headline cards read these
rebuilt runs where they exist, so every line comes from one model. The
original runs are left untouched as the record of what was published.

Brazil also gets 17 July to 9 August, when games were played after the World
Cup break but the simulator wasn't running yet.

Checked against two real runs on 2 November (Brazil and the Championship):
every finishing position within 1.5 percentage points, which is simulation
noise.

Made with `tools/rebuild_history.py`, one folder per run time, same layout as
`data/simulations`.
