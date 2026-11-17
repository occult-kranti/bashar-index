"""Exact object preservation and interrupted-move recovery without a network."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from pipeline import drive_ingest as storage
from pipeline import native_metadata_snapshot as snapshot


class Drive:
    RETRY_FLAGS = []

    def __init__(self, remote, old):
        self.objects = {remote: [copy.deepcopy(old)]}
        self.moves = []
        self.lose_ack = False
        self.corrupt_move = False

    def execute(self, args, timeout, operation):
        if args[0] == 'lsjson':
            name = args[args.index('--include') + 1].lstrip('/')
            rows = self.objects.get(args[1] + '/' + name, [])
            return SimpleNamespace(stdout=json.dumps([dict(r, Name=name, Path=name) for r in rows]))
        assert args[0] == 'moveto' and '--immutable' in args
        source, destination = args[1:3]
        assert destination not in self.objects
        self.moves.append((source, destination))
        self.objects[destination] = self.objects.pop(source)
        if self.corrupt_move:
            self.objects[destination][0]['ID'] = 'unexpected-object'
        if self.lose_ack:
            self.lose_ack = False
            raise storage.IngestError('drive_network', 'lost response after move')
        return SimpleNamespace(stdout='')


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        folder = self.root / 'audio/fixture'
        folder.mkdir(parents=True)
        audio, meta = folder / 'aaaaaaaaaaa.m4a', folder / 'aaaaaaaaaaa.info.json'
        audio.write_bytes(b'new native audio')
        meta.write_bytes(b'new metadata')
        self.record = {'video_id': 'aaaaaaaaaaa', 'channel_dir': 'fixture', 'tab': 'videos',
                       'path': audio.relative_to(self.root).as_posix(),
                       'remote': 'fixture:Audio/fixture/Videos/aaaaaaaaaaa.m4a', **storage.hash_file(audio),
                       'metadata': {'path': meta.relative_to(self.root).as_posix(),
                                    'remote': 'fixture:Audio/fixture/Videos/aaaaaaaaaaa.info.json', **storage.hash_file(meta)}}
        self.audio = {'ID': 'audio-object', 'Size': self.record['bytes'], 'Hashes': {'MD5': self.record['md5']}}
        self.old = {'ID': 'old-metadata-object', 'Size': 777, 'Hashes': {'md5': 'a' * 32}}
        self.remote = self.record['metadata']['remote']
        self.target = 'fixture:Audio/fixture/Videos/aaaaaaaaaaa/MetadataSnapshots/' + 'a' * 32 + '.info.json'
        self.drive = Drive(self.remote, self.old)

    def run_helper(self, metadata='original'):
        return snapshot.preserve_conflicting_metadata(self.root, self.record, self.drive,
            observed_audio=self.audio, observed_metadata=self.old if metadata == 'original' else metadata)

    def test_preserves_exact_id_before_new_metadata_is_allowed(self):
        result = self.run_helper()
        self.assertEqual(result['preserved']['drive_id'], self.old['ID'])
        self.assertEqual(self.drive.moves, [(self.remote, self.target)])
        journal = storage.read_jsonl(self.root / 'sync/native_metadata_lineage_manifest.jsonl')
        self.assertEqual([r['status'] for r in journal], ['move_intent', 'old_metadata_preserved'])
        self.assertTrue((self.root / self.record['path']).exists())
        self.assertTrue((self.root / self.record['metadata']['path']).exists())

    def test_lost_move_ack_recovers_same_object_without_second_move(self):
        self.drive.lose_ack = True
        with self.assertRaisesRegex(storage.IngestError, 'lost response'):
            self.run_helper()
        result = self.run_helper(metadata=None)
        self.assertEqual(result['preserved']['drive_id'], self.old['ID'])
        self.assertEqual(len(self.drive.moves), 1)

    def test_existing_snapshot_without_durable_intent_holds(self):
        self.drive.objects[self.target] = [copy.deepcopy(self.old)]
        with self.assertRaises(storage.IngestError):
            self.run_helper()
        self.assertEqual(self.drive.moves, [])

    def test_duplicate_canonical_names_and_duplicate_snapshot_names_hold(self):
        for duplicate_path in (self.remote, self.target):
            with self.subTest(path=duplicate_path):
                self.drive = Drive(self.remote, self.old)
                self.drive.objects[duplicate_path] = [copy.deepcopy(self.old), dict(self.old, ID='duplicate')]
                with self.assertRaises(storage.IngestError):
                    self.run_helper()
                self.assertEqual(self.drive.moves, [])

    def test_missing_changed_or_same_identity_audio_never_moves_metadata(self):
        for bad in (None, dict(self.audio, Size=1), dict(self.audio, ID=self.old['ID'])):
            with self.subTest(proof=bad):
                self.audio = bad
                with self.assertRaises(storage.IngestError):
                    self.run_helper()
                self.assertEqual(self.drive.moves, [])
            self.audio = {'ID': 'audio-object', 'Size': self.record['bytes'], 'Hashes': {'MD5': self.record['md5']}}

    def test_changed_local_pair_or_cross_item_remote_holds(self):
        original = copy.deepcopy(self.record)
        self.record['metadata']['remote'] = self.remote.replace('aaaaaaaaaaa', 'bbbbbbbbbbb')
        with self.assertRaises(storage.IngestError):
            self.run_helper()
        self.record = original
        (self.root / self.record['path']).write_bytes(b'changed')
        with self.assertRaises(storage.IngestError):
            self.run_helper()
        self.assertEqual(self.drive.moves, [])

    def test_wrong_postmove_identity_never_records_preserved(self):
        self.drive.corrupt_move = True
        with self.assertRaises(storage.IngestError):
            self.run_helper()
        state = storage.load_state(self.root / 'sync/native_metadata_lineage_manifest.jsonl')
        self.assertEqual(state[self.record['video_id']]['status'], 'move_intent')

    def test_verified_caption_dependency_and_missing_old_proof_hold(self):
        storage.journal(self.root / 'sync/drive_caption_manifest.jsonl', {
            'video_id': self.record['video_id'], 'status': 'pending',
            'tracks': [{'status': 'verified', 'bundle': {'drive_id': 'saved-caption'}}]})
        with self.assertRaises(storage.IngestError):
            self.run_helper()
        (self.root / 'sync/drive_caption_manifest.jsonl').unlink()
        self.old.pop('ID')
        with self.assertRaises(storage.IngestError):
            self.run_helper()
        self.assertEqual(self.drive.moves, [])


if __name__ == '__main__':
    unittest.main()
