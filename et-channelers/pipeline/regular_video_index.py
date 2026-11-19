"""Index regular uploads from saved public channel Videos pages in their displayed order."""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from collect_channel_formats import MAX_BYTES, card_id
from collect_uploads_catalog import write_json
from common import utc_now
from uploads_playlist import DECODER, INITIAL_DATA, nested, text_field


AGE = re.compile(r'\b(?:ago|today|yesterday)\b', re.I)
CLOCK = re.compile(r'\d+(?::[0-5]\d){1,2}')


def strings(node, keys):
    """Read display strings only from a specific renderer subtree."""
    stack = [node]
    while stack:
        value = stack.pop()
        if isinstance(value, list):
            stack.extend(reversed(value))
        elif isinstance(value, dict):
            for key, item in reversed(value.items()):
                if key in keys and isinstance(item, str):
                    yield item
                elif isinstance(item, (list, dict)):
                    stack.append(item)


def sort_mode(header):
    stack = [header]
    options = []
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key in ('chipViewModel', 'chipCloudChipRenderer', 'listItemViewModel') and isinstance(value, dict):
                    label = value.get('text') or value.get('title')
                    label = (label.get('content') or text_field(label)) if isinstance(label, dict) else label
                    options.append((label, value.get('selected') is True or value.get('isSelected') is True))
                    if value.get('displayType') == 'CHIP_VIEW_MODEL_DISPLAY_TYPE_DROP_DOWN':
                        stack.append(value.get('tapCommand'))
                elif isinstance(value, (dict, list)):
                    stack.append(value)
    chosen = [str(label).lower() for label, selected in options if selected]
    if ('latest' in chosen or 'newest' in chosen) and not any(s in ('oldest', 'popular') for s in chosen):
        return 'selected_latest'
    if any(label in ('oldest', 'popular') for label in chosen) or any(str(label).lower() == 'latest' for label, _ in options):
        return 'different_or_unconfirmed_sort'
    return 'default_channel_order'


def card_details(card):
    ident = card_id(card)
    if not ident:
        return None, 'unrecognized_card'
    if 'shortsLockupViewModel' in card or 'reelItemRenderer' in card:
        return {'video_id': ident}, 'shorts'
    if 'lockupViewModel' in card:
        model = card['lockupViewModel']
        meta = nested(model, 'metadata.lockupMetadataViewModel') or {}
        title = nested(meta, 'title.content')
        badges = list(strings(nested(model, 'contentImage.thumbnailViewModel.overlays'), {'text', 'label', 'badgeStyle', 'style'}))
        badges.extend(strings(meta.get('badges'), {'label', 'text', 'style', 'tooltip'}))
        metadata_rows = nested(meta, 'metadata.contentMetadataViewModel.metadataRows') or []
        for details in metadata_rows:
            badges.extend(strings(details.get('badges'), {'badgeText', 'badgeStyle', 'label', 'text', 'tooltip'}))
        parts = [part for row in metadata_rows for part in row.get('metadataParts', [])]
        labels = [part.get('accessibilityLabel') or nested(part, 'text.content') for part in parts]
        labels = [s for s in labels if isinstance(s, str)]
        nav = nested(model, 'rendererContext.commandContext.onTap.innertubeCommand') or {}
        scheduled = bool(model.get('upcomingEventData'))
    else:
        model = card.get('videoRenderer') or card.get('gridVideoRenderer') or {}
        title = text_field(model.get('title'))
        badges = list(strings(model.get('badges'), {'label', 'style', 'tooltip'}))
        badges.extend(strings(model.get('thumbnailOverlays'), {'style', 'simpleText', 'text'}))
        badges.append(text_field(model.get('lengthText')))
        labels = [text_field(model.get('publishedTimeText')), text_field(model.get('viewCountText'))]
        nav = model.get('navigationEndpoint') or {}
        scheduled = bool(model.get('upcomingEventData'))
    endpoint = nested(nav, 'commandMetadata.webCommandMetadata.url') or ''
    if 'reelWatchEndpoint' in nav or urlsplit(endpoint).path.startswith('/shorts/'):
        return {'video_id': ident}, 'shorts'
    flags = ' '.join([*badges, *labels]).casefold()
    clock = next((s for s in badges if isinstance(s, str) and CLOCK.fullmatch(s)), None)
    duration = 0 if clock else None
    for digits in clock.split(':') if clock else ():
        duration = duration * 60 + int(digits)
    row = {'video_id': ident, 'title': title or '', 'duration_s': duration, 'duration_as_shown': clock,
           'publication_display': next((s for s in labels if AGE.search(s)), None),
           'display_metadata': labels, 'badges': list(dict.fromkeys(s for s in badges if s))}
    if scheduled or re.search(r'\bupcoming\b|\bscheduled\b|\bpremieres in\b|style_upcoming', flags):
        return row, 'scheduled'
    if re.search(r'\bmembers?[- _]only\b|\bmembers first\b|badge_members_only', flags):
        return row, 'members_only'
    if re.search(r'\bprivate video\b|\bdeleted video\b', flags) or title in ('Private video', 'Deleted video'):
        return row, 'unavailable'
    if re.search(r'\bstreamed\b|\blive now\b|\bwatching now\b|style_live', flags) or any(s.casefold() == 'live' for s in badges):
        return row, 'stream'
    return row, 'regular' if title else 'unrecognized_card'


