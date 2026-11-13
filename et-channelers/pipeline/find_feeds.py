#!/usr/bin/env python3
"""Look up podcast feeds for the tracked people through Apple's public podcast search.

Why: YouTube refuses audio requests from cloud servers, but many of the same recordings are also
published by their makers as podcast episodes, and a podcast feed is an offer to download. This
script only finds candidate feeds and grades them. It downloads no audio.

For each tracked person it asks https://itunes.apple.com/search (public, no key, about 20 calls a
minute) for the person's name and channel title, and grades every result:

  name-match   the podcast's author is the person and its title carries the person's or channel's
               name, and no more than two feeds make that claim. Good enough to queue.
  candidate    something matches but not enough to tell the maker's own feed from a re-upload or a
               guest appearance: needs a person (or a later check) to confirm.
  verified     never set here. A reviewer sets it in sources/podcast_feeds.csv after finding the feed
               linked from the maker's own site, or when the feed's website is an official domain
               listed in sources/official_sites.csv (this script applies that second rule itself).

People whose recordings are widely re-uploaded (--strict, by default the ids in STRICT) are never
promoted on a name match alone: they need the official-domain evidence.

Writes  <root>/sources/apple_candidates.jsonl   every result, one line per (person, feed)
        <root>/sources/feed_candidates.csv      the graded table for review
and with --merge, adds the name-match and verified rows to sources/podcast_feeds.csv in the
repository (public metadata: feed address, title, author). Existing rows are never changed.

    python3 pipeline/find_feeds.py --limit 5            # try five people
    python3 pipeline/find_feeds.py --all --merge        # everyone; record the accepted feeds
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, append_jsonl, ensure_outside_git, host_of, layout,  # noqa: E402
                    read_csv, read_jsonl, utc_now, write_csv)
from feeds import FetchError, get_bytes, parse_feed  # noqa: E402

INDEX = ET_ROOT / "youtube-index" / "youtube_index.json"
REGISTRY = ET_ROOT / "sources" / "podcast_feeds.csv"
OFFICIAL_SITES = ET_ROOT / "sources" / "official_sites.csv"
EXTRA_TARGETS = ET_ROOT / "sources" / "extra_targets.csv"
REGISTRY_FIELDS = ["person_id", "relation", "feed_url", "podcast_title", "author", "site_link", "apple_id",
                   "episodes_seen", "verification", "evidence", "added"]
CANDIDATE_FIELDS = ["person_id", "person_name", "query", "grade", "reason", "podcast_title", "author",
                    "episodes", "feed_url", "site_host", "apple_id", "genre"]
# People whose sessions are re-uploaded by many third parties: a matching author name proves nothing.
STRICT = {"darryl-anka", "esther-hicks", "jane-roberts", "lee-carroll", "j-z-knight", "l-l-research",
          "carla-l-rueckert", "barbara-marciniak", "paul-selig"}  # ids as written in the index
_FOLD = str.maketrans({"ł": "l", "Ł": "l", "ø": "o", "Ø": "o", "đ": "d", "Đ": "d", "ß": "ss", "æ": "ae", "Æ": "ae",
                       "œ": "oe", "Œ": "oe", "ı": "i"})
_NOISE = {"the", "and", "with", "of", "podcast", "show", "official", "channel", "tv", "radio", "a", "by", "s"}


def fold(text: str) -> str:
    """Lower-case ASCII form of a name: 'Athina Król' -> 'athina krol'."""
    text = unicodedata.normalize("NFKD", (text or "").translate(_FOLD))
    return "".join(ch for ch in text if not unicodedata.combining(ch)).lower()


def name_tokens(text: str):
    return [w for w in "".join(ch if ch.isalnum() else " " for ch in fold(text)).split() if w not in _NOISE]


def load_targets():
    """[{person_id, person_name, names:[...], role}] from the committed index plus sources/extra_targets.csv."""
    targets = {}
    if INDEX.exists():
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            info = channel.get("channel") or {}
            names = [channel.get("person_name"), info.get("title"), (info.get("handle") or "").lstrip("@")]
            targets[channel["person"]] = {"person_id": channel["person"], "person_name": channel.get("person_name") or "",
                                          "names": [n for n in names if n], "role": channel.get("role") or ""}
    if EXTRA_TARGETS.exists():
        for row in read_csv(EXTRA_TARGETS):
            if not row.get("person_id"):
                continue
            entry = targets.setdefault(row["person_id"], {"person_id": row["person_id"], "names": [],
                                                          "person_name": row.get("name") or "", "role": row.get("role") or ""})
            for name in [row.get("name")] + (row.get("aliases") or "").split("|") + (row.get("weak_aliases") or "").split("|"):
                if name and name.strip() and name.strip() not in entry["names"]:
                    entry["names"].append(name.strip())
    return [targets[k] for k in sorted(targets)]


def official_domains():
    out = {}
    if OFFICIAL_SITES.exists():
        for row in read_csv(OFFICIAL_SITES):
            if row.get("person_id") and row.get("domain"):
                out.setdefault(row["person_id"], set()).add(row["domain"].strip().lower().removeprefix("www."))
    return out


def apple_search(term, limit=10, timeout=30):
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"media": "podcast", "entity": "podcast", "term": term, "limit": limit, "country": "US"})
    _, _, body = get_bytes(url, timeout=timeout, max_bytes=4 * 1024 * 1024)
    return json.loads(body.decode("utf-8", "replace")).get("results", [])


def grade(target, result, strict, domains, site_host="", site_links_show=False):
    """(grade, reason) for one Apple result against one tracked person. Grades: verified, name-match,
    candidate, unrelated. 'name-match' may still be demoted later if too many feeds claim the name.

    Two things verify a feed, and both come from the maker's side, not from the feed:
      * the feed is served from a domain listed in official_sites.csv;
      * a page on that official site links to the show (site_links_show, found by --check-links).
    site_host is the host of the feed's own <link>. A feed can name any site as its website, and fan
    re-upload feeds usually name the maker's, so that claim never promotes a feed by itself."""
    person = set(name_tokens(target["person_name"]))
    author = set(name_tokens(result.get("artistName", "")))
    title = set(name_tokens(result.get("collectionName", "")))
    alias_sets = [set(name_tokens(n)) for n in target["names"]]
    alias_sets = [a for a in alias_sets if a]
    site_host = (site_host or "").removeprefix("www.")
    feed_host = host_of(result.get("feedUrl") or "").removeprefix("www.")
    official = domains.get(target["person_id"], ())
    if feed_host and any(feed_host == d or feed_host.endswith("." + d) for d in official):
        return "verified", f"the feed itself is served from the official domain {feed_host}"
    if site_links_show:
        return "verified", "a page on the official site links to this show"
    author_is_person = bool(person) and person <= author and len(author) <= len(person) + 2
    title_has_name = any(a <= title for a in alias_sets)
    claims_site = bool(site_host) and any(site_host == d or site_host.endswith("." + d) for d in official)
    if author_is_person and title_has_name:
        if target["person_id"] in strict:
            return "candidate", "author and title match, but this person is widely re-uploaded: needs official-site evidence"
        return "name-match", "author is the person and the title carries the name"
    if claims_site:
        return "candidate", "the feed names the official site as its website, but the site was not found linking back: confirm by hand"
    if author_is_person:
        return "candidate", "author is the person; title does not carry the name"
    if title_has_name:
        return "candidate", "title carries the name; author is someone else (re-upload, fan feed or a show about them)"
    return "unrelated", "name appears only in episodes or search ranking"


