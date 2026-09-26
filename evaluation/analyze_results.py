"""
Loads the most recent (or a specified) results JSONL and prints the
computed metrics table.
"""
import argparse
import glob
import os

import pandas as pd

from evaluation.metrics import load_jsonl, compute_metrics


def get_latest_results_file(results_dir: str = "results") -> str:
    files = glob.glob(os.path.join(results_dir, "experiment_*.jsonl"))
    if not files:
        raise FileNotFoundError(f"No experiment_*.jsonl files found in {results_dir}/")
    return max(files, key=os.path.getmtime)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None, help="Path to a specific results JSONL file")
    args = parser.parse_args()

    path = args.file or get_latest_results_file()
    print(f"Analyzing: {path}\n")

    entries = load_jsonl(path)
    df = compute_metrics(entries)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False))