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


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg is needed to make audio")
class TestOggCut(unittest.TestCase):
    def test_checksum_parts_and_lengths(self):
        import struct
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.opus"
            make_opus(src, 90)
            data = src.read_bytes()
            for off, size, *_ in drive_stage.ogg_pages(data):          # Ogg's CRC, as ffmpeg wrote it
                page = bytearray(data[off:off + size])
                stored = struct.unpack_from("<I", page, 22)[0]
                struct.pack_into("<I", page, 22, 0)
                self.assertEqual(drive_stage.ogg_crc(page), stored)
            parts = drive_stage.cut_ogg_opus(src, Path(tmp), "s [x]", 100_000)
            self.assertGreater(len(parts), 2)
            again = drive_stage.cut_ogg_opus(src, Path(tmp), "t [x]", 100_000)
            self.assertEqual([sha256_file(p) for p in parts], [sha256_file(p) for p in again])
            total = 0.0
            for i, p in enumerate(parts, 1):
                self.assertLessEqual(p.stat().st_size, 100_000)
                self.assertTrue(p.name.endswith(f"(part {i} of {len(parts)}).opus"))
                decode = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(p), "-f", "null", "-"],
                                        capture_output=True, text=True, timeout=60)
                self.assertEqual(decode.stderr.strip(), "", p.name)
                pages = drive_stage.ogg_pages(p.read_bytes())
                self.assertTrue(pages[-1][2] & 0x04)                     # the last page ends the stream
                self.assertFalse(any(pg[2] & 0x04 for pg in pages[:-1]))
                total += probe_duration(p)
            self.assertAlmostEqual(total, probe_duration(src), delta=0.1 * len(parts))

    def test_not_ogg_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "x.opus"
            f.write_bytes(b"not an ogg file at all" * 100)
            with self.assertRaises(ValueError):
                drive_stage.cut_ogg_opus(f, Path(tmp), "x", 1000)


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

    def run_tool(self, *args, stdin=None):
        return subprocess.run([sys.executable, "-I", str(PIPE / "drive_stage.py"), *args, "--root", str(self.root),
                               "--out", str(self.out)], capture_output=True, text=True, timeout=300, input=stdin)

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

    def record_folders(self):
        folders = [json.loads(x) for x in (self.out / "folders.jsonl").read_text(encoding="utf-8").splitlines()]
        res = self.tmp / "folders_done.jsonl"
        res.write_text("".join(json.dumps({"path": f["path"], "id": f"F{i}"}) + "\n" for i, f in enumerate(folders)),
                       encoding="utf-8")
        self.assertEqual(self.run_tool("record", str(res)).returncode, 0)

    @staticmethod
    def round_id(printed):
        import re
        found = re.search(r"round ([0-9a-f]{8}):", printed.stderr)
        if not found:
            raise AssertionError(printed.stderr)
        return found.group(1)

    def file_rows(self):
        lines = (self.root / "sync" / "drive_manifest.jsonl").read_text(encoding="utf-8").splitlines()
        return [r for r in map(json.loads, lines) if r.get("kind") != "folder"]

    def test_rounds_number_the_uploads_and_done_records_them(self):
        plan, _ = self.plan()
        self.record_folders()
        self.assertEqual(self.run_tool("batches", "--n", "3").returncode, 0)
        first = self.run_tool("round", "--size", "2")
        self.assertEqual(first.returncode, 0, first.stderr)
        rows = [line.split("\t") for line in first.stdout.splitlines()]
        self.assertEqual([r[0] for r in rows], ["1", "2"])
        self.assertTrue(all(len(r) == 5 and r[3].startswith("sha256:") for r in rows))
        self.assertIn(f"{len(plan)} pending in all", first.stderr)
        done = self.run_tool("done", "--round", self.round_id(first), stdin="1 D1\n2 D2\n9 D9\n1 D3\n")
        self.assertEqual(done.returncode, 1)                          # a number outside the round, one given twice
        self.assertIn("not recorded: 9 D9", done.stderr)
        self.assertIn("not recorded: 1 D3", done.stderr)
        self.assertIn("recorded 2 file(s)", done.stderr)
        self.assertEqual(sorted(r["drive_id"] for r in self.file_rows()), ["D1", "D2"])
        nxt = self.run_tool("round", "--size", "50")
        self.assertEqual(len(nxt.stdout.splitlines()), len(plan) - 2)
        self.assertNotIn(rows[0][1], nxt.stdout)                      # what is on Drive is not offered again

    def test_done_refuses_numbers_from_another_round_and_ids_already_recorded(self):
        # what the review found: after a partial `done`, `round` numbered the rest afresh, the first list's
        # numbers were recorded against other files, and those files were never offered again
        plan, _ = self.plan()
        self.record_folders()
        self.run_tool("batches", "--n", "1")
        self.assertIn("run `round` first", self.run_tool("done", "--round", "x", stdin="1 D1\n").stderr)
        first = self.run_tool("round", "--size", "3")
        rid = self.round_id(first)
        self.assertEqual(self.round_id(self.run_tool("round", "--size", "3")), rid)     # nothing recorded: same round
        self.assertEqual(self.run_tool("done", "--round", rid, stdin="1 D1\n").returncode, 0)
        second = self.run_tool("round", "--size", "3")
        self.assertNotEqual(self.round_id(second), rid)                                   # the rest, numbered afresh
        stale = self.run_tool("done", "--round", rid, stdin="2 D2\n3 D3\n")             # the first list's numbers
        self.assertEqual(stale.returncode, 1)
        self.assertIn("nothing recorded", stale.stderr)
        self.assertIn("trash those uploads on Drive (D2 D3)", stale.stderr)             # and what to do with them
        self.assertEqual(self.run_tool("done", stdin="2 D2\n").returncode, 1)            # no round named at all
        twice = self.run_tool("done", "--round", self.round_id(second), stdin="1 D1\n")  # an id fed in again
        self.assertEqual(twice.returncode, 1)
        self.assertIn("already has that Drive id", twice.stderr)
        self.assertEqual([r["drive_id"] for r in self.file_rows()], ["D1"])
        self.assertIn(f'"left": {len(plan) - 1}', self.run_tool("status").stdout)

    def test_done_records_only_its_own_lines(self):
        # what the review found: `done` gave the ledger every earlier round's lines again, so a text volume
        # uploaded twice had its third version recorded at an old Drive id and was never uploaded again
        page = self.root / "transcripts_publisher" / "ann" / "web-00000000000000d4.txt"
        for n, edition in enumerate(("first", "second", "third"), 1):
            page.write_text(f"the {edition} edition of the page " + "word " * 20, encoding="utf-8")
            self.plan()
            if n == 1:
                self.record_folders()
            self.run_tool("batches", "--n", "1")
            listed = self.run_tool("round", "--size", "50")
            lines = [line.split("\t") for line in listed.stdout.splitlines()]
            volume = [x for x in lines if "texts from the source" in x[1]]
            self.assertEqual(len(volume), 1, listed.stdout)                 # the changed volume is offered again
            pick = volume[0][0] if n < 3 else next(x[0] for x in lines if x is not volume[0])
            done = self.run_tool("done", "--round", self.round_id(listed), stdin=f"{pick} D{n}\n")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("recorded 1 file(s)", done.stderr)
        key = next(p["key"] for p in map(json.loads, (self.out / "plan.jsonl").read_text(encoding="utf-8").splitlines())
                   if "texts from the source" in p["title"])
        self.assertEqual([r["drive_id"] for r in self.file_rows() if r["key"] == key], ["D1", "D2"])
        self.assertIn("texts from the source", self.run_tool("round", "--size", "50").stdout)   # the third is still due

    def test_done_refuses_an_upload_whose_file_changed_after_the_round(self):
        # a text volume rewritten between `round` and `done`: the upload holds the old bytes, so recording it
        # with the plan's new checksum would leave the new edition off Drive for good
        page = self.root / "transcripts_publisher" / "ann" / "web-00000000000000d4.txt"
        self.plan()
        self.record_folders()
        self.run_tool("batches", "--n", "1")
        listed = self.run_tool("round", "--size", "50")
        vol = next(x.split()[0] for x in listed.stdout.splitlines() if "texts from the source" in x)
        page.write_text("a new edition of the page " + "word " * 20, encoding="utf-8")
        self.plan()
        self.run_tool("batches", "--n", "1")
        done = self.run_tool("done", "--round", self.round_id(listed), stdin=vol + " D1")
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertIn("changed or left the plan", done.stderr)
        self.assertEqual(self.file_rows(), [])
        self.assertIn("texts from the source", self.run_tool("round", "--size", "50").stdout)   # the new edition is due

    def test_done_refuses_an_upload_whose_file_left_the_plan_after_the_round(self):
        # planned again with other kinds between `round` and `done`: the upload matched nothing and `done` said 0
        self.plan()
        self.record_folders()
        self.run_tool("batches", "--n", "1")
        listed = self.run_tool("round", "--size", "50")
        vol = next(x.split()[0] for x in listed.stdout.splitlines() if "texts from the source" in x)
        again = self.run_tool("plan", "--audio-from", str(self.pulled), "--max-mb", "0.12", "--kinds", "audio",
                              "--known-folder", "04 Audio=AUDIO", "--known-folder", "03 Transcripts=TEXT")
        self.assertEqual(again.returncode, 0, again.stderr)
        done = self.run_tool("done", "--round", self.round_id(listed), stdin=vol + " D1")
        self.assertEqual(done.returncode, 1, done.stderr)
        self.assertIn("changed or left the plan", done.stderr)
        self.assertEqual(self.file_rows(), [])



