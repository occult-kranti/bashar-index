"""The lead's decisions of 2026-11-21 06:44 ("Hypothesis code, decisions on the second verification"), items (1) to (5)
and (9): the seen-only path, the one freeze-2 record, H6 centred per recording, H9's two-stage bootstrap, A5 on both
intervals of H5 and H6, and creator-by-model strata for H5. Synthetic records and temporary folders only: no test
opens the production label tree."""
import contextlib
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import a10_checks, adapter, common  # noqa: E402
from hypotheses import constants as K  # noqa: E402
from hypotheses import h2_hedging, h4_contraction, h5_world_claims, h6_asks, h9_family  # noqa: E402
from hypotheses import run, simulate, stats, verdicts  # noqa: E402
from hypotheses import voice_sets as vs  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
ALL_PARTS = ("voice", "features", "asks", "forecasts", "titles", "content", "h9")


def seen_tree(root, seed="t-seen-tree", n_seen=12):
    """A synthetic labels/seen tree (every folder marked) under root/labels; returns (labels folder, in-memory bundle)."""
    bundle, files = simulate.cohort(stats.seed_for(seed), 0, {"exact": True, "theta": 0.8}, n_seen=n_seen, parts=ALL_PARTS, raw=True)
    labels = Path(root, "labels")
    simulate.write_files(labels / "seen", files)
    return labels, bundle


def view(label):
    return {"label": label, "label_b": label, "detail": "none", "cue": ["none", 0], "flags": [], "own_broad": label == "V1"}


def voice_record(audio, creator, group="seen", synthetic=False):
    units = [{"id": 1, "first": 0, "last": 9, "n_words": 10, "map": "V1", "small": view("V1"), "middle": view("V1"), "label": "V1",
              "label_b": "V1", "own_broad": True}]
    return {"audio": audio, "creator": creator, "video_id": "v-" + audio, "group": group,
            "info": {"language": "en", "model_role": K.ASR_MODEL_REQUIRED}, "words": 10,
            "map": {"format": "solo", "claimant": "sole_speaker", "main_kind": "own_talk"}, "label_of_record": "small",
            "units": units, "frozen_utc": "2026-11-21T04:58:22Z", "run_limit": None, "synthetic": synthetic}


def write(folder, name, data):
    Path(folder).mkdir(parents=True, exist_ok=True)
    Path(folder, name).write_text(json.dumps(data), encoding="utf-8")


