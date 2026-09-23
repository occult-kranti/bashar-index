"""demand.py — H4 Q&A demand dynamics (P3, P4).

r2_design.md §1(b), with an HONEST DATA DEVIATION recorded up front:
  analysis.json.questions stores the 949 classified questions only as aggregate
  per-tag counts plus 99 sampled examples; per-question tag assignments keyed to
  video_id are NOT stored in the repo (digests' qa_topics carry no tag field).
  Therefore:
    * P3 is run on per-video 20-tag topic-share vectors (digests'
      topic_percentages, present for all 75 videos), aggregated to a
      tag x content_type table measured in percentage points. This is the
      in-repo traceable analog of the question-count table; the measurement
      caveat is stated in every output.
    * A small-sample cross-check on the 99 sampled examples is reported as
      EXPLORATORY: the sample covers only 2 of 4 content types, so the
      asymptotic chi2 is structurally inapplicable (zero expected cells);
      a Monte-Carlo permutation p (margins fixed) is used instead.
    * P4 is a binomial GLM on per-video disclosure share (successes =
      round(share * n_questions), trials = n_questions), reliable-year videos
      2024-2026, per design.

Seed 42. Outputs: results/demand_results.json,
figures/fig_f4_demand_mosaic.png, fig_f5_disclosure_trend.png
"""
from __future__ import annotations

import os
from collections import defaultdict

import numpy as np
from scipy import stats
import statsmodels.api as sm

import common
from common import SEED, RESULTS, FIGURES
import report

RNG = np.random.default_rng(SEED)
N_BOOT = 10_000
N_PERM = 10_000
DISCLOSURE_TAG = "et_contact_disclosure_2027"
V_THRESHOLD = 0.2
BASE_RATE = 16.8  # frozen base rate note (design §1b)

TYPES = ["Full session (re-upload)", "Interview with Darryl Anka",
         "Clip / excerpt", "Official highlight clip"]


def load_joined():
    tags = [t["tag"] for t in common.load_analysis()["tags"]]
    vmap = {v["video_id"]: v for v in common.load_videos()}
    rows = []
    for d in common.load_digests():
        v = vmap[d["video_id"]]
        tp = d.get("topic_percentages") or {}
        vec = np.array([float(tp.get(t, 0.0)) for t in tags])
        rows.append({
            "video_id": d["video_id"],
            "content_type": v["content_type"],
            "year": v.get("year"),
            "year_reliable": bool(v.get("year_reliable")),
            "n_questions": len(d.get("qa_topics") or []),
            "vec": vec,  # percentage points per tag, sums to ~100
        })
    return tags, rows


def contingency(rows, tags):
    """tag x type table in summed percentage points."""
    tab = np.zeros((len(tags), len(TYPES)))
    for r in rows:
        j = TYPES.index(r["content_type"])
        tab[:, j] += r["vec"]
    return tab


def cramers_v(tab):
    chi2 = stats.chi2_contingency(tab, correction=False)[0]
    n = tab.sum()
    r, k = tab.shape
    return float(np.sqrt(chi2 / (n * (min(r, k) - 1))))


def bias_corrected_v(tab):
    chi2 = stats.chi2_contingency(tab, correction=False)[0]
    n = tab.sum()
    r, k = tab.shape
    phi2 = max(0.0, chi2 / n - (k - 1) * (r - 1) / (n - 1))
    rb = r - (r - 1) ** 2 / (n - 1)
    kb = k - (k - 1) ** 2 / (n - 1)
    denom = min(kb - 1, rb - 1)
    return float(np.sqrt(phi2 / denom)) if denom > 0 else 0.0


def cluster_boot_v(rows, tags, n_boot=N_BOOT):
    """Cluster bootstrap over videos within content-type strata."""
    by_type = defaultdict(list)
    for r in rows:
        by_type[r["content_type"]].append(r)
    vs = []
    for _ in range(n_boot):
        tab = np.zeros((len(tags), len(TYPES)))
        for j, t in enumerate(TYPES):
            pool = by_type[t]
            idx = RNG.integers(0, len(pool), len(pool))
            for i in idx:
                tab[:, j] += pool[i]["vec"]
        vs.append(cramers_v(tab))
    return [float(np.percentile(vs, 2.5)), float(np.percentile(vs, 97.5))]


