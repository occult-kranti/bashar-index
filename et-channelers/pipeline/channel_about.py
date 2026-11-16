#!/usr/bin/env python3
"""Read each tracked channel's public About page: its description, the links it declares, its country.

The About page (https://www.youtube.com/@handle/about) is a plain public HTML page. Its structured data
(ytInitialData, the aboutChannelViewModel block) carries the channel's description, the external links the
maker declares (title and address, wrapped in youtube.com/redirect?q=..., which is unwrapped here, nested
wrappers too; a scheme-less target gets https://, a target that is not http(s) is dropped), the country, and
the subscriber and video counts. An address written in the description text is read with a plain regular
expression (a file name such as image@2x.png is not an address); nothing is looked up anywhere else, and the
"View email address" button, which sits behind a captcha, is never pressed or emulated.

One GET per channel, at least --min-interval seconds apart (5 by default; robots.txt, read first, counts as a
request too), with the project's plain client name, no cookies, no login, no proxy. A redirect away from
youtube.com is not followed: one to consent.youtube.com or a /sorry/ page is a refusal, any other one an error.
Three refusals in a row (403, 429, a consent or bot-check page) stop the run (exit code 3). Like every other
step that asks YouTube, this one sends nothing unless the owner's override ET_YOUTUBE_ROBOTS_OVERRIDE=1 is set
for the run (exit code 9 otherwise); the About page itself is a path youtube.com's robots.txt allows, and a
disallow would be honoured.

Reads   plan/targets.csv (every row with a youtube_channel_url whose state is not excluded)
Writes  <root>/analysis/coverage/channel_about.jsonl   one line per channel fetch (latest line wins):
        person_id, channel_url, fetched_at (when the answer arrived), final_url, status, description,
        links [{title, url}], emails, country, subscribers_text, videos_text, error
--merge fetches nothing: it adds about_links, about_emails, about_country and about_fetched to
        <root>/analysis/coverage/contacts.csv (every existing column and value kept), puts the description's
        addresses into contact_emails, and names both sources in email_source. Before the table is replaced,
        the old one is copied beside it (contacts.before-about.<stamp>.csv) and every old cell outside
        contact_emails / email_source is checked against the new table; a difference aborts the merge. A merge
        that would change nothing writes nothing.

A channel fetched (status ok, same url) within --max-age-days (30) is not fetched again; a failed one is tried
again. The tool is public, its output is private: the description and the addresses stay in the private folder.

    ET_YOUTUBE_ROBOTS_OVERRIDE=1 python3 pipeline/channel_about.py --limit 3
    ET_YOUTUBE_ROBOTS_OVERRIDE=1 python3 pipeline/channel_about.py
    python3 pipeline/channel_about.py --merge
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, SKIPPED_BY_RULE, YOUTUBE_OVERRIDE, Breaker, add_root_arg, append_jsonl,  # noqa: E402
                    ensure_outside_git, host_of, latest_by_key, read_csv, read_jsonl, utc_now, write_csv,
                    youtube_override)
from feeds import FetchError, get_bytes  # noqa: E402
from fetch_publisher_text import Robots  # noqa: E402

TARGETS = ET_ROOT / "plan" / "targets.csv"
OUT_REL = Path("analysis") / "coverage" / "channel_about.jsonl"
CONTACTS_REL = Path("analysis") / "coverage" / "contacts.csv"
ABOUT_COLUMNS = ["about_links", "about_emails", "about_country", "about_fetched"]
ABOUT_SOURCE = "the channel's About page description"
MERGE_MAY_CHANGE = ("contact_emails", "email_source")        # the only existing columns a merge may touch
EMAIL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}")
# a match whose last label is a file extension is a file name (image@2x.png), not an address
FILE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico", "pdf", "mp3", "mp4", "m4a", "wav", "mov",
                   "avi", "html", "htm", "css", "js", "json", "xml", "txt", "zip", "gz", "csv", "doc", "docx"}
# words of YouTube's bot-check page, looked for only on a page that carries no about block
BOT_CHECK = ("confirm you're not a bot", "confirm you’re not a bot", "unusual traffic from your computer network",
             "/sorry/index")
MAX_PAGE_BYTES = 12_000_000
MAX_UNWRAP = 5


# ------------------------------------------------------------------------------------------------ parsing
def initial_data(markup: str):
    """The ytInitialData object of a YouTube page, or None when the page carries none."""
    decoder = json.JSONDecoder()
    for found in re.finditer(r"ytInitialData\s*=\s*", markup):
        start = markup.find("{", found.end())
        if start < 0 or start - found.end() > 2:
            continue
        try:
            data, _ = decoder.raw_decode(markup, start)
        except ValueError:
            continue
        if isinstance(data, dict):
            return data
    return None


def find_key(node, key):
    """The value under the first `key` found anywhere in a nested JSON object, or None."""
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            found = find_key(value, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_key(value, key)
            if found is not None:
                return found
    return None


def _unwrap_once(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if (host == "youtube.com" or host.endswith(".youtube.com")) and parts.path.rstrip("/") == "/redirect":
        query = urllib.parse.parse_qs(parts.query)
        for name in ("q", "url", "u"):
            if query.get(name) and query[name][0].strip():
                return query[name][0].strip()
        return ""                                              # a wrapper around nothing
    return url


def unwrap_redirect(url: str) -> str:
    """The target of a YouTube redirect wrapper (youtube.com/redirect?...&q=<target>), unwrapped until stable
    (a wrapper inside a wrapper too); any other address as is."""
    url = (url or "").strip()
    for _ in range(MAX_UNWRAP):
        inner = _unwrap_once(url)
        if inner == url:
            break
        url = inner
    return url


def normalise_link(url: str) -> str:
    """A declared link as a fetchable http(s) address: wrappers unwrapped, a scheme-less target (www.example.test/x)
    given https://, and "" for a target that is not http(s) (javascript:, mailto:, an empty q)."""
    url = unwrap_redirect(url)
    if not url:
        return ""
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", url):         # has a scheme
        return url if re.match(r"^https?://", url, re.I) else ""
    if url.startswith("//"):
        return "https:" + url
    return "https://" + url.lstrip("/")


