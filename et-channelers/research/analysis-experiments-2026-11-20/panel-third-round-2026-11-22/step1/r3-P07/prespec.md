# r3-P07 prespecification: boundary anatomy from stored word times and text

Written 2026-11-26T06:26Z (UTC, from `date -u`; the exact time and this file's SHA-256 are in `prespec-record.md`) by a
step-1 agent (a model agent working for the lead; not a person), before any feature value near a boundary was computed.
Only outcome-free structure had been probed (`code/probe_p07.py`: formats, claimants, field names, counts of boundaries
by format and of the creators holding them). Deposit 2 was merged before this entry started. Known leak (split policy):
the writer has read the exploratory round's published aggregates (rv-D3, RX-CB, ENTRY-E3, GRID, E1, nlp-R7, PT-cd) and
the step-1 results of r3-P01 and r3-P02. This entry runs on all seen creators and is not split (descriptive; split
policy).

Exploratory; not a test of H1-H10. Seen creators only. Voice labels are model-coded and not checked by a person;
transcripts and word times are recognizer output, not checked by a person.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What the programme fixes (programme 2.1, r3-P07; programme-decisions.json; margins register)

Describe time outside recognized speech, and a ramp or a step at claimed-voice entries and exits, against
position-matched shifted boundaries; descriptive wording only (never "induction" or "return"); edited recordings split
from audience sessions; plot: small multiples per feature, entries and exits as columns, with the shift band and a
placebo curve; solo and audience-session panels where each holds 5 or more creators. The margins register lists the
entry as a description with no margin; deposit 2's default margins by measure type are used as the yardstick of the
described rows. The lead's step-1 decision 7 passes the seam-zone exclusion row (within 1 s of a run-grid seam) to this
entry; decision 5 passes r3-P02's described fact that pauses couple with punctuation less closely in the claimed voice.

## Choices this file fixes (the programme leaves them open)

1. **Labels.** Small model (the seen label of record), rule B label ("B"), as r3-P02 used them: claimed voice = V2 or V3;
   every other label is "not claimed". No claimant restriction (r3-P02's base). The middle model is not used (departure:
   no middle-model rows are built).
2. **Boundaries.** An entry is a change from a not-claimed unit to a claimed unit; an exit the change from a claimed unit
   to a not-claimed unit (adjacent sentence units of the filtered transcript of record). Its time is the midpoint of the
   gap between the last word of the earlier unit and the first word of the later unit (word times of the filtered
   transcript of record, which the voice units index: `rv-words.private.pkl`, seen only).
3. **Panels (the split).** By the voice map's format (model-coded): **solo** (read as the programme's "edited
   recordings": the stored data hold no field saying whether a recording was edited, so the map's single-presenter
   format stands in, stated as a departure) and **audience session**. A row pools **all labelled recordings** (every
   format) besides. A panel or row is printed only where it holds 5 or more creators with a boundary of that type.
