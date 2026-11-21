# Draft for the registry: amendment A10 and its companions

**Status: a draft for the lead to paste into [`registry.md`](registry.md). Nothing here is in force until the lead
enters it.** Written on 2026-11-21 between about 03:13 and 03:25 UTC, under the registry decisions of 2026-11-21 at
02:50, 02:55 and 03:08 UTC; brought in line with the rows of 03:12, 03:18 and 03:21 UTC by the verifier at about 03:40
UTC; revised between 06:03 and 06:16 UTC to the registry rows of 04:55 UTC (three rows), 04:59 UTC (two rows) and
05:00 UTC, the freeze-1 entry, and the hypothesis code as it stood when read between 06:03 and 06:15 UTC (three of its
files, the adapter, its README and a test file, changed again between 06:13 and 06:15 UTC). Checked by a second
verifier between 06:22 and 06:41 UTC against the registry, hypotheses.md, the git log of the registry and the hypothesis
code as last changed at 06:14:36 UTC; no code file changed between then and 06:37 UTC. The registry rows of 06:33,
06:36 and 06:39 UTC and the contact-log entry committed at 06:36 were added to Part 8; rows entered later go into
Part 8 when the lead pastes it. The thirteen sentences the revision had marked for a check against code were
confirmed or corrected, and the marks removed. Revised again between 08:18 and 08:35 UTC to the registry rows up to
07:50 UTC (the last commit of the registry, 07:50:12 UTC: the rows of 06:44 and 07:50 and the contact-log entry of
06:49:10) and to the hypothesis code as the third engineering round left it (simulation task fingerprint
`8f778e9f33b4`; every module's hash equals those of the end-to-end run of 07:33 to 07:52 UTC and of the quick battery
of 07:53 to 08:01:43 UTC, both on synthetic data; the 06:44 decision tests pass, 28 of 28, rerun at 08:21 UTC). Each
decision of 06:44 is written where it belongs (Parts 1, 3, 4, 6, 7 and 8). Checked by a third verifier between 08:59
and 09:18 UTC against the registry up to its commit of 09:10:22 UTC (still the last at 09:17:49), hypotheses.md (hash
unchanged), the git log of the registry and the hypothesis code (task fingerprint still `8f778e9f33b4` at 09:17:56,
every module hash unchanged since the quick battery; the 06:44 decision tests pass, 28 of 28, at 09:11 UTC). The eight sentences marked for a check against
code were confirmed (six) or corrected (two: the forms the freeze-2 check reads, in Part 4; the null-mean check of
H2's amended version, in A10.7 point 3), and the marks removed. Also corrected: the definition of s_i and the level of
the OE sign-flip (A10.1, A10.4), H10's run condition (A10.2) and the tolerance of the null-mean check (A10.7). The three
registry commits after 07:50:12 UTC were added to Part 8 (08:24:06, 08:33:43, 09:10:22). If the code changes again
before freeze 2 (the memory variant of the seen-only loader, the constants), the sentences of A10.4, A10.7 point 3,
Part 4 and Part 6 that describe code are the ones to check again. Revised again on 2026-11-21 between 14:07 and
14:36 UTC (date -u) to the registry rows of 09:19, 11:08, 11:10, 12:52 and 13:05 UTC (commits 09:19:46 to 13:05:21 UTC;
13:05:21 was still the last commit of the registry at 14:07) and to the hypothesis code after its fifth and sixth
engineering rounds: H6's final reference (the larger of the cluster-level conditional p and the sign-flip p of OE, clusters
at a 5-unit window), the ask deduplication, the feature-version refusal, H9's token rule features-4, and the freeze-2
constants as entered (task fingerprint `d97db4a2a7c4` for the runs and level tables of 12:52; `908111b94170` at 14:10:38
UTC, after the constants were entered, `constants.py` being the only module that differs). A10.1, A10.4, A10.7 point 3,
the guard paragraph and its table, Parts 4 and 6 and Part 8 were changed; sentences that describe code were read against
the code and its outputs, and none is left marked for a check. Checked by a fourth verifier between 14:35 and 15:00 UTC
(date -u) against the registry (last commit still 13:05:21 UTC), hypotheses.md (hash unchanged), the registry's git log
and the hypothesis code (task fingerprint `908111b94170` at 14:37:35 UTC; `llm/freeze2.json` absent at 14:37:35 and
14:48:41): the level tables and the 1,000-set file were re-read cell by cell, `run.py constants` was run again on the
seen tree (14:39:26 to 14:40:01 UTC, exit 0, every printed value identical to the run of 14:00), the battery plan
(`--estimate`) and the selftest (224 tests, the same 4 not passing, 14:41:30 to 14:43:20 UTC) were rerun. Corrected: the
labelling side's A10 check (Part 4: it tests for the string `**A10.`, which the registry has held since the row of 09:19),
the class of 12:52 (2) (Part 1, introduction), the time of the level table and a wording of its counts (A10.4), the
number of runs of the seen-only path (Part 4), and three phrases that would not read right once pasted (Part 8).
Aligned for pasting on 2026-11-21 between 15:46 and 16:20 UTC (date -u), to be pasted before freeze 2, which is to be
written right after the paste: brought in line with the registry row of 15:14 UTC (commit 15:14:55 UTC, the only
registry commit after 13:05:21 and still the last at 16:04:08 UTC), with the hypothesis code as committed (`c8f1f73`,
15:16:44 UTC, and `c08c2a8`, 15:17:18 UTC, which sets LF line endings; task fingerprint `32757fe34057` and constants
SHA-256 `cf544528...` at 15:49:31 UTC; selftest 224 of 224 passing, 15:50:25 to 15:52:15 UTC) and with produce.py's
`features` command as its file read at about 15:48 UTC (last written 15:41:50 UTC). The settled points of 15:14 (2) are
written in Part 1 (introduction), A10.2, A10.4, A10.7 point 3, the guard paragraph and Parts 2, 3, 4 and 6; 15:14 (1)
in Part 4; Part 8 has two rows for 15:14 and a new pending list. Sentences that state a state of things were made true
for the paste; the ones that could not be are listed in the notes (item 6).

