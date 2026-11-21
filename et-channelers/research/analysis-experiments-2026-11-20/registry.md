# Registry of hypotheses: frozen 2026-11-20

This file freezes the registry that rule R2 of the experiment catalogue requires. It was made before any
transcript of a hold-out creator was analysed.

## What is frozen

| Item | Value |
|---|---|
| Frozen at | 2026-11-20 19:47 UTC, repository commit `b0970fe` |
| Text of the hypotheses | [`hypotheses.md`](hypotheses.md), SHA-256 `831ed6fa718e83e7f21720b8be783cc35d7d3e107d6218947c536d50319ef713` |
| Confirmatory hypotheses | H1 to H10 as stated there: claim, direction, estimand, unit, reference distribution, refuting result |
| Registered exploratory questions | E1 to E13 as stated there; none takes a confirmatory place |
| Smallest effects of interest | the values marked "proposed" in the text are adopted as written; the two placeholders (H7, H9) are set from the seen creators before their tests and recorded here when set |
| Multiple comparisons | Holm correction over the confirmatory hypotheses that are run |
| Hold-out | the 23 creators with at most 3 of the first 1,213 finished transcripts and 10 or more recordings still to come at that point; 17 of them have only English transcripts in the finished run |

The owner's instruction, given on 2026-11-20 after reading the ten candidates: *add the ten, add all, and remove
those whose findings turn out meaningless; use that to improve further; use the ChatGPT API for annotation and
labelling, studying current research on it first; at most 110 USD in total.*

## Amendments made by that instruction

**A1. Labels come from a language model, not from two human markers.** The catalogue's rule R7 asked that no
label be used before two people had measured its precision and recall. The owner has decided that span labels
(a being's voice, relayed or embodied, against the creator's own voice), forecast statements with their
checkability and commitment, asks, and sentence codes are produced by prompts to a language model through the
ChatGPT API. Consequences that this registry fixes:

* Every result that rests on such labels is called *model-coded* wherever it is reported, and states that no
  person has validated the labels, unless and until a human-checked sample exists.
* Reliability is reported as agreement between two different models given the same codebook, and as stability
  of one model across repeated runs. Agreement between models is not validity, and the reports say so.
* Prompts and codebooks are developed only on recordings of the 71 seen creators. They are frozen, with the
  code, by hash in a second entry below before any hold-out recording is labelled or analysed.
* A human check remains open: if the owner or anyone else codes a sample by hand, precision and recall are
  measured on it and estimates are corrected for misclassification.

**A2. Pruning.** After the tests, hypotheses whose findings are uninformative are removed from the headline
claims of the paper, as the owner asked. So that the removal cannot bias what is reported, every registered
hypothesis keeps one row in a results table with its estimate, interval and verdict, including the ones
removed, and the paper says how many were tested and how many are discussed. Anything changed or added after
seeing results is labelled exploratory.

**A3. Budget.** 110 USD at most: about 50 for the labelling, about 50 for experiments. A ledger records the
cost of every request, and the code refuses work that would pass a cap. *Changed by the owner on 2026-11-20 at
about 22:30 UTC:* "total budget is 120, spend and optimize", in answer to the measurement that many requests
sent at once on the standard interface cost about 1.5 times the batch price. The caps in code are now 60 USD for
labelling, 50 for experiments, 4 for setup and 115 in total, five below the limit.

**A4. What cannot run yet.** H7 and H10 need the replication wave (later uploads). H8 needs the comparison set.
They stay registered and unrun. H1 to H6 and H9 can run once their labels exist; H3 needs no labels.

**A5. Stricter verdict, added 2026-11-20 after H3 was tested.** H3 passed its registered shift test on the
hold-out while its interval over creators included zero and the larger seen sample showed nothing. For every
hypothesis not yet run, "supported" therefore also requires the 90% interval over creators to exclude zero.
H3's own verdict is reported as registered, with this weakness stated beside it in
[`results/README.md`](results/README.md).

**A6. H3 dropped by the owner, 2026-11-20.** After reading the result the owner's instruction was: *drop H3*.
Under A2 this means:

* H3 leaves the claims of the paper. Its row, estimate, interval and registered verdict stay in the results
  table, and the paper says that one hypothesis was tested and withdrawn.
* H3 is closed. It is not tested again as a confirmatory hypothesis, on the replication wave or anywhere
  else; any later look at the same contrast is exploratory and is labelled so.
* The untrimmed observation (more first-person singular in the first and last three minutes of a
  recording) stays as a description of how recordings open and close. It is not a claim about channelled
  speech.
* Holm correction counts H3 as one hypothesis that was run: dropping it does not make the thresholds of
  the others easier.
* H8 compares the H3 contrast with sermons and wellness talks. It stays registered and unrun; whether it
  keeps its place now that H3 is dropped is an open decision for the owner, and nothing is changed here.

