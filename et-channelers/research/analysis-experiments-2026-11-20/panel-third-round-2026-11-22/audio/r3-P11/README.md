# r3-P11: an acoustic codebook for audio outside recognized speech

Written by the audio agent, a model agent working for the project lead (not a person); times from `date -u`. Class a.2,
run under the lead's ruling 4 (Tier 0 audio). **Exploratory; not a test of H1-H10.** Seen creators only. Voice labels
(they place claimed-voice onsets and the excluded time next to other participants) are model-coded and not checked by a
person. The classes are rule-based with descriptive names and not checked by a person (a listening check is class c and
closed under ruling 10).
Acoustic features describe the sound of these recordings, never a speaker's state or a source.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Question (programme):** what fills time outside recognized speech, and the 30 s before onsets. Prespecification:
`../prespec.public.md` (published redacted), sections 2 and 7.

## How it ran

- **Tier:** S by count (outcome-free; the 23 non-development creators); the classes are fixed rules
  with no data-tuned part, so the description is made once on all eligible non-development creators.
- **Frames:** admitted frames not inside any recognized word of the record, in every processed recording of the
  non-development creators (no rate gate). Time next to units labelled as another participant, other material,
  unseparated conversation or cannot tell is never processed and is counted as "excluded (not processed)".
- **Classes** (prespecification section 2): digital silence; silence near the background floor; breath-like;
  vocalisation without recognized words; sustained voiced tone, voice-like; tone, instrument-like; music-like or
  sustained sound; other sound, unclassified. Where digital silence dominates, "no breaths" means "not observable"; over
  a bed, gaps are "music-like" or "unclassified", never "silence".
- **Windows:** start-aligned and end-aligned bins (minutes 0-1, 1-2, 2-5, 5-10, 10 onwards); the 30 s before the first
  claimed-voice unit of a recording; 30 s before position-matched shifted points (5 per onset, same tenth, 30 s or more
  from any voice boundary). Each creator's share by class, then the mean over creators (creator-balanced).

## Results (run 2026-11-26 18:00Z; reruns at 18:06Z, 18:07Z and 18:12Z for the privacy rule and the legend; rerun at 19:14Z under the lead's decision 109, no number changed)

- **Composition** (all 23 non-development creators in the early and late bins; bins after minute 10 rest on 10 to 19):
  outside recognized speech, the largest classes are silence near the background floor (about 0.30 to 0.38 of such
  frames, creator-balanced), other sound, unclassified (about 0.23 to 0.36), excluded time next to units of other
  participants or material (about 0.13 to 0.32, largest in the long middle bins) and digital silence (about 0.10 to 0.16).
  Breath-like frames are about 1%, vocalisation without recognized words about 1 to 2.5%, music-like sound up to about 2%
  (highest in the first and last minute).
- **Before the first claimed-voice unit** (10 to 19 creators): against shifted points, less silence near the floor (about
  0.32 against 0.38). The excluded share is about 0.08 before the first claimed-voice unit; before shifted points it is
  not printed (privacy rule). The voiced-tone, instrument-tone and music-like classes before the first claimed-voice unit
  are not printed (privacy rule) and are counted in "other sound, unclassified".
- **In words:** most time outside recognized speech is near-floor silence or unclassified sound; the rule-based classes
  that would mark toning, instruments or breaths are rare (breath-like frames about 1% throughout), and before
  claimed-voice onsets the toning and instrument classes are not printed (privacy rule).

### Tables

**`public/data-r3-P11-classes.csv`**

