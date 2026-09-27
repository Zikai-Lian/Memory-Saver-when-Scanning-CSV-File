"""
Polars lazy/streaming approach: build a lazy query plan with
scan_csv (which never materializes the whole file up front) and let
Polars' streaming engine execute it in batches under the hood.
"""
import polars as pl

from .base import Approach


class PolarsLazyApproach(Approach):
    key = "polars_lazy"
    display_name = "polars_lazy_streaming"

    @staticmethod
    def _collect(lazy_frame: pl.LazyFrame) -> pl.DataFrame:
        try:
            return lazy_frame.collect(engine="streaming")
        except TypeError:  # older polars versions
            return lazy_frame.collect(streaming=True)

    def _aggregate(self, path: str) -> dict:
        lf = pl.scan_csv(path).with_columns(
            (pl.col("price") * pl.col("quantity")).alias("revenue")
        )

        by_category = self._collect(
            lf.group_by("category").agg(total_revenue=pl.col("revenue").sum())
        )
        by_country = self._collect(
            lf.group_by("country").agg(avg_order_value=pl.col("revenue").mean())
        )
        totals = self._collect(
            lf.select(total_revenue=pl.col("revenue").sum(), total_orders=pl.len())
        )

        return {
            "total_revenue": totals["total_revenue"][0],
            "total_orders": totals["total_orders"][0],
            "revenue_by_category": dict(zip(by_category["category"], by_category["total_revenue"])),
            "avg_order_value_by_country": dict(zip(by_country["country"], by_country["avg_order_value"])),
        }
