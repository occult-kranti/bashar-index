#!/usr/bin/env python3
"""Assemble per-channel compact JSON files into the SCHEMA.md output array.

Usage: python3 -I build.py <channels_dir> <output_json>

Each channel file ch_NN_*.json has:
  person, role, status, channel (object or null), secondary_channels (list),
  videos_compact: [[video_id, title, view_count_text, published_text, length_text,
                    is_channeling, entity, note], ...],
  earliest_known_video (optional), sources (list)
"""
import glob
import json
import os
import re
import sys

OBSERVED = "2026-10-23"


def parse_views(text):
    if not text:
        return -1
    m = re.match(r"([\d.,]+)\s*([KMB]?)", text.replace(",", ""))
    if not m:
        return -1
    n = float(m.group(1))
    mult = {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[m.group(2)]
    return int(n * mult)


def expand(ch):
    videos = []
    for v in ch.get("videos_compact", []):
        vid, title, views, pub, length, is_ch, entity, note = (list(v) + [None] * 8)[:8]
        videos.append({
            "video_id": vid,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={vid}" if vid else None,
            "view_count_text": views,
            "published_text": pub,
            "published_date": None,
            "length_text": length,
            "is_channeling": bool(is_ch),
            "entity": entity,
            "note": note or "",
        })
    channel = ch.get("channel")
    if channel:
        channel.setdefault("observed_at", OBSERVED)
        if channel.get("channel_id") and not channel.get("rss_url"):
            channel["rss_url"] = (
                "https://www.youtube.com/feeds/videos.xml?channel_id=" + channel["channel_id"]
            )
    ch_videos = [v for v in videos if v["is_channeling"]]
    entities = []
    for v in ch_videos:
        if v["entity"] and v["entity"] not in entities:
            entities.append(v["entity"])
    top = sorted(ch_videos, key=lambda v: parse_views(v["view_count_text"]), reverse=True)[:8]
    summary = {
        "recent_videos_read": len(videos),
        "channeling_videos_in_recent": len(ch_videos),
        "entities_seen": entities,
        "top_channeling_video_ids": [v["video_id"] for v in top],
    }
    if ch.get("earliest_known_video"):
        summary["earliest_known_video"] = ch["earliest_known_video"]
    out = {
        "person": ch["person"],
        "role": ch["role"],
        "status": ch["status"],
        "channel": channel,
        "secondary_channels": ch.get("secondary_channels", []),
        "videos": videos,
        "summary": summary,
        "sources": ch.get("sources", []),
    }
    if ch.get("note"):
        out["note"] = ch["note"]
    return out


def main():
    channels_dir, out_path = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(os.path.join(channels_dir, "ch_*.json")))
    result = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            ch = json.load(fh)
        result.append(expand(ch))
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(f"wrote {len(result)} channels -> {out_path}")
    for r in result:
        s = r["summary"]
        print(f"  {r['person']}: {r['status']} videos={s['recent_videos_read']} channeling={s['channeling_videos_in_recent']}")


if __name__ == "__main__":
    main()
