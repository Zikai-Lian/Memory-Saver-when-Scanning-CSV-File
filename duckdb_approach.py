"""
DuckDB approach: let an embedded OLAP engine query the CSV directly
with SQL. DuckDB streams/spills to disk internally rather than
loading the whole file into a Python-visible structure.
"""
import argparse
import json

import duckdb


def run(path: str) -> dict:
    con = duckdb.connect()
    con.execute(f"CREATE VIEW tx AS SELECT * FROM read_csv_auto('{path}')")

    totals = con.execute(
        "SELECT SUM(price * quantity) AS total_revenue, COUNT(*) AS total_orders FROM tx"
    ).fetchone()

    by_category = con.execute(
        """
        SELECT category, SUM(price * quantity) AS total_revenue
        FROM tx GROUP BY category ORDER BY category
        """
    ).fetchall()

    by_country = con.execute(
        """
        SELECT country, AVG(price * quantity) AS avg_order_value
        FROM tx GROUP BY country ORDER BY country
        """
    ).fetchall()

    return {
        "total_revenue": round(float(totals[0]), 2),
        "total_orders": int(totals[1]),
        "revenue_by_category": {row[0]: round(float(row[1]), 2) for row in by_category},
        "avg_order_value_by_country": {row[0]: round(float(row[1]), 2) for row in by_country},
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()
    result = run(args.input)
    print("RESULT:" + json.dumps(result, sort_keys=True))
