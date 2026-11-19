import gzip
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from pipeline import expand_regular_roster as expand
from pipeline import resolve_channel_intake as intake


class ChannelIntakeTests(unittest.TestCase):
    def setUp(self):
        self.channel = 'UC' + 'a' * 22
        self.url = 'https://www.youtube.com/channel/' + self.channel
        self.meta = {'metadata': {'channelMetadataRenderer': {'externalId': self.channel, 'title':'Demo',
                     'channelUrl': self.url, 'ownerUrls': ['http://www.youtube.com/@Example']}}}
        self.raw = ('var ytInitialData = ' + json.dumps(self.meta) + ';').encode()

    def test_requested_handle_and_id_bind_to_same_publisher_page(self):
        result = intake.channel_identity(self.raw, 'https://www.youtube.com/@example')
        self.assertEqual((result['channel_id'], result['handle']), (self.channel, '@Example'))
        self.assertEqual(intake.channel_identity(self.raw, self.url), result)
        for wrong in ('https://www.youtube.com/@guest', self.url[:-1] + 'b'):
            with self.subTest(wrong=wrong), self.assertRaisesRegex(ValueError, 'disagrees'):
                intake.channel_identity(self.raw, wrong)

    def test_expansion_reuses_original_channel_pages_and_collapses_aliases(self):
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            def group(slug, ident):
                return {'creator': slug, 'channel_id': ident, 'observed_at':'2026-11-19T12:00:00Z',
                        'state':'observed', 'items':[], 'public_items':[], 'observed_items':[],
                        'public_listing_complete':True, 'listing_complete':True,
                        'page_sha256':hashlib.sha256(self.raw).hexdigest()}
            prior_data = {'channels':[group('old','UC'+'b'*22)]}
            prior = {'path':'former-index', 'sha256':'a'*64, 'bytes':100}
            newcomer, alias = group('new', self.channel), group('alias','UC'+'b'*22)
            capture = root/'new'; capture.mkdir()
            (capture/'videos.html.gz').write_bytes(gzip.compress(self.raw))
            source = root/'new-index.json';source.write_text(json.dumps({'channels':[alias, newcomer]}))
            result, added, duplicates = expand.join_listings(prior_data, prior, [source], root)
            self.assertEqual([g['creator'] for g in result['channels']], ['old','new'])
            self.assertEqual(result['listing_sources_by_channel']['old'], prior)
            self.assertEqual((len(added), len(duplicates), duplicates[0]['canonical_creator']), (1,1,'old'))
            self.assertEqual(result['summary']['public_regular_targets'], 0)
            newcomer['public_listing_complete'] = False
            source.write_text(json.dumps({'channels':[newcomer]}))
            with self.assertRaisesRegex(ValueError,'complete public regular'):
                expand.join_listings(prior_data, prior, [source], root)
            newcomer['public_listing_complete'] = True
            source.write_text(json.dumps({'channels':[newcomer]}))
            (capture/'videos.html.gz').write_bytes(gzip.compress(b'changed'))
            with self.assertRaisesRegex(ValueError, 'does not match'):
                expand.join_listings(prior_data, prior, [source], root)


if __name__ == '__main__':
    unittest.main()
