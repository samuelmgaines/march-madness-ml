import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import json
import os

START_YEAR = 1985
END_YEAR = 2025
EXCLUDE_YEARS = {2020}

LEAGUE = "men"
# LEAGUE = "women"

OUTPUT_FILE = f"../data/{LEAGUE}/mm-results.csv"
TEAM_DATA_DIR = f"../data/{LEAGUE}/teams"

NAME_MAP_FILE = "mm-results-names.json"

BASE_URL = "https://www.sports-reference.com/cbb/postseason/{league}/{year}-ncaa.html"

RATE_LIMIT_SECONDS = 5
last_request_time = 0


# -------------------------------------------------
# Load team name mapping
# -------------------------------------------------
with open(NAME_MAP_FILE, "r", encoding="utf-8") as f:
    TEAM_NAME_MAP = json.load(f)


# -------------------------------------------------
# Rate limited request
# -------------------------------------------------
def rate_limited_get(url):
    global last_request_time

    elapsed = time.time() - last_request_time
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)

    response = requests.get(url)
    last_request_time = time.time()
    return response


# -------------------------------------------------
# Resolve team name
# Supports arrays of possible names
# -------------------------------------------------
def resolve_team_name(scraped_name):
    mapped = TEAM_NAME_MAP.get(scraped_name)

    if mapped is None:
        return scraped_name

    # If mapped value is a single name
    if isinstance(mapped, str):
        return mapped

    # If mapped value is a list of possible names
    if isinstance(mapped, list):
        for candidate in mapped:
            team_file = os.path.join(TEAM_DATA_DIR, f"{candidate}.csv")
            if os.path.exists(team_file):
                return candidate

        # fallback if none exist
        return mapped[0]

    return scraped_name


# -------------------------------------------------
# Parse tournament year
# -------------------------------------------------
def parse_year(year):

    print(f"Processing {year}")

    url = BASE_URL.format(year=year, league=LEAGUE)
    r = rate_limited_get(url)

    if r.status_code != 200:
        print(f"Failed for {year}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    brackets = soup.find("div", id="brackets")
    if not brackets:
        print(f"No bracket found for {year}")
        return []

    data = []

    region_number_map = {}
    next_region_number = 1

    for region in brackets.find_all("div", recursive=False):

        region_name = region.get("id")
        if not region_name:
            continue

        # National bracket = Final Four + Championship
        if region_name == "national":
            region_number = 0
        else:
            if region_name not in region_number_map:
                region_number_map[region_name] = next_region_number
                next_region_number += 1

            region_number = region_number_map[region_name]

        bracket_div = region.find("div", id="bracket")
        if not bracket_div:
            continue

        rounds = bracket_div.find_all("div", class_="round")

        for round_index, round_div in enumerate(rounds, start=1):

            games = round_div.find_all("div", recursive=False)

            for game in games:

                teams = game.find_all("div", recursive=False)
                if len(teams) < 2:
                    continue

                try:

                    # Team 1
                    seed1 = teams[0].find("span").text.strip()
                    links1 = teams[0].find_all("a")
                    team1 = links1[0].text.strip()
                    score1 = links1[1].text.strip() if len(links1) > 1 else ""

                    # Team 2
                    seed2 = teams[1].find("span").text.strip()
                    links2 = teams[1].find_all("a")
                    team2 = links2[0].text.strip()
                    score2 = links2[1].text.strip() if len(links2) > 1 else ""

                except:
                    continue

                # Normalize team names
                team1 = resolve_team_name(team1)
                team2 = resolve_team_name(team2)

                # Handle Final Four + Championship
                if region_name == "national":
                    actual_round = 5 if round_index == 1 else 6
                else:
                    actual_round = round_index

                data.append([
                    year,
                    actual_round,
                    region_number,
                    region_name.capitalize(),
                    seed1,
                    score1,
                    team1,
                    team2,
                    score2,
                    seed2
                ])

    return data


# -------------------------------------------------
# Main execution
# -------------------------------------------------
def main():

    all_rows = []

    for year in range(START_YEAR, END_YEAR + 1):

        if year in EXCLUDE_YEARS:
            continue

        rows = parse_year(year)

        print(f"Found {len(rows)} games")

        all_rows.extend(rows)

    df = pd.DataFrame(all_rows, columns=[
        "Year",
        "Round",
        "Region Number",
        "Region Name",
        "Seed 1",
        "Score 1",
        "Team 1",
        "Team 2",
        "Score 2",
        "Seed 2"
    ])

    df.to_csv(OUTPUT_FILE, index=False)

    print("Finished writing:", OUTPUT_FILE)


if __name__ == "__main__":
    main()