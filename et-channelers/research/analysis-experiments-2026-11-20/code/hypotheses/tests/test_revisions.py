"""Revisions of 2026-11-21 (registry rows 02:50, 02:55 and 03:08; track B): the wording rules of M9 (H2's shared-wording
flag, H5's self-naming exclusion), H2's retained parts, H5's Q2 assignments, the merged claimed voice, the A10 guard, the
uninformative flag, the verdict wording, the hold-out cross-check and the counts of every label source. Synthetic records
and invented strings only."""
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import a10_checks, adapter  # noqa: E402
from hypotheses import constants as K  # noqa: E402
from hypotheses import features as F  # noqa: E402
from hypotheses import h1_rate, h2_hedging, h4_contraction, h5_world_claims, h6_asks  # noqa: E402
from hypotheses import run, simulate, stats, verdicts, wording  # noqa: E402
from hypotheses import voice_sets as vs  # noqa: E402

PARTS = K.H2_PARTS


# ---------------------------------------------------------------- the pattern lists

class SharedWording(unittest.TestCase):
    POSITIVE = {"in one scenario the markets will fall": "SC1",
                "there are two timelines and we choose": "SC2",
                "many possible futures are open": "SC2",
                "either the vote passes or it fails": "SC3",
                "either way something will shift": "SC4",
                "in some sense the old world ends": "WD1",
                "on another level the structures collapse": "WD2",
                "on a higher level the change has come": "WD2",
                "energetically it has already happened": "WD3",
                "I’m not saying it will happen next week": "WD4"}
    # registry 2026-11-21 04:55 (e): the plain hedge "a possibility" (the former SC5) is no scenario wording; it is now a
    # negative case (its POSITIVE entry was moved here, not dropped)
    NEGATIVE = ("the vote will pass in March", "the scenery will change", "they will not either", "a higher level of income",
                "on the level of the street", "the timeline of events is fixed", "I am saying it will happen",
                "in a way that surprises everyone", "they will promise nothing", "",
                "one possibility is that the grid fails", "there is a possibility that the markets fall",
                "another possibility is a new council")

    def test_each_pattern_finds_its_clause(self):
        for text, pid in self.POSITIVE.items():
            self.assertIn(pid, wording.shared_wording(text), text)
        self.assertEqual(sorted(set(self.POSITIVE.values())), ["SC1", "SC2", "SC3", "SC4", "WD1", "WD2", "WD3", "WD4"])

    def test_ordinary_statements_are_not_flagged(self):
        for text in self.NEGATIVE:
            self.assertEqual(wording.shared_wording(text), [], text)

    def test_the_list_after_0455(self):
        """Registry 04:55 (e): SC1-SC4 and WD1-WD4 stay; SC5 ('a possibility') leaves the list."""
        self.assertEqual([pid for pid, _, _ in K.H2_SHARED_WORDING], ["SC1", "SC2", "SC3", "SC4", "WD1", "WD2", "WD3", "WD4"])
        parsed = adapter.parse_statement(statement(quote="syn a possibility syn"))
        self.assertEqual(parsed["shared_wording"], [])

    def test_kinds_and_several_fields(self):
        ids = wording.shared_wording("syn", "in one scenario", None, "on another level")
        self.assertEqual(ids, ["SC1", "WD2"])
        self.assertEqual(wording.shared_kinds(ids), ["scenario", "withdrawal"])

    def test_every_pattern_names_a_kind_and_compiles(self):
        self.assertEqual(len({pid for pid, _, _ in K.H2_SHARED_WORDING}), len(K.H2_SHARED_WORDING))
        self.assertTrue(all(kind in ("scenario", "withdrawal") for _, kind, _ in K.H2_SHARED_WORDING))


class SelfNaming(unittest.TestCase):
    def test_patterns(self):
        for text in ("I am Ashtar and I greet you", "we are the Pleiadian collective", "this is Thor of the council",
                     "my name is Elan", "we are known as the guardians", "we are a council of nine"):
            self.assertTrue(wording.self_naming(text), text)
        for text in ("I am here with you", "I'm grateful for this", "we are the ones we waited for", "this is it", ""):
            self.assertFalse(wording.self_naming(text), text)

    def test_feature_files_carry_the_flag(self):
        words = [{"t": t, "start": i * 0.4, "end": i * 0.4 + 0.3} for i, t in enumerate("I am Ashtar . Today we talk".split())]
        units = [{"id": 1, "first": 0, "last": 3}, {"id": 2, "first": 4, "last": 6}]
        rows = F.unit_features(words, units, F.contraction_patterns([("it's", "it is")]))
        self.assertEqual([row["self_name"] for row in rows], [True, False])


# ---------------------------------------------------------------- H2

def statement(values=None, committed=True, quote="syn statement", words=12, weight_p=1.0, where="STATEMENT"):
    values = values or {}
    full = {part: values.get(part, "NO") for part in PARTS}
    return {"key": quote, "verified": True, "duplicate": False, "statement_words": words, "statement_quote": quote, "markers": {},
            "coded": True, "inclusion_p": weight_p,
            "fc": {"values": full, "where": {part: (where if full[part] != "NO" else "NA") for part in PARTS}},
            "fd": {"committed": committed, "four_way": "bare" if committed else "hedged"}}


def forecast_bundle(by_creator, group="holdout"):
    """by_creator: {creator: [raw statement]}; one recording per creator."""
    recordings = []
    for creator, statements in sorted(by_creator.items()):
        data = {"audio": "a-" + creator, "creator": creator, "group": group, "statements": statements, "synthetic": True}
        (parsed,) = adapter.parse_forecasts(data, {})
        recordings.append({"audio": data["audio"], "creator": creator, "group": group, "forecasts": parsed})
    return {"recordings": recordings, "titles": None, "records": [r["forecasts"] for r in recordings]}


