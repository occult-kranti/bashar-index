"""Offline session lifetime/admission tests; no yt-dlp/browser/network imports."""
import asyncio
import contextlib
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import browser_audio as audio
REAL_CONFIGURE = audio._configure

URL = "https://www.youtube.com/watch?v=ABCDEFGHIJK"
SECRET = "https://example.com/PRIVATE?pot=SECRET_TOKEN Authorization: Bearer PRIVATE_KEY"


class FakeBrowser:
    def __init__(self):
        self.stopped = False
        self.stop_threads = []

    def stop(self):
        self.stopped = True
        self.stop_threads.append(threading.get_ident())


class FakeYDL:
    def __init__(self, options, owner):
        self.params, self.owner = options, owner
        self.entered = False
        self.exited = 0
        self.browser = FakeBrowser()
        self.provider = type("Provider", (), {})()
        self.provider._browser = self.browser
        self.director = type("Director", (), {"providers": {"wpc": self.provider}})()
        self._ies_instances = {"Youtube": type("Extractor", (), {"_pot_director": self.director})()}
        self._close_hooks = [self.browser.stop]
        self.calls = []

    def __enter__(self):
        if self.owner.enter_error:
            raise RuntimeError(SECRET)
        self.entered = True
        return self

    def __exit__(self, *_args):
        self.exited += 1
        if self.owner.close_error:
            raise RuntimeError(SECRET)
        self.close()

    def close(self):
        self.browser.stop()

    def extract_info(self, url, download):
        self.calls.append((url, download))
        if self.owner.provider_loop:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.provider._WPCPTP__loop = loop
        if self.owner.warning:
            self.params["logger"].warning(self.owner.warning)
        if self.owner.error:
            self.params["logger"].error(self.owner.error)
            raise RuntimeError(self.owner.error)
        return dict(self.owner.info)


class Factory:
    def __init__(self):
        self.instances = []
        self.info = {"id": "ABCDEFGHIJK", "url": "https://media.googlevideo.com/audio?pot=SECRET_TOKEN"}
        self.error = self.warning = None
        self.close_error = self.enter_error = self.provider_loop = False

    def __call__(self, options):
        ydl = FakeYDL(options, self)
        self.instances.append(ydl)
        return ydl


