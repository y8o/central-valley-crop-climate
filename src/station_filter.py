import os
import pandas as pd
import glob

# Directory where the individual county station CSVs are stored
input_dir = "data/raw/county_station_batches"
output_path = "data/raw/county_station_map.csv"

# Criteria for preferred station types (more reliable sources)
PREFERRED_PREFIXES = ("USC", "USW")

# Initialize results
selected_stations = []

# Loop through each county's station file
for file in glob.glob(os.path.join(input_dir, "stations_*.csv")):
    df = pd.read_csv(file)
    county = os.path.basename(file).replace("stations_", "").replace(".csv", "").replace("_", " ")

    if df.empty:
        continue

    # Filter for stations that started on or before 2010 and are active at least through 2024
    df["mindate"] = pd.to_datetime(df["mindate"], errors="coerce")
    df["maxdate"] = pd.to_datetime(df["maxdate"], errors="coerce")
    df_filtered = df[
        (df["mindate"] <= "2010-01-01") &
        (df["maxdate"] >= "2024-01-01")
    ].copy()

    # Prefer USC/USW stations
    df_filtered["is_preferred"] = df_filtered["id"].str.contains("|".join(PREFERRED_PREFIXES))

    # Sort by preference and longest coverage period
    df_filtered["coverage_years"] = (df_filtered["maxdate"] - df_filtered["mindate"]).dt.days / 365.25
    df_filtered = df_filtered.sort_values(
        by=["is_preferred", "coverage_years"],
        ascending=[False, False]
    )

    if not df_filtered.empty:
        best_station = df_filtered.iloc[0]
        selected_stations.append({
            "county": county,
            "station_id": best_station["id"],
            "name": best_station["name"],
            "mindate": best_station["mindate"].date(),
            "maxdate": best_station["maxdate"].date(),
            "latitude": best_station["latitude"],
            "longitude": best_station["longitude"],
            "elevation": best_station.get("elevation", None),
        })

# Save to CSV
df_selected = pd.DataFrame(selected_stations)
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_selected.to_csv(output_path, index=False)

output_path, df_selected.head(15)