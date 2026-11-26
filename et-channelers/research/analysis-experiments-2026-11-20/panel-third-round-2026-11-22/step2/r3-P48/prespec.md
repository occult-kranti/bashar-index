> Redacted copy: 1 private path replaced; the hash recorded at hashing time is kept privately.

# r3-P48 with r3-P49 / r4-P18 and r3-P50: prespecification (and the shared rules of the step-2 lexicon descriptions)

Written 2026-11-26 from 12:44:25Z (UTC, from `date -u`) by the step-2 description agent, a model agent working for the
project lead (not a person). It fixes every choice that the programme (`programme.md`, step 2), deposit 3 (read from
`origin/main`, merge bfee7c3) and the lead's decisions 51 to 66 leave open, for the entries r3-P48, r3-P49 / r4-P18,
r3-P50, r3-P51 / r4-P28, r4-P29, r3-P52 / r4-P12, r3-P53 / r4-P30, r3-P55 and r3-P56. Section 0 is shared by all seven
entry folders; each other folder's `prespec.md` cites it by this file's SHA-256. It is hashed, with the other six, before
any statistic of these entries is computed.

**What was known when this was written.** r3-P42's public files and README (published privately at 12:17Z) were read: they
say which classes of each list are thin on the 23 creators (every L05 sub-register, every L07 class, L08's two resolution
classes, L10's modes other than MODE-HIGHERSELF and MODE-RELAY, L11's REF-CREATOR, L12's IDIOM) and print r3-P42's own
checks. No statistic of these entries had been computed, r3-P42's private results file was not opened, and no count of
any list had been read beyond r3-P42's public files.

Exploratory; not a test of H1-H10. Every count is a cue count: sense not resolved, precision unknown, until a reader is
funded. Voice and asks labels are model-coded and not checked by a person; comparisons between instruments are
agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 0. Shared rules (bind all seven entry folders)

### 0.1 Units, inputs and reads

- **Creators.** The 23 non-development seen creators of deposit 2's split (tier L), all their seen recordings, run once
  with no split (decision 65 item 1).
- **Speech text and counts.** r3-P42's private extract and counts, used as they are:
  `r3-P42/private/p42-extract.private.pkl` (SHA-256 `8101aba5...1215`) and `r3-P42/private/p42-counts.private.pkl`
  (SHA-256 `1cd15e57...007e`), made with the shared matcher `common/lexmatch.py` (SHA-256 `2297864c...8d28`). r3-P42's
  analysis module `r3-P42/code/analyse_p42.py` (SHA-256 `e6d370d8...ee30f`) is imported unchanged, so that its placebo
  draws, statistics and checks are reused exactly (its hash is checked at import). No transcript is read again.
- **Re-matching on the extract** (no corpus read): where a statistic needs a per-unit or per-recording count that r3-P42's
  counts do not hold (r3-P52's per-recording first-person forms; r3-P55's ENDORSE and PRICE hits per unit; r3-P53's mode
  hits per unit; the named-person proxy T190 per position), the extract's token sequences are matched again by
  `lexmatch.Lexicon.match` (lists named per entry); totals are checked against r3-P42's counts and a mismatch stops the
  run.
- **New reads, seen only, where the extract lacks the field:**
  1. page text (title and description) of the 23 creators' seen recordings, through PT's seen-only `page_text()` (as
     r3-P42 read it), for r3-P50; only video ids of recordings in the extract are kept;
  2. the frozen asks labels, unit times, the voice map fields (claimant, format) and the middle model's voice labels,
     through the frozen analysis package's seen-only bundle (`adapter.load_seen_bundle`, by MR's `mrcommon.load_bundle`,
     as step 1's r3-P04 to r3-P06 read it), restricted to the 23 creators, for r3-P51 (middle-model row), r3-P52 (own-voice
     talks) and r3-P56 (asks and hours). A recording whose voice units do not line up with the extract's units (count of
     units) is left out of the rows that need both.
  Both are recorded in `contacts.md` as reads that are not contacts. No hold-out or other-group file is opened.
- **Voice.** The frozen primary definition (label of record, rule B, own voice broad, claimed voice V2 + V3; claimants
  sole speaker or host), as r3-P42's run record. **Voice-eligible creators**: 1,000 or more tokens on each side (r3-P42's
  rule; the same set as r3-P42's 11). Tenth of a recording: `min(9, int(10 * i / n))` for unit index i of n units (the
  frozen H6 convention, as r3-P05).

### 0.2 Lists, set-asides and the thin rule