class H2Revisions(unittest.TestCase):
    def test_the_adapter_keeps_the_flag_and_drops_the_wording(self):
        quote = "syn in one scenario syn"
        parsed = adapter.parse_statement(statement(quote=quote))
        self.assertEqual(parsed["shared_wording"], ["SC1"])
        self.assertNotIn(quote, json.dumps(parsed))
        self.assertEqual(adapter.parse_statement(statement(quote="syn", **{}))["shared_wording"], [])
        given = dict(statement(quote="syn"), shared_wording=["WD2"])
        self.assertEqual(adapter.parse_statement(given)["shared_wording"], ["WD2"])         # a file may carry the ids

    def test_primary_leaves_flagged_statements_out_and_the_row_keeps_them(self):
        b, _ = simulate.cohort(stats.seed_for("t-h2-flag"), 10, {"exact": True, "beta": -0.7}, parts=("voice", "forecasts"), raw=True)
        _, bands, parts = simulate.calibration_constants("H2")
        primary = h2_hedging.analyse(b, bands=bands, parts=parts, extras=False, permutations=99, draws=99)
        kept = h2_hedging.analyse(b, bands=bands, parts=parts, extras=False, permutations=99, draws=99, include_flagged=True)
        self.assertGreater(primary["eligibility"]["flagged_statements"], 0)
        self.assertEqual(primary["eligibility"]["flagged_statements"], kept["eligibility"]["flagged_statements"])
        self.assertLess(primary["eligibility"]["statements"], kept["eligibility"]["statements"])
        self.assertFalse(primary["eligibility"]["flagged_included"])
        names = [name for name, _ in h2_hedging.rows()]
        self.assertIn("flagged statements included (shared scenario or withdrawal wording, M9)", names)

    def test_parts_from_seen_keep_parts_at_five_percent(self):
        statements = []
        for i in range(100):           # time window YES 50 times, place 5 times, named actor 4 times, the others never
            values = {"time_window": "YES" if i % 2 else "NO", "place": "YES" if i < 5 else "NO", "named_actor": "YES" if 10 <= i < 14 else "NO"}
            statements.append(statement(values, quote=f"syn {i}"))
        b = forecast_bundle({"s1": statements[:50], "s2": statements[50:]}, group="seen")
        retained, share, count = h2_hedging.parts_from_seen(b)
        self.assertEqual(count, 100)
        self.assertEqual(retained, ("time_window", "place"))
        self.assertAlmostEqual(share["place"], 0.05)
        self.assertAlmostEqual(share["named_actor"], 0.04)
        self.assertEqual(K.H2_PART_PREVALENCE_MIN, 0.05)
        # FREEZE2, entered from seen labels (registry 2026-11-21 12:52 (6)): parts of H2_PARTS, in H2_PARTS order
        self.assertIsInstance(K.H2_PARTS_RETAINED, tuple)
        self.assertEqual(K.H2_PARTS_RETAINED, tuple(part for part in K.H2_PARTS if part in K.H2_PARTS_RETAINED))

    def test_the_score_counts_only_retained_parts(self):
        st = adapter.parse_statement(statement({"time_window": "YES", "place": "YES", "quantity": "YES"}))
        self.assertEqual(h2_hedging.score(st, parts=("time_window", "place")), 2)
        self.assertEqual(h2_hedging.score(st, parts=PARTS), 3)

    def test_no_part_retained_is_not_determinable(self):
        b = forecast_bundle({f"c{i}": [statement({"time_window": "YES"}, quote=f"syn {i} {j}") for j in range(30)] for i in range(9)})
        result = h2_hedging.analyse(b, bands=(10, 20), parts=(), extras=False)
        self.assertFalse(result["determinable"])
        final, holm = verdicts.finalise({"H2": result})
        self.assertEqual(final["H2"]["verdict"], h2_hedging.NO_PART)
        self.assertEqual(holm["H2"]["input_p"], 1.0)
        self.assertTrue(final["H2"]["uninformative"])

    def test_freeze2_needs_the_parts(self):
        import inspect
        from unittest import mock
        self.assertIn("K.H2_PARTS_RETAINED is None", inspect.getsource(adapter.freeze2_problem))
        with mock.patch.object(K, "H2_PARTS_RETAINED", None):     # registry 12:52 (6): the parts are entered
            with self.assertRaises(ValueError):                                # a run without the parts is refused
                h2_hedging.analyse(forecast_bundle({"c": [statement()]}), bands=(10, 20))


# ---------------------------------------------------------------- H5

def voice_unit(i, label, cue):
    view = {"label": label, "label_b": label, "detail": "none", "cue": list(cue), "flags": [], "own_broad": label == "V1"}
    return {"id": i, "first": 0, "last": 0, "n_words": 10, "map": label, "small": view, "middle": view, "label": label,
            "label_b": label, "own_broad": view["own_broad"]}


class H5Revisions(unittest.TestCase):
    def test_self_naming_units_from_voice_cues(self):
        units = [voice_unit(1, "V1", ("own_person_identity", 1)), voice_unit(2, "V2", ("self_name", 2)),
                 voice_unit(3, "V2", ("self_name", 2)), voice_unit(4, "V2", ("self_name", 2)), voice_unit(5, "V3", ("report_clause", 5))]
        data = {"audio": "a", "creator": "c", "group": "holdout", "info": {"language": "en"}, "map": {}, "label_of_record": "middle",
                "units": units, "synthetic": True}
        record = adapter.parse_voice(data)
        self.assertEqual(vs.self_naming_units(record), [2, 3])                 # the cue unit and the unit after it
        for unit in data["units"]:
            unit["middle"]["cue"] = unit["small"]["cue"] = None
        self.assertIsNone(vs.self_naming_units(adapter.parse_voice(data)))     # no cue in the file: fall back

    def test_counts_leave_out_excluded_units_and_q2(self):
        content = {"units": {1: {"primary": "Q1", "secondary": "NONE", "weight": 2}, 2: {"primary": "Q1", "secondary": "NONE", "weight": 1},
                             3: {"primary": "Q2", "secondary": "NONE", "weight": 1}, 4: {"primary": "Q1", "secondary": "Q2", "weight": 1},
                             5: {"primary": "Q4", "secondary": "NONE", "weight": 3}}, "mode": "systematic"}
        item = {"content": content}
        groups = K.H5_GROUPS["primary"]
        self.assertEqual(h5_world_claims._counts(item, groups, 40, False)[:2], (4.0, 3.0))
        self.assertEqual(h5_world_claims._counts(item, groups, 40, False, excluded={1})[:3], (2.0, 3.0, 2))
        self.assertEqual(h5_world_claims._counts(item, groups, 40, False, drop_codes=("Q2",))[:2], (3.0, 3.0))   # units 3, 4 out
        self.assertEqual(h5_world_claims._counts(item, K.H5_GROUPS["sensitivity_A"], 40, False)[:2], (5.0, 3.0))  # Q2 is world

    def test_feature_fallback(self):
        item = {"voice": None, "features": {"units": {1: {"self_name": False}, 4: {"self_name": True}, 5: {"self_name": False}}}}
        excluded, source = h5_world_claims.self_naming_excluded(item)
        self.assertEqual((sorted(excluded), source), ([4, 5], "feature patterns"))
        self.assertEqual(h5_world_claims.self_naming_excluded({"voice": None, "features": None}), (set(), "none"))

    def test_rows_hold_the_three_q2_assignments(self):
        names = [name for name, _ in h5_world_claims.rows()]
        self.assertIn("Q2 merged with Q1 (sensitivity A: world = Q1 + Q2)", names)
        self.assertIn("Q2 excluded (units coded Q2 left out)", names)
        self.assertIn("units next to a self-naming cue kept (before M9)", names)
        self.assertEqual(sorted(K.H5_Q2_ASSIGNMENTS), ["as registered", "excluded", "merged with Q1"])

    def test_the_exclusion_is_counted_and_reported(self):
        b = simulate.cohort(stats.seed_for("t-h5-self"), 12, {"exact": True, "theta": 0.8}, n_seen=0, parts=simulate.PARTS["H5"])
        result = h5_world_claims.analyse(b, draws=99)
        tally = result["eligibility"]["self_naming_exclusion"]
        self.assertGreater(tally["units_left_out"], 0)
        self.assertEqual(sorted(tally["recordings_by_cue_source"]), ["voice cues"])
        table = result["secondary"]["Q2 assignments (M9)"]
        self.assertEqual(sorted(table), ["as registered", "excluded", "merged with Q1"])
        self.assertEqual(table["as registered"]["p"], result["p"])
        kept = h5_world_claims.analyse(b, draws=99, extras=False, self_naming=False)
        self.assertEqual(kept["eligibility"]["self_naming_exclusion"], "not applied")


# ---------------------------------------------------------------- voice: the merged claimed side

