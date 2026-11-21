"""H5. World claims sit in the claimed voice, practice in the speaker's own.

Measure: the sentence-code route the registry allows ("a sentence sample coded as world claim against practice
instruction"; protocol section 5). For creator c and side s (A: titled as channelled or relayed; B: solo own-voice talks;
title rule of protocol section 3; guided practice, promotions and interviews excluded by title kind cues and by the voice
map's main kind), W = coded points in the world-claim codes, P = points in the practice-and-feeling codes, with
multiplicity; a recording coded whole (weights are words) is rescaled to its k points.
Amendment A10.4 (CAL-A11), applied in the amended version: Holm p is a one-sided sign-flip over creators of
OE = W_A / T_A - (W_A + W_B) / (T_A + T_B), T = W + P; the estimate is the Mantel-Haenszel odds ratio across creators;
the minimum is moved from 10 hits per group and side to 10 per group (T_A >= 10 and T_B >= 10). Until the coverage
repeat (CAL part f) the MH estimate carries the wider of the creator-bootstrap percentile interval and the t interval
(log OR +- t(k-1) x the delete-one-creator jackknife SE; constants.MH_INTERVAL_RULE, registry 2026-11-21 04:55 (j)).
A5 holds only if both the t interval on the creator OE values and that MH interval exclude zero above it (registry
2026-11-21 06:44 (5)). In the recognizer-model-stratified row the strata are creator by model (06:44 (9)): OE is centred
within each model, the MH odds ratio has one stratum per creator and model, and no side contrast mixes models.
The registered version (A10 guard, registry 03:08): the half-count difference of log ratios with the per-side rule,
pooled by DerSimonian-Laird, sign-flip over creators with 9,999 draws, and the registered creator-bootstrap interval,
drawn as catalogue rule R1 says (creators, then each creator's recordings within each side; registry 04:55 (d)).
A10.7 point 2 (registry 04:55 (c)): the random-effects sensitivity row, the same half-count estimator pooled by HKSJ
with t(k-1), is a secondary estimate without a verdict.
Unit: creator with at least 2 recordings on each side; not run below 12 creators. Smallest effect 0.4 log units. Refuted
by a 90% interval inside -0.4 to +0.4, or a negative difference whose interval excludes zero.

Revisions before freeze 1 (registry, lead's decision of 2026-11-21 02:50, meta-review M9):
  * units next to a self-naming cue are excluded from both sides: the unit that holds a self-introduction of a claimed
    source (a self_name cue unit of the voice label of record) and the unit after it (voice_sets.self_naming_units;
    where a voice file carries no cue, the feature files' pattern flags; a recording with neither is counted);
  * three Q2 assignments are reported as rows: as registered (the primary), merged with Q1, excluded
    (constants.H5_Q2_ASSIGNMENTS).
"""
import math

from . import common
from . import constants as K
from . import stats
from . import tipping
from . import voice_sets as vs

H = "H5"
A10_REPLACES = ("estimator: half-count difference of log ratios pooled by random effects (registered) -> OE for the Holm p "
                "and the Mantel-Haenszel odds ratio as the estimate (A10.4, CAL-A11)",
                "reference: sign-flip of half-count values, 9,999 draws (registered) -> sign-flip of OE, exact up to 20 creators "
                "(A10.1, A10.4)",
                "minimum: 10 hits per group and side (registered) -> 10 per group, the margin only (A10.4)",
                "interval: creator bootstrap (creators, then recordings, R1) of the pooled half-count estimate (registered) -> "
                "for A5 both the t interval on OE and the MH log odds ratio's interval, the wider of the creator-bootstrap "
                "percentile and the jackknife t interval until the coverage repeat (A10.7; registry 04:55 (j), 06:44 (5))")


