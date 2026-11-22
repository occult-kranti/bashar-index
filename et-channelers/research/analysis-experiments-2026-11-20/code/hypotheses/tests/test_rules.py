"""Voice definitions, the adapter and its guard, verdict rules and the "not determinable" boundary. Synthetic data only."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import adapter  # noqa: E402
from hypotheses import constants as K  # noqa: E402
from hypotheses import features as F  # noqa: E402
from hypotheses import h1_rate, h2_hedging, h5_world_claims, h6_asks, h9_family  # noqa: E402
from hypotheses import simulate, stats, verdicts  # noqa: E402
from hypotheses import voice_sets as vs  # noqa: E402


def unit(i, label, label_b=None, own_broad=None, words=10):
    view = {"label": label, "label_b": label_b or label, "detail": "uncued_solo" if label == "V0" else "none", "cue": ["none", 0],
            "flags": [], "own_broad": (label == "V1") if own_broad is None else own_broad}
    return {"id": i, "first": 0, "last": 0, "n_words": words, "map": label, "small": view, "middle": view, "label": label,
            "label_b": view["label_b"], "own_broad": view["own_broad"]}


def voice_file(units, claimant="sole_speaker", synthetic=True, group="holdout"):
    return {"audio": "a1", "creator": "c1", "video_id": "v1", "group": group, "info": {"language": "en"}, "publisher_audio": False,
            "words": 100, "map": {"format": "solo", "claimant": claimant, "main_kind": "claimed_voice", "opening_end_unit": 2,
                                  "closing_start_unit": None}, "label_of_record": "middle", "units": units, "synthetic": synthetic}


class VoiceDefinitions(unittest.TestCase):
    def test_rule_b_and_own_definitions(self):
        record = adapter.parse_voice(voice_file([unit(1, "V1"), unit(2, "V0", own_broad=True), unit(3, "V2"), unit(4, "V1", "V2"),
                                                 unit(5, "V3")]))
        primary, _ = vs.sides(record, vs.definition())
        self.assertEqual(primary, ["own", "own", "claimed", "claimed", "claimed"])
        rule_a, _ = vs.sides(record, vs.definition(rule="A"))
        self.assertEqual(rule_a[3], "own")                        # an offer ends the claimed voice under rule A
        strict, _ = vs.sides(record, vs.definition(own="strict"))
        self.assertEqual(strict[1], None)                         # uncued solo speech is own voice only under the broad rule
        embodied, _ = vs.sides(record, vs.definition(claimed=("V2",)))
        self.assertEqual(embodied[4], None)                       # relayed is on neither side of H4's primary
        h4, _ = vs.sides(record, vs.primary_definition("H4"))     # registry 2026-11-21 04:55 (a): H4's primary is V2
        self.assertEqual(h4, embodied)
        h1, _ = vs.sides(record, vs.primary_definition("H1"))
        self.assertEqual(h1, primary)                             # H1 (and H6): V2 + V3

    def test_claimant_filter_and_spans(self):
        record = adapter.parse_voice(voice_file([unit(1, "V1", words=200), unit(2, "V1", words=150), unit(3, "V2", words=400)],
                                                claimant="guest_or_client"))
        self.assertIsNone(vs.sides(record, vs.definition()))
        record["claimant"] = "sole_speaker"
        side_list, _ = vs.sides(record, vs.definition())
        self.assertEqual(vs.spans(record, side_list), [("own", 0, 1, 350), ("claimed", 2, 2, 400)])


class Guard(unittest.TestCase):
    def test_real_records_are_refused_before_freeze_2(self):
        real = adapter.parse_voice(voice_file([unit(1, "V1")], synthetic=False))
        self.assertIsNotNone(adapter.freeze2_problem())
        with self.assertRaises(PermissionError):
            adapter.require_permission([real])
        adapter.require_permission([adapter.parse_voice(voice_file([unit(1, "V1")]))])   # synthetic passes

    def test_load_bundle_refuses_real_files(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "voice").mkdir()
            Path(folder, "voice", "a1.json").write_text(json.dumps(voice_file([unit(1, "V1")], synthetic=False)), encoding="utf-8")
            with self.assertRaises(PermissionError):
                adapter.load_bundle({"voice": str(Path(folder, "voice"))})


class Files(unittest.TestCase):
    def test_round_trip_through_label_files(self):
        bundle, files = simulate.cohort(5, 12, {"exact": True, "mu1": -0.1}, raw=True)
        with tempfile.TemporaryDirectory() as folder:
            paths = simulate.write_files(folder, files)
            loaded = adapter.load_bundle(paths)
        a = h1_rate.analyse(bundle, extras=False)
        b = h1_rate.analyse(loaded, extras=False)
        self.assertEqual(a["p"], b["p"])
        self.assertAlmostEqual(a["estimate"]["log_ratio"], b["estimate"]["log_ratio"])

    def test_contraction_counts(self):
        patterns = F.contraction_patterns([("it's", "it is"), ("don't", "do not"), ("i'm", "i am")])
        self.assertEqual(F.contraction_counts("It's fine, I am here and I don't know; it is so", patterns), (2, 2))
        self.assertEqual(F.syllables("channelled"), 2)
        self.assertEqual(F.syllables("wanted"), 2)
        self.assertGreaterEqual(F.syllables("energy"), 3)


class Boundary(unittest.TestCase):
    def test_h1_minimum(self):
        for n, determinable in ((11, False), (12, True)):
            b = simulate.cohort(stats.seed_for("t-h1", n), n, {"exact": True, "mu1": -0.2}, parts=("voice", "features"))
            result = h1_rate.analyse(b, extras=False)
            self.assertEqual(result["eligibility"]["creators"], n)
            self.assertEqual(result["determinable"], determinable)
            final, holm = verdicts.finalise({"H1": result})
            if determinable:
                self.assertEqual(final["H1"]["verdict"], "supported (model-coded)")
            else:
                self.assertEqual(final["H1"]["verdict"], f"not determinable: too few eligible creators ({n} of 12)")
                self.assertEqual(final["H1"]["holm_input_p"], 1.0)

    def test_h2_minimum_is_nine(self):
        yardstick, bands, parts = simulate.calibration_constants("H2")
        full = simulate.cohort(stats.seed_for("t-h2"), 12, {"exact": True, "beta": -0.7}, parts=("voice", "forecasts"))
        by_creator = h2_hedging.statements_by_creator(full, bands=bands, parts=parts)
        usable = [c for c in sorted(by_creator) if len(by_creator[c]) >= K.H2_MIN_STATEMENTS and h2_hedging.creator_d(by_creator[c])[0] is not None]
        for n, determinable in ((8, False), (9, True)):
            b = dict(full, recordings=[item for item in full["recordings"] if item["creator"] in usable[:n]])
            result = h2_hedging.analyse(b, bands=bands, parts=parts, extras=False, permutations=99, draws=99)
            self.assertEqual(result["eligibility"]["creators"], n)
            self.assertEqual(result["determinable"], determinable)
            self.assertTrue(result["registered_version"]["determinable"])        # the registered minimum was 8
            final, holm = verdicts.finalise({"H2": result})
            if not determinable:
                # Changed by registry 2026-11-21 04:55 (g): a version that is not determinable makes the result "not
                # determinable" (it read "versions differ" before); the assertions are stricter than before: the kind,
                # the version named in the reason, p = 1 in Holm and the uninformative flag.
                self.assertTrue(final["H2"]["verdict"].startswith("not determinable in the amended version: too few eligible "
                                                                  "creators (8 of 9)"), final["H2"]["verdict"])
                self.assertEqual(final["H2"]["verdict_kind"], "not determinable")
                self.assertEqual(holm["H2"]["input_p"], 1.0)
                self.assertTrue(final["H2"]["uninformative"])

    def test_h6_needs_eight_creators_with_an_ask(self):
        b = simulate.cohort(stats.seed_for("t-h6"), 12, {"exact": True}, parts=("voice", "asks"))
        creators = sorted({item["creator"] for item in b["recordings"]})
        for item in b["recordings"]:
            if item["creator"] in creators[7:]:
                item["asks"]["asks"] = []
        result = h6_asks.analyse(b, extras=False, draws=99)
        with_ask = result["eligibility"]["creators_with_T_at_least_1"]
        self.assertLessEqual(with_ask, 7)
        self.assertFalse(result["determinable"])
        final, holm = verdicts.finalise({"H6": result})
        self.assertIn(f"creators with an ask {with_ask} of 8", final["H6"]["verdict"])
        self.assertEqual(holm["H6"]["input_p"], 1.0)
        self.assertTrue(final["H6"]["uninformative"])

    def test_h6_oe_null_mean_is_zero_by_construction(self):
        # with no voice effect a / T has expectation s for every T (conditional binomial), whatever the exposure
        totals = [{"a": a, "b": t - a, "wc": 300, "wo": 700} for t in (1, 2, 5) for a in range(t + 1)]
        weights = [stats.math.comb(t, a) * 0.3 ** a * 0.7 ** (t - a) for t in (1, 2, 5) for a in range(t + 1)]
        oe = h6_asks.oe_values(totals)
        self.assertAlmostEqual(sum(w * v for w, v in zip(weights, oe)), 0.0, places=12)

    def test_h5_margin_rule(self):
        row = {"WA": 12, "PA": 0, "WB": 3, "PB": 9}
        self.assertTrue(h5_world_claims._passes(row, 10, per_side=False))
        self.assertFalse(h5_world_claims._passes(row, 10, per_side=True))

    def test_h9_minimum_and_reference(self):
        for n, determinable in ((7, False), (8, True)):
            b = simulate.cohort(stats.seed_for("t-h9", n), n, {"exact": True, "h9_content": 0.12}, n_seen=40, parts=simulate.PARTS["H9"])
            elig = h9_family.eligible(b)
            self.assertEqual(elig["creators"], n)
            self.assertEqual(elig["determinable"], determinable)

    def test_below_reliability_floor(self):
        b = simulate.cohort(stats.seed_for("t-gate"), 12, {"exact": True, "mu1": -0.2}, parts=("voice", "features"))
        result = h1_rate.analyse(b, extras=False)
        final, holm = verdicts.finalise({"H1": result}, gates={"H1": {"passed": False, "detail": "kappa"}})
        # registry 2026-11-21 01:15 and 01:30, A10.5: "not run for want of an instrument", p = 1, uninformative
        self.assertTrue(final["H1"]["verdict"].startswith("not run for want of an instrument: below the reliability floor"))
        self.assertEqual(final["H1"]["verdict_kind"], "not determinable")
        self.assertTrue(final["H1"]["uninformative"])
        self.assertIsNone(final["H1"]["verdict_statement"])
        self.assertEqual(holm["H1"]["input_p"], 1.0)

    def test_sentences(self):
        self.assertIn(K.PUNCTUATION_SENTENCE, verdicts.sentences("H4"))
        self.assertNotIn(K.PUNCTUATION_SENTENCE, verdicts.sentences("H2"))
        self.assertIn(K.MODEL_CODED, verdicts.sentences("H9"))
        for name in ("H1", "H2", "H4", "H5", "H6", "H9"):
            self.assertNotIn("validat", " ".join(verdicts.sentences(name)).lower())


class Determinism(unittest.TestCase):
    def test_same_seed_same_result(self):
        one = simulate.task(("H6", "null", 12, 1.0, 0, 2))["rows"]
        two = simulate.task(("H6", "null", 12, 1.0, 0, 2))["rows"]
        self.assertEqual(json.dumps(one, sort_keys=True), json.dumps(two, sort_keys=True))

    def test_parallel_equals_serial(self):
        from hypotheses import progress
        tasks = [("H5", "null", 12, 0.0, i, 1) for i in range(3)]
        serial, _ = progress.parallel_map(simulate.task, tasks, 1, "test")
        parallel, _ = progress.parallel_map(simulate.task, tasks, 3, "test")
        strip = lambda results: json.dumps([r["rows"] for r in results], sort_keys=True)
        self.assertEqual(strip(serial), strip(parallel))


if __name__ == "__main__":
    unittest.main()
