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

    def write_caption_summary(self, deadline=0, pending=1, error_class='rate_limited'):
        value = {'schema_version':1, 'policy':'english-published-and-original-automatic-v1',
                 'remote':'etdrive:04 Audio', 'updated_at':'2026-11-16T00:00:00Z',
                 'pending_verified_audio_videos':pending, 'pending_source_videos':pending,
                 'retry_not_before_epoch':deadline, 'error_class':error_class}
        (self.sync / 'drive_caption_backfill_state.json').write_text(json.dumps(value), encoding='utf-8')

    def waiting_process(self, *extra, state_name="waiting_for_drive_cooldown"):
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
                    current = self.state()
                    if current.get("state") == state_name and current.get("supervisor_pid") == process.pid:
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
        self.assertEqual(self.state()["private_root_ceiling_bytes"], 17_000_000_000)
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

    def test_startup_waits_for_source_deadline_before_launching(self):
        deadline = time.time() + 5
        (self.sync / 'drive_ingest_manifest.jsonl').write_text(json.dumps({
            'video_id': 'invented-id', 'status': 'error', 'error_class': 'forbidden',
            'retry_not_before_epoch': deadline}) + '\n', encoding='utf-8')
        original = self.launcher.read_text(encoding='utf-8')
        self.launcher.write_text(original.replace('Add-Content',
            "[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() | Set-Content -LiteralPath (Join-Path $PrivateRoot 'started-ms.txt')\nAdd-Content", 1), encoding='utf-8')
        first = self.waiting_process(state_name='waiting_for_youtube_cooldown')
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.state()['cooldown_provider'], 'youtube')
        first.communicate(timeout=12)
        self.assertEqual(first.returncode, 0)
        started = int((self.root / 'started-ms.txt').read_text(encoding='utf-8-sig'))
        self.assertGreaterEqual(started, deadline * 1000)

    def test_exit3_with_confirmed_source_block_waits_and_caches_journal(self):
        original = self.launcher.read_text(encoding='utf-8')
        self.launcher.write_text(original[:original.index('exit (')] +
            "$future=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()+30\n"
            "@{video_id='invented-id';status='error';error_class='bot_check';retry_not_before_epoch=$future} | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PrivateRoot 'sync/drive_ingest_manifest.jsonl') -Encoding UTF8\n"
            "exit 3\n", encoding='utf-8')
        first = self.waiting_process(state_name='waiting_for_youtube_cooldown')
        state = self.state()
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(state['exit_code'], 3)
        self.assertEqual(state['attempts'], 1)
        self.assertGreaterEqual(state['until_epoch'], time.time() + 580)
        # A reread inside the wait loop would fail on this invalid replacement.
        (self.sync / 'drive_ingest_manifest.jsonl').write_text(json.dumps({
            'video_id': 'invented-id', 'error_class': 'forbidden',
            'retry_not_before_epoch': 'invalid'}) + '\n', encoding='utf-8')
        time.sleep(2.5)
        self.assertIsNone(first.poll(), 'The waiting loop must use its cached source deadline')
        (self.sync / 'STOP_DRIVE_INGEST').touch()
        first.communicate(timeout=6)
        self.assertEqual(first.returncode, 130)
        self.assertEqual(len(self.calls()), 1)

    def test_caption_cooldown_does_not_delay_audio_startup(self):
        now = time.time()
        video = 'same-video'
        (self.sync / 'drive_ingest_manifest.jsonl').write_text(
            json.dumps({'video_id': video, 'error_class': 'forbidden', 'retry_not_before_epoch': now + 1000}) + '\n' +
            json.dumps({'video_id': video, 'status': 'deleted'}) + '\n', encoding='utf-8')
        (self.sync / 'drive_caption_manifest.jsonl').write_text(
            json.dumps({'video_id': video, 'error_class': 'forbidden', 'retry_not_before_epoch': now + 2000}) + '\n' +
            json.dumps({'video_id': video, 'status': 'pending', 'error_class': 'drive_rate_limited',
                        'source_error_class': 'rate_limited',
                        'retry_not_before_epoch': now + 30}) + '\n', encoding='utf-8')
        result = self.run_supervisor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.state()['source_until_epoch'], 0)

    def test_caption_only_block_does_not_make_an_audio_exit3_retryable(self):
        original = self.launcher.read_text(encoding='utf-8')
        self.launcher.write_text(original[:original.index('exit (')] +
            "$future=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()+30\n"
            "@{video_id='same-video';status='pending';error_class='forbidden';retry_not_before_epoch=$future} | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PrivateRoot 'sync/drive_caption_manifest.jsonl') -Encoding UTF8\n"
            "exit 3\n", encoding='utf-8')
        (self.sync / 'drive_ingest_manifest.jsonl').write_text(
            json.dumps({'video_id': 'same-video', 'status': 'deleted'}) + '\n', encoding='utf-8')
        result = self.run_supervisor()
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.state()['state'], 'stopped_after_nonquota_result')

    def test_legacy_caption_global_wait_migrates_without_erasing_a_real_drive_wait(self):
        deadline = time.time() + 1000
        (self.sync / 'drive_caption_manifest.jsonl').write_text(json.dumps({
            'video_id':'same-video','source_error_class':'rate_limited',
            'retry_not_before_epoch':deadline})+'\n', encoding='utf-8')
        prior = {'schema_version':2,'state':'stopped','attempts':0,'until_epoch':deadline,
                 'source_until_epoch':deadline,'exit_code':130,'cooldown_provider':'youtube'}
        self.write_state(prior)
        result = self.run_supervisor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(self.state()['cooldown_scope_version'], 1)
        self.write_state(prior)
        (self.root / 'child-calls.txt').unlink()
        drive_deadline = time.time() + 30
        (self.sync / 'drive_ingest_cooldown.json').write_text(
            json.dumps({'until_epoch':drive_deadline}), encoding='utf-8')
        first = self.waiting_process()
        self.assertEqual(self.calls(), [])
        self.assertAlmostEqual(self.state()['until_epoch'], drive_deadline, places=5)
        (self.sync / 'STOP_DRIVE_INGEST').touch()
        first.communicate(timeout=6)
        self.assertEqual(first.returncode, 130)

    def test_successful_audio_schedules_caption_backfill_after_its_deadline(self):
        deadline = time.time() + 5
        self.write_caption_summary(deadline)
        original = self.launcher.read_text(encoding='utf-8')
        self.launcher.write_text(original[:original.index('exit (')] +
            "$calls=@(Get-Content -LiteralPath (Join-Path $PrivateRoot 'child-calls.txt')).Count\n"
            "if ($calls -gt 1) {\n"
            "  [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() | Set-Content -LiteralPath (Join-Path $PrivateRoot 'backfill-started-ms.txt')\n"
            "  $path=Join-Path $PrivateRoot 'sync/drive_caption_backfill_state.json'\n"
            "  $state=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json\n"
            "  $state.pending_verified_audio_videos=0; $state.pending_source_videos=0; $state.retry_not_before_epoch=0\n"
            "  $state | ConvertTo-Json | Set-Content -LiteralPath $path -Encoding UTF8\n"
            "}\nexit 0\n", encoding='utf-8')
        first = self.waiting_process(state_name='waiting_for_caption_cooldown')
        self.assertEqual(len(self.calls()), 1, 'Audio must run before the caption wait')
        self.assertTrue(self.state()['await_caption_backfill'])
        first.communicate(timeout=12)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(len(self.calls()), 2)
        started = int((self.root / 'backfill-started-ms.txt').read_text(encoding='utf-8-sig'))
        self.assertGreaterEqual(started, deadline * 1000)
        self.assertEqual(self.state()['state'], 'stages_complete')

    def test_caption_backfill_wait_survives_restart_and_stop_without_audio_relaunch(self):
        deadline = time.time() + 1000
        self.write_caption_summary(deadline)
        self.write_state({'schema_version':2,'state':'waiting_for_caption_cooldown','attempts':1,
                          'until_epoch':deadline,'exit_code':0,'await_caption_backfill':True,
                          'cooldown_provider':'captions'})
        first = self.waiting_process(state_name='waiting_for_caption_cooldown')
        self.assertEqual(self.calls(), [])
        self.assertTrue(self.state()['await_caption_backfill'])
        self.assertAlmostEqual(self.state()['caption_until_epoch'], deadline, places=5)
        (self.sync / 'STOP_DRIVE_INGEST').touch()
        first.communicate(timeout=6)
        self.assertEqual(first.returncode, 130)
        self.assertEqual(self.calls(), [])

    def test_caption_deadline_expiring_during_audio_gets_only_one_immediate_revisit(self):
        self.write_caption_summary(time.time()+1000)
        original = self.launcher.read_text(encoding='utf-8')
        self.launcher.write_text(original[:original.index('exit (')] +
            "$calls=@(Get-Content -LiteralPath (Join-Path $PrivateRoot 'child-calls.txt')).Count\n"
            "if ($calls -eq 1) {\n"
            "  $path=Join-Path $PrivateRoot 'sync/drive_caption_backfill_state.json'\n"
            "  $state=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json\n"
            "  $state.retry_not_before_epoch=([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()/1000.0)+0.2\n"
            "  $state | ConvertTo-Json | Set-Content -LiteralPath $path -Encoding UTF8\n"
            "  Start-Sleep -Milliseconds 1000\n"
            "}\nexit 0\n", encoding='utf-8')
        result = self.run_supervisor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 2, 'Known elapsed cooldown gets one revisit, not a third pass')
        self.assertEqual(self.state()['attempts'], 2)
        self.assertEqual(self.state()['state'], 'caption_backfill_pending')

    def test_caption_backfill_is_bounded_and_unknown_delays_do_not_spin(self):
        self.write_caption_summary(time.time()+1000)
        result = self.run_supervisor('-MaxAttempts','1')
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(self.state()['state'], 'caption_backfill_retry_budget_exhausted')
        self.assertEqual(len(self.calls()), 1)
        again = self.run_supervisor('-MaxAttempts','1')
        self.assertEqual(again.returncode, 3, again.stderr)
        self.assertEqual(len(self.calls()), 1)
        for error_class, deadline in [('rate_limited',0),('network',time.time()+1000)]:
            with self.subTest(error_class=error_class):
                (self.sync / 'drive_ingest_resume_state.json').unlink()
                (self.root / 'child-calls.txt').unlink()
                self.write_caption_summary(deadline, error_class=error_class)
                result = self.run_supervisor()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.state()['state'], 'caption_backfill_pending')
                self.assertEqual(len(self.calls()), 1)

    def test_non_hard_block_deadlines_do_not_make_exit3_retryable(self):
        for error_class, delay in (('login_required', 1000), ('live', 1000),
                                   ('network', 1000), ('deferred_storage', 1000), ('forbidden', -30)):
            with self.subTest(error_class=error_class):
                (self.sync / 'drive_ingest_resume_state.json').unlink(missing_ok=True)
                (self.root / 'child-calls.txt').unlink(missing_ok=True)
                (self.root / 'child-exit.txt').write_text('3', encoding='utf-8')
                (self.sync / 'drive_ingest_manifest.jsonl').write_text(json.dumps({
                    'video_id': 'invented-id', 'error_class': error_class,
                    'retry_not_before_epoch': time.time() + delay}) + '\n', encoding='utf-8')
                result = self.run_supervisor()
                self.assertEqual(result.returncode, 3, result.stderr)
                self.assertEqual(len(self.calls()), 1)
                self.assertEqual(self.state()['state'], 'stopped_after_nonquota_result')

    def test_source_retry_also_consumes_the_persisted_attempt_budget(self):
        original = self.launcher.read_text(encoding='utf-8')
        self.launcher.write_text(original[:original.index('exit (')] +
            "$future=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()+30\n"
            "@{video_id='invented-id';error_class='forbidden';retry_not_before_epoch=$future} | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $PrivateRoot 'sync/drive_ingest_manifest.jsonl') -Encoding UTF8\nexit 3\n", encoding='utf-8')
        result = self.run_supervisor('-MaxAttempts', '1')
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(self.state()['state'], 'retry_budget_exhausted')
        self.assertEqual(self.state()['cooldown_provider'], 'youtube')
        self.assertGreaterEqual(self.state()['until_epoch'], time.time() + 580)
        again = self.run_supervisor('-MaxAttempts', '1')
        self.assertEqual(again.returncode, 3, again.stderr)
        self.assertEqual(len(self.calls()), 1)

    def test_latest_source_record_and_later_drive_deadline_are_respected(self):
        now = time.time()
        rows = [
            {'video_id': 'old', 'error_class': 'forbidden', 'retry_not_before_epoch': now + 10000},
            {'video_id': 'old', 'status': 'deleted'},
            {'video_id': 'current', 'error_class': 'rate_limited', 'retry_not_before_epoch': now + 30},
        ]
        (self.sync / 'drive_ingest_manifest.jsonl').write_text(
            ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        (self.sync / 'drive_ingest_cooldown.json').write_text(
            json.dumps({'until_epoch': now + 60}), encoding='utf-8')
        first = self.waiting_process(state_name='waiting_for_youtube_cooldown')
        self.assertEqual(self.state()['cooldown_provider'], 'both')
        self.assertAlmostEqual(self.state()['source_until_epoch'], now + 30, places=5)
        self.assertAlmostEqual(self.state()['until_epoch'], now + 60, places=5)
        (self.sync / 'STOP_DRIVE_INGEST').touch()
        first.communicate(timeout=6)
        self.assertEqual(first.returncode, 130)
        self.assertEqual(self.calls(), [])

    def test_budget_and_four_upload_transfers_are_forwarded_and_bounded(self):
        self.launcher.write_text(
            "param([string]$PrivateRoot,[double]$MaxLocalGb,[int]$UploadTransfers,[Parameter(ValueFromRemainingArguments=$true)]$Rest)\n"
            "@{cap=$MaxLocalGb;uploads=$UploadTransfers} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $PrivateRoot 'settings.json')\nexit 0\n", encoding='utf-8')
        result = self.run_supervisor('-MaxLocalGb', '16', '-UploadTransfers', '4')
        self.assertEqual(result.returncode, 0, result.stderr)
        settings = json.loads((self.root / 'settings.json').read_text(encoding='utf-8-sig'))
        self.assertEqual(settings, {'cap': 16, 'uploads': 4})
        self.assertEqual(self.state()['private_root_ceiling_bytes'], 16_000_000_000)
        rejected = self.run_supervisor('-MaxLocalGb', '18')
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(self.state()['private_root_ceiling_bytes'], 16_000_000_000)

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