**Sources.** The calibration item's draft amendments (CAL, second-round panel, numbered A8 to A14 there; private
panel record); the registry rows of 2026-11-21 at 02:50 (definition of "uninformative", hold-out-only primary),
02:55 (relayed voice merged), 03:08 (A10 with its guard, replacement of the human check, recognizer rule), 04:55
(budget guard at worst case; the lead's decisions (a) to (n) on the freeze-readiness open points; the second reading),
04:59 (freeze 1 without the known-answer battery's last voice batches; gate VG-6), 05:00 (seen production), 06:33,
06:36 and 06:39 (interfaces of the seen chain; the exploratory reporting plan), 06:44 (the decisions on the second
verification, numbered (1) to (11)), 07:50 (the forecast critic's interface), 08:33 (the known-answer battery's voice
parts through the standard interface), 09:10 (the known-answer battery complete), 09:19, 11:08 and 12:52 (the decisions
after the third, fourth and fifth verifications of the hypothesis code), 11:10 (seen production complete), 13:05
(addendum 2 of the exploratory reporting plan) and 15:14 (freeze 1, amendment 1, for the hold-out feature step; points
settled for the A10 text); the hold-out contact log, up to
its entry of 06:49:10 (no later entry); the freeze-1 entry (04:58:22 UTC); the paper review's points M6 and M8 (private meta-review); the
hypothesis code in `code/hypotheses`, its README and its synthetic test, end-to-end and quick-battery outputs, and the
level tables of H6's p values on constructed numbers (`sim_out/h6-cluster-reference-levels.md`) and on synthetic
creators (`sim_out/h6-pipeline-levels-1252.json`; both read only); the output of `run.py constants` on the seen labels
(14:00 UTC, and the verifier's rerun at 14:39 UTC with the same output; counts and derived numbers only); the private features note (counts only); the checkability prompt and its answer
schema; the docstring and freeze-2 checks of produce.py, read at about 15:48 UTC (code only); the git log of this
worktree for every time in the deviation table.

**Public-safe.** No transcript text, creator or channel names, video ids, titles, model names or per-creator values.
CAL's private figures appear only where the registry already states them (H3's mean of -0.063 under its own reference,
its seen value 0.019 and 0.083 recentred, the minimums of 8 and 9 creators, the projected eligible counts 5, 3 and 5
against 12, the gate figures the registry quotes, and H4's yardstick with and without its minimum, 0.1474 over 52
creators and 0.156 over 60, from the row of 15:14), with one exception: CAL's simulated rejection rate of the OE
sign-flip (A10.4), a rate over simulated sets that holds no creator value, which the lead asked to state. Gate VG-6's
figures are those of the registry row of 04:59. The exact rejection rates in A10.4 are computed on constructed numbers,
and its simulated rates on synthetic creators, not on any creator or label. The freeze-2 constants and the A10.7 null
means (A10.7 point 3, Part 4) are aggregates over seen creators printed by `run.py constants`, with no creator value.

**What existed when A10 was written (03:13 to 03:40 UTC).**

* Known: H3's hold-out result (2026-11-20 20:39 UTC); CAL's calibration, coverage and power runs on seen creators and
  on unlabelled analogues; the pilots, gates, reliability runs and known-answer battery of the instruments, all on
  seen creators; the paper review.
* Not existing: freeze 1; any first-round production label on any creator (the cost ledger holds only pilot,
  reliability, smoke-test, known-answer, verification, discovery and panel requests; checked at 03:27 UTC, the latest
  entry, at 03:20 UTC, is a panel second reading on seen check creators); any
  label of a hold-out creator; any registered quantity of H1, H2 or H4 to H10 computed on real labels (the analysis
  code has run on synthetic data only).

**What existed when this revision was written (06:03 UTC onward; brought up to date between 08:18 and 08:35 UTC, at
about 09:15 UTC, between 14:07 and 14:36 UTC, and between 15:46 and 16:20 UTC).**

* Freeze 1 of the instruments exists (04:58:22 UTC). Gate VG-6 was opened after it and passed (04:59 UTC). Seen-creator
  production started at 05:00 UTC through the batch interface; several of its stages moved to the standard interface at
  06:33, 06:39 and 07:50 UTC, and it was complete at 11:10 UTC (registry row of 11:10: voice, asks, sentence codes and
  forecasts for the 1,293 English recordings of the 71 seen creators, titles for the 71). This revision opened none of its
  labels; it read the aggregate output of `run.py constants` (below). The known-answer battery (constructed texts) was
  reported complete at 09:10 UTC.
* The seen feature files were written again for H9's token rule as features-3 (11:20:46 to 11:22:20 UTC) and features-4
  (13:01:12 to 13:02:48 UTC), from seen transcripts only (private features note). The seen-only path of 06:44 (1) was run
  on the production seen tree at 14:00:03 to 14:00:37 UTC (`run.py constants`, exit 0): it printed the three freeze-2
  constants and the A10.7 null means, as counts and derived numbers only, and the constants were entered in
  `constants.py` (Part 4).
* Freeze 2 has not been made. Its one record, `llm/freeze2.json` (decision of 06:44 (2)), did not exist at 08:19, 08:34,
  09:04, 09:05, 09:17, 14:10:38, 14:37:35, 14:48:41, 15:47:24, 15:49:31 or 16:04:08 UTC (`run.py hashes`; file checks), so the hypothesis code's ordinary loaders refuse
  every real label file, and the freeze-1 entry allows hold-out labels only after freeze 2. No hold-out label and no
  registered quantity of H1, H2 or H4 to H10 exists.
* The registry row of 15:14 UTC (commit 15:14:55 UTC) amends freeze 1 for a hold-out feature step in produce.py and
  settles points of this text. produce.py held the new `features` command when read at about 15:48 UTC (file last
  written at 15:41:50 UTC; its SHA-256 no longer the `60bd9f62...` that freeze 1 holds for it); freeze.json was still
  the record of 04:58:22 UTC (`frozen_utc` 2026-11-21T04:58:22Z, file unchanged since then) at 15:47:24 and 16:04:08
  UTC. The
  hypothesis code was committed at 15:16:44 UTC (`c8f1f73`) and given LF
  line endings at 15:17:18 UTC (`c08c2a8`), which rewrote four of its modules (`constants.py`, `features.py`, `run.py`,
  `simulate.py`, last written 15:17:17 UTC) and changed the task fingerprint from `908111b94170` to `32757fe34057` and
  the constants file's SHA-256 from `c079dbf8...` to `cf544528...`; the three freeze-2 constants keep the values entered
  at 14:10 UTC, and `features.py` differs from the bytes of the features-4 run only in its line endings.
* The decisions written in here were taken at 04:55 UTC (commit 04:55:07 UTC), before freeze 1 and before any
  first-round label; at 06:44 and 09:19 UTC (commits 06:44:05 and 09:19:46 UTC), after freeze 1 and while seen production
  was running; at 11:08 UTC (commit 11:08:52), two minutes before seen production was reported complete; and at 12:52 UTC
  (commit 12:52:07), after it. All were taken before freeze 2, before any hold-out label and before the freeze-2 constants
  and the null means were computed on seen labels (14:00 UTC). Each of these rows states that none of its decisions uses
  a first-round or hold-out label. The decisions of 15:14 UTC (commit 15:14:55) were taken before freeze 2 and any
  hold-out label but after the freeze-2 constants and the null means had been computed on seen labels; two of its
  points cite values computed on seen labels (H4's yardstick with and without its minimum, and the null mean of H6's
  registered version).

**Where each part goes (suggestion).** Part 1 into "Amendments made by that instruction", after the paragraph
"Primary definitions for H1, H4 and H6", so that the numbers run A9, A10, A11; its heading carries its own date so
that a reader sees it was written after A11. Parts 2 to 7 directly after A10. Part 8 as a new section "Deviations from
the frozen registry" before "Procedure freeze", and as the appendix table of the paper (review item D6). The
section "Notes for the lead" at the end is not for pasting.

---

## Part 1. Amendment A10

**A10. The stricter amendments approved in principle under A9, entered 2026-11-21 (decision of 03:08 UTC) from the
calibration item's drafts, before freeze 1 and before any first-round label.** A9 approved these amendments in
principle and asked for their exact text before freeze 2. They come from the calibration item (CAL) of the
second-round panel, whose drafts are numbered A8 to A14. The registry's A8, A9 and A11 already exist, so the drafts
are entered here as A10.1 to A10.7: A10.k is CAL's A(7 + k), in order (CAL's A8 is A10.1, and so on to CAL's A14,
which is A10.7). The same numbering is used in the analysis code and its README. Every part was first written after
H3's hold-out result and CAL's calibration on seen creators were known, and before freeze 1, before any first-round
production label on any creator, and before any label of a hold-out creator. The corrections decided at 04:55 UTC
(decisions (c), (d), (g), (i), (j), (k), (l) and (m) of that row) were also taken before freeze 1 and before any
first-round label, and each one either follows the registered text or makes a verdict harder to reach. The
corrections decided at 06:44 UTC (decisions (3), (4), (5) and (9) of that row) were taken after freeze 1, while
seen-creator production was running, and before freeze 2 and any hold-out label; that row states that none of them
uses a first-round or hold-out label. (4) takes the reading the registered text gives, (5) makes a verdict harder to
reach, (3) changes the amended version of H6 and so falls under the guard, and (9) changes one sensitivity row of H5
in both versions. The wording that enters them was written after freeze 1 and after seen-creator production
had started (05:00 UTC), and uses no label. The corrections decided at 09:19, 11:08 and 12:52 UTC (H6's reference:
09:19 (1), 11:08 (1), 12:52 (1); the A10.7 check: 09:19 (2) and (3); the counting of asks: 12:52 (2)) were taken before
freeze 2 and any hold-out label, while seen production was running (09:19), two minutes before it was reported complete
(11:08) or after (12:52, seen production complete at 11:10 UTC), and before any freeze-2 constant or null mean was
computed on seen labels (14:00 UTC); each row states that none of its decisions uses a first-round or
hold-out label. Since 11:08 (1) H6's amended p is never below the sign-flip p that A10.4 drafted, so these corrections
make the amended version's verdict harder to reach, not easier; 09:19 (2) tightens a check; 12:52 (2) changes what both
versions of H6 count, alike: it removes a double count in the output of the frozen ask instrument, the guard compares
the two versions on the same merged asks and so does not cover it, and its direction is not known in advance (Part 8).
Decision (2) of 15:14 UTC classes it so: a counting correction in both versions of H6, outside the guard. The same
decision settles how other parts of this text and its companions read (A10.2, A10.4, A10.7 point 3, the guard, Parts
2, 4 and 6); it was taken before freeze 2 and any hold-out label, after the freeze-2 constants and the null means had
been computed on seen labels (14:00 UTC), and Part 8 gives the direction of each of its points.
Apart from that counting correction, each part either can only make a verdict harder to reach or falls under the
guard at the end of this amendment. A10 becomes final
at freeze 2 at the latest. Until then its text may be corrected, but no correction may make a verdict easier to reach
(A9). Nothing in A10 says whether any hypothesis is true.

**A10.1. The p-value that enters Holm is creator-level, and the count is fixed at 10.** For H1, H2, H4 to H7, H9
and H10.

* For each hypothesis, the p-value that enters Holm comes from a test on creator values. Up to 20 creators a sign-flip
  p is computed by exact enumeration of every sign pattern. Above 20 it is a Monte Carlo test with 99,999 draws and
  p = (b + 1)/(B + 1), where b counts the draws at least as extreme as the observed value and B is the number of draws.
  Enumeration gives the exact p of the sign-flip distribution. The test keeps its nominal level only where each
  creator's value is symmetric about zero under no effect; for the OE values of A10.4 that need not hold when T is
  small, so there the level is not guaranteed and can exceed nominal (A10.4). For H6 the sign-flip therefore does not
  decide alone (below; decisions of 11:08 (1) and 12:52 (1)).
  * H1: sign-flip of creator mean log rate ratios, one-sided (as registered).
  * H2: sign-flip of creator Somers' D, pooled within length bands, two-sided. It replaces the registered
    permutation of commitment codes within creator and length band.
  * H4: sign-flip of creator mean standardised drops, one-sided (as registered).
  * H5: sign-flip of the conditional differences (OE) of A10.4, one-sided.
  * H6: one-sided, of the mean OE of A10.4 over the creators with an ask: the larger of two p values, the cluster-level
    conditional Monte Carlo p (99,999 draws, p = (b + 1)/(B + 1)) and the creator sign-flip p of OE (exact up to 20
    creators). Both test the mean of the creator values, each creator counted once: the first draws the voice of every
    creator's asks again under no difference inside any recording, the second flips the signs of the creator values. The
    rule, its level figures (at most 0.42% at 0.005 in the constructed cases inside the 5-unit window, against up to
    3.27% for the sign-flip alone) and its stated limit (dependence of asks beyond the window is not modelled) are in
    A10.4.
  * H7: sign-flip of the creator differences of A10.6, one-sided. It replaces the registered permutation of upload
    dates.
  * H9: as registered (family labels permuted across creators within family size), which is already creator-level.
  * H10: sign-flip of creator risk differences, two-sided (as registered).
* Within-creator references are printed as secondary rows and never enter Holm: H2's permutation within creator and
  band, H7's date permutation, and H3's circular shift.
* Holm runs over m = 10. H3 (closed, A6) and H8 (dropped, A9) enter as run with p = 1. A hypothesis that is not run
  (H7, which needs the replication wave, and no wave exists: A4 and decision of 04:55 (h); H10, not run in the first
  round: decision of 04:55 (m)), not determinable (A10.2) or
  without an instrument (A10.5) enters with p = 1. Holm is monotone in the p-values, so a verdict given early is not
  revoked by a later one.
* Every interval printed with a verdict is an unadjusted companion. A5 stays: "supported" also needs the 90% interval
  over creators to exclude zero, by the procedures of A10.7; for the amended versions of H5 and H6, both the t interval
  on the creator OE values and the interval of the Mantel-Haenszel estimate must exclude it (A10.4; decision of 06:44
  (5)). Each hypothesis keeps its registered effect-size condition. Refutation and equivalence statements read from
  intervals are labelled "unadjusted".
* *Why.* CAL tested the references under a creator-level placebo on seen creators, which keeps each creator's habits
  and sets the population effect to zero. Under it, the registered recording-level references of H3 and of an H2
  analogue rejected more than twice as often as their nominal level at the first Holm step, at the creator counts the
  hold-out can give (8 to 17). CAL's rule ("more than twice nominal is amended
  before the freeze") therefore fails for both. The creator sign-flip on the same placebo data stayed close to
  nominal. The registered text already set its thresholds for the strictest case, all ten run; fixing m at 10 makes
  that case the rule. CAL's figures stay in the panel's private record until the paper prints them in its
  calibration table (review item R2).

**A10.2. The outcome "not determinable: too few eligible creators".** For H1, H2, H4 to H7, H9 and H10.

* Before freeze 2, each hypothesis prints three things: its eligibility rule; its minimum number of creators; and its
  detectable effect at the projected number of eligible creators, taken from the label-based repeat of the
  calibration (CAL part f). H6's detectable effect comes instead from the power of the full simulation battery on
  synthetic creators (11:08 (1)); the full battery runs on the frozen code after freeze 2 and fills H6's
  detectable-effect note (decision of 15:14 (2)).
* The test sets a lower limit: the smallest number of creators at which an exact sign-flip can pass the first Holm
  step (0.005). That is 8 for a one-sided test (2^-8 = 0.0039) and 9 for a two-sided test (2 x 2^-9 = 0.0039; with 8
  creators the smallest two-sided p is 0.0078). The registry's stricter minimums stay, and the larger minimum
  applies:

  | | Minimum eligible creators |
  |---|---|
  | H1, H4 | 12 with both voices (registered) |
  | H2 | 9 with 30 verified statements (A10.3) |
  | H5 | 12 (registered) |
  | H6 | 12 with both voices (registered), and 8 with at least one ask (A10.4) |
  | H7 | 8 (one-sided) |
  | H9 | 8 (one-sided), and a family-label permutation whose smallest p can reach 0.005 |
  | H10 | 15, with at least 50 matured statements among them (registered: "at least 50 matured statements from 15 creators") |

* The eligible count is made by code that reads labels only, after every exclusion (the recognizer rule, the
  exclusion of creators without asks in A10.4). It is written to a file before any outcome is computed.
* Below its minimum, a hypothesis is not run as a test. It enters Holm with p = 1. Its row reads "not determinable:
  too few eligible creators (k of m)", and its estimate and interval are shown as description. Under the guard, a
  result is "not determinable" as soon as either version is (guard, decision of 04:55 (g)).
* At or above its minimum, if the detectable effect exceeds 1.5 times the smallest effect of interest, the row reads
  "run; detectable only from X (Y times the smallest effect of interest)". The hold-out robustness rows HR (b) and
  (c) are then not bought for that hypothesis.
* Announced in advance (registry, 02:50 UTC): H1, H4 and H6 are probably not determinable at their projected
  eligible counts (median 5, 3 and 5 creators against 12).
* *Why.* With fewer than 8 creators (one-sided) or 9 (two-sided), no exact sign-flip can pass the first Holm step. One
  creator below the minimum, its smallest p (0.0078) could pass Holm only at the fifth step, after four other
  hypotheses had been rejected; two creators below (0.0156), not at all in the first round, where H3, H7, H8 and H10
  hold p = 1 and so no hypothesis can reach a step beyond the sixth (threshold 0.01). A test run there would in practice end in "not
  supported", and a reader would take that as evidence against the hypothesis.
  The outcome adds a condition, so it can only make a verdict harder to reach.

**A10.3. H2's minimum is 9 creators with 30 verified statements, not 8.** For H2.

* Registered: "not run below 8 creators with 30 validated statements". Amended: 9. Under A8, "validated" is read as
  "passed the instrument's verification step (model-coded)".
* *Why.* H2 is two-sided, and its Holm p is the creator sign-flip of A10.1. With 8 creators the smallest two-sided p
  is 2/256 = 0.0078, above the first Holm step.

**A10.4. Conditional estimators for H6 and H5, with a minimum on the margin only.** For H5 and H6.

* **H6.** For each creator with both voices and each of its eligible recordings i: a_i = asks to buy or enrol in
  claimed-voice spans, b_i = the same in own-voice spans, T_i = a_i + b_i, s_i = the claimed voice's share of the
  recording's words in the two voices (claimed and own); a, b and T are the sums over the creator's eligible recordings.
  Asks of one class whose unit ranges overlap are counted once (decision of 12:52 (2)): the find is the union of two
  draws, which can return one ask twice with different ranges; the instrument is frozen and unchanged, and the analysis
  merges such asks, in both versions of H6, before anything is counted. The merge is a counting correction in both
  versions, outside the guard (decision of 15:14 (2)).
  * Creators with T = 0 are excluded and counted.
  * The statistic: the mean, over creators with T of 1 or more, of OE = (a - sum over i of T_i s_i)/T, centred per
    recording (decision of 06:44 (3)). Given the T_i, its mean under no difference inside any recording is zero,
    whatever the recordings' ask rates. With one eligible recording it is a/T - s, the form of CAL's draft. CAL's draft
    summed a and b and took s over a creator's recordings together; that form is not centred when ask rates differ
    between recordings with different claimed shares: a creator who asks more often in recordings with less claimed
    voice has a/T below s with no difference inside any recording, in H6's predicted direction.
  * Holm p (decisions of 11:08 (1) and 12:52 (1), which replace the reference of 09:19 (1)): one-sided, the larger of two
    p-values of that mean.
    * The cluster-level conditional Monte Carlo p. A recording's asks are grouped into clusters: taken in the order of
      their units (sentences), an ask joins the cluster before it when its first unit is at most 5 units after the
      cluster's last unit, so asks within 5 units of each other (about one minute of speech) chain into one cluster.
      Under the null each cluster is in the claimed voice with the recording's claimed share s_i, all its asks with it,
      independently between clusters, given the clusters. p = (b + 1)/(B + 1) with B = 99,999 draws from a stream
      seeded by the result's label, so the p is reproducible; inside about 0.0045 to 0.0055 the side of 0.005 still
      depends on the draws (correction in the 12:52 row).
    * The creator sign-flip p of OE, computed by exact enumeration up to 20 creators (A10.1).
  * *Why two.* OE's distribution under no effect need not be symmetric about zero: for small T and shares far from one
    half it is skewed, so the sign-flip is not a test of exact level. In CAL's simulation of H6 with no true effect (of
    its own form) it stayed close to nominal and was above it at 17 creators: 0.67% against 0.5% at the first Holm step
    (600 sets; Monte Carlo SE about 0.29 points, so the excess is within Monte Carlo error). By exact enumeration on
    constructed numbers it exceeds nominal where creators have one or two asks in recordings whose claimed share is well
    below one half: 17 creators each with one ask at a claimed share of 0.3 give 1.93% rejections at 0.005 with no
    effect. A reference that draws asks one by one (a_i from Bin(T_i, s_i), the reference of 09:19 (1)) removes that
    excess but over-rejects when the asks come in bursts in one voice: 7.74% at 0.005 for 17 creators with one burst of
    3 asks at s = 0.3. The cluster-level p holds its level wherever the cluster rule finds the bursts, and the larger of
    the two p-values falls below a threshold only when both do, so neither failure can carry a verdict alone. Where the
    asks of a burst lie two or more units apart, 11:08's rule (the same, overlapping or adjacent units) saw separate
    clusters: a burst of 3 asks 2 units apart at s = 0.3 (17 creators) then gave 1.93% at 0.005 for the larger p as
    well; 12:52 (1) widened the window to 5 units, which gives 0.23%.
  * *Level figures* (exact enumeration on constructed numbers; no generator and no label; `sim_out/h6-cluster-reference-
    levels.md` and its `.json`, stamped 13:13:58 UTC and last written at 13:33:27 UTC, on the code of 12:52, task
    fingerprint `d97db4a2a7c4`). In the 27 constructed cases inside the window (one or more
    bursts of 2 to 4 asks at shares 0.3 to 0.7, bursts whose asks lie 1 to 3 units apart at shares 0.3 to 0.5, single
    asks at shares 0.2 to 0.6, 12 and 17 creators) the larger p rejects in at most 0.42% of sets at 0.005 and 4.76% at
    0.05 with the analysis's 99,999 draws (0.40% and 4.48% with the battery's 9,999); the sign-flip alone rejects in
    more than 0.5% of sets at 0.005 in 17 of the 27 cases (up to 3.27%), and the ask-by-ask reference in 16 (up to
    10.28%). On synthetic creators through
    the battery's code path (1,000 sets a row, 9,999 draws, Monte Carlo SE about 0.22 points at 0.005), the larger p
    rejects at 0.005 in 0.4% (12 creators) and 0.3% (17) of the sets with one gapped burst a creator at claimed shares
    below one half, against 1.5% and 0.9% under 11:08's clusters; in 0.4% with bursts on consecutive units (17 creators),
    against 5.0% for the ask-by-ask reference; and in 0.1% with one to three single asks a creator at shares below one
    half (17 creators), against 0.6% for the sign-flip alone.
  * *Stated limit.* Dependence of asks beyond the window is not modelled, and every H6 result says so. A burst whose asks
    lie more than 5 units apart is seen as several clusters, and at claimed shares below one half both p-values then
    over-reject: 17 creators with one burst of 3 asks 6 units apart at s = 0.3 give 1.93% at 0.005 for the larger p (as
    for the sign-flip alone). A sensitivity row computes the same p with a 10-unit window (0.23% in that case) and
    carries no verdict.
  * The ask-by-ask conditional p of 09:19 (1) is printed beside the larger p and enters nothing.
  * Estimate: the Mantel-Haenszel rate ratio over the same creators, with one stratum per creator and recording
    (06:44 (3)). It carries the wider of two 90% (and 95%) intervals, element by element (lower bound the smaller of the
    two lower bounds, upper bound the larger of the two upper bounds): the creator-bootstrap percentile interval and the
    t interval (decision of 04:55 (j)). The label-based coverage repeat (CAL part f) that could have chosen between them
    has not run, so the interval stays the wider one (decision of 15:14 (2)). The code reads the t interval of a
    Mantel-Haenszel estimate as its log plus or minus t(k - 1) times the delete-one-creator jackknife standard error (a
    creator is deleted, and drawn by the bootstrap, with all its recordings), and holds the rule in one constant, set to
    the wider interval. That interval decides the refutations and the "uninformative" flag. A5 holds only if
    both the t interval on the creator OE values and that interval exclude zero on the predicted side (06:44 (5)).
  * The registered log rate ratio with the half-count correction becomes a sensitivity row. Per-creator log ratios
    are shown only for creators with T of 5 or more, and only in private files.
  * Any minimum on hits is set on T, never on a or b. The run condition is 8 or more creators with T of 1 or more,
    in addition to the registered 12 creators with both voices.
  * The registered verdict conditions stay: "does not sell" needs a ratio of 0.5 or lower; refuted by an interval
    inside 0.67 to 1.5, or by a ratio above 1.
* **H5.** For each creator: world-claim hits (w) and practice hits (p) in recordings titled as channelled or relayed
  (group A) and in own-voice talks (group B), with T_A = w_A + p_A and T_B = w_B + p_B.
  * Holm p: one-sided sign-flip over creators of OE = w_A/T_A - (w_A + w_B)/(T_A + T_B); as for H6's OE, an
    enumeration, not a test of exact level (H6 adds a second p, above; H5 keeps the sign-flip alone). In the
    recognizer-model-stratified row OE is centred within each model (Part 6).
  * Estimate: the Mantel-Haenszel odds ratio across creators (one stratum per creator; per creator and model in the
    model-stratified row), carrying the wider interval as for H6 (04:55 (j)). That interval decides the refutations
    and the "uninformative" flag; A5 holds only if both the t interval on the creator OE values and that interval
    exclude zero on the predicted side (06:44 (5)).
  * Minimum: 10 hits per group (T_A and T_B each 10 or more), in place of the registered 10 hits per group and side.
    The registered per-side rule is reported as a row.
  * The exclusions of the 02:50 UTC revision (units next to a self-naming cue) are applied before the hits are
    counted (Part 7).
* *Why.* CAL simulated H6 with no true effect at the pilot's sparse ask rates. The registered half-count log ratio
  was biased in H6's predicted direction, and its sign-flip rejected more often than nominal. OE has mean zero under
  no effect by construction (for H6 in the per-recording form of 06:44 (3), given the T_i, whatever the recordings'
  ask rates), and its sign-flip, in the form CAL simulated, stayed near nominal (for H6's level with few asks and
  with bursts, see its Holm p above). A minimum on each side selects
  creators on the outcome. CAL's draft argued, but did not simulate, that the margin-only rule keeps H5's OE centred.
  CAL's coverage audit found the creators-only percentile interval below its nominal level and the t interval closest
  to it, so the interval takes the wider of the two rather than the percentile interval alone.
