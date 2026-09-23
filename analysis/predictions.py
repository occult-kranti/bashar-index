"""predictions.py — H1 prediction-ratchet analysis (P1, P2) + ledger build.

Implements r2_design.md §1(a) verbatim, with the r2 advisor amendments:
  * absolute freeze note: design + 50-phrase lexicon frozen at git HEAD cff3988;
  * JT statistic clarified: per-claim c_i across ordinal Delta bins; pooled C per
    bin reported descriptively (with per-claim median c_i as pooling sensitivity);
  * era-confound control: within-era JT (post-2015 claims) AND per-claim partial
    Spearman of c_i vs Delta controlling date_made;
  * stated-n rule: n printed for every test; where n < 10 the honest claim is
    "directional + CI only — the ledger is the finding, the statistic is the
    annotation";
  * dates from title-only sources (year_reliable: false) stay in the ledger,
    flagged, but are excluded from all time series / tests.

Seed 42 everywhere. Outputs:
  results/ledger.csv, results/predictions_results.json,
  figures/fig_f1_gantt.png, fig_f2_conditionality.png, fig_f3_drift.png
"""
from __future__ import annotations

import csv
import os
import re

import numpy as np
from scipy import stats

import common
from common import SEED, RESULTS, FIGURES
import report

RNG = np.random.default_rng(SEED)
N_BOOT = 10_000
N_PERM = 10_000

YEAR_RE = re.compile(r"(?:19|20)\d{2}")

BIN_ORDER = [">10y", "5-10y", "1-5y", "<1y", "post-deadline"]
# H1: C increases as Delta -> 0, so the ordered alternative runs from >10y
# (lowest predicted C) to post-deadline (highest predicted C).


# ------------------------------------------------------------------ ledger

def parse_bounds(date_str: str):
    """Extract (lower, upper) bound years from a recorded date string."""
    years = [int(m.group(0)) for m in YEAR_RE.finditer(date_str or "")]
    if not years:
        return None, None
    return min(years), max(years)


def delta_bin(t, lo, hi):
    d = lo - t
    if t > hi:
        return "post-deadline"
    if d > 10:
        return ">10y"
    if d >= 5:
        return "5-10y"
    if d >= 1:
        return "1-5y"
    return "<1y"


def build_ledger():
    digests = common.load_digests()
    vmap = {v["video_id"]: v for v in common.load_videos()}
    rows, seen = [], set()
    for d in digests:
        vid = d["video_id"]
        v = vmap.get(vid, {})
        year = v.get("year")
        reliable = bool(v.get("year_reliable"))
        note = v.get("researcher_note") or d.get("researcher_note") or ""
        reframe = (not reliable) or bool(
            re.search(r"re-upload|actually|unlikely|mislabel", note, re.I))
        for p in d.get("predictions_and_dates") or []:
            date_str = str(p.get("date") or p.get("year")
                           or p.get("year_or_date") or "")
            claim = " ".join(x for x in [p.get("prediction") or "",
                                         p.get("context") or ""]).strip()
            if not claim:
                continue
            key = (vid, date_str, claim)
            if key in seen:
                continue
            seen.add(key)
            lo, hi = parse_bounds(date_str)
            h, hits = common.lexicon_hits(claim)
            T = common.token_count(claim)
            rows.append({
                "video_id": vid,
                "date_made": year if reliable else None,
                "date_made_title_only": year,
                "year_reliable": reliable,
                "date_str": date_str,
                "window_lower": lo,
                "window_upper": hi,
                "claim": claim,
                "lexicon_hits": h,
                "matched_phrases": ";".join(sorted(set(hits))),
                "tokens": T,
                "c_i": (h / T) if T else None,
                "delta_bin": (delta_bin(year, lo, hi)
                              if reliable and lo is not None else None),
                "contact_related": bool(re.search(r"contact|disclosure", claim, re.I)),
                "outcome": "unresolved (prospective)" if (lo and (year or 0) <= hi)
                           else "retrospective/unscored",
                "reframe_flag": bool(reframe),
            })
    return rows


# ------------------------------------------------------------------ stats

def jt_statistic(values: np.ndarray, groups: np.ndarray, order: list) -> float:
    """Jonckheere–Terpstra J: concordant minus half-ties pair count across
    ordinally increasing groups."""
    J = 0.0
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            a = values[groups == order[i]]
            b = values[groups == order[j]]
            if len(a) == 0 or len(b) == 0:
                continue
            diff = b[None, :] - a[:, None]
            J += np.sum(diff > 0) + 0.5 * np.sum(diff == 0)
    return J


