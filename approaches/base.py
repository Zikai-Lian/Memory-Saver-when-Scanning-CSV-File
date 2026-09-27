"""
Shared building blocks for every aggregation approach.

- AggregationResult: the value object every approach returns, so results
  can be compared with a plain ==.
- Approach: abstract base class. Subclasses implement _aggregate(); the
  public run() method is the same for all of them (template method pattern)
  and takes care of rounding and packaging the result.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Mapping


def _round_map(values: Mapping[str, float]) -> dict[str, float]:
    """Round every value to cents and sort by key so output is deterministic."""
    return {str(k): round(float(v), 2) for k, v in sorted(values.items())}


@dataclass(frozen=True)
class AggregationResult:
    """The answer to the benchmark query. Two approaches agree iff their results are ==."""

    total_revenue: float
    total_orders: int
    revenue_by_category: dict[str, float] = field(default_factory=dict)
    avg_order_value_by_country: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_raw(
        cls,
        total_revenue: float,
        total_orders: int,
        revenue_by_category: Mapping[str, float],
        avg_order_value_by_country: Mapping[str, float],
    ) -> "AggregationResult":
        """Build a result from unrounded engine output (numpy/pandas scalars are fine)."""
        return cls(
            total_revenue=round(float(total_revenue), 2),
            total_orders=int(total_orders),
            revenue_by_category=_round_map(revenue_by_category),
            avg_order_value_by_country=_round_map(avg_order_value_by_country),
        )

    @classmethod
    def from_dict(cls, data: Mapping) -> "AggregationResult":
        return cls(
            total_revenue=data["total_revenue"],
            total_orders=data["total_orders"],
            revenue_by_category=dict(data["revenue_by_category"]),
            avg_order_value_by_country=dict(data["avg_order_value_by_country"]),
        )

    def to_dict(self) -> dict:
        return asdict(self)


class Approach(ABC):
    """One way of answering the benchmark query over a CSV file."""

    #: short id used on the command line, e.g. "duckdb"
    key: str = ""
    #: label used in the results CSV and chart
    display_name: str = ""

    def run(self, path: str) -> AggregationResult:
        """Run the query on the CSV at `path`. Same for every subclass."""
        return AggregationResult.from_raw(**self._aggregate(path))

    @abstractmethod
    def _aggregate(self, path: str) -> dict:
        """
        Compute the query and return a dict with the keys
        total_revenue, total_orders, revenue_by_category,
        avg_order_value_by_country (values may be unrounded).
        """

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"
