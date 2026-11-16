"""Offline Windows supervisor regression tests; every child is a temporary stub.

Run: python -m unittest discover -s et-channelers/pipeline/tests
     -p test_supervise_drive_ingest.py -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


POWERSHELL = shutil.which("powershell.exe")
SUPERVISOR = Path(__file__).resolve().parents[1] / "supervise_drive_ingest.ps1"
LAUNCHER = SUPERVISOR.with_name("start_drive_ingest.ps1")


def ps_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


@unittest.skipUnless(sys.platform == "win32" and POWERSHELL, "Windows PowerShell required")
class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="supervisor-offline-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "private"
        self.sync = self.root / "sync"
        self.sync.mkdir(parents=True)
        self.launcher = self.base / "start_drive_ingest.ps1"
        self.launcher.write_text(
            "param([string]$PrivateRoot, [Parameter(ValueFromRemainingArguments=$true)]$Rest)\n"
            "Add-Content -LiteralPath (Join-Path $PrivateRoot 'child-calls.txt') -Value 'call'\n"
            "exit ([int](Get-Content -LiteralPath (Join-Path $PrivateRoot 'child-exit.txt') -Raw))\n",
            encoding="utf-8",
        )
        (self.root / "child-exit.txt").write_text("0", encoding="utf-8")

    def command(self, *extra):
        return [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SUPERVISOR),
                "-LauncherPath", str(self.launcher), "-PrivateRoot", str(self.root), *extra]

    def run_supervisor(self, *extra):
        return subprocess.run(self.command(*extra), capture_output=True, text=True, timeout=25)

    def state(self):
        return json.loads((self.sync / "drive_ingest_resume_state.json").read_text(encoding="utf-8-sig"))

    def calls(self):
        path = self.root / "child-calls.txt"
        return path.read_text(encoding="utf-8-sig").splitlines() if path.exists() else []

    def write_state(self, value):
        (self.sync / "drive_ingest_resume_state.json").write_text(json.dumps(value), encoding="utf-8")

    def waiting_process(self, *extra):
        process = subprocess.Popen(self.command(*extra), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True)
        self.addCleanup(self.close_process, process)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.fail(f"Supervisor exited before waiting: {stdout} {stderr}")
            if (self.sync / "drive_ingest_resume_state.json").exists():
                try:
                    if self.state().get("state") == "waiting_for_drive_cooldown":
                        return process
                except (OSError, ValueError):
                    pass  # Windows can briefly deny a read during atomic replacement.
            time.sleep(0.05)
        self.fail("Supervisor did not publish its waiting state")

    @staticmethod
    def close_process(process):
        if process.poll() is None:
            process.terminate()
        process.communicate(timeout=10)

    def test_success_replaces_durable_state_on_windows(self):
        result = self.run_supervisor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.state()["state"], "stages_complete")
        self.assertEqual(self.state()["attempts"], 1)
        self.assertFalse((self.sync / "drive_ingest_resume_state.json.tmp").exists())

    def test_quota_budget_survives_restart_and_preserves_backoff(self):
        (self.root / "child-exit.txt").write_text("75", encoding="utf-8")
        result = self.run_supervisor("-MaxAttempts", "1")
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertEqual(self.state()["state"], "retry_budget_exhausted")
        self.assertGreaterEqual(self.state()["until_epoch"], time.time() + 580)
        again = self.run_supervisor("-MaxAttempts", "1")
        self.assertEqual(again.returncode, 75, again.stderr)
        self.assertEqual(len(self.calls()), 1, "Restart must not replenish attempts")

    def test_nonquota_failure_and_stop_do_not_retry(self):
        (self.root / "child-exit.txt").write_text("3", encoding="utf-8")
        result = self.run_supervisor()
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        (self.sync / "STOP_DRIVE_INGEST").touch()
        stopped = self.run_supervisor()
        self.assertEqual(stopped.returncode, 130, stopped.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_bad_cooldown_or_incomplete_retry_state_fails_closed(self):
        cooldown = self.sync / "drive_ingest_cooldown.json"
        cooldown.write_text("{bad", encoding="utf-8")
        result = self.run_supervisor()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])
        cooldown.unlink()
        self.write_state({"schema_version": 2})
        result = self.run_supervisor()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), [])

    def test_wait_holds_exclusive_lock_and_stop_interrupts_wait(self):
        (self.sync / "drive_ingest_cooldown.json").write_text(
            json.dumps({"until_epoch": time.time() + 1000}), encoding="utf-8")
        first = self.waiting_process()
        duplicate = self.run_supervisor()
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertEqual(self.calls(), [])
        before = time.monotonic()
        (self.sync / "STOP_DRIVE_INGEST").touch()
        first.communicate(timeout=6)
        self.assertEqual(first.returncode, 130)
        self.assertLess(time.monotonic() - before, 3.5)
        self.assertEqual(self.calls(), [])

    def test_explicit_budget_reset_retains_recorded_wait(self):
        deadline = time.time() + 1000
        self.write_state({"schema_version": 2, "attempts": 3, "until_epoch": deadline,
                          "exit_code": 75, "state": "retry_budget_exhausted"})
        first = self.waiting_process("-ResetRetryBudget")
        self.assertEqual(self.state()["attempts"], 0)
        self.assertAlmostEqual(self.state()["until_epoch"], deadline, places=5)
        self.assertEqual(self.calls(), [])
        (self.sync / "STOP_DRIVE_INGEST").touch()
        first.communicate(timeout=6)
        self.assertEqual(first.returncode, 130)

    def test_legacy_one_attempt_is_not_forgotten(self):
        self.write_state({"state": "paused_after_one_attempt", "one_attempt": True, "exit_code": 75})
        result = self.run_supervisor("-MaxAttempts", "1")
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertEqual(self.state()["attempts"], 1)
        self.assertEqual(self.calls(), [])

    def test_defaults_use_profile_root_and_adjacent_launcher(self):
        # Copy only the supervisor and fake child; default resolution cannot reach real jobs.
        adjacent = self.base / "supervise_drive_ingest.ps1"
        shutil.copyfile(SUPERVISOR, adjacent)
        profile = self.base / "fake-profile"
        private = profile / "et-channelers-private"
        private.mkdir(parents=True)
        (private / "child-exit.txt").write_text("0", encoding="utf-8")
        environment = dict(os.environ, USERPROFILE=str(profile))
        result = subprocess.run([POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(adjacent)],
                                env=environment, capture_output=True, text=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((private / "child-calls.txt").exists())
        self.assertFalse((self.root / "child-calls.txt").exists())

    def test_supervisor_preserves_native_exit_codes_when_stderr_is_redirected(self):
        original = self.launcher.read_text(encoding="utf-8")
        self.launcher.write_text(original.replace(
            "Add-Content", "[Console]::Error.WriteLine('benign native warning')\nAdd-Content", 1),
            encoding="utf-8")
        for code in (0, 75):
            with self.subTest(code=code):
                for name in ("drive_ingest_resume_state.json", "drive_ingest_resume_state.json.tmp"):
                    (self.sync / name).unlink(missing_ok=True)
                (self.root / "child-exit.txt").write_text(str(code), encoding="utf-8")
                log = self.base / f"supervisor-stderr-{code}.log"
                command = (f"$ErrorActionPreference='Stop'; & {ps_literal(SUPERVISOR)} "
                           f"-LauncherPath {ps_literal(self.launcher)} -PrivateRoot {ps_literal(self.root)} "
                           f"-MaxAttempts 1 *> {ps_literal(log)}; exit $LASTEXITCODE")
                result = subprocess.run([POWERSHELL, "-NoProfile", "-Command", command],
                                        capture_output=True, text=True, timeout=25)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertIn("benign native warning", log.read_text(encoding="utf-16"))
                self.assertEqual(self.state()["exit_code"], code)

    def test_launcher_native_helper_keeps_stderr_and_exit_code_under_outer_redirect(self):
        # Read only the actual helper AST; never execute the launcher's top-level code.
        for code in (0, 75):
            with self.subTest(code=code):
                log = self.base / f"launcher-stderr-{code}.log"
                child = f"import sys; print('benign Python warning', file=sys.stderr); sys.exit({code})"
                command = (
                    "$ErrorActionPreference='Stop'; $tokens=$null; $errors=$null; "
                    f"$ast=[System.Management.Automation.Language.Parser]::ParseFile({ps_literal(LAUNCHER)},[ref]$tokens,[ref]$errors); "
                    "$fn=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] "
                    "-and $node.Name -eq 'Invoke-EtPython'},$true); "
                    ". ([ScriptBlock]::Create($fn.Extent.Text)); "
                    f"$EtPython={ps_literal(sys.executable)}; "
                    f"& {{ Invoke-EtPython -Arguments @('-c',{ps_literal(child)}); 'after-native-call' }} "
                    f"*> {ps_literal(log)}; exit $EtExitCode"
                )
                result = subprocess.run([POWERSHELL, "-NoProfile", "-Command", command],
                                        capture_output=True, text=True, timeout=25)
                self.assertEqual(result.returncode, code, result.stderr)
                output = log.read_text(encoding="utf-16")
                self.assertIn("benign Python warning", output)
                self.assertIn("after-native-call", output)


if __name__ == "__main__":
    unittest.main()
