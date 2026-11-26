# r3-P03 prespecification (written before any quantity of this entry was computed)

Written 2026-11-26T02:41:23Z (UTC, from `date -u`) by a step-1 agent (a model agent working for the lead; not a person),
before any locator, AUC, benchmark or register-matched contrast of this entry was computed. Deposit 2 was merged before;
nothing here is tuned on outcomes. Exploratory; not a test of H1-H10. Seen creators only.

What this agent had seen before writing it: the exploratory round's public aggregates (KA, MR-18c, RX-CB, MTMM, E2, E5);
r3-P01's results on recognizer instability (including the change of the contraction-share drop when unstable tokens are
dropped, never the drop itself). It had not seen the seen-creator value of H4's drop.

## The contrast

H4's contraction contrast: within a recording, contraction share (contracted / (contracted + full) over H4's closed list)
on each side, reported as the standardised drop (own share minus claimed share) divided by H4's frozen
yardstick (0.1474), creator means of recording values; claimed side V2 (embodied, H4's registered side), rule B, broad
own voice, claimants sole speaker and host or owner (`voice_sets.primary_definition("H4")`); small model of record on
every seen recording (primary), the middle model on the seen recordings it labelled in full (row).

## Rows ("one contrast, several locators")

- **R0** the frozen estimator: `h4_contraction.creator_drops` with the feature files (H4's form minimum per side).
- **R0-middle** the same under the middle model.
- **R1** contractible classes A, B and C apart (r3-P01's class rule on H4's closed list; counts from the transcript
  tokens), label of record.
- **R2** cue-free interiors: units at least 3 units from every voice boundary of the label (any change of side), not
  overlapping a seam zone (word midpoint within 1 s of an internal 30-s seam), and with no RX framing-cue hit (J1, J2a,
  J2b, J3) and no self-naming flag (the voice file's self-naming cue units or the feature file's flag) in the unit or its
  two neighbours. The share of claimed-voice contractible items kept and the eligible creators print first; under 5
  creators: not computed.
- **R3** register-matched: within each recording, the claimed and own units are cut into five strata by quintile of the
  F1 register score (below); the drop is computed inside each stratum holding items on both sides, averaged over strata
  with weights min(items claimed, items own); creator mean of recording values; standardised.
- **R5** alternative locators, each with its attenuation benchmark:
  * K-F1, a register-only locator: in each recording, the units of the claimed and own sides ranked by the leave-creator-
    out F1 score; the top units, as many as the label puts on the claimed side, are "claimed", the rest "own".
  * K-cue, early cue to leave-taking cue: units from the first opening cue hit (J1, J2a, J2b) to the next leave-taking
    hit (J3), or to the end, are "claimed"; the rest of the units on either side of the label "own". Sensitivity only.
  * K-middle: the middle model's sides against the small model's, on recordings both labelled in full.
  For each: PPV and NPV of K against the label, weighted by contractible items, over the units both sides hold; the
  benchmark is (PPV + NPV - 1) x (the label's drop on the same units and recordings); D = K's drop - benchmark, per creator
  (each creator's own table), creator mean and interval.
- **Reference bands**: the registered tempo control (`h4_contraction.tempo_control`: fast minus slow own-voice windows,
  standardised) and a frame band (own-voice units of the map's opening and closing parts against own-voice body units:
  body share minus frame share, standardised).

## The AUC ladder (label of record)

Unit features from the text the voice labeller sees (T1, contraction-neutral; computed with prep.variant):
- **F0** formatting baseline: words in the unit, punctuation marks per word, sentence marks (MR-18c's definitions).
- **F1** register without contractions: F0 plus repeated-word share, visible fillers per word, mean letters per word,
  share of words of 7 or more letters, function-word share (H9's list), first-person singular, first-person plural and
  second-person shares, archaic-form share (r3-P01's list), hedge share (features.py's list), type-token ratio, question
  marks per unit.
- **F1c** F1 plus the unit's contraction share on the text as transcribed (T0) and a flag for units holding items: printed
  to show what contractions would add; the labeller does not see them.
- **F2** F1 plus framing-cue words: RX cue hits in the unit (J1, J2a, J2b, J3) and the self-naming flag.
Model: standardised features, logistic regression (scikit-learn, L2, C = 1), leave-one-creator-out (each creator scored
by a model fitted on all other creators' units). Units: claimed and own units of recordings holding both, label of record.
Per creator with 10 or more units on each side: the AUC of the score for claimed against own. Estimators: the median of
creator AUCs and the pooled within-creator AUC (concordant pairs within creators over all within-creator pairs); the
creator-equal mean printed beside. Intervals: 90% creator bootstrap (2,000 draws, seed 2026112603), percentile; the
creator AUCs are shown as quantile bars (10th to 90th percentile over creators), no point per creator.

## Margins (deposit 2's defaults; the entry states none)

- Standardised drop and D: 0.20 between-creator SD (in H4-yardstick units).
- AUC: 0.10 away from 0.50.

## Readings, fixed now

- Per contrast row: A ("beyond the margin") when the 90% t interval on creator means lies wholly above +0.20 (H4's named
  direction: fewer contractions in the claimed voice); B when it lies wholly inside -0.20 to +0.20; otherwise undetermined;
  under 5 creators not computed.
- Per D row: inside -0.20 to +0.20 "consistent with a contrast carried by the units the two locators share"; wholly
  below -0.20 "depends on what only the label selects"; wholly above +0.20 "the locator carries more of the contrast than
  its agreement with the label gives"; otherwise undetermined.
- Per AUC estimator: "beyond" when its interval lies wholly above 0.60 (or below 0.40), "inside" when wholly inside 0.40 to
  0.60, otherwise undetermined. The two estimators disagree when their readings differ: the ladder rung then reads
  "undetermined".
- **The entry's reading** (only these words; never "tautology"):
  1. If R0 does not read A: "undetermined (the contraction contrast on the label of record is not beyond its margin, so
     whether it can be told apart from register is not readable)".
  2. Else "cannot be told apart from register in these data" if R3 reads B, or if the F1 rung reads "beyond" on both
     estimators while R3 does not read A, or if K-F1's D lies wholly above +0.20.
  3. Else "told apart from register in these data (on these checks only)" if R3 reads A, the F1 rung's estimators agree,
     and K-F1's D does not lie wholly above +0.20.
  4. Otherwise "undetermined".
- Interval for contrast and D rows: the 90% t interval on creator means (deposit 2's default; r3-P30's
  interval-choice.csv is used instead if it exists when the analysis runs, and the README says which).

## Not run

The register-normalised relabel (dropped by the programme); the punctuation-free relabel and the masked-ask relabel (class
c: stripped labels are not stored at unit level, to be confirmed); the label's run-to-run ceiling at creator level (no
repeated small-model labels of these units are used here).

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
