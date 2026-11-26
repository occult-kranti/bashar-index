<!-- Redacted public copy of `prespec.md`, made 2026-11-26T14:25:54Z (UTC, from date -u) by the step-3 agent. The original was hashed at 2026-11-26T14:09:16Z, before any outcome of either entry was computed; the hash recorded at hashing time is kept privately, because the original holds exact creator counts that the public files print as bands (step-1 decision 49 item i). Redactions, marked [redacted: ...]: three creator counts replaced by their printed forms; one reference to a hash. Nothing else differs. -->

# r3-P38 / r4-P24 (qualifier clauses at speaking time) and the shared rules of r3-P40 / r4-P25: prespecification

Written 2026-11-26 from 14:07:46Z (UTC, from `date -u`) by the step-3 agent for these two entries, a model agent working
for the project lead (not a person). It fixes every choice that the programme (`programme.md`, step 3, on `origin/main`
a5e20e0), deposits 1 to 4 and the lead's decisions 1 to 69 leave open. Section 0 binds both entries; section 1 is r3-P38's.
r3-P40's own section is `../r3-P40/prespec.md`, which cites this file by its SHA-256 (kept privately). Both files are hashed together
before any outcome of either entry is computed.

Exploratory; not a test of H1-H10. Every count is a cue count: sense not resolved, precision unknown (no reader). The
forecast statements are model-coded candidates (LAB-F), not checked by a person; the frozen coder's fields are
rule-based, not checked by a person; TIME's roles are model-coded, not checked by a person. Comparisons between
instruments are agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What was known when this was written

- Read: the programme (sections 0, 2.0, 2.1 step 3, 2.2 card b8, 2.3, 2.5, 3.1 N23 and N24, 5), `programme-decisions.json`,
  the lead's rulings, deposit 2 (margins register, lead's margins and readings, split policy, account-prediction cells,
  `deposit.json`, ledger manifest), deposit 3 (README, lists README, L15 and its addendum-2 file, the public rule-coder
  collision table, the L05, L01, L13 and register rows of the prevention-colliding terms, addendum 2d, r3-P42's
  prespecification), deposit 4 (README, `hashes.md`, `year-roles.csv`: both hashes match), step 1's `r3-P30` interval
  table and readings table, the lead's step-1 and step-2 decisions, step 1's `pubrules.py`, step 2's shared matcher,
  `desc_common.py` and r3-P48's prespecification section 0, r3-P42's README (it says L15's three cue families are thin
  on the 23 creators when read only near the literature years, and gives r3-P42's A1 shares), r3-P56's README and status,
  the frozen coder (`rule_coder.py`, hash `4fe41740...5aef71` checked) and the ledger's builder.
- Looked at, outcome-free: the ledger's row structure with every text field redacted (one row's structure printed; its
  six frozen rule-qualifier flags were visible for that one row, all false); a label file's structure with text redacted;
  TIME's hit and answer structure (one answer printed); r3-P42's extract structure (voice sides).
