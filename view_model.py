import pickle
import xgboost as xgb
import numpy as np

LEAGUE = "men"
# LEAGUE = "women"

# Load the XGBoost model
with open(f"models/{LEAGUE}/march_madness_model.pkl", "rb") as f:
    model = pickle.load(f)

feature_names = model.get_booster().feature_names
importances = model.feature_importances_

# Sort features by importance
sorted_idx = np.argsort(importances)[::-1]

for idx in sorted_idx:
    print(f"{feature_names[idx]}: {importances[idx]}")

print()

d = {"streak": 0, "win_percentage": 0, "srs": 0, "ppg": 0, "opp_ppg": 0, "head_to_head": 0, "round": 0}
for idx in sorted_idx:
    if feature_names[idx] == "Streak_diff" or feature_names[idx] == "Streak_high" or feature_names[idx] == "Streak_low":
        d["streak"] += importances[idx]
    elif feature_names[idx] == "Win%_diff" or feature_names[idx] == "Win%_high" or feature_names[idx] == "Win%_low":
       d["win_percentage"] += importances[idx]
    elif feature_names[idx] == "SRS_diff" or feature_names[idx] == "SRS_high" or feature_names[idx] == "SRS_low":
        d["srs"] += importances[idx]
    elif feature_names[idx] == "Ppg_diff" or feature_names[idx] == "Ppg_high" or feature_names[idx] == "Ppg_low":
        d["ppg"] += importances[idx]
    elif feature_names[idx] == "Opp_ppg_diff" or feature_names[idx] == "Opp_ppg_high" or feature_names[idx] == "Opp_ppg_low":
        d["opp_ppg"] += importances[idx]
    elif feature_names[idx] == "Head_to_head":
        d["head_to_head"] = importances[idx]
    elif feature_names[idx] == "Round":
        d["round"] = importances[idx]
for k, v in sorted(d.items(), key=lambda x: x[1], reverse=True):
    print(f"{k}: {v}")
