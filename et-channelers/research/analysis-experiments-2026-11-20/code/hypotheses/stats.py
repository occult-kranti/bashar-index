"""Estimators, references and intervals shared by the hypothesis modules. Standard library only, deterministic.

Random streams: every draw comes from random.Random(seed_for(...)), where seed_for hashes BASE_SEED with a label, so a
result does not depend on the order in which tasks run or on the process that runs them. Nothing iterates over a set
of strings without sorting it first (string hashing is randomised per process).
"""
import bisect
import hashlib
import math
import random
from statistics import NormalDist

from . import constants as K

_NORMAL = NormalDist()


# ---------------------------------------------------------------- random streams

def seed_for(*parts):
    """A 64-bit seed from BASE_SEED and the given labels."""
    text = "|".join(str(part) for part in (K.BASE_SEED,) + parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def rng(*parts):
    return random.Random(seed_for(*parts))


# ---------------------------------------------------------------- basic summaries

def mean(values):
    values = list(values)
    return sum(values) / len(values) if values else None


def sd(values):
    values = list(values)
    if len(values) < 2:
        return None
    m = sum(values) / len(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def quantile(sorted_values, q):
    """Linear interpolation between order statistics (type 7)."""
    n = len(sorted_values)
    if n == 0:
        return None
    if n == 1:
        return sorted_values[0]
    h = (n - 1) * q
    lo = math.floor(h)
    hi = min(lo + 1, n - 1)
    return sorted_values[lo] + (h - lo) * (sorted_values[hi] - sorted_values[lo])


# ---------------------------------------------------------------- t distribution without scipy

def _betacf(a, b, x):
    """Continued fraction of the incomplete beta function (modified Lentz)."""
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 400):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def betainc(a, b, x):
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t, df):
    x = df / (df + t * t)
    tail = 0.5 * betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


_T_PPF = {}                               # memo of t_ppf: a pure function of (q, df), so results are bit-identical


def t_ppf(q, df):
    """Quantile of Student's t by bisection (deterministic, about 1e-12). Memoised: the bootstraps of the registered
    DerSimonian-Laird versions ask for the same few quantiles thousands of times."""
    key = (float(q), float(df))
    if key not in _T_PPF:
        _T_PPF[key] = _t_ppf(q, df)
    return _T_PPF[key]


def _t_ppf(q, df):
    if not 0.0 < q < 1.0:
        raise ValueError("q must lie in (0, 1)")
    if q == 0.5:
        return 0.0
    lo, hi = -1.0, 1.0
    while t_cdf(lo, df) > q:
        lo *= 2.0
    while t_cdf(hi, df) < q:
        hi *= 2.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13 * max(1.0, abs(mid)):
            break
    return (lo + hi) / 2.0


def z_ppf(q):
    return _NORMAL.inv_cdf(q)


# ---------------------------------------------------------------- intervals

def t_interval(values, level=K.A5_LEVEL):
    """t interval on creator values (A10.7 = CAL-A14 point 1). Returns (mean, lo, hi) or (mean, None, None) below 2
    values."""
    values = list(values)
    m = mean(values)
    s = sd(values)
    if s is None:
        return m, None, None
    half = t_ppf(0.5 + level / 2.0, len(values) - 1) * s / math.sqrt(len(values))
    return m, m - half, m + half


