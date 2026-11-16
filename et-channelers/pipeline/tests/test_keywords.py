#!/usr/bin/env python3
"""Tests for pipeline/keywords.py with invented data: tokens and stopwords, the channel's name and its title
furniture, TF-IDF, the log-odds z and the Mantel-Haenszel z checked by hand, the log-odds sign against the rates,
Fisher's exact test, the blackout lexicon with its excludes (built-in and from a theme file), the history's tabs,
kinds kept apart, the public counts without text, and a repeatable output in fresh processes.

    python3 -I -m unittest discover -s et-channelers/pipeline/tests -p test_keywords.py -v
"""
from __future__ import annotations

import collections
import csv
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PIPE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PIPE))
import keywords as kw  # noqa: E402

QUEUE_FIELDS = ["video_id", "url", "channel_dir", "title", "duration_s", "channeling", "entity", "sources", "shard",
                "tab", "listing_rank", "upload_date_approx"]
CATALOG_FIELDS = ["item_id", "person_id", "lane", "title", "published", "publisher_text_path", "captions_path",
                  "asr_path", "twin_of"]

# two invented channels; every word below is made up for the test
TIER = {"zed-quorn": [("ZQ000000001", "Zorblax speaks: the quillon harvest is near"),
                      ("ZQ000000002", "Zorblax: prepare for a BLACKOUT this winter"),
                      ("ZQ000000003", "Zorblax | quillon harvest and the media blackout"),
                      ("ZQ000000004", "Zorblax on solar flare season")],
        "mira-vantelle": [("MV000000001", "Mira Vantelle: crystalline grid activation"),
                          ("MV000000002", "Star tides and moon gardens"),
                          ("MV000000003", "Schumann resonance blackout today")]}
HISTORY = {"zed-quorn": [("ZQ000000101", "Zorblax on moon gardens"), ("ZQ000000102", "Zorblax: star tides"),
                         ("ZQ000000103", "Zorblax and the power grid going down"), ("ZQ000000104", "Zorblax: moon gardens")],
           "mira-vantelle": [("MV000000101", "Moon gardens"), ("MV000000102", "Star tides return")]}
# a short of the channel's: left out of the history by default, since the tier has only videos
SHORTS = {"zed-quorn": [("ZQ000000201", "Zorblax: blackout quillon short")]}


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def make_root(root):
    tier = [{"video_id": v, "channel_dir": ch, "title": t, "tab": "videos"} for ch, vs in TIER.items() for v, t in vs]
    hist = [{"video_id": v, "channel_dir": ch, "title": t, "tab": "videos"} for ch, vs in HISTORY.items() for v, t in vs]
    hist += [{"video_id": v, "channel_dir": ch, "title": t, "tab": "shorts"} for ch, vs in SHORTS.items() for v, t in vs]
    write_csv(root / "jobs" / "queue_newest10.csv", QUEUE_FIELDS, tier)
    write_csv(root / "jobs" / "queue_youtube_all.csv", QUEUE_FIELDS, tier + hist)
    # a podcast twin of ZQ000000001 with a text from the source, speech-to-text made here and the video's captions
    (root / "transcripts_publisher" / "zed-quorn").mkdir(parents=True)
    (root / "transcripts_publisher" / "zed-quorn" / "pod-a.txt").write_text(
        "The quillberry orchards bloom. The quillberry orchards rest. Register here for the zentrova blackout "
        "workshop.", encoding="utf-8")
    (root / "transcripts" / "zed-quorn").mkdir(parents=True)
    (root / "transcripts" / "zed-quorn" / "pod-a.json").write_text(json.dumps(
        {"segments": [{"start": 0.0, "text": "Zanthor rivers sing."}, {"start": 2.0, "text": "Zanthor rivers rest."}]}),
        encoding="utf-8")
    (root / "captions" / "zed-quorn").mkdir(parents=True)
    (root / "captions" / "zed-quorn" / "ZQ000000002.txt").write_text("Mivvle lanterns glow. Mivvle lanterns fade.",
                                                                     encoding="utf-8")
    # an older text from the source with a blackout sentence
    (root / "transcripts_publisher" / "zed-quorn" / "web-b.txt").write_text(
        "Quillberry orchards wait. A blackout of the power grid is coming.", encoding="utf-8")
    write_csv(root / "catalog" / "catalog.csv", CATALOG_FIELDS, [
        {"item_id": "pod-a", "person_id": "zed-quorn", "lane": "pod", "twin_of": "ZQ000000001",
         "publisher_text_path": "transcripts_publisher/zed-quorn/pod-a.txt", "asr_path": "transcripts/zed-quorn/pod-a.txt"},
        {"item_id": "ZQ000000002", "person_id": "zed-quorn", "lane": "youtube",
         "captions_path": "captions/zed-quorn/ZQ000000002.txt"},
        {"item_id": "web-b", "person_id": "zed-quorn", "lane": "web",
         "publisher_text_path": "transcripts_publisher/zed-quorn/web-b.txt"}])


