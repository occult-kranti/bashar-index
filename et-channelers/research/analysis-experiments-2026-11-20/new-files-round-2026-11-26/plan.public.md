> **Published copy, redacted (2026-11-27).** This copy differs from the private original in four kinds of redaction only: private path tokens read "(a private path)"; the count of non-development (tier-L) creators is withheld; the standing rule on a small printed group is given only in its generic form; and one exact recording count of a banded set is written as its band. Every other word is as hashed. The original was hashed at 2026-11-26T22:49:35Z (UTC); its hash is kept privately (step-1 decision 49 item i; decisions 112, 113 and 122).

# The new-files round: plan (descriptive persistence on new recordings of the seen creators)

Written 2026-11-26 between 22:45:03Z and 22:49:27Z (UTC, from `date -u`; drafting began after the scope count at 22:13:09Z) by a planning agent working for the project lead (a model
agent; not a person), under the lead's decision 118.1 and the brief (a private path).
Plan only: no measure was computed on the new files, and no new transcript's text was read. The hash and its time are in
`plan-hash-record.md`; every read made for this plan is in `contacts.md`.

**Status.** Exploratory; not a test of H1-H10. A descriptive persistence check on new recordings of the seen creators:
not a confirmation, not a fresh-creator wave. Every measure planned here is rule-based or recognizer-based and is not
checked by a person; no model-coded label of a new recording exists, and none is made.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

**Privacy of this file.** It holds private paths, so it is private. If it is ever published, it is published as a
redacted copy and the hash recorded in `plan-hash-record.md` stays private (step-1 decision 49 item i; decisions 112 and
113). Counts of recordings and creators are printed only as bands. No creator, channel, person, id or title appears.

**Path shorthands.** RUN = (a private path);
PANEL = (a private path); REL = the release on main,
`et-channelers/research/analysis-experiments-2026-11-20/results/exploratory-2026-11-21/`; PMAIN = the panel folder on
main; R2 = (a private path); PRB = (a private path);
PRD = (a private path); EX = (a private path); SH =
(a private path);
NU = (a private path); L50 =
(a private path); NF = this folder.

---

## 0. What this round is, and what it is not

- **The owner's step.** The owner's order of work (2026-11-26, about 04:50 UTC) puts "another round" on the new files
  after the latest-20+ analysis. That analysis is complete (decision 117). The owner chose "Round now, no more ASR"
  (decision 118.1): the round runs on the transcripts that exist, with no further transcription.
- **Descriptive, same creators.** It asks one question per measure: do the seen creators' new recordings give a value
  inside a margin, fixed now, of the value the latest-20+ release or programme printed? The answer words are "persists",
  "shifts" and "undetermined" (section 3).
- **What it is not.**
  - It is not a confirmation. A wave of the same roster tests persistence only (programme 2.0; rv-R2; the lead's
    rulings, "Also decided"). rv-R2's plasmode found that once a seen look passed, a wave of the same creators passes a
    0.005 test in 4.6 to 10.8% of cases (REL `built/rv-R2/public/rv-r2-plasmode.csv`), so agreement here is expected
    more often than it would be on fresh creators.
  - It is not a test of H1-H10. No registered hypothesis statistic is computed (H3's statistic, rv-R1 / H3-SEEN, is
    left out on purpose; section 2.4).
  - It is not a fresh-creator wave. No class-b card is tested. r3-P20's registered reliability prediction (card b4)
    is NOT tested: no instrument is re-run, because no model call is allowed. r4-P20's rider on later uploads is not
    scored (section 2.4).
