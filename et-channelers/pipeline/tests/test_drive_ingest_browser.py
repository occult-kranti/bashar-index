"""Offline browser-session lifetime tests; no Chromium, YouTube or Drive calls."""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import drive_ingest as ingest
from media_metadata import build_metadata

VIDEO_ID = "ABCDEFGHIJK"


class StubBrowserError(RuntimeError):
    def __init__(self, kind, message="private helper diagnostic"):
        super().__init__(message)
        self.kind = kind


class BrowserLifetimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="browser-ingest-offline-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.row = {"video_id": VIDEO_ID, "channel_dir": "example", "tab": "videos",
                    "listing_rank": 0, "url": f"https://www.youtube.com/watch?v={VIDEO_ID}",
                    "title": "Fixture"}
        self.args = types.SimpleNamespace(root=self.root, timeout=5, ytdlp="offline-stub",
            browser_audio=True, youtube_client="default", collect_captions=False,
            collect_metadata=True, download_only=True, remote="", rate_bytes=1024,
            http_chunk_bytes=0)
        self.info = {"id": VIDEO_ID, "title": "Fixture", "description": "Public description",
                     "ext": "webm", "protocol": "https", "vcodec": "none",
                     "url": "https://example.googlevideo.com/videoplayback?sig=private-fixture",
                     "http_headers": {"User-Agent": "Fixture", "Cookie": "private-fixture"},
                     "format_id": "251", "duration": 3}
        self.lease = Mock(name="PRIVATE_LEASE_MUST_NOT_SERIALIZE")
        self.browser = types.ModuleType("browser_audio")
        self.browser.BrowserAudioError = StubBrowserError
        self.browser.open_audio = Mock(return_value=(self.info, self.lease))
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, {"browser_audio": self.browser}).start()
        self.cli = patch.object(ingest, "run_tool").start()
        self.cli.return_value = types.SimpleNamespace(returncode=0, stderr="",
            stdout=json.dumps({"id": VIDEO_ID, "title": "Metadata only"}))
        self.budget = Mock()
        self.budget.write.side_effect = lambda handle, data: handle.write(data)
        self.stop = threading.Event()
        self.state_path = self.root / "sync" / "drive_ingest_manifest.jsonl"

    def attempt(self):
        with contextlib.redirect_stderr(io.StringIO()):
            return ingest.ingest_one(self.args, self.row, self.budget, Mock(), self.stop,
                                     None, self.state_path)

    def test_lease_stays_open_through_stream_then_metadata_is_safe(self):
        events = []
        self.lease.close.side_effect = lambda: events.append("closed")
        def transfer(info, part, *_):
            self.assertIsInstance(info, ingest.BrowserAudioInfo)
            self.lease.close.assert_not_called()
            self.assertIs(info.browser_lease, self.lease)
            events.append("stream-start")
            part.write_bytes(b"bounded fixture audio")
            events.append("stream-end")
            return ingest.hash_file(part)
        with patch.object(ingest, "stream_audio", side_effect=transfer):
            self.assertEqual(self.attempt(), "downloaded")
        self.assertEqual(events, ["stream-start", "stream-end", "closed"])
        self.lease.close.assert_called_once_with()
        self.cli.assert_not_called()
        self.budget.release.assert_called_once_with(VIDEO_ID)
        sidecar = self.root / "audio/example/Videos" / (VIDEO_ID + ".info.json")
        document = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertEqual(document["metadata"]["description"], "Public description")
        combined = sidecar.read_text(encoding="utf-8") + self.state_path.read_text(encoding="utf-8")
        for private in ("browser_lease", "PRIVATE_LEASE_MUST_NOT_SERIALIZE", "private-fixture"):
            self.assertNotIn(private, combined)

    def test_stream_403_closes_lease_and_preserves_source_cooldown(self):
        def refused(info, *_):
            self.assertIs(info.browser_lease, self.lease)
            self.lease.close.assert_not_called()
            raise ingest.IngestError("forbidden", "HTTP 403")
        with patch.object(ingest, "stream_audio", side_effect=refused):
            self.assertEqual(self.attempt(), "error")
        self.lease.close.assert_called_once_with()
        self.budget.release.assert_called_once_with(VIDEO_ID)
        self.assertTrue(self.stop.is_set())
        state = ingest.load_state(self.state_path)[VIDEO_ID]
        self.assertEqual(state["source_error_class"], "forbidden")
        self.assertGreater(state["retry_not_before_epoch"], 0)

    def test_budget_rejection_before_stream_closes_unreserved_lease(self):
        self.budget.reserve_item.side_effect = ingest.IngestError("deferred_storage", "Buffer unavailable")
        with patch.object(ingest, "stream_audio") as transfer:
            self.assertEqual(self.attempt(), "deferred_storage")
        transfer.assert_not_called()
        self.lease.close.assert_called_once_with()
        self.budget.release.assert_not_called()
        self.assertFalse(self.stop.is_set())

    def test_validation_failure_closes_lease_without_cli_fallback(self):
        cases = [{"id": "WRONGID1234"}, {"is_live": True}, {"vcodec": "h264"},
                 {"protocol": "m3u8"}, {"url": "https://untrusted.invalid/media"}]
        for changes in cases:
            with self.subTest(changes=changes):
                lease = Mock()
                self.browser.open_audio.return_value = (dict(self.info, **changes), lease)
                with self.assertRaises(ingest.IngestError):
                    ingest.extract_audio(self.args, self.row)
                lease.close.assert_called_once_with()
        self.cli.assert_not_called()

    def test_browser_error_kind_survives_without_private_diagnostic(self):
        self.browser.open_audio.side_effect = StubBrowserError("forbidden", "private signed URL and session")
        with self.assertRaises(ingest.IngestError) as caught:
            ingest.extract_audio(self.args, self.row)
        self.assertEqual(caught.exception.kind, "forbidden")
        self.assertNotIn("private signed", str(caught.exception))
        self.cli.assert_not_called()

    def test_explicit_metadata_only_uses_cli_despite_browser_flag(self):
        result = ingest.extract_audio(self.args, self.row, metadata_only=True)
        self.assertEqual(result["id"], VIDEO_ID)
        self.assertNotIsInstance(result, ingest.BrowserAudioInfo)
        self.browser.open_audio.assert_not_called()
        command = self.cli.call_args.args[0]
        for option in ("--ignore-no-formats-error", "--simulate", "--write-subs", "--write-auto-subs"):
            self.assertIn(option, command)
        self.assertNotIn("-f", command)

    def test_existing_audio_metadata_backfill_never_opens_browser_lease(self):
        self.browser.open_audio.side_effect = AssertionError("Metadata backfill must not open Chromium")
        audio = self.root / "audio/example/Videos" / (VIDEO_ID + ".webm")
        audio.parent.mkdir(parents=True)
        audio.write_bytes(b"already downloaded audio")
        record = dict(ingest.hash_file(audio), video_id=VIDEO_ID,
                      path=str(audio.relative_to(self.root)), status="downloaded")
        path = ingest.ensure_metadata(self.args, self.row, record, self.budget,
            Mock(), self.stop, None, self.state_path, info=None)
        self.assertTrue(path.exists())
        self.browser.open_audio.assert_not_called()
        self.assertIn("--ignore-no-formats-error", self.cli.call_args.args[0])

    def test_dict_serialization_never_walks_the_private_lease_attribute(self):
        info = ingest.BrowserAudioInfo({"id": VIDEO_ID, "title": "Public"}, self.lease)
        self.assertEqual(json.loads(json.dumps(info)), {"id": VIDEO_ID, "title": "Public"})
        serialized = json.dumps(build_metadata(info, self.row, "2026-11-17T00:00:00Z"))
        self.assertNotIn("browser_lease", serialized)
        self.assertNotIn("PRIVATE_LEASE", serialized)
        ingest.close_browser_info(info)
        ingest.close_browser_info(info)
        self.lease.close.assert_called_once_with()

    def test_cli_browser_option_is_opt_in(self):
        self.assertFalse(ingest.parser().parse_args(["plan"]).browser_audio)
        self.assertTrue(ingest.parser().parse_args(["plan", "--browser-audio"]).browser_audio)


