"""rubric_calibration.py — round-5 novel module (advisor-approved, WITH TEETH).

Retroactive calibration of the frozen 2027 open-contact rubric against the
historical dated claims already in the prediction ledger. EXPLORATORY and
DESCRIPTIVE only — this module measures genre discipline, not truth; no output
speaks to origin.

============================ HARD NO-TUNING CLAUSE ============================
The 2027 rubric (verbatim in FROZEN_RUBRIC below, copied unchanged from
analysis/README.md §"2027 prospective rubric", itself frozen per r2 advisor
ruling d) MAY NOT BE EDITED after this calibration is scored, WHATEVER the
calibration shows. A rubric that misclassifies the past is a finding about the
rubric, published as such — never a license to tune the rubric into agreement
with history, because a rubric fitted to the past is worthless for 2027
(r4 advisor, round-5 approval constraint). If this clause is unacceptable, the
module does not run. Calibration failures ship at the same prominence as
successes.
===============================================================================

Scoring protocol (pre-specified in this file BEFORE outcomes are tabulated;
the first run of this module is the tabulation):

  POPULATION. All rows of results/ledger.csv (n = 164 dated claims).

  ELIGIBILITY SCREEN (deterministic, applied in order; every row is
  dispositioned and every exclusion reason is serialized):
    S1  not contact_related            -> excluded: not an open-contact claim
        (the rubric's claim-under-test is "open contact"; e.g. the 2016
        "everything will change" cluster is dispositioned here or in S3).
    S2  no parseable stated window     -> excluded: no stated deadline.
    S3  event-logistics or historical/biographical reference (documentary
        premieres, conferences, Roswell/Harmonic Convergence/channeling-origin
        retrospectives, CE-5 attempts) -> excluded: not a dated prediction of
        an open-contact outcome.
    S4  window upper bound <= 2025 (fully elapsed at the corpus cutoff,
        2026-06-30)                    -> SCORABLE (resolved).
    S5  window upper bound >= 2026     -> OPEN: enumerated and disclosed with
        elapsed-portion status, never scored.

  SCORING (blind-ish). The scorer applies ONLY the frozen rubric definitions
  to a frozen public-record fact table (PUBLIC_RECORD below), compiled from
  the public record independently of the claim text. Claim text determines
  only the deadline; the outcome class is looked up, never judged ad hoc:
    full    — a rubric full criterion met by the stated deadline;
    partial — a rubric partial criterion met by the stated deadline;
    failure — neither, by the stated deadline.
  The rubric is blind to hedging: a claim hedged "possible" is scored on the
  outcome it points at (this is a property of the rubric, disclosed, not a
  scoring choice made after seeing outcomes).

  PASS RATE. (full + partial) / n_resolved, with a Clopper–Pearson 95% bound
  as descriptive annotation only. Ledger rows are doctrinally correlated
  (one corpus, one source); no independence is claimed and no inference is
  drawn. There are no positive instances in history, so the calibration
  estimates the rubric's historical SPECIFICITY (false-positive immunity),
  not its sensitivity — this asymmetry is itself a reported finding.

Seed 42 (reserved; the module is deterministic). Outputs:
  results/rubric_results.json, figures/fig_f8_rubric_calibration.png
"""
from __future__ import annotations

import csv
import os
import re
from collections import Counter

import numpy as np
from scipy import stats

import common
from common import RESULTS, FIGURES
import report

BANNER = "measures genre discipline, not truth"
CORPUS_CUTOFF = "2026-06-30"   # corpus end (mid-2026)
RESOLVED_UPPER_MAX = 2025      # windows with upper <= 2025 are fully elapsed
NO_TUNING_CLAUSE = (
    "HARD NO-TUNING CLAUSE (r4 advisor constraint, binding): the frozen 2027 "
    "rubric may not be edited after this calibration is scored, whatever it "
    "shows. A rubric that misclassifies the past is a finding about the "
    "rubric, published as such — never a license to tune the rubric into "
    "agreement with history; a rubric fitted to the past is worthless for "
    "2027.")

