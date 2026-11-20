import csv
import io
import unittest

from pipeline import collection_failure_report as f


class FailureReportTests(unittest.TestCase):
    def setUp(self):
        self.frame = [
            dict(video_id=str(i).zfill(11), source_channel_name="Creator", channel_dir="creator",
                 title="Recording | [test]", tab="videos", listing_rank=i-1) for i in range(1, 6)]
        self.keys = [r["video_id"] for r in self.frame]
        self.at = 1_790_000_010
        stamp = self.at - 5
        self.attempt = {"attempt_at_epoch": stamp, "source_started_at_epoch": stamp,
                        "attempt": {"sha256": "a"*64}, "status": "held", "error_class": "source_403"}
        self.refused = {"disposition": "current_source_refusal", "current_source_refusals": [
            {"at_epoch": self.at, "status": 403, "attempt_sha256": "a"*64}],
            "closed_attempt_history": [self.attempt]}
        self.local = {"disposition": "ordinary_ready_scoped_local_recovery", "closed_attempt_history": [
            {**self.attempt, "error_class": "qualified_downloader_failed", "source_response": {
                "status": 200, "body_complete": False, "content_length": 1200, "received_bytes": 64}}]}
        self.queued = {"disposition": "closed_native_ticket_pending", "closed_attempt_history": [
            {"error_class": "native_route_pending", "status": "native_route_pending", "attempt_at_epoch": stamp}]}

    def test_verified_recovery_and_queued_items_are_excluded(self):
        closed = {"at_epoch": self.at+1, "rows": [dict(outcome, video_id=key) for key, outcome in zip(
            self.keys, [self.refused, self.refused, self.local, self.queued,
                        {"disposition": "ordinary_ready_unattempted", "closed_attempt_history": []}])]}
        proof = {"generated_at": "2026-11-20T01:00:00Z", "summary": {"channels": 1, "latest20_target": 5, "audio_available": 1}}
        report = f.assemble(self.frame, dict.fromkeys(self.keys, 120), closed, proof, [{"video_id": self.keys[1]}])
        self.assertEqual(report["remaining"], 4)
        self.assertEqual(report["other_pending"], 2)
        rows = report["failures"]
        self.assertEqual([r["video_id"] for r in rows], [self.keys[0], self.keys[2]])
        self.assertEqual([r["rank"] for r in rows], [1,3])
        self.assertEqual([r["http_status"] for r in rows], [403,200])
        self.assertEqual(rows[0]["attempt_count"], 1)
        self.assertIn("64 of 1,200 bytes", rows[1]["reason"])
        self.assertEqual(rows[0]["last_attempt_utc"], f.utc(self.at-5))
        self.assertEqual(rows[0]["last_refusal_utc"], f.utc(self.at))
        self.assertNotIn(self.keys[1], f.markdown(report))
        self.assertIn(f"({rows[0]['url']})", f.markdown(report))

    def test_pending_handoff_is_not_a_failure_and_unknown_error_text_is_never_exported(self):
        self.assertIsNone(f.failed_outcome(self.queued))
        payload = {"disposition":"local_or_administrative_hold","closed_attempt_history":[
            dict(self.attempt, error_class="private-drive-path-or-secret")]}
        failure = f.failed_outcome(payload)
        self.assertEqual(failure["category"], "needs_review")
        self.assertNotIn("private-drive-path-or-secret", str(failure))
        pause = f.failed_outcome(dict(self.refused, current_source_refusals=[
            {"at_epoch": self.at, "status": 429, "retry_not_before_epoch": self.at+300}]))
        self.assertIn(f.utc(self.at+300), pause["next_step"])
        self.assertIsNone(f.failed_outcome(dict(disposition="ordinary_ready_unattempted", closed_attempt_history=[])))

    def test_csv_public_links_spreadsheet_formulas_and_markdown_escape(self):
        row = dict.fromkeys(f.COLUMNS, "")
        row.update(title="=SUM(1,2)", creator="@creator", category="provider_refusal", url="https://www.youtube.com/watch?v=abcdefghijk")
        body = f.csv_content({"failures":[row]})
        values = list(csv.DictReader(io.StringIO(body.lstrip("\ufeff"))))
        self.assertEqual(values[0]["Creator"], "'@creator")
        self.assertEqual(values[0]["Video title"], "'=SUM(1,2)")
        self.assertEqual(values[0]["Video URL"], row["url"])
        self.assertEqual(f.md_cell("<i>A|[B]</i>"), r"&lt;i&gt;A\|\[B\]&lt;/i&gt;")

    def test_metadata_provider_failure_has_no_selected_media_http_status(self):
        row = {"disposition": "local_or_administrative_hold", "closed_attempt_history": [
            dict(self.attempt, error_class="wpc_provider_attempt_failed", source_response={})]}
        actual = f.failed_outcome(row)
        self.assertEqual(actual["category"], "metadata_failure")
        self.assertIsNone(actual["http_status"])
        self.assertIn("creator", actual["next_step"])

    def test_missing_audio_but_no_previous_failure_still_writes_a_header(self):
        result = dict(failures=[], selected=2, verified=0, remaining=2, other_pending=2, creators=1,
                      generated_at="2026-11-20T00:00:00Z", closed_at="2026-11-19T23:00:00Z")
        self.assertEqual(len(f.csv_content(result).splitlines()),1)
        self.assertIn("no documented unresolved download failures", f.markdown(result))


if __name__ == "__main__":
    unittest.main()
