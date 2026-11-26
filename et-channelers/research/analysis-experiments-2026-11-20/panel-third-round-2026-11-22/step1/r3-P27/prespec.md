# r3-P27 prespecification: tuning leak, development against check creators

Written 2026-11-26 at about 06:39Z (UTC, from `date -u`; the exact time and this file's SHA-256 are in
`prespec-record.md`) by a step-1 agent (a model agent working for the lead; not a person), before any value of this
entry was computed. Looked at first, outcome-free: the paper's definition of the groups, the split policy, the keys and
counts of `step0/split.private.json` (its sources and checks), and the creator counts (not values) of r3-P04's three
statistics. Deposit 2 was merged before this entry started.

Exploratory; not a test of H1-H10. Seen creators only. Every label is model-coded and not checked by a person;
agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Which groups (established before any value)

- The paper (`appendix-protocol.tex`, `data.tex`): "Development and check creators are subsets [of the seen creators]:
  prompts were developed on the first, and the gate samples (G) and verification samples were drawn from the second."
  The split policy: "r3-P27 uses the paper's existing development and check partition as it is"; the development set is
  the registry's development set (the pilot's 48 creators). `step0/split.private.json` records the partition's source
  (`llm/pilot/creator-split.private.json`, SHA-256 91737c7c...ac06) and its checks: development 48, non-development 23,
  disjoint, together equal to the 71 seen creators.
- **Both groups are seen creators**, so the entry runs. Development = the tuning pool T (48); check = the 23 seen
  non-development creators (`draw` of the split file, both halves). No hold-out or other-group file is needed or opened.

## Rows (the paired forest: each figure on development and on check creators, with the difference)

Agreement figure (computable on both groups from stored seen labels):
- **G1 voice agreement, small against middle model**: on the seen recordings the middle model labelled in full, the
  share of sentence units on which the two models agree on claimed voice (V2 or V3, rule B label) against not claimed;
  creator value = mean over its recordings of the recording's agreement share. Margin: 5 points (share). Named direction
  of the difference: development minus check positive (prompt tuning would raise agreement on the development
  creators). Described beside it: Cohen's kappa pooled over units within each group (creator-cluster bootstrap, 90%).
- Agreement figures stored for one group only are listed, not computed: the gate sample G, the cross-vendor read
  (VER-3R) and the second readings (DBL) were drawn from check creators only; the pilot's set W was development
  recordings under pre-freeze prompts.

Contrasts (the seen claimed-minus-own statistics, small model of record, frozen per-recording functions through
`mrcommon.py`, unmatched):
- **C1 H1** log rate ratio (creator mean of recording values; margin log 0.223; r3-P30 class A_log_ratio).
- **C2 H4** standardised contraction drop (creator mean; margin 0.20 SD; class C_standardised).
- **C3 H6** OE of pay-or-enrol asks (per creator with T >= 1, the frozen `oe_values`; margin 0.05; class
  B_share_difference, as r3-P04 read it). Named direction: none (two-sided) for C1 to C3.

## Estimates and intervals

- **Each group's estimate**: 90% interval by r3-P30's `interval-choice.csv` for the class at the group's count (row of the
  largest simulated count at or below it); capped where no method holds.
- **The difference (development minus check)**: Welch's t interval on creator means, 90% (two-group differences are a
  design class r3-P30 did not simulate; deposit 2's fallback is the t interval, stated), with a stratified creator
  bootstrap percentile interval (2,000 draws, creators resampled within each group) beside. For C1, whose r3-P30 choice is
  a random-effects method at both counts, the difference is also given as the difference of the two groups' chosen
  estimates with the root sum of their squared half-widths (a row).
- **Readings of the difference** (deposit 2): **A** "a development-check difference beyond the margin" (Welch interval
  wholly beyond the margin; for G1 in the named direction, for C1 to C3 on either side), **B** "no development-check
  difference beyond the margin" (wholly inside), **undetermined** otherwise, and also when the bootstrap interval gives
  a different category, or when r3-P30 finds no method that holds for the class at either group's count. Not computed
  under 5 creators in either group.
- **Shrinkage factor** (described, never read): for C1 to C3, the check estimate divided by the development estimate
  (creator means), with the stratified bootstrap percentile interval; it says how far a prior built on the development
  creators would shrink on the check creators. A difference is not proof of tuning.

## Privacy

- No per-creator value; groups printed only with 5 or more creators; counts by the nested-count rule (`pubrules.py`,
  copied from r3-P01, with the tuning pool and the non-development creators registered).
- **Plain means and earlier outputs.** r3-P04 printed creator means of the same three statistics over its own bases. For
  C2 and C3 this entry's union base must equal r3-P04's count, and for C1 r3-P04 left out one creator with an observed
  value whom this entry cannot identify without re-running r3-P04's references: so C1 prints no plain creator mean (its
  group estimates are r3-P30's random-effects estimates, and the Welch row prints only the difference and its interval).
  If a union base differs from r3-P04's count for C2 or C3, the same rule applies to it.
- No quantile of creator values. Every public file carries the agnosticism sentence and "exploratory; not a test of
  H1-H10".
