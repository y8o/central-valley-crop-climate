import os
import pandas as pd
import numpy as np
import logging
import statsmodels.api as sm

# ------------------ CONFIG ------------------
INPUT_DIR = "data/processed/by_crop"
OUTPUT_FILE = "results/climate_trends/crop_sensitivity_summary.csv"
YIELD_COL = "yield"
TEMP_COL = "tmax_mean"

# ------------------ LOGGING ------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ------------------ MAIN ------------------
results = []

for file in os.listdir(INPUT_DIR):
    if not file.endswith(".csv"):
        continue
    crop = file.replace(".csv", "")
    df = pd.read_csv(os.path.join(INPUT_DIR, file))
    df = df.dropna(subset=[YIELD_COL, TEMP_COL])

    if len(df) < 10:
        continue

    X = sm.add_constant(df[TEMP_COL])
    y = df[YIELD_COL]
    model = sm.OLS(y, X).fit()

    results.append({
        "crop": crop,
        "slope_tmax": model.params[TEMP_COL],
        "intercept": model.params["const"],
        "r_squared": model.rsquared,
        "n": len(df)
    })

pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False)
print(f"Saved climate sensitivity summary to {OUTPUT_FILE}")