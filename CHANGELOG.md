# Changelog

What changed in the [Football League Simulator](https://football-league-simulator.streamlit.app/) and when, newest first. Only changes you'd notice as a visitor, or that change how the predictions are made — not every commit.

**New** = new feature · **Improved** = better at something it already did · **Model** = how the probabilities are calculated · **Fixed** = bug fix

---

## 23 October 2026 — Headline cards, table zones and a big usability pass

- **New:** Headline cards above the table: *Title race*, *Champions League race* (the teams either side of the top-4 cut-off — the real battle, not the obvious top teams) and *Relegation battle*. The Championship gets *Automatic promotion* and *Play-off race* cards, Brazil a *Libertadores race*. Click any card to expand it into a longer ranking, with the cut-off line marked.
- **New:** League-table zones: a coloured stripe on the position column for Champions League, possible 5th Champions League place (Premier League, La Liga, Serie A, Bundesliga), promotion, play-offs and relegation, with a legend.
- **New:** Hover a team name to see its last 5 results (date, W/D/L, score, opponent, home/away).
- **New:** Hover any percentage for a plain-English explanation, e.g. *"Chelsea: 21.37% chance of finishing 4th"*.
- **New:** "Matchday 9 of 38 · 29 to play" under each league name, so it's clear how settled the predictions are.
- **New:** Shareable links — the league and language live in the URL (`?league=laliga_spain&lang=es`), and the browser tab names the league.
- **New:** The site opens in the visitor's own language (Spanish, French or Portuguese) when their browser is set to one.
- **Improved:** Redesigned "last updated" badge: *"Updated 5 hours ago"* with the exact time in the visitor's own time zone, and a status dot that turns amber if the daily update is late.
- **Improved:** "How This Simulation Works" uses the full page width in an even 4 + 4 grid; phone layout polished.
- **Fixed:** League buttons broken by a Streamlit update (labels squashed to "Premier League ..."); Streamlit is now pinned so updates can't silently break the layout again.

## 20 October 2026

- **Model:** Team strengths now include what the betting market thinks. The model works backwards from the last six weeks of odds (recent prices count more) to estimate each team's attack and defence, and blends it in at 25% market / 75% goals. News the market picks up — transfers, new managers, injuries — now affects every remaining fixture, not just the next round. In a backtest this made forecasts slightly but measurably more accurate.
- **Improved:** Rewrote the "How This Simulation Works" steps in all four languages to match how the model now works.

## 19 October 2026

- **New:** Goal difference (GD) column in the table, in the standard order: position, team, played, goal difference, points.

## 12–14 October 2026

- **Model:** Newly promoted and relegated teams start from updated baselines, measured from how such teams actually did last season.
- **Fixed:** A league no longer disappears from the app when its standings fail to download (the Premier League vanished on 14 Oct); the app keeps the last good data instead.
- **Fixed:** On days the standings changed, some remaining matches were treated as already played, producing false 100% predictions.

## 9–10 September 2026 — Four languages

- **New:** Language switcher: English, Spanish, French and Brazilian Portuguese, including dates and table headers.
- **Improved:** New full-width green hero banner ("9 Leagues · Updated Daily"), a step-card "How This Simulation Works" section with a new *Home Advantage* step, and a reworked mobile layout.

## 2 September 2026

- **Improved:** Simulation engine rewritten to run all 10,000 seasons at once — about 90× faster, same results.
- **Model:** Tuned how quickly the model trusts this season's results, with promoted and relegated teams leaning more on their starting baseline than established teams; by the halfway point every team is judged on this season alone.
- **Fixed:** When the fixtures feed came back incomplete for a team, its remaining fixtures are now restored from the previous day (this had caused false 100% positions for four Premier League teams on 30–31 Aug).

## 19–21 August 2026

- **New:** Portugal's Primeira Liga — nine leagues in total.
- **Model:** Newly promoted teams start below average and teams relegated into the Championship above average, based on how past promoted/relegated teams actually performed; the effect fades as the season goes on.
- **Improved:** On desktop, position, team, games and points stay frozen while you scroll sideways through the percentages.

## 9–11 August 2026 — New season and a redesign

- **New:** Switched to the 2026/27 season, with promoted and relegated clubs in every league (Brazil stays on its calendar-year season).
- **Improved:** Visual redesign: green colour scheme, the Inter font, restyled cards and buttons, and dark mode that follows the device setting.
- **New:** League buttons replace the dropdown menu.
- **Model:** Team strength now uses the current and previous season, so one or two early results no longer swing a team's chances (PSV had shown near-zero title odds after a single draw). Early-season caution is set per team, and home advantage and average goals weight recent matches more.
- **Fixed:** The daily update works again after ESPN started blocking automated requests from cloud servers.
- **Fixed:** Matches missing from the fixtures feed are added back, so every team plays its full schedule in the simulation.

## 2 May 2026

- **New:** Leagues whose season has finished show the final table instead of simulating it.

## 17–22 April 2026

- **New:** The Dutch Eredivisie.
- **New:** "What-if" scenario analysis, first used to simulate the Premier League title race under different Manchester City vs Arsenal results.
- **Improved:** The daily update re-runs whenever any team has played, not only when league positions change.
- **Fixed:** Standings downloads are more robust against being blocked.

## 1–4 April 2026

- **Model:** Early in a season, team ratings are pulled towards the league average so a few results don't make predictions overconfident; the effect fades to nothing by the halfway point.
- **Fixed:** Each league uses its own season start date, so Brazil's calendar-year season counts only this season's matches.
- **Improved:** The daily update is more reliable: it retries failed data sources, can't overlap with itself, and never publishes results built from incomplete data.

## 28–31 March 2026 — Beyond the top five

- **New:** Brazil's Série A — the first league outside Europe.
- **New:** The EFL Championship (England's second tier).
- **New:** README and MIT open-source licence.

## 7–10 March 2026 — Launch

- **New:** First version: the Premier League, Serie A, La Liga, Bundesliga and Ligue 1, showing each team's chance of finishing in every position.
- **Model:** Each remaining match uses bookmakers' odds (margin removed) where available, otherwise a goals model from each team's attack and defence with home advantage; the rest of the season is simulated 10,000 times.
- **Data:** Standings from ESPN, fixtures and results from Football-Data.org, odds from The Odds API.
- **New:** Simulations re-run automatically every day.
- **New:** "How This Simulation Works" section, CSV download, About Me section, and a mobile-friendly table.
