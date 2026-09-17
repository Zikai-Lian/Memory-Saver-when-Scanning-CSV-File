"""
Runs a single command as a fresh subprocess and reports its wall time
and peak resident set size (RSS).

This script is itself invoked as a brand-new process for every
approach it measures, so resource.getrusage(RUSAGE_CHILDREN) after
the child exits reflects *only* that one child's peak RSS -- there's
no cross-contamination between approaches, since RUSAGE_CHILDREN
tracks the maximum RSS seen among reaped children of the calling
process, and here there's only ever one.
"""
import argparse
import json
import resource
import subprocess
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    args = ap.parse_args()

    t0 = time.perf_counter()
    proc = subprocess.run(args.cmd, capture_output=True, text=True)
    wall_time_s = time.perf_counter() - t0

    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    peak_rss_mb = usage.ru_maxrss / 1024  # ru_maxrss is in KB on Linux

    result_line = next((l for l in proc.stdout.splitlines() if l.startswith("RESULT:")), None)
    payload = {
        "wall_time_s": round(wall_time_s, 3),
        "peak_rss_mb": round(peak_rss_mb, 2),
        "returncode": proc.returncode,
        "result": json.loads(result_line[len("RESULT:"):]) if result_line else None,
        "stderr_tail": proc.stderr[-2000:] if proc.returncode != 0 else "",
    }
    print(json.dumps(payload))


if __name__ == "__main__":
    main()
