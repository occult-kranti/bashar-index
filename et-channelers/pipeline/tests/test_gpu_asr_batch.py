"""Offline regressions for the normal pooled, all-source ASR command."""
from collections import Counter, deque
from contextlib import ExitStack
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pipeline import common, gpu_asr as base, gpu_asr_batch as batch, gpu_asr_editions as editions
from pipeline import gpu_asr_multilingual as multi, postrun_candidates, stage_archived_text
from pipeline.tests import test_gpu_asr_editions as fixtures


class PostCollectionBatchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.EditionAsrTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.settings = self.fixture.settings

    def test_native_strict_probe_and_prior_language_review_are_bound_to_exact_audio(self):
        video = "native00001"
        item = self.fixture.item(video, editions.NATIVE)
        row = {key: item[key] for key in ("channel_dir", "video_id", "tab")}
        prefix = self.fixture.remote + "/testing/Videos/" + video
        native = {**row, **item["audio"], "remote": prefix + ".m4a", "path": video + ".m4a", "status": "deleted",
                  "metadata": {**item["metadata"], "remote": prefix + ".info.json"},
                  "native_acquisition_quality": {"strict_probe_passed": True, "audio_streams": 1,
                                                 "container_duration_seconds": 32_399.963719,
                                                 "source_duration_seconds": 32_400}}
        source = editions.source_catalogue(self.root, [row], self.fixture.remote, native_records={video: native})
        recording = next(iter(source[video].values()))
        self.assertEqual(recording["duration_seconds"], 32_399.963719)
        self.assertEqual(recording["source_timebase"], "native_youtube_audio_seconds")
        self.assertIn(video + "/ASR/", editions.result_remote(recording, "asr-" + "0"*24))
        inputs = {video: native}, source, []
        hold = {"video_id": video, "status": "held", "semantic_text_generated": False,
                "decision": {"status": "held", "reason": "no_reliable_speech"},
                "source_audio_drive_id": native["drive_id"], "source_audio_sha256": "f"*64}
        with patch.object(editions.collection_coverage, "mixed_selection",
                          return_value=([row], {}, self.fixture.selection)):
            def inventory(**options):
                return editions.inventory(self.root, self.root/"selection", self.fixture.selection,
                                          self.fixture.remote, inputs=inputs, **options)["rows"][0]
            common.append_jsonl(self.root/"sync/asr_language_manifest.jsonl", hold)
            self.assertEqual(inventory()["status"], "edition_asr_eligible")
            common.append_jsonl(self.root/"sync/asr_language_manifest.jsonl", {**hold, "source_audio_sha256": native["sha256"]})
            self.assertEqual(inventory()["status"], "existing_language_review")
            permit = {key:recording[key] for key in ("channel_dir","audio","metadata")}
            self.assertEqual(inventory(reviews={video:permit},review_sha256="c"*64)["status"], "edition_asr_eligible")
            wrong = {**permit,"metadata":{**permit["metadata"],"drive_id":"independent_revision"}}
            self.assertEqual(inventory(reviews={video:wrong},review_sha256="c"*64)["status"], "existing_language_review")
        native["metadata"]["drive_id"] = native["drive_id"]
        self.assertFalse(editions.source_catalogue(self.root, [row], self.fixture.remote, native_records={video: native}))

    def test_premature_inventory_cannot_silently_omit_newly_archived_audio(self):
        item = self.fixture.item()
        draft = {"source_scope": editions.ALL_SOURCES,
                 "rows": [{"video_id": item["video_id"], "status": "audio_missing", "selected_source": None}]}
        complete = {"rows": [{"video_id": item["video_id"], "status": "edition_asr_eligible", "selected_source": item}]}
        with self.assertRaisesRegex(ValueError, "Newly ready audio"):
            editions.grouped_sources(draft, complete)
        with self.assertRaisesRegex(ValueError, "lacks a typed ASR source"):
            editions.grouped_sources(draft, draft)

    def test_exact_completed_windows_survive_failure_between_original_and_translation(self):
        item = self.fixture.item(kind=editions.NATIVE)
        item["duration_seconds"] = 90.0
        calls = Counter()
        fail = True
        runtime = self.fixture.runtime
        runtime.windows = lambda path, duration: ((i*30.0, range(i, i+30*base.SAMPLE_RATE)) for i in range(3))

        def transcribe(audio, **config):
            nonlocal fail
            key = config["task"], audio.start
            calls[key] += 1
            if key == ("translate", 1) and fail:
                fail = False
                raise RuntimeError("simulated CUDA process interruption")
            word = SimpleNamespace(start=.2, end=.9, probability=.91, word=" speech")
            segment = SimpleNamespace(start=.1, end=1, text=" speech", words=[word], avg_logprob=-.1,
                                      no_speech_prob=.05, compression_ratio=1.)
            return iter([segment]), SimpleNamespace(duration_after_vad=1.)

        runtime.model.transcribe = transcribe
        monitor = SimpleNamespace(begin=Mock(), guard=Mock(), finish=Mock(return_value={"sample_count": 3}))
        checkpoint = self.root/"windows.sqlite"
        with patch.object(base, "gpu_lease", return_value={"rolling_utilization_target": .7, "max_vram_bytes": 10**9}), \
             patch.object(multi, "Monitor", return_value=monitor), \
             patch.object(multi, "detect_language", return_value={"status": "accepted", "language": "ja"}) as detect:
            def run():
                return editions.infer(self.settings, item, self.root/"invented.wav", runtime, self.fixture.model,
                                      self.fixture.proposal, self.fixture.selection, lambda: None,
                                      checkpoint_path=checkpoint, capacity_check=lambda size: None)
            with self.assertRaisesRegex(RuntimeError, "interruption"):
                run()
            self.assertTrue(checkpoint.is_file())
            result = run()
        self.assertEqual(detect.call_count, 1)
        self.assertEqual(calls, Counter({("translate", 1): 2, ("translate", 0): 1, ("translate", 2): 1,
                                         ("transcribe", 0): 1, ("transcribe", 1): 1, ("transcribe", 2): 1}))
        record = editions.publish(self.settings, result, [item], self.fixture.mock_drive(result))[0]
        row = {key: item[key] for key in ("channel_dir", "video_id", "tab")}
        job = {"kind": editions.RESULT, "edition": item, "record": record, "row": row, "proof": record}
        views = stage_archived_text.text_views(self.root, job, Path(result["bundle"]["path"]), self.fixture.remote)
        for name, view in views.items():
            self.assertEqual(view["source_timebase"], "native_youtube_audio_seconds")
            self.assertEqual([s["time_start"] for s in view["segments"]], [.1, 30.1, 60.1])
            path = self.root/"analysis"/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base.encoded(view))
        self.assertIn(item["video_id"], postrun_candidates.select_views(self.root, [row]))

    def test_long_bundle_expansion_uses_duration_bound_and_full_crc_checks(self):
        item = self.fixture.item(kind=editions.NATIVE)
        item["duration_seconds"] = 32_400
        doc, text = fixtures.test_corpus_asr_view.AsrViewTests.document(["speech", "control"], "en", True)
        doc["duration_seconds"] = item["duration_seconds"]
        monitor = SimpleNamespace(begin=Mock(), guard=Mock(),
                                  finish=Mock(return_value={"synthetic_samples": "0" * 21_000_000}))
        with patch.object(base, "gpu_lease", return_value={"rolling_utilization_target": .7, "max_vram_bytes": 10**9}), \
             patch.object(multi, "Monitor", return_value=monitor), \
             patch.object(multi, "detect_language", return_value={"status": "accepted", "language": "en"}), \
             patch.object(base, "collect_segments", return_value=(doc, text, 12)):
            result = editions.infer(self.settings, item, self.root/"invented.wav", self.fixture.runtime,
                                    self.fixture.model, self.fixture.proposal, self.fixture.selection, lambda: None,
                                    capacity_check=lambda size: None)
        path = Path(result["bundle"]["path"])
        self.assertAlmostEqual(batch.paired_limit(32_400), 101_200_000)
        with self.assertRaisesRegex(base.AsrError, "bundle_crc_or_expansion"):
            multi.verify_pair(path)
        record = editions.publish(self.settings, result, [item], self.fixture.mock_drive(result))[0]
        view = editions.text_views(path, {"record": record, "edition": item})
        self.assertEqual(view["english"]["source_kind"], "original_asr")
        self.assertFalse(view["english"]["translation_performed"])

    def test_complete_temporary_bundle_reopens_without_inference_and_partial_is_preserved(self):
        item = self.fixture.item()
        result = self.fixture.inference(item, "en")
        path = Path(result["bundle"]["path"])
        temporary = path.with_suffix(".zip.part")
        path.rename(temporary)
        recovered = editions.recover_local_result(self.settings, item, self.fixture.selection, self.fixture.proposal)
        self.assertEqual(recovered["bundle"], result["bundle"])
        path.unlink()
        temporary.write_bytes(b"partial ZIP")
        self.assertIsNone(editions.recover_local_result(self.settings, item, self.fixture.selection, self.fixture.proposal))
        self.assertFalse(temporary.exists())
        self.assertEqual(next(path.parent.glob("*.interrupted-*")).read_bytes(), b"partial ZIP")

    def test_live_physical_floor_changed_reservations_and_amortized_scans(self):
        plan = self.root/"sync/analysis_resource_plan.json"
        plan.parent.mkdir()
        plan.write_text("{}")
        cap = 23_000_000_000
        sample = {"managed_bytes": 12_000_000_000, "active_reservation_headroom_bytes": 110_000_000, "cap_bytes": cap}
        b = batch.StorageBudget(self.settings)
        with patch.object(base, "inventory", return_value=sample) as full, \
             patch.object(batch.shutil, "disk_usage", return_value=SimpleNamespace(free=19_000_000_000)) as free:
            for _ in range(32):
                b.admit(50_000)
            self.assertEqual(full.call_count, 1)
            b.admit(1)
            self.assertEqual(full.call_count, 2)
            plan.write_text('{"changed":true}')
            b.admit(1)
            self.assertEqual(full.call_count, 3)
            plan.write_text('{"changed":"during a recording"}')
            b.physical(50)
            self.assertEqual(full.call_count, 4)
            free.return_value = SimpleNamespace(free=12_110_000_001)
            with self.assertRaisesRegex(base.AsrError, "physical_disk_reserve"):
                b.physical(2)
            full.side_effect = base.AsrError("managed_storage_admission")
            with self.assertRaisesRegex(base.AsrError, "managed_storage_admission"):
                b.admit(12_000_000_000)

    def test_incremental_receipts_recover_torn_line_and_reject_conflict(self):
        path = self.root/"journal.jsonl"
        index = batch.PublicationIndex()
        a = {"source_key": "one", "run_id": "A", "value": 1}
        b = {"source_key": "two", "run_id": "B", "value": 2}
        common.append_jsonl(path, a)
        self.assertEqual(len(index.refresh(path)), 1)
        with path.open("ab") as handle:
            handle.write(b'{"incomplete":')
        with self.assertWarns(RuntimeWarning):
            self.assertEqual(len(index.refresh(path)), 1)
        common.append_jsonl(path, b)
        self.assertEqual(len(index.refresh(path)), 2)
        common.append_jsonl(path, {**a, "value": 3})
        with self.assertRaisesRegex(base.AsrError, "asr_journal_conflict"):
            index.refresh(path)

    def test_rolling_gpu_budget_carries_between_short_recordings_and_expires_after_idle(self):
        history = deque()
        readings = iter((100.0, 105.0, 111.0, 150.0))
        with patch.object(multi.time, "monotonic", side_effect=readings):
            for index, value in enumerate((100, 95, 10, 2)):
                monitor = multi.Monitor(Mock(), Mock(), rolling_history=history)
                monitor.start = 100.
                monitor.add({"gpu_percent": value, "vram_bytes": 1, "temperature_c": 45})
                if index == 2:
                    self.assertEqual(monitor.rolling_mean(), 205/3)
            self.assertEqual(monitor.rolling_mean(), 2)

    def test_normal_run_drains_more_than_twenty_reuses_one_model_and_continues_past_source_review(self):
        items = []
        for i in range(23):
            item = self.fixture.item("batch" + str(i).zfill(6), editions.NATIVE)
            item["audio"]["sha256"] = hashlib.sha256(item["video_id"].encode()).hexdigest()
            items.append(item)
        frame = [{key: item[key] for key in ("video_id","channel_dir","tab")} for item in items]
        proposal = {"profile": editions.PROFILE, "selection_sha256": self.fixture.selection,
                    "source_scope": editions.ALL_SOURCES, "remote": self.fixture.remote,
                    "rows": [{"video_id": item["video_id"], "selected_source": item, "status":"edition_asr_eligible"} for item in items]}
        path = self.root/"plan.json"
        path.write_bytes(base.encoded(proposal))
        plan_sha = base.hashes(path)["sha256"]
        sync = self.root/"sync"
        sync.mkdir()
        (sync/"STOP_DRIVE_INGEST").touch()
        (sync/"analysis_resource_plan.json").write_text("{}")
        lease = {"input_frame_sha256": plan_sha, "model": self.fixture.model}
        local = self.root/"fixture.m4a"
        def infer(settings, origin, *args, **kwargs):
            if origin is items[3] or origin["video_id"] == items[3]["video_id"]:
                raise base.AsrError("word_text_alignment")
            return {"status": "success", "run_id": "invented"}
        def publish(settings, local, associations, drive, **kwargs):
            return [{"video_id": item["video_id"], "inference_source": item} for item in associations]
        with ExitStack() as st:
            def mock(obj, name, **kwargs):
                return st.enter_context(patch.object(obj, name, **kwargs))
            mock(editions.collection_coverage, "mixed_selection", return_value=(frame, {}, self.fixture.selection))
            mock(editions.collection_coverage, "coverage", return_value=({}, frame))
            mock(postrun_candidates, "complete_frame")
            mock(base, "gpu_lease", return_value=lease)
            mock(batch.shutil, "disk_usage", return_value=SimpleNamespace(free=30_000_000_000))
            scan = mock(base, "inventory", return_value={"managed_bytes":100_000, "active_reservation_headroom_bytes":0,
                                                        "cap_bytes":23_000_000_000})
            catalogue = mock(editions, "catalogue_inputs", return_value=({}, {}, []))
            mock(editions, "inventory", return_value=proposal)
            model = mock(multi, "model_proof", return_value=self.fixture.model)
            mock(editions, "staged_pair", return_value={"audio": local, "metadata": local})
            speech = mock(editions, "infer", side_effect=infer)
            mock(editions, "publish", side_effect=publish)
            factory = Mock(return_value=self.fixture.runtime)
            results = editions.run(self.settings, path, self.fixture.selection, path, plan_sha, Mock(),
                                   limit=None, runtime_factory=factory)
        self.assertEqual(Counter(row["state"] for row in results), {"verified": 22, "source_review": 1})
        self.assertEqual((scan.call_count, catalogue.call_count, model.call_count, factory.call_count), (1, 1, 1, 1))
        self.assertEqual(speech.call_count, 23)
        self.fixture.runtime.close.assert_called_once()
