# r3-P37 / r4-P20: which calendar the forecast format keeps; two clocks (sky anchors against the weekday habit)

Third-round programme, step 3 (forecasts and time), class a.1. The programme pairs r4-P20 with r3-P37 ("r3-P37 /
r4-P20"; r4-P20 is carried by r3-P37), so r4-P20 sits in this folder. r4-P21's anchor-class half also lives here (the
four anchor classes); its typing half is in `../r3-P36/`. Written 2026-11-26 by a step-3 agent (a model agent working for
the project lead; not a person); times from `date -u`. Exploratory; not a test of H1-H10. It describes the calendar the
format keeps, never its origin.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Design

Prespecification: `prespec.md` (hashed 2026-11-26T14:11:40Z, before any outcome; `prespec-hash-record.md`); run record:
`run-record.md`.

- **Uploads.** Confirmed UTC upload days of the labelled seen recordings (TL-BUILD's stored table, built by TL-BUILD's
  loaders; estimated days have no weekday and are not used). No label enters the date-only rows.
- **Anchors** (`private/anchors.csv`, SHA-256 `2222c21be109e7c379d16b0ee2cd13114b724bdebfd3f6d28d276b3548904a6d`,
  hashed in the prespecification; `code/anchors.py`). Four classes from public calendars and published algorithms:
  - sky: new and full moons, solstices and equinoxes (Meeus 1998, *Astronomical Algorithms*, ch. 49 and 27), eclipses as
    a flagged subclass (ch. 54);
  - festival: Christmas Day, Western Easter Sunday (Meeus ch. 8), Imbolc, Beltane, Lughnasadh and Samhain at their
    conventional civil dates (Hutton 1996, *The Stations of the Sun*);
  - civil: the first day of every month (Gregorian calendar, ISO 8601);
  - numerological: dates whose day equals the month (1/1 to 12/12).
  A spot check of 38 published dates (eclipses from NASA's canons, Espenak and Meeus 2006 and 2009; seasons; phases;
  Easter) passed before the table was written. et's announced-period class has no public date and is not computed.
- **Anchored by date alone:** some anchor of the class lies at offset 0 or +1 (upload day minus anchor day; den-soc's
  ritual window); rows at -1 to +1 and -7 to -1. **Habit:** the most used UTC weekday(s) of the creator's other uploads
  (leave-one-out). **Added / shifted:** for an off-habit upload, whether the habit-day date within three days carries
  another upload of the creator.
- **Tier S** (20 or more of the 23 non-development creators eligible: 10 or more confirmed upload days; printed "all but
  fewer than 5 of 23"). The exploration side (half A and the tuning pool) ran first and was hashed; the sealed half B ran
  once after a code-hash check. Readings come from the sealed half only.
- **Primary (N19):** per creator, off-habit share of sky-or-festival anchored uploads minus that of the creator's other
  uploads (creators with 2 or more anchored and 1 or more other uploads); E1 the creator mean; E2 the creator mean minus
  each creator's mean over 999 habit-preserving shuffles (all of a creator's days moved by the same whole number of weeks).
  Margin 5 points; named direction positive; 90% t intervals fixed in advance (interval class not calibrated by r3-P30).

## Results

**Off-habit contrast** (`public/data-r3-P37-offhabit.csv`, `public/fig-r3-P37-offhabit.png`), sealed half B:

| Row | Creators | E1 (90% interval) | E2 (90% interval) | Reading |
|---|---|---|---|---|
| **Primary:** sky or festival, 0 to +1 | 5 to 9 | 0.086 (-0.068 to 0.240) | 0.097 (-0.069 to 0.263) | **undetermined** |
| Sky alone | not computed or not printed | | | not computed or not printed |
| Tolerance, -1 to +1 | not computed or not printed | | | not computed or not printed |
| Lead window, -7 to -1 | not computed or not printed | | | not computed or not printed |
| Off-habit and shifted | 5 to 9 | 0.055 (-0.183 to 0.294) | E1 only | undetermined (row) |
| Off-habit and added | 5 to 9 | 0.032 (-0.166 to 0.229) | E1 only | undetermined (row) |
| Festival, civil, numerological, eclipse days, strong weekday habit | not computed or not printed | | | not computed or not printed |

In words: on the sealed half, whether uploads made on or the day after a sky or festival date leave the creator's
weekday habit more often than its other uploads is **undetermined**: the intervals run from a few points below zero to
well beyond the margin on the positive side, and they sit inside the shuffle band. Neither clock is shown to win. The
exploration side (described, not read; 40 to 49 creators in the primary) gives -0.028 (-0.097 to 0.042), inside its shuffle
band; there, the added share is lower on anchored days (-0.077, -0.139 to -0.015) and the shifted share higher (0.052,
-0.006 to 0.110), as descriptions only.

