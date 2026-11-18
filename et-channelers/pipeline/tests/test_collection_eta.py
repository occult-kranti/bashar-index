"""Offline estimator failures: mixed timings, missing data, proof, privacy and stages."""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collection_eta as eta


def row(n=0, duration=100, channel="invented"):
    return {"video_id": f"{n:011d}", "channel_dir": channel, "tab": "videos", "duration_s": str(duration)}


def receipt(item, size=10000):
    destination = f"etdrive:04 Audio/{item['channel_dir']}/Videos/{item['video_id']}"
    return dict(item, status="deleted", path=f"audio/invented/Videos/{item['video_id']}.webm",
                remote=destination + ".webm", drive_id="private-object", bytes=size,
                md5="a" * 32, sha256="b" * 64, downloaded_at="2026-11-16T00:00:00Z",
                verified_at="2026-11-17T00:00:00Z",
                metadata=dict(remote=destination + ".info.json", drive_id="private-meta-object",
                              bytes=100, md5="c" * 32, sha256="d" * 64))


class CollectionEtaTests(unittest.TestCase):
    def operational_fixture(self, root):
        live = root / 'live'; live.mkdir()
        (root / 'sync').mkdir()
        item = row()
        (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps(receipt(item)), encoding='utf-8')
        values = {
            'series-state.json': dict(status='finished_with_holds', proposal_sha256='a' * 64,
                authorization_sha256='b' * 64, frames={'0': dict(phase='drained', outcomes={
                    item['video_id']: {'status': 'canonical_verified'}, 'PRIVATE-ID': {'status': 'uncertain'}})}),
            'source-invocation.json': dict(at='2026-11-17T23:50:00Z', series_proposal_sha256='a' * 64,
                root_authorization_sha256='b' * 64, private_token='SECRET'),
            'source-process-exit.json': dict(at='2026-11-18T00:10:00Z', exit_code=0),
            'native-allocation-released.json': dict(lease_id='PRIVATE-LEASE')}
        for name, value in values.items():
            (live / name).write_text(json.dumps(value), encoding='utf-8')
        for name, counts in [('next.json', {'selected': 30}), ('campaign.json', {'selected': 1153, 'frames': 58})]:
            (root / name).write_text(json.dumps({'counts': counts}), encoding='utf-8')
        return live

    def test_terminal_service_includes_full_waits_and_counts_verified_success_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); live = self.operational_fixture(root)
            status = {'scope': 'local_youtube_collection', 'generated_at': '2026-11-18T00:11:00Z',
                      'counts': {'verified_pairs': 1, 'asr_verified_videos': 0, 'private_token': 'SECRET'},
                      'stages': [{'key': 'newest20', 'total': 1420}]}
            result = eta.operational_estimate(root, live, root / 'next.json', root / 'campaign.json', status, now=1800000000)
            service = result['measured_service']
            self.assertEqual(service['elapsed_seconds'], 1200)
            self.assertEqual(service['first_pass_decisions'], 2)
            self.assertEqual(service['verified_native_pairs'], 1)
            self.assertEqual(service['held_or_uncertain_decisions'], 1)
            self.assertEqual(service['immediate_success_fraction'], .5)
            self.assertEqual(result['next_recovery_batch']['planning_active_hours'], [5, 10])
            self.assertIsNone(result['full_audio_and_text_completion_hours'])
            self.assertIsNone(result['guaranteed_completion_date'])
            for private in ('PRIVATE', 'SECRET', str(root), row()['video_id'], 'a' * 64):
                self.assertNotIn(private, json.dumps(result))
            status['native_lane'] = dict(kind='native_v4_campaign', state='running', source_count=600,
                                         cohort_index=1, completed_decisions=20)
            running = eta.operational_estimate(root, live, root / 'next.json', root / 'campaign.json', status)
            campaign = running['untouched_first_pass']
            self.assertEqual(campaign['state'], 'running_admitted_cohort')
            self.assertEqual(campaign['items'], 1133)
            self.assertEqual(campaign['selected_items'], 1153)
            self.assertEqual(campaign['later_prepared_items'], 553)

    def test_limited_v5_frame_keeps_prior_progress_without_crediting_startup_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); live = self.operational_fixture(root)
            status = {'scope': 'local_youtube_collection', 'native_lane': dict(kind='native_v5_source_hold', state='paused',
                frame_items=20, prior_completed_decisions=40)}
            result = eta.operational_estimate(root, live, root / 'next.json', root / 'campaign.json', status)
            campaign = result['untouched_first_pass']
            self.assertEqual(campaign['items'], 1113)
            self.assertEqual(campaign['completed_decisions'], 40)
            self.assertEqual(campaign['later_prepared_items'], 1093)
            self.assertEqual(campaign['state'], 'held_native_source')
            self.assertIsNone(result['guaranteed_completion_date'])

    def test_incomplete_or_mismatched_terminal_proof_cannot_calibrate_current_eta(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); live = self.operational_fixture(root)
            for name, changed in [('source-process-exit.json', {'exit_code': 1}),
                                  ('native-allocation-released.json', {}),
                                  ('series-state.json', {'status': 'running'}),
                                  ('source-invocation.json', {'root_authorization_sha256': 'c' * 64})]:
                path = live / name; original = path.read_text(encoding='utf-8')
                path.write_text(json.dumps(changed), encoding='utf-8')
                with self.subTest(name=name), self.assertRaises(ValueError):
                    eta.completed_service(root, live)
                path.write_text(original, encoding='utf-8')
            (root / 'sync/drive_ingest_manifest.jsonl').write_text('', encoding='utf-8')
            with self.assertRaises(ValueError):
                eta.completed_service(root, live)

    def test_completed_recovery_subtracts_decisions_without_treating_holds_as_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); service = self.operational_fixture(root)
            live = root / 'recovery'; live.mkdir()
            def put(name, value):
                path = live / name; data = json.dumps(value).encode(); path.write_bytes(data)
                return {'path': str(path), 'bytes': len(data), 'sha256': eta.hashlib.sha256(data).hexdigest()}
            pins = {key: put(key + '.json', {'private_proof': 'SECRET'}) for key in ('plan', 'settings', 'root_grant')}
            put('activation.json', dict(pins, lease_id='PRIVATE-LEASE'))
            invoked = dict(pid=123, process_creation_filetime='456', source_count=2,
                           started_at_epoch=eta.epoch('2026-11-18T00:20:00Z'), lease_id='PRIVATE-LEASE',
                           **{key + '_sha256': pin['sha256'] for key, pin in pins.items()})
            put('invocation.json', invoked)
            put('source-process-exit.json', dict(pid=123, process_creation_filetime='456', exit_code=3,
                                               at='2026-11-18T00:22:00Z'))
            terminal = dict(status='terminal', lease_id='PRIVATE-LEASE',
                parent_process_exited=True, child_audits_complete=True, owned_jobs_closed=True,
                matching_reservation_released=True, matching_lease_released=True,
                summary={'verified': 1, 'held': 1, 'pending': 0, 'skipped': 0, 'note': 'PRIVATE'},
                **{key + '_sha256': pin['sha256'] for key, pin in pins.items()})
            put('terminal.json', terminal)
            rec = dict(receipt(row()), native_batch_plan_sha256=pins['plan']['sha256'])
            (root / 'sync/drive_ingest_manifest.jsonl').write_text(json.dumps(rec), encoding='utf-8')
            (root / 'next.json').write_text(json.dumps({'counts': {'selected': 2}}), encoding='utf-8')
            status = {'scope': 'local_youtube_collection', 'counts': {}, 'stages': []}
            result = eta.operational_estimate(root, service, root / 'next.json', root / 'campaign.json', status,
                                              recovery_live=[live])
            recovery = result['next_recovery_batch']
            self.assertEqual(recovery['state'], 'terminal_with_holds')
            self.assertEqual(recovery['items'], 0)
            self.assertEqual(recovery['completed_verified_pairs'], 1)
            self.assertEqual(recovery['completed_held_items'], 1)
            self.assertEqual(recovery['planning_active_hours'], [0, 0])
            self.assertNotIn('PRIVATE', json.dumps(result)); self.assertNotIn('SECRET', json.dumps(result))
            with self.assertRaises(ValueError):
                eta.operational_estimate(root, service, root / 'next.json', root / 'campaign.json', status,
                                          recovery_live=[live, live])

    def test_mixed_receipt_wait_is_not_transfer_rate_and_progress_is_deduplicated(self):
        item = row()
        final = receipt(item)
        download = dict(final, status="download_complete", updated_at="2026-11-15T00:00:00Z")
        progress = json.dumps(dict(video_id=item['video_id'], status="downloading", bytes=8000,
                                   total_bytes=10000, elapsed_s=8)).encode()
        result = eta.estimate([item], [download, final], logs=[progress, progress], now=0)
        self.assertEqual(result['timing_evidence']['attempt_elapsed_seconds']['median'], 86400)
        self.assertEqual(result['timing_evidence']['download_to_first_verification_seconds']['median'], 86400)
        self.assertFalse(result['timing_evidence']['receipt_spans_used_as_bandwidth'])
        self.assertEqual(result['download_progress_evidence']['verified_objects_with_progress'], 1)
        self.assertEqual(result['download_progress_evidence']['per_worker_bytes_per_second']['median'], 1000)
        self.assertIn('assumed', result['assumptions']['download_rate_basis'])

    def test_bad_progress_cannot_supply_goodput(self):
        item = row(); final = receipt(item)
        lines = [dict(video_id=item['video_id'], status='downloading', bytes=1000, total_bytes=9999, elapsed_s=5),
                 dict(video_id=item['video_id'], status='downloading', bytes=1000, total_bytes=10000, elapsed_s=-1),
                 dict(video_id='99999999999', status='downloading', bytes=1000, total_bytes=10000, elapsed_s=5)]
        evidence = eta.progress_evidence(['\n'.join(map(json.dumps, lines)).encode()], {item['video_id']: final})
        self.assertEqual(evidence['verified_objects_with_progress'], 0)

    def test_unknown_durations_use_explicit_strata_without_duration_filter(self):
        rows = [row(i, (i + 1) * 100) for i in range(5)] + [row(5, '')]
        estimate = eta.duration_projection(rows, {}, set())
        self.assertEqual(estimate['unknown_duration_items'], 1)
        self.assertEqual(estimate['imputation_counts']['channel_tab'], 1)
        self.assertEqual(estimate['duration_seconds_scenarios'], [1700, 1800, 1960])
        long = eta.duration_projection([row(9, 100000)], {}, set())
        self.assertEqual(long['known_items_over_8_hours'], 1)
        self.assertEqual(long['known_duration_seconds'], 100000)

    def test_absent_durations_and_sizes_remain_unknown_not_zero_eta(self):
        result = eta.estimate([row(0, 'NaN'), row(1, -2)], [], now=0)
        stage = result['stages']['all_indexed']
        self.assertIsNone(stage['duration_seconds_scenarios'])
        self.assertEqual(stage['scenarios'], [])
        self.assertGreater(stage['metadata_start_floor_hours'], 0)
        self.assertIsNone(result['guaranteed_completion_date'])

    def test_unmeasured_shorts_do_not_inherit_long_video_durations(self):
        rows = [row(i, 10000) for i in range(5)] + [dict(row(5, ''), tab='shorts')]
        result = eta.duration_projection(rows, {}, set())
        self.assertEqual(result['duration_seconds_scenarios'], [50015, 50060, 50180])
        self.assertEqual(result['imputation_counts']['assumed_shorts_no_observations'], 1)
        self.assertEqual(result['unknown_duration_by_tab'], {'shorts': 1})

    def test_pipeline_uses_max_and_aggregate_upload_rate(self):
        result = eta.conditional_hours(11, 1000, 100, 20, 4, 10)
        self.assertAlmostEqual(result['overlapped_active_floor_hours'], 100 / 3600)
        self.assertAlmostEqual(result['upload_service_hours'], 50 / 3600)

    def test_only_complete_proof_removes_audio_from_remaining(self):
        first, second = row(), row(1)
        broken = receipt(second); del broken['metadata']['drive_id']
        result = eta.estimate([first, second], [receipt(first), broken], now=0)
        self.assertEqual(result['inventory']['queue_verified_pairs'], 1)
        self.assertEqual(result['stages']['all_indexed']['remaining_items'], 1)

    def test_caption_cooldown_does_not_block_audio_but_audio_cooldown_does(self):
        item = row()
        cap = dict(item, status='pending', error_class='rate_limited', retry_not_before_epoch=200)
        independent = eta.estimate([item], [], [cap], now=100)
        self.assertEqual(independent['status'], 'conditional_only')
        self.assertGreater(independent['cooldowns']['caption_current_wait_hours'], 0)
        audio = dict(item, status='error', source_error_class='forbidden', error_class='drive_read', retry_not_before_epoch=300)
        blocked = eta.estimate([item], [audio], [cap], now=100)
        self.assertEqual(blocked['status'], 'blocked')
        self.assertAlmostEqual(blocked['cooldowns']['audio_current_wait_hours'], 200 / 3600)
        self.assertTrue(blocked['no_finite_guaranteed_completion'])

    def test_stages_fail_closed_and_incremental_fifty_does_not_duplicate_twenty(self):
        rows = [row(i) for i in range(4)]
        with self.assertRaises(ValueError):
            eta.estimate(rows, [], stage_rows={'newest20': rows[:2], 'newest50_inclusive': rows[2:]})
        stages = {'newest20': rows[:1], 'newest50_inclusive': rows[:3], 'remaining_archive': rows[3:]}
        result = eta.estimate(rows, [receipt(rows[0])], stage_rows=stages, now=0)
        self.assertEqual(result['stages']['newest50_incremental']['remaining_items'], 2)
        expected = sum(result['stages'][name]['scenarios'][1]['overlapped_active_floor_hours']
                       for name in ('newest20', 'newest50_incremental', 'remaining_archive'))
        self.assertEqual(result['staged_archive_active_floor_hours']['central'], expected)

    def test_isolated_cli_outputs_only_aggregates_and_does_not_modify_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root/'jobs').mkdir(); (root/'sync').mkdir()
            item = dict(row(), title='PRIVATE TEXT MUST NOT LEAK', url='https://private.invalid/signed')
            handle = io.StringIO(); writer = csv.DictWriter(handle, fieldnames=list(item)); writer.writeheader(); writer.writerow(item)
            queue = root/'jobs/queue_youtube_all_merged.csv'; queue.write_text(handle.getvalue(), encoding='utf-8')
            journal = root/'sync/drive_ingest_manifest.jsonl'
            journal.write_text(json.dumps(receipt(item))+'\n{torn', encoding='utf-8')
            before = {path: path.read_bytes() for path in (queue, journal)}
            process = subprocess.run([sys.executable, '-I', str(Path(eta.__file__)), '--root', str(root)],
                                     capture_output=True, text=True, timeout=20)
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(process.stdout)
            self.assertEqual(result['malformed_receipt_records_skipped']['audio'], 1)
            for secret in ('PRIVATE TEXT', 'private.invalid', 'private-object', 'invented', str(root), item['video_id']):
                self.assertNotIn(secret, process.stdout)
            self.assertEqual(before, {path: path.read_bytes() for path in before})

    def test_cli_cannot_overwrite_an_external_queue_input(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); root = base/'private'; root.mkdir()
            queue = base/'queue.csv'
            queue.write_text('video_id,channel_dir,tab,duration_s\n00000000000,invented,videos,100\n', encoding='utf-8')
            original = queue.read_bytes()
            process = subprocess.run([sys.executable, '-I', str(Path(eta.__file__)), '--root', str(root),
                                      '--queue', str(queue), '--out', str(queue)],
                                     capture_output=True, text=True, timeout=20)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(queue.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
