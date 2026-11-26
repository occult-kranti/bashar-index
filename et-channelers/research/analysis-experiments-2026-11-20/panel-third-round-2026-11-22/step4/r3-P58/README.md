# r3-P58: does the audience reward the claimed voice inside a channel?

Third-round panel programme, step 4 (class a.1), five rows, "association at capture". Run on 2026-11-26 (UTC, from
`date -u`) by the step-4 agent, a model agent working for the project lead (not a person). Prespecification `prespec.md`
with `../common/prespec-shared.md`, hashed 14:07:09Z before any outcome (`prespec-hash-record.md`).

**Exploratory; not a test of H1-H10.** One snapshot cannot show audience capture (D11): every row is an association at
capture, inside a channel, and nothing here is causal. Labels are model-coded and not checked by a person; the title and
control-vocabulary rows are cue counts. The later part (creators moving toward rewarded formats) needs r3-P72's metadata
snapshots (class b).

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Tier and units

- **Tier X.** Eligible non-development creators: 18 (8 or more seen recordings aged 30 days or more at capture, with a view
  count, a duration, and voice and asks labels; META part (c)'s sample rule and floor). Two-fold cross-fitting over the
  deposited halves: each fold's outcomes are residualised on log10 age and log10 length with within-creator slopes fitted
  on the other fold's recordings; the creators of both folds are then pooled.
- Outcomes: views, likes per view and comments per view (log10), each as the cross-fitted residual ("at equal age and
  length"). Rows: (1) the voice map's main kind "claimed voice"; (2) the claimed-voice share of words; (3) a title naming a
  being (META part (c)'s rule-based cue; no model title code); (4) a spoken pay-or-enrol ask; (5) control vocabulary present
  (CSS-12's secret-control list of E11).
- Statistic: creator mean of within-creator Spearman correlations (creators with 8 or more recordings in which row and
  outcome vary); 90% interval by r3-P30's class E (the t interval on creator means at every simulated count); margin 0.10;
  no direction deposited. Band: the permutation-maximum band over the five rows of each outcome (1,999 within-creator
  permutations).

## Results in words

- **No row reads beyond the margin and none within it: all fifteen read "undetermined".**
- **Views:** the claimed-voice share of words with views inside a channel at equal age and length (creator mean 0.21,
  90% 0.08 to 0.35) is **outside the permutation-maximum band (±0.16) but undetermined against the 0.10 margin
  (association at capture)**; the interval reaches inside the margin. The claimed-voice main kind points the same way (0.15, 0.00 to 0.30; inside the band). A
  title naming a being (-0.04), a spoken pay-or-enrol ask (-0.01) and control vocabulary (0.02) sit near zero.
- **Likes per view and comments per view:** every row lies inside its permutation-maximum band; point estimates range from
  -0.13 to 0.12.
- Read as the programme words it: the claimed-voice share of words with views is outside the permutation-maximum band
  but undetermined against the 0.10 margin (association at capture); it is not a finding, and whether any association
  is a reward, a selection of topics, or an artefact of one snapshot cannot be told (D11). No account prediction was
  deposited for r3-P58; none is scored. den-soc's round-3 retirement condition (claimed-voice associations with views
  tightly equivalent to zero, or negative beyond the band) is not met: the views row is outside the permutation-maximum
  band but undetermined against the 0.10 margin (association at capture). This is a description, not a scored
  prediction.

Consistency: META-3 (release) found few recording properties going with audience counts at capture, with longer
recordings going with more views and older ones with fewer; this entry removes those two slopes by design. Its rows are new
(kinds, voice share, spoken asks, CSS-12 vocabulary); META-3's title cues are not repeated except the named-being cue,
which here reads near zero on the non-development creators.

Multiplicity (deposit 2): no family-wise adjustment across entries (the permutation-maximum band is family-wise within each
outcome); 56 primaries; about 2.8 readings beyond a margin expected by chance at half-margin effects. A reading is never
called a finding.

## Rows not computed

None: every row has 5 or more creators.

## Files

| File | What |
|---|---|
| `public/data-r3-P58-forest.csv` | five rows by three outcomes: estimate, interval, band, readings |
| `public/fig-r3-P58-forest.png`, `.pdf` | the forest with the margin and the permutation-maximum band |
| `prespec.md`, `prespec-hash-record.md` | prespecification and its hash |
| `code/p58.py`, `code/publish_p58.py` | analysis and publication (shared code in `../common/`) |
| `contacts.md`, `status.json` | reads (no contact); status with every file's SHA-256 |

## Privacy

The eligible count prints as 18. Every row's creator count prints in one form, "withheld (5 or more of the 18)", because
the rows' creator sets nest inside one another and any finer form would narrow another row's band. Every interval is r3-P30's class E, whose method is the same at every count (decision 64), so no interval
tells a count. Checks: see `../common/privacy-checks.md`.

## Departures

1. Freedman-Lane residual permutation with time blocks (round 3's sensitivity) is not run; the prespecification fixed the
   within-creator permutation of the outcome residual as the one band.
2. The spoken-ask row uses any final pay-or-enrol ask in the recording (any voice), as fixed in the prespecification.
3. **Row counts** were first printed in the register's per-set forms; the step's nest check (14:24Z) found that nested row
   sets narrowed one another's bands, so every row's count now prints as "withheld (5 or more of the 18)" (14:25Z). A
   privacy change only: no estimate, interval or reading changed.

## Changes at the joint staging of steps 3 to 5 (2026-11-26T14:59:32Z, UTC from `date -u`)

- **How the views row is cited (the lead's decision 80).** The claimed-voice share of words with views is cited
  only as "outside the permutation-maximum band but undetermined against the 0.10 margin (association at
  capture)". It is never cited as a finding.
- **"withheld (5 or more of the 18)"** is accepted as a floor form (the lead's decision 79).

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- The views row is worded only as "outside the permutation-maximum band but undetermined against the 0.10 margin
  (association at capture)", in the Results and in den-soc's retirement condition. No number changed.
