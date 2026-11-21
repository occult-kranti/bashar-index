"""Simulation battery on synthetic creators only: generators that plant known effects in creators, recordings, units,
spans and label files, and the experiments the task asks for (recovery of planted effects, null rejection rates at 12
and 17 creators against the nominal level, interval coverage, behaviour at the "not determinable" boundary).

Generators produce label records in the formats the adapter reads (produce.py's voice and asks records, the pilot's
forecast, content and title layouts, this package's feature files), every one marked "synthetic": true, and pass them
through the adapter's parsers, so the analysis runs the same code path as on real files. write_files() puts one dataset
on disk for the end-to-end test of run.py. Nothing here reads a real file.

Model of a creator (all values per creator, so that the creator is the unit, as in CAL's creator-level placebo):
  H1  syllable rate base ~ N(3.9, 0.35)/s; claimed units multiplied by exp(e1_c), e1_c ~ N(mu1, tau1); recording and unit
      noise; pauses 5-20% of unit time.
  H4  own-voice contraction share ~ N(0.62, SIGMA_Y); claimed share (V2 and V3 alike) = own - drop_c * SIGMA_Y,
      drop_c ~ N(mu4, tau4). H4's primary reads the embodied voice (V2; registry 2026-11-21 04:55 (a)); a recording's
      claimed voice is embodied with probability 0.7, and in the calibration mode ("exact") each creator's first
      recording with both voices is embodied, so that every creator stays eligible for H4 (no random draw is added).
  M9  claimed voices open with a self-naming cue half of the time (that unit is coded Q1 when sampled); 10% of forecast
      statements carry shared scenario or withdrawal wording, which sets the observable outcome to NO and the commitment
      to hedged.
  H6  pay-or-enrol asks ~ Poisson(rate * words / 1000), own rate ~ Gamma(2, 0.275) per 1,000 words, claimed rate = own * RR;
      with "ask_rate_by_share" (the battery's null_heterogeneous scenario, registry 2026-11-21 06:44 (3)) a recording's
      rates are multiplied by exp(-k (s - 0.5)), s its claimed share of words (clamped to 0.25 .. 0.75), and the claimed
      voice of a recording with both voices opens after 22 to 60 own units, so that the shares spread between recordings.
      With "claimed_fraction" and "asks_per_creator" (the null_sparse_low_share scenario, registry 2026-11-21 09:19 (1))
      the claimed voice of a recording with both voices covers a fraction U(lo, hi) of its units (claimed shares of words
      below one half), and each creator has a whole number of asks U{lo..hi}, each on a unit of its recordings with both
      voices drawn in proportion to the unit's words (times RR in the claimed voice). With "claimed_fraction",
      "bursts_per_creator" and "burst_sizes" (the null_burst scenario, registry 2026-11-21 11:08 (1)) each creator has
      U{lo..hi} bursts of U{2..4} asks; a burst's anchor unit is drawn in proportion to words (times RR in the claimed
      voice) and its asks lie on consecutive units of the anchor's voice, so that a whole burst falls in one voice. With
      "burst_gaps" as well (the null_gapped scenario, registry 2026-11-21 12:52 (1)) consecutive asks of a burst lie
      U{1..3} units apart (not on consecutive units), still inside the anchor's stretch of one voice, at claimed shares
      below one half: the bursts that 11:08's adjacency rule split into single asks.
  H2  checkability = YES parts of five (P = 0.25 each, cannot-tell 3%, FRAME 5%); P(committed) = logistic(a_c + b_c (x - 1.2)).
  H5  coded points per recording; odds of world against practice codes exp(N(-1, 0.6)) on own-voice talks, times exp(theta)
      on channelled ones.
  H9  content tokens from global + creator + family distributions, function words from a base profile with creator and
      family style.
Voice labels: true side per unit; the record model flips 3% of units and the second model 6%; 15% of own units are
"cannot tell, uncued solo" (broad own voice only); offer spans after a claimed voice are V1 under rule A and claimed under
rule B (true side: claimed).
"""
import bisect
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

from . import adapter
from . import common
from . import constants as K
from . import features as F
from . import h1_rate, h2_hedging, h4_contraction, h5_world_claims, h6_asks, h9_family
from . import progress
from . import sim_cost
from . import stats
from . import verdicts
from . import voice_sets as vs

SIGMA_Y = 0.10
FAMILIES = ("S1", "S2", "S7", "A1", "A2", "G3")
CONTENT_VOCAB = 800
DEFAULT = {"mu1": 0.0, "tau1": 0.05, "mu4": 0.0, "tau4": 0.3, "rr": 1.0, "beta": 0.0, "tau2": 0.15, "theta": 0.0,
           "h9_content": 0.0, "h9_function": 0.0, "flip_record": 0.03, "flip_other": 0.06, "recordings": 8}


# ---------------------------------------------------------------- small helpers

def poisson(r, lam):
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, int(round(r.gauss(lam, math.sqrt(lam)))))
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= r.random()
        if p <= limit:
            return k
        k += 1


def binomial(r, n, p):
    return sum(r.random() < p for _ in range(n))


def logistic(x):
    return 1.0 / (1.0 + math.exp(-x))


# ---------------------------------------------------------------- one creator

def creator_habits(r, cfg):
    family = r.choice(FAMILIES)
    return {"rate": max(2.0, r.gauss(3.9, 0.35)), "e1": r.gauss(cfg["mu1"], cfg["tau1"]),
            "own_share": min(0.95, max(0.2, r.gauss(0.62, SIGMA_Y))), "drop": r.gauss(cfg["mu4"], cfg["tau4"]),
            "ask": r.gammavariate(2.0, 0.275), "a2": r.gauss(1.0, 0.5), "b2": r.gauss(cfg["beta"], cfg["tau2"]),
            "odds5": math.exp(r.gauss(-1.0, 0.6)), "family": family,
            "second_family": r.choice([f for f in FAMILIES if f != family]) if r.random() < 0.2 else None,
            "content_seed": r.getrandbits(32), "style_seed": r.getrandbits(32)}


