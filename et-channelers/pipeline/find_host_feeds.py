#!/usr/bin/env python3
"""Find the podcast of each interview show that carries a recording of the Bashar Index list.

Sixteen of the channels behind the 75 Bashar recordings are interview shows, and most interview shows
also publish their episodes as a podcast. A podcast episode is a file on the show's own host, which a
cloud server can fetch; the same interview on YouTube it cannot. This script looks each show up in
Apple's public podcast search, reads the feeds whose name fits, and grades them:

  verified    the name fits and the feed lives on a website the show's channel declares, or
              the name fits and the feed carries the very interview that is in the list (its title
              matches one of the list's recordings from that channel)
  name-match  the name fits and the feed has an episode whose title names the person
  candidate   the name fits and nothing else was found: left for a person to look at

"The name fits" means the show's name and the podcast's title share their distinctive words (noise such
as "podcast", "show", "clips" aside); a one-word name counts only when the two names are the same.
A registered host feed is never taken whole: select_episodes.py keeps only the episodes whose title
names a tracked person.

Reads   sources/bashar_host_channels.csv (host_channels.py), the list of recordings by channel
Writes  <root>/sources/host_feed_lookups.jsonl     what Apple returned and what each feed showed
        <root>/sources/host_feed_candidates.csv    the graded table
        sources/podcast_feeds.csv (--merge)        rows with relation "host" and person_id "host:<show>"

    python3 pipeline/find_host_feeds.py --limit 3
    python3 pipeline/find_host_feeds.py --all --merge
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, append_jsonl, ensure_outside_git, host_of, layout, read_csv,  # noqa: E402
                    read_jsonl, utc_now, write_csv)
from feeds import FetchError, get_bytes, parse_feed, title_similarity  # noqa: E402
from find_feeds import (REGISTRY, REGISTRY_FIELDS, apple_search, clean_address, clean_author, clean_cell, fold,  # noqa: E402
                        load_targets, on_podcast_host)
from discover_sites import is_platform  # noqa: E402
from host_channels import OUT as HOSTS, groups  # noqa: E402
from select_episodes import assign_person, matchers  # noqa: E402

CANDIDATE_FIELDS = ["host_id", "channel", "grade", "reason", "podcast_title", "author", "episodes", "episodes_naming_a_person",
                    "best_title_match", "feed_url", "site_host", "apple_id"]
NOISE = {"the", "a", "an", "and", "with", "of", "podcast", "show", "official", "channel", "tv", "radio", "clips", "clip",
         "audio", "dr", "s", "by", "from", "hosted"}
TWIN = 0.5      # how alike two titles must be for "the feed carries the listed interview"


def words(name: str):
    """Distinctive lower-case words of a show's name: 'Next Level Soul Clips' -> ['next', 'level', 'soul']."""
    return [w for w in re.findall(r"[^\W_]+", fold((name or "").split("(")[0])) if w not in NOISE]


def name_fits(show: str, podcast: str) -> bool:
    """Do a channel's name and a podcast's title name the same show?"""
    a, b = words(show), words(podcast)
    if not a or not b:
        return False
    if "".join(re.findall(r"[^\W_]+", fold(show.split("(")[0]))) == "".join(re.findall(r"[^\W_]+", fold(podcast))):
        return True                                           # the same name outright, noise words and all
    shared = set(a) & set(b)
    if len(shared) >= 2 and 2 * len(shared) / (len(set(a)) + len(set(b))) >= 0.6:
        return True
    # one name inside the other counts only as a phrase: the words together and in order. A long subtitle
    # that happens to contain "next", "level" and "soul" somewhere is another show.
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    if len(short) >= 2 and any(long[i:i + len(short)] == short for i in range(len(long) - len(short) + 1)):
        return True
    joined_a, joined_b = "".join(a), "".join(b)               # NewRealities / New Realities
    return len(joined_a) >= 8 and (joined_b.startswith(joined_a) or joined_a.startswith(joined_b)) and len(joined_b) >= 8


