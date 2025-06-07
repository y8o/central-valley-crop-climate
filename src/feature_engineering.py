import os
import pandas as pd
import numpy as np
from glob import glob
from collections import defaultdict
from sklearn.impute import KNNImputer
import logging

# -------------------- CONFIG --------------------
INPUT_DIR = "data/raw/climate_noaa"
OUTPUT_DIR = "data/processed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "climate_features_2010_2024.csv")
YEARS = list(range(2010, 2025))
VARIABLES = ["TMAX", "TMIN", "PRCP"]

# -------------------- LOGGING --------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# -------------------- STEP 1: Aggregate Daily to Annual --------------------
def summarize_annual_climate():
    summary_rows = []
    missing_log = defaultdict(list)

    county_dirs = sorted(glob(os.path.join(INPUT_DIR, "*")))
    for county_dir in county_dirs:
        county = os.path.basename(county_dir)
        for year in YEARS:
            file_path = os.path.join(county_dir, f"{county}_{year}.csv")
            if not os.path.exists(file_path):
                logging.warning(f"Missing file: {county} {year}")
                missing_log[county].append(year)
                summary_rows.append({
                    "county": county,
                    "year": year,
                    "tmax_mean": np.nan,
                    "tmin_mean": np.nan,
                    "prcp_total": np.nan
                })
                continue

            try:
                df = pd.read_csv(file_path)
                summary_rows.append({
                    "county": county,
                    "year": year,
                    "tmax_mean": df["TMAX"].mean() if "TMAX" in df.columns else np.nan,
                    "tmin_mean": df["TMIN"].mean() if "TMIN" in df.columns else np.nan,
                    "prcp_total": df["PRCP"].sum() if "PRCP" in df.columns else np.nan
                })
            except Exception as e:
                logging.error(f"Error reading {file_path}: {e}")
                missing_log[county].append(year)
                summary_rows.append({
                    "county": county,
                    "year": year,
                    "tmax_mean": np.nan,
                    "tmin_mean": np.nan,
                    "prcp_total": np.nan
                })

    return pd.DataFrame(summary_rows), missing_log

# -------------------- STEP 2: KNN Impute Missing --------------------
def impute_climate_data(df):
    pivoted = df.pivot(index="year", columns="county", values=["tmax_mean", "tmin_mean", "prcp_total"])
    
    # Flatten multi-index columns
    flat = pivoted.copy()
    flat.columns = [f"{metric}_{county}" for metric, county in flat.columns]
    
    # Drop all-NaN columns (KNNImputer cannot handle them)
    non_nan_columns = flat.columns[flat.notna().any()]
    flat_reduced = flat[non_nan_columns]

    # Impute
    imputer = KNNImputer(n_neighbors=3)
    imputed_array = imputer.fit_transform(flat_reduced)
    imputed_df = pd.DataFrame(imputed_array, columns=non_nan_columns, index=flat.index)

    # Reinsert all-NaN columns as NaN
    for col in flat.columns:
        if col not in imputed_df.columns:
            imputed_df[col] = np.nan

    # Restore column order
    imputed_df = imputed_df[flat.columns].reset_index()

    # Melt and unstack
    melted = imputed_df.melt(id_vars=["year"], var_name="metric_county", value_name="value")
    melted[["metric", "county"]] = melted["metric_county"].str.extract(r"(\w+)_(.+)")
    final_df = melted.drop(columns="metric_county").pivot_table(
        index=["county", "year"],
        columns="metric",
        values="value"
    ).reset_index()

    return final_df

# -------------------- MAIN --------------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_summary, missing_log = summarize_annual_climate()

    logging.info(f"Total summary rows: {len(df_summary)}")
    logging.info(f"Missing data summary:")
    for county, years in missing_log.items():
        logging.info(f"  {county}: missing {len(years)} years")

    df_imputed = impute_climate_data(df_summary)
    df_imputed.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"✔ Saved output to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()