def index_channel(creator, channel, raw, observed_at, evidence, limit=20):
    wire_hash = hashlib.sha256(raw).hexdigest()
    if evidence.get('wire_sha256') != wire_hash:
        raise ValueError('Saved channel page and its observation disagree')
    markup = raw.decode('utf-8')
    match = INITIAL_DATA.search(markup)
    if not match:
        raise ValueError('Missing channel page data')
    data, _ = DECODER.raw_decode(markup, match.end())
    if nested(data, 'metadata.channelMetadataRenderer.externalId') != channel:
        raise ValueError('Returned channel identity differs from the roster')
    tabs = [entry['tabRenderer'] for entry in (nested(data, 'contents.twoColumnBrowseResultsRenderer.tabs') or [])
            if isinstance(entry.get('tabRenderer'), dict)]
    def slug(tab):
        return urlsplit(nested(tab, 'endpoint.commandMetadata.webCommandMetadata.url') or '').path.rstrip('/').rsplit('/', 1)[-1]
    url = f'https://www.youtube.com/channel/{channel}/videos'
    base = {'creator': creator, 'channel_dir': creator, 'channel_id': channel, 'url': url, 'observed_at': observed_at,
            'channel_name': nested(data, 'metadata.channelMetadataRenderer.title'), 'page_sha256': wire_hash,
            'items': [], 'public_items': [], 'observed_items': [], 'excluded': [], 'listing_complete': False,
            'public_listing_complete': False}
    if tabs and all(slug(tab) != 'videos' for tab in tabs) and evidence.get('state') == 'tab_absent':
        return {**base, 'state': 'absent', 'listing_complete': True, 'public_listing_complete': True, 'exhausted': True}
    selected = [tab for tab in tabs if tab.get('selected') is True]
    if len(selected) != 1 or slug(selected[0]) != 'videos':
        return {**base, 'state': 'partial', 'reason': 'selected_tab_mismatch'}
    grid = nested(selected[0], 'content.richGridRenderer') or {}
    primary = grid.get('contents')
    order = sort_mode(grid.get('header'))
    if not isinstance(primary, list) or order == 'different_or_unconfirmed_sort':
        return {**base, 'state': 'partial', 'reason': 'grid_or_sort_unconfirmed', 'sort': order}
    entries, public, excluded, seen = [], [], [], set()
    unknown_positions = []
    continuation = False
    for position, item in enumerate(primary):
        if 'continuationItemRenderer' in item:
            continuation = True
            continue
        card = nested(item, 'richItemRenderer.content')
        if not isinstance(card, dict):
            if 'richSectionRenderer' not in item and 'adSlotRenderer' not in item:
                unknown_positions.append(position)
            continue
        row, kind = card_details(card)
        if kind not in ('regular', 'members_only') or row['video_id'] in seen:
            excluded.append({'primary_grid_position': position, 'video_id': row and row.get('video_id'),
                             'reason': 'duplicate' if kind in ('regular', 'members_only') else kind})
            if kind == 'unrecognized_card':
                unknown_positions.append(position)
            continue
        seen.add(row['video_id'])
        row.update(channel_dir=creator, expected_channel_id=channel, observed_primary_channel_id=channel,
                   listing_rank=len(entries), regular_listing_rank=len(entries), primary_grid_position=position, tab='videos', source_url=url,
                   access_status='members_only' if kind == 'members_only' else 'public_listing',
                   page_sha256=wire_hash, observed_at=observed_at, publication_status='listed_completed_regular_upload',
                   url='https://www.youtube.com/watch?v=' + row['video_id'])
        entries.append(row)
        if kind == 'regular':
            public.append({**row, 'listing_rank': len(public), 'public_listing_rank': len(public)})
    if order == 'default_channel_order' and (continuation or unknown_positions or len(entries) > limit):
        return {**base, 'state': 'partial', 'reason': 'latest_sort_unconfirmed', 'sort': order,
                'observed_items': entries, 'excluded': excluded, 'primary_grid_entries': len(primary)}

    def complete_for(rows):
        last_position = rows[limit-1]['primary_grid_position'] if len(rows) >= limit else len(primary)
        return not any(i <= last_position for i in unknown_positions) and (len(rows) >= limit or not continuation)
    complete = complete_for(entries)
    return {**base, 'state': 'observed' if complete else 'partial', 'listing_complete': complete,
            'public_listing_complete': complete_for(public), 'public_items': public[:limit],
            'can_extend': continuation and order == 'selected_latest' and bool(entries) and not unknown_positions,
            'exhausted': not continuation and not unknown_positions, 'sort': order, 'items': entries[:limit],
            'observed_items': entries, 'excluded': excluded, 'primary_grid_entries': len(primary)}


