"""Verdict rules: Holm over the fixed count of 10, the outcome "not determinable", the reliability floor, A5 and the
registered conditions, the A10 guard, the uninformative flag, and the sentences every result carries.

Order of the rules for one version (amended or registered) of one hypothesis:
  1. fewer eligible creators than its minimum (A10.2 = CAL-A9): "not determinable: too few eligible creators (k of m)";
     enters Holm with p = 1; estimate and interval shown as description. H2 with no checkability part at 5% prevalence:
     "not determinable: no checkability part reaches 5% prevalence on seen statements".
  2. an instrument below its reliability floor (plan 3.4, A10.5 = CAL-A12; gates input): "not run for want of an
     instrument: below the reliability floor" (registry 2026-11-21 01:15 and 01:30, A10.5); p = 1 in Holm; counted as
     not determinable, so the result is uninformative (A10 Part 3).
  3. the Holm step passes (adjusted p <= 0.05; m = 10, H3, H7, H8 and H10 at p = 1, A10.1), the registered support rule
     holds, the 90% interval over creators excludes zero (A5), and the registered effect-size condition holds:
     "supported (model-coded)" (A8).
  4. the registered refutation holds: "refuted (model-coded)", with the reason; refutations read from intervals are
     unadjusted (A10.1 = CAL-A8 point 4).
  5. otherwise "not determined", with the conditions that failed.

A10 guard (registry, lead's decision of 2026-11-21 03:08): where A10 replaces a registered estimator, reference,
minimum, interval or centring, both versions are computed; the larger of the two p values enters Holm (a version that is
not usable counts as p = 1), both versions are judged on that Holm step, and a verdict stands only if both versions give
it. Registry 2026-11-21 04:55 (g): if either version is not determinable, the result is "not determinable" (kind "not
determinable", the reason naming the version), and so uninformative; "not determined: the registered and the amended
versions differ (...)" is kept for two determinable versions that disagree.

Uninformative (registry 02:50): a result is uninformative when its 90% creator interval contains both zero and the
smallest effect of interest in either direction, or its verdict is not determinable; judged on each version, and the
result is flagged when either version is.

Wording (registry 03:08): "supported (model-coded)" or "refuted (model-coded)", followed by "verified by a third model,
on known-answer texts and by a reader of another vendor" with the figures passed in the config. Never "validated".

A verdict is "robust to the labeller" only if every multiverse row gives the same verdict (plan 3.5).
"""
import json
from pathlib import Path

from . import constants as K
from . import stats

GUARD_RULE = ("A10 guard (registry 2026-11-21 03:08): the larger of the registered and the amended p enters Holm; a verdict "
              "stands only if both versions give it, otherwise 'not determined'; if either version is not determinable, "
              "the result is 'not determinable' (registry 2026-11-21 04:55 (g))")
NOT_DETERMINABLE = "not determinable"


def _reason(text):
    """The reason of a 'not determinable' text without its leading words."""
    return text[len(NOT_DETERMINABLE) + 2:] if text.startswith(NOT_DETERMINABLE + ": ") else text
NOT_RUN_INSTRUMENT = "not run for want of an instrument"      # registry 2026-11-21 01:15 and 01:30, A10.5
# registry 2026-11-21 03:21 (gate VG-6, the cross-vendor voice check): if it fails, H1, H4 and H6 carry this flag and
# their verdicts are capped at "not determined". Config: "cross_vendor_voice": {"passed": true/false, "kappa": k}.
VENDOR_FLAG = "readers of two vendors disagree (kappa {kappa})"


def vendor_cap(hypothesis, text, kind, vendor_check):
    """(text, kind, flag or None) under the VG-6 rule of 03:21: only a check entered as failed caps anything."""
    if hypothesis not in K.VOICE_HYPOTHESES or not vendor_check or vendor_check.get("passed") is not False:
        return text, kind, None
    flag = VENDOR_FLAG.format(kappa=vendor_check.get("kappa"))
    if kind in ("supported", "refuted"):
        return f"not determined: {flag} (capped; without the cap: {text})", "not determined", flag
    return text, kind, flag


