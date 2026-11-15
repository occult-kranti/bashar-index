#!/usr/bin/env python3
"""Fetch transcripts that the publisher wrote, so those recordings need no speech-to-text.

Two kinds of source, both public pages or files the publisher links for readers:
  pages     sources/publisher_pages.csv in the repository: one row per page that holds a session's
            published text (for example the 106 Ra Contact sessions on llresearch.org).
  episodes  transcript links carried by a podcast feed (<podcast:transcript>), for every listed episode:
            the makers' own feeds, and the episodes of interview shows that name a tracked person.

For each one it saves, in the private folder only,
    <root>/transcripts_publisher/<person>/<item id>.txt        plain text
    <root>/transcripts_publisher/<person>/<item id>.source.gz  the bytes as fetched, gzip-compressed
and appends a line to <root>/transcripts_publisher/publisher_text_manifest.jsonl (kind, host, sizes,
word count, hashes, and any media file the page links). The text is the publisher's edition: it is
never mixed with machine transcripts, and it never goes into Git.

Rules: robots.txt of every host is read first and obeyed; one request per host per second by
default; a Retry-After is obeyed; a host that answers 403 or 429 three times in a row is left alone for
the rest of the run, and any 403 or 429 ends the run with exit code 3. A host that refused is not asked
again on later runs until its wait is over (common.resting_hosts: a day at least, longer if it says so
or refuses again). A redirect, robots.txt's included, follows the same rules (feeds.Hops): the host it leads
to waits for its own turn, an answer is charged to the host that gave it, and no redirect is followed to a
host that is being left alone. Without --limit or --all the script only prints what it would do.

    python3 pipeline/fetch_publisher_text.py --limit 3
    python3 pipeline/fetch_publisher_text.py --all
"""
from __future__ import annotations

import argparse
import collections
import gzip
import os
import concurrent.futures as cf
import hashlib
import html
import json
import re
import sys
import threading
import time
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, ITEM_RE, HostGates, Progress, add_root_arg, append_jsonl, archived_ids, atomic_write_text,  # noqa: E402
                    ensure_outside_git, host_of, http_error_class, item_id, latest_by_key, layout, normalise_text,
                    read_csv, read_jsonl, resting_hosts_along, say_refused, say_resting, sha256_text, utc_now)
from feeds import USER_AGENT, YOUTUBE_ID_IN_TEXT, FetchError, Hops, get_bytes, parse_date, safe_url  # noqa: E402

PAGES = ET_ROOT / "sources" / "publisher_pages.csv"
MEDIA_LINK = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+\.(?:mp3|m4a|ogg|opus|wav|flac)(?:\?[^"']*)?)["']""", re.I)
SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "form", "button", "noscript", "svg", "template"}
BLOCK_TAGS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "blockquote", "section", "article",
              "dt", "dd", "pre", "hr"}
MAX_TEXT_BYTES = 12 * 1024 * 1024
# readers' comment threads: Blogger's <div class='comments' id='comments'>, WordPress's comments-area,
# comment-list and reply form. They are readers' words, not the publisher's, so the text leaves them out
# (the page as fetched, comments included, is still kept in .source.gz)
COMMENT_IDS = {"comments", "disqus_thread", "respond"}
COMMENT_CLASSES = {"comments", "comments-area", "comment-list", "commentlist", "comment-respond", "comment-thread"}


def is_comment_block(attrs) -> bool:
    values = dict(attrs)
    if (values.get("id") or "").strip().lower() in COMMENT_IDS:
        return True
    return bool(COMMENT_CLASSES & set((values.get("class") or "").lower().split()))


