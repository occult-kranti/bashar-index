# r3-P07: boundary anatomy from stored word times and text

Third-round programme, step 1 (class a.1, after r3-P01 and r3-P02). Written 2026-11-26 (UTC times from `date -u` in
`status.json`) by a step-1 agent (a model agent working for the lead; not a person). Exploratory; not a test of H1-H10.
Seen creators only; no model call, no download. Voice labels are model-coded (small model of record, rule B) and not
checked by a person; word times and text are recognizer output, not checked by a person. A description throughout:
no row is read A or B, none is a finding, and nothing here is worded as "induction" or "return".

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Question

What happens to time outside recognized speech, and to five text and recognizer features, in the minute around a
claimed-voice entry and exit: is there a step at the boundary or a ramp toward or away from it, beyond what
position-matched shifted sentence-unit boundaries show? Edited recordings apart from audience sessions.

## Prespecification and bases

- `prespec.md` (SHA-256 `703ec5ead596873469b5f42486b1d326caf4749784542c9af971963be79878db`), hashed at
  2026-11-26T06:26:35Z (`prespec-record.md`), before any feature value near a boundary was computed. Only outcome-free
  counts had been probed (`code/probe_p07.py`).
- 1,284 seen labelled recordings of 71 creators (word times from the paper review's seen-only cache; labels through the
  frozen seen-only path). A boundary is a change between a claimed-voice unit (V2 or V3, rule B) and any other unit
  (r3-P02's definition); about 950 entries and 830 exits in solo recordings and about 240 of each in audience sessions;
  boundaries with no shifted candidate (about 3%) are left out.
- **Panels:** the voice map's format (model-coded): solo (read as the programme's "edited recordings"; whether a
  recording was edited is not stored) and audience session. Solo: 55 creators (rows of other statistics: all but fewer
  than 5 of 55, or 50). Audience sessions: 13 creators.
- **Features**, in 2-s bins from -60 s to +60 s: F1 time outside recognized speech (primary; share of time not inside a
  recognized word); F2 recognized words per minute; F3 share of words with word probability below 0.5; F4, F5, F6 first-
  person singular, first-person plural and second-person forms per word.
- **Statistics:** step = (0, 10] s minus [-10, 0) s; ramp before = [-10, 0) minus [-60, -30); ramp after = (30, 60]
  minus (0, 10]. Shares as differences, rates as log ratios (0.5 added).
- **Reference S (printed estimate):** each boundary moved 200 times to a sentence-unit boundary of the same recording that
  is not a claimed-voice boundary, 20 s or more away and within a tenth of the recording (position-matched); estimate =
  creator mean of (real minus the mean over draws). **Reference P (placebo):** the same creator's own-voice-only
  recordings at the boundary's position, 50 draws (primary feature only). **Seam-zone exclusion row** (lead's decision 7).
- **Intervals:** 90%, r3-P30's `interval-choice.csv` by class (F1, F3 B_share_difference; F2 A_log_ratio; F4 to F6
  H_rare_counts) at the row's count; the t interval on creator means beside as a sensitivity column. Every row with an exact
  count names its method, which holds at that count; on rows whose count is banded the method is given as
  r3-P30's choice at the row's count and the t interval beside is not printed (the lead's step-1 decision 53). Margins (yardstick only): 5 points for shares, log 0.223 for rates.

## What it shows (described rows; `public/r3-P07-described-rows.csv`)

**Time outside recognized speech (F1), solo recordings, against shifted boundaries:**

| Boundary | Step | Ramp before | Ramp after |
|---|---|---|---|
| Entries | +2.2 points (90% -0.6 to 4.9): wholly inside the margin | not printed: the row's count is banded | -8.8 (-12.3 to -5.3): wholly beyond the margin, below |
| Exits | not printed: the row's count is banded | +8.4 (5.0 to 11.7): crosses | not printed: the row's count is banded |

In words: around claimed-voice entries and exits in solo recordings, more of the time lies outside recognized speech
than around sentence-unit boundaries 20 s or more away in the same part of the recording. The excess is local: it peaks
in the seconds next to the boundary (creator-balanced, about 42% of the 2-s bin just after an entry against about 25%
far from it; shifted boundaries peak at about 27%) and fades within about 15 s, more slowly on the side after the
boundary. So around entries the change between the 10 s next to the boundary and the half-minute further out is beyond
the margin after the boundary, and the step across the boundary itself lies inside the margin; some rows' descriptions
are not printed for privacy. The placebo
(own-voice-only recordings of the same creators, 47 creators for entries) and the seam-zone exclusion give the same
picture where printed (P: ramp after -11.4 points, -15.9 to -7.9; seam-excluded: -9.0, -12.7 to -5.4).

**Audience sessions (13 creators):** the same local excess around exits (ramp after -16.3 points, -22.4 to -9.0, wholly
beyond the margin, below; step +9.2, 4.9 to 14.7, crosses the margin); around entries every F1 row whose description is
printed is inside the margin or crosses it. Some rows' intervals and descriptions are not printed for privacy (the lead's
step-1 decision 56).

