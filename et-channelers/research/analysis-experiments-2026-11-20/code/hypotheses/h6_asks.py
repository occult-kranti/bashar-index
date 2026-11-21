"""H6. Asks to buy or enrol are rarer in the claimed voice than in the own voice of the same recording.

Registered (hypotheses.md): within-recording rate ratio of validated pay-or-enrol asks, claimed against own, third-party
adverts removed, sign-flip over creators, creator-bootstrap interval; smallest effect: ratio 0.5 or lower for "does not
sell", equivalence band 0.67 to 1.5; refuted by an interval inside 0.67 to 1.5 or a ratio above 1; not run below 12
creators with both voices. Drafted amendment A10.4 = CAL-A11 (approved in principle, A9), which this module applies,
with its centring per recording (registry 2026-11-21 06:44 (3)):
  per eligible recording i of a creator: a_i = asks in claimed spans, b_i = asks in own spans, T_i = a_i + b_i, s_i = the
  claimed share of its words in the two voices, wc_i / (wc_i + wo_i); a, b, T summed over the creator's eligible
  recordings; creators with T = 0 are excluded and counted; the creator value is OE = (a - sum_i T_i s_i) / T, whose mean
  is zero under no within-recording effect given the T_i, whatever the ask rates of the recordings (the pooled a / T - s
  of CAL-A11 is not centred when ask rates differ between recordings with different claimed shares: 06:44 (3));
  Holm p (registry 2026-11-21 11:08 (1), which amends 09:19 (1); the cluster window of 12:52 (1)): one-sided, the larger
  of two p values of the mean OE over the creators with T >= 1 (amended_p):
    - the cluster-level conditional Monte Carlo p (conditional_p, by="cluster"): a recording's counted asks are grouped
      into clusters (clusters_of: asks within H6_CLUSTER_WINDOW = 5 units of each other chain into one cluster, registry
      12:52 (1); 11:08 (1) joined only the same, overlapping or adjacent units, a window of 1); under the null each
      cluster's voice is drawn as one unit, claimed with the recording's claimed share s_i, all asks of the cluster
      following it, given the clusters; p = (b + 1) / (m + 1), m = REFERENCE_DRAWS = 99,999 Monte Carlo draws (not exact
      convolution: the support of the mean OE grows with the least common multiple of the creators' T), from a stream
      seeded by the label (reproducible; inside about 0.0045 to 0.0055 the side of 0.005 still depends on the draws,
      registry 12:52);
    - the creator sign-flip p of OE (stats.signflip_p, exact up to 20 creators), the reference of 06:44 (3) to 09:19.
  Neither carries a verdict alone: the sign-flip over-rejects where asks are few and claimed shares lie below one half
  (1.93% at the 0.005 level with 17 creators of one ask at a share of 0.3), a reference that draws asks one by one
  over-rejects bursts of asks in one voice (7.7% at the 0.005 level for 17 creators with one burst of 3 at s = 0.3), and
  the cluster p holds wherever the bursts are found by the cluster rule (simulate.h6_cluster_levels, exact enumeration on
  constructed numbers). Dependence of asks beyond the window is not modelled (CLUSTER_STATEMENT, in every result): a
  burst whose asks lie more than 5 units apart is seen as several clusters, and at claimed shares below one half both
  halves of the amended p then over-reject; a 10-unit window (H6_SENSITIVITY_WINDOW) is a sensitivity row (secondary,
  no verdict). The ask-level conditional p of 09:19 (asks drawn one by one, a_i ~ Binomial(T_i, s_i)) is shown beside
  them and enters nothing;
  estimate: the Mantel-Haenszel rate ratio with creator-by-recording strata over the same creators (its interval until
  the label-based coverage repeat: the wider of the creator-bootstrap percentile and the t interval, log ratio +-
  t(k-1) x the delete-one-creator jackknife SE; constants.MH_INTERVAL_RULE, registry 2026-11-21 04:55 (j)); A5 needs
  both the t interval on the creator OE values and that MH interval to exclude zero below (06:44 (5)); the registered
  half-count log ratio is a sensitivity row; per-creator log ratios only for T >= 5; run condition 8 or more creators
  with T >= 1 besides the registered 12 with both voices.
Registered version under the A10 guard (registry 03:08): the creator mean of half-count log rate ratios over every
creator with both voices (T = 0 included, as registered, and uncentred: registry 04:55 (k); its null mean on seen
creators is a10_checks.h6_null), sign-flip over creators, and the registered creator-bootstrap interval drawn as catalogue
rule R1 says, creators then recordings (registry 04:55 (d)).
Attribution of an ask to a voice (CHOICE): the side that holds the majority of the words of the ask's units; a tie or a
majority outside both sides puts the ask on neither side.
Clusters (registry 12:52 (1), amending 11:08 (1)): formed within a recording over every ask that passes the verdict and
class rule (CHOICE of 11:08: the asks on neither side too, so that an ask in an unlabelled unit does not split a burst),
by unit id (units are sentences, ids consecutive within a recording): an ask joins the cluster before it when its first
unit is at most H6_CLUSTER_WINDOW = 5 after the cluster's last unit (asks within 5 units of each other, about one minute
of speech, chaining); a cluster's size is its number of asks on the claimed or own side, and a cluster without one is
dropped. Asks of one pitch that lie further apart are not joined: that dependence is not modelled (CLUSTER_STATEMENT).
Asks of one class whose unit ranges overlap reach this module once (adapter.merge_overlapping_asks, registry 12:52 (2)),
so T, a, b, the MH strata and the clusters count them once.
"""
import bisect
import math

