# Step-2 lexicon descriptions: the run record (operational choices fixed before any statistic)

Written 2026-11-26 after the seven prespecifications were hashed (12:46:51Z) and after the extra extract ran (12:50:29Z to
12:52:50Z; it computes no statistic: it re-matches r3-P42's extract, checks its totals against r3-P42's counts, and reads
the seen-only bundle and page text), and **before any statistic of these entries was computed**. UTC from `date -u`. By
the step-2 description agent (a model agent working for the project lead; not a person). It is hashed with the analysis
code before the analysis runs. Later changes are dated departures in the READMEs.

Exploratory; not a test of H1-H10.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What the extra extract did (prespec 0.1)

- Re-matched every token sequence of r3-P42's extract with all speech lists (as r3-P42's count step), kept the hits of
  L05, L06, L07, L08 (base rule), L10, L11, L12 and L14 with unit, side and tenth, L09's forms per recording outside frame
  units, and the T190 proxy as runs per unit (runs split at unit boundaries). Totals equal r3-P42's counts in every
  (list, term) cell, and tokens outside frames equal r3-P42's per-recording values.
- Bundle: 408 recordings of the 23 creators carry a voice record; the record model's sides equal the extract's sides in
  every recording inside the definition.
- Page text: 372 pages of the extract's recordings. **Web and e-mail addresses are removed from descriptions before
  matching** (links are L13's domain rows, which are page-only and not part of r3-P50's ratios; address fragments would
  otherwise add tokens). Page n-grams are kept only where they are also speech placebo candidates (the placebo rows
  come from r3-P42's speech tables).

## Choices the prespecifications leave open

1. One process runs the seven entries in the order r3-P48 package, r3-P51, r4-P29, r3-P52, r3-P53, r3-P55, r3-P56, with
   one register of printed creator counts (first printed form binds).
2. r3-P42's L05, L06, L11, L12 and L13 runs are repeated by its own `run_list` (same seeds and streams), so the placebo
   sets equal r3-P42's.
3. A1 re-matches placebos on stream `[C1-placebo seed, list, 1]` (r3-P42's A1 stream); A4 (without hits on L01's counted
   tokens) on stream `[C1-placebo seed, list, 3]`. A1 and A4 change a reading only when the full reading lies outside the
   band and the reduced one does not (r3-P42's rule).
4. r3-P50: a creator enters with page tokens and speech tokens above 0. The link-bound row widens a match cell one decile,
   then one dispersion band, at a time (r3-P42's sampler rule).
5. r3-P51: a T190 hit is a run of proxy tokens; the middle-model row uses `voice_sets.sides` with model "middle" on
   recordings the middle model labelled in full and whose units line up with the extract.
6. r3-P52: own-voice talks use the bundle's record-model rule-B labels (step 1's `own_only`); format from the voice map.
   The function-word placebo words are r3-P42's L09 draws, counted per recording from the extract outside frame units.
7. r3-P53: the difference of LAB-V's claimed share between a mode group and the other creators is a between-group
   difference, so its interval is the two-sample (Welch) t interval, the two-group analogue of r3-P30's t interval on
   creator means; r3-P30's class-B choice at the count is printed beside it.
8. r3-P56: DISSEM is counted in hits (per hour); the recall probe counts hit units; recordings enter the per-hour rows only
   if every unit has a start and an end time and the recording has asks labels.