- **What the plan agent has seen before writing.** The published aggregates of the release, steps 1 to 5, the audio
  entries, the addendum and deposits 1 to 4 (all on main), the private code and READMEs of the entries named below, and
  the outcome-free fields listed in `contacts.md` (ledger rows, file lists, channel folders, durations, listing ranks,
  receipt field names, deposit 2's split membership for the 23 non-development creators). No new transcript, no new
  value, no hold-out or other-group file.

---

## 1. Scope

### 1.1 Sources

| Source | Folder | Ledger | Method (from the transcription scripts' code) |
|---|---|---|---|
| New uploads | (a private path) | (a private path) | Corpus English-only model and settings ((a private path) CONFIG), back-to-back 30-s windows, English channels only. The three files of the whole-file first version ((a private path)) were redone and are never used. |
| Latest-50+ | (a private path) | (a private path) | The same method and model; stopped on the owner's instruction at 14:56:45Z. |

Each transcript JSON holds `duration_s`, `info.language` ("en", set, not detected), `info.duration_after_vad`, and
`segments[]` with `id, start, end, text, words[{start, end, word, probability}], avg_logprob, no_speech_prob,
compression_ratio` (field names read from the writing code, not from any file).

### 1.2 How a new recording is mapped to a creator, and dropped

1. Read only the two ledgers (fields `video_id`, `channel_dir`, `status`, `audio_sha256`, `duration_s`) and the queue
   columns `video_id`, `channel_dir`, `listing_rank` (and `upload_date_approx`, presence only).
2. A recording's creator is its `channel_dir`. Its group is read from (a private path): seen, hold-out,
   other, or unlisted. Development membership (the tuning pool T, 48) and the 23 non-development creators (tier L) are
   read from deposit 2's split record ((a private path), the programme's normal use, decision 111.5;
   logged).
3. **Kept:** status `transcribed` and group `seen`. **Dropped before any text is read:** every other group, every
   skipped or unlisted row.
4. **Duplicates.** A video in both ledgers is kept once, as its new-uploads copy (the earlier one), and its latest-50+
   copy is never opened. Rule fixed now.
5. **Overlap with the corpus.** No new recording's video id or audio hash appears in the corpus ASR manifest
   ((a private path)), so no seen recording is counted twice (checked; 0 overlaps).
6. The result is one **allow-list manifest** ((a private path), written by stage 0, hashed
   before extraction): one row per kept recording, with creator, source, path, duration, listing rank and audio hash.
   The round's loader opens only paths on that list. It never lists or globs a transcript folder: the folders also hold
   hold-out and other-group transcripts (section 1.4).

The plan-stage count script is (a private path) (SHA-256
`c1861bf2a5176832099c8a0698087a28a35deb9d1a43703e249a558e8cff7085`). It reads only the fields above, opens no transcript,
and printed exact counts to the planning agent's scratchpad only.

### 1.3 Counts, in band form

Bands are chosen so that each leaves 5 or more admissible values against every other band here and the fixed counts
(101, 71, 48, 23, 18, 12, 11, 6, 36). They are re-checked by the solvers before anything is published (section 5).

| Set | New uploads | Latest-50+ | Both sources (each recording once) |
|---|---|---|---|
| Recordings of seen creators kept | 60 to 69 | 180 to 199 | 250 to 259 |
| Seen creators with a kept recording | 30 to 39 | 60 to 69 | 65 or more of the 71 |
| Of them, non-development (tier L) | not computed or not printed | not computed or not printed | not computed or not printed |
| Audio of kept recordings | about 20 hours | about 85 hours | about 105 to 110 hours |

- Latest-50+ kept recordings by listing position at the 25 November listing: 30 to 39 at positions 1 to 20, 150 to 159 at
  positions 21 to 50. Most latest-50+ recordings are therefore **older** uploads than the latest-20 set, while every
  new-uploads recording is **later** (uploaded after the latest-20 capture). The round compares other recordings of the
  same creators, partly later and partly earlier; section 3.5 keeps the two sources apart as secondary rows.
- Fewer than 5 recordings of seen creators appear in both sources; each is kept once (rule 1.2.4).
- Seen creators with 3 or more kept recordings (the all-seen eligibility rule of section 3.4): 60 or more of the 71.
- Kept recordings per creator: most creators have 3 or 4; very few have more than 5. The latest-20+ corpus held about
  17 per creator.

### 1.4 Facts the lead should know (outcome-free)

1. **245, not 246.** The latest-50+ ledger holds 266 rows: 245 `transcribed` and 21 `skipped_non_english_channel`.
   Exactly 245 transcript files exist, one per transcribed row. One partial audio copy sits in (a private path) and was never
   transcribed. With the duplicates, the two sources hold 324 distinct transcribed recordings, not 330.
2. **Hold-out and other-group transcripts sit in the same folders.** Both transcription jobs transcribed every English
   channel, so 50 to 59 distinct recordings of hold-out creators and 10 to 19 of other-group creators were transcribed
   into (a private path) and (a private path). The round never opens them (rule 1.2.6). The lead may wish to ask
   the owner whether they should be moved into a sealed folder. Nothing is moved or deleted by this plan.
3. **Language was set, not detected.** Each new recording was transcribed as English because every corpus recording
   of its channel was English. A recording in another language would not be caught. No screen can be added without
   reading text or a model, so this is a stated limitation.
4. **Dates and page fields.** New uploads carry an approximate upload date in their queue; latest-50+ rows carry none.
   Every kept recording has a platform metadata object (JSON) recorded in its Drive receipt, but none is stored
   locally: reading page text, view counts or confirmed upload days needs a copy from the project's own Drive
   (decision 2 in section 8).
5. **Machine state at writing.** At 22:37Z the guarded venv refused to start (3.0 GB of commit left; 3.3 GB by the
   system count). A heavy job was running, probably the GPU re-decode of decision 118.3. The round's jobs wait for the
   guard (section 7).

### 1.5 Never opened

(a private path), (a private path), (a private path), any reliability folder, every transcript of a hold-out,
other or unlisted creator, the forecast ledger (a private path), and the whole-file first-version transcripts. No
recursive text search runs over RUN. Each contact is logged in the group's `contacts.md` with a `date -u` time.

---

## 2. Measures

### 2.1 How the original code is reused

- **One adapter, no edits to code of record.** (a private path) turns a manifest row into exactly what the
  original loaders return for a corpus row:
  - `prep.load_words(row)` returns `(info, words)`. The adapter builds `info` with: language "en";
    `model_role` "english_only"; `audio_seconds` = `duration_s`; `speech_seconds` = `info.duration_after_vad`;
    `publisher_audio` False. It applies the artefact filter **v2**, loaded by path from (a private path) and
    checked by hash, to the segments with `duration_s`; then `prep.without_ellipses`; then `prep.build_units` for units
    (8 to 40 words).
  - Unfiltered segments go to the measures that read them (thanks phrases, window phase), as in the originals.
  - Filter **v1** ((a private path), hash-checked by the frozen H3 code) feeds E3 only, as published.
  - Listing order (for split-halves) comes from the manifest's listing rank.

  The adapter keeps the seen guard: it refuses any row whose creator is not a seen creator, and any path not on the
  manifest.
- **New caches, never the caches of record.** Every cache the round builds lives under (a private path) with a new
  name. The original caches (rv-words, rv-features, the RX seen-units cache, the GRID extract, the HOLD2 seen cache, the
  r3-P42 extract and counts) are read only, for the old side of paired rows and for the equivalence step.
- **Equivalence step, before any new file is opened.** For every planned row, the round's code path is first run on the
  latest-20+ inputs.
  - **Rows whose instrument is unchanged** (G1 to G3 except r3-P02) must reproduce the published value to its printed
    decimals. A row that does not reproduce stops: "not computed (the round's code does not reproduce the published
    value)".
  - **Rows whose label-free form changes the instrument** (r3-P02's units; every G4 row, whose token sequences are
    whole recordings instead of label-unit runs; r3-P61's unit seconds): the label-free re-run on the old recordings,
    P', is computed and printed beside the published value P. Such a row is read for persistence only if P' lies
    inside P's persistence margin (or in the same band region). Otherwise it reads "not comparable (the label-free form
    moves the published value beyond its margin on the same recordings)".

  The equivalence results are hashed before any new value is computed.
- **Base rules stay the originals'.** For example: RX 150 or more words; pace 60 s of speech and 200 or more words; TM,
  CH and CSS 300 or more (as each original states); E3 its 180-s trims, 600 s and 800 words after trims, ten bins of
  50 or more words; E1 its non-final windows of 20 or more words with a window in each half. These are applied at
  extraction, before any outcome, and the eligible counts are fixed then (section 4).
- **Quantiles are never printed for the new sets**, whose counts are banded (D67, D70): no creator median, quartile or
  decile. Where a published headline is a quantile (rv-R4's pace median, rv-D2-H's medians, ENTRY-E1's median
  position), the row is left out or replaced by the creator-equal mean that the release also prints.

### 2.2 Measures to compute

Columns: published latest-20+ value with its interval as printed, and its source (REL = release, PMAIN = panel folder on
main); the published creator set; the code reused; the margin type (section 3.2: S share, R ratio, C correlation or
agreement, M registered value margin, B band region, D described); and whether a paired within-creator row is planned
(P).

**G1. Recognizer, seams and silence** (`NF/recognizer-seams/`). New-set rule: all-seen (section 3.4).