class MainText(HTMLParser):
    """Text of the <main> element (or <article>, or <body>), without navigation, forms, scripts or readers'
    comment threads."""

    def __init__(self, container):
        super().__init__(convert_charrefs=True)
        self.container, self.depth, self.skip, self.parts = container, 0, 0, []
        self.thread_tag, self.thread_depth = None, 0      # the comment thread being skipped, and its nesting

    def handle_starttag(self, tag, attrs):
        if tag == self.container:
            self.depth += 1
        if self.thread_tag:
            if tag == self.thread_tag:
                self.thread_depth += 1
            return
        if self.depth and is_comment_block(attrs):
            self.thread_tag, self.thread_depth = tag, 1
            return
        if self.depth and tag in SKIP_TAGS:
            self.skip += 1
        if self.depth and not self.skip and tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.thread_tag:
            if tag == self.thread_tag:
                self.thread_depth -= 1
                if not self.thread_depth:
                    self.thread_tag = None
            return
        if self.depth and tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        if self.depth and not self.skip and tag in BLOCK_TAGS:
            self.parts.append("\n")
        if tag == self.container and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth and not self.skip and not self.thread_tag:
            self.parts.append(data)


def html_to_text(markup: str) -> str:
    for container in ("main", "article", "body"):
        if re.search(rf"<{container}\b", markup, re.I):
            parser = MainText(container)
            parser.feed(markup)
            text = "".join(parser.parts)
            lines = [" ".join(line.split()) for line in text.splitlines()]
            cleaned = "\n".join(line for line in lines if line)
            if cleaned:
                return cleaned
    return ""


def cues_to_text(body: str) -> str:
    """WebVTT or SubRip -> text. Drops the header, cue numbers, timings, tags and repeated lines."""
    out, last = [], None
    for line in body.replace("\r", "").split("\n"):
        line = line.strip()
        if not line or line.upper().startswith(("WEBVTT", "NOTE", "STYLE", "REGION", "KIND:", "LANGUAGE:")):
            continue
        if "-->" in line or line.isdigit():
            continue
        line = html.unescape(re.sub(r"<[^>]+>", "", line)).strip()
        if line and line != last:
            out.append(line)
            last = line
    return "\n".join(out)


def json_to_text(body: str) -> str:
    """Podcast-namespace transcript JSON ({"segments":[{"speaker","body"}]}) -> text."""
    data = json.loads(body)
    segments = data.get("segments") if isinstance(data, dict) else data
    lines, speaker = [], None
    for seg in segments or []:
        if not isinstance(seg, dict):
            continue
        text = str(seg.get("body") or seg.get("text") or "").strip()
        if not text:
            continue
        who = seg.get("speaker")
        if who and who != speaker:
            lines.append(f"\n{who}: {text}")
            speaker = who
        else:
            lines.append(text)
    return re.sub(r"[ \t]+", " ", " ".join(lines)).strip()


def to_text(body: bytes, content_type: str, declared: str, url: str):
    """(kind, text). kind is one of page, vtt, srt, json, plain."""
    text = body.decode("utf-8", "replace").lstrip("\ufeff")
    hint = f"{declared} {content_type} {url.lower().split('?')[0][-6:]}".lower()
    head = text[:300].lstrip().lower()
    if head.startswith("webvtt") or "vtt" in hint:
        return "vtt", cues_to_text(text)
    if "subrip" in hint or "srt" in hint or re.match(r"1\s*\n\d\d:\d\d:\d\d", text.lstrip()):
        return "srt", cues_to_text(text)
    if "json" in hint or head.startswith(("{", "[")):
        try:
            return "json", json_to_text(text)
        except (ValueError, AttributeError):
            pass
    if "html" in hint or "<html" in head or "<!doctype html" in head or re.search(r"<(main|article|body|p)\b", text[:5000], re.I):
        return "page", html_to_text(text)
    return "plain", "\n".join(" ".join(line.split()) for line in text.splitlines() if line.strip())