class ClaimedVoice(unittest.TestCase):
    def test_claimed_side_per_hypothesis(self):
        """Registry 02:55 and 04:55 (a). This test replaced test_every_registered_quantity_uses_v2_and_v3, which asserted
        V2 + V3 for H4 as well: 04:55 (a) keeps H4's registered primary on the embodied voice (V2). H1 and H6 keep V2 + V3,
        and every row of a hypothesis, extra sources included, uses its claimed side."""
        self.assertEqual(vs.definition()["claimed"], ("V2", "V3"))
        self.assertEqual(K.REGISTERED_CLAIMED, ("V2", "V3"))
        self.assertEqual(K.CLAIMED_BY_HYPOTHESIS, {"H1": ("V2", "V3"), "H4": ("V2",), "H6": ("V2", "V3")})
        for hypothesis, claimed in K.CLAIMED_BY_HYPOTHESIS.items():
            self.assertEqual(vs.primary_definition(hypothesis)["claimed"], claimed)
        specs = run.row_specs({"recordings": [], "titles": None}, ["extra"])
        seen = set()
        for hypothesis, name, source, options in specs:
            if hypothesis in ("H1", "H4", "H6") and source == "primary":
                self.assertEqual(tuple(options["claimed"]), K.CLAIMED_BY_HYPOTHESIS[hypothesis], (hypothesis, name))
                seen.add(hypothesis)
        self.assertEqual(seen, {"H1", "H4", "H6"})
        self.assertTrue(all(not options for h, name, source, options in specs if source == "extra"))
        # an extra source's row runs with the hypothesis's own claimed side (run.run_row uses primary_definition)
        import inspect
        self.assertIn("vs.primary_definition(hypothesis", inspect.getsource(run.run_row))

    def test_h4_primary_is_embodied_and_the_merged_voice_a_secondary(self):
        """A recording whose claimed voice is relayed only counts for H1 (V2 + V3) and not for H4 (V2)."""
        relayed = {"audio": "r1", "creator": "c1", "video_id": "v-r1", "group": "holdout", "info": {"language": "en"},
                   "map": {"format": "solo", "claimant": "sole_speaker", "main_kind": "claimed_voice"}, "label_of_record": "middle",
                   "units": [voice_unit(1, "V1", ("own_person_identity", 1)), voice_unit(2, "V3", ("report_clause", 2))],
                   "synthetic": True}
        b = adapter.bundle(voice=[adapter.parse_voice(relayed)])
        self.assertEqual(h4_contraction.eligible(b, vs.primary_definition("H4"))["creators"], 0)
        self.assertEqual(h4_contraction.eligible(b, vs.merged_claimed(vs.primary_definition("H4")))["creators"], 1)
        self.assertEqual(run.counts(b, {"bands": None, "parts": None})["H4"]["creators"], 0)

    def test_relayed_only_rows_are_below_the_floor_without_a_verdict(self):
        b = simulate.cohort(stats.seed_for("t-relayed"), 12, {"exact": True, "mu1": -0.1, "mu4": 1.0}, parts=("voice", "features"))
        yardstick, _, _ = simulate.calibration_constants("H4")
        h4_full = h4_contraction.analyse(b, yardstick=yardstick, draws=99)
        for result, key in ((h1_rate.analyse(b, draws=99), "relayed only"), (h4_full, "relayed spans (estimate)")):
            row = result["secondary"][key]
            self.assertEqual(row["flag"], K.BELOW_FLOOR)
            self.assertIsNone(row["verdict"])
        merged = h4_full["secondary"]["claimed voice V2 + V3 (merged, registry 02:55; secondary, no verdict)"]
        self.assertIsNone(merged["verdict"])
        self.assertEqual(merged["note"], K.MERGED_CLAIMED_NOTE)
        # the H4 primary is V2 (04:55 (a)); the comparison with vs.definition() (V2 + V3) became primary_definition("H4")
        h4 = h4_contraction.analyse(b, yardstick=yardstick, extras=False)
        self.assertEqual(h4["eligibility"]["creators"], h4_contraction.eligible(b, vs.primary_definition("H4"))["creators"])
        self.assertEqual(h4["eligibility"]["creators"], 12)        # the calibration generator keeps every creator eligible


# ---------------------------------------------------------------- the A10 guard, uninformative, wording

def fake(hypothesis, p, kind="supported", interval=(-0.3, -0.1), determinable=True, version="amended"):
    conditions = {"supported": {"registered": True, "a5": True, "effect_size": True, "refuted": None},
                  "refuted": {"registered": False, "a5": False, "effect_size": True, "refuted": "no slowing: the 95% interval of the ratio lies inside"},
                  "neither": {"registered": True, "a5": False, "effect_size": False, "refuted": None}}[kind]
    return {"hypothesis": hypothesis, "version": version, "determinable": determinable, "p": p, "estimate": {"x": -0.2},
            "eligibility": {"creators": 17, "minimum": 12}, "conditions": conditions, "creator_interval_90": interval}


class Guard(unittest.TestCase):
    def test_the_larger_p_enters_holm_and_both_must_agree(self):
        result = dict(fake("H1", 0.0001), registered_version=fake("H1", 0.0004, version="registered"))
        final, holm = verdicts.finalise({"H1": result})
        self.assertEqual(holm["H1"]["input_p"], 0.0004)
        self.assertEqual(final["H1"]["verdict"], K.SUPPORTED)
        self.assertTrue(final["H1"]["a10_guard"]["verdicts_agree"])
        self.assertEqual(final["H1"]["versions"]["registered"]["p"], 0.0004)
        result = dict(fake("H1", 0.0001), registered_version=fake("H1", 0.0001, "neither", version="registered"))
        final, _ = verdicts.finalise({"H1": result})
        self.assertTrue(final["H1"]["verdict"].startswith("not determined: the registered and the amended versions differ"))
        self.assertEqual(final["H1"]["verdict_kind"], "not determined")

    def test_a_registered_p_above_the_step_blocks_support(self):
        result = dict(fake("H4", 0.0001), registered_version=fake("H4", 0.2, version="registered"))
        final, holm = verdicts.finalise({"H4": result})
        self.assertEqual(holm["H4"]["input_p"], 0.2)
        self.assertNotEqual(final["H4"]["verdict_kind"], "supported")

    def test_an_unusable_version_counts_as_p_one(self):
        result = dict(fake("H5", 0.0001), registered_version=fake("H5", 0.0001, determinable=False, version="registered"))
        _, holm = verdicts.finalise({"H5": result})
        self.assertEqual(holm["H5"]["input_p"], 1.0)

    def test_holm_count_and_fixed_p(self):
        _, holm = verdicts.finalise({})
        self.assertEqual(sorted(holm), sorted(K.ALL_HYPOTHESES))
        for name in ("H3", "H7", "H8", "H10"):
            self.assertEqual(holm[name]["input_p"], 1.0)
        self.assertEqual((K.A10_MIN_ONE_SIDED, K.A10_MIN_TWO_SIDED, K.MIN_CREATORS["H2"], K.HOLM_M), (8, 9, 9, 10))
        self.assertEqual(K.MIN_CREATORS, {"H1": 12, "H2": 9, "H4": 12, "H5": 12, "H6": 12, "H9": 8})

    def test_the_registered_versions_exist_on_synthetic_data(self):
        b = simulate.cohort(stats.seed_for("t-versions"), 12, {"exact": True, "mu1": -0.15, "rr": 0.3}, parts=("voice", "features", "asks"))
        h1 = h1_rate.analyse(b, extras=False)
        reg = h1["registered_version"]
        self.assertEqual(reg["p"], h1["p"])                                    # same sign-flip
        self.assertIn("dl_95", reg["intervals"])
        self.assertAlmostEqual(reg["estimate"]["log_ratio"], h1["estimate"]["log_ratio"])
        h6 = h6_asks.analyse(b, extras=False, draws=99)
        self.assertIn("mean_half_count_log_ratio", h6["registered_version"]["estimate"])
        self.assertNotIn("creator_values", h6["registered_version"])