| # | Measure | Published value (interval, method) and source | Published set | Code reused | Margin | P |
|---|---|---|---|---|---|---|
| G1.1 | rv-R7: share of a creator's English transcripts with a thanks phrase starting 27 to 30 s into a window, creator-equal | 0.4939 (0.4466 to 0.5412, 90% t over creators); REL `built/rv-R7/public/rv-r7-prevalence-and-seams.csv` (rv-R4's `thanks_late` 0.49392 is the same quantity) | 71 seen, 1,284 transcripts | (a private path) (via the adapter), (a private path) | M: 0.05 (rv-R4's registered margin) | yes |
| G1.2 | rv-R7: removals by the positional rule per speech hour, creator-equal | 3.019 (2.721 to 3.318, 90% t); same file | 71 | as G1.1 | R | yes |
| G1.3 | rv-R7: within-segment word gaps that are exactly zero (filter v2) | 0.9053 (0.9018 to 0.909, 90% creator bootstrap); same file | 71 | as G1.1 | S | yes |
| G1.4 | rv-R7: pauses of 0.3 s or more that fall at a segment boundary (filter v2) | 0.3871 (0.3763 to 0.3989, 90% creator bootstrap); same file | 71 | as G1.1 | S | yes |
| G1.5 | GRID: grid-made share of all pauses of 0.3 to 30 s | 2.976% (2.809 to 3.163, 90% creator bootstrap); REL `gallery/figures/GRID/data-grid-made-pauses.csv` | 71, 1,211 transcripts | (a private path), `analyse.py`, `grid_common.py` | R | yes |
| G1.6 | GRID: stand-alone thanks segments starting 27 to 30 s into a window | 80.61% (77.18 to 83.91, 90% creator bootstrap); REL `gallery/figures/GRID/data-thanks-window-phase.csv` | 71 | as G1.5 | S | no (pooled) |
| G1.7 | E1: chance per window of the inserted thanks phrase, slower half against faster half of a recording (articulation rate) | pooled ratio 1.326 (1.164 to 1.510, 90% two-stage bootstrap); creator-equal 1.140 (0.913 to 1.448); REL `packages/ER/e1-thanks-by-tempo.csv` | 71, 1,230 recordings | (a private path), `e1_analyse.py`, `ercommon.py` | R (E1's registered 0.80 to 1.25, applied around the published value) | no |
| G1.8 | r3-P02, all-voice described rows: sentence marks per word ending 0-1, 1-2, 2-5 and 5-15 s from a run-grid seam; the 0-1 minus 5-15 contrast; D5's chance of a sentence mark after gaps under 0.3 s, 0.3 to 1 s and 1 s or more; D5's coupling; share of segment starts in second 0 of a window | 0.1252 (0.122 to 0.1285); 0.0592; 0.0576; 0.0584 (0.0563 to 0.0605); contrast 0.0668 (0.0644 to 0.0693); D5 0.0215 (0.0199 to 0.0231), 0.4527 (0.4349 to 0.4706), 0.6304 (0.6122 to 0.6487); coupling 0.6089 (0.5907 to 0.6271): all t on creator means, "described, not read"; segment starts bin 0: 0.1744 (0.1695 to 0.1793); PMAIN `step1/r3-P02/public/r3-P02-described-rows.csv`, `data-r3-P02-window-phase.csv` | 71 | (a private path) (its all-voice functions); units from `prep.build_units` on the new transcripts in place of the label files' units (an instrument change: P' rule of 2.1) | R for values under 0.25, S otherwise | yes |
| G1.9 | rv-D3: share of audio outside recognizer segments (filter v2), creator-equal; share outside the voice detector's speech, creator-equal | 0.149 (0.118 to 0.180, 95% t) and 0.122 (0.087 to 0.156, 95% t); REL `built/rv-D3/public/rv-D3-share-without-speech.csv`. Beside them, rv-R4's `nonspeech` baseline, 0.11812 (0.09854 to 0.14089, 90% creator bootstrap; 1/n recording weights) | 71, 1,293 transcripts | (a private path) logic via the adapter, (a private path), `dcommon.py`; (a private path) for the rv-R4 row | R for the rv-D3 rows; M 0.025 for rv-R4's row (registered) | yes |
| G1.10 | rv-D3: speech coverage of the first and of the last 15 s, all lengths | 0.7472 (95% sup-t 0.6803 to 0.8141) and 0.4892 (0.4009 to 0.5776); REL `built/rv-D3/public/rv-D3-aligned-coverage.csv`. rv-R4's `end_coverage_15s` baseline 0.48873 (0.43138 to 0.54394) | 71 | as G1.9 | M 0.05 (rv-R4's registered end-coverage margin, used for both ends) | no |

**G2. Pace, register and variance** (`NF/pace-variance/`). New-set rule: all-seen.