* The margin-only minimum admits more creators than the registered rule, and OE replaces a registered statistic.
  The guard therefore applies to both hypotheses. The centring per recording (06:44 (3)) and the reference of 11:08 (1)
  and 12:52 (1) change only the amended version of H6; the registered version is computed as registered beside it.
  The counting of overlapping asks once (12:52 (2)) applies to both versions alike, so the guard compares them on the
  same asks; it is a counting correction outside the guard (15:14 (2)).

**A10.5. The gate rule for agreement.** For every instrument that feeds a registered test (voice, asks, forecasts,
sentence codes, titles).

* A gate passes if the point estimate is at least the floor and the lower end of the 90% bootstrap interval is at
  least the floor minus 0.10. The bootstrap resamples creators, then recordings, with 2,000 draws.
* Per-creator and per-format agreement are printed. Formats that leave the eligible set when they are below the
  floor are declared before the gate is run.
* The floors stay as set (annotation plan section 6, decision 6, taken at 01:15 UTC under the owner's delegation).
  An instrument still below a floor after the one revision that plan 3.4 allows is not used for the registered
  test. Its hypothesis is entered as "not run for want of an instrument" and counts in Holm with p = 1.
* Exception: the owner's decisions of about 00:30 UTC on the checkability parts of H2 and the title codes of H5 and
  H9 stand as made. Those instruments are reported with their failed gates and their adjudication figures. The
  exception is not extended to any other instrument.
* *Why.* The registered rules ("kappa at least 0.6" and the like) read the point estimate alone. CAL simulated three
  rules at the pilot's spread: the point estimate alone, the lower bound alone, and both together. The lower bound
  alone fails many good instruments. The combined rule screens out poor instruments at least as well as the point
  estimate alone. It adds a condition to the registered rule, so it cannot pass an instrument that the registered
  rule fails.

**A10.6. H7's estimator, reference and margin.** For H7, which needs the replication wave. No wave exists (downloads
closed on 2026-11-20), so H7 is not run in the first round (A4; decision of 04:55 (h)).

* *Estimator.* The anchor-matched contrast: recordings uploaded within 3 days of each other minus recordings 14 to 60
  days apart.
  * For each anchor recording and each other creator, take the mean cosine to that creator's near recordings minus
    the mean cosine to its far recordings.
  * Average over partner creators, then over the anchor creator's anchors, then with equal weight over creators.
  * Compute this separately for anchors in weeks with an almanac-listed date and in other weeks. The estimand is the
    creator-balanced difference between the two.
* *Text representation.* TSIM v1: sublinear TF-IDF with document frequencies from seen recordings, l2 norm and cosine,
  with names and the calendar lexicon masked. It is fixed by hash before the wave is collected. It specifies the
  registered "TF-IDF cosine" with names masked and calendar words removed.
* *Reference.* The Holm p is the creator sign-flip of A10.1. Two secondary bands are printed: the registered
  permutation of upload dates among each creator's own recordings (G), and the block reference L, which permutes
  dates inside each creator's 28-day blocks (9,999 draws). The leave-one-date-out range stays mandatory.
* *Margin.* k x SD_L, where SD_L is the standard deviation of the primary estimand under L on seen creators. SD_L and
  k are fixed and entered here before any wave recording is collected; k is not fixed now. This sets the registered
  placeholder (0.01) under the registry's rule that placeholders are "set from the seen creators before their
  tests". When H7 is run, its verdict must hold against both margins, the placeholder 0.01 and k x SD_L, and stands
  only if both give it (decision of 04:55 (i)). H7 is not coded; the rule is written in the code's README.
* The near-against-far contrast S is reported as description with its L band and is not tested (as registered).
* *Why.* The placeholder 0.01 is not in the units of the estimand's own spread under no effect. A margin taken from
  the estimand's own reference distribution on seen creators can be fixed before the wave without seeing any wave
  data. A much smaller margin would make an excess above the margin easier to show, so the verdict is held to both
  margins. The date permutation is a within-creator reference; under A10.1 it becomes a band, and the creator
  sign-flip is the test.
* The estimator and the reference replace registered ones, so the guard applies.

**A10.7. Interval procedures and centring.** For H1, H2, H4, H5, H6, H7 and H10.

1. Where the estimand is a mean of creator values (the OE means of H5 and H6, H10's risk difference), the interval
   is the t interval on creator values, with k - 1 degrees of freedom. H1, H2 and H4 register a random-effects pool;
   for them A5 reads the pool's 90% interval by item 2, and the t interval on the creator values (creator means; for
   H2 the creators' D) is printed beside it. For H5 and H6, whose estimate is a Mantel-Haenszel ratio, A5 needs both
   the t interval on the OE values and the interval the ratio carries (A10.4; 06:44 (5)). The two-stage bootstrap of
   rule R1 (creators, then recordings) is kept as a sensitivity row of H1 and H4. For H2, H5 and H6 the registered
   version's own "creator-bootstrap interval" is drawn creators then recordings, as R1 says (decision of 04:55 (d); see
   the guard). H9's creator-bootstrap interval, which A10 does not replace, is drawn the same way in both of its
   versions: creators (hold-out and seen apart), then recordings within each cell, with every cell re-rarefied in every
   draw (06:44 (4)).
2. Random-effects pools of the amended versions (H1, H2 and H4) and H5's random-effects sensitivity row use the
   Hartung-Knapp-Sidik-Jonkman interval with t(k - 1), not DerSimonian-Laird with a normal interval. H5's row is the
   registered half-count estimator pooled this way, with its prediction interval and the sign-flip of A10.1; it is an
   estimate without a verdict (decision of 04:55 (c)). The registered version that the guard
   computes beside each of them, H5's included, keeps DerSimonian-Laird with a normal interval (note a). The
   prediction interval for a new creator is printed as registered.
3. Every log-ratio estimand must show, on seen creators, a mean of zero under its own reference, or be recentred on
   it. It must also report how well it recovers a planted effect of the smallest size of interest. The null-mean
   check runs on seen labels before freeze 2 and is printed. The recovery check was to run on seen labels as well (CAL
   part f); CAL part (f) has not run, and the simulation battery on synthetic creators stands in for it (decision of
   15:14 (2)): recovery is reported from the full battery, which runs on the frozen code after freeze 2.
   * Before freeze 2 the hypothesis code reaches seen labels only through the seen-only path (decision of 06:44 (1);
     Part 4). Its command `run.py constants` prints the null-mean check beside the freeze-2 constants, from seen
     labels, as counts and means only: computed for both versions of H5 and H6 and for H2's registered version (the
     mean of its within-creator permutation reference), and stated as zero by construction for the sign-flips of H1,
     H4 and H2's amended version (H9's reference mean is reported with every H9 result). The analysis computes the
     check again on the seen creators of its primary source and writes it into the report's metadata.
   * The check ran on seen labels at 14:00:03 to 14:00:37 UTC, after the decisions of 12:52 (`run.py constants`, 999
     draws; 1,284 seen recordings of 71 creators under the recognizer rule; a verifier's rerun at 14:39:26 to 14:40:01
     UTC printed the same values). Every version that the check computes
     was "centred" except H6's registered half-count version: null mean -0.137 against a tolerance of 0.069 (48
     creators with both voices),
     "recentring needed", as expected from its form; it stays uncentred under the guard (04:55 (k), confirmed with this
     value at 15:14 (2)). H6's amended OE has
     null mean 0 (exactly, by construction).
   * The code's planted check covers H6 (the expected values at a rate ratio of 0.5, at the seen margins). Recovery of
     a planted effect by the other estimands is measured by the simulation battery on synthetic creators, which stands
     in for CAL part (f) on seen labels (15:14 (2)). The Mantel-Haenszel estimates of H5 and H6 keep the wider of their
     two intervals, since no coverage repeat on seen labels has chosen between them (04:55 (j); 15:14 (2); A10.4).
   * The registered versions under the guard are not recentred. In particular H6's registered half-count version
     stays uncentred, and its null mean on seen creators is reported (decisions of 04:55 (k) and 15:14 (2)); the code writes it
     into the report's metadata with the other null means and marks a version "recentring needed" when it is off
     zero by more than a tenth of its smallest effect on its own scale (decision of 09:19 (2)): the log-scale smallest
     effect for the registered versions; for the OE versions of H5 and H6, the OE value of the smallest effect at the
     seen creators' counts and shares (for H6 about -0.17 at shares near one half, so a tolerance of about 0.017; for
     H5 about 0.05 at even sides; 0.1 on the share scale stood before 09:19). Under the guard a verdict needs both
     versions, so a registered version biased toward support cannot create a verdict; it can only remove one.
   * The check covers H6's amended OE in its per-recording form (06:44 (3)) under the null of its reference (11:08 (1),
     12:52 (1)): each cluster of a recording's asks (asks within 5 units of each other) is placed on the claimed side with
     probability s_i, all its asks with it, given the clusters. The OE's mean is zero by construction under it, as under
     the ask-by-ask null of 09:19. The pooled form of CAL's draft is printed beside it; the registered version's
     expectation is taken over the clusters' law, with the ask-by-ask value beside it. Asks of one class on overlapping
     unit ranges are counted once (12:52 (2)), and recordings without an ask file are kept with no asks, as the analysis
     keeps them (09:19 (3)). The level of the reference itself is in A10.4: under this null, in the 27 constructed cases
     inside the window, H6's amended p (the larger of the cluster p and the sign-flip p) rejects in at most 0.42% of sets
     at 0.005 and 4.76% at 0.05; beyond the window, where the null of the check and of the reference is not the data's,
     it is not held (1.93% at 0.005 in the constructed case of A10.4), and the result says so.
   * Example, H3 (exploratory, A6): the registered U has a mean of -0.063 under its own reference (A9). Recentred,
     its seen value moves from 0.019 to 0.083. H3's registered verdict is not changed by this.

* *Why.* CAL audited interval coverage on seen creators at 12 and 17 creators, and the t interval on creator means
  came closest to its nominal level. In the same audit Hartung-Knapp-Sidik-Jonkman intervals came closer to their
  nominal level than DerSimonian-Laird intervals, and under the creator placebo DerSimonian-Laird intervals excluded
  zero more often than nominal. An estimand whose mean under no
  effect is not zero can pass or fail for that reason alone, as H3's does.
* Recentring and a new interval can move a result toward support, as H3's seen value shows. The guard therefore
  applies wherever this part replaces a registered interval or centring.

**Guard (2026-11-21, 03:08 UTC; completed at 04:55 UTC; applied at 06:44, 11:08, 12:52 and 15:14 UTC).** Wherever A10 replaces a registered
estimator, reference, minimum, interval or centring, both versions are computed on the same data:

* the registered version, as written in [`hypotheses.md`](hypotheses.md) and this registry, each with the interval
  that hypotheses.md registers for that hypothesis (decision of 04:55 (d));
* the amended version.

The larger of the two p-values enters Holm. A verdict, "supported (model-coded)" or "refuted (model-coded)", stands
only if both versions give it; otherwise the row reads "not determined: the registered and the amended versions
differ". Where a verdict rests on an interval (for example H1's upper 95% bound below 0.95), the interval of each
version must meet the condition. A version that cannot be run, for example because its minimum is not met, has p = 1.
If either version is not determinable, the result is "not determinable", with the reason naming the version (for
example "not determinable in the amended version: too few eligible creators (8 of 9)"), and it is flagged
uninformative (decision of 04:55 (g)); "versions differ" is kept for two determinable versions that disagree. Both
versions are printed. The guard is needed because some replacements can move a result toward support: recentring
moved H3's seen value from 0.019 to 0.083, and the margin-only minimum of A10.4 admits more creators than the
registered rule.

The decisions of 06:44 UTC keep this rule and say how it applies:

* H6's registered version stays as registered (uncentred, 04:55 (k)) beside the amended version, whose OE and
  Mantel-Haenszel ratio are centred per recording ((3); A10.4).
* Where A10 replaces no interval (H9), both versions carry the same interval, drawn creators, then recordings, as R1
  says ((4); A10.7).
* The amended versions of H5 and H6 meet A5 only if both the t interval on the creator OE values and the wider
  Mantel-Haenszel interval exclude zero ((5)); their registered versions keep the interval they register.
* The revisions of meta-review M9 (Part 7) change what is measured, not an estimator, reference, minimum, interval or
  centring, and are not under the guard; the rows without them are reported beside each primary with their own
  verdicts ((7)).

The decisions of 11:08 and 12:52 UTC keep the rule as well:

* H6's amended p is itself the larger of two p-values, the cluster-level conditional p and the sign-flip p of OE (11:08
  (1), with the 5-unit clusters of 12:52 (1); A10.4). The guard then takes the larger of that p and the registered p, so
  H6's p in Holm is the largest of three, and a verdict still needs both versions. The registered version keeps its
  sign-flip of half-count log ratios; the 10-unit sensitivity row and the statement that dependence beyond the window is
  not modelled belong to the amended version.
* Asks of one class on overlapping unit ranges are counted once in both versions of H6 (12:52 (2)); it corrects a
  count, not an estimator, reference, minimum, interval or centring, and the guard compares the two versions on the
  same asks. The decision of 15:14 (2) classes it as a counting correction in both versions, outside the guard.
* H9's token rule (11:08 (2) and (3), 12:52 (3) and (5): every token of every family variant kept out of the content
  words, contractions whose parts are function words counted as function words, ain't and y'all among them) changes what is measured in both versions
  alike: both read the same feature files, of one feature version per analysis (12:52 (4)). Like the M9 revisions it
  replaces no estimator, reference, minimum, interval or centring, so the guard has no second version of it to compute.

The decisions of 15:14 UTC keep the rule as well:

* H6's registered version stays as registered under the guard: the half-count log rate ratio, uncentred, beside the
  amended version (15:14 (2), confirming 04:55 (k)). Its null mean on seen creators is -0.137 against a tolerance of
  0.069, so the code marks it "recentring needed" and does not recentre it (A10.7 point 3). Because a verdict needs
  both versions, that bias can remove a verdict of H6 but cannot create one.
* The interval of the amended versions' Mantel-Haenszel estimates stays the wider of two (15:14 (2); A10.4); the
  registered versions keep the interval they register.

| | Registered version, computed beside the amended one | Amended version (A10) | Replaced, so the guard applies |
|---|---|---|---|
| H1 | sign-flip of creator mean log rate ratios; random-effects pool as first read (note a), with its 95% and 90% intervals and 95% prediction interval; minimum 12. hypotheses.md registers the pool's 95% interval and prediction interval and no bootstrap for H1, and no registry row before 2026-11-21 registers one; catalogue rule R1 says how to resample where a bootstrap is used and does not add one. The registered H1 version therefore checks the pool's intervals, as coded, and R1's two-stage bootstrap is H1's sensitivity row, not checked by the guard (decision of 04:55 (d)) | the same sign-flip and minimum; HKSJ pool, whose 90% interval A5 reads; t interval on creator means printed; null-mean check | interval |
| H2 | commitment codes permuted within creator and length band (9,999 draws), two-sided; random-effects pool (note a); creator-bootstrap 90% interval of the pooled D, drawn creators then recordings (R1; 04:55 (d)); minimum 8 | two-sided sign-flip of creator D; HKSJ pool, whose 90% interval A5 reads; minimum 9 | reference, interval, minimum |
| H4 | sign-flip of creator mean standardised drops; random-effects pool (note a) with its 95% interval and prediction interval; minimum 12; embodied voice (V2) | the same sign-flip, minimum and voice (V2; 04:55 (a)); HKSJ pool, whose 90% interval A5 reads; t interval on creator means printed | interval |
| H5 | sign-flip (9,999 draws) of creator differences of half-count log ratios; 10 hits per group and side; random-effects pool (note a); creator-bootstrap interval of the pooled estimate, drawn creators then recordings within each side (R1; 04:55 (d)); in the model-stratified row a creator's value is the inverse-variance mean of its per-model values (06:44 (9)) | one-sided sign-flip of OE; Mantel-Haenszel odds ratio with the wider interval (A10.4); 10 hits per group; for A5 both the t interval on OE and the wider Mantel-Haenszel interval (06:44 (5)); HKSJ random-effects row without a verdict; in the model-stratified row, strata creator by model (06:44 (9)) | estimator, reference statistic, minimum, interval |
| H6 | sign-flip of creator log rate ratios with the half-count correction over every creator with both voices (T = 0 included, as registered, and uncentred: 04:55 (k)); creator-bootstrap interval, drawn creators then recordings (R1; 04:55 (d)); minimum 12 with both voices; overlapping asks of one class counted once (12:52 (2)) | one-sided, over creators with an ask, the mean of OE centred per recording (06:44 (3)), with p the larger of its cluster-level conditional Monte Carlo p (asks within 5 units chain into one cluster; 99,999 draws) and its sign-flip p (11:08 (1), 12:52 (1)); a 10-unit window as a sensitivity row; Mantel-Haenszel rate ratio with creator-by-recording strata and the wider interval (A10.4); minimum 12 with both voices and 8 with an ask; for A5 both the t interval on OE and the wider Mantel-Haenszel interval (06:44 (5)); overlapping asks counted once | estimator, reference statistic, minimum, interval |
| H7 | S in listed-date weeks minus other weeks; upload dates permuted within creator (9,999 draws); creator-bootstrap interval | anchor-matched contrast on TSIM v1; creator sign-flip; G and L bands. Not run in the first round | estimator, reference, interval (margin: note b) |
| H9 | family labels permuted across creators within family size (9,999 draws); creator-bootstrap interval, drawn creators (hold-out and seen apart), then recordings within each cell, every cell re-rarefied in every draw (R1; 06:44 (4)); no creator minimum beyond a reference whose smallest p can pass 0.005 | as registered, with the same interval and a minimum of 8 hold-out creators with a cell (A10.2) | minimum |
| H10 | sign-flip over creators (9,999 draws); creator-bootstrap interval | sign-flip by exact enumeration up to 20 creators; t interval on creator means. Not run in the first round (04:55 (m)) | interval |

