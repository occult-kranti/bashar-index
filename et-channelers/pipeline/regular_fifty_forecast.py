"""Estimate future latest-50 audio time from dated listings and local receipts without scheduling downloads."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path

from . import additive_video_selection, common


def candidates(selection, index, older_rows):
    primary = defaultdict(set)
    for row in selection["rows"]:
        if row.get("fresh_public_regular"):
            primary[row["channel_dir"]].add(row["video_id"])
    owners = {row["channel_dir"]: row["channel_id"] for row in selection["channels"]}
    if (not owners or len(owners) != len(selection["channels"]) or selection.get("latest_regular_per_creator") != 20
            or index.get("per_channel") != 20):
        raise ValueError("Use the dated primary regular-20 selection and its source index")
    older = defaultdict(list)
    for row in older_rows:
        if row["tab"] == "videos":
            older[row["channel_dir"]].append(row)
    channels, items = {}, []
    for group in index["channels"]:
        slug, owner = group["channel_dir"], group["channel_id"]
        if slug in channels or owners.get(slug) != owner or group.get("public_listing_complete") is not True:
            raise ValueError("The forecast needs the same complete public-20 channel listings")
        cards = sorted(group["observed_items"], key=lambda row: row["listing_rank"])
        listed = {r["video_id"] for r in cards}
        if len(listed) != len(cards) or any(r["channel_dir"] != slug or r["observed_primary_channel_id"] != owner for r in cards):
            raise ValueError("An observed card lost its channel identity or is duplicated")
        public = [r["video_id"] for r in cards if r["access_status"] == "public_listing" and r["tab"] == "videos"][:50]
        if set(public[:20]) != primary[slug]:
            raise ValueError("The saved public prefix differs from the latest-20 cohort")
        limit = len(public) if group["exhausted"] else 50
        estimated = list(public)
        past = sorted(older[slug], key=lambda r: int(r["listing_rank"]))
        # Append older ranks only behind the deepest identical video seen in both versions.
        anchor = max((i for i, row in enumerate(past) if row["video_id"] in public), default=-1)
        if anchor >= 0:
            for row in past[anchor + 1:]:
                if len(estimated) == limit:
                    break
                video = row["video_id"]
                if video not in listed and video not in estimated:
                    estimated.append(video)
        channels[slug] = (primary[slug], public, estimated, limit)
        for rank, video in enumerate(estimated):
            items.append(dict(channel_dir=slug, video_id=video, tab="videos", tabs_observed=["videos"],
                              expected_channel_id=owner, listing_rank=rank, fresh_regular=True, fresh_public_regular=True,
                              public_media_dispatch_excluded=False))
    if set(channels) != set(owners):
        raise ValueError("The forecast is missing a channel")
    return channels, items


def workload(channels, saved):
    rows = {}
    for slug, (previous, prefix, estimated, limit) in channels.items():
        known = set(prefix) - previous
        assumed = set(estimated) - previous
        covered = {v for c, v in saved if c == slug}
        rows[slug] = {"latest20": len(previous), "observed": len(prefix), "with_older_list": len(estimated),
                      "ceiling": limit, "saved_beyond20_on_prefix": len(known & covered),
                      "saved_beyond20_with_older_list": len(assumed & covered), "pending_on_prefix": len(known - covered),
                      "pending_with_older_list": len(assumed - covered),
                      "pending_at_ceiling": limit - len(previous) - len(known & covered)}
    totals = {field: sum(row[field] for row in rows.values()) for field in next(iter(rows.values()))}
    return rows, totals


def measured_rate(checkpoints, selection_sha):
    points = sorted({(datetime.fromisoformat(s["generated_at"].replace("Z", "+00:00")), s["summary"]["audio_available"])
                     for s in checkpoints if s.get("selection_sha256") == selection_sha})
    if (len(points) < 2 or any(b[1] < a[1] or b[0] <= a[0] for a, b in zip(points, points[1:]))
            or points[-1][1] <= points[0][1]):
        raise ValueError("Need increasing, comparable receipt checkpoints on one selection")
    def rate(i, j):
        return (points[j][1] - points[i][1]) * 3600 / (points[j][0] - points[i][0]).total_seconds()
    i, hourly = 0, []
    while i < len(points) - 1:
        choices = [(abs(seconds - 3600), j) for j in range(i + 1, len(points))
                   if 2700 <= (seconds := (points[j][0] - points[i][0]).total_seconds()) <= 4800]
        if not choices:
            break
        _, j = min(choices)
        hourly.append(rate(i, j))
        i = j
    return {"first": [points[0][0].isoformat(), points[0][1]], "last": [points[-1][0].isoformat(), points[-1][1]],
            "recordings_per_hour": rate(0, -1), "nonoverlapping_hourly_rates": hourly}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "selection", "index", "older-queue", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--checkpoint", action="append", required=True, type=Path)
    parser.add_argument("--remote", default="etdrive:04 Audio")
    args = parser.parse_args(argv)
    root, out = common.ensure_outside_git(args.root), common.ensure_outside_git(args.out)
    if not out.is_relative_to(root):
        raise ValueError("Write the per-creator forecast in the private archive")
    selection_bytes = args.selection.read_bytes()
    selection, index_bytes = json.loads(selection_bytes), args.index.read_bytes()
    with args.older_queue.open(encoding="utf-8-sig", newline="") as stream:
        channels, rows = candidates(selection, json.loads(index_bytes), csv.DictReader(stream))
    inventory = additive_video_selection.verified_counts({"rows": rows, "channels": selection["channels"]}, root, args.remote)
    saved = {(r["channel_dir"], r["video_id"]) for r in inventory["rows"] if r["verified_audio"]}
    by_creator, totals = workload(channels, saved)
    sha = hashlib.sha256(selection_bytes).hexdigest()
    rate = measured_rate((json.loads(p.read_bytes()) for p in args.checkpoint), sha)
    report = {"selection_sha256": sha, "index_sha256": hashlib.sha256(index_bytes).hexdigest(),
              "older_queue_sha256": hashlib.sha256(args.older_queue.read_bytes()).hexdigest(),
              "start_condition": "latest20_translations_and_both_analysis_rounds_complete", "records": totals,
              "rates": rate, "hours_from_start": {k: totals[k] / rate["recordings_per_hour"] for k in (
                  "pending_on_prefix", "pending_with_older_list", "pending_at_ceiling")}, "by_creator": by_creator}
    common.atomic_write_text(out, json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "by_creator"}))


if __name__ == "__main__":
    main()
