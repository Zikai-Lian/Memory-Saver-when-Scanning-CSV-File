"""
Naive approach: load the entire CSV into a single pandas DataFrame,
then aggregate. This is the "obvious" way to do it, and the one that
falls over (or gets painfully slow / swaps) once the file no longer
fits comfortably in RAM.
"""
import argparse
import json

import pandas as pd


def run(path: str) -> dict:
    df = pd.read_csv(path)
    df["revenue"] = df["price"] * df["quantity"]

    by_category = (
        df.groupby("category")["revenue"]
        .agg(total_revenue="sum", orders="count")
        .sort_index()
    )
    by_country_avg = df.groupby("country")["revenue"].mean().sort_index()

    return {
        "total_revenue": round(float(df["revenue"].sum()), 2),
        "total_orders": int(len(df)),
        "revenue_by_category": {k: round(float(v), 2) for k, v in by_category["total_revenue"].items()},
        "avg_order_value_by_country": {k: round(float(v), 2) for k, v in by_country_avg.items()},
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()
    result = run(args.input)
    print("RESULT:" + json.dumps(result, sort_keys=True))
