import joblib
import json
import pandas as pd

# Load the trained model
model = joblib.load("march_madness_model.pkl")

import json
import os
import logging

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


# Load first-round matchups (assume this is from a CSV or pre-defined dataset)
def load_first_round(year):
    """Loads first-round matchups for the given year."""
    df = pd.read_csv(f"data/first_rounds/{year}_firsts.csv")  # Ensure the CSV has correct format
    return df

# Predict game winners
def predict_winner(team1, team2, seed1, seed2, year, model):
    """Uses the model to predict the winner of a matchup."""
    team1_stats = load_team_stats(year, team1)
    team2_stats = load_team_stats(year, team2)

    if not team1_stats or not team2_stats:
        return None  # Skip if data is missing

    features = pd.DataFrame([{
        "SRS_Diff": team1_stats["SRS"] - team2_stats["SRS"],
        "Win%_Diff": team1_stats["Win%"] - team2_stats["Win%"],
        "PointDiff_Diff": team1_stats["PointDiff"] - team2_stats["PointDiff"],
        "Seed_Diff": seed1 - seed2,
    }])

    return team1 if model.predict(features)[0] == 1 else team2

# Simulate full tournament using only the first-round data
def simulate_bracket(year, model, output_file="predicted_bracket.json"):
    """Simulates the entire tournament, using first-round matchups and progressing logically."""
    
    # Load first round games
    current_round = load_first_round(year)
    rounds = []  # Store all match results

    for r in range(1, 7):  # Keep going until only 1 team remains (champion)
        winners = []
        winning_seeds = []

        for _, game in current_round.iterrows():
            team1, team2 = game["Team 1"], game["Team 2"]
            seed1, seed2 = game["Seed 1"], game["Seed 2"]
            
            winner = predict_winner(team1, team2, seed1, seed2, year, model)
            winners.append(winner)
            winning_seeds.append(seed1 if winner == team1 else seed2)
            rounds.append({"Round": r, "Matchup": f"{team1} vs {team2}", "Winner": winner})

        # Prepare next round's matchups
        if r != 6:
            current_round = pd.DataFrame({"Team 1": winners[::2], "Team 2": winners[1::2], "Seed 1": winning_seeds[::2], "Seed 2": winning_seeds[1::2]})

    # Save results
    with open(output_file, "w") as file:
        json.dump(rounds, file, indent=4)

    print(f"Bracket saved to {output_file}")

# Run bracket simulation
for year in [2010, 2011, 2018, 2019]:
    simulate_bracket(year, model, output_file="predicted_brackets/predicted_bracket_{}.json".format(year))
