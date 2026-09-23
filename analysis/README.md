# Bashar-Index analysis suite — rounds 3–4 (implementation + audit fixes)

Evidence-honest panel build over the cloned repo at
`/mnt/agents/lab2/bashar-index` (**HEAD cff3988** — the design, the frozen
lexicon, and every pre-registration are pinned to this commit hash, per the
advisor's absolute-timestamp amendment).

## Reproduce

```bash
cd /mnt/agents/lab2/analysis
python predictions.py        # P1, P2 + ledger (results/ledger.csv)
python demand.py             # P3, P4 (+ E5 99-sample cross-check)
python doctrine_graph.py     # descriptive only
python doctrine_dynamics.py  # descriptive only: flip timeline + liquid emphasis
python rubric_calibration.py # EXPLORATORY: retroactive calibration of frozen 2027 rubric
python acquisition.py        # pilot fetch; --dry-run to only enumerate
python -c "import report; report.family_summary()"   # global Holm family -> results/family_holm.json
```

Dependencies: numpy, scipy, pandas, matplotlib, networkx, statsmodels
(yt-dlp only for acquisition).

**Seed registry: every stochastic procedure uses seed 42** (bootstraps 10,000
resamples; permutation tests 10,000; doctrine bootstrap 2,000; network layout
seed 42). Results are byte-reproducible given the same library versions.

## Multiple-comparison policy (enforced by report.py)

Exactly four primary tests, Holm-corrected as a family at α=0.05:

| id | test | module |
|----|------|--------|
| P1 | H1 conditionality: one-sided Jonckheere–Terpstra of per-claim cᵢ across ordinal Δ bins | predictions.py |
| P2 | H1 drift: Theil–Sen slope of contact-window lower bound L(t) ≥ 1 (CI-based) | predictions.py |
| P3 | H4 segmentation: χ² tag × content_type, confirmed only if Cramér's V > 0.2 | demand.py |
| P4 | H4 trend: binomial-GLM slope > 0 for disclosure share on year + monotone fitted shares | demand.py |

`report.py` **refuses to serialize an unbadged exploratory p-value or a p-only
test** (effect size + CI mandatory) — enforcement is a build error, not a
convention. Everything outside P1–P4 is EXPLORATORY / hypothesis-generating.
`report.family_summary()` applies Holm across the global P1–P4 family and
writes `results/family_holm.json` (P2 enters CI-based, with its CI verdict).

## Stated-n rule (advisor ruling b)

Every result states its n before interpretation. Current corpus truth:

- **P1: n = 88** claims with a reliable `date_made` and a parseable stated
  deadline (of 164 ledger rows; **38 rows** kept-but-flagged from
  title-only-date videos are excluded from all time series — r3 audit
  discrepancy 1: this README previously said 76; the ledger and
  `predictions_results.json.excluded_from_time_series` both say 38, and the
  code path confirms 38 `year_reliable: false` rows).
- **P2: n = 25** restated contact-window bounds (deduplicated per
  video/bounds). n ≥ 10, so the CI-based design runs as registered — but each
  point is a *restatement*, not an independent window; the ledger is the
  finding, the statistic is the annotation.
- **P3: 75 videos** × 20-tag share vectors; **P4: 34 reliable-year videos
  (556 questions), 2024–2026.**

## P1 headline wording (advisor ruling §2, binding)

The ratchet signature is **rejected**: P1 one-sided JT permutation p = 0.948,
Somers' D = −0.309. The observed direction is flat-to-falling conditionality,
consistent with the **pre-registered null shape** (r2_design §1a: honest
forecasting predicts flat or *falling* conditionality near resolution). The
negative trend is weak, era-fragile, and driven by the 5–10y bin (n = 3).
State the two companion statistics correctly and separately:

- **E2 (UNCONTROLLED):** Spearman ρ = −0.214, exploratory p = 0.0456 — no era
  control.
- **E3 (ERA-CONTROLLED):** partial Spearman ρ = −0.203 controlling
  `date_made`, bootstrap 95% CI [−0.386, −0.0046] (upper bound grazes zero);
  naive asymptotic two-sided p on the rank residuals ≈ 0.059. The headline
  "exploratory p = .046" belongs to E2 alone; the round-3 summary conflated
  them.

A rejected H1 is a **null result for the ratchet hypothesis, not a confirmed
alternative** — no sentence of the form "the corpus demonstrates honest
forecasting" is licensed. F2's dashed reference line is the weighted mean of
the observed bins, a descriptive reference, **not** a null model.

## Data deviation (honest)

`analysis.json.questions` stores the 949 classified questions only as
aggregate per-tag counts plus 99 sampled examples; per-question tags keyed to
`video_id` are **not stored in the repo**. P3/P4 therefore run on per-video
20-tag topic-share vectors (`digests.topic_percentages`, present for all 75
videos), with per-video question counts as GLM weights. Cells are
pipeline-estimated share points, not raw question counts. The 99-sample
cross-check (E5) is reported EXPLORATORY — and round 3 silently dropped it:
the 99 samples cover only 2 of 4 content types (full sessions + interviews),
so the clip/highlight columns are all-zero, `chi2_contingency` raised
`ValueError` on a zero expected cell, and the code swallowed it (r3 audit
discrepancy 2). Now fixed: E5 restricts the table to the sampled types and
replaces the inapplicable asymptotic χ² with a Monte-Carlo permutation p
(type labels permuted across the 99 examples, both margins fixed, 10k, seed
42), with a bootstrap CI on Cramér's V. See `demand_results.json`.

## Lexicon count note

The frozen escape-hatch lexicon (r2_design.md §1a, verbatim) contains **50
phrases**, not 47 as shorthand elsewhere suggested. Verbatim fidelity to the
frozen list is what is enforced (`common.py` asserts 50).

## Round-4 audit-fix ledger (r3 advisor discrepancies)

1. **n accounting (fixed):** excluded title-only-date rows = **38**, not 76
   (see stated-n rule above).
2. **E5 99-sample cross-check (implemented):** was silently absent; now a
   Monte-Carlo permutation test on the sampled 2-type table, EXPLORATORY,
   serialized in `demand_results.json` (see data deviation above).
3. **Provenance (amended):** `predictions.py` now lists only the inputs it
   actually reads (`data/digests/*.json`, `data/videos.json`). Design §1a said
   the lexicon would also be counted on
   `analysis.json.predictions[].examples[].text`; audit shows all 58 examples
   are already represented verbatim in digest rows and in `ledger.csv`, so
   wiring the file in would add zero claims and no result changes. Recorded
   in `predictions_results.json.provenance_correction_r3`. `teachings.md` is
   read by `doctrine_graph.py`, never by `predictions.py`.
4. **Residual-direction note (fixed):** the disclosure skew is carried by
   free **interviews (+6.9)** and **clips/excerpts (+3.1)** standardized
   residuals; **official highlight clips are UNDER-represented (−3.0)**, as
   F4 shows. The earlier sentence claiming highlight clips skew to disclosure
   is retracted; see `demand_results.json.residual_direction_descriptive`.

Plus the E2/E3 conflation fix (see P1 headline wording above) and the
demotion of the P3 asymptotic p = 1e-175 to decorative-only status (it is
count-inference-meaningless under pseudo-replication; the operative evidence
is V > 0.2 narrowly cleared, the cluster-bootstrap CI [0.211, 0.300], and the
within-year-strata permutation p = 1e-4).

## Round-5 changes (advisor r4 mandatory surgery + approved novel module)

**E7 slip-velocity surgery (r4 advisor §2, applied).** The slip-velocity
headline now reads: median **1.0 yr/yr with IQR [0.5, 4.25]** — only 29% of
flips sit at exactly 1.0 (38% below, 33% above, tail to 24 yr/yr). The
previous bootstrap CI [1.0, 1.0] is **REMOVED as a degenerate bootstrap
artifact**: the 73 velocities are all-pairs ratios computed from only 35
window rows (each row enters ~4 pairs), so the resample treated dependent
ratios as independent and the discrete median collapsed the interval to zero
width. The removal is recorded in
`doctrine_dynamics_results.json.slip_velocity_uncertainty.removed_degenerate_ci`,
not hidden. The all-pairs structure ("73 pairwise flips from 35 window rows,
non-independent") is disclosed wherever n = 73 appears. The **clean headline**
is the consecutive-restatement subset: pairs with elapsed = 1 y (n = 38)
recede at median **1.0 yr/yr**; pairs with elapsed ≥ 3 y (n = 32) recede at
median 0.4 yr/yr. F7a's caption carries the IQR.

**Retroactive rubric calibration (rubric_calibration.py — r4-advisor-approved
round-5 novel module, EXPLORATORY).** The frozen 2027 rubric (below) is
applied unchanged to the historical dated claims in the ledger under a
pre-specified protocol (eligibility screen S1–S5; blind-ish scoring against a
frozen public-record fact table — claim text sets the deadline, never the
outcome). Result: of 164 ledger rows, 2 resolved open-contact claims were
scorable (2020 window start; 2025 "early markers") and both score **failure**
— historical pass rate **0/2** (Clopper–Pearson 95% [0, 0.84], descriptive
annotation only; rows are doctrinally correlated). 55 open-window claims
(including all 2026/27 claims) are disclosed as not yet scorable; the 2016
cluster (13 rows) passes through the screen and is excluded as event
logistics / not-open-contact. The calibration establishes historical
**specificity** (no false positives on the past — every near-miss, from the
2017 AATIP disclosure to the 2024 AARO report, fails the tightened partial
criteria for stated reasons); sensitivity is unknowable from history because
no true positive exists to detect. See `results/rubric_results.json` and F8.

> **HARD NO-TUNING CLAUSE (binding, r4 advisor):** the frozen 2027 rubric may
> not be edited after the calibration is scored, whatever it shows. A rubric
> that misclassifies the past is a finding about the rubric, published as
> such — never a license to tune the rubric into agreement with history,
> because a rubric fitted to the past is worthless for 2027. This clause is
> also embedded verbatim in `rubric_calibration.py` and
> `results/rubric_results.json`.

## Limitations

- **Era control:** every reliable-date prediction in the corpus is post-2015,
  so the within-era JT sensitivity is vacuous; the operative era control is
  the partial Spearman of cᵢ vs Δ controlling `date_made` (E3).
- **Acquisition is blocked in this environment** (network egress unreachable;
  see `results/acquisition_results.json`). No transcripts were fabricated;
  stylometry (Q3) remains blocked pending real transcripts + the WER audit
  (gates 15% overall / 10% function-word WER, with a mandatory Whisper
  hallucination screen; on 1984–96 cassette audio these gates are optimistic
  and the pass-only-spans fallback induces era/audio-quality selection bias —
  the era-extension arm may degrade to descriptive).
- **Doctrine graph measures genre discipline, not truth.** Consistency is
  descriptive corpus science; no output speaks to origin.
- Window-drift points are restatements of canonical windows quoted across
  videos; they are not independent doctrinal events.
- The 5–10y Δ bin has n=3; its pooled C is descriptive only.

## 2027 prospective rubric (frozen, tightened per advisor ruling d)

Scored blind to timing against the public record by a coder blind to the
panel's drift results; only events after the pre-registration count;
retrospective re-interpretation never scores.

- **Success (full):** a national government or the UN formally confirms
  non-human intelligence and initiates a public diplomatic/communication
  exchange, OR a non-human craft/entity is publicly presented and independently
  verified by ≥2 major scientific institutions, before 2030-01-01.
- **Partial (tightened):** an official government statement using **explicit
  non-human-origin language** (not "unknown") about materials or craft,
  verified by a **national laboratory or peer-reviewed analysis**; or a
  mass-witnessed (≥1,000 independent witnesses), multi-instrument
  (≥2 independent instrument classes, e.g. radar + optical — not two cameras)
  event officially unresolved and endorsed as anomalous by ≥2 national
  space/defense agencies.
- **Failure:** neither criterion met by 2030-01-01.

Window re-issues are logged as ratchet events (the ledger), never as edits to
this rubric.
