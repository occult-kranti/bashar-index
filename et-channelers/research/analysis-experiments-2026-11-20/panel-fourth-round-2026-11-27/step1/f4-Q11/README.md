# f4-Q11, step 1: media metaphors for contact, the voice-free rows on the 48 (fourth panel)

Run on 2026-11-27 (UTC, every time from `date -u`) by the step-1 analysis agent, a model agent working for the project
lead (not a person), under deposit 5's registration (section 4.11; step 1 of section 3.3) and the lead's decision 156.

**Exploratory; not a test of H1-H10.** Cue counts, sense not resolved, precision unknown. Families are named by what is
said, never as a sign of anything. "channel" is never counted; literal platform senses are flagged and never counted.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Tier wording.** Voice-free rows on the 48 are **a second description on a disjoint set**; the 71 are **described
only**. The list is new in deposit 5, so **no published 23-creator value exists**; the registration's "23 as the published
reference" prints as that statement.

## What was run, in order

| Step | Time (UTC) | What |
|---|---|---|
| Prespecification | hashed 18:22:41 | `private/prespec.md`, before any count of the list |
| Amendment 1 | hashed 18:24:32 | the placebo pool's exclusion (deposit 5's lexicon lists, not its instrument families), the shared second pass |
| Second pass | 18:24 to 18:28 | deposit 5's list matched on the step-1 extract's sequences (scope f4-Q11; G3, G4), after deposit 3's first pass; the placebo candidate table |
| Analysis | 18:29:12 (the 48), 18:29:45 (the 71) | the rows below |
| Public files | final run 19:34:25 to 19:34:26 (after decision 166; earlier runs 18:41:21 to 18:41:23 and, after decision 162, 18:57:25 to 18:57:27) | `public/` |

## Printed first: the literal-platform share (F-B3b)

Of the matched tokens of each family, the flagged literal-platform share is 0.17 for radio, 0.53 for recording and
playback and 0.18 for computing and network (creator-balanced, the 48); wire and screen hold no flagged form.

## The primary: described only (decision 129.9)

The registered primary is **the composition test across the five generation families on the 48, voice-free**, by
r3-P43's placebo and pseudo-strata machinery. That machinery groups creators by CSS-5's title-profile ladder, which
rests on model-coded title labels. Decision 129.9 bars creator groups from model-coded title labels in any new
registration; deposit 5's registration named this test as f4-Q11's primary without resolving that rule, and the conflict
was found at count time. Under the lead's decision 162 the stricter rule governs, so the primary reads **"described only
(decision 129.9)"**: its creator groups rest on model-coded title labels; under decision 129.9 no reading is made. The
values, described: pseudo-F 0.62 (permutation p 0.633); matched-placebo band 0.21 to 2.48; pseudo-strata band 0.24 to
1.55; over 10 reseeded placebo draws the band endpoints range from 0.13 to 0.24 and from 2.23 to 3.04. The 71's values
are not printed (decision 166). No published 23-creator value.

## Expected decidability (registration 4.11)

"The composition test reads against bands, not margins; on the 23, none of r3-P43's parts lay outside both ... **The
composition and voice rows are expected to stay undetermined unless the structure is strong.**"

## Other voice-free rows

- **T-Q11-1**: wire and signal, radio, recording and playback, and computing and network are computed; screen and
  programme is thin on the 48 ("not computed (too few terms or creators)") and prints no value beside that status
  (decision 166). Rates and creator bands of the computed families in `data-f4-Q11-generations.csv`; the 71's rates are
  not printed (decision 166).
- **F-B3a, the dated strip**: four generations are dated (radio is undated and not placed); with the screen family thin,
  three dated families are computed, so the rank test reads "not computed (fewer than 5 computed dated families)" and
  the strip is described (shares of the 48 with their placebo bands).
- **F-Q11-2, near the act**: within 30 tokens of a self-described mode cue against matched windows (share-difference
  margin 5 points; no direction named): radio and computing and network read "equal within the margin (accounted for)";
  wire and signal (difference 0.067, 90% 0.014 to 0.120) and recording and playback read "undetermined".
