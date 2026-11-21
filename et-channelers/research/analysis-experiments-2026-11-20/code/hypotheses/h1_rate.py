"""H1. The claimed voice is delivered more slowly than the creator's own voice in the same recording.

Estimand (hypotheses.md): per creator, the mean over eligible recordings of log(rate in claimed-voice spans / rate in
own-voice spans); rate = estimated syllables per minute of span time, pauses inside the span included, the gap at the
boundary excluded; spans of at least 300 words each; own-voice spans exclude interviews until speakers are separated.
Pool: random effects, HKSJ with t(k-1) (A10.7 = CAL-A14), 95% interval and 95% prediction interval. Holm p: exact sign-flip of
creator means, one-sided (A10.1 = CAL-A8). Verdicts: slower if the upper 95% bound of the ratio is below 0.95; no slowing if
the 95% interval lies inside 0.95 to 1.05; otherwise not determined; "supported" also needs the 90% interval to exclude
zero (A5) and the Holm step. Minimum 12 creators with both voices. Negative control: own-voice recordings that pass from
a greeting to a main part. Secondaries (estimates only): embodied and relayed apart; the pause and articulation split.
Claimed voice is V2 plus V3 (registry 2026-11-21 02:55); relayed alone carries the flag "below the reliability floor" and
no verdict. A10 guard (registry 03:08): the registered version (DerSimonian-Laird pool, normal intervals) is computed
beside the amended one (HKSJ); see verdicts.py.
"""
import math

from . import common
from . import constants as K
from . import stats
from . import tipping
from . import voice_sets as vs

H = "H1"


def _qualifying(record, how):
    got = vs.sides(record, how)
    if got is None or record["format"] in K.H1_EXCLUDED_FORMATS:
        return None
    side_list, _ = got
    spans = [span for span in vs.spans(record, side_list) if span[3] >= K.H1_MIN_SPAN_WORDS]
    if not any(span[0] == "claimed" for span in spans) or not any(span[0] == "own" for span in spans):
        return None
    return spans


def eligible(bundle, how):
    """Labels only: creators with at least one recording holding a claimed and an own span of 300 words or more."""
    bundle = common.confirmatory(bundle)
    creators, recordings = set(), 0
    for item in bundle["recordings"]:
        if "voice" in item and _qualifying(item["voice"], how):
            creators.add(item["creator"])
            recordings += 1
    return common.eligibility(H, len(creators), recordings)


def _span_measure(record, features, span, measure):
    units = record["units"][span[1]:span[2] + 1]
    rows = [features["units"].get(unit["id"]) for unit in units]
    if any(row is None for row in rows):
        return None
    time = rows[-1]["end"] - rows[0]["start"]
    gaps = sum(max(0.0, b["start"] - a["end"]) for a, b in zip(rows, rows[1:]) if b["start"] - a["end"] >= K.H1_PAUSE_SECONDS)
    pauses = sum(row.get("pauses", 0.0) for row in rows) + gaps
    amount = sum(row[measure] for row in rows)
    return amount, time, max(time - pauses, 1e-9)


def recording_value(record, features, spans, measure="syllables"):
    """log rate ratio claimed to own, and its articulation part, for one recording."""
    totals = {"claimed": [0.0, 0.0, 0.0], "own": [0.0, 0.0, 0.0]}
    for span in spans:
        got = _span_measure(record, features, span, measure)
        if got is None:
            return None
        for i in range(3):
            totals[span[0]][i] += got[i]
    (ca, ct, cart), (oa, ot, oart) = totals["claimed"], totals["own"]
    if min(ca, ct, oa, ot) <= 0:
        return None
    value = math.log((ca / ct) / (oa / ot))
    articulation = math.log((ca / cart) / (oa / oart))
    return {"value": value, "articulation": articulation, "pause_part": value - articulation}


