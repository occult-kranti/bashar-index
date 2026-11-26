# r3-P33: a headline robustness and informativeness audit, with the selection rule printed

Third-round panel programme, step 1 (class a.1), after r3-P06 and r3-P30. Written 2026-11-26 (UTC times from `date -u`
in status.json) by a step-1 agent (a model agent working for the project lead; not a person). Seen creators only. No
model call, no network call, no download. Every input is a published file, except a draft of the release README (not published; the published README
carries no list of 17 descriptions): the exploratory round's public tables, and the step-1 entries' public files (r3-P01, r3-P03, r3-P04, r3-P05, r3-P06, r3-P30, and r3-P26's
result). No creator-level value was read.

**Status.** Exploratory; not a test of H1-H10. Labels are model-coded and not checked by a person; agreement between
models is agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## The selection rule, printed before it was applied

`prespec.md` (SHA-256 `b67a0ab79e627078c3e732bf709c4aff6525a3d7230845f8cf464421571c6539`) was hashed at
**2026-11-26T06:36:30Z**, before the rule was applied; `p33_run.py` refuses to run if it changed. Known leak (stated
there): the writer had read the README, the headlines and the step-1 entries' public files first; the rule follows the
programme's named panels and rows and chooses no estimate.

**Part 1: how the 17 "most informative descriptions" of a draft of the release README (not published; the published README carries no such list) were chosen.** **Chosen after the results
were seen.** No rule that chose them is printed in any place searched: that draft README (its section says only that
each description rests on 5 or more creators), the status table, the collector's code and records (read file by file),
the lead's decisions of 2026-11-22, the deviations summary, the addendum-3 draft and the published programme (which
records the absence, A6). This is the wording the programme's correction text (r3-P35) asks for.

**Part 2: this audit's rule** (prespec S1 to S12, in short): the unit is a stated seen quantity of the 17 descriptions or
of the cited outputs' headlines; hold-out statements are not audited; each quantity is a contrast or a level; every
contrast is classed against deposit 2's margin for its measure type ("for design only": the margins were fixed after
these results were published) and given a detectable size; the artefact cascade has one panel per seen by-voice
headline the programme names (H1, H4, H6, E5) with rows in the programme's fixed order; envelopes are lower bounds;
a thin panel-wide band is drawn as a disclosure.

## Primary: the artefact cascade (`fig-r3-P33-cascade`, `r3-P33-cascade-readings.csv`)

Rows in the fixed order: unmatched; position-matched; beyond both transplants (XT and ST); register-matched; middle
model; acoustic (a.2, never computed here); the asks envelope. Values and their 90% intervals are those the step-1
entries and E5 printed (r3-P30's method where the entry applied it); a row is capped at undetermined where its source
says no interval method holds at its count or its reference is not admissible.

| Headline (margin; named direction) | Computed rows | Rows reading A | Cascade reading |
|---|---|---|---|
| H1 rate, log ratio (0.223; slower in the claimed voice) | 5 | not printed | not printed: it rests only on rows whose count is banded |
| H4 contraction, SD units (0.20; fewer contractions in the claimed voice) | 6 | 2 | **A on 2 of the 3 computed rows whose reading is printed** (unmatched, register-matched); first row without A: beyond the cross-creator transplant (the reference is not admissible at this count, r3-P04; the interval alone lies far beyond the margin); some rows' readings are not printed for privacy |
| H6 asks, observed minus expected share (0.05; fewer claimed asks) | 4 | not printed | not printed: it rests only on rows whose count is banded; register-matched not built; the middle model not published (fewer than 5 creators); the asks envelope not printed |
| E5 long pauses, per 100 words (no deposited margin fits) | 2 | - | **every computed row includes zero** (small model +0.45, 90% -0.07 to 0.96; middle model +0.91, -0.06 to 1.87); position, transplant and register rows not built |
| E5 fillers, per 1,000 words (no deposited margin fits) | 2 | - | **every computed row includes zero** (small -0.13, -0.55 to 0.28; middle -0.57, -1.60 to 0.46) |

**In words.** No seen headline keeps reading A through every row; none could, because the acoustic row is not ruled in.
The contraction contrast (H4) survives register matching; whether it survives the transplants cannot be said at this
creator count. The cascade readings of the ask placement (H6) and the rate (H1) are not printed: they rest only on rows
whose count is banded; H6's middle-model and envelope rows cannot be printed. E5's pause and filler contrasts include zero on both models and have no matched rows.

**The asks envelope is a lower bound.** Its rule-reversal end (island asks counted claimed, r3-P06) differs from the
labelled value in fewer than 5 creators, so it is not printed (pairs rule); r3-P05 printed the same fact for the
creator-balanced share. The two-model envelope of LAB-A's level, 0.061 (small model, all seen recordings, 95% 0.034 to
0.092) to 0.078 (middle model on its subset, 95% 0.013 to 0.164), is on different bases. Both are lower bounds on label
uncertainty: shared errors of one vendor's models (VER-DEP) are not inside them.

**Panel-wide band** (thin bars; a disclosure, not a test): each printed interval widened by 1.898 on each side, the
Bonferroni factor over the register's 56 primaries (normal approximation). The H4 unmatched and register-matched rows
stay beyond their margins under it; rows whose values are not printed (their count is banded) have no band.

## Informativeness of the 17 descriptions (`data-r3-P33-informativeness.csv`, `fig-r3-P33-informativeness`)

