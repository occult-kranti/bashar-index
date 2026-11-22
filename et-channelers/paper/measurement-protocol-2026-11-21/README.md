# Measurement-and-protocol paper (draft of 2026-11-21)

Assembled 2026-11-21, 06:45 to 07:15 UTC, revised after two reviews (methods; privacy and consistency) from 07:36
to 08:40 UTC, revised again from 11:10 to 12:00 UTC for the parts of those reviews the first revision never saw, the
page limit and the new facts (section 8), revised a fourth time from 12:24 to 13:10 UTC after a new methods review
and a new privacy review of the third draft (section 9), brought up to the registry of 18:41 UTC, with the
first-round results wired in, from 19:16 to 20:15 UTC (results round, section 10), filled with the published results
from 20:42 to 20:55 UTC (section 11), corrected after the pre-publish verification from 21:28 UTC (section 12), and
corrected again after the final pre-push check from 23:35 UTC (section 13; clock: `date -u`). This folder holds an
anonymous ICWSM submission draft in the AAAI two-column format:

> *What a Speech-Recognition Pipeline Does to Online Channelling Recordings: Agreement Anchors, Decoding-Window Seams,
> and a Registered, Then Amended, Protocol for Model-Coded Labels*

This README holds no transcript text, creator or channel name or code, video id, title, quotation, or per-recording or
per-creator value, and no count of fewer than 5 creators.

## 1. What the paper is

A measurement-and-protocol paper (registry decision of 2026-11-21, 02:50 UTC). Its subject is what a Whisper-family
pipeline does to the audio of recordings published by creators selected by the authors as channelling mediums:

