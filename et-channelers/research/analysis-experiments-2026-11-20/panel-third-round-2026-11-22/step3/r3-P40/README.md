# r3-P40 / r4-P25: passed prophesied years against control years

Third-round panel programme, step 3 (forecasts and time), class a.2 (ruling 11). Run on 2026-11-26 (UTC, every time from
`date -u`) by the step-3 agent for r3-P38 and r3-P40, a model agent working for the project lead (not a person), in one run
with r3-P38 (shared code and shared prespecification section 0 in `../r3-P38/`). r4-P25 is carried: its primary is
r3-P40's (programme 2.5).

**Exploratory; not a test of H1-H10.** Tier L: the 23 non-development seen creators of deposit 2's split, run once with no
split. Cue families near named years only (deposit 3's L15 through the shared matcher, 30-token window, spoken years
normalised); cue counts, sense not resolved, precision unknown. Voice labels and TIME's roles are model-coded and not
checked by a person. Only "the first matching cue family" would be printed, never a frame. No date is said to have failed.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What was run, in order

| Step | Time (UTC) | What |
|---|---|---|
| Sources read | 13:48:14 to 14:02:27 | as r3-P38; deposit 4 (`README.md`, `year-roles.csv`) checked against its `hashes.md` (both match) and copied byte for byte (`private/deposit-4-year-roles.csv`) |
| Alignment check, prespecification | 14:05:53 to 14:09:16 | as r3-P38; `prespec.md` hashed at 14:09:16Z with r3-P38's (`prespec-hash-record.md`) |
| Extract | 14:09:21 to 14:09:54 | `../r3-P38/code/extract_p3840.py full` (year tokens with spoken form and TIME role) |
| Analysis | 14:13:39 to 14:13:47 | `code/p40.py`: the matcher's own L15 counts and this entry's window arithmetic agree on every sequence; every year token was found at its position |
| Public files | 14:17:20 to 14:20:01 | `code/publish_p40.py`; counts set by `code/nest_check_p3840.py` |
| Privacy checks | 14:20 to 14:23 | as r3-P38 |

## Results in words

- **Year mentions.** The 23 creators name 662 four-digit years from 1800 to 2099 (nearly all transcribed as digits).
  275 of them were open at upload (the year of the upload or later; r3-P38's side of deposit 4's placement) and 387 had
  passed. Of the passed ones: class 1 (prophesied target years) 57 mentions, named by 10 to 19 creators (2012 by 5 to 9);
  class 2 family A (2001, 2008) 30 mentions by 5 to 9 creators; class 2 family B (2020) 46 mentions by 10 to 19 creators;
  other passed years 254 mentions, 1844 and 1954 among them (described only; named by fewer than 5 creators).
- **Class 3: not computed (the deposited class-3 rule yields no controls on this roster).** Under deposit 4's match (same
  creator, spoken form and voice; distance from the upload year within one year of a class-1 mention's; no year
  within two years of a target year), controls are possible only where a creator's uploads lie 2 or more calendar
  years apart. This is a defect of the lead's deposited rule, found on application; it says nothing about the
  creators' speech. Under the prespecified 4-year window, fewer than 5 creators hold a class-3 mention.
- **No cue family can be computed.** Inside the 30-token windows of the passed class-1, class-2, class-3 and biographical
  mentions, no form of fulfilment framing, timeline split or deferral framing is used by 5 or more creators, so each
  family and their pooled set read **"not computed (too few terms or creators)"** (the thin rule of addendum 2d), and
  fewer than 5 creators hold a classified cue family near the years of any class. Every stacked cue-share row, by class
  and voice, and every contrast (class 1 against control family A, against family B with Holm across the two, and
  against class 3) is therefore not computed; the checks C2, A1, A6 and r3-P42's control-year band have nothing to
  read. r3-P42 had found L15 thin near the literature years alone; deposit 4's year roles do not change that on tier L.
- **Biographical reference rows**: passed years outside classes 1 and 2 whose TIME small-model role is "biography" are
  named by 10 to 19 creators; no cue family is used near them by 5 or more creators. TIME's year hits on these recordings
  all lined up with the transcripts; a role was assigned to all but 5 of them.