from . import adapter
from . import common
from . import constants as K
from . import stats
from . import tipping
from . import voice_sets as vs

H = "H6"
# Registry 2026-11-21 11:08 (1): Monte Carlo draws of the cluster-level conditional reference (and of the ask-level one
# shown beside it) in the analysis: 99,999, so that the decision at 0.005 does not depend on the seed (Monte Carlo SE of
# the p near 0.005 about 0.00022, against 0.0007 with 9,999); p = (b + 1) / (m + 1), so 0.005 x (m + 1) = 500 and
# 0.05 x (m + 1) = 5,000 are whole numbers and the test's level is exact at both. The battery uses the smaller
# simulate.H6_BATTERY_REFERENCE_DRAWS.
REFERENCE_DRAWS = 99999
# Registry 2026-11-21 12:52 (1): asks within this many units of each other chain into one cluster (an ask joins the
# cluster before it when its first unit is at most this many after the cluster's last unit). Units are sentences of 8 to
# 40 words (prep.UNIT_MIN, UNIT_MAX), so 5 units are about one minute of speech; asks of one pitch lie a sentence or two
# apart. 11:08 (1) joined only the same, overlapping or adjacent units, a window of 1.
H6_CLUSTER_WINDOW = 5
# Registry 2026-11-21 12:52 (1): the window of the sensitivity row (secondary, no verdict).
H6_SENSITIVITY_WINDOW = 10
# Registry 2026-11-21 12:52 (1): H6's result states that dependence of asks beyond the window is not modelled.
CLUSTER_STATEMENT = (f"H6's reference draws the voice of each cluster of asks as one unit: asks within {H6_CLUSTER_WINDOW} "
                     "units (sentences, about one minute of speech) of each other form one cluster, chaining. Dependence "
                     f"of asks beyond the window (asks of one pitch more than {H6_CLUSTER_WINDOW} units apart) is not "
                     f"modelled; a {H6_SENSITIVITY_WINDOW}-unit window is a sensitivity row (registry 2026-11-21 12:52 (1)).")


def clusters_of(spans, window=H6_CLUSTER_WINDOW):
    """Registry 2026-11-21 12:52 (1), amending 11:08 (1): the clusters of one recording's asks. spans: (first_unit,
    last_unit, side) of every ask that passes the verdict and class rule, side "claimed", "own" or None (neither side).
    Taken in the order of their units, an ask joins the cluster before it when its first unit is at most `window` after
    the cluster's last unit (H6_CLUSTER_WINDOW = 5: asks within 5 units of each other; 1, the rule of 11:08: the same
    checked unit range, overlapping ranges or adjacent units), so that clusters chain; asks on neither side join and link
    clusters but are not counted. Returns the sizes (asks on the claimed or own side) of the clusters, in unit order,
    clusters without such an ask left out; they sum to a + b."""
    if window < 0:
        raise ValueError("the cluster window is a whole number of units, 0 or more")
    sizes, last, size = [], None, 0
    for first, end, side in sorted(spans, key=lambda span: (span[0], span[1])):
        if last is not None and first <= last + window:
            last = max(last, end)
        else:
            if size:
                sizes.append(size)
            last, size = end, 0
        size += side is not None
    if size:
        sizes.append(size)
    return sizes


