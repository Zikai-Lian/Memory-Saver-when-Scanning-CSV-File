"""
Benchmark driver: runs each approach against the same dataset (each
in its own fresh, isolated process via measure_run.py), records wall
time and peak RSS, verifies all approaches agree on the result, and
writes results/benchmark_results.csv.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

APPROACHES = [
    ("naive_pandas (load-all)", ["approaches/naive_pandas.py"]),
    ("chunked_pandas", ["approaches/chunked_pandas.py"]),
    ("polars_lazy_streaming", ["approaches/polars_lazy.py"]),
    ("duckdb_sql", ["approaches/duckdb_approach.py"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/transactions.csv")
    ap.add_argument("--out", default="results/benchmark_results.csv")
    args = ap.parse_args()

    rows = []
    reference_result = None
    for name, cmd in APPROACHES:
        full_cmd = [sys.executable, "measure_run.py", sys.executable] + cmd + ["--input", args.input]
        print(f"Running: {name} ...", flush=True)
        out = subprocess.run(full_cmd, capture_output=True, text=True)
        if not out.stdout.strip():
            print(f"  FAILED (no output). stderr:\n{out.stderr}", file=sys.stderr)
            continue
        payload = json.loads(out.stdout.strip().splitlines()[-1])
        if payload["returncode"] != 0:
            print(f"  FAILED: {payload['stderr_tail']}", file=sys.stderr)
            continue

        result = payload["result"]
        if reference_result is None:
            reference_result = result
            correctness = "reference"
        else:
            correctness = "MATCH" if result == reference_result else "MISMATCH"

        print(f"  wall_time={payload['wall_time_s']:.2f}s  "
              f"peak_rss={payload['peak_rss_mb']:.1f}MB  correctness={correctness}", flush=True)

        rows.append({
            "approach": name,
            "wall_time_s": payload["wall_time_s"],
            "peak_rss_mb": payload["peak_rss_mb"],
            "total_revenue": result["total_revenue"],
            "total_orders": result["total_orders"],
            "correctness": correctness,
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write("approach,wall_time_s,peak_rss_mb,total_revenue,total_orders,correctness\n")
        for r in rows:
            f.write(f"{r['approach']},{r['wall_time_s']},{r['peak_rss_mb']},"
                    f"{r['total_revenue']},{r['total_orders']},{r['correctness']}\n")

    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
