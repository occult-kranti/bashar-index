"""Synthetic metadata only: no media, source service, private path or verifier I/O."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from pipeline import qualified_edition_receipts as receipts

FIXTURE = Path(__file__).with_name('fixtures') / 'qualified_edition_receipt.json'


def receipt_fixture():
    return json.loads(FIXTURE.read_bytes())


def reseal(record):
    record['qualification']['payload_sha256'] = receipts.sha(receipts.encoded(record['qualification']['payload']))
    record['provenance']['qualification'] = deepcopy(record['qualification'])
    local = receipts.file_proof(receipts.encoded(record['provenance']))
    record['metadata']['local_proof'] = local
    record['metadata']['remote_proof'].update(bytes=local['bytes'], md5=local['md5'])
    return record


class EditionReceiptTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('Source forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))
        self.record = receipt_fixture()

    def validate(self, record=None):
        return receipts.validate(self.record if record is None else record, remote_base='etdrive:04 Audio')

    def test_canonical_paired_metadata_proof_is_qualified_without_native_or_text(self):
        edition = self.validate()
        self.assertEqual('abcdefghijk', edition.video_id)
        self.assertFalse(edition.native_promotion)
        self.assertFalse(edition.text_or_ASR_coverage)

    def test_detached_actual_file_fingerprints_fail_even_with_resealed_provenance(self):
        for key in ('private_muxed_source_file', 'derived_audio_file'):
            record = deepcopy(self.record)
            record['qualification']['payload']['AAC_preservation'][key] = receipts.file_proof(b'other synthetic file')
            with self.subTest(key=key), self.assertRaises(receipts.ReceiptHold):
                self.validate(reseal(record))

    def test_resealed_weaker_quality_or_language_claim_is_rejected(self):
        for key, value in [('duration_tolerance_seconds', .25), ('spoken_language_verified', True),
                           ('native_canonical_promotion', True), ('GPU_requested', True)]:
            record = deepcopy(self.record)
            record['qualification']['payload']['AAC_preservation'][key] = value
            with self.subTest(key=key), self.assertRaises(receipts.ReceiptHold):
                self.validate(reseal(record))

    def test_observed_body_extent_and_remote_pair_are_required(self):
        record = deepcopy(self.record)
        record['qualification']['payload']['source_http']['received_bytes'] -= 1
        with self.assertRaises(receipts.ReceiptHold): self.validate(reseal(record))
        record = deepcopy(self.record)
        record['metadata']['remote_proof']['md5'] = 'e' * 32
        with self.assertRaises(receipts.ReceiptHold): self.validate(record)
        record = deepcopy(self.record)
        record['audio']['remote_proof']['sha256'] = record['audio']['local_proof']['sha256']
        with self.assertRaises(receipts.ReceiptHold): self.validate(record)

    def test_unpublished_legacy_or_impossible_packet_proofs_contribute_zero(self):
        invalid = []
        for key, value in [('status', 'local_complete'), ('kind', 'youtube_progressive_AAC_packet_preserving_extract')]:
            record = deepcopy(self.record); record[key] = value; invalid.append(record)
        record = deepcopy(self.record)
        for side in ('source_AAC_packets', 'derived_AAC_packets'):
            record['qualification']['payload']['AAC_preservation'][side]['packet_count'] = 1_000_000
        invalid.append(reseal(record))
        result = receipts.covered(invalid + [self.record, deepcopy(self.record)],
                                  targets={'abcdefghijk'}, remote_base='etdrive:04 Audio')
        self.assertEqual({'abcdefghijk'}, result['qualified_youtube_edition_video_ids'])
        self.assertEqual(3, result['rejected_records'])
        self.assertEqual(0, result['native_audio_increment'])
        self.assertEqual(0, result['caption_or_ASR_increment'])


if __name__ == '__main__':
    unittest.main()
