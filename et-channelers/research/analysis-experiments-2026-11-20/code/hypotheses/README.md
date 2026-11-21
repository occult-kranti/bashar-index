# Analysis code for H1, H2, H4, H5, H6 and H9

Status, 2026-11-20 (evening, EST), revised 2026-11-21 (track B), after the lead's decisions of 2026-11-21 04:55 UTC (section
"Decisions of 2026-11-21 04:55"), 06:44 UTC (section "Decisions of 2026-11-21 06:44"), 09:19 UTC (section "Decisions of
2026-11-21 09:19"), 11:08 UTC (section "Decisions of 2026-11-21 11:08") and 12:52 UTC (section "Decisions of 2026-11-21
12:52"), and with the FREEZE2 constants entered (section "FREEZE2 constants"); this text brought in line with the code on
2026-11-21 between 14:07 and 14:36 UTC (task fingerprint `908111b94170...` at 14:10:38 UTC). The hypothesis code has
been tested on **synthetic data and constructed numbers only**. No hypothesis quantity has been computed on real labels of
any creator (the rule against estimates during development), and no hold-out label exists. Real seen data have been read
for freeze 2 only, outside any hypothesis estimate: by the seen feature step (`features.py seen`, runs of features-2,
features-3 and features-4, the last 13:01:12 to 13:02:48 UTC), which read the seen transcripts through `prep.load_units`
and its guard (its checks, recorded in the private features note, also read structural fields of the seen voice label
files), and by the seen-only path (`run.py constants`, 14:00:03 to 14:00:37 UTC, exit 0), which read `labels/seen` of the
production label tree and printed the three FREEZE2 constants, the values beside them and the A10.7 null means, as counts
and derived numbers only.
No API call was made. The adapter
follows `llm/design/label-files.md` (the data dictionary of produce.py's freeze integration). The code is to be hashed at
freeze 2 (`python -I run.py hashes` prints the two keys of the freeze-2 record that describe it); until the one freeze-2
record, `llm/freeze2.json`, matches this code (it did not exist at 14:10:38 UTC), the adapter opens no folder or file that
the synthetic generator has not marked (the permission check runs before anything is listed or opened) and refuses every
label file that is not marked `"synthetic": true`, with one exception: the seen-only path (`adapter.load_seen_bundle`,
`run.py constants`), which opens `labels/seen` of the production label tree only, for the FREEZE2 constants, the A10.7 null
means and CAL part (f).

Run everything with the guarded interpreter `C:\Users\mehta\et-channelers-tools\analysis-venv\Scripts\python.exe -I`
(memory ceiling per process tree, at most four workers, below-normal priority; registry, lead's decision of 2026-11-21
02:00 UTC). Worker counts default to `os.cpu_count()`, which that venv caps at 4; the pool is capped by it as well.

Every result this code produces on real labels is **model-coded**: no person has checked a label (A8). The strongest
verdicts are "supported (model-coded)" and "refuted (model-coded)", each followed by "verified by a third model, on
known-answer texts and by a reader of another vendor" with the figures from the config (registry 03:08). The word
"validated" is never written; verification figures that contain it are refused.

**Revisions of 2026-11-21 (track B; registry rows 02:50, 02:55 and 03:08), synthetic data only.** H2's shared-wording
flag and retained parts; H5's self-naming exclusion and three Q2 assignments; claimed voice = V2 + V3 for H1 and H6 with
the relayed-only rows flagged "below the reliability floor"; amendment A10 (A10.1 to A10.7) with the guard that computes
the registered and the amended version of every replaced estimator, reference, minimum or interval; the uninformative
flag; the verdict wording; the exclusion counts of every label source and the hold-out cross-check against TABLE.
**Decisions of 04:55 (registry rows "Hypothesis code, decisions on the freeze-readiness open points" and "Second
reading").** H4's primary back on the embodied voice (V2), with V2 + V3 a secondary without a verdict; the
model-stratified recognizer row; H5's HKSJ random-effects sensitivity row; the registered creator-bootstrap intervals of
H2, H5 and H6 drawn creators then recordings (R1); SC5 out of H2's flag; the permission check before any file is opened;
"not determinable" when either guarded version is; the wider MH interval of H5 and H6 (a constant freeze 2 can switch);
H2's FRAME time-window row. **Decisions of 06:44 (registry row "Hypothesis code, decisions on the second verification").**
(1) the seen-only path and `run.py constants`; (2) one freeze-2 record, `llm/freeze2.json` with the six keys of 02:45; (3)
H6's amended OE and MH rate ratio centred per recording; (4) H9's creator bootstrap two-stage (creators, then recordings,
cells re-rarefied in every draw) in both versions; (5) A5 of H5 and H6 on both the t interval of the creator OE values and
the wider MH interval; (9) creator-by-model strata for H5 in the model-stratified row. **Decisions of 09:19 (registry
row "Hypothesis code, decisions after the third verification").** (1) H6's amended p from a conditional Monte Carlo
reference under the per-recording null in place of the sign-flip of OE, and the battery's null scenario with claimed
shares below one half and 1 to 3 asks per creator; (2) the A10.7 tolerance of the OE versions on the OE scale; (3) the
null check keeps recordings without an ask file; (4) the verifier's test file that globbed the production label tree
left the package. **Decisions of 11:08 (registry row "Hypothesis code, decisions after the fourth verification").** (1)
H6's amended p is the larger of a cluster-level conditional Monte Carlo p and the sign-flip p of OE, with 99,999 draws in
the analysis, the battery's `null_burst` scenario and H6's detectable-effect note from the battery; (2) and (3) H9's
content words exclude every token of every family variant, and contractions whose parts are function words count as
function words (features-3); (4) the flat-list mask stays, and the 9 seen transcripts without a stated model enter the
model-stratified row as unknown model. **Decisions of 12:52 (registry row "Hypothesis code, decisions after the fifth
verification").** (1) H6's clusters chain asks within 5 units of each other, with a 10-unit sensitivity row, the
statement in every H6 result that dependence of asks beyond the window is not modelled, and the battery's `null_gapped`
scenario; (2) asks of one class whose unit ranges overlap are counted once; (3) ain't and y'all split into function words
(features-4); (4) a bundle whose feature files mix feature versions is refused; (5) the wide mask of 11:08 (2) stays; (6)
the FREEZE2 constants computed through the seen-only path, recomputed by a second reader and entered. Sections
"Revisions of 2026-11-21", "Decisions of 2026-11-21 04:55", "Decisions of 2026-11-21 06:44", "Decisions of 2026-11-21
09:19", "Decisions of 2026-11-21 11:08", "Decisions of 2026-11-21 12:52" and "A10 and its guard".

## Files

| File | Role |
|---|---|
| `constants.py` | PROCEDURE: every choice the texts leave open, the minimums, smallest effects, seeds, draws, wording. `FREEZE2` values are entered from seen labels before freeze 2 (done 2026-11-21, section "FREEZE2 constants"; H9's smallest effect is still the placeholder 0.2); `CHOICE` values are listed below for the owner |
| `stats.py` | estimators and references, standard library only: exact sign-flip (meet in the middle) and Monte Carlo above 20 creators, Holm over the fixed count, HKSJ random-effects pool with prediction interval, the DerSimonian-Laird pool with normal intervals (registered versions), t quantiles, creator bootstrap and two-stage bootstrap, Somers' D, Mantel-Haenszel rate and odds ratios, permutation p, detectable effect |
| `adapter.py` | the only module that reads label files (formats below); the freeze-2 guard on the one record `llm/freeze2.json` (`freeze2_problem`, `freeze2_entry`) and the permission check before any file is opened (`open_problem`); the seen-only path (`load_seen_bundle`, `seen_open_problem`, `read_seen_json`); the ASR-model rule, its model-stratified view and the hold-out cross-check against TABLE; H2's shared-wording ids and the voice cues; asks of one class on overlapping unit ranges counted once (`merge_overlapping_asks`, `ask_overlap_counts`; registry 12:52 (2)) and the refusal of a bundle whose feature files mix feature versions (`require_one_feature_version`; 12:52 (4)) |
| `features.py` | per-unit timing, syllables, letters and contraction counts (H1, H4) and per-recording token counts (H9) from a word list; H9's token rule (`h9_parts`) and names input (`h9_mask_forms`); a seen-only command, run on the seen transcripts (features-2, features-3 and features-4, 2026-11-21; FEATURE_VERSION features-4 since registry 12:52 (3)) |
| `voice_sets.py` | claimed and own voice per unit under one definition (model, rule A or B, broad or strict own voice, claimants); the claimed side per hypothesis (`primary_definition`: H1 and H6 V2 + V3, H4 V2; `merged_claimed`, `embodied_only`, `relayed_only`, `below_floor`); spans; the self-naming units of H5; the voice multiverse rows |
| `wording.py` | the fixed wording rules of M9: `shared_wording` (H2's flag) and `self_naming` (H5's fallback), pattern ids out, never text |
| `h1_rate.py`, `h2_hedging.py`, `h4_contraction.py`, `h5_world_claims.py`, `h6_asks.py`, `h9_family.py` | one module per hypothesis: eligibility from labels only, the estimate, the Holm p, intervals, registered conditions, the registered version under the A10 guard (`registered_version`), secondary rows, tipping-point table |
| `a10_checks.py` | A10.7: null means on seen creators of every estimand under its reference (registered and amended versions), each flagged against a tenth of its smallest effect on its own scale (the OE versions of H5 and H6 on the OE scale, 09:19 (2)); H6's null places each cluster of a recording's asks in one voice (11:08 (1), clusters at the 5-unit window of 12:52 (1)); and H6's planted check at the seen margins |
| `tipping.py` | tipping-point arithmetic |
| `verdicts.py` | Holm with the count fixed at 10, the A10 guard, the verdict rules, the uninformative flag, the verdict wording and the sentences that go with every result |
| `report.py` | public `report.json` and `report.md` (counts and derived numbers only; both versions of the guard), private `report.private.json` (creator-level values) |
| `progress.py` | progress with ETA, deterministic parallel map |
| `simulate.py` | synthetic generators and the simulation battery (H6's null scenarios `null_heterogeneous`, `null_sparse_low_share`, `null_burst` and `null_gapped`); `require_fingerprint` (the frozen-fingerprint check) and `plan_estimate`; the exact levels of H6's p values on constructed numbers (`h6_reference_levels` of 09:19; `h6_cluster_levels`, `h6_cluster_level_cases`, `h6_gapped_level_cases` and `h6_cluster_reference_levels` of 11:08 (1) and 12:52 (1)) |
| `sim_cost.py` | the battery's cost model (seconds a repetition per hypothesis at 12 and 17 creators, H9 as a base plus a part per bootstrap draw): the ETA, the planned wall time (`run.py simulate --estimate`) and the largest-first order of the tasks; outside `simulate.TASK_MODULES`, so it changes no fingerprint and no task result |
| `run.py` | command line |
| `analyse-config.template.json` | the confirmatory config template: hold-out and seen label folders, the ASR-model rule, the hold-out cross-check on, the verification figures to fill |
| `tests/` | unit tests (`python -I run.py selftest`): `test_stats.py`, `test_rules.py`, `test_label_files.py` (the layouts of label-files.md, the refusals, the checkpoint), `test_asr_rule.py` (the ASR-model rule), `test_revisions.py` (the revisions of 2026-11-21: pattern lists, H2 flag and parts, H5 exclusion and Q2, the claimed side per hypothesis, A10 guard, uninformative, wording, cross-check, counts per source, A10.7; and the decisions of 04:55: the permission check before opening, "not determinable" under the guard, the MH interval, the two-stage registered intervals, H5's HKSJ row, H2's FRAME row, the model-stratified row, no silent wave, the A10 numbering), `test_decisions_0644.py` (the decisions of 06:44: the seen-only path on synthetic labels/seen trees, links and wrong groups refused, the group read first; the one freeze-2 record and its fail-closed keys; H6 centred per recording and its null check; H9's two-stage re-rarefied bootstrap; A5 on both intervals; H5's creator-by-model strata), `test_decisions_0919.py` (the
decisions of 09:19: H6's conditional reference against exact enumeration, its level on constructed numbers, the sparse
low-share null scenario, the OE-scale tolerances, the null check with recordings without an ask file, and a scan that no
source of the package names the production label tree's hold-out or other folders), `test_decisions_1108.py` (the
decisions of 11:08 (1): the clusters, the cluster-level reference against its exact law, the amended p as the larger of
the two, the levels on constructed numbers against the code path, the `null_burst` scenario, the A10.7 null under
clusters, H6's detectable-effect note from the battery; one assertion written for the 11:08 clusters now passes
`window=1`), `test_decisions_1252.py` (the decisions of 12:52 (1), (2) and (4), 22 tests: the 5-unit window and the
10-unit row, the statement in the result and the report, the `null_gapped` scenario, the levels of the amended p inside
and beyond the window, the merge of overlapping asks and its counts in counts.json before outcomes, the refusal of mixed
feature versions), `test_features_h9.py` (H9's token rule of features-3 and features-4, the names input, ain't and y'all,
and the closed list of H4's contractions; synthetic strings only), `test_sim_cost.py` (the cost model against timed repetitions, the table independent of the task order, `--estimate` runs nothing, `--expect-fingerprint` refuses another fingerprint before anything is written) |

## Commands (always `python -I`, guarded venv)

```
python -I run.py selftest                       # 224 unit tests (4 of them still assume the FREEZE2 constants unset:
                                                # see "FREEZE2 constants")
python -I run.py simulate [--quick] [--workers N] [--no-checkpoint]   # the simulation battery, resumable; writes sim_out/
         [--expect-fingerprint FP]              # refuses to start unless simulate.TASK_MODULES hash to FP (in full or its
                                                # first 12 or more digits), before anything is written
         [--estimate]                           # prints the planned CPU and wall time on N workers (sim_cost.py); runs nothing
python -I run.py e2e [--workers N]              # one synthetic dataset as label files -> full analysis -> report, twice;
                                                # checks the ASR plant, the cross-check plant, the counts of an extra
                                                # source, the model-stratified row's counts, the absence of the word
                                                # "validated" and the repeat
python -I run.py analyse CONFIG.json [--workers N]  # the confirmatory run (refused on real labels before freeze 2)
python -I run.py constants [--labels DIR] [--draws N] [--out FILE]
                                                # the FREEZE2 constants and the A10.7 null means from labels/seen only
                                                # (the seen-only path, registry 06:44 (1)); counts and derived numbers only
python -I run.py hashes                         # analysis_code_sha256 and constants_sha256 for llm/freeze2.json, the
                                                # simulation task fingerprint, and the freeze-2 status
```

`analyse` and `simulate` print progress lines on stderr: tasks done, share of the work, elapsed time, ETA and the clock time
of completion; the same is written to a status file (`sim_out/simulation-status.json`, `OUT/analysis-status.json`) with the
process id, so the ETA of a detached run can be read at any time. The ETA weights each task by its declared cost: in
`simulate`, the expected seconds of `sim_cost.py` (repetitions times the measured seconds of one repetition at the task's
creator count; H9 a base plus a part per bootstrap draw, so it follows `simulate.H9_BATTERY_BOOTSTRAP_DRAWS`); the same
figures order the tasks largest first and give `run.py simulate --estimate`. Both run their tasks in worker processes; each
task carries its own seed label, so results do not depend on the number of workers or the order in which tasks finish, and
`simulate.run` hands the rows to the table in a fixed order (experiment, then first repetition), not the cost model's
(tested: `test_parallel_equals_serial`, `test_sim_cost.test_table_does_not_depend_on_the_order_of_the_tasks`, and `e2e`
compares two runs with different worker counts).

**Checkpoint.** `simulate` appends every finished task to `sim_out/simulation-checkpoint.jsonl` (one line per task, written
by the parent, flushed and synced). Rerunning the same command skips every task found there under the same code
fingerprint (sha256 over the modules a task's result depends on, `simulate.TASK_MODULES`: every module except `run.py`,
`report.py`, `progress.py` and `sim_cost.py`; `run.py hashes` prints it, and `run.py simulate --expect-fingerprint FP`
starts a battery only on the fingerprint FP the lead declares frozen); a torn last line is ignored. A resumed battery gives the same table as a fresh one (tested on a small plan:
resumed, fresh with two workers and fresh with one worker are identical). The first full run (30 workers, before the
guard) died at 20:43 local with 121 of 842 tasks done, in the out-of-memory failure of the machine; nothing of it was kept.
Its log is `sim_out/simulation-run-1-died-2026-11-20T2043.log`.

`analyse` first applies the ASR-model rule (below; with the hold-out cross-check when the config turns it on), computes the
eligible counts from labels only and writes `counts.json` (the eligible counts and the rule's exclusions per group, for the
primary source and every extra source) before any outcome is computed (A10.2 = CAL-A9), runs the A10.7 null-mean check on the seen
creators, then runs every hypothesis and every multiverse row as separate parallel tasks, applies the verdict rules and the
A10 guard and writes the report.

## Rules applied

* **A5.** "Supported" needs the 90% interval over creators to exclude zero: the HKSJ 90% interval for the pooled estimands
  (H1, H2, H4), for H5 and H6 both the t interval on the creator OE values (the values the Holm test uses) and the interval
  the MH estimate carries (registry 06:44 (5); `conditions.a5_parts` shows each), the creator-bootstrap interval for H9
  (A10.7 = CAL-A14; two-stage, registry 06:44 (4)). The MH estimates of H5 and H6 carry the wider of the creator-bootstrap
  percentile and the jackknife t interval (registry 04:55 (j)); that interval also decides their refutations and the
  uninformative flag.
* **A8 and the wording of registry 03:08.** Verdicts are "supported (model-coded)", "refuted (model-coded)", "not determined", or
  "not determinable"; every result carries the model-coded sentence and the verification sentence. A supported or refuted verdict
  also has `verdict_statement`: "supported (model-coded), verified by a third model (F1), on known-answer texts (F2) and by a reader
  of another vendor (F3)", with F1 to F3 from the config (`"verification": {"all": {"third_model": ..., "known_answer": ...,
  "cross_vendor": ...}, "<H>": {...}}`; a missing figure prints "figures not entered"). A figure containing "validated" is refused.
* **Uninformative (registry 02:50).** `uninformative` is true when the verdict is not determinable, or the 90% creator interval of
  either version contains both zero and the smallest effect of interest in either direction (`constants.UNINFORMATIVE_SESOI`, on
  the interval's scale: H1 0.05 on the log ratio, H2 0.10, H4 0.5, H5 0.4 on the MH log odds ratio, H6 log 2 on the log MH ratio,
  H9 0.2); `uninformative_reasons` says why. Rows carry the flag too.
* **A10 (registry 03:08), written from the calibration item's drafts** (`panel-second-round-2026-11-20/r2-runs/CAL/private/amendment-drafts.md`,
  numbered A8 to A14 there and cited as CAL-A8 ... CAL-A14 here, because the registry's own A8, A9 and A11 exist). The seven
  items of the registry row are the seven drafts in order: A10.1 = CAL-A8, A10.2 = CAL-A9, A10.3 = CAL-A10, A10.4 = CAL-A11,
  A10.5 = CAL-A12, A10.6 = CAL-A13 (H7, unrun), A10.7 = CAL-A14 (A10.k = CAL-A(7+k), registry 04:55 (l); the test
  `test_revisions.A10Numbering` checks every pairing in the code and here). The guard is described in "A10 and its guard":
  * A10.1 (CAL-A8): the p that enters Holm is creator-level: exact sign-flip up to 20 creators, 99,999 Monte Carlo draws above
    (H1, H4 one-sided; H2 two-sided; H5 one-sided on OE); H6's amended p is the larger of the cluster-level conditional
    Monte Carlo p of the mean OE and the sign-flip p of OE (registry 11:08 (1) and 12:52 (1), amending 09:19 (1); A10.4
    below); H9 keeps its registered family-label permutation. Within-creator
    references (H2's permutation within creator and band) are secondary rows and never enter Holm. Holm count fixed at 10;
    H3 and H8 enter as run with p = 1; H7 and H10 (unrun) at p = 1. Refutations read from intervals are labelled unadjusted.
  * A10.2 (CAL-A9): "not determinable: too few eligible creators (k of m)" below each minimum, with p = 1 in Holm and the
    estimate kept as description; the eligible count is computed from labels before outcomes; minimums 12 for H1, H4, H5, H6
    (registry), 9 for H2 (A10.3), 8 one-sided for H9 plus a reference that can reach 0.005; the detectable-effect note ("run;
    detectable only from X") when the config gives the SD of creator values from the label-based CAL repeat; H6's note comes
    from the simulation battery's power instead (registry 11:08 (1), CHOICE 26).
  * A10.3 (CAL-A10): H2's minimum raised from 8 to 9 creators with 30 verified statements.
  * A10.4 (CAL-A11): H6: a, b, T per creator and T_i, s_i per eligible recording (s_i = wc_i / (wc_i + wo_i), the claimed
    share of the words in the two voices); T = 0 excluded and counted; creator value OE = (a - sum_i T_i s_i) / T, centred
    per recording (registry 06:44 (3); CAL-A11's a/T - s pools s over the recordings); Holm p one-sided, of the mean OE over
    the creators with T >= 1, the larger of two p values (`h6_asks.amended_p`; registry 11:08 (1), amending 09:19 (1)): the
    cluster-level conditional Monte Carlo p (`h6_asks.conditional_p` by "cluster": a recording's asks within 5 units of
    each other chain into one cluster, registry 12:52 (1), and the reference draws each cluster's voice as one unit,
    claimed with the recording's claimed share s_i and all its asks with it; p = (b + 1) / (m + 1), m =
    `h6_asks.REFERENCE_DRAWS` = 99,999, from a stream seeded by the label) and the sign-flip p of OE that the draft names
    (exact up to 20 creators); the ask-level conditional p of 09:19 (1), a_i ~ Binomial(T_i, s_i) given T_i, is shown beside
    them and enters nothing; every H6 result states that dependence of asks beyond the window is not modelled, and a
    10-unit window is a sensitivity row; asks of one class on overlapping unit ranges count once (12:52 (2)); estimate the Mantel-Haenszel rate ratio with creator-by-recording
    strata; half-count log ratio as a sensitivity row; per-creator logs only for T >= 5 (private file); run condition 8 or more creators with T >= 1 besides the
    12 with both voices. H5: OE = W_A/T_A - (W_A+W_B)/(T_A+T_B) (centred within each model in the model-stratified row, 06:44
    (9)); estimate the Mantel-Haenszel odds ratio (strata creator, or creator by model in that row); minimum on the margin only
    (T_A >= 10 and T_B >= 10); the registered per-side rule as a row.
  * A10.5 (CAL-A12, kappa gate) is applied through the `gates` input: an instrument below its floor gives "not run for want of an
    instrument: below the reliability floor" (registry 01:15 and 01:30, A10.5), p = 1 in Holm, counted as not determinable
    and so uninformative. The gate figures themselves come from the reliability runs, not from this code.
  * VG-6 (registry 03:21): the config's `"cross_vendor_voice": {"passed": false, "kappa": k}` caps H1, H4 and H6 (and their
    rows) at "not determined" with the flag "readers of two vendors disagree (kappa k)"; a pass or no entry changes nothing.
  * A10.6 (CAL-A13): H7's estimator, reference and margin; H7 is not run in the first round (p = 1 in Holm). When it is run,
    its verdict must hold against both margins, the placeholder 0.01 and k x SD_L (registry 04:55 (i)); not coded.
  * A10.7 (CAL-A14): t interval on creator means; HKSJ with t(k-1) for the pools and for H5's random-effects sensitivity row
    (registry 04:55 (c)); the two-stage bootstrap of R1 as a sensitivity row of H1 and H4; point 3, the null-mean check on
    seen creators and planted-effect recovery: `a10_checks.null_means` (before freeze 2 through the seen-only path, `run.py
    constants`, registry 06:44 (1); in `report.json` under `meta.a10_7_null_means_on_seen_creators`, computed on the seen
    creators of the primary source) and the simulation battery.
  * H10 is not run in the first round (p = 1 in Holm; registry 04:55 (m)); its two readers are replaced before it is run.
* **Primary definitions** (registry, before freeze 1): broad own voice, and an offer alone does not end a claimed voice (rule B
  of `voice.py`). Under rule B a unit moved into a claimed voice is never own voice. Rows: rule A, strict own voice, rule A with
  strict own voice ("labels as the model gives them"), the second model, claimant `cannot_tell` admitted.
* **Punctuation.** "The voice label responds to punctuation and case." goes with every result of H1, H4 and H6.
* **Owner decisions before freeze 1** are carried as disclosure sentences: H2's checkability record is the middle model (gate
  failed for time window and place); H5 and H9 use the title record "final" (middle model, the large model on disputed titles;
  gate failed). The middle model without adjudication and the small model are rows.

## Revisions of 2026-11-21 (registry rows 02:50, 02:55 and 03:08)

**H2, shared wording (02:50, meta-review M9).** The checkability codebook (`llm/prompts/forecasts_fc.txt`) sets the observable
outcome to NO for "outcomes that cannot fail (either A or B)" and for "outcomes that the wording itself withdraws ("in some
sense", "on another level")"; the commitment codebook (`forecasts_fd.txt`) counts "talk of probability or of one possible
scenario", "one scenario is", "a disclaimer that the speaker is not saying it will happen" as hedges and "which of several
scenarios comes about" ("in one scenario ..., in the other ...", "in one timeline <X>, in another <Y>") as condition CE. The
same words lower both variables. `wording.shared_wording` flags a statement whose wording holds one of the patterns of
`constants.H2_SHARED_WORDING`:

| Id | Kind | Pattern (lower-cased wording) |
|---|---|---|
| SC1 | scenario | `scenario`, `scenarios` |
| SC2 | scenario | `one / another / other / either / alternate / alternative / different / several / two / three / multiple / many / possible / potential / probable` (+ optional `possible / potential / probable`) followed by `timeline(s) / futures / outcomes / possibilities` |
| SC3 | scenario | `either ... or` within one sentence (at most 80 characters between) |
| SC4 | scenario | `either way`, `one way or the other / another`, `whichever way / happens / comes / it goes` |
| WD1 | withdrawal | `in some / a / one / certain sense`, `in some way(s)` |
| WD2 | withdrawal | `on another / a different / other / some level(s)`, `on a higher / deeper / inner / energetic / spiritual / soul / subtle / other / different level`, `on the energetic / spiritual / soul / inner / higher / astral / etheric level` |
| WD3 | withdrawal | `energetically`, `metaphorically`, `symbolically`, `so to speak` |
| WD4 | withdrawal | `not / never saying / predicting / promising` (covers "I'm not saying it will") |

The rule reads the wording only (`statement_quote` of label-files.md, and a sentence field where a file carries one, or the
ids if a file carries `shared_wording` itself), never a code: a flag that read the codes would select on the outcome. The
adapter keeps only the ids, not the wording. H2's primary row uses the unflagged statements (eligibility, 30 statements per
creator, counts them); the row "flagged statements included" is reported beside it with its own verdict; the eligibility
record counts the flagged statements by pattern. Tests: `test_revisions.SharedWording`, `H2Revisions`. Registry 04:55 (e):
the former SC5 (`one / another / a possibility`, a plain commitment hedge, not scenario wording) left the list; the other
ids are not renumbered.

**H2, retained parts (02:50).** The score counts the parts in `constants.H2_PARTS_RETAINED` (FREEZE2), the parts whose
prevalence on seen statements is at least `H2_PART_PREVALENCE_MIN` = 0.05 (`h2_hedging.parts_from_seen`: weighted share of
verified, non-duplicate statements with a record reading in which the part is YES in STATEMENT or CONTEXT; CHOICE: flagged
statements included, because the prevalence describes the instrument). The five-part score is the row "all five checkability
parts". With no part retained, H2 is "not determinable: no checkability part reaches 5% prevalence on seen statements".

**H5 (02:50).** Units next to a self-naming cue are left out on both sides: the unit that holds a self-introduction of a
claimed source and the unit after it. The cue comes from the voice label file: every unit view carries its span's cue
(`[cue type, cue unit]`, voice.py), and the cue units of type `self_name` of the label of record are the self-naming units
(`voice_sets.self_naming_units`). Where a voice file carries no cue, the feature files' `self_name` flag (`features.py`,
since FEATURE_VERSION features-2, unchanged in features-3 and features-4; patterns `constants.SELF_NAMING_PATTERNS`: "I am / I'm / we are / we're (the / a) <Capitalised>",
"this is <Name> of / from the", "my / our name is", "I am / we are known as / called", "we are a / the collective / council /
group / federation / consciousness / family / alliance of") is the fallback; it cannot tell a source from a person naming
themselves, so it can only remove more. A recording with neither is counted under `recordings_by_cue_source: none`. The
eligibility record holds the counts (recordings by cue source, units and points left out per side). Three Q2 assignments
(`constants.H5_Q2_ASSIGNMENTS`): as registered (the primary: Q2 on neither side), merged with Q1 (world = Q1 + Q2; the former
sensitivity A), excluded (every unit with Q2 as primary or secondary code leaves the sample; a recording coded whole is
rescaled without them). The two besides the primary are multiverse rows with their own verdicts, and the primary result's
secondary block "Q2 assignments (M9)" lists all three side by side. The row "units next to a self-naming cue kept" shows the
estimate before M9.

**Claimed voice (02:55; H4 changed back at 04:55 (a)).** Gate D's specific-V3 row failed on its bound after the one
revision, so relayed voice is merged into claimed voice: `constants.REGISTERED_CLAIMED` = ("V2", "V3") is the claimed side of
H1 and H6 and of all their multiverse rows and extra sources. H4 keeps the embodied voice (V2) that hypotheses.md registers
(`constants.CLAIMED_BY_HYPOTHESIS`, see "Decisions of 2026-11-21 04:55"). The relayed-only secondaries of H1 ("relayed
only") and H4 ("relayed spans (estimate)") carry `flag: "below the reliability floor"`, the note and `verdict: null`, and
report.md prints them as such. The synthetic generator plants H4's drop in the whole claimed voice (V2 and V3 alike).

**Verdict wording, uninformative flag**: see "Rules applied" above.

**Recognizer-rule follow-ups (verifier of the ASR fix).** `counts.json` holds the rule's exclusion counts of every label
source under `asr_model_rule_by_source` (the extra multiverse sources too), written before any outcome. The optional hold-out
cross-check (`"holdout_model_crosscheck": {"table": TABLE's private recordings.csv, "enabled": true}`, on in
`analyse-config.template.json`) compares, at analysis time, each hold-out recording's model role from its label files with
TABLE's resolved model: `adapter.load_table_models` takes from the CSV header the index of an id column (`video_id` or
`audio`) and of the model column (`asr_model_resolved`, else `asr_model`, `model_role`, `model`) and keeps only those two
cells of the rows of the bundle's hold-out recordings. It is refused before freeze 2 (`freeze2.json` must match), except in a
synthetic run whose config marks the table synthetic; the file is not opened to decide. A recording the rule keeps but whose
table model differs is excluded (`excluded_crosscheck_mismatch`); per group `crosscheck` counts checked, agree, disagree (by
label/table pair), not in the table and table states none.

## Decisions of 2026-11-21 04:55 (registry rows "Hypothesis code, decisions on the freeze-readiness open points" and "Second reading")

Each item as implemented; tests in `tests/test_revisions.py` unless named otherwise. Synthetic data only.

* **(a) H4's claimed side.** H4's primary is the embodied first-person voice (V2), as hypotheses.md registers it
  (`constants.H4_CLAIMED`, `CLAIMED_BY_HYPOTHESIS`; `voice_sets.primary_definition("H4")`); relayed units are on neither side.
  Every H4 multiverse row and extra source uses V2 (`run.row_specs`, `run.run_row`), and `counts.json` counts V2. The merged
  claimed voice V2 + V3 is the secondary "claimed voice V2 + V3 (merged, registry 02:55; secondary, no verdict)" with
  `verdict: null` and `constants.MERGED_CLAIMED_NOTE`; report.md prints it. H1 and H6 keep V2 + V3. In the calibration mode
  of the generator each creator's first recording with both voices is embodied, without an extra random draw, so H4's
  boundary rows still change only the count. Tests: `ClaimedVoice` (the old `test_every_registered_quantity_uses_v2_and_v3`
  asserted V2 + V3 for H4; it became `test_claimed_side_per_hypothesis`), `test_rules.VoiceDefinitions`.
* **(b) The model-stratified recognizer row (03:08).** `adapter.apply_asr_rule` keeps, beside the primary list (English-only
  only, as before), the recordings of another stated model and of unknown model, each tagged with its model
  (`asr_stratum`); recordings whose sources disagree and hold-out recordings whose TABLE model differs stay out, because
  their model is in dispute. `adapter.model_stratified_view` gives the bundle of the one row
  `constants.ASR_STRATIFIED_ROW`, which `run.row_specs` adds for H1, H2, H4, H5, H6 and H9 whenever the rule is applied; its
  verdict is computed and guarded like every row. Every comparison stays within one model (`common.stratum`): H1, H4 and H6
  are within-recording contrasts; H2 crosses the length band with the model; H5 pairs a creator's channelled and own-voice
  recordings only within one model, and since 06:44 (9) each model is a stratum of its own (creator by model), so that no
  side contrast mixes models; H9 builds cells within one model and pairs each hold-out cell only with seen cells of its
  model (a mask on `h9_family.Pairs`). The seen-derived constants (yardstick, length bands, retained parts) stay
  English-only. `counts.json` holds, per group, `in_model_stratified_row` and `model_stratified_row_by_model`, and
  `asr_model_rule.model_stratified_row` the totals, before any outcome; `e2e` checks them against its plant
  (`model_stratified_row.counts_match_the_plant`). Test: `ModelStratifiedRow`.
* **(c) H5's HKSJ random-effects sensitivity row (A10.7 point 2).** `h5_world_claims.random_effects_row`: the registered
  half-count estimator (10 hits per group and side) pooled by HKSJ with t(k-1), with its prediction interval and the A10.1
  sign-flip; a secondary without a verdict. The registered version under the guard keeps DerSimonian-Laird with the normal
  interval. Test: `H5RandomEffectsRow`.
* **(d) Registered intervals.** hypotheses.md registers for H2, H5 and H6 a "creator-bootstrap interval", and catalogue rule
  R1, which every entry carries ("Resample creators, then recordings within a creator"), draws it creators then recordings
  (the frozen H3 entry reads it the same way; A10.7 = CAL-A14 calls it "R1's registered procedure"). Their registered versions now
  use `stats.bootstrap_two_stage`: H2 resamples each drawn creator's recordings (with their statements) and pools the drawn
  creators' D by DerSimonian-Laird; H5 resamples a creator's channelled recordings among its channelled ones and its
  own-voice talks among its own-voice talks; H6 resamples a creator's recordings with both voices. The intervals say so
  (`"bootstrap": "creators, then recordings (R1)"`). **H1:** hypotheses.md registers "random-effects meta-analysis, with a 95%
  interval and a 95% prediction interval" and no bootstrap, and no registry row before 2026-11-21 registers one for H1; R1
  says how to resample where a bootstrap is used, it does not add one. H1's registered version therefore stays as coded (the
  DerSimonian-Laird pool's intervals); R1's two-stage bootstrap stays H1's sensitivity row outside the guard, and the A10
  draft's guard table (`A10-draft.md`, H1 row) now says so. H4 likewise registers the pool and no bootstrap. Test:
  `TwoStageRegisteredIntervals`.
* **(e) H2's shared-wording flag** covers the scenario and withdrawal categories both codebooks name: SC1-SC4 and WD1-WD4;
  the former SC5 ("a possibility", a plain commitment hedge) left the list. Tests: `SharedWording` (its SC5 example became a
  negative case).
* **(f) The permission check before any file is opened.** `adapter.open_problem` runs before a folder is listed
  (`json_files`) and before a file is opened (`read_json`, `load_model_map`, the cross-check's TABLE file): after freeze 2
  everything may be opened; before it, only files in a folder holding the synthetic generator's marker
  (`adapter.SYNTHETIC_MARKER`, written by `simulate.mark_synthetic` and `simulate.write_files`), and never a path under
  `labels/holdout` or `labels/other`, marked or not. A label file in a marked folder that is then not marked `"synthetic":
  true` is refused as soon as it is parsed: only its markers are read first (`not_for_analysis` reads `synthetic`, `smoke`,
  `run_limit` and `frozen_utc`), no label field (the H2 flag rule never runs on it); per-recording model files and TABLE's
  CSV carry no synthetic mark, so only their folder's marker gates them (corrected 06:44: the text said "before any field"
  and overstated it). `load_bundle` computes the freeze-2 status once and passes it to every loader; the old record check
  after loading stays as a second layer. Before freeze 2 this also closes the direct loaders (`load_voice` and the others)
  on real seen labels; the seen-only path of 06:44 (1) is the one way to them. Tests: `PermissionBeforeOpening`,
  `test_label_files.Refusals`.
* **(g) "Not determinable" under the guard.** If either version is not determinable, the result is "not determinable"
  (kind "not determinable"), with the reason naming the version: "not determinable in the amended version: too few eligible
  creators (8 of 9) (registered version: ...)", "... in the registered version: ...", or "not determinable in both
  versions (amended: ...; registered: ...)"; where both versions give the same reason it is printed once. It is flagged
  uninformative and enters Holm at p = 1. "Not determined: the registered and the amended versions differ" stays for two
  determinable versions that disagree. Rows follow the same rule. Tests: `GuardNotDeterminable`,
  `test_rules.Boundary.test_h2_minimum_is_nine` (it read "versions differ" at 8 creators before; it now asserts the kind, the
  version named, p = 1 and the flag).
* **(h) No replication wave.** The hold-out is the only confirmation sample: `constants.CONFIRMATORY_GROUPS = ("holdout",)`
  and `common.confirmatory` leave every recording of another group out (a "wave" included); no code path pools one. If a wave
  is ever collected, a verdict must hold on the hold-out alone and on the pooled row (documented, not coded). Test:
  `NoSilentWave`.
* **(i) H7** is not run in the first round; when it is run, its verdict must hold against both margins (the placeholder 0.01
  and k x SD_L). Documented, not coded.
* **(j) The MH interval.** Until the coverage repeat (CAL part f) has run, the MH estimates of H5 and H6 carry the wider of the
  creator-bootstrap percentile interval and the t interval, elementwise (`constants.MH_INTERVAL_RULE = "wider"`, allowed
  values `MH_INTERVAL_RULES`; `stats.mh_interval`). The t interval of an MH estimate is a CHOICE: log MH +- t(k-1) x the
  delete-one-creator jackknife standard error (`stats.jackknife_t_interval`; for a plain mean it is the t interval on creator
  means). Freeze 2 may switch the constant to "bootstrap_percentile" or "t" once the coverage repeat has run. The interval
  (`intervals.mh_90_log_or` and `mh_95_log_or` for H5, `mh_90` and `mh_95` for H6, with both inputs beside them) decides H5's
  and H6's refutations, their `creator_interval_90` (the uninformative flag) and the battery's coverage column (with the
  bootstrap percentile alone beside it). Test: `MantelHaenszelInterval`.
* **(k) H6's registered half-count version stays uncentred;** its null mean on seen creators is reported in `report.json`
  under `meta.a10_7_null_means_on_seen_creators.H6` (`registered_half_count_null_mean`, `registered_flag`), as before.
  Test: `A10Checks.test_the_registered_h6_version_stays_uncentred_and_its_null_mean_is_reported`.
* **(l) A10 numbering:** A10.k = CAL-A(7+k) everywhere (A10.1 = CAL-A8 ... A10.7 = CAL-A14). Test: `A10Numbering`.
* **(m) H10** is not run in the first round (p = 1 in Holm); no code change.
* **Second reading (r): H2's FRAME row.** The checkability answer marks a time window taken only from the period of the
  talk with `where` = FRAME (`llm/prompts/forecasts_fc.txt` and `forecasts_fc.schema.json`; label-files.md `fc.where`; the
  adapter keeps `(value, where)` per part). The row `h2_hedging.FRAME_ROW` ("time window from the period of the talk (FRAME)
  counted as NO") scores such a time window as NO whatever its value. The primary already counts STATEMENT and CONTEXT only
  (R10), so for YES readings the row repeats the primary; it differs where a FRAME time window is CANNOT_TELL (the primary
  leaves the statement out as missing; the row counts the part as NO). The existing row "FRAME parts counted (R10)" is the
  one in which a FRAME time window counts as YES. Test: `H2FrameRow`.

## Decisions of 2026-11-21 06:44 (registry row "Hypothesis code, decisions on the second verification")

Each item as implemented; tests in `tests/test_decisions_0644.py`. Synthetic data only: no test opens the production label
tree (the tests that need one patch `adapter.PRODUCTION_LABELS` to a temporary tree and `adapter.FREEZE2` to a missing file).

* **(1) The seen-only path.** `adapter.load_seen_bundle(labels=None, instruments=...)` reads `labels/seen/<instrument>/` of
  the production label tree (`adapter.PRODUCTION_LABELS`, llm/labels; instruments voice, asks, features, forecasts,
  sentences, titles; CHOICE 13 for features). Three layers. (a) `seen_open_problem` runs before a folder is listed and
  before each file is opened: the path, links and junctions resolved, must lie inside `<labels>/seen`; a path under
  `labels/holdout` or `labels/other` (also through a link), a link that leads out of labels/seen, a labels/seen that is
  itself a link to another folder, any other path, and a root not named `labels` are refused. (b) `read_seen_json` reads the
  file's `group` first and refuses the file unless it is "seen", before any other field of it is read (the markers `smoke`,
  `run_limit` and `frozen_utc` come after; the pilot mapping layout, which names no group at its top, is refused). (c) Every
  parsed record is checked again (`require_seen_records`). Real records are read only under the frozen ASR-model rule, which
  is applied as in the analysis. A tree outside the production tree is read only where its folders hold the synthetic
  marker and its files are marked synthetic (tests, e2e). The ordinary loaders are unchanged and still refuse real seen
  labels before freeze 2. `run.py constants` (`run.seen_constants`) prints H4_YARDSTICK (the small model, the record on
  seen) with the middle-model version beside it, H2_LENGTH_BANDS, H2_PARTS_RETAINED with the prevalence table, the A10.7
  null means (`a10_checks.null_means`) and counts (files read per instrument, the rule's counts, creators, statements); no
  creator, recording or label value. It writes nothing into the code: the lead enters the printed constants in
  `constants.py` before freeze 2. CAL part (f) can call `adapter.load_seen_bundle` the same way. `e2e` writes its synthetic
  seen cohort as a labels/seen tree and checks that the path gives the in-memory constants
  (`seen_only_path.constants_match_in_memory` in `e2e-summary.json`). Tests: `SeenOnlyPath` (a synthetic tree, the command,
  other paths, a junction or symlink into labels/holdout, the group read first with the marker reader and the parser
  mocked to fail, real seen files of a patched production tree read and nothing else, a real file outside it refused).
* **(2) One freeze-2 record.** `adapter.FREEZE2` is `llm/freeze2.json`; no record beside the modules is read any more.
  `freeze2_problem`: the six keys of 02:45 (`adapter.FREEZE2_KEYS`, the same as produce's `fc_common.FREEZE2_KEYS`; the test
  compares them where the private folder exists) present and not empty, `sha256` and `analysis_code_sha256` dicts,
  `constants_sha256` a sha256, `registry_commit` a commit hash, else "freeze2.json lacks <key> ..." (fails closed); then
  `analysis_code_sha256` ({path: sha256}, a relative path read under this folder, as produce reads it) lists every module and
  every listed file still has its hash; `constants_sha256` is the hash of `constants.py`; the FREEZE2 constants are set. The
  other keys (the llm file hashes, freeze 1, the registry commit through git) are checked by `produce.freeze2_problem`,
  which gates every hold-out label (CHOICE 14). `run.py hashes` prints `{"analysis_code_sha256": ..., "constants_sha256":
  ...}` (`adapter.freeze2_entry`), the two keys the record takes from this code. Tests: `Freeze2Record`.
* **(3) H6 centred per recording (amended version).** OE = (a - sum_i T_i s_i) / T over the creator's eligible recordings i
  (T_i = a_i + b_i, s_i the claimed share of its words; `h6_asks.oe_value`); with one recording it is CAL-A11's a/T - s. Its
  mean is zero under no within-recording effect given the T_i, whatever the recordings' ask rates; CAL-A11's pooled a/T - s
  is not (the verifier's example, shares 0.9 and 0.1 and rates 1 and 5 per 1,000 words: about -0.27, in H6's direction).
  The MH rate ratio has one stratum per creator and recording (`h6_asks.mh_ratio`); its jackknife deletes a creator, its
  bootstrap draws creators with their recordings. The registered version is unchanged (uncentred, 04:55 (k)). A10.7:
  `a10_checks.h6_null` places asks on the claimed side with probability s_i given T_i in every recording: the amended OE's
  null mean is exactly zero; CAL-A11's pooled OE is reported beside it (`pooled_OE_before_0644_null_mean`); the registered
  half-count expectation now uses the convolution of the recordings' binomials (before: one binomial at the pooled share),
  so its number moves a little. Battery: H6's null scenario `null_heterogeneous` (ask rates that differ between a creator's
  recordings with their claimed shares, no difference inside any recording; `simulate.H6_HETEROGENEITY`), with the pooled
  OE's rejection rates beside (`reject_*_pooled_oe_before_0644`). Tests: `H6CentredPerRecording`.
* **(4) H9's creator bootstrap, creators then recordings, in both versions** (A10 replaces no H9 interval, so the
  registered version carries the same interval). Per draw: hold-out and seen creators drawn with replacement, apart; in every
  cell of a drawn creator its recordings drawn with replacement, as many as the cell has; every drawn cell pooled and
  re-rarefied to 2,000 tokens without replacement; TF-IDF (idf over the draw's cells), the z-scored function-word profiles
  (centre and spread over the draw's cells), the similarities and both contrasts computed again; same-model pairs only in
  the model-stratified row (CHOICE 15). `h9_family._Encoder`, `_sample_indices`, `_draw_vectors`, `_content_similarities`
  and `_contrast` reproduce `vectorize`, `_cosine` and `Pairs.contrast` (the test compares the similarities to 1e-9). A
  draw costs about 60 ms at 17 hold-out and 40 seen creators, so the battery gives H9's bootstrap
  `simulate.H9_BATTERY_BOOTSTRAP_DRAWS` = 99 draws (registry 06:44 (4) allows fewer for H9; H9's light runs had 199 before,
  and the light runs of H2, H5 and H6 use 499; the comment beside the constant in simulate.py, which said "the 199 of the
  other light runs", was corrected with the revision of 09:19, which changed the task fingerprint anyway);
  the analysis keeps `constants.BOOTSTRAP_DRAWS` = 9,999 and `e2e` 999. Tests: `H9TwoStage`.
* **(5) A5 for H5 and H6** holds only if both the t interval on the creator OE values and the MH interval (the wider of
  04:55 (j)) exclude zero on the predicted side: `conditions.a5`, with `conditions.a5_parts` naming each. The registered
  versions keep their registered intervals. Tests: `A5OnBothIntervals` (an MH interval made wide by a mock blocks A5 where
  the t interval alone would pass).
* **(9) Creator-by-model strata for H5** in the model-stratified row: `creator_tables` keeps one stratum per model in which
  the creator has both sides (`strata`: W and P per side and the per-recording points); OE is centred within each stratum,
  (W_A - sum_m T_A,m W_m / T_m) / T_A; the MH odds ratio has one stratum per creator and model; the registered half-count
  value is the inverse-variance weighted mean of the strata's values (CHOICE 16); the two-stage bootstrap resamples within
  side and stratum; the 2-recordings rule and the hit rules read the creator's totals over its strata. Outside that row a
  creator has one stratum and every value and draw is the one of before. Tests: `H5CreatorByModelStrata`.
* **(6), (7), (8), (10), (11)** need no code change: (6) H6's smallest effect for "uninformative" stays log 2
  (`constants.UNINFORMATIVE_SESOI`); (7) the M9 revisions stay outside the guard, the rows without them keep their own
  verdicts; (8) H2's FRAME row stays as built; (10) the paper cites commit times; (11) a new full battery is to run on this
  code (not started by this revision; runtime in "Simulation battery").
* **Text fixes:** the adapter's docstring and item (f) above no longer say that a real file is refused "before any field"
  is read (its markers are read first); `simulate.py`'s comment on H4's plant names V2 as the registered primary.

## Decisions of 2026-11-21 09:19 (registry row "Hypothesis code, decisions after the third verification")

Items (1) to (4) as implemented; tests in `tests/test_decisions_0919.py`. Constructed numbers and synthetic records only.
Items (5) (the code committed to the analysis branch before freeze 2) and (6) (H5's stratified-row choice stays, stated as
a limit) need no change to the code.

* **(1) H6's conditional Monte Carlo reference.** *Superseded by 11:08 (1) and 12:52 (1) (sections below): the amended p is
  now the larger of the cluster-level conditional p and the sign-flip p of OE, with 99,999 draws in the analysis and
  `p_method` "max(conditional_monte_carlo_clusters_99999, signflip_oe_exact)"; the ask-level reference described here is
  computed beside it (`p_parts.ask_level_conditional_0919`) and enters nothing. The text below describes the code of
  09:19.* The amended version's p (`h6_asks.conditional_p`): the statistic is the
  mean over the creators with T >= 1 of OE = (a - sum_i T_i s_i) / T (each creator once, as the sign-flip aggregated it),
  with s_i = wc_i / (wc_i + wo_i); the reference draws every recording's asks again, a_i ~ Binomial(T_i, s_i) given its
  T_i, independently between recordings (the distribution of the asks when they fall on a recording's words at one rate
  in both voices, whatever the recordings' rates); p = (b + 1) / (m + 1), b the draws at or below the observed value
  ("less"), m = `h6_asks.REFERENCE_DRAWS` = 9,999, from a stream seeded by the label (`stats.rng`). The statistic is
  compared as an exact whole number (`_integer_statistic`: with L the least common multiple of the creators' T, the sum
  of L / T x a; the centring term is fixed under the reference), so ties are exact. Exact under that null at every level
  alpha with alpha (m + 1) whole (0.005 x 10,000 = 50 and 0.05 x 10,000 = 500): P(p <= alpha) <= alpha. A recording with
  T_i = 0 (a recording without an ask file too) adds nothing. The registered version is unchanged (creator mean of
  half-count log ratios, T = 0 included, sign-flip, R1 bootstrap). The battery uses `simulate.H6_BATTERY_REFERENCE_DRAWS`
  = 9,999, the analysis's count (about 0.03 s a repetition at 17 creators). `p_method` reads
  "conditional_monte_carlo_9999".
  **Level on constructed numbers** (exact enumeration under the per-recording null, `simulate.h6_reference_levels`; one
  recording per creator unless named; rejection rates at 0.005 and at 0.05):

  | case | sign-flip of OE | conditional reference, 9,999 draws | exact conditional test |
  |---|---|---|---|
  | 17 creators, T = 1, s = 0.2 | 2.25%, 11.82% | 0.00%, 2.25% | 0.00%, 2.25% |
  | 17 creators, T = 1, s = 0.3 | 1.93%, 7.74% | 0.23%, 1.93% | 0.23%, 1.93% |
  | 17 creators, T = 1, s = 0.4 | 1.23%, 4.64% | 0.21%, 4.48% | 0.21%, 4.64% |
  | 17 creators, T = 1, s = 0.5 | 0.12%, 2.45% | 0.14%, 2.45% | 0.12%, 2.45% |
  | 17 creators, T = 2, s = 0.2 | 2.21%, 6.57% | 0.30%, 2.26% | 0.48%, 2.26% |
  | 17 creators, T = 2, s = 0.3 | 0.99%, 6.00% | 0.32%, 3.34% | 0.32%, 3.34% |
  | 17 creators, T = 2, s = 0.4 | 0.33%, 4.31% | 0.35%, 3.41% | 0.48%, 3.41% |
  | 17 creators, T = 2, s = 0.5 | 0.15%, 2.09% | 0.37%, 2.88% | 0.45%, 2.88% |
  | 17 creators, T = 3, s = 0.2 | 1.29%, 6.71% | 0.33%, 4.21% | 0.48%, 4.21% |
  | 17 creators, T = 3, s = 0.3 | 1.04%, 7.67% | 0.24%, 3.36% | 0.20%, 3.36% |
  | 17 creators, T = 3, s = 0.4 | 0.54%, 5.25% | 0.39%, 4.35% | 0.43%, 4.36% |
  | 17 creators, T = 3, s = 0.5 | 0.33%, 3.51% | 0.31%, 4.53% | 0.23%, 4.60% |
  | 17 creators, T cycled 1, 2, 3, s = 0.2 | 3.30%, 10.07% | 0.40%, 3.77% | 0.49%, 3.68% |
  | 17 creators, T cycled 1, 2, 3, s = 0.3 | 1.52%, 7.42% | 0.41%, 4.17% | 0.44%, 3.94% |
  | 17 creators, T cycled 1, 2, 3, s = 0.4 | 0.80%, 6.00% | 0.42%, 4.28% | 0.35%, 4.17% |
  | 17 creators, T cycled 1, 2, 3, s = 0.5 | 0.33%, 3.93% | 0.43%, 4.58% | 0.39%, 4.62% |
  | 17 creators, T = 1, s cycled 0.2 to 0.5 | 0.68%, 6.03% | 0.07%, 3.42% | 0.06%, 3.42% |
  | 17 creators, two recordings (T_i = 1 at s = 0.2, T_i = 2 at s = 0.4) | 0.26%, 2.88% | 0.34%, 4.42% | 0.34%, 4.43% |
  | 12 creators, T = 1, s = 0.3 | 1.38%, 8.50% | 0.00%, 1.38% | 0.00%, 1.38% |

  The sign-flip of OE exceeds 0.005 in 13 of the 19 cases (up to 3.30%) and 0.05 in 12 (up to 11.82%); the conditional
  reference stays at or below both levels in every case (at most 0.43% and 4.58%). The first row of the sign-flip
  reproduces both verifiers' 1.93% (and 0.99% at T = 2, 1.38% at 12 creators). The Monte Carlo column is exact for the
  test as coded: given the observed value S, b ~ Binomial(m, F(S)) with F the null distribution function of S, and the
  test rejects when b <= 49 (0.005) or b <= 499 (0.05) (`simulate.largest_count_rejected`). A run of the package's own
  `conditional_p` and `stats.signflip_p` on 20,000 simulated constructed null sets per case agrees with these figures
  (section "Battery and checks of 09:19" below).
  **Battery:** a third H6 null scenario, `null_sparse_low_share` (`simulate.SCENARIO_CFG`): in every recording with both
  voices the claimed voice covers 25% to 45% of the units (`H6_SPARSE_CLAIMED_FRACTION`; claimed shares of the words in
  the two voices about 0.24 to 0.47 after label error, median about 0.35), and each creator has 1 to 3 pay-or-enrol asks in
  all (`H6_SPARSE_ASKS_PER_CREATOR`), each on a unit of its recordings with both voices drawn in proportion to the unit's
  words (`sparse_asks_records`), at 12 and 17 creators with the null sizes (2,000 sets; 30 in the quick battery). Every
  H6 row also carries the sign-flip of OE on the same set (`p_signflip_oe_before_0919`, columns
  `reject_*_signflip_oe_before_0919`) beside CAL-A11's pooled OE. The generator's other scenarios draw exactly as before
  (the synthetic files of eight scenarios at three seeds each and of the e2e cohort are byte-identical to those of the
  code before this revision). Tests: `H6ConditionalReference`, `SparseLowShareScenario`.
* **(2) The A10.7 tolerance of the OE versions** (`a10_checks.h6_oe_smallest_effect`, `h5_oe_smallest_effect`): a tenth of
  the smallest effect expressed on the OE scale at the seen creators' counts and shares, in place of 0.1 on the share
  scale. H6: delta_OE = mean over the creators with T >= 1 of sum_i T_i (q_i - s_i) / T, q_i = rho s_i / (rho s_i + 1 - s_i),
  rho = 0.5 (the expected OE given the T_i when the claimed voice asks at half the own voice's rate per word; the same as
  the planted check's `amended_OE_mean_at_plant`; the pooled OE moves by the same amount, so it serves both OE forms); at
  s = 0.5 it is -1/6, at s = 0.3 about -0.12. H5: delta_OE = mean over the creators that pass the margin rule of
  T_B / (T_A + T_B) x (p_A - p_B) with logit p_A - logit p_B = 0.4 and T_A p_A + T_B p_B = W_A + W_B (the side shares that
  differ by the smallest log odds ratio and give the creator's observed world-claim hits; E[OE | T_A, T_B] at those
  shares, checked by exact enumeration in the test); at even sides and a pooled share of one half it is 0.0498. The flag
  is "recentring needed" when |null mean| > 0.1 x |delta_OE|; `null_means` reports `OE_smallest_effect`, `OE_tolerance`,
  the formula and, for H5, the creators it averages. The registered versions keep 0.1 x their log-scale SESOI. Tests:
  `OEScaleTolerance`.
* **(3) The null check keeps recordings without an ask file** with a = b = 0, as `h6_asks.creator_tables` and the analysis
  keep them (CHOICE 17): `a10_checks.h6_null` reads every recording with both voices; a creator without any ask file
  counts in the registered half-count mean with T = 0 (its words in the word totals) and adds nothing to OE;
  `recordings_without_ask_file` is reported. Test: `H6NullKeepsRecordingsWithoutAskFile`.
* **(4) No file of the package opens the production label tree's hold-out or other folders.** The verifier's test file
  `verify/test_verify_hypcode.py` (it globbed `llm/labels/holdout` and `llm/labels/other` and read every
  `labels-smoke/seen` file; it was never part of `run.py selftest`) moved out of the package with its folder, unchanged
  (sha256 04e3c5df...0370a6), to the session scratchpad (`moved-from-hypotheses\verify\`). No other file of the package
  opened that tree: the adapter refuses any path under labels/holdout or labels/other before freeze 2 (its loaders open
  hold-out labels only after freeze 2, from the folders an analysis config names), the seen-only path opens labels/seen
  only, `features.py` writes the seen feature files, and the tests build temporary trees. `NothingOpensTheHoldOutOrOtherTree`
  scans every .py file of the package: no join of the production root (`LLM`, `PRODUCTION_LABELS`) with "labels",
  "holdout" or "other" outside the adapter, no path into the private folder outside `adapter.py` and `features.py`, no
  glob of the production tree, and no verifier file. Freeze 2's code hashes cover the top-level modules only, so the move
  changes no hash.

## Decisions of 2026-11-21 11:08 (registry row "Hypothesis code, decisions after the fourth verification")

Item (1) in `h6_asks.py`, `a10_checks.py`, `simulate.py`, `verdicts.py` and `run.py`; tests in
`tests/test_decisions_1108.py`. Items (2) and (3) in `features.py` (features-3; tests in `tests/test_features_h9.py`).
Item (4) needs no change to the code. Constructed numbers and synthetic records only. The row also corrects the 09:19 row:
the ask-level conditional reference does not "only make a verdict harder to reach"; on some data its p is below the
sign-flip's. The cluster rule of (1) was widened at 12:52 (1) (next section); this section gives the rule of 11:08 where it
differs.

* **(1) H6's amended p, the larger of two** (`h6_asks.amended_p`):
  * the cluster-level conditional Monte Carlo p (`conditional_p(..., by="cluster")`). The units of the draw are the clusters
    of a recording's asks (`clusters_of`; at 11:08 asks in the same checked unit range, in overlapping ranges or in
    adjacent units, a window of 1 unit). Under the null each cluster is in the claimed voice with the recording's claimed
    share s_i, all its asks with it, independently between clusters, given the clusters. Each draw takes every creator's a
    from its exact null law (`creator_pmf`, the convolution of the clusters' two-point laws {0: 1 - s_i, k: s_i}, read
    through the inverse of its distribution function, one uniform a creator). The statistic is the whole number of
    `_integer_statistic` (ties exact); p = (b + 1) / (m + 1), b the draws at or below the observed value;
  * the creator sign-flip p of OE (`signflip_oe_p`: `stats.signflip_p`, exact up to 20 creators), the reference of 06:44
    (3) to 09:19.

  Neither carries a verdict alone: the sign-flip over-rejects where asks are few and claimed shares lie below one half,
  and a reference that draws asks one by one over-rejects bursts of asks in one voice. The ask-level conditional p of
  09:19 (1) is computed beside them and enters nothing. Streams: the label plus "clusters", "signflip-oe" and
  "conditional". `p_parts` holds the three p values with their methods, `enters_holm` ("max(cluster_conditional,
  signflip_oe); ask_level_conditional_0919 shown only") and the cluster counts (`clusters`,
  `asks_in_clusters_of_2_or_more`, `largest_cluster`); `p_method` reads "max(conditional_monte_carlo_clusters_99999,
  signflip_oe_exact)" at 20 creators or fewer.
  * *Draws.* `h6_asks.REFERENCE_DRAWS` = 99,999 in the analysis (9,999 at 09:19), so 0.005 x (m + 1) = 500 and
    0.05 x (m + 1) = 5,000 are whole numbers and the test's level is exact at both; the Monte Carlo SE of a p near 0.005 is
    about 0.00022 (0.0007 with 9,999). The p is reproducible (seeded by its label); inside about 0.0045 to 0.0055 the side
    of 0.005 still depends on the draws (registry 12:52, correcting the 11:08 row's "does not depend on the seed"). The
    battery keeps `simulate.H6_BATTERY_REFERENCE_DRAWS` = 9,999 (CHOICE 23).
  * *Which asks form clusters:* CHOICE 21.
  * *A10.7* (`a10_checks.h6_null`): the null places each cluster of a recording's asks in the claimed voice with
    probability s_i, all its asks with it. The amended OE's null mean stays exactly zero (its expectation does not depend
    on the clusters); the registered half-count mean is taken over the clusters' law, with the 09:19 mean (asks one by one)
    beside it (`registered_half_count_null_mean_asks_one_by_one_0919`) and the cluster counts.
  * *Battery.* The H6 null scenario `null_burst` (CHOICE 24). Every H6 row carries, beside the amended p, its two halves
    and the references it replaced (`simulate.H6_COMPARISON_PS`: the cluster p alone, the sign-flip of OE alone, the
    ask-level p of 09:19, the sign-flip of CAL-A11's pooled OE), and `run.simulation_markdown` prints them in the table
    "H6: the amended p, its two halves and the references it replaced".
  * *Levels on constructed numbers.* `simulate.h6_cluster_levels` gives, by exact enumeration under the cluster null, the
    rejection rates at 0.005 and 0.05 of the cluster p (with the stated draws, from the binomial law of the draws), the
    exact cluster test, the ask-level p, the sign-flip p and the amended p; `h6_cluster_reference_levels` tabulates the
    cases of `h6_cluster_level_cases` (section "Battery and checks of 11:08 and 12:52").
  * *Detectable effect* (A10.2): H6's note comes from the battery's power (`verdicts.h6_detectable_from_battery`, CHOICE
    26), not from `stats.detectable_effect`, which assumes the sign-flip of normal creator values; `run.analyse` writes it
    into counts.json without a creator SD. With no full battery of the current task fingerprint on file it states none.
* **(2) H9's names input** (`features.h9_mask_forms`): the NAMES v2 list forms and every token of every variant of the
  frozen family table (freeze 1), apostrophes removed (CHOICE 9).
* **(3) Contractions whose parts are function words** (it's, we're, don't) count as those function words
  (`features.h9_parts`, `h9_counts`; FEATURE_VERSION features-3; CHOICE 9).
* **(4)** needs no change to the code: the flat-list mask (every NAMES v2 form masked in every recording, the form of the
  released mask) stays, stated in CHOICE 9; the 9 seen transcripts without a stated model enter the model-stratified row
  as unknown model (CHOICE 12).
* The seen feature files were written again as features-3 (11:20:46 to 11:22:20 UTC, 1,293 files; private features note)
  before the FREEZE2 constants were computed; 12:52 (3) replaced them with features-4.

## Decisions of 2026-11-21 12:52 (registry row "Hypothesis code, decisions after the fifth verification")

Items (1), (2) and (4) in `h6_asks.py`, `adapter.py`, `a10_checks.py`, `simulate.py` and `run.py` (its battery markdown);
tests in `tests/test_decisions_1252.py` (22 tests). Item (3) in `features.py` (features-4; `tests/test_features_h9.py`).
Item (5) needs no change; item (6) is the section "FREEZE2 constants". Constructed numbers and synthetic records only. The
row also corrects the 11:08 row: with 99,999 draws the p is reproducible (seeded by its label), but inside about 0.0045 to
0.0055 the side of 0.005 still depends on the draws.

* **(1) The cluster window.** `h6_asks.H6_CLUSTER_WINDOW` = 5: taken in the order of their units, an ask joins the cluster
  before it when its first unit is at most 5 after the cluster's last unit, so clusters chain (`clusters_of(spans,
  window)`). Units are sentences of 8 to 40 words (prep.UNIT_MIN, UNIT_MAX), so 5 units are about one minute of speech;
  asks of one pitch lie a sentence or two apart. 11:08's rule is the window of 1.
  * *Sensitivity row.* `H6_SENSITIVITY_WINDOW` = 10: the secondary "cluster window of 10 units (sensitivity row, registry
    2026-11-21 12:52 (1))" (`h6_asks.window_p`), the larger of the cluster-level conditional p at 10 units and the same
    sign-flip p of OE (which does not depend on the clusters), over the same creators with T >= 1; no verdict.
  * *The stated limit.* Every H6 result carries `h6_asks.CLUSTER_STATEMENT` in `notes` ("Dependence of asks beyond the
    window (asks of one pitch more than 5 units apart) is not modelled; a 10-unit window is a sensitivity row") and
    `cluster_rule` (the two windows, the rule, `"dependence_beyond_the_window": "not modelled"`); report.json keeps the
    statement under the amended version's `notes`, and report.md prints the sensitivity row with its note, which says the
    same for 10 units. The eligibility record, and so counts.json, carries `cluster_window_units`.
  * *Battery.* The H6 null scenario `null_gapped` (CHOICE 25). Every H6 row also carries the amended p with 11:08's
    clusters (window 1) and with the 10-unit window (`p_amended_window_1_1108`, `p_amended_window_10`), printed as two
    more columns.
  * *Levels.* `simulate.h6_gapped_level_cases` adds bursts whose consecutive asks lie 1 to 3 units apart at claimed shares
    below one half, under the window of 5 and of 1, and bursts whose asks lie more than 5 units apart, under 5 and 10: the
    data come from the true cluster (one burst in one voice), the tests read the clusters the rule sees
    (`h6_gapped_recording`).
* **(2) Asks of one class whose unit ranges overlap count once** (`adapter.merge_overlapping_asks`, called by
  `parse_asks`; the instrument is frozen and unchanged). The find is the union of two draws, which can return one ask
  with different unit ranges (10..10 and 10..11). The rules are CHOICE 22. Every quantity reads the merged asks: T, a and
  b of both H6 versions, the amended version's MH strata and clusters, and the A10.7 null. Counts, no ids: each asks record carries
  `ask_overlaps`, `adapter.ask_overlap_counts` sums them per group, H6's eligibility record holds them as
  `ask_overlaps_counted_once` (taken before the confirmatory restriction, so counts.json shows the seen recordings too)
  and `a10_checks.h6_null` reports them.
* **(3) ain't and y'all** split into function words (features-4, CHOICE 9).
* **(4) One feature version per bundle.** `adapter.bundle` calls `require_one_feature_version`: a bundle whose feature
  files carry more than one `feature_version` (a file that states none counts as a version of its own) is refused, naming
  the versions with their file counts. `load_bundle` and the seen-only `load_seen_bundle` both build their bundle through
  it. The rule asks for one version, not a named one, so the hold-out feature files must be features-4 to be read beside
  the seen ones.
* **(5)** needs no change: the wide mask of 11:08 (2) stays (every token of every family variant, masked in every
  recording; 107,540 of the 1,816,569 features-2 content tokens of the seen files, 5.92%, lay on variant tokens, private
  features note), which can only lower same-family content similarity.
* **(6)** The FREEZE2 constants: section "FREEZE2 constants".

## A10 and its guard (registry 03:08)

For every hypothesis the module computes the amended version (the primary result) and, in `registered_version`, the version
as registered before A10 wherever A10 replaces an estimator, reference, minimum, interval or centring:

| | Registered version | Amended version | A10 items |
|---|---|---|---|
| H1 | DerSimonian-Laird pool, normal 95% and 90% intervals, DL prediction interval; exact sign-flip; minimum 12 (hypotheses.md registers the pool's intervals and no bootstrap: R1's two-stage bootstrap is a sensitivity row outside the guard, registry 04:55 (d)) | HKSJ with t(k-1); same sign-flip and minimum | A10.7 |
| H2 | within-creator-and-band permutation of commitment (9,999 draws), two-sided; creator-bootstrap 90% interval of the DL-pooled D, creators then recordings (R1); minimum 8 | two-sided creator sign-flip; HKSJ; minimum 9 | A10.1, A10.3, A10.7 |
| H4 | DerSimonian-Laird pool and intervals; same sign-flip; minimum 12; embodied voice (V2) in both versions | HKSJ | A10.7 |
| H5 | half-count difference of log ratios, 10 hits per group and side, DL pool, sign-flip with 9,999 Monte Carlo draws, creator-bootstrap interval of the pooled estimate, creators then recordings within each side (R1) | OE sign-flip (exact up to 20), MH odds ratio with the wider of the bootstrap percentile and the jackknife t interval, margin-only minimum, A5 on both the t interval on OE and that MH interval (06:44 (5)); HKSJ random-effects sensitivity row (no verdict); creator-by-model strata in the model-stratified row, both versions (06:44 (9)) | A10.1, A10.4, A10.7 |
| H6 | creator mean of half-count log rate ratios over every creator with both voices (T = 0 included, uncentred), sign-flip, creator-bootstrap interval of the mean, creators then recordings (R1); asks of one class on overlapping unit ranges counted once, as in the amended version (12:52 (2)) | OE = (a - sum_i T_i s_i)/T, centred per recording (06:44 (3)); the p of the mean OE over T >= 1 is the larger of its cluster-level conditional Monte Carlo p (asks within 5 units of each other chain into one cluster, each cluster in the claimed voice with the recording's claimed share s_i, 99,999 draws; 11:08 (1), 12:52 (1)) and the sign-flip p of OE; a 10-unit window as a sensitivity row; dependence beyond the window stated as not modelled; MH rate ratio with creator-by-recording strata and the wider of the bootstrap percentile and the jackknife t interval, 8 creators with T >= 1, A5 on both the t interval on OE and that MH interval (06:44 (5)) | A10.4, A10.7 |
| H9 | no creator minimum (only a reference that can reach 0.005); the creator bootstrap of both versions draws creators, then recordings, and re-rarefies the cells in every draw (R1; 06:44 (4); not an A10 item) | also 8 hold-out creators with a cell | A10.2 |

The larger of the two p values enters Holm (a version that is not usable counts as p = 1); for H6 the amended p is itself
the larger of the cluster-level conditional p and the sign-flip p of OE (11:08 (1)), so H6's guarded p is the largest of
three. Both versions are judged on that
Holm step; a verdict stands only if both give it. If either version is not determinable, the result is "not determinable"
with the version named (registry 04:55 (g)); two determinable versions that disagree give "not determined: the registered
and the amended versions differ (registered: ...; amended: ...)". `report.json` holds both versions per hypothesis under `versions` (p, the p that enters the
guard, estimate, intervals, the 90% creator interval, conditions, eligible creators and minimum, verdict, uninformative) and
`a10_guard` (what A10 replaces, the rule, whether the verdicts agree); report.md prints them as a table. Rows (the
multiverse) are guarded the same way. A10.1 (m = 10, H3, H7, H8, H10 at p = 1), A10.2 (minimums 8 one-sided and 9 two-sided
beside the registry's 12), A10.5 (the kappa combined rule, through `gates`) and A10.6 (H7, unrun) need no second version
here. A10.7's null-mean check (`a10_checks.py`) reports, on the seen creators of the primary source, the null mean of each
version under its reference (H1, H4 and the sign-flips: zero by construction; H2's permutation reference mean; H5 under a
within-creator permutation of recording sides; H6 by the exact conditional expectation per recording given its clusters
and s_i (registry 06:44 (3); each cluster of asks in one voice, 11:08 (1), clusters at the 5-unit window of 12:52 (1),
asks of one class on overlapping unit ranges counted once, 12:52 (2)), with CAL-A11's pooled OE beside it and the planted
check at a rate ratio of 0.5; recordings
without an ask file kept with a = b = 0, as the analysis keeps them, 09:19 (3)) and marks a version "recentring needed"
when it is off zero by more than 10% of its smallest effect on its own scale (registry 09:19 (2)): the log-scale SESOI for
the registered versions (0.04 for H5, 0.069 for H6); for the OE versions of H5 and H6 the OE value of the smallest effect
at the seen creators' counts and shares, `OE_smallest_effect` (H6: the mean over creators with T >= 1 of
sum_i T_i (q_i - s_i) / T with q_i = 0.5 s_i / (0.5 s_i + 1 - s_i); H5: the mean over creators passing the margin rule of
T_B / (T_A + T_B) x (p_A - p_B) with logit p_A - logit p_B = 0.4 and T_A p_A + T_B p_B = W_A + W_B, which is
E[OE | T_A, T_B] at those shares); the tolerance is `OE_tolerance` = 0.1 x |OE_smallest_effect| (about 0.005 for H5 and
0.017 for H6 at shares near one half, where 0.1 on the share scale stood before). Before freeze 2 the check runs on
seen labels through the seen-only path (`run.py constants`, 06:44 (1)); its run of 14:00 UTC is in the section "FREEZE2
constants". The registered versions stay uncentred under the
guard (registry 04:55 (k); the guarded verdict is never stronger than the amended version's alone, so a biased registered
version cannot create a verdict); on the e2e synthetic seen cohort the registered H6 half-count estimator showed a null mean
of about -0.087 (in H6's direction) under the pooled binomial, as CAL reported (-0.073 to -0.088), and is marked
"recentring needed" in `meta.a10_7_null_means_on_seen_creators`; with the per-recording expectation of 06:44 (3) the same
cohort gives -0.104 (still "recentring needed"), the amended OE exactly 0 ("centred") and CAL-A11's pooled OE -0.006
(e2e of 2026-11-21 07:33 to 07:52 UTC); under the cluster null of 11:08 (1) and 12:52 (1) the registered mean is -0.1032
(-0.1035 with the asks one by one; 80 clusters, 6 asks in clusters of 2 or more), the OE means unchanged (e2e of about
13:14 to 13:32 UTC).

## The hypotheses as implemented

| | Unit and eligibility (labels only) | Holm p | Estimate and intervals | Supported (besides Holm and A5) | Refuted |
|---|---|---|---|---|---|
| H1 | hold-out creator with a recording holding a claimed and an own span of 300 words or more; claimant sole speaker or host; formats conversation and multi-presenter out; min 12 | sign-flip of creator mean log rate ratios, less | HKSJ pool, 95% and 90% intervals, 95% prediction interval | upper 95% bound of the ratio below 0.95 | 95% interval of the ratio inside 0.95 to 1.05 |
| H2 | hold-out creator with 30 or more verified, non-duplicate, unflagged statements coded on both dimensions (score over the retained parts); min 9 | sign-flip of creator D, two-sided | D of checkability between committed and uncommitted statements, within length bands, pooled; HKSJ | D below zero | 90% interval inside -0.10 to +0.10, or D above zero with the 90% interval above zero |
| H4 | hold-out creator with a recording holding embodied claimed voice (V2; registry 04:55 (a)) and own voice; at least 10 contractible forms per side and recording; min 12 | sign-flip of creator mean standardised drops, greater | HKSJ pool of (own share - claimed share) / yardstick | pooled drop at least 0.5 | 95% interval below 0.5, or prediction interval centred on zero (CHOICE) |
| H5 | hold-out creator with 2 or more recordings titled as channelled and 2 or more solo own-voice talks; units next to a self-naming cue left out; T_A, T_B >= 10; min 12 | sign-flip of OE, greater | MH log odds ratio with the wider of the creator-bootstrap percentile and the jackknife t interval (90% and 95%; 04:55 (j)); RBG interval | MH log OR above zero; A5 on both the t interval on OE and the MH interval (06:44 (5)) | that 90% interval inside -0.4 to +0.4, or negative with the interval below zero |
| H6 | hold-out creator with both voices (300 words or more each in a recording); min 12, and 8 with T >= 1 | mean OE = (a - sum_i T_i s_i)/T (per recording, 06:44 (3)), less: the larger of its cluster-level conditional Monte Carlo p (asks within 5 units chain into one cluster, each cluster's voice drawn with s_i; 11:08 (1), 12:52 (1)) and the sign-flip p of OE | MH rate ratio, creator-by-recording strata, with the wider of the creator-bootstrap percentile and the jackknife t interval (90% and 95%) | MH ratio at most 0.5; A5 on both the t interval on OE and the MH interval (06:44 (5)) | that 90% interval inside 0.67 to 1.5, or MH ratio above 1 |
| H9 | hold-out creator with a creator-by-family cell (P1, voiced by the creator, one specific family, title and opening agree, 2 recordings, 2,000 words), paired with seen cells; min 8 and a label permutation that can reach 0.005 | family labels of hold-out cells permuted among them, 9,999 draws, greater | content contrast minus function contrast, each divided by the SD of its different-family similarities; creator bootstrap (hold-out and seen apart), then recordings, cells re-rarefied in every draw (06:44 (4)) | difference above zero | bootstrap 90% interval at or below zero |

Secondary rows, estimates only: H1 embodied and relayed apart (relayed: below the reliability floor, no verdict), words and letters per minute, the articulation and pause parts,
the negative control (greeting to own-voice main part) and its difference from the claimed contrast, the two-stage bootstrap,
the leave-one-creator-out range. H2 the within-creator-and-band permutation, the creator-bootstrap interval, the
leave-one-out range, D per band, the four-step order, the R9 marker gaps. H4 relayed spans (below the reliability floor, no verdict), the merged claimed voice V2 + V3 (no verdict), the
tempo negative control, log(we/I) and hedge-rate shifts, the two-stage bootstrap. H5 the registered half-count row, the HKSJ random-effects sensitivity row (A10.7 point 2), the leave-one-out range and the three Q2 assignments side by side. H6 the
amended p with a 10-unit cluster window (registry 12:52 (1)), the
half-count row, the share of creators whose claimed voice voices an ask (Wilson 90%), the position-adjusted ratio (creator by
tenth), unchecked asks with the small model's verdict, the span-label confusion table. H9 the leave-one-out range and the
creators with two or more families.

Multiverse rows (plan 3.5), each with its own verdict computed with the same rules and the A10 guard (its guarded p replaces
the primary's in the Holm vector); a verdict is "robust to the labeller" only if every row gives it: the second model; the reworded prompt and each
altered input (as extra label sources in the config, `"sources": {"reworded prompt": {...}, "altered input: punctuation
removed": {...}}`); the recognizer-model-stratified row of every hypothesis (other and unknown models included, comparisons
within one model; 03:08, 04:55 (b)); rule A against rule B; strict against broad own voice; the claimant set; for H2 the flagged statements included, all five parts,
cannot-tell both ways, FRAME counted, a FRAME time window counted as NO (second reading, 04:55), the time-window part alone, middle tier final where it judged, the small model's checkability; for H5 Q2 merged with Q1
(sensitivity A), Q2 excluded, the sensitivity code groups B to D, the relaxed and the per-side minimums, the self-naming units
kept, the title models; for H9 without the opening rule, S8
not specific, within each tradition, the 100 most distinguishing words deleted, the title models.

Tipping-point tables (plan 3.5), plain arithmetic on the pooled raw tables: H1 and H4 attenuation (corrected estimate for a
total voice error a + b) and selection (how far mislabelled words would have to differ in the outcome, at error shares of 1%
to 20%, to move the estimate across the verdict boundary); H2 the missed-hedge rate in less checkable statements that would
remove the gap; H5 the share of false world-claim codes on the channelled side, or false practice codes on the own side, that
would bring the odds ratio to 1 or to exp(0.4); H6 the ratio of ask detection rates, or the excess of false asks per 1,000
claimed words, that would bring the ratio to 1 or 0.5; H9 the dilution by wrong family labels.

## ASR-model rule (lead's decision, before any label existed)

**Rule.** H1, H2, H4, H5, H6 and H9 use only recordings whose resolved recognizer (ASR) model is the run's English-only
model. A recording from any other model, with no stated model, or whose sources state different models is excluded and
counted per group. The rule is the same for seen, hold-out and other recordings, so H9's seen partners and the FREEZE2
constants computed on seen labels are covered too. Why: timing, pause, filler and contraction measures differ by recognizer.
TABLE (panel round 2, digest section 2.1, not independently verified) counts 1,284 seen transcripts from the English-only
model and 9 from the model the run uses elsewhere for language decisions; the run report records no model for those 9.

**Where the model comes from.** Every label file holds `info` (label-files.md), and `info.model_role` is the bundle's
provenance `compute.text_model_role` (`prep.load_words`). The run report's per-recording ledger reads the same field, and
TABLE's seen extract checks that this role is `english_only` exactly when the bundle loads the English-only model's hash. On
the seen bundles the role is `english_only` for 1,284 and empty for the 9, so those 9 resolve to "unknown" and are excluded.
The adapter reads the model at analysis time, from the same files for every group. Nobody has to open a hold-out file or row
now. Feature files written by `features.py` carry the same value as `asr_model`.

**Implementation.**
* `adapter.asr_model_of` gives every parsed record (voice, asks, forecasts, sentences, features) an `asr_model`: an explicit
  `asr_model_resolved` or `asr_model` if the file has one, else `info.model_role`. `""`, `none`, `not_recorded` and
  `unknown` state no model.
* `adapter.resolved_model` resolves a recording. If every source that states a model gives the same one, that is its model.
  If none states one, it is "unknown". If two differ, it is "conflict".
* `adapter.apply_asr_rule(bundle, required, models=None)` keeps the recordings resolved to `required` and writes the counts
  to `bundle["asr_rule"]`. These are counts only, with no ids. Per group they give recordings, kept, excluded,
  `excluded_other_model` (with `other_models` by name), `excluded_unknown_model` and `excluded_conflicting_sources`, plus
  the creators, the creators with an excluded recording and the creators with no recording left. Titles are read only
  through a kept recording.
* Config of `analyse`: `"asr_model_required"` defaults to `constants.ASR_MODEL_REQUIRED = "english_only"`.
  `"asr_models"` (optional) names a per-recording model file that the adapter reads after the guard. It can be TABLE's
  private `recordings.csv`, which has `video_id` and `asr_model_resolved` (its `multilingual_inferred` resolves the 9 by
  hash), or a JSON list of rows such as the run report's `per-recording.json`. The adapter keeps only an id column and the
  model column, and only for the recordings in the bundle. Every other column and row is dropped as the file is read.
  Every source of the multiverse is read under the same rule (`run_row`).
* `counts.json` holds the rule's counts under `asr_model_rule`, and those of every label source (the extra multiverse
  sources too) under `asr_model_rule_by_source`, written before any outcome (A10.2 = CAL-A9). `report.json` repeats them in `meta`.
* The hold-out cross-check against TABLE's resolved model (section "Revisions of 2026-11-21") runs inside the rule and adds
  `crosscheck` and `excluded_crosscheck_mismatch` to the hold-out group's counts.
* The model-stratified sensitivity row (registry 03:08 and 04:55 (b); section "Decisions of 2026-11-21 04:55"): the seen
  transcripts of the other model and every transcript of unknown model are excluded from the primary, as before, and go
  into one row per hypothesis, `constants.ASR_STRATIFIED_ROW`, with every comparison within one model. Its counts
  (`in_model_stratified_row`, `model_stratified_row_by_model` per group) are in `counts.json` before any outcome; `e2e`
  checks them against the plant (the other-model hold-out recording and the unknown-model seen recording are in the row; the
  conflicting recording and the cross-check mismatch are not).
* Refusals: `adapter.require_asr_rule` stops `load_bundle` from returning real records under any value other than the
  frozen one. A null value switches the rule off, and only synthetic data accepts that.
* Synthetic data: the generator writes `info.model_role = "english_only"`. `run.py e2e` plants one hold-out recording
  from another model, one hold-out recording whose voice and asks files disagree, and one seen recording with no model. It
  then checks that `counts.json` reports those three exclusions (`asr_model_rule.counts_match_the_plant` in
  `e2e-summary.json`). It also writes a synthetic TABLE file in which one English-only hold-out recording is listed under
  another model and one is missing (`holdout_crosscheck.counts_match_the_plant`), and an extra label source with one more
  conflicting recording (`counts_by_source.extra_source_exclusion_matches_the_plant`). In that cohort the plant lowers H5's eligible creators from 17 to 16. `tests/test_asr_rule.py` checks:
  * another model and an unknown model are excluded and counted per group;
  * the same recording is treated alike in every group;
  * an excluded recording leaves H1's eligible count;
  * sources that disagree are excluded;
  * the model file keeps only id and model for the bundle's rows, and the apostrophe repair works;
  * the JSON layouts are read;
  * `load_bundle` applies the rule from disk;
  * real records are refused without the frozen rule.

## Label files read (`adapter.py`)

The formats are those of `llm/design/label-files.md` (checked against it on 2026-11-20 at about 21:05 local; the document
itself was read, no label file of any creator was opened). Only `adapter.py` reads files, and only after the permission
check (`adapter.open_problem`, registry 04:55 (f)): before freeze 2 a folder is listed and a file opened only where the
synthetic generator's marker `SYNTHETIC-LABELS.json` sits in the same folder, never under `labels/holdout` or `labels/other`.
The one exception is the seen-only path of 06:44 (1) (`adapter.load_seen_bundle`): `labels/seen` of the production tree, the
group of every file read first (section "Decisions of 2026-11-21 06:44").
The config of `analyse` names one folder per instrument, `labels/<group>/<instrument>/`, or a list of them (hold-out and seen):

* voice (`voice/<audio>.json`, `produce.voice_record`): units with `small` and `middle` views (`label`, `label_b`, `detail`,
  `own_broad`, `cue` as `[cue type, cue unit]` for H5's self-naming exclusion); map fields; `label_of_record` (small on
  seen, middle elsewhere).
* asks (`asks/<audio>.json`, `produce.run_asks`): `class`, `first_unit`, `last_unit`, `final`, `final_class`, `final_from`,
  `final_small_fallback` per candidate; asks of one class whose unit ranges overlap are merged into one as the file is
  parsed (`merge_overlapping_asks`, registry 12:52 (2), CHOICE 22), with the counts in the record's `ask_overlaps`.
* forecasts (`forecasts/<audio>.json`): per statement `verified`, `duplicate`, `coded` (an uncoded statement is out),
  `statement_words`, `markers`, `statement_quote` (read only by H2's flag rule; only the pattern ids are kept), `fc` (record:
  the middle model, owner's decision), `fc_second` (the small model, read as the
  source "small" and run as the row "checkability: small"; `fc.where` per part, STATEMENT, CONTEXT, FRAME or NA, gives H2's
  FRAME rows), further `fc_<name>` / `fd_<name>` as rows, `fd` (commitment);
  weights 1 / `inclusion_p` (the pilot's `valve_p` or `candidate_p` when it is absent; a p of 0 is never divided by). A failed
  reading (`{"failed": ...}`) is missing. The middle model's routed reading of the critic is "never a label" there, so the R3
  row ("middle tier final where it judged") is built only if a statement carries a `middle_final` flag; in the production
  layout it does not, and the row is left out (H2 has 10 rows, the primary included, besides the model sources and the
  model-stratified row).
* sentence codes (`sentences/<audio>.json`; config key `sentences`, or the older `content`): `units` with `primary`,
  `secondary`, `group`, `weight`; a failed unit is left out and counted; `coded_whole` gives the weight mode (words, rescaled
  to k points, choice 8).
* titles (`titles/<creator file>.json`, one per creator; config key `titles` names the folder): each entry's `record` is the
  source "final" (the large model where it adjudicated and is valid, else the middle model), `primary` "middle", `second`
  "small", `large` "large". A failed reading is left out of its source; a title without a record is absent from "final". The
  large model reads only adjudicated titles, so it is not run as a row. A single pilot file `{"final" | "middle" | "small":
  {video id: reading}}` is still read.
* refused (label-files.md: never analyse them): a real file with `"smoke": true`, a non-null `run_limit`, or a null
  `frozen_utc`; `labels-smoke/` is never a source.

**Feature files** (this package's format; one JSON per recording, private): `{"audio", "creator", "group", "feature_version",
"asr_model", "units": [{"id", "start", "end", "words", "syllables", "letters", "pauses", "contracted", "full", "fp_sing", "fp_plur",
"hedges", "self_name"}], "h9": {"content": {token: n}, "function": {word: n}, "other": n, "opening_family_match": {family: bool}}}`. Unit ids
are those of `prep.build_units` on the filtered words, so they match the voice label files. One bundle reads feature files
of one `feature_version` only (registry 12:52 (4)); the seen files are features-4 (1,293 files, written 13:01:12 to
13:02:48 UTC; folder digest `79bf8844...`), and their units equal those of features-2 and features-3, so only H9's counts
changed between the versions.

## FREEZE2 constants (entered from seen labels, 2026-11-21, registry 12:52 (6))

The three constants are computed on seen recordings under the ASR-model rule:
`adapter.apply_asr_rule(seen_bundle, constants.ASR_MODEL_REQUIRED)` before `yardstick_from_seen`,
`length_bands_from_seen` and `parts_from_seen`, as `run.py e2e` does. `adapter.freeze2_problem` refuses real labels
while any of them is None. On real seen labels before freeze 2 the one way is the seen-only path (registry 06:44 (1)):
`C:\Users\mehta\et-channelers-tools\analysis-venv\Scripts\python.exe -I run.py constants [--out FILE]` reads
`llm/labels/seen/<instrument>/` only and prints the three constants, the values printed beside them and the A10.7 null
means, with counts.

**As entered.** `run.py constants` ran on the production seen tree on 2026-11-21 from 14:00:03 to 14:00:37 UTC (date -u),
exit 0, with the default 999 draws (CHOICE 13), after the code changes of 12:52 (1) to (4) and on the features-4 files. It
read 1,293 files each of voice, asks, features, forecasts and sentences and 71 title files; the ASR-model rule kept 1,284
of the 1,293 seen recordings (the 9 of unknown model out) of 71 creators. A second reader recomputed the three values
outside the package and got the same values bit for bit. The values were entered in `constants.py`, each with a comment
that names the command, the run time and the sha256 digests of the six label folders (sha256 of the sorted "sha256
filename" lines: voice `84026da0...`, asks `5da50547...`, features `79bf8844...`, forecasts `d103cfc7...`, sentences
`0ce26f44...`, titles `dfa0e894...`); `constants.py` changed from sha256 `ab9ffbd5...` to `c079dbf8...` and nothing else
in the file changed (`MH_INTERVAL_RULE` stays "wider").

| Constant | Entered | Printed beside it |
|---|---|---|
| `H4_YARDSTICK` | 0.14738201990446706 (52 seen creators with at least 40 own-voice forms; small model, the record on seen) | middle-model version 0.16182180258870596 (23 creators) |
| `H2_LENGTH_BANDS` | (12.0, 20.0) (tertile cut points over 9,005 verified, non-duplicate seen statements) | - |
| `H2_PARTS_RETAINED` | ("time_window", "named_actor", "observable_outcome") | weighted prevalence over the same 9,005 statements: time_window 0.1163, observable_outcome 0.1073, named_actor 0.0543 (retained); place 0.0429, quantity 0.0296 (below 5%) |

**A10.7 null means on seen creators (same run; counts and means only).** H2's registered permutation reference: mean
-0.0003 over 56 creators, "centred". H5 (22 creators): amended OE -0.0017 against a tolerance of 0.0037 (19 creators in
`OE_smallest_effect`), "centred"; registered -0.011 against 0.04, "centred". H6 (48 creators with both voices in 278
recordings, 30 with T >= 1, no recording without an ask file; 261 clusters, 143 asks in clusters of 2 or more): amended OE
exactly 0 against a tolerance of 0.0125, "centred"; CAL-A11's pooled OE -0.0060, "centred"; the registered half-count
-0.137 against 0.069, "recentring needed" (-0.141 with the asks one by one), which stays uncentred under the guard
(registry 04:55 (k)). The merge of 12:52 (2) on seen (the 1,284 ask files of the kept recordings): 493 files with a
merge; 5,878 asks as filed, 4,221 counted, 1,657 merged away in 1,112 groups (104 on one range, 1,008 on overlapping
ranges; 906 groups with two or more final asks), over all classes; 485 of the groups are of class K1, the pay-or-enrol
class that H6 counts.

**Tests after the entry.** `run.py selftest` runs 224 tests; with the constants entered, 4 fail (rerun 2026-11-21
14:12:43 to 14:14:31 UTC): `test_decisions_0644.Freeze2Record.test_changed_uncovered_and_constants` and
`test_one_record_satisfies_this_check`, `test_revisions.H2Revisions.test_freeze2_needs_the_parts` and
`test_parts_from_seen_keep_parts_at_five_percent`. Each asserts the state before the entry (a constant still None, or the
refusal "FREEZE2 constants are not set"); the same four pass with the three constants patched back to None (a scratchpad
script of the constants task, rerun at about 14:15 UTC). The tests are not changed here (open items).

* `H4_YARDSTICK`: `h4_contraction.yardstick_from_seen` on seen voice labels and feature files. Registry, lead's decision of
  2026-11-21 01:15 UTC (plan section 6, decision 5): from the small model's labels on all seen recordings (the record on
  seen, the function's default), with the middle-model version (`how=voice_sets.definition(model="middle")`, the seen
  recordings the middle model labelled) printed beside it.
* `H2_LENGTH_BANDS`: `h2_hedging.length_bands_from_seen` (tertiles of statement length over seen statements).
* `H2_PARTS_RETAINED`: `h2_hedging.parts_from_seen` (the parts with at least `H2_PART_PREVALENCE_MIN` = 5% prevalence on
  seen statements, registry 02:50); its prevalence table is printed beside it.
* H9's smallest effect 0.2 is a placeholder to check on seen cells (not entered); the detectable-effect SDs come from the
  label-based CAL repeat (part f), except H6's note, which comes from the battery (11:08 (1)).

## CHOICES for the owner to confirm before freeze 2

1. H1: own-voice spans exclude formats `conversation` and `multi_presenter` ("until speakers are separated").
2. H1: span time is last word end minus first word start of the run of units; inter-unit gaps inside a span count, the gap at
   a boundary does not; pauses for the articulation split are gaps of 0.25 s or more.
3. Syllables: vowel groups with a silent final e and a silent -ed removed (`features.syllables`); words and letters per minute
   are rows.
4. H1 and H4 variance of a creator mean: pooled within-creator variance of recording values divided by the number of recordings.
5. H1 negative control: own-voice recordings with a map opening of at least 100 words and a main part of at least 300.
6. H4: at least 10 contractible forms per side and recording; full forms counted as non-overlapping matches; refutation by a
   prediction interval centred on zero read as "the 95% interval holds zero and the prediction interval's half-width is at
   least 0.5".
7. H6: "both voices" means at least 300 words on each side of a recording; an ask belongs to the side with the majority of its
   words; unchecked asks are out of the primary.
8. H5: own-voice talks must be `solo` in the voice map where it exists; whole-coded recordings are rescaled to their k points.
9. H9: function-word profile as z-scored relative frequencies of the closed list in `features.FUNCTION_WORDS`, cosine; TF-IDF
   with smooth idf; rarefaction to 2,000 tokens; the permutation keeps the hold-out family sizes; seen cells are fixed.
   Token counts (FEATURE_VERSION features-4; registry 2026-11-21 11:08 (2) and (3), features-3, and 12:52 (3),
   features-4; `features.h9_parts`, `h9_counts`, `h9_mask_forms`). A token with apostrophes is cut into a host (before the
   first apostrophe) and clitics. A clitic "t" after a host ending in "n" is n't: the host loses that "n" (do, is, could
   ...; the stems "ca", "wo" and "ai" become can, will and is: can't, won't, ain't) and n't reads "not". ain't takes one
   fixed reading, "is not": prep.contractible_pairs reads it as am, are, is, have or has + not, all function words, and
   "is not" is prep.neutral's reading where no subject or participle decides (12:52 (3)). A host and first clitic of the
   table `JOINED` read as its two words: y'all = you + all, its full form in prep.contractible_pairs (12:52 (3)). The other
   clitics read 's "is", 're "are", 'm "am", 've "have", 'll "will", 'd "would" ('s may also stand for "has" or a
   possessive and 'd for "had"; all are function words, so the reading chooses only which function word is counted). If
   the host and every reading are on the list, the token counts as those function words in order ("it's" = it + is,
   "we're" = we + are, "don't" = do + not, "ain't" = is + not, "y'all" = you + all, "I'd've" = i + would + have), so a
   contraction counts as its full form, also in the 2,000-word cell rule and the rarefaction pool. Any other token is one
   form, the token without its apostrophes ("let's", "might've", "shan't", "y'know" and possessives such as "speaker's"
   stay one content form: "let", "might" and "shall" are not on the list, and "y" without "all" is not joined); that form
   is tested against the list, the mask and the three-letter rule, and it is the content key, so no function word is a
   content key. A content form is masked if it, or the part of the token before its first apostrophe, is in the names
   input or among the recording's capitalised-only words; the names input is the NAMES v2 list forms and every token of
   every variant of the frozen family table (freeze 1), apostrophes removed (`h9_mask_forms`; 1,217 forms in the seen
   run's input), since family-defining words counted as content raise same-family similarity mechanically. CHOICE
   (registry 11:08 (4), kept at 12:52 (5)): the mask is a flat list, applied to every token of every recording (the form
   of the released NAMES v2 mask), not only where a whole variant or name occurs; on the seen features-2 files 5.92% of
   content tokens lay on variant tokens, and the wide mask can only lower same-family content similarity. Function words
   are counted before the mask and the formula test. On the seen transcripts features-4 differs from features-3 in 19
   files (20 ain't tokens; no y'all), units unchanged (private features note).
10. H6 and H5 interval of the Mantel-Haenszel estimate (registry 04:55 (j)): the wider of the creator-bootstrap percentile
    and the t interval until the label-based coverage repeat fixes it (`constants.MH_INTERVAL_RULE`); the t interval of an MH
    estimate is read as its log +- t(k - 1) x the delete-one-creator jackknife standard error (CHOICE).
11. The registered creator bootstrap of H2, H5 and H6 under R1 (registry 04:55 (d)): H2's recordings carry their statements;
    H5's second stage draws within each side (channelled among channelled, own-voice among own-voice); a draw keeps the
    creators whose drawn recordings give a value (H2) and the per-side hit rule is not reapplied inside a draw (H5).
12. The model-stratified row: recordings whose sources state different models, and hold-out recordings whose TABLE model
    differs, stay out of it (their model is in dispute); H9 pairs a hold-out cell only with seen cells of its model.
    (Verifier, 2026-11-21: the code had kept a disputed recording whose labels state a model other than the English-only
    one; it now leaves it out as well. A recording whose labels state no model disputes nothing and stays in as unknown.)
    Registry 11:08 (4): the 9 seen transcripts without a stated model (TABLE resolves them to the other model by hash)
    enter the row as unknown model. In the code their label and feature files state no model, the seen group has no
    cross-check against TABLE, and the config template names no per-recording model file (`asr_models`), so
    `adapter.resolved_model` gives "unknown"; a config that named TABLE's file as `asr_models` would give them TABLE's
    model instead; the template has no such key, which keeps the reading of 11:08 (4).
13. The seen-only path (registry 06:44 (1)): it reads the instruments voice, asks, features, forecasts, sentences and titles
    of `labels/seen/`, top-level files only (a `refused/` subfolder is not read); the seen feature files are read from
    `labels/seen/features/` (the feature step, `features.py seen OUTDIR`, is to write there), because the path opens nothing
    outside `labels/seen`; a file in the pilot mapping layout (no group at its top) is refused; a tree outside the
    production tree is read only where its folders hold the synthetic marker and its files are marked synthetic; `run.py
    constants` runs the A10.7 permutation checks with 999 draws unless `--draws` says otherwise.
14. The freeze-2 check of this code (registry 06:44 (2)) reads only `llm/freeze2.json`: the six keys present and not empty,
    four of them in their forms (`sha256` and `analysis_code_sha256` dicts, `constants_sha256` a sha256, `registry_commit` a
    commit hash; `freeze1_frozen_utc` and `written_at_utc` only present: produce compares `freeze1_frozen_utc` with
    freeze.json), `analysis_code_sha256` (every module listed, every listed file, also one named by an absolute path or
    one that no longer exists, with its hash) and `constants_sha256`; it also requires the FREEZE2 constants to be set. It does not
    repeat produce's checks of the llm file hashes (`sha256`), of freeze 1 and of the registry commit (git); those gate every
    hold-out label, so no hold-out label exists unless they pass.
15. H9's two-stage bootstrap (registry 06:44 (4)): the second stage draws recordings within each cell (one creator, one
    family, one model); the cell rules (2 recordings, 2,000 words) and the rule that a hold-out cell's family has a seen cell
    are not reapplied inside a draw (as H5's per-side rule is not); idf, the function-word centres and spreads are computed
    over the draw's cells; the deleted words of the row "each family's 100 most distinguishing words deleted" are those of
    the observed cells; the re-rarefaction draws without replacement with its own sampler (the first k distinct of uniform
    64-bit draws), the same distribution as `rarefy` from another stream; a draw in which a contrast cannot be computed is
    counted as failed (`bootstrap_failed_draws`).
16. H5's creator-by-model strata (registry 06:44 (9)): the registered half-count value of a creator with several strata is
    the inverse-variance weighted mean of its strata's half-count values, with variance 1 / sum(1 / v_m); the points k of a
    whole-coded recording, the 2-recordings rule and the hit rules read the creator's totals over its strata.
17. H6 per recording (registry 06:44 (3)): a recording without an ask file stays in with a = b = 0 (T_i = 0 adds nothing to
    OE or to the MH strata), as before; the jackknife deletes a creator with all its recordings; the amended creator
    bootstrap draws creators with their recordings (no second stage, as before); the A10.7 expectation is conditional on each
    recording's T_i, and the registered half-count's by the convolution of the recordings' binomials; since 09:19 (3) the
    A10.7 check keeps the recordings without an ask file as well, so it reads the same creators and word totals as the
    analysis. The conditional reference of 09:19 (1) drew a_i given T_i independently between recordings (asks within a
    recording exchangeable between its words) and did not model asks that cluster in one stretch of a recording; since
    11:08 (1) and 12:52 (1) the reference draws clusters of asks (CHOICE 21), and dependence of asks beyond the 5-unit
    window is not modelled, as every H6 result states.
18. A5 on both intervals (registry 06:44 (5)) applies to the amended versions of H5 and H6; their registered versions keep
    the A5 interval they register; the refutations still read the MH interval alone.
19. The battery's H6 scenario `null_heterogeneous`: rates x exp(-8 (s - 0.5)) with s the recording's claimed share clamped to
    0.25 .. 0.75, and the claimed voice of a recording with both voices opening after 22 to 60 own units (40 to 48 otherwise),
    so that claimed shares spread between a creator's recordings (about 0.27 to 0.80).
20. The battery's H6 scenario `null_sparse_low_share` (registry 09:19 (1)): the claimed voice of a recording with both voices
    covers U(0.25, 0.45) of its units (claimed shares of the words in the two voices about 0.24 to 0.47 after label error;
    the low end stays above the 300-word rule in most recordings), and each creator has U{1, 2, 3} pay-or-enrol asks in all,
    placed on the units of its recordings with both voices in proportion to their words (3% of them unchecked, as in the
    other scenarios, so a few creators keep T = 0 and leave the T >= 1 set).
21. H6's clusters (registry 11:08 (1), window of 12:52 (1); `h6_asks.clusters_of`, `_recording_counts`): formed within a
    recording, by unit id, over every ask that passes the verdict and class rule, the asks on neither side too (a tie, or a
    majority of the ask's words outside both sides), so that an ask in an unlabelled unit does not split a burst; such
    asks join and link clusters but are not counted, and a cluster without an ask on the claimed or own side is dropped. A
    cluster's size is its number of asks on the claimed or own side; the sizes of a recording sum to its a + b. Under the
    reference a cluster is in the claimed voice with the recording's claimed share s_i (the share of the recording's words,
    not of the cluster's units), all its asks with it, even where the observed asks of one cluster lie on both sides. The
    unchecked asks are outside the clusters, as they are outside T. The sensitivity row forms the clusters again at 10
    units over the same creators and keeps the primary's sign-flip p.
22. Asks counted once (registry 12:52 (2); `adapter.merge_overlapping_asks`): the class is the candidate's `class`
    (`final_class` where it has none); two asks of one class overlap when their unit ranges share a unit, and overlaps
    chain (10..11, 11..12 and 12..12 are one ask); two asks of one class on the same range overlap too (the decision's
    words, not its example: the check reads a range once and cannot tell two offers apart); asks without a class are never
    merged. The merged ask spans the union of the ranges and carries its members' first verdict in the order ask, unchecked,
    unclear, not_ask (any other value last), with that member's `final_class` and `final_from`; where the merged verdict is
    "unchecked", it carries an unchecked member's small-model fallback, an ask of the class first. So under the primary
    rule and under the fallback row the merged ask counts exactly when one of its members would.
23. H6's reference draws (registry 11:08 (1)): 99,999 in the analysis (`h6_asks.REFERENCE_DRAWS`, the cluster p, the
    ask-level p beside it and the 10-unit row), 9,999 in the battery (`simulate.H6_BATTERY_REFERENCE_DRAWS`; at 17 creators
    about 0.2 s a reference with 99,999 draws against 0.02 s, about 2 CPU hours over the battery's H6 repetitions); the
    level of the test is exact at 0.005 and 0.05 with either count, and the battery's p near 0.005 is noisier than the
    analysis's.
24. The battery's H6 scenario `null_burst` (registry 11:08 (1); `simulate.burst_asks_records`): the claimed voice of a
    recording with both voices covers U(0.3, 0.7) of its units (`H6_BURST_CLAIMED_FRACTION`); each creator has U{1, 2}
    bursts (`H6_BURSTS_PER_CREATOR`) of U{2, 3, 4} pay-or-enrol asks (`H6_BURST_SIZES`); a burst's anchor unit is drawn
    over the units of the creator's recordings with both voices in proportion to their words, and its asks lie one a unit
    on consecutive units that contain the anchor and stay inside the anchor's stretch of one voice (where the stretch is
    shorter than the burst, the rest lies on its last unit), so a whole burst falls in one voice.
25. The battery's H6 scenario `null_gapped` (registry 12:52 (1); `burst_asks_records` with `burst_gaps`): the claimed voice
    covers U(0.25, 0.45) of the units (`H6_GAPPED_CLAIMED_FRACTION`, claimed shares below one half, as
    `null_sparse_low_share`); each creator has one burst (`H6_GAPPED_BURSTS_PER_CREATOR`) of U{2, 3, 4} asks
    (`H6_GAPPED_BURST_SIZES`) whose consecutive asks lie U{1, 2, 3} units apart (`H6_GAPPED_GAPS`), inside the anchor's
    stretch of one voice and covering the anchor; where the stretch is shorter than the burst's span the gaps become 1.
    Without `burst_gaps` the draws are those of `null_burst`, unchanged.
26. H6's detectable-effect note (registry 11:08 (1); `verdicts.h6_detectable_from_battery`): the power is the share of
    planted sets in which the guarded p (the larger of the registered and the amended p) reaches the first Holm step, at
    the battery's creator count nearest at or below the eligible count (12 or 17, so it understates the power above 17),
    for the planted rate ratios 0.5 (the smallest effect) and 0.25; 80% marks "detectable". It reads
    `sim_out/simulation-results.json` and uses it only if it is a full battery of the current task fingerprint; with a
    quick battery, another fingerprint or no file, the note says that none is stated.

## Simulation battery

Generators (`simulate.py`) build synthetic creators with creator-level habits (so the creator is the unit, as in CAL's
creator-level placebo), recordings of three kinds (both voices, claimed voice only, own-voice talk), units with true voices,
label views of two models with 3% and 6% of units flipped, uncued solo speech, offer spans that rule A and rule B treat
differently, unit timings, contraction counts, asks, forecast statements, sentence codes, titles and H9 token counts, all in
the label-file layouts and marked synthetic. The battery measures, at 12 and 17 eligible creators:

* null rejection rate of the p that enters Holm at 0.005 (the first Holm step) and at 0.05, with Monte Carlo SEs (2,000 sets;
  H9 1,000; halved at 23:55 local, see below);
* recovery of a planted effect near the smallest effect of interest and of a larger one (500 sets; H9 200): mean estimate
  against the large-sample target under the same generator (label error included) and against the planted value;
* coverage of the 90% interval used for A5 (H1, H2, H4: HKSJ; H9: creator bootstrap, two-stage with the cells re-rarefied
  in every draw, registry 06:44 (4), with `simulate.H9_BATTERY_BOOTSTRAP_DRAWS` = 99 draws in the battery, so its endpoints
  are rougher than the analysis's 9,999) and of the registered 95% interval; for H5 and H6 the coverage columns are those of
  the interval the Mantel-Haenszel estimate carries (the wider of the creator-bootstrap percentile and the jackknife t
  interval, registry 04:55 (j)), with the bootstrap percentile alone in the column beside it (A5 itself needs both that
  interval and the t interval on OE, registry 06:44 (5));
* H6 under a null whose ask rates differ between a creator's recordings (`null_heterogeneous`, registry 06:44 (3); CHOICE
  19), with the rejection rates of CAL-A11's pooled OE on the same sets beside those of the OE centred per recording;
* H6 under a null with claimed shares below one half and 1 to 3 asks per creator (`null_sparse_low_share`, registry
  09:19 (1); CHOICE 20), the region where the sign-flip of OE rejected too often;
* H6 under a null with bursts of 2 to 4 asks in one voice (`null_burst`, registry 11:08 (1); CHOICE 24), where a
  reference that draws asks one by one rejects too often, and under a null with one burst a creator whose asks lie 1 to 3
  units apart at claimed shares below one half (`null_gapped`, registry 12:52 (1); CHOICE 25), whose bursts 11:08's
  adjacency rule split wherever two asks lie two or more units apart; every H6 row carries, on the same sets, the two halves of the amended p (the cluster p alone, the
  sign-flip of OE alone), the ask-level p of 09:19, the sign-flip of CAL-A11's pooled OE and the amended p with the
  clusters of 11:08 (window 1) and of the 10-unit row (`simulate.H6_COMPARISON_PS`), with the mean largest cluster;
* the "not determinable" boundary: one creator below and at each minimum, with a large planted effect;
* the A10 guard (columns "guarded"): the rejection rate of the larger of the registered and the amended p, and the share of
  sets in which both versions meet the support conditions at the first Holm step.

Results: `sim_out/simulation-results.json` and `.md`; the quick battery `sim_out/simulation-results-quick.json` and `.md`.
H6's level tables on constructed numbers: `sim_out/h6-cluster-reference-levels.md` and `.json` (code of 12:52; the
table of 11:08 as `h6-cluster-reference-levels-pre-1252.*`); H6's p values through the battery's code path at 1,000 sets
a row: `sim_out/h6-pipeline-levels-1252.json` (section "Battery and checks of 11:08 and 12:52").

Runs of the full battery (all times local, EST):

1. 20:25 to 20:43, 30 workers, before the resource guard: died at 121 of 842 tasks in the machine's out-of-memory failure
   (log `sim_out/simulation-run-1-died-2026-11-20T2043.log`). Nothing kept.
2. 21:13 to 23:48:53, 4 workers, on the code loaded at 21:13 (before the revisions of 2026-11-21 UTC: H4 on V2 only, no A10
   guard, no M9 rules): terminated from outside at 788 of 842 tasks, exit 1 without a Python traceback (cause not found;
   no low-memory event in the system log). Kept as a record of the earlier code only: checkpoint
   `sim_out/simulation-checkpoint-code-2113.jsonl`, summary `sim_out/simulation-partial-code-2113.json` (rejection rates and
   mean estimates; the large-sample targets of H1 to H6 were among the unfinished tasks, so it has no coverage). On that code
   the null rejection rates of the Holm p were 0.0038 to 0.0075 at the first Holm step (4,000 sets; SE 0.0011; H9 2,000 sets,
   SE 0.0016) and 0.042 to 0.058 at 0.05; the highest were H5 at 12 creators (0.0075) and H9 at 17 (0.0075).
3. 23:58 to 01:43:17, 4 workers, on the revised code with the sizes halved: terminated from outside at 277 of 430 tasks
   (79% of the cost-weighted work after 1:45:20), again exit 1 without a traceback; in both terminations another session's
   job started within 25 seconds (23:49:18 and 01:43:24). It loaded the code before the decisions of 2026-11-21 04:55 were
   implemented (edits from about 00:06 local), so its numbers and its checkpoint fingerprint describe that earlier code.
   Kept as a record: checkpoint `sim_out/simulation-checkpoint-code-2358.jsonl`, summary
   `sim_out/simulation-partial-code-2358.json`. Finished there: H2, H9 and the 17-creator rows of H4, H5 and H6 (H5's
   12-creator null row 1,400 of 2,000 sets); not finished: H1, the other 12-creator rows of H4, H5 and H6, and the
   large-sample targets of H1 to H6 (so no coverage). Null rejection of the amended p that enters Holm: 0.003 to 0.006 at the
   first Holm step (2,000 sets, SE 0.0016; H9 1,000, SE 0.0022) and 0.040 to 0.056 at 0.05; of the guarded p (larger of
   registered and amended): 0.0007 to 0.006 and 0.006 to 0.055 (H5 lowest: the registered per-side minimum often leaves
   fewer than 12 creators). Planted large effects: mean estimates H2 D -0.36, H4 1.05 (planted 1.0), H5 0.81 (0.8), H6
   log ratio -1.41 (-1.39), H9 0.91 to 0.93 (target 0.88).

**A battery on the final code is still to run** (registry 06:44 (11); the battery started at 04:57 UTC on earlier code was
stopped at 06:42; no full battery ran on the code of 06:44, 09:19, 11:08 or 12:52). On the code as it stands, with the
FREEZE2 constants entered (task fingerprint `908111b94170ffcfe76088bcfcc985594d0b12781e1e15902426350e2de6bcc4`, 14:10:38
UTC; it differs from the fingerprint `d97db4a2a7c4` of the runs of 12:52 in `constants.py` alone, and the battery builds
its own constants from synthetic seen creators), `run.py simulate --estimate --workers 4` plans 590 tasks, 47,758 CPU
seconds (H9 25,996, H6 9,277 with its five null scenarios) and 3 h 19 min of wall time on 4 workers (`sim_cost.py` as
measured at 07:19 to 07:22 UTC); start it with `--expect-fingerprint 908111b94170` unless the code changes again. The
paragraphs below give the plans of earlier code. On the code of 09:19 (task fingerprint 091fa258ac1e...) `run.py simulate
--estimate --workers 4` plans 510 tasks, 44,430 CPU seconds (H9 25,996, H6 5,949 with its third null scenario) and
3 h 05 min of wall time on 4 workers (`sim_cost.py` as measured at 07:19 to 07:22 UTC, before H6's conditional reference;
see "Battery and checks of 09:19" for the measured cost). Command (guarded venv, from any folder; resumable only while no
module of `simulate.TASK_MODULES` changes): `C:\Users\mehta\et-channelers-tools\analysis-venv\Scripts\python.exe -I run.py
simulate --workers 4 --expect-fingerprint 091fa258ac1e`. Expected
time on the code of 06:44, from CPU seconds a repetition measured at about 07:15 UTC with no battery running (12 / 17
creators: H1 0.21 / 0.32, H2 0.57 / 0.86, H4 0.27 / 0.44, H5 0.37 / 0.55, H6 0.3 / 0.4, H9 7.8 / 9.2 with the two-stage
re-rarefied bootstrap of 99 draws, 5.0 at 17 before): about 38,000 CPU seconds (H9 about 24,000 of them, H6's added
heterogeneous null about 1,400). `run.py simulate --estimate --workers 4` (the cost model `sim_cost.py`, measured in a
4-worker pool at 07:19 to 07:22 UTC) plans 470 tasks, 42,800 CPU seconds (H9 26,000) and 2 h 58 min of wall time on 4
workers; the quick battery took 516 s against the model's 519 s with the light labelling jobs beside it, so about 3 h is
the expected wall time on the code of 06:44. With
199 H9 draws instead it would be about 1 h 20 min more (2,800 H9 repetitions x 100 draws x about 0.067 s, over 4 workers). The ETA is in `sim_out/simulation-status.json` while it runs; start
it with `--expect-fingerprint` set to the fingerprint `run.py hashes` prints for the frozen code.

The revised code was about five times slower in H2 and H5 (5.7 and 4.8 s a repetition at 17 creators): the creator bootstrap
of the registered DerSimonian-Laird versions recomputed the same t quantiles by bisection in every draw. `stats.t_ppf` is now
memoised (a pure function of q and df); six tasks covering every hypothesis gave byte-identical results before and after,
and H2 and H5 fell to 1.17 and 0.99 s.

### Battery and checks of 11:08 and 12:52

Guarded venv, synthetic or constructed data only. The code of 12:52 has task fingerprint
`d97db4a2a7c472fec0ec118c70a65e260cb9099384d4ed0c20170975960f2e7d` (features.py `d47a943c...`, features-4; h6_asks.py
`cac91d34...`, adapter.py `a5265796...`); every module hash recorded by the quick battery below equals the file at 14:10
UTC except `constants.py` (`ab9ffbd5...` then, `c079dbf8...` with the FREEZE2 constants). The code of 11:08 had fingerprint
`ba2112842874...`; its outputs are kept as `sim_out/e2e-pre-1252/`, `sim_out/simulation-*-quick-pre-1252.*` and
`sim_out/h6-cluster-reference-levels-pre-1252.*` (those of 09:19 as `*-pre-1108*`).

* `run.py selftest`: 224 tests (22 new in `test_decisions_1252.py`, 18 in `test_decisions_1108.py`, 19 in
  `test_features_h9.py`). With the FREEZE2 constants entered 4 of them fail, each asserting the state before the entry
  (section "FREEZE2 constants"; rerun 14:12:43 to 14:14:31 UTC).
* **Levels on constructed numbers** (`sim_out/h6-cluster-reference-levels.md` and `.json`, written 13:13:58 UTC by
  `simulate.h6_cluster_reference_levels` on fingerprint `d97db4a2a7c4`; exact enumeration, no simulation; the data come
  from the true clusters, the tests read the clusters the rule sees; the probability that each p is at most 0.005 / 0.05;
  one table for the analysis's 99,999 draws and one for the battery's 9,999). Selected rows, 99,999 draws, in percent:

  | case | cluster p | ask-level p (09:19) | sign-flip of OE | amended p |
  |---|---|---|---|---|
  | 17 creators, one ask each, s = 0.3 | 0.23 / 1.93 | 0.23 / 1.93 | 1.93 / 7.74 | 0.23 / 1.93 |
  | 17 creators, one burst of 3, s = 0.3 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
  | 12 creators, one burst of 3, s = 0.3 | 0.00 / 1.38 | 8.50 / 8.50 | 1.38 / 8.50 | 0.00 / 1.38 |
  | 17 creators, one burst of 3 asks 2 units apart, s = 0.3, window 5 | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |
  | the same, window 1 (the rule of 11:08) | 7.74 / 20.19 | 7.74 / 20.19 | 1.93 / 7.74 | 1.93 / 7.74 |
  | 17 creators, one burst of 4 asks 1, 2 and 3 units apart, s = 0.35, window 5 | 0.07 / 3.27 | 10.28 / 23.48 | 3.27 / 10.28 | 0.07 / 3.27 |
  | the same, window 1 | 3.27 / 10.28 | 10.28 / 23.48 | 3.27 / 10.28 | 3.27 / 10.28 |
  | 17 creators, one burst of 3 asks 6 units apart, s = 0.3, window 5 (beyond it) | 7.74 / 20.19 | 7.74 / 20.19 | 1.93 / 7.74 | 1.93 / 7.74 |
  | the same, window 10 (the sensitivity row) | 0.23 / 1.93 | 7.74 / 20.19 | 1.93 / 7.74 | 0.23 / 1.93 |

  In the 27 cases within the window (bursts, gapped bursts at the window of 5, sparse low-share and plain single asks)
  the amended p rejects at most 0.42% at 0.005 and 4.76% at 0.05 (0.40% and 4.48% with 9,999 draws), the cluster p alone
  at most 0.44% and 4.81%; the sign-flip of OE exceeds 0.005 in 17 of them (up to 3.27%; 11.82% at 0.05) and the ask-level
  p in 16 (up to 10.28%). Under 11:08's window of 1 the gapped bursts reach 1.13% to 3.27% at 0.005 for the amended p
  (the fifth verification's case, one burst of 3 asks 2 units apart at s = 0.3, 1.93%). Beyond the window the amended p
  rejects as the sign-flip alone does (1.93% at 0.005 in both cases with s = 0.3): that is the dependence the result
  states is not modelled; the 10-unit row gives 0.23% on those cases. The table of 11:08
  (`h6-cluster-reference-levels-pre-1252.md`, 12:06:22 UTC, fingerprint `ba2112842874`) holds the 21 burst, sparse and
  plain cases with the same figures.
* **The battery's path on synthetic sets** (`sim_out/h6-pipeline-levels-1252.json`, 1,000 sets a row, 9,999 reference
  draws, fingerprint `d97db4a2a7c4`, 612.8 s, written at about 13:55 UTC by a script outside the package that calls
  `simulate.task`; Monte Carlo SE 0.0022 at 0.005 and 0.0069 at 0.05). Rejection rates at 0.005 / 0.05:

  | scenario | creators | amended p | cluster p | sign-flip of OE | ask-level p | amended, window 1 | amended, window 10 | guarded |
  |---|---|---|---|---|---|---|---|---|
  | null | 17 | 0.002 / 0.035 | 0.003 / 0.046 | 0.003 / 0.042 | 0.004 / 0.049 | 0.002 / 0.035 | 0.002 / 0.033 | 0.001 / 0.033 |
  | null_burst | 17 | 0.004 / 0.040 | 0.004 / 0.042 | 0.004 / 0.048 | 0.050 / 0.161 | 0.004 / 0.041 | 0.003 / 0.041 | 0.003 / 0.033 |
  | null_gapped | 12 | 0.004 / 0.045 | 0.004 / 0.045 | 0.016 / 0.065 | 0.050 / 0.149 | 0.015 / 0.065 | 0.004 / 0.043 | 0.004 / 0.043 |
  | null_gapped | 17 | 0.003 / 0.034 | 0.003 / 0.034 | 0.009 / 0.069 | 0.053 / 0.146 | 0.009 / 0.069 | 0.003 / 0.033 | 0.003 / 0.034 |
  | null_sparse_low_share | 17 | 0.001 / 0.041 | 0.001 / 0.041 | 0.006 / 0.061 | 0.001 / 0.043 | 0.001 / 0.042 | 0.000 / 0.041 | 0.001 / 0.010 |

* `run.py e2e --workers 2` on the code of 12:52 (about 13:14 to 13:32 UTC, `sim_out/e2e/`; the run of the code of 11:08,
  about 11:36 to 11:54 UTC, is in `sim_out/e2e-pre-1252/`): every plant check true, the seen-only path gives the in-memory
  constants, the repeat with another worker count is identical, "validated" absent. Verdicts as before: H1, H2, H4, H5 and
  H9 "supported (model-coded)"; H6 "not determined (Holm step, A5 interval, effect-size condition)", uninformative, MH
  rate ratio 0.641, amended p 0.2009 (cluster p 0.1979, sign-flip p 0.2009, ask-level p 0.195 shown; 27 clusters, the
  largest of 2), registered p 0.0704, the 10-unit row p 0.2009 (cluster p 0.1963), no verdict. A10.7 on the e2e seen
  cohort: section "A10 and its guard".
* `run.py simulate --quick --workers 4` on the code of 12:52 (finished 13:41:16 UTC, 476 s, 64 tasks, all checkpoint lines
  on fingerprint `d97db4a2a7c4`, no module changed during the run; `sim_out/simulation-results-quick.*`; 30 null and 15
  planted sets a row, so every share is rough). H1, H2, H4, H5 and H9 as before. H6: under all five null scenarios the
  amended p and the guarded p reject at 0.005 in 0 of 30 sets at 12 and at 17 creators (0 to 0.10 at 0.05), while
  the ask-level p rejects in 0.067 (12) and 0.10 (17) of the `null_burst` sets and 0.067 and 0.10 of the `null_gapped`
  sets, and the sign-flip of OE and the window-1 amended p in 0.033 of the `null_gapped` sets at both counts. Planted:
  at the smallest effect "supported" in 0.067 (12) and 0.13 (17) of the sets, at the large plant 0.33 and 0.6 (0.33 and
  0.67 on the code of 11:08, quick battery of about 11:55 to 12:03 UTC on fingerprint `ba2112842874`). At the boundary H6 reads
  "not determinable" with 11 creators and "not determined (Holm step)" at 12 (p 0.0078 on that one set), as before.

### Battery and checks of 09:19

All on the code of the decisions of 09:19 (task fingerprint 091fa258ac1e2091...), guarded venv, synthetic or constructed
data only. The outputs of the code of 06:44 are kept as `sim_out/e2e-pre-0919/` and `sim_out/simulation-*-quick-pre-0919.*`.

* `run.py selftest`: 164 tests OK (09:42:24 to 09:43:54 UTC; 149 before, 15 new in `test_decisions_0919.py`).
* Code path on constructed numbers (scratchpad script, not part of the package): 20,000 simulated null sets per case
  through `h6_asks.conditional_p` (999 draws, so 0.005 x 1,000 and 0.05 x 1,000 are whole) and `stats.signflip_p`, beside
  the exact rates of the same tests (`simulate.h6_conditional_level` with 999 draws, `h6_signflip_level`); Monte Carlo SE
  0.05% at 0.005 and 0.15% at 0.05:

  | case | conditional reference: simulated (exact), at 0.005 and 0.05 | sign-flip of OE: simulated (exact) |
  |---|---|---|
  | 17 creators, T = 1, s = 0.3 | 0.16% (0.21%), 1.81% (1.93%) | 1.81% (1.93%), 7.44% (7.74%) |
  | 17 creators, T = 2, s = 0.3 | 0.24% (0.27%), 3.28% (3.34%) | 0.86% (0.99%), 6.16% (6.00%) |
  | 17 creators, T = 3, s = 0.4 | 0.32% (0.33%), 4.06% (3.98%) | 0.57% (0.54%), 5.30% (5.25%) |
  | 17 creators, T cycled 1, 2, 3, s = 0.2 | 0.33% (0.37%), 4.00% (4.15%) | 3.18% (3.30%), 9.70% (10.07%) |

* `run.py e2e --workers 2` (09:44:10 to 10:01:49 UTC, exit 0, `sim_out/e2e/`): every plant check true (ASR rule,
  TABLE cross-check, extra-source exclusion, model-stratified counts with the row in every hypothesis); the seen-only
  path read 320 voice, features and forecasts files and gives the in-memory constants; the repeat with another worker
  count is identical; "validated" absent. Verdicts: H1, H2, H4, H5 and H9 "supported (model-coded)"; H6 "not determined
  (Holm step, A5 interval, effect-size condition)", uninformative, MH rate ratio 0.641, amended p 0.190 (conditional
  reference; 0.20 under the sign-flip before), registered p 0.070 (unchanged). A10.7 on the e2e seen cohort (40
  creators, 159 recordings with both voices, none without an ask file): H6 amended OE null mean 0 against a tolerance of
  0.0169 (OE_smallest_effect -0.169), "centred"; CAL-A11's pooled OE -0.0061, "centred" on that scale; the registered
  half-count -0.1035 against 0.0693, "recentring needed" (as before); H5 amended OE 0.0001 against 0.0023
  (OE_smallest_effect 0.0234, 40 creators: smaller than at even sides because the channelled side holds about three
  quarters of each creator's hits), "centred"; registered -0.0096 against 0.04, "centred".
* `run.py simulate --quick --workers 4 --expect-fingerprint 091fa258ac1e` (10:02:41 to 10:13:29 UTC, 648 s, no module
  changed during the run; `sim_out/simulation-results-quick.json` and `.md`; 30 null and 15 planted sets per row, so every
  share is rough, SE about 0.013 at 0.005 and 0.04 at 0.05). The 47 tasks of H1, H2, H4, H5 and H9 give results
  identical to those of the code of 06:44. H6 under its three null scenarios, the amended p that enters Holm (conditional
  reference) at 0.005 and 0.05, the guarded p, and the sign-flip of OE on the same sets:

  | scenario | creators | amended | guarded | sign-flip of OE (before 09:19) | pooled OE (before 06:44) |
  |---|---|---|---|---|---|
  | null | 12 | 0.033, 0.067 | 0, 0.067 | 0, 0.067 | 0, 0.067 |
  | null | 17 | 0, 0.10 | 0, 0.10 | 0, 0.10 | 0, 0.10 |
  | null_heterogeneous | 12 (25 determinable) | 0, 0.04 | 0, 0.04 | 0, 0.08 | 0.04, 0.16 |
  | null_heterogeneous | 17 | 0, 0.10 | 0, 0.10 | 0, 0.167 | 0.033, 0.267 |
  | null_sparse_low_share | 12 | 0, 0 | 0, 0 | 0, 0.10 | 0, 0.067 |
  | null_sparse_low_share | 17 | 0, 0.033 | 0, 0 | 0, 0.033 | 0, 0.033 |

  Planted H6 effects: at the smallest effect (rate ratio 0.5) "supported" in 0.07 (12) and 0.13 (17) of the sets, at the
  large plant 0.33 and 0.87, both versions alike (0.07, 0.13, 0.33 and 0.67 before); the amended p rejects at 0.005 at
  least as often as the sign-flip did in every planted row. At the boundary H6 reads "not determinable" with 11 creators
  and "not determined (Holm step)" at 12 (p 0.0081 on that one set; 0.0078 under the sign-flip), the other hypotheses as
  before. Measured seconds a repetition (12 / 17 creators): H6 0.31 / 0.46 (0.32 / 0.49 before; the cost model 0.35 /
  0.49), so the conditional reference costs nothing measurable; H9 13.0 / 13.0 against 8.0 / 9.1 in the run of 06:44 with
  identical results, so this run's machine was slower for H9 (cause not found; no other Python process was running).
* `run.py simulate --estimate --workers 4`: 510 tasks, 44,430 CPU seconds (H9 25,996, H6 5,949), 3 h 05 min on 4 workers.
  At this run's measured speeds (H9 about 1.4 times the model, the others 0.75 to 0.95 times) it would be about
  52,500 CPU seconds, about 3 h 40 min. The full battery was not started.

Quick battery on the code of 06:44 (2026-11-21 07:53 to 08:01:43 UTC, 4 workers beside the light labelling jobs, 516 s
against 519 s planned by `sim_cost.py`, task fingerprint 8f778e9f33b4 on all 58 checkpoint lines, no module changed during
the run, code hashes equal to those of the e2e reports of 07:33 to 07:52 UTC; `sim_out/simulation-results-quick.json` and
`.md`; the quick outputs of the 04:55 code are kept as `sim_out/simulation-*-quick-pre-0644.*`, the e2e outputs of before
as `sim_out/e2e-pre-0644/`, whose report folder also holds the partial outputs of an e2e stopped at 07:28 UTC on mixed
code; 30 null and 15 planted sets per row, so every share is rough). Under the null the p that enters Holm and the guarded
p reject at 0.005 in at most 1 of 30 sets for every hypothesis (H1 and H9 at 12 creators, H2 at 17 plain only). The
changed rules: (3) H6 under the null with ask rates that differ between recordings (`null_heterogeneous`): the OE centred
per recording rejects in 0 of 25 and 0 of 30 sets at 0.005 (12 and 17 creators) and 0.08 and 0.17 at 0.05; CAL-A11's
pooled OE on the same sets 0.04 and 0.03 at 0.005 and 0.16 and 0.27 at 0.05 (under the plain null the two agree: 0 at
0.005, 0.07 and 0.10 at 0.05); the MH interval with creator-by-recording strata covers the target in 0.97, 0.83, 0.80 and
1.0 of the sets at 12 creators (null, heterogeneous null, large plant, smallest effect) and 0.73, 0.90, 1.0 and 0.93 at
17, the bootstrap percentile alone 0.90, 0.80, 0.67, 0.93 and 0.73, 0.87, 0.87, 0.93; at the smallest effect (rate ratio
0.5) "supported" in 0.07 (12) and 0.13 (17) of the sets (0.07 and 0.07 before), at the large plant 0.33 and 0.67 (0.33 and
0.73 before); the log MH ratio under the plain null at 17 creators averages -0.17 against a target of 0.02 (-0.17 before
too: few asks). (5) A5 on both intervals leaves H5's support unchanged (amended alone 1.0 and 0.87 at 12 creators, 1.0 and
1.0 at 17; both versions 0.2, 0, 1.0, 0.8, as before). (4) H9's two-stage interval (99 draws) covers the target in every
row (1.0 in all six; 0.93 at the smallest effect with 17 creators before), which suggests it is conservative; "supported"
at the smallest effect 0 (12) and 0 (17) of the sets (0.07 and 0.13 before), while the permutation p still rejects at
0.005 in 0.07 and 0.13 as before, so the wider interval now blocks A5 there; at the large plant 1.0. (9) H5's
creator-by-model strata and (1), (2) are not exercised by the battery (it builds no model-stratified view and reads no
files); the unit tests and e2e cover them. At the boundary every hypothesis is "not determinable" one creator below its
minimum and flagged uninformative; at the minimum H1, H2, H4, H5 and H9 read "supported", and H6's 12-creator set now
reads "not determined (Holm step)": its exact sign-flip p is 0.0078 (2^-7) under the per-recording OE, 0.0039 before, on
the same synthetic set (one set, so a property of that set, not of the minimum rule).

Quick battery on the final code after the decisions of 04:55 (2026-11-21 05:50 to 06:00 UTC, 4 workers beside another
battery, 576 s, no module changed during the run; `sim_out/simulation-results-quick.json` and `.md`, whose code hashes match
the modules; the earlier quick outputs are kept as `sim_out/simulation-*-quick-pre-0455.*`; 30 null and 15 planted sets per
row, so every share is rough): under the null the p that enters Holm and the guarded p reject at 0.005 in at most 1 of 30
sets for every hypothesis (H1 and H9 at 12 creators, H2 at 17 plain only). H4 on the embodied voice keeps every creator
eligible (determinable share 1 at 12 and 17) and reaches "supported" at the smallest effect in 0.2 (12) and 0.53 (17) of the
sets, at the large plant in 1.0. The MH interval of (j) covers the large-sample target at least as often as the bootstrap
percentile alone in every H5 and H6 row (H5: 0.967, 0.8, 0.867, 0.9, 0.867, 0.933 against 0.933, 0.8, 0.8, 0.9, 0.8, 0.933;
H6: 0.967, 0.8, 1.0, 0.767, 0.933, 0.933 against 0.933, 0.6, 0.933, 0.767, 0.867, 0.933). With the two-stage registered
intervals the shares supported by both versions are those of the earlier run: H5 at 12 creators 0.2 (large plant) and 0
(smallest effect), at 17 creators 1.0 and 0.8; H2 at the smallest effect 0.07. At the boundary (rule (g)) H2 with 8 creators
and H9 with 7 now read "not determinable in the amended version: too few eligible creators (8 of 9)" and "(7 of 8)", H5 with
11 "not determinable in both versions", all flagged uninformative; every hypothesis reads "supported" at its minimum.

Quick battery on the revised code before the decisions of 04:55 (2026-11-20 about 23:15 local, 4 workers, 779 s, no module
changed during the run; 30 null and 15 planted sets per row, so every share is rough): under the null, the p that enters Holm and the guarded p reject at
0.005 in at most 1 of 30 sets for every hypothesis. The guard costs support where the registered version is weaker: H5 at 12
creators reaches "supported" with both versions in 0.2 of the sets at the large plant (1.0 for the amended version alone) and
0 at the smallest effect (0.87 alone), because the registered per-side minimum leaves fewer than 12 creators; at 17 creators
1.0 and 0.8. H2 at the smallest effect: 0.07 with both versions against 0.13 (12 creators) and 0.2 (17) alone. At the
boundary, H2 with 8 creators and H9 with 7 read "not determined: the registered and the amended versions differ" (their
registered minimums were 8 and none); H1, H4, H5 and H6 read "not determinable" at 11 and "supported" at 12.

## Open items

* The adapter follows `label-files.md` as of 2026-11-20 21:05 local. Its "Voice and asks (unchanged)" section points to
  `produce.voice_record` and notes that pilot round 2 is revising the ask check prompt; if the check fields change, only
  `adapter.parse_asks` changes (it reads `final`, `final_class`, `final_from`, `final_small_fallback`).
* Feature files for hold-out recordings: `prep.load_units` opens non-seen transcripts only under `produce.py` after freeze 1,
  so the feature step for the hold-out needs a guarded command (for example a `produce.py features` subcommand that calls
  `features.unit_features` and `features.h9_counts`), added before freeze 1 or by a new freeze-1 entry. Since 12:52 (4) its
  files must carry the seen files' `feature_version` (features-4, `features.py` `d47a943c...`, with the names input
  `h9-names-1108.private.json` `bf9ace2f...` and the families input `h9-families.private.json` `33a1fbf8...`), or every
  bundle that holds both is refused.
* A10 (registry row 2026-11-21 03:08) is written from the CAL drafts as A10.1 to A10.7 and becomes final at freeze 2 at the
  latest; the code follows the registry row and the drafts.
* The reworded-prompt and altered-input label runs: their file layout is not fixed; the code reads them as extra sources in the
  voice layout.
* No practice-ask labels exist (R27 b); H6's practice-ask row says so.
* The ASR-model rule is in the registry (row 2026-11-21 03:08, "Recognizer rule"). The guarded hold-out feature step (above)
  should write `asr_model` from `info.model_role`, the `self_name` flag and the h9 counts as `features.py` does
  (FEATURE_VERSION features-4), with the same names and families inputs as the seen run.
* H4's primary is the embodied voice again (registry 04:55 (a)); the open item of track B on the 02:55 reading is closed.
* The registered H2 interval is read as the creator bootstrap (creators, then recordings, R1; registry 04:55 (d)) of the
  DerSimonian-Laird pooled D, the registered H5 and H6 versions as the half-count estimators of hypotheses.md (H6 with T = 0
  creators kept, as registered, and uncentred); the registered random-effects pools as DerSimonian-Laird with normal
  intervals (hypotheses.md names no method; note a of the A10 draft). They are listed in each module's A10_REPLACES.
* Closed by 06:44 (4): H9's creator bootstrap now draws creators, then recordings, and re-rarefies the cells in every draw,
  in both versions.
* Closed in code by 06:44 (1): the seen-only path (`adapter.load_seen_bundle`, `run.py constants`). Done before freeze 2,
  outside this package: the seen feature files in `llm/labels/seen/features/` (`features.py seen`, CHOICE 13; H4's
  yardstick needs them; features-3 at 11:20:46 to 11:22:20 UTC, then features-4 at 13:01:12 to 13:02:48 UTC, 1,293 files,
  recorded in the private features note); `run.py constants` on the real seen labels after seen production had finished
  (14:00:03 to 14:00:37 UTC); the three printed constants entered in `constants.py` (section "FREEZE2 constants"). Still
  to do: hash (`run.py hashes`) and write `llm/freeze2.json` with the six keys (it did not exist at 14:10:38 UTC); commit the
  package to the analysis branch first (registry 09:19 (5); `code/hypotheses/` was untracked at 14:07 UTC). CAL part (f)
  can read the seen labels through `adapter.load_seen_bundle`; it is not written here.
* Four tests assert the state before the FREEZE2 entry (section "FREEZE2 constants"): with the constants entered they
  fail, so `run.py selftest` exits 1 until they are rewritten to patch the constants to None (as the constants task's
  scratchpad check does) or to assert the entered state. A test file change does not change the freeze-2 code hashes
  (top-level modules only) or the task fingerprint.
* Memory of the seen-only path: `adapter.load_seen_bundle` still reads every file of every instrument before it parses
  any. The variant that parses each file as it is read was withdrawn on 2026-11-21 at about 08:13 UTC and not applied; the
  run of `run.py constants` on the whole seen tree (14:00:03 to 14:00:37 UTC) ended with exit 0 under the guarded venv's
  ceiling, so the variant was not needed for it. The analysis on hold-out and seen folders reads more files and goes
  through `load_bundle`, not this path.
* Closed by 06:44 (2): one freeze-2 record. `run.py hashes` prints `analysis_code_sha256` and `constants_sha256` for it; the
  other four keys come from produce's side (freeze 1, the llm file hashes, the registry commit, the time written).
* The full simulation battery on the final code is still to run (section "Simulation battery": fingerprint
  `908111b94170` with the FREEZE2 constants, about 3 h 19 min planned on 4 workers); no code since 06:44 has had one. H6's
  detectable-effect note states none until it has run (CHOICE 26).
* Closed by 09:19 (1) to (4): H6's level with sparse asks at claimed shares below one half, the OE-scale tolerance of
  A10.7, the null check's recordings without an ask file, the verifier's test file in the package. Closed by 11:08 (1)
  and 12:52 (1): the level of H6's reference with bursts of asks in one voice, also when their asks lie up to 5 units
  apart (the amended p as the larger of the cluster p and the sign-flip p), and H6's detectable-effect note (from the
  battery, no longer from the sign-flip's power on normal creator values). The A10 draft's A10.1, A10.4, A10.7 and guard
  paragraph were brought in line with this reference on 2026-11-21 between 14:07 and 14:36 UTC.
* Stated, not modelled (12:52 (1)): dependence of asks beyond the 5-unit window. Where a burst's asks lie more than 5 units
  apart at claimed shares below one half, both halves of the amended p over-reject (1.93% at 0.005 in the constructed case
  of three asks 6 units apart at s = 0.3, 17 creators); the 10-unit sensitivity row shows how far a result rests on it.
* H9's closed name list and family name variants (for the opening rule and masking) are private inputs of the feature step.
  Since registry 11:08 (2) the names input is the union of the NAMES v2 list forms and every token of every family variant
  (`features.h9_mask_forms`, CHOICE 9).
* Not changed here: the sections "Decisions of 2026-11-21 06:44" and "09:19" describe the code of their time where later
  decisions changed it (H6's reference of 06:44 and 09:19 and its 9,999 draws); the later sections say what changed.
