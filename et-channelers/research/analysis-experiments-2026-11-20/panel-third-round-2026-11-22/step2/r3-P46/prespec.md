# Step 2, lexicon descriptions r3-P43 / r4-P26, r3-P44 / r4-P27, r3-P45 and r3-P46: prespecification

Written 2026-11-26 from 12:43:04Z (UTC, from `date -u`) by the step-2 description agent for these four entries (a model
agent working for the project lead; not a person), **before any count of these entries**. It fixes every choice that the
programme (`programme.md`, step 2), deposit 3 (merged 2026-11-26T11:14:53Z; read from `origin/main`, 88 of 88 hashes
matched) and the lead's decisions 51 to 66 leave open. It is hashed before the first count and not changed afterwards;
any later change is a dated departure in the entry's README. One file serves the four entries; a byte-identical copy
sits in each entry folder.

Exploratory; not a test of H1-H10. Every count is a cue count, "sense not resolved, precision unknown", until a reader
is funded. Voice labels are model-coded and not checked by a person; comparisons between instruments are agreement,
never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**What the writer had read before writing this file.** Deposit 3, the programme, the lead's rulings and step-2
decisions, deposit 2's margins, r3-P30's interval-choice table, step 1's privacy decisions 49 to 64, and r3-P42's README,
run record and public files: r3-P42 ran the checks of section 5 of its prespecification on the same lists and creators,
so its published values (the composition test, the balances, the survival strip's rho, the layer pairs, L03 and L04)
were known. The writer also read the shape of the voice sides in r3-P42's private extract (how many recordings of each
voice-eligible creator hold both voice sides, and their sizes; no list was counted), which fixed the side minimum of
2.7(b). No other value of these entries was seen.

## 1. Inputs and shared rules (all four entries)

- **Units.** Tier L: the 23 non-development seen creators of deposit 2's split, all their seen recordings, run once with
  no split (decision 65 item 1). Voice statistics use the 11 voice-eligible creators of r3-P42's run record (at least
  1,000 tokens on each voice side under the frozen primary voice definition).
