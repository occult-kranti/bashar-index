# Prespecification: r3-P37 (which calendar the forecast format keeps), carrying r4-P20 (two clocks: sky anchors against the weekday habit)

Written 2026-11-26 between 14:09:41 and 14:11:29 UTC (both from `date -u`; the second is the first hashing; corrected and hashed again below) by a step-3 agent (a model agent working for the project lead; not a
person), before any outcome of this entry was computed. Its SHA-256 and the time of hashing are in
`prespec-hash-record.md`. Exploratory; not a test of H1-H10. No model or API call, no download.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Programme.** `programme.md` 2.1 step 3, r3-P37 / r4-P20 (a.1); `programme-decisions.json` (r4-P20 carried by r3-P37,
N19); deposit 2's margins and readings, split policy and account cells; the lead's common rules for steps 3 to 5. The
programme pairs r4-P20 with r3-P37, so r4-P20 sits in this folder. It describes the calendar the format keeps, never its
origin.

## 0. What was seen before this file

- Published: the release's META ("a typical channel uploads about once a week and many favour one weekday", all 101
  creators), SD and DC as css's round-4 memo summarises them, TL-7.7, TL-7.1, E12, TIME and RX's headlines; step 1 (r3-P30's
  interval table); deposits 1 to 4; the round memos of css, den-soc, occult, et, emic, stat and the attackers on this
  entry.
- Outcome-free counts computed for this prespecification (`../ft-common/code/eligibility.py`, SHA-256
  `d31d2f48...3763c`; output private): the number of confirmed upload days per creator, the first and last upload day
  of the seen recordings, and creator counts by split role. No upload day was read against any anchor, and no weekday
  was computed.
- The anchor table (section 2) was built and spot-checked before this file, from public calendars only.

## 1. Data and tier