def title_side(title):
    if title is None:
        return None
    if any(cue in K.H5_EXCLUDED_KIND_CUES for cue in title["kind_cues"]):
        return None
    if title["presentation"] == "P1" and title["voiced_by"] == "C" and title["cues"] and title["cues"] != ["NONLANGUAGE"]:
        return "A"
    if title["presentation"] in ("P0", "P2"):
        return "B"
    return None


def recording_side(item, titles):
    title = titles.get(item.get("video_id")) if item.get("video_id") else None
    side = title_side(title)
    voice = item.get("voice")
    if side is None or "content" not in item:
        return None
    if voice:
        if voice["language"] != "en" or voice["main_kind"] in K.H5_EXCLUDED_MAIN_KINDS:
            return None
        if side == "B" and voice["format"] not in K.H5_SOLO_FORMATS:
            return None
    return side


def self_naming_excluded(item):
    """(unit ids to exclude, source): the self-naming units and the unit after each, from the voice label of record's
    cues, else from the feature files' pattern flags (features.py), else (empty, "none")."""
    voice = item.get("voice")
    if voice:
        units = vs.self_naming_units(voice)
        if units is not None:
            return set(units), "voice cues"
    features = item.get("features")
    if features and any("self_name" in row for row in features["units"].values()):
        flagged = [uid for uid, row in features["units"].items() if row.get("self_name")]
        return {uid + step for uid in flagged for step in range(K.H5_SELF_NAMING_UNITS_AFTER + 1)}, "feature patterns"
    return set(), "none"


def _counts(item, groups, k, secondary_half, drop_codes=(), excluded=frozenset()):
    """(W, P, excluded points) of one recording. excluded: unit ids left out (self-naming); drop_codes: a unit whose
    primary or secondary code is one of them is left out (the Q2-excluded row). A recording coded whole is rescaled to k
    points over the units that remain."""
    world, practice = groups
    content = item["content"]
    weights = {uid: unit["weight"] for uid, unit in content["units"].items()}
    total_all = sum(weights.values())
    mode = content.get("mode")
    if mode is None and item.get("voice"):
        words = {unit["id"]: unit["n_words"] for unit in item["voice"]["units"]}
        if weights and all(words.get(uid) == w for uid, w in weights.items()) and total_all > 1.5 * k:
            mode = "whole"
    keep = [uid for uid in sorted(content["units"]) if uid not in excluded
            and not (drop_codes and (content["units"][uid]["primary"] in drop_codes or content["units"][uid].get("secondary") in drop_codes))]
    left_out = sum(weights[uid] for uid in content["units"] if uid in excluded)
    total = sum(weights[uid] for uid in keep)
    factor = (k / total) if mode == "whole" and total > 0 else 1.0
    w = p = 0.0
    for uid in keep:
        unit = content["units"][uid]
        weight = unit["weight"] * factor
        codes = [(unit["primary"], 1.0)]
        if secondary_half and unit.get("secondary") not in (None, "NONE", unit["primary"]):
            codes = [(unit["primary"], 0.5), (unit["secondary"], 0.5)]
        for code, share in codes:
            if code in world:
                w += weight * share
            elif code in practice:
                p += weight * share
    return w, p, (left_out * (k / total_all) if mode == "whole" and total_all > 0 else left_out)


