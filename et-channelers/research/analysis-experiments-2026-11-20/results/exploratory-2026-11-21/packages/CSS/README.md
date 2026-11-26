# Package CSS: source typology, economy typology and conspirituality census (seen creators)

Exploratory (registry A2); not a test of H1-H10. Exploratory reporting plan, section 6.11 (the paper review's "later"
list): CSS-5, CSS-10 and CSS-12. Second wave of the exploratory round (lead's decision D4, 2026-11-22). Seen creators
only; no hold-out or other-group contact; no model call. Every choice is "added after the exploratory reporting plan"
(plan status L). The choices of method were fixed in `code/prespec.json` before the package's first analysis run. The
lines below name every choice made after counts were seen. Each was made for privacy only, or to correct a
denominator, and none chooses an estimate.

Labels are model-coded and not checked by a person. Agreement between models is agreement, not a measure of correctness. Pattern and
word-list counts are cue counts. Every table describes the creators as distributions: no creator, title, name of a
creator, quotation or per-creator row appears, and no type label of a single creator is printed. The tables describe
what recordings and pages say. They do not judge the beliefs or practices of the people who make them.

Intervals: 90% creator-bootstrap percentile intervals (2,000 draws) unless a column says otherwise. Shares of creators
in `css10-offer-classes.csv` would carry Wilson 95% intervals, as the review asks; under the lead's decision D50 they
are not printed (see CSS-10). The co-occurrence band is the 5th to 95th
percentile of 999 shuffles (90%). Interval levels differ between packages of this round (lead's decision D18).

## Small cells and the second run

No cell, bin or statistic rests on 1 to 4 creators. Categories are pooled and bins merged by the plan's rule (section
3). A creator count 1 to 4 away from a nested group reads against that group: "all but fewer than 5 of N (that group)"
or "N (that group) and fewer than 5 more". This applies to groups printed here or by another package, and also to groups
that printed counts give by union or difference. A row that differs from a printed row of the same quantity in fewer
than 5 creators is not printed (addendum 2, item 9). This also covers two printed rows of disjoint creators joined, and
rows of LAB-T, LAB-A, PT, the PT gallery and E11. A partition whose total is printed is printed whole or merged, never
with one member left out.

The package was run twice. The first run (2026-11-22, 02:56 UTC) was read by two verifiers. The second run (03:46 UTC)
corrects what they found. Its outputs replace the first run's outputs, which were never released:

- Groups that printed counts give are now checked as printed counts. These are unions of the cells of a printed
  partition, the 71 seen creators or the page-metadata base less a printed group, and a row's base less its creators
  with a value of zero. A closure audit checks every count printed here against all of them, and finds nothing. The
  check also covers package E's groups, HOLD2's seen NAMES-H family counts and the gallery's PT ask-habit bins.
- CSS-5: the 'other families' group and its co-occurrence rows are withheld. With the profile counts they would give
  cells of the three-group overlap that rest on fewer than 5 creators. In the title method, the extraterrestrial
  federations row and the star-peoples row are printed as one row, because one of them lay within 1 to 4 creators of
  the star group. Three talk-mention rows now read against HOLD2's family counts.
- CSS-12: one class's profile rows had been printed with one member left out beside the census total. That class is
  now printed at a joined profile level, and every class is printed with all its profile rows or none.
- CSS-10: each kind of evidence now has its own denominator for the share of recordings. The spoken share is over
  transcribed recordings, and the written share is over recordings with page text. The first run divided every kind
  by their union.

## Deviations: the rerun of record (lead's decision D35, 2026-11-22)

The package was rerun from its source files on 2026-11-22, 05:10 to 05:13 UTC, with its compiled cache rebuilt (the
cache of the analysis module dated from an import made while the module was still being edited, before the first run).
All four steps ran again, seen creators only, one process at a time, with the same code except one change: the read of
TABLE's recordings file now tests the group column before a row is built (lead's decision D31). That change keeps the
same rows, and the step's inputs to the analysis came out identical.

The public files were compared with those of the second run (03:46 UTC) byte for byte. They are not identical, so the
rerun is now the run of record:

- every CSV differs in its "Made <UTC>" line, which holds the run's time;
- with that line masked, seven CSVs are identical and one differs in two numbers, both lower ends of 90% intervals in
  `css5-claimed-voice-by-source-group.csv`, pooled row (angelic or devotional figures and no star people; both kinds):
  - middle model, middle-model subset: 0.063 [0.024, 0.108] became 0.063 [0.025, 0.108];
  - small model, all seen recordings: 0.060 [0.034, 0.094] became 0.060 [0.031, 0.094];
- the six figures are byte-identical, and this README was not touched by the run.

