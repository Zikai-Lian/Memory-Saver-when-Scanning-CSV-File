"""
All aggregation approaches, plus a registry to look them up by key.

The registry imports each approach's module only when it's asked for.
That matters for the benchmark: the process running DuckDB shouldn't also
have pandas and Polars loaded, or its peak-memory number would include
libraries it never used.
"""
from importlib import import_module

from .base import AggregationResult, Approach

# key -> (module, class name). Order matters: the first one is the
# correctness reference the others are checked against.
_REGISTRY = {
    "naive_pandas": ("approaches.naive_pandas", "NaivePandasApproach"),
    "chunked_pandas": ("approaches.chunked_pandas", "ChunkedPandasApproach"),
    "polars_lazy": ("approaches.polars_lazy", "PolarsLazyApproach"),
    "duckdb": ("approaches.duckdb_approach", "DuckDBApproach"),
}

APPROACH_KEYS = list(_REGISTRY)


def get_approach_class(key: str) -> type[Approach]:
    try:
        module_name, class_name = _REGISTRY[key]
    except KeyError:
        raise ValueError(f"Unknown approach {key!r}. Choose from: {', '.join(_REGISTRY)}") from None
    return getattr(import_module(module_name), class_name)


def get_approach(key: str, **kwargs) -> Approach:
    """Create an approach by key, e.g. get_approach("chunked_pandas", chunk_size=100_000)."""
    return get_approach_class(key)(**kwargs)


__all__ = ["AggregationResult", "Approach", "APPROACH_KEYS", "get_approach", "get_approach_class"]
