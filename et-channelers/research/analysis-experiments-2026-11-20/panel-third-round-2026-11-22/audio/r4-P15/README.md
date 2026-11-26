# r4-P15: delivery at self-attributed voice switches

Written by the audio agent, a model agent working for the project lead (not a person); times from `date -u`. Class a.2,
run after r4-P03 under the lead's ruling 4. **Exploratory; not a test of H1-H10.** Seen creators only. Voice switches are
those the small model's labels place (model-coded, not checked by a person); "self-attributed" means presented by the
creator as another voice. Acoustic features describe the sound of these recordings (delivery), never a speaker's state or
a source; no person listened.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Question (programme):** delivery at self-attributed switches, read against matched edges and the creator's own range.
**Closest acoustic work (N13):** a laboratory within-subject comparison of trance channellers reading one story (Wahbeh
et al. 2019); within-talker stability across styles (Ferguson et al. 2024); within-person vocal variability (Lavan et al.
2019). This entry compares published recordings and claims no priority: a design "not found" in the members' searches
means only that. Prespecification: `../prespec.public.md` (published redacted), sections 4 and 10 (reading A7 of the speech member's table).

## How it ran

- **Tier:** X by count (outcome-free; the 23 non-development creators); the ladder's feature scales are
  fitted on the development creators; the reading is made once on all eligible non-development creators.
- **Own-range ladder (primary, A7):** per creator with 60 s of gated claimed interiors and 2 or more gated recordings with
  60 s of own-voice interior: a profile of articulation rate (log), F0 range, intensity variability and long-pause share,
  each in units of the between-creator SD of own-voice recording values; D_co (claimed profile to each own recording) minus
  D_oo (own to own across recordings); margin 0.20 SD; the negative control is the distance between the two halves of
  own-voice interiors within a recording, which D_co must exceed for "beyond the margin".
- **Switch curves:** all long, seam-free, gated voice boundaries (cue-free and cue-opened together) without a detected
  environment change (r4-P03's rule); the sustained shift minus matched edges, and the band, as in r3-P09.
- **Statistics:** 90% t interval on creator means, fixed (interval class not calibrated by r3-P30); A8 caps readings at
  undetermined below 12 eligible creators (and then, under the lead's decision 109.1, no estimate, interval or
  reading is printed).

## Results (run 2026-11-26 18:01Z; reruns 18:03Z and 18:06Z; rerun 19:13Z under the lead's decision 109)

**Not measurable acoustically in this corpus (fewer than 12 eligible creators after the background gate: A8).** Under the
lead's decision 109.1 (a rule that does not depend on the data), every estimate, interval and reading row prints
"not printed (A8: fewer than 12 eligible creators after the background gate)", and the figure is not published.

- **Battery:** the shared battery and its caps (`../common/README.md`; `../r3-P08/public/data-r3-P08-battery.csv`) apply
  to every row.
- **Decision 106.2:** A8 blocks this entry, which stays without a reading in this round. Running it with the tuning pool T
  added would be a new registration; it is on the fourth panel's agenda (the stored per-recording features make it
  cheap).

### Tables

**`public/data-r4-P15-ladder.csv`**

| row | creators | estimate | lo90 | hi90 | margin | words |
|---|---|---|---|---|---|---|
| D_co minus D_oo (primary, SD units) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.2 | not printed (A8: fewer than 12 eligible creators after the background gate) |
| D_co: claimed profile to own recordings (described) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |  | not printed (A8: fewer than 12 eligible creators after the background gate) |
| D_oo: own to own across recordings (described) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |  | not printed (A8: fewer than 12 eligible creators after the background gate) |
| negative control: own halves within a recording (described) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |  | not printed (A8: fewer than 12 eligible creators after the background gate) |
| D_co minus the negative control | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  |  | not printed (A8: fewer than 12 eligible creators after the background gate) |

**`public/data-r4-P15-reading.csv`**

| row | value |
|---|---|
| printed first | not measurable acoustically in this corpus (fewer than 12 eligible creators after the background gate: A8) |
| eligible non-development creators (ladder) | not printed (A8: fewer than 12 eligible creators after the background gate) |
| A8 | not measurable acoustically in this corpus (fewer than 12 eligible creators after the background gate: A8) |
| reading of the primary (A7) | not printed (A8: fewer than 12 eligible creators after the background gate) |

**`public/data-r4-P15-switch-curves.csv`**

| kind | feature | feature_text | creators | contrast | lo90 | hi90 | margin | words | leaves_band |
|---|---|---|---|---|---|---|---|---|---|
| entry | art | articulation rate (log; voiced-frame) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.223 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |
| entry | f0 | F0 range (SD units; voiced-frame; Tier 1) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.2 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |
| entry | lps | long-pause share (pause-tied; shared channel) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.05 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |
| exit | art | articulation rate (log; voiced-frame) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.223 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |
| exit | f0 | F0 range (SD units; voiced-frame; Tier 1) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.2 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |
| exit | lps | long-pause share (pause-tied; shared channel) | not printed (A8: fewer than 12 eligible creators after the background gate) |  |  |  | 0.05 | not printed (A8: fewer than 12 eligible creators after the background gate) |  |


## Departures and rows not computed

- **Departure from the split policy's wording** (accepted as the lead's decision 106.1, decided 2026-11-26 18:16Z).
  Deposit 2's split policy builds a data-tuned rule on exploration half A and runs it once on sealed half B (tier S),
  or cross-fits it over the two halves (tier X). Here the ladder's feature scales are fitted on the tuning pool
  T (the development creators) only, and the entry runs once on all eligible non-development creators (tier X by
  count).
  Reason: T sits on the exploration side and is never read for a split reading, so fitting on T alone keeps both halves
  out of every fit (decision 88's reading). **Limitation: half B is no longer sealed for the acoustic measures described
  here.**

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
No number changed: values are withheld, merged, re-banded or reworded.
Changes in this entry:

- under A8, every estimate, interval and reading row reads "not printed (A8: fewer than 12 eligible creators after
  the background gate)", and the figure is not published (decision 109.1);
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
| `code/analyse_p15.py` | `e7fca3e190eaa73424a71414a28217b0fb9e7a125304037403d995a1a970da5b` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `public/data-r4-P15-ladder.csv` | `ceba5c91e8c437efbdbd092a55c4542801356587cbee7fc9e1c778bd4c4dc295` |
| `public/data-r4-P15-reading.csv` | `ce31dfd4ef0aacb19ae6f9779b37e1a3bb9cef97eb4477bb60056bf60c37c623` |
| `public/data-r4-P15-switch-curves.csv` | `d92dfa8126768b02cc924edcc7d73e92226a5266ea183393881fc0a47670eefa` |

`status.json` carries the same hashes; `contacts.md` lists every read with its time.
