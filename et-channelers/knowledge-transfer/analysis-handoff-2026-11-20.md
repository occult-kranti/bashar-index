# Analysis handoff, 20 November 2026 (evening)

Where the analysis of the latest-20 cohort stands, what runs next, and the rules that bind whoever continues.
Written at about 22:30 UTC on 20 November 2026. The branch `feat/partial-cohort-asr-2026-11-20` was merged
into `main` the same evening ([PR #95](https://github.com/occult-kranti/bashar-index/pull/95)); later work
continues on that branch and reaches `main` by pull request.

## In one paragraph

Downloads are closed: 1,946 of the 1,976 selected recordings are archived, and the owner declared the other 30
final failures. The local speech-to-text run finished at 19:56 UTC and transcribed 1,697 audio files
(742.9 hours, 5.83 million words, seven languages). A bridge of 36 recordings through both recognizer models
shows which measures can be compared across them. A registry of ten hypotheses was frozen before the
last-transcribed creators were analysed; one hypothesis (H3) was tested and then dropped by the owner. Labels
for the other hypotheses are to be made by language models through the OpenAI API within the owner's budget (120 USD
that evening; since 21 November a hard stop at 130 USD with a warning at 120 USD, see the updates below); the
labelling instruments were then built, piloted once on already-seen creators and being revised. An expert panel
has started deliberating on the second round of analysis, which the owner widened to include regular
expressions, topics across channels, metadata, weekly and monthly change, correlations, and date comparisons
kept apart for confirmed and estimated dates. Spent on the API so far: about 2 USD.

## Updates of 21 November 2026, from the registry

This handoff describes the evening of 20 November. These rows of the
[registry](../research/analysis-experiments-2026-11-20/registry.md) (times UTC) supersede what it says about money,
the interface and freeze 1:

- **Budget (02:00).** The owner's total OpenAI budget is 130 USD, a hard stop in the client, with a warning at
  120 USD. The large production runs (forecasts, sentence codes, titles, seen-creator voice and ask labels) go
  through the batch interface at half price. At 04:55 the hard stop and every tag cap became checks at worst case,
  with every open batch job counted at its worst cost.
- **Freeze 1 (04:58).** The instruments were frozen at 04:58:22 (record `llm/freeze.json` in the private run folder).
  The cross-vendor voice check VG-6 passed at 04:59 (kappa 0.91, 90% creator-bootstrap 0.84 to 0.95). Freeze 1 unlocks
  the seen creators' labels; hold-out and other labels wait for freeze 2.
- **Production (05:00, 06:33, 06:39).** Seen-creator production started through the batch interface at 05:00. At 06:33
  the voice map and the forecast chain moved to the standard interface, and at 06:39 the sentence codes and the asks
  find and its small-model check followed. The small model's batch queue was the bottleneck: after 80 to 85 minutes
  it had returned no answer for the voice map or the forecast find, and later about 1,100 sentence-code answers in
  46 minutes with about 54,000 left. The middle-model stages and the title stages stay in batch.

## Done

| Item | Result | Where |
|---|---|---|
| Downloads | Closed by the owner on 20 November: 1,946 of 1,976 archived; the 30 outstanding are final failures and are not retried | [collection close](evidence/2026-11-20-close/) |
| Transcription | Done 19:56 UTC: 1,697 of 1,729 audio files, 742.9 of 746.3 hours. English 1,616; six other languages 81, pooled (each is spoken by fewer than 5 creators). 12.6% of the audio holds no speech. 32 recordings not transcribed (19 with no speech found in the whole recording, 13 held back for another reason: two plausible languages, no reliable speech or failed word alignment, pooled because each reason concerns fewer than 5 creators) | [progress table](partial-cohort-asr-progress.md), [run report with 12 figures](../research/transcription-run-2026-11-20/README.md) |
| GPU clean-up | Run lease released; the earlier lease and pause marker restored byte for byte (SHA-256 `37996ca3…` and `8bd53103…`); the run's scheduled task removed. The collector's stop marker and the disabled download tasks are untouched | private run folder |
| Recognizer bridge | 36 English recordings transcribed by both models, none failed. By the rule fixed beforehand, 7 of 17 measures agree within 0.2 between-creator standard deviations (pace, pronoun rates, contracted forms, word variety and length), 6 differ (pauses, word duration, segment length, filled pauses: the larger model writes about 4.5 times as many), 4 are not settled. The two transcripts differ in 3.5% of words at the median | [results](../research/analysis-experiments-2026-11-20/results/README.md#br-the-two-recognizer-models-on-the-same-audio) |
| Registry | Ten hypotheses H1 to H10 and thirteen exploratory questions frozen 19:47 UTC, with amendments A1 to A7 (model-coded labels instead of human markers; pruning keeps a results row; the budget, now 120 USD; what waits for new data; stricter verdict rule; H3 dropped; the second round belongs to the panel, with the owner's additions) | [registry](../research/analysis-experiments-2026-11-20/registry.md) |
| H3 | Tested on the 17 English hold-out creators with code frozen beforehand: estimate 0.169, 90% interval −0.130 to 0.495, shift-test p 0.0007; the 61 seen creators give 0.019. Supported by its registered rule, fragile, and dropped by the owner. It keeps its row and counts as run for the Holm correction | [results](../research/analysis-experiments-2026-11-20/results/README.md) |
| Experiment catalogue | 28 experiments under 16 rules, designed by the first analyst panel | [catalogue](../research/analysis-experiments-2026-11-20/README.md), [ANALYSIS_PLAN.md section 13](../ANALYSIS_PLAN.md) |
| Paper draft | 17 pages, ICWSM format, with the H3 test and the bridge; findings from the run snapshot marked preliminary | [paper/cohort-draft-2026-11-20](../paper/cohort-draft-2026-11-20/) |
| Dashboards | Findings dashboard on GitHub Pages (PRs #93 and #94 on `main`), with a "Tests and checks" tab; a private hosted copy for the owner | [findings dashboard](https://occult-kranti.github.io/bashar-index/et-channelers/dashboard/findings/) |
| Labelling instruments, round 1 | Voice spans (who speaks: own voice, a being's embodied voice, a relayed voice, others) and asks (requests to buy, enrol, give, subscribe or move off the platform) built and piloted on 32 recordings of seen creators. The two models agree on 79% of words (kappa 0.74), on own, embodied and relayed voice 88% (kappa 0.81); the ask finder found 48 of 49 reference asks. The reference labels were made by a language model, not a person | private `llm\pilot\` |
| Labelling critique | A critic wrote 27 required changes. The two that matter most: counting the creator's own offers as evidence of the own voice would make H6 partly true by construction; requiring a cue for the own voice sent 28 to 43% of own-voice words to "cannot tell". Both are fixed in the revised prompts | private `llm\design\annotation-plan.md` |
| Error analysis | The two models' disagreements were read: 57% come from conversations with several speakers, for which the codebook had no rule. Eight prompt changes were written from it | private `llm\prompts-next\CHANGES.md` |
| Code review | 32 findings on the labelling code. Those in the request runner and the ledger are fixed: a lock between processes, reservations before sending, a batch job settled once, vendor files deleted. The rest are being applied | private `llm\design\review-findings-2026-11-20.json` |
| Parallel requests | The API allows 10,000 requests a minute on both models. The runner now keeps up to 64 requests in flight on the small model and 32 on the middle one; 120 test requests took 4 seconds | private `llm\runner.py` |

## Running when this was written

These were background agents of one Claude Code session. If that session has ended, check whether their output
exists and redo what is missing.

| Work | Writes to | Done when |
|---|---|---|
| Revision of the voice and ask code to the revised prompts, the critic's changes and the review findings, checked by two independent testers | private `llm\` (`prep.py`, `voice.py`, `asks.py`, `produce.py`, `pilot_voice.py`, `tests\test_pure.py`, `prompts\`) and `research\analysis-experiments-2026-11-20\code\artefact_filter_v2.py` | `python -I tests\test_pure.py` passes and `prep.py` loads `artefact_filter_v2` |
| Forecast, sentence-code and title labellers, piloted on seen creators within 2.50 USD | private `llm\forecasts.py`, `content.py`, `titles.py`, `fc_common.py`, `pilot\` | its report; the recording-kind screen was dropped on the critic's advice |
| Second-round expert panel: statistician, computational linguist, computational social scientist, measurement methodologist and skeptic, two rounds each, then a chair | private `panel-second-round-2026-11-20\` (memos, responses, `programme.md`) | `programme.md` exists |

## Next, in order

1. **Pilot round 2 on seen creators only.** Run the revised voice and ask instruments on the 32 development
   recordings and on the check sample (40 recordings plus one of every creator neither designer read). Run the
   single-factor experiments of the labelling plan, section 4.1: reasoning effort none against low, the plain
   against the guided-fields variant, the middle model with its own map, the text variants (contractions
   visible, names masked, fillers removed, punctuation removed, positions hidden, filter off). Decide each by the
   rule written before the run. No hypothesis quantity is computed on pilot labels.
2. **The owner's decisions before the first freeze** (list below).
3. **Freeze 1.** `python -I produce.py freeze` writes the hashes of every prompt, schema, model setting and code
   file; copy them into a procedure entry in `registry.md` and commit before any hold-out recording is
   labelled. *Done 21 November, 04:58 UTC (registry, "Freeze 1 (instruments)").*
4. **Label the seen creators**, then **freeze 2** (constants computed from seen labels: H4's yardstick, H2's
   length bands, eligible sets, join rules), then **label the hold-out and other creators**, then the
   reliability checks on the hold-out. The labelling plan's stop rule applies: at most 45 USD committed.
5. **Run H1, H2, H4, H5, H6 and H9** with the stricter verdict rule of amendment A5. Every result is called
   model-coded and not validated by a person. Update the results table, both dashboards and the paper.
6. **Second round.** Carry out the panel's programme: the analyses without a language model first (regular
   expressions, topics compared across every channel, distributions, metadata joined to the recordings, change
   by week and by month inside each channel's span, correlations, same-date comparisons kept apart for
   confirmed and estimated dates), then the panel's language-model experiments within the 48 USD experiments
   cap.
7. **Later:** the replication wave (H7, H10, and confirmation of the others), the comparison set (H8), the pass
   over the recordings held in other text kinds, latest-50.

## Rules for whoever continues

- **Hold-out.** Freeze 1 was written at 04:58 UTC on 21 November; it unlocks the seen creators' labels only.
  Until freeze 2, open transcripts and titles only of the 71 seen creators (`creator-sets.json` in the private
  `llm` folder). The 23 hold-out creators and the 6 others may be counted only by ledger fields (durations,
  dates, languages). `prep.load_words` will refuse other recordings before the freeze.
- **Privacy.** Transcript text, creator names, video ids and titles stay private. Public outputs carry counts by
  category, distributions (quantiles, binned histograms, two-dimensional bins with at least 5 creators per occupied
  bin), cohort-level estimates with intervals and per-language rows. No public file, chart or table has a row,
  point, cell or label per creator, a row per recording, a creator code of any kind, a video id beside anything
  derived from a transcript or the run, or a top or bottom list of creators (the owner's decision of 20 November
  2026, "replace and tighten": the earlier creator codes could be broken). Speech-by-position displays use the
  seen creators only until freeze 2. Added after the privacy review of the same day: every number the run or a
  transcript measured rests on 5 or more creators. Since 21 November (paper review, task D7) no public row, bin or
  cell describes fewer than 5 creators, even with counts only: a language of fewer than 5 creators has no row of its
  own (every language but English is pooled into one row), and outcome reasons and read-sample kinds are pooled the
  same way; choose bins so that nothing needs suppressing, because suppressed cells can be solved from public
  margins (`run_report.py` checks this with `pinned_cells`); merge adjacent bins of a histogram until each holds 5
  or more creators; and print no minimum or maximum of a transcript measure (use the 10th and 90th percentiles),
  since an extreme is one creator's or one recording's value and can be tied to a name through public lengths. Transcript text goes to an outside service only for the
  OpenAI labelling the owner ordered, with `store` false; batch files are deleted at the vendor after collection.
- **Money.** The key is the owner's own file `%USERPROFILE%\Downloads\gpttoken.txt`, read in place; never copy,
  print or commit it, and suggest that the owner revoke it when the work is finished. Every request goes through
  `openai_client.py` and `runner.py`, whose ledger (`spend.jsonl`) reserves the worst case before sending.
  The owner's budget is 130 USD in total, a hard stop in the client, with a warning at 120 USD (registry,
  21 November 02:00); the hard stop and every tag cap are checked at worst case (04:55). Large production runs go
  through the batch interface at half price; the registry rows of 06:33 and 06:39 moved the voice map, the
  forecast chain, the sentence codes and the asks find and its small-model check to the standard interface.
  (On 20 November the caps in code were labelling 60 USD, experiments 50 USD and setup 4 USD, under a limit of
  120 USD.) Check `python -I openai_client.py --spend` before and after any run.
- **One process per answer-store tag.** Two processes on the same tag were what damaged a store line in round 1.
- **Wording.** Results on model labels are *model-coded*; agreement between two models is reliability, not
  validity. The creator is the unit of inference. A creator's newest 20 recordings can span three days or
  fifteen years, so change by week or month is described per channel and never called a trend. Languages other
  than English are described, not tested. Pause, word-timing and filler measures are not compared across the two
  recognizer models.
- **Machine.** The owner stopped and disabled the Codex jobs and their scheduled tasks on this machine on
  21 November 2026 (01:45 UTC; record `stopped-by-owner-20261120.json` in the private run folder); do not restart
  or re-enable them. Do not stop other processes or scheduled tasks you did not start. The collector's stop marker
  and the disabled download tasks stay as they are.

## Decisions waiting for the owner

1. *Decided 20 November:* the branch was merged into `main` (PR #95), and the budget was raised to 120 USD.
   *21 November, 02:00 UTC:* 130 USD in total as a hard stop in the client, with a warning at 120 USD.
2. Before freeze 1, from the labelling plan, section 6: which own-voice rule is primary (cued only, or also
   uncued solo speech outside the claimed voice); which offer rule is primary for H6 (the prompts now record
   offer-only cues so that both can be computed); the primary voice model on the hold-out; the claimant classes
   that enter H1, H4 and H6; H4's yardstick; the reliability floors; seen creators labelled before the hold-out.
3. Whether H8 keeps its place now that H3, whose contrast it compares, is dropped. *Decided 20 November, about
   22:45 UTC (registry A9): H8 is dropped.*
4. Who, if anyone, codes the small human sample (about four hours for the voice labels); it is the one addition
   that changes what H1, H4 and H6 may claim. *Decided 20 November, about 22:45 UTC (registry A8): no human check.*
5. The capture date of the replication wave (proposed 20 February 2027) and the roster of the comparison set.
6. The recordings with two plausible languages and the recordings held in other text kinds.

## Where things are

| What | Path |
|---|---|
| Transcripts (zip bundles) | `%USERPROFILE%\et-channelers-private\asr\results\` (bridge transcripts under `bridge-large-v3-20261120\`) |
| Run folder: supervisor, progress, bridge, dashboard builders, panel notes | `%USERPROFILE%\et-channelers-private\provisioning\claude-cohort-asr-20261120-v1\` |
| Labelling code, prompts, pilot reports, answer stores, ledger | the run folder's `llm\` (design documents in `llm\design\`) |
| Second-round panel | the run folder's `panel-second-round-2026-11-20\` |
| Worktree of this branch | `%USERPROFILE%\et-channelers-tools\partial-cohort-asr-20261120\` |
| Checkout used to deploy the dashboards | `%USERPROFILE%\et-channelers-tools\site-findings-20261120\` |
| Registry, results, analysis code | [`research/analysis-experiments-2026-11-20/`](../research/analysis-experiments-2026-11-20/) |
| Run report and figures | [`research/transcription-run-2026-11-20/`](../research/transcription-run-2026-11-20/) |

Commands that change nothing:

```powershell
$run = Join-Path $env:USERPROFILE 'et-channelers-private\provisioning\claude-cohort-asr-20261120-v1'
Push-Location (Join-Path $run 'llm')
python -I openai_client.py --spend     # money committed per phase
python -I runner.py --reservations     # reservations not yet settled
python -I runner.py --batches          # batch jobs and their state
python -I produce.py status            # frozen or not, recordings labelled per group
Pop-Location
```
