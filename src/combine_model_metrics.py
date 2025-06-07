import os
import re
import pandas as pd

INPUT_DIR = "results/yield_models"
OUTPUT_FILE = "results/model_results.csv"

rows = []
for file in os.listdir(INPUT_DIR):
    if not file.endswith("_metrics.txt"):
        continue
    crop = file.replace("_metrics.txt", "")
    path = os.path.join(INPUT_DIR, file)

    with open(path, "r") as f:
        content = f.read()
        r2_match = re.search(r"R²:\s*([0-9\.\-]+)", content)
        mae_match = re.search(r"MAE:\s*([0-9\.\-]+)", content)
        features_match = re.search(r"Features.?:\s(.*)", content)

        rows.append({
            "crop": crop,
            "r2": float(r2_match.group(1)) if r2_match else None,
            "mae": float(mae_match.group(1)) if mae_match else None,
            "features": features_match.group(1) if features_match else ""
        })

df = pd.DataFrame(rows)
df.to_csv(OUTPUT_FILE, index=False)
print(f"✔ Combined results written to {OUTPUT_FILE}")