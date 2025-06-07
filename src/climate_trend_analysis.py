import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging

# ------------------ CONFIG ------------------
INPUT_DIR = "data/processed/by_crop"
OUTPUT_DIR = "results/climate_trends"
YIELD_COL = "yield"
TEMP_COL = "tmax_mean"

# ------------------ LOGGING ------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ------------------ HELPER ------------------
def tag_heat_level(df):
    avg = df[TEMP_COL].mean()
    std = df[TEMP_COL].std()

    def tag(t):
        if t > avg + std:
            return "hot"
        elif t < avg - std:
            return "cool"
        else:
            return "normal"

    df["climate_band"] = df[TEMP_COL].apply(tag)
    return df

# ------------------ ANALYSIS ------------------
def analyze_climate_trends():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]

    for file in files:
        crop = file.replace(".csv", "")
        df = pd.read_csv(os.path.join(INPUT_DIR, file))

        if YIELD_COL not in df.columns or TEMP_COL not in df.columns:
            logging.warning(f"{crop}: Missing required columns.")
            continue

        df = df.dropna(subset=[YIELD_COL, TEMP_COL])
        if len(df) < 10:
            logging.warning(f"{crop}: Not enough data.")
            continue

        df = tag_heat_level(df)

        # Boxplot of yield vs climate band
        plt.figure(figsize=(6, 5))
        sns.boxplot(x="climate_band", y=YIELD_COL, data=df, palette="coolwarm")
        plt.title(f"{crop} – Yield by Hot/Normal/Cool Years")
        plt.ylabel("Yield")
        plt.xlabel("Climate Band")
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, f"{crop}_yield_by_climate_band.png"))
        plt.close()

        # Time series of yield
        plt.figure(figsize=(8, 4))
        sns.lineplot(data=df, x="year", y=YIELD_COL, marker="o")
        plt.title(f"{crop} – Yield Over Time")
        plt.ylabel("Yield")
        plt.xlabel("Year")
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, f"{crop}_yield_trend.png"))
        plt.close()

        # Save band averages
        band_summary = df.groupby("climate_band")[YIELD_COL].agg(["count", "mean", "std"]).reset_index()
        band_summary.to_csv(os.path.join(OUTPUT_DIR, f"{crop}_climate_band_summary.csv"), index=False)

        logging.info(f"{crop}: ✅ Plots and summary saved.")

# ------------------ ENTRY ------------------
if __name__ == "__main__":
    analyze_climate_trends()