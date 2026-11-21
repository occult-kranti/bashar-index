"""H4. Fewer contractible forms are contracted in the embodied claimed voice than in the own voice, by at least half a
between-creator standard deviation.

Estimand (hypotheses.md): within a recording, contraction share (contracted / (contracted + full) over H4's closed list)
in embodied first-person spans (V2) minus the own voice; the creator mean divided by the between-creator SD of own-voice
contraction share fixed on seen creators before the freeze (H4_YARDSTICK, FREEZE2; yardstick_from_seen computes it).
Reported as the standardised drop (own minus claimed, positive = fewer contractions in the claimed voice). Pool: random
effects, HKSJ, 95% interval and 95% prediction interval. Holm p: sign-flip of creator mean standardised drops, one-sided.
Supported: Holm step, 90% interval above zero (A5) and a pooled drop of at least 0.5 (the claim's size). Refuted: a 95%
interval below 0.5, or a prediction interval centred on zero (CHOICE: the 95% interval of the mean holds zero and the
prediction interval's half-width is at least 0.5). Relayed spans as an estimate. Negative control: contraction share in
fast against slow own-voice windows. Beside it: the shift in log(we / I) and in hedge rate.
Claimed side (registry 2026-11-21 04:55 (a)): H4's primary stays the embodied first-person voice (V2), as hypotheses.md
registers it; relayed units are on neither side. Every multiverse row and extra source of H4 uses V2. The merged claimed
voice of 02:55 (V2 + V3) is a secondary estimate without a verdict; relayed spans alone are an estimate "below the
reliability floor".
A10 guard (registry 03:08): the registered version pools by DerSimonian-Laird with normal intervals.
"""
import math

from . import common
from . import constants as K
from . import stats
from . import tipping
from . import voice_sets as vs

H = "H4"


def _side_counts(record, features, side_list, side):
    c = f = words = 0
    for unit, s in zip(record["units"], side_list):
        if s != side:
            continue
        row = features["units"].get(unit["id"]) if features else None
        if row is None:
            return None
        c, f, words = c + row["contracted"], f + row["full"], words + row["words"]
    return c, f, words


def _usable(record, how):
    got = vs.sides(record, how)
    if got is None:
        return None
    side_list, _ = got
    if "claimed" not in side_list or "own" not in side_list:
        return None
    return side_list


def eligible(bundle, how):
    """Labels only: creators with a recording that holds both voices (the form minimum needs the transcript and is
    counted as part of the outcome step)."""
    bundle = common.confirmatory(bundle)
    creators, recordings = set(), 0
    for item in bundle["recordings"]:
        if "voice" in item and _usable(item["voice"], how):
            creators.add(item["creator"])
            recordings += 1
    return common.eligibility(H, len(creators), recordings)


def recording_values(record, features, side_list):
    claimed = _side_counts(record, features, side_list, "claimed")
    own = _side_counts(record, features, side_list, "own")
    if claimed is None or own is None:
        return None
    if claimed[0] + claimed[1] < K.H4_MIN_FORMS_PER_SIDE or own[0] + own[1] < K.H4_MIN_FORMS_PER_SIDE:
        return None
    share_c = claimed[0] / (claimed[0] + claimed[1])
    share_o = own[0] / (own[0] + own[1])
    return {"drop": share_o - share_c, "share_claimed": share_c, "share_own": share_o}


def creator_drops(bundle, how, yardstick):
    by_creator, too_few = {}, 0
    for item in bundle["recordings"]:
        record = item.get("voice")
        if not record:
            continue
        side_list = _usable(record, how)
        if not side_list:
            continue
        got = recording_values(record, item.get("features"), side_list)
        if got is None:
            too_few += 1
            continue
        by_creator.setdefault(item["creator"], []).append(got["drop"] / yardstick)
    return by_creator, too_few


def yardstick_from_seen(bundle, how=None):
    """FREEZE2: SD between seen creators of own-voice contraction share (each creator: pooled counts over the own-voice
    units of its recordings). The owner's open point decides whether own voice comes from labels (this function) or from
    recordings titled as own-voice talks. The own side does not depend on the claimed side."""
    how = how or vs.primary_definition(H)
    counts = {}
    for item in bundle["recordings"]:
        record, features = item.get("voice"), item.get("features")
        if item.get("group") != "seen" or not record or not features:
            continue
        got = vs.sides(record, how)
        if got is None:
            continue
        own = _side_counts(record, features, got[0], "own")
        if own is None:
            continue
        total = counts.setdefault(item["creator"], [0, 0])
        total[0] += own[0]
        total[1] += own[1]
    shares = [c / (c + f) for c, f in (counts[k] for k in sorted(counts)) if c + f >= 4 * K.H4_MIN_FORMS_PER_SIDE]
    return stats.sd(shares), len(shares)


