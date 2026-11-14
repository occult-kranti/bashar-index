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

The counts of a row:
  items_listed       what the source lists: a channel's own listing (its Videos, Live and Shorts tabs), a
                     feed's episodes, the files or pages registered for a site, the archive.org recordings
  items_here         how many of them are in the archive as what the source yields: audio for a channel,
                     a podcast, files, archive.org and an interview show; text for text pages
  audio_here, texts_from_source, texts_made_here
                     the three kinds of holding, each on its own and never added together: audio, a text
                     the source itself published (a page, a feed's transcript, a caption track), and
                     speech-to-text made here
  counts_as_of       when the private catalogue the counts come from was built
Every catalogue item is counted on one row, except YouTube videos that are not in a channel's own listing
(the Bashar Index recordings on other channels, which plan/bashar_host_channels.csv covers) and items that
no list holds any more. Items the catalogue holds that no committed list names get a row of their own.

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
import time
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
# What ArchiveShelf named and held, as this project recorded it (a public page of this repository). The
# ArchiveShelf repository itself holds third-party transcripts and audio and is not linked from here.
ARCHIVESHELF = "https://github.com/occult-kranti/bashar-index/blob/main/et-channelers/sources/archiveshelf_intake.csv"
FIELDS = ["source_id", "person_id", "person_name", "kind", "source", "link", "data_link", "method", "chain", "collects",
          "from_cloud", "verification", "items_listed", "items_here", "audio_here", "texts_from_source", "texts_made_here",
          "status", "note", "counts_as_of"]
COUNT_FIELDS = {"items_listed": "listed", "items_here": "here", "audio_here": "audio", "texts_from_source": "source",
                "texts_made_here": "made"}
# Since this commit (e13d1e4) an interview's audio is queued only when it has live channeling; audio fetched
# before it is kept whatever its kind.
LIVE_ONLY_SINCE = "2026-11-14T00:26:40Z"
METHOD_FIELDS = ["method", "name", "collects", "from_cloud", "tool", "how", "rules"]
KIND_ORDER = ("youtube channel", "official site", "own podcast", "audio on own site", "texts on own site", "archive.org",
              "interview show", "earlier research")

# The ways a source is collected. "from_cloud" says whether it works from a cloud server such as this
# Codespace: YouTube refuses audio and caption requests from data-centre addresses. Whatever the connection,
# the steps that request paths youtube.com's robots.txt disallows are off until the owner decides (common.py).
METHODS = [
    ("youtube-listing", "YouTube channel listing", "list of videos, live streams and shorts (titles, lengths)", "yes",
     "discover.py (yt-dlp --flat-playlist on the Videos, Live and Shorts tabs)",
     "Asks YouTube for the channel's public lists. No media is requested.",
     "Off by rule until the owner decides: yt-dlp asks youtube.com's /youtubei/ for every page after the first, and its "
     "robots.txt disallows that path (ET_YOUTUBE_ROBOTS_OVERRIDE=1 turns it on). When on: one channel at a time, 5 s "
     "apart; stops after three refusals, and lists nothing until a day has passed."),
    ("youtube-channel-page", "YouTube channel page", "channel id, subscribers, the websites the channel declares", "yes",
     "discover_sites.py", "Reads the schema.org data on the channel's public page.",
     "robots.txt read first (it allows channel pages); 4 s between pages; stops after three refusals."),
    ("youtube-oembed", "YouTube embed lookup", "the channel of a recording, and whether it is still online", "yes",
     "host_channels.py", "YouTube's public oEmbed answer for one recording.",
     "robots.txt read first (it allows /oembed); 4 s between requests."),
    ("youtube-audio", "YouTube audio", "audio", "no",
     "download_audio.py, through run_all.py on a home connection",
     "yt-dlp fetches a small audio stream, which is re-encoded to mono 24 kbps Opus.",
     "Off by rule until the owner decides: the player is asked through youtube.com's /youtubei/, which its robots.txt "
     "disallows (ET_YOUTUBE_ROBOTS_OVERRIDE=1 turns it on). Refused from cloud servers too (bot check); nothing tries "
     "to get past that."),
    ("youtube-captions", "YouTube captions", "text (YouTube's own caption tracks)", "no",
     "fetch_captions.py, through run_all.py on a home connection", "Named English caption tracks only, no machine translations.",
     "Off by rule until the owner decides, like the audio (/youtubei/ and /api/ are disallowed by youtube.com's "
     "robots.txt); refused from cloud servers too."),
    ("podcast-search", "Apple Podcasts search", "the RSS address of a show", "yes", "find_feeds.py, find_host_feeds.py",
     "Apple's public search API. A show counts only when its own website or the person's site vouches for it.",
     "About 20 calls a minute at most; namesakes are set aside."),
    ("podcast-feed", "Podcast feed (RSS)", "episode list, lengths, transcript links", "yes", "fetch_feeds.py",
     "Reads the feed every podcast app reads.", "One feed per host at a time; obeys Retry-After; stops a host after three refusals; a host that refused rests a day or more."),
    ("podcast-audio", "Podcast episode audio", "audio", "yes", "download_enclosures.py",
     "Downloads the file the feed hands to podcast apps and re-encodes it to 24 kbps Opus.",
     "Two downloads at most per first host, one start a second per host, every host a redirect leads to included; one downloader at a time; obeys Retry-After (with a 403, 429 or 503); stops a host after refusals, and a host that refused rests a day or more; a free-disk floor."),
    ("podcast-transcript", "Transcript the feed links", "text", "yes", "fetch_publisher_text.py",
     "The publisher's own transcript (<podcast:transcript>: VTT, SRT or HTML).",
     "A robots.txt that says no is obeyed; obeys Retry-After; a site that cannot be reached is left alone for the run, one that refused for a day or more."),
    ("site-survey", "Official site survey", "what the site publishes (feeds, sitemap, podcast links)", "yes", "recon_sites.py",
     "Reads robots.txt, the home page and the sitemap. Saves addresses and counts only.",
     "robots.txt obeyed; one request a second per site."),
    ("site-pages", "Pages from the maker's sitemap", "text", "yes", "list_site_pages.py, fetch_publisher_text.py",
     "The address family that holds the maker's messages is chosen from the sitemap; each page's text is extracted.",
     "robots.txt obeyed for every page; one request a second per site; obeys Retry-After; a site that refused rests a day or more."),
    ("creator-files", "Audio on the maker's own site", "audio", "yes", "select_episodes.py, download_enclosures.py",
     "Recordings the maker offers for free download on their own site.", "As for podcast audio."),
    ("archive-org", "archive.org items", "audio (video items listed only)", "yes", "list_archive_org.py, download_enclosures.py",
     "archive.org's public metadata service lists each item's files; audio files are downloaded.",
     "robots.txt read first; one request a second; video files of several gigabytes are not fetched from here."),
    ("interview-kind", "Interview type", "the kind of each interview episode", "yes", "interview_types.py",
     "A reader given the whole transcript (a small model, checked on a sample), or show notes that say the session is "
     "channeled live. A title never decides.",
     "Audio is queued only for interviews with live channeling (since 14 November; audio fetched earlier is kept "
     "whatever its kind); the feed's own transcripts are fetched for every listed episode. The show notes come from "
     "the feed read, under its rules."),
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
COLLECTS = {"youtube channel": "list (off by rule until the owner decides; audio and captions also need a home connection)",
            "official site": "list",
            "own podcast": "audio, text", "audio on own site": "audio", "texts on own site": "text", "archive.org": "audio",
            "interview show": "audio (live channeling only), text", "earlier research": "list"}
# What "here" counts for each kind of source: what its method yields. Text for text pages, audio for the rest.
HERE_IS = {"texts on own site": "source"}


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
    """What the private catalogue holds, or Nones without one:
      counts   {(person, kind, key): Counter(listed, here, audio, source, made)}
      talks    {(person, show): {interview kind: Counter(listed, audio, audio_before_rule, text_only)}}
      as_of    when the catalogue was built
      outside  how many items no row counts: YouTube videos in no channel's own listing, and items no list
               holds any more"""
    if root is None:
        return None, None, "", 0
    paths = layout(root)
    path = paths.root / "catalog" / "catalog.csv"
    if not path.exists():
        return None, None, "", 0
    counts = collections.defaultdict(collections.Counter)
    talks = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    files_page = {r.get("media_url", "").strip(): bare(host_of(r.get("official_page") or ""))
                  for r in read_csv(SOURCES / "creator_files.csv")} if (SOURCES / "creator_files.csv").exists() else {}
    fetched = {k: v.get("started") or "" for k, v in latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl")).items()
               if v.get("status") == "ok"}
    outside = 0
    for row in read_csv(path):
        person, relation, lane = row.get("person_id") or "", row.get("relation") or "", row.get("lane") or ""
        if lane == "youtube":
            if not row.get("tab"):
                outside += 1          # not in a channel's own listing: a recording on someone else's channel
                continue
            key = (person, "youtube channel", "")
        elif relation == "own":
            key = (person, "own podcast", row.get("feed_key") or "")
        elif relation == "host":
            key = (person, "interview show", (row.get("feed_key") or "").rsplit("--", 1)[0])
        elif relation == "file":
            key = (person, "audio on own site", files_page.get(row.get("source_url", "").strip()) or bare(host_of(row.get("source_url") or "")))
        elif relation == "page":
            key = (person, "texts on own site", bare(host_of(row.get("source_url") or "") or row.get("source_host") or ""))
        elif relation == "archive":
            key = (person, "archive.org", "")
        else:
            outside += 1              # no list holds it any more (a failed download of an episode since dropped)
            continue
        held = {"audio": row.get("audio_status") == "ok", "source": row.get("text_from_source") == "1",
                "made": row.get("text_made_here") == "1"}
        count = counts[key]
        count["listed"] += 1
        count["here"] += held[HERE_IS.get(key[1], "audio")]
        for what, yes in held.items():
            count[what] += yes
        if key[1] == "interview show":
            talk = talks[(person, key[2])][row.get("interview_type") or "not classified"]
            talk["listed"] += 1
            talk["audio"] += held["audio"]
            talk["audio_before_rule"] += held["audio"] and "" < fetched.get(row.get("item_id"), "") < LIVE_ONLY_SINCE
            talk["text_only"] += held["source"] and not held["audio"]
    built, made = path.stat().st_mtime, ""
    summary = paths.public / "coverage.json"            # catalog.py writes it right after the catalogue, with the time
    try:
        if summary.stat().st_mtime >= built:
            made = json.loads(summary.read_text(encoding="utf-8")).get("generated") or ""
    except (OSError, ValueError):
        pass
    as_of = made or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(built))
    return counts, talks, as_of, outside


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


def interview_note(kinds):
    """What a show's listed episodes are, by kind, and what is held of the kinds whose audio is not queued."""
    said = ", ".join(f"{c['listed']} {k}" for k, c in sorted(kinds.items(), key=lambda kv: (-kv[1]["listed"], kv[0])))
    note = f"{said}; audio is queued only for live channeling, the feed's own transcript for every listed episode"
    other = [c for k, c in kinds.items() if k != "live channeling"]
    before = sum(c["audio_before_rule"] for c in other)
    since = sum(c["audio"] for c in other) - before
    text = sum(c["text_only"] for c in other)
    held = [part for part in (f"{before} as audio fetched before that rule (14 November) and kept" if before else "",
                              f"{since} as audio fetched since" if since else "",
                              f"{text} as the feed's transcript only" if text else "") if part]
    return note + (f"; of the other kinds, {', '.join(held)}" if held else "")


def imported_from(root):
    """{(person, host): where the texts were imported from}, for publisher texts taken in from earlier work."""
    out = collections.defaultdict(collections.Counter)
    for rec in latest_by_key(read_jsonl(layout(root).pubtext / "publisher_text_manifest.jsonl")).values():
        if rec.get("status") == "ok" and rec.get("origin") == "import":
            where = str(rec.get("imported_from") or "earlier work").split(",")[0].strip()
            out[(rec.get("channel_dir") or "", bare(rec.get("source_host") or ""))][where] += 1
    return {k: c.most_common(1)[0][0] for k, c in out.items()}


def build(root=None, said=None):
    """The rows of plan/sources.csv. Notes for the person running it go into `said` (a list), if given."""
    from select_episodes import distinct_archive_audio
    said = [] if said is None else said
    who = names()
    counts, talks, as_of, outside = catalogue_counts(root)
    surveys = site_surveys(root)
    rows, read = [], set()

    def add(person, kind, source, link, data_link="", verification="", status="", note="", key=""):
        read.add((person, kind, key))
        unknown = counts is None or kind in UNCOUNTED
        count = None if unknown else counts.get((person, kind, key))
        if count is None and kind == "youtube channel":
            unknown = True               # never listed: what the channel holds is not known, which is not none
        count = count or collections.Counter()
        rows.append({"person_id": person, "person_name": who.get(person, person), "kind": kind, "source": source,
                     "link": https(link), "data_link": https(data_link), "method": PRIMARY[kind], "chain": CHAINS[kind],
                     "collects": COLLECTS[kind], "from_cloud": "no" if kind == "youtube channel" else "yes",
                     "verification": verification,
                     **{field: "" if unknown else count[name] for field, name in COUNT_FIELDS.items()},
                     "status": status, "note": note, "counts_as_of": "" if unknown else as_of})

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
        listed = counts is not None and (person, "youtube channel", "") in counts
        add(person, "youtube channel", "YouTube channel", url, verification=evidence,
            status="listed; YouTube is off by rule until the owner decides (its robots.txt)" if listed
            else "not listed yet" if counts is not None else "")
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
        for (person, kind, key) in sorted(counts):
            if kind == "interview show" and key in shows:
                title, link, feed, grade = shows[key]
                add(person, "interview show", title, link, feed, verification=f"{grade}: the show's own feed", key=key,
                    note=interview_note(talks.get((person, key), {})))
    # files and pages on the maker's own site, grouped by site
    files = read_csv(SOURCES / "creator_files.csv") if (SOURCES / "creator_files.csv").exists() else []
    hosts = collections.Counter()
    for row in files:
        hosts[(row["person_id"], bare(host_of(row.get("official_page") or "") or host_of(row.get("media_url") or "")))] += 1
    for (person, host), n in sorted(hosts.items()):
        add(person, "audio on own site", f"Audio files on {host}", site_link(host),
            verification="offered for free download on the maker's own site", key=host, note=f"{n} files registered")
    offered = {(row.get("official_page") or "").strip() for row in files} - {""}
    pages, paired = collections.Counter(), collections.Counter()
    for row in read_csv(SOURCES / "publisher_pages.csv") if (SOURCES / "publisher_pages.csv").exists() else []:
        where = (row["person_id"], bare(host_of(row.get("page_url") or "")))
        pages[where] += 1
        paired[where] += (row.get("page_url") or "").strip() in offered
    for (person, host), n in sorted(pages.items()):
        # a page that offers an audio file is counted once, with that file, on the audio row
        k = paired[(person, host)]
        add(person, "texts on own site", f"Text pages on {host}", site_link(host),
            verification="listed in the site's own sitemap or index; the site is the person's", key=host,
            note=f"{n} pages registered" + (f", {k} of them counted with the audio file they offer" if k else ""))
    # archive.org
    deposits = collections.defaultdict(lambda: collections.Counter())
    listed_files = read_csv(SOURCES / "archive_org_sessions.csv") if (SOURCES / "archive_org_sessions.csv").exists() else []
    for row in listed_files:
        deposits[row["person_id"]][row["kind"]] += 1
    distinct = collections.Counter(row["person_id"] for row in distinct_archive_audio(listed_files))
    for person, kinds in sorted(deposits.items()):
        twice = kinds["audio"] - distinct[person]
        add(person, "archive.org", "Recordings deposited on archive.org", "https://archive.org/search?query=identifier%3Abashar-%2A"
            if person == "darryl-anka" else "https://archive.org/",
            "https://archive.org/metadata/", verification="the items the Bashar Index session catalogue cites" if person == "darryl-anka" else "",
            note=f"{kinds['audio']} audio files listed"
                 + (f" ({twice} of them a second encoding of a recording, counted once)" if twice else "")
                 + f"; {kinds['video']} video files listed, not fetched from here")
    # earlier research
    add("darryl-anka", "earlier research", "The Bashar Index site", SITE,
        verification="75 recordings digested from auto-transcripts, a 684-session catalogue, 48 podcast appearances",
        status="used for the tables of this dashboard")
    for row in read_csv(SOURCES / "archiveshelf_intake.csv") if (SOURCES / "archiveshelf_intake.csv").exists() else []:
        held = (row.get("captured_by_archiveshelf") or "").strip()
        if row.get("person_id") and held and held != "nothing":
            add(row["person_id"], "earlier research", "ArchiveShelf", ARCHIVESHELF, verification=held[:200],
                status="taken into this archive where the source allowed")
    # what the catalogue holds that no registered source names: a row of its own, so no item goes uncounted
    if counts is not None:
        origins = None
        for (person, kind, key), count in sorted(counts.items()):
            if (person, kind, key) in read:
                continue
            if kind == "texts on own site" and key:
                origins = imported_from(root) if origins is None else origins
                origin = origins.get((person, key))
                add(person, kind, f"Text pages on {key}", site_link(key), key=key,
                    verification=(f"texts imported into this archive from earlier work ({origin})" if origin
                                  else "texts held in this archive") + "; their pages are not in sources/publisher_pages.csv",
                    note=f"{count['listed']} pages known only from the archive's own records")
            elif kind == "audio on own site" and key:
                add(person, kind, f"Audio files on {key}", site_link(key), key=key,
                    verification="audio held in this archive; its files are not in sources/creator_files.csv",
                    note=f"{count['listed']} files known only from the archive's own records")
            elif kind == "archive.org":
                add(person, kind, "Recordings deposited on archive.org", "https://archive.org/", "https://archive.org/metadata/",
                    note=f"{count['listed']} recordings known only from the archive's own records")
            else:
                said.append(f"note: {count['listed']} {kind} item(s) of {person} ({key or 'no key'}) have no registered "
                            "source, so no row counts them")
        if outside:
            said.append(f"note: {outside} catalogue item(s) are counted on no row: YouTube videos in no channel's own "
                        "listing (the Bashar Index recordings on other channels, whose channels plan/bashar_host_channels.csv "
                        "lists) and items no list holds any more")
    # status from the counts. A podcast or an interview show yields audio and the feed's own transcripts:
    # its status says which, so a show whose transcripts are held does not read "none here".
    for row in rows:
        listed, here = row["items_listed"], row["items_here"]
        if row["status"] or listed in ("", 0):
            if not row["status"] and counts is not None:
                row["status"] = "registered, nothing listed yet"
            continue
        if row["kind"] in ("own podcast", "interview show"):
            row["status"] = ("all here as audio" if here >= listed else f"{here} of {listed} here as audio" if here
                             else "none here as audio yet")
            if row["texts_from_source"]:
                row["status"] += f"; {row['texts_from_source']} with the feed's own transcript"
            continue
        row["status"] = ("all here" if here >= listed else f"{here} of {listed} here" if here else "listed, none here yet")
        if row["kind"] == "audio on own site" and row["texts_from_source"]:
            row["status"] += f"; {row['texts_from_source']} with the text of the page that offers it"
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
    said = []
    rows = build(root, said)
    for line in said:
        print(line, file=sys.stderr)
    write_csv(args.out / "sources.csv", rows, FIELDS)
    write_csv(args.out / "methods.csv", [dict(zip(METHOD_FIELDS, m)) for m in METHODS], METHOD_FIELDS)
    kinds = collections.Counter(r["kind"] for r in rows)
    print(f"{len(rows)} sources for {len({r['person_id'] for r in rows})} people ({', '.join(f'{n} {k}' for k, n in kinds.most_common())}); "
          f"{len(METHODS)} methods -> {args.out / 'sources.csv'} ({utc_now()})")


if __name__ == "__main__":
    main()
