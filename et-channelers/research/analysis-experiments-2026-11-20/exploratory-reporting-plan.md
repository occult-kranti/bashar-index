# Exploratory reporting plan

Written 2026-11-21 between about 03:00 and 03:30 UTC, under the registry decision of 2026-11-21 02:50 UTC ("an
exploratory reporting plan is written and hashed now, and every exploratory output it lists is reported whatever it
shows"; first stamped 03:00 and corrected to the clock in the registry) and the paper review's request M6 (MR-09). It
also takes account of the registry decisions of 03:08 UTC. It is fixed by its SHA-256, which the lead enters in the
[registry](registry.md) with the commit that adds this file.

**When it was written.** Before any second-round result on a hold-out creator exists, and before any first-round
production label exists on any creator. What exists at this point: the second-round programme's free and pilot items on
seen creators, the paper review's build items on seen creators, the entrance (ENTRY) experiment and its model check, the
known-answer battery, the verification and timeline pilots, and instrument work (pilots, gates, reliability and smoke
tests) on seen creators. Section 6 marks each of these as built.

**What this file holds.** No transcript text, creator names or codes, channel names, video ids, titles, per-creator values
or per-recording rows. It lists outputs; it reports no result.

Exploratory (registry A2); not a test of H1-H10.

---

## 0. How this file is kept

- This file is not edited after its hash is entered in the registry. A change is made by an addendum file beside it,
  with its own UTC time and SHA-256 entered in the registry.
- An addendum may add an output, correct a factual error in a row (for example a wrong file name) or record an output as
  not run. It may not remove an output, change a primary estimand, band, panel, weighting or threshold after a result of
  that output is known, or move an output to a less visible place because of its result.
- Outputs added by an addendum carry the words "added after the exploratory reporting plan" and the addendum's UTC time
  wherever they are reported.

## 1. Scope

**Covered: every exploratory output of the study.** That is every output that is not a confirmatory row of H1 to H10:

- the second-round programme (23 items: TABLE to NONEN), its digest and its fixes;
- the paper review's build items (D1 to D8, R1 to R7, L1 to L3, run tags `rv-*`) and the items of its "later" list;
- the entrance experiment ENTRY and its model check;
- the verification layer and the prediction timeline of amendment A11;
- the accuracy anchor (the word error rate against third-party text, BR part b) and the grid-shift re-decode of the
  registry decision of 2026-11-21 02:50;
- the first-round labels on seen creators, reported as model-coded descriptions;
- the looks at H3 after its closure (A6);
- the thirteen registered exploratory questions E1 to E13 of [`hypotheses.md`](hypotheses.md) section 14.3;
- the hold-out robustness rows (programme item HR) and every hold-out pass of an exploratory item after freeze 2;
- the experiments of the analysis catalogue ([`README.md`](README.md), section 4), each mapped to the output that
  carries it or recorded as not run (section 6.12).

**Not covered, with the reason:**

- The confirmatory rows of H1 to H10, their verdicts and their registered robustness rows (the multiverse rows M1 to M13
  and the tipping-point table). They are governed by the registry: under A2 every registered hypothesis keeps one row with
  its estimate, interval and verdict, whatever it shows. Output VER-MV below only restates that every such row is printed.
- The channeler discovery (hashtag and search harvest; registry entry on the selection rule). It builds a list of candidate creators kept
  apart from the frozen cohort; it is not an analysis of the cohort. If any of it is reported, its counts are reported
  whole (harvest size, classified, kept), with no names.
- Private versions of outputs (coded per-creator plots, quotation lists, name lists, card tables). They stay private
  under rule R15 of the catalogue. They are not withheld results: the public form of the same output carries the result
  as a distribution (section 3).
- Operational records (ledgers, run logs, costs), except where an output row names them.

## 2. The reporting rule

P1. **Reported whatever it shows.** Every output listed in section 6 is reported in the place named in its row, with
its estimate, its interval, its counts (creators, recordings and, where it applies, words or items), its reference band
and its label line. A null result, a result in the unexpected direction, a failed gate and a "not determinable" result
are reported in the same place and in the same form as any other.

P2. **Not run is a result.** An output that cannot be produced is reported as "not run: <reason>" with the counts that
decided it: a gate that failed, a stop or go rule, too few creators (the minimum is named in the row or in the item's
text), money, an owner's decision, an instrument that was not frozen, downloads closed. The supplement holds a status
table of every output id of this plan (section 9).

P3. **No choice after the result.** The primary estimand, band, panel, weighting, threshold and admission rule are those
fixed before the output's first run: the item's `prespec.json` where it exists, otherwise the programme's, the
meta-review's or the protocol's text for that item. Every other version is a sensitivity row printed beside the primary,
never in its place. The one exception is a primary named by a registry decision entered before this file's hash (P4).

P4. **Choices already made after a result are shown as such.** Where a version was chosen after a result of the same
output was known, both versions are reported, with the UTC time of the choice and the words "chosen after the result".
Where a registry decision entered before this file's hash names the primary, that primary stands, and the version it
replaced is printed beside it. Known cases at the time of writing: TC's stage-1 gate reading (reading A, as run, stands
by the registry decision of 2026-11-21 03:08, decided at about 02:30 UTC after the stage-1 results; readings E and D
beside it); the RXP gate
estimator (hit-weighted primary, creator-equal beside it); the CM admission rule (F25 primary after a rerun; first-run
admission as a row); the COR within-creator estimator (ranks inside each creator; pooled ranks as a column); the DIR
headline (creator-equal after the verifier); GRID's seam rule (the capped, weighted rule is primary by the registry
decision of 03:08; the programme's literal rule and no rule are rows); the ENTRY patterns (version 1 frozen before the
check-creator reading; version 2 revised after the model check).

P5. **Versions.** When an output's code, patterns or rule are revised after its first result, the first frozen version
stays the version of record and every later version is reported beside it as a revision row. This applies to every
hold-out run as well: each version frozen in the freeze-2 record is run, and the first remains primary.

