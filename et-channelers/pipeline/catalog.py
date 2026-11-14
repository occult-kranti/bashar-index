#!/usr/bin/env python3
"""Build the index of everything collected, and the per-person coverage table.

Reads the manifests in the private folder (audio, machine transcripts, publisher texts, captions),
the queues and the committed source lists, and writes

  <root>/catalog/catalog.csv            one row per item: who, lane, title, date, length, where the
                                        audio and each kind of text are, the YouTube twin if any.
                                        PRIVATE: it holds titles, addresses and paths.
  <root>/public_export/coverage.csv     one row per person: counts, hours and word counts only.
                                        No titles, no addresses, no text. Safe to publish after a look.
  <root>/public_export/coverage.json    the same numbers plus totals, for the dashboard.

Text is counted in three separate kinds, never mixed:
  from the source   publisher_texts   a transcript the publisher wrote and offers (site page, feed link)
                    captions          YouTube's own caption track for a video
  made here         asr_transcripts   speech-to-text run on audio this project downloaded

With --publish the coverage table is also copied to plan/coverage.csv and plan/coverage.json in the
repository. The catalogue itself is never copied.

    python3 pipeline/catalog.py
    python3 pipeline/catalog.py --publish
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, ID_RE, add_root_arg, atomic_write_text, ensure_outside_git, item_id, lane_of,  # noqa: E402
                    latest_by_key, layout, listed_videos, read_csv, read_jsonl, utc_now, write_csv)
from find_feeds import load_targets  # noqa: E402
from select_episodes import collect  # noqa: E402

INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
BASHAR_IDS = ET_ROOT / "transcripts" / "scripts" / "all_ids.txt"
CREATOR_FILES = ET_ROOT / "sources" / "creator_files.csv"
PAGES = ET_ROOT / "sources" / "publisher_pages.csv"
REGISTRY = ET_ROOT / "sources" / "podcast_feeds.csv"
CATALOG_FIELDS = ["item_id", "person_id", "lane", "relation", "tab", "title", "published", "duration_s", "audio_status",
                  "audio_path", "audio_bytes", "publisher_text_status", "publisher_text_words", "publisher_text_path",
                  "captions_status", "captions_words", "captions_path", "asr_status", "asr_model", "asr_words",
                  "asr_path", "text_from_source", "text_made_here", "has_text", "twin_of", "twin_method",
                  "feed_key", "interview_type", "source_host", "source_url"]
COVERAGE_FIELDS = ["person_id", "person_name", "role", "youtube_videos_indexed", "own_feeds", "items_listed",
                   "items_outside_youtube", "distinct_listed", "distinct_captured", "youtube_listed", "youtube_shorts",
                   "youtube_captured", "interviews_listed", "interviews_live_channeling", "interviews_unclear",
                   "interviews_conversation", "interviews_commentary", "interviews_not_classified", "interviews_here",
                   "listed_hours", "audio_ok", "audio_hours", "audio_failed", "audio_podcast", "audio_creator_file", "audio_archive_org", "archive_org_listed",
                   "audio_youtube", "publisher_texts", "publisher_text_words", "captions", "captions_words",
                   "asr_transcripts", "asr_words", "asr_hours", "items_text_from_source", "items_text_made_here",
                   "items_with_text", "audio_awaiting_transcript", "youtube_twins", "next_step"]
SITE_WIDE_SHARE = 0.2   # a video id embedded on more than this share of one site's pages is page furniture


def boilerplate_ids(pub):
    """{person: set(video ids)} that appear on so many of a person's pages that they cannot be 'the' video."""
    pages, seen = collections.Counter(), collections.defaultdict(collections.Counter)
    for rec in pub.values():
        if rec.get("status") == "ok" and rec.get("youtube_ids"):
            pages[rec["channel_dir"]] += 1
            for vid in set(rec["youtube_ids"]):
                seen[rec["channel_dir"]][vid] += 1
    return {person: {vid for vid, n in counts.items() if pages[person] >= 10 and n > SITE_WIDE_SHARE * pages[person]}
            for person, counts in seen.items()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--publish", action="store_true", help="also copy the coverage table into plan/ in the repository")
    args = ap.parse_args()
    paths = layout(ensure_outside_git(args.root))

    def current(path):
        """Latest line per item, without ids that migrate_ids.py renamed."""
        return {k: v for k, v in latest_by_key(read_jsonl(path)).items() if v.get("status") != "superseded"}

    audio = current(paths.audio / "audio_manifest.jsonl")
    # A multi-process transcription writes one manifest per process and merges them when it ends; a long
    # run would otherwise look as if it had produced nothing until its last file.
    asr_lines = read_jsonl(paths.transcripts / "transcripts_manifest.jsonl")
    for part in sorted(paths.transcripts.glob("transcripts_manifest.part-*.jsonl")):
        asr_lines += read_jsonl(part)
    asr = {k: v for k, v in latest_by_key(asr_lines).items() if v.get("status") != "superseded"}
    pub = current(paths.pubtext / "publisher_text_manifest.jsonl")
    caps = current(paths.captions / "captions_manifest.jsonl")

    # which person a YouTube video belongs to: the index says so, and the Bashar-75 list is all Darryl Anka
    yt_person, indexed = {}, {}
    if INDEX.exists():
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            ids = [v["video_id"] for v in channel.get("videos") or [] if ID_RE.match(v.get("video_id") or "")]
            indexed[channel["person"]] = len(ids)
            for vid in ids:
                yt_person.setdefault(vid, channel["person"])
    if BASHAR_IDS.exists():
        for vid in (x.strip() for x in BASHAR_IDS.read_text(encoding="utf-8").splitlines()):
            if ID_RE.match(vid):
                yt_person.setdefault(vid, "darryl-anka")

    items = {}

    def entry(ident, person):
        if lane_of(ident) == "youtube":
            person = yt_person.get(ident, person)
        return items.setdefault(ident, {"item_id": ident, "person_id": person, "lane": lane_of(ident), "relation": "", "tab": "",
                                        "title": "", "published": "", "duration_s": "", "twin_of": "", "twin_method": "", "feed_key": "",
                                        "interview_type": "",
                                        "source_host": "", "source_url": "", "text_id": ident, "folder": person})

    # What exists is what the source lists hold (every accepted feed's episodes, every creator file),
    # not what the current queue file happens to contain: a queue built with --only, --per-channel or
    # --limit is a work order, and counting from it made "listed", "remaining" and "complete" wrong.
    listed, _, _ = collect(paths)
    for row in listed:
        e = entry(row["video_id"], row["channel_dir"])
        e.update(relation=row["relation"], title=row["title"], published=row["published"],
                 duration_s="" if row["duration_s"] is None else row["duration_s"], twin_of=row["twin_of"],
                 twin_method=row["twin_method"], source_url=row["url"], folder=row["channel_dir"],
                 feed_key=row.get("feed_key") or "", interview_type=row.get("interview_type") or "")
    queue = paths.jobs / "queue_enclosures.csv"
    for row in read_csv(queue) if queue.exists() else []:       # anything queued that the lists no longer hold
        if row["video_id"] not in items:
            e = entry(row["video_id"], row["channel_dir"])
            e.update(relation=row.get("relation", ""), title=row.get("title", ""), published=row.get("published", ""),
                     duration_s=row.get("duration_s", ""), twin_of=row.get("twin_of", ""),
                     twin_method=row.get("twin_method", ""), source_url=row.get("url", ""), folder=row["channel_dir"])
    queue = paths.jobs / "queue.csv"
    for row in read_csv(queue) if queue.exists() else []:
        e = entry(row["video_id"], row["channel_dir"])
        e.update(relation="youtube", title=row.get("title", ""), duration_s=row.get("duration_s", ""),
                 source_url=row.get("url", ""), folder=row["channel_dir"], source_host="youtube.com")

    # every video a channel lists (discover.py), whether or not a work order names it: the channel is the
    # measure of "complete", and the listing is the only place that says how much there is
    for row in listed_videos(paths.root):
        if ID_RE.match(row.get("video_id") or ""):
            e = entry(row["video_id"], row.get("person_id", ""))
            e.update(relation="youtube", tab=row.get("tab") or "videos", title=e["title"] or row.get("title") or "",
                     duration_s=e["duration_s"] or row.get("duration_s") or "", source_host="youtube.com")

    # a creator file pairs with the publisher page that offers it
    page_rows = read_csv(PAGES) if PAGES.exists() else []
    page_ids = {r["page_url"].strip(): item_id("web", r["page_url"].strip()) for r in page_rows if r.get("page_url")}
    page_title = {item_id("web", r["page_url"].strip()): r.get("title", "") for r in page_rows if r.get("page_url")}
    paired_pages = set()
    for row in read_csv(CREATOR_FILES) if CREATOR_FILES.exists() else []:
        page = (row.get("official_page") or "").strip()
        ident = item_id("web", (row.get("media_url") or "").strip())
        if page in page_ids:
            if ident in items:
                items[ident]["text_id"] = page_ids[page]
            paired_pages.add(page_ids[page])       # the page's text belongs to this recording: count it once, there

    for ident, rec in audio.items():
        e = entry(ident, rec.get("channel_dir", ""))
        e["folder"] = rec.get("channel_dir", e["folder"])
        e["source_host"] = e["source_host"] or rec.get("source_host", "") or ("youtube.com" if lane_of(ident) == "youtube" else "")
        e["published"] = e["published"] or rec.get("published", "")
        e["twin_of"] = e["twin_of"] or rec.get("twin_of", "")
        e["feed_key"] = e["feed_key"] or rec.get("feed_key", "")
    for ident, rec in asr.items():
        entry(ident, rec.get("channel_dir", ""))
    for ident, rec in caps.items():
        e = entry(ident, rec.get("channel_dir", ""))
        e["relation"] = e["relation"] or "youtube"
    for row in page_rows:
        page = (row.get("page_url") or "").strip()
        if page and page_ids[page] not in paired_pages and page_ids[page] not in items:
            e = entry(page_ids[page], row.get("person_id", ""))
            e.update(relation="page", title=row.get("title", ""), source_url=page, source_host="")
    furniture = boilerplate_ids(pub)
    for ident, rec in pub.items():
        if ident in paired_pages:
            continue                       # its text is shown on the audio item it belongs to
        e = entry(ident, rec.get("channel_dir", ""))
        e["title"] = e["title"] or rec.get("title") or page_title.get(ident, "")
        e["relation"] = e["relation"] or "page"
        e["published"] = e["published"] or rec.get("published", "")
        e["source_host"] = e["source_host"] or rec.get("source_host", "")
        e["source_url"] = e["source_url"] or rec.get("source_url", "")
        own = [v for v in rec.get("youtube_ids") or [] if v not in furniture.get(rec.get("channel_dir"), ())]
        if not e["twin_of"] and len(own) == 1:
            e["twin_of"], e["twin_method"] = own[0], "page-embed"

    rows = []
    for ident, e in sorted(items.items(), key=lambda kv: (kv[1]["person_id"], kv[1]["published"], kv[0])):
        au, tr, pt, cp = audio.get(ident, {}), asr.get(ident, {}), pub.get(e["text_id"], {}), caps.get(ident, {})
        ok = lambda rec: rec.get("status") == "ok"  # noqa: E731
        row = {**e,
               "audio_status": au.get("status", ""), "audio_path": f"audio/{au['path']}" if ok(au) else "",
               "audio_bytes": au.get("bytes", "") if ok(au) else "",
               "duration_s": au.get("duration_s") if ok(au) and au.get("duration_s") else e["duration_s"],
               "publisher_text_status": pt.get("status", ""),
               "publisher_text_words": pt.get("n_words", "") if ok(pt) else "",
               "publisher_text_path": f"transcripts_publisher/{pt['channel_dir']}/{e['text_id']}.txt" if ok(pt) else "",
               "captions_status": cp.get("status", ""), "captions_words": cp.get("n_words", "") if ok(cp) else "",
               "captions_path": f"captions/{cp['channel_dir']}/{ident}.txt" if ok(cp) else "",
               "asr_status": tr.get("status", ""), "asr_model": tr.get("model", "") if ok(tr) else "",
               "asr_words": tr.get("n_words", "") if ok(tr) else "",
               "asr_path": f"transcripts/{tr['channel_dir']}/{ident}.txt" if ok(tr) else ""}
        row["text_from_source"] = int(ok(pt) or ok(cp))
        row["text_made_here"] = int(ok(tr))
        row["has_text"] = int(row["text_from_source"] or row["text_made_here"])
        rows.append(row)
    write_csv(paths.root / "catalog" / "catalog.csv", rows, CATALOG_FIELDS)

    # ---- per-person coverage: numbers only
    # A video and the podcast episode or page that carries the same content are one piece of work: the
    # pair is listed once and is captured as soon as either side is in the archive. Without this a
    # person whose interviews were fetched as podcast episodes would still show every video as missing.
    listed_ids = {r["item_id"] for r in rows}
    work_of = {r["item_id"]: r["twin_of"] if r["twin_of"] in listed_ids else r["item_id"] for r in rows}
    captured_works = {work_of[r["item_id"]] for r in rows if r["audio_status"] == "ok" or r["has_text"]}
    names = {t["person_id"]: t for t in load_targets()}
    feeds = collections.Counter(r["person_id"] for r in (read_csv(REGISTRY) if REGISTRY.exists() else [])
                                if r.get("relation") == "own" and r.get("verification") in ("verified", "name-match"))

    def seconds(group):
        return sum(float(r["duration_s"]) for r in group if r["duration_s"] not in ("", None))

    def words(group, field):
        return sum(int(r[field] or 0) for r in group)

    table = []
    for person in sorted(set(names) | {r["person_id"] for r in rows if r["person_id"]}):
        mine = [r for r in rows if r["person_id"] == person]
        got = [r for r in mine if r["audio_status"] == "ok"]
        asr_done = [r for r in mine if r["asr_status"] == "ok"]
        waiting = sum(1 for r in got if not r["has_text"])
        # still to fetch: a listed recording without audio, unless its content is already here through its
        # twin (the podcast episode of a video, or the page that carries its text)
        remaining = [r for r in mine if r["relation"] in ("own", "host", "file", "archive", "youtube") and r["audio_status"] != "ok"
                     and not (r["lane"] == "youtube" and work_of[r["item_id"]] in captured_works)
                     and not (r["relation"] == "host" and r["interview_type"] != "live channeling")]
        tube = [r for r in mine if r["lane"] == "youtube"]
        talks = [r for r in mine if r["relation"] == "host"]

        def kind_count(kind, group=talks):
            return sum(1 for r in group if (r["interview_type"] or "not classified") == kind)
        pages_left = sum(1 for r in mine if r["relation"] == "page" and r["publisher_text_status"] != "ok")
        if not mine and not feeds.get(person):
            step = "no downloadable source found yet: run the YouTube lane on a home connection, or find the maker's own feed or site"
        elif remaining:
            only_youtube = all(r["relation"] == "youtube" for r in remaining)
            step = ("YouTube only: run the YouTube lane on a home connection" if only_youtube
                    else f"download the remaining {len(remaining)} listed items")
        elif pages_left:
            step = f"fetch the remaining {pages_left} publisher pages"
        elif waiting:
            step = f"transcribe {waiting} recordings that have no text yet"
        elif mine:
            step = "complete for the listed items"
        else:
            step = "read the accepted feed"
        table.append({
            "person_id": person, "person_name": names.get(person, {}).get("person_name", ""),
            "role": names.get(person, {}).get("role", ""), "youtube_videos_indexed": indexed.get(person, 0),
            "own_feeds": feeds.get(person, 0), "items_listed": len(mine),
            "items_outside_youtube": sum(1 for r in mine if r["lane"] != "youtube"),
            "distinct_listed": len({work_of[r["item_id"]] for r in mine}),
            "distinct_captured": len({work_of[r["item_id"]] for r in mine} & captured_works),
            "youtube_listed": len(tube), "youtube_shorts": sum(1 for r in tube if r["tab"] == "shorts"),
            "youtube_captured": sum(1 for r in tube if work_of[r["item_id"]] in captured_works),
            "interviews_listed": len(talks), "interviews_live_channeling": kind_count("live channeling"),
            "interviews_unclear": kind_count("unclear"), "interviews_conversation": kind_count("conversation"),
            "interviews_commentary": kind_count("commentary or clip"), "interviews_not_classified": kind_count("not classified"),
            "interviews_here": sum(1 for r in talks if r["audio_status"] == "ok" or r["has_text"]),
            "listed_hours": round(seconds(mine) / 3600, 1),
            "audio_ok": len(got), "audio_hours": round(seconds(got) / 3600, 1),
            "audio_failed": sum(1 for r in mine if r["audio_status"] == "error"),
            "audio_podcast": sum(1 for r in got if r["lane"] == "pod"),
            "audio_creator_file": sum(1 for r in got if r["lane"] == "web"),
            "audio_archive_org": sum(1 for r in got if r["lane"] == "ia"),
            "archive_org_listed": sum(1 for r in mine if r["lane"] == "ia"),
            "audio_youtube": sum(1 for r in got if r["lane"] == "youtube"),
            "publisher_texts": sum(1 for r in mine if r["publisher_text_status"] == "ok"),
            "publisher_text_words": words(mine, "publisher_text_words"),
            "captions": sum(1 for r in mine if r["captions_status"] == "ok"), "captions_words": words(mine, "captions_words"),
            "asr_transcripts": len(asr_done), "asr_words": words(mine, "asr_words"),
            "asr_hours": round(seconds(asr_done) / 3600, 1),
            "items_text_from_source": sum(r["text_from_source"] for r in mine),
            "items_text_made_here": sum(r["text_made_here"] for r in mine),
            "items_with_text": sum(r["has_text"] for r in mine), "audio_awaiting_transcript": waiting,
            "youtube_twins": sum(1 for r in mine if r["twin_of"]), "next_step": step})
    table.sort(key=lambda r: (-(r["items_with_text"] + r["audio_ok"]), -r["items_listed"], r["person_id"]))
    write_csv(paths.public / "coverage.csv", table, COVERAGE_FIELDS)
    totals = {}
    for key in COVERAGE_FIELDS:
        if table and isinstance(table[0][key], (int, float)):
            total = sum(r[key] for r in table)
            totals[key] = round(total, 1) if isinstance(table[0][key], float) else total
    summary = {"generated": utc_now(), "people": len(table),
               "people_with_a_listed_source": sum(1 for r in table if r["items_listed"]),
               "people_with_a_source_outside_youtube": sum(1 for r in table if r["items_outside_youtube"]),
               "people_with_a_channel_listing": sum(1 for r in table if r["youtube_listed"]),
               "people_with_audio": sum(1 for r in table if r["audio_ok"]),
               "people_with_text_from_source": sum(1 for r in table if r["items_text_from_source"]),
               "people_with_text_made_here": sum(1 for r in table if r["items_text_made_here"]),
               "people_with_any_text": sum(1 for r in table if r["items_with_text"]),
               "totals": totals, "rows": table}
    atomic_write_text(paths.public / "coverage.json", json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    if args.publish:
        write_csv(ET_ROOT / "plan" / "coverage.csv", table, COVERAGE_FIELDS)
        atomic_write_text(ET_ROOT / "plan" / "coverage.json", json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    t = totals
    print(f"catalogue {len(rows)} items -> {paths.root / 'catalog' / 'catalog.csv'}\n"
          f"coverage  {summary['people']} people | {summary['people_with_a_listed_source']} with a listed source | "
          f"{summary['people_with_audio']} with audio | {summary['people_with_any_text']} with text\n"
          f"  audio            {t.get('audio_ok', 0)} files, {t.get('audio_hours', 0)} h\n"
          f"  text from source {t.get('publisher_texts', 0)} publisher texts ({t.get('publisher_text_words', 0)} words), "
          f"{t.get('captions', 0)} caption tracks ({t.get('captions_words', 0)} words)\n"
          f"  text made here   {t.get('asr_transcripts', 0)} machine transcripts ({t.get('asr_words', 0)} words, "
          f"{t.get('asr_hours', 0)} h of audio)\n"
          f"  audio still awaiting a transcript: {t.get('audio_awaiting_transcript', 0)}"
          + (f"\npublished -> {ET_ROOT / 'plan' / 'coverage.csv'}" if args.publish else ""))


if __name__ == "__main__":
    main()
