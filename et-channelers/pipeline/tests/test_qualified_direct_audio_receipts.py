"""Synthetic receipt mutation tests. No Source, Drive, media or filesystem."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from pipeline import qualified_direct_audio_receipts as d
from pipeline.qualified_edition_receipts import FLAGS

REMOTE = 'testdrive:Audio'


def seal(record):
    q = record['qualification']; q['payload_sha256'] = d.sha(d.encoded(q['payload']))
    provenance = {k: deepcopy(record[k]) for k in ('schema_version', 'kind', 'video_id', 'channel_dir',
        'tab', 'variant_id', 'source_format_id', *FLAGS, 'translation_status', 'native_quality_state')}
    provenance.update(audio=deepcopy(record['audio']['local_proof']), qualification=deepcopy(q))
    record['provenance'] = provenance
    record['metadata']['local_proof'] = d.file_proof(d.encoded(provenance))
    parent = f"{record['channel_dir']}/AudioEditions/{record['video_id']}/{record['variant_id']}"
    for name, leaf in (('audio', 'audio.m4a'), ('metadata', 'provenance.json')):
        local = record[name]['local_proof']
        record[name]['remote_proof'] = {'bytes': local['bytes'], 'md5': local['md5'],
            'drive_id': 'fixture-' + name, 'relative_path': parent + '/' + leaf,
            'remote': REMOTE + '/' + parent + '/' + leaf}
    return record


def fixture():
    audio = d.file_proof(b'synthetic receipt bytes' * 1000)
    flags = dict.fromkeys(FLAGS, False); flags.update(translation_status='unknown', native_quality_state=None)
    selection = {'video_id': 'abcdefghijk', 'format_id': '140', 'protocol': 'https',
        'ext': 'm4a', 'acodec': 'mp4a.40.2', 'vcodec': 'none', 'filesize': audio['bytes'],
        'duration_seconds': 10.0, 'live_status': 'not_live', 'has_drm': False, 'is_drc': False,
        'original_audio_track_identity_verified': False, 'spoken_language_verified': False,
        'metadata_sha256': 'a' * 64}
    http = {'selected_video_id': selection['video_id'], 'selected_format_id': '140',
        'selected_url_sha256': 'b' * 64, 'request_url_sha256': 'b' * 64, 'final_url_sha256': 'b' * 64,
        'content_length': audio['bytes'], 'received_bytes': audio['bytes'], 'written_bytes': audio['bytes'],
        'exact_on_write_limit': audio['bytes'], 'status': 200, 'content_range': None,
        'body_sha256': audio['sha256'], 'body_complete': True, 'headers_checked_before_sink_write': True,
        'finished_count': 1, 'media_requests': 1, 'redirect_count': 0, 'retry_count': 0}
    scan = {'quality_state': 'complete_native_audio', 'strict_probe_passed': True, 'codec': 'aac',
        'audio_streams': 1, 'video_streams': 0, 'packet_count': 450, 'semantic_audio_reviewed': False,
        'human_reviewed': False, 'full_speech_coverage_claimed': False, 'full_decode_performed': False,
        'container_duration_seconds': 10.0, 'source_duration_seconds': 10.0}
    payload = dict(flags, source_file=audio, archived_audio_file=deepcopy(audio),
        source_and_archived_audio_same_bytes=True, file_before_after_quality_equal=True,
        audio_reencoded=False, remuxed_container=False, selection=selection,
        source_http=http, strict_probe=scan)
    q = {'contract': d.CONTRACT, 'payload_encoding': d.ENCODING,
        'quality_module': {'sha256': d.QUALITY_SHA, 'bytes': 4251}, 'payload': payload}
    record = dict(flags, schema_version=1, kind=d.KIND, status='deleted',
        video_id=selection['video_id'], channel_dir='fixture-channel', tab='shorts',
        variant_id=audio['sha256'], source_format_id='140', root_grant_sha256='c' * 64,
        native_count_increment=0, qualification=q, audio={'local_proof': deepcopy(audio)}, metadata={})
    return seal(record)


class DirectReceipts(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('builtins.open', side_effect=AssertionError('no filesystem')))
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('no network')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('no processes')))

    def reject(self, record):
        with self.assertRaises(d.ReceiptHold): d.validate(record, remote_base=REMOTE)

    def test_valid_pair_counts_only_qualified_audio_without_identity_or_text_claim(self):
        edition = d.validate(fixture(), remote_base=REMOTE)
        self.assertEqual('abcdefghijk', edition.video_id)
        self.assertFalse(edition.native_promotion); self.assertFalse(edition.text_or_ASR_coverage)

    def test_full206_extent_is_valid_but_partial_or_boolean_lengths_are_not(self):
        r = fixture(); h = r['qualification']['payload']['source_http']; size = h['content_length']
        h.update(status=206, content_range=[0, size - 1, size])
        d.validate(seal(r), remote_base=REMOTE)
        h['content_range'] = [1, size - 1, size]; self.reject(seal(r))
        h.update(status=200, content_range=None, finished_count=True); self.reject(seal(r))

    def test_transport_replay_wrong_URL_or_incomplete_bytes_reject_after_resealing(self):
        for key, value in (('media_requests', 2), ('redirect_count', 1), ('retry_count', 1),
                           ('final_url_sha256', 'd' * 64), ('received_bytes', 4), ('body_complete', False)):
            r = fixture(); r['qualification']['payload']['source_http'][key] = value
            self.reject(seal(r))

    def test_original_or_language_or_native_promotion_claims_never_accepted(self):
        for key in FLAGS:
            r = fixture(); r[key] = True; r['qualification']['payload'][key] = True
            self.reject(seal(r))
        r = fixture(); r['native_count_increment'] = 1; self.reject(seal(r))

    def test_same_file_and_pre_post_probe_fingerprint_binding_required(self):
        for key in ('source_and_archived_audio_same_bytes', 'file_before_after_quality_equal'):
            r = fixture(); r['qualification']['payload'][key] = False; self.reject(seal(r))
        r = fixture(); r['qualification']['payload']['archived_audio_file']['sha256'] = 'd' * 64
        self.reject(seal(r))

    def test_wrong_codec_video_streams_truncation_or_warning_probe_reject(self):
        for key, value in (('codec', 'opus'), ('video_streams', 1), ('container_duration_seconds', 1),
                           ('strict_probe_passed', False), ('quality_state', 'complete_with_codec_warning'),
                           ('full_speech_coverage_claimed', True), ('source_duration_seconds', float('inf'))):
            r = fixture(); r['qualification']['payload']['strict_probe'][key] = value
            if value == float('inf'):
                with self.assertRaises(ValueError): seal(r)
            else: self.reject(seal(r))

    def test_exact_nonDRM_nonDRC_completed_audio_offer_required(self):
        for key, value in (('has_drm', True), ('is_drc', True), ('format_id', '18'),
                           ('live_status', 'is_live'), ('vcodec', 'avc1'), ('filesize', 1),
                           ('original_audio_track_identity_verified', True)):
            r = fixture(); r['qualification']['payload']['selection'][key] = value
            self.reject(seal(r))

    def test_quality_module_pin_is_not_the_progressive_remux_verifier(self):
        r = fixture(); r['qualification']['quality_module']['sha256'] = '519b' + '0' * 60
        self.reject(seal(r))

    def test_pair_requires_actual_size_MD5_distinctIDs_and_scoped_paths(self):
        for change in ('md5', 'id', 'path', 'sha'):
            r = fixture()
            if change == 'md5': r['metadata']['remote_proof']['md5'] = '0' * 32
            if change == 'id': r['metadata']['remote_proof']['drive_id'] = r['audio']['remote_proof']['drive_id']
            if change == 'path': r['audio']['remote_proof']['relative_path'] = 'elsewhere/audio.m4a'
            if change == 'sha': r['audio']['remote_proof']['sha256'] = 'd' * 64
            self.reject(r)

    def test_provenance_file_hash_or_false_file_variant_reject(self):
        r = fixture(); r['provenance']['tab'] = 'videos'; self.reject(r)
        r = fixture(); r['variant_id'] = 'd' * 64; self.reject(seal(r))


if __name__ == '__main__': unittest.main()