- Lists, forms, gates and set-asides as `lexmatch` loads them (the binding "-a2d", "-a2c", "-a2b", "-a2" or original
  file; decisions 51 L1, 57 and 60). CR-A prints "not computed until r3-P54 (waits for the owner's ethics act)"; its terms
  that are not set aside never enter any set or total of these entries (no residual after the fact, decision 54 item 3).
- **Thin rule** (addendum 2d; decision 65 item 3): a class of L05 to L12 is computed only if 3 or more of its expanded
  forms are each used by 5 or more of the 23 creators (in the text the class is read on). Otherwise it prints
  **"not computed (too few terms or creators)"**. The same words print when a reading has fewer than 5 eligible creators.
  The rule is applied to every set a reading rests on: a class, and any pooled set an entry defines (applied to the pooled
  set as a whole).
- **r3-P42's thin-class statuses are recomputed** here by the same rule from the same counts; a difference stops the run.

### 0.3 Statistics, intervals and readings

- Rates per 10,000 tokens. **Creator-balanced**: the mean over creators of each creator's rate.
- **Margins** (deposit 2): ratio of rates, |log ratio| 0.223 (log 1.25); difference in shares, 0.05.
- **Where a design class of r3-P30 applies**, the 90% interval is r3-P30's choice for that class at the row's eligible
  count (the row of the largest simulated count at or below it), computed by step 1's `pubrules.interval` (SHA-256
  `24149975...255c`); where the chosen method does not hold at that count, the reading is at most "undetermined".
  Design classes used: **H** (log rate ratio of rare counts with 0.5 added, counts summed within creator) for per-creator
  voice ratios of cue counts; **B** (difference in shares, creator means) for share differences.
- **Readings** (deposit 2): **A** = the interval lies wholly beyond the margin in the deposited direction; **B** = wholly
  inside the margin; **undetermined** otherwise. Where no direction is deposited (every entry here except where stated),
  the words are "beyond the margin (<side> higher)", "within the margin (B)" or "undetermined"; the letter A is not used.
  The floor rule (the near 90% bound beyond half the margin) is implied by these words. Estimators or references that
  disagree give "undetermined".
- **Otherwise fixed methods**: r3-P42's matched-placebo band (central 90% of 200 placebo sets matched on length, frequency
  band and dispersion band, r3-P42's seeds and streams), r3-P42's pseudo-strata, a homogeneous-Poisson null and own-noise
  bands (seeds below). Words: "no excess over matched placebos" (inside), "outside the band (above)" / "(below)".
- **r3-P42's checks carried on every computed reading**: C2 (leave one term out; leave one form out for terms with 5 or
  more used forms; "undetermined (term-dependent)"), C4 (precision values 1.0, 0.5, 0.3 for E/Y-collision or blind-note
  terms; L05 by emic's ranges through `emic_C_code`), A1 (the same estimate without the forms of the public rule-coder
  collision table, for L05, L06, L07 and L08), A4 (where r3-P42 found a list's count carried above 0.20 by tokens of
  another list, here L05 and L06 with L01, the estimate is printed again without those shared hits). A reading that
  changes under C2, C4, A1 or A4 reads, in that order of precedence, "undetermined (term-dependent)", "undetermined at
  unknown precision", "not separable from the ledger's coded families", "undetermined (collision-dependent)".
- **Seeds.** Placebo draws are r3-P42's (`P.rng("C1-placebo", list)`), so that a set shared with r3-P42 gets the same
  bands. New draws use `numpy.random.default_rng([s, k])` with s = the first 8 hex digits of
  SHA-256("step2-desc|<entry>|<check>") read as an integer and k a stream number named in the code.
- **Bootstrap** (where named): creator resampling, B = 1,000, percentile, 90%.

### 0.4 Privacy (binding: the step-1 decisions 49 to 64, the brief)

- **Cells.** No cell, bin, bar or plotted group on fewer than 5 creators; no per-creator row or point. A value carried by
  (non-zero for) fewer than 5 creators of its base prints "not printed (fewer than 5 creators carry the estimate)".
- **Identifying text.** No names, ids, titles or quotations of corpus text. Terms are named only from the deposited lists,
  and only where 5 or more creators use them. The named-person proxy is printed only as an aggregate; no person is named.