- **Sensitivity**: the flagged forms counted apart (their rates printed, never pooled). No form of the list was placed
  differently by the two authors, so "f4-Q11: all listed forms" equals the primary and is not printed.

## What is not computed, and why

F-Q11-1 and claimed over own by generation: by voice, step 2. The persistence rows on the opened new files: barred
(decision 129.8). Dating by two agents' agreement: not a date, not used.

## Account cells (`data-f4-Q11-accounts.csv`)

Media renewal: hit (the computing and network family computes). Platform self-talk: not readable (two families
undetermined). Generic vocabulary (forbids a composition outside both bands): not readable (the composition is described
only, decision 129.9).

## Files

| File | What |
|---|---|
| `public/data-f4-Q11-literal-platform.csv` | F-B3b (printed first) |
| `public/data-f4-Q11-date-table.csv` | T-B3a |
| `public/data-f4-Q11-generations.csv` | T-Q11-1 (voice-free columns) and the flagged-forms sensitivity row |
| `public/data-f4-Q11-composition.csv` | the primary, with its Monte Carlo spread, and the 71 |
| `public/data-f4-Q11-survival.csv` | F-B3a |
| `public/data-f4-Q11-near-act.csv` | F-Q11-2 |
| `public/data-f4-Q11-accounts.csv` | the account cells |
| `public/fig-f4-Q11-literal-platform`, `-dated-families`, `-near-act` (PNG, PDF) | F-B3b, F-B3a, F-Q11-2 |
| `status.json` | every file's SHA-256 |

## Multiplicity and privacy

K = 33 (about 1.65 readings beyond a margin or band expected by chance at half-margin effects). No cell rests on fewer
than 5 creators; creator counts print as bands; terms are named only where 5 or more creators use them (the list's term
labels); no name, id, title or quotation.

## Amendment of 2026-11-27, from 18:55:17Z (UTC, from `date -u`): the lead's decision 162

The first version read the primary against its bands. The lead ruled (decision 162) that every row whose creator groups
rest on CSS-5's title-profile ladder prints its values and bands as a description only, with no A or B reading, because
decision 129.9 bars creator groups from model-coded title labels and the stricter rule governs. The primary therefore
reads "described only (decision 129.9)" (`data-f4-Q11-composition.csv`, with the note "its creator groups rest on
model-coded title labels; under decision 129.9 no reading is made"), and the generic-vocabulary account's cell reads "not
readable". No count was rerun and the hashed prespecification is unchanged. The other rows group no creators by title
labels and keep their readings.

## Amendment of 2026-11-27, from 19:36:04Z (UTC, from `date -u`): the lead's decision 166

The independent check of step 1 led to decision 166. Applied through the publication code; no count was rerun, no reading
changed and the hashed prespecification is unchanged:
1. **The thin family prints no value.** G4-SCREEN, thin on the 48, prints its status with no creator band, rate or
   flagged rate (`data-f4-Q11-generations.csv`).
2. **The 71's values.** A value is left unprinted wherever the printed values of the other sets would let a reader
   recover it. Main prints no 23-creator value for this new list, so the 71's values beside the 48's are left
   unprinted, 9 rows: the 71's rate for all five generation
   families (`data-f4-Q11-generations.csv`; G4-SCREEN computes on the 71 only), the 71's flagged share for radio,
   recording and playback, and computing and network (`data-f4-Q11-literal-platform.csv`), and the 71's composition
   values (`data-f4-Q11-composition.csv`; pseudo-F is not linear in its creators, but the test is applied alike).
3. **Final version.** The words marking the files as unfinished are removed from the title, the CSV headers and
   status.json, and the note addressed to the lead is removed (its content, that no published 23-creator value exists
   for this list, is stated above). A value that rounds to zero prints as "0.0" (radio's near-the-act interval).

## Amendment of 2026-11-27, from 19:58:51Z (UTC, from `date -u`): the lead's decision 172

Wording only (no file but this README changed): the rule for the 71's values is stated in the public decisions file's
general words ("left unprinted wherever the printed values of the other sets would let a reader recover it").

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