class Tokens(unittest.TestCase):
    def test_tokens_stopwords_years_and_breaks(self):
        text = ("The Power Grid's DOWN!! 2026 #Blackout https://example.com/x 11:11 🙏 5D shift, don't wait — "
                "I AM 𝐇𝐄𝐑𝐄")
        uni, bi = kw.terms(kw.tokens(text))
        self.assertEqual(uni, ["power", "grid", "down", "2026", "blackout", "5d", "shift", "wait"])
        self.assertEqual(bi, ["power grid", "grid down", "5d shift"])        # "#" breaks the pair

    def test_hashtags_and_ampersands_break_bigrams(self):
        self.assertEqual(kw.terms(kw.tokens("#quillon #zorblax")), (["quillon", "zorblax"], []))
        self.assertEqual(kw.terms(kw.tokens("Outages & Gardens")), (["outages", "gardens"], []))

    def test_may_as_a_month_free_will_usa_and_being(self):
        uni, bi = kw.terms(kw.tokens("May 2026 update: you may rest, 15 May"))
        self.assertEqual(uni, ["may", "2026", "update", "rest", "may"])
        self.assertEqual(bi, ["may 2026", "2026 update"])
        uni, bi = kw.terms(kw.tokens("Free will and the U.S. dollar; it will pass"))
        self.assertEqual(uni, ["free", "will", "usa", "dollar", "pass"])
        self.assertEqual(bi, ["free will", "usa dollar"])
        self.assertEqual(kw.terms(kw.tokens("a light being"))[1], ["light being"])

    def test_calendar_terms(self):
        self.assertTrue(kw.is_calendar("2026"))
        self.assertTrue(kw.is_calendar("october 2026"))
        self.assertTrue(kw.is_calendar("monday"))
        self.assertFalse(kw.is_calendar("2026 blackout"))
        self.assertFalse(kw.is_calendar("quillon"))

    def test_numbers_single_letters_and_stopwords_break_bigrams(self):
        uni, bi = kw.terms(kw.tokens("top 10 quillon tides of the moon x gardens"))
        self.assertEqual(uni, ["top", "quillon", "tides", "moon", "gardens"])
        self.assertEqual(bi, ["quillon tides"])     # 10, "of the" and "x" break the pairs
        uni, _ = kw.terms(kw.tokens("the 11th gate at 4PM, the 1960s and 5G towers in 2025"))
        self.assertEqual(uni, ["gate", "5g", "towers", "2025"])

    def test_chinese_and_japanese_runs_become_character_pairs(self):
        uni, bi = kw.terms(kw.tokens("人の悩み"))
        self.assertEqual(uni, ["人の", "の悩", "悩み"])
        self.assertEqual(bi, [])

    def test_channel_name_is_dropped(self):
        single, phrases, strings = kw.name_drops("mira-vantelle", "Mira Vantelle (Star Harbour)", "channeler")
        self.assertEqual(single, {"mira", "vantelle"})
        self.assertEqual(strings, ())
        uni, bi = kw.terms(kw.tokens("Mira's Star Harbour message for Vantelle fans, star seeds"), single, phrases)
        self.assertEqual(uni, ["message", "fans", "star", "seeds"])
        self.assertEqual(bi, ["star seeds"])
        # an organisation's words go only as a phrase
        single, phrases, _ = kw.name_drops("tide-house", "Tide House", "organisation")
        self.assertEqual(single, frozenset())
        self.assertEqual(kw.terms(kw.tokens("Tide House: the tide turns"), single, phrases)[0], ["tide", "turns"])

    def test_names_are_compared_without_accents(self):
        single, phrases, _ = kw.name_drops("zoe-kral", "Zoë Krąl", "channeler")
        self.assertEqual(single, {"zoe", "kral"})
        self.assertEqual(kw.terms(kw.tokens("Zoe Kral and Zoë Krąl: Krąl's gardens"), single, phrases)[0], ["gardens"])

    def test_ordinary_name_words_go_only_with_the_whole_name(self):
        single, phrases, _ = kw.name_drops("mira-rose", "Mira Rose", "channeler")
        self.assertEqual(single, {"mira"})                       # "rose" is a word of these titles
        self.assertEqual(kw.terms(kw.tokens("Rose gardens by Mira Rose"), single, phrases),
                         (["rose", "gardens"], ["rose gardens"]))
        # a brand whose words are all ordinary words: only the whole name goes
        single, phrases, _ = kw.name_drops("council-star-whispers", "Council Star Whispers", "channeler")
        self.assertEqual(single, frozenset())
        self.assertEqual(kw.terms(kw.tokens("The council speaks | Council Star Whispers"), single, phrases)[0],
                         ["council", "speaks"])

    def test_name_phrases_have_no_stopword_at_their_edges(self):
        _, phrases, _ = kw.name_drops("sara-vale", "Sara Vale (Into the Moon Channeling)", "channeler")
        self.assertIn(("moon", "channeling"), phrases)
        self.assertTrue(all(p[0] is not None and p[-1] is not None for p in phrases))
        self.assertEqual(kw.terms(kw.tokens("Moon Channeling: quillon tides"), frozenset(), phrases)[0],
                         ["quillon", "tides"])

    def test_names_in_japanese_letters_are_cut_out(self):
        single, phrases, strings = kw.name_drops("kiri-hana", "キリハナ Kiri Hana", "channeler")
        self.assertEqual(strings, ("キリハナ",))
        self.assertEqual(single, {"kiri", "hana"})               # no character pair alone
        uni, _ = kw.terms(kw.tokens(kw.cut_names("キリハナ 声の森 カリハ", strings)), single, phrases)
        self.assertEqual(uni, ["声の", "の森", "カリ", "リハ"])     # "リハ" of another word stays


