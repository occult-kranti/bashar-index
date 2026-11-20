"""Export a compact publication-date figure from the validated latest-20+ report."""
import argparse
from collections import Counter
import json
from pathlib import Path

from . import regular_recording_dates as source


def export(report, destination):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.patches import Patch

    records = report["records"]
    year_counts = source.period_counts(records, "year")
    last_year = max(r["year"] for r in year_counts if r["year"].isdigit())
    months = [r for r in source.period_counts(records, "month") if r["month"].startswith(last_year + "-")]
    groups = {"Earlier years": Counter(), str(int(last_year) - 1): Counter(),
              last_year: Counter(), "Across years": Counter()}
    for entry in year_counts:
        period = entry["year"]
        group = period if period in groups else ("Earlier years" if period.isdigit() else "Across years")
        groups[group].update({k: entry[k] for k in source.METHOD})

    fig, axes = plt.subplots(2, 1, figsize=(10.5, 7.3), gridspec_kw={"height_ratios": [1, 1.2]})
    fig.patch.set_facecolor("#faf9f6")
    colors = ("#29566a", "#cc873b")
    def bars(ax, labels, rows):
        exact = [r["publication"] + r["availability"] + r["upload"] for r in rows]
        estimated = [r["relative"] for r in rows]
        ax.set_facecolor("#faf9f6")
        ax.bar(labels, exact, color=colors[0], width=.64)
        ax.bar(labels, estimated, bottom=exact, color=colors[1], width=.64)
        largest = max((a + b for a, b in zip(exact, estimated)), default=0)
        ax.set_ylim(0, largest * 1.19 + 1)
        for i, (a, b) in enumerate(zip(exact, estimated)):
            ax.text(i, a + b + largest * .022, f"{a+b:,}", ha="center", fontsize=9)
        ax.set_axisbelow(True)
        ax.grid(axis="y", alpha=.16)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="both", length=0, pad=5)
        ax.set_ylabel("Recordings")

    bars(axes[0], list(groups), list(groups.values()))
    bars(axes[1], [r["month"][-2:] for r in months], months)
    axes[0].set_title("Year of publication or availability", loc="left", fontsize=13)
    axes[1].set_title(f"Months assigned within {last_year}", loc="left", fontsize=13)
    fig.suptitle("Publication dates of the latest 20+ regular uploads", x=.086, ha="left", fontsize=18)
    fig.legend(handles=[Patch(color=c, label=l) for c,l in zip(colors, ("Date-stamped metadata", "Listing-age interval"))],
               loc="upper left", bbox_to_anchor=(.08,.932), ncol=2, frameon=False)
    ambiguous = sum(1 for r in records if r["date_method"] == "relative" and not r["month_bin"])
    fig.text(.085,.044, f"{len(records):,} selected recordings across {report['creators']} channels. "
             f"{ambiguous} intervals across the full sample span multiple months.", fontsize=9)
    fig.text(.085,.019, "A listing-age interval enters a bin only if both endpoints fit. Source listings were observed in UTC.", fontsize=9)
    fig.subplots_adjust(top=.82, bottom=.12, left=.09, right=.97, hspace=.49)
    fig.savefig(destination, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    export(json.loads(args.report.read_bytes()), args.out)
