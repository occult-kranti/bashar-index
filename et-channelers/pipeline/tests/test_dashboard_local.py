"""Tests for dashboard_local.py (invented fragment, no network)."""
import json
import csv
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pipeline import dashboard_local, ingestion_status


FRAGMENT = (
    '<meta name="dash-one-writer">\n<style>.x{color:var(--color-fg)}</style>\n'
    '<div class="page"><b data-draw="g-people" data-source="totals" data-field="people" data-row="0">—</b></div>\n'
    "<script>dash.calc('totals', { inputs: ['targets'], fn: (t) => [{ people: t.length }] });</script>\n"
)


class BuildTests(unittest.TestCase):
    def test_wraps_fragment_in_a_page_with_a_host(self):
        html = dashboard_local.build(FRAGMENT, "../../plan/")
        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertNotIn('dash-one-writer', html)
        self.assertIn("window.dash = {", html)
        self.assertIn('data-draw="g-people"', html)
        self.assertIn("dash.calc('totals'", html)
        self.assertIn(json.dumps("../../plan/"), html)
        self.assertIn('"bashar_channels": "bashar_host_channels"', html)
        for name in ("coverage", "sources", "targets", "contacts", "transcript_audio"):
            self.assertIn(json.dumps(name), html)
        self.assertEqual(html.count("<script"), 4)  # shared navigation, d3, host, fragment
        self.assertIn('@media (prefers-color-scheme: dark)', html)
        self.assertIn(':root[data-theme="dark"]', html)
        self.assertTrue(html.rstrip().endswith("</html>"))
        self.assertNotIn('<p class="local-note">', html)
        self.assertIn('data-page="collection"', html)
        self.assertIn("if (typeof fn === 'function') draws.set", html)

    def test_base_is_json_escaped(self):
        html = dashboard_local.build(FRAGMENT, "./da\"ta/")
        self.assertIn(json.dumps("./da\"ta/"), html)