- **Creator counts.** Exact where allowed. Each printed count is checked against the stored-membership register of step 1
  (`pubrules.known_register()`: the release, step 1, deposit 2 and the split), r3-P42's printed sets (the 23 and the 11
  voice-eligible creators; r3-P42's L08 base printed as "held by 5 or more creators") and every count these entries print:
  a set identical to a registered one prints in that set's form; a set nested in (or holding) a registered set with an
  exact count 1 to 4 away prints "all but fewer than 5 of N" / "N and fewer than 5 more"; a set within 1 to 4 of a
  published count whose membership cannot be checked (101, 18, 6, 36) prints as a band ("10 to 19"); otherwise exactly.
  One count form per creator set, in every file. Counts near printed counts that cannot be stated against them are banded.
- **Banded rows** (decision 62): on a row whose count is banded or withheld and whose interval method is r3-P30's choice
  at the row's count, the estimate, the interval and the reading are withheld ("not printed: the row's count is banded").
  Fixed-method rows keep the estimate and band. A reading that rests only on such rows is withheld (decision 63).
- **Other recoveries.** A group mean is printed only where the group's count is printed exactly (no group means that,
  with an overall mean, would solve for group sizes). No quantiles of creator values over a banded count. Histogram bins
  are formed by rule (fixed edges, then adjacent bins merged from the tails inward until each holds 5 or more creators);
  Lorenz ordinates are printed only at bin edges of 5 or more creators. Blank cells follow these rules only.
- **Solvers** before finishing: zsolve, qscan_all2, whole_position_scan, the s1_* solvers that apply (s1_blanks with
  `d62`), the identifier scan with the extract's audio hashes, video ids and page keys as extra needles. No banded row may
  be left with 4 or fewer values.
- **Wording.** Offers, asks, conspiracy and contested content are described neutrally, without mockery. Privacy notes are
  in general terms. "model-coded", "not checked by a person", "agreement" (never "accuracy"), "exploratory; not a test of
  H1-H10", "creators who describe their practice as X", "first-person claimed voice", "presented as the source's". Every
  output carries the agnosticism sentence.
- **Outputs.** `public/` CSVs with a commented header; PNG at 200 dpi without text chunks; PDF without document
  information; style copied unchanged from the CHANGE group's private plotting code folder; figures drawn from the public CSVs.

## 1. r3-P48: the control register v2