**A7. Who proposes the second round of experiments, 2026-11-20.** The owner's instruction, given with A6:
*give the panel experts control and the second experiment budget (50 USD) after the initial analysis, the
hypothesis results and the dashboard are in; let them find flaws, improvements, further meaningful analysis
and language-model experiments on the collected data.* Everything that panel adds after seeing results is
exploratory by A2, stays inside the cap of A3, and follows the hold-out rule of A1.
The owner added the same day: the panel is also to consider, and where worthwhile implement, analyses by
regular expression (pattern counts over the transcripts), further topic analysis, comparisons, distributions, and analysis of all recording metadata joined to the transcripts for the
recordings that have it; and the panel deliberates in two rounds, each expert first proposing and then answering
the others.
A further addition the same evening: change from week to week, correlations, and the topics discussed compared
across every channel. Rule R3 of the catalogue still holds: a creator's newest 20 recordings can cover three days
or many years, so weekly change is described inside the weeks covered and is not a trend of the field.
Then: change by month as well as by week; and every analysis that uses dates is made twice and kept apart, once
on recordings whose publication date is confirmed to the day (including recordings of different channels published
on the same date), and once on recordings whose date is only estimated.

**A8. No human check, by the owner's decision of 2026-11-20 (about 22:45 UTC).** Asked whether a person would
code a small sample (about six hours: 200 voice units, pattern hits, a listening sample), the owner answered:
*skip it*. So no label is checked against a person. Every result that rests on model labels is reported as
model-coded and not validated by a person, and the strongest verdict available to H1, H2, H4, H5, H6 and H9 is
"supported (model-coded)" or "refuted (model-coded)". The only check of accuracy is the known-answer battery of
the second-round programme (texts with constructed answers), which measures the labellers on texts that are not
the corpus. The sample design stays on file in case a person becomes available.

**A9. H8 dropped, and the stricter amendments approved in principle, by the owner on 2026-11-20 (about 22:45
UTC).** H8 compared the H3 contrast in channelled recordings with sermons and wellness talks. The second-round
panel showed that the H3 contrast is biased (its mean under its own reference is -0.063, not zero) and that the
registered rule ignores differences between creators; H3 is closed (A6) and the comparison set has not been
collected. H8 is dropped and keeps a row in the results table as dropped; it counts as run with p = 1 for the Holm
correction. The owner also approved, in principle, the panel's amendments in the stricter direction for the
hypotheses not yet run: a creator-level sign-flip p-value enters the Holm correction, whose count is fixed at 10
with unrun hypotheses at p = 1; the outcome "not determinable: too few eligible creators"; the conditional
binomial estimator with a minimum-hit rule for H5 and H6; a kappa gate on point estimate and lower bound; H7's
estimator, reference and margin. Their exact text is drafted by the panel's calibration item and entered here as
A10 before freeze 2; none of them may make a verdict easier to reach.

**Primary definitions for H1, H4 and H6, chosen by the owner on 2026-11-20 before any label of the frozen
instrument exists.** Own voice: *broad* (speech with an own-person cue, and uncued solo speech outside the
claimed voice in recordings whose claimant is the sole speaker or the host). Offers: a passage whose only evidence
is the creator's own offer does *not* end a claimed voice. The other definitions (strict own voice; labels as the
model gives them) are computed and reported beside the primary ones as rows. These are constants of freeze 2.

**A11. Verification by language models, and a timeline of predictions, added by the owner on 2026-11-20 (about
22:50 UTC).** The owner's words: *use LLM based experiments and verifications to solve any limitations, LLMs are
better than human annotators - study research papers and use prompting engineering and sota guided cot and other
techniques and add timeline prediction as well as other analysis.* So the place of the human check (declined in
A8) is taken by verification with language models: known-answer texts, a third and larger model as adjudicator,
guided chain of thought, self-consistency, prompt variation, and estimates of each model's error rates from their
agreement. Results then name the verification that was done and its figures, for example "model-coded, verified by
a third model and on known-answer texts". A timeline of dated predictions in the recordings is added as an
exploratory analysis (A2): what is predicted, for when, by which channel, and for dates that have passed, whether
the predicted event is documented. Neither changes a registered hypothesis or makes a verdict easier to reach; the
verification figures enter the multiverse and tipping-point rows that the plan already requires.

**Selection rule of the cohort, stated by the owner on 2026-11-20 (about 23:10 UTC).** The owner's words:
*selection rule is channeling mediums*. The 101 creators were chosen as channelling mediums: creators who publish
recordings presented as messages channelled from non-human beings (extraterrestrial civilisations and councils,
archangels and angels, ascended masters and similar sources). The same evening the owner asked for a hashtag and
search discovery of further channelling mediums (#channeling, #pleiadian, #galacticcouncil, #raphael and the
like); its finds are candidates kept apart from the frozen cohort, which does not change.

**Budget as a warning, by the owner on 2026-11-20 (about 23:10 UTC):** *parallely implement all the llm based
experiments, dont worry about the usd token limit, use that as warning.* The caps of A3 now warn instead of
stopping; one guard at 250 USD stops only a fault that sends requests in a loop. Money changes nothing in the
registered procedures.

