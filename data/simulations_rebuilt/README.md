# Rebuilt runs

Every day of the 2026/27 season (and of Brazil's 2026 season) re-run with the
model as it was on 3 November 2026 (team strengths from the betting odds, in-play
prices removed from the odds history), using only what was known at the time of
that day's real run: the results played before it, a league table built from
those results (with points deductions taken from the current table), the
fixtures still to play, and that morning's bookmaker prices from
`data/odds_history`.

Why: the model changed several times during the season (the market blend and its
share, new starting points for promoted and relegated teams, two seasons of results), so
the original runs in `data/simulations` jump wherever the code changed. The
app's trend chart and the 7-day changes on the headline cards read these
rebuilt runs where they exist, so every line comes from one model. The
original runs are left untouched as the record of what was published.

Brazil also gets 17 July to 9 August, when games were played after the World
Cup break but the simulator wasn't running yet.

Checked against the real run of 3 November, 11:07 (Premier League and
Championship), rebuilt from the same data: 398 of the 400 Premier League cells
and every Championship cell within 1.5 percentage points; the other two are
Manchester City's split between 1st and 2nd (2.7 points), with the same
expected finishing position (2.02 against 2.03).

Made with `tools/rebuild_history.py`, one folder per run time, same layout as
`data/simulations`.
