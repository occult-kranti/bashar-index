#!/usr/bin/env python3
"""Choose which videos to process and write the queue every later step reads.

Sources (public metadata only):
  index     the video rows in youtube-index/youtube_index.json
  bashar75  the 75 Bashar recordings listed in transcripts/scripts/all_ids.txt
  discover  <root>/discover/videos_all.jsonl, written by discover.py (every video on a channel)
Sets:  bashar75 | indexed | channeling | all

    python3 pipeline/select_jobs.py --set bashar75
    python3 pipeline/select_jobs.py --set all --per-channel 20 --seed 7 --min-seconds 300
    python3 pipeline/select_jobs.py --set bashar75 --export-ids ids.json   # input for the Atlas caption tool

A per-channel sample is drawn with a seeded generator and the seed, rule and input hashes are
written next to the queue (queue.meta.json), so the selection can be reproduced and reported.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, ID_RE, add_root_arg, atomic_write_text, layout, parse_duration,  # noqa: E402
                    read_csv, read_jsonl, sha256_file, slug, stable_shard, utc_now, write_csv)

INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
BASHAR_IDS = ET_ROOT / "transcripts" / "scripts" / "all_ids.txt"
BASHAR_CSV = ET_ROOT / "draft-package" / "csv" / "bashar_videos_in_repo_by_channel.csv"
FIELDS = ["video_id", "url", "channel_dir", "title", "duration_s", "channeling", "entity", "sources", "shard"]


def blank(video_id):
    return {"video_id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}", "channel_dir": "",
            "title": "", "duration_s": None, "channeling": None, "entity": "", "sources": set()}


def merge(rows, video_id, source, **fields):
    row = rows.setdefault(video_id, blank(video_id))
    row["sources"].add(source)
    for key, value in fields.items():
        if value not in (None, "") and row.get(key) in (None, ""):
            row[key] = value


def load_sources(root):
    rows, used = {}, {}
    for rec in read_jsonl(layout(root).discover / "videos_all.jsonl"):
        if ID_RE.match(rec.get("video_id", "")):
            merge(rows, rec["video_id"], "discover", title=rec.get("title"), duration_s=rec.get("duration_s"),
                  channel_dir=rec.get("person_id"))
    if (layout(root).discover / "videos_all.jsonl").exists():
        used["discover"] = sha256_file(layout(root).discover / "videos_all.jsonl")
    if INDEX.exists():
        used["youtube_index.json"] = sha256_file(INDEX)
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            for v in channel.get("videos") or []:
                if ID_RE.match(v.get("video_id") or ""):
                    merge(rows, v["video_id"], "index", title=v.get("title"), channel_dir=channel["person"],
                          duration_s=parse_duration(v.get("length_text")), entity=v.get("entity", ""))
                    rows[v["video_id"]]["channeling"] = bool(v.get("is_channeling"))
    if BASHAR_IDS.exists():
        used["all_ids.txt"] = sha256_file(BASHAR_IDS)
        meta = {r["video_id"]: r for r in read_csv(BASHAR_CSV)} if BASHAR_CSV.exists() else {}
        for vid in (x.strip() for x in BASHAR_IDS.read_text(encoding="utf-8").splitlines()):
            if ID_RE.match(vid):
                m = meta.get(vid, {})
                merge(rows, vid, "bashar75", title=m.get("title"), channel_dir=slug(m.get("channel"), "bashar-reuploads"))
    return rows, used


def wanted(row, which):
    s = row["sources"]
    return {"bashar75": "bashar75" in s, "indexed": "index" in s,
            "channeling": "index" in s and row["channeling"] is True, "all": True}[which]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--set", dest="which", choices=("bashar75", "indexed", "channeling", "all"), default="bashar75")
    ap.add_argument("--per-channel", type=int, help="keep at most K videos per channel (seeded sample)")
    ap.add_argument("--seed", type=int, default=20261111)
    ap.add_argument("--min-seconds", type=int, default=0, help="drop videos known to be shorter (Shorts are < 60)")
    ap.add_argument("--max-seconds", type=int, default=0, help="drop videos known to be longer (0 = no limit)")
    ap.add_argument("--order", choices=("longest-first", "shortest-first", "shuffle", "as-is"), default="as-is")
    ap.add_argument("--shards", type=int, default=1, help="add a stable shard number 0..N-1 to each row")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", type=Path, help="queue CSV (default <root>/jobs/queue.csv)")
    ap.add_argument("--export-ids", type=Path, help="also write {records:[{video_id}]} for acquire_youtube.py")
    args = ap.parse_args()

    out = args.out or layout(args.root).jobs / "queue.csv"
    rows, used = load_sources(args.root)
    picked = [r for r in rows.values() if wanted(r, args.which)]
    if args.min_seconds:
        picked = [r for r in picked if r["duration_s"] is None or r["duration_s"] >= args.min_seconds]
    if args.max_seconds:
        picked = [r for r in picked if r["duration_s"] is None or r["duration_s"] <= args.max_seconds]
    picked.sort(key=lambda r: (r["channel_dir"], r["video_id"]))
    if args.per_channel:
        groups = {}
        for r in picked:
            groups.setdefault(r["channel_dir"], []).append(r)
        picked = []
        for chan in sorted(groups):
            group = groups[chan]
            rng = random.Random(f"{args.seed}:{chan}")
            picked += sorted(rng.sample(group, min(args.per_channel, len(group))), key=lambda r: r["video_id"])
    if args.order == "longest-first":
        picked.sort(key=lambda r: (-(r["duration_s"] or 0), r["video_id"]))
    elif args.order == "shortest-first":
        picked.sort(key=lambda r: (r["duration_s"] is None, r["duration_s"] or 0, r["video_id"]))
    elif args.order == "shuffle":
        random.Random(args.seed).shuffle(picked)
    if args.limit:
        picked = picked[:args.limit]

    table = [{**r, "channeling": "" if r["channeling"] is None else int(r["channeling"]),
              "duration_s": "" if r["duration_s"] is None else r["duration_s"],
              "sources": "+".join(sorted(r["sources"])), "shard": stable_shard(r["video_id"], args.shards)}
             for r in picked]
    write_csv(out, table, FIELDS)
    known = [r["duration_s"] for r in picked if r["duration_s"]]
    meta = {"created": utc_now(), "set": args.which, "per_channel": args.per_channel, "seed": args.seed,
            "min_seconds": args.min_seconds, "max_seconds": args.max_seconds, "order": args.order,
            "shards": args.shards, "limit": args.limit, "videos": len(picked),
            "channels": len({r["channel_dir"] for r in picked}), "with_known_duration": len(known),
            "known_hours": round(sum(known) / 3600, 1), "inputs_sha256": used}
    atomic_write_text(out.with_name("queue.meta.json"), json.dumps(meta, indent=2) + "\n")
    if args.export_ids:
        atomic_write_text(args.export_ids, json.dumps({"records": [{"video_id": r["video_id"]} for r in picked]}) + "\n")
    print(f"{len(picked)} videos from {meta['channels']} channels, {meta['known_hours']} h with known length "
          f"({len(picked) - len(known)} unknown) -> {out}")


if __name__ == "__main__":
    main()
