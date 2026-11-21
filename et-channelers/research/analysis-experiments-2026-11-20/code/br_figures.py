"""Figures of experiment BR (a) from br-bridge.json and, for BR-1, the per-recording pairs.

    python br_figures.py RESULTS_DIR [PAIRS_CSV]

Writes figures/br-2-difference-in-creator-spread.png in RESULTS_DIR from br-bridge.json. With PAIRS_CSV (the
br-pairs.csv that br_bridge.py writes, kept in the private archive since 20 November 2026) it also writes
figures/br-1-difference-distribution.png: per measure, the distribution of the paired differences as percentiles
(middle half, 10th to 90th percentile, median) with the mean difference and the limits of agreement. No mark stands
for a single recording: the 36 recordings come one per creator, so a per-recording mark would be a per-creator mark.
"""
import csv
import json
from pathlib import Path
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SURFACE, INK, MUTED, GRID, BLUE, BAND = "#fcfcfb", "#1f2328", "#6b7280", "#e5e7eb", "#2a78d6", "#dbe9fb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def main():
    folder = Path(sys.argv[1])
    result = json.loads((folder / "br-bridge.json").read_text(encoding="utf-8"))
    out = folder / "figures"
    out.mkdir(exist_ok=True)

    # BR-2: mean difference in units of the spread between creators
    rows = sorted(result["measures"], key=lambda row: abs(row["in_sd_units"]["mean"]))
    figure, axis = plt.subplots(figsize=(10.5, 0.34 * len(rows) + 1.7))
    margin = result["margin_in_between_creator_sd"]
    axis.axvspan(-margin, margin, color=BAND, zorder=0)
    axis.axvline(0, color=MUTED, linewidth=0.8, zorder=1)
    for position, row in enumerate(rows):
        low, high = row["in_sd_units"]["interval_90"]
        axis.plot([low, high], [position, position], color=MUTED, linewidth=2, solid_capstyle="round", zorder=2)
        axis.plot(row["in_sd_units"]["mean"], position, "o", color=BLUE, markersize=6.5, markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=3)
        verdict = "agrees" if row["bridge_safe"] else ("differs" if low > margin or high < -margin else "not settled")
        axis.text(1.01, position, verdict, transform=axis.get_yaxis_transform(), va="center", fontsize=8.5, color=INK)
    axis.set_yticks(range(len(rows)))
    axis.set_yticklabels([row["label"] for row in rows], color=INK)
    axis.set_xlabel("Larger model minus English-only model, in standard deviations between creators")
    axis.grid(axis="x", color=GRID, linewidth=0.6)
    axis.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axis.spines[side].set_visible(False)
    axis.tick_params(length=0)
    figure.suptitle(f"Two recognizer models on the same {result['pairs']} English recordings: which measures agree", x=0.01, ha="left", fontsize=11.5)
    figure.text(0.01, 0.01, "Dot: mean difference. Line: 90% interval. Shaded: the margin of 0.2 fixed beforehand; a measure agrees only if its whole "
                            "interval lies inside it," + chr(10) + "and differs if the whole interval lies outside it. Neither transcript was checked by a person.",
                fontsize=7.5, color=MUTED)
    figure.tight_layout(rect=(0, 0.05, 0.93, 0.96))
    figure.savefig(out / "br-2-difference-in-creator-spread.png", dpi=170)
    plt.close(figure)

    if len(sys.argv) < 3:
        print("wrote", sorted(path.name for path in out.glob("br-*.png")))
        return

    # BR-1: distribution of the paired differences per measure, in the measure's own units; percentiles only
    pairs = {}
    for row in csv.DictReader(open(sys.argv[2], encoding="utf-8")):
        if row["english_only_model"] != "":
            pairs.setdefault(row["measure"], []).append(float(row["larger_model"]) - float(row["english_only_model"]))
    measures = result["measures"]
    columns = 4
    lines = -(-len(measures) // columns)
    figure, axes = plt.subplots(lines, columns, figsize=(11.5, 1.8 * lines + 0.9))
    for axis, row in zip(axes.flat, measures):
        differences = np.asarray(pairs[row["measure"]])
        p10, q1, median, q3, p90 = np.percentile(differences, [10, 25, 50, 75, 90])
        low, high = row["limits_of_agreement"]
        axis.axvline(0, color=MUTED, linewidth=0.7)
        axis.axvspan(low, high, color=BAND, zorder=0)
        axis.plot([p10, p90], [0, 0], color=MUTED, linewidth=1.4, solid_capstyle="butt", zorder=2)
        axis.add_patch(plt.Rectangle((q1, -0.22), q3 - q1, 0.44, facecolor=BLUE, alpha=0.45, edgecolor="none", zorder=3))
        axis.plot([median, median], [-0.22, 0.22], color=INK, linewidth=1.4, zorder=4)
        axis.plot(row["mean_difference"], 0, "D", color=BLUE, markersize=5, markeredgecolor=SURFACE, markeredgewidth=0.6, zorder=5)
        reach = max(abs(low), abs(high), abs(p10), abs(p90)) * 1.1 or 1.0
        axis.set_xlim(-reach, reach)
        axis.set_ylim(-0.6, 0.6)
        axis.set_yticks([])
        axis.set_title(textwrap.fill(row["label"], 40), fontsize=8, loc="left", color=INK)
        axis.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
        axis.grid(axis="x", color=GRID, linewidth=0.5)
        axis.set_axisbelow(True)
        for side in ("top", "right", "left"):
            axis.spines[side].set_visible(False)
        axis.tick_params(length=0, labelsize=7.5)
    for axis in list(axes.flat)[len(measures):]:
        axis.axis("off")
    figure.suptitle(f"Larger model minus English-only model on the same {result['pairs']} English recordings, per measure in its own units",
                    x=0.01, ha="left", fontsize=11)
    figure.text(0.01, 0.005, "Bar: middle half of the paired differences; line: 10th to 90th percentile; black tick: median; diamond: mean difference; "
                             "shaded: limits of agreement. Percentiles only: no mark stands for one recording.", fontsize=7.5, color=MUTED)
    figure.tight_layout(rect=(0.0, 0.03, 1, 0.95))
    figure.savefig(out / "br-1-difference-distribution.png", dpi=150)
    plt.close(figure)
    print("wrote", sorted(path.name for path in out.glob("br-*.png")))


if __name__ == "__main__":
    main()
