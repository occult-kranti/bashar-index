"""Offline checks for queue union, provenance and person/entity attribution."""
import json
import hashlib
import contextlib
import io
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prepare_all_queue as prepare


def row(video_id="ABCDEFGHIJK", channel="source-one", **fields):
    return dict(video_id=video_id, channel_dir=channel, title="Title", tab="videos",
                listing_rank="0", sources="discover", **fields)


class QueuePreparationTests(unittest.TestCase):
    def test_union_preserves_newest_priority_and_all_source_provenance(self):
        newest = row(entity="")
        older = dict(newest, title="Old title", listing_rank="12", sources="index", entity="Existing label")
        other = row("LMNOPQRSTUV")
        merged = prepare.merge_inputs([newest], [older, other], [other])
        self.assertEqual([r["video_id"] for r in merged], ["ABCDEFGHIJK", "LMNOPQRSTUV"])
        self.assertEqual(merged[0]["listing_rank"], "0")
        self.assertEqual(merged[0]["title"], "Title")
        self.assertEqual(merged[0]["entity"], "Existing label")
        self.assertEqual(merged[0]["sources"], "discover+index")
        self.assertEqual(merged[1]["queue_provenance"], "saved_full+fresh_discovery")

    def test_legacy_unknown_tab_rank_and_entity_are_preserved(self):
        legacy = dict(row(), tab="", listing_rank="", sources="bashar75", entity="")
        targets = {"darryl-anka": {"person_name": "Darryl Anka", "role": "channeler"}}
        output = prepare.enrich(prepare.merge_inputs([], [legacy], []), targets,
                                {legacy["video_id"]: {"channel": "Host Show"}})[0]
        self.assertEqual(output["tab"], "")
        self.assertEqual(output["listing_rank"], "")
        self.assertEqual(output["entity"], "")
        self.assertEqual(output["entity_label_basis"], "unknown")
        self.assertEqual(output["source_channel_name"], "Host Show")
        self.assertEqual(output["primary_person_name"], "Darryl Anka")
        self.assertEqual(output["primary_person_basis"], "bashar75_corpus")

    def test_discovery_ranks_each_tab_and_channel_independently(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "listing.jsonl"
            records = [{"video_id": vid, "person_id": person, "tab": tab} for vid, person, tab in [
                ("ABCDEFGHIJK", "one", "videos"), ("LMNOPQRSTUV", "one", "videos"),
                ("WXYZabcdefg", "one", "shorts"), ("hijklmnopqr", "two", "videos")]]
            path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
            output = prepare.discovery_rows(path)
        self.assertEqual([r["listing_rank"] for r in output], [0, 1, 0, 0])
        self.assertTrue(all(r["entity"] == "" for r in output))

    def test_host_rank_is_not_borrowed_from_other_channel(self):
        original = dict(row(), tab="", listing_rank="", sources="bashar75")
        fresh = row(channel="another-source")
        merged = prepare.merge_inputs([], [original], [fresh])[0]
        self.assertEqual((merged["tab"], merged["listing_rank"]), ("", ""))

    def test_rank_is_not_borrowed_from_other_tab(self):
        original = dict(row(), listing_rank="")
        fresh = dict(row(), tab="streams", listing_rank="7")
        merged = prepare.merge_inputs([], [original], [fresh])[0]
        self.assertEqual((merged["tab"], merged["listing_rank"]), ("videos", ""))

    def test_snapshot_hash_describes_exact_bytes_parsed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "queue.csv"
            data = b'video_id,title\r\nABCDEFGHIJK,"A title"\r\n'
            path.write_bytes(data)
            rows, evidence = prepare.snapshot(path)
            path.write_text('replacement', encoding='utf-8')
        self.assertEqual(rows[0]["title"], "A title")
        self.assertEqual(evidence["sha256"], hashlib.sha256(data).hexdigest())

    def test_invalid_id_and_tab_fail_closed(self):
        for bad in (dict(row(), video_id="bad"), dict(row(), tab="unrecognized")):
            with self.assertRaises(ValueError):
                prepare.merge_inputs([], [bad], [])

    def test_newest_out_preserves_original_order_and_input_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            target = base / "plan/targets.csv"
            host = base / "draft-package/csv/bashar_videos_in_repo_by_channel.csv"
            prepare.write_csv(target, [{"person_id": "source-one", "person_name": "A Person", "role": "channeler"}],
                              ["person_id", "person_name", "role"])
            prepare.write_csv(host, [], ["video_id", "channel"])
            newest, saved, output, enriched = [base / name for name in ("newest.csv", "saved.csv", "merged.csv", "enriched.csv")]
            original = [dict(row("LMNOPQRSTUV"), listing_rank="1"), row()]
            prepare.write_csv(newest, original, prepare.FIELDS)
            prepare.write_csv(saved, [row("WXYZabcdefg")], prepare.FIELDS)
            before = newest.read_bytes()
            with mock.patch.object(prepare, "ET_ROOT", base), contextlib.redirect_stdout(io.StringIO()):
                result = prepare.main(["--newest", str(newest), "--existing", str(saved),
                                       "--out", str(output), "--newest-out", str(enriched)])
            rows, _ = prepare.snapshot(enriched)
            self.assertEqual(result, 0)
            self.assertEqual(newest.read_bytes(), before)
            self.assertEqual([r["video_id"] for r in rows], [r["video_id"] for r in original])
            self.assertEqual([r["listing_rank"] for r in rows], ["1", "0"])
            self.assertTrue(all(r["primary_person_name"] == "A Person" for r in rows))
            metadata = json.loads(enriched.with_suffix('.meta.json').read_text())
            self.assertEqual(metadata["input"]["sha256"], hashlib.sha256(before).hexdigest())


if __name__ == "__main__":
    unittest.main()
