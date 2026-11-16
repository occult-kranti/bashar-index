#!/usr/bin/env python3
"""A pilot of the model pass over the prediction candidates (ANALYSIS_PLAN 12.4 and 12.5): a blinded sample for
independent coders, and the scores of their labels.

    python3 -I pipeline/prediction_pilot.py sample --root ~/et-channelers-private --out <dir> --per-person 8
    python3 -I pipeline/prediction_pilot.py sample --root ~/et-channelers-private --out <new dir> --seed 2 \
        --exclude <earlier dir>                                  (a fresh sample, to measure rules the first one shaped)
    python3 -I pipeline/prediction_pilot.py score  --out <dir> labels_a.jsonl labels_b.jsonl
    python3 -I pipeline/prediction_pilot.py summary --publish plan/prediction_samples.csv <dir> [<dir> ...]

`sample` draws, with a fixed seed, up to --per-person candidates that have a target window from each person's
`analysis/predictions/<person>.jsonl`, shuffles them and writes `sample.jsonl` (uid, sentence, time expression:
no person, title, item or date, as 12.5 asks) and `key.jsonl` (what the coders must not see). `score` reads two
coders' labels and the key and writes `score.json`: agreement and Cohen's kappa on the type and on "prediction
like", and the share of candidates each coder and both coders call prediction-like (the rules pass's precision),
by kind (texts from the source apart from speech-to-text), by time rule and by person, and, from the
`strata.json` that `sample` writes, the share weighted by each person's windowed candidates, with a Wilson
interval for the plain share and a stratified interval (finite population correction) for the weighted one.
Everything stays private; score.json holds counts and uids only, no text. `sample` also writes `meta.json`
(seed, per person, the folders excluded, and --purpose). `summary` writes one row of counts per sample folder
(no text, no uids), which may be published as plan/prediction_samples.csv.
"""
from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import add_root_arg, atomic_write_text, ensure_outside_git, read_jsonl  # noqa: E402

TYPES = ("prediction", "conditional_prediction", "warning", "prophecy", "timeline_schedule", "self_validation",
         "refusal_to_date", "future_tense_teaching", "not_future", "promotion_or_logistics", "unclear")
PREDICTION_LIKE = {"prediction", "conditional_prediction", "warning", "prophecy", "timeline_schedule"}


def draw(rows, per_person, seed, exclude=()):
    """Up to per_person rows with a target window from each person, in a seeded, shuffled order; sentences in
    exclude (an earlier sample's) are never drawn again, so a fresh sample can measure rules that sample shaped."""
    exclude = set(exclude)
    by = collections.defaultdict(list)
    for r in rows:
        if r["sentence"] in exclude:
            continue
        if r.get("window_lo") is not None or r.get("window_hi") is not None:
            by[r["person_id"]].append(r)
    rng = random.Random(seed)
    picked = []
    for person in sorted(by):
        rs = sorted(by[person], key=lambda r: (r["item_id"], r["sentence"]))
        picked += rng.sample(rs, min(per_person, len(rs)))
    rng.shuffle(picked)
    return picked


def kappa(a, b):
    """Cohen's kappa for two equal-length label lists (1.0 when both are constant and equal)."""
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = collections.Counter(a), collections.Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else round((po - pe) / (1 - pe), 3)


def weighted_share(res_by_person, strata):
    """The share both coders call prediction-like, each person weighted by their windowed candidates (strata),
    over the people sampled: an estimate for the whole windowed set rather than for the sample."""
    num = den = 0
    for person, s in res_by_person.items():
        if s["units"] and strata.get(person):
            num += strata[person] * s["both_prediction_like"] / s["units"]
            den += strata[person]
    return round(num / den, 3) if den else None


def wilson(k, n, z=1.96):
    """Wilson score interval for k of n (95% by default); None for n = 0."""
    if not n:
        return None
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def weighted_interval(res_by_person, strata, z=1.96):
    """95% interval of weighted_share: stratified by person, each stratum's variance p(1-p)/(n-1) with the
    finite population correction (1 - n/N), over the people sampled; None without strata."""
    den = sum(strata.get(p, 0) for p, s in res_by_person.items() if s["units"] and strata.get(p))
    if not den:
        return None
    est = var = 0.0
    for person, s in res_by_person.items():
        n, big = s["units"], strata.get(person, 0)
        if not n or not big:
            continue
        w, p = big / den, s["both_prediction_like"] / n
        est += w * p
        if n > 1:
            var += w * w * max(0.0, 1 - n / big) * p * (1 - p) / (n - 1)
    half = z * math.sqrt(var)
    return [round(max(0.0, est - half), 3), round(min(1.0, est + half), 3)]