P6. **Corrections and superseded rows.** A figure found wrong by a verifier is reported in its corrected form, and the
correction is listed in the supplement's errata with the wrong value and the reason (for example the corrections and
withdrawn statements of the panel digest, section 4). A row superseded by a better measurement is listed as superseded
with a pointer (for example RX's own read precision, superseded by RXP). Nothing is deleted silently.

P7. **Fixed places.** The place of each output (section 3) is fixed here. If the main text runs out of space, a whole
main-text output may move to the supplement with a one-line pointer left in the main text and the move logged. No cell,
band, row or panel is moved or dropped selectively.

P8. **Numbers agree across places.** A number reported in more than one place is the same number. The consistency test
of build item rv-D4 runs over the paper, the supplement, the results README and the dashboard before each release, and fails
on any unexplained difference.

P9. **Wording.** Every output carries one of the existing label lines ("Exploratory, panel round 2 (registry A2/A7); not a
test of H1-H10", "Exploratory, paper review (registry A2/A7); not a test of H1-H10", or this plan's line, "Exploratory (registry A2);
not a test of H1-H10"). Model-coded
results say "model-coded" and name the verification done, with its figures, and "not validated by a person" (A8, A11).
Pattern counts below their precision gate are "cue counts". Change over time is described inside each channel's span and
never called a trend. No result is called validated, accurate or distinctive of channelling. No prediction is said to
have come true or failed. No significance marks; no recording-level or window-level p-values.

P10. **Release review.** Before an output reaches the public repository, the paper or the dashboard, it passes the review
that programme rule 13 requires (taken by the lead under the owner's delegation of 2026-11-21 00:50 UTC). The review
checks privacy, correctness and wording. It does not look at the direction or size of a result, and it cannot hold an
output back for its result.

## 3. Places of report and public safety

| Code | Place |
|---|---|
| M | Paper, main text (the measurement-and-protocol paper of the registry decision of 2026-11-21 02:50) |
| S | Paper, appendix or online supplement |
| W | Public dashboard (findings dashboard and its successors) |

Every place is public, so every reported form follows the tightened rule R15 of the catalogue:

- distributions only: counts by category, quantiles, binned histograms, cohort-level estimates with intervals;
- no creator name or code, no channel name, no video id, no title, no quotation, no per-recording row, no per-creator
  row, point, cell or label, no top or bottom list, no minimum or maximum of a transcript measure (10th and 90th
  percentiles instead);
- no cell with fewer than 5 creators. Bins and categories are merged by a rule fixed here, never by suppressing single
  cells: adjacent bins are merged until every bin holds 5 or more creators (the bin with the fewest creators joins the
  neighbour that holds fewer, the inner one on a tie, so outer bins grow inwards; the rule the public outputs already
  use); categories with fewer than 5 creators are pooled into "other" (languages, text kinds, source groups, pattern
  templates, calendar cells), and if "other" still holds fewer than 5 creators the smallest remaining categories join it; a
  calendar display merges consecutive periods until every cell holds 5 or more creators. A merge is stated in the caption.
  The one display decided otherwise is SD's calendar strip: by the registry decision of 2026-11-21 03:08 it shows 2026
  only, in ISO weeks, with weeks under 5 creators shown as "<5"; no margin is published from which a masked week could be
  solved, and if one would be, the weeks are merged instead.
  If a whole output rests on fewer than 5 creators, its public form is "fewer than 5 creators" and the output is still
  listed in the status table;
- no model-coded per-video label is published (registry decision of 2026-11-21 02:50).

Private versions of an output (per-creator plots in fresh panel codes, coded heat maps, quotations, cards, evidence
links) stay in the private run folder. They are never a place of report under this plan.

## 4. Multiplicity

The exploratory set is not corrected as a whole. Selection is controlled by P1: everything listed is reported. Inside a
display, the following rules hold.

- **Displays with many cells.** A display that sets more than 10 cells, pairs or curve points against a reference is
  read only through a family-wise band, and every cell is still shown:
  - heat maps, matrices and tables of many contrasts: a **permutation-maximum band**. Under the item's own reference,
    the statistic of every cell is recomputed in each draw (999 draws or more); the 95th percentile of the maximum of the
    absolute cell statistics over the display is the family-wise threshold. The reference is the one the item names:
    creator-label permutation for between-creator contrasts, permutation within creator for within-creator contrasts,
    date permutation within creator (G) or within 28-day blocks (L) for time, circular shift within the recording for
    position;
  - curves (lag curves, position curves, coverage curves): a **simultaneous band** (sup-t from 2,000 or more creator
    resamples, or the permutation maximum over the curve's points);
  - the false discovery rate at 10% may be printed as a screen only, labelled "screen, not a test".
- **What the text may discuss.** Only cells beyond the family-wise band are described as standing out. Every cell is
  shown, with pointwise intervals, and cells whose pointwise interval crosses the reference are faded (rule R14).
- **Expected by chance.** A display of k contrasts prints how many would pass by chance (for example "about 4 of 40
  expected").
- **Built displays without a family-wise band** are reported as built, with the caption "pointwise intervals; no
  family-wise control". A family-wise band may be added as a companion; it never replaces or hides a cell.
- **Sensitivity rows** (panels, weightings, masks, versions) are not tested against each other. They are printed beside
  the primary, and the text says which of them change the sentence against a margin fixed before the run where one
  exists (build item rv-R4).
- **Fixed counts of rows.** The rows of an item are those of its pre-specification. A row that did not exist at the
  item's first run is labelled post hoc.

## 5. Hold-out contacts

**Groups.** Seen: the 71 creators of the registry. Hold-out: the 23 creators of the registry. Other: the 7 creators
that are in neither group. The contact rule of the hold-out applies to the other group as well.

**A hold-out contact** is any operation, by code, by a model or by a person, that opens, loads, sends to a model, displays
or derives a value from any of the following, for any recording of a hold-out or other-group creator:

- transcript text, segments, words, word times or recognizer scores;
- timing measures by position in the recording (speech by position, pauses, coverage curves), even without words;
- titles, descriptions, chapters, tags, links, audience counts (views, likes, comments, subscribers), or any field of a
  metadata file. Loading a whole metadata file is a contact even if no field is kept;
- model labels, model answers or cards made from any of these.

**Not a contact:** counts of recordings, durations, publication dates and time stamps, capture times, languages,
recognizer model, edition, archive status and run-queue position, taken from the run ledger, the inventory or the
whitelisted columns of TABLE's extract; group-level counts of files; matching identifiers as strings in order to exclude
them, provided no field of the matched file is read (such matching is recorded in the item's own log).

**Rules.**

1. Before freeze 2 no output of this plan makes a contact. The contacts already made are those of the registry's contact
   log (including TABLE's single logged extraction) and those that build item rv-D6 adds to it; they are listed in the
   paper's limitations with their UTC times.
2. After freeze 2 a contact is allowed only by code whose hash is in the freeze-2 record, runs once per output, and is
   logged in the registry's contact log with UTC time, code hash, what was read and what was written. A repeat run is
   logged as a repeat. Model calls on hold-out text also need freeze 1 for the instrument, and the timeline's hold-out
   statements also need the timeline procedure freeze.
3. An unplanned contact is logged the same day. Every output it touched carries "made after a hold-out contact on <UTC
   date>", is still reported, and the contact is listed in the paper's limitations.
4. Hold-out results of exploratory items are reported as an exploratory replication: hold-out-only estimates, beside the
   seen estimates, never pooled with them into one estimate, and never called a confirmation. The balance table (build
   item rv-D2) is printed beside them, because the hold-out is the tail of an English-first run and is not exchangeable with
   the seen creators.
5. Other-group creators enter outputs after freeze 2 only as a group of their own, never pooled with seen or hold-out
   creators.

## 6. The outputs

**Status codes.**

| Code | Meaning |
|---|---|
| B | Built on seen creators (and on run-level counts of all creators where the row says so). **Reported in full as built**: every figure, table and CSV in the item's output folder, with its captions, as corrected by its verifier and fixer, in the public-safe form of section 3 |
| R | Runs now on seen creators without labels; not yet built. Reported whatever it shows once run |
| L | Waits for first-round labels on seen creators (and, where named, for freeze 1) |
| F2 | Waits for freeze 2; uses hold-out or other-group material |
| N | Waits for a decision, a GPU lease, packages or new data; not scheduled. Reported as not run unless it runs |
| X | Will not run in this study for a reason already known; reported as not run with that reason |

A row may carry two codes (for example "B; hold-out part F2"). Every hold-out part is also listed in section 8.

Columns: **Question**; **Data** (seen creators unless stated); **Measure and display**; **Multiplicity** (section 4);
**Place** (section 3).

### 6.1 Paper-review build items (all B; label "Exploratory, paper review")

Built 2026-11-21 on seen creators and on run-level counts of all creators, and checked by the review's verifiers. They are
reported in full as built.

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| rv-D1 | What was selected, archived and transcribed, and where was each loss? | Inventory, run ledger, TABLE coverage and date-evidence tables; counts for all 101 creators (not a contact) | Census flow by stage and group (creators, recordings, hours, reasons); status and edition share by listing rank; odds ratio of "not transcribed" ranks 1-5 against 6-20 (95% creator bootstrap); SMDs of transcribed, other-text and missing recordings (90%); corrected date sentence | Census; one odds ratio; SMDs read against fixed lines | M (flow, date sentence); S (rank figure, tables); W (flow counts) | B |
| rv-D2 | How do the seen, hold-out and other creators differ, and how did the run order make the hold-out? | Ledger and inventory fields only (not a contact) | Creator-level covariates, group medians, SMDs with 90% intervals; love plot; cross-validated AUC of hold-out membership against 999 shuffles; vintage cross-table; run-order paragraph | Covariates read against fixed lines of 0.1 and 0.25; one sentence for every covariate beyond 0.25, none left out; AUC against its permutation band | M (paragraph, love plot); S (Table B, AUC, vintage) | B; transcript-derived covariates of the hold-out F2 (rv-D2-H) |
| rv-D3 | Where does the time outside recognized speech sit? | 1,293 seen transcripts | Five time classes (pooled hours and creator-equal shares); share without speech under two definitions, three weightings, with intervals; start- and end-aligned coverage in 15-s bins by length band | Simultaneous sup-t band (built); leave-one-creator-out ranges | M (coverage figure); S (classes, reconciliation); W (coverage figure, seen only) | B; hold-out positional display F2 (rv-D3-H) |
| rv-D4 | What is each headline number, on which base, weighting and interval, and how did it move from the snapshot? | Closed run; seen creators for text-derived numbers | Table U (estimand, weighting, estimate, 95% interval, n); Table D (drift from the snapshot); provenance CSV; cross-document consistency report | None (census of numbers) | M (Table U); S (Table D, provenance, consistency report) | B |
| rv-D5 | What is the measurement status of each construct? | All instruments and their checks | One row per construct: instrument and version, reference, reliability with n and interval, bridge verdict, seam sensitivity, known biases, allowed uses | None | M | B; rows updated with L outputs, each update logged |
| rv-D6 | How was the design registered and then amended? | Git times, ledger progress, registry, contact log | Timeline figure (run, design events, results, contacts); deviation table (as registered, as done, time, decided by, results known, direction, effect) | None | M (figure); S (table) | B; rows added for later deviations |
| rv-D7 | Do the public outputs keep their privacy promises? | Every public CSV and figure and the repository history | Minimum creators per cell over quasi-identifiers; linkage test; violations by category; fixes | None | S (counts by category and the fixes made); the per-file list stays private | B |
| rv-D8 | What was sent to external services, and how much of it was third-party speech? | Ledger counts, pilot voice-map codes, batch records | Requests, recordings, creators, words and tokens by service, run tag and date; share of words placed with other speakers; retention status | None | M (table in the paper's ethics section); S (by tag and date) | B |
| rv-R1 | What does H3 show at the creator level? | Published H3 summaries, CAL outputs, seen creator values | Registered U; t interval on creator means; sign test; recentred U with sign-flip p; inverse-variance pool and heterogeneity; placebo rejection; power; type M; detectable effect. Figures: seen creator U histogram (bins of 5 or more creators), placebo p against uniform, recentred U by trim length, first-person rate in 15-s bins | One estimand with its calibration | M (H3 table, results-table wording); S (figures a-d); W (results row wording) | B; hold-out parts F2 (H3-X) |
| rv-R2 | Can each registered rule reach a verdict at the eligible numbers of creators? | CAL outputs, registry, seen variance components | One row per H1-H10: state, reference centre, placebo rejection, coverage, smallest effect and power, minimum n, projected eligible creators with 90% range, detectable effect, type S and M, minimum attainable p; persistence plasmode | None (calibration, not tests of the hypotheses) | M (table, eligibility dot plot); S (power curves, plasmode, type S and M) | B; eligibility re-projected from seen labels L (via CAL-f) |
| rv-R3 | What do the two recognizer models agree on, for which uses? | 35 seen bridge pairs (published numbers for the one other-group pair) | Limits of agreement, signed-rank intervals, verdicts with and without the outlying pair and leave-one-out; differences in between- and within-creator SD units; disagreement in numerals, years and capitalised words; MATTR and log-probability under both models | Per-measure and simultaneous (Bonferroni over 17) intervals, both shown | M (interval plot, verdict table); S (Bland-Altman panels, class disagreement); W (bridge card) | B |
| rv-R4 | Do the headlines survive other weightings and windows? | Closed run; TABLE dates | Each headline under five weightings, a common 120-day window, posting-rate tertiles, a fixed calendar window, log posting rate as covariate; specification curves | Every specification shown; margin for "changes the sentence" fixed in `R4-prespec.json` before the run | S; M (one sentence per headline saying whether any specification changes it) | B |
| rv-R5 | How is each measure's variance split between and within creators? | 1,293 seen recordings | REML random-intercept models; ICC with intervals; design effect and n_eff; reliability of a creator mean; length correlations; adjusted ICC; per-word segment measures; filter on and off; shrunken pace | Intervals per measure, no tests; count of disjoint pairs printed | M (Table VP-1, ICC figure); S (shrinkage densities, checks); W (ICC figure) | B |
| rv-R6 | How much recognition error can each word-based measure tolerate? | Seen transcripts; confusion profile of the seen bridge pairs | Injected substitutions, deletions and insertions at 0-20%; estimate relative to clean; injected rate at which a creator mean moves 0.2 between-creator SD; creator-specific error scenarios | One curve per measure; tolerance table | M (tolerance figure); S (table, scenarios) | B |
| rv-R7 | Where do the recognizer's inserted phrases and seams sit, and how good are the rules that remove them? | GRID outputs; seen segments | Per-window probability of the thanks phrase by speech status and phase; creator prevalence; rate per speech hour; precision bound from phase counts; onset density and word probability by phase; segment-start phase histogram; everything with the isolated-segment rule off | Histograms against a uniform baseline; leave-one-creator-out ranges | M (figure, rule table, abstract sentence); W (artefact card) | B |
| rv-L1 | What kinds of recordings do the channels publish (interim, probability sample of development creators)? | 96 recordings of 48 development creators, 2,500-word windows | Kinds and claimed-voice bands; creator-weighted shares of recordings and speech hours with intervals; two-model kappa; run-to-run stability; creators with no recording at the 25% threshold, with its range over models and thresholds | Shares with intervals; no tests | M (kinds table; replaces "17 of 34"); S (stacked bars); W (kinds distribution) | B; superseded as the census by LAB-K, and both are reported |
| rv-L2 | How much does the recognizer move the labels? | About 24 development-creator bridge pairs | Flip share of words (voice) and units (asks) between the two transcripts against the run-to-run flip share; the withdrawn asks unit rule as a withdrawn row | Intervals per instrument | S | B |
| rv-L3 | How many windows hold non-language or pseudo-words? | Seen 30-s windows | Flag rule fixed on development creators; model-read precision against unflagged windows; flagged minutes over creators; lexical measures with and without flagged windows | Precision with Wilson and creator-bootstrap intervals | S | B |

### 6.2 Second-round programme: the built part (B; label "Exploratory, panel round 2")

Built on seen creators (and on dates, durations and counts of all creators where stated), verified where the panel
digest says so, and fixed as the digest records. Reported in full as built, including the disputed rows in the form the
digest gives them and the open verifier notes as caveats.

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| TABLE | What is known about each recording outside its transcript, at which evidence level? | Inventory, date table, local metadata (seen text fields only); dates and durations of all creators | Id repair; coverage by group, field and date-evidence level E0-E3; composition of the confirmed panels A and B and the estimated panel | Census | S; M via rv-D1 | B |
| CAL | Are the remaining registered rules centred, calibrated at the creator level, covering and powered? | Seen creators; label-free analogues | Parts a-e, g, h: null centre and spread; creator-level placebo rejection at 0.05, 0.005 and the first Holm step; coverage of four interval procedures; planted-effect recovery; minimum n and detectable effect; half-count bias; kappa-gate operating characteristic | None (calibration) | M via rv-R2; S (full tables, p histograms) | B; part f and the label-based repeats L (CAL-f) |
| RX | Which countable wording patterns separate creators and positions in a recording? | 1,229 seen recordings of 150 words or more | Normalisation-layer counts; 10 families and their sub-patterns: hits, recordings, creators, top-creator share, split-half reliability, two estimators, shrunken rates, share of recordings with a hit; length correlations; filter on and off; position by tenths and first and last three minutes; histogram of years; cut units | Cue counts with creator intervals, no tests; position curves as built ("pointwise intervals; no family-wise control" where no band was built) | S; W (family-level distributions) | B; hold-out pass F2 (RX-H); cue-boundary part L (RX-CB) |
| GRID | How much of each timing measure does the 30-s decoding grid make, and how right is each filter rule? | 1,284 seen recordings of the English-only model | Grid-made share of pauses; four seam rules; filter phase histograms and precision bounds; isolated rule off; short-segment scan counts; bridge re-analysis | Creator bootstrap and leave-one-creator-out ranges | M via rv-R3 and rv-R7; S | B |
| DC | Inside the weeks and months a channel covers, are recordings close in time more alike? | Seen English transcripts of 300 words or more; panels A, B, estimated | Primary (pre-specified): centred TSIM similarity, 0-7 days minus 31-183 days, panel B; lag curves; weekly beat; slope distribution against G; calendar heat maps as distributions; panel composition | Primary pre-specified; curves with the G band; the 19 word-measure semivariances "description only, no family-wise control"; the withdrawn pooled imputation row listed as withdrawn | S; W (lag curve) | B; TC-code rows N; names-mask v2 rerun as a row N; hold-out replication F2 (DC-H) |
| SD | How often do channels publish on the same date beyond the quota and weekday habits, and are such recordings more alike? | (a) dates of all creators; (b, c) seen transcripts | (a) co-publication against R-WK with rows; (b) positive control first, then the pre-specified anchor-matched contrast (within 3 days minus 14-60 days) against the L and G bands, with every row of the pre-specification and the event proxy; (c) estimated panel at month scale; (d) H7 input | One primary; every row in the table with its pre-specified or post hoc status; the period split labelled post hoc | S; W (excess by band; calendar strip as in section 3) | B; hold-out replication of the period split F2 (SD-H) |
| CM | Do topics and measures move together across channels by month? | Seen creators, months June to November 2026 | Common shares against the within-creator shuffle, both positive controls on every panel, F25 admission primary and first-run admission as a row; week level as detectable share; co-movement within channels | Permutation maximum (built); the finding "no month measure is interpretable under the gate" is reported as such | S | B; TC-code rows N |
| TM | Which recurring vocabulary clusters are reproducible, and how is each channel's talk spread over them? | 14,152 windows of about 300 words, 71 seen creators | Stability by K; topic table with neutral labels, effective creators, top-creator share, between-creator shares, stable flag; channel-leak statistic against shuffles; split-half ceiling; topic shares by position | Shuffle references; position display as built (pointwise) | S; W (topic table with neutral labels) | B; hold-out transform F2 (TM-H) |
| CH | How is each measure distributed across and within channels, and do patterns, topics and words tell the same story? | 1,176 seen recordings of 71 creators; 40 measures | Between-creator variance shares, reliability, counting noise; distinctiveness as a distribution; Mantel agreement of the views; partition stability; span correlations by panel; fixed group comparisons | Expected-by-chance count beside the span correlations; Mantel and group comparisons by creator permutation; distributions only in public | S | B; TC rows N; hold-out replication F2 (CH-H) |
| COR | Which measures go together across channels, which within a channel, and where do the levels differ? | 24 measures, 276 pairs; 71 and 69 seen creators | Two-level heat map; pairs whose levels differ; partial versions on log words; fragile near-threshold pairs flagged | Permutation maximum (999) at each level (built); false discovery rate as a screen only | S; W (heat map) | B; TC, PT and META rows N |
| META | How do channels schedule and size uploads, and what goes with more views inside a channel? | (a) dates and durations of all 101 creators; (b, c) seen recordings | (a) gaps, spans, burstiness, weekday and hour concentration with a null band, lengths, the newest 20 against the catalogued list; (b) field coverage; (c) within-channel engagement: fixed-effects slopes, variance partition, feature forest plot with pooled estimates | (c) permutation maximum within creator (built), with Monte Carlo error; (a) weekday-by-hour counts against a uniform-null band | S; W (rhythm distributions only) | B; non-seen audience F2 (META-H) |
| PT | What does the page around a recording declare and ask for? | Seen descriptions, chapters, tags, titles (titles and text stay private) | (a) regex cue shares with model-read precision; (b) written asks by class, creator-balanced, with intervals and run agreement; template shares labelled as pooled; the mask-v1 breach note | Shares with intervals; no tests | S; W (ask-class shares) | B; parts c and d L (PT-cd); hold-out pass F2 (PT-H) |
| NAMES | Which word forms spell the same being, collective or place, and how much do stems and masks miss? | Seen forms with contexts (model-adjudicated) | Public family table (variant counts, exact-stem share, creators and recordings with and without variants); decoy false-merge rate; reader agreement; residual leak per mask | Exact and resampling intervals | S | B; hold-out forms by code F2 |
| TIME | What are dates and time expressions used for, and how far ahead do forecast-role years lie? | 9,354 seen hits | Role shares under both readers with the two-phase row; agreement and stability; horizon histogram (panel B; estimated panel "too few"); rule-anchored view | Shares with intervals | S | B; middle-model re-read R (bought in tier 4 of the money priority, capped at 0.20 USD, registry 03:08); hold-out pass F2 (TIME-H) |
| RXP | How often is a pattern hit what its name says, and how much do the patterns miss? | 2,136 seen hits; 400 recall windows | Precision per sub-pattern (hit-weighted primary, creator-equal beside it), gate counts under both, revisions on fresh hits, recall against one model reader for six constructs, reader agreement | Every sub-pattern reported; gates fixed before reading | S | B; B1 and B3 revisions X (not bought, registry 03:08) |
| TC | In codes that mean the same for every channel, what share of talk is each subject and segment kind? | 386 seen windows read three times | Reliability per code; stage-1 gate under readings A, E and D with the freeze time; the stop decision as made; noise floors | All codes reported; P4 applies | S | B (development and stage 1); stage 2 X (not bought, registry 03:08); hold-out pass X (did not qualify under any reading) |
| NE | Which being or group does a recording present as speaking, and do channels refer to the same datable events? | 200 seen windows (pilot) | Named-source shares under both models, first-person source share, datable-reference shares, kappa, go rule | Shares with intervals | S | B (pilot); full pass L/N (NE-F); hold-out F2 (NE-H) |
| DIR | Do recordings tell listeners what to do about health, money, preparation or practice? | 200 seen windows (pilot) | Creator-equal incidence by class, prefilter recall, reliability, the go or no-go note (no-go) | Shares with intervals | S | B (pilot); full pass X (go rule failed on prefilter recall) |
| KA | Do the labellers respond to what their codebooks admit, and not to register, the voice around an ask or the other part of H2? | Constructed texts from development windows | Per instrument and arm: label flips, recoveries and joint misses with creator-clustered intervals; audit arms KA-L, KA-D, KA-E, KA-C and K4n; effort arm; the sentences printed beside each instrument; costs | Differences between cells only; every arm run is reported | M (verification figures per instrument, via rv-D5 and LAB); S (full tables) | B; arms not bought (KA-X, confidence arm) X |

### 6.3 Second-round programme: the parts not yet run

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| HUMAN | How often are the voice labels right when judged by a person? | - | - | - | S (status table) | X: not run, the owner declined a person's check (A8); its place is taken by VER-3R and KA |
| CAL-f | How many creators are eligible for each within-creator contrast, and do the calibration results hold on labels? | Seen first-round labels | Eligibility count with projection to the English hold-out creators and interval; label-based repeats of CAL a-d | None (calibration) | M via rv-R2; S | L |
| PT-cd | Do written and spoken asks coincide, and do creator-written chapters mark structural changes? | Seen labels, seen chapters | (c) shares with written, spoken or both asks per class, between-creator shares apart from the within-creator association (within-creator permutation); (d) share of chapter starts within 30 s of a TC code change or a voice-map boundary, against circular shifts | Within-creator permutation; shift band | S; W (paired ask-class shares) | L; the TC part N |
| RX-CB | Do framing cues sit at model voice boundaries? | Seen cue hits and voice labels | Distance from each cue hit to the nearest boundary against circular shifts (999); share of claimed-voice spans opened by a cue; placebo lists | Shift band; one curve | S | L |
| MTMM | Does agreement within a construct across methods exceed agreement across constructs within a method? | RX, NAMES, NE, TC, PT, first-round labels | 4 x 4 creator-level agreement matrix with intervals; convergent and discriminant pass list; timeline rows of TL-7.8 | Pattern read as a whole; every cell shown | S; M (one sentence per construct) | L |
| NE-F | NE full pass | Remaining seen windows | Creator-by-family table (public as family counts of creators); title-speech agreement; relative recall; set intersection of families; shared-reference excess against L; reliability; the 30% criterion on claimed-voice windows | Permutation and L references | S | L/N (waits for the frozen NAMES table; a conditional line under the registry's money rule of 03:08) |
| TC-2 | TC stage 2 and the TC-code rows of DC, SD, CM, CH and COR | Remaining seen windows | As TC, with the noise floors and run-to-run agreement printed beside every use | As each item | S | X: not bought (registry 2026-11-21 03:08, reading A stands) |
| HR | Do the hold-out results of H6 and, where released, H2 and others hold under every reading, a second coder and rewordings? | Hold-out labels after freeze 2 | (a) H6 cell under three readings per event with exact intervals; asks missed by the small finder, by voice; (b) H2 under two coders; (c) every estimate under three wordings; confusion and wording-stability tables | Rows beside the primary; "robust" only if every row agrees | M (beside the registered rows); S | F2; (b) and (c) by their release rule (registry 2026-11-21 02:50 and 03:08); a row not released is reported as "not released" with the figures that decided it |
| NONEN | Which topic and source codes survive translation, and where do the non-English creators sit? | Non-English hold-out and other-group transcripts | Agreement between original and English views per item; profiles beside the nearest English creators, as a case panel in its own units | Description only; never pooled or tested | S | F2 |

### 6.4 ENTRY: when a channelled source enters

Version 1 (patterns entry-patterns-v1, rule entry-rule-v1) was frozen before any check-creator hit was read, and is the
version of record. Version 2 (entry-patterns-v2, entry-rule-v2) was revised after the model check; every output run under
it is reported beside version 1 as a revision row, with its in-sample status stated (P5). Everything is a cue count with
model-read precision.

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| ENTRY-E4 | How common is a found entrance? | 1,229 seen recordings | Creators with none; distribution of creator shares of recordings with an entrance (binned); creator-balanced share with interval and leave-one-out range; I against we | Shares with intervals | S; W (binned distribution) | B (v1) |
| ENTRY-E1 | When does the source enter? | Recordings with an entrance | Median first entrance in minutes and as share of running time, by length third; how entrances open | Intervals per cell | S; W | B (v1) |
| ENTRY-E2 | Where in a recording does each cue family sit? | Seen hits | Family by tenth of running time rates per 1,000 words; whole-recording rates | Built with pointwise intervals ("no family-wise control"); a permutation-maximum companion under within-recording circular shift may be added | S; W | B (v1) |
| ENTRY-E3 | What changes at the entrance? | Recordings with 5 or more minutes on both sides | Change in I, we and you forms and pace over 10 minutes after against before, with intervals and leave-one-out ranges | Four measures, all reported; a description, not a finding | S | B (v1) |
| ENTRY-T | Which cue templates and which persons go with which source groups? | Seen hits | Family table (hits, recordings, creators, check precision); masked templates; I against we by source group | Public templates and groups only with 5 or more creators (smaller pooled as "other") | S | B (v1) |
| ENTRY-MC | Are the patterns and the entrance rule right, by model readers? | Seeded samples of hits, entrances and recall windows | Precision per family and sub-pattern (sample share, weighted, creator-balanced; check-creator rows); entrance-rule accuracy and kinds of error; recall windows; agreement with pilot voice labels against their noise floor; reader agreement; known-answer items; the post hoc supplement labelled post hoc | Wilson and creator-bootstrap intervals | S | B |
| ENTRY-V2 | What does the revised version change? | Seen hits | In-sample carry-over of the model-check verdicts to version 2; every ENTRY output above under version 2, beside version 1; precision of version 2 on fresh hits only if a new reading is made | As above; labelled "revised after the model check" | S | B (in-sample carry-over); full-data rows when run (code only); fresh reading X (no further ENTRY model call, registry 03:08) |
| ENTRY-H | The same on hold-out creators | Hold-out transcripts after freeze 2 | Every ENTRY output above, under each frozen version | As above | S | F2 |

### 6.5 Verification layer (amendment A11)

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| GATES | Which instrument gates were met, and what did each revision change? | Pilot, gate and rerun samples on seen creators | Every gate of the annotation plan (A to E) and VG-0 to VG-9: value, interval, floor, pass or fail, revisions spent, the decision taken and its UTC time, including the instruments that failed | Every gate reported, including failures | M (summary in rv-D5); S (full table) | B for the gates run; L for the rest |
| VER-A | Where the two cheap readers split, how does a blind third reader side, and how far does it depart on agreed decoys? | Set W, 32 development creators | Shares sided with each reader and with neither; decoy departure; form and effort arms; repeats | Shares with intervals | S | B (pilot) |
| VER-GC | Does the published free-text guided form beat the typed form? | Development creators | Two-model agreement, stability, invalid answers and planted recovery under both forms; the rule's outcome | Rule fixed before the run | S | B |
| VER-SHARD | Do smaller shards recover planted decisions better at acceptable cost? | Development windows | Recovery, stability and cost per instrument and shard size; the rule's outcome | Rule fixed before the run | S | B |
| VER-3R | Does a reader of another vendor, reading blind, agree with the OpenAI readers? | 200 units of the four-stratum sample on check creators | Kappa and specific agreement against the OpenAI majority, with intervals; VG-6 outcome; direction of disagreements | Combined gate rule | M (one line beside H1, H4 and H6 and in rv-D5); S | Built and sealed until freeze 1; reported in full when unsealed, whatever it shows |
| VER-ADJ-G | The third reader on the check-creator gate samples | G-seen gate samples before freeze 1 | As VER-A, per instrument, with VG-4 and VG-5 outcomes | As VER-A | S | L |
| VER-ADJ-H | The third reader on the hold-out reliability sample | R-hold after freeze 2 | As VER-A | As VER-A | S | F2 |
| VER-DEP | What do three or more readers imply about shared errors? | All readers and rules per instrument | All-same share; effective votes; latent-class error rates (labelled heuristic); DMM correction where three groups exist; partial-identification bounds; threshold distance | Every instrument reported | S; M (bounds beside the registered rows) | L; hold-out bounds F2 |
| VER-CAL | Does stated confidence track known answers? | KA items and adjudicator answers | Reliability curve, expected calibration error, Brier score; consistency-based confidence | One curve per source | S | L where a confidence field exists; the KA confidence arm was not bought (registry 2026-11-21 02:40), so that part is X |
| DR-2 | How often does a second, other model agree on forecast candidates and sentence units? | 300 forecast candidates and 400 sentence units on seen creators (registry 2026-11-21 02:50) | Agreement with intervals; confusion tables | Every code reported | S | L |
| VER-MV | Every multiverse row and the tipping-point table for every registered hypothesis that runs | Registry procedures | Rows M1 to M13 where they apply; tipping-point table with KA, third-reader, decoy, latent-class, cross-vendor and bounds figures | Governed by the registry; listed here so that no row is left out | M; S | F2 |
| VER-NEXT | Rerun of the frozen hold-out pipeline on the next model snapshot | - | Agreement of verdicts | - | S | N (unfunded, optional) |

### 6.6 Prediction timeline (amendment A11)

By the registry decision of 2026-11-21 02:50 the timeline follows **methodological agnosticism**: it reports what was
predicted, for when, and whether an outcome would be observable, never whether a prediction came true; source types
(non-human entity, deceased person, higher self) are separate rows. The resolution step (TL-RES), the resolver arm of
TL-KA and analysis 7.6 are therefore not run for the study. The timeline pilot had already used the resolver before that
decision; the pilot is reported as a method pilot, with the number of real cards sent, the known-answer results with
their gate outcome, and without verdicts on real statements, as decided at 02:50 and stated here. (In the pilot no real
card was eligible for resolution; three matured cards that the card writer had called not resolvable were sent to the
resolver as a diagnostic, and of ten constructed known-answer items the eight that the card writer called resolvable
were sent to the resolver.)

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| TL-P | Does the timeline pipeline work? | Set W forecast pilot (development creators) | Card classes and R0 reasons; event types; flags; hindsight index; clusters at both thresholds; dry runs of analyses 7.1 and 7.2; the resolver's known-answer items with the gate outcome; the count of diagnostic cards sent | Counts | S | B (pilot; see the paragraph above) |
| TL-BUILD | What is dated, how, and for when? | Seen first-round forecast labels | Rows, windows, classes (absolute or relative, statement or frame, recurring), horizon, lead, width; status (pending, too recent, matured); due-date calendar; undated, open and recurring lanes; source-type rows; confirmed and estimated upload dates apart with composition tables | Counts and distributions; calendar cells merged to 5 or more channels | S; M (one paragraph); W (counts only) | L |
| TL-SPEC | How many statements are resolvable as worded, and why not? | Seen cards (frozen before use) | Resolvable share; R0 share by reason (analysis 7.5); card-writer gate; hindsight index (VG-9) | Shares with intervals | S; M (resolvability shares) | L |
| TL-7.1 | Do horizons recede within a channel? | Absolute statements of eligible channels | Slope of target midpoint on upload date, pooled by random effects, against within-channel permutation of upload dates (9,999) | One estimand; eligibility rule as frozen in the timeline procedure (the protocol's and the pilot's rules differ; the freeze names one primary and the other is a row) | S | L; reported as "not run: no eligible channel" if none qualifies |
| TL-7.2 | Do channels point to the same narrow future windows beyond the calendar? | Narrow windows across channels | Pair overlap against a horizon-preserving redraw (4,000) and a circular shift; positive control first; absolute-only and year-ahead rows | Positive control gates the reading; minimum 30 windows from 10 channels | S | L |
| TL-7.3 | Do channels restate, postpone or advance their own predictions? | Same-channel pairs in one cluster | Counts with exact intervals | Minimum 20 after-expiry pairs from 8 channels | S | L; probably "not run: too few pairs" before the replication wave |
| TL-7.4 | Do specificity and hedging change with horizon? | Seen statements | FC parts and FD commitment against horizon, within creator | A moderator beside H2, never part of it | S | L |
| TL-7.7 | How many dated statements take their window from a talk-level period? | Seen statements | Share by month of upload | Counts | S | L |
| TL-7.8 | Do three methods of time-window measurement agree? | TIME and RX hits, FC time part, FE window | Rows added to MTMM | As MTMM | S | L |
| TL-7.9 | When do pending windows become checkable? | Seen statements | Due-date calendar | Counts | S | L |
| TL-RES | Resolution of passed windows by a model with web search, with placebo windows | - | - | - | S (status table) | X: not run, methodological agnosticism (registry 2026-11-21 02:50); analysis 7.6 likewise |
| TL-H | The timeline outputs above on hold-out creators | Hold-out statements | As above | As above | S | F2 (after the timeline procedure freeze and freeze 2) |

### 6.7 Accuracy anchor and re-decode (registry decision of 2026-11-21 02:50)

The recognizer runs locally on this machine's GPU over archived audio only; no audio is downloaded and nothing is sent
outside. Before any word error rate is computed, two things are fixed and hashed: the class of every third-party text kind
(made or edited by people; machine-made; unknown, which is treated as not made by people), and the text normalisation of
both sides (case, punctuation, numerals, fillers, contractions, the artefact filter on and off).

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| BR-b | How far is the recognizer's text from text made or edited by people? | Seen recordings among the 214 that carry third-party text | Word error rate against texts made or edited by people only, by stratum (text kind, length band, pace third, recognizer model), with creator-bootstrap intervals; substitution, deletion and insertion shares; errors on numerals, years and capitalised names; machine-to-machine rows against automatic captions, against publisher texts of undeclared origin (treated as not made by people) and against the project's earlier recognizer text of the same audio (a reproducibility row), each labelled "agreement of two machines, not an error rate" | All strata reported; strata with fewer than 5 creators pooled in public; the headline rate goes into the abstract whatever its value | M (anchor table and abstract sentence); S (strata, error kinds); W (headline with interval) | R on seen creators; hold-out and other-group part F2 (BR-b-H); reported as not run, with the reason, if the human-made texts cover fewer than 5 creators |
| BR-y | Are years and numbers right against the references? | BR-b pairs | Exact and normalised match of years and numbers (meta-review nlp-R14 parts a and c) | Counts with exact intervals | S | L (needs the TIME and forecast freezes) |
| BR-GS | How much do the seam measures move when the decoding grid is shifted? | 40 seen recordings re-decoded with a shifted grid | Change in thanks-phrase segments, isolated segments, pause measures and word measures between grids, in between-creator SD units, with creator-bootstrap intervals; check of the positional precision bound | All measures reported | M (beside rv-R7); S | R |

### 6.8 First-round labels as model-coded descriptions (seen creators)

These describe what the frozen instruments find on seen creators. They are not hypothesis quantities. Every line says
"model-coded; verified by <list with figures>; not validated by a person". Public forms are code-level distributions over
creators; no per-recording label is published.

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| LAB-V | How much of each recording is in which voice? | Seen voice labels (middle-model subset for voice-dependent descriptions; small-model rows beside) | Creator distributions of word shares by voice code, by recording format, under the primary and the other own-voice definitions; relayed voice alone flagged "below the reliability floor"; the punctuation-and-case sentence | Descriptions, no tests | M (one description table for all instruments); S; W | L |
| LAB-A | Which asks occur, in which voice? | Seen ask labels | Creator-balanced shares by class and voice, with intervals | As above | M; S; W | L |
| LAB-F | Which forecasts occur, how checkable and how committed? | Seen forecast labels | Class and scope shares; checkability parts; commitment; time expressions; share flagged by the shared-wording rule | As above | M; S; W | L |
| LAB-S | What do the sentence codes show? | Seen sentence codes | Group shares by creator, with cut units shown apart | As above | S; W | L |
| LAB-T | How are recordings presented in their titles? | Seen title labels (titles stay private) | Presentation and family shares over creators | As above | S | L |
| LAB-K | What kinds of recordings are there (census)? | All seen recordings (phase 7f) | As rv-L1, on all seen recordings | As above | M (with rv-L1 beside it); S; W | L |
| LAB-H | The same descriptions on hold-out creators | Hold-out labels | As above, apart from the registered tests | As above | S | F2 |

### 6.9 H3 after its closure

| Id | Question | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| H3-SEEN | The seen-creator H3 contrast (published) | Seen creators | As in `results/h3-seen-exploratory.json`, with the recentred value of CAL beside it | One estimand | S | B |
| H3-X | H3 at the creator level on the hold-out, without the recordings that overlapped the first panel's pilot | Hold-out, frozen H3 code, run once after freeze 2 and logged as a contact | Exact creator sign-flip p, leave-one-creator-out range, random-effects pool with seen creators, the same without the pilot-overlap recordings (meta-review MR-05 hold-out parts and V13) | One estimand with rows | M (in the H3 table); S | F2; never a confirmatory verdict (A6) |

### 6.10 Registered exploratory questions E1 to E13 (hypotheses file, section 14.3)

Each keeps the method fixed there. Hold-out parts run after freeze 2.

| Id | Question (short) | Data | Measure and display | Multiplicity | Place | Status |
|---|---|---|---|---|---|---|
| E1 | Is the inserted thanks phrase tied to the decoding window or to silence? | Seen recordings | Per-window insertion chance in the slower against the faster half of a recording's windows, equivalence within a factor of 1.25 | One estimand | S | R (not built as specified; parts of it are in rv-R7) |
| E2 | Does a creator's claimed-voice profile resemble other creators' claimed voice more than the creator's own voice? | Seen voice labels, solo talks for own voice | The similarity difference, creator-balanced | As fixed | S | L |
| E3 | Is articulation rate higher at the edges, and does second-person address rise over a recording? | Seen recordings, trimmed by 180 s | Edge against middle pace ratio; first against last tenth address | One estimand each | S | R on seen creators (not built as specified); hold-out part F2 |
| E4 | Is slowing in the claimed voice carried by silence or by articulation? | Seen and hold-out voice labels | The exact split of log rate, under the seam rule | Conditional on H1 showing at least 5% slowing | S | L/F2; "not run: condition not met" if H1 is not run or below 5% |
| E5 | Silent against filled hesitation by voice | Seen voice labels | Described beside H1 | Description only | S | L |
| E6 | Is the claimed voice more formulaic? | Seen voice labels | Formula coverage by voice; creators surviving the length rule printed first | As fixed | S | L |
| E7 | Do opening and closing frames found on seen creators transfer to hold-out creators? | Inventory from seen creators, frozen and hashed before freeze 2; hold-out edges after freeze 2 | Coverage of edges against matched middle windows, circular-shift reference; absolute coverage | As fixed | S | Inventory before freeze 2; scoring F2 |
| E8 | Does a claimed source carry a tempo? | Seen labels and source families | Articulation rate and pause share in the source-family features | Description only | S | L |
| E9 | Does phrasing travel with a claimed source? | Seen and hold-out transcripts, names masked | Shared distinctive runs with same-family against other creators; edge-trimmed row | Exploratory count | S | L/F2 |
| E10 | Do asks follow urgency? | - | - | - | S (status table) | X: not run, DIR's go rule failed (no threat-statement full pass) |
| E11 | Does conspiracy vocabulary follow the claimed lineage? | Seen title groups and term families | Between-creator differences with intervals; the equivalence arm | Description with intervals | S | L |
| E12 | Do dated titles deliver dated statements? | Seen titles and forecast labels | Delivery rate with interval | An estimate, no test | S | L |
| E13 | Where do the non-English creators sit on language-free timing? | Non-English hold-out and other-group creators | Count of placements outside the 95% prediction interval of a new English creator, on measures the bridge allows | A stated count, no test | S (public only if 5 or more creators are described) | F2 |

### 6.11 The paper review's "later" list (meta-review section 5.3)

Each id is reported in the status table with its status. Multiplicity follows section 4 and the review's own
specification of each item. Rows that will run in this study:

| Id | Question | Data | Measure and display | Place | Status |
|---|---|---|---|---|---|
| MR-18c | Does voice-label timing leak into the timing contrasts? | Seen labels | Timing-leak test as specified by the review | S | L |
| MR-18d | What do the label-based contrasts give under permuted labels? | Seen labels | Label-permutation null | S | L |
| nlp-R7 | How sensitive are span results to boundary jitter? | Seen labels | Results under jittered boundaries | S | L |
| nlp-R9 | How much do checkability and commitment share wording? | Seen forecast labels | Share of statements flagged by the fixed rule of the registry decision of 02:50, by part | S | L |
| nlp-R10 | How often is a world claim a self-presentation? | Seen sentence codes | Share of units next to a self-naming cue, and H5's three Q2 assignments as description | S | L |
| nlp-R11 | Lexical against modal hedges | Seen forecast labels and RX | Rates by hedge kind | S | L |
| nlp-R13 | Capture-recapture recall of the finders | Seen labels of two finders | Recall estimate with interval | S | L |
| CSS-5 | Source typology | NE, NAMES, voice labels | Source types over creators | S | L |
| CSS-10 | Economy typology | Ask labels, META subscriber bands | Types over creators | S | L |
| CSS-11 | Legitimation by voice | Seen labels, a new codebook | Rates by voice | S | N (needs a new codebook and money) |
| CSS-12 | Conspirituality and directive census | RX families, E11, DIR | Census over creators | S | L in part; the directive part X (DIR no-go) |

Rows that will not run in this study, reported as not run with the reason: SR-07, V8, CSS-9, nlp-R4 and MR-21 (an
independent voice detector and audio tagger: no new audio-analysis packages); SR-06, MR-22 and V7 (a recognizer of another
family and a forced aligner: same); SR-09, nlp-R6 and CSS-3 (diarisation, speaker embeddings, synthetic-voice screen:
same); SR-08 (acoustic arm: same, and biometric); SR-21, MR-24 and nlp-R5 part a (re-probe of the creator-rule language
files: no GPU lease for it); SR-02, MR-17 (voice part), nlp-R17 and CSS-16 (a person's coding: A8); SR-10, nlp-R15 and
MR-19 (a local open-weights reader: no model download; VER-3R is the cross-vendor reader that exists); MR-16, SR-12, CSS-6,
SR-13, CSS-1, CSS-2, CSS-8, CSS-13, CSS-17, CSS-18 and MR-13 (new data, a new cohort or a comparison set: downloads are
closed by the owner); SR-16, V20, CSS-19 and V26 (acts of the owner: external time stamps, field hypotheses, ethics); V25
(a reproducibility capsule: engineering, not a result). MR-09 is this file.

### 6.12 Catalogue experiments (README section 4): where each is carried

| Experiment | Carried by | Not carried |
|---|---|---|
| T1 coverage ledger | TABLE, rv-D1 | - |
| VP variance partition | rv-R5, CH | - |
| EB shrinkage and rank intervals | rv-R5, CH | per-creator values (private only) |
| CA coverage audit and power | CAL, rv-R2 | - |
| QD quality dependence | rv-R6 (stage 1), rv-R7, GRID, BR-b, BR-GS | stage 2 against hand transcripts (X: A8) |
| HR hand reference | KA, VER-3R | the human study (X: A8) |
| SP speaker separation | - | X: no packages |
| BR bridge | results README (part a, published), rv-R3, BR-b | - |
| SD serial dependence | rv-R5 (ordered splits), DC | the variogram grid (X: order is not time, R10) |
| PO position curves | H3 (registered), rv-R1, rv-D3, RX, TM, ENTRY-E2, E3 | per-creator position heat maps (private only) |
| LX lexical diversity | CH (MATTR), E6 | - |
| SG delivery-state segmentation | LAB-V, rv-L1, LAB-K | private timeline strips |
| RH rhythm | GRID, CH, rv-R5 | the delivery-plane typology (N) |
| CX content axis | TM, CH, NAMES, NE | - |
| SM creator similarity | CH (distinctiveness, similarity, partitions) | - |
| GB grounds for belief | CSS-11 | N |
| SV source or speaker | NE-F, H9 (registered), E8, E9 | - |
| FL forecast ledger | LAB-F, TL-BUILD, TL-SPEC, timeline analyses | the accounting of passed forecasts (X: agnosticism) |
| AK ask ladder | LAB-A, PT | - |
| TP title cue against content | E12, META (c) title cues | - |
| EV world events | SD event proxy, NE datable references | event-study panels (N) |
| LG language case panel | NONEN, E13, rv-D7 language pooling | - |
| SY calendar synchrony | SD | - |
| FA first-appearance table | - | X: not run (left-truncated window; no power) |
| RW replication wave | - | X for this study: downloads closed |
| CS comparison set | - | X for this study: new data |
| SL selection sensitivity | rv-R4 (stage 1) | stage 2 (X: new data) |
| PF internal profile page | - | private by design; never a place of report |

## 7. Notes on particular outputs

- **The H7 margin and the A10 text** draw on SD (d) and CAL. They are registry inputs; the outputs themselves are
  reported as listed.
- **TC's stop decision.** Reading A stands and stage 2 is not bought (registry 2026-11-21 03:08, decided after the
  stage-1 results and stated so). Readings A, E and D are all reported with the freeze time and the decision time (P4);
  TC-2 is reported as not run with that reason.
- **Recognizer.** Timing, pause, filler and contraction outputs run after this plan use only transcripts of the
  English-only recognizer; the 9 seen transcripts of the other model, and any transcript of unknown model, form one
  model-stratified row (registry 03:08). Built outputs whose base includes those 9 transcripts (for example rv-D3 and
  rv-R5 on 1,293 seen transcripts) are reported as built (P5), with an English-only version as a row where one exists.
- **Public topic labels.** Style topics and topics whose top creator holds 0.20 or more of the weight carry neutral
  public labels (registry 03:08).
- **NAMES-mask v2.** DC, SD and CM were pre-specified on TSIM with the names-v0 mask. Their v0 results stay primary;
  reruns with mask v2 are rows beside them.
- **Pattern templates and calendar strips** (ENTRY-T, SD-1) are published only in bins and categories of 5 or more
  creators, with the calendar-strip rule of section 3.
- **Money.** The registry's priority for the money left under the 130 USD stop (2026-11-21 03:08) decides which paid
  lines run. Lines it does not buy are reported as not run with that reason: TC stage 2 and its hold-out pass, the DIR
  full pass, the RXP B1 and B3 revisions, and any further ENTRY model call. Conditional lines (HR b and c, the NE full
  pass, a KA re-run) are reported as not run if their condition or the money rule stops them.
- **Voice-based descriptions.** By the registry decision of 02:53, seen descriptions that depend on voice come from the
  middle-model subset, with the small model's known weaknesses beside them; relayed voice alone is reported with the flag
  "below the reliability floor" (voice revision 3, registry 02:55).
- **CAL's numbers** were held private until review; the review is now the lead's under the delegation, and they are
  reported through rv-R2 and the supplement as listed.
- **Hold-out exploratory replications** (DC-H, SD-H, CH-H, TM-H and the rest of section 8) print the seen and hold-out
  estimates side by side with the balance table, and never a pooled estimate.

## 8. Outputs that wait for freeze 2

All are run by code frozen in the freeze-2 record, once each, and logged as contacts (section 5).

| Id | What |
|---|---|
| rv-D2-H | Transcript-derived balance covariates of the hold-out |
| rv-D3-H | Positional time-without-speech display including hold-out creators |
| H3-X | Creator-level H3 statistics on the hold-out, with and without the pilot-overlap recordings |
| HR | H6 census; H2 second coder and rewordings by their release rule |
| LAB-H | Model-coded descriptions of the first-round labels on hold-out creators |
| VER-ADJ-H, VER-DEP (hold-out bounds), VER-MV | Third reader on R-hold; bounds; every multiverse and tipping-point row |
| BR-b-H | Word error rate on hold-out and other-group recordings with third-party text |
| RX-H, TIME-H, PT-H, NE-H, TM-H, ENTRY-H | Hold-out passes of patterns, time roles, page text (including non-seen page fields), named sources, the topic transform and the entrance rules |
| DC-H, SD-H, CH-H | Exploratory replication of change inside channels, the same-date period split and the channel atlas |
| META-H | Audience counts and page-field presence of non-seen recordings |
| META-169 | The 169 cloud-only metadata objects, read once read-only after freeze 2 and logged (registry 2026-11-21 03:08); seen fields join TABLE and META, non-seen fields join META-H, as rows |
| NAMES (hold-out forms) | Variant forms added by code only |
| NONEN, E13 | Non-English recordings in their own language; placements on language-free timing |
| E3, E4, E7, E9 (hold-out parts) | As in section 6.10 |
| TL-H | Timeline outputs on hold-out statements (also after the timeline procedure freeze) |

Not run on the hold-out: the TC hold-out pass (it did not qualify under any reading) and the DIR full pass (no-go).

## 9. Status table at report time

The supplement carries one table with every id of section 6, its status (reported; not run with reason; not released
with the figures that decided it; superseded with a pointer), its place, its UTC time of run and the hash of its code.
It prints how many outputs this plan lists, how many were reported, how many were not run, and how many the main text
discusses, so that a reader can see what was left in the supplement and why (registry A2).
