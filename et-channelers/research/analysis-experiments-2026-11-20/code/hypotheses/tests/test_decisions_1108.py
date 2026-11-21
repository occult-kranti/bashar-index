"""The lead's decision of 2026-11-21 11:08 ("Hypothesis code, decisions after the fourth verification"), item (1): H6's
amended p is the larger of the cluster-level conditional Monte Carlo p and the sign-flip p of OE; clusters are asks in the
same checked unit range or in adjacent units; 99,999 draws in the analysis; the battery's null_burst scenario; the levels
on constructed numbers; H6's detectable-effect note from the battery's power; the battery markdown with the replaced
references. Constructed numbers and synthetic records only: no test opens the production label tree."""
import math
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import a10_checks, common, run  # noqa: E402
from hypotheses import constants as K  # noqa: E402
from hypotheses import h6_asks, simulate, stats, verdicts  # noqa: E402
from hypotheses import voice_sets as vs  # noqa: E402

LEVEL = K.ALPHA / K.HOLM_M


def recording(a, b, s, clusters=None, words=1000):
    """A recording row of h6_asks.creator_tables with claimed share s of its words in the two voices."""
    row = {"a": a, "b": b, "wc": words * s, "wo": words * (1 - s), "unchecked": 0, "neither": 0}
    if clusters is not None:
        row["clusters"] = list(clusters)
    return row


# ---------------------------------------------------------------- the clusters

class Clusters(unittest.TestCase):
    def test_same_range_overlapping_and_adjacent_units_chain(self):
        """Since 12:52 (1) the window is 5 units (tests/test_decisions_1252.py); 11:08's rule is the window of 1."""
        self.assertEqual(h6_asks.clusters_of([]), [])
        self.assertEqual(h6_asks.clusters_of([(4, 4, "own"), (4, 4, "claimed")]), [2])          # one checked range
        self.assertEqual(h6_asks.clusters_of([(3, 5, "own"), (5, 6, "own")]), [2])               # overlapping ranges
        self.assertEqual(h6_asks.clusters_of([(7, 7, "claimed"), (8, 9, "own"), (10, 10, "own")]), [3])   # adjacent
        self.assertEqual(h6_asks.clusters_of([(2, 2, "own"), (4, 4, "own")], 1), [1, 1])         # a unit between them
        self.assertEqual(h6_asks.clusters_of([(2, 2, "own"), (4, 4, "own")]), [2])               # within 5 units (12:52)
        # order of the input does not matter; an ask on neither side links clusters and is not counted; a cluster of
        # asks on neither side only is dropped
        self.assertEqual(h6_asks.clusters_of([(12, 12, "claimed"), (9, 9, None), (10, 11, None), (8, 8, "own"),
                                              (20, 20, None)]), [2])
        self.assertEqual(h6_asks.clusters_of([(1, 1, "own"), (30, 31, "claimed"), (2, 2, "own")]), [2, 1])

    def test_the_rows_carry_their_clusters(self):
        cfg = simulate.experiment_cfg("H6", 1.0, "null_burst")
        b = simulate.cohort(stats.seed_for("t-1108-rows"), 17, cfg, parts=simulate.PARTS["H6"])
        tables = h6_asks.creator_tables(common.confirmatory(b), vs.primary_definition("H6"))
        sizes = []
        for rows in tables.values():
            for row in rows:
                self.assertEqual(sum(row["clusters"]), row["a"] + row["b"])
                sizes += row["clusters"]
        self.assertGreater(sum(1 for size in sizes if size >= 2), len(sizes) / 2)    # bursts are found as clusters
        self.assertLessEqual(max(sizes), 8)


# ---------------------------------------------------------------- the reference

