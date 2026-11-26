# rv-D5: the measurement status of each construct

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Public form made at the release review (plan P10) on
2026-11-22 from the item's build of 2026-11-21 01:23 UTC (not re-run). Place: M. The gate summary of GATES is carried
here (GATES has its own full table).

**Question.** What is the measurement status of each construct?

**Base.** All instruments and their checks: recognizer measures on the seen creators (between-creator reliability, the
two-model bridge on 36 pairs, the decoding-grid checks); model-coded label instruments on their gate, pilot and
known-answer samples (seen, development and check creators; constructed texts).

**What is shown.** `public/rv-D5-measurement-status.csv`: one row per construct (21 rows): instrument and version,
reference, reliability with n and interval and source, bridge verdict, seam sensitivity, known biases and allowed uses,
as built (the version of record), with one verifier correction, and a last column giving the paper's updated
reliability cell for the same construct (generated 2026-11-22 01:51 UTC), printed beside the version of record, never in
its place. The topic, named-source and pattern-family rows are not in the paper's table and keep only the built cell.

**What it shows.** No construct has a reference against which correctness could be measured: the recognizer measures
rest on between-creator reliability (ICC 0.25 to 0.60 in the build) and on the bridge between two recognizer models
(word measures agree; pause and word-time measures differ, so tempo is read within one model only); every label
instrument is model-coded, not checked by a person, and has agreement figures between models of one vendor, a reader of
another vendor for the voice label, and known-answer texts (an upper bound, not a measure of correctness on the corpus). Three
instruments fell below a gate on the gate sample and were kept or merged by the owner's decision: relayed voice (merged
into claimed voice), the forecast checkability parts and the title presentation.

**Withheld, and why.**

- Gate figures of the owner's 00:30 decision that rest on fewer than 5 creators under the rule for agreement figures
  (registry 2026-11-21 22:33, applied to the paper on 2026-11-22 00:13): checkability "place", and the titles'
  presentation kappa and stability on the check creators. Their verdicts (gate failed) are printed.
- Pilot agreement figures that were not recounted under that rule: the voice map against the label call on pilot W,
  the relayed-against-own flips (F12), the forecast pilot's class and time-window kappas (F39; its hedge kappa was recounted and is printed; the time window 0.55 of the forecast row is the owner's 00:30 gate figure, not F39's, and passes the paper's recount) and the title pilot kappas
  (F40), and the RX reader kappa on 2,136 hits; and known-answer figures of arms not recounted by creator (voice K1 claimed and own words;
  asks, one arm). The recounted known-answer figures are in the LAB package and in the paper's column. The topic row's
  "6 of 32 codes pass" is a count of codes, not an agreement figure, and stays.
- The count of files waiting for a person's language decision (fewer than 5 creators) and the F42 count of modal hedges
  on target (not recounted by creator).
- The creator count of the lexical-variety ICC reads "all but fewer than 5 of the 71 seen creators".

**Correction.** The built seam cell of pauses called a figure "time in pauses" that is the 2-s measure; the verifier
found that time in pauses of 0.3 s or more moves -0.41 SD. The cell now names the 2-s measure and states the verifier's
figure.

**Pace.** The pace row is recognized words per minute of voice-detector speech: a recognizer-output measure, not a
direct measure of speaking (D12). Its construct name is kept as built; the table's header says the same.

**Fix pass (2026-11-22, after the release verifier).** The pilot agreement figures named above (F39 hedge kappa, NE
window kappas and relative finding, RX reader kappa) were printed although the stated rule withholds figures not
recounted under the rule of 2026-11-21 22:33; they are now withheld like the others. The D12 note on pace was added.
No new value is printed.

**Release pass 2 (2026-11-25; lead's decision D48).** Agreement figures recounted by creator from the stored answers and labels, with a reader that imports no API client and makes no call (seen, check and development creators only). The forecast pilot's hedge kappa (F39, both columns) and the NE pilot's window kappas (any named source 0.714, any datable reference 0.548) and the share of the middle model's sources that the small model finds (0.71) pass the rule and are printed again. Three known-answer cells of the paper's column fail it and read "not published": the middle model's range over the voice recall arms of revision 3 and the range of the forecast parts (each range has an end whose misses come from fewer than 5 creators), and the share of planted non-asks kept as asks (its non-zero values come from fewer than 5 creators). The other pilot figures named above were not recounted and stay withheld.

**Interval levels.** They differ by cell and are stated in each cell: 95% for the ICCs (D4's build) and for the RX read
precision (Wilson); 90% for the bridge's signed-rank intervals; the paper's column keeps the levels of its own sources
(90% for the gate and cross-vendor figures); none for counts.

**Caveats.** Rows updated with the labelled outputs of the first round (plan row "rows updated with L outputs") are not built in this release
(lead's decision D55): the public form is made from the item's build of 2026-11-21, not re-run; the paper's column shows
the updates its builder made, each logged by it. "Agreement" means
agreement between models or readers, never accuracy.

**Figures.** None (record "no figure": a text table with no quantity on a common scale; the gate figures are drawn in
GATES-fig-1).

**Writer.** `build_tables_D.py` (SHA-256
`d38dc81e39a5d9606ca78aae9138138e1a429de11a2082f3e3de533467d1bb92`). The table was written at 2026-11-25T21:48:11Z and then edited by checked text replacements, each logged with its backup; the table and this README were edited by p2_d42_d55_built.py (SHA-256 d1ec7400b2f8706c764137be76fbb676452ae960047ad0504d142539677e3f33; pass 2, 2026-11-25T21:51:12Z), p2_d41_flags.py (SHA-256 f51c2a6a880fcc827d9cc34d021458633921adda1eac6118668b3c88ea876797; pass 2, 2026-11-25T22:02:04Z), apply_pass2.py (SHA-256 e0ada1d2bc8eb1bdeae35da6bd0929b6cc849c2543ddb5dfd6c434f806005a3b; pass 2 (D48), 2026-11-25T22:04:54Z), f01_edits.py (SHA-256 de3cdb4462a5fec5cdf3f49589e657901718c270b075bf45aaf2e3d7d3f45793; fix step, 2026-11-26T00:57:31Z), f33_edits.py (SHA-256 442d541d26f9e5167d980d3c61e23db5248293947ea568ce2b20d4a5a1ff37d4; second fix step, 2026-11-26T02:22:42Z), f51_d61_wording.py (SHA-256 909a5a86d373d72684c1a6f1f92bd427c6ad26db3303496d8a9280235e853098; third fix step, 2026-11-26T03:35:42Z), f52_edits.py (SHA-256 647ed82d76e723fa1c806a4d9c1215509c75f867f69b7963b3f2adaf35654556; third fix step, 2026-11-26T03:41:09Z; this note). The writer was patched afterwards (build_tables_D.py, SHA-256 b84a31fc38be3a70e633dee40e5e0699275dae11f86d0faa9f16cf88203781ab) and has not been rerun: a rerun would not reproduce these edits.