def wilson(k, n, level=K.A5_LEVEL):
    if n == 0:
        return None, None
    z = z_ppf(0.5 + level / 2.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def percentile_interval(draws, level):
    draws = sorted(value for value in draws if value is not None and not math.isnan(value))
    if len(draws) < 10:
        return None, None
    return quantile(draws, (1 - level) / 2), quantile(draws, 1 - (1 - level) / 2)


# ---------------------------------------------------------------- creator-level sign-flip (A10.1 = CAL-A8)

def _subset_sums(values):
    sums = [0.0]
    for value in values:
        sums = [s + value for s in sums] + [s - value for s in sums]
    return sums


def signflip_p(values, alternative, label=("signflip",), exact_max=K.SIGNFLIP_EXACT_MAX, draws=K.SIGNFLIP_MC_DRAWS):
    """p of the sign-flip test of the creator values. alternative: "greater" (mean above 0), "less" or "two-sided".
    Exact (all 2^n sign vectors, by meet in the middle) up to exact_max creators; above, Monte Carlo with
    p = (b + 1) / (m + 1) from a stream seeded by `label`. Returns (p, method)."""
    x = [float(v) for v in values]
    n = len(x)
    if n == 0:
        return 1.0, "none"
    absx = [abs(v) for v in x]
    observed = sum(x)
    tol = 1e-9 * max(1.0, sum(absx))
    if n <= exact_max:
        half = n // 2
        left, right = _subset_sums(absx[:half]), sorted(_subset_sums(absx[half:]))
        total = len(left) * len(right)

        def at_least(t):                 # number of sign vectors with sum >= t
            return sum(len(right) - bisect.bisect_left(right, t - a) for a in left)

        def at_most(t):
            return sum(bisect.bisect_right(right, t - a) for a in left)

        if alternative == "greater":
            count = at_least(observed - tol)
        elif alternative == "less":
            count = at_most(observed + tol)
        else:
            t = abs(observed)
            count = total if t <= tol else at_least(t - tol) + at_most(-t + tol)
        return min(1.0, count / total), "exact"
    stream = rng(*label)
    total_abs = sum(absx)
    hits = 0
    for _ in range(draws):
        bits = stream.getrandbits(n)
        s = 0.0
        for i in range(n):
            if bits >> i & 1:
                s += absx[i]
        s = 2.0 * s - total_abs
        if alternative == "greater":
            hits += s >= observed - tol
        elif alternative == "less":
            hits += s <= observed + tol
        else:
            hits += abs(s) >= abs(observed) - tol
    return (hits + 1) / (draws + 1), f"monte_carlo_{draws}"


def smallest_signflip_p(n, two_sided):
    return (2.0 if two_sided else 1.0) / (2 ** n) if n else 1.0


# ---------------------------------------------------------------- Holm over the fixed count (A6, A9, A10.1 = CAL-A8)

def holm(pvalues, m=K.HOLM_M, alpha=K.ALPHA):
    """pvalues: {hypothesis: p} for ALL_HYPOTHESES (missing ones enter at 1). Returns {hypothesis: (adjusted p, rejected)}.
    Ties are ordered by the hypothesis order of the registry, so the result is deterministic."""
    order = {name: index for index, name in enumerate(K.ALL_HYPOTHESES)}
    full = {name: float(pvalues.get(name, 1.0)) for name in K.ALL_HYPOTHESES}
    for name, value in pvalues.items():
        if name not in full:
            full[name] = float(value)
    if len(full) != m:
        raise ValueError(f"Holm count is fixed at {m}; got {len(full)} hypotheses")
    ranked = sorted(full, key=lambda name: (full[name], order.get(name, 99)))
    out, running = {}, 0.0
    for rank, name in enumerate(ranked):
        running = max(running, min(1.0, (m - rank) * full[name]))
        out[name] = (running, running <= alpha)
    return out


# ---------------------------------------------------------------- random-effects pool (A10.7 = CAL-A14 point 2)

def pooled_within_variance(values_by_creator):
    """Pooled within-creator variance of recording values, from creators with two or more recordings; None if none."""
    num, den = 0.0, 0
    for values in values_by_creator:
        if len(values) >= 2:
            m = sum(values) / len(values)
            num += sum((v - m) ** 2 for v in values)
            den += len(values) - 1
    return num / den if den > 0 else None


def creator_means_and_variances(values_by_creator):
    """Creator means with the variance of each mean: pooled within-creator variance / n_c (CHOICE). Without any creator
    of two recordings the variance of the creator means is used for every creator (equal weights)."""
    means = [sum(v) / len(v) for v in values_by_creator]
    within = pooled_within_variance(values_by_creator)
    if within is None or within <= 0:
        spread = sd(means)
        within = (spread ** 2 if spread else 1e-12)
        return means, [within for _ in values_by_creator]
    return means, [within / len(v) for v in values_by_creator]


def re_hksj(y, v, levels=(0.90, 0.95)):
    """DerSimonian-Laird tau^2, Hartung-Knapp-Sidik-Jonkman interval with t(k-1), and the prediction interval
    mu +- t(k-2) * sqrt(tau^2 + SE^2). Returns a dict, or None below 2 creators."""
    k = len(y)
    if k < 2:
        return None
    v = [max(value, 1e-12) for value in v]
    w = [1.0 / value for value in v]
    fixed = sum(wi * yi for wi, yi in zip(w, y)) / sum(w)
    q = sum(wi * (yi - fixed) ** 2 for wi, yi in zip(w, y))
    c = sum(w) - sum(wi * wi for wi in w) / sum(w)
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    ws = [1.0 / (vi + tau2) for vi in v]
    mu = sum(wi * yi for wi, yi in zip(ws, y)) / sum(ws)
    se_hk = math.sqrt(max(sum(wi * (yi - mu) ** 2 for wi, yi in zip(ws, y)) / ((k - 1) * sum(ws)), 0.0))
    out = {"k": k, "mu": mu, "se_hksj": se_hk, "se_dl": math.sqrt(1.0 / sum(ws)), "tau2": tau2, "intervals": {}, "prediction": {}}
    for level in levels:
        tq = t_ppf(0.5 + level / 2.0, k - 1)
        out["intervals"][str(level)] = (mu - tq * se_hk, mu + tq * se_hk)
        if k >= 3:
            tp = t_ppf(0.5 + level / 2.0, k - 2)
            half = tp * math.sqrt(tau2 + se_hk ** 2)
            out["prediction"][str(level)] = (mu - half, mu + half)
        else:
            out["prediction"][str(level)] = (None, None)
    return out


def re_dl(y, v, levels=(0.90, 0.95)):
    """DerSimonian-Laird random-effects pool with the normal interval mu +- z * SE_DL, and the prediction interval
    mu +- t(k-2) * sqrt(tau^2 + SE_DL^2) (Higgins, Thompson and Spiegelhalter 2009): the random-effects default that
    hypotheses.md's "random-effects meta-analysis" names without a method, and that A10.7 (CAL-A14 point 2) replaces by
    HKSJ. The point estimate and tau^2 are those of re_hksj. Returns a dict as re_hksj, or None below 2 creators."""
    base = re_hksj(y, v, levels)
    if base is None:
        return None
    k, mu, se = base["k"], base["mu"], base["se_dl"]
    out = {"k": k, "mu": mu, "se_dl": se, "tau2": base["tau2"], "intervals": {}, "prediction": {}}
    for level in levels:
        z = z_ppf(0.5 + level / 2.0)
        out["intervals"][str(level)] = (mu - z * se, mu + z * se)
        if k >= 3:
            half = t_ppf(0.5 + level / 2.0, k - 2) * math.sqrt(base["tau2"] + se ** 2)
            out["prediction"][str(level)] = (mu - half, mu + half)
        else:
            out["prediction"][str(level)] = (None, None)
    return out


# ---------------------------------------------------------------- bootstrap over creators

def bootstrap_creators(items, statistic, draws, label, level=K.A5_LEVEL):
    """Percentile interval of statistic(list of creator items) over creators drawn with replacement. Returns
    (lo, hi, failed draws)."""
    stream, n, values, failed = rng(*label), len(items), [], 0
    for _ in range(draws):
        sample = [items[stream.randrange(n)] for _ in range(n)]
        value = statistic(sample)
        if value is None:
            failed += 1
        else:
            values.append(value)
    lo, hi = percentile_interval(values, level)
    return lo, hi, failed


def two_stage_bootstrap(values_by_creator, draws, label, level=K.A5_LEVEL):
    """R1's procedure (creators, then recordings), kept as a sensitivity row (A10.7 = CAL-A14 point 1): the mean of
    creator means."""
    stream, n, out = rng(*label), len(values_by_creator), []
    for _ in range(draws):
        total = 0.0
        for _ in range(n):
            values = values_by_creator[stream.randrange(n)]
            total += sum(values[stream.randrange(len(values))] for _ in range(len(values))) / len(values)
        out.append(total / n)
    return percentile_interval(out, level)


def resample_list(items, stream):
    """The recordings of one creator drawn with replacement, as many as it has."""
    return [items[stream.randrange(len(items))] for _ in range(len(items))] if items else []


def bootstrap_two_stage(creators, statistic, draws, label, level=K.A5_LEVEL, resample=resample_list):
    """R1's registered resampling ("Resample creators, then recordings within a creator") as a percentile interval of any
    statistic: creators drawn with replacement, then each drawn creator's recordings drawn with replacement by
    resample(creator, stream) (default: a list of recordings resampled to its own length). statistic(list of resampled
    creators) gives a value or None. The registered "creator-bootstrap interval" of H2, H5 and H6 under the A10 guard
    (registry 2026-11-21 04:55 (d)). Returns (lo, hi, failed draws)."""
    stream, n, values, failed = rng(*label), len(creators), [], 0
    for _ in range(draws):
        sample = [resample(creators[stream.randrange(n)], stream) for _ in range(n)]
        value = statistic(sample)
        if value is None:
            failed += 1
        else:
            values.append(value)
    lo, hi = percentile_interval(values, level)
    return lo, hi, failed


def jackknife_t_interval(items, statistic, level=K.A5_LEVEL):
    """The t interval of a statistic of creator items (CHOICE for the Mantel-Haenszel estimates, registry 2026-11-21
    04:55 (j)): statistic(items) +- t(0.5 + level / 2, k - 1) x the delete-one-creator jackknife standard error. The
    statistic is on the scale the interval is wanted on (the log of a ratio). (lo, hi), or (None, None) below 3 creators
    or where a leave-one-out value cannot be computed."""
    k = len(items)
    if k < 3:
        return None, None
    full = statistic(items)
    if full is None:
        return None, None
    loo = [statistic(items[:i] + items[i + 1:]) for i in range(k)]
    if any(value is None for value in loo):
        return None, None
    centre = sum(loo) / k
    se = math.sqrt((k - 1) / k * sum((value - centre) ** 2 for value in loo))
    half = t_ppf(0.5 + level / 2.0, k - 1) * se
    return full - half, full + half


def wider_interval(*intervals):
    """Elementwise the widest of the given intervals: the smallest lower and the largest upper bound of those that
    exist; (None, None) if none does."""
    usable = [(lo, hi) for lo, hi in intervals if lo is not None and hi is not None]
    if not usable:
        return None, None
    return min(lo for lo, _ in usable), max(hi for _, hi in usable)


def mh_interval(bootstrap, t, rule=None):
    """The interval an MH estimate carries (constants.MH_INTERVAL_RULE, registry 2026-11-21 04:55 (j)): "wider" (the
    default until the coverage repeat has run), "bootstrap_percentile" or "t". Both inputs on one scale."""
    rule = K.MH_INTERVAL_RULE if rule is None else rule
    if rule not in K.MH_INTERVAL_RULES:
        raise ValueError(f"MH_INTERVAL_RULE must be one of {K.MH_INTERVAL_RULES}, not {rule!r}")
    if rule == "bootstrap_percentile":
        return tuple(bootstrap)
    if rule == "t":
        return tuple(t)
    return wider_interval(tuple(bootstrap), tuple(t))


# ---------------------------------------------------------------- Somers' D for H2

def somers_counts(pairs):
    """pairs: iterable of (x, committed, weight) with x a whole number. Returns (signed sum, pair weight) of the
    D of checkability between committed and uncommitted statements: positive if committed statements are more checkable."""
    w1, w0 = {}, {}
    for x, committed, weight in pairs:
        target = w1 if committed else w0
        target[x] = target.get(x, 0.0) + weight
    levels = sorted(set(w1) | set(w0))
    signed, cum0 = 0.0, 0.0
    below = {}
    for level in levels:
        below[level] = cum0
        cum0 += w0.get(level, 0.0)
    total0 = cum0
    for level in levels:
        a = w1.get(level, 0.0)
        if a:
            lower = below[level]
            higher = total0 - lower - w0.get(level, 0.0)
            signed += a * (lower - higher)
    return signed, sum(w1.values()) * total0, sum(w1.values()), total0


def somers_variance(d, n1, n0):
    """Hanley-McNeil variance of D = 2 AUC - 1."""
    if n1 <= 0 or n0 <= 0:
        return None
    a = (d + 1.0) / 2.0
    q1, q2 = a / (2.0 - a), 2.0 * a * a / (1.0 + a)
    var_a = (a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n0 - 1) * (q2 - a * a)) / (n1 * n0)
    return 4.0 * max(var_a, 1.0 / (12.0 * n1 * n0))


