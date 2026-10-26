# ⚽ Football League Simulator

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Daily%20Simulations-orange)
![License](https://img.shields.io/badge/License-MIT-green)

A **full Monte Carlo simulation pipeline** for nine football leagues in Europe and Brazil. It predicts how each league table will finish by simulating the rest of the season 10,000 times, using past results, team strengths and betting odds.

---

# 🌐 Live App

Try the interactive simulator:

https://football-league-simulator.streamlit.app/

See [CHANGELOG.md](CHANGELOG.md) for what's changed and when.

📝 For in-depth articles on the method and other football analytics projects, see my [Medium](https://medium.com/@vickyfrissdekereki).

---

# 🏆 Supported Leagues

| League | Country |
|---|---|
| Premier League | England |
| Championship | England |
| Serie A | Italy |
| La Liga | Spain |
| Bundesliga | Germany |
| Ligue 1 | France |
| Eredivisie | Netherlands |
| Primeira Liga | Portugal |
| Série A | Brazil |

---

# 🚀 Features

### In the app
- The probability of every team finishing in every league position, with colour gradients
- League-table zones: Champions League, a possible 5th Champions League place, promotion, play-offs and relegation
- Headline cards for the title race, the top-four race and the relegation battle (promotion and play-off races for the Championship, the Libertadores race for Brazil)
- Hover a team name for its last five results, or any percentage for a plain-English explanation
- Matchday progress under each league name and a "last updated" badge in the visitor's own time zone
- Four languages (English, Spanish, French, Portuguese), opening in the browser's language
- Shareable links (`?league=laliga_spain&lang=es`) and a CSV download of each table

### Behind it
- **Data collection:** current standings scraped from [ESPN](https://www.espn.com/soccer/standings), results and fixtures from the [football-data.org API](https://www.football-data.org/), and betting odds from [The Odds API](https://the-odds-api.com/)
- **Team strengths:** attack and defence ratings from goals scored and conceded, with recent games counting more. Early in the season they're pulled towards the league average (or a typical promoted or relegated side), then blended 25% with what the last six weeks of betting odds imply
- **Match probabilities:** a **Poisson model** of goals, with each league's home advantage. Matches the bookmakers have already priced use their odds directly, with the margin removed
- **Monte Carlo simulation:** 10,000 simulated seasons per league, aggregated into the probability of each final position
- **Daily updates:** GitHub Actions refreshes the data and simulations twice a day (03:30 and 13:00 UTC). Each run checks the results against the league table and fetches again if any games are missing

---

# 🗂️ Project Structure

| File | What it does |
|---|---|
| `1_dataset_creation.py` | Scrapes standings and fetches results, fixtures and odds |
| `2_dataset_processing.py` | Cleans team names, sets season start dates and builds each league's remaining fixtures |
| `3_probabilities.py` | Team strengths, home advantage and match outcome probabilities |
| `4_simulations.py` | Runs the Monte Carlo simulations |
| `precompute_simulations.py` | Runs the whole pipeline and saves the results to `data/` |
| `app.py` | The Streamlit dashboard |
| `.github/workflows/daily_simulations.yml` | The scheduled GitHub Actions run |

---

# 🧰 Tech Stack

- **Python 3.11**
- **Pandas**, **NumPy**, **SciPy**
- **Playwright** (headless Chromium for scraping the standings)
- **Requests** (football-data.org and The Odds API)
- **Matplotlib** (table styling)
- **Streamlit** (interactive dashboard)
- **GitHub Actions** (scheduled data updates and simulations)

---

# 💻 Usage

### 1️⃣ Clone the repository

```bash
git clone https://github.com/vickyfriss/football-league-predictions.git
cd football-league-predictions
```

### 2️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Streamlit app

```bash
streamlit run app.py
```

The app reads the precomputed simulations in `data/`, so it needs no API keys.

### 4️⃣ Refresh the data and simulations (optional)

You need free API keys from [football-data.org](https://www.football-data.org/) and [The Odds API](https://the-odds-api.com/). Put them in an `API_KEY.env` file (git-ignored) or set them as environment variables:

```bash
FOOTBALL_DATA_API_KEY=your_key
ODDS_DATA_API_KEY=your_key
```

Then install the browser Playwright uses and run the pipeline:

```bash
playwright install chromium
python precompute_simulations.py
```

---

# ⚽ Motivation

Football leagues are inherently uncertain. This project explores how **probabilistic modelling and Monte Carlo simulation** can estimate the likelihood of different league outcomes.

---

# 👤 Author

**Victoria Friss de Kereki**, Football Data Analyst · [Medium](https://medium.com/@vickyfrissdekereki) · [LinkedIn](https://www.linkedin.com/in/victoria-friss-de-kereki/) · [GitHub](https://github.com/vickyfriss)

---

# 📄 License

This project is released under the **MIT License**.
