"""Resolve unknown recording formats from the creator's public Videos, Shorts and Live tabs.

Pass the private JSON written by recording_selection.py. The default mode
uses saved observations and parses previously saved pages. Use --fetch to collect missing pages, then pass the
output folder to recording_selection.py --tab-evidence.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from channel_about import looks_like_bot_check
from collect_uploads_catalog import manifest, reject_redirect, write_json
from common import ID_RE, RateLimiter, SKIPPED_BY_RULE, ensure_outside_git, utc_now, youtube_override
from drive_ingest import MIN_FREE_BYTES
from feeds import FetchError, get_bytes, open_url
from fetch_publisher_text import Robots
from uploads_playlist import CHANNEL_ID, DECODER, INITIAL_DATA, nested


TABS = ('videos', 'shorts', 'streams')
MAX_BYTES = 8_000_000


def card_id(card):
    for renderer in ('videoRenderer', 'gridVideoRenderer', 'reelItemRenderer', 'shortsLockupViewModel', 'lockupViewModel'):
        model = card.get(renderer)
        if not isinstance(model, dict):
            continue
        if renderer == 'lockupViewModel':
            video = model.get('contentId')
            endpoint = nested(model, 'rendererContext.commandContext.onTap.innertubeCommand.watchEndpoint.videoId')
            if model.get('contentType') != 'LOCKUP_CONTENT_TYPE_VIDEO' or video != endpoint:
                return None
        elif renderer == 'shortsLockupViewModel':
            video = nested(model, 'onTap.innertubeCommand.reelWatchEndpoint.videoId')
        else:
            video = model.get('videoId')
            endpoint = (nested(model, 'navigationEndpoint.watchEndpoint.videoId')
                        or nested(model, 'navigationEndpoint.reelWatchEndpoint.videoId'))
            if endpoint and endpoint != video:
                return None
        return video if isinstance(video, str) and ID_RE.fullmatch(video) else None
    return None


def parse_tab(raw, channel, tab):
    if not CHANNEL_ID.fullmatch(channel) or tab not in TABS:
        raise ValueError('Expected a primary channel and a recording tab')
    markup = raw.decode('utf-8')
    match = INITIAL_DATA.search(markup)
    if not match:
        raise ValueError('Page is missing public channel data')
    data, _ = DECODER.raw_decode(markup, match.end())
    if nested(data, 'metadata.channelMetadataRenderer.externalId') != channel:
        raise ValueError('Page belongs to a different or unidentified channel')
    entries = nested(data, 'contents.twoColumnBrowseResultsRenderer.tabs') or []
    menu, selected = [], []
    for entry in entries:
        row = nested(entry, 'tabRenderer')
        if not isinstance(row, dict):
            continue
        url = nested(row, 'endpoint.commandMetadata.webCommandMetadata.url') or ''
        slug = urlsplit(url).path.rstrip('/').rsplit('/', 1)[-1]
        if slug in TABS:
            menu.append(slug)
        if row.get('selected') is True:
            selected.append((slug, row))
    result = {'menu_tabs': menu, 'membership': {}}
    if tab not in menu:
        return {**result, 'state': 'tab_absent'}
    if len(selected) != 1 or selected[0][0] != tab:
        return {**result, 'state': 'selected_tab_mismatch'}
    cards = nested(selected[0][1], 'content.richGridRenderer.contents')
    if not isinstance(cards, list):
        return {**result, 'state': 'unrecognized_primary_grid'}
    for position, item in enumerate(cards):
        card = nested(item, 'richItemRenderer.content')
        if isinstance(card, dict) and (video := card_id(card)):
            result['membership'].setdefault(video, position)
    return {**result, 'state': 'primary_grid_observed'}


def observe(folder, creator, channel, tab, robots, limiter):
    folder.mkdir(exist_ok=True, parents=True)
    url = f'https://www.youtube.com/channel/{channel}/{tab}'
    mark, page = folder / (tab + '.json'), folder / (tab + '.html.gz')
    base = {'expected_channel_id': channel, 'creator': creator, 'tab': tab, 'uri': url, 'membership': {}, 'menu_tabs': []}
    if mark.exists():
        record = json.loads(mark.read_bytes())
        if any(record.get(k) != base[k] for k in ('creator', 'expected_channel_id', 'tab', 'uri')):
            raise ValueError(f'Format evidence belongs to a different recording tab in {mark}')
        return record
    if page.exists():
        with gzip.open(page, 'rb') as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('Saved channel page exceeds the configured limit')
    elif robots is None:
        return {**base, 'state': 'uncached'}
    else:
        if shutil.disk_usage(folder).free < MIN_FREE_BYTES + MAX_BYTES:
            raise ValueError('Insufficient free disk space for the next observation')
        # Record the pending request before fetching so a resumed run never
        # accidentally opens the same page twice after an interrupted response.
        with (folder / (tab + '.attempt.json')).open('x', encoding='utf-8') as f:
            json.dump({**base, 'started': utc_now()}, f)
        try:
            if robots.allowed(url) is not True:
                state = 'provider_pause' if robots.held(url) or robots.refusal(url) else 'robots_disallowed'
                record = {**base, 'state': state}
                write_json(mark, record)
                return record
            limiter.wait()
            with open_url(url, timeout=20, headers={'Accept-Encoding': 'identity', 'Accept-Language': 'en'}, before_redirect=reject_redirect) as response:
                if response.headers.get('Retry-After') is not None:
                    raise FetchError(response.status, 'Provider requested a pause', klass='held')
                if (response.status != 200 or response.geturl() != url or response.headers.get_content_type() != 'text/html'
                        or response.headers.get('Content-Encoding', 'identity') != 'identity'):
                    raise ValueError('Unexpected channel listing response')
                data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES or not data:
                    raise ValueError('Empty or oversized channel listing')
            if looks_like_bot_check(url, data):
                raise FetchError(200, 'Provider requested a browser check', klass='bot_check')
            temp = page.with_suffix(f'.tmp{os.getpid()}')
            temp.write_bytes(gzip.compress(data, compresslevel=1, mtime=0))
            os.replace(temp, page)
        except FetchError as error:
            paused = error.status in (401, 403, 429) or error.retry_after is not None or error.klass in ('held', 'bot_check')
            record = {**base, 'state': 'provider_pause' if paused else 'unavailable', 'status': error.status}
            write_json(mark, record)
            return record
        except (OSError, http.client.HTTPException, ValueError) as error:
            record = {**base, 'state': 'unavailable', 'reason': type(error).__name__}
            write_json(mark, record)
            return record
    try:
        parsed = parse_tab(data, channel, tab)
    except (ValueError, UnicodeDecodeError) as error:
        parsed = {'state': 'unrecognized_page', 'reason': str(error)[:120]}
    record = {**base, 'wire_sha256': hashlib.sha256(data).hexdigest(), 'wire_bytes': len(data), **parsed}
    write_json(mark, record)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--fetch', action='store_true', help='fetch missing public pages for unresolved formats')
    args = parser.parse_args(argv)
    if args.fetch and not youtube_override():
        print('Public listing fetch skipped. Enable the project’s existing YouTube collection option to fetch pages.')
        return SKIPPED_BY_RULE
    folder = ensure_outside_git(args.out)
    validated = dict(manifest(args.selection))
    channels = json.loads(args.selection.read_bytes())['channels']
    limiter = RateLimiter(1, jitter=0)

    def get_robots(url, **options):
        limiter.wait()
        return get_bytes(url, **options, before_redirect=reject_redirect)

    robots = Robots(get=get_robots) if args.fetch else None
    totals = Counter()
    for channel in channels:
        creator = channel['channel_dir']
        remaining = {row['video_id'] for row in channel['items'] if row['tab'] == 'unknown'}
        menu = set(TABS)
        for tab in TABS:
            if not remaining or tab not in menu:
                continue
            result = observe(folder / creator, creator, validated[creator], tab, robots, limiter)
            totals[result['state']] += 1
            if result['state'] == 'provider_pause':
                print(json.dumps(dict(totals)))
                return 3
            if result['menu_tabs']:
                menu = set(result['menu_tabs'])
            remaining.difference_update(result['membership'])
        totals['unresolved_ids'] += len(remaining)
    print(json.dumps(dict(totals)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
