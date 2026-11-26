# r4-P23: the contact class in the frozen ledger

Third-round programme, step 3 (forecasts and time), class a.1. Written 2026-11-26 by a step-3 agent (a model agent working
for the project lead; not a person); times from `date -u`. Exploratory; not a test of H1-H10. Rule-based strata (the
frozen ledger's rule coder) over model-coded world-future statement candidates (LAB-F, TL-BUILD); not checked by a person;
agreement, never accuracy. Nothing is resolved, and no statement is called "failed".

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Question and design

et's question (N22): within creators, are contact-event statements bounded in time less often than world-event
statements? The rival the corpus supports so far: the format sets the window for every class alike. Strata are r3-P36's
cue strata as the ledger's frozen rule coder holds them (et's five contact strata: contact event, intervention,
evacuation, technology release, institutional disclosure; every other statement is "world event"). No member-written list.
Prespecification: `prespec.md` (SHA-256 and time in `prespec-hash-record.md`, hashed 2026-11-26T14:11:40Z, before any
outcome).

- **Tier L** (the lead's common rules: an entry that counts the ledger's frozen rule coder): once on the 23
  non-development seen creators, no split.
- **Eligible creators:** 5 or more statements in each class: **5 to 9** creators.
- **Primary:** per creator, the bounded share (closed window) of contact-class statements minus that of world-event
  statements; creator mean, 90% t interval fixed in advance; margin 5 points (deposit 2); named direction negative.

## Results (`public/data-r4-P23-contrast.csv`, `public/fig-r4-P23-contact.png`)

| Row | Creators | Estimate | 90% interval | Reading |
|---|---|---|---|---|
| Primary: bounded share, contact minus world event | 5 to 9 | -0.037 | -0.125 to 0.051 | undetermined |
| Row 1: any bounded time expression in place of a closed window | 5 to 9 | -0.042 | -0.142 to 0.057 | undetermined |
| Row 2: date refusals and energetic-only statements left out | not computed or not printed | | | not computed or not printed |
| Row 3 (rival): share of bounded statements whose window rests on the talk-level period alone | not computed or not printed | | | not computed or not printed |
| Row 4 (b8's second half): energetic share among bounded statements | not computed or not printed | | | not computed or not printed |

In words: on the few creators with enough statements in both classes, the within-creator difference in how often
contact-class and world-event statements carry a closed window is small, and its interval crosses the margin on the
negative side: **undetermined**. It neither shows the deficit et's question names nor shows the two classes bounded
alike within the margin. Row 1 agrees. Rows 2 to 4 are not computed or not printed.

**Resolvability classes by stratum** (`public/data-r4-P23-strata.csv`): not printed. In every stratum the class cells
that rest on fewer than 5 creators, pooled together, still rest on fewer than 5, so the prespecified rule withholds each
stratum's bar.

**Prediction scored** (deposit 2's account cell; platform format: "flat: contact and world-event statements bounded
alike"): **not decided by this reading** (the primary reads undetermined, not B). et's registered prediction (b8) is for
fresh creators and is not scored; the seen estimate is on its side in sign only, within an interval that includes both 0
and the margin.

**Not computed or not printed:** rows 2, 3 and 4; the stratum description (pooled cells on fewer than 5
creators); the programme's histogram (with fewer than 10 eligible creators a histogram of bins of 5 or more creators would
hold at most one bin; the interval against the margin band is drawn instead, as prespecified).

## Interval and privacy

The count prints as a band, and r3-P30's closest class (B1, one difference in shares per creator) chooses its method by
count, which decision 62 would withhold under a banded count; the t interval on creator values was fixed in advance
instead (in r3-P30's B1 grid it over-covers at 5 creators, 0.92). Values that could narrow a banded count are not printed.
Multiplicity: 56 primaries; about 2.8 readings A would be expected by chance if every true effect sat at half its margin.

## Departures

- The interval method is fixed in advance (t on creator values) instead of r3-P30's count-chosen choice for class B1
  (stated in the prespecification; privacy, decision 62's advice to use fixed methods).
- The programme's histogram is not drawn (stated in the prespecification).

## Files

`prespec.md`, `prespec-hash-record.md`, `code/p23_run.py`, shared code in `../ft-common/code/` (`ftload.py`, `ftpub.py`,
`pubrules.py` copied from step 1's r3-P01, `style.py` copied from the CH plots), `public/` (two CSV files and the figure as
PNG and PDF), `contacts.md`, `status.json` (hashes of every file). `private/results.private.json` holds per-creator
values and is never published.

## Changes at the joint staging of steps 3 to 5 (2026-11-26T14:59:32Z, UTC from `date -u`)

- **Stated against each other (the lead's decision 72).** r3-P38's eligible creators and r4-P21's tier-L creators
  with a closed window (the base of its deixis typing) are each printed as "all but fewer than 5 of 23"; by
  definition both lie inside r4-P23's tier-L creators with ledger statements, which is also printed as "all but
  fewer than 5 of 23". All three are stated against the same 23 and nest inside one another, so no printed form
  narrows another (checked at the joint staging with the private counts). No number or form changed.
- **Fixed 90% t intervals** are accepted (the lead's decision 82); where the fixed t interval over-covers at
  small counts, it is conservative.

## Change by the lead's decision 92 (2026-11-26T15:25:06Z, UTC from `date -u`)

- Some cells were changed (privacy rule); the CSV and the figure
  were changed (the figure redrawn by this entry's own plot function). No number changed.

## Change by the lead's decision 99 (2026-11-26T16:19:27Z, UTC from `date -u`)

- A count form in `public/data-r4-P23-strata.csv` was changed (privacy rule), and this README was reworded;
  the note on the fixed t interval is worded generally. No number changed.

## Change by the lead's decision 103 (2026-11-26T17:16:20Z, UTC from `date -u`)

- Some rows read "not computed or not printed". Every count below 5 in the
  strata file reads "fewer than 5" (0 to 4). The CSVs, the figure (redrawn by this entry's own plot function)
  and this README were changed. No number changed.

## Change by the lead's decision 104 (2026-11-26T17:33:22Z, UTC from `date -u`)

- Rows not computed and rows not printed carry one label ("not computed or not printed") in their count, method and status
  cells and are listed together; change notes are worded in general terms. The CSV, the figure (redrawn by this
  entry's own plot function) and this README were changed. No number changed.