| # | Measure | Published value and source | Published set | Code reused | Margin | P |
|---|---|---|---|---|---|---|
| G2.1 | rv-R4: pace ICC (creator share of variance, words per minute of speech) | 0.57789 (0.48113 to 0.64148, 90% creator bootstrap); REL `built/rv-R4/public/rv-r4-specifications.csv` (the same value as rv-R5's pace 0.5779 and CH-H's 0.5789) | 71, 1,211 | (a private path), `r4_weighting.py` | M 0.10 (registered) | no (a set statistic) |
| G2.2 | CH-H: pace, creator-equal mean (words per minute) | 148.5759 (145.1369 to 152.0148, 90% t); REL `packages/HOLD2/CH-H-variance-shares.csv` | 71, 1,176 | (a private path) logic via the adapter, `chh.py`; (a private path) | M 5.0 words per minute (rv-R4's registered pace margin) | yes |
| G2.3 | CH-H: creator-equal means of contraction rate, first-person singular, first-person plural and second-person rates (per 1,000 words) and word length | 28.5678 (25.8156 to 31.3201); 28.2734 (25.5666 to 30.9803); 16.9774 (15.2494 to 18.7054); 48.3701 (44.9537 to 51.7864); 4.3093 (4.2705 to 4.3481); all 90% t; same file | 71, 1,176 | as G2.2 | R | yes |
| G2.4 | CH-H: mean log words per recording | 7.7229 (7.5836 to 7.8623, 90% t); same file | 71 | as G2.2 | additive 0.223 (R on the log scale) | yes |
| G2.5 | CH-H: ICCs of the G2.3 and G2.4 measures | contraction 0.6157 (0.5151 to 0.6883), word length 0.581, log words 0.4318, first-person singular 0.2887, first-person plural 0.3884, second person 0.425 (90% creator bootstrap); same file | 71 | as G2.2 | C 0.10 | no |
| G2.6 | rv-R5: raw ICCs of contractions, mean ln word probability, non-speech share, mean segment log-probability, MATTR-500, first-person singular, second person, question marks, segments ending in "?", repeated five-word share, log length, ln word probability per segment | 0.7208, 0.2117, 0.5521, 0.4021, 0.5861, 0.5331, 0.4309, 0.6211, 0.4427, 0.3678, 0.4492, 0.2674 (95% creator bootstrap printed; the round prints 90%); REL `built/rv-R5/public/rv-r5-icc.csv` | 71, 1,211 (MATTR 1,106) | (a private path), `features.py`, `extract_seglogprob.py` (segment `avg_logprob` is in the new JSON) | C 0.10 | no |
| G2.7 | E3: articulation rate, edge tenths against middle tenths; second-person address, last tenth against first | 1.000 (0.993 to 1.007, 90% two-stage bootstrap); 1.341 (1.195 to 1.493); REL `packages/ER/e3-edges-and-address.csv` | 61 seen, 558 recordings | (a private path), `e3_report.py`, with (a private path)'s frozen feature code fed by the adapter (filter v1; its frozen-file hashes checked). No H3 statistic is computed. | R | yes |

**G3. Wording patterns, entrances, topics and vocabulary** (`NF/patterns-topics/`). New-set rule: all-seen.

| # | Measure | Published value and source | Published set | Code reused | Margin | P |
|---|---|---|---|---|---|---|
| G3.1 | RX: ten family rates per 1,000 words, creator-equal | A frames 0.4143 (0.3387 to 0.4899); B reporting 0.408 (0.3019 to 0.514); C address 1.0924 (0.87 to 1.3148); D time 2.5841 (2.1495 to 3.0187); E stance 12.4112 (11.7443 to 13.078); F asks 0.8417 (0.6295 to 1.0539); G names v0 3.8651 (3.1148 to 4.6153); H numerals 5.1908 (4.591 to 5.7907); I questions 6.009 (5.3082 to 6.7098); J framing cues 0.1066 (0.0517 to 0.1614); all 90% t; REL `packages/HOLD2/RX-H-pattern-rates.csv` (family rows). J holds r3-P03's frozen framing cues (the cue locator's rules, hashed in round 2's RX patterns), so this is the label-free form of that locator. | 71, 1,229 | (a private path), `rxmatch.py`, `normalise.py`, `patterns_v1.py`, `stats.py`; (a private path) | R | yes |
| G3.2 | RX: relative rate of greetings in the first tenth and of person sign-offs in the last tenth | 8.1854 (7.4081 to 9.0196); 9.8034 (9.1484 to 10.4267), 90%; REL `packages/HOLD2/RX-H-position-edges.csv` | creators with 5 or more hits (as printed there) | as G3.1 | R | no |
| G3.3 | ENTRY-E4: share of a creator's recordings with a first entrance cue, versions 1 and 2 | v1 0.086 (0.054 to 0.118), v2 0.076 (0.044 to 0.107), 90% t over creators; REL `gallery/figures/ENTRY-H/data-entryh-first-cue.csv` (the release's two-stage v1 0.0863, 0.0534 to 0.1217, in `gallery/figures/ENTRY/data-entry-how-common.csv`, printed beside) | 71 | (a private path), `entry_patterns.py`, `entry_patterns_v2.py`, `entry_match.py`, `entry_match_v2.py`, `analyse.py` | R | yes |
| G3.4 | ENTRY-E2: hits per 1,000 words in the first tenth of running time, handover and greeting cues (v1) | 0.52688 (0.08794 to 1.24888); 0.47682 (0.11503 to 0.98515), 90%; REL `gallery/figures/ENTRY/data-entry-where.csv`, panel B | 71 | as G3.3 | R | no |
| G3.5 | ENTRY-T: share of a creator's self-introductions using "we", by name group (v1) | being or collective in the NAMES list 0.3398 (0.1894 to 0.4921); capitalised name in no list 0.4643 (0.25 to 0.6786), 90% creator bootstrap; REL `gallery/figures/ENTRY/data-entry-i-we-by-group.csv` | seen creators with self-introductions | as G3.3 (groups from the frozen NAMES list; no model call) | S | no |
| G3.6 | TM: topic shares of the 16 topics under the frozen transform, creator-equal | e.g. topic 2 0.1009 (0.0865 to 0.1148); all 16 rows with 90% creator bootstrap in REL `packages/HOLD2/TM-H-topic-shares.csv` | 71, 1,185 recordings | (a private path), `tm_prep.py`; (a private path) with the frozen transform (a private path) and name mask v0 | R | yes |
| G3.7 | CSS-12 census, whole recordings: share of a creator's recordings with any consciousness-shift term; terms per 10,000 words; the same for secret-control terms; both lists in one recording; numbered dimensions or densities (share and rate) | 0.594 (0.537 to 0.645); 10.10 (8.73 to 11.57); 0.102 (0.074 to 0.130); 1.01 (0.55 to 1.54); 0.082 (0.060 to 0.108); 0.242 (0.201 to 0.286); 3.38 (2.53 to 4.28); 90% creator bootstrap; REL `packages/CSS/css12-census.csv` | 71 | (a private path), `css_analyse.py`, `csscommon.py`, lexicon (a private path) | S for 0.594; R for the others | yes |
| G3.8 | rv-R4: five term cue shares (share of a creator's recordings with the term) | 0.58657 (0.53006 to 0.64241); 0.59907 (0.54624 to 0.65575); 0.40773 (0.3533 to 0.46487); 0.28464 (0.23569 to 0.33487); 0.15044 (0.11657 to 0.18935); 90% creator bootstrap; REL `built/rv-R4/public/rv-r4-specifications.csv` | 71, 1,229 | (a private path), `r4_weighting.py` | M 0.05 (registered) | yes |

**G4. Lexicon, tier L** (`NF/lexicon-tier-L/`). The deposit-3 lists through (a private path) (it refuses
any list file whose hash differs from deposit 3), on non-development creators only (tier-L rule, section 3.4). Token
sequences are whole recordings (no label units), so every G4 row is an instrument change and takes the P' rule of 2.1.
Years are normalised by the frozen rule coder's `normalise_years`, called by the matcher; the coder's other fields have
no published value that rests on rules alone, so they are not a separate measure (section 2.4).

| # | Measure | Published value and source | Published set | Code reused | Margin | P |
|---|---|---|---|---|---|---|
| G4.1 | r3-P42: concentration (creator random-intercept variance, gamma-Poisson moments) of the 15 computed classes, with the published placebo band | L01 S02 2.633 (band 0.049 to 1.21, above); S03 0.228 (0.031 to 0.461, inside); S04 1.111 (0.056 to 0.774, above); S06 1.29 (0.089 to 1.016, above); S13 2.027 (-0.016 to 0.991, above); S14 1.52 (0.077 to 0.717, above); L03 DIM 1.165 (0.042 to 0.651, above); L06 SHIFT 0.508 (0.034 to 0.796, inside); L10 MODE-HIGHERSELF 0.247 (-0.27 to 1.836, inside); MODE-RELAY 0.255 (0.095 to 2.909, inside); L11 ENDORSE 0.262 (-0.124 to 1.855, inside); L12 DISSEM 0.07 (-0.225 to 1.966, inside); L14 AUTHORITY-C 0.773 (0.61 to 6.851, inside); PRICE 0.181 (0.139 to 2.167, inside); SOCIAL-D 4.365 (-0.38 to 1.686, above); PMAIN `step2/r3-P42/public/data-r3-P42-classes.csv` | 23 | (a private path) (rebuilt through the adapter with new file names), `count_p42.py`, `analyse_p42.py` (`st_phi`), `p42common.py` | B (the published placebo band's region); the original rule's final reading on the new files is printed beside, described | no (pooled) |
| G4.2 | r3-P49: pooled control set (L05's counted terms after every set-aside, CR-A left out) | phi 3.254 (placebo band 0.102 to 1.125, "excess over matched placebos"); creator-balanced rate 1.554 per 10,000 tokens; PMAIN `step2/r3-P48/public/data-r3-P49-concentration.csv` | 23 | (a private path) (`eval_set`), `desc_common.py`, `extract_desc.py` (its 23-creator assertion replaced by the tier-L rule's set) | B for phi; R for the rate | rate: yes |
| G4.3 | r3-P43: survival strip (entry year of each dated layer against the share of creators using it) | reading "no dated order beyond the null" (placebo band -0.668 to 0.406; date-permutation band -0.763 to 0.789); the rank correlation is never printed (decision 86.2); PMAIN `step2/r3-P43/public/data-r3-P43-readings.csv` | 23 | `analyse_p42.survival()` | B, reading only: the new rank correlation is computed privately and only its reading word prints | no |
| G4.4 | r4-P26 (a): creator-level co-presence (mean number of composition parts used) | 6.09 (placebo 6.09 to 7.00; pseudo-strata 5.57 to 7.00), "no excess co-presence over placebos"; computed parts only 2.30 (2.26 to 2.65; 1.35 to 2.43); same file | 23 | (a private path) (`copresence`) | D (depends on recordings per creator; section 3.2) | no |
| G4.5 | r3-P44: the 15 computed layer pairs, z against the curveball null blocked by audience band | P017 -1.1, P018 -1.2, P020 0.7, P028 -0.1, P029 -0.5, P031 -0.4, P033 -1.1, P041 0.5, P042 1.9, P045 -1.2, P053 -1.5, P054 -0.5, P074 -0.2, P075 0.7, P119 0.2; every pair "no structure beyond the null and placebos"; PMAIN `step2/r3-P44/public/data-r3-P44-pairs.csv` | 23 (audience bands from deposit 2's split record) | `analyse_p42.pairs()`, `curveball()` | B (the null's no-structure region as the original rule defines it); stratum rows print readings only | no |
| G4.6 | r3-P42: A4 collision cells and coder-shared shares | every printed cell of PMAIN `step2/r3-P42/public/data-r3-P42-collisions.csv` (e.g. L06 by L01 0.762, 0.636 to 0.849; L05 by L01 0.419, 0.102 to 0.538; L01 by L06 0.098, 0.06 to 0.147; L10 by L09 0.138, 0.088 to 0.194) and the coder shares of `data-r3-P42-lists.csv` | 23 | `analyse_p42.py` | S at 0.25 or more, R below | no |
| G4.7 | r3-P51: model-free named-actor proxy, all speech, creator-balanced runs per 10,000 tokens | 30.902 (no band); PMAIN `step2/r3-P51/public/data-r3-P51-proxy.csv` | 23 | (a private path) (the all-speech row) | R | yes |
| G4.8 | r3-P40: named-year timeline, all voices pooled, creator-balanced mentions per 100,000 tokens, years drawn where 5 or more creators name them | 2000 0.811; 2012 1.581; 2008 1.347; 2020 2.268; PMAIN `step3/r3-P40/public/data-r3-P40-timeline.csv` | 23 | (a private path) (its timeline function only, without its ledger read), (a private path), deposit 4's `year-roles.csv` | R | yes |
| G4.9 | r3-P61: L14 device rates by position of the unit's midpoint in running time, ladder fixed at the published level | price cue by fifths 2.81, 1.07, 0.75, 1.14, 1.11; devotional social proof by fifths 1.37, 0.73, 0.40, 0.70, 0.82; credential authority by halves 0.56, 0.18 (per 10,000 tokens; "described (no reading: a pilot)"); priced shares never printed; PMAIN `step4/r3-P61/public/data-r3-P61-heatmap.csv` | 23 | (a private path); unit seconds from `prep.build_units` times (an instrument change) | R per cell | no |
| G4.10 | r3-P42 and r3-P53: class statuses (computed, too thin, waiting for r3-P54) of all 67 classes; r3-P53's mode groups (creators with 2 or more cues) | 15 computed, 49 "not computed (too few terms)", 3 "not computed until r3-P54"; higher self "18 of 23"; relay "10 to 19"; PMAIN `step2/r3-P42/README.md`, `data-r3-P42-classes.csv`, `step2/r3-P53/public/data-r3-P53-modes.csv` | 23 | `analyse_p42.class_status`, (a private path) | D (counts; deposit 2: "not a margin quantity") | no |

The thin-class rule (3 or more terms each used by 5 or more creators; deposit 3, r3-P42 prespecification section 3, as
corrected by addendum 2d) is applied to the new files as deposited. A class computed on the latest-20+ recordings that is
too thin on the new files prints "not computed (too few terms or creators)" and counts in G4.10's status changes.
Placebo sets: see decision 7 in section 8.

**G5. Page fields and upload days** (`NF/page-dates/`). Only if the lead allows the Drive metadata copy (decision 2
in section 8); otherwise every row prints "not computed (page fields and upload days of the new recordings are stored
only on Drive)".

| # | Measure | Published value and source | Published set | Code reused | Margin | P |
|---|---|---|---|---|---|---|
| G5.1 | PT (a): page cue shares, creator mean | other platform 0.4127 (0.325 to 0.5003); event 0.393 (0.3211 to 0.4649); course 0.3592 (0.2854 to 0.433); platform engagement 0.3335 (0.2527 to 0.4143); payment 0.2139 (0.1355 to 0.2922), 90% t; REL `gallery/figures/PT/data-pt-page-cues.csv` | seen with page metadata, 1,228 | (a private path), `ptcommon.py`; (a private path) | S at 0.25 or more, R below | yes |
| G5.2 | META (b): share of recordings with creator-written chapters | 0.139 (0.088 to 0.189, 90%); REL `gallery/figures/META/data-field-coverage.csv` | 71, 1,411 | (a private path) | R | yes |
| G5.3 | r3-P60: destination classes from page links, share of links | own-site residual 0.642; platform self-links 0.129; other social 0.094; membership and donation 0.056; booking and courses 0.034; PMAIN `step4/r3-P60/public/data-r3-P60-rows.csv` | 23 | (a private path), `lexmatch.match_link` | S at 0.25 or more, R below; creator counts D | no |
| G5.4 | r3-P40: years by role at upload (other passed years by decade; years open at upload) | 1990s 1.102; 2000s 1.565; 2010s 4.92; 2020s 4.454; open 2020s 19.925; open 2030s 0.848 (per 100,000 tokens); PMAIN `step3/r3-P40/public/data-r3-P40-timeline.csv` | 23 | as G4.8, with upload years | R | no |

### 2.3 Not computed in this round (needs labels or an audio pass)

Each of these prints "not computed in this round (needs labels or an audio pass)" in the index's not-computed table.

- **Release outputs that read model-coded labels or model readers:** LAB-V, LAB-A, LAB-F, LAB-S, LAB-T, LAB-K, LAB-H;
  TL-P, TL-BUILD, TL-7.1 to TL-7.9; TIME; NE; DIR; KA; TC; RXP; ENTRY-MC; VER-A, VER-GC, VER-SHARD, VER-3R, VER-DEP,
  VER-CAL, VER-MV; DR-2; GATES; CAL; CAL-f; MTMM; RX-CB; MR-18c; MR-18d; nlp-R7, nlp-R9, nlp-R10, nlp-R11, nlp-R13; E2;
  E5; E6; E8; E9; E11; E12; PT-cd; PT (b); CSS-5; CSS-10; CSS-12's voice rows; rv-L1, rv-L2, rv-L3.
- **Programme step 1:** r3-P01 (every family A and B row is claimed minus own; family C needs a second decode),
  r3-P02's primaries I, II and IIa and every voice or grid-shift row, r3-P03's published contrast (its locator's cues
  run label-free inside G3.1), r3-P04, r3-P05, r3-P06, r3-P07, r3-P19, r3-P20, r3-P21, r3-P23, r3-P26, r3-P27, r3-P32,
  r3-P33.
- **Step 2:** r3-P42's voice, title-profile and economy rows and L09; the L01 composition test (its groups are creator
  profiles from model-coded titles; decision 8 in section 8); r3-P43's by-voice composition and balances; r4-P26 (b);
  r3-P45 (not computed on any tier); r3-P46; r3-P48 (nothing computable on tier L); r3-P50 (page text and titles; G5
  only if allowed); r3-P52 (model-coded recording kinds and voice); r3-P55; r3-P56; r4-P29 (thin on tier L; its voice
  and economy rows need labels).
