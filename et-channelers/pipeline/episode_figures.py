"""Export private, publication-size figures and CSVs from episode_comparison output.

    python -m pipeline.episode_figures comparison.json /private/figures --label "November selection"

Uses Matplotlib from channeling-atlas/research/analysis/requirements.txt. Heatmap
pages share a fixed scale. The network draws the pairs with the most distinct
supporting recording families. Every pair and display decision remains in the CSV.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import textwrap

try:
    from . import collection_coverage, common, gpu_asr
except ImportError:
    import collection_coverage
    import common
    import gpu_asr


COUNT_FIELDS = ("eligible_episodes", "assessed_episodes", "positive_episodes", "eligible_families",
                "assessed_families", "positive_families", "unresolved_family_singletons")
MEASURE_FIELDS = COUNT_FIELDS + ("episode_share", "family_balanced_observed_share", "frame_lower", "frame_upper",
                                 "timed", "partially_timed", "untimed", "supporting_video_ids")
NETWORK_FIELDS = ("topic_a", "topic_b", "jointly_assessed_creators", "supporting_creators",
                  "jointly_assessed_episodes", "supporting_episodes", "distinct_supporting_families",
                  "unresolved_supporting_singletons", "creator_balanced_observed_share",
                  "display_status", "supporting_video_ids")
INK, MUTED, TEAL = "#172F32", "#4F6668", "#236D70"


def display_name(name, width):
    return textwrap.fill(name.replace("_", " ").replace("-", " "), width=width, break_long_words=True)


def network_rows(result, min_families=2, min_creators=1, max_edges=18):
    if not all(type(n) is int and n >= 1 for n in (min_families, min_creators, max_edges)):
        raise ValueError("Network thresholds must be positive integers")
    frame = {r["video_id"]: r for r in result["frame"]}
    groups = defaultdict(list)
    for r in result["same_episode_co_mentions"]:
        groups[r["topic_a"], r["topic_b"]].append(r)
    rows = []
    for (left, right), cells in sorted(groups.items()):
        observed = [r for r in cells if r["assessed_episodes"]]
        videos = sorted({v for r in observed for v in r["supporting_video_ids"]})
        families = {("confirmed", frame[v]["recording_family_id"]) if frame[v]["recording_family_id"] is not None
                    else ("unresolved", v) for v in videos}
        creators = {frame[v]["channel_dir"] for v in videos}
        if not observed:
            status = "unassessed"
        elif len(families) < min_families or len(creators) < min_creators:
            status = "below_display_threshold"
        else:
            status = "qualifies"
        shares = [r["family_balanced_observed_share"] for r in observed]
        rows.append({"topic_a": left, "topic_b": right, "jointly_assessed_creators": len(observed),
                     "supporting_creators": len(creators), "jointly_assessed_episodes": sum(r["assessed_episodes"] for r in observed),
                     "supporting_episodes": len(videos), "distinct_supporting_families": len(families),
                     "unresolved_supporting_singletons": sum(f[0] == "unresolved" for f in families),
                     "creator_balanced_observed_share": sum(shares) / len(shares) if shares else None,
                     "display_status": status, "supporting_video_ids": videos})
    ranked = sorted((r for r in rows if r["display_status"] == "qualifies"),
                    key=lambda r: (-r["distinct_supporting_families"], -r["supporting_creators"],
                                   r["topic_a"], r["topic_b"]))
    for i, row in enumerate(ranked):
        row["display_status"] = "drawn" if i < max_edges else "qualifies_beyond_display_limit"
    return rows


def flat_measure(row):
    flat = dict(row)
    flat["frame_lower"], flat["frame_upper"] = flat.pop("family_balanced_frame_bounds")
    flat.update(flat.pop("timing_of_assessed_episodes"))
    return flat


def write_csv(path, rows, fields):
    data = [{k: json.dumps(r[k], ensure_ascii=False, separators=(",", ":")) if isinstance(r[k], list)
             else r[k] for k in fields} for r in rows]
    path.write_bytes(collection_coverage.csv_bytes(data, fields))


def save_figure(fig, out, stem):
    fig.savefig(out / (stem + ".svg"), bbox_inches="tight", pad_inches=0.16,
                metadata={"Date": None, "Creator": "Channeling research archive"})
    fig.savefig(out / (stem + ".png"), bbox_inches="tight", pad_inches=0.16, dpi=160,
                metadata={"Software": "Channeling research archive"})


def heatmap_figure(plt, cells, creators, topics, label):
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.ticker import PercentFormatter
    import numpy as np

    width = max(7.7, 3.2 + 1.45 * len(topics))
    height = max(3.7, 2.5 + .64 * len(creators))
    fig, ax = plt.subplots(figsize=(width, height), layout="constrained")
    fig.suptitle("Topic presence by creator", fontsize=19, fontweight="bold", color=INK)
    if not creators:
        ax.axis("off")
        ax.text(.5, .5, "No eligible recordings in this selection", ha="center", color=MUTED)
        return fig
    values = [[cells[c, t]["family_balanced_observed_share"] for t in topics] for c in creators]
    colors = LinearSegmentedColormap.from_list("family_share", ["#EDF6F0", "#A8D6C4", "#46928B", "#173D46"])
    colors = colors.with_extremes(bad="#D9DBDD")
    image = ax.imshow(np.ma.masked_invalid(np.array(values, dtype=float)), cmap=colors, vmin=0, vmax=1, aspect="auto")
    ax.set_title((label + "\n" if label else "") + "Equal weight per assessed recording family", fontsize=10, color=MUTED, pad=12)
    ax.set_xticks(range(len(topics)), [display_name(x, 19) for x in topics], fontsize=9)
    ax.set_yticks(range(len(creators)), [display_name(x, 25) for x in creators], fontsize=9)
    ax.xaxis.tick_top()
    ax.tick_params(which="both", length=0, labelcolor=INK)
    for s in ax.spines.values():
        s.set_visible(False)
    for i, creator in enumerate(creators):
        for j, topic in enumerate(topics):
            row = cells[creator, topic]
            share = row["family_balanced_observed_share"]
            color = INK if share is None or share < .68 else "white"
            estimate = "—" if share is None else f"{share:.0%}"
            ax.text(j, i - .11, estimate, ha="center", va="center", fontsize=12, weight="bold", color=color)
            ax.text(j, i + .21, f"{row['assessed_episodes']}/{row['eligible_episodes']}", ha="center",
                    va="center", fontsize=8, color=color)
    ax.set_xticks(np.arange(-.5, len(topics), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(creators), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.set_xlabel("Each cell shows assessed / eligible episodes below its estimate. Gray cells have no assessments.",
                  fontsize=9, color=MUTED, labelpad=9)
    bar = fig.colorbar(image, ax=ax, orientation="horizontal", shrink=.57, pad=.09, aspect=40, ticks=[0, .5, 1])
    bar.ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    bar.ax.tick_params(labelsize=8, length=0, labelcolor=MUTED)
    bar.outline.set_visible(False)
    return fig


def network_figure(plt, rows, label, min_families, min_creators):
    from matplotlib.lines import Line2D

    visible = [r for r in rows if r["display_status"] == "drawn"]
    qualified = sum(r["display_status"] in {"drawn", "qualifies_beyond_display_limit"} for r in rows)
    nodes = sorted({r[k] for r in visible for k in ("topic_a", "topic_b")})
    width = max(9.0, 6 + .48 * len(nodes))
    fig, ax = plt.subplots(figsize=(width, max(5.3, .62 * width)), layout="constrained")
    fig.suptitle("Topics mentioned in the same episode", fontsize=19, fontweight="bold", color=INK)
    subtitle = f"Showing {len(visible)} of {qualified} qualifying pairs from {len(rows)} topic pairs"
    ax.set_title((label + "\n" if label else "") + subtitle, fontsize=10, color=MUTED, pad=8)
    ax.set_axis_off()
    ax.set_xlim(-1.63, 1.63)
    ax.set_ylim(-1.38, 1.38)
    ax.set_aspect("equal")
    if not visible:
        ax.text(0, 0, "No pair meets the displayed support thresholds", ha="center", va="center", color=MUTED)
    else:
        angles = [math.pi / 2 - 2 * math.pi * i / len(nodes) for i in range(len(nodes))]
        pos = {n: (math.cos(a), math.sin(a)) for n, a in zip(nodes, angles)}
        max_support = max(r["distinct_supporting_families"] for r in visible)
        def stroke(n):
            return 1.0 + 4.0 * math.sqrt(n / max_support)
        for row in sorted(visible, key=lambda r: r["distinct_supporting_families"]):
            x, y = zip(pos[row["topic_a"]], pos[row["topic_b"]])
            ax.plot(x, y, linewidth=stroke(row["distinct_supporting_families"]), color=TEAL, alpha=.62, zorder=1)
        for node, (x, y) in pos.items():
            ax.scatter(x, y, s=99, facecolor="#E6F3E9", edgecolor=TEAL, linewidth=1.7, zorder=2)
            align = "left" if x > .25 else "right" if x < -.25 else "center"
            ax.text(x * 1.08, y * 1.13, display_name(node, 19), ha=align, va="center", fontsize=9, color=INK)
        levels = sorted({min(r["distinct_supporting_families"] for r in visible), max_support})
        lines = [Line2D([0], [0], color=TEAL, alpha=.62, linewidth=stroke(n)) for n in levels]
        ax.legend(lines, [str(n) for n in levels], title="Supporting recording families", frameon=False,
                  loc="lower center", ncol=len(levels), fontsize=8, title_fontsize=8)
    foot = (f"Minimum support per edge is {min_families} recording families and {min_creators} "
            f"{'creator' if min_creators == 1 else 'creators'}. Unresolved recordings count individually.")
    fig.supxlabel(foot, fontsize=9, color=MUTED)
    return fig


def render(result, out, label, min_families, min_creators, max_edges):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    edges = network_rows(result, min_families, min_creators, max_edges)
    write_csv(out / "creator-topic.csv", map(flat_measure, result["heatmap"]), ("channel_dir", "topic") + MEASURE_FIELDS)
    write_csv(out / "creator-topic-pairs.csv", map(flat_measure, result["same_episode_co_mentions"]),
              ("channel_dir", "topic_a", "topic_b") + MEASURE_FIELDS + ("episodes_with_either_topic", "episode_jaccard"))
    write_csv(out / "co-mention-network.csv", edges, NETWORK_FIELDS)
    cells = {(r["channel_dir"], r["topic"]): r for r in result["heatmap"]}
    creators, topics = sorted({k[0] for k in cells}), sorted({k[1] for k in cells})
    stems = []
    with matplotlib.rc_context({"svg.fonttype": "none", "svg.hashsalt": "episode-figures-v1", "font.family": "DejaVu Sans"}):
        creator_pages = [creators[i:i + 18] for i in range(0, len(creators), 18)] or [[]]
        topic_pages = [topics[i:i + 8] for i in range(0, len(topics), 8)] or [[]]
        for i, creator_page in enumerate(creator_pages, 1):
            for j, topic_page in enumerate(topic_pages, 1):
                fig = heatmap_figure(plt, cells, creator_page, topic_page, label)
                stem = f"topic-heatmap-r{i:02}-c{j:02}"
                save_figure(fig, out, stem)
                plt.close(fig)
                stems.append(stem)
        fig = network_figure(plt, edges, label, min_families, min_creators)
        save_figure(fig, out, "co-mention-network")
        plt.close(fig)
    return stems + ["co-mention-network"]


def export(result, out, *, label="", min_families=2, min_creators=1, max_edges=18):
    out = common.ensure_outside_git(out)
    out.mkdir(parents=True, exist_ok=True)
    source = json.dumps(result, allow_nan=False, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    # The manifest declares the entire current generation, including its precise number of heatmap pages.
    with gpu_asr.kernel_lock(out / ".episode-figures.lock"), TemporaryDirectory(dir=out) as staging:
        staging = Path(staging)
        stems = render(result, staging, label, min_families, min_creators, max_edges)
        files = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p.read_bytes()).hexdigest()}
                 for p in sorted(staging.iterdir())}
        manifest = {"schema_version": 1, "comparison_sha256": sha256(source).hexdigest(), "label": label,
                    "min_families": min_families, "min_creators": min_creators, "max_edges": max_edges, "files": files}
        for name in files:
            os.replace(staging / name, out / name)
        common.atomic_write_text(out / "figure-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return stems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparison", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--label", default="", help="Selection name or date shown on each figure")
    parser.add_argument("--min-families", type=int, default=2)
    parser.add_argument("--min-creators", type=int, default=1)
    parser.add_argument("--max-edges", type=int, default=18)
    args = parser.parse_args(argv)
    export(json.loads(args.comparison.read_bytes()), args.out, label=args.label,
           min_families=args.min_families, min_creators=args.min_creators, max_edges=args.max_edges)


if __name__ == "__main__":
    main()
