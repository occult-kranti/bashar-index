"""Offline capture boundaries: loopback HTTP, durable spooling and mocked Drive.

No browser, source website, audio decoder or external service is contacted.
"""
from __future__ import annotations

import csv
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import chromium_capture_service as capture


class FakeDrive:
    def __init__(self, *, failure=None, alter=None):
        self.failure, self.alter = failure, alter
        self.entries, self.calls = {}, []

    def copy_pair(self, audio, metadata, audio_remote, metadata_remote):
        self.calls.append(("copy", audio_remote, metadata_remote))
        if self.failure:
            raise self.failure
        for i, (path, remote) in enumerate(((audio, audio_remote), (metadata, metadata_remote))):
            proof = capture.hash_file(path)
            self.entries[remote] = {"ID": "drive-object-" + str(i), "IsDir": False,
                                    "Size": proof["bytes"], "Hashes": {"MD5": proof["md5"]}}

    def stat(self, remote):
        self.calls.append(("stat", remote))
        entry = json.loads(json.dumps(self.entries[remote]))
        return self.alter(remote, entry) if self.alter else entry


class CaptureFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="capture-service-offline-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "sync").mkdir()
        (self.root / "sync/STOP_DRIVE_INGEST").write_text(
            "Codex resource phase: isolated ASR provisioning and bounded SABR investigation", encoding="utf-8")
        self.resource_plan = {"collector_dispatch_allowed": False, "browser_capture_dispatch_allowed": True,
                              "accounting_cap_bytes": capture.MANAGED_CAP,
                              "reservations": [{"lease_id": "browser-capture-v1", "state": "active",
                                                "max_bytes": capture.SPOOL_CAP}]}
        (self.root / "sync/analysis_resource_plan.json").write_text(json.dumps(self.resource_plan), encoding="utf-8")
        self.queue = self.root / "queue.csv"
        with self.queue.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=("video_id", "channel_dir", "tab", "listing_rank", "duration_s"))
            writer.writeheader()
            writer.writerows({"video_id": f"vid{i:08d}", "channel_dir": "fixture", "tab": "videos",
                              "listing_rank": i, "duration_s": 10} for i in range(7))
        self.addCleanup(patch.stopall)
        patch.object(capture.shutil, "disk_usage", return_value=SimpleNamespace(free=50_000_000_000)).start()
        tree_bytes = capture.tree_bytes
        patch.object(capture, "tree_bytes", side_effect=lambda path: tree_bytes(path)
                     if Path(path).is_relative_to(self.root) else 0).start()
        self.store = self.make_store()

    def make_store(self, **kwargs):
        store = capture.Store(self.root, self.queue,
                              [self.root, Path(sys.prefix), Path(capture.__file__).resolve().parents[2]], **kwargs)
        self.addCleanup(store.executor.shutdown, wait=True)
        self.addCleanup(store.validators.shutdown, wait=True)
        return store

    def lease(self, worker="worker-one", **extra):
        with self.store.lock:
            return self.store.next(dict(worker_id=worker, **extra))["job"]

    def start_value(self, job, **extra):
        return dict(capture_id=job["capture_id"], video_id=job["video_id"],
                    ads_detected=False, is_live=False, playback_rate=1, source_time=0,
                    duration_seconds=10, source_metadata={"title": "Published fixture"}, **extra)

    def started(self):
        job = self.lease()
        self.store.start(self.start_value(job))
        return self.store.jobs[job["capture_id"]]

    def finish_value(self, job):
        return dict(capture_id=job["capture_id"], video_id=job["video_id"], source_ended=True,
                    ads_detected=False, playback_rate=1, source_duration=10, source_time=10,
                    coverage_intervals=[[0, 10]])

    def ready(self, extra_finish=None):
        job = self.started()
        self.store.chunk(job["capture_id"], 0, b"mock encoded opus recording")
        evidence = {"decoded_duration_seconds": 10, "mean_volume_db": -20, "codec": "opus",
                    "container": "webm", "full_decode_passed": True}
        with patch.object(capture, "inspect_audio", return_value=evidence), patch.object(self.store, "schedule_upload"):
            self.store.prepare_finish(dict(self.finish_value(job), **(extra_finish or {})))
            self.store.validate(job)
        return job

    def assert_owned_pair_exists(self, job):
        for name in ("audio.webm", "capture.info.json"):
            self.assertTrue(self.store.path(job["capture_id"], name).is_file())