def _recording_counts(record, asks, how, use_fallback=False, ask_class=K.H6_ASK_CLASS, with_positions=False,
                      window=H6_CLUSTER_WINDOW):
    got = vs.sides(record, how)
    if got is None:
        return None
    side_list, _ = got
    words = vs.words_by_side(record, side_list)
    if words["claimed"] < K.H6_MIN_SIDE_WORDS or words["own"] < K.H6_MIN_SIDE_WORDS:
        return None
    position = {unit["id"]: index for index, unit in enumerate(record["units"])}
    a = b = unchecked = neither = 0
    placed, spans = [], []
    for ask in (asks or {}).get("asks", []):
        verdict, klass = ask["final"], ask["final_class"]
        if verdict == "unchecked" and use_fallback and ask["fallback"]:
            verdict, klass = ask["fallback"]["verdict"], ask["fallback"]["class"]
        if verdict == "unchecked":
            unchecked += 1
            continue
        if verdict != "ask" or klass != ask_class:
            continue
        tally = {"claimed": 0, "own": 0, None: 0}
        for unit_id in range(ask["first_unit"], ask["last_unit"] + 1):
            index = position.get(unit_id)
            if index is not None:
                tally[side_list[index]] += record["units"][index]["n_words"]
        side = "claimed" if tally["claimed"] > max(tally["own"], tally[None]) else "own" if tally["own"] > max(tally["claimed"], tally[None]) else None
        spans.append((ask["first_unit"], ask["last_unit"], side))
        if side == "claimed":
            a += 1
        elif side == "own":
            b += 1
        else:
            neither += 1
        if side and with_positions:
            placed.append((side, position.get(ask["first_unit"], 0) / max(1, len(record["units"]))))
    out = {"a": a, "b": b, "wc": words["claimed"], "wo": words["own"], "unchecked": unchecked, "neither": neither,
           "clusters": clusters_of(spans, window)}
    if with_positions:
        tenths = {}
        for unit, side in zip(record["units"], side_list):
            if side:
                tenth = min(9, int(10 * position[unit["id"]] / max(1, len(record["units"]))))
                tenths.setdefault(tenth, {"claimed": 0, "own": 0})[side] += unit["n_words"]
        out["tenths"], out["placed"] = tenths, placed
    return out


def creator_tables(bundle, how, use_fallback=False, with_positions=False, window=H6_CLUSTER_WINDOW):
    """{creator: [recording rows]} of the recordings with both voices; each row's "clusters" are formed at `window`
    (H6_CLUSTER_WINDOW unless a sensitivity row asks for another)."""
    tables = {}
    for item in bundle["recordings"]:
        if "voice" not in item:
            continue
        got = _recording_counts(item["voice"], item.get("asks"), how, use_fallback, with_positions=with_positions,
                                window=window)
        if got is None:
            continue
        if item.get("asks") is None:
            got["no_ask_file"] = True
        tables.setdefault(item["creator"], []).append(got)
    return tables


def _sum(rows):
    return {key: sum(row[key] for row in rows) for key in ("a", "b", "wc", "wo", "unchecked", "neither")}


def eligible(bundle, how):
    """Labels only: creators with both voices (300 words or more on each side of a recording), and among them the
    creators with T >= 1 (counted from ask labels, before any rate is computed). Also, per group of the bundle (before
    the confirmatory restriction, so that counts.json shows the seen recordings too), how often asks of one class on
    overlapping unit ranges were counted once (adapter.ask_overlap_counts, registry 2026-11-21 12:52 (2)), and the cluster
    window (12:52 (1)); counts only."""
    overlaps = adapter.ask_overlap_counts(bundle)
    bundle = common.confirmatory(bundle)
    tables = creator_tables(bundle, how)
    with_ask = sum(1 for rows in tables.values() if _sum(rows)["a"] + _sum(rows)["b"] >= 1)
    out = common.eligibility(H, len(tables), sum(len(rows) for rows in tables.values()),
                             {"creators_with_T_at_least_1": with_ask, "minimum_with_T": K.H6_MIN_CREATORS_WITH_ASK,
                              "ask_overlaps_counted_once": overlaps, "cluster_window_units": H6_CLUSTER_WINDOW})
    out["determinable"] = len(tables) >= K.MIN_CREATORS[H] and with_ask >= K.H6_MIN_CREATORS_WITH_ASK
    return out


def _recordings(creator):
    """A creator's eligible recordings as a list of {a, b, wc, wo} rows; a single row stands for one recording."""
    return [creator] if isinstance(creator, dict) else list(creator)


def oe_value(creator):
    """Registry 2026-11-21 06:44 (3): OE = (a - sum_i T_i s_i) / T over the creator's recordings i (T_i = a_i + b_i, s_i
    the claimed share of recording i's words). With one recording it is a / T - s, CAL-A11's OE."""
    rows = _recordings(creator)
    total = sum(row["a"] + row["b"] for row in rows)
    expected = sum((row["a"] + row["b"]) * row["wc"] / (row["wc"] + row["wo"]) for row in rows)
    return (sum(row["a"] for row in rows) - expected) / total


