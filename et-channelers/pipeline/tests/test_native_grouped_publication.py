"""A partial remote copy must preserve each unpublished native Sink pair."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import RLock
import unittest
from unittest.mock import patch

from pipeline import drive_ingest as storage, native_audio_sink as native


class PartialDrive:
    def __init__(self, missing):
        self.missing = missing
        self.objects = {}
        self.copies = []
        self.readbacks = []

    def copy_batch(self, root, remote, manifest, transfers):
        paths = manifest.read_text(encoding='utf8').splitlines()
        self.copies.append((len(paths), transfers))
        for path in paths:
            if path == self.missing:
                continue
            body = (root/path).read_bytes()
            self.objects[path] = {'ID':'fixture-'+path, 'Size':len(body),
                                  'Hashes':{'md5':hashlib.md5(body).hexdigest()}, 'IsDir':False}
        raise storage.IngestError('drive_network', 'Simulated interrupted transfer')

    def stat_batch(self, remote, paths, manifest, *, allow_missing):
        self.readbacks.append(paths)
        return dict(self.objects)


class GroupedNativePublication(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root/'sync').mkdir()
        self.c = native.Coordinator.__new__(native.Coordinator)
        self.c.root, self.c.spool, self.c.core, self.c.lock = self.root, self.root/'spool', storage, RLock()
        self.c.publishing, self.c.live = set(), {}
        self.c.remote = 'example:archive'
        self.c.guard = lambda: None

    def sink(self, video):
        sink = native.Sink(self.c, video)
        sink.folder.mkdir(parents=True)
        row = {'video_id':video,'channel_dir':'interviews','tab':'videos','listing_rank':0}
        record = {**row,'queue_row':row,'status':'metadata_ready'}
        for ext, payload in [('webm',b'validated fixture audio '+video.encode()),('info.json',json.dumps(row).encode())]:
            path = sink.folder/(video+'.'+ext)
            path.write_bytes(payload)
            obj = {**storage.hash_file(path),'path':path.relative_to(self.root).as_posix(),
                   'remote':storage.remote_path(self.c.remote,row,ext)}
            if ext == 'webm':
                record.update(obj)
            else:
                record['metadata'] = obj
        native.atomic(sink.folder/'state.json',{'state':'local_validated','video_id':video,'queue_row':row,'record':record})
        return sink,record

    def test_only_exact_drive_pairs_have_a_receipt_before_cleanup(self):
        first, ready = self.sink('example0001')
        second, incomplete = self.sink('example0002')
        missing = storage.remote_relative(self.c.remote,incomplete['metadata']['remote'])
        remote = PartialDrive(missing)
        prior = storage.journal
        proof_before_delete = []
        def journal(path,row):
            if row['status']=='verified':
                proof_before_delete.append((row['video_id'],(self.root/row['path']).is_file(),
                                           (self.root/row['metadata']['path']).is_file()))
            return prior(path,row)
        with patch.object(storage,'journal',journal):
            outcomes=self.c.publish_ready([first,second],remote,publisher_headroom_bytes=1_000_000)
        self.assertEqual([(r.key,r.state) for r in outcomes],[('example0001','verified'),('example0002','retained')])
        self.assertEqual(proof_before_delete,[('example0001',True,True)])
        self.assertEqual(remote.copies,[(4,3)])
        self.assertEqual(len(remote.readbacks),1)
        self.assertFalse((self.root/ready['path']).exists())
        self.assertFalse((self.root/ready['metadata']['path']).exists())
        self.assertTrue((self.root/incomplete['path']).is_file())
        self.assertTrue((self.root/incomplete['metadata']['path']).is_file())
        self.assertEqual(second.state()['state'],'local_validated')
        self.assertEqual(outcomes[0].receipt['status'],'deleted')
        self.assertNotEqual(outcomes[0].receipt['drive_id'],outcomes[0].receipt['metadata']['drive_id'])
        self.assertIsNone(outcomes[1].receipt)


if __name__=='__main__':
    unittest.main()