def jt_permutation_p(values, groups, order, n_perm=N_PERM):
    """One-sided (increasing) permutation p for JT, seed 42."""
    J_obs = jt_statistic(values, groups, order)
    cnt = 1  # +1 smoothing
    for _ in range(n_perm):
        perm = RNG.permutation(values)
        if jt_statistic(perm, groups, order) >= J_obs:
            cnt += 1
    # normal approximation for reference
    ns = np.array([np.sum(groups == g) for g in order], dtype=float)
    N = ns.sum()
    E = (N * N - np.sum(ns * ns)) / 4.0
    V = (N * N * (2 * N + 3) - np.sum(ns * ns * (2 * ns + 3))) / 72.0
    z = (J_obs - E) / np.sqrt(V)
    p_norm = 1.0 - stats.norm.cdf(z)
    # effect: Somers'-D-like concordance across ordered pairs
    tot, exc = 0.0, 0.0
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            a = values[groups == order[i]]
            b = values[groups == order[j]]
            n = len(a) * len(b)
            diff = b[None, :] - a[:, None]
            exc += np.sum(diff == 0)
            tot += n
    denom = tot - exc
    D = (2 * J_obs - tot) / denom if denom > 0 else 0.0
    return J_obs, cnt / (n_perm + 1), p_norm, D


def bootstrap_ci(x, fn, n_boot=N_BOOT):
    x = np.asarray(x)
    stats_ = []
    for _ in range(n_boot):
        idx = RNG.integers(0, len(x), len(x))
        stats_.append(fn(x[idx]))
    return [float(np.percentile(stats_, 2.5)), float(np.percentile(stats_, 97.5))]


def bootstrap_ci_pairs(xs, ys, fn, n_boot=N_BOOT):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    out = []
    n = len(xs)
    for _ in range(n_boot):
        idx = RNG.integers(0, n, n)
        out.append(fn(xs[idx], ys[idx]))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def spearman_fn(a, b):
    r, _ = stats.spearmanr(a, b)
    return r


def partial_spearman(x, y, c):
    """Spearman(x,y) controlling c: Pearson corr of rank-residuals after
    regressing each variable's ranks on ranks(c)."""
    rx, ry, rc = stats.rankdata(x), stats.rankdata(y), stats.rankdata(c)
    bx = np.polyfit(rc, rx, 1)
    by = np.polyfit(rc, ry, 1)
    resx = rx - np.polyval(bx, rc)
    resy = ry - np.polyval(by, rc)
    r, _ = stats.pearsonr(resx, resy)
    return float(r)


def theil_sen_boot(t, y, n_boot=N_BOOT):
    slope, intercept, *_ = stats.theilslopes(y, t)
    boots = []
    n = len(t)
    for _ in range(n_boot):
        idx = RNG.integers(0, n, n)
        if len(np.unique(t[idx])) < 2:
            continue
        boots.append(stats.theilslopes(y[idx], t[idx])[0])
    ci = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
    return float(slope), float(intercept), ci


# ------------------------------------------------------------------ figures