class VendorCheck(unittest.TestCase):
    """Registry 2026-11-21 03:21 (gate VG-6): a failed cross-vendor voice check caps H1, H4 and H6 at 'not determined'
    and flags them; a pass, or no entry, changes nothing; other hypotheses are not touched."""

    def test_failed_check_caps_voice_hypotheses(self):
        primary = {"H1": dict(fake("H1", 0.0001), registered_version=fake("H1", 0.0001, version="registered")),
                   "H4": dict(fake("H4", 0.5, "refuted"), registered_version=fake("H4", 0.5, "refuted", version="registered")),
                   "H2": dict(fake("H2", 0.0001), registered_version=fake("H2", 0.0001, version="registered"))}
        rows = {"H1": [("second model", dict(fake("H1", 0.0001), registered_version=fake("H1", 0.0001, version="registered")))]}
        final, holm = verdicts.finalise(primary, rows, vendor_check={"passed": False, "kappa": 0.41})
        flag = "readers of two vendors disagree (kappa 0.41)"
        for name in ("H1", "H4"):
            self.assertEqual(final[name]["verdict_kind"], "not determined")
            self.assertTrue(final[name]["verdict"].startswith("not determined: " + flag))
            self.assertEqual(final[name]["vendor_flag"], flag)
            self.assertIn(flag, final[name]["sentences"])
            self.assertIsNone(final[name]["verdict_statement"])
        self.assertEqual(final["H1"]["rows"][0]["verdict_kind"], "not determined")
        self.assertEqual(final["H2"]["verdict_kind"], "supported")
        self.assertIsNone(final["H2"]["vendor_flag"])
        self.assertEqual(holm["H1"]["input_p"], 0.0001)                       # the cap leaves the Holm input as it is
        for check in (None, {"passed": True, "kappa": 0.8}, {"passed": None, "kappa": None}):
            final, _ = verdicts.finalise(primary, vendor_check=check)
            self.assertEqual(final["H1"]["verdict_kind"], "supported")
            self.assertIsNone(final["H1"]["vendor_flag"])

    def test_the_template_names_the_check(self):
        template = json.loads(run.TEMPLATE.read_text(encoding="utf-8"))
        self.assertIn("passed", template["cross_vendor_voice"])


class H5RelaxedRow(unittest.TestCase):
    def test_the_registered_version_of_a_row_uses_the_rows_minimum(self):
        b = simulate.cohort(stats.seed_for("t-h5-relaxed"), 12, {"exact": True, "theta": 0.8}, n_seen=0, parts=simulate.PARTS["H5"])
        relaxed = h5_world_claims.analyse(b, draws=99, extras=False, minimum=K.H5_RELAXED_HITS)
        self.assertEqual(relaxed["registered_version"]["eligibility"]["hit_minimum"], K.H5_RELAXED_HITS)
        primary = h5_world_claims.analyse(b, draws=99, extras=False)
        self.assertEqual(primary["registered_version"]["eligibility"]["hit_minimum"], K.H5_MIN_HITS_PER_GROUP)


class Uninformative(unittest.TestCase):
    def test_rule(self):
        cases = (((-0.10, 0.02), True), ((-0.30, -0.06), False), ((-0.04, 0.04), False), ((-0.01, 0.07), True))
        for interval, expected in cases:
            flag, _ = verdicts.uninformative(fake("H1", 0.1, interval=interval), "not determined")
            self.assertEqual(flag, expected, interval)
        self.assertTrue(verdicts.uninformative(fake("H1", 0.1), "not determinable")[0])
        self.assertEqual(K.UNINFORMATIVE_SESOI["H6"], math.log(2))

    def test_either_version_flags_the_result(self):
        result = dict(fake("H1", 0.0001, interval=(-0.3, -0.1)),
                      registered_version=fake("H1", 0.0001, interval=(-0.2, 0.1), version="registered"))
        final, _ = verdicts.finalise({"H1": result})
        self.assertTrue(final["H1"]["uninformative"])
        self.assertFalse(final["H1"]["versions"]["amended"]["uninformative"])


class Wording(unittest.TestCase):
    def test_supported_and_refuted_carry_the_verification_sentence(self):
        figures = {"all": {"third_model": "kappa 0.81", "known_answer": "recovery 9 of 10"}, "H1": {"cross_vendor": "kappa 0.74"}}
        result = dict(fake("H1", 0.0001), registered_version=fake("H1", 0.0001, version="registered"))
        final, _ = verdicts.finalise({"H1": result}, verification=figures)
        statement_text = final["H1"]["verdict_statement"]
        self.assertTrue(statement_text.startswith("supported (model-coded), verified by a third model (kappa 0.81), "
                                                  "on known-answer texts (recovery 9 of 10) and by a reader of another vendor (kappa 0.74)"))
        final, _ = verdicts.finalise({"H1": dict(fake("H1", 0.5, "refuted"), registered_version=fake("H1", 0.5, "refuted", version="registered"))})
        self.assertTrue(final["H1"]["verdict_statement"].startswith("refuted (model-coded), verified by a third model (figures not entered)"))
        self.assertNotIn("validat", json.dumps(final).lower())

    def test_the_word_validated_is_refused(self):
        with self.assertRaises(ValueError):
            verdicts.figures({"all": {"third_model": "validated by a model"}}, "H1")
        self.assertNotIn("validat", K.MODEL_CODED.lower())


# ---------------------------------------------------------------- the hold-out cross-check and the counts per source

def voice_file(audio, creator, group="holdout", model=K.ASR_MODEL_REQUIRED):
    info = {"language": "en"}
    if model:
        info["model_role"] = model
    return {"audio": audio, "creator": creator, "video_id": "v-" + audio, "group": group, "info": info, "words": 600,
            "map": {"format": "solo", "claimant": "sole_speaker", "main_kind": "claimed_voice", "opening_end_unit": None,
                    "closing_start_unit": None},
            "label_of_record": "middle", "units": [voice_unit(1, "V1", ("own_person_identity", 1)), voice_unit(2, "V2", ("announce", 1))],
            "synthetic": True}


