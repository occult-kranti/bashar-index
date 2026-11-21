"""H2. The more checkable a statement about the world's future, the less often it is stated with full commitment.

Estimand (hypotheses.md): within creators, Somers' D between checkability (count of the checkability parts) and
commitment (bare or boosted against hedged or conditional), computed within statement-length bands (H2_LENGTH_BANDS,
FREEZE2, from seen statements) and pooled, then pooled over creators by random effects. D here is the D of checkability
between committed and uncommitted statements (2 AUC - 1): below zero when committed statements are less checkable.
Weights 1 / p from the production valve. Unit: creator with at least 30 verified statements. Refuted by a 90% interval
inside -0.10 to +0.10, or a positive D whose interval excludes zero. Primary score: parts in STATEMENT or CONTEXT only
(R10); a cannot-tell part or commitment is missing (R7) and counted both ways in rows. Record of checkability: the middle
model on every statement (owner's decision before freeze 1).

Revisions before freeze 1 (registry, lead's decision of 2026-11-21 02:50, meta-review M9):
  * statements whose wording holds the scenario or withdrawal clauses that both codebooks name (wording.shared_wording,
    patterns constants.H2_SHARED_WORDING) are flagged; the primary row uses the unflagged statements, and the row with
    the flagged statements included is reported beside it. The flag reads the wording only, never a code.
  * the score counts only the parts with at least 5% prevalence on seen statements (constants.H2_PARTS_RETAINED, FREEZE2,
    parts_from_seen); the five-part score is a row. With no part retained H2 is not determinable.
A10 guard (registry 03:08): the amended version (A10.1 two-sided creator sign-flip; A10.3 minimum 9; A10.7 HKSJ) and the
registered version (within-creator-and-band permutation of commitment, 9,999 draws; minimum 8; the registered
creator-bootstrap 90% interval of the DerSimonian-Laird pooled D, drawn as catalogue rule R1 says: creators, then
recordings within each creator; registry 04:55 (d)) are both computed; verdicts.py combines them.
Rows added on 2026-11-21 04:55: a time window taken only from the period of the talk (where FRAME) counts as NO (second
reading); the recognizer-model-stratified row (registry 03:08), in which the length band is crossed with the model.
"""
from . import common
from . import constants as K
from . import stats
from . import tipping

H = "H2"
NO_PART = "not determinable: no checkability part reaches 5% prevalence on seen statements"
A10_REPLACES = ("reference: commitment permuted within creator and length band, 9,999 draws (registered) -> two-sided "
                "sign-flip of creator D (A10.1, CAL-A8)",
                "minimum: 8 creators (registered) -> 9, the two-sided minimum (A10.3, CAL-A10)",
                "interval: creator bootstrap (creators, then recordings, R1) of the pooled D (registered) -> HKSJ with "
                "t(k-1) (A10.7, CAL-A14)")
FRAME_ROW = "time window from the period of the talk (FRAME) counted as NO (second reading, registry 04:55)"


def retained_parts(parts=None):
    """The parts the score counts: the given ones, else constants.H2_PARTS_RETAINED (FREEZE2)."""
    parts = parts if parts is not None else K.H2_PARTS_RETAINED
    return None if parts is None else tuple(part for part in K.H2_PARTS if part in tuple(parts))


def score(statement, fc_source="record", ct=None, where=K.H2_PRIMARY_WHERE, only=None, parts=K.H2_PARTS, frame_time_window=None):
    """Checkability: number of YES parts (where in `where`) among `parts`; ct None: a cannot-tell part makes it missing;
    ct "yes"/"no": cannot-tell counted that way. only: one part name (the time-window row). frame_time_window "no": a
    time window whose "where" is FRAME (taken only from the period of the talk) is NO whatever its value (the row of the
    second reading, registry 2026-11-21 04:55)."""
    block = statement["parts"].get(fc_source)
    if not block:
        return None
    names = (only,) if only else parts
    total = 0
    for name in names:
        value, place = block[name]
        if frame_time_window == "no" and name == "time_window" and place == K.H2_FRAME_WHERE:
            continue
        if value == "CANNOT_TELL":
            if ct is None:
                return None
            total += ct == "yes"
        elif value == "YES" and place in where:
            total += 1
    return total


