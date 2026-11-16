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

A page's youtube_ids and media_links are read from its markup without the readers' comment threads and reply forms
(page_links): a video a reader links in a comment is not the post's, and must not pair the post with it.

--rederive (no network) builds each stored page text again from its saved source (.source.gz) with the current
extractor, for example after the extractor learnt to leave readers' comment threads out, and reads the page's
youtube_ids and media_links again the same way. A text is rewritten only when the change takes lines out and nothing
else: the new text's lines are the old ones in the same order with some missing, and the new text is not empty.
Anything else is skipped and reported. A page whose text stays as it is but whose ids or links change counts as
changed too: it gets a manifest line and no text is written. Ids also change where the id reader of the fetch missed an
address that today's reads (a youtube-nocookie.com embed, say); the reason says so. It is a dry run that prints a
summary per person (how many pages change their ids among it, and each such page with its ids before and after)
unless --apply is given; --apply first saves every text it will replace into one tar.gz under <root>/backups/ (and
writes nothing if that fails), then writes each new text and appends a manifest line with the new word count, hashes,
ids and links, saying when and why it was rederived (rederived_at; rederived_reason: readers' comment threads left
out, video ids read again with the current id reader, or both; rederived_backup when a text was replaced) and what
was there before (rederived_words_before, rederived_text_sha256_before, and rederived_youtube_ids_before or
rederived_media_links_before when those changed).

    python3 pipeline/fetch_publisher_text.py --rederive [--only suzanne-lie-ph-d]
    python3 pipeline/fetch_publisher_text.py --rederive --apply

To undo an --apply: extract its backup into the root, which puts the old texts back at their paths,
    tar -xzf <root>/backups/publisher-texts-before-rederive-<UTC time>.tar.gz -C <root>
then, for each item that run changed (its latest manifest line has the run's rederived_at, one time for all the lines
a run appends; the ones that replaced a text also name the backup in rederived_backup), append to the manifest a copy
of that latest line with n_words, text_sha256 and youtube_ids (and media_links) set back from rederived_words_before,
rederived_text_sha256_before and rederived_youtube_ids_before (and rederived_media_links_before); a field without its
*_before did not change. Leave the rederived_* fields out of the copy. Items whose ids alone changed are in no backup:
the manifest line is all they need.

--rederive --apply, --rescan and --compact-sources take one lock (<root>/jobs/fetch_publisher_text.rederive.lock), so
only one of them runs at a time.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import os
import concurrent.futures as cf
import hashlib
import html
import io
import json
import re
import sys
import tarfile
import threading
import time
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, ITEM_RE, HostGates, Progress, add_root_arg, append_jsonl, archived_ids, atomic_write_text,  # noqa: E402
                    ensure_outside_git, file_lock, host_of, http_error_class, item_id, latest_by_key, layout,
                    normalise_text, read_csv, read_jsonl, resting_hosts_along, say_refused, say_resting, sha256_text,
                    utc_now)
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


VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class CommentSpans(HTMLParser):
    """Where a page's readers' comment threads and reply forms are (is_comment_block), anywhere on the page:
    `spans`, [(start, end)] character offsets into the markup, each from the block's start tag to the end of its end
    tag (or to the end of the page when it is never closed), nested the way MainText nests them."""

    def __init__(self, markup: str):
        super().__init__(convert_charrefs=True)
        self.markup, self.spans = markup, []
        self.line_starts = [0] + [m.end() for m in re.finditer("\n", markup)]     # getpos() counts lines by \n
        self.thread_tag, self.thread_depth, self.thread_start = None, 0, 0

    def position(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if self.thread_tag:
            if tag == self.thread_tag:
                self.thread_depth += 1
            return
        if tag not in VOID_TAGS and is_comment_block(attrs):        # a void element holds nothing to leave out
            self.thread_tag, self.thread_depth, self.thread_start = tag, 1, self.position()

    def handle_endtag(self, tag):
        if self.thread_tag and tag == self.thread_tag:
            self.thread_depth -= 1
            if not self.thread_depth:
                start = self.position()                                # where "</tag" begins
                close = self.markup.find(">", start)
                self.spans.append((self.thread_start, len(self.markup) if close < 0 else close + 1))
                self.thread_tag = None

    def close(self):
        super().close()
        if self.thread_tag:
            self.spans.append((self.thread_start, len(self.markup)))
            self.thread_tag = None


def post_markup(markup: str) -> str:
    """The page's markup without its readers' comment threads and reply forms: what the publisher put on the page.
    Everything else is kept byte for byte (scripts, the head, the chrome), so links are found there as before."""
    finder = CommentSpans(markup)
    finder.feed(markup)
    finder.close()
    if not finder.spans:
        return markup
    parts, at = [], 0
    for start, end in finder.spans:
        parts.append(markup[at:start])
        at = end
    parts.append(markup[at:])
    return "\n".join(parts)          # a line break joins no two halves into one address


def page_links(markup: str, media_pattern: str = ""):
    """(youtube_ids, media_links) of a page, from its markup without readers' comment threads (post_markup): a video
    or an audio file a reader linked in a comment is not the post's own. At most 20 of each; media links are absolute
    and, when the page's row gives a media_pattern, only those that match it."""
    post = post_markup(markup)
    youtube_ids = sorted(set(YOUTUBE_ID_IN_TEXT.findall(post)))[:20]
    pattern = re.compile(media_pattern, re.I) if media_pattern else None
    media = []
    for link in dict.fromkeys(MEDIA_LINK.findall(post)):
        link = html.unescape(link)
        if link.startswith("//"):
            link = "https:" + link
        if link.startswith("http") and (pattern is None or pattern.search(link)):
            media.append(link)
    return youtube_ids, media[:20]


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
    media, page_title, published, youtube_ids = [], "", "", []
    if kind == "page":
        markup = body.decode("utf-8", "replace")
        found = re.search(r"<title[^>]*>(.*?)</title>", markup, re.I | re.S)
        page_title = " ".join(html.unescape(found.group(1)).split())[:300] if found else ""
        found = re.search(r"""<meta[^>]+property=["']article:published_time["'][^>]+content=["']([^"']+)["']""", markup, re.I)
        published = parse_date(found.group(1)) if found else ""
        try:
            # the videos and audio files of the post itself: what readers link in their comments is not the post's
            youtube_ids, media = page_links(markup, job["media_pattern"])
        except Exception as err:  # noqa: BLE001 - one odd page must not stop the batch
            rec.update(status="error", http_status=200, error_class="parse", error_tail=f"{type(err).__name__}: {err}"[-300:])
            return rec
    target = out_dir / job["channel_dir"]
    target.mkdir(parents=True, exist_ok=True)
    atomic_write_bytes(target / f"{job['video_id']}.source.gz", gzip.compress(body, compresslevel=6, mtime=0))
    atomic_write_text(target / f"{job['video_id']}.txt", text + "\n")
    rec.update(status="ok", http_status=200, kind=kind, content_type=ctype.split(";")[0].strip().lower(),
               bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), n_words=words,
               text_sha256=sha256_text(normalise_text(text)), media_links=media, title=page_title or job["title"],
               published=published, youtube_ids=youtube_ids, error_class="", error_tail="")
    return rec


# ---------------------------------------------------------------- --rederive: the stored texts again, from the saved pages
REDERIVE_REASON = "readers' comment threads left out"
REREAD_REASON = "video ids read again with the current id reader"     # it knows addresses an older one missed
REWRITE_LOCK = "fetch_publisher_text.rederive.lock"       # under <root>/jobs/: --rederive --apply, --rescan, --compact-sources


def text_lines(text: str):
    """A text's lines with their whitespace collapsed and blank lines left out: what the deletion-only check compares."""
    return [" ".join(line.split()) for line in text.splitlines() if line.strip()]


def only_deletions(old_lines, new_lines) -> bool:
    """True when new_lines is old_lines with some lines taken out: every new line is an old one, in the same order,
    so nothing was added, changed or moved."""
    rest = iter(old_lines)
    return all(line in rest for line in new_lines)          # `in` moves along the iterator: order is kept


