"""
Naive approach: load the entire CSV into a single pandas DataFrame,
then aggregate. This is the "obvious" way to do it, and the one that
falls over (or gets painfully slow / swaps) once the file no longer
fits comfortably in RAM.
"""
import pandas as pd

from .base import Approach


class NaivePandasApproach(Approach):
    key = "naive_pandas"
    display_name = "naive_pandas (load-all)"

    def _aggregate(self, path: str) -> dict:
        df = pd.read_csv(path)
        df["revenue"] = df["price"] * df["quantity"]

        return {
            "total_revenue": df["revenue"].sum(),
            "total_orders": len(df),
            "revenue_by_category": df.groupby("category")["revenue"].sum().to_dict(),
            "avg_order_value_by_country": df.groupby("country")["revenue"].mean().to_dict(),
        }