def oe_values(creators):
    return [oe_value(creator) for creator in creators]


def _draw_units(row, by):
    """The units that the conditional reference draws in one recording row, as (asks, s_i): one per cluster (by "cluster",
    registry 11:08 (1); the row's "clusters" sizes) or one per ask (by "ask", the reference of 09:19 (1)). A row without
    cluster sizes (constructed rows of the tests) counts every ask as a cluster of one."""
    total = row["a"] + row["b"]
    share = row["wc"] / (row["wc"] + row["wo"])
    sizes = row.get("clusters") if by == "cluster" else None
    if sizes is None:
        sizes = [1] * total
    if sum(sizes) != total:
        raise ValueError(f"cluster sizes {sizes} do not sum to the recording's {total} asks")
    return [(size, share) for size in sizes]


def reference_cells(creators, by="cluster"):
    """The data of the conditional reference: per creator with T >= 1, (T, observed a, [(k, s_i)] with one entry per unit
    of the draw: per cluster of k asks of recording i (by "cluster", registry 2026-11-21 11:08 (1)) or per ask, k = 1
    (by "ask", 09:19 (1))). sum k s_i = sum_i T_i s_i either way. A recording without asks (a no-ask-file row too) adds
    nothing."""
    if by not in ("cluster", "ask"):
        raise ValueError("by is 'cluster' or 'ask'")
    cells = []
    for creator in creators:
        rows = [row for row in _recordings(creator) if row["a"] + row["b"] > 0]
        total = sum(row["a"] + row["b"] for row in rows)
        if total:
            cells.append((total, sum(row["a"] for row in rows), [unit for row in rows for unit in _draw_units(row, by)]))
    return cells


def creator_pmf(units):
    """P(a = 0 .. T) of one creator under the null, units: [(k, s)], each unit of k asks in the claimed voice with
    probability s, independently: the convolution of the two-point laws {0: 1 - s, k: s}."""
    dist = [1.0]
    for size, share in units:
        out = [0.0] * (len(dist) + size)
        for a, prob in enumerate(dist):
            if prob:
                out[a] += prob * (1.0 - share)
                out[a + size] += prob * share
        dist = out
    return dist


