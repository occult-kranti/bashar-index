"""Offline Windows launcher regression: build and launch the same final queue."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which('powershell.exe'), 'Requires Windows PowerShell')
class FinalQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.private = self.base / 'private'
        jobs = self.private / 'jobs'
        jobs.mkdir(parents=True)
        self.canonical = jobs / 'queue_final_round.csv'
        self.custom = jobs / 'unchecked_custom.csv'
        self.custom.write_text('existing custom queue must not run or change', encoding='utf-8')
        for name in ('queue_newest20.csv', 'queue_newest50.csv', 'queue_youtube_all_merged.csv'):
            (jobs / name).write_text('video_id\nabcdefghijk\n', encoding='utf-8')
        wrapper = Path(__file__).resolve().parents[1] / 'start_drive_ingest.ps1'
        code = wrapper.read_text(encoding='utf-8').replace(
            "$EtPython = Join-Path $EtScripts 'python.exe'",
            "$EtPython = '" + sys.executable.replace("'", "''") + "'")
        self.wrapper = self.base / wrapper.name
        self.wrapper.write_text(code, encoding='utf-8')
        self.marker = self.private / 'unexpected-collector-call'
        (self.base / 'drive_ingest.py').write_text(
            'from pathlib import Path\nPath(' + repr(str(self.marker)) + ').touch()\n', encoding='utf-8')
        (self.base / 'prepare_collection_stages.py').write_text(
            "import sys\nfrom pathlib import Path\n"
            "jobs=Path(sys.argv[sys.argv.index('--out-dir')+1])\n"
            "(jobs/'queue_final_round.csv').write_text('freshly built queue')\n", encoding='utf-8')
        self.tools = self.base / 'tools'
        (self.tools / 'venv' / 'Scripts').mkdir(parents=True)
        for path in (self.tools / 'rclone.exe', self.tools / 'venv' / 'Scripts' / 'yt-dlp.exe'):
            path.touch()

    def launch(self, mode, final_queue=None):
        command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(self.wrapper),
                   '-Mode', mode, '-PrivateRoot', str(self.private), '-ToolRoot', str(self.tools)]
        if final_queue is not None:
            command.extend(['-FinalQueue', str(final_queue)])
        return subprocess.run(command, capture_output=True, text=True, timeout=20)

    def assert_rejected_before_build_or_collection(self, mode):
        result = self.launch(mode, self.custom)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('custom -FinalQueue is supported only', result.stderr)
        self.assertFalse(self.marker.exists())
        self.assertFalse(self.canonical.exists())
        self.assertEqual(self.custom.read_text(), 'existing custom queue must not run or change')

    def test_runall_rejects_unbuilt_custom_queue_before_any_child_process(self):
        self.assert_rejected_before_build_or_collection('RunAll')

    def test_index_rejects_custom_output_instead_of_silently_ignoring_it(self):
        self.assert_rejected_before_build_or_collection('Index')

    def test_index_accepts_default_and_normalized_equivalent_builder_path(self):
        for path in (None, self.canonical.parent / '..' / 'jobs' / self.canonical.name):
            with self.subTest(path=path):
                self.canonical.unlink(missing_ok=True)
                result = self.launch('Index', path)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.canonical.read_text(), 'freshly built queue')
                self.assertFalse(self.marker.exists())


if __name__ == '__main__':
    unittest.main()
