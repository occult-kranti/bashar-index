# Measurement-and-protocol paper (draft of 2026-11-21)

Assembled 2026-11-21, 06:45 to 07:15 UTC, revised after two reviews (methods; privacy and consistency) from 07:36
to 08:40 UTC, revised again from 11:10 to 12:00 UTC for the parts of those reviews the first revision never saw, the
page limit and the new facts (section 8), revised a fourth time from 12:24 to 13:10 UTC after a new methods review
and a new privacy review of the third draft (section 9), and brought up to the registry of 18:41 UTC, with the
first-round results wired in, from 19:16 to 20:15 UTC (results round, section 10; clock: `date -u`). It was then
rewritten section by section in a PaperOrchestra-style rewrite (2026-11-21 to 22; section 12, which also gives the
current section map, files and build state). This folder holds an anonymous ICWSM submission draft in the AAAI
two-column format, now titled:

> *Auditing Speech Recognition Without Human Transcripts on Online Channelling Recordings, with Lessons from a
> Registered, Then Amended, Protocol for Model-Coded Labels*

Its title before the rewrite was *What a Speech-Recognition Pipeline Does to Online Channelling Recordings: Agreement
Anchors, Decoding-Window Seams, and a Registered, Then Amended, Protocol for Model-Coded Labels*. Sections 1 to 11
below describe the draft before the rewrite; their section, table and page numbers are those of that draft.

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
the lead writes with `publish_results.py` from the private report. Until that file exists every result macro is a
`\pending` placeholder; once it exists, a rebuild fills Section 7.2, Table 2, the abstract, introduction and conclusion
sentences and the three results tables of Appendix B, for any outcome.

## 2. Files

| Path | What | Made by |
|---|---|---|
| `main.tex` | Integrator file: preamble, macro files, section order, bibliography, appendices. No prose. | integrator |
| `aaai25.sty`, `aaai25.bst` | AAAI 2025 author kit, copied unchanged from the old draft (SHA-256 in the header of `main.tex`) | copied |
| `sections/*.tex` | Title, abstract, Sections 1 to 9 (since the rewrite; 1 to 10 before it), ethics statement, Appendices A to C | writers A, B, C; revised in the review round; rewritten in the PaperOrchestra-style rewrite |
| `findings/numbers.tex` | Every number the paper uses, as a macro, one per line, with its source file and field in a comment. Only macros the paper uses are written; withheld macros never are | GENERATED |
| `findings/pending.tex` | One macro per placeholder; each expands to `\pending{...}` | GENERATED |
| `findings/results.tex` | The first-round result macros (`\Res...`), from the public results file; `\pending{...}` while it does not exist | GENERATED |
| `floats/tab_*.tex`, `floats/fig_*.pdf` (and `.png`) | Tabulars (the writers add float, caption, label) and figures | GENERATED |
| `floats/caption-notes.tex` | Base, unit and pooling of each figure, as macros | GENERATED |
| `floats/tab_results*.tex` | Results table (Appendix B since the rewrite; main text before it), both versions under the guard (two parts), robustness rows, Holm table | GENERATED |
| `refs.bib` | References verified in the old draft's reference work (Crossref or arXiv metadata) | writers A, C |
| `refs-new.bib` | Entries verified later by the lead; empty | lead |
| `refs-orchestra.bib` | 82 entries added by the rewrite's literature merge step, checked against Crossref, arXiv, DataCite, PMLR and OpenLibrary records; on the bibliography line of `main.tex` | literature merge step of the rewrite |
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
otherwise print 1 to 4 away from a creator total it prints or implies (hold-out 23, English-only hold-out 17, seen 71,
all 101, the other group (printed only as a bound, fewer than 10), the file's hold-out count) or above the English-only hold-out count. A scratch test of other outcomes
sets `ET_PAPER_PUB` (a copy of this folder), `ET_RESULTS_JSON` and `ET_RESULTS_ALLOW_SYNTHETIC=1`; it never writes into
this folder or the private work folder.

`build.sh` sets the PDF's dates in UTC (`SOURCE_DATE_EPOCH`, `FORCE_SOURCE_DATE`), and `main.tex` suppresses the pdfTeX
banner and the figures' info dictionaries, so the PDF carries no local time zone.

State of the build of 2026-11-21, 20:09 UTC (`\BuildStamp`; results pending): 517 macros written (only those the
paper uses), 12 pending macros and 18 result macros, 9 of them pending (33 placeholders in the PDF text by the paper
check), 0 errors, 0 undefined references, citations or macros, no float too large for its page; eight table cells run 1
to 2 pt over their column (no layout effect); builder checks 111 passed, 0 failed. The PDF has 53 pages: main text pages
1 to 8 (the conclusion and the start of the ethics statement on page 8), references pages 9 to 10, Appendix A pages 11
to 28, Appendix B pages 29 to 51, Appendix C pages 52 to 53. With the converter's synthetic documents (scratch copies,
section 10) the conclusion also ends on page 8.

