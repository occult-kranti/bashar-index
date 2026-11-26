# r3-P19: generalizability and decision study of the model labels ("consistency") (step 1, class a.1)

Written 2026-11-26T07:07:14Z (UTC, from `date -u`; drafted from 07:04Z) by a step-1 agent (a model agent working for the lead; not a person).
Exploratory; not a test of H1-H10. Seen creators only. No model call, no network call, no download, no GPU job. Every
label is model-coded and not checked by a person; every figure here is consistency (agreement between readings), never
accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Prespecification

`prespec.md` was written at 2026-11-26T06:30Z and hashed at 2026-11-26T06:31:30Z (SHA-256
`c2dbc6297be6c49d875e8c43b4706bcac6dd33fb0c0af925557e0c4525b44989`), before any variance component of any label quantity
was computed; `p19_analyse.py` refuses to run if it changed. Deposit 2's margin for agreement coefficients (0.10) is used
for the primary; the programme and deposit 2 state no margin of their own for this description entry.

## Primaries and readings (label-process share of one reading of one recording; 90% creator-bootstrap intervals)

The primary per instrument is the **label-process share**: the share of the variance of one reading of one recording
that comes from the label process (model and run components), against deposit 2's 0.10 margin. Reading A "the label
process carries a share beyond the margin", B "stays within the margin", otherwise undetermined. Every interval carries
the flag "interval method not calibrated by r3-P30 for this design class" (r3-P30 has no class for variance components).

| Instrument and quantity | Design | Label-process share | 90% interval | Reading |
|---|---|---|---|---|
| voice: claimed-voice share of words (small model, record) | composite: roster, two models, runs on G | 0.140 | 0.091 to 0.244 | undetermined |
| voice: own-voice share of words | composite | 0.129 | 0.087 to 0.197 | undetermined |
| asks: recording holds a pay-or-enrol ask (middle check, record) | composite (runs rebuilt from stored answers, r3-P23) | 0.105 | 0.077 to 0.165 | undetermined |
| forecasts: checkability time window YES share | two readings only (model and one reading's noise; no run main effect) | 0.245 | 0.201 to 0.296 | **A** |
| forecasts: checkability observable outcome YES share | two readings only | 0.311 | 0.231 to 0.416 | **A** |
| titles: presentation code P1 | two readings only | 0.228 | 0.154 to 0.320 | **A** |
| sentence codes: world-claim share | one reading stored | not computed | | not computed |

**In words.** For the voice and asks quantities most of one reading's variance lies between creators (31% to 49%) and
between a creator's recordings (37% to 56%); the label process holds about a tenth to a seventh, and its interval
straddles the 0.10 margin. For the forecast checkability parts and the title presentation
code, the two models' disagreement with one reading's noise holds about a quarter to a third of the variance, beyond the
margin. This is consistency between model readings; it says nothing about whether either reading is right.

## What the components show (data-r3-P19-components.csv)

- **Run noise is the largest label-process component for voice.** On set G (41 seen recordings, voice revision 3), the
  small model's run-to-run residual of the claimed-voice share is 0.0140 (whole instrument, map and label repeated) and
  0.0094 (label call only, one map); the middle model's is 0.0004. In the voice composite the run components are about
  9% of the claimed share's variance and the model components about 5% (model main effect 0.0012, creator x model 0,
  recording x model net of run noise 0.0058).
- **Prompt form (middle model, variant B at effort low against A at effort none; the two move together):** recording x
  prompt form 0.0042 (claimed share) and 0.0006 (own share).
- **Input forms (secondary; not facets of the frozen instrument).** Net of run noise, the claimed-voice share does not
  move with contractions visible, punctuation removed, positions hidden or the artefact filter off (each net component
  0). The own-voice share does: net components 0.016 (contractions visible), 0.012 (punctuation removed), 0.011 (positions
  hidden) and 0.028 (filter off, own map), against the own share's composite variance of 0.171.
- **Map.** The middle model's own map against the shared map: net of its run noise, about 0.
- **Recognizer facet.** Not stored at the level of a label quantity (below); rv-L2's published flip shares stand as
  published.

