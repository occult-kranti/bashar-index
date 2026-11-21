"""The adapter against the layouts of llm/design/label-files.md (synthetic records only), and the battery's checkpoint."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import adapter  # noqa: E402
from hypotheses import h2_hedging, h5_world_claims, h9_family  # noqa: E402
from hypotheses import simulate, stats  # noqa: E402


def reading(presentation, family="S1"):
    return {"presentation": presentation, "cues": ["CH_WORD"] if presentation == "P1" else [], "voiced_by": "C" if presentation == "P1" else "NA",
            "sources": [], "source_families": ["FAM" + family] if presentation == "P1" else [], "topic_families": [],
            "kind_cues": ["K0"], "time_cue": "TC0", "time_also_portal": False, "language": "en"}


class Titles(unittest.TestCase):
    def test_per_creator_files(self):
        entries = [
            {"video_id": "v1", "audio": ["a1"], "primary": reading("P1"), "second": reading("P1"), "large": None,
             "record": reading("P1"), "record_from": "primary", "adjudicated_because": None},
            {"video_id": "v2", "audio": ["a2"], "primary": reading("P1"), "second": reading("P0"), "large": reading("P0"),
             "record": reading("P0"), "record_from": "large", "adjudicated_because": "disagreement"},
            {"video_id": "v3", "audio": [], "primary": {"failed": "twice"}, "second": reading("P2"), "large": {"failed": "twice"},
             "record": None, "record_from": None, "adjudicated_because": "record_failed"}]
        with tempfile.TemporaryDirectory() as folder:
            simulate.mark_synthetic(folder)          # the permission check opens only marked folders before freeze 2
            Path(folder, "0123456789abcdef.json").write_text(json.dumps({"creator": "c", "group": "holdout", "titles": entries,
                                                                         "synthetic": True}), encoding="utf-8")
            titles = adapter.load_titles(folder)
        self.assertEqual(titles["final"]["v1"]["presentation"], "P1")
        self.assertEqual(titles["final"]["v2"]["presentation"], "P0")           # the large model decided the dispute
        self.assertNotIn("v3", titles["final"])                                  # no record: absent, not a guess
        self.assertEqual(titles["middle"]["v2"]["presentation"], "P1")
        self.assertNotIn("v3", titles["middle"])                                 # failed reading left out
        self.assertEqual(titles["small"]["v3"]["presentation"], "P2")
        self.assertEqual(sorted(titles["large"]), ["v2"])
        self.assertEqual(titles["final"]["v1"]["source_families"], ["S1"])      # FAM prefix removed
        self.assertTrue(titles["_synthetic"])


class Forecasts(unittest.TestCase):
    def statement(self, **extra):
        base = {"key": "1-2-x", "verified": True, "duplicate": False, "statement_words": 12, "markers": {},
                "fc": {"values": {p: "NO" for p in ("time_window", "place", "named_actor", "observable_outcome", "quantity")},
                       "where": {p: "NA" for p in ("time_window", "place", "named_actor", "observable_outcome", "quantity")}},
                "fc_second": {"failed": "twice"}, "fd": {"committed": True, "four_way": "bare"}}
        base.update(extra)
        return base

    def test_second_reading_is_the_small_model_and_weights_use_inclusion_p(self):
        st = adapter.parse_statement(self.statement(coded=True, inclusion_p=0.25, valve_p=0.5, candidate_p=1.0))
        self.assertIn("small", st["parts"])
        self.assertIsNone(st["parts"]["small"])                                  # a failed reading is missing
        self.assertNotIn("second", st["parts"])
        self.assertAlmostEqual(st["weight"], 4.0)

    def test_uncoded_statement_is_out(self):
        st = adapter.parse_statement(self.statement(coded=False, inclusion_p=0.3, valve_p=0.0))
        self.assertFalse(st["verified"])

    def test_zero_valve_p_does_not_divide(self):
        st = adapter.parse_statement(self.statement(valve_p=0.0, candidate_p=0.5))
        self.assertAlmostEqual(st["weight"], 2.0)

    def test_r3_row_only_with_the_flag(self):
        names = [name for name, _ in h2_hedging.rows(routing=False)]
        self.assertNotIn("middle tier final where it judged (R3)", names)
        self.assertIn("middle tier final where it judged (R3)", [name for name, _ in h2_hedging.rows(routing=True)])


class Sentences(unittest.TestCase):
    def test_failed_units_out_and_coded_whole(self):
        data = {"audio": "a1", "creator": "c", "group": "holdout", "coded_whole": True, "too_short": False, "synthetic": True,
                "units": {"3": {"primary": "Q1", "secondary": "NONE", "group": "world_claim", "weight": 14},
                          "4": {"failed": "twice", "weight": 11}}}
        (item,) = adapter.parse_content(data, {})
        self.assertEqual(item["mode"], "whole")
        self.assertEqual(sorted(item["units"]), [3])
        self.assertEqual(item["failed_units"], 1)
        data["coded_whole"] = False
        self.assertEqual(adapter.parse_content(data, {})[0]["mode"], "systematic")


class Refusals(unittest.TestCase):
    # The folders carry the synthetic marker so that the permission check of 2026-11-21 04:55 (f) lets read_json open
    # the file; the smoke, limited and unfrozen refusals are then tested as before (they come first after parsing).
    def test_smoke_limited_and_unfrozen_files_are_refused(self):
        for extra in ({"smoke": True, "frozen_utc": None}, {"run_limit": 2, "frozen_utc": "2026-11-21T00:00:00Z"},
                      {"frozen_utc": None}):
            with tempfile.TemporaryDirectory() as folder:
                simulate.mark_synthetic(folder)
                path = Path(folder, "a.json")
                path.write_text(json.dumps(dict({"audio": "a", "creator": "c", "units": []}, **extra)), encoding="utf-8")
                with self.assertRaises(ValueError):
                    adapter.read_json(path)

    def test_synthetic_files_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            simulate.mark_synthetic(folder)
            path = Path(folder, "a.json")
            path.write_text(json.dumps({"audio": "a", "synthetic": True, "frozen_utc": None}), encoding="utf-8")
            self.assertEqual(adapter.read_json(path)["audio"], "a")

    def test_a_real_file_in_a_marked_folder_is_refused_before_freeze_2(self):
        with tempfile.TemporaryDirectory() as folder:
            simulate.mark_synthetic(folder)
            path = Path(folder, "a.json")
            path.write_text(json.dumps({"audio": "a", "creator": "c", "units": [], "frozen_utc": "2026-11-21T00:00:00Z"}),
                            encoding="utf-8")
            with self.assertRaises(PermissionError):
                adapter.read_json(path)


class EndToEndLayouts(unittest.TestCase):
    def test_h5_and_h9_read_the_same_from_disk(self):
        bundle, files = simulate.cohort(11, 12, {"exact": True, "theta": 0.8, "h9_content": 0.12}, n_seen=12, raw=True)
        with tempfile.TemporaryDirectory() as folder:
            paths = simulate.write_files(folder, files)
            self.assertTrue(Path(paths["titles"]).is_dir() and Path(paths["sentences"]).is_dir())
            loaded = adapter.load_bundle(paths)
        a = h5_world_claims.analyse(bundle, extras=False, draws=99)
        b = h5_world_claims.analyse(loaded, extras=False, draws=99)
        self.assertEqual(json.dumps(a, sort_keys=True, default=str), json.dumps(b, sort_keys=True, default=str))
        c = h9_family.analyse(bundle, extras=False, draws=19, permutations=99)
        d = h9_family.analyse(loaded, extras=False, draws=19, permutations=99)
        self.assertEqual(json.dumps(c, sort_keys=True, default=str), json.dumps(d, sort_keys=True, default=str))


class Checkpoint(unittest.TestCase):
    def test_resumed_battery_equals_fresh(self):
        tasks = [("H1", "null", 12, 0.0, 0, 2), ("H5", "null", 12, 0.0, 0, 2)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder, "cp.jsonl")
            fingerprint = simulate.task_fingerprint()
            first = simulate.task(tasks[0])
            # a checkpoint holding the first task, one line from other code, and a torn line
            path.write_text(json.dumps({"fingerprint": fingerprint, "key": simulate.task_key(tasks[0]), "result": first}) + "\n"
                            + json.dumps({"fingerprint": "other", "key": simulate.task_key(tasks[1]), "result": {}}) + "\n"
                            + '{"fingerprint": "', encoding="utf-8")
            done = simulate.read_checkpoint(path, fingerprint)
            self.assertEqual(list(done), [simulate.task_key(tasks[0])])
            fresh = simulate.task(tasks[0])
            self.assertEqual(json.loads(json.dumps(fresh["rows"])), done[simulate.task_key(tasks[0])]["rows"])
        self.assertEqual(stats.seed_for("a", 1), stats.seed_for("a", 1))


if __name__ == "__main__":
    unittest.main()
