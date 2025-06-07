import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Load NOAA token from .env
load_dotenv()
NOAA_TOKEN = os.getenv("NOAA_API_TOKEN")
HEADERS = {"token": NOAA_TOKEN}

# Constants
BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
START_YEAR = 2010
END_YEAR = 2024
DATA_VARS = ["TMAX", "TMIN", "PRCP"]
ROOT_OUTPUT_DIR = "data/raw/climate_noaa"
STATION_MAP_PATH = "data/raw/county_station_map_2.csv"

# Read validated station map (ensure your header matches this exactly)
station_map = pd.read_csv(STATION_MAP_PATH)

def fetch_daily_data(station_id, year):
    """Fetch NOAA daily data for a station and year."""
    logging.info(f"Fetching {year} data for {station_id}")
    all_data = []
    offset = 1

    while True:
        params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": f"{year}-01-01",
            "enddate": f"{year}-12-31",
            "datatypeid": DATA_VARS,
            "limit": 1000,
            "offset": offset,
            "units": "metric",
            "format": "json"
        }
        try:
            response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            page = response.json().get("results", [])
            if not page:
                break
            all_data.extend(page)
            if len(page) < 1000:
                break
            offset += 1000
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch {year} for {station_id}: {e}")
            return None

    if not all_data:
        return None

    df = pd.DataFrame(all_data)
    df = df.pivot(index="date", columns="datatype", values="value").reset_index()
    df["station"] = station_id
    df["year"] = year
    return df

# Main loop
for _, row in station_map.iterrows():
    county = row["county"].strip().replace(" ", "_")
    station_id = row["station_id"]

    county_dir = os.path.join(ROOT_OUTPUT_DIR, county)
    os.makedirs(county_dir, exist_ok=True)

    for year in range(START_YEAR, END_YEAR + 1):
        filename = f"{county}_{year}.csv"
        output_path = os.path.join(county_dir, filename)

        if os.path.exists(output_path):
            logging.info(f"✓ Already exists: {output_path}")
            continue

        df = fetch_daily_data(station_id, year)
        if df is not None:
            df.to_csv(output_path, index=False)
            logging.info(f"✔ Saved: {output_path}")
        else:
            logging.warning(f"⚠ No data for {county} in {year}")
        time.sleep(1)

logging.info("🎉 Finished downloading all NOAA daily climate data.")