def usable(result, gate):
    return bool(result and result.get("determinable") and result.get("estimate") is not None and (gate is None or gate.get("passed", True)))


def version_ps(result, gate):
    """(amended p, registered p or None) as they enter the guard: 1 where a version is not usable."""
    amended = result["p"] if usable(result, gate) else 1.0
    registered = result.get("registered_version")
    if registered is None:
        return amended, None
    return amended, (registered["p"] if usable(registered, gate) else 1.0)


def holm_p(result, gate):
    amended, registered = version_ps(result, gate)
    return amended if registered is None else max(amended, registered)


def holm_inputs(results, gates=None):
    out = {name: K.FIXED_P.get(name, 1.0) for name in K.ALL_HYPOTHESES}
    for name, result in results.items():
        out[name] = holm_p(result, (gates or {}).get(name))
    return out


def verdict(result, gate, adjusted):
    elig = result.get("eligibility") or {}
    if not result.get("determinable"):
        if result.get("reason") or elig.get("reason"):
            return result.get("reason") or elig.get("reason"), "not determinable"
        k, m = elig.get("creators", 0), elig.get("minimum")
        detail = ""
        if result["hypothesis"] == "H6" and elig.get("creators_with_T_at_least_1") is not None and k >= (m or 0):
            detail = f"; creators with an ask {elig['creators_with_T_at_least_1']} of {elig.get('minimum_with_T')}"
        if result["hypothesis"] == "H9" and elig.get("reference_reaches_first_holm_step") is False and k >= (m or 0):
            return (f"not determinable: the family-label permutation cannot reach the first Holm step ({k} creators, "
                    f"{elig.get('distinct_labelings')} distinct labelings)"), "not determinable"
        return f"not determinable: too few eligible creators ({k} of {m}{detail})", "not determinable"
    if gate is not None and not gate.get("passed", True):
        return NOT_RUN_INSTRUMENT + ": " + K.BELOW_FLOOR + " (" + str(gate.get("detail", "")) + ")", "not determinable"
    c = result.get("conditions") or {}
    p_adj, rejected = adjusted
    if rejected and c.get("registered") and c.get("a5") and c.get("effect_size"):
        return K.SUPPORTED, "supported"
    if c.get("refuted"):
        suffix = " (unadjusted interval)" if "interval" in c["refuted"] else ""
        return K.REFUTED + ": " + c["refuted"] + suffix, "refuted"
    failed = [name for name, ok in (("Holm step", rejected), ("registered rule", c.get("registered")), ("A5 interval", c.get("a5")),
                                    ("effect-size condition", c.get("effect_size"))) if not ok]
    return "not determined (" + ", ".join(failed) + ")", "not determined"


def guarded(result, gate, adjusted):
    """(text, kind, {version: {verdict, verdict_kind}} or None) under the A10 guard."""
    text, kind = verdict(result, gate, adjusted)
    registered = result.get("registered_version")
    if registered is None:
        return text, kind, None
    rtext, rkind = verdict(registered, gate, adjusted)
    versions = {"amended": {"verdict": text, "verdict_kind": kind}, "registered": {"verdict": rtext, "verdict_kind": rkind}}
    if kind == NOT_DETERMINABLE or rkind == NOT_DETERMINABLE:           # registry 04:55 (g)
        if kind == rkind:
            if text == rtext:
                return text, kind, versions
            return (f"{NOT_DETERMINABLE} in both versions (amended: {_reason(text)}; registered: {_reason(rtext)})",
                    NOT_DETERMINABLE, versions)
        if kind == NOT_DETERMINABLE:
            return (f"{NOT_DETERMINABLE} in the amended version: {_reason(text)} (registered version: {rtext})",
                    NOT_DETERMINABLE, versions)
        return (f"{NOT_DETERMINABLE} in the registered version: {_reason(rtext)} (amended version: {text})",
                NOT_DETERMINABLE, versions)
    if kind == rkind:
        return text, kind, versions
    return (f"not determined: the registered and the amended versions differ (registered: {rtext}; amended: {text})",
            "not determined", versions)


