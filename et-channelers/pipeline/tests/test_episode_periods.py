import unittest

from pipeline import episode_comparison, episode_periods
from pipeline.tests.test_episode_comparison import member, observation, pin


def dated(video, creator, day, *, exact=True, family=None):
    return {**member(video, family=family, creator=creator), "selected_publication_date": day,
            "selected_date_quality": "exact" if exact else "approximate", "selected_date_source_sha256": pin(video)}


class PublicationQuarterTests(unittest.TestCase):
    def test_equal_creator_and_family_weights_and_comparable_changes(self):
        frame = [dated("a", "A", "2025-12-31"), dated("b", "A", "2026-01-01", family="same"),
                 dated("c", "A", "2026-01-02", family="same"), dated("d", "A", "2026-03-31"),
                 dated("e", "B", "2026-01-15"), dated("f", "C", "2026-01-20"),
                 dated("g", "A", "2026-08-01"), dated("h", "A", "2026-02-15", exact=False)]
        observations = [observation(i, "topic", [("X", "topic")] if i in "bc" else [], assessed=["X"], creator=c)
                        for i, c in (("a", "A"), ("b", "A"), ("c", "A"), ("d", "A"), ("e", "B"), ("g", "A"))]
        evidence = episode_comparison.compare(frame, observations, ["X"])["evidence"]
        result = episode_periods.summarize(iter(frame), evidence, ["X"])
        self.assertEqual(result["quarters"], ["2025-Q4", "2026-Q1", "2026-Q3"])
        self.assertEqual(result["undated_episodes"], 1)
        by_period = {r["publication_quarter"]: r for r in result["series"]}
        first = by_period["2026-Q1"]
        self.assertEqual((first["eligible_episodes"], first["assessed_episodes"], first["positive_episodes"]), (5, 4, 2))
        self.assertEqual((first["eligible_creators"], first["assessed_creators"]), (3, 2))
        self.assertEqual(first["episode_share"], .5)
        self.assertEqual(first["creator_balanced_share"], .25)
        self.assertAlmostEqual(first["creator_balanced_frame_lower"], 1 / 6)
        self.assertAlmostEqual(first["creator_balanced_frame_upper"], .5)
        self.assertIsNone(by_period["undated"]["creator_balanced_share"])
        (change,) = result["matched_quarter_changes"]
        self.assertEqual(change["matched_channel_dirs"], ["A"])
        self.assertEqual(change["mean_within_creator_change_percentage_points"], 50.0)

    def test_date_needs_a_valid_day_and_its_source_evidence(self):
        for day, source in (("2026-02-30", pin("proof")), ("20260101", pin("proof")), ("2026-01-01", None)):
            row = dated("a", "A", day)
            row["selected_date_source_sha256"] = source
            self.assertIsNone(episode_periods.publication_quarter(row))

    def test_disjoint_creators_have_no_within_creator_estimate(self):
        rows = [dated("a", "A", "2026-03-30"), dated("b", "B", "2026-04-01")]
        obs = [observation(k, "x", [], assessed=["X"], creator=c) for k, c in (("a", "A"), ("b", "B"))]
        proof = episode_comparison.compare(rows, obs, ["X"])["evidence"]
        change, = episode_periods.summarize(rows, proof, ["X"])["matched_quarter_changes"]
        self.assertEqual(change["matched_creators"], 0)
        self.assertIsNone(change["mean_within_creator_change_percentage_points"])
        with self.assertRaisesRegex(ValueError, "one selected episode"):
            episode_periods.summarize(rows, proof + proof[:1], ["X"])
