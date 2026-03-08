import pandas as pd

LEAGUE = "men"
# LEAGUE = "women"
eval_years = [2025]

# Load actual results
actual_results = pd.read_csv(f"data/{LEAGUE}/mm-results.csv")

def get_actual_winners(games):
    winners = set()
    for game in games:
        if game["Score 1"] > game["Score 2"]:
            winners.add(game["Team 1"])
        else:
            winners.add(game["Team 2"])
    return winners

for year in eval_years:
    num_correct_predictions_total = 0
    # Load predicted bracket
    predicted_results = pd.read_json(f"predicted_brackets/{LEAGUE}/predicted_bracket_{year}.json")

    for round in range(1, 7):
        # Get actual results for this round
        actual_round = actual_results[(actual_results["Year"] == year) & (actual_results["Round"] == round)]
        predicted_round = predicted_results[predicted_results["Round"] == round]

        # Compare actual vs predicted
        actual_winners = get_actual_winners(actual_round.to_dict(orient="records"))
        predicted_round = predicted_round.to_dict(orient="records")
        predicted_winners = set([game["Winner"] for game in predicted_round])
        num_correct_predictions = len(actual_winners & predicted_winners)
        num_correct_predictions_total += num_correct_predictions
        num_games = len(actual_round)

        print(f"Year: {year}, Round: {round}, Correct Predictions: {num_correct_predictions}/{num_games} ({num_correct_predictions/num_games:.0%})")
    
    print(f"Year: {year}, Total Correct Predictions: {num_correct_predictions_total}/63 ({num_correct_predictions_total/63:.0%})")
    print()