# ---------------------------------------------------------------- frozen rubric
# VERBATIM copy of analysis/README.md §"2027 prospective rubric (frozen,
# tightened per advisor ruling d)". Editing this text after the first scoring
# run is forbidden by the no-tuning clause above.
FROZEN_RUBRIC = {
    "claim_under_test": ("'open contact' within the window currently stated "
                         "as 2027 (in-corpus slips logged as ratchet events, "
                         "never edits to the rubric)"),
    "full": ("a national government or the UN formally confirms non-human "
             "intelligence and initiates a public diplomatic/communication "
             "exchange, OR a non-human craft/entity is publicly presented and "
             "independently verified by >=2 major scientific institutions"),
    "partial": ("an official government statement using explicit "
                "non-human-origin language (not 'unknown') about materials or "
                "craft, verified by a national laboratory or peer-reviewed "
                "analysis; or a mass-witnessed (>=1,000 independent "
                "witnesses), multi-instrument (>=2 independent instrument "
                "classes, e.g. radar + optical — not two cameras) event "
                "officially unresolved and endorsed as anomalous by >=2 "
                "national space/defense agencies"),
    "failure": "neither criterion met by the stated deadline",
}

# ------------------------------------------------------- frozen fact table
# Public-record evaluation of the frozen rubric's criteria, by year, compiled
# independently of the claim texts (the blind-ish arm: outcomes are looked up
# here, never inferred from claims). Every year <= 2025 evaluates identically:
# no rubric full or partial criterion has ever been met. Near-miss events are
# reviewed below with the specific criterion each fails, so the screen is seen
# to engage the real record rather than wave it through.
def public_record(year: int) -> dict:
    """Frozen rubric criteria evaluated against the public record for `year`.
    Returns which criteria were met by end of that year."""
    return {
        "full_gov_or_un_confirms_nhi_with_exchange": False,
        "full_craft_verified_by_2plus_scientific_institutions": False,
        "partial_explicit_nonhuman_language_lab_verified": False,
        "partial_mass_witness_multiinstrument_2plus_agencies": False,
    }


NEAR_MISS_REVIEW = [
    {"event": "2017 NYT AATIP/ATI disclosure + Navy videos",
     "criteria_failed": ("language was 'unknown/unidentified', never explicit "
                         "non-human-origin; no national-laboratory or "
                         "peer-reviewed verification -> fails tightened "
                         "partial; no diplomatic exchange -> fails full")},
    {"event": "2021 ODNI UAP preliminary assessment",
     "criteria_failed": ("'unidentified', officially unresolved but NOT "
                         "endorsed as anomalous by >=2 national space/defense "
                         "agencies; no instrument-class-verified mass event -> "
                         "fails partial")},
    {"event": "2022–2023 US congressional UAP hearings (incl. Grusch "
              "testimony)",
     "criteria_failed": ("sworn testimony is not an official government "
                         "statement of non-human origin; no national-lab or "
                         "peer-reviewed verification of materials -> fails "
                         "partial")},
    {"event": "2024 AARO Historical Record Report vol. 1",
     "criteria_failed": ("affirmatively reports NO non-human-origin evidence — "
                         "the opposite of the required explicit language -> "
                         "fails partial and full")},
    {"event": "Historical mass-sighting waves (e.g. 1952 Washington, 1997 "
              "Phoenix)",
     "criteria_failed": ("no official endorsement as anomalous by >=2 national "
                         "space/defense agencies; no explicit non-human-origin "
                         "statement -> fail partial")},
]

# ---------------------------------------------------------- eligibility screen
EVENT_LOGISTICS_RE = re.compile(
    r"documentar|premiere|theatrical|conference|expo|event in|showing of", re.I)
HISTORICAL_RE = re.compile(
    r"Roswell|Harmonic Convergence|first contact with Bashar|began channeling|"
    r"abduction|witnessed UFO|initiated Darryl|CE-5|crash—first", re.I)