def recording_kinds(r, n):
    kinds = ["both"] * max(2, n // 2) + ["own_only"] * max(2, n // 4)
    while len(kinds) < n:
        kinds.append("claimed_only")
    r.shuffle(kinds)
    return kinds[:n]


def voice_and_features(r, creator, group, index, kind, habits, cfg, synthetic=True, force_embodied=False):
    audio = f"syn-{creator}-{index:02d}"
    n_units = r.randint(90, 140)
    embodied = r.random() < 0.7 or force_embodied              # the draw is made either way: the stream does not change
    claimed_label = "V2" if embodied else "V3"
    truth = []
    if kind == "own_only":
        truth = ["own"] * n_units
        opening_end = r.randint(8, 12)
    elif kind == "claimed_only":
        opening_end = r.randint(3, 6)
        truth = ["own"] * opening_end + ["claimed"] * (n_units - opening_end)
    else:
        if cfg.get("claimed_fraction"):         # H6's null_sparse_low_share scenario (registry 09:19 (1)): shares below 1/2
            low, high = cfg["claimed_fraction"]
            fraction = r.uniform(low, high)
            closing = r.randint(4, 8)
            opening_end = n_units - closing - max(1, int(round(fraction * n_units)))
        else:
            if cfg.get("ask_rate_by_share"):    # H6's null_heterogeneous scenario: claimed shares spread between recordings
                opening_end = r.randint(22, 60)
            else:
                opening_end = r.randint(40, 48) if cfg.get("exact") else r.randint(24, 32)
            closing = r.randint(4, 8)
        truth = ["own"] * opening_end + ["claimed"] * (n_units - opening_end - closing) + ["own"] * closing
    offer = set()
    if kind != "own_only" and r.random() < 0.4:                     # an offer inside the claimed voice, near its end
        end = max(i for i, s in enumerate(truth) if s == "claimed")
        offer = set(range(max(opening_end, end - 3), end))
    claimant = r.choices(["sole_speaker", "host_or_owner", "cannot_tell", "guest_or_client"], [0.8, 0.12, 0.05, 0.03])[0]
    fmt = r.choices(["solo", "audience_session", "conversation"], [0.88, 0.08, 0.04])[0]
    main_kind = "own_talk" if kind == "own_only" else "claimed_voice"
    if r.random() < 0.05:
        main_kind = "guided_practice"
    if cfg.get("exact"):                                            # every creator inside the eligible set (calibration)
        claimant, fmt = "sole_speaker", "solo"
        main_kind = "own_talk" if kind == "own_only" else "claimed_voice"

    def model_view(flip):
        labels, labels_b, broad, details = [], [], [], []
        for i, side in enumerate(truth):
            if side == "claimed":
                label = "V1" if i in offer else claimed_label
                label_b = claimed_label
                detail = "none"
            else:
                uncued = r.random() < 0.15
                label = label_b = "V0" if uncued else "V1"
                detail = "uncued_solo" if uncued else "none"
            if r.random() < flip:
                label = label_b = r.choice(["V1", claimed_label, "V0", "V5"])
                detail = "unclear" if label == "V0" else "none"
            labels.append(label)
            labels_b.append(label_b)
            details.append(detail)
            broad.append(label == "V1" or (label == "V0" and detail == "uncued_solo" and claimant in K.PRIMARY_CLAIMANTS))
        return labels, labels_b, details, broad

    record_model = "small" if group == "seen" else "middle"
    views = {record_model: model_view(cfg["flip_record"]), ("small" if record_model == "middle" else "middle"): model_view(cfg["flip_other"])}
    units, feats, clock, word_index = [], [], r.uniform(1.0, 5.0), 0
    rec_noise = r.gauss(0.0, 0.05)
    drop = habits["drop"] * SIGMA_Y
    # cues of the spans (voice.py writes [cue type, cue unit] on every unit): half of the claimed voices open with a
    # self-naming cue at their first unit (H5's exclusion, registry 02:50), the others with an announcement
    first_claimed = next((i + 1 for i, side in enumerate(truth) if side == "claimed"), None)
    self_named = first_claimed is not None and r.random() < 0.5
    claimed_cue = ["self_name", first_claimed] if self_named else ["announce", max(1, (first_claimed or 1) - 1)]
    for i, side in enumerate(truth):
        n_words = r.randint(10, 20)
        per = {}
        for model, (labels, labels_b, details, broad) in views.items():
            cue = claimed_cue if side == "claimed" else ["own_person_identity", 1]
            per[model] = {"label": labels[i], "label_b": labels_b[i], "detail": details[i], "cue": list(cue),
                          "flags": ["offer_only_after_claimed"] if labels[i] != labels_b[i] else [], "own_broad": broad[i]}
        units.append({"id": i + 1, "first": word_index, "last": word_index + n_words - 1, "n_words": n_words, "map": per[record_model]["label"],
                      "small": per.get("small"), "middle": per.get("middle"), "label": per[record_model]["label"],
                      "label_b": per[record_model]["label_b"], "own_broad": per[record_model]["own_broad"]})
        word_index += n_words
        syl = max(n_words, int(round(n_words * r.gauss(1.35, 0.08))))
        rate = habits["rate"] * math.exp((habits["e1"] if side == "claimed" else 0.0) + rec_noise + r.gauss(0.0, 0.08))
        duration = syl / rate
        forms = poisson(r, n_words * 0.07)
        # the drop is planted in the whole claimed voice, V2 and V3 alike: H4's registered primary reads the embodied
        # voice (V2; registry 2026-11-21 04:55 (a)), which carries the drop, and so does its merged V2 + V3 secondary
        share = habits["own_share"] - (drop if side == "claimed" else 0.0)
        share = min(0.99, max(0.01, share))
        contracted = binomial(r, forms, share)
        feats.append({"id": i + 1, "start": round(clock, 3), "end": round(clock + duration, 3), "words": n_words, "syllables": syl,
                      "letters": int(syl * 2.9), "pauses": round(duration * r.uniform(0.05, 0.2), 3), "contracted": contracted,
                      "full": forms - contracted, "fp_sing": poisson(r, n_words * 0.04), "fp_plur": poisson(r, n_words * 0.03),
                      "hedges": poisson(r, n_words * 0.01), "self_name": bool(self_named and i + 1 == first_claimed)})
        clock += duration + r.uniform(0.05, 0.6)
    video = f"vid-{creator}-{index:02d}"
    voice = {"audio": audio, "creator": creator, "video_id": video, "group": group,
             "info": {"language": "en", "model_role": K.ASR_MODEL_REQUIRED},           # the bundle's recognizer role (ASR-model rule)
             "publisher_audio": False, "words": word_index,
             "map": {"format": fmt, "claimant": claimant, "content": "x", "main_kind": main_kind, "opening_end_unit": opening_end,
                     "closing_start_unit": None, "map_conflict": False, "flags": [], "failed_windows": 0, "failed_ranges": [],
                     "unmapped_ranges": [], "windows": 1, "detail_reset": 0, "detail_missing": 0, "own_cue_not_V1": 0, "vc_unresolved": 0},
             "label_of_record": record_model, "middle_labelled": True, "units": units, "spans_map": [], "spans_small": [], "spans_middle": [],
             "checks": {}, "failed_by_run": {"map": 0, record_model: 0}, "primary_runs": ["map", record_model], "failed_windows_total": 0,
             "variant": "A", "effort": "none", "frozen_utc": "synthetic", "written": "synthetic", "synthetic": synthetic}
    feature = {"audio": audio, "creator": creator, "group": group, "feature_version": F.FEATURE_VERSION, "units": feats, "synthetic": synthetic}
    return voice, feature, truth, embodied


def asks_record(r, voice, truth, habits, cfg, synthetic=True):
    asks = []
    own_rate = habits["ask"]
    if cfg.get("ask_rate_by_share"):
        # registry 2026-11-21 06:44 (3): ask rates that differ between a creator's recordings with their claimed share
        # (fewer asks per word where more of the recording is claimed voice), with no difference inside any recording
        words = {"claimed": 0, "own": 0}
        for unit, side in zip(voice["units"], truth):
            words[side] += unit["n_words"]
        share = min(0.75, max(0.25, words["claimed"] / max(1, words["claimed"] + words["own"])))
        own_rate *= math.exp(-cfg["ask_rate_by_share"] * (share - 0.5))
    for unit, side in zip(voice["units"], truth):
        rate = own_rate * (cfg["rr"] if side == "claimed" else 1.0)
        for _ in range(poisson(r, rate * unit["n_words"] / 1000.0)):
            asks.append(pay_or_enrol_ask(r, unit["id"]))
        if r.random() < unit["n_words"] * 0.0004:                    # platform-engagement asks do not count
            asks.append({"first_unit": unit["id"], "last_unit": unit["id"], "class": "K3", "final": "ask", "final_class": "K3",
                         "final_from": "middle", "final_small_fallback": None, "shared_units": False, "quote_check": "exact"})
    return asks_file(voice, asks, synthetic)


def pay_or_enrol_ask(r, unit_id):
    """One pay-or-enrol ask (K1) on one unit; 3% are left unchecked by the middle model, with the small model's verdict."""
    ask = {"first_unit": unit_id, "last_unit": unit_id, "class": "K1", "final": "ask", "final_class": "K1",
           "final_from": "middle", "final_small_fallback": None, "shared_units": False, "quote_check": "exact"}
    if r.random() < 0.03:
        ask.update({"final": "unchecked", "final_class": None, "final_from": None, "final_small_fallback": {"verdict": "ask", "class": "K1"}})
    return ask


def asks_file(voice, asks, synthetic=True):
    """produce.py's asks record of one recording around its list of asks."""
    return {"audio": voice["audio"], "creator": voice["creator"], "video_id": voice["video_id"], "group": voice["group"],
            "info": voice["info"], "publisher_audio": False, "words": voice["words"], "asks": asks, "find_windows_failed": 0,
            "find_failed_ranges": [], "check_calls_failed": {"small": 0, "middle": 0}, "middle_checked": True, "windows": 1,
            "failed_by_run": {"find": 0}, "primary_runs": ["find"], "failed_windows_total": 0, "frozen_utc": "synthetic",
            "written": "synthetic", "synthetic": synthetic}


def sparse_asks_records(r, recordings, cfg, synthetic=True):
    """H6's null_sparse_low_share scenario (registry 2026-11-21 09:19 (1)): one creator's asks records. recordings: the
    creator's (voice, truth, kind) in order. The creator has T ~ U{lo..hi} pay-or-enrol asks (cfg["asks_per_creator"]),
    each on a unit of its recordings with both voices drawn in proportion to the unit's words, times cfg["rr"] in the
    claimed voice; so under RR = 1 an ask that lands in recording i falls in its claimed voice with probability equal to
    its claimed share of words, given where the asks fell: the per-recording null of H6's reference."""
    low, high = cfg["asks_per_creator"]
    units, weights = [], []
    for index, (voice, truth, kind) in enumerate(recordings):
        if kind != "both":
            continue
        for unit, side in zip(voice["units"], truth):
            units.append((index, unit["id"]))
            weights.append(unit["n_words"] * (cfg["rr"] if side == "claimed" else 1.0))
    total = r.randint(low, high)
    placed = {}
    for index, unit_id in (r.choices(units, weights=weights, k=total) if units else []):
        placed.setdefault(index, []).append(pay_or_enrol_ask(r, unit_id))
    return [asks_file(voice, sorted(placed.get(index, []), key=lambda ask: ask["first_unit"]), synthetic)
            for index, (voice, _, _) in enumerate(recordings)]


def burst_asks_records(r, recordings, cfg, synthetic=True):
    """H6's null_burst scenario (registry 2026-11-21 11:08 (1)): one creator's asks records. recordings: the creator's
    (voice, truth, kind) in order. The creator has U{lo..hi} bursts (cfg["bursts_per_creator"]) of U{lo..hi} pay-or-enrol
    asks each (cfg["burst_sizes"]). A burst's anchor unit is drawn among the units of the creator's recordings with both
    voices in proportion to the unit's words (times cfg["rr"] in the claimed voice); its asks lie one a unit on
    consecutive units that contain the anchor and stay inside the anchor's stretch of one voice (where the stretch is
    shorter than the burst, the rest of the burst lies on its last unit). So under RR = 1 a burst falls in the claimed
    voice of recording i with probability equal to its claimed share of words, and all its asks with it: the cluster
    null of H6's reference, with clusters that the cluster rule (h6_asks.clusters_of) finds.
    With cfg["burst_gaps"] = (lo, hi) (the null_gapped scenario, registry 2026-11-21 12:52 (1)) consecutive asks of a burst
    lie U{lo..hi} units apart instead of on consecutive units: the burst's units span the sum of the gaps, lie inside the
    anchor's stretch and cover the anchor; where the stretch is shorter than that span the gaps become 1 (consecutive
    units, as above). Without burst_gaps the draws are those of null_burst, unchanged."""
    bursts_low, bursts_high = cfg["bursts_per_creator"]
    size_low, size_high = cfg["burst_sizes"]
    gaps = cfg.get("burst_gaps")
    units, weights = [], []
    for index, (voice, truth, kind) in enumerate(recordings):
        if kind != "both":
            continue
        for position, (unit, side) in enumerate(zip(voice["units"], truth)):
            units.append((index, position))
            weights.append(unit["n_words"] * (cfg["rr"] if side == "claimed" else 1.0))
    placed = {}
    for _ in range(r.randint(bursts_low, bursts_high) if units else 0):
        index, anchor = r.choices(units, weights=weights)[0]
        voice, truth, _ = recordings[index]
        size = r.randint(size_low, size_high)
        start = end = anchor
        while start > 0 and truth[start - 1] == truth[anchor]:
            start -= 1
        while end + 1 < len(truth) and truth[end + 1] == truth[anchor]:
            end += 1
        steps = [r.randint(*gaps) for _ in range(size - 1)] if gaps else None
        if steps and sum(steps) <= end - start:
            first = r.randint(max(start, anchor - sum(steps)), min(anchor, end - sum(steps)))
            positions = [first + sum(steps[:j]) for j in range(size)]
        elif end - start + 1 >= size:
            first = r.randint(max(start, anchor - size + 1), min(anchor, end - size + 1))
            positions = list(range(first, first + size))
        else:
            positions = list(range(start, end + 1)) + [end] * (size - (end - start + 1))
        for position in positions:
            placed.setdefault(index, []).append(pay_or_enrol_ask(r, voice["units"][position]["id"]))
    return [asks_file(voice, sorted(placed.get(index, []), key=lambda ask: ask["first_unit"]), synthetic)
            for index, (voice, _, _) in enumerate(recordings)]


SYNTHETIC_SHARED = ("syn in one scenario syn", "syn on another level syn", "syn either syn or syn")


def forecasts_record(r, audio, creator, group, habits, synthetic=True, n_mean=5.0):
    statements = []
    for k in range(poisson(r, n_mean)):
        values, where = {}, {}
        for part in K.H2_PARTS:
            u = r.random()
            values[part] = "CANNOT_TELL" if u < 0.03 else ("YES" if u < 0.03 + 0.25 else "NO")
            where[part] = ("FRAME" if r.random() < 0.05 else ("CONTEXT" if r.random() < 0.1 else "STATEMENT")) if values[part] != "NO" else "NA"
        # 10% of statements carry wording both codebooks name (M9): it sets the observable outcome to NO and the statement
        # to hedged, by definition; the primary row leaves them out
        shared = r.random() < 0.10
        quote = r.choice(SYNTHETIC_SHARED) if shared else f"syn statement {k}"
        if shared:
            values["observable_outcome"], where["observable_outcome"] = "NO", "NA"
        x = sum(1 for part in K.H2_PARTS if values[part] == "YES" and where[part] in K.H2_PRIMARY_WHERE)
        committed = r.random() < logistic(habits["a2"] + habits["b2"] * (x - 1.2)) and not shared
        cannot = r.random() < 0.02 and not shared
        four = ("bare" if r.random() < 0.8 else "boosted") if committed else ("hedged" if r.random() < 0.7 else "conditional")
        small_values = {p: (v if r.random() > 0.1 else ("YES" if v == "NO" else "NO")) for p, v in values.items()}
        statements.append({"key": f"{audio}-{k}", "verified": r.random() > 0.03, "duplicate": r.random() < 0.02,
                           "statement_quote": quote,
                           "statement_words": r.randint(8, 40), "markers": {"hedge": not committed and r.random() < 0.6, "condition": False,
                                                                            "time": values["time_window"] == "YES" and r.random() < 0.8},
                           "fc": {"values": values, "where": where}, "fc_second": {"values": small_values, "where": where},
                           "fd": {"committed": None if cannot else committed, "four_way": "cannot_tell" if cannot else four},
                           "coded": True, "inclusion_p": 1.0})
    return {"audio": audio, "creator": creator, "group": group, "statements": statements, "statements_coded": len(statements),
            "synthetic": synthetic}


def title_record(r, kind, habits, family_for_title, exact=False):
    if kind == "own_only":
        return {"presentation": r.choice(["P0", "P2"]), "cues": [], "voiced_by": "NA", "sources": [], "source_families": [],
                "topic_families": [], "kind_cues": ["KM"] if r.random() < 0.05 and not exact else ["K0"], "time_cue": "TC0",
                "time_also_portal": False, "language": "en"}
    return {"presentation": "P1" if r.random() > 0.04 or exact else "P9", "cues": ["CH_WORD"], "voiced_by": "C",
            "sources": [{"name": "x", "role": "SOURCE", "family": "FAM" + family_for_title}], "source_families": ["FAM" + family_for_title],
            "topic_families": [], "kind_cues": ["K0"], "time_cue": "TC0", "time_also_portal": False, "language": "en"}


def content_record(r, voice, side, habits, cfg, synthetic=True, points=60):
    odds = habits["odds5"] * (math.exp(cfg["theta"]) if side == "A" else 1.0)
    share_wp = 0.6
    p_world = share_wp * odds / (1 + odds)
    p_practice = share_wp - p_world
    body = [u for u in voice["units"][int(0.1 * len(voice["units"])):int(0.9 * len(voice["units"]))]]
    whole = r.random() < 0.1
    units = {}
    others = ("Q2", "Q3", "Q7", "Q8", "Q9", "Q0")
    # a self-introduction of a source is coded as a world claim (the M9 artefact that H5's exclusion removes)
    record = voice["label_of_record"]
    self_named = {unit[record]["cue"][1] for unit in voice["units"] if (unit.get(record) or {}).get("cue", ["none"])[0] == "self_name"}
    picks = body if whole else [body[r.randrange(len(body))] for _ in range(points)]
    for unit in picks:
        u = r.random()
        code = r.choice(("Q4", "Q5", "Q6")) if u < p_practice else ("Q1" if u < p_practice + p_world else r.choice(others))
        if unit["id"] in self_named:
            code = "Q1"
        entry = units.get(str(unit["id"]))
        if entry is None:
            units[str(unit["id"])] = {"primary": code, "secondary": "NONE" if r.random() < 0.8 else r.choice(others + ("Q1", "Q4")),
                                      "group": SENTENCE_GROUPS.get(code, "neither"), "candidates": [], "quote_check": "exact",
                                      "quote_words": 5, "soft": 0, "weight": unit["n_words"] if whole else 1}
        elif not whole:
            entry["weight"] += 1
    return {"audio": voice["audio"], "creator": voice["creator"], "group": voice["group"], "points": points, "too_short": False,
            "coded_whole": whole, "units": units, "units_coded": len(units), "synthetic": synthetic}


SENTENCE_GROUPS = {"Q1": "world_claim", "Q4": "practice_and_feeling", "Q5": "practice_and_feeling", "Q6": "practice_and_feeling"}


def family_distributions(seed):
    r = random.Random(seed)
    out = {}
    for family in FAMILIES:
        tokens = r.sample(range(CONTENT_VOCAB), 60)
        out[family] = {"content": tokens, "style": [r.gauss(0, 1) for _ in F.FUNCTION_WORDS]}
    return out


def h9_counts(r, habits, family, fams, cfg, n_content=700, n_function=700):
    base = [1.0 / (i + 10) for i in range(CONTENT_VOCAB)]
    total = sum(base)
    weights = [b / total for b in base]
    cr = random.Random(habits["content_seed"])
    for token in cr.sample(range(CONTENT_VOCAB), 60):
        weights[token] += 0.4 / 60
    if cfg["h9_content"] > 0:
        for token in fams[family]["content"]:
            weights[token] += cfg["h9_content"] / 60
    population = [f"c{i:04d}" for i in range(CONTENT_VOCAB)]
    content = {}
    for token in r.choices(population, weights=weights, k=n_content):
        content[token] = content.get(token, 0) + 1
    sr = random.Random(habits["style_seed"])
    fw = []
    for i, _ in enumerate(F.FUNCTION_WORDS):
        fw.append((1.0 / (i + 3)) * math.exp(0.3 * sr.gauss(0, 1) + cfg["h9_function"] * fams[family]["style"][i]))
    function = {}
    for token in r.choices(F.FUNCTION_WORDS, weights=fw, k=n_function):
        function[token] = function.get(token, 0) + 1
    return {"content": content, "function": function, "other": 150,
            "opening_family_match": {family: bool(cfg.get("exact")) or r.random() < 0.9}}


# ---------------------------------------------------------------- a cohort

def cohort(seed, n_holdout, cfg=None, n_seen=0, parts=("voice", "features", "asks", "forecasts", "titles", "content", "h9"),
           raw=False):
    """Synthetic creators: n_holdout hold-out and n_seen seen. Returns the analysis bundle (and the raw records if raw)."""
    cfg = dict(DEFAULT, **(cfg or {}))
    r = random.Random(seed)
    fams = family_distributions(r.getrandbits(32))
    files = {"voice": [], "features": [], "asks": [], "forecasts": [], "content": [], "titles": {}}
    for group, count in (("holdout", n_holdout), ("seen", n_seen)):
        for c in range(count):
            creator = f"{group[0]}{c:03d}"
            habits = creator_habits(r, cfg)
            kinds = recording_kinds(r, cfg["recordings"])
            first_both = kinds.index("both") if "both" in kinds else None
            per_creator_asks = []        # null_sparse_low_share: the creator's asks are placed once all its recordings exist
            for index, kind in enumerate(kinds):
                voice, feature, truth, _ = voice_and_features(r, creator, group, index, kind, habits, cfg,
                                                              force_embodied=bool(cfg.get("exact")) and index == first_both)
                family = habits["second_family"] if habits["second_family"] and index % 3 == 2 else habits["family"]
                if "voice" in parts:
                    files["voice"].append(voice)
                if "h9" in parts:
                    feature["h9"] = h9_counts(r, habits, family, fams, cfg)
                if "features" in parts or "h9" in parts:
                    files["features"].append(feature)
                if "asks" in parts and (cfg.get("asks_per_creator") or cfg.get("bursts_per_creator")):
                    per_creator_asks.append((voice, truth, kind))
                elif "asks" in parts:
                    files["asks"].append(asks_record(r, voice, truth, habits, cfg))
                if "forecasts" in parts:
                    files["forecasts"].append(forecasts_record(r, voice["audio"], creator, group, habits,
                                                               n_mean=8.0 if cfg.get("exact") else 5.0))
                if "titles" in parts:
                    # production layout of label-files.md: one file per creator, one entry per title; the middle model
                    # is the record, the small model disagrees on 5% of titles, the large model decides those
                    title = title_record(r, kind, habits, family, exact=cfg.get("exact", False))
                    flipped = dict(title, presentation="P9") if r.random() < 0.05 else title
                    disputed = flipped["presentation"] != title["presentation"]
                    entry = {"video_id": voice["video_id"], "audio": [voice["audio"]], "position": index + 1, "masked": False,
                             "primary": title, "second": flipped, "disputed": ["presentation"] if disputed else [],
                             "adjudicated_because": "disagreement" if disputed else None, "large": title if disputed else None,
                             "record": title, "record_from": "large" if disputed else "primary"}
                    files["titles"].setdefault(creator, {"creator": creator, "group": group, "titles": [],
                                                         "synthetic": True})["titles"].append(entry)
                if "content" in parts:
                    side = "B" if kind == "own_only" else "A"
                    files["content"].append(content_record(r, voice, side, habits, cfg))
            if per_creator_asks:
                place = burst_asks_records if cfg.get("bursts_per_creator") else sparse_asks_records
                files["asks"].extend(place(r, per_creator_asks, cfg))
    voice = [adapter.parse_voice(v) for v in files["voice"]]
    index = adapter.index_of(voice)
    b = adapter.bundle(voice=voice, asks=[adapter.parse_asks(a) for a in files["asks"]],
                       features=[adapter.parse_features(f) for f in files["features"]],
                       forecasts=[x for f in files["forecasts"] for x in adapter.parse_forecasts(f, index)],
                       content=[x for c in files["content"] for x in adapter.parse_content(c, index)],
                       titles=adapter.parse_title_files(list(files["titles"].values())) if "titles" in parts else None)
    adapter.require_permission(b["records"])
    return (b, files) if raw else b


def mark_synthetic(folder):
    """The marker the adapter's permission check looks for before freeze 2 (adapter.SYNTHETIC_MARKER; registry
    2026-11-21 04:55 (f)): written only by this generator, beside synthetic files."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / adapter.SYNTHETIC_MARKER).write_text(json.dumps({"synthetic": True, "written_by": "hypotheses.simulate"}),
                                                   encoding="utf-8")


def write_files(folder, files):
    """One dataset on disk in the layouts of the label files (for the end-to-end test of run.py); every folder carries
    the synthetic marker."""
    folder = Path(folder)
    mark_synthetic(folder)
    paths = {}
    for kind, name in (("voice", "voice"), ("features", "features"), ("asks", "asks"), ("forecasts", "forecasts"),
                       ("content", "sentences")):
        target = folder / name
        mark_synthetic(target)
        for record in files[kind]:
            (target / (record["audio"] + ".json")).write_text(json.dumps(record), encoding="utf-8")
        paths[name] = str(target)
    target = folder / "titles"
    mark_synthetic(target)
    for creator, record in sorted(files["titles"].items()):
        (target / (creator + ".json")).write_text(json.dumps(record), encoding="utf-8")
    paths["titles"] = str(target)
    return paths


# ---------------------------------------------------------------- experiments

PARTS = {"H1": ("voice", "features"), "H4": ("voice", "features"), "H6": ("voice", "asks"), "H2": ("voice", "forecasts"),
         "H5": ("voice", "titles", "content"), "H9": ("voice", "titles", "h9")}
EFFECT = {"H1": "mu1", "H4": "mu4", "H6": "rr", "H2": "beta", "H5": "theta", "H9": "h9_content"}
NULL = {"H1": 0.0, "H4": 0.0, "H6": 1.0, "H2": 0.0, "H5": 0.0, "H9": 0.0}
# planted parameters: about the smallest effect of interest, and a larger one. H2: beta of the logistic model (D about
# -0.10 and -0.34 without label error); H9: mass of the family distribution in the content mixture (delta about 0.27 and 0.85 at 17 creators).
PLANT = {"H1": (-0.05, -0.15), "H4": (0.5, 1.0), "H6": (0.5, 0.25), "H2": (-0.2, -0.7), "H5": (0.4, 0.8), "H9": (0.06, 0.12)}
# Registry 2026-11-21 06:44 (4): H9's creator bootstrap draws creators, then recordings, and re-rarefies every cell in
# every draw (about 60 ms a draw at 17 hold-out and 40 seen creators against well under 1 ms with fixed similarities), so
# the battery gives H9's bootstrap fewer draws than the 499 of the light runs of H2, H5 and H6 (H9's light runs had 199
# before); the analysis keeps 9,999 (constants.BOOTSTRAP_DRAWS). Percentile endpoints from 99 draws are rougher; the
# coverage column is read with that.
H9_BATTERY_BOOTSTRAP_DRAWS = 99
# Registry 2026-11-21 11:08 (1): Monte Carlo draws of H6's cluster-level and ask-level conditional references in the
# battery: 9,999, fewer than the analysis's 99,999 (h6_asks.REFERENCE_DRAWS). At 17 creators one reference takes about
# 0.2 s with 99,999 draws against 0.02 s with 9,999, so the analysis's count would add about 2 CPU hours to the
# battery's 18,000 H6 repetitions (and take H6 outside sim_cost.py's calibration). The test's level is exact at 0.005
# and 0.05 with either count (simulate.h6_cluster_reference_levels gives both); the battery's p near 0.005 is noisier
# than the analysis's, which moves single sets, not the level.
H6_BATTERY_REFERENCE_DRAWS = 9999
# Registry 2026-11-21 06:44 (3): the H6 null scenario "null_heterogeneous" lets a creator's ask rate per word differ
# between its recordings with their claimed share (rate x exp(-8 (s - 0.5)), s clamped to 0.25 .. 0.75: 7.4 to 0.14 times
# at the clamps; claimed shares spread over about 0.27 to 0.80) and plants no difference inside any recording: the pooled
# OE of CAL-A11 is not centred there (its mean given the T_i about -0.075, 0.23 SD of creator OE, in H6's direction, on
# synthetic cohorts of 60 creators), the per-recording OE of 06:44 (3) is.
H6_HETEROGENEITY = 8.0
# Registry 2026-11-21 09:19 (1): the H6 null scenario "null_sparse_low_share", the region where the sign-flip of OE
# rejected too often: in every recording with both voices the claimed voice covers 25% to 45% of the units (claimed shares
# of the words in the two voices about 0.24 to 0.47 after label error, median about 0.35), and every creator has 1 to 3
# pay-or-enrol asks in all, placed in proportion to words with no difference between the voices.
H6_SPARSE_CLAIMED_FRACTION = (0.25, 0.45)
H6_SPARSE_ASKS_PER_CREATOR = (1, 3)
# Registry 2026-11-21 11:08 (1): the H6 null scenario "null_burst", where an ask-level reference rejects too often: in
# every recording with both voices the claimed voice covers 30% to 70% of the units, and every creator has 1 or 2
# bursts of 2 to 4 pay-or-enrol asks, each burst on consecutive units of one voice, placed in proportion to words with
# no difference between the voices (burst_asks_records).
H6_BURST_CLAIMED_FRACTION = (0.3, 0.7)
H6_BURSTS_PER_CREATOR = (1, 2)
H6_BURST_SIZES = (2, 4)
# Registry 2026-11-21 12:52 (1): the H6 null scenario "null_gapped", where 11:08's adjacency rule found no burst and both
# halves of the amended p over-rejected (the fifth verification: 17 creators, one burst of 3 at a claimed share of 0.3
# seen as three single asks, 1.93% at 0.005): in every recording with both voices the claimed voice covers 25% to 45% of
# the units (claimed shares below one half, as null_sparse_low_share), and every creator has one burst of 2 to 4
# pay-or-enrol asks in one voice whose consecutive asks lie 1 to 3 units apart, placed in proportion to words with no
# difference between the voices (burst_asks_records with burst_gaps).
H6_GAPPED_CLAIMED_FRACTION = (0.25, 0.45)
H6_GAPPED_BURSTS_PER_CREATOR = (1, 1)
H6_GAPPED_BURST_SIZES = (2, 4)
H6_GAPPED_GAPS = (1, 3)
SCENARIO_CFG = {"null_heterogeneous": {"ask_rate_by_share": H6_HETEROGENEITY},
                "null_sparse_low_share": {"claimed_fraction": H6_SPARSE_CLAIMED_FRACTION,
                                          "asks_per_creator": H6_SPARSE_ASKS_PER_CREATOR},
                "null_burst": {"claimed_fraction": H6_BURST_CLAIMED_FRACTION, "bursts_per_creator": H6_BURSTS_PER_CREATOR,
                               "burst_sizes": H6_BURST_SIZES},
                "null_gapped": {"claimed_fraction": H6_GAPPED_CLAIMED_FRACTION,
                                "bursts_per_creator": H6_GAPPED_BURSTS_PER_CREATOR, "burst_sizes": H6_GAPPED_BURST_SIZES,
                                "burst_gaps": H6_GAPPED_GAPS}}
H6_NULL_SCENARIOS = ("null", "null_heterogeneous", "null_sparse_low_share", "null_burst", "null_gapped")
# The p values of every H6 row (registry 11:08 (1)): the amended p (the larger of the cluster-level conditional p and
# the sign-flip p of OE) is the row's "p"; beside it its two halves and the references it replaced, on the same sets;
# since 12:52 (1) also the amended p with the clusters of 11:08 (a window of 1 unit) and of the 10-unit sensitivity row.
H6_COMPARISON_PS = (("p_cluster_conditional", "the cluster-level conditional p alone (11:08 (1); window 5, 12:52 (1))"),
                    ("p_signflip_oe", "the sign-flip of OE alone (06:44 (3) to 09:19 (1))"),
                    ("p_ask_level_conditional_0919", "the ask-level conditional p (09:19 (1) to 11:08 (1))"),
                    ("p_pooled_oe_before_0644", "the sign-flip of CAL-A11's pooled OE (before 06:44 (3))"),
                    ("p_amended_window_1_1108", "the amended p with 11:08's clusters (same, overlapping or adjacent units)"),
                    ("p_amended_window_10", "the amended p with a 10-unit window (the sensitivity row of 12:52 (1))"))
# the windows of the comparison columns above (h6_comparison_ps)
H6_COMPARISON_WINDOWS = (("p_amended_window_1_1108", 1), ("p_amended_window_10", h6_asks.H6_SENSITIVITY_WINDOW))


def _run_one(hypothesis, b, seed, light, yardstick=None, bands=None, parts=None):
    label = (hypothesis, "sim", seed)
    if hypothesis == "H1":
        return h1_rate.analyse(b, label=label, extras=not light)
    if hypothesis == "H4":
        return h4_contraction.analyse(b, yardstick=yardstick, label=label, extras=not light)
    if hypothesis == "H6":
        return h6_asks.analyse(b, label=label, extras=not light, draws=499 if light else 1999,
                               reference_draws=H6_BATTERY_REFERENCE_DRAWS)
    if hypothesis == "H2":
        return h2_hedging.analyse(b, label=label, extras=not light, bands=bands, parts=parts, draws=499, permutations=199)
    if hypothesis == "H5":
        return h5_world_claims.analyse(b, label=label, extras=not light, draws=499 if light else 1999)
    if hypothesis == "H9":
        return h9_family.analyse(b, label=label, extras=False, draws=H9_BATTERY_BOOTSTRAP_DRAWS if light else 499,
                                 permutations=1999)
    raise ValueError(hypothesis)


def h6_pooled_oe_p(bundle, label):
    """The p of CAL-A11's pooled OE (a / T - s over a creator's recordings, before registry 2026-11-21 06:44 (3)) on the
    same synthetic set, for the battery's comparison column only; None below 2 creators with an ask."""
    tables = h6_asks.creator_tables(common.confirmatory(bundle), vs.primary_definition("H6"))
    rows = [rows for _, rows in sorted(tables.items()) if sum(row["a"] + row["b"] for row in rows) >= 1]
    if len(rows) < 2:
        return None
    p, _ = stats.signflip_p([h6_asks.pooled_oe_value(r) for r in rows], "less", label=label + ("pooled-oe",))
    return p