def rederive_item(rec, out_dir: Path, media_pattern=None):
    """What the current extractor makes of one stored text, from its saved page: the text, and the YouTube ids and
    media links found outside readers' comment threads (page_links; `media_pattern` is the page's row's, "" for none,
    None when the page is no longer listed: then only links it had already are kept). Reads files only: nothing is
    written and nothing is fetched. A dict with
        verdict       "changed", "unchanged" or "skipped"
        reason        why it was skipped
        words_before  the manifest's word count; words_after, the word count once the change is written
        text_changed, ids_changed, media_changed   whether the text, the youtube_ids, the media_links change
        ids_reread    whether the ids change because today's id reader finds others on the whole page than the stored
                      ones (not because of the comment threads)
    and for a change: base (the manifest line it starts from), path (the .txt), old (its bytes now), text (the new
    text), write_text (False when no text is written: only the ids or links change, or the text on disk is already
    the new one and only the manifest line is missing, from an --apply that stopped between the two), record (the
    manifest line to append)."""
    ident, person = rec["video_id"], rec.get("channel_dir") or ""
    words = int(rec.get("n_words") or 0)
    out = {"video_id": ident, "person": person, "verdict": "skipped", "reason": "", "words_before": words,
           "words_after": words, "text_changed": False, "ids_changed": False, "media_changed": False,
           "ids_reread": False}
    if rec.get("kind") != "page":
        out["reason"] = f"not a page ({rec.get('kind') or 'no kind'})"        # vtt, srt, json and plain texts stay as they are
        return out
    folder = out_dir / person
    packed, path = folder / f"{ident}.source.gz", folder / f"{ident}.txt"
    if not person or not packed.is_file():
        out["reason"] = "no .source.gz"
        return out
    if not path.is_file():
        out["reason"] = "no text on disk"
        return out
    try:
        body = gzip.decompress(packed.read_bytes())
    except Exception:  # noqa: BLE001 - a damaged file is reported, not fatal
        out["reason"] = "the .source.gz cannot be read"
        return out
    if rec.get("sha256") and hashlib.sha256(body).hexdigest() != rec["sha256"]:
        out["reason"] = "the .source.gz is not the page the manifest describes"
        return out
    # the same reading a fetch makes of these bytes (load_jobs declares text/html for a listed page)
    declared = "text/html" if rec.get("origin") == "page" else ""
    try:
        kind, text = to_text(body, rec.get("content_type") or "", declared, rec.get("source_url") or "")
    except Exception as err:  # noqa: BLE001
        out["reason"] = f"the extractor failed ({type(err).__name__})"
        return out
    if kind != "page":
        out["reason"] = f"the saved source does not read as a page ({kind})"
        return out
    try:
        markup = body.decode("utf-8", "replace")
        youtube_ids, media = page_links(markup, media_pattern or "")
    except Exception as err:  # noqa: BLE001
        out["reason"] = f"the link reader failed ({type(err).__name__})"
        return out
    old_ids, old_media = list(rec.get("youtube_ids") or []), list(rec.get("media_links") or [])
    whole_ids = sorted(set(YOUTUBE_ID_IN_TEXT.findall(markup)))[:20]     # the whole page, comments included
    if media_pattern is None:
        media = [link for link in media if link in old_media]     # not listed any more: no link it did not have
    ids_changed, media_changed = youtube_ids != old_ids, media != old_media
    old = path.read_bytes()
    old_text = old.decode("utf-8", "replace")
    old_lines, new_lines = text_lines(old_text), text_lines(text)
    words_after, text_hash = len(text.split()), sha256_text(normalise_text(text))
    write_text = text_changed = True
    if sha256_text(normalise_text(old_text)) != rec.get("text_sha256"):
        # an --apply that wrote this text and stopped before its manifest line: the line is still owed (a removed
        # line holds a word at least, so such a text has fewer words than the manifest says)
        if old_lines == new_lines and words_after < words:
            write_text = False
        else:
            out["reason"] = "the text on disk is not the one the manifest describes"
            return out
    elif old_lines == new_lines:
        if not (ids_changed or media_changed):
            out["verdict"] = "unchanged"
            return out
        # the text stays as it is (its counts too); only the manifest line with the post's own ids or links is owed
        write_text, text_changed, words_after, text_hash = False, False, words, rec.get("text_sha256") or ""
    elif not new_lines:
        out["reason"] = "the new text would be empty"
        return out
    elif not only_deletions(old_lines, new_lines):
        out["reason"] = "the extractor would add, change or move lines"
        return out
    # the fields a fetch computes from these bytes and this text (fetch_one); every other field is kept as it was,
    # the time of the fetch included. The *_before fields hold what a restore puts back (see the module's docstring).
    # why: comment threads left out of the text, the ids or the links; and ids that the id reader of the fetch missed
    # (the whole page read today gives other ids than the stored ones)
    reasons = [REDERIVE_REASON] if text_changed or media_changed or youtube_ids != whole_ids else []
    if ids_changed and whole_ids != old_ids:
        reasons.append(REREAD_REASON)
    record = {**rec, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(), "n_words": words_after,
              "text_sha256": text_hash, "youtube_ids": youtube_ids, "media_links": media,
              "rederived_from": "source.gz", "rederived_reason": "; ".join(reasons) or REDERIVE_REASON,
              "rederived_words_before": words, "rederived_text_sha256_before": rec.get("text_sha256") or ""}
    if ids_changed:
        record["rederived_youtube_ids_before"] = old_ids
    if media_changed:
        record["rederived_media_links_before"] = old_media
    out.update(verdict="changed", words_after=words_after, base=rec, path=path, old=old, text=text,
               write_text=write_text, text_changed=text_changed, record=record, ids_changed=ids_changed,
               media_changed=media_changed, ids_reread=ids_changed and whole_ids != old_ids)
    return out


