"""Continue a public Videos grid when members-only listings occupy the first page."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_uploads_catalog import write_json
from common import ensure_outside_git, utc_now
from drive_ingest import MIN_FREE_BYTES, MAX_LOCAL_BYTES, managed_roots, reserved_project_growth, storage_usage
from fetch_publisher_text import Robots
from regular_video_index import card_details


GRID = """() => {
    const grid = Array.from(document.querySelectorAll('ytd-rich-grid-renderer')).find(el => el.getClientRects().length);
    if (!grid) return null;
    const dataset = window.ytInitialData || {};
    const owner = dataset.metadata?.channelMetadataRenderer?.externalId;
    const tabs = dataset.contents?.twoColumnBrowseResultsRenderer?.tabs || [];
    const selected = tabs.map(x => x.tabRenderer).find(x => x?.selected);
    const tab = selected?.endpoint?.commandMetadata?.webCommandMetadata?.url || '';
    const gridCards = (grid.data?.contents || []).map(x => x.richItemRenderer?.content).filter(Boolean);
    const visibleCards = Array.from(grid.querySelectorAll('ytd-rich-item-renderer')).map(el => el.data?.content).filter(Boolean);
    const cards = gridCards.length >= visibleCards.length ? gridCards : visibleCards;
    return {owner, tab, cards};
}"""


def merge_grid(previous, sample, limit=20):
    """Keep positions from the original dated listing and require an overlapping anchor for each extension."""
    if sample.get('owner') != previous['channel_id'] or not urlsplit(sample.get('tab', '')).path.endswith('/videos'):
        raise ValueError('The browser did not return the expected creator Videos tab')
    shown, seen = [], set()
    for position, card in enumerate(sample['cards']):
        row, kind = card_details(card)
        if kind not in ('regular', 'members_only') or row['video_id'] in seen:
            if kind == 'unrecognized_card':
                raise ValueError('Unknown primary card in public continuation')
            continue
        seen.add(row['video_id'])
        row.update(primary_grid_position=position, access_status='members_only' if kind == 'members_only' else 'public_listing')
        shown.append(row)
    known = previous['observed_items']
    known_ids = [row['video_id'] for row in known]
    page_ids = [row['video_id'] for row in shown]
    if not known_ids or known_ids[-1] not in page_ids:
        return []
    anchor = page_ids.index(known_ids[-1])
    overlap = min(anchor+1, len(known_ids))
    if page_ids[anchor-overlap+1:anchor+1] != known_ids[-overlap:]:
        raise ValueError('The Videos listing changed between the first page and continuation')
    extra = shown[anchor+1:]
    if set(known_ids).intersection(x['video_id'] for x in extra):
        raise ValueError('Continuation repeats an earlier regular upload')
    offset = known[-1]['primary_grid_position'] - shown[anchor]['primary_grid_position']
    for row in extra:
        row['primary_grid_position'] += offset
    return extra


def final_page_ids(document):
    """Recognize the last page YouTube appended to the visible grid during ordinary scrolling."""
    for key in ('onResponseReceivedActions', 'onResponseReceivedEndpoints'):
        actions = document.get(key)
        if not isinstance(actions, list):
            continue
        for action in actions:
            if not isinstance(action, dict):
                continue
            append = action.get('appendContinuationItemsAction')
            if not isinstance(append, dict):
                continue
            items = append.get('continuationItems')
            if not isinstance(items, list) or any(not isinstance(item, dict) or 'continuationItemRenderer' in item for item in items):
                continue
            ids = []
            for item in items:
                if 'richSectionRenderer' in item or 'adSlotRenderer' in item:
                    continue
                renderer = item.get('richItemRenderer')
                card = renderer.get('content') if isinstance(renderer, dict) else None
                if not isinstance(card, dict):
                    break
                row, kind = card_details(card)
                if kind == 'unrecognized_card':
                    break
                if kind in ('regular', 'members_only'):
                    ids.append(row['video_id'])
            else:
                if ids and len(ids) == len(set(ids)):
                    yield tuple(ids)


def extend_one(ctx, group, where, robots, limit):
    destination = where/(group['creator']+'.json')
    if destination.is_file():
        return json.loads(destination.read_bytes())
    if robots.allowed(group['url']) is not True:
        raise ValueError('Public listing is unavailable under its current robots rules')
    page = ctx.new_page()
    statuses = []
    last_pages = set()
    provider_pause = False
    def response_seen(response):
        nonlocal provider_pause
        address = urlsplit(response.url)
        if address.hostname in {'youtube.com','www.youtube.com'} and (address.path.endswith('/videos') or address.path.endswith('/browse')):
            statuses.append(response.status)
            provider_pause |= response.status in (401, 403, 429) or 'retry-after' in response.headers
    def finished(request):
        address = urlsplit(request.url)
        if address.hostname not in {'youtube.com', 'www.youtube.com'} or not address.path.endswith('/browse'):
            return
        response = request.response()
        if response and response.ok and 'application/json' in response.headers.get('content-type', ''):
            data = response.json()
            if isinstance(data, dict):
                last_pages.update(final_page_ids(data))
    page.on('response', response_seen)
    page.on('requestfinished', finished)
    try:
        response = page.goto(group['url'], wait_until='domcontentloaded', timeout=35_000)
        if response is None or response.status != 200 or page.url != group['url']:
            raise ValueError('Public channel page did not open normally')
        page.wait_for_selector('ytd-rich-grid-renderer ytd-rich-item-renderer', timeout=22_000)
        observed = list(group['observed_items'])
        added = []
        public_count = len(group['public_items'])
        last_progress = time.monotonic()
        while True:
            if provider_pause:
                raise ValueError('The channel listing requested a pause')
            sample = page.evaluate(GRID)
            extra = merge_grid({**group, 'observed_items': observed}, sample) if sample and sample['cards'] else []
            if extra:
                observed.extend(extra)
                added.extend(extra)
                public_count += sum(x['access_status'] == 'public_listing' for x in extra)
                last_progress = time.monotonic()
            # The final response and the actual displayed grid must agree on the entire trailing page.
            ids = tuple(r['video_id'] for r in observed)
            terminal = next((tail for tail in sorted(last_pages, key=len, reverse=True)
                             if len(tail) <= len(added) and ids[-len(tail):] == tail), ())
            exhausted = bool(terminal)
            if public_count >= limit or exhausted:
                record = {'creator': group['creator'], 'channel_id': group['channel_id'], 'url': group['url'],
                          'first_page_sha256': group['page_sha256'], 'observed_at': utc_now(),
                          'source': 'rendered_public_Videos_grid', 'response_statuses': statuses,
                          'exhausted': exhausted, 'final_page_video_ids': list(terminal), 'items': added}
                write_json(destination, record)
                return record
            if time.monotonic() - last_progress >= 30:
                raise ValueError('The public Videos grid stopped advancing before its final page could be confirmed')
            page.evaluate('window.scrollTo(0, document.documentElement.scrollHeight)')
            page.wait_for_timeout(1250)
    finally:
        page.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--base', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--browser-channel', default='chrome', help='installed Playwright browser channel')
    args = ap.parse_args(argv)
    root = ensure_outside_git(args.root)
    folder = ensure_outside_git(args.out.parent)/'continuation'
    if not folder.is_relative_to(root) or args.out.resolve() == args.base.resolve():
        raise ValueError('A distinct private output is required')
    folder.mkdir(parents=True, exist_ok=True)
    base = json.loads(args.base.read_bytes())
    groups = [g for g in base['channels'] if not g['public_listing_complete'] and
              g.get('can_extend', g['listing_complete'])]
    missing = [g for g in groups if not (folder/(g['creator']+'.json')).exists()]
    if missing:
        from playwright.sync_api import sync_playwright
        _, used = storage_usage(root, managed_roots(root))
        growth = reserved_project_growth(root) + 128_000_000
        if used + growth > MAX_LOCAL_BYTES or shutil.disk_usage(root).free - growth < MIN_FREE_BYTES:
            raise ValueError('Insufficient headroom for a temporary metadata browser')
        robots = Robots()
        with tempfile.TemporaryDirectory(dir=folder, prefix='metadata-browser-') as profile, sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(profile, channel=args.browser_channel, headless=True, args=['--disk-cache-size=4194304'],
                                                       locale='en-US', viewport={'width': 1100, 'height': 860})
            def route(request):
                if request.request.resource_type in ('media', 'image', 'font') or urlsplit(request.request.url).path.endswith('/videoplayback'):
                    request.abort()
                else:
                    request.continue_()
            ctx.route('**/*', route)
            try:
                for group in missing:
                    extend_one(ctx, group, folder, robots, base['per_channel'])
            finally:
                ctx.close()
    for group in groups:
        file = folder/(group['creator']+'.json')
        raw = file.read_bytes()
        cont = json.loads(raw)
        if cont['first_page_sha256'] != group['page_sha256'] or cont['channel_id'] != group['channel_id']:
            raise ValueError('Continuation does not belong to the saved first page')
        if cont.get('exhausted') is True:
            tail = cont.get('final_page_video_ids')
            if not isinstance(tail, list) or not tail or [r['video_id'] for r in cont['items'][-len(tail):]] != tail:
                raise ValueError('Final page differs from the recorded end of the Videos grid')
        template = group['observed_items'][0]
        for item in cont['items']:
            rank = len(group['observed_items'])
            row = {**{k: template[k] for k in ('channel_dir', 'expected_channel_id', 'observed_primary_channel_id', 'tab', 'source_url', 'publication_status')},
                   **item, 'listing_rank': rank, 'regular_listing_rank': rank, 'url': 'https://www.youtube.com/watch?v='+item['video_id'],
                   'observed_at': cont['observed_at'], 'page_sha256': hashlib.sha256(raw).hexdigest()}
            group['observed_items'].append(row)
            if row['access_status'] == 'public_listing' and len(group['public_items']) < base['per_channel']:
                position = len(group['public_items'])
                group['public_items'].append({**row, 'listing_rank': position, 'public_listing_rank': position})
        group['items'] = group['observed_items'][:base['per_channel']]
        group['exhausted'] = cont.get('exhausted') is True
        group['listing_complete'] = len(group['items']) == base['per_channel'] or group['exhausted']
        group['public_listing_complete'] = len(group['public_items']) == base['per_channel'] or group['exhausted']
        group['state'] = 'observed' if group['listing_complete'] else 'partial'
        group['public_continuation_observed_at'] = cont['observed_at']
    base['index_revision'] = 3
    base['summary'].update(priority_regular_videos=sum(len(g['items']) for g in base['channels']),
                           completed_channel_listings=sum(g['listing_complete'] for g in base['channels']),
                           member_only_in_literal_latest20=sum(r['access_status'] == 'members_only' for g in base['channels'] for r in g['items']),
                           states=dict(Counter(g['state'] for g in base['channels'])),
                           public_regular_targets=sum(len(g['public_items']) for g in base['channels']),
                           completed_public_channel_listings=sum(g['public_listing_complete'] for g in base['channels']),
                           observed_regular_videos=sum(len(g['observed_items']) for g in base['channels']))
    write_json(args.out, base)
    print(json.dumps(base['summary']))


if __name__ == '__main__':
    main()
