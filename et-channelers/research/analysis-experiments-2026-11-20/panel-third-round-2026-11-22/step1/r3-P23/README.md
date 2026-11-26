# r3-P23: three-source capture-recapture for the finders' recall (step 1, class a.1)

Written 2026-11-26T07:07:14Z (UTC, from `date -u`) by a step-1 agent (a model agent working for the lead; not a person).
Exploratory; not a test of H1-H10. Seen creators only (set G of the gate runs). No model call, no network call: every
reading was rebuilt from stored answers. The finders are model-coded and not checked by a person; recall here is the
estimated recall of a finder under a capture-recapture model, not a measure of correctness.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Prespecification

`prespec.md` was written at 2026-11-26T06:31:30Z and hashed at 2026-11-26T06:31:31Z (SHA-256
`d2672fd77c44a137afffd39efd4bc64c5b16b07b7ec06fbbea47b18e29a3bdc8`); `p23_analyse.py` refuses to run if it changed.
Four clarifications were written at 2026-11-26T06:50:11Z, after the read-only rebuilds and before any table or estimate
was computed (`private/clarifications-before-analysis.md`, SHA-256
`11bdd74b339901b2da343f6b4e294f2b8c72046177ea83c2d0b0018cfa8a54f3`): the reading rule's two conditions apply in the order
written; admissibility is re-evaluated in every bootstrap draw; the asks K1 row has no nlp-R13 counterpart; and the
small-cell rule below.

## The three seen-side sources (all stored)

- **Forecasts:** the small model's two wordings A and R (the production finder's two captures) and the middle model's
  finder, on the 60 gate-E windows of set G; populations: all clusters (candidates), and clusters the middle critic
  accepts as F1 (statements).
- **Asks:** the small model's two find draws of run 1 and the middle model's find on set G; population: groups the
  middle check of the union accepts (any class), and those accepted with K1 (pay-or-enrol).
- **How they were read.** The instrument modules ran with the API client replaced by an empty stub, network sockets
  refused, file writes refused outside the entry folders, and the runner's senders replaced by refusals; every answer
  came from its store by the request id the module rebuilt (`code/readonly_env.py`). The rebuilt clusters reproduced the
  stored gate summaries exactly (forecasts: cluster count, accepted count, the three found-by counts and the four
  weighted relative recalls; asks: the gate-E counts and left-out count), so the captures are those the gates used.

## Primaries and readings (data-r3-P23-recall.csv; fig-r3-P23-recall)

Recall of the production finder (the union of the two small-model captures). nlp-R13's published two-capture recall is
on the whole seen roster (95% intervals as published); everything else is on set G's items, 90% creator-bootstrap
intervals, flagged "interval method not calibrated by r3-P30 for this design class".

| Population | nlp-R13 (roster) | Two captures on G (Chapman) | Three sources: admissible range (upper end = upper bound) | Reading |
|---|---|---|---|---|
| forecast candidates | 0.910 | 0.903 (0.835 to 0.943) | 0.097 (0.030 to 0.215); one admissible model, the all-two-way model with zero df | "optimistic by at least the margin" (see the caveat) |
| forecast F1 statements | 0.991 | 0.997 (0.996 to 0.999) | 0.786 to **0.876**; upper end 90% 0.650 to 0.927; two admissible models | **"optimistic by at least the margin"** |
| asks, any class | 0.991 (registered; observed upper bound 0.951) | 0.997 (0.992 to 1.000) | no admissible model | not computed: two-source estimate only |
| asks, pay-or-enrol (K1) | no counterpart row | 1.000 (1.000 to 1.000) | no admissible model | described only |

**In words.** For forecast statements, a finder of another model (the middle model) finds accepted statements that both
small-model captures miss, and the admissible three-source models put the production finder's recall at about 0.79 to
0.88 within these windows, against a two-capture estimate of 0.997 on the same items and nlp-R13's 0.991 on the roster:
the two dependent captures of one model are optimistic by more than the 0.05 margin. For asks, the three captures overlap
too much for any three-source model that allows the two draws' dependence to be identified; only
the two-capture estimate can be printed, and it inherits nlp-R13's dependence caveat (the check's observed misses on
the roster already showed it too high).

**Caveat on the candidate row.** Every candidate model without the full set of two-way interactions is rejected by fit;
the only admissible model has zero residual degrees of freedom, and its estimate (recall 0.097) rests on the sparsest
cells (candidates found by one small-model wording and the middle finder). Items one wording admits are often not items
the other model's finder targets, so the closed-population assumption fails for candidates: the reading follows the
prespecified rule, but the estimate is not a credible recall. The F1-statement row, whose target the critic fixes, is
the substantive one.

