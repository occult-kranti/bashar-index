# r3-P46: source names as title templates, and classes of name (step 2 of the third-round panel programme)

Run on 2026-11-26 (UTC, every time from `date -u`) by the step-2 description agent for r3-P43, r3-P44, r3-P45 and r3-P46
(a model agent working for the project lead; not a person), after deposit 3 (merged 2026-11-26T11:14:53Z) and r3-P42.

**Exploratory; not a test of H1-H10.** Tier L: the 23 non-development seen creators, run once with no split. Every count
is a cue count. Title codes and source-family readings are model-coded and not checked by a person; agreement between
methods is agreement, never accuracy. Name classes come from the literature (L04), never from counts, and no list of
names tied to one channel exists (decision 51 L4).

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What was run

The shared prespecification (`prespec.md`, section 5; hashed 12:44:24Z, before any count) and the shared run of
12:49:11Z to 12:51:57Z (`code/analyse_p4346.py`): L04 matched once more on the 23 creators' page titles (from r3-P42's
extract), and MTMM's four source-family measures rebuilt with CROSS's `mtmm.py` definitions and seen-only loaders for the
23 creators.

## Results in words

**Classes of name: not computed.** No expanded form of the OPEN or FRANCHISE class is used in the titles of 5 or more of
the 23 creators (addendum 2d's sense of "term"; r3-P42's row reading gives the same: no name is used by 5 or more), so
both classes print "not computed (too few terms or creators)". UNNAMED (a P1 title naming no listed name), carried from
r3-P42: 0.833 of P1 titles (35 of 42 titles; titles, not creators).

**Template status: not computed.** Pooling both classes, no listed name form is used in titles by 5 or more creators (the
thin rule needs 3), so template status (2 or more titles holding a listed name) and the comparison of MTMM's cells with
and without template recordings print "not computed (too few terms or creators)". The entry rests on these thin classes
and so cannot answer its own question on tier L.

**MTMM's source-family cells on tier L, all recordings** (described, not read; 23 creators, each holding all four
measures; 90% creator-bootstrap percentile intervals, 2,000 draws, a fixed method):

| Pair | Inputs | Spearman rho (90% interval) |
|---|---|---|
| small against rule | title against transcript | 0.374 (0.042 to 0.638) |
| small against page | title against title | 0.749 (0.486 to 0.934) |
| rule against page | title against transcript | 0.466 (0.045 to 0.731) |
| small against middle, middle against rule, middle against page | | not printed: the middle-model measure is non-zero for fewer than 5 of the 23 creators |

As in MTMM and r3-P26, the pair reading the same input (two title readings) agrees more than the pairs that cross from
titles to transcripts; on 23 creators the intervals are wide.

## Not computed

- OPEN and FRANCHISE; template status; MTMM's cells without template recordings and their differences: "not computed
  (too few terms or creators)".
- Three MTMM cells on tier L: not printed (fewer than 5 creators carry the middle-model measure).

## Files

| File | What |
|---|---|
| `public/data-r3-P46-classes.csv` | the name classes (both readings of the thin rule), UNNAMED, template status, the pooled count of names used |
| `public/data-r3-P46-mtmm.csv` | MTMM's six source-family pairs on tier L: with all recordings, and the not-computed comparison |
| `public/fig-r3-P46-template.*` | creators by template status (its status) and MTMM's source-family cells |
| `prespec.md`, `prespec-amendment-1.md`, `prespec-hash-record.md` | the shared prespecification and its hashes |
| `code/` | the shared code (identical in the four entries) |
| `contacts.md`, `status.json` | contacts (none) and the status with every file's SHA-256 |

## Privacy

No name is printed (none is used in titles by 5 or more creators). Creator counts printed: 23 only; template-status
counts are not printed (not computed). Counts of titles and of list forms are not counts of creators. Intervals are a
fixed-method creator bootstrap. The privacy solvers and the identifier scan ran before finishing (status.json): 0 rows
pinned or narrowed, 0 identifier hits.

## Departures

1. The rebuilt MTMM measures read the seen voice records of every seen creator (CROSS's loader) and keep the 23
   creators' only.
2. Shared departures (r3-P43's README): the thin rule's wording; figure layout edits after the first look.

## For the lead

- r3-P46's question (do CSS-5's profiles and MTMM's source-family convergence agree partly by construction through
  titles?) cannot be answered on tier L: listed names are too rare in these 23 creators' titles. A run on a larger tier
  would need its own registration (decided: decision 68).
- MTMM's middle-model source-family measure is non-zero for fewer than 5 of these 23 creators.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
