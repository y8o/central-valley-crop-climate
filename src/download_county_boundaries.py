import os
import geopandas as gpd

# ------------------ CONFIG ------------------
INPUT_FOLDER = "data/raw/us_counties"
OUTPUT_FILE = "data/raw/cv_county_boundaries.geojson"

# These must match the NAME field exactly (uppercase is safest)
CV_COUNTIES = [
    "SHASTA", "TEHAMA", "BUTTE", "GLENN", "YOLO", "SUTTER", "COLUSA",
    "SAN JOAQUIN", "STANISLAUS", "MERCED", "FRESNO", "KINGS", "KERN",
    "TULARE", "MADERA"
]

# ------------------ LOAD AND FILTER ------------------
# Find the .shp file inside the folder
shp_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".shp")]
assert len(shp_files) == 1, "Expected exactly one .shp file in folder"
shp_path = os.path.join(INPUT_FOLDER, shp_files[0])

# Load counties shapefile
gdf = gpd.read_file(shp_path)

# Filter for California (STATEFP 06)
gdf_ca = gdf[gdf["STATEFP"] == "06"]

# Filter for CV counties
gdf_cv = gdf_ca[gdf_ca["NAME"].str.upper().isin(CV_COUNTIES)]

# Save as GeoJSON
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
gdf_cv.to_file(OUTPUT_FILE, driver="GeoJSON")
print(f"✔ Saved filtered CV counties to {OUTPUT_FILE}")