class ClusterReference(unittest.TestCase):
    creators = [[recording(0, 3, 0.3, [3])], [recording(1, 2, 0.4, [2, 1]), recording(0, 1, 0.2, [1])],
                [recording(2, 0, 0.5, [2])], [recording(0, 2, 0.25, [1, 1])], [recording(0, 4, 0.35, [4]), recording(0, 0, 0.6, [])]]

    def exact_tail(self, creators, by):
        cells = h6_asks.reference_cells(creators, by)
        lcm, observed = h6_asks._integer_statistic(cells)
        law = simulate._law_of_statistic([h6_asks.creator_pmf(units) for _, _, units in cells],
                                         [lcm // total for total, _, _ in cells])
        return sum(prob for value, prob in law.items() if value <= observed)

    def test_the_cells_and_the_null_law(self):
        cells = h6_asks.reference_cells(self.creators)
        self.assertEqual([units for _, _, units in cells][1], [(2, 0.4), (1, 0.4), (1, 0.2)])
        self.assertEqual([total for total, _, _ in cells], [3, 4, 2, 2, 4])            # the a = b = 0 recording adds nothing
        self.assertEqual(len(h6_asks.reference_cells(self.creators, "ask")[0][2]), 3)
        self.assertEqual(h6_asks.creator_pmf([(3, 0.3)]), [0.7, 0.0, 0.0, 0.3])
        pmf = h6_asks.creator_pmf([(2, 0.4), (1, 0.2)])
        self.assertAlmostEqual(sum(pmf), 1.0, places=12)
        self.assertAlmostEqual(sum(a * q for a, q in enumerate(pmf)), 2 * 0.4 + 0.2, places=12)   # centred as sum T_i s_i
        with self.assertRaises(ValueError):
            h6_asks.reference_cells([[recording(1, 1, 0.5, [3])]])                    # sizes must sum to a + b

    def test_p_is_the_exact_cluster_tail_up_to_monte_carlo_error(self):
        for by in ("cluster", "ask"):
            tail = self.exact_tail(self.creators, by)
            p, method = h6_asks.conditional_p(self.creators, ("t-1108", by), 20000, by=by)
            self.assertEqual(method, f"conditional_monte_carlo_{by}s_20000")
            self.assertLess(abs(p - tail), 4 * math.sqrt(tail * (1 - tail) / 20000) + 1.0 / 20000, by)
        self.assertNotAlmostEqual(self.exact_tail(self.creators, "cluster"), self.exact_tail(self.creators, "ask"), places=3)

    def test_single_asks_give_the_ask_level_reference(self):
        singles = [[dict(row, clusters=[1] * (row["a"] + row["b"])) for row in rows] for rows in self.creators]
        bare = [[{k: v for k, v in row.items() if k != "clusters"} for row in rows] for rows in self.creators]
        same = h6_asks.conditional_p(singles, ("t-1108", "same"), 999)[0]
        self.assertEqual(same, h6_asks.conditional_p(bare, ("t-1108", "same"), 999)[0])
        self.assertEqual(same, h6_asks.conditional_p(self.creators, ("t-1108", "same"), 999, by="ask")[0])

    def test_the_amended_p_is_the_larger_of_the_two(self):
        p, method, parts = h6_asks.amended_p(self.creators, ("t-1108", "amended"), 999)
        self.assertEqual(parts["cluster_conditional"], h6_asks.conditional_p(self.creators, ("t-1108", "amended", "clusters"), 999)[0])
        self.assertEqual(parts["signflip_oe"], stats.signflip_p(h6_asks.oe_values(self.creators), "less",
                                                                label=("t-1108", "amended", "signflip-oe"))[0])
        self.assertEqual(p, max(parts["cluster_conditional"], parts["signflip_oe"]))
        self.assertEqual(method, "max(conditional_monte_carlo_clusters_999, signflip_oe_exact)")
        self.assertEqual(parts["ask_level_conditional_0919"],
                         h6_asks.conditional_p(self.creators, ("t-1108", "amended", "conditional"), 999, by="ask")[0])
        self.assertEqual((parts["clusters"], parts["asks_in_clusters_of_2_or_more"], parts["largest_cluster"]), (8, 11, 4))
        self.assertEqual(h6_asks.REFERENCE_DRAWS, 99999)
        self.assertLess(simulate.H6_BATTERY_REFERENCE_DRAWS, h6_asks.REFERENCE_DRAWS)
        self.assertEqual(simulate.largest_count_rejected(LEVEL, h6_asks.REFERENCE_DRAWS), 499)

    def test_analyse_enters_the_amended_p_and_keeps_the_registered_version(self):
        b = simulate.cohort(stats.seed_for("t-1108-analyse"), 12, simulate.experiment_cfg("H6", 1.0, "null_burst"),
                            parts=simulate.PARTS["H6"])
        result = h6_asks.analyse(b, label=("t-1108",), extras=False, draws=99, reference_draws=999)
        tables = h6_asks.creator_tables(common.confirmatory(b), vs.definition())
        hit = [c for c in sorted(tables) if h6_asks._sum(tables[c])["a"] + h6_asks._sum(tables[c])["b"] >= 1]
        p, method, parts = h6_asks.amended_p([tables[c] for c in hit], ("t-1108",), 999)
        self.assertEqual((result["p"], result["p_method"], result["p_parts"]), (p, method, parts))
        self.assertGreater(parts["asks_in_clusters_of_2_or_more"], 0)
        values = [h6_asks.half_count(h6_asks._sum(tables[c])) for c in sorted(tables)]       # registered, unchanged
        self.assertEqual(result["registered_version"]["p"], stats.signflip_p(values, "less", label=("t-1108", "registered"))[0])
        self.assertTrue(any("cluster-level conditional" in item and "sign-flip p of OE" in item for item in result["a10_replaces"]))
        self.assertTrue(result["determinable"] and result["registered_version"]["determinable"])
        self.assertEqual(verdicts.holm_p(result, None), max(result["p"], result["registered_version"]["p"]))   # A10 guard


# ---------------------------------------------------------------- the levels on constructed numbers

class LevelsOnConstructedNumbers(unittest.TestCase):
    """Exact enumeration under the cluster null (simulate.h6_cluster_levels) with the analysis's 99,999 draws."""

    @classmethod
    def setUpClass(cls):
        names = ("17 creators, one burst of 3, s = 0.3", "17 creators, three bursts of 2, s = 0.3",
                 "17 creators, T = 1 single asks, s = 0.3", "17 creators, T = 3 single asks, s = 0.5",
                 "12 creators, one burst of 3, s = 0.3")
        cases = [case for case in simulate.h6_cluster_level_cases() if case[1] in names]
        cls.rows = {row["case"]: row for row in simulate.h6_cluster_reference_levels(cases)}
        assert set(cls.rows) == set(names)

    def test_the_cluster_p_and_the_amended_p_hold_the_level(self):
        for row in self.rows.values():
            for alpha in ("0.005", "0.05"):
                for key in ("cluster", "cluster_exact", "amended"):
                    self.assertLessEqual(row[f"{key}_{alpha}"], float(alpha) + 1e-12, (row["case"], key))
                self.assertLessEqual(row["amended_" + alpha], row["cluster_" + alpha] + 1e-12)
                self.assertLessEqual(row["amended_" + alpha], row["signflip_" + alpha] + 1e-12)

    def test_each_replaced_reference_fails_somewhere(self):
        burst = self.rows["17 creators, one burst of 3, s = 0.3"]
        self.assertAlmostEqual(burst["ask_level_0.005"], 0.0774, places=4)              # the verifier's 7.74%
        self.assertAlmostEqual(burst["ask_level_0.05"], 0.2019, places=4)
        self.assertAlmostEqual(self.rows["12 creators, one burst of 3, s = 0.3"]["ask_level_0.005"], 0.0850, places=4)
        sparse = self.rows["17 creators, T = 1 single asks, s = 0.3"]
        self.assertAlmostEqual(sparse["signflip_0.005"], 0.0193, places=4)             # 09:19's 1.93%
        self.assertAlmostEqual(sparse["ask_level_0.005"], sparse["cluster_0.005"], places=12)   # single asks: the same
        self.assertGreater(self.rows["17 creators, three bursts of 2, s = 0.3"]["ask_level_0.05"], 0.10)
        plain = self.rows["17 creators, T = 3 single asks, s = 0.5"]
        self.assertLess(plain["signflip_0.005"], 0.005)

    def test_the_enumeration_matches_the_code_path(self):
        """Simulated data from the cluster null of 8 creators with one burst of 2 at s = 0.5 (and one single ask at
        s = 0.3), through h6_asks.amended_p with 199 draws, against the enumerated levels at 199 draws."""
        case = [[(0.5, [2]), (0.3, [1])] for _ in range(8)]
        level = simulate.h6_cluster_levels(case, alphas=(0.05,), draws=199)
        stream, sets = stats.rng("t-1108-code-path"), 1500
        hits = {"cluster": 0, "ask_level": 0, "amended": 0}
        for k in range(sets):
            creators = []
            for _ in case:
                burst = 2 if stream.random() < 0.5 else 0
                single = int(stream.random() < 0.3)
                creators.append([recording(burst, 2 - burst, 0.5, [2]), recording(single, 1 - single, 0.3, [1])])
            p, _, parts = h6_asks.amended_p(creators, ("t-1108-code-path", k), 199)
            hits["cluster"] += parts["cluster_conditional"] <= 0.05
            hits["ask_level"] += parts["ask_level_conditional_0919"] <= 0.05
            hits["amended"] += p <= 0.05
        for key, count in hits.items():
            expected = level[key][0.05]
            self.assertLess(abs(count / sets - expected), 4 * math.sqrt(expected * (1 - expected) / sets) + 0.005, key)
        self.assertGreater(level["ask_level"][0.05], 0.05)

    def test_the_small_binomial_tail(self):
        self.assertAlmostEqual(simulate.binomial_cdf_small(2, 10, 0.3), sum(math.comb(10, j) * 0.3 ** j * 0.7 ** (10 - j)
                                                                            for j in range(3)), places=12)
        self.assertAlmostEqual(simulate.binomial_cdf_small(49, 9999, 0.005), simulate._binomial_cdf(49, 9999, 0.005), places=7)
        self.assertEqual(simulate.binomial_cdf_small(-1, 10, 0.3), 0.0)
        self.assertEqual(simulate.binomial_cdf_small(10, 10, 0.3), 1.0)


# ---------------------------------------------------------------- the battery

class BurstScenario(unittest.TestCase):
    def test_the_plan_and_the_generator(self):
        for n in (12, 17):
            self.assertIn(("H6", "null_burst", n, 1.0, 30), simulate.plan(quick=True))
            self.assertIn(("H6", "null_burst", n, 1.0, 2000), simulate.plan())
        cfg = simulate.experiment_cfg("H6", 1.0, "null_burst")
        self.assertEqual((cfg["claimed_fraction"], cfg["bursts_per_creator"], cfg["burst_sizes"]), ((0.3, 0.7), (1, 2), (2, 4)))
        b = simulate.cohort(stats.seed_for("t-1108-burst"), 17, cfg, parts=simulate.PARTS["H6"])
        per_creator = {}
        for item in b["recordings"]:
            per_creator.setdefault(item["creator"], []).extend(item["asks"]["asks"])
        self.assertEqual(len(per_creator), 17)
        for asks in per_creator.values():
            self.assertTrue(2 <= len(asks) <= 8)
        tables = h6_asks.creator_tables(common.confirmatory(b), vs.primary_definition("H6"))
        shares = [row["wc"] / (row["wc"] + row["wo"]) for rows in tables.values() for row in rows]
        self.assertGreater(min(shares), 0.2)
        self.assertLess(max(shares), 0.85)
        self.assertGreaterEqual(sum(1 for rows in tables.values() if sum(r["a"] + r["b"] for r in rows)), 12)
        # the other scenarios do not carry its settings
        for scenario in ("null", "null_heterogeneous", "null_sparse_low_share"):
            self.assertNotIn("bursts_per_creator", simulate.experiment_cfg("H6", 1.0, scenario))

    def test_a_burst_lies_in_one_voice(self):
        r = simulate.random.Random(5)
        habits = simulate.creator_habits(r, simulate.DEFAULT)
        cfg = dict(simulate.DEFAULT, exact=True, **simulate.SCENARIO_CFG["null_burst"])
        recordings = []
        for index in range(4):
            voice, _, truth, _ = simulate.voice_and_features(r, "h000", "holdout", index, "both", habits, cfg)
            recordings.append((voice, truth, "both"))
        bursts = mixed = 0
        for _ in range(40):
            records = simulate.burst_asks_records(r, recordings, cfg)
            self.assertTrue(2 <= sum(len(record["asks"]) for record in records) <= 8)
            for record, (voice, truth, _) in zip(records, recordings):
                side = {unit["id"]: s for unit, s in zip(voice["units"], truth)}
                run_, last = [], None                  # the asks chained by the cluster rule, with their true voices
                for unit_id in sorted(ask["first_unit"] for ask in record["asks"]):
                    if last is not None and unit_id > last + 1:
                        bursts += 1
                        mixed += len(set(run_)) > 1
                        run_ = []
                    run_.append(side[unit_id])
                    last = unit_id
                if run_:
                    bursts += 1
                    mixed += len(set(run_)) > 1
        self.assertGreater(bursts, 40)
        self.assertLessEqual(mixed, bursts // 20)       # only two bursts that touch across a voice boundary mix voices

    def test_the_rows_and_the_summary_carry_every_p(self):
        rows = simulate.task(("H6", "null_burst", 12, 1.0, 0, 2))["rows"]
        for row in rows:
            for key, _ in simulate.H6_COMPARISON_PS:
                self.assertIn(key, row)
            if row["determinable"]:
                self.assertEqual(row["p"], max(row["p_cluster_conditional"], row["p_signflip_oe"]))
        table = simulate.summarise("H6", "null_burst", 12, 1.0, rows, None, 0.0)
        for name in ("cluster_conditional", "signflip_oe", "ask_level_conditional_0919", "pooled_oe_before_0644", "guarded"):
            self.assertIn("reject_0.005_" + name, table)
        self.assertIn("mean_largest_cluster", table)

    def test_the_markdown_shows_the_replaced_references(self):
        rows = simulate.task(("H6", "null_burst", 12, 1.0, 0, 2))["rows"]
        table = [simulate.summarise("H6", "null_burst", 12, 1.0, rows, None, 0.0)]
        text = run.simulation_markdown({"workers": 1, "seconds": 1, "progress": {}, "experiments": table, "boundary": []})
        self.assertIn("## H6: the amended p, its two halves and the references it replaced", text)
        for column in ("amended p", "cluster p", "sign-flip of OE", "ask-level p", "pooled OE", "guarded"):
            self.assertIn(column, text)
        self.assertIn("| null_burst | 12 | 2 |", text)


# ---------------------------------------------------------------- A10.7 under the cluster null

class A10NullUnderClusters(unittest.TestCase):
    def test_the_registered_mean_reads_the_clusters(self):
        b = simulate.cohort(stats.seed_for("t-1108-a10"), 0, simulate.experiment_cfg("H6", 1.0, "null_burst"), n_seen=12,
                            parts=("voice", "asks"))
        out = a10_checks.h6_null(a10_checks.seen_only(b))
        self.assertEqual(out["amended_OE_null_mean"], 0.0)
        self.assertGreater(out["asks_in_clusters_of_2_or_more"], 0)
        self.assertNotAlmostEqual(out["registered_half_count_null_mean"],
                                  out["registered_half_count_null_mean_asks_one_by_one_0919"], places=6)
        # single asks: the two nulls agree
        plain = simulate.cohort(stats.seed_for("t-1108-a10-plain"), 0, simulate.experiment_cfg("H6", 1.0, "null_sparse_low_share"),
                                n_seen=12, parts=("voice", "asks"))
        seen = a10_checks.seen_only(plain)
        for item in seen["recordings"]:          # keep one ask in each recording, so that no two asks form a cluster
            if item.get("asks"):
                item["asks"] = dict(item["asks"], asks=item["asks"]["asks"][:1])
        out = a10_checks.h6_null(seen)
        self.assertEqual(out["asks_in_clusters_of_2_or_more"], 0)
        self.assertAlmostEqual(out["registered_half_count_null_mean"],
                               out["registered_half_count_null_mean_asks_one_by_one_0919"], places=12)


# ---------------------------------------------------------------- H6's detectable-effect note from the battery

class DetectableFromTheBattery(unittest.TestCase):
    def battery(self, fingerprint, quick=False, powers=((0.31, 0.92), (0.45, 0.97))):
        rows = []
        for size, (sesoi, large) in zip((12, 17), powers):
            for scenario, power in (("plant_sesoi", sesoi), ("plant_large", large)):
                rows.append({"hypothesis": "H6", "scenario": scenario, "creators": size, "reps": 500,
                             "reject_0.005_guarded": power, "supported_at_first_holm_step_guarded": power * 0.9})
        return {"quick": quick, "progress": {"fingerprint": fingerprint}, "experiments": rows}

    def test_the_note_reads_the_battery_power_not_the_normal_sign_flip(self):
        fingerprint = simulate.task_fingerprint()
        with mock.patch.object(stats, "detectable_effect", side_effect=AssertionError("not for H6")):
            note = verdicts.detectable_note("H6", 18, None, "less", battery=self.battery(fingerprint))
            self.assertIn("17 creators", note)
            self.assertIn("rate ratio 0.5: 45%", note)
            self.assertIn("rate ratio 0.25: 97%", note)
            self.assertIn("80% power at a rate ratio of 0.25, not at the smallest effect (0.5)", note)
            note = verdicts.detectable_note("H6", 14, 0.3, "less", battery=self.battery(fingerprint, powers=((0.3, 0.7), (0.4, 0.9))))
            self.assertIn("12 creators", note)
            self.assertIn("80% power at neither planted ratio", note)
            note = verdicts.detectable_note("H6", 30, None, "less", battery=self.battery(fingerprint, powers=((0.3, 0.7), (0.85, 0.99))))
            self.assertIn("80% power at both planted ratios", note)
            self.assertIn("below the battery's smallest", verdicts.detectable_note("H6", 11, None, "less", battery=self.battery(fingerprint)))
            self.assertIn("none is stated", verdicts.detectable_note("H6", 17, None, "less", battery=self.battery("0" * 64)))
            self.assertIn("a quick run", verdicts.detectable_note("H6", 17, None, "less", battery=self.battery(fingerprint, quick=True)))
            with mock.patch.object(verdicts, "load_battery", return_value=None):
                self.assertIn("not on file", verdicts.detectable_note("H6", 17, None, "less"))
        self.assertIsNone(verdicts.load_battery(Path(__file__).resolve().parent / "no-such-file.json"))

    def test_the_analysis_writes_the_h6_note_without_a_creator_sd(self):
        """Verifier, 2026-11-21 after 11:08: run.analyse called detectable_note only where config["creator_sd"] held the
        hypothesis, so H6's battery note was None in counts.json (the e2e's config has no H6 SD, nor does the template).
        Stubbed bundle and counts; the run stops at the null check, after counts.json is written."""
        import json
        import tempfile

        class Stop(Exception):
            pass

        eligible = {h: {"creators": 17, "minimum": 12, "determinable": True} for h in ("H1", "H6")}
        battery = DetectableFromTheBattery.battery(self, simulate.task_fingerprint())
        with tempfile.TemporaryDirectory() as folder, \
                mock.patch.object(run.adapter, "load_bundle", return_value={"records": [{"synthetic": True}]}), \
                mock.patch.object(run, "asr_rule_of", return_value={"required": None, "models": None}), \
                mock.patch.object(run, "counts", return_value=eligible), \
                mock.patch.object(verdicts, "load_battery", return_value=battery), \
                mock.patch.object(run.a10_checks, "null_means", side_effect=Stop):
            with self.assertRaises(Stop):
                run.analyse({"out": folder, "sources": {"primary": {}}, "creator_sd": {"H4": 0.8}}, 1)
            detectable = json.loads((Path(folder) / "counts.json").read_text(encoding="utf-8"))["detectable"]
        self.assertIn("detectable effect from the simulation battery", detectable["H6"])
        self.assertIsNone(detectable["H1"])                       # no SD entered: no note, as before


if __name__ == "__main__":
    unittest.main()