def h6_comparison_ps(bundle, result, label, draws=H6_BATTERY_REFERENCE_DRAWS):
    """The p values of one H6 repetition beside the amended p (H6_COMPARISON_PS): the two halves of the amended p and the
    ask-level conditional p, as h6_asks.amended_p computed them in the analysis of the set, the pooled OE's p on the
    same set, and the amended p with the clusters formed at a window of 1 (11:08 (1)) and of 10 units (the sensitivity
    row; h6_asks.window_p, same sign-flip half, `draws` draws); None where the analysis did not get that far (below 2
    creators with an ask)."""
    parts = result.get("p_parts") or {}
    out = {"p_cluster_conditional": parts.get("cluster_conditional"), "p_signflip_oe": parts.get("signflip_oe"),
           "p_ask_level_conditional_0919": parts.get("ask_level_conditional_0919"),
           "p_pooled_oe_before_0644": h6_pooled_oe_p(bundle, label),
           "largest_cluster": parts.get("largest_cluster")}
    for key, window in H6_COMPARISON_WINDOWS:
        got = None
        if parts.get("signflip_oe") is not None:
            got = h6_asks.window_p(common.confirmatory(bundle), vs.definition(), window, label, parts["signflip_oe"], draws)
        out[key] = got["p"] if got else None
    return out