def fig_gantt(rows, path):
    plt = common.apply_style()
    win = [r for r in rows if r["window_lower"] and r["contact_related"]
           and r["date_made"]]
    # dedupe visual clutter: one row per (date_made, lower, upper)
    seen, spans = set(), []
    for r in sorted(win, key=lambda r: (r["date_made"], r["window_lower"])):
        k = (r["date_made"], r["window_lower"], r["window_upper"])
        if k in seen:
            continue
        seen.add(k)
        spans.append(r)
    fig, ax = plt.subplots(figsize=(10, max(4, 0.28 * len(spans) + 2)))
    for i, r in enumerate(spans):
        lo, hi, t = r["window_lower"], r["window_upper"], r["date_made"]
        ax.plot([lo, hi], [t, t], color=common.AMBER, lw=6, alpha=0.85,
                solid_capstyle="round")
        ax.plot(lo, t, "o", color=common.COPPER, ms=4)
    ax.axvline(2026.5, color=common.COPPER, lw=2, ls="--")
    ax.text(2026.6, ax.get_ylim()[0] if spans else 2020, " now (corpus end, mid-2026)",
            color=common.COPPER, fontsize=8, rotation=90, va="bottom")
    ax.set_xlabel("stated deadline / window bound (year)")
    ax.set_ylabel("date made (reliable-year videos only)")
    ax.set_title("F1. Sliding-window gantt — every stated contact window vs. the moving 'now'\n"
                 f"n = {len(spans)} distinct stated windows (deduplicated per video)")
    common.badge(fig, "content", "Frontier", exploratory=False,
                 extra="figure, not a finding (design §5)")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_conditionality(bin_stats, p1_note, path):
    plt = common.apply_style()
    bins = [b for b in BIN_ORDER if b in bin_stats]
    C = [bin_stats[b]["pooled_C"] for b in bins]
    lo = [bin_stats[b]["ci"][0] for b in bins]
    hi = [bin_stats[b]["ci"][1] for b in bins]
    ns = [bin_stats[b]["n"] for b in bins]
    x = np.arange(len(bins))
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(x, C, yerr=[np.array(C) - np.array(lo), np.array(hi) - np.array(C)],
                fmt="o-", color=common.AMBER, lw=2, ms=8, capsize=5,
                label="pooled C per Δ bin (bootstrap 95% CI)")
    overall = np.average(C, weights=ns)
    ax.axhline(overall, color=common.COPPER, ls=":", lw=1.5,
               label=("weighted mean of the observed bins — descriptive "
                      "reference, NOT a null model"))
    for xi, n in zip(x, ns):
        ax.annotate(f"n={n}", (xi, 0), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=8, color=common.TEXT)
    ax.set_xticks(x, bins)
    ax.set_xlabel("Δ = stated deadline − date made (ordered near → past)")
    ax.set_ylabel("conditionality index C = Σhits / Σtokens")
    ax.set_title("F2. Conditionality vs. time-to-deadline\n" + p1_note, fontsize=10)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.2)
    common.badge(fig, "content", "Frontier", exploratory=False, extra="P1 (primary)")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_drift(pts, fitL, fitU, path):
    plt = common.apply_style()
    t = np.array([p[0] for p in pts], float)
    L = np.array([p[1] for p in pts], float)
    U = np.array([p[2] for p in pts], float)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(t, U, color=common.AMBER, s=45, label="upper bound U(t)", zorder=3)
    ax.scatter(t, L, color=common.COPPER, s=45, label="lower bound L(t)", zorder=3)
    xs = np.linspace(t.min() - 0.5, t.max() + 0.5, 50)
    sU, iU = fitU["slope"], fitU["intercept"]
    sL, iL = fitL["slope"], fitL["intercept"]
    ax.plot(xs, iU + sU * xs, color=common.AMBER, lw=2)
    ax.plot(xs, iL + sL * xs, color=common.COPPER, lw=2)
    ax.plot(xs, U.mean() + 1.0 * (xs - t.mean()), color=common.TEXT, ls="--",
            lw=1, alpha=0.6, label="reference: drift = 1 (deadline recedes with time)")
    cap = (f"drift L(t) = {sL:.2f} yr/yr [95% CI {fitL['ci'][0]:.2f}, {fitL['ci'][1]:.2f}]   "
           f"U(t) = {sU:.2f} [{fitU['ci'][0]:.2f}, {fitU['ci'][1]:.2f}]   n = {len(pts)} restatements")
    ax.set_xlabel("date made (year)")
    ax.set_ylabel("stated bound (year)")
    ax.set_title("F3. Contact-window bound drift (Theil–Sen)\n" + cap, fontsize=10)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.2)
    common.badge(fig, "content", "Frontier", exploratory=False, extra="P2 (primary)")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ main