| window | creators | share: excluded (not processed) | share: digital silence | share: silence near the background floor | share: breath-like | share: vocalisation without recognized words | share: sustained voiced tone, voice-like | share: tone, instrument-like | share: music-like or sustained sound | share: other sound, unclassified | undecidable share (excluded + digital silence) | note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| start-aligned: minute 0-1 | all 23 | 0.209 | 0.118 | 0.297 | 0.01 | 0.024 | not printed (privacy rule) | 0.005 | 0.022 | 0.316 | 0.327 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| start-aligned: minute 1-2 | all 23 | 0.136 | 0.13 | 0.345 | 0.011 | 0.02 | not printed (privacy rule) | 0.002 | not printed (privacy rule) | 0.355 | 0.266 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| start-aligned: minutes 2-5 | all 23 | 0.128 | 0.123 | 0.369 | 0.013 | 0.015 | not printed (privacy rule) | 0.003 | 0.009 | 0.34 | 0.25 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| start-aligned: minutes 5-10 | not printed (privacy rule) | 0.189 | 0.127 | 0.372 | 0.011 | 0.013 | not printed (privacy rule) | 0.004 | not printed (privacy rule) | 0.284 | 0.316 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| start-aligned: minute 10 to the other end | 10 to 19 | 0.324 | 0.097 | 0.307 | 0.009 | 0.012 | not printed (privacy rule) | 0.004 | 0.011 | 0.235 | 0.421 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| end-aligned: minute 0-1 | all 23 | 0.157 | 0.152 | 0.313 | 0.008 | 0.025 | not printed (privacy rule) | 0.004 | 0.024 | 0.317 | 0.309 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| end-aligned: minute 1-2 | all 23 | 0.175 | 0.124 | 0.363 | 0.007 | 0.018 | not printed (privacy rule) | 0.003 | 0.017 | 0.292 | 0.3 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| end-aligned: minutes 2-5 | all 23 | 0.229 | 0.099 | 0.344 | 0.01 | 0.011 | not printed (privacy rule) | 0.002 | 0.015 | 0.29 | 0.328 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| end-aligned: minutes 5-10 | not printed (privacy rule) | 0.234 | 0.119 | 0.336 | 0.013 | 0.011 | not printed (privacy rule) | 0.003 | 0.003 | 0.281 | 0.353 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| end-aligned: minute 10 to the start | 10 to 19 | 0.302 | 0.098 | 0.31 | 0.011 | 0.014 | not printed (privacy rule) | 0.005 | 0.005 | 0.254 | 0.4 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| 30 s before the first claimed-voice unit | 10 to 19 | 0.084 | 0.155 | 0.32 | 0.008 | 0.011 | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) | 0.422 | 0.239 | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |
| 30 s before position-matched shifted points (5 per onset) | 10 to 19 | not printed (privacy rule) | 0.159 | 0.376 | 0.013 | 0.021 | not printed (privacy rule) | not printed (privacy rule) | not printed (privacy rule) | 0.431 | not printed (privacy rule) | a class reading 'not printed (privacy rule)' is counted in 'other sound, unclassified' |


## Departures and rows not computed

- **Departure from the split policy's wording** (accepted as the lead's decision 106.1, decided 2026-11-26 18:16Z).
  Deposit 2's split policy builds a data-tuned rule on exploration half A and runs it once on sealed half B (tier S),
  or cross-fits it over the two halves (tier X). Here the classes are fixed rules (the shared instrument was
  tuned on the tuning pool T, the development creators, before the prespecification), and the description is made
  once on all eligible non-development creators (tier S by count).
  Reason: T sits on the exploration side and is never read for a split reading, so fitting on T alone keeps both halves
  out of every fit (decision 88's reading). **Limitation: half B is no longer sealed for the acoustic measures described
  here.**
- et's prediction for non-language windows (no family effect): not computed (this batch does not join family loadings).
- The creator counts of the minutes 5-10 bins: not printed (privacy rule).
- The listening check (class c) stays closed (ruling 10).

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

- every class cell the privacy rule withholds reads one label, "not printed (privacy rule)", whatever the reason,
  and is counted in "other sound, unclassified"; the note column and the figure's legend are reworded in general
  terms (decision 109.3);
- the creator counts of the minutes 5-10 bins read "not printed (privacy rule)" (decision 109.2);
- the README states that the voice labels are model-coded (decision 109.7);
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
| `code/analyse_p11.py` | `4e2894fa0dfa0c59f7796bf2a7a3ac2b3bcd81148e43985817512111113355dc` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `public/data-r3-P11-classes.csv` | `4c38d9e399e808c63dc41ad52d7e383b2854819b6fa7d140f8565fc49789e18d` |
| `public/fig-r3-P11-codebook.pdf` | `4b72de4d8db3f13a6ecafba549e2e2489371521d51d07135179e73cc954d8935` |
| `public/fig-r3-P11-codebook.png` | `e27df9be7027d9eb0210ccb044a9b773fa7c5028aa0f0633e403287031e69b9a` |

`status.json` carries the same hashes; `contacts.md` lists every read with its time.
