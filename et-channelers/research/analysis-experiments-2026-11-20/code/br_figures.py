"""Figures of experiment BR (a) from br-bridge.json and br-pairs.csv.

    python br_figures.py RESULTS_DIR

Writes figures/br-1-difference-against-mean.png and figures/br-2-difference-in-creator-spread.png there.
"""
import csv
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, INK, MUTED, GRID, BLUE, BAND = "#fcfcfb", "#1f2328", "#6b7280", "#e5e7eb", "#2a78d6", "#dbe9fb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def main():
    folder = Path(sys.argv[1])
    result = json.loads((folder / "br-bridge.json").read_text(encoding="utf-8"))
    pairs = {}
    for row in csv.DictReader(open(folder / "br-pairs.csv", encoding="utf-8")):
        if row["english_only_model"] != "":
            pairs.setdefault(row["measure"], []).append((float(row["english_only_model"]), float(row["larger_model"])))
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

    # BR-1: difference against mean, one panel per measure
    measures = result["measures"]
    columns = 4
    lines = -(-len(measures) // columns)
    figure, axes = plt.subplots(lines, columns, figsize=(11.5, 2.5 * lines))
    for axis, row in zip(axes.flat, measures):
        values = pairs[row["measure"]]
        means = [(small + large) / 2 for small, large in values]
        differences = [large - small for small, large in values]
        axis.axhline(0, color=MUTED, linewidth=0.7)
        axis.axhline(row["mean_difference"], color=BLUE, linewidth=1.2)
        for limit in row["limits_of_agreement"]:
            axis.axhline(limit, color=BLUE, linewidth=0.8, linestyle=(0, (4, 3)))
        axis.plot(means, differences, "o", color=BLUE, markersize=4.2, alpha=0.85, markeredgecolor=SURFACE, markeredgewidth=0.6)
        axis.set_title(row["label"], fontsize=8, loc="left", color=INK)
        axis.grid(color=GRID, linewidth=0.5)
        axis.set_axisbelow(True)
        for side in ("top", "right"):
            axis.spines[side].set_visible(False)
        axis.tick_params(length=0, labelsize=7.5)
    for axis in list(axes.flat)[len(measures):]:
        axis.axis("off")
    figure.suptitle("Difference between the two models against their mean, per recording (solid: mean difference; dashed: limits of agreement)",
                    x=0.01, ha="left", fontsize=11)
    figure.supxlabel("Mean of the two models", fontsize=9, color=MUTED)
    figure.supylabel("Larger model minus English-only model", fontsize=9, color=MUTED)
    figure.tight_layout(rect=(0.01, 0.01, 1, 0.96))
    figure.savefig(out / "br-1-difference-against-mean.png", dpi=150)
    plt.close(figure)
    print("wrote", sorted(path.name for path in out.glob("br-*.png")))


if __name__ == "__main__":
    main()
