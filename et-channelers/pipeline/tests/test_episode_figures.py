import csv
from hashlib import sha256
from importlib.util import find_spec
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree

from pipeline import episode_comparison as comparison, episode_figures as figures
from pipeline.tests.test_episode_comparison import member, observation


def invented_comparison():
    topics = ["Contact", "Frequency", "Healing", "Prediction"]
    frame, assessments = [], []
    for video, channel, family, present in [
            ("a1", "Aurora", "shared-performance", ["Contact", "Prediction"]),
            ("a2", "Aurora", None, ["Contact", "Frequency"]),
            ("a3", "Aurora", None, []),
            ("g1", "Grove", "shared-performance", ["Contact", "Prediction"]),
            ("g2", "Grove", None, ["Frequency", "Prediction", "Healing"]),
            ("g3", "Grove", None, None),
            ("r1", "River", None, ["Contact", "Frequency", "Prediction"]),
            ("r2", "River", None, []),
            ("r3", "River", None, ["Contact", "Prediction"]),
            ("u1", "Willow", None, None)]:
        frame.append(member(video, family, channel))
        if present is not None:
            text = "Invented example " + " ".join(present)
            assessed = [t for t in topics if t != "Healing" or channel != "River"]
            segments = ([{"source_segment_id": "cue:1", "char_start": 0, "char_end": len(text),
                          "time_start": 0, "time_end": 1}] if channel == "Aurora" else None)
            assessments.append(observation(video, text, [(k, k) for k in present], assessed=assessed,
                                           creator=channel, segments=segments))
    return comparison.compare(frame, assessments, topics)


class EpisodeFigureTests(unittest.TestCase):
    def test_distinct_cross_creator_family_support_and_display_cap(self):
        result = invented_comparison()
        rows = figures.network_rows(result, min_families=2, min_creators=2, max_edges=1)
        by_pair = {(r["topic_a"], r["topic_b"]): r for r in rows}
        pair = by_pair["Contact", "Prediction"]
        self.assertEqual(pair["supporting_episodes"], 4)
        self.assertEqual(pair["distinct_supporting_families"], 3)
        self.assertEqual(pair["unresolved_supporting_singletons"], 2)
        self.assertEqual(pair["supporting_creators"], 3)
        self.assertEqual(pair["jointly_assessed_creators"], 3)
        self.assertEqual(pair["display_status"], "drawn")
        self.assertEqual(len([r for r in rows if r["display_status"] == "qualifies_beyond_display_limit"]), 2)
        self.assertEqual(by_pair["Contact", "Healing"]["display_status"], "below_display_threshold")
        with self.assertRaises(ValueError):
            figures.network_rows(result, min_creators=0)

    def test_unknown_pairs_remain_distinct_from_observed_zero(self):
        out = comparison.compare([member("a")], [], ["one", "two"])
        r, = figures.network_rows(out)
        self.assertEqual(r["display_status"], "unassessed")
        self.assertIsNone(r["creator_balanced_observed_share"])
        obs = observation("a", "example", [], assessed=["one", "two"])
        r, = figures.network_rows(comparison.compare([member("a")], [obs], ["one", "two"]))
        self.assertEqual(r["display_status"], "below_display_threshold")
        self.assertEqual(r["creator_balanced_observed_share"], 0)

    @unittest.skipUnless(find_spec("matplotlib"), "Chart exports require the existing research plotting environment")
    def test_rendered_figures_and_csvs_resolve_to_same_totals(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "comparison.json"
            raw.write_text(json.dumps(invented_comparison()), encoding="utf-8")
            out = root / "plots"
            figures.main([str(raw), str(out), "--label", "Invented fixture"])
            manifest = json.loads((out / "figure-manifest.json").read_bytes())
            for filename, proof in manifest["files"].items():
                self.assertEqual(sha256((out / filename).read_bytes()).hexdigest(), proof["sha256"])
            for stem in ("co-mention-network", "topic-heatmap-r01-c01"):
                svg = ElementTree.parse(out / (stem + ".svg")).getroot()
                visible = " ".join(svg.itertext())
                self.assertIn("Invented fixture", visible)
                self.assertTrue((out / (stem + ".png")).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
            with (out / "creator-topic.csv").open(encoding="utf-8-sig", newline="") as f:
                cells = {(r["channel_dir"], r["topic"]): r for r in csv.DictReader(f)}
            self.assertEqual(len(cells), 16)
            self.assertEqual(cells["Willow", "Contact"]["family_balanced_observed_share"], "")
            self.assertEqual(cells["Aurora", "Healing"]["family_balanced_observed_share"], "0.0")
            self.assertEqual(cells["Grove", "Healing"]["untimed"], "2")
            with (out / "co-mention-network.csv").open(encoding="utf-8-sig", newline="") as f:
                edges = list(csv.DictReader(f))
            self.assertEqual(sum(r["display_status"] == "drawn" for r in edges), 3)
            with (out / "creator-topic-pairs.csv").open(encoding="utf-8-sig", newline="") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 24)

    @unittest.skipUnless(find_spec("matplotlib"), "Chart exports require the existing research plotting environment")
    def test_empty_frame_exports_explanatory_figures(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            figures.export(comparison.compare([], [], ["one"]), root)
            self.assertIn("No eligible recordings", (root / "topic-heatmap-r01-c01.svg").read_text(encoding="utf-8"))
            self.assertIn("No pair meets", (root / "co-mention-network.svg").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
