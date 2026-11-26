# r3-P52 / r4-P12: plural self-reference at recording level: prespecification

Written 2026-11-26 from 12:44:25Z (UTC, from `date -u`) by the step-2 description agent, a model agent working for the
project lead (not a person), before any statistic of this entry was computed. Shared rules: section 0 of
`../r3-P48/prespec.md`. What was known: r3-P42's public L09 check (span level, on the 11 voice-eligible creators: the
first-person-plural share 0.21 higher in the claimed voice, outside its bands, term-dependent on "we").

Exploratory; description, not for registration. The first person in claimed-voice recordings is "presented as the
source's". Cue counts; voice and map labels model-coded, not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Units (ling's recording-level primary: no span label selects the units)

- **Claimed-voice recordings**: recordings inside the primary voice definition (claimant sole speaker or host) whose
  claimed-voice (V2 + V3) labelled units hold 300 or more words (H6's side floor).
- **Own-voice talks**: recordings with no unit in a claimed voice under the record model's rule-B labels and with own-voice
  (V1) units (step 1's `own_only`, the transplant hosts' rule), whose format is not "conversation" or "multi_presenter"
  (H1's excluded formats).
- Every token of a recording counts (both voices and unlabelled units), outside units holding a self-naming or address
  frame (L09's frames on the cased copy, r3-P42's extract flags). FP-PL and FP-SG as L09 (a2b), matched again on the
  extract (`lists=("L09",)`), totals checked against r3-P42's per-recording counts.
- **Eligible creators**: at least one recording of each class, with 1,000 or more tokens outside frames and one or more
  first-person hit in each class (pooled within class). **The eligible count is printed first** (shared 0.4).

## 2. Statistics

- **Shift** per creator: FP-PL / (FP-PL + FP-SG) pooled over the claimed-voice recordings minus the same over the own-voice
  talks. **Primary**: the creator mean with r3-P30's design class B interval at the eligible count; margin 0.05; no
  direction deposited (words "beyond the margin (plural higher in claimed-voice recordings)", "... (lower ...)", "within
  the margin (B)", "undetermined").
- **Bands beside it** (fixed methods): (a) function-word placebos: two function-word unigrams (H9's closed list) matched to
  FP-PL and FP-SG on frequency band and dispersion (r3-P42's L09 placebo draws), the same shift computed, central 90%;
  (b) own-noise band: each eligible creator's own-voice talks split at random into two halves (creators with 2 or more
  talks), the creator mean of the split-half share difference, 200 splits (stream ("r3-P52", "own-noise"), k = 1),
  central 90%.
- **C2**: leave one form out (forms of FP-PL and FP-SG used by 1 or more creators): a form whose removal changes the
  margin words or a band reading makes the row "undetermined (term-dependent)". **C4** as r3-P42's L09.
- **Sensitivity**: claimed-voice recordings defined as any recording inside the definition with 1 or more claimed-voice
  word.

## 3. Heterogeneity reading ("concentrated", "spread", "undetermined"; hashed thresholds)

- Noise-corrected between-creator SD of the shift: tau^2 = var(d_i) - mean_i(s_i^2), floored at 0, where s_i^2 is the
  binomial variance of creator i's shift (p_c(1 - p_c)/m_c + p_o(1 - p_o)/m_o, m = first-person hits per class) times a
  design effect: the mean, over eligible creators with 2 or more own-voice talks, of the observed mean squared split-half
  difference divided by its binomial expectation (200 splits, the stream of 2(b)), floored at 1.
- 90% interval of tau: creator bootstrap (B = 1,000, stream ("r3-P52", "tau"), k = 1), percentile.
- **Thresholds (hashed now)**: "concentrated" if the lower 90% bound of tau is 0.05 or more (creators differ by more than
  the share margin after noise); "spread" if the upper bound is below 0.05; else "undetermined". "A taught or copied
  format" is printed as a third reading that this statistic cannot tell apart from the other two. The members' readings
  (a shared genre style; a mark of particular lineages) are kept out of result sentences.
- Needs 5 or more eligible creators; else "not computed (too few terms or creators)".

## 4. Plot

A histogram over creators of the within-creator shift (bins by rule, 5 or more creators each), with the own-noise band, the
function-word placebo band and the hashed thresholds (+/- 0.05) marked; no per-creator slope chart.
