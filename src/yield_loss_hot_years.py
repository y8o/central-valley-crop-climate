import os
import pandas as pd
import numpy as np

# ------------------ CONFIG ------------------
CROP_DIR = "data/processed/by_crop"
OUTPUT_FILE = "results/climate_trends/yield_loss_hot_years.csv"
YIELD_COL = "yield"
TEMP_COL = "tmax_mean"

rows = []

for file in os.listdir(CROP_DIR):
    if not file.endswith(".csv"):
        continue

    crop = file.replace(".csv", "")
    df = pd.read_csv(os.path.join(CROP_DIR, file))
    if YIELD_COL not in df.columns or TEMP_COL not in df.columns:
        continue

    df = df.dropna(subset=[YIELD_COL, TEMP_COL])
    if len(df) < 10:
        continue

    mean_temp = df[TEMP_COL].mean()
    std_temp = df[TEMP_COL].std()

    df["band"] = df[TEMP_COL].apply(lambda t: "hot" if t > mean_temp + std_temp else "normal")

    hot_yield = df[df["band"] == "hot"][YIELD_COL].mean()
    normal_yield = df[df["band"] == "normal"][YIELD_COL].mean()
    delta = hot_yield - normal_yield
    percent = 100 * delta / normal_yield if normal_yield else np.nan
    n_hot = df["band"].value_counts().get("hot", 0)

    rows.append({
        "crop": crop,
        "normal_yield": round(normal_yield, 2),
        "hot_yield": round(hot_yield, 2),
        "yield_change": round(delta, 2),
        "percent_change": round(percent, 2),
        "hot_years": n_hot
    })

df_out = pd.DataFrame(rows)
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
df_out.to_csv(OUTPUT_FILE, index=False)
print(f"✔ Yield loss summary saved to {OUTPUT_FILE}")