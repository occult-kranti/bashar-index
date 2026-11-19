import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from extend_regular_video_grid import GRID, extend_one, final_page_ids, merge_grid
from regular_video_index import card_details, index_channel, sort_mode


CHANNEL = 'UC' + 'A' * 22


def card(number, *, duration=None, age=None, badges=(), tab='watch', upcoming=False):
    video_id = f'{number:011d}'
    model = {'videoId': video_id, 'title': {'simpleText': f'Talk {number}'},
             'navigationEndpoint': {'watchEndpoint': {'videoId': video_id},
                                    'commandMetadata': {'webCommandMetadata': {'url': f'/{tab}/{video_id}'}}},
             'badges': [{'metadataBadgeRenderer': {'label': label}} for label in badges]}
    if duration:
        model['lengthText'] = {'simpleText': duration}
    if age:
        model['publishedTimeText'] = {'simpleText': age}
    if upcoming:
        model['upcomingEventData'] = {'startTime': '1820000000'}
    return {'videoRenderer': model}


def dropdown(selected):
    return {'chipViewModel': {'displayType': 'CHIP_VIEW_MODEL_DISPLAY_TYPE_DROP_DOWN',
        'tapCommand': {'items': [{'listItemViewModel': {'title': {'content': name}, 'isSelected': name == selected}}
                                 for name in ('Latest', 'Popular', 'Oldest')]}}}


def page_bytes(cards, *, chosen='Latest', extra=()):
    grid = {'header': dropdown(chosen) if chosen else {}, 'contents': [{'richItemRenderer': {'content': c}} for c in cards] + list(extra)}
    tab = {'selected': True, 'endpoint': {'commandMetadata': {'webCommandMetadata': {'url': '/@example/videos'}}},
           'content': {'richGridRenderer': grid}}
    value = {'metadata': {'channelMetadataRenderer': {'externalId': CHANNEL}},
             'contents': {'twoColumnBrowseResultsRenderer': {'tabs': [{'tabRenderer': tab}]}}}
    return ('<script>var ytInitialData = ' + json.dumps(value) + ';</script>').encode()


def group(cards, *, chosen='Latest', extra=(), limit=20):
    raw = page_bytes(cards, chosen=chosen, extra=extra)
    return index_channel('example', CHANNEL, raw, '2026-11-19T01:00:00Z',
                         {'wire_sha256': hashlib.sha256(raw).hexdigest()}, limit)


