"""
Benchmark driver: runs each approach against the same dataset (each in
its own fresh, isolated process), records wall time and peak RSS,
verifies all approaches agree on the result, and writes a results CSV.

Usage:
    python benchmark.py --input data/transactions.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

from approaches import APPROACH_KEYS, AggregationResult, get_approach_class
from measurement import IsolatedRunner, Measurement


@dataclass
class BenchmarkRow:
    """One line of the results CSV."""

    approach: str
    wall_time_s: float
    peak_rss_mb: float
    total_revenue: float
    total_orders: int
    correctness: str

    FIELDS = ("approach", "wall_time_s", "peak_rss_mb", "total_revenue", "total_orders", "correctness")


class Benchmark:
    """Runs every approach on one input file and checks they all agree."""

    def __init__(self, input_path: str, approach_keys: list[str] = APPROACH_KEYS,
                 runner: Optional[IsolatedRunner] = None):
        self.input_path = input_path
        self.approach_keys = approach_keys
        self.runner = runner or IsolatedRunner()
        self.reference: Optional[AggregationResult] = None
        self.rows: list[BenchmarkRow] = []

    def _check(self, result: AggregationResult) -> str:
        """The first successful result is the reference; later ones must match it exactly."""
        if self.reference is None:
            self.reference = result
            return "reference"
        return "MATCH" if result == self.reference else "MISMATCH"

    def run(self) -> list[BenchmarkRow]:
        for key in self.approach_keys:
            name = get_approach_class(key).display_name
            print(f"Running: {name} ...", flush=True)
            m: Measurement = self.runner.measure(key, self.input_path)
            if not m.succeeded:
                print(f"  FAILED: {m.stderr_tail}", file=sys.stderr)
                continue

            correctness = self._check(m.result)
            print(f"  wall_time={m.wall_time_s:.2f}s  peak_rss={m.peak_rss_mb:.1f}MB  "
                  f"correctness={correctness}", flush=True)
            self.rows.append(BenchmarkRow(
                approach=name,
                wall_time_s=m.wall_time_s,
                peak_rss_mb=m.peak_rss_mb,
                total_revenue=m.result.total_revenue,
                total_orders=m.result.total_orders,
                correctness=correctness,
            ))
        return self.rows

    @property
    def all_match(self) -> bool:
        return all(r.correctness != "MISMATCH" for r in self.rows)

    def write_csv(self, out_path: str) -> Path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=BenchmarkRow.FIELDS)
            writer.writeheader()
            for row in self.rows:
                writer.writerow(asdict(row))
        return path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/transactions.csv")
    ap.add_argument("--out", default="results/benchmark_results.csv")
    args = ap.parse_args()

    bench = Benchmark(args.input)
    bench.run()
    path = bench.write_csv(args.out)
    print(f"\nResults written to {path}")
    if not bench.all_match:
        sys.exit("At least one approach disagreed with the reference result.")


if __name__ == "__main__":
    main()
