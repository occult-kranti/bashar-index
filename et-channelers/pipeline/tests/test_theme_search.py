#!/usr/bin/env python3
"""Tests for pipeline/theme_search.py with an invented root and an invented theme: matching and excluding (unit and
overlap excludes, scopes by id and by topic, kinds, look-ahead includes, the screen), the theme files' own examples
and must-keep sentences, kinds kept apart, near-copies (punctuation apart), twin titles read once, dates (--dates-from,
a text's opening date) and target windows (past anchors), twins and the tier scope, the queued titles, the priority
queue copied byte for byte from the tier queue, the public counts without text (the invented ones and the published
plan/theme_*.csv), the blinded sample (names masked, every twin hit in it), the score of two coders' labels, the
measure of earlier labels (kinds apart, hash-only labels, a coded sample) and the leak check.

    python3 -I -m unittest discover -s et-channelers/pipeline/tests -p test_theme_search.py -v
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

PIPE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPE))
import prediction_pilot as pp  # noqa: E402
import theme_search as ts  # noqa: E402

REAL_PLAN = ts.ET_ROOT / "plan"
QUEUE_FIELDS = ["video_id", "url", "channel_dir", "title", "duration_s", "channeling", "entity", "sources", "shard",
                "tab", "listing_rank", "upload_date_approx"]
CATALOG_FIELDS = ["item_id", "person_id", "lane", "relation", "tab", "title", "published", "publisher_text_path",
                  "captions_path", "asr_path", "twin_of", "twin_method"]

# an invented theme; every name, word and sentence below is made up for the test
MINI = {
    "theme": "darkzone", "description": "invented test theme", "generic_topics": ["unspecified"],
    "topics": ["power_grid", "internet_communications", "electronics_general", "unspecified"],
    "markers": {"advice": r"\b(?:stock up|candles?|prepar\w*)\b"},
    "include": [
        {"id": "blackout", "topic": "unspecified", "pattern": r"\bblack-?outs?\b"},
        {"id": "blackout_power", "topic": "power_grid", "pattern": r"\b(?:power|rolling)\s+black-?outs?\b"},
        {"id": "grid_failure", "topic": "power_grid", "pattern": r"^(?=.*\bpower grids?\b)(?=.*\bcollaps\w*)",
         "screen": r"\bpower grids?\b", "terms": r"\bpower grids?\b|\bcollaps\w*"},
        {"id": "internet_down", "topic": "internet_communications", "pattern": r"\binternet\b.{0,30}?\bgo(?:es)? down\b"},
        {"id": "flare_tech", "topic": "electronics_general", "pattern": r"^(?=.*\bsolar flares?\b)(?=.*\bsatellites?\b)",
         "screen": r"\bsolar flares?\b", "terms": r"\bsolar flares?\b|\bsatellites?\b"},
        {"id": "cyber_attack", "topic": "internet_communications", "pattern": r"\bcyber ?attacks?\b"}],
    "exclude": [
        {"id": "x_schumann", "mode": "unit", "scope": "all", "pattern": r"\bschumann\b"},
        {"id": "x_media", "mode": "overlap", "scope": ["blackout", "blackout_power"], "pattern": r"\bmedia black-?outs?\b"},
        {"id": "x_links", "mode": "unit", "scope": "all", "kinds": ["source"], "pattern": r"\bcontinue reading:"},
        {"id": "x_moon", "mode": "overlap", "scope": ["electronics_general"], "pattern": r"\bmoon satellites?\b"}],
}

TEXTS = {
    "transcripts_publisher/zed-quorn/pod-1111111111111111.txt":
        "The power grid will collapse next year, so stock up on candles. Quillon hour ends.",
    "transcripts_publisher/zed-quorn/web-2222222222222222.txt":
        "Quillon gardens rest. Rolling blackouts are coming to the valley. A media blackout hides the quillon news. "
        "Schumann resonance blackout today. Rolling blackouts are coming to the valley! The 2003 blackout was long. "
        "Continue Reading: Blackout in the valley",
    "transcripts_publisher/mira-vantelle/web-3333333333333333.txt":
        "A solar flare will hit the moon satellites. A solar flare could knock out satellites by 2030. "
        "The media blackout and the power blackout came together.",
    "transcripts_publisher/mira-vantelle/web-5555555555555555.txt":
        "Transcript March 3 2024 Notes on the valley blackout. The internet will go down in 2031. "
        "Blackouts have come every week since 2024.",
    "captions/zed-quorn/ZQ000000001.txt": "Mivvle lanterns glow. Satellites fail after a solar flare.",
}
MADE = {"transcripts/zed-quorn/pod-1111111111111111.json":
        {"segments": [{"start": 0.0, "text": "Welcome to the quillon hour."},
                      {"start": 4.0, "text": "The internet will go down in 2030."}]}}
CATALOG = [
    {"item_id": "ZQ000000001", "person_id": "zed-quorn", "lane": "youtube", "title": "Zorblax: prepare for a GLOBAL BLACKOUT",
     "captions_path": "captions/zed-quorn/ZQ000000001.txt"},
    {"item_id": "ZQ000000002", "person_id": "zed-quorn", "lane": "youtube", "title": "Zorblax: Schumann blackout chart"},
    {"item_id": "ZQ000000003", "person_id": "zed-quorn", "lane": "youtube",
     "title": "Zorblax on rolling blackouts in the quillon valley"},
    {"item_id": "pod-1111111111111111", "person_id": "zed-quorn", "lane": "pod", "title": "Quillon hour 12",
     "published": "2021-03-01", "publisher_text_path": "transcripts_publisher/zed-quorn/pod-1111111111111111.txt",
     "asr_path": "transcripts/zed-quorn/pod-1111111111111111.txt", "twin_of": "ZQ000000001", "twin_method": "title"},
    # the same title as its video, punctuated differently: read once, as the video's
    {"item_id": "pod-4444444444444444", "person_id": "zed-quorn", "lane": "pod",
     "title": "Zorblax - prepare for a global blackout!", "twin_of": "ZQ000000001", "twin_method": "title"},
    {"item_id": "web-2222222222222222", "person_id": "zed-quorn", "lane": "web", "title": "Continue Reading: Blackout notes",
     "published": "2020-05-05", "publisher_text_path": "transcripts_publisher/zed-quorn/web-2222222222222222.txt"},
    {"item_id": "web-3333333333333333", "person_id": "mira-vantelle", "lane": "web", "title": "Moon gardens",
     "published": "2022-01-01", "publisher_text_path": "transcripts_publisher/mira-vantelle/web-3333333333333333.txt"},
    {"item_id": "web-5555555555555555", "person_id": "mira-vantelle", "lane": "web", "title": "Valley notes",
     "publisher_text_path": "transcripts_publisher/mira-vantelle/web-5555555555555555.txt"},
]
QUEUE = [
    {"video_id": "ZQ000000001", "url": "https://www.youtube.com/watch?v=ZQ000000001", "channel_dir": "zed-quorn",
     "title": "Zorblax: prepare for a GLOBAL BLACKOUT", "duration_s": "600", "sources": "discover", "shard": "0",
     "tab": "videos", "listing_rank": "0", "upload_date_approx": "20261101"},
    {"video_id": "ZQ000000002", "url": "https://www.youtube.com/watch?v=ZQ000000002", "channel_dir": "zed-quorn",
     "title": "Zorblax: Schumann blackout chart", "duration_s": "300", "sources": "discover", "shard": "0",
     "tab": "videos", "listing_rank": "1", "upload_date_approx": "20261020"},
    {"video_id": "MV000000001", "url": "https://www.youtube.com/watch?v=MV000000001", "channel_dir": "mira-vantelle",
     "title": "Mira Vantelle, cyber attacks are coming", "duration_s": "", "entity": "Ossarine", "sources": "discover",
     "shard": "0", "tab": "videos", "listing_rank": "0", "upload_date_approx": "20261105"},
]
SECRET = ["Zorblax", "Quillon", "quillon", "Mivvle", "Rolling", "Vantelle,", "ZQ0000", "MV0000", "pod-1111", "web-2222",
          "web-3333", "web-5555", "gardens", "satellites", "GLOBAL", "Transcript"]


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_root(root):
    for rel, text in TEXTS.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    for rel, data in MADE.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(json.dumps(data), encoding="utf-8")
        (root / rel).with_suffix(".txt").write_text(" ".join(s["text"] for s in data["segments"]), encoding="utf-8")
    write_csv(root / "catalog" / "catalog.csv", CATALOG_FIELDS, CATALOG)
    write_csv(root / "jobs" / "queue_newest10.csv", QUEUE_FIELDS, QUEUE)
    # the same tier written another way: a byte-order mark, CRLF line ends, every field quoted
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=QUEUE_FIELDS, lineterminator="\r\n", quoting=csv.QUOTE_ALL)
    w.writeheader()
    w.writerows({k: r.get(k, "") for k in QUEUE_FIELDS} for r in QUEUE)
    (root / "jobs" / "queue_quoted.csv").write_bytes(("﻿" + buf.getvalue()).encode("utf-8"))
    (root / "theme.json").write_text(json.dumps(MINI), encoding="utf-8")
    (root / "plan").mkdir()


def run(*argv):
    with redirect_stdout(io.StringIO()):
        return ts.main([str(a) for a in argv])


def hits_of(root, scope, theme="darkzone"):
    return [r for f in sorted((root / "analysis" / "themes" / theme / scope).glob("*.jsonl"))
            for r in json.loads("[" + ",".join(f.read_text(encoding="utf-8").splitlines()) + "]")]


class TestTheme(unittest.TestCase):
    def setUp(self):
        self.theme = ts.Theme(MINI, "mini.json")

    def kept(self, text, kind="source"):
        return set(self.theme.evaluate(ts.norm(text, kind), kind)[0])

    def test_include_and_exclude_modes(self):
        self.assertEqual(self.kept("Rolling blackouts are coming."), {"blackout", "blackout_power"})
        self.assertEqual(self.kept("Schumann resonance blackout today."), set())             # unit, scope all
        self.assertEqual(self.kept("A media blackout hides it."), set())                     # overlap voids the match
        # overlap: the second blackout in the sentence is not the media blackout, so it stays
        self.assertEqual(self.kept("The media blackout and the power blackout came."), {"blackout", "blackout_power"})
        kept, voided = self.theme.evaluate("A media blackout hides it.", "source")
        self.assertEqual(voided, {"blackout": ["x_media"]})

    def test_lookahead_include_and_topic_scope(self):
        self.assertEqual(self.kept("Satellites fail after a solar flare."), {"flare_tech"})
        self.assertEqual(self.kept("A solar flare lights the moon satellites."), set())       # scope by topic, whole unit
        self.assertEqual(self.kept("The power grid shines."), set())
        unit = "The power grid will collapse soon."
        kept, _ = self.theme.evaluate(unit, "source")
        self.assertEqual(self.theme.terms(unit, kept), ["power grid", "collapse"])

    def test_exclude_kinds_and_titles(self):
        self.assertEqual(self.kept("Continue Reading: Blackout in the valley"), set())        # source
        self.assertEqual(self.kept("Continue Reading: Blackout in the valley", "title"), {"blackout"})
        self.assertEqual(ts.norm("Event_ the BLACKOUT", "title"), "Event the BLACKOUT")
        self.assertEqual(ts.norm("Event_ the BLACKOUT"), "Event_ the BLACKOUT")

    def test_generic_topics_and_screen(self):
        kept = self.theme.evaluate("Rolling blackouts are coming.", "source")[0]
        self.assertEqual(self.theme.hit_topics(kept), ["power_grid"])
        self.assertEqual(self.theme.hit_topics({"blackout": [(0, 1)]}), ["unspecified"])
        self.assertFalse(self.theme.candidate("Quillon gardens rest."))
        self.assertTrue(self.theme.candidate("The power grid shines."))
        opened = json.loads(json.dumps(MINI))
        del opened["include"][2]["screen"]
        self.assertIsNone(ts.Theme(opened).screen)     # a look-ahead include without a screen: every unit is tried
        bad = json.loads(json.dumps(MINI))
        bad["exclude"][1]["scope"] = ["no_such_include"]
        with self.assertRaises(ValueError):
            ts.Theme(bad)

    def test_quote_shows_the_terms_and_title_candidates(self):
        unit = " ".join(["word"] * 45) + " and then a solar flare will knock out the satellites by 2030."
        kept = self.theme.evaluate(unit, "source")[0]
        row = {"person_id": "zed-quorn", "item_id": "web-2222222222222222", "published": "2024-01-01"}
        rec = ts.make_hit(self.theme, "all", row, "source", 0, [(None, unit)], "2024-01-01", "published", 0, "", unit,
                          kept)
        self.assertIn("solar flare", rec["sentence"])                    # a look-ahead's terms, not its first words
        self.assertIn("satellites", rec["sentence"])
        self.assertLessEqual(len(rec["sentence"].replace("…", "").split()), 30)
        title = "2027 PREDICTIONS | Rolling blackouts are coming"
        kept = self.theme.evaluate(title, "title")[0]
        rec = ts.make_hit(self.theme, "all", row, "title", 0, [], "2026-11-01", "listing", 0, "", title, kept)
        self.assertTrue(rec["prediction_candidate"])                     # " | " in a title is not a link list
        self.assertEqual((rec["window_lo"], rec["past_window"]), (2027, False))

    def test_copies_ignore_punctuation(self):
        rows = [{"person_id": "p", "kind": "title", "_full": f, "date_said": "", "item_id": f"i{i}", "offset_s": None}
                for i, f in enumerate(("Event_Coming soon: the great blackout of the valley",
                                       "Event: Coming soon - the great blackout of the valley!"))]
        ts.collapse(rows)
        self.assertEqual([r["copy"] for r in rows], [False, True])
        self.assertEqual(ts.sentence_key(rows[0]["_full"]), ts.sentence_key(rows[1]["_full"]))
        self.assertEqual(ts.key_form("Event: Coming - soon!"), "event coming soon")

    def test_masker(self):
        hide = ts.masker("zed-quorn", ["Zorblax", "Ossa Rine"])
        self.assertEqual(hide("Zorblax said it; Zed Quorn and zed-quorn too; ossa-rine also."),
                         "[name] said it; [name] and [name] too; [name] also.")
        self.assertEqual(hide("Zorblaxian words stay"), "Zorblaxian words stay")             # whole words only
        self.assertEqual(ts.masker("orla-fenwick")("Cyber Attacks | Orla Fenwick"), "Cyber Attacks | [name]")


class TestThemeFiles(unittest.TestCase):
    """Every theme file in pipeline/themes: its includes match their invented examples, its excludes void theirs and
    leave their must-keep sentences as they are, and the file holds counts only (no item or video ids)."""

    def test_examples_and_keeps(self):
        files = sorted((PIPE / "themes").glob("*.json"))
        self.assertTrue(files)
        for path in files:
            data = json.loads(path.read_text(encoding="utf-8"))
            theme = ts.Theme(data, path)
            bare = ts.Theme(dict(data, exclude=[]), path)
            for inc in data["include"]:
                self.assertIn(inc["group"], ("strong", "weak"))
                self.assertTrue(inc.get("examples"), f"{path.name}: {inc['id']} has no examples")
                if ts.SLOW.search(inc["pattern"]):
                    self.assertTrue(inc.get("screen"), f"{path.name}: {inc['id']} needs a screen")
                for ex in inc["examples"]:
                    unit = ts.norm(ex)
                    self.assertTrue(theme.candidate(unit), f"{inc['id']}: screen misses {ex!r}")
                    self.assertIn(inc["id"], theme.evaluate(unit, "source")[0], f"{inc['id']}: {ex!r}")
                if "precision" in inc:
                    self.assertTrue(inc["precision"] is None or isinstance(inc["precision"], (int, float)))
            for exc in data["exclude"]:
                self.assertTrue(exc.get("examples"), f"{path.name}: {exc['id']} has no examples")
                kinds = exc.get("kinds") or ["source"]
                for ex in exc["examples"]:
                    unit = ts.norm(ex)
                    self.assertTrue(bare.evaluate(unit, kinds[0])[0], f"{exc['id']}: no include matches {ex!r}")
                    kept, voided = theme.evaluate(unit, kinds[0])
                    self.assertFalse(kept, f"{exc['id']}: {ex!r} keeps {kept}")
                    self.assertIn(exc["id"], {x for v in voided.values() for x in v})
                alone = ts.Theme(dict(data, exclude=[exc]), path)
                for ex in exc.get("keeps") or []:
                    unit = ts.norm(ex)
                    before = set(bare.evaluate(unit, kinds[0])[0])
                    self.assertTrue(before, f"{exc['id']}: no include matches the keep {ex!r}")
                    self.assertEqual(set(alone.evaluate(unit, kinds[0])[0]), before, f"{exc['id']} voids {ex!r}")
                    self.assertTrue(theme.evaluate(unit, kinds[0])[0], f"{ex!r} is no hit with the whole lexicon")
            # counts only in the repository: no item ids and nothing shaped like a YouTube video id
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"\b(?:web|pod|ia)-[0-9a-f]{16}\b", text))
            for token in re.findall(r"(?<![\w-])[A-Za-z0-9_-]{11}(?![\w-])", text):
                self.assertFalse(re.search(r"\d", token) and re.search(r"[A-Za-z]", token)
                                 and re.search(r"[A-Z]", token) and re.search(r"[a-z]", token),
                                 f"{path.name}: {token!r} looks like a video id")


class TestPublishedCounts(unittest.TestCase):
    """The published plan/theme_*.csv of the repository: digits and person ids only, every kind's "all" row."""

    def test_published_files(self):
        files = sorted(REAL_PLAN.glob("theme_*.csv"))
        for path in files:
            rows = read_rows(path)
            self.assertTrue(rows, path.name)
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"\b(?:web|pod|ia)-[0-9a-f]{16}\b", text))
            for r in rows:
                self.assertRegex(r["person_id"], r"^(?:all|[a-z0-9]+(?:-[a-z0-9]+)*)$", path.name)
                self.assertIn(r["kind"], ts.KINDS, path.name)
                self.assertRegex(r["scope"], r"^[a-z0-9_]+$", path.name)
                for k, v in r.items():
                    if k not in ("scope", "person_id", "kind"):
                        self.assertRegex(v or "", r"^\d*$", f"{path.name}: {k}={v!r}")
            self.assertEqual({r["kind"] for r in rows if r["person_id"] == "all"}, set(ts.KINDS), path.name)


