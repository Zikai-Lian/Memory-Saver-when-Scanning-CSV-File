"""
Runs a single command as a fresh subprocess and prints a Measurement
(wall time + peak RSS + parsed result) as one line of JSON.

This script is itself launched as a brand-new process for every
approach, so RUSAGE_CHILDREN only reflects the one child it runs.
See measurement.py for the details.

Usage: python measure_run.py <command> [args...]
"""
import sys
import time
import subprocess
import json

from approaches import AggregationResult
from measurement import Measurement, children_peak_rss_mb

RESULT_PREFIX = "RESULT:"


def main(cmd: list[str]) -> None:
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    wall_time_s = time.perf_counter() - t0

    result_line = next((l for l in proc.stdout.splitlines() if l.startswith(RESULT_PREFIX)), None)
    result = (
        AggregationResult.from_dict(json.loads(result_line[len(RESULT_PREFIX):]))
        if result_line else None
    )

    measurement = Measurement(
        wall_time_s=round(wall_time_s, 3),
        peak_rss_mb=round(children_peak_rss_mb(), 2),
        returncode=proc.returncode,
        result=result,
        stderr_tail=proc.stderr[-2000:] if proc.returncode != 0 else "",
    )
    print(measurement.to_json())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python measure_run.py <command> [args...]")
    main(sys.argv[1:])
