# r3-P17: a calm-register control, text rows (prespecification)

Written 2026-11-26 from 14:07:22Z (UTC, from `date -u`) by the step-5 agent (a model agent working for the project lead;
not a person), before any outcome of this entry was computed. Shared rules: `../common/prespec-common.md`. Class a.1 for
the text rows; the acoustic primary is a.2 and is not computed here (audio, later). **Tier: unsplit** (the split policy
names r3-P17): all 71 seen creators, once. The expected reading is "not informative at this size".

**Exploratory; not a test of H1-H10.** Voice labels and the recording map's main kind are model-coded and not checked by a
person. Guided practice is split by voice because, in occult's reading (a reading by a non-holder), many guided meditations
in this milieu are led in a claimed voice.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Groups (per creator; units outside H1's excluded formats)

- **CL** claimed voice outside guided practice: claimed-voice units (primary definition) of recordings whose main kind is
  not guided practice.
- **CLG** claimed-voice guided practice: claimed-voice units of guided-practice recordings.
- **OWG** own-voice guided practice: own-voice units (own-solo definition) of guided-practice recordings.
- **OWT** own-voice talks: own-voice units (own-solo definition) of own-talk recordings of the solo format.
- A creator enters a group with 300 or more words in it (H1's span size).

## 2. Text rows (recognizer word times; no audio)

Per creator and group, pooled over the group's runs of consecutive words (a run ends where the next word belongs to
another group or another recording):
- **Articulation rate**: syllables (`features.syllables`) per second of speaking time, speaking time being the run time
  (first word start to last word end) minus the gaps between words of 0.3 s or more (E8's definition).
- **Long-pause share**: time in gaps between words of 1 s or more over the run time. Seam rule (GRID's): a gap under 5 s
  that contains a multiple of 30 s is dropped from both numerator and denominator. No cap on long gaps (long silences
  belong to the register this control is about); stated.
- Fillers, pauses per 100 words and acoustic measures are not rows of this entry.

## 3. Contrasts and readings

| Row | Contrast (within creator) | Creators |
|---|---|---|
| C3 (primary) | CL against OWG: the claimed voice against the same creators' own-voice guided practice | both groups |
| C2 | OWG against OWT: the calm register's own shift | both groups |
| C1 | CL against OWT: the claimed voice against own-voice talks (the E5- and H1-like reference) | both groups |
| C4 | CLG against OWG: guided practice split by voice | both groups (fewer than 5 eligible: not computed) |

- Rate: log ratio (first group over second); margin |log| 0.223. Long-pause share: difference (first minus second);
  margin 0.05.
- **Interval: fixed in advance, the t interval on creator means (90%).** For the rate rows r3-P30's class G (per-creator
  difference between two classes of recordings, log ratio) chooses the same method, holding, at every simulated count from
  12 up; the share rows compare groups of different recordings, which no r3-P30 class describes, and carry "interval
  class not calibrated by r3-P30". The method is fixed here, not chosen by the count (two of these sets print as bands).
- Words (no deposited direction): "beyond the margin (first group higher)", "beyond the margin (first group lower)",
  "within the margin (B)", "undetermined"; fewer than 5 creators: "not computed (too few terms or creators)".
- **The entry's reading** per measure (only these words): "the calm-register account covers the claimed voice's
  difference on <measure>" if C3 reads B and C1 reads beyond the margin; "the claimed voice differs from own-voice guided
  practice on <measure>" if C3 reads beyond the margin; otherwise "not informative at this size (undetermined)".
- Creator-balanced means per group (with t intervals) are printed as described rows; no histogram is drawn over a group
  whose count prints as a band; no overall mean across groups is printed.
- Predictions deposited: none (deposit 2's cells for r3-P17 are silent; occult's reading is not attributed to an
  account). Nothing is scored.

## 4. Plot

Creator-balanced means of articulation rate and long-pause share for CL, OWG and OWT (CLG not computed), with 90%
intervals, beside the paired contrasts C1 to C3 against their margins. Distributions over creators only; no point per
creator.

## 5. Not run here

The acoustic primary (audio, later); the sensitivity rows without recitation-flagged recordings (the recitation cue class
is thin on tier L, step 2); middle-model rows.
