#!/usr/bin/env python3
"""A pilot of the model pass over the prediction candidates (ANALYSIS_PLAN 12.4 and 12.5): a blinded sample for
independent coders, and the scores of their labels.

    python3 -I pipeline/prediction_pilot.py sample --root ~/et-channelers-private --out <dir> --per-person 8
    python3 -I pipeline/prediction_pilot.py sample --root ~/et-channelers-private --out <new dir> --seed 2 \
        --exclude <earlier dir>                                  (a fresh sample, to measure rules the first one shaped)
    python3 -I pipeline/prediction_pilot.py score  --out <dir> labels_a.jsonl labels_b.jsonl

`sample` draws, with a fixed seed, up to --per-person candidates that have a target window from each person's
`analysis/predictions/<person>.jsonl`, shuffles them and writes `sample.jsonl` (uid, sentence, time expression:
no person, title, item or date, as 12.5 asks) and `key.jsonl` (what the coders must not see). `score` reads two
coders' labels and the key and writes `score.json`: agreement and Cohen's kappa on the type and on "prediction
like", and the share of candidates each coder and both coders call prediction-like (the rules pass's precision),
by kind (texts from the source apart from speech-to-text), by time rule and by person, and, from the
`strata.json` that `sample` writes, the share weighted by each person's windowed candidates. Everything stays private; score.json
holds counts and uids only, no text.
"""
from __future__ import annotations

import argparse
import collections
import json
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
    if strata:
        out["weighted_both_prediction_like"] = weighted_share(out["by_person"], strata)
        out["weighted_over_candidates"] = sum(strata.get(p, 0) for p in out["by_person"])
    return out


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
    c = sub.add_parser("score")
    c.add_argument("--out", type=Path, required=True, help="the sample folder, which holds key.jsonl")
    c.add_argument("labels", nargs=2, type=Path)
    args = ap.parse_args()
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