_CONSTANTS = {}


def calibration_constants(key):
    """FREEZE2 constants computed exactly as at freeze 2, from a synthetic seen cohort of 40 creators; one per key and
    process (cached), so every repetition of an experiment uses the same constant, as the study will. Returns
    (H4 yardstick, H2 length bands, H2 retained parts)."""
    if key not in _CONSTANTS:
        seen = cohort(stats.seed_for("seen-constants", key), 0, {"exact": True}, n_seen=40, parts=("voice", "features", "forecasts"))
        yardstick, _ = h4_contraction.yardstick_from_seen(seen)
        _CONSTANTS[key] = (yardstick, h2_hedging.length_bands_from_seen(seen), h2_hedging.parts_from_seen(seen)[0])
    return _CONSTANTS[key]


def guarded_row(result):
    """The A10 guard of one repetition: the larger p and whether both versions meet the support conditions."""
    registered = result.get("registered_version") or {}
    both = all(version.get("determinable") and all((version.get("conditions") or {}).get(key) for key in ("registered", "a5", "effect_size"))
               for version in (result, registered or result))
    return {"p_guarded": verdicts.holm_p(result, None), "both_versions_meet_support_conditions": both}


def primary_estimate(hypothesis, result):
    est = result.get("estimate") or {}
    key = {"H1": "log_ratio", "H4": "standardised_drop", "H6": "mh_rate_ratio", "H2": "somers_d", "H5": "mh_log_odds_ratio",
           "H9": "delta"}[hypothesis]
    value = est.get(key)
    if hypothesis == "H6" and value:
        return math.log(value)
    return value