def make_dir_link(target, link):
    """A directory symlink, else a junction (Windows without the symlink privilege); None where neither can be made."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return "symlink"
    except (OSError, NotImplementedError, AttributeError):
        pass
    try:
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
        return "junction"
    except Exception:                                    # noqa: BLE001 - no way to make a link here
        return None


# ---------------------------------------------------------------- (1) the seen-only path

class SeenOnlyPath(unittest.TestCase):
    """06:44 (1): before freeze 2, a loader that opens labels/seen only, refuses any other path and any record whose group
    is not seen (read first), for the FREEZE2 constants, the A10.7 null means and CAL part (f)."""

    def setUp(self):
        self.freeze2 = mock.patch.object(adapter, "FREEZE2", Path(tempfile.gettempdir(), "no-such-folder-0644", "freeze2.json"))
        self.freeze2.start()

    def tearDown(self):
        self.freeze2.stop()

    def test_a_synthetic_seen_tree_loads_and_gives_the_constants_of_the_cohort(self):
        with tempfile.TemporaryDirectory() as root:
            labels, memory = seen_tree(root)
            loaded = adapter.load_seen_bundle(labels)
            out = run.seen_constants(loaded, draws=49)
        self.assertTrue(loaded["seen_only"])
        self.assertEqual(len(loaded["recordings"]), len(memory["recordings"]))
        self.assertEqual(loaded["seen_files"]["voice"], len(memory["recordings"]))
        self.assertTrue(all(item["group"] == "seen" for item in loaded["recordings"]))
        ruled = adapter.apply_asr_rule(memory, K.ASR_MODEL_REQUIRED)
        self.assertEqual(out["FREEZE2"]["H4_YARDSTICK"], h4_contraction.yardstick_from_seen(ruled)[0])
        self.assertEqual(out["FREEZE2"]["H2_LENGTH_BANDS"], list(h2_hedging.length_bands_from_seen(ruled)))
        self.assertEqual(out["FREEZE2"]["H2_PARTS_RETAINED"], list(h2_hedging.parts_from_seen(ruled)[0]))
        self.assertIsNotNone(out["beside"]["H4_yardstick_middle_model"])
        self.assertAlmostEqual(out["a10_7_null_means_on_seen_creators"]["H6"]["amended_OE_null_mean"], 0.0, places=12)
        self.assertIn("registered_half_count_null_mean", out["a10_7_null_means_on_seen_creators"]["H5"])
        self.assertEqual(out["counts"]["asr_model_rule"]["kept"], len(memory["recordings"]))
        text = json.dumps(out, default=list)                # counts and derived numbers only: no creator or recording id
        self.assertNotIn("s000", text)
        self.assertNotIn("syn-", text)

    def test_the_constants_command_prints_counts_only(self):
        with tempfile.TemporaryDirectory() as root:
            labels, _ = seen_tree(root, "t-seen-command", n_seen=8)
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed):
                run.main(["constants", "--labels", str(labels), "--draws", "19"])
        out = json.loads(printed.getvalue())
        self.assertEqual(sorted(out["FREEZE2"]), ["H2_LENGTH_BANDS", "H2_PARTS_RETAINED", "H4_YARDSTICK"])
        self.assertTrue(out["synthetic"])
        self.assertNotIn("s000", printed.getvalue())

    def test_other_paths_are_refused_before_anything_is_opened(self):
        with tempfile.TemporaryDirectory() as root:
            labels, _ = seen_tree(root, "t-seen-other", n_seen=3)
            for group in ("holdout", "other"):
                folder = labels / group / "voice"
                simulate.mark_synthetic(folder)
                write(folder, "x.json", voice_record("h1", "c1", group=group, synthetic=True))
                self.assertIn("holdout or labels/other", adapter.seen_open_problem(folder, labels))
                with self.assertRaises(PermissionError):
                    adapter.json_seen_files(folder, labels)
                with self.assertRaises(PermissionError):
                    adapter.read_seen_json(folder / "x.json", labels)
            elsewhere = Path(root, "elsewhere", "voice")
            simulate.mark_synthetic(elsewhere)
            self.assertIn("outside labels/seen", adapter.seen_open_problem(elsewhere, labels))
            renamed = Path(root, "notlabels")
            simulate.write_files(renamed / "seen", {"voice": [], "features": [], "asks": [], "forecasts": [], "content": [], "titles": {}})
            with self.assertRaises(PermissionError):
                adapter.load_seen_bundle(renamed)
            unmarked = Path(root, "second", "labels")
            write(unmarked / "seen" / "voice", "a.json", voice_record("a", "c", synthetic=True))
            with self.assertRaises(PermissionError):              # outside the production tree: only marked folders
                adapter.load_seen_bundle(unmarked)

    def test_links_into_the_holdout_tree_are_refused(self):
        with tempfile.TemporaryDirectory() as root:
            labels, _ = seen_tree(root, "t-seen-links", n_seen=3)
            target = labels / "holdout" / "voice"
            target.mkdir(parents=True)
            Path(target, "x.json").write_text("not json {", encoding="utf-8")   # a ValueError would show it was opened
            simulate.mark_synthetic(target)
            made = []
            try:
                link = labels / "seen" / "asks-linked"
                kind = make_dir_link(target, link)
                if kind:
                    made.append(link)
                    self.assertIn("holdout or labels/other", adapter.seen_open_problem(link, labels))
                    with self.assertRaises(PermissionError):
                        adapter.json_seen_files(link, labels)
                file_link = labels / "seen" / "voice" / "linked.json"
                try:
                    os.symlink(target / "x.json", file_link)
                    made.append(file_link)
                except (OSError, NotImplementedError):
                    file_link = None
                if file_link is not None:
                    with self.assertRaises(PermissionError):
                        adapter.load_seen_bundle(labels)
                if not made:
                    self.skipTest("neither a symlink nor a junction can be made here")
            finally:
                for path in made:                               # remove the links themselves, never their targets
                    try:
                        if path.is_dir():
                            os.rmdir(path)                      # a junction or a directory symlink (Windows)
                        else:
                            os.unlink(path)
                    except OSError:
                        os.unlink(path)

    def test_the_group_field_is_read_first(self):
        with tempfile.TemporaryDirectory() as root:
            labels, _ = seen_tree(root, "t-seen-group", n_seen=2)
            folder = labels / "seen" / "voice"
            # sorted before the seen files, so that it is the first file read
            write(folder, "aa-holdout.json", voice_record("zz", "c9", group="holdout", synthetic=True))
            with mock.patch.object(adapter, "not_for_analysis", side_effect=AssertionError("a marker was read")) as markers, \
                    mock.patch.object(adapter, "parse_voice", side_effect=AssertionError("a label field was read")) as parse:
                with self.assertRaises(PermissionError):
                    adapter.read_seen_json(folder / "aa-holdout.json", labels)
                with self.assertRaises(PermissionError):
                    adapter.load_seen_bundle(labels, instruments=("voice",))
                markers.assert_not_called()
                parse.assert_not_called()
            Path(folder, "aa-holdout.json").unlink()
            nogroup = dict(voice_record("zy", "c8", synthetic=True))
            nogroup.pop("group")
            write(folder, "zy.json", nogroup)
            with self.assertRaises(PermissionError):
                adapter.load_seen_bundle(labels, instruments=("voice",))
            Path(folder, "zy.json").unlink()
            pilot = {"a1": {"statements": [], "group": "seen"}}         # the pilot mapping names no group at its top
            write(labels / "seen" / "forecasts", "pilot.json", pilot)
            with self.assertRaises(PermissionError):
                adapter.load_seen_bundle(labels, instruments=("voice", "forecasts"))

    def test_the_production_tree_reads_real_seen_files_and_nothing_else(self):
        with tempfile.TemporaryDirectory() as root:
            production = Path(root, "llm", "labels")
            write(production / "seen" / "voice", "a1.json", voice_record("a1", "c1"))
            write(production / "holdout" / "voice", "h1.json", voice_record("h1", "d1", group="holdout"))
            with mock.patch.object(adapter, "PRODUCTION_LABELS", production):
                self.assertIsNotNone(adapter.freeze2_problem())
                loaded = adapter.load_seen_bundle(instruments=("voice",))
                self.assertEqual([item["audio"] for item in loaded["recordings"]], ["a1"])
                self.assertFalse(loaded["records"][0]["synthetic"])        # a real seen file, before freeze 2
                with self.assertRaises(PermissionError):                   # the ordinary loaders stay closed to it
                    adapter.load_bundle({"voice": str(production / "seen" / "voice")})
                with self.assertRaises(PermissionError):
                    adapter.load_bundle({"voice": str(production / "holdout" / "voice")})
                write(production / "seen" / "voice", "h2.json", voice_record("h2", "d2", group="holdout"))
                with self.assertRaises(PermissionError):                   # a hold-out record placed in labels/seen
                    adapter.load_seen_bundle(instruments=("voice",))
                Path(production, "seen", "voice", "h2.json").unlink()
                with self.assertRaises(PermissionError):                   # real records only under the frozen rule
                    adapter.load_seen_bundle(instruments=("voice",), asr_model_required=None)
                limited = dict(voice_record("a2", "c2"), run_limit=3)
                write(production / "seen" / "voice", "a2.json", limited)
                with self.assertRaises(ValueError):                        # label-files.md: never analyse a limited run
                    adapter.load_seen_bundle(instruments=("voice",))

    def test_a_real_file_outside_the_production_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            labels, _ = seen_tree(root, "t-seen-real", n_seen=2)
            write(labels / "seen" / "voice", "r1.json", voice_record("r1", "c7", synthetic=False))
            with self.assertRaises(PermissionError):
                adapter.load_seen_bundle(labels, instruments=("voice",))

    def test_the_overstatement_is_gone(self):
        """The adapter reads a file's markers before it refuses it (verifier, 2026-11-21): the text says so."""
        self.assertNotIn("before any field of it is read", (HERE / "adapter.py").read_text(encoding="utf-8"))
        self.assertNotIn("before any field is read", (HERE / "README.md").read_text(encoding="utf-8"))
        self.assertNotIn("the registered quantity after the merge", (HERE / "simulate.py").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- (2) the one freeze-2 record

class Freeze2Record(unittest.TestCase):
    """06:44 (2): llm/freeze2.json with the six keys of 02:45; this code checks analysis_code_sha256 against its modules
    and constants_sha256; a record that lacks a key fails closed."""

    def record(self):
        return dict({"freeze1_frozen_utc": "2026-11-21T04:58:22Z", "sha256": {"produce.py": "0" * 64}, "registry_commit": "abc1234",
                     "written_at_utc": "2026-11-21T09:00:00Z"}, **adapter.freeze2_entry())

    def check(self, record):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root, "freeze2.json")
            path.write_text(record if isinstance(record, str) else json.dumps(record), encoding="utf-8")
            return adapter.freeze2_problem(path)

    def test_the_record_is_the_llm_one_with_the_six_keys(self):
        self.assertEqual(adapter.FREEZE2, adapter.LLM / "freeze2.json")
        self.assertEqual(adapter.FREEZE2.parent.name, "llm")
        self.assertEqual(len(adapter.FREEZE2_KEYS), 6)
        source = adapter.LLM / "fc_common.py"                # produce's key list, where the private folder exists
        if source.is_file():
            line = next(line for line in source.read_text(encoding="utf-8").splitlines() if line.startswith("FREEZE2_KEYS"))
            self.assertEqual(tuple(json.loads("[" + line.split("(", 1)[1].rsplit(")", 1)[0] + "]")), adapter.FREEZE2_KEYS)
        self.assertNotIn('HERE / "freeze2.json"', (HERE / "adapter.py").read_text(encoding="utf-8"))

    def test_one_record_satisfies_this_check(self):
        record = self.record()
        # registry 2026-11-21 12:52 (6): the constants are entered; the refusal while any one of them is None stays
        for name in ("H4_YARDSTICK", "H2_LENGTH_BANDS", "H2_PARTS_RETAINED"):
            with mock.patch.object(K, name, None):
                self.assertEqual(self.check(record), "FREEZE2 constants are not set (H4_YARDSTICK, H2_LENGTH_BANDS, "
                                                     "H2_PARTS_RETAINED)", name)
        self.assertIsNone(self.check(record))                    # the constants as entered in constants.py
        with mock.patch.object(K, "H4_YARDSTICK", 0.1), mock.patch.object(K, "H2_LENGTH_BANDS", (10, 20)), \
                mock.patch.object(K, "H2_PARTS_RETAINED", ("time_window",)):
            self.assertIsNone(self.check(record))
            with tempfile.TemporaryDirectory() as root:          # the guard opens to real records under that record
                path = Path(root, "freeze2.json")
                path.write_text(json.dumps(record), encoding="utf-8")
                with mock.patch.object(adapter, "FREEZE2", path):
                    adapter.require_permission([{"synthetic": False}])
                    broken = dict(record)
                    broken.pop("registry_commit")
                    path.write_text(json.dumps(broken), encoding="utf-8")
                    with self.assertRaises(PermissionError):
                        adapter.require_permission([{"synthetic": False}])

    def test_a_missing_or_empty_key_fails_closed(self):
        for key in adapter.FREEZE2_KEYS:
            record = self.record()
            record.pop(key)
            self.assertIn(f"lacks {key}", self.check(record), key)
            record[key] = "" if key not in ("sha256", "analysis_code_sha256") else {}
            self.assertIn(f"lacks {key}", self.check(record), key)
        self.assertIn("not JSON", self.check("not json {"))
        self.assertIn("not a JSON object", self.check("[1, 2]"))
        self.assertIn("as a dict", self.check(dict(self.record(), analysis_code_sha256=["adapter.py"])))
        self.assertIn("not a sha256", self.check(dict(self.record(), constants_sha256="x" * 64)))
        self.assertIn("not a commit hash", self.check(dict(self.record(), registry_commit="HEAD")))
        self.assertIn("does not exist", adapter.freeze2_problem(Path(tempfile.gettempdir(), "no-such-0644", "freeze2.json")))

    def test_changed_uncovered_and_constants(self):
        record = self.record()
        changed = dict(record, analysis_code_sha256=dict(record["analysis_code_sha256"], **{"stats.py": "0" * 64}))
        self.assertEqual(self.check(changed), "changed since freeze 2 (analysis_code_sha256): stats.py")
        missing = dict(record["analysis_code_sha256"])
        missing.pop("h9_family.py")
        self.assertEqual(self.check(dict(record, analysis_code_sha256=missing)),
                         "freeze2.json does not hash these modules (analysis_code_sha256): h9_family.py")
        gone = dict(record["analysis_code_sha256"], **{"no_such_module.py": "0" * 64})
        self.assertIn("no_such_module.py", self.check(dict(record, analysis_code_sha256=gone)))
        self.assertIn("constants_sha256 is not the sha256", self.check(dict(record, constants_sha256="0" * 64)))
        absolute = {str(HERE / name): value for name, value in record["analysis_code_sha256"].items()}
        self.assertIsNone(self.check(dict(record, analysis_code_sha256=absolute)))      # absolute paths are read too
        with mock.patch.object(K, "H2_PARTS_RETAINED", None):       # registry 12:52 (6): the constants are entered
            self.assertTrue(self.check(dict(record, analysis_code_sha256=absolute)).startswith("FREEZE2 constants"))

    def test_hashes_prints_the_two_keys(self):
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            run.main(["hashes"])
        text = printed.getvalue()
        entry = json.loads(text[:text.rindex("}") + 1])
        self.assertEqual(sorted(entry), ["analysis_code_sha256", "constants_sha256"])
        self.assertEqual(sorted(entry["analysis_code_sha256"]), adapter.code_files())
        self.assertIn("freeze 2 status (llm/freeze2.json):", text)


