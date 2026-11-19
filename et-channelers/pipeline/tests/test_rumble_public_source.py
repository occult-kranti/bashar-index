"""Synthetic publisher HTML with no account, transport token or captured media."""
import json
import unittest

from pipeline.rumble_public_source import published_descriptors, SourceError


ACCOUNT = 'https://rumble.com/c/Example'
WATCH = 'https://rumble.com/v123abc-example-episode.html'
CDN = 'https://hugh.cdn.rumble.cloud'


def source_fixture(audio_bytes=200, public=True, gate=False):
    title = 'An Example & A Question'
    date = '2026-01-02T10:00:00+00:00'
    listing = {'items': [{'object_type': 'video', 'permalink_id': 'v123abc', 'url': WATCH,
                          'by': {'url': ACCOUNT}, 'title': title, 'upload_date': date, 'duration': 16,
                          'visibility': 'public', 'downloadable': public, 'is_processing': False,
                          'is_age_restricted': False, 'live': False, 'availability': None}]}
    episode = {'@type': 'VideoObject', 'name': title, 'uploadDate': date, 'duration': 'PT0H0M16S',
               'embedUrl': 'https://rumble.com/embed/v45ef/'}
    player = {'fps': 30, 'title': 'An Example &amp;  A Question', 'pubDate': date, 'duration': 16,
              'live': 0, 'author': {'url': ACCOUNT}, 'sys': {'msg': None},
              'ua': {'audio': {'192': {'url': CDN + '/audio.aac', 'meta': {'w': 0, 'h': 0, 'bitrate': 192, 'size': audio_bytes}}},
                     'hls': {'url': 'https://example.invalid/video.m3u8'}},
              'cc': {'en-auto': {'language': 'English (auto)', 'path': CDN + '/auto.vtt'},
                     'en-GB': {'language': 'British English', 'path': CDN + '/published.vtt'},
                     'en-US': {'language': 'English (translated)', 'path': CDN + '/translation.vtt'},
                     'es': {'language': 'Spanish', 'path': CDN + '/es.vtt'}},
              'viewer_id': 'synthetic-irrelevant-field'}
    def script(kind, value):
        return '<script type="' + kind + '">' + json.dumps(value) + '</script>'
    page = (script('application/json', {'show_premium_exclusive_gate': gate}) +
            '<div class="js-premium-player-lock hidden">Premium only</div>' +
            script('application/ld+json', [{'@type': 'WebPage'}, episode]))
    embed = '<script>p.f["v45ef"]=' + json.dumps(player)[:-1] + ',loaded:localFunction()};</script>'
    return [s.encode() for s in (script('application/json', listing), page, embed)]


class PublishedSourceTests(unittest.TestCase):
    def test_publishes_only_audio_and_eligible_english_tracks(self):
        edition = published_descriptors(*source_fixture(), ACCOUNT, WATCH)
        self.assertEqual(edition['watch_page_id'], 'v123abc')
        self.assertEqual(edition['declared_embed_id'], 'v45ef')
        self.assertEqual(edition['duration_seconds'], 16)
        self.assertEqual(edition['audio']['192']['bytes'], 200)
        self.assertEqual({k: v['kind'] for k, v in edition['captions'].items()},
                         {'en-auto': 'automatic_original', 'en-GB': 'publisher_provided_unspecified'})
        self.assertEqual(set(edition['source_sha256']), {'listing', 'watch', 'embed'})
        encoded = json.dumps(edition)
        self.assertNotIn('viewer_id', encoded)
        self.assertNotIn('m3u8', encoded)

    def test_publication_and_visibility_are_required(self):
        for parts in (source_fixture(public=False), source_fixture(gate=True)):
            with self.assertRaises(SourceError):
                published_descriptors(*parts, ACCOUNT, WATCH)
        listing, watch, embed = source_fixture()
        with self.assertRaises(SourceError):
            published_descriptors(listing, watch.replace(b'lock hidden', b'lock'), embed, ACCOUNT, WATCH)

    def test_mismatched_channel_page_embed_and_remote_host(self):
        listing, watch, embed = source_fixture()
        for args in ((listing, watch, embed, ACCOUNT + '2', WATCH),
                     (listing, watch, embed, ACCOUNT, WATCH.replace('v123abc', 'v123abd')),
                     (listing, watch.replace(b'PT0H0M16S', b'PT0H1M16S'), embed, ACCOUNT, WATCH),
                     (listing, watch, embed.replace(b'p.f["v45ef"]=', b'p.f["v45ea"]='), ACCOUNT, WATCH),
                     (listing, watch, embed.replace(CDN.encode(), b'https://unrelated.example'), ACCOUNT, WATCH)):
            with self.subTest(args=args[-2:]), self.assertRaises(SourceError):
                published_descriptors(*args)
