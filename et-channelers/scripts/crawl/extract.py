"""Print a compact listing of each channel in a saved firecrawl alexandria result."""
import json, sys

path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    doc = json.load(f)
for item in doc["data"]["alexandria"]:
    if item.get("error"):
        print("ERROR:", json.dumps(item.get("error"))[:300], "| options:", item.get("options"))
        continue
    d = item["data"]
    print("=" * 100)
    print(f"CHANNEL: {d.get('channel_title')} | handle={d.get('handle')} | id={d.get('channel_id')} | subs={d.get('subscriber_count_text')} | videos={d.get('video_count_text')}")
    desc = (d.get("description") or "").replace("\n", " ")
    print(f"DESC: {desc[:300]}")
    for i, v in enumerate(d.get("videos") or []):
        print(f"{i:2d} {v['video_id']} | {v.get('view_count_text')} | {v.get('published_text')} | {v.get('length_text')} | {v['title']}")