def link_target(link_model: dict) -> str:
    """The address a channelExternalLinkViewModel points to: its tap command's url, unwrapped and normalised;
    else the shown text. "" when there is none worth keeping."""
    link = link_model.get("link") or {}
    shown = str(link.get("content") or "").strip()
    for run in link.get("commandRuns") or []:
        endpoint = find_key(run, "urlEndpoint") or {}
        url = str(endpoint.get("url") or "") if isinstance(endpoint, dict) else ""
        if not url:
            meta = find_key(run, "webCommandMetadata") or {}
            url = str(meta.get("url") or "") if isinstance(meta, dict) else ""
        if url:
            return normalise_link(url)
    return normalise_link(shown) if shown else ""


def emails_in(text: str):
    """Addresses written in a text, lower-cased, each once, in order; file names are not addresses."""
    out = []
    for match in EMAIL.findall(text or ""):
        address = match.rstrip(".").lower()
        if address.rsplit(".", 1)[-1] in FILE_EXTENSIONS:
            continue
        if address not in out:
            out.append(address)
    return out


def parse_about(markup: str) -> dict:
    """{description, links [{title, url}], emails, country, subscribers_text, videos_text, channel_id} from an About
    page, or {} when the page carries no about block (a consent page, a changed layout, not a channel)."""
    data = initial_data(markup)
    about = find_key(data, "aboutChannelViewModel") if data else None
    if not isinstance(about, dict):
        return {}
    links = []
    for item in about.get("links") or []:
        model = item.get("channelExternalLinkViewModel") if isinstance(item, dict) else None
        if not isinstance(model, dict):
            continue
        url = link_target(model)
        if not url:
            continue
        title = str((model.get("title") or {}).get("content") or "").strip()
        links.append({"title": title[:200], "url": url[:500]})
    description = str(about.get("description") or "")
    return {"description": description, "links": links, "emails": emails_in(description),
            "country": str(about.get("country") or ""), "subscribers_text": str(about.get("subscriberCountText") or ""),
            "videos_text": str(about.get("videoCountText") or ""), "channel_id": str(about.get("channelId") or "")}


