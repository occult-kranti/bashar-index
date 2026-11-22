"""The lead's decisions of 2026-11-21 12:52 ("Hypothesis code, decisions after the fifth verification"), items (1), (2) and
(4): H6's clusters chain asks within 5 units of each other (H6_CLUSTER_WINDOW), with a 10-unit sensitivity row, the
statement that dependence beyond the window is not modelled, the battery's null_gapped scenario and the levels of the
amended p in the burst, gapped, sparse-low-share and plain cases; asks of one class whose unit ranges overlap count once
(in the adapter; the instrument is frozen), with their count in counts.json before outcomes; and a bundle whose feature
files carry more than one feature_version is refused. Constructed numbers and synthetic records only: no test opens the
production label tree."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import adapter, common, report, run, verdicts  # noqa: E402
from hypotheses import constants as K  # noqa: E402
from hypotheses import h6_asks, simulate, stats  # noqa: E402
from hypotheses import voice_sets as vs  # noqa: E402

LEVEL = K.ALPHA / K.HOLM_M


def ask(first, last, kind="K1", final="ask", final_class="same", fallback=None):
    """One parsed ask as adapter.parse_asks gives it."""
    return {"first_unit": first, "last_unit": last, "class": kind, "final": final,
            "final_class": (kind if final == "ask" else None) if final_class == "same" else final_class,
            "final_from": None if final == "unchecked" else "middle", "fallback": fallback}


# ---------------------------------------------------------------- (1) the cluster window

class ClusterWindow(unittest.TestCase):
    def test_the_constants(self):
        self.assertEqual(h6_asks.H6_CLUSTER_WINDOW, 5)
        self.assertEqual(h6_asks.H6_SENSITIVITY_WINDOW, 10)

    def test_asks_within_five_units_chain(self):
        own = lambda *units: [(unit, unit, "own") for unit in units]
        self.assertEqual(h6_asks.clusters_of(own(2, 4)), [2])                     # one unit between them
        self.assertEqual(h6_asks.clusters_of(own(1, 6)), [2])                     # 5 units apart
        self.assertEqual(h6_asks.clusters_of(own(1, 7)), [1, 1])                  # 6 units apart
        self.assertEqual(h6_asks.clusters_of(own(1, 6, 11, 17)), [3, 1])          # chaining, then a gap of 6
        self.assertEqual(h6_asks.clusters_of([(3, 5, "own"), (10, 10, "claimed")]), [2])     # from the range's last unit
        self.assertEqual(h6_asks.clusters_of([(3, 5, "own"), (11, 11, "claimed")]), [1, 1])
        self.assertEqual(h6_asks.clusters_of(own(17, 1, 11, 6)), [3, 1])          # the input's order does not matter
        # an ask on neither side links and is not counted; a cluster of such asks only is dropped
        self.assertEqual(h6_asks.clusters_of([(1, 1, "own"), (5, 5, None), (9, 9, "claimed"), (30, 30, None)]), [2])
        # the rule of 11:08 (1) is the window of 1 unit; the sensitivity row's is 10
        self.assertEqual(h6_asks.clusters_of(own(2, 4), 1), [1, 1])
        self.assertEqual(h6_asks.clusters_of([(7, 7, "claimed"), (8, 9, "own"), (10, 10, "own")], 1), [3])
        self.assertEqual(h6_asks.clusters_of(own(1, 11), 10), [2])
        self.assertEqual(h6_asks.clusters_of(own(1, 12), 10), [1, 1])
        self.assertEqual(h6_asks.clusters_of([(4, 4, "own"), (4, 4, "claimed")], 0), [2])     # the same range, window 0
        with self.assertRaises(ValueError):
            h6_asks.clusters_of(own(1), -1)

    def test_the_rows_follow_the_window_and_nothing_else_changes(self):
        b = simulate.cohort(stats.seed_for("t-1252-rows"), 17, simulate.experiment_cfg("H6", 1.0, "null_gapped"),
                            parts=simulate.PARTS["H6"])
        held = common.confirmatory(b)
        tables = {window: h6_asks.creator_tables(held, vs.definition(), window=window) for window in (1, 5, 10)}
        self.assertEqual(h6_asks.creator_tables(held, vs.definition()), tables[5])          # the default is 5
        counted = {window: 0 for window in tables}
        for window, table in tables.items():
            for creator, rows in table.items():
                for row, other in zip(rows, tables[1][creator]):
                    self.assertEqual(sum(row["clusters"]), row["a"] + row["b"])
                    self.assertEqual((row["a"], row["b"], row["wc"], row["wo"]), (other["a"], other["b"], other["wc"], other["wo"]))
                    counted[window] += len(row["clusters"])
        self.assertGreater(counted[1], counted[5])                     # the gapped bursts split under 11:08's rule
        self.assertGreaterEqual(counted[5], counted[10])


class ResultStatesTheWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = simulate.cohort(stats.seed_for("t-1252-result"), 12, simulate.experiment_cfg("H6", 1.0, "null_gapped"),
                                     parts=simulate.PARTS["H6"])
        cls.result = h6_asks.analyse(cls.bundle, label=("t-1252",), draws=99, reference_draws=999)

    def test_the_result_carries_the_rule_and_the_statement(self):
        result = self.result
        self.assertEqual(result["cluster_rule"]["window_units"], 5)
        self.assertEqual(result["cluster_rule"]["sensitivity_window_units"], 10)
        self.assertEqual(result["cluster_rule"]["dependence_beyond_the_window"], "not modelled")
        self.assertEqual(result["notes"], [h6_asks.CLUSTER_STATEMENT])
        self.assertIn("beyond the window", h6_asks.CLUSTER_STATEMENT)
        self.assertIn("is not modelled", h6_asks.CLUSTER_STATEMENT)
        self.assertEqual(result["eligibility"]["cluster_window_units"], 5)

    def test_the_sensitivity_row(self):
        result = self.result
        key = "cluster window of 10 units (sensitivity row, registry 2026-11-21 12:52 (1))"
        row = result["secondary"][key]
        self.assertIsNone(row["verdict"])
        self.assertEqual((row["window_units"], row["primary_window_units"]), (10, 5))
        self.assertEqual(row["p_signflip_oe"], result["p_parts"]["signflip_oe"])          # the same sign-flip half
        self.assertEqual(row["p"], max(row["p_cluster_conditional"], row["p_signflip_oe"]))
        again = h6_asks.window_p(common.confirmatory(self.bundle), vs.definition(), 10, ("t-1252",),
                                 result["p_parts"]["signflip_oe"], 999)
        self.assertEqual(row["p_cluster_conditional"], again["p_cluster_conditional"])
        self.assertLessEqual(row["clusters"], result["p_parts"]["clusters"])
        self.assertIn("no verdict", row["note"])

    def test_the_report_shows_it(self):
        final, holm = verdicts.finalise({"H6": self.result})
        built = report.build({"H6": self.result}, final, holm, {"title": "t"})
        self.assertEqual(built["hypotheses"]["H6"]["versions"]["amended"]["notes"], [h6_asks.CLUSTER_STATEMENT])
        text = report.markdown(built)
        self.assertIn("Secondary estimate 'cluster window of 10 units", text)
        self.assertIn("dependence of asks beyond 10 units is not modelled either", text)


# ---------------------------------------------------------------- (1) the battery's gapped scenario

class GappedScenario(unittest.TestCase):
    def test_the_plan_and_the_settings(self):
        for n in (12, 17):
            self.assertIn(("H6", "null_gapped", n, 1.0, 30), simulate.plan(quick=True))
            self.assertIn(("H6", "null_gapped", n, 1.0, 2000), simulate.plan())
        cfg = simulate.experiment_cfg("H6", 1.0, "null_gapped")
        self.assertEqual((cfg["claimed_fraction"], cfg["bursts_per_creator"], cfg["burst_sizes"], cfg["burst_gaps"]),
                         ((0.25, 0.45), (1, 1), (2, 4), (1, 3)))
        for scenario in ("null", "null_heterogeneous", "null_sparse_low_share", "null_burst"):
            self.assertNotIn("burst_gaps", simulate.experiment_cfg("H6", 1.0, scenario))
        self.assertEqual(simulate.H6_NULL_SCENARIOS[-1], "null_gapped")

    def test_the_generator(self):
        cfg = simulate.experiment_cfg("H6", 1.0, "null_gapped")
        b = simulate.cohort(stats.seed_for("t-1252-gapped"), 17, cfg, parts=simulate.PARTS["H6"])
        per_creator, gaps = {}, []
        for item in b["recordings"]:
            asks = item["asks"]["asks"]
            per_creator.setdefault(item["creator"], []).extend(asks)
            units = sorted(a["first_unit"] for a in asks)
            gaps += [later - earlier for earlier, later in zip(units, units[1:])]
        self.assertEqual(len(per_creator), 17)
        self.assertTrue(all(2 <= len(asks) <= 4 for asks in per_creator.values()))         # one burst a creator
        self.assertTrue(gaps and all(1 <= gap <= 3 for gap in gaps))
        self.assertGreater(sum(1 for gap in gaps if gap >= 2), len(gaps) / 2)              # mostly not adjacent
        tables = h6_asks.creator_tables(common.confirmatory(b), vs.primary_definition("H6"))
        shares = [row["wc"] / (row["wc"] + row["wo"]) for rows in tables.values() for row in rows]
        self.assertLess(max(shares), 0.5)
        self.assertGreater(min(shares), 0.15)

    def test_a_gapped_burst_lies_in_one_voice(self):
        r = simulate.random.Random(11)
        habits = simulate.creator_habits(r, simulate.DEFAULT)
        cfg = dict(simulate.DEFAULT, exact=True, **simulate.SCENARIO_CFG["null_gapped"])
        recordings = []
        for index in range(4):
            voice, _, truth, _ = simulate.voice_and_features(r, "h000", "holdout", index, "both", habits, cfg)
            recordings.append((voice, truth, "both"))
        bursts = mixed = 0
        for _ in range(60):
            records = simulate.burst_asks_records(r, recordings, cfg)
            placed = [(record, voice, truth) for record, (voice, truth, _) in zip(records, recordings) if record["asks"]]
            self.assertEqual(len(placed), 1)                                   # one burst, in one recording
            record, voice, truth = placed[0]
            side = {unit["id"]: s for unit, s in zip(voice["units"], truth)}
            bursts += 1
            mixed += len({side[a["first_unit"]] for a in record["asks"]}) > 1
        self.assertEqual(mixed, 0)

    def test_the_rows_carry_the_window_comparisons(self):
        rows = simulate.task(("H6", "null_gapped", 12, 1.0, 0, 2))["rows"]
        for row in rows:
            for key, _ in simulate.H6_COMPARISON_PS:
                self.assertIn(key, row)
            if row["determinable"]:
                self.assertEqual(row["p"], max(row["p_cluster_conditional"], row["p_signflip_oe"]))
                self.assertGreaterEqual(row["p_amended_window_1_1108"], row["p_signflip_oe"])
                self.assertGreaterEqual(row["p_amended_window_10"], row["p_signflip_oe"])
        table = simulate.summarise("H6", "null_gapped", 12, 1.0, rows, None, 0.0)
        for name in ("amended_window_1_1108", "amended_window_10", "cluster_conditional", "signflip_oe"):
            self.assertIn("reject_0.005_" + name, table)
        text = run.simulation_markdown({"workers": 1, "seconds": 1, "progress": {}, "experiments": [table], "boundary": []})
        self.assertIn("window 1 (11:08)", text)
        self.assertIn("window 10", text)
        self.assertIn("null_gapped", text)


class LevelsOfTheAmendedP(unittest.TestCase):
    """Exact enumeration (simulate.h6_cluster_levels) with the analysis's 99,999 draws: the amended p in the burst, gapped,
    sparse-low-share and plain cases."""

    @classmethod
    def setUpClass(cls):
        cls.rows = {row["case"]: row for row in simulate.h6_cluster_reference_levels()}
        cls.kinds = {row["kind"] for row in cls.rows.values()}

    def test_every_kind_is_in_the_table(self):
        self.assertEqual(self.kinds, {"burst", "gapped", "gapped_beyond_window", "sparse_low_share", "plain"})

    def test_the_amended_p_holds_the_level_within_the_window(self):
        for row in self.rows.values():
            if row["kind"] == "gapped_beyond_window" or "the rule of 11:08" in row["case"]:
                continue
            for alpha in ("0.005", "0.05"):
                self.assertLessEqual(row["amended_" + alpha], float(alpha) + 1e-12, row["case"])
                self.assertLessEqual(row["cluster_" + alpha], float(alpha) + 1e-12, row["case"])

    def test_the_fifth_verifications_cases(self):
        """11:08's rule (window 1) sees the gapped bursts as single asks, and both halves fail (the verifier's figures);
        the window of 5 holds."""
        name = "17 creators, one burst of 3 asks 2 units apart, s = 0.3"
        old, new = self.rows[name + " (window 1, the rule of 11:08)"], self.rows[name + " (window 5)"]
        self.assertAlmostEqual(old["amended_0.005"], 0.0193, places=4)
        self.assertAlmostEqual(old["amended_0.05"], 0.0774, places=4)
        self.assertLess(new["amended_0.005"], 0.005)
        self.assertAlmostEqual(self.rows["17 creators, one burst of 3 asks 3 units apart, s = 0.4 (window 1, the rule of 11:08)"]
                               ["amended_0.005"], 0.0123, places=4)
        self.assertAlmostEqual(self.rows["12 creators, one burst of 3 asks 2 units apart, s = 0.3 (window 1, the rule of 11:08)"]
                               ["amended_0.005"], 0.0138, places=4)
        self.assertAlmostEqual(self.rows["9 creators at s = 0.3 and 8 at s = 0.5, one burst of 3 asks 2 units apart "
                                         "(window 1, the rule of 11:08)"]["amended_0.005"], 0.0113, places=4)

    def test_beyond_the_window_is_not_modelled(self):
        """A burst whose asks lie 6 units apart is seen as single asks at the window of 5 (the amended p over-rejects:
        the dependence the result says is not modelled); the 10-unit sensitivity row joins it."""
        name = "17 creators, one burst of 3 asks 6 units apart, s = 0.3"
        self.assertGreater(self.rows[name + " (window 5: beyond it)"]["amended_0.005"], 0.015)
        self.assertLess(self.rows[name + " (window 10, the sensitivity row)"]["amended_0.005"], 0.005)

    def test_the_gapped_recording(self):
        self.assertEqual(simulate.h6_gapped_recording(0.3, (0, 2, 4)), (0.3, [3], [3]))
        self.assertEqual(simulate.h6_gapped_recording(0.3, (0, 2, 4), 1), (0.3, [3], [1, 1, 1]))
        self.assertEqual(simulate.h6_gapped_recording(0.3, (0, 2, 9)), (0.3, [3], [2, 1]))
        with self.assertRaises(ValueError):
            simulate.h6_cluster_levels([[(0.3, [3], [1, 1])]])
        # without seen sizes the true clusters are the seen ones (the cases of 11:08)
        same = simulate.h6_cluster_levels([[(0.3, [3])]] * 6, draws=999)
        stated = simulate.h6_cluster_levels([[(0.3, [3], [3])]] * 6, draws=999)
        self.assertEqual(same, stated)


# ---------------------------------------------------------------- (2) asks of one class on overlapping ranges

class OverlappingAsksCountOnce(unittest.TestCase):
    def test_the_merge(self):
        merged, counts = adapter.merge_overlapping_asks([ask(10, 10), ask(10, 11)])
        self.assertEqual(len(merged), 1)
        self.assertEqual((merged[0]["first_unit"], merged[0]["last_unit"], merged[0]["final"], merged[0]["final_class"],
                          merged[0]["merged_from"]), (10, 11, "ask", "K1", 2))
        self.assertEqual((counts["groups"], counts["groups_on_overlapping_ranges"], counts["groups_on_one_range"],
                          counts["groups_with_two_or_more_final_asks"], counts["asks_merged_away"]), (1, 1, 0, 1, 1))
        self.assertEqual(counts["groups_by_class"], {"K1": 1})
        # the same range twice (two offers of one class) counts once too (CHOICE)
        merged, counts = adapter.merge_overlapping_asks([ask(4, 5), ask(4, 5)])
        self.assertEqual((len(merged), counts["groups_on_one_range"]), (1, 1))
        # overlaps chain; adjacent ranges do not overlap; other classes stay apart; an ask without a class is never merged
        merged, counts = adapter.merge_overlapping_asks([ask(10, 11), ask(11, 12), ask(12, 12), ask(13, 13), ask(12, 12, "K2"),
                                                         dict(ask(12, 12), **{"class": None, "final_class": None})])
        self.assertEqual([(a["first_unit"], a["last_unit"], a["class"]) for a in merged],
                         [(10, 12, "K1"), (13, 13, "K1"), (12, 12, "K2"), (12, 12, None)])
        self.assertEqual((counts["groups"], counts["asks_as_filed"], counts["asks_counted"]), (1, 6, 4))
        nothing, counts = adapter.merge_overlapping_asks([ask(1, 1), ask(3, 4)])
        self.assertEqual((len(nothing), counts["groups"]), (2, 0))
        self.assertNotIn("merged_from", nothing[0])

    def test_the_merged_verdict(self):
        """The merged ask counts exactly when one of its members would, under the primary rule and the fallback row."""
        fallback_ask = {"verdict": "ask", "class": "K1"}
        cases = [([ask(5, 5, final="not_ask"), ask(5, 6)], "ask", None),
                 ([ask(5, 5, final="not_ask"), ask(5, 6, final="unchecked", fallback=fallback_ask)], "unchecked", fallback_ask),
                 ([ask(5, 5, final="unchecked", fallback={"verdict": "not_ask", "class": None}),
                   ask(5, 6, final="unchecked", fallback=fallback_ask)], "unchecked", fallback_ask),
                 ([ask(5, 5, final="unclear"), ask(5, 6, final="not_ask")], "unclear", None),
                 ([ask(5, 5, final="ask"), ask(5, 6, final="unchecked", fallback=fallback_ask)], "ask", None)]
        for members, final, fallback in cases:
            merged, _ = adapter.merge_overlapping_asks(members)
            self.assertEqual((merged[0]["final"], merged[0]["fallback"]), (final, fallback), members)

    def test_parse_and_count_per_group(self):
        data = {"audio": "a1", "creator": "c1", "group": "holdout", "synthetic": True,
                "asks": [{"first_unit": 3, "last_unit": 3, "class": "K1", "final": "ask", "final_class": "K1"},
                         {"first_unit": 3, "last_unit": 4, "class": "K1", "final": "ask", "final_class": "K1"},
                         {"first_unit": 9, "last_unit": 9, "class": "K1", "final": "ask", "final_class": "K1"}]}
        parsed = adapter.parse_asks(data)
        self.assertEqual(len(parsed["asks"]), 2)
        self.assertEqual(parsed["ask_overlaps"]["groups"], 1)
        counted = adapter.ask_overlap_counts({"recordings": [{"group": "holdout", "asks": parsed},
                                                             {"group": "seen", "asks": adapter.parse_asks(dict(data, group="seen"))},
                                                             {"group": "seen", "asks": None}]})
        self.assertEqual(sorted(counted), ["holdout", "seen"])
        self.assertEqual((counted["holdout"]["ask_files"], counted["holdout"]["ask_files_with_a_merge"],
                          counted["holdout"]["asks_as_filed"], counted["holdout"]["asks_counted"]), (1, 1, 3, 2))

    def test_every_quantity_counts_them_once(self):
        """Hold-out asks files whose K1 asks span two units (u..u+1), against the same files with each such ask filed
        twice more, as u..u and as u+1..u+1 (overlapping ranges inside its own, as two find draws can return them): T,
        a, b, the MH ratio, the clusters, the unchecked count and every p are the same."""
        base = simulate.cohort(stats.seed_for("t-1252-twice"), 12, {"exact": True, "rr": 0.5}, parts=("voice", "asks"), raw=True)[1]
        planted = 0
        for record in base["asks"]:
            for item in record["asks"]:
                if item["class"] == "K1":
                    item["last_unit"] = item["first_unit"] + 1
        doubled = json.loads(json.dumps(base))
        for record in doubled["asks"]:
            if record["group"] != "holdout":
                continue
            extra = []
            for item in record["asks"]:
                if item["class"] == "K1":
                    extra += [dict(item, last_unit=item["first_unit"]), dict(item, first_unit=item["last_unit"])]
                    planted += 1
            record["asks"] += extra
        self.assertGreater(planted, 10)

        def bundle(files):
            voice = [adapter.parse_voice(v) for v in files["voice"]]
            return adapter.bundle(voice=voice, asks=[adapter.parse_asks(a) for a in files["asks"]])
        one, two = bundle(base), bundle(doubled)
        r1 = h6_asks.analyse(one, label=("t-1252-twice",), draws=99, reference_draws=999)
        r2 = h6_asks.analyse(two, label=("t-1252-twice",), draws=99, reference_draws=999)
        for key in ("p", "estimate", "creator_values", "p_parts", "unchecked_asks", "asks_on_neither_side", "intervals",
                    "secondary"):
            self.assertEqual(r1[key], r2[key], key)
        self.assertEqual(r1["registered_version"]["p"], r2["registered_version"]["p"])
        counted = h6_asks.eligible(two, vs.primary_definition("H6"))["ask_overlaps_counted_once"]["holdout"]
        before = h6_asks.eligible(one, vs.primary_definition("H6"))["ask_overlaps_counted_once"]["holdout"]
        self.assertEqual(counted["asks_counted"], before["asks_counted"])
        self.assertEqual(counted["asks_merged_away"] - before["asks_merged_away"], 2 * planted)
        # every K1 ask of the base (after its own merges: two asks on one or adjacent units) is now one group
        self.assertEqual(counted["groups"], planted - before["asks_merged_away"])
        self.assertEqual(counted["groups_on_overlapping_ranges"], counted["groups"])

    def test_counts_json_carries_them_before_outcomes(self):
        """Through the label files and the adapter, as run.analyse writes counts.json (run.counts) before any outcome."""
        b, files = simulate.cohort(stats.seed_for("t-1252-counts"), 12, {"exact": True}, n_seen=3, parts=("voice", "asks"),
                                   raw=True)
        record = next(r for r in files["asks"] if r["group"] == "holdout" and any(a["class"] == "K1" for a in r["asks"]))
        first = next(a for a in record["asks"] if a["class"] == "K1")
        record["asks"].append(dict(first, last_unit=first["last_unit"] + 1))
        with tempfile.TemporaryDirectory() as folder:
            paths = simulate.write_files(Path(folder) / "labels", files)
            loaded = adapter.load_bundle({"voice": paths["voice"], "asks": paths["asks"]}, K.ASR_MODEL_REQUIRED)
        counted = run.counts(loaded, {})["H6"]["ask_overlaps_counted_once"]
        direct = adapter.ask_overlap_counts(adapter.bundle(voice=[adapter.parse_voice(v) for v in files["voice"]],
                                                           asks=[adapter.parse_asks(a) for a in files["asks"]]))
        self.assertEqual(counted, direct)
        self.assertGreaterEqual(counted["holdout"]["groups_on_overlapping_ranges"], 1)
        self.assertIn("seen", counted)


# ---------------------------------------------------------------- (4) one feature_version a bundle

class OneFeatureVersion(unittest.TestCase):
    def features(self, *versions):
        return [adapter.parse_features({"audio": f"a{i}", "creator": "c1", "group": "holdout", "units": [], "synthetic": True,
                                        **({} if version is None else {"feature_version": version})})
                for i, version in enumerate(versions)]

    def test_a_mix_is_refused_naming_the_versions(self):
        with self.assertRaises(ValueError) as caught:
            adapter.bundle(features=self.features("features-3", "features-4", "features-4"))
        self.assertIn("features-3 (1 file)", str(caught.exception))
        self.assertIn("features-4 (2 files)", str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            adapter.bundle(features=self.features("features-4", None))
        self.assertIn(adapter.NO_FEATURE_VERSION, str(caught.exception))
        self.assertEqual(adapter.require_one_feature_version(self.features("features-4", "features-4")), {"features-4": 2})
        adapter.bundle(features=self.features(None, None))
        adapter.bundle()

    def test_the_loader_refuses_a_mixed_folder(self):
        _, files = simulate.cohort(stats.seed_for("t-1252-versions"), 3, {"exact": True}, parts=("voice", "features"), raw=True)
        files["features"][1]["feature_version"] = "features-0"
        with tempfile.TemporaryDirectory() as folder:
            paths = simulate.write_files(Path(folder) / "labels", files)
            with self.assertRaises(ValueError) as caught:
                adapter.load_bundle({"voice": paths["voice"], "features": paths["features"]}, K.ASR_MODEL_REQUIRED)
        self.assertIn("features-0 (1 file)", str(caught.exception))
        self.assertIn("more than one feature_version", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
