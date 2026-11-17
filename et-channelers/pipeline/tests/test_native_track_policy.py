"""Raw-inventory fixtures; no network, browser or media dependencies."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from pipeline import native_track_policy as policy, native_batch_worker as worker, media_metadata

ID = 'aaaaaaaaaaa'


def representation(itag, codec='mp4a.40.2', **extra):
    subtype = 'webm' if codec == 'opus' else 'mp4'
    return {'itag': itag, 'mimeType': f'audio/{subtype}; codecs="{codec}"',
            'contentLength': '123', 'url': 'https://media.invalid/?sig=never-export', **extra}


def response(formats=None, **extra):
    return {'videoDetails': {'videoId': ID}, 'playabilityStatus': {'status': 'OK'},
            'streamingData': {'__yt_dlp_client': 'mweb', 'adaptiveFormats': formats if formats is not None else [
                representation(139), representation(140), representation(251, 'opus')]}, **extra}


def selected(**extra):
    return {'id': ID, 'format_id': '140', 'protocol': 'https', 'vcodec': 'none', 'acodec': 'mp4a.40.2',
            'ext': 'm4a', 'language': None, 'language_preference': -1, 'filesize': 123, 'duration': 30, **extra}


class LegacyTrackTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('socket.socket.connect', side_effect=AssertionError('network forbidden')))
        self.enterContext(patch('subprocess.Popen', side_effect=AssertionError('process forbidden')))

    def test_explicit_drc_variants_preserve_complete_legacy_inventory_but_cannot_be_selected(self):
        raw = [response([representation(140), representation(140, isDrc=True, contentLength='124'),
                         representation(251, 'opus'), representation(251, 'opus', isDrc=True)])]
        before = copy.deepcopy(raw)
        inventory = policy.legacy_track_inventory(ID, raw)
        self.assertTrue(inventory['eligible']); self.assertTrue(inventory['inspection_complete'])
        self.assertEqual(inventory['inspected_formats'], 4)
        self.assertEqual(len(inventory['audio_representations']), 4)
        self.assertEqual(before, raw)
        proof = policy.legacy_selection_proof(selected(language='en'), inventory)
        self.assertFalse(proof['selected_is_drc']); self.assertIsNone(proof['source_language'])
        for change in ({'format_id': '140-drc'}, {'isDrc': True}, {'filesize': 124}, {'filesize': None}):
            self.assertIsNone(policy.legacy_selection_proof(selected(**change), inventory))
        self.assertNotIn('never-export', json.dumps(inventory))

    def test_same_variant_duplicates_drc_only_and_ambiguous_pairs_remain_held(self):
        cases = [[representation(140), representation(140)],
                 [representation(140), representation(140, isDrc=True), representation(140, isDrc=True)],
                 [representation(140, isDrc=True)],
                 [representation(140), representation(251, 'opus', isDrc=True)],
                 [representation(140), representation(140, 'opus', isDrc=True)],
                 [representation(140), representation(140, isDrc='true')]]
        for rows in cases:
            with self.subTest(rows=len(rows)):
                inventory = policy.legacy_track_inventory(ID, [response(rows)])
                self.assertFalse(inventory['eligible'])
                self.assertEqual(inventory['inspected_formats'], len(rows))

    def test_drc_rows_do_not_hide_later_labels_drm_or_client_conflicts(self):
        for changes, reason in [({'audioTrack': {'id': 'en.1', 'audioIsDefault': True}}, 'track_labels_present'),
                                ({'language': 'es'}, 'track_labels_present'),
                                ({'isVoiceBoost': True}, 'track_labels_present'),
                                ({'drmFamilies': ['WIDEVINE']}, 'drm_audio_alternative'),
                                ({'__yt_dlp_client': 'web'}, 'conflicting_client_inventory')]:
            rows = [representation(140), representation(140, isDrc=True),
                    representation(251, 'opus', url=None, **changes)]
            result = policy.legacy_track_inventory(ID, [response(rows)])
            self.assertFalse(result['eligible']); self.assertIn(reason, result['rejection_reasons'])
            self.assertEqual(result['inspected_formats'], 3)
        result = policy.legacy_track_inventory(ID, [response([representation(140), representation(140),
            representation(251, 'opus', language='es', drmFamilies=['WIDEVINE'])])])
        self.assertEqual(result['rejection_reasons'], ['ambiguous_duplicate_itag', 'track_labels_present', 'drm_audio_alternative'])

    def test_drc_query_is_only_allowed_when_exact_explicit_raw_flag_matches(self):
        for flag, query, allowed in [(True, 'drc=1', True), (False, 'drc=1', False),
                                      (True, 'drc=0', False), (True, 'drc=1&lang=es', False),
                                      (True, 'drc=1&vb=1', False), (True, 'xtags=opaque', False)]:
            rows = [representation(140), representation(140, isDrc=flag, url='https://media.invalid/?'+query)]
            self.assertEqual(policy.legacy_track_inventory(ID, [response(rows)])['eligible'], allowed)

    def test_catalog_bound_cannot_produce_complete_or_eligible_proof(self):
        with patch.object(policy, 'MAX_RAW_FORMATS', 2):
            result = policy.legacy_track_inventory(ID, [response()])
        self.assertFalse(result['eligible']); self.assertFalse(result['inspection_complete'])
        self.assertEqual(result['reason'], 'inventory_limit'); self.assertEqual(result['inspected_formats'], 2)

    def test_diagnostic_transport_hint_does_not_claim_protocol_completion_or_access(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(worker, 'TARGET', ID):
            state = worker.State({'preserved_controls': []}, Path(tmp), time.time()+60)
            formats = [selected(protocol=None, url='https://media.invalid/path?secret=never-export'),
                       selected(format_id='140-drc', protocol='https', url='https://media.invalid/private',
                                language='en', language_preference=10, format_note='English original')]
            worker.save_format_inventory(state, {'id': ID, 'formats': formats})
            value = worker.read(Path(tmp)/'format-inventory.json')
        self.assertEqual(value['protocol_pending_count'], 1)
        self.assertEqual(value['https_audio_transport_hints'], 2)
        self.assertIsNone(value['formats'][0]['protocol'])
        self.assertEqual(value['formats'][0]['protocol_state'], 'pre_normalization_missing')
        self.assertEqual(value['formats'][0]['transport_hint'], 'https')
        self.assertTrue(value['formats'][1]['drc_variant'])
        self.assertEqual(value['original_https_audio_candidates'], 0)
        self.assertFalse(value['transport_hints_prove_access'])
        self.assertTrue(all(row['access_proven'] is False for row in value['formats']))
        self.assertNotIn('never-export', json.dumps(value)); self.assertNotIn('media.invalid', json.dumps(value))

    def test_complete_unlabeled_representations_allow_inference_only_with_unknown_language(self):
        raw = [response(captions={'translatedLanguages': ['en', 'de', 'es']})]
        before = copy.deepcopy(raw); inventory = policy.legacy_track_inventory(ID, raw)
        self.assertTrue(inventory['eligible']); self.assertEqual(raw, before)
        proof = worker.validate_selection(selected(), ID, None, 1000, {'mp4a.40.2'}, inventory)
        self.assertEqual(proof['basis'], 'provider_single_legacy_track_inference')
        self.assertTrue(proof['origin_inferred']); self.assertFalse(proof['original_explicitly_verified'])
        self.assertIsNone(proof['source_language']); self.assertEqual(proof['source_language_status'], 'unknown')
        self.assertNotIn('never-export', json.dumps(inventory)); self.assertNotIn('https://', json.dumps(inventory))
        with tempfile.TemporaryDirectory() as tmp, patch.object(worker, 'TARGET', ID):
            state = worker.State({'preserved_controls': []}, Path(tmp), time.time() + 60)
            state.original_track = proof; state.raw_audio_inventory = inventory
            worker.persist_selection(state, dict(selected(), subtitles={'en': []}), media_metadata.build_metadata)
            metadata = worker.read(Path(tmp) / 'selected-metadata.info.json')
            self.assertIsNone(metadata['languages']['audio'])
            self.assertEqual(metadata['languages']['manual_subtitles'], ['en'])
            self.assertFalse(metadata['native_selection']['original_audio_evidence']['original_explicitly_verified'])

    def test_default_track_label_is_never_original_or_legacy(self):
        inventory = policy.legacy_track_inventory(ID, [response([representation(140, audioTrack={'id': 'en.1', 'audioIsDefault': True})])])
        self.assertFalse(inventory['eligible'])
        with self.assertRaisesRegex(worker.Held, 'original_audio_unproven'):
            worker.validate_selection(selected(language='en', language_preference=5), ID, None, 1000, {'mp4a.40.2'}, inventory)

    def test_normalized_caption_language_is_not_source_audio_evidence(self):
        inventory = policy.legacy_track_inventory(ID, [response()])
        info = selected(language='en', subtitles={'en': []})
        proof = worker.validate_selection(info, ID, None, 1000, {'mp4a.40.2'}, inventory)
        self.assertFalse(proof['normalized_language_used_as_audio_evidence'])
        self.assertIsNone(proof['source_language'])
        for change in ({'language_preference': -2}, {'language_preference': 5},
                       {'format_id': '251'}, {'filesize': 124}, {'filesize': None}, {'acodec': 'opus'}):
            self.assertIsNone(policy.legacy_selection_proof(dict(info, **change), inventory))
        for missing_size in (None, 0, True):
            missing = copy.deepcopy(inventory)
            next(f for f in missing['audio_representations'] if f['itag'] == 140)['source_bytes'] = missing_size
            self.assertIsNone(policy.legacy_selection_proof(info, missing))
        with tempfile.TemporaryDirectory() as tmp, patch.object(worker, 'TARGET', ID):
            state = worker.State({'preserved_controls': []}, Path(tmp), time.time() + 60)
            state.original_track = proof; state.raw_audio_inventory = inventory
            worker.persist_selection(state, info, media_metadata.build_metadata)
            metadata = worker.read(Path(tmp) / 'selected-metadata.info.json')
            for value in (metadata['languages']['audio'], metadata['metadata']['language'],
                          metadata['native_selection']['source_language'],
                          metadata['native_selection']['format']['language']):
                self.assertIsNone(value)
            self.assertEqual(metadata['languages']['manual_subtitles'], ['en'])
            self.assertEqual(info['language'], 'en')

    def test_labeled_multitrack_keeps_strict_explicit_original_branch(self):
        inventory = policy.legacy_track_inventory(ID, [response([
            representation(140, audioTrack={'id': 'en.0', 'displayName': 'English original'}),
            representation(140, audioTrack={'id': 'es.1', 'displayName': 'Spanish dubbed'})])])
        self.assertFalse(inventory['eligible'])
        proof = worker.validate_selection(selected(language='en', language_preference=10, format_note='English original'),
            ID, None, 1000, {'mp4a.40.2'}, inventory)
        self.assertTrue(proof['original_explicitly_verified']); self.assertFalse(proof['origin_inferred'])

    def test_duplicate_base_itag_is_ambiguous_even_without_track_labels(self):
        inventory = policy.legacy_track_inventory(ID, [response([representation(140), representation(140)])])
        self.assertFalse(inventory['eligible']); self.assertEqual(inventory['reason'], 'ambiguous_duplicate_itag')

    def test_url_missing_alternatives_are_inspected_before_transport_filtering(self):
        for extra in ({'language': 'es'}, {'xtags': 'acont=dubbed-auto'}, {'audioTrack': {'id': 'es.1'}}):
            alternate = representation(141, **extra); alternate.pop('url')
            inventory = policy.legacy_track_inventory(ID, [response([representation(140), alternate])])
            self.assertFalse(inventory['eligible'])
        tagged = representation(140, url='https://media.invalid/?xtags=acont%3Ddubbed-auto')
        self.assertFalse(policy.legacy_track_inventory(ID, [response([tagged])])['eligible'])

    def test_incomplete_wrong_identity_failed_or_conflicting_responses_hold(self):
        cases = [response(truncated=True), response(videoDetails={'videoId': 'bbbbbbbbbbb'}),
                 response(playabilityStatus={'status': 'LOGIN_REQUIRED'}),
                 response(streamingData={'__yt_dlp_client': 'mweb'}), response(streamingData=None)]
        for value in cases:
            with self.subTest(value=list(value)):
                self.assertFalse(policy.legacy_track_inventory(ID, [value])['eligible'])
        other = response(); other['streamingData']['__yt_dlp_client'] = 'web'
        self.assertFalse(policy.legacy_track_inventory(ID, [response(), other])['eligible'])

    def test_no_audio_drm_or_voice_modified_alternatives_hold(self):
        cases = [[], [{'itag': 137, 'mimeType': 'video/mp4; codecs="avc1.640028"'}],
                 [representation(140, drmFamilies=['WIDEVINE'])], [representation(140, isDrc=True)],
                 [representation(140, isVoiceBoost=True)]]
        for formats in cases:
            self.assertFalse(policy.legacy_track_inventory(ID, [response(formats)])['eligible'])

    def test_normalized_inventory_alone_or_unbound_selection_cannot_infer(self):
        for raw in (None, [], [selected()]):
            self.assertFalse(policy.legacy_track_inventory(ID, raw)['eligible'])
        with self.assertRaisesRegex(worker.Held, 'original_audio_unproven'):
            worker.validate_selection(selected(), ID, None, 1000, {'mp4a.40.2'})
        inventory = policy.legacy_track_inventory(ID, [response()])
        for change in ({'format_id': '140-1'}, {'acodec': 'opus'}, {'filesize': 999}, {'language_preference': 5}):
            self.assertIsNone(policy.legacy_selection_proof(selected(**change), inventory))


if __name__ == '__main__': unittest.main()