def screen_row(i, r):
    """Return (disposition, reason). Deterministic; order fixed by protocol."""
    if r["contact_related"] != "True":
        return ("excluded_not_contact",
                "not an open-contact claim (rubric scope)")
    if not r["window_upper"]:
        return ("excluded_no_deadline", "no parseable stated window/deadline")
    if EVENT_LOGISTICS_RE.search(r["claim"]):
        return ("excluded_event_logistics",
                "event logistics (premiere/conference), not an open-contact "
                "outcome claim")
    if HISTORICAL_RE.search(r["claim"]):
        return ("excluded_historical_reference",
                "historical/biographical reference, not a prediction")
    hi = int(r["window_upper"])
    if hi <= RESOLVED_UPPER_MAX:
        return ("scorable_resolved",
                f"window upper bound {hi} fully elapsed at corpus cutoff "
                f"{CORPUS_CUTOFF}")
    return ("open",
            f"window upper bound {hi} >= 2026: not yet scorable at corpus "
            f"cutoff {CORPUS_CUTOFF}")


def score_resolved(r):
    """Blind-ish scoring: outcome looked up from the frozen fact table at the
    claim's stated deadline. Claim text is never consulted here."""
    hi = int(r["window_upper"])
    facts = public_record(hi)
    if facts["full_gov_or_un_confirms_nhi_with_exchange"] or \
            facts["full_craft_verified_by_2plus_scientific_institutions"]:
        return "full", facts
    if facts["partial_explicit_nonhuman_language_lab_verified"] or \
            facts["partial_mass_witness_multiinstrument_2plus_agencies"]:
        return "partial", facts
    return "failure", facts


# ------------------------------------------------------------------ figure F8

def fig_f8(dispositions, scored, path):
    plt = common.apply_style()
    cats = {"scorable_resolved": 3, "open": 2,
            "excluded_event_logistics": 1, "excluded_historical_reference": 1,
            "excluded_not_contact": 0, "excluded_no_deadline": 0}
    labels = {"scorable_resolved": "resolved → scored under frozen rubric",
              "open": "window open at corpus cutoff (disclosed, unscored)",
              "excluded_event_logistics": "excluded: event logistics",
              "excluded_historical_reference": "excluded: historical reference",
              "excluded_not_contact": "excluded: not an open-contact claim",
              "excluded_no_deadline": "excluded: no stated deadline"}
    colors = {"scorable_resolved": "#c8503a", "open": common.AMBER,
              "excluded_event_logistics": common.COPPER,
              "excluded_historical_reference": common.COPPER,
              "excluded_not_contact": common.GRID,
              "excluded_no_deadline": common.GRID}
    fig, ax = plt.subplots(figsize=(12, 6))
    rng = np.random.default_rng(common.SEED)
    for disp, year in dispositions:
        y = cats[disp] + rng.uniform(-0.18, 0.18)
        ax.scatter(year, y, s=42, color=colors[disp],
                   alpha=0.9 if disp == "scorable_resolved" else 0.65,
                   zorder=3 if disp == "scorable_resolved" else 2,
                   edgecolors="none")
    for disp in ("scorable_resolved", "open", "excluded_event_logistics",
                 "excluded_not_contact"):
        ax.scatter([], [], s=42, color=colors[disp], label=labels[disp])
    # annotate the resolved failures (staggered to avoid collisions)
    offsets = [(-165, -4), (20, -34)]
    for s, off in zip(scored, offsets):
        ax.annotate(f"{s['window']} → FAILURE", (int(s["window_upper"]), 3),
                    textcoords="offset points", xytext=off, fontsize=8.5,
                    color="#c8503a", fontweight="bold")
    ax.axvline(2026.5, color=common.TEXT, ls="--", lw=1.2, alpha=0.7)
    ax.text(2025.9, -0.42, "corpus cutoff 2026-06-30", fontsize=8,
            color=common.TEXT, rotation=90, va="bottom", ha="right")
    ax.axvline(2030, color="#c8503a", ls=":", lw=1.4, alpha=0.8)
    ax.text(2030.6, -0.42, "frozen rubric deadline 2030-01-01", fontsize=8,
            color="#c8503a", rotation=90, va="bottom")
    ax.set_yticks([0, 1, 2, 3],
                  ["excluded (scope/deadline)", "excluded (logistics/history)",
                   "open windows", "resolved & scored"])
    ax.set_xlabel("stated window upper bound (year)")
    n_res = len(scored)
    n_fail = sum(1 for s in scored if s["score"] == "failure")
    # three-line wrap keeps the title inside the axes width (no right-edge clip)
    ax.set_title(
        "F8. Retroactive calibration of the FROZEN 2027 rubric on historical\n"
        f"dated ledger claims — resolved claims: n = {n_res}; full 0, "
        f"partial 0, failure {n_fail}\n"
        f"(historical pass rate 0/{n_res}). Rubric frozen regardless of "
        "outcome (no-tuning clause).", fontsize=9.5)
    ax.legend(fontsize=8, framealpha=0.2, loc="upper left")
    ax.set_xlim(1940, 2065)
    common.badge(fig, "content", "Frontier", exploratory=True,
                 extra="descriptive calibration (round 5); rubric frozen — no tuning")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ main

