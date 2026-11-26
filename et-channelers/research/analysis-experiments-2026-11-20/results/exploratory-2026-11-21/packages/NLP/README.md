# NLP: self-presentation, hedge kinds and finder recall (nlp-R10, nlp-R11, nlp-R13)

Exploratory (registry A2); not a test of H1-H10. Added after the exploratory reporting plan: these outputs were built in the
second wave of the exploratory round (lead's decision D4 of 2026-11-22), on code written then (status L of plan section
6.11, the paper review's "later" list). Seen creators only (71 creators; 1,293 recordings). No hold-out or other-group file
was opened, so no hold-out contact was made. No model was called. Place: supplement (S).

All labels here are model-coded and not checked by a person. Agreement between models is agreement, not a measure of correctness; the
recall in nlp-R13 is the estimated recall of the union of two finders, from the overlap of their items (capture-recapture)
under the stated assumptions, not a measure of correctness. Every
interval computed here is a 95% percentile interval from 2,000 creator-bootstrap draws (creators resampled with
replacement); the verification figures quoted in the CSVs' description lines carry their own levels (mostly 90%, as each
bracket states); levels differ between packages of this round (lead's decision D18). Rows that repeat a LAB row (the same
per-creator values) print LAB's cells, computed with LAB's bootstrap seed. Every CSV carries its own description lines,
including the verification that exists for each instrument, and its small-cell rules.

Revised on 2026-11-22 (about 03:25 UTC) after the release verifiers' report: nlp-R13 now puts every row on all
recordings; the asks-of-record recall was then given only as an observed upper bound (now printed beside the registered
row, see below); LAB's printed creator counts are taken into
the count rule; and the description lines state every interval's level. The first build's tables are superseded, and
none of their figures should be printed beside these. Release pass, 2026-11-22 (about 05:12 UTC; lead's decision D34):
nlp-R13's asks of record print the registered version (Chapman's recall) as the primary row and the observed upper bound
beside it, labelled "chosen after the result".

## Files

| File | Output | What it holds |
|---|---|---|
| `nlp-r10-self-presentation.csv`, `fig-nlp-r10-self-presentation.png` | nlp-R10 | How often a world claim sits next to a self-naming cue; H5's three Q2 assignments as description |
| `nlp-r11-hedge-kinds.csv`, `fig-nlp-r11-hedge-kinds.png` | nlp-R11 | Lexical against modal hedges in forecast statements; hedge kinds; the commitment model's codes by marker; three mappings of commitment |
| `nlp-r13-capture-recapture.csv`, `fig-nlp-r13-recall.png` | nlp-R13 | Capture-recapture (Chapman) recall of two finders of the same class |

## nlp-R10: how often is a world claim a self-presentation?

The question comes from the paper review (M8): a claimed voice that introduces itself makes a statement about non-human
beings, which the sentence codebook counts as a world claim (Q1), so channelled recordings could gain world-claim units
from self-presentation alone. Built from the seen sentence codes (instrument S, the small model; LAB-S's word weights over
the coded body, the middle 80% of running time) and the voice labels' cue field. "Cue-adjacent" is H5's frozen rule
(registry 2026-11-21 02:50): the unit that holds a self_name cue of the voice label of record and the unit after it.

The voice label records one cue per span: the cue that opened the span (its type and its unit). A self-naming inside a span
that another cue opened is not marked self_name, so it is not counted here. Every share below is therefore a lower bound
on self-presentation in world claims: it counts self-naming cues as the voice label marks them.

- In the coded sample, cue-adjacent units hold a creator-balanced mean of 0.002 of a creator's world-claim words (95%
  interval 0.000 to 0.004), and 0.002 of all coded words. Leaving them out moves the creator-balanced world-claim share by
  less than 0.001 under each of H5's three Q2 assignments (as registered 0.234; Q2 merged with Q1 0.372; Q2 excluded
  0.269, with cue-adjacent units kept and left out alike); single creators' shares move more.
- A census of every unit of every seen recording (section D) puts 0.003 of a creator's words in cue-adjacent units, and
  0.580 of a creator's self_name cue units in the body that the sentence sample covers: self-naming cues, as the voice
  label marks them, are rare in the speech as a whole, not only outside the sample.
- With the paper review's wider cue set (self_name or announce cues) the world-claim share in cue-adjacent units is 0.003.
- Within voice: the middle model's rows (primary for voice descriptions, registry 02:53) rest on fewer than 5 creators
  with a non-zero value and are not printed; on the small model, 0.003 of a creator's claimed-voice world-claim words are
  cue-adjacent, and none of the own-voice ones.
- The review also asked for a confusion matrix of the two models' sentence codes; it is DR-2's (VER/public/dr2-*.csv,
  400 units read a second time). A third reader of 400 units was not run: it needs model calls, and no money is left
  under the hard stop (registry 2026-11-21 18:41).