def committed(statement, fd_source="record", none_as=None):
    block = statement["commitment"].get(fd_source)
    if not block:
        return None
    value = block["committed"]
    return none_as if value is None else value


def flagged(statement):
    """The M9 flag: the statement's wording holds shared scenario or withdrawal wording (adapter.shared_wording_of)."""
    return bool(statement.get("shared_wording"))


def band_of(words, bands):
    for index, cut in enumerate(bands):
        if words <= cut:
            return index
    return len(bands)


def statements_by_creator(bundle, fc_source="record", fd_source="record", ct=None, none_as=None, where=K.H2_PRIMARY_WHERE,
                          only=None, bands=None, drop_unrouted=False, parts=None, include_flagged=False, tally=None,
                          frame_time_window=None, by_recording=None):
    """{creator: [(band, score, committed, weight, statement)]}. tally (a dict) receives the counts of flagged statements
    (verified, not duplicate) whatever include_flagged says. by_recording (a dict) receives {creator: {audio: [rows]}}
    with the same rows (the two-stage bootstrap's recordings). In the recognizer-model-stratified view (registry 03:08)
    the band is crossed with the recording's model: (band, model)."""
    bands = bands if bands is not None else K.H2_LENGTH_BANDS
    parts = retained_parts(parts) or ()
    out = {}
    for item in bundle["recordings"]:
        rec = item.get("forecasts")
        if not rec:
            continue
        stratum = common.stratum(bundle, item)
        for st in rec["statements"]:
            if not st["verified"] or st["duplicate"]:
                continue
            if drop_unrouted and st.get("routed_final") is False:
                continue
            if tally is not None:
                tally["statements"] = tally.get("statements", 0) + 1
                if flagged(st):
                    tally["flagged"] = tally.get("flagged", 0) + 1
                    for pid in st["shared_wording"]:
                        tally.setdefault("by_pattern", {})[pid] = tally.setdefault("by_pattern", {}).get(pid, 0) + 1
            if flagged(st) and not include_flagged:
                continue
            x, y = score(st, fc_source, ct, where, only, parts, frame_time_window), committed(st, fd_source, none_as)
            if x is None or y is None:
                continue
            band = band_of(st["words"], bands)
            row = ((band, stratum) if stratum is not None else band, x, y, st["weight"], st)
            out.setdefault(item["creator"], []).append(row)
            if by_recording is not None:
                by_recording.setdefault(item["creator"], {}).setdefault(item["audio"], []).append(row)
    return out


def eligible(bundle, **options):
    """Labels only: creators with at least 30 verified statements coded on both dimensions (unflagged statements in the
    primary definition)."""
    bundle = common.confirmatory(bundle)
    only, parts = options.get("only"), retained_parts(options.get("parts"))
    if parts is None and not only:
        raise ValueError("H2 needs the retained parts (FREEZE2): parts_from_seen on seen labels, entered before freeze 2")
    if not parts and not only:
        out = common.eligibility(H, 0, None, {"statements": 0, "parts_retained": []})
        out["determinable"], out["reason"] = False, NO_PART
        return out
    tally = {}
    by_creator = statements_by_creator(bundle, tally=tally, **options)
    creators = [c for c, rows in by_creator.items() if len(rows) >= K.H2_MIN_STATEMENTS]
    return common.eligibility(H, len(creators), None, {"statements": sum(len(by_creator[c]) for c in creators),
                                                      "parts_retained": list(retained_parts(options.get("parts")) or ()),
                                                      "single_part": only,
                                                      "flagged_statements": tally.get("flagged", 0),
                                                      "flagged_included": bool(options.get("include_flagged"))})


