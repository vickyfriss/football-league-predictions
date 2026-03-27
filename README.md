# ⚽ Football League Monte Carlo Simulation

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Daily%20Simulations-orange)
![License](https://img.shields.io/badge/License-MIT-green)

This project provides a **full Monte Carlo simulation pipeline** for European football leagues. It predicts league standings by simulating the remainder of the season using historical match data, team strengths, and betting odds.

---

# 🌐 Live App

Try the interactive simulator:

https://football-league-simulator.streamlit.app/

The dashboard allows you to explore predicted league outcomes and probability distributions for each team.

---

## Features
- **Data Collection & Processing:** Automatically scrapes and organizes past match results, upcoming fixtures, and betting odds.  
- **Probabilistic Modeling:** Computes match outcome probabilities using a weighted Poisson model for goals scored.  
- **Monte Carlo Simulation:** Runs thousands of simulations per league to estimate the distribution of final positions for each team.  
- **Interactive Visualization:** Styled tables show the probability of each team finishing in every league position, with intuitive color gradients.  
- **Streamlit Dashboard:** Run the pipeline interactively, choose the league, adjust the number of simulations, and visualize results.  

## Supported Leagues
- English Premier League  
- Serie A (Italy)  
- La Liga (Spain)  
- Bundesliga (Germany)  
- Ligue 1 (France)  

## Tech Stack
- Python 3  
- Pandas, NumPy, SciPy  
- Matplotlib for color styling  
- Streamlit for interactive dashboard  

## Usage
1. Clone the repository.  
2. Install dependencies from `requirements.txt`.  
3. Run the Streamlit app:  
```bash
streamlit run app.py  # ⚽ Football League Monte Carlo Simulation
```
