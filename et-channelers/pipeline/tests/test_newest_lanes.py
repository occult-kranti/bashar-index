#!/usr/bin/env python3
"""Tests for the newest-N tier runs of the YouTube lanes: the videos' own upload dates, the rank order of the
queue, speech-to-text beside the downloads, the tool check and the estimate in the plan, runs over queue files
given with --queue, and that the YouTube gate and the request pacing stay as the owner set them. Invented data,
stand-in tools, no network.

    python3 -I -m unittest discover -s et-channelers/pipeline/tests -p test_newest_lanes.py -v
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import datetime as dt
import io
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_pipeline  # noqa: E402  (also puts the pipeline folder on sys.path)
from test_pipeline import PIPE, PipelineCase, make_tool, mk  # noqa: E402

import common  # noqa: E402
import download_audio  # noqa: E402
import fetch_captions  # noqa: E402
import run_all  # noqa: E402
import select_jobs  # noqa: E402

# --------------------------------------------------------------------------- a stand-in yt-dlp that writes the dates
# test_pipeline.FAKE_YTDLP ignores --print-to-file. This one writes what the option asks for, as yt-dlp does:
# at "video" (also with --skip-download, then it writes caption tracks and stops) or at "after_move" (at the end
# of a download that worked). The video id's first four letters choose the dates.
DATES_PRE = r'''
import os as _os, re as _re, sys as _sys, time as _time
from pathlib import Path as _Path

_args = _sys.argv[1:]
_DATES = {"DATE": ("20240105", "NA", "1704412800"),        # an ordinary upload
          "PREM": ("20240101", "20240107", "1704067200"),  # a premiere: public on the release date
          "TSON": ("NA", "NA", "1704499200"),              # only a timestamp: 2024-01-06 UTC
          "NADT": ("NA", "NA", "NA")}                      # yt-dlp knows no date
_STAGES = ("pre_process", "after_filter", "video", "before_dl", "post_process", "after_move", "after_video", "playlist")


def _note(*parts):
    if _os.environ.get("FAKE_LOG"):
        with open(_os.environ["FAKE_LOG"], "a") as fh:
            fh.write(" ".join(str(p) for p in parts) + "\n")


def _print_to_file(stage, vid):
    if "--print-to-file" not in _args:
        return
    i = _args.index("--print-to-file")
    spec, target = _args[i + 1], _args[i + 2]
    m = _re.match(r"^(\w+):(.*)$", spec, _re.S)
    when, template = (m.group(1), m.group(2)) if m and m.group(1) in _STAGES else ("video", spec)
    if when != stage:
        return
    _note("PRINT", vid, stage)
    if vid.startswith("NOPR"):
        return                                             # an older yt-dlp, say: no file at all
    if vid.startswith("GARB"):
        line = "\x00\xff not\ta date"
    else:
        up, rel, ts = _DATES.get(vid[:4], ("20230615", "NA", "1686787200"))
        line = template.replace("%(upload_date)s", up).replace("%(release_date)s", rel).replace("%(timestamp)s", ts)
    with open(target, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


if "--version" in _args and _os.environ.get("FAKE_VERSION"):
    print(_os.environ["FAKE_VERSION"])
    _sys.exit(0)
if "--skip-download" in _args:                             # the captions lane
    _vid = _re.search(r"v=([A-Za-z0-9_-]{11})", _args[-1]).group(1)
    _note("CAPS", _vid, "%.4f" % _time.time(), " ".join(_args))
    if _vid.startswith("BOTC"):
        _sys.stderr.write("ERROR: [youtube] %s: Sign in to confirm you're not a bot\n" % _vid)
        _sys.exit(1)
    _print_to_file("video", _vid)
    if not _vid.startswith("NOCA"):
        _work = _Path(_args[_args.index("-o") + 1]).parent
        _work.mkdir(parents=True, exist_ok=True)
        (_work / (_vid + ".en.vtt")).write_text("WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nwords of %s\n" % _vid)
    _sys.exit(0)
'''
DATES_POST = r'''
_print_to_file("after_move", vid)                          # reached only when the download worked
'''
FAKE_YTDLP_DATES = DATES_PRE + test_pipeline.FAKE_YTDLP + DATES_POST

STUB_LANE = r'''
import sys, time
log, seconds, code = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
with open(log, "a") as fh:
    fh.write("DL START %.4f\n" % time.time())
time.sleep(seconds)
with open(log, "a") as fh:
    fh.write("DL END %.4f\n" % time.time())
print("lane finished")
sys.exit(code)
'''
STUB_TRANSCRIBE = r'''
import sys, time
log, seconds, code, kind = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
with open(log, "a") as fh:
    fh.write("TR START %s %.4f\n" % (kind, time.time()))
time.sleep(seconds)
with open(log, "a") as fh:
    fh.write("TR END %s %.4f\n" % (kind, time.time()))
if kind == "beside":                    # the pass after the lanes writes to the terminal itself
    print("pass finished")
sys.exit(code)
'''


def argparse_defaults(script):
    """{option: default} of every add_argument call in a pipeline script, read from its source."""
    out = {}
    for node in ast.walk(ast.parse((PIPE / script).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "add_argument" and node.args \
                and isinstance(node.args[0], ast.Constant):
            for kw in node.keywords:
                if kw.arg == "default":
                    try:
                        out[node.args[0].value] = ast.literal_eval(kw.value)
                    except ValueError:
                        pass
    return out


class NewestCase(PipelineCase):
    def setUp(self):
        super().setUp()
        self.ytdlp = make_tool(self.tmp / "bin", "yt-dlp", FAKE_YTDLP_DATES)

    def captions(self, *extra, env=None):
        return self.cli("fetch_captions.py", "--root", self.root, "--ytdlp", self.ytdlp, "--min-interval", "0", *extra,
                        env=env)

    def caption_manifest(self):
        return common.read_jsonl(self.root / "captions" / "captions_manifest.jsonl")

    def runner(self, *extra, env=None):
        return self.cli("run_all.py", "--root", self.root, "--store", f"dir:{self.tmp / 'store'}", *extra, env=env)

    def listing(self, counts, duration=600):
        """Channel listings as discover.py writes them: {channel: number of videos}, newest first."""
        ids = {}
        for chan, n in counts.items():
            ids[chan] = [mk("NW" + chan[0].upper(), i) for i in range(n)]
            for i, vid in enumerate(ids[chan]):
                common.append_jsonl(self.root / "discover" / "videos_all.jsonl",
                                    {"video_id": vid, "title": f"{chan} {i}", "duration_s": duration, "person_id": chan,
                                     "tab": "videos", "upload_date_approx": ""})
        return ids

    def select(self, *args, index=None, bashar75=()):
        """select_jobs.py, run here with the committed lists (the index, the 75) swapped for invented ones, so the
        queue can only hold invented videos. index: {channel: [video ids]}; bashar75: video ids.
        Returns (the queue's video ids, its meta file)."""
        lists = self.tmp / "invented-lists"
        lists.mkdir(exist_ok=True)
        channels = [{"person": chan, "videos": [{"video_id": v, "title": v, "length_text": "10:00", "is_channeling": True}
                                                for v in vids]} for chan, vids in (index or {}).items()]
        (lists / "youtube_index.json").write_text(json.dumps({"channels": channels}), encoding="utf-8")
        (lists / "all_ids.txt").write_text("".join(v + "\n" for v in bashar75), encoding="utf-8")
        argv = ["select_jobs.py", "--root", str(self.root), *map(str, args)]
        with mock.patch.multiple(select_jobs, INDEX=lists / "youtube_index.json", BASHAR_IDS=lists / "all_ids.txt",
                                 BASHAR_CSV=lists / "no-such.csv"), \
                mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            select_jobs.main()
        jobs = self.root / "jobs"
        return [r["video_id"] for r in common.read_csv(jobs / "queue.csv")], \
            json.loads((jobs / "queue.meta.json").read_text(encoding="utf-8"))

    def invented_tree(self, channels):
        """A copy of the pipeline's programs beside an invented channel index and no other committed list, so a whole
        run_all.py --go can only ever see invented channels and videos. channels: (person, handle); the stand-in
        yt-dlp lists as many videos as the digits ending the handle. Returns the copy's pipeline folder."""
        pipe = self.tmp / "invented-et" / "pipeline"
        pipe.mkdir(parents=True)
        for src in PIPE.glob("*.py"):
            shutil.copy2(src, pipe / src.name)
        index = pipe.parent / "youtube-index" / "youtube_index.json"
        index.parent.mkdir()
        index.write_text(json.dumps({"channels": [
            {"person": p, "person_name": p.title(), "status": "ok", "video_count": 9,
             "channel": {"url": f"https://www.youtube.com/@{h}", "handle": f"@{h}", "title": h}, "videos": []}
            for p, h in channels]}), encoding="utf-8")
        return pipe


# --------------------------------------------------------------------------- 1. the videos' own dates
class TestReadPublished(unittest.TestCase):
    def setUp(self):
        import tempfile
        import shutil
        self.tmp = Path(tempfile.mkdtemp(prefix="etdates-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def read(self, content):
        path = self.tmp / "dates.tsv"
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return download_audio.read_published(path)

    def test_good_lines(self):
        self.assertEqual(self.read("20240105\tNA\t1704412800\n"), ("2024-01-05", "upload_date"))
        self.assertEqual(self.read("20240101\t20240107\t1704067200\n"), ("2024-01-07", "release_date"))  # premiere
        self.assertEqual(self.read("NA\tNA\t1704499200\n"), ("2024-01-06", "timestamp"))                # UTC day
        self.assertEqual(self.read("NA\tNA\t1704499200.0\n"), ("2024-01-06", "timestamp"))
        self.assertEqual(self.read("19991231\tNA\tNA\n20240105\tNA\tNA\n"), ("2024-01-05", "upload_date"))  # the last line
        self.assertEqual(self.read("20240105 NA NA\n"), ("2024-01-05", "upload_date"))       # spaces for tabs
        self.assertEqual(self.read("2024-01-05\tNA\tNA\n"), ("2024-01-05", "upload_date"))

    def test_na_is_empty(self):
        self.assertEqual(self.read("NA\tNA\tNA\n"), ("", ""))
        self.assertEqual(self.read("\t\t\n"), ("", ""))

    def test_a_missing_file_is_empty(self):
        self.assertEqual(download_audio.read_published(self.tmp / "nothing-here.tsv"), ("", ""))
        self.assertEqual(download_audio.read_published(self.tmp), ("", ""))                    # a folder, not a file
        self.assertEqual(self.read(""), ("", ""))

    def test_garbage_is_empty(self):
        for junk in (b"\x00\xff\xfe\x80 not\ta date", "hello world", "20241345\tNA\tNA", "20240230\tNA\tNA",
                     "19000101\tNA\tNA", "abc\tdef\tghi", "NA\tNA\t1e400", "NA\tNA\tnan", "NA\tNA\t-1e18",
                     "202401051\tNA\tNA", "2024010\tNA\tNA"):
            self.assertEqual(self.read(junk), ("", ""), junk)

    def test_both_lanes_read_dates_the_same_way(self):
        self.assertIs(fetch_captions.read_published, download_audio.read_published)
        self.assertEqual(fetch_captions.DATE_FILE, download_audio.DATE_FILE)


class TestDateOptions(unittest.TestCase):
    """The date comes from the call each lane makes anyway: one more option, no extra request, not --print."""

    def test_audio_writes_the_dates_once_the_file_is_in_place(self):
        args = argparse.Namespace(ytdlp="yt-dlp", format="bestaudio", limit_rate="", sleep_requests=0.75)
        cmd = download_audio.ytdlp_cmd(args, {"url": "https://www.youtube.com/watch?v=" + mk("VID", 1)}, Path("w"))
        i = cmd.index("--print-to-file")
        self.assertEqual(cmd[i + 1], "after_move:%(upload_date)s\t%(release_date)s\t%(timestamp)s")
        self.assertEqual(Path(cmd[i + 2]), Path("w") / download_audio.DATE_FILE)
        self.assertNotIn("--print", cmd)                         # --print would also make yt-dlp quiet
        self.assertNotIn("--simulate", cmd)
        self.assertTrue(cmd[-1].startswith("https://www.youtube.com/watch?v="))     # the address stays last

    def test_captions_write_the_dates_at_the_video_stage(self):
        args = argparse.Namespace(ytdlp="yt-dlp", languages="en")
        cmd = fetch_captions.ytdlp_cmd(args, {"url": "https://www.youtube.com/watch?v=" + mk("VID", 1)}, Path("w"))
        i = cmd.index("--print-to-file")
        self.assertEqual(cmd[i + 1], "video:%(upload_date)s\t%(release_date)s\t%(timestamp)s")
        self.assertIn("--skip-download", cmd)
        self.assertNotIn("--print", cmd)
        self.assertTrue(cmd[-1].startswith("https://www.youtube.com/watch?v="))

    def test_the_date_file_is_never_taken_for_media_or_a_track(self):
        self.assertFalse(download_audio.DATE_FILE.startswith(mk("VID", 1)))
        self.assertFalse(download_audio.DATE_FILE.endswith(".vtt"))


class TestDatesInTheManifests(NewestCase):
    def test_audio_records_the_published_date(self):
        ids = [mk(p, 1) for p in ("DATE", "PREM", "TSON", "NADT", "GARB", "NOPR")]
        self.write_queue([(v, "chanA", 600) for v in ids])
        done = self.download("--all")
        self.assertEqual(done.returncode, 0, done.stderr)
        recs = {r["video_id"]: r for r in self.audio_manifest()}
        self.assertEqual({r["status"] for r in recs.values()}, {"ok"})            # a date never fails an item
        self.assertEqual({v: recs[v]["published"] for v in ids},
                         {ids[0]: "2024-01-05", ids[1]: "2024-01-07", ids[2]: "2024-01-06", ids[3]: "", ids[4]: "",
                          ids[5]: ""})
        self.assertEqual(recs[ids[1]]["published_from"], "release_date")
        self.assertNotIn("published_from", recs[ids[3]])
        self.assertEqual({e[2] for e in self.fake_events("PRINT")}, {"after_move"})
        self.assertEqual(list((self.root / "audio").rglob(download_audio.DATE_FILE)), [])   # the work folders are gone

    def test_a_failed_download_records_no_date_and_is_not_retried_for_one(self):
        self.write_queue([(mk("GONE", 1), "chanA", 600)])
        self.download("--all")
        rec = self.audio_manifest()[0]
        self.assertEqual((rec["status"], rec["error_class"]), ("error", "unavailable"))
        self.assertNotIn("published", rec)
        self.assertEqual(self.fake_events("PRINT"), [])

    def test_captions_record_the_published_date(self):
        ids = [mk("DATE", 2), mk("PREM", 2), mk("NOCA", 2), mk("NADT", 2), mk("GARB", 2)]
        self.write_queue([(v, "chanB", 600) for v in ids])
        done = self.captions("--all", "--workers", "1")
        self.assertEqual(done.returncode, 0, done.stderr)
        recs = {r["video_id"]: r for r in self.caption_manifest()}
        self.assertEqual(recs[ids[0]]["status"], "ok")
        self.assertEqual({v: recs[v]["published"] for v in ids},
                         {ids[0]: "2024-01-05", ids[1]: "2024-01-07", ids[2]: "2023-06-15", ids[3]: "", ids[4]: ""})
        self.assertEqual(recs[ids[2]]["error_class"], "no_captions")             # dated even without a track
        self.assertEqual((self.root / "captions" / "chanB" / f"{ids[0]}.txt").read_text(), f"words of {ids[0]}\n")
        self.assertEqual({e[2] for e in self.fake_events("PRINT")}, {"video"})
        self.assertEqual(list((self.root / "captions").rglob(download_audio.DATE_FILE)), [])

    def test_the_lanes_work_with_a_yt_dlp_that_writes_no_date_file(self):
        self.ytdlp = make_tool(self.tmp / "bin", "yt-dlp", test_pipeline.FAKE_YTDLP)    # ignores the option
        self.write_queue([(mk("VID", 1), "chanA", 600)])
        done = self.download("--all")
        self.assertEqual(done.returncode, 0, done.stderr)
        rec = self.audio_manifest()[0]
        self.assertEqual((rec["status"], rec["published"]), ("ok", ""))
        self.assertIn("--print-to-file", next(" ".join(e) for e in self.fake_events("ARGS")))

    def test_the_published_date_reaches_the_catalogue_from_audio_and_from_captions(self):
        audio_only, captions_only = mk("DATE", 3), mk("PREM", 3)
        self.write_queue([(audio_only, "chanA", 600)])
        self.assertEqual(self.download("--all").returncode, 0)
        self.write_queue([(captions_only, "chanB", 600)])
        self.assertEqual(self.captions("--all").returncode, 0)
        done = self.cli("catalog.py", "--root", self.root)
        self.assertEqual(done.returncode, 0, done.stderr)
        rows = {r["item_id"]: r for r in common.read_csv(self.root / "catalog" / "catalog.csv")}
        self.assertEqual((rows[audio_only]["published"], rows[audio_only]["audio_status"]), ("2024-01-05", "ok"))
        self.assertEqual((rows[captions_only]["published"], rows[captions_only]["captions_status"]), ("2024-01-07", "ok"))
        self.assertEqual(rows[captions_only]["audio_status"], "")                 # captions alone dated it


# --------------------------------------------------------------------------- 2. rank order for the newest tiers
class TestRankOrder(NewestCase):
    def test_newest_interleaves_the_channels_by_rank(self):
        ids = self.listing({"alpha": 4, "beta": 2, "gamma": 3})
        a, b, g = ids["alpha"], ids["beta"], ids["gamma"]
        order, meta = self.select("--set", "all", "--newest", "3")
        self.assertEqual(order, [a[0], b[0], g[0], a[1], b[1], g[1], a[2], g[2]])
        self.assertEqual((meta["order"], meta["order_from"]), ("rank", "the default with --newest"))
        # stopped after three videos, the run has every channel's newest
        order, _ = self.select("--set", "all", "--newest", "3", "--limit", "3")
        self.assertEqual(order, [a[0], b[0], g[0]])

    def test_an_explicit_order_wins(self):
        ids = self.listing({"alpha": 4, "beta": 2, "gamma": 3})
        a, b, g = ids["alpha"], ids["beta"], ids["gamma"]
        order, meta = self.select("--set", "all", "--newest", "3", "--order", "as-is")
        self.assertEqual(order, [a[0], a[1], a[2], b[0], b[1], g[0], g[1], g[2]])  # channel by channel, as before
        self.assertEqual((meta["order"], meta["order_from"]), ("as-is", "--order"))
        order, meta = self.select("--set", "all", "--newest", "3", "--order", "shortest-first")
        self.assertEqual(meta["order"], "shortest-first")

    def test_rank_without_newest_puts_unranked_rows_last(self):
        ids = self.listing({"alpha": 2, "beta": 1})
        index = {"alpha": [mk("IXA", 1), ids["alpha"][1]], "delta": [mk("IXD", 1), mk("IXD", 0)]}   # one also listed
        bashar75 = [mk("BSF", 2), mk("BSF", 1)]
        order, meta = self.select("--set", "all", "--order", "rank", index=index, bashar75=bashar75)
        self.assertEqual(order, [ids["alpha"][0], ids["beta"][0], ids["alpha"][1],     # ranked, every channel's newest first
                                 mk("IXA", 1), mk("BSF", 1), mk("BSF", 2), mk("IXD", 0), mk("IXD", 1)])  # then the rest
        rows = common.read_csv(self.root / "jobs" / "queue.csv")
        self.assertEqual([r["listing_rank"] for r in rows], ["0", "0", "1", "", "", "", "", ""])
        self.assertEqual(rows[2]["sources"], "discover+index")                    # listed and indexed: keeps its rank
        self.assertEqual((meta["order"], meta["order_from"]), ("rank", "--order"))
        _, meta = self.select("--set", "all", index=index, bashar75=bashar75)
        self.assertEqual((meta["order"], meta["order_from"]), ("as-is", "the default"))   # unchanged without --newest

    def test_rank_order_by_itself(self):
        def row(vid, chan, rank):
            return {"video_id": vid, "channel_dir": chan, "listing_rank": rank}
        rows = [row("u1", "zed", None), row("b1", "beta", 1), row("a0", "alpha", 0), row("u2", "alpha", None),
                row("b0", "beta", 0), row("a1", "alpha", 1), row("a2", "alpha", 2)]
        self.assertEqual([r["video_id"] for r in select_jobs.rank_order(rows)],
                         ["a0", "b0", "a1", "b1", "a2", "u2", "u1"])              # unranked last, by channel

    def test_the_audio_lane_works_down_the_queue_in_rank_order(self):
        self.listing({"alpha": 3, "beta": 3})
        order, _ = self.select("--set", "all", "--newest", "3")
        done = self.download("--all", "--workers", "1")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual([e[1] for e in self.fake_events("START")], order)


# --------------------------------------------------------------------------- 3. speech-to-text beside the downloads
class TestTranscribeAlongside(PipelineCase):
    def setUp(self):
        super().setUp()
        self.lane = make_tool(self.tmp / "bin", "stub-lane", STUB_LANE)
        self.stt = make_tool(self.tmp / "bin", "stub-transcribe", STUB_TRANSCRIBE)
        self.events = self.tmp / "events.log"

    def lane_cmd(self, seconds, code):
        return [self.lane, str(self.events), str(seconds), str(code)]

    def stt_cmd(self, seconds, code, kind):
        return [self.stt, str(self.events), str(seconds), str(code), kind]

    def run_lanes(self, lanes, beside, final, every):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            worst = run_all.run_lanes(lanes, [("transcribe", final)] if final else [], beside, every)
        return worst, out.getvalue()

    def event_lines(self):
        return [line.split() for line in self.events.read_text().splitlines()]

    def passes(self, kind=None):
        """[(kind, start, end)] of the transcription passes, checking on the way that no two ever ran at once."""
        out, open_pass = [], None
        for line in self.event_lines():
            if line[0] != "TR":
                continue
            if line[1] == "START":
                self.assertIsNone(open_pass, f"a pass started while another was running: {self.event_lines()}")
                open_pass = (line[2], float(line[3]))
            else:
                self.assertEqual(open_pass[0], line[2])
                out.append((line[2], open_pass[1], float(line[3])))
                open_pass = None
        self.assertIsNone(open_pass)
        return [p for p in out if kind in (None, p[0])]

    def lane_times(self):
        starts = [float(l[2]) for l in self.event_lines() if l[:2] == ["DL", "START"]]
        ends = [float(l[2]) for l in self.event_lines() if l[:2] == ["DL", "END"]]
        return starts, ends

    def test_passes_run_during_the_downloads_one_at_a_time_and_once_more_at_the_end(self):
        worst, out = self.run_lanes([("youtube", self.lane_cmd(5, 3)), ("captions", self.lane_cmd(2, 0))],
                                    self.stt_cmd(0.6, 0, "beside"), self.stt_cmd(0.1, 0, "final"), every=0.2)
        self.assertEqual(worst, 3)                                                # the lanes' exit code, unchanged
        _, ends = self.lane_times()
        self.assertEqual(len(ends), 2)                                            # both lanes ran to their end
        beside, final = self.passes("beside"), self.passes("final")
        self.assertGreaterEqual(sum(1 for _, start, _ in beside if start < max(ends)), 2, self.event_lines())
        self.assertEqual(len(final), 1)
        self.assertGreater(final[0][1], max(ends))                                # after the downloads
        self.assertEqual(self.passes()[-1][0], "final")                           # and after every pass beside them
        self.assertIn("[transcribe] pass finished", out)                          # its lines are labelled

    def test_a_pass_starts_every_interval_counted_from_the_last_start(self):
        import time
        quick = run_all.TranscribeAlongside(self.stt_cmd(0.05, 0, "beside"), every=1.0)
        with contextlib.redirect_stdout(io.StringIO()):
            quick.start()
            time.sleep(3.5)
            quick.finish()
        self.assertGreaterEqual(len(quick.starts), 3, self.event_lines())
        self.assertGreaterEqual(min(b - a for a, b in zip(quick.starts, quick.starts[1:])), 0.99, quick.starts)
        self.assertEqual(quick.codes, [0] * len(quick.starts))
        slow = run_all.TranscribeAlongside(self.stt_cmd(1.2, 0, "beside"), every=0.2)    # longer than the interval
        with contextlib.redirect_stdout(io.StringIO()):
            slow.start()
            time.sleep(3.0)
            slow.finish()
        self.passes()                                                             # never two at once
        self.assertGreaterEqual(len(slow.starts), 2)

    def test_failing_passes_never_stop_the_downloads_or_change_their_exit_code(self):
        worst, out = self.run_lanes([("youtube", self.lane_cmd(6, 0))], self.stt_cmd(0.05, 2, "beside"),
                                    self.stt_cmd(0.05, 0, "final"), every=0.1)
        self.assertEqual(worst, 0)                                                # failures beside the lanes do not count
        self.assertEqual(len(self.lane_times()[1]), 1)                            # the download ran to its end
        self.assertEqual(len(self.passes("beside")), run_all.GIVE_UP_AFTER)        # then it stopped trying
        self.assertEqual(len(self.passes("final")), 1)                            # the last pass still ran
        self.assertIn("passes in a row failed", out)
        worst, _ = self.run_lanes([("youtube", self.lane_cmd(0.5, 4))], self.stt_cmd(0.05, 1, "beside"),
                                  self.stt_cmd(0.05, 0, "final"), every=0.1)
        self.assertEqual(worst, 4)

    def test_exit_codes_combine_as_before(self):
        self.assertEqual(self.run_lanes([("youtube", self.lane_cmd(0.1, 0))], None, self.stt_cmd(0.05, 1, "final"), 0)[0], 1)
        self.assertEqual(self.run_lanes([("youtube", self.lane_cmd(0.1, 3))], None, self.stt_cmd(0.05, 1, "final"), 0)[0], 3)
        self.assertEqual(self.run_lanes([("youtube", self.lane_cmd(0.1, 0)), ("captions", self.lane_cmd(0.1, 4))],
                                        self.stt_cmd(0.05, 0, "beside"), self.stt_cmd(0.05, 0, "final"), 0.1)[0], 4)

    def test_a_transcriber_that_cannot_start_leaves_the_downloads_alone(self):
        worst, out = self.run_lanes([("youtube", self.lane_cmd(1.5, 0))], [str(self.tmp / "no-such-transcriber")],
                                    None, every=0.1)
        self.assertEqual(worst, 0)
        self.assertEqual(len(self.lane_times()[1]), 1)
        self.assertIn("[transcribe] could not start", out)

    def test_every_zero_means_only_after_the_downloads(self):
        self.run_lanes([("youtube", self.lane_cmd(1, 0))], None, self.stt_cmd(0.05, 0, "final"), every=0)
        self.assertEqual([p[0] for p in self.passes()], ["final"])

    def test_the_plan_names_the_passes_beside_the_lanes(self):
        root = ["--root", self.root, "--store", f"dir:{self.tmp / 'store'}", "--lanes", "youtube", "--set", "bashar75"]
        plan = self.cli("run_all.py", *root, "--transcribe", "tiny.en").stdout
        self.assertIn("beside     transcribe: every 300 s while the lanes run, one pass at a time", plan)
        self.assertIn("--hold-untranscribed", plan)                               # the sync keeps the audio for it
        self.assertLess(plan.index("beside"), plan.index("then       transcribe"))
        self.assertNotIn("beside", self.cli("run_all.py", *root, "--transcribe", "tiny.en", "--transcribe-every", "0").stdout)
        self.assertNotIn("beside", self.cli("run_all.py", *root).stdout)


# --------------------------------------------------------------------------- 4. the tool check and the estimate
class TestPreflight(NewestCase):
    TODAY = dt.date(2026, 11, 16)

    def check(self, needed, **paths):
        args = argparse.Namespace(**{"ytdlp": self.ytdlp, "ffmpeg": self.ffmpeg, "ffprobe": self.ffmpeg, **paths})
        out = io.StringIO()
        missing = run_all.preflight(args, needed, today=self.TODAY, out=out)
        return missing, out.getvalue()

    def version_tool(self, name, version, code=0):
        return make_tool(self.tmp / "bin", name, f"import sys\nprint({version!r})\nsys.exit({code})\n")

    def test_release_age(self):
        self.assertEqual(run_all.release_age_days("2026.10.26", self.TODAY), 21)
        self.assertEqual(run_all.release_age_days("2026.10.26.232915", self.TODAY), 21)       # a nightly
        self.assertLess(run_all.release_age_days("2099.01.01-fake", self.TODAY), 0)
        self.assertIsNone(run_all.release_age_days("version unknown", self.TODAY))
        self.assertIsNone(run_all.release_age_days("2026.13.40", self.TODAY))

    def test_an_old_yt_dlp_is_a_warning_not_a_stop(self):
        old = self.version_tool("yt-dlp-old", "2026.09.01")
        missing, out = self.check({"yt-dlp": True, "ffmpeg": True}, ytdlp=old)
        self.assertEqual(missing, [])
        self.assertIn("2026.09.01", out)
        self.assertIn(f"WARNING: this yt-dlp was released {(self.TODAY - dt.date(2026, 9, 1)).days} days ago", out)
        self.assertIn("look like blocks", out)
        self.assertIn("ffmpeg version fake-1.0", out)
        on_the_line = self.version_tool("yt-dlp-60", (self.TODAY - dt.timedelta(days=60)).strftime("%Y.%m.%d"))
        self.assertNotIn("WARNING", self.check({"yt-dlp": True}, ytdlp=on_the_line)[1])
        recent = self.version_tool("yt-dlp-new", "2026.10.26")
        self.assertNotIn("WARNING", self.check({"yt-dlp": True}, ytdlp=recent)[1])
        odd = self.version_tool("yt-dlp-odd", "custom build")
        missing, out = self.check({"yt-dlp": True}, ytdlp=odd)
        self.assertEqual(missing, [])
        self.assertIn("no release date", out)

    def test_a_missing_tool_is_named_with_what_to_do(self):
        missing, out = self.check({"yt-dlp": True, "ffmpeg": True, "ffprobe": False},
                                  ytdlp=str(self.tmp / "no-yt-dlp"), ffprobe=str(self.tmp / "no-ffprobe"))
        self.assertEqual(missing, ["yt-dlp"])                                     # ffprobe only costs the lengths
        self.assertIn("yt-dlp   not found", out)
        self.assertIn("python -m pip install -U yt-dlp", out)
        self.assertIn("--ytdlp PATH", out)
        self.assertIn("ffprobe  not found", out)
        self.assertIn("lengths are recorded as unknown", out)
        broken = self.version_tool("yt-dlp-broken", "", code=1)
        missing, out = self.check({"yt-dlp": True}, ytdlp=broken)
        self.assertEqual(missing, ["yt-dlp"])
        self.assertIn("cannot be run", out)

    @unittest.skipIf(os.name == "nt", "the program the system will not start is made the Unix way here")
    def test_a_tool_the_system_will_not_start_is_named_not_a_traceback(self):
        # on the PATH and executable, but for another machine (or damaged, or blocked by a virus scanner on Windows):
        # starting it raises an OSError, which must end as the same "cannot be run" line and exit 6
        odd = self.tmp / "bin" / "yt-dlp-wrong-build"
        odd.write_bytes(b"\x7fELF\x02\x01\x01" + b"\x00" * 57)
        odd.chmod(0o755)
        missing, out = self.check({"yt-dlp": True, "ffmpeg": True}, ytdlp=str(odd))
        self.assertEqual(missing, ["yt-dlp"])
        self.assertIn(f"yt-dlp   cannot be run: {odd} ended with code 126:", out)
        self.assertIn("--ytdlp PATH", out)
        self.assertIn("ffmpeg version fake-1.0", out)                             # and the check goes on
        done = self.runner("--lanes", "youtube,captions", "--set", "bashar75", "--go", "--ytdlp", odd,
                           "--ffmpeg", self.ffmpeg)
        self.assertEqual(done.returncode, 6, done.stdout + done.stderr)
        self.assertIn("STOPPED: yt-dlp cannot be run", done.stderr)
        self.assertNotIn("Traceback", done.stderr)
        self.assertFalse((self.root / "jobs" / "queue.csv").exists())

    def test_the_tools_each_lane_needs(self):
        def need(lanes, transcribe=""):
            return run_all.needed_tools(argparse.Namespace(lanes=lanes, transcribe=transcribe))
        self.assertEqual(need(["youtube", "captions"]), {"yt-dlp": True, "ffmpeg": True, "ffprobe": False})
        self.assertEqual(need(["captions"]), {"yt-dlp": True})
        self.assertEqual(need(["texts"]), {})
        self.assertEqual(need(["captions"], "large-v3"), {"yt-dlp": True, "ffmpeg": True})

    def test_the_run_stops_before_anything_starts_when_yt_dlp_cannot_be_run(self):
        done = self.runner("--lanes", "youtube,captions", "--set", "bashar75", "--go", "--ytdlp", self.tmp / "no-yt-dlp",
                           "--ffmpeg", self.ffmpeg)
        self.assertEqual(done.returncode, 6, done.stdout + done.stderr)
        self.assertIn("STOPPED: yt-dlp cannot be run", done.stderr)
        self.assertIn("yt-dlp   not found", done.stdout)
        self.assertFalse((self.root / "jobs" / "queue.csv").exists())              # not even the queue was built
        self.assertFalse(self.log.exists())

    def test_the_plan_runs_no_tool(self):
        done = self.runner("--lanes", "youtube,captions", "--set", "bashar75", "--ytdlp", self.ytdlp)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("check      tools: yt-dlp, ffmpeg, ffprobe", done.stdout)
        self.assertNotIn("TOOLS", done.stdout)
        self.assertFalse(self.log.exists())
        self.assertFalse(self.root.exists())

    def test_a_whole_run_with_an_old_yt_dlp_warns_goes_on_and_dates_what_it_fetched(self):
        # The whole tier run, as the owner starts it, on a copy of the programs that sees only invented channels.
        pipe = self.invented_tree([("alpha", "alpha3"), ("beta", "beta3")])
        cmd = [sys.executable, "-I", str(pipe / "run_all.py"), "--root", str(self.root),
               "--store", f"dir:{self.tmp / 'store'}", "--lanes", "youtube", "--newest", "2", "--min-interval", "0",
               "--watch", "1", "--ytdlp", str(self.ytdlp), "--ffmpeg", str(self.ffmpeg), "--ffprobe", "ffprobe-not-installed"]
        # and no yt-dlp other than the stand-in can be found by name
        path = os.pathsep.join(d for d in os.environ.get("PATH", "").split(os.pathsep) if d and not shutil.which("yt-dlp", path=d))
        env = {**os.environ, **self.env, "PATH": path, "FAKE_VERSION": "2025.06.30", "FAKE_SLEEP": "0.05"}
        # first the plan: every step that runs yt-dlp must name the stand-in, or the test stops before anything runs
        plan = subprocess.run(cmd, capture_output=True, text=True, timeout=240, env=env)
        self.assertEqual(plan.returncode, 0, plan.stderr)
        for script in ("discover.py", "download_audio.py"):
            self.assertIn("--ytdlp " + str(self.ytdlp), next(l for l in plan.stdout.splitlines() if script in l))
        self.assertFalse(self.log.exists())
        done = subprocess.run(cmd + ["--go"], capture_output=True, text=True, timeout=240, env=env)
        self.assertEqual(done.returncode, 0, done.stdout[-2000:] + done.stderr[-2000:])
        out = done.stdout
        self.assertIn("WARNING: this yt-dlp was released", out)
        self.assertLess(out.index("TOOLS"), out.index("ESTIMATE"))
        queue = common.read_csv(self.root / "jobs" / "queue.csv")
        self.assertEqual({r["sources"] for r in queue}, {"discover"})             # the invented listings, nothing else
        self.assertEqual([(r["channel_dir"], r["listing_rank"]) for r in queue],
                         [("alpha", "0"), ("beta", "0"), ("alpha", "1"), ("beta", "1")])     # in rank order
        self.assertIn("queue for the newest 2 of every channel: 4 videos from 2 channels", out[out.index("ESTIMATE"):])
        self.assertIn("youtube   4 to do", out)
        self.assertIn("--ffmpeg " + self.ffmpeg, next(l for l in out.splitlines() if "download_audio.py" in l))
        recs = [r for r in self.audio_manifest() if r["status"] == "ok"]
        self.assertEqual({r["video_id"] for r in recs}, {r["video_id"] for r in queue})
        self.assertEqual({r["published"] for r in recs}, {"2023-06-15"})
        rows = {r["item_id"]: r for r in common.read_csv(self.root / "catalog" / "catalog.csv")}
        self.assertEqual({rows[r["video_id"]]["published"] for r in recs}, {"2023-06-15"})
        self.assertIn("done", out.splitlines()[-1])


class TestEstimate(NewestCase):
    def test_the_plan_counts_the_tier_queue_and_the_least_time_each_lane_takes(self):
        ids = self.listing({"alpha": 3, "beta": 2, "gamma": 2})
        self.select("--set", "all", "--newest", "2")
        # one video already downloaded, one settled for the captions: they are not counted as left to do
        first = ids["alpha"][0]
        path = self.root / "audio" / "alpha" / f"{first}.opus"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"FAKEOPUS" * 10)
        common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                            {"video_id": first, "channel_dir": "alpha", "status": "ok", "path": f"alpha/{first}.opus",
                             "bytes": 80})
        common.append_jsonl(self.root / "captions" / "captions_manifest.jsonl",
                            {"video_id": ids["beta"][0], "channel_dir": "beta", "status": "error",
                             "error_class": "no_captions"})
        before = sorted(p for p in self.root.rglob("*"))
        done = self.runner("--lanes", "youtube,captions", "--newest", "2")
        self.assertEqual(done.returncode, 0, done.stderr)
        out = done.stdout
        self.assertIn("estimate   queue for the newest 2 of every channel: 6 videos from 3 channels, "
                      "1.0 h with known length (0 unknown)", out)
        self.assertIn("youtube   5 to do (0.8 h known): at least 40 s at a start every 10 s shared by 2 worker(s)", out)
        self.assertIn("captions  5 to do: at least 40 s at a start every 10 s, 1 worker", out)
        self.assertLess(out.index("estimate"), out.index("dry run"))
        self.assertEqual(sorted(p for p in self.root.rglob("*")), before)          # the plan wrote nothing
        self.assertFalse(self.log.exists())                                       # and ran no yt-dlp

    def test_a_queue_built_for_another_tier_is_not_taken_for_this_one(self):
        self.listing({"alpha": 3})
        self.select("--set", "all", "--newest", "2")
        out = self.runner("--lanes", "youtube,captions", "--newest", "3").stdout
        self.assertIn("jobs/queue.csv was not built for this selection yet", out)
        self.assertNotIn("to do", out)
        out = self.runner("--lanes", "texts", "--newest", "3").stdout
        self.assertNotIn("estimate", out)                                         # no YouTube lane, no estimate

    def test_the_least_time_follows_the_pacing(self):
        self.assertEqual(run_all.pacing_floor(0, 10), 0)
        self.assertEqual(run_all.pacing_floor(1, 10), 0)
        self.assertEqual(run_all.pacing_floor(450, 10), 4490)                     # shared by the workers: not halved
        self.assertEqual(run_all.span(4490), "75 min")
        self.assertEqual(run_all.span(4 * 3600), "4.0 h")


class TestQueueFiles(NewestCase):
    """run_all.py --queue: the YouTube lanes over queue files built elsewhere, no listing and no queue step."""

    def queue_file(self, name, rows, fields=None):
        """A queue file of invented videos: rows (video_id, channel_dir, duration_s), in select_jobs.py's columns
        unless `fields` gives others."""
        path = self.tmp / "queues" / name
        rows = [{"video_id": v, "url": f"https://www.youtube.com/watch?v={v}", "channel_dir": c, "duration_s": d,
                 "sources": "test", "shard": 0, "note": f"about {v}"} for v, c, d in rows]
        common.write_csv(path, rows, fields or select_jobs.FIELDS)
        return path

    def go(self, *extra, env=None):
        return self.runner("--lanes", "youtube,captions", "--go", "--ytdlp", self.ytdlp, "--ffmpeg", self.ffmpeg,
                           "--ffprobe", "ffprobe-not-installed", "--min-interval", "0", "--watch", "1", "--workers", "1",
                           *extra, env={"FAKE_SLEEP": "0.05", **(env or {})})

    def test_the_plan_skips_the_listing_and_the_queue_step_and_hands_the_file_to_both_lanes(self):
        first = self.queue_file("one.csv", [(mk("DATE", 1), "alpha", 600), (mk("DATE", 2), "beta", 1200)])
        plan = self.runner("--lanes", "youtube,captions", "--queue", first)
        self.assertEqual(plan.returncode, 0, plan.stderr)
        out = plan.stdout
        for script in ("discover.py", "select_jobs.py"):
            self.assertNotIn(script, out)
        merged = str(self.root / "jobs" / "queue_run.csv")
        for script in ("download_audio.py", "fetch_captions.py"):
            self.assertIn(f"--queue {merged} --all", next(l for l in out.splitlines() if script in l))
        self.assertIn(f"first      queue: merge {first} into {merged} (2 videos, 0 repeated rows dropped)", out)
        self.assertIn("--workers 1 --min-interval 10.0", next(l for l in out.splitlines() if "fetch_captions.py" in l))
        self.assertIn("dry run", out)
        self.assertFalse(self.root.exists())                                      # the plan wrote nothing
        self.assertFalse(self.log.exists())                                       # and ran no tool

    def test_two_files_in_order_with_a_video_in_both(self):
        a, b, c, d = mk("DATE", 1), mk("DATE", 2), mk("PREM", 3), mk("DATE", 4)
        first = self.queue_file("one.csv", [(a, "alpha", 600), (b, "beta", 600)])
        # the second file in another column order, with a column of its own, and `b` again with other words
        second = self.queue_file("two.csv", [(c, "gamma", 300), (b, "beta-again", 999), (d, "alpha", 300)],
                                 fields=["note", "channel_dir", "video_id", "url", "duration_s"])
        done = self.go("--queue", first, "--queue", second)
        self.assertEqual(done.returncode, 0, done.stdout[-2000:] + done.stderr[-2000:])
        out = done.stdout
        self.assertIn("queue: 4 videos from 2 file(s) (1 repeated rows dropped)", out)
        self.assertLess(out.index("TOOLS"), out.index("queue: 4 videos"))         # the tools first, then the merge
        self.assertLess(out.index("queue: 4 videos"), out.index("ESTIMATE"))
        rows = common.read_csv(self.root / "jobs" / "queue_run.csv")
        self.assertEqual([r["video_id"] for r in rows], [a, b, c, d])              # in order, first occurrence kept
        self.assertEqual(rows[1]["channel_dir"], "beta")
        self.assertEqual(list(rows[0].keys()), select_jobs.FIELDS)                # the first file's columns
        self.assertEqual((rows[2]["channel_dir"], rows[2]["sources"]), ("gamma", ""))   # a missing column is empty
        meta = json.loads((self.root / "jobs" / "queue_run.meta.json").read_text(encoding="utf-8"))
        self.assertEqual((meta["videos"], meta["duplicates_dropped"], len(meta["files"])), (4, 1, 2))
        self.assertFalse((self.root / "jobs" / "queue.csv").exists())              # no queue step
        self.assertFalse((self.root / "discover").exists())                        # no listing
        self.assertEqual([e[1] for e in self.fake_events("START")], [a, b, c, d])  # the audio lane, in that order
        self.assertEqual([e[1] for e in self.fake_events("CAPS")], [a, b, c, d])   # and the captions lane
        self.assertEqual({r["video_id"] for r in self.audio_manifest() if r["status"] == "ok"}, {a, b, c, d})
        self.assertEqual({r["video_id"]: r["published"] for r in self.caption_manifest()},
                         {a: "2024-01-05", b: "2024-01-05", c: "2024-01-07", d: "2024-01-05"})
        self.assertIn("done", out.splitlines()[-1])
        # run again: what is stored is skipped by the lanes' own rules, nothing is asked for twice
        self.log.unlink()
        again = self.go("--queue", first, "--queue", second)
        self.assertEqual(again.returncode, 0, again.stderr[-2000:])
        self.assertIn("youtube   0 to do", again.stdout)
        self.assertIn("captions  0 to do", again.stdout)
        self.assertEqual(self.fake_events("START") + self.fake_events("CAPS"), [])

    def test_queue_is_refused_with_newest_or_per_channel(self):
        first = self.queue_file("one.csv", [(mk("DATE", 1), "alpha", 600)])
        for extra in (["--newest", "10"], ["--per-channel", "5"], ["--set", "bashar75"]):
            done = self.runner("--lanes", "youtube,captions", "--queue", first, *extra)
            self.assertEqual(done.returncode, 2, done.stdout)
            self.assertIn("--queue cannot be combined with --newest, --per-channel or --set", done.stderr)
            self.assertNotIn("PLAN", done.stdout)
        done = self.runner("--lanes", "texts", "--queue", first)
        self.assertEqual(done.returncode, 2)
        self.assertIn("name one of them in --lanes", done.stderr)
        self.assertFalse(self.root.exists())

    def test_a_missing_file_or_one_without_video_id_stops_before_any_tool_runs(self):
        missing = self.tmp / "queues" / "not-here.csv"
        done = self.go("--queue", missing)
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertIn(f"STOPPED: queue file not found: {missing}", done.stderr)
        self.assertNotIn("PLAN", done.stdout)
        self.assertNotIn("TOOLS", done.stdout)
        self.assertFalse(self.log.exists())                                       # not even yt-dlp --version
        self.assertFalse(self.root.exists())
        odd = self.tmp / "queues" / "ids.csv"
        odd.parent.mkdir(exist_ok=True)
        odd.write_text("id,url\nabc,https://example.invalid/\n", encoding="utf-8")
        good = self.queue_file("one.csv", [(mk("DATE", 1), "alpha", 600)])
        done = self.go("--queue", good, "--queue", odd)                           # the second file is wrong
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertIn(f"STOPPED: queue file has no video_id column: {odd} (columns: id, url)", done.stderr)
        self.assertFalse(self.log.exists())
        self.assertFalse(self.root.exists())
        empty = self.tmp / "queues" / "empty.csv"
        empty.write_text("", encoding="utf-8")
        done = self.runner("--lanes", "youtube,captions", "--queue", empty)
        self.assertEqual(done.returncode, 2)
        self.assertIn("has no video_id column", done.stderr)

    def test_the_estimate_counts_the_queue_rows(self):
        ids = [mk("DATE", i) for i in range(1, 6)]
        first = self.queue_file("one.csv", [(ids[0], "alpha", 1800), (ids[1], "alpha", 1800), (ids[2], "beta", 3600)])
        second = self.queue_file("two.csv", [(ids[2], "beta", 3600), (ids[3], "gamma", ""), (ids[4], "gamma", 1800)])
        # one already downloaded and one settled for the captions: not counted as left to do
        path = self.root / "audio" / "alpha" / f"{ids[0]}.opus"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"FAKEOPUS" * 10)
        common.append_jsonl(self.root / "audio" / "audio_manifest.jsonl",
                            {"video_id": ids[0], "channel_dir": "alpha", "status": "ok", "path": f"alpha/{ids[0]}.opus",
                             "bytes": 80})
        common.append_jsonl(self.root / "captions" / "captions_manifest.jsonl",
                            {"video_id": ids[1], "channel_dir": "alpha", "status": "error", "error_class": "no_captions"})
        before = sorted(p for p in self.root.rglob("*"))
        done = self.runner("--lanes", "youtube,captions", "--queue", first, "--queue", second)
        self.assertEqual(done.returncode, 0, done.stderr)
        out = done.stdout
        self.assertIn("estimate   queue for --queue one.csv, two.csv: 5 videos from 3 channels, "
                      "2.5 h with known length (1 unknown)", out)
        self.assertIn("youtube   4 to do (2.0 h known): at least 30 s at a start every 10 s shared by 2 worker(s)", out)
        self.assertIn("captions  4 to do: at least 30 s at a start every 10 s, 1 worker", out)
        self.assertEqual(sorted(p for p in self.root.rglob("*")), before)          # the plan wrote nothing
        self.assertFalse(self.log.exists())
        captions_only = self.runner("--lanes", "captions", "--queue", first).stdout
        self.assertIn("queue for --queue one.csv: 3 videos from 2 channels", captions_only)
        self.assertNotIn("youtube ", captions_only[captions_only.index("estimate"):])


