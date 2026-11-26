# Deposit 3: the step-2 sense and collision register, the blind lists, their cross-review, and r3-P42's checks

Third-round panel programme, step 2: r3-P41, then the lists of r3-P43 to r3-P61, r3-P40 and their round-4 entries,
under the lead's ruling 11 and decisions 51 to 60 of 2026-11-26.
- Assembled at 2026-11-26T11:02:33Z (UTC, from `date -u`) by the step-2 cross-reviewer, a model agent working for the project
  lead (not a person).
- The lists were written by the step-2 lexicon writer, also a model agent.
- The public commit of this folder gives the external time stamp. Its merge time is the deposit's time.

**Written from the literature only, blind to the corpus. No count has been made.**

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What is in this folder

| Path | What it is |
|---|---|
| `r3-P41/` | The sense and collision register (255 rows; 1,192 expanded forms), its 124 sources, 16 layers, 6 gate sets, 15 planned lists, build checks and README. Unchanged; hashed first |
| `lists/`, `lists-README.md` | The 15 lists as first written (projections of the register). Unchanged |
| `code/` | The register's data and builder, and the list builder. Unchanged |
| `hash-record.md`, `lists-hash-record.md`, `addendum-1.md` | The writer's hash records and reading record. Unchanged |
| `addendum-2/` | The blind cross-review, with four parts: (1) `addendum-2-register.public.csv`: 114 dated rows of corrections and proposals, each with a reason, a severity and a source. In one row a source name is withheld (see below). (2) `lists/`: changed list files, with the rapture layer in its own file, the set-aside column, the memo crosswalk, the coder-collision column and the balance file. (3) `rule-coder-collisions-public.csv`: the list side of every collision with the ledger's rule coder, and the coder family as a label only. (4) `gate-word-check.csv`, the reviewer's proposed additions to r3-P42, and its hash record |
| `addendum-2b/` | The rows the lead accepted (decisions 54 and 55), applied: `addendum-2b-register.csv` (32 rows); `rules-a2b.md` (amended matching rules); gates, added register rows and sources; the crosswalk and balance files; `lists/` (changed list files, "-a2b"); its hash record |
| `addendum-2c/` | Single-source terms set aside (decision 57 item 1): `README-a2c.md` (the rule), `addendum-2c-register.csv` (7 terms), the regenerated list, crosswalk and balance files ("-a2c"), and its hash record |
| `addendum-2d/` | Decision 60: `README-a2d.md`, the correction of r3-P42's "thin class" rule (with `thin-rule-classes-a2d.csv`, the classes it affects); T070 set aside (no supporting source); the regenerated list, crosswalk and balance files ("-a2d"); its hash record |
| `r3-P48-predictions.md` | The members' predictions and precision ranges "fixed now", copied verbatim from the round-3 memos, each member named |
| `r3-P42/prespec.md` | r3-P42's final prespecification of the lexicon checks (draws, seeds and thresholds fixed), with its hash record |
| `hashes.md` | Every file's SHA-256, the deposits this one cites, and the private files cited by hash only |

**Which version binds.** For each list, the addendum-2d file binds if there is one, then the addendum-2c file, then
the addendum-2b file, then the addendum-2 file, then the original. Matching follows the register's rules G1 to G10 as
amended by `addendum-2b/rules-a2b.md`. The set-asides of decision 51 L1, decision 57 and decision 60 apply together.
r3-P42's prespecification is read with the correction in `addendum-2d/README-a2d.md`.

## The order of hashing (times from `date -u`, UTC, 2026-11-26)

1. The register (r3-P41) was hashed at **09:37:22Z**, first. At that moment no list existed.
2. The lists README was written from 09:38. The lists were written at 09:38:49Z from the hashed register, after the
   builder checked the register's hash. Both were hashed at 09:39:07Z to 09:39:09Z.
3. The writer's addendum 1 (reading record) was written at 09:41:33Z, and the draft deposit was hashed at 09:41:50Z.
4. The cross-review's addendum 2 was hashed at **10:28:01Z**.
5. Addendum 2b (accepted rows) was hashed at **10:38:46Z**.
6. r3-P42's final prespecification was hashed at **10:40:33Z**.
7. Addendum 2c (single-source terms set aside) was hashed at **10:58:42Z**.
8. Addendum 2d (the thin-rule correction; T070 set aside) was hashed at **11:01:54Z**.
9. This folder was assembled and hashed at 2026-11-26T11:02:33Z.

Addendum 2d corrects the wording of r3-P42's 'thin class' rule to its evident purpose before any count (decision 60).

No count of any list has been made at any of these times.

## How the lists were made and checked

- **Sources.** The lists come from dictionaries, published scholarship and reference works found on the web, by the
  writer and agents working for it. Every citation was checked by a blind cross-reviewer; corrections are in addendum 2.
- **Phrase forms.** Many phrase forms (resolution phrases, frames, device phrases) were written from a class definition
  that a source documents. The register's `source_check` column says where.
- **Class names.** Class names are descriptive, never evaluative. "Imported" describes where a vocabulary came from in
  the historical record. It never judges a speaker's sincerity.
- **Trope adjacency.** Terms that a glossary of antisemitic tropes documents (AJC 2024) are listed with the flag 'yes'
  or 'possible' and set aside from every count until r3-P54. The set-aside covers:
  - r3-P43 and r3-P44;
  - r3-P48 and r3-P49;
  - r3-P50 and r4-P18;
  - r4-P27, r4-P28 and r4-P29.

  A class that the set-aside empties prints "not computed until r3-P54 (waits for the owner's ethics act)". These
  classes are CR-A of the control register, r4-P27's decisive pair and one window estimand of r3-P48. r3-P54's own list
  waits for the owner's ethics act.
- **Citations of published works.** These are not creator identifiers, and they stay in the register and lists, even
  where the author or organisation also appears as a channel or person on the project's public site. But a counted
  term whose only source is such a work is set aside from every count, because a count of it could approximate one
  channel's own usage. A term with at least one independent other source stays counted. This rule sets aside 7 counted
  terms (`addendum-2c/`).
- **The composition test** of r3-P43 runs over the 12 R strata in occult's codes. et's seven groups enter only through
  et's balance family (via the crosswalk) and an exploratory display. They are not a separate primary.
- **The ADV-NEG class** of the control register follows the hashed rule of r3-P42's prespecification. At exactly half
  of its terms set aside, it is computed.
- **The ledger's rule coder** (deposit 2) is deposited by hash only. Its collisions with the lists are published as the
  list form and a coder-family label, never as the coder's own patterns.

## Not written blind, and not published

- **Source names tied to a single channel** are a fact about the corpus's channels. They are not written, privately or
  publicly (decision 51 L4). One register-addendum row records that such a name, found in a cited article, was not
  added. In the public copy that name is withheld. The private original is cited by hash in `hashes.md`.
- **Named persons** are never listed; a pattern row stands in.
- **r3-P40's passed target years, control years and contested year** come from the frozen ledger, a rule and a ruling.
- **Lightworker and several post-2012 terms** stay "not listed": no findable source dates them.

## Before any count

1. The public commit of this folder.
2. r3-P42's variant list for spellings and spoken numerals, generated by rule and hashed.
3. The second author's lists for the two-author test, hashed. For r3-P43 they are read as agreement only.
4. One run on all non-development seen creators. Every count is a cue count, "sense not resolved, precision unknown",
   until a reader is funded.