def creator_tables(bundle, title_source="final", groups_name="primary", secondary_half=False, drop_codes=(), self_naming=True,
                   tally=None):
    """{creator: {WA, PA, WB, PB, recordings, per_recording, strata}} of the creators with 2 recordings on each side
    (per_recording: {"A": [(W, P) of each channelled recording], "B": [...]}; strata: one {stratum, WA, PA, WB, PB, "A":
    [(W, P)], "B": [(W, P)]} per recognizer model in which the creator has both sides, what the two-stage bootstrap
    resamples). tally (a dict) receives the self-naming exclusion counts (recordings by cue source, units and points left
    out). In the recognizer-model-stratified view (registry 03:08) only the models in which the creator has recordings on
    both sides contribute, and each is a stratum of its own (creator by model, registry 2026-11-21 06:44 (9)): OE is
    centred within each stratum, the MH odds ratio has a stratum per creator and model, and the registered half-count
    value pools the strata, so no side contrast mixes models. Outside that view a creator has one stratum and every value
    is the one of before."""
    titles = (bundle.get("titles") or {}).get(title_source) or {}
    groups = K.H5_GROUPS[groups_name]
    by_creator = {}
    for item in bundle["recordings"]:
        side = recording_side(item, titles)
        if side:
            strata = by_creator.setdefault(item["creator"], {})
            strata.setdefault(common.stratum(bundle, item), {"A": [], "B": []})[side].append(item)
    tables = {}
    for creator in sorted(by_creator):
        kept = [(key, by_creator[creator][key]) for key in sorted(by_creator[creator], key=lambda value: "" if value is None else str(value))
                if by_creator[creator][key]["A"] and by_creator[creator][key]["B"]]
        sizes = {side: sum(len(sides[side]) for _, sides in kept) for side in ("A", "B")}
        if sizes["A"] < K.H5_MIN_RECORDINGS_PER_SIDE or sizes["B"] < K.H5_MIN_RECORDINGS_PER_SIDE:
            continue
        row = {"per_recording": {"A": [], "B": []}, "strata": []}
        for key, stratum_sides in kept:
            cell = {"stratum": key, "A": [], "B": []}
            for side in ("A", "B"):
                k = max(40, math.ceil(120 / sizes[side]))
                w = p = 0.0
                for item in stratum_sides[side]:
                    excluded, source = self_naming_excluded(item) if self_naming else (set(), "not applied")
                    dw, dp, left_out = _counts(item, groups, k, secondary_half, drop_codes, excluded)
                    w, p = w + dw, p + dp
                    cell[side].append((dw, dp))
                    row["per_recording"][side].append((dw, dp))
                    if tally is not None:
                        tally.setdefault("recordings_by_cue_source", {})[source] = tally.setdefault("recordings_by_cue_source", {}).get(source, 0) + 1
                        tally["units_left_out"] = tally.get("units_left_out", 0) + len(excluded & set(item["content"]["units"]))
                        tally["points_left_out_" + side] = tally.get("points_left_out_" + side, 0.0) + left_out
                cell["W" + side], cell["P" + side] = w, p
            row["strata"].append(cell)
        for key in ("WA", "PA", "WB", "PB"):
            row[key] = sum(cell[key] for cell in row["strata"])
        row["recordings"] = sizes["A"] + sizes["B"]
        tables[creator] = row
    return tables


def _strata(row):
    """The creator-by-model strata of a creator row (one stratum, the row itself, outside the model-stratified view)."""
    return row.get("strata") or [row]


def _passes(row, minimum, per_side):
    if per_side:
        return min(row["WA"], row["PA"], row["WB"], row["PB"]) >= minimum
    return row["WA"] + row["PA"] >= minimum and row["WB"] + row["PB"] >= minimum


def eligible(bundle, title_source="final", minimum=K.H5_MIN_HITS_PER_GROUP, per_side=False, groups_name="primary", drop_codes=(),
             self_naming=True, secondary_half=False):
    """Labels only: creators with 2 recordings on each side, then those that pass the hit rule (counted before any
    share is compared)."""
    bundle = common.confirmatory(bundle)
    tally = {}
    tables = creator_tables(bundle, title_source, groups_name, secondary_half, drop_codes, self_naming, tally)
    passing = [c for c, row in tables.items() if _passes(row, minimum, per_side)]
    out = common.eligibility(H, len(passing), sum(tables[c]["recordings"] for c in passing),
                             {"creators_two_recordings_each_side": len(tables), "hit_rule": "per side" if per_side else "per group",
                              "hit_minimum": minimum, "self_naming_exclusion": tally if self_naming else "not applied"})
    return out