A10_REPLACES = ("interval: random-effects pool by DerSimonian-Laird with normal intervals and prediction interval "
                "(registered) -> HKSJ with t(k-1) (A10.7, CAL-A14 point 2)",)


def conditions(mu, ci95, ci90, pi95):
    """The registered verdict conditions on the pooled drop and its 95%, 90% and 95% prediction intervals."""
    centred = (pi95[0] is not None and ci95[0] <= 0 <= ci95[1] and (pi95[1] - pi95[0]) / 2 >= K.SESOI[H])
    refuted = None
    if ci95[1] < K.SESOI[H]:
        refuted = "the 95% interval of the standardised drop lies below 0.5"
    elif centred:
        refuted = "signs differ across creators: the prediction interval is centred on zero (CHOICE)"
    return {"registered": ci90[0] > 0, "a5": ci90[0] > 0, "effect_size": mu >= K.SESOI[H], "refuted": refuted}


def analyse(bundle, how=None, yardstick=None, label=("H4",), extras=True, draws=K.BOOTSTRAP_DRAWS):
    """how: the voice definition; its claimed side is the embodied voice V2 for the registered quantity (hypotheses.md;
    registry 2026-11-21 04:55 (a)); the merged V2 + V3 is a secondary estimate."""
    bundle = common.confirmatory(bundle)
    how = how or vs.primary_definition(H)
    yardstick = yardstick if yardstick is not None else K.H4_YARDSTICK
    if not yardstick:
        raise ValueError("H4 needs the yardstick (FREEZE2): yardstick_from_seen on seen labels, entered before freeze 2")
    elig = eligible(bundle, how)
    by_creator, too_few = creator_drops(bundle, how, yardstick)
    creators = sorted(by_creator)
    values = [by_creator[c] for c in creators]
    out = {"hypothesis": H, "eligibility": elig, "recordings_below_form_minimum": too_few, "creators_with_values": len(creators),
           "yardstick": yardstick}
    if len(creators) < 2:
        out.update({"determinable": False, "p": 1.0, "estimate": None})
        return out
    res = common.pooled(values, label, "greater")
    pool = res["pool"]
    mu, ci95, ci90, pi95 = pool["mu"], pool["intervals"]["0.95"], pool["intervals"]["0.9"], pool["prediction"]["0.95"]
    out.update({"determinable": elig["determinable"] and len(creators) >= K.MIN_CREATORS[H],
                "estimate": {"standardised_drop": mu, "tau2": pool["tau2"]},
                "intervals": {"hksj_95": ci95, "hksj_90": ci90, "prediction_95": pi95, "t90_creator_means": res["t90"][1:]},
                "p": res["p"], "p_method": res["p_method"], "alternative": "greater",
                "positive_creators": res["positive_creators"], "creator_values": dict(zip(creators, res["creator_means"]))})
    out["conditions"] = conditions(mu, ci95, ci90, pi95)
    out.update({"version": "amended", "creator_interval_90": ci90, "a10_replaces": list(A10_REPLACES)})
    dl = res["pool_dl"]
    d95, d90, dp95 = dl["intervals"]["0.95"], dl["intervals"]["0.9"], dl["prediction"]["0.95"]
    out["registered_version"] = common.version(
        H, "registered", elig["creators"] >= K.REGISTERED_MIN_CREATORS[H] and len(creators) >= K.REGISTERED_MIN_CREATORS[H],
        res["p"], {"standardised_drop": mu, "tau2": dl["tau2"]}, {"dl_95": d95, "dl_90": d90, "prediction_95": dp95},
        conditions(mu, d95, d90, dp95), d90, dict(elig, minimum=K.REGISTERED_MIN_CREATORS[H]), A10_REPLACES, res["p_method"])
    out["tipping"] = {"attenuation": tipping.attenuation(mu, ci95[0], ci95[1]),
                      "selection": tipping.selection(K.SESOI[H] - mu),
                      "note": "selection: shift of the standardised drop needed at each error share for the estimate to "
                              "cross 0.5"}
    if not extras:
        return out
    sec = {}
    part, _ = creator_drops(bundle, vs.relayed_only(how), yardstick)
    sec["relayed spans (estimate)"] = vs.below_floor(_summary(part, label + ("relayed",)))
    part, _ = creator_drops(bundle, vs.merged_claimed(how), yardstick)
    sec["claimed voice V2 + V3 (merged, registry 02:55; secondary, no verdict)"] = dict(
        _summary(part, label + ("merged",)), note=K.MERGED_CLAIMED_NOTE, verdict=None)
    sec["negative control: fast minus slow own-voice windows (standardised)"] = _summary(
        {c: v for c, v in tempo_control(bundle, how, yardstick).items()}, label + ("tempo",))
    sec["shift in log(we / I), claimed minus own"] = _summary(_feature_shift(bundle, how, "pronouns"), label + ("pron",))
    sec["shift in hedges per 1,000 words, claimed minus own"] = _summary(_feature_shift(bundle, how, "hedges"), label + ("hedge",))
    sec["two-stage bootstrap 90% (R1, sensitivity)"] = stats.two_stage_bootstrap(values, min(draws, 1999), label + ("two-stage",))
    sec["leave-one-creator-out range of the creator mean"] = common.loo_range(res["creator_means"], common.mean_or_none)
    out["secondary"] = sec
    return out