Multiplicity: 56 primaries in the programme; if every true effect sat at half its margin, about 2.8 readings of A would
be expected by chance at the deposited 5% (r3-P30). A reading is a description, never a finding.

## Departures and choices (stated)

1. **The asks "any class" population is compared with nlp-R13's registered asks-of-record row** (clarification 3); its
   observed upper bound is printed beside.
2. **Small cells.** In every population at least one non-empty capture cell rests on 1 to 4 creators, so no cell count,
   total, estimated total, missed count, deviance, AIC or per-model estimate is printed; only the two-capture recall, the
   two ends of the admissible range with their intervals and the admissibility count. Every model's private fit is in
   `private/results.private.json`.
3. **Weighted sensitivity** (forecasts, cells weighted by 1 / p of the window stratum): upper end 0.098 (candidates) and
   0.878 (F1 statements), points only.
4. **Bases differ** (G's windows or recordings against the roster): the comparison with nlp-R13 is across bases, stated
   in every caption.

## Bases or fields not stored

None missing for the three sources: all three captures are stored for both classes. A seen-roster third capture is not
stored (the production finder ran the two small-model captures only); the three-source estimate rests on set G.

## Files

<!-- FILES -->
| File | SHA-256 |
|---|---|
| `code/p23_analyse.py` | `6fbdafc369629139d50dbaa24ad3448a2ba1090b8d672ec9025df87af0b0c24d` |
| `code/p23_publish.py` | `b22b8c84dbcc29a172f603b1401f39665feb41b5455bc7f3dd8cb9b4571627eb` |
| `code/p23_rebuild_asks.py` | `6e42f1218dcbbb62827b2422fb81f9acfa464c004962c00371e6d500a59f6d8d` |
| `code/p23_rebuild_forecasts.py` | `10b2b49937981a4228ae98e2fdfea67c20d34277093e105f3e1341aac73b9a77` |
| `code/qscan_all2.py` | `5b23104902f0e0e19b7d4d38096ef2f44df2f8ae4f6ebe56a77c979ae1aaf8af` |
| `code/quant.py` | `a2478a09a37c3c759485fdfa3e0f98c6cd1d9a3094cc3b58c566588a9b1cae5c` |
| `code/quant2.py` | `7421b55e42d6fd55880a4b44dbc42c89c5991f18ba652374a2a4e93865ce9248` |
| `code/readonly_env.py` | `68c288a41f999c339af2e89cacb6234fdff564b7f14ed8ca58021be5c7896911` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `code/zsolve.py` | `c59ec1843c0eefa36a1f607b8da8629046e67fb3de684244eb7e1b809449b600` |
| `public/data-r3-P23-recall.csv` | `179ee1908102bec8dbbddd5a31e5c0601bc18076a4ca6e071c63c293a8423cd4` |
| `public/fig-r3-P23-recall.pdf` | `f3d8b689b7d6a465d2f366ccad932a98f286326e82ce1b2179f452029af91a54` |
| `public/fig-r3-P23-recall.png` | `385c20e37ef0a484bab8af650cf62b773aa922b1af59fc96d4e5e853bcfac62c` |
| `prespec.md` | `d2672fd77c44a137afffd39efd4bc64c5b16b07b7ec06fbbea47b18e29a3bdc8` |
| `contacts.md` | `045092166e01fa599aea06c0aea882d32f7051f956d9a7993002a2a51489523b` |
| `private/prespec-hash.json` | `c8b8d358bb79190615bc71e2c4fb2e0df30920c0d9bc1574e1833a30ed3adf29` |
| `private/clarifications-before-analysis.md` | `11bdd74b339901b2da343f6b4e294f2b8c72046177ea83c2d0b0018cfa8a54f3` |
<!-- /FILES -->

## Contacts

None (see `contacts.md`; two filtered listings of `llm/answers` that displayed set-G store names only are recorded there).

## Privacy scan

r3-P01's identifier scan of every public file: no seen creator code, audio hash or video id. PNG without text chunks;
PDF without document information. The release's quantile solvers (`code/zsolve.py`, `code/qscan_all2.py`, REL set to
this entry's folder): 0 rows tested and 0 rows to fix. Creator counts through the nested-count register.

## For the lead

- The candidate row's reading follows the prespecified rule but rests on an unstable zero-df model (caveat above). The
  lead may rule that the candidate row is described only and that the F1-statement row carries the entry's reading.
- nlp-R13's two-capture recall of forecast statements (0.991) is optimistic: within set G's windows the admissible
  three-source models put it at 0.79 to 0.88. Any sentence citing nlp-R13's recall should carry this upper bound.
- For asks no three-source model is identifiable on set G; a larger seen sample read by the middle find would be class c.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
