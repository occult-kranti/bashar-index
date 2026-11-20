"""Export a compact publication-date figure from the validated latest-20+ report."""
import argparse
from collections import Counter
from datetime import date, timedelta
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


def export_daily(report, destination, window_days=30, end=None):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.ticker import MaxNLocator

    days = source.daily_counts(report["records"])
    if not days or window_days < 1:
        raise ValueError("The daily figure needs dated evidence and a positive window")
    last = date.fromisoformat(end or days[-1]["date"])
    first = last - timedelta(days=window_days - 1)
    rows = [row for row in days if first.isoformat() <= row["date"] <= last.isoformat()]
    if not rows:
        raise ValueError("The requested window is outside the observed date range")
    positions = list(range(len(rows)))
    stamps = [date.fromisoformat(row["date"]) for row in rows]
    field = [r["publication"] + r["availability"] + r["upload"] for r in rows]
    single = [r["relative_single_day"] for r in rows]
    assigned = [r["assigned_total"] for r in rows]
    possible = [r["possible_total"] for r in rows]
    fig, (ax, lens) = plt.subplots(2, 1, sharex=True, figsize=(12, 7.4),
                                   gridspec_kw={"height_ratios":[1.7, 1]})
    for panel in (ax, lens):
        panel.set_facecolor("#fbfaf7")
        panel.set_axisbelow(True)
        panel.grid(axis="y", alpha=.17)
        panel.spines[["top", "right", "left"]].set_visible(False)
        panel.tick_params(length=0, pad=5)
        panel.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
        panel.set_ylabel("Recordings")
    fig.patch.set_facecolor("#fbfaf7")
    ax.bar(positions, field, color="#245168", width=.72, label="Date-stamped metadata")
    ax.bar(positions, single, bottom=field, color="#e1ab59", edgecolor="#765833", linewidth=.5,
           width=.72, label="Estimate within one UTC day")
    ax.set_ylim(0, max(assigned, default=0)*1.25 + 1)
    if len(rows) <= 40:
        for position, count in zip(positions, assigned):
            ax.annotate(str(count), (position, count), xytext=(0,4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8, color="#203944")
    ax.legend(loc="upper right", frameon=False, ncol=2, fontsize=9)
    ax.set_title("Recordings assigned to each day", loc="left", fontsize=13)
    lens.fill_between(positions, assigned, possible, color="#eee1c7", step="mid")
    lens.step(positions, possible, where="mid", color="#996c25", label="Including overlapping date estimates")
    lens.step(positions, assigned, where="mid", color="#245168", label="Assigned to this day")
    lens.legend(loc="upper right", frameon=False, fontsize=8)
    lens.set_ylim(0, max(possible, default=0)*1.23 + 1)
    lens.set_title("How the count could change with more precise dates", loc="left", fontsize=13)
    step = max(1, round(len(rows) / 8))
    ticks = list(range(0, len(rows), step))
    if len(rows)-1 != ticks[-1] and len(rows)-1 - ticks[-1] <= step//2:
        ticks.pop()
    ticks = sorted(set([0, *ticks, len(rows)-1]))
    lens.set_xticks(ticks, [stamps[i].strftime("%b %d") for i in ticks])
    lens.set_xlim(-.65, len(rows)-.35)
    fig.suptitle("Daily distribution of selected regular uploads", x=.085, ha="left", fontsize=19)
    fig.text(.085,.911, f"{stamps[0]:%d %b %Y} through {stamps[-1]:%d %b %Y} UTC  |  "
             f"Latest-20+ selection across {report['creators']} channels", fontsize=10)
    fig.text(.085,.047, "An interval that spans dates contributes to the upper count on each date it overlaps.", fontsize=9)
    fig.text(.085,.023, "Adding those upper counts across days would count some recordings more than once.", fontsize=9)
    fig.subplots_adjust(top=.82, bottom=.13, left=.085, right=.975, hspace=.36)
    fig.savefig(destination, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--daily-window", type=int, help="Export a daily chart with this many calendar days")
    parser.add_argument("--end", help="Last UTC date of a daily chart (YYYY-MM-DD)")
    args = parser.parse_args()
    report = json.loads(args.report.read_bytes())
    if args.daily_window is None:
        export(report, args.out)
    else:
        export_daily(report, args.out, args.daily_window, args.end)
