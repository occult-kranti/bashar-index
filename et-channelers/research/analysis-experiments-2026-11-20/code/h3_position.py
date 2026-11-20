"""Registered hypothesis H3: first-person singular is denser at the trimmed edges of a recording than in its middle.

The specification is the H3 entry of hypotheses.md (frozen 2026-11-20). This script fixes what that text
leaves to the implementation; those choices are listed in PROCEDURE below and were written before any
hold-out transcript was read.

    python h3_position.py --archive PRIVATE_ROOT --sets creator-sets.json --group seen     exploratory
    python h3_position.py --archive PRIVATE_ROOT --sets creator-sets.json --group holdout  the registered test

It reads transcripts from the private archive and prints numbers only. Creators are never named in the output.
"""
import argparse
import glob
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))      # so that python -I finds the filter beside this file
import artefact_filter  # noqa: E402

FIRST_PERSON = {"i", "me", "my", "mine", "myself", "i'm", "i've", "i'll", "i'd"}
PROCEDURE = {
    "recordings": "English, transcribed by the English-only model in the run of 2026-11-20, not publisher-feed audio; one audio file counted once",
    "trim_seconds_each_end": 180,
    "minimum_after_trim": {"seconds": 600, "words": 800},
    "bins": 10,
    "minimum_words_per_bin": 50,              # all ten bins, because the reference shifts every bin into every place
    "edges": [1, 10], "middle": [3, 4, 5, 6, 7, 8],
    "rate": "first-person singular tokens over all tokens, tokens taken from the recognizer's word list after the artefact filter",
    "U": "ln((f_edges + 0.5) / (w_edges + 1)) - ln((f_middle + 0.5) / (w_middle + 1)); the half count keeps a zero finite",
    "estimand": "mean over creators of each creator's mean U (creators weighted equally)",
    "reference": "each recording's ten bins shifted circularly by an independent random offset from 0 to 9; one-sided p = (b + 1) / (m + 1)",
    "draws": 9999, "bootstrap": "creators resampled, then recordings within each drawn creator; percentile interval", "bootstrap_draws": 9999,
    "seed": 20261120, "smallest_effect_of_interest": 0.10, "alpha_first_holm_step_of_ten": 0.005,
    "first_person_singular": sorted(FIRST_PERSON), "artefact_filter": artefact_filter.VERSION,
    "verdict": "supported if p is at most 0.005 and U is at least 0.10; refuted if U is negative or its 90% interval lies inside -0.10 to 0.10; otherwise undetermined",
}


def token(word):
    return artefact_filter.plain(word)


def bins_of(segments, duration, trim):
    """Per bin: [first-person singular tokens, all tokens] for the running time left after the trim."""
    low, high = trim, duration - trim
    span = (high - low) / 10
    cells = [[0, 0] for _ in range(10)]
    if span <= 0:
        return cells, 0.0
    for part in segments:
        for word in part.get("words") or []:
            when = word["start"]
            if not low <= when < high:
                continue
            text = token(word["word"])
            if not text:
                continue
            cell = cells[min(9, int((when - low) / span))]
            cell[1] += 1
            cell[0] += text in FIRST_PERSON
    return cells, high - low


def contrast(cells):
    f_edge = cells[0][0] + cells[9][0]
    w_edge = cells[0][1] + cells[9][1]
    f_mid = sum(cells[i][0] for i in range(2, 8))
    w_mid = sum(cells[i][1] for i in range(2, 8))
    return math.log((f_edge + 0.5) / (w_edge + 1)) - math.log((f_mid + 0.5) / (w_mid + 1))


def balanced(by_creator):
    return statistics.fmean(statistics.fmean(values) for values in by_creator.values())


def percentile(values, share):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(round(share * (len(ordered) - 1)))))]


def load(archive, creators, filtered, trim):
    """Eligible recordings of the given creators as (creator, bins)."""
    ledger = [json.loads(line) for line in open(archive / "sync" / "edition_asr_manifest.jsonl", encoding="utf-8") if line.strip()]
    seen_audio, rows, excluded = set(), [], {"other_creator": 0, "not_english_model": 0, "publisher_audio": 0, "duplicate_audio": 0, "too_short": 0, "too_few_words": 0, "thin_bin": 0}
    removed = {}
    for record in ledger:
        if record["channel_dir"] not in creators:
            excluded["other_creator"] += 1
            continue
        source = record["inference_source"]
        audio = source["audio"]["sha256"]
        if audio in seen_audio:
            excluded["duplicate_audio"] += 1
            continue
        seen_audio.add(audio)
        if source.get("source_type") == "publisher_audio_edition":
            excluded["publisher_audio"] += 1
            continue
        found = glob.glob(str(archive / "asr" / "results" / ("edition-" + audio) / record["run_id"] / "*.zip"))
        with zipfile.ZipFile(found[0]) as bundle:
            proof = json.loads(bundle.read("provenance.json"))
            if proof["language_decision"]["language"] != "en" or proof["compute"].get("text_model_role") != "english_only":
                excluded["not_english_model"] += 1
                continue
            segments = json.loads(bundle.read("original/segments.json"))["segments"]
        duration = proof["metrics"]["audio_seconds"]
        if filtered:
            segments, counts = artefact_filter.clean(segments, duration)
            for key, value in counts.items():
                removed[key] = removed.get(key, 0) + value
        cells, seconds = bins_of(segments, duration, trim)
        if seconds < PROCEDURE["minimum_after_trim"]["seconds"]:
            excluded["too_short"] += 1
        elif sum(cell[1] for cell in cells) < PROCEDURE["minimum_after_trim"]["words"]:
            excluded["too_few_words"] += 1
        elif min(cell[1] for cell in cells) < PROCEDURE["minimum_words_per_bin"]:
            excluded["thin_bin"] += 1
        else:
            rows.append((record["channel_dir"], cells))
    return rows, excluded, removed


