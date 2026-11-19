from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from pipeline import episode_periods, episode_upload_calendar


def pin(text):
    return sha256(text.encode()).hexdigest()


class UploadCalendarTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "catalog.zip"
        self.frame, self.listings, self.observations, self.snapshots = [], [], [], []
        days = (("2026-04-01", ["2026-03-31"]), ("2026-01-02", []),
                (None, ["2025-06-02"]), ("2026-03-31", ["2026-03-30", "2026-03-31"]))
        for num, (published, upload_days) in enumerate(days):
            video = "v" + str(num)
            self.frame.append({"video_id": video, "channel_dir": "a", "expected_channel_id": "UC-a",
                               "tab": "videos", "selected_publication_date": published,
                               "selected_date_quality": "exact", "selected_date_source_sha256": pin(video)})
            evidence = {}
            for day in upload_days:
                source, projection = pin(video + day), pin(video + day + "-project")
                self.observations.append({"video_id": video, "input_sha256": source, "projection_sha256": projection})
                self.snapshots.append({"projection_sha256": projection, "metadata": {"upload_date": day}})
                evidence[day] = [source]
            self.listings.append({"video_id": video, "channel_id": "UC-a", "channel_dir": "a", "media_type": "videos",
                                  "observed_upload_day_evidence": evidence,
                                  "single_observed_upload_day": upload_days[0] if len(upload_days) == 1 else None})
        self.selection = pin("selection")
        self.summary = {"scope": "closed_full_cohort", "selection_sha256": self.selection, "recordings": 4, "creators": 1}

    def save(self):
        with ZipFile(self.path, "w") as archive:
            archive.writestr("summary.json", json.dumps(self.summary))
            for name, records in (("listings", self.listings), ("source-observations", self.observations),
                                  ("public-metadata-snapshots", self.snapshots)):
                archive.writestr("catalog/" + name + ".jsonl", "".join(json.dumps(x) + "\n" for x in records))
        return sha256(self.path.read_bytes()).hexdigest()

    def load(self):
        return episode_upload_calendar.read_catalog(self.path, self.save(), self.frame, self.selection)

    def test_dates_and_disagreement_keep_distinct_calendars(self):
        days, counts = self.load()
        self.assertEqual(days, {"v0": "2026-03-31", "v1": None, "v2": "2025-06-02", "v3": None})
        self.assertEqual(counts, {"different_upload_and_publication_quarters": 1, "missing_upload_day": 1,
                                  "upload_day_only": 1, "conflicting_observed_upload_days": 1})
        publication = episode_periods.summarize(self.frame, [], ["topic"])
        upload = episode_periods.summarize(self.frame, [], ["topic"], upload_days=days)
        self.assertEqual(publication["quarters"], ["2026-Q1", "2026-Q2"])
        self.assertEqual(upload["quarters"], ["2025-Q2", "2026-Q1"])
        self.assertEqual(upload["episodes_with_exact_upload_dates"], 2)
        self.assertEqual(upload["series"][-1]["upload_quarter"], "undated")
        self.assertEqual(upload["series"][-1]["eligible_episodes"], 2)
        self.assertNotIn("publication_quarter", upload["series"][0])

    def test_sample_wrong_hash_wrong_owner_and_incomplete_catalog_do_not_enter_analysis(self):
        self.summary["scope"] = "private_sample"
        with self.assertRaisesRegex(ValueError, "final catalog"):
            self.load()
        with self.assertRaisesRegex(ValueError, "receipt"):
            episode_upload_calendar.read_catalog(self.path, pin("wrong"), self.frame, self.selection)
        self.summary["scope"] = "closed_full_cohort"
        self.listings[0]["channel_id"] = "UC-other"
        with self.assertRaisesRegex(ValueError, "selected channel"):
            self.load()
        self.listings.pop(0)
        with self.assertRaisesRegex(ValueError, "omits selected"):
            self.load()

    def test_day_requires_matching_source_observation_on_the_same_recording(self):
        self.snapshots[0]["metadata"]["upload_date"] = "2026-04-01"
        with self.assertRaisesRegex(ValueError, "underlying metadata"):
            self.load()
        self.snapshots[0]["metadata"]["upload_date"] = "2026-03-31"
        self.observations[0]["video_id"] = "v1"
        with self.assertRaisesRegex(ValueError, "underlying metadata"):
            self.load()

    def test_portable_multi_selection_export_keeps_older_members_outside_the_denominator(self):
        self.summary = {"current_selection_sha256": self.selection, "state": "verified_current_cohort",
                        "current_recordings": 4, "selections": [{"selection_sha256": pin("older")},
                            {"selection_sha256": self.selection, "listing_complete": True, "creators": 1}]}
        for listing in self.listings:
            listing["in_current_selection"] = True
        self.listings.append({"video_id": "only-earlier", "in_current_selection": False})
        self.observations.append(dict(self.observations[0], video_id="only-earlier"))
        days, _ = self.load()
        self.assertEqual(set(days), {x["video_id"] for x in self.frame})
        self.summary["state"] = "private_metadata_preview"
        with self.assertRaisesRegex(ValueError, "final catalog"):
            self.load()