def oe(row):
    """CAL-A11's OE = W_A / T_A - (W_A + W_B) / (T_A + T_B). With several creator-by-model strata (the model-stratified
    view, registry 2026-11-21 06:44 (9)) it is centred within each stratum m: (W_A - sum_m T_A,m (W_m / T_m)) / T_A, the
    same value when there is one stratum."""
    strata = _strata(row)
    if len(strata) == 1:
        ta, tb = row["WA"] + row["PA"], row["WB"] + row["PB"]
        return row["WA"] / ta - (row["WA"] + row["WB"]) / (ta + tb)
    expected = 0.0
    for cell in strata:
        side_a, total = cell["WA"] + cell["PA"], cell["WA"] + cell["PA"] + cell["WB"] + cell["PB"]
        if total > 0:
            expected += side_a * (cell["WA"] + cell["WB"]) / total
    return (row["WA"] - expected) / (row["WA"] + row["PA"])


def mh_log_or(rows):
    """The MH log odds ratio with one stratum per creator (per creator and model in the model-stratified view)."""
    ratio, _ = stats.mh_odds_ratio([(c["WA"], c["PA"], c["WB"], c["PB"]) for r in rows for c in _strata(r)])
    return math.log(ratio) if ratio else None


def refutation(estimate, lo, hi):
    if lo is not None and -K.SESOI[H] < lo and hi < K.SESOI[H]:
        return "no division of labour: the 90% interval lies inside -0.4 to +0.4"
    if estimate is not None and estimate < 0 and hi is not None and hi < 0:
        return "a negative difference whose 90% interval excludes zero"
    return None


def _half_count_one(r):
    return math.log((r["WA"] + 0.5) / (r["PA"] + 0.5)) - math.log((r["WB"] + 0.5) / (r["PB"] + 0.5))


def _half_count_variance_one(r):
    return 1 / (r["WA"] + 0.5) + 1 / (r["PA"] + 0.5) + 1 / (r["WB"] + 0.5) + 1 / (r["PB"] + 0.5)


def half_count_value(r):
    """The registered creator value: the half-count difference of log ratios. With several creator-by-model strata (the
    model-stratified view, registry 2026-11-21 06:44 (9); CHOICE) the inverse-variance weighted mean of the strata's
    values, so that no side contrast mixes models; with one stratum the value of before."""
    strata = _strata(r)
    if len(strata) == 1:
        return _half_count_one(r)
    weights = [1 / _half_count_variance_one(cell) for cell in strata]
    return sum(w * _half_count_one(cell) for w, cell in zip(weights, strata)) / sum(weights)


def half_count_variance(r):
    strata = _strata(r)
    if len(strata) == 1:
        return _half_count_variance_one(r)
    return 1 / sum(1 / _half_count_variance_one(cell) for cell in strata)


def _dl_mu(pairs):
    pool = stats.re_dl([a for a, _ in pairs], [b for _, b in pairs])
    return pool["mu"] if pool else None


def _resample_sides(row, stream):
    """R1's second stage for H5: a creator's channelled recordings drawn among its channelled ones, its own-voice talks
    among its own-voice talks; with several creator-by-model strata, within each stratum (06:44 (9))."""
    strata = row.get("strata") or []
    if len(strata) <= 1:
        return {side: stats.resample_list(row["per_recording"][side], stream) for side in ("A", "B")}
    return {"strata": [{side: stats.resample_list(cell[side], stream) for side in ("A", "B")} for cell in strata]}


def _drawn_row(sides):
    return {"WA": sum(w for w, _ in sides["A"]), "PA": sum(p for _, p in sides["A"]),
            "WB": sum(w for w, _ in sides["B"]), "PB": sum(p for _, p in sides["B"])}