def backup_texts(root: Path, changes) -> Path:
    """Every text about to be replaced, as it is on disk now, in one tar.gz under <root>/backups/ named with the UTC
    time (members keep their paths below <root>, so `tar -xzf <backup> -C <root>` puts them back). It is read back
    and checked before it gets its name; anything wrong raises, and then nothing may be written."""
    folder = root / "backups"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    final, n = folder / f"publisher-texts-before-rederive-{stamp}.tar.gz", 1
    while final.exists():
        n += 1
        final = folder / f"publisher-texts-before-rederive-{stamp}-{n}.tar.gz"
    tmp = final.with_name(final.name + f".tmp{os.getpid()}")
    wanted = {}
    try:
        with open(tmp, "wb") as raw:
            with tarfile.open(fileobj=raw, mode="w:gz") as tar:
                for change in changes:
                    name = change["path"].relative_to(root).as_posix()
                    info = tarfile.TarInfo(name)
                    info.size, info.mode = len(change["old"]), 0o644
                    info.mtime = int(change["path"].stat().st_mtime)
                    tar.addfile(info, io.BytesIO(change["old"]))
                    wanted[name] = hashlib.sha256(change["old"]).hexdigest()
            raw.flush()
            os.fsync(raw.fileno())
        found = {}
        with tarfile.open(tmp, "r:gz") as tar:
            for member in tar.getmembers():
                handle = tar.extractfile(member)
                found[member.name] = hashlib.sha256(handle.read() if handle else b"").hexdigest()
        if found != wanted:
            raise OSError(f"the backup does not read back as written ({len(found)} of {len(wanted)} file(s) match)")
        os.replace(tmp, final)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return final


