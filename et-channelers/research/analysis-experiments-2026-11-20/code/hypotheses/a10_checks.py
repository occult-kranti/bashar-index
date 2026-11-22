"""A10.7 (registry 2026-11-21 03:08; CAL-A14 point 3): every log-ratio estimand must show, on seen creators, a mean of
zero under its reference, or be recentred, and must report recovery of a planted smallest effect.

null_means(bundle, settings) works on the seen creators of a bundle (group "seen", under the ASR-model rule) and returns
counts and means only:
  H1, H4  the sign-flip of creator means is symmetric: its null mean is zero by construction (stated, not computed).
  H2      amended: the two-sided sign-flip, zero by construction; registered: the mean of the within-creator-and-band
          permutation reference on the seen creators with 30 or more statements.
  H5      recording sides permuted within creator (the numbers of A and B recordings kept): the mean OE of the creators that
          pass the margin rule (amended) and the mean half-count log ratio difference of those that pass the per-side rule
          (registered), over the draws. A recording keeps the counts of its own side's k (CHOICE: the rescaling of whole-coded
          recordings is not redone under the permutation).
  H6      clusters of asks placed on the claimed side with probability s_i (recording i's claimed share of its words in
          the two voices), all asks of a cluster together (registry 2026-11-21 11:08 (1); every ask alone before, 06:44
          (3)), given the clusters (asks within h6_asks.H6_CLUSTER_WINDOW = 5 units of each other, chaining, registry
          12:52 (1); asks of one class on overlapping unit ranges counted once, 12:52 (2), with the count of such
          merges), in every recording: the exact expectation of the amended
          OE = (a - sum_i T_i s_i) / T (zero for every set of T_i), of CAL-A11's pooled a / T - s (shown beside it; not
          centred when the T_i are not proportional to the words), and of the registered half-count log ratio (creators
          with T = 0 included, as registered), averaged over creators; and, as the planted check, the same expectations at
          a rate ratio of 0.5. Recordings without an ask file stay in with a = b = 0, as in the analysis (registry
          2026-11-21 09:19 (3); README CHOICE 17).
  H9      the mean of the family-label reference is part of every H9 result (estimate.reference_mean).
A version whose null mean differs from zero by more than NULL_TOLERANCE times its smallest effect of interest is marked
"recentring needed"; the registered versions stay as registered under the A10 guard, which requires both versions to agree.
The smallest effect is on the scale of the version (registry 2026-11-21 09:19 (2)): for the registered versions the
log-scale SESOI (constants.UNINFORMATIVE_SESOI); for the OE versions of H5 and H6 the expected OE at the smallest effect,
given the seen creators' counts and shares:
  H6   delta_OE = mean over the creators with T >= 1 of sum_i T_i (q_i - s_i) / T, with q_i = rho s_i / (rho s_i + 1 - s_i)
       and rho = 0.5 (constants.SESOI["H6"]): the share of a recording's asks in the claimed voice when the claimed voice
       asks at half the own voice's rate per word (h6_oe_smallest_effect);
  H5   delta_OE = mean over the creators that pass the margin rule of T_B / (T_A + T_B) x (p_A - p_B), with
       logit p_A - logit p_B = theta = 0.4 (constants.SESOI["H5"]) and T_A p_A + T_B p_B = W_A + W_B (the two sides' shares
       of world claims among hits that differ by the smallest log odds ratio and give the creator's observed world-claim
       hits; T_A, T_B the hits on each side): E[OE | T_A, T_B] = p_A - (T_A p_A + T_B p_B) / (T_A + T_B) (h5_oe_smallest_effect).
  The tolerance of an OE version is NULL_TOLERANCE x |delta_OE| (at shares near one half and even sides, H5's delta_OE is
  about 0.05 and H6's about -0.17).
Planted-effect recovery of every hypothesis on synthetic creators is the simulation battery (simulate.py).
"""
import math

from . import adapter
from . import common
from . import constants as K
from . import h2_hedging, h5_world_claims, h6_asks
from . import stats
from . import voice_sets as vs

