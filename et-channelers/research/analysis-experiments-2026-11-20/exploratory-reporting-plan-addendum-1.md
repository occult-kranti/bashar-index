# Exploratory reporting plan, addendum 1

Written by the lead under the owner's delegation, 2026-11-21 05:30 UTC; corrected after verification at 05:47 UTC; items 7 and 10 to 13 amended by the lead at 06:35 UTC. It
belongs to `exploratory-reporting-plan.md`, SHA-256
`061bab3303a03951a57e2f05f58ca3ee86bbdba29db637117831715b6acf3c7c`, whose text last changed at 2026-11-21 03:25 UTC (file time). The plan's hash is entered in the registry together
with this addendum's. Under section 0 of the plan, this addendum records outputs as not run, adds outputs (items 1 and 2,
labelled as section 0 requires) and corrects factual errors; it removes no output and changes no estimand, band, panel,
weighting or threshold of an output whose result is known. Two items go beyond what section 0 lists: item 6 fixes a
primary that the plan left to a later freeze, and item 4 records a departure from section 3 made after the result was known.

Timing, stated openly (file times, UTC): the word-error-rate code (`wer-anchor-20261121/code/wer_anchor.py`, private run
folder) was first written before the plan's last change and last changed at 04:30, after it. Its tables were first
written at 03:21, when the first re-made transcript existed (03:21), before the plan's last change (the plan's verifier,
who made that change, found no transcript or table when it checked). A check of confusions on the first transcripts
followed at 03:30, and the normaliser file was last changed at 03:43 (version wa-norm-v2, fixed after that check), so
section 6.7's rule that the text classes and the normalisation are fixed and hashed before any word error rate is
computed was not met; no hash of either is recorded. The private per-creator table was first written at 04:01; the
tables reported now were written from 05:15, before the plan's hash was entered. Items 1 to 4 concern that output and
were written after its results were known. None of them selects a version of a figure by its result.

## 1. BR-b strata

The plan names four strata: text kind, length band, pace third and recognizer model. The code cuts by reference class
(the plan's text kind), length, recognizer confidence and audio edition.
- Text kind and length band are reported as built. Length is shown in thirds where every third holds 5 or more creators
  (the reproducibility row). The thirds of the caption row (11 creators) hold fewer than 5 creators; section 3's merge
  rule would leave that row in one bin, and the code shows it in halves at the median instead. The halves are labelled
  "added after the exploratory reporting plan" with this addendum's UTC time.
- Pace third: not run. The code was built without it; adding it now would add a stratum after the results are known.
- Recognizer model: not run, because every recording was decoded again with the run's English-only model, so the
  stratum has one level; the larger model enters only as a reference text (item 2).
- Recognizer confidence and audio edition: reported as built, labelled "added after the exploratory reporting plan" with
  this addendum's UTC time.

## 2. BR-b against texts made or edited by people

Among the seen creators no reference text is known to be made by people (0 recordings). Under BR-b's status rule
the human-reference row on seen creators is reported as "not run: no seen recording has a reference text known to be
made by people". The machine-to-machine rows are reported as built, each labelled "agreement of two
machines, not an error rate":
- platform automatic captions: 11 recordings of 11 creators;
- the project's earlier text of the same recognizer and settings (reproducibility): 48 recordings of 34 creators;
- the project's earlier text of the larger multilingual model: 5 recordings of 5 creators. The plan's reproducibility
  row took all of the project's earlier text to come from the run's recognizer; this row is labelled "added after the
  exploratory reporting plan";
- publisher texts of undeclared origin: fewer than 5 creators, so its public form is "fewer than 5 creators" (item 4).
The human-reference part moves, unchanged in its rules and places, to BR-b-H after freeze 2: hold-out and other-group
references are classed from the same receipt fields, without reading their text, before any word error rate is computed
on them.

## 3. Error kinds

Substitution, deletion and insertion shares are reported as built. Errors on numerals and years: not run in BR-b (the
code does not compute them); BR-y covers years and numbers on the same pairs. Errors on capitalised names: not run,
because the normaliser lower-cases before alignment.

## 4. Public cells of BR-b

The code's public writer suppresses cells under 5 creators; the plan requires merging. Where section 3's merge would join
a stratum's cells into the whole row, which is printed, both give the same public table. The caption row's halves are a
new cut, not a merge (item 1). One departure remains, decided after the results were known: the undeclared texts are not
pooled into "other" as section 3 requires for text kinds (that pool would take in the smallest remaining kind, which
would then not be printed on its own). Instead the other rows are printed on their own, the undeclared texts appear only
as "fewer than 5 creators", and the pooled automatic row of captions and undeclared texts is withheld, because beside the
caption row it would give the smaller cell by difference; the status table lists it with that reason. This departs from
section 3's rule ("never by suppressing single cells"), and section 0 does not provide for it; it is recorded here.

## 5. Factual corrections

- "The 214 recordings that carry third-party text": about half of the 214 carry the project's own earlier recognizer
  text, which is not third-party text. Rows BR-b and BR-b-H keep their populations; the
  wording "third-party" is corrected wherever the paper or the dashboard uses it.
- Other group: the roster less the 71 seen and 23 hold-out creators leaves 7; 6 of them are in the other group of
  `llm/creator-sets.json` and of the registry's contact log. Both counts are stated where either is used.
- VER-3R: built and sealed until freeze 1, as the plan says; it was opened after freeze 1 (registry 2026-11-21 04:59).

## 6. A primary the plan left open

TL-7.1 eligibility: the protocol's rule (at least 3 absolute dated statements over at least 60 days of uploads) is
primary, because it was fixed first (P3); the pilot's rule (at least 5 absolute statements with windows of 92 days or less
over at least 180 days) is a row beside it. No result of TL-7.1 exists: the pilot's dry run found no eligible channel,
because set W has 1 or 2 recordings per channel.