- **Text and matching.** r3-P42's private extract (SHA-256 `8101aba5...1a8215`) and counts (`1cd15e57...f007e`); no
  transcript is re-read. New counts are made by matching the extract's token sequences with the shared matcher
  `step2/common/lexmatch.py` (SHA-256 `2297864c...28d28`, which checks deposit 3's hashes), every speech list at once
  (so that G5b masks are as in r3-P42), keeping L01's hits.
- **r3-P42's code** (`analyse_p42.py`, SHA-256 `e6d370d8...7ee30f`; `p42common.py` `ae6b91c0...d9d6`) is imported
  unchanged for the quantities r3-P42 already computed (the composition test, balances, survival strip, layer pairs,
  matched placebos and pseudo-strata). Recomputed values must equal r3-P42's printed values at their printed precision;
  a difference is reported as a departure and r3-P42's published value stands.
- **Lists.** The binding version of each list (a2d, then a2c, a2b, a2, original); the set-asides of decisions 51 L1, 57
  and 60 together. Classes or columns emptied by the trope set-aside (L01 S12; S15; L02 P000) print "not computed until
  r3-P54 (waits for the owner's ethics act)". No residual is built after the fact.
- **Thin rule** (addendum 2d; decision 65 item 3). "Term" means a register row for L01's layers, the composition parts,
  the beside columns of 2.3, et's groups, balance sides and L02's pairs, and an expanded form for L03's and L04's
  classes. A class, part, column, group or side with fewer than 3 terms used by 5 or more of the 23 creators prints
  "not computed (too few terms or creators)". A statistic whose eligible creators number fewer than 5 prints the same.
  Where r3-P42 counted L04's terms as rows, the row reading is printed beside (the literal reading).
- **Margins and readings** (deposit 2): log ratio 0.223 (ratios outside 0.80 to 1.25), share difference 0.05,
  correlation 0.10. Reading A: the interval wholly beyond the margin in the named direction under every admissible
  reference; reading B: the reference-adjusted interval wholly inside the margin; otherwise undetermined. Where no
  direction was named in advance, an interval wholly beyond the margin reads "A (direction not named in advance:
  <side>)", a description. The admissible reference of a lexicon contrast is the matched placebo of r3-P42 (C1).
- **Intervals.** 90%. Where a design class of r3-P30 applies, the method r3-P30's table chooses at the eligible count
  (step 1's `pubrules.choice` and `pubrules.interval`, r3-P01's copy, SHA-256 `24149975...255c`); a class whose method
  does not hold at that count caps the reading at "undetermined". Otherwise the fixed methods named below (placebo,
  pseudo-strata, date-permutation and curveball bands; creator bootstrap). Every interval row prints its method.
- **C5 (two-author test).** Not run in this step (decision 65 item 2). For r3-P43 it would read agreement only; r3-P45
  must carry it. It prints "not computed in this step (decision 65 item 2)".
- **Multiplicity.** No family-wise adjustment beyond the Holm adjustment within each balance family. Each README prints
  deposit 2's half-effect disclosure (56 primaries; about 2.8 readings A expected by chance).
- **Seeds.** A new check's seed is the first 8 hex digits of `SHA-256("<entry>|<check>|step-2")`, read as an integer;
  streams are `numpy.random.default_rng([seed, k])` with k named below. r3-P42's own draws keep r3-P42's seeds.

## 2. r3-P43 / r4-P26: co-presence of historically dated vocabularies, by voice

Wording: "draws on vocabulary first current in period X", never descent; "imported" never judges sincerity.

2.1 **Shared primary: the composition test** (decision 54 item 4; decision 57 item 5): creator-level PERMANOVA on
Aitchison distance over the 12 occult parts R1, RNT, R2 to R9, R10a, R11, as r3-P42 ran it (CSS-5's ladder; labels
permuted within quintile blocks of total tokens, 1,999; placebo and pseudo-strata bands, 200 each), with its sensitivity
rows: New Thought beside (et's placement, decision 54 item 4), zero replacement 0.1, thin parts dropped, grades A and B
only (A5), without coder-shared forms (A1), with name variants (A6). Recomputed with r3-P42's functions (section 1).
Reading: outside both bands, "stratigraphic structure beyond placebos"; otherwise "no stratigraphic structure beyond
placebos".

2.2 **Balances.** Two named families (occult B1 to B3, et B1 to B3; `r3-P43-balances-a2d.csv`), Holm within each over
its three primary tests, directions from `r3-P48-predictions.md`; profile tests by 1,999 label permutations, voice tests
by 1,999 within-creator sign flips; thin sides "not computed (too few terms or creators)"; profile tests need 5 or more
creators in each title-profile group. Recomputed with r3-P42's functions.

2.3 **Creator-balanced stacked columns** (description). Value: the creator-balanced rate per 10,000 tokens (the mean over
a column's creators of each creator's rate) of each segment. Three columns: all speech (the 23 creators), claimed voice
and own voice (the 11 voice-eligible creators). Segments:
- each composition part that passes the thin rule (rows used by 5 or more of the 23 creators, all speech), by occult code
  (r3-P42's `part_of`: T084 to R11 only in its government, official or uap forms; T090 to R6 only in its "probable" forms);
- one segment "thin composition parts, pooled" holding every thin part, printed only if the pool itself passes the thin
  rule, otherwise "not computed (too few terms or creators)";
- **beside the composition, never inside** (separate columns of the figure, decision 54 item 5): (i) end-time vocabulary,
  every counted row of the S01 file; (ii) devotional names, S14; (iii) et's baseline R0 (rows whose `memo_code_et` is R0
  and `memo_column` is "beside": chakra, karma, vibration); (iv) the imported column F1, post-2016 political fusion (the
  counted S10b rows); (v) the contested column: every other counted L01 row whose `memo_column` is "apart" or "beside
  (contested column ...)", or whose form falls outside a composition part (T084's other forms, T090's other forms). F2
  (S12) and the adversarial rows of S15 print "not computed until r3-P54 (waits for the owner's ethics act)". New
  Thought (RNT) stays inside the composition, with et's placement as the sensitivity row of 2.1.
- Each beside column passes the thin rule on its own or prints "not computed (too few terms or creators)".
- A segment value is printed only if 5 or more creators of that column carry it (a non-zero count); otherwise "not
  printed (fewer than 5 creators carry it)".

2.4 **et's seven groups** (exploratory display only, decision 57 item 5). Creator-balanced rates (all speech, 23
creators) of G1 to G7 from the crosswalk's `memo_group_et`: a row joins a group when that field's leading token is the
group code and it carries no "(register" and no "row" qualifier; T054 joins G3; T084's R11 forms join G7; T090's
"probable" forms join G2; set-aside rows are out. Thin rule per group. No test.

2.5 **Survival strip.** Each dated layer S01 to S13 except S12 (imported, kept apart) and S14 (undated); S15 waits for
r3-P54. Entry year: the first four-digit year of `register-strata.csv`'s entry date. A layer enters only if it passes
the thin rule ("not computed (too few terms or creators)" otherwise, marked at its year on the figure). For an entered
layer: the share of the 23 creators using it (one or more counted hits), **printed as a band of the 23**: fewer than 5;
5 to 9; 10 to 14; 15 or more (one count form for every layer); beside it the central 90% of the same share over the 200
matched placebo sets (r3-P42's L01 draws). Spearman rho of entry year against the share, with the date-permutation and
placebo bands, recomputed with r3-P42's function; reading "dated order" only outside both.

2.6 **The claimed-minus-own composition over creators.** On the 11 voice-eligible creators. Parts: every composition
part that passes the thin rule, and one pooled part of every thin composition part. For each creator, clr coordinates of
the claimed-voice and of the own-voice part counts (zero counts replaced by 0.5, r3-P42's `clr`), and their difference.
Statistic per part: the mean of the difference over the 11. Interval: r3-P30's nearest design class, H (log rate ratio
of rare counts with 0.5 added, counts summed within creator), at 11 creators. Reference: for each of r3-P42's 200 L01
placebo draws, the same difference with every composition row replaced by its matched placebo; each creator's
reference-adjusted value is its difference minus its mean over the draws; same interval. Reading as in section 1
(margin 0.223), against the raw and the adjusted intervals. A part's row prints only if 5 or more of the 11 carry it
(a non-zero count on either side). Sensitivity rows: grades A and B only (A5; a changed reading reads "undetermined
(grade)"), without coder-shared forms (A1; a changed reading reads "not separable from the ledger's coded families"),
and leave one row out (C2; any row whose removal changes the reading makes it "undetermined (term-dependent)").

2.7 **r4-P26.**
- (a) **Creator-level co-presence** (N25's "placebo-controlled count of the co-presence"): the mean over the 23
  creators of the number of the 12 composition parts each creator uses (one or more counted hits). Bands: placebo (every
  composition row replaced by its matched placebo, r3-P42's 200 L01 draws) and pseudo-strata (the rows' part labels
  permuted, part sizes kept, 200 draws; stream `[seed("r3-P43|co-presence-pseudo|step-2"), 1]`). Reading: outside both
  bands on the same side, "more (or fewer) dated layers co-present than matched placebos"; otherwise "no excess
  co-presence over placebos". Sensitivity row: the computed parts only.
- (b) **Recording-level contrast** (N25's "claimed-voice recordings against the same creators' own-voice talks"): every
  recording of the 11 voice-eligible creators that holds at least 300 tokens on each voice side (the minimum at which
  every one of the 11 keeps a recording; fixed from the voice structure only). Per recording: log((c + 0.5) / Tc) minus
  log((o + 0.5) / To), with c and o the counted composition hits (all 12 parts) on the claimed and own sides and Tc, To
  their tokens. Creator value: the mean over its recordings. Interval: r3-P30's class A (log ratio of a rate between two
  parts of a recording; creator means of recordings) at 11 creators, with the recordings' values as the within-creator
  values. Reference: the same statistic for each draw's matched placebo n-grams of the composition rows, counted in the
  same recording sides; the recording's adjusted value is its value minus its mean over the 200 draws. Reading as in
  section 1 (margin 0.223). Sensitivity rows: A5, A1 and C2 as in 2.6.

2.8 **Predictions scored as stated** (`r3-P48-predictions.md`; the balance file):
- occult B1 (title direction), occult B2 (title direction), occult B3 (lower in the claimed voice), et B1, et B2, et B3:
  each scored on its own test if computed: "met" (the test's Holm-adjusted p at or under 0.10 in the stated direction),
  "not met", or the test's not-computed status.
- occult's F columns by voice ("F1 is denser in the own voice than in the claimed voice"): the F1 column's voice log rate
  ratio (creator-balanced, 11 voice-eligible creators, r3-P42's statistic) against its placebo band: "met" if below the
  band and beyond -0.223, "not met" otherwise, or not computed if F1 is thin. F2 waits for r3-P54.
- et's "what would change my mind": (i) "if no balance leaves den-meth's placebo band": scored on et's balances (not
  computed if all three are thin); (ii) "if R4 is sizeable for most creators": R4's status, and if computed whether 12 or
  more of the 23 creators use it (banded print); (iii) "if R11 occurs in fewer than 5 creators": printed as "fewer than 5
  of the 23 creators" or "5 or more of the 23 creators"; (iv) grades A and B: A5.

## 3. r3-P44 / r4-P27: co-use of strata, and the fusion thesis against a fixed-margin null

3.1 **Primary** (prespec section 5, L02): creator-level co-use of each pair of L01 layers against the curveball null
blocked by audience band (row and column margins kept within blocks; 200 draws) and against matched placebos; structure
only outside both on the same side. Recomputed with r3-P42's `pairs()`; printed as the distance from the null mean in
null standard deviations (z), never the co-use count.

3.2 **By stratum** (den-soc's audience-capture reading, N26): audience band (under 10,000; 10,000 or more) and economy
type (client offers in 2 or more recordings; none). Within a stratum: the incidence of the computed layers among its
creators; a curveball null within the stratum (one block, margins kept; r3-P42's `curveball` with 100 x n burn-in and
10 x n trades between 200 samples; stream `[seed("r3-P44|stratum-curveball|step-2"), s]`, s = 1 to 4 in the order
above); the placebo band from r3-P42's L01 matched placebos within the stratum. Same reading rule. A stratum is computed
only if it holds 5 or more creators. Stratum sizes, co-use counts and stratum means are never printed.

3.3 **The decisive pair P000** (federation against adversarial strand) and r4-P27's fusion test: "not computed until
r3-P54 (waits for the owner's ethics act)". The registered predictions (et: at or below chance; occult and emic: at or
above chance in the 2020s) are marked on the figure and scored "not scored: not computed until r3-P54". **P001**
(L05 against L06): its status from the thin rule. r4-P27's other carriers (r3-P48, r3-P49) report in their own entries.

3.4 **Figure**: a heat map of z for every computed layer pair, one panel for all creators and one per stratum, the
decisive pair outlined as its own cell with both predictions marked.

## 4. r3-P45: density or dimension, a title-free lineage marker

4.1 **Primary**: the per-creator density-scale share DEN / (DEN + DIM), a histogram over creators with its permutation
band (shuffled density and dimension labels, 200). If DEN has no counted term after the set-asides, the primary prints
"not computed (no counted density term after the set-asides of addendum 2c)", and the histogram is not drawn.
4.2 C5 is required for r3-P45 and is not run in this step: any reading would be "undetermined (author-dependent)" until
it runs.
4.3 Beside it, no new count: DIM's checks as r3-P42 computed them (voice contrast, concentration, single-form share),
recomputed with r3-P42's functions and labelled as carried.

## 5. r3-P46: source names as title templates, and classes of name

5.1 **Classes** OPEN and FRANCHISE (L04, titles of the 23 creators' recordings): the thin rule on expanded forms used in
titles by 5 or more creators (addendum 2d), with r3-P42's row count beside. Names are printed only from the list and
only if 5 or more creators' titles use them. UNNAMED (a P1 title naming no OPEN or FRANCHISE name) with its size.
5.2 **Template recordings**: a recording whose page title holds a counted L04 name form (either class; the matcher's
`match_title`). **Template status** of a creator: "template" if 2 or more of its titles hold one, otherwise "no
template". Computed only if the pooled L04 forms used in titles by 5 or more creators number 3 or more (the thin rule on
the pool); otherwise "not computed (too few terms or creators)". Creator counts by status are printed exactly if each is
5 or more and neither is nested within 1 to 4 of a registered printed group (step 1's `pubrules.known_register()`, the
23 and the 11); otherwise as "fewer than 5 of the 23 creators" and "all but fewer than 5 of the 23 creators".
5.3 **MTMM's source-family cells** on tier L: the four source-family measures of CROSS's `mtmm.py` (small, middle and
page read titles; rule reads transcripts), rebuilt with its definitions for the 23 creators: (a) all recordings; (b)
without template recordings (their titles and their transcripts dropped). For each of the six method pairs, Spearman rho
over the creators with both measures (5 or more, else not computed); 90% creator-bootstrap percentile interval, 2,000
draws, stream `[seed("r3-P46|mtmm-bootstrap|step-2"), 1]` (a fixed method: r3-P30 holds no class for a correlation
across creators, as r3-P26 found); the difference (b) minus (a) with the same resampled creators. Reading of the
difference against the correlation margin 0.10: B if its interval lies wholly within -0.10 to 0.10; A if wholly below
-0.10 (the named direction: convergence lower without template recordings, "agreement partly by construction"); "A
(direction not named in advance: higher)" if wholly above 0.10; otherwise undetermined. (b) and its difference are
computed only if template status is computed (5.2); (a) is printed in any case. The number of creators per pair is not
printed (one count form: "the 23 non-development creators with both measures").

## 6. Privacy (binding: step-1 decisions 49 to 64)

No cell, bin, bar or plotted group on fewer than 5 creators; no per-creator row or point; no quantile of creator values;
no group mean beside an overall mean that would solve for group sizes (stratum and profile group sizes are never
printed, nor their means; contrasts are printed as log ratios or z only). No names, ids, titles or corpus text; terms are
named only from the deposited lists and only where 5 or more creators use them. Creator counts printed: 23 and 11 (both
already printed by deposit 2 and r3-P42), layer users only as bands of the 23 (2.5), and template-status counts by 5.2.
Every count is checked against every count printed in this release, step 1, r3-P42 and deposit 2. Decision 62: a row
whose count is banded or withheld and whose interval method is chosen by the count prints no estimate, interval or
reading; a reading resting only on such rows is withheld (decision 63). Before finishing: the identifier scan (as
r3-P42), zsolve, qscan_all2, whole_position_scan and the s1_* solvers that apply (s1_blanks with `d62`).

## 7. Outputs

Per entry folder `step2/<id>/`: `code/` (hashed in status.json), `public/` (CSV with a commented header; PNG at 200 dpi
without text chunks; PDF without document information), README.md, contacts.md, status.json, and this file.

## 8. Order

1. This file is hashed (SHA-256 and `date -u` time in `prespec-hash-record.md`).
2. The count and analysis run once (`code/analyse_p4346.py`), under `run_locked.sh`, at most 4 workers.
3. Public files, figures, privacy scans and solvers.
