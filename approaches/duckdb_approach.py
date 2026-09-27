"""
DuckDB approach: let an embedded OLAP engine query the CSV directly
with SQL. DuckDB streams/spills to disk internally rather than
loading the whole file into a Python-visible structure.
"""
import duckdb

from .base import Approach


class DuckDBApproach(Approach):
    key = "duckdb"
    display_name = "duckdb_sql"

    def _aggregate(self, path: str) -> dict:
        con = duckdb.connect()
        try:
            # CREATE VIEW can't take a ? parameter, so escape any single
            # quotes in the path before putting it in the SQL string.
            safe_path = path.replace("'", "''")
            con.execute(f"CREATE VIEW tx AS SELECT * FROM read_csv_auto('{safe_path}')")

            total_revenue, total_orders = con.execute(
                "SELECT SUM(price * quantity), COUNT(*) FROM tx"
            ).fetchone()
            by_category = con.execute(
                "SELECT category, SUM(price * quantity) FROM tx GROUP BY category"
            ).fetchall()
            by_country = con.execute(
                "SELECT country, AVG(price * quantity) FROM tx GROUP BY country"
            ).fetchall()
        finally:
            con.close()

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "revenue_by_category": dict(by_category),
            "avg_order_value_by_country": dict(by_country),
        }
