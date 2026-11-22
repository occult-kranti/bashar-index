"""Shared steps of the hypothesis modules: creator-level summaries, the eligibility record, leave-one-creator-out ranges."""
import math

from . import constants as K
from . import stats


def confirmatory(bundle):
    """The bundle restricted to the creators of the confirmatory groups (hold-out); seen creators stay out of every
    confirmatory estimate except as H9's unread-against-read partner. A recording of any other group (a replication
    wave included, which does not exist: registry 2026-11-21 04:55 (h)) is left out, never pooled."""
    return dict(bundle, recordings=[item for item in bundle["recordings"] if item.get("group") in K.CONFIRMATORY_GROUPS])


def stratum(bundle, item):
    """The recognizer model of a recording in the model-stratified view (adapter.model_stratified_view; registry 03:08),
    None in every other bundle, so that only that row crosses its strata with the model."""
    return item.get("asr_stratum") if (bundle.get("asr_rule") or {}).get("stratified") else None


def eligibility(hypothesis, creators, recordings, extra=None, minimum=None):
    """The record A10.2 = CAL-A9 asks for before any outcome: the eligible count from labels only, and the minimum."""
    minimum = K.MIN_CREATORS[hypothesis] if minimum is None else minimum
    out = {"hypothesis": hypothesis, "creators": creators, "recordings": recordings, "minimum": minimum,
           "determinable": creators >= minimum}
    out.update(extra or {})
    return out


def pooled(values_by_creator, label, alternative, levels=(0.90, 0.95)):
    """Creator means, their HKSJ random-effects pool with prediction interval (A10.7 = CAL-A14), the DerSimonian-Laird
    pool with normal intervals (the registered version under the A10 guard), the t interval on creator means and the
    creator-level sign-flip p (the p that enters Holm, A10.1 = CAL-A8)."""
    means, variances = stats.creator_means_and_variances(values_by_creator)
    pool = stats.re_hksj(means, variances, levels)
    m, lo, hi = stats.t_interval(means, K.A5_LEVEL)
    p, method = stats.signflip_p(means, alternative, label=label + ("signflip",))
    return {"creator_means": means, "variances": variances, "pool": pool, "pool_dl": stats.re_dl(means, variances, levels),
            "t90": (m, lo, hi), "p": p, "p_method": method, "alternative": alternative,
            "positive_creators": sum(value > 0 for value in means), "n_creators": len(means)}


def version(hypothesis, name, determinable, p, estimate, intervals, conditions, interval_90, eligibility, replaced=(),
            method=None, notes=None):
    """One version of a hypothesis's test under the A10 guard (registry 2026-11-21 03:08): "registered" (the text of
    hypotheses.md and the registry before A10) or "amended" (A10.1 to A10.7). interval_90 is the 90% creator interval on
    the scale of K.UNINFORMATIVE_SESOI (the uninformative rule). No creator-level value goes in here."""
    return {"hypothesis": hypothesis, "version": name, "determinable": bool(determinable), "p": p, "p_method": method,
            "estimate": estimate, "intervals": intervals, "conditions": conditions, "creator_interval_90": interval_90,
            "eligibility": eligibility, "replaced_by_a10": list(replaced), "notes": notes}


def loo_range(values, statistic):
    """Leave-one-creator-out range of statistic(list)."""
    if len(values) < 3:
        return None, None
    out = [statistic(values[:i] + values[i + 1:]) for i in range(len(values))]
    out = [value for value in out if value is not None]
    return (min(out), max(out)) if out else (None, None)


def mean_or_none(values):
    return sum(values) / len(values) if values else None


def safe_log(value):
    return math.log(value) if value and value > 0 else None


def short(value, digits=4):
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, (list, tuple)):
        return [short(item, digits) for item in value]
    if isinstance(value, dict):
        return {key: short(item, digits) for key, item in value.items()}
    return value
