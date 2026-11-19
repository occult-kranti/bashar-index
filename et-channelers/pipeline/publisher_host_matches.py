"""Screen archived or newly fetched host-podcast catalogues for selected recordings.

Input is fetch_feeds.py's local JSONL output. Matches are private review candidates.
No network transfers, audio substitutions or changes to collection receipts occur.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
import json
from pathlib import Path

try:
    from . import collection_coverage, common, feeds
except ImportError:
    import collection_coverage
    import common
    import feeds


def screen(items, episodes, creator_names):
    by_id = {x["video_id"]: x for x in items}
    duration_by_id = {}
    for row in items:
        durations = {n for d in row.get("duration_or_badges_as_shown", []) if isinstance(d, str) and ":" in d
                     for n in [feeds.parse_duration_text(d)] if n and n > 0}
        if len(durations) == 1:
            duration_by_id[row["video_id"]] = durations.pop()
    timed = sorted((duration, video) for video, duration in duration_by_id.items())
    seconds = [entry[0] for entry in timed]
    reference_counts = Counter((ep["feed_key"], v) for ep in episodes for v in set(ep.get("youtube_ids", [])))
    feed_sizes = Counter(ep["feed_key"] for ep in episodes)
    names = {slug: set(feeds.tokens(name)) for slug, name in creator_names.items()}
    results = []
    for episode in episodes:
        references = set(episode.get("youtube_ids", []))
        # A frequently linked channel trailer is a promotion, as in select_episodes.py.
        exact = {v for v in references & by_id.keys()
                 if reference_counts[episode["feed_key"], v] <= max(1, feeds.PROMO_SHARE * feed_sizes[episode["feed_key"]])}
        candidates = {v: duration_by_id.get(v) for v in exact}
        length = episode.get("duration_s")
        title = episode["title"]
        title_words = set(feeds.tokens(title))
        if isinstance(length, (int, float)) and length > 0:
            delta = max(4, length * 0.01)
            for duration, vid in timed[bisect_left(seconds, length-delta):bisect_right(seconds, length+delta)]:
                who = names.get(by_id[vid]["channel_dir"], set())
                if vid in exact or feeds.title_similarity(title, by_id[vid]["title"]) >= .55 or (len(who) >= 2 and who <= title_words):
                    candidates[vid] = duration
        for vid, observed in sorted(candidates.items()):
            item = by_id[vid]
            results.append({"video_id": vid, "channel_dir": item["channel_dir"], "selected_title": item["title"],
                            "tab": item["tab"], "selected_display_seconds": observed,
                            "feed_key": episode["feed_key"], "episode_id": episode["video_id"],
                            "episode_title": title, "episode_published": episode.get("published"),
                            "episode_seconds": length, "season": episode.get("season_no"), "episode": episode.get("episode_no"),
                            "edition_basis": "item_notes_link" if vid in exact else "runtime_and_title_or_guest",
                            "content_word_similarity": round(feeds.title_similarity(title, item["title"]), 4),
                            "has_publisher_transcript_link": bool(episode.get("transcripts")),
                            "review_status": "candidate"})
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    root, out = common.ensure_outside_git(args.root), common.ensure_outside_git(args.out)
    if not out.is_relative_to(root):
        parser.error("Output must be in the private archive")
    coverage, saved = collection_coverage.coverage(root, selection=args.selection)
    archived = {r["video_id"] for r in saved}
    groups = json.loads(args.selection.read_bytes())["channels"]
    rows = [item for group in groups for item in group["items"] if item["video_id"] not in archived]
    episodes = {}
    for path in sorted((root / "feeds").glob("*.jsonl")):
        if path.name == "feeds_manifest.jsonl":
            continue
        for ep in common.read_jsonl(path):
            if ep.get("relation") == "host" and ep.get("video_id") and ep.get("feed_key"):
                episodes[ep["feed_key"], ep["video_id"]] = ep
    matches = screen(rows, list(episodes.values()), {r["channel_dir"]: r["channel"] for r in coverage["channels"]})
    summary = {"selection_sha256": coverage["selection_sha256"], "generated_at": coverage["generated_at"],
               "remaining_selected_audio": len(rows), "host_episodes_screened": len(episodes),
               "host_feeds": len({k[0] for k in episodes}), "review_candidates": len(matches),
               "by_basis": dict(Counter(r["edition_basis"] for r in matches))}
    common.atomic_write_text(out, json.dumps({**summary, "candidates": matches}, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