def analyse(rows, draws, resamples, seed):
    by_creator = {}
    for creator, cells in rows:
        by_creator.setdefault(creator, []).append(cells)
    observed = balanced({creator: [contrast(cells) for cells in items] for creator, items in by_creator.items()})
    chance = random.Random(seed)
    at_least = 0
    for _ in range(draws):
        shifted = {}
        for creator, items in by_creator.items():
            values = []
            for cells in items:
                offset = chance.randrange(10)
                values.append(contrast(cells[offset:] + cells[:offset]))
            shifted[creator] = values
        at_least += balanced(shifted) >= observed
    names = sorted(by_creator)
    creator_values = {creator: [contrast(cells) for cells in by_creator[creator]] for creator in names}
    boot = []
    for _ in range(resamples):
        means = []
        for creator in (chance.choice(names) for _ in names):
            values = creator_values[creator]
            means.append(statistics.fmean(chance.choice(values) for _ in values))
        boot.append(statistics.fmean(means))
    creator_means = [statistics.fmean(values) for values in creator_values.values()]
    edge_rate = statistics.fmean(statistics.fmean(1000 * (c[0][0] + c[9][0]) / (c[0][1] + c[9][1]) for c in by_creator[n]) for n in names)
    middle_rate = statistics.fmean(statistics.fmean(1000 * sum(c[i][0] for i in range(2, 8)) / sum(c[i][1] for i in range(2, 8)) for c in by_creator[n]) for n in names)
    return {"creators": len(names), "recordings": len(rows), "U": round(observed, 4),
            "interval_90": [round(percentile(boot, 0.05), 4), round(percentile(boot, 0.95), 4)],
            "interval_95": [round(percentile(boot, 0.025), 4), round(percentile(boot, 0.975), 4)],
            "p_one_sided": round((at_least + 1) / (draws + 1), 5), "draws": draws,
            "creators_with_positive_U": sum(value > 0 for value in creator_means),
            "between_creator_sd": round(statistics.stdev(creator_means), 4) if len(creator_means) > 1 else None,
            "first_person_per_1000_words": {"edges": round(edge_rate, 1), "middle": round(middle_rate, 1)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--sets", required=True, type=Path)
    parser.add_argument("--group", required=True, choices=["seen", "holdout"])
    parser.add_argument("--counts-only", action="store_true", help="print how many creators and recordings are eligible, and nothing computed from text")
    args = parser.parse_args()
    sets = json.loads(args.sets.read_text(encoding="utf-8"))
    creators = set(sets["seen_creators"] if args.group == "seen" else sets["holdout_creators"])
    code = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest() for name in ("h3_position.py", "artefact_filter.py")}
    out = {"hypothesis": "H3", "group": args.group, "code_sha256": code, "procedure": PROCEDURE}
    rows, excluded, removed = load(args.archive, creators, True, PROCEDURE["trim_seconds_each_end"])
    out["eligible"] = {"creators": len({creator for creator, _ in rows}), "recordings": len(rows), "excluded": excluded}
    out["artefact_filter_removed"] = removed
    if not args.counts_only:
        out["registered_trimmed_filtered"] = analyse(rows, PROCEDURE["draws"], PROCEDURE["bootstrap_draws"], PROCEDURE["seed"])
        plain_rows, _, _ = load(args.archive, creators, False, PROCEDURE["trim_seconds_each_end"])
        out["trimmed_without_filter"] = analyse(plain_rows, 999, 999, PROCEDURE["seed"])
        untrimmed, _, _ = load(args.archive, creators, True, 0)
        out["untrimmed_filtered_reported_not_tested"] = analyse(untrimmed, 999, 999, PROCEDURE["seed"])
        result = out["registered_trimmed_filtered"]
        low, high = result["interval_90"]
        effect = PROCEDURE["smallest_effect_of_interest"]
        out["verdict"] = ("supported" if result["p_one_sided"] <= PROCEDURE["alpha_first_holm_step_of_ten"] and result["U"] >= effect
                          else "refuted" if result["U"] < 0 or (low > -effect and high < effect)
                          else "undetermined")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