## Decision study (data-r3-P19-dstudy.csv; fig-r3-P19-dstudy-recordings, fig-r3-P19-dstudy-runs)

Relative coefficient E rho^2 of a creator's mean, model fixed at the record, one run (90% intervals):

| Instrument | 1 recording | 5 recordings | 20 recordings |
|---|---|---|---|
| voice, claimed share | 0.51 (0.42 to 0.60) | 0.84 (0.79 to 0.88) | 0.95 (0.94 to 0.97) |
| voice, own share | 0.33 (0.26 to 0.40) | 0.71 (0.64 to 0.77) | 0.91 (0.88 to 0.93) |
| asks, pay-or-enrol present | 0.37 (0.30 to 0.43) | 0.75 (0.68 to 0.79) | 0.92 (0.89 to 0.94) |
| checkability, time window | 0.25 (0.13 to 0.34) | 0.62 (0.42 to 0.72) | 0.87 (0.75 to 0.91) |
| checkability, observable outcome | 0.15 (0.09 to 0.20) | 0.46 (0.34 to 0.55) | 0.77 (0.67 to 0.83) |
| titles, presentation P1 (titles per creator) | 0.49 (0.39 to 0.58) | 0.83 (0.76 to 0.87) | 0.95 (0.93 to 0.97) |

Repeating a run moves E rho^2 by at most about 0.04 (voice claimed share, one recording per creator: 0.51 with one run,
0.56 with five); recordings per creator matter far more. With the model random (one model drawn), the coefficients are a
little lower (voice claimed share at five recordings 0.83; titles at five 0.66).

Multiplicity: 56 primaries in the programme; if every true effect sat at half its margin, about 2.8 readings of A would
be expected by chance at the deposited 5% (up to about 6.1 for the share, standardised, AUC and rank-correlation classes;
r3-P30's readings table). A reading is never a finding.

## Departures and choices (stated)

1. **Design 1's reading of record.** The prespecification's design 1 names "the small model of record"; it uses each
   instrument's reading of record: voice the small model; asks the middle check; checkability the middle model; sentence
   codes the one reading; titles the middle model's primary reading (the record is the large model's reading where
   adjudicated, which is not a crossed level).
2. **A coding error corrected before publication (no reading changed).** The first run of `p19_analyse.py` computed the
   decision-study curves of the instruments without a run facet from the two-model design's noise-free recording
   component, against the prespecification's own words ("the recording component includes that reading's noise"); the
   curves were recomputed from design 1 (model fixed) and design 2 (model random), and the model-random curve of the
   composite now uses the creator component minus creator x model. Label-process shares and readings are unchanged
   (same seeds).
3. **Asks' run facet** comes from r3-P23's read-only rebuild of the asks gate runs on set G (prespec item 5); the rebuild
   reproduced the stored gate counts exactly.