NULL_TOLERANCE = 0.10                    # share of the SESOI (on the estimand's scale) a null mean may differ from zero


def seen_only(bundle):
    return dict(bundle, recordings=[item for item in bundle["recordings"] if item.get("group") == "seen"])


def _flag(value, sesoi):
    """sesoi: the smallest effect on the scale of `value` (its magnitude counts); None if either is missing."""
    if value is None or sesoi is None:
        return None
    return "recentring needed" if abs(value) > NULL_TOLERANCE * abs(sesoi) else "centred"


def _expit(x):
    return 1.0 / (1.0 + math.exp(-x))


def h6_oe_smallest_effect(shares, rho=K.SESOI["H6"]):
    """Registry 2026-11-21 09:19 (2): H6's smallest effect on the OE scale. shares: per creator with T >= 1, its
    recordings' (T_i, s_i). delta_OE = mean over creators of sum_i T_i (q_i - s_i) / T, q_i = rho s_i / (rho s_i + 1 - s_i)
    (the expected OE given the T_i when the claimed voice asks at rho times the own voice's rate per word)."""
    values = []
    for rows in shares:
        total = sum(t_i for t_i, _ in rows)
        if total:
            values.append(sum(t_i * (rho * s_i / (rho * s_i + 1 - s_i) - s_i) for t_i, s_i in rows) / total)
    return common.mean_or_none(values)


def _side_shares(world, side_a, side_b, theta):
    """p_A and p_B with logit p_A - logit p_B = theta and side_a p_A + side_b p_B = world (bisection on logit p_B)."""
    low, high = -50.0, 50.0
    for _ in range(200):
        mid = (low + high) / 2.0
        if side_a * _expit(mid + theta) + side_b * _expit(mid) < world:
            low = mid
        else:
            high = mid
    return _expit((low + high) / 2.0 + theta), _expit((low + high) / 2.0)


def h5_oe_smallest_effect(rows, theta=K.SESOI["H5"]):
    """Registry 2026-11-21 09:19 (2): H5's smallest effect on the OE scale. rows: per creator {WA, PA, WB, PB} (hits by
    side). delta_OE = mean over the creators that pass the margin rule of T_B / (T_A + T_B) x (p_A - p_B), with
    logit p_A - logit p_B = theta and T_A p_A + T_B p_B = W_A + W_B; a creator whose hits are all world claims or all
    practice adds 0. None if no creator passes."""
    values = []
    for row in rows:
        if not h5_world_claims._passes(row, K.H5_MIN_HITS_PER_GROUP, False):
            continue
        side_a, side_b = row["WA"] + row["PA"], row["WB"] + row["PB"]
        world = row["WA"] + row["WB"]
        if 0 < world < side_a + side_b:
            p_a, p_b = _side_shares(world, side_a, side_b, theta)
            values.append(side_b / (side_a + side_b) * (p_a - p_b))
        else:
            values.append(0.0)
    return common.mean_or_none(values)


def _binomial(n, prob):
    return [math.comb(n, a) * prob ** a * (1 - prob) ** (n - a) for a in range(n + 1)]


def _convolve(left, right):
    out = [0.0] * (len(left) + len(right) - 1)
    for i, x in enumerate(left):
        if x:
            for j, y in enumerate(right):
                out[i + j] += x * y
    return out