def grade(show, podcast_title, feed_url, site_link, declared_sites, naming, best_match):
    """(grade, reason). `naming` is how many episodes name a tracked person, `best_match` how alike the
    closest episode title is to one of the list's recordings from this channel (0 to 1)."""
    if not name_fits(show, podcast_title):
        return "unrelated", "another show"
    sites = {d.removeprefix("www.") for d in declared_sites if not is_platform(d)}
    for label, address in (("is served from", feed_url), ("gives as its website", site_link)):
        host = host_of(address or "").removeprefix("www.")
        if host and not on_podcast_host(host) and any(host == d or host.endswith("." + d) for d in sites):
            return "verified", f"the name fits and the feed {label} {host}, which the show's channel declares"
    if best_match >= TWIN:
        return "verified", f"the name fits and the feed carries an interview of the list (title match {best_match:.2f})"
    if naming:
        return "name-match", f"the name fits and {naming} episode(s) name a tracked person"
    return "candidate", "the name fits, but no episode names a tracked person: confirm by hand"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--hosts", type=Path, default=HOSTS)
    ap.add_argument("--registry", type=Path, default=REGISTRY)
    ap.add_argument("--kinds", default="interview show", help="which kinds of channel to look up (comma-separated)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--min-interval", type=float, default=3.2, help="seconds between Apple calls")
    ap.add_argument("--results", type=int, default=8)
    ap.add_argument("--max-feeds", type=int, default=3, help="feeds read per show, best name fit first")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--merge", action="store_true", help="add verified and name-match feeds to the registry")
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    raw_path = paths.sources / "host_feed_lookups.jsonl"
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    shows = [r for r in (read_csv(args.hosts) if args.hosts.exists() else []) if r.get("kind") in kinds]
    if not shows:
        sys.exit(f"no channel of kind {sorted(kinds)} in {args.hosts}: run host_channels.py first")
    listed = groups()
    done = set() if args.refresh else {r["host_id"] for r in read_jsonl(raw_path) if r.get("kind") == "done"}
    todo = [s for s in shows if s["host_id"] not in done]
    print(f"shows {len(shows)} | already looked up {len(shows) - len(todo)} | to do {len(todo)}", file=sys.stderr)
    rules = matchers(load_targets())
    if not args.limit and not args.all:
        print("dry run: pass --limit N or --all", file=sys.stderr)
        todo = []
    elif args.limit:
        todo = todo[:args.limit]
    last = 0.0
    for n, show in enumerate(todo, 1):
        names, seen, failed = [show["channel"].split("(")[0].strip(), show.get("youtube_name") or ""], set(), False
        found = {}
        for name in names:
            key = " ".join(words(name))
            if not key or key in seen:
                continue
            seen.add(key)
            wait = args.min_interval - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.monotonic()
            try:
                results = apple_search(" ".join(w for w in re.findall(r"[^\W_]+", name) if w.lower() != "clips"), args.results)
            except (FetchError, ValueError) as err:
                failed = True
                if getattr(err, "status", 0) in (403, 429):
                    sys.exit(f"STOPPED: Apple answered {err.status}. Wait a few minutes and rerun; finished shows are skipped.")
                continue
            for res in results:
                if res.get("feedUrl") and name_fits(show["channel"], res.get("collectionName", "")):
                    found.setdefault(res["feedUrl"], res)
        for feed_url, res in list(found.items())[:args.max_feeds]:
            note = {"kind": "feed", "host_id": show["host_id"], "channel": show["channel"], "feed_url": feed_url,
                    "podcast_title": res.get("collectionName", ""), "author": res.get("artistName", ""),
                    "apple_id": res.get("collectionId"), "at": utc_now()}
            try:
                time.sleep(1.0)
                _, _, body = get_bytes(feed_url, timeout=60, max_bytes=80_000_000)
                parsed = parse_feed(body, feed_url, show["host_id"])
                titles = [e.get("title") or "" for e in parsed["episodes"]]
                naming = [t for t in titles if assign_person(t, rules)[0]]
                mine = [r.get("title") or "" for r in listed.get(show["channel"], [])]
                best = max((title_similarity(t, m) for t in naming for m in mine), default=0.0)
                note.update(status="ok", link=parsed["feed"]["link"], episodes=len(titles), naming=len(naming),
                            best_match=round(best, 3))
            except FetchError as err:
                note.update(status="error", http_status=err.status, error=str(err)[:200])
            except Exception as err:  # noqa: BLE001 - a broken feed must not stop the sweep
                note.update(status="error", http_status=0, error=f"{type(err).__name__}: {err}"[:200])
            append_jsonl(raw_path, note)
        if not failed:
            append_jsonl(raw_path, {"kind": "done", "host_id": show["host_id"], "feeds": len(found), "at": utc_now()})
        if n % 5 == 0 or n == len(todo):
            print(f"[host feeds] {n}/{len(todo)} shows looked up", file=sys.stderr, flush=True)

    # ---- grade everything seen so far
    by_host = {s["host_id"]: s for s in shows}
    best = {}
    for rec in read_jsonl(raw_path):
        if rec.get("kind") != "feed" or rec.get("status") != "ok" or rec["host_id"] not in by_host:
            continue
        show = by_host[rec["host_id"]]
        verdict, reason = grade(show["channel"], rec["podcast_title"], rec["feed_url"], rec.get("link") or "",
                                (show.get("websites") or "").split(), rec.get("naming", 0), rec.get("best_match", 0.0))
        if verdict == "unrelated" or not clean_address(rec["feed_url"]):
            continue
        best[(rec["host_id"], rec["feed_url"])] = {
            "host_id": rec["host_id"], "channel": show["channel"], "grade": verdict, "reason": reason,
            "podcast_title": clean_cell(rec["podcast_title"]), "author": clean_author(rec["author"]),
            "episodes": rec.get("episodes", ""), "episodes_naming_a_person": rec.get("naming", 0),
            "best_title_match": rec.get("best_match", 0.0), "feed_url": clean_address(rec["feed_url"]),
            "site_host": host_of(rec.get("link") or ""), "site_link": clean_address(rec.get("link") or ""),
            "apple_id": rec.get("apple_id") or ""}
    order = {"verified": 0, "name-match": 1, "candidate": 2}
    rows = sorted(best.values(), key=lambda r: (r["channel"].lower(), order[r["grade"]], -int(r["episodes_naming_a_person"] or 0)))
    write_csv(paths.sources / "host_feed_candidates.csv", rows, CANDIDATE_FIELDS)
    counts = {g: sum(1 for r in rows if r["grade"] == g) for g in order}
    print(f"graded {len(rows)} feeds for {len({r['host_id'] for r in rows})} shows: "
          + ", ".join(f"{counts[g]} {g}" for g in order) + f" -> {paths.sources / 'host_feed_candidates.csv'}")
    if args.merge:
        existing = read_csv(args.registry) if args.registry.exists() else []
        have = {(r["person_id"], r["feed_url"]) for r in existing}
        taken, added = {r["person_id"] for r in existing if r.get("relation") == "host"}, 0
        for row in rows:
            # one feed per show: the best-graded, and never a second one beside a feed already registered
            if row["grade"] not in ("verified", "name-match") or row["host_id"] in taken \
                    or (row["host_id"], row["feed_url"]) in have:
                continue
            existing.append({"person_id": row["host_id"], "relation": "host", "feed_url": row["feed_url"],
                             "podcast_title": row["podcast_title"], "author": row["author"], "site_link": row["site_link"],
                             "apple_id": row["apple_id"], "episodes_seen": row["episodes"], "verification": row["grade"],
                             "evidence": f"interview show in the Bashar Index list ({row['channel']}); Apple podcast search: {row['reason']}",
                             "added": utc_now()[:10]})
            taken.add(row["host_id"])
            added += 1
        existing.sort(key=lambda r: (r["person_id"], r["feed_url"]))
        write_csv(args.registry, existing, REGISTRY_FIELDS)
        print(f"registry: {added} host feed(s) added, {len(existing)} total -> {args.registry}")


if __name__ == "__main__":
    main()