def permutation_null(rows, tags, n_perm=N_PERM):
    """Shuffle content_type within year strata (reliable-year videos only);
    recompute chi2. Returns observed chi2 on the subset and permutation p."""
    sub = [r for r in rows if r["year_reliable"] and r["year"]]
    tab_obs = contingency(sub, tags)
    chi2_obs = stats.chi2_contingency(tab_obs, correction=False)[0]
    years = np.array([r["year"] for r in sub])
    cnt = 1
    for _ in range(n_perm):
        perm_types = np.array([r["content_type"] for r in sub], dtype=object)
        for y in np.unique(years):
            mask = years == y
            perm_types[mask] = RNG.permutation(perm_types[mask])
        tab = np.zeros((len(tags), len(TYPES)))
        for r, t in zip(sub, perm_types):
            tab[:, TYPES.index(t)] += r["vec"]
        if stats.chi2_contingency(tab, correction=False)[0] >= chi2_obs:
            cnt += 1
    return chi2_obs, cnt / (n_perm + 1), len(sub)


# ------------------------------------------------------------------ figures

def fig_mosaic(tab, tags, path, labels):
    plt = common.apply_style()
    exp = np.outer(tab.sum(1), tab.sum(0)) / tab.sum()
    res = (tab - exp) / np.sqrt(exp + 1e-12)
    fig, ax = plt.subplots(figsize=(9, 8))
    vmax = np.nanmax(np.abs(res))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("ambercopper",
                                             [common.COPPER, common.BG, common.AMBER])
    im = ax.imshow(res, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(TYPES)),
                  [t.replace(" (", "\n(").replace(" clip", "\nclip")
                   for t in TYPES], fontsize=8)
    ax.set_yticks(range(len(tags)), labels, fontsize=8)
    for i in range(len(tags)):
        for j in range(len(TYPES)):
            ax.text(j, i, f"{res[i, j]:+.1f}", ha="center", va="center",
                    fontsize=7, color=common.TEXT)
    ax.set_title("F4. Tag × content-type standardized Pearson residuals\n"
                 "(amber = over-represented, copper = under-represented)")
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.7, label="standardized residual")
    common.badge(fig, "content", "Frontier", exploratory=False, extra="P3 (primary)")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_trend(fit, by_year, path, note):
    plt = common.apply_style()
    yrs = sorted(by_year)
    share = [100 * by_year[y]["succ"] / by_year[y]["trials"] for y in yrs]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(yrs, share, "o", color=common.AMBER, ms=9,
            label="observed disclosure-question share (%)")
    xs = np.linspace(min(yrs), max(yrs), 100)
    X = sm.add_constant(xs)
    ax.plot(xs, 100 * fit.predict(X), color=common.COPPER, lw=2,
            label="fitted logistic trend")
    ci = fit.get_prediction(X).summary_frame(alpha=0.05)
    ax.fill_between(xs, 100 * ci["mean_ci_lower"], 100 * ci["mean_ci_upper"],
                    color=common.COPPER, alpha=0.15, label="95% confidence band")
    ax.axhline(BASE_RATE, color=common.TEXT, ls=":", lw=1, alpha=0.6,
               label=f"frozen base rate {BASE_RATE}% (all questions)")
    ax.set_xticks(yrs)
    ax.set_xlabel("year (reliable-year videos only)")
    ax.set_ylabel("et_contact_disclosure_2027 share of Q&A (%)")
    ax.set_title("F5. Disclosure-topic share over time\n" + note, fontsize=10)
    ax.legend(fontsize=8, framealpha=0.2, loc="upper left")
    common.badge(fig, "content", "Frontier", exploratory=False, extra="P4 (primary)")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ main