def uninformative(result, kind):
    """(flag, reason) of one version: its verdict is not determinable, or its 90% creator interval contains zero and the
    smallest effect of interest in either direction (K.UNINFORMATIVE_SESOI, on the interval's scale)."""
    if kind == "not determinable":
        return True, "the verdict is not determinable"
    lo, hi = result.get("creator_interval_90") or (None, None)
    if lo is None or hi is None:
        return True, "no 90% creator interval"
    sesoi = K.UNINFORMATIVE_SESOI[result["hypothesis"]]
    if lo <= 0 <= hi and (lo <= -sesoi or hi >= sesoi):
        return True, f"the 90% creator interval ({lo:.3g} to {hi:.3g}) contains zero and an effect of {sesoi:.3g} in size"
    return False, None


def figures(verification, hypothesis):
    """The verification figures of one hypothesis from the config: {"all": {...}, "<H>": {...}} merged, or a text."""
    if not verification:
        return None
    if isinstance(verification, str):
        return verification
    common_part, own = verification.get("all"), verification.get(hypothesis)
    if isinstance(own, str):
        return own
    merged = dict(common_part or {}) if isinstance(common_part, dict) else {}
    merged.update(own or {})
    for value in merged.values():
        if "validat" in str(value).lower():
            raise ValueError("verification figures must not use the word 'validated' (registry 2026-11-21 03:08)")
    return merged or None


def verification_clause(found):
    """'verified by a third model (...), on known-answer texts (...) and by a reader of another vendor (...)'."""
    if isinstance(found, str):
        if "validat" in found.lower():
            raise ValueError("verification text must not use the word 'validated' (registry 2026-11-21 03:08)")
        return found
    found = found or {}
    parts = [f"{phrase} ({found.get(key) or K.NOT_ENTERED})" for key, phrase in K.VERIFICATION_PARTS]
    return f"{parts[0]}, {parts[1]} and {parts[2]}"


def verdict_statement(kind, found):
    """The full wording of a supported or refuted verdict (registry 03:08); None for the other outcomes."""
    if kind == "supported":
        return f"{K.SUPPORTED}, {verification_clause(found)}"
    if kind == "refuted":
        return f"{K.REFUTED}, {verification_clause(found)}"
    return None


def sentences(hypothesis, verification=None, detectable=None):
    out = [K.MODEL_CODED]
    if hypothesis in K.VOICE_HYPOTHESES:
        out.append(K.PUNCTUATION_SENTENCE)
    if hypothesis in K.DISCLOSURES:
        out.append(K.DISCLOSURES[hypothesis])
    out.append("Verification (A11, registry 03:08): " + verification_clause(verification) + ".")
    if detectable:
        out.append(detectable)
    return out


BATTERY_RESULTS = "sim_out/simulation-results.json"           # beside this file: the full battery (run.py simulate)
H6_PLANTS = (("plant_sesoi", 0.5), ("plant_large", 0.25))     # the battery's planted rate ratios (simulate.PLANT["H6"])


def load_battery(path=None):
    """The full battery's results (run.py simulate, not --quick), or None if there is no such file."""
    path = Path(path) if path else Path(__file__).resolve().parent / BATTERY_RESULTS
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return None