- **Step 3:** r3-P36 / r4-P21, r3-P38 / r4-P24 and r4-P23 (they rest on the frozen ledger's model-coded candidates);
  r3-P37's word-anchored row (it codes ledger statement text); r3-P40's by-voice, class-3 and biography rows.
- **Step 4:** r3-P57 / r4-P32 (asks and recording kinds); r3-P58 (its recording set needs voice and asks labels).
- **Step 5:** r3-P14, r3-P15 / r4-P13, r3-P16, r3-P17, r3-P18 (no published value of the footing locator is
  label-free), r4-P14 (every row is by voice side).
- **Audio entries and addendum (an audio pass):** r3-P08, r3-P09, r3-P11, r3-P12, r4-P03, r4-P15, r4-P16; the addendum's
  r3-P01 part E, r3-P13, r3-P14's acoustic part, r3-P15's acoustic rungs, r3-P16's delivery rows, r3-P17's acoustic
  primary and r4-P06's acoustic column.
- **A second decode or a reference:** BR-b, BR-y, BR-GS, rv-R3, r3-P01's family C and q values, r3-P02's grid-shift and
  bridge rows (the GPU re-decode of decision 118.3 covers seen recordings only).

### 2.4 Not computed, for other reasons (fixed now)

| Output | Reason printed |
|---|---|
| rv-R1 / H3-SEEN / H3-X | not computed: a registered hypothesis's statistic; this round tests no hypothesis |
| DC, SD, CM, META (a) rhythm, rv-R4's window and posting-rate rows, r3-P37's date-only rows, r3-P65 | not computed: these read spans of dated uploads within a channel, and the new files hold about one dated later upload per creator (and no confirmed day for the latest-50+ batch) |
| r4-P20's rider on later uploads (deposit 2's account-prediction cell) | not scored: the later uploads span about a week, far below r3-P37's 10 days per creator; it stays a rider on a later collection |
| COR; CH-H's Mantel views | not computed: the within-channel half and the Mantel views need 5 or more recordings per creator, which very few creators reach in the new files |
| TM-H's channel-leak NMI | described only, not read: it depends on how many recordings each creator contributes |
| NAMES | not computed: the frozen name store's variant forms were adjudicated by a model; forms new to these transcripts would stay unadjudicated, so the variant share would not be comparable |
| META (c), r3-P58's later part | not computed: view and reaction counts of uploads a few days old are not comparable with counts at equal age |
| rv-D2-H's covariates, rv-R4's pace median, ENTRY-E1 | not computed: their published values are creator quantiles, which are never printed over a banded count (D67, D70); G2.2 prints the creator-equal pace mean in their place |
| ENTRY-E3 | described only, and only if 5 or more creators qualify (16 creators and 25 recordings in the release) |
| E13 | not applicable: a hold-out measure |
| TABLE / rv-D1 | replaced by this round's own scope table (G0) |
| rv-D2, rv-R2, rv-R6, CAL, r3-P30, r3-P01's tolerance arm | not a persistence target: group balance, simulation or calibration, not a description of the recordings |
| Deposit 2's rule coder, as a measure | no published value rests on the coder alone (its printed fields all rest on model-coded candidates), so there is nothing to persist against; it enters only through `normalise_years` (G4) |
| E4, E7, E10 and every other output not run in the release | nothing to persist against |