**Owner decisions before freeze 1, 2026-11-21 (about 01:00 UTC), after the pilot of the forecast and title
instruments.** Two instruments failed the two-model gate after both allowed prompt revisions: the checkability
parts of H2 (time window kappa 0.55, place 0.29, floor 0.60) and the title codes that split recordings for H5 and
group creators for H9 (presentation kappa 0.45 and stability 0.87 on the check creators, floors 0.70 and 0.90).
The owner chose: for checkability, the middle model codes every statement and is the record, and the largest model
with guided chain of thought re-reads a sample of about 300 statements to measure how often the record is right;
for titles, the middle model is the record and the largest model decides every title on which the middle and small
models disagree. Both are reported with their failed gates and with the adjudication figures (amendments A8 and
A11). The voice label moved more under removed punctuation and capitals than between two runs (4.3% of words
between claimed and own voice against 1.0%, check sample, small model); by the plan's rule the sentence "the voice
label responds to punctuation and case" goes with every result of H1, H4 and H6.

## Procedure freeze

One entry per hypothesis, written before that hypothesis touches a hold-out transcript. For the hypotheses
that need labels the entry will also hold the hashes of the codebooks and prompts and the model identifiers.

### H3, frozen 2026-11-20 20:38 UTC (needs no labels)

| Item | Value |
|---|---|
| Analysis code | [`code/h3_position.py`](code/h3_position.py), SHA-256 `d1cc2b2e2b2e6ff22d4d648457c1004b526ae9e28b36293269d5df2748460d6e` |
| Artefact filter | [`code/artefact_filter.py`](code/artefact_filter.py), version 1, SHA-256 `72bccae081dbbcbaa3923e1354f330498fcb20739cf1d88083f8ccba0b73e0f1`; its precision and recall are not measured |
| Choices the text left open | all in the `PROCEDURE` block of the code: all ten bins need 50 words; a half count keeps a zero rate finite; first-person singular is the nine forms listed there; 9,999 shift draws and 9,999 bootstrap draws with seed 20261120; the verdict rule |
| Seen creators, exploratory | trimmed U 0.019 (90% interval -0.129 to 0.165; 61 creators, 558 recordings; 36 creators positive). Untrimmed U 0.427 (0.248 to 0.608; 64 creators). File [`results/h3-seen-exploratory.json`](results/h3-seen-exploratory.json) |
| Hold-out, counted before the test | 17 creators and 169 recordings are eligible. With the between-creator spread seen above (SD 0.66) the standard error is about 0.16: the test can detect a U of about 0.54 at the registered threshold with 80% power, and a 90% interval will be about 0.26 wide on each side. So it cannot return "negligible", and it can support H3 only if the effect is several times the smallest effect of interest |
| Interval procedure | percentile bootstrap over creators, then recordings; its coverage has not been audited (the coverage audit CA has not run) |
| Result, run 2026-11-20 20:39 UTC with the code above | U 0.169 on 17 creators and 169 recordings; 90% interval -0.130 to 0.495; shift p 0.0007; 9 of 17 creators positive. Supported by the registered rule, and fragile: see [`results/README.md`](results/README.md) |
| Decision | dropped by the owner on 2026-11-20 (amendment A6): out of the claims, row kept, closed |

## Hold-out contact log

Every time a file, figure or table touched recordings of the 23 hold-out creators (or of the 6 other creators)
outside a procedure frozen for that purpose, it is listed here, whether or not anything was learned from it.
Counts of recordings, durations, dates and languages taken from the run ledger are not contacts.

| When (UTC) | What touched the hold-out | What was read or produced | Status |
|---|---|---|---|
| 2026-11-20, during the run | The snapshot tables of the first analyst panel (catalogue section 2) | 32 audio files of hold-out creators entered recording-level descriptive tables before the hold-out was declared | Known since the catalogue; stated in the paper's limitations |
| 2026-11-20, after the run | The run report and the findings dashboard: speech by position in the recording, recordings by length and share without speech | Timing measures (no words) of every transcribed recording, hold-out creators included, shown in a position heat map and per-creator tables | Found by the second-round panel; to be stated in the paper. Fixed 2026-11-21: the run report, the paper figures and the dashboards now draw positional displays from seen creators only, and publish distributions instead of per-creator rows (owner's decision on public identifiers) |
| 2026-11-20 20:39 | The registered test of H3, as its frozen procedure allowed | Every English hold-out transcript was opened by the frozen code; the code opened each file more than once across its count-only and full runs | Allowed by the H3 freeze; listed for completeness |
| 2026-11-20, about 21:50 to 22:15 | A coverage script of the second-round panel (social scientist, round 1) | About 415 metadata files of hold-out recordings were loaded in full (title, description, tags among their fields) and the presence of fields was counted for non-seen creators. The panel reports that no hold-out text was analysed or written out | Breach of the round's rule, found by two other panel members; no hold-out text field is to be extracted before freeze 2 |
| Planned | The TABLE item of the second-round programme | One extraction pass over all metadata files, writing only time stamps and durations for non-seen recordings; logged in the panel's `r2-runs/contact-log.md` | Planned contact, disclosed in advance |

None of these contacts produced a statistic about a registered hypothesis on hold-out text other than H3's
registered test. The contacts are listed in the paper's limitations once the owner approves the wording.

