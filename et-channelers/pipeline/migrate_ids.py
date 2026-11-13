#!/usr/bin/env python3
"""One-off: rename podcast items from the first id scheme to the stable one.

The first version of the podcast lane made an episode's id from the feed's address plus the guid, so a
feed that moved would have had every episode downloaded and counted again. Ids are now made from the
person and the guid. After reading the feeds again (fetch_feeds.py --refresh), each episode in
<root>/feeds/*.jsonl carries both: "video_id" (new) and "legacy_id" (old). This script renames what is
already on disk under an old id:

    <root>/audio/<person>/<old>.opus                    -> <new>.opus
    <root>/transcripts/<person>/<old>.json and .txt     -> <new>.json and .txt (the id inside the JSON too)
    <root>/transcripts_publisher/<person>/<old>.*       -> <new>.*

and for each manifest appends a line for the new id (a copy of the old one, with "migrated_from") and a
line that marks the old id "superseded", so nothing is lost from the record and no step counts or
fetches the old id again. Safe to run twice. Without --go it only reports.

Items already uploaded to a store under an old id are reported and left alone: their bundles hold
the old names.

    python3 pipeline/fetch_feeds.py --refresh
    python3 pipeline/migrate_ids.py            # report
    python3 pipeline/migrate_ids.py --go
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (add_root_arg, append_jsonl, archived_ids, atomic_write_text, ensure_outside_git,  # noqa: E402
                    latest_by_key, layout, read_jsonl, sha256_file, utc_now)

KINDS = ("audio", "asr", "pubtext")


def id_map(paths):
    """{old id: new id} from the feed files, leaving out episodes whose id did not change."""
    mapping = {}
    for feed_file in sorted(paths.feeds.glob("*.jsonl")):
        if feed_file.name == "feeds_manifest.jsonl":
            continue
        for episode in read_jsonl(feed_file):
            old, new = episode.get("legacy_id"), episode.get("video_id")
            if old and new and old != new:
                mapping.setdefault(old, new)
    return mapping


def move(src: Path, dst: Path, go: bool) -> bool:
    if not src.exists():
        return False
    if dst.exists():
        raise SystemExit(f"refusing to overwrite {dst}: both the old and the new name exist")
    if go:
        os.replace(src, dst)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--go", action="store_true", help="rename (without this, only report)")
    args = ap.parse_args()
    paths = layout(ensure_outside_git(args.root))
    mapping = id_map(paths)
    stored = set().union(*(archived_ids(paths.root, kind) for kind in KINDS + ("captions",)))
    report = {"ids_that_changed": len(mapping), "audio": 0, "asr": 0, "pubtext": 0, "left_alone_in_a_store": 0}

    jobs = (("audio", paths.audio / "audio_manifest.jsonl", paths.audio, (".opus",)),
            ("asr", paths.transcripts / "transcripts_manifest.jsonl", paths.transcripts, (".json", ".txt")),
            ("pubtext", paths.pubtext / "publisher_text_manifest.jsonl", paths.pubtext, (".txt", ".source")))
    for kind, manifest, folder, suffixes in jobs:
        latest = latest_by_key(read_jsonl(manifest))
        for old, rec in list(latest.items()):
            new = mapping.get(old)
            if not new or rec.get("status") == "superseded" or new in latest:
                continue
            if old in stored:
                report["left_alone_in_a_store"] += 1
                continue
            where = folder / rec.get("channel_dir", "")
            moved = [move(where / f"{old}{suffix}", where / f"{new}{suffix}", args.go) for suffix in suffixes]
            fresh = {**rec, "video_id": new, "migrated_from": old, "migrated_at": utc_now()}
            if rec.get("path"):
                fresh["path"] = rec["path"].replace(old, new)
            if kind == "asr" and args.go and (where / f"{new}.json").exists():
                doc = json.loads((where / f"{new}.json").read_text(encoding="utf-8"))
                doc["video_id"] = new
                atomic_write_text(where / f"{new}.json", json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
                fresh["json_sha256"] = sha256_file(where / f"{new}.json")
            if args.go:
                append_jsonl(manifest, fresh)
                append_jsonl(manifest, {"video_id": old, "channel_dir": rec.get("channel_dir", ""), "status": "superseded",
                                        "superseded_by": new, "at": utc_now()})
            report[kind] += 1 if (any(moved) or rec.get("status") != "ok") else 0
    print(json.dumps({"renamed" if args.go else "would rename": report}, indent=1))
    if not args.go:
        print("report only: add --go to rename", file=sys.stderr)


if __name__ == "__main__":
    main()
