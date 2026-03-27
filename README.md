# ⚽ Football League Monte Carlo Simulation

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Daily%20Simulations-orange)
![License](https://img.shields.io/badge/License-MIT-green)
[![Open Simulator](https://img.shields.io/badge/Open%20Simulator-Streamlit-green)](https://football-league-simulator.streamlit.app/)

This project provides a **full Monte Carlo simulation pipeline** for European football leagues. It predicts league standings by simulating the remainder of the season using historical match data, team strengths, and betting odds.

---

# 🌐 Live App

Try the interactive simulator:

https://football-league-simulator.streamlit.app/

The dashboard allows you to explore predicted league outcomes and probability distributions for each team.

---

# 🚀 Features

### Data Collection & Processing
Automatically scrapes and organises:

- past match results  
- upcoming fixtures  
- betting odds  

### Probabilistic Modelling
Computes match outcome probabilities using a **weighted Poisson model** for goals scored.

### Monte Carlo Simulation
Runs thousands of simulations per league to estimate the **distribution of final league positions**.

### Interactive Visualisation
Styled tables show the probability of each team finishing in every league position using **intuitive colour gradients**.

### Streamlit Dashboard
Run the simulation interactively:

- choose a league  
- visualise outcome probabilities  

---

# 🏆 Supported Leagues

- English Premier League  
- Serie A (Italy)  
- La Liga (Spain)  
- Bundesliga (Germany)  
- Ligue 1 (France)

---

# 🧰 Tech Stack

- **Python 3**
- **Pandas**
- **NumPy**
- **SciPy**
- **Matplotlib** (visual styling)
- **Streamlit** (interactive dashboard)
- **GitHub Actions** (daily automated simulations)

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

---

# ⚽ Motivation

Football leagues are inherently uncertain. This project explores how **probabilistic modelling and Monte Carlo simulation** can be used to estimate the likelihood of different league outcomes.

---

# 📄 License

This project is released under the **MIT License**.