- **Uploads.** The labelled seen recordings in TL-BUILD's stored recording table (`TL/private/timeline-rows.private.json`,
  key `recordings`; TL-BUILD's loaders: TABLE's confirmed day of version B, or the midpoint of the upload period). Only
  confirmed upload days (panel B) are used: an estimated midpoint has no weekday. Days are UTC days (META-1's caveat).
- **Eligible creators** (outcome-free): 10 or more labelled seen recordings with a confirmed upload day (META's own floor
  for weekday concentration, "creators with 10+ stamps"). Among the 23 non-development creators the eligible count is
  "20 or more" (printed as "all but fewer than 5 of 23").
- **Tier S** (deposit 2's split policy; 20 or more eligible non-development creators). The date-only rows are read once
  on the **sealed half B**. The **exploration side** (half A and the tuning pool T) is computed first, written and
  hashed, and printed as described rows, never as readings. No choice is tuned between the two stages: the code and this
  file are fixed before the exploration stage, and the sealed stage refuses to run if any code hash changed.
- **Tier L** for the word-anchored row only (section 5): it applies the ledger's frozen rule coder, so it runs once on the
  23 non-development creators, with no split.

## 2. The anchor table (hashed here)

`private/anchors.csv`, SHA-256 `2222c21be109e7c379d16b0ee2cd13114b724bdebfd3f6d28d276b3548904a6d`, written by
`code/anchors.py` (SHA-256 `2291de35e208f94f460451dfb396ab85def8772112a3de24fbaab0a2319df199`) from public calendars and
published algorithms; 1,263 rows from 2007-07-01 to 2027-06-30 (the seen upload range plus 26 weeks each side).

| Class | Anchors | Source |
|---|---|---|
| sky | new and full moons; March and September equinoxes; June and December solstices (UTC day of the instant); eclipses as a flagged subclass | Meeus (1998) *Astronomical Algorithms*, 2nd ed., ch. 49, 27 and 54; delta-T 69 s |
| festival | Christmas Day; Western Easter Sunday; Imbolc 1 Feb, Beltane 1 May, Lughnasadh 1 Aug, Samhain 31 Oct | Gregorian calendar; Meeus (1998) ch. 8; Hutton (1996) *The Stations of the Sun* |
| civil | the first day of every month | Gregorian civil calendar (ISO 8601) |
| numerological | dates whose day number equals the month number (1/1 to 12/12) | Gregorian civil calendar; et's "repeated-digit civil dates" |

The four classes are den-soc's round-4 statement of et's four classes (civil period, sky event, festival, numerological
civil date). et's original fourth class, periods a group or creator announces, has no public date and is not computed
("not definable by date alone"). Spot check: 38 published dates (NASA eclipse canons, Espenak and Meeus 2006 and 2009;
almanac season and phase dates; four Easter dates) are reproduced, and every eclipse day is a syzygy day.

## 3. Definitions

- **Offset** of an upload to a class: upload day minus the day of the nearest anchor of that class (smallest absolute
  difference; a tie goes to the positive offset).
- **Anchored (date only).** An upload is anchored to a class in window W when some anchor of the class lies at an offset
  in W. Primary window W0 = {0, +1} (den-soc's ritual window, hashed in round 3). Rows: W1 = {-1, 0, +1} (css's
  one-day tolerance for UTC days); WL = {-7, ..., -1} (den-soc's lead window).
- **Primary class:** sky or festival (N19: "uploads anchored by date alone to sky or festival events"). Rows: sky, festival,
  civil, numerological and the eclipse subclass, each alone, in W0.
- **Weekday habit** (leave-one-out, so anchored and other uploads are treated alike): for each upload, the weekday or
  weekdays that hold the most of the creator's *other* confirmed uploads. The upload is **off-habit** when its UTC weekday
  is not among them.
- **Added and shifted** (attack-stat's split). For an off-habit upload, look at the dates within three days either side
  that fall on a habit weekday. If the creator has another confirmed upload on any of them, the upload is **added**; if
  not, and every such date lies inside the creator's seen span (first to last confirmed upload), it is **shifted**; else
  **edge** (counted in neither). Missing seen recordings (not labelled) can make an upload look shifted; this is printed.
- **Contrast-eligible creator** in a row: an eligible creator with 2 or more anchored and 1 or more other uploads
  (css and den-meth: "two or more anchored uploads").

## 4. Primary, rows, intervals and readings

- **Primary (r4-P20 / N19):** on the sealed half B, the creator mean of d_c = off-habit share of anchored uploads minus
  off-habit share of the creator's other uploads (sky or festival, W0).
- **Reference (admissible):** habit-preserving date shuffles: each creator's upload days are moved together by 7k days,
  k drawn uniformly from -26..-1 and 1..26 (weekdays, spacing and counts kept; SD's reference kind), 999 draws, a
  separate k per creator. For each creator, s_c is the mean of d_c over the draws in which the creator is
  contrast-eligible (s_c is left undefined, and the creator out of E2, if fewer than 100 draws qualify). **E1** = creator
  mean of d_c; **E2** (reference-adjusted) = creator mean of d_c - s_c. The shuffle band of E1 (5th to 95th percentile of
  the creator mean of d_c over draws) is printed beside it.
- **Margin:** deposit 2's difference in shares, 5 points (0.05). **Named direction:** positive (anchored uploads off the
  habit more often).
- **Interval:** 90% t interval on creator values, a fixed method. No r3-P30 design class has uploads as units with two or
  a few anchored uploads per creator (B1 simulates many sentence units per class), so every interval here is flagged
  "interval class not calibrated by r3-P30". A fixed method is not withheld under a banded count (decision 62).
- **Readings** (deposit 2): **A** if the intervals of E1 and E2 lie wholly above +0.05; **B** if both lie wholly inside
  -0.05 to +0.05; "beyond the margin, opposite to the named direction" if both lie wholly below -0.05 (decision 2);
  otherwise **undetermined**; **not computed** with fewer than 5 contrast-eligible creators.
- **Rows** (sealed half; the same rows on the exploration side, described): each class alone in W0; the primary class in
  W1 and in WL; off-habit split into shifted and added (d for each kind, with E1's interval); creators whose most used
  weekday holds half or more of their confirmed uploads (META's "half or more on one day"; computed from all their
  uploads, not from anchors).
- **Offsets:** for each class, the creator-balanced share of uploads at each offset from -7 to +7 (each eligible
  creator's uploads, every upload counted, equal weight per creator), with the pointwise 5th to 95th percentile band of
  the same shares under the shuffles; the creator-balanced shares in W0 (ritual window) and WL (lead) are printed against
  their shuffle bands as "above the band", "inside the band" or "below the band" (den-soc's table, described). It is
  printed beside, never read as a reading: date-only anchors make "near the event" a matter of chance alignment, which
  the shuffle band measures.

## 5. The word-anchored row (secondary; description only; tier L)

Uploads anchored by naming are near the event by construction (programme; attack-den-meth). Deposit 3's list README says
the word-anchored class "would need a list the lead may assign"; none has been assigned. This entry uses the closed,
already hashed event-anchor pattern of the ledger's frozen rule coder (`EVENT_ANCHOR`, deposit 2), applied to the frozen
ledger's statements of each recording (world-future statements only, not titles), with its nouns sorted into the four
classes before any count: sky (solstice, equinox, eclipse, full/new/blood/super/harvest/blue moon, supermoon); festival
(Christmas, Easter, Halloween); numerological (11:11, 12:12, eleven eleven, twelve twelve, Lion's Gate); civil
(New Year's). Other nouns of the pattern (portals, gateways, elections, summits and the like, and festivals without a
date in the table) are not used. A recording is word-anchored to a class if one of its statements matches. Printed: the
creator-balanced offsets of word-anchored uploads to the nearest anchor of the named class, on the 23 non-development
creators, if 5 or more of them have a word-anchored upload with a confirmed day; otherwise "not computed (fewer than 5
creators)". The statement text is never written.

## 6. Privacy and counts

The step-1 and step-2 rules and the lead's common rules: no cell, bin, bar or plotted group on fewer than 5 creators; no
per-creator rows or points; counts checked against each other, the release, steps 1 and 2, deposits 2 to 4 and the
fixed counts, nested groups 1 to 4 apart stated against each other or banded (step 1's `pubrules.Register`, copied
with its hash); no quantile of creator values over a banded count; no per-creator distributions where a count is banded
(the off-habit shares are printed as creator means with intervals; the programme's "distributions of the off-habit share"
are drawn only where the count is exact); privacy notes in general words. Solvers of the brief run before the report.

## 7. Predictions scored

Deposit 2's account cells for r3-P37 and r4-P20 are all silent for this seen run (the platform-format rider applies to
later uploads, class b). Nothing is scored. Members' round memos state opposed expectations (css: sky-anchored uploads
keep the habit; occult and den-soc: they leave it); they were not deposited as cells and are not scored.

## 8. Plots

`fig-r3-P37-offsets`: creator-balanced shares of upload day minus nearest sky-or-festival anchor (-7 to +7) with the
shuffle band, exploration side and sealed half, and the word-anchored panel or its "not computed" note.
`fig-r3-P37-offhabit`: E1 and E2 with 90% intervals by row against the margin band, sealed half (readings) beside the
exploration side (described), with the off-habit shares of anchored and other uploads as creator means.

## 9. Seeds and multiplicity

Seed of a draw stream: the first 8 hex digits of SHA-256("r3-P37|<stream>|step-3") read as an integer, with
`numpy.random.default_rng([seed, k])`; streams "shuffle-exploration" and "shuffle-sealed". 56 primaries in the programme;
deposit 2's half-effect disclosure (about 2.8 readings A expected by chance) is printed. A reading A is never called a
finding.