def somers_ordinal(rows):
    """rows: (x, y, weight) with y ordinal; D = sum over pairs untied on y of sign(y)sign(x) / pairs untied on y."""
    num = den = 0.0
    for i in range(len(rows)):
        xi, yi, wi = rows[i]
        for j in range(i + 1, len(rows)):
            xj, yj, wj = rows[j]
            if yi == yj:
                continue
            w = wi * wj
            den += w
            sx = (xi > xj) - (xi < xj)
            sy = (yi > yj) - (yi < yj)
            num += w * sx * sy
    return (num / den if den else None), den


# ---------------------------------------------------------------- Mantel-Haenszel (A10.4 = CAL-A11)

def mh_rate_ratio(strata):
    """strata: (a, b, exposure_a, exposure_b). Rate ratio a-side to b-side, with the Greenland-Robins variance of its log."""
    num = den = var_num = 0.0
    for a, b, ea, eb in strata:
        e = ea + eb
        if e <= 0:
            continue
        num += a * eb / e
        den += b * ea / e
        var_num += ea * eb * (a + b) / (e * e)
    if num <= 0 or den <= 0:
        return None, None
    return num / den, var_num / (num * den)


def mh_odds_ratio(strata):
    """strata: (wa, pa, wb, pb). Odds ratio of w against p, side a to side b, with the Robins-Breslow-Greenland variance."""
    r_sum = s_sum = pr = ps_qr = qs = 0.0
    for wa, pa, wb, pb in strata:
        n = wa + pa + wb + pb
        if n <= 0:
            continue
        r, s = wa * pb / n, wb * pa / n
        p, q = (wa + pb) / n, (wb + pa) / n
        r_sum, s_sum = r_sum + r, s_sum + s
        pr, ps_qr, qs = pr + p * r, ps_qr + p * s + q * r, qs + q * s
    if r_sum <= 0 or s_sum <= 0:
        return None, None
    var = pr / (2 * r_sum ** 2) + ps_qr / (2 * r_sum * s_sum) + qs / (2 * s_sum ** 2)
    return r_sum / s_sum, var