---

## 3. The persistence rule (fixed now, before any new value is read)

### 3.1 The primary rule

For each row: P is the published value copied in section 2.2 (a fixed number), M its margin (section 3.2), and [L, U]
the new value's 90% creator interval by the fixed method of section 3.3.

- **Additive margins (S, C, M):**
  - "persists" when P - M <= L and U <= P + M;
  - "shifts" when U < P - M or L > P + M;
  - otherwise "undetermined".
- **Ratio margin (R),** with M = 0.223 on the log scale (0.80 to 1.25):
  - "persists" when L >= P / 1.25 and U <= 1.25 P;
  - "shifts" when U < P / 1.25 or L > 1.25 P;
  - otherwise "undetermined".
  - A lower bound at or below zero cannot persist.
- **Band region (B).** The published reading's region is bounded by the published band edges (below the 5th
  percentile, inside, above the 95th).
  - "persists" when [L, U] lies wholly inside that region;
  - "shifts" when [L, U] lies wholly inside another region;
  - otherwise "undetermined".
  - Rows whose statistic is never printed (G4.3) print the word only.
- **Described (D):** no persistence word. The new value is printed beside the published one and, for statistics that
  depend on how many recordings a creator contributes (G4.4, G4.10), beside an exposure-matched old reference. That
  reference is the central 90% of 200 seeded draws of k recordings per creator from the creator's latest-20+
  recordings, where k is the creator's number of new recordings; it is computed and hashed before any new value.
- **Not computed:** fewer than 5 eligible creators, or a class too thin under the deposited rule.
- **Instrument changes:** the P' guard of section 2.1 applies first.

P is treated as fixed: its own interval is printed beside it but does not enter the rule. The comparison is not
independent of P, because the new recordings come from the same creators.

### 3.2 Margins, in order of precedence

1. **A margin the output registered itself:**
   - rv-R4's margins: 0.05 for the thanks phrase, end coverage and term shares; 0.025 for non-speech; 0.1 for the pace
     ICC; 5.0 words per minute for pace;
   - E1's 0.80 to 1.25.
2. **Deposit 2's margins by measure type** (`lead-margins-and-readings-2026-11-26.md`):
   - S, a share or probability of 0.25 or more: 5 percentage points;
   - R, a rate, a ratio, a count per words, or a share under 0.25: 0.80 to 1.25 (deposit 2's ratio
     margin, so that small shares are not read on an absolute scale that cannot fail);
   - C, an ICC, correlation or agreement coefficient: 0.10;
   - a log-scale quantity (G2.4): 0.223 additive.
3. **B, a band region,** for rows that the original reads against a placebo, pseudo-strata or null band: the published
   band edges.
4. **D, described:** counts of creators or classes, and statistics that depend on exposure. Deposit 2: "not a margin
   quantity".

### 3.3 Intervals

- **The method.** Each row uses its original output's own interval method at the 90% level, with fixed settings: t on
  creator means; creator bootstrap percentile with B = 2,000; two-stage bootstrap with B = 2,000. Band-region rows use a
  creator bootstrap percentile with B = 1,000.
- **Seeds.** The round's seed is 2026112603. An original's own seed is kept where it has one.
- **Why fixed.** No method is chosen by the creator count, so decision 62 does not withhold banded rows.
- **Flag.** Every row carries "fixed method; interval class not calibrated by r3-P30 for new recordings of seen
  creators".

### 3.4 Eligibility and within-creator pairing

**Who enters a row** (outcome-free; fixed at extraction from ledger fields and each original's base rule, before any
outcome).
- **All-seen rule (G1 to G3; G5.1, G5.2).** A seen creator enters with 3 or more new recordings in the measure's base.
  - On the plan-stage counts this set lies 5 or more below the 71, so neither the primary nor the paired rows nest
    within 1 to 4 of the published set.
  - If, after a measure's base rule, its new set nests within 1 to 4 of the published set or of any printed set
    carrying the same measure (checked by membership, privately, before any outcome), that measure's new rows are
    withheld under the one label.
- **Tier-L rule (G4; G5.3, G5.4).** Two branches, fixed now; the lead chooses one before computation (decision 1 in
  section 8).
  - **Branch A**, if the lead rules that a statistic computed only on new recordings is not "the same measure" under
    decision 103: a non-development creator enters with 2 or more new recordings.
  - **Branch B**, the default, literal reading: a non-development creator enters with 4 or more new recordings.

**Paired within-creator rows** (where column P says yes).
- **The pair set.** The creators in both the published set and the new set.
  - All-seen measures: the all-seen rule (3 or more new recordings).
  - Tier-L measures: 4 or more new recordings in both branches.
- **Old value.** o_c is the creator's value on their latest-20+ recordings in the measure's base, recomputed from the
  caches of record. The recomputation must reproduce the published value on the full published set first.
- **New value.** n_c is the creator's value on the new recordings.
- **Additive types (S, M).** Read the creator-equal mean of n_c - o_c, with a 90% t interval on creator values, against
  plus or minus M.
- **Ratio type (R).** Read the ratio of the creator-equal means of n_c and o_c over the pair set, with a 90% creator
  bootstrap (B = 2,000), against 0.80 to 1.25.
- **Reading words.** "persists within creator", "shifts within creator", "undetermined".
- **Set statistics** (ICCs, pooled shares, band-read rows) have no paired row.
- **When a pair set is withheld.** It is withheld under the one label, whatever the data show, if it nests within 1
  to 4 of:
  - the published set;
  - any printed set carrying the same measure;
  - any printed group that it would lie within 1 to 4 of (the standing rule, generic form).

  This is checked by membership, privately, before any outcome.

### 3.5 By source (secondary rows)

The primary pools both sources, each recording once. Secondary rows split them:
- "later uploads" (the new-uploads source);
- "other uploads" (the latest-50+ source, mostly older).

Each uses the same rule and eligibility inside the source and prints only where 5 or more creators qualify. They have no
paired rows and no persistence word of their own; they are described beside the primary. Season is a named confound:
the later uploads fall in one week of late November.

### 3.6 Wording, multiplicity and what the words do not mean

