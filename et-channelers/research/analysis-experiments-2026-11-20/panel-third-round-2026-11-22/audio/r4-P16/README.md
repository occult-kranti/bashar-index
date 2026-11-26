# r4-P16: the non-speech layer before claimed-voice onsets (part a)

Written by the audio agent, a model agent working for the project lead (not a person); times from `date -u`. Class a.2
(its audio part, under the lead's ruling 4). **Exploratory; not a test of H1-H10.** Seen creators only. Onsets are placed
by model-coded labels, not checked by a person; the classes are rule-based with descriptive names, never "induction" or
"trance onset". Acoustic features describe the sound of these recordings, never a speaker's state or a source.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Question (programme):** the non-speech layer before claimed-voice onsets; breathing that precedes any long utterance is
the control (N14). **Prior work named (N14):** breathing that scales with the coming utterance (Torreira, Bogels and
Levinson 2015); trance respiration by sensor (Wahbeh et al. 2019); hallucination over non-speech (Koenecke et al. 2024).
Not found means only that. Prespecification: `../prespec.public.md` (published redacted), sections 2 and 11.

## How it ran

- **Tier:** X by count (outcome-free; the 23 non-development creators); no data-tuned part; the
  description is made once on all eligible non-development creators.
- **Onsets:** claimed-voice onsets (primary definition) with 30 s before them, in every processed recording (no rate
  gate). Frames outside recognized speech in the 30 s before each onset.
- **References:** position-matched points (5 per onset, same recording and tenth, 30 s or more from any boundary) and
  length-matched own-voice onsets of the same creator (span length within a factor of 2). The template stratum (onsets in
  the first 60 s of a recording) is printed apart; its complement: not printed (privacy rule).
- **Rows:** creator-balanced stacked class shares with the undecidable share; the breath-like share before claimed onsets
  minus before own-voice onsets (and minus before matched points), 90% t interval on creator means, fixed (interval
  class not calibrated by r3-P30), margin 0.05.
- **Part (b)** (a filter rule on what the recognizer writes over wordless vocalisation) is text work, a.1, and is not run
  in this audio batch.

## Results (run 2026-11-26 18:02Z; reruns 18:06Z, 18:07Z and 18:12Z, and 19:14Z under the lead's decision 109; same contrasts)

- **Breath-like share, claimed minus length-matched own-voice onsets** (N14's control; 10 to 19 creators): about +0.003
  (-0.005 to 0.010): **within the margin (B)**.
- **Breath-like share, claimed minus position-matched points:** about 0.000 (-0.004 to 0.004): **within the margin (B)**.
- **Caveat on the B readings:** breath-like frames are about 1% of the time outside recognized speech here, far below the
  0.05 margin, so a difference inside the margin is close to built in by the base rate; the breath class is rule-based
  and was not tested on the battery; and the 30 s before own-voice onsets hold much excluded time (about a third: they
  often follow other participants or material), which limits that comparison.
- **Composition:** before claimed onsets, near-floor silence about 0.31, digital silence about 0.14, excluded about 0.13,
  unclassified about 0.41; the template stratum (onsets in the first 60 s; 5 to 9 creators) prints near-floor silence
  and unclassified sound. Cells the privacy rule withholds read "not printed (privacy rule)" and are counted in "other
  sound, unclassified".
- **In words:** the rule-based breath-like layer before claimed-voice onsets is no larger than before own-voice onsets or
  matched points, within a margin the class's low base rate makes easy to meet.

### Tables

**`public/data-r4-P16-breath.csv`**

| row | creators | estimate | lo90 | hi90 | margin | words |
|---|---|---|---|---|---|---|
| breath-like share: claimed minus length-matched own-voice onsets | 10 to 19 | 0.003 | -0.005 | 0.01 | 0.05 | within the margin (B) |
| breath-like share: claimed minus position-matched points | 10 to 19 | -0.0 | -0.004 | 0.004 | 0.05 | within the margin (B) |

**`public/data-r4-P16-onsets.csv`**

| window | creators | share: excluded (not processed) | share: digital silence | share: silence near the background floor | share: breath-like | share: vocalisation without recognized words | share: sustained voiced tone, voice-like | share: tone, instrument-like | share: music-like or sustained sound | share: other sound, unclassified | undecidable share (excluded + digital silence) | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 30 s before claimed-voice onsets | 10 to 19 | 0.129 | 0.135 | 0.309 | 0.009 | 0.009 | not printed (privacy rule) | 0.003 | not printed (privacy rule) | 0.406 | 0.264 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| 30 s before position-matched points (5 per onset) | 10 to 19 | 0.015 | 0.148 | 0.364 | not printed (privacy rule) | 0.019 | not printed (privacy rule) | 0.002 | not printed (privacy rule) | 0.451 | 0.163 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| 30 s before length-matched own-voice onsets (same creator) | 10 to 19 | 0.338 | 0.072 | 0.301 | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) | 0.29 | 0.409 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| claimed onsets in the first 60 s of a recording (template stratum) | 5 to 9 | not printed (privacy rule) | not printed (privacy rule) | 0.37 | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) | 0.63 | not printed (privacy rule) | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |


## Departures and rows not computed

- **Departure from the split policy's wording** (accepted as the lead's decision 106.1, decided 2026-11-26 18:16Z).
  Deposit 2's split policy builds a data-tuned rule on exploration half A and runs it once on sealed half B (tier S),
  or cross-fits it over the two halves (tier X). Here no part is tuned on data (the shared instrument was tuned
  on the tuning pool T, the development creators, before the prespecification), and the description is made once on
  all eligible non-development creators (tier X by count).
  Reason: T sits on the exploration side and is never read for a split reading, so fitting on T alone keeps both halves
  out of every fit (decision 88's reading). **Limitation: half B is no longer sealed for the acoustic measures described
  here.**
- Part (b), the filter rule on what the recognizer writes over wordless vocalisation: not run here (text work, a.1).
- The complement of the template stratum: not printed (privacy rule).
- The recall read (class c, 1 to 3 USD) stays unfunded.

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

- every class cell the privacy rule withholds, the reference rows' breath-like cells among them, reads one label,
  "not printed (privacy rule)", whatever the reason, and is counted in "other sound, unclassified"; the B readings'
  own rows still print (decisions 109.3 and 109.6);
- the note column and the figure's legend are reworded in general terms, and the template stratum's complement reads
  "not printed (privacy rule)" (decisions 109.3 and 109.7);
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
| `code/analyse_p16.py` | `ecc1e1238bb71548619b786d40bce5ee9ecdbc102509e6e2fd178837121c1633` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `public/data-r4-P16-breath.csv` | `a8b18e0822e0aded5f80f4d08f16237ac859ab9b47120f6cb42eab10e6242965` |
| `public/data-r4-P16-onsets.csv` | `975f7360af0828bdbf82fa006bc79f380c855788df36e33d2793bcdd1b65fe0c` |
| `public/fig-r4-P16-onsets.pdf` | `06bc0213d92d38bf52ceeafb66a00056eb85abbf366c3bcbb11ed3c0bc453417` |
| `public/fig-r4-P16-onsets.png` | `d0cd63de80b4e4fa347b26651b9fe45d71cb8e3e97d2e4ca8008e744b40adfeb` |

`status.json` carries the same hashes; `contacts.md` lists every read with its time.
