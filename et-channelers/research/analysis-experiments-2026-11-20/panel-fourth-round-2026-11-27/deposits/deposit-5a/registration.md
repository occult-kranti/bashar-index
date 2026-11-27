# Deposit 5a: the forecast registration (f4-Q07 and f4-Q19)

Fourth-round panel, deposit 5a: the forecast part of deposit 5, hashed and published first and alone (decision 131.9),
before any count of either entry and before the windows of the frozen ledger's largest group pass. Written 2026-11-27
from 10:00:55Z (UTC, from `date -u`) by a drafting agent working for the project lead (a model agent, not a person). The
SHA-256 of this file and the time it was taken are in `hash-record.md`.

**Status.** Exploratory; not a test of H1-H10. The forecast candidates are model-coded (LAB-F, TL-BUILD) and not checked
by a person. The ledger's classes, flags and strata are rule-based and not checked by a person. Every comparison between
instruments is agreement, never accuracy. No statement is ever scored. A date is said to have "passed", never to have
"failed", and the only wording for what could be checked is "scorable as worded".

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Privacy.** No creator, channel, title, id or statement text appears here. No contactee, channeller, channelled being or
group is named. Every number is printed on main, is one of deposit 2's margins, is a design constant fixed here, or is a
date. Works are cited by author and year, with the reading level their review recorded, as the programme cites them.

Contents: 1 frozen inputs; 2 rules common to both entries; 3 f4-Q07; 4 f4-Q19; 5 H10 is untouched; 6 what this deposit
does not do.

---

## 1. Frozen inputs