def creator_values(bundle, how, measure="syllables", key="value"):
    by_creator, missing = {}, 0
    for item in bundle["recordings"]:
        if "voice" not in item:
            continue
        spans = _qualifying(item["voice"], how)
        if not spans:
            continue
        if "features" not in item:
            missing += 1
            continue
        got = recording_value(item["voice"], item["features"], spans, measure)
        if got is None:
            missing += 1
            continue
        by_creator.setdefault(item["creator"], []).append(got[key])
    return by_creator, missing


def negative_control(bundle, how):
    """log(rate in the own-voice main part / rate in the greeting), in own-voice recordings (no claimed span) whose map
    gives the end of the opening: per creator, the mean over recordings."""
    by_creator = {}
    for item in bundle["recordings"]:
        record, features = item.get("voice"), item.get("features")
        if not record or not features or not record.get("opening_end_unit"):
            continue
        got = vs.sides(record, how)
        if got is None or record["format"] in K.H1_EXCLUDED_FORMATS:
            continue
        side_list, _ = got
        if "claimed" in side_list:
            continue
        cut = record["opening_end_unit"]
        stop = record.get("closing_start_unit") or (len(record["units"]) + 1)
        opening = [i for i, unit in enumerate(record["units"]) if unit["id"] <= cut and side_list[i] == "own"]
        main = [i for i, unit in enumerate(record["units"]) if cut < unit["id"] < stop and side_list[i] == "own"]
        words = lambda idx: sum(record["units"][i]["n_words"] for i in idx)
        if words(opening) < K.H1_NEG_MIN_OPENING_WORDS or words(main) < K.H1_NEG_MIN_MAIN_WORDS:
            continue
        rates = []
        for idx in (main, opening):
            rows = [features["units"].get(record["units"][i]["id"]) for i in idx]
            if any(row is None for row in rows):
                rates = None
                break
            time = sum(row["end"] - row["start"] for row in rows)
            rates.append(sum(row["syllables"] for row in rows) / time if time > 0 else None)
        if rates and all(rates):
            by_creator.setdefault(item["creator"], []).append(math.log(rates[0] / rates[1]))
    return {creator: sum(v) / len(v) for creator, v in by_creator.items()}


A10_REPLACES = ("interval: random-effects pool by DerSimonian-Laird with normal intervals (registered) -> HKSJ with "
                "t(k-1) (A10.7, CAL-A14 point 2)",)


def conditions(ci95, ci90):
    """The registered verdict conditions on a 95% and a 90% interval of the pooled log ratio."""
    upper_ratio, lower_ratio = math.exp(ci95[1]), math.exp(ci95[0])
    return {"registered": upper_ratio < K.H1_BAND[0], "a5": ci90[1] < 0, "effect_size": upper_ratio < K.H1_BAND[0],
            "refuted": "no slowing: the 95% interval of the ratio lies inside 0.95 to 1.05"
            if K.H1_BAND[0] <= lower_ratio and upper_ratio <= K.H1_BAND[1] else None}


