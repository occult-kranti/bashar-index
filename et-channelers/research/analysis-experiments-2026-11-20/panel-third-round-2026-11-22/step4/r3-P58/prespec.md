# r3-P58: does the audience reward the claimed voice inside a channel? (prespecification)

Written 2026-11-26 (UTC, from `date -u`; the hash time is in `prespec-hash-record.md`) by the step-4 agent, a model agent
working for the project lead (not a person), before any outcome of this entry was computed. Shared rules:
`../common/prespec-shared.md`.

Exploratory; five rows, worded "association at capture": one snapshot cannot show audience capture (D11). The later part
(r3-P72's metadata snapshots) is class b. Labels are model-coded and not checked by a person; title and speech cues are
cue counts. Nothing here is causal.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Units and tier

- **Recordings** (META part (c)'s sample rule): seen recordings with a view count, age at capture 30 days or more and a
  known duration (TABLE's seen rows), that carry voice and asks labels.
- **Eligible creators** (outcome-free): 8 or more such recordings (META part (c)'s floor). Among the 23 non-development
  creators: **10 to 19, tier X**. Two-fold cross-fitting over halves A and B: the within-creator slopes of each outcome on
  log10 age and log10 length (creator fixed effects, slopes pooled over creators with 3 or more recordings, META part
  (c)'s residualisation) are fitted on one fold's recordings and used to residualise the other fold's; each creator's
  association is then computed on its residuals, and creators of both folds are pooled. Fold values are not printed.
- **Outcomes** (three): views (log10), likes per view (log10, recordings with 1 or more likes) and comments per view
  (log10, recordings with 1 or more comments), each as the cross-fitted within-creator residual on log10 age and log10
  length ("at equal age and length").
- **Five rows** (round 3's trimmed list; hashed now):
  1. claimed-voice main kind (voice map, small model: kind "claimed voice"; 1 or 0);
  2. claimed-voice share of the recording's words (small model, rule B, V2 + V3);
  3. a title source cue by rule: META part (c)'s regular expression for a named being in the title (read from its file;
     no model title code: no LAB-T row);
  4. a spoken pay-or-enrol ask (the frozen asks instrument, any final K1 ask in the recording);
  5. control vocabulary present (CSS-12's pass: one or more secret-control terms of E11's list in the transcript).

## 2. Statistics and readings

- Per row and outcome: per creator with 8 or more recordings in which the row's value and the outcome both vary, the
  Spearman correlation of the row with the outcome residual; the creator mean, with r3-P30's class E (within-creator
  rank correlation, one value per creator) at the row's count: the t interval on creator means at every simulated count,
  so the interval carries no count information (decision 64). Margin 0.10. No direction is deposited: "beyond the margin
  (higher with the feature)", "beyond the margin (lower with the feature)", "within the margin (B)", "undetermined".
- **The band** (one per outcome, over all five rows): the outcome residual permuted within creator, jointly for all
  rows, 1,999 draws; each row's creator mean standardised by its permutation SD; the 95th percentile of the maximum over
  rows of |standardised mean| gives the band (± that value times each row's permutation SD). A row outside the band reads
  "outside the permutation-maximum band" beside its margin words. Freedman-Lane with time blocks is not run (a stated
  departure from round 3's sensitivity).
- No account prediction is deposited for r3-P58 (deposit 2's cells are silent); none is scored. den-soc's retirement
  condition (round 3) is printed as a description only.
- Row counts print in the form `Counts` gives; rows on fewer than 5 creators: "not computed (too few terms or creators)".

## 3. Plot

A forest of within-channel associations at equal age and length, five rows by three outcomes, each with its interval,
the margin band (±0.10) and the permutation-maximum band. No per-creator point.

## 4. Consistency

Against META-3 (within a channel, few properties went with audience counts at capture; longer recordings with more views,
older ones with fewer): the residualisation removes those two slopes by design.
