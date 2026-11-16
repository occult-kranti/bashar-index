"""Offline catalog integrity, incremental publication and identity tests."""
import csv
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import archive_catalog as catalog


def queued(video_id="ABCDEFGHIJK", **extra):
    return dict(video_id=video_id, channel_dir="test-channel", title="Invented item", tab="videos",
                listing_rank="0", duration_s="120", queue_provenance="newest20+saved_full", **extra)


def receipt(row, remote="etdrive:04 Audio", legacy=False, owner=None):
    owner = owner or row["channel_dir"]
    parent = f"{remote}/{owner}/" + ("YouTube native" if legacy else catalog.SOURCE_FOLDERS[row["tab"]])
    audio = dict(video_id=row["video_id"], channel_dir=owner, status="deleted",
                 path=f"audio/{owner}/{row['video_id']}.webm", remote=f"{parent}/{row['video_id']}.webm",
                 drive_id="audio-object", bytes=12, md5="a" * 32, sha256="b" * 64,
                 metadata=dict(remote=f"{parent}/{row['video_id']}.info.json", drive_id="metadata-object",
                               bytes=45, md5="c" * 32, sha256="d" * 64))
    return audio


class FakeDrive:
    def __init__(self):
        self.uploads, self.objects = [], {}
        self.fail = False

    def copy(self, path, remote):
        self.uploads.append(remote)
        self.objects[remote] = path.read_bytes()

    def stat(self, remote):
        evidence = catalog.digest(self.objects[remote])
        return {"ID": "invented-object", "Size": evidence["bytes"],
                "Hashes": {"md5": "wrong" if self.fail else evidence["md5"]}}


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.queue = self.root / "jobs/full.csv"
        self.journal = self.root / "sync/drive_ingest_manifest.jsonl"

    def queue_rows(self, rows):
        self.queue.parent.mkdir(parents=True, exist_ok=True)
        self.queue.write_bytes(catalog.csv_bytes(rows, catalog.QUEUE_FIELDS))

    def state(self, rows):
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        self.journal.write_bytes(b"".join(catalog.encoded_json(row) for row in rows))

    def prepare(self):
        return catalog.prepare_catalog(self.root, self.queue, "etdrive:04 Audio", min_free_bytes=0)

    def test_baseline_then_delta_rebuild_is_idempotent_and_deduplicates_by_id(self):
        first, second = queued(), queued("LMNOPQRSTUV")
        self.queue_rows([first, second])
        initial = self.prepare()
        self.assertEqual(initial["counts"]["items"], 2)
        self.assertEqual(len(initial["files"]), 3)
        unchanged = self.prepare()
        self.assertFalse(unchanged["new_snapshot"])
        self.assertEqual(unchanged["manifest_path"], initial["manifest_path"])
        self.state([receipt(first)])
        update = self.prepare()
        manifest = catalog.load_manifest(Path(update["manifest_path"]))
        self.assertEqual(update["changed_items"], 1)
        self.assertEqual(len(manifest["deltas"]), 1)
        rebuilt = catalog.rebuild(update["manifest_path"])
        self.assertEqual(len(rebuilt), 2)
        self.assertEqual(rebuilt[0]["archive_state"], "verified_pair")
        self.assertEqual(rebuilt[1]["archive_state"], "queued")
        self.assertEqual(rebuilt[0]["queue_provenance"], "newest20+saved_full")

    def test_preserves_actual_legacy_storage_owner_without_fabricating_attribution(self):
        row = queued(entity="", primary_person_name="", primary_person_basis="")
        self.queue_rows([row])
        original = receipt(row, legacy=True, owner="original-host")
        self.state([original])
        result = catalog.rebuild(self.prepare()["manifest_path"])[0]
        self.assertEqual(result["audio_remote"], original["remote"])
        self.assertEqual(result["metadata_remote"], original["metadata"]["remote"])
        self.assertEqual(result["archive_channel_dir"], "original-host")
        self.assertEqual(result["channel_dir"], "test-channel")
        self.assertEqual(result["source_folder"], "Videos")
        self.assertEqual(result["primary_person_basis"], "unknown")
        self.assertEqual(result["entity"], "")
        self.assertEqual(result["entity_label_basis"], "unknown")

    def test_all_source_tabs_and_long_or_unknown_durations_stay_in_catalog(self):
        rows = [dict(queued(video_id), tab=tab, duration_s=duration) for video_id, tab, duration in (
            ("ABCDEFGHIJK", "videos", "100000"), ("LMNOPQRSTUV", "shorts", "1"),
            ("WXYZabcdefg", "streams", ""), ("hijklmnopqr", "", ""))]
        self.queue_rows(rows)
        plan = self.prepare()
        rebuilt = catalog.rebuild(plan["manifest_path"])
        self.assertEqual({r["source_folder"] for r in rebuilt}, {"Videos", "Shorts", "Recorded streams", "Unclassified"})
        self.assertEqual(plan["counts"]["items"], 4)
        manifest = catalog.load_manifest(Path(plan["manifest_path"]))
        self.assertIsNone(manifest["duration_filter"])

    def test_upload_verifies_objects_before_manifest_and_reuses_durable_receipts(self):
        row = queued()
        self.queue_rows([row])
        drive = FakeDrive()
        initial = self.prepare()
        result = catalog.upload_catalog(initial, drive)
        self.assertEqual(result["uploaded_objects"], 3)
        self.assertEqual(drive.uploads[-1], initial["manifest_remote"])
        self.assertEqual(catalog.upload_catalog(initial, drive)["uploaded_objects"], 0)
        self.state([receipt(row)])
        update = self.prepare()
        self.assertEqual(catalog.upload_catalog(update, drive)["uploaded_objects"], 3)
        self.assertEqual(drive.uploads.count(initial["files"][0]["remote"]), 1)
        self.assertEqual(drive.uploads[-1], update["manifest_remote"])

    def test_hash_failure_never_publishes_manifest_or_deletes_local_objects(self):
        self.queue_rows([queued()])
        plan, drive = self.prepare(), FakeDrive()
        drive.fail = True
        with self.assertRaises(catalog.IngestError):
            catalog.upload_catalog(plan, drive)
        self.assertNotIn(plan["manifest_remote"], drive.uploads)
        self.assertTrue(all(Path(item["path"]).exists() for item in plan["files"]))
        drive.fail = False
        self.assertEqual(catalog.upload_catalog(plan, drive)["uploaded_objects"], 3)

    def test_rebuild_rejects_corrupted_object(self):
        self.queue_rows([queued()])
        plan = self.prepare()
        path = Path(plan["files"][0]["path"])
        path.write_bytes(path.read_bytes() + b"corrupt")
        with self.assertRaisesRegex(ValueError, "integrity"):
            catalog.rebuild(plan["manifest_path"])

    def test_changed_queue_creates_new_baseline_without_removed_ghost_rows(self):
        self.queue_rows([queued(), queued("LMNOPQRSTUV")])
        original = self.prepare()
        self.queue_rows([queued()])
        changed = self.prepare()
        manifest = catalog.load_manifest(Path(changed["manifest_path"]))
        self.assertEqual(manifest["deltas"], [])
        self.assertEqual(len(catalog.rebuild(changed["manifest_path"])), 1)
        self.assertTrue(Path(original["manifest_path"]).exists())

    def test_wrong_archive_or_duplicate_id_is_rejected(self):
        row = queued()
        self.queue_rows([row, row])
        with self.assertRaisesRegex(ValueError, "unique"):
            self.prepare()
        self.queue_rows([row])
        self.state([receipt(row, remote="other:folder")])
        with self.assertRaisesRegex(ValueError, "outside"):
            self.prepare()

    def test_malformed_receipt_evidence_is_reported_and_never_counted_as_proof(self):
        self.queue_rows([queued()])
        self.state([receipt(queued())])
        self.journal.write_bytes(self.journal.read_bytes() + b'{"video_id":')
        records, _, warnings = catalog.read_receipts(self.journal)
        self.assertEqual(len(records), 1)
        self.assertEqual(warnings, {"malformed_lines": 0, "unfinished_tail": 1})
        first = self.prepare()
        self.journal.write_bytes(self.journal.read_bytes() + b"\n")
        result = self.prepare()
        self.assertEqual(result["receipt_parse_warnings"], {"malformed_lines": 1, "unfinished_tail": 0})
        self.assertEqual(result["counts"]["verified_pairs"], 1)
        self.assertEqual(result["changed_items"], 0)
        self.assertNotEqual(result["manifest_path"], first["manifest_path"])
        self.assertEqual(catalog.load_manifest(Path(result["manifest_path"]))["deltas"], [])

    def test_catalog_respects_storage_ceiling(self):
        self.queue_rows([queued()])
        with self.assertRaises(catalog.IngestError):
            catalog.prepare_catalog(self.root, self.queue, "etdrive:04 Audio", max_local_bytes=1, min_free_bytes=0)
        self.assertFalse((self.root / catalog.CATALOG_DIR / "current.json").exists())

    def test_persistent_stop_marker_prevents_catalog_network_requests(self):
        self.queue_rows([queued()])
        plan, drive = self.prepare(), FakeDrive()
        (self.root / "sync/STOP_DRIVE_INGEST").touch()
        with self.assertRaises(catalog.IngestError) as caught:
            catalog.upload_catalog(plan, drive)
        self.assertEqual(caught.exception.kind, "stopped")
        self.assertEqual(drive.uploads, [])


if __name__ == "__main__":
    unittest.main()