class BrowserAudioTests(unittest.TestCase):
    def setUp(self):
        self.previous = asyncio.new_event_loop()
        asyncio.set_event_loop(self.previous)
        self.factory = Factory()
        self.patches = [patch.object(audio, "_configure", return_value=self.factory),
                        patch.object(audio, "_SLOTS", threading.BoundedSemaphore(4)),
                        patch.object(audio, "_CLEANUP_FAILED", threading.Event()),
                        patch.object(audio, "_THREAD", threading.local())]
        self.configure = self.patches[0].start()
        for item in self.patches[1:]:
            item.start()

    def tearDown(self):
        lease = getattr(audio._THREAD, "lease", None)
        if lease is not None:
            lease.close()
        for item in reversed(self.patches):
            item.stop()
        self.previous.close()
        asyncio.set_event_loop(None)

    def test_import_does_not_load_optional_dependencies_or_open_resources(self):
        code = "import sys;sys.path.insert(0,sys.argv[1]);import browser_audio;assert 'yt_dlp' not in sys.modules;assert 'nodriver' not in sys.modules"
        result = subprocess.run([sys.executable, "-c", code, str(Path(audio.__file__).parent)], capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"")

    def test_context_lives_until_stream_finally_and_close_is_idempotent(self):
        info, lease = audio.open_audio(URL, 15)
        ydl = self.factory.instances[0]
        self.assertTrue(ydl.entered)
        self.assertFalse(ydl.browser.stopped)
        self.assertEqual(ydl.exited, 0)
        self.assertIn("SECRET_TOKEN", info["url"])
        with lease:
            self.assertFalse(ydl.browser.stopped)
        lease.close()
        self.assertTrue(ydl.browser.stopped)
        self.assertEqual(ydl.exited, 1)
        self.assertEqual(ydl.browser.stop_threads, [threading.get_ident()])
        self.assertIs(asyncio.get_event_loop(), self.previous)

    def test_provider_worker_loop_and_initial_loop_close_on_owner_thread(self):
        self.factory.provider_loop = True
        def worker():
            info, lease = audio.open_audio(URL, 10)
            self.assertEqual(len(lease._loops), 2)
            loops = list(lease._loops)
            lease.close()
            return all(loop.is_closed() for loop in loops), audio._current_loop()
        with ThreadPoolExecutor(max_workers=1) as pool:
            self.assertEqual(pool.submit(worker).result(timeout=5), (True, None))

    def test_owned_async_browser_process_finishes_before_provider_loop_closes(self):
        self.factory.provider_loop = True
        _, lease = audio.open_audio(URL, 10)
        ydl = self.factory.instances[0]
        class Process:
            returncode = None
            waited = False
            async def wait(self):
                self.waited = not asyncio.get_running_loop().is_closed()
                self.returncode = 0
                return 0
        process = Process()
        ydl.browser._process = process
        provider_loop = ydl.provider._WPCPTP__loop
        lease.close()
        self.assertTrue(process.waited)
        self.assertEqual(process.returncode, 0)
        self.assertTrue(provider_loop.is_closed())

    def test_lazy_provider_setup_runs_once_and_uses_only_fresh_headless_configuration(self):
        class Provider:
            pass
        preferences = []
        plugins = SimpleNamespace(load_all_plugins=Mock())
        register = Mock(side_effect=lambda cls: lambda preference: preferences.append((cls, preference)))
        config_type = Mock(return_value=SimpleNamespace(uses_custom_data_dir=True))
        modules = {"yt_dlp.plugins": plugins, "yt_dlp_plugins.extractor.getpot_wpc": SimpleNamespace(WPCPTP=Provider),
                   "yt_dlp.extractor.youtube.pot.provider": SimpleNamespace(register_preference=register),
                   "nodriver.core.config": SimpleNamespace(Config=config_type), "yt_dlp": SimpleNamespace(YoutubeDL=self.factory)}
        with patch.object(audio, "_YOUTUBE_DL", None), patch.object(audio, "_INIT_LOCK", threading.Lock()), \
                patch.object(audio.importlib, "import_module", side_effect=modules.__getitem__):
            self.assertIs(REAL_CONFIGURE(1), self.factory)
            self.assertIs(REAL_CONFIGURE(1), self.factory)
            plugins.load_all_plugins.assert_called_once_with()
            register.assert_called_once_with(Provider)
            self.assertEqual(preferences[0][1](None, None), 100000)
            Provider().get_nodriver_config()
            config_type.assert_called_once_with(headless=True)
            with self.assertRaises(audio.BrowserAudioError):
                Provider().get_nodriver_config(proxy="http://PRIVATE")

    def test_wrong_thread_cannot_close_live_context(self):
        _, lease = audio.open_audio(URL, 10)
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(lease.close)
            with self.assertRaises(audio.BrowserAudioError) as caught:
                future.result(timeout=5)
        self.assertEqual(caught.exception.kind, "browser_thread")
        self.assertFalse(lease.closed)
        self.assertFalse(self.factory.instances[0].browser.stopped)
        lease.close()

    def test_four_live_leases_bound_admission_without_a_fifth_browser(self):
        ready = threading.Barrier(5)
        release = threading.Event()
        def worker():
            _, lease = audio.open_audio(URL, 2)
            try:
                ready.wait(timeout=3)
                release.wait(timeout=3)
            finally:
                lease.close()
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(worker) for _ in range(4)]
            try:
                ready.wait(timeout=3)
                with self.assertRaises(audio.BrowserAudioError) as caught:
                    audio.open_audio(URL, 0.01)
                self.assertEqual(caught.exception.kind, "browser_busy")
                self.assertEqual(len(self.factory.instances), 4)
            finally:
                release.set()
            for future in futures:
                future.result(timeout=5)
        _, lease = audio.open_audio(URL, 0.01)
        lease.close()

    def test_nested_same_worker_lease_is_rejected_without_closing_first(self):
        _, first = audio.open_audio(URL, 10)
        with self.assertRaises(audio.BrowserAudioError) as caught:
            audio.open_audio(URL, 10)
        self.assertEqual(caught.exception.kind, "browser_context")
        self.assertFalse(first.closed)

    def test_metadata_only_tolerates_missing_formats_and_simulates_english_captions(self):
        self.factory.info = {"id": "ABCDEFGHIJK", "formats": []}
        info, lease = audio.open_audio(URL, 60, metadata_only=True)
        options = self.factory.instances[0].params
        self.assertEqual(info["formats"], [])
        self.assertTrue(options["ignore_no_formats_error"])
        self.assertNotIn("format", options)
        self.assertTrue(options["simulate"] and options["skip_download"])
        self.assertTrue(options["writesubtitles"] and options["writeautomaticsub"])
        self.assertEqual(options["subtitleslangs"], ["en.*"])
        self.assertEqual(options["subtitlesformat"], "json3/vtt")
        self.assertEqual(options["socket_timeout"], 30)
        self.assertEqual(self.factory.instances[0].calls, [(URL, False)])
        lease.close()

    def test_audio_configuration_has_native_format_no_proxy_cookies_or_retries(self):
        _, lease = audio.open_audio(URL, 10)
        options = self.factory.instances[0].params
        self.assertEqual(options["format"], "bestaudio[protocol=https][vcodec=none]")
        self.assertEqual(options["extractor_args"], {"youtube": {"player_client": ["mweb"]}})
        self.assertEqual(options["proxy"], "")
        for field in ("retries", "extractor_retries", "fragment_retries", "file_access_retries"):
            self.assertEqual(options[field], 0)
        self.assertNotIn("cookiefile", options)
        self.assertNotIn("cookiesfrombrowser", options)
        self.assertFalse(options["cachedir"])
        lease.close()

    def test_forbidden_and_other_failures_close_once_without_retry_or_secret_output(self):
        for message, expected in [("HTTP Error 403: Forbidden " + SECRET, "forbidden"),
                                  ("HTTP Error 429: Too Many Requests " + SECRET, "rate_limited"),
                                  ("Sign in to confirm you are not a bot " + SECRET, "bot_check"),
                                  ("Requested format is not available " + SECRET, "no_formats"),
                                  ("unexpected " + SECRET, "other")]:
            with self.subTest(expected=expected):
                self.factory.error = message
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    with self.assertRaises(audio.BrowserAudioError) as caught:
                        audio.open_audio(URL, 10)
                self.assertEqual(caught.exception.kind, expected)
                self.assertNotIn("PRIVATE", str(caught.exception))
                self.assertNotIn("SECRET", repr(caught.exception))
                self.assertTrue(caught.exception.__suppress_context__)
                self.assertEqual(output.getvalue(), "")
                ydl = self.factory.instances[-1]
                self.assertEqual(len(ydl.calls), 1)
                self.assertEqual(ydl.exited, 1)
                self.assertTrue(ydl.browser.stopped)

    def test_explicit_premiere_is_live_but_arbitrary_title_text_is_not(self):
        for message, kind in [("ERROR: [youtube] ABCDEFGHIJK: Premieres in 20 minutes", "live"),
                              ("WARNING: title Premieres in 20 minutes " + SECRET, "other")]:
            self.factory.error = message
            with self.assertRaises(audio.BrowserAudioError) as caught:
                audio.open_audio(URL, 10)
            self.assertEqual(caught.exception.kind, kind)

    def test_caption_warning_is_constant_and_never_preserves_warning_text(self):
        self.factory.warning = "Subtitles require a PO Token " + SECRET
        info, lease = audio.open_audio(URL, 10, caption_intent=True)
        self.assertEqual(info["_caption_access_warning"], "subtitle_access_requirement")
        self.assertNotIn(SECRET, json.dumps(info))
        logger = self.factory.instances[0].params["logger"]
        self.assertNotIn(SECRET, repr(vars(logger)))
        lease.close()

    def test_metadata_mismatch_and_live_result_close_before_return(self):
        for info, kind in [({"id": "WRONG______"}, "metadata"),
                           ({"id": "ABCDEFGHIJK", "live_status": "is_upcoming"}, "live")]:
            self.factory.info = info
            with self.assertRaises(audio.BrowserAudioError) as caught:
                audio.open_audio(URL, 10)
            self.assertEqual(caught.exception.kind, kind)
            self.assertTrue(self.factory.instances[-1].browser.stopped)

    def test_failed_enter_cleans_up_and_cleanup_failure_blocks_new_leases(self):
        self.factory.enter_error = True
        with self.assertRaises(audio.BrowserAudioError):
            audio.open_audio(URL, 10)
        self.assertTrue(self.factory.instances[-1].browser.stopped)
        self.factory.enter_error = False
        self.factory.close_error = True
        _, lease = audio.open_audio(URL, 10)
        lease.close()
        self.assertEqual(lease.cleanup_error, "browser_cleanup")
        self.assertTrue(self.factory.instances[-1].browser.stopped)
        self.factory.close_error = False
        calls = len(self.factory.instances)
        with self.assertRaises(audio.BrowserAudioError) as caught:
            audio.open_audio(URL, 0.01)
        self.assertEqual(caught.exception.kind, "browser_cleanup")
        self.assertEqual(len(self.factory.instances), calls)

    def test_cleanup_failure_preserves_source_error_and_other_live_lease_can_close(self):
        ready, finish = threading.Event(), threading.Event()
        def existing_worker():
            _, existing = audio.open_audio(URL, 2)
            browser = self.factory.instances[-1].browser
            ready.set()
            finish.wait(timeout=3)
            existing.close()
            return existing.closed, browser.stopped
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(existing_worker)
            self.assertTrue(ready.wait(timeout=3))
            try:
                self.factory.error = "HTTP Error 403: Forbidden " + SECRET
                self.factory.close_error = True
                with self.assertRaises(audio.BrowserAudioError) as caught:
                    audio.open_audio(URL, 1)
                self.assertEqual(caught.exception.kind, "forbidden")
                self.assertNotIn("SECRET", str(caught.exception))
                self.assertTrue(audio._CLEANUP_FAILED.is_set())
                self.factory.error = None
                self.factory.close_error = False
                with self.assertRaises(audio.BrowserAudioError) as blocked:
                    audio.open_audio(URL, 0.01)
                self.assertEqual(blocked.exception.kind, "browser_cleanup")
            finally:
                finish.set()
            self.assertEqual(future.result(timeout=5), (True, True))

    def test_cleanup_failure_while_waiting_for_capacity_releases_slot_without_start(self):
        def acquire(**_kwargs):
            audio._CLEANUP_FAILED.set()
            return True
        slots = Mock(acquire=Mock(side_effect=acquire))
        with patch.object(audio, "_SLOTS", slots):
            with self.assertRaises(audio.BrowserAudioError) as caught:
                audio.open_audio(URL, 1)
        self.assertEqual(caught.exception.kind, "browser_cleanup")
        slots.release.assert_called_once_with()
        self.configure.assert_not_called()

    def test_only_owned_temporary_profiles_are_removed(self):
        _, lease = audio.open_audio(URL, 10)
        owned = Path(tempfile.mkdtemp(prefix="uc_"))
        with tempfile.TemporaryDirectory(prefix="unowned_") as other:
            class Config:
                uses_custom_data_dir = False
            config = Config()
            config.user_data_dir = owned
            lease._track_profile(config)
            config.user_data_dir = other
            lease._track_profile(config)
            lease.close()
            self.assertFalse(owned.exists())
            self.assertTrue(Path(other).exists())

    def test_invalid_inputs_never_acquire_or_initialize_browser(self):
        for timeout in (0, -1, float("nan"), float("inf"), "bad"):
            with self.subTest(timeout=timeout), self.assertRaises(audio.BrowserAudioError):
                audio.open_audio(URL, timeout)
        for url in ("http://www.youtube.com/watch?v=ABCDEFGHIJK", "https://user:secret@youtube.com/watch?v=ABCDEFGHIJK",
                    "https://example.com/watch?v=ABCDEFGHIJK", "https://youtube.com/playlist?list=secret"):
            with self.subTest(url=url), self.assertRaises(audio.BrowserAudioError):
                audio.open_audio(url, 10)
        self.configure.assert_not_called()
        self.assertEqual(self.factory.instances, [])


if __name__ == "__main__":
    unittest.main()
