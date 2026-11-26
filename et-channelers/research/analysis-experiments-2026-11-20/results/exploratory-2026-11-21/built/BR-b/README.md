# BR-b: the run's recognizer text against other texts of the same audio (seen creators)

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory (registry A2); not a test of H1-H10. Plan section 6.7, row BR-b. Built on 2026-11-21 before the exploratory
round; this public form was made by the release review (plan P10) on 2026-11-22 (tables written 05:17 UTC; revised after
the release verification, tables rewritten 05:56 UTC: the caption row's recognizer-confidence halves withdrawn, labels and
notes corrected). Every row printed here is **agreement of two machines, not an error rate**.

## What it asks

How far is the recognizer's text from text made or edited by people? The plan's headline was a word error rate against
such texts, by stratum (text kind, length band, pace third, recognizer model), with substitution, deletion and insertion
shares, and with rows against machine texts labelled "agreement of two machines, not an error rate".

## The answer

- **No word error rate against text made by people exists.** No seen recording has a reference text known to be made by
  people, so that row is "not run" (addendum 1 item 2). Its hold-out and other-group part, BR-b-H, is not run either:
  fewer than 5 creators in each group have a reference that could be made by people; the recognizer was not run
  (lead's decision D33). D33 covers every hold-out and other-group part of BR-b, the machine-agreement rows included.
- **Platform automatic captions against the run's recognizer** (11 recordings of 11 creators): the two texts disagree on
  3.76% of the caption words (creator mean, each creator once; 95% interval 2.55 to 5.17%), or 4.89% pooled over
  words (2.65 to 7.22%). No caption recording agrees word for word. After the analysis artefact filter the creator mean is
  3.79% (2.60 to 5.16%).
- **Reproducibility** (the project's earlier text of the same recordings, made by the same recognizer and settings; 48
  recordings of 34 creators): disagreement 0.43% (0.13 to 0.75%), 0.24% pooled over words (0.03 to 0.58%); 40 of the 48
  recordings (83%) are reproduced word for word.
- **The larger multilingual model** (the project's earlier text of the same recordings made by the larger model; 5
  recordings of 5 creators; a row added after the exploratory reporting plan): disagreement 5.22% (2.47 to 8.20%),
  4.19% pooled over words (3.01 to 7.73%).
- Publisher-hosted transcripts of undeclared origin rest on fewer than 5 creators and are not published; the pooled row of
  all automatic texts is not published either (beside the caption row it would give the undeclared cell by difference).

**Sentence for the abstract and the dashboard** (addendum 1 item 12): No seen recording has a reference text known to be
made by people. Against platform automatic captions, the run's recognizer disagrees on 3.76% of words (creator mean; 95%
creator-bootstrap interval 2.55 to 5.17%; 11 recordings of 11 creators): agreement of two machines, not an error rate.

What the caption row does and does not say: edit distance obeys the triangle inequality, so the recognizer's own word
error against a perfect transcript is at most this disagreement plus the captions' own word error, and at least the
disagreement minus it. This holds in edit counts; as rates it holds only approximately, when the caption and a perfect
transcript are of similar length (the rates have different denominators). Neither bound is known without a reference
made by people. The two machines may share errors (similar models on the same audio), which would make their
disagreement smaller than either one's own error.

## Base

Seen creators only (the 71 of the registry); the recordings that carried English text of another kind and were set
aside before the run, decoded again with the run's English-only recognizer, its settings and its audio edition. No
hold-out or other-group text, caption, title, label or receipt was read for BR-b. The inventory table counts the
other-text recordings of every group from the run's ledger fields only.

## What is shown

