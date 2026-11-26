# r3-P41: the shared sense and collision register (step 2 of the third-round programme)

Written 2026-11-26 (register built at about 09:36 UTC, from `date -u`) by the step-2 lexicon writer, a model agent working
for the project lead (not a person). Lead's ruling 11 of 2026-11-26: members may write and cross-review lists now, from
the literature only and blind to the corpus, with this register hashed first; lists go in a second deposit before any
count.

**Written from the literature only, blind to the corpus; no count has been made.** No transcript, label, feature,
ledger, result, step-1 output, dashboard file or private file was opened. The writer read only the programme, the
rulings, deposits 1 and 2 (public files), the public literature digest `literature-related.md` (method cards only) and
published works on the web.

> Exploratory programme; no measure in this study can tell whether a non-human source speaks; every measure describes
> the speech in these recordings and how the creators present it.

## What the register is

One row per term or pattern that any planned step-2 list may use (and the terms considered and left out, with the
reason). For each it gives the senses, the sense the programme means, the known collisions, a disambiguation rule (or
"excluded"), the lists it sits on, dating for the layered list, trope adjacency, and its sources with what was seen.
The lists of step 2 are projections of this register, written only after its hash was recorded (`../hash-record.md`).

## Files

| File | What it holds |
|---|---|
| `register.csv` | 255 rows (217 counted, gated, flagged, frame or domain rows; 38 excluded, not listed, class or fixed-elsewhere rows), 1,192 expanded forms |
| `register-sources.csv` | the 124 sources cited, with URL and what was seen |
| `register-strata.csv` | the 16 thematic-historical layers of r3-P43's joint table, with entry dates and their sources |
| `register-gates.csv` | the 6 gate sets (co-occurrence conditions) and the list each applies in |
| `register-lists.csv` | the 15 planned lists (L01 to L15) and the entries each serves |
| `checks.txt` | the build's mechanical checks (0 problems) |
| `../code/register_terms.py`, `../code/register_sources.py`, `../code/build_register.py` | the register's source data and builder (hashed with it) |

## Columns of `register.csv`

- `term_id`; sense ids are `Txxx.sN`. `programme_sense_ids` names the sense(s) the programme means.
- `rule_kind`: `counted` (the forms count); `gated` (count only with a gate word within the window); `counted-unless-gate`
  (count unless a gate word is near: the platform sense of "this channel"); `flagged` (context-assigned: reported as a
  flag, never counted); `frame` (a pattern that removes a unit from a ratio); `domain` (link domains in page text);
  `excluded`, `not listed`, `class row`, `gate-only`, `fixed elsewhere` (considered; reason in `disambiguation_rule`).
- `lists`, `list_classes`: the lists and the class or layer on each.
- `forms_expanded`: every variant matched (alternatives and optional suffixes already expanded). `exclusion_forms`.
- `collisions`: E everyday sense; H homograph; R religious, devotional or New Age sense outside the programme's meaning;
  Y sense common in YouTube speech generally.
- `stratum_first_current`, `stratum_dating_source`, `dating_certainty`, `strand` (federation or adversarial, for
  r3-P44's decisive pair): only for L01.
- `trope_adjacent`: "yes" only where a cited reference names the term (AJC 2024); "possible" where et's condition may
  apply but no source was checked for the term.
- `shared_with`: the term sits on more than one list. `nested_in_other_lists`: one of its forms lies inside another
  list's longer form.
- `sources`, `source_check`: keys into `register-sources.csv`, and what was actually seen. Where the phrases were
  written by the writer from a class definition, `source_check` says so.
- `blind_note`: "precision decided by r3-P42's checks, not by reading" where a term's usefulness depends on what creators
  actually say.

## Matching rules (binding on every list)

- **G1 Normalisation.** Lower-case; curly apostrophes to straight; hyphens to spaces; other punctuation removed except
  apostrophes inside words, digits and the signs $ % £ €. Tokens split on white space. Domain forms are matched inside
  URLs of page text only.
- **G2 Forms.** A form is a token sequence; only the listed variants match (no stemming).
- **G3 Overlaps.** Inside one list, overlapping matches resolve to the longest form, so a token counts once per list.
  Across lists each list matches on its own, so a token may count on two lists (a shared token). r3-P41's collision
  matrix is exactly the share of each list's count carried by tokens that also sit on another list.
- **G4 Exclusions.** A match is dropped when an exclusion form of the same term covers any of its tokens.
- **G5 Gates.** A gated term counts only if a word of its gate set occurs within plus or minus the window, inside the
  same recording and the same label unit sequence. Gates apply only in their own list. **No list term serves as another
  list's sense collocate:** the build checks that no gate word is a counted form of any other list (0 violations;
  "facebook" was removed from a gate for this reason).
- **G6 Context assignment.** Where a token's list or class could be assigned only by reading its context beyond a hashed
  gate, it is flagged and never counted (programme r3-P41): "censored" between the two suppression halves; "disclosure"
  when both disclosure gates pass; "great awakening" between the spiritual and political layers.
- **G7 Cue counts.** Every count from these lists is a cue count, "sense not resolved, precision unknown", until a reader
  is funded (programme step 2). Shares are described over creators, in cells of 5 or more creators.
- **G8 Units and bases.** Three lists select units with list-level rules, which are not sense collocates: L08 counts
  resolution phrases only inside units that hold an L05 adversary or hidden-group hit (its base); L11's endorsement
  co-occurrence needs a REF-CREATOR and an ENDORSE hit of L11 in one unit; L14 codes each device hit priced when an
  L14 PRICE hit is in the same unit.
- **G9 Voice.** No list defines voice. Claimed-voice and own-voice splits come from the frozen voice labels of the
  counting step; "the first person is presented as the source's" (programme N10).
