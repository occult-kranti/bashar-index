#!/usr/bin/env python3
"""Choose which non-YouTube items to download and write the queue download_enclosures.py reads.

Sources
  feeds     <root>/feeds/*.jsonl written by fetch_feeds.py.
            relation "own":  every episode belongs to the tracked person.
            relation "host": an interview show; only episodes whose title names a tracked person are kept.
  files     sources/creator_files.csv in the repository: audio files hosted on the maker's own site,
            each with the page that offers it (for example the Kryon free-audio pages).

Every queued item gets a stable id: pod-<16 hex> for a podcast episode, web-<16 hex> for a creator file.
Where the same recording is also a YouTube video in the index, the queue records that id as twin_of,
with how the link was made:
  link    the episode's own show notes link to that YouTube video
  title   the titles share most of their words (and the lengths agree when both are known)
The audio is still labelled with the lane it came from: a podcast edition can differ from the video
(intro, adverts), so it is never counted as a YouTube download.

    python3 pipeline/select_episodes.py                              # everything, no cap
    python3 pipeline/select_episodes.py --per-channel 25 --seed 7    # reproducible sample
    python3 pipeline/select_episodes.py --max-hours 300 --order newest-first

The seed, rules and input hashes are written next to the queue (queue_enclosures.meta.json).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, ID_RE, add_root_arg, atomic_write_text, ensure_outside_git, host_of, item_id,  # noqa: E402
                    layout, parse_duration, read_csv, read_jsonl, sha256_file, stable_shard, utc_now, write_csv)
from feeds import name_pattern, title_similarity  # noqa: E402
from find_feeds import load_targets  # noqa: E402

INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
BASHAR_CSV = ET_ROOT / "draft-package" / "csv" / "bashar_videos_in_repo_by_channel.csv"
CREATOR_FILES = ET_ROOT / "sources" / "creator_files.csv"
FIELDS = ["video_id", "url", "channel_dir", "title", "duration_s", "published", "lane", "relation", "feed_key",
          "guid", "twin_of", "twin_method", "twin_score", "transcript_url", "transcript_type", "bytes_hint", "shard"]
TRANSCRIPT_PREFERENCE = ("text/vtt", "application/x-subrip", "application/srt", "text/srt", "application/json",
                         "text/html", "text/plain")


def known_videos():
    """{person_id: [{video_id, title, duration_s}]} from the committed index and the Bashar-75 list."""
    out = {}
    if INDEX.exists():
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            for video in channel.get("videos") or []:
                if ID_RE.match(video.get("video_id") or ""):
                    out.setdefault(channel["person"], []).append({
                        "video_id": video["video_id"], "title": video.get("title") or "",
                        "duration_s": parse_duration(video.get("length_text"))})
    if BASHAR_CSV.exists():
        have = {v["video_id"] for v in out.get("darryl-anka", [])}
        for row in read_csv(BASHAR_CSV):
            if ID_RE.match(row.get("video_id") or "") and row["video_id"] not in have:
                out.setdefault("darryl-anka", []).append({"video_id": row["video_id"], "title": row.get("title") or "",
                                                          "duration_s": None})
                have.add(row["video_id"])
    return out


def find_twin(episode, videos, min_title, duration_tolerance):
    """(video_id, method, score) of the indexed YouTube video that is the same recording, or ('', '', 0)."""
    by_id = {v["video_id"]: v for v in videos}
    linked = [i for i in episode.get("youtube_ids") or [] if i in by_id]
    if len(linked) == 1:
        return linked[0], "link", 1.0
    best, best_score = None, 0.0
    for video in videos:
        score = title_similarity(episode.get("title", ""), video["title"])
        if score > best_score:
            best, best_score = video, score
    if best and best_score >= min_title:
        a, b = episode.get("duration_s"), best["duration_s"]
        if a and b and abs(a - b) > duration_tolerance * max(a, b):
            return "", "", 0.0
        return best["video_id"], "title", round(best_score, 3)
    return "", "", 0.0


def pick_transcript(episode):
    listed = episode.get("transcripts") or []
    for wanted in TRANSCRIPT_PREFERENCE:
        for entry in listed:
            if entry.get("type") == wanted and entry.get("url"):
                return entry["url"], entry["type"]
    for entry in listed:
        if entry.get("url"):
            return entry["url"], entry.get("type") or ""
    return "", ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--relation", default="own,host,file", help="which kinds to queue: own, host, file")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--per-channel", type=int, help="keep at most K items per person (seeded sample)")
    ap.add_argument("--seed", type=int, default=20261113)
    ap.add_argument("--min-seconds", type=int, default=0, help="drop items known to be shorter")
    ap.add_argument("--max-seconds", type=int, default=0, help="drop items known to be longer (0 = no limit)")
    ap.add_argument("--since", default="", help="keep episodes published on or after YYYY-MM-DD (undated ones are kept)")
    ap.add_argument("--max-hours", type=float, default=0, help="stop adding once the queue holds this many hours")
    ap.add_argument("--assume-minutes", type=float, default=45, help="length assumed for --max-hours when unknown")
    ap.add_argument("--order", choices=("round-robin", "newest-first", "shortest-first", "as-is"), default="round-robin",
                    help="round-robin takes one item per person in turn, so every person starts early")
    ap.add_argument("--keep-trailers", action="store_true")
    ap.add_argument("--min-title", type=float, default=0.72, help="title overlap needed to call a video a twin")
    ap.add_argument("--duration-tolerance", type=float, default=0.12)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", type=Path, help="queue CSV (default <root>/jobs/queue_enclosures.csv)")
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    out = args.out or paths.jobs / "queue_enclosures.csv"
    kinds = {x.strip() for x in args.relation.split(",") if x.strip()}
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    targets = load_targets()
    patterns = [(t["person_id"], name_pattern(t["names"])) for t in targets]
    patterns = [(pid, pat) for pid, pat in patterns if pat is not None]
    videos = known_videos()
    used, rows, seen_urls, seen_titles = {}, [], set(), set()
    dropped = {"trailer": 0, "host_no_tracked_person": 0, "duplicate": 0, "too_short": 0, "too_long": 0, "before_since": 0}

    def add(row, person):
        # Same file twice is a duplicate. Same title is only a duplicate when the lengths are known and
        # equal (one episode carried by two feeds); two creator files can share a title and still differ.
        key = (person, " ".join(row["title"].lower().split()), row["duration_s"])
        if row["url"] in seen_urls or (row["title"] and row["duration_s"] and key in seen_titles):
            dropped["duplicate"] += 1
            return
        if args.min_seconds and row["duration_s"] and row["duration_s"] < args.min_seconds:
            dropped["too_short"] += 1
            return
        if args.max_seconds and row["duration_s"] and row["duration_s"] > args.max_seconds:
            dropped["too_long"] += 1
            return
        if args.since and row["published"] and row["published"] < args.since:
            dropped["before_since"] += 1
            return
        seen_urls.add(row["url"])
        seen_titles.add(key)
        rows.append(row)

    for feed_file in sorted(paths.feeds.glob("*.jsonl")):
        if feed_file.name == "feeds_manifest.jsonl":
            continue
        used[feed_file.name] = sha256_file(feed_file)
        for episode in read_jsonl(feed_file):
            relation = episode.get("relation")
            if relation not in kinds:
                continue
            if episode.get("episode_type") == "trailer" and not args.keep_trailers:
                dropped["trailer"] += 1
                continue
            if relation == "own":
                person = episode["person_id"]
            else:
                person = next((pid for pid, pat in patterns if pat.search(episode.get("title") or "")), "")
                if not person:
                    dropped["host_no_tracked_person"] += 1
                    continue
            if only and person not in only:
                continue
            twin, method, score = find_twin(episode, videos.get(person, []), args.min_title, args.duration_tolerance)
            t_url, t_type = pick_transcript(episode)
            add({"video_id": episode["video_id"], "url": episode["enclosure_url"], "channel_dir": person,
                 "title": episode.get("title") or "", "duration_s": episode.get("duration_s"),
                 "published": episode.get("published") or "", "lane": "pod", "relation": relation,
                 "feed_key": episode["feed_key"], "guid": episode.get("guid") or "", "twin_of": twin,
                 "twin_method": method, "twin_score": score or "", "transcript_url": t_url, "transcript_type": t_type,
                 "bytes_hint": episode.get("enclosure_bytes") or ""}, person)

    if "file" in kinds and CREATOR_FILES.exists():
        used["creator_files.csv"] = sha256_file(CREATOR_FILES)
        for row in read_csv(CREATOR_FILES):
            person, url = row.get("person_id") or "", (row.get("media_url") or "").strip()
            if not person or not host_of(url) or (only and person not in only):
                continue
            twin = row.get("twin_of") or ""
            add({"video_id": item_id("web", url), "url": url, "channel_dir": person, "title": row.get("title") or "",
                 "duration_s": int(float(row["duration_s"])) if row.get("duration_s") else None,
                 "published": row.get("published") or "", "lane": "web", "relation": "file", "feed_key": "",
                 "guid": "", "twin_of": twin if ID_RE.match(twin) else "", "twin_method": "creator-index" if twin else "",
                 "twin_score": "", "transcript_url": "", "transcript_type": "", "bytes_hint": ""}, person)

    rows.sort(key=lambda r: (r["channel_dir"], r["published"] or "", r["video_id"]))
    if args.per_channel:
        groups = {}
        for r in rows:
            groups.setdefault(r["channel_dir"], []).append(r)
        rows = []
        for person in sorted(groups):
            group = groups[person]
            rng = random.Random(f"{args.seed}:{person}")
            rows += sorted(rng.sample(group, min(args.per_channel, len(group))), key=lambda r: r["video_id"])
    if args.order == "newest-first":
        rows.sort(key=lambda r: (r["published"] or "", r["video_id"]), reverse=True)
    elif args.order == "shortest-first":
        rows.sort(key=lambda r: (r["duration_s"] is None, r["duration_s"] or 0, r["video_id"]))
    elif args.order == "round-robin":
        groups = {}
        for r in sorted(rows, key=lambda r: (r["published"] or "", r["video_id"]), reverse=True):
            groups.setdefault(r["channel_dir"], []).append(r)
        rows, depth = [], 0
        while any(len(g) > depth for g in groups.values()):
            rows += [groups[p][depth] for p in sorted(groups) if len(groups[p]) > depth]
            depth += 1
    if args.max_hours:
        kept, total = [], 0.0
        for r in rows:
            seconds = r["duration_s"] or args.assume_minutes * 60
            if total + seconds > args.max_hours * 3600:
                continue
            kept.append(r)
            total += seconds
        rows = kept
    if args.limit:
        rows = rows[:args.limit]

    table = [{**r, "duration_s": "" if r["duration_s"] is None else r["duration_s"],
              "shard": stable_shard(r["video_id"], args.shards)} for r in rows]
    write_csv(out, table, FIELDS)
    known = [r["duration_s"] for r in rows if r["duration_s"]]
    per_person = {}
    for r in rows:
        per_person[r["channel_dir"]] = per_person.get(r["channel_dir"], 0) + 1
    meta = {"created": utc_now(), "relation": sorted(kinds), "only": sorted(only), "per_channel": args.per_channel,
            "seed": args.seed, "min_seconds": args.min_seconds, "max_seconds": args.max_seconds, "since": args.since,
            "max_hours": args.max_hours, "order": args.order, "min_title": args.min_title,
            "duration_tolerance": args.duration_tolerance, "items": len(rows), "people": len(per_person),
            "by_lane": {lane: sum(1 for r in rows if r["lane"] == lane) for lane in ("pod", "web")},
            "by_relation": {k: sum(1 for r in rows if r["relation"] == k) for k in ("own", "host", "file")},
            "with_twin": sum(1 for r in rows if r["twin_of"]),
            "with_publisher_transcript": sum(1 for r in rows if r["transcript_url"]),
            "with_known_duration": len(known), "known_hours": round(sum(known) / 3600, 1),
            "dropped": dropped, "per_person": dict(sorted(per_person.items())), "inputs_sha256": used}
    atomic_write_text(out.with_name(out.stem + ".meta.json"), json.dumps(meta, indent=2) + "\n")
    print(f"{len(rows)} items for {len(per_person)} people ({meta['by_relation']['own']} own-feed, "
          f"{meta['by_relation']['host']} interview, {meta['by_relation']['file']} creator files), "
          f"{meta['known_hours']} h with known length ({len(rows) - len(known)} unknown), "
          f"{meta['with_twin']} matched to an indexed YouTube video, "
          f"{meta['with_publisher_transcript']} with a publisher transcript -> {out}")


if __name__ == "__main__":
    main()
