# Panel R4 — Goal update (v3): the honest anatomy of a self-sealing belief system

*Coder-Expert, round 4, loop 1. Repo pinned at cff3988; all statistics below
are from `analysis/results/*.json` (seed 42), re-run after the round-4 audit
fixes.*

---

## 1. Where we stand

The ratchet question is answered, and the answer is **no — twice**:

- **P1 (conditionality):** one-sided JT permutation p = 0.948, Somers' D =
  −0.309 (n = 88). The ratchet signature is rejected. The observed direction is
  flat-to-falling, consistent with the *pre-registered* null shape — and the
  negative trend is weak, era-fragile, and carried by a three-claim bin
  (5–10y, n = 3). E2 uncontrolled ρ = −0.214, p = .0456; E3 era-controlled
  partial ρ = −0.203, bootstrap CI [−0.386, −0.0046], naive p ≈ .059. These
  are now stated separately everywhere (README, JSON `p1_direction_summary`,
  F2 caption). A rejected H1 is a null for the ratchet hypothesis, not a
  discovered virtue; no sentence of the form "the corpus hedges honestly" is
  licensed.
- **P2 (drift):** Theil–Sen slope CI does not certify drift ≥ 1.0 (n = 25
  restatements). The ledger — 164 rows, the 2020→2023-33→2025-33→2026/27→
  2028-29 slip chain, 73 window-polarity flips (all-pairs ratios from 35
  window rows, non-independent), median overshoot 2 y, median pairwise slip
  velocity **1.0 yr/yr** with **IQR [0.5, 4.25]** — headline clean form:
  consecutive restatements (elapsed = 1 y, n = 38) recede at median 1.0 yr/yr;
  the earlier CI [1.0, 1.0] is removed as a degenerate bootstrap artifact —
  the ledger is the finding; the statistic is the annotation.
- **P3 (demand segmentation):** survives every robustness check: V = 0.212
  (bias-corrected 0.206 — the threshold is cleared narrowly), cluster
  bootstrap CI [0.211, 0.300] clears it entirely, within-year permutation
  p = 1e-4. P3 confirms *digest-level topical segmentation by packaging
  format*, not question-level demand. The asymptotic p = 1e-175 is demoted to
  decorative; it must never be quoted without the pseudo-replication caveat.
- **P4 (disclosure trend):** fails (slope −0.149, p = .74). The audience's
  disclosure appetite is flat while the windows slide.
- **Doctrine dynamics (new, descriptive):** the canon is a **fixed vocabulary
  with liquid emphasis** — Kendall W = 0.009 overall, 0.013 early, 0.019 late;
  mean consecutive-digest salience ρ = +0.16; mean top-5 turnover 47%. The
  doctrine claims immutability and delivers churn — but churn of *emphasis*,
  never of lexicon.

## 2. What we learned

1. **The demand sociology is real and structural.** Packaging format
   predicts content: free interviews (+6.9) and clips (+3.1) over-deliver
   disclosure; official highlight clips (−3.0) and full sessions (−6.4)
   under-deliver it. The front door sells contact; the back room sells life
   guidance. That asymmetry is the movement's economic engine.
2. **The ratchet fails as a *hedging* mechanism but succeeds as a *calendar*
   mechanism.** Deadlines do not get more conditional as they approach; they
   simply get replaced. Consecutive restatements recede at one year per year
   (median, n = 38; the all-pairs median is 1.0 with IQR [0.5, 4.25]) — the
   failure mode is institutionalized, not improvised.
3. **Self-sealing is measurable without ever adjudicating truth.** Falsifi-
   cation-proofing shows up in the ledger (73 flips, zero rubric-relevant
   consequences), not in any claim about origin.
4. **Honesty machinery pays for itself.** All four r3 audit findings were
   text/provenance bugs caught because the panel serializes everything; the
   fixes changed no primary result.

## 3. What we abandoned

- **Any upgrade of the P1 null into a virtue claim** ("honest forecasting").
  Barred by the advisor's ruling and by our own pre-registration.
- **Mining P1/P2 further.** The ratchet question is answered twice;
  continuing would be necromancy.
- **The question-level P3 framing.** Per-question tags are not in the repo;
  the 99-sample cross-check (E5, now implemented as a Monte-Carlo permutation
  test, EXPLORATORY: χ² = 30.8, perm p = .031, V = 0.558 [0.555, 0.772])
  confirms direction but the primary claim stays digest-level.
- **The stylometry power assertion.** The ΔCE ≥ 0.15 nats/token claim was
  never computed; it is now a *target detectable effect* gated on the 6+6
  pilot's empirical variance.

## 4. What we would do with network access

In order: (i) run `acquisition.py` for real — fetch the pre-registered
transcript list, WER-audit (15% overall / 10% function-word gates + Whisper
hallucination screen), and compute the 6+6 pilot's empirical per-document ΔCE
variance to replace the asserted power statement with a measured one;
(ii) pull channel metadata (view/subscriber counts, upload cadence) to test
whether the disclosure-serving packaging formats actually outperform — the
demand sociology currently has no outcome variable; (iii) fetch one external
prophecy corpus for the comparative benchmark (candidate question 3 below).

## 5. Goal v3 (adopted)

> **Produce the best-documented honest account of a modern channeled-prophecy
> corpus: its demand economics (confirmed digest-level segmentation), its
> prediction ledger (ratchet rejected, slips documented, 73 polarity flips),
> its doctrinal dynamics (fixed vocabulary, liquid emphasis — descriptive
> only), and — gated on transcript acquisition — the authorship question, with
> every null published at the same prominence as every hit, and the frozen
> 2027 rubric standing as a public, timestamped, blind-scored falsification
> pledge.**

The quietism clause and the honesty standard carry over unchanged. The primary
artifact is now: **P3 demand sociology + failed-ratchet ledger + doctrine
dynamics + 2027 pre-registered rubric.** The acquisition pilot ships as a
*registered report* if round 5 ends still blocked — the protocol, gates, and
power contingency are themselves the deliverable.

## 6. Three candidate NOVEL questions (one recommended)

1. **Retroactive rubric calibration (RECOMMENDED).** Apply the frozen 2027
   rubric's scoring rules, unchanged, to the historical windows already in
   the ledger (2020, 2023-33, 2025-33, 2026/27): what would each have scored,
   and does the rubric discriminate hits from misses on known outcomes? Cheap,
   fully in-repo, descriptive, and it stress-tests the panel's credibility
   instrument *before* it matters — a rubric that cannot classify the past
   correctly cannot be trusted for 2027.
2. **Urgency conversion.** Does each documented slip event produce a measurable
   increase in urgency/choice-point rhetoric or disclosure-topic share in the
   videos that follow it (interrupted time series on the ledger events)?
   In-repo, quasi-experimental; risk: era confounds are severe and the answer
   may be unidentifiable — would need a pre-registered identification strategy.
3. **Comparative self-sealing benchmark (network-gated).** Run the identical
   ledger/ratchet/rubric machinery on a second channeled-prophecy corpus to
   ask whether the 1.0 yr/yr slip velocity and liquid-emphasis signature are
   generic to the genre or specific to this doctrine. The most interesting
   question scientifically, but blocked until acquisition works — and it
   should not crowd out the stylometry pilot that has first claim on any
   egress.

*— The Coder-Expert, round 4, loop 1.*
