# Audio entries (Tier 0 and Tier 1): one prespecification for r3-P12, r3-P08, r3-P11, r3-P09, r4-P03, r4-P15 and r4-P16

> Published redacted (2026-11-26T19:37:45Z, the lead's decision 111; 2026-11-26T19:49:16Z, decision 112): outcome-free counts are printed as
> tier letters only, and references to the hash record point to its public copy. The original stays private and
> unchanged; it was hashed at 15:27:51Z (UTC), before the pass and before any outcome; the hash is kept privately (step-1 decision 49 item i).

Written 2026-11-26 from 15:25Z (UTC, from `date -u`) by the audio agent, a model agent working for the project lead (not a
person), under the lead's ruling 4 (Tier 0 and Tier 1 granted for seen recordings already on Drive, with the owner's
archive; Tier 2 closed). Written and hashed before the acoustic pass and before any outcome of these seven entries was
computed. Its hash time is in `prespec-hash-record.public.md`; the hash is kept privately.

**Exploratory; not a test of H1-H10.** Seen creators only. Voice labels are model-coded (the small model, the label of
record on seen recordings) and not checked by a person; comparisons between instruments are agreement, never accuracy.
Acoustic features describe the sound of these recordings (delivery and recording conditions), never a speaker's state or a
source. Recovery is checked on constructed audio only (an upper bound); no person listened (Tier 2 stays closed). No model
or API call, no git commit; nothing is installed.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## 0. Sources, what was seen, order

### 0.1 Sources that bind
- Programme (origin/main, fetched 14:57Z): sections 0 and 2.0, the a.2 table rows of r3-P08, r3-P09, r3-P11, r3-P12,
  r4-P03, r4-P15, r4-P16, section 2.5, novelty wordings N13 and N14, objection O14; `programme-decisions.json`;
  `lead-rulings-2026-11-26.md` (ruling 4).
- Deposit 2: margins and readings (`lead-margins-and-readings-2026-11-26.md`), the split policy and the private split,
  the account-prediction cells (every cell of these seven entries is "silent": nothing is scored), the calibration card.
- The speech member's acoustic reading table A1 to A8 (private round-3 memo, section 3; it is not in `programme.md`), the
  speech member's tiers (round 2, section 2.3), meas's merged battery criteria 1 to 7 (round-3 memo, Q2), the speech
  member's class rules for time outside recognized speech (round 3, Q5). These are design text; where they set a margin
  the programme does not state, deposit 2's default margin holds (the lead's margins file: "where an entry does state one,
  the entry's own value holds"; these entries state none). Their structure (rows, references, A8's creator floor) is
  adopted as written below.
- Common rules for steps 3 to 5 (privacy, tiers, order, solvers, output), the lead's decisions 1 to 91.

