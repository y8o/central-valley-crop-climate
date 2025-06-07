import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------ CONFIG ------------------
CROP = "corn"  # set crop here
DATA_FILE = f"data/processed/by_crop/{CROP}.csv"
MAP_FILE = "data/raw/cv_county_boundaries.geojson"  # must match FIPS/names
OUTPUT_FILE = f"results/climate_trends/{CROP}_hot_year_yield_map.png"
TEMP_COL = "tmax_mean"
YIELD_COL = "yield"

# ------------------ LOAD ------------------
df = pd.read_csv(DATA_FILE)
df = df.dropna(subset=[YIELD_COL, TEMP_COL])

# Tag hot years
mean_temp = df[TEMP_COL].mean()
std_temp = df[TEMP_COL].std()
df["climate_band"] = df[TEMP_COL].apply(lambda t: "hot" if t > mean_temp + std_temp else "normal")

# Aggregate by county and climate band
grouped = df.groupby(["county", "climate_band"])[YIELD_COL].mean().unstack().reset_index()
grouped["yield_change_hot_minus_normal"] = grouped.get("hot", 0) - grouped.get("normal", 0)

# Load geo and merge
gdf = gpd.read_file(MAP_FILE)
gdf["county"] = gdf["NAME"].str.upper().str.replace(" ", "_")
merged = gdf.merge(grouped, on="county", how="left")

# Plot
fig, ax = plt.subplots(1, 1, figsize=(8, 6))
merged.plot(
    column="yield_change_hot_minus_normal",
    cmap="RdBu",
    legend=True,
    ax=ax,
    missing_kwds={"color": "lightgrey", "label": "No data"},
    edgecolor="black"
)
ax.set_title(f"{CROP.title()} – Yield Change (Hot vs Normal Years)")
plt.axis("off")
plt.tight_layout()
plt.savefig(OUTPUT_FILE)
plt.close()
print(f"Saved map to {OUTPUT_FILE}")