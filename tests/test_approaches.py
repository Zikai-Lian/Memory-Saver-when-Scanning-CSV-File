"""
Unit tests. Run with:  python -m pytest

They use a small generated CSV, so they finish in a few seconds.
"""
import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from approaches import APPROACH_KEYS, AggregationResult, Approach, get_approach  # noqa: E402
from approaches.chunked_pandas import ChunkedPandasApproach  # noqa: E402
from benchmark import Benchmark  # noqa: E402
from generate_data import TransactionDataGenerator  # noqa: E402
from measurement import Measurement  # noqa: E402


@pytest.fixture(scope="session")
def small_csv(tmp_path_factory) -> str:
    path = tmp_path_factory.mktemp("data") / "tx.csv"
    TransactionDataGenerator(chunk_size=7_000, seed=1).write(20_000, str(path))
    return str(path)


@pytest.fixture
def tiny_csv(tmp_path) -> str:
    """Hand-written data where the right answer is easy to work out."""
    path = tmp_path / "tiny.csv"
    rows = [
        # order_id, user_id, product_id, category, price, quantity, country, timestamp
        (1, 1, 1, "books", 10.0, 2, "US", "2024-01-01T00:00:00"),  # revenue 20
        (2, 1, 2, "books", 5.0, 1, "CA", "2024-01-01T00:00:00"),   # revenue 5
        (3, 2, 3, "toys", 3.0, 3, "US", "2024-01-01T00:00:00"),    # revenue 9
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(TransactionDataGenerator.HEADER)
        writer.writerows(rows)
    return str(path)


EXPECTED_TINY = AggregationResult(
    total_revenue=34.0,
    total_orders=3,
    revenue_by_category={"books": 25.0, "toys": 9.0},
    avg_order_value_by_country={"CA": 5.0, "US": 14.5},
)


@pytest.mark.parametrize("key", APPROACH_KEYS)
def test_each_approach_gets_the_known_answer(key, tiny_csv):
    assert get_approach(key).run(tiny_csv) == EXPECTED_TINY


def test_all_approaches_agree_on_generated_data(small_csv):
    results = [get_approach(key).run(small_csv) for key in APPROACH_KEYS]
    assert all(r == results[0] for r in results)
    assert results[0].total_orders == 20_000


def test_chunk_size_does_not_change_the_answer(small_csv):
    expected = ChunkedPandasApproach(chunk_size=500_000).run(small_csv)
    assert ChunkedPandasApproach(chunk_size=3_333).run(small_csv) == expected


def test_chunk_size_must_be_positive():
    with pytest.raises(ValueError):
        ChunkedPandasApproach(chunk_size=0)


def test_every_approach_is_an_approach():
    for key in APPROACH_KEYS:
        approach = get_approach(key)
        assert isinstance(approach, Approach)
        assert approach.key == key and approach.display_name


def test_unknown_approach_is_rejected():
    with pytest.raises(ValueError, match="Unknown approach"):
        get_approach("excel")


def test_approach_base_class_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Approach()


def test_result_round_trips_through_dict():
    assert AggregationResult.from_dict(EXPECTED_TINY.to_dict()) == EXPECTED_TINY


def test_measurement_round_trips_through_json():
    m = Measurement(wall_time_s=1.5, peak_rss_mb=200.0, returncode=0, result=EXPECTED_TINY)
    assert Measurement.from_json(m.to_json()) == m
    assert m.succeeded


def test_benchmark_flags_a_mismatch(tiny_csv):
    """A fake runner lets us test the correctness check without spawning processes."""
    wrong = AggregationResult(total_revenue=0.0, total_orders=3)

    class FakeRunner:
        def __init__(self):
            self.results = iter([EXPECTED_TINY, EXPECTED_TINY, wrong])

        def measure(self, key, path):
            return Measurement(wall_time_s=0.1, peak_rss_mb=10.0, returncode=0, result=next(self.results))

    bench = Benchmark(tiny_csv, approach_keys=["naive_pandas", "chunked_pandas", "duckdb"],
                      runner=FakeRunner())
    rows = bench.run()
    assert [r.correctness for r in rows] == ["reference", "MATCH", "MISMATCH"]
    assert not bench.all_match