def creator_d(rows):
    """Pooled D over bands, and its variance (Hanley-McNeil per band)."""
    signed = pairs = 0.0
    parts = []
    for band in sorted({row[0] for row in rows}):
        s, w, n1, n0 = stats.somers_counts((x, y, wt) for b, x, y, wt, _ in rows if b == band)
        if w > 0:
            signed, pairs = signed + s, pairs + w
            parts.append((w, stats.somers_variance(s / w, n1, n0)))
    if pairs <= 0:
        return None, None
    variance = sum((w / pairs) ** 2 * v for w, v in parts)
    return signed / pairs, variance


def recording_tallies(rows):
    """{band: ({score: weight} committed, {score: weight} uncommitted)} of one recording's rows: what the two-stage
    bootstrap resamples (creator_d of the concatenated rows equals d_from_tallies of their tallies)."""
    out = {}
    for band, x, y, wt, _ in rows:
        committed_w, uncommitted_w = out.setdefault(band, ({}, {}))
        target = committed_w if y else uncommitted_w
        target[x] = target.get(x, 0.0) + wt
    return out


def d_from_tallies(tallies):
    """creator_d of the recordings whose tallies are given (with repeats: a recording drawn twice counts twice)."""
    merged = {}
    for tally in tallies:
        for band, (committed_w, uncommitted_w) in tally.items():
            m1, m0 = merged.setdefault(band, ({}, {}))
            for x, w in committed_w.items():
                m1[x] = m1.get(x, 0.0) + w
            for x, w in uncommitted_w.items():
                m0[x] = m0.get(x, 0.0) + w
    signed = pairs = 0.0
    parts = []
    for band in sorted(merged):
        m1, m0 = merged[band]
        s, w, n1, n0 = stats.somers_counts([(x, True, wt) for x, wt in sorted(m1.items())] + [(x, False, wt) for x, wt in sorted(m0.items())])
        if w > 0:
            signed, pairs = signed + s, pairs + w
            parts.append((w, stats.somers_variance(s / w, n1, n0)))
    if pairs <= 0:
        return None, None
    return signed / pairs, sum((w / pairs) ** 2 * v for w, v in parts)


def _two_stage_dl_mu(sample):
    """The registered statistic in one two-stage draw: the DerSimonian-Laird pooled D of the drawn creators, each from its
    drawn recordings."""
    pairs = [got for got in (d_from_tallies(recordings) for recordings in sample) if got[0] is not None]
    return _dl_mu(pairs) if len(pairs) >= 2 else None


def creator_d_ordinal(rows):
    num = den = 0.0
    for band in sorted({row[0] for row in rows}):
        sub = [(x, K.FOUR_STEP.get((st["commitment"].get("record") or {}).get("four_way")), wt) for b, x, y, wt, st in rows if b == band]
        sub = [r for r in sub if r[1] is not None]
        d, w = stats.somers_ordinal(sub)
        if d is not None:
            num, den = num + d * w, den + w
    return num / den if den else None


def conditions(mu, ci90):
    refuted = None
    if -K.SESOI[H] < ci90[0] and ci90[1] < K.SESOI[H]:
        refuted = "no trade-off: the 90% interval of D lies inside -0.10 to +0.10"
    elif mu > 0 and ci90[0] > 0:
        refuted = "a positive D whose 90% interval excludes zero"
    return {"registered": mu < 0, "a5": ci90[1] < 0, "effect_size": True, "refuted": refuted}


def _dl_mu(pairs):
    pool = stats.re_dl([a for a, _ in pairs], [b for _, b in pairs])
    return pool["mu"] if pool else None


