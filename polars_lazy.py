"""
Polars lazy/streaming approach: build a lazy query plan with
scan_csv (which never materializes the whole file up front) and let
Polars' streaming engine execute it in batches under the hood.
"""
import argparse
import json

import polars as pl


def run(path: str) -> dict:
    lf = pl.scan_csv(path).with_columns(
        (pl.col("price") * pl.col("quantity")).alias("revenue")
    )

    by_category = (
        lf.group_by("category")
        .agg(total_revenue=pl.col("revenue").sum(), orders=pl.len())
        .sort("category")
    )
    by_country = (
        lf.group_by("country")
        .agg(avg_order_value=pl.col("revenue").mean())
        .sort("country")
    )
    totals = lf.select(
        total_revenue=pl.col("revenue").sum(),
        total_orders=pl.len(),
    )

    try:
        cat_df = by_category.collect(engine="streaming")
        cty_df = by_country.collect(engine="streaming")
        tot_df = totals.collect(engine="streaming")
    except TypeError:
        # older/newer polars API fallback
        cat_df = by_category.collect(streaming=True)
        cty_df = by_country.collect(streaming=True)
        tot_df = totals.collect(streaming=True)

    return {
        "total_revenue": round(float(tot_df["total_revenue"][0]), 2),
        "total_orders": int(tot_df["total_orders"][0]),
        "revenue_by_category": {
            row["category"]: round(float(row["total_revenue"]), 2) for row in cat_df.to_dicts()
        },
        "avg_order_value_by_country": {
            row["country"]: round(float(row["avg_order_value"]), 2) for row in cty_df.to_dicts()
        },
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()
    result = run(args.input)
    print("RESULT:" + json.dumps(result, sort_keys=True))
