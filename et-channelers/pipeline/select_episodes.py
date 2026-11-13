#!/usr/bin/env python3
"""Choose which non-YouTube items to download and write the queue download_enclosures.py reads.

Sources
  feeds     <root>/feeds/*.jsonl written by fetch_feeds.py, for feeds the registry accepts today.
            relation "own":  every episode belongs to the tracked person.
            relation "host": an interview show; only episodes whose title names a tracked person are kept.
  files     sources/creator_files.csv in the repository: audio files hosted on the maker's own site,
            each with the page that offers it (for example the Kryon free-audio pages).

Every queued item gets a stable id: pod-<16 hex> for a podcast episode, web-<16 hex> for a creator file.
Where the same recording is also a YouTube video in the index, the queue records that id as twin_of,
with how the link was made:
  link    the episode's own show notes link to that video (a link that sits in more than a fifth of a
          feed's episodes is a promotion, not that episode's video, and is ignored)
  title   the titles share most of their words, every number in them agrees (Day 10 is not Day 11),
          and both lengths are known and within the tolerance
A title match whose lengths cannot be compared is written to twin_candidate instead and is not
counted as a twin. One video is the twin of at most one item: the best match keeps it.
The audio is still labelled with the lane it came from: a podcast edition can differ from the video
(intro, adverts), so it is never counted as a YouTube download.

Interview shows. A title must carry a person's full name (accents and case ignored) or one of their
strong aliases. An alias marked weak in sources/extra_targets.csv (a phrase such as "Law of One")
cannot assign an episode by itself, and a title that names two tracked people equally is left for a
person to sort out rather than given to whoever comes first.

    python3 pipeline/select_episodes.py                              # everything, no cap
    python3 pipeline/select_episodes.py --per-channel 25 --seed 7    # reproducible sample
    python3 pipeline/select_episodes.py --max-hours 300 --order newest-first

The seed, rules and input hashes are written next to the queue (queue_enclosures.meta.json).
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, ID_RE, add_root_arg, atomic_write_text, ensure_outside_git, host_of, item_id,  # noqa: E402
                    layout, listed_videos, parse_duration, read_csv, read_jsonl, sha256_file, stable_shard, utc_now,
                    write_csv)
from feeds import title_similarity, tokens  # noqa: E402
from fetch_feeds import REGISTRY, read_registry  # noqa: E402
from find_feeds import fold, load_targets  # noqa: E402

INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
BASHAR_CSV = ET_ROOT / "draft-package" / "csv" / "bashar_videos_in_repo_by_channel.csv"
CREATOR_FILES = ET_ROOT / "sources" / "creator_files.csv"
EXTRA_TARGETS = ET_ROOT / "sources" / "extra_targets.csv"
FIELDS = ["video_id", "url", "channel_dir", "title", "duration_s", "published", "lane", "relation", "feed_key",
          "guid", "twin_of", "twin_method", "twin_score", "twin_candidate", "transcript_url", "transcript_type",
          "bytes_hint", "shard"]
TRANSCRIPT_PREFERENCE = ("text/vtt", "application/x-subrip", "application/srt", "text/srt", "application/json",
                         "text/html", "text/plain")
PROMO_SHARE = 0.2     # a video linked from more than this share of a feed's episodes is a promotion
DEFAULTS = {"relation": "own,host,file", "only": "", "min_seconds": 0, "max_seconds": 0, "since": "",
            "keep_trailers": False, "min_title": 0.72, "duration_tolerance": 0.12, "registry": REGISTRY,
            "accept": "verified,name-match"}


def known_videos(paths=None):
    """{person_id: [{video_id, title, duration_s}]} from the committed index, the Bashar-75 list and, when
    the private folder holds them, the channel listings discover.py wrote (videos and live streams;
    shorts carry no length and are never the twin of an episode)."""
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
    if paths is not None:
        have = {v["video_id"]: v for group in out.values() for v in group}
        for row in listed_videos(paths.root):
            vid = row.get("video_id") or ""
            if not ID_RE.match(vid) or (row.get("tab") or "videos") == "shorts" or not row.get("person_id"):
                continue
            if vid in have:                                   # the index knew the title; the listing knows the length
                have[vid]["duration_s"] = have[vid]["duration_s"] or row.get("duration_s")
                continue
            have[vid] = {"video_id": vid, "title": row.get("title") or "", "duration_s": row.get("duration_s")}
            out.setdefault(row["person_id"], []).append(have[vid])
    return out


def numbers_in(title: str):
    """The numbers a title carries, as a sorted list, without calendar years (2019 in one edition's
    title and not in the other's is common and says nothing about which recording it is)."""
    return sorted(n.lstrip("0") or "0" for n in re.findall(r"\d+", title or "") if not re.fullmatch(r"(?:19|20)\d\d", n))


def find_twin(episode, videos, min_title, duration_tolerance, promo=()):
    """(video_id, method, score, candidate). `video_id` is set only for a match that is safe to count.
    `candidate` is a title match whose lengths could not be compared: worth a look, not counted."""
    by_id = {v["video_id"]: v for v in videos}
    linked = [i for i in episode.get("youtube_ids") or [] if i in by_id and i not in promo]
    if len(linked) == 1:
        return linked[0], "link", 1.0, ""
    best, best_score = None, 0.0
    for video in videos:
        if numbers_in(episode.get("title", "")) != numbers_in(video["title"]):
            continue          # Day 10 and Day 11, Part 1 and Part 2: different recordings
        score = title_similarity(episode.get("title", ""), video["title"])
        if score > best_score:
            best, best_score = video, score
    if not best or best_score < min_title or len(tokens(best["title"])) < 2:
        return "", "", 0.0, ""
    a, b = episode.get("duration_s"), best["duration_s"]
    if not a or not b:
        return "", "", 0.0, best["video_id"]
    if abs(a - b) > duration_tolerance * max(a, b):
        return "", "", 0.0, ""
    return best["video_id"], "title", round(best_score, 3), ""


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


# ---------------------------------------------------------------- who an interview episode is about
def weak_aliases():
    """{person_id: set(folded alias)} for aliases marked weak in extra_targets.csv (column weak_aliases)."""
    out = {}
    for row in read_csv(EXTRA_TARGETS) if EXTRA_TARGETS.exists() else []:
        for alias in (row.get("weak_aliases") or "").split("|"):
            if alias.strip():
                out.setdefault(row["person_id"], set()).add(" ".join(re.findall(r"[^\W_]+", fold(alias))))
    return out


def name_parts(name: str):
    """'JZ Knight / Ramtha' -> ['jz knight', 'ramtha']; 'Jordan Younger (The Balanced Blonde)' ->
    ['jordan younger', 'the balanced blonde']. Folded, so accents and case do not matter."""
    parts = re.split(r"[/()\[\]|]| - ", name or "")
    return [" ".join(re.findall(r"[^\W_]+", fold(p))) for p in parts if re.findall(r"[^\W_]+", fold(p))]


def matchers(targets):
    """[(person_id, compiled pattern, strength, text)] where strength 2 is the person's own name of two
    or more words, 1 another strong name or alias, 0 an alias marked weak."""
    weak, out = weak_aliases(), []
    for target in targets:
        seen = set()
        for position, name in enumerate(target["names"]):
            for part in name_parts(name):
                if part in seen or sum(len(w) for w in part.split()) < 4:
                    continue
                seen.add(part)
                words = part.split()
                if part in weak.get(target["person_id"], ()):
                    strength = 0
                elif position == 0 and len(words) >= 2:
                    strength = 2
                else:
                    strength = 1
                pattern = re.compile(r"(?<![^\W_])" + r"[\W_]+".join(re.escape(w) for w in words) + r"(?![^\W_])")
                out.append((target["person_id"], pattern, strength, part))
    return out


def assign_person(title: str, rules):
    """(person_id, why). '' when nobody is named, when only a weak alias matches, or when the title
    names two tracked people equally strongly."""
    folded = " ".join(re.findall(r"[^\W_]+", fold(title)))
    best = {}
    for person, pattern, strength, part in rules:
        found = pattern.search(folded)
        if not found:
            continue
        if part == "bashar" and re.match(r"\s*al\b", folded[found.end():]):
            continue            # Bashar al-Assad is somebody else
        best[person] = max(best.get(person, -1), strength)
    strong = {p: s for p, s in best.items() if s >= 1}
    if not strong:
        return "", "weak_alias_only" if best else "nobody_named"
    top = max(strong.values())
    winners = sorted(p for p, s in strong.items() if s == top)
    if len(winners) > 1:
        return "", "ambiguous"
    return winners[0], "named"


# ---------------------------------------------------------------- everything that could be queued
def collect(paths, opts=None):
    """(rows, dropped, used input hashes): every item the source lists hold, with twins worked out and
    duplicates removed, before any sampling or limit. catalog.py uses this as the list of what exists."""
    o = {**DEFAULTS, **(opts or {})}
    kinds = {x.strip() for x in o["relation"].split(",") if x.strip()}
    only = {x.strip() for x in str(o["only"]).split(",") if x.strip()}
    rules = matchers(load_targets())
    videos = known_videos(paths)
    used, rows, seen_urls, seen_titles, seen_ids = {}, [], set(), set(), set()
    dropped = collections.Counter({k: 0 for k in ("trailer", "host_no_tracked_person", "host_ambiguous", "duplicate",
                                                  "too_short", "too_long", "before_since", "feed_not_in_registry")})

    def add(row, person):
        key = (person, " ".join(row["title"].lower().split()), row["duration_s"])
        # Same file or same id twice is a duplicate. Same title is only a duplicate when the lengths are
        # known and equal (one episode carried by two feeds); two creator files can share a title.
        if row["url"] in seen_urls or row["video_id"] in seen_ids \
                or (row["title"] and row["duration_s"] and key in seen_titles):
            dropped["duplicate"] += 1
            return
        if o["min_seconds"] and row["duration_s"] and row["duration_s"] < o["min_seconds"]:
            dropped["too_short"] += 1
            return
        if o["max_seconds"] and row["duration_s"] and row["duration_s"] > o["max_seconds"]:
            dropped["too_long"] += 1
            return
        if o["since"] and row["published"] and row["published"] < o["since"]:
            dropped["before_since"] += 1
            return
        seen_urls.add(row["url"])
        seen_ids.add(row["video_id"])
        seen_titles.add(key)
        rows.append(row)

    # Only feeds the registry accepts today are read. A feed that was rejected, or that moved and left
    # its old episode list behind, must not keep feeding the queue.
    accepted = {row["feed_key"] for row in read_registry(o["registry"], {x.strip() for x in o["accept"].split(",") if x.strip()})}
    # Two accepted feeds can hold the same episode (a show listed at an old and a new address). The copy
    # from the feed that was read successfully most recently is the live one, so those files go first;
    # a feed whose last read failed goes last and only contributes episodes nothing else has.
    last_read = {}
    for rec in read_jsonl(paths.feeds / "feeds_manifest.jsonl"):
        if rec.get("feed_key"):
            last_read[rec["feed_key"]] = (rec.get("status") == "ok", rec.get("started", ""))

    def freshness(feed_file):
        ok, when = last_read.get(feed_file.stem, (False, ""))
        return (not ok, "".join(chr(255 - ord(c)) for c in when), feed_file.name)   # ok first, then newest first

    for feed_file in sorted(paths.feeds.glob("*.jsonl"), key=freshness):
        if feed_file.name == "feeds_manifest.jsonl":
            continue
        if feed_file.stem not in accepted:
            dropped["feed_not_in_registry"] += 1
            continue
        used[feed_file.name] = sha256_file(feed_file)
        episodes = read_jsonl(feed_file)
        linked = collections.Counter(i for e in episodes for i in set(e.get("youtube_ids") or []))
        promo = {i for i, n in linked.items() if n > max(1, PROMO_SHARE * len(episodes))}
        for episode in episodes:
            relation = episode.get("relation")
            if relation not in kinds:
                continue
            if episode.get("episode_type") == "trailer" and not o["keep_trailers"]:
                dropped["trailer"] += 1
                continue
            if relation == "own":
                person = episode["person_id"]
            else:
                person, why = assign_person(episode.get("title") or "", rules)
                if not person:
                    dropped["host_ambiguous" if why == "ambiguous" else "host_no_tracked_person"] += 1
                    continue
            if only and person not in only:
                continue
            twin, method, score, candidate = find_twin(episode, videos.get(person, []), o["min_title"],
                                                       o["duration_tolerance"], promo)
            t_url, t_type = pick_transcript(episode)
            add({"video_id": episode["video_id"], "url": episode["enclosure_url"], "channel_dir": person,
                 "title": episode.get("title") or "", "duration_s": episode.get("duration_s"),
                 "published": episode.get("published") or "", "lane": "pod", "relation": relation,
                 "feed_key": episode["feed_key"], "guid": episode.get("guid") or "", "twin_of": twin,
                 "twin_method": method, "twin_score": score or "", "twin_candidate": candidate,
                 "transcript_url": t_url, "transcript_type": t_type,
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
                 "twin_score": "", "twin_candidate": "", "transcript_url": "", "transcript_type": "",
                 "bytes_hint": ""}, person)

    # one video is the twin of at most one item: a link beats a creator index, which beats a title match
    rank = {"link": 3, "creator-index": 2, "title": 1}
    holder = {}
    for row in rows:
        if row["twin_of"]:
            score = (rank.get(row["twin_method"], 0), float(row["twin_score"] or 0))
            if row["twin_of"] not in holder or score > holder[row["twin_of"]][0]:
                holder[row["twin_of"]] = (score, row["video_id"])
    for row in rows:
        if row["twin_of"] and holder[row["twin_of"]][1] != row["video_id"]:
            row.update(twin_candidate=row["twin_of"], twin_of="", twin_method="", twin_score="")
    return rows, dict(dropped), used


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--relation", default=DEFAULTS["relation"], help="which kinds to queue: own, host, file")
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
    ap.add_argument("--min-title", type=float, default=DEFAULTS["min_title"], help="title overlap needed to call a video a twin")
    ap.add_argument("--duration-tolerance", type=float, default=DEFAULTS["duration_tolerance"])
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--registry", type=Path, default=REGISTRY, help="feed registry (default sources/podcast_feeds.csv)")
    ap.add_argument("--accept", default=DEFAULTS["accept"], help="verification values whose feeds are read")
    ap.add_argument("--out", type=Path, help="queue CSV (default <root>/jobs/queue_enclosures.csv)")
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    out = args.out or paths.jobs / "queue_enclosures.csv"
    ensure_outside_git(out.parent)       # the queue holds titles and addresses: never inside a checkout
    rows, dropped, used = collect(paths, {k: getattr(args, k) for k in DEFAULTS})
    kinds = sorted({x.strip() for x in args.relation.split(",") if x.strip()})
    only = sorted({x.strip() for x in args.only.split(",") if x.strip()})

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
    meta = {"created": utc_now(), "relation": kinds, "only": only, "per_channel": args.per_channel,
            "seed": args.seed, "min_seconds": args.min_seconds, "max_seconds": args.max_seconds, "since": args.since,
            "max_hours": args.max_hours, "order": args.order, "min_title": args.min_title,
            "duration_tolerance": args.duration_tolerance, "items": len(rows), "people": len(per_person),
            "by_lane": {lane: sum(1 for r in rows if r["lane"] == lane) for lane in ("pod", "web")},
            "by_relation": {k: sum(1 for r in rows if r["relation"] == k) for k in ("own", "host", "file")},
            "with_twin": sum(1 for r in rows if r["twin_of"]),
            "with_twin_candidate": sum(1 for r in rows if r["twin_candidate"]),
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
