from bs4 import BeautifulSoup
import json
import logging
import pandas as pd
import requests
import time

logging.getLogger().setLevel(logging.INFO) # toggle logging level

# helper function to parse HTML table
def parse_html_table(table):
    # parse the column headers
    try:
        headers = []
        html_headers = table.find_all('thead')[0].find_all('tr')[0].find_all('th')
        for header in html_headers:
            headers.append(header.get('data-stat'))
    except:
        logging.error(f'No headers found for {year} {team}')
        return None

    # parse the rows
    try:
        games = []
        for row in table.find_all('tbody')[0].find_all('tr'):
            if row.get('class') == ['thead']:
                continue
            cells = row.find_all('td')
            game = {}
            for i, cell in enumerate(cells):
                game[headers[i+1]] = cell.get_text()
            games.append(game)
    except:
        logging.error(f'Error parsing rows for {year} {team}')
        return None
    
    return games

# configure file paths
mm_results_path = '../data/mm-results.csv'
sports_reference_names_path = 'sports-reference-names.json'
errors_path = 'errors'
error_list_filename = 'error-list.txt'
data_yearly_path = '../data/yearly'

df = pd.read_csv(mm_results_path)

with open(sports_reference_names_path) as f:
    sr_names = json.load(f)

with open(f'{errors_path}/{error_list_filename}', 'r') as f:
    error_list = f.readlines()

# pull data for each March Madness team from Sports Reference
for error in error_list:
    # make sure team name is in the Sports Reference names dictionary
    year, team, status_code = error.strip().split(',')
    if team not in sr_names:
        logging.warning(f"Could not find Sports Reference name for {team}. Skipping...")
        with open(f'{errors_path}/{error_list_filename}', 'a') as f:
            f.write(f"{year},{team},Team name not found\n")
        continue

    # make HTTP request to Sports Reference
    sr_team = sr_names[team]
    schedule_response = requests.get(f"https://www.sports-reference.com/cbb/schools/{sr_team}/men/{year}-schedule.html")

    # handle error status code
    if schedule_response.status_code != 200:
        with open(f'{errors_path}/{year}-{team}.html', 'w') as f:
            f.write(schedule_response.text)
        with open(f'{errors_path}/{error_list_filename}', 'a') as f:
            f.write(f"{year}-{team}: {schedule_response.status_code}\n")
        logging.error(f"Error retrieving schedule for {team} in {year}")
        continue

    # parse HTML response
    soup = BeautifulSoup(schedule_response.text, 'html.parser')
    table = soup.find(id='schedule')
    if table is None:
        logging.error(f'No schedule found for {year} {team}')
        with open(f'{errors_path}/{year}-{team}.html', 'w') as f:
            f.write(schedule_response.text)
        with open(f'{errors_path}/{error_list_filename}', 'a') as f:
            f.write(f"{year},{team},No schedule found\n")
        continue
    games = parse_html_table(table)
    if games is None:
        with open(f'{errors_path}/{year}-{team}.html', 'w') as f:
            f.write(schedule_response.text)
        with open(f'{errors_path}/{error_list_filename}', 'a') as f:
            f.write(f"{year},{team},Error parsing table\n")
        continue
    
    # save data to file
    with open(f'{data_yearly_path}/{year}-{team}.json', 'w') as f:
        json.dump(games, f, indent=4)
    logging.info(f"Retrieved schedule for {team} in {year}")
    time.sleep(5) # be nice to the server