"""
Runs one approach and prints its result as `RESULT:{json}`.

This is the process whose memory gets measured, so it imports only what
the chosen approach needs to run.

Usage:
    python run_approach.py duckdb --input data/transactions.csv
    python run_approach.py chunked_pandas --input data/transactions.csv --chunk-size 250000
"""
import argparse
import json

from approaches import get_approach


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("approach", help="naive_pandas, chunked_pandas, polars_lazy, or duckdb")
    ap.add_argument("--input", required=True)
    ap.add_argument("--chunk-size", type=int, default=None, help="only used by chunked_pandas")
    args = ap.parse_args()

    options = {"chunk_size": args.chunk_size} if args.chunk_size else {}
    approach = get_approach(args.approach, **options)
    result = approach.run(args.input)
    print("RESULT:" + json.dumps(result.to_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