def main():
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(FIGURES, exist_ok=True)
    aj = common.load_analysis()
    tags, rows = load_joined()
    labels = {t["tag"]: t["label"] for t in aj["tags"]}
    tag_labels = [labels[t] for t in tags]

    # ---- P3: chi2 + Cramer's V on full 75-video percentage-point table
    tab = contingency(rows, tags)
    chi2, p_chi2, dof, _ = stats.chi2_contingency(tab, correction=False)
    V = cramers_v(tab)
    Vbc = bias_corrected_v(tab)
    ci_V = cluster_boot_v(rows, tags)
    confirmed_p3 = bool(p_chi2 < report.ALPHA and V > V_THRESHOLD)

    # permutation null within year strata (reliable-year videos only)
    chi2_sub, p_perm, n_sub = permutation_null(rows, tags)
    sub_rows = [r for r in rows if r["year_reliable"] and r["year"]]
    V_sub = cramers_v(contingency(sub_rows, tags))
    p_sub = stats.chi2_contingency(contingency(sub_rows, tags),
                                   correction=False)[1]

    # video-cluster sensitivity: Kruskal–Wallis per tag on video-level shares
    kw = {}
    for i, t in enumerate(tags):
        groups = [[r["vec"][i] for r in rows if r["content_type"] == ty]
                  for ty in TYPES]
        H, p = stats.kruskal(*groups)
        kw[t] = {"H": float(H), "p": float(p)}
    n_kw_sig = sum(1 for v in kw.values() if v["p"] < 0.05)

    # ---- E5: 99-sample exploratory cross-check (r3 audit discrepancy 2, fixed)
    # Root cause of the previously swallowed ValueError: the 99 sampled
    # question examples come ONLY from Full session (re-upload) and Interview
    # with Darryl Anka videos; the Clip/excerpt and Official highlight clip
    # columns are all-zero, so chi2_contingency computes a zero expected cell
    # and raises. Fix: (i) restrict the table to the content types the sample
    # actually covers; (ii) replace the inapplicable asymptotic chi2 (every
    # expected cell < 5) with a Monte-Carlo permutation p that permutes type
    # labels across the 99 examples — this conditions on both margins and is
    # valid for sparse tables (seed 42, 10k permutations). Cramer's V gets a
    # bootstrap CI over examples.
    obs99 = []  # (tag_index, content_type)
    vmap = {v["video_id"]: v for v in common.load_videos()}
    for t in aj["questions"]:
        i = tags.index(t["tag"])
        for e in t["examples"]:
            v = vmap.get(e["video_id"])
            if v:
                obs99.append((i, v["content_type"]))
    n99 = len(obs99)
    sampled_types = sorted({ty for _, ty in obs99}, key=TYPES.index)
    unsampled_types = [ty for ty in TYPES if ty not in sampled_types]
    tab99 = np.zeros((len(tags), len(sampled_types)))

    def chi2_from_pairs(pairs):
        tb = np.zeros_like(tab99)
        for i, ty in pairs:
            tb[i, sampled_types.index(ty)] += 1
        e = np.outer(tb.sum(1), tb.sum(0)) / max(1, tb.sum())
        m = e > 0
        return float(np.sum((tb - e)[m] ** 2 / e[m])), tb

    chi2_99, tab99 = chi2_from_pairs(obs99)
    dof99 = int((tab99.shape[0] - 1) * (tab99.shape[1] - 1))
    V99 = float(np.sqrt(chi2_99 / (n99 * (min(tab99.shape) - 1))))
    exp99 = np.outer(tab99.sum(1), tab99.sum(0)) / n99
    n_sparse99 = int(np.sum(exp99[exp99 > 0] < 5))
    types99 = np.array([ty for _, ty in obs99], dtype=object)
    idx99 = np.array([i for i, _ in obs99])
    cnt = 1  # +1 smoothing
    for _ in range(N_PERM):
        perm = RNG.permutation(types99)
        if chi2_from_pairs(zip(idx99, perm))[0] >= chi2_99 - 1e-12:
            cnt += 1
    p_99 = cnt / (N_PERM + 1)
    boot_v = []
    for _ in range(N_BOOT):
        bi = RNG.integers(0, n99, n99)
        c2, tb = chi2_from_pairs([obs99[k] for k in bi])
        denom = tb.sum() * (min(tb.shape) - 1)
        boot_v.append(float(np.sqrt(c2 / denom)) if denom > 0 else 0.0)
    ci_V99 = [float(np.percentile(boot_v, 2.5)),
              float(np.percentile(boot_v, 97.5))]

    # ---- P4: binomial GLM, reliable-year videos 2024-2026
    di = tags.index(DISCLOSURE_TAG)
    trend_rows = [r for r in rows if r["year_reliable"] and r["year"]
                  and 2024 <= r["year"] <= 2026 and r["n_questions"] > 0]
    y = np.array([round(r["vec"][di] / 100.0 * r["n_questions"])
                  for r in trend_rows], float)
    n = np.array([r["n_questions"] for r in trend_rows], float)
    x = np.array([r["year"] for r in trend_rows], float)
    X = sm.add_constant(x)
    fit = sm.GLM(y / n, X, family=sm.families.Binomial(),
                 freq_weights=n).fit()
    slope = float(fit.params[1])
    se = float(fit.bse[1])
    z = slope / se
    p_one_sided = float(1 - stats.norm.cdf(z))
    ci_slope = [slope - 1.96 * se, slope + 1.96 * se]
    by_year = {}
    for r, yi, ni in zip(trend_rows, y, n):
        by_year.setdefault(r["year"], {"succ": 0, "trials": 0})
        by_year[r["year"]]["succ"] += yi
        by_year[r["year"]]["trials"] += ni
    fitted_shares = [float(fit.predict(sm.add_constant([[1.0, float(yi)]]))[0])
                     for yi in sorted(by_year)]
    monotone = all(a <= b for a, b in zip(fitted_shares, fitted_shares[1:]))
    confirmed_p4 = bool(p_one_sided < report.ALPHA and slope > 0 and monotone)

    # descriptive residual direction for the disclosure tag (r3 audit
    # discrepancy 4: the summary sentence must match F4's actual residuals)
    di_desc = tags.index(DISCLOSURE_TAG)
    exp_full = np.outer(tab.sum(1), tab.sum(0)) / tab.sum()
    res_full = (tab - exp_full) / np.sqrt(exp_full + 1e-12)
    res_disc = {TYPES[j]: float(res_full[di_desc, j])
                for j in range(len(TYPES))}

    # ---- figures
    fig_mosaic(tab, tags, os.path.join(FIGURES, "fig_f4_demand_mosaic.png"),
               tag_labels)
    note = (f"P4 slope={slope:+.2f} log-odds/yr [{ci_slope[0]:+.2f}, "
            f"{ci_slope[1]:+.2f}], one-sided p={p_one_sided:.3f}; "
            f"monotone={monotone}\nn={len(trend_rows)} videos / "
            f"{int(n.sum())} questions, reliable years 2024-2026")
    fig_trend(fit, by_year, os.path.join(FIGURES, "fig_f5_disclosure_trend.png"),
              note)

    # ---- results doc
    tests = []
    tests.append(report.make_test(
        "P3", statistic={"chi2": float(chi2), "dof": int(dof),
                         "n_percentage_points": float(tab.sum())},
        p=float(p_chi2),
        effect={"cramers_v": V, "bias_corrected_v": Vbc}, ci95=ci_V,
        exploratory=False,
        note=(f"Chi2 on 20-tag x 4-type table of summed per-video topic-share "
              f"points (75 videos; per-question tags are not stored in-repo — "
              f"see data_deviation). H4 segmentation confirmed only if p<0.05 "
              f"AND V>0.2 (design threshold): confirmed={confirmed_p3}. "
              f"Cluster bootstrap CI over videos. Permutation null within year "
              f"strata (reliable-year videos, n={n_sub}): chi2={chi2_sub:.1f}, "
              f"permutation p={p_perm:.4f}, asymptotic p={p_sub:.4g}, "
              f"V={V_sub:.3f}. The headline asymptotic p (1e-175) is "
              f"DECORATIVE as count inference — cells are pipeline-estimated "
              f"share points with massive pseudo-replication — and must never "
              f"be quoted without this caveat (advisor ruling §3). The "
              f"operative evidence is: V={V:.3f} clears the pre-registered "
              f"0.2 threshold narrowly (bias-corrected {Vbc:.3f} does not), "
              f"the cluster bootstrap CI clears it entirely, and the "
              f"within-year-strata permutation p={p_perm:.4f} is robust to "
              f"the row-independence problem. P3 confirms digest-level "
              f"topical segmentation by packaging format, NOT question-level "
              f"demand."),
        extra={"permutation_p_within_year_strata": float(p_perm),
               "confirmed_by_threshold": confirmed_p3}))
    tests.append(report.make_test(
        "P4", statistic={"slope_log_odds_per_year": slope, "se": se, "z": float(z)},
        p=p_one_sided,
        effect={"slope": slope}, ci95=[float(ci_slope[0]), float(ci_slope[1])],
        exploratory=False,
        note=(f"Binomial GLM of disclosure-topic share on year, reliable-year "
              f"videos 2024-2026 (n={len(trend_rows)} videos, {int(n.sum())} "
              f"questions). One-sided slope>0 plus monotone fitted shares: "
              f"monotone={monotone}; confirmed={confirmed_p4}. Frozen base "
              f"rate: {BASE_RATE}%."),
        extra={"monotone_fitted_shares": monotone,
               "confirmed_by_threshold": confirmed_p4,
               "base_rate_frozen": BASE_RATE}))
    tests.append(report.make_test(
        "E4-kw-video-cluster-sensitivity",
        statistic={"n_tags_kw_p_lt_0.05": n_kw_sig,
                   "min_kw_p": min(v["p"] for v in kw.values())},
        p=None, effect={"share_of_20_tags_kw_significant": n_kw_sig / 20.0},
        ci95=None,
        exploratory=True,
        note=("Video-level Kruskal–Wallis per tag across content types "
              "(row-independence sensitivity). Full table in "
              "EXPLORATORY_kw_by_tag.")))
    tests.append(report.make_test(
        "E5-sample99-crosscheck",
        statistic={"chi2": float(chi2_99), "dof": int(dof99), "n": n99,
                   "sampled_content_types": list(sampled_types),
                   "unsampled_content_types": list(unsampled_types),
                   "n_expected_cells_lt_5": n_sparse99},
        p=float(p_99), effect={"cramers_v": float(V99)}, ci95=ci_V99,
        exploratory=True,
        note=("Chi2 on the 99 sampled question examples only. The sample "
              "covers just two content types (full sessions + interviews); "
              "clip/highlight columns are structurally zero, which is what "
              "made the asymptotic test raise (zero expected cell) in round "
              "3 — that exception was silently swallowed and the promised "
              "check went missing. Now: table restricted to sampled types; "
              "asymptotic p replaced by a Monte-Carlo permutation p (type "
              "labels permuted across the 99 examples, both margins fixed, "
              "10k, seed 42); V bootstrap-CI'd over examples. Sparse-table "
              "warning stands: expected cells < 5 throughout; directional "
              "cross-check only.")))

    extra = {
        "data_deviation": (
            "Per-question tag assignments keyed to video_id are NOT stored in "
            "the repo (analysis.json.questions carries aggregate counts + 99 "
            "sampled examples; digests' qa_topics carry no tag field). P3/P4 "
            "therefore run on per-video 20-tag topic-share vectors "
            "(digests.topic_percentages, all 75 videos) with per-video question "
            "counts as GLM weights. All cells are pipeline-estimated share "
            "points, not raw question counts."),
        "questions_accounted_for": int(sum(r["n_questions"] for r in rows)),
        "questions_expected": 949,
        "videos_total": len(rows),
        "videos_reliable_year": sum(1 for r in rows if r["year_reliable"]),
        "EXPLORATORY_kw_by_tag": kw,
        "residual_direction_descriptive": {
            "note": ("Design-predicted pattern check (descriptive, not a 5th "
                     "test), corrected per r3 audit discrepancy 4: "
                     "et_contact_disclosure_2027 is OVER-represented in free "
                     f"interviews ({res_disc['Interview with Darryl Anka']:+.1f}) "
                     f"and clips/excerpts ({res_disc['Clip / excerpt']:+.1f}) "
                     "standardized Pearson residuals, but UNDER-represented in "
                     "official highlight clips "
                     f"({res_disc['Official highlight clip']:+.1f}) and full "
                     f"sessions ({res_disc['Full session (re-upload)']:+.1f}). "
                     "The round-3 sentence ('free clips/highlights/interviews "
                     "skew to disclosure') contradicted F4 on the highlight "
                     "column and is retracted: the free-packaging skew to "
                     "disclosure is carried by interviews and clips, not by "
                     "official highlights."),
            "disclosure_row_standardized_residuals": res_disc,
        },
    }
    doc = report.finalize(
        "demand", tests,
        common.provenance(["data/analysis.json", "data/videos.json",
                           "data/digests/*.json"]),
        grade="Frontier", digest_level="content", extra=extra)
    path = report.write_results(doc, "demand_results.json")
    print(f"P3: chi2={chi2:.1f} dof={dof} p={p_chi2:.4g} V={V:.3f} "
          f"(bc {Vbc:.3f}) CI{ci_V} confirmed={confirmed_p3}")
    print(f"    permutation p={p_perm:.4f} (n_sub={n_sub} videos)")
    print(f"P4: slope={slope:+.3f} CI{ci_slope} p1={p_one_sided:.4f} "
          f"monotone={monotone} confirmed={confirmed_p4} "
          f"(n={len(trend_rows)} videos, {int(n.sum())} questions)")
    print(f"KW sensitivity: {n_kw_sig}/20 tags p<0.05; "
          f"E5 sample99: n={n99} chi2={chi2_99:.1f} perm_p={p_99:.4f} "
          f"V={V99:.3f} CI{[round(c, 3) for c in ci_V99]}")
    print("wrote", path)


if __name__ == "__main__":
    main()
