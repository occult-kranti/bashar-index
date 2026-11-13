#!/usr/bin/env python3
"""Build the two transcript manifests (metadata only, no transcript text).

Inputs
  rows.json    output of count_from_agent_logs.py (one row per sub-agent tool call; needs the session logs)
  astro_dir    folder of locally saved full-text transcripts (<video_id>.txt); only the file NAMES are read
  videos.json  data/videos.json of the Bashar Index (the 75 recordings)
  all_ids.txt  the 75 target video ids
Outputs (written to out_dir)
  bashar75_manifest.csv       one row per target recording: retrieved / error, and how it was read
  other_videos_manifest.csv   transcript pages tried for other tasks (profiles, location-claim research)

Usage: python3 -I build_manifest.py rows.json astro_dir videos.json all_ids.txt out_dir
"""
import csv, json, os, re, sys, collections as C

rows_path, astro_dir, videos_path, ids_path, out_dir = sys.argv[1:6]
os.makedirs(out_dir, exist_ok=True)

VID = re.compile(r"(?:[?&]v=|youtu\.be/|/shorts/|/embed/)([A-Za-z0-9_-]{11})")
rows = json.load(open(rows_path, encoding="utf-8"))
videos = {v["video_id"]: v for v in json.load(open(videos_path, encoding="utf-8"))}
ids = [l.strip() for l in open(ids_path, encoding="utf-8") if l.strip()]
saved = {f[:-4] for f in os.listdir(astro_dir) if f.endswith(".txt")}

# Two recordings were read in the main session before the sub-agent logs begin; they were
# quote-checked there and are recorded here from the session notes.
INLINE = {"E_cPno64Z-Q", "1x7Z68os7HE"}

att, ok, desc = C.Counter(), C.Counter(), {}
for r in rows:
    if "youtubetotranscript" not in r["url"]:
        continue
    m = VID.search(r["url"])
    if not m:
        continue
    v = m.group(1)
    att[v] += 1
    desc.setdefault(v, set()).add(r["desc"])
    if r["status"] == "ok":
        ok[v] += 1

# Package researcher notes mark these two as re-uploads of an Emersion Conference session that was read.
DUP = {"mk_yQrOQHJs": "DvWNnqnBAjc", "tskKYl3w0J8": "DvWNnqnBAjc"}


def how(v):
    s, a, i = v in saved, ok[v] > 0, v in INLINE
    if s and a:
        return "saved_file+agent_read"
    if s:
        return "saved_file"
    if a:
        return "agent_read"
    if i:
        return "main_session_inline"
    return ""


out = []
for v in ids:
    meta = videos[v]
    h = how(v)
    status = "retrieved" if h else "error"
    note = ""
    if status == "error" and v in DUP:
        note = f"duplicate session of {DUP[v]} (retrieved), per package researcher_note; title date unreliable"
    out.append([v, meta.get("title", ""), meta.get("channel", ""), meta.get("url", f"https://www.youtube.com/watch?v={v}"),
                status, "" if status == "retrieved" else "client_error", h,
                "yes" if v in saved else "no", att[v], ok[v], note])
with open(os.path.join(out_dir, "bashar75_manifest.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["video_id", "title", "channel", "url", "transcript_status", "error_code", "how_read",
                "full_text_saved_locally", "agent_fetch_attempts", "agent_fetches_ok", "note"])
    w.writerows(out)

others = sorted(v for v in att if v not in set(ids))
out2 = []
for v in others:
    d = "; ".join(sorted(desc[v]))
    out2.append([v, f"https://www.youtube.com/watch?v={v}", "retrieved" if ok[v] else "error",
                 "" if ok[v] else "client_error", att[v], ok[v], d])
with open(os.path.join(out_dir, "other_videos_manifest.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["video_id", "url", "transcript_status", "error_code", "agent_fetch_attempts", "agent_fetches_ok", "read_for_task"])
    w.writerows(out2)

c = C.Counter(r[4] for r in out)
print("bashar75:", len(out), dict(c), "| saved locally:", sum(1 for r in out if r[7] == "yes"),
      "| how_read:", dict(C.Counter(r[6] for r in out if r[6])))
print("others:", len(out2), dict(C.Counter(r[2] for r in out2)))