class Furniture(unittest.TestCase):
    TITLES = ["Zorblax speaks: the tides", "Zorblax on stars", "Zorblax | moons", "quiet harbours"]

    def test_words_in_more_than_half_of_the_titles(self):
        furn = kw.furniture([kw.terms(kw.tokens(t)) for t in self.TITLES], share=0.5, min_titles=3)
        self.assertEqual(furn, {"zorblax": 0.75})

    def test_too_few_titles_have_no_furniture(self):
        self.assertEqual(kw.furniture([kw.terms(kw.tokens(t)) for t in self.TITLES], 0.5, 10), {})

    def test_exactly_half_is_not_furniture(self):
        titles = ["Zorblax tides", "Zorblax stars", "moons", "harbours"]
        self.assertEqual(kw.furniture([kw.terms(kw.tokens(t)) for t in titles], 0.5, 1), {})


class Statistics(unittest.TestCase):
    def test_tfidf_by_hand(self):
        # N = 2; df: x 1, y 2, z 1; idf x = z = ln(3/2) + 1 = 1.405465, y = ln(3/3) + 1 = 1
        # A: x (1 + ln 2) * 1.405465 = 2.379659, y 1; norm sqrt(2.379659^2 + 1) = 2.581236 -> 0.921907, 0.387411
        # B: y 1, z 1.405465; norm sqrt(1 + 1.405465^2) = 1.724915 -> 0.579739, 0.814802
        w, df, idf = kw.tfidf({"A": collections.Counter(x=2, y=1), "B": collections.Counter(y=1, z=1)})
        self.assertEqual(dict(df), {"x": 1, "y": 2, "z": 1})
        self.assertAlmostEqual(idf["x"], 1.405465, places=6)
        self.assertAlmostEqual(idf["y"], 1.0, places=9)
        self.assertAlmostEqual(w["A"]["x"], 0.921907, places=6)
        self.assertAlmostEqual(w["A"]["y"], 0.387411, places=6)
        self.assertAlmostEqual(w["B"]["y"], 0.579739, places=6)
        self.assertAlmostEqual(w["B"]["z"], 0.814802, places=6)

    def test_log_odds_by_hand_with_a_given_prior(self):
        # a0 = 2, prior w = v = 0.5 -> alpha 1 each; n_a = 4, n_b = 6
        # w: ln((3+1)/(4+2-3-1)) - ln((1+1)/(6+2-1-1)) = ln 2 - ln(1/3) = ln 6 = 1.791759
        #    var = 1/(3+1) + 1/(1+1) = 0.75, z = 1.791759 / 0.866025 = 2.068946
        # v: ln(2/4) - ln(6/2) = -ln 6; var = 1/2 + 1/6, z = -1.791759 / 0.816497 = -2.194448
        out = kw.log_odds(collections.Counter(w=3, v=1), collections.Counter(w=1, v=5), 2.0, {"w": 0.5, "v": 0.5})
        self.assertAlmostEqual(out["w"][0], math.log(6), places=9)
        self.assertAlmostEqual(out["w"][1], 2.068946, places=6)
        self.assertAlmostEqual(out["v"][0], -math.log(6), places=9)
        self.assertAlmostEqual(out["v"][1], -2.194448, places=6)

    def test_log_odds_by_hand_with_the_pooled_prior(self):
        # the default: prior = pooled shares (w 4/10, v 6/10), a0 = n_a = 4 -> alpha w 1.6, v 2.4
        # w: ln(4.6 / 3.4) - ln(2.6 / 7.4) = 1.348249; var = 1/4.6 + 1/2.6, z = 1.737679
        # v: ln(3.4 / 4.6) - ln(7.4 / 2.6) = -1.348249; var = 1/3.4 + 1/7.4, z = -2.057850
        out = kw.log_odds(collections.Counter(w=3, v=1), collections.Counter(w=1, v=5))
        self.assertAlmostEqual(out["w"][0], 1.348249, places=6)
        self.assertAlmostEqual(out["w"][1], 1.737679, places=6)
        self.assertAlmostEqual(out["v"][0], -1.348249, places=6)
        self.assertAlmostEqual(out["v"][1], -2.057850, places=6)

    def test_log_odds_rises_when_the_rate_rises(self):
        # invented counts: 3 of 64 now (4.7%) against 213 of 5,695 before (3.7%). A prior from other channels
        # (share 0.004554, a0 1000) drew the small tier to that share and called the word falling (z -4.18);
        # the channel's own pooled prior with a0 = 64: alpha 2.400417, delta 0.125453, z 0.287951
        a, b = collections.Counter(x=3, other=61), collections.Counter(x=213, other=5482)
        self.assertAlmostEqual(kw.log_odds(a, b, 1000.0, {"x": 0.004554, "other": 0.995446})["x"][1], -4.1798, places=4)
        d, z = kw.log_odds(a, b)["x"]
        self.assertAlmostEqual(d, 0.125453, places=6)
        self.assertAlmostEqual(z, 0.287951, places=6)

    def test_log_odds_sign_is_the_sign_of_the_rate_difference(self):
        rng = random.Random(11)
        for _ in range(300):
            a = collections.Counter({f"t{i}": rng.choice([0, 0, 1, 2, 5, 30]) for i in range(8)})
            b = collections.Counter({f"t{i}": rng.choice([0, 1, 3, 40, 400, 2000]) for i in range(8)})
            a, b = +a, +b
            if not a or not b:
                continue
            na, nb = sum(a.values()), sum(b.values())
            for scale in (None, 1.0, 1000.0):
                for t, (d, z) in kw.log_odds(a, b, scale).items():
                    diff = a[t] / na - b[t] / nb
                    if abs(diff) < 1e-12:
                        self.assertAlmostEqual(z, 0.0, places=9)
                    else:
                        self.assertEqual(z > 0, diff > 0, (t, a[t], na, b[t], nb, scale, z))

    def test_mantel_haenszel_by_hand(self):
        # channel 1: 1 of 2 titles now, 0 of 4 before: E = 2*1/6, V = 2*4*1*5 / (36*5) = 2/9
        # channel 2: 1 of 2 now, 1 of 2 before: E = 2*2/4 = 1, V = 2*2*2*2 / (16*3) = 1/3
        # O - E = 2 - 4/3 = 2/3, less 0.5 -> 1/6; z = (1/6) / sqrt(5/9) = 1 / (2 sqrt 5) = 0.223607
        self.assertAlmostEqual(kw.stratified_z([(1, 2, 0, 4), (1, 2, 1, 2)]), 0.223607, places=6)
        self.assertLess(kw.stratified_z([(0, 10, 50, 100), (0, 10, 40, 100)]), 0)   # absent now: never rising
        self.assertIsNone(kw.stratified_z([(0, 10, 0, 100)]))

    def test_fisher_by_hand(self):
        # 2 of 3 against 0 of 3: P(X=2) = C(2,2) C(4,1) / C(6,3) = 4/20; P(X=0) = 4/20, P(X=1) = 12/20
        rise, two = kw.fisher(2, 3, 0, 3)
        self.assertAlmostEqual(rise, 0.2)
        self.assertAlmostEqual(two, 0.4)
        self.assertEqual(kw.fisher(1, 0, 1, 3), (None, None))

    def test_benjamini_hochberg(self):
        self.assertEqual(kw.bh_threshold([0.01, 0.02, 0.03, 0.5]), 0.03)   # 0.03 <= .05 * 3/4
        self.assertEqual(kw.bh_threshold([0.2, 0.5]), 0.0)