def h6_detectable_from_battery(n, battery=None, fingerprint=None):
    """Registry 2026-11-21 11:08 (1): H6's detectable-effect note from the simulation battery's power, not from
    stats.detectable_effect (which assumes the sign-flip of normal creator values, not H6's amended p). The power is the
    share of planted sets in which the p that enters Holm (the A10 guard's larger p) reaches the first Holm step, at the
    battery's creator count nearest at or below n (12 or 17; power grows with creators, so this understates it), for the
    planted rate ratios 0.5 (the smallest effect) and 0.25. battery: the results of run.py simulate (default: the file
    sim_out/simulation-results.json); used only if it is a full battery of the current task fingerprint."""
    if battery is None:
        battery = load_battery()
    if fingerprint is None:
        from . import simulate                                   # late: simulate imports this module
        fingerprint = simulate.task_fingerprint()
    if not battery:
        return "H6's detectable effect comes from the simulation battery (run.py simulate), whose results are not on file"
    ran_on = (battery.get("progress") or {}).get("fingerprint")
    if battery.get("quick") or ran_on != fingerprint:
        return (f"H6's detectable effect comes from the full simulation battery of this code (task fingerprint "
                f"{str(fingerprint)[:12]}); the results on file are {'a quick run' if battery.get('quick') else 'of other code'} "
                f"(fingerprint {str(ran_on)[:12]}), so none is stated")
    rows = {(row["scenario"], row["creators"]): row for row in battery.get("experiments", []) if row.get("hypothesis") == "H6"}
    sizes = sorted({creators for scenario, creators in rows if scenario in dict(H6_PLANTS)})
    usable = [size for size in sizes if size <= n]
    if not usable:
        return (f"No detectable effect is stated: {n} creators is below the battery's smallest planted count "
                f"({sizes[0] if sizes else 'none'})")
    size = usable[-1]
    powers = []
    for scenario, ratio in H6_PLANTS:
        row = rows.get((scenario, size)) or {}
        power = row.get("reject_0.005_guarded")
        powers.append((ratio, power, row.get("supported_at_first_holm_step_guarded"), row.get("reps")))
    reached = [ratio for ratio, power, _, _ in powers if power is not None and power >= 0.80]
    shown = "; ".join(f"rate ratio {ratio}: {power:.0%} reach the first Holm step, {supported:.0%} 'supported' ({reps} sets)"
                      for ratio, power, supported, reps in powers if power is not None and supported is not None)
    if len(reached) == len(H6_PLANTS):
        verdict = "80% power at both planted ratios, the smallest effect (0.5) included"
    elif reached:
        verdict = (f"80% power at a rate ratio of {' and '.join(str(r) for r in reached)}, not at the smallest effect "
                   f"({H6_PLANTS[0][1]})")
    else:
        verdict = "80% power at neither planted ratio"
    return (f"detectable effect from the simulation battery (synthetic creators, {size} creators, the battery's count "
            f"nearest at or below the {n} eligible; task fingerprint {str(fingerprint)[:12]}): {shown}; {verdict}")


def detectable_note(hypothesis, n, creator_sd, alternative, battery=None):
    """A10.2 = CAL-A9 point 4. creator_sd: SD of creator values from the label-based CAL repeat (part f); without it the note
    says so. H6 (registry 2026-11-21 11:08 (1)): from the simulation battery's power (h6_detectable_from_battery), whatever
    creator_sd is; battery: the battery's results (default: the file beside this module)."""
    if hypothesis == "H6":
        return h6_detectable_from_battery(n, battery)
    if creator_sd is None:
        return "Detectable effect not computed: the SD of creator values from the label-based CAL repeat is not entered."
    d = stats.detectable_effect(n, alternative)
    if d is None:
        return f"No effect is detectable at the first Holm step with {n} creators."
    effect = d * creator_sd
    if hypothesis == "H5":                               # creator values are OE shares; the SESOI is a ratio
        return f"detectable from OE {effect:.3g} at 80% power at the first Holm step (the ratio it implies depends on the shares)"
    if hypothesis == "H9":
        return "H9's reference is a label permutation; its detectable effect comes from the simulation battery"
    sesoi = abs(K.SESOI[hypothesis])
    if effect > K.DETECTABLE_FACTOR * sesoi:
        return f"run; detectable only from {effect:.3g} ({effect / sesoi:.2g} times the smallest effect of interest)"
    return f"detectable from {effect:.3g} at 80% power at the first Holm step"


def _version_record(result, gate, kind_text):
    if result is None:
        return None
    text, kind = kind_text
    flag, reason = uninformative(result, kind)
    return {"version": result.get("version"), "determinable": result.get("determinable"), "p": result.get("p"),
            "p_method": result.get("p_method"), "p_entering_the_guard": result["p"] if usable(result, gate) else 1.0,
            "estimate": result.get("estimate"), "intervals": result.get("intervals"),
            "creator_interval_90": result.get("creator_interval_90"), "conditions": result.get("conditions"),
            "eligible_creators": (result.get("eligibility") or {}).get("creators"),
            "minimum": (result.get("eligibility") or {}).get("minimum"), "verdict": text, "verdict_kind": kind,
            "uninformative": flag, "uninformative_reason": reason, "notes": result.get("notes")}