def is_consent_or_sorry(url: str) -> bool:
    host = host_of(url)
    return host.startswith("consent.") or "/sorry/" in urllib.parse.urlsplit(url).path


def looks_like_bot_check(final_url: str, body: bytes) -> bool:
    """For a page that carries no about block: a consent or /sorry/ address, or the bot-check page's words."""
    if is_consent_or_sorry(final_url):
        return True
    head = body[:200_000].decode("utf-8", "replace").lower()
    return any(mark in head for mark in BOT_CHECK)


def stay_on_youtube(target: str):
    """before_redirect hook: a redirect away from youtube.com is not followed (nothing is sent to the other
    host). consent.youtube.com and /sorry/ count as a refusal (klass bot_check), anything else as an error."""
    host = host_of(target)
    if is_consent_or_sorry(target):
        raise FetchError(0, f"redirect to {host} not followed: a consent or bot-check page", target, klass="bot_check")
    if not (host == "youtube.com" or host.endswith(".youtube.com")):
        raise FetchError(0, f"redirect to {host} not followed: not youtube.com", target, klass="offsite")


# ------------------------------------------------------------------------------------------------ the list
def about_url(channel_url: str) -> str:
    return channel_url.rstrip("/").removesuffix("/videos").removesuffix("/about") + "/about"


def tracked(targets_path=TARGETS):
    """[{person_id, channel_url}] for every tracked person with a channel whose state is not excluded."""
    out = []
    for row in read_csv(targets_path) if Path(targets_path).exists() else []:
        url = (row.get("youtube_channel_url") or "").strip()
        if not url.startswith("https://www.youtube.com/") or (row.get("state") or "").strip().lower().startswith("excluded"):
            continue
        out.append({"person_id": row["person_id"], "channel_url": url.rstrip("/")})
    return out


def is_fresh(record, max_age_days: int, now=None, channel_url: str = "") -> bool:
    """True when the record is a successful fetch younger than max_age_days (of the same channel url, when one
    is given: a changed url is read again)."""
    if not record or record.get("status") != "ok":
        return False
    if channel_url and (record.get("channel_url") or "").rstrip("/") != channel_url.rstrip("/"):
        return False
    try:
        fetched = dt.datetime.fromisoformat(str(record.get("fetched_at") or "").replace("Z", "+00:00"))
    except ValueError:
        return False
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=dt.timezone.utc)
    now = now or dt.datetime.now(dt.timezone.utc)
    return (now - fetched) < dt.timedelta(days=max_age_days)


# ------------------------------------------------------------------------------------------------ fetching
def gate(step: str):
    """Nothing is sent without the owner's override. (The About page is a path robots.txt allows, so the
    general gate's wording does not fit this step; the rule is the same.)"""
    if youtube_override():
        print(f"{step}: {YOUTUBE_OVERRIDE}=1: the About pages are read, by the owner's decision (one request per "
              "channel; robots.txt is honoured)", file=sys.stderr, flush=True)
        return
    print(f"skipped: {step}: every request to youtube.com needs the owner's override {YOUTUBE_OVERRIDE}=1 (the owner "
          "opted in on 2026-11-15, but this run does not set it). Nothing was sent.", file=sys.stderr, flush=True)
    sys.exit(SKIPPED_BY_RULE)


