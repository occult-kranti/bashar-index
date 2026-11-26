# r3-P05 / r4-P05: ask placement under position; who voices the ask

Third-round panel programme, step 1 (class a.1), inside r3-P04's prespecification and after r3-P06. Written 2026-11-26
(UTC times from `date -u` in status.json) by a model agent working for the project lead (not a person). r4-P05's no-cost
part (novelty N16, carried under the registry's N4; not a new claim) is carried by this entry. r3-P22's arm A is class c
(not run); the declared-persona comparison is class b (r3-P67).

**Status.** Exploratory; not a test of H1-H10. Seen creators only. Every label is model-coded and not checked by a person;
agreement between models is agreement, never accuracy. Asks are described as the creators make them: requests to buy or
enrol, to act on the platform, to go off it, or to give money.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What it asks

Once position in the recording is held fixed, are pay-or-enrol asks still rarer in the claimed voice than the other
units of the same stratum, and rarer than frame formulas the genre allows in either voice? Three placements are told
apart: the closing slot (convention), the host's footing toward the audience, and a separation specific to commerce. The
expected direction is also a documented convention of host-read advertising (N16's prior work).

## Method (r3-P04's `code/prespec.json`, r3-P05 part, before any outcome)

- Items: final asks of a class at their first unit; voice by H6's majority-of-words rule (asks on neither side left out);
  frame-formula units as r3-P06. Recordings with both voices (300 words each side), H6's definition (V2 + V3, rule B).
- Strata: recording x tenth (primary), twentieths and 60-s bins (sensitivities), recording (the frozen OE centring).
  Informative stratum: an item and a claimed share p of its units strictly between 0 and 1.
- Stat's two-stage, exactly centred score: z = (sum O - sum E)/sqrt(sum V) per creator, E = m p, V = m p (1 - p); mean z
  with a t interval and an exact sign-flip check; cohort ratio R = sum O / sum E with a creator-cluster bootstrap. If R and
  the mean score disagree in direction the class is undetermined.
- Margin: deposit 2's ratio margin 0.80 to 1.25 (den-soc's 0.5 and 0.67 to 1.5 are a pointer only); named direction:
  fewer claimed asks than position predicts.

## Results (small model, all recordings with both voices, tenth strata)

- **Reading: A.** Pay-or-enrol asks fall in the claimed voice 0.29 times as often as position predicts (90% 0.08 to
  0.47; mean score -1.29, -1.64 to -0.95; the two agree in direction). Twentieths 0.33 (0.14 to 0.52), recording strata
  0.21 (0.09 to 0.34). The middle model's row (180-s trims) points the same way; its values are not published (claimed
  asks from fewer than 5 creators). Not "inseparable from position": printed with equal prominence beside LAB-A.
- **Class: undetermined.** Platform asks (0.16, 0.07 to 0.27) and off-platform asks (0.17, 0.09 to 0.29) are pulled out
  of the claimed voice as strongly as pay-or-enrol asks, the signature den-soc named for the host's footing toward the
  audience in general; but "footing" also needs frame formulas below the margin, and they sit at 0.79 (0.60 to 0.93).
  "Commerce-specific" needs the commerce-minus-frame contrast below zero on both estimators: the ratio of cohort ratios is
  0.36 (0.10 to 0.65), but the creator-mean score difference is -0.38 (-1.00 to 0.23), which includes zero.
- Position-predicted against observed (the ladder): the creator-balanced claimed share of pay-or-enrol asks is 0.065
  (0.017 to 0.113) against 0.359 (0.305 to 0.413) that position predicts; the labelled share over all such asks is 0.117
  (0.058 to 0.175); at the rule-reversal end (asks in own-voice islands or just before a claimed span resumes counted
  claimed) it is the same except in fewer than 5 creators (not printed). The page-only rung is not built here.
- occult's row: of own-voice pay-or-enrol asks outside the claimed span, the creator-balanced share after the last claimed
  offset is 0.72 (0.60 to 0.84): more come after the last offset than before the first onset, the direction den-soc
  predicted from platform convention.
- By tenth (figure): the claimed share of words rises to about 0.7 mid-recording and falls at both ends; pay-or-enrol and
  platform asks stay well below it in every merged bin; frame formulas sit near or above it.