def main():
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(FIGURES, exist_ok=True)
    with open(os.path.join(RESULTS, "ledger.csv")) as f:
        rows = list(csv.DictReader(f))

    dispositions = []   # (disposition, window_upper_year) for the figure
    scored, open_windows, exclusions = [], [], Counter()
    for i, r in enumerate(rows):
        disp, reason = screen_row(i, r)
        if disp.startswith("excluded"):
            exclusions[disp] += 1
            if r["window_upper"]:
                dispositions.append((disp, int(r["window_upper"])))
            continue
        hi = int(r["window_upper"])
        if disp == "scorable_resolved":
            cls, facts = score_resolved(r)
            scored.append({
                "ledger_row": i, "video_id": r["video_id"],
                "date_made": r["date_made"] or None,
                "year_reliable": r["year_reliable"] == "True",
                "window": r["date_str"], "window_lower": int(r["window_lower"]),
                "window_upper": hi, "claim": r["claim"],
                "score": cls, "rubric_facts_at_deadline": facts,
            })
            dispositions.append((disp, hi))
        else:  # open
            open_windows.append({
                "ledger_row": i, "window": r["date_str"],
                "window_lower": int(r["window_lower"]), "window_upper": hi,
                "status": ("open at corpus cutoff " + CORPUS_CUTOFF +
                           "; no rubric full/partial criterion met in the "
                           "elapsed portion of the window to date"),
            })
            dispositions.append((disp, hi))

    n_res = len(scored)
    tally = Counter(s["score"] for s in scored)
    n_pass = tally.get("full", 0) + tally.get("partial", 0)
    pass_rate = n_pass / n_res if n_res else None
    # Clopper–Pearson 95% bound, descriptive annotation only (rows are
    # doctrinally correlated; no independence claimed).
    if n_res:
        cp_lo = float(stats.beta.ppf(0.025, n_pass, n_res - n_pass + 1)) \
            if n_pass else 0.0
        cp_hi = float(stats.beta.ppf(0.975, n_pass + 1, n_res - n_pass)) \
            if n_pass < n_res else 1.0
    else:
        cp_lo = cp_hi = None

    # canonical slip-chain window-level table (advisor scope: 2020, 2023-33,
    # 2025-33, 2026/27, 2028-29)
    chain = [
        {"window": "2020", "status": "resolved",
         "score": "failure",
         "note": "original window start; elapsed without any rubric criterion "
                 "met; restated as 2023–33 (ratchet event)"},
        {"window": "2023–2033", "status": "open",
         "score": None,
         "note": "lower bound elapsed: no criterion met in elapsed portion; "
                 "window runs to 2033"},
        {"window": "2025–2033", "status": "open", "score": None,
         "note": "re-issued window; no criterion met to date"},
        {"window": "2026/27", "status": "open", "score": None,
         "note": "current canonical window; the 2027 preregistered watch "
                 "applies"},
        {"window": "2028–2029", "status": "open", "score": None,
         "note": "in-corpus re-issue (ratchet event), logged not edited"},
    ]

    # 2016-cluster disposition (task scope: show the screen engaged it)
    cluster2016 = [r for r in rows if r["window_lower"] == "2016"]
    c16 = Counter(screen_row(i, r)[0]
                  for i, r in enumerate(rows) if r["window_lower"] == "2016")

    fig_f8(dispositions, scored,
           os.path.join(FIGURES, "fig_f8_rubric_calibration.png"))

    tests = [report.make_test(
        "E10-retroactive-rubric-calibration",
        statistic={"n_ledger_rows": len(rows),
                   "n_resolved_scored": n_res,
                   "score_tally": dict(tally),
                   "n_open_windows_disclosed": len(open_windows),
                   "exclusions": dict(exclusions),
                   "historical_pass_rate": pass_rate},
        p=None,
        effect={"historical_pass_rate_full_plus_partial": pass_rate},
        ci95=[cp_lo, cp_hi],
        exploratory=True,
        note=("Frozen 2027 rubric applied unchanged to resolved historical "
              f"dated claims (window upper <= {RESOLVED_UPPER_MAX}): "
              f"{n_res} resolved claims, scores "
              f"{dict(tally)}; historical pass rate {n_pass}/{n_res} "
              f"(Clopper–Pearson 95% [{cp_lo:.3f}, {cp_hi:.3f}] — descriptive "
              "annotation only; ledger rows are doctrinally correlated, no "
              "independence claimed). The calibration establishes the "
              "rubric's historical SPECIFICITY (no false positives on the "
              "past); sensitivity is UNKNOWABLE from history because no true "
              "open-contact event exists to detect. Scoring was blind-ish: "
              "outcomes looked up from a frozen public-record fact table, "
              "never judged from claim text. " + NO_TUNING_CLAUSE))]

    extra = {
        "banner": BANNER,
        "module_note": ("Round-5 novel module, approved by the r4 advisor "
                        "with the no-tuning constraint. Retroactive "
                        "calibration baseline for the 2027 watch. "
                        "EXPLORATORY, descriptive; no p-value by design."),
        "no_tuning_clause": NO_TUNING_CLAUSE,
        "frozen_rubric_verbatim": FROZEN_RUBRIC,
        "scoring_protocol": ("Pre-specified in this module before tabulation: "
                             "eligibility screen S1–S5 (deterministic, ordered)"
                             ", blind-ish lookup scoring against a frozen "
                             "public-record fact table, pass rate = (full + "
                             "partial)/n_resolved."),
        "corpus_cutoff": CORPUS_CUTOFF,
        "public_record_near_miss_review": NEAR_MISS_REVIEW,
        "scored_claims": scored,
        "open_windows_disclosed": open_windows,
        "canonical_slip_chain_windows": chain,
        "cluster_2016_disposition": {
            "n_rows": len(cluster2016),
            "screen_counts": dict(c16),
            "note": ("The 2016 cluster (First Contact documentary premieres; "
                     "'everything will change by fall 2016') passes through "
                     "the eligibility screen and is excluded as event "
                     "logistics / not-open-contact — the rubric's scope "
                     "discipline is part of what is being calibrated.")},
        "calibration_interpretation": (
            "Historical pass rate 0/{n} under the frozen rubric. Baseline for "
            "the 2027 watch: any full or partial score at the 2030 deadline "
            "would be unprecedented against this corpus's entire dated-claim "
            "history. The rubric is stringent — it has never been satisfied "
            "by any event in the public record (see near-miss review) — so a "
            "2027 pass is a high-credibility signal, and a 2027 failure "
            "continues the documented base rate. The rubric is NOT modified "
            "in response to this calibration (no-tuning clause).".format(n=n_res)),
        "cross_references": {
            "rubric_source": "analysis/README.md §2027 prospective rubric "
                             "(frozen, tightened per advisor ruling d)",
            "ledger": "results/ledger.csv",
            "slip_chain": "predictions_results.json.documented_slip_chain",
        },
    }
    doc = report.finalize(
        "rubric_calibration", tests,
        common.provenance(["results/ledger.csv",
                           "frozen rubric text: analysis/README.md §2027 "
                           "prospective rubric (verbatim, unedited)"],
                          reverification="deterministic; no stochastic steps"),
        grade="Frontier", digest_level="content", extra=extra)
    doc["banner"] = BANNER
    path = report.write_results(doc, "rubric_results.json")
    print(f"ledger rows={len(rows)}  resolved={n_res}  tally={dict(tally)}  "
          f"pass_rate={pass_rate}  CP95=[{cp_lo:.3f},{cp_hi:.3f}]")
    print(f"open windows disclosed={len(open_windows)}  "
          f"exclusions={dict(exclusions)}")
    print(f"2016 cluster: {len(cluster2016)} rows -> {dict(c16)}")
    print("wrote", path)


if __name__ == "__main__":
    main()