**Offsets** (`public/data-r3-P37-offsets.csv`, `public/fig-r3-P37-offsets.png`): the creator-balanced share of uploads in
the ritual window, in the week before and in the days after sky-or-festival anchors lies inside the habit-preserving
shuffle band on both sides; uploads fall near these dates about as often as the creators' weekly rhythms alone give
(described; date-only anchors make nearness a matter of alignment, which the band measures). By class, the numerological
class's lead window lies above the band on both sides and its after-window below it on the sealed half; the other class
windows lie inside (described, never read).

**Word-anchored uploads** (tier L; the frozen rule coder's event-anchor pattern on the ledger's statements): fewer than
5 creators: not computed.

**Predictions scored:** none deposited for the seen run (deposit 2's cells for r3-P37 and r4-P20 are silent; the
platform-format rider is for later uploads). Members' opposed expectations in the round memos (css: anchored uploads keep
the habit; occult and den-soc: they leave it) were not deposited and are not scored; the reading decides between neither.

**Not computed or not printed:** on the sealed half, the sky-alone, festival, civil, numerological, eclipse, one-day
tolerance, lead-window and strong-habit rows; on the exploration side, the sky-alone, eclipse and one-day tolerance rows; the word-anchored row; et's announced-period class.

Multiplicity: 56 primaries; about 2.8 readings A would be expected by chance if every true effect sat at half its margin.

## Limitations

UTC days blur the local weekday (META-1's caveat; the -1 to +1 row helps). Seen recordings are each creator's newest
labelled uploads, so a missing recording can make an off-habit upload look shifted. The sealed half has few creators with
two or more anchored uploads.

## Departures

- Offsets on the sealed half are printed by window (lead, ritual, after), not by day: decided before its offsets were
  read, because daily bins on the sealed half could rest on fewer than 5. Daily offsets are printed for the exploration
  side only, and only the sky-or-festival class is drawn by day; the other classes are printed by window. (The
  prespecification asked for daily offsets for each class on both sides.)
- Blank E2 or band cells are written out ("not computed", "E1 only") rather than left empty.
- The word-anchored class uses the frozen rule coder's event-anchor pattern, because no list was assigned for it
  (deposit 3's list README). Stated in the prespecification.

## For the lead (settled)

- **Settled** (the lead's decisions 83 and 85): the tier stays S as run (for later entries, a date or anchor table
  written blind from public sources and hashed before any count counts as tier L); the word-anchored row's use of the
  frozen rule coder's event-anchor pattern is accepted as a stated departure.
- Tier S puts the reading on the sealed half (12 creators) although no rule here is tuned to data: the anchor table is
  written blind from public calendars, like a tier-L list. Whether blind date tables should be tier L (all 23
  non-development creators) is the lead's decision.
- A word-anchored list for r3-P37 was never assigned.

## Changes at the joint staging of steps 3 to 5 (2026-11-26T14:59:32Z, UTC from `date -u`)

- **Tier counts (the lead's decision 78).** `public/data-r3-P37-counts.csv` no longer prints the eligible counts
  of the sealed half and of the exploration side: "not printed (privacy rule)"; the tier letter (S) and the
  non-development count ("all but fewer than 5 of 23") print as before. Edited by hand with a dated comment line
  (the publication script was not rerun). No number changed.
- **Tier S stays as run (the lead's decision 83)**; a blind date table written before any count counts as tier L for
  later entries. The word-anchored row's use of the frozen rule coder's event-anchor pattern is accepted as a
  stated departure (decision 85).

## Files

`prespec.md`, `prespec-hash-record.md`, `run-record.md`, `code/anchors.py`, `code/p37_run.py`, `code/p37_publish.py`,
shared code in `../ft-common/code/`, `public/` (three CSV files, two figures as PNG and PDF), `contacts.md`, `status.json`
(hashes). `private/` holds both stage files with per-creator values (never published) and the anchor table, which holds public calendar dates only and could be published as is (its header predates the label lines, because it was hashed first).

## Change by the lead's decision 92 (2026-11-26T15:25:06Z, UTC from `date -u`)

- Some cells were changed (privacy rule); the CSV and the off-habit figure were
  changed (redrawn by this entry's own plot function). No number changed.

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- A count form among the sealed rows was changed (privacy rule), and the description of the sealed half's daily bins
  is worded generally. The CSVs, the off-habit figure (redrawn by this entry's own plot function) and this
  README were changed. No number changed.

## Change by the lead's decision 103 (2026-11-26T17:16:20Z, UTC from `date -u`)

- Some rows read "not computed or not printed"; count forms are made uniform. The off-habit CSV, its figure (redrawn by this entry's own plot function, which now
  names withheld rows) and this README were changed; the settled notes to the lead are marked. No number changed.

## Change by the lead's decision 104 (2026-11-26T17:33:22Z, UTC from `date -u`)

- Rows not computed and rows not printed carry one label ("not computed or not printed") in their count, method and status
  cells and are listed together; change notes are worded in general terms. The CSV, the figure (redrawn by this
  entry's own plot function) and this README were changed. No number changed.
