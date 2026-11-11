"""Build per-channel JSON files from a saved alexandria result + a classification spec.

spec file: JSON list of objects:
{
  "channel_id": "UC...",            # which result item to use
  "out": "09_goodchild.json",
  "person": "Blossom Goodchild",
  "role": "channeler",
  "url": "https://www.youtube.com/@...",   # optional override
  "default": [true, "Federation of Light", ""],   # default [is_channeling, entity, note] for videos not listed
  "videos": {"0": [true, "Ashtar", "note"], "3": [false, null, "interview"]},   # overrides by index
  "secondary_channels": [...], "earliest_known_video": {...}, "sources": [...]
}
"""
import json, sys, os, re

raw_path, spec_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
with open(raw_path, encoding="utf-8") as f:
    doc = json.load(f)
with open(spec_path, encoding="utf-8") as f:
    specs = json.load(f)

by_id = {}
for item in doc["data"]["alexandria"]:
    if item.get("error"):
        continue
    d = item["data"]
    by_id[d["channel_id"]] = d


def views_to_int(t):
    if not t:
        return 0
    m = re.match(r"([\d.,]+)\s*([KMB]?)", t.replace(",", ""))
    if not m:
        return 0
    n = float(m.group(1))
    mult = {"K": 1e3, "M": 1e6, "B": 1e9, "": 1}[m.group(2)]
    return int(n * mult)


for s in specs:
    d = by_id[s["channel_id"]]
    default = s.get("default", [False, None, ""])
    overrides = s.get("videos", {})
    vids = []
    for i, v in enumerate(d.get("videos") or []):
        cls = overrides.get(str(i), default)
        vids.append({
            "video_id": v["video_id"],
            "title": v["title"],
            "url": v["url"],
            "view_count_text": v.get("view_count_text"),
            "published_text": v.get("published_text"),
            "published_date": None,
            "length_text": v.get("length_text"),
            "is_channeling": bool(cls[0]),
            "entity": cls[1],
            "note": cls[2] if len(cls) > 2 else "",
        })
    ents = []
    for v in vids:
        if v["entity"] and v["entity"] not in ents:
            ents.append(v["entity"])
    top = sorted([v for v in vids if v["is_channeling"]], key=lambda v: -views_to_int(v["view_count_text"]))[:8]
    handle = d.get("handle")
    url = s.get("url") or (f"https://www.youtube.com/{handle}" if handle else f"https://www.youtube.com/channel/{d['channel_id']}")
    desc = (d.get("description") or "").replace("\n", " ").strip()
    entry = {
        "person": s["person"],
        "role": s.get("role", "channeler"),
        "status": "ok",
        "channel": {
            "title": d.get("channel_title"),
            "handle": handle,
            "channel_id": d["channel_id"],
            "url": url,
            "subscriber_count_text": d.get("subscriber_count_text"),
            "video_count_text": d.get("video_count_text"),
            "description_short": desc[:200],
            "rss_url": d.get("rss_url"),
            "observed_at": "2026-10-23",
            "source": "youtube-com/channel_videos",
        },
        "secondary_channels": s.get("secondary_channels", []),
        "videos": vids,
        "summary": {
            "recent_videos_read": len(vids),
            "channeling_videos_in_recent": sum(1 for v in vids if v["is_channeling"]),
            "entities_seen": ents,
            "top_channeling_video_ids": [v["video_id"] for v in top],
        },
        "sources": s.get("sources", [url]),
    }
    if s.get("earliest_known_video"):
        entry["summary"]["earliest_known_video"] = s["earliest_known_video"]
    if s.get("channel_note"):
        entry["channel"]["note"] = s["channel_note"]
    out = os.path.join(out_dir, s["out"])
    with open(out, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=1)
    print(f"wrote {out}: {len(vids)} videos, {entry['summary']['channeling_videos_in_recent']} channeling, entities={ents}")
