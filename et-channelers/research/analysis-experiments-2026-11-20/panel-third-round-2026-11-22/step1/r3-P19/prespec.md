# r3-P19 prespecification: generalizability and decision study of the model labels ("consistency")

Written 2026-11-26T06:30Z (UTC, from `date -u`) by a step-1 agent (a model agent working for the lead; not a person),
before any variance component, share, coefficient or decision-study value of this entry was computed. Deposit 2 was
merged before; nothing here is tuned on outcomes. Exploratory; not a test of H1-H10. Seen creators only. Every label is
model-coded and not checked by a person; every figure is "consistency" (agreement between readings), never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**What this agent had seen before writing it.** The exploratory round's public aggregates (GATES, VER-DEP, VER-3R, VER-A,
DR-2, rv-R5, rv-L2, LAB-*); the voice gate-rerun notes of set G (`llm/pilot2/gate-rerun.md`: two-model kappas, the share of
words keeping one group over runs, and the altered-input "moved" shares, all pooled over G); the structure (field names,
file counts) of the stores read below. No variance component of any label quantity, on any base, had been seen.

## Label quantities (rows), one value per recording (or per title)

| Id | Instrument | Quantity |
|---|---|---|
| V-claimed | voice | share of the recording's words in a claimed voice (rule B: V2 or V3), the primary definition of LAB-V |
| V-own | voice | share of words in the creator's own voice (broad own, not claimed) |
| A-K1 | asks | recording holds at least one pay-or-enrol ask (K1 in the range's classes, verdict "ask") under the given check (0/1) |
| F-time | forecasts | share of the recording's coded statements whose checkability part "time window" is YES (recordings with 1 or more statement coded by both readings) |
| F-outcome | forecasts | the same for "observable outcome" |
| S-world | sentence codes | share of the recording's coded body words in the world-claim group (unit weights) |
| T-P1 | titles | the title's presentation code is P1 (0/1); object: the title, nested in its creator |

## Designs (each a separate G-study on the base its stored data hold)

1. **Roster design** (labels/seen through the frozen seen-only loader; small model of record on every seen recording):
   creator (c) and recording within creator (r:c), by the one-way nested random-effects moment estimator (unbalanced; the
   n0 coefficient), for every row above.
2. **Two-model roster design** (c, r:c, model m and their interactions), on the items both models read: voice on the
   recordings the middle model labelled in full (small against middle); asks on recordings whose every range carries a
   valid small and middle check; checkability on statements with both the record (middle) and the small reading; titles on
   titles with usable middle and small readings (the large model's partial readings are not a crossed level and are left
   out). Estimation: sums s = (y1 + y2) / 2 and differences d = y1 - y2 per item; the nested moment estimator on s and on d;
   sigma2(c x m) = between-creator variance of d / 2; sigma2(r x m, e) = within-creator variance of d / 2; sigma2(c) =
   between(s) - sigma2(c x m) / 2; sigma2(r:c) = within(s) - sigma2(r x m, e) / 2; sigma2(m) = (mean(d)^2 - var(d) / N) / 2.
   Sentence codes have one reading in production: no model facet (stated).
3. **Set G designs (voice only; revision 3; 41 recordings; recording is the object, creators mostly one recording each)**,
   balanced two- and three-factor random ANOVA by expected mean squares on V-claimed and V-own:
   - run, whole instrument (map and label repeated): B-luna, B-luna-map1-rep1, B-luna-map2-rep2;
   - run, label only (one map): B-luna, B-luna-rep1, B-luna-rep2;
   - model x run: {B-luna, B-luna-rep1} against {B-terra, B-terra-rep1} (run nested in model);
   - prompt form x run (middle model): {B-terra, B-terra-rep1} against {A-terra, A-terra-rep1} (variant A at effort none
     against variant B at effort low: the prompt form and the effort move together; stated);
   - input form: B-luna against B-luna-T0, -T5, -hide, -nofilter (each altered input is one separate run): the raw
     recording-by-input component and the same net of the matching run component (T0, T5, hide: the one-map run
     residual; nofilter, which used its own map: the whole-instrument run residual), floored at 0;
   - map: B-terra (shared map) against B-terra-ownmap, net of the middle model's run residual (B-terra against -rep1).
4. **Recognizer (grid and model).** The relabelled shifted-grid transcripts are not stored (class c). For the recognizer
   model, rv-L2's per-pair record holds pairwise flip counts only, from which each reading's own label quantity cannot be
   solved: "not stored at the level of a label quantity"; rv-L2's published flip shares are cited beside, unchanged.
5. **Asks on G (conditional).** If r3-P23's read-only rebuild of the asks gate runs on G succeeds, the run facet of A-K1
   (runs r1, r2, r3 of the whole asks instrument) is computed from it by design 3's run ANOVA; otherwise "not rebuilt".

Negative moment estimates are set to 0 and counted. Run-noise correction: the roster's r:c component of a quantity read
once includes run noise; the voice composite uses sigma2(r:c, true) = sigma2(r:c) - sigma2(r x run, e) (whole instrument,
G), floored at 0 (stated as an assumption that G's run noise transports to the roster).

## The voice composite and the stacked relative components (the plot)

Composite total for one recording read once by one random model and run: creator + r:c (true) + model + c x m + r x m
(net of run noise) + run + r x run. Prompt-form, input-form and map components are printed beside as secondary
components, not in the total (they are not facets of the frozen instrument). Other instruments: creator, recording and
(where stored) model components only; the run, prompt and input facets read "not stored" (G holds only pooled summaries
for them), except asks' runs under item 5.

## Primary per instrument and its reading

**Label-process share**: (model components + run components) / composite total, for one recording read once. Margin:
deposit 2's 0.10 for agreement coefficients (the share is one minus an absolute generalizability coefficient for one
reading of one recording; a choice, stated). Reading **A** "the label process carries a share beyond the margin" if the
90% interval lies wholly above 0.10; **B** "the label process stays within the margin" if wholly below 0.10;
**undetermined** otherwise; "not computed" under 5 creators. Instruments without a stored run facet print the model-only
share, labelled so (a lower bound on the label-process share).

## Decision study

Relative coefficient for a creator mean, model fixed at the record, n_r recordings and n_run runs:
E rho^2 = sigma2(c) / (sigma2(c) + sigma2(r:c, true) / n_r + sigma2(r x run, e) / (n_r n_run)); the absolute Phi adds
sigma2(run) / n_run; a second curve with the model random adds sigma2(c x m) + sigma2(r x m, net) / n_r (one model). Curves
against n_r = 1 to 20 for n_run = 1, 2, 3, and against n_run = 1 to 5 for n_r = 1, 5, 20 (design constants), voice
V-claimed and V-own; other instruments against n_r only (n_run = 1, run component not stored).

## Intervals and rules

- 90% creator-cluster bootstrap, percentile, 2,000 draws, seed 2026112619 (creators resampled with their recordings; on G
  the creators of G resampled with their recordings; roster and G resampled independently, an assumption stated).
  r3-P30's battery holds no design class for variance components or their shares: the method is the battery's boot_pct,
  and each reading carries the flag "interval method not calibrated by r3-P30 for this design class".
- No cell, bar or plotted group on fewer than 5 creators; creator counts printed through r3-P01's `pubrules.Register`
  (nested counts 1 to 4 apart stated against the other; counts within 4 of 101, 71, 23, 18, 6 and 36 banded).
- No per-creator or per-recording value is published; components and shares are pooled statistics.
- Multiplicity: 56 primaries in the programme; the half-effect disclosure is printed as in r3-P30's readings table.