@unittest.skipUnless(shutil.which("powershell.exe"), "Requires Windows PowerShell")
class BrowserLauncherTests(unittest.TestCase):
    def test_launcher_forwards_browser_flag_only_when_selected(self):
        with tempfile.TemporaryDirectory(prefix="browser-launcher-offline-") as folder:
            base = Path(folder)
            private = base / "private"
            jobs = private / "jobs"
            jobs.mkdir(parents=True)
            (jobs / "queue_newest20.csv").write_text("video_id\nABCDEFGHIJK\n", encoding="utf-8")
            source = Path(__file__).resolve().parents[1] / "start_drive_ingest.ps1"
            wrapper = base / source.name
            wrapper.write_text(source.read_text(encoding="utf-8").replace(
                "$EtPython = Join-Path $EtScripts 'python.exe'",
                "$EtPython = '" + sys.executable.replace("'", "''") + "'"), encoding="utf-8")
            marker = base / "received-arguments.json"
            (base / "drive_ingest.py").write_text(
                "import json,sys\nfrom pathlib import Path\n"
                + "Path(" + repr(str(marker)) + ").write_text(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
            for enabled in (False, True):
                with self.subTest(enabled=enabled):
                    command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                               "-File", str(wrapper), "-Mode", "Plan", "-PrivateRoot", str(private),
                               "-ToolRoot", str(base / "tools")]
                    if enabled:
                        command.append("-BrowserAudio")
                    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    received = json.loads(marker.read_text(encoding="utf-8"))
                    self.assertEqual(received.count("--browser-audio"), int(enabled))


if __name__ == "__main__":
    unittest.main()
