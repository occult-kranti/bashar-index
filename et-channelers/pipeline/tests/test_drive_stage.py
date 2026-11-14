"""drive_stage.py: names, folders, audio parts, text volumes and the Drive ledger."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIPE = HERE.parent
sys.path.insert(0, str(PIPE))

import drive_stage  # noqa: E402
from common import probe_duration, sha256_file  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def make_opus(path: Path, seconds: int):
    """Noise at a constant 24 kbps, so the size of a cut is predictable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-f", "lavfi", "-i",
                    f"anoisesrc=d={seconds}:c=pink:r=16000:a=0.3", "-ac", "1", "-c:a", "libopus", "-b:a", "24k",
                    "-vbr", "off", str(path)], check=True, timeout=120)


class TestNames(unittest.TestCase):
    def test_clean_removes_reserved_characters_and_shortens(self):
        self.assertEqual(drive_stage.clean('a\\b:c*d?e"f<g>h|i'), "a b c d e f g h i")
        self.assertEqual(drive_stage.clean("L/L Research"), "L∕L Research")
        self.assertEqual(drive_stage.clean("Sounds True: Insights"), "Sounds True - Insights")
        self.assertEqual(drive_stage.clean("  two\n lines  "), "two lines")
        long = drive_stage.clean("x" * 300, 50)
        self.assertLessEqual(len(long), 51)
        self.assertTrue(long.endswith("…"))

    def test_groups_and_interview_names(self):
        feeds = {"host-show--1": "The Show", "own--2": "My Podcast"}
        self.assertEqual(drive_stage.group_of({"lane": "ia", "relation": "archive"}, feeds), "archive.org sessions")
        self.assertEqual(drive_stage.group_of({"lane": "web", "relation": "file"}, feeds), "Audio from own website")
        self.assertEqual(drive_stage.group_of({"lane": "pod", "relation": "own", "feed_key": "own--2"}, feeds),
                         "Podcast - My Podcast")
        self.assertEqual(drive_stage.group_of({"lane": "pod", "relation": "host", "feed_key": "host-show--1"}, feeds),
                         "Interviews on other shows")
        row = {"item_id": "pod-0123456789abcdef", "relation": "host", "feed_key": "host-show--1",
               "published": "2024-05-06T10:00:00Z", "title": "Talk: part 1/2", "interview_type": "live channeling"}
        self.assertEqual(drive_stage.audio_name(row, feeds),
                         "2024-05-06 The Show - Talk - part 1∕2 (live channeling) [pod-0123456789abcdef]")
        self.assertTrue(drive_stage.audio_name({"item_id": "ia-0123456789abcdef"}, {}).startswith("undated untitled"))


