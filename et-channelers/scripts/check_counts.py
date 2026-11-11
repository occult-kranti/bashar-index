#!/usr/bin/env python3
"""Recompute the headline numbers quoted in et-channelers/README.md from the committed files.

Stdlib only, no network. Exits 1 if any number has drifted.
    python3 et-channelers/scripts/check_counts.py
"""
import csv, json, re, sys, collections as C
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IDX = json.load(open(ROOT / "youtube-index/youtube_index.json", encoding="utf-8"))
GROUPS = {g: json.load(open(ROOT / f"youtube-index/group_{g}.json", encoding="utf-8")) for g in "ABC"}


def rows(p):
    return list(csv.DictReader(open(ROOT / p, newline="", encoding="utf-8")))


ch_csv, vid_csv = rows("dashboard/data/channels.csv"), rows("dashboard/data/videos.csv")
pl_csv, en_csv = rows("dashboard/data/playlists.csv"), rows("dashboard/data/entities.csv")
m75, mother = rows("transcripts/bashar75_manifest.csv"), rows("transcripts/other_videos_manifest.csv")

channels = IDX["channels"]
vids = [(c, v) for c in channels for v in (c.get("videos") or [])]
ok_channels = [c for c in channels if c["status"] == "ok"]
ids = [v["video_id"] for _, v in vids if v.get("video_id")]
group_entries = [e for g in GROUPS.values() for e in g]
group_vids = sum(len(e.get("videos") or []) for e in group_entries)
# person ids are the "- slug | name" lines before the "Entity ids" heading
can_people = set(re.findall(r"^- ([a-z0-9][a-z0-9-]*) \|",
                            (ROOT / "research/notes/CANONICAL_IDS.md").read_text(encoding="utf-8").split("## Entity ids")[0],
                            flags=re.M))
handles = json.load(open(ROOT / "research/report/people_yt_handles.json", encoding="utf-8"))


def _norm(u):
    return re.sub(r"^https?://(www\.|m\.)?youtube\.com/", "", u.lower().rstrip("/"))


def _chan_refs(c):
    """Channel URLs and handles an index entry carries (primary and secondary), normalised."""
    out, ch = set(), c.get("channel")
    if isinstance(ch, str):
        out.add(_norm(ch))
    elif isinstance(ch, dict):
        out |= {_norm(ch[k]) for k in ("url", "handle", "channel_url") if isinstance(ch.get(k), str)}
    for s in c.get("secondary_channels") or []:
        if isinstance(s, str):
            out.add(_norm(s))
        elif isinstance(s, dict):
            out |= {_norm(s[k]) for k in ("url", "handle") if isinstance(s.get(k), str)}
    return out


handle_refs = {_norm(u) for e in handles for u in (e.get("yt") or [])}

checks = [
    # --- the 92 people / channels
    ("people/channel entries", len(channels), 92),
    ("  fully crawled (status ok)", len(ok_channels), 16),
    ("  channel details from notes only (metadata-only)", sum(c["status"] == "metadata-only" for c in channels), 38),
    ("  no channel recorded (no_youtube)", sum(c["status"] == "no_youtube" for c in channels), 31),
    ("  not found", sum(c["status"] == "not_found" for c in channels), 7),
    ("  group files: A / B / C entries", tuple(len(g) for g in GROUPS.values()), (31, 31, 30)),
    ("  group files: original status counts", dict(sorted(C.Counter(e["status"] for e in group_entries).items())),
     {"credits_exhausted": 75, "not_found": 1, "ok": 16}),
    # --- how the people lists relate (they were never merged into one list)
    ("canonical person ids (CANONICAL_IDS.md)", len(can_people), 129),
    ("  crawled entries with a canonical person id", sum(c["person"] in can_people for c in channels), 87),
    ("  crawled entries with an id the index added", sum(bool(c.get("person_id_is_new")) for c in channels), 5),
    ("handle list: names", len(handles), 115),
    ("  with at least one YouTube URL", sum(bool(e.get("yt")) for e in handles), 46),
    ("  crawled entries whose channel URL or handle is on the handle list", sum(bool(_chan_refs(c) & handle_refs) for c in channels), 45),
    # --- videos
    ("video rows", len(vids), 466),
    ("  group files total videos (must equal index)", group_vids, 466),
    ("  videos read from crawled channels", sum(len(c.get("videos") or []) for c in ok_channels), 449),
    ("  videos entered from research notes", len(vids) - sum(len(c.get("videos") or []) for c in ok_channels), 17),
    ("  crawled channels that hit the 30-video cap", sum(len(c.get("videos") or []) >= 30 for c in ok_channels), 14),
    ("  distinct video ids", len(set(ids)), 457),
    ("  video rows without an id", len(vids) - len(ids), 9),
    ("  flagged as channeling", sum(bool(v.get("is_channeling")) for _, v in vids), 244),
    ("  title names an entity", sum(bool(v.get("entity")) for _, v in vids), 209),
    # --- dashboard CSVs agree with the JSON
    ("dashboard channels.csv rows", len(ch_csv), 92),
    ("dashboard videos.csv rows", len(vid_csv), 466),
    ("dashboard playlists.csv rows", len(pl_csv), 12),
    ("dashboard entities.csv rows", len(en_csv), 15),
    ("  csv channel statuses == json", dict(C.Counter(r["index_status"] for r in ch_csv)),
     dict(C.Counter(c["status"] for c in channels))),
    ("  csv video statuses", dict(sorted(C.Counter(r["index_status"] for r in vid_csv).items())),
     {"metadata-only": 16, "not_found": 1, "ok": 449}),
    ("  csv channeling == yes", sum(r["channeling"] == "yes" for r in vid_csv), 244),
    # --- draft package tables quoted in the README
    ("draft youtube_channels.csv rows", len(rows("draft-package/csv/youtube_channels.csv")), 92),
    ("draft youtube_videos.csv rows", len(rows("draft-package/csv/youtube_videos.csv")), 466),
    ("draft people_directory.csv rows", len(rows("draft-package/csv/people_directory.csv")), 127),
    ("draft timeline_draft.csv rows", len(rows("draft-package/csv/timeline_draft.csv")), 530),
    ("draft entities_catalogue_raw.csv rows", len(rows("draft-package/csv/entities_catalogue_raw.csv")), 73),
    ("draft youtube_links_harvest.csv rows", len(rows("draft-package/csv/youtube_links_harvest.csv")), 136),
    # --- transcripts
    ("Bashar-75 manifest rows", len(m75), 75),
    ("  retrieved", sum(r["transcript_status"] == "retrieved" for r in m75), 55),
    ("  error (client_error)", sum(r["transcript_status"] == "error" for r in m75), 20),
    ("  full text saved locally (not in repo)", sum(r["full_text_saved_locally"] == "yes" for r in m75), 12),
    ("other-videos manifest rows", len(mother), 15),
    ("  retrieved", sum(r["transcript_status"] == "retrieved" for r in mother), 9),
    ("distinct videos with a transcript retrieved", sum(r["transcript_status"] == "retrieved" for r in m75 + mother), 64),
]

bad = 0
for name, got, want in checks:
    good = got == want
    bad += not good
    print(f"{'PASS' if good else 'FAIL'}  {name}: {got}" + ("" if good else f"   (expected {want})"))
print(f"\n{len(checks) - bad}/{len(checks)} checks passed")
sys.exit(1 if bad else 0)
