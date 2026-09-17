"""
Plots the benchmark results: peak memory and wall time per approach,
as two separate single-axis bar charts (never a dual-axis chart).
"""
import csv

import matplotlib.pyplot as plt

# Fixed categorical order/colors -- assigned by approach identity, not by rank/value.
COLORS = {
    "naive_pandas (load-all)": "#94A3B8",   # neutral gray -- the baseline being improved on
    "chunked_pandas": "#3B82F6",             # blue
    "polars_lazy_streaming": "#10B981",      # green
    "duckdb_sql": "#8B5CF6",                 # purple
}


def load_results(path):
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def plot(rows, out_path):
    approaches = [r["approach"] for r in rows]
    mem = [float(r["peak_rss_mb"]) for r in rows]
    time_s = [float(r["wall_time_s"]) for r in rows]
    colors = [COLORS.get(a, "#94A3B8") for a in approaches]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor("white")

    # --- Peak memory chart ---
    ax = axes[0]
    bars = ax.bar(approaches, mem, color=colors, width=0.6)
    ax.set_title("Peak memory (RSS) by approach", fontsize=13, fontweight="bold", loc="left")
    ax.set_ylabel("Peak RSS (MB)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", rotation=20)
    for b, v in zip(bars, mem):
        ax.annotate(f"{v:,.0f} MB", (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=9, color="#334155")

    # --- Wall time chart ---
    ax = axes[1]
    bars = ax.bar(approaches, time_s, color=colors, width=0.6)
    ax.set_title("Wall-clock time by approach", fontsize=13, fontweight="bold", loc="left")
    ax.set_ylabel("Wall time (s)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", rotation=20)
    for b, v in zip(bars, time_s):
        ax.annotate(f"{v:,.1f} s", (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=9, color="#334155")

    fig.suptitle("Out-of-core CSV aggregation: memory & speed tradeoffs (876 MB / 15M rows)",
                  fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=160)
    print(f"Saved chart to {out_path}")


if __name__ == "__main__":
    rows = load_results("results/benchmark_results.csv")
    plot(rows, "results/benchmark_chart.png")
