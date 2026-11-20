"""Review how creator and claimed-source TF–IDF clusters change with the cosine threshold."""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from . import common, corpus_group_lexical as lexical, episode_figures, gpu_asr


PAIR_FIELDS = ("kind", "left", "right", "cosine", "comparison", "left_texts", "left_selected",
               "right_texts", "right_selected", "shared_texts", "shared_families")
CURVE_FIELDS = ("kind", "threshold", "eligible_groups", "unassessed_groups", "possible_pairs", "compared_pairs",
                "edges", "components", "isolated_groups", "largest_component", "largest_component_share")


def summarize(result, thresholds):
    if result.get("method") != lexical.METHOD:
        raise ValueError("Expected reviewed-family lexical centroids")
    thresholds = sorted(set(thresholds))
    if not thresholds or any(type(t) not in (int, float) or not math.isfinite(t) or not 0 < t <= 1 for t in thresholds):
        raise ValueError("Provide cosine thresholds above zero and at most one")
    groups = {g["id"]: g for g in result["groups"]}
    if len(groups) != len(result["groups"]):
        raise ValueError("A lexical group appears more than once")
    members = {}
    for group in groups.values():
        if group["kind"] not in ("creator", "claimed_entity"):
            raise ValueError("Unexpected group kind")
        members.setdefault(group["kind"], []).append(group["id"])
    comparisons, seen = [], set()
    for item in result["cosine_overlap"]:
        a, b = item["left"], item["right"]
        left, right = groups[a], groups[b]
        if left["kind"] != right["kind"]:
            continue
        key = tuple(sorted((a, b)))
        if a == b or key in seen:
            raise ValueError("Duplicate or self comparison")
        seen.add(key)
        if key != (a, b):
            a, b, left, right = b, a, right, left
        score = item["cosine"]
        if score is not None and (type(score) not in (int, float) or not math.isfinite(score) or not -1e-6 <= score <= 1+1e-6):
            raise ValueError("Expected a finite nonnegative cosine similarity")
        overlap = bool(item["shared_text_units"] or item["shared_reviewed_family_or_singleton_units"])
        if item["overlap_is_not_independent"] is not overlap:
            raise ValueError("Shared source counts do not match the recorded comparison")
        state = "shared source" if overlap else "no lexical evidence" if score is None else "compared"
        comparisons.append(dict(kind=left["kind"], left=a, right=b, cosine=score, comparison=state,
            left_texts=left["observed_recordings"], left_selected=left["selected_recordings"],
            right_texts=right["observed_recordings"], right_selected=right["selected_recordings"],
            shared_texts=item["shared_text_units"], shared_families=item["shared_reviewed_family_or_singleton_units"]))
    comparisons.sort(key=lambda row: (row["kind"], row["left"], row["right"]))
    if len(seen) != sum(len(ids) * (len(ids)-1) // 2 for ids in members.values()):
        raise ValueError("The generation has an incomplete within-group comparison matrix")
    curves = []
    for kind, ids in sorted(members.items()):
        eligible = {i for i in ids if groups[i]["top_terms"]}
        pairs = [row for row in comparisons if row["kind"] == kind and row["comparison"] == "compared"]
        if any(r["left"] not in eligible or r["right"] not in eligible for r in pairs):
            raise ValueError("A measured cosine belongs to an unassessed group")
        for threshold in thresholds:
            parent = {i:i for i in eligible}
            def find(key):
                while key != parent[key]:
                    parent[key] = parent[parent[key]]
                    key = parent[key]
                return key
            edges = 0
            for row in pairs:
                if row["cosine"] >= threshold:
                    edges += 1
                    parent[find(row["right"])] = find(row["left"])
            sizes = Counter(find(i) for i in eligible)
            largest = max(sizes.values(), default=0)
            curves.append(dict(kind=kind, threshold=threshold, eligible_groups=len(eligible), unassessed_groups=len(ids)-len(eligible),
                possible_pairs=len(eligible)*(len(eligible)-1)//2, compared_pairs=len(pairs), edges=edges, components=len(sizes),
                isolated_groups=sum(v == 1 for v in sizes.values()), largest_component=largest,
                largest_component_share=largest/len(eligible) if eligible else None))
    return comparisons, curves


def render(curves, out, *, label=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter
    kinds = {"creator": ("Creators", episode_figures.TEAL), "claimed_entity": ("Claimed sources", "#7A4271")}
    fig, ax = plt.subplots(figsize=(8.4, 4.7), layout="constrained")
    try:
        fig.suptitle("How the lexical clusters change with the threshold", fontsize=16, weight="bold", color=episode_figures.INK)
        ax.set_title(label or "TF–IDF similarity between recording-family-weighted groups", fontsize=10,
                     color=episode_figures.MUTED, pad=14)
        for kind, (name, color) in kinds.items():
            rows = [r for r in curves if r["kind"] == kind and r["compared_pairs"]]
            if rows:
                ax.plot([r["threshold"] for r in rows], [r["largest_component_share"] for r in rows],
                        color=color, linewidth=2, marker="o" if kind == "creator" else "s",
                        linestyle="-" if kind == "creator" else "--", label=f"{name} ({rows[0]['eligible_groups']} assessed)")
        if ax.get_lines():
            ax.legend(frameon=False)
        else:
            ax.text(.5,.5,"No independent group comparisons available",transform=ax.transAxes,ha="center")
        ax.set(ylim=(0,1.03), xlabel="Minimum cosine similarity for a connection",
               ylabel="Assessed groups in the largest cluster")
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.set_xticks(sorted({r["threshold"] for r in curves}))
        ax.grid(axis="y", color="#D3DEDB", linewidth=.7)
        ax.spines[["top","right"]].set_visible(False)
        episode_figures.save_figure(fig, out, "cluster-threshold-sensitivity")
    finally:
        plt.close(fig)


def export(generation, out, thresholds, *, label=""):
    generation, out = common.ensure_outside_git(generation), common.ensure_outside_git(out)
    manifest = json.loads((generation / "manifest.json").read_bytes())
    raw = (generation / "analysis.json").read_bytes()
    digest = sha256(raw).hexdigest()
    if (digest != manifest.get("analysis_sha256") or digest != manifest.get("revision") or digest != generation.name
            or len(raw) != manifest.get("analysis_bytes") or manifest.get("method") != lexical.METHOD):
        raise ValueError("The lexical results no longer match their completed generation")
    comparisons, curves = summarize(json.loads(raw), thresholds)
    out.mkdir(parents=True, exist_ok=True)
    with gpu_asr.kernel_lock(out / ".lexical-figures.lock"), TemporaryDirectory(dir=out) as staging:
        staging = Path(staging)
        episode_figures.write_csv(staging/"within-group-similarity.csv", comparisons, PAIR_FIELDS)
        episode_figures.write_csv(staging/"cluster-threshold-sensitivity.csv", curves, CURVE_FIELDS)
        render(curves, staging, label=label)
        files = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p.read_bytes()).hexdigest()} for p in staging.iterdir()}
        for filename in files:
            os.replace(staging/filename, out/filename)
        common.atomic_write_text(out/"figure-manifest.json", json.dumps(
            {"analysis_sha256":digest, "cosine_thresholds":sorted(set(thresholds)), "label":label, "files":files},
            ensure_ascii=False, indent=2)+"\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--thresholds", nargs="+", type=float, default=[.25,.35,.45,.55,.65,.75,.85,.95])
    parser.add_argument("--label", default="")
    args = parser.parse_args(argv)
    export(args.generation, args.out, args.thresholds, label=args.label)


if __name__ == "__main__":
    main()
