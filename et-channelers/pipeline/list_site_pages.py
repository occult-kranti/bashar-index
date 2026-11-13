#!/usr/bin/env python3
"""List what a maker's own site offers, and register the pages that hold their texts.

recon_sites.py counts the addresses in a site's sitemap. This script names them by family (the first
part of the path: /post/, /blog/, /2024/ ...) so a person can see which family is the maker's
messages, posts or transcripts, and with --merge adds the chosen ones to sources/publisher_pages.csv,
where fetch_publisher_text.py picks them up.

Without --merge nothing in the repository changes: the run prints each family, how many addresses it
holds and how many the pattern would take.

    python3 pipeline/list_site_pages.py --only michelle-robinson
    python3 pipeline/list_site_pages.py --only michelle-robinson --match '/post/' --merge

Only sites listed in sources/official_sites.csv are read, so every page registered here is on a site
the person declared as theirs. robots.txt is obeyed for the sitemap files, and again for every page
when it is fetched later; a site gets one request a second at most. Addresses and counts only: no
page text is read or saved here.

Reads   sources/official_sites.csv
Writes  <root>/sources/site_pages.jsonl          one line per site: families and counts
        sources/publisher_pages.csv (--merge)    new rows only; existing rows are never changed
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, HostGates, add_root_arg, append_jsonl, ensure_outside_git, host_of, layout,  # noqa: E402
                    read_csv, utc_now, write_csv)
from feeds import FetchError, get_bytes  # noqa: E402
from fetch_publisher_text import Robots  # noqa: E402
from recon_sites import POST_LIKE, sitemap_locs  # noqa: E402

OFFICIAL_SITES = ET_ROOT / "sources" / "official_sites.csv"
PAGES = ET_ROOT / "sources" / "publisher_pages.csv"
PAGE_FIELDS = ["person_id", "title", "page_url", "media_pattern", "evidence"]
NOT_A_PAGE = re.compile(r"\.(?:jpe?g|png|gif|webp|svg|pdf|mp3|mp4|m4a|zip|css|js|xml|ico)$", re.I)


def family(url: str) -> str:
    """The kind of address: '/post/…' for a page under /post/, '/<year>/…' for dated posts, '/<page>' for
    a page directly under the site root, '/' for the home page."""
    parts = [p for p in urllib.parse.urlsplit(url).path.split("/") if p]
    if not parts:
        return "/"
    if len(parts) == 1:
        return "/<page>"
    return ("/<year>/…" if re.fullmatch(r"(?:19|20)\d\d", parts[0]) else f"/{parts[0].lower()}/…")


def slug_title(url: str) -> str:
    """A readable stand-in for the title, from the last part of the address. The real title is recorded
    when the page is fetched."""
    parts = [p for p in urllib.parse.urlsplit(url).path.split("/") if p]
    last = urllib.parse.unquote(parts[-1]) if parts else ""
    last = re.sub(r"\.(?:html?|php|aspx?)$", "", last, flags=re.I)
    return " ".join(re.sub(r"[-_+]+", " ", last).split())[:200].lower()


def read_sitemaps(domain, fetch, max_files):
    """(page addresses on this site, sitemap files read, sitemap files left unread)."""
    root = f"https://{domain}"
    queue = [root + "/sitemap.xml"]
    try:
        _, _, body = fetch(root + "/robots.txt", check_robots=False)
        named = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", body.decode("utf-8", "replace"))
        queue = list(dict.fromkeys(named + queue))
    except FetchError:
        pass
    pages, read, seen = [], 0, set()
    bare = domain.removeprefix("www.")
    while queue and read < max_files:
        url = queue.pop(0)
        if url in seen or host_of(url).removeprefix("www.") != bare:
            continue                                   # a sitemap may point elsewhere: only this site is read
        seen.add(url)
        try:
            _, _, body = fetch(url)
        except FetchError:
            continue
        read += 1
        found, children = sitemap_locs(body)
        pages += [p for p in found if host_of(p).removeprefix("www.") == bare and not NOT_A_PAGE.search(urllib.parse.urlsplit(p).path)]
        queue += [c for c in children if c not in seen and c not in queue]
    return list(dict.fromkeys(pages)), read, len(queue)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--official-sites", type=Path, default=OFFICIAL_SITES)
    ap.add_argument("--pages", type=Path, default=PAGES, help="the list to add to (default sources/publisher_pages.csv)")
    ap.add_argument("--only", required=True, help="comma-separated person ids")
    ap.add_argument("--domain", default="", help="read just this one of the person's official sites")
    ap.add_argument("--match", default=POST_LIKE.pattern, help="pattern an address must contain to be registered")
    ap.add_argument("--exclude", default="", help="pattern that leaves an address out")
    ap.add_argument("--evidence", default="", help="what to record as the reason these pages are the person's texts")
    ap.add_argument("--max-sitemaps", type=int, default=40, help="sitemap files read per site")
    ap.add_argument("--min-interval", type=float, default=1.0, help="seconds between requests to one site")
    ap.add_argument("--timeout", type=int, default=40)
    ap.add_argument("--merge", action="store_true", help="add the matching pages to the list")
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    wanted = {x.strip() for x in args.only.split(",") if x.strip()}
    sites = [r for r in read_csv(args.official_sites) if r["person_id"] in wanted
             and (not args.domain or r["domain"].removeprefix("www.") == args.domain.removeprefix("www."))]
    if not sites:
        sys.exit("no official site is listed for " + ", ".join(sorted(wanted))
                 + ": add it to sources/official_sites.csv first (discover_sites.py reads it from the channel page)")
    try:
        take = re.compile(args.match, re.I)
        leave = re.compile(args.exclude, re.I) if args.exclude else None
    except re.error as err:
        sys.exit(f"not a usable pattern: {err}")
    robots, gates = Robots(), HostGates(interval=args.min_interval, stop_after=3)

    def fetch(url, check_robots=True):
        host = host_of(url)
        if gates.blocked(host):
            raise FetchError(0, "host left alone after repeated refusals")
        if check_robots:
            verdict = robots.allowed(url)
            if not verdict:
                raise FetchError(0, "robots.txt could not be read" if verdict is None else "robots.txt does not allow this address")
        gates.wait(host)
        try:
            out = get_bytes(url, timeout=args.timeout, max_bytes=30_000_000)
        except FetchError as err:
            if err.status in (403, 429):
                gates.hard_block(host)
            raise
        gates.success(host)
        return out

    existing = read_csv(args.pages) if args.pages.exists() else []
    have = {r["page_url"].strip() for r in existing}
    added = 0
    for site in sorted(sites, key=lambda r: (r["person_id"], r["domain"])):
        person, domain = site["person_id"], site["domain"]
        pages, read, unread = read_sitemaps(domain, fetch, args.max_sitemaps)
        chosen = [p for p in pages if take.search(urllib.parse.urlsplit(p).path + "/")
                  and not (leave and leave.search(p)) and robots.allowed(p)]
        families = collections.Counter(family(p) for p in pages)
        taken = collections.Counter(family(p) for p in chosen)
        append_jsonl(paths.sources / "site_pages.jsonl",
                     {"person_id": person, "domain": domain, "at": utc_now(), "sitemap_files_read": read,
                      "sitemap_files_unread": unread, "pages": len(pages), "matching": len(chosen),
                      "families": dict(families.most_common(40)), "pattern": args.match, "exclude": args.exclude})
        print(f"{person} | {domain}: {len(pages)} addresses in {read} sitemap file(s)"
              + (f", {unread} file(s) left unread (raise --max-sitemaps)" if unread else "")
              + (" | no sitemap could be read" if not read else ""))
        for name, count in families.most_common(25):
            print(f"    {count:6d}  {name:28s} {'take ' + str(taken[name]) if taken.get(name) else ''}")
        new = [p for p in chosen if p not in have]
        print(f"    -> {len(chosen)} match the pattern, {len(new)} not listed yet")
        if args.merge:
            why = args.evidence or (f"listed in {domain}'s own sitemap; the site is in official_sites.csv "
                                    f"({site.get('evidence', '')[:80].strip() or 'declared by the person'}); robots.txt allows it")
            for page in new:
                existing.append({"person_id": person, "title": slug_title(page), "page_url": page, "media_pattern": "",
                                 "evidence": why})
                have.add(page)
                added += 1
    if args.merge:
        write_csv(args.pages, existing, PAGE_FIELDS)
        print(f"pages: {added} added, {len(existing)} total -> {args.pages}")
    elif any(True for _ in sites):
        print("nothing registered: pass --merge to add the matching pages, --match / --exclude to choose them")
    if gates.blocked_hosts():
        print("left alone after repeated refusals: " + ", ".join(gates.blocked_hosts()), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
