"""
Measuring one approach in isolation.

Each approach runs in its own fresh process tree:

    benchmark.py  ->  measure_run.py  ->  run_approach.py <key>

measure_run.py is started fresh for every approach, so
resource.getrusage(RUSAGE_CHILDREN) inside it only ever sees the one
child it launched. That keeps peak-memory numbers from leaking between
approaches.
"""
from __future__ import annotations

import json
import resource
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from approaches import AggregationResult

HERE = Path(__file__).resolve().parent


def children_peak_rss_mb() -> float:
    """Peak RSS of reaped child processes, in MB.

    ru_maxrss is reported in kilobytes on Linux but in bytes on macOS.
    """
    max_rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return max_rss / divisor


@dataclass
class Measurement:
    """What we learned from running one approach once."""

    wall_time_s: float
    peak_rss_mb: float
    returncode: int
    result: Optional[AggregationResult]
    stderr_tail: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0 and self.result is not None

    def to_json(self) -> str:
        return json.dumps({
            "wall_time_s": self.wall_time_s,
            "peak_rss_mb": self.peak_rss_mb,
            "returncode": self.returncode,
            "result": self.result.to_dict() if self.result else None,
            "stderr_tail": self.stderr_tail,
        })

    @classmethod
    def from_json(cls, text: str) -> "Measurement":
        data = json.loads(text)
        result = data.get("result")
        return cls(
            wall_time_s=data["wall_time_s"],
            peak_rss_mb=data["peak_rss_mb"],
            returncode=data["returncode"],
            result=AggregationResult.from_dict(result) if result else None,
            stderr_tail=data.get("stderr_tail", ""),
        )

    @classmethod
    def failure(cls, message: str) -> "Measurement":
        return cls(wall_time_s=0.0, peak_rss_mb=0.0, returncode=1, result=None, stderr_tail=message)


class IsolatedRunner:
    """Runs one approach in a fresh process tree and returns its Measurement."""

    def __init__(self, python: str = sys.executable):
        self.python = python

    def measure(self, approach_key: str, input_path: str, extra_args: tuple[str, ...] = ()) -> Measurement:
        cmd = [
            self.python, str(HERE / "measure_run.py"),
            self.python, str(HERE / "run_approach.py"), approach_key,
            "--input", input_path, *extra_args,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        lines = proc.stdout.strip().splitlines()
        if not lines:
            return Measurement.failure(proc.stderr[-2000:] or "no output")
        return Measurement.from_json(lines[-1])
