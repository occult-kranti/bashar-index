# Exploratory round of 2026-11-21 to 22: release

Exploratory (registry A2); not a test of H1-H10.

Release of the exploratory round, assembled 2026-11-25T22:35:48Z (UTC, from the clock) by the collector of release pass 2,
from the round's public files as reviewed in release passes 1 and 2, under the lead's decisions D1 to D70 (taken under
the owner's delegation; registry 2026-11-22 02:09, 05:00 and 07:15; D57 to D70 on 2026-11-26). It reports against the registered
[exploratory reporting plan](../../exploratory-reporting-plan.md) and its addenda
[1](../../exploratory-reporting-plan-addendum-1.md), [2](../../exploratory-reporting-plan-addendum-2.md) and
[3](../../exploratory-reporting-plan-addendum-3.md). The figures are in the gallery: [`gallery/index.html`](gallery/index.html).
Dated corrections made after publication (2026-11-26: the third-round programme's r3-P35 under the lead's ruling 13,
and D72 and D73) are listed under [Corrections](#corrections) at the end; they change no verdict.

## What the round is

- **After the registered tests.** The registered first-round tests ran on the hold-out creators on 2026-11-21 (18:54 to
  19:03 UTC) and are published in [`../first-round-2026-11-21.md`](../first-round-2026-11-21.md): all six were
  uninformative (not determinable, or not run for want of an instrument). The exploratory round began afterwards, at
  2026-11-21 23:17 UTC. **Nothing in this folder is a test verdict, and nothing changes or adds to the registered
  verdicts.**
- **Code written after freeze 2.** All the round's code was written after freeze 2 (2026-11-21 16:10:00 UTC). Outputs
  that needed only seen creators' first-round labels (plan status L) carry the words "added after the exploratory
  reporting plan" for every choice their code fixed. Hold-out outputs (status F2) were run by code that is not in the
  freeze-2 record, which departs from the plan (deviation R1): each driver ran on the seen creators first, with the same
  SHA-256, and then once on the hold-out, and every run and repeat is in the contact log.
- **Two waves and two release passes.** The first wave (packages LAB, TL, VER, CROSS, E, HOLD, HOLD2) ran the no-cost
  outputs of status L and F2. After the lead's decisions D1 to D19, a second wave (ER, MR, NLP, CSS, BRBH) ran the
  no-cost outputs no package had taken (D4), and package E9H ran E9's hold-out part by the owner's order of 2026-11-22
  02:22 UTC. Package FIX1 made release-review edits of wording. Release pass 1 (2026-11-22, about 05:10 to 07:10 UTC)
  drew a figure for every reported output and reviewed the outputs built before the round into public tables; each
  group was verified adversarially and fixed. Release pass 2 (2026-11-25) applied the lead's decisions D40 to D56,
  recounted by creator the agreement figures it could rebuild (D48) and assembled this folder. Its five fix steps
  (2026-11-26) corrected the problems that the pass's verifiers, its release scans and an independent privacy check
  found. Of the 14 agreement
  figures the recount had left open, the first fix step settled 8 (6 recounted by creator, 2 found already
  counted; it also withheld two model-check precisions of ENTRY, a new entry), and the third recounted a ninth
  (the paper's frame-only relay kappa, whose sample holds seen creators only: it passes, D60); GRID's positional
  precision is withheld (D58), and 4 figures stay not recounted, each withheld or no longer printed (below). The
  fix steps also withheld cells that fail the dominance screen or isolate single creators, and corrected wording,
  dates and pointers, the third under the lead's decisions D57 to D66; the fourth fix step (fix5) applied D67 to D69 and the fifth
  fix step (fix6) applied D70 (below). What is still open is listed under "Still
  open for the lead" below.
- **No model was called in this round.** The model budget was spent before it began (the hard stop of registry
  2026-11-21 18:41). Outputs that need model calls are reported as "not run: needs model calls; no money left under the
  hard stop".
- **Multiplicity.** Displays with many cells are read only through a family-wise band where one was built, and say
  "pointwise intervals; no family-wise control" where none was (plan section 4). No p-value or interval here is a test
  of a registered hypothesis.

## Counts by status

From [`status-table.csv`](status-table.csv) (plan section 9), after both waves and both release passes:

- **172 outputs** are listed: every id of plan sections 6.1 to 6.11, and the hold-out ids of section 8 that have no row
  of their own in section 6. The 28 experiments of the analysis catalogue (section 6.12) are a mapping to these outputs;
  they are listed in the table and not counted.
- **111 reported:** 58 produced in this round (45 in the first wave, 13 in the second, E9's hold-out part among them as
  "not computable") and 53 built before the round, reported as built in their public forms (`built/` and the gallery).
- **1 superseded:** rv-L1, the interim kinds table, superseded as the census by LAB-K; both are printed side by side.
- **60 not run:** 42 will not run in this study for reasons known before the round (status X); 11 need model calls; 3
  have a registered precondition that was not met (TL-H, decision D2; E7 and E7-H, D3); 2 have a condition that was not
  met (E4 and its hold-out part: H1 is not determinable); BR-b-H (fewer than 5 creators in each group have a reference
  that could be made by people, D33); and the VER-DEP hold-out bounds (no registered estimate exists for them to stand
  beside, and computing them would be a further hold-out contact).
- **0 not released.** BR-b-H, the one output that read "not released" after the second wave, is "not run" under D33.
- **Main text:** 39 outputs have a place in the paper's main text, directly or through another output. 35 are
  published here and in the gallery (D54): 34 reported and 1 superseded (rv-L1, printed beside its successor LAB-K).
  4 are not run: HR (no package of the round carried it; it needs model calls), TL-SPEC, BR-b-H and the VER-DEP
  hold-out bounds. The paper's results section names the outputs with a main-text place that the round's packages
  carried: 12 reported and 3 not run (TL-SPEC, BR-b-H and the VER-DEP hold-out bounds).

## How to read this folder

| Path | What it holds |
|---|---|
| [`status-table.csv`](status-table.csv) | One row per output id of the plan (kind `output`), the catalogue mapping (kind `catalogue`) and the counts (kind `count`). Columns: kind, section, id, question, plan_status, status, reason, parts_not_run_or_not_released, place, utc_run, code_sha256, other_code_sha256 (every later writer or editor of the output's public files, with its SHA-256: D14), headline, files. `files` names the output's files in this folder and its figure ids in the gallery |
| `packages/<PKG>/` | The public CSV and Markdown files of each package of the round, with its README where it has one (`README.md`; TL's `README-TL.md`; HOLD's `hold-README.md`; ER's `ER-README.md`; BRBH's `BR-b-H-README.md`; VER's `ver.md`). Packages E, HOLD2 and E9H have no README of their own: this file and the status table describe them |
| `built/<ID>/` | The public form of each output built before the round (paper-review items rv-D1 to rv-L3, GATES, the verification and timeline pilots, BR-b and BR-GS): `README.md` and `public/*.csv`. The round-2 programme's built items (TABLE to KA, ENTRY) are published as figures and data files in the gallery only |
| [`gallery/index.html`](gallery/index.html) | Every released figure, with its caption, data file and place |
| [`contacts.md`](contacts.md) | The round's hold-out contact log, one row per contact |
| [`deviations.md`](deviations.md) | The round's departures from the plan, each with its decision, and the rows withheld for privacy |

The places are those of plan section 3: **M** the paper's main text, **S** the supplement, **W** the dashboard. Under D54
the paper's main text, written before this release, is not expanded: outputs with an M place are published here and in
the gallery, and the paper's results section points to them by id. This release copies only CSV and Markdown files, three
reviewed plain-text files (D63) and the gallery (D56): no package PNG or PDF (the gallery redraws every figure), no backup,
no private file and no status file. The three parts that their items wrote as plain-text files are published as CSV
files (release pass 2, fix step) and, since the third fix step, as the reviewed plain-text files themselves (D63):
rv-R7's abstract sentence (`built/rv-R7/public/rv-r7-abstract-sentence.csv` and `.txt`), rv-D2-H's sentences
(`packages/HOLD2/rv-D2-H-sentences.csv` and `.txt`) and rv-D8's proposed rule for future external calls
(`built/rv-D8/public/rv-D8-proposed-rule.csv` and `.txt`).

**Model-coded labels.** Every label (voice, asks, forecasts, sentence codes, titles, recording kinds) was made by
language models under frozen instruments unless an output says otherwise. Each description says "model-coded", names the verification that exists,
with its figures, and says "not checked by a person": the owner chose no person's check (registry A8). The full
verification lines, with intervals, are in `packages/LAB/README.md`; the gate figures are in `built/GATES/`. Relayed
voice alone is below its reliability floor. The forecast class of record is below its floor on the hold-out reliability
sample, and the sentence codes' stability is below its floor there.

**Agreement, never accuracy.** Agreement between models, readers or methods is called agreement. Recovery on constructed
known-answer texts is an upper bound and not a measure of correctness on the corpus. Pattern counts below their
precision gate are "cue counts". Change over time is described inside each channel's span and is never called a trend.
No prediction is said to have come true or to have failed: the study never checks that.

**Recognizer output.** Pace, pause, silence and tempo measures come from the recognizer's words and word times. They are
recognizer-output measures, not direct measures of speaking. The recognizer bridge found the pause and word-time measures
model-dependent, so every tempo result describes the recognizer's timing within one model.

**Hold-out outputs** (package HOLD, HOLD2, E3-H in `packages/ER/`, BR-b-H in `packages/BRBH/`, E9's hold-out part in
`packages/E9H/`, VER-MV) are exploratory hold-out descriptions. They are printed beside the seen creators' values, never
pooled with them, and never called a confirmation. The hold-out is the tail of an English-first run and is not
exchangeable with the seen creators: read every hold-out row beside the balance table (rv-D2 in `built/rv-D2/` and its
transcript part rv-D2-H in `packages/HOLD2/`).

**Interval levels differ between packages** (D18). LAB and NLP mostly use 95% creator-bootstrap intervals; TL, PT-cd,
E11, HOLD, HOLD2, MR, CSS and E9H mostly use 90%; ER prints 90% and 95%; BR-y uses exact 95% intervals (Clopper-Pearson);
the built items state theirs. Every caption and table note states its level.

## Privacy rules, in short

Every public file follows plan section 3 and the stricter rules the round applied (deviation R3; addendum 3 item 11):

1. Distributions and creator-level aggregates only. No creator or channel name, creator code, video id, title,
   quotation, per-creator or per-recording row, point or line, and no minimum or maximum of a transcript measure (10th
   and 90th percentiles instead).
2. No cell, bin, bar, point or plotted group rests on fewer than 5 creators; bins and categories are merged by the rule
   of plan section 3, and a whole output that rests on fewer than 5 creators reads "fewer than 5 creators".
3. Two printed creator counts of nested groups never differ by 1 to 4, also against counts already public (101 roster,
   71 seen, 23 hold-out creators, and every count printed in the release); where they would, a count reads "all but
   fewer than 5 of N" or "5 or more". Every pair that was public before the round is listed in addendum 3 item 9
   (D45, D57, D66), among the owner's items.
4. No value is recoverable by subtraction from public totals or by complement; a share near 100% whose misses come from
   1 to 4 creators reads "not published (misses from fewer than 5 creators)", never a bound near 100% (D21). No
   quantile is printed in a row whose creator count is withheld or printed as a band, because a quantile's position
   among the sorted creator values can give the count back (D67), nor in a row whose count of creators with a non-zero
   value is withheld or printed as a band, or which the quantile cells alone could narrow to fewer than 5,
   to within 4 of the row's base or to within 4 of another printed count (D70).
5. Pairs rule: of two printed rows whose difference rests on 1 to 4 creators, one is not printed (addendum 2 item 9,
   read as addendum 3 item 13 states).
6. Agreement figures: the positive code comes from 5 or more creators in each reading, and disagreements or misses come
   from none or from 5 or more creators (the 22:33 rule). Every agreement figure on seen, check or development
   creators printed here was recounted by creator in release pass 2 and its fix steps (D48, D60). The R-hold
   agreement figures are printed as the published first-round file checked them under the 22:33 rule; they were
   not recounted, because a recount would be a hold-out contact, and their gate A and B shares near 100% read
   "not published (misses not recounted by creator)" (D21, D59). GRID's positional precision, a share near 100% bounded
   from window-phase counts, reads the same (D58); nlp-R13's Chapman recalls near 1 rest on estimated, not
   observed, misses and are printed, labelled estimated (D58).
7. Dominance screen: a statistic is printed only where no creator provably holds half or more of the total, and only
   where 5 or more creators carry a non-zero value (addendum 3 item 11).
8. Years other than 2026 appear only in D28's form: the earliest years pooled into one open bin with no start year, and
   every bin resting on 5 or more creators. No local time-zone date; the gallery's PDFs carry no document information
   and its PNGs no text beyond the dpi (D30).

These rules hide values; they never choose an estimate. Where a package tightened them after seeing a rendering, its
status says so. **One exception:** by the owner's order (registry 2026-11-22 02:22 UTC), E9's hold-out part is released
although its base, H9's eligible hold-out creators, has fewer than 5 creators. It prints no figure of those creators: E9's
statistic is not computable on them, and the file says why.

## The lead's decisions, in their public wording

- **D11.** The known-answer region figure is "region recovery on constructed texts 0.96" (E2, E5, E6). Package E's
  tables say of known-answer recovery that it is "not a measure of correctness on it" (D47).
- **D12.** The hold-out's pace covariate reads "fewer recognized words per minute inside the recognizer's segments (a
  recognizer-output measure, not a direct measure of speaking)"; ENTRY's and TOPICS's pace wording reads "recognized
  words per minute".
- **D13.** CROSS's `README.md` is named among CROSS's outputs and released as the package README.
- **D14.** VER-MV's status names every writer of its public files with its SHA-256 (`ver_mv.py`, `ver_mv_flags.py`,
  `ver_mv_fix.py`).
- **D15.** The same-vendor third model's kappa is "the VER-3R sample (third model of the same vendor)"; the plan's VER-3R
  row stays the reader of another vendor.
- **D16.** One wording throughout: "a hold-out creator with one non-English recording among English ones". No new count
  is printed.
- **D18.** Interval levels differ between packages; every caption and table note states its level.
- **D21.** A recovery or agreement cell whose misses come from 1 to 4 creators reads "not published (misses from fewer
  than 5 creators)", never a bound such as a share near 100%.
- **D24.** The gallery keeps both figures of each overlapping pair, cross-referenced. The dashboard shows one of each
  pair: RXP's precision figure, COR-1, TIME's roles figure, and TOPICS-fig-3 for CH's span check.
- **D28.** rx-years is released only in the form DATES-2 uses: the earliest years pooled into one open bin ("up to ..."),
  with no start year printed, and every bin resting on 5 or more creators.
- **D33.** BR-b-H: "not run: fewer than 5 creators in each group have a reference that could be made by people; the
  recognizer was not run". This covers every hold-out and other-group part of BR-b, its machine-agreement rows included;
  BR-b's seen rows stay as built.
- **D40.** The owner's positional rule of 20 November ran until freeze 2 by its own terms. The hold-out positional
  outputs the plan registers for after freeze 2 (rv-D3-H, H3-X, E3-H) are published as exploratory outputs, beside the
  seen ones and never pooled (addendum 3 item 8).
- **D46.** The dominance screen and the joint-audit thresholds of the B-LV items were added after results, for privacy
  only; neither changes an estimate (addendum 3 item 11).
- **D50.** CSS-10's page-text base is not printed, because it lies fewer than 5 below 71 (D57); it is printed in no file. Its
  tables add up to the 71 through a pooled row "other or no page text", the counts beside the shares of creators are
  dropped, and the Wilson shares of creators are withheld too (confirmed by the lead, D57).
- **D51.** rv-R2's projected eligible counts are "simulated projections, not counts of creators". The pairs rule covers
  cells whose per-creator values differ in 1 to 4 creators, not bins of two series that differ in membership.
- **D52.** BR-GS's precision check and thanks row keep their fixed public form; its other measures are released. BR-b's
  recognizer-confidence halves were withdrawn after the release verification, a departure from addendum 1 item 1.
- **D53.** A per-row gate verdict (for example PT precision 0.80 or more, TC run-to-run 0.85 or more) may stand beside a
  share printed as "not published (misses from fewer than 5 creators)"; the exact value stays withheld.
- **D54.** Outputs with an M place are published in this release and the gallery; the paper's results section points
  to them, and its appendix B.10 cites them by id. This is a deviation: less prominent than registered.
- **D57.** No public text points to the page-text base or calls it public. D50's reason reads: the page-text base is not
  printed, because it lies fewer than 5 below 71. PT's ask-habit K4 bin is merged by the plan's rule and CROSS's K4 row
  withholds a count by the nested-count rule.
- **D58.** GRID's positional precision (its bound from window-phase counts, with the point and the interval) reads
  "not published (misses not recounted by creator)" in GRID, rv-R7, rv-D5 and the paper. nlp-R13's Chapman recalls
  near 1 stay, labelled estimated. CSS-10's model-read precision range reads "0.735 or more (precisions whose misses
  come from fewer than 5 creators are not published)".
- **D59.** The R-hold gate A and B shares read "not published (misses not recounted by creator)" in the published
  first-round file too, with a dated correction note; no verdict changes.
- **D60.** The paper's frame-only relay kappa rests on the gate sample G, which holds seen creators only; it was
  recounted by creator, passes, and is printed again. TL's files withhold the 00:30 checkability place kappa.
- **D61.** D11's negative phrase reads "agreement, not a measure of correctness" everywhere. The flag of X-E's outputs reads
  "Made after a hold-out contact on 2026-11-22 (a file read or listing that showed file names or sizes only)".
- **D62.** E3-H and H3-X print H3's hold-out base (17), not the 18 beside it. VER-SHARD's arms are named by their
  size (15, 5 or 1 units per call; 10 or 3 hits per call). TM's and CH's seen figures give topic 14 the neutral label
  of TM-H.
- **D63.** The three reviewed plain-text public files are copied into the release.
- **D64.** HOLD2's scope cuts (DC-H, SD-H, CH-H, META-H) are accepted as reported departures (R5). The deviation rows
  of the release pass's fix steps (174 to 176) are in the registry's deviation table.
- **D65.** The second fix step's content searches over the public worktree scanned no file of hold-out or other-group
  measured values (`contacts.md`): not a contact.
- **D66.** Whether H3's seen sets of 61 and 64 creators are nested with seen groups of 57 to 66 creators cannot be
  checked without a contact; it is listed with D45's pairs (addendum 3 item 9).
- **D67.** No quantile (10th to 90th percentile) is printed in a row whose creator count is withheld or printed as a
  band: CSS-10's rows over the page-text base; the rows of LAB-F, LAB-A, LAB-S, LAB-V by format, nlp-R10 and nlp-R11
  printed as "all but fewer than 5 of 71" or "withheld (within 4 of another printed count)"; META-H's rows printed
  as "5 or more" or "all but fewer than 5 of 23"; and their figures and gallery copies (nlp-R9's figure keeps its
  means). An uninterpolated quantile of creator values sits on a whole position of the sorted values, and that
  position can give the count back. Means and their intervals stay. One row of LAB-V whose quantiles could narrow
  its withheld count of creators with a non-zero value prints none either. The release scans gained a
  whole-position test. This was the fourth fix step (fix5); its deviation row is 177 in `deviations.md`.
- **D68.** Rule 8 above reads in D28's form; rx-years and TL's calendars follow it (an open earliest bin, or no year
  before 2026; every bin on 5 or more creators).
- **D69.** The gallery copy of rv-R2's power curves carries D51's label: "simulated projections, not counts of
  creators".
- **D70.** Even over a printed base, the pattern of printed zero, printed non-zero and blank quantile cells can fix
  or narrow the count of creators with a non-zero value. So no quantile (10th to 90th percentile, medians) is
  printed in a row whose count of creators with a non-zero value is withheld or printed as a band, nor in a row
  which the quantile cells alone fix to fewer than 5, to within 4 of the row's base or to within 4 of a printed
  count: quantiles were dropped where they could narrow a withheld count, in LAB-A, LAB-F, LAB-K, LAB-T, LAB-V,
  nlp-R10, nlp-R11, CSS-5, CSS-12, LAB-H, TM-H and rv-D3-H, with LAB-V's spread figure and CSS-12's census figure
  redrawn. Means, their intervals and every count stay; each changed file carries a dated note line. The release
  scans gained the independent check's two solvers (the non-zero-count solver, in its two modes, and the
  whole-release hidden-base scan). This was the fifth fix step (fix6); its deviation row is 178.
- **D72 and D73** (added 2026-11-26). E5's creator counts under H1's span rule are printed in band form; one share is no longer printed (dated correction below). The matter is
  listed among the owner's items (addendum 4, item 9).

## Limits

- **Model-coded labels, not checked by a person.** Every label-based output describes what language models coded under
  frozen instruments. Several instruments are below their reliability floor on the hold-out reliability sample, and
  relayed voice is below its floor everywhere. Agreement between models is not agreement with what was said.
- **Hold-out contacts.** Every hold-out and other-group run of the round was a logged contact, after the registered
  tests. Some contacts were logged late, some were unplanned (among them seven over-wide text searches and three file reads
  or listings of release pass 1),
  and two verifier reads were not recorded when made; [`contacts.md`](contacts.md) lists every contact, with what was
  displayed and which outputs carry "Made after a hold-out contact on <date>". No contact displayed a hold-out value in
  public, and none changed a registered verdict.
- **Deviations.** The round departs from the plan in recorded ways: code not in the freeze-2 record for hold-out
  outputs, stricter small-cell rules that withhold single cells, scope cuts, choices made after a result (labelled
  "chosen after the result"), parts not built in this release (D55) and the main-text places (D54).
  [`deviations.md`](deviations.md) gives each with its decision; the registry's deviation table holds the same rows.
- **Withheld figures.** Every withheld cell is named in the status table's `parts_not_run_or_not_released` column and in
  `deviations.md`. A withheld value is never replaced by a bound near 100%.
- **Not a sample of a field.** The cohort is a frozen roster of 101 creators chosen by a registered rule; the hold-out is
  the tail of an English-first run. The descriptions say what these creators' recordings and pages contain, not what
  the people who make them believe, intend or earn.

**Still open for the lead** (after release pass 2's fifth fix step (fix6), 2026-11-26).

- **Not recounted by creator, each withheld or no longer printed**: the R-hold gate A and B shares (a recount would be
  a hold-out contact; withheld in `built/GATES`, LAB-H and the published first-round file, D59, verdicts kept), one
  gate share on G whose misses the stored records do not attribute to creators (withheld), the rv-D5 pilot figures
  (withheld) and HOLD's pre-revision gate line (no longer printed).
- **Owner's items** (registered or published files that this release does not edit): the registry's decision row of
  2026-11-21 19:30, which quotes the R-hold voice gate A share; and the creator-count pairs that were public before
  the round, listed in addendum 3 item 9 (D45's pairs, rv-R3's 35 seen creators and one other-group creator, and
  COR's within-channel level beside the 71 seen creators).
- **Nesting not verified by member sets** (D66): H3's seen sets (61 and 64) against seen groups of 57 to 66 creators;
  a rebuild needs H3's per-recording eligibility, which sits in files that also hold hold-out rows (a contact).
- The deletion of private files with hold-out text (D10) is still to be made.

## Every output

One row per output id, from [`status-table.csv`](status-table.csv), by plan section. Status words are the plan's:
"reported", "superseded", "not run". Headlines are descriptions, not findings; each rests on 5 or more creators except
E9's hold-out part (the owner's exception). The
`files` column names the files in this folder; "gallery:" gives the figure ids in [`gallery/index.html`](gallery/index.html).

### 6.1 Paper-review build items

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| rv-D1 | What was selected, archived and transcribed, and where was each loss? | reported | M (flow, date sentence); S (rank figure, tables); W (flow counts) | Of 1,976 selected recordings of 101 creators, 1,699 were transcribed; the losses were 30 final download failures, 215 recordings set aside before the run (mostly English text of another kind, concentrated at the newest listing ranks) and 32 recordings not transcribed, most because no speech was found. | built/rv-D1/: public/rv-D1-dates.csv, public/rv-D1-flow.csv, public/rv-D1-h3-eligibility.csv, public/rv-D1-rank-odds.csv, public/rv-D1-rank-shares.csv, public/rv-D1-seen-subsets.csv, public/rv-D1-smd-missingness.csv, README.md; gallery: rv-D1-fig-1, rv-D1-fig-2, rv-D1-fig-3 |
| rv-D2 | How do the seen, hold-out and other creators differ, and how did the run order make the hold-out? | reported | M (paragraph, love plot); S (Table B, AUC, vintage) | The hold-out differs from the seen creators in language, audio edition, date evidence and run order, and fields known before the run already predict hold-out membership (cross-validated AUC 0.69 against a shuffle band up to 0.67), so the hold-out is not exchangeable with the seen creators. | built/rv-D2/: public/rv-D2-auc.csv, public/rv-D2-run-order.csv, public/rv-D2-sentences.csv, public/rv-D2-table-B-balance.csv, public/rv-D2-vintage.csv, README.md; gallery: rv-D2-fig-1, rv-D2-fig-2 |
| rv-D3 | Where does the time outside recognized speech sit? | reported | M (coverage figure); S (classes, reconciliation); W (coverage figure, seen only) | About 15% of the seen creators' audio lies outside recognized speech (12% outside the voice detector's speech), and coverage is lowest at the edges: about three quarters of the first 15 s and half of the last 15 s are covered. | built/rv-D3/: public/rv-D3-aligned-coverage.csv, public/rv-D3-classes-by-position.csv, public/rv-D3-companion-rows.csv, public/rv-D3-partial-window-by-length.csv, public/rv-D3-reconciliation.csv, public/rv-D3-share-without-speech.csv, README.md; gallery: rv-D3-fig-1, rv-D3-fig-2, rv-D3-fig-3, rv-D3-fig-4 |
| rv-D4 | What is each headline number, on which base, weighting and interval, and how did it move? | reported | M (Table U); S (Table D, provenance, consistency report) | The release's consistency test, run at release time over every release file, the README, the paper and the results README: no printed count contradicts its source (30 count checks pass), and version 1's failing rows compare files outside the release; summary in rv-D4-consistency-summary.csv (D17, D39). | built/rv-D4/: public/rv-D4-consistency-summary.csv, README.md |
| rv-D5 | What is the measurement status of each construct? | reported | M | No construct has a reference against which correctness could be measured: recognizer measures rest on between-creator reliability and the two-model bridge, every label instrument is model-coded with agreement figures only, and relayed voice, forecast checkability and title presentation fell below a gate and were merged or kept by the owner's decision. | built/rv-D5/: public/rv-D5-measurement-status.csv, README.md |
| rv-D6 | How was the design registered and then amended? | reported | M (figure); S (table) | Within three hours of the registry freeze came the H3 test, a stricter verdict rule written after its result, H3's withdrawal and three hold-out contacts; of 19 deviations from the registered text, 9 are looser. | built/rv-D6/: public/rv-D6-deviation-table.csv, public/rv-D6-timeline-events.csv, README.md; gallery: rv-D6-fig-1 |
| rv-D7 | Do the public outputs keep their privacy promises? | reported | S (counts by category and the fixes made) | The release's privacy scan, run at release time over every release file, the paper and the results README: counts by category and the fixes made are in rv-D7-scan-summary.csv; after release pass 2's fix step no cell fails the dominance screen, and every hit of a hard rule was reviewed: fixed, kept with its reason, or listed as open for the lead (D17). | built/rv-D7/: public/rv-D7-scan-summary.csv, README.md |
| rv-D8 | What was sent to external services, and how much of it was third-party speech? | reported | M (ethics table); S (by tag and date) | By 01:16 UTC on 21 November the API had received 69,442 requests carrying about 26 million words of seen creators' transcript-derived text (an estimate, with repeats), about 14% of it third-party speech in the pilot (model-coded); the paper's rerun on the whole ledger counts 396,608 requests. | built/rv-D8/: public/rv-D8-external-processing.csv, public/rv-D8-paper-full-ledger.csv, public/rv-D8-pilot-formats.csv, public/rv-D8-proposed-rule.csv, public/rv-D8-proposed-rule.txt, public/rv-D8-requests-by-category.csv, public/rv-D8-requests-by-date.csv, public/rv-D8-requests-by-run-tag.csv, public/rv-D8-third-party-share.csv, README.md; gallery: rv-D8-fig-1, rv-D8-fig-2 |
| rv-R1 | What does H3 show at the creator level? | reported | M (H3 table, results-table wording); S (figures a-d); W (results row wording) | At the creator level H3 is not determined: on the 17 hold-out creators the 90% t interval of the registered contrast includes zero and 9 of 17 are positive, the registered rule says 'supported' 1.3 to 1.6% of the time under a creator-level null (nominal 0.5%), and on the 61 seen creators the recentred contrast is 0.083 with an interval that includes zero. | built/rv-R1/: public/rv-r1-h3-creator-level.csv, public/rv-r1-h3-seen-beside-cal.csv, public/rv-r1-u-histogram.csv, public/rv-r1-u-percentiles.csv, public/rv-r1-placebo-p.csv, public/rv-r1-recentred-u-by-trim.csv, public/rv-r1-first-person-15s.csv, public/rv-r1-power-simulation.csv, public/rv-r1-dashboard-row.csv, README.md; gallery: rv-R1-a, rv-R1-b, rv-R1-c, rv-R1-d |
| rv-R2 | Can each registered rule reach a verdict at the eligible numbers of creators? | reported | M (table, eligibility dot plot); S (power curves, plasmode, type S and M) | At the projected numbers of eligible hold-out creators H1, H4 and H6 cannot pass the first Holm step and H5 probably cannot, H2's registered within-creator reference rejects about 14 times too often, and under persistent creator effects a wave of the same creators passes a null 9 to 22 times too often while fresh creators stay near nominal. | built/rv-R2/: public/rv-r2-calibration-eligibility.csv, public/rv-r2-projected-eligible.csv, public/rv-r2-power-curves.csv, public/rv-r2-type-sm.csv, public/rv-r2-plasmode.csv, README.md; gallery: rv-R2-a, rv-R2-b, rv-R2-c |
| rv-R3 | What do the two recognizer models agree on, for which uses? | reported | M (interval plot, verdict table); S (Bland-Altman panels, class disagreement); W (bridge card) | On the same English audio the two recognizer models agree within 0.2 between-creator SD on 7 of the 17 measures (pace, pronoun and contraction rates, word length, vocabulary variety), differ on 6 (word timing, pauses, segment length, filled pauses) and leave 4 not settled; agreement of two machines, not an error rate. | built/rv-R3/: public/rv-r3-bridge-verdicts.csv, public/rv-r3-verdict-tallies.csv, public/rv-r3-interval-plot.csv, public/rv-r3-bland-altman.csv, public/rv-r3-class-disagreement.csv, public/rv-r3-confusion-profile.csv, public/rv-r3-mattr-logprob.csv, public/rv-r3-seen-sds.csv, README.md; gallery: rv-R3-a, rv-R3-c, rv-R3-d |
| rv-R4 | Do the headlines survive other weightings and windows? | reported | S; M (one sentence per headline) | Pace and the share of time without speech stay within their pre-set margins under almost every weighting and window (2 and 3 of 40 specifications beyond), while the thanks-phrase and term-cue shares rise when recordings are weighted by hours. | built/rv-R4/: public/rv-r4-summary.csv, public/rv-r4-specifications.csv, public/rv-r4-span-bins.csv, public/rv-r4-span-loess.csv, public/rv-r4-posting-rate.csv, README.md; gallery: rv-R4-a, rv-R4-b, rv-R4-c |
| rv-R5 | How is each measure's variance split between and within creators? | reported | M (Table VP-1, ICC figure); S (shrinkage densities, checks); W (ICC figure) | Between about a fifth and three quarters of a measure's variance lies between creators (pace 0.58, contractions 0.72, mean ln word probability 0.21), and the creator-bootstrap intervals are up to 3.6 times wider than the parametric ones. | built/rv-R5/: public/rv-r5-vp1.csv, public/rv-r5-icc.csv, public/rv-r5-icc-scale.csv, public/rv-r5-pace-shrinkage.csv, public/rv-r5-table7-check.csv, README.md; gallery: rv-R5-a, rv-R5-b |
| rv-R6 | How much recognition error can each word-based measure tolerate? | reported | M (tolerance figure); S (table, scenarios) | The same simulated recognition error for every creator leaves pronoun, contraction and question-mark rates within 0.2 between-creator SD up to 20%, moves word length and MATTR at about 4 to 5% and filled pauses at about 5%, and error that differs between creators can create a correlation of word length and MATTR with silence; a tolerance, not a measured error rate. | built/rv-R6/: public/rv-r6-tolerance.csv, public/rv-r6-injection-curves.csv, public/rv-r6-creator-error.csv, README.md; gallery: rv-R6-a, rv-R6-b |
| rv-R7 | Where do the recognizer's inserted phrases and seams sit, and how good are the rules that remove them? | reported | M (figure, rule table, abstract sentence); W (artefact card) | A two-word thanks phrase starts in the last 3 s of a 30-s decoding window in 2.3% of windows full of speech, 50 to 150 times as often as in any earlier 3-s stretch, and appears in half of the English transcripts; a positional rule removes it (its precision bound from phase counts: not published (misses not recounted by creator)). | built/rv-R7/: public/rv-r7-artefact-rules.csv, public/rv-r7-thanks-by-phase.csv, public/rv-r7-prevalence-and-seams.csv, public/rv-r7-segment-start-phase.csv, public/rv-r7-onset-density.csv, public/rv-r7-abstract-sentence.csv, public/rv-r7-abstract-sentence.txt, README.md; gallery: rv-R7-a, rv-R7-b |
| rv-L1 | What kinds of recordings do the channels publish (interim probability sample of development creators)? | superseded | M (kinds table); S (stacked bars); W (kinds distribution) | In the interim sample of 96 recordings of 48 development creators, own-voice talks and a channelled voice were the commonest main kinds of a creator's recordings, and under both models about a third of a creator's recordings had a claimed voice in half or more of their words; rv-L1 is superseded as the census by LAB-K and printed beside it. | built/rv-L1/: public/rv-l1-agreement.csv, public/rv-l1-creators-without-a-claimed-recording.csv, public/rv-l1-kinds-and-bands.csv, README.md; gallery: rv-L1-fig-1, rv-L1-fig-2 |
| rv-L2 | How much does the recognizer move the labels? | reported | S | Changing the recognizer added no detectable instability to the voice labels (all labels: between-transcript minus run-to-run flips -0.025, 90% interval -0.083 to 0.021, on 25 bridge pairs); for asks rv-L2 finds no firm recognizer effect, a possible effect not ruled out. | built/rv-L2/: public/rv-l2-asks-unit-rule-withdrawn.csv, public/rv-l2-label-flips.csv, public/rv-l2-where-flips-sit.csv, README.md; gallery: rv-L2-fig-1 |
| rv-L3 | How many windows hold non-language or pseudo-words? | reported | S | Two models read about half to three fifths of the flagged windows as non-language or pseudo-words (0.52 and 0.59; model-read), mostly in the 10 creators with 10 or more flagged windows (0.68 and 0.75) and far less elsewhere; no unflagged window of 200 was read as non-language, so recall is not established. | built/rv-L3/: public/rv-l3-flag-counts.csv, public/rv-l3-lexical-with-without.csv, public/rv-l3-precision-by-creator-load.csv, public/rv-l3-precision-by-oov-band.csv, public/rv-l3-precision.csv, README.md; gallery: rv-L3-fig-1 |

### 6.2 Second-round programme, built part

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| TABLE | What is known about each recording outside its transcript, at which evidence level? | reported | S; M via rv-D1 | Of 1,411 selected recordings of the 71 seen creators, 1,176 reach the text-analysis base, and all 71 creators remain at every step (census counts, no interval); local time stamps confirm most estimated publication days among the newest uploads: the estimated share of listing ranks 1-5 falls from 35% to 16% (all 101 creators' publication dates, no group split; 90% creator-bootstrap intervals). Exploratory; not a test of H1-H10. | gallery: TABLE-1, TABLE-2 |
| CAL | Are the remaining registered rules centred, calibrated at the creator level, covering and powered? | reported | M via rv-R2; S (full tables, p histograms) | Under creator-level placebos drawn from the seen creators, the registered tests of H2, H3 and H6 reject 2.3 to 15 times too often at the first Holm step while creator sign-flip tests stay near the nominal 0.5% (95% Monte Carlo intervals); only the t interval on creator means keeps close to 90% coverage (0.885 to 0.915); at 12 to 17 creators a creator-level sign-flip reaches 80% power only for effects 0.8 to 1.8 times the smallest effect of interest, and H3's recentred contrast needs 6 to 8 times. Calibration on label-free analogues (the H6 simulation uses model-coded pilot labels, not checked by a person); exploratory, not a test of H1-H10. | gallery: CAL-1, CAL-2, CAL-3 |
| RX | Which countable wording patterns separate creators and positions in a recording? | reported | S; W (family-level distributions) | Wording-pattern rates differ over a hundredfold between sub-patterns (creator-equal means, 90% t intervals); most split-half reliability estimates of creator rates reach 0.70, but most of their 90% creator-bootstrap intervals dip below it; greetings and introductions crowd the first tenth of a recording and sign-offs and asks the last (pointwise 90% creator-bootstrap bands, no family-wise control); 2026, 2020 and 2027 are each named by about half of the seen creators (census of creators, no interval; earliest years pooled into one open bin, D28). Cue counts until their precision is known; exploratory, not a test of H1-H10. | gallery: rx-rates, rx-position, rx-years |
| GRID | How much of each timing measure does the 30-s decoding grid make, and how right is each filter rule? | reported | M via rv-R3 and rv-R7; S | The 30-second decoding grid makes about 3% of the pauses between words and 2.5% of pause time; four in five stand-alone two-word thanks segments start in the last 3 seconds of a decoding window, and the share of the filter's removals that are recognizer insertions, bounded from phase counts, is not published (misses not recounted by creator); dropping every pause that spans a seam lowers pause-measure means by up to 0.41 creator SD, while the capped, weighted rule (primary) moves them by 0.14 SD or less and keeps creators' rank order (90% t intervals). Exploratory; not a test of H1-H10. | gallery: GRID-1, GRID-2, GRID-3 |
| DC | Inside the weeks and months a channel covers, are recordings close in time more alike? | reported | S; W (lag curve) | Inside a channel's own span, recordings uploaded within about two weeks of each other share more vocabulary than recordings further apart, with peaks at whole weeks; the pre-specified primary (0-7 against 31-183 days) is +0.037 (90% t interval 0.022 to 0.051; 56 seen creators) and holds on both confirmed date versions, without same-day pairs and on same weekdays; only recording length changes along a channel's span beyond a family-wise check, with directions split. Upload date, not date of speaking; not a trend of the field; exploratory, not a test of H1-H10. | gallery: DC-fig-1, DC-fig-2, DC-fig-3, DATES-1, DATES-2, DATES-3 |
| SD | How often do channels publish on the same date beyond quota and weekday habits, and are such recordings more alike? | reported | S; W (excess by band; calendar strip as in section 3) | Channels upload on the same dates about as often as their own weekly habits predict (ratio 0.98, 90% creator bootstrap 0.95 to 1.01; all creators with a confirmed upload date in any group, dates only, no group split; seen only in the figure); different channels' recordings from the same few days share almost no extra vocabulary (+0.0010, 90% t interval -0.0009 to +0.0030), although a calendar-word control shows that such a signal can be seen; at month scale estimated-date recordings are more alike than shuffled dates give, but this cannot be told apart from each channel's own drift. UTC upload dates; never read as contact, coordination, copying or influence; exploratory, not a test of H1-H10. | gallery: SD-fig-1, SD-fig-2, SD-fig-3, DATES-1, DATES-2, DATES-3 |
| CM | Do topics and measures move together across channels by month? | reported | S | No month measure is interpretable under the programme gate: the calendar-word control fails in every month panel under the primary admission rule (F25, chosen after the first run's result), and no word or pattern measure's month-to-month change stands out from shuffled months under either admission rule, apart from one first-run version-A pass that is withdrawn because its panel's calendar-word control failed (permutation maximum; 90% creator-bootstrap intervals). Movement within each channel's own span, never a trend of the field; exploratory, not a test of H1-H10. | gallery: CM-fig-1, CM-fig-2, DATES-1, DATES-2, DATES-3 |
| TM | Which recurring vocabulary clusters are reproducible, and how is each channel's talk spread over them? | reported | S; W (topic table with neutral labels) | Sixteen recurring vocabulary clusters cover the seen channels' talk, but only three reappear in every refit; two channels' topic mixes almost always differ more than one channel's two halves (median distance ratio 2.47), the dominant topic of a window carries channel identity far beyond shuffles, and topic shares shift with position in the recording (pointwise intervals; no family-wise control). Topics are vocabulary clusters with analyst-written labels not checked by a person, never beliefs; 90% creator-bootstrap intervals; exploratory, not a test of H1-H10. | gallery: TM-fig-1, TM-fig-2, TM-fig-3 |
| CH | How is each measure distributed across and within channels, and do patterns, topics and words tell the same story? | reported | S | Channels differ: in every family of measures a third to over half of the typical measure's variation lies between channels, most for topics (family medians 0.34 to 0.55; reliability of a creator mean 0.82 to 0.99); a channel's two halves are far more alike than the halves of two different channels; channels do not fall into stable groups (only a fragile two-group topic split clears the 0.75 stability rule); and how many days a channel's recordings span says little about its measures. 90% creator-bootstrap intervals; RX rates are cue counts; topic labels are analyst-written, not checked by a person; exploratory, not a test of H1-H10. | gallery: CH-fig-1, CH-fig-2, CH-fig-3, TOPICS-fig-3 |
| COR | Which measures go together across channels, which within a channel, and where do the levels differ? | reported | S; W (heat map) | Measures that go together across channels mostly go together inside a channel too, but about half as strongly: of 276 pairs, 19 pass the family-wise threshold across channels (three of them fragile), 75 inside channels and 16 at both, none with opposite signs; 10 of 23 measures go with recording length inside channels and none across; recognized words per minute (a recognizer-output measure, not a direct measure of speaking) and time without speech go together at both levels, while recognizer confidence follows words per minute only weakly (0.10 inside channels, beyond the family-wise threshold of 0.078; 0.11 across channels, where the interval crosses 0). Permutation-maximum thresholds; 90% creator-bootstrap intervals; RX rates are cue counts; exploratory, not a test of H1-H10. | gallery: COR-1, COR-2, COR-3, TOPICS-fig-1, TOPICS-fig-2 |
| META | How do channels schedule and size uploads, and what goes with more views inside a channel? | reported | S; W (rhythm distributions only) | A typical channel uploads about once a week and many favour one weekday (all 101 creators' publication dates and durations, no group split; census, no interval); captured page metadata covers 87% of a seen channel's uploads on average and 14% carry creator-written chapters (90% creator-bootstrap intervals); within a channel few recording properties went with audience counts at capture: three cells pass their family-wise band, and longer recordings went with more views and older ones with fewer (90% intervals; one snapshot, nothing causal; title and speech properties are cue counts, written asks model-coded and not checked by a person). Exploratory; not a test of H1-H10. | gallery: META-1, META-2, META-3 |
| PT | What does the page around a recording declare and ask for? | reported | S; W (ask-class shares) | Other-platform, event and course cues are the most common page cues, and course, event and shop cues miss the 0.80 precision gate; written asks are on most pages, much of their text is a repeated channel template, and many channels put the same kind of ask on all or most of their pages. Written asks are model-coded, not checked by a person (run-to-run kappa on any ask 0.96); 90% t intervals on creator means, Wilson 95% intervals for precision; exploratory, not a test of H1-H10. | gallery: pt-page-cues, pt-written-asks, pt-ask-habit |
| NAMES | Which word forms spell the same being, collective or place, and how much do stems and masks miss? | reported | S | Variant spellings carry 29% of the mentions of named collectives, against 6% for beings and 15% for places; exact spellings find a fifth to two-thirds of each star-people family's mentions, and the round-1 stem patterns do about as well (57% and 58% of 2,419 mentions); a capital-letter mask leaves 22% of those families' mentions, and a mask built only from the names list leaves most own-name introductions, which the released names-mask v2 removes by design. Families are model-coded by two models, not checked by a person; 95% creator-bootstrap intervals; exploratory, not a test of H1-H10. | gallery: NAMES-fig-1, NAMES-fig-2, LEXICON-fig-3 |
| TIME | What are dates and time expressions used for, and how far ahead do forecast-role years lie? | reported | S | About one time expression in seven (0.14) is model-coded as a forecast, and the share depends on the model (on the same 600 hits, pooled forecast shares of 0.14 for the small model and 0.10 for the middle model; kappa 0.65); schedule talk rises at the opening and the close; most years named in a forecast role lie in the year of publication or the four years after (76% for the average creator, 90% interval 68% to 83%). Model-coded, not checked by a person; a mention in a forecast role is not a prediction made or come true; exploratory, not a test of H1-H10. | gallery: time-roles, time-position, time-horizon, LEXICON-fig-2 |
| RXP | How often is a pattern hit what its name says, and how much do the patterns miss? | reported | S | 9 of 25 wording patterns clear the 0.80 precision gate under both weightings (17 when read hits are weighted by creators' hits, the primary chosen after the result), 2 fall below 0.60, and one revision brings platform asks to the gate on fresh hits; the patterns miss most of what a model reader finds, except offers and asks (about half). Model-read precision and recall, not checked by a person; 95% creator-bootstrap intervals; exploratory, not a test of H1-H10. | gallery: rxp-precision, rxp-revisions, rxp-recall, LEXICON-fig-1 |
| TC | In codes that mean the same for every channel, what share of talk is each subject and segment kind? | reported | S | Most model-coded topic codes miss the frozen run-to-run floor (2 single codes and 4 merged groups pass under reading A, the reading that stands), so stage 2 was not bought; the stop decision hangs on how the gate is read (6 codes pass as run, 14 under the programme's wording), and two models differ on a window's topic mix by about two-thirds as much as two creators' windows differ. Model-coded, not checked by a person; agreement between models, not a check by a person; 90% creator-bootstrap intervals, noise floors as quartiles pooled over window pairs; exploratory, not a test of H1-H10. | gallery: tc-agreement, tc-gate-readings, tc-noise-floor, codes-coverage |
| NE | Which being or group does a recording present as speaking, and do channels refer to the same datable events? | reported | S | In the 200-window pilot both models find a named source in about 7 of 10 windows (window kappa 0.71), but they split on datable outside references (kappa 0.55): the small model lists 3.4 times as many as the middle model, most of which only it lists. Model-coded, not checked by a person; claims reported as claims; agreement between models; 90% t intervals on creator means; exploratory, not a test of H1-H10. | gallery: ne-pilot-shares, ne-model-entries, codes-coverage |
| DIR | Do recordings tell listeners what to do about health, money, preparation or practice? | reported | S | In the 200-window pilot, after the critic, practice directives appear in about half of a creator's sampled windows and other classes are rarer; the keyword prefilter catches about 4 in 10 of the middle model's directive and threat entries (0.415 pooled), far below the 0.70 required, so the go rule failed and the full pass was not run; after the verifier's finding the headline moved to equal weight per creator (values shift by at most 0.06; the no-go stands). Model-coded, not checked by a person; 90% t intervals on creator means; exploratory, not a test of H1-H10. | gallery: dir-incidence, dir-prefilter-recall, codes-dir-estimand, codes-coverage |
| KA | Do the labellers respond to what their codebooks admit, and not to register or the context of an ask? | reported | M (verification figures per instrument, via rv-D5 and LAB); S (full tables) | On constructed texts the labellers recover 60% to 100% of planted answers, an upper bound because planted texts are cleaner than real speech, and relayed forecasts stay among the weakest after the critic's revision (74% small model, 83% middle); deleting the cited cue moves the voice label (small model -14 points, middle -4), changes the codebooks ignore move point estimates by 6 points or less, but their intervals reach 16 points and two exclude zero, and voice revision 3 with its label variant raised the small model's recovery by 14 to 18 points on framed texts. Model-coded, not checked by a person; 90% bootstrap intervals over creators; shares whose misses come from 1 to 4 creators are not published; exploratory, not a test of H1-H10. | gallery: KA-1, KA-2, KA-3 |

### 6.3 Second-round programme, parts not yet run

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| HUMAN | How often are the voice labels right when judged by a person? | not run | S (status table) | Not run: no person checked any label (owner's decision A8). | - |
| CAL-f | How many creators are eligible for each within-creator contrast, and do the calibration results hold on labels? | reported | M via rv-R2; S | On seen labels about two thirds of the seen creators meet the frozen eligibility rules for H1, H4 and H6, and more for H2; this lies between the two projection bounds onto the English hold-out creators, a post hoc check and not a forecast; on seen labels only H6's registered half-count statistic is off-centre (model-coded, not checked by a person). | packages/CROSS/: cal-f-eligibility.csv, cal-f-null-centre.csv, README.md; gallery: CAL-f-fig-1, CAL-f-fig-2, CAL-f-fig-3 |
| PT-cd | Do written and spoken asks coincide, and do creator-written chapters mark structural changes? | reported | S; W (paired ask-class shares) | Pay-or-enrol, money and off-platform asks are written on the page more often than they are said in the recording (their paired creator-level intervals exclude zero), platform-engagement asks differ little (its paired interval includes zero), and inside a creator a recording with a written ask carries a spoken ask of the same class more often than within-creator permutation allows for every class with enough creators; creator-written chapter starts sit at claimed-voice boundaries no more often than shifted starts in the small middle-model subset, and more often under the small model's labels (model-coded, not checked by a person). | packages/CROSS/: pt-c-written-spoken.csv, pt-d-chapters.csv, README.md; gallery: PT-cd-fig-1, PT-cd-fig-2, PT-cd-fig-3 |
| RX-CB | Do framing cues sit at model voice boundaries? | reported | S | Framing-cue hits lie much nearer to model claimed-voice boundaries than circularly shifted hits (above the shift band at every printed distance: at 5 and 20 s in the middle-model subset, whose later points rest on too few creators to print, and up to two minutes under the small model) while placebo-list hits stay inside their band, and a cue opens only a small share of claimed-voice spans, though more than shifted hits do (cue counts; model-coded boundaries, not checked by a person). | packages/CROSS/: rx-cb-curve.csv, rx-cb-spans-opened.csv, README.md; gallery: RX-CB-fig-1, RX-CB-fig-2 |
| MTMM | Does agreement within a construct across methods exceed agreement across constructs within a method? | reported | S; M (one sentence per construct) | For voice, source family and asks, agreement within a construct across methods exceeds agreement across constructs, so all three pass the convergent and discriminant checks; but source family's pass rests mainly on three methods that read only titles (median convergent rho 0.44 over the method pairs that cross inputs, against 0.68 over all pairs), the two model cells of voice and of asks read the same inputs, voice and source family overlap substantially, and the subject construct was not run (agreement between methods, not a human check). | packages/CROSS/: mtmm-matrix.csv, mtmm-summary.csv, mtmm-pass-list.csv, README.md; gallery: MTMM-fig-1, MTMM-fig-2 |
| NE-F | NE full pass | not run | S | The NE full pass was not run because it needs model calls and no money is left under the hard stop; on the pilot windows, every released row names a source in far more than 30% of claimed-voice windows (model-coded, not checked by a person). | packages/CROSS/: ne-f-30pct-criterion.csv, README.md |
| TC-2 | TC stage 2 and the TC-code rows of DC, SD, CM, CH and COR | not run | S | Not run: TC stage 2 was not bought. | - |
| HR | Do the hold-out results of H6 and, where released, H2 hold under every reading, a second coder and rewordings? | not run | M (beside the registered rows); S | Not run: the hold-out robustness rows need model calls that were not bought. | - |
| NONEN | Which topic and source codes survive translation, and where do the non-English creators sit? | not run | S | Whether topic and source codes survive translation was not measured: the codes need model calls the budget no longer allows, and the code-only translation counts could not first be run on seen creators. | packages/HOLD/: hold-README.md |

### 6.4 ENTRY

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| ENTRY-E4 | How common is a found entrance? | reported | S; W (binned distribution) | The ENTRY patterns (version 1, of record) find a first entrance cue in about 9% of a seen creator's recordings (creator-balanced; 90% two-stage bootstrap interval 5% to 12%) and in none for most creators; version 2, revised after the model check, gives a similar share. Cue counts: by the model check (model-coded, not checked by a person) the rule finds at most about a fifth of entrances, so entrances as the model readers code them are more common. Exploratory; not a test of H1-H10. | gallery: entry-how-common |
| ENTRY-E1 | When does the source enter? | reported | S; W | First entrance cues come early in a recording: under version 1 the creator-balanced median position is about a seventh of the running time (median 3.0 minutes; 90% two-stage bootstrap interval), and version 2's supported tier, defined after the result, sits earlier (median 0.6 minutes). Cue counts; the model check (model-coded, not checked by a person) found that most late cues are not where speech presented as a source's begins. Exploratory; not a test of H1-H10. | gallery: entry-where |
| ENTRY-E2 | Where in a recording does each cue family sit? | reported | S; W | Handover and greeting cues peak in the first tenth of a recording and leave-taking cues in the last (hits per 1,000 words by tenth of running time, means over the 71 seen creators; pointwise 90% two-stage bootstrap bands, no family-wise control; adjacent tenths merged until 5 or more creators have a hit); the presenter's own introduction is the negative control. Cue counts; exploratory, not a test of H1-H10. | gallery: entry-where |
| ENTRY-E3 | What changes at the entrance? | reported | S | Around the first entrance cue, first- and second-person rates and recognized words per minute (a recognizer-output measure, not a direct measure of speaking) show no clear change: every 90% two-stage bootstrap interval of the 10 minutes after against before includes zero, under version 1 and version 2. Cue counts; the model check (model-coded, not checked by a person) found that most of these cues are not where speech presented as a source's begins, so this describes what surrounds a cue. A description, not a finding; exploratory, not a test of H1-H10. | gallery: entry-around-cue |
| ENTRY-T | Which cue templates and which persons go with which source groups? | reported | S | In each source group shown, about 34% to 51% of a creator's self-introductions use 'we' rather than 'I' (creator-balanced, 90% creator-bootstrap intervals; groups with fewer than 5 creators pooled as 'other'); the split largely restates how the lexicon groups are built. Cue counts; the NAMES list is model-coded, not checked by a person; exploratory, not a test of H1-H10. | gallery: entry-t2-i-we-by-source-group |
| ENTRY-MC | Are the patterns and the entrance rule right, by model readers? | reported | S | By two model readers, with a third model adjudicating their disagreements, 'we' self-introductions, handovers and the presenter's own introductions are mostly what they claim, greetings are weak, and the first-entrance rule finds at most about a fifth of the entrances the readers code (recall upper bound 0.21). Model-coded, not checked by a person; agreement among models; 90% two-stage bootstrap intervals; exploratory, not a test of H1-H10. | gallery: entry-model-check |
| ENTRY-V2 | What does the revised version change? | reported | S | Version 2 of the ENTRY patterns and rule, revised after the model check and shown beside version 1 as in-sample revision rows, changes no reading: it finds a first entrance cue in a similar share of recordings (about 8%, against about 9%), places first cues earlier, and leaves the change around the cue unclear; its supported tier was defined after the result. Cue counts; the model check is model-coded, not checked by a person; 90% two-stage bootstrap intervals; exploratory, not a test of H1-H10. | gallery: entry-how-common, entry-where, entry-around-cue, entry-t2-i-we-by-source-group |
| ENTRY-H | The ENTRY outputs on hold-out creators | reported | S | Entrance cues appear in a small share of hold-out recordings, as on the seen creators; they are cue counts whose seen model check found most such cues are not where a source begins, and most version-2 and position cells are withheld because they rest on, or differ from version 1 in, fewer than 5 creators. | packages/HOLD/: entry-h.csv, hold-README.md; gallery: ENTRY-H-fig-1, ENTRY-H-fig-2, ENTRY-H-fig-3 |

### 6.5 Verification layer

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| GATES | Which instrument gates were met, and what did each revision change? | reported | M (summary in rv-D5); S (full table) | The claimed, own and other voice met its agreement gates on the gate sample and on R-hold (relayed voice failed and was merged into claimed voice); forecast checkability and title presentation failed and were kept as records by the owner's decision, and on R-hold the forecast class of record (kappa 0.507 against 0.60) and the sentence codes' stability (0.816 against 0.85) fell below their floors. | built/GATES/: public/GATES-gates.csv, README.md; gallery: GATES-fig-1 |
| VER-A | Where the two cheap readers split, how does a blind third reader side? | reported | S | Where the two cheap readers split, a blind third model of the same vendor gave the middle model's label on about half of the disputed words (0.49, 90% 0.25 to 0.81), the small model's on about a third and neither on about a sixth; gate VG-4 fails. | built/VER-A/: public/ver-a-cost.csv, public/ver-a-labels-round2-reference.csv, public/ver-a-sides-on-disputed-words.csv, public/ver-a-verdicts-gates-constructed.csv, README.md; gallery: VER-A-fig-1 |
| VER-GC | Does the published free-text guided form beat the typed form? | reported | S | The published free-text guided form did not beat the typed form on any of the three instruments (forecast class, forecast commitment, ask check): under the rule fixed before any call the typed form stays and the guided form is multiverse row M9. | built/VER-GC/: public/ver-gc-forms.csv, README.md; gallery: VER-GC-fig-1 |
| VER-SHARD | Do smaller shards recover planted decisions better at acceptable cost? | reported | S | Smaller shards changed neither planted recovery nor run-to-run stability beyond the rule's thresholds for the sentence codes, the forecast checkability parts and TIME's roles, so the current shard sizes stay. | built/VER-SHARD/: public/ver-shard.csv, README.md; gallery: VER-SHARD-fig-1 |
| VER-3R | Does a reader of another vendor, reading blind, agree with the OpenAI readers? | reported | M (one line beside H1, H4 and H6 and in rv-D5); S | A reader of another vendor, reading blind, agreed with the OpenAI readers' majority on claimed, own and other voice at kappa 0.91 (90% 0.84 to 0.95; 200 units of 23 check creators), so gate VG-6 passes; the third model of the same vendor agreed with the same majority at 0.79. | built/VER-3R/: public/ver3r-disagreement-cells.csv, public/ver3r-gate-and-sensitivity.csv, public/ver3r-latent-class.csv, public/ver3r-reader-pairs.csv, public/ver3r-reader-profile.csv, public/ver3r-strata-and-packets.csv, README.md; gallery: VER-3R-fig-1 |
| VER-ADJ-G | The third reader on the check-creator gate samples | not run | S | Not run: the third-reader pass on the gate samples needs model calls, and no money is left under the hard stop. | packages/VER/: ver.md |
| VER-ADJ-H | The third reader on the hold-out reliability sample | not run | S | Not run: the third reader on R-hold needs model calls. | - |
| VER-DEP | What do three or more readers imply about shared errors? | reported | S; M (bounds beside the registered rows) | On the voice sample of seen check creators, four readers of four models count for fewer than two independent votes (heuristic; their all-same share is not published, as VER-3R's joint audit withholds it); the two OpenAI models' errors on constructed items are substantially correlated (phi about 0.5); a three-group correction for asks reached a boundary and is not informative. | packages/VER/: ver-dep.csv, ver.md; gallery: VER-DEP-fig-1, VER-DEP-fig-2 |
| VER-CAL | Does stated confidence track known answers? | reported | S | On constructed known-answer items the models stated confidence near the top of the scale for every instrument (mean 0.96 to 0.99), which tracked agreement with the constructed answer only roughly; for the small model, voice labels on which two runs split agreed with the constructed answer far less often than those on which the runs agreed. | packages/VER/: ver-cal-summary.csv, ver-cal-bins.csv, ver.md; gallery: VER-CAL-fig-1, VER-CAL-fig-2 |
| DR-2 | How often does a second, other model agree on forecast candidates and sentence units? | reported | S | A second OpenAI model agreed with the record on the sentence-code groups (kappa 0.79) and on the time-window, named-actor and observable-outcome parts of checkability (kappa 0.69 to 0.79); place and quantity are too rare on this sample to publish. | packages/VER/: dr2-views.csv, dr2-codes.csv, dr2-confusion.csv, ver.md; gallery: DR-2-fig-1 |
| VER-MV | Every multiverse row and the tipping-point table for every registered hypothesis that runs | reported | M; S | Every robustness row the frozen code computed for the six registered hypotheses is listed in the published results and every verification row M1 to M13 is accounted for, most as not run; the tipping-point tables are not released because no registered result was determinable or run. | packages/VER/: ver-mv-rows.csv, ver-mv-crosswalk.csv, ver.md; gallery: VER-MV-fig-1, VER-MV-fig-2 |
| VER-NEXT | Rerun of the frozen hold-out pipeline on the next model snapshot | not run | S | Not run: unfunded. | - |

### 6.6 Prediction timeline

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| TL-P | Does the timeline pipeline work? | reported | S | The timeline pipeline ran end to end on the pilot set: none of the 172 cards of bounded statements (21 creators) was resolvable as worded, analysis 7.1 had no eligible channel, 7.2 was a dry run below its minimum, and the resolver failed its known-answer gate (1 of 8 items matched). | built/TL-P/: public/tl-p-pilot.csv, README.md; gallery: TL-P-fig-1 |
| TL-BUILD | What is dated, how, and for when? | reported | S; M (one paragraph); W (counts only) | Among the seen creators' kept world-future statements (model-coded, not checked by a person), about 27% carry a bounded time expression; closed windows lie a median of about 69 days after the upload day and about three quarters within a year; pooled over statements, about 64% of dated statements take their window from the talk-level period rather than from their own words (about 53% when each creator counts equally); titles announcing a deceased person or a higher self come from too few creators to be shown apart. | packages/TL/: tl-build-lanes.csv, tl-build-classes.csv, tl-build-measures.csv, tl-build-status.csv, tl-build-year-flags.csv, tl-build-composition.csv, tl-build-calendar.csv, tl-build-source-types.csv, README-TL.md; gallery: TL-BUILD-fig-1, TL-BUILD-fig-2, TL-BUILD-fig-3, TL-BUILD-fig-4, TL-BUILD-fig-5, TL-BUILD-fig-6, TL-BUILD-fig-7 |
| TL-SPEC | How many statements are resolvable as worded, and why not? | not run | S; M (resolvability shares) | Not run: resolvability as worded needs the blind card writer and its second reader, which need model calls, and no money is left under the hard stop. | packages/TL/: README-TL.md |
| TL-7.1 | Do horizons recede within a channel? | reported | S | In the channels eligible under the protocol rule with confirmed upload days, the targets of absolute windows moved about one day later per day of upload (pooled slope about 1.0, 90% interval 0.38 to 1.50, above the within-channel permutation band): closer to a constant lead than to fixed targets in the primary, while the row pooling confirmed and estimated upload days has a wide interval (about -2.3 to 1.5) and the estimated panel alone has too few eligible channels; described within each channel's span. | packages/TL/: tl-7-1-receding-horizons.csv, README-TL.md; gallery: TL-7.1-fig-1 |
| TL-7.2 | Do channels point to the same narrow future windows beyond the calendar? | reported | S | The positive control was too small to show its excess, so cross-channel overlap of narrow future windows is not read as shared attention beyond the calendar; the main count lies inside the horizon-preserving redraw reference and above the circular-shift reference; the analysis within event clusters was not run (needs model calls). | packages/TL/: tl-7-2-convergence.csv, README-TL.md; gallery: TL-7.2-fig-1 |
| TL-7.3 | Do channels restate, postpone or advance their own predictions? | not run | S | Not run: restated, postponed and advanced predictions need event clusters confirmed by two models, which need model calls, and no money is left under the hard stop. | packages/TL/: README-TL.md |
| TL-7.4 | Do specificity and hedging change with horizon? | reported | S | Within creator, no clear difference shows between windows more than a year ahead and nearer ones in the shares of statements coded with an observable outcome, a quantity or commitment (and, over all closed windows, a named actor): 7 of the 10 cells are released and every released 90% interval includes zero, though the commitment intervals still allow differences of more than 10 percentage points; the place cells and one named-actor cell are not released because one band's YES codes come from fewer than 5 creators. (Wording changed after the release review of the plotting pass, 2026-11-22: 'differ little' claimed more than the intervals show.) | packages/TL/: tl-7-4-specificity-by-horizon.csv, README-TL.md; gallery: TL-7.4-fig-1 |
| TL-7.7 | How many dated statements take their window from a talk-level period? | reported | S | With confirmed upload days, about 65% of dated statements (about 54% creator-equal) take their window from the talk-level period alone (both panels together about 64%, 53% creator-equal), and the share differs between the merged upload months without a steady direction inside the months covered. | packages/TL/: tl-7-7-frame-share-by-month.csv, README-TL.md; gallery: TL-7.7-fig-1 |
| TL-7.8 | Do three methods of time-window measurement agree? | reported | S | At the creator level the four time-window readings agree with one another (Spearman about 0.66 to 0.96) far more than with the hedging or condition readings (about -0.21 to 0.00), but the FC-FE and rule-FE cells are partly by construction (FE ran only where the FC time part, the rule or FB's time expression called for it); on the statements where FE was due the time cells are about 0.45 to 0.92; at the statement level the FC and FE readings agree well (kappa 0.79) while the TIME_RE rule agrees only weakly with either (about 0.27 to 0.30); agreement, not a measure of correctness. | packages/TL/: tl-7-8-mtmm-rows.csv, tl-7-8-statement-agreement.csv, README-TL.md; gallery: TL-7.8-fig-1, TL-7.8-fig-2, TL-7.8-fig-3 |
| TL-7.9 | When do pending windows become checkable? | reported | S | Of the pending closed windows, the largest group becomes first checkable in January 2027 (mostly windows ending in December 2026), and the rest spread thinly over later years; when outcomes would become observable is described, never whether they occur. | packages/TL/: tl-7-9-due-calendar.csv, README-TL.md; gallery: TL-7.9-fig-1 |
| TL-RES | Resolution of passed windows by a model with web search, with placebo windows | not run | S (status table) | Not run: the study never asks whether a prediction came true. | - |
| TL-H | The timeline outputs on hold-out creators | not run | S | Not run: its precondition, a timeline procedure freeze before the seen timeline outputs were read, was not met. | packages/HOLD/: hold-README.md |

### 6.7 Accuracy anchor and re-decode

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| BR-b | How far is the recognizer's text from text made or edited by people? | reported | M (anchor table, abstract sentence); S (strata, error kinds); W (headline with interval) | No seen recording has a reference known to be made by people, so no word error rate exists; the run's recognizer and platform automatic captions disagree on 3.76% of words (creator mean, 95% interval 2.55 to 5.17%; 11 recordings of 11 creators; agreement of two machines, not an error rate), and the same recognizer and settings reproduce the project's earlier text of the same audio word for word in 40 of 48 recordings. | built/BR-b/: README.md, public/br-b-anchor-rows.csv, public/br-b-strata.csv, public/br-b-error-kinds.csv, public/br-b-other-text-inventory.csv; gallery: BR-b-fig-1, BR-b-fig-2, BR-b-fig-3 |
| BR-y | Do years and numbers agree with the references? | reported | S | Digit-written numbers of the project's earlier transcripts of the same audio, made with the same recognizer and settings, are all reproduced by the run's recognizer text (agreement of two machines, not an error rate), years written on a recording's page are found in its transcript for about a third of items (exact match), and the caption, larger-model and year rows of the pairs rest on too few creators, or too few creators with misses, to be released. | packages/CROSS/: br-y-years-numbers.csv, README.md; gallery: BR-y-fig-1 |
| BR-GS | How much do the seam measures move when the decoding grid is shifted? | reported | M (beside rv-R7); S | Moving the 30-s decoding grid by 15 s changes about 4 recognized words in 100, clustered near window seams, while the 10 controls decoded again on the run's own grid with the same worker reproduce the transcript of record word for word; thanks-phrase segments per hour of speech change by -0.40 between-creator SD (95% interval -0.88 to +0.08), pause and word measures by less than a quarter SD with every interval including 0, and the positional rule's 55 and 37 removals give fewer than 5 creators with a recurring removal. | built/BR-GS/: README.md, public/br-gs-sd-units.csv, public/br-gs-grid-shift-summary.csv, public/br-gs-onset-position.csv, public/br-gs-precision-check.csv; gallery: BR-GS-fig-1, BR-GS-fig-2, BR-GS-fig-3, BR-GS-fig-4 |

### 6.8 First-round labels as model-coded descriptions

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| LAB-V | How much of each recording is in which voice? | reported | M; S; W | On the middle-model subset a seen creator's words were on average about one third in a claimed voice, mostly embodied, and a little over one third in the creator's own voice, with similar shares from the small model on all recordings; model-coded, not checked by a person, and relayed voice alone is below the reliability floor. | packages/LAB/: lab-v-voice-shares.csv, lab-v-voice-shares-by-format.csv, lab-main-description-table.csv, lab-main-description-table.md, README.md; gallery: LAB-V-fig-1, LAB-V-fig-2, LAB-V-fig-3 |
| LAB-A | Which asks occur, in which voice? | reported | M; S; W | Spoken pay-or-enrol asks occurred in about four in ten of a creator's recordings on average, and fewer than one in ten of a creator's such asks fell in a claimed voice under either model; model-coded, not checked by a person. | packages/LAB/: lab-a-ask-classes.csv, lab-a-ask-voice.csv, lab-main-description-table.csv, lab-main-description-table.md, README.md; gallery: LAB-A-fig-1, LAB-A-fig-2 |
| LAB-F | Which forecasts occur, how checkable and how committed? | reported | M; S; W | On average about one in five of a creator's read forecast candidates was a world-future statement; of a creator's coded statements about a quarter on average named a checkable time window, fewer than one in ten an observable outcome, and most carried no hedge or condition; model-coded, not checked by a person, with the ten classes a description only and checkability kept after a failed two-model gate. | packages/LAB/: lab-f-forecasts.csv, lab-main-description-table.csv, lab-main-description-table.md, README.md; gallery: LAB-F-fig-1, LAB-F-fig-2 |
| LAB-S | What do the sentence codes show? | reported | S; W | World claims took about a quarter of a creator's coded body words and practice-and-feeling codes about three in ten, with broadly similar shares in cut and whole units; model-coded, not checked by a person, and the group's stability fell below its floor on the hold-out reliability sample. | packages/LAB/: lab-s-sentence-codes.csv, README.md; gallery: LAB-S-fig-1, LAB-S-fig-2 |
| LAB-T | How are recordings presented in their titles? | reported | S | On average about a quarter of a creator's titles present the recording as carrying a source's message and about a fifth name a source family; model-coded, kept as records after failed presentation gates, not checked by a person. | packages/LAB/: lab-t-title-codes.csv, README.md; gallery: LAB-T-fig-1, LAB-T-fig-2 |
| LAB-K | What kinds of recordings are there (census)? | reported | M (with rv-L1 beside it); S; W | Across all seen recordings the main kind (small-model map) was a claimed voice or an own-voice talk for about three in ten of a creator's recordings each, and under the small model on all recordings about four in ten of a creator's recordings had a claimed voice in a quarter or more of their words (middle model on its subset: a little over four in ten), comparable to rv-L1's interim figures from an earlier instrument; model-coded, not checked by a person. | packages/LAB/: lab-k-kinds-and-bands.csv, lab-k-agreement.csv, lab-k-beside-rv-l1.csv, lab-main-description-table.csv, lab-main-description-table.md, README.md; gallery: LAB-K-fig-1, LAB-K-fig-2, LAB-K-fig-3 |
| LAB-H | The label descriptions on hold-out creators | reported | S | The hold-out creators' model-coded voice, asks, forecasts, sentence codes, titles and recording kinds are printed beside the seen creators' under the LAB package's definitions, with the registered rule-B claimed side and broad own voice as the primary voice rows; the forecast class and the sentence codes are below their reliability floors on the hold-out sample, and cells resting on fewer than 5 creators are withheld. | packages/HOLD/: lab-h-descriptions.csv, hold-README.md; gallery: LAB-H-fig-1, LAB-H-fig-2, LAB-H-fig-3, LAB-H-fig-4, LAB-H-fig-5, LAB-H-fig-6, LAB-H-fig-7 |

### 6.9 H3 after its closure

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| H3-SEEN | The seen-creator H3 contrast (published) | reported | S | Published before this round. | results/h3-seen-exploratory.json (published before the round) |
| H3-X | H3 at the creator level on the hold-out, without the pilot-overlap recordings | reported | M (in the H3 table); S | At the creator level the hold-out's trimmed edge-against-middle contrast in first-person singular is positive with a t interval that includes zero; measured from the shift reference's exact centre it is larger, leaving out the pilot-era recordings changes it little, and H3 stays closed with no verdict. | packages/HOLD/: h3x-creator-level.csv, hold-README.md; gallery: H3-X-fig-1 |

### 6.10 Registered exploratory questions E1 to E13

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| E1 | Is the inserted thanks phrase tied to the decoding window or to silence? | reported | S | Equality within a factor of 1.25 is not shown: the pooled per-window chance of the inserted thanks phrase is higher in the slower half of a recording's windows (90% interval above 1), while the creator-equal version's interval includes 1. | packages/ER/: e1-thanks-by-tempo.csv, e1-descriptives.csv, ER-README.md; gallery: E1-fig-1, E1-fig-2 |
| E2 | Does a creator's claimed-voice profile resemble other creators' claimed voice more than the creator's own voice? | reported | S | In the few creators who qualified, a creator's claimed-voice function-word profile was closer to the same creator's own-voice profile than to other creators' claimed-voice profiles (model-coded voice, not checked by a person); with unstandardised profiles, a row chosen after the result, the difference is near zero in the middle-model subset. | packages/E/: e2-function-word-profiles.csv; gallery: E2-fig-1 |
| E3 | Is articulation rate higher at the edges, and does second-person address rise over a recording? | reported | S | After the 180-s trims, the seen creators' recordings show no edge-against-middle difference in recognizer-timed articulation rate beyond about 1% (90% interval 0.993 to 1.007), while second-person address is higher in the last tenth than in the first. | packages/ER/: e3-edges-and-address.csv, e3-position-curves.csv, e3-position-curves-seen-simultaneous.csv, ER-README.md; gallery: E3-fig-1, E3-fig-2 |
| E4 | Is slowing in the claimed voice carried by silence or by articulation? | not run | S | Not run: its condition, at least 5% slowing under H1, cannot be met because H1 was not determinable. | - |
| E5 | Silent against filled hesitation by voice | reported | S | No difference in hesitation between the claimed voice and the same creators' own voice is shown: every t interval of the within-creator differences includes zero; the means lean towards more long silent pauses and fewer filler words in the claimed voice, and only the primary's bootstrap interval for pauses of 1 s or more lies above zero (model-coded voice; description only; detectable sizes in r3-P33; corrected 2026-11-26 under r3-P35). | packages/E/: e5-hesitation-by-voice.csv; gallery: E5-fig-1 |
| E6 | Is the claimed voice more formulaic? | reported | S | No clear difference in formula coverage between claimed-voice and own-voice spans of the same creators (the intervals of the differences include zero; no equivalence margin was set): the claimed voice was not found to be more formulaic (model-coded voice). | packages/E/: e6-formula-coverage-by-voice.csv; gallery: E6-fig-1 |
| E7 | Do opening and closing frames found on seen creators transfer to hold-out creators? | not run | S | Not run: its registered precondition (inventory frozen before freeze 2) was not met. | - |
| E8 | Does a claimed source carry a tempo? | reported | S | Among the few creators with family-titled recordings, tempo and pause share varied mostly between creators, and the share of variance between source families could not be pinned down (its interval runs from zero to near one; model-coded title families). | packages/E/: e8-tempo-by-source-family.csv; gallery: E8-fig-1 |
| E9 | Does phrasing travel with a claimed source? | reported | S | Creators titled under the same source family shared slightly more rare five-word runs with each other than with creators of other families, but the difference lies inside the band of permuted family labels and rests on few creators (model-coded title families). | packages/E/: e9-shared-runs-by-family.csv; gallery: E9-fig-1 |
| E10 | Do asks follow urgency? | not run | S (status table) | Not run: DIR's go rule failed. | - |
| E11 | Does conspiracy vocabulary follow the claimed lineage? | reported | S | No clear difference between creators titled under star-people families and under angelic or devotional figures in the share of recordings with secret-control or with consciousness-shift vocabulary (both intervals include zero), and neither vocabulary's 90% t interval lies inside the equivalence margin of 0.10 fixed before the run (for secret-control vocabulary the lower end, -0.103, lies just outside, while the bootstrap interval lies inside), so equivalence is not shown (cue counts, model-coded title groups). | packages/E/: e11-vocabulary-by-lineage.csv; gallery: E11-fig-1 |
| E12 | Do dated titles deliver dated statements? | reported | S | Most recordings whose titles name a calendar period hold a model-coded time-anchored statement about the world's future, a higher share than the same creators' other recordings (an estimate, no test), on forecast labels whose class is below its reliability floor on the hold-out reliability sample and whose time-window part failed its two-model gate on the seen gate sample. | packages/E/: e12-title-delivery.csv; gallery: E12-fig-1 |
| E13 | Where do the non-English creators sit on language-free timing? | reported | S (public only if 5 or more creators are described) | No placement of the hold-out creators whose recordings are mostly not in English (5 or more creators), on speech share after voice activity detection or on recording length, falls outside the 95% prediction interval of a new English creator (a 5% chance per placement); the pause and word-time measures were not used because the recognizer bridge finds them model-dependent. | packages/HOLD/: e13-placements.csv, hold-README.md |

### 6.11 The paper review's 'later' list

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| MR-18c | Does voice-label timing leak into the timing contrasts? | reported | S | Within recordings, the five text features the voice labeller sees explain about 6% of the variation in unit speech rate but almost none of the claimed-voice label (R-squared 0.002), and they predict almost none of the claimed-minus-own difference in unit rate (0.001 of -0.071 on the log scale); the all-units row and the middle model agree (model-coded voice; not checked by a person). | packages/MR/: mr-18c-timing-leak.csv, README.md; gallery: MR-18c-fig-1, MR-18c-fig-2, MR-18c-fig-3 |
| MR-18d | What do the label-based contrasts give under permuted labels? | reported | S | Under the registered permutation of voice spans within recordings none of the label-based statistics is centred (H1's null mean -0.021 against a tolerance of 0.005; H4's 0.48 SD units; H6's log rate ratio -0.39); a post hoc diagnostic is consistent with the permuted labels keeping part of the observed assignment (for H1 the same permutation is centred when unit rates are made independent of position and label, and a constant label effect of the seen size with no position effect already gives about 69% of the observed null mean), while a unit-level shuffle is centred for H4 and H6, so this permutation cannot serve as a centring check for these statistics (model-coded voice; not checked by a person). | packages/MR/: mr-18d-permutation-null.csv, mr-18d-post-hoc-diagnostic.csv, README.md; gallery: MR-18d-fig-1, MR-18d-fig-2, MR-18d-fig-3 |
| nlp-R7 | How sensitive are span results to boundary jitter? | reported | S | No shift of up to 3 sentence units in either direction, and no random shift from the two models' boundary disagreement, changes where the interval of H1, H4 or H6 lies against the amended reading rule's conditions on seen creators; the estimates move by at most 0.027 (H1, log ratio), 0.33 SD units (H4) and 0.86 (H6, log ratio) across the shifts (small model of record; a description, not a test; model-coded voice; not checked by a person). | packages/MR/: nlp-r7-boundary-jitter.csv, nlp-r7-boundary-disagreement.csv, README.md; gallery: nlp-R7-fig-1, nlp-R7-fig-2 |
| nlp-R9 | How much do checkability and commitment share wording? | reported | S | About one in seventy of a creator's coded statements on average is flagged by the shared-wording rule (model-coded, not checked by a person). | packages/LAB/: lab-f-forecasts.csv, README.md; gallery: nlp-R9-fig-1 |
| nlp-R10 | How often is a world claim a self-presentation? | reported | S | In the coded sentence sample, units holding or following a self-naming cue (as the voice label marks it, one cue per span, so a lower bound) carry a creator-balanced mean of 0.002 of a creator's world-claim words (95% interval 0.000 to 0.004), so leaving them out moves the creator-balanced world-claim share by less than 0.001 under each of H5's three Q2 assignments (model-coded; not checked by a person). | packages/NLP/: nlp-r10-self-presentation.csv, README.md; gallery: nlp-R10-fig-1, nlp-R10-fig-2 |
| nlp-R11 | Lexical against modal hedges | reported | S | In the sentences of model-coded forecast statements RX finds a lexical hedge only in 0.082 and a modal hedge only in 0.052 of a creator's statements (creator-balanced means), the commitment model codes a hedge in 0.619 and 0.696 of these against 0.076 where RX finds neither, and evidential terms and perception reports are rare, so counting them as committed moves the committed share only from 0.771 to 0.775 (cue counts and model codes; not checked by a person). | packages/NLP/: nlp-r11-hedge-kinds.csv, README.md; gallery: nlp-R11-fig-1, nlp-R11-fig-2 |
| nlp-R13 | Capture-recapture recall of the finders | reported | S | Taking the forecast finder's two wordings as two captures, Chapman's estimate puts their joint recall of forecast candidates at 0.910 (95% creator-bootstrap interval 0.897 to 0.923) and of F1 statements at 0.991, likely too high because both captures are one model; for the asks find's two draws Chapman's estimate as registered puts the recall of the asks of record at 0.991 (95% interval 0.988 to 0.993), but the check added more asks of record that neither draw found (148) than that estimate allows (27), which contradicts it; the observed upper bound, chosen after the result, is 0.951 (95% interval 0.939 to 0.962) (model finders; agreement, not a measure of correctness). | packages/NLP/: nlp-r13-capture-recapture.csv, README.md; gallery: nlp-R13-fig-1 |
| CSS-5 | Source typology | reported | S | Of the kinds of source that seen creators' titles present as speaking, star peoples, federations, councils and other extraterrestrials are named by the most creators, about four in ten creators' titles name no source family that way, and on average about three quarters of a creator's claimed-voice words lie in recordings whose titles name no source family (model-coded titles and voice, not checked by a person; the speech-based NE full pass was not run). | packages/CSS/: css5-source-types.csv, css5-claimed-voice-by-source-group.csv, css5-repertoire.csv, css5-profiles-and-cooccurrence.csv, README.md; gallery: CSS-5-fig-1, CSS-5-fig-2, CSS-5-fig-3, CSS-5-fig-4, CSS-5-fig-5 |
| CSS-10 | Economy typology | reported | S | From their asks and pages, client offers (sessions or readings) were found for 39 of the 71 seen creators: for most creators of channels under 10,000 subscribers and for fewer than half of the rest (larger channels, pooled with the few seen creators without page text); courses, classes, events or retreats appear in about six in ten of a creator's recordings with page text (spoken asks model-coded, page cues cue counts, not checked by a person; offers, not income). | packages/CSS/: css10-offer-classes.csv, css10-economy-types.csv, README.md; gallery: CSS-10-fig-1, CSS-10-fig-2 |
| CSS-11 | Legitimation by voice | not run | S | Not run: needs a new codebook and money. | - |
| CSS-12 | Conspirituality and directive census | reported | S | On average consciousness-shift vocabulary occurred in about six in ten of a seen creator's recordings and secret-control vocabulary in about one in ten, with both in one recording less often still; in the middle-model subset the claimed-minus-own differences for consciousness-shift terms and numbered dimensions include zero (90% intervals) and the secret-control difference is not printed, while in the small-model view consciousness-shift terms and numbered dimensions were somewhat denser in claimed voice (cue counts; vocabulary, not belief; the directive part not run). | packages/CSS/: css12-census.csv, css12-by-source-profile.csv, README.md; gallery: CSS-12-fig-1, CSS-12-fig-2, CSS-12-fig-3 |
| SR-07 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: an independent voice detector and audio tagger: no new audio-analysis packages (plan section 6.11). | - |
| V8 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: an independent voice detector and audio tagger: no new audio-analysis packages (plan section 6.11). | - |
| CSS-9 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: an independent voice detector and audio tagger: no new audio-analysis packages (plan section 6.11). | - |
| nlp-R4 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: an independent voice detector and audio tagger: no new audio-analysis packages (plan section 6.11). | - |
| MR-21 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: an independent voice detector and audio tagger: no new audio-analysis packages (plan section 6.11). | - |
| SR-06 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a recognizer of another family and a forced aligner: no new audio-analysis packages (plan section 6.11). | - |
| MR-22 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a recognizer of another family and a forced aligner: no new audio-analysis packages (plan section 6.11). | - |
| V7 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a recognizer of another family and a forced aligner: no new audio-analysis packages (plan section 6.11). | - |
| SR-09 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: diarisation, speaker embeddings, synthetic-voice screen: no new audio-analysis packages (plan section 6.11). | - |
| nlp-R6 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: diarisation, speaker embeddings, synthetic-voice screen: no new audio-analysis packages (plan section 6.11). | - |
| CSS-3 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: diarisation, speaker embeddings, synthetic-voice screen: no new audio-analysis packages (plan section 6.11). | - |
| SR-08 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: acoustic arm: no new audio-analysis packages, and biometric (plan section 6.11). | - |
| SR-21 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: re-probe of the creator-rule language files: no GPU lease for it (plan section 6.11). | - |
| MR-24 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: re-probe of the creator-rule language files: no GPU lease for it (plan section 6.11). | - |
| nlp-R5 (part a) | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: re-probe of the creator-rule language files: no GPU lease for it (plan section 6.11). | - |
| SR-02 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a person's coding: A8 (plan section 6.11). | - |
| MR-17 (voice part) | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a person's coding: A8 (plan section 6.11). | - |
| nlp-R17 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a person's coding: A8 (plan section 6.11). | - |
| CSS-16 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a person's coding: A8 (plan section 6.11). | - |
| SR-10 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a local open-weights reader: no model download; VER-3R is the cross-vendor reader that exists (plan section 6.11). | - |
| nlp-R15 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a local open-weights reader: no model download; VER-3R is the cross-vendor reader that exists (plan section 6.11). | - |
| MR-19 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a local open-weights reader: no model download; VER-3R is the cross-vendor reader that exists (plan section 6.11). | - |
| MR-16 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| SR-12 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| CSS-6 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| SR-13 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| CSS-1 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| CSS-2 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| CSS-8 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| CSS-13 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| CSS-17 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| CSS-18 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| MR-13 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: new data, a new cohort or a comparison set: downloads are closed by the owner (plan section 6.11). | - |
| SR-16 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: acts of the owner: external time stamps, field hypotheses, ethics (plan section 6.11). | - |
| V20 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: acts of the owner: external time stamps, field hypotheses, ethics (plan section 6.11). | - |
| CSS-19 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: acts of the owner: external time stamps, field hypotheses, ethics (plan section 6.11). | - |
| V26 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: acts of the owner: external time stamps, field hypotheses, ethics (plan section 6.11). | - |
| V25 | Paper review 'later' list item (meta-review section 5.3) | not run | S (status table) | Not run in this study. not run: a reproducibility capsule: engineering, not a result (plan section 6.11). | - |
| MR-09 | An exploratory reporting plan (paper review request M6) | reported | - | The plan is registered and this table reports against it. | exploratory-reporting-plan.md and its addenda 1 to 3 (published beside the results folder) |

### 8 Hold-out ids without a row of their own

| Id | Question | Status | Place | Headline | Files |
|---|---|---|---|---|---|
| rv-D2-H | Transcript-derived balance covariates of the hold-out | reported | S; M (one sentence per covariate beyond 0.25 in the rv-D2 paragraph) | The hold-out's English creators have fewer recognized words per minute inside recognizer segments and lower recognizer confidence than the seen creators (SMD about -0.8 for both), and more time before their first and after their last recognized segment. | packages/HOLD2/: rv-D2-H-transcript-covariates.csv, rv-D2-H-sentences.csv, rv-D2-H-sentences.txt; gallery: rv-D2-H-fig-1 |
| rv-D3-H | Positional time-without-speech display including hold-out creators | reported | M (coverage figure, hold-out beside seen); S (share without speech) | Hold-out coverage point estimates in the first and last minute lie below the seen curve, but the two curves are not distinguished under their simultaneous bands; the overall share of audio outside recognized speech is close to the seen value, with overlapping intervals. | packages/HOLD2/: rv-D3-H-aligned-coverage.csv, rv-D3-H-share-without-speech.csv; gallery: rv-D3-H-fig-1, rv-D3-H-fig-2, rv-D3-H-fig-3 |
| BR-b-H | Word error rate on hold-out and other-group recordings with third-party text | not run | M (anchor table, via BR-b); S | BR-b-H was not run: fewer than 5 creators in each group have a reference that could be made by people (even counting every caption whose receipt leaves its maker open, under 5 creators (0 to 4) in each group), so the recognizer was not run, and BR-b's machine-agreement rows were not run on these groups either. | packages/BRBH/: BR-b-H-eligibility.csv, BR-b-H-README.md |
| RX-H | Hold-out pass of the RX patterns | reported | S; W (family-level distributions) | Most pattern-family rates of the hold-out sit inside or near the seen intervals; greetings again open and sign-offs again close recordings, while the frame, ask and framing-cue families have lower point estimates than on seen creators (cue counts, precision read on seen hits only); the reporting family's hold-out rate is not released (dominated by fewer than 5 creators). | packages/HOLD2/: RX-H-pattern-rates.csv, RX-H-position-edges.csv; gallery: RX-H-fig-1, RX-H-fig-2 |
| TIME-H | Hold-out pass of the time roles | not run | S (status table) | Not run: the time-role reading needs model calls and no money is left under the hard stop. | - |
| PT-H | Hold-out pass of the page text (including non-seen page fields) | reported | S | Hold-out page text shows payment, course, event, shop, other-platform and platform-engagement cues in shares close to the seen creators', with booking and newsletter cues too sparse to print (cue counts, precision read on seen hits only). | packages/HOLD2/: PT-H-family-shares.csv, PT-H-link-classes.csv; gallery: PT-H-fig-1, PT-H-fig-2 |
| NE-H | Hold-out pass of the named sources | not run | S (status table) | Not run: the named-source reading needs model calls and no money is left under the hard stop. | - |
| TM-H | Hold-out transform of the topic model | reported | S; W (topic table with neutral labels) | Under the frozen topic transform the hold-out's topic shares lie near the seen ones: no topic difference passes the family-wise band (the largest point differences, planet/humanity/star beings higher and channel logistics lower, stay inside it), and topics still track channels well beyond the shuffles. | packages/HOLD2/: TM-H-topic-shares.csv, TM-H-topic-differences.csv, TM-H-channel-leak.csv, TM-H-position-edges.csv; gallery: TM-H-fig-1, TM-H-fig-2, TM-H-fig-3 |
| DC-H | Exploratory replication of change inside channels | reported | S | Inside hold-out channels, recordings published within a week of each other are again more alike in vocabulary than recordings one to six months apart (+0.026, 90% interval 0.003 to 0.048), a little less than the seen +0.037. | packages/HOLD2/: DC-H-primary.csv; gallery: DC-H-fig-1 |
| SD-H | Exploratory replication of the same-date period split | reported | S | Across hold-out channels the near-date resemblance is not above the date-shuffle references overall or in either part of the post hoc split; in the later part the hold-out estimate is below zero. | packages/HOLD2/: SD-H-period-split.csv; gallery: SD-H-fig-1 |
| CH-H | Exploratory replication of the channel atlas | reported | S | On hold-out creators the Mantel agreement of a channel's topic, pattern and word views has lower point values than on seen creators (0.09 to 0.27 against 0.31 to 0.41; the groups are not compared under an interval), and most topic-share variance shares have lower point values (pointwise intervals, no family-wise control). | packages/HOLD2/: CH-H-variance-shares.csv, CH-H-mantel-views.csv; gallery: CH-H-fig-1, CH-H-fig-2 |
| META-H | Audience counts and page-field presence of non-seen recordings | reported | S | Hold-out recordings carry descriptions, links, chapters and tags slightly less often than seen recordings (point estimates; the intervals overlap), and inside hold-out channels longer recordings again went with more views at capture while the age slope is near zero. | packages/HOLD2/: META-H-page-fields.csv, META-H-audience-counts.csv, META-H-engagement-core.csv; gallery: META-H-fig-1, META-H-fig-2, META-H-fig-3 |
| META-169 | The 169 cloud-only metadata objects, read once read-only after freeze 2 | reported | S (rows beside TABLE, META and META-H) | All 169 cloud-only objects were read once and matched their recorded hashes, but they carry almost no platform page fields, so they add recordings to the metadata coverage but almost no page-field or audience-count values. | packages/HOLD2/: META-169-objects.csv, META-H-page-fields.csv, META-H-audience-counts.csv; gallery: META-169-fig-1 |
| NAMES-H | Variant forms added by code only (NAMES hold-out forms) | reported | S | On hold-out transcripts the seen name list finds the same kinds of families, exact canonical spellings dominate for most of them, and code adds a few dozen near-match forms that are not among the seen candidate forms, none of them adjudicated. | packages/HOLD2/: NAMES-H-family-table.csv, NAMES-H-code-only-forms.csv; gallery: NAMES-H-fig-1 |
| E3-H | E3 on the hold-out creators | reported | S | On the hold-out creators the same code gives an edge-against-middle articulation ratio whose interval includes 1 and a rise in second-person address from the first to the last tenth like the seen creators', printed side by side and never pooled. | packages/ER/: e3-edges-and-address.csv, e3-position-curves.csv, ER-README.md; gallery: E3-H-fig-1, E3-H-fig-2 |
| E4-H | E4 on the hold-out creators | not run | S | The split of slowing into pauses and articulation was not run on the hold-out because H1 could not be determined there. | packages/HOLD/: hold-README.md |
| E7-H | E7 scoring on hold-out edges | not run | S | Not run: its registered precondition (inventory frozen before freeze 2) was not met. | - |
| E9-H | E9 on the hold-out creators | reported | S | Run on the hold-out creators alone, E9's measure of whether phrasing travels with a claimed source could not be computed (no family has cells of two or more hold-out creators, so no cell has a same-family partner); the base is fewer than 5 creators and the output is released by the owner's exception. | packages/E9H/: e9h-shared-runs-seen-and-holdout.csv |
| VER-DEP-H | VER-DEP hold-out bounds (partial-identification bounds and threshold distances) | not run | M (bounds beside the registered rows); S | Not run: no registered estimate exists for the bounds to stand beside. | - |

### 6.12 Catalogue experiments: where each is carried

| Id | Experiment | Carried by | Not carried |
|---|---|---|---|
| T1 | coverage ledger | carried by: TABLE (reported), rv-D1 (reported) | - |
| VP | variance partition | carried by: rv-R5 (reported), CH (reported) | - |
| EB | shrinkage and rank intervals | carried by: rv-R5 (reported), CH (reported) | not carried: per-creator values (private only) |
| CA | coverage audit and power | carried by: CAL (reported), rv-R2 (reported) | - |
| QD | quality dependence | carried by: rv-R6 (reported), rv-R7 (reported), GRID (reported), BR-b (reported), BR-GS (reported) | not carried: stage 2 against hand transcripts (X: A8) |
| HR | hand reference | carried by: KA (reported), VER-3R (reported) | not carried: the human study (X: A8) |
| SP | speaker separation | not carried | not carried: X: no packages |
| BR | bridge | carried by: rv-R3 (reported), BR-b (reported) | not carried: part a published in the results README |
| SD | serial dependence | carried by: rv-R5 (reported), DC (reported) | not carried: the variogram grid (X: order is not time, R10) |
| PO | position curves | carried by: rv-R1 (reported), rv-D3 (reported), RX (reported), TM (reported), ENTRY-E2 (reported), E3 (reported) | not carried: H3 (registered); per-creator position heat maps (private only) |
| LX | lexical diversity | carried by: CH (reported), E6 (reported) | - |
| SG | delivery-state segmentation | carried by: LAB-V (reported), rv-L1 (superseded), LAB-K (reported) | not carried: private timeline strips |
| RH | rhythm | carried by: GRID (reported), CH (reported), rv-R5 (reported) | not carried: the delivery-plane typology (N) |
| CX | content axis | carried by: TM (reported), CH (reported), NAMES (reported), NE (reported) | - |
| SM | creator similarity | carried by: CH (reported) | - |
| GB | grounds for belief | carried by: CSS-11 (not run) | not carried: N |
| SV | source or speaker | carried by: NE-F (not run), E8 (reported), E9 (reported) | not carried: H9 (registered; not determinable in the first round) |
| FL | forecast ledger | carried by: LAB-F (reported), TL-BUILD (reported), TL-SPEC (not run), TL-7.1 (reported), TL-7.2 (reported), TL-7.3 (not run), TL-7.4 (reported), TL-7.7 (reported), TL-7.8 (reported), TL-7.9 (reported) | not carried: the accounting of passed forecasts (X: agnosticism) |
| AK | ask ladder | carried by: LAB-A (reported), PT (reported) | - |
| TP | title cue against content | carried by: E12 (reported), META (reported) | not carried: META (c) title cues |
| EV | world events | carried by: SD (reported), NE (reported) | not carried: event-study panels (N) |
| LG | language case panel | carried by: NONEN (not run), E13 (reported), rv-D7 (reported) | - |
| SY | calendar synchrony | carried by: SD (reported) | - |
| FA | first-appearance table | not carried | not carried: X: not run (left-truncated window; no power) |
| RW | replication wave | not carried | not carried: X for this study: downloads closed |
| CS | comparison set | not carried | not carried: X for this study: new data |
| SL | selection sensitivity | carried by: rv-R4 (reported) | not carried: stage 2 (X: new data) |
| PF | internal profile page | not carried | not carried: private by design; never a place of report |

## Corrections

Dated notes made after publication, in the form of the published first-round file's corrections (lead's decision D48).
Each changes wording, adds a reading aid or withholds a value; none changes an estimate, an interval or a verdict. The
frozen texts that the same corrections touch (the registry's frozen text, `hypotheses.md`, the freeze records) are not
edited: their corrections are in [addendum 4](../../exploratory-reporting-plan-addendum-4.md).

- **2026-11-26 (D72, D73).** E5's creator counts under H1's span rule are printed in band form; one share is no longer printed, in E5's table and in the gallery's data
  file, figure (redrawn by its plotting group's own code, changed only in the count labels and in its title) and
  caption. The status table names the share. No estimate or interval changes.
- **2026-11-26 (r3-P35: E5 led by the absence of a shown difference).** E5's headline (above, in the status table and
  in the gallery's title) now leads with the absence of a shown difference: every t interval of the within-creator
  differences includes zero. The detectable sizes that the third-round programme's r3-P33 prints for E5's primary
  (80% power, one-sided 5%, from the printed intervals) are about 1.4 long pauses of 1 s or more per 100 words and
  1.6 filler words per 1,000 words, so the null says little.
- **2026-11-26 (r3-P35: the agnosticism sentence).** Every description in this release is read with the sentence the
  third-round panel agreed and the lead adopted: "No measure in this study can tell whether a non-human source speaks;
  every measure describes the speech in these recordings and how the creators present it." Phrases such as "says
  nothing about a claimed state" are read in this form.
- **2026-11-26 (r3-P35: voice definitions centred on the creator).** The voice classes are read as definitions whose
  subject is the creator: the first-person claimed voice (the frozen instrument's "embodied" code) is the creator
  speaking in the first person as a named non-human source; the reported claimed voice (its "relayed" code) is the
  creator reporting what a source is said to say; the own voice is the creator speaking as themself. A voice is
  "presented as" a source's, never "authored by" one. The frozen instruments and their code names do not change.
- **2026-11-26 (r3-P35: validity status of label-based captions).** Every caption, headline and table note here that
  rests on labels (voice, asks, forecasts, sentence codes, titles, recording kinds, and the outputs built on them)
  carries this validity status, whether or not it repeats it: model-coded; agreement between
  models, readers or methods only, never accuracy; not checked by a person; relayed voice alone below its floor
  everywhere; on the hold-out reliability sample, the forecast class of record and the sentence codes' stability below
  their floors; forecast checkability and title presentation kept as records after failed gates. The gallery's index
  carries the same line.
- **2026-11-26 (r3-P35: LAB-A's caption fact).** LAB-A's shares of asks in a claimed voice depend on how the voice
  codebook treats offers: the known-answer battery scores an own offer inside a claimed passage as own voice and holds
  no arm with an offer presented in the source's voice, so it cannot show whether the labeller moves offers out of the
  claimed voice. Until the programme's arm A runs (unfunded), LAB-A's headline is read as depending on the codebook's
  own-offer rule, and voice may not be separable from position in a recording (H6's own registered text names the
  own-voice frame as its mechanism; addendum 4). This applies to LAB-A's headline, tables and gallery captions.
- **2026-11-26 (the titles' failed gates; the lead's step-1 decision 36).** Wherever this release cites the titles'
  failed presentation gates (GATES, rv-D5, LAB-T, CAL-f's title line), read beside it: "the gate sample and the
  hold-out reliability sample drew harder titles than the rest of the seen roster (r3-P20); outside them,
  presentation agreement was higher".
- **2026-11-26 (nulls and their detectable sizes; r3-P35 and step-1 decision 29).** A null is read with its detectable
  size. E9's null (phrasing shared within title families) could detect only about 2.6 shared runs per pair on 6
  creators (r3-P33), so it says little. r3-P33 prints a detectable size beside every seen contrast of its audit that
  is not beyond its margin (among them E5, E6, PT-cd's platform asks, E1's creator-equal ratio and CSS-12's rows that
  include zero). The release's other nulls about channels, groups or recognizers converging (SD's same-date
  vocabulary, SD-H, TM-H and rv-L2's label flips) have no printed detectable size; until one is printed, none is read
  as independence, as the absence of an effect or as a market.
- **2026-11-26 (H1's rate against the deposited margin; the lead's step-1 decision 28).** MR-18c and nlp-R7 print the
  claimed-minus-own difference in rate on H1's spans. Every small-model row of that contrast printed in this release
  lies inside the third-round programme's deposited ratio margin (0.80 to 1.25; deposit 2), which is much wider than
  H1's registered smallest effect (a log ratio of -0.05, about 5% slower): by the deposited margin, the slowing these
  rows describe is small. Step 1's own H1 rows (r3-P04) have banded counts, and their readings are not printed for
  privacy. Exploratory; not a test of H1.
- **2026-11-27 (the gate sample G; the lead's decision 134).** Two gallery captions describe the gate sample G, one as
  "seen and check creators" and one as "seen creators; not the 23 check creators of the VER-3R sample". G holds a
  seeded draw from the seen creators plus every check creator that draw did not cover, so it includes development and
  check creators, and its rows on the check creators alone report its check subset. The second caption means only that
  G is not VER-3R's sample. The gallery's generated files are not edited. No number or reading changes.