class CrossCheck(unittest.TestCase):
    def table(self, folder, rows):
        simulate.mark_synthetic(folder)              # the permission check of 04:55 (f) opens only marked folders
        path = Path(folder, "recordings.csv")
        path.write_text("# synthetic\nvideo_id,group,title_like_column,asr_model_resolved\n"
                        + "".join(f"{video},holdout,x,{model}\n" for video, model in rows), encoding="utf-8")
        return str(path)

    def test_mismatch_excluded_and_counted(self):
        b = adapter.bundle(voice=[adapter.parse_voice(voice_file(a, "c" + a)) for a in ("a1", "a2", "a3")]
                           + [adapter.parse_voice(voice_file("s1", "d1", group="seen"))])
        with tempfile.TemporaryDirectory() as folder:
            path = self.table(folder, [("v-a1", "english_only"), ("'v-a2", "multilingual_inferred"), ("v-s1", "multilingual")])
            out = adapter.apply_asr_rule(b, K.ASR_MODEL_REQUIRED, crosscheck={"table": path, "synthetic": True})
            loaded = adapter.load_table_models(path, ["a1"], ["v-a1", "v-a2"])
        self.assertEqual(sorted(item["audio"] for item in out["recordings"]), ["a1", "a3", "s1"])    # seen is not checked
        holdout = out["asr_rule"]["by_group"]["holdout"]
        self.assertEqual(holdout["excluded_crosscheck_mismatch"], 1)
        self.assertEqual({k: holdout["crosscheck"][k] for k in ("checked", "agree", "disagree", "not_in_table")},
                         {"checked": 3, "agree": 1, "disagree": 1, "not_in_table": 1})
        self.assertNotIn("crosscheck", out["asr_rule"]["by_group"]["seen"])
        self.assertEqual(loaded, {"audio": {}, "video_id": {"v-a1": "english_only", "v-a2": "multilingual_inferred"}})

    def test_refused_before_freeze_2(self):
        b = adapter.bundle(voice=[adapter.parse_voice(voice_file("a1", "c1"))])
        with tempfile.TemporaryDirectory() as folder:
            path = self.table(folder, [("v-a1", "english_only")])
            with self.assertRaises(PermissionError):                         # the config does not mark the table synthetic
                adapter.apply_asr_rule(b, K.ASR_MODEL_REQUIRED, crosscheck={"table": path})
            real = dict(b, records=[dict(b["records"][0], synthetic=False)])
            with self.assertRaises(PermissionError):                         # real records: only after freeze 2
                adapter.apply_asr_rule(real, K.ASR_MODEL_REQUIRED, crosscheck={"table": path, "synthetic": True})
        self.assertIsNone(adapter.crosscheck_spec({"table": "x", "enabled": False}))

    def test_the_template_turns_it_on(self):
        template = json.loads(run.TEMPLATE.read_text(encoding="utf-8"))
        self.assertTrue(template["holdout_model_crosscheck"]["enabled"])
        self.assertEqual(template["asr_model_required"], K.ASR_MODEL_REQUIRED)
        rule = run.asr_rule_of(template)
        self.assertEqual(rule["crosscheck"]["groups"], ["holdout"])

    def test_counts_of_an_extra_source(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder, "voice")
            simulate.mark_synthetic(target)
            for data in (voice_file("a1", "c1"), voice_file("a2", "c2", model="multilingual")):
                (target / (data["audio"] + ".json")).write_text(json.dumps(data), encoding="utf-8")
            counted = run.source_rule_counts("extra", {"voice": str(target)}, {"required": K.ASR_MODEL_REQUIRED})
        self.assertEqual(counted["by_group"]["holdout"]["excluded_other_model"], 1)
        self.assertTrue(counted["applied"])


class A10Checks(unittest.TestCase):
    def test_dl_against_hksj(self):
        y, v = [0.1, -0.2, 0.3, 0.05], [0.01, 0.02, 0.015, 0.01]
        dl, hk = stats.re_dl(y, v), stats.re_hksj(y, v)
        self.assertAlmostEqual(dl["mu"], hk["mu"])
        z = stats.z_ppf(0.975)
        self.assertAlmostEqual(dl["intervals"]["0.95"][1] - dl["mu"], z * dl["se_dl"])

    def test_null_means_on_seen_creators(self):
        b = simulate.cohort(stats.seed_for("t-null"), 0, {"exact": True}, n_seen=12, parts=("voice", "asks", "titles", "content", "forecasts"))
        _, bands, parts = simulate.calibration_constants("H2")
        out = a10_checks.null_means(b, {"bands": bands, "parts": parts}, draws=49)
        self.assertAlmostEqual(out["H6"]["amended_OE_null_mean"], 0.0, places=12)
        self.assertIsNotNone(out["H6"]["registered_half_count_null_mean"])
        self.assertLess(out["H6"]["amended_OE_mean_at_plant"], 0)
        self.assertIn("registered_half_count_null_mean", out["H5"])
        self.assertIn("registered_permutation_reference_mean", out["H2"])
        self.assertIn("no seen recordings", a10_checks.null_means({"recordings": []}, {})["note"])

    def test_the_registered_h6_version_stays_uncentred_and_its_null_mean_is_reported(self):
        """Registry 04:55 (k): the registered H6 half-count version is not recentred; its null mean on seen creators is
        reported with its flag (report.json meta.a10_7_null_means_on_seen_creators, from run.analyse)."""
        import inspect
        b = simulate.cohort(stats.seed_for("t-null-h6"), 12, {"exact": True}, parts=("voice", "asks"))
        result = h6_asks.analyse(b, extras=False, draws=99)
        totals = {c: h6_asks._sum(rows) for c, rows in h6_asks.creator_tables(common_confirmatory(b), vs.definition()).items()}
        mean = sum(h6_asks.half_count(t) for t in totals.values()) / len(totals)
        self.assertAlmostEqual(result["registered_version"]["estimate"]["mean_half_count_log_ratio"], mean)   # no centring
        seen = simulate.cohort(stats.seed_for("t-null-h6-seen"), 0, {"exact": True}, n_seen=12, parts=("voice", "asks"))
        out = a10_checks.null_means(seen, {}, draws=9)["H6"]
        self.assertIn(out["registered_flag"], ("centred", "recentring needed"))
        self.assertIsNotNone(out["registered_half_count_null_mean"])
        self.assertIn("a10_7_null_means_on_seen_creators", inspect.getsource(run.analyse))


def common_confirmatory(bundle):
    from hypotheses import common
    return common.confirmatory(bundle)


# ---------------------------------------------------------------- the lead's decisions of 2026-11-21 04:55

def garbage_folder(folder, name="x.json"):
    """A folder with a file that is not JSON: opening and parsing it would raise ValueError, so a PermissionError shows
    that the permission check ran before the file was opened."""
    Path(folder).mkdir(parents=True, exist_ok=True)
    Path(folder, name).write_text("not json {", encoding="utf-8")
    return str(folder)


class PermissionBeforeOpening(unittest.TestCase):
    """04:55 (f): every loader calls the permission check before it lists a folder or opens a file."""

    def test_every_loader_refuses_an_unmarked_folder_without_opening_it(self):
        with tempfile.TemporaryDirectory() as root:
            folder = garbage_folder(Path(root, "voice"))
            for load in (adapter.load_voice, adapter.load_asks, adapter.load_features, adapter.load_titles,
                         lambda f: adapter.load_forecasts(f, {}), lambda f: adapter.load_content(f, {})):
                with self.assertRaises(PermissionError):
                    load(folder)
            with self.assertRaises(PermissionError):
                adapter.read_json(Path(folder, "x.json"))
            with self.assertRaises(PermissionError):
                adapter.load_bundle({"voice": folder, "asks": folder})
            with self.assertRaises(PermissionError):
                adapter.load_model_map(Path(folder, "x.json"), ["a"], ["v"])
            # TABLE's CSV reader is a loader too (verifier, 2026-11-21): a readable table in an unmarked folder is refused
            Path(folder, "t.csv").write_text("video_id,asr_model_resolved\nv,english_only\n", encoding="utf-8")
            with self.assertRaises(PermissionError):
                adapter.load_table_models(Path(folder, "t.csv"), ["a"], ["v"])

    def test_the_production_tree_stays_closed_even_when_marked(self):
        with tempfile.TemporaryDirectory() as root:
            for group in ("holdout", "other"):
                folder = Path(root, "labels", group, "voice")
                simulate.mark_synthetic(folder)
                garbage_folder(folder)
                self.assertTrue(adapter.production_tree(folder))
                with self.assertRaises(PermissionError):
                    adapter.load_voice(str(folder))
            seen = Path(root, "labels", "seen", "voice")
            self.assertFalse(adapter.production_tree(seen))

    def test_a_real_file_is_refused_before_any_field_is_read(self):
        from unittest import mock
        real = statement(quote="syn in one scenario syn")
        data = {"audio": "a1", "creator": "c1", "group": "holdout", "statements": [real], "frozen_utc": "2026-11-21T00:00:00Z"}
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root, "forecasts")
            simulate.mark_synthetic(folder)
            (folder / "a1.json").write_text(json.dumps(data), encoding="utf-8")
            with mock.patch.object(wording, "shared_wording", side_effect=AssertionError("the H2 flag rule ran")) as rule:
                with self.assertRaises(PermissionError):
                    adapter.load_bundle({"forecasts": str(folder)})
                rule.assert_not_called()

    def test_synthetic_marked_folders_load(self):
        bundle, files = simulate.cohort(stats.seed_for("t-marked"), 3, {"exact": True}, parts=("voice", "asks"), raw=True)
        with tempfile.TemporaryDirectory() as root:
            paths = simulate.write_files(root, files)
            self.assertTrue(adapter.synthetic_folder(paths["voice"]))
            loaded = adapter.load_bundle({"voice": paths["voice"], "asks": paths["asks"]})
        self.assertEqual(len(loaded["recordings"]), len(bundle["recordings"]))
        self.assertIsNotNone(adapter.freeze2_problem())                       # the check was the pre-freeze-2 one


