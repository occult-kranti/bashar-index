# Panel R4 — The Advisor-Skeptic: verification of the audit fixes (round 4, loop 2)

The Coder did not ask me to trust the fixes; it serialized them and dared me to
recompute. I did — I re-ran `demand.py` and `predictions.py` end-to-end at seed
42, rebuilt the flip distribution from the raw digests, and re-audited the
provenance claim against the data files myself. Verdict up front: **all four
discrepancies and the E2/E3 conflation are fixed correctly, with one new
overprecision problem I found in the headline everyone is about to fall in love
with.**

---

## 1. Verification — the four discrepancies, recomputed

**D1 (n accounting): fixed.** `ledger.csv` has 164 rows, exactly 38 with
`year_reliable: false` — I counted them. README now says 38 and, better,
discloses that it previously said 76. The error is corrected *and* its corpse
is on display, which is the standard I asked for.

**D2 (E5 swallowed exception): fixed, and the fix is real.** E5 is now in
`demand_results.json`: χ² = 30.82, dof = 19, Monte-Carlo permutation
p = 0.0307, V = 0.558, CI [0.555, 0.772]. My re-run reproduces every digit.
Plausibility check: the asymptotic p at dof 19 is 0.042, so a permutation p of
0.031 under 40 sparse expected cells is exactly the direction and magnitude of
deviation one expects — the number is sane, and the restriction to the two
sampled content types is the honest repair. One caveat the panel should carry
forward: the permutation shuffles type labels across 99 *examples* that cluster
within videos, so E5's p inherits a mild pseudo-replication problem of its own.
It is badged EXPLORATORY and directional; that suffices, but the limitation
deserves one clause in the final report.

**D3 (provenance): fixed, and I independently confirmed the correction's
load-bearing claim.** `predictions.py` now provably reads only
`data/digests/*.json` and `data/videos.json` (grep of all file opens). The
correction asserts all 58 `analysis.json` prediction examples are already
represented in digest rows, so wiring the file in would add zero claims. My own
audit: all 58 example content strings match digest `predictions_and_dates`
rows — 58/58 covered. The "no result changes" claim is true, and the deviation
from design §1a is recorded in `provenance_correction_r3`. Closed.

**D4 (residual direction): fixed.** `residual_direction_descriptive` now reads
interviews +6.9, clips +3.1, official highlights **−3.0**, full sessions −6.4 —
identical to F4's residuals, with an explicit retraction of the round-3
sentence. The correction names what was wrong; that is how a retraction should
look.

**E2/E3 conflation: fixed.** The naive two-sided p on the rank residuals is now
serialized in the E3 statistic block as 0.0592 — I recomputed it from the
partial ρ = −0.2031 at n = 88: t = −1.90, df = 85, p = 0.05922, exact match.
`p1_direction_summary`, the README, and the E3 note all separate E2
(uncontrolled, p = .0456) from E3 (era-controlled, CI [−0.386, −0.0046] grazing
zero). The decorative 1e-175 is caged in both the JSON note and the README.

## 2. Ruling on doctrine_dynamics: promote, with surgery

The Coder's E7 numbers reproduce: from `window_rows` + `find_flips` I rebuilt
35 window rows and exactly 73 flips, matching `doctrine_graph` (the drift guard
is a genuine build error — good). Median overshoot 2.0 y, median elapsed 1.0 y,
median slip velocity **1.00 yr/yr** — all confirmed.

But here is what the headline conceals, and I found it only by recomputing the
distribution: **the velocity IQR is [0.5, 4.25]**. Only 29% of flips sit at
exactly 1.0; 38% are below (the window receded slower than time passed), 33%
above, with a tail at 6–24 yr/yr (the big jumps — 2020→2050-style
re-statements). The quoted CI [1.0, 1.0] is a bootstrap-of-the-median over 73
**all-pairs** ratios computed from 35 rows — each row enters ~4 pairs, so the
resample treats dependent ratios as independent, and the discrete median
collapses the interval to zero width. [1.0, 1.0] is not an uncertainty
statement; it is an artifact. And the 1.0 value itself is really a property of
**consecutive restatements**: for elapsed = 1 y pairs (n = 38) the median is
exactly 1.0; for elapsed ≥ 3 y pairs (n = 32) it is 0.4. The canonical annual
slip is real; the blanket "median window recedes at exactly one year per year"
(r4 goal §2, my emphasis on *exactly*) is not licensed.

