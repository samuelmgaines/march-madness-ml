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
excluded_years = {2025}  # Exclude years to test later (don't train on them)


# Safe helpers
def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def get_stat(game, *keys, default=""):
    for key in keys:
        if key in game and game[key] not in ("", None):
            return game[key]
    return default


# Helper function to get srs score from string
def get_srs(srs_str):
    if srs_str:
        try:
            return float(srs_str)
        except ValueError:
            return 0
    return 0


# Extract team level stats
def load_team_stats(year, team_name):
    file_path = f"data/{LEAGUE}/yearly/{year}-{team_name}.json"

    if not os.path.exists(file_path):
        with open("helper/alternate-names.json", "r") as f:
            name_mapping = json.load(f)
        if team_name in name_mapping:
            file_path = f"data/{LEAGUE}/yearly/{year}-{name_mapping[team_name]}.json"
            if not os.path.exists(file_path):
                logging.error(f"File not found: {file_path}")
        else:
            logging.error(f"File not found: {file_path}")
            return None

    with open(file_path, "r") as file:
        games = json.load(file)

    # Exclude March Madness games
    try:
        regular_season_games = [g for g in games if g.get("game_type") != "NCAA"]
    except KeyError:
        regular_season_games = games

    total_games = len(regular_season_games)

    if total_games == 0:
        return None

    srs_values = []

    for g in regular_season_games:
        srs_str = get_stat(g, "srs", "SRS").strip()

        if srs_str:
            try:
                srs_values.append(float(srs_str))
            except ValueError:
                continue

    # If no SRS exists, default to 0 instead of dropping the team
    if srs_values:
        srs_avg = sum(srs_values) / len(srs_values)
    else:
        srs_avg = 0

    win_percentage = (
        sum(1 for g in regular_season_games if get_stat(g, "game_result", "result") == "W")
        / total_games
    )

    avg_points = (
        sum(safe_int(get_stat(g, "pts", "points")) for g in regular_season_games)
        / total_games
    )

    avg_opp_points = (
        sum(safe_int(get_stat(g, "opp_pts", "opp_points")) for g in regular_season_games)
        / total_games
    )

    streak_score = 0
    wins = []

    for g in regular_season_games:
        if get_stat(g, "game_result", "result") == "W":
            wins.append(get_stat(g, "opp_name", "opponent"))

    for i, g in enumerate(regular_season_games[-10:]):
        if get_stat(g, "game_result", "result") == "W":
            streak_score += (i + 1) / 10 * get_srs(get_stat(g, "srs", "SRS").strip())

    return {
        "SRS": srs_avg,
        "Win%": win_percentage,
        "Ppg": avg_points,
        "Opp Ppg": avg_opp_points,
        "Streak Score": streak_score,
        "Wins": wins,
    }


# Get head-to-head record
def get_head_to_head(team1_stats, team2_stats, team1, team2):
    return team1_stats["Wins"].count(team2) - team2_stats["Wins"].count(team1)


print("Loading data...")
start_time = time.time()

march_madness_df = pd.read_csv(f"data/{LEAGUE}/mm-results.csv")

march_madness_df = march_madness_df[
    march_madness_df["Year"].apply(lambda x: x not in excluded_years)
]


# Add stats for each team
def add_team_stats(row):

    year = row["Year"]

    if random.random() < 0.5:
        row[["Team 1", "Team 2", "Seed 1", "Seed 2", "Score 1", "Score 2"]] = row[
            ["Team 2", "Team 1", "Seed 2", "Seed 1", "Score 2", "Score 1"]
        ]

    team1_stats = load_team_stats(year, row["Team 1"])
    team2_stats = load_team_stats(year, row["Team 2"])

    if not team1_stats or not team2_stats:
        logging.error(f"Stats missing for {year} - {row['Team 1']} vs {row['Team 2']}")
        return None

    return pd.Series(
        {
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
            "Streak_high": max(
                team1_stats["Streak Score"], team2_stats["Streak Score"]
            ),
            "Streak_low": min(
                team1_stats["Streak Score"], team2_stats["Streak Score"]
            ),
            "Streak_diff": team1_stats["Streak Score"]
            - team2_stats["Streak Score"],
            "Round": row["Round"],
            "Year": year,
            "Winner": 1 if row["Score 1"] > row["Score 2"] else 0,
        }
    )


features_df = march_madness_df.apply(add_team_stats, axis=1).dropna()

X = features_df.drop(columns=["Winner"])
y = features_df["Winner"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.05, random_state=42
)

print(f"Data loaded in {time.time() - start_time:.2f} seconds.")

print("Training model...")
start_time = time.time()

model = XGBClassifier(n_estimators=100, learning_rate=0.1, verbosity=1)

model.fit(X_train, y_train)

print(f"Training completed in {time.time() - start_time:.2f} seconds.")

y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))


import joblib

joblib.dump(model, f"models/{LEAGUE}/march_madness_model.pkl")

# model = joblib.load(f"models/{LEAGUE}/march_madness_model.pkl")