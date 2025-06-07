import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Load NOAA API key
load_dotenv()
NOAA_TOKEN = os.getenv("NOAA_API_TOKEN")
HEADERS = {"token": NOAA_TOKEN}

# Central Valley counties with CA FIPS codes
CENTRAL_VALLEY_FIPS = {
    'Shasta': '067',
    'Tehama': '103',
    'Butte': '007',
    'Glenn': '021',
    'Yolo': '113',
    'Sutter': '101',
    'Colusa': '011',
    'San Joaquin': '077',
    'Stanislaus': '099',
    'Merced': '047',
    'Fresno': '019',
    'Kings': '031',
    'Kern': '029',
    'Tulare': '107',
    'Madera': '039'
}

BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations"

def fetch_stations_for_county(county, fips):
    """Fetch stations for a given county FIPS code."""
    location_id = f"FIPS:06{fips}"
    params = {
        "datasetid": "GHCND",
        "locationid": location_id,
        "limit": 1000,
        "sortfield": "maxdate",
        "sortorder": "desc"
    }
    try:
        logging.debug(f"Requesting stations for {county} (FIPS: {fips})")
        response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json().get("results", [])
        for station in data:
            station["county"] = county
        logging.info(f"✓ Retrieved {len(data)} stations for {county}")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"✗ Failed to fetch stations for {county}: {e}")
        return []

# Prepare output directory
output_dir = "data/raw/county_station_batches"
os.makedirs(output_dir, exist_ok=True)

# Loop through counties one at a time with delay
all_stations = []
for county, fips in CENTRAL_VALLEY_FIPS.items():
    stations = fetch_stations_for_county(county, fips)
    if stations:
        df = pd.json_normalize(stations)
        csv_path = os.path.join(output_dir, f"stations_{county.replace(' ', '_')}.csv")
        df.to_csv(csv_path, index=False)
        logging.debug(f"Saved {csv_path}")
        all_stations.extend(stations)
    time.sleep(1)  # 1 second delay to avoid rate limiting

# Save combined result
combined_df = pd.json_normalize(all_stations)
combined_path = "data/raw/cv_county_stations_all.csv"
combined_df.to_csv(combined_path, index=False)

combined_path, combined_df[["id", "name", "county", "latitude", "longitude", "mindate", "maxdate"]].head(15)