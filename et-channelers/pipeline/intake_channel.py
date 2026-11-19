#!/usr/bin/env python3
"""Append one completed flat channel listing to private queues, with backups.

No network, media, captions, transcript analysis or job launch. Run without
--apply to review counts. Existing queue rows keep their metadata and order.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ID_RE, atomic_write_text, ensure_outside_git, utc_now
from drive_ingest import MAX_LOCAL_BYTES, MIN_FREE_BYTES, exclusive_lock, managed_roots, reserved_project_growth, storage_usage
from prepare_all_queue import EXTRA_FIELDS
from prepare_collection_stages import grouped_index, validate_tier
from select_jobs import FIELDS

TABS = ("videos", "streams", "shorts")
LANES = {"queue_newest20.csv": 20, "queue_newest20_enriched.csv": 20,
         "queue_newest50.csv": 50, "queue_newest50_enriched.csv": 50,
         "queue_youtube_all_merged.csv": None}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def csv_bytes(rows, fields):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("utf-8")


def csv_snapshot(data):
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    fields = reader.fieldnames
    rows = list(reader)
    if not fields or "video_id" not in fields:
        raise ValueError("Queue lacks its video ID field")
    if any(None in row for row in rows):
        raise ValueError("Malformed CSV row")
    return rows, fields


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def flatten_listing(data, person, name, role, expected_channel):
    if data.get("channel_id") != expected_channel:
        raise ValueError("Canonical channel ID differs from the expected identity")
    tabs = {}
    def visit(node):
        children = node.get("entries")
        if not isinstance(children, list):
            return
        tab = urlsplit(node.get("webpage_url", "")).path.rstrip("/").rsplit("/", 1)[-1]
        if tab in TABS and not any(isinstance(x, dict) and "entries" in x for x in children):
            if tab in tabs:
                raise ValueError("Duplicate source tab")
            tabs[tab] = children
        else:
            for child in children:
                if isinstance(child, dict):
                    visit(child)
    visit(data)
    if "videos" not in tabs:
        raise ValueError("No explicit Videos-tab listing; cannot build newest lanes")
    if any(len(entries) >= 20000 for entries in tabs.values()):
        raise ValueError("A source tab reached the extraction cap; coverage is incomplete")
    rows, excluded, seen = [], [], set()
    for tab in TABS:
        for rank, entry in enumerate(tabs.get(tab, [])):
            video_id = entry.get("id", "")
            if not ID_RE.fullmatch(video_id):
                raise ValueError("Flat listing contains an invalid video ID")
            owner = entry.get("channel_id")
            if owner and owner != expected_channel:
                raise ValueError("Flat listing contains a different channel owner")
            if video_id in seen:
                continue
            seen.add(video_id)
            if entry.get("live_status") in {"is_live", "is_upcoming", "post_live"}:
                excluded.append({"video_id": video_id, "tab": tab, "source_rank": rank,
                                 "reason": entry["live_status"]})
                continue
            date = entry.get("upload_date") or ""
            if not date and isinstance(entry.get("timestamp"), (int, float)):
                date = dt.datetime.fromtimestamp(entry["timestamp"], dt.timezone.utc).strftime("%Y%m%d")
            row = {key: "" for key in FIELDS + EXTRA_FIELDS}
            row.update(video_id=video_id, url=f"https://www.youtube.com/watch?v={video_id}",
                       channel_dir=person, title=entry.get("title") or "",
                       duration_s=str(entry.get("duration")) if entry.get("duration") is not None else "",
                       sources="discover", tab=tab, listing_rank=str(rank), upload_date_approx=date,
                       source_channel_name=data.get("channel") or name, primary_person_id=person,
                       primary_person_name=name, primary_person_role=role,
                       primary_person_basis="tracked_source_person", entity_label_basis="unknown",
                       queue_provenance="channel_intake")
            rows.append(row)
    if not rows:
        raise ValueError("No completed items were listed")
    return rows, {tab: len(tabs.get(tab, [])) for tab in TABS}, excluded


def append_only(existing, incoming):
    ids = [row["video_id"] for row in existing]
    if len(ids) != len(set(ids)) or any(not ID_RE.fullmatch(x) for x in ids):
        raise ValueError("Existing queue contains invalid or duplicate IDs")
    seen, added = set(ids), []
    for row in incoming:
        if row["video_id"] not in seen:
            seen.add(row["video_id"])
            added.append(dict(row))
    return [dict(row) for row in existing] + added, len(added)


def build_plan(root, flat_path, person, name, role, channel_id):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", person):
        raise ValueError("Unsafe person ID")
    if not re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel_id):
        raise ValueError("Invalid canonical channel ID")
    raw = flat_path.read_bytes()
    source = json.loads(raw)
    incoming, source_tabs, excluded = flatten_listing(source, person, name, role, channel_id)
    before, after, queue_rows, additions = {}, {}, {}, {}
    jobs = root / "jobs"
    created = utc_now()

    def capture(path):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if rel not in before:
            before[rel] = path.read_bytes() if path.exists() else None
        return rel

    def emit(path, payload):
        after[capture(path)] = payload

    for filename, limit in LANES.items():
        path = jobs / filename
        previous = before[capture(path)]
        if previous is None:
            raise ValueError("An existing queue is missing")
        old, fields = csv_snapshot(previous)
        if any(row["channel_dir"] == person for row in old):
            raise ValueError("Channel already occurs in a queue; use a separately reviewed refresh")
        new = [r for r in incoming if limit is None or
               (r["tab"] == "videos" and int(r["listing_rank"]) < limit)]
        merged, count = append_only(old, new)
        if any(set(row) - set(fields) for row in new):
            raise ValueError("Input queue schema cannot preserve intake metadata")
        assert merged[:len(old)] == old
        queue_rows[filename], additions[filename] = merged, count
        payload = csv_bytes(merged, fields)
        emit(path, payload)
        meta_path = path.with_suffix(".meta.json")
        meta_bytes = before[capture(meta_path)]
        old_meta = json.loads(meta_bytes) if meta_bytes is not None else {}
        meta = {"schema_version": 2, "created": created, "operation": "append_channel_intake",
                "person_id": person, "channel_id": channel_id, "videos": len(merged),
                "channels": len({r["channel_dir"] for r in merged}), "added_items": count,
                "order": "existing_order_then_new_channel_tab_order", "duration_filter": None,
                "queue_sha256": digest(payload), "previous_csv_sha256": digest(previous),
                "source_snapshot": {"path": str(flat_path.resolve()), "sha256": digest(raw)},
                "previous_metadata": old_meta}
        emit(meta_path, json_bytes(meta))

    twenty = queue_rows["queue_newest20_enriched.csv"]
    fifty = queue_rows["queue_newest50_enriched.csv"]
    full = queue_rows["queue_youtube_all_merged.csv"]
    ids20, ids50 = validate_tier(twenty, 20), validate_tier(fifty, 50)
    full_ids = {r["video_id"] for r in full}
    if not ids20 <= ids50 <= full_ids:
        raise ValueError("New tiers are not nested within the full queue")
    if len({r["channel_dir"] for r in twenty}) != len({r["channel_dir"] for r in fifty}):
        raise ValueError("Priority channel coverage differs")
    remaining = [r for r in full if r["video_id"] not in ids50]
    groups = grouped_index(remaining)
    final_path, groups_path = jobs / "queue_final_round.csv", jobs / "final_round_by_channel_tab.csv"
    emit(final_path, csv_bytes(remaining, list(full[0])))
    emit(groups_path, csv_bytes(groups, ["channel_dir", "source_channel_name", "primary_people",
         "tab", "items", "known_duration_hours", "unknown_duration_items"]))
    by_channel = collections.defaultdict(list)
    for row in full:
        by_channel[row["channel_dir"]].append(row)
    mappings = [{"channel_dir": key, "source_channel_name": items[0].get("source_channel_name", key),
                 "primary_people": " | ".join(sorted({r.get("primary_person_name", "") for r in items} - {""})),
                 "items": len(items), "tabs": "+".join(sorted({r.get("tab") or "unknown" for r in items})),
                 "items_with_entity_labels": sum(bool(r.get("entity")) for r in items)}
                for key, items in sorted(by_channel.items())]
    emit(jobs / "queue_youtube_all_merged.channels.csv", csv_bytes(mappings,
         ["channel_dir", "source_channel_name", "primary_people", "items", "tabs", "items_with_entity_labels"]))
    stage_path = jobs / "collection_stages.meta.json"
    stage_bytes = before[capture(stage_path)]
    previous_stage = json.loads(stage_bytes) if stage_bytes is not None else {}
    inputs = {key: {"path": str(jobs / filename),
                   "sha256": digest(after["jobs/" + filename])}
              for key, filename in {"newest20": "queue_newest20_enriched.csv",
                 "newest50": "queue_newest50.csv", "full_catalog": "queue_youtube_all_merged.csv"}.items()}
    stages = {"created": created, "inputs": inputs, "newest20_items": len(twenty),
              "newest50_items": len(fifty), "newest50_channels": len({r["channel_dir"] for r in fifty}),
              "total_indexed_items": len(full), "remaining_items": len(remaining),
              "remaining_tabs": dict(collections.Counter(r.get("tab") or "unknown" for r in remaining)),
              "duration_filter": None, "final_round_status": previous_stage.get("final_round_status", "indexed_only_not_started"),
              "previous_metadata": previous_stage,
              "outputs": {key: {"path": str(jobs / filename), "sha256": digest(after["jobs/" + filename])}
                 for key, filename in {"newest50": "queue_newest50_enriched.csv",
                     "remaining": "queue_final_round.csv", "groups": "final_round_by_channel_tab.csv"}.items()}}
    emit(stage_path, json_bytes(stages))

    discovered = [{"video_id": r["video_id"], "title": r["title"], "duration_s": r["duration_s"],
                   "person_id": person, "tab": r["tab"], "upload_date_approx": r["upload_date_approx"]}
                  for r in incoming]
    listing = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in discovered).encode("utf-8")
    channel_path = root / "discover" / "channels" / f"{person}.jsonl"
    if channel_path.exists():
        raise ValueError("Discovery file already exists; refusing a silent refresh")
    emit(channel_path, listing)
    for filename, extra in [
        ("videos_all.jsonl", listing),
        ("discover_manifest.jsonl", (json.dumps({"person_id": person,
            "channel_url": f"https://www.youtube.com/channel/{channel_id}/videos", "started": created,
            "status": "ok", "n_videos": len(incoming), "tabs": dict(collections.Counter(r["tab"] for r in incoming)),
            "source_tabs": source_tabs, "excluded_unfinished": len(excluded),
            "snapshot_sha256": digest(raw), "coverage_note": "One completed flat extraction; source may change."}) + "\n").encode())]:
        path = root / "discover" / filename
        prior = before[capture(path)] or b""
        emit(path, prior + (b"\n" if prior and not prior.endswith(b"\n") else b"") + extra)
    summary = {"created": created, "person_id": person, "channel_id": channel_id,
               "source_tabs": source_tabs, "source_items": len(incoming), "excluded_unfinished": excluded,
               "newest20_items": len(twenty), "newest50_items": len(fifty), "full_items": len(full),
               "remaining_items": len(remaining), "tracked_channels": len({r["channel_dir"] for r in fifty}),
               "source_directories": len(by_channel), "additions": additions,
               "snapshot_sha256": digest(raw), "duration_filter": None,
               "entity_attribution": "Unknown per item; a channel owner is not automatically an episode speaker."}
    return before, after, summary


def publish(root, before, after, summary):
    # Account for durable backups, staged outputs, replacement growth and one
    # largest atomic-write temporary. Keep the project's agreed private cap.
    previous_bytes = sum(len(v) for v in before.values() if v is not None)
    output_bytes = sum(len(v) for v in after.values())
    extra_bytes = previous_bytes + output_bytes + max(0, output_bytes - previous_bytes) \
        + max(map(len, after.values()), default=0) + 1_000_000
    _, used = storage_usage(root, managed_roots(root))
    outstanding = reserved_project_growth(root)
    if used + outstanding + extra_bytes > MAX_LOCAL_BYTES:
        raise ValueError("Intake staging would exceed the managed project cap")
    if shutil.disk_usage(root).free - outstanding - extra_bytes < MIN_FREE_BYTES:
        raise ValueError("Insufficient disk headroom for intake staging")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = root / "jobs" / "queue_backups" / f"{summary['person_id']}_{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    for rel, payload in before.items():
        if payload is not None:
            destination = backup / "before" / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
    for rel, payload in after.items():
        destination = backup / "after" / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    receipt = {**summary, "status": "prepared", "backup_dir": str(backup),
               "before": {k: digest(v) if v is not None else None for k, v in before.items()},
               "after": {k: digest(v) for k, v in after.items()}}
    atomic_write_text(backup / "intake_receipt.json", json_bytes(receipt).decode())
    for rel, original in before.items():
        path = root / rel
        actual = path.read_bytes() if path.exists() else None
        if actual != original:
            raise RuntimeError("An intake input changed; nothing published. Review staged backup.")
    written = []
    try:
        for rel, payload in after.items():
            atomic_write_text(root / rel, payload.decode("utf-8"))
            written.append(rel)
        if any((root / rel).read_bytes() != payload for rel, payload in after.items()):
            raise RuntimeError("Published bytes differ from staged output")
    except BaseException:
        for rel in reversed(written):
            path, original = root / rel, before[rel]
            if path.read_bytes() != after[rel]:
                raise RuntimeError("Concurrent output change: manual recovery required from backup")
            if original is None:
                path.unlink()
            else:
                atomic_write_text(path, original.decode("utf-8"))
        receipt["status"] = "rolled_back"
        atomic_write_text(backup / "intake_receipt.json", json_bytes(receipt).decode())
        raise
    receipt["status"] = "committed"
    atomic_write_text(backup / "intake_receipt.json", json_bytes(receipt).decode())
    atomic_write_text(root / "jobs" / f"{summary['person_id'].replace('-', '_')}_intake.json",
                      json_bytes(receipt).decode())
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--person-id", required=True)
    parser.add_argument("--person-name", required=True)
    parser.add_argument("--role", default="interview_host")
    parser.add_argument("--channel-id", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    ensure_outside_git(root)
    if args.apply:
        with exclusive_lock(root):
            before, after, summary = build_plan(root, args.snapshot, args.person_id, args.person_name, args.role, args.channel_id)
            summary = publish(root, before, after, summary)
    else:
        _, _, summary = build_plan(root, args.snapshot, args.person_id, args.person_name, args.role, args.channel_id)
    print(json.dumps({k: v for k, v in summary.items() if k not in {"before", "after"}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
