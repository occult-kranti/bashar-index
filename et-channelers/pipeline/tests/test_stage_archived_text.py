from hashlib import md5, sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from pipeline import stage_archived_text as staging


class Archive:
    RETRY_FLAGS = []

    def __init__(self, body):
        self.body = body
        self.lookups = []
        self.copies = []
        self.object_id = "zip-id"

    def stat_batch(self, remote, names, manifest):
        paths = manifest.read_text(encoding="utf-8").splitlines()
        assert names == paths
        self.lookups.append(paths)
        return {name: {"Size": len(self.body), "Hashes": {"MD5": md5(self.body).hexdigest()},
                       "ID": self.object_id} for name in paths}

    def execute(self, args, timeout, operation):
        self.copies.append(args)
        base = Path(args[2])
        for name in Path(args[args.index("--files-from-raw") + 1]).read_text(encoding="utf-8").splitlines():
            dest = base / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(self.body)


class ArchiveStagingTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.selection = self.root / "selection.json"
        self.selection.write_text("{}")
        self.pin = sha256(b"{}").hexdigest()
        self.frame = [dict(video_id=v, channel_dir="person", tab="videos") for v in ("abcde123456", "vwxyz123456")]
        self.coverage = {"selection_sha256": self.pin,
                         "summary": {"latest20_target": 2, "audio_available": 2, "channels": 1, "remaining_audio": 0}}
        self.body = b"archived fixture"
        self.drive = Archive(self.body)
        self.inputs = [dict(kind="youtube_caption", row=row, record={"video_id": row["video_id"]}, track_id="en",
                            proof={"remote": "test:archive/" + row["video_id"] + "/caption.zip",
                                   "drive_id": "zip-id", "bytes": len(self.body),
                                   "sha256": sha256(self.body).hexdigest(), "md5": md5(self.body).hexdigest()})
                       for row in self.frame]
        self.patch(staging.collection_coverage, "mixed_selection", return_value=(
            self.frame, {"person": "short_complete_displayed_list"}, self.pin))
        self.patch(staging.collection_coverage, "coverage", return_value=(self.coverage, self.frame))
        self.patch(staging, "input_rows", return_value=self.inputs)
        self.patch(staging, "headroom", return_value=10_000_000)

    def patch(self, obj, name, **kwargs):
        context = patch.object(obj, name, **kwargs)
        self.addCleanup(context.stop)
        return context.start()

    def execute(self, **kwargs):
        return staging.stage(self.root, self.selection, self.pin, self.drive, remote="test:archive", **kwargs)

    def test_two_files_use_one_read_batch_and_views_survive_owned_zip_cleanup(self):
        def fixture(root, job, path, remote):
            self.assertEqual(path.read_bytes(), self.body)
            return {f"caption_views/{job['row']['video_id']}/version.json": {"text": "sample"}}
        views = self.patch(staging, "text_views", side_effect=fixture)
        self.assertEqual(self.execute()["views_staged"], 2)
        self.assertEqual(len(self.drive.lookups), 1)
        self.assertEqual(len(self.drive.copies), 1)
        self.assertFalse(list((self.root / "analysis/text_bundle_cache").rglob("*.zip")))
        self.assertEqual(self.execute()["views_staged"], 2)
        self.assertEqual(len(self.drive.lookups), 1)
        self.assertEqual(views.call_count, 2)
        output = next((self.root / "analysis/caption_views").rglob("version.json"))
        output.write_text("corrupt")
        with self.assertRaisesRegex(ValueError, "previously staged text view changed"):
            self.execute()

    def test_changed_remote_identity_prevents_transfer(self):
        self.drive.object_id = "wrong-object"
        with self.assertRaisesRegex(ValueError, "different Drive object"):
            self.execute()
        self.assertFalse(self.drive.copies)

    def test_plan_reads_no_drive_and_incomplete_frame_cannot_read_bundles(self):
        self.coverage["summary"].update(remaining_audio=1, audio_available=1)
        self.assertEqual(self.execute(inventory_only=True)["recordings_with_inputs"], 2)
        with self.assertRaisesRegex(ValueError, "verified audio"):
            self.execute()
        self.assertFalse((self.root / "analysis").exists())
        self.assertFalse(self.drive.lookups)

    def test_owner_authorized_outstanding_recording_lets_the_archived_ones_stage_and_nothing_looser(self):
        absent = self.frame[1]["video_id"]
        self.coverage["summary"].update(remaining_audio=1, audio_available=1)
        self.patch(staging.collection_coverage, "coverage", return_value=(self.coverage, self.frame[:1]))
        self.patch(staging, "input_rows", return_value=self.inputs[:1])
        self.patch(staging, "text_views", side_effect=lambda root, job, path, remote:
                   {f"caption_views/{job['row']['video_id']}/version.json": {"text": "sample"}})
        for unlisted in (None, frozenset({"another0001"}), frozenset({absent, "another0001"})):
            with self.subTest(outstanding=unlisted), self.assertRaises(ValueError):
                self.execute(outstanding=unlisted)
        self.assertFalse(self.drive.lookups)
        self.assertEqual(self.execute(outstanding=frozenset({absent}))["views_staged"], 1)
        self.assertEqual(len(self.drive.copies), 1)