def analyse(bundle, label=("H2",), extras=True, draws=K.BOOTSTRAP_DRAWS, permutations=K.PERMUTATION_DRAWS, bands=None, **options):
    bundle = common.confirmatory(bundle)
    bands = bands if bands is not None else K.H2_LENGTH_BANDS
    if bands is None:
        raise ValueError("H2 needs the length bands (FREEZE2): length_bands_from_seen on seen labels, entered before freeze 2")
    if options.get("parts") is None and K.H2_PARTS_RETAINED is None and not options.get("only"):
        raise ValueError("H2 needs the retained parts (FREEZE2): parts_from_seen on seen labels, entered before freeze 2")
    parts = retained_parts(options.get("parts"))
    base = {"hypothesis": H, "version": "amended", "a10_replaces": list(A10_REPLACES), "parts_retained": list(parts or ()),
            "flagged_included": bool(options.get("include_flagged"))}
    if not parts and not options.get("only"):
        elig = eligible(bundle, bands=bands, **options)
        reg = common.version(H, "registered", False, 1.0, None, None, None, (None, None),
                             dict(elig, minimum=K.REGISTERED_MIN_CREATORS[H]), A10_REPLACES)
        return dict(base, eligibility=elig, determinable=False, p=1.0, estimate=None, reason=NO_PART, registered_version=reg,
                    creator_interval_90=(None, None))
    tally, recordings = {}, {}
    by_creator = statements_by_creator(bundle, bands=bands, tally=tally, by_recording=recordings, **options)
    eligible_creators = sorted(c for c, rows in by_creator.items() if len(rows) >= K.H2_MIN_STATEMENTS)
    values, variances, kept, no_variation = [], [], [], 0
    for creator in eligible_creators:
        d, v = creator_d(by_creator[creator])
        if d is None:
            no_variation += 1
            continue
        values.append(d)
        variances.append(v)
        kept.append(creator)
    elig = common.eligibility(H, len(eligible_creators), None,
                              {"statements": sum(len(by_creator[c]) for c in eligible_creators), "creators_without_variation": no_variation,
                               "parts_retained": list(parts or ()), "single_part": options.get("only"),
                               "flagged_statements": tally.get("flagged", 0), "flagged_by_pattern": tally.get("by_pattern", {}),
                               "flagged_included": bool(options.get("include_flagged"))})
    out = dict(base, eligibility=elig, creators_with_values=len(kept))
    reg_elig = dict(elig, minimum=K.REGISTERED_MIN_CREATORS[H])
    if len(kept) < 2:
        out.update({"determinable": False, "p": 1.0, "estimate": None, "creator_interval_90": (None, None),
                    "registered_version": common.version(H, "registered", False, 1.0, None, None, None, (None, None), reg_elig,
                                                         A10_REPLACES)})
        return out
    pool = stats.re_hksj(values, variances)
    p, method = stats.signflip_p(values, "two-sided", label=label + ("signflip",))
    mu, ci90, ci95 = pool["mu"], pool["intervals"]["0.9"], pool["intervals"]["0.95"]
    out.update({"determinable": elig["determinable"] and len(kept) >= K.MIN_CREATORS[H],
                "estimate": {"somers_d": mu, "tau2": pool["tau2"]},
                "intervals": {"hksj_90": ci90, "hksj_95": ci95, "prediction_95": pool["prediction"]["0.95"],
                              "t90_creator_d": stats.t_interval(values)[1:]},
                "p": p, "p_method": method, "alternative": "two-sided", "creator_values": dict(zip(kept, values)),
                "creator_interval_90": ci90})
    out["conditions"] = conditions(mu, ci90)
    # the registered version: within-creator-and-band permutation p, the creator bootstrap of the DL-pooled D drawn as R1
    # says (creators, then recordings within each creator; registry 04:55 (d)), minimum 8
    perm = permutation_row([by_creator[c] for c in kept], permutations, label + ("perm",))
    tallies = [[recording_tallies(rows) for rows in recordings[c].values()] for c in kept]
    blo, bhi, failed = stats.bootstrap_two_stage(tallies, _two_stage_dl_mu, draws, label + ("registered", "two-stage"), K.A5_LEVEL)
    dl = stats.re_dl(values, variances)
    reg_ci = (blo, bhi)
    out["registered_version"] = common.version(
        H, "registered", elig["creators"] >= K.REGISTERED_MIN_CREATORS[H] and len(kept) >= K.REGISTERED_MIN_CREATORS[H],
        perm["p_two_sided"], {"somers_d": dl["mu"], "tau2": dl["tau2"]},
        {"bootstrap_90_pooled_d": reg_ci, "bootstrap": "creators, then recordings (R1)", "bootstrap_failed_draws": failed,
         "dl_90": dl["intervals"]["0.9"]},
        conditions(dl["mu"], reg_ci) if blo is not None else {"registered": dl["mu"] < 0, "a5": False, "effect_size": True,
                                                              "refuted": None},
        reg_ci, reg_elig, A10_REPLACES, f"within-creator-and-band permutation, {permutations} draws",
        {"permutation_reference_mean": perm["reference_mean"]})
    rows_all = [row for c in kept for row in by_creator[c]]
    xs = sorted(row[1] for row in rows_all)
    median = stats.quantile(xs, 0.5)
    high = [row for row in rows_all if row[1] > median]
    low = [row for row in rows_all if row[1] <= median]
    out["tipping"] = {"counts": tipping.commitment(sum(r[3] for r in high if r[2]), sum(r[3] for r in high),
                                                   sum(r[3] for r in low if r[2]), sum(r[3] for r in low)),
                      "note": "statements above against at or below the pooled median checkability, weighted"}
    if not extras:
        return out
    sec = {}
    sec["within-creator-and-band permutation of commitment (registered reference; the registered version of the A10 guard)"] = perm
    boot = stats.bootstrap_creators(values, common.mean_or_none, draws, label + ("boot",), K.A5_LEVEL)
    sec["creator-bootstrap 90% of the mean creator D"] = boot[:2]
    sec["leave-one-creator-out range of the pooled D"] = common.loo_range(
        list(zip(values, variances)), lambda pairs: (stats.re_hksj([a for a, _ in pairs], [b for _, b in pairs]) or {}).get("mu"))
    per_band = {}
    for c in kept:
        for band in sorted({row[0] for row in by_creator[c]}):
            s, w, _, _ = stats.somers_counts((x, y, wt) for b, x, y, wt, _ in by_creator[c] if b == band)
            if w > 0:
                per_band.setdefault(band, []).append(s / w)
    sec["D within each length band (mean of creator values)"] = {str(b): {"creators": len(v), "mean": common.mean_or_none(v)}
                                                                  for b, v in sorted(per_band.items())}
    ordinal = [creator_d_ordinal(by_creator[c]) for c in kept]
    ordinal = [v for v in ordinal if v is not None]
    sec["four-step order hedged < conditional < bare < boosted (sensitivity)"] = {"creators": len(ordinal), "mean": common.mean_or_none(ordinal),
                                                                                  "t90": stats.t_interval(ordinal)[1:] if len(ordinal) >= 2 else None}
    sec["R9 differential-error check (deterministic markers)"] = marker_gaps(rows_all)
    out["secondary"] = sec
    return out