# --------------------------------------------------------------------------- 5. what must not change
class TestGateAndPacingUnchanged(NewestCase):
    def without_override(self):
        return {k: v for k, v in os.environ.items() if k != common.YOUTUBE_OVERRIDE}

    def run_off(self, script, *args):
        env = {**self.without_override(), "FAKE_LOG": str(self.log)}
        return subprocess.run([sys.executable, "-I", str(PIPE / script), *map(str, args)], capture_output=True,
                              text=True, timeout=240, env=env)

    def test_the_gate_still_holds_every_youtube_step(self):
        self.write_queue([(mk("DATE", 1), "chanA", 600)])
        for script, args in (("download_audio.py", ["--ytdlp", self.ytdlp, "--ffmpeg", self.ffmpeg, "--all"]),
                             ("fetch_captions.py", ["--ytdlp", self.ytdlp, "--all"])):
            done = self.run_off(script, "--root", self.root, *args)
            self.assertEqual(done.returncode, common.SKIPPED_BY_RULE, done.stderr)
            self.assertIn("Nothing was sent", done.stderr)
        plan = self.run_off("run_all.py", "--root", self.root, "--store", f"dir:{self.tmp / 'store'}",
                            "--lanes", "youtube,captions,texts", "--newest", "10")
        self.assertIn("skipped: the youtube and captions lane(s)", plan.stderr)
        self.assertNotIn("download_audio.py", plan.stdout)
        self.assertNotIn("estimate", plan.stdout)
        gone = self.run_off("run_all.py", "--root", self.root, "--store", f"dir:{self.tmp / 'store'}",
                            "--lanes", "youtube,captions", "--newest", "10", "--go", "--ytdlp", self.ytdlp)
        self.assertEqual(gone.returncode, common.SKIPPED_BY_RULE)
        self.assertFalse(self.log.exists())                                       # yt-dlp never ran, not even --version

    def test_the_runner_paces_the_lanes_as_before(self):
        plan = self.runner("--lanes", "youtube,captions", "--newest", "10").stdout
        youtube = next(l for l in plan.splitlines() if "download_audio.py" in l)
        captions = next(l for l in plan.splitlines() if "fetch_captions.py" in l)
        self.assertIn("--workers 2 --min-interval 10.0", youtube)
        self.assertIn("--workers 1 --min-interval 10.0", captions)
        fast = self.runner("--lanes", "youtube,captions", "--min-interval", "1").stdout
        self.assertIn("--workers 1 --min-interval 5.0", next(l for l in fast.splitlines() if "fetch_captions.py" in l))
        defaults = argparse_defaults("run_all.py")
        self.assertEqual((defaults["--workers"], defaults["--min-interval"]), (2, 10.0))

    def test_the_lanes_keep_their_defaults(self):
        audio = argparse_defaults("download_audio.py")
        self.assertEqual((audio["--workers"], audio["--min-interval"], audio["--stop-after-blocks"],
                          audio["--sleep-requests"], audio["--per-channel"]), (2, 10.0, 3, 0.75, 2))
        caps = argparse_defaults("fetch_captions.py")
        self.assertEqual((caps["--min-interval"], caps["--stop-after-blocks"]), (5.0, 3))

    def test_three_bot_checks_still_stop_both_lanes(self):
        self.write_queue([(mk("BOT", i), "chanA", 600) for i in range(6)])
        done = self.download("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3, done.stderr)
        self.assertEqual(len(self.fake_events("START")), 3)
        self.write_queue([(mk("BOTC", i), "chanA", 600) for i in range(6)])
        done = self.captions("--all", "--workers", "1")
        self.assertEqual(done.returncode, 3, done.stderr)
        self.assertEqual(len(self.fake_events("CAPS")), 3)

    def test_no_evasion_in_either_command(self):
        url = {"url": "https://www.youtube.com/watch?v=" + mk("VID", 1)}
        audio = download_audio.ytdlp_cmd(argparse.Namespace(ytdlp="yt-dlp", format="bestaudio", limit_rate=""), url, Path("w"))
        caps = fetch_captions.ytdlp_cmd(argparse.Namespace(ytdlp="yt-dlp", languages="en"), url, Path("w"))
        for cmd in (audio, caps):
            joined = " ".join(cmd)
            for word in ("--cookies", "--proxy", "--username", "--password", "--netrc", "--impersonate",
                         "--extractor-args", "player_client", "po_token", "--add-header", "--geo-bypass"):
                self.assertNotIn(word, joined)
            self.assertIn("--ignore-config", cmd)


if __name__ == "__main__":
    unittest.main()