def _log_pair(value):
    return (math.log(value[0]), math.log(value[1])) if value and value[0] and value[1] else None


def a5_interval(hypothesis, result):
    """The 90% interval of the estimate: HKSJ for the pools, the interval the MH estimate carries (the wider of the
    creator-bootstrap percentile and the jackknife t interval, registry 2026-11-21 04:55 (j)) for H5 and H6, the creator
    bootstrap for H9."""
    ints = result.get("intervals") or {}
    value = {"H1": ints.get("hksj_90"), "H4": ints.get("hksj_90"), "H2": ints.get("hksj_90"), "H6": ints.get("mh_90"),
             "H5": ints.get("mh_90_log_or"), "H9": ints.get("bootstrap_90")}[hypothesis]
    return _log_pair(value) if hypothesis == "H6" else value


def bootstrap_only90(hypothesis, result):
    """H5 and H6: the creator-bootstrap percentile 90% interval alone (the MH interval before 2026-11-21 04:55 (j)), so the
    battery shows what the wider interval changes; None for the other hypotheses."""
    ints = result.get("intervals") or {}
    if hypothesis == "H5":
        return ints.get("bootstrap_90_log_or")
    if hypothesis == "H6":
        return _log_pair(ints.get("bootstrap_90_mh"))
    return None


def registered95(hypothesis, result):
    ints = result.get("intervals") or {}
    value = ints.get("hksj_95") or ints.get("mh_95") or ints.get("mh_95_log_or")
    return _log_pair(value) if hypothesis == "H6" else value


def experiment_cfg(hypothesis, effect, scenario=None):
    return dict({"exact": True, EFFECT[hypothesis]: effect}, **SCENARIO_CFG.get(scenario, {}))


def task(spec):
    """One chunk of repetitions of one experiment. spec: (hypothesis, scenario, n, effect, first rep, reps)."""
    hypothesis, scenario, n, effect, first, reps = spec
    started = time.time()
    if scenario == "target":
        return {"spec": spec, "target": large_sample_target(hypothesis, effect), "seconds": time.time() - started}
    yardstick, bands, h2_parts = calibration_constants(hypothesis)
    rows = []
    for rep in range(first, first + reps):
        seed = stats.seed_for("sim", hypothesis, scenario, n, effect, rep)
        b = cohort(seed, n, experiment_cfg(hypothesis, effect, scenario), n_seen=40 if hypothesis == "H9" else 0,
                   parts=PARTS[hypothesis])
        result = _run_one(hypothesis, b, seed, light=True, yardstick=yardstick, bands=bands, parts=h2_parts)
        extra = h6_comparison_ps(b, result, (hypothesis, "sim", seed)) if hypothesis == "H6" else {}
        rows.append(dict({"p": result.get("p"), "estimate": primary_estimate(hypothesis, result), "determinable": result.get("determinable"),
                          "eligible": (result.get("eligibility") or {}).get("creators"), "a5": a5_interval(hypothesis, result),
                          "a5_bootstrap_only": bootstrap_only90(hypothesis, result),
                          "registered95": registered95(hypothesis, result), "conditions": result.get("conditions")},
                         **guarded_row(result), **extra))
    return {"spec": spec, "rows": rows, "seconds": time.time() - started}


def large_sample_target(hypothesis, effect, reps=3):
    """What the estimator converges to under the generator, label error included: the mean estimate over a few large
    synthetic designs (240 creators; H9: 60 hold-out and 60 seen creators). Coverage is measured against it; bias is
    reported against the planted value as well, which shows the attenuation by label error."""
    yardstick, bands, h2_parts = calibration_constants(hypothesis)
    values = []
    for rep in range(reps):
        n, seen = (60, 60) if hypothesis == "H9" else (240, 0)
        b = cohort(stats.seed_for("target", hypothesis, effect, rep), n, experiment_cfg(hypothesis, effect), n_seen=seen,
                   parts=PARTS[hypothesis])
        if hypothesis == "H9":
            result = h9_family.analyse(b, label=("target", rep), extras=False, draws=10, permutations=10)
        else:
            result = _run_one(hypothesis, b, ("target", rep), light=True, yardstick=yardstick, bands=bands, parts=h2_parts)
        value = primary_estimate(hypothesis, result)
        if value is not None:
            values.append(value)
    return stats.mean(values)


def planted_value(hypothesis, effect):
    if hypothesis == "H6":
        return math.log(effect)
    if hypothesis == "H2":
        return h2_truth(effect)
    if hypothesis == "H9":
        return None
    return effect


def h2_truth(beta, creators=4000, seed=7):
    """Population mean of creator D under the generator without label error: exact D per creator from the distribution
    of the observed score (each part YES at STATEMENT or CONTEXT with probability 0.25 / 0.97 * 0.95, given no cannot-tell
    part), averaged over creators."""
    r = random.Random(seed)
    q = 0.25 / 0.97 * 0.95
    px = [math.comb(5, x) * q ** x * (1 - q) ** (5 - x) for x in range(6)]
    total = 0.0
    for _ in range(creators):
        a, b = r.gauss(1.0, 0.5), r.gauss(beta, DEFAULT["tau2"])
        pi = [logistic(a + b * (x - 1.2)) for x in range(6)]
        num = sum(px[i] * pi[i] * px[j] * (1 - pi[j]) * ((i > j) - (i < j)) for i in range(6) for j in range(6))
        den = sum(px[i] * pi[i] for i in range(6)) * sum(px[j] * (1 - pi[j]) for j in range(6))
        total += num / den
    return total / creators


def summarise(hypothesis, scenario, n, effect, rows, target, planted):
    level_first = K.ALPHA / K.HOLM_M
    ps = [row["p"] for row in rows if row["p"] is not None and row["determinable"]]
    est = [row["estimate"] for row in rows if row["estimate"] is not None]
    out = {"hypothesis": hypothesis, "scenario": scenario, "creators": n, "planted_parameter": effect, "reps": len(rows),
           "determinable_share": sum(1 for row in rows if row["determinable"]) / len(rows),
           "reject_0.005": sum(p <= level_first for p in ps) / len(ps) if ps else None,
           "reject_0.05": sum(p <= 0.05 for p in ps) / len(ps) if ps else None,
           "mc_se_0.005": math.sqrt(level_first * (1 - level_first) / len(ps)) if ps else None,
           "mc_se_0.05": math.sqrt(0.05 * 0.95 / len(ps)) if ps else None,
           "mean_estimate": stats.mean(est), "sd_estimate": stats.sd(est), "target": target, "planted_value": planted,
           "mean_eligible": stats.mean([row["eligible"] or 0 for row in rows])}
    if target is not None and est:
        out["bias_vs_target"] = out["mean_estimate"] - target
        if planted is not None:
            out["bias_vs_planted"] = out["mean_estimate"] - planted
        for name in ("a5", "a5_bootstrap_only", "registered95"):
            inside = [row[name][0] <= target <= row[name][1] for row in rows if row.get(name) and row[name][0] is not None]
            out["coverage_" + name] = sum(inside) / len(inside) if inside else None
            out["intervals_" + name] = len(inside)
    supported = 0
    for row in rows:
        c = row["conditions"] or {}
        if row["determinable"] and row["p"] is not None and row["p"] <= level_first and c.get("registered") and c.get("a5") \
                and c.get("effect_size"):
            supported += 1
    out["supported_at_first_holm_step"] = supported / len(rows)
    # H6 only (registry 11:08 (1)): the halves of the amended p and the references it replaced, on the same sets
    for key, _ in H6_COMPARISON_PS:
        values = [row[key] for row in rows if row.get(key) is not None and row["determinable"]]
        if values:
            name = key[2:]
            out["reject_0.005_" + name] = sum(p <= level_first for p in values) / len(values)
            out["reject_0.05_" + name] = sum(p <= 0.05 for p in values) / len(values)
    largest = [row["largest_cluster"] for row in rows if row.get("largest_cluster") is not None and row["determinable"]]
    if largest:
        out["mean_largest_cluster"] = stats.mean(largest)
    # the A10 guard: the larger of the two p values, and support only when both versions meet the conditions
    guarded = [row for row in rows if row.get("p_guarded") is not None]
    if guarded:
        determinable = [row for row in guarded if row["determinable"]]
        out["reject_0.005_guarded"] = (sum(row["p_guarded"] <= level_first for row in determinable) / len(determinable)
                                       if determinable else None)
        out["reject_0.05_guarded"] = (sum(row["p_guarded"] <= 0.05 for row in determinable) / len(determinable)
                                      if determinable else None)
        out["supported_at_first_holm_step_guarded"] = sum(
            1 for row in guarded if row["p_guarded"] <= level_first and row["both_versions_meet_support_conditions"]) / len(rows)
    return out