def h6_null(bundle, how=None, plant=K.SESOI["H6"]):
    """H6 under no within-recording effect: in each recording i a cluster of asks (h6_asks.clusters_of at the window of
    registry 2026-11-21 12:52 (1), 5 units; 11:08 (1)) is on the claimed side with probability s_i (its claimed share of
    its words in the two voices),
    all its asks with it, given the clusters (06:44 (3) and 09:19 drew every ask alone, the same where every cluster is a
    single ask; that version of the registered mean is shown beside it). Exact expectations,
    averaged over creators: the amended OE = (a - sum_i T_i s_i) / T (creators with T >= 1; zero for every set of T_i), the
    pooled OE of CAL-A11 before 06:44 (3) (a / T - s with s pooled over the recordings; off zero where the T_i are not
    proportional to the words), and the registered half-count log ratio (a is the sum of the recordings' binomials;
    creators with T = 0 included, as registered); and the same expectations at a planted rate ratio (the smallest effect,
    0.5). Every recording with both voices counts, a recording without an ask file with a = b = 0, as the analysis keeps it
    (registry 2026-11-21 09:19 (3)). The OE versions are flagged against a tenth of the OE value of the smallest effect at
    these creators' T_i and s_i (09:19 (2), h6_oe_smallest_effect), the registered one against a tenth of log 2."""
    tables = h6_asks.creator_tables(bundle, how or vs.definition())
    creators = [rows for _, rows in sorted(tables.items()) if rows]
    if not creators:
        return {"creators": 0, "note": "no seen recording with both voices"}
    out = {"null": {"oe": [], "pooled": [], "half": [], "half_asks": []},
           "plant": {"oe": [], "pooled": [], "half": [], "half_asks": []}}
    for rows in creators:
        t = h6_asks._sum(rows)
        n, s_pooled = t["a"] + t["b"], t["wc"] / (t["wc"] + t["wo"])
        shares = [(row["a"] + row["b"], row["wc"] / (row["wc"] + row["wo"])) for row in rows]
        centre = sum(n_i * s_i for n_i, s_i in shares)
        # registry 11:08 (1): the clusters of a recording's asks fall in one voice together (each with the recording's
        # share, or its planted share); the 09:19 null drew the asks one by one (shown beside it)
        clusters = [unit for row in rows if row["a"] + row["b"] for unit in h6_asks._draw_units(row, "cluster")]
        for name, rr in (("null", 1.0), ("plant", plant)):
            probs = [(n_i, s_i if rr == 1.0 else s_i * rr / (s_i * rr + 1 - s_i)) for n_i, s_i in shares]
            dist = h6_asks.creator_pmf([(size, s_i if rr == 1.0 else s_i * rr / (s_i * rr + 1 - s_i))
                                        for size, s_i in clusters])
            by_ask = [1.0]
            for n_i, q_i in probs:
                by_ask = _convolve(by_ask, _binomial(n_i, q_i))
            for key, law in (("half", dist), ("half_asks", by_ask)):
                out[name][key].append(sum(weight * h6_asks.half_count({"a": a, "b": n - a, "wc": t["wc"], "wo": t["wo"]})
                                          for a, weight in enumerate(law)))
            if n:
                expected_a = sum(n_i * q_i for n_i, q_i in probs)                # the same with or without clusters
                out[name]["oe"].append((expected_a - centre) / n)                 # E[(a - sum T_i s_i) / T]
                out[name]["pooled"].append(expected_a / n - s_pooled)              # E[a / T] - s, pooled
    sesoi = K.UNINFORMATIVE_SESOI["H6"]
    oe_mean, half_mean = common.mean_or_none(out["null"]["oe"]), common.mean_or_none(out["null"]["half"])
    pooled_mean = common.mean_or_none(out["null"]["pooled"])
    # registry 09:19 (2): the smallest effect on the OE scale at these creators' T_i and s_i (the pooled OE moves by the
    # same amount between the null and the plant, so the same value serves it)
    smallest = h6_oe_smallest_effect([[(row["a"] + row["b"], row["wc"] / (row["wc"] + row["wo"])) for row in rows]
                                      for rows in creators], K.SESOI["H6"])
    return {"creators": len(creators), "creators_T_ge_1": len(out["null"]["oe"]),
            "recordings": sum(len(rows) for rows in creators),
            "recordings_without_ask_file": sum(1 for rows in creators for row in rows if row.get("no_ask_file")),
            "amended_OE_null_mean": oe_mean, "amended_flag": _flag(oe_mean, smallest),
            "amended_OE": "(a - sum_i T_i s_i) / T, centred per recording (registry 2026-11-21 06:44 (3))",
            "pooled_OE_before_0644_null_mean": pooled_mean, "pooled_OE_before_0644_flag": _flag(pooled_mean, smallest),
            "OE_smallest_effect": smallest, "OE_tolerance": None if smallest is None else NULL_TOLERANCE * abs(smallest),
            "OE_smallest_effect_formula": "mean over creators with T >= 1 of sum_i T_i (q_i - s_i) / T, "
                                          "q_i = 0.5 s_i / (0.5 s_i + 1 - s_i) (rate ratio 0.5; registry 2026-11-21 09:19 (2))",
            "registered_half_count_null_mean": half_mean, "registered_flag": _flag(half_mean, sesoi),
            "registered_tolerance": NULL_TOLERANCE * sesoi,
            "registered_half_count_null_mean_asks_one_by_one_0919": common.mean_or_none(out["null"]["half_asks"]),
            "clusters": len([1 for rows in creators for row in rows for _ in row.get("clusters") or []]),
            "asks_in_clusters_of_2_or_more": sum(size for rows in creators for row in rows for size in row.get("clusters") or []
                                                 if size >= 2),
            "cluster_window_units": h6_asks.H6_CLUSTER_WINDOW,
            # registry 12:52 (2): how often asks of one class on overlapping unit ranges were counted once (counts only)
            "ask_overlaps_counted_once": adapter.ask_overlap_counts(bundle),
            "planted_rate_ratio": plant, "planted_log": math.log(plant),
            "registered_half_count_mean_at_plant": common.mean_or_none(out["plant"]["half"]),
            "amended_OE_mean_at_plant": common.mean_or_none(out["plant"]["oe"]),
            "method": "exact conditional expectation given each seen creator's clusters and s_i: each cluster of a "
                      "recording's asks (asks within 5 units of each other, registry 2026-11-21 12:52 (1)) in the claimed "
                      "voice with probability s_i, all its asks with it (11:08 (1)); the 09:19 null with the asks drawn "
                      "one by one is shown beside the registered mean; the OE means are the same under both"}