def assemble(channels, folder, index_name='fresh-videos.json'):
    folder = Path(folder)
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.json', index_name):
        raise ValueError('Expected a JSON filename in the private run directory')
    result = []
    for creator, channel in channels:
        where = folder/creator
        base = {'creator': creator, 'channel_dir': creator, 'channel_id': channel, 'url': f'https://www.youtube.com/channel/{channel}/videos',
                'items': [], 'public_items': [], 'observed_items': [], 'listing_complete': False, 'public_listing_complete': False}
        try:
            mark = json.loads((where/'videos.json').read_bytes())
            when = json.loads((where/'videos.attempt.json').read_bytes())['started']
            if (mark.get('expected_channel_id'), mark.get('creator'), mark.get('tab')) != (channel, creator, 'videos'):
                raise ValueError('Unexpected observation identity')
            if not (where/'videos.html.gz').exists():
                result.append({**base, 'state': 'unavailable', 'observed_at': when, 'reason': mark['state']})
                continue
            with gzip.open(where/'videos.html.gz', 'rb') as source:
                raw = source.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError('Archive exceeds listing page limit')
            result.append(index_channel(creator, channel, raw, when, mark))
        except (OSError, ValueError, KeyError) as exc:
            result.append({**base, 'state': 'unavailable', 'reason': str(exc)[:200]})
    summary = {'channels': len(result), 'states': dict(Counter(g['state'] for g in result)),
               'completed_channel_listings': sum(g['listing_complete'] for g in result),
               'priority_regular_videos': sum(len(g['items']) for g in result),
               'public_regular_targets': sum(len(g['public_items']) for g in result),
               'completed_public_channel_listings': sum(g['public_listing_complete'] for g in result),
               'member_only_in_literal_latest20': sum(i.get('access_status') == 'members_only' for g in result for i in g['items']),
               'observed_regular_videos': sum(len(g['observed_items']) for g in result)}
    stamp = max((g.get('observed_at', '') for g in result), default='') or utc_now()
    write_json(folder/index_name, {'schema_version': 1, 'index_revision': 2, 'label': 'Latest 20+ videos', 'per_channel': 20,
               'observed_at': stamp, 'summary': summary, 'channels': result})
    return summary