**Other features (S-centred):** recognized words per minute and low-probability words: every row whose description is
printed lies wholly inside the margin or crosses it. First-person singular forms: after an exit their rate steps up in
audience sessions (+0.68, 0.36 to 1.00: wholly beyond the margin, above), and in the half-minute after an entry they fall
below the first 10 s (solo -0.66, -0.82 to -0.50, wholly beyond, below).
In audience sessions, second-person forms are rarer in the 10 s before an entry than in the half-minute further out, more
so than at shifted boundaries (ramp before -0.50, -0.75 to -0.24: wholly beyond, below). Every other row whose
description is printed is inside the margin or crosses it; some rows' values are not printed for privacy.

**Passed from r3-P02 (lead's decisions 5 and 7), noted here:** pauses couple with punctuation less closely in the
claimed voice (a described fact), and claimed-voice boundaries sit near decoding seams less often than rotated labels;
both bear on F1 at boundaries, which sit where sentence units end and pauses are. The seam-zone exclusion row changes
no description.

Multiplicity: the register holds 56 primaries; if every true effect sat at half its margin, about 2.8 passes of the
floor rule would be expected at the deposited 5% (up to about 6.1 for the share classes, r3-P30). This entry is a
description and reads no primary.

## Figures

- `fig-r3-P07-profiles-solo` and `fig-r3-P07-profiles-audience`: small multiples per feature, entries and exits as
  columns; real boundaries, the shift band (5th to 95th percentile over 200 draws of the creator-balanced mean; not a
  quantile of creator values) and its mean, the placebo curve. Bins on fewer than 5 creators, or whose non-zero values
  come from 1 to 4 creators, are blank (the band of three audience-session features is blank for that reason).
- `fig-r3-P07-steps`: every statistic in margin units with its 90% interval, solo and audience panels, entries and exits.

## Files

| File | SHA-256 |
|---|---|
| `public/data-r3-P07-profiles.csv` | `ac9db409524aeec98dadc874e0c78e64b051ec6a9e94ec3eec31dcaa5b33d09d` |
| `public/fig-r3-P07-profiles-audience.pdf` | `f88324e98d55351bb14c5eed6b398fb5e83151e27e1058cd29952d9350093fda` |
| `public/fig-r3-P07-profiles-audience.png` | `fdc5b3dc31fb2269632e916be39801c1b91e950a54712ca5c1f6aee6109e9b7d` |
| `public/fig-r3-P07-profiles-solo.pdf` | `738bddf8263b2b467a4243b40490113ebfb789776fafa016179b4916061f8279` |
| `public/fig-r3-P07-profiles-solo.png` | `7c6f5e89cbeb5ec15049fdb7767b69fa18ec813b63c1bce3d9ab32712cedf6ec` |
| `public/fig-r3-P07-steps.pdf` | `48e37ab1e7cdda8fd77eacbf8372869ff80b7275c3bc51d25b43c041f0a31b73` |
| `public/fig-r3-P07-steps.png` | `5546b4ffa03878050399d733730d597f532325fcf19bb2726f8fa68bc4c30c5b` |
| `public/r3-P07-described-rows.csv` | `069858d1821c47633ed2ad1995dcc1ff0e77f789f67cf769e61073f7c1320ab0` |
| `code/finalize.py` | `f3711f285ef2310f56383d4aa121c8cd25157913ab3d85edde2ce1ef91e3d7fe` |
| `code/p07_plot.py` | `e183f42a4f6f66f622ed11656f1cde43889837469369943f53d2161d124384b3` |
| `code/p07_publish.py` | `45e225d49246fac9f859ed240a125a213ece94e4d6628294e6bfe316a538c00d` |
| `code/p07_run.py` | `cd228233d1e547d4945cdfd8c683fb91c183e85668452bf29bcfb2694ebc1f45` |
| `code/probe_p07.py` | `18947627780c1d421aff7ca2adc7bf6b2c9fbeaeab2bc4b61dd00e1d00f2b473` |
| `code/pubrules.py` | `241499756e6c5f3145e1cb077412e5be91281470f82b34a4cb965615b814255c` |
| `code/scan_ids.py` | `8e13207c018538e592903f635f90c4bdce058848f8d9292bef3a2945fcaae14c` |
| `code/style.py` | `ab28f40911b5dc6163f9140543633a1986395d756f809123756e44129717d7d5` |
| `code/scans/qscan_all2.py` | `78afbcf9dfe5bdc5d534f063598bb7cffb5c964bed782a54f43fac49e64d3846` |
| `code/scans/quant.py` | `a2478a09a37c3c759485fdfa3e0f98c6cd1d9a3094cc3b58c566588a9b1cae5c` |
| `code/scans/quant2.py` | `7421b55e42d6fd55880a4b44dbc42c89c5991f18ba652374a2a4e93865ce9248` |
| `code/scans/zsolve.py` | `14ef03d1fbe5d43d391cc763ddbb5cbb5382bef3c4194a698aa963d0f5bc277a` |
| `prespec.md` | `703ec5ead596873469b5f42486b1d326caf4749784542c9af971963be79878db` |
| `prespec-record.md` | `df9d4646d671c7f8a9fa094348bb2adba718e8f451629a6e0eaca67a9d096139` |
| `contacts.md` | `f2a44d6634a929cbfe3e3b3f130a4104bfe150d09ad9994d3cd93fe773148208` |

Private (not published): `private/` (per-creator and per-recording values, sums, run logs). Public data CSVs carry a commented header; PNGs at 200 dpi without text chunks; PDFs without document information.

**Privacy scans** (copies in `code/scans/`, `REL` set to this entry's `public/`): zsolve.py: 0 rows tested, 0 pinned, 0 narrowed; qscan_all2.py: 0 files with quantile columns, 0 rows with a hidden or banded base; identifier scan (creator codes, audio hashes, video ids): 0 hits; PNG text chunks and PDF document information: none. quant.py and quant2.py copied; they read the 'quantiles' column of one release file, and no public file of this entry has such a column, so they were not run on it.

## Departures and choices (stated)

1. "Edited recordings" are read as the voice map's format "solo": no stored field says whether a recording was edited.
2. The pooled all-formats row of the prespecification is not published: its creator set overlaps the solo panel's, and
   the same statistic over overlapping sets could let a difference be solved for a few creators (privacy).
3. Rows of one panel, boundary type and statistic share one creator base for all six features (privacy).
4. The dominance rule (non-zero values from 1 to 4 creators) is applied to the profile bins as well as the 5-creator
   floor.
5. No middle-model rows; the voice detector's timeline is not used (rv-D3 records no positional figure for it).

## Fields or bases not stored

Whether a recording was edited (no field); a voice-detector timeline per recording (not used); acoustic features
(a.2, audio ruling); a person's boundary sample (class c).

## Contacts

None (`contacts.md`).

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