The paper check (`check_paper.py`, run by `build.sh`) found at 20:13 UTC what it found at 13:00 UTC, with 55 creator
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

## 4. What waits for the first-round results and freeze 2

Every placeholder prints as **[pending: ...]** and is filled only by a later build from its source, never by hand.

| Waits for | Placeholders |
|---|---|
| The public results file of the first-round tests (the lead runs `publish_results.py` when the tests end) | the result macros of `findings/results.tex` (`\ResSummary`, `\ResAbstract`, `\ResStamp`, `\ResH<k>Kind`, ...) and the four `tab_results*` tables |
| H3 at the creator level on the hold-out | `\PendHThreeX` |
| Word error rate against possibly human-made texts of hold-out and other-group creators | `\PendBrbH` |
| Seen-creator model-coded descriptions under freeze 1 | `\PendLabV`, `\PendLabA`, `\PendLabF`, `\PendLabS`, `\PendLabT`, `\PendLabK` |
| Verification: effective number of readers; third reader on gate samples | `\PendVerDep`, `\PendVerAdjG` |
| Years and numbers against references; prediction timeline counts | `\PendBrY`, `\PendTlBuild` |
| Exploratory output status at report time (written by the builder in `tab_outputs.tex`) | `\pending{status table at report time}` |

Filled in the results round from the registry (no longer placeholders): freeze 2, A10's entry and addendum 2.
Stated in the text instead of a placeholder: CAL part (f) did not run (registry 16:06 (2)), and HR (a) and HR (b, c)
were not bought (18:41). When a source appears, add its reader to `build_numbers.py` (replacing the entry in its
`PENDING` list), run `bash build.sh --numbers`, and check the build log and the paper check. When the public results
file appears, `bash build.sh --numbers` (or `--results-only` followed by `bash build.sh`) fills the results.

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

- **Canonical literature.** Closed in the rewrite: `refs-orchestra.bib` holds verified entries for canonical works on
  channelling, and the rewritten Sections 1 and 2 cite them (Klimo; Brown; Hughes; Wooffitt). `refs-new.bib` stays
  empty.
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
- **Bridge (fourth round).** The paper prints the bridge as verdicts and tallies on the seen pairs only; each equals
  the verdict on all registered pairs. Printing the registered results as published instead, as the privacy review
  proposed, is the lead's decision (private fix list of the fourth round).
- **Projections (fourth round).** One count withheld in this round can still be bounded from printed projections; the
  private fix list of the fourth round states how, for the lead.

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
- **Open.** The public results file does not exist yet (the lead writes it). CAL part (f) did not run and is stated so.
  The disclosure scan named in the task (`pipeline/public_disclosure_scan.py` of this checkout) is not in this
  checkout; the privacy checkout's copy was run. The registry's row of 16:13 names the number of hold-out creators with
  English recordings, which this paper withholds (and which the printed projections already bound); the paper does
  not repeat it.

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

## 12. PaperOrchestra-style rewrite (2026-11-21 to 22)

Every section file was rewritten by one writer each, in the manner of the PaperOrchestra multi-agent paper-writing
method (outline, literature step, section writers, integrator, reviewers and verifiers, all Anthropic model agents; no
code of that method and no outside model API ran). The house rules of the earlier rounds hold: numbers only through
the macros of `findings/*.tex`, the privacy rules, the registered wording, limitations stated.

- **Title.** *Auditing Speech Recognition Without Human Transcripts on Online Channelling Recordings, with Lessons from
  a Registered, Then Amended, Protocol for Model-Coded Labels* (`sections/title.tex`).
