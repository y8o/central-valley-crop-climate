# src/data_collection.py

import os
import pandas as pd
import requests
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()
API_KEY = os.getenv("USDA_API_KEY")

# Central Valley county names
CENTRAL_VALLEY_COUNTIES = [
    'Shasta', 'Tehama', 'Butte', 'Glenn', 'Yolo', 'Sutter', 'Colusa',
    'San Joaquin', 'Stanislaus', 'Merced', 'Fresno', 'Kings', 'Kern',
    'Tulare', 'Madera'
]

def fetch_all_crop_data(year_start=2010, year_end=2024):
    """Fetch all crop-related statistics from USDA NASS for Central Valley counties."""
    base_url = "https://quickstats.nass.usda.gov/api/api_GET/"
    all_records = []

    for county in CENTRAL_VALLEY_COUNTIES:
        logging.info(f"Fetching data for {county}...")
        params = {
            'key': API_KEY,
            'source_desc': 'SURVEY',
            'sector_desc': 'CROPS',
            'agg_level_desc': 'COUNTY',
            'state_alpha': 'CA',
            'county_name': county,
            'year__GE': str(year_start),
            'year__LE': str(year_end),
            'format': 'JSON'
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json().get("data", [])
            if data:
                all_records.extend(data)
                logging.info(f"✓ Retrieved {len(data)} records from {county}")
            else:
                logging.warning(f"No records found for {county}")
        except requests.exceptions.HTTPError as err:
            logging.error(f"HTTP error for {county}: {err}")
        except Exception as e:
            logging.error(f"General error for {county}: {e}")

    if not all_records:
        logging.error("No data collected from any county.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    keep_cols = [
        'year', 'state_name', 'county_name', 'county_ansi', 'commodity_desc',
        'short_desc', 'statisticcat_desc', 'domain_desc', 'Value', 'unit_desc'
    ]
    df = df[keep_cols]
    df.columns = [
        'year', 'state', 'county', 'county_fips', 'commodity',
        'description', 'statistic', 'domain', 'value', 'unit'
    ]
    df['year'] = df['year'].astype(int)
    df['value'] = pd.to_numeric(df['value'].str.replace(",", ""), errors='coerce')
    df['county_fips'] = df['county_fips'].astype(str).str.zfill(3)
    df = df.dropna(subset=["value"])
    return df

if __name__ == "__main__":
    try:
        os.makedirs("data/raw", exist_ok=True)
        df = fetch_all_crop_data()
        if not df.empty:
            output_path = "data/raw/usda_central_valley_all_ag_data_2010_2024.csv"
            df.to_csv(output_path, index=False)
            logging.info(f"✔ Saved data to {output_path}")
        else:
            logging.warning("⚠ No data to save.")
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")