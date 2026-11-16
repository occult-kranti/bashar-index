#!/usr/bin/env python3
"""Tests for pipeline/prediction_page.py with invented candidates and an invented catalogue: the guard (a 31-word
quote, a 6% item share, a private path, a questioner pattern, an audio link, an unknown-length item), copies kept
once, the sort order, the public-address rules, the share budget, the counts table without text, the page
parsing as HTML with every quote present once, and the contract of the interactive page (one external script, no
innerHTML or storage, dark-token parity, the hash grammar round-tripped in node when node is present, the CSV
columns, the legend, the table, the no-d3 fallback and the narrow-screen CSS). Round two adds the full-screen stage, the
spot, the years-ahead and probe facets, the lead lines, the help dialog and the pointer extras, each pinned by its markup,
CSS and script contract and by the hash round trip.

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
        self.assertEqual(pp.HASH_KEYS, ("p", "k", "f", "s", "d", "e", "b", "a", "y", "q", "x", "w", "g", "v", "o", "i", "l", "fs"))
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
            basis: ['published', 'title', 'address', 'none'], ahead: ['0', '1', '5', 'none'], n: 480, FULL: [1920, 2080], DEFAULT: [1985, 2055]};
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
eq(rt('#q=' + encodeURIComponent('a'.repeat(99) + '\uD83D\uDE00' + 'b')), '#q=' + encodeURIComponent('a'.repeat(99) + '\uD83D\uDE00'));   // cut by code points, never inside a pair
eq(cleanQ('x\uD83Dy'), 'xy');                              // a lone surrogate is dropped, so the writer never throws
eq(cleanQ('\uD83D\uDE00').length, 2);
eq(serializeHash(parseHash('#q=' + encodeURIComponent('\uD83D\uDE00'), meta), meta), '#q=' + encodeURIComponent('\uD83D\uDE00'));
eq(JSON.stringify(parseHash('#s=1&w=1', meta).x), JSON.stringify([1985, 2055]));
eq(rt('#fs=1'), '#fs=1');                                 // full screen (the expanded mode from a link)
eq(rt('#fs=0'), '');
eq(rt('#i=3&fs=1&v=table'), '#v=table&i=3&fs=1');         // fs is written last
eq(rt('#a=5,0&y=2030&l=1&fs=1'), '#a=0,5&y=2030&l=1&fs=1'); // years ahead in band order, the probe year, lead lines
eq(rt('#y=1800'), '');                                    // a probe year outside the axis is ignored
eq(rt('#y=2500'), '');
eq(rt('#y=203'), '');
eq(rt('#g=ahead'), '#g=ahead');
eq(rt('#l=0&fs=0'), '');
eq(rt('#a=7'), '');
eq(parseHash('#y=2030', meta).y, 2030);
eq(parseHash('#x=2020-2040', meta).y, null);
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
        self.assertEqual(legend.count("<li>"), 10)
        for s in ("filled circle", "filled diamond", "hollow mark", "thin ring", "bar: target span", "triangle", "rounded pill", "dashed line",
                  "hairline", "solid line"):
            self.assertIn(s, legend)
        for i in ("minimap", "caveat-mini", "no-d3", "chart-help", "chart-status", "chart-svg", "chart-axis", "chartbox", "chart-scroll",
                  "table", "tablewrap", "empty", "toolbar", "q", "count", "group", "follow", "legend", "timeline-section", "groups",
                  "years", "caveat", "facts", "active", "clear-all", "group-nav", "zoom-in", "zoom-out", "zoom-fit", "zoom-now", "zoom-reset",
                  "stage", "statements-section", "fs-toggle", "fs-scrim", "facets-h", "facets-close", "caveat-more", "caveat-more-1",
                  "caveat-more-2", "list-toggle", "list-n", "share", "share-status", "share-fallback",
                  "spot", "spot-h", "spot-body", "spot-close", "spot-prev", "spot-next", "spot-card", "spot-zoom", "spot-person", "spot-status",
                  "leads-toggle", "probe-year", "probe-clear", "help", "help-h", "help-btn", "help-close"):
            self.assertEqual(self.page.count(f'id="{i}"'), 1, i)
        self.assertIn('<svg id="chart-svg"', self.page)
        self.assertIn('tabindex="0" role="group" aria-roledescription="zoomable timeline"', self.page)
        self.assertIn('<table id="table"><caption class="sr-only">', self.page)
        self.assertIn("<thead></thead><tbody></tbody><tfoot></tfoot>", self.page)   # never server-rendered: quotes stay once
        self.assertEqual(len(re.findall(r'<details class="facet" data-facet="([pkfdebay])"', self.page)), 8)
        self.assertNotIn("people-select", self.page)
        self.assertIn('<a class="skip" href="#timeline-section">', self.page)
        self.assertIn("about 56% of windowed candidates (95% interval about 47% to 65%)", self.page)
        self.assertIn('<p id="caveat-mini" title=', self.page)

    def test_cards_carry_data_attributes_and_one_locate_button_each(self):
        self.assertEqual(self.page.count(">on the timeline</button>"), len(self.records))
        cards = re.findall(r'<li class="st" id="s(\d+)" data-i="(\d+)" data-start="(\d+)" data-end="(\d+)" data-person="([\w-]+)" '
                           r'data-kind="(source|made)" data-said="(none|\d{4})" data-cert="(strong|conditional|hedged|plain)" '
                           r'data-basis="(published|title|address|none)" data-ahead="(0|1|3|5|10|20|none)">', self.page)
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
        self.assertIn('<span class="sel-t">Rows and groups</span> <select id="group" name="g" aria-label="rows and groups">', self.page)

    def test_facet_chips_count_and_label_without_text(self):
        facets = re.search(r'<div class="trow trow-2" id="facets">(.*?)</div>\s*<div class="trow trow-3">', self.page, re.S).group(1)
        self.assertIn('<input type="checkbox" name="p" value="mira-vantelle"><span class="cname">Mira Vantelle</span><span class="ccount num">2</span>', facets)
        self.assertIn('name="e" value="none"><span class="cname">date not known</span><span class="ccount num">1</span>', facets)
        self.assertIn('name="b" value="address"><span class="cname">from the page address</span><span class="ccount num">1</span>', facets)
        self.assertIn('name="s" value="1"><span class="cname">strong wording only</span><span class="ccount num">1</span>', facets)
        self.assertNotIn("lanterns", facets)
        self.assertNotIn("harbour", facets)
        # years ahead: counted chips in band order, bands present only; the probe facet has no chips, a bounded number input
        self.assertIn('name="a" value="5"><span class="cname">5 to 9 years</span><span class="ccount num">1</span>', facets)     # 2031 said 2024
        self.assertIn('name="a" value="10"><span class="cname">10 to 19 years</span><span class="ccount num">1</span>', facets)  # by 2030 said 2014
        self.assertIn('name="a" value="none"><span class="cname">date said not known</span><span class="ccount num">1</span>', facets)
        self.assertNotIn('name="a" value="0"', facets)
        self.assertLess(facets.index('name="a" value="5"'), facets.index('name="a" value="10"'))
        self.assertLess(facets.index('name="a" value="10"'), facets.index('name="a" value="none"'))
        probe = re.search(r'<details class="facet" data-facet="y">(.*?)</details>', facets, re.S).group(1)
        self.assertNotIn("chip-check", probe)
        self.assertIn('<input type="number" id="probe-year" name="y" min="1920" max="2080" step="1" inputmode="numeric">', probe)
        self.assertIn('<button type="button" id="probe-clear" class="btn">clear</button>', probe)
        self.assertIn('<option value="ahead">by years ahead</option>', self.page)

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
        self.assertIn("if (Math.abs(scroll.clientWidth - W) > 2 || (state.fs && Math.abs(scroll.clientHeight - HV) > 2)) { layout(); renderNow(); } }, 150); }).observe(scroll);", pp.JS)

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

    def test_ahead_band(self):
        r = dict(self.records[0])
        for said, lo, hi, band in (("", 2031, 2031, "none"), ("2031", 2031, 2031, "0"), ("2031", 2020, 2020, "0"), ("2029", 2031, 2031, "1"),
                                   ("2027", 2031, 2031, "3"), ("2022", 2031, 2031, "5"), ("2012", 2031, 2031, "10"), ("2000", 2031, 2031, "20"),
                                   ("2024-03", None, 2030, "5"), ("2024", 2025, 2035, "10")):
            r["date_said"], r["window_lo"], r["window_hi"] = said, lo, hi
            self.assertEqual(pp.ahead_band(r), band, (said, lo, hi))
        # the JS mirrors the thresholds
        self.assertIn("d.aheadBand = d.ahead === null ? 'none' : (d.ahead <= 0 ? '0' : d.ahead <= 2 ? '1' : d.ahead <= 4 ? '3' : d.ahead <= 9 ? '5' : d.ahead <= 19 ? '10' : '20');", pp.JS)
        self.assertEqual(pp.AHEAD_ORDER, ("0", "1", "3", "5", "10", "20", "none"))
        for k, label in pp.AHEAD_LABELS.items():
            self.assertIn("'" + label + "'", pp.JS, label)

    def test_probe_and_lead_lines_contract(self):
        self.assertIn("function coversYear(d, y) { return d.window_lo === null ? (y <= d.end && (d.saidYear === null || y >= d.saidYear)) : (d.start <= y && y <= d.end); }", pp.JS)
        for s in ("case 'y': return state.y === null || coversYear(d, state.y);", "case 'a': return !state.a.length || state.a.indexOf(d.aheadBand) >= 0;",
                  "var FACETS = ['p', 'k', 'f', 's', 'd', 'e', 'b', 'a', 'y', 'q'];", "ahead: { key: function (d) { return d.aheadBand; }, keys: AHEAD_KEYS",
                  "else if (g === 'ahead') state.a = [k];", "tok('y', '', 'Expected for ' + state.y)", "'Ahead: ' + AHEAD_LABEL[k]",
                  "' · windows cover ' + state.y", "var probeLine = svg.append('line').attr('class', 'probe-line')", "probeLabel.text(ptxt);",
                  "var ptxt = py + ' · ' + pn", "miniProbe", "leadsAllG = plotG.append('g').attr('class', 'leads-all')",
                  "if (state.l) visItems.forEach(", "else if (k === 'l') toggleLeads(); else if (k === 'y') probeFocus();",
                  "$('#leads-toggle').addEventListener('click', toggleLeads);", "if (st.l) parts.push('l=1');", "if (st.y !== null) parts.push('y=' + st.y);",
                  "case 'a': st.a = list(meta.ahead); break;"):
            self.assertIn(s, pp.JS, s)
        # the lead-line layer paints under the hover lead, the probe line over the row labels
        chart = pp.JS.split("function initChart()")[1]
        self.assertLess(chart.index("attr('class', 'leads-all')"), chart.index("attr('class', 'leads')"))
        self.assertLess(chart.index("attr('class', 'rowlabels')"), chart.index("attr('class', 'probe-line')"))
        for s in (".lead-all{stroke:var(--fg-faint);stroke-width:1}", ".probe-line{stroke:var(--fg);stroke-width:1.5}", ".probe-mini{stroke:var(--fg);stroke-width:1}",
                  ".probe-line,.probe-mini{stroke:Highlight}", ".lead-all{stroke:GrayText}"):
            self.assertIn(s, pp.CSS, s)
        self.assertIn("a for years ahead, y for the probe year", self.page)

    def test_help_dialog_keys_and_contrast(self):
        self.assertEqual(self.page.count("<dialog"), 1)
        dialog = re.search(r'<dialog id="help" class="help" aria-labelledby="help-h">(.*?)</dialog>', self.page, re.S).group(1)
        self.assertRegex(dialog, r'<h2 id="help-h"[^>]*>Keyboard shortcuts and help</h2>')
        self.assertEqual(dialog.count('<th scope="col">'), 3)
        self.assertGreaterEqual(dialog.count("<kbd>"), 25)
        for s in ("<kbd>Shift</kbd>+<kbd>F</kbd>", "<kbd>?</kbd>", "<kbd>j</kbd> <kbd>k</kbd>", "<kbd>l</kbd>", "<kbd>y</kbd>", "Shift+drag zooms",
                  "Shift+scroll or a sideways trackpad swipe pans", "fs=1 opens the expanded mode", "Escape leaves at once", "The address after # holds the whole view",
                  '<button type="button" id="help-close" class="btn">Close</button>'):
            self.assertIn(s, dialog, s)
        self.assertNotIn("<script", dialog)
        stage = re.search(r'<div id="stage">(.*?)<div id="fs-scrim" hidden></div>\n</div>', self.page, re.S).group(1)
        self.assertIn('<dialog id="help"', stage)                         # inside the stage, so never inert in full screen
        self.assertIn('<button type="button" id="help-btn" class="btn" aria-haspopup="dialog" aria-controls="help"', self.page)
        self.assertIn("Shift+F is full screen; ? lists every shortcut.", self.page)
        for s in ("function openHelp(opener)", "help.showModal()", "help.setAttribute('open', '')", "help.addEventListener('close', helpBack);",
                  "else if (e.key === '?') { e.preventDefault(); openHelp(e.target); }", "function helpOpen() { return help.hasAttribute('open'); }"):
            self.assertIn(s, pp.JS, s)
        code = pp.JS.split("var help = $('#help')")[1].split("$('#help-close')")[0]
        for bad in ("innerHTML", "insertAdjacentHTML", "cloneNode", ".html("):
            self.assertNotIn(bad, code)
        self.assertIn("#stage.is-fs #chart-help{display:none}", pp.CSS)
        self.assertIn(".help::backdrop{background:var(--scrim", pp.CSS)
        self.assertIn("kbd{font-family:var(--font-mono)", pp.CSS)
        # text never set in --fg-faint (below 4.5:1); the token stays for graphics
        for rule in (".tip .hint{", ".mini-axis text{", ".chip-check[data-zero]{", ".seg label:has(input:disabled){"):
            block = pp.CSS.split(rule)[1].split("}")[0]
            self.assertNotIn("--fg-faint", block, rule)
            self.assertIn("--fg-muted", block, rule)
        self.assertIn(".stackbar{fill:var(--fg-faint)", pp.CSS)

    def test_pointer_extras_inside_the_chart(self):
        chart = pp.JS.split("function initChart()")[1].split("return { render: schedule")[0]
        # Shift+wheel and a sideways swipe pan: a non-passive listener registered before the zoom, so d3's filter never sees them
        self.assertIn("svgNode.addEventListener('wheel', function (e) {", chart)
        self.assertLess(chart.index("svgNode.addEventListener('wheel'"), chart.index("svg.call(zoom)"))
        self.assertIn("}, { passive: false });", chart)
        self.assertIn("e.preventDefault(); e.stopImmediatePropagation();", chart)
        self.assertIn("if (e.ctrlKey || e.metaKey || !(e.shiftKey || horiz)) return;", chart)   # plain wheel scrolls, Ctrl+wheel zooms when armed
        self.assertIn("pan(delta / plotW * 1.5);", chart)
        # Shift+drag rubber band: the zoom filter rejects it, 8px or more sets the window, Escape cancels
        self.assertIn("if (ev.type === 'mousedown' && ev.shiftKey) return false;", chart)
        self.assertIn("var rubber = svg.append('rect').attr('class', 'rubber')", chart)
        self.assertIn("if (apply && Math.abs(b - a) >= 8) {", chart)
        self.assertIn("setDomain([x.invert(Math.min(a, b)), x.invert(Math.max(a, b))], true);", chart)
        self.assertIn("if (e.key === 'Escape' && rubberA !== null) { endRubber(e, false); e.preventDefault(); }", chart)
        self.assertIn("e.pointerType === 'touch'", chart)                 # touch keeps the one- or two-finger rule
        self.assertIn(".rubber{fill:var(--brush);stroke:var(--accent);stroke-width:1", pp.CSS)
        self.assertIn(".rubber{fill:Highlight;fill-opacity:.3}", pp.CSS)
        # no new hash keys and no new tokens for these
        self.assertEqual(len(pp.HASH_KEYS), 18)

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

    # ---- round two: full screen
    def test_stage_wraps_the_toolbar_the_timeline_and_the_statements(self):
        stage = re.search(r'<div id="stage">(.*?)<div id="fs-scrim" hidden></div>\n</div>', self.page, re.S).group(1)
        for s in ('<form id="toolbar"', '<section id="timeline-section"', '<section id="statements-section" aria-labelledby="statements">'):
            self.assertIn(s, stage, s)
        self.assertNotIn('<details id="years"', stage)                   # the year index, the methods and the footer stay outside
        self.assertNotIn("<h2 id=\"methods\">", stage)
        self.assertIn("#stage{display:contents}", pp.CSS)                # no box of its own outside full screen: the toolbar stays sticky
        self.assertIn('<button type="button" id="fs-toggle" class="btn needs-d3" aria-pressed="false" aria-keyshortcuts="Shift+F"', self.page)
        self.assertIn('<button type="button" id="list-toggle" class="btn fs-only" aria-pressed="true"', self.page)
        self.assertIn('<div class="sheet-head"><b id="facets-h">Filters</b><button type="button" id="facets-close" class="btn">Close</button></div>', self.page)
        self.assertIn('<div id="caveat-more" class="caveat-more" hidden><p id="caveat-more-1"></p><p id="caveat-more-2"></p></div>', self.page)   # filled at runtime: the prose exists once
        self.assertEqual(self.page.count("about 56% of windowed candidates are real predictions"), 2)   # #caveat-mini and its title only, plus the figure
        self.assertIn('<div class="ch-main">', self.page)
        self.assertIn('<div class="ch-more">', self.page)
        self.assertIn('<span class="long">list and table follow the window</span><span class="short">follow the window</span>', self.page)

    def test_full_screen_css_contract(self):
        self.assertIn("#stage.is-fs{display:grid", pp.CSS)
        self.assertIn("height:100vh;height:100dvh", pp.CSS)
        self.assertIn("html.fs,html.fs body{overflow:hidden", pp.CSS)
        self.assertIn("html.fs-fallback body{position:fixed;inset:0;width:100%}", pp.CSS)
        caveats = re.findall(r"#stage\.is-fs #caveat-mini\{[^}]*\}", pp.CSS)
        self.assertEqual(len(caveats), 1)
        self.assertIn("white-space:normal;overflow:visible", caveats[0])  # the caveat wraps in full in full screen: no clamp, no ellipsis
        for bad in ("display:none", "line-clamp", "nowrap", "ellipsis", "overflow:hidden"):
            self.assertNotIn(bad, caveats[0], bad)
        self.assertNotIn("#stage.is-fs #fs-toggle{order:-1}", pp.CSS)      # the focus order is the visual order
        self.assertIn("#stage.is-fs #legend{display:grid;grid-auto-flow:column;grid-template-rows:auto auto", pp.CSS)   # two rows at 48rem+, scrolling
        self.assertIn("#stage.is-fs.v-table > #statements-section{display:none}", pp.CSS)   # table view: no empty list column or sheet
        self.assertIn("#stage.is-fs.v-table #list-toggle{display:none}", pp.CSS)
        self.assertIn("@media (min-width:64rem) and (max-width:79.99rem){", pp.CSS)
        self.assertNotIn("#legend{display:none", pp.CSS)                  # the legend is a scrolling row on phones, never hidden
        self.assertIn("backdrop-filter:none", pp.CSS)                     # a filtered toolbar would become the containing block of the fixed sheet
        self.assertIn("#stage.is-fs > #toolbar{", pp.CSS)
        self.assertIn("#stage.is-fs.list-on{grid-template-columns:minmax(0,1fr) var(--panel-w)}", pp.CSS)
        self.assertIn("#stage.is-fs > #statements-section{position:fixed;left:0;right:0;bottom:0", pp.CSS)
        self.assertIn("#fs-scrim{position:fixed;inset:0;background:var(--scrim);z-index:var(--z-scrim)}", pp.CSS)
        self.assertIn("@media (min-width:64rem)", pp.CSS)
        self.assertIn("window.matchMedia('(min-width:64rem)')", pp.JS)
        for tok in ("--scrim:", "--z-stage:", "--z-scrim:", "--z-sheet:", "--panel-w:"):
            self.assertIn(tok, pp.CSS, tok)
        light = re.search(r":root\{(.*?)\}", pp.CSS, re.S).group(1)
        self.assertIn("--scrim:", light)                                 # the dark blocks are covered by the parity test
        self.assertIn(":root[data-theme=\"dark\"]{", pp.CSS)             # the theme attribute still switches the tokens
        self.assertIn('@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){', pp.CSS)
        # the pinned rules of round one are byte-identical
        self.assertIn("@media (pointer:coarse){.zoomctl button{min-width:40px;min-height:40px}}", pp.CSS)
        self.assertIn(".wrap{max-width:76rem;margin:0 auto;padding:0 16px}", pp.CSS)
        self.assertEqual(re.search(r"#chart-scroll\{[^}]*\}", pp.CSS).group(0), "#chart-scroll{max-height:72vh;overflow-y:auto;overflow-x:hidden;scrollbar-gutter:stable;position:relative}")

    def test_full_screen_js_contract(self):
        for s in ("function enterFs(native)", "function leaveFs(reason)", "'fullscreenchange'", "requestFullscreen", "exitFullscreen",
                  ".inert = on", "root.classList.add('fs-fallback')", "stage.classList.add('is-fs')", "if (state.fs) enterFs(false);",
                  "leaveFs('escape')", "leaveFs('browser')", "leaveFs('hash')", "if ((e.key === 'F' || e.key === 'f') && e.shiftKey)", "navigator.clipboard.writeText",
                  "function toggleFs() { if (!chart) return;", "if (state.fs && state.v !== 'table') setList(true);", "classList.toggle('v-table', state.v === 'table')",
                  "itype !== 'checkbox' && itype !== 'radio'", "function sheetInert(on)", "function ensheet() { setList(false);", "help.scrollTop = 0;",
                  "k === 'f' && !ev.shiftKey",
                  "copy is not available here; the address is selected below", "fb.select()", "setList(column())",
                  "ev.touches.length >= (state.fs ? 1 : 2)", "rowH = state.fs ? Math.max(base, Math.min(72, Math.floor((HV - 12) / n))) : base;",
                  "L = W >= 1440 ? 200 : 150", "'orientationchange'", "case 'fs': st.fs = v === '1'; break;", "if (st.fs) parts.push('fs=1');"):
            self.assertIn(s, pp.JS, s)
        self.assertIn("if (!chart) state.fs = false;", pp.JS)             # no chart, no full screen (the toggle needs d3)
        self.assertIn('<h2 id="help-h" tabindex="-1">', self.page)        # the help opens at its top
        self.assertNotIn('aria-keyshortcuts="l"', self.page)              # l works with the chart focused only
        self.assertNotIn("k === 'f' || k === 'F'", pp.JS)                 # fit is f alone, so Shift+F reaches the page
        # the caveat text is copied from #caveat at runtime, never written twice into the source
        self.assertIn("$('#caveat-more-1').textContent = ps[0] ? ps[0].textContent : ''", pp.JS)
        # the Escape ladder is one document handler that skips what the svg already handled
        ladder = pp.JS.split("doc.addEventListener('keydown', function (e) {")[-1]   # the last document keydown handler
        self.assertIn("if (e.defaultPrevented) return;", ladder)
        self.assertLess(ladder.index("helpOpen()"), ladder.index("leaveFs('escape')"))

    # ---- round two: the spot, a pinned statement under the chart
    def test_spot_markup_is_empty_in_the_source_and_filled_from_the_record(self):
        self.assertIn('<aside id="spot" class="spot needs-js" aria-labelledby="spot-h" hidden tabindex="-1">', self.page)
        self.assertIn('<div id="spot-body"></div>', self.page)                           # built at runtime: the quotes stay once in the source
        self.assertIn('<h3 id="spot-h"></h3>', self.page)
        self.assertIn('<p id="spot-status" class="sr-only" aria-live="polite"></p>', self.page)
        self.assertIn("function renderSpot() {", pp.JS)
        self.assertIn("applyPin(); renderSpot(); scheduleHash();", pp.JS)              # state.i is the single source of truth
        body = pp.JS.split("function renderSpot() {")[1].split("$('#spot-close')")[0]
        for s in ("windowLabel(d)", "markSample(d)", "d.person_name", "kindLabel(d)", "flagsOf(d)", "d.quote", "d.time_expr", "saidLabel(d)",
                  "aheadText(d)", "d.item_id", "linkLabel(d)", "noLinkLabel(d)", "'labelled candidate'", "' of ' + VIEW_ORDER.length + ' in view'"):
            self.assertIn(s, body, s)
        for bad in ("innerHTML", "insertAdjacentHTML", "cloneNode"):
            self.assertNotIn(bad, body)
        self.assertIn("VIEW_ORDER = ORDER.filter(", pp.JS)
        # a click on a mark pins without scrolling the page; the card path stays on Shift+click and the spot's button
        self.assertIn("if (e.shiftKey && it.single) { showCard(it.d.i); return; }", pp.JS)
        self.assertIn("$('#spot-card').addEventListener('click', function () { if (state.i !== null) showCard(state.i); });", pp.JS)
        self.assertIn("tipPinned = null; if (COARSE) hideTip(); goTo(it.d.i);", pp.JS)   # one tap pins; no second tap
        self.assertNotIn("tap again: open the card", pp.JS)
        self.assertIn("'tap: pin, details below'", pp.JS)
        self.assertIn("else if (k === 'j') spotStep(1); else if (k === 'k') spotStep(-1);", pp.JS)
        self.assertIn("focusI: function (i) { return focusMark(stackOf[i] || ('i' + i)); }", pp.JS)
        self.assertIn('#stage.is-fs #spot{flex:none;max-height:11rem;overflow:auto', pp.CSS)
        self.assertIn('.spot[data-kind="source"]{border-left-color:var(--series-source)}', pp.CSS)

if __name__ == "__main__":
    unittest.main()