def plan(quick=False):
    """The experiments: (hypothesis, scenario, n, effect, reps).
    Sizes: 2,000 null sets (Monte Carlo SE 0.0016 at the first Holm step, 0.0049 at 0.05) and 500 planted sets (SE about
    0.013 on a coverage of 0.90); H9, five times dearer, 1,000 and 200. Halved on 2026-11-20 23:55 local from 4,000 and
    1,000 (H9 2,000 and 400) when the revised code (registered and amended versions under the A10 guard) put the full
    sizes at about 4.8 hours on the four workers the resource guard allows. H6 also has the null scenarios
    "null_heterogeneous" (ask rates that differ between recordings, registry 2026-11-21 06:44 (3)),
    "null_sparse_low_share" (claimed shares below one half and 1 to 3 asks per creator, registry 2026-11-21 09:19 (1))
    "null_burst" (bursts of 2 to 4 asks in one voice, claimed shares 0.3 to 0.7, registry 2026-11-21 11:08 (1)) and
    "null_gapped" (one burst of 2 to 4 asks in one voice a creator, consecutive asks 1 to 3 units apart, claimed shares
    below one half, registry 2026-11-21 12:52 (1)), with the null sizes."""
    reps_null = {"H1": 2000, "H4": 2000, "H6": 2000, "H2": 2000, "H5": 2000, "H9": 1000}
    reps_plant = {"H1": 500, "H4": 500, "H6": 500, "H2": 500, "H5": 500, "H9": 200}
    if quick:
        reps_null = {key: 30 for key in reps_null}
        reps_plant = {key: 15 for key in reps_plant}
    out = []
    for hypothesis in ("H1", "H2", "H4", "H5", "H6", "H9"):
        for n in (12, 17):
            out.append((hypothesis, "null", n, NULL[hypothesis], reps_null[hypothesis]))
            if hypothesis == "H6":                   # registry 06:44 (3), 09:19 (1), 11:08 (1): H6's further nulls
                for scenario in H6_NULL_SCENARIOS[1:]:
                    out.append((hypothesis, scenario, n, NULL[hypothesis], reps_null[hypothesis]))
            for name, effect in zip(("plant_sesoi", "plant_large"), PLANT[hypothesis]):
                out.append((hypothesis, name, n, effect, reps_plant[hypothesis]))
    return out


def task_cost(spec):
    """Expected seconds of a task in one worker, from sim_cost (measured seconds a repetition at 12 and 17 creators; H9's
    follow H9_BATTERY_BOOTSTRAP_DRAWS). Only the ETA, the planned wall time and the order of the tasks use it; sim_cost.py
    is outside TASK_MODULES, so recalibrating it changes no fingerprint, and run() assembles the table in a fixed order."""
    return sim_cost.task_seconds(spec, H9_BATTERY_BOOTSTRAP_DRAWS)


def plan_estimate(workers, quick=False, chunk=100):
    """Planned CPU and wall seconds of the battery on `workers` workers, with the task fingerprint (run.py simulate
    --estimate); runs nothing."""
    out = sim_cost.estimate(tasks_for(quick, chunk), workers, H9_BATTERY_BOOTSTRAP_DRAWS)
    out["fingerprint"] = task_fingerprint()
    return out


