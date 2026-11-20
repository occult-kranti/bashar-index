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

## Procedure freeze

To be filled before the hold-out is labelled: the hashes of the codebooks, the prompts, the labelling code and
the analysis code, the model identifiers, and the date.

| Item | Value |
|---|---|
| Status | not yet frozen |
