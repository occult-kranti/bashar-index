# ER: registered exploratory questions E1 and E3 (with E3-H)

Exploratory (registry A2); not a test of H1-H10. Second wave of the exploratory round (lead's decision D4, registry
2026-11-22 02:09). Every output here was made by code added after the exploratory reporting plan, on 2026-11-22. E1 and
E3 had status R in the plan (section 6.10: "not built as specified"); addendum 1 item 9 allows them to be reported as
not run if not built; they were built and are reported. The hold-out part of E3 (E3-H, plan section 8) was run by code
written after freeze 2, which departs from the plan's "code frozen in the freeze-2 record"; it ran once, after the same
code had run on the seen creators, and each read of hold-out material is logged as a contact. Place: S (supplement).

Everything here is recognizer output (the run's automatic transcripts), after the project's artefact filter. Nothing
was checked by a person, nothing was listened to, and no language model was used. No p-value is printed; intervals are
percentile intervals at the level stated beside each (90% and 95% here; levels differ between packages).

**Public form.** Aggregates over 5 or more creators only; every creator count printed is either published already or
lies 5 or more from every published count; no names, codes, ids, titles, quotations, per-creator or per-recording rows;
no minimum or maximum of a measure. Every numerator of a printed rate rests on 5 or more creators with a non-zero
count. Counts of thanks-phrase segments by half are not printed; chances per window are printed instead, and the
segments that the printed chances leave out (by difference from the public totals of the same transcripts) rest on 5 or
more creators (checked in `e1_analyse.py`).

**This file** is written by hand from the CSV files below and the checks their scripts record; no script writes it.
Revised on 2026-11-22 after the first verification (the BR-GS citation now uses only BR-GS's public form, addendum 2
item 4; the reading of E1 says only what was measured).

## E1: is the inserted thanks phrase tied to the decoding window or to silence? (`e1-thanks-by-tempo.csv`, `e1-descriptives.csv`, `fig-e1-thanks-by-tempo.png`)

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

**Data.** Seen creators only: the 1,284 transcripts of the English-only model (71 creators; the base of GRID and rv-R7),
of which 1,230 have a window in each half (71 creators). Hypotheses.md says E1 "runs first, on the hold-out creators";
the plan's row (section 6.10), written later, names seen recordings, and section 8 lists no hold-out part of E1, so no
hold-out material was read for E1.

**As registered.** Windows of the run's fixed 30-s decoding grid, the final window of each recording excluded, windows
of 20 words or more; each recording's windows split at its median articulation rate; insertions counted as the excess
of exact "thank you" segments starting in a window's last 3 s over 3/27 of those starting earlier; the chance per window
compared between the slower and the faster half; equivalence within a factor of 1.25; half labels permuted within
recording (9,999 draws).

**Choices made in building it (before its first result).** Articulation rate = estimated syllables per minute of speaking
time, i.e. word durations plus gaps under 0.3 s (pauses of 0.3 s or more left out), from the words after the artefact
filter v2; thanks-phrase segments are counted before the filter (GRID's definitions). Because the filter's positional
rule removes the late phrases, a counted insertion never enters the window's tempo. A window at the median is in neither
half. The estimand is pooled over recordings; its intervals come from 9,999 resamples of creators and then of
recordings within each drawn creator (H3's procedure); the 90% interval gives the equivalence reading (two one-sided 5%
readings against 0.8 and 1.25). The permutation reference is shown as the central 95% range of the ratio under permuted
labels, not as a p-value.

**Rows added after the exploratory reporting plan.** (a) The same split at the median share of each window's first 27 s
outside speaking time ("silence"), because articulation rate leaves pauses out by construction and the question names
silence. (b) The creator-equal version of the primary (each creator's chance per half, averaged over creators). (c) The
descriptions in `e1-descriptives.csv` (where in the window a thanks-phrase segment starts).

**Result.**
- Primary (pooled): the chance of an inserted phrase per window is 0.0259 in the slower half and 0.0195 in the faster
  half; ratio 1.33 (90% 1.16 to 1.51; 95% 1.14 to 1.55). With the half labels permuted the ratio lies between 0.90 and
  1.11 (central 95%). The 90% interval crosses 1.25, so equality within a factor of 1.25 is not shown.
- Creator-equal row (added after the plan): 1.14 (90% 0.91 to 1.45; 95% 0.87 to 1.50): smaller, and its interval
  includes 1. The pooled ratio's lean towards the slower half is therefore carried partly by creators with many
  insertions; the creator-equal version does not show it.
- Silence row (added after the plan): ratio of the more silent to the less silent half 0.74 (90% 0.64 to 0.86; 95% 0.62
  to 0.89); permuted central 95% 0.90 to 1.11. Equality within 1.25 is not shown either; in this split the windows with
  more silence in their first 27 s carry fewer insertions.
- Per 1,000 words the excess is 0.39 in the slower half and 0.25 in the faster half (pooled).

**Where in the window the phrase starts (descriptions added after the plan, `e1-descriptives.csv`).**
- In the primary's windows (both halves, pooled), a thanks-phrase segment starts in the last 3 s with chance 0.0231 per
  window (90% 0.0209 to 0.0254), and in a given 3-s stretch of the first 27 s with chance 0.00038 per window (90% 0.00027
  to 0.00050; pooled over the nine stretches). Each rests on 5 or more creators with a non-zero count.
- In non-final windows with no word after the filter, no thanks-phrase segment starts in the last 3 s; those that occur
  start in the first 27 s (from 5 or more creators), and the filter removed them by rules other than its positional one.

**What the built records add (already reported elsewhere; not recomputed here).**
- rv-R7 (paper review, build-robustness R7): in windows mostly covered by other recognized speech, a stand-alone thanks
  phrase starts in the last 3 s with probability 0.0234 per window (90% 0.0216 to 0.0253); in windows with no other
  recognized segment none starts in the last 3 s.
- BR-GS (the grid-shift re-decode of seen recordings, the grid moved by 15 s): the positional rule, applied on each
  decode's own grid, removes 55 thanks-phrase segments on the run grid and 37 on the shifted grid. Searched for in the
  other decode (within 1 s and within 2 s), the removals give "fewer than 5 creators with a recurring removal" on both
  grids; this is BR-GS's public form (addendum 2 item 4), and no share is printed. Thanks-phrase segments per hour of
  speech change by -0.40 between-creator SD (95% -0.88 to +0.08) when the grid moves.

**Reading.** The end-of-window phrase is tied to the decoding window: in E1's windows it starts in the last 3 s about
sixty times as often as in a 3-s stretch earlier in the window (pooled), it does not start in the last 3 s of windows
without other speech, and when the grid moves the positional rule again finds such phrases at the ends of the moved
windows, with fewer than 5 creators with a recurring removal (BR-GS). Equality within a factor of 1.25 is not shown, so
E1 does not establish that a positional rule alone is enough. The pooled chance per window is higher in the slower half
(90% interval above 1), while the creator-equal version's interval includes 1; it is lower in the more silent half (a
row added after the plan). In windows without other speech the phrase starts in the window's first 27 s, never in its
last 3 s (E1's description; rv-R7 agrees for the last 3 s), and there the filter removes it by rules other than the
positional one. No silence rule was evaluated.
Whether a per-word count of thanks or closing formulas carries tempo beyond arithmetic is not settled here: the pooled
ratio points that way, the creator-equal ratio does not show it. This is a statement about this pipeline's fixed windows
and this recognizer, not about the recognizer family.

**Limits.** Tempo and silence are measured from the same recognizer's word times, which the recognizer bridge (rv-R3;
GRID's re-analysis) found model-dependent (pause measures and word length in seconds differ between the two models). In
a window where the recognizer inserts the phrase, its timing of the other words may be affected by the same decoding, so
the association may lie inside the decoding of those windows rather than in the speaker's tempo. The creator-equal row
is weaker than the pooled one, so creators with many insertions carry part of the pooled ratio.

## E3 and E3-H: tempo and address over running time (`e3-edges-and-address.csv`, `e3-position-curves.csv`, `e3-position-curves-seen-simultaneous.csv`, `fig-e3-position-curves.png`)

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

**Data.** H3's own recordings and bins, read by the frozen H3 code (`h3_position.py`, artefact filter v1, H3's registered
filter): English, English-only model, not publisher-feed audio, 180 s trimmed at each end, at least 600 s and 800 words
left, ten bins of the remaining running time with 50 words or more each. Seen: 61 creators, 558 recordings. Hold-out
(E3-H): 17 creators, 169 recordings. Both sets equal H3's published sets, and H3's U was reproduced on both.

**As registered.** Two estimands, one each: the articulation rate at the edges (tenths 1 and 10, as H3) against the middle
(tenths 3 to 8), and second-person address in the last tenth against the first tenth. Built as creator-balanced means of
per-recording log ratios (address with H3's half-count rule), printed as ratios, with 90% and 95% intervals from 9,999
resamples of creators and then recordings (H3's procedure). Beside each, the exact centre of H3's circular-shift
reference (for address it is 1 by construction). Articulation rate as in E1 (syllables per minute of speaking time
without pauses of 0.3 s or more). Second person: you, your, yours, yourself, yourselves, you're, you've, you'll, you'd.

**Rows added after the exploratory reporting plan.** The recentred pace ratio; the rates behind each ratio; the first and
the last tenth each against the middle; words instead of syllables; the position curves (ten tenths each). The curves in
`e3-position-curves.csv` and the figure carry pointwise 90% intervals. For the seen curves,
`e3-position-curves-seen-simultaneous.csv` adds the simultaneous 90% sup-t band over the ten tenths that plan section 4
asks for (same 9,999 resamples). The hold-out curves have no simultaneous band: a deviation from plan section 4 (adding
one would need a further read of the hold-out file). No tenth is read on its own.

**Result, seen creators.**
- Pace: edge against middle 1.000 (90% 0.993 to 1.007; 95% 0.991 to 1.009); reference centre 0.999; recentred 1.001.
  After the trims, articulation rate at the edges differs from the middle by no more than about 1% (90% interval 0.993
  to 1.007; 237.4 against 237.2 syllables per minute of speaking time). Words instead of syllables: 1.002 (90% 0.994 to
  1.011).
- Address: last against first tenth 1.34 (90% 1.20 to 1.49; 95% 1.17 to 1.53); 43.0 second-person forms per 1,000 words
  in the first tenth and 53.0 in the last.

**Result, hold-out creators (E3-H), beside the seen ones, never pooled.**
- Pace: 1.026 (90% 0.992 to 1.068; 95% 0.987 to 1.078); reference centre 0.997; recentred 1.029 (90% 0.994 to 1.074).
- Address: 1.41 (90% 1.13 to 1.77; 95% 1.08 to 1.85); 39.5 and 47.5 per 1,000 words in the first and last tenth.
- Hold-out against seen (ratio of the two ratios, independent resamples; a heterogeneity statement, not a pooled
  estimate): pace 1.026 (90% 0.991 to 1.068); address 1.05 (90% 0.82 to 1.36).

**Balance.** The hold-out is the tail of an English-first run and is not exchangeable with the seen creators. In the
supplement, E3-H stands next to the balance table rv-D2 (Table B, `D2-table-B-balance.csv`, paper review
build-descriptive D2) and its transcript part rv-D2-H (package HOLD2, `rv-D2-H-transcript-covariates.csv` and
`rv-D2-H-love-plot.png`). rv-D2-H finds fewer recognized words per minute inside the recognizer's segments in the
hold-out (a recognizer-output measure, not a direct measure of speaking); the hold-out's articulation rates here are
lower in both edge and middle tenths, and the ratio compares each recording with itself.

**Limits.** The tempo arm rests on the recognizer's word times and pauses, which the recognizer bridge found
model-dependent; within one model a constant offset cancels in a ratio, but a position-dependent timing error does not,
and the edges hold teasers, music and other speakers. The pace results describe the recognizer's timing, not a measured
speaking rate. The grid shift (BR-GS) moved the word-based articulation rate with the same pause rule by -0.02
between-creator SD (95% -0.09 to +0.05). The address arm rests on word counts, which the bridge found to agree between
the two models. As hypotheses.md says, a rise in address has no reading as anything particular to channelling without
labels or a comparison set: closing parts of many talks address the listener. The pilot's untrimmed figures (another
creator set, another tempo definition) are not comparable with these.

## Files and code

| File | Written by (SHA-256) |
|---|---|
| `e1-thanks-by-tempo.csv`, `e1-descriptives.csv`, `fig-e1-thanks-by-tempo.png` | `e1_analyse.py` (`6c0cee36f86699006ec19ef60f7140bee63f5f40a46144a541ffa582ea64baae`; revision of 2026-11-22, run at 02:57:48Z; it replaced version `d4b05839...` of 02:27:55Z, and the table's numbers are unchanged), from the seen pass `e1_extract.py` (`f6b9d7cd6590a5ca1d6224bac979efe278bf2c49fd826bf9939efa4159bc892a`) |
| `e3-edges-and-address.csv`, `e3-position-curves.csv`, `fig-e3-position-curves.png` | `e3_report.py` (`c121431d23a9987268a065e113ed3a93baf7f9998414ae877ff2a178414b0ba6`), from `e3_run.py` (`4d2e6742609260cdd876b68855ae015c0b080699f55d0aa76040df6f4d3693e1`) on each group |
| `e3-position-curves-seen-simultaneous.csv` | `e3_supt_seen.py` (`7989a2ca95cc344255d27a3bbc36294246b0b63dc3de7727e7b55ea14a535cc7`; seen file only, run at 02:58:22Z), importing `e3_report.py` unchanged |
| `ER-README.md` | by hand, from the files above and the checks their scripts record |
| all | shared helpers `ercommon.py` (`0711d8d3a30c3b128a163483695f20b3c6a28fe16f7882fe8811b36060dde121`); the frozen H3 code (`h3_position.py` `d1cc2b2e...`, `artefact_filter.py` `72bccae0...`); GRID's `grid_common.py` (`e54c8ba8...`); `prep.py` (`49e7e4c3...`) |

## Figures in the release

The PNG files named in this README are the package's own drawings, which a release does not copy (D56). Every output of the package is drawn in the release gallery (`gallery/index.html`; records in `gallery/manifest.json`), under these figure ids: E1: E1-fig-1, E1-fig-2; E3-H: E3-H-fig-1, E3-H-fig-2; E3: E3-fig-1, E3-fig-2. Edited on 2026-11-26 in release pass 2's fix step (fix2, f01_edits.py; its SHA-256 is in the round's records), for privacy and consistency only.
