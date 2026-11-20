"""Build small research packets from validated aggregate tables and traceable local text passages."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path


def method_evidence(snapshot):
    counts = snapshot["summary"]
    return {
        "SELECTION": {"selection_sha256": snapshot["selection_sha256"], "recordings": counts["latest20_target"],
            "creators": counts["channels"], "design": "Latest 20 public completed regular Videos-tab uploads per creator, no duration or date cutoff. Exhausted smaller catalogs are included."},
        "EDITIONS": {key: counts[key] for key in ("audio_available", "youtube_native_audio", "publisher_only_audio", "qualified_youtube_only_audio")},
        "SOURCE-QUALITY": "Qualified YouTube audio lacks confirmed original track or language. A publisher counterpart can have another edit and timebase. Text source, claimed entity and recording family are separate evidence fields.",
        "EVENT-LEAD": "A user reported a recent Dreemtime Academy and Sam the Illusionist discussion of the same event. Treat this as a search lead pending explicit event identifiers, independent dated sources and comparison of both recordings.",
        "RESEARCH-DESIGN": "Study topics include claimed entities, shared events, predictions, proposed experiments, healing and frequency claims. Measure lexical overlap, date and topic distributions, creator balance, excerpt attribution and alternative explanations.",
        "METHOD-SBERT": {"reference": "Reimers and Gurevych (2019), Sentence-BERT",
            "url": "https://aclanthology.org/D19-1410/",
            "method": "Sentence embeddings permit cosine comparisons across passages. For this corpus, evaluate whether retrieved pairs describe the same identifiable event before counting agreement."},
        "METHOD-HDBSCAN": {"reference": "McInnes, Healy and Astels (2017), hdbscan",
            "url": "https://joss.theoj.org/papers/10.21105/joss.00205",
            "method": "Hierarchical density-based clustering offers a comparison for thresholded similarity graphs. Report parameter sensitivity, unassigned passages and duplicate-family handling as corpus-specific evaluation decisions."},
    }


def _csv(path):
    with path.open(encoding="utf-8-sig", newline="") as reader:
        yield from csv.DictReader(reader)


def corpus_evidence(generation, base):
    generation = Path(generation)
    manifest = json.loads((generation / "manifest.json").read_bytes())
    roster = json.loads((generation / "view-inventory.json").read_bytes())
    frame = {r["video_id"]: r for r in roster}
    evidence = dict(base)
    evidence["CORPUS"] = {"revision": manifest["revision"], "all_recordings": len(roster),
                          "selected_english_texts": manifest["eligible_primary_texts"],
                          "missing_with_review": manifest["missing_primary_texts"],
                          "english_text_sources": dict(Counter(r["selected_primary"]["source_kind"]
                            for r in roster if r["selected_primary"])),
                          "measurement": "Lexicon hits are unreviewed textual candidates. A co-mention is within one recording. Neither establishes endorsement, accuracy or a common event."}

    by_topic = defaultdict(Counter)
    by_pair = []
    for row in _csv(generation / "figures" / "creator-topic.csv"):
        counts = by_topic[row["topic"]]
        for key in ("eligible_episodes", "assessed_episodes", "positive_episodes"):
            counts[key] += int(row[key])
        if int(row["positive_episodes"]):
            counts["creators_with_candidates"] += 1
    for row in _csv(generation / "figures" / "co-mention-network.csv"):
        by_pair.append({k: row[k] for k in ("topic_a", "topic_b", "jointly_assessed_episodes",
                       "supporting_episodes", "supporting_creators", "distinct_supporting_families",
                       "unresolved_supporting_singletons")})
    evidence["TOPIC-COUNTS"] = {k: dict(v) for k, v in sorted(by_topic.items())}
    evidence["CO-MENTIONS"] = sorted(by_pair, key=lambda r: (-int(r["supporting_episodes"]), r["topic_a"], r["topic_b"]))[:18]

    # Per topic and creator, keep the lowest hash. This is independent of archive
    # order. Spans retained in the final packet come from distinct recordings.
    samples = defaultdict(dict)
    with (generation / "concordance.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["record_type"] != "candidate":
                continue
            vid, topic = row["video_id"], row["candidate_family"]
            owner = frame[vid]["channel_dir"]
            chosen = frame[vid]["selected_primary"]
            if not chosen or row["text_version_id"] != chosen["text_version_id"]:
                raise ValueError("Candidate sample does not match its selected text")
            key = sha256(f"{topic}|{vid}|{row['start_codepoint']}|{row['rule_id']}".encode()).hexdigest()
            previous = samples[topic].get(owner)
            if previous is None or key < previous[0]:
                samples[topic][owner] = key, row
    used = set()
    for topic, by_owner in sorted(samples.items()):
        accepted = 0
        for key, row in sorted(by_owner.values(), key=lambda item: item[0]):
            vid = row["video_id"]
            if vid in used:
                continue
            context = (row["context_before"].split()[-10:] + row["matched_text"].split()[:10]
                       + row["context_after"].split()[:10])
            evidence["PASSAGE-" + key[:12]] = {"video_id": vid, "url": "https://www.youtube.com/watch?v=" + vid,
                "creator": frame[vid]["channel_dir"], "topic": topic, "rule": row["rule_id"],
                "text_version_id": row["text_version_id"], "span": [row["start_codepoint"], row["end_codepoint"]],
                "context_excerpt": " ".join(context), "source_seconds": row.get("source_time_start_or_null"),
                "edition": row["source_kind"]}
            used.add(vid)
            accepted += 1
            if accepted == 3 or len(used) >= 45:
                break
        if len(used) >= 45:
            break
    evidence["SAMPLING"] = {"candidate_examples": len(used), "method": "At most three creator-distinct candidates per family and 45 overall, ordered by SHA-256. One excerpt per video. Aggregate counts cover all selected texts. Context is abbreviated."}
    return evidence
