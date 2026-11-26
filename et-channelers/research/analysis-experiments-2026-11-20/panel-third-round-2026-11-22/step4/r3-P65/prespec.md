# r3-P65: survivorship and attrition (prespecification)

Written 2026-11-26 (UTC, from `date -u`; the hash time is in `prespec-hash-record.md`) by the step-4 agent, a model agent
working for the project lead (not a person), before any gap length of this entry was read. Shared rules:
`../common/prespec-shared.md`.

Exploratory; a gap bound now. Deletions and the regular-upload tab bound every audience and economy reading: they were
built "in this platform-surviving roster". The metadata-only snapshots and the regular, live and short shares by audience
band are class b (r3-P72's request). No channel or video id is printed.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Data and tier

- **Upload days.** Each seen creator's newest-20 regular uploads (the selection quota) from TABLE's seen rows: listing
  rank and the confirmed upload day under version B (E1 or E2). Recordings whose day is only an interval (E3) break
  adjacency: a gap is read only between adjacent listing ranks whose days are both confirmed. Same-day uploads collapse
  into one upload day (a gap of 0 days is not a gap).
- **Eligible creators** (outcome-free): 2 or more adjacent confirmed pairs (the privacy amendment of prespec-shared 0.3,
  made before any gap length was read; first written: 10 or more). Every non-development creator is eligible: **tier S**.
- **Roles.** Nothing is tuned: the posting model is fitted per creator by the fixed rule below. The reading is made once
  on the **sealed half B** (12 creators). The exploration side (half A with the tuning pool: its eligible creators,
  printed in the form `Counts` gives) is described by means and bands only, with no reading and no histogram.

## 2. The posting model and the gap bound

- **Weekday-habit posting model** (round 3: "each creator's weekday-habit posting model"): per creator, each calendar day
  of weekday w carries an upload with probability p_w = (the creator's confirmed upload days on weekday w) / (the number
  of weekday-w days from the creator's first to last confirmed day). Gaps under the model are simulated (100,000 draws
  per creator: a start weekday drawn from the creator's own upload-day weekdays, then days stepped until the next upload;
  gaps capped at 3,650 days), giving the model's 95th percentile gap q95 and the model's exceedance probability
  e = P(gap > q95).
- **Excess long gaps.** Per creator: k = the observed gaps longer than q95; expected = e x (the creator's gap count);
  excess = k - expected. "An upper bound that includes breaks": a long gap is a deletion, a private upload, a break or a
  change of habit, and no reading tells them apart.
- **The gap bound.** Per creator, the uploads the model expects inside its long gaps beyond one: m = the sum over long
  gaps of max(0, floor(sum of p_w over the gap's interior days)), and the bound share m / (the creator's confirmed upload
  days + m): at most this share of the window could be missing uploads, breaks included.
- **The model's band.** 1,000 replicate data sets: each creator's gaps redrawn from its own model (as many gaps as
  observed), the same statistics recomputed (with the creator's q95 and e kept); central 90%.
- **Primary (sealed half B):** the creator-balanced mean excess long gaps against the model's band: "excess over the
  posting model" (above), "no excess over the posting model" (inside), "below the posting model" (below). No direction
  is deposited and no design class of r3-P30 applies (a fixed-method band). The creator-balanced mean gap bound share is
  printed beside it (described).
- **Histogram** (programme's plot): over the sealed half's creators, excess long gaps in bins formed by step 2's rule
  (fixed edges of width 0.5 over -1.0 to 3.0, tails merged inward to 5 or more creators), with the model's band per bin
  (central 90% of the replicate bin counts).
- **Exploration side (described):** the same two means with the model's band.

## 3. Other bounds (stated facts, no reading)

- **Listing scans.** From the new-uploads scan's counts-only `summary.json` (all 101 channels, no group split): new
  uploads since the corpus crawl and since 21 November, and videos of the earlier windows no longer shown (removed, made
  private or pushed out of the window) on fewer than 5 channels: printed only in that form.
- **rv-D1** (release, public): 30 final download failures; recordings never listed (live streams, short videos,
  members-only material, other platforms, deleted uploads) are outside the quota.
- **Regular-upload tab:** whether the tab counts of shorts and live streams are stored is looked up (ruling 6) and
  recorded as "stored" (with the file kind) or "not stored"; the shares by audience band stay class b.

## 4. Plot

A histogram of excess long gaps per creator (sealed half) against the posting model's band, with the means of both sides
in the caption. No per-creator point.