def rederive(paths, only=(), apply=False, stream=None):
    """--rederive. Prints a summary per person and returns {"results": [rederive_item(...), ...], "written": texts
    rewritten, "lines": manifest lines appended, "backup": its path or None}. Without `apply` it writes nothing at all."""
    stream = stream or sys.stdout
    out_dir = paths.pubtext
    manifest = out_dir / "publisher_text_manifest.jsonl"
    recs = [r for r in latest_by_key(read_jsonl(manifest)).values()
            if r.get("status") == "ok" and (not only or r.get("channel_dir") in only)]
    # the media_pattern a fetch uses for each listed page (sources/publisher_pages.csv); None for a page no longer listed
    patterns = {job["video_id"]: job["media_pattern"] for job in load_jobs(paths, {"pages"}, set())}
    progress = Progress(len(recs), "rederive", every=30.0)
    results = []
    for rec in recs:
        pattern = patterns.get(rec["video_id"]) if rec.get("origin") == "page" else ""
        results.append(rederive_item(rec, out_dir, pattern))
        progress.tick()
    mode = "apply" if apply else "dry run"

    def links_part(group):
        """How many pages change their youtube_ids (and media_links), and on how many of them the text stays."""
        ids = [r for r in group if r["ids_changed"]]
        media = sum(r["media_changed"] for r in group)
        part = f" | ids changed {len(ids)}"
        if ids:
            reread = sum(r["ids_reread"] for r in ids)
            part += (f" ({sum(not r['text_changed'] for r in ids)} of them with the text as it is"
                     + (f"; {reread} read again with the current id reader" if reread else "") + ")")
        return part + (f" | media links changed {media}" if media else "")

    people = collections.defaultdict(list)
    for res in results:
        people[res["person"]].append(res)
    for person in sorted(people):
        group = people[person]
        count = collections.Counter(r["verdict"] for r in group)
        reasons = collections.Counter(r["reason"] for r in group if r["verdict"] == "skipped")
        before, after = sum(r["words_before"] for r in group), sum(r["words_after"] for r in group)
        line = (f"rederive ({mode}) {person}: checked {len(group)} | changed {count['changed']} | "
                f"unchanged {count['unchanged']} | skipped {count['skipped']}")
        if reasons:
            line += " (" + "; ".join(f"{why}: {n}" for why, n in sorted(reasons.items())) + ")"
        line += f" | words {before:,} -> {after:,}" + links_part(group)
        cuts = [r for r in group if r["verdict"] == "changed" and r["words_after"] < r["words_before"]]
        if cuts:
            most = max(cuts, key=lambda r: 1 - r["words_after"] / r["words_before"])
            line += f" | most cut {most['video_id']} ({most['words_before']:,} -> {most['words_after']:,} words)"
        print(line, file=stream)
    changes = [r for r in results if r["verdict"] == "changed"]
    count = collections.Counter(r["verdict"] for r in results)
    print(f"rederive ({mode}) all: checked {len(results)} | changed {count['changed']} | unchanged {count['unchanged']} "
          f"| skipped {count['skipped']} | words {sum(r['words_before'] for r in results):,} -> "
          f"{sum(r['words_after'] for r in results):,}" + links_part(results), file=stream)
    for res in changes:
        if res["ids_changed"]:
            print(f"rederive ({mode}) ids {res['person']} {res['video_id']}: "
                  f"{' '.join(res['base'].get('youtube_ids') or []) or '-'} -> {' '.join(res['record']['youtube_ids']) or '-'}"
                  f" ({res['record']['rederived_reason']})", file=stream)
    report = {"results": results, "written": 0, "lines": 0, "backup": None}
    if not apply:
        print(f"dry run: nothing was written; pass --apply to rewrite {sum(c['write_text'] for c in changes)} text(s) "
              f"and append {len(changes)} manifest line(s) (the texts they replace are saved under <root>/backups/ first)",
              file=stream)
        return report
    if not changes:
        print("rederive: nothing to rewrite", file=stream)
        return report
    replaced = [c for c in changes if c["write_text"]]
    backup = None
    if replaced:
        try:
            backup = backup_texts(paths.root, replaced)
        except Exception as err:  # noqa: BLE001 - no backup, no writes
            print(f"rederive: the backup failed ({type(err).__name__}: {err}); nothing was written", file=sys.stderr)
            raise SystemExit(1)
        print(f"rederive: {len(replaced)} text(s) saved in {backup}", file=stream)
    report["backup"] = backup
    latest = latest_by_key(read_jsonl(manifest))           # read again: another run may have added a line meanwhile
    late, run_at = 0, utc_now()                            # one time for every line of this run: a restore finds them by it
    for change in changes:
        if latest.get(change["video_id"]) != change["base"] or \
                (change["write_text"] and change["path"].read_bytes() != change["old"]):
            late += 1                                      # it changed during this run: left for the next one
            continue
        extra = {}
        if change["write_text"]:
            atomic_write_text(change["path"], change["text"] + "\n")          # the way a fetch writes it
            report["written"] += 1
            extra["rederived_backup"] = backup.relative_to(paths.root).as_posix()
        append_jsonl(manifest, {**change["record"], "rederived_at": run_at, **extra})
        report["lines"] += 1
    print(f"rederive: rewrote {report['written']} text(s), appended {report['lines']} manifest line(s)"
          + (f"; {late} changed during this run and were left alone" if late else ""), file=stream)
    return report


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
                    help="no network: read the saved page sources again and refresh the video ids found on them "
                         "(outside readers' comment threads)")
    ap.add_argument("--compact-sources", action="store_true",
                    help="no network: gzip saved page sources kept uncompressed by earlier versions (.source -> .source.gz)")
    ap.add_argument("--rederive", action="store_true",
                    help="no network: build each stored page text again from its .source.gz with the current extractor, "
                         "where that only takes lines out, and read its video ids and media links again outside readers' "
                         "comment threads; prints what would change unless --apply is given")
    ap.add_argument("--apply", action="store_true",
                    help="with --rederive: write the new texts and their manifest lines (the texts they replace go "
                         "into a tar.gz under <root>/backups/ first)")
    args = ap.parse_args()
    if args.apply and not args.rederive:
        ap.error("--apply goes with --rederive")

    paths = layout(ensure_outside_git(args.root))
    out_dir = paths.pubtext
    manifest = out_dir / "publisher_text_manifest.jsonl"
    lock = None
    if (args.rederive and args.apply) or args.rescan or args.compact_sources:
        # the modes that rewrite saved files or append to the manifest without the network run one at a time, held until
        # the process ends; a --rederive dry run writes nothing, not even a lock
        lock = file_lock(paths.jobs / REWRITE_LOCK, "fetch_publisher_text.py --rederive --apply, --rescan or --compact-sources")
    if args.rederive:
        rederive(paths, {x.strip() for x in args.only.split(",") if x.strip()}, apply=args.apply)
        return
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
            ids, _ = page_links(source.decode("utf-8", errors="replace"))      # the post's own: readers' comments left out
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