class GuardNotDeterminable(unittest.TestCase):
    """04:55 (g): a version that is not determinable makes the result 'not determinable', naming the version, and
    uninformative; 'versions differ' stays for two determinable versions that disagree."""

    def test_amended_not_determinable(self):
        amended = dict(fake("H2", 0.0001, determinable=False), eligibility={"creators": 8, "minimum": 9})
        result = dict(amended, registered_version=fake("H2", 0.0001, version="registered"))
        final, holm = verdicts.finalise({"H2": result})
        self.assertEqual(final["H2"]["verdict_kind"], "not determinable")
        self.assertTrue(final["H2"]["verdict"].startswith("not determinable in the amended version: too few eligible creators (8 of 9)"))
        # the registered version is judged on the guarded Holm step (p = 1 from the unusable amended version)
        self.assertIn("registered version: not determined (Holm step)", final["H2"]["verdict"])
        self.assertTrue(final["H2"]["uninformative"])
        self.assertIsNone(final["H2"]["verdict_statement"])
        self.assertEqual(holm["H2"]["input_p"], 1.0)

    def test_registered_not_determinable(self):
        registered = dict(fake("H5", 0.0001, determinable=False, version="registered"), eligibility={"creators": 11, "minimum": 12})
        final, _ = verdicts.finalise({"H5": dict(fake("H5", 0.0001), registered_version=registered)})
        self.assertEqual(final["H5"]["verdict_kind"], "not determinable")
        self.assertTrue(final["H5"]["verdict"].startswith("not determinable in the registered version: too few eligible creators (11 of 12)"))
        self.assertIn("amended version: not determined (Holm step)", final["H5"]["verdict"])
        self.assertTrue(final["H5"]["uninformative"])

    def test_both_not_determinable(self):
        same = dict(fake("H1", 0.5, determinable=False), eligibility={"creators": 11, "minimum": 12})
        final, _ = verdicts.finalise({"H1": dict(same, registered_version=dict(same, version="registered"))})
        self.assertEqual(final["H1"]["verdict"], "not determinable: too few eligible creators (11 of 12)")
        other = dict(fake("H9", 0.5, determinable=False), eligibility={"creators": 7, "minimum": None})
        final, _ = verdicts.finalise({"H9": dict(dict(same, hypothesis="H9"), registered_version=dict(other, version="registered"))})
        self.assertTrue(final["H9"]["verdict"].startswith("not determinable in both versions (amended: too few eligible creators (11 of 12); "))
        self.assertEqual(final["H9"]["verdict_kind"], "not determinable")

    def test_rows_follow_the_same_rule(self):
        amended = dict(fake("H2", 0.0001, determinable=False), eligibility={"creators": 8, "minimum": 9})
        row = dict(amended, registered_version=fake("H2", 0.0001, version="registered"))
        primary = dict(fake("H2", 0.0001), registered_version=fake("H2", 0.0001, version="registered"))
        final, _ = verdicts.finalise({"H2": primary}, {"H2": [("a row", row)]})
        self.assertEqual(final["H2"]["rows"][0]["verdict_kind"], "not determinable")
        self.assertTrue(final["H2"]["rows"][0]["uninformative"])
        self.assertFalse(final["H2"]["robust_to_the_labeller"])


class MantelHaenszelInterval(unittest.TestCase):
    """04:55 (j): until the coverage repeat, the MH estimates of H5 and H6 carry the wider of the creator-bootstrap
    percentile and the t interval, elementwise; a constant that freeze 2 can switch."""

    def test_rule(self):
        self.assertEqual(K.MH_INTERVAL_RULE, "wider")
        self.assertEqual(stats.mh_interval((0.1, 0.5), (0.2, 0.7)), (0.1, 0.7))
        self.assertEqual(stats.mh_interval((0.1, 0.5), (None, None)), (0.1, 0.5))
        self.assertEqual(stats.mh_interval((0.1, 0.5), (0.2, 0.7), rule="bootstrap_percentile"), (0.1, 0.5))
        self.assertEqual(stats.mh_interval((0.1, 0.5), (0.2, 0.7), rule="t"), (0.2, 0.7))
        with self.assertRaises(ValueError):
            stats.mh_interval((0.1, 0.5), (0.2, 0.7), rule="narrower")

    def test_jackknife_t(self):
        items = [1.0, 2.0, 4.0, 7.0]
        lo, hi = stats.jackknife_t_interval(items, lambda xs: sum(xs) / len(xs), 0.90)
        m, tlo, thi = stats.t_interval(items, 0.90)                   # for a mean the jackknife SE is the usual SE
        self.assertAlmostEqual(lo, tlo)
        self.assertAlmostEqual(hi, thi)
        self.assertEqual(stats.jackknife_t_interval(items[:2], lambda xs: 0.0), (None, None))

    def test_h5_and_h6_carry_the_wider_interval(self):
        b = simulate.cohort(stats.seed_for("t-mh"), 12, {"exact": True, "theta": 0.8, "rr": 0.4}, parts=("voice", "asks", "titles", "content"))
        h5 = h5_world_claims.analyse(b, extras=False, draws=199)
        ints = h5["intervals"]
        self.assertEqual(ints["mh_90_log_or"], stats.wider_interval(ints["bootstrap_90_log_or"], ints["jackknife_t90_log_or"]))
        self.assertEqual(h5["creator_interval_90"], ints["mh_90_log_or"])
        self.assertEqual(ints["mh_interval_rule"], "wider")
        h6 = h6_asks.analyse(b, extras=False, draws=199)
        ints = h6["intervals"]
        self.assertEqual(ints["mh_90"], stats.wider_interval(ints["bootstrap_90_mh"], ints["jackknife_t90_mh"]))
        self.assertAlmostEqual(h6["creator_interval_90"][0], math.log(ints["mh_90"][0]))
        self.assertEqual(simulate.a5_interval("H5", h5), h5["intervals"]["mh_90_log_or"])     # the battery's coverage column


