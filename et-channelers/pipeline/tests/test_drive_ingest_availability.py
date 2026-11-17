"""Site-mandated availability is honored before custom HTTPS transport."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from pipeline import drive_ingest as m


class ClockStop:
    def __init__(self):
        self.clock = 100.0
        self.stopped = False
        self.stop_after = None
        self.waits = []

    def is_set(self):
        return self.stopped

    def set(self):
        self.stopped = True

    def wait(self, seconds):
        self.waits.append(seconds)
        self.clock += seconds
        if self.stop_after is not None and self.clock >= self.stop_after:
            self.stopped = True
        return self.stopped


class Response(io.BytesIO):
    status = 200
    headers = {"Content-Length": "3"}


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.part = self.root / "audio.part"
        self.stop = ClockStop()
        self.info = {"id": "abcdefghijk", "url": "https://fixture.googlevideo.com/videoplayback?private=not-logged",
                     "filesize": 3, "ext": "m4a", "protocol": "https", "vcodec": "none"}
        self.budget = SimpleNamespace(file_cap=100, admit_size=Mock(), write=lambda out, data: out.write(data))
        self.get_times = []
        self.opener = Mock()
        self.opener.open.side_effect = self.get
        self.patches = [patch.object(m.time, "time", side_effect=lambda: self.stop.clock),
                        patch.object(m.time, "monotonic", side_effect=lambda: self.stop.clock),
                        patch.object(m.urllib.request, "build_opener", return_value=self.opener)]
        for scoped in self.patches:
            scoped.start()
            self.addCleanup(scoped.stop)

    def get(self, *_args, **_kwargs):
        self.get_times.append(self.stop.clock)
        return Response(b"abc")

    def transfer(self):
        return m.stream_audio(self.info, self.part, self.budget, 1000000, self.stop)

    def test_future_deadline_delays_first_get_and_holds_selected_format_scope(self):
        self.info.update(available_at=9999, requested_formats=[{"available_at": 102.5}, {"available_at": 104}],
                         formats=[{"available_at": 999999}])
        result = self.transfer()
        self.assertEqual(result["bytes"], 3)
        self.assertEqual(self.get_times, [104])
        self.assertTrue(all(0 < delay <= .25 for delay in self.stop.waits))
        self.assertEqual(self.part.read_bytes(), b"abc")

    def test_ready_or_absent_deadline_requests_immediately(self):
        self.info["available_at"] = 99
        self.transfer()
        self.assertEqual(self.get_times, [100])

    def test_long_wait_is_deferred_without_get_or_partial_file(self):
        self.info["available_at"] = 180
        with self.assertRaises(m.IngestError) as caught:
            self.transfer()
        self.assertEqual(caught.exception.kind, "source_not_ready")
        self.assertEqual(caught.exception.retry_not_before_epoch, 180)
        self.opener.open.assert_not_called()
        self.assertFalse(self.part.exists())
        self.assertEqual(self.stop.waits, [])

    def test_stop_during_wait_prevents_get_and_file_creation(self):
        self.info["available_at"] = 110
        self.stop.stop_after = 100.5
        with self.assertRaises(m.IngestError) as caught:
            self.transfer()
        self.assertEqual(caught.exception.kind, "stopped")
        self.opener.open.assert_not_called()
        self.assertFalse(self.part.exists())

    def test_invalid_deadline_is_rejected_before_transport(self):
        for value in (float("nan"), float("inf"), -1, True, "105", {}, [], 10**1000):
            with self.subTest(value=repr(value)):
                self.info["available_at"] = value
                with self.assertRaises(m.IngestError) as caught:
                    self.transfer()
                self.assertEqual(caught.exception.kind, "source_availability_invalid")
        self.opener.open.assert_not_called()

    def test_storage_is_rechecked_after_site_wait_before_get(self):
        self.info["available_at"] = 102
        self.budget.admit_size.side_effect = m.IngestError("deferred_storage", "Buffer unavailable")
        with self.assertRaises(m.IngestError):
            self.transfer()
        self.assertEqual(self.stop.clock, 102)
        self.opener.open.assert_not_called()

    def test_extractor_preserves_selected_deadline(self):
        self.info["available_at"] = 123
        args = SimpleNamespace(ytdlp="fixture", timeout=3)
        result = SimpleNamespace(returncode=0, stdout=json.dumps(self.info), stderr="")
        with patch.object(m, "run_tool", return_value=result):
            extracted = m.extract_audio(args, {"video_id": "abcdefghijk", "url": "https://www.youtube.com/watch?v=abcdefghijk"})
        self.assertEqual(extracted["available_at"], 123)

    def test_deferred_item_records_safe_retry_and_releases_browser_then_does_not_reextract(self):
        row = {"video_id": "abcdefghijk", "channel_dir": "fixture", "tab": "videos", "url": "https://www.youtube.com/watch?v=abcdefghijk"}
        args = SimpleNamespace(root=self.root, collect_metadata=False, collect_captions=False, download_only=True,
                               rate_bytes=1000000, http_chunk_bytes=0, remote="", browser_audio=True)
        budget = Mock(file_cap=1000000)
        lease = Mock()
        info = m.BrowserAudioInfo({**self.info, "available_at": 180}, lease)
        state_path = self.root / "sync/drive_ingest_manifest.jsonl"
        with patch.object(m, "extract_audio", return_value=info) as extract, contextlib.redirect_stderr(io.StringIO()):
            result = m.ingest_one(args, row, budget, Mock(), self.stop, None, state_path)
            self.assertEqual(result, "deferred_availability")
            record = m.load_state(state_path)[row["video_id"]]
            self.assertEqual(record["availability_retry_not_before_epoch"], 180)
            self.assertNotIn("retry_not_before_epoch", record)
            self.assertNotIn("source_error_class", record)
            self.assertNotIn("private=", state_path.read_text(encoding="utf-8"))
            self.assertFalse(self.stop.is_set())
            lease.close.assert_called_once()
            budget.release.assert_called_once_with(row["video_id"])
            self.assertEqual(m.ingest_one(args, row, budget, Mock(), self.stop, None, state_path, prior=record), "deferred_availability")
            extract.assert_called_once()
        self.opener.open.assert_not_called()


if __name__ == "__main__":
    unittest.main()