*Note a.* The registered text says "random-effects meta-analysis" without naming an estimator. CAL read it as
DerSimonian-Laird with a normal interval, and that reading is the registered version here.
*Note b.* The margin is set under the registry's rule for placeholders (A10.6). The guard as decided at 03:08 UTC
does not name the margin; the decision of 04:55 (i) closes the gap: when H7 is run, its verdict must hold against
both margins.

---

## Part 2. Replacement of the human check in every rule that names it

**Replacement of the human check, 2026-11-21 (03:08 UTC), fixed before any hold-out label.** The owner chose no human
check (A8), and that stands. Some rules name a person's check: the second-round programme's item HUMAN, and the
registered steps "checked on HR". Without a substitute, each of those rules would either block the run or be skipped
without notice. Each is replaced as follows. No floor is lowered.

| Rule that named a person | Replaced by |
|---|---|
| Freeze 1 waits on HUMAN's gate: a person codes 200 voice units of the check creators, and accuracy on claimed against own voice must be at least 0.80 | Freeze 1 waits on four things: the gates of plan 3.4 under the rule of A10.5; the known-answer battery's pre-set rules; the three-reader adjudication figures (A11); and the blind read of 200 seen check units by a reader of another vendor (decision of 01:10 UTC; gate VG-6, whose meaning was fixed at 03:21 UTC) |
| HR (b, c): released per hypothesis only if "HUMAN passed", with CAL's two conditions | Released per hypothesis when four things hold. The instrument passed its gates at freeze 1. It meets its known-answer recovery rule. The other-vendor reader agrees on the collapsed contrast with kappa at least 0.60 and a lower 90% bound at least 0.50; the comparator is the stored majority of the OpenAI readers, as the protocol defines it, and the record model's row is printed beside it and decides nothing (03:21 UTC). CAL's two conditions hold: 9 or more eligible creators, and a detectable effect within 1.5 times the smallest effect of interest (A10.2). The release record carries `verification_passed` and `verification_basis` (decision of 02:50 UTC), not a field named after a human check |
| H6: "ask labels validated on HR's shared sample (kappa at least 0.6, F1 at least 0.6)" | Ask gates D and E; the known-answer asks; and the other-vendor reader's agreement on asks to pay or enrol |
| H1: "the syllable estimator checked on HR excerpts" | The registered rows of words per minute and letters per minute, printed beside the syllable rate |
| H4: "an HR check that hand and recognizer transcripts give the same contraction share in each voice" | Contraction agreement on the 36 bridge pairs: the two recognizer models compared with each other, model against model |
| Precision of patterns and word lists read by a person (rule R7; the programme's person-read precision) | Precision figures read "share confirmed by a model reader, not checked by a person" |

* *Wording.* Results read "supported (model-coded)" or "refuted (model-coded)", "verified by a third model, on
  known-answer texts and by a reader of another vendor". Never "validated".
* *What does not change.* A1's open human check stays open, and the sample design stays on file (A8). The person
  accuracy floor of HUMAN (0.80 against one person's coding) has no counterpart, because agreement between models is
  not accuracy (A1). None of the replacements is reported as accuracy.
* *The other-vendor read (gate VG-6), fixed at 03:21 UTC before its sealed figures are opened at freeze 1.* If it
  fails, H1, H4 and H6 carry the flag "readers of two vendors disagree (kappa k)", their verdicts are capped at "not
  determined", and the HR (b, c) money returns to the reserve. If it passes, it serves the HR (b, c) release rule
  above. This overrides the programme's rule that the fallback reader cannot pass HUMAN's gate; the lead took it under
  the owner's delegation. Own voice is compared under both definitions (broad for every reader, narrow for every
  reader).
* *Afterwards (registry, 04:59 UTC).* Freeze 1 was made at 04:58:22 UTC without waiting for the known-answer
  battery's last voice batches: the battery measures recovery on constructed text and cannot change the voice
  instrument, whose one revision is spent. This departs from the first row of the table above and is listed in Part
  8. Gate VG-6 was then opened with its seal verified and passed: kappa 0.91 (90% creator-bootstrap interval 0.84 to
  0.95) on the claimed, own and other contrast, and 0.91 (0.83 to 0.96) on the embodied contrast that H4 uses. By
  the rule of 03:21 no vendor flag applies to H1, H4 and H6, and VG-6 meets its part of the HR (b, c) release rule.
  The known-answer battery was reported complete at 09:10 UTC, and that row states the known-answer part met as well.
  The release is still decided per hypothesis, and it also needs CAL's two eligibility conditions and the money rule
  (decision of 15:14 (2)): the two conditions (9 or more eligible creators, and a detectable effect within 1.5 times
  the smallest effect of interest; A10.2) are read after the hold-out labels, from the hold-out's eligible counts; and
  HR (b, c), a line of the fifth money tier, starts only if committed spend plus its cap stays at or below 120 USD
  (03:08).
* *Not replaced here.* H10's two readers, who first resolve what a passage refers to (hypotheses.md, H10). H10 is not
  run in the first round and enters Holm with p = 1; its readers are replaced before it is run (decision of 04:55
  (m)).
* *Already replaced before 03:08 UTC, listed for completeness:*
  * the two people of the span-label protocol (hypotheses.md 14.0, item 1) and of rule R7, by A1 and A8;
  * the two title coders (14.0, item 2), by the two-model gates, and after those failed, by the owner's decision of
    about 00:30 UTC;
  * the 600 double-coded sentences for H2, by three things: the two-model gates; the largest model's re-read of
    about 300 statements (about 00:30 UTC); and a second reading of 300 forecast candidates and 400 sentence units by
    another model (02:50 UTC; its figures are in the registry row of 04:55).

---

## Part 3. Definition of "uninformative"

**"Uninformative" under A2, defined 2026-11-21 (02:50 UTC), before any hold-out label and before any registered
quantity of H1, H2 or H4 to H10 exists.** A result of a registered hypothesis is *uninformative* in either of two
cases:

* its 90% interval over creators contains both zero and the smallest effect of interest in either direction;
* its verdict is not determinable (A10.2).

An uninformative result leaves the headline claims of the paper. Its row, with estimate, interval and verdict, stays
in the results table (A2). Every other result is informative whatever its direction and stays in the claims with its
verdict. That includes an interval that excludes zero, and an interval that lies inside plus and minus the smallest
effect of interest (no effect of that size). The paper says how many registered hypotheses were tested, how many were
uninformative, and how many are discussed.

Applied as follows (writer's specification; the hypothesis code applies it; H6's δ was fixed at 06:44 UTC, decision
(6)):

* "Zero" is the no-effect value on the scale where the smallest effect is registered: 0 for differences and for log
  ratios (a ratio of 1).
* "In either direction": with δ the smallest effect of interest, the interval holds zero and holds δ or -δ. For a
  ratio, -δ on the log scale is the reciprocal of the ratio that δ gives.
* The interval is the 90% interval over creators of the primary estimate, by the procedures of A10.7; for H5 and H6
  it is the interval that the Mantel-Haenszel estimate carries (A10.4: the wider of two, since the coverage repeat has
  not run; 15:14 (2)), not the t interval on OE that A5 also reads (06:44 (5)). Under the guard, the intervals of both versions are
  read, and the result is uninformative if either is. A result that is not determinable in either version is not
  determinable (guard, 04:55 (g)) and so uninformative.
* "Not determinable" also covers "not run for want of an instrument" (A10.5), because no estimate exists under an
  instrument that passed its gates.
* H3 and H8 keep the rows that A6 and A9 give them. The definition is not used to bring either back into the claims
  or to reword it. H3's result was known when the definition was written.

| | Scale | δ |
|---|---|---|
| H1 | pooled log rate ratio | 0.05 (the registered log ratio of -0.05 and its mirror; ratios about 0.95 and 1.05) |
| H2 | pooled Somers' D | 0.10 |
| H4 | pooled standardised drop | 0.5 between-creator standard deviations |
| H5 | log of the Mantel-Haenszel odds ratio | 0.4 |
| H6 | log of the Mantel-Haenszel rate ratio | log 2 (ratios 0.5 and 2), the registered smallest effect (decision of 06:44 (6); the equivalence band 0.67 to 1.5, which would give the stricter log 1.5, was not taken) |
| H7 | creator-balanced excess | k x SD_L (A10.6) |
| H9 | standardised content-minus-style difference | 0.2 (placeholder until it is set from seen cells) |
| H10 | risk difference | 0.15 |

---

## Part 4. Hold-out-only estimates are primary

**Hold-out-only estimates are primary, decided 2026-11-21 (02:50 UTC) before any hold-out label; no replication wave
exists (04:55 UTC).** For H1, H2, H4, H5, H6 and H9, four things are computed on hold-out creators only (for H9,
hold-out creators against seen creators, as registered): the primary estimate, its intervals, the Holm p and the
verdict.

* *No wave.* No replication wave exists: downloads were closed on 2026-11-20. The hold-out is therefore the only
  confirmation sample, and the first round has no pooled row (decision of 04:55 (h)). No code path pools a wave: the
  confirmatory estimates read hold-out recordings only (H9 also its seen partners), and a recording of any other group
  is left out, never pooled.
* *If a wave is ever collected.* The registered "hold-out and replication wave pooled" estimate is then reported as a
  secondary row, and a verdict must hold both on the hold-out alone and on the pooled row (04:55 (h)); the code's
  README states this rule, and no code implements a pooled row. The wave on its own is reported as persistence in the
  same roster. H7 and H10 have data only on a wave; neither is run in the first round (A4; 04:55 (h), (m)). If they are
  ever run, their results are worded as persistence within the roster, not as results for new creators (hypotheses.md
  14.0, "Two kinds of confirmation"). H3 was registered on the hold-out alone; H8 is dropped.
* *Freeze 2 in the code (06:44 (2)).* Freeze 2 is one record, `llm/freeze2.json`, with the six keys fixed at 02:45. The
  hypothesis code reads no other record. It requires every key to be present and not empty, four of them in their
  form (the two hash maps as maps, `constants_sha256` a SHA-256, `registry_commit` a commit hash),
  `analysis_code_sha256` to list every module of the code with its current hash, `constants_sha256` to be the hash of
  its constants file, and the freeze-2 constants to be set; a missing or empty key fails closed. The record's other
  keys (the hashes of the labelling files, freeze 1, the registry commit) are checked by the labelling side, which
  gates every hold-out label: it also requires the freeze-1 time to be that of the freeze-1 record and registry.md at
  the named commit (read with git) to contain the string `**A10.`, the heading of this amendment. The registry's row of
  09:19 UTC quotes that string, so every registry commit since 09:19:46 UTC passes this test whether or not A10 has been
  entered: the test does not by itself show that A10 is in force, and the freeze-2 record must name a commit that holds
  this amendment (checked by reading the registry at that commit). Because the constants file is one of the hashed modules, the record can
  be written only after the freeze-2 constants are entered. They were entered after the run of 14:00 UTC (decision of
  12:52 (6); a second reader's independent computation gave the same three values): H4's yardstick 0.14738201990446706
  (52 seen creators; the middle model's 0.1618 printed beside it), H2's length bands (12, 20) words and H2's retained
  parts time window, named actor and observable outcome (place and quantity below 5% prevalence; 9,005 verified seen
  statements). H4's yardstick is taken over the seen creators with at least 40 own-voice forms (contracted and full),
  a minimum that, as the row of 15:14 states, was set in code before any seen label existed; it is kept, stated as a
  choice (decision of 15:14 (2)): 0.1474 over 52 creators with it, 0.156 over 60 without it. The yardstick only scales
  H4's standardised drops, so the sign-flip p does not depend on it; the conditions that compare a drop with 0.5 do.
  The code was committed at
  15:16:44 UTC (`c8f1f73`, decision of 09:19 (5)) and given LF line endings at 15:17:18 UTC (`c08c2a8`, so that the
  freeze-2 hashes can be checked against the repository's files); the constants file's SHA-256 is now `cf544528...`
  (`c079dbf8...` when the constants were entered, 14:10:38 UTC), with the same three values. The record did not exist at
  14:10:38, 14:37:35, 14:48:41, 15:47:24, 15:49:31 or 16:04:08 UTC.
* *Hold-out protection in the code (04:55 (f)).* Every ordinary loader of the hypothesis code runs its permission
  check before it lists a folder or opens a file. Until the freeze-2 record passes, it opens only files in folders that
  the synthetic generator has marked, never a path under `labels/holdout` or `labels/other`. It refuses a label file
  that is not marked synthetic as soon as it is parsed, before any label field is read; only the file's synthetic,
  smoke-run, run-limit and freeze-record markers are looked at. A per-recording model file or the published table
  carries no such mark, so only its folder gates it. The hold-out cross-check against the table is refused before
  freeze 2, except in a run whose records and table are all marked synthetic.
* *The seen-only path (06:44 (1)).* One loader is the exception: before freeze 2 it opens `labels/seen` of the
  production label tree and nothing else, to compute the freeze-2 constants (H4's yardstick, H2's length bands and
  retained parts), the A10.7 null-mean check and CAL part (f). It checks every folder and file before it is listed or
  opened, with links and junctions resolved, and refuses `labels/holdout`, `labels/other`, a link that leads out of
  `labels/seen` and any other path. It parses each file and looks at its `group` field first; a file whose group is
  not "seen" is refused before any other field of it is used. Every parsed record is checked again, and real records
  are read only under the frozen recognizer rule (Part 6). Outside the production tree it reads only folders and files
  marked synthetic (tests). No hypothesis estimate reads through it, and it is part of the code that freeze 2 hashes.
  It was run on the production seen tree at 14:00:03 to 14:00:37 UTC (`run.py constants`, exit 0): 1,293 files each
  of voice, asks, features, forecasts and sentences and 71 title files, all of group "seen"; the recognizer rule kept
  1,284 recordings and left out the 9 of unknown model. A verifier ran the same command once more at 14:39:26 to
  14:40:01 UTC (exit 0), on the same code, and every printed value was the same.
* *One feature version (12:52 (4)).* Every bundle the code builds, through the ordinary loaders or the seen-only path,
  is refused if its feature files carry more than one feature version. The seen feature files are features-4, so the
  hold-out feature files must be written by the same rule before H9 can pair hold-out cells with seen cells.
* *The hold-out feature step (freeze 1, amendment 1; decision of 15:14 (1)).* The hold-out and other-group feature files
  that H1, H4, H5 and H9 read had no guarded path: hold-out transcripts open only while produce.py is the program, and
  produce.py had no feature step, as the analysis code's README foresaw ("by a new freeze-1 entry"). produce.py gains a
  command `features GROUP`. For a group other than seen it runs only after freeze 2. It loads the analysis package's
  `features.py` only if its SHA-256 equals the hash that freeze 2 pins for it, so that seen and hold-out features come
  from one source; it uses the seen run's names and families inputs, whose hashes freeze 2 pins; and it writes
  `labels/GROUP/features` with the same feature version. No instrument, prompt, model, setting or request changes.
  Freeze 1 is written again for the changed produce.py; the record of 04:58:22 UTC is kept beside it, and seen labels
  keep their freeze time. Since the freeze-2 record must name the freeze-1 record in force (its `freeze1_frozen_utc` is
  checked against `freeze.json`), freeze 2 is written after freeze 1 has been written again.
* *Why.* The wave would hold later recordings of the same creators. Pooled with the hold-out, it would mix new
  creators with later recordings of creators already seen. Creators' habits persist, so the seen creators' part of the
  wave would tend to "confirm" by persistence alone (meta-review M8). The hold-out creators are the only creators on
  whom no instrument was developed (A1); their contacts are listed in the contact log.
* *Consequence.* Fewer creators enter each test, so each test has less power, and the persistence of seen creators
  cannot carry a verdict. A subset of creators can show a larger effect than a pool; the rule of 04:55 (h), that a
  verdict must also hold on a pooled row if one ever exists, keeps that from making a verdict easier to reach. The
  registered text already says that H2's margin of 0.10 "cannot be resolved on the hold-out alone". H2's refutation by
  equivalence is therefore probably out of reach; a refutation by a positive D remains possible.

---

## Part 5. Relayed voice merged into claimed voice

**Relayed voice merged into claimed voice, 2026-11-21 (02:55 UTC), at the first measurement on the frozen voice
pair; H4's primary confirmed on the embodied voice at 04:55 UTC.** After the one revision that plan 3.4 allows
(voice revision 3):

* gates A, B and C passed (C 0.901 against 0.90);
* gate D's kappa rows passed (claimed, own and other voice 0.890; embodied against own 0.921);
* gate D's relayed-voice row failed on its lower bound (0.762, lower bound 0.488, against 0.60 and 0.50).

Under plan 3.4, the code is merged once the one revision is spent: relayed voice is merged into claimed voice. The
relayed-only secondary estimates of H1 and H4 are reported with the flag *below the reliability floor* and carry no
verdict. The alternative declared beforehand, frame-only relay reported apart, was measured and does not help (0.654,
lower bound 0.141).

* *Effect (decision of 04:55 (a)).* No registered primary quantity uses relayed voice alone.
  * H1's primary is the claimed voice, embodied and relayed together (V2 + V3), as registered ("spans a creator
    presents as a claimed voice"). Its embodied-only estimate is a secondary row without a verdict.
  * H4's primary stays the embodied first-person voice (V2), as hypotheses.md registers it ("Primary on embodied
    first-person spans"); gate D's embodied row passed. The claimed voice V2 + V3 is a secondary row of H4 without a
    verdict. Every H4 robustness row, and its eligible count, uses V2.
  * H6 uses the claimed voice V2 + V3.
* *Related, for reliability reporting only (01:10 UTC).* Labels V4 (another participant) and V6 (unseparated
  conversation) are merged into one "other speakers" label. Neither enters a registered contrast.

---

## Part 6. Recognizer rule

**Recognizer rule, 2026-11-21 (03:08 UTC), fixed before any label; its sensitivity row built as written (04:55 UTC),
with H5's strata creator by model (06:44 UTC), the 9 seen transcripts without a stated model in it as unknown model
(11:08 UTC), and recordings whose model is in dispute kept out of it (15:14 UTC).**
Every registered test uses only transcripts of the run's English-only recognizer model. So does every constant
derived from seen creators that a test uses: H4's yardstick, H2's length bands, the eligibility projections and CAL
part (f), which has not run (15:14 (2)); the freeze-2 constants of 14:00 UTC were computed on the 1,284 seen recordings
the rule keeps. The 9 seen
transcripts of the other model and every transcript of unknown model are excluded from the
primary and go into one sensitivity row, stratified by model (decision of 04:55 (b)). The label and feature files of
those 9 state no model (the published table names the other model for them), so they enter the row as unknown model
(decision of 11:08 (4)); the analysis's config template names no per-recording model file that would give them the
table's model. The
unknown-model transcripts include 2 hold-out transcripts, until freeze 2.

* *In the code.* The rule keeps, beside the primary list, the recordings of another stated model and of unknown
  model, each tagged with its model, and adds one model-stratified row to H1, H2, H4, H5, H6 and H9.
  * H1, H4 and H6 are within-recording contrasts, so each comparison stays within one model.
  * H2 crosses its length bands with the model.
  * H9 builds cells within one model and pairs each hold-out cell only with seen cells of its model.
  * H5 keeps, for each creator, only the models in which it has both channelled and own-voice recordings, and each
    of those models is a stratum of its own, creator by model, so that no side contrast mixes models (decision of
    06:44 (9)). OE is centred within each model: (w_A - sum over models m of T_A,m w_m/T_m)/T_A, with w_m and T_m the
    creator's world-claim hits and hits of both sides in model m. The Mantel-Haenszel odds ratio has one stratum per
    creator and model. The registered half-count value of a creator with several strata is the inverse-variance
    weighted mean of its strata's values, and the two-stage bootstrap resamples within side and stratum. The
    two-recordings rule and the hit rules read the creator's totals over its strata. Outside this row a creator has
    one stratum and every value is unchanged.
  * A recording whose model is in dispute stays out of the row (decision of 15:14 (2)): it is neither of another
    stated model nor of unknown model. Recordings whose sources state different models are in dispute. So are hold-out
    recordings whose own sources state a model that the published table contradicts. A hold-out recording whose
    sources state no model disputes nothing and stays in the row as unknown model.
  * The row's counts are written before any outcome.
* *Why.* The recognizer models differ in timing, pause, filler and contraction measures (bridge BR, part a). The rule
  makes the registered condition "English recordings from one recognizer model" exact.

---

## Part 7. H2 and H5 at the analysis level

**H2 and H5 revised at the analysis level (meta-review M9), 2026-11-21 (02:50 UTC), with the decisions of 04:55 UTC,
before any first-round label, and confirmed at 06:44 UTC.** These change what H2 and H5 measure, not an estimator,
reference, minimum, interval or centring, so the guard does not cover them (decision of 06:44 (7)). The rows without
each change (H2 with the flagged statements included, H2's five-part score, H5 with the self-naming units kept) are
reported beside each primary with their own verdicts, and show what each change does.

* **H2, shared wording.** A statement is flagged when its wording holds scenario or withdrawal wording, the two
  categories that both codebooks name: the checkability codebook names outcomes that cannot fail ("either A or B")
  and outcomes that the wording itself withdraws ("in some sense", "on another level"); the commitment codebook names
  "one possible scenario", alternative timelines set side by side and the disclaimer "I'm not saying it will". The
  rule is a fixed list of patterns, four for scenario wording (SC1 to SC4) and four for withdrawal wording (WD1 to
  WD4), that reads only the statement's wording, never a code. The plain hedge "a possibility" (the former SC5) left
  the list at 04:55 (e): it is the commitment code itself, not scenario wording, and flagging it would select the
  primary sample on the outcome. H2's primary row uses the unflagged statements; the row with the flagged statements
  included is reported beside it with its own verdict, and the flagged statements are counted by pattern.
* **H2, parts.** The checkability score counts only the parts with at least 5% prevalence on seen statements, a
  constant entered before freeze 2. The five-part score is a row. If no part reaches 5%, H2 is "not determinable: no
  checkability part reaches 5% prevalence on seen statements".
* **H2, a time window from the period of the talk (second reading, 04:55).** The checkability answer marks a time
  window that only the line "Period of the talk" supplies with its "where" value FRAME (the answer's
  `time_window.where`; STATEMENT, CONTEXT, FRAME or NA). H2 gets a sensitivity row in which such a time window counts
  as NO, whatever its value. The primary score already counts a part only where it is found in the statement or its
  context sentence (STATEMENT or CONTEXT, rule R10), so a FRAME time window read as YES does not count in the primary
  either. The new row therefore differs from the primary only where a FRAME time window is read "cannot tell" (and
  only if the time window is among the retained parts): the primary leaves such a statement out as missing, and the
  row counts the part as NO. The existing row "FRAME parts counted" is the one in which a FRAME time window, like any
  FRAME part, counts as YES. The second reading found
  most time-window disagreements in record readings of YES from FRAME; the primary score does not count those. The row
  stays as built (decision of 06:44 (8)): rule R10 already keeps FRAME time windows out of the primary, so the second
  reading's FRAME disagreements do not reach it.
* **H5.** The unit that holds a self-introduction of a claimed source, and the unit after it, are excluded from both
  sides and counted; the row with those units kept is reported beside the primary. Three assignments of code Q2 are
  reported: as registered (the primary), merged with Q1, and excluded.
* **Second reading (02:50; figures in the registry row of 04:55).** It covers checkability and the sentence codes, not
  commitment. The checkability codebook is not changed before freeze 1.

---

## Part 8. Deviations from the frozen registry

The registry was frozen at 2026-11-20 19:47 UTC. It names repository commit `b0970fe` (19:36:36 UTC), the last commit
that changed hypotheses.md; the registry file itself was first committed in `6f05e11` (19:47:41 UTC). The text of the
hypotheses is unchanged since then: [`hypotheses.md`](hypotheses.md) still has SHA-256 `831ed6fa...ef713`.

**How to read the table.**

* *Times.* "Registry" is the time the entry states. "Commit" is the UTC time of the commit that first holds the
  entry, from the git log of this worktree, converted from the commits' -05:00 offset to UTC. The commit time is the
  one an outside reader can check, and the paper cites it (decision of 06:44 (10)), with the stamp beside it. Where
  they differ, see the notes under the table.
* *Results.* Every change below was made after H3's hold-out result (2026-11-20 20:39 UTC), except the H3 procedure
  freeze. No change was made after a hold-out label or a registered quantity of H1, H2 or H4 to H10 existed, and
  none existed when this table was last brought up to date (2026-11-21, 15:46 to 16:20 UTC; freeze 2 had not been
  made). Every change up to 04:55 UTC was made before freeze
  1 (04:58:22 UTC) and before any first-round production label; the rows from 04:59 UTC on come after freeze 1, and
  seen-creator production starts with the row of 05:00 UTC. The decisions of 06:44 UTC were taken while seen
  production was running; the row states that none of them uses a first-round or hold-out label, and the hypothesis
  code could read no real label file when they were taken (its loaders refused every unmarked folder). The decisions of
  09:19 and 11:08 UTC were taken while seen production was running (it was reported complete at 11:10 UTC) and those of
  12:52 UTC after it; each of the three rows states that none of its decisions uses a first-round or hold-out label, and
  the freeze-2 constants and the A10.7 null means on seen labels were computed only after the row of 12:52 (14:00 UTC).
  The decisions of 15:14 UTC were taken after that computation, before freeze 2 and any hold-out label; the row cites
  two values computed on seen labels (H4's yardstick with and without its minimum; the null mean of H6's registered
  version).
  The column "Also known" lists what else was known:
  * BR: the recognizer bridge result (21:26 UTC);
  * BR-b: the first tables of the word-error-rate anchor (bridge part b; 03:21 UTC; normaliser version 2 made at
    03:31:13 to 03:31:26 UTC, the edit of 03:43 changing only the trimming rule, as addendum 2 of the exploratory
    reporting plan corrects);
  * CAL: the calibration item's results on seen creators and analogues, cited by A9 (about 22:45 UTC);
  * G: pilot, gate, reliability or known-answer results of the instrument the row concerns, on seen creators;
  * PAN: other results of the second-round panel, on seen creators;
  * REV: the paper review (by 02:49 UTC);
  * FRV: the freeze-readiness verification of the code and the instruments (code review, offline probes and
    simulation on synthetic creators; by 04:55 UTC);
  * DBL: the second reading of 02:50 on seen check creators (figures in the row of 04:55);
  * VG: the cross-vendor voice check's sealed figures, opened after freeze 1;
  * SV: the second verification of the hypothesis code and of the draft of A10 (06:22 to 06:41 UTC; a reading of the code,
    the registry, hypotheses.md and the registry's git log, with a constructed numerical example; no label);
  * V3, V4, V5: the third, fourth and fifth verifications of the hypothesis code (readings of the code, exact
    enumeration on constructed numbers and runs on synthetic creators; no label), reported before the rows of 09:19,
    11:08 and 12:52;
  * FT: counts of the seen feature step on seen transcripts (private features note: the content share of contractions
    and of family-variant tokens under features-2, 09:29 UTC onward; the ain't and y'all counts of the verifier of round
    5, 12:24 UTC); counts only, no label;
  * SP: seen-creator production, complete at 11:10 UTC (the freeze-2 constants and the null means, with their counts,
    were computed on its labels at 14:00 UTC, after the row of 13:05 and before that of 15:14);
  * SP-C: the outputs of that computation on seen labels (14:00 UTC; counts and derived numbers only), and H4's
    yardstick without its minimum as the row of 15:14 states it;
  * DV: the fourth verification of this draft (14:35 to 15:00 UTC; a reading of the registry, the code and its outputs,
    with reruns of `run.py constants` on the seen tree and of the selftest; no hold-out label).
* *Direction.* "stricter": a verdict can only become harder to reach. "guarded": the change could move a result
  toward support and is covered by A10's guard. "neutral": no effect on any verdict. "exploratory": exploratory
  outputs only. "deviation": a departure from an earlier rule or text, stated with its direction. "construct": a change
  of what is measured, made in both versions alike, direction not known in advance unless stated. "budget" and
  "operations" have no effect on any procedure.

| Registry (UTC) | Commit (UTC) | Change | Applies to | Also known | Direction |
|---|---|---|---|---|---|
| 11-20 20:38 | 20:38:07 | H3 procedure freeze. The interval is a percentile bootstrap because the coverage audit had not run; the registered text named the procedure that audit would fix | H3 | H3's seen values (exploratory) | neutral; a deviation from the text, made before the result |
| 11-20 "after H3 was tested" | 20:39:59 | A5: "supported" also needs the 90% creator interval to exclude zero | H1, H2, H4-H10 | H3's result itself | stricter |
| 11-20 | 20:49:09 | A6: H3 dropped (out of the claims, row kept, closed). Its registered wave replication is not run | H3 | - | stricter for the claims; the replication is a deviation |
| 11-20 | 20:49:09 | A7: the second-round panel gets control of the second 50 USD; everything it adds is exploratory | - | - | exploratory |
| "the same day" | 21:18:10 | A7 addition: metadata, topics, comparisons, distributions; two rounds of deliberation | - | - | exploratory |
| "the same day" | 21:26:30 | A7 addition amended: analyses by regular expression (pattern counts) added to the list | - | BR | exploratory |
| "the same evening" | 21:34:07 | A7 additions: change by week and by month, correlations, topics across channels; date analyses split by date quality | - | BR | exploratory |
| about 22:30 | 22:32:31 | A3: budget raised to 120 USD | - | BR | budget |
| - | 22:56:59 | Hold-out contact log added | - | PAN | disclosure |
| about 22:45 | 23:03:43 | A8: no human check; the strongest verdict is "model-coded" | H1, H2, H4-H6, H9 | BR, CAL, G | weaker evidence, stricter wording |
| about 22:45 | 23:03:43 | A9: H8 dropped (p = 1 in Holm); the stricter amendments approved in principle | H8; all | CAL | stricter |
| - | 23:03:43 | Primary definitions: broad own voice; an offer alone does not end a claimed voice | H1, H4, H6 | CAL, G (voice pilots) | neutral; chosen before any label of the frozen instrument |
| about 22:50 | 23:06:19 | A11: verification by language models in place of the human check; timeline of predictions (exploratory) | wording of H1-H6, H9 | CAL | neutral |
| about 23:10 | 23:21:52 | Selection rule of the cohort stated, after H3's test | cohort | - | neutral; written afterwards (M6) |
| about 23:10 | 23:21:52 | Budget caps become warnings | - | - | budget |
| about 00:30 (note 1) | 00:35:52 | Owner: checkability (H2) and title codes (H5, H9) kept as records after failing their gates, with adjudication by the largest model; the punctuation sentence for H1, H4 and H6 | H2, H5, H9; H1, H4, H6 | G (the failed gates) | looser for those instruments (used below their floors), disclosed with the failed gates |
| - | 00:36:39 | Contact log: positional displays drawn from seen creators only; distributions published instead of per-creator rows | public outputs | - | disclosure |
| 00:45 (note 2) | 00:54:27 | Ask check judges each unit range once and returns a set of classes | H6 | G | neutral (engineering) |
| 00:50 | 00:54:27 | Reworded voice codebook; two rewordings per primary codebook; the pay-or-enrol census, all built before freeze 1 | robustness rows | - | stricter (more rows) |
| 01:10 | 01:29:31 | V4 and V6 merged for reliability reporting; "guided steps" wording; the adjudicating model fixed; the other-vendor reader added; timeline built after the seen forecast labels | reliability, wording, exploratory | G (verification pilot) | neutral; the other-vendor reader is stricter |
| 01:15 | 01:29:31 | Voice: variant B, with the one revision spent on gate C (0.834 against 0.90); if gate C fails again, H1, H4 and H6 are not run | H1, H4, H6 | G | stricter (consequence fixed beforehand) |
| 01:15 | 01:29:31 | Ask check input states the number of candidates; ask gate rerun | H6 | G | neutral |
| 01:15 | 01:29:31 | Middle model is the voice record on the hold-out; H4's yardstick comes from small-model labels on all seen recordings | H1, H4, H6 | G | neutral |
| 01:15 | 01:29:31 | Gate rule: combined rule; an instrument below its floor means "not run", p = 1 | all labelled | G | stricter (A10.5) |
| 01:15 | 01:29:31 | Forecast protocol defaults: H5's share and minimum hits as CAL drafted them; H2 also on one-voice recordings; calendar class; titles without a cue coded as not presented; seen creators labelled first | H2, H5 | CAL | H5's minimum guarded (A10.4); the rest neutral |
| 01:20 | 01:29:31 | Ask check: context units are for reading only; a class listed twice is accepted | H6 | G | neutral |
| 01:30 | 02:02:18 | Ask gate C failed (0.721), so the one revision is used: the union of two draws. The gate row is not switched to the row that passed. A second failure means H6 is not run (declared before the rerun). Output cap set | H6 | G | stricter or neutral |
| 02:00 | 02:02:18 | Budget 130 USD with a hard stop; batch interface; restart in the guarded environment, with no label, gate or estimate changed | - | - | budget, operations |
| 02:20 | 02:21:14 | Ask rerun: gate C passes; gate B fails for the small check, so the middle model becomes the ask-check record | H6 | G | neutral (both measured on the same runs) |
| 02:25 (note 3) | 02:21:14 | Discovery stopped by a hard cap; the H6 census keeps the middle-model find; a hold-out preparer for the rewording rows | -; H6 rows | - | budget; stricter (rows) |
| 02:40 | 02:48:59 | Known-answer battery cap raised for the six items that check frozen instruments | instruments | G | budget |
| 02:45 | 02:48:59 | Listing repair (25 seen transcripts had no listing row); format of the freeze-2 record | all labelled | - | neutral (data repair) |
| 02:50 (note 4) | 02:48:59 | Hold-out robustness rows released on `verification_passed` and `verification_basis`, not `human_passed` | HR | - | neutral (follows A8) |
| 02:50 (note 4) | 02:48:59 | The paper becomes a measurement-and-protocol paper; first-round results are reported as model-coded descriptions | paper | REV | stricter (claims) |
| 02:50 (note 4) | 02:48:59 | A8 stands; H1, H4 and H6 announced as probably not determinable (median 5, 3 and 5 eligible creators against 12) | H1, H4, H6 | REV, CAL | stricter (announced in advance) |
| 02:50 (note 4) | 02:48:59 | Accuracy anchor: word error rate against text made or edited by people, on seen creators; grid-shift re-decode | measurement | REV, BR | exploratory |
| 02:50 (note 4) | 02:48:59 | Public outputs: rows and bins with fewer than 5 creators merged; dashboard statements corrected | public outputs | REV | disclosure |
| 02:50 (note 4) | 02:48:59 | Registry additions before freeze 2: A10; hold-out-only primary; "uninformative" defined; exploratory reporting plan | all | REV, CAL | A10 guarded; "uninformative" stricter for the claims; hold-out-only primary has less power and, with the rule of 04:55 (h), cannot make a verdict easier to reach (Part 4) |
| 02:50 (note 4) | 02:48:59 | H2 and H5 revised at the analysis level (M9). H2: flagged statements, and reduced to its parts with at least 5% prevalence. H5: excludes units next to a self-naming cue; three Q2 assignments. Second readings by another model | H2, H5 | REV, G | changes registered estimands before any label; direction not known in advance; the rows without each change are reported beside (Part 7) |
| 02:50 (note 4) | 02:48:59 | H3: the wave replication reported as not run; one logged rerun of the frozen H3 code on the hold-out after freeze 2 (exploratory) | H3 | REV, CAL | exploratory |
| 02:50 (note 4) | 02:48:59 | Prediction timeline: methodological agnosticism; source types reported as separate rows | exploratory | REV | exploratory; stricter wording |
| 02:50 (note 4) | 02:48:59 | Left to the owner: ethics, lawful basis, inclusion rule, external registration, unlinking the site | - | REV | not decided |
| 02:53 | 02:56:03 | Forecast critic: one boundary sentence; forecast gates rerun; the known-answer relayed arm rescored | H2 (forecast class) | G (known-answer battery) | neutral (follows the codebook); before freeze 1 |
| 02:53 | 02:56:03 | Voice: the middle model stays the hold-out record; seen voice descriptives come from the middle-model subset | H1, H4, H6 | G | neutral |
| 02:55 | 02:56:03 | Voice revision 3: relayed voice merged into claimed voice (Part 5) | H1, H4 | G | stricter (consequence fixed in plan 3.4) |
| 02:55 | 02:56:03 | Voice settings for freeze 1; the middle model at effort low, a recorded deviation from the plan's effort rule | H1, H4, H6 | G | neutral |
| - | 02:56:03 | Stamps of nine rows corrected from 03:00 to 02:50 | record | - | correction of the record |
| 03:08 | 03:08:35 | Order of spending under the 130 USD stop | all | - | budget |
| 03:08 | 03:08:35 | Replacement of the human check in every rule that names it (Part 2) | freeze 1, HR, H1, H4, H6 | G, REV | follows A8; no floor lowered |
| 03:08 | 03:08:35 | A10 with its guard (Part 1) | H1, H2, H4-H7, H9, H10 | CAL, REV | stricter or guarded |
| 03:08 | 03:08:35 | Recognizer rule (Part 6) | all labelled tests | PAN | stricter |
| 03:08 | 03:08:35 | Panel decisions adopted: H3 wording; topic reading A, decided at about 02:30 UTC after its stage-1 results; and others | exploratory; H3 wording | PAN, CAL | exploratory; one reading chosen after its results, stated openly |
| 03:12 | 03:12:49 | Forecast critic: the relayed-forecast sentence counted as its one revision; gate D passes on its lower bound; the ten-class label fails stability (0.77 against 0.85) and is a description only; the known answer is not changed | H2 (forecast class); timeline | G (gates, known-answer battery) | neutral for the registered uses, which need F1 against the rest (gate D's contrast) |
| 03:12 | 03:12:49 | Class of record for every registered and timeline use: F1 against the rest, whose stability passes gate C (0.93). Gate C in the annotation plan reads "at least 85% of units keep their class", the ten-class label; the coarser class was chosen at 03:12, after the ten-class row had failed | H2 (forecast class); timeline | G (the failed ten-class row) | deviation from gate C's wording, chosen after its result and stated openly: looser for the gate (a two-class label keeps its value more easily than a ten-class one); neutral for the registered uses, which read only F1 against the rest |
| 03:12 | 03:12:49 | Production adjudication of checkability keeps the large model fixed at 01:10; the recorded gate figures, made with another tier, stay as recorded and the difference is reported | H2 (checkability) | G | neutral (decided before these figures) |
| 03:18 | 03:18:18 | Entrance experiment: pattern version 1 is primary, version 2 (revised after the check reading) a labelled secondary row; the names lexicon pinned to the store version of its seen run; counts as cue counts and upper bounds | exploratory | G (check reading), PAN | exploratory; version 2 made after a reading, labelled |
| 03:21 | 03:21:45 | Other-vendor voice check (gate VG-6) fixed before its sealed figures are opened: comparator the stored OpenAI majority; on failure H1, H4 and H6 are flagged and capped at "not determined" and the HR (b, c) money returns; on a pass it serves the HR (b, c) release rule, overriding the programme's rule that the fallback cannot pass | H1, H4, H6; HR | G (figures sealed) | stricter for H1, H4 and H6; looser for the HR release (the fallback can pass), fixed before the figures |
| 03:21 | 03:21:45 | Verification before freeze 1: typed guided fields and shard sizes kept; the sentence-code instrument stays at one unit per call, the gated form, against the protocol text's 15 per call; the time instrument's role stability reported as a limit | instruments (H2, H5) | G | neutral; a deviation from the protocol text, the gated form kept |
| 04:55 | 04:55:07 | Budget guard at worst case: the 130 USD hard stop and every tag cap are tested with every open batch job at its worst case plus the new step's worst case; the protocol's one repeat reserves its full output cap; batch reservations hold twice the measured mean output (at most the cap), measured on seen pilot and gate stores; production waves under 128 USD at worst case; the verification shard's pins amended for four files after its requests were rebuilt and found unchanged | - | FRV | budget, operations; the hard stop holds at worst case again |
| 04:55 | 04:55:07 | Decisions on the freeze-readiness open points: (a) H4's primary stays the embodied voice (V2) as registered, V2 + V3 a secondary row without a verdict (Part 5); (b) the model-stratified recognizer row built as written (Part 6); (c) H5's HKSJ random-effects row (A10.7); (d) each registered version under the guard uses the interval hypotheses.md registers for it (guard); (e) "a possibility" leaves H2's shared-wording flag (Part 7); (f) label files opened only after the permission check (Part 4); (g) "not determinable" when either guarded version is (guard); (h) no replication wave, the hold-out the only confirmation sample (Part 4); (i) H7's verdict against both margins (A10.6); (j) the wider Mantel-Haenszel interval until the coverage repeat (A10.4); (k) H6's registered version uncentred, its null mean reported (A10.7); (l) A10.k = CAL A(7 + k) in text and code; (m) H10 not run in the first round, its readers replaced before it is run (Part 2); (n) the simulation battery on the earlier code stopped, a new one on the final code | H1, H2, H4-H7, H9, H10 | FRV, DBL, CAL | (a), (d) and (k) follow the registered text; (b) and (c) add rows; (g), (h), (i) and (j) stricter; (e) changes H2's primary sample, direction not known in advance, and removes a selection on the outcome; (f), (l), (m) and (n) neutral or operations |
| 04:55 | 04:55:07 | Second reading (02:50) recorded on seen check creators; the checkability codebook is not changed before freeze 1; H2 gets a sensitivity row in which a time window taken only from the period of the talk counts as NO; the reading covers checkability and the sentence codes, not commitment | H2, H5 | DBL | stricter (one more row); the primary already does not count such a time window read as YES, so the row differs from it only where it is read "cannot tell" (Part 7) |
| freeze-1 entry: 04:58:22 | 04:59:30 | Freeze 1 of the instruments: record, configuration, models, code and 83 prompt and schema files fixed by hash; seen production unlocked, hold-out and other labels only after freeze 2 | instruments | G, FRV, DBL | procedure freeze |
| 04:59 (note 5) | 04:59:30 | Freeze 1 does not wait for the known-answer battery's last voice batches (pending since about 02:47 UTC), against the rule of 03:08 that freeze 1 waits on the battery's pre-set rules (Part 2); the request-id fixture retaken for the four forecast-critic lists only | freeze 1; HR | G (the battery's finished items) | deviation from the 03:08 rule, stated with its reason: looser for freeze 1's timing; no instrument is affected (each has spent its revision), and the battery still serves the paper and the HR (b, c) release |
| 04:59 | 04:59:30 | Gate VG-6 opened after freeze 1 with its seal verified: kappa 0.91 (0.84 to 0.95) on claimed, own and other voice, 0.91 (0.83 to 0.96) on the embodied contrast; it passes, so no vendor flag applies to H1, H4 and H6, and VG-6 meets its part of the HR (b, c) release | H1, H4, H6; HR | VG | neutral (a result read under the meaning fixed at 03:21) |
| 05:00 | 05:00:56 | Seen-creator production starts through the batch interface under freeze 1, one driver per instrument, with its cost projection (about 20 USD) reported before sending and spending stops on three of its lines | seen labels | G | budget, operations |
| 06:33 | 06:33:35 | The heads of the seen voice and forecast chains move to the standard interface after their batch jobs had returned nothing for 80 to 85 minutes (open jobs cancelled first; request ids and bodies unchanged; about 2 USD extra); three known-answer batch jobs re-sent after cancellation at 05:44 | seen labels; known-answer battery | - | budget, operations |
| 06:36 | 06:36:14 | Exploratory reporting plan and its addendum 1 registered by hash. Lead's decisions in the addendum: the public rows of the word-error-rate anchor keep machine texts of different origin apart and withhold the pooled automatic row, a departure from the plan's section 3; the diagnostic cards' verdicts are not reported; the missing measures of the grid-shift re-decode (BR-GS) are built from the existing re-decodes; the abstract gives the caption figure as agreement only; the anchor's hold-out part runs after freeze 2 as a logged contact | exploratory outputs | BR-b | exploratory; hashed after the anchor's first tables, which the addendum names; the departure is stated with its reason |
| 06:39 | 06:39:33 | Every small-model stage of the seen chain (sentence codes, asks find and small-model check) moves to the standard interface after its batch jobs were cancelled and collected; the middle-model and title stages stay in batch; extra cost of all moves about 5 USD; the committed spend projected after the seen and hold-out chains stays under the 120 USD warning only if the hold-out small-model stages go through batch or the queue clears | seen labels | - | budget, operations |
| contact log: about 03:00 to 06:35 | 06:36:14 | Hold-out contact: the public-output generators loaded the run report's per-recording timing cache, hold-out and other creators included, to rebuild distribution tables; no word, label or hypothesis statistic was read or produced | public outputs | - | disclosure; one generator no longer loads the cache and the other two are changed to read seen creators only for positional measures (closed by the entry of 06:49:10) |
| 06:44 | 06:44:05 | Decisions on the second verification of the hypothesis code, before freeze 2 and any hold-out label: (1) a seen-only permission path: before freeze 2 the analysis code may open labels/seen only, refusing any other path and any record whose group is not seen, for the freeze-2 constants, CAL part (f) and the A10.7 null-mean check; the path is part of the code freeze 2 hashes (Part 4; A10.7); (2) one freeze-2 record, `llm/freeze2.json` with the six keys of 02:45, which the analysis code checks against its modules (Part 4); (3) H6's amended OE and Mantel-Haenszel rate ratio centred per recording, the registered version as registered (A10.4; guard); (4) H9's creator-bootstrap interval drawn creators, then recordings (R1) in both versions, with fewer draws allowed in the simulation battery if stated (A10.7; guard); (5) A5 for H5 and H6 on both the t interval of the creator OE values and the wider Mantel-Haenszel interval (A10.1; A10.4); (6) H6's δ for "uninformative" stays log 2 (Part 3); (7) the M9 revisions stay outside the guard, the rows without them reported with their own verdicts (Part 7); (8) H2's FRAME row stays as built (Part 7); (9) creator-by-model strata for H5 in the model-stratified row (Part 6); (10) times cited in the paper are commit times (this table); (11) the full simulation battery started at 04:57 on earlier code was stopped at 06:42, a new one is to run on the final code | H2, H5, H6, H9; freeze 2; paper | SV, FRV | (1) neutral for every verdict: a narrow exception to (f) that opens only seen labels, which freeze 1 released for production, and computes no hypothesis quantity; (2) neutral, fails closed; (3) guarded: it changes the amended statistic and removes a centring fault in H6's predicted direction; (4) and (6) follow the registered text (for (6), the stricter δ of log 1.5 was not taken); (5) stricter; (7) and (8) neutral, confirming Part 7; (9) a sensitivity row only, now exactly within one model; (10) record; (11) operations |
| contact log: 06:49:10 (note 6) | 07:43:42 | Hold-out contact: a one-off script loaded the run report's per-recording timing cache once and kept only the rows of the 71 seen creators (by the creator sets of freeze 1), writing a seen-only derivative; nothing was computed on any other row, and the script refuses to run again. Since then no generator reads the cache: whole-run counts come from ledger fields, every timing measure from the seen derivative | public outputs | - | disclosure; closes the generators' use of hold-out timing rows |
| 07:50 (note 7) | 07:50:12 | The forecast critic (about 42,600 small-model requests) was first sent through batch to save about 2.2 USD, under a rule fixed beforehand: cancel if under half is back after 30 minutes. None of the first 3,000 came back in 30 minutes, so its batch jobs were cancelled and collected and it runs through the standard interface (estimate 4.4 USD, run limit 6 USD). Seen titles, voice and asks are done | seen labels | - | budget, operations; the rule fixed beforehand was applied |
| - (note 7) | 08:24:06 | The row of 07:50 moved from the hold-out contact log into the table of decisions (commit message: "insertion slip"); its text unchanged | record | - | correction of the record |
| 08:33 | 08:33:43 | Known-answer battery: its voice parts (the revision-3 arms and the voice audit), waiting in the small model's batch queue since about 02:47 (cancelled and re-sent once at 05:44), finish through the standard interface after both lanes' open batch jobs were cancelled and collected; a few hundred requests, about 1 USD, inside the battery's tag cap tested at worst case | known-answer battery; HR | - | budget, operations |
| 09:10 | 09:10:22 | Known-answer battery complete (constructed texts; exploratory, an upper bound and not accuracy on the corpus): with voice revision 3 the small model's recovery rose on the relayed-voice, own-offer and interview arms, and the canary gates pass for voice, asks and forecasts. With VG-6 (04:59), the row states both parts of the HR (b, c) release rule met; HR (b, c), a tier-5 line, starts only within the 120 USD rule of 03:08 | HR; paper | G (the battery's results) | neutral: a result read under rules fixed before it (03:08, 03:21); no instrument changes |
| 09:19 (note 8) | 09:19:46 | Decisions on the third verification of the hypothesis code, before freeze 2 and any hold-out label: (1) H6's amended version keeps OE centred per recording, but its reference becomes a conditional Monte Carlo draw under the per-recording null (each recording's asks from a binomial with its claimed share, given its ask count) in place of the sign-flip, because exact enumeration showed the one-sided sign-flip rejecting 1.93% at 0.005 with one ask a creator at a claimed share of 0.3; the battery gains a null scenario with shares below one half and 1 to 3 asks a creator (A10.4); (2) the A10.7 null-mean tolerance of the OE versions is a tenth of the smallest effect on the OE scale, not 0.1 on the share scale (A10.7); (3) the null check keeps recordings without an ask file, as the analysis does (A10.7); (4) a verifier's test file that globbed the production label tree leaves the code's package; (5) the hypothesis code is committed to the analysis branch before freeze 2, and A10 keeps its `**A10.` heading for the labelling side's check (Part 4); (6) H5's stratified-row choice for a stratum without hits on one side stays as written (weight at most 0.25), stated as a limit | H5, H6; freeze 2 | V3 | (1) guarded (the amended version only); the row said it "can only make a verdict harder to reach", which the row of 11:08 corrects; replaced at 11:08 (1); (2) stricter (a tighter check); (3) neutral: the check reads the creators the analysis reads; (4) neutral: protects the hold-out; (5) record; (6) a sensitivity row, a stated limit |
| 11:08 | 11:08:52 | Correction to the row of 09:19: the conditional reference does not "only make a verdict harder to reach"; on some data its p is below the sign-flip's | H6 | V4 | correction of the record |
| 11:08 | 11:08:52 | Decisions on the fourth verification, before freeze 2 and any hold-out label: (1) H6's amended reference redraws asks by cluster (asks in the same checked unit range or in adjacent units form one cluster; each cluster's voice drawn with the recording's claimed share), and the p that enters the guard is the larger of this cluster-level conditional p and the sign-flip p of OE, so that neither the sparse low-share case (where the sign-flip over-rejects) nor bursts of asks in one voice (where an ask-level reference over-rejects: 7.7% at 0.005 for bursts of 3) can carry a verdict alone; 99,999 draws in the analysis; a burst scenario in the battery; H6's detectable-effect note from the battery (A10.1; A10.4; guard); (2) H9's content words exclude every variant of the frozen family table as well as the NAMES v2 list forms; (3) contractions whose parts are function words count as function words; (4) masking NAMES v2 forms everywhere (the flat-list form of the released mask) stays, stated as a choice, and the 9 seen transcripts without a stated model enter the model-stratified row as unknown model (Part 6); the seen feature files are written again with (2) and (3) before the freeze-2 constants are computed | H6, H9; freeze 2 | V4, FT | (1) stricter than the sign-flip of OE that A10.4 drafted, since the amended p is never below it; against the reference of 09:19 the direction depends on the data; inside the guard; (2) construct, both versions of H9: removes a mechanical raise of same-family content similarity, in H9's predicted direction; (3) construct, both versions of H9, direction not known in advance; (4) a stated choice and a sensitivity row; the re-written feature files: operations |
| 11:10 | 11:10:21 | Seen-creator production complete under freeze 1 (05:01 to 11:10): voice, asks, sentence codes and forecasts for all 1,293 English recordings of the 71 seen creators, titles for the 71 creators; production measured 24.27 USD, committed spend 111.89 USD against the 120 USD warning and the 130 USD hard stop; no hold-out or other-group recording was labelled; the freeze-2 constants are computed from these labels alone | seen labels; freeze 2 | - | budget, operations |
| 12:52 | 12:52:07 | Correction to the row of 11:08: with 99,999 draws the p is reproducible (seeded by its label), but inside about 0.0045 to 0.0055 the side of 0.005 still depends on the draws | H6 | V5 | correction of the record |
| 12:52 | 12:52:07 | Decisions on the fifth verification, before freeze 2 and any hold-out label: (1) H6's clusters: asks within 5 units of each other (about one minute of speech) form one cluster, chaining; a 10-unit window is a sensitivity row; H6's result states that dependence of asks beyond the window is not modelled; the battery gains a scenario with asks one to three units apart at shares below one half (A10.4; guard); (2) the analysis counts asks of one class whose unit ranges overlap once (the union of two find draws can return one ask twice); the instrument is frozen and unchanged (A10.4; guard); (3) H9's contraction rule also splits ain't and y'all into function words; (4) the analysis refuses a bundle whose feature files mix feature versions (Part 4); (5) the wide mask of 11:08 (2) stays (every token of every family variant, about 6% of content tokens), which can only lower same-family content similarity; (6) the freeze-2 constants are computed from the seen labels through the seen-only path after these changes, recomputed by a second reader and entered in `constants.py` (Part 4) | H6, H9; freeze 2 | V5, FT, SP | (1) corrects a level fault of 11:08's clusters (a burst of 3 asks 2 units apart at s = 0.3, 17 creators: 1.93% at 0.005 with the clusters of 11:08, 0.23% with the 5-unit window; A10.4); the amended p stays at least the sign-flip p, so stricter than A10.4's draft; inside the guard; its limit beyond the window is stated; (2) a counting correction in both versions of H6, direction not known in advance; (3) construct, both versions of H9 (20 tokens on the seen transcripts); (4) stricter: fails closed; (5) confirms 11:08 (2); (6) procedure: the constants come from seen labels alone, after every change above (14:00 UTC) |
| 13:05 | 13:05:21 | Exploratory reporting plan, addendum 2 registered by hash (`c35f316b...`): it corrects addendum 1 (normaliser version 2 made at 03:31:13 to 03:31:26 UTC; the edit of 03:43 changed only the trimming rule), records version 1 as rebuilt exactly and run (rates not printed by the pair rule), the public inventory form, the precision check without a band, the choices of the grid-shift re-decode made while building, the per-cell interval seeds, the merged rows, and the dominance and pair rules applied to every public cell of the anchor and the re-decode; and it fixes the hold-out anchor's reading of caption makers before freeze 2 | exploratory outputs | BR-b | exploratory; corrects the record of addendum 1 (row of 06:36); every choice made after a result is named |
| 15:14 | 15:14:55 | Before freeze 2. (1) Freeze 1, amendment 1: the hold-out and other-group feature files that H1, H4, H5 and H9 read had no guarded path (hold-out transcripts open only while produce.py is the program, and produce.py had no feature step), as the analysis code's README foresaw. produce.py gains a command `features GROUP` that runs only after freeze 2 for a group other than seen, loads the analysis package's `features.py` only at the SHA-256 that freeze 2 pins for it (so seen and hold-out features come from one source), uses the seen run's names and families inputs (hashes pinned in freeze 2) and writes `labels/GROUP/features` with the same feature version; no instrument, prompt, model, setting or request changes. Freeze 1 is written again for the changed produce.py; the record of 04:58:22 UTC is kept beside it, and seen labels keep their freeze time (Part 4) | H1, H4, H5, H9; freeze 1; freeze 2 | SP, DV | operations: a new freeze-1 entry that adds a guarded path for the hold-out features, computed by the code and with the inputs of the seen run; no instrument, label or verdict rule changes |
| 15:14 | 15:14:55 | (2) Settled for the A10 text, before freeze 2: the ask merge of 12:52 (2) is a counting correction in both versions of H6, outside the guard (Part 1; A10.4; guard); with CAL part (f) not run, the simulation battery on synthetic creators stands in for planted-effect recovery and the Mantel-Haenszel interval stays the wider of two (A10.4; A10.7 point 3); a recording whose model is in dispute stays out of the model-stratified row (Part 6); H4's yardstick keeps its minimum of 40 own-voice forms per creator, set in code before any seen label existed (0.1474 over 52 creators; 0.156 over 60 without it), stated as a choice (Part 4); H6's registered half-count version stays uncentred under the guard (seen null mean -0.137; A10.7 point 3; guard); the HR (b, c) release also needs CAL's two eligibility conditions, read after the hold-out labels, and its money rule (Part 2); the full battery runs on the frozen code after freeze 2 and fills H6's detectable-effect note (A10.2) | H4, H5, H6; HR; A10 text | SP, SP-C, V5, DV | the ask merge: a classification of the text, the counting of 12:52 (2) unchanged; the battery for recovery: a weaker check than the seen-label check the draft of A10.7 asked for, read by no verdict; the wider interval: as 04:55 (j), stricter; disputed recordings: a sensitivity row only; H4's yardstick: a stated choice made after both values were known on seen labels, keeping the rule the code held before them; the yardstick scales H4's standardised drops, so it moves the conditions that compare a drop with 0.5 (the kept value is the smaller) and not the sign-flip p, direction not fixed; H6's registered version: follows the registered text (04:55 (k)); the HR (b, c) release: follows the rule of 03:08 and A10.2, stricter than the row of 09:10 read alone; the battery after freeze 2: operations, and H6's detectable-effect note is filled after freeze 2 rather than before it as A10.2 asks of the others |

*Notes on the times.*

1. The paragraph "Owner decisions before freeze 1" was first stamped "about 01:00 UTC" in a commit made at 00:35:52.
   It was corrected to "about 00:30" at 00:54:27.
2. The owner's delegation is dated "about 00:50 UTC". The first row listed under it is stamped 00:45.
3. The rows stamped 02:25 are held by a commit made at 02:21:14.
4. The rows stamped 02:50 are held by a commit made at 02:48:59. Nine of them were first stamped 03:00 and corrected
   at 02:56:03 (commit message: "times corrected to the clock").
5. The row "Freeze 1 does not wait for the known-answer battery's last voice batches" is stamped 04:59, after the
   freeze it describes (04:58:22). Both are held by the commit made at 04:59:30: the decision took effect at the
   freeze and was written down after it.
6. The contact-log entry stamped 06:49:10 is held by a commit made at 07:43:42, about 54 minutes later.
7. The row stamped 07:50 was first committed (07:50:12) in the registry's hold-out contact log, after its contact
   entries, with three cells against that table's four. It records an interface decision, not a contact; the commit of
   08:24:06 moved it, unchanged, into the table of decisions. Its stamp and its first commit agree.
8. From the row of 09:19 to that of 15:14 each commit added one row, and each stamp lies within the minute before its
   commit (09:19:46, 11:08:52, 11:10:21, 12:52:07, 13:05:21, 15:14:55). The two corrections of the record (to 09:19 in the row of
   11:08, to 11:08 in the row of 12:52) are written inside the later row; the earlier rows are unchanged. The registry
   row of 15:14 holds two numbered parts in one cell; this table gives each part a row of its own, both with the
   commit 15:14:55.

*Pending at the time of writing (15:46 to 16:20 UTC, before freeze 2).* A10 itself, which becomes final at freeze 2 at
the latest. The freeze-2 record, `llm/freeze2.json`, written after the code is hashed (06:44 (2)), naming a registry
commit that holds A10 and the freeze-1 record in force (Part 4). The hold-out feature files, which `produce.py
features` writes after freeze 2 under freeze 1 as written again for the changed produce.py, with the seen run's
feature version, features-4 (15:14 (1); Part 4). The full simulation battery (04:55 (n); 06:44 (11)), which runs on the
frozen code after freeze 2 and fills H6's detectable-effect note (15:14 (2)); only quick batteries have run, the last
on the code of 12:52 (finished 13:41 UTC, task fingerprint `d97db4a2a7c4`). H7's k and SD_L, before any wave recording
(H7 is not run in the first round). H9's smallest effect, which is set from seen cells (still the placeholder 0.2). The
label-based repeat of the calibration (CAL part f), which has not run: the battery stands in for planted-effect
recovery, and the Mantel-Haenszel interval stays the wider one (15:14 (2)). An external timestamped registration, which
is left to the owner (02:50 UTC). Done since the revision of 14:07 to 14:36 UTC: the hypothesis code committed
(09:19 (5); commit `c8f1f73`, 15:16:44 UTC, with LF line endings set by `c08c2a8`, 15:17:18 UTC); the four unit tests
that failed with the constants entered now pass (selftest 224 of 224, 15:50:25 to 15:52:15 UTC). Done before it: the
freeze-2 constants and the A10.7 null-mean check on seen labels (14:00 UTC; Part 4, A10.7 point 3), and seen
production (11:10 UTC). (The exploratory reporting plan's hash was entered at 06:36 UTC, its addendum 2 at 13:05.)

---

## Notes for the lead (not for pasting)

1. **Differences from CAL's drafts.**
   * H3 enters Holm with p = 1, as the 03:08 row says. CAL's draft entered it with its creator-level p, which by CAL's
     own estimate acts as p = 1 for the others anyway.
   * CAL's numbers for SD_L and its examples for k are left out. The registry does not state them, and k is not
     fixed.
   * CAL's simulation and coverage figures are given in words, not numbers, because the registry does not state
     them. The one exception is the OE sign-flip's rate at 17 creators in A10.4, which you asked to state (checked
     against CAL's private draft between 09:05 and 09:10 UTC: 0.17%, 0.33% and 0.67% at 8, 12 and 17 creators, 600 sets, SE 0.29
     points). The exact rates in A10.4 (1.93%, 7.74%, 0.23%, 0.42% and 4.76%, and the others there) are not CAL's: they
     are computed on constructed numbers with the code's own tests (`sim_out/h6-cluster-reference-levels.md`), and the
     simulated rates of A10.4 on synthetic creators through the battery's code path
     (`sim_out/h6-pipeline-levels-1252.json`).
   * CAL's A13 point 4 (A10.6) asked to delete a sentence of the frozen text. The frozen text is not edited, so
     A10.6 says instead that S is description only.
   * CAL's A14 point 1 (A10.7) gives means of creator values the t interval. The code applies it to the OE means of
     H5 and H6 and keeps the HKSJ 90% interval of the pool for H1, H2 and H4, which register a pool (A14 point 2).
     Since 06:44 (5), A5 for H5 and H6 also needs the interval of the Mantel-Haenszel estimate, which CAL's draft did
     not ask.
   * CAL's A11 (A10.4) pooled a, b and s over a creator's recordings. Since 06:44 (3) the amended H6 is centred per
     recording, with creator-by-recording strata for the Mantel-Haenszel ratio. The two forms agree for a creator with
     one eligible recording. CAL's simulated rate of 0.67% (A10.4) is a property of CAL's form; the full battery on the
     frozen code (to run after freeze 2, 15:14 (2)) measures the new one.
2. **Settled by the decisions of 06:44 UTC, and where they are written.**
   * *H6's δ in Part 3* (old note 3): log 2, decision (6); Part 3. The stricter log 1.5 was not taken.
   * *The M9 revisions and the guard* (old note 3): outside the guard, decision (7); Part 7 and the guard paragraph.
     The rows without them are reported with their own verdicts. As I read (7), the primary's verdict is not required
     to hold on them; if you meant otherwise, say so before freeze 2.
   * *H2's FRAME row* (old note 3): stays as built, decision (8); Part 7.
   * *H9's bootstrap* (old note 3): creators, then recordings, in both versions, decision (4); A10.7 item 1, the guard
     paragraph and its table. The code re-rarefies every cell in every draw; the analysis keeps 9,999 draws, the
     end-to-end run 999, and the battery 99 (stated in the code's README, as (4) requires).
   * *The freeze-2 constants and the A10.7 null-mean check before freeze 2* (old note 3): the seen-only path, decision
     (1); Part 4 and A10.7 point 3. The command `run.py constants` prints the three constants, the middle-model
     yardstick and the part prevalence table beside them, the null means and counts only. It ran on the production
     seen tree at 14:00:03 to 14:00:37 UTC (12:52 (6); Part 4, A10.7 point 3).
   * *H5 in the model-stratified row* (old note 3): creator-by-model strata, decision (9); Part 6.
   * *H6's OE and one ask rate per creator* (old note 3): centred per recording, decision (3); A10.4, A10.7 point 3 and
     the guard. The null-mean check now places asks per recording, and the battery has a null scenario in which ask
     rates differ between a creator's recordings.
   * *The freeze-2 record's format* (old note 3): one record, `llm/freeze2.json`, decision (2); Part 4. The code reads
     `analysis_code_sha256` and `constants_sha256` from it and no record beside the modules, so on the analysis side
     the 02:45 row's statement that the six-key record "satisfies both checks that read it" now holds. The labelling
     side's check (`produce.freeze2_problem`, re-read at about 09:04 UTC) checks the same six keys, the freeze-1 time
     against freeze.json, the labelling file hashes, the analysis code and constants hashes, and that registry.md at
     the named commit contains the string `**A10.` (git, not the working tree). The pasted Part 1 must keep its heading
     `**A10. ...`. But the check does not make freeze 2 wait for A10 (corrected by the fourth verifier, 14:48 UTC): the
     registry row of 09:19, decision (5), quotes the string `**A10.` itself, so `git show <commit>:./registry.md`
     contains it for the commit of 09:19:46 UTC and every later one (`1cd98d3`, 13:05:21 UTC, and `c28162c`, 15:14:55
     UTC, included), and a freeze-2 record naming any of them passes produce's test with no A10 in the registry.
     `produce.py` has changed since freeze 1 for the `features` command of 15:14 (1) (SHA-256 `0497c5b5...` at 15:47 UTC
     against the `60bd9f62...` that freeze 1 holds; file last written 15:41:50 UTC), but its test is unchanged
     (`registry_a10_problem`, re-read at about 15:48 UTC, still looks only for the string `**A10.`), so the guard
     against this stays procedural: write `registry_commit` only after the commit that pastes Part 1, and check it, for
     example that `git show <commit>:./registry.md` holds "**A10. The stricter amendments" and "**A10.7.". Part 4 says
     so.
   * *A5 for H5 and H6*: both intervals, decision (5); A10.1, A10.4, A10.7 item 1, the guard and its table.
   * *Times* (old note 3): commit times in the paper, decision (10); Part 8, "How to read the table".
   * *The battery started at 04:57 UTC*: stopped, decision (11); Part 8. Its last status line is stamped 06:43:17 UTC,
     so it stopped at about 06:43, not 06:42 as the row says (a difference of about a minute, noted for the record).
   * Settled earlier and unchanged: H4's primary (04:55 (a)); the A10 numbering (04:55 (l); the five explicit
     pairings in this draft, and every "A10.k = CAL-A(7 + k)" pairing in the code and its README, were checked again
     by script between 09:05 and 09:10 UTC, none mismatched); guard coverage for every first-round hypothesis (H1,
     H2, H4, H5, H6, H9); A10.5's exception for the owner's 00:30 decision, which the pasted A10.5 records; H7's margin
     (04:55 (i)); H10's readers (04:55 (m)); the first verifier's points (04:55 (b) to (h), (j)).
3. **Settled by the decisions of 09:19, 11:08 and 12:52 UTC, and where they are written.**
   * *The level of H6's OE sign-flip with sparse asks* (old note 3, third verification): 09:19 (1) replaced the
     sign-flip by an ask-level conditional reference; the fourth verification found that it over-rejects bursts, and
     11:08 (1) made the p the larger of a cluster-level conditional p and the sign-flip p; the fifth found bursts with
     asks a few units apart split into single asks, and 12:52 (1) set the 5-unit window. A10.1, A10.4 (with the level
     figures and the stated limit), the guard paragraph and its table, Part 8. The 11:08 row corrects the 09:19 row's "can
     only make a verdict harder to reach", and the 12:52 row corrects the 11:08 row's claim that the decision at 0.005
     does not depend on the seed; both corrections are rows of Part 8.
   * *The tolerance of the null-mean check for OE* (old note 3): a tenth of the smallest effect on the OE scale, 09:19
     (2); A10.7 point 3. On seen labels H5's amended OE then has a tolerance of 0.0037 and H6's of 0.0125.
   * *H6's null-mean check and recordings without an ask file* (old note 3): kept with no asks, as the analysis keeps
     them, 09:19 (3); A10.7 point 3. On seen labels no seen recording with both voices lacked an ask file.
   * *A verifier test that opens the production label tree* (old note 3): it left the package, 09:19 (4), and a scan in
     the unit tests fails if any file of the package names the production tree's hold-out or other folders.
   * *The hypothesis code in git* (old note 3): to be committed to the analysis branch before freeze 2, and A10 keeps its
     `**A10.` heading, 09:19 (5). Done: committed at 15:16:44 UTC (`c8f1f73`, branch `feat/partial-cohort-asr-2026-11-20`)
     and given LF line endings at 15:17:18 UTC (`c08c2a8`). Of `sim_out` only five summary files are tracked (the
     quick-battery table and the level table, each as `.md` and `.json`, and the pipeline-level file; constructed or
     synthetic data), the rest is
     ignored. This draft is still untracked (15:55 UTC).
   * *H5's stratified-row choice* (old note 3, choices): stays, stated as a limit, 09:19 (6).
   * *The memory of the seen-only path* (old note 3): the loader was not changed, and `run.py constants` read the whole
     seen tree with exit 0 at 14:00 UTC under the guarded environment's ceiling (again at 14:39 UTC, 35 seconds).
   * *The seen feature files* (old note 3): written to `labels/seen/features` (features-3 at 11:22, features-4 at 13:02
     UTC; 1,293 files), and the analysis now refuses a bundle that mixes feature versions, 12:52 (4); Part 4.
   * *The 9 seen transcripts without a stated model* (part of old note 3 on disputed recordings): unknown model in the
     stratified row, 11:08 (4); Part 6.
4. **Settled by the decisions of 15:14 UTC (and earlier), and where they are written.**
   * *The class of 12:52 (2)* (fourth verifier): a counting correction in both versions of H6, outside the guard,
     15:14 (2); Part 1 (introduction), A10.4, the guard paragraph, Part 8. On seen asks the merge joined 1,657 of 5,878
     filed asks (485 of the 1,112 merge groups of class K1; run of 14:00 and the rerun of 14:39); the count was known
     when the class was settled, and the class changes no computation.
   * *Hold-out feature files*: freeze 1, amendment 1, 15:14 (1); Part 4 and Part 8. Part 4 describes the command as the
     row decides it, not as the code does, because produce.py was still being changed when read (last written 15:41:50
     UTC). As read at about 15:48 UTC its `features` command calls `frozen()` first, then, for holdout and other,
     `freeze2_problem()`, and `run_features` checks freeze 2 and the unlocked prep again before it reads anything; it
     pins `features.py`, `wording.py` and `constants.py` (not `features.py` alone) and the names and families inputs
     (in freeze 2's `sha256` table). `features seen` also needs `freeze2.json`. `features.py` now hashes to
     `b724e149...` (LF); its bytes differ from those of the features-4 run (`d47a943c...`) only in line endings (the
     file with CRLF line endings hashes to `d47a943c...`, checked at about 15:48 UTC), so the `features seen` re-run check
     should find the seen files byte-identical.
   * *CAL part (f), planted recovery and the interim interval*: CAL part (f) is not run; the battery on synthetic
     creators stands in for planted-effect recovery, and the Mantel-Haenszel interval stays the wider of two, 15:14 (2);
     A10.4, A10.7 point 3, Part 3, the guard paragraph. `MH_INTERVAL_RULE` is `"wider"` in `constants.py`.
   * *The model-stratified row's disputed recordings*: out of the row, 15:14 (2); Part 6.
   * *H4's yardstick minimum* (new in the text): 40 own-voice forms per creator, kept as a choice, 15:14 (2); Part 4.
     In the code it is `4 * H4_MIN_FORMS_PER_SIDE` in `h4_contraction.yardstick_from_seen`.
   * *H6's registered version*: uncentred under the guard, 15:14 (2); the guard paragraph, A10.7 point 3.
   * *The 09:10 row and the HR (b, c) release*: the release also needs CAL's two conditions, read after the hold-out
     labels, and the money rule, 15:14 (2); Part 2.
   * *The full battery on the final code* (06:44 (11)): it runs on the frozen code after freeze 2 and fills H6's
     detectable-effect note, 15:14 (2); A10.2, Part 8 (pending list). Only quick batteries have run, the last on the
     code of 12:52 (fingerprint `d97db4a2a7c4`, finished 13:41 UTC). The fingerprint is now `32757fe34057` (15:49:31
     UTC, after the LF commit); start the battery with `--expect-fingerprint` set to the fingerprint freeze 2 freezes.
   * *Four stale unit tests*: done, not by a decision. `run.py selftest` ran 224 tests at 15:50:25 to 15:52:15 UTC, all
     passing (two test files were last written at 14:50 UTC, after the fourth verifier's run of 14:41 to 14:43).
   * *The 07:50 row's place* (note 7): the commit of 08:24:06 UTC moved it, unchanged, into the table of decisions. Part
     8 keeps 07:50:12 as its commit time (the first commit that holds it) and lists the move as a correction of the
     record.
   * *Exploratory reporting plan*: the registry row of 06:36 UTC (commit 06:36:14 UTC) enters the hashes of the plan and
     of addendum 1, and the row of 13:05 UTC (commit 13:05:21) that of addendum 2. All three still match the files
     (checked again at about 15:57 UTC), and the three files are committed. Addendum 2 corrects the time at which the
     anchor's normaliser became version 2 (03:31, not 03:43); the "Also known" entry BR-b of Part 8 says so.
5. **Still open.**
   * *The order of the last steps.* produce.py no longer has the hash that freeze 1 holds (`0497c5b5...` against
     `60bd9f62...`, 15:47 UTC), so `frozen()` fails until freeze 1 is written again, and every produce.py command that
     needs it waits. freeze2.json must name the freeze-1 record in force (`freeze1_frozen_utc` against `freeze.json`).
     The order that passes: produce.py final; freeze 1 written again (the 04:58:22 record kept beside it); the commit
     that pastes A10; `run.py hashes`; freeze2.json with `registry_commit` set to that commit and the `sha256` table
     holding the labelling files and the two feature inputs. If freeze 1 is written again after the paste, the pasted
     Part 4 still reads true; if it is written after freeze 2, freeze 2 fails its own check and must be written again.
   * *A10.2's detectable effects for H1, H2, H4 and H5.* A10.2 asks each hypothesis to print, before freeze 2,
     its detectable effect from CAL part (f). CAL part (f) has not run, and the row of 15:14 settles only H6's note
     (from the battery, after freeze 2); H9's note in the code says its detectable effect comes from the battery, which
     no registry row states. Without a creator SD in the analysis config the code prints "Detectable effect
     not computed: the SD of creator values from the label-based CAL repeat is not entered." (`verdicts.detectable_note`),
     and the "run; detectable only from X" rule and the HR (b, c) condition that reads the detectable effect then have
     nothing to read. Decide before freeze 2: a source for those SDs (for example the battery's synthetic creators, or
     CAL's figures on seen creators and analogues), or a sentence in A10.2 that says the effect is not computed.
   * *H9's smallest effect* is still the placeholder 0.2 in `constants.py` ("set from seen cells", Part 3 and the
     pending list). If freeze 2 is written right after the paste, the placeholder is what freeze 2 freezes; say so in
     the record, or set it first (that changes the fingerprint).
   * *The code's README* still names the fingerprint `908111b94170` and the constants hash `c079dbf8...` of 14:10 UTC
     (its status paragraph and the FREEZE2 section); the README is not a hashed module, but a reader of the frozen
     code will compare it with `run.py hashes`.
   * *Choices that the decisions of 06:44 to 12:52 left to the code* (its README, choices 13 to 26). New since the last
     version: which asks form H6's clusters (the asks on neither side join and link clusters, and a cluster's voice is
     drawn with the recording's share, not the cluster's; 21); how overlapping asks merge (two asks of one class on the
     same range merge too, and the merged ask keeps its members' first verdict in the order ask, unchecked, unclear,
     not ask; 22); 99,999 draws in the analysis and 9,999 in the battery (23); the `null_burst` and `null_gapped`
     scenarios (24, 25); H6's detectable-effect note from a full battery of the current fingerprint only (26); the
     fixed reading "is not" for ain't and the flat-list mask (9); the 9 seen transcripts as unknown model (12). Among the
     older ones: a creator's
     registered H5 value in the model-stratified row is the inverse-variance mean of its per-model values (the code
     verifier notes that a kept stratum can have no hits on one side, because the hit rules read the creator's totals;
     it then adds one side's log ratio, not a side contrast, with a weight of at most 0.25); for H6 a
     recording without an ask file stays in with no asks, and the jackknife and the amended bootstrap delete or draw a
     creator with all its recordings; H9's second stage draws recordings within each cell and does not reapply the cell
     rules inside a draw; A5 on both intervals applies to the amended versions only. Confirm them with the list before
     freeze 2. (H6's note from the full battery, choice 26, now also follows 15:14 (2).)
6. **Sentences of the pasted parts that could not be made true at paste time** (15:46 to 16:20 UTC).
   * A10.2, first bullet: "Before freeze 2, each hypothesis prints three things: ... and its detectable effect at the
     projected number of eligible creators, taken from the label-based repeat of the calibration (CAL part f)." CAL
     part (f) has not run and will not run before freeze 2 (15:14 (2)); the H6 exception is written in, but for H1, H2,
     H4 and H5 nothing prints a detectable effect before freeze 2 (H9's note in the code points to the battery; H7 and
     H10 are not run), and no registry row says what replaces CAL part (f) here (item 5). The rule is left as A10.2
     drafted it, because changing it is a decision.
   * Part 4, the hold-out feature step, and Part 8, the row of 15:14 (1), describe produce.py's command as the registry
     row decides it. Whether the code matches can only be checked once produce.py is final (item 4); and whether
     freeze 1 has already been written again at the paste is not known here, so both are worded to read true either way.
   * Part 8, pending list: "H9's smallest effect, which is set from seen cells". True as a pending item at the paste;
     if freeze 2 follows directly, it freezes the placeholder (item 5).
7. **For information (not for pasting).**
   * *What the quick battery on the code of 12:52 shows* (synthetic; 13:33 to 13:41 UTC; 30 null and 15 planted sets a
     row, so every share is rough; for you, not for pasting). Under all five H6 null scenarios the amended and the guarded
     p reject at 0.005 in none of the sets at 12 and 17 creators, while the ask-level reference rejects in 0.07 to 0.10 of
     the burst and gapped sets; at the smallest effect "supported" in 0.07 (12) and 0.13 (17), at the large plant 0.33
     and 0.6. The 1,000-set runs of A10.4 give the levels with more precision. The other hypotheses are as on the code of
     06:44 below.
   * *What the quick battery on the code of 06:44 shows* (synthetic; 30 null and 15 planted sets per row, so every
     share is rough; for you, not for pasting). Under the null with ask rates that differ between recordings, H6's OE
     centred per recording rejected at 0.005 in none of the sets (12 and 17 creators), CAL's pooled form in 0.04 and
     0.03 of the same sets: (3) does what it was decided for. At 0.05 the centred OE rejected in 0.08 and 0.17 of those
     sets, which 30 sets cannot tell from 0.05; the code verifier's 300-set probe of the same scenarios, without
     bootstraps, gave about 0.04. H9's two-stage interval covered its target in
     every row and blocked A5 at the smallest effect ("supported" in 0 of the sets at 12 and at 17 creators, against
     0.07 and 0.13 before), while its permutation p still rejected as before: H9 loses power at its smallest effect,
     which is still a placeholder (0.2). H6's 12-creator boundary set read "not determined (Holm step)", because its
     exact sign-flip p was 2^-7 on that one set.