class TwoStageRegisteredIntervals(unittest.TestCase):
    """04:55 (d): each registered version uses the interval its text registers. H2, H5 and H6 register a
    creator-bootstrap interval, which catalogue rule R1 draws as creators, then recordings; H1 and H4 register the pool's
    interval (no bootstrap), so their registered versions keep the DerSimonian-Laird interval."""

    def test_two_stage_draws_recordings_within_creators(self):
        creators = [[1.0], [2.0], [3.0, 5.0]]
        lo, hi, failed = stats.bootstrap_two_stage(creators, lambda s: sum(sum(r) / len(r) for r in s) / len(s), 499, ("t",))
        self.assertEqual(failed, 0)
        self.assertLess(lo, hi)
        self.assertEqual(stats.resample_list([], stats.rng("t")), [])

    def test_tallies_reproduce_creator_d(self):
        b, _ = simulate.cohort(stats.seed_for("t-tallies"), 4, {"exact": True, "beta": -0.7}, parts=("voice", "forecasts"), raw=True)
        _, bands, parts = simulate.calibration_constants("H2")
        recordings = {}
        by_creator = h2_hedging.statements_by_creator(common_confirmatory(b), bands=bands, parts=parts, by_recording=recordings)
        for creator, rows in by_creator.items():
            d, v = h2_hedging.creator_d(rows)
            td, tv = h2_hedging.d_from_tallies([h2_hedging.recording_tallies(r) for r in recordings[creator].values()])
            self.assertAlmostEqual(d, td)
            self.assertAlmostEqual(v, tv)

    def test_registered_versions_name_the_procedure(self):
        b = simulate.cohort(stats.seed_for("t-two-stage"), 12, {"exact": True, "theta": 0.8, "rr": 0.4, "beta": -0.7},
                            parts=("voice", "asks", "titles", "content", "forecasts"))
        _, bands, parts = simulate.calibration_constants("H2")
        h2 = h2_hedging.analyse(b, bands=bands, parts=parts, extras=False, draws=99, permutations=99)
        h5 = h5_world_claims.analyse(b, extras=False, draws=99)
        h6 = h6_asks.analyse(b, extras=False, draws=99)
        for result in (h2, h5, h6):
            self.assertEqual(result["registered_version"]["intervals"]["bootstrap"], "creators, then recordings (R1)")
            lo, hi = result["registered_version"]["creator_interval_90"]
            self.assertTrue(lo is not None and hi is not None and lo < hi)
        h1 = h1_rate.analyse(simulate.cohort(stats.seed_for("t-h1-dl"), 12, {"exact": True}, parts=("voice", "features")), extras=False)
        self.assertIn("dl_90", h1["registered_version"]["intervals"])            # H1: the pool's interval (as coded)
        self.assertEqual(h1["registered_version"]["creator_interval_90"], h1["registered_version"]["intervals"]["dl_90"])

    def test_h5_sides_are_resampled_apart(self):
        row = {"per_recording": {"A": [(1.0, 0.0)] * 3, "B": [(0.0, 1.0)] * 2}}
        drawn = h5_world_claims._resample_sides(row, stats.rng("t-sides"))
        self.assertEqual((len(drawn["A"]), len(drawn["B"])), (3, 2))
        self.assertEqual(set(drawn["A"]), {(1.0, 0.0)})


class H5RandomEffectsRow(unittest.TestCase):
    """04:55 (c): H5's random-effects sensitivity row of A10.7 uses HKSJ; the registered version keeps DerSimonian-Laird."""

    def test_row(self):
        b = simulate.cohort(stats.seed_for("t-h5-re"), 12, {"exact": True, "theta": 0.8}, parts=simulate.PARTS["H5"])
        result = h5_world_claims.analyse(b, draws=99)
        row = result["secondary"]["random-effects sensitivity row: half-count estimator pooled by HKSJ (A10.7 point 2)"]
        self.assertIsNone(row["verdict"])
        reg = result["registered_version"]
        self.assertEqual(row["creators"], reg["eligibility"]["creators"])
        self.assertAlmostEqual(row["mu"], reg["estimate"]["half_count_log_ratio_difference"])     # same tau^2 and weights
        self.assertNotEqual(tuple(row["hksj_90"]), tuple(reg["intervals"]["dl_90"]))              # t(k-1) HKSJ, not DL normal
        self.assertIn("dl_90", reg["intervals"])
        self.assertEqual(row["p_method"], "exact")


class H2FrameRow(unittest.TestCase):
    """Second reading of 04:55: a time window taken only from the period of the talk (where FRAME) counts as NO."""

    def test_score(self):
        framed_yes = adapter.parse_statement(statement({"time_window": "YES", "place": "YES"}, where="FRAME"))
        self.assertEqual(framed_yes["parts"]["record"]["time_window"], ("YES", "FRAME"))
        self.assertEqual(h2_hedging.score(framed_yes, parts=PARTS, frame_time_window="no"), 0)        # place FRAME: not counted either
        self.assertEqual(h2_hedging.score(framed_yes, parts=PARTS, where=("STATEMENT", "CONTEXT", "FRAME"), frame_time_window="no"), 1)
        framed_ct = adapter.parse_statement(statement({"time_window": "CANNOT_TELL"}, where="FRAME"))
        self.assertIsNone(h2_hedging.score(framed_ct, parts=PARTS))                                   # primary: missing
        self.assertEqual(h2_hedging.score(framed_ct, parts=PARTS, frame_time_window="no"), 0)         # the row: NO
        plain = adapter.parse_statement(statement({"time_window": "YES"}))
        self.assertEqual(h2_hedging.score(plain, parts=PARTS, frame_time_window="no"), 1)

    def test_the_row_is_built(self):
        rows = dict(h2_hedging.rows())
        self.assertEqual(rows[h2_hedging.FRAME_ROW], {"frame_time_window": "no"})
        self.assertEqual(K.H2_FRAME_WHERE, "FRAME")