| File | What it holds | Place |
|---|---|---|
| `public/br-b-anchor-rows.csv` | The anchor table: one row per normaliser, reference class and variant (raw, filtered, trimmed), with status, recordings, creators, reference words (rounded to hundreds), creator-mean and word-pooled disagreement with 95% intervals, and the share of recordings without disagreement | M (anchor table, abstract sentence); W (headline with interval) |
| `public/br-b-strata.csv` | The anchor rows by audio edition, length and recognizer confidence; the caption row in length halves (the only split printed with values) | S |
| `public/br-b-error-kinds.csv` | Substitutions, deletions and insertions as shares of reference words for the printed rows and the caption row's length halves | S |
| `public/br-b-other-text-inventory.csv` | The recordings with other text, by text class and group (addendum 2 item 3) | S |

Figures (gallery group B-BR): the anchor rows (BR-b-fig-1, M and W), the caption row's length halves (BR-b-fig-2, S)
and the error kinds (BR-b-fig-3, S).

**By stratum** (raw variant): the caption row by length, shorter half 3.20% (1.94 to 4.70%, 6 creators) and longer
half 4.44% (2.48 to 6.93%, 5 creators); the halves' intervals overlap. The length halves replace the plan's length thirds
(each third holds fewer than 5 creators) and are labelled "added after the exploratory reporting plan" with addendum 1's
time (2026-11-21 05:30 UTC). The caption row's recognizer-confidence halves (a stratum not in the plan, also added after
it) are not published: beside the length halves, a second split of the same 11 creators would bound the cells where a
length half meets a confidence half, which hold fewer than 5 creators. All caption recordings use native audio, so that
level is the row itself (one cell, one interval: addendum 1 item 13).

**Error kinds** (word-pooled shares of reference words): captions 1.62% substitutions, 1.49% deletions, 1.79%
insertions; reproducibility 0.10%, 0.06%, 0.08%; larger model 1.45%, 1.36%, 1.38%. No single kind dominates.

## The normaliser: version 2 was chosen after the result (plan P4)

Both texts are normalised the same way before a word-level Levenshtein alignment (Unicode, lower case, tags and markup
removed, symbols and numbers spoken as words, contractions expanded, punctuation dropped, filled pauses dropped). The
version reported, **wa-norm-v2, was chosen after the result**: it was fixed on 2026-11-21 at 03:31 UTC, after a check of
the commonest confusions on the first re-made transcripts, and the first tables (03:21 UTC) had used version 1. Version 1
was rebuilt exactly from the record and run beside it on the same pairs. Its rows print recordings, creators and the share
without disagreement, but no rates: beside the version-2 row of the same variant each version-1 row differs in fewer than
5 creators (pairs rule, addendum 2 items 2 and 9). Plan 6.7's rule that the text classes and the normaliser are fixed and
hashed before any rate was not met; both versions were hashed after the first rates (addendum 2 item 2).

Known defects of wa-norm-v2 (addendum 1 item 10): accented letters are dropped; the 'etc' and 'vs' rules also fire at
the start of longer words (this moved no published rate at the fifth decimal); only some decade forms are read; currency
is read only in simple forms. Each applies to both texts alike, but not equally often in captions and recognizer text.

## What is withheld, and why

| Part | Public form | Reason |
|---|---|---|
| Reference made or edited by people, seen creators | not run | no seen recording has such a reference (addendum 1 item 2) |
| BR-b-H (hold-out and other group, every part) | not run | fewer than 5 creators in each group have a reference that could be made by people; the recognizer was not run (D33) |
| Undeclared publisher transcripts (row and strata) | "fewer than 5 creators" | the row rests on fewer than 5 creators |
| Pooled row of all automatic texts | not published | beside the caption row it would give the undeclared cell by difference (addendum 1 item 4, a departure from plan section 3 recorded there) |
| Trimmed rows | counts and share only | beside the raw row each differs in fewer than 5 creators (pairs rule) |
| Version-1 rates | counts and share only | beside the version-2 row each differs in fewer than 5 creators (pairs rule) |
| Error kinds of the filtered caption row | not published | beside the raw row their difference rests on fewer than 5 creators |
| Caption row in thirds | not published; length halves instead | each third holds fewer than 5 creators (halves added after the exploratory reporting plan, addendum 1 item 1) |
| Caption row by recognizer confidence (halves; their rates and error kinds) | not published | beside the length halves, two splits of the same 11 creators printed with sums or means would bound the cells where a length half meets a confidence half, which hold fewer than 5 creators (Fréchet bounds; withdrawn after the release verification of 2026-11-22) |
| Reproducibility row by audio edition, length third and confidence third | one line each, no level listed | a level rests on fewer than 5 creators or its disagreements come from fewer than 5 creators, and the levels and the row would give one another by difference (D21) |
| Larger-model row's strata | not published | every level holds fewer than 5 creators |
| Pace third and recognizer model strata | not run | not built; the recognizer stratum has one level (addendum 1 item 1) |
| Errors on numerals and years; on capitalised names | not run | the code does not compute them (BR-y covers years and numbers on the same pairs); the normaliser lower-cases (addendum 1 item 3) |
| Undeclared class in the inventory, both groups | "fewer than 5 creators" | the class total is public, so both group cells are withheld (addendum 2 item 3) |

