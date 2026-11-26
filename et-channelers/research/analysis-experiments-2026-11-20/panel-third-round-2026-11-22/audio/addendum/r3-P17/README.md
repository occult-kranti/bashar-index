# r3-P17, acoustic primary: the calm-register control on acoustic delivery (audio addendum)

Written 2026-11-26 (UTC, from `date -u`) by the audio-addendum agent, a model agent working for the project lead (not a
person), under the lead's decision 106.4. Prespecification: `../prespec.public.md` (published redacted), section 3 (hashed 2026-11-26T18:39:23Z,
before any outcome). Analysis 18:41:26Z to 18:41:32Z; publication from 18:46:54Z, redone under decision 109 at 18:55Z.

**Exploratory; not a test of H1-H10.** Seen creators only. Voice labels and the recording's main kind are model-coded and
not checked by a person. Acoustic features describe the sound of these recordings, never a speaker's state or a source;
no person listened. Computed from the stored per-recording summaries; no audio was read here.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Not measurable acoustically in this corpus (fewer than 12 eligible creators after the background gate: A8).** The
primary contrast, the claimed voice against the same creators' own-voice guided practice, has fewer than 12 eligible
creators after the gate. Under the lead's decision 109 item 1 (a rule that does not depend on the data), every estimate,
interval and reading row of this part reads "not printed (A8: fewer than 12 eligible creators after the background gate)",
and no figure is published.

## Design (as registered)

- **Groups** (r3-P17's prespecification): CL claimed voice outside guided practice; CLG claimed-voice guided practice; OWG
  own-voice guided practice; OWT own-voice talks (solo format). A creator enters a group with 300 or more words in it and
  60 s or more of gated clean interior of the group's spans (speech-to-background ratio 25 dB or more; 10 s dropped inside
  each span end).
- **Measures** (round-3 design: "acoustic rate and energy pauses on gated spans as primary, recognizer rows as
  sensitivities"): acoustic articulation rate (nuclei per second of phonation time) and acoustic long-pause share (acoustic
  pauses of 1 s or more over interior time). The recognizer rows are r3-P17's published text rows.
- **Contrasts:** C3 (primary) CL against OWG; C2 OWG against OWT; C1 CL against OWT; C4 CLG against OWG. Margins |log
  ratio| 0.223 and 0.05; the t interval on creator means, fixed in advance.
- **Tier: unsplit** (deposit 2's split policy names r3-P17): all seen creators. Departure from the split policy's wording,
  accepted as the lead's decision 106.1: data-tuned parts are fitted on the tuning pool T only and each reading is made once
  on all eligible creators (this part has no data-tuned part). Reason: T sits on the exploration side and is never read for
  a split reading, so fitting on T alone keeps both halves out of every fit (decision 88's reading). Limitation: half B is
  no longer sealed for the acoustic measures described here.
- **Battery:** rate rows never read "within the margin (B)" (criterion 1's slope not met); they may read beyond
  (criterion 3 met for rate). Long-pause rows carry no battery cap.

## Rows

Every contrast and group row: not printed (A8: fewer than 12 eligible creators after the background gate). The entry's
reading per measure: not printed (A8). r3-P17's published text rows stand as published (step 5).

## Rows not computed

Claimed-voice guided practice and C4 (too few terms or creators), as in the text rows. A run on a larger pool would be a new
registration (the fourth panel's agenda, as decision 106.2 says for r3-P09 and r4-P15).

Predictions deposited: none (deposit 2's cells for r3-P17 are silent; occult's reading is not attributed to an account);
nothing is scored. Multiplicity: 56 primaries; if every true effect sat at half its margin, about 2.8 readings beyond the
margin would be expected by chance. A reading is never a finding.

## Files

| File | What |
|---|---|
| `public/data-r3-P17-acoustic-contrasts.csv` | the contrasts, each "not printed (A8)", C4 not computed |
| `public/data-r3-P17-acoustic-groups.csv` | the groups, each "not printed (A8)", CLG not computed |
| `public/data-r3-P17-acoustic-reading.csv` | the A8 statement, the battery, the rows not computed |
| `code/analyse_p17a.py`, `code/publish_p17a.py`, `code/style.py` | analysis, publication, style (copied unchanged) |
| `contacts.md`, `status.json` | contacts; every file's SHA-256 |

## Privacy

No per-creator or per-recording value; no estimate is printed. Checks: `../README.md`.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Change by the lead's decision 113

2026-11-26T19:57:53Z (UTC, from the clock). No number changed. The prespecification is cited as its published, redacted
copy (`../prespec.public.md`), hashed at 18:39:23Z (UTC), before any outcome; the hash is kept privately (step-1 decision 49 item i); its citation of the audio
prespecification's hash is replaced. CSV headers are rewritten by rerunning the code for headers only, and every hash in
`status.json` is refreshed; the originals are listed there under `not_published`.

## Change by the lead's decision 114

2026-11-26T20:13:50Z (UTC, from the clock). No number changed. The contact log carries the half-B limitation of decision 106.1.
