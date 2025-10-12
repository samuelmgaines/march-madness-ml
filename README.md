# March Madness ML Algorithm

## Project Description

In this personal project, I train a machine learning model to make men's March Madness predictions based on historical data from past college basketball seasons.

## Data

### March Madness History

Data from previous March Madness tournaments (1985 - 2019) comes from [here](https://data.world/michaelaroy/ncaa-tournament-results). This data has been downloaded and can be found in `data/mm-results.csv`. A few column names have been altered for uniqueness and clarity.

### Seasonal Stats

Team stats from each season are pulled from [SportsReference](https://www.sports-reference.com/cbb). This data is not in the repository by default. Download instructions are found in Set Up.

## Usage

### Provide First Round Matchups

Make sure any years you wish to create a bracket for are present in the `data/first_rounds` folder. If any are not present, they will likely need to be manually created. _Order of the games matters!_

### Download Seasonal Stats

Before training the model, seasonal data for each March Madness team must be scraped from SportsReference. To do this, run `helper/pull-sports-reference.py`. This will take a few hours since SportsReference has a rate-limiting policy. When the process is complete, data can be found in `data/yearly` with filename format `Year-Team.json`. Make sure the code is configured to download all years you wish to train or make a prediction on. The variable `mm_results_path` can be set to point to a `first_rounds` file if a desired year is not present in `mm-results.csv`.

A list of any errors from the load can be found in `helper/errors/error-list.txt`. Each line in this file represents an error and has the format `Year,Team,Error code`. The full error response for each request can be found in `helper/errors/Year-Team.html`.

An error code of `Team name not found` signifies that the team was not found in `helper/sports-reference-names.json`. Add it as a key in this file and set the value to the team's SportsReference name. To find this, visit https://www.sports-reference.com/cbb/schools/ and click on the team. The URL will then have the format `https://www.sports-reference.com/cbb/schools/TEAM/men/`, where `TEAM` is the SportsReference team name.

Similarly, an error code of `404` most likely signifies that the SportsReference team name is incorrect in `helper/sports-reference-names.json`.

An error code of `No schedule found` signifies that the table was not located in the HTML response. Further troubleshooting should be done to discover why this might be.

An error code of `Error parsing table` signifies that the table could not be parsed correctly for some reason. Like before, further troubleshooting should be done.

Any other error codes will also require further troubleshooting.

Once all errors are addressed, delete all files from the `helper/errors` directory (except `error-list.txt`). Then, run `helper/pull-sports-reference-errors.py` to pull data from the seasons specified in `error-list.txt`. If there are any more errors, repeat the troubleshooting process.

### Train the Model

After downloading all the seasonal stats, train the model by running `train.py`. Make sure the code is configured to train on the years you wish to train on. This creates the model and stores it in `march_madness_model.pkl`.

### View the Model

After creating the model, you can view how it weighs different factors by running `view_model.py`.

### Fill out a Bracket

After creating the model, fill out brackets by running `test.py`. Make sure the code is configured to run on the years you wish to create a bracket for. Predictions will be placed in the `predicted_brackets` folder.

### Evaluate the Model

After filling out brackets, evaluate the predictions by running `evaluate.py`. This will only work if results for predicted years are present in `data/mm-results.csv`.

## Results

The model created a 2025 prediction that can be found in the `archive` folder. The algorithm's results were submitted in the ESPN Tournament Challenge, and can be viewed [here](https://fantasy.espn.com/games/tournament-challenge-bracket-2025/bracket?id=f7758260-02f2-11f0-bf6c-6defe417cf10). The algorithm's bracket score 880 points, placing it in the 48.5 percentile across all 2025 brackets. Unfortunately, the algorithm selected 2-seed St. John's, who was eliminated in the second round, to win it all.
