"""
Generates a large synthetic e-commerce transactions CSV for the
out-of-core benchmark. Written in chunks with numpy vectorized calls
so *generating* the data never itself requires holding the whole
dataset in memory (that would defeat the point of the demo).

Usage:
    python3 generate_data.py --rows 15000000 --out data/transactions.csv
"""
import argparse
import csv
import time

import numpy as np

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


def generate(rows: int, out_path: str, chunk_size: int = 1_000_000, seed: int = 42):
    rng = np.random.default_rng(seed)
    start_ts = np.datetime64("2024-01-01T00:00:00")
    two_years_seconds = 2 * 365 * 24 * 3600

    written = 0
    t0 = time.perf_counter()
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        while written < rows:
            n = min(chunk_size, rows - written)

            order_ids = np.arange(written, written + n)
            user_ids = rng.integers(1, 2_000_000, size=n)
            product_ids = rng.integers(1, 50_000, size=n)
            categories = rng.choice(CATEGORIES, size=n)
            # right-skewed price distribution (lognormal), clipped
            prices = np.round(np.clip(rng.lognormal(mean=3.0, sigma=0.9, size=n), 1.0, 2000.0), 2)
            quantities = rng.integers(1, 10, size=n)
            countries = rng.choice(COUNTRIES, size=n)
            offsets = rng.integers(0, two_years_seconds, size=n)
            timestamps = start_ts + offsets.astype("timedelta64[s]")

            rows_chunk = zip(
                order_ids, user_ids, product_ids, categories,
                prices, quantities, countries, timestamps.astype(str),
            )
            writer.writerows(rows_chunk)

            written += n
            elapsed = time.perf_counter() - t0
            print(f"  wrote {written:,} / {rows:,} rows ({elapsed:.1f}s elapsed)", flush=True)

    elapsed = time.perf_counter() - t0
    print(f"Done. {rows:,} rows written to {out_path} in {elapsed:.1f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=15_000_000)
    ap.add_argument("--out", type=str, default="data/transactions.csv")
    ap.add_argument("--chunk-size", type=int, default=1_000_000)
    args = ap.parse_args()
    generate(args.rows, args.out, args.chunk_size)
