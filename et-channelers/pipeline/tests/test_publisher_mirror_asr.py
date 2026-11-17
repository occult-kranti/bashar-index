"""Offline mirror/RSS admission tests: no media, inference or network."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipeline import publisher_mirror_asr as m, publisher_variant_asr as worker


class MirrorAsrTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.video = "abcdefghijk"
        self.audio = m.hashes(b"invented publisher audio")
        self.parent = f"fixture:Audio/fixture-person/Videos/{self.video}/PublisherVariants/{self.audio['sha256']}"
        self.audio.update(remote=self.parent + "/audio.mp3", drive_id="audio-object")
        self.item = {"private_root": str(self.root), **{key: str(self.root / value) for key, value in {
            "archive_receipt_path": "receipt.json", "provenance_reference_path": "reference.json",
            "accepted_metadata_path": "accepted.json", "mapping_path": "mapping.json", "feed_path": "feed.xml",
            "audio_path": "inputs/audio.mp3", "provenance_path": "inputs/provenance.json"}.items()}}
        self.mapped = {"youtube_video_id": self.video, "channel_dir": "fixture-person", "status": "ready",
                       "association_method": "official_publisher_distinctive_full_title_date_duration",
                       "episode_guid": "episode-1", "source_audio_enclosure": {"url": "https://publisher.example/audio.mp3",
                       "length": "24", "type": "audio/mpeg"}}
        self.accepted = {"artifact_kind": "accepted_official_publisher_rss_episode", "episode": {
            "guid": "episode-1", "audio": copy.deepcopy(self.mapped["source_audio_enclosure"])},
            "feed": {"language": "en-us", "language_scope": "publisher_rss_channel", "channel": {"language": "en-us"}}}
        self.archive = {"status": "verified", "kind": "qualified_publisher_mirror_audio_variant", "item_id": "item-1",
                        "variant_id": self.audio["sha256"], "audio": self.audio, "provider": "OfficialRSS",
                        "channel_dir": "fixture-person", "associated_youtube_id": self.video, "watch_page_id": "episode-1",
                        "association_method": "publisher_owner_title_date_duration", "association_qualification": "Publisher edition, edit equality unknown.",
                        "exact_youtube_crossreference": False, "human_verified": False, "recording_equivalence_verified": False,
                        "actual_probe_duration_s": 61.3, "provider_declared_duration_s": 61, "caption_state": "complete", "caption_bundles": []}
        self.archive.update({key: False for key in ("native_youtube_bytes", "changes_native_audio_count", "changes_native_asr_count", "changes_native_caption_count")})
        self.feed_language = "en-us"
        self.metadata_override = {}
        self.write_fixture()

    def put(self, key, data):
        raw = worker.encoded(data)
        Path(self.item[key]).write_bytes(raw)
        return m.hashes(raw)

    def write_fixture(self):
        language = f"<language>{self.feed_language}</language>" if self.feed_language is not None else ""
        raw = (f'<rss><channel>{language}<item><guid>episode-1</guid>'
               '<enclosure url="https://publisher.example/audio.mp3" length="24" type="audio/mpeg"/></item></channel></rss>').encode()
        Path(self.item["feed_path"]).write_bytes(raw)
        self.accepted["feed"].update({key: value for key, value in m.hashes(raw).items() if key != "md5"})
        self.accepted["feed"].update(language=self.feed_language, channel={"language": self.feed_language})
        self.accepted["association_evidence"] = copy.deepcopy(self.mapped)
        self.accepted["mapping_sha256"] = self.put("mapping_path", {"items": [self.mapped]})["sha256"]
        self.archive["accepted_api_sha256"] = self.put("accepted_metadata_path", self.accepted)["sha256"]
        metadata = {"artifact_kind": self.archive["kind"], "item_id": "item-1", "accepted_api_sha256": self.archive["accepted_api_sha256"],
                    "audio": {key: self.audio[key] for key in ("bytes", "md5", "sha256")}, "probe": {"duration_seconds": 61.3},
                    "association": {key: self.archive[key] for key in m.ASSOCIATION_KEYS}, "publisher_metadata": copy.deepcopy(self.accepted),
                    "recording_equivalence_verified": False}
        if "original_youtube_link" in self.archive:
            metadata["association"]["original_youtube_link"] = self.archive["original_youtube_link"]
        metadata.update({key: False for key in ("native_youtube_bytes", "changes_native_audio_count", "changes_native_asr_count", "changes_native_caption_count")})
        metadata.update(self.metadata_override)
        self.archive["provenance"] = {**self.put("provenance_reference_path", metadata), "remote": self.parent + "/provenance.json", "drive_id": "provenance-object"}
        self.put("archive_receipt_path", self.archive)

    def prepare(self):
        return worker.prepare_job(self.item)

    def test_dispatch_reuses_unchanged_worker_profile_and_retains_exact_source_bytes(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")):
            result = self.prepare()
        self.assertEqual(result["status"], "eligible")
        self.assertEqual(result["source_kind"], "publisher_audio_variant")
        self.assertEqual(result["audio"], self.audio)
        self.assertEqual(result["provenance_data"], worker.read(self.item["provenance_reference_path"]))
        self.assertEqual(result["language"]["scope"], "publisher_rss_channel_declaration")
        self.assertFalse(result["language"]["episode_language_independently_verified"])
        self.assertFalse(result["language"]["native_youtube_language_asserted"])
        self.assertEqual(result["association"]["source_adapter"]["profile"], m.PROFILE)
        self.assertEqual((worker.POLICY["max_sources"], worker.POLICY["max_input_bytes"]), (2, 256000000))
        self.assertFalse(Path(result["audio_path"]).exists())

    def test_exact_link_is_preserved_without_claiming_same_recording(self):
        self.archive.update(kind="publisher_mirror_audio_variant", association_method="publisher_rss_exact_youtube_id",
                            exact_youtube_crossreference=True, original_youtube_link="https://www.youtube.com/watch?v=" + self.video)
        self.mapped["exact_youtube_reference"] = self.archive["original_youtube_link"]
        self.mapped["association_method"] = "official_feed_item_exact_youtube_link"
        self.write_fixture()
        result = self.prepare()
        self.assertTrue(result["association"]["exact_youtube_crossreference"])
        self.assertFalse(result["association"]["recording_equivalence_verified"])
        self.archive["original_youtube_link"] = "https://www.youtube.com/watch?v=other123456"
        self.write_fixture()
        with self.assertRaisesRegex(worker.VariantError, "exact_source_link"):
            self.prepare()

    def test_feed_language_is_not_inferred_from_queue_title(self):
        for language in ("de", None):
            with self.subTest(language=language):
                self.feed_language = language
                self.mapped["queue_title"] = "An English display title"
                self.write_fixture()
                result = self.prepare()
                self.assertEqual(result["status"], "pending_publisher_language_evidence")
                self.assertIsNone(result["language"])

    def test_explicit_nonlexical_review_is_not_forced_english(self):
        self.mapped["nonlexical"] = True
        self.write_fixture()
        self.assertEqual(self.prepare()["status"], "held_language_review")

    def test_forged_english_declaration_conflicting_with_hashed_feed_is_rejected(self):
        self.feed_language = "de"
        self.write_fixture()
        self.accepted["feed"].update(language="en", channel={"language": "en"})
        self.archive["accepted_api_sha256"] = self.put("accepted_metadata_path", self.accepted)["sha256"]
        metadata = worker.read(self.item["provenance_reference_path"])
        metadata.update(accepted_api_sha256=self.archive["accepted_api_sha256"], publisher_metadata=self.accepted)
        self.archive["provenance"].update(self.put("provenance_reference_path", metadata))
        self.put("archive_receipt_path", self.archive)
        with self.assertRaisesRegex(worker.VariantError, "feed_language_binding"):
            self.prepare()

    def caption(self):
        proof = m.hashes(b"invented caption ZIP")
        return {**proof, "remote": self.parent + "/Captions/" + proof["sha256"] + "/captions.zip", "drive_id": "caption-object",
                "language": "en-us", "usable_timed_text": True, "coverage": {"cue_union_seconds_clamped": 3, "every_word_coverage_verified": False}}

    def test_usable_partial_inventory_suppresses_duplicate_asr_not_claiming_coverage(self):
        self.archive.update(caption_state="pending", caption_bundles=[self.caption()])
        self.write_fixture()
        result = self.prepare()
        self.assertEqual(result["status"], "publisher_text_available_review_before_asr")
        availability = result["association"]["source_adapter"]["caption_availability"]
        self.assertEqual(availability["inventory_state"], "pending")
        self.assertFalse(availability["speech_coverage_verified"])

    def test_empty_caption_inventory_does_not_mean_text_exists(self):
        self.assertEqual(self.prepare()["status"], "eligible")
        track = self.caption()
        track["usable_timed_text"] = False
        self.archive["caption_bundles"] = [track]
        self.write_fixture()
        self.assertEqual(self.prepare()["status"], "eligible")

    def test_caption_proof_from_other_audio_or_duplicate_drive_id_fails_closed(self):
        for field, value in (("remote", "fixture:Other/captions.zip"), ("drive_id", "audio-object")):
            track = self.caption()
            track[field] = value
            self.archive["caption_bundles"] = [track]
            self.write_fixture()
            with self.assertRaisesRegex(worker.VariantError, "caption_proof"):
                self.prepare()

    def test_audio_pair_requires_distinct_drive_identity_and_exact_remote(self):
        for field, value in (("drive_id", "audio-object"), ("remote", "fixture:Other/provenance.json"), ("md5", "0" * 32)):
            self.write_fixture()
            archive = copy.deepcopy(self.archive)
            archive["provenance"][field] = value
            self.put("archive_receipt_path", archive)
            with self.subTest(field=field), self.assertRaises(worker.VariantError):
                self.prepare()

    def test_changed_evidence_or_native_promotion_is_rejected(self):
        for key in ("provenance_reference_path", "accepted_metadata_path", "mapping_path", "feed_path"):
            self.write_fixture()
            with Path(self.item[key]).open("ab") as stream:
                stream.write(b" ")
            with self.subTest(key=key), self.assertRaises(worker.VariantError):
                self.prepare()
        self.write_fixture()
        self.archive["changes_native_asr_count"] = True
        self.put("archive_receipt_path", self.archive)
        with self.assertRaisesRegex(worker.VariantError, "native_promotion"):
            self.prepare()

    def test_wrong_feed_episode_cannot_be_relabelled_into_accepted_item(self):
        self.mapped["episode_guid"] = "unrelated"
        self.write_fixture()
        with self.assertRaisesRegex(worker.VariantError, "feed_episode"):
            self.prepare()

    def test_input_paths_cannot_escape_private_root_or_use_junction(self):
        self.item["audio_path"] = str(self.root.parent / "outside.mp3")
        with self.assertRaisesRegex(worker.VariantError, "path_outside_private"):
            self.prepare()
        self.item["audio_path"] = str(self.root / "inputs/audio.mp3")
        with patch.object(Path, "is_junction", return_value=True, create=True), self.assertRaisesRegex(worker.VariantError, "private_root"):
            self.prepare()


if __name__ == "__main__":
    unittest.main()
