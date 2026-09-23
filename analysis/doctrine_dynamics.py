"""doctrine_dynamics.py — round-4 novel descriptive module (advisor-approved).

"How a canon drifts while claiming immutability." DESCRIPTIVE ONLY — this
module measures genre discipline, not truth; no output speaks to origin.

Two registered descriptive analyses, both fully in-repo:

  (1) Window-polarity flip dynamics. doctrine_graph.py surfaced 73 flips
      (later-stated contact window lying entirely beyond an earlier-stated
      window). Here we characterize the DISTRIBUTION: overshoot (years the
      new lower bound sits past the old upper bound), elapsed time between
      restatements, pairwise slip velocity (years of lower-bound recession
      per year elapsed), and all of it split by era (<=2024 vs >=2025, the
      doctrine_graph era split).

  (2) Liquid emphasis. Kendall's W of within-digest term-salience ranks is
      0.009 — salience ranks are essentially uncorrelated across digests:
      the doctrine is a fixed vocabulary with liquid emphasis. Here we
      distribute the finding across era: W overall / early / late, per-year
      W, and consecutive-digest salience-rank volatility (Spearman of the
      salience vectors and top-5 turnover between adjacent digests).

Seed 42 everywhere. Outputs:
  results/doctrine_dynamics_results.json, figures/fig_f7_dynamics.png
"""
from __future__ import annotations

import os
import re
from collections import Counter

import numpy as np
from scipy import stats

import common
from common import SEED, RESULTS, FIGURES
import report
from predictions import parse_bounds
from doctrine_graph import norm, kendall_w, FREQ_SCORE, TOP_K_W

RNG = np.random.default_rng(SEED)
N_BOOT = 10_000
BANNER = "measures genre discipline, not truth"
ERA_SPLIT = 2024  # <=2024 "early", >=2025 "late" — same split as doctrine_graph


# ------------------------------------------------------------------ flips

def window_rows(digests, vmap):
    """Replicates doctrine_graph.detect_contradictions block (3) exactly:
    contact-mentioning prediction rows on reliable-year videos with a
    parseable window whose upper bound is still in the future at t."""
    rows = []
    for d in digests:
        v = vmap.get(d["video_id"], {})
        t = v.get("year") if v.get("year_reliable") else None
        if not t:
            continue
        for p in d.get("predictions_and_dates") or []:
            txt = " ".join([str(p.get("prediction") or ""),
                            str(p.get("context") or "")])
            if not re.search(r"contact", txt, re.I):
                continue
            lo, hi = parse_bounds(str(p.get("date") or p.get("year")
                                      or p.get("year_or_date") or ""))
            if lo and hi >= t:
                rows.append({"video_id": d["video_id"], "t": t,
                             "lo": lo, "hi": hi})
    rows.sort(key=lambda r: (r["t"], r["lo"], r["hi"]))
    return rows


def find_flips(rows):
    flips = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if b["t"] > a["t"] and b["lo"] > a["hi"]:
                flips.append({
                    "t_earlier": a["t"], "window_earlier": [a["lo"], a["hi"]],
                    "t_later": b["t"], "window_later": [b["lo"], b["hi"]],
                    "overshoot_years": b["lo"] - a["hi"],
                    "elapsed_years": b["t"] - a["t"],
                    "lower_bound_recession": b["lo"] - a["lo"],
                    "slip_velocity": ((b["lo"] - a["lo"]) / (b["t"] - a["t"])),
                    "era_pair": (("early" if a["t"] <= ERA_SPLIT else "late")
                                 + "->" +
                                 ("early" if b["t"] <= ERA_SPLIT else "late")),
                })
    return flips


def era_of(t):
    return "early" if t <= ERA_SPLIT else "late"