Departures from the plan row, stated: shares are weighted by words (as LAB-S), not counted by units; H5's Q2 assignments
are described with LAB-S's word weights over all seen recordings, not with H5's sides, points or estimator; the wider cue
set, the voice split and the census are added rows. The self_name cue is a field of the voice label; no check of that field
on its own is reported. Every seen recording with coded units carries voice cues, so H5's feature-pattern fallback was not
used. The as-registered, kept world-claim and practice-and-feeling rows are LAB-S's group rows (the same per-creator
values) and print LAB-S's cells.

## nlp-R11: lexical against modal hedges

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Plan row: seen forecast labels and RX; rates by hedge kind. For every coded F1 statement (verified, duplicates removed,
commitment code present; weights 1 / inclusion probability, as LAB-F) the sentence the commitment model read is read with
RX's frozen patterns: E1 lexical hedge, E2 modal hedge (may, might, could as epistemic modals) and B3 perception report.
E1's terms are split, here, into epistemic, evidential ("I feel like", "I feel that", "I sense") and devotional ("god
willing") terms, after the paper review's point that such phrases are often evidential or devotional rather than
epistemic. Rows are cue counts: RXP's model-read precision on seen hits is 0.84 raw for E1 (a count), 0.67 for E2 and 0.633
for B3 (cue counts; Wilson 95% intervals in the CSV); the E1 split has no precision of its own.

- RX finds neither a lexical nor a modal hedge in the sentences of 0.856 of a creator's coded statements (creator-balanced
  mean); a lexical hedge only in 0.082, a modal hedge only in 0.052, both in 0.009.
- The commitment model codes a hedge in 0.163 of statements: in 0.076 of those whose sentence holds neither RX hedge, 0.619
  of those with a lexical hedge only, 0.696 with a modal hedge only and 0.816 with both. Of the statements it codes as
  hedged, 0.419 hold no RX hedge or perception marker (the model's codebook names markers that RX does not list).
- Evidential terms (0.007) and perception reports (0.003) are rare in forecast sentences; the model codes "source marker:
  PERCEPTION" on 0.022 of statements. Devotional "god willing" occurs for fewer than 5 creators.
- Counting statements coded hedged whose sentence holds only evidential markers as committed moves the committed share
  from 0.771 (as coded; LAB-F's row and cells) to 0.775. Counting devotional-only sentences as committed too changes no
  creator's share, so that mapping is not repeated. The condition row (CL or CE) is LAB-F's conditional row and prints
  its cells. These mappings use the sentence's markers, not the model's own cue quotation
  (kept only in the answer store), so they approximate the review's recode; a recode by a model was not run (it needs model
  calls; no money is left under the hard stop, registry 2026-11-21 18:41). The review's split by voice label was not built:
  the plan row names hedge kinds only.

## nlp-R13: capture-recapture recall of the finders

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Chapman's recalls near 1 stay printed and are estimated: they rest on misses estimated by capture-recapture, not on misses observed in creators (lead's decision D58, 2026-11-26).

Two finders of the same class over the same recordings: the forecast finder's two wordings A and R (both the small model;
every label window read by both; the instrument joined candidates of the two passes that are the same statement), and,
added here, the asks find's two draws of the same request. Chapman's estimator of the total, pooled over creators; recall
of the union = items found / estimated total. Every row is on all recordings, the base of the production totals.

- Forecast candidates: recall of the union 0.910 (95% interval 0.897 to 0.923); wording A alone 0.756, wording R alone
  0.632. With a time marker 0.944, without 0.905; with a closed-list hedge 0.925, without 0.908; creator-stratified 0.903.
- F1 statements of record: 0.991 (95% interval 0.989 to 0.993); A alone 0.932, R alone 0.865.
- Asks find: candidates as filed 0.866 (95% interval 0.844 to 0.888; 0.867 on the recordings in which every find call was
  answered); merged under the registry's rule for overlapping asks of one class 0.973 (0.966 to 0.979).
