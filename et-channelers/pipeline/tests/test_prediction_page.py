#!/usr/bin/env python3
"""Tests for pipeline/prediction_page.py with invented candidates and an invented catalogue: the guard (a 31-word
quote, a 6% item share, a private path, a questioner pattern, an audio link, an unknown-length item), copies kept
once, the sort order, the public-address rules, the share budget, the counts table without text, and the page
parsing as HTML with every quote present once.

    python3 -I -m unittest discover -s et-channelers/pipeline/tests -p test_prediction_page.py -v
"""
from __future__ import annotations

import csv
import json
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


if __name__ == "__main__":
    unittest.main()
