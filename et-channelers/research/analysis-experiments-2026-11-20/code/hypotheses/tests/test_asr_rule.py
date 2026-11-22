"""The ASR-model rule (lead's decision before any label existed): H1, H2, H4, H5, H6 and H9 use only recordings whose
resolved recognizer model is the run's English-only model; another model, an unknown model or sources that disagree
are excluded and counted per group, the same way in every group. Synthetic records only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from hypotheses import adapter  # noqa: E402
from hypotheses import constants as K  # noqa: E402
from hypotheses import h1_rate  # noqa: E402
from hypotheses import run  # noqa: E402
from hypotheses import simulate  # noqa: E402
from hypotheses import voice_sets as vs  # noqa: E402

ENGLISH = K.ASR_MODEL_REQUIRED


def unit(i, label, words):
    view = {"label": label, "label_b": label, "detail": "none", "cue": ["none", 0], "flags": [], "own_broad": label == "V1"}
    return {"id": i, "first": 0, "last": 0, "n_words": words, "map": label, "small": view, "middle": view, "label": label,
            "label_b": label, "own_broad": view["own_broad"]}


def voice_file(audio, creator, group="holdout", model=ENGLISH, synthetic=True):
    """A recording that qualifies for H1 (an own and a claimed span of 300 words, sole speaker, solo)."""
    info = {"language": "en"}
    if model is not None:
        info["model_role"] = model
    return {"audio": audio, "creator": creator, "video_id": "v-" + audio, "group": group, "info": info, "publisher_audio": False,
            "words": 600, "map": {"format": "solo", "claimant": "sole_speaker", "main_kind": "claimed_voice", "opening_end_unit": None,
                                  "closing_start_unit": None},
            "label_of_record": "middle", "units": [unit(1, "V1", 300), unit(2, "V2", 300)], "synthetic": synthetic}


def asks_file(audio, creator, group="holdout", model=None):
    data = {"audio": audio, "creator": creator, "video_id": "v-" + audio, "group": group, "asks": [], "synthetic": True}
    if model is not None:
        data["info"] = {"language": "en", "model_role": model}
    return data


def make_bundle(voice_files, asks_files=(), features_files=()):
    return adapter.bundle(voice=[adapter.parse_voice(v) for v in voice_files], asks=[adapter.parse_asks(a) for a in asks_files],
                          features=[adapter.parse_features(f) for f in features_files])


class ModelOfAFile(unittest.TestCase):
    def test_label_files_state_the_bundle_role(self):
        self.assertEqual(adapter.parse_voice(voice_file("a1", "c1"))["asr_model"], ENGLISH)
        self.assertIsNone(adapter.parse_voice(voice_file("a1", "c1", model=None))["asr_model"])      # role absent
        for empty in ("", "none", "None", "not_recorded", "unknown"):
            self.assertIsNone(adapter.parse_voice(voice_file("a1", "c1", model=empty))["asr_model"])
        self.assertEqual(adapter.parse_voice(voice_file("a1", "c1", model=" English_Only "))["asr_model"], ENGLISH)
        explicit = dict(voice_file("a1", "c1"), asr_model_resolved="multilingual_inferred")
        self.assertEqual(adapter.parse_voice(explicit)["asr_model"], "multilingual_inferred")     # explicit field first
        self.assertEqual(adapter.parse_features({"audio": "a1", "creator": "c1", "units": [], "asr_model": "multilingual"})["asr_model"],
                         "multilingual")


class Rule(unittest.TestCase):
    def test_other_and_unknown_models_are_excluded_and_counted_per_group(self):
        b = make_bundle([voice_file("h1", "c1"), voice_file("h2", "c2", model="multilingual"), voice_file("h3", "c3", model=None),
                         voice_file("h4", "c1", model="multilingual"),
                         voice_file("s1", "d1", group="seen"), voice_file("s2", "d2", group="seen", model=None)])
        out = adapter.apply_asr_rule(b, ENGLISH)
        self.assertEqual(sorted(item["audio"] for item in out["recordings"]), ["h1", "s1"])
        rule = out["asr_rule"]
        self.assertEqual(rule["required"], ENGLISH)
        self.assertEqual((rule["recordings"], rule["kept"], rule["excluded"]), (6, 2, 4))
        holdout, seen = rule["by_group"]["holdout"], rule["by_group"]["seen"]
        self.assertEqual((holdout["recordings"], holdout["kept"], holdout["excluded"]), (4, 1, 3))
        self.assertEqual((holdout["excluded_other_model"], holdout["excluded_unknown_model"], holdout["excluded_conflicting_sources"]),
                         (2, 1, 0))
        self.assertEqual(holdout["other_models"], {"multilingual": 2})
        self.assertEqual((holdout["creators"], holdout["creators_with_an_excluded_recording"], holdout["creators_with_no_recording_left"]),
                         (3, 3, 2))
        self.assertEqual((seen["kept"], seen["excluded_unknown_model"], seen["excluded_other_model"]), (1, 1, 0))
        self.assertEqual(len(b["recordings"]), 6)                                   # the input bundle is not changed
        self.assertEqual(out["records"], b["records"])                              # the guard still sees every record
        json.dumps(rule)                                                            # counts only, serialisable

    def test_the_same_recording_is_treated_alike_in_every_group(self):
        for group in ("seen", "holdout", "other"):
            out = adapter.apply_asr_rule(make_bundle([voice_file("a1", "c1", group=group, model="multilingual"),
                                                      voice_file("a2", "c1", group=group)]), ENGLISH)
            self.assertEqual([item["audio"] for item in out["recordings"]], ["a2"])
            self.assertEqual(out["asr_rule"]["by_group"][group]["excluded_other_model"], 1)

    def test_an_excluded_recording_leaves_the_eligible_count(self):
        b = make_bundle([voice_file("h1", "c1"), voice_file("h2", "c2", model="multilingual"), voice_file("h3", "c3", model=None)])
        self.assertEqual(h1_rate.eligible(b, vs.definition())["creators"], 3)        # every one qualifies on labels
        self.assertEqual(h1_rate.eligible(adapter.apply_asr_rule(b, ENGLISH), vs.definition())["creators"], 1)

    def test_sources_that_disagree_are_excluded(self):
        b = make_bundle([voice_file("a1", "c1"), voice_file("a2", "c1"), voice_file("a3", "c1")],
                        asks_files=[asks_file("a1", "c1", model="multilingual"), asks_file("a2", "c1")],          # a2: asks state none
                        features_files=[{"audio": "a3", "creator": "c1", "group": "holdout", "units": [], "asr_model": "multilingual"}])
        out = adapter.apply_asr_rule(b, ENGLISH)
        self.assertEqual([item["audio"] for item in out["recordings"]], ["a2"])
        self.assertEqual(out["asr_rule"]["by_group"]["holdout"]["excluded_conflicting_sources"], 2)

    def test_a_model_name_is_required(self):
        with self.assertRaises(ValueError):
            adapter.apply_asr_rule(make_bundle([voice_file("a1", "c1")]), None)


class ModelFile(unittest.TestCase):
    def test_csv_keeps_only_id_and_model_of_bundle_rows(self):
        b = make_bundle([voice_file("a1", "c1", model=None), voice_file("a2", "c1"), voice_file("a3", "c2", model=None)])
        with tempfile.TemporaryDirectory() as folder:
            simulate.mark_synthetic(folder)          # the permission check of 04:55 (f) opens only marked folders before freeze 2
            path = Path(folder, "recordings.csv")
            path.write_text("# a comment line\n# another\nvideo_id,group,asr_model,asr_model_resolved,other\n"
                            "v-a1,holdout,english_only,english_only,x\n"
                            "v-a2,holdout,not_recorded,multilingual_inferred,y\n"
                            "'v-a3,holdout,english_only,english_only,z\n"
                            "v-zz,holdout,english_only,english_only,w\n", encoding="utf-8")
            kept = adapter.load_model_map(path, ["a1", "a2", "a3"], ["v-a1", "v-a2", "v-a3"])
            out = adapter.apply_asr_rule(b, ENGLISH, models=str(path))
        self.assertEqual(kept["video_id"], {"v-a1": ENGLISH, "v-a2": "multilingual_inferred", "v-a3": ENGLISH})   # v-zz dropped
        self.assertEqual(kept["audio"], {})
        # a1: the file supplies the model; a2: the file disagrees with the label file; a3: the apostrophe is repaired
        self.assertEqual(sorted(item["audio"] for item in out["recordings"]), ["a1", "a3"])
        self.assertEqual(out["asr_rule"]["by_group"]["holdout"]["excluded_conflicting_sources"], 1)
        self.assertTrue(out["asr_rule"]["model_file"])

    def test_json_layouts(self):
        b = make_bundle([voice_file("a1", "c1", model=None), voice_file("a2", "c1", model=None)])
        layouts = ({"recordings": [{"video_id": "v-a1", "model": "english_only"}, {"video_id": "v-a2", "model": None}]},
                   [{"audio": "a1", "asr_model_resolved": "english_only"}],
                   {"a1": "english_only", "v-a2": "multilingual"})
        expected = (["a1"], ["a1"], ["a1"])
        for layout, want in zip(layouts, expected):
            with tempfile.TemporaryDirectory() as folder:
                simulate.mark_synthetic(folder)
                path = Path(folder, "models.json")
                path.write_text(json.dumps(layout), encoding="utf-8")
                out = adapter.apply_asr_rule(b, ENGLISH, models=str(path))
            self.assertEqual([item["audio"] for item in out["recordings"]], want)


class Loading(unittest.TestCase):
    def test_load_bundle_applies_the_rule_from_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder, "voice")
            simulate.mark_synthetic(target)
            for data in (voice_file("a1", "c1"), voice_file("a2", "c2", model="multilingual"), voice_file("a3", "c3", model=None)):
                (target / (data["audio"] + ".json")).write_text(json.dumps(data), encoding="utf-8")
            paths = {"voice": str(target)}
            ruled = adapter.load_bundle(paths, ENGLISH)
            plain = adapter.load_bundle(paths)                                       # synthetic: the rule may be left off
        self.assertEqual([item["audio"] for item in ruled["recordings"]], ["a1"])
        self.assertEqual(ruled["asr_rule"]["by_group"]["holdout"]["excluded"], 2)
        self.assertEqual(len(plain["recordings"]), 3)
        self.assertNotIn("asr_rule", plain)

    def test_real_records_need_the_frozen_rule(self):
        real = [adapter.parse_voice(voice_file("a1", "c1", synthetic=False))]
        for required in (None, "", "multilingual"):
            with self.assertRaises(PermissionError):
                adapter.require_asr_rule(real, required)
        adapter.require_asr_rule(real, ENGLISH)
        adapter.require_asr_rule(real, "English_Only")
        adapter.require_asr_rule([adapter.parse_voice(voice_file("a1", "c1"))], None)           # synthetic passes without it

    def test_run_config(self):
        self.assertEqual(run.asr_rule_of({}), {"required": ENGLISH, "models": None})          # the frozen default
        self.assertEqual(run.asr_rule_of({"asr_model_required": None}), {"required": None, "models": None})
        self.assertEqual(run.asr_rule_of({"asr_model_required": "English_Only", "asr_models": "m.csv"}),
                         {"required": ENGLISH, "models": "m.csv"})


if __name__ == "__main__":
    unittest.main()
