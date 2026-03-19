import joblib
import json
import pandas as pd
import numpy as np
import os
import logging
import csv
from collections import defaultdict

# LEAGUE = "men"
LEAGUE = "women"
prediction_years = [2026]

# Load the trained model
model = joblib.load(f"models/{LEAGUE}/march_madness_model.pkl")

# Load team ID mapping
with open(f"kaggle/{LEAGUE}_team_ids.json", "r") as f:
    team_name_to_id = json.load(f)

# Helper function to get srs score from string
def get_srs(srs_str):
    if srs_str:
        try:
            return float(srs_str)
        except ValueError:
            return 0
    return 0

# Helper function to safely convert to int
def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

# Extract team level stats
def load_team_stats(year, team_name):
    file_path = f"data/{LEAGUE}/yearly/{year}-{team_name}.json"
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return None
    
    with open(file_path, "r") as file:
        games = json.load(file)

    regular_season_games = [g for g in games if g["game_type"] != "NCAA"]
    
    total_games = len(regular_season_games)
    if total_games == 0:
        return None
    
    srs_values = []
    for g in regular_season_games:
        srs_str = g.get("srs", "").strip()
        if srs_str:
            try:
                srs_values.append(float(srs_str))
            except ValueError:
                continue

    if not srs_values:
        return None
    
    srs_avg = sum(srs_values) / len(srs_values)
    win_percentage = sum(1 for g in regular_season_games if g["game_result"] == "W") / total_games
    try:
        avg_points = sum(safe_int(g["pts"]) for g in regular_season_games) / total_games
    except ValueError:
        print("Error calculating average points for team {}".format(team_name))
    avg_opp_points = sum(safe_int(g["opp_pts"]) for g in regular_season_games) / total_games
    streak_score = 0
    for i, g in enumerate(regular_season_games[-10:]):
        if g["game_result"] == "W":
            streak_score += (i + 1)/10 * get_srs(g.get("srs", "").strip())
    wins = []
    win_srs = []
    loss_srs = []

    for g in regular_season_games:
        result = g["game_result"]
        srs_val = get_srs(g.get("srs", "").strip())

        if result == "W":
            wins.append(g["opp_name"])
            if srs_val is not None:
                win_srs.append(srs_val)
        elif result == "L":
            if srs_val is not None:
                loss_srs.append(srs_val)

    if win_srs:
        top_wins = sorted(win_srs, reverse=True)[:3]
        best_wins = sum(top_wins) / len(top_wins)
    else:
        best_wins = 0

    if loss_srs:
        worst_losses_list = sorted(loss_srs)[:3]
        worst_losses = sum(worst_losses_list) / len(worst_losses_list)
    else:
        worst_losses = 0

    return {
        "SRS": srs_avg,
        "Win%": win_percentage,
        "Ppg": avg_points,
        "Opp Ppg": avg_opp_points,
        "Streak Score": streak_score,
        "Best Wins": best_wins,
        "Worst Losses": worst_losses,
        "Wins": wins
    }

# Load first-round matchups
def load_first_round(year):
    df = pd.read_csv(f"data/{LEAGUE}/first_rounds/{year}_firsts.csv")
    return df

# Get win probability for a matchup
def get_win_probability(team1_name, team2_name, seed1, seed2, year, round_num, model):
    team1_stats = load_team_stats(year, team1_name)
    team2_stats = load_team_stats(year, team2_name)

    if not team1_stats or not team2_stats:
        return None

    features = pd.DataFrame([{
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
        "Best_wins_diff": team1_stats["Best Wins"] - team2_stats["Best Wins"],
        "Best_wins_high": max(team1_stats["Best Wins"], team2_stats["Best Wins"]),
        "Best_wins_low": min(team1_stats["Best Wins"], team2_stats["Best Wins"]),
        "Worst_losses_diff": team1_stats["Worst Losses"] - team2_stats["Worst Losses"],
        "Worst_losses_high": max(team1_stats["Worst Losses"], team2_stats["Worst Losses"]),
        "Worst_losses_low": min(team1_stats["Worst Losses"], team2_stats["Worst Losses"]),
        "Round": round_num,
        "Year": year
    }])

    try:
        prob = model.predict_proba(features)[0][1]
        return float(prob)
    except:
        return 1.0 if model.predict(features)[0] == 1 else 0.0

