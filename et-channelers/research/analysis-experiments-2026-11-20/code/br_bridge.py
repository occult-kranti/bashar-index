"""Experiment BR, part (a): the two recognizer models on the same English audio.

The run transcribed English with an English-only model and other languages with a larger multilingual
model. Thirty-six English recordings (one per creator, hold-out creators excluded, drawn before any
result was seen) were transcribed again with the larger model. This script compares the pair of
transcripts of each recording, measure by measure.

For every measure it reports the mean paired difference (larger model minus English-only model), its
90% interval, the limits of agreement, and the difference in units of the between-creator standard
deviation. A measure is "bridge-safe" only if that interval lies inside 0.2 between-creator standard
deviations on both sides (two one-sided tests at 5%). The margin and the rule are the catalogue's.

The between-creator standard deviation of each measure comes from the English-only-model recordings
of the creators seen before the registry was frozen (creator means, creators with three or more
recordings). No hold-out creator is read.

    python -I br_bridge.py --archive PRIVATE_ROOT --plan bridge-plan.json --ledger bridge-ledger.jsonl \
        --sets creator-sets.json --out OUT_DIR

Output: br-bridge.json and br-pairs.csv. Numbers only: recordings are numbered, creators are not named.
"""
import argparse
import csv
import glob
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artefact_filter  # noqa: E402

MARGIN = 0.2                      # between-creator standard deviations, from the catalogue (BR, method)
MIN_RECORDINGS = 3                # a creator enters the between-creator spread with this many recordings
T90 = {35: 1.6896, 34: 1.6909, 33: 1.6924, 32: 1.6939, 31: 1.6955, 30: 1.6973, 29: 1.6991, 28: 1.7011, 27: 1.7033, 26: 1.7056,
       25: 1.7081, 24: 1.7109, 23: 1.7139, 22: 1.7171, 21: 1.7207, 20: 1.7247, 19: 1.7291, 18: 1.7341, 17: 1.7396, 16: 1.7459,
       15: 1.7531, 14: 1.7613, 13: 1.7709, 12: 1.7823, 11: 1.7959, 10: 1.8125, 9: 1.8331, 8: 1.8595, 7: 1.8946, 6: 1.9432, 5: 2.0150}