- **G10 Trope windows (et's condition).** Windows next to senses that parts of the literature document as carriers of
  the antisemitic world-conspiracy trope or the hidden-bloodline trope are never counted, totalled or shown by family in
  public in the lexicon entries. No carrier term appears in any list here; their detection list is r3-P54's, written
  only after the owner's ethics act (see decision D1).

## Lists fixed elsewhere (not changed)

Deposit 2 hashed the ledger's rule coder (`code/rule_coder.py`, SHA-256 `4fe41740...5aef71`), whose word lists were
written blind to the corpus: emic's six qualifier families (time-hedge, probability doctrine, collective-choice
conditional, outcome-booster, energetic predicate, prevention or obstruction), the energetic-predicate and date-refusal
rules, the conditional flag, et's contact class and ling's deixis typing. Ruling 11 put r3-P38 / r4-P24's lists "with
the ledger deposit if they are ready in time"; they were. They are fixed and are not rewritten here. The coder is a
private file this writer was not permitted to open, so its terms are not in this register (class rows T246 to T255);
their collisions with L06, L08 and L15 must be checked by an agent allowed to read the coder (decision D2).

## What could not be written blind

- **r3-P46's single-channel names.** Whether a name is tied to one channel is a fact about the corpus's channels. The
  literature gives only historical ties (Seth, Roberts 1972; Ra, the Law of One). Not written (decision D4).
- **r3-P40's year roles.** The passed prophesied years are the frozen ledger's (corpus-derived); control years are
  matched by rule; the contested year is a lead's ruling. Only three literature target years are listed (1844, 1954,
  1987, plus 2012 through L01).
- **r3-P51's named persons.** Persons are never listed; a pattern row (consecutive capitalised tokens) is the
  model-free proxy.
- **Layer S10a** (post-2012 non-political hopes): its best-known terms ("the Event", "solar flash", bare "the shift",
  "lightworker", "twin flame") have no findable scholarly source; only "new earth" and Cannon's "three waves of
  volunteers" are listed. Such terms are recorded as "not listed" with the reason.
- **Precision of everyday-colliding forms** (rows with a `blind_note`): kept as cues; r3-P42's precision bands decide
  whether they stay, not reading.

## Sources, briefly

124 sources are cited: 2 dictionaries (Merriam-Webster, whose First Known Use lines were read for about 50 headwords; the
Online Etymology Dictionary), scholarly histories of Spiritualism, Theosophy, New Thought, the New Age, UFO religions
and channelling (Braude 1989; Campbell 1980; Godwin 1994; Satter 1999; Albanese 2007; Sutcliffe 2003; Hanegraaff 1996;
Hammer 2001; Lewis 1995; Partridge 2004; Festinger et al. 1956; Hoopes 2011; Sitler 2006; Crockford 2021, 2022;
Berendt 2025), reference works (Gale's Encyclopedia of Occultism and Parapsychology and Encyclopedia of American
Religions; the World Religions and Spirituality Project), conspiracy scholarship (Barkun 2013; Ward and Voas 2011;
Asprem and Dyrendal 2015; Byford 2011; Amarasingam and Argentino 2020; Parmigiani 2021), linguistics (Biber et al.
1999; Quirk et al. 1985; LIWC2015; Rehbein and Ruppenhofer 2022; Petryk 2016, 2019; Wooffitt 2001, 2006), commerce and
persuasion (Carrette and King 2005; Lau 2000; Bowman 1999; Heelas 2008; York 2001; Cialdini 1984, 2021; Mathur et al.
2019) and platforms (Hua et al. 2022; Ballard et al. 2022; Rogers 2020; Savolainen 2022; Are 2022; Steen et al. 2023),
plus primary works where a term's first use is the evidence (Atkinson 1906; King 1934; Van Tassel 1952; Roberts 1972;
Sitchin 1976; Montgomery 1979; the Law of One sessions; Cannon 2011). Tertiary pages (three Wikipedia articles), one
fact-check and one advocacy glossary (AJC 2024, used only to flag trope adjacency) are marked as such. Nothing was
invented; where a source could not be found, the register says "not listed" or "no source found".

## Decisions for the lead

- **D1 (trope windows).** et's condition needs r3-P54's carrier list to exclude windows, and that list waits for the
  owner's ethics act. Until then, L05 and the entries that read it (r3-P48, r3-P49, r3-P50, r4-P18, r4-P27's adversarial
  pair, r4-P28, r4-P29's base) cannot apply the exclusion. Options: hold those counts; or run them with every term
  marked "yes" or "possible" set aside and the caption saying so (the window exclusion still missing).
- **D2 (frozen coder).** An agent allowed to read `rule_coder.py` should list its terms' collisions with L06, L08 and
  L15 as a dated addendum to this register (the register itself is not edited).
- **D3 ("never on one list").** The programme keeps evacuation lore "never on one list with rapture lore". Here both sit
  in L01's joint table but in separate layers (S06 and S01). If the lead reads "list" literally, S01 moves to its own
  file before deposit.
- **D4 (single-channel names).** Whether a private list of historically documented single-channel names is wanted.
- **D5 (balances and contested columns).** The programme says two shared balances of r3-P43 are hashed and a third is
  disputed, and that the stacked columns show "contested and imported columns apart"; neither the balances nor the
  members' contested set is in any public file. Here "imported" is S12 (programme section 5) and "contested" is read as
  `dating_certainty` = uncertain; the lead should supply or confirm both.
- **D6 (being names in public).** The project's registry text names no being. These lists publish open and
  franchise-like source names from the literature (Ashtar, Sananda, Saint Germain and others). The lead decides
  whether L01 S14, L04 and the named rows of L01 are published in full or deposited by hash only.