# ---------------------------------------------------------------- permutation p

def permutation_p(observed, reference, alternative):
    """p = (b + 1) / (m + 1) against reference draws."""
    tol = 1e-12 * max(1.0, abs(observed))
    if alternative == "greater":
        b = sum(value >= observed - tol for value in reference)
    elif alternative == "less":
        b = sum(value <= observed + tol for value in reference)
    else:
        b = sum(abs(value) >= abs(observed) - tol for value in reference)
    return (b + 1) / (len(reference) + 1)


# ---------------------------------------------------------------- detectable effect (A10.2 = CAL-A9 point 1)

def signflip_power(n, d, alternative, alpha, reps, label):
    """Power of the exact sign-flip at level alpha for n normal creator values with mean d (in SD units)."""
    stream, hits = rng(*label), 0
    for _ in range(reps):
        values = [stream.gauss(d, 1.0) for _ in range(n)]
        p, _ = signflip_p(values, alternative)
        hits += p <= alpha
    return hits / reps


def detectable_effect(n, alternative, alpha=K.ALPHA / K.HOLM_M, power=0.80, reps=K.POWER_REPS):
    """The effect (in SD units of creator values) that the sign-flip detects with the given power at the first Holm step;
    None if no effect can (too few creators). Bisection on a fixed grid of seeds: deterministic."""
    if smallest_signflip_p(n, alternative == "two-sided") > alpha:
        return None
    sign = -1.0 if alternative == "less" else 1.0
    lo, hi = 0.0, 4.0
    for step in range(14):
        mid = (lo + hi) / 2.0
        got = signflip_power(n, sign * mid, alternative, alpha, reps, ("power", n, alternative, alpha))
        if got >= power:
            hi = mid
        else:
            lo = mid
    return hi