def permutation_row(rows_by_creator, draws, label):
    """Mean creator D against commitment codes permuted within creator and band (two-sided)."""
    def mean_d(groups):
        values = []
        for rows in groups:
            d, _ = creator_d(rows)
            if d is not None:
                values.append(d)
        return common.mean_or_none(values)

    observed = mean_d(rows_by_creator)
    stream = stats.rng(*label)
    reference = []
    for _ in range(draws):
        shuffled = []
        for rows in rows_by_creator:
            new = []
            for band in sorted({row[0] for row in rows}):
                sub = [row for row in rows if row[0] == band]
                flags = [row[2] for row in sub]
                stream.shuffle(flags)
                new += [(row[0], row[1], flag, row[3], row[4]) for row, flag in zip(sub, flags)]
            shuffled.append(new)
        reference.append(mean_d(shuffled))
    reference = [value for value in reference if value is not None]
    return {"observed_mean_d": observed, "p_two_sided": stats.permutation_p(observed, reference, "two-sided") if reference else 1.0,
            "draws": draws, "reference_mean": common.mean_or_none(reference)}


def marker_gaps(rows):
    """Coder's time-window rate among statements the time expression flags, split by the hedge marker; and the coder's
    uncommitted rate among statements the hedge list flags, split by the time marker (R9)."""
    def rate(selected, test):
        return (sum(1 for r in selected if test(r)) / len(selected)) if selected else None

    timed = [r for r in rows if r[4]["markers"].get("time")]
    hedged = [r for r in rows if r[4]["markers"].get("hedge")]
    tw = lambda r: (r[4]["parts"].get("record") or {}).get("time_window", (None, None))[0] == "YES"
    a, b = rate([r for r in timed if r[4]["markers"].get("hedge")], tw), rate([r for r in timed if not r[4]["markers"].get("hedge")], tw)
    c, d = rate([r for r in hedged if r[4]["markers"].get("time")], lambda r: not r[2]), rate([r for r in hedged if not r[4]["markers"].get("time")], lambda r: not r[2])
    return {"time_window_rate_hedged_minus_unhedged": (a - b) if a is not None and b is not None else None,
            "uncommitted_rate_timed_minus_untimed": (c - d) if c is not None and d is not None else None,
            "rule": "a gap beyond the run-to-run figure plus 5 points is stated wherever H2 is reported"}


