import unittest
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from pipeline import regular_recording_dates as dates


class RecordingDateTests(unittest.TestCase):
    def setUp(self):
        self.selected = {"video_id": "abcdefghijk", "channel_dir": "creator", "source_channel_name": "Creator",
                         "expected_channel_id": "UCverified", "listing_rank": 0, "title": "Example"}
        self.grid = {"publication_display": "2 days ago", "observed_at": "2026-11-19T01:00:00Z",
                     "page_sha256": "a" * 64, "source_url": "https://www.youtube.com/@creator/videos"}

    def test_named_fields_have_distinct_meanings_and_utc_days(self):
        fields = {"publication": {"2026-11-16": {"b" * 64}}, "upload": {"2026-10-22": {"c" * 64}}}
        row = dates.build_row(self.selected, self.grid, fields)
        self.assertEqual((row["date_method"], row["exact_day"], row["upload_day"]), ("publication", "2026-11-16", "2026-10-22"))
        self.assertEqual(dates.calendar_day("2026-11-01T00:05:00+01:00"), "2026-10-31")
        self.assertEqual(dates.calendar_day("20261102"), "2026-11-02")

    def test_visible_age_remains_an_interval(self):
        row = dates.build_row(self.selected, self.grid, {})
        self.assertEqual((row["date_min"], row["date_max"], row["year_bin"], row["month_bin"]),
                         ("2026-11-15", "2026-11-18", "2026", "2026-11"))
        self.assertIsNone(row["exact_day"])
        self.assertEqual(dates.relative_interval("3 months ago", None), (None, None))
        self.assertEqual(dates.relative_interval("Live", self.grid["observed_at"]), (None, None))

    def test_crossing_calendar_boundaries_and_conflicting_proofs(self):
        grid = dict(self.grid, publication_display="1 year ago")
        estimate = dates.build_row(self.selected, grid, {})
        self.assertIsNone(estimate["month_bin"])
        self.assertIsNone(estimate["year_bin"])
        conflict = dates.build_row(self.selected, grid, {"availability":
            {"2024-08-13": {"a"*64}, "2024-11-24": {"b"*64}}})
        counts = dates.period_counts([estimate, conflict], "year")
        self.assertEqual([(r["year"], r["total"]) for r in counts], [("Ambiguous year", 1), ("Unresolved", 1)])
        self.assertIsNone(conflict["exact_day"])

    def test_sidecar_is_bound_to_video_and_owner(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp)/"batch"/"jobs"/"abcdefghijk"/"private-metadata.json"
            path.parent.mkdir(parents=True)
            meta = {"source": {"platform":"youtube", "video_id":"abcdefghijk"},
                    "metadata":{"id":"abcdefghijk", "channel_id":"UCwrong", "upload_date":"20261114"}}
            path.write_text(json.dumps(meta))
            frame = {"abcdefghijk": self.selected}
            evidence = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
            self.assertEqual(dates.supplement(evidence, frame, tmp), {})
            meta["metadata"]["channel_id"] = "UCverified"
            path.write_text(json.dumps(meta))
            self.assertEqual(dates.supplement(evidence, frame, tmp), {"matched_job_sidecars": 1})
            self.assertIn("2026-11-14", evidence["abcdefghijk"]["upload"])

    def test_daily_bounds_include_leap_day_and_zero_count_days(self):
        def observation(kind, lo, hi):
            return {"date_method": kind, "date_min": lo, "date_max": hi,
                    "exact_day": lo if kind in ("publication", "availability", "upload") else None}
        rows = [observation("publication", "2024-02-29", "2024-02-29"),
                observation("relative", "2024-02-29", "2024-02-29"),
                observation("relative", "2024-02-28", "2024-03-01"),
                observation("relative", "2024-02-28", "2024-02-29"),
                observation("availability", "2024-03-03", "2024-03-03"),
                observation("unknown", None, None)]
        daily = dates.daily_counts(rows)
        self.assertEqual([r["date"] for r in daily],
                         ["2024-02-28", "2024-02-29", "2024-03-01", "2024-03-02", "2024-03-03"])
        self.assertEqual([r["assigned_total"] for r in daily], [0, 2, 0, 0, 1])
        self.assertEqual([r["relative_possible_extra"] for r in daily], [2, 2, 1, 0, 0])
        self.assertEqual([r["possible_total"] for r in daily], [2, 4, 1, 0, 1])
        self.assertEqual((daily[1]["relative_single_day"], daily[1]["publication"]), (1, 1))
        self.assertEqual(dates.daily_counts([observation("unknown", None, None)]), [])

    def test_daily_metadata_cannot_span_two_days(self):
        with self.assertRaisesRegex(ValueError, "one UTC day"):
            dates.daily_counts([{"date_method":"upload", "date_min":"2026-11-19", "date_max":"2026-11-20",
                                 "exact_day":"2026-11-19"}])
