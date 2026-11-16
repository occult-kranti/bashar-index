#!/usr/bin/env python3
"""Tests for transcript_audio.py: every audio state of an item with a transcript, parts on Drive, withdrawn
store lines, the partition, the gaps, and that the public CSV carries counts only. Invented root, no network.

    python3 -I et-channelers/pipeline/tests/test_transcript_audio.py
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIPE = HERE.parent
sys.path.insert(0, str(PIPE))

import common  # noqa: E402
import transcript_audio as ta  # noqa: E402

STORE = "gh:someone/private-archive@v1"
CATALOG_FIELDS = ("item_id", "person_id", "lane", "relation", "title", "duration_s", "published", "audio_status",
                  "audio_path", "audio_bytes", "publisher_text_status", "captions_status", "asr_status", "twin_of",
                  "twin_method", "feed_key", "interview_type", "source_url")

# invented ids (11 characters: YouTube-shaped; "<lane>-<16 hex>": the other lanes)
YT_TEXT = "ytAAAAAAAA1"        # YouTube video with captions, nothing downloaded
YT_FAIL = "ytAAAAAAAA2"        # YouTube video with captions, an earlier download failed (bot check)
YT_TWIN = "ytAAAAAAAA3"        # the video a page's text belongs to (nothing downloaded)
YT_DONE = "ytAAAAAAAA4"        # the video a page's text belongs to: downloaded, left the disk, in store, on Drive; no text
POD_DISK = "pod-00000000000000a1"   # downloaded, on disk, in store, all parts on Drive
POD_GONE = "pod-00000000000000a2"   # downloaded, deleted from disk, in store, partly on Drive -> pull back
POD_WAIT = "pod-00000000000000a3"   # text, recording not downloaded yet (fetchable here)
POD_LOST = "pod-00000000000000a4"   # downloaded, store line withdrawn -> not in store, not on Drive, on disk
POD_FAIL = "pod-00000000000000a5"   # text, download failed (unavailable): fetchable here
POD_HELD = "pod-00000000000000a6"   # interview-show episode (host) that is a conversation: held by policy, not queued
POD_HFAIL = "pod-00000000000000a7"  # interview-show episode that is a conversation, an earlier download failed: never queued
WEB_PAGE = "web-00000000000000b1"   # a page with no recording
WEB_TWIN = "web-00000000000000b2"   # a page whose recording is the YouTube video YT_TWIN (not downloaded)
WEB_FILE = "web-00000000000000b3"   # creator file with text, not downloaded yet
WEB_VIA = "web-00000000000000b4"    # a page whose recording is the YouTube video YT_DONE: downloaded through the twin
IA_OK = "ia-000000000000000c1"      # archive.org, downloaded, on disk, in store, on Drive (one part), both texts
NO_TEXT = "pod-00000000000000d1"    # downloaded, no transcript: not in the table
TITLE = "Invented Session Title Zq"


def cat(item, person, lane, relation, audio="", text="", caps="", asr="", twin="", path="", nbytes="", interview=""):
    return {"item_id": item, "person_id": person, "lane": lane, "relation": relation, "title": TITLE + " " + item,
            "duration_s": "100", "published": "2024-01-02", "audio_status": audio, "audio_path": path,
            "audio_bytes": nbytes, "publisher_text_status": text, "captions_status": caps, "asr_status": asr,
            "twin_of": twin, "twin_method": "title" if twin else "", "feed_key": "", "interview_type": interview,
            "source_url": f"https://example.invalid/{item}.mp3"}


class RootCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="etta-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "private"
        self.plan = self.tmp / "plan"
        self.paths = common.layout(self.root)
        (self.root / "catalog").mkdir(parents=True)
        self.write_catalog()
        self.write_manifests()

    def audio(self, item, person="alice", size=1000, on_disk=True):
        rel = f"audio/{person}/{item}.opus"
        if on_disk:
            f = self.root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"x" * size)
        return {"path": rel, "nbytes": str(size)}

    def write_catalog(self):
        rows = [
            cat(YT_TEXT, "alice", "youtube", "youtube", caps="ok"),
            cat(YT_FAIL, "alice", "youtube", "youtube", audio="error", caps="ok"),
            cat(YT_TWIN, "bob", "youtube", "youtube"),
            cat(YT_DONE, "bob", "youtube", "youtube", audio="ok", **self.audio(YT_DONE, "bob", on_disk=False)),
            cat(POD_DISK, "alice", "pod", "own", audio="ok", asr="ok", **self.audio(POD_DISK)),
            cat(POD_GONE, "alice", "pod", "own", audio="ok", asr="ok", text="ok", **self.audio(POD_GONE, on_disk=False)),
            cat(POD_WAIT, "alice", "pod", "host", text="ok", twin=YT_TWIN, interview="live channeling"),
            cat(POD_LOST, "bob", "pod", "own", audio="ok", asr="ok", **self.audio(POD_LOST, "bob")),
            cat(POD_FAIL, "bob", "pod", "own", audio="error", text="ok"),
            cat(POD_HELD, "bob", "pod", "host", text="ok", twin=YT_TWIN, interview="conversation"),
            cat(POD_HFAIL, "bob", "pod", "host", audio="error", text="ok", interview="conversation"),
            cat(WEB_PAGE, "bob", "web", "page", text="ok"),
            cat(WEB_TWIN, "bob", "web", "page", text="ok", twin=YT_TWIN),
            cat(WEB_FILE, "bob", "web", "file", text="ok"),
            cat(WEB_VIA, "bob", "web", "page", text="ok", twin=YT_DONE),
            cat(IA_OK, "bob", "ia", "archive", audio="ok", asr="ok", text="ok", **self.audio(IA_OK, "bob")),
            cat(NO_TEXT, "alice", "pod", "own", audio="ok", **self.audio(NO_TEXT)),
        ]
        common.write_csv(self.root / "catalog" / "catalog.csv", rows, CATALOG_FIELDS)

    def write_manifests(self):
        am = self.root / "audio" / "audio_manifest.jsonl"
        for item, status, cls in ((YT_FAIL, "error", "bot_check"), (POD_FAIL, "error", "network"), (POD_FAIL, "error", "unavailable"),
                                  (POD_HFAIL, "error", "unavailable"), (POD_DISK, "ok", None), (POD_GONE, "ok", None),
                                  (POD_LOST, "ok", None), (IA_OK, "ok", None), (YT_DONE, "ok", None)):
            rec = {"video_id": item, "status": status, "channel_dir": "x"}
            if cls:
                rec["error_class"] = cls
            common.append_jsonl(am, rec)
        sm = self.root / "sync" / "sync_manifest.jsonl"
        for item in (POD_DISK, POD_GONE, POD_LOST, IA_OK, NO_TEXT, YT_DONE):
            common.append_jsonl(sm, {"video_id": item, "kind": "audio", "store": STORE, "verified": True})
        common.append_jsonl(sm, {"video_id": POD_DISK, "kind": "asr", "store": STORE, "verified": True})
        common.append_jsonl(sm, {"video_id": POD_LOST, "kind": "audio", "store": STORE, "withdrawn": True})
        common.append_jsonl(sm, {"video_id": WEB_FILE, "kind": "audio", "store": STORE})   # never verified
        dm = self.root / "sync" / "drive_manifest.jsonl"
        common.append_jsonl(dm, {"key": "f", "kind": "folder", "path": ["alice"], "drive_id": "d0"})
        for part in (1, 2, 3):
            common.append_jsonl(dm, {"item_id": POD_DISK, "mime": "audio/ogg", "part": part, "parts": 3, "drive_id": f"d{part}"})
        common.append_jsonl(dm, {"item_id": POD_DISK, "mime": "audio/ogg", "part": 2, "parts": 3, "drive_id": "d2b"})  # re-upload
        common.append_jsonl(dm, {"item_id": POD_GONE, "mime": "audio/ogg", "part": 1, "parts": 2, "drive_id": "d5"})
        common.append_jsonl(dm, {"item_id": IA_OK, "mime": "audio/ogg", "part": 1, "parts": 1, "drive_id": "d6"})
        common.append_jsonl(dm, {"item_id": YT_DONE, "mime": "audio/ogg", "part": 1, "parts": 1, "drive_id": "d8"})
        common.append_jsonl(dm, {"item_id": POD_LOST, "mime": "text/plain", "part": 1, "parts": 1, "drive_id": "d7"})  # a text, not audio

    def run_tool(self, *extra):
        return subprocess.run([sys.executable, "-I", str(PIPE / "transcript_audio.py"), "--root", str(self.root),
                               "--plan-dir", str(self.plan), *extra], capture_output=True, text=True, timeout=120)

    def rows(self):
        return {r["item_id"]: r for r in ta.build_rows(self.paths)}


class TestStates(RootCase):
    def test_only_items_with_a_transcript_are_listed_once_under_each_kind(self):
        rows = self.rows()
        self.assertNotIn(NO_TEXT, rows)
        self.assertNotIn(YT_TWIN, rows)
        self.assertNotIn(YT_DONE, rows)
        self.assertEqual(rows[POD_GONE]["kinds"], ["made", "source"])
        self.assertEqual(rows[YT_TEXT]["kinds"], ["captions"])
        self.assertEqual(rows[WEB_PAGE]["kinds"], ["source"])

    def test_each_state(self):
        rows = self.rows()
        states = {k: r["state"] for k, r in rows.items()}
        self.assertEqual(states, {
            YT_TEXT: "no_audio_youtube", YT_FAIL: "failed", POD_DISK: "downloaded", POD_GONE: "downloaded",
            POD_WAIT: "no_audio_not_yet", POD_LOST: "downloaded", POD_FAIL: "failed", WEB_PAGE: "no_audio_page",
            WEB_TWIN: "no_audio_youtube", WEB_FILE: "no_audio_not_yet", IA_OK: "downloaded",
            POD_HELD: "no_audio_interview_held", POD_HFAIL: "failed", WEB_VIA: "downloaded"})
        # a podcast item with a YouTube twin keeps its own recording: it is fetchable here, not a YouTube wait
        self.assertTrue(rows[POD_WAIT]["fetchable_here"])
        # an interview episode that is not live channeling is held by policy: never queued, whatever its twin
        self.assertFalse(rows[POD_HELD]["fetchable_here"])
        self.assertIn("held by policy", rows[POD_HELD]["why"])
        # ... and a failed download of such an episode is not queued again either
        self.assertFalse(rows[POD_HFAIL]["fetchable_here"])
        self.assertEqual(rows[POD_HFAIL]["error_class"], "unavailable")
        self.assertFalse(rows[WEB_TWIN]["fetchable_here"])
        self.assertFalse(rows[WEB_VIA]["fetchable_here"])
        self.assertFalse(rows[YT_FAIL]["fetchable_here"])
        self.assertTrue(rows[POD_FAIL]["fetchable_here"])
        self.assertTrue(rows[WEB_FILE]["fetchable_here"])
        # every item but the page that looks through to its twin is its own recording
        self.assertEqual({k for k, r in rows.items() if r["audio_item"] != k}, {WEB_VIA})

    def test_a_page_takes_the_audio_state_of_its_downloaded_twin(self):
        rows = self.rows()
        via = rows[WEB_VIA]
        self.assertEqual((via["state"], via["audio_item"]), ("downloaded", YT_DONE))
        self.assertIn(YT_DONE, via["why"])
        self.assertEqual(via["audio_path"], f"audio/bob/{YT_DONE}.opus")
        self.assertFalse(via["on_disk"])
        self.assertTrue(via["in_store"])
        self.assertEqual(via["stores"], [STORE])
        self.assertEqual(via["drive_state"], "all")
        self.assertFalse(via["pull_back"])
        # a page whose twin has no audio yet keeps the class of what the twin is
        self.assertEqual((rows[WEB_TWIN]["state"], rows[WEB_TWIN]["audio_item"]), ("no_audio_youtube", WEB_TWIN))
        # a page whose twin's download failed is a failed download, with the twin's error class
        catalog = {YT_FAIL: cat(YT_FAIL, "alice", "youtube", "youtube", audio="error")}
        page = cat(WEB_PAGE, "alice", "web", "page", text="ok", twin=YT_FAIL)
        state, why, audio = ta.resolve(page, catalog)
        self.assertEqual((state, audio["item_id"]), ("failed", YT_FAIL))
        self.assertIn(YT_FAIL, why)
        # a twin that is not in the catalogue, or an item that is not a page, is never looked through
        self.assertEqual(ta.resolve(page, {})[2]["item_id"], WEB_PAGE)
        pod = cat(POD_WAIT, "alice", "pod", "host", text="ok", twin=YT_DONE, interview="live channeling")
        self.assertEqual(ta.resolve(pod, {YT_DONE: cat(YT_DONE, "bob", "youtube", "youtube", audio="ok")})[2]["item_id"], POD_WAIT)
        # counts follow the look-through: the page is a downloaded item in store and on Drive
        counts = {(c["person_id"], c["kind"]): c for c in ta.count(list(rows.values()))}
        self.assertEqual(counts[("bob", "source")]["audio_downloaded"], 2)   # the archive item and the page via its twin
        self.assertEqual(counts[("bob", "source")]["on_drive"], 2)
        self.assertEqual(counts[("bob", "source")]["in_store"], 2)

    def test_drive_parts_are_counted_from_the_last_split(self):
        lines = [{"item_id": POD_DISK, "mime": "audio/ogg", "part": p, "parts": 3} for p in (1, 2, 3)]
        self.assertEqual(ta.drive_index(lines)[POD_DISK], (3, 3))
        lines.append({"item_id": POD_DISK, "mime": "audio/ogg", "part": 1, "parts": 2})     # uploaded again in two parts
        self.assertEqual(ta.drive_index(lines)[POD_DISK], (1, 2), "the parts of the old split do not count")
        lines.append({"item_id": POD_DISK, "mime": "audio/ogg", "part": 2, "parts": 2})
        self.assertEqual(ta.drive_index(lines)[POD_DISK], (2, 2))
        lines.append({"item_id": POD_DISK, "mime": "audio/ogg", "part": 2, "parts": 2})     # the same part again
        self.assertEqual(ta.drive_index(lines)[POD_DISK], (2, 2))

    def test_a_file_the_sync_removes_counts_as_not_on_disk(self):
        self.assertEqual(ta.disk_state(None, "10"), (False, False))
        self.assertEqual(ta.disk_state(self.root / "audio" / "nowhere.opus", "10"), (False, False))
        self.assertEqual(ta.disk_state(self.root / "audio" / "alice" / f"{POD_DISK}.opus", "1000"), (True, False))
        self.assertEqual(ta.disk_state(self.root / "audio" / "alice" / f"{POD_DISK}.opus", "999"), (True, True))
        self.assertEqual(ta.disk_state(self.root / "audio" / "alice" / f"{POD_DISK}.opus", ""), (True, False))
        self.assertEqual(ta.disk_state(self.root / "audio" / "alice", "10"), (False, False))   # a folder is not the file

    def test_failed_downloads_carry_the_latest_error_class(self):
        rows = self.rows()
        self.assertEqual(rows[YT_FAIL]["error_class"], "bot_check")
        self.assertEqual(rows[POD_FAIL]["error_class"], "unavailable")   # the latest manifest line wins
        self.assertEqual(rows[POD_DISK]["error_class"], "")

    def test_on_disk_store_and_drive(self):
        rows = self.rows()
        self.assertTrue(rows[POD_DISK]["on_disk"])
        self.assertFalse(rows[POD_GONE]["on_disk"])
        self.assertTrue(rows[POD_DISK]["in_store"])
        self.assertEqual(rows[POD_DISK]["stores"], [STORE])
        self.assertFalse(rows[POD_LOST]["in_store"], "a withdrawn line takes the item out of the store")
        self.assertFalse(rows[WEB_FILE]["in_store"], "a line that was never verified is no copy")
        self.assertEqual((rows[POD_DISK]["drive_parts_seen"], rows[POD_DISK]["drive_parts"], rows[POD_DISK]["drive_state"]), (3, 3, "all"))
        self.assertEqual(rows[POD_GONE]["drive_state"], "partly")
        self.assertEqual(rows[IA_OK]["drive_state"], "all")
        self.assertEqual(rows[POD_LOST]["drive_state"], "none", "a text volume on Drive is not the audio")
        self.assertFalse(rows[POD_GONE]["disk_size_differs"])

    def test_a_file_of_another_size_is_flagged(self):
        (self.root / "audio" / "alice" / f"{POD_DISK}.opus").write_bytes(b"y" * 10)
        rows = self.rows()
        self.assertTrue(rows[POD_DISK]["on_disk"])
        self.assertTrue(rows[POD_DISK]["disk_size_differs"])

    def test_a_running_process_hold_is_shown(self):
        common.hold_items(self.root, "test", [POD_DISK])
        rows = self.rows()
        self.assertTrue(rows[POD_DISK]["held"])
        self.assertFalse(rows[IA_OK]["held"])

    def test_pull_back_is_in_store_not_on_disk_not_fully_on_drive(self):
        rows = self.rows()
        self.assertEqual([k for k, r in rows.items() if r["pull_back"]], [POD_GONE])
        # a page and its twin share one recording: it is pulled back once
        twin = dict(rows[POD_GONE], item_id=WEB_PAGE, audio_item=POD_GONE)
        pulls = ta.pull_back([rows[POD_GONE], twin, rows[POD_DISK]])
        self.assertEqual([p["item_id"] for p in pulls], [POD_GONE])

    def test_a_page_whose_twin_is_another_lanes_item_waits_for_that_item(self):
        state, why = ta.classify({"lane": "web", "relation": "page", "audio_status": "", "twin_of": POD_WAIT})
        self.assertEqual(state, "no_audio_not_yet")
        self.assertIn("pod item", why)
        self.assertEqual(ta.classify({"lane": "page", "relation": "", "audio_status": "", "twin_of": ""})[0], "no_audio_page")

    def test_interview_episodes_are_held_unless_they_are_live_channeling(self):
        host = {"lane": "pod", "relation": "host", "audio_status": "", "twin_of": ""}
        for kind in ("conversation", "commentary or clip", "unclear", "not classified", ""):
            self.assertEqual(ta.classify({**host, "interview_type": kind})[0], "no_audio_interview_held", kind)
        self.assertIn("held by policy", ta.classify({**host, "interview_type": "conversation"})[1])
        # an episode nobody has classified yet waits for its classification: the same class, another reason
        for kind in ("not classified", ""):
            self.assertIn("not classified yet", ta.classify({**host, "interview_type": kind})[1])
            self.assertNotIn("held by policy", ta.classify({**host, "interview_type": kind})[1])
        self.assertEqual(ta.classify({**host, "interview_type": "live channeling"})[0], "no_audio_not_yet")
        # a downloaded or failed episode keeps its own class whatever its kind
        self.assertEqual(ta.classify({**host, "interview_type": "conversation", "audio_status": "ok"})[0], "downloaded")
        self.assertEqual(ta.classify({**host, "interview_type": "conversation", "audio_status": "error"})[0], "failed")
        # the maker's own podcast is never held
        self.assertEqual(ta.classify({**host, "relation": "own", "interview_type": "conversation"})[0], "no_audio_not_yet")

    def test_only_filters_persons(self):
        rows = {r["item_id"] for r in ta.build_rows(self.paths, {"bob"})}
        self.assertIn(WEB_PAGE, rows)
        self.assertNotIn(POD_DISK, rows)


class TestCounts(RootCase):
    def test_counts_per_person_and_kind_with_totals(self):
        counts = {(c["person_id"], c["kind"]): c for c in ta.count(ta.build_rows(self.paths))}
        self.assertEqual(set(k for k in counts if k[0] == "all"), {("all", "made"), ("all", "source"), ("all", "captions"), ("all", "any")})
        tot = counts[("all", "any")]
        self.assertEqual(tot["items_with_text"], 14)
        self.assertEqual(tot["audio_downloaded"], 5)
        self.assertEqual(tot["on_disk"], 3)
        self.assertEqual(tot["in_store"], 4)
        self.assertEqual(tot["not_in_store"], 1)
        self.assertEqual(tot["on_drive"], 3)
        self.assertEqual(tot["partly_on_drive"], 1)
        self.assertEqual(tot["not_on_drive"], 1)
        self.assertEqual(tot["no_audio_page"], 1)
        self.assertEqual(tot["no_audio_youtube"], 2)
        self.assertEqual(tot["no_audio_interview_held"], 1)
        self.assertEqual(tot["no_audio_not_yet"], 2)
        self.assertEqual(tot["download_failed"], 3)
        self.assertEqual(counts[("all", "captions")]["items_with_text"], 2)
        self.assertEqual(counts[("all", "made")]["items_with_text"], 4)
        self.assertEqual(counts[("all", "source")]["items_with_text"], 10)
        self.assertEqual(counts[("bob", "source")]["no_audio_interview_held"], 1)
        self.assertEqual(counts[("alice", "any")]["no_audio_interview_held"], 0)
        self.assertEqual(counts[("alice", "captions")]["download_failed"], 1)
        self.assertEqual(counts[("bob", "made")]["audio_downloaded"], 2)
        self.assertNotIn(("alice", "captions_x"), counts)
        # the kinds are kept apart: one item with two texts is counted under both, and once under "any"
        self.assertEqual(counts[("alice", "made")]["items_with_text"] + counts[("alice", "source")]["items_with_text"]
                         + counts[("alice", "captions")]["items_with_text"], 6)
        self.assertEqual(counts[("alice", "any")]["items_with_text"], 5)

    def test_the_partition_holds_for_every_row_and_is_checked(self):
        counts = ta.count(ta.build_rows(self.paths))
        for c in counts:
            ta.check_partition(c)
            self.assertEqual(c["audio_downloaded"] + c["no_audio_page"] + c["no_audio_youtube"] + c["no_audio_interview_held"]
                             + c["no_audio_not_yet"] + c["download_failed"], c["items_with_text"])
            self.assertEqual(c["in_store"] + c["not_in_store"], c["audio_downloaded"])
            self.assertEqual(c["on_drive"] + c["partly_on_drive"] + c["not_on_drive"], c["audio_downloaded"])
        broken = dict(counts[0], no_audio_page=counts[0]["no_audio_page"] + 1)
        with self.assertRaises(AssertionError):
            ta.check_partition(broken)
        broken = dict(counts[-1], in_store=counts[-1]["in_store"] + 1)
        with self.assertRaises(AssertionError):
            ta.check_partition(broken)
        broken = dict(counts[-1], no_audio_interview_held=counts[-1]["no_audio_interview_held"] + 1)
        with self.assertRaises(AssertionError):
            ta.check_partition(broken)

    def test_a_kind_nobody_has_still_gets_a_total_row_at_zero(self):
        rows = [r for r in ta.build_rows(self.paths) if "captions" not in r["kinds"]]
        counts = {(c["person_id"], c["kind"]): c for c in ta.count(rows)}
        self.assertEqual(counts[("all", "captions")]["items_with_text"], 0)
        self.assertNotIn(("alice", "captions"), counts)

    def test_totals_add_the_persons(self):
        counts = {(c["person_id"], c["kind"]): c for c in ta.count(ta.build_rows(self.paths))}
        for kind in ta.KINDS:
            for f in ta.COUNT_FIELDS[2:]:
                self.assertEqual(counts[("all", kind)][f], sum(c[f] for (p, k), c in counts.items() if k == kind and p != "all"))


class TestOutputs(RootCase):
    def test_private_outputs_and_the_public_csv_hold_counts_only(self):
        done = self.run_tool("--publish-counts")
        self.assertEqual(done.returncode, 0, done.stderr)
        out = self.root / "analysis" / "coverage"
        lines = [json.loads(l) for l in (out / "transcript_audio.jsonl").read_text().splitlines()]
        self.assertEqual(len(lines), 14)
        self.assertEqual(set(lines[0]), set(ta.ITEM_FIELDS))
        self.assertTrue((out / "transcript_audio.md").is_file())
        md = (out / "transcript_audio.md").read_text()
        self.assertIn("## Totals per kind", md)
        self.assertIn("as of the run time", md)   # the numbers move while the cycles run
        self.assertIn("no audio: interview held", md)
        public = self.plan / "transcript_audio.csv"
        self.assertTrue(public.is_file())
        with open(public, newline="") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(tuple(rows[0].keys()), ta.COUNT_FIELDS)
        text = public.read_text()
        for item in (YT_TEXT, YT_FAIL, YT_DONE, POD_DISK, POD_GONE, WEB_PAGE, WEB_VIA, IA_OK, NO_TEXT):
            self.assertNotIn(item, text)
        self.assertNotIn(TITLE, text)
        self.assertNotIn("example.invalid", text)
        self.assertNotIn("audio/", text)
        for row in rows:
            self.assertIn(row["kind"], ta.KINDS)
            self.assertRegex(row["person_id"], r"^(all|[a-z]+)$")
            for f in ta.COUNT_FIELDS[2:]:
                self.assertTrue(row[f].isdigit(), f)
        self.assertEqual([r["person_id"] for r in rows][-4:], ["all"] * 4)
        self.assertIn("any", done.stdout)

    def test_only_with_publish_counts_is_refused(self):
        done = self.run_tool("--only", "alice", "--publish-counts")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("--publish-counts cannot go with --only", done.stderr)
        self.assertFalse((self.plan / "transcript_audio.csv").exists())
        self.assertFalse((self.root / "analysis" / "coverage" / "transcript_audio_counts.csv").exists())
        done = self.run_tool("--only", "alice")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertFalse((self.plan / "transcript_audio.csv").exists())

    def test_without_publish_counts_nothing_lands_in_plan(self):
        done = self.run_tool()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertFalse((self.plan / "transcript_audio.csv").exists())
        self.assertTrue((self.root / "analysis" / "coverage" / "transcript_audio_counts.csv").is_file())
        self.assertFalse((self.root / "analysis" / "coverage" / "transcript_audio_fetch.csv").exists())

    def test_gaps_default_columns(self):
        done = self.run_tool("--gaps")
        self.assertEqual(done.returncode, 0, done.stderr)
        out = self.root / "analysis" / "coverage"
        with open(out / "transcript_audio_fetch.csv", newline="") as fh:
            fetch = list(csv.DictReader(fh))
        self.assertEqual(tuple(fetch[0].keys()), ta.QUEUE_FIELDS)
        self.assertEqual({r["video_id"] for r in fetch}, {POD_WAIT, POD_FAIL, WEB_FILE})   # POD_HELD is held by policy
        by = {r["video_id"]: r for r in fetch}
        self.assertEqual(by[POD_WAIT]["url"], f"https://example.invalid/{POD_WAIT}.mp3")
        self.assertEqual(by[POD_WAIT]["channel_dir"], "alice")
        with open(out / "transcript_audio_pull.csv", newline="") as fh:
            pull = list(csv.DictReader(fh))
        self.assertEqual([(r["item_id"], r["drive_state"]) for r in pull], [(POD_GONE, "partly")])
        self.assertIn("## Gaps", (out / "transcript_audio.md").read_text())

    def test_gaps_take_the_cycle_queues_columns_and_rows(self):
        fields = ("video_id", "url", "channel_dir", "title", "duration_s", "published", "lane", "relation", "feed_key",
                  "guid", "twin_of", "twin_method", "twin_score", "twin_candidate", "transcript_url", "transcript_type",
                  "bytes_hint", "interview_type", "shard")
        common.write_csv(self.root / "jobs" / "queue_cycle.csv",
                         [{"video_id": WEB_FILE, "url": "https://maker.invalid/file.mp3", "channel_dir": "bob",
                           "title": "queued title", "guid": "g-1", "bytes_hint": "123", "shard": 2}], fields)
        _, rows = ta.fetch_queue(ta.build_rows(self.paths), self.paths)
        self.assertEqual(tuple(rows[0].keys()), fields)
        by = {r["video_id"]: r for r in rows}
        self.assertEqual(by[WEB_FILE]["url"], "https://maker.invalid/file.mp3")   # the queue's row is copied
        self.assertEqual(by[WEB_FILE]["guid"], "g-1")
        self.assertEqual(by[WEB_FILE]["bytes_hint"], "123")
        self.assertEqual(by[WEB_FILE]["lane"], "web")                                  # blanks come from the catalogue
        self.assertEqual(by[POD_WAIT]["twin_of"], YT_TWIN)                               # the rest from the catalogue
        self.assertEqual(by[POD_WAIT]["guid"], "")
        self.assertEqual(by[POD_WAIT]["shard"], 0)
        self.assertNotIn(POD_HFAIL, by)   # a failed interview episode that is not live channeling is not queued again

    def test_queue_files_are_read_newest_first_and_only_those_with_video_ids(self):
        jobs = self.root / "jobs"
        common.write_csv(jobs / "queue_old.csv", [{"video_id": WEB_FILE, "url": "https://old.invalid/a.mp3"}], ("video_id", "url"))
        common.write_csv(jobs / "queue_listing.csv", [{"channel": "c", "note": WEB_FILE}], ("channel", "note"))   # no video_id column
        os.utime(jobs / "queue_old.csv", (1_600_000_000, 1_600_000_000))
        common.write_csv(jobs / "queue_new.csv", [{"video_id": WEB_FILE, "url": "https://new.invalid/a.mp3"}], ("video_id", "url"))
        os.utime(jobs / "queue_new.csv", (1_700_000_000, 1_700_000_000))
        found = ta.queued_rows(self.paths, {WEB_FILE, POD_WAIT})
        self.assertEqual(found[WEB_FILE]["url"], "https://new.invalid/a.mp3")
        self.assertNotIn(POD_WAIT, found)
        self.assertEqual(ta.queued_rows(self.paths, set()), {})

    def test_the_root_must_be_outside_git(self):
        inside = PIPE / "tests" / "_not_a_root"
        done = subprocess.run([sys.executable, "-I", str(PIPE / "transcript_audio.py"), "--root", str(inside)],
                              capture_output=True, text=True, timeout=60)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("Git checkout", done.stderr)
        self.assertFalse(inside.exists())


if __name__ == "__main__":
    unittest.main(verbosity=1)
