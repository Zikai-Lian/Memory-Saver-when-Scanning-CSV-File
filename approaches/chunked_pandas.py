"""
Chunked pandas approach: read the CSV in fixed-size chunks
(pd.read_csv(..., chunksize=...)), aggregate each chunk, and combine
the partial results. Peak memory is bounded by chunk size instead of
total file size, at the cost of some extra bookkeeping code.
"""
import pandas as pd

from .base import Approach


class RunningGroupStats:
    """Running sum and count per group, merged one chunk at a time."""

    def __init__(self):
        self.sums = pd.Series(dtype="float64")
        self.counts = pd.Series(dtype="int64")

    def update(self, grouped) -> None:
        self.sums = self.sums.add(grouped.sum(), fill_value=0.0)
        self.counts = self.counts.add(grouped.count(), fill_value=0)

    def mean(self) -> pd.Series:
        return self.sums / self.counts


class ChunkedPandasApproach(Approach):
    key = "chunked_pandas"
    display_name = "chunked_pandas"

    def __init__(self, chunk_size: int = 500_000):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size

    def _aggregate(self, path: str) -> dict:
        by_category = RunningGroupStats()
        by_country = RunningGroupStats()
        total_revenue = 0.0
        total_orders = 0

        for chunk in pd.read_csv(path, chunksize=self.chunk_size):
            chunk["revenue"] = chunk["price"] * chunk["quantity"]
            by_category.update(chunk.groupby("category")["revenue"])
            by_country.update(chunk.groupby("country")["revenue"])
            total_revenue += chunk["revenue"].sum()
            total_orders += len(chunk)

        return {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "revenue_by_category": by_category.sums.to_dict(),
            "avg_order_value_by_country": by_country.mean().to_dict(),
        }

    def __repr__(self) -> str:
        return f"ChunkedPandasApproach(chunk_size={self.chunk_size})"