class RegularVideoIndexTests(unittest.TestCase):
    def test_short_recordings_old_recordings_and_undated_records_keep_displayed_order(self):
        recent = [card(8, tab='shorts'), card(9, upcoming=True), card(10, badges=['LIVE']),
                  card(1, duration='0:12', age='7 years ago'), card(2, duration='100:00:05'),
                  card(3, age='12 years ago')]
        result = group(recent, extra=[{'richSectionRenderer': {'content': card(15)}}])
        self.assertEqual([x['video_id'] for x in result['public_items']], [f'{i:011d}' for i in (1, 2, 3)])
        self.assertEqual([x['duration_s'] for x in result['public_items']], [12, 360005, None])
        self.assertIsNone(result['public_items'][1]['publication_display'])
        self.assertTrue(result['exhausted'])
        self.assertTrue(result['public_listing_complete'])
        self.assertEqual([x['reason'] for x in result['excluded']], ['shorts', 'scheduled', 'stream'])

    def test_members_only_keeps_its_literal_position_public_list_continues(self):
        result = group([card(1, badges=['Members only']), card(2), card(3)], limit=2)
        self.assertEqual([x['video_id'] for x in result['items']], [f'{i:011d}' for i in (1, 2)])
        self.assertEqual([x['video_id'] for x in result['public_items']], [f'{i:011d}' for i in (2, 3)])
        self.assertEqual([x['regular_listing_rank'] for x in result['public_items']], [1, 2])
        self.assertEqual([x['public_listing_rank'] for x in result['public_items']], [0, 1])
        self.assertEqual(result['items'][0]['access_status'], 'members_only')

    def test_selected_sort_and_unrecognized_position_prevent_false_coverage(self):
        self.assertEqual(sort_mode(dropdown('Latest')), 'selected_latest')
        for selected in ('Popular', 'Oldest'):
            self.assertFalse(group([card(1)], chosen=selected)['listing_complete'])
        uncertain = group([{}, card(1)], limit=1)
        self.assertFalse(uncertain['public_listing_complete'])
        continuation = group([card(1)], extra=[{'continuationItemRenderer': {}}], limit=2)
        self.assertFalse(continuation['public_listing_complete'])
        self.assertTrue(group([card(1), card(2)], chosen=None, limit=2)['listing_complete'])
        self.assertFalse(group([card(1), card(2), card(3)], chosen=None, limit=2)['listing_complete'])

    def test_continuation_must_overlap_displayed_order_and_creator(self):
        previous = group([card(1), card(2), card(3)])
        sample = {'owner': CHANNEL, 'tab': '/@example/videos', 'cards': [card(2), card(3), card(4)]}
        self.assertEqual([r['primary_grid_position'] for r in merge_grid(previous, sample)], [3])
        with self.assertRaises(ValueError):
            merge_grid(previous, {**sample, 'cards': [card(1), card(3), card(4)]})
        with self.assertRaises(ValueError):
            merge_grid(previous, {**sample, 'owner': 'UC'+'B'*22})
        self.assertEqual(merge_grid(previous, {**sample, 'cards': [card(8), card(9)]}), [])

    def test_inconsistent_renderer_identity_is_excluded(self):
        wrong = card(1)
        wrong['videoRenderer']['navigationEndpoint']['watchEndpoint']['videoId'] = f'{2:011d}'
        self.assertEqual(card_details(wrong), (None, 'unrecognized_card'))

    def test_progressing_public_grid_can_pass_eight_member_pages(self):
        previous = group([card(1)], extra=[{'continuationItemRenderer': {}}], limit=2)
        self.assertTrue(previous['can_extend'])
        pages = iter([card(i, badges=['Members only']) for i in range(2, 12)] + [card(12)])
        visible = [card(1)]
        ctx = Mock()
        page = ctx.new_page.return_value
        page.goto.return_value.status = 200
        page.url = previous['url']
        def evaluate(script):
            if script == GRID:
                return {'owner': CHANNEL, 'tab': '/@example/videos', 'cards': visible[-2:]}
            visible.append(next(pages))
        page.evaluate.side_effect = evaluate
        robots = Mock()
        robots.allowed.return_value = True
        with tempfile.TemporaryDirectory() as folder:
            result = extend_one(ctx, previous, Path(folder), robots, 2)
        self.assertEqual(len(result['items']), 11)
        self.assertEqual(result['items'][-1]['video_id'], f'{12:011d}')
        self.assertFalse(result['exhausted'])

    def test_final_response_must_describe_an_identifiable_page_without_a_continuation(self):
        def payload(items):
            return {'onResponseReceivedActions': [{'appendContinuationItemsAction': {'continuationItems': items}}]}
        initial = [{'richItemRenderer': {'content': card(2)}}, {'richItemRenderer': {'content': card(3)}}]
        self.assertEqual(list(final_page_ids(payload(initial))), [(f'{2:011d}', f'{3:011d}')])
        self.assertEqual(list(final_page_ids(payload(initial + [{'continuationItemRenderer': {}}]))), [])
        self.assertEqual(list(final_page_ids(payload(initial + [{'unrecognized': {}}]))), [])
        self.assertEqual(list(final_page_ids(payload(initial + [{'richItemRenderer': None}]))), [])
        self.assertEqual(list(final_page_ids({'onResponseReceivedEndpoints': None,
            'onResponseReceivedActions': [{'appendContinuationItemsAction': None}]})), [])

    def test_short_final_listing_requires_end_of_same_displayed_grid(self):
        previous = group([card(1)], extra=[{'continuationItemRenderer': {}}], limit=20)
        ctx = Mock()
        page = ctx.new_page.return_value
        page.goto.return_value.status = 200
        page.url = previous['url']
        handlers = {}
        page.on.side_effect = lambda name, callback: handlers.update({name: callback})
        visible = [card(1)]
        def evaluate(script):
            if script == GRID:
                return {'owner': CHANNEL, 'tab': '/@example/videos', 'cards': visible}
            visible.append(card(2, badges=['Members only']))
            finished = Mock(url='https://www.youtube.com/youtubei/v1/browse')
            response = finished.response.return_value
            response.ok = True
            response.headers = {'content-type': 'application/json'}
            response.json.return_value = {'onResponseReceivedActions': [{'appendContinuationItemsAction': {
                'continuationItems': [{'richItemRenderer': {'content': visible[-1]}}]}}]}
            handlers['requestfinished'](finished)
        page.evaluate.side_effect = evaluate
        robots = Mock()
        robots.allowed.return_value = True
        with tempfile.TemporaryDirectory() as folder:
            result = extend_one(ctx, previous, Path(folder), robots, 20)
        self.assertTrue(result['exhausted'])
        self.assertEqual(result['final_page_video_ids'], [f'{2:011d}'])