def tasks_for(quick=False, chunk=100):
    experiments = plan(quick)
    tasks, targets_needed = [], set()
    for hypothesis, scenario, n, effect, reps in experiments:
        targets_needed.add((hypothesis, effect))
        size = max(1, min(chunk if hypothesis != "H9" else max(1, chunk // 4), reps))
        for first in range(0, reps, size):
            tasks.append((hypothesis, scenario, n, effect, first, min(size, reps - first)))
    tasks = [(h, "target", 0, e, 0, 0) for h, e in sorted(targets_needed)] + tasks
    tasks.sort(key=lambda t: -task_cost(t))                          # largest first, so that the ETA settles early
    return tasks


TASK_MODULES = ("adapter.py", "common.py", "constants.py", "features.py", "h1_rate.py", "h2_hedging.py", "h4_contraction.py",
                "h5_world_claims.py", "h6_asks.py", "h9_family.py", "simulate.py", "stats.py", "tipping.py", "verdicts.py",
                "voice_sets.py", "wording.py")


def task_fingerprint():
    """sha256 over the modules a task's result depends on (run.py, report.py, progress.py and sim_cost.py only schedule
    and print). A checkpoint line is reused only under the same fingerprint."""
    hashes = adapter.code_hashes()
    text = "|".join(f"{name}:{hashes[name]}" for name in TASK_MODULES if name in hashes)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def require_fingerprint(expected):
    """The task fingerprint, if `expected` is it (in full or its first 12 or more hexadecimal digits, any case); else
    SystemExit naming both. run.py simulate --expect-fingerprint calls it before anything runs, so a battery starts only
    on the code the lead declared frozen."""
    actual = task_fingerprint()
    wanted = str(expected).strip().lower()
    if len(wanted) < 12 or not actual.startswith(wanted):
        raise SystemExit(f"simulate: the task fingerprint is {actual}, not the frozen {expected}: a module of "
                         f"simulate.TASK_MODULES changed after the freeze, so the battery does not start")
    return actual


def task_key(spec):
    return json.dumps(list(spec))


def read_checkpoint(path, fingerprint):
    """{task key: result} of the lines written under this fingerprint; a torn last line is skipped."""
    done = {}
    if path is None or not Path(path).is_file():
        return done
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if item.get("fingerprint") == fingerprint:
            done[item["key"]] = item["result"]
    return done


def run(workers, quick=False, chunk=100, status_path=None, checkpoint_path=None):
    """The battery. With checkpoint_path, every finished task is appended there (by the parent, one line each) and a
    rerun of the same command skips the tasks found there under the same code fingerprint. Results do not depend on
    resuming: each repetition's data come from its own seed."""
    tasks = tasks_for(quick, chunk)
    fingerprint = task_fingerprint()
    done = read_checkpoint(checkpoint_path, fingerprint)
    todo = [spec for spec in tasks if task_key(spec) not in done]
    handle = open(checkpoint_path, "a", encoding="utf-8") if checkpoint_path else None

    def keep(spec, result):
        if handle:
            handle.write(json.dumps({"fingerprint": fingerprint, "key": task_key(spec), "result": result}) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    try:
        fresh, summary = progress.parallel_map(task, todo, workers, "simulation", cost=task_cost, status_path=status_path,
                                               on_result=keep, prior_tasks=len(tasks) - len(todo),
                                               prior_cost=sum(task_cost(spec) for spec in tasks if task_key(spec) in done),
                                               total_tasks=len(tasks))
    finally:
        if handle:
            handle.close()
    by_key = dict(done)
    by_key.update({task_key(spec): result for spec, result in zip(todo, fresh)})
    # a fixed order (experiment, then first repetition), not the cost model's, so that the rows of an experiment reach
    # summarise in repetition order however the tasks were scheduled or resumed
    results = [by_key[task_key(spec)] for spec in sorted(tasks, key=lambda t: (t[0], t[1], t[2], t[3], t[4]))]
    summary["fingerprint"] = fingerprint
    targets, grouped, seconds = {}, {}, 0.0
    for result in results:
        h, s, n, e = result["spec"][:4]
        seconds += result["seconds"]
        if s == "target":
            targets[(h, e)] = result["target"]
        else:
            grouped.setdefault((h, s, n, e), []).extend(result["rows"])
    table = []
    for key in sorted(grouped, key=lambda k: (k[0], k[2], k[1])):
        h, s, n, e = key
        planted = 0.0 if s == "null" else planted_value(h, e)
        table.append(summarise(h, s, n, e, grouped[key], targets[(h, e)], planted))
    summary["cpu_seconds_in_tasks"] = round(seconds, 1)
    summary["tasks_total"] = len(tasks)
    return table, summary


# ---------------------------------------------------------------- boundary checks

def boundary_table():
    """Verdicts at the "not determinable" boundary: each hypothesis one creator below its minimum and at it, with a large
    planted effect, so that only the count changes."""
    out = []
    cases = {"H1": [11, 12], "H4": [11, 12], "H6": [11, 12], "H2": [8, 9], "H5": [11, 12], "H9": [7, 8]}
    for hypothesis, sizes in cases.items():
        yardstick, bands, h2_parts = calibration_constants(hypothesis)
        for n in sizes:
            b = cohort(stats.seed_for("boundary", hypothesis, n), n, experiment_cfg(hypothesis, PLANT[hypothesis][1]),
                       n_seen=40 if hypothesis == "H9" else 0, parts=PARTS[hypothesis])
            result = _run_one(hypothesis, b, ("boundary", n), light=True, yardstick=yardstick, bands=bands, parts=h2_parts)
            final, _ = verdicts.finalise({hypothesis: result})
            elig = result.get("eligibility") or {}
            out.append({"hypothesis": hypothesis, "generated_creators": n, "eligible": elig.get("creators"), "minimum": elig.get("minimum"),
                        "determinable": result.get("determinable"), "raw_p": result.get("p"),
                        "registered_version_p": (result.get("registered_version") or {}).get("p"),
                        "holm_input_p": final[hypothesis]["holm_input_p"], "verdict": final[hypothesis]["verdict"],
                        "uninformative": final[hypothesis]["uninformative"]})
    return out


# ---------------------------------------------------------------- H6's reference on constructed numbers (09:19 (1))
#
# Exact rejection rates under the per-recording null (given every recording's T_i, a_i ~ Binomial(T_i, s_i)) of the
# creator sign-flip of OE (H6's reference from 06:44 (3) until 09:19 (1)) and of the conditional Monte Carlo reference
# that replaced it (h6_asks.conditional_p), on constructed creators: no generator, no label, no draw. A creator is a list
# of (T_i, s_i), one per recording with asks.

def _binomial_pmf(n, p):
    return [math.comb(n, a) * p ** a * (1 - p) ** (n - a) for a in range(n + 1)]


def _binomial_cdf(k, n, p):
    """P(Binomial(n, p) <= k)."""
    if k < 0:
        return 0.0
    if k >= n or p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    return stats.betainc(n - k, k + 1, 1.0 - p)


def _creator_outcomes(recordings):
    """One creator's distribution of a (its claimed asks, summed over its recordings) and its centre sum_i T_i s_i."""
    dist = [1.0]
    for t_i, s_i in recordings:
        pmf = _binomial_pmf(t_i, s_i)
        out = [0.0] * (len(dist) + len(pmf) - 1)
        for i, x in enumerate(dist):
            for j, y in enumerate(pmf):
                out[i + j] += x * y
        dist = out
    return dist, sum(t_i * s_i for t_i, s_i in recordings)


def largest_count_rejected(alpha, draws):
    """The largest b (draws at or beyond the observed value) with (b + 1) / (draws + 1) <= alpha, as the code compares
    them; -1 if none."""
    b = int(math.floor(alpha * (draws + 1))) + 1
    while b >= 0 and (b + 1) / (draws + 1) > alpha:
        b -= 1
    return b


def h6_conditional_level(creators, alphas=(K.ALPHA / K.HOLM_M, 0.05), draws=H6_BATTERY_REFERENCE_DRAWS):
    """Exact rejection rates under the per-recording null of the one-sided conditional Monte Carlo test with `draws`
    draws (b ~ Binomial(draws, F(S)) given the observed S, F(v) = P(S <= v) under the null; rejected when b is at most
    largest_count_rejected) and of the exact conditional test it approximates (rejected when F(S) <= alpha). S is the
    integer statistic of h6_asks._integer_statistic, so ties are exact. Returns {"monte_carlo": {alpha: rate},
    "exact_conditional": {alpha: rate}}."""
    lcm = 1
    for recordings in creators:
        total = sum(t_i for t_i, _ in recordings)
        lcm = lcm * total // math.gcd(lcm, total)
    dist = {0: 1.0}
    for recordings in creators:
        weight = lcm // sum(t_i for t_i, _ in recordings)
        pmf, _ = _creator_outcomes(recordings)
        new = {}
        for value, prob in dist.items():
            for a, q in enumerate(pmf):
                if q:
                    new[value + weight * a] = new.get(value + weight * a, 0.0) + prob * q
        dist = new
    cumulative, below = 0.0, {}
    for value in sorted(dist):
        cumulative += dist[value]
        below[value] = cumulative
    out = {"monte_carlo": {}, "exact_conditional": {}, "draws": draws}
    for alpha in alphas:
        k0 = largest_count_rejected(alpha, draws)
        out["monte_carlo"][alpha] = sum(prob * _binomial_cdf(k0, draws, below[value]) for value, prob in dist.items())
        out["exact_conditional"][alpha] = sum(prob for value, prob in dist.items() if below[value] <= alpha)
    return out


def h6_signflip_level(creators, alphas=(K.ALPHA / K.HOLM_M, 0.05), limit=200000):
    """Exact rejection rates under the per-recording null of the one-sided creator sign-flip of OE (stats.signflip_p,
    exact up to 20 creators): every joint outcome of the creators' claimed asks, identical creators taken together by
    their multinomial counts. None if more than `limit` joint outcomes."""
    import itertools
    kinds = {}
    for recordings in creators:
        key = tuple(sorted(recordings))
        kinds[key] = kinds.get(key, 0) + 1
    per_kind = []
    for recordings, count in sorted(kinds.items()):
        pmf, centre = _creator_outcomes(recordings)
        total = sum(t_i for t_i, _ in recordings)
        values = [(a - centre) / total for a in range(total + 1)]
        options = []
        for counts in _compositions(count, total + 1):
            prob = math.factorial(count)
            for a, c in enumerate(counts):
                prob = prob / math.factorial(c) * pmf[a] ** c
            options.append((prob, [v for v, c in zip(values, counts) for _ in range(c)]))
        per_kind.append(options)
    size = 1
    for options in per_kind:
        size *= len(options)
    if size > limit:
        return None
    rates = {alpha: 0.0 for alpha in alphas}
    for combo in itertools.product(*per_kind):
        prob, values = 1.0, []
        for p_kind, v_kind in combo:
            prob *= p_kind
            values += v_kind
        if prob == 0.0:
            continue
        p, _ = stats.signflip_p(values, "less")
        for alpha in alphas:
            if p <= alpha:
                rates[alpha] += prob
    return {"exact": rates, "joint_outcomes": size}


def _compositions(n, bins):
    """Every way to put n identical creators into `bins` outcome bins (tuples of counts)."""
    if bins == 1:
        yield (n,)
        return
    for first in range(n + 1):
        for rest in _compositions(n - first, bins - 1):
            yield (first,) + rest


def h6_level_cases():
    """The constructed cases of registry 2026-11-21 09:19 (1): 17 creators with 1 to 3 asks at claimed shares 0.2 to 0.5
    (one recording each, all alike; T cycled 1, 2, 3; shares cycled 0.2 to 0.5 with one ask; two recordings each), and
    the A10 verifier's 12 creators of one ask at a share of 0.3."""
    shares = (0.2, 0.3, 0.4, 0.5)
    cases = []
    for t in (1, 2, 3):
        for s in shares:
            cases.append((f"17 creators, T = {t}, s = {s}", [[(t, s)] for _ in range(17)]))
    for s in shares:
        cases.append((f"17 creators, T cycled 1, 2, 3, s = {s}", [[(1 + c % 3, s)] for c in range(17)]))
    cases.append(("17 creators, T = 1, s cycled 0.2 to 0.5", [[(1, shares[c % 4])] for c in range(17)]))
    cases.append(("17 creators, two recordings (T_i = 1 at s = 0.2, T_i = 2 at s = 0.4)", [[(1, 0.2), (2, 0.4)] for _ in range(17)]))
    cases.append(("12 creators, T = 1, s = 0.3", [[(1, 0.3)] for _ in range(12)]))
    return cases


def h6_reference_levels(cases=None, draws=H6_BATTERY_REFERENCE_DRAWS):
    """The table of registry 2026-11-21 09:19 (1): for each constructed case the exact rejection rates at 0.005 and 0.05
    of the sign-flip of OE, of the conditional Monte Carlo reference with `draws` draws and of the exact conditional
    test, under the per-recording null."""
    rows = []
    for name, creators in (cases or h6_level_cases()):
        flip = h6_signflip_level(creators)
        cond = h6_conditional_level(creators, draws=draws)
        level = K.ALPHA / K.HOLM_M
        rows.append({"case": name, "creators": len(creators),
                     "signflip_0.005": flip["exact"][level] if flip else None, "signflip_0.05": flip["exact"][0.05] if flip else None,
                     "joint_outcomes": flip["joint_outcomes"] if flip else None,
                     "conditional_mc_0.005": cond["monte_carlo"][level], "conditional_mc_0.05": cond["monte_carlo"][0.05],
                     "exact_conditional_0.005": cond["exact_conditional"][level],
                     "exact_conditional_0.05": cond["exact_conditional"][0.05], "draws": draws})
    return rows


# ---------------------------------------------------------------- H6's amended p on constructed numbers (11:08 (1))
#
# Exact rejection rates under the cluster null (each cluster of a recording's asks in the claimed voice with the
# recording's claimed share s_i, all its asks with it, independently between clusters) of the p values of registry
# 2026-11-21 11:08 (1): the cluster-level conditional Monte Carlo p, the ask-level conditional Monte Carlo p of 09:19 (1),
# the creator sign-flip p of OE, and the amended p, the larger of the cluster p and the sign-flip p. A creator is a list
# of recordings (s_i, [cluster sizes]); a cluster of one is a single ask, so the sparse and plain cases are the
# per-recording null of 09:19 (1). Since 12:52 (1) a recording may also state the sizes the cluster rule sees, (s_i,
# [true sizes], [seen sizes]): the gapped cases, bursts whose asks lie some units apart. No generator, no label, no draw.

def binomial_cdf_small(k, n, p):
    """P(Binomial(n, p) <= k), the terms summed in logs (for k small against n; exact to rounding for any n)."""
    if k < 0:
        return 0.0
    if k >= n or p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    log_p, log_q, base = math.log(p), math.log1p(-p), math.lgamma(n + 1)
    terms = [base - math.lgamma(j + 1) - math.lgamma(n - j + 1) + j * log_p + (n - j) * log_q for j in range(k + 1)]
    top = max(terms)
    return min(1.0, math.exp(top) * math.fsum(math.exp(term - top) for term in terms))


def _law_of_statistic(pmfs, weights):
    """{S: probability} of S = sum_c weight_c a_c, the a_c independent with the laws pmfs[c] on 0, 1, ..."""
    dist = {0: 1.0}
    for pmf, weight in zip(pmfs, weights):
        new = {}
        for value, prob in dist.items():
            for a, q in enumerate(pmf):
                if q:
                    new[value + weight * a] = new.get(value + weight * a, 0.0) + prob * q
        dist = new
    return dist


def _lower_tail(dist):
    """v -> P(S <= v) under the law dist, for any whole number v."""
    values = sorted(dist)
    cumulative, running = [], 0.0
    for value in values:
        running += dist[value]
        cumulative.append(running)

    def tail(v):
        index = bisect.bisect_right(values, v)
        return cumulative[index - 1] if index else 0.0
    return tail


def _seen_sizes(recording):
    """The cluster sizes the test sees in one constructed recording: (s_i, [true sizes]) or (s_i, [true sizes], [seen
    sizes]) (registry 12:52 (1): a burst whose asks lie further apart than the window is seen as several clusters)."""
    return list(recording[2]) if len(recording) > 2 else list(recording[1])


def h6_cluster_levels(creators, alphas=(K.ALPHA / K.HOLM_M, 0.05), draws=h6_asks.REFERENCE_DRAWS, limit=300000):
    """creators: per creator its recordings (s_i, [cluster sizes]) or (s_i, [true cluster sizes], [the sizes the cluster
    rule sees]): the data come from the true clusters (each in the claimed voice with s_i, all its asks with it), the
    test's reference from the clusters it sees (registry 2026-11-21 12:52 (1): a burst whose asks lie further apart than
    the window is seen as several clusters; h6_gapped_recording). Exact rejection rates under that null, at each
    alpha, of: "cluster", the cluster-level conditional Monte Carlo test with `draws` draws (h6_asks.conditional_p by
    "cluster": b ~ Binomial(draws, F(S)) given the observed S, F the distribution function of the seen clusters' null
    law; rejected when b is at most largest_count_rejected); "cluster_exact", the exact conditional test it approximates
    (F(S) <= alpha); "ask_level", the conditional Monte Carlo test that draws asks one by one (09:19 (1));
    "signflip", the creator sign-flip of OE (stats.signflip_p); "amended", the larger of the cluster p and the sign-flip
    p (h6_asks.amended_p: both reject). S is h6_asks._integer_statistic's whole number, so ties are exact. The last two
    by enumeration of the creators' joint outcomes, identical creators taken together by their multinomial counts; None
    above `limit` joint outcomes."""
    import itertools
    per = []
    for recordings in creators:
        true_units = [(size, recording[0]) for recording in recordings for size in recording[1]]
        seen_units = [(size, recording[0]) for recording in recordings for size in _seen_sizes(recording)]
        ask_units = [(1, share) for size, share in true_units for _ in range(size)]
        if sum(size for size, _ in seen_units) != sum(size for size, _ in true_units):
            raise ValueError("the seen cluster sizes must sum to the true ones")
        per.append((sum(size for size, _ in true_units), h6_asks.creator_pmf(true_units), h6_asks.creator_pmf(ask_units),
                    sum(size * share for size, share in true_units), h6_asks.creator_pmf(seen_units)))
    lcm = 1
    for total, _, _, _, _ in per:
        lcm = lcm * total // math.gcd(lcm, total)
    weights = [lcm // total for total, _, _, _, _ in per]
    law = _law_of_statistic([pmf for _, pmf, _, _, _ in per], weights)
    cluster_tail = _lower_tail(_law_of_statistic([pmf for _, _, _, _, pmf in per], weights))
    ask_tail = _lower_tail(_law_of_statistic([pmf for _, _, pmf, _, _ in per], weights))
    cut = {alpha: largest_count_rejected(alpha, draws) for alpha in alphas}
    memo = {}

    def monte_carlo(alpha, tail):
        """P(the Monte Carlo test rejects at alpha | the null tail probability of the observed S)."""
        if (alpha, tail) not in memo:
            memo[(alpha, tail)] = binomial_cdf_small(cut[alpha], draws, tail)
        return memo[(alpha, tail)]

    out = {"draws": draws, "cluster": {}, "cluster_exact": {}, "ask_level": {}, "signflip": None, "amended": None}
    for alpha in alphas:
        out["cluster"][alpha] = sum(prob * monte_carlo(alpha, cluster_tail(value)) for value, prob in law.items())
        out["cluster_exact"][alpha] = sum(prob for value, prob in law.items() if cluster_tail(value) <= alpha + 1e-15)
        out["ask_level"][alpha] = sum(prob * monte_carlo(alpha, ask_tail(value)) for value, prob in law.items())
    kinds = {}
    for index, recordings in enumerate(creators):
        kinds.setdefault(tuple(sorted((recording[0], tuple(sorted(recording[1])), tuple(sorted(_seen_sizes(recording))))
                                      for recording in recordings)), []).append(index)
    per_kind = []
    for _, members in sorted(kinds.items()):
        total, pmf, _, centre, _ = per[members[0]]
        weight = weights[members[0]]
        support = [a for a, q in enumerate(pmf) if q > 0]
        options = []
        for counts in _compositions(len(members), len(support)):
            prob, values, value = float(math.factorial(len(members))), [], 0
            for a, count in zip(support, counts):
                prob = prob / math.factorial(count) * pmf[a] ** count
                values += [(a - centre) / total] * count
                value += weight * a * count
            options.append((prob, values, value))
        per_kind.append(options)
    size = 1
    for options in per_kind:
        size *= len(options)
    out["joint_outcomes"] = size
    if size > limit:
        return out
    flip, both = {alpha: 0.0 for alpha in alphas}, {alpha: 0.0 for alpha in alphas}
    for combo in itertools.product(*per_kind):
        prob, values, value = 1.0, [], 0
        for kind_prob, kind_values, kind_value in combo:
            prob *= kind_prob
            values += kind_values
            value += kind_value
        if prob == 0.0:
            continue
        p_flip, _ = stats.signflip_p(values, "less")
        tail = cluster_tail(value)
        for alpha in alphas:
            if p_flip <= alpha:
                flip[alpha] += prob
                both[alpha] += prob * monte_carlo(alpha, tail)
    out["signflip"], out["amended"] = flip, both
    return out


def h6_cluster_level_cases():
    """The constructed cases of registry 2026-11-21 11:08 (1), as (kind, name, creators): bursts (clusters of 2 to 4 asks
    in one voice at shares 0.3 to 0.7), the sparse low-share cases of 09:19 (1) (single asks, 1 to 3 a creator, shares
    0.2 and 0.3) and plain cases (single asks, shares near one half); and the gapped cases of 12:52 (1)
    (h6_gapped_level_cases)."""
    def alike(n, recordings):
        return [[(share, list(sizes)) for share, sizes in recordings] for _ in range(n)]
    cases = [("burst", f"17 creators, one burst of 3, s = {s}", alike(17, [(s, [3])])) for s in (0.3, 0.5, 0.7)]
    cases += [("burst", "17 creators, one burst of 2, s = 0.3", alike(17, [(0.3, [2])])),
              ("burst", "17 creators, one burst of 4, s = 0.5", alike(17, [(0.5, [4])])),
              ("burst", "12 creators, one burst of 3, s = 0.3", alike(12, [(0.3, [3])])),
              ("burst", "17 creators, three bursts of 2, s = 0.5", alike(17, [(0.5, [2, 2, 2])])),
              ("burst", "17 creators, three bursts of 2, s = 0.3", alike(17, [(0.3, [2, 2, 2])])),
              ("burst", "17 creators, bursts of 2 and 4, s = 0.7", alike(17, [(0.7, [2, 4])])),
              ("burst", "17 creators, a burst of 3 at s = 0.3 and one ask at s = 0.6 (two recordings)",
               alike(17, [(0.3, [3]), (0.6, [1])]))]
    cases += [("sparse_low_share", f"17 creators, T = {t} single asks, s = {s}", alike(17, [(s, [1] * t)]))
              for t, s in ((1, 0.3), (2, 0.3), (3, 0.2), (1, 0.2))]
    cases += [("sparse_low_share", "12 creators, T = 1, s = 0.3", alike(12, [(0.3, [1])])),
              ("sparse_low_share", "17 creators, T cycled 1, 2, 3 single asks, s = 0.3",
               [[(0.3, [1] * (1 + c % 3))] for c in range(17)])]
    cases += [("plain", "17 creators, T = 3 single asks, s = 0.5", alike(17, [(0.5, [1] * 3)])),
              ("plain", "17 creators, T = 4 single asks, s = 0.5", alike(17, [(0.5, [1] * 4)])),
              ("plain", "12 creators, T = 4 single asks, s = 0.5", alike(12, [(0.5, [1] * 4)])),
              ("plain", "17 creators, T = 2 single asks, s = 0.6", alike(17, [(0.6, [1] * 2)])),
              ("plain", "17 creators, two recordings (2 single asks at s = 0.4, 2 at s = 0.6)",
               alike(17, [(0.4, [1, 1]), (0.6, [1, 1])]))]
    return cases + h6_gapped_level_cases()


def h6_gapped_recording(share, offsets, window=h6_asks.H6_CLUSTER_WINDOW):
    """Registry 2026-11-21 12:52 (1): one constructed recording that holds one burst (one true cluster) of asks on the
    unit offsets given (e.g. [0, 2, 4]: asks two units apart), as (s, [burst size], the cluster sizes that
    h6_asks.clusters_of sees at `window`)."""
    return (share, [len(offsets)], h6_asks.clusters_of([(offset, offset, "own") for offset in offsets], window))


def h6_gapped_level_cases():
    """The gapped cases of registry 2026-11-21 12:52 (1), as (kind, name, creators): bursts whose consecutive asks lie 1
    to 3 units apart at claimed shares below one half, under the window of 12:52 (5 units) and under 11:08's adjacency
    rule (1 unit, which sees them as single asks: the fifth verification's case), and bursts whose asks lie further
    apart than 5 units (dependence beyond the window, not modelled), under 5 units and under the 10-unit sensitivity
    row."""
    def alike(n, share, offsets, window):
        return [[h6_gapped_recording(share, offsets, window)] for _ in range(n)]
    within = (("17 creators, one burst of 3 asks 2 units apart, s = 0.3", 17, 0.3, (0, 2, 4)),
              ("17 creators, one burst of 3 asks 3 units apart, s = 0.4", 17, 0.4, (0, 3, 6)),
              ("17 creators, one burst of 2 asks 3 units apart, s = 0.3", 17, 0.3, (0, 3)),
              ("17 creators, one burst of 4 asks 1, 2 and 3 units apart, s = 0.35", 17, 0.35, (0, 1, 3, 6)),
              ("12 creators, one burst of 3 asks 2 units apart, s = 0.3", 12, 0.3, (0, 2, 4)))
    beyond = (("17 creators, one burst of 3 asks 6 units apart, s = 0.3", 17, 0.3, (0, 6, 12)),
              ("17 creators, one burst of 3 asks 2 and 7 units apart, s = 0.3", 17, 0.3, (0, 2, 9)))
    cases = []
    for window, tag in ((h6_asks.H6_CLUSTER_WINDOW, "window 5"), (1, "window 1, the rule of 11:08")):
        for name, n, share, offsets in within:
            cases.append(("gapped", f"{name} ({tag})", alike(n, share, offsets, window)))
        cases.append(("gapped", f"9 creators at s = 0.3 and 8 at s = 0.5, one burst of 3 asks 2 units apart ({tag})",
                      alike(9, 0.3, (0, 2, 4), window) + alike(8, 0.5, (0, 2, 4), window)))
    for window, tag in ((h6_asks.H6_CLUSTER_WINDOW, "window 5: beyond it"),
                        (h6_asks.H6_SENSITIVITY_WINDOW, "window 10, the sensitivity row")):
        for name, n, share, offsets in beyond:
            cases.append(("gapped_beyond_window", f"{name} ({tag})", alike(n, share, offsets, window)))
    return cases


def h6_cluster_reference_levels(cases=None, draws=h6_asks.REFERENCE_DRAWS):
    """The table of registry 2026-11-21 11:08 (1): for each constructed case the exact rejection rates at 0.005 and 0.05,
    under the cluster null, of the cluster p, the exact cluster test, the ask-level p, the sign-flip p and the amended
    p (h6_cluster_levels), with `draws` Monte Carlo draws (the analysis's 99,999 by default)."""
    level = K.ALPHA / K.HOLM_M
    rows = []
    for kind, name, creators in (cases or h6_cluster_level_cases()):
        got = h6_cluster_levels(creators, draws=draws)
        row = {"kind": kind, "case": name, "creators": len(creators), "draws": draws, "joint_outcomes": got["joint_outcomes"]}
        for key in ("cluster", "cluster_exact", "ask_level", "signflip", "amended"):
            for alpha, tag in ((level, "0.005"), (0.05, "0.05")):
                row[f"{key}_{tag}"] = got[key][alpha] if got[key] is not None else None
        rows.append(row)
    return rows
