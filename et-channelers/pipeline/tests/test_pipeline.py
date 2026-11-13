#!/usr/bin/env python3
"""Tests for the ET-channelers batch pipeline. Standard library only; no network, no GPU, no real YouTube.

    python3 -I et-channelers/pipeline/tests/test_pipeline.py -v

A stand-in yt-dlp and ffmpeg (small Python scripts written to a temp folder) replace the real tools, so
these tests cover scheduling, resume, retries, the circuit breaker and the safety rails. They do not
test YouTube itself or the Whisper model; run the pilot in pipeline/README.md for that.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIPE = HERE.parent
ET = PIPE.parent
sys.path.insert(0, str(PIPE))

import common  # noqa: E402
import inventory  # noqa: E402
import select_jobs  # noqa: E402

GUARD = ET / "scripts" / "guard_no_raw_media.py"

# --------------------------------------------------------------------------- stand-in tools
FAKE_YTDLP = r'''
import hashlib, json, os, re, shutil, sys, time
from pathlib import Path

args = sys.argv[1:]
log = os.environ.get("FAKE_LOG")
state = Path(os.environ.get("FAKE_STATE", "."))


def note(*parts):
    if log:
        with open(log, "a") as fh:
            fh.write(" ".join(str(p) for p in parts) + "\n")


def fail(vid, message):
    note("END", vid, "%.4f" % time.time(), "fail")
    sys.stderr.write(message + "\n")
    sys.exit(1)


if "--version" in args:
    print("2099.01.01-fake")
    sys.exit(0)

url = args[-1]
if "--flat-playlist" in args:
    handle = re.search(r"/@([^/]+)/", url).group(1)
    note("CALL", "list", handle, "%.4f" % time.time())
    if handle.startswith("blocked"):
        sys.stderr.write("ERROR: [youtube:tab] Sign in to confirm you’re not a bot\n")
        sys.exit(1)
    if handle.startswith("gone"):
        sys.stderr.write("ERROR: [youtube:tab] This account has been terminated\n")
        sys.exit(1)
    m = re.search(r"(\d+)$", handle)
    count = int(m.group(1)) if m else 5
    entries = [{"id": "v" + hashlib.sha1(("%s:%d" % (handle, i)).encode()).hexdigest()[:10],
                "title": "%s video %d" % (handle, i), "duration": 60 + 60 * i, "view_count": 100 + i}
               for i in range(count)]
    print(json.dumps({"id": handle, "entries": entries}))
    sys.exit(0)

work = Path(args[args.index("-o") + 1]).parent
vid = re.search(r"v=([A-Za-z0-9_-]{11})", url).group(1)
note("START", vid, "%.4f" % time.time())
note("PROXYENV", vid, ",".join(sorted(k for k in os.environ if k.lower().endswith("_proxy"))) or "none")
note("ARGS", vid, " ".join(args))
time.sleep(float(os.environ.get("FAKE_SLEEP", "0.3")))
counter = state / (vid + ".count")
n = int(counter.read_text()) + 1 if counter.exists() else 1
counter.write_text(str(n))
if vid.startswith("BOT"):
    fail(vid, "ERROR: [youtube] %s: Sign in to confirm you’re not a bot" % vid)
if vid.startswith("RATE"):
    fail(vid, "ERROR: unable to download video data: HTTP Error 429: Too Many Requests")
if vid.startswith("FORB"):
    fail(vid, "ERROR: unable to download video data: HTTP Error 403: Forbidden")
if vid.startswith("SESS"):
    fail(vid, "ERROR: [youtube] %s: Video unavailable. This content isn't available, try again later. The current "
              "session has been rate-limited by YouTube for up to an hour. It is recommended to use `-t sleep`" % vid)
if vid.startswith("NOFM"):
    fail(vid, "ERROR: [youtube] %s: Requested format is not available. Use --list-formats for a list of available formats" % vid)
if vid.startswith("GONE"):
    fail(vid, "ERROR: [youtube] %s: Video unavailable. This video has been removed by the uploader" % vid)
if vid.startswith("LOGI"):
    fail(vid, "ERROR: [youtube] %s: Sign in to confirm your age. This video may be inappropriate" % vid)
if vid.startswith("NETW") and n == 1:
    fail(vid, "ERROR: Unable to download webpage: Connection reset by peer")
if vid.startswith("NETX"):
    fail(vid, "ERROR: Unable to download webpage: Connection reset by peer")
if vid.startswith("NOFI"):
    note("END", vid, "%.4f" % time.time(), "ok")
    sys.exit(0)
work.mkdir(parents=True, exist_ok=True)
if os.environ.get("FAKE_SRC"):
    shutil.copy(os.environ["FAKE_SRC"], str(work / (vid + ".wav")))
else:
    body = b"BADAUDIO" if vid.startswith("BADA") else b"RAW:" + vid.encode() * 40
    (work / (vid + ".webm")).write_bytes(body)
note("END", vid, "%.4f" % time.time(), "ok")
'''

FAKE_FFMPEG = r'''
import os, sys
from pathlib import Path

args = sys.argv[1:]
if "-version" in args:
    print("ffmpeg version fake-1.0")
    sys.exit(0)
if os.environ.get("FAKE_LOG"):
    with open(os.environ["FAKE_LOG"], "a") as fh:
        fh.write("FFARGS " + " ".join(args) + "\n")
src, dst = Path(args[args.index("-i") + 1]), Path(args[-1])
data = src.read_bytes()
if data.startswith(b"BADAUDIO"):
    sys.stderr.write("Invalid data found when processing input\n")
    sys.exit(1)
dst.write_bytes(b"FAKEOPUS" + data)
'''


def make_tool(bin_dir: Path, name: str, source: str) -> str:
    """Write a stand-in command-line tool and return the path to run it."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        script = bin_dir / f"{name}.py"
        script.write_text(source, encoding="utf-8")
        wrapper = bin_dir / f"{name}.cmd"
        wrapper.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n')
        return str(wrapper)
    wrapper = bin_dir / name
    wrapper.write_text(f"#!{sys.executable}\n{source}", encoding="utf-8")
    wrapper.chmod(0o755)
    return str(wrapper)


def mk(prefix: str, n: int) -> str:
    """An 11-character video id that starts with `prefix` (the stand-in tools key their behaviour on it)."""
    tail = str(n)
    return (prefix + "0" * 11)[:11 - len(tail)] + tail


def read_jsonl(path):
    return common.read_jsonl(path)


class PipelineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="etpipe-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "private"
        self.log = self.tmp / "fake.log"
        self.state = self.tmp / "state"
        self.state.mkdir()
        self.ytdlp = make_tool(self.tmp / "bin", "yt-dlp", FAKE_YTDLP)
        self.ffmpeg = make_tool(self.tmp / "bin", "ffmpeg", FAKE_FFMPEG)
        self.env = {"FAKE_LOG": str(self.log), "FAKE_STATE": str(self.state), "FAKE_SLEEP": "0.3"}

    # -- running things
    def cli(self, script, *args, env=None):
        return subprocess.run([sys.executable, "-I", str(PIPE / script), *map(str, args)], capture_output=True,
                              text=True, timeout=240, env={**os.environ, **self.env, **(env or {})})

    def download(self, *extra, env=None):
        return self.cli("download_audio.py", "--root", self.root, "--ytdlp", self.ytdlp, "--ffmpeg", self.ffmpeg,
                        "--ffprobe", "ffprobe-not-installed", "--min-interval", "0", "--backoff", "0.01", *extra,
                        env=env)

    def transcribe(self, *extra):
        return self.cli("transcribe.py", "--root", self.root, "--engine", "stub", *extra)

    # -- fixtures
    def write_queue(self, rows):
        """rows: (video_id, channel_dir, duration_s)"""
        common.write_csv(self.root / "jobs" / "queue.csv",
                         [{"video_id": v, "url": f"https://www.youtube.com/watch?v={v}", "channel_dir": c,
                           "duration_s": d, "sources": "test", "shard": 0} for v, c, d in rows], select_jobs.FIELDS)

    def make_audio(self, ids, chan="chanA", size=2000):
        for i, vid in enumerate(ids):
            path = self.root / "audio" / chan / f"{vid}.opus"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"FAKEOPUS" + bytes([65 + i % 20]) * (size + 300 * i))

    # -- reading results
    def audio_manifest(self):
        return read_jsonl(self.root / "audio" / "audio_manifest.jsonl")

    def tr_manifest(self):
        return read_jsonl(self.root / "transcripts" / "transcripts_manifest.jsonl")

    def fake_events(self, kind):
        out = []
        if self.log.exists():
            for line in self.log.read_text().splitlines():
                parts = line.split()
                if parts and parts[0] == kind:
                    out.append(parts)
        return out

    def peak_concurrency(self, chan_of=None):
        """Highest number of fake downloads running at once (overall, or per channel if chan_of maps id -> channel)."""
        events = []
        for kind, vid, t, *_ in (e for e in self.fake_events("START") + self.fake_events("END")):
            events.append((float(t), 0 if kind == "END" else 1, vid))
        events.sort()
        now, peak = Counter(), Counter()
        for _, is_start, vid in events:
            key = chan_of[vid] if chan_of else "all"
            now[key] += 1 if is_start else -1
            peak[key] = max(peak[key], now[key])
        return peak