class TestVolumes(unittest.TestCase):
    def test_volumes_respect_the_size_and_keep_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            entries = [f"entry {i} " + "é" * 400 + "\n" for i in range(10)]
            vols = drive_stage.write_volumes(entries, Path(tmp), "P - texts", 2000)
            self.assertGreater(len(vols), 1)
            text = ""
            for i, v in enumerate(vols, 1):
                self.assertLessEqual(v.stat().st_size, 2000)
                self.assertTrue(v.name.endswith(f"vol {i} of {len(vols)}.txt"))
                text += v.read_text(encoding="utf-8")
            self.assertEqual(text, "".join(entries))


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg is needed to make and cut audio")
class TestPlan(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="etdrive-"))
        self.root, self.pulled, self.out = self.tmp / "private", self.tmp / "pulled", self.tmp / "stage"
        audio = self.root / "audio"
        audio.mkdir(parents=True)
        self.small, self.big = "pod-00000000000000a1", "ia-00000000000000b2"
        make_opus(audio / "ann" / f"{self.small}.opus", 10)
        make_opus(self.pulled / "audio" / "ann" / f"{self.big}.opus", 100)   # deleted here, pulled from the store
        with open(audio / "audio_manifest.jsonl", "w", encoding="utf-8") as fh:
            for item, base, lane in ((self.small, self.root, "pod"), (self.big, self.pulled, "ia"),
                                     ("ia-00000000000000c3", self.root, "ia")):
                f = base / "audio" / "ann" / f"{item}.opus"
                rec = {"video_id": item, "channel_dir": "ann", "lane": lane, "status": "ok",
                       "path": f"ann/{item}.opus", "published": "2001-02-03",
                       "feed_key": "ann--1" if lane == "pod" else ""}
                if f.exists():
                    rec.update(bytes=f.stat().st_size, sha256=sha256_file(f), duration_s=probe_duration(f))
                else:
                    rec.update(bytes=123, sha256="0" * 64, duration_s=5)
                fh.write(json.dumps(rec) + "\n")
        (self.root / "feeds").mkdir()
        (self.root / "feeds" / "feeds_manifest.jsonl").write_text(
            json.dumps({"feed_key": "ann--1", "title": "Ann's Podcast"}) + "\n", encoding="utf-8")
        (self.root / "catalog").mkdir()
        with open(self.root / "catalog" / "catalog.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["item_id", "person_id", "lane", "relation", "title", "published",
                                                "feed_key", "interview_type", "source_url"])
            w.writeheader()
            w.writerow({"item_id": self.small, "person_id": "ann", "lane": "pod", "relation": "own",
                        "title": "Short one", "published": "2001-02-03", "feed_key": "ann--1"})
            w.writerow({"item_id": self.big, "person_id": "ann", "lane": "ia", "relation": "archive",
                        "title": "Long session", "published": "1990-01-01"})
        pub = self.root / "transcripts_publisher" / "ann"
        pub.mkdir(parents=True)
        (pub / "web-00000000000000d4.txt").write_text("words from the page", encoding="utf-8")
        made = self.root / "transcripts" / "ann"
        made.mkdir(parents=True)
        (made / f"{self.small}.txt").write_text("words heard", encoding="utf-8")
        (self.root / "transcripts" / "transcripts_manifest.jsonl").write_text(
            json.dumps({"video_id": self.small, "channel_dir": "ann", "status": "ok", "model": "base.en",
                        "engine": "faster-whisper"}) + "\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_tool(self, *args):
        return subprocess.run([sys.executable, "-I", str(PIPE / "drive_stage.py"), *args, "--root", str(self.root),
                               "--out", str(self.out)], capture_output=True, text=True, timeout=300)

    def plan(self):
        done = self.run_tool("plan", "--audio-from", str(self.pulled), "--max-mb", "0.12",
                             "--known-folder", "04 Audio=AUDIO", "--known-folder", "03 Transcripts=TEXT")
        self.assertEqual(done.returncode, 0, done.stderr)
        return [json.loads(x) for x in (self.out / "plan.jsonl").read_text(encoding="utf-8").splitlines()], done.stderr

    def test_plan_cuts_big_files_into_playable_parts_the_same_way_each_time(self):
        plan, err = self.plan()
        self.assertIn("audio not found here 1", err)          # the third item has no file anywhere
        audio = [p for p in plan if p["key"].startswith("audio:")]
        small = [p for p in audio if p["key"] == f"audio:{self.small}"]
        parts = sorted((p for p in audio if p["key"].startswith(f"audio:{self.big}#")), key=lambda p: p["part"])
        self.assertEqual(len(small), 1)
        self.assertEqual(small[0]["folder"], ["04 Audio", "ann", "Podcast - Ann's Podcast"])
        self.assertEqual(small[0]["title"], f"2001-02-03 Short one [{self.small}].opus")
        self.assertEqual(Path(small[0]["path"]), self.root / "audio" / "ann" / f"{self.small}.opus")   # not copied
        self.assertGreater(len(parts), 1)
        self.assertEqual([p["part"] for p in parts], list(range(1, len(parts) + 1)))
        self.assertEqual(parts[0]["folder"], ["04 Audio", "ann", "archive.org sessions"])
        total = 0.0
        for p in parts:
            self.assertLessEqual(p["bytes"], 120_000)
            self.assertEqual(p["sha256"], sha256_file(p["path"]))
            self.assertIn(f"(part {p['part']} of {len(parts)}).opus", p["title"])
            total += probe_duration(p["path"])
        self.assertAlmostEqual(total, 100, delta=1.0)      # nothing lost, nothing doubled
        again, _ = self.plan()
        self.assertEqual({p["key"]: p["sha256"] for p in again}, {p["key"]: p["sha256"] for p in plan})

    def test_texts_from_the_source_and_made_here_are_never_in_one_file(self):
        plan, _ = self.plan()
        texts = {p["key"]: p for p in plan if p["key"].startswith("text:")}
        self.assertEqual(set(texts), {"text:ann:source:1of1", "text:ann:made:1of1"})
        source = Path(texts["text:ann:source:1of1"]["path"]).read_text(encoding="utf-8")
        made = Path(texts["text:ann:made:1of1"]["path"]).read_text(encoding="utf-8")
        self.assertIn("words from the page", source)
        self.assertNotIn("words heard", source)
        self.assertIn("words heard", made)
        self.assertIn("kind: speech-to-text made here (faster-whisper, base.en)", made)
        self.assertEqual(texts["text:ann:made:1of1"]["folder"], ["03 Transcripts", "ann"])

    def test_recorded_uploads_are_not_planned_again_and_folders_unlock_batches(self):
        plan, _ = self.plan()
        folders = [json.loads(x) for x in (self.out / "folders.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([f["path"] for f in folders][:2], [["03 Transcripts"], ["04 Audio"]])   # parents first
        self.assertEqual(self.run_tool("batches", "--n", "2").returncode, 0)
        waiting = self.run_tool("batches", "--n", "2").stderr
        self.assertIn("wait for their folder", waiting)
        res = self.tmp / "folders_done.jsonl"
        res.write_text("".join(json.dumps({"path": f["path"], "id": f"F{i}"}) + "\n" for i, f in enumerate(folders)),
                       encoding="utf-8")
        self.assertEqual(self.run_tool("record", str(res)).returncode, 0)
        made = self.run_tool("batches", "--n", "2")
        self.assertNotIn("wait for their folder", made.stderr)
        lines = [json.loads(x) for b in sorted((self.out / "batches").glob("*.jsonl"))
                 for x in b.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(lines), len(plan))
        self.assertTrue(all(x["ref"].startswith("sha256:") and x["parentId"].startswith(("F", "AUDIO", "TEXT"))
                            for x in lines))
        first = plan[0]
        res2 = self.tmp / "files_done.jsonl"
        res2.write_text(json.dumps({"key": first["key"], "id": "D1"}) + "\n", encoding="utf-8")
        self.assertEqual(self.run_tool("record", str(res2)).returncode, 0)
        again, _ = self.plan()
        self.assertNotIn(first["key"], {p["key"] for p in again})
        self.assertEqual(len(again), len(plan) - 1)


if __name__ == "__main__":
    unittest.main()