# ---------------------------------------------------------------- (3) H6 centred per recording

def recording(a, b, wc, wo):
    return {"a": a, "b": b, "wc": wc, "wo": wo, "unchecked": 0, "neither": 0}


class H6CentredPerRecording(unittest.TestCase):
    """06:44 (3): OE = (a - sum_i T_i s_i) / T and the MH rate ratio with creator-by-recording strata; the registered
    version unchanged; the A10.7 null check covers the new statistic."""

    def test_the_statistic(self):
        rows = [recording(2, 1, 900, 100), recording(1, 4, 100, 900)]
        expected = (3 - (3 * 0.9 + 5 * 0.1)) / 8
        self.assertAlmostEqual(h6_asks.oe_value(rows), expected)
        self.assertAlmostEqual(h6_asks.pooled_oe_value(rows), 3 / 8 - 0.5)
        single = recording(2, 3, 300, 700)
        self.assertAlmostEqual(h6_asks.oe_value(single), 2 / 5 - 0.3)          # one recording: CAL-A11's OE
        self.assertEqual(h6_asks.oe_values([single, rows]), [h6_asks.oe_value(single), h6_asks.oe_value(rows)])
        strata = [(2, 1, 900, 100), (1, 4, 100, 900)]
        self.assertAlmostEqual(h6_asks.mh_ratio([rows]), stats.mh_rate_ratio(strata)[0])
        self.assertNotAlmostEqual(h6_asks.mh_ratio([rows]), stats.mh_rate_ratio([(3, 5, 1000, 1000)])[0])

    def test_null_mean_zero_where_the_pooled_oe_is_not(self):
        """The worked example of the verifier (2026-11-21): equal-length recordings with claimed shares 0.9 and 0.1 and
        ask rates 1 and 5 per 1,000 words; no difference inside either recording."""
        def expectation(statistic, t1, t2, s1=0.9, s2=0.1):
            total = 0.0
            for a1 in range(t1 + 1):
                for a2 in range(t2 + 1):
                    weight = math.comb(t1, a1) * s1 ** a1 * (1 - s1) ** (t1 - a1) * math.comb(t2, a2) * s2 ** a2 * (1 - s2) ** (t2 - a2)
                    rows = [recording(a1, t1 - a1, 900 * s1 / 0.9, 900 * (1 - s1) / 0.9), recording(a2, t2 - a2, 1000 * s2, 1000 * (1 - s2))]
                    total += weight * statistic(rows)
            return total
        for t1, t2 in ((1, 5), (2, 9), (3, 3)):
            self.assertAlmostEqual(expectation(h6_asks.oe_value, t1, t2), 0.0, places=12)
        self.assertLess(expectation(h6_asks.pooled_oe_value, 1, 5), -0.2)        # about -0.27, in H6's direction

    def test_the_a10_7_check_covers_the_new_statistic(self):
        b = simulate.cohort(stats.seed_for("t-h6-a107"), 0, {"exact": True, "ask_rate_by_share": simulate.H6_HETEROGENEITY},
                            n_seen=30, parts=("voice", "asks"))
        out = a10_checks.h6_null(a10_checks.seen_only(b))
        self.assertEqual(out["amended_OE_null_mean"], 0.0)
        self.assertEqual(out["amended_flag"], "centred")
        self.assertIn("per recording", out["amended_OE"])
        self.assertLess(out["pooled_OE_before_0644_null_mean"], -0.02)           # the pooled OE leans to H6's side
        self.assertLess(out["amended_OE_mean_at_plant"], -0.05)
        self.assertIsNotNone(out["registered_half_count_null_mean"])

    def test_simulated_null_with_rates_that_differ_between_recordings(self):
        b = simulate.cohort(stats.seed_for("t-h6-hetero"), 120, {"exact": True, "rr": 1.0, "ask_rate_by_share": simulate.H6_HETEROGENEITY},
                            parts=("voice", "asks"))
        tables = h6_asks.creator_tables(common.confirmatory(b), vs.primary_definition("H6"))
        rows = [r for _, r in sorted(tables.items()) if sum(x["a"] + x["b"] for x in r) >= 1]
        new = [h6_asks.oe_value(r) for r in rows]
        se = stats.sd(new) / math.sqrt(len(new))
        self.assertLess(abs(stats.mean(new)), 3 * se)
        bias = [sum((x["a"] + x["b"]) * x["wc"] / (x["wc"] + x["wo"]) for x in r) / sum(x["a"] + x["b"] for x in r)
                - h6_asks._sum(r)["wc"] / (h6_asks._sum(r)["wc"] + h6_asks._sum(r)["wo"]) for r in rows]
        self.assertLess(stats.mean(bias), -0.03)              # the pooled OE's conditional bias given the T_i

    def test_analyse_uses_recording_strata_and_keeps_the_registered_version(self):
        b = simulate.cohort(stats.seed_for("t-h6-strata"), 12, {"exact": True, "rr": 0.3}, parts=("voice", "asks"))
        result = h6_asks.analyse(b, extras=False, draws=99)
        tables = h6_asks.creator_tables(common.confirmatory(b), vs.definition())
        hit = [c for c in sorted(tables) if h6_asks._sum(tables[c])["a"] + h6_asks._sum(tables[c])["b"] >= 1]
        self.assertEqual([result["creator_values"][c] for c in hit], [h6_asks.oe_value(tables[c]) for c in hit])
        strata = [(r["a"], r["b"], r["wc"], r["wo"]) for c in hit for r in tables[c]]
        self.assertAlmostEqual(result["estimate"]["mh_rate_ratio"], stats.mh_rate_ratio(strata)[0])
        self.assertIn("creator by recording", result["estimate"]["strata"])
        registered = result["registered_version"]
        totals = {c: h6_asks._sum(rows) for c, rows in tables.items()}
        self.assertAlmostEqual(registered["estimate"]["mean_half_count_log_ratio"],
                               sum(h6_asks.half_count(t) for t in totals.values()) / len(totals))

    def test_the_battery_has_the_heterogeneous_null(self):
        self.assertIn(("H6", "null_heterogeneous", 12, 1.0, 30), simulate.plan(quick=True))
        self.assertEqual(simulate.experiment_cfg("H6", 1.0, "null_heterogeneous")["ask_rate_by_share"], simulate.H6_HETEROGENEITY)
        self.assertNotIn("ask_rate_by_share", simulate.experiment_cfg("H6", 1.0, "null"))
        rows = simulate.task(("H6", "null_heterogeneous", 12, 1.0, 0, 2))["rows"]
        self.assertTrue(all("p_pooled_oe_before_0644" in row for row in rows))