def _integer_statistic(cells):
    """The mean OE of the creators as an exact whole number: with L the least common multiple of the creators' T, the sum
    of L / T x a over the creators. Under the per-recording null the T_i and s_i are fixed, so sum_c OE_c = (this number)
    / L - sum_c (sum_i T_i s_i) / T_c, a fixed shift: ordering draws by this number orders them by the mean OE, and ties
    are exact (no rounding)."""
    lcm = 1
    for total, _, _ in cells:
        lcm = lcm * total // math.gcd(lcm, total)
    return lcm, sum(lcm // total * a for total, a, _ in cells)


def conditional_p(creators, label, draws=REFERENCE_DRAWS, alternative="less", by="cluster"):
    """The conditional Monte Carlo p of the mean over the creators with T >= 1 of OE = (a - sum_i T_i s_i) / T (each
    creator counts once). by "cluster" (registry 2026-11-21 11:08 (1)): the reference draws each cluster of a recording's
    asks (clusters_of) as one unit, in the claimed voice with the recording's claimed share s_i and all its asks with it,
    independently between clusters, given the clusters; by "ask" (09:19 (1), shown beside it): every ask alone, so
    a_i ~ Binomial(T_i, s_i) given T_i. Either is the distribution of the asks under no within-recording effect when its
    units fall in the voices in proportion to their words, whatever the recordings' ask rates. Each draw takes every
    creator's a from its exact null law (creator_pmf, inverse of its distribution function, one uniform a creator), the
    same distribution as drawing every unit. p = (b + 1) / (m + 1), b the draws at or below the observed value ("less",
    H6's side; "greater" at or above), m = draws, from a stream seeded by `label`; exact at every level alpha with
    alpha (m + 1) whole: P(p <= alpha) <= alpha under that null. Returns (p, method)."""
    if alternative not in ("less", "greater"):
        raise ValueError("H6's conditional reference is one-sided")
    cells = reference_cells(creators, by)
    if not cells:
        return 1.0, "none"
    lcm, observed = _integer_statistic(cells)
    tables = []
    for total, _, units in cells:
        cumulative, running = [], 0.0
        for prob in creator_pmf(units):
            running += prob
            cumulative.append(running)
        cumulative[-1] = 1.0                        # a uniform below 1 never falls past a = T
        tables.append((cumulative, lcm // total))
    draw, find = stats.rng(*label).random, bisect.bisect_right
    hits = 0
    for _ in range(draws):
        value = 0
        for cumulative, weight in tables:
            value += weight * find(cumulative, draw())
        hits += value <= observed if alternative == "less" else value >= observed
    return (hits + 1) / (draws + 1), f"conditional_monte_carlo_{by}s_{draws}"


def signflip_oe_p(creators, label):
    """The creator sign-flip p of OE, one-sided below (stats.signflip_p: exact up to 20 creators); the reference of
    06:44 (3) to 09:19 (1) and, since 11:08 (1), one half of the amended p. Returns (p, method)."""
    rows = [creator for creator in creators if sum(row["a"] + row["b"] for row in _recordings(creator))]
    return stats.signflip_p(oe_values(rows), "less", label=label)


def amended_p(creators, label, draws=REFERENCE_DRAWS):
    """Registry 2026-11-21 11:08 (1): the p of the amended version, the larger of the cluster-level conditional Monte Carlo
    p and the sign-flip p of OE, so that neither the sparse low-share case (where the sign-flip over-rejects) nor bursts
    of asks in one voice (where a reference drawing asks one by one over-rejects) can carry a verdict alone. The
    ask-level conditional p of 09:19 (1) is computed beside them and enters nothing. creators: the creators with T >= 1
    (recording rows). Returns (p, method, parts)."""
    p_cluster, cluster_method = conditional_p(creators, label + ("clusters",), draws, by="cluster")
    p_flip, flip_method = signflip_oe_p(creators, label + ("signflip-oe",))
    p_ask, ask_method = conditional_p(creators, label + ("conditional",), draws, by="ask")
    parts = {"cluster_conditional": p_cluster, "cluster_conditional_method": cluster_method,
             "signflip_oe": p_flip, "signflip_oe_method": flip_method,
             "ask_level_conditional_0919": p_ask, "ask_level_conditional_0919_method": ask_method,
             "enters_holm": "max(cluster_conditional, signflip_oe); ask_level_conditional_0919 shown only",
             **cluster_counts(creators)}
    return max(p_cluster, p_flip), f"max({cluster_method}, signflip_oe_{flip_method})", parts


def cluster_counts(creators):
    """Counts of the clusters of the creators' recording rows: clusters, asks in clusters of 2 or more, the largest."""
    sizes = [size for creator in creators for row in _recordings(creator) for size in (row.get("clusters") or [])]
    return {"clusters": len(sizes), "asks_in_clusters_of_2_or_more": sum(size for size in sizes if size >= 2),
            "largest_cluster": max(sizes) if sizes else 0}


def window_p(bundle, how, window, label, signflip_p, draws=REFERENCE_DRAWS, use_fallback=False):
    """Registry 2026-11-21 12:52 (1): the amended p with the clusters formed at another window (the sensitivity row's 10
    units; the battery also shows 11:08's window of 1): the larger of the cluster-level conditional p at `window` and the
    sign-flip p of OE (signflip_p, which does not depend on the clusters), over the same creators with T >= 1 (T does not
    depend on the window). bundle: the confirmatory bundle. Returns {window_units, p, p_cluster_conditional,
    p_signflip_oe, p_method, clusters, ...}; None below 2 creators with an ask."""
    tables = creator_tables(bundle, how, use_fallback, window=window)
    rows = [tables[c] for c in sorted(tables) if _sum(tables[c])["a"] + _sum(tables[c])["b"] >= 1]
    if len(rows) < 2:
        return None
    p_cluster, method = conditional_p(rows, label + ("window", window, "clusters"), draws, by="cluster")
    return {"window_units": window, "p": max(p_cluster, signflip_p), "p_cluster_conditional": p_cluster,
            "p_signflip_oe": signflip_p, "p_method": f"max({method}, signflip_oe)", **cluster_counts(rows)}


def pooled_oe_value(creator):
    """CAL-A11's OE before 06:44 (3): a / T - s with a, T and s pooled over the creator's recordings (not centred when ask
    rates differ between recordings); kept for comparison only (A10.7 and the battery's null_heterogeneous column)."""
    t = _sum(_recordings(creator))
    return t["a"] / (t["a"] + t["b"]) - t["wc"] / (t["wc"] + t["wo"])


def mh_ratio(creators):
    """The Mantel-Haenszel rate ratio with creator-by-recording strata (registry 2026-11-21 06:44 (3))."""
    ratio, _ = stats.mh_rate_ratio([(row["a"], row["b"], row["wc"], row["wo"]) for creator in creators
                                    for row in _recordings(creator)])
    return ratio


def _log_mh_ratio(creators):
    ratio = mh_ratio(creators)
    return math.log(ratio) if ratio else None


def _exp_pair(pair):
    return tuple(math.exp(value) if value is not None else None for value in pair)


A10_REPLACES = ("estimator: creator mean of half-count log rate ratios (registered) -> OE = (a - sum_i T_i s_i)/T, centred "
                "per recording, for the Holm p and the Mantel-Haenszel rate ratio with creator-by-recording strata as the "
                "estimate (A10.4, CAL-A11; registry 06:44 (3))",
                "reference: sign-flip of half-count log ratios (registered) -> the mean OE over creators with T >= 1, "
                f"p the larger of its cluster-level conditional Monte Carlo p (asks within {H6_CLUSTER_WINDOW} units of each "
                "other chain into one cluster, registry 12:52 (1); each cluster in the claimed voice with the recording's "
                "claimed share s_i) and the creator sign-flip p of OE (A10.4; registry 11:08 (1), amending 09:19 (1))",
                "minimum: 12 creators with both voices (registered) -> also 8 or more with T >= 1 (A10.4)",
                "interval: creator bootstrap (creators, then recordings, R1) of the mean log ratio (registered) -> for A5 "
                "both the t interval on OE and the MH interval, the wider of the creator-bootstrap percentile and the "
                "jackknife t interval until the coverage repeat (A10.7; registry 04:55 (j), 06:44 (5))")


def half_count(t):
    """The registered creator value: log(((a + 0.5) / wc) / ((b + 0.5) / wo))."""
    return math.log(((t["a"] + 0.5) / t["wc"]) / ((t["b"] + 0.5) / t["wo"]))


def _mean_half_count(sample):
    """The registered statistic in one two-stage draw: the mean over the drawn creators of the half-count log ratio of
    their drawn recordings."""
    values = [half_count(_sum(recordings)) for recordings in sample]
    return common.mean_or_none(values)


def registered_version(totals_all, label, draws, tables=None):
    """hypotheses.md as registered: creator-level log rate ratio with a half-count correction over every creator with both
    voices, sign-flip over creators, creator-bootstrap interval (creators, then recordings within each creator, as R1
    says; registry 2026-11-21 04:55 (d); tables: {creator: [recording rows]}); supported if the ratio is below 1, the 90%
    interval excludes zero (A5) and the ratio is at most 0.5; refuted by an interval inside 0.67 to 1.5 or a ratio above 1."""
    creators = sorted(c for c, t in totals_all.items() if t["wc"] and t["wo"])
    values = [half_count(totals_all[c]) for c in creators]
    elig = common.eligibility(H, len(creators), None, {"creators_both_voices": len(creators)},
                              minimum=K.REGISTERED_MIN_CREATORS[H])
    if len(values) < 2:
        return common.version(H, "registered", False, 1.0, None, None, None, (None, None), elig, A10_REPLACES), {}
    p, method = stats.signflip_p(values, "less", label=label + ("registered",))
    mean = common.mean_or_none(values)
    if tables is None:                                   # one recording per creator: the second stage changes nothing
        tables = {c: [totals_all[c]] for c in creators}
    lo, hi, _ = stats.bootstrap_two_stage([tables[c] for c in creators], _mean_half_count, draws,
                                          label + ("registered", "two-stage"), K.A5_LEVEL)
    ratio = math.exp(mean)
    refuted = None
    if lo is not None and K.H6_EQUIVALENCE[0] <= math.exp(lo) and math.exp(hi) <= K.H6_EQUIVALENCE[1]:
        refuted = "sells like the human: the 90% interval of the ratio lies inside 0.67 to 1.5"
    elif ratio > 1:
        refuted = "the ratio is above 1"
    cond = {"registered": ratio < 1, "a5": hi is not None and hi < 0, "effect_size": ratio <= K.SESOI[H], "refuted": refuted}
    return (common.version(H, "registered", elig["determinable"], p, {"mean_half_count_log_ratio": mean, "ratio": ratio},
                           {"bootstrap_90_log_ratio": (lo, hi), "bootstrap": "creators, then recordings (R1)"}, cond, (lo, hi),
                           elig, A10_REPLACES, method),
            dict(zip(creators, values)))


def analyse(bundle, how=None, label=("H6",), extras=True, draws=K.BOOTSTRAP_DRAWS, use_fallback=False,
            reference_draws=REFERENCE_DRAWS):
    bundle = common.confirmatory(bundle)
    how = how or vs.definition()
    elig = eligible(bundle, how)
    tables = creator_tables(bundle, how, use_fallback)
    creators = sorted(tables)
    totals_all = {c: _sum(tables[c]) for c in creators}
    hit = [c for c in creators if totals_all[c]["a"] + totals_all[c]["b"] >= 1]
    totals = [totals_all[c] for c in hit]
    per_creator = [tables[c] for c in hit]              # recording rows: OE and MH strata per recording (06:44 (3))
    out = {"hypothesis": H, "eligibility": elig, "creators_both_voices": len(creators), "creators_T_ge_1": len(hit),
           "creators_T_zero_excluded": len(creators) - len(hit),
           "unchecked_asks": sum(t["unchecked"] for t in totals_all.values()),
           "asks_on_neither_side": sum(t["neither"] for t in totals_all.values()),
           "version": "amended", "a10_replaces": list(A10_REPLACES),
           # registry 2026-11-21 12:52 (1): the window, and the statement that dependence beyond it is not modelled
           "cluster_rule": {"window_units": H6_CLUSTER_WINDOW, "sensitivity_window_units": H6_SENSITIVITY_WINDOW,
                            "rule": "an ask joins the cluster before it when its first unit is at most the window after "
                                    "the cluster's last unit (units are sentences; clusters chain)",
                            "dependence_beyond_the_window": "not modelled"},
           "notes": [CLUSTER_STATEMENT]}
    out["registered_version"], out["registered_creator_values"] = registered_version(totals_all, label, draws, tables)
    if len(hit) < 2:
        out.update({"determinable": False, "p": 1.0, "estimate": None, "creator_interval_90": (None, None)})
        return out
    oe = oe_values(per_creator)
    # registry 2026-11-21 11:08 (1): the larger of the cluster-level conditional p and the sign-flip p of OE
    p, method, p_parts = amended_p(per_creator, label, reference_draws)
    m, lo, hi = stats.t_interval(oe)
    ratio = mh_ratio(per_creator)
    blo, bhi, failed = stats.bootstrap_creators(per_creator, mh_ratio, draws, label + ("boot",), K.A5_LEVEL)
    blo95, bhi95, _ = stats.bootstrap_creators(per_creator, mh_ratio, draws, label + ("boot95",), 0.95)
    # registry 04:55 (j): the MH ratio carries the wider of the bootstrap percentile and the t interval (on the log scale,
    # shown as ratios)
    t90 = _exp_pair(stats.jackknife_t_interval(per_creator, _log_mh_ratio, K.A5_LEVEL))
    t95 = _exp_pair(stats.jackknife_t_interval(per_creator, _log_mh_ratio, 0.95))
    mh90, mh95 = stats.mh_interval((blo, bhi), t90), stats.mh_interval((blo95, bhi95), t95)
    pooled = {k: sum(t[k] for t in totals) for k in ("a", "b", "wc", "wo")}
    out.update({"determinable": elig["determinable"],
                "estimate": {"mh_rate_ratio": ratio, "mean_OE": m, "asks_claimed": pooled["a"], "asks_own": pooled["b"],
                             "strata": "creator by recording (registry 2026-11-21 06:44 (3))"},
                "intervals": {"t90_OE": (lo, hi), "mh_90": mh90, "mh_95": mh95, "mh_interval_rule": K.MH_INTERVAL_RULE,
                              "bootstrap_90_mh": (blo, bhi), "bootstrap_95_mh": (blo95, bhi95),
                              "jackknife_t90_mh": t90, "jackknife_t95_mh": t95, "bootstrap_failed_draws": failed},
                "p": p, "p_method": method, "p_parts": p_parts, "alternative": "less",
                "creator_values": {c: v for c, v in zip(hit, oe)}})
    refuted = None
    if ratio is not None and mh90[0] is not None and K.H6_EQUIVALENCE[0] <= mh90[0] and mh90[1] <= K.H6_EQUIVALENCE[1]:
        refuted = "sells like the human: the 90% interval of the ratio lies inside 0.67 to 1.5"
    elif ratio is not None and ratio > 1:
        refuted = "the ratio is above 1"
    # registry 2026-11-21 06:44 (5): A5 holds only if the t interval on the creator OE values and the MH interval both
    # exclude zero (a ratio of 1) on the predicted side
    a5_oe, a5_mh = hi is not None and hi < 0, mh90[1] is not None and mh90[1] < 1
    out["conditions"] = {"registered": ratio is not None and ratio < 1, "a5": a5_oe and a5_mh,
                         "a5_parts": {"t90_OE_below_zero": a5_oe, "mh_90_below_one": a5_mh},
                         "effect_size": ratio is not None and ratio <= K.SESOI[H], "refuted": refuted}
    out["creator_interval_90"] = (math.log(mh90[0]), math.log(mh90[1])) if mh90[0] and mh90[1] else (None, None)
    out["tipping"] = {"counts": tipping.rate_ratio(pooled["a"], pooled["b"], pooled["wc"], pooled["wo"], (1.0, K.SESOI[H])),
                      "note": "pooled raw table of the creators with T >= 1"}
    if not extras:
        return out
    sec = {}
    # registry 2026-11-21 12:52 (1): the sensitivity row, clusters at a 10-unit window (the sign-flip half is the same)
    wide = window_p(bundle, how, H6_SENSITIVITY_WINDOW, label, p_parts["signflip_oe"], reference_draws, use_fallback)
    sec[f"cluster window of {H6_SENSITIVITY_WINDOW} units (sensitivity row, registry 2026-11-21 12:52 (1))"] = dict(
        wide or {}, verdict=None, primary_window_units=H6_CLUSTER_WINDOW,
        note=(f"sensitivity row: the amended p with asks within {H6_SENSITIVITY_WINDOW} units of each other in one "
              f"cluster (the primary window is {H6_CLUSTER_WINDOW} units); no verdict; dependence of asks beyond "
              f"{H6_SENSITIVITY_WINDOW} units is not modelled either"))
    half = [half_count(totals_all[c]) for c in creators if totals_all[c]["wc"] and totals_all[c]["wo"]]
    if len(half) >= 2:
        hp, _ = stats.signflip_p(half, "less", label=label + ("half",))
        sec["registered half-count log ratio (sensitivity; the registered version of the A10 guard)"] = {
            "creators": len(half), "mean": common.mean_or_none(half), "t90": stats.t_interval(half)[1:], "signflip_p": hp}
    shown = {c: math.log((totals_all[c]["a"] / totals_all[c]["wc"]) / (totals_all[c]["b"] / totals_all[c]["wo"]))
             for c in creators if totals_all[c]["a"] and totals_all[c]["b"] and totals_all[c]["a"] + totals_all[c]["b"] >= K.H6_LOG_DISPLAY_MIN_T}
    sec["per-creator log ratios, T >= 5 (private)"] = {"creators": len(shown)}
    out["private_log_ratios_T5"] = shown
    voiced = sum(1 for c in creators if totals_all[c]["a"] >= 1)
    sec["share of creators whose claimed voice voices at least one pay-or-enrol ask"] = {
        "count": voiced, "of": len(creators), "share": voiced / len(creators), "wilson_90": stats.wilson(voiced, len(creators))}
    positioned = creator_tables(bundle, how, use_fallback, with_positions=True)
    strata = []
    for c in hit:
        for rec in positioned.get(c, []):
            for tenth, words in sorted(rec["tenths"].items()):
                a = sum(1 for side, where in rec["placed"] if side == "claimed" and min(9, int(10 * where)) == tenth)
                b = sum(1 for side, where in rec["placed"] if side == "own" and min(9, int(10 * where)) == tenth)
                strata.append((a, b, words["claimed"], words["own"]))
    adj, _ = stats.mh_rate_ratio(strata)
    sec["position-adjusted MH ratio (strata: creator by tenth of the recording)"] = adj
    if not use_fallback:
        fb = analyse(bundle, how, label + ("fallback",), extras=False, draws=min(draws, 1999), use_fallback=True,
                     reference_draws=reference_draws)
        sec["unchecked asks take the small model's verdict"] = {"mh_rate_ratio": (fb.get("estimate") or {}).get("mh_rate_ratio"),
                                                                 "p": fb.get("p")}
    sec["practice asks"] = "not available: no practice-ask labels exist (annotation plan R27 b, second budget)"
    sec["span-label confusion, record against the second model (words)"] = span_confusion(bundle, how)
    out["secondary"] = sec
    return out


def span_confusion(bundle, how):
    """Word-weighted table between the label of record and the other model on the eligible recordings: bounds how many
    words, and so asks, could change voice."""
    table = {}
    other = dict(how, model="other")
    for item in bundle["recordings"]:
        record = item.get("voice")
        if not record:
            continue
        left, right = vs.sides(record, how), vs.sides(record, other)
        if left is None or right is None:
            continue
        for key, words in vs.confusion(record, left[0], right[0]).items():
            table["/".join(key)] = table.get("/".join(key), 0) + words
    return dict(sorted(table.items()))
