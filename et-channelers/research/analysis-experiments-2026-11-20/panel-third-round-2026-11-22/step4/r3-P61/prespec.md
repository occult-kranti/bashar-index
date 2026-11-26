# r3-P61: persuasion and monetisation devices, with a priced-or-unpriced rule (pilot; prespecification)

Written 2026-11-26 (UTC, from `date -u`; the hash time is in `prespec-hash-record.md`) by the step-4 agent, a model agent
working for the project lead (not a person), before any count of this entry beyond r3-P42's public files was made.
Shared rules: `../common/prespec-shared.md`.

Exploratory; class a.2 (ruling 11), a pilot, then an instrument for the comparison set only. **Tier L**: run once on the
23 non-development seen creators, with no split. Without a business-matched stratum the device counts have **no reading
of their own**: every row is a description. Devices with devotional twins are coded priced or unpriced. Cue counts:
sense not resolved, precision unknown. Full coding (15 to 30 USD) and reliability (40 to 60 coder-hours) are class c.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 1. Inputs

- Deposit 3's L14 (binding `addendum-2b/lists/r3-P61-persuasion-devices-a2b.csv`): device families with commercial (-C)
  and devotional (-D) forms apart, and PRICE, which defines "priced" (G8: a device hit is priced when a PRICE hit sits in
  the same label unit).
- Step 2's re-matched hits (`step2/r3-P48/private/desc-extract.private.pkl`: every L14 hit of r3-P42's extract with its
  recording, unit, voice side) and the extract's unit tokens and unit durations; r3-P42's counts for the thin statuses
  and priced shares. Totals are checked against r3-P42's counts (a difference stops the run).

## 2. Rows

- **Status of each class** by the thin rule (addendum 2d), recomputed and checked against r3-P42's.
- **Position heat map** (programme): for each computed class, the creator-balanced rate per 10,000 tokens in each tenth
  of running time (a unit's tenth by its midpoint time over the recording's summed unit durations; by unit index where
  durations are missing, stated), over the 23 creators. A cell prints only where 5 or more creators carry a hit in it.
  Coarsening ladder, fixed now: if every tenth of a row has 5 or more carrying creators the row prints by tenths; else by
  fifths; else by halves; else the row prints "not computed (too few terms or creators)". Commercial and devotional
  forms side by side; thin classes print their status.
- **Priced or unpriced.** For each class with 5 or more creators carrying hits: the creator-balanced share of its hits
  that are priced (r3-P42's statistic, recomputed and checked).
- No voice contrast here (r3-P42 printed them; they sit inside their placebo bands or fail as structure); no reading.

## 3. Plot

A heat map of device by tenth of running time (cells of 5 or more creators), commercial and devotional forms side by side,
with the priced share beside each computed row. No per-creator point.