def flip_era_summary(flips):
    by_pair = Counter(f["era_pair"] for f in flips)
    by_earlier = Counter(era_of(f["t_earlier"]) for f in flips)
    out = {"by_era_pair": dict(by_pair),
           "by_earlier_statement_era": dict(by_earlier),
           "median_overshoot_by_pair": {}}
    for pair in by_pair:
        vals = [f["overshoot_years"] for f in flips if f["era_pair"] == pair]
        out["median_overshoot_by_pair"][pair] = float(np.median(vals))
    return out


def boot_ci_median(x, n_boot=N_BOOT):
    x = np.asarray(x, float)
    if len(x) == 0:
        return [None, None]
    boots = [np.median(x[RNG.integers(0, len(x), len(x))])
             for _ in range(n_boot)]
    return [float(np.percentile(boots, 2.5)),
            float(np.percentile(boots, 97.5))]


# ------------------------------------------------------------------ liquid emphasis

def salience_matrix(digests, top_terms):
    """m digests x k terms salience (high=3/med=2/low=1/absent=0)."""
    ratings = np.zeros((len(digests), len(top_terms)))
    for i, d in enumerate(digests):
        score = {norm(k["term"]): FREQ_SCORE.get(str(k.get("freq", "")).lower(), 0.5)
                 for k in (d.get("key_terms") or [])}
        for j, t in enumerate(top_terms):
            ratings[i, j] = score.get(t, 0.0)
    return ratings


def liquid_emphasis(digests, vmap):
    from doctrine_graph import build_graph  # reuse doc_count/top-term selection
    glossary = common.load_glossary()
    _, doc_count, _, _, _ = build_graph(glossary, digests)
    top_terms = [t for t, _ in doc_count.most_common(TOP_K_W)]

    years = np.array([vmap[d["video_id"]].get("year")
                      if vmap[d["video_id"]].get("year_reliable") else None
                      for d in digests], dtype=object)
    R_all = salience_matrix(digests, top_terms)
    W_all = kendall_w(R_all)

    # era-split W (reliable-year digests only)
    era_W = {}
    for era in ("early", "late"):
        sel = [i for i, y in enumerate(years)
               if y is not None and era_of(y) == era]
        era_W[era] = {"n_digests": len(sel),
                      "W": kendall_w(R_all[sel]) if len(sel) >= 2 else None}

    # per-year W (years with >= 3 reliable digests)
    per_year = {}
    for y in sorted({y for y in years if y is not None}):
        sel = [i for i, yy in enumerate(years) if yy == y]
        if len(sel) >= 3:
            per_year[int(y)] = {"n_digests": len(sel),
                                "W": kendall_w(R_all[sel])}

    # consecutive-digest salience-rank volatility (reliable-year digests,
    # corpus order = year then video_id)
    order = sorted([i for i, y in enumerate(years) if y is not None],
                   key=lambda i: (years[i], digests[i]["video_id"]))
    pairs = []
    n_undefined = 0
    import warnings
    for a, b in zip(order, order[1:]):
        va, vb = R_all[a], R_all[b]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            rho, _ = stats.spearmanr(va, vb)
        if np.isnan(rho):  # constant salience vector (e.g. all-absent digest)
            rho = None
            n_undefined += 1
        ka = set(np.argsort(-va)[:5].tolist())
        kb = set(np.argsort(-vb)[:5].tolist())
        pairs.append({"from_year": int(years[a]), "to_year": int(years[b]),
                      "spearman": None if rho is None else float(rho),
                      "top5_turnover": 1.0 - len(ka & kb) / 5.0})
    rhos = np.array([p["spearman"] for p in pairs
                     if p["spearman"] is not None])
    turnover = np.array([p["top5_turnover"] for p in pairs])

    # bootstrap CI for W_all over digests (matches doctrine_graph's 2000)
    boot = []
    for _ in range(2000):
        idx = RNG.integers(0, len(digests), len(digests))
        boot.append(kendall_w(R_all[idx]))
    ci_W = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]

    return {
        "top_terms": top_terms,
        "W_overall": float(W_all), "ci_W_overall": ci_W,
        "era_W": era_W, "per_year_W": per_year,
        "consecutive": pairs,
        "mean_consecutive_spearman": float(np.mean(rhos)),
        "ci_consecutive_spearman": boot_ci_median(rhos),
        "median_consecutive_spearman": float(np.median(rhos)),
        "mean_top5_turnover": float(np.mean(turnover)),
        "n_pairs_undefined_constant_vector": n_undefined,
    }


