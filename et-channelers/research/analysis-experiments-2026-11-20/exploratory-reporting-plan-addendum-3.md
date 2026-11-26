# Exploratory reporting plan, addendum 3

Drafted by the collector of the exploratory round's second wave at 2026-11-22T04:43:23Z and completed by the collector
of release pass 2 at 2026-11-25T22:33:57Z (UTC, from the clock; item 9 completed in the pass's third fix step at
2026-11-26T03:57:37Z, D57 and D66), under the lead's decisions D19 and D33 to D54 (lead's
decisions of 2026-11-22; registry 2026-11-22 02:09, 05:00 and 07:15), taken by the lead under the owner's delegation.
Its SHA-256 is entered in the [registry](registry.md) by the lead with the commit that adds this file.

It belongs to `exploratory-reporting-plan.md` (SHA-256 `061bab3303a03951a57e2f05f58ca3ee86bbdba29db637117831715b6acf3c7c`)
and follows addendum 1 (SHA-256 `0a574770ad8a281e56185bb6a528c84111deb45fb46f20475fbd9f7f0f10d0f7`) and addendum 2
(SHA-256 `c35f316b35277ef6f5fd36207a135bcfbd8a3056f6186dea218184ef27341e12`). Under section 0 of the plan, items 1 to 7
correct factual errors in rows and record outputs as not run. Items 8 to 13 record readings, places and privacy rules
that the lead decided after the round's results were known; like addendum 1 item 4 and addendum 2 item 9, they hide
values or state how outputs are reported, and none selects a version of a figure by its result. The addendum adds no
output and removes no output. **No item changes a registered verdict:** the registered first-round tests ran on
2026-11-21 (18:54 to 19:03 UTC) and their results were published before the exploratory round began (2026-11-21 23:17
UTC).

Exploratory (registry A2); not a test of H1-H10.

