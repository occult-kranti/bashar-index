# r4-P03: a splice and acoustic-environment census at voice boundaries

Written by the audio agent, a model agent working for the project lead (not a person); times from `date -u`. Class a.2,
run under the lead's ruling 4 (it reads audio). **Exploratory; not a test of H1-H10.** Seen creators only. Voice
boundaries are model-coded and not checked by a person. A detected environment change describes the recording's
background sound, never how or why a recording was made; a change is not an edit, and digital silence makes a boundary
undecidable, not "unedited".

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Question (programme):** audits the premise "same speaker, same microphone, same recording" behind r4-P01, r4-P13 and
r4-P15 (den-soc's attack A1; objection O14); becomes an exclusion rule. Prespecification: `../prespec.public.md` (published redacted), section 9.

## How it ran

- **Tier:** X by count (outcome-free; the 23 non-development creators). The detector's threshold is the
  only data-tuned part: the 95th percentile of the environment score at the development creators' non-boundary edges (a
  5% false-positive rate on the null class; its value is kept private). It is read once on all eligible non-development
  creators.
- **Events:** voice boundaries (primary definition) with 10 s of span on each side, in every processed recording (no rate
  gate); matched non-boundary edges of the same creator (tenth, punctuation class, pause bin, segment start; up to 5).
- **Score:** the per-band distance of the background spectrum (non-active frames; 10 s each side, 0.5 s left out).
  Undecidable: digital silence over half of either side, or under 0.3 s of background on either side.
- **Statistic:** per creator, the share of decidable boundaries with a detected change minus that share at matched edges;
  90% t interval on creator means, fixed (interval class not calibrated by r3-P30); margin 0.05.
- **Exclusion rule (hashed in the prespecification):** a boundary with a detected change leaves the delivery rows of
  r3-P09 and r4-P15.

## Results (run 2026-11-26 17:59Z; reruns 18:05Z and 19:12Z (the lead's decision 109), same numbers)

- **Shares** (10 to 19 creators): voice boundaries with a detected environment change about 0.09 (0.03 to 0.15); matched
  non-boundary edges about 0.054 (0.025 to 0.084).
- **Primary, boundaries minus matched edges:** about +0.035 (-0.028 to 0.098): **undetermined** against the 0.05 margin.
- **Undecidable shares:** in `public/data-r4-P03-undecidable.csv`; cells the privacy rule withholds read "not printed
  (privacy rule)", and the figure does not draw them.
- **Battery criterion 6:** the score separates session joins (AUC about 0.91), music-bed onsets (0.96) and spectral
  changes without an edit (0.99) from unedited points; it does **not** see same-session cuts at a pause (0.46) or pure
  gain steps (0.49). The census is therefore limited to changes of background spectrum; a cut within one room and
  session is invisible to it.
- **In words:** voice boundaries do not show a detectable excess of background change over matched edges at this size;
  the premise "same recording environment" is neither confirmed nor refuted, and the census cannot speak to cuts made
  within one session.
- **Exclusion rule applied:** boundaries with a detected change left r3-P09's and r4-P15's delivery rows.

### Tables

**`public/data-r4-P03-battery-splices.csv`**

| class | auc | points | criterion |
|---|---|---|---|
| gain step | 0.494 | 52 | not met |
| music-bed onset | 0.957 | 52 | met |
| same-session cut | 0.463 | 52 | not met |
| session join | 0.908 | 42 | met |
| spectral change without an edit | 0.991 | 52 | met |

**`public/data-r4-P03-census.csv`**

| row | creators | estimate | lo90 | hi90 | margin | words |
|---|---|---|---|---|---|---|
| share of decidable boundaries with a detected change (creator mean) | 10 to 19 | 0.09 | 0.03 | 0.15 |  | described |
| share at matched non-boundary edges (creator mean) | 10 to 19 | 0.054 | 0.025 | 0.084 |  | described |
| boundaries minus matched edges (primary) | 10 to 19 | 0.035 | -0.028 | 0.098 | 0.05 | undetermined |

**`public/data-r4-P03-undecidable.csv`**

