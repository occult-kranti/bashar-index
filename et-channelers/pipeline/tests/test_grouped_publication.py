from collections import deque
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from pipeline import drive_ingest as storage
from pipeline import grouped_publication as grouped


class DriveFixture:
    def __init__(self, delay=0):
        self.delay = delay
        self.objects = {}
        self.commands = []
        self.transferred = []
        self.fail_after = None
        self.error = None
        self.before_stat = None

    def copy_batch(self, root, remote, manifest, transfers=1):
        self.commands.append(('copy', transfers))
        time.sleep(self.delay)
        for index, relative in enumerate(manifest.read_text(encoding='utf-8').splitlines()):
            if self.fail_after == index:
                raise storage.IngestError(self.error, 'simulated copy termination')
            data = (root / relative).read_bytes()
            if relative not in self.objects:
                self.transferred.append(relative)
                self.objects[relative] = {'ID':hashlib.sha256(relative.encode()).hexdigest(), 'Size':len(data),
                                          'Hashes':{'md5':hashlib.md5(data).hexdigest()}}

    def stat_batch(self, remote, paths, manifest, *, allow_missing):
        self.commands.append(('stat', len(paths)))
        time.sleep(self.delay)
        if self.before_stat:
            self.before_stat(self)
        return {p:self.objects[p] for p in paths if p in self.objects}


class GroupedPublicationTests(unittest.TestCase):
    def setUp(self):
        self.context = TemporaryDirectory()
        self.addCleanup(self.context.cleanup)
        self.root = Path(self.context.name)
        self.files = self.root/'files'
        self.files.mkdir()
        self.receipts = []
        self.drive = DriveFixture()

    def pairs(self, count, *, prefix='row'):
        pairs = []
        for index in range(count):
            key = f'{prefix}{index}'
            folder = self.files/key
            folder.mkdir()
            objects = []
            for name in ('audio.m4a','metadata.json'):
                path = folder/name
                path.write_bytes((key+name).encode()*64)
                objects.append(grouped.StagedObject(key+'/'+name, storage.hash_file(path), storage.fingerprint(path)))
            def commit(observed, key=key, objects=objects):
                self.assertEqual(set(observed), {'audio','metadata'})
                receipt = {'key':key,'drive_ids':[observed[k]['ID'] for k in ('audio','metadata')]}
                (self.root/(key+'.receipt')).write_text(repr(receipt), encoding='ascii')
                self.receipts.append(receipt)
                for obj in objects:
                    (self.files/obj.relative).unlink()
                return receipt
            pairs.append(grouped.StagedPair(key, *objects, commit))
        return pairs

    def publish(self, pairs):
        return grouped.publish_staged_pairs(pairs, files_root=self.files, control_root=self.root, remote='fixture:',
                                            drive=self.drive, guard=lambda:None)

    def test_six_pairs_have_one_transfer_one_read_and_six_independent_receipts(self):
        result = self.publish(self.pairs(6))
        self.assertEqual([r.state for r in result], ['verified']*6)
        self.assertEqual(self.drive.commands, [('copy',3),('stat',12)])
        self.assertEqual(len(self.receipts), 6)

    def test_partial_copy_reuses_existing_objects_and_retains_incomplete_pairs(self):
        pairs = self.pairs(3)
        self.drive.error, self.drive.fail_after = 'drive_network', 3
        first = self.publish(pairs)
        self.assertEqual([r.state for r in first], ['verified','retained','retained'])
        self.assertFalse((self.files/pairs[0].audio.relative).exists())
        for pair in pairs[1:]:
            self.assertTrue((self.files/pair.audio.relative).exists())
            self.assertTrue((self.files/pair.metadata.relative).exists())
        self.drive.fail_after = None
        self.assertEqual([r.state for r in self.publish(pairs[1:])], ['verified']*2)
        self.assertEqual(len(self.drive.transferred),6)
        self.assertEqual(len(set(self.drive.transferred)),6)

    def test_missing_or_wrong_hash_holds_only_its_own_pair(self):
        pairs = self.pairs(3)
        def mismatch(drive):
            drive.objects.pop(pairs[1].metadata.relative)
            drive.objects[pairs[2].audio.relative]['Hashes']={'md5':'0'*32}
        self.drive.before_stat = mismatch
        result = self.publish(pairs)
        self.assertEqual([r.state for r in result], ['verified','retained','retained'])
        self.assertEqual([r.reason for r in result], [None,'drive_missing','drive_verify'])

    def test_quota_halts_readback_and_keeps_all_staged_files(self):
        pairs = self.pairs(3)
        self.drive.error, self.drive.fail_after = 'drive_rate_limited', 2
        result = self.publish(pairs)
        self.assertEqual([r.reason for r in result], ['drive_rate_limited']*3)
        self.assertEqual(self.drive.commands, [('copy',3)])
        self.assertEqual(len(self.receipts),0)
        self.assertTrue(all((self.files/p.audio.relative).exists() for p in pairs))

    def test_duplicate_remote_identity_cannot_credit_any_pair(self):
        pair, = self.pairs(1)
        self.drive.before_stat=lambda drive:drive.objects[pair.audio.relative].update(ID=drive.objects[pair.metadata.relative]['ID'])
        self.assertEqual(self.publish([pair])[0].reason,'drive_verify')
        self.assertEqual(self.receipts,[])

    def test_trusted_local_identity_is_rechecked_before_cleanup(self):
        pairs = self.pairs(2)
        self.drive.before_stat=lambda _: (self.files/pairs[0].audio.relative).write_bytes(b'changed')
        self.assertEqual([r.state for r in self.publish(pairs)], ['retained','verified'])
        self.assertTrue((self.files/pairs[0].metadata.relative).exists())

    def test_opportunistic_flush_never_waits_for_unready_work(self):
        ready=deque(range(7))
        self.assertEqual(grouped.drain_ready(ready,lambda items:items,lambda item:item),list(range(6)))
        self.assertEqual(grouped.drain_ready(ready,lambda items:self.fail(),lambda item:item),[6])
        self.assertEqual(grouped.drain_ready(ready,lambda items:self.fail(),lambda item:self.fail()),[])

    def test_slow_mock_drive_measures_serial_and_grouped_cost(self):
        self.drive.delay=.02
        serial = self.pairs(6, prefix='serial')
        start=time.perf_counter()
        for pair in serial:
            self.assertEqual(self.publish([pair])[0].state,'verified')
        serial_elapsed=time.perf_counter()-start
        serial_calls=len(self.drive.commands)
        self.drive.commands.clear()
        batch=self.pairs(6, prefix='batch')
        start=time.perf_counter()
        self.assertTrue(all(r.state=='verified' for r in self.publish(batch)))
        grouped_elapsed=time.perf_counter()-start
        self.assertEqual((serial_calls,len(self.drive.commands)),(12,2))
        print(f'6 staged pairs, 20ms per mock Drive operation: serial {serial_elapsed:.3f}s/{serial_calls} calls, grouped {grouped_elapsed:.3f}s/{len(self.drive.commands)} calls')