def _two_stage_half_count_mu(sample):
    """The registered statistic in one two-stage draw: the DerSimonian-Laird pool of the drawn creators' half-count values."""
    pairs = []
    for sides in sample:
        if "strata" in sides:
            cells = [_drawn_row(cell) for cell in sides["strata"]]
            row = dict({key: sum(cell[key] for cell in cells) for key in ("WA", "PA", "WB", "PB")}, strata=cells)
        else:
            row = _drawn_row(sides)
        pairs.append((half_count_value(row), half_count_variance(row)))
    return _dl_mu(pairs)


def registered_rows(tables, minimum=K.H5_MIN_HITS_PER_GROUP):
    """The creators of the registered hit rule (10 per group and side) and their tables."""
    creators = [c for c in sorted(tables) if _passes(tables[c], minimum, True)]
    return creators, [tables[c] for c in creators]


def registered_version(tables, label, draws, minimum=K.H5_MIN_HITS_PER_GROUP):
    """hypotheses.md as registered: per creator log(world / practice) in the channelled recordings minus the same in the
    own-voice talks, half-count correction, 10 hits per group and side; pooled by random effects (DerSimonian-Laird);
    sign-flip over creators (9,999 draws); creator-bootstrap interval, drawn as catalogue rule R1 says: creators, then
    recordings within each creator's sides (registry 2026-11-21 04:55 (d))."""
    creators, rows = registered_rows(tables, minimum)
    elig = common.eligibility(H, len(creators), sum(r["recordings"] for r in rows), {"hit_rule": "per side", "hit_minimum": minimum},
                              minimum=K.REGISTERED_MIN_CREATORS[H])
    if len(rows) < 2:
        return common.version(H, "registered", False, 1.0, None, None, None, (None, None), elig, A10_REPLACES), {}
    y, v = [half_count_value(r) for r in rows], [half_count_variance(r) for r in rows]
    pool = stats.re_dl(y, v)
    p, method = stats.signflip_p(y, "greater", label=label + ("registered",), exact_max=0, draws=K.REGISTERED_SIGNFLIP_DRAWS)
    lo, hi, failed = stats.bootstrap_two_stage(rows, _two_stage_half_count_mu, draws, label + ("registered", "two-stage"),
                                               K.A5_LEVEL, resample=_resample_sides)
    mu = pool["mu"]
    cond = {"registered": mu > 0, "a5": lo is not None and lo > 0, "effect_size": True, "refuted": refutation(mu, lo, hi)}
    return (common.version(H, "registered", elig["determinable"], p, {"half_count_log_ratio_difference": mu, "tau2": pool["tau2"]},
                           {"bootstrap_90": (lo, hi), "bootstrap": "creators, then recordings (R1)", "bootstrap_failed_draws": failed,
                            "dl_90": pool["intervals"]["0.9"]},
                           cond, (lo, hi), elig, A10_REPLACES, method),
            dict(zip(creators, y)))


def random_effects_row(tables, label, minimum=K.H5_MIN_HITS_PER_GROUP):
    """A10.7 point 2 (registry 2026-11-21 04:55 (c)): H5's random-effects sensitivity row, the registered half-count
    estimator (10 hits per group and side) pooled by Hartung-Knapp-Sidik-Jonkman with t(k-1), with its prediction
    interval and the creator sign-flip of A10.1 (exact up to 20 creators). An estimate without a verdict; the registered
    version under the guard keeps DerSimonian-Laird."""
    creators, rows = registered_rows(tables, minimum)
    out = {"creators": len(creators), "estimator": "half-count difference of log ratios, 10 hits per group and side",
           "pool": "HKSJ with t(k-1) (A10.7 point 2)", "verdict": None,
           "note": "sensitivity row of A10.7 point 2; the registered version of the A10 guard keeps DerSimonian-Laird"}
    if len(rows) < 2:
        return out
    y, v = [half_count_value(r) for r in rows], [half_count_variance(r) for r in rows]
    pool = stats.re_hksj(y, v)
    p, method = stats.signflip_p(y, "greater", label=label + ("re-hksj",))
    out.update({"mu": pool["mu"], "tau2": pool["tau2"], "hksj_90": pool["intervals"]["0.9"], "hksj_95": pool["intervals"]["0.95"],
                "prediction_95": pool["prediction"]["0.95"], "signflip_p": p, "p_method": method})
    return out


