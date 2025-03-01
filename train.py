import json
import os
import pandas as pd
import logging
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier
import time
from sklearn.ensemble import RandomForestClassifier

# Extract team level stats
def load_team_stats(year, team_name):
    file_path = f"data/yearly/{year}-{team_name}.json"
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
    avg_point_diff = sum(int(g["pts"]) - int(g["opp_pts"]) for g in regular_season_games) / total_games

    return {"SRS": srs_avg, "Win%": win_percentage, "PointDiff": avg_point_diff}

print("Loading data...")
start_time = time.time()

# Merge team stats with March Madness data
march_madness_df = pd.read_csv("data/mm-results.csv")
excluded_years = [2010, 2011, 2018, 2019]  # Exclude years to run brackets on later

# Apply the condition to filter rows
march_madness_df = march_madness_df[march_madness_df["Year"].apply(lambda x: x not in excluded_years)]

# Add stats for each team
def add_team_stats(row):
    year = row["Year"]
    team1_stats = load_team_stats(year, row["Team 1"])
    team2_stats = load_team_stats(year, row["Team 2"])
    
    if not team1_stats or not team2_stats:
        logging.error(f"Stats missing for {year} - {row['Team 1']} vs {row['Team 2']}")
        return None  # Skip if stats are missing
    
    return pd.Series({
        "SRS_Diff": team1_stats["SRS"] - team2_stats["SRS"],
        "Win%_Diff": team1_stats["Win%"] - team2_stats["Win%"],
        "PointDiff_Diff": team1_stats["PointDiff"] - team2_stats["PointDiff"],
        "Seed_Diff": row["Seed 1"] - row["Seed 2"],
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
joblib.dump(model, "march_madness_model.pkl")

# Load the model later
# model = joblib.load("march_madness_model.pkl")
