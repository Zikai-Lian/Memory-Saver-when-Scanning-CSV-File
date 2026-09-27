"""
Plots the benchmark results: peak memory and wall time per approach,
as two separate single-axis bar charts (never a dual-axis chart).

Usage:
    python plot_results.py [--results results/benchmark_results.csv] [--out results/benchmark_chart.png]
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")  # render to a file without needing a display
import matplotlib.pyplot as plt  # noqa: E402


@dataclass
class ChartPanel:
    """One of the two bar charts."""

    column: str
    title: str
    ylabel: str
    label_format: str


class BenchmarkPlotter:
    # Fixed colors per approach, so a color always means the same approach.
    COLORS = {
        "naive_pandas (load-all)": "#94A3B8",  # neutral gray: the baseline
        "chunked_pandas": "#3B82F6",            # blue
        "polars_lazy_streaming": "#10B981",     # green
        "duckdb_sql": "#8B5CF6",                # purple
    }
    DEFAULT_COLOR = "#94A3B8"
    PANELS = (
        ChartPanel("peak_rss_mb", "Peak memory (RSS) by approach", "Peak RSS (MB)", "{:,.0f} MB"),
        ChartPanel("wall_time_s", "Wall-clock time by approach", "Wall time (s)", "{:,.1f} s"),
    )

    def __init__(self, rows: list[dict], title: str):
        self.rows = rows
        self.title = title

    @classmethod
    def from_csv(cls, path: str, title: str) -> "BenchmarkPlotter":
        with open(path) as f:
            return cls(list(csv.DictReader(f)), title)

    @property
    def approaches(self) -> list[str]:
        return [r["approach"] for r in self.rows]

    def _draw_panel(self, ax, panel: ChartPanel) -> None:
        values = [float(r[panel.column]) for r in self.rows]
        colors = [self.COLORS.get(a, self.DEFAULT_COLOR) for a in self.approaches]
        bars = ax.bar(self.approaches, values, color=colors, width=0.6)
        ax.set_title(panel.title, fontsize=13, fontweight="bold", loc="left")
        ax.set_ylabel(panel.ylabel)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", rotation=20)
        for bar, value in zip(bars, values):
            ax.annotate(panel.label_format.format(value),
                        (bar.get_x() + bar.get_width() / 2, value),
                        ha="center", va="bottom", fontsize=9, color="#334155")

    def save(self, out_path: str) -> None:
        fig, axes = plt.subplots(1, len(self.PANELS), figsize=(12, 5))
        fig.patch.set_facecolor("white")
        for ax, panel in zip(axes, self.PANELS):
            self._draw_panel(ax, panel)
        fig.suptitle(self.title, fontsize=14, fontweight="bold")
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        fig.savefig(out_path, dpi=160)
        plt.close(fig)
        print(f"Saved chart to {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/benchmark_results.csv")
    ap.add_argument("--out", default="results/benchmark_chart.png")
    ap.add_argument("--title", default="Out-of-core CSV aggregation: memory & speed tradeoffs (876 MB / 15M rows)")
    args = ap.parse_args()
    BenchmarkPlotter.from_csv(args.results, args.title).save(args.out)


if __name__ == "__main__":
    main()
