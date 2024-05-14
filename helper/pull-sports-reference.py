import json
import logging
import pandas as pd
import requests
import time

logging.getLogger().setLevel(logging.INFO) # toggle logging level

# configure file paths
mm_results_path = './data/mm-results.csv'
sports_reference_names_path = 'sports-reference-names.json'
errors_path = 'errors'
error_list_filename = 'error-list.txt'
data_yearly_path = './data/yearly'

df = pd.read_csv(mm_results_path)

yearly_team_stats = {}
with open(sports_reference_names_path) as f:
    sr_names = json.load(f)

for year in range(1985, 2020):
    # get all March Madness teams for the year
    teams = set()
    games = df.loc[df['Year'] == year]
    for index, row in games.iterrows():
        teams.add(row['Team 1'])
        teams.add(row['Team 2'])
    
    # pull data for each March Madness team from Sports Reference
    for team in teams:
        if team not in sr_names:
            logging.warning(f"Could not find Sports Reference name for {team}. Skipping...")
            with open(f'{errors_path}/{error_list_filename}', 'a') as f:
                f.write(f"{year},{team},Team name not found\n")
            continue
        sr_team = sr_names[team]
        schedule_response = requests.get(f"https://www.sports-reference.com/cbb/schools/{sr_team}/men/{year}-schedule.html")
        if schedule_response.status_code != 200:
            with open(f'{errors_path}/{year}-{team}.html', 'w') as f:
                f.write(schedule_response.text)
            with open(f'{errors_path}/{error_list_filename}', 'a') as f:
                f.write(f"{year},{team},{schedule_response.status_code}\n")
            logging.error(f"Error retrieving schedule for {team} in {year} (code {schedule_response.status_code})")
        else:
            with open(f'{data_yearly_path}/{year}-{team}.html', 'w') as f:
                f.write(schedule_response.text)
            logging.info(f"Retrieved schedule for {team} in {year}")
        time.sleep(5) # be nice to the server