4. **Features** (each computed from stored word times and text, in 2-s bins from -60 s to +60 s around the boundary;
   a bin's part outside the recording is left out of its denominator):
   - F1 **time outside recognized speech** (primary): share of the bin's time not inside any recognized word interval
     (the union of [start, end] of the filtered words). Margin: 5 points (difference in shares).
   - F2 recognized words per minute (word starts in the bin per minute of bin time). Margin: ratio outside 0.80 to 1.25
     (log 0.223). r3-P30 class A_log_ratio.
   - F3 share of words with stored word probability below 0.5 (r3-P01's family A threshold). Margin: 5 points. Class
     B_share_difference.
   - F4 first-person singular forms per word (features.py's FP_SING on the plain form's host: i, me, my, mine, myself).
     Margin: log 0.223. Class H_rare_counts.
   - F5 first-person plural forms per word (FP_PLUR: we, us, our, ours, ourselves). Margin and class as F4.
   - F6 second-person forms per word (you, your, yours, yourself, yourselves; host of a contraction; written here).
     Margin and class as F4.
   F1's class is B_share_difference.
5. **Ramp and step statistics** (per boundary type, feature and panel). Windows: W1 = [-60, -30) s, W2 = [-10, 0) s,
   W3 = (0, 10] s, W4 = (30, 60] s.
   - **step** = value(W3) - value(W2);
   - **ramp before** = value(W2) - value(W1);
   - **ramp after** = value(W4) - value(W3).
   For shares (F1, F3) the value is the share and the statistic a difference; for rates (F2, F4 to F6) the value is the
   log rate with 0.5 added to the count (F2: log of (words + 0.5) per minute of window time; F4 to F6: log of
   (forms + 0.5) / (words + 0.5)) and the statistic a log ratio. Values are pooled within a recording (sums of
   numerators and denominators over the recording's boundaries of that type) and the creator value is the plain mean of
   its recording values (creator means of recordings, r3-P30's design).
6. **Reference S: position-matched shifted boundaries (the shift band).** Each real boundary at time t of a recording of
   duration D is moved, 200 times, to a sentence-unit boundary of the same recording that is not a claimed-voice
   boundary, drawn uniformly from those whose time u satisfies 20 s <= |u - t| <= max(0.1 D, 20 s) (the same position
   band, within a tenth of the recording either side, and far enough for the step windows not to hold the real
   boundary). A boundary with no such candidate enters no draw (counted). The S-centred statistic of a creator is its
   real statistic minus the mean over draws of the same statistic computed on its shifted boundaries (same pooling).
   The shift band of a profile is the 5th to 95th percentile over the 200 draws of the creator-balanced mean profile
   (percentiles over draws, not quantiles of creator values).
7. **Reference P: the placebo curve.** The same creator's own-voice-only recordings (no unit labelled V2 or V3), in
   formats other than conversation and multi-presenter (r3-P04's ST hosts): for each real boundary, 50 draws, each a host
   recording chosen at random with a time at the boundary's position fraction t / D of the host's duration plus a
   uniform shift within +-0.05 of the host's duration, moved to the host's nearest sentence-unit boundary. The placebo
   curve is the creator-balanced mean over creators with hosts; P-centred statistics (real minus the mean over draws of
   the placebo statistic) are printed as a second described row for the primary feature F1, on those creators.
8. **Intervals.** 90%, by the method r3-P30's `interval-choice.csv` selects for the feature's design class at the row's
   creator count (the row of the largest simulated count at or below it); random-effects methods use creators with two
   or more recordings, as r3-P30's battery does (no variance floor beyond the battery's). The t interval on creator means
   is printed beside every row as a sensitivity column. Where r3-P30 finds no method that holds, the row's description
   is capped ("no interval method holds at this count").
9. **Wording of described rows** (no reading A or B; descriptive only): "wholly beyond the margin, above" or "below";
   "wholly inside the margin"; "crosses the margin"; "not computed (fewer than 5 creators)". The S-centred statistic is
   the printed estimate; the uncentred and P-centred statistics are printed beside it. No direction is named, so both
   sides are described alike. No row is called a finding, and none is worded as "induction" or "return".
10. **Seam-zone exclusion row** (lead's decision 7): the primary feature's S-centred statistics recomputed with every
    real boundary whose time lies within 1 s of a run-grid seam (k x 30 s, k >= 1) left out (its shifted copies too),
    printed beside, never replacing the primary.
11. **Profiles.** Per creator, the feature's bin values pooled over the creator's boundaries (sums of numerators and
    denominators), then the creator-balanced mean per bin; a bin is plotted only where 5 or more creators contribute.
    Profiles are drawn as real, S-mean with the shift band, and P.
12. **Privacy.** No per-creator or per-recording value is public. Creator counts follow the nested-count rule
    (`code/pubrules.py`, copied from r3-P01; registered groups plus 101, 71, 23, 18, 6, 36). No quantile of creator
    values is printed. Every public file carries the agnosticism sentence and "exploratory; not a test of H1-H10".

## Not run here

The voice detector's timeline (rv-D3 records no positional figure for it); acoustic features (a.2, audio ruling);
middle-model rows; a person's boundary sample (class c).
