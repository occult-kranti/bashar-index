#!/usr/bin/env python3
"""Tests for pipeline/prediction_page.py with invented candidates and an invented catalogue: the guard (a 31-word
quote, a 6% item share, a private path, a questioner pattern, an audio link, an unknown-length item), copies kept
once, the sort order, the public-address rules, the share budget, the counts table without text, the page
parsing as HTML with every quote present once, and the contract of the interactive page (one external script, no
innerHTML or storage, dark-token parity, the hash grammar round-tripped in node when node is present, the CSV
columns, the legend, the table, the no-d3 fallback and the narrow-screen CSS).

    python3 -I -m unittest discover -s et-channelers/pipeline/tests -p test_prediction_page.py -v
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

PIPE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPE))
import prediction_page as pp  # noqa: E402

CAT_FIELDS = ["item_id", "person_id", "lane", "relation", "title", "published", "publisher_text_words", "captions_words",
              "asr_words", "publisher_text_path", "asr_path", "captions_path", "audio_path", "twin_of", "source_host",
              "source_url"]
WORDS_40 = " ".join(f"w{i}" for i in range(40))      # an invented 40-word "sentence" with no English in it
LONG_PAGE = ("The quorvel lanterns will drift above the tessaline harbour in 2031 and every keeper shall watch them "
             "turn before the tide of that year comes in, so the council says.")  # 30 words


def cat_row(item_id, person="zed-quorn", lane="web", relation="page", words="2000", url="https://example.org/post/one",
            twin="", **more):
    row = {k: "" for k in CAT_FIELDS}
    row.update({"item_id": item_id, "person_id": person, "lane": lane, "relation": relation, "title": "a post",
                "published": "2024-03-05", "publisher_text_words": words, "source_url": url, "twin_of": twin,
                "source_host": pp.host_of(url)})
    row.update(more)
    return row


def cand(item_id, sentence, person="zed-quorn", lo=2031, hi=2031, kind="source", date="2024-03-05", basis="published",
         offset=None, copy=False, **more):
    row = {"person_id": person, "item_id": item_id, "kind": kind, "title": "a post", "date_said": date, "date_basis": basis,
           "offset_s": offset, "sentence": sentence, "markers": ["will"], "time_expr": str(lo or hi), "time_rule": "year",
           "window_lo": lo, "window_hi": hi, "conditional": False, "hedged": False, "strong": False, "copy_group": 0,
           "copy": copy}
    row.update(more)
    return row


PEOPLE = {"zed-quorn": {"person_id": "zed-quorn", "person_name": "Zed Quorn", "role": "channeler"},
          "mira-vantelle": {"person_id": "mira-vantelle", "person_name": "Mira Vantelle", "role": "channeler"},
          "tov-arlen": {"person_id": "tov-arlen", "person_name": "Tov Arlen", "role": "channeler"}}


class Root:
    """An invented private root: catalog/catalog.csv, analysis/predictions/<person>.jsonl, plan/targets.csv."""

    def __init__(self, catalogue, candidates):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "private"
        (self.root / "catalog").mkdir(parents=True)
        (self.root / "analysis" / "predictions").mkdir(parents=True)
        with open(self.root / "catalog" / "catalog.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAT_FIELDS)
            w.writeheader()
            w.writerows(catalogue)
        by_person = {}
        for c in candidates:
            by_person.setdefault(c["person_id"], []).append(c)
        for person, rows in by_person.items():
            (self.root / "analysis" / "predictions" / f"{person}.jsonl").write_text(
                "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        self.targets = Path(self.tmp.name) / "targets.csv"
        with open(self.targets, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["person_id", "person_name", "role"])
            w.writeheader()
            w.writerows(PEOPLE.values())
        self.out = Path(self.tmp.name) / "out" / "predictions.html"

    def build(self):
        return pp.build(self.root, self.out, self.targets)

    def cleanup(self):
        self.tmp.cleanup()


def records_and_page(catalogue, candidates):
    cat = {r["item_id"]: r for r in catalogue}
    records, _ = pp.build_records(candidates, cat, PEOPLE)
    page = pp.render_page(records, "", "2026-11-16T00:00:00Z")
    return records, page, cat


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = [cat_row("web-1111111111111111")]
        self.candidates = [cand("web-1111111111111111", LONG_PAGE)]

    def test_clean_fixture_passes(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        report = pp.guard(records, cat, page, self.candidates, PEOPLE)
        self.assertEqual(report["records"], 1)
        self.assertEqual(report["quotes"], 1)

    def test_31_word_quote_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        records[0]["quote"] = LONG_PAGE + " again"
        records[0]["quote_words"] = 31
        with self.assertRaisesRegex(pp.GuardError, "over 30 words"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)

    def test_31_words_of_a_sentence_anywhere_on_the_page_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        private = self.candidates + [cand("web-1111111111111111", WORDS_40, lo=None, hi=None)]
        page = page.replace("<h1>", f"<h1>{WORDS_40}</h1><h1>")
        with self.assertRaisesRegex(pp.GuardError, "consecutive words"):
            pp.guard(records, cat, page, private, PEOPLE)

    def test_6_percent_share_refused(self):
        # a 100-word item with a 6-word quote is 6%: the builder would cut it to 5 (then withhold); the guard refuses it
        catalogue = [cat_row("web-1111111111111111", words="100")]
        records, page, cat = records_and_page(catalogue, self.candidates)
        records[0]["quote"] = " ".join(LONG_PAGE.split()[:6])
        records[0]["quote_words"] = 6
        with self.assertRaisesRegex(pp.GuardError, "item share over 5%"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)

    def test_private_path_in_a_title_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        bad = page.replace("<title>Prediction timelines</title>", "<title>/workspaces/private/x</title>")
        with self.assertRaisesRegex(pp.GuardError, "private path"):
            pp.guard(records, cat, bad, self.candidates, PEOPLE)
        bad = page.replace("<title>Prediction timelines</title>", "<title>see transcripts/zed/web-1.txt</title>")
        with self.assertRaisesRegex(pp.GuardError, "private path"):
            pp.guard(records, cat, bad, self.candidates, PEOPLE)

    def test_catalogue_path_value_refused(self):
        catalogue = [cat_row("web-1111111111111111", publisher_text_path="texts/zed-quorn/one.md")]
        records, page, cat = records_and_page(catalogue, self.candidates)
        bad = page.replace("<h1>", "<h1>texts/zed-quorn/one.md ")
        with self.assertRaisesRegex(pp.GuardError, "private path"):
            pp.guard(records, cat, bad, self.candidates, PEOPLE)

    def test_record_key_outside_allow_list_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        records[0]["sentence"] = "x"
        with self.assertRaisesRegex(pp.GuardError, "allow-list"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)

    def test_questioner_pattern_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        records[0]["quote"] = "Questioner: Mary will see the lanterns in 2031"
        with self.assertRaisesRegex(pp.GuardError, "speaker prefix"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)
        records[0]["quote"] = "Robert: the lanterns will drift in 2031"
        with self.assertRaisesRegex(pp.GuardError, "speaker prefix"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)
        records[0]["quote"] = "write to zed@example.org before 2031"
        with self.assertRaisesRegex(pp.GuardError, "speaker prefix"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)
        # L/L Research style: a bare "Questioner" opener with no punctuation, an all-caps name, a two-word name
        for opener in ("Questioner Since 2031 is coming soon, I want to ask about the lanterns",
                       "JIM: the lanterns will drift in 2031", "Mary Ann: the lanterns will drift in 2031"):
            records[0]["quote"] = opener
            with self.assertRaisesRegex(pp.GuardError, "speaker prefix"):
                pp.guard(records, cat, page, self.candidates, PEOPLE)

    def test_bare_questioner_on_the_page_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        page = page.replace("<h1>", "<h1>Questioner Since 2031 is coming ")
        with self.assertRaisesRegex(pp.GuardError, "speaker prefix"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)

    def test_listed_questioner_name_refused_and_withheld_by_builder(self):
        private = [cand("web-1111111111111111", "Orlabeth will see the quorvel lanterns drift above the harbour in 2031.")]
        records, page, cat = records_and_page(self.catalogue, private)
        with self.assertRaisesRegex(pp.GuardError, "speaker prefix"):
            pp.guard(records, cat, page, private, PEOPLE, questioners=["Orlabeth"])
        records, notes = pp.build_records(private, cat, PEOPLE, questioners=["Orlabeth"])
        self.assertIsNone(records[0]["quote"])
        self.assertEqual(notes["withheld"][0]["why"], "named questioner")

    def test_mp3_link_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        for link in ("https://example.org/ep.mp3", "http://example.org/post/one", "https://dts.podtrac.com/redirect/x",
                     "https://d3ctxlq1ktw2nl.cloudfront.net/a/b", "https://example.org/feed.xml"):
            records[0]["link"] = link
            with self.assertRaisesRegex(pp.GuardError, "not a public https page"):
                pp.guard(records, cat, page, self.candidates, PEOPLE)

    def test_unknown_length_refused_unless_no_quote(self):
        catalogue = [cat_row("web-1111111111111111", words="")]
        records, page, cat = records_and_page(catalogue, self.candidates)
        self.assertIsNone(records[0]["quote"])                                  # the builder withheld it
        pp.guard(records, cat, page, self.candidates, PEOPLE)                   # and the guard accepts that
        records[0]["quote"] = " ".join(LONG_PAGE.split()[:8])
        records[0]["quote_words"] = 8
        with self.assertRaisesRegex(pp.GuardError, "unknown length"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)

    def test_paraphrase_and_count_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        records[0]["quote"] = "The quorvel lanterns might drift above the harbour"
        with self.assertRaisesRegex(pp.GuardError, "word-for-word prefix"):
            pp.guard(records, cat, page, self.candidates, PEOPLE)
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        with self.assertRaisesRegex(pp.GuardError, "records for 2 windowed"):
            pp.guard(records, cat, page, self.candidates + [cand("web-1111111111111111", "Lanterns in 2032.", lo=2032, hi=2032)], PEOPLE)

    def test_media_and_five_word_leak_refused(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        with self.assertRaisesRegex(pp.GuardError, "embeds media"):
            pp.guard(records, cat, page.replace("<h1>", '<audio src="https://example.org/a"></audio><h1>'), self.candidates, PEOPLE)
        private = self.candidates + [cand("web-1111111111111111", "Keepers of the tessaline harbour sleep.", lo=None, hi=None)]
        leak = page.replace("<h1>", "<h1>keepers of the tessaline harbour ")
        with self.assertRaisesRegex(pp.GuardError, "five-word run"):
            pp.guard(records, cat, leak, private, PEOPLE)

    def test_per_person_cap(self):
        records, page, cat = records_and_page(self.catalogue, self.candidates)
        with self.assertRaisesRegex(pp.GuardError, "per-person cap"):
            pp.guard(records, cat, page, self.candidates, PEOPLE, cap=10)


class BuilderTests(unittest.TestCase):
    def test_copies_kept_once_and_no_window_left_out(self):
        catalogue = [cat_row("web-1111111111111111"), cat_row("web-2222222222222222", url="https://example.org/post/two")]
        private = [cand("web-1111111111111111", LONG_PAGE),
                   cand("web-2222222222222222", LONG_PAGE, copy=True, copy_group=0),
                   cand("web-2222222222222222", "Soon the lanterns will drift.", lo=None, hi=None)]
        records, _ = pp.build_records(private, {r["item_id"]: r for r in catalogue}, PEOPLE)
        self.assertEqual([r["item_id"] for r in records], ["web-1111111111111111"])

    def test_sort_order_and_person_order(self):
        catalogue = [cat_row("web-1111111111111111"), cat_row("web-2222222222222222", person="mira-vantelle"),
                     cat_row("pod-3333333333333333", person="mira-vantelle", lane="pod", relation="own",
                             url="https://example.org/ep/3.mp3", twin="abcdefghijk", words="", asr_words="5000")]
        private = [cand("web-1111111111111111", "Quorn one in 2040.", lo=2040, hi=2040),
                   cand("web-2222222222222222", "Vantelle a by 2030.", person="mira-vantelle", lo=None, hi=2030),
                   cand("web-2222222222222222", "Vantelle b from 2025 to 2035.", person="mira-vantelle", lo=2025, hi=2035, date=""),
                   cand("pod-3333333333333333", "Vantelle c in 2025 at nine.", person="mira-vantelle", lo=2025, hi=2025, kind="made",
                        offset=9.0, date="2023-01-01"),
                   cand("pod-3333333333333333", "Vantelle d in 2025 at four.", person="mira-vantelle", lo=2025, hi=2025, kind="made",
                        offset=4.0, date="2023-01-01")]
        records, _ = pp.build_records(private, {r["item_id"]: r for r in catalogue}, PEOPLE)
        self.assertEqual([r["person_id"] for r in records], ["mira-vantelle"] * 4 + ["zed-quorn"])   # most statements first
        self.assertEqual([r["quote"][:10] for r in records[:4]],
                         ["Vantelle d", "Vantelle c", "Vantelle b", "Vantelle a"])    # by lo (or hi), hi, date, item, offset
        self.assertEqual([pp.window_label(r) for r in records], ["2025", "2025", "2025 to 2035", "by 2030", "2040"])
        self.assertEqual(records[0]["offset_s"], 4.0)
        self.assertEqual(records[0]["date_precision"], "day")
        self.assertEqual(records[2]["date_precision"], "unknown")
        self.assertTrue(records[2]["span"])
        self.assertEqual(sorted(records[0]), sorted(pp.PUBLIC_KEYS))

    def test_public_address_rules(self):
        self.assertEqual(pp.public_link(cat_row("w", url="https://example.org/post/one")), ("https://example.org/post/one", "page"))
        self.assertEqual(pp.public_link(cat_row("w", lane="pod", relation="own", url="https://example.org/ep/1.mp3", twin="abcdefghijk")),
                         ("https://www.youtube.com/watch?v=abcdefghijk", "episode page"))
        self.assertEqual(pp.public_link(cat_row("w", lane="pod", relation="host", url="https://dts.podtrac.com/redirect.mp3/x/y.mp3")),
                         (None, None))
        self.assertEqual(pp.public_link(cat_row("w", lane="pod", url="https://www.buzzsprout.com/1/episodes/2-title.mp3")), (None, None))
        self.assertEqual(pp.public_link(cat_row("w", lane="pod", url="https://www.buzzsprout.com/1/episodes/2-title")),
                         ("https://www.buzzsprout.com/1/episodes/2-title", "episode page"))
        self.assertEqual(pp.public_link(cat_row("w", lane="ia", relation="archive", url="https://archive.org/download/item-1/File%20A.mp3")),
                         ("https://archive.org/details/item-1", "episode page"))
        self.assertEqual(pp.public_link(cat_row("w", url="http://example.org/post/one")), (None, None))
        self.assertEqual(pp.public_link(cat_row("w", url="")), (None, None))
        self.assertFalse(pp.public_address_ok("https://media.blubrry.com/x/y"))
        self.assertFalse(pp.public_address_ok("https://api.spreaker.com/x"))

    def test_share_budget(self):
        # a 166-word page: budget 8 words; the first statement gets 8 with an ellipsis, the second none
        catalogue = [cat_row("web-1111111111111111", words="166")]
        private = [cand("web-1111111111111111", LONG_PAGE), cand("web-1111111111111111", "Keepers watch the tide in 2032 again.", lo=2032, hi=2032)]
        records, notes = pp.build_records(private, {r["item_id"]: r for r in catalogue}, PEOPLE)
        self.assertEqual(records[0]["quote"], "The quorvel lanterns will drift above the tessaline …")
        self.assertEqual(records[0]["quote_words"], 8)
        self.assertIsNone(records[1]["quote"])
        self.assertEqual(notes["withheld"][0]["why"], "item share")
        # a long item: eight statements of 30 words each fit within 5% of 5,000 words
        catalogue = [cat_row("web-1111111111111111", words="5000")]
        private = [cand("web-1111111111111111", LONG_PAGE.replace("2031", str(2031 + i)), lo=2031 + i, hi=2031 + i) for i in range(8)]
        records, notes = pp.build_records(private, {r["item_id"]: r for r in catalogue}, PEOPLE)
        self.assertEqual(sum(r["quote_words"] for r in records), 240)
        self.assertEqual(notes["withheld"], [])

    def test_speaker_turn_withheld_by_builder(self):
        catalogue = [cat_row("web-1111111111111111")]
        private = [cand("web-1111111111111111", "Jim: will the lanterns drift above the harbour in 2031?"),
                   cand("web-1111111111111111", "Zed: the lanterns will drift above the harbour in 2032.", lo=2032, hi=2032),
                   cand("web-1111111111111111", "Questioner I would like to ask about the lanterns in 2033.", lo=2033, hi=2033),
                   cand("web-1111111111111111", "ZED: the lanterns will drift above the harbour in 2034.", lo=2034, hi=2034),
                   cand("web-1111111111111111", "Mary Ann: the lanterns will drift above the harbour in 2035.", lo=2035, hi=2035)]
        records, notes = pp.build_records(private, {r["item_id"]: r for r in catalogue}, PEOPLE)
        self.assertIsNone(records[0]["quote"])
        self.assertEqual(notes["withheld"][0]["turn"], "Jim:")
        self.assertTrue(records[1]["quote"].startswith("Zed:"))     # a tracked person's own turn stays
        self.assertIsNone(records[2]["quote"])                      # a bare "Questioner" opener
        self.assertEqual(notes["withheld"][1]["turn"], "Questioner")
        self.assertTrue(records[3]["quote"].startswith("ZED:"))     # the person's own name in capitals stays
        self.assertIsNone(records[4]["quote"])                      # a two-word name
        self.assertEqual(notes["withheld"][2]["turn"], "Mary Ann:")

    def test_share_denominator_follows_the_kind(self):
        """A speech-to-text quote is measured against the transcript's words, not the show notes'."""
        cat = cat_row("pod-3333333333333333", lane="pod", relation="host", url="https://example.org/episode/3",
                      words="4000", asr_words="400", captions_words="")
        self.assertEqual(pp.item_words(cat), 4000)
        self.assertEqual(pp.item_words(cat, {"made"}), 400)
        self.assertEqual(pp.item_words(cat, {"made", "source"}), 400)
        private = [cand("pod-3333333333333333", LONG_PAGE, kind="made", offset=5.0)]
        records, _ = pp.build_records(private, {cat["item_id"]: cat}, PEOPLE)
        self.assertEqual(records[0]["quote_words"], 20)              # 5% of 400, not 30
        page = pp.render_page(records, "", "2026-11-16T00:00:00Z")
        pp.guard(records, {cat["item_id"]: cat}, page, private, PEOPLE)
        records[0]["quote"] = pp.quote(LONG_PAGE, 30)
        records[0]["quote_words"] = 30
        with self.assertRaisesRegex(pp.GuardError, "item share"):
            pp.guard(records, {cat["item_id"]: cat}, pp.render_page(records, "", "2026-11-16T00:00:00Z"), private, PEOPLE)

    def test_per_person_cap_in_builder(self):
        catalogue = [cat_row("web-1111111111111111", words="5000")]
        private = [cand("web-1111111111111111", LONG_PAGE.replace("2031", str(2031 + i)), lo=2031 + i, hi=2031 + i) for i in range(3)]
        records, notes = pp.build_records(private, {r["item_id"]: r for r in catalogue}, PEOPLE, cap=70)
        self.assertEqual([r["quote_words"] for r in records], [30, 30, 0])
        self.assertEqual(notes["withheld"][0]["why"], "person cap")


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self.skip, self.tags = [], 0, []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == "script":
            self.skip += 1

    def handle_endtag(self, tag):
        if tag == "script":
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.text.append(data)


class WholeBuildTests(unittest.TestCase):
    def setUp(self):
        catalogue = [cat_row("web-1111111111111111"), cat_row("web-2222222222222222", person="mira-vantelle", url="https://example.org/post/two"),
                     cat_row("pod-3333333333333333", person="mira-vantelle", lane="pod", relation="host",
                             url="https://dts.podtrac.com/redirect.mp3/x/ep.mp3", words="", asr_words="4000", asr_path="transcripts/m/pod-3333333333333333.txt",
                             audio_path="audio/m/pod-3333333333333333.opus")]
        private = [cand("web-1111111111111111", LONG_PAGE),
                   cand("web-1111111111111111", LONG_PAGE, copy=True),
                   cand("web-1111111111111111", "Soon the lanterns will drift.", lo=None, hi=None),
                   cand("web-2222222222222222", "Vantelle says the harbour wall will stand until 2030 at least.", person="mira-vantelle",
                        lo=None, hi=2030, conditional=True, hedged=True, date="2014-07", basis="source address"),
                   cand("pod-3333333333333333", "Vantelle on tape says the keepers leave between 2025 and 2035 for good.", person="mira-vantelle",
                        lo=2025, hi=2035, kind="made", offset=69.0, strong=True),
                   # a person with a candidate but no target window: counted in the totals, no section on the page
                   cand("web-4444444444444444", "Arlen says the lanterns will drift again one day.", person="tov-arlen", lo=None, hi=None)]
        catalogue.append(cat_row("web-4444444444444444", person="tov-arlen", url="https://example.org/post/four"))
        self.root = Root(catalogue, private)
        self.records, self.report = self.root.build()
        self.page = self.root.out.read_text(encoding="utf-8")

    def tearDown(self):
        self.root.cleanup()

    def test_page_written_and_report_private(self):
        self.assertEqual(self.report["records"], 3)
        self.assertTrue((self.root.root / "analysis" / "predictions" / "public_page_report.md").exists())
        self.assertTrue((self.root.root / "analysis" / "predictions" / "public_page_counts.csv").exists())
        self.assertIn("Generated 20", self.page)
        self.assertIn("from 3 items", self.page)
        self.assertNotIn("transcripts/m/", self.page)
        self.assertNotIn("dts.podtrac.com", self.page)
        self.assertIn("at 1:09 of the recording, no public page known", self.page)
        self.assertIn('<script type="application/json" id="data">', self.page)
        self.assertIn("by 2030", self.page)
        self.assertIn("2025 to 2035", self.page)
        self.assertIn("said 2014-07 (from address)", self.page)

    def test_page_parses_as_html_with_every_quote_once(self):
        p = _Text()
        p.feed(self.page)
        text = " ".join(p.text)
        self.assertEqual(p.tags[0], "html")
        for r in self.records:
            if r["quote"]:
                self.assertEqual(text.count(r["quote"]), 1, r["quote"])
        data = json.loads(self.page.split('<script type="application/json" id="data">')[1].split("</script>")[0].replace("<\\/", "</"))
        self.assertEqual(len(data), 3)
        self.assertEqual(sorted(data[0]), sorted(pp.PUBLIC_KEYS))

    def test_counts_csv_without_text(self):
        with open(self.root.root / "analysis" / "predictions" / "public_page_counts.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r["person_id"] for r in rows], ["mira-vantelle", "zed-quorn", "tov-arlen"])
        self.assertEqual(rows[0]["with_window"], "2")
        self.assertEqual(rows[1]["statements"], "2")          # distinct candidates, the copy not counted
        self.assertEqual(rows[1]["with_window"], "1")
        self.assertEqual((rows[2]["statements"], rows[2]["with_window"], rows[2]["earliest_target"]), ("1", "0", ""))
        self.assertEqual(sum(int(r["statements"]) for r in rows), 5)
        self.assertIn("5 distinct candidates in all over 3 people, 3 of them with a target window", self.page)
        self.assertNotIn("Tov Arlen</h2>", self.page)         # no section for a person with nothing windowed
        self.assertEqual(rows[0]["speech_to_text"], "1")
        self.assertEqual(rows[0]["earliest_target"], "2025")
        self.assertEqual(rows[0]["latest_target"], "2035")
        for col in rows[0]:
            self.assertNotIn(col, ("sentence", "quote", "title", "time_expr", "path"))
        text = (self.root.root / "analysis" / "predictions" / "public_page_counts.csv").read_text(encoding="utf-8")
        self.assertNotIn("lanterns", text)

    def test_guard_failure_writes_nothing(self):
        catalogue = [cat_row("web-1111111111111111", words="100")]
        private = [cand("web-1111111111111111", LONG_PAGE)]
        root = Root(catalogue, private)
        try:
            # 5% of 100 words is 5: under the floor, so withheld, and the build passes; force a breach through the cap
            with self.assertRaises(pp.GuardError):
                pp.build(root.root, root.out, root.targets, cap=-1)
            self.assertFalse(root.out.exists())
        finally:
            root.cleanup()


class PageContractTests(unittest.TestCase):
    """The redesigned page: one external script (d3), no innerHTML or storage in the JS, the token parity of the dark
    blocks, the hash grammar (round-tripped in node when node is on the PATH), the CSV columns, the legend, the table,
    the no-d3 fallback markup and the narrow-screen CSS. Invented data throughout."""

    @classmethod
    def setUpClass(cls):
        catalogue = [cat_row("web-1111111111111111"), cat_row("web-2222222222222222", person="mira-vantelle", url="https://example.org/post/two"),
                     cat_row("pod-3333333333333333", person="mira-vantelle", lane="pod", relation="host",
                             url="https://dts.podtrac.com/redirect.mp3/x/ep.mp3", words="", asr_words="4000")]
        cls.private = [cand("web-1111111111111111", LONG_PAGE),
                       cand("web-2222222222222222", "Vantelle says the harbour wall will stand until 2030 at least.", person="mira-vantelle",
                            lo=None, hi=2030, conditional=True, hedged=True, date="2014-07", basis="source address"),
                       cand("pod-3333333333333333", "Vantelle on tape says the keepers leave between 2025 and 2035 for good.", person="mira-vantelle",
                            lo=2025, hi=2035, kind="made", offset=69.0, strong=True, date="")]
        cls.records, cls.page, cls.cat = records_and_page(catalogue, cls.private)
        cls.js = pp.JS.replace("__AXIS_END__", str(pp.AXIS_END)).replace("__BUILD_YEAR__", str(pp.BUILD_YEAR)).replace(
            "__CARDS_SHOWN__", str(pp.CARDS_SHOWN)).replace("__NOW__", "2026.87").replace("__PUBLIC_KEYS__", json.dumps(pp.PUBLIC_KEYS))

    def test_guard_accepts_the_redesigned_page(self):
        report = pp.guard(self.records, self.cat, self.page, self.private, PEOPLE)
        self.assertEqual(report["records"], 3)

    def test_exactly_one_external_script_and_it_is_d3(self):
        tags = re.findall(r"<script\s[^>]*src=\"([^\"]+)\"[^>]*>", self.page)
        self.assertEqual(tags, ["https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"])
        tag = re.search(r"<script\s[^>]*src=\"https://cdnjs[^>]*>", self.page).group(0)
        self.assertIn("onerror=\"document.documentElement.classList.add('no-d3')\"", tag)
        self.assertIn('crossorigin="anonymous"', tag)
        self.assertNotIn("defer", tag)
        self.assertNotIn("integrity", tag)
        # the only "http" inside any script tag's attributes is that one address
        self.assertEqual(sum("http" in t for t in re.findall(r"<script\b[^>]*>", self.page)), 1)
        self.assertNotIn("<link", self.page)                              # no stylesheet or font request
        self.assertNotIn("@import", pp.CSS)

    def test_js_never_uses_innerhtml_storage_or_history_push(self):
        for bad in ("innerHTML", "outerHTML", ".html(", "insertAdjacentHTML", "localStorage", "sessionStorage", "document.cookie",
                    "pushState", "cloneNode", "eval(", "XMLHttpRequest", "fetch("):
            self.assertNotIn(bad, pp.JS, bad)
        self.assertIn("history.replaceState", pp.JS)
        self.assertIn("appendChild(LI[", pp.JS)                          # regrouping moves the card nodes
        self.assertIn("textContent", pp.JS)

    def test_dark_tokens_cover_every_light_token_in_both_dark_blocks(self):
        light = re.search(r":root\{(.*?)\}", pp.CSS, re.S).group(1)
        names = re.findall(r"(--[\w-]+):", light)
        self.assertGreater(len(names), 20)
        media = re.search(r'@media \(prefers-color-scheme: dark\)\{:root:not\(\[data-theme="light"\]\)\{(.*?)\}\}', pp.CSS, re.S).group(1)
        forced = re.search(r':root\[data-theme="dark"\]\{(.*?)\}', pp.CSS, re.S).group(1)
        for n in names:
            self.assertIn(n + ":", media, n)
            self.assertIn(n + ":", forced, n)
        self.assertEqual(media, forced)                                  # emitted twice from one string
        self.assertIn("body{margin:0;background:var(--bg)", pp.CSS)
        self.assertIn("@media (prefers-reduced-motion: reduce)", pp.CSS)
        self.assertIn("@media (forced-colors: active)", pp.CSS)

    def test_hash_keys_are_quoted_in_the_js(self):
        self.assertEqual(pp.HASH_KEYS, ("p", "k", "f", "s", "d", "e", "b", "q", "x", "w", "g", "v", "o", "i"))
        for k in pp.HASH_KEYS:
            self.assertIn(f"'{k}'", pp.JS, k)
        self.assertIn("var HASH_KEYS = ['" + "', '".join(pp.HASH_KEYS) + "'];", pp.JS)

    def _hash_block(self):
        return re.search(r"/\* @@hash-begin \*/(.*?)/\* @@hash-end \*/", pp.JS, re.S).group(1)

    @unittest.skipUnless(shutil.which("node"), "node is not on the PATH")
    def test_js_has_no_syntax_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "page.js"
            p.write_text(self.js, encoding="utf-8")
            r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    @unittest.skipUnless(shutil.which("node"), "node is not on the PATH")
    def test_hash_grammar_round_trips_in_node(self):
        script = self._hash_block() + r"""