Paths are relative to `et-channelers/research/analysis-experiments-2026-11-20/`, pinned to commit `ae5f573` of `main`.
Each SHA-256 below is that of the file's bytes at that commit (`git show ae5f573:<path> | sha256sum`), checked at the
time in `hash-record.md`. Three inputs changed between commit `8881a90` and `ae5f573` (the release README, the fourth
panel's programme and `registry.md`): each gained only decision 134's dated notes on the gate sample, which touch none of
the rows cited here. Every later reading reads each input as it stands at the pinned commit and checks its hash first. A
dated correction made later to a file on main is printed beside the reading and never used silently. A private input
whose hash differs stops the reading.

| Input | Path on main | SHA-256 of the bytes at `ae5f573` |
|---|---|---|
| Deposit 1: the frozen ledger's hash | `panel-third-round-2026-11-22/deposits/deposit-1-forecast-ledger.md` | `a610239db91eb26c9072dab050538de44e5028c076d42f60adf2af8fa96fb5f1` |
| Deposit 2: README | `panel-third-round-2026-11-22/deposits/deposit-2/README.md` | `dbee18ac483fb1e1c1346287e7e7ee7d8aa50c38bc94f1b633c1377282b00be2` |
| Deposit 2: the ledger's manifest | `panel-third-round-2026-11-22/deposits/deposit-2/ledger-manifest.json` | `741c4627bc934a620a955a360a7777b3a128a634b0fba350b12f357784970acb` |
| Deposit 2: the ledger figure's data | `panel-third-round-2026-11-22/deposits/deposit-2/data-r3-P39-ledger.csv` | `9d85183fbd06a5eb240c8117ab046bd347675d275854e42c4d5e688f13c80016` |
| Deposit 2: margins and readings | `panel-third-round-2026-11-22/deposits/deposit-2/lead-margins-and-readings-2026-11-26.md` | `c25c8979eb272b19125a0597658295241d1d4c40a33f0a22015032f90bbf18cd` |
| Deposit 2: account cells | `panel-third-round-2026-11-22/deposits/deposit-2/account-prediction-cells.md` | `f8e360695ddf0266b7d6fc89eb2ad852137db20307d1aca0a2d1c6f84ead1c8a` |
| Deposit 2: account cells (matrix) | `panel-third-round-2026-11-22/deposits/deposit-2/account-prediction-cells.csv` | `2efdf3fe26716f3f55a3d323d97d65f6bddec8e7a05f5a3ce9e4b7bba61bdf84` |
| Deposit 2: split policy | `panel-third-round-2026-11-22/deposits/deposit-2/split-policy.md` | `efdcfae32314efc75273cac8cf44cfc20ce34bc9aef7c2f7fd4cf479b943d3e7` |
| Deposit 3: L15, the passed-years cue list (latest deposited version) | `panel-third-round-2026-11-22/deposits/deposit-3/addendum-2/lists/r3-P40-passed-years-a2.csv` | `9b1d8c7d8ad55f6a496730d8032f1bd16d9b07abb25541bb1777bb364c606443` |
| Deposit 3: the gates on L15 (G-A1, G-A8) | `panel-third-round-2026-11-22/deposits/deposit-3/addendum-2/r3-P42-prespec-additions.md` | `345ba152f30f45c9ec535fb31b3365577308f61aeca3e889691984f404eb9fb7` |
| r4-P23: prespecification | `panel-third-round-2026-11-22/step3/r4-P23/prespec.md` | `c206eb26162b808258fd05806cb9ffb59c80b6aad43c9d4989a38466b3e3e5d6` |
| r4-P23: README | `panel-third-round-2026-11-22/step3/r4-P23/README.md` | `0b10c10d5501fa3cd8e0499d033cc630c558abd40bfad0ba5933fcd4232e5f89` |
| r4-P23: the published rows | `panel-third-round-2026-11-22/step3/r4-P23/public/data-r4-P23-contrast.csv` | `94d8cdf0e4ed8a79b0505636357e0d8828151f61580194f961ee0276b44ba934` |
| r4-P23: the strata description | `panel-third-round-2026-11-22/step3/r4-P23/public/data-r4-P23-strata.csv` | `777ee6873ed08684656035fad1768819955da6fabd2c614045188953d7222789` |
| r3-P36 / r4-P21: prespecification | `panel-third-round-2026-11-22/step3/r3-P36/prespec.md` | `ed5a37d4d8b516d64f53789e644afd9c5250d00bb721e101a3427b3ed7a61803` |
| r3-P36 / r4-P21: README | `panel-third-round-2026-11-22/step3/r3-P36/README.md` | `4095a87da91ae39753598f17d9bfb53d0b1f7ec160005d5bca997f1155b11d83` |
| r3-P36: the published slopes | `panel-third-round-2026-11-22/step3/r3-P36/public/data-r3-P36-slopes.csv` | `dada83123483abc68482cea773746b567340587b86e2a2d2f2c3006ea838d9cc` |
| r3-P36: the explicit-window count | `panel-third-round-2026-11-22/step3/r3-P36/public/data-r3-P36-explicit-count.csv` | `9e2263fc80acb39ed1318e964cf007d7779c922785ce76ad6e5bb2da02f3bed9` |
| r4-P21: the calendar typing | `panel-third-round-2026-11-22/step3/r3-P36/public/data-r4-P21-typing.csv` | `1adb88481240e4ba7e7d2fbc378bf4f5c19cc8c02d3c4e61437206b2f304fdc8` |
| r3-P30: interval choice by class and count | `panel-third-round-2026-11-22/step1/r3-P30/public/interval-choice.csv` | `fcfe22cfba84b8b5eedd059ff605afb0055761b88c4c4d96e708d24400a6e1f6` |
| The third panel's programme (cards b3 and b7) | `panel-third-round-2026-11-22/programme.md` | `7f34500c7fa97b3877600175b0ccca394d681b87c6ad0963b40047b5fa0138bd` |
| The third panel's rulings (ruling 3: listing-only snapshots) | `panel-third-round-2026-11-22/lead-rulings-2026-11-26.md` | `d7794594c250201b9264ebc13575a1f62e30779403dbd75a5e8fa777f953f716` |
| TL-7.9: the due calendar | `results/exploratory-2026-11-21/packages/TL/tl-7-9-due-calendar.csv` | `204e3eac1e6b70620d1f269aa92b6ace2c87386674c5636f8e399e255c8c0e05` |
| The TL package's README | `results/exploratory-2026-11-21/packages/TL/README-TL.md` | `5b09ce3e035fb665d246816936e8c72e27174ec0edaf85e5c4b62ca44b0985eb` |
| The release README (TL-BUILD, TL-7.7, TL-7.9, LAB-F, PT rows) | `results/exploratory-2026-11-21/README.md` | `7489b5becabbdcd4bdc5f35548f0f1f77b56fba4cbc1c0499c5edff17ee740c2` |
| The fourth panel's programme (f4-Q07, f4-Q09, f4-Q19) | `panel-fourth-round-2026-11-27/programme.md` | `31cadaa571998408e55e52f94673301aa9195283521533a0f4c954cb55f9b3f1` |
| The lead's decisions 125 to 132 | `panel-fourth-round-2026-11-27/lead-decisions.md` | `bc85a6238b92e05e0c97b9a0897148995d40435125237978e4b3be4a190cb599` |
| H10's registered text (not edited here) | `hypotheses.md` | `831ed6fa718e83e7f21720b8be783cc35d7d3e107d6218947c536d50319ef713` |
| H10's run condition and interval rules (not edited here) | `registry.md` | `a35dd0de83f2a8387297ca78a77fb9fdce3823897d7ddf3da7efdcf2ef7b2e4b` |

Private files, cited by the hashes that deposits 1 and 2 publish (the files stay private):

| Private file | Published in | SHA-256 |
|---|---|---|
| The frozen forecast ledger (frozen 2026-11-26T01:45:31Z) | deposit 1 | `d2e8e3fd32291f3b0b0a40f5e8a54cf88819e391b6c89a536df49c80a799a80a` |
| The ledger's rule coder | deposit 2 | `4fe41740974b88f76358a99bb970bab2c1847b2ca9e907c2e1be518c575aef71` |
| The ledger's builder (placebo draw) | deposit 2 | `004235539db98ecda1a39edfba9d6c07b5b47dbd56f32e631819035276005b27` |
| The recognizer-quality fields | deposit 2 | `3bd8033e89ab3c5b0d20398cec3e8b14a4937984c59f6d52a950935ab1f73a0c` |
| The split draw (development membership, for the private guard only) | deposit 2 | `85848e4cb78327c52163d254a16447b90581fd6e1a696c959237fc7d0ef077f2` |

**Deposit 2's recorded hashes.** Some of the SHA-256 values that deposit 2's README records differ from main's bytes.
This deposit cites main's bytes at the pinned commit. The file-by-file reconciliation is left to a separate correction.

**Stored inputs without a published file hash.** The voice labels of record (LAB-V, freeze 1), LAB-F's stored forecast
labels (held inside the ledger, which carries each label file's SHA-256), the stored transcripts and the recognizer
configuration of record, and the listing scans of 21 and 25 November 2026 (ruling 3). Each later reading records the
SHA-256 of every such file it reads, in its own prespecification, before it reads it.

---

## 2. Rules common to both entries

### 2.1 Margins and reading words (deposit 2, unchanged)

- **Margins.** A difference in shares: 5 percentage points. A ratio: outside 0.80 to 1.25 (absolute log ratio 0.223).
  A coefficient (kappa): 0.10. No margin is lowered to make a reading reachable, and no registered rule is loosened
  after its result (decision 129.13).
- **Reading words, for a row with a named direction:** "A" (the 90% interval lies wholly beyond the margin in the named
  direction, under every admissible reference the row names); "B, accounted for" (wholly inside the margin under every
  admissible reference); "beyond the margin, opposite to the named direction"; otherwise "undetermined".
- **Reading words, for a row with no named direction:** "more than the reference, beyond the margin"; "less than the
  reference, beyond the margin"; "equal to the reference within the margin (accounted for)"; otherwise "undetermined".
- **Printed labels:** "not computed (too few creators)" with fewer than 5 eligible creators; "not printed (privacy
  rule)"; "not computed (no later transcripts)"; "not computed (snapshot not taken on its registered date)";
  "undetermined (the tuning-pool guard does not pass)".
- **The floor rule** binds: no reading is looser than "the near 90% creator-interval bound lies beyond half the smallest
  effect". Every reading word above is stricter.
- **A reading A is never called a finding.**

### 2.2 Intervals

- Every share difference and every log ratio between creators: the 90% t interval on creator values, fixed in advance,
  as r4-P23 used it. Counts print as bands, so a count-chosen method would be withheld (decision 62); fixed t intervals
  were accepted (decision 82). Each caption says "interval fixed in advance".
- Slopes: the method that r3-P30 version 2 chooses for the precision-weighted slope class at the count (section 3.7).
- Agreement (kappa): a creator bootstrap of 2,000 resamples, percentile 90% interval, seed `2026112751`.

### 2.3 The private tuning-pool guard (f4-Q07's rows)

The ledger's candidates come from forecast prompts developed on the 48 development creators, so every f4-Q07 row carries
the tuning-exposure note: "the forecast labels' prompts were developed on the development creators". The guard, in the
programme's wording (f4-Q05b): a reading beyond the margin, in either direction, also needs the same sign of the point
estimate in the development part and in the rest, computed privately from the split draw and never printed. Otherwise
the row reads "undetermined (the tuning-pool guard does not pass)", its one label. No row prints by development
membership, fold or half, and no row of the development part minus the rest prints under any name (decision 129.3).
Deposit 5 may restate the guard for other entries; it may not loosen it for these.

### 2.4 Account cells, before and after the count (decision 130.3)

- **Before any data**, each account's cell in each column reads "forbids" (the account rules that outcome out),
  "allows" (the account is not silent on the column and does not rule the outcome out) or "silent" (the account says
  nothing about the column). An account that forbids nothing prints "forbids nothing".
- **After the count**, each column (or row) reading selects at most one outcome ("more", "equal" or "less" than its
  reference). Each account's cell in that column is then marked:
  - **miss**: the decided outcome lands on a tile the account forbids;
  - **hit**: the decided outcome lands on a tile the account allows, in a column where the account forbids a direction;
  - **absorbed**: the account is silent on the column, or allows both "more" and "less" (the third panel's meaning);
  - **not readable**: the column reads "undetermined" or "not computed", so no outcome was decided.

  The grid prints these marks only; no account is called confirmed or refuted.
- Each account's absorbed columns before any data (silent, or allowing both directions), and the tiles it shares with
  every other account, print beside the grid, as deposit 2's silence shares did.

### 2.5 Privacy guards (both entries)

- No cell, bin, bar, step, week, tile count or plotted group rests on fewer than 5 creators; no per-creator, per-channel,
  per-anchor or per-statement row or point; a row whose creator values are non-zero for 1 to 4 creators is not printed
  (the dominance rule).
- **Counts** print in the printed forms of the project's register (`pubrules.Register`): an exact count, "fewer than
  5", "5 to 9", a ten-band such as "10 to 19", "all but fewer than 5 of N", or "N and fewer than 5 more", registered
  against every printed group (the 71, the 48, the 23, the 11, r4-P23's "5 to 9", the 59 creators with a closed window,
  r3-P36's bands and TL-7.9's channel bands), so that no printed count narrows another.
- **Shares of creators (decision 132.5).** A share of creators takes the printed form of its count; values on the 48,
  the 23 and the 71 print together only where all three counts are exact; otherwise they are banded or not printed.
  Neither entry prints a row on the 48 or on the 23 alone (section 2.3).
- **Decision 129.6.** Every by-voice row first passes a hashed, outcome-free check that its voice-eligible set lies 5 or
  more from the published voice-eligible set (the 11) and from every printed nested set; otherwise it reads "not printed
  (privacy rule)". The standing rule: no statistic is printed on any subset of a printed group that lies within 1 to 4
  of it. The same check applies to row 0's eligible set against r4-P23's published eligible set (section 3.6).
- **Decision 129.10.** No histogram or bin table over a banded set: a creator-balanced mean, its interval and a share in
  the printed form of its count instead. A list term, anchor term or formula is named only where 5 or more creators use
  it.
- No statement text, anchor match, title, description or upload date of any creator is printed. Month axes follow D28's
  form (no year before 2026; earlier periods pooled into one open bin).
- Every public file of a later reading passes the identifier scan, a search for private paths and the name screen
  against the people directories before it is published.

### 2.6 Multiplicity

Each of the two entries has one primary (decision 129.11): f4-Q07's row 0 (section 3.6) and f4-Q19's return column
(section 4.6). Both count in deposit 5's number of primaries K. Every caption reprints deposit 5's half-effect disclosure
(about 0.05 × K readings A expected by chance if every true effect sat at half its margin).

### 2.7 Wording

"Scorable as worded" is the only wording for what could be checked; never "vague", "unfalsifiable" or "recede". A date
has "passed", and no date ever "failed". An outcome equal to its placebo or other reference reads "accounted for", never
"unnoticed". "Undated imminent statements", never "perpetual imminence". "Model-found forward statements" for the first
funnel step. "Availability change", never "hiding". "Followed by", never "caused by". Step and column names describe
forms, never motives. Nothing is called distinctive to these creators without a stratum of periodic forecasters who make
no contact claim (f4-Q20).

---

## 3. f4-Q07: the frozen ledger's scorability funnel, its contact class and its calendar-unit slopes

### 3.1 What it asks

RQ-C1 and RQ-C2 of the programme: what share of the creators' model-found forward statements could ever be scored as
worded, at which step of a statement's form that is lost, whether contact-event statements differ from world-event
statements through the whole funnel, and which calendar the dated windows keep. No statement is ever scored.

### 3.2 Data, sets and unit

- **Statements.** Every row of the frozen ledger (SHA-256 `d2e8e3fd…a80a`, checked before use): 9,033 model-found forward
  statement candidates, bounded and unbounded, of all but fewer than 5 of the 71 seen creators (the manifest's printed
  form). 2,482 carry a bounded time expression; 2,139 a closed window.
- **Fields used** (the ledger's own, as the frozen coder and builder wrote them): the window and its lane; TL-BUILD's
  talk-period flag ("the window rests on the talk-level period alone"); the model-coded absolute type of the time
  expression; the rule-based resolvability class and every component kept with it (closed window, energetic-predicate
  terms, observable-public-predicate terms, the specificity components); flags C (its rule parts and LAB-F's stored
  condition, kept apart) and D; the qualifier families; the contact class and strata; the rule-based deixis (form,
  function, calendar unit); LAB-F's stored checkability record; the upload day; the seeded placebo draw.
- **Voice.** The voice labels of record. A statement's voice is the label covering most of its words (its stored first
  to last units); a statement with no majority voice is left out of by-voice rows. "Claimed voice" means the first-person
  claimed voice; the reported claimed voice is pooled with it only in a named sensitivity row.
- **Sets.** The funnel and rows 0 to 5 run once on every seen creator who holds the rows' statements (tier L over
  model-coded candidates, "L+T", no split). The published 23-creator values of r4-P23 are printed beside as the reference
  and are never re-read as new. No row prints on the 48 or the 23 alone.
- **Unit.** The creator, every share creator-balanced (each creator weighs equally; statements counted equally within a
  creator). The channel, for slopes.
- **Reproduction first.** r4-P23's published primary on the 23 (-0.037, 90% interval -0.125 to 0.051, on "5 to 9"
  creators) is reproduced with the reused code, and the reproduction hashed, before any larger-set count. If it does not
  reproduce, nothing else runs and the lead is told.

