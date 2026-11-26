# rv-D3: where the time outside recognized speech sits

Made after a hold-out contact on 2026-11-22 (a text search that showed file names only).

Exploratory, paper review (registry A2/A7); not a test of H1-H10. Public form made at the release review (plan P10) on
2026-11-22 from the item's build of 2026-11-21 01:24 to 01:26 UTC (not re-run). Place: M (coverage figure); S (classes,
reconciliation); W (coverage figure, seen only). The hold-out beside the seen creators is rv-D3-H (package HOLD2); its
figure is drawn here as rv-D3-fig-4 from HOLD2's public file only.

**Question.** Where does the time outside recognized speech sit?

**Base.** 71 seen creators, 1,293 transcripts of the closed run (549.6 h), recognizer segments after artefact filter
v2. rv-D3-fig-4 uses HOLD2's base: English transcripts of the English-only model (seen 71 creators, 1,284 transcripts;
18 English hold-out creators).

**What is shown.**

| File | Content |
|---|---|
| `public/rv-D3-share-without-speech.csv` | Share of audio without speech under two definitions: pooled, creator-equal, creator median, share held by the 5 creators with the most |
| `public/rv-D3-classes-by-position.csv` | Time by class (inside segments; gaps under 3 s, 3 to 30 s; stretches of 30 s or more) and position |
| `public/rv-D3-aligned-coverage.csv` | Coverage of 15-s bins aligned at the start and the end, all lengths and by length band (creators and transcripts per band), with sup-t and pointwise bands |
| `public/rv-D3-companion-rows.csv` | Coverage of the last partial decoding window, the window before it, the middle, the first and last 15 s |
| `public/rv-D3-partial-window-by-length.csv` | The last partial window and the window before it, by the partial window's length |
| `public/rv-D3-reconciliation.csv` | Per-recording difference of the two definitions (quantiles) and their rank correlation |
| Gallery group B-D, `rv-D3` | fig-1 coverage, all lengths (M, W); fig-2 by length band (S); fig-3 classes by position (S); fig-4 hold-out beside seen (rv-D3-H's rows, M) |

**What it shows.** About 15% of the seen creators' audio lies outside recognizer segments (pooled 14.8%, 95% interval
10.9 to 19.9; creator median 11.4%) and 12.1% (7.7 to 17.5) outside the voice detector's speech; the five creators with
the most hold 46% of the detector's non-speech time. Of the time outside segments, 4.4 points lie before the first or
after the last segment. Coverage is lowest at the edges: 0.75 (0.70 to 0.80) of the first 15 s and 0.49 (0.42 to 0.55)
of the last 15 s, against 0.87 in the middle of recordings of 6 min or more. The last, partial 30-s decoding window is
covered 0.48 against 0.78 for the full window before it. The last minute holds more time outside recognized speech than
the rest, mostly in gaps of 3 to 30 s (creator-equal 0.12 against 0.03). The two definitions agree per recording at
Spearman 0.89 (median difference 3.5 points). Beside the seen creators, the English hold-out creators' coverage lies
lower over the first and last three minutes, inside overlapping simultaneous bands (rv-D3-H; not tested against each
other).

**Withheld, and why.**

- The leave-one-creator-out range of the pooled share: each of its ends, beside the pooled share, isolates one creator
  (pairs rule). The share held by the 5 creators with the most is printed instead.
- Creator counts per 15-s bin (beside the band's count they would be nested counts 1 to 4 apart); every bin rests on 30
  or more creators. Creator counts 1 to 4 below 71 read "all but fewer than 5 of 71".
- The hold-out's transcript count in rv-D3-fig-4: beside the hold-out's published transcript and non-English counts it
  would isolate a single transcript; the base is given as 18 English hold-out creators.

**Interval levels.** 95% throughout: creator bootstrap for pooled shares and creator medians; t and creator bootstrap
for creator-equal shares; simultaneous (sup-t) 95% bands from 2,000 creator-then-recording resamples for the coverage
curves (pointwise 95% bands beside them in the table). Each curve is read through its simultaneous band.

**Caveats.** Time outside recognized speech is not "no speech": music, toning, meditation, silence and long pauses are
not told apart. The last end-aligned bin lies in the last, partial decoding window, so its dip mixes decoding and
content. The voice detector has no positional figure. Coverage is a recognizer-output measure.

**Fix pass (2026-11-22, after the release verifier).** The length-band rows and rv-D3-fig-2 are withheld (the
superseded figure files are kept privately, not deleted), and rv-D3-fig-4 drops the hold-out transcript count. No new
value is printed.

**Release pass 2 (2026-11-25, lead's decision D47).** HOLD2 withdrew its seen rows by length band from rv-D3-H's
public files, so the pair that withheld them here no longer exists. The two writers were rerun unchanged: the
coverage curves by length band (under 5 min; 5 to 20 min; 20 to 60 min; 60 min or more), with their creator and
transcript counts, and rv-D3-fig-2 are printed again. No other value changed.

**Writers.** Tables: `build_tables_D.py` (SHA-256
`d38dc81e39a5d9606ca78aae9138138e1a429de11a2082f3e3de533467d1bb92`); figures: `plot_D.py` (SHA-256
`ab68d497db1726d7fd12edfbec30e72b71efe5b208be0886822e8c014fa44caf`).
