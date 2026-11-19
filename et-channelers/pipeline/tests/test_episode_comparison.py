import copy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from pipeline import episode_comparison as comparison


def pin(value):
    return sha256(value.encode()).hexdigest()


def member(video, family=None, creator="sample"):
    row = {"video_id": video, "channel_dir": creator}
    if family:
        row.update(recording_family_id=family, recording_family_evidence_sha256=pin(family))
    return row


def observation(video, text, terms, *, assessed=("A", "B"), segments=None, creator="sample"):
    view = {"video_id": video, "channel_dir": creator, "source_kind": "publisher_text",
            "language": "en-GB", "text_version_id": pin(video + text), "raw_sha256": pin("raw" + text),
            "text_sha256": pin(text), "text": text, "offset_unit": "unicode_codepoint",
            "segments": segments or []}
    return {"view": view, "assessed_topics": list(assessed), "assessment_method_sha256": pin("review criteria"),
            "matches": [{"topic": topic, "char_start": text.index(word), "char_end": text.index(word) + len(word)}
                        for topic, word in terms]}


class EpisodeComparisonTests(unittest.TestCase):
    def test_episode_and_family_estimands_expose_selection_bounds(self):
        frame = [member(k, "one") for k in ("a", "b", "c")] + [member("d"), member("e")]
        obs = [observation(k, "yes", [("A", "yes")]) for k in ("a", "b", "c")]
        obs.append(observation("d", "no", []))
        out = comparison.compare(frame, obs, ["A", "B"])
        cell = out["heatmap"][0]
        self.assertEqual((cell["eligible_episodes"], cell["assessed_episodes"], cell["positive_families"]), (5, 4, 1))
        self.assertEqual(cell["episode_share"], 0.75)
        self.assertEqual(cell["family_balanced_observed_share"], 0.5)
        self.assertEqual(cell["family_balanced_frame_bounds"], [1 / 3, 2 / 3])
        self.assertEqual(cell["unresolved_family_singletons"], 2)
        self.assertEqual(cell["timing_of_assessed_episodes"], {"timed": 0, "partially_timed": 0, "untimed": 4})
        self.assertEqual(cell["supporting_video_ids"], ["a", "b", "c"])
        self.assertEqual(len(out["frame"]), 5)
        self.assertEqual(len(out["evidence"]), 4)

    def test_co_mentions_must_share_an_episode_and_assessment(self):
        frame = [member("a", "one"), member("b", "one"), member("c")]
        obs = [observation("a", "first", [("A", "first")]),
               observation("b", "other", [("B", "other")]),
               observation("c", "no B", [], assessed=("B",))]
        edge = comparison.compare(frame, obs, ["A", "B"])["same_episode_co_mentions"][0]
        self.assertEqual((edge["positive_families"], edge["assessed_episodes"], edge["episodes_with_either_topic"]), (0, 2, 2))
        self.assertEqual(edge["episode_jaccard"], 0)
        self.assertEqual(edge["family_balanced_frame_bounds"], [0, 0])
        self.assertEqual(edge["supporting_video_ids"], [])

    def test_unicode_and_distinct_cues_roundtrip_to_source_edition(self):
        view = observation("a", "🌞 A\nplus B", [("A", "A\nplus B"), ("B", "B")],
                           segments=[{"source_segment_id": "vtt:2", "char_start": 0, "char_end": 3,
                                      "time_start": 1.0, "time_end": 3.5},
                                     {"source_segment_id": "vtt:3", "char_start": 4, "char_end": 10,
                                      "time_start": 3.0, "time_end": 7.0}])
        result = comparison.compare([member("a")], [view], ["A", "B"])
        self.assertEqual(result["same_episode_co_mentions"][0]["episode_jaccard"], 1)
        entry = result["evidence"][0]
        self.assertEqual(entry["known_cue_union_seconds"], 6)
        self.assertEqual(entry["timing"], "timed")
        proof = entry["matches"][0]
        self.assertEqual((proof["char_start"], proof["char_end"]), (2, 10))
        self.assertEqual([(x["source_segment_id"], x["char_start"], x["time_end"]) for x in proof["source_segments"]],
                         [("vtt:2", 2, 3.5), ("vtt:3", 4, 7.0)])
        self.assertNotIn("text", entry)

    def test_untimed_incomplete_and_unassessed_stay_distinct(self):
        frame = [member("a"), member("b"), member("c", creator="other")]
        obs = [observation("a", "match", [("A", "match")]),
               observation("b", "one", [], assessed=("B",),
                           segments=[{"source_segment_id": "cue:0", "char_start": 0, "char_end": 3,
                                      "time_start": 0.7, "time_end": None}])]
        out = comparison.compare(frame, obs, ["A", "B"])
        cells = {(r["channel_dir"], r["topic"]): r for r in out["heatmap"]}
        self.assertIsNone(cells["other", "A"]["episode_share"])
        self.assertEqual(cells["other", "A"]["family_balanced_frame_bounds"], [0, 1])
        self.assertEqual(cells["sample", "B"]["timing_of_assessed_episodes"]["partially_timed"], 1)
        self.assertIsNone(out["evidence"][1]["known_cue_union_seconds"])
        self.assertEqual(out["evidence"][0]["matches"][0]["source_segments"], [])

    def test_invalid_groups_views_offsets_and_assessments_are_rejected(self):
        frame = [member("a")]
        obs = observation("a", "word", [("A", "word")])
        bad = [([dict(member("a"), recording_family_id="unconfirmed")], [obs]),
               (frame * 2, [obs]), (frame, [obs, obs]), (frame, [observation("a", "word", [], creator="wrong")])]
        for path, value in [(("view", "text_sha256"), pin("stale")), (("view", "language"), "de"),
                            (("assessed_topics",), ["B"]), (("assessment_method_sha256",), None),
                            (("view", "offset_unit"), "bytes"), (("matches", 0, "char_end"), 20)]:
            changed = copy.deepcopy(obs)
            leaf = changed
            for key in path[:-1]:
                leaf = leaf[key]
            leaf[path[-1]] = value
            bad.append((frame, [changed]))
        for rows, views in bad:
            with self.subTest(rows=len(rows), views=views), self.assertRaises(ValueError):
                comparison.compare(rows, views, ["A", "B"])

    def test_cli_uses_private_inputs_and_writes_reproducible_json(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for key, value in {"frame": {"rows": [member("a")]}, "topics": ["A"],
                               "observations": [observation("a", "sample", [], assessed=["A"])]}.items():
                (root / key).write_text(json.dumps(value), encoding="utf-8")
            args = [s for k in ("frame", "observations", "topics", "out") for s in ("--" + k, str(root / k))]
            comparison.main(args)
            result = json.loads((root / "out").read_bytes())
            self.assertEqual(result["heatmap"][0]["family_balanced_frame_bounds"], [0, 0])
            self.assertEqual(result["same_episode_co_mentions"], [])


if __name__ == "__main__":
    unittest.main()
