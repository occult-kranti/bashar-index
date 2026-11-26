# r3-P15 / r4-P13, acoustic rungs: person or register? The distance ladder on delivery (audio addendum)

Written 2026-11-26 (UTC, from `date -u`) by the audio-addendum agent, a model agent working for the project lead (not a
person), under the lead's decision 106.4. Prespecification: `../prespec.public.md` (published redacted), section 4 (hashed 2026-11-26T18:39:23Z,
before any outcome). Analysis 18:42:58Z to 18:43:14Z; publication from 18:48:08Z.

**Exploratory; not a test of H1-H10.** Seen creators only. Voice labels are model-coded (the small model) and not checked
by a person; agreement, never accuracy. Acoustic features describe the sound of these recordings (delivery), never a
speaker's state or a source; no person listened. Every reading is about delivery style, never about a source. Computed
from the stored per-recording summaries; no audio was read here.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What was measured

Step 5's r3-P15 built the ladder on function-word profiles. The round-3 design adds "acoustic rungs of the ladder on
scale-free features only, never timbre". Here the profile is four scale-free delivery features: articulation rate (log),
F0 range (semitones relative to the recording's own median; Tier 1), intensity variability (the within-chunk SD of
voiced-frame level, so gain differences between recordings do not enter) and long-pause share. No tilt, flatness,
bandwidth or band level. Parts hold exactly 120 s of gated clean interior (12 chunks of 10 s drawn without replacement,
20 draws, as r3-P15's rarefaction). Distance: Euclidean over the features in two scalings, both fitted on the tuning pool
T only: S1 the between-creator SD, S2 the own voice's recording-to-recording SD.

Rungs (as r3-P15): own-own, claimed-claimed and claimed-own halves of one recording; own-own and claimed-own across
recordings; pooled halves against other creators' claimed and own voices. Contrasts P1 = CO - OO, P1b = CC - OO,
P2 = CO_x - OO_x, P3 = CX - CO_p, P3b = OX - OO_p, each in units of the between-creator SD of the reference distance;
margin 0.20; primary P1, P2 and P3 on the composite profile, a direction only if S1 and S2 agree.

**Tier: unsplit** (deposit 2's split policy names r3-P15): all seen creators, once. Departure from the split policy's
wording, accepted as the lead's decision 106.1: the data-tuned part (the scalings) is fitted on the tuning pool T only,
not built on exploration half A, and each reading is made once on all eligible creators. Reason: T sits on the
exploration side and is never read for a split reading, so fitting on T alone keeps both halves out of every fit
(decision 88's reading). Limitation: half B is no longer sealed for the acoustic measures described here.

**Interval:** r3-P15's rule, r3-P30's choice for C_standardised at the row's count: the t interval on creator means, the
same at every simulated count from 30 up; every printed row has 30 or more gated creators (A8 met); a row under 30 would
read "not computed or not printed". The reference rungs of the standardised contrasts (own-own same recording,
own-own across recordings, claimed-own pooled, own-own pooled) print no interval, a fixed rule (the lead's
decision 114).

**Battery caps (audio prespecification section 3, applied to a composite as the addendum's prespecification fixes):** the
composite contains articulation rate (criterion 1's slope not met: no "within") and F0 range (criterion 3 not met: no
direction), so composite rows read at most "undetermined (battery criteria 1 (rate slope) and 3 (pitch range) not met)".
Per-feature rows carry their own feature's cap.

## Results (composite profile; S1 and S2)

| Row | Creators | S1 (90%) | S2 (90%) | Words before the caps | Words |
|---|---|---|---|---|---|
| P1 same recording, claimed-own minus own-own (primary) | 30 or more | 0.37 (-0.02 to 0.75) | 0.30 (-0.04 to 0.65) | undetermined | undetermined |
| P1b same recording, claimed-claimed minus own-own | 30 or more | -0.44 (-0.80 to -0.07) | -0.43 (-0.80 to -0.06) | undetermined | undetermined |
| P2 across recordings (primary) | 30 or more | 0.04 (-0.09 to 0.16) | 0.09 (-0.05 to 0.23) | undetermined (the scalings disagree) | undetermined (the scalings disagree) |
| P3 pooled: other creators' claimed minus claimed-own (primary) | 30 or more | 0.79 (0.59 to 1.00) | 0.87 (0.64 to 1.11) | beyond the margin (nearer the creator's own voice) | undetermined (battery criteria 1 and 3 not met) |
| P3b pooled: other creators' own minus own-own | 30 or more | 1.36 (1.18 to 1.54) | 1.65 (1.44 to 1.87) | beyond the margin (own voices of different creators farther apart) | undetermined (battery criteria 1 and 3 not met) |

**The entry's reading on the acoustic rungs: undetermined** (by construction under the battery caps; r3-P15's cases 1 to 3
cannot be read).

**Described per feature** (`public/data-r3-P15-acoustic-features.csv`; not the reading): on articulation rate and on
intensity variability the claimed voice is nearer the creator's own voice than other creators' claimed voices (P3 beyond
the margin, 1.31 and 0.95 SD); on the same-recording and across-recording rungs no single feature reads beyond the margin;
P1b's point estimates are negative on the composite and on every feature (claimed-claimed halves of one recording nearer
each other than own-own halves, the direction step 5 read on function words), but every P1b interval reaches inside the
margin; the between-person scale (P3b) is beyond the margin on articulation rate, intensity variability and long-pause
share. F0-range rows read neither way (criterion 3).

**In words.** On scale-free delivery features, the claimed-own distance within a recording exceeds the own-own noise band
by about a third of a between-creator SD, with an interval from about zero to 0.75 (P1 undetermined), and the claimed voice
lies much nearer the creator's own delivery than other creators' claimed voices (P3, capped). Delivery, like function words,
carries the speaker. A reading is never a finding.

Predictions deposited: none (deposit 2's cells for r3-P15 and r4-P13 are silent); nothing is scored. Multiplicity: 56
primaries; if every true effect sat at half its margin, about 2.8 readings beyond the margin would be expected by chance.

## Rows not computed

The decode rung (text only, step 5); topic-matched segments, the transplant placebo and the recitation-flagged sensitivity
row (as step 5); middle-model rows; timbre (excluded by design).

## Departures and choices (stated)

1. The two scalings stand in for r3-P15's two standardisations (an unstandardised profile has no meaning for features in
   different units); fixed in the prespecification.
2. Parts of 120 s of interior (F0 range reaches split-half reliability 0.7 at 120 s, battery criterion 7) rather than 200
   tokens; same-recording halves are cut by chunk count in time order; a recording enters the same-recording rung only when
   each half holds 12 full chunks (a stricter form of the prespecification's 240 s of interior).
3. The pooled rung uses claimed interiors of recordings in the pass: conversation and multi-presenter recordings have no
   audio (no third party's voice is processed), a departure from E2's own rule, stated in the prespecification.

## Files

| File | What |
|---|---|
| `public/data-r3-P15-acoustic-contrasts.csv` | composite contrasts P1 to P3b under S1 and S2, with words |
| `public/data-r3-P15-acoustic-features.csv` | the same contrasts per feature (described) |
| `public/data-r3-P15-acoustic-ladder.csv` | composite rung distances (described; the reference rungs without interval) |
| `public/data-r3-P15-acoustic-reading.csv` | the profile, scalings, caps, primaries and the entry's reading |
| `public/fig-r3-P15-acoustic-ladder.png`, `.pdf` | the acoustic ladder and the per-feature contrasts |
| `code/analyse_p15a.py`, `code/publish_p15a.py`, `code/style.py` | analysis, publication, style (copied unchanged) |
| `contacts.md`, `status.json` | contacts; every file's SHA-256 |

## Privacy

No per-creator or per-recording value or point; no absolute pitch, no timbre; no names, ids, titles or quotations. Counts
print as "30 or more", a band inside which r3-P30's interval choice is one method (decisions 64 and 71). Values that could
narrow a banded count are not printed. Checks: `../README.md`.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Change by the lead's decision 113

2026-11-26T19:57:53Z (UTC, from the clock). No number changed. The prespecification is cited as its published, redacted
copy (`../prespec.public.md`), hashed at 18:39:23Z (UTC), before any outcome; the hash is kept privately (step-1 decision 49 item i); its citation of the audio
prespecification's hash is replaced. CSV headers are rewritten by rerunning the code for headers only, and every hash in
`status.json` is refreshed; the originals are listed there under `not_published`.

## Change by the lead's decision 114

2026-11-26T20:13:50Z (UTC, from the clock). No number changed. The reference rungs of the standardised contrasts print no interval, a fixed rule (ladder table, CSV headers and
figure; the figure is redrawn by this part's code). The contact log carries the half-B limitation of decision 106.1.
