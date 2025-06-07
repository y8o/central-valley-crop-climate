import os
import pandas as pd
import logging

# ------------------ CONFIG ------------------
USDA_FILE = "data/raw/usda_central_valley_all_ag_data_2010_2024.csv"
CLIMATE_FILE = "data/processed/climate_features_2010_2024.csv"
OUTPUT_DIR = "data/processed/by_crop"

# ------------------ LOGGING ------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ------------------ LOAD & CLEAN USDA ------------------
def load_usda():
    logging.info(f"Reading USDA data from: {USDA_FILE}")
    df = pd.read_csv(USDA_FILE)
    df.columns = df.columns.str.lower().str.strip()

    df["year"] = df["year"].astype(int)
    df["county"] = df["county"].str.strip().str.upper().str.replace(" ", "_")
    df["commodity"] = df["commodity"].str.upper().str.strip()
    df["statistic"] = df["statistic"].str.upper().str.strip()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")  # <-- FIXED
    logging.info(f"Loaded USDA rows: {len(df)}")
    return df

# ------------------ LOAD CLIMATE ------------------
def load_climate():
    logging.info(f"Reading climate data from: {CLIMATE_FILE}")
    df = pd.read_csv(CLIMATE_FILE)
    df["county"] = df["county"].str.upper().str.replace(" ", "_")
    logging.info(f"Loaded climate rows: {len(df)}")
    return df

# ------------------ MAIN ROUTINE ------------------
def build_crop_datasets(usda_df, climate_df):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    crop_list = usda_df["commodity"].unique()
    logging.info(f"Detected {len(crop_list)} crops")

    for crop in crop_list:
        logging.info(f"Processing: {crop}")
        df_crop = usda_df[usda_df["commodity"] == crop].copy()
        if df_crop.empty:
            logging.warning(f"No data for {crop}")
            continue

        df_pivot = df_crop.pivot_table(
            index=["county", "year"],
            columns="statistic",
            values="value"
        ).reset_index()

        df_pivot.columns = [col.lower().replace(" ", "").replace("/", "_per") for col in df_pivot.columns]
        df_pivot["commodity"] = crop

        merged = pd.merge(climate_df, df_pivot, on=["county", "year"], how="inner")
        output_file = os.path.join(OUTPUT_DIR, f"{crop.lower().replace(',', '').replace(' ', '_')}.csv")
        merged.to_csv(output_file, index=False)
        logging.info(f"✔ Saved {output_file} with {len(merged)} rows")

def main():
    logging.info("🚀 Starting crop-specific dataset builder...")
    usda = load_usda()
    climate = load_climate()
    build_crop_datasets(usda, climate)
    logging.info("🎉 Done creating per-crop datasets.")

# ------------------ ENTRY ------------------
if __name__ == "__main__":
    main()