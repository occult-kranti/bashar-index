#!/usr/bin/env python3
"""Ask each official site what it publishes: a podcast it links to, a feed of posts, a sitemap.

For every domain in sources/official_sites.csv this reads robots.txt, the home page and, if the site
has one, its sitemap, and reports what a later lane could collect from the maker's own site:

  podcast   a feed the site links to that carries audio enclosures, or an Apple podcast it links to
            (resolved to its feed through Apple's public lookup). Because the maker's own site points at
            it, such a feed is verified by construction.
  posts     a feed without enclosures (a blog): its items are candidate publisher texts.
  sitemap   how many addresses the site's sitemap lists, and how many look like posts.

It downloads no audio and saves no page text: only addresses and counts. robots.txt is obeyed, each
site gets one request per second at most, and a site that refuses is left alone.

Writes  <root>/sources/site_recon.jsonl     one line per site, with what was found
        <root>/sources/site_recon.csv       the same as a table for review
and with --merge adds the podcasts it found to sources/podcast_feeds.csv as verified, each with the
page that links it as the evidence. Existing rows are never changed.

    python3 pipeline/recon_sites.py --limit 5
    python3 pipeline/recon_sites.py --all --merge
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import html
import json
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, HostGates, add_root_arg, append_jsonl, ensure_outside_git, host_of, latest_by_key,  # noqa: E402
                    layout, read_csv, read_jsonl, utc_now, write_csv)
from feeds import FetchError, get_bytes, parse_feed  # noqa: E402
from fetch_publisher_text import Robots  # noqa: E402
from find_feeds import REGISTRY, REGISTRY_FIELDS, clean_address, clean_author, clean_cell, grade, load_targets  # noqa: E402

OFFICIAL_SITES = ET_ROOT / "sources" / "official_sites.csv"
FEED_LINK = re.compile(r"""<link\b[^>]*\btype\s*=\s*["']application/(?:rss|atom)\+xml["'][^>]*>""", re.I)
HREF = re.compile(r"""\bhref\s*=\s*["']([^"']+)["']""", re.I)
APPLE_ID = re.compile(r"podcasts\.apple\.com/[^\"'\s<>]*?/id(\d{6,12})", re.I)
FEED_HOSTS = re.compile(r"""https?://(?:anchor\.fm/s/[\w-]+/podcast/rss|feeds?\.[\w.-]+/[^"'\s<>]+|[\w.-]+\.libsyn\.com/rss[^"'\s<>]*|"""
                        r"""feed\.podbean\.com/[^"'\s<>]+|[\w-]+\.podbean\.com/feed[^"'\s<>]*|rss\.buzzsprout\.com/\d+\.rss|"""
                        r"""www\.spreaker\.com/show/\d+/episodes/feed|media\.rss\.com/[\w-]+/feed\.xml|[\w.-]+/feed/podcast/?)""", re.I)
POST_LIKE = re.compile(r"/(?:\d{4}/\d{2}/|blog/|post/|posts/|news/|articles?/|channel(?:ing|ling)s?/|messages?/|transcripts?/)[^/]", re.I)
FIELDS = ["person_id", "domain", "status", "home_final_host", "podcast_feeds", "post_feeds", "post_feed_items",
          "apple_ids", "sitemap_urls", "sitemap_post_like", "sitemap_files_read", "note"]


def links_on(markup: str, base: str):
    """(feed links declared in <head>, podcast feed addresses anywhere, Apple podcast ids) on a page."""
    declared = []
    for tag in FEED_LINK.findall(markup):
        found = HREF.search(tag)
        if found:
            declared.append(urllib.parse.urljoin(base, html.unescape(found.group(1)).strip()))
    hosted = [html.unescape(u) for u in FEED_HOSTS.findall(markup)]
    apple = sorted(set(APPLE_ID.findall(markup)))
    return list(dict.fromkeys(declared)), list(dict.fromkeys(hosted)), apple


def sitemap_locs(body: bytes):
    """(page addresses, child sitemap addresses) in one sitemap file."""
    text = body.decode("utf-8", "replace")
    locs = [html.unescape(x).strip() for x in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)]
    if re.search(r"<sitemapindex\b", text, re.I):
        return [], locs
    return locs, []


def apple_feed(apple_id, timeout=30):
    """{feed_url, title, author, episodes} for an Apple podcast id, or None."""
    try:
        _, _, body = get_bytes(f"https://itunes.apple.com/lookup?id={apple_id}&entity=podcast", timeout=timeout,
                               max_bytes=2 * 1024 * 1024)
        for res in json.loads(body.decode("utf-8", "replace")).get("results", []):
            if res.get("feedUrl"):
                return {"feed_url": res["feedUrl"], "title": res.get("collectionName", ""), "author": res.get("artistName", ""),
                        "episodes": res.get("trackCount"), "apple_id": str(apple_id)}
    except (FetchError, ValueError):
        pass
    return None