| events | decidable | undecidable_digital_silence | undecidable_too_little_background |
|---|---|---|---|
| voice boundaries | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) |
| non-boundary edges | not printed (privacy rule) | not printed (privacy rule) | 0.004 |


## Departures and rows not computed

- **Departure from the split policy's wording** (accepted as the lead's decision 106.1, decided 2026-11-26 18:16Z).
  Deposit 2's split policy builds a data-tuned rule on exploration half A and runs it once on sealed half B (tier S),
  or cross-fits it over the two halves (tier X). Here the detector's threshold is fixed on the tuning pool T
  (the development creators' non-boundary edges) only, and the census is read once on all eligible non-development
  creators (tier X by count).
  Reason: T sits on the exploration side and is never read for a split reading, so fitting on T alone keeps both halves
  out of every fit (decision 88's reading). **Limitation: half B is no longer sealed for the acoustic measures described
  here.**
- The local click score stored per edge (frame-level level jumps) is kept private and is not a row; the battery tested
  the background score only.

## Privacy

No cell, bin or plotted group rests on fewer than 5 creators; no row or point is per creator or per recording; no audio,
waveform or spectrogram of any recording; no absolute pitch; no names, ids, titles or quotations. Creator counts print as
"all 23", as bands, or not at all; values that could narrow a banded count are not printed. A cell or count withheld under
the privacy rule reads "not printed (privacy rule)", whatever the reason; in the stacked class shares such a class is
counted in "other sound, unclassified". Every interval method is fixed in the prespecification, so decision 62 does not
apply to banded rows. The privacy checks are listed in `../common/README.md`.

Multiplicity: 56 primaries in the programme; if every true effect sat at half its margin, about 2.8 readings beyond the
margin would be expected by chance. A reading is never a finding.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Change by the lead's decision 109

2026-11-26T19:28:21Z (UTC, from the clock), after the independent privacy check of the seven audio entries.
No number changed: values are withheld, merged, re-banded or reworded, and the figure is redrawn by this entry's code.
Changes in this entry:

- undecidable-share cells the privacy rule withholds read "not printed (privacy rule)"; the figure is redrawn without
  the undecidable panel, and the README's sentence on the undecidable shares is corrected (decision 109.4);
- the departure from the split policy's wording is printed with its reason and its limitation, as the lead accepted
  it on 2026-11-26 at 18:16Z (decisions 106.1 and 109.5);
- the privacy paragraph is reworded in general terms (decision 109.3);
- every hash in this README's file table and in `status.json` is refreshed.

## Change by the lead's decision 111

2026-11-26T19:37:45Z (UTC, from the clock). No number changed. The tier by count prints as its letter only,
and the prespecification is cited as its published, redacted copy (`../prespec.public.md`; the original stays
private and unchanged).

## Change by the lead's decision 112

2026-11-26T19:49:16Z (UTC, from the clock). No number changed. The original prespecification's hash is no longer
printed: the CSV headers (rewritten by this entry's code), `status.json` and this README cite `../prespec.public.md`,
hashed at 15:27:51Z (UTC), before the pass and before any outcome; the hash is kept privately (step-1 decision 49 item i).

## Files

| File | SHA-256 |
|---|---|
| `code/analyse_p03.py` | `1a90151daada7e0d8b6a060fe0ba1bb193fc99c26101b83d2159a915199b4f72` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `public/data-r4-P03-battery-splices.csv` | `1519cccd4b112be3a5a0c8920810d2926161b4bcb4e44829ee60cab03729b95f` |
| `public/data-r4-P03-census.csv` | `73c333a0adedec2bf34dd2cb838fdca071287f1ef8d02f517d79f73e5bdd009b` |
| `public/data-r4-P03-undecidable.csv` | `b3ef99c6443021ef493dbd5212b0b980b4cd17e7c64ecbe77e9ee96e96af40ae` |
| `public/fig-r4-P03-environment.pdf` | `e2d2617d8110ed1324a1504f7ee34d34db88a9aeff522d4677085aedca845c1f` |
| `public/fig-r4-P03-environment.png` | `fc51be3b1dfe4540111f6d9e7e81edb6bdb02be5f453a1e82f0da5faf9d6a338` |

`status.json` carries the same hashes; `contacts.md` lists every read with its time.