### 3.3 The contact class and its rule

- **Rule.** A statement is in the contact class when its text matches one or more of the frozen coder's five contact
  strata (contact event, intervention, evacuation, technology release, institutional disclosure; et's strata). Every
  other statement is "world event". The five strata are pooled into one class by this data-independent rule (membership
  in any stratum), fixed here before any count. A statement may sit in several strata; it counts once.
- **Printing.** Rows 0 to 5 and F-Q07-1 use the pooled contact class only. The strata are never printed apart.
- **Limits.** Rule-based, not checked by a person; precision and recall unknown. The strata must not themselves carry
  unboundedness (N22's note), and the coder's strata do not read the window.

### 3.4 The funnel

Shares are cumulative: the creator-balanced share of a creator's model-found forward statements still retained after
the step. The steps run in this order.

| Step | Retained when | Second instrument, for agreement | Label of the step |
|---|---|---|---|
| 1. Model-found forward statements | every ledger row | none (the starting set) | r3-P23's caveat beside it: finder recall is optimistic |
| 2. Bounded window | the ledger's window is closed (the coder's own input, as in r4-P23's primary) | LAB-F's model-coded checkability part "time window" | read, or "instrument-defined" |
| 3. Explicit absolute window | closed, not resting on the talk-level period alone, and model-coded absolute (a year or an event-table day): r3-P36's subset; its confirmed-upload-day condition applies to slopes only | the coder's rule-based deixis form (calendar-absolute or event-anchored) | read, or "instrument-defined" |
| 4. Named observable outcome | the coder's observable-public-predicate component is present | LAB-F's model-coded checkability part "observable outcome" | read, or "instrument-defined" |
| 5. No conditional flag | flag C is absent (the ledger's flag: its rule parts or LAB-F's stored condition CL or CE) | agreement of the rule parts with LAB-F's stored condition | read, or "instrument-defined" |
| 6. No date-refusal flag | flag D is absent | none | "one instrument only (agreement not defined)" |
| 7. No energetic predicate | the coder's energetic-predicate component is absent | none | "one instrument only (agreement not defined)" |

- **The core.** A statement retained at step 7 is "scorable as worded" in this funnel's sense. Beside the core prints the
  share of it in the coder's rule class R (which also needs the specificity component: a named public actor, institution
  or place, or a mass-observable event class).
- **Exits at step 2,** printed apart: dated statements without a closed window (an open, contradictory or otherwise
  unresolved window); **undated imminent statements**; other undated statements. An undated imminent statement has no
  bounded time expression, and the coder's unbounded-span list matches its text with at least one match that contains the
  word "soon", "shortly", "now", "near", "days" or "weeks", or the phrase "before long". The coder has no imminence class,
  so this split of its own list is fixed here, before any count.
- **The agreement floor.** A step with a second instrument is read only where Cohen's kappa between the step's rule and
  its second instrument, over the statements entering the step (all creators pooled; 5 or more creators holding them), is
  0.60 or more on its point estimate (the project's gate floor), with its 90% interval printed. Below the floor the step
  prints its share with the label "instrument-defined" and no sentence about the speech; every later step carries the note
  "below an instrument-defined step". LAB-F's parts count as present only where the stored record codes them present; any
  other value, "cannot tell" included, counts as absent. The checkability parts inherit a failed two-model gate, and the
  caption says so.
- **The talk-period share.** At every step from step 2 on, the creator-balanced share of retained statements whose window
  rests on the talk-level period alone prints beside the step. From step 3 on it is 0 by definition and prints so.
- **The placebo statements.** The ledger's seeded window-shifted placebo draw (seed `2026112601`; 39 statements; windows
  shifted by minus and plus 12 calendar months) is run through every step as its own line. The builder draws placebos
  only from closed-window statements of rule class R with no date refusal and no collective-choice condition, so the
  placebo line starts from that subset and is a check of the coder, never a contrast of speech.
- **The coder check (a precondition).** Before any step is read, the frozen coder (hash checked) is run on every placebo
  statement with each shifted window. The coder's class rule reads the statement text, the closed-window flag, the upload
  day and LAB-F's stored condition, not the window's dates, so a shift cannot change a class unless the coder or its
  inputs have changed. The check prints "kept" or "not kept". If any placebo statement changes class or flag at any rule
  step, the coder is unstable and the funnel is withdrawn.
- **By voice.** Within each creator, the claimed-voice share retained at each step minus the own-voice share, for creators
  with 5 or more forward statements in each voice, under decision 129.6 and the private guard. Only step 2's row carries
  reading words (it holds an account's cell, section 3.9); every other step is described.
- **Never scored.** The almanac class (windows anchored to the sky-event and numbered-date terms of the coder's event-anchor
  list) and the date-refusal class are described and never scored.

### 3.5 Contact against world event: rows 0 to 5

Each row is a within-creator difference, contact class minus world event, with the creator mean and the fixed 90% t
interval. Rows 1 to 4 keep r4-P23's registered definitions, eligibility and reading words; row 5 is added here.

| Row | Quantity (contact minus world event) | Eligible creators | Named direction |
|---|---|---|---|
| 0 (primary) | bounded share: the share of statements with a closed window | 5 or more statements in each class | negative |
| 0s (sensitivity) | as row 0 | 3 or more statements in each class | negative |
| 1 | the share with any bounded time expression (open or closed) | 5 or more statements in each class, recomputed on the row's statements | negative |
| 2 | row 0 with date refusals (flag D) and energetic-only statements left out of both classes | as row 1 | negative |
| 3 | among bounded statements, the share whose window rests on the talk-level period alone (the rival: the format sets the window) | creators eligible for row 0 with one or more bounded statement in each class | none named ("beyond the margin (direction not named in advance)") |
| 4 | among bounded statements, the share with an energetic predicate (rule class NE or M); b8's registered half, for fresh creators, is not scored here | 5 or more bounded statements in each class | none named here |
| 5 (voice) | among bounded statements, the claimed-voice share | 5 or more bounded statements in each class; decision 129.6; the private guard | positive (et's sub-question: contact dating placed in the claimed voice more often) |

Eligible counts print as bands. The published tier-L primary (-0.037, -0.125 to 0.051) is drawn in outline beside row 0.

### 3.6 The primary and its margin

- **Primary.** Row 0: r4-P23's registered within-creator difference in bounded share, contact class minus world event,
  on the larger eligible set (every seen creator with 5 or more ledger statements in each class).
- **Margin.** 5 percentage points (deposit 2). **Named direction:** negative (contact statements bounded less often).
- **Reading words.** "A" if the interval lies wholly below -0.05; "B, accounted for" if wholly inside -0.05 to +0.05;
  "beyond the margin, opposite to the named direction" if wholly above +0.05; otherwise "undetermined"; "not computed
  (too few creators)" below 5 eligible creators. No reference beyond the margin itself is named (as in r4-P23).
- **Interval.** The 90% t interval on creator values, fixed in advance.
- **Guards.** The private tuning-pool guard (section 2.3). Before any count, an outcome-free check that the eligible set
  lies 5 or more from r4-P23's published eligible set and from every printed nested set; otherwise row 0 reads "not
  printed (privacy rule)".

### 3.7 Calendar-unit slopes (decision 84)

- **The slope class card.** r3-P30 version 2's precision-weighted slope class, cited as the programme's f4-Q09 (ii) and
  stat-meas-5, with every detail not fixed there left to version 2's prespecification: label-free analogue slopes from the seen recognizer cache, with within-channel x set to the
  stored upload dates and heteroscedastic error; counts 5, 8, 12, 18, 23, 30, 40, 50 and 71; 20,000 data sets per cell
  at the counts entries use and 2,000 elsewhere; candidates: inverse-variance random effects with
  Hartung-Knapp-Sidik-Jonkman, with and without the DerSimonian-Laird floor; a REML random-slope model with Satterthwaite
  or Kenward-Roger degrees of freedom; a wild cluster bootstrap-t with Webb weights; a precision-weighted t with weights
  truncated at a fixed quantile; the unweighted t on channel slopes as the comparator. A method holds where its coverage
  lies within 0.02 of 0.90 and each one-sided miss rate is 0.07 or less (r3-P30's rule). The seed, the truncation
  quantile, the three residual-variance scenarios and the smoothed choice rule are fixed in version 2's prespecification,
  hashed before its battery runs. Its method choice by count (T-Q07-2) is deposited before any slope is drawn.
- **Estimand.** TL-7.1's: within a channel, the slope of the window midpoint on the upload day (1, a constant lead or
  rolling horizon; 0, a fixed target). Explicit absolute windows only (step 3's set), confirmed upload days, channels with
  3 or more units over 60 or more days (TL-7.1's protocol rule). Relative and period-framed windows give a constant lead by
  construction (D15) and are not used.
- **Rows.** Pooled, unweighted t on channel slopes (as published: -5.17, 90% interval -17.80 to 7.46); pooled, under
  version 2's chosen method; within channel (channel-centred upload day; the primary split) and between channel (the
  channel's mean upload day); by calendar unit of the stated window: year-unit names, month-unit names, dated days
  (model-coded calendar-day kind), with doubly absolute statements (the coder's "absolute in both" cell) apart; contact
  class against world event where 5 or more creators hold each; the control row with year-flagged statements left out (as
  r3-P36); TL-7.1's within-channel permutation of upload days (9,999 draws) as the reference band. The almanac-unit class
  is described and never scored. No slope here uses the recognizer's timing, so no grid-shift row is needed; any later
  slope that does prints BR-GS's grid-shift row beside it.
- **Tier and words.** Every slope is a description at tier D (decision 128): it prints its estimate, its interval and the
  word "described", with lines at 0, 0.5 and 1, and carries no reading words. The between-channel SD and a prediction
  interval for a new channel print beside the pooled rows: a mixture of regimes across channels makes a pooled slope
  between 0 and 1 a mixture, not an intermediate regime.
- **The margin in regime units, deposited for later waves (class b and c), not read here.** The smallest effect is the
  distance between the regimes (1); the reading point is its midpoint (0.5): "closer to a rolling horizon" if the near
  90% bound lies above 0.5, "closer to fixed events" if the far bound lies below 0.5, otherwise "undetermined".
- **den's prediction, deposited before any slope and described, never scored.** Year-unit slopes near 0 and month-unit
  slopes near 1 (the calendar habit); the informative outcome would be a month-unit slope well below 1.
- **Leverage (outcome-free, first).** Within-channel upload-day spans print as a mean with its interval and the share of
  channels whose span exceeds the design span (the span needed for a slope standard error of 0.5 regime units under each
  residual-variance scenario), in the printed form of its count. No histogram over channels.

### 3.8 Tier and expected decidability

- **Tier.** L (the frozen rule coder) over model-coded candidates, with the tuning-exposure note and the private guard.
  The funnel is a description. Slopes are descriptions at tier D.
- **Expected decidability** (stat-meas's table, round 3): "Undetermined is expected: the published interval spans several
  margins, and even the larger set may not narrow it enough." The funnel's by-voice steps run only under decision 129.6;
  no slope method holds below 71. r3-P30's closest class for row 0 (B1, one difference in shares per creator) prints mean
  widths of 2.336 margins at 8 creators, 1.843 at 12, 1.469 at 18, 1.289 at 23 and 1.126 at 30: B is reachable only when
  the estimate is centred near 0, and A needs a difference well beyond the margin. Those widths come from label-free
  analogues; real rows can be wider. **Plainly: the primary is expected to stay undetermined; the entry's value is a
  frozen, dated description of what could ever be scored as worded.**

### 3.9 Forbidden cells (deposited before any count)

| Account (source, reading level) | Forbids |
|---|---|
| Deficit: contact claims kept undated or spiritualised (Wojcik 2021, full text, passages; Tumminia 2005, abstract) | row 0 "beyond the margin, opposite to the named direction" (contact bounded more often, interval wholly above +0.05) |
| Format: the recording format sets the window for every class (TL-BUILD, TL-7.7; deposit 2's platform-format cell for r4-P23, "flat: contact and world-event statements bounded alike") | row 0 beyond the margin in either direction (A, or opposite); row 3 beyond the margin in either direction |
| The sceptic's expectation that a claimed voice speaks less checkably (den, round 1) | at step 2 (bounded window), a claimed-minus-own retained share whose interval lies wholly above -0.05 (claimed at or above own) |
| The calendar habit (den's slope prediction) | forbids nothing (tier D: described, never scored) |
| Deposit 2's other accounts (performance, inherited genre, business, milieu norm, contact through a filter) | forbid nothing on this entry |

After the count each forbidden cell is marked as section 2.4 sets out (T-Q07-1's account column).

### 3.10 Sensitivity rows (named now; none replaces a primary)

- Row 0s: eligibility at 3 or more statements in each class (section 3.5).
- The funnel with "any bounded time expression" in place of a closed window at step 2.
- The funnel weighted by LAB-F's inclusion probabilities (LAB-F's convention), beside the unweighted primary form.
- The by-voice rows and row 5 with the first-person and reported claimed voice pooled.
- Slopes: the unweighted pooled row as published; the between-channel row; the control row without year-flagged
  statements; the permutation reference band.

### 3.11 Figures and tables (exactly; each figure with its data CSV and caption)

- **F-C1a, funnel lines.** x: funnel step (step 1 reads "model-found forward statements"). y: creator-balanced share
  retained (0 to 1), 90% bars. Two lines (originals; placebo statements). Two panels (contact class; world event).
- **F-C1b, contact against world.** y: rows 0 to 5 and 0s, the published tier-L primary in outline beside row 0. x:
  difference in share, contact minus world event, 90% interval; the band of plus or minus 5 points shaded.
- **F-C1c, by voice.** x: funnel step. y: within-creator claimed-minus-own difference in share retained, dot-intervals,
  with the band of plus or minus 5 points.
- **T-C1a, exits.** Per step: the creator-balanced share lost there; kappa with its 90% interval against the floor
  (0.60); the step's label; the talk-period share; at step 2, the three exits printed apart.
- **F-C2a, slope forest.** y: the rows of section 3.7. x: slope in regime units with its 90% interval; lines at 0, 0.5
  and 1; the word "described" at right.
- **F-C2b, coverage grid.** x: channels simulated (5 to 71). y: 90% coverage, one line per candidate method, the band
  0.88 to 0.92 shaded; a second panel of one-sided misses with a line at 0.07.
- **F-C2c, leverage.** The mean within-channel span with its interval and the share above the design span in the printed
  form of its count; the design curve of the span needed for a slope standard error of 0.5 regime units under three
  residual-variance scenarios.
- **F-Q07-1, resolvability classes by class.** x: the contact class (pooled) and world event. y: creator-balanced share
  of statements in each rule class (R, M, NE, NU, NX), stacked. Merging, fixed here: R and M merge first into "an
  observable public predicate (R or M)"; any class cell still on fewer than 5 creators then merges into "other classes
  (pooled for privacy)"; a bar whose pooled cell still rests on fewer than 5 creators reads "not computed or not printed".
- **F-Q07-2, when the core would mature.** x: the month in which a core statement first becomes checkable (window end
  plus 30 days, TL-7.9's rule), in D28's form, consecutive months merged until each cell holds 5 or more creators. y:
  creator-balanced count share. Caption: when an outcome would become observable, never whether it occurs.
- **T-Q07-1.** Rows 0 to 5 and 0s: eligible creators (band), estimate, interval, margin, reading, and each account's cell
  with its mark.
- **T-Q07-2.** The precision-weighted slope class's method choice by count, with Monte Carlo intervals.
- The folded disclosure arm's F-C5a, F-C5b and T-C5a are registered with that arm in deposit 5 (section 3.14).

### 3.12 Privacy guards specific to f4-Q07

The rules of section 2.5, and: no stratum is printed apart; no anchor, year or month of any single statement is printed;
the core's maturity months print only in merged cells of 5 or more creators; within-channel spans print only as a mean
and a share; F-Q07-2 pools periods before 2026 into one open bin.

### 3.13 What happens at maturity

Nothing of f4-Q07 is read at maturity. Its rows describe the frozen ledger and depend on no later upload and no event; they
run after deposit 5 whether or not any window has passed. F-Q07-2 prints when outcomes would become observable, never
whether they occur. No statement is checked against anything that happened.

### 3.14 The folded disclosure arm (U16): deferred to deposit 5

The programme folds U16 into f4-Q07 as a conditional arm. Its blind table of official acts, its lag scale and N27's
three-way prediction table (where the transparency-reduces account and the stigmatized-knowledge account name their
cells) are written blind and hashed in deposit 5, before any count, as the programme's order of work says. This deposit
fixes only that the arm does not read the ledger's windows, and that the news-hook account forbids a voice split beyond
the margin.

### 3.15 Preconditions and order

1. This deposit is hashed and merged.
2. Deposit 5 is hashed and merged (it carries the half-effect disclosure's K and the arm of section 3.14).
3. r3-P30 version 2's prespecification is hashed; its battery runs; T-Q07-2 is deposited (before any slope).
4. Outcome-free: the hash checks; the reproduction of r4-P23's primary; the coder check on the placebo statements;
   decision 129.6's checks; the nesting check of row 0's eligible set; the eligible counts in their printed forms.
5. The funnel, rows 0 to 5, then the slopes. Each later step is prespecified and hashed before its outputs are read.

---

## 4. f4-Q19: after the window, the January 2027 maturities

### 4.1 What it asks

When a window in the frozen ledger closes, do the same creators return to it, reframe it, change their cadence or
offers, or carry on, and does any of this differ from what they do around the ledger's placebo windows? Exploratory;
same roster, so persistence only (a claim about creators like these needs fresh creators, f4-Q20). No statement is
scored: "matured" means only that the window's end has passed.

### 4.2 Which windows: the maturity groups

- **The January 2027 group (primary).** Every ledger statement with a closed window whose end day plus 30 days falls in
  January 2027, TL-7.9's rule for "first checkable": window end days from 2026-12-02 to 2027-01-01. TL-7.9 printed this as
  its largest group (156 window units, 336 statements, 25-29 channels, at its check date of 2026-11-21); the ledger's own
  count of the group is reproduced and printed against TL-7.9's row before any later file is read.
- **The close day** of a statement is its window's end day. Event time runs in weeks from the close day; the first-checkable
  day (close day plus 30 days) is marked on the axis.
- **The December 2026 group** (TL-7.9's first row: window end days from 2026-11-01 to 2026-12-01; 51 window units, 115
  statements, 15-19 channels) is read under the same rules as a described sensitivity row only, on uploads dated after
  2026-11-25 (no new rows on files already opened, decision 129.8).
- **Later groups** (TL-7.9's later rows) are not registered here. Each needs its own dated registration before its
  first-checkable month.

### 4.3 Anchors, placebo anchors and the second reference

- **Anchor rule (rule-based, fixed here).** For each statement in the group, its anchor is a pair: a key term and a year.
  The key term is the event-anchor noun of the frozen coder's event-anchor rule where the statement's rule-based deixis
  form is event-anchored; otherwise the name of the window end's month. The year is the window end's year. Where the
  window spans whole calendar years (it starts on 1 January and ends on 31 December), the anchor is the year alone.
- **A return** is a later upload of the same creator, with an upload day from the close day plus 1 to the close day plus
  84 (12 weeks), whose transcript holds the key term and the year within 30 tokens of each other (r3-P40's window), or
  the year alone for whole-year anchors. Matching uses the coder's own normalisation (lower case; spoken years as digits)
  and its month rule. A creator's statements with the same anchor count once (distinct anchors). Later uploads carry no
  voice labels; every voice and every speaker in them counts.
- **Placebo anchors (the card's reference).** The same rule applied to the window shifted by minus and by plus 12 calendar
  months (the ledger's shift, by the coder's own shift function), so the key term stays and the year moves by one. A
  statement's placebo outcome is the mean of its two shifted outcomes (0, 0.5 or 1), counted in the same later uploads.
- **The second admissible reference (the swapped-creator reference).** In uploads made after the close, the real year
  and the two placebo years stand at different distances from the time of speaking (one placebo year is the current or
  coming year, the other an earlier one), and ordinary calendar talk differs with that distance. So for each distinct
  anchor of a creator, the reference is the creator-balanced share of other seen creators (with no ledger statement on
  that anchor and one or more transcribed upload in the same days) whose uploads in those days hold the anchor, each
  using only its first n uploads by date, where n is the creator's own number of uploads in those days (all of them, if
  fewer). **This reference is conditional on the owner's act:** it exists only if the later transcripts cover every seen
  creator's uploads in those days, which widens what that act would cover (section 4.4). Without it, the primary's
  reading is at most "undetermined" (section 4.6).
- **The ledger's own seeded draw** (the 39 placebo statements) is a sensitivity row (section 4.9).

### 4.4 Snapshots, horizon and later transcripts

- **Snapshots** (listing-only, metadata only, no download, no audio, no video opened, under ruling 3). S0 is already
  taken; S1 to S3 are named here **subject to the owner's go-ahead**:
  - S0, the listing scans of 21 and 25 November 2026 (ruling 3): the baseline;
  - S1, 2027-02-01: feasibility first, and availability as a sensitivity row;
  - S2, 2027-04-05: the primary snapshot for every column at the 12-week horizon;
  - S3, 2027-07-12: the 26-week sensitivity rows.

  Each is taken on its date or within the 7 days after it; otherwise every row that depends on it reads "not computed
  (snapshot not taken on its registered date)". No date is moved after any outcome is seen.
- **Horizon.** 12 weeks (84 days) after the close day for the primary; 26 weeks (182 days) as a sensitivity row.
- **Later transcripts** are the owner's act: a download of the audio of the later uploads listed at S2, and local
  recognition with the recognizer of record in its stored configuration (no re-decode output is used), as heavy jobs under
  the machine rules. The scope the primary needs: every seen creator's uploads with an upload day from 2026-12-03 to
  2027-03-26, since the second reference reads other creators' uploads in the same days; the sensitivity rows extend it
  to uploads from 2026-11-26 (the December 2026 group) and to 2027-07-02 (the 26-week horizon). Without later
  transcripts the return and framing columns read "not computed (no later transcripts)" and the metadata columns still
  run.

### 4.5 The columns

Each column is a within-creator contrast, the real window against its reference, with the creator mean and the fixed 90%
t interval. Each reads with the words for a row with no named direction (section 2.1). Its outcome is "more", "equal" or
"less" than the reference when the reading decides, and no outcome otherwise.

| Column | Creator value | Reference | Margin | Eligible creators |
|---|---|---|---|---|
| Return (primary) | over the creator's distinct anchors: the real outcome minus the placebo outcome | placebo anchors; and the swapped-creator reference (both admissible) | 5 points | one or more distinct anchor in the group and one or more transcribed later upload within 12 weeks |
| Framing of a return | the share of returns to real anchors whose first matching L15 cue family within 30 tokens either side is fulfilment or timeline split, minus the same share for returns to placebo anchors (L15 with deposit 3's gate G-A1) | returns to placebo anchors | 5 points | one or more return of each kind |
| Cadence | log of (uploads in the 56 days after the reference day + 0.5) / (uploads in the 56 days before + 0.5), minus the same at the placebo reference day | the reference day shifted by minus 12 calendar months (the same season) | absolute log ratio 0.223 (0.80 to 1.25) | one or more upload in each "before" window |
| Offers | the share of uploads whose page carries an offer cue (PT's frozen page-cue families for payment, booking, course, event or shop; three of these miss PT's precision gate, as main prints), after minus before, minus the same at the placebo reference day | as cadence | 5 points | one or more upload in each of the four windows, with page metadata in the snapshot |
| Availability at equal age | the share of the creator's recordings carrying a group statement that are unavailable at S2, minus the share among the creator's other seen recordings uploaded within 30 days of them (equal age at the same snapshot) | the same creator's other recordings | 5 points | one or more recording on each side |

- **The reference day** for cadence and offers is the creator's lower median close day among its group statements. The
  days before and after it exclude the day itself.
- **Availability** counts any listing change that makes a recording unavailable ("availability change"); removals by the
  author and by the platform are split in a row where the snapshot shows the reason.
- **Model-free columns.** Return, cadence and availability use no model and no list beyond the coder's own rules. Framing
  uses deposit 3's L15; offers use PT's frozen rule. The group itself rests on model-coded candidates, and every caption
  carries the tuning-exposure note.

### 4.6 The primary and its margin

- **Primary.** The return column on the January 2027 group at the 12-week horizon: within creator, over the creator's
  distinct anchors, the share returned to minus the placebo share.
- **Margin.** A risk difference of 5 percentage points. **No direction is named:** the accounts disagree, and their
  directions sit in the account table (section 4.8).
- **Reading words.** "More than placebo, beyond the margin" if the interval lies wholly above +0.05 under both admissible
  references; "less than placebo, beyond the margin" if wholly below -0.05 under both; "equal to placebo within the margin
  (accounted for)" if wholly inside -0.05 to +0.05 under both; otherwise "undetermined"; "not computed (too few
  creators)" below 5 eligible creators; "not computed (no later transcripts)" without them. If the second reference
  cannot be computed, the reading is at most "undetermined". An outcome equal to the placebo reads "accounted for",
  never "unnoticed".
- **Interval.** The 90% t interval on creator values, fixed in advance.

### 4.7 Tier and expected decidability

- **Tier.** L: the anchor rule, the placebo rule, L15 and PT's rule are fixed before any later upload exists, over the
  frozen ledger's model-coded candidates, on every seen creator who holds a group statement. Class b (later collection);
  same roster, persistence only. No row prints by development membership.
- **Expected decidability.** stat-meas's table holds no row for this card; by analogy with r3-P30's class B1 (one
  difference in shares per creator), mean widths are 2.336 margins at 8 creators, 1.843 at 12, 1.469 at 18 and 1.289 at
  23: B is reachable only when the estimate is centred near 0, and A needs a large difference. The cadence column reads,
  by analogy with r3-P30's log-ratio class, 0.359 margins wide at 12 and 0.288 at 18, while no method holds at 23. Few
  creators will hold both a group statement and transcribed later uploads, and the third panel's b7 expected "fewer than
  5 creators" for availability. **Plainly: the primary is expected to stay undetermined or not computed; the entry's value
  is a registration made before any of these windows closed, with each account's forbidden cells fixed in advance.**

### 4.8 The account table (den's table; every account's forbidden cells)

den's round-1 table, as the card names its accounts. The drafter wrote the cells; den, whose table it is, reviewed and
amended them before the lead accepted the table. Columns as in section 4.5; outcomes "more", "equal", "less" than the
reference. A cell not listed as forbidden in a non-silent column reads "allows".

| Account (source, reading level) | Return | Framing of a return | Cadence | Offers | Availability |
|---|---|---|---|---|---|
| Outreach after the date (Festinger, Riecken and Schachter 1956; catalogue, its claims as quoted in Kelly 2025a; disputed by Kelly 2025a, full text) | forbids less | silent | forbids less and equal | silent | silent |
| Demise and attrition (Kelly 2025b, full text; Kelly 2025a for no increase after the date) | forbids more | silent | forbids more and equal | forbids more | silent |
| Reinterpretation as success (Tumminia 1998 and 2005, abstracts) | forbids less | forbids less and equal | silent | silent | silent |
| The emic timing rule ("already happened on an energetic level"; the third panel's emic contribution (programme section 5), as the ET review's bridge B1 records it; a reported insider norm, not a checked literature entry) | silent | forbids less | silent | silent | silent |
| Passing unnoticed (Bader 1999, abstract) | forbids more and less | silent | forbids more and less | forbids more and less | forbids more and less |
| The serial-format null (the third panel's b3; deposit 2's platform-format cells for b3 and b7) | forbids more and less | silent | forbids more and less | forbids more and less | forbids more and less |

Why each account forbids what it forbids (the reading of each work as its review records it):
- **Outreach:** committed members increased proselytising after the date passed; on a platform, the date is addressed,
  not avoided, and uploads rise after the close beyond the placebo day. The account, as quoted, concerns unpriced
  proselytising; PT's offer cues are priced forms, so it is silent on offers.
- **Demise and attrition:** demise is the most common outcome in the extant cases, and outreach did not rise after the
  date; on a platform, fewer uploads, no rise in offers, no renewed attention to the date.
- **Reinterpretation as success:** members' interpretive reason sustains a passed prophecy's validity; returns to the
  passed date carry fulfilment or timeline-split framing beyond returns to placebo dates, and the date is not avoided.
- **The emic timing rule:** a stated event is said to have occurred on an energetic level once its date passes; returns
  to a passed date carry fulfilment framing at least as often as returns to placebo dates. It says nothing about how
  often the date is returned to.
- **Passing unnoticed:** the date passes without response; no change in either direction in return, cadence, offers or
  availability.
- **The serial-format null:** dated statements of periodical recordings behave "as for any periodic column": no
  difference in either direction in return, cadence, offers or availability. Deposit 2's b7 cell ("no excess of removal
  by the author at equal age") stays as recorded there; the two-sided cell here is stricter, not looser.

**Beside the grid:** passing unnoticed and the serial-format null forbid identical tiles and part only on f4-Q20's
stratum of periodic forecasters with no contact claim.

Absorbed columns before any data (silent, or allowing both directions): outreach, framing, offers and availability;
demise and attrition, framing and availability; reinterpretation, cadence, offers and availability; the emic timing
rule, return, cadence, offers and availability; passing unnoticed, framing; the serial-format null, framing. Every
account forbids at least one tile. Deposit 2's other accounts are not named on this card and are not entered. After the
count, each account's cells are marked as section 2.4 sets out; no account is called confirmed or refuted.

### 4.9 Sensitivity rows (named now; none replaces the primary)

- The 26-week horizon (S3).
- The ledger's own seeded placebo statements (the 39) as the placebo set, in place of the shift applied to every group
  statement.
- The minus-12-month placebo anchor alone (both years in the past at speaking time).
- Page return: the anchor rule run on the titles and descriptions of later uploads in the listing snapshots (metadata
  only; runs without later transcripts).
- Availability at S1; author removals alone, where the snapshot shows the reason.
- The December 2026 group (section 4.2), described.

### 4.10 Figures and tables

- **T-Q19-1, feasibility, printed first** (at S1 and again at S2, before any outcome): creators with a group statement;
  of them, creators with a later upload listed; creators eligible for each column. All as bands.
- **F-Q19-1, event time.** x: weeks since the close day (0 to 12; 0 to 26 in the sensitivity row), the first-checkable
  day marked. y: creator-balanced cumulative share of distinct anchors returned to, real against placebo anchors, with
  the 90% band of the real-minus-placebo difference under 9,999 within-creator exchanges of the real and placebo labels
  (seed `2026112752`). A week is drawn only where 5 or more creators are eligible.
- **F-Q19-2, cadence.** The cadence log ratio after against before the reference day, as dot-intervals, real against
  placebo days, with the 0.80 to 1.25 band; the offers row beside it with the plus or minus 5-point band.
- **F-Q19-3, the account table as a tile grid.** Accounts by tiles (each column's three outcomes): "forbids", "allows" or
  "silent" before the data; after the count, each account's cells in a column marked "miss", "hit", "absorbed" or "not
  readable" as section 2.4 defines them. Beside it, each account's absorbed columns before any data, the tiles it shares
  with every other account, and the sentence: passing unnoticed and the serial-format null forbid identical tiles and
  part only on f4-Q20's stratum of periodic forecasters with no contact claim.
- **T-Q19-2, the columns** (added: the card names no table for them): column, eligible creators (band), estimate,
  interval, margin, reference, reading, and the outcome it selects.

### 4.11 Privacy guards specific to f4-Q19

The rules of section 2.5, and: no anchor, key term, month or year of any single statement prints, and no anchor-level
row; weeks, columns and tiles rest on 5 or more creators; availability prints as shares only, never a list of recordings;
offer cues print by family only; no title or description text; the swapped-creator reference prints only as the row's
estimate.

### 4.12 What happens at maturity

| When (UTC) | What happens | What is read |
|---|---|---|
| Before 2026-12-02 | This deposit is hashed and merged; no group window has closed | nothing |
| 2026-12-02 to 2027-01-01 | The group's windows close | nothing |
| 2027-01-01 to 2027-01-31 | The group's statements become first checkable | nothing (no statement is ever checked) |
| 2027-02-01 (S1) | Listing-only snapshot, subject to the owner's go-ahead | T-Q19-1 (feasibility) only |
| 2027-04-05 (S2) | Listing-only snapshot, subject to the owner's go-ahead; later transcripts if the owner acts | T-Q19-1 again; then cadence, offers and availability; then return and framing if transcripts exist; then the grid's marks |
| 2027-07-12 (S3) | Listing-only snapshot, subject to the owner's go-ahead | the 26-week sensitivity rows |

Each reading after S2 is preceded by its own prespecification, hashed before its outputs are read, which may add
computational detail but changes nothing fixed here. If the owner does not act on later transcripts, the primary reads
"not computed (no later transcripts)", the metadata columns are printed with their readings, and their cells are marked.

---

## 5. H10 is untouched

H10's registered test (`hypotheses.md`, "H10. Silence after the date (conditional)", and its run condition and interval
rules in `registry.md`) is not edited, restated, narrowed or run by this deposit. Its estimand (a within-creator risk
difference against matched undated statements, coded by two blind readers on a replication wave), its smallest effect of
0.15, its run condition of at least 50 matured statements from 15 creators, and its refutation rule stand as registered.

f4-Q19 is not H10's test and not a version of it. It uses a different reference (placebo anchors and a swapped-creator
reference, never matched undated statements), a rule-based anchor match (no readers), a 5-point margin and a
same-roster, persistence-only frame. It reads the same frozen ledger that the third panel's b3 named for a run of H10,
and reading it here alters nothing H10 needs: H10's matched undated controls, its blind readers, its capture date, its
wave and its run condition are left to H10's own procedure. f4-Q19's readings are never printed as H10's result, as
evidence for or against H10, or as meeting H10's run condition. If H10 is ever run, it runs on its own registered terms.

---

## 6. What this deposit does not do

- It computes nothing on any outcome and makes no count: no ledger row, statement text, transcript, label file, page or
  later upload was read to write it.
- It scores no statement and checks no statement against any event. Scoring any statement stays class c and the owner's
  act, and it is unfunded.
- It makes no model or API call and no download, and it opens no hold-out, other or reliability folder.
- It registers no list beyond the split of the coder's own unbounded-span list (section 3.4) and the anchor rule
  (section 4.3); every other list is deposit 3's, and new lists wait for deposit 5.
- It defers the folded disclosure arm to deposit 5 (section 3.14) and registers no maturity group after January 2027.
- It changes no published file.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
