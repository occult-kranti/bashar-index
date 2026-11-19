import hashlib
import unittest

from pipeline.corpus_concordance import Concordance


def text_view(lines):
    text = "\n".join(lines)
    cursor, spans = 0, []
    for i, line in enumerate(lines):
        spans.append({"source_segment_id": f"json3:{i}", "char_start": cursor, "char_end": cursor + len(line),
                      "time_start": i * 5, "time_end": None if i == len(lines)-1 else (i + 1)*5})
        cursor += len(line) + 1
    return {"video_id": "example_123", "text_version_id": "test-version", "bundle_sha256": "1" * 64,
            "text": text, "segments": spans, "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "language": "en-gb", "source_kind": "automatic_original"}


class ConcordanceTests(unittest.TestCase):
    def test_private_matches_retain_raw_cue_locators_offsets_and_unknown_end(self):
        view = text_view(["🌙 528 Hz. There was a control", "group."])
        rows = list(Concordance().records(view))
        frequency = next(r for r in rows if r.get("rule_id") == "frequency_numeric_hz")
        self.assertEqual(view["text"][frequency["start_codepoint"]:frequency["end_codepoint"]], "528 Hz")
        control = next(r for r in rows if r.get("rule_id") == "science_control_cue")
        self.assertEqual(control["matched_text"], "control\ngroup")
        self.assertEqual(control["raw_segment_ids"], ["json3:0", "json3:1"])
        self.assertEqual(control["raw_offset_mapping"][-1]["normalized_cue_end"], 5)
        self.assertIsNone(control["source_time_end_or_null"])
        self.assertIsNone(control["speaker_attribution_id_or_null"])

    def test_bounded_slices_reproduce_unbroken_regex_scan_once(self):
        engine = Concordance()
        step = engine.length - 2*engine.margin
        for n in (step-10, step-1, step, step+1, step+10):
            text = ("x" * n) + " within 12 days. " + ("much " * 800) + " a control group and 528 Hz."
            expected = sorted((name, m.span()) for name, _, rx in engine.rules for m in rx.finditer(text))
            actual = sorted((name, m.span()) for name, _, m in engine.matches(text))
            self.assertEqual(actual, expected)

    def test_detector_negative_windows_and_family_assignment(self):
        view = text_view(["chair " * 150 + "we will meet."])
        rows = list(Concordance().records(view, work_family_id="reviewed-f1", leakage_group_id="excerpts-g1"))
        anchors = [(r["word_count"], r["has_detector_match"]) for r in rows if r["record_type"] == "anchor"]
        self.assertEqual(anchors, [(150, False), (3, True)])
        self.assertTrue(all(r["work_family_id"] == "reviewed-f1" and r["leakage_group_id"] == "excerpts-g1" for r in rows))
        self.assertEqual(next(r["anchor_window_id"] for r in rows if r["record_type"] == "candidate"), 1)

    def test_wrong_language_changed_bytes_and_unmapped_text_fail(self):
        for change in ({"language": "ja"}, {"text_sha256": "0"*64}, {"segments": []}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                list(Concordance().records({**text_view(["testable"]), **change}))


if __name__ == "__main__":
    unittest.main()