**Timing, stated openly.** Items 1 to 7 were written after the exploratory round's first wave had run and been collected
(2026-11-22, about 02:00 UTC), so after the results of the outputs they concern, where those outputs ran. Item 3 removes
from a row a quantity that was never computed (a pool the plan's own general rule forbids); items 4 and 5 record outputs
as not run because a registered precondition was not met; item 7 records the rule by which an output was found not
eligible before any of its values was computed. Items 8 to 13 were decided by the lead on 2026-11-22 (about 05:00 to
07:15 UTC), after the round's outputs and their figures had been seen and before any of them was published, and are
written here on 2026-11-25. None of them selects a version of a figure by its result.

## 1. VER-CAL: which part of KA's confidence arm was not bought

- **What the plan says.** Section 6.5, row VER-CAL, status: "L where a confidence field exists; the KA confidence arm
  was not bought (registry 2026-11-21 02:40), so that part is X".
- **Correction.** Only the voice-label and ask-check parts of KA's confidence arm were not bought. Stated confidence
  exists in KA's battery for the forecast critic class, the checkability parts, the commitment code, the sentence codes
  and the title presentation, each read by the small and the middle model, and VER-CAL scored it against the
  constructed answers (it reproduced KA's stored ECE and Brier scores exactly). The X part of VER-CAL is the voice and
  ask-check stated confidence only.
- **Why.** KA's README lists as not bought "the confidence arm on the voice label and the ask check"; the registry row of
  2026-11-21 02:40 calls it "the confidence arm (0.35)". The plan's row took the whole arm to be missing.

## 2. DR-2: what the second reading covers

- **What the plan says.** Section 6.5, row DR-2, data: "300 forecast candidates and 400 sentence units on seen creators
  (registry 2026-11-21 02:50)".
- **Correction.** The second reading covers 300 coded statements read on the five checkability parts (time window,
  place, named actor, observable outcome, quantity), not 300 forecast candidates, and not the forecast class or the
  commitment code; and 400 sentence units. Both are seen creators of the gate sample G (registry 2026-11-21 04:55).
- **Why.** The readings on disk (2026-11-21 03:15 to 03:21 UTC, 0.62 USD) and the registry row of 04:55 show what was
  read; DR-2 rebuilt every confusion table from them.

## 3. H3-X: no pool with the seen creators (lead's decision D1)

- **What the plan says.** Section 6.9, row H3-X, measure: "Exact creator sign-flip p, leave-one-creator-out range,
  random-effects pool with seen creators, the same without the pilot-overlap recordings". Section 5 rule 4: hold-out
  results of exploratory items are "hold-out-only estimates, beside the seen estimates, never pooled with them into one
  estimate".
- **Correction.** Rule 4 stands over the row. The row's "random-effects pool with seen creators" is replaced by "the
  hold-out estimate beside the seen estimate, and their difference". The other parts of the row are unchanged.
- **Why.** The two texts conflict, and the general rule protects every hold-out replication. H3 is withdrawn from the
  claims (A6), so no claim rests on the row. The pool was never computed: package HOLD printed the hold-out estimate, the
  seen estimate and their difference when it ran H3-X (2026-11-21 23:27 to 2026-11-22 00:01 UTC), and the lead decided
  the conflict at 2026-11-22 02:08 UTC, after that run.

## 4. TL-H: the timeline procedure freeze was never made (lead's decision D2)

- **What the plan says.** Section 6.6, row TL-H, status: "F2 (after the timeline procedure freeze and freeze 2)".
  Section 5 rule 2: "the timeline's hold-out statements also need the timeline procedure freeze". Section 8, row TL-H:
  "Timeline outputs on hold-out statements (also after the timeline procedure freeze)".
- **Correction.** No timeline procedure freeze was entered in the registry before the seen timeline outputs were read.
  The seen timeline procedure was built and run in the exploratory round itself (package TL, code written from
  2026-11-21 23:20 UTC; runs 2026-11-22 01:00:15 and 01:01:47 UTC). A freeze made now would be chosen after those
  outputs were seen, which is not the freeze the plan requires. TL-H is therefore reported as "not run (precondition
  not met)". Its other reasons stand beside it: TL-SPEC's cards need model calls, and no money is left under the hard
  stop (registry 2026-11-21 18:41); the forecast class of record fails gate D on R-hold. No hold-out timeline material
  was read.
- **The procedure for a future wave.** The seen procedure as built in this round is recorded here as the procedure that
  a future confirmation wave would freeze, by these hashes, before it reads any new data. It is not frozen by this
  addendum, and no hold-out run may use it under this plan:

  | File (package TL, `code/`) | Role | SHA-256 |
  |---|---|---|
  | `tl_build.py` | Build step: statement rows from the seen forecast labels; stored FE answers matched by exact request id | `f2c7e2d96a2a596c4e839d5304538235fabe9f3dec124fb197def6019d81166e` |
  | `tl_analyse.py` | TL-BUILD, TL-7.1, TL-7.2, TL-7.4, TL-7.7 and TL-7.9 (run 2026-11-22 01:00:15 UTC) | `9548b354c11c46a38fd1653dcdf78585b452dacbfa3b0342e5e1620178c60a5c` |
  | `tl_mtmm.py` | TL-7.8, the rows for MTMM (run 2026-11-22 01:01:47 UTC) | `48f79bf190b7a87bf82c5118fad549e90760be2a336356832d96aea06a07557f` |
  | `tl_status.py` | Writer of the package README and status entries | `ca2bc400453c75130a13da266d86fa0404e385d49f4b098e0904e19bfa2558e3` |

  The choices those files fix (eligibility as addendum 1 item 6, confirmed upload days primary, the source-type mapping
  of about 00:40 UTC and the choices labelled "chosen after the result") are listed in TL's status entries. The TL
  package's public files were rerun in their release form at 2026-11-22 05:51:17 UTC (lead's decision D43); a future
  wave would freeze the procedure as of that run. It would also need TL-SPEC's cards, which need model calls.
- **Why.** Section 5 rule 2 makes the freeze a precondition of any hold-out timeline run; P3 and P4 do not allow a
  freeze to be chosen after the outputs it governs were seen.

## 5. E7: the inventory was never frozen before freeze 2 (lead's decision D3)

- **What the plan says.** Section 6.10, row E7, data: "Inventory from seen creators, frozen and hashed before freeze 2;
  hold-out edges after freeze 2"; status: "Inventory before freeze 2; scoring F2". Section 8 lists E7's hold-out part.
- **Correction.** No inventory of the seen creators' opening and closing frames was frozen and hashed before freeze 2
  (2026-11-21 16:10:00 UTC); none is in the run folder or the registry, and none can be frozen retroactively. E7 and its
  hold-out part E7-H are reported as "not run: its registered precondition (inventory frozen before freeze 2) was not
  met". E7 needs no model call.