4. Negative moment estimates are set to 0 and marked in the components table.
5. Roster and set-G bootstraps are independent (set G's creators are seen creators too); stated as an assumption.

## Bases or fields not stored

- Recognizer facet: the relabelled shifted-grid transcripts are not stored (class c); rv-L2's per-pair record holds
  pairwise flip counts only, from which no reading's own label quantity can be solved.
- Run facets of the forecast class, commitment, checkability, sentence codes and titles on G: only pooled gate
  summaries are stored (not rebuilt here; a rebuild like r3-P23's is possible for some of them from stored answers).
- Sentence codes: one reading in production (no model facet); commitment: one reading.

## Files

<!-- FILES -->
| File | SHA-256 |
|---|---|
| `code/finalize.py` | `11240b1fd145fbbd8f0adb4e9b2a63205fe9ca67c34d117b119677c6be5b98f8` |
| `code/p19_analyse.py` | `66a75dec55ac79d590371a0be185c36bcb291a12f06d42acb08ed5d175ceee2c` |
| `code/p19_extract_g.py` | `f98628bdbbafcf4b6a43f2e1544ebe5cf514db1f15c179b371ef2797c4543781` |
| `code/p19_extract_roster.py` | `155ead48dd55c09f8f13f19a73176345e3e319c6345af3660b03aa34894b1fb7` |
| `code/p19_publish.py` | `317ae27db515b2502759e36a9ec082bb8cd5535c4347df8f289b86e8245f3f40` |
| `code/pcommon.py` | `9889e97a49df599ce6b5ca89d6acf8da2979257443e020912858701a0630ec64` |
| `code/probe_structure.py` | `47408c9b7cb2872241e5ad682740a559b84cebbee297d9b1ffdc3a4182bdf42c` |
| `code/qscan_all2.py` | `188cae5b379df1eca5209f4b3fbb54a767ce407dab4197e057e979c1488c0cb4` |
| `code/quant.py` | `a2478a09a37c3c759485fdfa3e0f98c6cd1d9a3094cc3b58c566588a9b1cae5c` |
| `code/quant2.py` | `7421b55e42d6fd55880a4b44dbc42c89c5991f18ba652374a2a4e93865ce9248` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `code/zsolve.py` | `e029e9c5497ef1ce809c248b6ea5b36a665c3abeff191d54fd35ed26b77f65eb` |
| `public/data-r3-P19-components.csv` | `0473e7a9f9692e9aeb7a20a520bb3f67744338be21ccfb8748fa2458ecf22158` |
| `public/data-r3-P19-dstudy.csv` | `08d088af91d0d188ac3bfa876ebf6897aba1a0917db9443647e8d99e1600f956` |
| `public/data-r3-P19-shares.csv` | `13c293a404c539c6ed0bcb26f2d4c62cd04d94d3322eeb79ac68f3e17d110d4e` |
| `public/fig-r3-P19-components.pdf` | `7a64c213e8a7513fc03cc19cc92a02680a2947b92de31f8b2137f442cd0307ed` |
| `public/fig-r3-P19-components.png` | `14f5ad8be2ca7707d26240804d614c0cc6a15593f301f528fb5dfa81f34f8761` |
| `public/fig-r3-P19-dstudy-recordings.pdf` | `4bd7960f6eac9053bd5f8800ac4762dac7e4caf15893e8a32dc3c611223f1cde` |
| `public/fig-r3-P19-dstudy-recordings.png` | `378dc7ae2e2945a9f843d3dffd1cde658e94630ac18bb2996f38c8f7090eacf4` |
| `public/fig-r3-P19-dstudy-runs.pdf` | `a2e0055db05e99ff5b6174b6d1e7d32ff9c0bd31bb7c86b272548f78c6110a79` |
| `public/fig-r3-P19-dstudy-runs.png` | `d97250b221027b1ba2d1d4c679b53271c656d780781164e943ebca42fa95b9f8` |
| `prespec.md` | `c2dbc6297be6c49d875e8c43b4706bcac6dd33fb0c0af925557e0c4525b44989` |
| `contacts.md` | `929080cd9e2e43f1590bf6c98d8fadc259acdbe0ef6be57a3186d63f23e1de7a` |
| `private/prespec-hash.json` | `719546ef93c9ec470688d59548b098ae298baee13884bda7a2e99e1929c04081` |
<!-- /FILES -->

## Contacts

None (see `contacts.md`).

## Privacy scan

r3-P01's identifier scan of every public file: no seen creator code, audio hash or video id. PNG without text chunks;
PDF without document information. The release's quantile solvers (`code/zsolve.py`, `code/qscan_all2.py`, REL set to
this entry's folder): 0 rows tested and 0 rows to fix (no quantile columns). Creator counts printed through r3-P01's
nested-count register.

## For the lead

- The voice and asks readings are undetermined, with intervals straddling 0.10; the checkability parts and title
  presentation read A. Every interval is flagged as not calibrated by r3-P30: the lead may want such readings capped at
  "undetermined" as for classes where r3-P30 found no holding method.
- The small model's run-to-run noise is the largest label-process component for voice; the decision study says more
  recordings per creator buy far more consistency than repeated runs.
- The own-voice share moves with altered inputs beyond run noise; the claimed-voice share does not. This bears on any
  own-voice contrast (r3-P15, r3-P17) and on r3-P03's register reading.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