## 7. Reporting of the timeline pilot's diagnostic cards

The plan leaves out the verdicts of the diagnostic cards (registry 2026-11-21 02:50, agnosticism: never whether a
prediction came true; plan section 6.6). That stands: the registry decision came after the pilot ran, but an addendum
cannot overturn a registry decision, so no verdict on a real statement is reported. The cards come from fewer than 5
creators, so under section 3 their public form, wherever they are counted, is "fewer than 5 creators".

## 8. Registry rows after the plan's last change

Rows of 2026-11-21 03:12 (two), 03:18 and 03:21 (two) were committed before the plan's last change but are not taken into
account in it, which follows the registry up to 03:08; rows of 04:55 (three), 04:59 (two) and 05:00 came after the plan's
text was fixed. None removes an output or changes its estimand or place: the 03:12 row fixes the forecast class that the
timeline outputs use (F1 against the rest), the 03:18 row the wording of ENTRY's counts and timing results, the 03:21 row
adds TIME's reliability limit, and the second-reading row of 04:55 adds figures that DR-2 reports.

## 9. Outputs that may not be built

E1 and E3 (status R) are reported as "not run", with the reason, if they are not built before the report.

## 10. The normaliser of BR-b

The normaliser (wa-norm-v2) was fixed after a check of confusions on the first re-made transcripts, so it is a version
chosen after a result (P4). It is reported with that statement. Version 1 is run as a row beside it if it can be rebuilt
exactly from the record; otherwise it is recorded as not run, with that reason. Known defects of v2 (accented letters,
'etc' and 'vs' inside longer words, decades, currency) are listed in the WER anchor's README; the 'etc' and 'vs' defect left the published rates unchanged
to five decimals, and the others were not measured.

## 11. BR-GS as built

The grid-shift output as built has the word change, seam, onset, pause and word-count measures. The plan's row also names
the change in thanks-phrase segments, the change in isolated segments, changes in between-creator SD units and the check
of the positional precision bound. These are computed from the existing re-decodes (no new decoding) before the report;
any of them that is not is reported as not run.

## 12. BR-b in the abstract and on the dashboard

BR-b's headline is the rate against texts made by people. With that row not run on seen creators, the abstract and the
dashboard say that no seen reference is known to be made by people and give the agreement with platform automatic
captions as agreement, with its interval and the words "agreement of two machines, not an error rate"; never as an error
rate.

## 13. One cell, one interval

Where a stratum covers a whole row (for example the caption row's native audio edition), the row's own interval is the one
reported (P8); the stratum does not print a second interval for the same cell.
