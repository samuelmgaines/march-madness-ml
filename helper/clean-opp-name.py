import json
import re
import os

# Folder paths
input_folder = "../data/yearly"
output_folder = "../data/yearly-cleaned"

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# Function to clean opponent names
def clean_opp_name(name):
    new_opp_name = re.split(r"\u00a0", name)[0].strip()
    if '-' in new_opp_name:
        new_opp_name = new_opp_name.replace('-', ' ')
    if 'State' in new_opp_name and new_opp_name != 'NC State':
        new_opp_name = new_opp_name.replace('State', 'St')
    if 'Saint' in new_opp_name:
        new_opp_name = new_opp_name.replace('Saint', 'St')
    return new_opp_name

march_teams = set()
opp_teams = set()
# Process each file in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith(".json"):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        team_name = filename.split("-")[1].split(".")[0]
        march_teams.add(team_name)
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Apply cleaning
        for game in data:
            game["opp_name"] = clean_opp_name(game["opp_name"])
            opp_teams.add(game["opp_name"])
        
        # Save the cleaned data
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        print(f"Cleaned data saved to {output_path}")

# print(f"March Madness teams found: {march_teams}")
# print()
# print(f"Opponent teams found: {opp_teams}")