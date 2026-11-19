"""Prepare the next public-50 queue from a completed public-20 cohort and a fresh Videos index."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re

from .additive_video_selection import verified_counts
from .common import ensure_outside_git
from .gpu_asr import kernel_lock


def prepared_queue(previous, fresh, previously_saved):
    """Retain every prior membership and schedule only missing, freely listed recordings."""
    if previous.get("latest_regular_per_creator") != 20 or fresh.get("per_channel") != 50:
        raise ValueError("Expected the completed 20 and newly indexed 50 cohorts")
    previous_owners = {c["channel_dir"]: c["channel_id"] for c in previous["channels"]}
    current_owners = {c["channel_dir"]: c["channel_id"] for c in fresh["channels"]}
    if (previous_owners != current_owners or not previous_owners or
            len(current_owners) != len(fresh["channels"]) or len(previous_owners) != len(previous["channels"])):
        raise ValueError("The new index must cover the same creator roster")
    previous_keys = {(r["channel_dir"], r["video_id"]) for r in previous["rows"] if r.get("fresh_public_regular") is True}
    if not previous_keys or not previous_keys.issubset(previously_saved):
        raise ValueError(f"The previous cohort still needs {len(previous_keys - previously_saved)} recordings")
    rows = []
    seen = set()
    for creator in fresh["channels"]:
        slug, owner = creator["channel_dir"], creator["channel_id"]
        videos = creator["public_items"]
        if (creator.get("public_listing_complete") is not True or len(videos) > 50
                or (len(videos) < 50 and creator.get("exhausted") is not True)):
            raise ValueError(f"Public listing is incomplete for {slug}")
        for rank, item in enumerate(videos):
            video = item["video_id"]
            if (item.get("channel_dir") != slug or item.get("expected_channel_id") != owner
                    or item.get("observed_primary_channel_id") != owner or item.get("public_listing_rank") != rank
                    or item.get("tab") != "videos" or item.get("access_status") != "public_listing"
                    or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video) or video in seen):
                raise ValueError(f"Unverified or duplicate public listing row for {slug}")
            seen.add(video)
            key = (slug, video)
            rows.append({"channel_dir": slug, "channel_id": owner, "video_id": video, "tab": "videos",
                         "listing_rank": rank, "title": item["title"], "url": "https://www.youtube.com/watch?v=" + video,
                         "duration_seconds": item.get("duration_s"), "previous_cohort": key in previous_keys,
                         "verified_audio": key in previously_saved})
    rows.sort(key=lambda r: (r["listing_rank"], r["channel_dir"]))
    new_keys = {(r["channel_dir"], r["video_id"]) for r in rows}
    return {"schema_version": 1, "cohort": "Latest 50 public regular uploads", "channels": len(current_owners),
            "target": len(rows), "already_saved": sum(r["verified_audio"] for r in rows),
            "remaining": sum(not r["verified_audio"] for r in rows),
            "previous_cohort_size": len(previous_keys),
            "previous_cohort_outside_current_50": len(previous_keys - new_keys), "rows": rows}


def publish_inputs(root, previous_path, fresh_path, out, remote):
    root, out = ensure_outside_git(root), ensure_outside_git(out)
    if not out.is_relative_to(root):
        raise ValueError("Queue output must be inside the private root")
    previous_raw, fresh_raw = previous_path.read_bytes(), fresh_path.read_bytes()
    previous, fresh = json.loads(previous_raw), json.loads(fresh_raw)
    candidates = {(r["channel_dir"], r["video_id"]): r for r in previous["rows"] if r.get("fresh_public_regular") is True}
    for group in fresh["channels"]:
        for row in group["public_items"]:
            key = (group["channel_dir"], row["video_id"])
            candidates.setdefault(key, dict(row, tabs_observed=["videos"], fresh_regular=True,
                                             fresh_public_regular=True, public_media_dispatch_excluded=False))
    inventory = verified_counts({"rows": list(candidates.values()), "channels": previous["channels"]}, root, remote)
    saved = {(r["channel_dir"], r["video_id"]) for r in inventory["rows"] if r["verified_audio"]}
    result = prepared_queue(previous, fresh, saved)
    result.update(previous_selection_sha256=hashlib.sha256(previous_raw).hexdigest(),
                  fresh_index_sha256=hashlib.sha256(fresh_raw).hexdigest(), observed_at=fresh["observed_at"])
    output = io.StringIO(newline="")
    fields = ["channel_dir", "channel_id", "video_id", "tab", "listing_rank", "title", "url", "duration_seconds"]
    writer = csv.DictWriter(output, fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(row for row in result["rows"] if not row["verified_audio"])
    queue = output.getvalue().encode("utf-8")
    result["pending_csv_sha256"] = hashlib.sha256(queue).hexdigest()
    out.mkdir(parents=True, exist_ok=True)
    files = {"pending.csv": queue, "selection.json": (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()}
    with kernel_lock(out/"plan.lock"):
        for name, data in files.items():
            target = out/name
            if target.exists() and target.read_bytes() != data:
                raise ValueError("Choose a new output directory for a changed index or receipt inventory")
        for name, data in files.items():
            target = out/name
            if not target.exists():
                temporary = target.with_suffix(target.suffix + ".part")
                temporary.write_bytes(data)
                os.replace(temporary, target)
    return {k: v for k, v in result.items() if k != "rows"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "previous", "fresh", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--remote", default="etdrive:04 Audio")
    args = parser.parse_args()
    print(json.dumps(publish_inputs(args.root, args.previous, args.fresh, args.out, args.remote)))


if __name__ == "__main__":
    main()