- Counted, outcome-free (no qualifier family, cue hit or year mention counted): the tier-L ledger rows by lane and
  placement (578 rows placed "open" on [redacted: all but fewer than 5 of the 23] creators: 568 closed windows, 4 contradictory, 6 open-ended; 19 "passed" on [redacted: 5 to 9]
  creators; 86 without a findable target; 2,134 undated); voice-eligible creators (11, r3-P42's set); an alignment run
  of `code/extract_p3840.py check` (14:05:53 to 14:06:10Z): all 410 recordings of r3-P42's extract line up unit by unit
  with a fresh seen-only read, and all 658 of TIME's D1_year hits on 160 of these recordings line up by their stored
  offsets; 15 register terms are flagged "yes" or "possible" for trope adjacency (50 expanded forms).
- Not read: any count, share or rate of the coder's families on these creators, of L15's cue families near any year,
  or of year mentions; r3-P42's private results.

## 0. Shared rules (both entries)

### 0.1 Tier, creators and instruments

- **Tier L** (deposit 2's split policy; decision 65 item 1): both entries count deposit-2 or deposit-3 instruments, so
  they run once on the 23 non-development seen creators, with no split.
- **r3-P38's families**: the six qualifier families of the frozen rule coder (deposit 2), called through
  `rule_coder.code(text, False, None)["qualifiers"]`, imported from its file after its hash is checked, never edited
  (decision 54 item 2). Matched forms for the thin rule and C2 come from the coder's own compiled patterns and skip
  rules (`p3840common.family_forms`); a unit where forms and the coder's flag disagree stops the run.
- **r3-P40's cue families**: deposit 3's L15 in its binding file (`addendum-2/lists/r3-P40-passed-years-a2.csv`)
  through the shared matcher `step2/common/lexmatch.py` (hash `2297864c...8d28`): FULFIL, SPLIT and DEFER, the 30-token
  window, G1a's spoken years.
- **Year roles**: deposit 4 (`year-roles.csv`, hash `90fd5fc8...39e9`, copied byte for byte and checked).

### 0.2 Reads (seen only; none is a contact)

1. r3-P42's private extract (hash `8101aba5...1215`): token sequences per recording and voice-side run, unit ids, unit
   token counts and voice sides.
2. One new read of the same 410 transcripts through `prep.load_units` (prep's seen guard; creator checked against the
   split's 23): the extract holds no cased text (the coder's input) and no spoken form of a year. Each recording must
   line up with the extract unit by unit (count of units, tokens per unit under the matcher's normalisation); one that
   does not is left out and counted (the check run found none). Nothing textual is stored: per unit, the six family
   flags, their matched forms, the trope-overlap flag, and the year tokens (position, year, spoken form, TIME role).
3. The frozen ledger (deposit 1, hash `d2e8e3fd...a80a`), rows of the 23 creators.
4. LAB-F's seen forecast label files (`llm/labels/seen/forecasts`), the 410 recordings only: unit spans of every finder
   candidate, every coded statement and every frame (r3-P38's non-forecast pool).
5. TL-BUILD's upload dates (`TL/private/timeline-rows.private.json`, hash `28fdfae6...d448`; TABLE's confirmed day B,
   else the midpoint of the label's upload period), as the ledger and TL-BUILD use them.
6. TIME's stored D1_year hits and small-model roles (round 2; `time-hits.private.pkl` `4d87b791...8702`,
   `answers-small.private.json` `17a3da0a...0149`), lined up by RX's frozen normalisation (`normalise.py`
   `d407c805...65dc`) at the stored offsets; a role is given to a year token only where the hits of one unit and year
   and the tokens of that unit and year are equally many.
7. r3-P42's hashed A6 variant list (`variants-a6.private.json`, `acc61b07...033d`): its six spoken-year forms only.
8. Step 1's `pubrules.py` (`24149975...255c`) and step 2's `desc_common.py` (`17e5184a...8acc`) for r3-P30's choice
   and the nested-count register, imported unchanged.

No hold-out, other-group or reliability file is opened; no recursive search of the run folder.

### 0.3 Placement (deposit 4)

- **A ledger statement** (dated rows only) is placed by its frozen window against its upload day: **open** if the
  window's end is on or after the upload day, or the window is open-ended (lane "open"); **passed** if the end is before
  the upload day; **unclassed** if it has no window (lane "unresolved_by_program") or no upload date. Undated rows are
  unclassed. Open statements are r3-P38's forecast items; passed statements are r3-P40's described row.
- **A named year** Y in a recording uploaded in year U is **passed** if Y < U and **open at upload** if Y >= U. Open
  years belong to r3-P38's side and enter r3-P40 only in its memory timeline.

### 0.4 Statistics, intervals and readings

- **Margins** (deposit 2): ratio of rates, |log ratio| 0.223 (0.80 to 1.25); difference in shares, 0.05.
- **Words.** With a deposited direction (r3-P38: excess in forecast sentences, emic's prediction in card b8 and N23):
  **A** = the 90% interval lies wholly beyond the margin in that direction and every named control row's estimate lies in
  the same direction; **B** = wholly inside the margin; "beyond the margin, opposite to the named direction" = wholly
  beyond on the other side (step-1 decision 2); otherwise **undetermined**. Without one (r3-P40): "beyond the margin
  (<side> higher)", "within the margin (B)", "undetermined"; no letter A.
- **Order of statuses**: the thin rule ("not computed (too few terms or creators)"), then the carrier floor ("not
  printed (fewer than 5 creators carry the estimate)" or r3-P40's withdrawal), then the reading, then the checks in this
  order of precedence: C2 ("undetermined (term-dependent)"), A1 ("not separable from the ledger's coded families"; r3-P40
  only), A6 ("undetermined (spoken-year variants)"; r3-P40 only).
- **Thin rule** (addendum 2d; decision 65): a family or class is computed only if 3 or more of its expanded forms (for
  the coder: distinct matched forms, digits written as #) are each used by 5 or more creators in the text the class is
  read on; the same for a pooled set as a whole.
- **C2**: leave one form out (every form used by 1 or more creators in that text); a changed reading word, or an
  estimate that crosses a margin bound, reads "undetermined (term-dependent)". The coder's forms are never named in a
  public file (deposit 3 publishes no coder pattern); L15 forms are named only where 5 or more creators use them.
- **Multiplicity**: no family-wise adjustment (deposit 2), except Holm across r3-P40's two control families (deposit 4).
  Every output prints the register's 56 primaries and the half-effect disclosure (about 2.8 readings beyond a margin by
  chance). A reading beyond a margin is never called a finding.
- **Seeds**: `numpy.random.default_rng([s, k])`, s = the first 8 hex digits of SHA-256("step3|<entry>|<check>") read as
  an integer, k a stream number named in the code.

### 0.5 Privacy (binding: the brief's common rules, the step-1 decisions 49 to 64, step 2's section 0.4)

- No cell, bin, bar or plotted group on fewer than 5 creators; no per-creator row or point; no names, ids, titles or
  quotations; no term named unless 5 or more creators use it, and no coder form named at all.
- **Creator counts** by step 2's `desc_common.Counts` (the stored-membership register of `pubrules.known_register()`,
  plus r3-P42's 11 voice-eligible creators and every set these entries print): identical sets print alike; a set nested
  1 to 4 from a registered exact set of 10 or more prints "all but fewer than 5 of N" / "N and fewer than 5 more"; near a
  small or banded set, or within 1 to 4 of 101, 18, 6 or 36, a decade band; otherwise exactly. One form per set in every
  file. Every printed count is also checked by number against the counts printed in the release, step 1, step 2 and
  deposits 2 to 4.
- **Decision 62**: a row whose count is banded or withheld and whose interval method is chosen by r3-P30 at the row's
  count prints no estimate, interval or reading. r3-P38's interval is fixed here in advance (section 1.4) and r3-P40's
  is a fixed bootstrap, so the rule does not bite; it is stated in each file.
- No group means that, with an overall mean, would solve for group sizes; no quantiles of creator values; blank cells
  only by these rules; privacy notes in general terms.
- **Solvers** before finishing: zsolve, qscan_all2, whole_position_scan, the s1_* solvers that apply (s1_blanks with
  `d62`), the identifier scan (creator codes, audio hashes, video ids, page keys). PNGs without text chunks; PDFs
  without document information.
- **Wording**: families and cue families are named descriptively; no motive is printed; a conditional is never called
  an escape; no date is said to have failed; offers, prophecy and contested content are described neutrally.

## 1. r3-P38 / r4-P24: qualifier clauses at speaking time

1. **Forecast items.** The ledger rows of the 23 creators placed "open" (0.3). Each item is the statement's label units
   (`statement_units`, first to last), and it carries family k if the coder flags k on any of its units (each unit's text
   coded alone). An item whose units fall outside its recording is dropped and counted (none expected).
2. **Non-forecast pool (primary).** Units of the same recording outside every finder candidate's span, every coded
   statement's span and every frame unit of its LAB-F label file, and outside every ledger row's units; units with no
   token are left out. **Named control row (NF-2)**: the pool is every unit outside the ledger rows' units only.
3. **Length matching.** For an item of n units and L tokens (tokens under the matcher's normalisation, from the
   extract), the candidates are the runs of n consecutive pool units of the same recording; a run's length is its token
   sum. The matched set is every candidate with |log(l / L)| <= log 1.25; if fewer than 5, the 5 nearest in |log(l / L)|
   (ties: the earlier first unit); if fewer than 5 candidates exist, all of them; if none, the item is dropped and
   counted. A candidate carries family k if the coder flags k on any of its units. Matching never reads a family.
4. **Statistic, per family k.** For creator c, F = the number of c's items carrying k; E = the sum over c's items of the
   share of its matched set carrying k (the length-matched expectation). y_c = log((F + 0.5) / (E + 0.5)). The estimate
   is the mean of y_c over the eligible creators (every creator with 1 or more matched item; [redacted: all but fewer than 5 of the 23] expected), printed as a
   ratio with its 90% **t interval on creator means**. This is r3-P30's design class H_rare_counts ("log rate ratio of
   rare counts, 0.5 added, counts summed within creator"), whose choice is the t interval at every simulated count from 8
   to 71; the eligible set is known to hold 8 or more creators before any outcome, so the method is fixed here in
   advance and carries no count information (as step-1 decision 64 found for class E). Beside it, descriptions only:
   the creator-balanced share of items carrying k, and the creator-balanced matched expectation (E over the creator's
   number of items).
5. **Readings** (0.4), direction: excess (forecast sentences denser). Named control row: NF-2; for the prevention family
   also the sensitivity row S1. Floors: the thin rule over the forecast items and their matched candidates of the
   eligible creators; the carrier floor needs 5 or more creators with F > 0 and 5 or more with E > 0. C2 on every
   computed family.
6. **Sensitivity and described rows.**
   - **S1** (decision 54 item 2, in the words of r3-P42's hashed prespecification, A2): for the prevention family, an
     item or candidate whose prevention match lies on a span matched by a register term flagged "yes" or "possible" for
     trope adjacency is dropped (the pool is rematched without such candidates). Read like the primary, printed beside.
   - **S2**: emic's band of plus or minus 20% (0.80 to 1.20; card b8) as a second margin: reading words beside.
   - **Q**: the ledger's frozen rule-qualifier fields (coded on the stored quotation at the freeze) for the same items,
     with the same matched candidates: estimate and interval described, not read; and the creator-balanced agreement
     between quotation coding and unit coding per family (agreement, never accuracy).
   - Counts printed: items placed, dropped, and matched; the share of items matched within the ±25% band.
7. **No voice split**: the programme names none for r3-P38.
8. **Plot**: grouped bars of each family in forecast and matched non-forecast sentences (creator-balanced shares), with
   the excess-ratio strip (estimate and interval against the 0.80 to 1.25 band; emic's 0.80 to 1.20 band marked).
9. **Predictions**: the deposited account-prediction cells of r3-P38 and r4-P24 are silent in every column, so nothing is
   scored. Card b8's registered prediction (emic) is for fresh creators and a secular genre; it is not tested here.
10. **Order**: this file and r3-P40's are hashed; then `extract_p3840.py full`; then `p38.py` and `p40.py`; then the
    public files, figures, solvers and the README. After the hash, nothing here changes; any departure is stated in the
    README.