def fetch_all(args, todo, out_path):
    """One About page per channel, paced (robots.txt first, paced too); appends a record per channel; returns
    (ok, failed, refused, tripped)."""
    last = [None]

    def paced_get(url, timeout=args.timeout, max_bytes=MAX_PAGE_BYTES, before_redirect=stay_on_youtube):
        if last[0] is not None:
            wait = args.min_interval - (time.monotonic() - last[0])
            if wait > 0:
                time.sleep(wait)
        last[0] = time.monotonic()
        return get_bytes(url, timeout=timeout, max_bytes=max_bytes, before_redirect=before_redirect)

    robots, breaker = Robots(get=paced_get), Breaker(args.stop_after_blocks)
    ok = failed = refused = 0
    for n, entry in enumerate(todo, 1):
        if breaker.tripped.is_set():
            break
        url = about_url(entry["channel_url"])
        rec = {"person_id": entry["person_id"], "channel_url": entry["channel_url"], "fetched_at": "", "final_url": "",
               "status": "", "description": "", "links": [], "emails": [], "country": "", "subscribers_text": "",
               "videos_text": "", "error": ""}
        allowed = robots.allowed(url)
        if allowed is not True:
            rec.update(fetched_at=utc_now(), status="error",
                       error="robots.txt disallows the About page" if allowed is False else "robots.txt could not be read this run")
            append_jsonl(out_path, rec)
            failed += 1
            continue
        try:
            final, _, body = paced_get(url)
        except FetchError as err:
            rec.update(fetched_at=utc_now(), final_url=err.final_url or "")
            if err.status in (403, 429) or err.klass == "bot_check":
                breaker.hard_block()
                rec.update(status="refused", error=f"HTTP {err.status}" if err.status else str(err)[:300])
                refused += 1
            else:
                rec.update(status="error", error=str(err)[:300])
                failed += 1
            append_jsonl(out_path, rec)
            continue
        rec.update(fetched_at=utc_now(), final_url=final)
        facts = parse_about(body.decode("utf-8", "replace"))
        if facts:
            breaker.success()
            facts.pop("channel_id", None)
            rec.update(status="ok", **facts)
            ok += 1
        elif looks_like_bot_check(final, body):
            breaker.hard_block()
            rec.update(status="refused", error="consent or bot-check page instead of the channel")
            refused += 1
        else:
            breaker.success()                                  # the page answered; it just carried no about block
            rec.update(status="no_about", error="the page carries no aboutChannelViewModel block")
            failed += 1
        append_jsonl(out_path, rec)
        if n % 10 == 0 or n == len(todo):
            print(f"[about] {n}/{len(todo)} channels read", file=sys.stderr, flush=True)
    return ok, failed, refused, breaker.tripped.is_set()


# ------------------------------------------------------------------------------------------------ merging
def split_values(text: str):
    return [v for v in re.split(r"[\s;,]+", (text or "").strip()) if v]


class MergeAborted(Exception):
    """The merged table would differ from the old one in a cell no merge may change: nothing was written."""


def verify_kept(before, after, old_fields):
    """Raises MergeAborted unless `after` has the same rows as `before` with every old cell unchanged, apart from
    the columns a merge may write (the About columns, contact_emails, email_source)."""
    may_change = set(MERGE_MAY_CHANGE) | set(ABOUT_COLUMNS)
    if len(after) != len(before):
        raise MergeAborted(f"row count would change: {len(before)} -> {len(after)}")
    for n, (old, new) in enumerate(zip(before, after), 1):
        if (new.get("person_id") or "") != (old.get("person_id") or ""):
            raise MergeAborted(f"row {n} person_id would change: nothing written")
        for column in old_fields:
            if column not in may_change and (new.get(column) or "") != (old.get(column) or ""):
                raise MergeAborted(f"row {n} column {column} would change: nothing written")