- the agreement anchors (no reference made by people exists for the seen creators; platform captions, the project's
  earlier recognizer text and a larger model's earlier text are machine-to-machine agreement, not error rates);
- the bridge between the two recognizer models (seen pairs only);
- window seams, the grid-shift control (with its thanks-phrase, isolated-segment and SD-unit rows) and the inserted
  thanks phrase;
- where time outside recognizer segments sits, and the voice detector's non-speech share;
- coverage of the newest-20 quota and selection;
- the creator-level variance structure and the error tolerance of word measures;
- the registered, then amended, protocol for model-coded labels: registry, hold-out of whole speakers, freezes,
  amendments, gates (failures and the owner's exception included), known-answer battery, second reading, cross-vendor
  reader, deviations.

It is not a findings paper about channelling, not a dataset paper (nothing is released) and not a validation paper (no
person checked any label or transcript). Section 7 states the design of the first-round tests (H1, H2, H4, H5, H6, H9),
their projected eligible creators (both of CAL's bounds) and power in advance; their results reach the paper only
through the public results file `research/analysis-experiments-2026-11-20/results/first-round-2026-11-21.json`, which
the lead writes with `publish_results.py` from the private report. The file was published on 2026-11-21 (section 11);
a rebuild fills Section 7.2, Table 2, the abstract, introduction and conclusion sentences, the gate failures on R-hold
(Section 6.4) and the three results tables of Appendix B from it, for any outcome. Before it existed, every result
macro was a `\pending` placeholder.

## 2. Files

| Path | What | Made by |
|---|---|---|
| `main.tex` | Integrator file: preamble, macro files, section order, bibliography, appendices. No prose. | integrator |
| `aaai25.sty`, `aaai25.bst` | AAAI 2025 author kit, copied unchanged from the old draft (SHA-256 in the header of `main.tex`) | copied |
| `sections/*.tex` | Title, abstract, Sections 1 to 10, ethics statement, Appendices A to C | writers A, B, C; revised in the review round |
| `findings/numbers.tex` | Every number the paper uses, as a macro, one per line, with its source file and field in a comment. Only macros the paper uses are written; withheld macros never are | GENERATED |
| `findings/pending.tex` | One macro per placeholder; each expands to `\pending{...}` | GENERATED |
| `findings/results.tex` | The first-round result macros (`\Res...`), from the public results file; `\pending{...}` while it does not exist | GENERATED |
| `floats/tab_*.tex`, `floats/fig_*.pdf` (and `.png`) | Tabulars (the writers add float, caption, label) and figures | GENERATED |
| `floats/caption-notes.tex` | Base, unit and pooling of each figure, as macros | GENERATED |
| `floats/tab_results*.tex` | Results table (main text), both versions under the guard (two parts), robustness rows, Holm table | GENERATED |
| `refs.bib` | References verified in the old draft's reference work (Crossref or arXiv metadata) | writers A, C |
| `refs-new.bib` | Entries verified later by the lead; empty | lead |
| `build.sh` | Build script (below) | integrator |

Kept in the private work folder `paper-measurement-2026-11-21/work` of the run, because they read or hold private
values (privacy review, item 6): the builder `build_numbers.py`, the paper check `check_paper.py` and its report, the
build record `build-record.json` (every computed macro with its source hashes, withheld ones included), `provenance.csv`,
and, in `work/planning/`, the outline, the fix lists (`fix-list.md`, `-A`, `-B`, `-C` and `fix-list-review-2.md`, `-3`, `-4`) and the
writers' macro requests. Never edit a GENERATED file by hand: change the builder and rebuild.

## 3. How to build

Requirements: MiKTeX (`pdflatex`, `bibtex`), and for the regeneration step the private work folder and the guarded
analysis venv (one process, no worker pool, no API call).

```bash
bash build.sh             # typeset only: four pdflatex passes and bibtex; prints errors, undefined references,
                          # citations and macros, float and box problems, then runs the paper check if present
bash build.sh --numbers   # first regenerate findings/ and floats/ with the private builder, then typeset
```

`ET_PY` and `ET_WORK` override the default paths of the venv's Python and of the private work folder. Plain LaTeX also
works: `pdflatex main; bibtex main; pdflatex main; pdflatex main`.

Results only: `build_numbers.py --results-only` rewrites `findings/results.tex` and `floats/tab_results*.tex` alone from
the public results file (the rest of the paper as built). The builder reads that file and nothing else of the tests: it
validates it against `first-round-results.schema.json`, refuses a synthetic document in this folder, prints every
creator count in the file's printed form, and states against 5 or against the minimum any count that this paper would
otherwise print 1 to 4 away from a creator total it prints or implies (the group totals, the English-only hold-out
count, the file's hold-out count, and the counts already public on main: the bridge's registered pairs, H3's eligible
and positive counts, the hold-out design and the registry's other group) or above the English-only hold-out count. A
scratch test of other outcomes
sets `ET_PAPER_PUB` (a copy of this folder), `ET_RESULTS_JSON` and `ET_RESULTS_ALLOW_SYNTHETIC=1`; it never writes into
this folder or the private work folder.

`build.sh` sets the PDF's dates in UTC (`SOURCE_DATE_EPOCH`, `FORCE_SOURCE_DATE`), and `main.tex` suppresses the pdfTeX
banner and the figures' info dictionaries, so the PDF carries no local time zone.

State of the build after the final pre-push check (section 13; `\BuildStamp` gives its time, the results file was
read as published at the time `\ResStamp` gives): 519 macros written (only those the paper uses), 12 pending macros and
22 result macros, none of them pending (15 placeholders in the PDF text by the paper check, all from
`findings/pending.tex` and the status table at report time), 0 errors, 0 undefined references, citations or macros, no
float too large for its page; nine boxes run at most 4 pt over their column (no layout effect); builder checks 162
passed, 0 failed. The PDF has 59 pages: main text pages 1 to 8 (the conclusion ends on page 8), the ethics statement
and the references from page 9, Appendix A from page 12, Appendix B from page 30, Appendix C pages 58 to 59. The paper
check found no undefined macro or missing citation, no privacy hit (its accepted matches are listed in its report with
their reason: a cited co-author's surname, the platform's name in cited titles, the build script's default path), no
risky phrase and no nested creator-count pair of the forms it recognises (sections 12 and 13).

Earlier state, kept for the record: the paper check (`check_paper.py`, run by `build.sh`) found at 20:13 UTC what it found at 13:00 UTC, with 55 creator
counts near a printed total listed for review (one more, a caption's "fewer than 5 creators"); the disclosure scan
(`public_disclosure_scan.py` of the privacy checkout, `pipeline/` of this checkout has none; run at 20:13 UTC on all 85
readable files of this folder, the PDF included, against 237 name strings, 1,976 ids and 1,393 seen titles) found 0
small cells, names, ids or titles. At 13:00 UTC the check had found: no undefined macro or missing citation; no
creator name, creator key or code, recording id or channel id in any file of this folder or in the PDF text; the
check's banned words occur in the PDF only inside the reference list (a co-author's name in one cited work, and the
platform's name in cited titles) and in `build.sh` (the default path of the private work folder). Its disclosure audit
found: no planning file in this folder; no unused or withheld macro in `numbers.tex`; no risky phrase in any public
file; 54 creator counts near a printed total, listed for review in the private report. The repository's disclosure scan
(`public_disclosure_scan.py` of the privacy checkout, run at 12:56 UTC on every file of this folder, the PDFs and build
files included, against 237 name strings, 1,976 ids and 1,393 seen titles) found 0 small cells, names, ids or titles.

## 4. What still waits for its source

Every placeholder prints as **[pending: ...]** and is filled only by a later build from its source, never by hand. The
first-round results are no longer among them: they are filled from the public results file (section 11).

| Waits for | Placeholders |
|---|---|
| H3 at the creator level on the hold-out | `\PendHThreeX` |
| Word error rate against possibly human-made texts of hold-out and other-group creators | `\PendBrbH` |
| Seen-creator model-coded descriptions under freeze 1 | `\PendLabV`, `\PendLabA`, `\PendLabF`, `\PendLabS`, `\PendLabT`, `\PendLabK` |
| Verification: effective number of readers; third reader on gate samples | `\PendVerDep`, `\PendVerAdjG` |
| Years and numbers against references; prediction timeline counts | `\PendBrY`, `\PendTlBuild` |
| Exploratory output status at report time (written by the builder in `tab_outputs.tex`) | `\pending{status table at report time}` |

Filled in the results round from the registry (no longer placeholders): freeze 2, A10's entry and addendum 2.
Stated in the text instead of a placeholder: CAL part (f) did not run (registry 16:06 (2)), and HR (a) and HR (b, c)
were not bought (18:41). When a source appears, add its reader to `build_numbers.py` (replacing the entry in its
`PENDING` list), run `bash build.sh --numbers`, and check the build log and the paper check. A new version of the public
results file is read by `bash build.sh --numbers` (or `--results-only` followed by `bash build.sh`).

## 5. Integrator's changes and decisions of the first assembly (2026-11-21)

1. `main.tex` written as in the outline; `\pending` defined there; `\clearpage` before each appendix.
2. Macros requested by the writers added to the builder, each computed from its source.
3. The word-error anchor files were rewritten by their own workflow at 06:59 UTC; the builder reads the reported
   normaliser's rows, and Section 5.1 says that the normaliser was fixed after the first result.
4. Tables taller than a page are written by the builder in parts of consecutive rows, each with its header.
5. Table U takes D3's interval for the pooled non-speech share, the one the text prints.
6. Seams figure: four panels; deviation table and timeline captions fixed to what the floats hold.
7. Wording fixes ("planted claimed passages recovered", "No human reference", "filter off", "mid-window rate").

P7 move log: at the build of 07:05 UTC `fig:icc` and `fig:bridge` moved to Appendix A and `tab:external` to Appendix B,
with captions unchanged.

## 6. Second review round (2026-11-21, 07:36 to 08:40 UTC)

Applied from the methods review and the privacy-and-consistency review (both received truncated; every visible item
was handled). Generator first, then text. The item-by-item answer is `work/planning/fix-list-review-2.md` (private).

- **Eligibility (methods 1).** Both of CAL's bounds in the abstract, Section 7, Table 5 and Figure 13, with CAL power at
  each; the text says the 02:50 announcement rests on the lower, creator-property bound, why (the cautious bound; the
  pilot cannot tell the two apart), and that it is a statement of risk, not a forecast.
- **Gate rule (methods 2, 3).** Section 6.5 states plan 3.4's full rule (pre-declared merges, or not run) and the
  exception written into A10.5; H2, H5 and H9 are flagged as resting on instruments below their floors, with the
  wording their verdicts may carry; the abstract names the two failed instruments. The relayed-into-claimed merge is
  described as decided at 02:55 after the pre-declared merge failed, and deviation row 45 is classed looser (A10's own
  record says stricter; both are printed).
- **Cross-vendor reader (methods 4).** 200 units of 23 creators, the unweighted kappa, the disagree stratum and the
  weight concentration in the text and in Table 31; "weighted to the frame" in the abstract.
- **Positional sentence (methods 5).** Abstract and conclusion now rest on recognizer-segment coverage; the detector
  share is a separate statement.
- **Grid shift (methods 6).** The thanks-phrase, isolated-segment and SD-unit rows and the direct precision check are
  in the text and in a second part of the grid-shift table; the thanks rate is stated as conditional on the grid.
- **Triangle inequality (methods 8).** Stated on edit counts; the rate form carries the unknown ratio and the
  normaliser.
- **Small intervals (methods 9).** The anchors print 95% t intervals on creator values; percentile-bootstrap cells on
  fewer than 12 creators are marked rough; the cross-vendor interval carries the coverage note.
- **Seen-only rule (methods 10; privacy 2).** The bridge rests on its seen pairs everywhere (verdicts, figure, table,
  Bland-Altman, status table); the all-creator detector rows of Table U and Table D are gone, and Table D's snapshot
  cells computed from all creators' transcripts read "--"; the limitations list the contacts of the public-output
  generators (about 03:00 to 06:35) and of the one-off seen-derivative script (06:49).
- **Small cells (methods 7; privacy 1, 3, 4, 5).** The flow figure and caption merge every reason of fewer than 5
  creators; counts that fall fewer than 5 short of a printed total read "all but <5" (Table U, artefact, non-speech
  and pseudo-word tables, flow figure); roster vintage only for all creators; the seen total of the other-text
  recordings, its kind split and the outside-the-seen-group count are no longer printed; the half-to-one-SD bin of
  bridge pairs is gone; the outlying pair is "more than ten times the median pair's" (withdrawn in the fourth round,
  section 9).
- **Private material (privacy 6).** Planning files, macro requests and the build record moved to the private work
  folder; `numbers.tex` holds only used macros; a list of withheld macros in the builder; comments that stated withheld
  values removed.
- **Deviations (privacy 7).** Six registry rows that A10 Part 7 already carries are no longer added twice; the 06:44
  registry row, in neither list before, is added; 67 rows.
- Also fixed: `|D|` printed as dashes in Table 5; thousands separators printed as `{,}` in Table U.
- **Sources that changed during the round.** The anchor files were rewritten again at about 08:05 UTC with a dominance
  rule; the builder now prints only rows whose status is "reported", so the normaliser-1 caption figure and the trimmed
  caption variant are no longer printed. A registry contact-log row of 07:50 that names no contact is left out of the
  contact table (reported by the builder).

## 7. Open points

- **Canonical literature.** `refs-new.bib` is empty; the canonical works on channelling and its milieu that the review
  names wait for verified entries. Section 9 states their absence and the other review conditions still unmet.
- **Addendum 2** of the reporting plan (normaliser timeline, public inventory form, grid-shift choices, seeds) is the
  lead's to write and register (`\PendAddendumTwo`).
- **Precision band.** Closed in the fourth round: no share or band of the direct precision check is printed; the
  count keeps the anchor file's wording ("fewer than 5 creators with a recurring removal", which includes none).
- **Already public elsewhere.** The paper now prints the set-aside count as one count (other text or a language
  review) and the census in recordings only, as the public outcome table does. Some figures the paper withholds can
  still be worked out from files already published in the repository; the private fix list of the fourth round names
  them for the lead (outside this folder).
- **A10 alignment.** The deviation table drops a registry row wherever the A10 draft holds a row of the same time and
  adds the registry rows written after the draft's last alignment, so a rebuild after a later alignment keeps every
  deviation once.
- The paper checklist follows the 2024 ICWSM template from memory; check it against the target year's template.
- Ethics and exemption determination, lawful basis, data-protection assessment and removal route are the owner's acts;
  the vendor-retention terms of the Anthropic agents were not read. The paper is not to be submitted before the ethics
  determination.
- **Bridge (fourth round; restated in section 12).** The paper prints the bridge as verdicts and tallies on the seen
  pairs only; each equals the verdict on all registered pairs. Since the pre-publish verification the seen pairs are
  not counted: the bridge is sized by its registered pairs (public on main, one per creator), all but fewer than 5 from
  seen creators. Printing the registered results as published instead remains the lead's decision.
- **Projections (closed in section 12).** The projections are capped at the number of hold-out creators with English
  recordings, which the paper withholds; their recording-property bounds are now stated against the minimum only, and
  no printed range end shows the cap.

## 8. Third review round (2026-11-21, 11:10 to 12:00 UTC)

Every item of the first-pass reviews after the point where the second round's copy was cut off (methods review from
item 10 (c), privacy and consistency review from item 7) is answered in the private `work/planning/fix-list-review-3.md`,
with the sentence that answers it. In brief:

- **Length.** Main text from the title to the conclusion now ends on page 8; the ethics statement follows on page 9.
  Moved, not dropped (each marked "moved here ... by the page limit"): the two status tables and the programme table to
  Appendix B; the census flow figure, the coverage figure and the artefact table to Appendix A; the paragraphs "Three
  levels" and "Dates", parts of Sections 5.5 and 5.7, Section 6.7, the H3 detail, the second-reading and cross-vendor
  detail, the merge list of plan 3.4 and the hypothesis-code decisions in detail to the appendices. Abstract,
  introduction, related work (every citation kept), limitations and Section 8 condensed.
- **Anchors.** The caption row is a re-decode with the run's recognizer on set-aside recordings, not a sample of the run;
  the normaliser timeline follows the anchor item's record (version 2 made at 03:31; 03:43 is the trimming fix); the
  rows of Table 1 are on their own scales, as its caption now says; per-cell seeds and the dominance rule are in the
  rebuilt numbers; the seen inventory is described in its public form, without the seen totals.
- **Bridge, grid shift, artefacts.** The agreeing and differing measures as R3 gives them; limits of agreement as
  macros; the grid-shift concentration as a ratio to the uniform share, the worker-version mix, the pause share in SD
  units; no percentile of the per-recording change; the voice detector gates decoding; the precision bound's assumption
  stated beside the direct check.
- **Protocol.** A10 is a draft (ten amendments entered); the reporting plan's registration time and what preceded it;
  title gates of record with the 00:30 figures beside them; revision counts; the known-answer battery on revision 3
  (registry 09:10); interfaces and the hard stop at worst case; seen production complete (11:10); the H6 and H9
  hypothesis-code decisions of 06:44, 09:19 and 11:08; H9 not projected; only H1, H4 and H6 announced at 02:50.
- **Consistency and privacy.** Ethics and the external-processing table rest on one read of the request ledger and sum
  to its totals; entrance bins from version 1; Table U's two-level log-probability rows fill the former placeholder;
  tails of fewer than 5 creators no longer printed (percentiles, other-group quartiles, limits without the outlying
  pair); group sizes that gave small cells by difference removed; agreed wording in the known-answer, gate and
  deviation tables; PDF dates in UTC.

## 9. Fourth review round (2026-11-21, 12:24 to 13:10 UTC)

A new methods review (12 items, the last received cut off) and a new privacy review (8 items, the last cut off) of the
third draft. Generator first, then text; every visible item was applied, two in another form than proposed (the
bridge as verdicts only, not on all registered pairs; the rank figure in two classes per rank, not in rank bins whose
creator counts the counts-only source cannot show). The item-by-item answer is
`work/planning/fix-list-review-4.md` (private); the state before the round is in `work/backup-before-review-4/`.

- **Methods.** Section 8 states what A10's guard covers (changes of estimator, reference, minimum, interval or
  centring) and names the looser and mixed deviations outside it; a class "mixed" holds the HR release rule of 03:21
  (stricter for H1, H4, H6, looser for HR) and the M9 revisions (direction not known, outside the guard by registry
  06:44 (7)). The grid's thanks-phrase change is stated with its interval, which includes zero ("may move with the
  grid"), and on its own estimand (all thanks segments, before the filter). The known-answer bounds carry their
  assumption, recovery shares as upper and error shares as lower bounds. The precision check prints no band. VG-6
  names its comparator, its reader's model family, the concentration of disagreement on claimed voice, the sealed
  figures' time and the middle model's row. The choices after a gate result (ask record, forecast class) and freeze 1's
  timing are in Section 6.3. The grid shift compares like estimands by worker version (new macros from the private
  per-recording file). The tolerance thresholds are set against the measured machine disagreement. The triangle bound
  reads |rD - e|. The 02:55 merge applies to H1 and H6 (registry 04:55 (a)); A10 "at freeze 2 at the latest".
- **Privacy.** The bridge is printed as verdicts and tallies only (no seen-pair mean, interval, limit of agreement,
  outlier ratio or drop tally; the mean-difference and Bland-Altman figures are removed). Table B drops the roster-vintage
  row and the other group's medians, and prints "--" for the hold-out quartiles of the non-English share; the love plot
  drops the vintage row. The rank figure shows two status classes per rank and native against other audio, every cell
  5 or more creators. The set-aside count is one count (other text or a language review) and the census is in
  recordings only (abstract, Sections 3 and 4, the flow figure, the exclusion table, Table U, Table D, the timeline
  key). The count of hold-out creators with English recordings is withheld (text, figure line). D4's isolated-segment
  counts leave Table U and Table D.
- **Length.** Moved to the appendices, each marked "moved here ... by the page limit": the second half of Section 7's
  calibration paragraph, the ICC detail of Section 5.7, the caption strata of 5.1, the bridge's numeral and capital
  ratios, the definitions paragraph of Section 4, the window shares and prevalence of 5.4, the seam rule's rank
  correlation, the known-answer arms and the second reading's units and intervals of 6.4, production cost and
  interfaces of 6.1, H3's recentred seen value; condensed in place: Sections 5.6, 6.2, 8, 9 and the conclusion. The
  seams figure is set at 0.9 of the text width.

## 10. Results round (2026-11-21, 19:16 to 20:15 UTC)

Brought up to the registry of 18:41 UTC and wired to the public results file. Generator first, then text; the state
before the round is in the private `work/backup-before-results-round/`.

- **Registry after 13:05.** Addendum 2 (13:05) fills its placeholder. Freeze 1, amendment 1 (16:06; the production
  driver's feature step, every other hash unchanged; the freeze table, Table 26, holds both records), freeze 2 (16:10) with its constants
  (H4's yardstick 0.1474 over 52 seen creators, the 40-form minimum stated as a choice, 0.156 over 60 without it; H2's
  bands 12 and 20 and retained parts; H9's smallest effect 0.2, the placeholder adopted, a deviation), A10 entered
  (16:07), hold-out production (16:11 to 16:47; recordings only, no label count of hold-out text, as no seen label
  count is printed either), R-hold (30 recordings, 89 arms) and the checkability check on the hold-out (300
  statements), the reliability driver's plan-mode limit (17:29), interfaces and the hard stop at worst case (16:20),
  the final spend (126.70 USD committed, past the warning, under the hard stop) and what was not bought (HR (a), HR
  (b, c)); the H6 cluster window, the ask deduplication and H9's mask and contraction rules (12:52). Freeze 1 is
  printed from its first record (`llm/freeze-20261121T045822Z.json`), since `llm/freeze.json` is now the amendment.
- **Deviations.** The table reads the registry's own deviation table (A10 Part 8, rows to 15:14) and adds the registry
  rows after it (16:06 to 18:41): 93 rows; H9's smallest effect is a third "mixed" row. The timeline runs to 18:41
  (A10's entry, freeze 2, hold-out production, R-hold, the end of labelling) and its key is set in two halves.
- **External processing.** Hold-out and other-group transcript windows went to the API after freeze 2: the ledger
  categories, the external-processing table, its caption and the ethics statement say so.
- **Results.** `results()` in the builder reads the public results file (schema 1.x, validated), never the private
  report, and writes `findings/results.tex` and `tab_results` (main text), `tab_results_detail` (two parts),
  `tab_results_rows` and `tab_results_holm` (Appendix B). Section 7.2 says how many hypotheses were tested, how many are
  uninformative and how many are discussed, names the informative ones by verdict kind with their claims, and carries
  the registered wording (model-coded; the verification wording for supported and refuted verdicts; the instrument
  flag of H2, H5 and H9; uninformative results out of the headline claims). Tested in scratch copies with the
  converter's synthetic sample and three variants (refuted, not determined and not determinable results; all six
  uninformative; none uninformative; counts the paper withholds; a relative count form): every build compiled, the
  main text ended on page 8, and the disclosure scan found nothing.
- **Length.** Moved to Appendix B or A, each marked "moved here ... by the page limit (results round)": the constants
  and first-round production details, the CAL bound ranges and power counts, the cross-vendor strata and weights, the
  second-reading detail, the triangle inequality, the grid shift by worker version and in SD units, the precision
  check, part of the tolerance paragraph, and the cloud-only read; condensed in place: Sections 6.3, 7, 8, 9, 10.
- **Open at this round (closed since).** The public results file did not exist yet at this round (it was written at
  20:48 UTC; section 11). CAL part (f) did not run and is stated so. The disclosure scan named in the task
  (`pipeline/public_disclosure_scan.py` of this checkout) is not in this checkout; the privacy checkout's copy was run.
  The registry's row of 16:13 named the number of hold-out creators with English recordings, which this paper
  withholds; the paper does not repeat it, and since section 12 no printed projection shows it either.

## 11. Results filled (2026-11-21, 20:42 to 20:55 UTC)

The lead wrote the public results file (`research/analysis-experiments-2026-11-20/results/first-round-2026-11-21.md`
and `.json`, schema 1.2) and rebuilt the paper from it (`bash build.sh --numbers`): 56 pages, main text on pages 1 to
8, no undefined macro or citation, no disclosure hit. Every first-round result is uninformative (H1, H4, H5, H6 and H9
not determinable; H2 not run for want of an instrument); none passes the Holm step.

- **Wording.** "Not validated by a person" became "not checked by a person" (Section 6.4 and the cross-vendor table).
- **Captions.** The programme table's caption lost its "pending" clause (the float fitted after it); the contact
  table's caption names the registered tests run by their frozen procedures, as the registry's contact log now does.
- **Registry.** Its results section and rows state eligible counts against their minimums, as the public file does;
  the row of 16:13 no longer names the number of hold-out creators with English recordings.
- **Still pending in the paper.** The exploratory outputs of the reporting plan (findings/pending.tex: the seen-creator
  model-coded descriptions, VER-DEP, VER-ADJ-G, BR-b-H, BR-y, H3-X, TL-BUILD) are not produced by the registered tests
  and stay marked pending until they are.

## 12. Pre-publish verification (2026-11-21, from 21:28 UTC)

An adversarial verification of the public outputs before publication (privacy of the paper, consistency with the
public results file and the registry). Generator first, then text; the builder and the paper check before the round are
in the private `work/backup-before-prepublish-fixes/`. No count printed here is new.

- **Projections.** CAL's projections are capped at the number of hold-out creators with English recordings, which the
  paper withholds; a median or range end at that cap stated it. The recording-property bounds are now stated against
  the registered minimum only (Section 7, the programme table, the eligibility figure, which draws them as arrows from
  the minimum), a creator-property range end that would show the cap is left open, and the median of English
  recordings is taken over all hold-out creators. The builder checks that no printed or drawn projection value reaches
  the cap.
- **Balance.** Table B and the Love plot drop a group's standardized difference when it rests on fewer than 5
  creators with a value other than the group's common one, and a field where the seen group has 1 to 4 such creators
  or neither comparison group can be printed (a dominance check in the builder on the private covariate file; counts
  only leave it).
- **Nested counts.** The label-flip table prints a recording count, one per creator, fewer than 5 below a count it is
  nested in as "all but <5"; so does the known-answer table for the creators of a row against its arm or block. The
  other group is given no count (a bound only), since the roster's and the registry's other groups are nested and
  differ by fewer than 5. The seen bridge pairs are not counted: the bridge is sized by its registered pairs, all but
  fewer than 5 from seen creators, and the verdicts, each equal to the verdict on all registered pairs, stay as they
  were.
- **Entrance cues.** A read-precision share whose on-target items come from fewer than 5 creators is not printed; the
  builder bounds the creators from the samples' at most two items per creator and otherwise takes the count the
  verification made from the private sample file (this builder opens no transcript file).
- **Results tables.** The robustness summary reads the published rows only ("not assessable" where every row is
  withheld); a hypothesis label is no longer taken for a count (H6's detectable-effect note and H9's wording are
  printed as the results file gives them).
- **Gates and spend.** The gate tables cover the gate sample G; on R-hold the forecast class of record fails gate D and
  the sentence codes fail gate C, stated in Section 6.3, the tests, the limitations and the conclusion with the figures
  of the public results file only (`\ResRhold...` macros of `findings/results.tex`). The committed spend is stated with
  its measured part, the rest held by unreleased reservations of ended runs (Appendix B and the deviation table). The
  deviation rows on A10's exact text and on the smallest effects of H7 and H9 now state their outcome (16:07 and 16:06).
- **Checks.** `check_paper.py` lists, besides its earlier checks, accepted privacy matches with their reason, new risky
  phrases (the hold-out title total, the seen bridge pairs, the projections' cap, the other group's count), and nested
  creator-count pairs of the forms it can recognise (a row's creators against its block or arm in a table, a column of
  nested counts, "N of M", group-qualified counts in the PDF text against the group's printed or public total, and an
  exact count beside "all but fewer than 5 of M"). The builder's final check scans every generated file for the same
  counts.

## 13. Final pre-push check (2026-11-21, from 23:35 UTC; rebuilt 2026-11-22, 00:10 and 00:15 UTC)

The fixes of the final check before the push, generator first, then text; the builder before them is in the private
`work/backup-before-prepublish-fixes/build_numbers.before-final-check.py`. No count of creators is printed here.

- **One rule for every agreement figure.** The lead's rule of 22:33 UTC (the positive code from 5 or more creators in
  each reading; the creators with an item the readings code differently none or 5 or more; a minor code both readings
  give alike is not a cell of its own) now governs every agreement figure the paper prints from a reliability sample. It
  is read as worded (lead's decision of 2026-11-22 00:15 UTC): a figure with a positive code (YES, F1, an ask found,
  committed and the like; P1 for the title presentation codes) is tested on that code in each reading and on its
  disagreements; a figure over several codes with no single positive code needs 5 or more creators in all and
  disagreements from none or 5 or more creators, and a code both readings give alike is not tested on its own. A
  figure that fails reads "not published (fewer than 5 creators)"; its verdict is kept.
  - The second reading (Table 31) is counted from its readings: place and quantity are not published, and
    `\DblFcPlace` and `\DblFcQuantity` read "not published (fewer than 5 creators)".
  - The gate tables on the gate sample G (Tables 27 and 28) are counted from the items of every gate figure, rebuilt
    from the stored answers by the private `work/recount_agreement_g.py` (nothing sent; each recomputed point estimate
    equals the recorded one). Not published: checkability place and quantity at gates C and D; place, named actor and
    quantity against the large model; the hedge gap of gate E; the title presentation stability and the title source
    family at gate C; the ask stability of the final accepted asks.
  - The registry's figures of the owner's 00:30 decision are counted too: the place figure and the two title figures
    are not published; the time-window figure stays.
  - Counts of valid answers are given as shares, without their shortfalls, as the results file now gives them.
- **Deviations.** The table carries the registry rows to 23:34 (99 rows in six parts): the start of the exploratory
  round (23:17, exploratory) and the results file republished at 23:33 (23:34) are added. The simulation battery
  (21:52) is a budget or operations row; the rows of the results file (20:48, 22:33, 23:34) are reporting, which the
  caption now counts in "other", with the freeze-1 entry. The 22:33 row gives the rule in the registry's words ("0 or 5
  or more") and says that three hold-out checkability parts withheld at 21:50 were published under it. The caption's
  range reads 16:06 to 23:34.
- **Timeline.** Figure 14 runs to the registry's latest row (23:34 UTC): the republication of 22:33, the start of the
  exploratory round and the current version of the results file (23:33) are events; its caption says so, and the axis
  carries ticks to 21:00 on 21 November.
- **Contacts.** The registry's contact entry for the privacy recounts behind the results file (about 21:30 to 23:30)
  is read into Table 45; the table's widest column was widened so that it fits its page.
- **Length.** 59 pages; the main text is unchanged and still ends on page 8, the ethics statement on page 9.
- **Not checked.** The cross-vendor table (VER-3R units), the known-answer battery (constructed texts, recovery against
  a key, not agreement between readings), the hedge kappa and read precisions of the status table, and the
  pre-declared frame-only merge of 02:55 were not recounted.