# ---------------------------------------------------------------- (4) H9's two-stage bootstrap

class H9TwoStage(unittest.TestCase):
    """06:44 (4): creators, then recordings within creators, every cell re-rarefied in every draw, for both versions."""

    @classmethod
    def setUpClass(cls):
        b = simulate.cohort(stats.seed_for("t-h9-two-stage"), 8, {"exact": True, "h9_content": 0.12}, n_seen=12, parts=simulate.PARTS["H9"])
        cls.bundle = b
        cls.held, cls.seen = h9_family._comparable(h9_family.cells(b))

    def test_sampling_without_replacement(self):
        stream = stats.rng("t-sample")
        for n, k in ((50, 20), (50, 40), (7, 7), (7, 9)):
            picks = list(h9_family._sample_indices(n, k, stream))
            self.assertEqual(len(picks), min(n, k))
            self.assertEqual(len(set(picks)), min(n, k))
            self.assertTrue(all(0 <= i < n for i in picks))
        counts = [0] * 10
        for _ in range(3000):
            for i in h9_family._sample_indices(10, 3, stream):
                counts[i] += 1
        self.assertTrue(all(abs(c - 900) < 120 for c in counts), counts)      # 3000 x 0.3 each, SE about 25

    def test_rarefied_counts_and_vectors_match_the_primary_code(self):
        encoder = h9_family._Encoder(self.held + self.seen)
        stream = stats.rng("t-vectors")
        counters = [h9_family._rarefied_counts(encoder, cell["parts"], K.H9_RAREFY_TOKENS, stream) for cell in self.held + self.seen]
        for counter, cell in zip(counters, self.held + self.seen):
            self.assertEqual(sum(counter.values()), min(K.H9_RAREFY_TOKENS, cell["words"]))
        tokens = {code: token for token, code in encoder.content.items()}
        words = {code: word for word, code in encoder.function.items()}
        drawn = [({tokens[c]: n for c, n in counter.items() if c in tokens}, {words[c]: n for c, n in counter.items() if c in words})
                 for counter in counters]
        tfidf, zs = h9_family.vectorize(drawn)
        fast, norms, fast_zs = h9_family._draw_vectors(encoder, counters, set())
        nh = len(self.held)
        sim = h9_family._content_similarities(fast[:nh], norms[:nh], fast[nh:], norms[nh:], encoder.n_content)
        for h in range(nh):
            for s in range(0, len(self.seen), 3):
                self.assertAlmostEqual(sim[h][s], h9_family._cosine(tfidf[h], tfidf[nh + s]), places=9)
                self.assertAlmostEqual(math.sumprod(fast_zs[h], fast_zs[nh + s]), h9_family._cosine(zs[h], zs[nh + s]), places=9)
        big = h9_family._content_similarities(fast[:nh], norms[:nh], fast[nh:], norms[nh:], 10 ** 5)   # the gather path
        self.assertAlmostEqual(big[0][1], sim[0][1], places=12)

    def test_every_draw_resamples_recordings_and_rerarefies(self):
        calls = []
        original = h9_family._rarefied_counts

        def spy(encoder, parts, tokens, stream):
            calls.append([id(part) for part in parts])
            return original(encoder, parts, tokens, stream)
        with mock.patch.object(h9_family, "_rarefied_counts", side_effect=spy):
            (lo, hi), failed = h9_family._bootstrap_delta(self.held, self.seen, 5, ("t-spy",), 0.9)
        creators = len({c["creator"] for c in self.held}) + len({c["creator"] for c in self.seen})
        self.assertGreaterEqual(len(calls), 5 * creators)                   # every drawn cell is re-rarefied in every draw
        self.assertTrue(any(len(set(ids)) < len(ids) for ids in calls))      # recordings are drawn with replacement
        again = h9_family._bootstrap_delta(self.held, self.seen, 5, ("t-spy",), 0.9)
        self.assertEqual(again, ((lo, hi), failed))                          # deterministic

    def test_both_versions_carry_the_two_stage_interval(self):
        result = h9_family.analyse(self.bundle, extras=False, draws=19, permutations=99)
        self.assertIn("then recordings", result["intervals"]["bootstrap"])
        self.assertEqual(result["intervals"]["bootstrap_draws"], 19)
        self.assertEqual(result["registered_version"]["intervals"], result["intervals"])
        self.assertEqual(result["registered_version"]["creator_interval_90"], result["creator_interval_90"])

    def test_the_battery_draw_count_is_named(self):
        import inspect
        self.assertLess(simulate.H9_BATTERY_BOOTSTRAP_DRAWS, K.BOOTSTRAP_DRAWS)
        self.assertIn("H9_BATTERY_BOOTSTRAP_DRAWS", inspect.getsource(simulate._run_one))