def merge_contacts(contacts_path, records, stamp=None) -> dict:
    """Adds the About columns to the contacts table in place; every existing column and value is kept. The
    description's addresses go into contact_emails (union, existing first) and email_source names both sources.
    Before the table is replaced the old one is copied beside it (contacts.before-about.<stamp>.csv) and every
    old cell outside contact_emails / email_source is checked; a difference raises MergeAborted. A merge that
    would change nothing writes nothing (and makes no copy). Returns counts."""
    contacts_path = Path(contacts_path)
    rows = read_csv(contacts_path) if contacts_path.exists() else []
    fields = list(rows[0].keys()) if rows else []
    if not rows:
        with open(contacts_path, newline="", encoding="utf-8-sig") as handle:
            header = handle.readline().strip()
        fields = [f for f in header.split(",") if f] if header else []
    old_fields, before = list(fields), [dict(r) for r in rows]
    for column in ABOUT_COLUMNS:
        if column not in fields:
            fields.append(column)
    for column in MERGE_MAY_CHANGE:
        if column not in fields:
            fields.append(column)
    latest = latest_by_key([r for r in records if r.get("status") == "ok"], "person_id")
    touched = emails_added = 0
    for row in rows:
        for column in ABOUT_COLUMNS + list(MERGE_MAY_CHANGE):
            row.setdefault(column, "")
        rec = latest.get(row.get("person_id"))
        if not rec:
            continue
        touched += 1
        row["about_links"] = " ".join(dict.fromkeys(l["url"] for l in rec.get("links") or [] if l.get("url")))
        row["about_emails"] = " ".join(rec.get("emails") or [])
        row["about_country"] = rec.get("country") or ""
        row["about_fetched"] = str(rec.get("fetched_at") or "")[:10]
        if rec.get("emails"):
            have = split_values(row["contact_emails"])
            new = [e for e in rec["emails"] if e.lower() not in {h.lower() for h in have}]
            if new:
                emails_added += len(new)
                row["contact_emails"] = " ".join(have + new)
            sources = [s.strip() for s in (row["email_source"] or "").split(";") if s.strip()]
            if ABOUT_SOURCE not in sources:
                sources.append(ABOUT_SOURCE)
            row["email_source"] = "; ".join(sources)
    verify_kept(before, rows, old_fields)
    changed = fields != old_fields or any(new.get(c, "") != old.get(c, "") for old, new in zip(before, rows) for c in fields)
    counts = {"rows": len(rows), "with_about": touched, "emails_added": emails_added, "columns": len(fields),
              "changed": changed, "copy": ""}
    if not changed:
        return counts
    if contacts_path.exists():
        stamp = stamp or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        copy = contacts_path.with_name(f"{contacts_path.stem}.before-about.{stamp}.csv")
        n = 1
        while copy.exists():                                   # a second merge in the same second: its own copy
            n += 1
            copy = contacts_path.with_name(f"{contacts_path.stem}.before-about.{stamp}-{n}.csv")
        shutil.copy2(contacts_path, copy)
        counts["copy"] = str(copy)
    write_csv(contacts_path, rows, fields)
    return counts


# ------------------------------------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--targets", type=Path, default=TARGETS)
    ap.add_argument("--limit", type=int, default=0, help="fetch at most N channels")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--merge", action="store_true", help="fetch nothing; add the About columns to contacts.csv")
    ap.add_argument("--min-interval", type=float, default=5.0, help="seconds between requests (default 5)")
    ap.add_argument("--max-age-days", type=int, default=30, help="a channel read this recently is not read again")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--stop-after-blocks", type=int, default=3)
    args = ap.parse_args(argv)
    root = ensure_outside_git(args.root)
    out_path, contacts_path = root / OUT_REL, root / CONTACTS_REL
    records = read_jsonl(out_path)
    if args.merge:
        if not contacts_path.exists():
            print(f"no contacts table at {contacts_path}", file=sys.stderr)
            sys.exit(2)
        try:
            counts = merge_contacts(contacts_path, records)
        except MergeAborted as why:
            print(f"merge aborted: {why}", file=sys.stderr)
            sys.exit(4)
        print(f"contacts {counts['rows']} rows | {counts['with_about']} with an About page read | "
              f"{counts['emails_added']} addresses added to contact_emails | {counts['columns']} columns -> {contacts_path}"
              + (f" | old table kept as {counts['copy']}" if counts["copy"] else " | nothing to change, nothing written"))
        return
    wanted = tracked(args.targets)
    if args.only:
        only = {p.strip() for p in args.only.split(",") if p.strip()}
        wanted = [e for e in wanted if e["person_id"] in only]
    latest = latest_by_key(records, "person_id")
    due = [e for e in wanted if not is_fresh(latest.get(e["person_id"]), args.max_age_days, channel_url=e["channel_url"])]
    todo = due[:args.limit] if args.limit else due
    print(f"channels {len(wanted)} | read within {args.max_age_days} days {len(wanted) - len(due)} | to read {len(todo)}",
          file=sys.stderr)
    if not todo:
        return
    gate("channel_about.py")                                # nothing is sent without the owner's override
    ok, failed, refused, tripped = fetch_all(args, todo, out_path)
    print(f"read {ok} | failed {failed} | refused {refused} of {len(todo)} -> {out_path}")
    if tripped:
        print("STOPPED: three refusals in a row. Wait, then rerun: channels already read are skipped.", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