def analyse(bundle, how=None, label=("H1",), extras=True, draws=K.BOOTSTRAP_DRAWS):
    bundle = common.confirmatory(bundle)
    how = how or vs.definition()
    elig = eligible(bundle, how)
    by_creator, missing = creator_values(bundle, how)
    creators = sorted(by_creator)
    values = [by_creator[c] for c in creators]
    out = {"hypothesis": H, "eligibility": elig, "missing_features": missing, "creators_with_values": len(creators)}
    if len(creators) < 2:
        out.update({"determinable": False, "p": 1.0, "estimate": None})
        return out
    res = common.pooled(values, label, "less")
    pool = res["pool"]
    mu, ci95, ci90, pi95 = pool["mu"], pool["intervals"]["0.95"], pool["intervals"]["0.9"], pool["prediction"]["0.95"]
    out.update({"determinable": elig["determinable"] and len(creators) >= K.MIN_CREATORS[H],
                "estimate": {"log_ratio": mu, "ratio": math.exp(mu), "tau2": pool["tau2"]},
                "intervals": {"hksj_95": ci95, "hksj_90": ci90, "prediction_95": pi95, "ratio_95": tuple(math.exp(v) for v in ci95),
                              "t90_creator_means": res["t90"][1:]},
                "p": res["p"], "p_method": res["p_method"], "alternative": "less",
                "positive_creators": res["positive_creators"], "creator_values": dict(zip(creators, res["creator_means"]))})
    out["conditions"] = conditions(ci95, ci90)
    out.update({"version": "amended", "creator_interval_90": ci90, "a10_replaces": list(A10_REPLACES)})
    # A10 guard (registry 03:08): the registered version pools by DerSimonian-Laird with normal intervals; the p (exact
    # sign-flip of creator means) and the minimum (12) are the same in both versions
    dl = res["pool_dl"]
    d95, d90 = dl["intervals"]["0.95"], dl["intervals"]["0.9"]
    out["registered_version"] = common.version(
        H, "registered", elig["creators"] >= K.REGISTERED_MIN_CREATORS[H] and len(creators) >= K.REGISTERED_MIN_CREATORS[H],
        res["p"], {"log_ratio": mu, "ratio": math.exp(mu), "tau2": dl["tau2"]},
        {"dl_95": d95, "dl_90": d90, "prediction_95": dl["prediction"]["0.95"], "ratio_95": tuple(math.exp(v) for v in d95)},
        conditions(d95, d90), d90, dict(elig, minimum=K.REGISTERED_MIN_CREATORS[H]), A10_REPLACES, res["p_method"])
    margin = (math.log(K.H1_BAND[0]) - ci95[1])
    out["tipping"] = {"attenuation": tipping.attenuation(mu, ci95[0], ci95[1]),
                      "selection": tipping.selection(margin),
                      "note": "selection: shift of the log ratio needed at each error share for the upper 95% bound to "
                              "cross log(0.95) (positive: the estimate would have to rise to lose 'slower')"}
    if not extras:
        return out
    sec = {}
    part, _ = creator_values(bundle, vs.embodied_only(how))
    sec["embodied only"] = dict(_summary(part, label + ("embodied only",)), note=K.EMBODIED_ONLY_NOTE, verdict=None)
    part, _ = creator_values(bundle, vs.relayed_only(how))
    sec["relayed only"] = vs.below_floor(_summary(part, label + ("relayed only",)))
    for name, measure in (("words per minute", "words"), ("letters per minute", "letters")):
        part, _ = creator_values(bundle, how, measure=measure)
        sec[name] = _summary(part, label + (name,))
    for name, key in (("articulation part", "articulation"), ("pause part", "pause_part")):
        part, _ = creator_values(bundle, how, key=key)
        sec[name] = _summary(part, label + (name,))
    control = negative_control(bundle, how)
    sec["negative control (greeting to own-voice main part)"] = _summary({c: [v] for c, v in control.items()}, label + ("neg",))
    both = sorted(set(control) & set(by_creator))
    diffs = [out["creator_values"][c] - control[c] for c in both]
    m, lo, hi = stats.t_interval(diffs) if len(diffs) >= 2 else (None, None, None)
    sec["claimed contrast minus negative control"] = {"creators": len(both), "mean": m, "t90": (lo, hi),
                                                       "rule": "if this interval includes zero the result is worded as slowing "
                                                               "between frame and main part (writer's addition)"}
    sec["two-stage bootstrap 90% (R1, sensitivity)"] = stats.two_stage_bootstrap(values, min(draws, 1999), label + ("two-stage",))
    sec["leave-one-creator-out range of the creator mean"] = common.loo_range(res["creator_means"], common.mean_or_none)
    out["secondary"] = sec
    return out


def _summary(by_creator, label):
    values = [by_creator[c] for c in sorted(by_creator)]
    if len(values) < 2:
        return {"creators": len(values)}
    res = common.pooled(values, label, "less")
    return {"creators": len(values), "log_ratio": res["pool"]["mu"], "hksj_95": res["pool"]["intervals"]["0.95"],
            "t90": res["t90"][1:], "signflip_p": res["p"]}
