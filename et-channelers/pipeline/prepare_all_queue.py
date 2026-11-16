#!/usr/bin/env python3
"""Merge newest-first, saved full-history and fresh listings without fetching media.

Writes a private queue, an input-hash/coverage sidecar and a readable source-to-person
map. Existing item entity labels are preserved as unverified source metadata;
missing entities remain empty. No alias is promoted to an entity attribution.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, ID_RE, atomic_write_text, ensure_outside_git, latest_by_key,
                    sha256_file, utc_now, write_csv)
from select_jobs import FIELDS

EXTRA_FIELDS = ["source_channel_name", "primary_person_id", "primary_person_name",
                "primary_person_role", "primary_person_basis", "entity_label_basis", "queue_provenance"]


def snapshot(path, kind="csv"):
    """Hash the exact immutable bytes parsed, even if a producer replaces the path."""
    data = path.read_bytes()
    text = data.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text))) if kind == "csv" else [
        json.loads(line) for line in text.splitlines() if line.strip()]
    return rows, {"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest()}


def discovery_rows(path, records=None):
    ranks = collections.Counter()
    rows = []
    for record in snapshot(path, "jsonl")[0] if records is None else records:
        person, tab = record.get("person_id", ""), record.get("tab", "")
        key = (person, tab)
        row = {field: "" for field in FIELDS}
        row.update(video_id=record.get("video_id", ""), channel_dir=person,
                   title=record.get("title") or "", duration_s=record.get("duration_s") or "",
                   tab=tab, listing_rank=ranks[key], sources="discover",
                   upload_date_approx=record.get("upload_date_approx", ""))
        ranks[key] += 1
        rows.append(row)
    return rows


def merge_inputs(newest, saved, fresh):
    """First occurrence owns metadata and position; later inputs fill only blanks."""
    result, provenance = {}, collections.defaultdict(list)
    for label, rows in (("newest20", newest), ("saved_full", saved), ("fresh_discovery", fresh)):
        for original in rows:
            row = dict(original)
            video_id = row.get("video_id", "")
            if not ID_RE.fullmatch(video_id):
                raise ValueError(f"Invalid video ID in {label}")
            if not row.get("channel_dir"):
                raise ValueError(f"Missing source channel in {label}")
            if row.get("tab", "") not in {"", "videos", "streams", "shorts"}:
                raise ValueError(f"Unrecognized tab in {label}")
            row["url"] = f"https://www.youtube.com/watch?v={video_id}"
            if video_id not in result:
                result[video_id] = row
            else:
                kept = result[video_id]
                # A channel's rank is meaningful only within the same source/tab.
                same_channel = kept.get("channel_dir") == row["channel_dir"]
                if same_channel and not kept.get("tab") and kept.get("listing_rank") in (None, ""):
                    kept["tab"], kept["listing_rank"] = row.get("tab", ""), row.get("listing_rank", "")
                elif same_channel and kept.get("tab") and kept.get("tab") == row.get("tab") \
                        and kept.get("listing_rank") in (None, ""):
                    kept["listing_rank"] = row.get("listing_rank", "")
                for key, value in row.items():
                    if key in {"tab", "listing_rank"}:
                        continue
                    if kept.get(key) in (None, "") and value not in (None, ""):
                        kept[key] = value
                sources = set(str(kept.get("sources", "")).split("+")) | set(str(row.get("sources", "")).split("+"))
                kept["sources"] = "+".join(sorted(sources - {""}))
            if label not in provenance[video_id]:
                provenance[video_id].append(label)
    for video_id, row in result.items():
        row["queue_provenance"] = "+".join(provenance[video_id])
    return list(result.values())


def enrich(rows, targets, hosts):
    for row in rows:
        channel = row["channel_dir"]
        target = targets.get(channel, {})
        source_name = target.get("person_name") or hosts.get(row["video_id"], {}).get("channel") or channel
        person_id = channel if target else ""
        basis = "tracked_source_person" if target else "unknown"
        if "bashar75" in str(row.get("sources", "")).split("+"):
            person_id, basis = "darryl-anka", "bashar75_corpus"
        person = targets.get(person_id, {})
        row.update(source_channel_name=source_name, primary_person_id=person_id,
                   primary_person_name=person.get("person_name", ""),
                   primary_person_role=person.get("role", ""), primary_person_basis=basis,
                   entity_label_basis="source_metadata_unverified" if row.get("entity") else "unknown")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--newest", type=Path, required=True)
    parser.add_argument("--existing", type=Path, required=True)
    parser.add_argument("--discover-root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--newest-out", type=Path, help="optional enriched newest subset, preserving its input order")
    args = parser.parse_args(argv)
    ensure_outside_git(args.out.parent)
    if args.newest_out:
        ensure_outside_git(args.newest_out.parent)
    newest, newest_input = snapshot(args.newest)
    saved, saved_input = snapshot(args.existing)
    inputs = {"newest20": newest_input, "saved_full": saved_input}
    fresh, successful = [], set()
    if args.discover_root:
        listing = args.discover_root / "discover" / "videos_all.jsonl"
        records, inputs["fresh_discovery"] = snapshot(listing, "jsonl")
        fresh = discovery_rows(listing, records)
        manifest = args.discover_root / "discover" / "discover_manifest.jsonl"
        records, inputs["discovery_manifest"] = snapshot(manifest, "jsonl")
        states = latest_by_key(records, "person_id")
        successful = {person for person, rec in states.items()
                      if rec.get("status") == "ok" and {"videos", "streams", "shorts"} <= set(rec.get("tabs", {}))}
    if args.out.resolve() in {Path(item["path"]) for item in inputs.values()}:
        parser.error("Output must not overwrite an input snapshot")
    if args.newest_out and args.newest_out.resolve() in {
            args.out.resolve(), *(Path(item["path"]) for item in inputs.values())}:
        parser.error("Enriched newest output must not overwrite the merged queue or an input snapshot")
    target_rows, inputs["person_map"] = snapshot(ET_ROOT / "plan" / "targets.csv")
    host_rows, inputs["host_corpus_map"] = snapshot(ET_ROOT / "draft-package" / "csv" / "bashar_videos_in_repo_by_channel.csv")
    targets = {r["person_id"]: r for r in target_rows}
    hosts = {r["video_id"]: r for r in host_rows}
    rows = enrich(merge_inputs(newest, saved, fresh), targets, hosts)
    write_csv(args.out, rows, FIELDS + EXTRA_FIELDS)
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[row["channel_dir"]].append(row)
    mappings = []
    for channel, items in sorted(grouped.items()):
        mappings.append({"channel_dir": channel, "source_channel_name": items[0]["source_channel_name"],
                         "primary_people": " | ".join(sorted({r["primary_person_name"] for r in items} - {""})),
                         "items": len(items), "tabs": "+".join(sorted({r.get("tab") or "unknown" for r in items})),
                         "items_with_entity_labels": sum(bool(r.get("entity")) for r in items)})
    mapping_path = args.out.with_name(args.out.stem + ".channels.csv")
    write_csv(mapping_path, mappings, ["channel_dir", "source_channel_name", "primary_people", "items", "tabs",
                                       "items_with_entity_labels"])
    tracked = {r["channel_dir"] for r in newest}
    saved_listed = {r["channel_dir"] for r in saved if r.get("tab") in {"videos", "streams", "shorts"}
                    and "discover" in str(r.get("sources", "")).split("+")}
    metadata = {"created": utc_now(), "order": "newest20_then_saved_full_then_new_discoveries",
                "videos": len(rows), "source_directories": len(grouped), "tracked_channels": len(tracked),
                "input_rows": {"newest20": len(newest), "saved_full": len(saved), "fresh_discovery": len(fresh)},
                "tabs": dict(collections.Counter(r.get("tab") or "unknown" for r in rows)),
                "tracked_channels_missing_full_listing": sorted(tracked - saved_listed - successful),
                "fresh_successful_all_tab_channels": sorted(successful), "inputs": inputs,
                "queue_sha256": sha256_file(args.out), "entity_policy": "Preserved item labels are unverified; missing remains unknown.",
                "coverage_note": "Saved listing snapshots are not proof of exhaustive current channel history."}
    atomic_write_text(args.out.with_name(args.out.stem + ".meta.json"), json.dumps(metadata, indent=2) + "\n")
    if args.newest_out:
        by_id = {row["video_id"]: row for row in rows}
        newest_enriched = [by_id[row["video_id"]] for row in newest]
        write_csv(args.newest_out, newest_enriched, FIELDS + EXTRA_FIELDS)
        newest_metadata = {"created": utc_now(), "videos": len(newest_enriched),
                           "channels": len({r["channel_dir"] for r in newest_enriched}),
                           "order": "preserved_from_newest_input", "input": newest_input,
                           "enrichment_queue_sha256": metadata["queue_sha256"],
                           "queue_sha256": sha256_file(args.newest_out),
                           "entity_policy": metadata["entity_policy"]}
        atomic_write_text(args.newest_out.with_name(args.newest_out.stem + ".meta.json"),
                          json.dumps(newest_metadata, indent=2) + "\n")
    print(json.dumps({key: metadata[key] for key in ("videos", "source_directories", "tracked_channels",
                                                   "tabs", "tracked_channels_missing_full_listing")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
