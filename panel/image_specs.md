# Image specs — Bashar-Index site folio (7 plates)

*Round 5, Coder-Expert. Copy-paste-ready generation prompts for the public
folio. House style: "Resonant Vessels" — engraved-plate scientific diagrams
(fine copperplate linework, stipple shading, sepia/amber ink on dark archival
ground) and dark archival 3D renders (matte bronze, smoked glass, low tungsten
light, museum-vitrine atmosphere). Palette: ground #191715, ink #ede6da,
amber #e8a33d, copper #b5713a, failure-red accent #c8503a.*

**Standing rules for all 7 plates:**
- **No unprovenanced numerals may be burned into an image.** Any number that
  appears inside the generated artwork must be either (a) a decorative
  non-numeric glyph, or (b) copied verbatim from `analysis/results/*.json`
  and listed under "Burned-in numerals" below with its JSON source. All other
  quantities live in the HTML caption overlay, never in the pixels.
- Grade banners ("EXPLORATORY", "digest_level: content | grade: Frontier",
  and the quietism line "measures genre discipline, not truth") are added as
  text overlays at publish time, exactly as the analysis figures F1–F8 carry
  them; prompts below note where the banner strip goes but do not ask the
  generator to render statistics.

---

## Plate 1 — Folio hero: the instrumented séance-laboratory

**Prompt:**
> Dark archival 3D render, wide cinematic composition: a mid-20th-century
> séance room reimagined as a metrology laboratory. A channeler sits at a
> heavy oak table, eyes closed, hands flat; around the table, instead of
> candles, an array of brass and smoked-glass instruments — galvanometers with
> engraved dials (no numerals on the faces, only tick marks), a chart recorder
> unspooling a long paper trace onto the floor, a vacuum-tube oscillograph
> glowing faint amber, a plumb line and spirit level mounted absurdly on the
> spirit cabinet. A single tungsten lamp overhead; dust motes in the beam;
> everything else falls into deep charcoal shadow. Matte bronze, bone, aged
> paper, black lacquer. Museum-vitrine stillness, faint volumetric haze. No
> text, no numbers anywhere in the scene. Aspect 21:9.

**Labels (HTML overlay, not baked in):** "the instrumented session" ·
"digest_level: transcript — Speculative" · quietism banner.
**Caption:** *Every claim in this archive was produced in a room like this
one. The panel's contribution is not to judge the room but to instrument it —
to measure what the sessions promise, package, and quietly re-schedule.*
**Grade banner:** Speculative (transcript-level scene) + quietism line.
**Burned-in numerals:** none.

## Plate 2 — Stylometry pipeline diagram (blocked arm)

**Prompt:**
> Engraved-plate scientific diagram, copperplate etching style, amber ink on
> near-black ground: a horizontal process plate in three registers. Left
> register: a stack of manuscript transcript sheets feeding a small engraved
> waterwheel labeled only with a glyph; center register: the sheets transform
> into a row of identical apothecary jars each holding a sorted handful of
> small word-tiles (the tiles are blank or carry only function-word silhouettes
> like "the", "of", "and" — no other words); right register: the jars tip
> into the pans of a delicate balance scale whose beam is engraved with a
> waveform, and whose pointer rests between two engraved bowls. Fine stipple
> shading, ruled construction lines, plate border with corner rosettes. A
> broken link in the chain between the first and second register, drawn as a
> snapped chain with a small padlock hanging from it — the acquisition
> blocker. No numerals anywhere.

**Labels (engraved-style overlay at publish):** "transcripts (BLOCKED —
network egress)" → "function-word vectors" → "cross-entropy classifier,
ΔCE per token".
**Caption:** *The authorship arm, frozen mid-pipeline. Transcripts cannot be
fetched in the build environment, so the classifier never runs: the protocol,
WER gates (15% overall / 10% function-word), and the 6+6 pilot power
contingency ship as a registered report instead. No transcript was
fabricated.*
**Grade banner:** Speculative | status: BLOCKED, registered-report fallback.
**Burned-in numerals:** none (WER gate values live in the caption).

## Plate 3 — The prediction ledger / receding-deadline ratchet

