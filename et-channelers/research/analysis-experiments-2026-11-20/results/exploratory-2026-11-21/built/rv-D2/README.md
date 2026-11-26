# rv-D2: how the seen, hold-out and other creators differ, and how the run order made the hold-out

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Public form made at the release review (plan P10) on
2026-11-22 from the item's build of 2026-11-21 (01:18 to 02:27 UTC; not re-run). Place: M (paragraph, love plot); S
(Table B, AUC, vintage). The transcript-derived covariates of the hold-out are rv-D2-H (package HOLD2), printed beside
this table.

**Question.** How do the seen, hold-out and other creators differ, and how did the run order make the hold-out?

**Base.** Creator-level fields of the run ledger and the inventory only (counts, durations, dates, languages, audio
edition, run positions; not a contact): 71 seen creators, 23 hold-out creators and the other group (fewer than 10
creators). No transcript field of a non-seen creator was read.

**What is shown.**

| File | Content |
|---|---|
| `public/rv-D2-table-B-balance.csv` | Table B: medians and quartiles (seen, hold-out), SMD of hold-out and of other against seen with 90% intervals |
| `public/rv-D2-auc.csv` | Cross-validated AUC of hold-out membership against 999 label shuffles |
| `public/rv-D2-run-order.csv` | Run-ledger positions by group |
| `public/rv-D2-vintage.csv` | Roster vintage, all creators |
| `public/rv-D2-sentences.csv` | One sentence for every covariate whose hold-out SMD lies beyond 0.25 |
| Gallery group B-D, `rv-D2` | fig-1 love plot (M); fig-2 AUC against the shuffle band (S) |

**What it shows.** Fields known before the run already separate hold-out from seen creators (cross-validated AUC 0.69,
95% band of 999 label shuffles 0.30 to 0.67, p = 0.022); with the two language-decision fields the AUC is 0.84
(p = 0.001). Beyond the 0.25 line, hold-out creators have more recordings with English text of another kind (SMD +0.65),
more native platform audio (+0.74) and less audio extracted from video files (-0.53), more confirmed upload days
(+0.69) and fewer still-estimated dates (-0.30), earlier metadata capture (-0.64; the medians are equal, the means
differ), more transcripts not in English
(+0.74), fewer language decisions by the creator rule (-0.83), a smaller share of selected files transcribed (-0.77), and
later first and last lines in the run's ledger (+0.75 and +4.12). The other group's differences rest on few creators and
are not read.

**The run-order paragraph (corrected).** Until about 05:52 UTC on 20 November (ledger line 251) the worker took
recordings in the proposal's order; from 04:19 UTC a language fallback decided recordings whose probes held no clear
speech. From 05:52 UTC the worker ran with an English-first ordering (committed at 06:08 UTC): creators already
established as English first, then creators not yet known, then creators detected mostly in another language, the
proposal's order holding within each tier. The paper's snapshot (about 13:00 UTC, 1,213 ledger lines) was taken inside
this ordering, and the hold-out was then defined as the 23 creators with at most three of those transcripts and ten or
more still to come. The hold-out is therefore the tail of an English-first queue: all 6 creators with a non-English
transcript are in it; its median first ledger line is 130 against 43 for the seen creators and its median last line
1622 against 1297; all but fewer than 5 of its 23 creators had a transcript before 05:52 UTC, but the median hold-out
creator had 1 transcript in the snapshot against 17 for the seen creators. Of all 101 creators, 74 were on the
74-channel roster table of 19 November (04:31 UTC) and 27 were added later that day; the vintage by group is not
published. A logistic model on 13 inventory and date fields known before the run separates hold-out from seen creators
with a cross-validated AUC of 0.69 (95% band of 999 label shuffles 0.30 to 0.67; p = 0.022); adding the two
language-decision fields raises it to 0.84 (p = 0.001). The hold-out differs from the seen creators in language, audio
edition, date evidence and run order; a difference between seen and hold-out results is not a replication or a failed
replication.

**Withheld, and why.**

- The other group's medians and quartiles (fewer than 10 creators: only its SMDs are printed, as in the paper), and its
  SMD where it rests on fewer than 5 creators with a value other than the group's common one (native audio, extracted
  audio, language decisions by the creator rule); its SMD for the non-English share is printed as "not defined (0 for
  every creator of both groups)".
- The other group's median first and last ledger lines and its median count of transcripts in the snapshot, in
  `rv-D2-run-order.csv`: over the run's 1,699 ledger lines they would reproduce Table B's withheld medians, so they are
  not published, as in Table B (verifier).
- The hold-out quartiles of the non-English share (a quartile would interpolate a single creator's value).
- The SMDs of "files selected" and of the publisher audio edition: values other than the group's common one come from
  fewer than 5 creators. Their sentences are withheld for the same reason, so the plan's "one sentence for every
  covariate beyond 0.25" holds for every printed covariate.
- The roster vintage by group, its SMD and its sentence (cells of fewer than 5 creators). The built paragraph's vintage
  sentence re-disclosed two masked cells (verifier); this form gives the vintage for all creators only.
- Exact counts of creators with a transcript before the English-first phase in the hold-out and other groups ("all but
  fewer than 5 of 23"; "5 or more"), and creator counts per Table B row (two rows rest on all but fewer than 5 of the
  seen creators).

**Interval levels.** SMDs: 90% creator-bootstrap intervals (2,000 draws, stratified by group), read against the fixed
lines 0.1 and 0.25 (no test). AUC: 95% band of 999 label shuffles.

**Caveats.** E1 and E3 are levels of date evidence, not exploratory questions. Run-queue fields (block Q) differ by
construction. The hold-out is not exchangeable with the seen creators, so every hold-out result of this study is read
beside this table and beside rv-D2-H, and never pooled with the seen result.

**Fix pass (2026-11-22, after the release verifier).** The other group's run-order medians are withheld; its
non-English SMD reads "not defined"; the metadata-capture sentence says that the medians are equal and the means differ;
the love plot prints its left-edge values beside their points and keys the fixed lines. No new value is printed.

**Writers.** Tables: `build_tables_D.py` (SHA-256
`d38dc81e39a5d9606ca78aae9138138e1a429de11a2082f3e3de533467d1bb92`); figures: `plot_D.py` (SHA-256
`ab68d497db1726d7fd12edfbec30e72b71efe5b208be0886822e8c014fa44caf`). The table was checked cell by cell against the
paper's public balance table (same values; same withheld cells).