- **Passed ledger statements** (deposit 4's placement: a frozen window that had ended before the upload day): 19
  statements of 5 to 9 creators; no classified cue family is carried by 5 or more creators.
- **Memory timeline** (creator-balanced mentions per 100,000 tokens, bars only where 5 or more creators name a year of
  that role): 2012 1.58 and 2000 0.81 (class 1; 1987, 1999, 2003 and 2011 are named by fewer than 5 creators each); 2008
  1.35 (family A; 2001 fewer than 5); 2020 2.27 (family B); other passed years 1.10 (1990s), 1.57 (2000s), 4.92 (2010s),
  4.45 (2020s); years open at upload 19.93 (2020s) and 0.85 (2030s). Named years cluster near the uploads.
- **Predictions**: the account-prediction cells of r3-P40 and r4-P25 are silent in every column; nothing is scored.
- **Multiplicity** (deposit 2): 56 primaries in the register; about 2.8 readings beyond a margin expected by chance at
  half-margin effects. No reading was made here.

## Rows not computed

Every cue row and contrast: FULFIL, SPLIT, DEFER and the pooled set (thin); the stacked first-matching cue shares of
class 1 (all six years and 2012 alone), class 2 families A and B, class 3 and its 4-year sensitivity, the biographical
reference rows, 1844 and 1954, and the passed ledger statements, in every voice; the contrasts D_A, D_B and D_3 with
their Holm step, C2, A1, A6 and band checks. The by-voice rows rest on fewer than 5 creators in every class (on the 11
voice-eligible creators, years are rarely named inside the voice definition).

## Files

| File | What |
|---|---|
| `public/data-r3-P40-rows.csv` | cue families' thin-rule status; per class and voice: creators naming, creators with a classified cue family, status |
| `public/data-r3-P40-contrasts.csv` | the three contrasts and their status |
| `public/data-r3-P40-timeline.csv` | the memory timeline by role |
| `public/fig-r3-P40-years.{png,pdf}` | the memory timeline beside the status of the stacked cue shares by class and voice |
| `prespec.public.md`, `prespec-hash-record.public.md` | redacted public copies of the prespecification (section 2; section 0 is `../r3-P38/prespec.public.md`) and of its hash record; the originals and their hashes stay private |
| `code/p40.py`, `code/publish_p40.py`, `code/nest_check_p3840.py`, `code/style.py` | analysis, publication, the nested-count check; style copied unchanged |
| `contacts.md`, `status.json` | reads (no contact); status with every file's SHA-256 |

Shared code (`../r3-P38/code/p3840common.py`, `extract_p3840.py`) is cited by hash in `status.json`. `private/` holds
the copied year roles, the results, the count register and the logs; it is never published.

## Privacy

The creator counts printed are the tier's 23, r3-P38's eligible set ("all but fewer than 5 of 23") and decade bands for
the creators naming a class ("5 to 9", "10 to 19"); every count other than 23 is banded because step 2a printed
layer-user counts as bands whose memberships are not in the register. "Fewer than 5" means 0 to 4.
The nested-count check over step 1's stored-membership register, step 2's printed sets, r3-P42's 11 and both entries' sets
leaves every band with 5 or more admissible values (r3-P38's four-value form keeps all four). No estimate or interval
is printed on any banded row (nothing is computed), so decision 62 has nothing to withhold. Timeline bars are
creator-balanced means over all 23 creators; no creator count is printed per bar; decades named by fewer than 5 creators
are not listed. Solvers, identifier scan and PNG/PDF checks: as in `../r3-P38/README.md` (0 hits, 0 rows narrowed; the
d62 adapter found no printed row of this entry to test).

## Departures

1. **The window-arithmetic check** (prespecification 2.3) is worded there as "hits that belong to at least one mention or
   A6 variant". It was run as: the matcher's counted L15 hits with every year from 1800 to 2099 as target years equal the
   hits lying within 30 tokens of any year token (digit-with-separator tokens included, as the matcher counts them). Every
   sequence agreed. No A6 spoken-year variant occurs on these creators.
2. **Counts banded beyond the shared count rule** (every count other than 23): a privacy choice made after the
   nested-count check; no value changed.

## For the lead

1. **L15 stays thin on tier L** with deposit 4's year roles: no cue form is used by 5 or more creators near any class of
   passed year. A count on more creators (the tuning pool, or fresh creators) would be a new registration; the frames
   remain class c (2 to 4 USD; about 6 coder-hours).
2. **Settled (the lead's decision 73): the deposited class-3 rule yields no controls on this roster.** Under deposit
   4's match, controls are possible only where a creator's uploads lie 2 or more calendar years apart (for the 4-year
   window, fewer than 5 creators hold a class-3 mention). Any revision would be a new deposit before a new count; the
   corrected rule goes on the fourth panel's agenda with the larger-tier run.

## Changes at the joint staging of steps 3 to 5 (2026-11-26T14:59:32Z, UTC from `date -u`)

- **Class 3 (the lead's decision 73).** `public/data-r3-P40-rows.csv` now prints the class-3 rows as "not computed
  (the deposited class-3 rule yields no controls on this roster)" and says why in its header; the Results bullet
  above says it plainly. The CSV was edited by hand with a dated comment line (the publication script was not
  rerun); the figure's "not computed" for class 3 stands. No number changed.

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- The year-mention totals fold the two literature years into the other passed years (values that could narrow a count
  are not printed); the class-3 condition is restated as the condition under which controls are
  possible; the "For the lead" note on class 3 is marked as settled. The rows CSV's header and this README were
  changed. No value changed.

## Change by the lead's decision 104 (2026-11-26T17:33:22Z, UTC from `date -u`)

- The CSV headers and this README state the count form "fewer than 5" as 0 to 4. No number changed.
