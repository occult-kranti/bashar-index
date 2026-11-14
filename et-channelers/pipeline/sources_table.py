#!/usr/bin/env python3
"""Every source of every tracked person, with its link, how it is collected, and how far collection got.

The dashboard's "Sources" section and the "How each source is collected" table come from here.

Writes
  plan/sources.csv   one row per source of one person: a YouTube channel, an official site, a podcast of
                     their own, an interview show that names them, audio files on their own site, text
                     pages on their own site, recordings on archive.org, earlier research. Each row gives
                     a link a person can open, the address the pipeline reads (feed, site), the method
                     (an id from methods.csv) and the chain of steps, what it yields (audio, text, a list),
                     whether that works from a cloud server, the evidence that the source is the person's
                     own, and how many items are listed and how many are in the archive.
  plan/methods.csv   one row per method: what it collects, the tool that does it, whether it works from a
                     cloud server, and the rules it keeps.

Public addresses only: channels, sites, feeds and catalogue pages. No address of a single recording, no
title, no text. Counts come from the private catalogue (catalog.py) when there is one; with --no-private
they are left empty.

    python3 pipeline/catalog.py && python3 pipeline/sources_table.py
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, ensure_outside_git, host_of, latest_by_key, layout, read_csv,  # noqa: E402
                    read_jsonl, utc_now, write_csv)
from feeds import feed_key  # noqa: E402

SOURCES = ET_ROOT / "sources"
PLAN = ET_ROOT / "plan"
INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
SITE = "https://occult-kranti.github.io/bashar-index/"
ARCHIVESHELF = "https://github.com/occult-kranti/archiveshelf"
FIELDS = ["source_id", "person_id", "person_name", "kind", "source", "link", "data_link", "method", "chain", "collects",
          "from_cloud", "verification", "items_listed", "items_here", "status", "note"]
METHOD_FIELDS = ["method", "name", "collects", "from_cloud", "tool", "how", "rules"]
KIND_ORDER = ("youtube channel", "official site", "own podcast", "audio on own site", "texts on own site", "archive.org",
              "interview show", "earlier research")

# The ways a source is collected. "from_cloud" says whether it works from a cloud server such as this
# Codespace: YouTube refuses audio and caption requests from data-centre addresses.
METHODS = [
    ("youtube-listing", "YouTube channel listing", "list of videos, live streams and shorts (titles, lengths)", "yes",
     "discover.py (yt-dlp --flat-playlist on the Videos, Live and Shorts tabs)",
     "Asks YouTube for the channel's public lists. No media is requested.",
     "One channel at a time, 5 s apart; stops after three refusals."),
    ("youtube-channel-page", "YouTube channel page", "channel id, subscribers, the websites the channel declares", "yes",
     "discover_sites.py", "Reads the schema.org data on the channel's public page.",
     "robots.txt read first; 4 s between pages; stops after three refusals."),
    ("youtube-oembed", "YouTube embed lookup", "the channel of a recording, and whether it is still online", "yes",
     "host_channels.py", "YouTube's public oEmbed answer for one recording.", "robots.txt read first; 4 s between requests."),
    ("youtube-audio", "YouTube audio", "audio", "no",
     "download_audio.py, through run_all.py on a home connection",
     "yt-dlp fetches a small audio stream, which is re-encoded to mono 24 kbps Opus.",
     "Refused from cloud servers (bot check). Nothing tries to get past that: it runs on the owner's computer."),
    ("youtube-captions", "YouTube captions", "text (YouTube's own caption tracks)", "no",
     "fetch_captions.py, through run_all.py on a home connection", "Named English caption tracks only, no machine translations.",
     "Refused from cloud servers, like the audio."),
    ("podcast-search", "Apple Podcasts search", "the RSS address of a show", "yes", "find_feeds.py, find_host_feeds.py",
     "Apple's public search API. A show counts only when its own website or the person's site vouches for it.",
     "About 20 calls a minute at most; namesakes are set aside."),
    ("podcast-feed", "Podcast feed (RSS)", "episode list, lengths, transcript links", "yes", "fetch_feeds.py",
     "Reads the feed every podcast app reads.", "One feed per host at a time; stops a host after three refusals."),
    ("podcast-audio", "Podcast episode audio", "audio", "yes", "download_enclosures.py",
     "Downloads the file the feed hands to podcast apps and re-encodes it to 24 kbps Opus.",
     "Two downloads per host at most, one start a second; stops a host after refusals; a free-disk floor."),
    ("podcast-transcript", "Transcript the feed links", "text", "yes", "fetch_publisher_text.py",
     "The publisher's own transcript (<podcast:transcript>: VTT, SRT or HTML).",
     "A robots.txt that says no is obeyed; a site that cannot be reached is left alone for the run."),
    ("site-survey", "Official site survey", "what the site publishes (feeds, sitemap, podcast links)", "yes", "recon_sites.py",
     "Reads robots.txt, the home page and the sitemap. Saves addresses and counts only.",
     "robots.txt obeyed; one request a second per site."),
    ("site-pages", "Pages from the maker's sitemap", "text", "yes", "list_site_pages.py, fetch_publisher_text.py",
     "The address family that holds the maker's messages is chosen from the sitemap; each page's text is extracted.",
     "robots.txt obeyed for every page; one request a second per site."),
    ("creator-files", "Audio on the maker's own site", "audio", "yes", "select_episodes.py, download_enclosures.py",
     "Recordings the maker offers for free download on their own site.", "As for podcast audio."),
    ("archive-org", "archive.org items", "audio (video items listed only)", "yes", "list_archive_org.py, download_enclosures.py",
     "archive.org's public metadata service lists each item's files; audio files are downloaded.",
     "robots.txt read first; one request a second; video files of several gigabytes are not fetched from here."),
    ("interview-kind", "Interview type", "the kind of each interview episode", "yes", "interview_types.py",
     "A reader given the whole transcript (a small model, checked on a sample), or show notes that say the session is "
     "channeled live. A title never decides.", "Only interviews with live channeling are downloaded."),
    ("speech-to-text", "Speech-to-text made here", "text with timestamps", "yes", "transcribe.py",
     "faster-whisper base.en (base for German), on audio already downloaded.", "Kept apart from texts that come from the source."),
    ("earlier-research", "Earlier research", "digests, lists and inventories", "yes", "the Bashar Index site; ArchiveShelf",
     "Work done before this pipeline: the Bashar Index digests (from auto-transcripts, 2026-10) and ArchiveShelf's inventory.",
     "Their counts are shown as they were recorded."),
]
CHAINS = {
    "youtube channel": "youtube-listing, youtube-channel-page, youtube-audio, youtube-captions",
    "official site": "site-survey",
    "own podcast": "podcast-search, podcast-feed, podcast-audio, podcast-transcript, speech-to-text",
    "audio on own site": "creator-files, speech-to-text",
    "texts on own site": "site-pages",
    "archive.org": "archive-org, speech-to-text",
    "interview show": "podcast-search, podcast-feed, interview-kind, podcast-audio, podcast-transcript, speech-to-text",
    "earlier research": "earlier-research",
}
PRIMARY = {"youtube channel": "youtube-listing", "official site": "site-survey", "own podcast": "podcast-audio",
           "audio on own site": "creator-files", "texts on own site": "site-pages", "archive.org": "archive-org",
           "interview show": "interview-kind", "earlier research": "earlier-research"}
COLLECTS = {"youtube channel": "list (audio and captions need a home connection)", "official site": "list",
            "own podcast": "audio, text", "audio on own site": "audio", "texts on own site": "text", "archive.org": "audio",
            "interview show": "audio, text (live channeling only)", "earlier research": "list"}


def https(url: str) -> str:
    """The address if it is a plain https address, otherwise nothing: only such links reach the dashboard."""
    url = (url or "").strip()
    return url if url.lower().startswith("https://") and host_of(url) else ""


def site_link(domain: str) -> str:
    return https(f"https://{domain.strip().removeprefix('https://').removeprefix('http://').strip('/')}/")


def apple_page(apple_id) -> str:
    return f"https://podcasts.apple.com/podcast/id{apple_id}" if str(apple_id or "").isdigit() else ""


def names():
    """{person_id: display name} from the target list, else the index."""
    out = {}
    if (PLAN / "targets.csv").exists():
        out = {r["person_id"]: r["person_name"] for r in read_csv(PLAN / "targets.csv") if r.get("person_id")}
    if INDEX.exists():
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            out.setdefault(channel["person"], channel.get("person_name") or channel["person"])
    return out


def bare(host: str) -> str:
    return (host or "").lower().removeprefix("www.")


def catalogue_counts(root):
    """({(person, kind, key): [listed, here]}, {(person, show): Counter(interview kind)}) from the private
    catalogue, or (None, None) without one."""
    if root is None:
        return None, None
    path = layout(root).root / "catalog" / "catalog.csv"
    if not path.exists():
        return None, None
    counts = collections.defaultdict(lambda: [0, 0])
    talks = collections.defaultdict(collections.Counter)
    files_page = {r.get("media_url", "").strip(): bare(host_of(r.get("official_page") or ""))
                  for r in read_csv(SOURCES / "creator_files.csv")} if (SOURCES / "creator_files.csv").exists() else {}
    for row in read_csv(path):
        person, relation, lane = row.get("person_id") or "", row.get("relation") or "", row.get("lane") or ""
        got = int(row.get("audio_status") == "ok" or row.get("has_text") == "1")
        if lane == "youtube":
            key = (person, "youtube channel", "")
        elif relation == "own":
            key = (person, "own podcast", row.get("feed_key") or "")
        elif relation == "host":
            key = (person, "interview show", (row.get("feed_key") or "").rsplit("--", 1)[0])
            talks[(person, key[2])][row.get("interview_type") or "not classified"] += 1
        elif relation == "file":
            key = (person, "audio on own site", files_page.get(row.get("source_url", "").strip()) or bare(host_of(row.get("source_url") or "")))
        elif relation == "page":
            key = (person, "texts on own site", bare(host_of(row.get("source_url") or "") or row.get("source_host") or ""))
        elif relation == "archive":
            key = (person, "archive.org", "")
        else:
            continue
        counts[key][0] += 1
        counts[key][1] += got
    return counts, talks


def site_surveys(root):
    """{domain: one line on what the site survey found}, from the private survey file."""
    if root is None:
        return {}
    out = {}
    for rec in latest_by_key(read_jsonl(layout(root).sources / "site_recon.jsonl"), "domain").values():
        domain = bare(rec.get("domain") or "")
        if rec.get("status") != "ok":
            out[domain] = "survey refused or unreachable"
            continue
        parts = []
        if rec.get("podcasts"):
            parts.append(f"{len(rec['podcasts'])} podcast link(s)")
        if rec.get("post_feeds"):
            parts.append(f"{len(rec['post_feeds'])} post feed(s)")
        parts.append(f"{rec.get('sitemap_urls', 0)} sitemap addresses, {rec.get('sitemap_post_like', 0)} post-like")
        out[domain] = "surveyed: " + ", ".join(parts)
    return out


UNCOUNTED = ("official site", "earlier research")     # sources that hold no items of their own


def build(root=None):
    who = names()
    counts, talks = catalogue_counts(root)
    surveys = site_surveys(root)
    rows = []

    def add(person, kind, source, link, data_link="", verification="", status="", note="", key=""):
        listed, here = ("", "") if counts is None or kind in UNCOUNTED else counts.get((person, kind, key), [0, 0])
        rows.append({"person_id": person, "person_name": who.get(person, person), "kind": kind, "source": source,
                     "link": https(link), "data_link": https(data_link), "method": PRIMARY[kind], "chain": CHAINS[kind],
                     "collects": COLLECTS[kind], "from_cloud": "no" if kind == "youtube channel" else "yes",
                     "verification": verification, "items_listed": listed, "items_here": here, "status": status, "note": note})

    # YouTube channels: the index, the channels added since, and the target list (which also carries the
    # channels named by the ArchiveShelf intake)
    channels = {}
    if INDEX.exists():
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            info = channel.get("channel") or {}
            if str(info.get("url") or "").startswith("https://"):
                channels[channel["person"]] = (info["url"], "found for the Bashar index (2026-10-23)")
    for row in read_csv(SOURCES / "extra_channels.csv") if (SOURCES / "extra_channels.csv").exists() else []:
        if row.get("person_id") and str(row.get("channel_url") or "").startswith("https://"):
            channels.setdefault(row["person_id"], (row["channel_url"], (row.get("evidence") or "")[:160]))
    for row in read_csv(PLAN / "targets.csv") if (PLAN / "targets.csv").exists() else []:
        if row.get("person_id") and str(row.get("youtube_channel_url") or "").startswith("https://"):
            channels.setdefault(row["person_id"], (row["youtube_channel_url"], "named in the ArchiveShelf channel intake"))
    for person, (url, evidence) in sorted(channels.items()):
        add(person, "youtube channel", "YouTube channel", url, verification=evidence,
            status="listed; audio and captions wait for a home connection")
    # official sites
    for row in read_csv(SOURCES / "official_sites.csv") if (SOURCES / "official_sites.csv").exists() else []:
        add(row["person_id"], "official site", row["domain"], site_link(row["domain"]),
            verification=(row.get("evidence") or "")[:200],
            status=surveys.get(bare(row["domain"]), "not surveyed yet" if root is not None else ""))
    # podcasts: the person's own, and the interview shows
    shows = {}
    for row in read_csv(SOURCES / "podcast_feeds.csv") if (SOURCES / "podcast_feeds.csv").exists() else []:
        if row.get("verification") not in ("verified", "name-match"):
            continue
        link = apple_page(row.get("apple_id")) or https(row.get("site_link") or "") or row["feed_url"]
        title = row.get("podcast_title") or host_of(row["feed_url"])
        if row.get("relation") == "own":
            add(row["person_id"], "own podcast", title, link, row["feed_url"],
                verification=f"{row['verification']}: {(row.get('evidence') or '')[:160]}", status="",
                key=feed_key(row["person_id"], row["feed_url"]))
        elif row.get("relation") == "host":
            shows[row["person_id"].replace(":", "-")] = (title, link, row["feed_url"], row["verification"])
    if counts is not None:
        for (person, kind, key), (listed, here) in sorted(counts.items()):
            if kind == "interview show" and key in shows:
                title, link, feed, grade = shows[key]
                kinds = talks.get((person, key), collections.Counter())
                said = ", ".join(f"{n} {k}" for k, n in kinds.most_common())
                add(person, "interview show", title, link, feed, verification=f"{grade}: the show's own feed", key=key,
                    note=f"{said}; only interviews with live channeling are downloaded")
    # files and pages on the maker's own site, grouped by site
    hosts = collections.Counter()
    for row in read_csv(SOURCES / "creator_files.csv") if (SOURCES / "creator_files.csv").exists() else []:
        hosts[(row["person_id"], bare(host_of(row.get("official_page") or "") or host_of(row.get("media_url") or "")))] += 1
    for (person, host), n in sorted(hosts.items()):
        add(person, "audio on own site", f"Audio files on {host}", site_link(host),
            verification="offered for free download on the maker's own site", key=host, note=f"{n} files registered")
    pages = collections.Counter()
    for row in read_csv(SOURCES / "publisher_pages.csv") if (SOURCES / "publisher_pages.csv").exists() else []:
        pages[(row["person_id"], bare(host_of(row.get("page_url") or "")))] += 1
    for (person, host), n in sorted(pages.items()):
        add(person, "texts on own site", f"Text pages on {host}", site_link(host),
            verification="listed in the site's own sitemap or index; the site is the person's", key=host,
            note=f"{n} pages registered")
    # archive.org
    deposits = collections.defaultdict(lambda: collections.Counter())
    for row in read_csv(SOURCES / "archive_org_sessions.csv") if (SOURCES / "archive_org_sessions.csv").exists() else []:
        deposits[row["person_id"]][row["kind"]] += 1
    for person, kinds in sorted(deposits.items()):
        add(person, "archive.org", "Recordings deposited on archive.org", "https://archive.org/search?query=identifier%3Abashar-%2A"
            if person == "darryl-anka" else "https://archive.org/",
            "https://archive.org/metadata/", verification="the items the Bashar Index session catalogue cites" if person == "darryl-anka" else "",
            note=f"{kinds['audio']} audio files; {kinds['video']} video files listed, not fetched from here")
    # earlier research
    add("darryl-anka", "earlier research", "The Bashar Index site", SITE,
        verification="75 recordings digested from auto-transcripts, a 684-session catalogue, 48 podcast appearances",
        status="used for the tables of this dashboard")
    for row in read_csv(SOURCES / "archiveshelf_intake.csv") if (SOURCES / "archiveshelf_intake.csv").exists() else []:
        held = (row.get("captured_by_archiveshelf") or "").strip()
        if row.get("person_id") and held and held != "nothing":
            add(row["person_id"], "earlier research", "ArchiveShelf", ARCHIVESHELF, verification=held[:200],
                status="taken into this archive where the source allowed")
    # status from the counts
    for row in rows:
        listed, here = row["items_listed"], row["items_here"]
        if row["status"] or listed in ("", 0):
            if not row["status"] and counts is not None:
                row["status"] = "registered, nothing listed yet"
            continue
        row["status"] = ("all here" if here >= listed else f"{here} of {listed} here" if here else "listed, none here yet")
    order = {k: i for i, k in enumerate(KIND_ORDER)}
    rows.sort(key=lambda r: (r["person_name"].lower(), order[r["kind"]], r["source"].lower()))
    for n, row in enumerate(rows, 1):
        row["source_id"] = f"s{n:04d}"
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--no-private", action="store_true", help="from the committed lists only: counts stay empty")
    ap.add_argument("--out", type=Path, default=PLAN)
    args = ap.parse_args()
    root = None if args.no_private else ensure_outside_git(args.root)
    rows = build(root)
    write_csv(args.out / "sources.csv", rows, FIELDS)
    write_csv(args.out / "methods.csv", [dict(zip(METHOD_FIELDS, m)) for m in METHODS], METHOD_FIELDS)
    kinds = collections.Counter(r["kind"] for r in rows)
    print(f"{len(rows)} sources for {len({r['person_id'] for r in rows})} people ({', '.join(f'{n} {k}' for k, n in kinds.most_common())}); "
          f"{len(METHODS)} methods -> {args.out / 'sources.csv'} ({utc_now()})")


if __name__ == "__main__":
    main()