class TestDriveHold(unittest.TestCase):
    """drive_hold.py lists in every Drive hold note the audio on disk that is not yet fully on Drive."""

    def test_the_hold_lists_what_is_on_disk_and_not_fully_on_drive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "audio" / "zed"
            audio.mkdir(parents=True)
            manifest = []
            for vid in ("pod-full", "pod-half", "pod-none"):
                (audio / f"{vid}.opus").write_bytes(b"x")
                manifest.append({"video_id": vid, "status": "ok", "path": f"zed/{vid}.opus", "bytes": 1})
            manifest.append({"video_id": "pod-gone", "status": "ok", "path": "zed/pod-gone.opus", "bytes": 1})   # stored, deleted
            (root / "audio" / "audio_manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in manifest))
            (root / "sync" / "holds").mkdir(parents=True)
            ledger = [{"key": "audio:pod-full#1", "item_id": "pod-full", "part": 1, "parts": 2, "drive_id": "a"},
                      {"key": "audio:pod-full#2", "item_id": "pod-full", "part": 2, "parts": 2, "drive_id": "b"},
                      {"key": "audio:pod-half#1", "item_id": "pod-half", "part": 1, "parts": 2, "drive_id": "c"}]
            (root / "sync" / "drive_manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ledger))
            note = root / "sync" / "holds" / "drive-123.json"
            note.write_text(json.dumps({"who": "drive", "pid": 123, "video_ids": ["old"]}))
            p = subprocess.run([sys.executable, "-I", str(PIPE / "drive_hold.py"), "--root", str(root)],
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(p.returncode, 0, p.stderr)
            data = json.loads(note.read_text())
            self.assertEqual(data["video_ids"], ["pod-half", "pod-none"])    # one part missing counts as not on Drive
            self.assertEqual((data["who"], data["pid"]), ("drive", 123))       # the rest of the note is kept
            self.assertIn("held for Drive 2", p.stdout)

if __name__ == "__main__":
    unittest.main()
