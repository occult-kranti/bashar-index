"""Read each primary channel's public uploads playlist once, retaining a mixed-type inventory.

The channel manifest is a CSV with channel_dir and channel_id, or JSON with
{"channels": [{"creator": "...", "channel_id": "UC..."}]}. All run files go under
the private output folder. Use a new folder for a fresh point-in-time inventory.

    python pipeline/collect_uploads_catalog.py plan --channels channels.csv
    python pipeline/collect_uploads_catalog.py fetch --channels channels.csv --out /private/catalog-run
    python pipeline/collect_uploads_catalog.py reparse --channels channels.csv --out /private/catalog-run

Each row records its displayed position, credited creators and live or duration
labels. A confirmed source-tab classification and completed recording can be
joined by video ID. No format is inferred from its length.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from channel_about import is_consent_or_sorry, looks_like_bot_check
from common import RateLimiter, SKIPPED_BY_RULE, atomic_write_text, ensure_outside_git, read_csv, utc_now, youtube_override
from feeds import FetchError, get_bytes, open_url
from fetch_publisher_text import Robots
from uploads_playlist import CHANNEL_ID, parse_uploads_page, uploads_url


MAX_PAGE_BYTES = 16_000_000
PROBE_INTERVAL = 1_600_000


def write_json(path, value):
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def manifest(path):
    rows = json.loads(path.read_bytes())["channels"] if path.suffix.lower() == ".json" else read_csv(path)
    result = []
    owners, creators = set(), set()
    for row in rows:
        creator = row.get("creator") or row.get("channel_dir")
        channel = row.get("channel_id")
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", creator or "")
                or not CHANNEL_ID.fullmatch(channel or "") or channel in owners or creator.casefold() in creators):
            raise ValueError("Each manifest row needs a unique creator and public channel ID")
        owners.add(channel)
        creators.add(creator.casefold())
        result.append((creator, channel))
    if not result:
        raise ValueError("Empty channel manifest")
    return result


def reject_redirect(url):
    kind = "bot_check" if is_consent_or_sorry(url) else "redirect"
    raise FetchError(0, "Uploads playlist redirect", url, klass=kind)


def capture(response, channel, target, body):
    if response.status != 200 or response.geturl() != uploads_url(channel):
        raise ValueError("Unexpected public playlist response")
    if response.headers.get("Retry-After"):
        raise FetchError(response.status, "Provider requested a pause", klass="held")
    if (response.headers.get("Content-Encoding", "identity").lower() != "identity"
            or response.headers.get("Content-Type", "").split(";")[0].lower().strip() != "text/html"):
        raise ValueError("Unexpected public playlist content type")
    size = response.headers.get("Content-Length")
    if size is not None and (not size.isascii() or not size.isdigit() or int(size) <= 0):
        raise ValueError("Invalid declared page size")
    declared = int(size) if size else None
    next_probe = PROBE_INTERVAL
    complete = False
    deadline = time.monotonic() + 45
    while len(body) < MAX_PAGE_BYTES:
        if time.monotonic() >= deadline:
            break
        piece = response.read1(min(65_536, MAX_PAGE_BYTES - len(body)))
        if not piece:
            complete = declared is None or declared == len(body)
            break
        body.extend(piece)
        if declared is not None and len(body) == declared:
            complete = True
            break
        if len(body) >= next_probe:
            next_probe += PROBE_INTERVAL
            try:
                frames = parse_uploads_page(bytes(body), channel, complete_http=False)
            except ValueError:
                continue
            positions = {row["position_zero_based"] for row in frames["items"]}
            if all(n in positions for n in range(target)):
                return frames, False, "requested_prefix_observed"
    try:
        frames = parse_uploads_page(bytes(body), channel, complete_http=complete)
    except ValueError as error:
        if looks_like_bot_check(uploads_url(channel), bytes(body)):
            raise FetchError(200, "Challenge page in place of the playlist", klass="bot_check") from None
        # Record actual HTTP completeness even when this version cannot parse the page.
        return None, complete, str(error)
    return frames, complete, "complete_http" if complete else "bounded_or_partial_http"


def save_page(folder, body):
    final = folder / "public-listing.html.gz"
    tmp = final.with_suffix(f".tmp{os.getpid()}")
    tmp.write_bytes(gzip.compress(body, compresslevel=1, mtime=0))
    os.replace(tmp, final)


def observe(creator, channel, folder, robots, limiter, target):
    url = uploads_url(channel)
    rec = {"creator": creator, "channel_id": channel, "url": url, "started": utc_now(),
           "listing_requests": 0, "complete_http": False, "provider_stop": False}
    folder.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also prevents two runs from opening the same page.
    with (folder / "attempt.json").open("x", encoding="utf-8") as handle:
        json.dump(rec, handle)
    body = bytearray()
    try:
        if robots.allowed(url) is not True:
            rec["result"] = "robots_disallowed_or_unavailable"
            rec["provider_stop"] = bool(robots.refusal(url) or robots.held(url))
        else:
            limiter.wait()
            rec["listing_requests"] = 1
            headers = {"Accept-Encoding": "identity", "Accept-Language": "en"}
            with open_url(url, timeout=20, headers=headers, before_redirect=reject_redirect) as response:
                rec["http_status"] = response.status
                frames, rec["complete_http"], rec["read_end"] = capture(response, channel, target, body)
            if frames:
                write_json(folder / "frames.json", frames)
                rec["result"] = "verified_primary_frames"
                rec["verified_positions"] = len(frames["items"])
            else:
                rec["result"] = "unrecognized_or_incomplete_playlist"
    except FetchError as error:
        rec["http_status"] = error.status
        rec["result"] = error.klass or "request_error"
        rec["provider_stop"] = error.status in (401, 403, 429) or error.retry_after is not None or error.klass in ("bot_check", "held")
    except (ValueError, OSError, http.client.HTTPException) as error:
        rec["result"] = "page_read_error"
        rec["error"] = str(error)[:200]
    if body:
        save_page(folder, body)
    rec.update(ended=utc_now(), observed_bytes=len(body), body_sha256=hashlib.sha256(body).hexdigest())
    write_json(folder / "receipt.json", rec)
    return rec


def reparse(folder, channel):
    receipt_file = folder / "receipt.json"
    source = folder / "public-listing.html.gz"
    if not receipt_file.is_file() or not source.is_file():
        return False
    rec = json.loads(receipt_file.read_bytes())
    with gzip.open(source, "rb") as stream:
        raw = stream.read(MAX_PAGE_BYTES + 1)
    if (len(raw) > MAX_PAGE_BYTES or rec["channel_id"] != channel or len(raw) != rec["observed_bytes"]
            or hashlib.sha256(raw).hexdigest() != rec["body_sha256"]):
        raise ValueError("Saved source differs from its acquisition receipt")
    try:
        frames = parse_uploads_page(raw, channel, complete_http=rec["complete_http"])
    except ValueError:
        return False
    write_json(folder / "frames.json", frames)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=("plan", "fetch", "reparse"))
    parser.add_argument("--channels", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--prefix", type=int, default=55, help="verified positions to retain before ending the read")
    parser.add_argument("--min-interval", type=float, default=1.0, help="minimum seconds between requests")
    args = parser.parse_args(argv)
    if args.prefix < 1 or args.prefix > 100 or args.min_interval < 0:
        parser.error("Use a prefix in 1..100 and a nonnegative minimum interval")
    if args.mode == "fetch" and not youtube_override():
        print("Uploads catalog skipped. Set ET_YOUTUBE_ROBOTS_OVERRIDE=1 for the authorized collection run.", file=sys.stderr)
        return SKIPPED_BY_RULE
    channels = manifest(args.channels)
    if args.mode == "plan":
        print(json.dumps({"creators": len(channels), "listing_requests": 0, "prefix": args.prefix}))
        return 0
    if not args.out:
        parser.error("--out is required for fetch and reparse")
    out = ensure_outside_git(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.mode == "reparse":
        count = sum(reparse(out / creator, channel) for creator, channel in channels)
        print(json.dumps({"parsed_creators": count, "creators": len(channels), "listing_requests": 0}))
        return 0
    limiter = RateLimiter(args.min_interval, jitter=0)

    def get_robots(url, **options):
        limiter.wait()
        return get_bytes(url, **options, before_redirect=reject_redirect)

    robots = Robots(get=get_robots)
    counts = Counter()
    seen = requests = 0
    stopped = ""
    for creator, channel in channels:
        folder = out / creator
        receipt_file = folder / "receipt.json"
        if receipt_file.is_file():
            rec = json.loads(receipt_file.read_bytes())
            if rec.get("channel_id") != channel or rec.get("creator") != creator:
                raise ValueError("The run folder contains receipts for a different creator manifest")
        elif (folder / "attempt.json").exists():
            stopped = "previous_attempt_has_no_receipt"
            break
        elif shutil.disk_usage(out).free < 2_000_000_000 + MAX_PAGE_BYTES:
            stopped = "local_storage_buffer"
            break
        else:
            try:
                rec = observe(creator, channel, folder, robots, limiter, args.prefix)
            except FileExistsError:
                stopped = "another_process_started_this_creator"
                break
            requests += rec["listing_requests"]
        seen += 1
        counts[rec["result"]] += 1
        if rec["provider_stop"]:
            stopped = "provider_pause"
            break
    summary = {"creators": len(channels), "accounted_creators": seen, "listing_requests_this_invocation": requests,
               "results": dict(counts), "stopped": stopped, "ended": utc_now()}
    write_json(out / "summary.json", summary)
    print(json.dumps(summary))
    return 3 if stopped else 0


if __name__ == "__main__":
    raise SystemExit(main())
