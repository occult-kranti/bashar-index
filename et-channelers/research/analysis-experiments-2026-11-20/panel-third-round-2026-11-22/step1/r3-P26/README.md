# r3-P26 / r4-P06: a method-dependence map and an MTMM read over input-disjoint pairs

Third-round panel programme, step 1 (class a.1). This folder, `r3-P26`, **carries r4-P06** (MTMM over input-disjoint
pairs; novelty log N05). Written 2026-11-26 (UTC times from `date -u` in status.json) by a step-1 agent (a model agent
working for the project lead; not a person). Seen creators only. No model call, no network call, no download.

**Status.** Exploratory; not a test of H1-H10. Every model cell is model-coded and not checked by a person; rule cells
are cue counts; agreement between methods is agreement, never accuracy.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## What it asks

MTMM found that, for voice, source family and asks, agreement between methods inside a construct exceeds agreement
across constructs (Campbell and Fiske's pattern). But MTMM's and RX-CB's voice cells are partly agreement by
construction (D3): methods that read the same text, the same cue forms or the same model's output agree for that reason
alone. Campbell and Fiske's independence condition asks for convergence between methods that share as little as
possible. So: once each method's inputs are written down, which pairs share no input at all, and do those pairs still
agree? "No input-disjoint pair" and "not computable" are permitted answers.

## Prespecification

`prespec.md` (SHA-256 `e0bebf115bec5049924acf61b330ec638a6a63f145da6593c17eab363b416b35`) and the map it fixes,
`code/p26common.py` (SHA-256 `a66c5f072d7bb33d3dc602fab40957541c4305175bbcaebca20828ec310b4921`), were hashed at
**2026-11-26T06:29:28Z**, before any value of this entry was computed; `p26_run.py` refuses to run if either changed.
Known leak (stated there): the writer had read MTMM's public cells, TL-7.8's public rows and the headlines of RX-CB and
VER-DEP before writing the map. The map is coded from the methods' definitions; which pairs share no input follows from
it, not from the values.

## The dependence map and the input classes

Each method is placed on the inputs it reads (`public/data-r3-P26-dependence-map.csv`, `fig-r3-P26-dependence-map`):
transcript words; punctuation and case; recognizer timing and units; voiced frames (a.2; no method yet); title text;
page description; position; **the brand** (the named source: self-naming formulas, source and family names); cue lists,
codebooks and models by identity; the vendor (a shared vendor counts as shared: VER-DEP finds that two OpenAI models'
errors on constructed items correlate, phi about 0.5, and that four readers count for fewer than two independent votes);
and upstream model outputs (the small finder's ask candidates, the forecast finder's kept statements).

A pair's class follows from what it shares: **C1** the same text read by the same instrument; **C2** a shared text
surface; **C3** different surfaces but a shared model, vendor, codebook or list; **C4** shares only the brand; **C5**
input-disjoint.

Facts of the instruments that drive the classes (read from code and frozen prompts, worded without quotation):
- The frozen voice codebook names a voice naming itself as a source as a claimed-voice cue; RX's framing patterns J2a and
  J2b capture the same self-naming forms, so the voice models and the voice rule share the brand (D3, by construction).
- The title instrument puts its private family table of names and spelling variants into the models' instructions, and
  its word rule (MTMM's source family|page) reads the same table, so three of source family's four methods read the
  same title with the same list.
- The title presentation code (voice|page) and source family|middle come from one middle-model reading.
- PT part b masks the creator's own names on the page before the small model codes it; the page asks method reads no brand.

## Primary and readings (deposit 2's correlation margin 0.10; named direction positive)

| Construct | Input-disjoint (C5) pairs | Median convergent rho over C5 pairs (90% creator bootstrap) | Reading | Beside it: pairs sharing only the brand (C4) |
|---|---|---|---|---|
| voice (MTMM) | 0 | - | **no input-disjoint pair** | 0.381 (0.204 to 0.546), 1 pair |
| source family (MTMM) | 0 | - | **no input-disjoint pair** | 0.443 (0.274 to 0.596), 3 pairs |
| asks (MTMM) | 1 (the price-cue rule on the transcript against the page's written asks) | 0.110 (-0.085 to 0.293); all but fewer than 5 of 71 creators | **undetermined** (the interval crosses the margin and includes zero) | no pair |
| time window, hedging, condition (TL-7.8) | 0 | - | **no input-disjoint pair** (every reading shares the transcript and, but for one, the finder's statements) | - |
| subject (MTMM) | - | - | **not computable** (the construct was not run) | - |
| acoustic column | - | - | **not computable here** (a.2: r3-P08) | - |

**In words.** Voice and source family have no pair of methods that shares no input; their least dependent pairs share
the brand, and there agreement is clearly positive but lower than where methods read the same text. Asks has one
input-disjoint pair, and its agreement (0.11) cannot be told apart from zero or from the margin: undetermined. The
ceiling of any reading here would have been "convergent with a method of another family"; no construct reaches it. This
does not say the instruments are wrong; it says that the agreement MTMM reported rests on methods that share inputs.

**Described rows (not read; `data-r3-P26-convergence-by-class.csv`, `fig-r3-P26-convergence-by-class`).** Pooled over
the three constructs, the median convergent rho falls as fewer inputs are shared: C1 0.85 (0.81 to 0.92, 5 pairs), C2
0.53 (0.41 to 0.62, 4), C3 0.45 (0.33 to 0.57, 4), C4 0.42 (0.29 to 0.58, 4), C5 0.11 (-0.08 to 0.29, 1). Within voice
the C3 pairs (title code against the transcript labels, sharing the vendor and the brand) sit above the C2 pairs, so the
gradient is not strict within every construct. MTMM's own "cross-input" medians (pairs reading different surfaces: voice
0.574, source family 0.443, asks 0.317) mix classes C3, C4 and C5. TL-7.8's convergent cells are all C1 or C2 (medians of
its published cells: time window 0.72 and 0.74, hedging 0.71, condition 0.45; no interval, TL's creator values were not
rebuilt).

**Campbell-Fiske comparison for the one C5 pair** (described): its rho exceeds 0.875 of the 16 heterotrait rhos that
share one of its measures (90% 0.375 to 1.0), and all 7 of those that are themselves input-disjoint (90% 0.57 to 1.0).
These are shares of comparisons between correlations, not shares of creators.

**Other pairs the programme cites** (`data-r3-P26-pair-classes.csv`): RX-CB's framing-cue hits against model voice
boundaries are class C2 and partly agreement by construction (the codebook's self-naming cue and RX's J2 patterns are the
same forms); VER-DEP's readers are all C1 (one codebook on the same units; the other-vendor reader differs only in
vendor).

**Interval.** 90% creator-bootstrap percentile, 2,000 draws, taken with MTMM's own seeded generator and creator order, so
that every single-pair interval reproduces the published cell interval exactly (it does, for all 66 cells, points and
intervals). r3-P30's battery holds no design class for a correlation across creators of two creator-level shares (its
class E is a within-creator rank correlation, one value per creator), so the interval is the programme's creator
bootstrap, **not one r3-P30 calibrated**. The one computed primary reads undetermined, so the choice moves no reading.

