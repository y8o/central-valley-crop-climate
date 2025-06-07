import os
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt

# ------------------ CONFIG ------------------
CROP_DIR = "data/processed/by_crop"
MAP_FILE = "data/raw/cv_county_boundaries.geojson"
OUTPUT_FILE = "results/climate_trends/all_crops_yield_change_map.png"
YIELD_COL = "yield"
TEMP_COL = "tmax_mean"

# ------------------ PROCESS ------------------
yield_deltas = []

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
    df["climate_band"] = df[TEMP_COL].apply(
        lambda t: "hot" if t > mean_temp + std_temp else "normal"
    )

    grouped = df.groupby(["county", "climate_band"])[YIELD_COL].mean().unstack()
    grouped["delta"] = grouped.get("hot", 0) - grouped.get("normal", 0)
    grouped["crop"] = crop
    grouped = grouped.reset_index()

    yield_deltas.append(grouped[["county", "delta"]])

# ------------------ AGGREGATE ------------------
combined = pd.concat(yield_deltas)
avg_change = combined.groupby("county")["delta"].mean().reset_index()
avg_change.columns = ["county", "avg_yield_change_hot_vs_normal"]

# ------------------ LOAD MAP ------------------
gdf = gpd.read_file(MAP_FILE)
gdf["county"] = gdf["NAME"].str.upper().str.replace(" ", "_")

# ------------------ MERGE ------------------
merged = gdf.merge(avg_change, on="county", how="left")

# ------------------ PLOT ------------------
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
merged.plot(
    column="avg_yield_change_hot_vs_normal",
    cmap="coolwarm",
    legend=True,
    edgecolor="black",
    ax=ax,
    missing_kwds={"color": "lightgrey", "label": "No data"}
)
ax.set_title("Average Yield Change in Hot Years vs Normal (All Crops)")
plt.axis("off")
plt.tight_layout()
plt.savefig(OUTPUT_FILE)
plt.close()

print(f"✔ Map saved to {OUTPUT_FILE}")