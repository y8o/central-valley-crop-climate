import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

# ------------------ CONFIG ------------------
CROP_DIR = "data/processed/by_crop"
MAP_FILE = "data/raw/cv_county_boundaries.geojson"
OUTPUT_CSV = "data/processed/avg_yield_by_county.csv"
OUTPUT_PNG = "results/central_valley_yield_map.png"
YIELD_COL = "yield"

# ------------------ STEP 1: COMPUTE COUNTY-LEVEL AVG YIELD ------------------
all_rows = []

for file in os.listdir(CROP_DIR):
    if not file.endswith(".csv"):
        continue
    df = pd.read_csv(os.path.join(CROP_DIR, file))
    if YIELD_COL not in df.columns:
        continue
    df = df.dropna(subset=[YIELD_COL])
    if len(df) < 5:
        continue
    df["county"] = df["county"].str.upper().str.replace(" ", "_")
    all_rows.append(df[["county", "year", YIELD_COL]])

combined = pd.concat(all_rows)
avg_yield = combined.groupby("county")[YIELD_COL].mean().reset_index()
avg_yield.columns = ["county", "avg_yield"]
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
avg_yield.to_csv(OUTPUT_CSV, index=False)

# ------------------ STEP 2: PLOT MAP ------------------
gdf = gpd.read_file(MAP_FILE)
gdf["county"] = gdf["NAME"].str.upper().str.replace(" ", "_")
gdf = gdf.merge(avg_yield, on="county", how="left")

fig, ax = plt.subplots(1, 1, figsize=(12, 8))

# Plot counties with average yield
gdf.plot(
    column="avg_yield",
    cmap="YlGnBu",
    legend=True,
    edgecolor="black",
    linewidth=0.6,
    ax=ax,
    missing_kwds={"color": "lightgrey", "label": "No Data"}
)

# Add basemap (terrain)
ctx.add_basemap(
    ax,
    crs=gdf.crs,
    source=ctx.providers.OpenStreetMap.Mapnik,
    alpha=0.7
)

# Styling
ax.set_title("Central Valley – Average Yield Across All Crops (2010–2024)", fontsize=16)
ax.axis("off")
plt.tight_layout()

os.makedirs(os.path.dirname(OUTPUT_PNG), exist_ok=True)
plt.savefig(OUTPUT_PNG, dpi=300)
plt.close()

print(f"Map saved to {OUTPUT_PNG}")