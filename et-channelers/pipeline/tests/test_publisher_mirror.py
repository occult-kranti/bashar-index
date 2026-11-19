"""Fake HTTPS/Drive and a fake probe: no real media, subprocess or network."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from pipeline import publisher_mirror as m
from pipeline import rumble_public_source
from pipeline.tests.test_rumble_public_source import ACCOUNT, CDN, WATCH, source_fixture


AUDIO = b"invented-audio-fixture" * 100
CAPTION = b"WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nInvented fixture words.\n"


class Response(io.BytesIO):
    def __init__(self, body, *, declared=None, status=200):
        super().__init__(body)
        self.status = status
        self.headers = {"Content-Length": str(len(body) if declared is None else declared)}


class Transport:
    def __init__(self):
        self.calls = []
        self.fail_caption = False
        self.fail_audio = False
        self.truncate = False
        self.lock = threading.Lock()

    def open(self, request, timeout):
        with self.lock:
            url = request.full_url
            self.calls.append(url)
        caption = url.endswith(".vtt")
        if (caption and self.fail_caption) or (not caption and self.fail_audio):
            raise HTTPError(url, 403, "private transport detail must never be logged", {}, None)
        body = CAPTION if caption else AUDIO
        return Response(body, declared=len(body) + 1 if self.truncate else None)


class Drive:
    def __init__(self):
        self.objects = {}
        self.copies = self.stats = 0
        self.missing_id = False
        self.bad_hash = False

    def copy_batch(self, root, remote, manifest, transfers):
        assert transfers == 2
        self.copies += 1
        for relative in manifest.read_text().splitlines():
            self.objects[relative] = (root / relative).read_bytes()

    def stat_batch(self, remote, paths, manifest):
        self.stats += 1
        return {p: {"Size": len(self.objects[p]), "Hashes": {"MD5": "0" * 32 if self.bad_hash else hashlib.md5(self.objects[p]).hexdigest()},
                    **({} if self.missing_id else {"ID": "fixture-" + hashlib.sha256(p.encode()).hexdigest()[:20]})} for p in paths}


class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "sync").mkdir()
        (self.root / "sync/STOP_DRIVE_INGEST").write_text("fixture")
        self.transport, self.drive = Transport(), Drive()
        self.probes = 0
        self.item = self.item_fixture("abcdefghijk")
        self.plan = self.root / "plan.json"
        self.put(self.plan, {"schema_version": 1, "items": [self.item]})
        self.settings = m.Settings(self.root, self.plan, "fixture-owner", "fixture-lease",
            [self.root, Path(sys.prefix).resolve(), Path(m.__file__).resolve().parents[2]],
            "fixture:Audio", "no-subprocess", 64_000_000, workers=2)
        self.put(self.root / "sync/analysis_resource_plan.json", {"accounting_cap_bytes": m.MAX_MANAGED,
            "collector_dispatch_allowed": False, "reservations": [{"state": "active", "lease_id": self.settings.lease_id,
            "owner": self.settings.owner, "max_bytes": self.settings.spool_cap_bytes}]})
        self.bind()
        tree = m.native.tree_bytes
        self.tree_patch = patch.object(m.native, "tree_bytes", side_effect=lambda p: tree(p) if Path(p).resolve().is_relative_to(self.root) else 0)
        self.tree_patch.start()
        self.addCleanup(self.tree_patch.stop)

    def put(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(m.encoded(value))

    def item_fixture(self, video):
        raw = {"title": "Invented title", "description": "Invented publisher description", "audio": {"url": "https://cdn.example.test/" + video + ".aac"},
               "caption": {"url": "https://cdn.example.test/" + video + ".vtt"}, "http_headers": {"Authorization": "private-fixture-value"}}
        path = self.root / (video + ".json")
        self.put(path, raw)
        return {"provider": "Fixture", "channel_dir": "fixture-person", "associated_youtube_id": video, "watch_page_id": "watch-" + video,
                "association_method": "publisher_owner_title_date_duration", "association_qualification": "Qualified publisher edition; edit identity unverified.",
                "exact_youtube_crossreference": False, "human_verified": False,
                "accepted_metadata": {"path": path.name, "sha256": m.sha(path.read_bytes())}, "allowed_hosts": ["cdn.example.test"],
                "audio": {"url_pointer": ["audio", "url"], "maximum_bytes": 10_000, "metadata_declared_bytes": len(AUDIO) - 1,
                          "codec": "aac", "extension": "aac", "duration_seconds": 10},
                "captions": [{"track_id": "en-auto", "provider_language_key": "en-auto", "language": "en", "kind": "automatic_original",
                              "translated": False, "raw_format": "vtt", "url_pointer": ["caption", "url"], "maximum_bytes": 4096}]}

    def bind(self):
        self.put(self.root / "sync/publisher_mirror_lease.json", {"state": "active", "owner": self.settings.owner, "lease_id": self.settings.lease_id,
             "expires_at_epoch": time.time() + 120, "worker_sha256": m.sha(Path(m.__file__).read_bytes()), "plan_sha256": m.sha(self.plan.read_bytes()),
             "remote": self.settings.remote, "max_workers": self.settings.workers, "spool_cap_bytes": self.settings.spool_cap_bytes,
             "managed_roots": [str(p) for p in self.settings.managed_roots]})

    def probe(self, path, selected, executable):
        self.probes += 1
        self.assertEqual(path.read_bytes(), AUDIO)
        return {"duration_seconds": selected["durationMs"] / 1000, "codec": "aac", "method": "offline_fixture"}

    def batch(self):
        return m.MirrorBatch(self.settings, self.drive, opener=self.transport, probe=self.probe,
                             disk_free=lambda: m.DISK_FLOOR + 10_000_000_000)

    def test_public_rumble_descriptors_feed_verified_audio_and_captions(self):
        descriptor = rumble_public_source.published_descriptors(*source_fixture(len(AUDIO)), ACCOUNT, WATCH)
        metadata = self.root / 'accepted-publisher-edition.json'
        self.put(metadata, descriptor)
        pin = m.sha(metadata.read_bytes())
        self.item.update(provider=descriptor['provider'], watch_page_id=descriptor['watch_page_id'],
                         declared_embed_id=descriptor['declared_embed_id'], allowed_hosts=['hugh.cdn.rumble.cloud'],
                         accepted_metadata={'path': metadata.name, 'sha256': pin})
        self.item['audio'].update(url_pointer=['audio', '192', 'url'],
                                  metadata_declared_bytes=descriptor['audio']['192']['bytes'],
                                  duration_seconds=descriptor['duration_seconds'])
        self.item['captions'][0]['url_pointer'] = ['captions', 'en-auto', 'url']
        self.put(self.plan, {'schema_version': 1, 'items': [self.item]})
        self.bind()

        result = self.batch().run()
        self.assertEqual((result['verified'], self.probes, self.drive.copies, self.drive.stats), (1, 1, 1, 1))
        self.assertCountEqual(self.transport.calls, [CDN + '/audio.aac', CDN + '/auto.vtt'])
        record = json.loads((self.root / 'sync/publisher_mirror_manifest.jsonl').read_text())
        self.assertTrue(m.complete_receipt(record, m.load_items(self.root, self.plan)[1][0], self.settings.remote))
        self.assertEqual(record['accepted_api_sha256'], pin)
        self.assertEqual(record['audio']['sha256'], m.sha(AUDIO))
        self.assertEqual(len(self.drive.objects), 3)
        self.assertNotIn('viewer_id', metadata.read_text())

    def test_full_batch_verifies_three_objects_before_cleanup_and_skips_existing(self):
        result = self.batch().run()
        self.assertEqual((result["verified"], result["held"], self.probes, self.drive.copies, self.drive.stats), (1, 0, 1, 1, 1))
        self.assertEqual(len(self.drive.objects), 3)
        journal = (self.root / "sync/publisher_mirror_manifest.jsonl").read_text()
        self.assertNotIn("https://", journal)
        self.assertNotIn("private-fixture", journal)
        record = json.loads(journal)
        self.assertTrue(m.complete_receipt(record, m.load_items(self.root, self.plan)[1][0], self.settings.remote))
        self.assertEqual(record["caption_bundle"]["coverage"]["every_word_coverage_verified"], False)
        self.assertFalse(list((self.root / "publisher_mirror/files").rglob("*.aac")))
        before = (len(self.transport.calls), self.drive.copies, self.drive.stats)
        again = self.batch().run()
        self.assertEqual(again["items"][0]["status"], "already_verified")
        self.assertEqual((len(self.transport.calls), self.drive.copies, self.drive.stats), before)
        provenance = next(json.loads(v) for p, v in self.drive.objects.items() if p.endswith("provenance.json"))
        self.assertEqual(provenance["publisher_metadata"]["title"], "Invented title")
        self.assertNotIn("https://", json.dumps(provenance))
        self.assertNotIn("Authorization", json.dumps(provenance))

    def test_missing_drive_id_retains_all_then_resumes_without_source_or_probe(self):
        self.drive.missing_id = True
        held = self.batch().run()
        self.assertEqual(held["held"], 1)
        self.assertEqual(held["items"][0]["error_class"], "drive_id_missing")
        self.assertEqual(len(list((self.root / "publisher_mirror/files").rglob("publisher-audio.aac"))), 1)
        self.assertFalse((self.root / "sync/publisher_mirror_manifest.jsonl").exists())
        before = len(self.transport.calls)
        self.drive.missing_id = False
        self.assertEqual(self.batch().run()["verified"], 1)
        self.assertEqual(len(self.transport.calls), before)
        self.assertEqual(self.probes, 1)

    def test_truncated_transfer_remains_held_and_is_not_automatically_retried(self):
        self.transport.truncate = True
        first = self.batch().run()
        self.assertEqual(first["items"][0]["error_class"], "publisher_body_truncated")
        before = len(self.transport.calls)
        self.transport.truncate = False
        second = self.batch().run()
        self.assertEqual(second["items"][0]["error_class"], "partial_requires_review")
        self.assertEqual(len(self.transport.calls), before)
        self.assertEqual(self.probes, 0)

    def test_caption_refusal_does_not_discard_verified_audio(self):
        self.transport.fail_caption = True
        result = self.batch().run()
        self.assertEqual(result["items"][0]["caption_state"], "pending")
        record = json.loads((self.root / "sync/publisher_mirror_manifest.jsonl").read_text())
        self.assertEqual(len(self.drive.objects), 2)
        self.assertFalse(m.complete_receipt(record, m.load_items(self.root, self.plan)[1][0], self.settings.remote))
        self.assertTrue((self.root / "sync/publisher_mirror_source_cooldowns.json").exists())
        self.assertFalse((self.root / "sync/drive_ingest_manifest.jsonl").exists())

    def test_parallel_source_refusal_stops_future_work_and_preserves_youtube_state(self):
        items = [self.item] + [self.item_fixture("abcdefghij" + c) for c in "lmno"]
        self.put(self.plan, {"schema_version": 1, "items": items})
        self.bind()
        self.transport.fail_audio = True
        original = b'{"retry_not_before_epoch":9999999999}\n'
        (self.root / "sync/native_batch_source_cooldown.json").write_bytes(original)
        result = self.batch().run()
        self.assertEqual(result["held"], 5)
        self.assertLessEqual(len(self.transport.calls), 2)
        self.assertEqual((self.root / "sync/native_batch_source_cooldown.json").read_bytes(), original)

    def test_metadata_hash_and_translation_policy_fail_before_transport(self):
        (self.root / self.item["accepted_metadata"]["path"]).write_text("changed")
        with self.assertRaisesRegex(m.MirrorError, "accepted_metadata_changed"):
            self.batch()
        self.assertFalse(self.transport.calls)
        self.item = self.item_fixture("abcdefghijk")
        self.item["captions"][0]["translated"] = True
        self.put(self.plan, {"schema_version": 1, "items": [self.item]})
        with self.assertRaisesRegex(m.MirrorError, "caption_language_policy"):
            self.batch()

    def test_whole_item_reservation_defers_without_duration_filter_or_get(self):
        self.item["audio"]["duration_seconds"] = 86_400
        self.item["audio"]["maximum_bytes"] = self.settings.spool_cap_bytes
        self.put(self.plan, {"schema_version": 1, "items": [self.item]})
        self.bind()
        result = self.batch().run()
        self.assertEqual(result["items"][0]["error_class"], "spool_storage_deferred")
        self.assertFalse(self.transport.calls)

    def test_other_reservations_and_expired_owner_prevent_requests(self):
        plan = m.read(self.root / "sync/analysis_resource_plan.json")
        plan["reservations"].append({"state": "active", "lease_id": "other", "max_bytes": m.MAX_MANAGED})
        self.put(self.root / "sync/analysis_resource_plan.json", plan)
        with self.assertRaisesRegex(m.MirrorError, "managed_storage_deferred"):
            self.batch().run()
        lease = m.read(self.root / "sync/publisher_mirror_lease.json")
        lease["expires_at_epoch"] = time.time() - 1
        self.put(self.root / "sync/publisher_mirror_lease.json", lease)
        with self.assertRaisesRegex(m.MirrorError, "publisher_lease_expired"):
            self.batch().run()
        self.assertFalse(self.transport.calls)

    def test_crash_between_owned_deletions_recovers_from_durable_receipt(self):
        original_remove = m.storage.Budget.remove
        removed = []
        def interrupted(budget, path, *args, **kwargs):
            if path.name == "provenance.json" and removed:
                raise OSError("fixture cleanup interruption")
            result = original_remove(budget, path, *args, **kwargs)
            if path.name == "publisher-audio.aac":
                removed.append(path)
            return result
        with patch.object(m.storage.Budget, "remove", interrupted):
            result = self.batch().run()
        self.assertEqual(result["held"], 1)
        self.assertTrue(removed)
        record = json.loads((self.root / "sync/publisher_mirror_manifest.jsonl").read_text())
        self.assertEqual(record["status"], "verified")
        calls, copies = len(self.transport.calls), self.drive.copies
        result = self.batch().run()
        self.assertEqual(result["verified"], 1)
        self.assertEqual((len(self.transport.calls), self.drive.copies), (calls, copies))
        self.assertEqual(self.drive.stats, 2)

    def test_changed_artifact_and_wrong_remote_hash_never_delete(self):
        self.drive.bad_hash = True
        first = self.batch().run()
        self.assertEqual(first["held"], 1)
        audio = next((self.root / "publisher_mirror/files").rglob("publisher-audio.aac"))
        audio.write_bytes(b"unexpected replacement")
        self.drive.bad_hash = False
        calls, copies = len(self.transport.calls), self.drive.copies
        second = self.batch().run()
        self.assertEqual(second["items"][0]["error_class"], "local_artifact_changed")
        self.assertTrue(audio.exists())
        self.assertEqual((len(self.transport.calls), self.drive.copies), (calls, copies))

    def test_completed_audio_relocation_checkpoint_is_recoverable(self):
        batch = self.batch()
        with m.storage.exclusive_lock(self.root):
            batch.guard(force=True)
            batch.spool.mkdir()
            batch.files.mkdir()
            batch.budget = m.storage.Budget(self.root, m.MAX_MANAGED, 0, m.DISK_FLOOR, reserve=m.CONTROL, cached=True)
            job = batch.spool / "jobs/fixture"
            job.mkdir(parents=True)
            old = job / "audio.aac"
            moved = batch.files / "publisher-audio.aac"
            moved.write_bytes(AUDIO)
            proof = m.storage.hash_file(moved)
            state = {"downloads": {"audio": {"proof": proof, "relative": old.relative_to(self.root).as_posix()}},
                     "audio_move": {"from": old.relative_to(self.root).as_posix(), "to": moved.relative_to(self.root).as_posix()}}
            found = batch.download(batch.items[0], state, job / "state.json", "audio", batch.items[0]["audio"], old)
            self.assertEqual(found, proof)
            self.assertEqual(state["downloads"]["audio"]["relative"], moved.relative_to(self.root).as_posix())
        self.assertFalse(self.transport.calls)


class PublisherFormats(unittest.TestCase):
    setUp = MirrorTests.setUp
    put = MirrorTests.put
    item_fixture = MirrorTests.item_fixture
    bind = MirrorTests.bind
    probe = MirrorTests.probe
    batch = MirrorTests.batch

    def test_qualified_previous_policy_still_passes(self):
        MirrorTests.test_full_batch_verifies_three_objects_before_cleanup_and_skips_existing(self)

    def test_exact_rss_link_is_preserved_but_never_claims_native_or_edit_equality(self):
        self.item.update(association_method='publisher_rss_exact_youtube_id', exact_youtube_crossreference=True,
                         original_youtube_link='https://www.youtube.com/watch?v=abcdefghijk')
        self.item['audio'].update(codec='mp3', extension='mp3')
        self.put(self.plan, {'schema_version': 1, 'items': [self.item]})
        self.bind()
        result = self.batch().run()
        self.assertEqual(result['verified'], 1)
        record = json.loads((self.root / 'sync/publisher_mirror_manifest.jsonl').read_text())
        self.assertEqual(record['kind'], 'publisher_mirror_audio_variant')
        self.assertEqual(record['original_youtube_link'], self.item['original_youtube_link'])
        self.assertFalse(record['recording_equivalence_verified'])
        self.assertFalse(record['native_youtube_bytes'])
        self.assertTrue(m.complete_receipt(record, m.load_items(self.root, self.plan)[1][0], self.settings.remote))
        record['original_youtube_link'] = 'https://www.youtube.com/watch?v=zzzzzzzzzzz'
        self.assertFalse(m.complete_receipt(record, m.load_items(self.root, self.plan)[1][0], self.settings.remote))

    def test_spoofed_or_wrong_youtube_links_are_not_accepted(self):
        for url in ('https://youtube.com.evil.test/watch?v=abcdefghijk', 'https://www.youtube.com/watch?v=zzzzzzzzzzz',
                    'https://www.youtube.com/watch?v=abcdefghijk&v=zzzzzzzzzzz', 'https://owner@www.youtube.com/watch?v=abcdefghijk',
                    'https://www.youtube.com/watch?v=abcdefghijk&token=private'):
            with self.subTest(url=url), self.assertRaises(m.MirrorError):
                m.exact_youtube_link(url, 'abcdefghijk')
        self.assertEqual(m.exact_youtube_link('https://youtu.be/abcdefghijk', 'abcdefghijk'), 'https://youtu.be/abcdefghijk')

    def test_mp3_probe_is_publisher_only_and_audio_only(self):
        before = dict(m.native.CODECS)
        value = {'streams': [{'codec_type': 'audio', 'codec_name': 'mp3', 'nb_read_packets': '20'}], 'format': {'duration': '7935.722676', 'format_name': 'mp3'}}
        result = SimpleNamespace(returncode=0, stderr='', stdout=json.dumps(value))
        with patch.object(m.subprocess, 'run', return_value=result) as call:
            proof = m.inspect_publisher_audio(Path('fictional.mp3'), {'codec': 'mp3', 'durationMs': 7935723}, 'fixture-ffprobe')
        self.assertEqual(call.call_count, 1)
        self.assertIn('-count_packets', call.call_args.args[0])
        self.assertEqual(proof['codec'], 'mp3')
        self.assertEqual(m.native.CODECS, before)
        value['streams'].append({'codec_type': 'video', 'codec_name': 'h264'})
        result.stdout = json.dumps(value)
        with patch.object(m.subprocess, 'run', return_value=result), self.assertRaisesRegex(m.MirrorError, 'publisher_audio_only'):
            m.inspect_publisher_audio(Path('fictional.mp3'), {'codec': 'mp3', 'durationMs': 7935723}, 'fixture-ffprobe')

    def test_publisher_rss_language_uncertainty_is_preserved(self):
        track = self.item['captions'][0]
        track.update(kind='published', translated=None, translation_status='not_declared', language='en-US',
                     language_basis='publisher_rss_channel', track_language_verified=False,
                     origin='publisher_provided_human_or_automatic_unspecified')
        self.put(self.plan, {'schema_version': 1, 'items': [self.item]})
        self.bind()
        self.assertEqual(self.batch().run()['verified'], 1)
        record = json.loads((self.root / 'sync/publisher_mirror_manifest.jsonl').read_text())
        self.assertEqual(record['caption_bundle']['translation_status'], 'not_declared')
        self.assertFalse(record['caption_bundle']['track_language_verified'])

    def test_adts_duration_uses_complete_frame_geometry_not_bitrate_estimate(self):
        # Synthetic ADTS LC framing; no encoded speech/decoder/model involved.
        count, length = 44964, 8
        header = bytes([255, 241, 76, 128, 1, 31, 252])
        audio = self.root / 'framing-fixture.aac'
        audio.write_bytes((header + b'\0') * count)
        value = {'streams': [{'codec_type': 'audio', 'codec_name': 'aac', 'profile': 'LC', 'sample_rate': '48000',
                             'channels': 2, 'nb_read_packets': str(count)}], 'format': {'duration': '933.341536', 'format_name': 'aac'}}
        result = SimpleNamespace(returncode=0, stderr='', stdout=json.dumps(value))
        with patch.object(m.subprocess, 'run', return_value=result) as call:
            proof = m.inspect_publisher_audio(audio, {'codec': 'aac', 'durationMs': 959000}, 'fixture-ffprobe')
        self.assertEqual(call.call_count, 1)
        self.assertEqual(proof['complete_adts_frames'], count)
        self.assertAlmostEqual(proof['duration_seconds'], 959.232)
        self.assertEqual(proof['ffprobe_format_duration_seconds'], 933.341536)
        audio.write_bytes(audio.read_bytes()[:-1])
        with self.assertRaisesRegex(m.MirrorError, 'publisher_adts_truncated'):
            m.adts_lc_duration(audio, value['streams'][0], count)

    def test_adts_unknown_profile_and_frame_count_disagreement_hold(self):
        audio = self.root / 'one-frame.aac'
        audio.write_bytes(bytes([255, 241, 76, 128, 1, 31, 252, 0]))
        stream = {'profile': 'HE-AAC', 'sample_rate': '48000', 'channels': 2}
        with self.assertRaisesRegex(m.MirrorError, 'publisher_adts_profile'):
            m.adts_lc_duration(audio, stream, 1)
        stream['profile'] = 'LC'
        with self.assertRaisesRegex(m.MirrorError, 'publisher_adts_probe_disagreement'):
            m.adts_lc_duration(audio, stream, 2)


class ScopedBreakerTests(unittest.TestCase):
    setUp = MirrorTests.setUp
    put = MirrorTests.put
    item_fixture = MirrorTests.item_fixture
    bind = MirrorTests.bind
    probe = MirrorTests.probe
    batch = MirrorTests.batch

    def test_audio_refusal_does_not_stop_another_provider(self):
        other = self.item_fixture('lmnopqrstuv')
        other['provider'] = 'OtherPublisher'
        self.put(self.plan, {'schema_version': 1, 'items': [self.item, other]})
        self.settings.workers = 1
        self.bind()
        original = self.transport.open
        def selective(request, timeout):
            if request.full_url.endswith('abcdefghijk.aac'):
                self.transport.calls.append(request.full_url)
                raise HTTPError(request.full_url, 403, 'fixture', {}, None)
            return original(request, timeout)
        self.transport.open = selective
        result = self.batch().run()
        self.assertEqual((result['verified'], result['held']), (1, 1))
        self.assertEqual(len(self.transport.calls), 3)
        scoped = m.read(self.root / 'sync/publisher_mirror_source_cooldowns.json')
        entry = next(iter(scoped['scopes'].values()))
        self.assertEqual((entry['provider'], entry['endpoint']), ('Fixture', 'audio'))
        self.assertIn('request_binding_sha256', entry)
        self.assertFalse((self.root / 'sync/publisher_mirror_source_cooldown.json').exists())

    def test_caption_refusal_allows_same_provider_audio_but_no_caption_retry(self):
        other = self.item_fixture('lmnopqrstuv')
        self.put(self.plan, {'schema_version': 1, 'items': [self.item, other]})
        self.settings.workers = 1
        self.bind()
        self.transport.fail_caption = True
        result = self.batch().run()
        self.assertEqual((result['verified'], result['caption_pending']), (2, 2))
        self.assertEqual(sum(url.endswith('.aac') for url in self.transport.calls), 2)
        self.assertEqual(sum(url.endswith('.vtt') for url in self.transport.calls), 1)
        entry = next(iter(m.read(self.root / 'sync/publisher_mirror_source_cooldowns.json')['scopes'].values()))
        self.assertEqual(entry['endpoint'], 'caption')
        records = (self.root / 'sync/publisher_mirror_manifest.jsonl').read_text()
        self.assertNotIn('https://', records)
        self.assertEqual(json.loads(records.splitlines()[0])['source_requests']['audio']['endpoint'], 'audio')

    def test_scoped_deadline_survives_new_instance_and_same_request_never_retries(self):
        self.transport.fail_audio = True
        first = self.batch().run()
        self.assertEqual(first['held'], 1)
        old = (self.root / 'sync/publisher_mirror_source_cooldowns.json').read_bytes()
        before = len(self.transport.calls)
        second = self.batch().run()
        self.assertEqual(second['items'][0]['error_class'], 'partial_requires_review')
        self.assertEqual(len(self.transport.calls), before)
        self.assertEqual((self.root / 'sync/publisher_mirror_source_cooldowns.json').read_bytes(), old)
        batch = self.batch()
        item = batch.items[0]
        with self.assertRaisesRegex(m.MirrorError, 'publisher_endpoint_cooldown'):
            batch.guard(source=True, source_scope=batch.request_scope(item, 'audio', item['audio']), force=True)
        batch.guard(source=True, source_scope=batch.request_scope(item, 'caption:en-auto', item['captions'][0]))

    def test_legacy_unscoped_deadline_stays_global_and_unchanged(self):
        path = self.root / 'sync/publisher_mirror_source_cooldown.json'
        self.put(path, {'schema_version': 1, 'error_class': 'forbidden', 'retry_not_before_epoch': time.time() + 600})
        old = path.read_bytes()
        result = self.batch().run()
        self.assertEqual(result['items'][0]['error_class'], 'publisher_source_cooldown')
        self.assertFalse(self.transport.calls)
        self.assertEqual(path.read_bytes(), old)

    def legacy_binding(self):
        legacy_path = self.root / 'sync/publisher_mirror_source_cooldown.json'
        self.put(legacy_path, {'schema_version': 1, 'error_class': 'forbidden', 'retry_not_before_epoch': time.time() + 600})
        item = m.load_items(self.root, self.plan)[1][0]
        state = {'schema_version': 1, 'item_id': item['item_id'], 'plan_sha256': m.sha(self.plan.read_bytes()),
                 'started': ['audio'], 'downloads': {}, 'error_class': 'publisher_http_403'}
        snapshot = self.root / 'immutable-failure.json'
        self.put(snapshot, state)
        state_pin = {'path': snapshot.name, 'sha256': m.sha(snapshot.read_bytes())}
        evidence = {'kind': 'publisher_audio_source_failure_binding', 'provider': item['provider'], 'artifact_kind': 'audio',
            'item_id': item['item_id'], 'error_class': 'forbidden', 'accepted_metadata': item['accepted_metadata'],
            'plan': {'path': self.plan.name, 'sha256': m.sha(self.plan.read_bytes())}, 'failure_state': state_pin,
            'legacy_cooldown': {'sha256': m.sha(legacy_path.read_bytes())}, 'retry_not_before_epoch': m.read(legacy_path)['retry_not_before_epoch'],
            'caption_request_started': False, 'source_audio_requests_started': 1, 'audio_bytes_completed': 0}
        evidence_path = self.root / 'immutable-evidence.json'
        self.put(evidence_path, evidence)
        binding = {'schema_version': 1, 'authorization': 'root_agent_explicit_scope_binding', 'provider': item['provider'], 'endpoint': 'audio',
            'legacy_cooldown_sha256': m.sha(legacy_path.read_bytes()), 'retry_not_before_epoch': evidence['retry_not_before_epoch'],
            'failure_evidence': {'path': evidence_path.name, 'sha256': m.sha(evidence_path.read_bytes())}, 'failure_state_snapshot': state_pin}
        self.put(self.root / 'sync/publisher_mirror_legacy_scope_binding.json', binding)
        return legacy_path, evidence_path, snapshot

    def test_explicit_legacy_binding_preserves_deadline_and_separates_audio(self):
        legacy, _, _ = self.legacy_binding()
        original = legacy.read_bytes()
        batch = self.batch()
        audio = {'provider': 'Fixture', 'endpoint': 'audio'}
        with self.assertRaisesRegex(m.MirrorError, 'publisher_endpoint_cooldown'):
            batch.guard(source=True, source_scope=audio, force=True)
        batch.guard(source=True, source_scope={'provider': 'Fixture', 'endpoint': 'caption'}, force=True)
        batch.guard(source=True, source_scope={'provider': 'OtherPublisher', 'endpoint': 'audio'}, force=True)
        self.assertEqual(legacy.read_bytes(), original)
        self.assertFalse(self.transport.calls)

    def test_stale_legacy_evidence_or_snapshot_cannot_lift_global_hold(self):
        legacy, evidence, snapshot = self.legacy_binding()
        for path in (legacy, evidence, snapshot, self.plan, self.root / self.item['accepted_metadata']['path']):
            old = path.read_bytes()
            with self.subTest(path=path.name):
                path.write_bytes(old + b'\n')
                batch = self.batch() if path != self.root / self.item['accepted_metadata']['path'] else None
                self.assertIsNone(m.bound_legacy_scope(self.root, legacy.read_bytes()))
                if batch:
                    # The plan lease is separately pinned; test source binding in isolation.
                    self.bind()
                    with self.assertRaisesRegex(m.MirrorError, 'publisher_source_cooldown'):
                        batch.guard(source=True, source_scope={'provider': 'OtherPublisher', 'endpoint': 'audio'}, force=True)
                path.write_bytes(old)
                self.bind()
        self.assertFalse(self.transport.calls)




if __name__ == "__main__":
    unittest.main()