def h5_null(bundle, draws, label=("a10.7", "H5")):
    titles = (bundle.get("titles") or {}).get("final") or {}
    groups = K.H5_GROUPS["primary"]
    by_creator = {}
    for item in bundle["recordings"]:
        side = h5_world_claims.recording_side(item, titles)
        if side:
            by_creator.setdefault(item["creator"], {"A": [], "B": []})[side].append(item)
    cells = {}
    for creator in sorted(by_creator):
        sides = by_creator[creator]
        if len(sides["A"]) < K.H5_MIN_RECORDINGS_PER_SIDE or len(sides["B"]) < K.H5_MIN_RECORDINGS_PER_SIDE:
            continue
        counted = []
        for side in ("A", "B"):
            k = max(40, math.ceil(120 / len(sides[side])))
            for item in sides[side]:
                excluded, _ = h5_world_claims.self_naming_excluded(item)
                w, p, _ = h5_world_claims._counts(item, groups, k, False, (), excluded)
                counted.append((w, p))
        cells[creator] = (len(sides["A"]), counted)
    if not cells:
        return {"creators": 0}
    observed = []                                   # the creators' hits on their own sides, for the OE tolerance (09:19 (2))
    for creator in sorted(cells):
        n_a, counted = cells[creator]
        observed.append({"WA": sum(w for w, _ in counted[:n_a]), "PA": sum(p for _, p in counted[:n_a]),
                         "WB": sum(w for w, _ in counted[n_a:]), "PB": sum(p for _, p in counted[n_a:])})
    smallest = h5_oe_smallest_effect(observed, K.SESOI["H5"])
    stream = stats.rng(*label)
    oe_means, half_means = [], []
    for _ in range(draws):
        oe_values, half_values = [], []
        for creator in sorted(cells):
            n_a, counted = cells[creator]
            order = counted[:]
            stream.shuffle(order)
            row = {"WA": sum(w for w, _ in order[:n_a]), "PA": sum(p for _, p in order[:n_a]),
                   "WB": sum(w for w, _ in order[n_a:]), "PB": sum(p for _, p in order[n_a:])}
            if h5_world_claims._passes(row, K.H5_MIN_HITS_PER_GROUP, False):
                oe_values.append(h5_world_claims.oe(row))
            if h5_world_claims._passes(row, K.H5_MIN_HITS_PER_GROUP, True):
                half_values.append(h5_world_claims.half_count_value(row))
        if oe_values:
            oe_means.append(sum(oe_values) / len(oe_values))
        if half_values:
            half_means.append(sum(half_values) / len(half_values))
    oe_mean, half_mean = common.mean_or_none(oe_means), common.mean_or_none(half_means)
    return {"creators": len(cells), "draws": draws, "amended_OE_null_mean": oe_mean, "amended_flag": _flag(oe_mean, smallest),
            "OE_smallest_effect": smallest, "OE_tolerance": None if smallest is None else NULL_TOLERANCE * abs(smallest),
            "OE_smallest_effect_formula": "mean over creators passing the margin rule of T_B / (T_A + T_B) x (p_A - p_B), "
                                          "logit p_A - logit p_B = 0.4, T_A p_A + T_B p_B = W_A + W_B "
                                          "(registry 2026-11-21 09:19 (2))",
            "creators_in_OE_smallest_effect": sum(1 for row in observed
                                                  if h5_world_claims._passes(row, K.H5_MIN_HITS_PER_GROUP, False)),
            "registered_half_count_null_mean": half_mean, "registered_flag": _flag(half_mean, K.UNINFORMATIVE_SESOI["H5"]),
            "registered_tolerance": NULL_TOLERANCE * K.UNINFORMATIVE_SESOI["H5"],
            "method": "recording sides permuted within creator"}


