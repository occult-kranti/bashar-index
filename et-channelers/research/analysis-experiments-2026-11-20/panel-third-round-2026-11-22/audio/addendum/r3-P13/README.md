# r3-P13 (card b2), the seen exploration: a label-free acoustic hypothesis (audio addendum)

Written 2026-11-26 (UTC, from `date -u`) by the audio-addendum agent, a model agent working for the project lead (not a
person), under the lead's decision 106.4. Prespecification: `../prespec.public.md` (published redacted), section 5 (hashed 2026-11-26T18:39:23Z,
before any outcome). Analysis 18:43:58Z to 18:44:16Z; publication from 18:50:04Z, redone under decision 109 at 18:56Z.

**Exploratory; not a test of H1-H10.** Seen creators only (the tuning pool T). The events are rule-located (RX's cue
patterns on the transcript); no voice label locates them, but the audio around them is admitted only where the model-coded
labels mark own or claimed speech (no third party's voice is processed). Acoustic features describe the sound of these
recordings, never a speaker's state or a source; no person listened. Computed from the stored per-recording summaries.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Not measurable acoustically in this corpus (fewer than 12 eligible creators after the background gate: A8).** The
framing-cue family had fewer than 12 eligible creators in T already before the gate (an outcome-free count, recorded in
the prespecification). Under the lead's decision 109 item 1, every estimate, interval and reading row reads "not printed
(A8: fewer than 12 eligible creators after the background gate)", and no figure is published.

## Design (as registered)

- **Card b2:** in fresh creators, voiced-frame delivery changes after a rule-located shift into a claimed voice more than
  after placebo hits, announced non-channelled switches and position-matched points, and more than at the comparison
  strata's opening formulas; registered only if the seen exploration curves leave the placebo band.
- **Pool: the tuning pool T only.** The exploration is a data-tuned search (which cue families and lags to register), so it
  runs on T. Departure from the split policy's wording, accepted as the lead's decision 106.1: data-tuned parts are fitted
  on T only, not built on exploration half A. Reason: T sits on the exploration side and is never read for a split
  reading, so a search on T alone keeps both halves out of it (decision 88's reading). Limitation: half B is no longer
  sealed for the acoustic measures described here.
- **Events:** the first hit in a recording of RX's opening families with hit-weighted read precision 0.80 or more (RXP: J1
  announcement, J2b "we are" + group; J2a is below it); placebo events: the first hit of RX-CB's placebo lists for J1 and J2;
  5 shifted points per event (same recording and tenth, 30 s or more from any hit). An event enters with a gated recording
  and 40 s or more of admitted time in each of -60 to -10 s and +10 to +60 s.
- **Features and curves** (r3-P09's code): articulation rate (log), F0 range (SD units fitted on T), long-pause share
  (pause-tied), in 10-s windows from -60 to +60 s; the sustained shift; the permutation-maximum band from the shifted
  points. The leak-free planning SD (the speech member's round-3 Q4, acoustic version) and the creators needed for a
  fresh-creator test.
- **Battery:** articulation-rate rows may read beyond (criterion 3 met) but never "no change" (criterion 1's slope);
  F0-range rows read neither way (criterion 3).

## Rows

Framing-cue rows, placebo-hit rows, framing cue minus placebo, and the planning SD with the power curve: not printed (A8:
fewer than 12 eligible creators after the background gate).

**The registration condition** (card b2): not met in this round. The exploration is not measurable acoustically here, and
the announced-switch placebo and the difference in differences, which the round-3 design requires before any
registration, are not available.

## Rows not computed

- Footing change points: r3-P18's locator is stored only for the 11 voice-eligible non-development creators; rebuilding it
  on T reads transcript text.
- Announced non-channelled switches: no list exists; writing one would be a new registration.
- The difference in differences against the comparison strata's opening formulas: no comparison stratum in the corpus (a
  new collection).
- A run on a larger pool would be a new registration (the fourth panel's agenda, as decision 106.2 says for r3-P09 and
  r4-P15).

Predictions deposited: none (deposit 2's cells for b2 are silent); nothing is scored. Multiplicity: 56 primaries; if every
true effect sat at half its margin, about 2.8 readings beyond the margin would be expected by chance.

## Files

| File | What |
|---|---|
| `public/data-r3-P13-exploration.csv` | every row "not printed (A8)", and the rows not computed |
| `public/data-r3-P13-reading.csv` | the A8 statement, the pool, the registration condition, the battery |
| `code/analyse_p13x.py`, `code/publish_p13x.py`, `code/style.py` | analysis, publication, style (copied unchanged) |
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
