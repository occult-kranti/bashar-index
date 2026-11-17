"""Standard-library fixtures only: no browser, network, packages or source work."""
import asyncio
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from pipeline import chromium_extensions as c


class Worker:
    def __init__(self, extension_id, path="service-worker.js", manifest=None):
        self.url = f"chrome-extension://{extension_id}/{path}"
        self.manifest = manifest
        self.reads = 0

    async def evaluate(self, expression):
        assert expression == "chrome.runtime.getManifest()"
        self.reads += 1
        return self.manifest


class Context:
    def __init__(self, workers):
        self.service_workers = workers


class FakeBrowser:
    def __init__(self, workers, *, close_error=False):
        self.events = []
        self.live_transport = True
        self.kwargs = None
        self.profile = None
        self.context = Context(workers)
        async def close():
            assert self.live_transport
            self.events.append("close")
            if close_error:
                raise RuntimeError("fixture close failure")
        self.context.close = close
        self.chromium = SimpleNamespace(launch_persistent_context=self.launch)

    async def launch(self, profile, **kwargs):
        self.events.append("launch")
        self.profile, self.kwargs = profile, kwargs
        return self.context


class Extensions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.downloader = self.root / "downloader with spaces"
        self.adblock = self.root / "adblock"
        actual = Path(__file__).resolve().parents[2] / "browser_capture_extension" / "manifest.json"
        self.original = json.loads(actual.read_bytes())
        self.blocker = {"manifest_version": 3, "name": "__MSG_extensionName__", "version": "2026.1116.1650", "background": {"service_worker": "background.js"}}
        self.write(self.downloader, self.original)
        self.write(self.adblock, self.blocker)
        self.executable = self.root / "fake-browser.exe"
        self.executable.write_bytes(b"not executable; fixture only")

    def write(self, path, manifest):
        path.mkdir(exist_ok=True)
        (path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        worker = manifest.get("background", {}).get("service_worker", "service-worker.js")
        if ".." not in worker and ":" not in worker and not worker.startswith("//") and "\\" not in worker and not any(ord(c) < 32 for c in worker):
            target = path / worker.removeprefix("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("// Offline fixture", encoding="utf-8")

    def test_flags_use_both_absolute_paths_and_preserve_downloader_identity(self):
        launch = c.build_extension_launch(self.downloader / "manifest.json", self.adblock)
        joined = f"{self.downloader.resolve()},{self.adblock.resolve()}"
        self.assertEqual(launch.args, (f"--disable-extensions-except={joined}", f"--load-extension={joined}"))
        self.assertEqual(launch.downloader.keyed_id, c.DOWNLOADER_ID)
        self.assertEqual(len(launch.adblocker.manifest_sha256), 64)

    def test_bad_paths_duplicate_and_wrong_mv_fail_closed(self):
        for value in (str(self.adblock) + ",other", str(self.adblock) + "\nother"):
            with self.subTest(value=value), self.assertRaisesRegex(c.ExtensionError, "extension_path_characters"):
                c.build_extension_launch(self.downloader, value)
        with self.assertRaisesRegex(c.ExtensionError, "duplicate_extension_path"):
            c.build_extension_launch(self.downloader, self.downloader / "manifest.json")
        for mv in (2, True, "3"):
            self.write(self.adblock, {**self.blocker, "manifest_version": mv})
            with self.assertRaisesRegex(c.ExtensionError, "extension_manifest_version"):
                c.build_extension_launch(self.downloader, self.adblock)

    def test_wrong_downloader_key_and_escaping_worker_are_rejected(self):
        self.write(self.downloader, {**self.original, "key": "eA=="})
        with self.assertRaisesRegex(c.ExtensionError, "downloader_identity_mismatch"):
            c.build_extension_launch(self.downloader, self.adblock)
        self.write(self.downloader, self.original)
        self.write(self.adblock, {**self.blocker, "background": {"service_worker": "../escape.js"}})
        with self.assertRaisesRegex(c.ExtensionError, "extension_worker_path"):
            c.build_extension_launch(self.downloader, self.adblock)

    async def test_downloader_selection_ignores_first_worker_wrong_id_and_path(self):
        launch = c.build_extension_launch(self.downloader, self.adblock)
        real = Worker(c.DOWNLOADER_ID)
        others = [Worker("a" * 32), Worker(c.DOWNLOADER_ID, "wrong.js"), Worker(c.DOWNLOADER_ID, "service-worker.js?x=1")]
        for workers in (others + [real], [real] + others):
            found = await c.select_downloader_worker(Context(workers), launch.downloader, timeout_seconds=.1)
            self.assertIs(found, real)
        self.assertEqual(sum(w.reads for w in [real] + others), 0)

    async def test_wait_observes_late_worker_without_event_race(self):
        launch = c.build_extension_launch(self.downloader, self.adblock)
        context = Context([])
        real = Worker(c.DOWNLOADER_ID)
        async def add():
            await asyncio.sleep(.01)
            context.service_workers.append(real)
        task = asyncio.create_task(add())
        found = await c.select_downloader_worker(context, launch.downloader, timeout_seconds=.2, poll_interval_seconds=.005)
        await task
        self.assertIs(found, real)

    async def test_wait_bounds_and_missing_worker(self):
        launch = c.build_extension_launch(self.downloader, self.adblock)
        for value in (0, -1, 61, float("nan"), True):
            with self.subTest(timeout=value), self.assertRaisesRegex(c.ExtensionError, "extension_wait_bounds"):
                await c.select_downloader_worker(Context([]), launch.downloader, timeout_seconds=value)
        with self.assertRaisesRegex(c.ExtensionError, "downloader_worker_timeout"):
            await c.select_downloader_worker(Context([Worker("b" * 32)]), launch.downloader, timeout_seconds=.01)

    async def test_adblock_actual_id_and_version_are_separate_from_downloader(self):
        launch = c.build_extension_launch(self.downloader, self.adblock)
        real = Worker("b" * 32, "background.js", {**self.blocker, "name": "Localized public name"})
        wrong_version = Worker("c" * 32, "background.js", {**self.blocker, "version": "0.0.1"})
        result = await c.select_adblock_worker(Context([Worker(c.DOWNLOADER_ID), wrong_version, real]), launch.adblocker, timeout_seconds=.1)
        self.assertIs(result.worker, real)
        self.assertEqual(result.extension_id, "b" * 32)
        self.assertEqual(result.version, self.blocker["version"])

    async def test_root_relative_worker_path_preserves_official_manifest(self):
        manifest = {**self.blocker, "background": {"service_worker": "/js/background.js"}}
        self.write(self.adblock, manifest)
        before = (self.adblock / "manifest.json").read_bytes()
        launch = c.build_extension_launch(self.downloader, self.adblock)
        self.assertEqual(launch.adblocker.worker_path, "js/background.js")
        worker = Worker("b" * 32, "js/background.js", manifest)
        result = await c.select_adblock_worker(Context([worker]), launch.adblocker, timeout_seconds=.1)
        self.assertIs(result.worker, worker)
        self.assertEqual((self.adblock / "manifest.json").read_bytes(), before)

    def test_root_relative_does_not_admit_external_or_escaping_worker_paths(self):
        for worker in ("//js/background.js", "/../outside.js", "https://example.test/a.js", "\\js\\a.js", "/js/back\nground.js"):
            with self.subTest(worker=worker):
                self.write(self.adblock, {**self.blocker, "background": {"service_worker": worker}})
                with self.assertRaisesRegex(c.ExtensionError, "extension_worker_path"):
                    c.build_extension_launch(self.downloader, self.adblock)

    async def test_adblock_manifest_read_and_ambiguity_are_bounded(self):
        launch = c.build_extension_launch(self.downloader, self.adblock)
        workers = [Worker(ch * 32, "background.js", self.blocker) for ch in "bc"]
        with self.assertRaisesRegex(c.ExtensionError, "ambiguous_adblock_worker"):
            await c.select_adblock_worker(Context(workers), launch.adblocker, timeout_seconds=.1)
        class Hanging(Worker):
            async def evaluate(self, expression):
                await asyncio.sleep(10)
        with self.assertRaisesRegex(c.ExtensionError, "adblock_worker_timeout"):
            await c.select_adblock_worker(Context([Hanging("b" * 32, "background.js")]), launch.adblocker, timeout_seconds=.01)

    def factory(self, browser, **kwargs):
        args = dict(owned_profile_path=self.root / "new-owned-profile", executable_path=self.executable,
                    downloader_dir=self.downloader, adblocker_dir=self.adblock, worker_timeout_seconds=.01)
        args.update(kwargs)
        return c.launch_project_chromium(browser, **args)

    async def test_factory_loads_both_roles_and_closes_inside_transport(self):
        downloader = Worker(c.DOWNLOADER_ID, manifest=self.original)
        blocker = Worker("b" * 32, "background.js", self.blocker)
        browser = FakeBrowser([blocker, downloader])
        profile = self.root / "new-owned-profile"
        profile.mkdir()
        async with self.factory(browser, launch_args=("--mute-audio",), viewport={"width": 1100, "height": 800}) as session:
            browser.events.append("body")
            self.assertIs(session.downloader_worker, downloader)
            self.assertIs(session.adblocker.worker, blocker)
            self.assertIs(session.context, browser.context)
            self.assertEqual(browser.kwargs["args"], [*session.launch.args, "--mute-audio"])
            self.assertEqual(browser.kwargs["service_workers"], "block")
            self.assertFalse(session.closed)
        browser.live_transport = False
        self.assertEqual(browser.events, ["launch", "body", "close"])
        self.assertTrue(session.closed)
        self.assertTrue(profile.is_dir())  # Cleanup belongs to the profile owner.
        self.assertEqual(downloader.reads, 1)

    async def test_factory_closes_when_runtime_manifest_validation_fails(self):
        browser = FakeBrowser([Worker(c.DOWNLOADER_ID, manifest={**self.original, "version": "9.9"})])
        with self.assertRaisesRegex(c.ExtensionError, "downloader_manifest_mismatch"):
            async with self.factory(browser):
                self.fail("invalid extension yielded")
        self.assertEqual(browser.events, ["launch", "close"])

    async def test_factory_preserves_body_failure_if_close_also_fails(self):
        browser = FakeBrowser([Worker(c.DOWNLOADER_ID, manifest=self.original), Worker("b" * 32, "background.js", self.blocker)], close_error=True)
        with self.assertRaisesRegex(RuntimeError, "original_fixture_failure"):
            async with self.factory(browser) as session:
                raise RuntimeError("original_fixture_failure")
        self.assertEqual(browser.events, ["launch", "close"])
        self.assertEqual(session.cleanup_error, "context_close_unconfirmed")
        self.assertFalse(session.closed)

    async def test_factory_rejects_profile_and_argument_overrides_before_launch(self):
        browser = FakeBrowser([])
        for argument in ("https://example.test/", "--load-extension=elsewhere", "--disable-extensions",
                         "--user-data-dir=personal", "--profile-directory=Default", "--app=https://example.test/",
                         "--restore-last-session", "--homepage=https://example.test/", "--mute-audio\n--url=x"):
            with self.subTest(argument=argument), self.assertRaisesRegex(c.ExtensionError, "chromium_launch_arguments"):
                async with self.factory(browser, launch_args=[argument]):
                    self.fail("invalid argument yielded")
        profile = self.root / "new-owned-profile"
        profile.mkdir()
        (profile / "Preferences").write_text("existing profile", encoding="utf-8")
        with self.assertRaisesRegex(c.ExtensionError, "chromium_owned_paths"):
            async with self.factory(browser):
                self.fail("existing profile yielded")
        self.assertEqual(browser.events, [])


if __name__ == "__main__":
    unittest.main()