Cause: a pooled row is the sum of its members' per-creator shares, and the order of creators in that sum follows the
process's string hashing, which changes from run to run. The seeded bootstrap draws then fall on the creators in another
order, so the interval ends of these two rows can move in the third decimal at each run. No point value, count or other
cell changed, and the compiled cache played no part.

Fix (release fix pass, 2026-11-22, 05:56 UTC): the pooled row's creators are now put in sorted order before the bootstrap,
like every other row's, so its interval ends no longer depend on the process. Only the analysis step ran again, twice,
in two processes, with identical outputs; the extract and the pass of the rerun above were kept. Against that rerun one
number changed, and these are the final values of record:

- middle model, middle-model subset: 0.063 [0.025, 0.108] became 0.063 [0.024, 0.108];
- small model, all seen recordings: 0.060 [0.031, 0.094], unchanged.

No other cell, count or figure changed.

### Deviation notes (release pass 2, 2026-11-25)

- **Deterministic ordering, chosen after a result (reproducibility only).** The pooled rows' creators are put in sorted
  order (sorted keys) before the bootstrap, in the release fix pass of 2026-11-22 (05:56 UTC). Before it, their order
  followed the process's string hashing, so their interval ends moved from run to run.
- **Changed interval ends** (`css5-claimed-voice-by-source-group.csv`, pooled row: angelic or devotional figures and
  no star people; both kinds). Against the second run (03:46 UTC):
  - middle model, middle-model subset: 0.063 [0.024, 0.108], then 0.063 [0.025, 0.108] in the D35 rerun, and
    0.063 [0.024, 0.108] in the final run of record;
  - small model, all seen recordings: 0.060 [0.034, 0.094], then 0.060 [0.031, 0.094] in the D35 rerun and in the
    final run of record.
  No point value or count changed.
- **CSS-10's page-text base (lead's decision D50, option A; added after the exploratory reporting plan, for privacy
  only).** The analysis step ran again on 2026-11-25 from the patched code, with the extract and the transcript pass
  kept. Only the two CSS-10 files changed; every CSS-5 and CSS-12 file is identical apart from its run stamp. See
  CSS-10 below.

## CSS-5: which kinds of source are claimed (place S)

Files: `css5-source-types.csv`, `css5-claimed-voice-by-source-group.csv`, `css5-repertoire.csv`,
`css5-profiles-and-cooccurrence.csv`, `fig-css5-source-types.png`, `fig-css5-repertoire.png`.

- Four methods, one row per source type:
  - titles: a title presented as carrying a source's words names the source. This is the claim method, model-coded,
    and primary.
  - recording edges: name forms of the family table in the first or last running words. This counts mentions.
  - the NE pilot windows: a named source speaking or relayed, in 200 windows only.
  - talk mentions: NAMES families.

  Types follow the review's typology as far as the family codes allow. An individual extraterrestrial cannot be told
  from a people, and higher self shares a code with God and Source.
- The NE full pass (NE-F) was not run (model calls; no money left under the hard stop), so no speech-based source label
  exists beyond the pilot windows.
- Table 5b (H1, H4, H5 and H6 by source type) is not built. Those estimators are registered for the hold-out test, with
  12 or more eligible creators each. A split of the seen creators by source type is not among their registered
  analyses, and no eligibility count per source type was made.
- The type-by-type heat map (review figure 5b) is not released, because a pair of title rows rests on 1 to 4 creators
  in the cell or in its difference from a type row. The package releases two things instead:
  - the creators' source profiles, by E11's lineage rule.
  - the star and angelic groups, which are unions of profiles, with their co-occurrence against 999 shuffles.
- Verification: the title codes are those of LAB-T. Source family passed its gate on G and failed on the hold-out
  reliability sample on its lower bound; the codes are kept as records by the owner's decision. Two-model agreement per
  type is printed where the agreement rule of registry 2026-11-21 22:33 allows. Not checked by a person.

## CSS-10: economy of the practice (place S)

Page-text base (lead's decision D50, option A; release pass 2, 2026-11-25; added after the exploratory reporting plan,
for privacy only). The base is not printed. Every count table of `css10-economy-types.csv` adds up to the 71 seen
creators through a labelled row "other or no page text": the seen creators without page text (fewer than 5) are
pooled with the smallest type, with the smallest subscriber band and, in the type-by-band table, with the cell where
that type meets the merged band that holds that band, so that the three tables agree. `css10-offer-classes.csv`
prints neither the counts nor the Wilson shares of creators that rest on the base: a share over the base, read with
its printed range, would give the base back. The shares of recordings are printed as before. The package figure of
the shares of creators (`fig-css10-offer-classes.png`) is no longer written.

Files: `css10-offer-classes.csv`, `css10-economy-types.csv`.

- Offer classes come from two kinds of evidence:
  - spoken asks: model-coded, from the asks instrument's K1 objects, K2 and K5.
  - page text: PT's cue families and link classes (cue counts), and PT's written asks (model-coded).

  A creator offers a class when it is found in 2 or more recordings. Membership communities are spoken only, because
  the page cues do not separate them. The page payment cue, counted as donations, also catches channel memberships.