# ------------------------------------------------------------------ figure F7

def fig_dynamics(flips, liq, path, vel_iqr=None, consec=None):
    plt = common.apply_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15.5, 7.4),
                                   gridspec_kw={"width_ratios": [1.25, 1],
                                                "wspace": 0.28})

    # (a) flip timeline: x = date made, y = stated bound year; each flip is a
    # segment from the violated earlier upper bound to the later lower bound.
    for f in flips:
        col = common.AMBER if f["era_pair"] == "late->late" else common.COPPER
        ax1.plot([f["t_earlier"], f["t_later"]],
                 [f["window_earlier"][1], f["window_later"][0]],
                 color=col, lw=0.9, alpha=0.45)
        ax1.plot(f["t_earlier"], f["window_earlier"][1], "o", ms=3,
                 color=common.COPPER, alpha=0.6)
        ax1.plot(f["t_later"], f["window_later"][0], "o", ms=3,
                 color=common.AMBER, alpha=0.6)
    lims = [min(f["t_earlier"] for f in flips) - 1,
            max(max(f["window_later"]) for f in flips) + 2]
    ax1.plot(lims, lims, ls=":", color=common.TEXT, lw=1, alpha=0.6,
             label="y = x (bound = date made)")
    ax1.set_xlabel("date made (reliable-year videos)")
    ax1.set_ylabel("stated window bound (year)")
    cap_extra = ""
    if vel_iqr is not None and consec is not None:
        cap_extra = (f"\nslip velocity median 1.0 yr/yr, IQR "
                     f"[{vel_iqr[0]:.2f}, {vel_iqr[1]:.2f}] (all pairs, "
                     "non-independent); consecutive restatements (elapsed=1y, "
                     f"n={consec['n']}) median {consec['median_slip_velocity_yr_per_yr']:.1f}")
    ax1.set_title(f"F7a. Flip timeline (n = {len(flips)} pairwise flips from 35\n"
                  "window rows): an earlier window's upper bound (copper)\n"
                  "violated by a later lower bound (amber)" + cap_extra,
                  fontsize=9)
    ax1.legend(fontsize=8, framealpha=0.2, loc="upper left")

    # (b) salience-rank volatility: consecutive-digest Spearman over time
    pts = [p for p in liq["consecutive"] if p["spearman"] is not None]
    xs = [p["to_year"] for p in pts]
    ys = [p["spearman"] for p in pts]
    ax2.scatter(xs, ys, s=28, color=common.AMBER, alpha=0.8, zorder=3,
                label="consecutive-digest salience Spearman")
    ax2.axhline(liq["mean_consecutive_spearman"], color=common.COPPER, lw=1.6,
                label=f"mean = {liq['mean_consecutive_spearman']:+.2f}")
    ax2.axhline(0, color=common.TEXT, ls=":", lw=1, alpha=0.5)
    ax2.set_xlabel("year of later digest")
    ax2.set_ylabel("rank correlation of top-15 term salience")
    w = liq["W_overall"]
    we = liq["era_W"]["early"]["W"]
    wl = liq["era_W"]["late"]["W"]
    ax2.set_title("F7b. Liquid emphasis — salience-rank volatility\n"
                  f"Kendall W = {w:.3f} (early {we:.3f}, late {wl:.3f})",
                  fontsize=9.5)
    ax2.legend(fontsize=8, framealpha=0.2, loc="lower left")

    fig.suptitle(f"F7. Doctrine dynamics — {BANNER}", fontsize=12, y=0.99)
    common.badge(fig, "content", "Frontier", exploratory=True,
                 extra="descriptive module (round 4)")
    # rect top lowered so the multi-line panel titles clear the suptitle
    fig.tight_layout(rect=[0, 0.03, 1, 0.88])
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ main