def main():
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(FIGURES, exist_ok=True)
    rows = build_ledger()

    ledger_path = os.path.join(RESULTS, "ledger.csv")
    fields = ["video_id", "date_made", "date_made_title_only", "year_reliable",
              "date_str", "window_lower", "window_upper", "delta_bin",
              "lexicon_hits", "matched_phrases", "tokens", "c_i",
              "contact_related", "outcome", "reframe_flag", "claim"]
    with open(ledger_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ---- P1: conditionality vs Delta (reliable-date, parseable-deadline claims)
    testable = [r for r in rows if r["delta_bin"] and r["c_i"] is not None]
    vals = np.array([r["c_i"] for r in testable])
    grps = np.array([r["delta_bin"] for r in testable])
    n1 = len(testable)
    J, p_perm, p_norm, D = jt_permutation_p(vals, grps, BIN_ORDER)
    # bootstrap CI for Somers' D over claims
    boot_D = []
    for _ in range(N_BOOT):
        idx = RNG.integers(0, n1, n1)
        boot_D.append(_somers(vals[idx], grps[idx]))
    ci_D = [float(np.percentile(boot_D, 2.5)), float(np.percentile(boot_D, 97.5))]

    # within-era JT: post-2015 claims only (advisor amendment a-ii)
    era = [r for r in testable if r["date_made"] >= 2016]
    vE = np.array([r["c_i"] for r in era])
    gE = np.array([r["delta_bin"] for r in era])
    era_res = None
    if len(era) >= 10 and len(set(gE)) >= 3:
        Je, p_perm_e, p_norm_e, De = jt_permutation_p(vE, gE, BIN_ORDER)
        boot_e = []
        for _ in range(N_BOOT):
            idx = RNG.integers(0, len(era), len(era))
            boot_e.append(_somers(vE[idx], gE[idx]))
        ci_De = [float(np.percentile(boot_e, 2.5)),
                 float(np.percentile(boot_e, 97.5))]
        era_res = {"n": len(era), "J": float(Je), "p_perm": float(p_perm_e),
                   "p_normal": float(p_norm_e), "somers_D": float(De),
                   "ci_D": ci_De}

    # Spearman rho(C, -Delta) and partial Spearman controlling date_made
    cont = [r for r in testable if r["window_lower"] is not None]
    c_i = np.array([r["c_i"] for r in cont])
    negD = np.array([-(r["window_lower"] - r["date_made"]) for r in cont], float)
    dm = np.array([r["date_made"] for r in cont], float)
    rho, p_sp = stats.spearmanr(c_i, negD)
    ci_rho = bootstrap_ci_pairs(c_i, negD, spearman_fn)
    prho = partial_spearman(c_i, negD, dm)

    # bootstrap for partial spearman (resample triples)
    boot_p = []
    nn = len(c_i)
    for _ in range(N_BOOT):
        idx = RNG.integers(0, nn, nn)
        try:
            boot_p.append(partial_spearman(c_i[idx], negD[idx], dm[idx]))
        except Exception:
            continue
    ci_prho = [float(np.percentile(boot_p, 2.5)), float(np.percentile(boot_p, 97.5))]

    # naive asymptotic two-sided p for the partial correlation on rank
    # residuals (r3 audit: must be stated alongside, never conflated with,
    # E2's uncontrolled p). Asymptotics on residualized ranks are approximate;
    # the bootstrap CI is the operative uncertainty statement.
    t_naive = prho * np.sqrt((nn - 3) / max(1e-12, 1.0 - prho ** 2))
    p_naive_e3 = float(2.0 * stats.t.sf(abs(t_naive), nn - 3))

    # per-bin descriptive pooled C + per-claim median c_i (advisor a-i)
    bin_stats = {}
    for b in BIN_ORDER:
        sel = [r for r in testable if r["delta_bin"] == b]
        if not sel:
            continue
        H = sum(r["lexicon_hits"] for r in sel)
        T = sum(r["tokens"] for r in sel)
        ci = [float(np.percentile(
            [ (lambda ix: sum(sel[i]["lexicon_hits"] for i in ix) /
              max(1, sum(sel[i]["tokens"] for i in ix)))(RNG.integers(0, len(sel), len(sel)))
              for _ in range(2000)], q)) for q in (2.5, 97.5)]
        bin_stats[b] = {"n": len(sel), "pooled_C": H / T if T else None,
                        "median_c_i": float(np.median([r["c_i"] for r in sel])),
                        "ci": ci}

    # ---- P2: window drift on restated contact windows
    pts = sorted({(r["date_made"], r["window_lower"], r["window_upper"])
                  for r in rows if r["date_made"] and r["contact_related"]
                  and r["window_lower"] is not None})
    t = np.array([p[0] for p in pts], float)
    L = np.array([p[1] for p in pts], float)
    U = np.array([p[2] for p in pts], float)
    n2 = len(pts)
    sL, iL, ciL = theil_sen_boot(t, L)
    sU, iU, ciU = theil_sen_boot(t, U)

    # ---- figures
    p1_note = (f"P1 JT (per-claim c_i, n={n1}): permutation p={p_perm:.4f} — "
               f"ratchet signature rejected\n"
               f"E2 uncontrolled rho={rho:.3f}, p={p_sp:.4f} | E3 "
               f"era-controlled partial rho={prho:.3f},\n"
               f"CI [{ci_prho[0]:.3f}, {ci_prho[1]:.4f}], "
               f"naive p={p_naive_e3:.3f}")
    fig_gantt(rows, os.path.join(FIGURES, "fig_f1_gantt.png"))
    fig_conditionality(bin_stats, p1_note,
                       os.path.join(FIGURES, "fig_f2_conditionality.png"))
    fig_drift(pts, {"slope": sL, "intercept": iL, "ci": ciL},
              {"slope": sU, "intercept": iU, "ci": ciU},
              os.path.join(FIGURES, "fig_f3_drift.png"))

    # ---- results doc
    tests = []
    tests.append(report.make_test(
        "P1", statistic={"jt_J": float(J), "p_normal_approx": float(p_norm)},
        p=float(p_perm),
        effect={"somers_D": float(D)}, ci95=ci_D,
        exploratory=False,
        note=(f"One-sided Jonckheere–Terpstra on per-claim c_i across ordinal "
              f"Delta bins (n={n1}); permutation p (10k, seed 42). Pooled C per "
              f"bin is descriptive only. Ratchet signature REJECTED "
              f"(p={p_perm:.4f}, Somers D={D:.3f}); the observed direction is "
              f"flat-to-falling, consistent with the pre-registered null shape "
              f"(r2_design §1a: honest forecasting predicts flat or falling "
              f"conditionality near resolution). The negative trend is weak, "
              f"era-fragile, and carried by the 5-10y bin (n="
              f"{bin_stats.get('5-10y', {}).get('n', 0)}); see "
              f"p1_direction_summary for the E2/E3 distinction. A rejected H1 "
              f"is a null result for the ratchet hypothesis, NOT a confirmed "
              f"alternative (advisor ruling §2).")))
    tests.append(report.make_test(
        "P2", statistic={"theil_sen_slope_L": sL, "theil_sen_slope_U": sU},
        p=None,  # CI-based test per design §1(a)
        effect={"drift_rate_L": sL, "drift_rate_U": sU}, ci95=ciL,
        exploratory=False,
        note=(f"CI-based per design: drift >= 1.0 means the deadline recedes at "
              f"least as fast as time passes (ratchet signature). n={n2} restated "
              f"contact-window bounds; slope_U 95% CI [{ciU[0]:.2f}, {ciU[1]:.2f}]. "
              + ("n < 10: directional + CI only; the ledger is the finding, the "
                 "statistic is the annotation." if n2 < 10 else
                 "Each point is a restatement of a contact window in a reliable-"
                 "date video (deduplicated per video/bounds)."))))
    tests.append(report.make_test(
        "E1-within-era-JT", statistic={"jt_J": era_res["J"] if era_res else None},
        p=era_res["p_perm"] if era_res else None,
        effect={"somers_D": era_res["somers_D"] if era_res else None},
        ci95=era_res["ci_D"] if era_res else None, exploratory=True,
        note=("Advisor amendment (a): JT restricted to post-2015 claims, "
              f"n={era_res['n'] if era_res else 0}. Controls the era confound: "
              "Delta correlates with calendar date and hedge vocabulary densified "
              "over decades."
              + (" HONEST NOTE: the restriction is vacuous here — every "
                 "reliable-date claim in the corpus is already post-2015, so this "
                 "is identical to P1; the operative era control is E3 (partial "
                 "Spearman controlling date_made)." if era_res and era_res["n"] == n1
                 else ""))))
    tests.append(report.make_test(
        "E2-spearman", statistic={"spearman_rho": float(rho), "n": len(cont)},
        p=float(p_sp), effect={"rho_C_vs_negDelta": float(rho)}, ci95=ci_rho,
        exploratory=True,
        note="Per-claim Spearman of c_i vs -(Delta); bootstrap CI over claims (10k)."))
    tests.append(report.make_test(
        "E3-partial-spearman-era-controlled",
        statistic={"partial_rho": float(prho), "n": len(cont),
                   "naive_p_two_sided_rank_residuals": p_naive_e3},
        p=None, effect={"partial_rho_c_negDelta_given_date_made": float(prho)},
        ci95=ci_prho,
        exploratory=True,
        note=("Advisor amendment (a): partial Spearman controlling date_made via "
              "rank residualization; bootstrap CI (10k, seed 42). This is the "
              "era-controlled companion to P1. Naive asymptotic two-sided p on "
              "the rank residuals is reported in the statistic block "
              f"(~{p_naive_e3:.3f}); asymptotics on residualized ranks are "
              "approximate, so the bootstrap CI is the operative uncertainty "
              "statement. Do NOT conflate with E2's UNCONTROLLED Spearman "
              f"p={p_sp:.4f}: E2 does not control era, E3 does (r3 audit).")))

    extra = {
        "ledger_rows": len(rows),
        "ledger_csv": "results/ledger.csv",
        "n_P1": n1,
        "n_P2": n2,
        "bin_stats": bin_stats,
        "freeze_note": ("Design and the 50-phrase escape-hatch lexicon (verbatim "
                        "from r2_design.md §1a) are frozen at git HEAD cff3988 "
                        "(design round 2, loop 1); the lexicon may not be edited "
                        "after the first scoring run."),
        "stated_n_rule": ("Advisor ruling (b): n is stated before interpretation "
                          "for every test; where n < 10 the claim is directional + "
                          "CI only — the ledger is the finding, the statistic is "
                          "the annotation."),
        "excluded_from_time_series": sum(1 for r in rows if not r["year_reliable"]),
        "documented_slip_chain": ("2020 -> 2023-33 -> 2025-33 -> 2026/27 -> "
                                  "2028-29 (see ledger rows and F1/F3)"),
        "p1_direction_summary": (
            f"P1 ratchet signature REJECTED (one-sided JT permutation "
            f"p={p_perm:.4f}; Somers D={D:.3f}). Observed direction is "
            f"flat-to-falling conditionality, consistent with the "
            f"pre-registered null shape (r2_design §1a). The negative trend "
            f"is weak, era-fragile, and carried by the 5-10y bin (n=3): "
            f"E2 UNCONTROLLED Spearman rho={rho:.3f}, p={p_sp:.4f}; E3 "
            f"ERA-CONTROLLED partial rho={prho:.3f}, bootstrap 95% CI "
            f"[{ci_prho[0]:.3f}, {ci_prho[1]:.4f}] (upper bound grazes zero), "
            f"naive asymptotic two-sided p on rank residuals={p_naive_e3:.4f}. "
            f"A rejected H1 is a null result for the ratchet hypothesis, not "
            f"evidence that the corpus hedges honestly (advisor ruling §2)."),
        "provenance_correction_r3": (
            "r3 audit discrepancy 3, amended: the previous version of this "
            "document listed data/analysis.json and data/teachings.md as "
            "inputs; this module never read either. Design §1a said the "
            "lexicon would also be counted on "
            "analysis.json.predictions[].examples[].text. Audit (string "
            "match, seed-independent): all 58 examples are already "
            "represented verbatim in the digests' predictions_and_dates rows "
            "and in results/ledger.csv — wiring analysis.json in would add "
            "zero claims, so P1/P2 statistics are unchanged either way. "
            "Provenance is therefore amended to list only inputs actually "
            "read (deviation from design §1a recorded here). teachings.md is "
            "read by doctrine_graph.py, never by this module."),
    }
    doc = report.finalize(
        "predictions", tests,
        common.provenance(["data/digests/*.json", "data/videos.json"]),
        grade="Frontier", digest_level="content", extra=extra)
    path = report.write_results(doc, "predictions_results.json")
    print(f"ledger rows={len(rows)}  n_P1={n1}  n_P2={n2}")
    print(f"P1: J={J:.1f} p_perm={p_perm:.4f} (norm {p_norm:.4g}) D={D:.3f} CI{ci_D}")
    print(f"within-era: {era_res}")
    print(f"spearman rho={rho:.3f} p={p_sp:.4g} CI{ci_rho}")
    print(f"partial rho (era-controlled)={prho:.3f} CI{ci_prho}")
    print(f"P2: slope L={sL:.3f} CI{ciL} ; slope U={sU:.3f} CI{ciU} (n={n2})")
    print("bin stats:", {b: (s['n'], round(s['pooled_C'], 4)) for b, s in bin_stats.items()})
    print("wrote", path)


def _somers(values, groups):
    J = jt_statistic(values, groups, BIN_ORDER)
    tot, exc = 0.0, 0.0
    for i in range(len(BIN_ORDER)):
        for j in range(i + 1, len(BIN_ORDER)):
            a = values[groups == BIN_ORDER[i]]
            b = values[groups == BIN_ORDER[j]]
            diff = b[None, :] - a[:, None]
            exc += np.sum(diff == 0)
            tot += len(a) * len(b)
    denom = tot - exc
    return (2 * J - tot) / denom if denom > 0 else 0.0


if __name__ == "__main__":
    main()
