# r3-P20: why reliability did not transport (gate ladder, disagreement model) and the registered prediction (step 1, class a.1; the prediction is class b with r4-P07)

Written 2026-11-26T07:07:14Z (UTC, from `date -u`) by a step-1 agent (a model agent working for the lead; not a person).
Exploratory; not a test of H1-H10. Seen creators only for every computed value. The gate-sample (G) and hold-out (R-hold)
rungs are the published values of the GATES table, copied; no hold-out file was opened and nothing was recomputed on the
hold-out. No model call, no network call. Every label is model-coded and not checked by a person; agreement
(consistency), never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Prespecification

`prespec.md` was written at 2026-11-26T06:31:30Z and hashed at 2026-11-26T06:31:30Z (SHA-256
the hash recorded at hashing time is kept privately), before any agreement outside G, bin agreement,
model coefficient or prediction was computed; `p20_analyse.py` refuses to run if it changed.

## The gate ladder and its readings (fig-r3-P20-ladder; data-r3-P20-ladder.csv)

Rung 2 is computed on seen recordings outside the gate sample G (primary) and on seen creators with no recording in G
(secondary). Reading of the transport gap (rung 2 minus G; margin 0.10): A beyond the margin, B within it, otherwise
undetermined. 90% creator-bootstrap intervals, flagged "interval method not calibrated by r3-P30 for this design class".

| Statistic | G (published) | Seen outside G | Gap reading | R-hold (published) | R-hold against rung 2 (chance) |
|---|---|---|---|---|---|
| voice kappa claimed / own / other | 0.890 | 0.854 (0.817 to 0.885) | **B**, transports within the margin | 0.832 | inside |
| voice kappa embodied / own / other | 0.921 | 0.849 (0.805 to 0.883) | undetermined (gap -0.072) | 0.815 | inside |
| voice stability over runs | 0.901 | not stored outside G | | 0.920 | |
| asks specific agreement on pay-or-enrol | 0.867 | 0.865 (0.843 to 0.886) | **B** | 0.833 | inside |
| forecast class F1-or-not, small against middle | 0.64 | not stored outside G | | 0.507 (fail) | |
| forecast commitment | 0.70 | not stored outside G | | 0.756 | |
| checkability time window | 0.56 | 0.635 (0.598 to 0.672) | undetermined (gap +0.075) | 0.805 (lower bound only) | outside |
| checkability named actor | 0.38 | 0.470 (0.422 to 0.508) | undetermined (gap +0.090) | 0.419 | outside (no interval published) |
| checkability observable outcome | 0.56 | 0.517 (0.474 to 0.552) | **B** | 0.328 | outside (no interval published) |
| sentence codes stability; kappa | 0.88; 0.80 | not stored outside G | | 0.816 (fail); 0.695 | |
| titles presentation (4 codes) | 0.64 | 0.813 (0.761 to 0.862) | **A**: higher outside G beyond the margin | 0.630 | inside |
| titles source family | 0.74 | 0.830 (0.749 to 0.899) | undetermined | 0.659 | inside |
| titles P1 or not | 0.70 | 0.842 (0.772 to 0.904) | undetermined | not published | |

The secondary rows (creators outside G) read the same except voice claimed / own / other (undetermined; the interval
reaches the margin).

## Why reliability did not transport: what the ladder separates (descriptions, not readings)

- **Overfitting or selection on G.** Where rung 2 exists, nothing shows a gate value inflated by tuning on G beyond the
  margin: voice and asks transport within it, no checkability part is lower outside G beyond the margin, and the title
  presentation code agrees more outside G than in G (A), so G's titles (and, by the published values, R-hold's) were
  harder than the rest of the seen titles: a selection of material, not overfitting.
