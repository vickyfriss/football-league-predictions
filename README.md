# ⚽ Football League Monte Carlo Simulation

This project provides a **full Monte Carlo simulation pipeline** for European football leagues. It predicts league standings by simulating the remainder of the season using historical match data, team strengths, and betting odds.  

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

This project provides a **full Monte Carlo simulation pipeline** for European football leagues. It predicts league standings by simulating the remainder of the season using historical match data, team strengths, and betting odds.  

## Features
- **Data Collection & Processing:** Automatically scrapes and organizes past match results, upcoming fixtures, and betting odds.  
- **Probabilistic Modeling:** Computes match outcome probabilities using a weighted Poisson model for goals scored.  
- **Monte Carlo Simulation:** Runs thousands of simulations per league to estimate the distribution of final positions for each team.  
- **Interactive Visualization:** Styled tables show the probability of each team finishing in every league position, with intuitive color gradients.  
- **Streamlit Dashboard:** Run the pipeline interactively, choose the league, adjust the number of simulations, and visualize results.  

## Supported Leagues
- Premier League (England)  
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
streamlit run app.py
```
4. Select a league and number of simulations in the sidebar.

## Outcome

This tool estimates team position probabilities and provides insights into league dynamics using statistical simulation—perfect for analysts, fans, or betting enthusiasts.
