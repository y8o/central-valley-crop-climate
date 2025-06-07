import os
import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.impute import SimpleImputer

# ------------------ CONFIG ------------------
INPUT_DIR = "data/processed/by_crop"
OUTPUT_DIR = "results/yield_models"
YIELD_COL_NAME = "yield"

# ------------------ LOGGING ------------------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ------------------ UTILS ------------------
def plot_actual_vs_pred(y_true, y_pred, crop_name, out_path):
    plt.figure(figsize=(6, 6))
    sns.scatterplot(x=y_true, y=y_pred)
    plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], "--", color="red")
    plt.xlabel("Actual Yield")
    plt.ylabel("Predicted Yield")
    plt.title(f"{crop_name} – Actual vs Predicted Yield")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

def plot_feature_importance(model, feature_names, crop_name, out_path):
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    plt.figure(figsize=(8, 4))
    sns.barplot(x=importances[indices], y=np.array(feature_names)[indices])
    plt.title(f"{crop_name} – Feature Importance")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()

# ------------------ MODELING ------------------
def model_yield_per_crop():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".csv")]

    for file in files:
        crop_name = file.replace(".csv", "")
        path = os.path.join(INPUT_DIR, file)
        df = pd.read_csv(path)

        if YIELD_COL_NAME not in df.columns:
            logging.warning(f"No 'yield' column in {file}, skipping.")
            continue

        logging.info(f"Processing crop: {crop_name} – total rows: {len(df)}")

        df = df.dropna(subset=[YIELD_COL_NAME])
        if len(df) < 10:
            logging.warning(f"Not enough rows with yield: {crop_name}")
            continue

        feature_cols = [col for col in df.columns if col not in ["county", "year", "commodity", YIELD_COL_NAME] and df[col].dtype in [np.float64, np.int64]]

        # Drop features with too much missing data
        feature_cols = [col for col in feature_cols if df[col].isna().mean() < 0.5]
        if not feature_cols:
            logging.warning(f"No usable features left for {crop_name}")
            continue

        logging.info(f"{crop_name} – Using features: {feature_cols}")

        X = df[feature_cols]
        y = df[YIELD_COL_NAME]

        # Impute remaining missing values (mean imputation)
        imputer = SimpleImputer(strategy="mean")
        X_imputed = imputer.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(X_imputed, y, test_size=0.2, random_state=42)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)

        logging.info(f"{crop_name} – R²: {r2:.3f}, MAE: {mae:.2f}, rows modeled: {len(df)}")

        # Save metrics
        with open(os.path.join(OUTPUT_DIR, f"{crop_name}_metrics.txt"), "w") as f:
            f.write(f"R²: {r2:.4f}\n")
            f.write(f"MAE: {mae:.4f}\n")
            f.write(f"Rows: {len(df)}\n")
            f.write(f"Features used: {', '.join(feature_cols)}\n")

        # Save plots
        plot_actual_vs_pred(y_test, y_pred, crop_name, os.path.join(OUTPUT_DIR, f"{crop_name}_actual_vs_pred.png"))
        plot_feature_importance(model, feature_cols, crop_name, os.path.join(OUTPUT_DIR, f"{crop_name}_feature_importance.png"))

# ------------------ ENTRY ------------------
if __name__ == "__main__":
    model_yield_per_crop()