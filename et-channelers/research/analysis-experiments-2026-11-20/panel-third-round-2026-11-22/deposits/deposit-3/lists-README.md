# Step-2 lists: which programme entry uses which list, and how each list is built

Written 2026-11-26 from 09:38 UTC (from `date -u`), after r3-P41's register was hashed at 09:37:22 UTC
(`hash-record.md`) and before any list file was written. Writer: the step-2 lexicon writer, a model agent working for the
project lead (not a person).

**Written from the literature only, blind to the corpus; no count has been made.**

> Exploratory programme; no measure in this study can tell whether a non-human source speaks; every measure describes
> the speech in these recordings and how the creators present it.

## How every list is built

- **A list is a projection of the hashed register** (`r3-P41/register.csv`). `code/build_lists.py` selects the
  register rows that name the list in their `lists` column and whose `rule_kind` is one that counts or shapes a count
  (`counted`, `gated`, `counted-unless-gate`, `flagged`, `frame`, `domain`, `class row`). Nothing is added to a list that
  is not in the register, and no register row is edited.
- **One row per term.** Columns: `list_id`, `entry` (running number), `term_id`, `term`, `class_or_stratum`,
  `sense_ids` (the register's programme sense ids), `forms` (every variant), `exclusion_forms`, `gate` (with its list
  and window), `rule_kind`, `rule` (the register's disambiguation rule), dating columns (L01 only), `strand`,
  `trope_adjacent`, `also_on_lists`, `source_keys` and `citations` (full references with URLs, from
  `r3-P41/register-sources.csv`).
- **Matching** follows the register's rules G1 to G10 (normalisation, longest match inside a list, exclusions, gates that
  never use another list's terms, context-assigned tokens flagged and never counted, cue counts only, unit and base
  rules, voice from the frozen labels, and et's trope-window condition).
- **Run once** on all non-development seen creators with no split (split policy, tier L: "lists written blind from the
  literature and hashed before any count"), after r3-P42's checks are prespecified and hashed.
- **Cross-review.** A second agent reviews the register and lists before the deposit. Any change is a new dated version
  with a new hash.

## Programme entries and their lists

| Programme entry | List(s) | Construction rule |
|---|---|---|
| r3-P41 (sense and collision register) | `r3-P41/` (the register itself) | One row per term; the collision matrix is computed from shared tokens of the lists below (G3) |
| r3-P42 (lexicon checks without a reader) | none; uses every list | Prespecification draft in `r3-P42/prespec-draft.md` (not hashed, not run) |
| r3-P43 / r4-P26 (dated vocabularies, by voice) | **L01** `r3-P43-dated-strata.csv` | Terms by thematic-historical layer (16 layers, `r3-P41/register-strata.csv`), each layer with an entry date and its source; per-term first-currency dates where a source gives one, "uncertain" or "undated" otherwise; S12 imported, kept apart; S14 the undated devotional column; evacuation lore (S06) only with ship collocates and never in S01 with rapture lore; wording "draws on vocabulary first current in period X", never descent |
| r3-P44 / r4-P27 (co-use of strata; fusion thesis) | **L02** `r3-P44-strata-pairs.csv` (pairs over L01, L05, L06) | All pairs of L01 layers, plus the decisive pair (L01 federation strand against adversarial strand, with et's and occult's and emic's opposed predictions as the programme states them) and the conspirituality pair (L05 against L06); no new terms |
| r3-P45 (density or dimension) | **L03** `r3-P45-density-dimension.csv` | Density-scale forms (Law of One ordinals) against dimension-scale forms (ordinal and numeral D forms); bare "density", "dimension" and "3d" excluded |
| r3-P46 (source names as title templates) | **L04** `r3-P46-source-name-classes.csv` | Applied to titles. OPEN (kind and collective names) and FRANCHISE (individual names used by many channels in the published record); UNNAMED is a residual rule; the single-channel class is not written (register T244; decision D4) |
| r3-P48 (control register v2) | **L05** `r3-P48-control-register-v2.csv` | Sub-registers with descriptive names: CR-A names a hidden controlling group; CR-B names an institution as controlling; CR-C names a technology or programme of control; CR-D names an ontological or spiritual control system; CR-E describes the population as controlled. Adversary classes split by valence: ADV-NEG, ADV-AMB. BRIDGE terms (polarity cosmology) count as cosmology by default and as bridge only within 20 tokens of a CR-A or CR-B term. Trope senses never counted, totalled or shown by family (register G10; decision D1). The members' predictions for r3-P48 are not in the programme and are not written here |
| r3-P49 / r4-P18 (concentration of control talk) | **L05** and **L06** `r3-P49-shift-terms.csv` | Control terms from L05; shift terms from L06; placebo terms are drawn by r3-P42's generator, not listed |
| r3-P50 / r4-P18 (page against speech) | L05, L06, L12, L13 | No list of its own; per-list ratios; commerce placebos link-bound and word-class-matched placebos come from r3-P42's generator |
| r3-P51 / r4-P28 (named actors and contested content) | **L07** `r3-P51-named-actor-classes.csv` (+ L05 for the control register) | Institutions by class (security, space, international, government, religious, media, corporations); disclosure split by two gates into institutional and consciousness-based (a token passing both is flagged, never counted); contested public-health content; criminal-law process words for den-soc's legal-risk rows; a named-person pattern row (never printed per person) |
| r4-P29 (two ways of defanging) | **L08** `r4-P29-defanging.csv` | Inner-means and outside-agent resolution phrases, counted only inside units that hold an L05 ADV-NEG, ADV-AMB or CR-A hit (the base); a lexical proxy and recall bound |
| r3-P52 / r4-P12 (plural self-reference) | **L09** `r3-P52-plural-self-reference.csv` | First-person plural and singular forms; units holding a self-naming or address frame are removed from the ratio; "the US" excluded |
| r3-P53 / r4-P30 (self-described modes) | **L10** `r3-P53-self-described-modes.csv` | Cue classes for the programme's modes: full trance, conscious or blended, dictation, relay, higher self or Source, received text read aloud, recitation of another receiver, light language (vocalisation without recognisable words, self-described as light language); "creators who describe their practice as X" |
| r3-P16 (who shifts, by mode) | L10's groups | No list of its own |
| r3-P14 (self-described attribution of reading aloud) | L10 class MODE-READALOUD | No list of its own |
| r3-P55 (endorsement at matched positions) | **L11** `r3-P55-endorsement.csv` | REF-CREATOR and ENDORSE hits within 20 tokens in one unit; "this channel" counted only with no platform word within 10 tokens; den-soc's "no price" row uses L14's PRICE class as a row condition, not as a sense collocate |
| r3-P56 (insider commerce idiom, dissemination asks) | **L12** `r3-P56-commerce-idiom-dissemination.csv` | IDIOM (payment as exchange, gift or support) and DISSEM (asks to pass a message on); a recall probe of LAB-A |
| r3-P60 (destinations and suppression talk) | **L13** `r3-P60-destinations-suppression.csv` | Destination classes by link domain in page text, with funnel depth 1 to 4 (writer's order) and an own-site residual; suppression talk split into platform moderation and hidden-actor suppression; "censored" flagged, never counted |
| r3-P61 (persuasion devices, priced or unpriced) | **L14** `r3-P61-persuasion-devices.csv` | Device families from Cialdini and Mathur et al., commercial forms and devotional twins apart; each hit coded priced when a PRICE cue is in the same unit; a pilot, an instrument for the comparison set only |
| r3-P40 / r4-P25 (passed prophesied years) | **L15** `r3-P40-passed-years.csv` (+ L01's "2012" and "timeline split") | Cue families FULFIL, SPLIT, DEFER within 30 tokens of a target-year token; literature target years listed; the ledger's passed years, control years and the contested year are class rows decided by rule or ruling, not by reading |
| r3-P38 / r4-P24 (qualifier clauses) | none new: fixed in deposit 2 | Emic's six qualifier families inside the ledger's rule coder (`code/rule_coder.py`, SHA-256 `4fe41740...5aef71`), hashed with the ledger under ruling 11; not rewritten |
| r4-P23 (contact class in the ledger) | none: fixed in deposit 2 | Cue strata inside the ledger; no member-written list (programme) |
| r3-P54 (hateful-trope screen) | not written | Its list waits for the owner's ethics act; stage B by people only |
| r3-P37 (two clocks) | not written here | An a.1 entry whose primary is a date table, not a lexicon; its word-anchored class would need a list the lead may assign |
| r3-P05, r3-P06 (asks, frame formulas, platform asks) | none | a.1 entries on model-coded label classes, not member-written lists |

## Visibility

All lists are public in the draft deposit, with these exceptions proposed for the lead (register decisions D4, D6): no
single-channel name list exists; open and franchise-like being names (L01 S14 and named rows, L04) are published from the
literature unless the lead decides to deposit them by hash only.