Every printed statistic rests on 5 or more creators with a non-zero value (or on none); no two printed cells of one
reference class differ in 1 to 4 creators; no two printed splits of one row meet in a cell of 1 to 4 creators; shares
without disagreement are printed only where recordings with and without disagreement each come from 0 or 5 or more
creators. The release review rechecked every printed cell against the item's seen per-creator values (2026-11-22, 05:15
UTC; again after the revision, 05:56 UTC, with the check reading the printed cells from the public tables themselves).

## Interval level

95% percentile intervals from 2,000 creator-bootstrap resamples, with a seed of its own for each cell (re-seeded per cell
before release, addendum 2 item 6). Creator mean: each creator weighted once; word-pooled: all words of a row pooled.
Pointwise intervals; no family-wise control. Interval levels differ between the round's packages (D18).

## Caveats

- No row measures how close the recognizer comes to what was said: every row compares two machine texts.
- Few creators: the caption row rests on 11 creators and the larger-model row on 5; a few creators' recordings carry much
  of such a row's disagreement.
- Not a sample of the run: the other-text recordings are one group of recordings (set aside before the run because text
  of another kind existed); the caption row is all native audio, one recording per creator.
- The references were not checked against the audio; heads and tails present in only one text change little (the trimmed
  rows are not published, for the pairs rule).
- The project's earlier-text rows have no filtered variant: their reference is unfiltered recognizer text, so like is
  compared with like (as built).
- The reproducibility row compares the run's final recognizer worker with earlier workers of the same model and
  settings; the recordings that are not reproduced word for word differ by code path or numerics, which were not
  separated.
- Normalisation is a set of choices (for example years read as years, 's read as "is"); other choices move small rates by
  tenths of a point. Platform captions may drop or merge words at caption-line breaks.
- Recognizer output and machine captions, not checked by a person.

## Code

Public tables written by `br_public.py` (SHA-256 `a03e56ab5f6ff37c3ab1cefacba8f4ad51975a9d0aa71042bf49c0dd6170da66`)
from the item's own tables; every printed cell checked by `verify_br.py` (SHA-256
`592d9b7da6d4e9df228494036e5a0a48b3514fcd130679a80202986f4eb31efd`); figures drawn by `plot_br.py` (SHA-256
`47a09ba3f3dbd224e2d4a4063353b70f9d72809bf090aa058eee039e5f151433`). The first public form (`br_public.py` SHA-256
`f1dacf5a7a03b00eb5747a6d0d8805c647dda42253b1d1da271344b8eaebd7fe`, `verify_br.py` SHA-256
`514fb7a46afb8d5e1ce947156520cf70b39438fc69cfde314f45b5252062443a`) was never published. Normaliser versions: wa-norm-v1 SHA-256
`fa543673e9982337b5a4b8d7a8223b330c05c2a4120b2f0e5fb12d7b738a6492`; wa-norm-v2 SHA-256
`208c78f069de65742775103cbfcaa55f6a1e97e3d07a57d733dd41ee58912655`.
