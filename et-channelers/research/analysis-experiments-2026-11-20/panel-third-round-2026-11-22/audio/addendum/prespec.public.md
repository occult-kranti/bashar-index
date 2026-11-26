# Audio addendum: one prespecification for the registered parts that wait for audio (the lead's decision 106.4)

> Published redacted (2026-11-26T19:57:53Z, the lead's decision 113; 2026-11-26T20:13:50Z, decision 114): the citation of the audio
> prespecification's hash is replaced, a phrase quoting an estimate the audio entries do not print is replaced, the
> standing rule is worded generically, and references to the hash record point to its public copy. The original
> stays private and unchanged; it was hashed at 18:39:23Z (UTC), before any outcome; the hash is kept privately (step-1 decision 49 item i).

Written 2026-11-26 from 18:36Z (UTC, from `date -u`) by the audio-addendum agent, a model agent working for the project
lead (not a person). Written and hashed before any outcome of these parts was computed; its hash time is in
`prespec-hash-record.public.md` (the hash is kept privately). Parts: r3-P01's part E, r3-P17's acoustic primary, r3-P15's acoustic rungs, r3-P13's
exploration, r4-P06's acoustic column, r3-P14's acoustic part, r3-P16's delivery rows, and the GPU re-decode (r3-P01's
family C over the whole roster, r3-P02's grid rows), which is not run (decision 106.4).

**Exploratory; not a test of H1-H10.** Seen creators only. Voice labels are model-coded (the small model, the label of
record on seen recordings) and not checked by a person; comparisons between instruments are agreement, never accuracy.
Acoustic features describe the sound of these recordings (delivery and recording conditions), never a speaker's state or
a source; recovery was checked on constructed audio only (an upper bound); no person listened. No audio is read, copied or
decoded: every part is computed from the stored per-recording summaries (`audio/private/features/`), the audio entries'
outcome-free label extract and the CROSS pass's stored cue hits. No GPU lease, no model or API call, nothing installed, no
git commit; one worker.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 0. Sources, what was seen, order

### 0.1 Sources that bind
- Programme (origin/main 9c8ac62, fetched 18:20Z): sections 0, 2.0 and 2.1 (step 1's r3-P01 and r3-P26 / r4-P06; step 5's
  r3-P14, r3-P15 / r4-P13, r3-P16, r3-P17; the a.2 table and "Also waiting for the Tier 0 ruling"), 2.2's card b2
  (r3-P13); `programme-decisions.json`; `lead-rulings-2026-11-26.md`.
- Deposit 2: margins and readings, the split policy (r3-P01, r3-P15 and r3-P17 are named unsplit), the account-prediction
  cells, the calibration card; r3-P30's `interval-choice.csv` (SHA-256 `fcfe22cf...e1f6`).
- Each part's registered text: r3-P01's published README and its hashed tolerance-arm record (margins); r3-P15's,
  r3-P17's, r3-P14's and r3-P16's published prespecifications (step 5, shared file `common/prespec-common.md`) and
  READMEs; r3-P26's published prespecification and code (`p26common.py`, the map and the class rule); the round-3 pooled
  method text where the programme names a part without its design (r3-P01 E: "part E at matched acoustic tempo";
  r3-P15: "acoustic rungs on scale-free features only, never timbre"; r3-P17: "acoustic rate and energy pauses on gated
  spans as primary, recognizer rows as sensitivities"; r3-P13: "early cue hits of the better-precision families";
  r3-P14's acoustic feature list) and the speech member's reading table A1 to A8.
- The audio prespecification (published redacted; its hash is kept privately): the instrument, the location rules, the
  background gate (A8: SBR 25 dB or more; fewer than 12 eligible creators after the gate prints "not measurable
  acoustically in this corpus" first and caps readings at undetermined), the battery and its caps (section 3).
- The common rules for steps 3 to 5; the lead's decisions 1 to 106 (95.4, 103, 104 and 106 in particular).

### 0.2 What I had seen before writing this file
- **The seven audio entries' results** (READMEs and public tables): r3-P08 (I4 acoustic nucleus rate about -0.002,
  undetermined by battery criterion 1; I1 within the margin; I5 recognized syllables per nucleus about -0.043, 90% -0.098
  to 0.011, undetermined; F0 range and intensity variability rows undetermined; the battery table), r3-P09 and r4-P15
  (A8 not met; estimates capped; r4-P15's ladder estimate: not printed (privacy rule)), r3-P11 and r4-P16 (class shares; the
  breath-like share within the margin), r3-P12 (creator shares of variance; F0 range's share partly condition), r4-P03
  (environment-change excess undetermined; criterion 6).
- **Published results of steps 1 to 5** that bear on these parts: r3-P01 (families A, B1, D read B; B2, C1, C2
  undetermined; the tolerance-arm margins), r3-P26 (no input-disjoint pair for voice and source family; asks undetermined;
  the acoustic column "not computable here"), r3-P15 (P1 undetermined, P2 undetermined, P3 beyond the margin nearer the
  creator's own voice; P1b claimed-claimed halves nearer than own-own), r3-P17 (text rate within the margin on C1 to C3;
  long-pause share C3 beyond the margin, claimed lower), r3-P14 (text score undetermined on the 11), r3-P16 (shift
  undetermined; by mode not computed: within the 11 one side of each comparison holds fewer than 5 creators), and the
  lead's decisions files for steps 1 to 5, which summarise the other entries. Other step 1 to 5 READMEs were not read for
  outcomes.
- **Outcome-free counts** (`common/code/eligibility_add.py`, label extract and cue-hit times only; no acoustic value, not
  even the gate's SBR), printed here only as bands: r3-P01 part E 30 or more creators; r3-P17 groups CL 30 or more, OWG
  12 to 29, OWT 30 or more, CLG fewer than 5; contrasts C1 30 or more, C2 12 to 29, C3 12 to 29, C4 fewer than 5; r3-P15
  rungs (same recording, own-own, claimed-claimed, across recordings, pooled) 30 or more each; r3-P13 on T: early framing-cue
  hits 5 to 11 creators, early placebo-list hits 12 to 29.
- No acoustic value of any recording was read before this file was hashed; no outcome of these parts exists.

### 0.3 Order
1. This file and the code it names are hashed (`prespec-hash-record.public.md`; the hash is kept privately).
2. Gated counts (the background gate on the stored SBR) are recorded per part before any contrast is computed.
3. The parts in the order r3-P01 E, r3-P17, r3-P15, r3-P13, r4-P06; then the not-run parts' files; then publication, the
   solvers and the status files. One worker; any job over a minute under `run_locked.sh`.

## 1. Shared rules (all computed parts)

- **Recordings and admitted audio:** the pass's 895 recordings and their stored summaries; only admitted time (claimed or
  own under the own-solo definition; no third party's voice) carries features (audio prespecification section 1).
- **Gate (A8):** a recording enters when its stored SBR is 25 dB or more. **A8** applies to every row (the speech member's
  table: "A8, all rows"): a row on fewer than 12 gated creators reads at most "undetermined (A8)"; when the part's primary
  row has fewer than 12, the part prints "not measurable acoustically in this corpus (fewer than 12 eligible creators after
  the background gate: A8)" first. Rows on fewer than 5 creators read "not computed (too few terms or creators)".
- **Battery caps (audio prespecification section 3, as stated; decision 106.3):** rate rows (acoustic nucleus or
  articulation rate, and quantities whose recovery runs through the nucleus count) read "within the margin (B)" only if
  criterion 1's slope and criterion 3 hold (the slope is not met: never B); "beyond the margin" only if criterion 3 holds
  for rate (met). Pitch-range rows read neither way (criterion 3 not met for pitch range). Pause and intensity rows carry no
  battery cap. **For a distance over several features** (r3-P15's composite profile), a direction may be read only if every
  feature in the profile may read it; with F0 range in the profile the composite reads at most "undetermined (battery
  criteria 1 (rate slope) and 3 (pitch range) not met)" in either direction. This is how this file applies the stated caps
  to a composite (an implementation choice, put to the lead).
- **Tiers:** r3-P01, r3-P15 and r3-P17 are unsplit contrasts on all seen creators (deposit 2's split policy names them);
  their data-tuned parts (r3-P15's feature scales) are fitted on the tuning pool T only (decision 106.1). r3-P13's
  exploration is a data-tuned search and runs on T only (the exploration side; decision 106.1). Decision 106.1's departure
  and its limitation (half B is no longer sealed for the acoustic measures described here) are printed in every output.
  T and the non-development creators are read from r3-P40's stored count register, not from deposit 2's split file.
- **Margins** (deposit 2, unless the part's registered text fixes one): ratio of rates |log| 0.223; share difference
  0.05; standardised difference 0.20 SD (unit stated per row). r3-P01's part E uses r3-P01's hashed tolerance-arm margin
  (section 2).
- **Words:** no part has a deposited direction (step 2's convention): "beyond the margin (<side>)", "within the margin
  (B)", "undetermined", with the caps above. A reading is never a finding.
- **Count forms:** gated sets print as "fewer than 5", "5 to 11" or "12 or more" (the audio entries' forms, so that A8's
  verdict never narrows a band), except where a part's interval method is chosen by the count (r3-P01 E, r3-P15): there
  the band is aligned with r3-P30's rows, so the method carries no count information within it (decisions 64 and 71), and
  rows outside such a band read "not computed or not printed" (decisions 62 and 104). Every printed set is checked by
  membership against the steps 1 to 5 universe (the lead's `universe.py`), the audio entries' sets, the 11 voice-eligible
  creators (the standing rule: no statistic is printed on any subset of a printed group that lies within 1 to 4 of it) and every other set printed here; where two sets of the same measure nest within 1 to 4 (decision 103), the
  secondary row reads "not computed or not printed" (decision 104's one label).
- **Multiplicity:** no family-wise adjustment; every output prints: 56 primaries; if every true effect sat at half its
  margin about 2.8 readings beyond the margin would be expected by chance. A reading is never a finding.
- **Predictions:** deposit 2's cells for r3-P01, r4-P01, r3-P14, r3-P15, r4-P13, r3-P17, r3-P26, r4-P06 and b2 (r3-P13)
  are silent: nothing is scored. r3-P16's cells read "same as every other account": scored as "no account is retired,
  whatever the result (D23)".
- **Seeds:** `numpy.random.default_rng([s, k])`, s = first 8 hex digits of SHA-256("audio-addendum|<entry>|<name>").
- **Plots:** the CHANGE group's style, 200 dpi PNG without text chunks, PDF without document information; distributions
  over 5 or more creators only, no per-creator or per-recording point.

## 2. r3-P01 part E: recognized syllables per acoustic nucleus (step 1 entry; unsplit, all seen creators)

- **Registered text:** programme r3-P01 ("part E (recognized syllables per acoustic nucleus)", a.2); round-3 pooled
  method ("Part E ... at matched acoustic tempo (den-meth)"); r4-P01 ("within speaker and recording"; "read only at
  boundaries that pass the splice census"); the speech member's A4 (the deletion row: claimed voice lower means deletion,
  the recognizer's slowing at least partly deletion).
- **Base:** gated recordings in the pass holding both voices (primary definition) with 60 s or more of clean interior on
  each side (battery criterion 7's minimum for rate measures). Per recording: E_r = log((S_c + 0.5) / (N_c + 0.5)) -
  log((S_o + 0.5) / (N_o + 0.5)), S the recognized syllables of words whose midpoint lies in the side's clean interiors
  (the run recognizer of record), N the acoustic nuclei in the same interiors.
- **Creator value:** precision-weighted mean over the creator's eligible recordings (weight N_c N_o / (N_c + N_o)), as
  r3-P01's creator values. **Interval:** r3-P01's registered rule: design class A_log_ratio (log ratio of a rate between
  two parts of a recording; creator means of recordings), r3-P30's choice at the row's creator count, by step 1's
  `pubrules.interval`; the random-effects methods use creators with 2 or more recordings, each creator's variance floored
  at the Poisson sampling variance of its recording values (mean over recordings of 1/(S_c+0.5) + 1/(N_c+0.5) +
  1/(S_o+0.5) + 1/(N_o+0.5), divided by the number of recordings). Where r3-P30's method does not hold at the count, a
  reading is at most undetermined. Beside every row: the t interval on creator means over all of the row's creators,
  labelled "sensitivity (not the reading)" (the lead's step-1 decision).
- **Margin:** r3-P01's consequence-based margins are hashed in its tolerance-arm record; part E's log ratio is the
  transport of the syllable-rate contrast from the acoustic instrument to the recognizer (E = recognizer rate contrast
  minus acoustic rate contrast), so the hashed "all words, log ratio of syllable rate" margin applies: **0.0222**. (A4's
  0.05 and deposit 2's 0.223 are not used: one margin, the entry's own.)
- **Rows:** E1 (primary) as above; E2 **matched acoustic tempo** (den-meth): within each eligible recording, consecutive
  10-s chunks of each side's clean interiors, binned by acoustic articulation rate (fixed bins 0.5 nuclei per second wide
  from 0 to 10); per bin holding both sides, log((sum S_c + 0.5)/(sum N_c + 0.5)) - log((sum S_o + 0.5)/(sum N_o + 0.5));
  recording value = weighted mean over shared bins (weight n_c n_o / (n_c + n_o), n chunk counts); recordings with 3 or
  more matched chunks on each side; creator value = mean over recordings; same interval rule. E3 **splice census**
  (described): E1 on recordings none of whose voice boundaries with 10 s each side has a detected environment change
  (r4-P03's stored flags and threshold).
- **Reading (two-sided; r3-P01 names no direction):** "beyond the margin (claimed voice lower)" (fewer recognized
  syllables per nucleus: differential deletion or normalisation by the recognizer) or "(claimed voice higher)" needs E1's
  interval wholly beyond 0.0222 on that side, E2's interval wholly beyond on the same side (estimators must agree:
  programme 2.0), battery criterion 3 for rate (met) and A8. "Within the margin (B)" ("no differential deletion detected
  against the acoustic nucleus count") needs criterion 1's slope and is therefore never printed here: at most
  "undetermined (battery criterion 1 (rate slope) not met)". Otherwise "undetermined". Caveat printed: the nucleus detector
  compresses rate differences (slope about 0.45), so a real rate difference between voices moves E in the direction of
  the recognizer's rate contrast even without deletion; E2 holds acoustic tempo but cannot remove that compression.
- **Count forms:** bands aligned with r3-P30's A_log_ratio rows: "30 to 39", "40 to 49", "50 to 70" (a single method
  in each; at 71 "all 71", where no method holds and a reading is at most undetermined); a row below 30 reads "not
  computed or not printed". The count of creators with 2 or more recordings is not printed.
- **Not run:** family C over the whole roster and r3-P02's grid rows (the GPU re-decode: a re-transcription, read as
  covered by the owner's instruction of 26 November; decision 106.4); a recognizer of another family (package ruling); a
  person's word reference (class c).
- **Plot:** E1 to E3 with their intervals against the margin, beside r3-P01's published family readings (words only) and
  r3-P08's I1, I4 and I5 estimates (published, non-development creators) for scale.

## 3. r3-P17 acoustic primary: the calm-register control (step 5 entry; unsplit, all seen creators)

- **Registered text:** r3-P17's prespecification (groups, contrasts, margins, words, the entry's reading); round-3 pooled
  method ("acoustic rate and energy pauses on gated spans as primary, recognizer rows as sensitivities").
- **Groups** (as r3-P17, units outside H1's excluded formats): CL claimed voice outside guided practice (primary
  definition, recordings whose main kind is not guided practice); CLG claimed-voice guided practice; OWG own-voice guided
  practice (own-solo definition); OWT own-voice talks (own-solo definition, own-talk recordings of the solo format). A
  creator enters a group with 300 or more words in it (r3-P17's rule) **and** 60 s or more of gated clean interior of the
  group's spans (battery criterion 7; spans are maximal runs of the group's units; clean interiors drop 10 s inside each
  end; an acoustic choice, stated).
- **Measures** (per creator and group, pooled over the group's gated clean interiors): acoustic articulation rate (nuclei
  per second of phonation time, de Jong and Wempe's minpause 0.3 s) and acoustic long-pause share (acoustic pauses of 1 s
  or more over interior time, energy-based). Recognizer rows are r3-P17's published text rows (cited, not recomputed).
- **Contrasts:** C3 (primary) CL against OWG; C2 OWG against OWT; C1 CL against OWT; C4 CLG against OWG (fewer than 5
  eligible: not computed). Rate: log ratio, margin |log| 0.223; long-pause share: difference, margin 0.05. Interval: the
  t interval on creator means (90%), fixed (r3-P17's rule; rate rows r3-P30's class G chooses the same method at 12 or
  more; share rows "interval class not calibrated by r3-P30").
- **Caps:** rate rows never read B (criterion 1's slope); they may read beyond (criterion 3 met). A8 per row; the entry
  prints A8's sentence first if C3 has fewer than 12 gated creators.
- **The entry's reading per measure** (r3-P17's words): "the calm-register account covers the claimed voice's difference
  on <measure>" if C3 reads B and C1 reads beyond; "the claimed voice differs from own-voice guided practice on <measure>"
  if C3 reads beyond; otherwise "not informative at this size (undetermined)". For rate, B is unavailable, so only the
  second sentence or "not informative" can print.
- **Described rows:** creator-balanced group means (CL, OWG, OWT) with t intervals over each group's own gated set; no
  overall mean across groups; no group mean on a contrast's set.
- **Plot:** group means of both acoustic measures beside the contrasts C1 to C3 against their margins, the text rows'
  published estimates marked for comparison.

## 4. r3-P15 acoustic rungs: person or register, the distance ladder (step 5 entry; unsplit, all seen creators)

- **Registered text:** r3-P15's prespecification (rungs, contrasts, standardisation by the reference distance's
  between-creator SD, the two-standardisation agreement rule, words, the entry's reading); round-3: "acoustic rungs of
  the ladder (P08) on scale-free features only, never timbre"; A7 (the own-range ladder) and r4-P15's feature set.
- **Profile (scale-free, no timbre):** articulation rate (log), F0 range (semitones relative to the recording's median;
  Tier 1), intensity variability (dB; the within-chunk SD of voiced-frame level, pooled over chunks, so gain differences
  between recordings do not enter) and long-pause share. No tilt, flatness, rolloff or band level.
- **Parts:** exactly 120 s of gated clean interior (battery criterion 7: F0 range's 120 s), built from 12 chunks of 10 s
  drawn without replacement from the part's consecutive 10-s chunks; 20 draws (r3-P15's rarefaction); distances averaged
  over draws.
- **Two scalings** (the analogue of r3-P15's two standardisations; both fitted on T only, on own-voice parts of gated
  recordings): S1 the between-creator SD of T creators' mean own-voice part values; S2 the pooled within-creator SD of
  own-voice part values across a T creator's recordings (the own voice's recording-to-recording SD, den-meth's unit).
  Distance: Euclidean over the four scaled features.
- **Rungs:** same recording (recordings with 240 s or more of claimed and of own clean interior, primary definition; each
  side cut in time order into halves): OO, CC, CO as in r3-P15; OO-only and CC-only rows on recordings with 240 s on that
  side; across recordings: a claimed part (primary) and an own part (own-solo) per recording with 120 s, OO_x and CO_x as
  in r3-P15 (creators with 2 or more own parts and a claimed part with an own part of another recording); pooled: claimed
  interiors of gated recordings in the pass (excluded formats have no audio: a departure from E2's own rule, stated) and
  own interiors (own-solo) of solo gated recordings, each pooled in recording then time order and cut into halves (each
  120 s or more): OO_p, CO_p, CX, OX as in r3-P15. Creator values as r3-P15 (means over recordings or pairs).
- **Contrasts:** P1 = CO - OO, P1b = CC - OO, P2 = CO_x - OO_x, P3 = CX - CO_p, P3b = OX - OO_p, each divided by the
  between-creator SD of the reference distance's creator values (r3-P15). Primary: P1, P2, P3 on the composite profile; a
  row reads beyond or within only if S1 and S2 give the same words. Interval: class C_standardised, r3-P30's choice at the
  row's count (the t interval at 30 or more, the same at every simulated count from 30 up); counts print as "30 or more";
  a row with fewer than 30 gated creators reads "not computed or not printed" (decision 62's reasoning). Margin 0.20.
- **Caps:** the composite contains rate (criterion 1 slope) and F0 range (criterion 3), so composite rows read at most
  "undetermined (battery criteria 1 (rate slope) and 3 (pitch range) not met)". **Per-feature rows** (described): the same
  five contrasts on each feature alone (one-dimensional distances; the scaling cancels), each capped by its own feature's
  rule (articulation rate: never B; F0 range: neither way; intensity variability and long-pause share: no cap).
- **The entry's reading** (r3-P15's words on the acoustic primaries): case 1 needs P1 to read B, cases 2 and 3 need P1 and
  P3 beyond; with the caps the acoustic reading is "undetermined" by construction, and the per-feature rows say where any
  acoustic distance lies.
- **Described rows:** the composite rung distances (creator means with t intervals) under S1 and S2.
- **Plot:** the acoustic ladder (paired dot-intervals per rung, OO as the noise band), S1 and S2 side by side; per-feature
  standardised contrasts against the margin.

## 5. r3-P13 exploration: a label-free acoustic hypothesis (b2; exploration on the tuning pool T only)

- **Registered text:** card b2 (prediction, measure, decision rule: "registered only if the seen exploration curves leave
  the placebo band"); round-3 pooled method (early cue hits of the better-precision families; footing change points; an
  announced-switch placebo family; placebo hits; position-matched points; the difference in differences against the
  comparison strata; a leak-free planning SD from shifted pseudo-cue points in own-voice-only recordings; the plot).
- **Pool:** T only (decision 106.1); T creators' gated recordings.
- **Events (rule-located; no voice label locates them):** the first hit in a recording of RX's better-precision opening
  families (RXP's hit-weighted read precision 0.80 or more: J1 announcement, J2b "we are" + group; J2a, below it, is out);
  placebo events: the first hit of RX-CB's placebo lists for J1 and J2 (P1, P2). An event enters when its recording passes
  the gate and 40 s or more of admitted time lie in each of the windows -60 to -10 s and +10 to +60 s (admitted time is
  defined by the labels: no third party's voice is processed; stated).
- **Features and curves** (as r3-P09's code, `bshared.py`): articulation rate (log), F0 range (SD units: T's
  between-creator SD of own-voice F0 range), long-pause share (pause-tied, never alone a change of delivery), in 10-s
  windows from -60 to +60 s; the sustained shift (10 to 60 s after minus 60 to 10 s before). **Shifted points:** 5 per
  event in the same recording and tenth, 30 s or more from any framing or placebo hit, with the same admitted-time rule;
  the permutation-maximum band (200 draws, one shifted point per event per draw, 90%).
- **Rows:** R1 framing cue: per feature, the creator-mean sustained shift minus the mean of its shifted points (t interval,
  margins 0.223 log, 0.20 SD, 0.05), and whether the creator-mean curve leaves the band; R2 placebo hits: the same; R3
  framing cue minus placebo (creators with both): the sustained-shift difference. **Leak-free planning SD** (speech, round
  3 Q4; acoustic version): pseudo-cue points in T creators' own-voice-only gated recordings (own units and no claimed unit
  under the primary definition), one per recording, placed by seed at the tenths of the framing-cue events, the sustained
  shift of articulation rate; the SD over creators of their means; creators needed for a two one-sided test of
  equivalence and for a one-sided test, at power 0.8 and 5%, against effect sizes 0.05 to 0.30 (log), under heterogeneity
  0, half and one noise SD.
- **Not computed:** footing change points (r3-P18's locator is stored only for the 11 voice-eligible non-development
  creators; rebuilding it on T reads transcript text); the announced-switch placebo family (no list exists; writing one
  would be a new registration); the difference in differences against comparison strata (none in the corpus: a new
  collection).
- **Caps:** A8 on R1's creators (the outcome-free count is 5 to 11 before the gate, so "not measurable acoustically in
  this corpus" prints first and every row is capped at undetermined); rate rows and "leaves the band" for articulation rate
  read as beyond-type statements (criterion 3 met), "inside the band" never reads as "no change" (criterion 1's slope); F0
  rows read neither way.
- **Plot:** peri-cue small multiples (framing cue, placebo hit, shift) with the band; the power curve. Footing change
  point and announced switch panels print "not computed".

## 6. r4-P06's acoustic column (r3-P26's map; outcome-free)

- **Registered text:** r3-P26's prespecification and `p26common.py` (the map, the class rule C1 to C5; "no input-disjoint
  pair" and "not computable" are permitted answers).
- **What the stored features can give:** every stored acoustic quantity is computed over label-admitted time and located
  by the small model's labels on recognizer units. So an acoustic method from the stored features reads the labels'
  inputs (the small model, the voice codebook and through it the brand, the vendor, recognizer timing and units, position)
  besides voiced frames. Three codings are classed against every MTMM method with r3-P26's unchanged `pair_class`: (a)
  r3-P26's placeholder (voiced frames, units, position: no method of this kind can be built from the stored features);
  (b) a label-located voiced-frame method (the stored features' acoustic rates and F0 rows); (c) a label-located
  pause-tied method (meas's shared-channel cell). The acoustic column's primary per construct is "no input-disjoint pair"
  if no coding that the stored features can build is class C5 with a method of that construct; no correlation is computed
  (none is needed for that answer).
- **Plot:** the class grid of the three codings against the twelve MTMM methods.

## 7. Parts not run or not computed (decided now, from the registered text and outcome-free facts)

- **r3-P14's acoustic part:** not run. The registered part is a read-like delivery score built from acoustic pause
  placement by clause slot, pause-duration regularity, run length, hesitation pauses and breaths at boundaries, fitted and
  compared per creator. (1) The audio prespecification (section 2) bars computing the read-like quantity per creator (the
  P10 veto's proxy rule); (2) pause-duration regularity is the feature the speech member vetoed as a hidden
  synthetic-voice screen; (3) hesitation pauses need a filled-pause detector the pass did not run (a further audio pass);
  (4) the clause-slot placement of acoustic pauses needs the transcript's words, which the stored features do not hold.
  Printed: "not run (needs a further audio pass; the read-like score is not computed per creator under the audio
  prespecification)".
- **r3-P16's delivery rows:** not computed (too few terms or creators). r3-P16's registered shift pool is the 11
  voice-eligible creators, within which one side of each mode comparison holds fewer than 5 creators (step 5, published);
  the background gate can only remove creators. No overall delivery shift over the 11 is printed: it is not r3-P16's
  question, and A8 cannot be met on 11 creators.
- **The GPU re-decode** (r3-P01's family C over the whole roster, r3-P02's grid rows): not run (decision 106.4: a
  re-transcription of the seen recordings, read as covered by the owner's instruction of 26 November, "no need to
  transcribe further, complete 20+ analysis first"; it goes to the owner and the fourth panel's agenda).

## 8. Privacy and outputs

The common rules' privacy section binds, with decisions 62, 95.4, 103 and 104. Never printed: audio, waveforms or
spectrograms, any per-recording or per-creator value, absolute pitch, names, ids, titles or quotations. Every output
carries the agnosticism sentence, the acoustic-features line and decision 106.1's departure. Outputs per part under
`audio/addendum/<id>/` (code/, public/, README.md, contacts.md, status.json). Solvers before finishing: zsolve,
qscan_all2, whole_position_scan, every s1_* solver with paths adapted (s1_blanks with `d62`), `audio_blanks.py`'s d62
and shape routes (adapted to the addendum's folders) and the identifier scan (creator codes, audio hashes, video ids,
page keys, the pass's stems).

## 9. Code fixed with this file (SHA-256 in `prespec-hash-record.public.md`)

`common/code/addcommon.py` (loaders, helpers) and `common/code/eligibility_add.py` (the outcome-free counts above). The
audio entries' code is used unchanged (`audio/common/code/`: `locate.py`, `measures.py`, `features.py`, `adata.py`,
`bshared.py`, `acommon.py`), as is step 1's `pubrules.py` (r3-P30's methods) and r3-P26's `p26common.py`. Analysis code
written after this file implements sections 2 to 6 as stated; any departure is logged in the part's README with its time.
