import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collect_channel_formats import card_id, observe, parse_tab


CHANNEL = 'UC' + 'a' * 22
VIDEO = 'a' * 11
OTHER = 'b' * 11


def markup(tab='shorts', *, extra_selection=False):
    grid = [{'richItemRenderer': {'content': {'shortsLockupViewModel': {
        'onTap': {'innertubeCommand': {'reelWatchEndpoint': {'videoId': VIDEO}}}}}}},
        {'richSectionRenderer': {'contents': [{'videoRenderer': {'videoId': OTHER}}]}}]
    tabs = [{'tabRenderer': {'selected': name == tab or extra_selection,
                             'endpoint': {'commandMetadata': {'webCommandMetadata': {'url': '/@creator/' + name}}},
                             'content': {'richGridRenderer': {'contents': grid}}}} for name in ('videos', 'shorts')]
    document = {'metadata': {'channelMetadataRenderer': {'externalId': CHANNEL}},
                'contents': {'twoColumnBrowseResultsRenderer': {'tabs': tabs}},
                'sidebar': {'videoRenderer': {'videoId': OTHER}}}
    return ('<script>var ytInitialData = ' + json.dumps(document) + ';</script>').encode()


class ChannelFormats(unittest.TestCase):
    def test_fetch_keeps_the_configured_physical_disk_reserve(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('collect_channel_formats.shutil.disk_usage', return_value=Mock(free=11_999_999_999)):
                with self.assertRaisesRegex(ValueError, 'free disk space'):
                    observe(Path(tmp), 'creator', CHANNEL, 'videos', Mock(), Mock())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_only_primary_tab_cards_can_supply_a_format(self):
        result = parse_tab(markup(), CHANNEL, 'shorts')
        self.assertEqual(result['membership'], {VIDEO: 0})
        alternate = markup().replace(b'var ytInitialData = ', b'window["ytInitialData"] = ')
        self.assertEqual(parse_tab(alternate, CHANNEL, 'shorts')['membership'], {VIDEO: 0})
        self.assertEqual(result['state'], 'primary_grid_observed')
        self.assertEqual(parse_tab(markup(), CHANNEL, 'streams')['state'], 'tab_absent')
        self.assertEqual(parse_tab(markup(), CHANNEL, 'videos')['state'], 'selected_tab_mismatch')
        self.assertEqual(parse_tab(markup(extra_selection=True), CHANNEL, 'shorts')['state'], 'selected_tab_mismatch')
        with self.assertRaises(ValueError):
            parse_tab(markup(), 'UC' + 'b' * 22, 'shorts')

    def test_lockup_rejects_mismatched_endpoint_and_nonvideo_content(self):
        lockup = {'contentId': VIDEO, 'contentType': 'LOCKUP_CONTENT_TYPE_VIDEO', 'rendererContext': {
            'commandContext': {'onTap': {'innertubeCommand': {'watchEndpoint': {'videoId': OTHER}}}}}}
        self.assertIsNone(card_id({'lockupViewModel': lockup}))
        lockup['rendererContext']['commandContext']['onTap']['innertubeCommand']['watchEndpoint']['videoId'] = VIDEO
        self.assertEqual(card_id({'lockupViewModel': lockup}), VIDEO)
        lockup['contentType'] = 'LOCKUP_CONTENT_TYPE_PLAYLIST'
        self.assertIsNone(card_id({'lockupViewModel': lockup}))

    def test_offline_capture_restarts_without_a_network_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(observe(root, 'creator', CHANNEL, 'shorts', None, None)['state'], 'uncached')
            (root / 'shorts.html.gz').write_bytes(gzip.compress(markup()))
            once = observe(root, 'creator', CHANNEL, 'shorts', None, None)
            self.assertEqual(once['membership'], {VIDEO: 0})
            self.assertEqual(once, observe(root, 'creator', CHANNEL, 'shorts', None, None))
            with self.assertRaises(ValueError):
                observe(root, 'unrelated', CHANNEL, 'shorts', None, None)