def judge(name, result, gate, adjusted):
    """The guarded verdict of one result (primary or row), with both versions and the uninformative flag."""
    text, kind, versions = guarded(result, gate, adjusted)
    amended = _version_record(result, gate, verdict(result, gate, adjusted))
    registered = result.get("registered_version")
    reg_record = _version_record(registered, gate, verdict(registered, gate, adjusted)) if registered else None
    flags = [(amended["uninformative"], amended["uninformative_reason"])]
    if reg_record:
        flags.append((reg_record["uninformative"], reg_record["uninformative_reason"]))
    if kind == "not determinable":
        flags.append((True, "the verdict is not determinable"))
    reasons = sorted({reason for flag, reason in flags if flag and reason})
    return {"verdict": text, "verdict_kind": kind, "uninformative": any(flag for flag, _ in flags), "uninformative_reasons": reasons,
            "versions": {"amended": amended, "registered": reg_record},
            "a10_guard": {"applies": registered is not None, "replaced": list(result.get("a10_replaces") or []),
                          "rule": GUARD_RULE, "verdicts_agree": None if versions is None else
                          versions["amended"]["verdict_kind"] == versions["registered"]["verdict_kind"]}}


def finalise(primary, rows=None, gates=None, verification=None, detectable=None, vendor_check=None):
    """primary: {hypothesis: result}; rows: {hypothesis: [(row name, result)]}. vendor_check: the VG-6 outcome
    {"passed": bool, "kappa": k} (registry 03:21). Returns {hypothesis: final record} and the Holm table."""
    gates, rows, detectable = gates or {}, rows or {}, detectable or {}
    inputs = holm_inputs(primary, gates)
    table = stats.holm(inputs)
    out = {}
    for name, result in sorted(primary.items()):
        found = figures(verification, name)
        judged = judge(name, result, gates.get(name), table[name])
        judged["verdict"], judged["verdict_kind"], vendor_flag = vendor_cap(name, judged["verdict"], judged["verdict_kind"], vendor_check)
        kind = judged["verdict_kind"]
        row_records, kinds = [], []
        for row_name, row in rows.get(name, []):
            if row_name == "primary":
                continue
            row_inputs = dict(inputs)
            row_inputs[name] = holm_p(row, gates.get(name))
            row_table = stats.holm(row_inputs)
            row_judged = judge(name, row, gates.get(name), row_table[name])
            row_judged["verdict"], row_judged["verdict_kind"], _ = vendor_cap(name, row_judged["verdict"], row_judged["verdict_kind"],
                                                                              vendor_check)
            kinds.append(row_judged["verdict_kind"])
            row_records.append({"row": row_name, "estimate": row.get("estimate"), "intervals": row.get("intervals"), "p": row.get("p"),
                                "p_registered_version": (row.get("registered_version") or {}).get("p"),
                                "holm_input_p": row_inputs[name], "holm_adjusted_p": row_table[name][0],
                                "verdict": row_judged["verdict"], "verdict_kind": row_judged["verdict_kind"],
                                "uninformative": row_judged["uninformative"],
                                "eligible_creators": (row.get("eligibility") or {}).get("creators")})
        amended_p, registered_p = version_ps(result, gates.get(name))
        out[name] = {"verdict": judged["verdict"], "verdict_kind": kind,
                     "verdict_statement": verdict_statement(kind, found),
                     "holm_input_p": inputs[name], "holm_input_p_amended": amended_p, "holm_input_p_registered": registered_p,
                     "holm_adjusted_p": table[name][0], "holm_rejected": table[name][1],
                     "versions": judged["versions"], "a10_guard": judged["a10_guard"],
                     "uninformative": judged["uninformative"], "uninformative_reasons": judged["uninformative_reasons"],
                     "robust_to_the_labeller": bool(kinds) and all(k == kind for k in kinds),
                     "vendor_flag": vendor_flag,
                     "rows": row_records, "sentences": sentences(name, found, detectable.get(name)) + ([vendor_flag] if vendor_flag else [])}
    return out, {name: {"input_p": inputs[name], "adjusted_p": table[name][0], "rejected": table[name][1]} for name in K.ALL_HYPOTHESES}
