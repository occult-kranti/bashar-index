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
cost of every request, and the code refuses work that would pass a cap.

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
The owner added the same day: the panel is also to consider, and where worthwhile implement, further topic
analysis, comparisons, distributions, and analysis of all recording metadata joined to the transcripts for the
recordings that have it; and the panel deliberates in two rounds, each expert first proposing and then answering
the others.

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
