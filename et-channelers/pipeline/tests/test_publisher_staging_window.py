from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from pipeline import publisher_mirror as mirror


class PublisherAdmissionTests(unittest.TestCase):
    def test_retained_failures_and_parallel_pending_are_charged_to_one_lease(self):
        staged = [50]
        window = mirror.PublisherStagingWindow(250, lambda: staged[0])
        with window.admit_group(100):
            # These jobs haven't written anything yet. A second parent can't consume their future bytes.
            with self.assertRaisesRegex(mirror.MirrorError, "spool_storage_deferred"):
                with window.admit_group(101):
                    self.fail("unreserved source started")
            staged[0] = 145    # The first group retained an almost complete item after local QC failed.
        with self.assertRaisesRegex(mirror.MirrorError, "spool_storage_deferred"):
            with window.admit_group(106):
                self.fail("new source started on top of a retained file")
        with window.admit_group(105) as total:
            self.assertEqual(total, 250)
        staged[0] = 260
        with self.assertRaisesRegex(mirror.MirrorError, "spool_storage_deferred"):
            with window.admit_group(1):
                self.fail("full but failed spool was overlooked")

    def test_physical_buffer_rechecked_before_each_group_and_drain_can_release_pending(self):
        free = [100]
        window = mirror.PublisherStagingWindow(100, lambda: 10, physical_free=lambda: free[0], minimum_free_bytes=40)
        with self.assertRaisesRegex(mirror.MirrorError, "disk_buffer"):
            with window.admit_group(61):
                self.fail("physical buffer violated")
        with self.assertRaisesRegex(OSError, "fixture"):
            with window.admit_group(60):
                raise OSError("fixture")
        free[0] = 70
        with window.admit_group(30) as occupied:
            self.assertEqual(occupied, 40)

    def test_global_projection_charges_retained_bytes_once_and_only_future_bytes_to_disk_free(self):
        args = dict(inactive_managed_bytes=1000, staged_actual_bytes=548, remaining_requested_bytes=40,
                    other_reserved_bytes=600, other_unspent_bytes=100, journal_growth_bytes=3,
                    free_bytes=1200, managed_limit_bytes=2300, minimum_free_bytes=1000)
        self.assertEqual(mirror.publisher_capacity_projection(**args),
                         {"publisher_envelope_bytes":588, "projected_managed_bytes":2191,
                          "projected_physical_free_bytes":1057})
        for key, value, message in [("managed_limit_bytes", 2190, "managed_storage_deferred"),
                                    ("minimum_free_bytes", 1058, "disk_buffer"),
                                    ("other_unspent_bytes", 601, "invalid_publisher_capacity"),
                                    ("remaining_requested_bytes", -2, "invalid_publisher_staging_bytes")]:
            with self.subTest(field=key), self.assertRaisesRegex(mirror.MirrorError, message):
                mirror.publisher_capacity_projection(**{**args, key:value})


class PublisherUploadGroupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.manifest = self.root/"files.txt"
        self.objects = {f"creator/Videos/vid{i:08d}/edition.mp3":
                        {"bytes": 200 + i, "md5": f"{i:032x}", "sha256": f"{i:064x}"} for i in range(1, 7)}
        self.manifest.write_text("\n".join(self.objects) + "\n", encoding="utf-8")
        self.observed = {path:{"ID":"id" + str(i), "Size":p["bytes"], "Hashes":{"MD5":p["md5"]}}
                         for i, (path, p) in enumerate(self.objects.items())}
        self.drive = Mock()
        self.drive.stat_batch.return_value = self.observed

    def publish(self, **kwargs):
        return mirror.publish_verified_group(self.drive, self.root, "drive:Audio", self.manifest, self.objects, **kwargs)

    def test_six_immutable_source_objects_have_one_transfer_group_and_one_bulk_readback(self):
        result = self.publish(transfers=3)
        self.drive.copy_batch.assert_called_once_with(self.root, "drive:Audio", self.manifest, transfers=3)
        self.drive.stat_batch.assert_called_once_with("drive:Audio", set(self.objects), self.manifest)
        self.assertEqual({p["drive_id"] for p in result.values()}, {r["ID"] for r in self.observed.values()})
        for path, row in result.items():
            self.assertEqual(row["sha256"], self.objects[path]["sha256"])
            self.assertEqual(row["remote"], "drive:Audio/" + path)
            self.assertNotIn("drive_id", self.objects[path])

    def test_partial_and_duplicate_remote_ids_preserve_every_original_for_recovery_without_copy(self):
        names = list(self.objects)
        self.drive.stat_batch.return_value = {name:self.observed[name] for name in names[:-1]}
        with self.assertRaisesRegex(mirror.MirrorError, "missing_objects"):
            self.publish()
        self.drive.reset_mock()
        self.drive.stat_batch.return_value = self.observed
        self.observed[names[1]]["ID"] = self.observed[names[0]]["ID"]
        with self.assertRaisesRegex(mirror.MirrorError, "drive_id_duplicate"):
            self.publish(copy=False)
        self.drive.copy_batch.assert_not_called()
        self.observed[names[1]]["ID"] = "recovered-existing-id"
        self.assertEqual(self.publish(copy=False)[names[1]]["drive_id"], "recovered-existing-id")
        self.assertEqual(self.drive.copy_batch.call_count, 0)
        self.assertTrue(all("drive_id" not in value for value in self.objects.values()))

    def test_manifest_disagreement_and_invalid_transfer_count_never_contact_drive(self):
        self.manifest.write_text("../outside.mp3\n", encoding="utf-8")
        with self.assertRaisesRegex(mirror.MirrorError, "upload_manifest"):
            self.publish()
        with self.assertRaisesRegex(mirror.MirrorError, "upload_scope"):
            self.publish(transfers=8)
        self.drive.copy_batch.assert_not_called()
        self.drive.stat_batch.assert_not_called()
