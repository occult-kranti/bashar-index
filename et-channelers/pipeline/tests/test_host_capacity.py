import os
import unittest

from pipeline import host_capacity as capacity


class HostCapacityTests(unittest.TestCase):
    def sample(self, available, commit_spare=12):
        gib = capacity.GIB
        return capacity.MemorySnapshot(32 * gib, int(available * gib), 64 * gib, int((64 - commit_spare) * gib))

    def test_active_launches_and_buffers_consume_headroom(self):
        slots = capacity.additional_bootstraps
        self.assertEqual(slots(self.sample(8)), 2)
        self.assertEqual(slots(self.sample(8), active_bootstraps=1), 1)
        self.assertEqual(slots(self.sample(8), maximum_bootstraps=1), 1)
        self.assertEqual(slots(self.sample(3.5)), 2)
        self.assertEqual(slots(self.sample(3.5), active_media=4, upload_transfers=3), 1)

    def test_commit_and_physical_pressure_are_independent_and_recover_on_new_sample(self):
        self.assertEqual(capacity.additional_bootstraps(self.sample(1.9)), 0)
        self.assertEqual(capacity.additional_bootstraps(self.sample(9, commit_spare=3.5)), 0)
        self.assertEqual(capacity.additional_bootstraps(self.sample(3.3, commit_spare=4.5)), 1)

    def test_physical_disk_floor_is_decimal_and_accounts_for_future_growth(self):
        self.assertEqual(capacity.disk_headroom(21_000_000_000, 6_000_000_000, 3_000_000_000), 0)
        self.assertLess(capacity.disk_headroom(12_000_000_000, 1), 0)
        with self.assertRaises(ValueError):
            capacity.additional_bootstraps(self.sample(8), active_bootstraps=-1)

    @unittest.skipUnless(os.name == "nt", "Windows host counters")
    def test_real_host_returns_page_counts_converted_to_bytes(self):
        sample = capacity.windows_memory()
        self.assertGreater(sample.physical_total, capacity.GIB)
        self.assertGreater(sample.commit_limit, capacity.GIB)
        self.assertEqual(sample.physical_total % 4096, 0)
        self.assertEqual(sample.commit_used % 4096, 0)