- **"persists"** means only that the new recordings' value lies within the stated margin of the printed one, as an
  equivalence description at one-sided 5% per bound. **"shifts"** means only that it lies wholly outside. Neither word
  is a finding, a replication or a confirmation. Neither says anything about H1-H10, or about whether any non-human
  source speaks.
- **Multiplicity.** No family-wise adjustment is applied. There are on the order of 120 persistence rows, so some
  "shifts" readings are expected by chance alone. Shared creators make "persists" more likely than it would be for fresh
  creators (rv-R2).
- **Required wording.** Rule-based and recognizer-based; not checked by a person. "Agreement", never "accuracy". Neutral
  wording for offers, asks and prophecy. Never "failed" for a date.
- **Not a confirmation.** "This is not a confirmation, not a test of H1-H10, and not a fresh-creator wave; r3-P20's
  prediction is not tested here."

---

## 4. Tiers, splits and how creators are counted

- **The halves do not apply.** Deposit 2's halves were drawn to guard rules tuned after the deposit: a sealed half B
  read once. The new files are new recordings of the same seen creators, so deposit 2's halves do not apply as a
  sealed check:
  - every rule run here is frozen code, or a deposited list, whose published value was already read;
  - no rule is tuned in this round;
  - new recordings of a creator in half B are not sealed material for anything.

  **So the round runs no split.** Each measure runs once on the eligible seen creators of its published set: all seen
  creators for release measures and r3-P02, and non-development creators for tier-L measures. Every row carries its
  original tier letter and the words "new recordings of seen creators; descriptive, no split". The tier-S entries read
  on half B (r3-P37, r3-P65) are not computed (section 2.4). No row is printed by half, fold or roster vintage.
- **How creators are counted.**
  - A creator is a channel folder of the seen roster (`creator-sets.json`), counted once across both sources.
  - A creator enters a row under the rules of section 3.4, which use only ledger fields and the original base rules.
    Those counts are fixed at extraction, before any outcome, and recorded in each group's prespecification.
  - Creator-equal means weight each creator once, whatever their number of new recordings.
- **Bands.**
  - No exact count is printed that nests 1 to 4 apart with any published set: the release, steps 1 to 5, the audio
    entries and addendum, deposits 2 to 4, the fixed counts, or E5's earlier exact counts kept in git history
    (decision 104 B2).
  - Counts take the standard forms ("all N" only when true, or a band leaving 5 or more admissible values under the
    strict standard).
  - The tier-L counts are not printed.
  - Recording counts are not creator counts (step-2 decision 70 item 2), but they are banded here too.

---

## 5. Privacy plan

**The rules every output follows** (decisions 62, 63, 70, 86, 92, 95, 97, 103, 104 and 109 to 116):

- **One label for withheld rows.** A computed row that is withheld reads exactly like one that was not computed:
  - "not computed or not printed" in its count, method and status cells;
  - listed with the not-computed rows;
  - with no note saying why, or that it nests (decision 104 B1).

  Privacy notes are general ("values that could narrow a banded count are not printed"). The standing rule is
  printed only in its generic form (decision 97.3).
- **Zero and 1 to 4 carriers read alike.**
  - Every count below 5 reads "fewer than 5", with a header saying "0 to 4" (decision 103 N2).
  - A class cell with 0 or 1 to 4 carriers reads "not printed (privacy rule)" (decisions 92.2 and 109.3).
  - A share whose numerator comes from fewer than 5 creators is not printed.
  - Terms are named only where 5 or more creators use them, in the new files and in the published run.
- **The strict band standard (decision 92.1).** Every banded count must keep 5 or more admissible values once every
  printed count, band and nesting is taken into account. That covers this round, the release, steps 1 to 5, the audio
  entries and addendum, deposits 2 to 4 and the fixed counts. A count that fails is banded wider, or withheld where no
  band can leave 5 values (decision 111.2).
- **The standing rule.** No statistic is printed on any subset of a printed group that lies within 1 to 4 of it.
- **Decisions 62 and 63.** Interval methods are fixed (section 3.3). Any row whose count is banded and whose method
  would depend on the count is withheld, with its reading.
- **No quantiles over banded counts (D67, D70).**
  - No creator median, quartile or decile.
  - Histograms only with bins of 5 or more creators.
  - No per-creator row, point or slope.