class Robots:
    """robots.txt per site, read once per run. Three answers:
        True   the address may be fetched (the rules allow it, or the site has no robots.txt)
        False  the rules disallow it
        None   robots.txt could not be read this run (timeout, 5xx, or the site answered 401/403/429).
               Nothing is fetched from that site this run, and the items are tried again next run:
               an unread robots.txt is not a refusal, and it is not permission either.
    A 429 for robots.txt itself is different: the site asked to be left alone, so refusal() reports it, and
    the first of its items is recorded as rate limited, so that later runs leave the host alone until its wait is over.
    The 429 is charged to the host that sent it, which is another one when robots.txt redirects. A robots.txt
    that redirects to a host being left alone is not read (held(): the get callable raised klass "held"), and
    nothing is asked of that site this run, nor recorded.
    """

    def __init__(self, timeout=30, get=None):
        self.timeout, self.cache, self.refused, self.lock = timeout, {}, {}, threading.Lock()
        self.get = get          # how robots.txt is fetched: get_bytes, unless the caller sends it through its own gates

    def _rules(self, root):
        with self.lock:
            if root not in self.cache:
                try:
                    _, _, body = (self.get or get_bytes)(root + "/robots.txt", timeout=self.timeout, max_bytes=2 * 1024 * 1024)
                    parser = urllib.robotparser.RobotFileParser()
                    parser.parse(body.decode("utf-8", "replace").splitlines())
                    self.cache[root] = parser
                except FetchError as err:
                    missing = 400 <= err.status < 500 and err.status not in (401, 403, 429)
                    # "no file": the site answered 401 or 403 for robots.txt itself. Not permission to read
                    # its pages, but different from a site that could not be reached at all.
                    self.cache[root] = True if missing else "no file" if err.status in (401, 403) else None
                    if err.klass == "held":
                        self.cache[root] = "held"
                    if err.status == 429:
                        self.refused[root] = {"retry_after": err.retry_after,
                                              "host": host_of(err.final_url or "") or host_of(root)}
            return self.cache[root]

    def held(self, url):
        """True when this site's robots.txt redirects to a host that is being left alone: not read this run."""
        base = re.match(r"^(https?://[^/]+)", url, re.I)
        return bool(base) and self._rules(base.group(1).lower()) == "held"

    def refusal(self, url):
        """{"retry_after": seconds or None, "host": the host that answered} when the site answered 429 for its
        robots.txt on this run, else None."""
        base = re.match(r"^(https?://[^/]+)", url, re.I)
        if not base:
            return None
        root = base.group(1).lower()
        self._rules(root)
        return self.refused.get(root)

    def allowed(self, url):
        base = re.match(r"^(https?://[^/]+)", url, re.I)
        if not base:
            return False
        rules = self._rules(base.group(1).lower())
        if rules is None or rules in ("no file", "held"):
            return None
        if isinstance(rules, bool):
            return rules
        return rules.can_fetch(USER_AGENT, url)

    def answered_without_a_file(self, url):
        """True when the site answered 401 or 403 for robots.txt: it is up, and keeps no readable rules."""
        base = re.match(r"^(https?://[^/]+)", url, re.I)
        return bool(base) and self._rules(base.group(1).lower()) == "no file"

    def crawl_delay(self, url):
        base = re.match(r"^(https?://[^/]+)", url, re.I)
        rules = self._rules(base.group(1).lower()) if base else None
        if rules is None or isinstance(rules, (bool, str)):
            return None
        try:
            delay = rules.crawl_delay(USER_AGENT)
            return float(delay) if delay else None
        except (TypeError, ValueError):
            return None


def saved_source(folder: Path, ident: str):
    """The bytes of a saved page source, compressed (.source.gz) or as earlier versions kept it, or None."""
    packed, plain = folder / f"{ident}.source.gz", folder / f"{ident}.source"
    if packed.exists():
        return gzip.decompress(packed.read_bytes())
    return plain.read_bytes() if plain.exists() else None


