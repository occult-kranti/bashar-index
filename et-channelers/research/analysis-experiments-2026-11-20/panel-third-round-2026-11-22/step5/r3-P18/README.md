# r3-P18: a transparent footing locator and a disagreement diagnostic (step 5, class a.1)

Run on 2026-11-26 (UTC, from `date -u`) by the step-5 agent, a model agent working for the project lead (not a person).
Prespecification `prespec.md` (with the closed codebook) and `../common/prespec-common.md`, hashed at 14:11:38Z before the
extract ran; analysis 14:20:56Z to 14:21:08Z; publication from 14:28Z.

**Exploratory; not a test of H1-H10.** Voice labels model-coded, not checked by a person. The codebook and the labeller read
the same transcript: their agreement is **by shared design**, never validation, never accuracy. The value lies in the
disagreement cells and in a free locator for a wave.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Tier X**: the 11 voice-eligible non-development creators; the locator's one tuned part, the hold length L, is fitted on
the other half with T (matching the label's claimed share of words) and read on each half. The fitted L is "no limit" for
both codebook variants.

## Results in words (11 creators)

- **Four cells (word shares, creator-balanced).** Full codebook: agreed claimed 0.42, agreed own 0.28, label claimed with
  locator own 0.08, label own with locator claimed 0.21. Pronoun-blind codebook: 0.32, 0.32, 0.18, 0.17.
- **Agreement by shared design** (Cohen's kappa, word-weighted): full codebook 0.28 (0.11 to 0.46); pronoun-blind 0.17
  (-0.01 to 0.35); r3-P03's RX cue span (reference) 0.08 (-0.03 to 0.18), its cells not printed (fewer than 5 creators
  carry one of them). A locator with this agreement is a weak screen for a wave.
- **The uncued share** (the primary for the label's reliance): on average **0.69 (0.59 to 0.78)** of the words the label
  calls claimed lie in units with no codebook cue within two units either side. Most of the label's claimed voice rests on
  something other than the codebook's deixis and frames (continuity, content, register).
- **The disagreement cells adjudicated by label-invisible features** (pronoun-blind locator, the primary; unmatched and
  position-stratified): the rows are **not computed or not printed**. meas's condition 3 is not met
  (no feature validated outside the table; the acoustic instrument is audio, later), so any row would be consistency
  of correlates, never evidence.

Predictions deposited: none. Multiplicity: 56 primaries; about 2.8 readings beyond the margin expected by chance if every
true effect sat at half its margin, up to about 6.1 for the share, standardised, AUC and rank-correlation classes.

## Rows not computed

Agreement by source type (too few creators per source type at 11, as prespecified); relayed spans apart (relayed voice alone
is below the reliability floor); the two-coder check of 300 windows (class c, about 1,000 to 1,600 USD); acoustic features.

## Files

| File | What |
|---|---|
| `public/data-r3-P18-concordance.csv` | four cells and kappa per locator, with the fitted L |
| `public/data-r3-P18-adjudication.csv` | disputed cells against the agreed cells on four label-invisible features (not computed or not printed) |
| `public/data-r3-P18-uncued.csv` | the uncued share and its bins; rows not computed |
| `public/fig-r3-P18-footing.png/.pdf` | the four-cell concordance panel and the uncued share over creators |
| `code/analyse_p18.py`, `code/publish_p18.py`, `code/style.py` | analysis, publication, style; shared code in `../common/code/` |
| `prespec.md`, `contacts.md`, `status.json` | prespecification (the codebook), contacts (none), status with every file's SHA-256 |

## Departures and choices (stated)

1. The adjudication rows read "not computed or not printed" (the lead's decisions 92, 99 and 104). No value changes.
2. The index s is a ratio of small differences: where the agreed cells barely differ, its point value can fall outside its
   bootstrap interval; the reading words follow the interval, as prespecified.
3. Cross-fitting with T on the fitting side in both folds; fold-level counts are not printed.

## Privacy

No per-creator row or point; the codebook is design text written without the corpus, with no count per pattern. Checks:
`../common/README.md`.

## Change by the lead's decision 92 (2026-11-26T15:25:06Z, UTC from `date -u`)

- Some cells were changed (privacy rule);
  the CSV and the figure's footer were changed (redrawn by this entry's own figure function). No
  number changed.

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- Some cells were changed (privacy rule), in the CSV, the figure (redrawn by this
  entry's own figure function, whose titles and footer were
  reworded) and this README; the hold length L prints as
  one value. No number changed.

## Change by the lead's decision 104 (2026-11-26T17:33:22Z, UTC from `date -u`)

- A change note is worded in general terms. No number changed.
