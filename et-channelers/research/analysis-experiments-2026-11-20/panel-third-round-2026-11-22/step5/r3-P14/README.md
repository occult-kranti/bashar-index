# r3-P14: read aloud, recited or spontaneous? The text part (step 5, class a.1)

Run on 2026-11-26 (UTC, from `date -u`) by the step-5 agent, a model agent working for the project lead (not a person).
Prespecification `prespec.md` with `../common/prespec-common.md`, hashed at 14:11:38Z before the extract ran; analysis at
14:19:54Z; publication from 14:27Z.

**Exploratory; not a test of H1-H10.** Voice labels model-coded, not checked by a person. Text features only (lexical slots,
recognizer word times, repetitions as transcribed). Public names: "read-like delivery profile" for the score and
"received text read aloud, self-described" for the attribution. The score is never printed per creator, never read as a
synthetic-voice screen, and never worded "scripted" or "not live". Reading a received text aloud is, in emic's reading (a
reading by a non-holder), a respected mode.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Tier X** for the text score (10 to 19 eligible non-development creators: the 11 voice-eligible creators of r3-P42):
two-fold cross-fitting on the deposited halves, the score's standardisation constants fitted on the other half with the
tuning pool T, read once on the 11. **Tier L** for the self-described attribution (L10's MODE-READALOUD).

## Primaries and readings (11 creators; 90% interval, r3-P30's choice for each class at 11)

| Row | Estimate (90% interval) | Interval | Reading |
|---|---|---|---|
| S read-like delivery profile score, claimed minus own (cross-fitted; margin 0.20 SD) | 0.08 (-0.58 to 0.58) | Hodges-Lehmann; no method holds for C_standardised at 11 | **undetermined** |
| W within-phrase pause share, claimed minus own (margin 0.05) | -0.07 (-0.21 to 0.08) | t on creator means (B, holds) | **undetermined** |
| R lexical repairs, log ratio claimed over own (margin 0.223) | 0.32 (0.10 to 0.55) | t on creator means (H, holds) | **undetermined** |
| Guided practice by voice | - | - | not computed (too few terms or creators) |
| Creators who describe their practice as received text read aloud (MODE-READALOUD) | - | - | not computed (too few terms or creators) (step 2) |

Described: within-phrase pause share 0.30 (claimed) and 0.37 (own); lexical repairs 8.1 and 4.6 per 1,000 words (claimed
voice higher on the point estimate, interval reaching inside the margin); most pause events (about 0.88 and 0.91) fall in
ambiguous slots, so the slot rule reads a small share of pauses. The score difference falls on either side of zero (bins of
6 and 5 creators).

The score's poles are not named: no reference corpus anchors it (the calibration corpora are class b), and the known-groups
check is not in the text part. The text part therefore does not say whether the claimed voice is read, recited or
spontaneous; it says the two voices are not told apart on these text features at 11 creators.

Predictions deposited: none. Multiplicity: 56 primaries; about 2.8 readings beyond the margin expected by chance if every
true effect sat at half its margin, up to about 6.1 for the share, standardised, AUC and rank-correlation classes.

## Rows not computed

The acoustic part (audio, later); two public calibration corpora (class b); listening (class c, 10 to 20 hours); guided
practice by voice and the self-described attribution (too few terms or creators); position matching.

## Files

| File | What |
|---|---|
| `public/data-r3-P14-rows.csv` | rows S, W, R and the rows not computed |
| `public/data-r3-P14-described.csv` | creator-balanced means by voice; histogram bins of the score difference |
| `public/fig-r3-P14-read-like.png/.pdf` | within-phrase pause share and repairs by voice; histogram of the score difference |
| `code/analyse_p14.py`, `code/publish_p14.py`, `code/style.py` | analysis, publication, style; shared code in `../common/code/` |
| `prespec.md`, `contacts.md`, `status.json` | prespecification, contacts (none), status with every file's SHA-256 |

## Departures and choices (stated)

1. Cross-fitting: T joins the fitting side in both folds (the policy places T on the exploration side and never reads it);
   fold-level counts are not printed.
2. Self-repair phrases are not counted (senses not resolved without a reader); repairs are lexical repetitions only.
3. Not position-matched (r3-P04's references are not rebuilt for these features).

## Privacy

No per-creator row or point; no text. Checks: `../common/README.md`.
