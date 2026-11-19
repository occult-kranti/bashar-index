"""Compare topic presence across a frozen recording frame and one primary text per episode.

Each observation supplies an offset-addressable text view, the topics assessed throughout
that text, and their match spans. An absent assessment stays unknown. A confirmed recording
family needs an evidence hash. Unresolved recordings form individually identified singletons.
All results refer to the supplied English texts. Timed selectors retain their source edition.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from bisect import bisect_left, bisect_right
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path
import re

try:
    from . import common, corpus_caption_view
except ImportError:
    import common
    import corpus_caption_view


def digest(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def label(value):
    return isinstance(value, str) and bool(value.strip())


def primary_frame(rows):
    frame = {}
    for row in rows:
        video, creator = row["video_id"], row["channel_dir"]
        if not label(creator) or not label(video) or video in frame:
            raise ValueError("Each selected recording needs one creator and one unique video ID")
        family = row.get("recording_family_id")
        proof = row.get("recording_family_evidence_sha256")
        if family is None:
            if proof is not None:
                raise ValueError("Family evidence requires a confirmed family assignment")
            group = ("unresolved", video)
        elif label(family) and digest(proof):
            group = ("confirmed", family)
        else:
            raise ValueError("Confirmed family assignment needs an ID and evidence hash")
        frame[video] = {"creator": creator, "group": group, "family_evidence": proof}
    return frame


def interval(segment):
    start, end = segment.get("time_start"), segment.get("time_end")
    if any(x is not None and (type(x) not in (int, float) or not math.isfinite(x) or x < 0)
           for x in (start, end)):
        raise ValueError("Invalid time in source segment")
    if end is not None and (start is None or end < start):
        raise ValueError("Invalid source segment time interval")
    return start, end


def prepare_observation(observation, frame, topics):
    view = observation["view"]
    video, text = view["video_id"], view["text"]
    if (video not in frame or frame[video]["creator"] != view.get("channel_dir")
            or not isinstance(text, str) or not text.strip()
            or view.get("offset_unit") != "unicode_codepoint"
            or not re.fullmatch(r"en(?:[-_][A-Za-z0-9]+)*", view.get("language") or "", re.I)
            or not label(view.get("source_kind"))
            or not all(digest(view.get(k)) for k in ("text_version_id", "raw_sha256", "text_sha256"))
            or sha256(text.encode()).hexdigest() != view["text_sha256"]):
        raise ValueError("Unbound English primary text view or stale text offsets")
    assessed = observation["assessed_topics"]
    if (not digest(observation.get("assessment_method_sha256")) or not isinstance(assessed, list)
            or not all(label(t) for t in assessed) or len(set(assessed)) != len(assessed)
            or not set(assessed) <= topics):
        raise ValueError("Pin the assessment method and declare the distinct topics assessed throughout the view")
    assessed = set(assessed)
    segments, cursor, source_ids = [], 0, set()
    for segment in view["segments"]:
        a, b = segment["char_start"], segment["char_end"]
        source_id = segment["source_segment_id"]
        if (type(a) is not int or type(b) is not int or not cursor <= a < b <= len(text)
                or not label(source_id) or source_id in source_ids):
            raise ValueError("Invalid source segment offsets or identifier")
        start, end = interval(segment)
        segments.append((a, b, source_id, start, end))
        cursor = b
        source_ids.add(source_id)

    starts = [s[0] for s in segments]
    ends = [s[1] for s in segments]
    evidence, seen = [], set()
    for match in observation["matches"]:
        topic, a, b = match["topic"], match["char_start"], match["char_end"]
        if (topic not in assessed or type(a) is not int or type(b) is not int
                or not 0 <= a < b <= len(text) or not text[a:b].strip()):
            raise ValueError("Match must address a nonempty span of an assessed topic")
        if (topic, a, b) in seen:
            continue
        seen.add((topic, a, b))
        anchors = []
        for left, right, segment_id, start, end in segments[bisect_right(ends, a):bisect_left(starts, b)]:
            if text[max(left, a):min(right, b)].strip():
                anchors.append({"source_segment_id": segment_id, "char_start": max(a, left),
                                "char_end": min(b, right), "time_start": start, "time_end": end})
        evidence.append({"topic": topic, "char_start": a, "char_end": b, "source_segments": anchors})
    exposure = [(a, b) for _, _, _, a, b in segments if a is not None and b is not None]
    timing = "untimed"
    if segments and any(a is not None for _, _, _, a, _ in segments):
        timing = "timed" if len(exposure) == len(segments) else "partially_timed"
    proof = {k: view[k] for k in ("video_id", "channel_dir", "text_version_id", "text_sha256",
                                  "raw_sha256", "source_kind", "language")}
    for key in ("source_edition_id", "source_audio_sha256", "edition_receipt_sha256", "source_timebase",
                "original_language", "translation_performed", "caption_kind"):
        if key in view:
            proof[key] = view[key]
    proof.update(timing=timing, assessed_topics=sorted(assessed),
                 assessment_method_sha256=observation["assessment_method_sha256"],
                 known_cue_union_seconds=corpus_caption_view.timed_union(
                     [{"start": a, "end": b} for a, b in exposure]),
                 matches=sorted(evidence, key=lambda x: (x["char_start"], x["char_end"], x["topic"])))
    return video, (assessed, {x["topic"] for x in evidence}, proof)


def measure(frame, rows, observation_by_video, required):
    """Each assessed episode has one vote. Each observed family has one vote in the second mean."""
    per_family = defaultdict(Counter)
    total = Counter()
    supporting = []
    for video in rows:
        counts = per_family[frame[video]["group"]]
        counts["eligible"] += 1
        total["eligible"] += 1
        observation = observation_by_video.get(video)
        if observation is None:
            continue
        assessed, topics_present, proof = observation
        if not required <= assessed:
            # Even a partial assessment can exclude co-occurrence when one required topic was absent.
            if (required & assessed) - topics_present:
                counts["ruled_out"] += 1
            continue
        for key in ("assessed", proof["timing"]):
            total[key] += 1
        counts["assessed"] += 1
        if required & topics_present:
            total["any"] += 1
        if required <= topics_present:
            counts["positive"] += 1
            total["positive"] += 1
            supporting.append(video)
    observed = [f for f in per_family.values() if f["assessed"]]
    families = len(per_family)
    observed_family_share = (sum(f["positive"] / f["assessed"] for f in observed) / len(observed)
                             if observed else None)
    # Sharp bounds assign every unassessed episode to absent or present within its own family.
    lower = sum(f["positive"] / f["eligible"] for f in per_family.values()) / families
    upper = sum((f["positive"] + f["eligible"] - f["assessed"] - f["ruled_out"]) / f["eligible"]
                for f in per_family.values()) / families
    result = {"eligible_episodes": total["eligible"], "assessed_episodes": total["assessed"],
              "positive_episodes": total["positive"], "eligible_families": families,
              "assessed_families": len(observed), "positive_families": sum(f["positive"] > 0 for f in observed),
              "unresolved_family_singletons": sum(group[0] == "unresolved" for group in per_family),
              "episode_share": total["positive"] / total["assessed"] if total["assessed"] else None,
              "family_balanced_observed_share": observed_family_share,
              "family_balanced_frame_bounds": [lower, upper],
              "timing_of_assessed_episodes": {k: total[k] for k in ("timed", "partially_timed", "untimed")},
              "supporting_video_ids": sorted(supporting)}
    if len(required) == 2:
        result["episodes_with_either_topic"] = total["any"]
        result["episode_jaccard"] = total["positive"] / total["any"] if total["any"] else None
    return result


def compare(frame_rows, observations, topic_ids):
    """Produce channel heatmap cells, same-episode graph edges, and their private evidence table."""
    if (not isinstance(topic_ids, list) or not topic_ids or not all(label(t) for t in topic_ids)
            or len(set(topic_ids)) != len(topic_ids)):
        raise ValueError("Declare each topic once")
    frame = primary_frame(frame_rows)
    topics, views = set(topic_ids), {}
    for record in observations:
        video, prepared = prepare_observation(record, frame, topics)
        if video in views:
            raise ValueError("Preselect one text version per recording before comparing topics")
        views[video] = prepared
    groups = defaultdict(list)
    for video, item in sorted(frame.items()):
        groups[item["creator"]].append(video)
    cells, edges = [], []
    for creator, videos in sorted(groups.items()):
        for topic in sorted(topics):
            cells.append({"channel_dir": creator, "topic": topic,
                          **measure(frame, videos, views, {topic})})
        for left, right in combinations(sorted(topics), 2):
            edges.append({"channel_dir": creator, "topic_a": left, "topic_b": right,
                          **measure(frame, videos, views, {left, right})})
    sources = [views[video][2] for video in sorted(views)]
    membership = [{"video_id": video, "channel_dir": row["creator"],
                   "recording_family_id": row["group"][1] if row["group"][0] == "confirmed" else None,
                   "recording_family_evidence_sha256": row["family_evidence"]}
                  for video, row in sorted(frame.items())]
    return {"schema_version": 1, "eligible_episodes": len(frame), "primary_texts": len(views),
            "heatmap": cells, "same_episode_co_mentions": edges, "frame": membership, "evidence": sources}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", required=True, type=Path, help="Frozen recording rows, optionally inside a rows field")
    parser.add_argument("--observations", required=True, type=Path, help="Private array of primary views and assessments")
    parser.add_argument("--topics", required=True, type=Path, help="JSON array of topic identifiers")
    parser.add_argument("--out", required=True, type=Path, help="Private comparison file outside Git")
    args = parser.parse_args(argv)
    dest = common.ensure_outside_git(args.out)
    rows = json.loads(args.frame.read_bytes())
    result = compare(rows["rows"] if isinstance(rows, dict) else rows,
                     json.loads(args.observations.read_bytes()), json.loads(args.topics.read_bytes()))
    common.atomic_write_text(dest, json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