**Prompt:**
> Engraved-plate diagram: a large wall calendar rendered as an architectural
> engraving, but the calendar's pages are mounted on a ratchet-and-pawl
> mechanism of brass gears at the right edge; each page is identical, showing
> only a blank window-frame outline, and a taut string runs from a brass pin
> on each page to a small weight that hangs progressively further right on
> each successive page — the deadline physically receding as the mechanism
> turns. Below the calendar, an engraved ledger book lies open with ruled
> columns and many rows of tick marks (no legible writing, no numerals); a few
> rows are crossed out and rewritten one line lower. Deep shadows, stipple,
> copper and amber inks on dark ground, plate border. No legible dates or
> numerals in the artwork.

**Labels (overlay):** the slip chain as caption text: "2020 → 2023–33 →
2025–33 → 2026/27 → 2028–29"; "73 window-polarity flips (all-pairs ratios
from 35 window rows, non-independent)"; "consecutive restatements recede at
median 1.0 yr/yr (IQR [0.5, 4.25])".
**Caption:** *The ratchet that fails as hedging and succeeds as a calendar:
each promised window is replaced, on schedule, by a later one. The ledger —
164 dated claims — is the finding; the statistics are annotation.*
**Grade banner:** digest_level: content | grade: Frontier; the E7 flip
statistics on the overlay carry the **EXPLORATORY** banner, mirroring the
figure twin F7a.
**Burned-in numerals:** none; all counts and the IQR live in the overlay
(sources: `predictions_results.json`, `doctrine_dynamics_results.json`).

## Plate 4 — Doctrine network as constellation map

**Prompt:**
> Engraved celestial cartography plate in the style of a 19th-century star
> atlas: a dark circular firmament chart with a constellation of small
> engraved star-nodes connected by fine hairline arcs, densely webbed in the
> center, sparse at the rim; nodes are tiny engraved symbols (keys, ladders,
> spheres, prisms) rather than letters; faint dashed concentric coordinate
> circles and a decorative compass rose in the corner; the whole chart rests
> on a dark wooden table beside a brass dividers and an ink well. Amber and
> bone-white ink on near-black, heavy stipple, plate border with rosettes.
> Crucially: the constellation's stars are fixed, but a handful of stars are
> drawn with small circular motion arrows showing them brightening and dimming
> in place — emphasis churns, positions never move. No text labels, no
> numerals.

**Labels (overlay):** "126 nodes · 635 edges" (from `doctrine_results.json`);
"Kendall W ≈ 0.009 — a fixed vocabulary with liquid emphasis".
**Caption:** *The doctrine mapped as a firmament: the stars never move, only
their brightness. Salience ranks are uncorrelated across digests (W ≈ 0.009)
and half the top-five terms turn over between consecutive digests — churn of
emphasis, never of lexicon.*
**Grade banner:** EXPLORATORY — descriptive | quietism line mandatory.
**Burned-in numerals:** none (node/edge counts and W in overlay only).

## Plate 5 — SPECT psychography study setup (3D render)

**Prompt:**
> Dark archival 3D render, museum-vitrine realism: a small clinical side-room
> staged as a psychography study. At a writing desk in the foreground, a
> medium sits upright writing on paper, eyes closed, a pencil moving; beside
> the desk an instrument trolley holds a chart recorder and an engraved brass
> control panel with unmarked dials. Through a wide lead-glass window behind
> them, the gantry ring of a gamma camera (SPECT scanner) looms in dim amber
> rim light, its twin detector heads open around an empty padded table. In the
> far background, a second writing desk with an empty chair faces a small
> monitor cart — the station for the same medium's non-trance writing control
> condition. Matte clinical surfaces aged like old bronze, deep
> charcoal shadows, one practical lamp on the desk, faint haze. Quiet,
> respectful, documentary tone; no people other than the medium; no readable
> text, no numerals on any dial or screen.

**Labels (overlay):** "within-subject SPECT psychography design (Peres et
al., 2012, external literature)"; "control: each medium's own non-trance
writing (within-subject)"; "panel status: external precedent only — not part
of this corpus".
**Caption:** *The one published neuroimaging precedent for trance writing
(Peres et al., 2012): experienced mediums showed DECREASED frontal rCBF
(hypofrontality) during psychography relative to their own non-trance
writing; the increased-activity pattern appeared only in the less-expert
subgroup — a design the panel cites as precedent, not as evidence about this
corpus.*
**Grade banner:** grade: Speculative (external-study depiction).
**Burned-in numerals:** none (the 2012 citation lives in the caption).

