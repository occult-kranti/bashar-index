"""Private, source-addressable retrieval using the study's fixed English candidate lexicon."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

try:
    from . import common
except ImportError:
    import common


LEXICON = Path(__file__).resolve().parents[1] / "research/analysis-plan-2026-11-16/search-lexicon.json"


def validate_paragraph_view(view):
    """Verify the source paragraph addresses and enforce the untimed evidence boundary."""
    segments = view.get("segments")
    if (not isinstance(segments, list) or not segments or type(view.get("paragraph_count")) is not int
            or len(segments) != view["paragraph_count"] or view.get("source_timebase") is not None
            or view.get("source_timecodes_alignment_verified") is not False or view.get("usable_timed_text") is not False):
        raise ValueError("Untimed publisher text requires source paragraphs without aligned timestamps")
    previous, member = -1, None
    for index, row in enumerate(segments):
        if not isinstance(row, dict):
            raise ValueError("Expected a source paragraph record")
        ordinal = row.get("source_paragraph_index")
        source = row.get("source_member")
        if (type(row.get("paragraph_index")) is not int or row["paragraph_index"] != index
                or type(ordinal) is not int or ordinal <= previous
                or source not in ("word/document.xml", "publisher-transcript.en.txt")
                or (member is not None and source != member)
                or row.get("source_segment_id") != f"{source}:paragraph:{ordinal}"
                or ("time_start" not in row or row["time_start"] is not None)
                or ("time_end" not in row or row["time_end"] is not None)):
            raise ValueError("Publisher paragraph has an invalid source address or media timestamp")
        previous, member = ordinal, source


def paragraph_mapping(segments, first, last):
    return [{"source_segment_id": s["source_segment_id"], "source_member": s["source_member"],
             "source_paragraph_index": s["source_paragraph_index"], "paragraph_index": s["paragraph_index"],
             "normalized_paragraph_start": max(first, s["char_start"]) - s["char_start"],
             "normalized_paragraph_end": min(last, s["char_end"]) - s["char_start"]} for s in segments]


class Concordance:
    def __init__(self):
        source = LEXICON.read_text(encoding="utf-8")
        self.revision = hashlib.sha256(source.encode()).hexdigest()
        lexicon = json.loads(source)
        settings = lexicon["engine_contract"]
        self.length = settings["maximum_scan_codepoints"]
        self.margin = settings["overlap_codepoints"]
        self.anchor_words = settings["anchor_window_words_proposed"]
        self.rules = [(r["id"], r["candidate_family"], re.compile(r["pattern"], re.I)) for r in lexicon["rules"]]

    def matches(self, text):
        """Assign each match to the slice with its first character; neighboring slices supply context."""
        step = self.length - 2 * self.margin
        for start in range(0, len(text), step):
            end = min(start + step, len(text))
            left, right = max(0, start - self.margin), min(len(text), end + self.margin)
            for rule, category, pattern in self.rules:
                for match in pattern.finditer(text, left, right):
                    if start <= match.start() < end:
                        yield rule, category, match

    def records(self, view, *, work_family_id=None, leakage_group_id=None):
        text, segments = view["text"], view["segments"]
        if (not isinstance(text, str) or not text.strip() or hashlib.sha256(text.encode()).hexdigest() != view["text_sha256"]
                or not re.fullmatch(r"en(?:-[A-Za-z0-9]+)*", view["language"], re.I)):
            raise ValueError("Expected a pinned nonempty English text view")
        if not segments:
            raise ValueError("The text view requires source segments")
        paragraph_view = view.get("source_kind") == "publisher_untimed_transcript"
        if paragraph_view:
            validate_paragraph_view(view)
        starts, ends, previous = [], [], 0
        for row in segments:
            start, end = row["char_start"], row["char_end"]
            if (type(start) is not int or type(end) is not int or not previous <= start < end <= len(text)
                    or text[previous:start].strip() or not row.get("source_segment_id")):
                raise ValueError("Source segment offsets leave content unmapped or overlap")
            starts.append(start)
            ends.append(end)
            previous = end
        if text[previous:].strip():
            raise ValueError("Trailing text lacks source coordinates")
        words = [w.start() for w in re.finditer(r"\S+", text)]
        hit_anchors = set()
        base = {"video_id": view["video_id"], "text_version_id": view["text_version_id"],
                "artifact_sha256": view["bundle_sha256"], "lexicon_revision": self.revision,
                "language_provenance": view["language"], "source_kind": view["source_kind"],
                "work_family_id": work_family_id, "leakage_group_id": leakage_group_id,
                "speaker_attribution_id_or_null": None}
        if paragraph_view:
            base.update(evidence_granularity="paragraph", source_timebase=None,
                        source_document_sha256=view["source_document_sha256"], source_edition_id=view["source_edition_id"],
                        edition_receipt_sha256=view["edition_receipt_sha256"],
                        recording_association_method=view["recording_association_method"])
        for rule, category, match in self.matches(text):
            first, last = match.span()
            anchor = max(0, bisect_right(words, first) - 1) // self.anchor_words
            hit_anchors.add(anchor)
            touched = segments[bisect_right(ends, first):bisect_left(starts, last)]
            if not touched:
                raise ValueError("A match lacks a source cue")
            if paragraph_view:
                mapping = paragraph_mapping(touched, first, last)
            else:
                mapping = [{"source_segment_id": s["source_segment_id"],
                            "normalized_cue_start": max(first, s["char_start"]) - s["char_start"],
                            "normalized_cue_end": min(last, s["char_end"]) - s["char_start"]} for s in touched]
            times_start, times_end = [s["time_start"] for s in touched], [s["time_end"] for s in touched]
            yield {**base, "record_type": "candidate", "rule_id": rule, "candidate_family": category,
                   "anchor_window_id": anchor, "start_codepoint": first, "end_codepoint": last,
                   "matched_text": match.group(), "context_before": text[max(0, first-90):first],
                   "context_after": text[last:last+90], "raw_segment_ids": [m["source_segment_id"] for m in mapping],
                   "raw_offset_mapping": mapping, "source_time_start_or_null": min(times_start) if None not in times_start else None,
                   "source_time_end_or_null": max(times_end) if None not in times_end else None,
                   "review_status": "unreviewed_candidate"}
        for i in range(0, len(words), self.anchor_words):
            stop = min(i + self.anchor_words, len(words))
            index = i // self.anchor_words
            last = words[stop] if stop < len(words) else len(text)
            item = {**base, "record_type": "anchor", "anchor_window_id": index, "start_codepoint": words[i],
                    "end_codepoint": last, "word_count": stop-i, "has_detector_match": index in hit_anchors}
            if paragraph_view:
                touched = segments[bisect_right(ends, words[i]):bisect_left(starts, last)]
                mapping = paragraph_mapping(touched, words[i], last)
                item.update(raw_segment_ids=[s["source_segment_id"] for s in touched], raw_offset_mapping=mapping,
                            source_time_start_or_null=None, source_time_end_or_null=None)
            yield item


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", type=Path, required=True, help="Private corpus text view")
    parser.add_argument("--out", type=Path, required=True, help="Private JSONL output")
    parser.add_argument("--work-family-id", help="Reviewed same-recording family when established")
    parser.add_argument("--leakage-group-id", help="Reviewed copy/excerpt group when established")
    args = parser.parse_args(argv)
    source, out = common.ensure_outside_git(args.view), common.ensure_outside_git(args.out)
    if source == out or out.suffix.lower() != ".jsonl":
        parser.error("Choose a distinct private JSONL destination")
    view = json.loads(source.read_bytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=out.parent, suffix=".part", encoding="utf-8",
                                         newline="\n", delete=False) as target:
            temporary = Path(target.name)
            for record in Concordance().records(view, work_family_id=args.work_family_id, leakage_group_id=args.leakage_group_id):
                target.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                count += 1
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, out)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(json.dumps({"video_id": view["video_id"], "private_records": count}))


if __name__ == "__main__":
    main()