**Multiplicity.** 56 primaries in the programme; if every true effect sat at half its margin, about 2.8 readings A would
be expected at the deposited 5%, up to about 6.1 for the share, standardised, AUC and rank-correlation classes (r3-P30).
A reading A is never a finding; none occurs here. Account cells (deposit 2): every account is silent on r3-P26 and
r4-P06, so no account is retired or supported.

**Novelty (log only).** The deposited log reads: "Measure-centric source maps applied to computational methods of one
footing construct, with convergence counted only over input-disjoint pairs, were not found in 7 member searches (8
attacker searches). Not found means only that." It is an application of Campbell and Fiske's independence condition; no
novelty sentence prints before the second attack pass (ruling 12).

## Departures and choices (stated)

1. **The map's codings are this agent's** (from code and frozen prompts): in particular that the voice models read the
   brand, that the vendor counts as a shared input, and that the upstream statement set carries the small model. With the
   vendor not counted as shared, the pair voice|small and voice|page would move from C3 to C4; the other C3 pairs share a
   model itself and would stay C3; no pair would become input-disjoint, so no primary would change.
2. **TL-7.8 was not rebuilt**: its classes are from the map, its values are TL's published cells; no interval for its
   class medians.
3. **RX-CB and VER-DEP** enter the map and the pair table only; no correlation is recomputed for them.
4. **The acoustic column** (a.2) and **the subject construct** (not run in MTMM) are "not computable".
5. A pair of P18's footing codebook and P69's screen (named in round 3's text) do not exist yet and are not on the map.

## Bases or fields not stored

- No per-creator subject measure (TC stage 2 was not bought). No acoustic measure (a.2). No speech-based source-family
  label (the NE full pass was not run), so every model cell of source family reads titles.
- TL-7.8's per-creator values were not rebuilt here (stored in TL's private folder; not needed for any primary).

## Contacts

None (see `contacts.md`).

## For the lead

1. Whether a between-creator correlation read on an uncalibrated creator bootstrap may ever read A (moot here: the only
   computed primary is undetermined).
2. Whether the vendor should count as a shared input (the map counts it, from VER-DEP); it changes no primary.
3. MTMM's published "cross-input" median mixes pairs that share a model or the brand; the paper's MTMM sentence ("source
   family's pass rests mainly on methods that read only titles") could add that no voice or source-family pair is
   input-disjoint.

## Files

SHA-256 of every file: `status.json`. Public data CSVs carry a commented header; PNGs at 200 dpi without text chunks;
PDFs without document information.

| File | What |
|---|---|
| `prespec.md` | the prespecification (hashed before any computation) |
| `public/r3-P26-readings.csv` | the primary per construct, with its reading, the C4 row and MTMM's cross-input median beside it |
| `public/data-r3-P26-convergence-by-class.csv` | median convergent rho by input class, per construct and pooled, with intervals (figure data) |
| `public/data-r3-P26-pair-classes.csv` | every method pair: kind, class, shared inputs, published rho and interval |
| `public/data-r3-P26-dependence-map.csv` | the map: methods by inputs (figure data) |
| `public/fig-r3-P26-dependence-map.png/.pdf` | the dependence map as a grid |
| `public/fig-r3-P26-mtmm-hatched.png/.pdf` | the MTMM matrix hatched by input class |
| `public/fig-r3-P26-convergence-by-class.png/.pdf` | median convergence by input class with intervals |
| `code/p26common.py` | the map and the class rule (hashed with the prespec) |
| `code/p26_run.py` | rebuild through CROSS `mtmm.build()` (seen-only, unchanged code), reproduction check, bootstrap |
| `code/p26_publish.py` | public tables and figures |
| `code/style.py` | the CHANGE group's style, copied unchanged |
| `code/zsolve.py`, `qscan_all2.py`, `quant.py`, `quant2.py` | the release's privacy scans, pointed at this folder |
| `private/` | run logs, the result file (no per-creator value), the prespec hash record (never published) |

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

Note (the lead's step-1 decision 49(h), 2026-11-26T09:22:54Z): the SHA-256 values printed here are those of the private files as written; the SHA-256 of each published file is in status.json, `published_copy.published_sha256`.