def length_bands_from_seen(bundle, fc_source="record"):
    """FREEZE2: tertile cut points of statement length (words) over verified statements of seen creators."""
    words = sorted(st["words"] for item in bundle["recordings"] if item.get("group") == "seen" and item.get("forecasts")
                   for st in item["forecasts"]["statements"] if st["verified"] and not st["duplicate"])
    if len(words) < 30:
        return None
    return (stats.quantile(words, 1 / 3), stats.quantile(words, 2 / 3))


def parts_from_seen(bundle, fc_source="record", threshold=K.H2_PART_PREVALENCE_MIN):
    """FREEZE2 (registry 02:50, M9): the parts whose prevalence on seen statements is at least `threshold` (5%).
    Prevalence of a part: the weighted share (weights 1 / p) of verified, non-duplicate statements with a usable record
    reading in which the part is YES in STATEMENT or CONTEXT (R10; CHOICE: all such statements, flagged ones included,
    because the prevalence describes the instrument). Returns (retained parts in H2_PARTS order, {part: prevalence},
    statements counted). Only counts and shares; no statement is returned."""
    total, yes, count = 0.0, {part: 0.0 for part in K.H2_PARTS}, 0
    for item in bundle["recordings"]:
        if item.get("group") != "seen" or not item.get("forecasts"):
            continue
        for st in item["forecasts"]["statements"]:
            block = st["parts"].get(fc_source)
            if not st["verified"] or st["duplicate"] or not block:
                continue
            count += 1
            total += st["weight"]
            for part in K.H2_PARTS:
                value, place = block[part]
                if value == "YES" and place in K.H2_PRIMARY_WHERE:
                    yes[part] += st["weight"]
    if total <= 0:
        return None, {}, 0
    share = {part: yes[part] / total for part in K.H2_PARTS}
    return tuple(part for part in K.H2_PARTS if share[part] >= threshold), share, count


def rows(fc_sources=("record",), fd_sources=("record",), routing=True):
    """routing: some statement carries the R3 flag (middle_final). The production files of label-files.md keep the
    middle model's routed reading on the candidate and call it never a label, so without the flag the R3 row is not
    built (it would repeat the primary)."""
    out = [("primary", {}),
           ("flagged statements included (shared scenario or withdrawal wording, M9)", {"include_flagged": True}),
           ("all five checkability parts (the score as registered before M9)", {"parts": list(K.H2_PARTS)}),
           ("cannot-tell parts counted as YES", {"ct": "yes"}),
           ("cannot-tell parts counted as NO", {"ct": "no"}),
           ("cannot-tell commitment counted as committed", {"none_as": True}),
           ("cannot-tell commitment counted as not committed", {"none_as": False}),
           ("FRAME parts counted (R10)", {"where": ("STATEMENT", "CONTEXT", "FRAME")}),
           (FRAME_ROW, {"frame_time_window": "no"}),
           ("time-window part alone", {"only": "time_window"})]
    if routing:
        out.append(("middle tier final where it judged (R3)", {"drop_unrouted": True}))
    for source in fc_sources:
        if source != "record":
            out.append((f"checkability: {source}", {"fc_source": source}))
    for source in fd_sources:
        if source != "record":
            out.append((f"commitment: {source}", {"fd_source": source}))
    return out
