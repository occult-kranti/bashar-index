import unittest

from pipeline import regular_fifty_forecast as forecast


class ForecastTests(unittest.TestCase):
    def data(self):
        def card(i, status="public_listing"):
            return {"video_id": str(i), "listing_rank": i, "channel_dir": "a", "observed_primary_channel_id": "owner",
                    "access_status": status, "tab": "videos"}
        cards = [card(i) for i in range(22)] + [card(22, "members_only")]
        selection = {"latest_regular_per_creator": 20, "channels": [{"channel_dir": "a", "channel_id": "owner"}],
                     "rows": [dict(r, fresh_public_regular=True) for r in cards[:20]]}
        group = {"channel_id": "owner", "channel_dir": "a", "public_listing_complete": True, "exhausted": False,
                 "observed_items": cards}
        older = [card(i) for i in [15, 20, 21, 22, 23, 24, 25]]
        return selection, {"per_channel": 20, "channels": [group]}, older

    def test_overlap_credits_previous_twenty_and_exact_extra_receipts_once(self):
        selection, index, past = self.data()
        channels, rows = forecast.candidates(selection, index, past)
        owners, totals = forecast.workload(channels, {("a", "21"), ("a", "25"), ("another", "20")})
        self.assertEqual(totals, owners["a"])
        self.assertEqual((totals["observed"], totals["with_older_list"], totals["ceiling"]), (22, 25, 50))
        self.assertEqual((totals["pending_on_prefix"], totals["pending_with_older_list"], totals["pending_at_ceiling"]),
                         (1, 3, 29))
        self.assertNotIn("22", {r["video_id"] for r in rows})
        index["channels"][0]["exhausted"] = True
        channels, _ = forecast.candidates(selection, index, past)
        self.assertEqual(forecast.workload(channels, set())[1]["ceiling"], 22)

    def test_changed_roster_or_unanchored_history(self):
        selection, index, earlier = self.data()
        channels, _ = forecast.candidates(selection, index, [earlier[-1]])
        self.assertEqual(len(channels["a"][2]), 22)
        index["channels"][0]["observed_items"][0]["observed_primary_channel_id"] = "different"
        with self.assertRaisesRegex(ValueError, "channel identity"):
            forecast.candidates(selection, index, earlier)

    def test_rate_uses_one_cohort_and_nonoverlapping_intervals(self):
        points = [{"generated_at": f"2026-11-19T{hour}:00:00Z", "selection_sha256": "a",
                   "summary": {"audio_available": count}} for hour, count in enumerate((10, 90, 190), 10)]
        points.append(dict(points[1], selection_sha256="b", summary={"audio_available": 8000}))
        rate = forecast.measured_rate(points, "a")
        self.assertEqual(rate["recordings_per_hour"], 90)
        self.assertEqual(rate["nonoverlapping_hourly_rates"], [80, 100])
        points[1]["summary"] = {"audio_available": 5}
        with self.assertRaisesRegex(ValueError, "comparable"):
            forecast.measured_rate(points, "a")