- **Why.** E7 registers the inventory as frozen before any hold-out transcript is read; an inventory built now cannot
  meet that, because hold-out transcripts have been read since (the exploratory round's logged contacts).

## 6. Section 6.11: the rows that will run in this study

- **What the plan says.** Section 6.11: "Rows that will run in this study:", followed by eleven rows: MR-18c, MR-18d,
  nlp-R7, nlp-R9, nlp-R10, nlp-R11, nlp-R13, CSS-5, CSS-10, CSS-11 and CSS-12.
- **Correction.** Two parts of that list will not run in this study: CSS-11 (its own status is N: it needs a new codebook,
  and model calls, with no money left under the hard stop, registry 2026-11-21 18:41) and the directive part of CSS-12
  (its own status marks it X: DIR's go rule failed). The rest ran: nlp-R9 is carried by LAB-F (first wave of the
  exploratory round); MR-18c, MR-18d, nlp-R7, nlp-R10, nlp-R11, nlp-R13, CSS-5, CSS-10 and CSS-12's census part ran in
  the round's second wave (lead's decision D4, registry 2026-11-22 02:09).
- **Why.** The heading says "will run" of rows whose own status says that they, or a part of them, will not.

## 7. BR-b-H: eligibility before any rate, and its status word (lead's decisions D5 and D33)

- **What the plan says.** Section 6.7, row BR-b, status: "R on seen creators; hold-out and other-group part F2
  (BR-b-H); reported as not run, with the reason, if the human-made texts cover fewer than 5 creators". Section 8, row
  BR-b-H: "Word error rate on hold-out and other-group recordings with third-party text". Addendum 1 item 2 moved the
  human-reference part to BR-b-H, with the references "classed from the same receipt fields, without reading their
  text, before any word error rate is computed on them"; addendum 2 item 10 gives the classing rule. BR-b-H needs the
  local recognizer over archived audio, not a model API call.
- **Correction.** BR-b-H runs in this order. First, the hold-out's and the other group's references are classed as
  addendum 2 item 10 requires, from metadata and reference files only, without opening audio and without running the
  recognizer. If fewer than 5 hold-out creators (or, separately, other-group creators) would carry a rate, the
  recognizer does not run for that part. Only an eligible part runs the local recognizer, with BR-b's settings, as one
  locked job, with a memory check before it starts; its audio and reference reads are hold-out contacts.
- **Status word (D33).** The plan's BR-b row governs: a part found not eligible is "reported as not run, with the
  reason". D5's word "not released" is corrected to "not run: fewer than 5 creators in each group have a reference that
  could be made by people; the recognizer was not run". This covers every hold-out and other-group part of BR-b, its
  machine-agreement rows (agreement of two machines, not an error rate) included. BR-b's seen rows stay as built.
- **What it gave.** Package BRBH classed the references on 2026-11-22 (02:16 to 02:43 UTC) with BR-b's classifier
  unchanged, after the same code had reproduced BR-b's seen classes. In each group the references that could be made by
  people rest on under 5 creators (0 to 4), even when every caption whose receipt leaves its maker open is counted as
  made by people. Neither part is eligible, so no audio, text bundle or reference text was opened and the recognizer was
  not run. BR-b-H is reported as not run, with that reason.
- **Why.** A recognizer pass over hold-out audio is a heavy local job and a set of hold-out contacts; under the
  5-creator rule it could produce no publishable rate for a part that is not eligible.

## 8. Hold-out positional outputs after freeze 2 (lead's decision D40)