def main():
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(FIGURES, exist_ok=True)
    digests = common.load_digests()
    vmap = {v["video_id"]: v for v in common.load_videos()}

    # (1) flips
    rows = window_rows(digests, vmap)
    flips = find_flips(rows)
    # drift guard: this module's flip count must match doctrine_graph's
    dg_path = os.path.join(RESULTS, "doctrine_results.json")
    if os.path.exists(dg_path):
        import json as _json
        dg = _json.load(open(dg_path))
        dg_flips = next((f["n_flips"] for f in
                         dg.get("EXPLORATORY_contradiction_flags", [])
                         if f["id"] == "window-polarity-flips"), None)
        if dg_flips is not None and dg_flips != len(flips):
            raise report.BadgeError(
                f"flip-count drift: doctrine_graph={dg_flips} vs "
                f"doctrine_dynamics={len(flips)}")
    overshoots = np.array([f["overshoot_years"] for f in flips], float)
    elapsed = np.array([f["elapsed_years"] for f in flips], float)
    velocities = np.array([f["slip_velocity"] for f in flips], float)
    era_summary = flip_era_summary(flips)
    ci_overshoot = boot_ci_median(overshoots)

    # --- r4-advisor mandatory surgery on the E7 slip-velocity headline -------
    # (i)   Report the velocity IQR next to every quoting of the median.
    # (ii)  The previous bootstrap CI of the median over all 73 pairwise
    #       velocities collapsed to [1.0, 1.0]. That interval is a DEGENERATE
    #       BOOTSTRAP ARTIFACT, not an uncertainty statement: the 73 ratios are
    #       all-pairs combinations computed from only 35 window rows (each row
    #       enters ~4 pairs), so the resample treats dependent ratios as
    #       independent, and the discrete median collapses the interval to zero
    #       width. It is REMOVED from serialization; the operative uncertainty
    #       statement is the IQR. The removal is recorded, not hidden.
    # (iii) The all-pairs structure is disclosed wherever n=73 appears.
    # (iv)  The clean form of the velocity claim is the CONSECUTIVE-RESTATEMENT
    #       subset (elapsed = 1 y): the canonical annual slip.
    vel_q25, vel_q75 = (float(np.percentile(velocities, q)) for q in (25, 75))
    consec = np.array([f["slip_velocity"] for f in flips
                       if f["elapsed_years"] == 1], float)
    far = np.array([f["slip_velocity"] for f in flips
                    if f["elapsed_years"] >= 3], float)
    consec_summary = {
        "definition": ("consecutive-restatement subset: flip pairs with "
                       "elapsed_years == 1 (adjacent annual restatements)"),
        "n": int(len(consec)),
        "median_slip_velocity_yr_per_yr": float(np.median(consec)),
        "iqr": [float(np.percentile(consec, 25)),
                float(np.percentile(consec, 75))],
        "share_at_exactly_1": float(np.mean(consec == 1.0)),
    }
    far_summary = {
        "definition": "flip pairs with elapsed_years >= 3",
        "n": int(len(far)),
        "median_slip_velocity_yr_per_yr": float(np.median(far)),
        "iqr": [float(np.percentile(far, 25)),
                float(np.percentile(far, 75))] if len(far) else None,
    }
    velocity_uncertainty = {
        "median_yr_per_yr": float(np.median(velocities)),
        "iqr": [vel_q25, vel_q75],
        "share_at_exactly_1": float(np.mean(velocities == 1.0)),
        "share_below_1": float(np.mean(velocities < 1.0)),
        "share_above_1": float(np.mean(velocities > 1.0)),
        "all_pairs_structure": (f"{len(flips)} pairwise flips from "
                                f"{len(rows)} window rows, non-independent "
                                "(each row enters ~4 pairs)"),
        "removed_degenerate_ci": {
            "value": [1.0, 1.0],
            "status": "REMOVED — degenerate bootstrap artifact, not an "
                      "uncertainty statement (resample over dependent "
                      "all-pairs ratios; discrete median collapses the "
                      "interval to zero width). See r4_advisor.md §2.",
        },
        "headline_subset": "consecutive_restatement_subset",
    }

    # (2) liquid emphasis
    liq = liquid_emphasis(digests, vmap)

    fig_dynamics(flips, liq, os.path.join(FIGURES, "fig_f7_dynamics.png"),
                 vel_iqr=[vel_q25, vel_q75], consec=consec_summary)

    tests = []
    tests.append(report.make_test(
        "E7-window-polarity-flip-dynamics",
        statistic={"n_flips": len(flips),
                   "n_window_rows": len(rows),
                   "all_pairs_structure": (f"{len(flips)} pairwise flips from "
                                           f"{len(rows)} window rows, "
                                           "non-independent"),
                   "median_overshoot_years": float(np.median(overshoots)),
                   "median_elapsed_years": float(np.median(elapsed)),
                   "median_slip_velocity_yr_per_yr": float(np.median(velocities)),
                   "slip_velocity_iqr": [vel_q25, vel_q75],
                   "consecutive_restatement_subset": consec_summary,
                   "elapsed_ge_3_subset": far_summary,
                   "max_overshoot_years": float(overshoots.max())},
        p=None,
        effect={"median_overshoot_years": float(np.median(overshoots))},
        ci95=ci_overshoot,
        exploratory=True,
        note=("Distribution of the window-polarity flips surfaced by "
              "doctrine_graph (later-stated contact window entirely beyond an "
              "earlier-stated one): "
              f"{len(flips)} pairwise flips from {len(rows)} window rows, "
              "NON-INDEPENDENT (all-pairs structure; each row enters ~4 "
              "pairs). Overshoot = new lower bound minus violated old upper "
              "bound; slip velocity = lower-bound recession per year elapsed. "
              f"Median slip velocity {np.median(velocities):.2f} yr/yr with "
              f"IQR [{vel_q25:.2f}, {vel_q75:.2f}] — only "
              f"{100*np.mean(velocities == 1.0):.0f}% of flips sit at exactly "
              "1.0. HEADLINE (clean form): consecutive restatements (elapsed "
              f"= 1 y, n = {len(consec)}) recede at median "
              f"{np.median(consec):.2f} yr/yr; pairs with elapsed >= 3 y "
              f"(n = {len(far)}) recede at median {np.median(far):.2f} yr/yr. "
              "The earlier bootstrap CI of the median ([1.0, 1.0]) is REMOVED "
              "as a degenerate bootstrap artifact over dependent ratios "
              "(r4 advisor mandatory surgery). Descriptive ledger fact, not "
              "inference; no p-value by design.")))
    tests.append(report.make_test(
        "E8-liquid-emphasis-by-era",
        statistic={"W_overall": liq["W_overall"],
                   "W_early_<=2024": liq["era_W"]["early"]["W"],
                   "n_early": liq["era_W"]["early"]["n_digests"],
                   "W_late_>=2025": liq["era_W"]["late"]["W"],
                   "n_late": liq["era_W"]["late"]["n_digests"],
                   "k_terms": TOP_K_W},
        p=None,
        effect={"W": liq["W_overall"]},
        ci95=liq["ci_W_overall"],
        exploratory=True,
        note=("Kendall's W of within-digest term-salience ranks, distributed "
              "across era. W ≈ 0 in every slice: salience ranks are "
              "essentially uncorrelated across digests — the doctrine is a "
              "fixed vocabulary with liquid emphasis. Per-year W in extras. "
              "Descriptive; no p-value by design.")))
    tests.append(report.make_test(
        "E9-consecutive-salience-volatility",
        statistic={"n_adjacent_pairs": len(liq["consecutive"]),
                   "n_pairs_defined": len(liq["consecutive"]) -
                   liq["n_pairs_undefined_constant_vector"],
                   "n_pairs_undefined_constant_vector":
                   liq["n_pairs_undefined_constant_vector"],
                   "mean_spearman": liq["mean_consecutive_spearman"],
                   "median_spearman": liq["median_consecutive_spearman"],
                   "mean_top5_turnover": liq["mean_top5_turnover"]},
        p=None,
        effect={"median_consecutive_spearman":
                liq["median_consecutive_spearman"]},
        ci95=liq["ci_consecutive_spearman"],
        exploratory=True,
        note=("Spearman of top-15 salience vectors between adjacent "
              "reliable-year digests (corpus order), plus top-5 term "
              "turnover. Pairs where a digest's salience vector is constant "
              "(all-absent) have undefined Spearman and are excluded from "
              "the rank-correlation summaries (count disclosed). High "
              "turnover + near-zero rank correlation quantify 'liquid "
              "emphasis'. Descriptive; no p-value by design.")))

    extra = {
        "banner": BANNER,
        "module_note": ("Round-4 novel descriptive module, approved by the r3 "
                        "advisor: 'how a canon drifts while claiming "
                        "immutability'. Descriptive corpus science only; "
                        "nothing here speaks to origin or truth."),
        "era_split_year": ERA_SPLIT,
        "flip_era_distribution": era_summary,
        "flip_overshoot_quantiles": {
            q: float(np.percentile(overshoots, qq))
            for q, qq in [("p25", 25), ("p50", 50), ("p75", 75), ("p90", 90)]},
        "slip_velocity_uncertainty": velocity_uncertainty,
        "consecutive_restatement_subset": consec_summary,
        "elapsed_ge_3_subset": far_summary,
        "per_year_kendall_W": liq["per_year_W"],
        "EXPLORATORY_consecutive_pairs": liq["consecutive"],
        "cross_references": {
            "doctrine_graph": "results/doctrine_results.json (flip detection, "
                              "Kendall W machinery)",
            "slip_chain": "predictions_results.json.documented_slip_chain",
        },
    }
    doc = report.finalize(
        "doctrine_dynamics", tests,
        common.provenance(["data/digests/*.json", "data/videos.json",
                           "data/glossary.json",
                           "results/doctrine_results.json (read-only drift "
                           "guard: flip-count cross-check)"]),
        grade="Frontier", digest_level="content", extra=extra)
    doc["banner"] = BANNER
    path = report.write_results(doc, "doctrine_dynamics_results.json")
    print(f"window rows={len(rows)}  flips={len(flips)}")
    print(f"overshoot median={np.median(overshoots):.1f}y CI{ci_overshoot}; "
          f"velocity median={np.median(velocities):.2f} "
          f"IQR[{vel_q25:.2f}, {vel_q75:.2f}] "
          "(degenerate bootstrap CI [1.0, 1.0] REMOVED — artifact); "
          f"consecutive (elapsed=1y, n={len(consec)}) median="
          f"{np.median(consec):.2f}; elapsed>=3 (n={len(far)}) median="
          f"{np.median(far):.2f}")
    print(f"era distribution: {era_summary['by_era_pair']}")
    print(f"W overall={liq['W_overall']:.4f} CI{liq['ci_W_overall']}; "
          f"early={liq['era_W']['early']['W']:.4f} "
          f"(n={liq['era_W']['early']['n_digests']}), "
          f"late={liq['era_W']['late']['W']:.4f} "
          f"(n={liq['era_W']['late']['n_digests']})")
    print(f"consecutive pairs={len(liq['consecutive'])} "
          f"mean rho={liq['mean_consecutive_spearman']:+.3f} "
          f"mean top5 turnover={liq['mean_top5_turnover']:.2f}")
    print("wrote", path)


if __name__ == "__main__":
    main()