def h2_null(bundle, bands, parts, draws, label=("a10.7", "H2")):
    if not bands or parts is None:
        return {"note": "length bands or retained parts not set"}
    by_creator = h2_hedging.statements_by_creator(bundle, bands=bands, parts=parts)
    groups = [by_creator[c] for c in sorted(by_creator) if len(by_creator[c]) >= K.H2_MIN_STATEMENTS]
    if not groups:
        return {"creators": 0}
    perm = h2_hedging.permutation_row(groups, draws, label)
    value = perm["reference_mean"]
    return {"creators": len(groups), "draws": draws, "amended": "two-sided sign-flip: null mean zero by construction",
            "registered_permutation_reference_mean": value, "registered_flag": _flag(value, K.UNINFORMATIVE_SESOI["H2"])}


def null_means(bundle, settings, draws=499):
    """A10.7 on the seen creators of the bundle. Counts and means only."""
    seen = seen_only(bundle)
    if not seen["recordings"]:
        return {"note": "no seen recordings in the bundle: the A10.7 null-mean check needs seen labels"}
    symmetric = "sign-flip of creator means: symmetric about zero, null mean zero by construction"
    return {"H1": {"amended": symmetric, "registered": symmetric},
            "H4": {"amended": symmetric, "registered": symmetric},
            "H2": h2_null(seen, tuple(settings.get("bands") or ()) or None,
                          tuple(settings["parts"]) if settings.get("parts") is not None else None, draws),
            "H5": h5_null(seen, draws),
            "H6": h6_null(seen),
            "H9": {"note": "the family-label reference mean is reported with every H9 result (estimate.reference_mean)"},
            "planted_effect_recovery": "simulation battery on synthetic creators (simulate.py; sim_out/simulation-results*.json); "
                                       "H6 also at the seen margins above",
            "tolerance": f"recentring needed when |null mean| > {NULL_TOLERANCE} x the smallest effect of interest on the "
                         "version's scale: the log-scale SESOI for the registered versions; for the OE versions of H5 and "
                         "H6 the expected OE at the smallest effect given the seen creators' counts and shares "
                         "(OE_smallest_effect, registry 2026-11-21 09:19 (2))"}