class Blackouts(unittest.TestCase):
    def setUp(self):
        self.lex = kw.Lexicon(kw.FALLBACK, "built-in")

    def test_built_in_includes_and_excludes(self):
        m = self.lex.match
        self.assertEqual(m("Prepare for a BLACKOUT this winter"), {"blackout": "strong"})
        self.assertEqual(m("Will the power grid go down?"), {"power_grid": "strong"})
        self.assertEqual(m("The internet will go down"), {"internet_down": "strong"})
        self.assertEqual(m("Solar flare incoming!"), {"solar_flare": "weak"})
        self.assertEqual(m("The media blackout on disclosure"), {})          # overlaps the match
        self.assertEqual(m("Crystalline grid activation"), {})
        self.assertEqual(m("The crystalline grid down here"), {})
        self.assertEqual(m("Schumann resonance blackout today"), {})          # anywhere in the unit
        self.assertEqual(m("After the blackout I fainted"), {})
        self.assertEqual(m("Kin 79: Blue Magnetic Storm"), {})               # a calendar day, not the sun
        self.assertEqual(m("A magnetic storm hits"), {"solar_storm": "weak"})
        self.assertEqual(m("A media blackout, then a blackout of the power grid"),
                         {"blackout": "strong", "power_grid": "strong"})    # the second blackout stands
        self.assertEqual(m("Cyber risks to the quillon"), {"cyber_attack": "strong"})
        self.assertEqual(m("Ten Days of Darkness"), {"days_of_darkness": "strong"})
        self.assertEqual(m("10 days of darkness?"), {"days_of_darkness": "strong"})

    def test_underscores_do_not_hide_a_match(self):
        side = kw.Side(self.lex)
        side.add("t1", "", ["Solar_Flares_and_quillon"])
        self.assertEqual((side.strong, side.weak), (0, 1))

    def test_a_title_with_both_groups_counts_in_both(self):
        side = kw.Side(self.lex)
        side.add("t1", "", ["A Carrington event and a magnetic storm"])
        self.assertEqual((side.strong, side.weak), (1, 1))

    def test_theme_file_scopes_groups_and_anchored_patterns(self):
        data = {"include": [{"id": "grid_any", "topic": "power_grid", "pattern": r"\bgrid\b", "precision": 0.3},
                            {"id": "flash", "topic": "solar_flash", "pattern": r"\bsolar flash\b"},
                            {"id": "x_class", "topic": "solar", "pattern": r"\bx-class\b"},
                            {"id": "solar_cme", "topic": "space", "pattern": r"\bcoronal\b"},
                            {"id": "outage", "topic": "power_grid", "pattern": r"\boutages?\b"},
                            {"id": "dropped", "topic": "power_grid", "pattern": r"\bquillon\b", "use": False},
                            ["both", "power_grid", r"^(?=.*\bsolar\b)(?=.*\bpower\b)"]],
                "exclude": [{"id": "ley", "pattern": r"\bley lines?\b", "scope": ["grid_any"]}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blackouts.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            lex = kw.load_lexicon(path)
            by_precision = kw.load_lexicon(path, weak_precision=0.5)
        # weak: the file says so, or the id or topic names flares, storms or CMEs, or the topic is "solar" alone;
        # a "solar flash" stays strong; a low measured precision only with weak_precision
        self.assertEqual({x["id"]: x["group"] for x in lex.includes},
                         {"grid_any": "strong", "flash": "strong", "x_class": "weak", "solar_cme": "weak",
                          "outage": "strong", "both": "strong"})
        self.assertEqual({x["id"]: x["group"] for x in by_precision.includes}["grid_any"], "weak")
        self.assertEqual(lex.match("the grid and the ley lines"), {})
        self.assertEqual(lex.match("an outage near the ley lines"), {"outage": "strong"})
        self.assertEqual(lex.match("quillon"), {})
        side = kw.Side(lex)
        side.add("t1", "", ["Nothing here.", "The solar storm took the power."])
        self.assertEqual((side.strong, side.weak, side.units_matched), (1, 0, 1))

    def test_missing_theme_file_falls_back(self):
        self.assertTrue(kw.load_lexicon(Path("/nonexistent/blackouts.json")).source.startswith("built-in"))


class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "private"
        make_root(cls.root)
        cls.plan = Path(cls.tmp.name) / "plan"
        cls.argv = ["--root", str(cls.root), "--scope", "newest10", "--queue", "jobs/queue_newest10.csv",
                    "--history", "jobs/queue_youtube_all.csv", "--lexicon", str(Path(cls.tmp.name) / "none.json"),
                    "--furniture-min-titles", "3", "--plan-dir", str(cls.plan), "--publish-counts"]
        cls.result = kw.main(cls.argv)
        cls.out = cls.root / "analysis" / "keywords" / "newest10"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def terms_of(self, ch, kind):
        return {r["term"] for r in self.result["channels"][ch][kind]["tfidf"]}

    def test_kinds_stay_apart(self):
        zq = self.result["channels"]["zed-quorn"]
        self.assertEqual(sorted(zq), ["captions", "made", "source", "titles"])
        self.assertIn("quillberry", self.terms_of("zed-quorn", "source"))
        self.assertIn("zanthor", self.terms_of("zed-quorn", "made"))
        self.assertIn("mivvle", self.terms_of("zed-quorn", "captions"))
        for kind, word in (("source", "quillberry"), ("made", "zanthor"), ("captions", "mivvle")):
            for other in ("titles", "source", "made", "captions"):
                if other != kind:
                    self.assertNotIn(word, self.terms_of("zed-quorn", other), (kind, other))
        self.assertEqual(sorted(self.result["kinds"]), ["captions", "made", "source", "titles"])
        self.assertEqual(sorted(self.result["channels"]["mira-vantelle"]), ["titles"])

    def test_promotion_sentences_are_left_out_of_texts(self):
        src = self.result["channels"]["zed-quorn"]["source"]
        self.assertEqual((src["tier_sentences"], src["tier_sentences_dropped"]), (2, 1))
        self.assertNotIn("zentrova", self.terms_of("zed-quorn", "source"))
        self.assertEqual(src["blackouts"]["strong"]["tier"], 0)        # its "blackout" was the notice's
        self.assertEqual(kw.content(["Join us for a webinar on the quillon tides.", "The tides turn."]),
                         (["The tides turn."], 1))

    def test_post_headers_and_notices_are_cut(self):
        kept, dropped = kw.content(["Tuesday, March 3, 2026 The quillon tides turn.",
                                    "Quillon rivers. Posted by Zed Quorn at 10:15 AM",
                                    "MY NEW VIDEO IS OUT!!", "Saturday, May 30, 2015", "Quillon rivers rest."])
        self.assertEqual(kept, ["The quillon tides turn.", "Quillon rivers rest."])
        self.assertEqual(dropped, 3)

    def test_a_short_text_tier_is_not_tested(self):
        src = self.result["channels"]["zed-quorn"]["source"]
        self.assertIn("fewer than 500", src["log_odds_skipped"])
        self.assertNotIn("rising", src)
        rows = {(r["channel"], r["kind"]): r for r in kw.count_rows(self.result)}
        self.assertEqual(rows[("zed-quorn", "source")]["rising_significant"], "")
        self.assertNotEqual(rows[("zed-quorn", "titles")]["rising_significant"], "")

    def test_history_takes_the_tiers_tabs(self):
        self.assertEqual(self.result["history_tabs"], ["videos"])
        t = self.result["channels"]["zed-quorn"]["titles"]
        self.assertEqual((t["history_items"], t["blackouts"]["strong"]["history"]), (4, 1))   # the short left out
        opts = kw.parse_args(self.argv + ["--history-tabs", "all"])
        tier, hist = kw.read_csv(self.root / "jobs" / "queue_newest10.csv"), kw.read_csv(self.root / "jobs" / "queue_youtube_all.csv")
        allt = kw.analyse(self.root, "newest10", tier, hist, [], kw.Lexicon(kw.FALLBACK, "built-in"), opts)
        t = allt["channels"]["zed-quorn"]["titles"]
        self.assertEqual((t["history_items"], t["blackouts"]["strong"]["history"]), (5, 2))

    def test_tier_and_history_titles_and_furniture(self):
        t = self.result["channels"]["zed-quorn"]["titles"]
        self.assertEqual((t["tier_items"], t["history_items"]), (4, 4))
        self.assertIn("zorblax", t["furniture"])                 # in all 8 of the channel's titles
        self.assertNotIn("zorblax", self.terms_of("zed-quorn", "titles"))
        rising = {r["term"]: r for r in t["rising"]}
        self.assertEqual((rising["quillon"]["now"], rising["quillon"]["before"]), (2, 0))
        for r in t["rising"] + t["falling"]:                     # the sign follows the rates
            self.assertEqual(r["z"] > 0, r["per1000_now"] > r["per1000_before"], r["term"])
        self.assertNotIn("mira", self.terms_of("mira-vantelle", "titles"))    # the channel's own name

    def test_blackouts_by_kind(self):
        tb = self.result["channels"]["zed-quorn"]["titles"]["blackouts"]
        self.assertEqual((tb["strong"]["tier"], tb["strong"]["history"]), (1, 1))   # media blackout left out
        self.assertEqual((tb["weak"]["tier"], tb["weak"]["history"]), (1, 0))
        self.assertEqual(tb["strong"]["tier_per100"], 25.0)
        mv = self.result["channels"]["mira-vantelle"]["titles"]["blackouts"]
        self.assertEqual(mv["strong"]["tier"], 0)                # crystalline grid and Schumann left out
        sb = self.result["channels"]["zed-quorn"]["source"]["blackouts"]
        self.assertEqual((sb["strong"]["tier"], sb["strong"]["history"], sb["history_items"]), (0, 1, 1))

    def test_private_outputs(self):
        for name in ("zed-quorn.md", "mira-vantelle.md", "summary.md", "keywords.json", "counts.csv"):
            self.assertTrue((self.out / name).exists(), name)
        summary = (self.out / "summary.md").read_text(encoding="utf-8")
        self.assertIn("Used by most channels now", summary)
        self.assertIn("## Texts from the source", summary)

    def test_public_counts_hold_no_text(self):
        path = self.plan / "keywords_newest10.csv"
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(list(rows[0]), kw.COUNT_FIELDS)
        self.assertEqual({(r["channel"], r["kind"]) for r in rows},
                         {("mira-vantelle", "titles"), ("zed-quorn", "titles"), ("zed-quorn", "source"),
                          ("zed-quorn", "made"), ("zed-quorn", "captions")})
        words = {w.lower() for vs in (*TIER.values(), *HISTORY.values()) for v, t in vs for w in [v, *t.split()]}
        words |= {"quillberry", "zanthor", "mivvle", "pod-a", "web-b"}
        for r in rows:
            for k, v in r.items():
                if k in ("scope", "channel", "kind"):
                    continue
                if v != "":
                    float(v)                                      # a number, or blank
            for v in r.values():
                for w in words - {"zed-quorn", "mira-vantelle", "the", "a", "and", "on", "for", "is"}:
                    self.assertNotIn(w, v.lower().split(), (k, v))

    def test_output_is_repeatable_in_fresh_processes(self):
        # two processes with different hash seeds (not -I or -E, which would ignore PYTHONHASHSEED)
        outs = []
        for seed in ("1", "2"):
            out = Path(self.tmp.name) / f"seed{seed}"
            argv = [a for a in self.argv if a != "--publish-counts"] + ["--out", str(out)]
            env = {"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": seed}
            subprocess.run([sys.executable, "-s", str(PIPE / "keywords.py"), *argv], env=env, check=True,
                           capture_output=True, timeout=300)
            outs.append({p.name: p.read_bytes() for p in sorted(out.iterdir())})
        self.assertEqual(sorted(outs[0]), ["counts.csv", "keywords.json", "mira-vantelle.md", "summary.md",
                                           "zed-quorn.md"])
        self.assertEqual(outs[0], outs[1])
        self.assertEqual(outs[0]["keywords.json"], (self.out / "keywords.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
