# r3-P65: survivorship and attrition (the gap bound)

Third-round panel programme, step 4 (class a.1 for the gap bound). Run on 2026-11-26 (UTC, from `date -u`) by the step-4
agent, a model agent working for the project lead (not a person). Prespecification `prespec.md` with
`../common/prespec-shared.md`, hashed 14:07:09Z before any gap length was read (`prespec-hash-record.md`).

**Exploratory; not a test of H1-H10.** Deletions and the regular-upload tab bound every audience and economy reading: those
readings describe a platform-surviving roster's newest regular uploads. Listing metadata only; no channel or video id is
printed. The metadata-only snapshots and the regular, live and short shares by audience band are class b (r3-P72).

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Tier and units

- **Tier S.** Every non-development creator is eligible (2 or more adjacent listing ranks with confirmed upload days; the
  band is "20 or more"). Nothing is tuned: the posting model is fitted per creator by a fixed rule. The reading is made
  once on the **sealed half B** (12 creators). The exploration side (half A with the tuning pool, 59 creators; its
  eligible count is not printed, a privacy rule) is described only.
- Data: each seen creator's newest-20 regular uploads (the selection quota), confirmed upload days (version B); gaps between
  adjacent ranks whose days are both confirmed; same-day uploads collapsed.
- **Weekday-habit posting model:** for each creator, the chance of an upload on each weekday from the creator's own days.
  **Excess long gaps:** gaps above the model's 95th percentile, minus the number the model expects; an upper bound that
  includes breaks. **Gap bound:** the uploads the model expects inside those long gaps, as a share of the window. Band: the
  central 90% over 1,000 replicate data sets drawn from each creator's model (a fixed method).

## Results in words

- **Sealed half B (the reading): no excess over the posting model.** The mean excess is 0.02 long gaps per creator (the
  model's 90% band -0.31 to 0.36). The mean gap bound is 0.08 of the window (band 0.04 to 0.13): at most about one upload in
  twelve of a creator's newest window could be missing (deleted, made private, or a break), and the model alone expects as
  much.
- **Exploration side (described, no reading):** mean excess 0.09 (band -0.16 to 0.18), inside the model's band; mean gap
  bound 0.11, above the model's band (0.06 to 0.10): on the exploration side long gaps hold a little more room for missing
  uploads than each creator's own posting habit predicts. Breaks and deletions are not told apart.
- **Histogram (the programme's plot):** with step 2's bin rule (5 or more creators per bin), the sealed half's 12 creators
  fall in one merged bin, so the histogram carries no shape; the figure shows the two means against the model's bands.
- **Stated facts:** across the 101 channels, 103 new regular uploads appeared between the corpus crawl of 19 November and
  25 November (the newest-20 window keeps moving); a few videos of the earlier listing windows were no longer shown on 25
  November (removed, made private or pushed out of the window) on fewer than 5 channels (counts-only scan summary). The
  release's rv-D1 records 30 final download failures among the 1,976 selected recordings, and that recordings never listed
  (live streams, short videos, members-only material, other platforms, deleted uploads) are outside the quota.
- **Regular-upload tab (ruling 6):** stored. TABLE's whitelisted channel catalogue of 2026-11-17 holds per-tab counts of
  regular, short and live items for catalogued creators. The programme placed the regular, live and short shares by
  audience band in class b; they are not computed here (see "For the lead").

No account prediction was deposited for r3-P65; none is scored. Multiplicity (deposit 2): 56 primaries; about 2.8 readings
beyond a margin expected by chance at half-margin effects. A reading is never called a finding.

## Rows not computed

The histogram's shape (one merged bin under the 5-creator rule); the regular, live and short shares by audience band
(class b, as the programme places them).

## Files

| File | What |
|---|---|
| `public/data-r3-P65-gaps.csv` | sealed and exploration rows, the merged histogram bin, stated facts |
| `public/fig-r3-P65-gaps.png`, `.pdf` | mean excess long gaps and mean gap bound against the model's bands |
| `prespec.md`, `prespec-hash-record.md` | prespecification and its hash |
| `code/p65.py`, `code/publish_p65.py` | analysis and publication (shared code in `../common/`) |
| `contacts.md`, `status.json` | reads (no contact); status with every file's SHA-256 |

## Privacy

The sealed half prints as 12 (deposit 2's set); the exploration side's eligible count is not printed (privacy rule;
59 = half A's 11 and the tuning pool's 48). Means and bands only on the exploration side (no histogram); no overall mean is printed, so no
group size follows from the means. The scan's removals are printed only as "fewer than 5 channels". Checks: see
`../common/privacy-checks.md`.

## Departures

1. **Eligibility threshold** changed before any gap length was read, for privacy only (prespec-shared 0.3): first written 10
   or more adjacent confirmed pairs, then 2 or more, so that every count prints exactly.
2. **Seen creators only**, as the brief binds; round 3's proposal read the gaps of all 101 creators.
3. The figure shows means against bands instead of a histogram, because the prespecified histogram collapses to one bin.

## For the lead (settled)

- **Settled** (the lead's decision 76): the tab shares by audience band move from class b to a.1, because the tab
  counts are stored; they run in a later batch.
- The regular, live and short tab counts are **stored** (TABLE's catalogue of 2026-11-17, catalogued creators only). The
  programme assumed they need r3-P72's snapshots. Whether the shares by audience band move from class b to a.1 is the
  lead's ruling; nothing was computed from them here.

## Changes at the joint staging of steps 3 to 5 (2026-11-26T14:59:32Z, UTC from `date -u`)

- **Tier counts (the lead's decision 78).** The exploration side's eligible count is not printed (privacy rule)
  in `public/data-r3-P65-gaps.csv` (two described rows) and above; the sealed half prints as 12 (deposit 2's set,
  every creator of it eligible). The CSV was edited by hand with a dated comment line (the publication script was
  not rerun). No number changed.
- **Tab shares by audience band** move from class b to a.1 (the tab counts are stored) and run in a later batch
  (the lead's decision 76).

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- The merged histogram bin's creator count moves from the band columns to the value column of
  `public/data-r3-P65-gaps.csv`. No number changed.

## Change by the lead's decision 103 (2026-11-26T17:16:20Z, UTC from `date -u`)

- The note to the lead is marked as settled. No number changed.