Of the 15 classed seen contrasts with a deposited margin type, 2 (r3-P04's H1 and H6 unmatched rows) are not printed:
their counts are banded. Of the other 13, **5 lie beyond the margin** (H4 unmatched; PT-cd's pay-or-enrol, money and
off-platform asks, written more often than said; E2's small-model profile distance), **1 is trivial** (excludes zero,
inside the margin: MR-18c's unit-rate gap),
**2 are equivalent** (E6's formula coverage; E3's edge pace), **3 are non-zero with size undetermined** (E2 on the
middle-model subset; E1's pooled thanks-phrase ratio; E3's rise in address at the end) and **2 are uninformative**
(PT-cd's platform asks; E1's creator-equal ratio, also capped). Ten more contrasts have no deposited margin that fits
their units (TL-7.1's slope, E5's pauses and fillers, DC's seen comparator, five CSS-12 vocabulary differences, E9):
TL-7.1, DC and two small-model CSS-12 rows exclude zero; the rest include it.

**Detectable sizes** (80% power, one-sided 5%, from the printed interval), printed beside every contrast not beyond its
margin: for example E5's long pauses 1.42 per 100 words and fillers 1.56 per 1,000 words (middle-model subset, 20
creators); E6 0.041 (below its 5-point margin, so its equivalence is informative); E9 2.57 shared runs per pair (6
creators), so E9's null says little; PT-cd's platform asks 0.116; E1's creator-equal ratio 1.42.

**Not classed** (`r3-P33-not-classed.csv`): levels (LAB-V, LAB-K, LAB-A, TL-BUILD, TL-7.7, nlp-R10, nlp-R11, nlp-R13,
CSS-5, CSS-10, the CSS-12 census), agreement figures (MTMM and TL-7.8, read over input-disjoint pairs by r3-P26; DR-2,
VER-DEP), checks (MR-18d, nlp-R7), contrasts printed without an interval of the difference (PT-cd's within-creator
excess, RX-CB) and hold-out statements (items 10 and 12, the hold-out values of item 11, E3-H, VER-MV): not audited.

**rv-R4** covers one audited quantity: the thanks phrase at a window end (item 13's E1) moves beyond rv-R4's own margin
in 20 of 40 weighting and window specifications (8 with an interval outside the baseline band).

**Multiplicity.** 56 primaries; at half the margin about 2.8 readings A by chance at the deposited 5%, up to about 6.1
for the share, standardised, AUC and rank-correlation classes (r3-P30). A reading A is never a finding.

## Departures and choices (stated)

1. **E9 added** to the informativeness table after the rule was printed: the programme's section 4.2 names it among the
   nulls whose detectable sizes r3-P33 prints; it is not in the 17 descriptions (S1 would have left it out).
2. **Margin types chosen** where the unit needed a judgment: E2's z-scored cosine is read as a correlation (0.10);
   DC's vocabulary-similarity difference, TL-7.1's slope, E5's rates per words, CSS-12's terms per 10,000 words and E9's
   runs per pair read "no deposited margin fits".
3. **E5's rows**: the small-model row is r3-P01's reproduction on H1's spans (no seam rule); the middle-model row is
   E5's primary without the seam rule, to match it; E5's seam-rule row is the informativeness row.
4. **The round-3 survival matrix** (listing-rank, vintage, visibility, audience reweighting, template perturbation,
   leave-1-out and leave-5-out) and a studentised max-t band were **not run**: the adopted programme's step-1 text and
   deposit 2's primary fix the cascade; boundary fragility is r3-P32's. rv-R4 is cited where it applies.
5. **Detectable sizes** use a normal approximation from each printed interval, also for bootstrap intervals.

## Bases or fields not stored

- No acoustic row (a.2). No register-matched row for H1, H6 or E5, no position or transplant rows for E5 (not built by
  any step-1 entry). The middle model's H6 rows and the far end of the asks envelope are not publishable (fewer than 5
  creators).
- The roster-history arm (uploads before the newest 20) is class b, riding on r3-P72's metadata request.

## Contacts

None (see `contacts.md`).

## For the lead

1. Whether r3-P35's correction for the README should read "chosen after the results were seen" (this audit found no rule).
2. H1 reads "inside the margin" at deposit 2's ratio margin on every small-model row, while the registry's H1 smallest
   effect (r3-P04's sensitivity row) is much narrower: the README's E5 and MR-18c sentences describe a slowing that the
   deposited margin calls small.
3. Whether E9's null (detectable size about 2.6 shared runs per pair, 6 creators) should be printed with that size.

## Files

SHA-256 of every file: `status.json`. Public data CSVs carry a commented header; PNGs at 200 dpi without text chunks;
PDFs without document information.

| File | What |
|---|---|
| `prespec.md` | the prespecification and the printed selection rule (hashed before it was applied) |
| `public/r3-P33-selection-rule.csv` | part 1 (how the 17 were chosen; places searched) and part 2 (pointer to S1 to S12) |
| `public/r3-P33-cascade-readings.csv` | the cascade reading per headline (the primary) |
| `public/data-r3-P33-cascade.csv` | every cascade row with its source, interval, panel-wide band and reading (figure data) |
| `public/data-r3-P33-informativeness.csv` | every classed contrast: margin, class, r3-P30's view, detectable size, rv-R4 |
| `public/r3-P33-not-classed.csv` | levels, agreement figures, checks and hold-out statements, with why they are not classed |
| `public/fig-r3-P33-cascade.png/.pdf` | den-meth's artefact cascade |
| `public/fig-r3-P33-informativeness.png/.pdf` | classed contrasts on a margin scale with detectable sizes |
| `code/p33_run.py` | the audit (published inputs only) |
| `code/style.py` | the CHANGE group's style, copied unchanged |
| `code/zsolve.py`, `qscan_all2.py`, `quant.py`, `quant2.py` | the release's privacy scans, pointed at this folder |

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