- **Transcript quality.** On the seen rung-2 base, recognizer confidence predicts little disagreement: voice odds ratio
  0.85 per between-creator SD of recording quality (90% 0.58 to 1.32), checkability time window 0.96 (0.78 to 1.21).
  Shifting every recording's quality by the hold-out's published SMD (-0.8) predicts kappa 0.837 for voice (change -0.017,
  90% -0.069 to +0.025; R-hold published 0.832) and 0.625 for the time window (change -0.011, -0.061 to +0.046). Agreement
  against quality terciles is flat within its intervals (fig-r3-P20-quality). Conversation recordings disagree less than
  solo ones (odds ratio 0.31, 0.16 to 0.51).
- **Chance.** For voice, asks and the titles the R-hold value lies inside the rung-2 interval widened by R-hold's
  published half-width. The checkability parts' R-hold values lie outside the rung-2 interval in both directions (time
  window higher, observable outcome lower), and R-hold publishes no interval for two of them: neither quality nor chance
  as measured here accounts for them.
- **The two R-hold failures** (forecast class of record, sentence-code stability) have no stored rung 2: the seen data
  hold no second reading of the forecast class outside G (the middle critic read only routed candidates) and no rerun of
  the sentence codes outside G. Their published G and R-hold intervals overlap (forecast class 0.503 to 0.75 against
  0.169 to 0.792), so chance is not excluded; the ladder cannot separate the three explanations for them.

## The registered reliability prediction (class b; registered with r4-P07; written, not tested)

