"""Offline contracts for 20 -> 50 -> index-only, and the explicit final round."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_collection_stages as stages


def row(video_id, rank, tab="videos", duration=""):
    return dict(video_id=video_id, channel_dir="source", listing_rank=rank, tab=tab,
                duration_s=duration, title=video_id, sources="discover")


class StageIndexTests(unittest.TestCase):
    def test_exact_tier_order_and_all_remaining_tabs_without_duration_filter(self):
        first = row("ABCDEFGHIJK", "0")
        later = row("LMNOPQRSTUV", "20")
        full = [first, later, row("WXYZabcdefg", "0", "shorts", "2"),
                row("hijklmnopqr", "0", "streams", "72000"), row("stuvwxyzABC", "", "", "")]
        tier, remaining, total = stages.partition([first], [later, first], full, {}, {})
        self.assertEqual([r["video_id"] for r in tier], [later["video_id"], first["video_id"]])
        self.assertEqual([r["listing_rank"] for r in tier], ["20", "0"])
        self.assertEqual([r["tab"] for r in remaining], ["shorts", "streams", ""])
        self.assertEqual(total, 5)
        groups = stages.grouped_index(remaining)
        self.assertEqual({r["tab"]: r["items"] for r in groups}, {"shorts": 1, "streams": 1, "unknown": 1})

    def test_missing_twenty_member_and_nonvideos_tier_fail_closed(self):
        first, later = row("ABCDEFGHIJK", "0"), row("LMNOPQRSTUV", "20")
        with self.assertRaises(ValueError):
            stages.partition([first], [later], [first, later], {}, {})
        with self.assertRaises(ValueError):
            stages.partition([first], [dict(first, tab="shorts")], [first], {}, {})

    def test_tier_member_missing_old_full_catalog_is_indexed_once(self):
        first, later = row("ABCDEFGHIJK", "0"), row("LMNOPQRSTUV", "20")
        tier, remaining, total = stages.partition([first], [first, later], [first], {}, {})
        self.assertEqual((len(tier), remaining, total), (2, [], 2))


@unittest.skipUnless(shutil.which("powershell.exe"), "PowerShell wrapper contract requires Windows PowerShell")
class WrapperStageTests(unittest.TestCase):
    def test_explicit_full_run_obeys_tier_barriers_and_index_mode_only_builds_catalog(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            wrapper = Path(__file__).resolve().parents[1] / "start_drive_ingest.ps1"
            code = wrapper.read_text(encoding="utf-8").replace(
                "$EtPython = Join-Path $EtScripts 'python.exe'",
                "$EtPython = '" + sys.executable.replace("'", "''") + "'")
            (base / wrapper.name).write_text(code, encoding="utf-8")
            (base / "drive_ingest.py").write_text('''import csv,json,sys
from pathlib import Path
def select_queue(path,newest=20,entire_queue=False): return list(csv.DictReader(Path(path).open()))
def load_state(path): return json.loads(Path(path).read_text())
def receipt_complete(record,row,remote): return record.get('complete',False)
def terminal_unavailable(record): return record.get('status') == 'unavailable'
if __name__ == '__main__':
 args=sys.argv[1:]; root=Path(args[args.index('--root')+1])
 with (root/'calls.jsonl').open('a') as out: out.write(json.dumps(args)+'\\n')
''', encoding="utf-8")
            (base / "prepare_collection_stages.py").write_text('''import json,sys
from pathlib import Path
args=sys.argv[1:]; root=Path(args[args.index('--out-dir')+1]).parent
with (root/'calls.jsonl').open('a') as out: out.write(json.dumps(['INDEX'])+'\\n')
''', encoding="utf-8")
            private = base / "private"
            (private / "jobs").mkdir(parents=True)
            (private / "sync").mkdir()
            tools = base / "tools"
            (tools / "venv/Scripts").mkdir(parents=True)
            for tool in (tools / "venv/Scripts/yt-dlp.exe", tools / "rclone.exe"):
                tool.touch()
            for name, ids in (("queue_newest20_enriched.csv", ["ABCDEFGHIJK"]),
                              ("queue_newest50.csv", ["ABCDEFGHIJK", "LMNOPQRSTUV"]),
                              ("queue_newest50_enriched.csv", ["ABCDEFGHIJK", "LMNOPQRSTUV"]),
                              ("queue_youtube_all_merged.csv", ["ABCDEFGHIJK", "LMNOPQRSTUV", "WXYZabcdefg"]),
                              ("queue_final_round.csv", ["WXYZabcdefg"])):
                (private / "jobs" / name).write_text("video_id\n" + "\n".join(ids) + "\n")
            all_ids = {"ABCDEFGHIJK", "LMNOPQRSTUV", "WXYZabcdefg"}
            for mode, complete, expected_calls, expected_exit in (
                    ("Index", set(), ["index"], 0),
                    ("Run", set(), ["20"], 0),
                    ("RunAll", set(), ["index", "20"], 3),
                    ("RunAll", {"ABCDEFGHIJK"}, ["index", "20", "50"], 3),
                    ("RunAll", {"ABCDEFGHIJK", "LMNOPQRSTUV"}, ["index", "20", "50", "remaining"], 3),
                    ("RunAll", all_ids, ["index", "20", "50", "remaining"], 0),
                    ("RunFinal", all_ids, ["remaining"], 0)):
                (private / "sync/drive_ingest_manifest.jsonl").write_text(
                    json.dumps({vid: {"complete": True} for vid in complete}))
                log = private / "calls.jsonl"
                log.unlink(missing_ok=True)
                result = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                                         str(base / wrapper.name), "-Mode", mode, "-PrivateRoot", str(private),
                                         "-ToolRoot", str(tools)], capture_output=True, text=True)
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                self.assertEqual(result.returncode, expected_exit, result.stdout + result.stderr)
                stages = ["index" if call == ["INDEX"] else "remaining" if "--entire-queue" in call
                          else call[call.index("--newest") + 1] for call in calls]
                self.assertEqual(stages, expected_calls)


if __name__ == "__main__":
    unittest.main()
