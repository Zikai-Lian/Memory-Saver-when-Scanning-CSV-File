"""
Generates a large synthetic e-commerce transactions CSV for the
out-of-core benchmark. Written in chunks with numpy vectorized calls
so *generating* the data never itself requires holding the whole
dataset in memory (that would defeat the point of the demo).

Usage:
    python3 generate_data.py --rows 15000000 --out data/transactions.csv
"""
from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path

import numpy as np


class TransactionDataGenerator:
    CATEGORIES = [
        "electronics", "home_kitchen", "books", "toys", "clothing",
        "sports", "beauty", "grocery", "automotive", "garden",
        "office", "pet_supplies", "music", "movies", "jewelry",
        "shoes", "baby", "tools", "health", "furniture",
    ]
    COUNTRIES = [
        "US", "CA", "GB", "DE", "FR", "IN", "BR", "AU", "JP", "MX",
        "IT", "ES", "NL", "SE", "KR",
    ]
    HEADER = ["order_id", "user_id", "product_id", "category",
              "price", "quantity", "country", "timestamp"]
    START = np.datetime64("2024-01-01T00:00:00")
    SPAN_SECONDS = 2 * 365 * 24 * 3600  # two years

    def __init__(self, chunk_size: int = 1_000_000, seed: int = 42):
        self.chunk_size = chunk_size
        self.rng = np.random.default_rng(seed)

    def _make_chunk(self, first_id: int, n: int):
        """Return an iterator of n rows, all built with vectorized numpy calls."""
        rng = self.rng
        # Draw columns in this exact order so a given seed reproduces the
        # same dataset as the original script (the published results).
        user_ids = rng.integers(1, 2_000_000, size=n)
        product_ids = rng.integers(1, 50_000, size=n)
        categories = rng.choice(self.CATEGORIES, size=n)
        # right-skewed price distribution (lognormal), clipped
        prices = np.round(np.clip(rng.lognormal(mean=3.0, sigma=0.9, size=n), 1.0, 2000.0), 2)
        quantities = rng.integers(1, 10, size=n)
        countries = rng.choice(self.COUNTRIES, size=n)
        offsets = rng.integers(0, self.SPAN_SECONDS, size=n)
        timestamps = self.START + offsets.astype("timedelta64[s]")
        order_ids = np.arange(first_id, first_id + n)
        return zip(order_ids, user_ids, product_ids, categories,
                   prices, quantities, countries, timestamps.astype(str))

    def write(self, rows: int, out_path: str) -> None:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        written = 0
        t0 = time.perf_counter()
        with open(out_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADER)
            while written < rows:
                n = min(self.chunk_size, rows - written)
                writer.writerows(self._make_chunk(written, n))
                written += n
                print(f"  wrote {written:,} / {rows:,} rows ({time.perf_counter() - t0:.1f}s elapsed)", flush=True)
        print(f"Done. {rows:,} rows written to {out_path} in {time.perf_counter() - t0:.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=15_000_000)
    ap.add_argument("--out", type=str, default="data/transactions.csv")
    ap.add_argument("--chunk-size", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    TransactionDataGenerator(args.chunk_size, args.seed).write(args.rows, args.out)


if __name__ == "__main__":
    main()