### 0.2 What I had seen before writing this file
- The exploratory release's public aggregates and step 1's published entries (as listed in step 5's section 0.1: E5's
  claimed voice has more long silent pauses on average with intervals including zero; r3-P02's weaker pause-punctuation
  coupling in the claimed voice; r3-P01's families A, B1 and D without differential recognizer instability). Step 3, 4
  and 5 READMEs were not read for outcomes; step 5's shared prespecification and code were read for their loaders.
- Outcome-free eligibility from the label extract (section 1; `common/code/eligibility_audio.py`): counts only, printed
  below as tier letters.
- **Development audio (tuning pool T only, exploration side, never read for any contrast).** Four recordings of four
  development creators were decoded to test mechanics and timing; 60-s own-voice clean-interior excerpts of three of
  them were held to run the battery while the instrument was tuned: the nucleus rule was set to de Jong and Wempe's
  exact dip rule with 20-ms smoothing (chosen from a grid of smoothing 1, 2, 3 and 5 frames and dips 1 and 2 dB on
  resampled copies), pause runs separated by 30 ms or less are joined, a frame is voiced only where the YIN difference
  function dips below 0.15, and the background spectrum uses non-active frames. Seen on those excerpts: rate recovery
  under time stretch and resampling has a slope near 0.5 (criterion 1's 0.9 to 1.1 not met on those excerpts), octave
  errors under 2% of voiced frames, inserted pauses of 300 ms or more all detected with a median edge error of 20 to
  30 ms, large rate and pitch-range biases with background noise at 15 to 20 dB below speech and under a music bed, and
  the environment score separating music-bed onsets and spectral changes from unedited points better than cuts and
  gain steps. The excerpts and every development output were deleted before the pass. No claimed-voice audio and no
  non-development creator's audio was read before this file was hashed.

### 0.3 Order
1. This file and the code it names are hashed (`prespec-hash-record.public.md`; the hash is kept privately).
2. The pass (`common/code/pass_audio.py`), one heavy job under `run_locked.sh`, non-development creators first.
3. The census (r3-P12) and the background gate first; the gated eligible counts are recorded before any voice contrast
   is computed.
4. The entries in the order r3-P08, r3-P11, r3-P09, r4-P03, r4-P15, r4-P16; then publication, the privacy solvers and the
   status files.

## 1. Inputs and location rules (outcome-free; `common/code/extract_labels.py`, `locate.py`)

- **Recordings.** Seen transcripts with a voice record whose units equal the voice file's units (English-only model of
  record): 1,284 recordings. **In the pass:** those not of H1's excluded formats (conversation, multi-presenter) with at
  least one admitted unit: 895 recordings of the 71 seen creators, 335.4 hours, 18.06 GB; 224 recordings (77.0 hours) of
  the 23 non-development creators. Remote path, size and SHA-256 of every recording come from the run ledger
  (`sync/edition_asr_manifest.jsonl`, `inference_source.audio`), the file `prep.recordings()` reads; the ingest manifest
  holds only the native downloads (812 of the 1,293 seen audio keys), so it is the fallback (a departure from the brief's
  wording, stated).
- **Admitted audio (no third party's voice processed).** A unit is admitted when its side under the own-solo definition
  (rule B, broad own voice, claimants sole speaker, host or owner, or no claimed voice; small model) is claimed or own.
  Units labelled V4 (other participant), V5 (other material), V6 (unseparated conversation) or V0 other than uncued solo
  speech are never processed: their samples, and gaps next to them, are set to zero before any feature is computed.
  Admitted time: each admitted unit from its first word start to its last word end, joined with the gap to the next unit
  when that unit is admitted too, and the lead-in and tail when the first or last unit is admitted.
- **Voice sides for contrasts:** the primary definition (claimed V2 + V3; own broad; claimants sole speaker or host or
  owner; small model). Spans are maximal runs of same-side units.
- **Clean interiors:** each span with 10 s dropped inside each end; interiors under 5 s are not used.
- **Voice boundaries:** directly adjacent units on opposite sides (entry: own to claimed; exit: claimed to own); time =
  midpoint of the gap between the two units. *Cue-free:* no RX opening or leave-taking cue within 2 units. *Seam-free:*
  not within 2 s of an internal 30-s seam. *Long:* 60 s or more of span on each side (for the 10-to-60-s windows).
  *Env:* 10 s or more of span on each side (r4-P03).
- **Matched non-boundary edges:** unit edges inside a span (both neighbours on the same side), with the same fields,
  matched to a boundary within the same creator on tenth of running time, the punctuation class of the unit's last word
  (full stop, question mark, exclamation mark, comma-like, none), the pause bin of the gap (under 0.3 s, 0.3 to 1 s, 1 s
  or more) and whether the next unit opens a recognizer segment; when no exact match exists the tenth is relaxed to
  adjacent tenths, then the punctuation class; up to 5 matched edges per boundary (seeded), never the boundary's own
  neighbours.
- **Claimed-voice onsets:** the first unit of a claimed span; *pre_ok* when the 30 s before it lie in the recording.
  **Own-voice onsets:** the same for own spans (own-solo definition).
- **Time outside recognized speech:** admitted frames not inside any recognized word interval of the record.

**Outcome-free eligibility among the 23 non-development creators** (from labels and word times only):

| Entry | Tier by count |
|---|---|
| r3-P12 (2 or more recordings with 60 s of admitted speech) | S |
| r3-P11 (a recording in the pass) | S |
| r3-P08 (60 s or more of clean claimed and of clean own interiors) | X |
| r3-P09 (a cue-free, seam-free, long boundary) | X |
| r3-P09, cue-opened column | D (not computed) |
| r4-P03 (a boundary with 10 s each side) | X |
| r4-P15 (a long seam-free boundary; the ladder: 60 s claimed and 2 own recordings) | X |
| r4-P16 (a claimed onset with 30 s before it) | X |

## 2. The instrument (`common/code/instrument.py`, `features.py`, `measures.py`)

numpy and scipy only: librosa and parselmouth (Praat) are not installed in the guarded venv, and nothing is installed.
Decoding: PyAV 16.0.1, already installed in the ASR environment and read from its site-packages by the guarded venv's
Python (a departure, stated: the analysis venv has no PyAV), as the corpus run decoded (`windows()` of
`pipeline/gpu_asr.py`: mono 16 kHz float, back-to-back 30-s windows). Frames: 25 ms Hann, 10 ms hop, 512-point FFT.

**Tier 0.**
- Level (dBFS per frame); digital silence: frame RMS below -70 dBFS; clipping: a sample at 0.99 or more.
- Recording levels over admitted non-silent frames: 10th, 50th, 90th, 99th percentiles; silence threshold = the larger
  of the 99th percentile minus 25 dB (de Jong and Wempe 2009) and the 10th percentile plus 3 dB; speech-to-background
  ratio (SBR) = 90th minus 10th percentile.
- Active frame: 20-ms smoothed level at or above the silence threshold. Acoustic pause: a run of non-active admitted
  frames of 150 ms or more after joining runs separated by 30 ms or less. Long pause: 1 s or more. Phonation time: span
  time minus pauses of 0.3 s or more (de Jong and Wempe's minpause).
- Syllable nuclei: peaks of the 20-ms smoothed intensity above the silence threshold, kept when the intensity dips by
  more than 2 dB before the next candidate (de Jong and Wempe's rule), on a voiced frame. Speech rate = nuclei per second
  of span time; articulation rate = nuclei per second of phonation time.
- Spectral flatness (100 to 4,000 Hz), high-band share (4 to 8 kHz), 99% rolloff (bandwidth), eight band levels; the
  background spectrum per 1-s block = mean band levels over the block's non-active admitted non-silent frames.
- Syllabic modulation index per 1-s block: envelope modulation power in 2 to 10 Hz over 0.5 to 25 Hz on a 2-s window.
- Reverberation proxy: median level decay slope over the first 150 ms after active runs followed by 0.3 s of pause.
- Frame classes outside recognized speech (rule-based, descriptive names; speech member's Q5 and P10 classes):
  excluded (not processed); digital silence; silence near the background floor (below the 10th percentile plus 6 dB);
  breath-like (unvoiced, aperiodicity above 0.35, flatness 0.20 or more, 10 dB or more below the 90th percentile, a run
  of 0.15 to 1.5 s); vocalisation without recognized words (a voiced run of 0.3 s or more, or of 1 s or more with
  syllabic modulation); sustained voiced tone, voice-like (a voiced run of 1 s or more, pitch SD 0.08 to 1.0 semitones,
  modulation index below 0.35); tone, instrument-like (a voiced run of 1 s or more steadier than 0.08 semitones, or a
  percussive attack of 15 dB within 30 ms followed by a 6-dB decay over 1 s with a peaky spectrum); music-like or
  sustained sound (flatness below 0.20, modulation below 0.35, for 1 s or more); other sound, unclassified. Where digital
  silence dominates, "no breaths" means "not observable"; over a bed, gaps are "unclassified" or "music-like", never
  "silence".

**Tier 1** (normalised span summaries only; never an absolute value).
- F0 by a YIN-type tracker (de Cheveigne and Kawahara 2002) on 8-kHz audio, 60 to 500 Hz, threshold 0.15, parabolic
  interpolation; voiced only where the difference function dips below the threshold; semitones relative to the
  recording's median over admitted voiced frames (the median itself is never stored); octave guard: a frame more than
  9 semitones from the median of the voiced frames among its 7 neighbours is dropped. F0 range = 90th minus 10th
  percentile of the semitone histogram (one-semitone bins, linear within a bin).
- Intensity variability: SD of level over voiced frames. Spectral tilt: 50-1,000 Hz over 1-4 kHz (dB), voiced frames.

**Nothing of Tier 2**: no absolute pitch, formant, envelope beyond a frame, embedding, speaker count or synthetic-voice
score; the studio-regular and read-like quantities are never computed per creator.

**Stored per recording** (private, `audio/private/features/`): 1-s block counts and statistics, nucleus times, pause
intervals, class counts outside recognized speech, per-edge local discontinuity scores and recording-level covariates.
No audio, no waveform, no spectrogram, no text.

## 3. The battery (r3-P08; meas's merged criteria 1 to 7)

Built from 60-s own-voice clean-interior excerpts (own-solo definition) of up to 16 development creators, one recording
each, chosen by seed (`pass_audio.battery_selection`), held in memory during the pass; only recovery numbers are kept.

| Criterion | How | Pass |
|---|---|---|
| 1 absolute recovery | 8 inserted floor-level silences of 0.15 to 2 s; time stretch with pitch kept (WSOLA) by 0.85 to 1.15; resampled pitch shifts of +2 and -2 semitones; octave-guard share on clean speech | pauses of 300 ms or more detected at 95% or more, median edge error 20 ms or less; rate error within 3% and recovery slope 0.9 to 1.1; octave errors under 2%; median shift within 0.5 semitones and range of shifted copies within 0.5 semitones |
| 2 robustness by stratum | pink noise at 20 and 15 dB below speech, reverberation (RT60 0.6 s), a music-like bed at -15 dB, a 12-dB quieter copy | criterion 1's rate tolerance holds in the strata the gate admits |
| 3 differential recovery | the bias under the bedded, reverberant and quieter conditions minus the clean bias | under a third of the margin (log 0.074 for rates) |
| 4 null specificity | r3-P09's full pipeline on pseudo-boundaries at matched own-voice edges of the development creators | the band rejects at no more than 10% |
| 5 power | the margin planted into own-voice pseudo-boundaries of the development creators at the real creator count | power 0.8 or more under the floor rule |
| 6 splice classes | same-session cut at a pause, session join, gain step, music-bed onset, spectral change without an edit, against unedited pause points, scored by r4-P03's environment score | AUC 0.8 or more per class; the threshold of r4-P03 is fixed on the null class |
| 7 reliability | split-half (odd and even 15-s chunks) correlation against span length over development own-voice interiors | the minimum span of each measure is the shortest length at which it reaches 0.7 |

**Consequences fixed now.** Rate rows read "beyond the margin" only if criterion 3 holds for rate; they read "within the
margin (B)" only if criterion 1's slope and criterion 3 hold; otherwise at most "undetermined (battery criterion N not
met)". Pitch rows likewise with criterion 1's pitch parts and criterion 3. A null delivery reading in r3-P09 needs
criterion 5. Criteria 4, 5 and 7 run on the stored summaries of the development creators after the pass.

## 4. Shared statistical rules

- **Pool.** Readings are made on the 23 non-development creators only. The development creators (T) are never read for
  any contrast; they serve the battery and every data-tuned part (r3-P12's condition adjustment, r4-P03's threshold,
  r4-P15's feature scales, criteria 4, 5 and 7), which is fitted on T alone. Because no part is tuned on either half,
  both deposited halves stay sealed and each reading is made once on all eligible non-development creators: under tier S
  this is the sealed reading with nothing built on half A; under tier X it is the two-fold cross-fit with T on the
  fitting side in both folds (decision 88), which here is the identity. The tier letter by count is printed beside every
  entry. This reading of the policy, and decision 83's analogy (a rule table written blind from published sources and
  hashed before any count runs once on all non-development creators), are put to the lead.
- **Background gate (A8).** A recording passes when its SBR is 25 dB or more (a music bed or noise within 25 dB of speech
  fails it; the development battery showed large biases at 15 to 20 dB). A span, boundary or onset is gated in when its
  recording passes. **A8:** an entry whose eligible non-development creators after the gate number fewer than 12 prints
  first "not measurable acoustically in this corpus (fewer than 12 eligible creators after the background gate: A8)", and
  its readings are capped at "undetermined"; rows on fewer than 5 creators read "not computed (too few terms or
  creators)".
- **Intervals.** 90%, the t interval on creator means, fixed here (not chosen by the count; decision 62 does not apply,
  decisions 71, 82 and 87), flagged "interval class not calibrated by r3-P30" where no r3-P30 class fits. r3-P12's
  shares use a creator-cluster bootstrap (2,000 draws, percentile), fixed here and flagged the same way. Bands of r3-P09
  are permutation-maximum bands (fixed method).
- **Margins (deposit 2).** Ratio of rates: absolute log ratio 0.223; share difference: 0.05; standardised difference:
  0.20 SD (the unit stated per row); AUC: 0.10 from 0.50.
- **Words** (no deposited direction for any of these entries; step 2's convention): "beyond the margin (<side>)",
  "within the margin (B)", "undetermined", with the A8 and battery caps above. A reading is never a finding.
- **Multiplicity.** No family-wise adjustment. Every output prints the disclosure: 56 primaries; if every true effect sat
  at half its margin about 2.8 readings beyond the margin would be expected by chance.
- **Seeds.** `numpy.random.default_rng([s, k])`, s = first 8 hex digits of SHA-256("audio|<entry>|<name>").
- **Predictions.** Deposit 2's account-prediction cells for all seven entries are "silent"; nothing is scored. et's
  prediction for r3-P11 (no family effect) needs family loadings that this batch does not join: "not computed".

## 5. r3-P12: recording-condition census, covariates only (description; tier S by count)

- **Recordings:** non-development recordings in the pass with feature status ok and 60 s or more of own-voice clean
  interior (own-solo definition). Creators with 2 or more such recordings.
- **Delivery measures** (per recording, over its own-voice clean interiors): acoustic speech rate (log), articulation
  rate (log), long-pause share, F0 range (semitones; Tier 1), intensity variability (dB; Tier 1), recognizer speech rate
  (recognized syllables per second over the same interiors, log), recognizer word probability (mean).
- **Condition covariates** (exogenous): SBR, background level (10th percentile, dBFS), bandwidth (log rolloff), high-band
  share, digital-silence share, clipping share, reverberation proxy, source codec (three classes) and source bit rate
  (log).
- **Statistic:** each measure's creator share of variance (one-way random-effects ANOVA estimator, truncated at 0), raw
  and condition-adjusted (residuals of an ordinary least-squares fit of the measure on the covariates, the coefficients
  fitted on the development creators' recordings only and applied unchanged), with the difference (raw minus adjusted)
  and the covariates' R-squared on the non-development recordings. Interval: creator-cluster bootstrap, 90%.
- **Also:** the gate census (recordings and creators passing the background gate; covariate distributions over creators
  in bins of 5 or more creators). Never printed per creator; never a synthetic-voice screen; no studio-regular row.
- **Plot:** each measure's creator share of variance, raw and condition-adjusted, with intervals.

## 6. r3-P08: acoustic instrument on label-located spans (contrast; tier X by count)

- **Eligible:** non-development creators with 60 s or more of gated clean claimed interiors and of gated clean own
  interiors (primary definition; excluded formats out).
- **Five instruments, one contrast** (per creator, pooled interiors by side; claimed-over-own log ratio):
  I1 the run recognizer's rate (recognized syllables per second of interior time); I2 the larger recognizer (rv-R3's
  bridge decode, only on its recordings); I3 the shifted grid (BR-GS's re-decode, only on its recordings); **I4 the
  acoustic nucleus speech rate (primary, A1)**; I5 recognized syllables per nucleus (A4, deletion).
- **Rows besides:** acoustic articulation rate; long-pause share (shared channel, A2: never counted as convergence);
  F0 range (A3, two-sided); intensity variability; a same-recording row (recordings holding both voices); the negative
  control (own voice in the first 60 s of admitted speech against own-voice interiors after it, log ratio of I4).
- **Reading of the primary:** "beyond the margin (claimed faster / slower)" needs the interval beyond 0.223, I1 in the
  same direction, the negative control within the margin, I5 within the margin (no differential deletion detected), A8,
  and battery criterion 3; "within the margin (B)" needs the interval inside 0.223, battery criteria 1 (slope) and 3, and
  A8; otherwise "undetermined". I2 and I3 print only on 5 or more creators.
- **Plot:** "one contrast, five instruments": creator-mean log ratios with 90% intervals under I1 to I5, the margin shaded.

## 7. r3-P11: acoustic codebook for audio outside recognized speech (description; tier S by count)

- **Eligible:** non-development creators with a recording in the pass.
- **Description:** creator-balanced class shares (each creator's share of its frames outside recognized speech, then the
  mean over creators) over start-aligned bins (minutes 0-1, 1-2, 2-5, 5-10, 10 to the end) and end-aligned bins (the same
  from the end), and in the 30 s before the first claimed-voice unit of a recording against position-matched shifted
  points (5 per onset, the same tenth, not within 30 s of a voice boundary). The undecidable share (digital silence and
  excluded) is always printed. Cells under 5 creators are not printed.
- **Plot:** stacked class shares over start- and end-aligned bins, and before onsets beside shifted points.

## 8. r3-P09: do voice boundaries sit on changes in delivery or production? (contrast; tier X by count)

- **Boundaries:** cue-free, seam-free, long, gated; entries and exits apart; boundaries with a music-like class share of
  0.5 or more within 5 s, or with a detected environment change (r4-P03's rule), leave the delivery rows and are counted.
- **Features:** voiced-frame primaries: articulation rate (log) and F0 range (semitones); pause-tied (shared channel):
  long-pause share, which alone never yields O1.
- **Estimand (sustained shift):** the feature over 10 to 60 s after the boundary minus over 60 to 10 s before it; the
  local discontinuity and the 30-s window row (5 to 30 s) are secondary. Per creator: mean over its boundaries of the
  boundary shift minus the mean shift of its matched edges.
- **Curves and band:** the feature in 10-s windows from -60 to +60 s; null curves from pseudo-boundaries at local
  shifts within the same tenth of the same recording (seeded, 200 draws); each (feature, window) cell standardised by its
  null SD; one permutation-maximum band per boundary type (90% quantile of the maximum absolute standardised cell).
- **Readings (A5, A6):** O1 "boundaries sit on a change of delivery beyond framing words" when a voiced-frame feature's
  creator-mean sustained shift has its interval beyond the margin (articulation: log 0.223; F0 range: 0.20 between-creator
  SD of own-voice F0 range, the SD from T) and its curve leaves the band; O2 "no change of delivery detected" when every
  voiced feature's interval is inside its margin, every cell inside the band, and criterion 5's power is 0.8 or more;
  otherwise O3 "undetermined". Production (A6): share of boundaries with a detected environment change minus that share
  at matched edges (margin 0.05), with the undecidable share printed (from r4-P03).
- **Plot:** small multiples (features by entries and exits), cue-free column (cue-opened not computed), with the band and
  the matched-edge curve.

## 9. r4-P03: splice and acoustic-environment census at voice boundaries (description with an exclusion rule; tier X)

- **Boundaries:** every voice boundary (primary definition) with 10 s of span each side in a processed recording (no
  rate gate); matched non-boundary edges as in section 1.
- **Detected environment change:** r4-P03's environment score (per-band distance of the background spectrum, 10 s each
  side, 0.5 s left out next to the edge) at or above the threshold fixed at the 95th percentile of the score at the
  development creators' non-boundary edges (5% false-positive rate on the null class). Undecidable: digital silence over
  half of either side, or under 0.3 s of background on either side.
- **Statistic:** per creator, the share of decidable boundaries with a detected change minus the share at matched edges;
  creator mean, t interval, margin 0.05. Printed with the undecidable shares and battery criterion 6's AUC per class.
- **Exclusion rule (hashed here, used by r3-P09 and r4-P15):** a boundary with a detected environment change leaves the
  delivery rows.
- **Plot:** creator-level shares of boundaries with a detected change against matched edges (distributions over creators
  in cells of 5 or more), undecidable share beside.

## 10. r4-P15: delivery at self-attributed voice switches (contrast; tier X by count)

- **Boundary curves:** all long, seam-free, gated voice boundaries (cue-free and cue-opened together) without a detected
  environment change; the same estimand and matched edges as r3-P09; one row per voiced feature.
- **Own-range ladder (A7; primary):** per creator with 60 s of gated claimed interiors and 2 or more gated recordings
  with 60 s of own-voice interior: features articulation rate (log), F0 range, intensity variability and long-pause
  share, each scaled by the between-creator SD of own-voice recording values fitted on T; D_co = mean over own recordings
  of the Euclidean distance between the claimed pooled profile and the recording's own profile; D_oo = mean distance over
  pairs of own recordings. Contrast: D_co minus D_oo (SD units), margin 0.20. **Negative control:** the same distance
  between the first and second halves of own-voice interiors within a recording (mean over recordings), which must be
  smaller than D_co for "beyond the margin". "Beyond the margin (claimed outside the own range)" reads "a delivery change
  by the same speaker"; "within the margin (B)" reads "the claimed voice lies within the creator's ordinary range of
  delivery".
- **Closest acoustic work (N13):** a laboratory within-subject comparison of trance channellers reading one story (Wahbeh
  et al. 2019), named in the README.
- **Plot:** boundary curves against matched edges; the own-range ladder (D_oo, D_co, negative control) over creators.

## 11. r4-P16: the non-speech layer before claimed-voice onsets (part a; description; tier X by count)

- **Onsets:** claimed-voice onsets with 30 s before them in a processed recording.
- **Windows:** the frames outside recognized speech in the 30 s before each onset; references: position-matched points
  (5 per onset, same tenth, same recording, not within 30 s of a boundary) and length-matched own-voice onsets of the
  same creator (span length within a factor of 2), which carry the breathing that precedes any long utterance (N14's
  control); a template stratum (onsets within the first 60 s of a recording) is printed apart.
- **Rows:** stacked class shares (creator-balanced) beside the references, undecidable share printed; breath-like share
  before claimed onsets minus before own onsets (margin 0.05; words as in section 4). Descriptive class names only;
  never "induction" or "trance onset".
- **Part (b)** (a filter rule on what the recognizer writes over wordless vocalisation) is text work, a.1, and not run
  here.
- **Plot:** stacked class shares before onsets beside the references.

## 12. Privacy and outputs

The common rules' privacy section binds (cells of 5 or more creators, no per-creator rows or points, count forms against
every printed count and the fixed counts, decision 62, recoverable values, wording, solvers before finishing). Never
printed: audio, waveforms or spectrograms of a recording, any per-recording or per-creator value, absolute pitch. Every
output carries the agnosticism sentence and the line that acoustic features describe the recordings' sound, never a
speaker's state or a source. Outputs per entry under `audio/<id>/` (public/, README.md, contacts.md, status.json, code/);
plots in the CHANGE group's style at 200 dpi, PNG without text chunks, PDF without document information.

## 13. Code fixed with this file (SHA-256)

| File | SHA-256 |
|---|---|
| `common/code/acommon.py` | 0ea79a48e7ba54d3aa2079051e388dd9e860035915dec524ab10eae52ba1fdc3 |
| `common/code/extract_labels.py` | 1bce0fe7e9eedc8bdaf920deb2015a3019ca8f3fb59155b904809617ea4d3d02 |
| `common/code/eligibility_audio.py` | 848b6a7e99af84f6179e3af878a026ad6c3ea9de8804d94c25adcdbd8b4794cc |
| `common/code/locate.py` | 149e2fca29813317e011cf45c81a7c246a8f8a9ab097850ebb6714fe03319c6d |
| `common/code/instrument.py` | a81a6161d4c73607242775bc7c7df3900ef01d673dade19dccfa3c552ed64de2 |
| `common/code/features.py` | 7a06903b156930ec2042d3ccf6d89c639321af420dde67bcd49d2bdefc46f864 |
| `common/code/measures.py` | 719f92017d3f799d8b9f9e97a3c74452a5f4dc82e7a0c3fbd90235d591fd04d3 |
| `common/code/battery.py` | daf672ae7024bf424a17852fe6f1d9a4a44495c54977e819843fe6124fdfa0b1 |
| `common/code/pass_audio.py` | c0025542ac03c0b7fab34f67c60ad0e7465204c036beb4f63bcb1a7bcc46a223 |
| `common/code/devtest.py` | a002cf24080240de1d0af06c8fb132b7e48f507a1d61d73ecf20c502784b9944 |

Analysis code written after this file implements sections 4 to 11 as stated; any departure is logged in the entry's
README with its time.
