import pickle
import xgboost as xgb
import numpy as np

# Load the XGBoost model
with open("march_madness_model.pkl", "rb") as f:
    model = pickle.load(f)

feature_names = model.get_booster().feature_names
importances = model.feature_importances_

# Sort features by importance
sorted_idx = np.argsort(importances)[::-1]

for idx in sorted_idx:
    print(f"{feature_names[idx]}: {importances[idx]}")