class ModelStratifiedRow(unittest.TestCase):
    """03:08 and 04:55 (b): other-model and unknown-model transcripts go into one model-stratified sensitivity row."""

    def bundle(self):
        files = [voice_file("h1", "c1"), voice_file("h2", "c2", model="multilingual"), voice_file("h3", "c3", model=None),
                 voice_file("s1", "d1", group="seen", model="multilingual"), voice_file("s2", "d2", group="seen")]
        conflict = voice_file("h4", "c1")
        asks = {"audio": "h4", "creator": "c1", "group": "holdout", "asks": [], "info": {"model_role": "multilingual"}, "synthetic": True}
        return adapter.bundle(voice=[adapter.parse_voice(f) for f in files + [conflict]], asks=[adapter.parse_asks(asks)])

    def test_the_row_holds_other_and_unknown_models_and_not_conflicts(self):
        out = adapter.apply_asr_rule(self.bundle(), K.ASR_MODEL_REQUIRED)
        self.assertEqual(sorted(item["audio"] for item in out["recordings"]), ["h1", "s2"])        # the primary, as before
        view = adapter.model_stratified_view(out)
        self.assertTrue(view["asr_rule"]["stratified"])
        self.assertEqual(sorted((item["audio"], item["asr_stratum"]) for item in view["recordings"]),
                         [("h1", "english_only"), ("h2", "multilingual"), ("h3", "unknown"), ("s1", "multilingual"),
                          ("s2", "english_only")])
        holdout = out["asr_rule"]["by_group"]["holdout"]
        self.assertEqual(holdout["in_model_stratified_row"], 3)
        self.assertEqual(holdout["model_stratified_row_by_model"], {"english_only": 1, "multilingual": 1, "unknown": 1})
        self.assertEqual(out["asr_rule"]["model_stratified_row"]["added_to_the_primary"], 3)
        self.assertNotIn("asr_stratum", out["recordings"][0])                                    # the primary items are not tagged
        with self.assertRaises(ValueError):
            adapter.model_stratified_view(self.bundle())

    def test_a_label_model_that_table_disputes_stays_out_of_the_row(self):
        """README (b) and item 12, constants.py: hold-out recordings whose TABLE model differs stay out of the row (their
        model is in dispute), whatever model the labels state; a recording whose labels state no model has nothing in
        dispute and stays in as unknown (verifier, 2026-11-21)."""
        files = [voice_file("h1", "c1"), voice_file("h2", "c2", model="multilingual"), voice_file("h3", "c3", model=None)]
        b = adapter.bundle(voice=[adapter.parse_voice(f) for f in files])
        with tempfile.TemporaryDirectory() as folder:
            simulate.mark_synthetic(folder)
            path = Path(folder, "recordings.csv")
            path.write_text("video_id,asr_model_resolved\nv-h1,multilingual_inferred\nv-h2,english_only\nv-h3,english_only\n",
                            encoding="utf-8")
            out = adapter.apply_asr_rule(b, K.ASR_MODEL_REQUIRED, crosscheck={"table": str(path), "synthetic": True})
        self.assertEqual(out["recordings"], [])
        self.assertEqual([(item["audio"], item["asr_stratum"]) for item in out["recordings_model_stratified"]], [("h3", "unknown")])
        holdout = out["asr_rule"]["by_group"]["holdout"]
        self.assertEqual((holdout["excluded_crosscheck_mismatch"], holdout["in_model_stratified_row"]), (1, 1))
        self.assertEqual(holdout["crosscheck"]["disagree"], 3)

    def test_the_row_is_specified_for_every_hypothesis(self):
        ruled = adapter.apply_asr_rule(self.bundle(), K.ASR_MODEL_REQUIRED)
        specs = [(h, name) for h, name, source, options in run.row_specs(ruled, []) if options.get("asr_stratified")]
        self.assertEqual(sorted(h for h, _ in specs), sorted(K.THIS_TRACK))
        self.assertTrue(all(name == K.ASR_STRATIFIED_ROW for _, name in specs))
        self.assertFalse(any(options.get("asr_stratified") for *_, options in run.row_specs({"recordings": [], "titles": None}, [])))

    def test_comparisons_stay_within_one_model(self):
        # H2: the length band is crossed with the model
        b = forecast_bundle({"c1": [statement({"time_window": "YES"}, quote=f"syn {i}") for i in range(4)]})
        b = dict(b, recordings=[dict(item, asr_stratum="multilingual") for item in b["recordings"]], asr_rule={"stratified": True})
        band = h2_hedging.band_of(12, (10, 20))                     # statement() has 12 words
        rows = h2_hedging.statements_by_creator(b, bands=(10, 20), parts=PARTS)["c1"]
        self.assertEqual({row[0] for row in rows}, {(band, "multilingual")})
        plain = h2_hedging.statements_by_creator(dict(b, asr_rule={}), bands=(10, 20), parts=PARTS)["c1"]
        self.assertEqual({row[0] for row in plain}, {band})
        # H5: sides in different models do not pair up
        titles = {"final": {"vA1": {"presentation": "P1", "voiced_by": "C", "cues": ["CH_WORD"], "kind_cues": ["K0"], "source_families": []},
                            "vA2": {"presentation": "P1", "voiced_by": "C", "cues": ["CH_WORD"], "kind_cues": ["K0"], "source_families": []},
                            "vB1": {"presentation": "P0", "voiced_by": "NA", "cues": [], "kind_cues": ["K0"], "source_families": []},
                            "vB2": {"presentation": "P0", "voiced_by": "NA", "cues": [], "kind_cues": ["K0"], "source_families": []}}}
        content = {"units": {1: {"primary": "Q1", "secondary": "NONE", "weight": 6}, 2: {"primary": "Q4", "secondary": "NONE", "weight": 6}},
                   "mode": "systematic", "failed_units": 0}
        items = [{"audio": v, "creator": "c1", "group": "holdout", "video_id": v, "content": content,
                  "asr_stratum": "english_only" if v.startswith("vA") else "multilingual"} for v in ("vA1", "vA2", "vB1", "vB2")]
        mixed = {"recordings": items, "titles": titles, "asr_rule": {"stratified": True}}
        self.assertEqual(h5_world_claims.creator_tables(mixed), {})                         # A and B never meet within a model
        self.assertEqual(sorted(h5_world_claims.creator_tables(dict(mixed, asr_rule={}))), ["c1"])
        # H9: a hold-out cell is paired only with seen cells of its own model
        from hypotheses import h9_family
        pairs = h9_family.Pairs([{"a": 1.0}, {"a": 1.0}, {"a": 1.0}], [0], [1, 2], ["S1", "S1"], ["S1"], mask=[[True, False]])
        self.assertEqual((pairs.ns, pairs.count), ([1], [{"S1": 1}]))
        unmasked = h9_family.Pairs([{"a": 1.0}, {"a": 1.0}, {"a": 1.0}], [0], [1, 2], ["S1", "S1"], ["S1"])
        self.assertEqual((unmasked.ns, unmasked.count), ([2], [{"S1": 2}]))


class NoSilentWave(unittest.TestCase):
    """04:55 (h): no replication wave exists; the hold-out is the only confirmation sample, and no code path pools a
    recording of another group into a confirmatory estimate."""

    def test_only_the_holdout_is_confirmatory(self):
        from hypotheses import common
        self.assertEqual(K.CONFIRMATORY_GROUPS, ("holdout",))
        b = simulate.cohort(stats.seed_for("t-wave"), 12, {"exact": True, "mu1": -0.15}, parts=("voice", "features"))
        base = h1_rate.analyse(b, extras=False)
        wave = [dict(item, group="wave", creator="w" + item["creator"]) for item in b["recordings"]]
        pooled = dict(b, recordings=b["recordings"] + wave)
        self.assertEqual(len(common.confirmatory(pooled)["recordings"]), len(b["recordings"]))
        again = h1_rate.analyse(pooled, extras=False)
        self.assertEqual((again["eligibility"]["creators"], again["p"]), (base["eligibility"]["creators"], base["p"]))


class A10Numbering(unittest.TestCase):
    """04:55 (l): A10.k = CAL-A(7+k) in every code comment, docstring and the README."""

    def test_every_pairing(self):
        import re
        here = Path(__file__).resolve().parents[1]
        texts = [path.read_text(encoding="utf-8") for path in sorted(here.glob("*.py"))] + [(here / "README.md").read_text(encoding="utf-8")]
        pairs = []
        for text in texts:
            # "A10.k = CAL-Aj", "A10.k, CAL-Aj", "A10.k (CAL-Aj"; and "CAL-Aj = A10.k", "CAL-Aj (A10.k" (a comma after
            # CAL-Aj starts the next item of a list, so it pairs nothing)
            pairs += [(int(a), int(c)) for a, c in re.findall(r"A10\.(\d)\s*(?:=|,|\()\s*CAL-A(\d+)", text)]
            pairs += [(int(a), int(c)) for c, a in re.findall(r"CAL-A(\d+)\s*(?:=|\()\s*A10\.(\d)", text)]
        self.assertGreater(len(pairs), 10)
        self.assertEqual([pair for pair in pairs if pair[1] != pair[0] + 7], [])


if __name__ == "__main__":
    unittest.main()
