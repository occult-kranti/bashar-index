# r3-P23 prespecification: three-source capture-recapture for the finders' recall

Written 2026-11-26T06:31:30Z (UTC, from `date -u`) by a step-1 agent (a model agent working for the
lead; not a person), before any three-source table, log-linear fit or recall of this entry was computed. Deposit 2 was
merged before; nothing here is tuned on outcomes. Exploratory; not a test of H1-H10. Seen creators only (set G of the
gate runs is seen-only). No model call: every reading comes from stored answers.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**What this agent had seen before writing it.** nlp-R13's public table (two captures of one model: forecast candidates
0.910, F1 statements 0.991, asks of record 0.991 with the observed upper bound 0.951); the pooled gate-E summary of the
forecast finder on G (`llm/pilot/gates-g-fafb-fbfix.json`: relative recall of the small finder against the middle finder
and critic, by pass, and the counts of accepted clusters found by the small finder only, the middle finder only and both);
the asks gate's pooled summary on G. No three-source table, no split of the small finder's clusters by pass together with
the middle finder, and no log-linear estimate had been seen.

## The three seen-side sources

- **Forecasts (set G, gate E's 60 drawn windows):** A = the small model, wording A; R = the small model, wording R (the
  production finder's two captures, from the run-1 record `pilot2/gates-g-fbfix/out-g-fbfix.private.json`, field
  found_by); M = the middle model's finder (wording A, effort none), read from the stored answers of store `pilot-fa-g`.
  Items are grouped exactly as gate E grouped them (`gates_g.worker_fafb`: union-find under `forecasts.same_statement`).
  Populations: (i) **all clusters** (candidates; the analogue of nlp-R13's candidate row); (ii) **clusters the middle
  critic accepts as F1** (stored answers of store `pilot-fb-g-r1`, the revised critic; the analogue of the statements row).
- **Asks (set G, the asks gate's English recordings):** D0 and D1 = the small model's two find draws of run 1 (store
  `p4-asks-g-r1`, field draws); M = the middle model's find (store `p3-asks-g-findmid`). Items: unit ranges of the union
  (`pilot_asks_gate_g.middle_arm`), grouped by shared units (its `clusters`), left out where they start in a window either
  find lost (as gate E). Populations: (i) **groups the middle check of the union accepts as an ask of any class**
  (analogue of nlp-R13's asks of record); (ii) the same with K1 in the accepted classes.
- **How the stores are read.** The instrument modules are imported with the API client replaced by an empty stub, network
  sockets refused, file writes refused outside this entry's folder, and the runner's send functions replaced by a refusal;
  every answer is looked up in its store by the request id the module rebuilds; a missing answer stops the run (no
  partial table). If a source cannot be rebuilt this way, the entry prints the two-source bound for that class and says
  the third source is not rebuilt.

## Estimators

- **Two-source (comparison):** Chapman's estimator for A against R (forecasts) and D0 against D1 (asks) on the same items,
  as nlp-R13 computed it on the roster.
- **Three-source:** Poisson log-linear models on the 7 observed cells (the cell missed by all three is the unknown),
  hierarchical, the three-way interaction set to zero: [A][R][M]; [AR][M]; [AM][R]; [RM][A]; [AR][AM]; [AR][RM];
  [AM][RM]; [AR][AM][RM] (zero residual degrees of freedom). N = observed + exp(intercept).
- **Admissible models (fixed now):** those that include the interaction of the two small-model captures ([AR], or [D0 D1]
  for asks; their dependence is known: one model with similar or identical prompts) and whose fit is not rejected
  (deviance goodness-of-fit p >= 0.10 where residual df > 0; the all-two-way model is admissible when its estimate is
  finite and its missed count is not negative).
- **Recall of the production finder** = items found by A or R (D0 or D1) / N. The **range over admissible models** is
  printed; its **upper end is the upper bound** of the production finder's recall within these windows; the lower end is
  printed beside. Also printed: every model's N, missed count, deviance, df and AIC.
- **Population and weights.** Primary: unweighted, the closed population of items in the drawn windows (forecasts) or
  the G recordings (asks). Sensitivity (point only): forecast cells weighted by 1 / p of the window's stratum, as gate E
  weighted.

## Intervals and reading

- 90% creator-cluster bootstrap percentile intervals (2,000 draws, seed 2026112623; creators of G resampled with their
  windows or recordings, every model refitted). r3-P30 holds no class for capture-recapture: flagged "interval method not
  calibrated by r3-P30 for this design class".
- **Reading (description, fixed now):** nlp-R13's two-capture recall is "optimistic by at least the margin" if the upper
  end of the admissible range (its point) lies more than 0.05 (deposit 2's margin for a difference in shares) below
  nlp-R13's published recall of the same class, and the upper 90% bound of that upper end lies below nlp-R13's value;
  "not shown to be optimistic beyond the margin" if the upper end's interval reaches within 0.05 of nlp-R13's value or
  above it; otherwise "undetermined". Comparisons are across bases (G windows against the whole roster), stated.
- Small cells: capture cells are printed only where each printed cell holds items of 5 or more creators; otherwise cells
  are pooled (A only with R only, and so on) or not printed, and the estimates are printed alone. No per-creator value.
  Recall near 1 rests on estimated, not observed, misses (D58). Creator counts through `pubrules.Register`.
- Multiplicity: 56 primaries in the programme; half-effect disclosure as r3-P30 prints it.
