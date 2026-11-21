"""Tipping-point tables (annotation plan 3.5): how far the two kinds of label error would have to differ between the
compared groups before the verdict changes. Plain arithmetic on the pooled raw tables; no model of the error is
estimated, and none of these numbers is an error rate of the labels.

Voice contrasts (H1, H4): the two kinds of error are own-voice words labelled claimed and claimed words labelled own.
  * attenuation: errors that carry the outcome of their true voice shrink the contrast by (1 - a - b); the table gives
    the corrected estimate and interval for a total error a + b on a grid. Such errors can hide an effect, never make one.
  * selection: errors that pick out words by the outcome itself (slow own speech labelled claimed, for example) shift the
    contrast by about e * delta, where e is the share of a side's words that are mislabelled and delta how far those words
    differ from their true voice. The table gives the delta needed, at each e, to move the estimate across the verdict
    boundary.
Count outcomes (H2, H5, H6): the two kinds of error are missed and false codes of the outcome, and the table gives the
ratio of detection rates, or the excess of false codes, between the compared groups at which the corrected estimate
reaches each boundary.
"""
import math

GRID = (0.01, 0.02, 0.05, 0.10, 0.20)


def attenuation(estimate, lo, hi, grid=GRID):
    rows = []
    for total in grid:
        factor = 1.0 - total
        rows.append({"total_error": total, "corrected_estimate": estimate / factor,
                     "corrected_interval": (None if lo is None else lo / factor, None if hi is None else hi / factor)})
    return rows


def selection(margin, grid=GRID):
    """margin: how far the estimate must move (in its own units, signed) to cross the verdict boundary."""
    return [{"error_share": share, "outcome_offset_needed": margin / share} for share in grid]


def rate_ratio(a, b, exposure_a, exposure_b, boundaries):
    """H6: pooled asks a (claimed side) and b (own side) over exposures in words. For each boundary RR*: the ratio of
    detection rates s_claimed / s_own at which the corrected ratio equals RR*, and the excess of false asks per 1,000
    claimed-side words that, removed, would bring it there."""
    if not (exposure_a and exposure_b) or b == 0:
        return []
    observed = (a / exposure_a) / (b / exposure_b)
    rows = []
    for boundary in boundaries:
        rows.append({"boundary_ratio": boundary, "observed_ratio": observed,
                     "detection_ratio_needed": observed / boundary,
                     "false_asks_per_1000_claimed_words": 1000.0 * (a / exposure_a - boundary * b / exposure_b)})
    return rows


def odds_ratio(wa, pa, wb, pb, boundaries):
    """H5: pooled world (w) and practice (p) points, side A (channelled titles) and B (own-voice talks). For each boundary
    OR*: the share x of side-A world-claim codes that would have to be false (truly practice), or the share y of side-B
    practice codes that would have to be false (truly world claims), for the corrected odds ratio to equal OR*."""
    if min(wa, pa, wb, pb) <= 0:
        return []
    observed = (wa / pa) / (wb / pb)
    rows = []
    for boundary in boundaries:
        r = boundary * wb / pb
        x = (wa - r * pa) / (wa * (1.0 + r))
        t = (wa / pa) / boundary
        y = (t * pb - wb) / (pb * (1.0 + t))
        rows.append({"boundary_log_or": math.log(boundary), "observed_log_or": math.log(observed),
                     "false_world_share_side_A": x, "false_practice_share_side_B": y})
    return rows


def commitment(committed_high, n_high, committed_low, n_low):
    """H2: statements above against at or below the median checkability. The share m of hedged or conditional statements
    in the less checkable group that the coder would have to miss (and so code as committed) for the observed gap in
    commitment to vanish, if the more checkable group had no such error."""
    if not n_high or not n_low:
        return []
    high, low = committed_high / n_high, committed_low / n_low
    if high >= 1.0:
        return []
    return [{"committed_share_high": high, "committed_share_low": low,
             "missed_hedge_rate_low_needed": (low - high) / (1.0 - high)}]


def dilution(estimate, lo, hi, boundary, grid=GRID):
    """H9: random family labels shrink both contrasts. The share m of wrong labels at which the corrected interval
    (divided by 1 - m) would reach the boundary."""
    rows = attenuation(estimate, lo, hi, grid)
    for row in rows:
        row["reaches_boundary"] = (row["corrected_interval"][1] is not None and row["corrected_interval"][1] >= boundary)
    return rows