def atomic_write_bytes(path: Path, data: bytes):
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def load_jobs(paths, kinds, only):
    jobs, seen = [], set()
    if "pages" in kinds and PAGES.exists():
        for row in read_csv(PAGES):
            person, url = row.get("person_id") or "", (row.get("page_url") or "").strip()
            if not person or not host_of(url) or (only and person not in only):
                continue
            ident = item_id("web", url)  # keyed by the page; audio files pair with it through official_page
            if ident not in seen:
                seen.add(ident)
                jobs.append({"video_id": ident, "channel_dir": person, "url": url, "declared": "text/html",
                             "title": row.get("title") or "", "origin": "page",
                             "media_pattern": row.get("media_pattern") or ""})
    if "episodes" in kinds:
        # Every listed episode that carries a transcript link: the maker's own feeds, and the episodes of
        # interview shows that name a tracked person. The queue file is one work order among several, so it
        # is only read for anything the lists no longer hold.
        from select_episodes import collect          # imported here: listing pages needs none of it
        listed, _, _ = collect(paths)
        queue = paths.jobs / "queue_enclosures.csv"
        for row in listed + (read_csv(queue) if queue.exists() else []):
            url = (row.get("transcript_url") or "").strip()
            if not url or not ITEM_RE.match(row.get("video_id") or "") or row["video_id"] in seen:
                continue
            if only and row["channel_dir"] not in only:
                continue
            seen.add(row["video_id"])
            jobs.append({"video_id": row["video_id"], "channel_dir": row["channel_dir"], "url": url,
                         "declared": row.get("transcript_type") or "", "title": row.get("title") or "",
                         "origin": "episode", "media_pattern": ""})
    return jobs


def robots_reader(gates, stopped):
    """How Robots reads a site's robots.txt in a run: a redirect leads only to a host that is not being left alone
    (`stopped`), in that host's own turn and after its own Retry-After (Hops)."""
    def get(url, **kwargs):
        return get_bytes(url, before_redirect=Hops(host_of(url), gates, stopped), **kwargs)
    return get


