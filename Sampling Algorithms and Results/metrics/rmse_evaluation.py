import os
import pandas as pd
import numpy as np

# =========================================================
# CONFIG
# =========================================================
RESULTS_CSV = "sampling_results.csv"   # risultati aggregati (per-run)
FULL_CSV = "scenario_metrics.csv"
OUTPUT_DIR = "rmse_results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# LOAD FULL DATASET
# =========================================================
def load_full_dataset(csv_path):
    df = pd.read_csv(csv_path)
    df["Outcome"] = df["collision_occurred"].astype(int)
    return df

# =========================================================
# TRUE PARAMETER
# =========================================================
def compute_true_accuracy(df):
    return 1.0 - df["Outcome"].mean()

# =========================================================
# RMSE
# =========================================================
def compute_rmse(estimates, true_value):
    estimates = np.asarray(estimates, dtype=float)
    return float(np.sqrt(np.mean((estimates - true_value) ** 2)))

# =========================================================
# MAIN RMSE EVALUATION
# =========================================================
def evaluate_rmse(results_csv, full_csv_path):
    # --- load ground truth ---
    full_df = load_full_dataset(full_csv_path)
    true_acc = compute_true_accuracy(full_df)

    # --- load per-run estimates ---
    res_df = pd.read_csv(results_csv)

    required_cols = {"method", "budget", "run", "accuracy"}
    if not required_cols.issubset(res_df.columns):
        raise ValueError(f"Results CSV must contain {required_cols}")

    rows = []

    for (method, budget), g in res_df.groupby(["method", "budget"]):
        if len(g) < 2:
            continue

        rmse_val = compute_rmse(g["accuracy"].values, true_acc)

        rows.append({
            "method": method,
            "budget": budget,
            "rmse": rmse_val,
            "runs": len(g),
            "mean_accuracy": g["accuracy"].mean()
        })

    return pd.DataFrame(rows).sort_values(["method", "budget"])

# =========================================================
# SCRIPT ENTRY POINT
# =========================================================
if __name__ == "__main__":
    rmse_df = evaluate_rmse(RESULTS_CSV, FULL_CSV)

    if rmse_df.empty:
        print("No valid RMSE results found.")
    else:
        output_path = os.path.join(OUTPUT_DIR, "rmse_summary.csv")
        rmse_df.to_csv(output_path, index=False)
        print(f"RMSE results saved to {output_path}")
