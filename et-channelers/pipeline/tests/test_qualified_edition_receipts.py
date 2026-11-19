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

def profile_receipt(record, profile='HE-AAC'):
    record = deepcopy(record)
    qualification = record['qualification']
    preservation = qualification['payload']['AAC_preservation']
    component = {'sha256': receipts.PROFILE_COMPONENT_SHA, 'bytes': receipts.PROFILE_COMPONENT_BYTES}
    base = {'sha256': receipts.VERIFIER_SHA, 'bytes': 10864}
    qualification.update(verifier_artifact=component, base_verifier_artifact=base)
    preservation.update(quality_contract=receipts.PROFILE_CONTRACT,
                        quality_component_artifact=deepcopy(component), base_verifier_artifact=deepcopy(base))
    for side in ('source_audio', 'derived_audio'):
        preservation[side]['profile'] = profile
    return reseal(record)

def streaming_receipt(record):
    record = profile_receipt(record)
    qualification = record['qualification']
    preservation = qualification['payload']['AAC_preservation']
    component = {'sha256': receipts.STREAM_COMPONENT_SHA, 'bytes': receipts.STREAM_COMPONENT_BYTES}
    qualification['verifier_artifact'] = component
    preservation.update(
        quality_contract=receipts.STREAM_CONTRACT, quality_component_artifact=deepcopy(component),
        base_verifier_role='digest_compatibility_reference_only', base_verifier_execution_claimed=False,
        packet_summary_mode='incremental_ffprobe_JSON_one_packet_buffer_v1',
        packet_count_bound_basis='positive_packet_payload_sizes_sum_not_exceeding_actual_file_bytes',
        maximum_source_bytes=2_000_000_000, maximum_derived_bytes=2_000_000_000,
        maximum_packet_record_bytes=65536, maximum_stderr_bytes=1_000_000,
        fixed_packet_count_or_duration_cutoff=False)
    return reseal(record)


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

    def test_reviewed_profile_component_accepts_preserved_HE_AAC_and_LC(self):
        for profile in ('HE-AAC', 'LC'):
            with self.subTest(profile=profile):
                edition = self.validate(profile_receipt(self.record, profile))
                self.assertFalse(edition.native_promotion)
                self.assertFalse(edition.text_or_ASR_coverage)

    def test_HE_AAC_requires_new_component_base_pin_and_matching_contract(self):
        record = profile_receipt(self.record)
        cases = []
        old = deepcopy(record)
        old['qualification']['verifier_artifact'] = {'sha256': receipts.VERIFIER_SHA, 'bytes': 10864}
        cases.append(old)
        legacy_bound = deepcopy(old)
        legacy_bound['qualification']['payload']['AAC_preservation']['quality_contract'] = receipts.LEGACY_CONTRACT
        cases.append(legacy_bound)
        unknown = deepcopy(record)
        unknown['qualification']['verifier_artifact']['sha256'] = 'a' * 64
        cases.append(unknown)
        base = deepcopy(record)
        base['qualification']['base_verifier_artifact']['sha256'] = 'b' * 64
        cases.append(base)
        nested = deepcopy(record)
        nested['qualification']['payload']['AAC_preservation']['quality_component_artifact']['bytes'] += 1
        cases.append(nested)
        legacy = deepcopy(record)
        legacy['qualification']['payload']['AAC_preservation']['quality_contract'] = receipts.LEGACY_CONTRACT
        cases.append(legacy)
        for i, invalid in enumerate(cases):
            with self.subTest(case=i), self.assertRaises(receipts.ReceiptHold):
                self.validate(reseal(invalid))

    def test_profile_extension_retains_packet_configuration_and_identity_guards(self):
        record = profile_receipt(self.record)
        mutations = [
            ('derived_audio', 'profile', 'LC'),
            ('derived_audio', 'extradata_sha256', 'e' * 64),
            ('derived_AAC_packets', 'packet_sequence_sha256', 'f' * 64),
            ('derived_AAC_packets', 'skip_samples', 999),
        ]
        for side, key, value in mutations:
            invalid = deepcopy(record)
            invalid['qualification']['payload']['AAC_preservation'][side][key] = value
            with self.subTest(key=key), self.assertRaises(receipts.ReceiptHold):
                self.validate(reseal(invalid))
        with self.assertRaises(receipts.ReceiptHold):
            self.validate(profile_receipt(self.record, 'HE-AACv2'))

    def test_profile_component_rejects_source_or_output_above_its_32MB_contract(self):
        for field in ('source_file', 'derived_audio_file'):
            record = profile_receipt(self.record)
            qualification = record['qualification']
            payload = qualification['payload']
            payload[field]['bytes'] = 32_000_001
            qualification['payload_sha256'] = receipts.sha(receipts.encoded(payload))
            with self.subTest(field=field), self.assertRaisesRegex(receipts.ReceiptHold, 'file_fingerprint'):
                receipts.qualification(qualification, record['video_id'], payload['derived_audio_file'],
                                       payload['source_file']['sha256'])

    def test_streaming_component_has_separate_artifact_and_reference_role(self):
        record = streaming_receipt(self.record)
        self.assertFalse(self.validate(record).native_promotion)
        for key, value in [('base_verifier_execution_claimed', True),
                           ('base_verifier_role', 'executed'),
                           ('fixed_packet_count_or_duration_cutoff', True),
                           ('maximum_packet_record_bytes', 1_000_000)]:
            invalid = deepcopy(record)
            invalid['qualification']['payload']['AAC_preservation'][key] = value
            with self.subTest(key=key), self.assertRaises(receipts.ReceiptHold):
                self.validate(reseal(invalid))
        invalid = deepcopy(record)
        invalid['qualification']['verifier_artifact'] = {
            'sha256': receipts.PROFILE_COMPONENT_SHA, 'bytes': receipts.PROFILE_COMPONENT_BYTES}
        with self.assertRaises(receipts.ReceiptHold):
            self.validate(reseal(invalid))

    def test_streaming_packet_count_uses_payload_bytes_and_keeps_file_limits(self):
        record = streaming_receipt(self.record)
        qualification = record['qualification']
        payload = qualification['payload']
        preservation = payload['AAC_preservation']
        payload['source_file']['bytes'] = 300_000_000
        payload['derived_audio_file']['bytes'] = 100_000_000
        preservation['private_muxed_source_file'] = deepcopy(payload['source_file'])
        preservation['derived_audio_file'] = deepcopy(payload['derived_audio_file'])
        payload['selection'].update(filesize=300_000_000, duration_seconds=9288.)
        for key in ('content_length', 'received_bytes', 'written_bytes', 'exact_on_write_limit'):
            payload['source_http'][key] = 300_000_000
        for side in ('source_audio', 'derived_audio'):
            preservation[side]['duration_seconds'] = 9288.
        for side in ('source_AAC_packets', 'derived_AAC_packets'):
            preservation[side].update(packet_count=200_001, packet_payload_bytes=40_000_000,
                                      packet_duration_sum_seconds=9288.)
        def validate_payload():
            qualification['payload_sha256'] = receipts.sha(receipts.encoded(payload))
            return receipts.qualification(qualification, record['video_id'], payload['derived_audio_file'],
                                          payload['source_file']['sha256'])
        self.assertEqual(200_001, validate_payload()['AAC_preservation']['source_AAC_packets']['packet_count'])
        record['audio']['local_proof'] = deepcopy(payload['derived_audio_file'])
        record['audio']['remote_proof'].update(bytes=100_000_000,
                                              md5=payload['derived_audio_file']['md5'])
        record['provenance']['audio'] = deepcopy(payload['derived_audio_file'])
        self.assertFalse(self.validate(reseal(record)).native_promotion)
        for side in ('source_AAC_packets', 'derived_AAC_packets'):
            preservation[side]['packet_count'] = 40_000_001
        with self.assertRaisesRegex(receipts.ReceiptHold, 'positive_payload_packet_count_bound'):
            validate_payload()
        for side in ('source_AAC_packets', 'derived_AAC_packets'):
            preservation[side]['packet_count'] = 200_001
        preservation['maximum_derived_bytes'] = 99_999_999
        with self.assertRaisesRegex(receipts.ReceiptHold, 'file_fingerprint'):
            validate_payload()

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