# --------------------------------------------------------------------------- common.py
class TestCommon(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="etcommon-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_parse_duration(self):
        for text, want in [("1:02:03", 3723), ("15:38", 938), ("45", 45), ("", None), (None, None), ("abc", None),
                           ("1:2:3:4", None), ("-1:00", None)]:
            self.assertEqual(common.parse_duration(text), want, text)

    def test_shards_partition_and_are_stable_across_processes(self):
        ids = [mk("VID", i) for i in range(200)]
        shards = [[v for v in ids if common.stable_shard(v, 4) == k] for k in range(4)]
        self.assertEqual(sorted(sum(shards, [])), sorted(ids))
        self.assertTrue(all(25 <= len(s) <= 75 for s in shards), [len(s) for s in shards])
        code = f"import sys; sys.path.insert(0, {str(PIPE)!r}); from common import stable_shard; print(stable_shard('abc', 7))"
        seen = {subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                               env={**os.environ, "PYTHONHASHSEED": seed}).stdout for seed in ("1", "2", "3")}
        self.assertEqual(len(seen), 1, "stable_shard must not depend on Python's randomised hash()")

    def test_parse_shard(self):
        self.assertEqual(common.parse_shard(None), (0, 1))
        self.assertEqual(common.parse_shard("2/8"), (2, 8))
        for bad in ("8/8", "x", "-1/4", "1/0"):
            with self.assertRaises(SystemExit, msg=bad):
                common.parse_shard(bad)

    def test_lpt_assign_is_a_balanced_partition(self):
        items = [9, 8, 7, 6, 5, 4, 3, 2, 1]
        bins = common.lpt_assign(items, 3, weight=lambda x: x)
        self.assertEqual(sorted(sum(bins, [])), sorted(items))
        loads = [sum(b) for b in bins]
        self.assertLessEqual(max(loads) - min(loads), 2, loads)

    def test_classify_error(self):
        table = {
            "ERROR: [youtube] abc: Sign in to confirm you’re not a bot": "bot_check",
            "HTTP Error 429: Too Many Requests": "rate_limited",
            "unable to download: HTTP Error 403: Forbidden": "forbidden",
            "Sign in to confirm your age": "login_required",
            "Join this channel to get access to members-only content": "login_required",
            "Video unavailable": "unavailable",
            "Video unavailable. This content isn't available, try again later. The current session has been "
            "rate-limited by YouTube for up to an hour": "rate_limited",
            "Requested format is not available. Use --list-formats for a list of available formats": "no_formats",
            "This video is not available in your country": "unavailable",
            "Private video. Sign in if you've been granted access": "unavailable",
            "Connection reset by peer": "network",
            "something strange": "other",
            "": "other",
        }
        for text, want in table.items():
            self.assertEqual(common.classify_error(text), want, text)
        self.assertEqual(common.HARD_BLOCKS, {"bot_check", "rate_limited", "forbidden"})

    def test_read_jsonl_skips_a_torn_last_line_only(self):
        path = self.tmp / "a.jsonl"
        path.write_text('{"a":1}\n{"a":2}\n{"a":')
        self.assertEqual(common.read_jsonl(path), [{"a": 1}, {"a": 2}])
        path.write_text('{"a":1}\n{bad\n{"a":2}\n')
        with self.assertRaises(json.JSONDecodeError):
            common.read_jsonl(path)
        self.assertEqual(common.read_jsonl(self.tmp / "missing.jsonl"), [])

    def test_latest_record_wins(self):
        recs = [{"video_id": "a", "n": 1}, {"video_id": "b", "n": 1}, {"video_id": "a", "n": 2}]
        self.assertEqual(common.latest_by_key(recs)["a"]["n"], 2)

    def test_atomic_write_and_csv_roundtrip(self):
        common.atomic_write_text(self.tmp / "x" / "y.txt", "hello\n")
        self.assertEqual((self.tmp / "x" / "y.txt").read_text(), "hello\n")
        self.assertEqual([p.name for p in (self.tmp / "x").iterdir()], ["y.txt"])
        common.write_csv(self.tmp / "t.csv", [{"a": 1, "b": "x,y"}], ["a", "b"])
        self.assertEqual(common.read_csv(self.tmp / "t.csv"), [{"a": "1", "b": "x,y"}])

    def test_refuses_a_folder_inside_a_git_checkout(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        (repo / "data").mkdir()
        with self.assertRaises(SystemExit) as cm:
            common.ensure_outside_git(repo / "data")
        self.assertIn("inside a Git checkout", str(cm.exception))
        self.assertEqual(common.ensure_outside_git(self.tmp / "elsewhere"), (self.tmp / "elsewhere").resolve())

    def test_breaker_needs_consecutive_blocks(self):
        b = common.Breaker(3)
        b.hard_block(), b.hard_block(), b.success(), b.hard_block(), b.hard_block()
        self.assertFalse(b.tripped.is_set())
        b.hard_block()
        self.assertTrue(b.tripped.is_set())

    def test_rate_limiter_spaces_calls(self):
        now, slept = [0.0], []

        def sleep(seconds):
            slept.append(seconds)
            now[0] += seconds

        limiter = common.RateLimiter(2.0, jitter=0, clock=lambda: now[0], sleep=sleep)
        for _ in range(3):
            limiter.wait()
        self.assertEqual(slept, [2.0, 2.0])

    def test_private_root_default_honours_environment(self):
        old = os.environ.get("ET_PRIVATE_DIR")
        os.environ["ET_PRIVATE_DIR"] = str(self.tmp / "elsewhere")
        try:
            self.assertEqual(common.default_root(), self.tmp / "elsewhere")
        finally:
            if old is None:
                del os.environ["ET_PRIVATE_DIR"]
            else:
                os.environ["ET_PRIVATE_DIR"] = old


# --------------------------------------------------------------------------- inventory.py
class TestInventory(unittest.TestCase):
    """The expected numbers are those of the committed index (observed 2026-10-23); update them if it is re-crawled."""

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.est = inventory.build()

    def test_totals(self):
        self.assertEqual((len(self.rows), self.est["entries_with_total"], self.est["entries_without_total"]), (92, 48, 44))
        self.assertEqual(self.est["total_videos_known"], 40652)
        self.assertEqual(self.est["channels_over_1000_videos"], 14)

    def test_rows_are_ranked_and_complete(self):
        known = [r for r in self.rows if r["total_videos"] != ""]
        self.assertEqual([r["rank"] for r in known], list(range(1, 49)))
        self.assertEqual([r["total_videos"] for r in known], sorted((r["total_videos"] for r in known), reverse=True))
        self.assertTrue(all(r["rank"] == "" for r in self.rows[48:]))
        self.assertEqual(len({r["person_id"] for r in self.rows}), 92)

    def test_hours_add_up(self):
        self.assertEqual(self.est["hours"]["central"], sum(r["est_hours"] for r in self.rows if r["est_hours"] != ""))
        self.assertLess(self.est["hours"]["low"], self.est["hours"]["central"])
        self.assertLess(self.est["hours"]["central"], self.est["hours"]["high"] * 1.05)

    def test_block_is_wrapped_and_names_the_total(self):
        block = inventory.render_block(self.rows, self.est)
        self.assertTrue(block.startswith(inventory.START) and block.endswith(inventory.END))
        self.assertIn("40,652 videos", block)
        self.assertEqual(block.count("\n| 1 |"), 2)  # the top-15 table and the full table both start at rank 1


# --------------------------------------------------------------------------- select_jobs.py
class TestSelectJobs(PipelineCase):
    def select(self, *args):
        p = self.cli("select_jobs.py", "--root", self.root, *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def queue(self):
        return common.read_csv(self.root / "jobs" / "queue.csv")

    def test_bashar75_is_75_unique_valid_ids(self):
        self.select("--set", "bashar75")
        rows = self.queue()
        self.assertEqual(len(rows), 75)
        self.assertEqual(len({r["video_id"] for r in rows}), 75)
        self.assertTrue(all(common.ID_RE.match(r["video_id"]) for r in rows))
        meta = json.loads((self.root / "jobs" / "queue.meta.json").read_text())
        self.assertEqual((meta["videos"], meta["set"]), (75, "bashar75"))
        self.assertIn("all_ids.txt", meta["inputs_sha256"])

    def test_sampling_is_reproducible_and_capped(self):
        self.select("--set", "indexed", "--per-channel", "3", "--seed", "7")
        first = (self.root / "jobs" / "queue.csv").read_text()
        self.select("--set", "indexed", "--per-channel", "3", "--seed", "7")
        self.assertEqual(first, (self.root / "jobs" / "queue.csv").read_text())
        self.assertTrue(all(c <= 3 for c in Counter(r["channel_dir"] for r in self.queue()).values()))
        self.select("--set", "indexed", "--per-channel", "3", "--seed", "8")
        self.assertNotEqual(first, (self.root / "jobs" / "queue.csv").read_text())

    def test_shards_cover_every_row_once(self):
        self.select("--set", "indexed", "--shards", "4")
        rows = self.queue()
        self.assertEqual({int(r["shard"]) for r in rows}, {0, 1, 2, 3})
        self.assertTrue(all(int(r["shard"]) == common.stable_shard(r["video_id"], 4) for r in rows))

    def test_duration_filters_keep_unknown_lengths(self):
        self.select("--set", "indexed")
        everything = self.queue()
        self.select("--set", "indexed", "--min-seconds", "300", "--max-seconds", "3600")
        for r in self.queue():
            self.assertTrue(r["duration_s"] == "" or 300 <= int(r["duration_s"]) <= 3600)
        self.assertLess(len(self.queue()), len(everything))

    def test_discover_output_is_merged(self):
        common.append_jsonl(self.root / "discover" / "videos_all.jsonl",
                            {"video_id": mk("DSC", 1), "title": "t", "duration_s": 600, "person_id": "zed"})
        self.select("--set", "all")
        row = next(r for r in self.queue() if r["video_id"] == mk("DSC", 1))
        self.assertEqual((row["channel_dir"], row["sources"], row["duration_s"]), ("zed", "discover", "600"))
        self.select("--set", "bashar75")
        self.assertNotIn(mk("DSC", 1), {r["video_id"] for r in self.queue()})

    def test_export_ids_for_the_caption_tool(self):
        out = self.tmp / "ids.json"
        self.select("--set", "bashar75", "--limit", "5", "--export-ids", out)
        self.assertEqual(len(json.loads(out.read_text())["records"]), 5)

    def test_orders(self):
        self.select("--set", "indexed", "--order", "longest-first", "--limit", "20")
        known = [int(r["duration_s"]) for r in self.queue() if r["duration_s"]]
        self.assertEqual(known, sorted(known, reverse=True))


# --------------------------------------------------------------------------- discover.py
class TestDiscover(PipelineCase):
    def write_index(self, spec):
        """spec: (person, handle, expected_total). The stand-in yt-dlp lists as many videos as the digits ending the handle."""
        channels = [{"person": p, "person_name": p.title(), "status": "ok", "video_count": total,
                     "channel": {"url": f"https://www.youtube.com/@{h}", "handle": f"@{h}", "title": h}, "videos": []}
                    for p, h, total in spec]
        self.index = self.tmp / "index.json"
        self.index.write_text(json.dumps({"channels": channels}))

    def discover(self, *extra):
        # No extra channels unless a test names a file: the committed list holds real channels.
        return self.cli("discover.py", "--root", self.root, "--index", self.index, "--ytdlp", self.ytdlp,
                        "--min-interval", "0", "--extra-channels", self.tmp / "no-extra-channels.csv", *extra)

    def test_lists_every_channel_and_records_coverage(self):
        self.write_index([("alpha", "alpha4", 4), ("beta", "beta6", 8)])
        p = self.discover("--workers", "2")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(read_jsonl(self.root / "discover" / "videos_all.jsonl")), 10)
        self.assertEqual(len(read_jsonl(self.root / "discover" / "channels" / "alpha.jsonl")), 4)
        manifest = common.latest_by_key(read_jsonl(self.root / "discover" / "discover_manifest.jsonl"), "person_id")
        self.assertEqual((manifest["alpha"]["coverage"], manifest["beta"]["coverage"]), (1.0, 0.75))

    def test_rerun_skips_finished_channels(self):
        self.write_index([("alpha", "alpha4", 4), ("beta", "beta6", 6)])
        self.discover()
        calls = len(self.fake_events("CALL"))
        p = self.discover()
        self.assertEqual(p.returncode, 0)
        self.assertIn("0 to do", p.stderr)
        self.assertEqual(len(self.fake_events("CALL")), calls)

    def test_stops_after_three_bot_checks(self):
        self.write_index([("b1", "blocked1", 1), ("b2", "blocked2", 1), ("b3", "blocked3", 1), ("okay", "okay5", 5)])
        p = self.discover("--workers", "1")
        self.assertEqual(p.returncode, 3, p.stderr)
        self.assertEqual(len(self.fake_events("CALL")), 3, "no request may follow the third block")
        records = read_jsonl(self.root / "discover" / "discover_manifest.jsonl")
        self.assertEqual([r["error_class"] for r in records], ["bot_check"] * 3)
        self.assertFalse((self.root / "discover" / "channels" / "okay.jsonl").exists())

    def test_terminated_channel_is_recorded_once(self):
        self.write_index([("gone", "gone3", 3), ("alpha", "alpha4", 4)])
        self.assertEqual(self.discover().returncode, 0)
        self.discover()
        self.assertEqual(sum(1 for e in self.fake_events("CALL") if e[2] == "gone3"), 1)
        self.discover("--retry-failed")
        self.assertEqual(sum(1 for e in self.fake_events("CALL") if e[2] == "gone3"), 2)

    def test_channels_outside_the_index_are_listed_too(self):
        self.write_index([("alice", "alice5", 5)])
        extra = self.tmp / "extra_channels.csv"
        common.write_csv(extra, [
            {"person_id": "stewart-pearce", "person_name": "Stewart Pearce", "channel_url": "https://www.youtube.com/@extra7",
             "channel_id": "UC0ycS7cUA44tvG9T8VErW_w", "handle": "@extra7"},
            {"person_id": "not-a-youtube-row", "person_name": "X", "channel_url": "https://example.org/@nope3"},
            {"person_id": "alice", "person_name": "already in the index", "channel_url": "https://www.youtube.com/@dupe9"}],
            ["person_id", "person_name", "channel_url", "channel_id", "handle"])
        p = self.discover("--extra-channels", extra)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = read_jsonl(self.root / "discover" / "channels" / "stewart-pearce.jsonl")
        self.assertEqual(len(rows), 7)                                    # the stand-in lists as many as the handle's number
        self.assertEqual({r["person_id"] for r in rows}, {"stewart-pearce"})
        self.assertEqual(len(read_jsonl(self.root / "discover" / "channels" / "alice.jsonl")), 5)
        self.assertFalse((self.root / "discover" / "channels" / "not-a-youtube-row.jsonl").exists())
        listed = {e[2] for e in self.fake_events("CALL")}
        self.assertEqual(listed, {"alice5", "extra7"})                    # a person the index has is not listed twice

    def test_uses_the_documented_playlist_flag(self):
        self.write_index([("alpha", "alpha4", 4)])
        import discover
        self.assertIn("--playlist-items", Path(discover.__file__).read_text())
        self.assertNotIn("--playlist-end", Path(discover.__file__).read_text())


# --------------------------------------------------------------------------- download_audio.py
class TestDownload(PipelineCase):
    def setUp(self):
        super().setUp()
        sys.modules.pop("download_audio", None)

    def ok_manifest(self):
        return {r["video_id"]: r for r in self.audio_manifest() if r["status"] == "ok"}

    def test_dry_run_changes_nothing(self):
        self.write_queue([(mk("VID", 1), "chanA", 600), (mk("VID", 2), "chanA", 900)])
        p = self.download()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("dry run", p.stderr)
        self.assertIn("to do 2", p.stderr)
        self.assertFalse((self.root / "audio").exists())
        self.assertFalse(self.log.exists())

    def test_pilot_limit(self):
        self.write_queue([(mk("VID", i), "chanA", 600) for i in range(5)])
        self.assertEqual(self.download("--limit", "2").returncode, 0)
        self.assertEqual(len(self.audio_manifest()), 2)
        self.assertEqual(len(list((self.root / "audio" / "chanA").glob("*.opus"))), 2)

    def test_parallel_with_worker_and_channel_caps(self):
        chan = {}
        rows = []
        for c in "ABC":
            for i in range(4):
                vid = mk("VID" + c, i)
                chan[vid] = f"chan{c}"
                rows.append((vid, f"chan{c}", 600))
        self.write_queue(rows)
        p = self.download("--all", "--workers", "4", "--per-channel", "2")
        self.assertEqual(p.returncode, 0, p.stderr)
        done = self.ok_manifest()
        self.assertEqual(len(done), 12)
        for vid, rec in done.items():
            f = self.root / "audio" / rec["path"]
            self.assertEqual((f.stat().st_size, common.sha256_file(f)), (rec["bytes"], rec["sha256"]))
        self.assertEqual(self.peak_concurrency()["all"], 4, "4 workers should all be busy")
        per_channel = self.peak_concurrency(chan)
        self.assertLessEqual(max(per_channel.values()), 2)
        self.assertEqual(max(per_channel.values()), 2)

    def test_one_slot_per_channel_serialises_that_channel(self):
        ids = [mk("VID", i) for i in range(4)]
        self.write_queue([(v, "chanA", 600) for v in ids])
        p = self.download("--all", "--workers", "4", "--per-channel", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.peak_concurrency()["all"], 1)

    def test_workers_are_not_stuck_behind_a_busy_channel(self):
        """Channel-sorted queue, 1 slot per channel: the pool must still run different channels side by side."""
        ids = [(mk("VIDA", i), "chanA") for i in range(3)] + [(mk("VIDB", i), "chanB") for i in range(3)]
        self.write_queue([(v, c, 600) for v, c in ids])
        started = time.time()
        p = self.download("--all", "--workers", "2", "--per-channel", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(self.peak_concurrency()["all"], 2)
        self.assertLess(time.time() - started, 6 * 0.3 + 4, "two channels in parallel should take about half of serial time")

    def test_start_rate_limit_spaces_launches(self):
        self.write_queue([(mk("VID", i), f"chan{i}", 600) for i in range(4)])
        self.assertEqual(self.download("--all", "--workers", "4", "--min-interval", "0.5").returncode, 0)
        starts = sorted(float(e[2]) for e in self.fake_events("START"))
        gaps = [b - a for a, b in zip(starts, starts[1:])]
        self.assertGreaterEqual(min(gaps), 0.4, gaps)

    def test_resume_skips_finished_and_repairs_missing_files(self):
        ids = [mk("VID", i) for i in range(3)]
        self.write_queue([(v, "chanA", 600) for v in ids])
        self.assertEqual(self.download("--all").returncode, 0)
        calls = len(self.fake_events("START"))
        p = self.download("--all")
        self.assertIn("to do 0", p.stderr)
        self.assertEqual(len(self.fake_events("START")), calls)
        (self.root / "audio" / "chanA" / f"{ids[1]}.opus").unlink()
        self.assertEqual(self.download("--all").returncode, 0)
        self.assertEqual(len(self.fake_events("START")), calls + 1)
        self.assertTrue((self.root / "audio" / "chanA" / f"{ids[1]}.opus").exists())

    def test_encoder_settings_and_provenance(self):
        self.write_queue([(mk("VID", 1), "chanA", 600)])
        self.assertEqual(self.download("--all", "--bitrate", "32k").returncode, 0)
        ff = self.fake_events("FFARGS")[0]
        joined = " ".join(ff)
        for want in ("-ac 1", "-ar 16000", "-c:a libopus", "-b:a 32k", "-f opus"):
            self.assertIn(want, joined)
        rec = self.audio_manifest()[0]
        self.assertEqual(rec["tool"], "yt-dlp 2099.01.01-fake")
        self.assertEqual(rec["encoder"], "ffmpeg version fake-1.0")
        self.assertEqual(rec["target"], "opus mono 16000 Hz 32k")
        self.assertEqual(rec["path"], "chanA/" + mk("VID", 1) + ".opus")

    def test_scratch_files_are_cleaned_up(self):
        self.write_queue([(mk("VID", 1), "chanA", 600), (mk("BADA", 1), "chanA", 600), (mk("NOFI", 1), "chanA", 600)])
        self.download("--all")
        leftovers = [p for p in (self.root / "audio").rglob("*") if p.is_file() and p.suffix != ".opus" and p.name != "audio_manifest.jsonl"]
        self.assertEqual(leftovers, [])
        self.assertFalse(list((self.root / "audio").rglob("*.part")))

    def test_network_error_is_retried_then_succeeds(self):
        self.write_queue([(mk("NETW", 1), "chanA", 600)])
        self.assertEqual(self.download("--all").returncode, 0)
        rec = self.audio_manifest()[0]
        self.assertEqual((rec["status"], rec["attempts"]), ("ok", 2))

    def test_network_error_gives_up_after_the_attempt_limit(self):
        self.write_queue([(mk("NETX", 1), "chanA", 600)])
        self.assertEqual(self.download("--all", "--attempts", "3").returncode, 0)
        rec = self.audio_manifest()[0]
        self.assertEqual((rec["status"], rec["error_class"], rec["attempts"]), ("error", "network", 3))
        self.assertEqual(len(self.fake_events("START")), 3)

    def test_removed_and_age_gated_videos_are_tried_once_and_skipped_later(self):
        ids = [mk("GONE", 1), mk("LOGI", 1)]
        self.write_queue([(v, "chanA", 600) for v in ids])
        self.assertEqual(self.download("--all").returncode, 0)
        self.assertEqual({r["video_id"]: r["error_class"] for r in self.audio_manifest()},
                         {ids[0]: "unavailable", ids[1]: "login_required"})
        self.assertEqual(len(self.fake_events("START")), 2, "one attempt each, no retries")
        self.assertIn("to do 0", self.download("--all").stderr)
        self.assertEqual(len(self.fake_events("START")), 2)
        self.download("--all", "--retry-failed")
        self.assertEqual(len(self.fake_events("START")), 4)

    def test_other_failures_are_recorded_with_a_class_and_do_not_stop_the_run(self):
        ids = [mk("BADA", 1), mk("NOFI", 1), mk("VID", 1)]
        self.write_queue([(v, "chanA", 600) for v in ids])
        p = self.download("--all", "--workers", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        got = {r["video_id"]: (r["status"], r.get("error_class")) for r in self.audio_manifest()}
        self.assertEqual(got, {ids[0]: ("error", "transcode"), ids[1]: ("error", "other"), ids[2]: ("ok", "")})

    def test_three_blocks_in_a_row_stop_the_run_without_retrying(self):
        blocked = [mk("BOT", i) for i in range(3)]
        fine = [mk("VID", i) for i in range(3)]
        self.write_queue([(v, "chanA", 600) for v in blocked + fine])
        p = self.download("--all", "--workers", "1", "--attempts", "5")
        self.assertEqual(p.returncode, 3, p.stderr)
        self.assertIn("STOPPED", p.stderr)
        starts = Counter(e[1] for e in self.fake_events("START"))
        self.assertEqual(starts, Counter(blocked), "each blocked video once, nothing after the third block")
        self.assertEqual([r["error_class"] for r in self.audio_manifest()], ["bot_check"] * 3)

    def test_other_hard_blocks_count_too(self):
        ids = [mk("RATE", 1), mk("FORB", 1), mk("BOT", 1), mk("VID", 1)]
        self.write_queue([(v, "chanA", 600) for v in ids])
        p = self.download("--all", "--workers", "1")
        self.assertEqual(p.returncode, 3, p.stderr)
        self.assertEqual([r["error_class"] for r in self.audio_manifest()], ["rate_limited", "forbidden", "bot_check"])

    def test_blocks_separated_by_successes_do_not_trip_the_breaker(self):
        ids = [mk("BOT", 1), mk("VID", 1), mk("BOT", 2), mk("VID", 2), mk("BOT", 3), mk("VID", 3)]
        self.write_queue([(v, "chanA", 600) for v in ids])
        p = self.download("--all", "--workers", "1")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(Counter(r["status"] for r in self.audio_manifest()), Counter(ok=3, error=3))

    def test_rerun_after_a_stop_continues_with_the_untouched_videos(self):
        blocked = [mk("BOT", i) for i in range(3)]
        fine = [mk("VID", i) for i in range(2)]
        self.write_queue([(v, "chanA", 600) for v in blocked + fine])
        self.assertEqual(self.download("--all", "--workers", "1").returncode, 3)
        (self.root / "jobs" / "queue.csv").unlink()
        self.write_queue([(v, "chanA", 600) for v in fine])  # the operator waits, drops the blocked ids
        self.assertEqual(self.download("--all", "--workers", "1").returncode, 0)
        self.assertEqual(set(self.ok_manifest()), set(fine))

    def test_shards_split_the_queue_without_overlap(self):
        ids = [mk("VID", i) for i in range(10)]
        self.write_queue([(v, f"chan{i % 3}", 600) for i, v in enumerate(ids)])
        self.assertEqual(self.download("--all", "--shard", "0/2").returncode, 0)
        first = set(self.ok_manifest())
        self.assertEqual(self.download("--all", "--shard", "1/2").returncode, 0)
        both = self.ok_manifest()
        self.assertEqual(set(both), set(ids))
        self.assertTrue(first and first < set(ids))
        self.assertEqual(len(self.audio_manifest()), 10, "no video downloaded twice")

    def test_refuses_to_write_inside_a_git_checkout(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        p = self.cli("download_audio.py", "--root", repo / "data", "--all", "--ytdlp", self.ytdlp)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("inside a Git checkout", p.stderr)
        self.assertFalse((repo / "data").exists())

    def test_a_rate_limited_session_stops_the_run_and_is_not_filed_as_removed(self):
        ids = [mk("SESS", i) for i in range(6)]
        self.write_queue([(v, "chanA", 60) for v in ids])
        done = self.download("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3, done.stderr)
        recs = self.audio_manifest()
        self.assertEqual(len(recs), 3)                                   # three refusals, then it stops
        self.assertEqual({r["error_class"] for r in recs}, {"rate_limited"})
        self.assertEqual(len(self.fake_events("START")), 3)             # never retried into the limit
        calls = len(self.fake_events("START"))
        self.download("--all", "--workers", "1")                         # and tried again on the next run
        self.assertGreater(len(self.fake_events("START")), calls)

    def test_no_usable_formats_is_a_setup_fault_not_a_missing_video(self):
        ids = [mk("NOFM", i) for i in range(4)]
        self.write_queue([(v, "chanA", 60) for v in ids])
        done = self.download("--all", "--workers", "1")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual({r["error_class"] for r in self.audio_manifest()}, {"no_formats"})
        calls = len(self.fake_events("START"))
        self.download("--all", "--workers", "1")                         # not skipped as if the video were gone
        self.assertEqual(len(self.fake_events("START")), 2 * calls)

    def test_a_run_of_setup_faults_stops_with_its_own_exit_code(self):
        ids = [mk("NOFM", i) for i in range(12)]
        self.write_queue([(v, "chanA", 60) for v in ids])
        done = self.download("--all", "--workers", "1", "--stop-after-failures", "5")
        self.assertEqual(done.returncode, 6, done.stderr)
        self.assertIn("point at the setup", done.stderr)
        self.assertEqual(len(self.audio_manifest()), 5)

    def test_setup_faults_separated_by_successes_do_not_stop_the_run(self):
        ids = [mk("NOFM", 1), mk("GOOD", 1), mk("NOFM", 2), mk("GOOD", 2), mk("NOFM", 3), mk("GOOD", 3)]
        self.write_queue([(v, "chanA", 60) for v in ids])
        done = self.download("--all", "--workers", "1", "--stop-after-failures", "2")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(len(self.audio_manifest()), 6)

    def test_removed_videos_do_not_count_as_setup_faults(self):
        ids = [mk("GONE", i) for i in range(6)]
        self.write_queue([(v, "chanA", 60) for v in ids])
        done = self.download("--all", "--workers", "1", "--stop-after-failures", "3")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(len(self.audio_manifest()), 6)

    def test_pace_follows_the_downloaders_own_advice_and_tools_connect_directly(self):
        import argparse
        import download_audio
        args = argparse.Namespace(ytdlp="yt-dlp", format="bestaudio", limit_rate="", ffmpeg="ffmpeg",
                                  sample_rate=16000, bitrate="24k")
        cmd = download_audio.ytdlp_cmd(args, {"url": "https://www.youtube.com/watch?v=" + mk("VID", 1)}, Path("w"))
        self.assertEqual(cmd[cmd.index("--sleep-requests") + 1], "0.75")
        help_text = " ".join(self.cli("download_audio.py", "--help").stdout.split())   # argparse wraps lines
        self.assertIn("(default 10:", help_text)
        self.write_queue([(mk("GOOD", 1), "chanA", 60)])
        done = self.download("--all", env={"HTTPS_PROXY": "http://127.0.0.1:9", "http_proxy": "http://127.0.0.1:9",
                                           "ALL_PROXY": "socks5://127.0.0.1:9"})
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual({e[2] for e in self.fake_events("PROXYENV")}, {"none"})   # the tool never saw a proxy
        self.assertEqual(common.direct_env({"HTTP_PROXY": "x", "Https_Proxy": "y", "PATH": "/bin"}), {"PATH": "/bin"})

    def test_command_lines_use_no_cookies_proxies_or_logins(self):
        import argparse
        import download_audio
        args = argparse.Namespace(ytdlp="yt-dlp", format="bestaudio", limit_rate="2M", ffmpeg="ffmpeg",
                                  sample_rate=16000, bitrate="24k")
        cmd = download_audio.ytdlp_cmd(args, {"url": "https://www.youtube.com/watch?v=" + mk("VID", 1)}, Path("w"))
        for flag in ("--cookies", "--cookies-from-browser", "--proxy", "--username", "--password", "--netrc",
                     "--video-password", "--geo-bypass", "--add-header", "--impersonate", "--extractor-args"):
            self.assertNotIn(flag, cmd)
        self.assertIn("--ignore-config", cmd)
        self.assertEqual(cmd[cmd.index("--limit-rate") + 1], "2M")
        self.assertNotIn("-x", cmd, "re-encoding is done by ffmpeg, not by yt-dlp -x (which copies Opus sources unchanged)")


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg and ffprobe on PATH")
class TestRealEncode(PipelineCase):
    def test_output_is_mono_opus_and_much_smaller_than_the_source(self):
        probe = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
        if "libopus" not in probe:
            self.skipTest("this ffmpeg has no libopus")
        src = self.tmp / "tone.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "sine=frequency=440:duration=3:sample_rate=44100", "-ac", "2", str(src)], check=True)
        self.write_queue([(mk("VID", 1), "chanA", 3)])
        p = self.cli("download_audio.py", "--root", self.root, "--ytdlp", self.ytdlp, "--ffmpeg", "ffmpeg",
                     "--ffprobe", "ffprobe", "--min-interval", "0", "--all", env={"FAKE_SRC": str(src)})
        self.assertEqual(p.returncode, 0, p.stderr)
        rec = self.audio_manifest()[0]
        self.assertEqual(rec["status"], "ok", rec)
        self.assertAlmostEqual(rec["duration_s"], 3.0, delta=0.3)
        out = self.root / "audio" / rec["path"]
        self.assertEqual(out.read_bytes()[:4], b"OggS")
        self.assertLess(out.stat().st_size, src.stat().st_size / 10)
        info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,channels",
                                          "-of", "json", str(out)], capture_output=True, text=True).stdout)
        self.assertEqual((info["streams"][0]["codec_name"], info["streams"][0]["channels"]), ("opus", 1))
        self.assertEqual(common.probe_duration(out), rec["duration_s"])


def _has_numpy():
    try:
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


@unittest.skipUnless(shutil.which("ffmpeg") and _has_numpy(), "needs ffmpeg and numpy")
class TestDecodeAudio(PipelineCase):
    def test_decodes_to_16k_mono_float32_without_pyav(self):
        import numpy as np
        import transcribe
        tone = self.tmp / "tone.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        "sine=frequency=440:duration=2:sample_rate=44100", "-ac", "2", str(tone)], check=True)
        samples = transcribe.decode_audio(tone)
        self.assertEqual(samples.dtype, np.float32)
        self.assertAlmostEqual(len(samples) / 16000, 2.0, delta=0.05)
        self.assertGreater(float(np.abs(samples).max()), 0.1)
        with self.assertRaises(RuntimeError):
            transcribe.decode_audio(self.tmp / "missing.wav")
        source = Path(transcribe.__file__).read_text()
        self.assertFalse("import av" in source, "decoding must not rely on PyAV")
        self.assertTrue("decode_audio(path, a.ffmpeg)" in source, "the engine must hand decoded samples to the model")


# --------------------------------------------------------------------------- transcribe.py (stub engine)
class TestTranscribe(PipelineCase):
    def test_single_process(self):
        ids = [mk("VID", i) for i in range(5)]
        self.make_audio(ids)
        p = self.transcribe("--limit", "3")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(self.tr_manifest()), 3)
        tdir = self.root / "transcripts" / "chanA"
        self.assertEqual(len(list(tdir.glob("*.json"))), 3)
        self.assertEqual(len(list(tdir.glob("*.txt"))), 3)
        rec = self.tr_manifest()[0]
        doc = json.loads((tdir / f"{rec['video_id']}.json").read_text())
        self.assertEqual(rec["status"], "ok")
        self.assertEqual((rec["n_segments"], len(doc["segments"])), (3, 3))
        self.assertEqual(rec["audio_sha256"], common.sha256_file(self.root / "audio" / "chanA" / f"{rec['video_id']}.opus"))
        self.assertEqual(rec["json_sha256"], common.sha256_file(tdir / f"{rec['video_id']}.json"))

    def test_processes_share_the_work_and_results_are_merged(self):
        ids = [mk("VID", i) for i in range(8)]
        self.make_audio(ids)
        p = self.transcribe("--workers", "3", "--stub-delay", "0.1")
        self.assertEqual(p.returncode, 0, p.stderr)
        tdir = self.root / "transcripts"
        self.assertEqual(sorted(r["video_id"] for r in self.tr_manifest()), sorted(ids))
        self.assertEqual(len(list(tdir.glob("chanA/*.json"))), 8)
        self.assertFalse(list(tdir.glob("transcripts_manifest.part-*.jsonl")), "part files must be merged away")
        self.assertEqual(len(list((tdir / ".jobs").glob("worker-*.json"))), 3)

    def test_rerun_does_nothing_and_a_missing_output_is_redone(self):
        ids = [mk("VID", i) for i in range(4)]
        self.make_audio(ids)
        self.assertEqual(self.transcribe().returncode, 0)
        before = self.root / "transcripts" / "transcripts_manifest.jsonl"
        text = before.read_text()
        self.assertIn("0 to transcribe", self.transcribe().stderr)
        self.assertEqual(before.read_text(), text)
        (self.root / "transcripts" / "chanA" / f"{ids[2]}.json").unlink()
        self.assertEqual(self.transcribe().returncode, 0)
        redone = [r["video_id"] for r in self.tr_manifest()][4:]
        self.assertEqual(redone, [ids[2]])

    def test_a_bad_file_is_recorded_and_the_batch_goes_on(self):
        ids = [mk("VID", i) for i in range(3)]
        self.make_audio(ids)
        (self.root / "audio" / "chanA" / f"{ids[1]}.opus").write_bytes(b"CORRUPT" + b"x" * 500)
        p = self.transcribe()
        self.assertEqual(p.returncode, 0, p.stderr)
        got = {r["video_id"]: r["status"] for r in self.tr_manifest()}
        self.assertEqual(got, {ids[0]: "ok", ids[1]: "error", ids[2]: "ok"})
        self.assertIn("0 to transcribe", self.transcribe().stderr)
        self.transcribe("--retry-failed")
        self.assertEqual(len(self.tr_manifest()), 4)

    def test_one_process_per_device_with_its_own_cuda_visible_devices(self):
        self.make_audio([mk("VID", i) for i in range(6)])
        p = self.transcribe("--devices", "0,1", "--stub-delay", "0.05")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual({r["cuda_visible_devices"] for r in self.tr_manifest()}, {"0", "1"})
        self.assertEqual(len(self.tr_manifest()), 6)

    def test_scratch_folders_are_ignored(self):
        self.make_audio([mk("VID", 1)])
        stray = self.root / "audio" / ".work" / mk("VID", 2) / f"{mk('VID', 2)}.webm"
        stray.parent.mkdir(parents=True)
        stray.write_bytes(b"RAW")
        self.assertEqual(self.transcribe().returncode, 0)
        self.assertEqual([r["video_id"] for r in self.tr_manifest()], [mk("VID", 1)])

    def test_more_processes_finish_sooner(self):
        self.make_audio([mk("VID", i) for i in range(6)])
        t0 = time.time()
        self.assertEqual(self.transcribe("--stub-delay", "0.4").returncode, 0)
        serial = time.time() - t0
        shutil.rmtree(self.root / "transcripts")
        t0 = time.time()
        self.assertEqual(self.transcribe("--workers", "3", "--stub-delay", "0.4").returncode, 0)
        parallel = time.time() - t0
        self.assertLess(parallel, serial * 0.8, (serial, parallel))

    def test_shards_do_not_overlap(self):
        ids = [mk("VID", i) for i in range(9)]
        self.make_audio(ids)
        seen = []
        for k in range(3):
            self.assertEqual(self.transcribe("--shard", f"{k}/3").returncode, 0)
            done = [r["video_id"] for r in self.tr_manifest()]
            seen.append(set(done) - set().union(*seen) if seen else set(done))
        self.assertEqual(sorted(r["video_id"] for r in self.tr_manifest()), sorted(ids), "each video exactly once")
        self.assertEqual(sorted(sum((list(s) for s in seen), [])), sorted(ids))
        for k, part in enumerate(seen):
            self.assertTrue(all(common.stable_shard(v, 3) == k for v in part), (k, part))
        self.assertGreaterEqual(sum(1 for s in seen if s), 2)

    def test_refuses_a_data_folder_inside_a_git_checkout(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        p = self.cli("transcribe.py", "--root", repo / "data", "--engine", "stub")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("inside a Git checkout", p.stderr)


# --------------------------------------------------------------------------- verify.py and export_public.py
class TestEndToEnd(PipelineCase):
    def setUp(self):
        super().setUp()
        self.env["FAKE_SLEEP"] = "0.05"
        self.ids = [mk("VID", i) for i in range(6)]
        self.write_queue([(v, "chanA" if i < 3 else "chanB", 600) for i, v in enumerate(self.ids)])
        self.assertEqual(self.download("--all").returncode, 0)
        self.assertEqual(self.transcribe("--workers", "2", "--stub-delay", "0.01").returncode, 0)

    def verify(self, *extra):
        return self.cli("verify.py", "--root", self.root, *extra)

    def test_clean_run_verifies(self):
        p = self.verify("--hash")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("audio ok: 6 | transcripts ok: 6 | problems: 0", p.stdout)

    def test_missing_audio_is_reported(self):
        (self.root / "audio" / "chanA" / f"{self.ids[0]}.opus").unlink()
        p = self.verify()
        self.assertEqual(p.returncode, 1)
        self.assertIn("audio file missing", p.stdout)

    def test_truncated_transcript_is_reported(self):
        path = self.root / "transcripts" / "chanB" / f"{self.ids[4]}.json"
        path.write_text(path.read_text()[:40])
        p = self.verify()
        self.assertEqual(p.returncode, 1)
        self.assertIn("does not parse", p.stdout)

    def test_silent_corruption_needs_the_hash_check(self):
        path = self.root / "audio" / "chanA" / f"{self.ids[1]}.opus"
        data = bytearray(path.read_bytes())
        data[20] ^= 0xFF  # same size, different bytes
        path.write_bytes(bytes(data))
        self.assertEqual(self.verify().returncode, 0)
        p = self.verify("--hash")
        self.assertEqual(p.returncode, 1)
        self.assertIn("audio hash differs", p.stdout)

    def test_audio_without_a_transcript_is_reported(self):
        manifest = self.root / "transcripts" / "transcripts_manifest.jsonl"
        lines = manifest.read_text().splitlines()
        manifest.write_text("\n".join(lines[:-1]) + "\n")
        p = self.verify()
        self.assertEqual(p.returncode, 1)
        self.assertIn("audio downloaded but not transcribed", p.stdout)

    def test_qa_sample_sheet(self):
        p = self.verify("--qa-sample", "2", "--windows", "2")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        rows = common.read_csv(self.root / "qa" / "qa_sample.csv")
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r["machine_text"] and r["human_text"] == "" for r in rows))
        self.assertEqual(self.verify("--qa-sample", "2", "--windows", "2").returncode, 0)
        self.assertEqual(common.read_csv(self.root / "qa" / "qa_sample.csv"), rows, "same seed, same sample")

    def test_public_export_has_numbers_and_hashes_only(self):
        p = self.cli("export_public.py", "--root", self.root)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = self.root / "public_export" / "media_manifest_public.csv"
        rows = common.read_csv(out)
        import export_public
        self.assertEqual(list(rows[0].keys()), export_public.FIELDS)
        self.assertEqual(sorted(r["video_id"] for r in rows), sorted(self.ids))
        blob = out.read_text()
        self.assertNotIn("stub segment", blob)
        self.assertNotIn(str(self.root), blob)
        for r in rows:
            self.assertRegex(r["audio_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(r["text_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual((r["audio_status"], r["transcript_status"]), ("ok", "ok"))
        self.assertFalse(any("text" in f.lower() and f != "text_sha256" for f in export_public.FIELDS))


# --------------------------------------------------------------------------- doctor.py
class TestDoctor(PipelineCase):
    def doctor(self, *args, path):
        return subprocess.run([sys.executable, "-I", str(PIPE / "doctor.py"), *map(str, args)], capture_output=True,
                              text=True, timeout=120, env={"PATH": str(path)})

    def test_missing_tools_are_reported_with_a_fix_and_exit_code_1(self):
        p = self.doctor("--root", self.root, path=self.tmp)  # a PATH with nothing on it
        self.assertEqual(p.returncode, 1, p.stdout)
        for line in ("MISSING", "ffmpeg", "yt-dlp", "winget install"):
            self.assertIn(line, p.stdout)

    def test_data_folder_inside_git_is_reported(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        p = self.doctor("--root", repo / "data", path=self.tmp)
        self.assertIn("data folder", p.stdout)
        self.assertIn("outside the repository", p.stdout)

    def test_stand_in_tools_pass_the_tool_checks(self):
        p = self.doctor(path=self.tmp / "bin")
        self.assertRegex(p.stdout, r"ok\s+yt-dlp\s+2099\.01\.01-fake")


# --------------------------------------------------------------------------- scripts/guard_no_raw_media.py
class TestGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="etguard-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def run_guard(self, *paths):
        return subprocess.run([sys.executable, "-I", str(GUARD), "--paths", *map(str, paths)], capture_output=True, text=True)

    def test_clean_tree_passes(self):
        (self.tmp / "notes.md").write_text("hello\n")
        (self.tmp / "data.csv").write_text("a,b\n1,2\n")
        p = self.run_guard(self.tmp)
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_media_and_captions_are_flagged(self):
        for name in ("a.opus", "b.mp3", "c.wav", "d.vtt", "e.srt", "f.part"):
            (self.tmp / name).write_bytes(b"x")
        p = self.run_guard(self.tmp)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stdout.count("audio-or-video-file"), 4)
        self.assertEqual(p.stdout.count("caption-file"), 2)

    def test_speech_to_text_json_is_flagged(self):
        (self.tmp / "t.json").write_text('{"segments":[{"avg_logprob":-0.1,"text":"hi"}]}')
        self.assertIn("speech-to-text-json", self.run_guard(self.tmp).stdout)

    def test_secrets_are_flagged_but_never_printed(self):
        token = "ghp" + "_" + "A1b2" * 9
        (self.tmp / "config.txt").write_text(f"token={token}\n")
        (self.tmp / "key.pem").write_text("-----BEGIN " + "RSA PRIVATE KEY-----\nabc\n")
        (self.tmp / "other.md").write_text("AKIA" + "ABCDEFGHIJKLMNOP\n")
        p = self.run_guard(self.tmp)
        self.assertEqual(p.returncode, 1)
        self.assertIn("github-token", p.stdout)
        self.assertIn("aws-access-key", p.stdout)
        self.assertNotIn(token, p.stdout + p.stderr)

    def test_scratch_folders_and_big_files_are_flagged(self):
        (self.tmp / ".work").mkdir()
        (self.tmp / ".work" / "x.txt").write_text("x")
        (self.tmp / "big.bin").write_bytes(b"\0" * 5_000_001)
        out = self.run_guard(self.tmp).stdout
        self.assertIn("scratch-or-private-folder", out)
        self.assertIn("file-over-5MB", out)

    def test_what_the_collection_lanes_write_is_flagged(self):
        pod, web, yt = "pod-0123456789abcdef", "web-fedcba9876543210", "kvU9mCJr-eo"
        files = {
            f"transcripts_publisher/sam-the-illusionist/{web}.txt": "four thousand words of a session\n",
            f"transcripts_publisher/sam-the-illusionist/{web}.source": "<html>the page as fetched</html>",
            f"transcripts/athina-krol/{pod}.txt": "machine transcript text\n",
            f"transcripts/athina-krol/{pod}.json": '{"segments": []}',
            f"captions/chanY/{yt}.txt": "caption text\n",
            f"elsewhere/{pod}.txt": "an item file anywhere is still an item file\n",
            "catalog/catalog.csv": "item_id,person_id,lane,relation,title,published\npod-1,a,pod,own,A private title,\n",
            "jobs/queue_enclosures.csv": "video_id,url,channel_dir,title\npod-1,https://x/1.mp3,a,T\n",
            "audio/audio_manifest.jsonl": '{"video_id":"pod-1","channel_dir":"a","source_url":"https://x/1.mp3"}\n',
            "sources/apple_candidates.jsonl": '{"kind":"result","person_id":"a","feed_url":"https://x/feed"}\n',
            "sync/audio-20261113T180000-0a1b2c3d.tar": "bundle bytes",
            "sync/manifests.tar": "bundle bytes",
        }
        for rel, text in files.items():
            f = self.tmp / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        p = self.run_guard(self.tmp)
        self.assertEqual(p.returncode, 1, p.stdout)
        flagged = {line.split(": ")[0].replace(str(self.tmp) + "/", "") for line in p.stdout.splitlines() if ": " in line}
        self.assertEqual(flagged, set(files), f"not flagged: {sorted(set(files) - flagged)}")
        for rule in ("collected-item-file", "saved-page-source", "private-catalogue", "download-queue",
                     "collection-manifest", "archive-bundle"):
            self.assertIn(rule, p.stdout)
        self.assertNotIn("A private title", p.stdout)                   # the rule is named, the content is not shown

    def test_public_lists_and_counts_are_not_flagged(self):
        files = {
            "plan/coverage.csv": "person_id,person_name,role,items_listed\nathina-krol,Athina,channeler,225\n",
            "sources/podcast_feeds.csv": "person_id,relation,feed_url\nathina-krol,own,https://feed.example/x.xml\n",
            "sources/publisher_pages.csv": "person_id,title,page_url\nl-l-research,Session 1,https://site.example/1\n",
            "transcripts/bashar75_manifest.csv": "video_id,status,error\nkvU9mCJr-eo,ok,\n",
            "transcripts/scripts/all_ids.txt": "kvU9mCJr-eo\n",
            "transcripts/findings/note.md": "a findings note\n",
            "plan/estimates.json": "{}",
        }
        for rel, text in files.items():
            f = self.tmp / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        p = self.run_guard(self.tmp)
        self.assertEqual(p.returncode, 0, p.stdout)

    def test_a_linked_subfolder_into_a_checkout_is_refused(self):
        repo = self.tmp / "repo"
        (repo / ".git").mkdir(parents=True)
        (repo / "audio").mkdir()
        root = self.tmp / "private"
        root.mkdir()
        (root / "audio").symlink_to(repo / "audio", target_is_directory=True)
        with self.assertRaises(SystemExit) as stop:
            common.ensure_outside_git(root)
        self.assertIn("inside a Git checkout", str(stop.exception))
        (root / "audio").unlink()
        (root / "audio").symlink_to(self.tmp / "elsewhere", target_is_directory=True)   # a link to a plain folder is fine
        (self.tmp / "elsewhere").mkdir()
        self.assertEqual(common.ensure_outside_git(root), root.resolve())

    def test_the_repository_itself_is_clean(self):
        p = subprocess.run([sys.executable, "-I", str(GUARD)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout)


if __name__ == "__main__":
    unittest.main()