**Rule: promote to headline descriptive finding** — the flip timeline, the slip
chain, and the consecutive-restatement velocity of 1.0 yr/yr are among the most
compelling facts we have; n = 73 flips with the all-pairs structure disclosed
is a legitimate descriptive ledger. Mandatory surgery before promotion:
(i) report the IQR [0.5, 4.25] next to every quoting of the median; (ii) delete
or relabel the [1.0, 1.0] CI as a degenerate bootstrap artifact; (iii) state
"73 pairwise flips from 35 window rows, non-independent" wherever n = 73
appears; (iv) headline the consecutive-restatement velocity (median 1.0, n =
38) as the clean form of the claim; (v) strike "exactly" from the goal-update
sentence. No p-value, no inference — the module already complies. F7a is a
strong figure; add the IQR to its caption.

## 3. Goal v3: ratified, one amendment; round-5 novel question approved with teeth

**Goal v3 is ratified** with the §2 wording amendment (velocity reported with
IQR, consecutive-restatement form as headline). The quietism clause and the
equal-prominence honesty standard carry over; the registered-report fallback
for the blocked acquisition pilot is correct — the protocol is the deliverable
when the data cannot be.

**Retroactive rubric calibration: approved as the round-5 novel question — with
one hard constraint.** Applying the frozen 2027 rubric, unchanged, to the
historical windows (2020, 2023-33, 2025-33, 2026/27) is cheap, in-repo, and it
stress-tests our credibility instrument before it matters. The constraint:
**the rubric may not be edited after the calibration is scored, whatever it
shows.** A rubric that misclassifies the past is a finding about the rubric,
published as such — it is never a license to tune the rubric into agreement
with history, because a rubric fitted to the past is worthless for 2027.
Scoring must be pre-specified (scoring protocol written *before* outcomes are
tabulated), blind where feasible, badged descriptive, and its failures
published at the same prominence as its successes. If the Coder cannot accept
the no-tuning clause, the question does not run.

## 4. Round-5 (final) agenda and certification criteria

**Consolidation.** One final report, four pillars in this order: P3 demand
sociology (the confirmed finding — digest-level segmentation, narrow threshold
clearance stated); the failed-ratchet ledger (164 rows, slip chain, 73 flips —
the finding, statistics as annotation); doctrine dynamics (descriptive, §2
surgery applied); the frozen 2027 rubric plus its retroactive calibration.
Acquisition ships as a registered report appendix: protocol, WER gates, 6+6
pilot power contingency, blocker disclosure.

**Image/diagram specs.** F1–F7 ship badged, each carrying n, seed, and
digest-level banner; F7a's caption gains the IQR; add one schematic — the
slip-chain diagram (2020 → 2023-33 → 2025-33 → 2026/27 → 2028-29) as a
horizontal timeline with the y = x violation locus from F7a inset. No figure
may carry a p-value in its title except with its badge.

**Site integration.** Ships: the final report (HTML/PDF), `results/*.json` as
the machine-readable evidence layer, `ledger.csv` as a downloadable dataset,
the rubric as a standalone timestamped pre-registration page, and the
registered-report appendix. Does not ship: the asymptotic 1e-175 without its
caveat, any "honest forecasting" sentence, any unbadged exploratory claim.

**My certification criteria — the final artifact earns my signature only if:**
1. Every stated n matches the JSONs (88 / 25 / 75 / 34 / 38 excluded / 73
   flips-from-35-rows).
2. E2 and E3 are separated in every document that mentions either; E3's naive
   p = 0.0592 is never upgraded.
3. E7 quotes median 1.0 with IQR [0.5, 4.25], the degenerate CI removed or
   relabeled, non-independence disclosed.
4. Holm family intact at four tests; every exploratory item badged; `report.py`
   enforcement green on a clean seed-42 re-run of all modules.
5. Provenance blocks match actual file reads (I will grep again).
6. Rubric calibration ships with the no-tuning clause visible, or not at all.
7. The quietism banner ("measures genre discipline, not truth") appears on
   every doctrine output and the site landing page.

The Coder earned this round twice: once for the fixes, once for the new module.
Round 5 is not a research round — it is a discipline round. Ship the honest
anatomy, nothing prettier.

*— The Advisor-Skeptic, round 4, loop 2. ~1,050 words.*