var meta = {people: ['darryl-anka', 'zed-quorn'], decades: ['pre', '2020', '2030'], said: ['none', '1980', '2020'],
            basis: ['published', 'title', 'address', 'none'], n: 480, FULL: [1920, 2080], DEFAULT: [1985, 2055]};
function rt(h) { return serializeHash(parseHash(h, meta), meta); }
function eq(a, b) { if (a !== b) { throw new Error(JSON.stringify(a) + ' !== ' + JSON.stringify(b)); } }
eq(rt('#p=darryl-anka&x=2020-2040&w=1&g=said'), '#p=darryl-anka&x=2020-2040&w=1&g=said');
eq(rt('#f=conditional&v=table&o=start.1'), '#f=conditional&v=table&o=start.1');
eq(rt('#d=2020,2030'), '#d=2020,2030');
eq(rt('#i=12'), '#i=12');
eq(rt('#x=1920-2080&g=target'), '#x=1920-2080&g=target');
eq(rt('#e=none&b=address'), '#e=none&b=address');
eq(rt('#i=3&v=table&p=zed-quorn,darryl-anka&k=made'), '#p=darryl-anka,zed-quorn&k=made&v=table&i=3');   // fixed key order
eq(rt('#s12'), '#i=12');                                  // legacy fragments
eq(rt('#p-darryl-anka'), '#p=darryl-anka');
eq(rt('#p-nobody'), '');
eq(rt('#methods'), '');                                   // a plain anchor is left alone
eq(rt('#p=nobody&k=bogus&f=all&i=9999&x=abc&g=horizon&v=horizon&o=drop.1&zz=1'), '');
eq(rt('#x=2030-2031'), '#x=2028.5-2032.5');               // widened to four years
eq(rt('#x=1900-2500'), '#x=1920-2080');                   // clamped into the axis
eq(rt('#x=1985-2055'), '');                               // the default window is omitted
eq(rt('#q=%22two%20years%22%20-soon'), '#q=%22two%20years%22%20-soon');
eq(rt('#q=%E0%A4%A'), '');                                // a malformed value resets without throwing
eq(rt('garbage'), '');
eq(rt(''), '');
eq(parseHash('#i=479', meta).i, 479);
eq(parseHash('#i=480', meta).i, null);
eq(parseHash('#q=' + encodeURIComponent('x'.repeat(300)), meta).q.length, 100);
eq(JSON.stringify(parseHash('#s=1&w=1', meta).x), JSON.stringify([1985, 2055]));
console.log('ok');
"""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "hash.js"
            p.write_text(script, encoding="utf-8")
            r = subprocess.run(["node", str(p)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "ok")

    def test_hash_block_is_self_contained(self):
        block = self._hash_block()
        for fn in ("defaultState", "parseHash", "serializeHash", "clampWindow", "shiftWindow"):
            self.assertIn("function " + fn + "(", block)
        self.assertNotIn("document", block)
        self.assertNotIn("DATA", block)

    def test_csv_export_uses_the_public_keys_only(self):
        self.assertNotIn("__PUBLIC_KEYS__", self.page)
        self.assertIn("PUBLIC_KEYS = " + json.dumps(pp.PUBLIC_KEYS), self.page)
        self.assertEqual(re.findall(r"__[A-Z_]+__", self.page), [])
        self.assertIn("PUBLIC_KEYS.map(csvCell)", pp.JS)                 # the header row
        self.assertIn("PUBLIC_KEYS.map(function (k)", pp.JS)             # the data rows
        for private in ("sentence", "copy_group", "markers", "audio", "transcript"):
            self.assertNotIn("'" + private + "'", pp.JS)
        self.assertIn("'\\ufeff'", pp.JS)                                # BOM
        self.assertIn("revokeObjectURL", pp.JS)
        self.assertIn('id="download"', self.page)

    def test_legend_table_and_chart_markup(self):
        legend = re.search(r'<ul id="legend"[^>]*>(.*?)</ul>', self.page, re.S).group(1)
        self.assertEqual(legend.count("<li>"), 8)
        for s in ("filled circle", "filled diamond", "hollow mark", "thin ring", "bar: target span", "triangle", "rounded pill", "dashed line"):
            self.assertIn(s, legend)
        for i in ("minimap", "caveat-mini", "no-d3", "chart-help", "chart-status", "chart-svg", "chart-axis", "chartbox", "chart-scroll",
                  "table", "tablewrap", "empty", "toolbar", "q", "count", "group", "follow", "legend", "timeline-section", "groups",
                  "years", "caveat", "facts", "active", "clear-all", "group-nav", "zoom-in", "zoom-out", "zoom-fit", "zoom-now", "zoom-reset"):
            self.assertEqual(self.page.count(f'id="{i}"'), 1, i)
        self.assertIn('<svg id="chart-svg"', self.page)
        self.assertIn('tabindex="0" role="group" aria-roledescription="zoomable timeline"', self.page)
        self.assertIn('<table id="table"><caption class="sr-only">', self.page)
        self.assertIn("<thead></thead><tbody></tbody><tfoot></tfoot>", self.page)   # never server-rendered: quotes stay once
        self.assertEqual(len(re.findall(r'<details class="facet" data-facet="([pkfdeb])"', self.page)), 6)
        self.assertNotIn("people-select", self.page)
        self.assertIn('<a class="skip" href="#timeline-section">', self.page)
        self.assertIn("about 56% of windowed candidates (95% interval about 47% to 65%)", self.page)
        self.assertIn('<p id="caveat-mini" title=', self.page)

    def test_cards_carry_data_attributes_and_one_locate_button_each(self):
        self.assertEqual(self.page.count(">on the timeline</button>"), len(self.records))
        cards = re.findall(r'<li class="st" id="s(\d+)" data-i="(\d+)" data-start="(\d+)" data-end="(\d+)" data-person="([\w-]+)" '
                           r'data-kind="(source|made)" data-said="(none|\d{4})" data-cert="(strong|conditional|hedged|plain)" '
                           r'data-basis="(published|title|address|none)">', self.page)
        self.assertEqual(len(cards), len(self.records))
        self.assertEqual([c[0] for c in cards], [str(i) for i in range(len(self.records))])
        by_item = {r["item_id"]: r for r in self.records}
        self.assertIn('data-cert="strong"', self.page)
        self.assertIn('data-said="2010" data-cert="conditional" data-basis="address"', self.page)
        self.assertIn('data-said="none"', self.page)
        self.assertIn('<svg class="mk"', self.page)
        self.assertIn('<blockquote class="q">', self.page)
        self.assertIn('<span class="st-person">', self.page)
        self.assertEqual(pp.cert_of(by_item["pod-3333333333333333"]), "strong")
        self.assertEqual(pp.basis_key(by_item["web-2222222222222222"]), "address")

    def test_group_sections_with_sparkline_and_countline(self):
        self.assertEqual(self.page.count('<section class="group"'), 2)
        self.assertNotIn('class="person"', self.page)
        self.assertIn('<h3 class="ghead"><button type="button" class="gtoggle" aria-expanded="true" aria-controls="p-mira-vantelle-cards">', self.page)
        self.assertIn("2 statements · 1 hedged · 1 conditional · earliest target 2025 · latest 2035 · 1 from source texts, 1 from speech-to-text", self.page)
        self.assertIn('<svg class="mini" viewBox="0 0 72 14" width="72" height="14" role="img" aria-label="2 statements, targets 2025 to 2035">', self.page)
        self.assertIn('<div id="groups" data-group="person">', self.page)
        self.assertIn('<select id="group" name="g">', self.page)

    def test_facet_chips_count_and_label_without_text(self):
        facets = re.search(r'<div class="trow trow-2" id="facets">(.*?)</div>\s*<div class="trow trow-3">', self.page, re.S).group(1)
        self.assertIn('<input type="checkbox" name="p" value="mira-vantelle"><span class="cname">Mira Vantelle</span><span class="ccount num">2</span>', facets)
        self.assertIn('name="e" value="none"><span class="cname">date not known</span><span class="ccount num">1</span>', facets)
        self.assertIn('name="b" value="address"><span class="cname">from the page address</span><span class="ccount num">1</span>', facets)
        self.assertIn('name="s" value="1"><span class="cname">strong wording only</span><span class="ccount num">1</span>', facets)
        self.assertNotIn("lanterns", facets)
        self.assertNotIn("harbour", facets)

    def test_no_d3_fallback_markup_and_no_js_fallback(self):
        self.assertIn('<p id="no-d3" class="muted" hidden>The chart library did not load; the table and the lists below are complete.</p>', self.page)
        self.assertIn(".no-js .needs-js,.no-js .needs-d3,.no-d3 .needs-d3{display:none!important}", pp.CSS)
        self.assertIn('<html lang="en" class="no-js">', self.page)
        self.assertIn("if (!window.d3 || root.classList.contains('no-d3')) return null;", pp.JS)
        self.assertIn("if (!chart) state.v = 'table';", pp.JS)
        self.assertIn("<noscript>", self.page)
        # without JavaScript every card is visible: hidden attributes are only ever added by the script
        self.assertNotIn('<li class="st" hidden', self.page)
        self.assertNotIn("<section class=\"group\" hidden", self.page)
        # the d3-free code never touches d3: only initChart does
        before, after = pp.JS.split("function initChart()")
        self.assertNotIn("d3.", before)
        self.assertNotIn("d3.", after.split("return { render: schedule")[1])

    def test_narrow_screen_css(self):
        self.assertIn("@media (max-width:47.99rem)", pp.CSS)
        self.assertIn("@media (min-width:48rem)", pp.CSS)
        self.assertIn("html{overflow-x:clip", pp.CSS)
        self.assertIn(".wrap{max-width:76rem;margin:0 auto;padding:0 16px}", pp.CSS)
        self.assertIn("td.quote{min-width:22rem", pp.CSS)                # the table scrolls inside its box, never the page
        self.assertIn("#chart-scroll{max-height:72vh;overflow-y:auto;overflow-x:hidden", pp.CSS)
        self.assertIn(".tip{position:absolute;z-index:10;max-width:min(22rem,100% - 16px)", pp.CSS)
        self.assertIn("@media (pointer:coarse){.zoomctl button{min-width:40px;min-height:40px}}", pp.CSS)

    def test_plain_anchors_are_not_a_view(self):
        """A click on "Details" (#caveat) or the skip link changes the hash; that must not reset the filters, and an
        anchor the page did not write is left in the address."""
        self.assertIn("function isView(h)", pp.JS)
        self.assertIn("if (location.hash === lastWritten || (location.hash && !isView(location.hash))) return;", pp.JS)
        self.assertIn("if (!h && !isView(location.hash)) return;", pp.JS)
        self.assertIn('href="#caveat"', self.page)
        self.assertIn('href="#timeline-section"', self.page)

    @unittest.skipUnless(shutil.which("node"), "node is not on the PATH")
    def test_is_view_in_node(self):
        fn = re.search(r"function isView\(h\) \{.*?\}\n", pp.JS).group(0)
        script = fn + r"""
function eq(a, b) { if (a !== b) { throw new Error(JSON.stringify(a) + ' !== ' + JSON.stringify(b)); } }
eq(isView('#caveat'), false); eq(isView('#timeline-section'), false); eq(isView('#methods'), false); eq(isView(''), false);
eq(isView('#p=darryl-anka&x=2020-2040'), true); eq(isView('#v=table'), true); eq(isView('#s12'), true); eq(isView('#p-darryl-anka'), true);
console.log('ok');
"""
        with tempfile.TemporaryDirectory() as d:
            q = Path(d) / "isview.js"
            q.write_text(script, encoding="utf-8")
            r = subprocess.run(["node", str(q)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "ok")

    def test_chart_caption_only_for_rows_by_person(self):
        self.assertIn("$('#chart-caption').hidden = chartGrouping() !== 'person';", pp.JS)
        self.assertIn('<p id="chart-caption" class="muted">Rows are ordered by statements found, which reflects how much text each '
                      'person published and how well the rules fit their style, not how often they predict.</p>', self.page)

    def test_row_label_title_survives_truncation(self):
        # the label text lives in a tspan, so .text() on it never removes the <title> that carries the full name
        self.assertIn("ent.select('text').append('title');", pp.JS)
        self.assertIn("ent.select('text').append('tspan');", pp.JS)
        self.assertIn("span.text(s + '…')", pp.JS)

    def test_caveat_line_with_its_link_is_exposed_to_assistive_technology(self):
        # the sticky line holds a focusable link, so it is never aria-hidden (a nameless tab stop otherwise)
        line = re.search(r'<p id="caveat-mini"[^>]*>.*?</p>', self.page, re.S).group(0)
        self.assertNotIn("aria-hidden", line)
        self.assertIn('<a href="#caveat">Details</a>', line)
        self.assertIn("about 56% of windowed candidates are real predictions (95% interval about 47% to 65%)", line)

    def test_chart_box_scrolls_without_trapping_the_page_and_shares_one_width_with_the_axis(self):
        rule = re.search(r"#chart-scroll\{[^}]*\}", pp.CSS).group(0)
        self.assertNotIn("overscroll-behavior", rule)                   # the wheel chains to the page at the end of the rows
        self.assertIn("scrollbar-gutter:stable", rule)
        # W is the scroll container's client width (a classic scrollbar excluded) and the axis and mini-map take it in px
        self.assertIn("var w = scroll.clientWidth || (box.clientWidth - 8); W = Math.max(320, w || 800);", pp.JS)
        self.assertIn(".attr('width', W).attr('height', 30).style('width', W + 'px');", pp.JS)
        self.assertIn(".attr('height', miniH).style('width', W + 'px');", pp.JS)
        self.assertIn("if (Math.abs(scroll.clientWidth - W) > 2) { layout(); renderNow(); } }, 150); }).observe(scroll);", pp.JS)

    def test_row_labels_are_cached_ordered_and_found_by_key(self):
        self.assertIn("var labelCache = {};", pp.JS)
        self.assertIn("ck = full + '|' + maxW, c = labelCache[ck];", pp.JS)
        branch = pp.JS.split("span.text(full);")[1].split("labelCache[ck] = ")[0]
        self.assertEqual(pp.JS.count("getComputedTextLength"), branch.count("getComputedTextLength"))   # only inside the uncached branch
        self.assertIn("var all = lab.merge(ent).order();", pp.JS)
        self.assertIn("function labelAt(r) {", pp.JS)
        self.assertNotIn("$$('.rowlabel.btn-label', svgNode)", pp.JS)   # never by DOM position
        self.assertIn("var lb = labelAt(it.row); if (lb) lb.focus();", pp.JS)

    def test_one_update_per_filter_change_and_table_kept_when_unchanged(self):
        self.assertIn("relayout = true;\n      try { setDomain(cur, false); } finally { relayout = false; }", pp.JS)
        self.assertIn("if (relayout) return;", pp.JS)
        self.assertIn("requestAnimationFrame(function () { if (pending) render(); });", pp.JS)
        self.assertIn("if (sig === lastTableSig && tbody.rows.length === rows.length) return;", pp.JS)

    def test_said_label_is_escaped_in_the_card(self):
        r = dict(self.records[0]); r["date_said"] = "2024<&>"; r["date_basis"] = "title"
        html = pp.card_html(0, r)
        self.assertIn("said 2024&lt;&amp;&gt; (from title)", html)
        self.assertNotIn("2024<&>", html)

    def test_no_d3_keeps_the_table_view_after_a_hashchange(self):
        self.assertIn("function applyState() {\n    if (!chart) state.v = 'table';", pp.JS)

    def test_one_breakpoint_for_css_and_script(self):
        self.assertIn("window.matchMedia('(min-width:48rem)')", pp.JS)
        self.assertNotIn("window.innerWidth < 768", pp.JS)
        self.assertIn("if (!wide()) $('#years').open = false;", pp.JS)

    def test_now_fraction(self):
        self.assertEqual(pp.now_fraction("2026-11-16T00:00:00Z"), "2026.87")
        self.assertEqual(pp.now_fraction("2026-01-01"), "2026.00")
        self.assertEqual(pp.now_fraction("not a date"), "2026.50")
        self.assertIn("NOW_F = 2026.87", self.page)

    def test_page_size_within_limit_with_generous_margin(self):
        self.assertLess(len(self.page.encode("utf-8")), pp.PAGE_LIMIT // 4)

if __name__ == "__main__":
    unittest.main()