FIRST_SINGULAR = {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'll", "i'd"}
FIRST_PLURAL = {"we", "us", "our", "ours", "ourselves", "we're", "we've", "we'll", "we'd"}
SECOND = {"you", "your", "yours", "yourself", "yourselves", "you're", "you've", "you'll", "you'd"}
FILLERS = {"um", "uh", "uhm", "umm", "er", "erm", "ah", "hmm", "mm", "mhm"}
CONTRACTION = re.compile(r"^[a-z]+'(t|re|ve|ll|d|m)$")
MEASURES = [
    ("pace", "Words per minute of speech"),
    ("word_seconds", "Mean length of a word (seconds)"),
    ("long_pauses", "Pauses of one second or more, per minute of speech"),
    ("short_pauses", "Pauses of 0.3 to 1 second, per minute of speech"),
    ("pause_share", "Share of the running time inside pauses of 0.3 seconds or more"),
    ("first_singular", "First-person singular per 1,000 words"),
    ("first_plural", "First-person plural per 1,000 words"),
    ("second_person", "Second person per 1,000 words"),
    ("contractions", "Contracted forms per 1,000 words"),
    ("fillers", "Filled pauses (um, uh) per 1,000 words"),
    ("variety", "Share of distinct words in a moving window of 100 words"),
    ("word_letters", "Mean length of a word (letters)"),
    ("segment_words", "Words per recognizer segment"),
    ("word_probability", "Mean probability the recognizer gives its words"),
    ("thanks_inserted", "Inserted thanks phrase, per hour"),
    ("isolated_short", "Isolated short segments, per hour"),
    ("looped_words", "Words removed as loops, per 1,000 words"),
]


def measures(segments, duration, speech_seconds):
    """All measures of one transcript. Artefacts are counted on the raw segments and removed before the rest."""
    kept, removed = artefact_filter.clean(segments, duration)
    words = [word for part in kept for word in part.get("words") or []]
    tokens = [artefact_filter.plain(word["word"]) for word in words]
    pairs = [(token, word) for token, word in zip(tokens, words) if token]
    tokens = [token for token, _ in pairs]
    words = [word for _, word in pairs]
    count = len(tokens)
    if count < 200 or speech_seconds <= 0:
        return None, tokens
    minutes = speech_seconds / 60
    gaps = [max(0.0, later["start"] - earlier["end"]) for earlier, later in zip(words, words[1:])]
    window, distinct = 100, []
    for start in range(0, count - window + 1, 10):
        distinct.append(len(set(tokens[start:start + window])) / window)
    raw_words = sum(len(part.get("words") or []) for part in segments)
    return {
        "pace": count / minutes,
        "word_seconds": statistics.fmean(max(0.0, word["end"] - word["start"]) for word in words),
        "long_pauses": sum(gap >= 1.0 for gap in gaps) / minutes,
        "short_pauses": sum(0.3 <= gap < 1.0 for gap in gaps) / minutes,
        "pause_share": sum(gap for gap in gaps if gap >= 0.3) / duration,
        "first_singular": 1000 * sum(token in FIRST_SINGULAR for token in tokens) / count,
        "first_plural": 1000 * sum(token in FIRST_PLURAL for token in tokens) / count,
        "second_person": 1000 * sum(token in SECOND for token in tokens) / count,
        "contractions": 1000 * sum(bool(CONTRACTION.match(token)) for token in tokens) / count,
        "fillers": 1000 * sum(token in FILLERS for token in tokens) / count,
        "variety": statistics.fmean(distinct) if distinct else float("nan"),
        "word_letters": statistics.fmean(len(token.replace("'", "")) for token in tokens),
        "segment_words": count / max(1, len(kept)),
        "word_probability": statistics.fmean(word.get("probability") or 0.0 for word in words),
        "thanks_inserted": removed["thanks_inserted"] / (duration / 3600),
        "isolated_short": removed["isolated_short"] / (duration / 3600),
        "looped_words": 1000 * removed["looped_words"] / max(1, raw_words),
    }, tokens


def word_errors(reference, other):
    """Edit distance between two word lists (substitutions, deletions, insertions), by rows."""
    previous = list(range(len(other) + 1))
    for row, word in enumerate(reference, 1):
        current = [row] + [0] * len(other)
        for column, candidate in enumerate(other, 1):
            current[column] = min(previous[column] + 1, current[column - 1] + 1, previous[column - 1] + (word != candidate))
        previous = current
    return previous[-1]


def word_errors_fast(reference, other):
    try:
        import numpy
    except ImportError:
        return word_errors(reference, other)
    names = {}
    left = numpy.array([names.setdefault(word, len(names)) for word in reference])
    right = numpy.array([names.setdefault(word, len(names)) for word in other])
    steps = numpy.arange(len(right) + 1)
    previous = steps.copy()
    for row, word in enumerate(left, 1):
        current = numpy.empty(len(right) + 1, dtype=numpy.int64)
        current[0] = row
        numpy.minimum(previous[1:] + 1, previous[:-1] + (right != word), out=current[1:])
        current = numpy.minimum.accumulate(current - steps) + steps      # insertions along the row
        previous = current
    return int(previous[-1])


def read_bundle(path):
    with zipfile.ZipFile(path) as bundle:
        proof = json.loads(bundle.read("provenance.json"))
        segments = json.loads(bundle.read("original/segments.json"))["segments"]
    task = proof["metrics"]["tasks"]["original"]
    return proof, segments, proof["metrics"]["audio_seconds"], task["duration_after_vad_seconds"]


def bundle_of_record(archive, audio, run_id):
    found = glob.glob(str(archive / "asr" / "results" / ("edition-" + audio) / run_id / "*.zip"))
    return found[0] if found else None


def summary(differences, spread):
    count = len(differences)
    mean = statistics.fmean(differences)
    deviation = statistics.stdev(differences)
    half = T90[count - 1] * deviation / math.sqrt(count)
    row = {"pairs": count, "mean_difference": mean, "sd_of_differences": deviation, "interval_90": [mean - half, mean + half],
           "limits_of_agreement": [mean - 1.96 * deviation, mean + 1.96 * deviation]}
    if spread and spread > 0:
        row["between_creator_sd"] = spread
        row["in_sd_units"] = {"mean": mean / spread, "interval_90": [(mean - half) / spread, (mean + half) / spread]}
        row["bridge_safe"] = bool(-MARGIN < (mean - half) / spread and (mean + half) / spread < MARGIN)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--sets", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    archive, out = Path(args.archive), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    plan_bytes = Path(args.plan).read_bytes()
    plan = json.loads(plan_bytes)
    order = {row["audio_sha256"]: index for index, row in enumerate(plan["rows"], 1)}
    cells = {row["audio_sha256"]: row["cell"] for row in plan["rows"]}
    done = {}
    for line in Path(args.ledger).read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if row.get("status") == "transcribed":
            done[row["audio_sha256"]] = row

    pairs = []
    for audio, row in sorted(done.items(), key=lambda item: order[item[0]]):
        record = bundle_of_record(archive, audio, row["run_id_of_record"])
        proof_small, segments_small, duration, speech = read_bundle(record)
        proof_large, segments_large, _, speech_large = read_bundle(archive / row["bundle_path"])
        assert proof_small["compute"].get("text_model_role") == "english_only", "the transcript of record is not from the English-only model"
        assert "large-v3" in proof_large["model"]["repository"] and "distil" not in proof_large["model"]["repository"]
        small, tokens_small = measures(segments_small, duration, speech)
        large, tokens_large = measures(segments_large, duration, speech_large)
        if small is None or large is None:
            continue
        errors = word_errors_fast(tokens_large, tokens_small)
        pairs.append({"recording": order[audio], "cell": cells[audio], "english_only": small, "larger": large,
                      "words": {"english_only": len(tokens_small), "larger": len(tokens_large)},
                      "word_disagreement": errors / max(1, len(tokens_large)),
                      "speech_seconds_equal": abs(speech - speech_large) < 0.5})

    # between-creator spread on the English-only-model recordings of the reference creators
    creators = set(json.loads(Path(args.sets).read_text(encoding="utf-8"))["seen_creators"])
    by_creator, seen_audio = {}, set()
    for line in open(archive / "sync" / "edition_asr_manifest.jsonl", encoding="utf-8"):
        if not line.strip():
            continue
        record = json.loads(line)
        source = record["inference_source"]
        audio = source["audio"]["sha256"]
        if record["channel_dir"] not in creators or audio in seen_audio or source.get("source_type") == "publisher_audio_edition":
            continue
        seen_audio.add(audio)
        path = bundle_of_record(archive, audio, record["run_id"])
        if not path:
            continue
        proof, segments, duration, speech = read_bundle(path)
        if proof["language_decision"]["language"] != "en" or proof["compute"].get("text_model_role") != "english_only":
            continue
        values, _ = measures(segments, duration, speech)
        if values:
            by_creator.setdefault(record["channel_dir"], []).append(values)
    spread, reference_creators = {}, 0
    eligible = {creator: rows for creator, rows in by_creator.items() if len(rows) >= MIN_RECORDINGS}
    reference_creators = len(eligible)
    for key, _ in MEASURES:
        means = [statistics.fmean(row[key] for row in rows if not math.isnan(row[key])) for rows in eligible.values()]
        spread[key] = statistics.stdev(means)

    table = []
    for key, label in MEASURES:
        usable = [pair for pair in pairs if not (math.isnan(pair["larger"][key]) or math.isnan(pair["english_only"][key]))]
        differences = [pair["larger"][key] - pair["english_only"][key] for pair in usable]
        row = {"measure": key, "label": label,
               "mean_english_only": statistics.fmean(pair["english_only"][key] for pair in usable),
               "mean_larger": statistics.fmean(pair["larger"][key] for pair in usable)}
        row.update(summary(differences, spread[key]))
        means = [(pair["larger"][key] + pair["english_only"][key]) / 2 for pair in usable]
        row["correlation_of_difference_with_level"] = statistics.correlation(means, differences) if len(set(means)) > 1 and len(set(differences)) > 1 else None
        table.append(row)
    disagreement = sorted(pair["word_disagreement"] for pair in pairs)
    quarter = lambda share: disagreement[min(len(disagreement) - 1, int(round(share * (len(disagreement) - 1))))]
    result = {
        "experiment": "BR (a)", "pairs": len(pairs), "planned": len(plan["rows"]),
        "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
        "code_sha256": {name: hashlib.sha256((Path(__file__).resolve().parent / name).read_bytes()).hexdigest()
                        for name in ("br_bridge.py", "artefact_filter.py")},
        "difference": "larger multilingual model minus English-only model, same audio",
        "margin_in_between_creator_sd": MARGIN,
        "rule": "bridge-safe if the 90% interval of the mean difference lies inside the margin on both sides",
        "between_creator_sd_from": {"group": "creators seen before the registry was frozen", "creators_with_three_or_more_recordings": reference_creators,
                                    "recordings": sum(len(rows) for rows in eligible.values())},
        "word_disagreement": {"definition": "word edits (substitution, deletion, insertion) needed to turn the English-only "
                                            "transcript into the larger model's, over the larger model's word count, after the "
                                            "artefact filter and lower-casing; neither transcript is a human reference",
                              "mean": statistics.fmean(disagreement), "median": quarter(0.5), "quartiles": [quarter(0.25), quarter(0.75)],
                              "smallest": disagreement[0], "largest": disagreement[-1]},
        "speech_seconds_equal_in_all_pairs": all(pair["speech_seconds_equal"] for pair in pairs),
        "measures": table,
        "bridge_safe": [row["measure"] for row in table if row.get("bridge_safe")],
        "not_bridge_safe": [row["measure"] for row in table if not row.get("bridge_safe")],
    }
    (out / "br-bridge.json").write_text(json.dumps(result, indent=1), encoding="utf-8", newline="\n")
    with open(out / "br-pairs.csv", "w", encoding="utf-8", newline="") as handle:
        sheet = csv.writer(handle, lineterminator="\n")
        sheet.writerow(["recording", "measure", "english_only_model", "larger_model"])
        for pair in pairs:
            for key, _ in MEASURES:
                sheet.writerow([pair["recording"], key, round(pair["english_only"][key], 5), round(pair["larger"][key], 5)])
            sheet.writerow([pair["recording"], "word_disagreement", "", round(pair["word_disagreement"], 5)])
    print(json.dumps({"pairs": len(pairs), "word_disagreement_median": round(quarter(0.5), 4),
                      "bridge_safe": result["bridge_safe"], "not_bridge_safe": result["not_bridge_safe"]}, indent=1))


if __name__ == "__main__":
    main()