# ---------------------------------------------------------------- (5) A5 on both intervals of H5 and H6

class A5OnBothIntervals(unittest.TestCase):
    """06:44 (5): A5 holds only if both the t interval on the creator OE values and the wider MH interval exclude zero on
    the predicted side."""

    def test_h6(self):
        b = simulate.cohort(stats.seed_for("t-a5-h6"), 12, {"exact": True, "rr": 0.25}, parts=("voice", "asks"))
        result = h6_asks.analyse(b, extras=False, draws=199)
        parts = result["conditions"]["a5_parts"]
        self.assertEqual(parts["t90_OE_below_zero"], result["intervals"]["t90_OE"][1] < 0)
        self.assertEqual(parts["mh_90_below_one"], result["intervals"]["mh_90"][1] < 1)
        self.assertEqual(result["conditions"]["a5"], parts["t90_OE_below_zero"] and parts["mh_90_below_one"])
        self.assertTrue(parts["t90_OE_below_zero"])
        with mock.patch.object(stats, "mh_interval", return_value=(0.2, 1.3)):
            wide = h6_asks.analyse(b, extras=False, draws=99)
        self.assertTrue(wide["conditions"]["a5_parts"]["t90_OE_below_zero"])
        self.assertFalse(wide["conditions"]["a5"])
        final, _ = verdicts.finalise({"H6": wide})
        self.assertNotEqual(final["H6"]["versions"]["amended"]["verdict_kind"], "supported")

    def test_h5(self):
        b = simulate.cohort(stats.seed_for("t-a5-h5"), 14, {"exact": True, "theta": 0.8}, parts=simulate.PARTS["H5"])
        result = h5_world_claims.analyse(b, extras=False, draws=199)
        parts = result["conditions"]["a5_parts"]
        self.assertEqual(parts["t90_OE_above_zero"], result["intervals"]["t90_OE"][0] > 0)
        self.assertEqual(parts["mh_90_log_or_above_zero"], result["intervals"]["mh_90_log_or"][0] > 0)
        self.assertEqual(result["conditions"]["a5"], parts["t90_OE_above_zero"] and parts["mh_90_log_or_above_zero"])
        self.assertTrue(parts["t90_OE_above_zero"])
        with mock.patch.object(stats, "mh_interval", return_value=(-0.1, 1.2)):
            wide = h5_world_claims.analyse(b, extras=False, draws=99)
        self.assertTrue(wide["conditions"]["a5_parts"]["t90_OE_above_zero"])
        self.assertFalse(wide["conditions"]["a5"])