- **Section map.** 1 Introduction; 2 Related work; 3 Corpus and pipeline (3.1 corpus, 3.2 pipeline); 4 Measuring the
  pipeline without a human reference (4.1 agreement anchors and the two-model bridge, 4.2 window seams and the grid
  shift, 4.3 the apparently inserted phrase and the positional filter, 4.4 time without speech and coverage, 4.5
  variance and error tolerance); 5 the internally registered, then amended, protocol (5.1 registry, hold-out and
  freezes, 5.2 instruments and gates, 5.3 amendments and the guard, 5.4 verification without a person); 6 the first
  round (Table 1, the registered hypotheses and their state; 6.3 the results as registered, H3); 7 deviations and
  lessons; 8 limitations; 9 conclusion; ethics statement. Appendix A: measurement records; Appendix B: protocol records
  (B.7 holds the first-round results tables, `tab_results*`); Appendix C: the paper checklist.
- **Bibliography.** `main.tex` reads `refs`, `refs-new` and `refs-orchestra` (file table, section 2).
- **Builder outputs.** `findings/` and `floats/` are those of the private builder's run of 22 November 2026, 00:15 UTC
  (`\BuildStamp`), copied unchanged; the rewrite never runs `build.sh --numbers`. They carry the lead's rule of
  21 November, 22:33 UTC for agreement figures (a figure that fails it reads "not published (fewer than 5 creators)"),
  the public results file as republished at 23:33 UTC (schema 1.3.0), and the deviation table to the registry row of
  23:34 UTC. The lead then ran the builder against the rewritten sections (22 November 2026, 01:51 UTC; section 13),
  which leaves out the 23 macros the rewritten text does not use.
- **Final verification fixes (2026-11-22, to 01:45 UTC).** Wording for the withheld agreement figures and the rule in
  the gate and second-reading captions; the results file's three republications; the deviation rows of 23:17 (the
  exploratory round, on code written after freeze 2) and 23:34; the privacy recounts behind the results file in the
  contact lists; the position confound of voice spans; a main-text statement on the exploratory reporting plan; the
  90% level of three intervals of Section 5.4; citation wording (religion online, correlated errors, forced alignment,
  reliability minimums).
- **Build state (2026-11-22, 01:45 UTC).** 68 pages: main text pages 1 to 8 (the ethics statement ends on page 8),
  references pages 9 to 11, Appendix A pages 12 to 32, Appendix B pages 33 to 66, Appendix C pages 67 to 68. No LaTeX
  error, no undefined reference, citation or macro, no float too large; nine table cells run up to 3.7 pt over their
  column. The paper check found no privacy-name hit, no risky disclosure phrase, no nested creator-count pair, no
  undefined macro and no missing citation.

## 13. Lead's decisions on the rewrite's open items (2026-11-22, 01:51 to 02:10 UTC)

The final verification left five items to the lead (registry row of 2026-11-22 01:55).

- **The other group's size.** It follows by difference from counts public on the main branch (roster, seen and hold-out
  creators), and the registered plan files there print it. What it shows is run coverage, not a value of anyone's
  speech. Those files are hashed records and are not edited. The paper
  keeps the bound and its privacy rule now names this exception (Section 3.1).
- **Entrance-cue read precision.** These rows are agreement figures under the rule of 21 November, 22:33 UTC, so the
  items read off target must also come from no creator or from 5 or more. The development row (one off-target item,
  hence one creator) is withheld. The check row's off-target items come from 5 or more creators (counted by script from
  the private sample file, counts only) and stay. The anchors table's source comment no longer describes the withheld
  value.
- **Commits, hash prefixes and script names.** They stay in this public draft. It sits in the project's own public
  repository, and the hashes are the evidence of the registration. A copy for double-blind review would print them as
  "withheld for anonymous review" and use role words for the scripts.
- **Bibliography.** The rewrite corrected entries in `refs.bib` against their records, against its own rule of not
  editing that file. The corrections are kept. The Wooffitt entry's note now says that its DOI is the 2017 reissue's.
- **Submission.** The paper is not to be submitted before an ethics or exemption determination exists. The checklist
  answer (Appendix C, 1(i)) now says so. The main text is at its page limit, and its ethics statement already says
  that no determination exists.
- **Build state (01:51 UTC).** The builder was run against the rewritten sections (`bash build.sh --numbers`): 163
  checks passed. 68 pages: the main text and ethics statement end on page 8, and the references start on page 9. The
  paper check is clean: no unused macro in `numbers.tex`, no nested creator-count pair, no privacy-name hit, no risky
  phrase.
- **History.** The rewrite replaces the measurement paper in place. The draft it replaces stays in the history of the
  main branch (pull request 102).