- r3-P06's gate did not fire; it rests on island asks of fewer than 5 creators.
- Money gifts: fewer than 5 creators (not computed). Dissemination asks: not a class of the frozen asks codebook (sharing
  is pooled into the platform class): not stored, not computable without a list (ruling 11) or a model read (class c).

Interval note: cohort ratios carry a creator-cluster bootstrap 90% interval (not a class r3-P30 calibrated); mean scores
the t interval on creator means (r3-P30's nearest class, one value per creator, chooses it at these counts; r3-P30 class E_rank_correlation: the t interval on creator means at every simulated count); shares by
tenth the t interval on creator means, as a description. Half-effect disclosure: about 2.8 readings A at the deposited 5%,
up to about 6.1 for the share, standardised, AUC and rank-correlation classes (r3-P30's readings table); a reading A is
never called a finding.

## Departures

- The primary is the small model on all recordings (r3-P04's base); LAB-A's voice primary is the middle-model subset,
  where claimed asks come from fewer than 5 creators.
- The own-voice-only position curve (css's platform baseline) and the page-only rung of r4-P05's ladder were not built.
- A unit's tenth is by sentence-unit index (the frozen H6 convention), not by time; the 60-s rows use unit start times.

## Contacts

None (see `contacts.md`).

## For the lead

1. The class rule as written needs both commerce-minus-frame estimators below zero; they disagree here (ratio of ratios
   below 0.80, score difference crossing zero). The entry prints "undetermined", as stat's disagreement rule says.
2. r3-P06's deictic arm would fire the gate if it were read on that statistic; the commerce-specific class is not reached
   either way.

## Files (SHA-256)

| File | SHA-256 |
|---|---|
| `public/data-r3-P05-by-tenth.csv` | `b553bc041a73c403fa193742915949cd677a955003533857f7e17d9aa4d535ed` |
| `public/data-r3-P05-forest.csv` | `532933f4851c54a4fa4e0bfd498e9315832cebe3d03f8005d309060d98ec7cfa` |
| `public/fig-r3-P05-by-tenth.pdf` | `5f15cee49b0e77166cc414dd957534220f5418f75e0f643583814dcf5062843d` |
| `public/fig-r3-P05-by-tenth.png` | `f166b6226683376a157b7ad99ad0079df6cbe0a587cee0b8d4760cd7b9f33bbd` |
| `public/fig-r3-P05-forest.pdf` | `1d42801adec75fc4d3a9ad963267ce87b3eb55caee73b2d3fd212082916be87c` |
| `public/fig-r3-P05-forest.png` | `c3217951559640c0fa52a950697875c60c8e326bfc5e3a3a0b718bb9c3a585ff` |
| `public/r3-P05-contrasts.csv` | `c87824f6c76106a9a390fd7b02097d9cbee84bef20514c0be082f49bd9944ba2` |
| `public/r3-P05-reading.csv` | `e2ea402d63894f2c3b00d044af2d3a9055220a2cc9f4639d1f8b726f1935f610` |
| `code/p05_publish.py` | `503fa8ac22146843105a53c8434b52030075630db53fc9f7061674bf8cc794d7` |
| `code/p05_run.py` | `68a975dbf629f0fa1cd4efd9e64ffc6896dcd08cf79fba9e808c6908f338685c` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `../r3-P04/code/common.py (shared)` | `afb6dcf765d44997672e7341911a70990e889cd6407bf50145ebc41dc016874b` |
| `../r3-P04/code/intervals.py (shared)` | `f428af347014e1b390261794aa58fc6f573b612bb3148aac3db6883d965c599d` |
| `../r3-P04/code/prespec.json (shared)` | the hash recorded at hashing time is kept privately |
| `../r3-P04/code/pubcommon.py (shared)` | `b3a81fe31eee2e48d614ae72db333dbabaebef4a07fe38f52e52bffad0296d02` |
| `../r3-P04/code/scan_public.py (shared)` | `73bbe208ffa5e6ddadc59fa01173a4ae2b181ad748f325997087c723c1696ec9` |
| `../r3-P04/code/write_status.py (shared)` | `b24b1f356fbd180caef9dc8ccd3a591fcf3962d311f047b73717243d2071993f` |

Code files carry local paths and stay private; their hashes are the record. Per-creator numbers stay in `private/` under anonymous indices.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these recordings and how the creators present it.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
