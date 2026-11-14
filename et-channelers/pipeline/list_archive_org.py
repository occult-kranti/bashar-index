#!/usr/bin/env python3
"""List the recordings behind the Bashar session catalogue's archive.org entries.

The Bashar Index data package (data/session_catalog.csv at the top of this repository) catalogues 684
Bashar sessions from 1984 on. 393 of its rows point at an archive.org item: a recording somebody
deposited there. These are channeled sessions themselves, not talk about them, and archive.org serves
its files to any client. This script asks archive.org's public metadata service what each item holds
and writes one row per media file:

  audio   an audio file (tape transfers, mostly): small, queued like any other recording
  video   a video file, often several gigabytes: listed with its size, not queued from here

Nothing is downloaded by this script. robots.txt is read first, one request a second at most, and three
refusals in a row stop the run (exit code 3). The recordings belong to their rights holders (the Bashar
sessions: Darryl Anka / Bashar Communications, Inc.): what is fetched later stays in the private folder.

Reads   data/session_catalog.csv (repository root)
Writes  sources/archive_org_sessions.csv   person_id, identifier, session_date, title, file_name, media_url,
                                           kind, format, bytes, duration_s, evidence

    python3 pipeline/list_archive_org.py --limit 5
    python3 pipeline/list_archive_org.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ET_ROOT, Breaker, read_csv, utc_now, write_csv  # noqa: E402
from feeds import FetchError, get_bytes  # noqa: E402
from fetch_publisher_text import Robots  # noqa: E402

CATALOGUE = ET_ROOT.parent / "data" / "session_catalog.csv"
OUT = ET_ROOT / "sources" / "archive_org_sessions.csv"
FIELDS = ["person_id", "identifier", "session_date", "title", "file_name", "media_url", "kind", "format", "bytes",
          "duration_s", "evidence"]
AUDIO = re.compile(r"\.(?:mp3|m4a|ogg|oga|flac|wav|wma|aac|opus)$", re.I)
VIDEO = re.compile(r"\.(?:mp4|m4v|mkv|avi|mov|mpe?g|webm|ogv|flv|wmv)$", re.I)
ITEM = re.compile(r"^https?://archive\.org/details/([A-Za-z0-9._-]+)/?$")


def seconds(value):
    """archive.org gives a length as seconds ('6806.26') or as a clock ('1:53:26')."""
    text = str(value or "").strip()
    if not text:
        return ""
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return int(float(text))
    parts = text.split(":")
    if all(re.fullmatch(r"\d+(?:\.\d+)?", p) for p in parts) and 2 <= len(parts) <= 3:
        total = 0.0
        for part in parts:
            total = total * 60 + float(part)
        return int(total)
    return ""


def media_files(metadata: dict):
    """The files of one item worth listing: every original audio file, or, when the item has none, its
    original video files. A derivative (archive.org's own re-encoding) is left out when the original is there."""
    files = [f for f in metadata.get("files") or [] if isinstance(f, dict) and f.get("name")]
    originals = [f for f in files if f.get("source") == "original"] or files
    audio = [f for f in originals if AUDIO.search(f["name"])]
    if audio:
        return [("audio", f) for f in audio]
    return [("video", f) for f in originals if VIDEO.search(f["name"])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalogue", type=Path, default=CATALOGUE)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--person", default="darryl-anka", help="whose sessions the catalogue lists")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--min-interval", type=float, default=1.0)
    ap.add_argument("--stop-after-blocks", type=int, default=3)
    ap.add_argument("--refresh", action="store_true", help="ask again about items already listed")
    ap.add_argument("--timeout", type=int, default=40)
    args = ap.parse_args()

    wanted = []
    for row in read_csv(args.catalogue) if args.catalogue.exists() else []:
        found = ITEM.match((row.get("source_url") or "").strip())
        if found and found.group(1) not in [w[0] for w in wanted]:
            wanted.append((found.group(1), row))
    have = read_csv(args.out) if args.out.exists() else []
    done = set() if args.refresh else {r["identifier"] for r in have}
    todo = [w for w in wanted if w[0] not in done]
    print(f"archive.org items in the catalogue {len(wanted)} | already listed {len(wanted) - len(todo)} | to ask about {len(todo)}",
          file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N or --all", file=sys.stderr)
        todo = []
    elif args.limit:
        todo = todo[:args.limit]
    robots, breaker, last = Robots(), Breaker(args.stop_after_blocks), 0.0
    rows = [r for r in have if args.refresh is False or r["identifier"] not in {w[0] for w in todo}]
    for n, (identifier, entry) in enumerate(todo, 1):
        if breaker.tripped.is_set():
            break
        url = f"https://archive.org/metadata/{identifier}"
        if not robots.allowed(url):
            break
        wait = args.min_interval - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.monotonic()
        try:
            _, _, body = get_bytes(url, timeout=args.timeout, max_bytes=20_000_000)
            metadata = json.loads(body)
        except FetchError as err:
            if err.status in (403, 429):
                breaker.hard_block()
            continue
        except ValueError:
            continue
        breaker.success()
        base = {"person_id": args.person, "identifier": identifier, "session_date": entry.get("date") or "",
                "title": (entry.get("title") or "").strip()[:200]}
        found = media_files(metadata) if not metadata.get("is_dark") else []
        if not found:
            rows.append({**base, "kind": "none", "evidence": f"archive.org lists no audio or video file for this item ({utc_now()[:10]})"})
        for kind, item in found:
            rows.append({**base, "file_name": item["name"], "kind": kind, "format": item.get("format") or "",
                         "media_url": f"https://archive.org/download/{identifier}/{urllib.parse.quote(item['name'])}",
                         "bytes": item.get("size") or "", "duration_s": seconds(item.get("length")),
                         "evidence": f"file of the archive.org item the Bashar Index session catalogue cites for this session; "
                                     f"listed by archive.org's metadata service on {utc_now()[:10]}"})
        if n % 25 == 0 or n == len(todo):
            print(f"[archive.org] {n}/{len(todo)} items asked about", file=sys.stderr, flush=True)
            write_csv(args.out, rows, FIELDS)
    rows.sort(key=lambda r: (r["session_date"] or "9999", r["identifier"], r.get("file_name") or ""))
    write_csv(args.out, rows, FIELDS)
    audio = [r for r in rows if r["kind"] == "audio"]
    video = [r for r in rows if r["kind"] == "video"]
    hours = sum(int(r["duration_s"] or 0) for r in audio) / 3600
    print(f"{len({r['identifier'] for r in rows})} items listed: {len(audio)} audio files in {len({r['identifier'] for r in audio})} items "
          f"({hours:.0f} h where the length is given, {sum(int(r['bytes'] or 0) for r in audio) / 1e9:.1f} GB), "
          f"{len(video)} video files in {len({r['identifier'] for r in video})} items "
          f"({sum(int(r['bytes'] or 0) for r in video) / 1e9:.0f} GB) -> {args.out}")
    if breaker.tripped.is_set():
        print("STOPPED: three refusals in a row. Wait, then rerun: items already listed are skipped.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
