"""Offline bounds for the higher-throughput upload configuration."""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drive_ingest as ingest


class TransferLimitTests(unittest.TestCase):
    def test_default_project_cap_and_physical_reserve(self):
        args = ingest.parser().parse_args(['plan'])
        self.assertEqual((args.max_local_gb, args.min_free_gb), (23.0, 12.0))
        self.assertEqual((args.workers, args.upload_transfers, args.upload_batch_items, args.ready_items),
                         (6, 3, 12, 24))

    def test_cli_accepts_requested_parallel_configuration(self):
        args = ingest.parser().parse_args(['run', '--workers', '8', '--upload-transfers', '4',
                                           '--upload-batch-items', '12', '--ready-items', '64'])
        self.assertEqual((args.workers, args.upload_transfers, args.upload_batch_items, args.ready_items),
                         (8, 4, 12, 64))

    def test_cli_rejects_out_of_range_transfer_counts(self):
        for value in ('0', '-1', '5', '100', '2.5'):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                ingest.parser().parse_args(['run', '--upload-transfers', value])
            self.assertEqual(error.exception.code, 2)

    def test_direct_batch_api_cannot_exceed_four_transfers(self):
        drive = ingest.Rclone('unused')
        with patch.object(ingest, 'run_tool') as tool:
            for value in (0, -1, 5, 100, 2.5, '4'):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    drive.copy_batch(Path('source'), 'archive:', Path('manifest'), transfers=value)
        tool.assert_not_called()

    def test_all_upload_modes_use_bounded_chunks_and_api_rate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            audio, metadata, manifest = root / 'abcdefghijk.webm', root / 'abcdefghijk.info.json', root / 'files.txt'
            tool = Mock(return_value=SimpleNamespace(returncode=0, stdout='{}'))
            with patch.object(ingest, 'run_tool', tool):
                drive = ingest.Rclone('unused')
                drive.copy(audio, 'archive:channel/Videos/abcdefghijk.webm')
                drive.copy_pair(audio, metadata, 'archive:channel/Videos/abcdefghijk.webm',
                                'archive:channel/Videos/abcdefghijk.info.json')
                drive.copy_batch(root, 'archive:', manifest, transfers=4)
            for expected_transfers, call in zip((1, 2, 4), tool.call_args_list):
                command = call.args[0]
                value = lambda flag: command[command.index(flag) + 1]
                self.assertEqual(value('--transfers'), str(expected_transfers))
                self.assertEqual(value('--drive-chunk-size'), '32M')
                self.assertEqual(value('--tpslimit'), '2')
                self.assertEqual(value('--tpslimit-burst'), '1')
                self.assertEqual(value('--buffer-size'), '1M')
                self.assertIn('--checksum', command)
                self.assertIn('--immutable', command)
            batch = tool.call_args_list[-1].args[0]
            self.assertIn('--files-from-raw', batch)
            self.assertIn('--no-traverse', batch)
            self.assertEqual(batch[batch.index('--checkers') + 1], '2')


if __name__ == '__main__':
    unittest.main()
