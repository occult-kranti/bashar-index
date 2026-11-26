# r3-P60: where audiences are sent off the platform, and suppression talk

Third-round panel programme, step 4 (class a.2, ruling 11), tier L. Run on 2026-11-26 (UTC, from `date -u`) by the step-4
agent, a model agent working for the project lead (not a person). Prespecification `prespec.md` with
`../common/prespec-shared.md`, hashed 14:07:09Z (`prespec-hash-record.md`).

**Exploratory; not a test of H1-H10.** Deposit 3's L13 (addendum 2b): destination classes by link domain, including the
messaging-app broadcast class, own-site (residual), platform and shortener classes; suppression talk split into platform
moderation talk and hidden-actor suppression talk ("censored" flagged, never counted). Links are read as settings: **a link
is a link, not a verdict** (never allegiance, never routing). Cue counts: sense not resolved, precision unknown; precision
reads are class c.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Tier and units

Tier L: the 23 non-development seen creators, once, no split. Page links: web addresses in the descriptions of their seen
recordings, matched by host (rule G1c; no link followed), counted by r3-P42 with the shared matcher
(`step2/common/lexmatch.py`); every one of the 23 has page links. Speech: r3-P42's form counts of L13's suppression terms.

## Results in words

- **Destinations (creators of the 23 with one or more links of the class):** links to domains on no destination list (the
  own-site residual) are set by all but fewer than 5 of the 23; platform self-links and other social platforms by 10 to 19
  each; membership and donation pages by 6 (0.26 of the 23); booking and course platforms by 5 to 9. Alternative video
  platforms, podcast platforms, newsletters, link aggregators, the messaging-app broadcast class, merchandise and link
  shorteners are each set by fewer than 5 creators. Shares of links (r3-P42's statistic, recomputed and equal to its printed
  values): own-site residual 0.64, platform self-links 0.13, other social 0.09, membership and donation 0.06, booking and
  courses 0.03.
- **Funnel depth:** 10 to 19 creators have a link at depth 3 or 4 (payment, or one-to-one service or paid teaching), 5 to 9
  at depth 4. Shares of links by depth: depth 0 0.13, depth 4 0.03; depths 1, 2, 3 and "undetermined" are not
  printed (values that could narrow a withheld value are not printed). Unresolved (shortener) links stay under 0.20 of a
  creator's links, so depth is readable (r3-P42's rule).
- **Suppression talk, split: both halves "not computed (too few terms or creators)"** by the thin rule (fewer than 3 forms of
  each half used by 5 or more of the 23 creators), as r3-P42 found. The halves are not pooled.
- **The paired-difference dot plot** (recordings with platform-suppression talk against others): not computed; it rests on
  the platform half. **Alternative video platforms against control vocabulary:** not computed (fewer than 5 creators link
  to them).

No account prediction was deposited for r3-P60; none is scored. No reading is made: destinations are described as
settings.

## Rows not computed

Both suppression halves; the paired-difference dot plot; the alternative-platform contrast; creator shares of the seven
classes set by fewer than 5 creators.

## Files

| File | What |
|---|---|
| `public/data-r3-P60-rows.csv` | destination classes (creators, shares), funnel depth, suppression statuses, plot statuses |
| `public/fig-r3-P60-destinations.png`, `.pdf` | creators by destination class (exact or banded) and link shares by depth |
| `prespec.md`, `prespec-hash-record.md` | prespecification and its hash |
| `code/p60.py`, `code/plot_p60.py` | analysis (with the consistency check against r3-P42) and figure |
| `contacts.md`, `status.json` | reads (no contact); status with every file's SHA-256 |

## Privacy

Counts in the step's register forms; a share of the 23 only where the count is exact. A depth's share of links prints
only where every class at that depth is printed (as in step 2's r3-P42 file). Checks: `../common/privacy-checks.md`.

## Departures

None from the prespecification. The withheld depth shares follow the shared privacy rules (prespec-shared 0.3).

## For the lead (settled)

- **Settled** (the lead's decisions 75 and 86). Step 2's r3-P42 file, as published, does not print the link shares at
  funnel depths 1, 2, 3 and "undetermined": a depth's share prints only where every class at that depth is printed.
  This entry follows the same rule (the lead's decision 99).

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- The share of page links at funnel depth 2 is not printed: a depth's share prints only where every class at that
  depth is printed, as in step 2's r3-P42 file. The CSV, the figure (redrawn by this entry's own plot function,
  its subtitle reworded) and this README were changed. The "For the lead" note is marked as settled. No number changed.
