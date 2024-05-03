# March Madness ML Algorithm

## Project Description

In this personal project, I train a machine learning model to make men's March Madness predictions based on historical data from past college basketball seasons. Development is currently in progress.

## Set Up

### Requirements

To use this project, you will need a free API key for SportsDataIO. Get this key by visiting their [website](https://sportsdata.io/developers) and registering for the SportsDataIO API Free Trial. If prompted for a sport, select College Basketball (CBB).

### Environment Variables

Create a file `.env` in the root directory. The contents of the file should be the following:

```
API_KEY=your_sportsdataio_api_key
```

## Data

### March Madness History

Data from previous March Madness tournaments (1985 - 2019) comes from [here](https://data.world/michaelaroy/ncaa-tournament-results). This data has been downloaded and can be found in `data/mm-results.csv`. A few column names have been altered for uniqueness and clarity.

### Seasonal Stats
Team stats from each season are pulled from the [SportsDataIO](https://sportsdata.io/developers) API.