def analyse(bundle, title_source="final", groups_name="primary", minimum=K.H5_MIN_HITS_PER_GROUP, per_side=False,
            secondary_half=False, drop_codes=(), self_naming=True, label=("H5",), extras=True, draws=K.BOOTSTRAP_DRAWS):
    bundle = common.confirmatory(bundle)
    drop_codes = tuple(drop_codes or ())
    tally = {}
    tables = creator_tables(bundle, title_source, groups_name, secondary_half, drop_codes, self_naming, tally)
    creators = [c for c in sorted(tables) if _passes(tables[c], minimum, per_side)]
    rows = [tables[c] for c in creators]
    elig = common.eligibility(H, len(creators), sum(r["recordings"] for r in rows),
                              {"creators_two_recordings_each_side": len(tables), "hit_minimum": minimum,
                               "hit_rule": "per side" if per_side else "per group",
                               "self_naming_exclusion": tally if self_naming else "not applied"})
    out = {"hypothesis": H, "eligibility": elig, "title_source": title_source, "groups": groups_name, "drop_codes": list(drop_codes),
           "version": "amended", "a10_replaces": list(A10_REPLACES)}
    out["registered_version"], out["registered_creator_values"] = registered_version(tables, label, draws, minimum)
    if len(rows) < 2:
        out.update({"determinable": False, "p": 1.0, "estimate": None, "creator_interval_90": (None, None)})
        return out
    values = [oe(r) for r in rows]
    p, method = stats.signflip_p(values, "greater", label=label + ("signflip",))
    m, lo, hi = stats.t_interval(values)
    log_or = mh_log_or(rows)
    blo, bhi, failed = stats.bootstrap_creators(rows, mh_log_or, draws, label + ("boot",), K.A5_LEVEL)
    blo95, bhi95, _ = stats.bootstrap_creators(rows, mh_log_or, draws, label + ("boot95",), 0.95)
    # registry 04:55 (j): the MH estimate carries the wider of the bootstrap percentile and the t interval
    t90, t95 = stats.jackknife_t_interval(rows, mh_log_or, K.A5_LEVEL), stats.jackknife_t_interval(rows, mh_log_or, 0.95)
    mh90, mh95 = stats.mh_interval((blo, bhi), t90), stats.mh_interval((blo95, bhi95), t95)
    _, var = stats.mh_odds_ratio([(c["WA"], c["PA"], c["WB"], c["PB"]) for r in rows for c in _strata(r)])
    out.update({"determinable": elig["determinable"],
                "estimate": {"mh_log_odds_ratio": log_or, "mean_OE": m},
                "intervals": {"t90_OE": (lo, hi), "mh_90_log_or": mh90, "mh_95_log_or": mh95, "mh_interval_rule": K.MH_INTERVAL_RULE,
                              "bootstrap_90_log_or": (blo, bhi), "bootstrap_95_log_or": (blo95, bhi95),
                              "jackknife_t90_log_or": t90, "jackknife_t95_log_or": t95,
                              "rbg_90_log_or": (log_or - stats.z_ppf(0.95) * math.sqrt(var), log_or + stats.z_ppf(0.95) * math.sqrt(var)) if var and log_or is not None else (None, None),
                              "bootstrap_failed_draws": failed},
                "p": p, "p_method": method, "alternative": "greater", "creator_values": dict(zip(creators, values)),
                "creator_interval_90": mh90})
    # registry 2026-11-21 06:44 (5): A5 holds only if the t interval on the creator OE values and the MH interval both
    # exclude zero on the predicted side (above)
    a5_oe, a5_mh = lo is not None and lo > 0, mh90[0] is not None and mh90[0] > 0
    out["conditions"] = {"registered": log_or is not None and log_or > 0, "a5": a5_oe and a5_mh,
                         "a5_parts": {"t90_OE_above_zero": a5_oe, "mh_90_log_or_above_zero": a5_mh}, "effect_size": True,
                         "refuted": refutation(log_or, mh90[0], mh90[1])}
    pooled = {k: sum(r[k] for r in rows) for k in ("WA", "PA", "WB", "PB")}
    out["tipping"] = {"counts": tipping.odds_ratio(pooled["WA"], pooled["PA"], pooled["WB"], pooled["PB"], (1.0, math.exp(K.SESOI[H]))),
                      "note": "pooled raw table (point equivalents) of the eligible creators"}
    if not extras:
        return out
    sec = {}
    reg = out["registered_version"]
    sec["registered half-count difference of log ratios, 10 hits per group and side (the registered version of the A10 guard)"] = {
        "creators": reg["eligibility"]["creators"], "dl_mean": (reg["estimate"] or {}).get("half_count_log_ratio_difference"),
        "bootstrap_90": (reg["intervals"] or {}).get("bootstrap_90"), "signflip_p": reg["p"]}
    sec["random-effects sensitivity row: half-count estimator pooled by HKSJ (A10.7 point 2)"] = random_effects_row(
        tables, label, minimum)
    sec["leave-one-creator-out range of the MH log odds ratio"] = common.loo_range(rows, mh_log_or)
    if groups_name == "primary" and not drop_codes and title_source == "final" and minimum == K.H5_MIN_HITS_PER_GROUP \
            and not per_side and not secondary_half and self_naming:
        sec["Q2 assignments (M9)"] = q2_assignments(bundle, label, draws, out)
    out["secondary"] = sec
    return out


