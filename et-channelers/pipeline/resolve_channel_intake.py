"""Resolve submitted YouTube channels and save one reusable Videos listing per new channel."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from channel_about import looks_like_bot_check
from collect_channel_formats import MAX_BYTES, parse_tab
from collect_uploads_catalog import reject_redirect, write_json
from common import RateLimiter, ensure_outside_git, utc_now
from drive_ingest import MAX_LOCAL_BYTES, MIN_FREE_BYTES, managed_roots, reserved_project_growth, storage_usage
from feeds import get_bytes, open_url
from fetch_publisher_text import Robots
from uploads_playlist import CHANNEL_ID, DECODER, INITIAL_DATA, nested


def channel_path(url):
    parts = urlsplit(url)
    if parts.netloc not in {'youtube.com', 'www.youtube.com'} or parts.scheme not in {'https', 'http'}:
        raise ValueError('Expected a public YouTube channel address')
    path = unquote(parts.path).rstrip('/')
    if not (re.fullmatch(r'/@[^/\s?#]+', path) or re.fullmatch(r'/channel/UC[\w-]{22}', path, re.ASCII)):
        raise ValueError('Expected a channel handle or channel ID')
    return path


def channel_identity(raw, submitted):
    markup = raw.decode('utf-8')
    match = INITIAL_DATA.search(markup)
    if not match:
        raise ValueError('Missing public channel data')
    document, _ = DECODER.raw_decode(markup, match.end())
    meta = nested(document, 'metadata.channelMetadataRenderer') or {}
    ident = meta.get('externalId') or ''
    if not CHANNEL_ID.fullmatch(ident) or channel_path(meta.get('channelUrl', '')) != '/channel/' + ident:
        raise ValueError('Channel metadata and canonical channel URL disagree')
    handles = []
    for url in [meta.get('vanityChannelUrl'), *(meta.get('ownerUrls') or [])]:
        if url:
            try:
                path = channel_path(url)
            except ValueError:
                continue
            if path.startswith('/@') and path not in handles:
                handles.append(path)
    requested = channel_path(submitted)
    if (requested.startswith('/channel/') and requested != '/channel/' + ident
            or requested.startswith('/@') and requested.casefold() not in {h.casefold() for h in handles}):
        raise ValueError('Submitted channel disagrees with the owner of the Videos tab')
    return {'channel_id': ident, 'channel_name': meta['title'], 'canonical_url': 'https://www.youtube.com/channel/' + ident,
            'handle': handles[0][1:] if handles else '', 'description': meta.get('description', '')}


def resolve(root, submissions, folder, *, workers=3):
    root, folder = ensure_outside_git(root), ensure_outside_git(folder)
    if not folder.is_relative_to(root) or not 1 <= workers <= 6:
        raise ValueError('Use a private intake folder and one to six listing workers')
    roster = list(submissions)
    slugs = [r['creator'] for r in roster]
    if len(set(slugs)) != len(slugs) or any(not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,119}', n) for n in slugs):
        raise ValueError('Each submitted creator needs a unique directory')
    for entry in roster:
        channel_path(entry['url'])
    folder.mkdir(parents=True, exist_ok=True)
    _, used = storage_usage(root, managed_roots(root))
    allowance = min(MAX_LOCAL_BYTES - used, shutil.disk_usage(folder).free - MIN_FREE_BYTES) - reserved_project_growth(root)
    if sum(not (folder/n/'videos.html.gz').is_file() for n in slugs) * (MAX_BYTES + 256_000) > allowance:
        raise ValueError('Insufficient disk headroom for the submitted listings')
    limiter = RateLimiter(1, jitter=0)
    def get_rules(url, **kw):
        limiter.wait()
        return get_bytes(url, **kw, before_redirect=reject_redirect)
    robots = Robots(get=get_rules)
    def observe(entry):
        slug, url = entry['creator'], 'https://www.youtube.com' + channel_path(entry['url']) + '/videos'
        home = folder/slug
        home.mkdir(exist_ok=True)
        page, attempt = home/'videos.html.gz', home/'videos.attempt.json'
        if page.is_file():
            when = json.loads(attempt.read_bytes())
            if when['uri'] != url:
                raise ValueError('Cached page belongs to a different submitted URL')
            with gzip.open(page, 'rb') as source:
                raw = source.read(MAX_BYTES + 1)
        else:
            if robots.allowed(url) is not True:
                raise ValueError('Public channel listing disallowed or temporarily unavailable')
            limiter.wait()
            when = {'started': utc_now(), 'uri': url, 'creator': slug}
            with open_url(url, timeout=25, headers={'Accept-Encoding':'identity', 'Accept-Language':'en'},
                          before_redirect=reject_redirect) as response:
                if (response.status != 200 or response.geturl() != url or response.headers.get('Retry-After') is not None
                        or response.headers.get_content_type() != 'text/html'):
                    raise ValueError('Unexpected response from the submitted channel')
                raw = response.read(MAX_BYTES + 1)
        if not raw or len(raw) > MAX_BYTES or looks_like_bot_check(url, raw):
            raise ValueError('Expected a bounded public channel page')
        identity = channel_identity(raw, entry['url'])
        channel = identity['channel_id']
        observation = parse_tab(raw, channel, 'videos')
        if not page.exists():
            write_json(attempt, when)
            temp = page.with_suffix('.tmp')
            temp.write_bytes(gzip.compress(raw, compresslevel=1, mtime=0))
            os.replace(temp, page)
        digest = hashlib.sha256(raw).hexdigest()
        write_json(home/'videos.json', {'creator': slug, 'expected_channel_id': channel, 'uri': url, 'tab': 'videos',
                                        'wire_bytes': len(raw), 'wire_sha256': digest, **observation})
        result = dict(identity, creator=slug, submitted_url=entry['url'], observed_at=when['started'], page_sha256=digest)
        write_json(home/'identity.json', result)
        return result
    # Load the shared origin's robots file once before concurrent listing requests.
    if any(not (folder/n/'videos.html.gz').is_file() for n in slugs):
        robots.allowed('https://www.youtube.com/')
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(observe, roster))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--submissions', type=Path, required=True, help='JSON list of objects with creator and url')
    args = ap.parse_args()
    results = resolve(args.root, json.loads(args.submissions.read_bytes()), args.out)
    write_json(args.out/'resolved-channels.json', {'channels': results})
    print(json.dumps([{'creator': r['creator'], 'channel_id': r['channel_id'], 'handle': r['handle']} for r in results]))


if __name__ == '__main__':
    main()