def clean_cell(text, limit=200) -> str:
    """Text from a stranger's podcast listing, made safe to put in a CSV that people open in a
    spreadsheet: one line, no control characters, capped, and never starting like a formula."""
    text = "".join(ch if ch.isprintable() else " " for ch in str(text or ""))
    text = " ".join(text.split())[:limit]
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def clean_author(text) -> str:
    """As clean_cell, and blank when it is an e-mail address rather than a name."""
    text = clean_cell(text)
    return "" if re.search(r"[^@\s]+@[^@\s]+\.[^@\s]+", text) else text


def clean_address(text) -> str:
    """The address if it is a plain http(s) address with a host, otherwise nothing."""
    text = str(text or "").strip()
    return text if re.match(r"^https?://[^\s/]+\.[^\s]*$", text) and len(text) <= 500 and host_of(text) else ""


def show_needles(feed_url, apple_id):
    """Strings that, found on the maker's own site, show that the site links to this show."""
    needles = []
    if apple_id:
        needles.append(f"id{apple_id}")
    parts = urllib.parse.urlsplit(feed_url)
    bare = (parts.hostname or "").lower().removeprefix("www.") + parts.path.rstrip("/")
    if len(parts.path.strip("/")) >= 4:          # a feed address with a real path, not just a host
        needles.append(bare.lower())
    return needles