class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        make_root(cls.root)
        cls.et_root = ts.ET_ROOT
        ts.ET_ROOT = cls.root                       # --publish-counts writes to <root>/plan in these tests
        run("search", "--root", cls.root, "--theme", cls.root / "theme.json", "--scope", "all", "--publish-counts",
            "--priority-from", "jobs/queue_newest10.csv")
        run("search", "--root", cls.root, "--theme", cls.root / "theme.json", "--scope", "newest10",
            "--queue", "jobs/queue_newest10.csv", "--publish-counts")
        run("search", "--root", cls.root, "--theme", cls.root / "theme.json", "--scope", "quoted",
            "--queue", "jobs/queue_quoted.csv")
        cls.all, cls.tier = hits_of(cls.root, "all"), hits_of(cls.root, "newest10")

    @classmethod
    def tearDownClass(cls):
        ts.ET_ROOT = cls.et_root
        cls.tmp.cleanup()

    def counts(self, scope):
        return read_rows(self.root / "analysis" / "themes" / "darkzone" / scope / "counts.csv")

    def test_hits_and_kinds_apart(self):
        kinds = {(r["item_id"], r["kind"]) for r in self.all}
        self.assertIn(("pod-1111111111111111", "source"), kinds)
        self.assertIn(("pod-1111111111111111", "made"), kinds)
        self.assertIn(("ZQ000000001", "captions"), kinds)
        self.assertIn(("ZQ000000001", "title"), kinds)
        self.assertNotIn(("ZQ000000002", "title"), kinds)                 # the Schumann chart
        self.assertNotIn(("pod-4444444444444444", "title"), kinds)        # its video's title, read once
        self.assertIn(("web-2222222222222222", "title"), kinds)           # the link-list exclude is for texts only
        web = [r for r in self.all if r["item_id"] == "web-2222222222222222" and r["kind"] == "source"]
        self.assertEqual(sorted(r["idx"] for r in web), [1, 4, 5])        # media, Schumann and link list left out
        made = next(r for r in self.all if r["kind"] == "made")
        self.assertEqual((made["offset_s"], made["includes"]), (4.0, ["internet_down"]))
        both = next(r for r in self.all if r["item_id"] == "web-3333333333333333" and r["idx"] == 2)
        self.assertEqual((both["includes"], both["topics"]), (["blackout", "blackout_power"], ["power_grid"]))
        c = {(r["person_id"], r["kind"]): r for r in self.counts("all")}
        self.assertEqual((c[("zed-quorn", "source")]["items_read"], c[("zed-quorn", "source")]["hits"],
                          c[("zed-quorn", "source")]["distinct"]), ("2", "4", "3"))
        self.assertEqual(c[("zed-quorn", "made")]["hits"], "1")
        self.assertEqual(c[("zed-quorn", "captions")]["hits"], "1")
        self.assertEqual((c[("zed-quorn", "title")]["items_read"], c[("zed-quorn", "title")]["hits"]), ("5", "3"))
        self.assertEqual(c[("all", "source")]["hits"], "9")
        self.assertEqual(c[("all", "captions")]["items_read"], "1")

    def test_copies_markers_and_windows(self):
        rolling = [r for r in self.all if r["item_id"] == "web-2222222222222222" and r["idx"] in (1, 4)]
        self.assertEqual(sorted(r["copy"] for r in rolling), [False, True])
        self.assertEqual(len({r["copy_group"] for r in rolling}), 1)
        grid = next(r for r in self.all if r["includes"] == ["grid_failure"])
        self.assertEqual((grid["date_said"], grid["window_lo"], grid["window_hi"], grid["past_window"]),
                         ("2021-03-01", 2022, 2022, False))
        self.assertEqual((grid["future"], grid["warning"], grid["terms"]),
                         (["will"], ["candles", "stock up"], ["power grid", "collapse"]))
        past = next(r for r in self.all if r["item_id"] == "web-2222222222222222" and r["idx"] == 5)
        self.assertEqual((past["window_lo"], past["past_window"], past["past_reason"]),
                         (2003, True, "before the year said"))
        self.assertEqual(ts.targets(past), [])
        c = {(r["person_id"], r["kind"]): r for r in self.counts("all")}
        self.assertEqual((c[("zed-quorn", "source")]["with_window"], c[("zed-quorn", "source")]["earliest_target"],
                          c[("zed-quorn", "source")]["warning_marked"]), ("1", "2022", "1"))
        self.assertEqual((c[("zed-quorn", "source")]["earliest_said"], c[("zed-quorn", "source")]["latest_said"]),
                         ("2020", "2021"))

    def test_opening_date_and_past_anchor(self):
        mine = {r["idx"]: r for r in self.all if r["item_id"] == "web-5555555555555555"}
        self.assertEqual(sorted(mine), [0, 1, 2])
        self.assertEqual({(r["date_said"], r["date_basis"]) for r in mine.values()},
                         {("2024-03-03", "date the text opens with")})
        self.assertEqual((mine[0]["window_lo"], mine[0]["past_reason"]), (2024, "date of the text"))
        self.assertEqual((mine[1]["window_lo"], mine[1]["past_window"]), (2031, False))
        self.assertEqual((mine[2]["window_lo"], mine[2]["past_reason"]), (2024, "past anchor"))   # "since 2024"
        c = {(r["person_id"], r["kind"]): r for r in self.counts("all")}
        self.assertEqual((c[("mira-vantelle", "source")]["with_window"], c[("mira-vantelle", "source")]["latest_target"]),
                         ("2", "2031"))
        self.assertEqual(ts.lead_date("← All notes Notes 4th of June 2019 Speaker: words"), ("2019-06-04", (18, 34)))
        self.assertEqual(ts.lead_date("We met in June 2019 and it was good"), ("", None))

    def test_dates_from(self):
        out = self.root / "dated"
        run("search", "--root", self.root, "--theme", self.root / "theme.json", "--scope", "all", "--out", out,
            "--dates-from", "jobs/queue_newest10.csv")
        title = [json.loads(x) for x in (out / "zed-quorn.jsonl").read_text().splitlines()]
        title = next(r for r in title if r["item_id"] == "ZQ000000001" and r["kind"] == "title")
        self.assertEqual((title["date_said"], title["date_basis"]), ("2026-11-01", "listing, approximate"))
        undated = next(r for r in self.all if r["item_id"] == "ZQ000000001" and r["kind"] == "title")
        self.assertEqual(undated["date_said"], "")

    def test_publish_refuses_partial_counts(self):
        for extra in (["--only", "zed-quorn"], ["--kinds", "source,title"]):
            with self.assertRaises(SystemExit):
                run("search", "--root", self.root, "--theme", self.root / "theme.json", "--scope", "all",
                    "--out", self.root / "partial", "--publish-counts", *extra)

    def test_quotes_are_cut(self):
        long = "word " * 50 + "a blackout is coming " + "word " * 50
        cut = ts.cut(long, at=long.index("blackout"))
        self.assertIn("blackout", cut)
        self.assertLessEqual(len(cut.replace("…", "").split()), 30)
        self.assertTrue(cut.startswith("… ") and cut.endswith(" …"))
        cut = ts.cut(long, at=[long.index("blackout"), long.index("coming")])
        self.assertIn("blackout is coming", cut)

    def test_tier_scope_twins_and_titles(self):
        self.assertEqual({r["item_id"] for r in self.tier},
                         {"pod-1111111111111111", "ZQ000000001", "MV000000001"})      # the other pages are not in it
        for r in self.tier:
            if r["item_id"] == "pod-1111111111111111":
                self.assertEqual(r["via_twin"], "ZQ000000001")
            else:
                self.assertEqual(r["via_twin"], "")
        cap = next(r for r in self.tier if r["kind"] == "captions")
        self.assertEqual((cap["date_said"], cap["date_basis"]), ("2026-11-01", "listing, approximate"))
        mv = next(r for r in self.tier if r["item_id"] == "MV000000001")               # a queued title not catalogued
        self.assertEqual((mv["person_id"], mv["kind"], mv["listing_rank"]), ("mira-vantelle", "title", "0"))
        titles = read_rows(self.root / "analysis/themes/darkzone/newest10/titles.csv")
        self.assertEqual([t["video_id"] for t in titles], ["ZQ000000001", "MV000000001"])
        self.assertEqual(titles[1]["topics"], "internet_communications")
        c = {(r["person_id"], r["kind"]): r for r in self.counts("newest10")}
        z = c[("zed-quorn", "title")]
        self.assertEqual(tuple(z[k] for k in ts.TIER_FIELDS), ("2", "1", "1", "1", "1", "1", "1", "1"))
        self.assertEqual(c[("zed-quorn", "source")]["videos_queued"], "")              # per person, on the title row
        self.assertEqual(c[("all", "title")]["titles_matching"], "2")
        self.assertEqual(c[("all", "captions")]["items_read"], "1")

    def test_priority_queue_copies_the_tier_lines(self):
        tier = (self.root / "jobs" / "queue_newest10.csv").read_text(encoding="utf-8").splitlines(keepends=True)
        prio = (self.root / "jobs" / "queue_darkzone_newest10.csv").read_text(encoding="utf-8").splitlines(keepends=True)
        self.assertEqual(prio, [tier[0], tier[1], tier[3]])                         # header and matching rows
        raw = (self.root / "jobs" / "queue_quoted.csv").read_bytes().split(b"\r\n")
        quoted = (self.root / "jobs" / "queue_darkzone_quoted.csv").read_bytes()
        self.assertEqual(quoted, b"\r\n".join([raw[0], raw[1], raw[3]]) + b"\r\n")   # BOM, CRLF, quotes kept
        rows = read_rows(self.root / "jobs" / "queue_darkzone_newest10.csv")
        self.assertEqual(rows[1]["title"], "Mira Vantelle, cyber attacks are coming")
        # scope all with --priority-from: the videos with a title or text hit (here ZQ000000001: title, twin, captions)
        allq = (self.root / "jobs" / "queue_darkzone_all.csv").read_text(encoding="utf-8").splitlines(keepends=True)
        self.assertEqual(allq, [tier[0], tier[1]])
        why = read_rows(self.root / "analysis/themes/darkzone/all/priority.csv")
        self.assertEqual((why[0]["video_id"], why[0]["title_hit"], why[0]["text_hits_source"], why[0]["text_hits_made"],
                          why[0]["text_hits_captions"]), ("ZQ000000001", "1", "1", "1", "1"))

    def test_published_counts_have_no_text(self):
        for name in ("theme_darkzone.csv", "theme_darkzone_newest10.csv"):
            text = (self.root / "plan" / name).read_text(encoding="utf-8")
            for word in SECRET:
                self.assertNotIn(word, text, f"{name} holds {word!r}")
            rows = list(csv.DictReader(io.StringIO(text)))
            for r in rows:
                for k, v in r.items():
                    if k not in ("scope", "person_id", "kind"):
                        self.assertRegex(v, r"^\d*$", f"{name}: {k}={v!r}")
            self.assertEqual({r["kind"] for r in rows if r["person_id"] == "all"}, set(ts.KINDS))
        self.assertIn("titles_matching", (self.root / "plan" / "theme_darkzone_newest10.csv").read_text().split("\n")[0])

    def test_sample_blinded_and_twins_ensured(self):
        out = self.root / "analysis" / "themes" / "darkzone" / "sample_a"
        run("sample", "--root", self.root, "--theme", self.root / "theme.json", "--from", "all", "--per-person", "2",
            "--out", out)
        first = (out / "sample.jsonl").read_text(encoding="utf-8")
        run("sample", "--root", self.root, "--theme", self.root / "theme.json", "--from", "all", "--per-person", "2",
            "--out", out)
        self.assertEqual(first, (out / "sample.jsonl").read_text(encoding="utf-8"))   # seeded
        blind = [json.loads(x) for x in first.splitlines()]
        key = [json.loads(x) for x in (out / "key.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(blind), 4)                                           # two people, two each
        for b in blind:
            self.assertEqual(set(b), {"uid", "sentence", "context", "matched_terms"})
        for word in ("zed-quorn", "mira-vantelle", "ZQ0000", "pod-1111", "web-2222", "web-3333", "2021", "2020-05"):
            self.assertNotIn(word, first)
        self.assertEqual([k["uid"] for k in key], [b["uid"] for b in blind])
        self.assertEqual({k["person_id"] for k in key}, {"zed-quorn", "mira-vantelle"})
        strata = json.loads((out / "strata.json").read_text())
        self.assertEqual(strata, {"mira-vantelle": 5, "zed-quorn": 8})            # distinct hits, copies once
        # no draw at all: every hit that came through a twin of a queued video is still added
        out2 = self.root / "analysis" / "themes" / "darkzone" / "sample_b"
        run("sample", "--root", self.root, "--theme", self.root / "theme.json", "--from", "all", "--per-person", "0",
            "--ensure-twins", "newest10", "--out", out2)
        meta = json.loads((out2 / "meta.json").read_text())
        self.assertEqual((meta["drawn"], meta["units"], meta["ensure_twins"]["newest10"]["added"]), (0, 2, 2))
        key2 = [json.loads(x) for x in (out2 / "key.jsonl").read_text().splitlines()]
        self.assertTrue(all(k["ensured"] == "twins:newest10" and k["via_twin"] == "ZQ000000001" for k in key2))
        # every hit of a tier, its titles too; the person's names in a unit are masked (the queue's entity too)
        out3 = self.root / "analysis" / "themes" / "darkzone" / "sample_d"
        run("sample", "--root", self.root, "--theme", self.root / "theme.json", "--from", "all", "--per-person", "0",
            "--ensure-twins", "newest10", "--ensure-scope", "newest10", "--out", out3)
        meta = json.loads((out3 / "meta.json").read_text())
        self.assertEqual((meta["units"], meta["ensure_scope"]["newest10"]["added"]), (5, 3))
        self.assertEqual(meta["ensure_scope"]["newest10"]["by_kind"], {"captions": 1, "made": 1, "source": 1, "title": 2})
        blind = (out3 / "sample.jsonl").read_text(encoding="utf-8")
        self.assertIn("[name], cyber attacks are coming", blind)
        self.assertNotIn("Vantelle", blind)
        self.assertEqual(ts.person_names(self.root)["mira-vantelle"], ["Ossarine"])

    def test_score(self):
        out = self.root / "analysis" / "themes" / "darkzone" / "sample_c"
        run("sample", "--root", self.root, "--theme", self.root / "theme.json", "--from", "all", "--per-person", "10",
            "--out", out)
        key = [json.loads(x) for x in (out / "key.jsonl").read_text().splitlines()]
        a, b = [], []
        for i, k in enumerate(key):
            a.append({"uid": k["uid"], "on_topic": "yes", "type": "prediction" if i % 2 else "warning"})
            b.append({"uid": k["uid"], "on_topic": "yes" if i % 3 else "no", "type": "prediction" if i % 2 else "warning"})
        b[-1] = {"uid": key[-1]["uid"], "on_topic": "yes", "type": "guess"}        # not a type: left out
        for name, rows in (("labels_a.jsonl", a), ("labels_b.jsonl", b)):
            (out / name).write_text("".join(json.dumps(r) + "\n" for r in rows))
        res = run("score", "--out", out, out / "labels_a.jsonl", out / "labels_b.jsonl")
        n = len(key) - 1
        self.assertEqual(res["invalid_type"], [key[-1]["uid"]])
        self.assertEqual(res["units"], n)
        on_b = [i % 3 != 0 for i in range(n)]
        self.assertEqual(res["all"]["both_on"], sum(on_b))
        self.assertEqual(res["on_topic_kappa_binary"], pp.kappa([True] * n, on_b))
        both = [i for i in range(n) if on_b[i]]
        self.assertEqual(res["all"]["both_on_prediction_like"], len(both))        # warnings are prediction-like
        self.assertEqual(res["all"]["both_on_warning"], sum(i % 2 == 0 for i in both))
        self.assertEqual(res["on_share_wilson95"], pp.wilson(sum(on_b), n))
        self.assertIn("power_grid", res["by_topic"])
        self.assertIsNotNone(res["weighted_on_share"])
        self.assertTrue((out / "score.json").exists())

    def test_measure(self):
        grid = next(r for r in self.all if r["includes"] == ["grid_failure"])
        labels = self.root / "labels.csv"
        write_csv(labels, ["item_id", "kind", "idx", "key", "label"], [
            {"item_id": "web-3333333333333333", "kind": "source", "idx": 0, "label": "off"},   # voided by x_moon
            {"item_id": "web-3333333333333333", "kind": "source", "idx": 1, "label": "on"},
            {"item_id": "web-3333333333333333", "kind": "source", "idx": 2, "label": "on"},
            {"item_id": "web-2222222222222222", "kind": "source", "idx": 5, "label": "off"},
            {"item_id": "ZQ000000003", "kind": "title_youtube", "idx": 0, "label": "on"},
            {"item_id": "ZQ000000003", "kind": "title_youtube", "idx": 0, "label": "edge"},
            {"item_id": "", "kind": "", "idx": "", "key": grid["key"], "label": "on"},          # hash only: a hit
            {"item_id": "", "kind": "", "idx": "", "key": "0123456789abcdef", "label": "on"}])  # hash only: no hit
        theme = self.root / "theme_copy.json"
        theme.write_text(json.dumps(MINI), encoding="utf-8")
        out = self.root / "analysis" / "themes" / "darkzone" / "sample_m"
        run("sample", "--root", self.root, "--theme", self.root / "theme.json", "--from", "all", "--per-person", "10",
            "--out", out)
        key = [json.loads(x) for x in (out / "key.jsonl").read_text().splitlines()]
        for name in ("labels_a.jsonl", "labels_b.jsonl"):
            (out / name).write_text("".join(json.dumps({"uid": k["uid"], "on_topic": "yes", "type": "prediction"}) + "\n"
                                            for k in key))
        inc, exc, summary = run("measure", "--root", self.root, "--theme", theme, "--scope", "all", "--labels", labels,
                                "--coded", out, "--write-lexicon")
        flare = inc["flare_tech"]["by_kind"]
        self.assertEqual((flare["source"]["read"], flare["source"]["precision"], flare["source"]["distinct"]), (1, 1.0, 1))
        self.assertEqual((flare["captions"]["read"], flare["captions"]["distinct"]), (0, 1))
        self.assertEqual(inc["flare_tech"]["precision"], 1.0)                 # the lowest kind with a read
        black = inc["blackout"]["by_kind"]
        self.assertEqual((black["source"]["read"], black["source"]["on"], black["title"]["read"], black["title"]["edge"]),
                         (2, 1, 1, 1))                                       # kinds apart, never pooled
        self.assertEqual(inc["blackout"]["precision"], 0.0)
        self.assertEqual(inc["grid_failure"]["by_kind"]["source"]["on"], 1)  # the hash-only label, joined
        self.assertEqual(exc["x_moon"]["by_kind"]["source"]["voided_read"], 1)
        self.assertEqual((summary["labels_not_hits"], summary["on_labels_not_hits"]), ({"on": 1}, 1))
        self.assertEqual(summary["by_kind"]["source"]["labelled_units"], 5)
        self.assertEqual(summary["coded"]["by_kind"]["source"]["units"],
                         sum(k["kind"] == "source" for k in key))
        self.assertEqual(inc["grid_failure"]["coded"]["source"]["precision"], 1.0)
        written = json.loads(theme.read_text(encoding="utf-8"))
        self.assertEqual(written["include"][4]["precision"], 1.0)
        self.assertEqual(written["exclude"][3]["measured"]["by_kind"]["source"]["voided_read"], 1)

    def test_leaks(self):
        data = json.loads(json.dumps(MINI))
        data["include"][1]["examples"] = ["Rolling blackouts are coming to the valley again."]   # 7 stored words
        path = self.root / "leaky.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(ts.main(["leaks", "--root", str(self.root), "--theme", str(path)]), 1)
        self.assertIn("LEAK blackout_power:examples: longest shared run 7", printed.getvalue())
        self.assertNotIn("Rolling", printed.getvalue())                       # counts and ids only
        data["include"][1]["examples"] = ["Tall lanterns were dark in every orchard."]
        data["include"][1]["notes"] = "seen in ZQ000000002"
        path.write_text(json.dumps(data), encoding="utf-8")
        with redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(ts.main(["leaks", "--root", str(self.root), "--theme", str(path)]), 1)
        self.assertIn("ID", printed.getvalue())
        del data["include"][1]["notes"]
        path.write_text(json.dumps(data), encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(ts.main(["leaks", "--root", str(self.root), "--theme", str(path)]), 0)


if __name__ == "__main__":
    unittest.main()
