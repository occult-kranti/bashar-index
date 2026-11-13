#!/usr/bin/env python3
"""Build the one list of everyone tracked: where each name came from, what is captured, what is planned.

Three bodies of work named people and channels:
  bashar-index   the index in this repository (youtube-index/youtube_index.json)
  archiveshelf   the ArchiveShelf channel intake (sources/archiveshelf_intake.csv)
  added          people added since (sources/extra_targets.csv)
This script joins them on the person id and says, for each person,

  identity   verified, unresolved (nobody has established who the name refers to) or excluded
  channel    address, id, subscribers, and how many videos, live streams and shorts the channel lists
  found      podcast feeds, creator-hosted files and publisher pages registered in sources/
  captured   distinct pieces of work in the archive, audio files and hours, texts obtained from the
             source, transcripts made here by speech-to-text
  state      captured | partly captured | planned: source found | planned: YouTube only |
             planned: no source yet | unresolved | excluded

A video and the podcast episode or page that carries the same content count as one piece of work.

It also writes the list of channels behind the 75 Bashar recordings of the Bashar Index site: the
official channel, the interview shows and the re-upload channels, each with what was read before and
what is in the archive now.

Writes  plan/targets.csv, plan/targets_summary.json, plan/bashar_host_channels.csv

Everything written is public metadata and counts: no titles of individual recordings, no addresses of
files, no text. Captured counts come from the private folder (catalog.py writes them); with
--no-private the committed snapshot plan/coverage.json is used and the private-only columns stay empty.

    python3 pipeline/catalog.py --publish && python3 pipeline/targets.py
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, atomic_write_text, ensure_outside_git, latest_by_key, layout,  # noqa: E402
                    read_csv, read_jsonl, slug, utc_now, write_csv)

INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
INVENTORY = ET_ROOT / "plan" / "channel_inventory.csv"
COVERAGE = ET_ROOT / "plan" / "coverage.json"
BASHAR_CSV = ET_ROOT / "draft-package" / "csv" / "bashar_videos_in_repo_by_channel.csv"
BASHAR_READ = ET_ROOT / "transcripts" / "bashar75_manifest.csv"
SOURCES = ET_ROOT / "sources"
BASHAR_PERSON = "darryl-anka"          # every recording of the Bashar Index site is his
FIELDS = ["person_id", "person_name", "role", "origin", "identity", "index_status", "youtube_channel_url",
          "youtube_channel_id", "subscribers", "channel_videos_stated", "videos_listed", "live_listed", "shorts_listed",
          "listed_video_hours", "official_sites", "podcast_feeds", "creator_files", "publisher_pages", "items_listed",
          "items_captured", "captured_audio_files", "captured_audio_hours", "captured_source_texts",
          "captured_source_words", "captured_machine_transcripts", "audio_awaiting_transcript", "earlier_work", "state",
          "next_step"]
HOST_FIELDS = ["channel", "host_id", "kind", "bashar_recordings", "interviews", "transcripts_read_earlier",
               "youtube_channel_url", "youtube_channel_id", "websites", "podcast_feeds", "captured_here", "state",
               "next_step"]
STATES = ("captured", "partly captured", "planned: source found", "planned: YouTube only", "planned: no source yet",
          "unresolved", "excluded")
HOST_STATES = ("captured", "partly captured", "planned: podcast feed found", "planned: YouTube only")
NUMBERS = ("podcast_feeds", "creator_files", "publisher_pages", "items_listed", "items_captured", "captured_audio_files",
           "captured_source_texts", "captured_source_words", "captured_machine_transcripts", "audio_awaiting_transcript")


def rows_of(path):
    return read_csv(path) if Path(path).exists() else []


def number(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def state_of(identity, listed, captured, has_source, has_channel, channel_listed=True):
    """One of STATES. `listed` and `captured` count distinct pieces of work; `has_source` means something
    outside YouTube is registered for the person; `has_channel` that a YouTube channel is known;
    `channel_listed` that its videos have been listed, so `listed` includes them. Nobody is "captured"
    while a channel of theirs has not even been counted."""
    if identity in ("excluded", "unresolved"):
        return identity
    if listed and captured >= listed and (channel_listed or not has_channel):
        return "captured"
    if captured:
        return "partly captured"
    if has_source:
        return "planned: source found"
    if has_channel:
        return "planned: YouTube only"
    return "planned: no source yet"


def channel_listings(paths):
    """{person: {videos, streams, shorts, hours}} from the channel listings discover.py wrote."""
    out = {}
    done = latest_by_key(read_jsonl(paths.discover / "discover_manifest.jsonl"), "person_id")
    for person, rec in done.items():
        listing = paths.discover / "channels" / f"{person}.jsonl"
        if rec.get("status") != "ok" or not listing.exists():
            continue
        rows = read_jsonl(listing)
        tabs = collections.Counter(r.get("tab") or "videos" for r in rows)
        seconds = sum(r.get("duration_s") or 0 for r in rows)
        out[person] = {"videos": tabs.get("videos", 0), "streams": tabs.get("streams", 0), "shorts": tabs.get("shorts", 0),
                       "hours": round(seconds / 3600, 1)}
    return out


def build(root=None):
    """The table, one dict per person or unresolved name."""
    people = {}

    def person(pid, name="", role=""):
        entry = people.setdefault(pid, {**dict.fromkeys(FIELDS, ""), "person_id": pid, "origins": set(), "sites": [],
                                        "earlier": []})
        entry["person_name"] = entry["person_name"] or name
        entry["role"] = entry["role"] or role
        return entry

    # 1. the Bashar index. Its status says what was read of the channel, not who the person is: every
    #    entry is a known person, including those whose channel was not found.
    if INDEX.exists():
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            entry = person(channel["person"], channel.get("person_name") or "", channel.get("role") or "")
            entry["origins"].add("bashar-index")
            info = channel.get("channel") or {}
            videos = len(channel.get("videos") or [])
            entry.update(index_status=channel.get("status") or "", identity="verified",
                         youtube_channel_url=(info.get("url") or "") if str(info.get("url")).startswith("http") else "",
                         youtube_channel_id=info.get("channel_id") or "",
                         subscribers=channel.get("subscribers") or "", channel_videos_stated=channel.get("video_count") or "")
            if videos:
                entry["earlier"].append(f"Bashar index: {videos} videos listed")
    for row in rows_of(INVENTORY):
        if row.get("person_id") in people:
            entry = people[row["person_id"]]
            entry["subscribers"] = entry["subscribers"] or row.get("subscribers") or ""
            entry["channel_videos_stated"] = entry["channel_videos_stated"] or row.get("total_videos") or ""
    # 2. the ArchiveShelf intake
    loose = []
    for row in rows_of(SOURCES / "archiveshelf_intake.csv"):
        if not row.get("person_id"):
            loose.append(row)
            continue
        entry = person(row["person_id"], row["archiveshelf_name"])
        entry["origins"].add("archiveshelf")
        entry["identity"] = entry["identity"] or ("verified" if row.get("identity") == "verified" else "unresolved")
        entry["youtube_channel_url"] = entry["youtube_channel_url"] or row.get("youtube_url") or ""
        held = (row.get("captured_by_archiveshelf") or "").strip()
        entry["earlier"].append("ArchiveShelf: " + (held if held and held != "nothing" else "channel named, nothing collected"))
    # 3. people added since, and channels the index does not have
    for row in rows_of(SOURCES / "extra_targets.csv"):
        entry = person(row["person_id"], row.get("name") or "", row.get("role") or "")
        if not entry["origins"]:
            entry["origins"].add("added")
            entry["identity"] = "verified"
    for row in rows_of(SOURCES / "extra_channels.csv"):
        if row.get("person_id") in people:
            entry = people[row["person_id"]]
            entry["youtube_channel_url"] = entry["youtube_channel_url"] or row.get("channel_url") or ""
            entry["youtube_channel_id"] = entry["youtube_channel_id"] or row.get("channel_id") or ""
    # 4. what is registered for each
    for row in rows_of(SOURCES / "official_sites.csv"):
        if row.get("person_id") in people and row["domain"] not in people[row["person_id"]]["sites"]:
            people[row["person_id"]]["sites"].append(row["domain"])
    feeds = collections.Counter(r["person_id"] for r in rows_of(SOURCES / "podcast_feeds.csv")
                                if r.get("relation") == "own" and r.get("verification") in ("verified", "name-match"))
    files = collections.Counter(r["person_id"] for r in rows_of(SOURCES / "creator_files.csv"))
    pages = collections.Counter(r["person_id"] for r in rows_of(SOURCES / "publisher_pages.csv"))
    # 5. what the private folder knows
    coverage_file, listings = COVERAGE, {}
    if root is not None:
        paths = layout(root)
        coverage_file = paths.public / "coverage.json"
        listings = channel_listings(paths)
        for rec in latest_by_key(read_jsonl(paths.sources / "channel_pages.jsonl"), "person_id").values():
            if rec.get("status") == "ok" and rec["person_id"] in people:
                entry = people[rec["person_id"]]
                entry["youtube_channel_id"] = rec.get("channel_id") or entry["youtube_channel_id"]
                entry["subscribers"] = rec.get("subscribers") or entry["subscribers"]
    coverage = {}
    if Path(coverage_file).exists():
        coverage = {r["person_id"]: r for r in json.loads(Path(coverage_file).read_text(encoding="utf-8")).get("rows", [])}
    read_before, digested = bashar_read_before()

    table = []
    for pid in sorted(people):
        entry, cov, seen = people[pid], coverage.get(pid, {}), listings.get(pid)
        listed = number(cov.get("distinct_listed", cov.get("items_listed")))
        captured = number(cov.get("distinct_captured", number(cov.get("items_with_text")) + number(cov.get("audio_awaiting_transcript"))))
        if pid == BASHAR_PERSON and digested:
            entry["earlier"].append(f"Bashar Index site: {digested} recordings digested; transcripts of {read_before} "
                                    "read in 2026-10, text not kept")
        entry.update(
            origin="both" if {"bashar-index", "archiveshelf"} <= entry["origins"] else sorted(entry["origins"])[0],
            identity=entry["identity"] or "verified", official_sites=" ".join(entry["sites"]),
            podcast_feeds=feeds.get(pid, 0), creator_files=files.get(pid, 0), publisher_pages=pages.get(pid, 0),
            videos_listed=seen["videos"] if seen else "", live_listed=seen["streams"] if seen else "",
            shorts_listed=seen["shorts"] if seen else "", listed_video_hours=seen["hours"] if seen else "",
            items_listed=listed, items_captured=captured, captured_audio_files=number(cov.get("audio_ok")),
            captured_audio_hours=float(cov.get("audio_hours") or 0),
            captured_source_texts=number(cov.get("publisher_texts")) + number(cov.get("captions")),
            captured_source_words=number(cov.get("publisher_text_words")) + number(cov.get("captions_words")),
            captured_machine_transcripts=number(cov.get("asr_transcripts")),
            audio_awaiting_transcript=number(cov.get("audio_awaiting_transcript")),
            earlier_work="; ".join(entry["earlier"]), next_step=cov.get("next_step", ""))
        has_source = bool(entry["podcast_feeds"] or entry["creator_files"] or entry["publisher_pages"]
                          or number(cov.get("items_outside_youtube")))
        entry["state"] = state_of(entry["identity"], listed, captured, has_source, bool(entry["youtube_channel_url"]),
                                  seen is not None)
        if entry["state"] in ("planned: YouTube only", "planned: no source yet", "unresolved"):
            entry["next_step"] = {
                "planned: YouTube only": "run the YouTube lane on a home connection (run_all.py); look for the maker's own site or feed",
                "planned: no source yet": "no channel or site known: find where this person publishes",
                "unresolved": "establish who this name refers to"}[entry["state"]]
        table.append({k: entry[k] for k in FIELDS})
    for row in loose:
        excluded = row.get("identity") == "excluded"
        blank = {**dict.fromkeys(FIELDS, ""), **dict.fromkeys(NUMBERS, 0), "captured_audio_hours": 0.0}
        table.append({**blank, "person_name": row["archiveshelf_name"], "origin": "archiveshelf",
                      "identity": "excluded" if excluded else "unresolved", "state": "excluded" if excluded else "unresolved",
                      "earlier_work": "ArchiveShelf: " + (row.get("verification") or "named only"),
                      "next_step": "left out at the owner's request" if excluded else "establish who this name refers to"})
    order = {s: i for i, s in enumerate(STATES)}
    table.sort(key=lambda r: (order[r["state"]], -r["items_captured"], -r["items_listed"], r["person_name"].lower()))
    return table


def bashar_read_before():
    """(transcripts read in the 2026-10 transcript stage, recordings in the Bashar Index site's list)."""
    rows = rows_of(BASHAR_READ)
    return sum(1 for r in rows if r.get("transcript_status") == "retrieved"), len(rows)


def bashar_hosts(root=None):
    """The channels behind the 75 Bashar recordings: what kind each is, what was read earlier, what is here."""
    read = {r["video_id"]: r.get("transcript_status") == "retrieved" for r in rows_of(BASHAR_READ)}
    known = {r["channel"]: r for r in rows_of(SOURCES / "bashar_host_channels.csv")}
    feeds = collections.Counter(r["person_id"] for r in rows_of(SOURCES / "podcast_feeds.csv")
                                if r.get("relation") == "host" and r.get("verification") in ("verified", "name-match"))
    here = None
    if root is not None:
        catalogue = layout(root).root / "catalog" / "catalog.csv"
        if catalogue.exists():
            here = set()
            for row in read_csv(catalogue):
                if row.get("audio_status") == "ok" or row.get("has_text") == "1":
                    here.update(x for x in (row["item_id"], row.get("twin_of")) if x)
    groups = {}
    for row in rows_of(BASHAR_CSV):
        group = groups.setdefault(row["channel"], {"channel": row["channel"], "official": row.get("official") == "True",
                                                   "ids": [], "types": []})
        group["ids"].append(row["video_id"])
        group["types"].append(row.get("content_type") or "")
    out = []
    for group in groups.values():
        host_id = "host:" + slug(group["channel"].split("(")[0].strip(), "channel").lower()
        interviews = sum(1 for t in group["types"] if t.lower().startswith("interview"))
        kind = ("official channel" if group["official"] else "interview show" if interviews
                else "re-upload channel" if any("re-upload" in t.lower() for t in group["types"]) else "clip channel")
        total = len(group["ids"])
        captured = "" if here is None else sum(1 for v in group["ids"] if v in here)
        info = known.get(group["channel"], {})
        state = ("captured" if captured and captured >= total else "partly captured" if captured
                 else "planned: podcast feed found" if feeds.get(host_id) else "planned: YouTube only")
        step = {"captured": "", "partly captured": "fetch the rest: YouTube lane on a home connection",
                "planned: podcast feed found": "download the episodes that match the indexed interviews",
                "planned: YouTube only": ("look for the show's own podcast feed (find_host_feeds.py); otherwise the YouTube lane "
                                          "on a home connection" if kind == "interview show"
                                          else "YouTube lane on a home connection")}[state]
        out.append({"channel": group["channel"], "host_id": host_id, "kind": kind, "bashar_recordings": total,
                    "interviews": interviews, "transcripts_read_earlier": sum(1 for v in group["ids"] if read.get(v)),
                    "youtube_channel_url": info.get("channel_url", ""), "youtube_channel_id": info.get("channel_id", ""),
                    "websites": info.get("websites", ""), "podcast_feeds": feeds.get(host_id, 0), "captured_here": captured,
                    "state": state, "next_step": step})
    order = {s: i for i, s in enumerate(HOST_STATES)}
    out.sort(key=lambda r: (order[r["state"]], -r["bashar_recordings"], r["channel"].lower()))
    return out


def summarise(table, hosts):
    by_state = collections.Counter(r["state"] for r in table)
    by_origin = collections.Counter(r["origin"] for r in table)
    cross = collections.Counter((r["origin"], r["state"]) for r in table)
    totals = {key: sum(r[key] for r in table) for key in NUMBERS}
    totals["captured_audio_hours"] = round(sum(r["captured_audio_hours"] for r in table), 1)
    for key in ("videos_listed", "live_listed", "shorts_listed"):
        totals[key] = sum(number(r[key]) for r in table)
    totals["listed_video_hours"] = round(sum(float(r["listed_video_hours"] or 0) for r in table), 1)
    return {"generated": utc_now(), "targets": len(table),
            "by_state": {s: by_state.get(s, 0) for s in STATES}, "by_origin": dict(sorted(by_origin.items())),
            "by_origin_and_state": [{"origin": o, "state": s, "targets": n} for (o, s), n in sorted(cross.items())],
            "with_channel": sum(1 for r in table if r["youtube_channel_url"]),
            "with_channel_listing": sum(1 for r in table if r["videos_listed"] != ""),
            "with_official_site": sum(1 for r in table if r["official_sites"]), "totals": totals,
            "bashar": {"host_channels": len(hosts), "recordings": sum(h["bashar_recordings"] for h in hosts),
                       "interviews": sum(h["interviews"] for h in hosts),
                       "transcripts_read_earlier": sum(h["transcripts_read_earlier"] for h in hosts),
                       "captured_here": sum(number(h["captured_here"]) for h in hosts),
                       "by_kind": dict(collections.Counter(h["kind"] for h in hosts)),
                       "by_state": dict(collections.Counter(h["state"] for h in hosts))}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--no-private", action="store_true",
                    help="build from the committed lists and the committed coverage snapshot only")
    ap.add_argument("--out", type=Path, default=ET_ROOT / "plan", help="folder for the three files (default plan/)")
    args = ap.parse_args()
    root = None if args.no_private else ensure_outside_git(args.root)
    table, hosts = build(root), bashar_hosts(root)
    summary = summarise(table, hosts)
    write_csv(args.out / "targets.csv", table, FIELDS)
    write_csv(args.out / "bashar_host_channels.csv", hosts, HOST_FIELDS)
    atomic_write_text(args.out / "targets_summary.json", json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    print(f"targets {len(table)}: " + ", ".join(f"{n} {s}" for s, n in summary["by_state"].items() if n)
          + f"\norigins {summary['by_origin']} | {summary['with_channel']} with a channel, "
          f"{summary['with_channel_listing']} listed in full | Bashar recordings {summary['bashar']['recordings']} on "
          f"{len(hosts)} channels, {summary['bashar']['captured_here']} here -> {args.out / 'targets.csv'}")


if __name__ == "__main__":
    main()