## Plate 6 — The 2027 rubric scorecard plate

**Prompt:**
> Engraved-plate legal-scientific hybrid: a heavy parchment scorecard mounted
> on a dark wooden board under a glass vitrine, sealed with a red wax seal
> pressed with a key emblem. The scorecard shows three engraved rows marked
> only with symbols — a laurel wreath (full), a half-laurel (partial), an
> empty circle (failure) — each row followed by a long blank checkbox ruled in
> ink; the parchment is blank of all writing except the three symbols and
> ruled lines. Above the board, a small engraved hourglass with sand still in
> the upper bulb — the deadline has not yet arrived. A brass plaque beneath
> the vitrine is blank (engraving happens at publish, not in the render).
> Beside the vitrine, a historian's white glove and a magnifier. Amber,
> bone, oxblood-red wax on near-black; stipple; plate border. No numerals, no
> legible text.

**Labels (overlay, abridged summaries of the frozen rubric — the full
verbatim text is in analysis/README §"2027 prospective rubric" and FINAL_REPORT
§7):** "FULL — government/UN
confirms NHI + public exchange, or verified craft by ≥2 scientific
institutions, before 2030-01-01" · "PARTIAL — explicit non-human-origin
statement, lab/peer-reviewed verified; or mass-witnessed multi-instrument
event endorsed by ≥2 agencies" · "FAILURE — neither by 2030-01-01" ·
"retroactive calibration baseline: historical pass rate 0/2 — rubric frozen
regardless of outcome (no-tuning clause)".
**Caption:** *The falsification pledge, sealed before the outcome window: the
same instrument that scores 2027 was applied unchanged to the corpus's
resolved historical claims — both scored failure — and may not be edited in
response. Frozen, timestamped, blind-scored at the deadline.*
**Grade banner:** pre-registered | rubric frozen — no tuning; EXPLORATORY
calibration twin F8 carries its own badge.
**Burned-in numerals:** none (the 2030-01-01 deadline and 0/2 baseline live in
the overlay; sources: README §2027 rubric, `rubric_results.json`).

## Plate 7 — Digests → analysis pipeline plate

**Prompt:**
> Engraved-plate industrial-process diagram in the style of an 18th-century
> encyclopedia plate ("Diderot plate"): a left-to-right machine hall. Far
> left: a wall of small framed video-screen engravings feeding into a hopper;
> then a stamping press that converts each frame into a uniform punched card
> (the digest) dropping onto a conveyor; the conveyor passes under three
> engraved inspection gantries labeled only with symbols — a scale (demand
> segmentation), a calendar gear (prediction ledger), an astrolabe (doctrine
> graph); at the far right the cards are bound into a tall archive volume on a
> pedestal, with a small final gate in front of the pedestal drawn as a
> turnstile with a "4" formed by four tick-marks-only counters — representing
> the four primary tests, rendered as abstract ticks, not numerals. Fine
> parallel hatching, construction lines, plate border, dark ground, amber and
> copper inks. No legible words or numerals.

**Labels (overlay):** "75 digests → 164 ledger rows · 949 questions · 20 tags"
→ "P1–P4 Holm family (α = 0.05); everything else EXPLORATORY" →
"results/*.json + figures F1–F8, seed 42".
**Caption:** *The whole pipeline as one plate: public videos become digests,
digests become ledgers and share-vectors, and a single enforcement gate —
the multiple-comparison enforcer — decides what may call itself a finding.
Four pre-registered tests; everything else is badged exploratory.*
**Grade banner:** digest_level: content | grade: Frontier.
**Burned-in numerals:** none; all counts in overlay (sources:
`predictions_results.json`, `demand_results.json`, `family_holm.json`).

---

### Folio-wide consistency notes
- All seven plates share the palette, plate-border motif, and the standing
  rule that statistics ride in HTML overlays sourced from
  `analysis/results/*.json` — the artwork carries zero burned-in numerals.
- Doctrine-themed plates (1, 4) must carry the quietism line in their overlay:
  "measures genre discipline, not truth" (advisor certification criterion 7).
- Overlay grade banners mirror the figure badges: EXPLORATORY for E5–E10
  twins (F7a, F8), Frontier for digest-level content, Speculative for
  transcript-level or external-study material (plates 1, 2, 5).