- **What the record says.** The owner's positional rule of 20 November 2026 showed displays of speech by position in
  the recording for the seen creators only "until freeze 2" (corrections file, item C10). The plan registers hold-out
  positional outputs for after freeze 2: rv-D3-H (section 8) and H3-X (section 6.9), and in the round's second wave E3-H
  (section 8; lead's decision D4). The results README still left the owner's confirmation open and said that no other
  positional estimate on the hold-out is published.
- **Reading.** The rule ran until freeze 2 by its own terms and lapsed there (2026-11-21 16:10:00 UTC). The hold-out
  positional outputs of the round are published as exploratory outputs, beside the seen ones, never pooled with them
  (section 5 rule 4) and never called a confirmation. The stale sentence of the results README is replaced by a
  statement of the lapse at freeze 2 with a pointer to these outputs.
- **Why.** The plan registered these outputs; the rule that had held them back was bounded in time.

## 9. Creator-count pairs that were public before the round (lead's decisions D45, D57 and D66)

- **What the rule says.** The round's nested-count rule: no two printed creator counts of nested groups differ by 1 to
  4, also against counts already public (applied to groups that are subsets of each other, D44).
- **Pairs that were public before the round.** H3's seen counts 61 and 64; the 17 creators of H3's hold-out row beside
  the 18 English hold-out creators; 23 hold-out creators minus 18 English ones, which is 5, beside the public count
  of 6 creators with non-English transcripts (the difference is the hold-out creator with one non-English recording
  among English ones, D16, with no value attached); the 36 pairs of the recognizer bridge, 35 of seen creators and
  one of an other-group creator (the registered plan's rv-R3 row and the paper; no value of the one creator is
  printed); and COR's within-channel level, 69 seen creators with 5 or more recordings, beside the 71 seen
  creators (the registered plan's COR row). These were printed in published files before this round.
- **Not checked (D66).** Whether H3's seen sets of 61 and 64 creators are nested, in fact, with seen groups of 57 to
  66 creators printed in the release cannot be checked without a hold-out contact: H3's per-recording eligibility
  sits in files that also hold hold-out rows. They are not nested by definition; the question is listed here with
  the pairs above.
- **Reading.** They stay as published. No new file prints such a pair for the same measure. They are listed among the
  owner's items, because the published files that print them are not edited by this plan.

## 10. Places of the main-text outputs (lead's decision D54)

- **What the plan says.** Section 3 and each output's row fix its place; P7 allows a whole main-text output to move to
  the supplement with a one-line pointer left in the main text, and the move logged.
- **What is done.** The paper's main text was written before the release and is not expanded. Outputs with an M place
  are published in the release (`results/exploratory-2026-11-21/`) and its gallery; the paper's results section gets
  one paragraph that points to them, and its appendix B.10 cites them by id. This is a deviation: the outputs are less
  prominent than registered. It was decided for reasons of timing, not of any result, and applies to every M output
  alike. The dashboard shows one figure of each overlapping pair (decision D24), which overrides the place column for
  those picks; RX has no dashboard figure, KA-2 stays in the supplement, SD-fig-3 goes on the dashboard, and
  rv-L1-fig-1 is in the supplement only.
- **Why.** P1 asks that every output be reported whatever it shows; a release with a pointer reports every output in
  full, where a rewrite of the main text could not be finished before the release.

## 11. Privacy screens added after results (lead's decision D46)

- **Added after results, for privacy only.** Two screens join the rules of plan section 3 and addendum 2 item 9: the
  dominance screen (no printed cell in which one creator provably holds half or more of the total) and the thresholds of
  the joint audit of the built items of group B-LV (rv-L1 to rv-L3, VER-3R, VER-A, VER-GC, VER-SHARD and TL-P). They
  were decided after results had been seen, like addendum 2 item 9, and are labelled "added after results".
- **Effect.** Neither changes an estimate; each can only withhold a printed value. The dominance screen runs over every
  release file before publication.

## 12. BR-GS's scope and BR-b's recognizer-confidence halves (lead's decision D52)

- **BR-GS.** The lead's words "nothing more specific" cover BR-GS's precision check of the positional filter and its
  thanks-phrase row, whose public form is fixed (addendum 2 items 4 and 7). The other BR-GS measures pass every rule and
  are released, as P1 requires.
- **BR-b's confidence halves.** Addendum 1 item 1 reports the recognizer-confidence stratum of BR-b "as built". Its
  halves of the caption row were withdrawn after the release verification of 2026-11-22: beside the length halves, a
  second split of the same creators would bound cells of fewer than 5 creators. This is a departure from addendum 1
  item 1 (less reported), for privacy only, recorded here and in the registry's deviation table.

## 13. Projections and two-series histograms (lead's decision D51)

- **Projections.** rv-R2's projected eligible counts are printed as "simulated projections, not counts of creators".
- **The pairs rule for two series.** The pairs rule of addendum 2 item 9 ("of two printed rows whose difference rests on
  1 to 4 creators, one is not printed") is read as covering cells whose per-creator values differ in 1 to 4 creators.
  It does not cover the bins of two histograms of different series whose memberships differ, as package HOLD read it.
  The reading hides no value that the rule as worded would show and was fixed before release.

## Not in this addendum

- The owner's exception of 2026-11-22 02:22 UTC (registry), which released E9's hold-out part although its base has
  fewer than 5 creators, is a registry decision, not a factual correction; it is recorded in the registry and in the
  release's status table.
- The exploratory round's departures from rules (code written after freeze 2 for F2 outputs, the stricter small-cell
  rules, scope cuts, post hoc choices, the agreement recount of decision D48, the CSS rerun of decision D35, the parts
  not built of decision D55) are entered in the registry's deviation table and in the release's `deviations.md`, not
  here. The round's hold-out contacts are entered in the registry's contact log and in the release's `contacts.md`.
- Wording: plan P9 gives its own verb for the line that no person checked the labels; the round's files say "not
  checked by a person", the wording the owner's rules require, which keep that verb out of every file.
