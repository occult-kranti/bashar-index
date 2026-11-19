import base64
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_public_metadata as handoff
from media_metadata import build_metadata


class NativePublicMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.video = 'fGEdTgyu-B0'
        self.channel = 'UC' + 'x' * 22
        self.captured = '2026-11-19T17:25:00Z'
        self.built = '2026-11-19T18:12:00Z'
        self.row = {'video_id': self.video, 'expected_channel_id': self.channel, 'tab': 'videos'}
        self.link = 'https://publisher.example.org/events/2026-05'
        signed = 'https://r1.googlevideo.com/videoplayback?sig=SECRET_TRANSPORT'
        self.public = {'id': self.video, 'channel_id': self.channel, 'title': 'Panel chat',
                       'description': f'Publisher recording {self.link}. Temporary asset {signed}',
                       'chapters': [{'start_time': 0, 'end_time': 580, 'title': 'Opening',
                                     'headers': {'Cookie': 'SECRET_CHAPTER'}}],
                       'timestamp': 1778117332, 'upload_date': '20260507', 'release_date': '20260508',
                       'formats': [{'url': signed, 'http_headers': {'Cookie': 'SECRET_FORMAT'}}],
                       'http_headers': {'Cookie': 'SECRET_SESSION'}, 'url': signed,
                       'subtitles': {'en-US': [{'ext': 'vtt', 'name': 'English', 'url': signed, 'data': 'PRIVATE_TEXT'}]},
                       'automatic_captions': {'en-orig': [{'name': 'English (Original)', 'ext': 'vtt', 'url': signed}],
                                              'live_chat': [{'url': signed}]}}
        self.native = build_metadata({'id': self.video,'channel_id': self.channel,'format_id':'140','language':'en',
                                      'acodec':'aac','url':signed,'http_headers':{'Cookie':'SECRET_NATIVE'}}, self.row, self.built)

    def store(self, info=None):
        return handoff.observe_handoff(self.folder, self.public if info is None else info, video_id=self.video,
                                       channel_id=self.channel, captured_at=self.captured)

    def test_dated_observation_reaches_regular_metadata_fields_and_preserves_audio_selection(self):
        before = deepcopy(self.public)
        ref = self.store()
        replay = self.store()
        self.assertEqual(ref, replay)
        self.assertEqual(len(list(self.folder.iterdir())), 1)
        merged = handoff.merge_capture(self.native, {'public_episode_capture': ref}, self.folder)
        self.assertEqual(merged['captured_at'], self.captured)
        self.assertEqual(merged['public_episode_observation']['native_metadata_built_at'], self.built)
        self.assertEqual(merged['metadata']['chapters'], [{'start_time':0, 'end_time':580, 'title':'Opening'}])
        self.assertIn(self.link, merged['metadata']['description'])
        self.assertEqual(merged['metadata']['upload_date'], '20260507')
        self.assertEqual(merged['metadata']['release_date'], '20260508')
        self.assertEqual(merged['metadata']['timestamp'], 1778117332)
        self.assertEqual(merged['metadata']['format_id'], '140')
        self.assertEqual(merged['queue'], self.row)
        self.assertEqual(merged['languages'], {'manual_subtitles':['en-US'],'automatic_captions':['en-orig'],'audio':'en'})
        self.assertEqual(merged['metadata']['automatic_captions']['en-orig'][0]['name'],'English (Original)')
        self.assertFalse(merged['sanitization']['caption_text_fetched'])
        self.assertFalse(any(t in json.dumps(merged) for t in ('SECRET','googlevideo.com','Cookie','PRIVATE_TEXT')))
        self.assertNotIn('chapters', self.native['metadata'])
        self.assertEqual(self.public, before)

    def test_older_handoff_unmodified_and_optional_local_write_failure_explicit(self):
        self.assertIs(handoff.merge_capture(self.native, {}, self.folder), self.native)
        with mock.patch.object(handoff, 'mkstemp', side_effect=OSError('local fixture')):
            ref = self.store()
        merged = handoff.merge_capture(self.native, {'public_episode_capture':ref}, self.folder)
        self.assertEqual(merged['public_episode_observation'], {'status':'unavailable','reason':'local_write_failed'})
        self.assertNotIn('chapters', merged['metadata'])

    def test_content_channel_and_handoff_filename_are_bound(self):
        ref = self.store()
        for changed in ({'channel_id':'UC'+'y'*22},{'filename':'../elsewhere.json'},{'captured_at':self.built}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                handoff.merge_capture(self.native, {'public_episode_capture':{**ref,**changed}},self.folder)
        path = self.folder / ref['filename']
        original = path.read_bytes()
        path.write_bytes(original.replace(b'Panel chat', b'Panel xxxx'))
        with self.assertRaises(ValueError):
            handoff.merge_capture(self.native, {'public_episode_capture':ref},self.folder)
        with self.assertRaises(ValueError):
            self.store({**self.public, 'id':'abcdefghijk'})

    def test_large_research_snapshot_is_losslessly_archived_inside_the_bounded_sidecar(self):
        self.public['chapters'] = [{'start_time':i, 'title':f'Chapter {i} with a sufficiently long name'} for i in range(4800)]
        ref = self.store()
        merged = handoff.merge_capture(self.native, {'public_episode_capture': ref}, self.folder)
        proof = merged['public_episode_observation']
        body = gzip.decompress(base64.b64decode(proof['full_snapshot_gzip_base64']))
        self.assertEqual(hashlib.sha256(body).hexdigest(), ref['sha256'])
        self.assertEqual(len(json.loads(body)['metadata']['chapters']),4800)
        self.assertLess(len(json.dumps(merged)), 256 * 1024)


if __name__ == '__main__':
    unittest.main()