def site_links_show(domain, feed_url, apple_id, cache, timeout=40):
    """True if the official site's home page mentions the show's Apple id or its feed address.
    One request per domain per run; a site that cannot be read proves nothing (False)."""
    if domain not in cache:
        try:
            _, _, body = get_bytes(f"https://{domain}/", timeout=timeout, max_bytes=6 * 1024 * 1024)
            cache[domain] = body.decode("utf-8", "replace").lower()
        except FetchError:
            cache[domain] = ""
    page = cache[domain]
    return bool(page) and any(needle in page for needle in show_needles(feed_url, apple_id))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--limit", type=int, default=0, help="look up at most N people")
    ap.add_argument("--all", action="store_true", help="look up everyone")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--min-interval", type=float, default=3.2, help="seconds between Apple calls (about 20 a minute allowed)")
    ap.add_argument("--results", type=int, default=10, help="results to ask for per query")
    ap.add_argument("--max-claimants", type=int, default=2,
                    help="if more feeds than this match one person's name, none is promoted automatically")
    ap.add_argument("--strict", default=",".join(sorted(STRICT)), help="person ids that need official-site evidence")
    ap.add_argument("--check-links", action="store_true",
                    help="read each matching feed once to learn its website, so the official-domain rule can apply")
    ap.add_argument("--merge", action="store_true", help="add accepted feeds to sources/podcast_feeds.csv")
    ap.add_argument("--refresh", action="store_true", help="look people up again even if already done")
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    raw_path = paths.sources / "apple_candidates.jsonl"
    targets = load_targets()
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        targets = [t for t in targets if t["person_id"] in wanted]
    done = set() if args.refresh else {r["person_id"] for r in read_jsonl(raw_path) if r.get("kind") == "done"}
    todo = [t for t in targets if t["person_id"] not in done]
    print(f"people {len(targets)} | already looked up {len(targets) - len(todo)} | to do {len(todo)}", file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N or --all", file=sys.stderr)
    else:
        if args.limit:
            todo = todo[:args.limit]
        strict = {x.strip() for x in args.strict.split(",") if x.strip()}
        last = 0.0
        for n, target in enumerate(todo, 1):
            queries = []
            for name in target["names"]:
                key = " ".join(name_tokens(name))
                if key and key not in [" ".join(name_tokens(q)) for q in queries]:
                    queries.append(name)
            failed = False
            for query in queries[:3]:
                wait = args.min_interval - (time.monotonic() - last)
                if wait > 0:
                    time.sleep(wait)
                last = time.monotonic()
                try:
                    results = apple_search(query, args.results)
                except (FetchError, ValueError) as err:
                    status = getattr(err, "status", 0)
                    append_jsonl(raw_path, {"kind": "error", "person_id": target["person_id"], "query": query,
                                            "status": status, "error": str(err)[:200], "at": utc_now()})
                    failed = True
                    if status in (403, 429):
                        sys.exit(f"STOPPED: Apple answered {status}. Wait a few minutes and rerun; finished people are skipped.")
                    continue
                for res in results:
                    if not res.get("feedUrl"):
                        continue
                    append_jsonl(raw_path, {"kind": "result", "person_id": target["person_id"], "query": query,
                                            "feed_url": res["feedUrl"], "podcast_title": res.get("collectionName", ""),
                                            "author": res.get("artistName", ""), "episodes": res.get("trackCount"),
                                            "apple_id": res.get("collectionId"), "genre": res.get("primaryGenreName", ""),
                                            "at": utc_now()})
            if not failed:
                append_jsonl(raw_path, {"kind": "done", "person_id": target["person_id"], "at": utc_now()})
            if n % 10 == 0 or n == len(todo):
                print(f"[feeds] {n}/{len(todo)} people looked up", file=sys.stderr, flush=True)

    # ---- grade everything seen so far (also on a dry run, so the table can be rebuilt offline)
    strict = {x.strip() for x in args.strict.split(",") if x.strip()}
    domains = official_domains()
    by_id = {t["person_id"]: t for t in load_targets()}
    records = read_jsonl(raw_path)
    links = {r["feed_url"]: r for r in records if r.get("kind") == "feed_link"}
    if args.check_links:
        wanted, last = [], 0.0
        for rec in records:
            if rec.get("kind") == "result" and rec["person_id"] in by_id and rec["feed_url"] not in links \
                    and rec["feed_url"] not in wanted:
                shown = {"artistName": rec["author"], "collectionName": rec["podcast_title"], "feedUrl": rec["feed_url"]}
                if grade(by_id[rec["person_id"]], shown, strict, domains)[0] != "unrelated":
                    wanted.append(rec["feed_url"])
        for n, feed_url in enumerate(wanted, 1):
            wait = 1.0 - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            note = {"kind": "feed_link", "feed_url": feed_url, "at": utc_now()}
            try:
                _, _, body = get_bytes(feed_url, timeout=60)
                feed = parse_feed(body, feed_url)["feed"]
                note.update(status="ok", link=feed["link"], author=feed["author"], owner_name=feed["owner_name"],
                            title=feed["title"], episodes=feed["episodes"])
            except FetchError as err:
                note.update(status="error", http_status=err.status, error=str(err)[:200])
            except Exception as err:  # noqa: BLE001 - a broken feed must not stop the sweep
                note.update(status="error", http_status=0, error=f"{type(err).__name__}: {err}"[:200])
            append_jsonl(raw_path, note)
            links[feed_url] = note
            if n % 20 == 0 or n == len(wanted):
                print(f"[feeds] {n}/{len(wanted)} feed websites read", file=sys.stderr, flush=True)
    best, pages = {}, {}
    site_checks = {(r["person_id"], r["feed_url"]): r for r in records if r.get("kind") == "site_check"}
    for rec in records:
        if rec.get("kind") != "result" or rec["person_id"] not in by_id:
            continue
        target = by_id[rec["person_id"]]
        shown = {"artistName": rec["author"], "collectionName": rec["podcast_title"], "feedUrl": rec["feed_url"]}
        site_host = host_of((links.get(rec["feed_url"]) or {}).get("link") or "")
        key = (rec["person_id"], rec["feed_url"])
        if args.check_links and key not in site_checks and domains.get(rec["person_id"]) \
                and grade(target, shown, strict, domains, site_host)[0] in ("candidate", "name-match"):
            found = [d for d in sorted(domains[rec["person_id"]])
                     if site_links_show(d, rec["feed_url"], rec.get("apple_id"), pages)]
            site_checks[key] = {"kind": "site_check", "person_id": rec["person_id"], "feed_url": rec["feed_url"],
                                "linked_from": found, "at": utc_now()}
            append_jsonl(raw_path, site_checks[key])
        linked = bool((site_checks.get(key) or {}).get("linked_from"))
        verdict, reason = grade(target, shown, strict, domains, site_host, linked)
        if verdict == "unrelated":
            continue
        if linked and verdict == "verified":
            reason = f"{site_checks[key]['linked_from'][0]} links to this show"
        row = {"person_id": rec["person_id"], "person_name": target["person_name"], "query": rec["query"],
               "grade": verdict, "reason": reason, "podcast_title": clean_cell(rec["podcast_title"]),
               "author": clean_author(rec["author"]), "episodes": rec.get("episodes") or "",
               "feed_url": clean_address(rec["feed_url"]), "site_host": site_host,
               "site_link": clean_address((links.get(rec["feed_url"]) or {}).get("link") or ""),
               "apple_id": rec.get("apple_id") or "", "genre": clean_cell(rec.get("genre", ""), 60)}
        if not row["feed_url"]:
            continue                                 # not an http(s) address: nothing to read
        best.setdefault((rec["person_id"], rec["feed_url"]), row)
    rows = list(best.values())
    claimants = {}
    for row in rows:
        if row["grade"] == "name-match":
            claimants.setdefault(row["person_id"], []).append(row)
    for person, group in claimants.items():
        if len(group) > args.max_claimants:
            for row in group:
                row["grade"], row["reason"] = "candidate", f"{len(group)} feeds claim this author: cannot tell the maker's own feed from re-uploads"
    order = {"verified": 0, "name-match": 1, "candidate": 2}
    rows.sort(key=lambda r: (r["person_id"], order[r["grade"]], r["podcast_title"].lower()))
    write_csv(paths.sources / "feed_candidates.csv", rows, CANDIDATE_FIELDS)
    counts = {g: sum(1 for r in rows if r["grade"] == g) for g in order}
    people = {g: len({r["person_id"] for r in rows if r["grade"] == g}) for g in order}
    print(f"graded {len(rows)} feed candidates: " + ", ".join(f"{counts[g]} {g} ({people[g]} people)" for g in order)
          + f" -> {paths.sources / 'feed_candidates.csv'}")

    if args.merge:
        existing = read_csv(REGISTRY) if REGISTRY.exists() else []
        have = {(r["person_id"], r["feed_url"]) for r in existing}
        added = 0
        for row in rows:
            if row["grade"] in ("verified", "name-match") and (row["person_id"], row["feed_url"]) not in have:
                existing.append({"person_id": row["person_id"], "relation": "own", "feed_url": row["feed_url"],
                                 "podcast_title": row["podcast_title"], "author": row["author"],
                                 "site_link": row.get("site_link", ""),
                                 "apple_id": row["apple_id"], "episodes_seen": row["episodes"],
                                 "verification": row["grade"], "evidence": f"Apple podcast search: {row['reason']}",
                                 "added": utc_now()[:10]})
                have.add((row["person_id"], row["feed_url"]))
                added += 1
        existing.sort(key=lambda r: (r["person_id"], r["feed_url"]))
        write_csv(REGISTRY, existing, REGISTRY_FIELDS)
        print(f"registry: {added} feed(s) added, {len(existing)} total -> {REGISTRY}")


if __name__ == "__main__":
    main()