def q2_assignments(bundle, label, draws, primary):
    """The three Q2 assignments side by side (registry 02:50): as registered (the primary result), merged with Q1,
    excluded. Each is also a multiverse row with its own verdict (rows)."""
    out = {}
    for name, options in K.H5_Q2_ASSIGNMENTS.items():
        result = primary if name == "as registered" else analyse(bundle, label=label + ("q2", name), extras=False,
                                                                 draws=min(draws, 1999), **options)
        out[name] = {"eligible_creators": result["eligibility"]["creators"], "estimate": result.get("estimate"),
                     "p": result.get("p"), "t90_OE": (result.get("intervals") or {}).get("t90_OE"),
                     "mh_90_log_or": (result.get("intervals") or {}).get("mh_90_log_or"),
                     "bootstrap_90_log_or": (result.get("intervals") or {}).get("bootstrap_90_log_or"),
                     "options": {key: list(value) if isinstance(value, tuple) else value for key, value in options.items()}}
    return out


def rows(bundle_has_titles=("final", "middle", "small")):
    """Multiverse rows of H5 beside the primary (protocol section 5, the plan's model rows, and M9's Q2 assignments)."""
    out = [("primary", {}),
           ("Q2 merged with Q1 (sensitivity A: world = Q1 + Q2)", {"groups_name": "sensitivity_A"}),
           ("Q2 excluded (units coded Q2 left out)", {"drop_codes": ["Q2"]}),
           ("sensitivity B: world = Q1 + Q2, practice + Q3", {"groups_name": "sensitivity_B"}),
           ("sensitivity C: practice + Q8", {"groups_name": "sensitivity_C"}),
           ("sensitivity D: a secondary code counts half", {"secondary_half": True}),
           ("relaxed minimum: 5 per group", {"minimum": K.H5_RELAXED_HITS}),
           ("registered per-side minimum (10 per group and side)", {"per_side": True}),
           ("units next to a self-naming cue kept (before M9)", {"self_naming": False})]
    for source in bundle_has_titles:
        if source != "final":
            out.append((f"titles: {source} model without adjudication", {"title_source": source}))
    return out