def recon_one(row, gates, robots, args):
    person, domain = row["person_id"], row["domain"]
    home = f"https://{domain}/"
    rec = {"person_id": person, "domain": domain, "started": utc_now(), "podcasts": [], "post_feeds": [],
           "apple_ids": [], "sitemap_urls": 0, "sitemap_post_like": 0, "sitemap_files_read": 0, "note": ""}

    def fetch(url, max_bytes=8_000_000):
        host = host_of(url)
        if gates.blocked(host):
            raise FetchError(0, "host left alone after repeated refusals")
        verdict = robots.allowed(url)
        if verdict is None:
            raise FetchError(0, "robots.txt could not be read")
        if not verdict:
            raise FetchError(0, "robots.txt does not allow this address")
        delay = robots.crawl_delay(url)
        if delay:
            gates.set_interval(host, min(delay, 30.0))
        gates.wait(host)
        try:
            out = get_bytes(url, timeout=args.timeout, max_bytes=max_bytes)
        except FetchError as err:
            if err.status in (403, 429):
                gates.hard_block(host)
            raise
        gates.success(host)
        return out

    try:
        final, _, body = fetch(home)
    except FetchError as err:
        rec.update(status="error", note=str(err)[:160])
        return rec
    rec["home_final_host"] = host_of(final)
    declared, hosted, apple = links_on(body.decode("utf-8", "replace"), final)
    rec["apple_ids"] = apple[:5]
    seen = set()
    for url in (declared + hosted)[:args.max_feeds]:
        url = clean_address(url)
        if not url or url in seen or "/comments/feed" in url:
            continue
        seen.add(url)
        try:
            _, _, feed_body = fetch(url, max_bytes=60_000_000)
            parsed = parse_feed(feed_body, url, person)
        except (FetchError, ValueError, Exception) as err:  # noqa: BLE001 - a broken feed is a note, not a stop
            rec["note"] = (rec["note"] + f" feed unreadable: {type(err).__name__};")[:300]
            continue
        feed = parsed["feed"]
        entry = {"feed_url": url, "title": clean_cell(feed["title"]), "author": clean_author(feed["author"]),
                 "items": feed["items"], "episodes": feed["episodes"], "found_on": final}
        (rec["podcasts"] if feed["episodes"] else rec["post_feeds"]).append(entry)
    for apple_id in apple[:3]:
        found = apple_feed(apple_id)
        if found and found["feed_url"] not in {p["feed_url"] for p in rec["podcasts"]}:
            rec["podcasts"].append({"feed_url": clean_address(found["feed_url"]), "title": clean_cell(found["title"]),
                                    "author": clean_author(found["author"]), "items": found["episodes"],
                                    "episodes": found["episodes"], "found_on": final, "apple_id": found["apple_id"]})
    rec["podcasts"] = [p for p in rec["podcasts"] if p["feed_url"]]

    # the sitemap: how much the site lists, and how much of it looks like posts
    root = re.match(r"^(https?://[^/]+)", final).group(1)
    queue, read, pages = [root + "/sitemap.xml"], 0, []
    try:
        _, _, robots_body = get_bytes(root + "/robots.txt", timeout=args.timeout, max_bytes=2 * 1024 * 1024)
        named = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots_body.decode("utf-8", "replace"))
        queue = list(dict.fromkeys(named + queue))
    except FetchError:
        pass
    while queue and read < args.max_sitemaps:
        url = queue.pop(0)
        if host_of(url) != host_of(root):
            continue
        try:
            _, _, sm = fetch(url, max_bytes=30_000_000)
        except FetchError:
            continue
        read += 1
        found_pages, children = sitemap_locs(sm)
        pages += found_pages
        queue += [c for c in children if c not in queue]
    rec.update(status="ok", sitemap_urls=len(set(pages)), sitemap_files_read=read,
               sitemap_post_like=sum(1 for u in set(pages) if POST_LIKE.search(urllib.parse.urlsplit(u).path + "/")),
               sitemaps_left_unread=len(queue))
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--official-sites", type=Path, default=OFFICIAL_SITES)
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--workers", type=int, default=4, help="sites read at once (each site still gets one request a second)")
    ap.add_argument("--max-feeds", type=int, default=4, help="feeds read per site")
    ap.add_argument("--max-sitemaps", type=int, default=8, help="sitemap files read per site")
    ap.add_argument("--timeout", type=int, default=40)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--merge", action="store_true", help="add the podcasts found to sources/podcast_feeds.csv as verified")
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    out = paths.sources / "site_recon.jsonl"
    rows = [r for r in (read_csv(args.official_sites) if args.official_sites.exists() else []) if r.get("domain")]
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        rows = [r for r in rows if r["person_id"] in wanted]
    key = lambda r: f"{r['person_id']}|{r['domain']}"  # noqa: E731
    done = {} if args.refresh else {f"{r['person_id']}|{r['domain']}": r for r in read_jsonl(out) if r.get("status") == "ok"}
    todo = [r for r in rows if key(r) not in done]
    print(f"official sites {len(rows)} | already looked at {len(rows) - len(todo)} | to look at {len(todo)}", file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N or --all", file=sys.stderr)
    else:
        if args.limit:
            todo = todo[:args.limit]
        gates, robots = HostGates(1.0, 3), Robots()
        with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for n, rec in enumerate(pool.map(lambda r: recon_one(r, gates, robots, args), todo), 1):
                append_jsonl(out, rec)
                if n % 10 == 0 or n == len(todo):
                    print(f"[recon] {n}/{len(todo)} sites looked at", file=sys.stderr, flush=True)

    latest = {}
    for rec in read_jsonl(out):
        latest[f"{rec['person_id']}|{rec['domain']}"] = rec
    table = []
    for rec in sorted(latest.values(), key=lambda r: (r["person_id"], r["domain"])):
        table.append({"person_id": rec["person_id"], "domain": rec["domain"], "status": rec.get("status", ""),
                      "home_final_host": rec.get("home_final_host", ""), "podcast_feeds": len(rec.get("podcasts") or []),
                      "post_feeds": len(rec.get("post_feeds") or []),
                      "post_feed_items": sum(p.get("items") or 0 for p in rec.get("post_feeds") or []),
                      "apple_ids": len(rec.get("apple_ids") or []), "sitemap_urls": rec.get("sitemap_urls", 0),
                      "sitemap_post_like": rec.get("sitemap_post_like", 0),
                      "sitemap_files_read": rec.get("sitemap_files_read", 0), "note": rec.get("note", "")})
    write_csv(paths.sources / "site_recon.csv", table, FIELDS)
    ok = [t for t in table if t["status"] == "ok"]
    print(f"looked at {len(table)} sites, {len(ok)} readable | {sum(1 for t in ok if t['podcast_feeds'])} link a podcast | "
          f"{sum(1 for t in ok if t['post_feeds'])} have a feed of posts | "
          f"{sum(1 for t in ok if t['sitemap_post_like'] >= 20)} list 20 or more post-like pages in a sitemap -> "
          f"{paths.sources / 'site_recon.csv'}")

    if args.merge:
        existing = read_csv(args.registry) if args.registry.exists() else []
        have = {(r["person_id"], r["feed_url"]) for r in existing}
        shows = {(r["person_id"], str(r["apple_id"])) for r in existing if r.get("apple_id")}
        added = 0
        names = {t["person_id"]: t for t in load_targets()}
        domains = {}
        for site in rows:
            domains.setdefault(site["person_id"], set()).add(site["domain"].removeprefix("www."))
        others = 0
        for rec in latest.values():
            for pod in rec.get("podcasts") or []:
                if (rec["person_id"], pod["feed_url"]) in have or (pod.get("apple_id") and (rec["person_id"], pod["apple_id"]) in shows):
                    continue
                # A site also links shows its owner was a guest on. The link proves the site knows the show,
                # not whose show it is: that takes the feed living on the official domain, or the maker's
                # name on it. Everything else is listed in the review table and not accepted.
                target = names.get(rec["person_id"], {"person_id": rec["person_id"], "person_name": "", "names": []})
                verdict, _ = grade(target, {"artistName": pod.get("author", ""), "collectionName": pod.get("title", ""),
                                            "feedUrl": pod["feed_url"]}, set(), domains)
                if verdict not in ("verified", "name-match"):
                    others += 1
                    continue
                existing.append({"person_id": rec["person_id"], "relation": "own", "feed_url": pod["feed_url"],
                                 "podcast_title": pod["title"], "author": pod["author"], "site_link": f"https://{rec['domain']}/",
                                 "apple_id": pod.get("apple_id", ""), "episodes_seen": pod.get("episodes") or "",
                                 "verification": "verified",
                                 "evidence": f"linked from the official site {rec['domain']} (found on {pod['found_on'][:120]})",
                                 "added": utc_now()[:10]})
                have.add((rec["person_id"], pod["feed_url"]))
                added += 1
        existing.sort(key=lambda r: (r["person_id"], r["feed_url"]))
        write_csv(args.registry, existing, REGISTRY_FIELDS)
        print(f"registry: {added} podcast feed(s) added, {len(existing)} total -> {args.registry}"
              + (f" | {others} linked show(s) left out: neither on the official domain nor carrying the maker's name "
                 "(a show the person appeared on, most likely)" if others else ""))


if __name__ == "__main__":
    main()