- **Classes.** L05's sub-registers ADV-NEG, ADV-AMB, BRIDGE, CR-B, CR-C, CR-D, CR-E: status by the thin rule. CR-A: "not
  computed until r3-P54 (waits for the owner's ethics act)".
- **For a computed class** (programme: per-sub-register rate distributions over creators by profile and voice): r3-P42's
  statistics on the class (creator-balanced rate; voice contrast on the voice-eligible creators; title-profile,
  audience and economy contrasts; phi), each against its matched-placebo band and L05's pseudo-strata band, with C2, C4
  (emic's ranges), A1 and A4. The display is dot-and-band per class (never a 100% stacked bar, never per-creator dots).
- **Prediction scorecard** (the deposited predictions, `r3-P48-predictions.md`; meas's four rules):
  1. et's A-window estimand (Mantel-Haenszel risk ratio of the share of windows holding a control term, A windows against
     F windows; smallest effect 1.5): "not computed until r3-P54 (waits for the owner's ethics act)" (decision 54 item 3;
     the valence-A family is set aside). F windows are not described alone (no residual after the fact).
  2. et's negative control (shift vocabulary in the same windows; predicted ratio near 1): the same.
  3. et's rule for telling fusion from no difference (the absolute rates of A and F windows): the same.
  4. One row per sub-register (meas's rules): (1) the creator-equal difference in rates, claimed minus own, per 10,000
     tokens, with the voice log ratio read against the margin 0.223; (2) the band is r3-P42's matched-placebo band (C1);
     (3) "for", "against" or "undetermined" by the margin under the size rule: with no direction deposited for any
     sub-register, the row prints "no direction deposited" in place of "for" or "against", and the margin words of 0.3;
     (4) whether the sign survives emic's precision ranges (C4). A row on fewer than 5 creators prints "fewer than 5
     creators"; a thin class prints "not computed (too few terms or creators)".
- occult's and et's B1 to B3 (r3-P43's balances) and occult's F columns belong to r3-P43 and are not scored here.
- **Plot**: the scorecard and the class statuses (and dot-and-band rates for any computed class).

## 2. r3-P49 / r4-P18: concentration of control talk

- **The control set (primary).** L05's counted terms after every set-aside, CR-A left out entirely (0.2), pooled; the thin
  rule is applied to the pooled set (0.2). It cannot be decomposed into sub-registers (r3-P48). **Beside it**, r3-P42's
  convention (a list's whole is the union of its computed classes): printed as its status. The lead may choose which
  binds (README "for the lead").
- **The shift set.** L06's SHIFT (r3-P42's computed class), a comparison row, never the reference.
- **Primary statistic.** phi, the creator random-intercept variance of a gamma-Poisson model by moments (r3-P42's
  `st_phi`), of the control set, read against the central 90% of phi over 200 matched placebo sets (r3-P42's L05 draws).
  Reading: "excess over matched placebos" (above the band), "no excess over matched placebos" (inside), "below matched
  placebos" (below). No design class of r3-P30 applies to a variance component; no reading A or B. C2, C4 (emic's
  ranges), A1 (without coder-shared forms, placebos re-matched by r3-P42's `a1_check` rule), A4 (without hits on L01's
  counted tokens) as in 0.3. The shift set gets the same rows.
- **Lorenz curves (display).** Creators ordered by their rate of the set (ties broken by r3-P42's creator order); bins of
  5, 6, 6 and 6 creators from the lowest rate up (23 = 5 + 6 + 6 + 6, fixed by rule); the ordinate at each bin edge is
  the cumulative share of the sum of creator rates. Bands at each edge: (a) the matched-placebo band (central 90% of the
  200 placebo sets' ordinates); (b) a homogeneous-Poisson null (each creator's count drawn as Poisson(tokens x pooled
  rate), 200 draws, stream ("r3-P49", "poisson-null"), k = 1 control, 2 shift). Curves for control, shift and placebo
  (the placebo sets' median ordinate) terms. A set carried by fewer than 5 creators is not drawn.
- **The crossed outcome table (r3-P49 with r3-P50, hashed now).** Rows: the control set, the shift set, L12's DISSEM and
  IDIOM, L13's suppression halves; columns: status, phi reading (r3-P49), page-over-speech reading overall and by control
  tercile (r3-P50). Cells follow sections 2 and 3.

## 3. r3-P50 / r4-P18: page text against speech (placement, never routing)

- **Page text.** Per recording of the extract with page text: the title and the description, each normalised by
  `lexmatch.normalise` and matched as its own token sequence by `Lexicon.match` (lists L05, L06, L12, L13; the T190 proxy
  masks placebo candidates as in speech). Page tokens per creator: the sum over the creator's pages.
- **Sets.** The control set (as r3-P49's primary), L06 SHIFT, L12 DISSEM and IDIOM, L13 SUPP-PLATFORM and SUPP-HIDDEN
  (each by the thin rule on speech, as r3-P42). L13's link classes: "not applicable (links occur on the page only; speech
  cannot be clicked)".
- **Statistic.** Over the 23 creators, LR = log(mean page rate / mean speech rate), creator-balanced. **Placebo
  adjustment**: the same LR for each of r3-P42's 200 matched placebo sets of that list (their page counts from page n-grams
  outside every list form, numeral and T190 span, as in speech); the estimate is LR minus the median placebo LR; its band
  is the central 90% of LR minus each placebo LR. A side (page or speech) carried by fewer than 5 creators prints "not
  printed (fewer than 5 creators carry the estimate)".
- **Readings** (margin 0.223, the equivalence band shaded): "page denser than speech" (the band wholly above +0.223; the
  third direction registered by N17), "speech denser than page" (wholly below -0.223), "within the margin (B)" (wholly
  inside), else "undetermined". No direction is deposited, so no letter A.
- **Commerce placebos are link-bound** (L12 only, a sensitivity row): placebo phrases drawn from page n-grams of
  description lines that hold a link, with at least one word outside H9's function-word list, matched to each real term on
  length, page frequency decile and page dispersion band (creators), 200 draws (stream ("r3-P50", "link-bound"), k = 12).
  If the primary and this row give different readings: "undetermined (placebo-dependent)". Titles' word-class matching is
  not built separately (titles are inside the page text of both real and placebo counts); this is a departure stated in the
  README.
- **By control tercile.** Creators ranked by their control-set speech rate (ties by r3-P42's creator order) into terciles
  of 8, 8 and 7 creators (lowest first); the statistic and reading per tercile, each tercile count checked by 0.4. Only if
  the control set is computed; else "not computed (the control set is not computed)".
- **Plot**: a forest of placebo-adjusted page-over-speech log ratios per list with the equivalence band shaded, beside
  r3-P49's Lorenz curves.

## 4. What is not done here

No stance read (class c), no precision read, no model call. r3-P54's screen and list are not touched. The title-profile
contrasts are printed only where every group holds 5 or more creators.