def fetch_one(job, out_dir, gates, robots, args, resting=()):
    """Fetch one text. Returns the manifest record, or None if it was not asked for: its host was already
    stopped, or the host a redirect leads to (robots.txt's included) is being left alone, on this run or in
    `resting` from earlier runs."""
    host = host_of(job["url"])
    rec = {"video_id": job["video_id"], "channel_dir": job["channel_dir"], "origin": job["origin"],
           "source_host": host, "source_url": job["url"], "started": utc_now(),
           "final_host": host}            # the host that answered: the first one, unless a redirect led elsewhere
    if gates.blocked(host):
        return None
    try:
        address = safe_url(job["url"])
    except (FetchError, ValueError) as err:          # a port out of range, embedded credentials, and so on
        rec.update(status="error", error_class="bad_address", error_tail=str(err)[-300:])
        return rec
    verdict = robots.allowed(address)
    if robots.held(address):
        return None      # its robots.txt redirects to a host that is being left alone: nothing asked, nothing recorded
    # A transcript that a podcast feed links (<podcast:transcript>) is offered to podcast apps the way the
    # episode's audio is: the feed is the publisher's word. The file stores that keep such transcripts have
    # no robots.txt and answer 403 for it, which must not hide a file the publisher hands out. A site that
    # could not be reached is still left alone for this run, and a robots.txt that says no is obeyed.
    handed_out = job["origin"] == "episode" and robots.answered_without_a_file(address)
    refusal = robots.refusal(address)
    if refusal is not None:
        # the site answered 429 for robots.txt: a refusal like any other, remembered so later runs let it rest.
        # It is one answer: counted and recorded once, for the first of the site's items, and the host is left
        # alone for the rest of the run (its other items are tried again once its wait is over)
        with robots.lock:
            first, refusal["counted"] = not refusal.get("counted"), True
        if not first:
            return None
        refuser = refusal.get("host") or host
        gates.hard_block(refuser, float("inf"))
        rec.update(status="error", http_status=429, error_class="rate_limited", final_host=refuser,
                   error_tail="robots.txt answered 429: nothing was fetched from this site on this run")
        if refusal["retry_after"] is not None:
            rec["retry_after_s"] = refusal["retry_after"]
        return rec
    if verdict is None and not handed_out:
        rec.update(status="error", error_class="network",
                   error_tail="robots.txt could not be read, so nothing was fetched from this site on this run")
        return rec
    if verdict is False:
        rec.update(status="error", error_class="robots", error_tail="robots.txt does not allow this address")
        return rec
    delay = robots.crawl_delay(address)
    if delay:
        gates.set_interval(host, min(delay, 60.0))
    gates.wait(host)
    if gates.blocked(host):
        return None                               # it refused while this request waited for its turn
    # a transcript's address may redirect to a file store: that host waits for its own turn and its own
    # Retry-After, is charged with its own answers, and is not asked at all while it is being left alone
    hops = Hops(host, gates, lambda h: gates.blocked(h) or h in resting)
    try:
        final_url, ctype, body = get_bytes(job["url"], timeout=args.timeout, max_bytes=MAX_TEXT_BYTES, before_redirect=hops)
    except FetchError as err:
        if err.klass == "held":
            return None   # the host it leads to is being left alone: nothing was asked of it, nothing recorded
        refuser = hops.answered(err) or host
        klass = err.klass or (http_error_class(err.status) if err.status else "network")
        if klass in ("rate_limited", "forbidden"):
            gates.hard_block(refuser, err.retry_after)
        elif err.retry_after:
            gates.unavailable(refuser, err.retry_after)          # a 503 that says how long to wait: obeyed
        rec.update(status="error", http_status=err.status, error_class=klass, error_tail=str(err)[-300:],
                   **hops.record(refuser))
        if err.retry_after is not None:
            rec["retry_after_s"] = err.retry_after
        return rec
    answered = host_of(final_url) or host
    hops.credit(answered)                                     # every host along the way answered as asked
    rec.update(hops.record(answered))
    try:
        kind, text = to_text(body, ctype, job["declared"], job["url"])
    except Exception as err:  # noqa: BLE001 - one odd file must not stop the batch
        rec.update(status="error", http_status=200, error_class="parse", error_tail=f"{type(err).__name__}: {err}"[-300:])
        return rec
    words = len(text.split())
    if words < args.min_words:
        rec.update(status="error", http_status=200, error_class="too_short", kind=kind, n_words=words,
                   error_tail=f"only {words} words extracted")
        return rec
    target = out_dir / job["channel_dir"]
    target.mkdir(parents=True, exist_ok=True)
    atomic_write_bytes(target / f"{job['video_id']}.source.gz", gzip.compress(body, compresslevel=6, mtime=0))
    atomic_write_text(target / f"{job['video_id']}.txt", text + "\n")
    media, page_title, published, youtube_ids = [], "", "", []
    if kind == "page":
        markup = body.decode("utf-8", "replace")
        found = re.search(r"<title[^>]*>(.*?)</title>", markup, re.I | re.S)
        page_title = " ".join(html.unescape(found.group(1)).split())[:300] if found else ""
        found = re.search(r"""<meta[^>]+property=["']article:published_time["'][^>]+content=["']([^"']+)["']""", markup, re.I)
        published = parse_date(found.group(1)) if found else ""
        youtube_ids = sorted(set(YOUTUBE_ID_IN_TEXT.findall(markup)))[:20]
        pattern = re.compile(job["media_pattern"], re.I) if job["media_pattern"] else None
        for link in dict.fromkeys(MEDIA_LINK.findall(markup)):
            link = html.unescape(link)
            if link.startswith("//"):
                link = "https:" + link
            if link.startswith("http") and (pattern is None or pattern.search(link)):
                media.append(link)
    rec.update(status="ok", http_status=200, kind=kind, content_type=ctype.split(";")[0].strip().lower(),
               bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), n_words=words,
               text_sha256=sha256_text(normalise_text(text)), media_links=media[:20], title=page_title or job["title"],
               published=published, youtube_ids=youtube_ids, error_class="", error_tail="")
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--kinds", default="pages,episodes", help="which sources to fetch: pages, episodes")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--min-interval", type=float, default=1.0, help="seconds between requests to one host")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--min-words", type=int, default=50, help="shorter extractions are recorded as an error")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--ask-resting", action="store_true",
                    help="ask hosts that refused on an earlier run again, before their wait is over")
    ap.add_argument("--rescan", action="store_true",
                    help="no network: read the saved page sources again and refresh the video ids found on them")
    ap.add_argument("--compact-sources", action="store_true",
                    help="no network: gzip saved page sources kept uncompressed by earlier versions (.source -> .source.gz)")
    args = ap.parse_args()

    paths = layout(ensure_outside_git(args.root))
    out_dir = paths.pubtext
    manifest = out_dir / "publisher_text_manifest.jsonl"
    if args.compact_sources:
        done = saved = 0
        for old_file in sorted(out_dir.rglob("*.source")):
            body = old_file.read_bytes()
            packed = old_file.with_name(old_file.name + ".gz")
            atomic_write_bytes(packed, gzip.compress(body, compresslevel=6, mtime=0))
            if gzip.decompress(packed.read_bytes()) != body:          # checked before the original goes
                packed.unlink()
                continue
            old_file.unlink()
            done += 1
            saved += len(body) - packed.stat().st_size
        print(f"compacted {done} saved page source(s), {saved / 1e6:.0f} MB freed")
        return
    if args.rescan:
        changed = 0
        for rec in latest_by_key(read_jsonl(manifest)).values():
            source = saved_source(out_dir / rec.get("channel_dir", ""), rec["video_id"])
            if rec.get("status") != "ok" or rec.get("kind") != "page" or source is None:
                continue
            ids = sorted(set(YOUTUBE_ID_IN_TEXT.findall(source.decode("utf-8", errors="replace"))))[:20]
            if ids != (rec.get("youtube_ids") or []):
                append_jsonl(manifest, {**rec, "youtube_ids": ids, "rescanned": utc_now()})
                changed += 1
        print(f"rescan: video ids refreshed on {changed} saved page(s)")
        return
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    jobs = load_jobs(paths, {x.strip() for x in args.kinds.split(",") if x.strip()}, only)
    records = read_jsonl(manifest)
    done = latest_by_key(records)
    stored = archived_ids(paths.root, "pubtext")
    todo = []
    for job in jobs:
        prev = done.get(job["video_id"])
        if prev and prev["status"] == "ok" and (job["video_id"] in stored
                                                or (out_dir / job["channel_dir"] / f"{job['video_id']}.txt").exists()):
            continue
        if prev and prev["status"] == "error" and prev.get("error_class") not in ("network", "rate_limited", "forbidden") \
                and not args.retry_failed:
            continue
        todo.append(job)
    # a host that refused on an earlier run is not asked again before its wait is over, as the first host of an
    # address or as the host a redirect leads to; a success counts for every host along the way
    resting = {} if args.ask_resting else resting_hosts_along(records, "source_host")
    say_resting(resting, collections.Counter(host_of(j["url"]) for j in todo if host_of(j["url"]) in resting), "text(s)")
    todo = [j for j in todo if host_of(j["url"]) not in resting]
    hosts = sorted({host_of(j["url"]) for j in todo})
    print(f"publisher texts listed {len(jobs)} | already saved or settled {len(jobs) - len(todo)} | to fetch {len(todo)} "
          f"from {len(hosts)} host(s)", file=sys.stderr)
    if not args.limit and not args.all:
        print("dry run: pass --limit N for a pilot or --all for everything", file=sys.stderr)
        return
    if args.limit:
        todo = todo[:args.limit]
    gates, progress = HostGates(args.min_interval), Progress(len(todo), "publisher-text")
    robots = Robots(get=robots_reader(gates, lambda h: gates.blocked(h) or h in resting))
    ok = 0
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for rec in pool.map(lambda j: fetch_one(j, out_dir, gates, robots, args, resting), todo):
            if rec is None:
                continue
            append_jsonl(manifest, rec)
            ok += rec["status"] == "ok"
            progress.tick(rec["status"] == "ok")
    latest = [r for r in latest_by_key(read_jsonl(manifest)).values() if r["status"] == "ok"]
    print(f"saved {ok} this run | on disk: {len(latest)} publisher texts, {sum(r['n_words'] for r in latest)} words")
    if say_refused(gates):                       # any refusal, not only a tripped breaker: the cycle report says so
        sys.exit(3)


if __name__ == "__main__":
    main()
