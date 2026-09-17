"""
Chunked pandas approach: read the CSV in fixed-size chunks
(pd.read_csv(..., chunksize=...)), aggregate each chunk, and combine
the partial results. Peak memory is bounded by chunk size instead of
total file size, at the cost of some extra bookkeeping code.
"""
import argparse
import json

import pandas as pd


def run(path: str, chunk_size: int = 500_000) -> dict:
    category_sum = pd.Series(dtype="float64")
    category_count = pd.Series(dtype="int64")
    country_sum = pd.Series(dtype="float64")
    country_count = pd.Series(dtype="int64")
    total_revenue = 0.0
    total_orders = 0

    for chunk in pd.read_csv(path, chunksize=chunk_size):
        chunk["revenue"] = chunk["price"] * chunk["quantity"]

        cat_grp = chunk.groupby("category")["revenue"]
        category_sum = category_sum.add(cat_grp.sum(), fill_value=0.0)
        category_count = category_count.add(cat_grp.count(), fill_value=0)

        cty_grp = chunk.groupby("country")["revenue"]
        country_sum = country_sum.add(cty_grp.sum(), fill_value=0.0)
        country_count = country_count.add(cty_grp.count(), fill_value=0)

        total_revenue += chunk["revenue"].sum()
        total_orders += len(chunk)

    avg_order_value_by_country = (country_sum / country_count).sort_index()

    return {
        "total_revenue": round(float(total_revenue), 2),
        "total_orders": int(total_orders),
        "revenue_by_category": {k: round(float(v), 2) for k, v in category_sum.sort_index().items()},
        "avg_order_value_by_country": {k: round(float(v), 2) for k, v in avg_order_value_by_country.items()},
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--chunk-size", type=int, default=500_000)
    args = ap.parse_args()
    result = run(args.input, args.chunk_size)
    print("RESULT:" + json.dumps(result, sort_keys=True))