`public/r3-P20-registered-prediction.csv` holds, for each statistic with a rung 2, the 90% prediction interval for a
future wave's reliability sample in the 2 x 2 of r4-P07 (snapshot same / new x new uploads of seen speakers / fresh
speakers), by the prespecified rule (rung-2 estimate +- 1.645 x sqrt(SE_boot^2 + SE_R^2); fresh speakers widened by the
quality counterfactual where it exists; no drift stated). It was hashed at **2026-11-26T07:03:23Z** (from `date -u`),
SHA-256 **`f5f88d86e2a5a9c643aa8ba284ba4fb9fa8bcea2405f0376c99f7431c03da71b`**, and is not compared with any data here.
Example: voice kappa claimed / own / other, new uploads of seen speakers, 0.731 to 0.978; fresh speakers 0.713 to 0.978.
Upper ends above 1 are capped at 1 (the statistic's maximum).

Multiplicity: 56 primaries in the programme; if every true effect sat at half its margin, about 2.8 readings of A would
be expected by chance at the deposited 5% (up to about 6.1 for the share, standardised, AUC and rank-correlation classes;
r3-P30's readings table). A reading is never a finding.

## Departures and choices (stated)

1. **Quality bins.** Deciles and quintiles failed the 5-creator or 22:33 rule, so the prespecified fallback (terciles)
   is printed; cut points are not printed.
2. **Format levels in the voice model.** Levels with 5 or more creators were kept (conversation, mixed, audience
   session); the unclear and multi-presenter formats form one pooled level "other formats" rather than joining mixed as
   the prespecification wrote (they were too few to change mixed's estimate; stated).
3. **G creator counts** are not printed by this entry: the G rows print "published with GATES" (G's figures rest on
   different gate subsets).
4. **R-hold without a published interval** (checkability time window, named actor, observable outcome; titles P1 has
   no R-hold value): the chance column describes R-hold against the rung-2 interval only.
5. **Prediction intervals** are capped at 1. The SE of a wave's reliability sample uses R-hold's published half-width
   where it exists, else twice the rung-2 bootstrap SD (as prespecified).
6. **"Outside G" for titles** is every seen title not read in the titles gate on G (G's titles matched by video key);
   for asks and forecasts it is the seen recordings outside set G's 41 recordings.

## Bases or fields not stored

- A second reading of the forecast class of record outside G (only routed candidates were read by the middle critic).
- A second commitment reading; sentence-code reruns or a second model on sentence codes outside G; voice reruns outside
  G (production labelled each recording once). These rungs read "not stored outside G".
- The hold-out's quality distribution: only rv-D2-H's published SMD is used (no hold-out file opened).
- HR (the hold-out robustness rows) did not run (model calls not bought).

## Files

<!-- FILES -->
| File | SHA-256 |
|---|---|
| `code/p20_analyse.py` | `e7b1c8463d3b9c913cded6a7c7765ffa584af1003ffd3dd9765b3b35a534462b` |
| `code/p20_publish.py` | `0a29acf8266b5e4bd0dfc7c18d4c05916f6bbce3889b825a63be896480a5a281` |
| `code/p20_quality.py` | `33c12b40f4991522411f0da96825b977bcb028d3c368b3efdde93012ae4ee084` |
| `code/qscan_all2.py` | `c3368895ea475ff0e56bbe03c8c97b78c441f20052b010323533f2d9a8ef3bf2` |
| `code/quant.py` | `a2478a09a37c3c759485fdfa3e0f98c6cd1d9a3094cc3b58c566588a9b1cae5c` |
| `code/quant2.py` | `7421b55e42d6fd55880a4b44dbc42c89c5991f18ba652374a2a4e93865ce9248` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `code/zsolve.py` | `301ccb16c41517d974a60acd212d9eae987ecf5f72e9f327fd176d0c69e0b7c1` |
| `public/data-r3-P20-disagreement-model.csv` | `a2308493a4a63b783b3a9b8bc98e383b9ca7384cb1f3d5c06dd47d6c89484336` |
| `public/data-r3-P20-ladder.csv` | `5e8b74c553b3d5b6a627ad1a9d9b5b49a2c9a0052fd66095345d8cc6ecb59acc` |
| `public/data-r3-P20-quality-bins.csv` | `b2d214ee930dbc343e138a7a1cc59442060b2c72d8564a9275c51dab7d63d208` |
| `public/fig-r3-P20-ladder.pdf` | `9e4a0cfdf2a10ffb4f3368680a8f62271d764cc0609256a50c43a8bd8f48eb44` |
| `public/fig-r3-P20-ladder.png` | `071315fe8d2edcac0602ea5711649f181f41d0f22f30bd4e0d3a144878e65723` |
| `public/fig-r3-P20-quality.pdf` | `7588eb11f6eb54c80a95f7485d654cb6c5fe60bc2851bfc535b9372096c6a5bc` |
| `public/fig-r3-P20-quality.png` | `5170c7fbb1b3c815b0821cae79c2a779f2c5de0cca1f9a5504b20e17ca313320` |
| `public/r3-P20-registered-prediction.csv` | `f5f88d86e2a5a9c643aa8ba284ba4fb9fa8bcea2405f0376c99f7431c03da71b` |
| `prespec.md` | the hash recorded at hashing time is kept privately |
| `contacts.md` | `6158764de2b2a9d676aadee0daa512ea789a9b35b87b40766db02773eb841714` |
| `private/prediction-hash.json` | `65c9754905743c2911974982c973642357988b97cf89d0e9ebbfba085d97db0c` |
| `private/prespec-hash.json` | `f50de297b765e6c123461e682774b6490548f3db890b923ebd168b26dda6b610` |
<!-- /FILES -->

## Contacts

None (see `contacts.md`).

## Privacy scan

r3-P01's identifier scan of every public file: no seen creator code, audio hash or video id. PNG without text chunks;
PDF without document information. The release's quantile solvers (`code/zsolve.py`, `code/qscan_all2.py`, REL set to
this entry's folder): 0 rows tested and 0 rows to fix. Every computed agreement figure passes the 22:33 rule (title
source families pooled by VER's rule where needed, named in the table); creator counts through the nested-count register.

## For the lead

- The ladder cannot explain the two R-hold failures (forecast class, sentence-code stability): their seen rung 2 is not
  stored. A rerun of the sentence codes, or a second forecast-class reading, on a seen sample outside G is class c
  (model calls), and it is the cheapest arm that would separate selection from transport.
- Title presentation agrees more outside G than in G or on R-hold: G and R-hold may both have drawn harder titles. The
  lead may want this noted wherever the titles' failed gates are cited.
- The registered prediction's hash above is for the r4-P07 deposit; the lead decides when it is deposited.
- Every rung-2 interval is flagged as not calibrated by r3-P30 (no class for pooled kappas).

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
