#!/usr/bin/env python3
"""Prepare newest-50 audio work and index the remaining final round; no network."""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ET_ROOT, ID_RE, atomic_write_text, ensure_outside_git, sha256_file, utc_now, write_csv
from prepare_all_queue import EXTRA_FIELDS, enrich, snapshot
from select_jobs import FIELDS


def validate_tier(rows, newest):
    ids, ranks = set(), set()
    for row in rows:
        video_id, channel = row.get("video_id", ""), row.get("channel_dir", "")
        if not ID_RE.fullmatch(video_id) or not channel or video_id in ids:
            raise ValueError("Tier has an invalid or duplicate video ID or missing channel")
        try:
            rank = int(row.get("listing_rank", ""))
        except (ValueError, TypeError) as exc:
            raise ValueError("Tier requires its original listing ranks") from exc
        if row.get("tab") != "videos" or not 0 <= rank < newest or (channel, rank) in ranks:
            raise ValueError("Tier must contain unique Videos-tab ranks below its limit")
        ids.add(video_id)
        ranks.add((channel, rank))
    if not rows:
        raise ValueError("Tier is empty")
    return ids


def partition(newest20, newest50, full, targets, hosts):
    ids20, ids50 = validate_tier(newest20, 20), validate_tier(newest50, 50)
    if not ids20 <= ids50:
        raise ValueError("Newest-50 snapshot must include every newest-20 ID")
    catalog = {}
    for row in full:
        video_id = row.get("video_id", "")
        if not ID_RE.fullmatch(video_id) or video_id in catalog:
            raise ValueError("Full index has an invalid or duplicate video ID")
        if row.get("tab", "") not in {"videos", "shorts", "streams", ""}:
            raise ValueError("Full index contains an unrecognized source tab")
        catalog[video_id] = dict(row)
    tier = []
    for source in newest50:
        prior = catalog.get(source["video_id"], {})
        row = dict(source)
        for key, value in prior.items():
            if key not in {"tab", "listing_rank"} and row.get(key) in (None, ""):
                row[key] = value
        row["queue_provenance"] = "newest50_snapshot+full_catalog" if prior else "newest50_snapshot"
        tier.append(row)
    enrich(tier, targets, hosts)
    for row in tier:
        catalog.setdefault(row["video_id"], dict(row))
    remaining = [row for video_id, row in catalog.items() if video_id not in ids50]
    return tier, remaining, len(catalog)


def grouped_index(rows):
    groups = collections.defaultdict(list)
    for row in rows:
        groups[(row["channel_dir"], row.get("tab") or "unknown")].append(row)
    output = []
    for (channel, tab), items in sorted(groups.items()):
        durations = [float(r["duration_s"]) for r in items if r.get("duration_s") not in (None, "")]
        output.append({"channel_dir": channel, "source_channel_name": items[0].get("source_channel_name", channel),
                       "primary_people": " | ".join(sorted({r.get("primary_person_name", "") for r in items} - {""})),
                       "tab": tab, "items": len(items), "known_duration_hours": round(sum(durations) / 3600, 3),
                       "unknown_duration_items": len(items) - len(durations)})
    return output


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--newest20", type=Path, required=True)
    ap.add_argument("--newest50", type=Path, required=True)
    ap.add_argument("--full", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args(argv)
    ensure_outside_git(args.out_dir)
    inputs = {}
    twenty, inputs["newest20"] = snapshot(args.newest20)
    fifty, inputs["newest50"] = snapshot(args.newest50)
    full, inputs["full_catalog"] = snapshot(args.full)
    names, inputs["person_map"] = snapshot(ET_ROOT / "plan" / "targets.csv")
    hosts, inputs["host_map"] = snapshot(ET_ROOT / "draft-package" / "csv" / "bashar_videos_in_repo_by_channel.csv")
    tier, remaining, total = partition(twenty, fifty, full,
                                       {r["person_id"]: r for r in names}, {r["video_id"]: r for r in hosts})
    tier_path = args.out_dir / "queue_newest50_enriched.csv"
    remaining_path = args.out_dir / "queue_final_round.csv"
    group_path = args.out_dir / "final_round_by_channel_tab.csv"
    if {tier_path.resolve(), remaining_path.resolve(), group_path.resolve()} & {Path(item["path"]) for item in inputs.values()}:
        ap.error("Stage outputs must not replace input snapshots; use the original newest50 asset as input")
    write_csv(tier_path, tier, FIELDS + EXTRA_FIELDS)
    write_csv(remaining_path, remaining, FIELDS + EXTRA_FIELDS)
    groups = grouped_index(remaining)
    write_csv(group_path, groups, ["channel_dir", "source_channel_name", "primary_people", "tab", "items",
                                   "known_duration_hours", "unknown_duration_items"])
    metadata = {"created": utc_now(), "inputs": inputs, "newest20_items": len(twenty),
                "newest50_items": len(tier), "newest50_channels": len({r["channel_dir"] for r in tier}),
                "total_indexed_items": total, "remaining_items": len(remaining),
                "remaining_tabs": dict(collections.Counter(r.get("tab") or "unknown" for r in remaining)),
                "duration_filter": None, "final_round_status": "indexed_only_not_started",
                "outputs": {"newest50": {"path": str(tier_path), "sha256": sha256_file(tier_path)},
                            "remaining": {"path": str(remaining_path), "sha256": sha256_file(remaining_path)},
                            "groups": {"path": str(group_path), "sha256": sha256_file(group_path)}}}
    atomic_write_text(args.out_dir / "collection_stages.meta.json", json.dumps(metadata, indent=2) + "\n")
    atomic_write_text(tier_path.with_suffix(".meta.json"), json.dumps({"input": inputs["newest50"],
                      "videos": len(tier), "channels": metadata["newest50_channels"],
                      "order": "preserved_from_newest50_snapshot", "queue_sha256": sha256_file(tier_path)}, indent=2) + "\n")
    print(json.dumps({key: metadata[key] for key in ("newest20_items", "newest50_items", "newest50_channels",
                      "total_indexed_items", "remaining_items", "remaining_tabs", "final_round_status")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
