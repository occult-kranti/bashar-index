# r3-P26 / r4-P06: prespecification (written before any outcome of this entry is computed)

Third-round programme, step 1, class a.1. Folder `r3-P26`; it carries r4-P06 (MTMM over input-disjoint pairs; novelty
log N05). Written by a step-1 agent (a model agent working for the project lead; not a person). Exploratory; not a test
of H1-H10. Seen creators only. No model call, no network call.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What is fixed here, and what the programme and deposit 2 already fix

- Programme (r3-P26, r4-P06): MTMM's and RX-CB's voice cells are partly agreement by construction (D3); convergence is
  counted only over pairs that share no input, with a "shares the brand" input class; "no input-disjoint pair" and "not
  computable" are permitted answers. Plot: the dependence map as a grid; the MTMM heat map hatched by shared inputs;
  median convergence by input class with creator-bootstrap intervals. The acoustic column is a.2 (not computed here).
- Deposit 2 (margins register): primary "median convergence by input class, counted only over input-disjoint pairs, with
  creator-bootstrap intervals"; no margin stated, so the lead's default for a correlation or agreement coefficient holds:
  **0.10**. Readings A, B, undetermined as deposited; account cells: every account silent on r3-P26 and r4-P06.

## The dependence map (fixed in `code/p26common.py` before this file was hashed)

Each method of MTMM (12 measures), TL-7.8 (8 readings), RX-CB (boundaries and cue hits) and VER-DEP (four voice readers)
is placed on the inputs it reads, coded from the method's definition only (CROSS `mtmm.py`; the TL package's README and
rows; RX `patterns_v1.py`; the title instrument `titles.py` and its word rule; PT part b `pt_b.py`; the frozen voice
codebook's cue list). Input tokens: transcript words; punctuation and case; recognizer timing and units; voiced frames
(a.2); title text; page description; position; the brand (the named source: self-naming formulas, source and family
names); hand-written cue lists (by identity); frozen codebooks (by identity); models (small, middle, large) and vendor
(a shared vendor is a shared input: VER-DEP finds same-vendor errors correlated); upstream model outputs (the small
finder's ask candidates; the forecast finder's kept statements). Choices made here (stated): the voice models read the
brand (the frozen codebook names self-naming as a claimed-voice cue); RX's J2a and J2b read the brand and letter case;
the title presentation code and every source-family method read the brand; the asks methods do not; PT part b's mask
removes the creator's own names, so the page asks method reads no brand.

**Pair classes** (the first that applies, from the set of shared inputs):
C1 the same text read by the same instrument (a shared surface and a shared codebook, list or upstream units);
C2 shares a text surface or what is derived from it; C3 different surfaces, shares a model, vendor, codebook or list;
C4 different surfaces, shares only the brand; **C5 input-disjoint (shares no input)**.

## Primary and reading rule

- **Primary (per construct):** the median Spearman rho over the construct's convergent pairs of class C5, for each MTMM
  construct (voice, source family, asks) and each TL-7.8 construct (time window, hedging, condition). Where a construct
  has no C5 pair, its primary reads **"no input-disjoint pair"** and nothing is computed. The subject construct reads
  "not computable" (not run in MTMM); the acoustic column "not computable (a.2)".
- **Interval:** 90% creator bootstrap, percentile, 2,000 draws, resampling the seen creators with replacement and
  recomputing every pair's rho (pairwise complete, at least 5 creators) and the class medians within each draw, exactly
  as CROSS `mtmm.py` draws them (its seeded generator `rng_for("mtmm", "boot")` and creator order), so that a single
  pair's interval reproduces the published cell interval. r3-P30's battery has no design class for a correlation across
  creators of two creator-level shares; its nearest class (E, a within-creator rank correlation, one value per creator)
  does not apply. The programme names a creator bootstrap, so that is used; the README says the interval is not one r3-P30
  calibrated, and the lead is asked whether such a row may read A.
- **Reading** (margin 0.10, named direction positive): **A** "convergent with a method of another family, beyond the
  margin" (the ceiling wording; programme 4.2) if the lower bound lies above +0.10; **B** "no convergence beyond the
  margin across input-disjoint methods" if the interval lies inside -0.10 to +0.10; "beyond the margin, opposite to the
  named direction" if the upper bound lies below -0.10 (the lead's step-1 decision 2); **undetermined** otherwise.
  A single C5 pair is read on its own rho. No family-wise adjustment.
- **TL-7.8:** its per-creator values are not rebuilt. By the map no TL-7.8 pair is C5, so its primaries read "no
  input-disjoint pair" whatever the values; its published cells are tabulated by class (points and the published
  intervals only; class medians of published cells as points, no interval).

## Rows beside the primary (described, not read)

1. Rebuild check: the 12 MTMM measures are rebuilt with CROSS `mtmm.build()` (seen-only path, unchanged code, its hash
   recorded) and every published cell rho must be reproduced to 4 decimals; if not, the entry stops and reports.
2. Median convergent rho by class C1 to C5, per MTMM construct and pooled over the three constructs (median over all
   convergent pairs of the class), with the same bootstrap.
3. The published cross-input median (MTMM's "different inputs" pairs) printed beside, for comparison.
4. Campbell-Fiske comparisons for the C5 convergent pairs: the share of comparisons in which the pair's rho exceeds a
   heterotrait rho sharing one of its measures (MTMM's rule), with the same bootstrap; and the same share restricted to
   heterotrait pairs that are themselves C5.
5. RX-CB and VER-DEP: their pairs' classes on the map (C1 or C2; no correlation recomputed); their published figures
   are cited in words.

## Privacy

Creator counts as MTMM printed them (71; "all but fewer than 5 of 71" for any pair with the page asks measure). No
per-creator value, no quantile over creators. Medians are over method pairs, never over creators.

## Known leak

While reading the inputs, the writer read MTMM's public matrix (every cell rho), TL-7.8's public rows and the headlines
of RX-CB and VER-DEP, before writing the map. The map is coded from method definitions; which pairs fall in C5 follows
from it, not from the values.

## Plots

1. `fig-r3-P26-dependence-map`: methods (rows) by inputs (columns), filled where read.
2. `fig-r3-P26-mtmm-hatched`: the 12 x 12 MTMM matrix (lower triangle), coloured by rho, hatched by pair class.
3. `fig-r3-P26-convergence-by-class`: per construct and pooled, the median convergent rho by class with 90% creator
   bootstrap intervals, the 0.10 margin shaded; classes with no pair labelled "no pair".

Every caption states 90% creator-bootstrap intervals, "model-coded, not checked by a person", "agreement, never
accuracy" and "exploratory; not a test of H1-H10".
