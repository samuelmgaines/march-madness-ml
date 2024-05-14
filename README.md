# March Madness ML Algorithm (In Development)

## Project Description

In this personal project, I train a machine learning model to make men's March Madness predictions based on historical data from past college basketball seasons. Development is currently in progress.

## Data

### March Madness History

Data from previous March Madness tournaments (1985 - 2019) comes from [here](https://data.world/michaelaroy/ncaa-tournament-results). This data has been downloaded and can be found in `data/mm-results.csv`. A few column names have been altered for uniqueness and clarity.

### Seasonal Stats

Team stats from each season are pulled from [SportsReference](https://www.sports-reference.com/cbb). This data is not in the repository by default. Download instructions are found in Set Up.

## Set Up

### Download Seasonal Stats

Before training the model, seasonal data for each March Madness team must be scraped from SportsReference. To do this, run `helper/pull-sports-reference.py`. This will take a few hours since SportsReference has a rate-limiting policy. When the process is complete, data can be found in `data/yearly` with filename format `YEAR-Team.html`.

A list of any errors from the load can be found in `helper/errors/error-list.txt`. Each line in this file represents an error and has the format `YEAR,Team,Error code`. The full error response for each request can be found in `helper/errors/YEAR-Team.html`.

An error code of `Team name not found` signifies that the team was not found in `helper/sports-reference-names.json`. Add it as a key in this file and set the value to the team's SportsReference name. To find this, visit https://www.sports-reference.com/cbb/schools/ and click on the team. The URL will then have the format `https://www.sports-reference.com/cbb/schools/TEAM/men/`, where `TEAM` is the SportsReference team name.

Similarly, an error code of `404` most likely signifies that the SportsReference team name is incorrect in `helper/sports-reference-names.json`.

Once all errors are addressed, delete all files from the `helper/errors` directory (except `error-list.txt`). Then, run `helper/pull-sports-reference-errors.py` to pull data from the seasons specified in `error-list.txt`. If there are any more errors, repeat the troubleshooting process.