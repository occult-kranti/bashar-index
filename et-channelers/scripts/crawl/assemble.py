import json, sys, glob, os

src_dir = sys.argv[1]
out_path = sys.argv[2]
entries = []
for p in sorted(glob.glob(os.path.join(src_dir, "*.json"))):
    with open(p, encoding="utf-8") as f:
        obj = json.load(f)
    # sanity: recompute summary counts from videos where videos exist
    vids = obj.get("videos") or []
    summ = obj.setdefault("summary", {})
    summ["recent_videos_read"] = len(vids)
    summ["channeling_videos_in_recent"] = sum(1 for v in vids if v.get("is_channeling"))
    ents = []
    for v in vids:
        e = v.get("entity")
        if e and e not in ents:
            ents.append(e)
    if ents or "entities_seen" not in summ:
        summ["entities_seen"] = ents
    entries.append(obj)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=1)
print(f"wrote {len(entries)} entries -> {out_path}")
for e in entries:
    print(f"  {e['person']}: status={e['status']} videos={len(e.get('videos') or [])} channeling={e['summary'].get('channeling_videos_in_recent')}")