- Asks of record, the registered version (primary row; lead's decision D34 of 2026-11-22): Chapman's recall of the union
  is 0.991 (95% creator-bootstrap interval 0.988 to 0.993; draw 0 alone 0.901, draw 1 alone 0.905). It is contradicted by
  the observed misses: Chapman's estimate allows 27 asks of record missed by both draws, but the check itself added 148
  asks of record that neither draw found, so the estimated total is below the number of asks of record known to exist and
  this recall is too high.
- Asks of record, the replacement chosen after the result (printed beside the registered row): the observed upper bound
  found / (found + observed missed) = 0.951 (95% creator-bootstrap interval 0.939 to 0.962). The true recall of the two
  draws together is at most this, and lower if further asks were missed by both draws and by the check. Time of the
  choice (plan P4; UTC, 2026-11-22): not recorded to the minute; the bound was in the package's code by 03:24:49 and was
  printed by the run of record of 03:26:16 (the superseded first build of 02:46 to 02:47 was not kept, so whether it
  already printed the bound is not known). The run of record printed only this bound for the asks of record; the
  registered row was added in the release pass by
  `nlp_r13_registered.py` (added after the exploratory reporting plan; seen asks labels only; it reproduced every
  printed asks cell before writing, and redrew `fig-nlp-r13-recall.png`).

Assumptions and why they may fail. (1) A closed population: the recordings are fixed texts and both finders read the same
windows, but the target is set by each finder's own wording, and a window that failed in one pass removes that pass's
opportunity in it (in a few recordings a window failed; they are kept, so the assumption fails slightly there; for the asks
find, the row of recordings with every call answered shows the effect). (2) Independent captures with equal catchability: both captures are one
model with similar (forecasts) or identical (asks) prompts, so easy items are found by both and hard ones by neither; this
positive dependence and heterogeneity make the estimated total too small and the recall too high, so the estimated missed
share is a lower bound. The asks of record that the check added are a direct count of misses of one kind (another class on
a range a draw found), and they exceed the estimate: there the estimate is plainly too low. (3) Matching: one item split
into two candidates counts as two items found once each, which pushes the other way. A candidate found by both forecast
passes spans the union of their units, which makes a marker slightly more likely for it, so within a marker stratum the
recall leans high and in the stratum without it low.

## Small-cell rules applied

No figure, cell or bin rests on fewer than 5 creators; a statistic is printed only where 5 or more creators carry a non-zero
value; creator counts lying 1 to 4 from a count they are nested in read "all but fewer than 5", and counts within 4 of
another printed count of the same table, or of a count LAB prints (LAB-S and LAB-V for nlp-R10, LAB-F for nlp-R11 and the
forecast rows of nlp-R13 together with nlp-R11's counts, LAB-A for the asks rows), are withheld; a row whose difference
from a printed row (or from rows printed by LAB-F, for nlp-R11) rests on 1 to 4 creators is not printed, and in nlp-R13
this is applied to each capture cell as well (found by one finder only, by the other only, by both), so that no cell can
be recovered by subtraction from 1 to 4 creators, also against the published production totals; cells that add up to a known total are pooled, never
suppressed one by one; quantiles as LAB's rule allows; no minimum or maximum; no per-creator or per-recording row, name,
code, video id, title or quotation. A private ledger of every statistic cell was checked with LAB's ledger check (no cell
solvable from printed cells rests on 1 to 4 creators) and every public file was scanned for names and ids: no finding.

## Code

`nlp_r10.py` (nlp-R10), `nlp_forecasts.py` (nlp-R11 and nlp-R13), `nlpcommon.py` (shared),
reusing LAB's `labcommon.py` (statistics and small-cell rules), the hypothesis code's H5 rule and seen-only reader,
RX's frozen normalisation and patterns, and the forecast chain's marker patterns; `nlp_r13_registered.py`
(release pass, lead's decision D34) prints nlp-R13's registered row for the asks of record with the package's own
functions; `nlp_r13_release_wording.py` (release pass, verifier fixes; wording only) wrote the time of the
choice of the upper bound and the description of the recall into nlp-R13's CSV; `nlp_check.py` is the privacy scan. SHA-256 values are in each CSV's provenance line and in the release's status table (`status-table.csv`). This README is written by hand
(no code writes it).

## Quantiles over a withheld base (release pass 2's fourth fix step, 2026-11-26)

Under the lead's decision D67, no quantile is printed in a row whose creator count is withheld or printed as a band ("all but fewer than 5 of 71", "withheld (within 4 of another printed count)"): a quantile of creator values sits on a position of the sorted values, and that position can give the withheld count back. Such rows print their means and intervals only. Files: nlp-r10-self-presentation.csv and nlp-r11-hedge-kinds.csv (quantile cells blank). Edited on 2026-11-26 in release pass 2's fourth fix step (fix5, f71_d67_quantiles.py, SHA-256 d1242dd9f19465a7f4ee24f76ae5fbe88475b752b354f0044dc963d2487c86fa); no other value changed.

## Quantiles that could narrow a withheld count (release pass 2's fifth fix step (fix6), 2026-11-26)

Under the lead's decision D70, which extends D67, no quantile is printed in a row whose count of creators with a non-zero value is withheld or printed as a band, nor in a row where the quantiles alone could narrow such a count (to fewer than 5, to within 4 of the row's base or to within 4 of another printed count): quantiles were dropped where they could narrow a withheld count. Such rows print their means and intervals only. Files: nlp-r10-self-presentation.csv and nlp-r11-hedge-kinds.csv (quantile cells blank). Edited on 2026-11-26 in release pass 2's fifth fix step (fix6, f91_d70_quantiles.py, SHA-256 1a03a8648a6fc3ce380ec018255a5e4e7a60d3b4134c579c8f5a20ae289eb418); no other value changed.

## Figures in the release

The PNG files named in this README are the package's own drawings, which a release does not copy (D56). Every output of the package is drawn in the release gallery (`gallery/index.html`; records in `gallery/manifest.json`), under these figure ids: nlp-R10: nlp-R10-fig-1, nlp-R10-fig-2; nlp-R11: nlp-R11-fig-1, nlp-R11-fig-2; nlp-R13: nlp-R13-fig-1. Edited on 2026-11-26 in release pass 2's fix step (fix2, f01_edits.py; its SHA-256 is in the round's records), for privacy and consistency only.
