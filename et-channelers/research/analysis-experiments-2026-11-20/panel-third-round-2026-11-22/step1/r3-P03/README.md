# r3-P03: label circularity -- register, cues and the contraction contrast (step 1, class a.1)

Written 2026-11-26T03:00:10Z (UTC, from `date -u`) by a step-1 agent (a model agent working for the
lead; not a person). Exploratory; not a test of H1-H10. Seen creators only. Voice labels are model-coded; not checked by a
person. No model call, no network call.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Prespecification

`prespec.md` was written at 2026-11-26T02:41:23Z and hashed at 02:41:57Z (SHA-256
`d14f89d7711be4863fb459dde68a11fe2a17d82a00749c09b15a75809ebf1365`), before any locator, AUC, benchmark or matched
contrast was computed; `analyse_p03.py` refuses to run if it changed. It fixes the rows, the features, the model, the
margins (deposit 2's defaults: 0.20 SD for the drop and D, 0.10 from 0.50 for AUC) and the reading rule.

## The entry's reading

**"Told apart from register in these data (on these checks only)."** Path through the prespecified rule: the
contraction drop on the label of record reads A (beyond the margin), the register-matched drop reads A, the F1 rung's two
AUC estimators agree (both beyond 0.60 before r3-P30's cap, both undetermined after it), and the register-only locator's
D is not printed (the row's count is banded); some rows' readings are not printed for privacy. Never "tautology". The register-normalised relabel was dropped by the programme and
not run.

This reading says the claimed-against-own contraction drop survives holding register fixed in these data. It does not
say the label is free of register: the register the labeller sees predicts the label well above chance (below).

## Primaries ("one contrast, several locators"; H4's drop in between-creator SD units, 90% intervals)

| Row | Creators | Drop | 90% interval | Method (r3-P30) | Reading |
|---|---|---|---|---|---|
| R0 label of record (frozen H4 estimator) | 34 | 1.79 | 1.41 to 2.16 | t on creator means | A |
| R0 middle model | all but fewer than 5 of the seen creators eligible for H4 (middle model) (20) | not printed: the row's count is banded | not printed: the row's count is banded | r3-P30's choice at the row's count | not printed: the row's count is banded |
| R1 class A pairs | 29 | 2.55 | 2.05 to 3.01 | bootstrap-t | A |
| R1 class B pairs | fewer than 5 | - | - | - | not computed |
| R1 class C pairs | 23 | 1.33 | 0.82 to 1.80 | bootstrap-t | A |
| R2 cue-free interiors (48% of claimed-voice contractible items kept) | 20 to 29 | not printed: the row's count is banded | not printed: the row's count is banded | r3-P30's choice at the row's count | not printed: the row's count is banded |
| R3 register-matched (F1 quintiles) | 44 | 1.61 | 1.17 to 2.05 | t on creator means | A |
| R5 register-only locator (K-F1) | all but fewer than 5 of 34 | not printed: the row's count is banded | not printed: the row's count is banded | r3-P30's choice at the row's count | not printed: the row's count is banded (contrast, benchmark and D) |
| R5 opening cue to leave-taking cue (K-cue) | 12 | 1.36 | 0.75 to 1.94 | two-stage | undetermined; D +0.04 (-0.34 to 0.38) |
| R5 middle model as locator (K-middle) | 10 to 19 | not printed: the row's count is banded | not printed: the row's count is banded | r3-P30's choice at the row's count | not printed: the row's count is banded (contrast, benchmark and D) |
| band: tempo control (fast minus slow own-voice windows) | 44 and fewer than 5 more | not printed: the row's count is banded | not printed: the row's count is banded | r3-P30's choice at the row's count | reference |
| band: frame (own-voice frame against body) | 18 | 0.27 | -0.01 to 0.54 | two-stage | reference |

**AUC ladder** (leave-one-creator-out logistic score from what the labeller sees, claimed against own units; creators
with 10 or more units on each side: all but fewer than 5 of 44). Median of creator AUCs and pooled within-creator AUC,
90% creator bootstrap. The median estimator and the quantiles over creators are not printed (the release's decision D67, applied by the lead's step-1 decision 18: no quantile of creator values over a banded creator count); the pooled AUC and every reading are printed.

| Rung | Median AUC | Pooled AUC | 10th to 90th percentile | Reading (before / after r3-P30's cap) |
|---|---|---|---|---|
| F0 formatting | not printed (D67) | 0.52 (0.46 to 0.57) | not printed (D67) | inside / undetermined |
| F1 register without contractions | not printed (D67) | 0.73 (0.69 to 0.78) | not printed (D67) | beyond / undetermined |
| F1 + the unit's contraction share | not printed (D67) | 0.77 (0.74 to 0.81) | not printed (D67) | beyond / undetermined |
| F2 = F1 + framing-cue words | not printed (D67) | 0.73 (0.69 to 0.78) | not printed (D67) | beyond / undetermined |

r3-P30 finds no interval method that holds for AUC below 71 creators, so every rung reads at most "undetermined"; the
estimators agree on every rung. Formatting alone (punctuation, sentence marks, unit length) does not predict the label
beyond the margin; register without contractions does, and the contraction share adds little.

r3-P02 (described, not read): the coupling of pauses with sentence marks is weaker in the claimed voice; F0 and F1 read
punctuation that pauses make. A row wholly beyond the margin opposite to the named direction would be described as
"beyond the margin, opposite to the named direction" (a label added after r3-P02's results); no row is.

Multiplicity: 56 primaries in the programme; if every true effect sat at half its margin, the readings of A expected by
chance are about 2.8 at the deposited 5%, up to about 6.1 for the share, standardised, AUC and rank-correlation classes
(r3-P30's readings table). A reading is never a finding.

## Files

| File | What |
|---|---|
| `prespec.md` | the prespecification (hashed before any computation) |
| `public/data-r3-P03-locators.csv` | every locator row, benchmark, D and band, with interval method and reading |
| `public/data-r3-P03-auc.csv` | the AUC ladder: the pooled estimator, creator-equal mean, readings of both estimators before and after the cap (the median estimator and the quantiles not printed, D67) |
| `public/data-r3-P03-reading.csv` | the entry's reading and its path through the rule |
| `public/fig-r3-P03-locators.png/.pdf` | "one contrast, several locators" beside the pooled AUC of each rung |
| `code/` | `extract_p03.py` (per-unit numbers of T1 and T0 text, 3 worker processes passed ledger rows), `analyse_p03.py`, `publish_p03.py`, `plot_p03.py`, `style.py` (copied verbatim); it imports `p01common.py` and `pubrules.py` from `../r3-P01/code/` |
| `private/` | per-unit numbers, per-creator values, logs (never published) |

SHA-256 of every file: status.json. Data CSVs carry a commented header; PNG 200 dpi without text chunks; PDF without
document information; identifier scan of every public file: none found.

## Departures and choices (stated)

1. **Interval methods**: drop, benchmark and D rows use r3-P30's choice for C_standardised at each row's count (the
   prespec allowed this if the file existed when the analysis ran; it did). AUC rows keep the prespecified creator
   bootstrap and take r3-P30's cap.
2. **R3** is computed on every recording holding claimed (V2) and own units, without H4's form minimum per side (the
   prespec named none), so it rests on more creators (44) than R0 (34).
3. **R1** counts contractible forms from transcript tokens by r3-P01's class rule, not from the feature files; class B
   has fewer than 5 creators, so ling's prediction about class B cannot be checked.
4. **K-cue** uses the RX cue reader's stored hits (CROSS transcript pass); the opening-to-leave-taking span is a
   sensitivity locator on 12 creators.
5. **The frame band** uses the voice map's opening and closing parts (opening_end_unit, closing_start_unit).
6. **The median estimator is computed but not printed** (2026-11-26T06:09:15Z, the lead's step-1 decision 18). The prespecification names two AUC estimators; the median of creator AUCs, its interval and the quantiles over creators rest on a banded creator count, and the release's decision D67 does not print quantiles of creator values over such a count. Its reading words stay as computed, and no reading changes. A departure for privacy, after the results, stated here.

## Fields not stored, arms not run

- Punctuation-stripped voice labels at unit level: not found among the seen label instruments (labels/seen holds voice,
  asks, features, forecasts, sentences, titles); the punctuation-free relabel stays class c (1 to 5 USD). The
  reliability folders were not opened (they may hold hold-out material), so the lead may want that confirmed.
- Masked-ask relabel: class c, not run. Register-normalised relabel: dropped by the programme.
- The label's run-to-run ceiling at creator level: no repeated small-model labels of these units were used; not computed.

## Contacts

None (see `contacts.md`).

## For the lead

- The register the labeller sees predicts the label (pooled AUC about 0.73 to 0.77) while the contraction drop survives register
  matching; the register-only locator carries somewhat more of the drop than its agreement with the label predicts (D
  +0.27, 90% 0.10 to 0.44, undetermined against the 0.20 margin). Both facts should print together; the entry's reading follows the prespecified rule.
- The prespec's reading rule lets the AUC rung matter only through estimator disagreement or when R3 fails; with
  r3-P30's cap the rung can no longer read "beyond" at this count. The lead may want the "cannot be told apart" branch
  restated for capped rungs in a later deposit.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