- Base: the seen creators with page metadata. Fewer than 5 seen creators have none. Its size is not printed here (D50,
  above); the files print it as "all but fewer than 5 of 71".
- Economy types: client offers are sessions or readings; audience offers are courses or events, membership and
  products.
  - The 'client offers only' type held fewer than 5 creators and was joined to 'client and audience offers'. Pooled
    into 'other', it would follow by difference from the printed sessions row. This was chosen after the counts were
    seen, for privacy only.
  - 'Donations only' and 'no offer found' are pooled with 'audience offers only' by the plan's rule.
- Type by subscriber band is printed with the bands merged until every cell holds 5 or more creators; the creators
  without page text sit in the pooled cell (D50). Type by source
  profile is not released: the profiles are printed over the 71 seen creators, and this base is smaller by fewer than 5.
- Written against spoken asks per class (review figure 10b) is carried by PT-cd (package CROSS) and not repeated.
- A description of what pages and asks offer, not of income.

## CSS-12: conspirituality census (place S; the directive part not run)

Files: `css12-census.csv`, `css12-by-source-profile.csv`, `fig-css12-census.png`, `fig-css12-by-voice.png`,
`fig-css12-by-source-profile.png`.

- The census counts four kinds of vocabulary:
  - secret-control vocabulary and consciousness-shift vocabulary, from E11's two closed lists. Package E wrote the
    lists before any E11 count. These are cue counts, with no precision check.
  - both lists in one recording, which is the pairing that "conspirituality" names.
  - RX's numbered dimensions or densities (H3), a cue count.

  The base is whole recordings of the English-only recognizer model. E11's own contrast counted only the body of each
  recording, so its shares differ from these.
- By voice, the middle-model subset is primary (registry 2026-11-21 02:53), and the small model on all recordings is
  shown beside it. The voice labels are verified as in LAB-V: by a third model of the same vendor, a reader of another
  vendor and known-answer texts. They are not checked by a person.
- By source profile, each class is printed at the first level of a fixed ladder at which all its rows can be printed:
  the five profiles, then the angelic or devotional profile joined with 'both', then any family against none. A class
  that fits no level is not printed by profile. Figure 12a draws the printed rows only.
- The directive part (health, money and preparedness directives) is not run: DIR's go rule failed on prefilter recall.
- Vocabulary is counted, not belief, intent or harm.

## Quantiles over a withheld base (release pass 2's fourth fix step, 2026-11-26)

Under the lead's decision D67, no quantile is printed in a row whose creator count is withheld or printed as a band ("all but fewer than 5 of 71", "withheld (within 4 of another printed count)"): a quantile of creator values sits on a position of the sorted values, and that position can give the withheld count back. Such rows print their means and intervals only. File: css10-offer-classes.csv, whose rows all rest on the withheld page-text base (its quantiles cells read 'not printed'). Edited on 2026-11-26 in release pass 2's fourth fix step (fix5, f71_d67_quantiles.py, SHA-256 d1242dd9f19465a7f4ee24f76ae5fbe88475b752b354f0044dc963d2487c86fa); no other value changed.

## Quantiles that could narrow a withheld count (release pass 2's fifth fix step (fix6), 2026-11-26)

Under the lead's decision D70, which extends D67, no quantile is printed in a row whose count of creators with a non-zero value is withheld or printed as a band, nor in a row where the quantiles alone could narrow such a count (to fewer than 5, to within 4 of the row's base or to within 4 of another printed count): quantiles were dropped where they could narrow a withheld count. Such rows print their means and intervals only. Files: css12-census.csv, css12-by-source-profile.csv and css5-claimed-voice-by-source-group.csv (their 'quantiles' cells read 'not printed (lead's decision D70)'). Edited on 2026-11-26 in release pass 2's fifth fix step (fix6, f91_d70_quantiles.py, SHA-256 1a03a8648a6fc3ce380ec018255a5e4e7a60d3b4134c579c8f5a20ae289eb418); no other value changed.

## Figures in the release

The PNG files named in this README are the package's own drawings, which a release does not copy (D56). Every output of the package is drawn in the release gallery (`gallery/index.html`; records in `gallery/manifest.json`), under these figure ids: CSS-10: CSS-10-fig-1, CSS-10-fig-2; CSS-12: CSS-12-fig-1, CSS-12-fig-2, CSS-12-fig-3; CSS-5: CSS-5-fig-1, CSS-5-fig-2, CSS-5-fig-3, CSS-5-fig-4, CSS-5-fig-5. Edited on 2026-11-26 in release pass 2's fix step (fix2, f01_edits.py; its SHA-256 is in the round's records), for privacy and consistency only.