- **No recoverable values.**
  - No group means that, with an overall mean, would solve for a group size. The by-source rows and the pooled rows are
    run through `sums_complements.py` and zsolve.
  - No pattern of blank cells that depends on the data.
  - No value in one file that can be matched with a value in another to reveal a withheld count or method.
  - Pooled shares dominated by fewer than 5 creators are not printed (the release's dominance rule, `dominance_release.py`).
- **Redacted copies keep original hashes private** (step-1 decision 49 item i; decisions 112 and 113).
  - A prespecification or README that holds a private path is published as a redacted copy, and the original's hash
    reads "kept privately" in every published file.
  - Before staging, the grep for each such hash must find 0 hits in every publishable file, at full length and at its
    first 16, 12 and 8 characters. That includes this plan's hash.
- **Labels in every output.** Every CSV header, README, contacts.md, status.json and figure caption carries:
  - "Exploratory; not a test of H1-H10.";
  - "New recordings of seen creators: a descriptive persistence check, not a confirmation and not a fresh-creator wave.";
  - "Rule-based and recognizer-based; not checked by a person; agreement, never accuracy.";
  - the agnosticism sentence.

  PNGs carry no text chunks; PDFs carry no document information.

**The checks, in order** (all outputs to (a private path), never published):

1. **Self-checks by each group's code:**
   - the equivalence step (section 2.1);
   - membership nesting of every printed set against the published sets (step-2 and step-5 private memberships;
     deposit 2's split record under its normal use; E5's two sets, decision 104 B2);
   - the standing rule;
   - a blanks audit.
2. **All solvers,** from (a private path), with paths adapted to NF:
   - zsolve, qscan_all2, whole_position_scan;
   - every s1_* (s1_blanks with `d62`, s1_bucket, s1_carried, s1_chain, s1_crossval, s1_predk, s1_profile, s1_seen,
     s1_shape, and the _p01 variants where they apply);
   - the s2_* solvers (rank bands with deposit 3's lists, pseudo-pool, influence complement, L13 additivity, CLR
     identity);
   - nesting_scan / nesting_rebuild, withheld_scan, sums_complements, dominance_release, hygiene_scan.

   No banded row may be left with 4 or fewer values.
3. **The audio checker's scripts,** from (a private path), adapted to NF: `members.py`, `nest_audio.py` and
   `nest2.py`, `audio_blanks_final.py`, `blanks_add_final.py`, `vintage_screen2.py`, `why_narrow.py`, `ident_audio.py`,
   `hashcheck.py`.
4. **The identifier scan** (`pubrules.scan_identifiers`, (a private path)). Its needles:
   - every new recording's audio hash, video id and transcript hash, in every group, hold-out and other included;
   - the corpus audio hashes and video ids;
   - page keys and creator codes;
   - channel folder names;
   - the hashes of every redacted file.
5. **An independent check** by a fresh agent that did not write the round. It is given the code and outputs, not this
   plan's conclusions. It rechecks after every fix pass until its verdict is "publishable".
6. **The lead, then one PR.** Staging only of files whose SHA-256 matches the list after the final verdict, then
   `guard_no_raw_media.py` and `check_counts.py`. Merge only after the CI check is listed and passes (decision 67).

---

## 6. Outputs

```
new-files-round-2026-11-26/
  plan.md, plan-hash-record.md, contacts.md          (this stage)
  README.md                                          short index: scope bands, one table of every row with its
                                                     persistence word, the not-computed table, decisions, labels
  not-computed.csv                                   every output of sections 2.3 and 2.4 with its printed reason
  (a private path)                    the plan-stage count script (hash above)
  common/  code/ (nf_adapter.py, scope.py, persist.py, nfpub.py, style.py), (a private path) (manifest), README.md,
           contacts.md, status.json
  scope/                 G0: the scope table in bands (recordings, creators, hours, sources, listing positions)
  recognizer-seams/      G1
  pace-variance/         G2
  patterns-topics/       G3
  lexicon-tier-L/        G4
  page-dates/            G5 (or a README listing its rows as not computed)
  check/                 never published
```

**Each group folder** holds:
- (a private path), with hashes recorded in status.json;
- (a private path) (caches and per-creator values, never published);
- `prespec.md` with `prespec-hash-record.md`, hashed with a `date -u` time before any outcome of the group. It cites this
  plan's hash, lists the exact rows, code hashes and eligibility counts as bands, and states what was seen before;
- `public/`:
  - CSVs with a commented header carrying the labels;
  - one row per measure: published value and its interval, P' where it applies, new value with its 90% interval and
    method, margin and type, persistence word, paired row (word, plus estimate and interval where printable), set bands;
  - figures as PNG at 200 dpi and PDF;
- `README.md`, `contacts.md` and `status.json`, as in step 1.

**Plots, in the CHANGE style.**
- **Style.** Copy (a private path) unchanged in its tokens: the light surface, the ink and
  muted greys, NEUTRAL_FILL for reference ranges, S1 blue for new values, S2 orange for paired rows, direct labels where
  aqua would fall below 3:1. The label line is replaced by this round's.
- **One "persistence forest" per group.**
  - One row per measure, on a common axis in margin units: log(new / published) / 0.223 for R rows, (new - published) /
    M for additive rows.
  - The persistence band from -1 to 1 shaded NEUTRAL_FILL, the published value at 0, the new value as a dot with its 90%
    interval, the paired row as a second marker where printed.
  - Band-read rows (B) go in their own panel, with the published band shaded and the published value as a hollow marker.
- **What is never plotted:** per-creator points, quantile bars, or bins of fewer than 5 creators.
- **Index summary figure.** A count of rows by persistence word per group, a count of measures and not of creators.
- **Checks.** Every PNG is looked at with the Read tool before staging.

---

## 7. Cost and time

- **Money: none.** No model or API call; nothing is sent to OpenAI (the 130 USD stop stands; no spend to report).
  Nothing is downloaded from any platform. If decision 2 allows it, G5 copies the kept recordings' metadata objects
  (small JSON files) from the project's own Drive.
- **Data size.** 250 to 259 transcripts and about 120 MB of JSON for the kept recordings (both transcript folders
  together hold about 150 MB). That is about a fifth of the latest-20+ corpus (1,293 transcripts, 549.6 hours).
- **Memory and workers.**
  - One worker per job, in the guarded venv (`-I`; default ceiling 4 GB; never ET_GUARD_OFF), wrapped in
    (a private path).
  - Extraction streams one transcript at a time, so the expected peak is under 2 GB.
  - The topic transform, the placebo and pseudo-strata draws, and the bootstraps hold one cache of tens of MB at a
    time.
  - Every job checks free commit first and waits while the guard would refuse (under 6 GB).
  - The GPU re-decode (decision 118.3) is a heavy job. The round's extraction never runs beside it if commit is short,
    and never as a third heavy job.
- **Order of jobs and estimated single-worker times:**
  1. The lead's decisions (section 8). Then (a private path) (the adapter, persist.py, the scope manifest), tested on
     constructed JSON only; manifest hashed. About 30 minutes of writing, seconds of compute.
  2. The prespecifications of G1 to G5, hashed.
  3. The equivalence step on the latest-20+ inputs, read-only caches of record; results hashed. About 20 to 40
     minutes. This includes rebuilding the r3-P42 extract with whole-recording sequences for the P' rows, and the
     exposure-matched references.
  4. Extraction of the new files through the adapter, one heavy job. About 10 to 20 minutes.
  5. G1 and G2 (about 15 to 30 minutes, the ICC bootstraps dominating); then G3 (about 20 to 30 minutes, the topic
     transform and RX); then G4 (about 30 to 60 minutes, 200 placebo sets, 200 pseudo-strata draws, 200 curveball
     draws and the creator bootstraps); then G5 if allowed (about 15 minutes after the Drive copy). One at a time.
  6. Figures and public files, about 15 minutes. Every PNG is looked at.
  7. The solvers, the audio checker's scripts and the identifier scan, about 30 to 60 minutes.
  8. The index README; the independent check (about an hour of agent time per pass); the lead; the PR.

  In all, about 3 to 5 hours of wall-clock compute behind the re-decode, plus the check passes.

---

## 8. Decisions the lead must take before the computation starts

1. **The nesting rule's scope for new-only statistics** (decides G4's branch). Does decision 103's "no statistic of the
   same measure on two groups nested within 1 to 4" cover a statistic computed only on new recordings beside a
   published statistic on older recordings of a superset?
   - Recommended: no (branch A). No published value can be differenced with it to recover a creator's value. Paired rows,
     which reuse old recordings, stay under decision 103 in every case.
   - Default if no ruling: branch B, 4 or more new recordings per creator. Most tier-L classes would then read "not
     computed".
2. **The Drive metadata copy** for G5 (page cues, chapters, r3-P60, and r3-P40's upload-year rows): one read-only copy
   of the kept recordings' metadata objects from the project's own Drive. It is no platform contact, but it is a
   transfer.
   - Recommended: allow it, seen creators only, from the manifest.
   - Default: G5 not computed.
3. **The scope facts.**
   - Confirm that the round runs on the transcripts that exist: 245 latest-50+ transcripts, not 246, and 324 distinct
     transcribed recordings, not 330.
   - Confirm the duplicate rule (the new-uploads copy is kept).
4. **The hold-out and other-group transcripts in the same folders.** Whether to ask the owner to move them into a sealed
   folder. The round's allow-list never opens them either way.
5. **H3 left out** (rv-R1 / H3-SEEN). Confirm it: computing it on seen creators' new recordings would put a registered
   hypothesis's statistic in a descriptive round.
6. **r4-P20's rider on later uploads.** Confirm "not scored" (too few dated later uploads).
7. **Placebo sets for G4's band rows.**
   - Recommended: the persistence word uses the published band edges, as section 3.1 fixes. The new placebo bands for
     the described reading use the latest-20+ run's own placebo term sets where r3-P42's private draw record holds them,
     with the same seeds and rule otherwise; it is stated which.
   - The alternative is to redraw on the new files' vocabulary.
8. **Creator groups carried from stored labels.** Should the L01 composition test and r3-P42's title-profile rows use
   the creators' profile groups from the latest-20+ title labels (model-coded) as fixed creator attributes?
   - Recommended: no. They are not label-free, and the brief excludes them.
9. **Order beside the GPU re-decode** (decision 118.3). Recommended: the round's extraction waits until the re-decode
   ends or commit is back above the guard's floor with margin. Both stay under the two-slot lock.
10. **Deposit 2's split record.** The round reads it twice: once for tier-L membership and audience bands, and once for
    the nesting checks. This is its normal use (decision 111.5), logged in each contacts.md. Confirm.
11. **Publication.** Whether the round is published on main and where. Suggested: under
    `research/analysis-experiments-2026-11-20/panel-third-round-2026-11-22/new-files-round/`, after the independent
    check, in one PR. This plan is published only as a redacted copy, with its hash kept privately.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
