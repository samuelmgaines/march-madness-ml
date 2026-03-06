import json
import os
import pandas as pd
import logging
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
import time
from sklearn.ensemble import RandomForestClassifier
import random

LEAGUE = "men"
# LEAGUE = "women"
excluded_years = {2021}  # Exclude years to test later (don't train on them)

# Helper function to get srs score from string
def get_srs(srs_str):
    if srs_str:  # Ensure it's not empty
        try:
            return float(srs_str)  # Convert safely
        except ValueError:
            return 0
    return 0

# Extract team level stats
def load_team_stats(year, team_name):
    file_path = f"data/{LEAGUE}/yearly/{year}-{team_name}.json"
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return None
    
    with open(file_path, "r") as file:
        games = json.load(file)

    # Exclude March Madness games (optional, but could help avoid data leakage)
    regular_season_games = [g for g in games if g["game_type"] != "NCAA"]
    
    # Compute statistics
    total_games = len(regular_season_games)
    if total_games == 0:
        return None  # Avoid division by zero
    
    srs_values = []
    for g in regular_season_games:
        srs_str = g.get("srs", "").strip()  # Get value and strip spaces
        if srs_str:  # Ensure it's not empty
            try:
                srs_values.append(float(srs_str))  # Convert safely
            except ValueError:
                continue  # Skip invalid values

    if not srs_values:
        return None  # No valid SRS values
    
    srs_avg = sum(srs_values) / len(srs_values)
    win_percentage = sum(1 for g in regular_season_games if g["game_result"] == "W") / total_games
    avg_points = sum(int(g["pts"]) for g in regular_season_games) / total_games
    avg_opp_points = sum(int(g["opp_pts"]) for g in regular_season_games) / total_games
    streak_score = 0
    wins = []
    for g in regular_season_games:
        if g["game_result"] == "W":
            wins.append(g["opp_name"])
    for i, g in enumerate(regular_season_games[-10:]):
        if g["game_result"] == "W":
            streak_score += (i + 1)/10 * get_srs(g.get("srs", "").strip())

    return {"SRS": srs_avg, "Win%": win_percentage, "Ppg": avg_points, "Opp Ppg": avg_opp_points, "Streak Score": streak_score, "Wins": wins}

# Get head-to-head record
def get_head_to_head(team1_stats, team2_stats, team1, team2):
    return team1_stats["Wins"].count(team2) - team2_stats["Wins"].count(team1)

print("Loading data...")
start_time = time.time()

# Merge team stats with March Madness data
march_madness_df = pd.read_csv(f"data/{LEAGUE}/mm-results.csv")

# Apply the condition to filter rows
march_madness_df = march_madness_df[march_madness_df["Year"].apply(lambda x: x not in excluded_years)]

# Add stats for each team
def add_team_stats(row):
    year = row["Year"]

    # Randomly swap team order
    if random.random() < 0.5:
        row[["Team 1", "Team 2", "Seed 1", "Seed 2", "Score 1", "Score 2"]] = row[["Team 2", "Team 1", "Seed 2", "Seed 1", "Score 2", "Score 1"]]

    team1_stats = load_team_stats(year, row["Team 1"])
    team2_stats = load_team_stats(year, row["Team 2"])
    
    if not team1_stats or not team2_stats:
        logging.error(f"Stats missing for {year} - {row['Team 1']} vs {row['Team 2']}")
        return None  # Skip if stats are missing
    
    return pd.Series({
        "SRS_diff": team1_stats["SRS"] - team2_stats["SRS"],
        "SRS_high": max(team1_stats["SRS"], team2_stats["SRS"]),
        "SRS_low": min(team1_stats["SRS"], team2_stats["SRS"]),
        "Win%_diff": team1_stats["Win%"] - team2_stats["Win%"],
        "Win%_high": max(team1_stats["Win%"], team2_stats["Win%"]),
        "Win%_low": min(team1_stats["Win%"], team2_stats["Win%"]),
        "Ppg_diff": team1_stats["Ppg"] - team2_stats["Ppg"],
        "Ppg_high": max(team1_stats["Ppg"], team2_stats["Ppg"]),
        "Ppg_low": min(team1_stats["Ppg"], team2_stats["Ppg"]),
        "Opp_ppg_diff": team1_stats["Opp Ppg"] - team2_stats["Opp Ppg"],
        "Opp_ppg_high": max(team1_stats["Opp Ppg"], team2_stats["Opp Ppg"]),
        "Opp_ppg_low": min(team1_stats["Opp Ppg"], team2_stats["Opp Ppg"]),
        "Streak_high": max(team1_stats["Streak Score"], team2_stats["Streak Score"]),
        "Streak_low": min(team1_stats["Streak Score"], team2_stats["Streak Score"]),
        "Streak_diff": team1_stats["Streak Score"] - team2_stats["Streak Score"],
        "Head_to_head": get_head_to_head(team1_stats, team2_stats, row["Team 1"], row["Team 2"]),
        # "Seed_diff": row["Seed 1"] - row["Seed 2"],
        # "Seed_high": max(row["Seed 1"], row["Seed 2"]),
        # "Seed_low": min(row["Seed 1"], row["Seed 2"]),
        "Round": row["Round"],  # Keep round for reference
        "Winner": 1 if row["Score 1"] > row["Score 2"] else 0  # Label for ML model
    })


# Apply function to dataset
features_df = march_madness_df.apply(add_team_stats, axis=1).dropna()


# Train-test split
X = features_df.drop(columns=["Winner"])
y = features_df["Winner"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05, random_state=42)

print(f"Data loaded in {time.time() - start_time:.2f} seconds.")

print("Training model...")
start_time = time.time()

# Train model with XGBoost
model = XGBClassifier(n_estimators=100, learning_rate=0.1, verbosity=1)
model.fit(X_train, y_train)

print(f"Training completed in {time.time() - start_time:.2f} seconds.")

y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))


import joblib

# Save the model
joblib.dump(model, f"models/{LEAGUE}/march_madness_model.pkl")

# Load the model later
# model = joblib.load(f"models/{LEAGUE}/march_madness_model.pkl")