def tempo_control(bundle, how, yardstick):
    """Own-voice windows of about H4_WINDOW_WORDS words; per recording, contraction share in the faster half of its
    windows minus the slower half (split at the recording's median syllable rate); per creator the mean, standardised."""
    by_creator = {}
    for item in bundle["recordings"]:
        record, features = item.get("voice"), item.get("features")
        if not record or not features:
            continue
        got = vs.sides(record, how)
        if got is None:
            continue
        windows, current = [], []
        for unit, side in zip(record["units"], got[0]):
            row = features["units"].get(unit["id"])
            if side != "own" or row is None:
                current = []
                continue
            current.append(row)
            if sum(r["words"] for r in current) >= K.H4_WINDOW_WORDS:
                windows.append(current)
                current = []
        if len(windows) < 4:
            continue
        rated = []
        for rows in windows:
            time = sum(r["end"] - r["start"] for r in rows)
            if time > 0:
                rated.append((sum(r["syllables"] for r in rows) / time, sum(r["contracted"] for r in rows), sum(r["full"] for r in rows)))
        rated.sort()
        half = len(rated) // 2
        slow, fast = rated[:half], rated[len(rated) - half:]
        cs, fs = sum(r[1] for r in slow), sum(r[2] for r in slow)
        cf, ff = sum(r[1] for r in fast), sum(r[2] for r in fast)
        if cs + fs < K.H4_MIN_FORMS_PER_SIDE or cf + ff < K.H4_MIN_FORMS_PER_SIDE:
            continue
        by_creator.setdefault(item["creator"], []).append((cf / (cf + ff) - cs / (cs + fs)) / yardstick)
    return by_creator


def _feature_shift(bundle, how, which):
    by_creator = {}
    for item in bundle["recordings"]:
        record, features = item.get("voice"), item.get("features")
        if not record or not features:
            continue
        side_list = _usable(record, how)
        if not side_list:
            continue
        sums = {"claimed": [0, 0, 0, 0], "own": [0, 0, 0, 0]}
        for unit, side in zip(record["units"], side_list):
            row = features["units"].get(unit["id"])
            if side and row:
                for i, key in enumerate(("fp_plur", "fp_sing", "hedges", "words")):
                    sums[side][i] += row.get(key, 0)
        c, o = sums["claimed"], sums["own"]
        if which == "pronouns":
            value = math.log((c[0] + 0.5) / (c[1] + 0.5)) - math.log((o[0] + 0.5) / (o[1] + 0.5))
        else:
            if not c[3] or not o[3]:
                continue
            value = 1000.0 * (c[2] / c[3] - o[2] / o[3])
        by_creator.setdefault(item["creator"], []).append(value)
    return by_creator


def _summary(by_creator, label):
    values = [by_creator[c] for c in sorted(by_creator)]
    if len(values) < 2:
        return {"creators": len(values)}
    res = common.pooled(values, label, "greater")
    return {"creators": len(values), "estimate": res["pool"]["mu"], "hksj_95": res["pool"]["intervals"]["0.95"],
            "t90": res["t90"][1:], "signflip_p": res["p"]}