class StatusExportTests(unittest.TestCase):
    def test_verified_publisher_mirrors_and_captions_keep_separate_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'jobs').mkdir()
            (root / 'jobs/queue_newest20.csv').write_text(
                'video_id,channel_dir\n12345678901,PRIVATE-PERSON\n', encoding='utf-8')
            parent = ingestion_status.DEFAULT_REMOTE + '/PRIVATE-PERSON/Videos/12345678901/PublisherVariants/' + 'a' * 64
            def obj(path, digest='b' * 64):
                return {'remote': path, 'bytes': 123, 'drive_id': 'PRIVATE-' + hashlib.sha256(path.encode()).hexdigest()[:16],
                        'md5': 'c' * 32, 'sha256': digest}
            record = {'schema_version': 1, 'kind': 'qualified_publisher_mirror_audio_variant', 'status': 'verified',
                      'associated_youtube_id': '12345678901', 'channel_dir': 'PRIVATE-PERSON', 'variant_id': 'a' * 64,
                      'association_method': 'publisher_owner_title_date_duration', 'native_youtube_bytes': False,
                      'changes_native_audio_count': False, 'changes_native_asr_count': False,
                      'changes_native_caption_count': False, 'exact_youtube_crossreference': False, 'human_verified': False,
                      'audio': obj(parent + '/publisher-audio.aac', 'a' * 64),
                      'provenance': obj(parent + '/provenance.json'),
                      'caption_bundle': dict(obj(parent + '/Captions/' + 'b' * 64 + '/captions.zip'),
                                             language='en', usable_timed_text=True)}
            path = root / 'sync/publisher_mirror_manifest.jsonl'
            def write():
                path.write_text(json.dumps(record) + '\n' + json.dumps(record) + '\n{partial', encoding='utf-8')
            write()
            result = ingestion_status.snapshot(root)
            self.assertEqual(result['counts']['publisher_mirror_audio_target_videos'], 1)
            self.assertEqual(result['counts']['publisher_mirror_caption_target_videos'], 1)
            self.assertEqual(result['counts']['source_audio_available_target_videos'], 1)
            self.assertEqual(result['counts']['source_audio_with_text_target_videos'], 1)
            for key in ('verified_pairs', 'audio_archived_videos', 'asr_verified_videos', 'text_available_videos'):
                self.assertEqual(result['counts'][key], 0)
            for private in ('PRIVATE', '12345678901', str(root)):
                self.assertNotIn(private, json.dumps(result))
            provenance_id = record['provenance']['drive_id']
            record['provenance']['drive_id'] = record['audio']['drive_id']
            write()
            invalid_pair = ingestion_status.snapshot(root)['counts']
            self.assertEqual(invalid_pair['publisher_mirror_audio_target_videos'], 0)
            self.assertEqual(invalid_pair['publisher_mirror_caption_target_videos'], 0)
            record['provenance']['drive_id'] = provenance_id
            caption_id = record['caption_bundle']['drive_id']
            for source_id in (record['audio']['drive_id'], provenance_id):
                record['caption_bundle']['drive_id'] = source_id
                write()
                invalid_caption = ingestion_status.snapshot(root)['counts']
                self.assertEqual(invalid_caption['publisher_mirror_audio_target_videos'], 1)
                self.assertEqual(invalid_caption['publisher_mirror_caption_target_videos'], 0)
                self.assertEqual(invalid_caption['source_audio_with_text_target_videos'], 0)
            record['caption_bundle']['drive_id'] = caption_id
            record['caption_bundles'] = [record.pop('caption_bundle')]
            write()
            self.assertEqual(ingestion_status.snapshot(root)['counts']['publisher_mirror_caption_target_videos'], 1)
            record['caption_bundles'][0]['language'] = 'ja'
            write()
            self.assertEqual(ingestion_status.snapshot(root)['counts']['publisher_mirror_caption_target_videos'], 0)
            generated = dict(obj(parent + '/ASR/trial/trial.zip'), schema_version=1, status='verified',
                             artifact_kind='publisher_variant_asr', associated_youtube_id='12345678901',
                             channel_dir='PRIVATE-PERSON', variant_id='a' * 64, run_id='trial',
                             quality_state='unreviewed_asr', source_audio=dict(record['audio']),
                             source_provenance=dict(record['provenance']), native_youtube_bytes=False,
                             changes_native_audio_count=False, changes_native_asr_count=False)
            asr_path = root / 'sync/publisher_variant_asr_manifest.jsonl'
            asr_path.write_text(json.dumps(generated) + '\n', encoding='utf-8')
            self.assertEqual(ingestion_status.snapshot(root)['counts']['publisher_mirror_asr_target_videos'], 1)
            self.assertEqual(ingestion_status.snapshot(root)['counts']['source_audio_with_text_target_videos'], 1)
            result_id = generated['drive_id']
            for source_id in (record['audio']['drive_id'], provenance_id):
                generated['drive_id'] = source_id
                asr_path.write_text(json.dumps(generated) + '\n', encoding='utf-8')
                invalid_asr = ingestion_status.snapshot(root)['counts']
                self.assertEqual(invalid_asr['publisher_mirror_audio_target_videos'], 1)
                self.assertEqual(invalid_asr['publisher_mirror_asr_target_videos'], 0)
                self.assertEqual(invalid_asr['source_audio_with_text_target_videos'], 0)
            generated['drive_id'] = result_id
            generated['source_audio']['sha256'] = 'd' * 64
            asr_path.write_text(json.dumps(generated) + '\n', encoding='utf-8')
            self.assertEqual(ingestion_status.snapshot(root)['counts']['publisher_mirror_asr_target_videos'], 0)
            record.update(kind='publisher_mirror_audio_variant', association_method='publisher_rss_exact_youtube_id',
                          exact_youtube_crossreference=True, original_youtube_link='https://youtu.be/12345678901')
            write()
            self.assertEqual(ingestion_status.snapshot(root)['counts']['publisher_mirror_audio_target_videos'], 1)
            record['original_youtube_link'] = 'https://youtu.be/DIFFERENTID'
            write()
            self.assertEqual(ingestion_status.snapshot(root)['counts']['publisher_mirror_audio_target_videos'], 0)
            record['original_youtube_link'] = 'https://youtu.be/12345678901'
            record['provenance']['drive_id'] = ''
            write()
            self.assertEqual(ingestion_status.snapshot(root)['counts']['publisher_mirror_audio_target_videos'], 0)

    def test_local_browser_proof_is_private_and_never_promotes_source_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            proof = root / 'provisioning/adblock-v1/runs/example/audit-summary.json'
            proof.parent.mkdir(parents=True)
            content = b'{"private_fixture":"SECRET DETAILS"}'
            proof.write_bytes(content)
            record = {'schema_version': 1, 'status': 'verified_local', 'scope': 'project_isolated_chromium',
                      'name': 'uBlock Origin Lite', 'version': '2026.1116.1650', 'browser_version': '151.0.7922.34',
                      'mode': 'optimal', 'tested_at': '2026-11-17T15:34:01Z',
                      'local_filtering_verified': True, 'downloader_coexistence_verified': True,
                      'profiles_cleaned': True, 'source_acceptance_verified': True,
                      'private_url': 'https://SECRET.invalid',
                      'proof': {'path': proof.relative_to(root).as_posix(), 'bytes': len(content),
                                'sha256': hashlib.sha256(content).hexdigest()}}
            state = root / 'sync/browser_extensions_state.json'
            state.write_text(json.dumps(record), encoding='utf-8')
            result = ingestion_status.snapshot(root)
            self.assertEqual(result['browser_support']['state'], 'verified_local')
            self.assertFalse(result['browser_support']['source_acceptance_verified'])
            self.assertEqual(result['counts']['verified_pairs'], 0)
            for value in ('SECRET', str(root), 'https://', 'sha256', 'audit-summary'):
                self.assertNotIn(value, json.dumps(result))
            proof.write_bytes(content + b'changed')
            self.assertEqual(ingestion_status.snapshot(root)['browser_support']['state'], 'not_verified')
            proof.write_bytes(content)
            record['proof']['path'] = str(Path(folder).parent / 'outside/audit-summary.json')
            state.write_text(json.dumps(record), encoding='utf-8')
            self.assertEqual(ingestion_status.snapshot(root)['browser_support']['state'], 'not_verified')

    def test_publisher_editions_require_complete_proofs_and_never_promote_native_progress(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'jobs').mkdir()
            (root / 'jobs/queue_newest20.csv').write_text(
                'video_id,channel_dir\n12345678901,PRIVATE-PERSON\nABCDEFGHIJK,PRIVATE-PERSON\n', encoding='utf-8')
            remote = ingestion_status.DEFAULT_REMOTE
            def obj(kind, path):
                return {'kind': kind, 'remote': path, 'bytes': 123, 'drive_id': 'PRIVATE-ID',
                        'md5': 'a' * 32, 'sha256': 'b' * 64}
            text_kind = 'publisher_authored_article_batch'
            batch = {'schema_version': 1, 'status': 'verified', 'artifact_kind': text_kind,
                     'changes_native_audio_count': False, 'changes_full_asr_count': False,
                     'proof': obj(text_kind, remote + '/PRIVATE-PERSON/PublisherText/Batches/' + 'b' * 64 + '/publisher-text.zip'),
                     'items': [{'video_id': '12345678901', 'author_html_sha256': 'c' * 64, 'text_sha256': 'd' * 64,
                                'article_url': 'https://PRIVATE.invalid/article', 'title': 'PRIVATE TITLE'},
                               {'video_id': [], 'author_html_sha256': 'c' * 64, 'text_sha256': 'd' * 64},
                               {'video_id': 'NOTINTARGET', 'author_html_sha256': 'c' * 64, 'text_sha256': 'd' * 64}]}
            parent = remote + '/PRIVATE-PERSON/Videos/ABCDEFGHIJK/PublisherVariants/' + 'b' * 64
            variant = {'schema_version': 1, 'status': 'verified', 'artifact_kind': 'publisher_podcast_audio_variant',
                       'video_id': 'ABCDEFGHIJK', 'channel_dir': 'PRIVATE-PERSON', 'native_youtube_bytes': False,
                       'changes_native_audio_count': False, 'changes_full_asr_count': False,
                       'audio': obj('publisher_podcast_audio_variant', parent + '/publisher-audio.mp3'),
                       'provenance': obj('publisher_podcast_variant_provenance', parent + '/provenance.json')}
            companion_path = root / 'sync/publisher_companion_manifest.jsonl'
            variant_path = root / 'sync/publisher_variant_manifest.jsonl'
            publisher_asr_path = root / 'sync/publisher_variant_asr_manifest.jsonl'
            transcript = dict(batch, artifact_kind='publisher_transcript_batch',
                              proof=obj('publisher_transcript_batch', remote + '/PRIVATE-PERSON/PublisherTranscripts/Batches/' + 'b' * 64 + '/publisher-transcripts.zip'),
                              items=[dict(batch['items'][0], text_kind='publisher_transcript_untimed',
                                          publisher_declares_transcript=True, language='en',
                                          original_youtube_link='https://youtu.be/12345678901')])
            transcript['proof'].pop('kind')  # the batch's artifact_kind supplies its role
            variant_asr = dict(obj('publisher_variant_asr', parent + '/ASR/trial/trial.zip'),
                               schema_version=1, status='verified', artifact_kind='publisher_variant_asr',
                               associated_youtube_id='ABCDEFGHIJK', channel_dir='PRIVATE-PERSON',
                               variant_id='b' * 64, run_id='trial', source_audio=dict(variant['audio']),
                               source_provenance=dict(variant['provenance']), native_youtube_bytes=False,
                               changes_native_audio_count=False, changes_native_asr_count=False,
                               quality_state='unreviewed_asr')
            variant_asr['source_audio'].pop('kind')
            variant_asr['source_provenance'].pop('kind')
            qualified = dict(variant, video_id='12345678901', artifact_kind='qualified_publisher_podcast_audio_variant',
                             identity_basis='publisher_rss_source_id_references', direct_watch_link_present=False,
                             association_human_verified=False)
            qualified_parent = remote + '/PRIVATE-PERSON/Videos/12345678901/PublisherVariants/' + 'b' * 64
            qualified['audio'] = obj('qualified_publisher_podcast_audio_variant', qualified_parent + '/publisher-audio.mp3')
            qualified['provenance'] = obj('qualified_publisher_variant_provenance', qualified_parent + '/provenance.json')
            qualified_asr = dict(variant_asr, associated_youtube_id='12345678901',
                                 source_audio=dict(qualified['audio']), source_provenance=dict(qualified['provenance']),
                                 remote=qualified_parent + '/ASR/trial/trial.zip')
            publisher_asr_path.write_text(json.dumps(variant_asr) + '\n' + json.dumps(variant_asr) + '\n')
            with publisher_asr_path.open('a') as stream:
                stream.write(json.dumps(qualified_asr) + '\n')
            def write(records, variants):
                companion_path.write_text('\n'.join(json.dumps(x) for x in records) + '\n', encoding='utf-8')
                variant_path.write_text('\n'.join(json.dumps(x) for x in variants) + '\n', encoding='utf-8')
            write([batch, batch, transcript, {'artifact_kind': []}], [variant, variant, qualified])
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['counts']['publisher_text_target_videos'], 1)
            self.assertEqual(result['counts']['publisher_audio_variant_target_videos'], 2)
            self.assertEqual(result['counts']['publisher_audio_qualified_variant_target_videos'], 1)
            self.assertEqual(result['counts']['publisher_transcript_target_videos'], 1)
            self.assertEqual(result['counts']['publisher_variant_asr_target_videos'], 2)
            for key in ('verified_pairs', 'audio_archived_videos', 'asr_verified_videos', 'text_available_videos'):
                self.assertEqual(result['counts'][key], 0)
            self.assertEqual(result['stages'][0]['verified'], 0)
            for private in ('PRIVATE', 'ABCDEFGHIJK', '12345678901', 'https://', str(root)):
                self.assertNotIn(private, json.dumps(result))
            # An incomplete pair, a different remote, or mixed completion scope is not evidence.
            variant['provenance'].pop('drive_id')
            batch['proof']['remote'] = 'other:' + batch['proof']['remote']
            write([batch], [variant])
            invalid = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(invalid['counts']['publisher_text_target_videos'], 0)
            self.assertEqual(invalid['counts']['publisher_audio_variant_target_videos'], 0)
            self.assertEqual(invalid['counts']['publisher_variant_asr_target_videos'], 0)
            batch['proof']['remote'] = remote + '/PRIVATE-PERSON/PublisherText/Batches/' + 'b' * 64 + '/publisher-text.zip'
            batch['changes_full_asr_count'] = True
            write([batch], [])
            self.assertEqual(ingestion_status.snapshot(root)['counts']['publisher_text_target_videos'], 0)
            # An unrelated source proof or a non-English/non-transcript item never joins.
            batch['changes_full_asr_count'] = False
            transcript['items'][0]['publisher_declares_transcript'] = False
            variant['provenance']['drive_id'] = 'PRIVATE-ID'
            variant_asr['source_audio']['drive_id'] = 'WRONG-SOURCE'
            publisher_asr_path.write_text(json.dumps(variant_asr) + '\n')
            write([transcript], [variant])
            rejected = ingestion_status.snapshot(root)
            self.assertEqual(rejected['counts']['publisher_transcript_target_videos'], 0)
            self.assertEqual(rejected['counts']['publisher_variant_asr_target_videos'], 0)

    def test_isolated_cli_exports_only_aggregates_from_an_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'private'
            (root / 'sync').mkdir(parents=True)
            (root / 'jobs').mkdir()
            (root / 'jobs/queue_newest20.csv').write_text(
                'video_id,channel_dir,title\n12345678901,PRIVATE-PERSON,SECRET TITLE\n', encoding='utf-8')
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps({
                'video_id': '12345678901', 'status': 'unavailable', 'error_class': 'unavailable',
                'title': 'SECRET TITLE', 'path': str(root), 'url': 'https://private.invalid/SECRET',
            }) + '\n', encoding='utf-8')
            output = Path(folder) / 'public/status.json'
            result = subprocess.run(
                [sys.executable, '-I', str(Path(ingestion_status.__file__).resolve()),
                 '--root', str(root), '--out', str(output)],
                cwd=folder, capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            public = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(json.loads(result.stdout), public)
            self.assertEqual(public['counts']['unavailable'], 1)
            self.assertEqual(public['counts']['verified_pairs'], 0)
            self.assertEqual(public['counts']['channels'], 1)
            self.assertFalse(output.with_suffix('.json.tmp').exists())
            for private in ('SECRET', 'PRIVATE-PERSON', '12345678901', str(root), 'https://'):
                self.assertNotIn(private, json.dumps(public))

    def test_supervisor_backoff_and_full_archive_plan_are_public_aggregates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_resume_state.json').write_text(json.dumps({
                'schema_version': 2, 'mode': 'RunAll', 'download_workers': 6,
                'state': 'waiting_for_drive_cooldown', 'until_epoch': 1800001200,
                'private_log': 'SECRET FILE', 'supervisor_pid': 1234}))
            result = ingestion_status.snapshot(root, now=1800000000)
        self.assertEqual(result['operation']['state'], 'cooldown')
        self.assertEqual(result['operation']['workers'], 6)
        self.assertTrue(result['operation']['full_archive_requested'])
        self.assertEqual(result['stages'][-1]['key'], 'final_archive')
        self.assertEqual(result['storage']['ceiling_bytes'], 17_000_000_000)
        self.assertNotIn('SECRET FILE', json.dumps(result))
        self.assertNotIn('supervisor_pid', json.dumps(result))

    def test_source_and_drive_cooldowns_are_typed_public_aggregates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps({
                'video_id': 'PRIVATE-ID', 'error_class': 'forbidden',
                'retry_not_before_epoch': 1800001200, 'error': 'PRIVATE ERROR'}) + '\n', encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'cooldown')
            self.assertEqual(result['operation']['cooldown_provider'], 'youtube')
            self.assertEqual(result['operation']['retry_after'], ingestion_status.stamp(1800001200))
            (root / 'sync/drive_ingest_cooldown.json').write_text(
                json.dumps({'until_epoch': 1800001800}), encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['cooldown_provider'], 'both')
            self.assertEqual(result['operation']['retry_after'], ingestion_status.stamp(1800001800))
            self.assertNotIn('PRIVATE', json.dumps(result))

    def test_source_backoff_and_budget_from_supervisor_are_allowlisted(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            state = {'schema_version': 2, 'state': 'waiting_for_youtube_cooldown',
                     'cooldown_provider': 'youtube', 'until_epoch': 1800001200,
                     'private_root_ceiling_bytes': 16_000_000_000}
            target = root / 'sync/drive_ingest_resume_state.json'
            target.write_text(json.dumps(state), encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'cooldown')
            self.assertEqual(result['operation']['cooldown_provider'], 'youtube')
            self.assertEqual(result['storage']['ceiling_bytes'], 16_000_000_000)
            state.update(state='retry_budget_exhausted', private_root_ceiling_bytes=19_000_000_000,
                         cooldown_provider='PRIVATE VALUE')
            target.write_text(json.dumps(state), encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'paused')
            self.assertEqual(result['storage']['ceiling_bytes'], 17_000_000_000)
            self.assertNotIn('PRIVATE VALUE', json.dumps(result))

    def test_pre_begin_native_refusal_updates_source_deadline_without_counting_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps({
                'video_id': 'PRIVATE-ID', 'error_class': 'forbidden', 'retry_not_before_epoch': 1800001200}) + '\n')
            (root / 'sync/drive_caption_manifest.jsonl').write_text(json.dumps({
                'video_id': 'PRIVATE-ID', 'error_class': 'rate_limited', 'retry_not_before_epoch': 1800005000}) + '\n')
            (root / 'sync/STOP_DRIVE_INGEST').touch()
            target = root / 'sync/native_batch_source_cooldown.json'
            valid = {'schema_version': 1, 'endpoint': 'youtube_native_audio', 'source_error_class': 'bot_check',
                     'retry_not_before_epoch': 1800002400, 'private_evidence': 'PRIVATE TOKEN PATH'}
            target.write_text(json.dumps(valid))
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'paused')
            self.assertEqual(result['operation']['cooldown_provider'], 'youtube')
            self.assertEqual(result['operation']['retry_after'], ingestion_status.stamp(1800002400))
            self.assertEqual(result['operation']['caption_retry_after'], ingestion_status.stamp(1800005000))
            self.assertEqual(result['counts']['verified_pairs'], 0)
            self.assertEqual(result['counts']['unavailable'], 0)
            self.assertNotIn('PRIVATE', json.dumps(result))
            for invalid in ({**valid, 'endpoint': 'other'}, {**valid, 'source_error_class': 'network'},
                            {**valid, 'retry_not_before_epoch': '1800009000'}, {**valid, 'retry_not_before_epoch': float('nan')}):
                with self.subTest(invalid=invalid):
                    target.write_text(json.dumps(invalid))
                    unchanged = ingestion_status.snapshot(root, now=1800000000)
                    self.assertEqual(unchanged['operation']['retry_after'], ingestion_status.stamp(1800001200))

    def test_private_fields_never_enter_public_counts_and_audio_alone_is_not_a_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'jobs').mkdir()
            (root / 'sync').mkdir()
            for name in ('queue_newest20_enriched.csv', 'queue_newest50_enriched.csv', 'queue_youtube_all_merged.csv'):
                with (root / 'jobs' / name).open('w', newline='') as handle:
                    writer = csv.DictWriter(handle, fieldnames=['video_id','channel_dir','title'])
                    writer.writeheader()
                    writer.writerow({'video_id':'PRIVATEidA1','channel_dir':'PRIVATE-PERSON','title':'SECRET TITLE'})
                    writer.writerow({'video_id':'PRIVATEidB1','channel_dir':'PRIVATE-PERSON','title':'SECRET TITLE'})
            destination = 'etdrive:04 Audio/PRIVATE-PERSON/Videos/PRIVATEidA1'
            first = {'video_id':'PRIVATEidA1','channel_dir':'PRIVATE-PERSON','status':'deleted','bytes':10,'drive_id':'SECRET DRIVE ID',
                     'md5':'PRIVATE HASH','sha256':'PRIVATE HASH','title':'SECRET TITLE',
                     'url':'https://private.invalid/SECRET','path':'audio/PRIVATEidA1.webm','token':'SECRET TOKEN',
                     'remote': destination+'.webm',
                     'metadata':{'drive_id':'PRIVATE METADATA ID','md5':'PRIVATE HASH','sha256':'PRIVATE HASH',
                                 'remote':destination+'.info.json'}}
            second = dict(first, video_id='PRIVATEidB1', metadata=None)
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps(first)+'\n'+json.dumps(second)+'\n')
            result = ingestion_status.snapshot(root, now=1800000000)
        serialized = json.dumps(result)
        for value in ('PRIVATEid','PRIVATE-PERSON','SECRET','PRIVATE HASH',str(root),'https://'):
            self.assertNotIn(value, serialized)
        self.assertEqual(result['scope'], 'local_youtube_collection')
        self.assertEqual(result['counts']['verified_pairs'], 1)
        self.assertEqual(result['counts']['awaiting_upload'], 1)
        self.assertEqual(result['stages'][0]['total'], 2)

    def test_text_availability_preserves_partial_caption_inventory_and_requires_archived_proofs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            def audio(video):
                remote = f'etdrive:04 Audio/PRIVATE-PERSON/Videos/{video}'
                return {'video_id':video, 'channel_dir':'PRIVATE-PERSON', 'status':'deleted',
                        'path':f'audio/{video}.webm', 'remote':remote+'.webm', 'bytes':10,
                        'drive_id':'SECRET AUDIO ID', 'md5':'a'*32, 'sha256':'b'*64,
                        'metadata':{'drive_id':'SECRET META ID','md5':'c'*32,'sha256':'d'*64,
                                    'remote':remote+'.info.json'}}
            def caption(video, status='deleted', tracks=1, **changes):
                value = {'video_id':video,'channel_dir':'PRIVATE-PERSON', 'status':status,
                         'policy':ingestion_status.CAPTION_POLICY, 'captured_at':'2026-11-16T00:00:00Z',
                         'unresolved':[], 'text':'SECRET CAPTION TEXT', 'tracks':[]}
                for n in range(tracks):
                    identity = f'published.en.{n}'
                    value['tracks'].append({'track_id':identity,'language':'en','kind':'published',
                        'machine_translated':False,'status':'deleted','bundle':{'bytes':20,'drive_id':'SECRET TRACK ID',
                            'md5':'e'*32,'sha256':'f'*64,
                            'remote':f'etdrive:04 Audio/PRIVATE-PERSON/Videos/{video}.captions.{identity}.zip'}})
                value.update(changes)
                return value
            a, b, c, d, e, f, g, h = [f'PRIVATEid{n}1' for n in 'ABCDEFGH']
            audio_rows = [audio(video) for video in (a, b, e, f, g)]
            rows = [caption(a, tracks=2), caption(b, status='pending', tracks=2),
                    caption(c, status='none', tracks=0), caption(d, status='none', tracks=0, unresolved=['access']),
                    caption(f), caption(g, policy='outdated'), caption(h)]
            rows[1]['tracks'][1]['status'] = 'ready'
            rows[1]['unresolved'] = [{'reason':'original_origin_unproven'}]
            rows[4]['tracks'][0]['bundle']['remote'] = 'etdrive:WRONG/PRIVATE/file.zip'
            asr = [{'video_id':video, 'channel_dir':'PRIVATE-PERSON', 'run_id':'test-run',
                    'status':'verified', 'artifact_kind':'asr_bundle', 'bytes':30,
                    'drive_id':'SECRET ASR ID', 'md5':'1'*32, 'sha256':'2'*64,
                    'source_audio_drive_id':'SECRET AUDIO ID', 'source_audio_sha256':'b'*64,
                    'remote':f'etdrive:04 Audio/PRIVATE-PERSON/Videos/{video}/ASR/test-run/test-run.zip'}
                   for video in (a, e)]
            for name, records in [('drive_ingest_manifest.jsonl',audio_rows),
                                  ('drive_caption_manifest.jsonl',rows), ('asr_manifest.jsonl',asr)]:
                (root / 'sync' / name).write_text(''.join(json.dumps(row)+'\n' for row in records), encoding='utf-8')
            result = ingestion_status.snapshot(root, now=1800000000)
        self.assertEqual(result['counts']['verified_pairs'], 5)
        self.assertEqual(result['counts']['caption_verified_videos'], 2)
        self.assertEqual(result['counts']['caption_verified_tracks'], 4)
        self.assertEqual(result['counts']['caption_none_english'], 1)
        self.assertEqual(result['counts']['caption_pending_videos'], 5)
        self.assertEqual(result['counts']['asr_verified_videos'], 2)
        self.assertEqual(result['counts']['caption_text_available_videos'], 2)  # a, b only
        self.assertEqual(result['counts']['caption_inventory_review_videos'], 1)  # b remains incomplete
        self.assertEqual(result['counts']['text_available_videos'], 3)  # a, b, e; a is not double-counted
        self.assertEqual(result['counts']['text_missing_videos'], 2)  # wrong proof and outdated policy
        self.assertEqual(result['counts']['text_inventory_complete_videos'], 2)  # a, e
        self.assertEqual(result['counts']['text_artifact_videos'], 2)  # compatibility semantics
        self.assertEqual(result['counts']['text_pending_videos'], 3)
        self.assertNotIn('speech_coverage', result['counts'])
        for private in ('PRIVATE', 'SECRET', 'etdrive:', 'WRONG', str(root)):
            self.assertNotIn(private, json.dumps(result))

    def test_caption_deadline_is_independent_of_resolved_audio_and_latest_per_lane(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps({
                'video_id':'PRIVATEidA1','status':'deleted'})+'\n', encoding='utf-8')
            rows = [{'video_id':'PRIVATEidA1','error_class':'forbidden','retry_not_before_epoch':1800009000},
                    {'video_id':'PRIVATEidA1','status':'pending','error_class':'drive_rate_limited',
                     'source_error_class':'rate_limited',
                     'retry_not_before_epoch':1800001200,'error':'SECRET URL'}]
            target = root / 'sync/drive_caption_manifest.jsonl'
            target.write_text(''.join(json.dumps(row)+'\n' for row in rows), encoding='utf-8-sig')
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertIsNone(result['operation']['cooldown_provider'])
            self.assertIsNone(result['operation']['retry_after'])
            self.assertEqual(result['operation']['state'], 'ready')
            self.assertEqual(result['operation']['caption_state'], 'cooldown')
            self.assertEqual(result['operation']['caption_retry_after'], ingestion_status.stamp(1800001200))
            (root / 'sync/drive_ingest_resume_state.json').write_text(json.dumps({
                'schema_version':2, 'state':'waiting_for_caption_cooldown', 'await_caption_backfill':True,
                'until_epoch':1800001200, 'cooldown_provider':'captions'}), encoding='utf-8')
            waiting = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(waiting['operation']['state'], 'ready')
            self.assertIsNone(waiting['operation']['retry_after'])
            (root / 'sync/drive_ingest_resume_state.json').write_text(json.dumps({
                'schema_version':2, 'state':'waiting_for_youtube_cooldown', 'source_until_epoch':1800001200,
                'until_epoch':1800001201, 'cooldown_provider':'youtube'}), encoding='utf-8')
            migrated = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(migrated['operation']['state'], 'ready')
            self.assertIsNone(migrated['operation']['retry_after'])
            self.assertNotIn('SECRET', json.dumps(result))
            (root / 'sync/drive_ingest_resume_state.json').unlink()
            with target.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps({'video_id':'PRIVATEidA1','status':'deleted'})+'\n')
            self.assertNotEqual(ingestion_status.snapshot(root, now=1800000000)['operation']['state'], 'cooldown')

    def test_cooldown_and_stop_are_reported_without_claiming_a_running_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sync').mkdir()
            (root / 'sync/drive_ingest_cooldown.json').write_text(json.dumps({'until_epoch':1800000600,'reason':'PRIVATE ERROR'}))
            self.assertEqual(ingestion_status.snapshot(root, now=1800000000)['operation']['state'], 'cooldown')
            (root / 'sync/STOP_DRIVE_INGEST').touch()
            result = ingestion_status.snapshot(root, now=1800000000)
            self.assertEqual(result['operation']['state'], 'paused')
            self.assertNotIn('PRIVATE ERROR', json.dumps(result))


if __name__ == "__main__":
    unittest.main()