def score(a_rows, b_rows, key_rows, strata=None):
    a = {r["uid"]: r for r in a_rows}
    b = {r["uid"]: r for r in b_rows}
    key = {r["uid"]: r for r in key_rows}
    uids = [u for u in key if u in a and u in b]
    missing = sorted(set(key) - set(uids))
    bad = sorted(u for u in uids if a[u].get("type") not in TYPES or b[u].get("type") not in TYPES)
    uids = [u for u in uids if u not in bad]
    like = lambda r: r.get("type") in PREDICTION_LIKE  # noqa: E731
    ta, tb = [a[u]["type"] for u in uids], [b[u]["type"] for u in uids]
    la, lb = [like(a[u]) for u in uids], [like(b[u]) for u in uids]

    def share(group):
        us = [u for u in uids if group(u)]
        n = len(us)
        return {"units": n,
                "coder_a_prediction_like": sum(like(a[u]) for u in us),
                "coder_b_prediction_like": sum(like(b[u]) for u in us),
                "both_prediction_like": sum(like(a[u]) and like(b[u]) for u in us),
                "either_prediction_like": sum(like(a[u]) or like(b[u]) for u in us)}

    out = {"units": len(uids), "missing": missing, "invalid_type": bad,
           "type_agreement": round(sum(x == y for x, y in zip(ta, tb)) / len(uids), 3) if uids else None,
           "type_kappa": kappa(ta, tb),
           "prediction_like_agreement": round(sum(x == y for x, y in zip(la, lb)) / len(uids), 3) if uids else None,
           "prediction_like_kappa": kappa(la, lb),
           "dates_event_kappa": kappa([bool(a[u].get("time_dates_the_event")) for u in uids],
                                      [bool(b[u].get("time_dates_the_event")) for u in uids]),
           "all": share(lambda u: True),
           "by_kind": {k: share(lambda u, k=k: key[u]["kind"] == k) for k in sorted({key[u]["kind"] for u in uids})},
           "by_time_rule": {k: share(lambda u, k=k: key[u]["time_rule"] == k)
                            for k in sorted({key[u]["time_rule"] for u in uids})},
           "by_person": {k: share(lambda u, k=k: key[u]["person_id"] == k)
                         for k in sorted({key[u]["person_id"] for u in uids})},
           "types_a": dict(collections.Counter(ta).most_common()),
           "types_b": dict(collections.Counter(tb).most_common()),
           "disagree_prediction_like": [u for u, x, y in zip(uids, la, lb) if x != y]}
    out["both_prediction_like_wilson95"] = wilson(out["all"]["both_prediction_like"], out["all"]["units"])
    if strata:
        out["weighted_both_prediction_like"] = weighted_share(out["by_person"], strata)
        out["weighted_ci95"] = weighted_interval(out["by_person"], strata)
        out["weighted_over_candidates"] = sum(strata.get(p, 0) for p in out["by_person"])
        out["windowed_candidates"] = sum(strata.values())
    return out


SUMMARY_COLUMNS = ("sample", "purpose", "seed", "per_person", "excluded", "units", "people", "type_kappa",
                   "prediction_like_kappa", "dates_event_kappa", "coder_a_prediction_like", "coder_b_prediction_like",
                   "both_prediction_like", "share_both", "wilson95_lo", "wilson95_hi", "weighted_share",
                   "weighted95_lo", "weighted95_hi", "weighted_over_candidates", "windowed_candidates")