# Generate probabilities for all possible tournament games
def generate_tournament_probabilities(year, model, output_file="tournament_probabilities.csv"):
    """Generates win probabilities for every possible game in the tournament structure."""
    
    # Load first round games
    first_round_df = load_first_round(year)
    
    # Initialize the bracket slots
    # Each slot contains a list of possible (team, seed) that could be in that slot
    bracket_slots = []
    
    # First round: process the predetermined matchups
    all_games = []
    print("Processing Round 1 (predetermined matchups)")
    
    for _, game in first_round_df.iterrows():
        team1 = game["Team 1"]
        team2 = game["Team 2"]
        seed1 = game["Seed 1"]
        seed2 = game["Seed 2"]
        
        # Get team IDs
        if team1 not in team_name_to_id or team2 not in team_name_to_id:
            continue
        
        team1_id = team_name_to_id[team1]
        team2_id = team_name_to_id[team2]
        
        # Get win probability
        prob_team1_wins = get_win_probability(team1, team2, seed1, seed2, year, 1, model)
        
        if prob_team1_wins is not None:
            # Determine lower ID team and corresponding probability
            if team1_id < team2_id:
                lower_id = team1_id
                higher_id = team2_id
                prob_lower_wins = prob_team1_wins
            else:
                lower_id = team2_id
                higher_id = team1_id
                prob_lower_wins = 1 - prob_team1_wins
            
            matchup_id = f"{year}_{lower_id}_{higher_id}"
            
            game_info = {
                "ID": matchup_id,
                "Pred": round(prob_lower_wins, 4),
                "Round": 1,
                "Team1": team1,
                "Team2": team2,
                "Seed1": seed1,
                "Seed2": seed2
            }
            all_games.append(game_info)
        
        # Create slot with both possible winners for future rounds
        bracket_slots.append([
            (team1, seed1),
            (team2, seed2)
        ])
    
    print(f"Round 1: {len(all_games)} games")
    
    # Process subsequent rounds
    round_num = 2
    
    while len(bracket_slots) > 1:
        print(f"Processing Round {round_num} with {len(bracket_slots)} slots")
        
        next_round_slots = []
        round_games = []
        
        # Pair up slots for this round's games
        for i in range(0, len(bracket_slots), 2):
            slot1 = bracket_slots[i]
            slot2 = bracket_slots[i+1]
            
            # Every team from slot1 can play every team from slot2
            for team1, seed1 in slot1:
                for team2, seed2 in slot2:
                    # Get team IDs
                    if team1 not in team_name_to_id or team2 not in team_name_to_id:
                        continue
                    
                    team1_id = team_name_to_id[team1]
                    team2_id = team_name_to_id[team2]
                    
                    # Get win probability
                    prob_team1_wins = get_win_probability(team1, team2, seed1, seed2, year, round_num, model)
                    
                    if prob_team1_wins is not None:
                        # Determine lower ID team and corresponding probability
                        if team1_id < team2_id:
                            lower_id = team1_id
                            higher_id = team2_id
                            prob_lower_wins = prob_team1_wins
                        else:
                            lower_id = team2_id
                            higher_id = team1_id
                            prob_lower_wins = 1 - prob_team1_wins
                        
                        matchup_id = f"{year}_{lower_id}_{higher_id}"
                        
                        game_info = {
                            "ID": matchup_id,
                            "Pred": round(prob_lower_wins, 4),
                            "Round": round_num,
                            "Team1": team1,
                            "Team2": team2,
                            "Seed1": seed1,
                            "Seed2": seed2
                        }
                        round_games.append(game_info)
                        all_games.append(game_info)
            
            # Create next round slot with all possible winners
            next_slot = []
            for team1, seed1 in slot1:
                for team2, seed2 in slot2:
                    next_slot.append((team1, seed1))  # Team1 could win
                    next_slot.append((team2, seed2))  # Team2 could win
            
            # Remove duplicates while preserving order
            next_slot = list(dict.fromkeys(next_slot))
            next_round_slots.append(next_slot)
        
        print(f"Round {round_num}: {len(round_games)} possible games")
        round_num += 1
        bracket_slots = next_round_slots
    
    # Write to CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Pred'])
        
        for game in all_games:
            writer.writerow([game['ID'], game['Pred']])
    
    print(f"\nTotal games analyzed: {len(all_games)}")
    print(f"Probabilities CSV saved to {output_file}")
    
    # Save detailed JSON for debugging
    debug_file = output_file.replace('.csv', '_details.json')
    with open(debug_file, 'w') as f:
        json.dump(all_games, f, indent=2)
    
    return all_games

# Run probability generation
for year in prediction_years:
    generate_tournament_probabilities(
        year, 
        model, 
        output_file=f"kaggle/predictions/{LEAGUE}/probabilities_{year}.csv"
    )