class CaptureStoreTests(CaptureFixture, unittest.TestCase):
    def test_missing_resource_authorization_and_unaccounted_roots_fail_closed(self):
        self.resource_plan["browser_capture_dispatch_allowed"] = False
        plan = self.root / "sync/analysis_resource_plan.json"
        plan.write_text(json.dumps(self.resource_plan), encoding="utf-8")
        with self.assertRaisesRegex(capture.CaptureError, "capture_resource_reservation_required"):
            self.make_store()
        self.resource_plan["browser_capture_dispatch_allowed"] = True
        plan.write_text(json.dumps(self.resource_plan), encoding="utf-8")
        with self.assertRaisesRegex(capture.CaptureError, "managed_roots_incomplete"):
            capture.Store(self.root, self.queue, [self.root])
        (self.root / "sync/STOP_DRIVE_INGEST").write_text("User requested stop", encoding="utf-8")
        with self.assertRaisesRegex(capture.CaptureError, "collector_resource_phase_required"):
            self.make_store()

    def test_second_service_owner_cannot_acquire_existing_kernel_lease(self):
        path = self.root / "sync/browser_capture_service.lock"
        with capture.kernel_lock(path):
            with self.assertRaisesRegex(Exception, "gpu_owner_busy"):
                with capture.kernel_lock(path):
                    self.fail("duplicate service acquired the live kernel lease")

    def test_revoked_reservation_or_stop_marker_blocks_live_chunks_without_discarding_bytes(self):
        job = self.started()
        self.store.chunk(job["capture_id"], 0, b"retained")
        self.resource_plan["browser_capture_dispatch_allowed"] = False
        (self.root / "sync/analysis_resource_plan.json").write_text(json.dumps(self.resource_plan), encoding="utf-8")
        with self.assertRaisesRegex(capture.CaptureError, "capture_resource_reservation_required"):
            self.store.chunk(job["capture_id"], 1, b"disallowed")
        self.resource_plan["browser_capture_dispatch_allowed"] = True
        (self.root / "sync/analysis_resource_plan.json").write_text(json.dumps(self.resource_plan), encoding="utf-8")
        (self.store.spool / "STOP_CAPTURE").write_text("user stop", encoding="utf-8")
        with self.assertRaisesRegex(capture.CaptureError, "capture_stop_requested"):
            self.store.chunk(job["capture_id"], 1, b"disallowed")
        self.assertEqual(self.store.path(job["capture_id"], "audio.webm.part").read_bytes(), b"retained")
        self.assertEqual(job["sequence"], 1)

    def test_same_worker_is_idempotent_and_four_concurrent_leases_are_distinct(self):
        first = self.lease()
        self.assertEqual(first, self.lease())
        jobs = [first] + [self.lease("worker-" + str(i)) for i in range(3)]
        self.assertEqual(len({j["video_id"] for j in jobs}), 4)
        with self.assertRaisesRegex(capture.CaptureError, "four_workers_active"):
            self.lease("fifth-worker")
        self.assertEqual(len(self.store.jobs), 4)

    def test_racing_same_worker_requests_create_one_durable_lease(self):
        barrier, results = threading.Barrier(8), []
        def request():
            barrier.wait()
            results.append(self.lease("same-worker"))
        threads = [threading.Thread(target=request) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(len(results), 8)
        self.assertEqual(len({j["capture_id"] for j in results}), 1)
        self.assertEqual(len(list(self.store.spool.glob("capture-*/state.json"))), 1)

    def test_requested_priority_does_not_fake_newest_rank(self):
        requested = self.root / "requested.csv"
        requested.write_text("video_id,channel_dir,tab,listing_rank,duration_s\nPINNED00001,fixture,videos,698,10\n", encoding="utf-8")
        other = self.make_store(requested=requested)
        job = other.next({"worker_id": "priority"})["job"]
        self.assertEqual(job["video_id"], "PINNED00001")
        self.assertEqual(other.jobs[job["capture_id"]]["source"]["listing_rank"], 698)

    def test_spool_exact_reservation_boundary_includes_control_headroom(self):
        self.store.spool_cap = 2_000_000
        with self.assertRaisesRegex(capture.CaptureError, "spool_backpressure"):
            self.lease()
        self.assertEqual(self.store.jobs, {})

    def test_managed_and_disk_reserves_reject_before_admission(self):
        self.store.outside_bytes = capture.MANAGED_CAP - capture.OTHER_GROWTH_RESERVE - 1
        with self.assertRaisesRegex(capture.CaptureError, "managed_storage_backpressure"):
            self.lease()
        self.store.outside_bytes = 0
        with patch.object(capture.shutil, "disk_usage", return_value=SimpleNamespace(free=capture.DISK_FLOOR)):
            with self.assertRaisesRegex(capture.CaptureError, "disk_buffer_backpressure"):
                self.lease()
        self.assertEqual(self.store.jobs, {})

    def test_failed_start_save_rolls_back_and_can_retry_without_orphan_part(self):
        leased = self.lease()
        with patch.object(self.store, "save", side_effect=OSError("simulated state write failure")):
            with self.assertRaises(OSError):
                self.store.start(self.start_value(leased))
        job = self.store.jobs[leased["capture_id"]]
        self.assertEqual(job["state"], "leased")
        self.assertFalse(self.store.path(job["capture_id"], "audio.webm.part").exists())
        self.store.start(self.start_value(leased))
        self.assertEqual(job["state"], "recording")

    def test_chunk_replay_and_storage_pressure_never_append_bytes(self):
        job = self.started()
        self.store.chunk(job["capture_id"], 0, b"first")
        path = self.store.path(job["capture_id"], "audio.webm.part")
        with self.assertRaisesRegex(capture.CaptureError, "chunk_sequence_conflict"):
            self.store.chunk(job["capture_id"], 0, b"replayed")
        with patch.object(self.store, "budget", side_effect=capture.CaptureError("spool_backpressure", 507)):
            with self.assertRaises(capture.CaptureError):
                self.store.chunk(job["capture_id"], 1, b"overflow")
        self.assertEqual(path.read_bytes(), b"first")
        self.assertEqual(job["sequence"], 1)
        self.assertEqual(job["bytes"], 5)

    def test_finish_strips_unrecognized_transport_fields_from_durable_metadata(self):
        job = self.ready({"cookie": "PRIVATE_COOKIE", "transport": {"signed_url": "PRIVATE_URL"}})
        for name in ("state.json", "capture.info.json"):
            value = self.store.path(job["capture_id"], name).read_text(encoding="utf-8")
            self.assertNotIn("PRIVATE_COOKIE", value)
            self.assertNotIn("PRIVATE_URL", value)

    def test_replayed_source_clock_gap_or_ad_cannot_reach_decoder(self):
        job = self.started()
        self.store.chunk(job["capture_id"], 0, b"audio")
        cases = [{"coverage_intervals": [[0, 2], [6, 10]]}, {"ads_detected": True}, {"source_ended": False},
                 {"playback_rate": 2}, {"source_time": 5}]
        for change in cases:
            with self.subTest(change=change), patch.object(capture, "inspect_audio") as decoder:
                with self.assertRaises(capture.CaptureError):
                    self.store.finish(dict(self.finish_value(job), **change))
                decoder.assert_not_called()
        self.assertEqual(job["state"], "recording")

    def test_decoder_failure_retains_incomplete_bytes_and_never_uploads(self):
        job = self.started()
        self.store.chunk(job["capture_id"], 0, b"audio")
        with patch.object(capture, "inspect_audio", side_effect=capture.CaptureError("silent_or_unmeasured_recording")), \
             patch.object(self.store, "schedule_upload") as upload:
            self.store.prepare_finish(self.finish_value(job))
            self.store.validate(job)
            upload.assert_not_called()
        self.assertEqual(job["state"], "held")
        self.assertEqual(self.store.path(job["capture_id"], "audio.webm.part").read_bytes(), b"audio")
        self.assertEqual(self.store.completed(), set())

    def test_upload_failure_preserves_both_artifacts_without_completion(self):
        job = self.ready()
        self.store.drive = FakeDrive(failure=capture.IngestError("drive_rate_limited", "offline refusal"))
        self.store.upload(job)
        self.assertEqual(job["state"], "upload_held")
        self.assert_owned_pair_exists(job)
        self.assertEqual(self.store.completed(), set())

    def test_missing_or_wrong_remote_proof_prevents_every_delete(self):
        changes = [lambda e: dict(e, ID=""), lambda e: dict(e, Size=e["Size"] + 1),
                   lambda e: dict(e, Hashes={}), lambda e: dict(e, Hashes={"MD5": "0" * 32}),
                   lambda e: dict(e, IsDir=True), lambda e: dict(e, ID="drive-object-0")]
        job = self.ready()
        for change in changes:
            with self.subTest(change=change):
                self.store.drive = FakeDrive(alter=lambda remote, e: change(e) if remote.endswith("capture.info.json") else e)
                self.store.upload(job)
                self.assertEqual(job["state"], "upload_held")
                self.assert_owned_pair_exists(job)
                self.assertEqual(self.store.completed(), set())

    def test_local_mutation_is_rejected_before_any_drive_call(self):
        job = self.ready()
        self.store.path(job["capture_id"], "audio.webm").write_bytes(b"changed")
        drive = self.store.drive = FakeDrive()
        self.store.upload(job)
        self.assertEqual(drive.calls, [])
        self.assert_owned_pair_exists(job)

    def test_durable_exact_pair_receipt_precedes_first_owned_delete(self):
        job = self.ready()
        self.store.drive = FakeDrive()
        original_unlink = Path.unlink
        observed = []
        def unlink(path, *args, **kwargs):
            if path.name in {"audio.webm", "capture.info.json"}:
                receipts = capture.records(self.root / "sync/browser_capture_manifest.jsonl")
                self.assertEqual(len(receipts), 1)
                self.assertTrue(capture.browser_receipt_complete(receipts[0], job["source"], self.store.remote))
                self.assertEqual(len([c for c in self.store.drive.calls if c[0] == "stat"]), 2)
                observed.append(path.name)
            return original_unlink(path, *args, **kwargs)
        with patch.object(Path, "unlink", new=unlink):
            self.store.upload(job)
        self.assertEqual(observed, ["audio.webm", "capture.info.json"])
        self.assertEqual(job["state"], "verified")
        self.assertEqual(self.store.completed(), {job["video_id"]})
        self.assertIsNone(self.lease("other", video_id=job["video_id"]))

    def test_journal_write_failure_keeps_both_artifacts(self):
        job = self.ready()
        self.store.drive = FakeDrive()
        with patch.object(capture, "journal", side_effect=OSError("durable append refused")):
            self.store.upload(job)
        self.assert_owned_pair_exists(job)
        self.assertEqual(self.store.completed(), set())

    def test_restart_marks_unfinished_recording_held_and_preserves_part(self):
        job = self.started()
        self.store.chunk(job["capture_id"], 0, b"partial")
        restarted = self.make_store()
        self.assertEqual(restarted.jobs[job["capture_id"]]["state"], "held")
        self.assertEqual(restarted.path(job["capture_id"], "audio.webm.part").read_bytes(), b"partial")
        self.assertEqual(restarted.completed(), set())

    def test_restart_reconciles_interrupted_upload_with_exact_saved_pair(self):
        job = self.ready()
        job["state"] = "uploading"
        self.store.save(job)
        restarted = self.make_store(drive=FakeDrive())
        saved = restarted.jobs[job["capture_id"]]
        self.assertEqual(saved["state"], "ready_for_upload")
        restarted.schedule_upload()
        restarted.executor.shutdown(wait=True)
        self.assertEqual(saved["state"], "verified")
        self.assertEqual(restarted.completed(), {job["video_id"]})

    def test_restart_after_first_unlink_recovers_survivor_from_durable_receipt(self):
        job = self.ready()
        drive = self.store.drive = FakeDrive()
        original_unlink = Path.unlink
        def fail_second(path, *args, **kwargs):
            if path.name == "capture.info.json":
                raise OSError("simulated crash after audio deletion")
            return original_unlink(path, *args, **kwargs)
        with patch.object(Path, "unlink", new=fail_second):
            self.store.upload(job)
        self.assertFalse(self.store.path(job["capture_id"], "audio.webm").exists())
        self.assertTrue(self.store.path(job["capture_id"], "capture.info.json").exists())
        calls_before = list(drive.calls)
        restarted = self.make_store(drive=drive)
        self.assertEqual(restarted.jobs[job["capture_id"]]["state"], "verified")
        self.assertFalse(restarted.path(job["capture_id"], "capture.info.json").exists())
        self.assertEqual(drive.calls, calls_before)

    def test_restart_never_deletes_changed_survivor_despite_prior_receipt(self):
        job = self.ready()
        self.store.drive = FakeDrive()
        original_unlink = Path.unlink
        def retain(path, *args, **kwargs):
            if path.name == "audio.webm":
                raise OSError("simulated crash before local cleanup")
            return original_unlink(path, *args, **kwargs)
        with patch.object(Path, "unlink", new=retain):
            self.store.upload(job)
        self.store.path(job["capture_id"], "capture.info.json").write_bytes(b"changed after remote receipt")
        with self.assertRaisesRegex(capture.CaptureError, "verified_cleanup_local_changed"):
            self.make_store()
        self.assert_owned_pair_exists(job)

    def test_finish_returns_before_decoder_and_status_waits_for_validation(self):
        job = self.started()
        self.store.chunk(job["capture_id"], 0, b"audio")
        entered, release = threading.Event(), threading.Event()
        def inspect(*_):
            entered.set()
            self.assertTrue(release.wait(3))
            return {"decoded_duration_seconds": 10, "mean_volume_db": -20,
                    "codec": "opus", "container": "webm", "full_decode_passed": True}
        with patch.object(capture, "inspect_audio", side_effect=inspect), patch.object(self.store, "schedule_upload"):
            try:
                result = self.store.finish(self.finish_value(job))
                self.assertEqual(result["state"], "validating")
                self.assertTrue(entered.wait(2))
                self.assertEqual(self.store.status({"capture_id": job["capture_id"]})["state"], "validating")
            finally:
                release.set()
                self.store.validators.shutdown(wait=True)
        self.assertEqual(self.store.status({"capture_id": job["capture_id"]})["state"], "ready_for_upload")
        job["state"] = "upload_held"
        self.assertEqual(self.store.status({"capture_id": job["capture_id"]})["state"], "held")


class AudioValidationTests(unittest.TestCase):
    def inspect(self, probe=None, stderr=b"n_samples: 160000\nmean_volume: -20.0 dB\n"):
        probe = probe or {"streams": [{"codec_type": "audio", "codec_name": "opus"}], "format": {"duration": "N/A"}}
        returns = [SimpleNamespace(stdout=json.dumps(probe).encode(), stderr=b""),
                   SimpleNamespace(stdout=b"", stderr=stderr)]
        with patch.object(capture.subprocess, "run", side_effect=returns) as run:
            result = capture.inspect_audio(Path("offline.webm"), 10, "offline-ffprobe", "offline-ffmpeg")
        return result, run.call_args_list

    def test_unknown_container_duration_uses_full_decoded_mono16k_samples(self):
        result, calls = self.inspect(stderr=b"n_samples: 0\nn_samples: 160000\nmean_volume: -20.0 dB\n")
        self.assertEqual(result["decoded_duration_seconds"], 10)
        self.assertIn("aresample=16000,aformat=channel_layouts=mono,volumedetect", calls[1].args[0])
        self.assertTrue(result["full_decode_passed"])

    def test_truncation_silence_and_unmeasured_recording_are_rejected(self):
        for stderr in (b"n_samples: 16000\nmean_volume: -20.0 dB", b"n_samples: 160000\nmean_volume: -90.0 dB",
                       b"mean_volume: -20.0 dB", b"n_samples: 160000\nmean_volume: -inf dB"):
            with self.subTest(stderr=stderr), self.assertRaises(capture.CaptureError):
                self.inspect(stderr=stderr)

    def test_video_stream_or_conflicting_container_duration_is_rejected(self):
        probes = [{"streams": [{"codec_type": "video", "codec_name": "vp9"}]},
                  {"streams": [{"codec_type": "audio", "codec_name": "opus"}], "format": {"duration": "100"}}]
        for probe in probes:
            with self.subTest(probe=probe), self.assertRaises(capture.CaptureError):
                self.inspect(probe=probe)


class CaptureHttpTests(CaptureFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.server = capture.ThreadingHTTPServer(("127.0.0.1", 0), capture.Handler)
        self.server.store = self.store
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .02}, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def request(self, path, *, method="POST", value=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        self.addCleanup(connection.close)
        complete = {"Host": f"127.0.0.1:{self.server.server_port}", "Origin": capture.ORIGIN,
                    "Authorization": "Bearer " + self.store.token, "Content-Type": "application/json"}
        complete.update(headers or {})
        body = (json.dumps(value).encode() if value is not None else b"") if method == "POST" else None
        connection.request(method, path, body=body, headers=complete)
        response = connection.getresponse()
        raw = response.read()
        return response.status, dict(response.getheaders()), json.loads(raw) if raw else {}

    def test_pair_requires_exact_host_and_extension_origin(self):
        for headers in ({"Host": "localhost:" + str(self.server.server_port)},
                        {"Host": "127.0.0.1:" + str(self.server.server_port + 1)},
                        {"Origin": "https://www.youtube.com"}, {"Origin": capture.ORIGIN + "/"}, {"Origin": "null"}):
            with self.subTest(headers=headers):
                status, _, value = self.request("/capture/v1/pair", headers=headers)
                self.assertEqual(status, 403)
                self.assertNotIn("token", value)
        status, headers, value = self.request("/capture/v1/pair", headers={"Authorization": ""})
        self.assertEqual(status, 200)
        self.assertEqual(value["token"], self.store.token)
        self.assertEqual(headers["Access-Control-Allow-Origin"], capture.ORIGIN)
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_missing_or_wrong_auth_cannot_allocate_lease(self):
        for auth in ("", "Bearer wrong", "bearer " + self.store.token):
            with self.subTest(auth=auth):
                status, _, value = self.request("/capture/v1/next", headers={"Authorization": auth})
                self.assertEqual(status, 401)
                self.assertEqual(value["error"], "unauthorized")
        self.assertEqual(self.store.jobs, {})
        status, _, value = self.request("/capture/v1/next", value={"worker_id": "http"})
        self.assertEqual(status, 200)
        self.assertEqual(value["job"]["video_id"], "vid00000000")

    def test_size_and_transfer_encoding_are_rejected_before_parsing(self):
        for header, expected in (({"Content-Length": str(capture.MAX_CONTROL + 1)}, 413),
                                 ({"Transfer-Encoding": "chunked"}, 400)):
            status, _, _ = self.request("/capture/v1/next", headers=header)
            self.assertEqual(status, expected)
        self.assertEqual(self.store.jobs, {})

    def test_preflight_is_exact_origin_only_and_health_never_exposes_token(self):
        status, headers, _ = self.request("/capture/v1/next", method="OPTIONS", headers={"Authorization": ""})
        self.assertEqual(status, 204)
        self.assertEqual(headers["Access-Control-Allow-Origin"], capture.ORIGIN)
        status, headers, _ = self.request("/capture/v1/next", method="OPTIONS", headers={"Origin": "https://evil.invalid"})
        self.assertEqual(status, 403)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        status, _, value = self.request("/capture/v1/health", method="GET", headers={"Origin": "", "Authorization": ""})
        self.assertEqual(status, 200)
        self.assertNotIn(self.store.token, json.dumps(value))


if __name__ == "__main__":
    unittest.main()