def summary_row(folder):
    """One row of counts (no text, no uids) for a sample folder: its meta.json, and the score of its two
    coders' labels recomputed with the current code."""
    folder = Path(folder)
    meta = json.loads((folder / "meta.json").read_text()) if (folder / "meta.json").exists() else {}
    strata = json.loads((folder / "strata.json").read_text()) if (folder / "strata.json").exists() else None
    res = score(read_jsonl(folder / "labels_a.jsonl"), read_jsonl(folder / "labels_b.jsonl"),
                read_jsonl(folder / "key.jsonl"), strata)
    al, wil, wci = res["all"], res["both_prediction_like_wilson95"] or [None, None], res.get("weighted_ci95") or [None, None]
    return {"sample": meta.get("name", folder.name), "purpose": meta.get("purpose", ""), "seed": meta.get("seed", ""),
            "per_person": meta.get("per_person", ""), "excluded": " ".join(meta.get("excluded", [])),
            "units": res["units"], "people": len(res["by_person"]), "type_kappa": res["type_kappa"],
            "prediction_like_kappa": res["prediction_like_kappa"], "dates_event_kappa": res["dates_event_kappa"],
            "coder_a_prediction_like": al["coder_a_prediction_like"], "coder_b_prediction_like": al["coder_b_prediction_like"],
            "both_prediction_like": al["both_prediction_like"],
            "share_both": round(al["both_prediction_like"] / res["units"], 3) if res["units"] else "",
            "wilson95_lo": wil[0], "wilson95_hi": wil[1], "weighted_share": res.get("weighted_both_prediction_like", ""),
            "weighted95_lo": wci[0], "weighted95_hi": wci[1],
            "weighted_over_candidates": res.get("weighted_over_candidates", ""),
            "windowed_candidates": res.get("windowed_candidates", "")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    add_root_arg(s)
    s.add_argument("--out", type=Path, required=True)
    s.add_argument("--per-person", type=int, default=8)
    s.add_argument("--seed", type=int, default=20261115)
    s.add_argument("--exclude", type=Path, action="append", default=[],
                   help="an earlier sample folder whose sentences must not be drawn again (repeatable)")
    s.add_argument("--purpose", default="", help='what the sample is for, e.g. "shapes rules" or "measures rules"')
    c = sub.add_parser("score")
    c.add_argument("--out", type=Path, required=True, help="the sample folder, which holds key.jsonl")
    c.add_argument("labels", nargs=2, type=Path)
    m = sub.add_parser("summary", help="one row of counts per sample folder, for plan/prediction_samples.csv")
    m.add_argument("--publish", type=Path, required=True, help="the CSV to write (counts only; it may be in the repository)")
    m.add_argument("folders", nargs="+", type=Path)
    args = ap.parse_args()
    if args.cmd == "summary":
        rows = [summary_row(f) for f in args.folders]
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=SUMMARY_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        atomic_write_text(args.publish, buf.getvalue())
        print(f"{len(rows)} samples -> {args.publish}")
        return
    out = ensure_outside_git(args.out)
    if args.cmd == "sample":
        rows = [r for f in sorted((Path(args.root) / "analysis" / "predictions").glob("*.jsonl")) for r in read_jsonl(f)]
        seen = [r["sentence"] for d in args.exclude for r in read_jsonl(Path(d) / "sample.jsonl")]
        picked = draw(rows, args.per_person, args.seed, seen)
        out.mkdir(parents=True, exist_ok=True)
        key, blind = [], []
        for i, r in enumerate(picked, 1):
            uid = f"u{i:03d}"
            key.append({"uid": uid, **{k: r.get(k) for k in ("person_id", "item_id", "kind", "date_said", "window_lo",
                                                             "window_hi", "time_rule", "time_expr")}})
            blind.append({"uid": uid, "sentence": r["sentence"], "time_expression": r["time_expr"]})
        atomic_write_text(out / "key.jsonl", "".join(json.dumps(k, ensure_ascii=False) + "\n" for k in key))
        atomic_write_text(out / "sample.jsonl", "".join(json.dumps(b, ensure_ascii=False) + "\n" for b in blind))
        strata = collections.Counter(r["person_id"] for r in rows
                                     if r.get("window_lo") is not None or r.get("window_hi") is not None)
        atomic_write_text(out / "strata.json", json.dumps(dict(sorted(strata.items())), indent=1))
        atomic_write_text(out / "meta.json", json.dumps({
            "name": out.name, "purpose": args.purpose, "seed": args.seed, "per_person": args.per_person,
            "excluded": [Path(d).name for d in args.exclude], "units": len(picked),
            "people": len({k["person_id"] for k in key})}, indent=1))
        print(f"{len(picked)} units from {len({k['person_id'] for k in key})} people -> {out}")
    else:
        strata = json.loads((out / "strata.json").read_text()) if (out / "strata.json").exists() else None
        res = score(read_jsonl(args.labels[0]), read_jsonl(args.labels[1]), read_jsonl(out / "key.jsonl"), strata)
        atomic_write_text(out / "score.json", json.dumps(res, indent=1))
        al = res["all"]
        print(f"{res['units']} units; type kappa {res['type_kappa']}, prediction-like kappa "
              f"{res['prediction_like_kappa']}; prediction-like: coder A {al['coder_a_prediction_like']}, "
              f"coder B {al['coder_b_prediction_like']}, both {al['both_prediction_like']}; weighted by person "
              f"{res.get('weighted_both_prediction_like')}")


if __name__ == "__main__":
    main()