# ---------------------------------------------------------------- (9) creator-by-model strata for H5

def titled(presentation):
    return ({"presentation": "P1", "voiced_by": "C", "cues": ["CH_WORD"], "kind_cues": ["K0"], "source_families": []}
            if presentation == "A" else {"presentation": "P0", "voiced_by": "NA", "cues": [], "kind_cues": ["K0"], "source_families": []})


def content(world, practice):
    return {"units": {1: {"primary": "Q1", "secondary": "NONE", "weight": world}, 2: {"primary": "Q4", "secondary": "NONE", "weight": practice}},
            "mode": "systematic", "failed_units": 0}


class H5CreatorByModelStrata(unittest.TestCase):
    """06:44 (9): in the model-stratified row H5's strata are creator by model, so no side contrast mixes models."""

    def bundle(self, stratified=True):
        plan = [("vA1", "english_only", 9, 3), ("vA2", "english_only", 8, 4), ("vB1", "english_only", 3, 9), ("vB2", "english_only", 2, 10),
                ("vA3", "multilingual", 4, 8), ("vB3", "multilingual", 1, 23)]
        items = [{"audio": v, "creator": "c1", "group": "holdout", "video_id": v, "content": content(w, p), "asr_stratum": model}
                 for v, model, w, p in plan]
        titles = {"final": {v: titled(v[1]) for v, *_ in plan}}
        return {"recordings": items, "titles": titles, "asr_rule": {"stratified": True} if stratified else {}}

    def test_strata_oe_mh_and_half_count(self):
        row = h5_world_claims.creator_tables(self.bundle())["c1"]
        self.assertEqual([cell["stratum"] for cell in row["strata"]], ["english_only", "multilingual"])
        english, multi = row["strata"]
        self.assertEqual((english["WA"], english["PA"], english["WB"], english["PB"]), (17.0, 7.0, 5.0, 19.0))
        self.assertEqual((multi["WA"], multi["PA"], multi["WB"], multi["PB"]), (4.0, 8.0, 1.0, 23.0))
        self.assertEqual((row["WA"], row["PA"], row["WB"], row["PB"], row["recordings"]), (21.0, 15.0, 6.0, 42.0, 6))
        centred = (21 - (24 * 22 / 48 + 12 * 5 / 36)) / 36          # within each model: T_A,m x (W_m / T_m)
        self.assertAlmostEqual(h5_world_claims.oe(row), centred)
        self.assertNotAlmostEqual(h5_world_claims.oe(row), 21 / 36 - 27 / 84)   # the pooled contrast mixes the models
        ratio, _ = stats.mh_odds_ratio([(17, 7, 5, 19), (4, 8, 1, 23)])
        self.assertAlmostEqual(h5_world_claims.mh_log_or([row]), math.log(ratio))
        values = [math.log(17.5 / 7.5) - math.log(5.5 / 19.5), math.log(4.5 / 8.5) - math.log(1.5 / 23.5)]
        weights = [1 / (1 / 17.5 + 1 / 7.5 + 1 / 5.5 + 1 / 19.5), 1 / (1 / 4.5 + 1 / 8.5 + 1 / 1.5 + 1 / 23.5)]
        self.assertAlmostEqual(h5_world_claims.half_count_value(row), sum(w * v for w, v in zip(weights, values)) / sum(weights))
        self.assertAlmostEqual(h5_world_claims.half_count_variance(row), 1 / sum(weights))
        drawn = h5_world_claims._resample_sides(row, stats.rng("t-strata"))
        self.assertEqual([(len(cell["A"]), len(cell["B"])) for cell in drawn["strata"]], [(2, 2), (1, 1)])
        self.assertIsNotNone(h5_world_claims._two_stage_half_count_mu([drawn, drawn]))

    def test_outside_the_stratified_row_nothing_changes(self):
        row = h5_world_claims.creator_tables(self.bundle(stratified=False))["c1"]
        self.assertEqual(len(row["strata"]), 1)
        total = row["WA"] + row["PA"] + row["WB"] + row["PB"]
        self.assertEqual(h5_world_claims.oe(row), row["WA"] / (row["WA"] + row["PA"]) - (row["WA"] + row["WB"]) / total)
        ratio, _ = stats.mh_odds_ratio([(row["WA"], row["PA"], row["WB"], row["PB"])])
        self.assertEqual(h5_world_claims.mh_log_or([row]), math.log(ratio))
        self.assertEqual(h5_world_claims.half_count_value(row),
                         math.log((row["WA"] + 0.5) / (row["PA"] + 0.5)) - math.log((row["WB"] + 0.5) / (row["PB"] + 0.5)))
        drawn = h5_world_claims._resample_sides(row, stats.rng("t-one"))
        self.assertEqual(sorted(drawn), ["A", "B"])                          # the second stage of before, draw for draw


if __name__ == "__main__":
    unittest.main()
