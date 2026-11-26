# Audio entries, common folder: the pass, the instrument, the battery and the privacy checks

Written by the audio agent, a model agent working for the project lead (not a person); times from `date -u`. The audio
entries of the third-round programme (class a.2, under the lead's ruling 4: Tier 0 and Tier 1 audio for seen recordings
already on Drive, with the owner's archive; Tier 2 closed): r3-P12, r3-P08, r3-P11, r3-P09, r4-P03, r4-P15 and r4-P16.
**Exploratory; not a test of H1-H10.** Seen creators only. Voice labels are model-coded and not checked by a person;
comparisons between instruments are agreement, never accuracy. Acoustic features describe the sound of these recordings
(delivery and recording conditions), never a speaker's state or a source; recovery was checked on constructed audio only
(an upper bound); no person listened. No model or API call, no GPU lease (no GPU work was needed), nothing installed, no
git commit.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.

## Order

1. 15:08Z to 15:12Z: the outcome-free label extract and eligibility (`code/extract_labels.py`, `code/eligibility_audio.py`;
   no audio, no acoustic value).
2. 15:18Z to 15:25Z: a development test of the instrument on four development creators' recordings (tuning pool T only;
   every development output deleted before the pass; what was seen is stated in the prespecification, section 0.2).
3. 15:27:51Z: the one prespecification for the seven entries hashed, before the pass and before any outcome (published
   as the redacted copy `../prespec.public.md`, with `../prespec-hash-record.public.md`; the hash is kept privately,
   step-1 decision 49 item i).
4. 15:28:00Z to 17:58:03Z (2 h 30 min wall time): the acoustic pass, one heavy job under `run_locked.sh` (`code/pass_audio.py`).
5. 17:58:33Z to 18:07:13Z: the census and the background gate first, then the entries; then publication, the privacy checks and
   the status files.

## The pass (`code/pass_audio.py`, `code/merge_ledgers.py`)

| Item | Value |
|---|---|
| Seen recordings with a voice record (units equal to the voice file) | 1,284 |
| In the pass (not a conversation or multi-presenter format; at least one admitted unit) | 895 recordings, 335.4 hours of audio, 18.06 GB |
| Of them, the non-development creators' | 224 recordings, 77.0 hours |
| Processed | 895; failures 0; copy or SHA-256 failures 0; processed twice 0; every one with a feature file |
| Compute and copy time (summed over recordings) | 2.35 hours of compute; 1.29 hours of Drive copy |
| Wall time | 15:28:00Z to 17:58:03Z |

Each recording was copied from Drive (rclone) to a private temp folder, its SHA-256 checked against the run
ledger's audio key, decoded, summarised and deleted; never more than 2 audio files per worker. Free commit memory was
checked before each recording.

**Sharding (at the coordinator's request, 15:45Z).** The single pass was stopped cleanly after 117 recordings (STOP
file), and the rest split by stem parity into two workers with their own temp folders, ledgers and logs (the instrument
and feature code unchanged; only the orchestration of `pass_audio.py` changed, so its SHA-256 differs from the one in the
prespecification's section 13: a departure, stated; the version hashed then is kept privately). The second worker was
started at 7.2 GB of free commit memory and stopped itself twice under the 6-GB rule (after 26 and 2 recordings); its
remaining 365 recordings then ran alone after the first worker ended. The merged ledgers show no recording processed
twice.

| Segment | Recordings | Time (UTC) |
|---|---|---|
| single pass | 117 | 15:28:00Z to 15:45:29Z |
| worker 0 (even stems) | 385 | 15:45:45Z to 16:51:04Z |
| worker 1 (odd stems), two runs stopped by the 6-GB rule | 28 | 15:46:15Z to 15:50:41Z |
| worker 1, the rest, alone | 365 | 16:51:08Z to 17:58:03Z |

**No GPU lease.** No GPU work was needed (every Tier 0 and Tier 1 feature runs on the CPU), so no lease was taken. The
historical lease and pause marker were checked unchanged by SHA-256, against the values `lease_control.py` checks.

## The instrument (prespecification section 2)

numpy and scipy only (librosa and parselmouth are not installed in the guarded venv; nothing was installed). PyAV 16.0.1,
already installed in the ASR environment, decodes as the corpus run did (mono 16 kHz, back-to-back 30-s windows); it is
read from the ASR environment's site-packages by the guarded venv's Python (a departure, stated). Every sample outside
admitted time (units labelled as another participant, other material, unseparated conversation or cannot tell, and the
gaps next to them) is set to zero before any feature is computed, and conversation and multi-presenter recordings are not
copied at all, so no third party's voice is processed.

- **Tier 0:** level, digital silence, acoustic pauses, syllable nuclei after de Jong and Wempe (2009), syllabic
  modulation, spectral flatness, bandwidth, background spectrum, reverberation proxy, rule-based classes of frames
  outside recognized speech.
- **Tier 1:** F0 in semitones relative to the recording's own median (a YIN-type tracker after de Cheveigne and Kawahara
  2002; the median itself is never stored), intensity variability and spectral tilt over voiced frames.
- **Nothing of Tier 2:** no absolute pitch, formant, envelope beyond a frame, embedding, speaker count or synthetic-voice
  score.
- **Stored per recording** (private, `audio/private/features/`): 1-s block statistics, nucleus times, pause intervals,
  class counts outside recognized speech, per-edge local scores and recording-level condition covariates. No audio,
  waveform, spectrogram or text.

## The battery (meas's merged criteria; `code/battery.py`, `code/battery_post.py`)

Constructed audio from 60-s own-voice clean-interior excerpts of 10 to 19 development creators (one each, chosen by
seed), held in memory only; criterion 7 on the development creators' stored summaries; criteria 4 and 5 in r3-P09. The
table is `../r3-P08/public/data-r3-P08-battery.csv`.

| Criterion | Result |
|---|---|
| 1 absolute recovery | met for pause detection, octave errors and pitch shifts; not met for pause edges (25 ms), rate error at the extreme stretches and the rate slope (about 0.45) |
| 2 robustness by stratum | not met (reverberation biases rate by about +0.07 log) |
| 3 differential recovery | met for rate; not met for pitch range |
| 4 null specificity | met (about 6%) |
| 5 power at the margin | met (about 0.80) |
| 6 splice classes | met for session joins, music-bed onsets and spectral changes; not met for same-session cuts and gain steps |
| 7 reliability | minimum span 60 s for every measure, 120 s for F0 range |

Consequences fixed in the prespecification: acoustic rate rows cannot read "within the margin" (criterion 1's slope),
pitch-range rows cannot read either way (criterion 3), and r4-P03's census sees background changes only.

## Tiers and the pool (prespecification section 4)

| Entry | Tier by count (outcome-free, 23 non-development creators) | How it ran |
|---|---|---|
| r3-P12 | S | once on all eligible non-development creators; the condition adjustment fitted on the development creators only |
| r3-P11 | S | once on all eligible non-development creators (no data-tuned part) |
| r3-P08 | X | once on all eligible non-development creators; the standardisation unit fitted on the development creators |
| r3-P09 | X; cue-opened column D: not computed | as r3-P08 |
| r4-P03 | X | the detector's threshold fixed on the development creators' non-boundary edges; read once on the non-development creators |
| r4-P15 | X | the ladder's feature scales fitted on the development creators; read once on the non-development creators |
| r4-P16 | X | once on all eligible non-development creators (no data-tuned part) |

The tier prints as its letter only (the lead's decision 111).

**Departure from the split policy's wording** (accepted as the lead's decision 106.1, decided 2026-11-26 18:16Z). Deposit
2's split policy builds a data-tuned rule on exploration half A and runs it once on sealed half B (tier S), or cross-fits
it over the two halves (tier X). Here every data-tuned part (the shared instrument's development test, r3-P12's condition
adjustment, the standardisation units, r4-P03's threshold, r4-P15's feature scales, battery criteria 4, 5 and 7) is fitted
on the tuning pool T (the development creators, exploration side, never read for any contrast) only, never on either
half, and each reading is made once on all eligible non-development creators. Under tier X this is the cross-fit with T
on the fitting side in both folds (decision 88 as written); under tier S (r3-P12 and r3-P11, two descriptions that carry
no reading) it departs from the wording "run once on the sealed half". Reason: T sits on the exploration side and is
never read for a split reading, so fitting on T alone keeps both halves out of every fit. **Limitation: half B is no
longer sealed for the acoustic measures described here.** (Dated note, 2026-11-26 18:16Z: the lead accepted this reading
as a departure from the policy's wording, decision 106.1.)

## Shared code (`code/`)

| File | What |
|---|---|
| `acommon.py` | paths, constants, statistics helpers, writing |
| `extract_labels.py`, `eligibility_audio.py`, `locate.py` | the outcome-free label extract, eligibility and location rules |
| `instrument.py`, `features.py`, `measures.py` | the instrument, the per-recording summary, span and edge statistics |
| `battery.py`, `battery_post.py` | the known-answer battery and its criteria |
| `pass_audio.py`, `devtest.py` | the pass and the development test |
| `adata.py`, `bshared.py`, `osr.py` | shared analysis code (gate, matched edges, boundary curves, class shares) |
| `scan_audio.py`, `audio_blanks.py`, `gate_record.py` | privacy scans (identifiers, PNG and PDF metadata; banded and withheld rows); the gate record |
| `readme_tables.py`, `write_readmes.py`, `finalize_audio.py` | README tables and texts, status files and contact logs |
| `publish_prespec.py`, `pubheader.py` | the published, redacted prespecification and its hash record; the CSV headers' prespecification line (decisions 111 and 112) |

## Privacy checks (all before the files were finalised)

| Check | Result |
|---|---|
| zsolve, qscan_all2, whole_position_scan (copies of the release scans pointed at the publishable audio files) | 0 rows flagged; no table holds quantiles |
| s1_blanks (d62) and s1_shape routes on these tables (`code/audio_blanks.py`) | 16 files, 146 rows; 52 rows with a banded or withheld creator count (21 of them withheld); 21 rows with a printed estimate or interval, each with a method fixed in the prespecification; 0 with a count-chosen method; 0 estimates on fewer than 5 creators or on a withheld count |
| s1_carried on every CSV | 0 rows testable |
| s1_predk and s1_chain | not applicable (they read r3-P32's columns); s1_blanks, s1_blanks_p01, s1_shape, s1_seen, s1_profile, s1_bucket and s1_bucket_p01 read step 1's file names and test nothing here; s1_crossval and s1_p27: nothing testable |
| identifier scan (`code/scan_audio.py`: seen creator codes, audio hashes, video ids, the pass's recording and creator stems; 88 files, code included; the published prespecification copies) | 0 files with an identifier; a wider needle set (the independent check's scan) on the 50 publishable files: 0 |
| PNG text chunks; PDF document information | 0 of 5; 0 of 5 (the two entries under A8 publish no figure) |
| nesting by membership against every printed set (decisions 92.1, 95.4 and 103) | checked privately; no count is printed here |
| sums and complements; withheld values; hygiene (copies of the release scans) | 0 sums or complements flagged; withheld-value hits are chance matches of numbers, listed for the eye; 0 private paths, 0 PNG chunks, 0 PDF information |
| cells withheld under the privacy rule | one label, "not printed (privacy rule)", whatever the reason; in the stacked class shares such a class is counted in "other sound, unclassified"; values that could narrow a banded count or rebuild a withheld cell are not printed |
| the two entries under A8 (r3-P09, r4-P15) | every estimate, interval and reading row reads "not printed (A8: fewer than 12 eligible creators after the background gate)"; no figure |

## Change by the lead's decision 109

2026-11-26T19:28:21Z (UTC, from the clock), after the independent privacy check of the seven audio entries. No number
changed: values are withheld, merged, re-banded or reworded, and the figures are redrawn by each entry's own code (the
two entries under A8 publish none).

- The departure from the split policy's wording is printed here and in every entry's README with its reason and its
  limitation, as the lead accepted it (decisions 106.1 and 109.5).
- The Drive remote's name and the historical lease hashes are dropped; the identifier scan's file count is corrected (the
  scan before the fix pass read 91 files, not 74; it reads 87 now, the two A8 entries' figures being withdrawn).
- The privacy-check table is rerun and corrected: one label for every withheld cell, with zero and 1 to 4 carriers alike,
  now also on r4-P03's undecidable shares.
- Shared code changed: `osr.py` (the floor rule), `audio_blanks.py` (the new count forms and withheld labels),
  `write_readmes.py` (rerunnable; the entries' README texts) and `finalize_audio.py` (contact logs without the remote's
  name, the label lines, dated notes); each entry's own code as its README states. The prespecification is unchanged; its
  hash record gains the exploratory label as a note below the record.
- Every hash in `status.json` is refreshed; `status.json` now also lists the prespecification and its hash record.

## Change by the lead's decision 111

2026-11-26T19:37:45Z (UTC, from the clock). No number changed.

- The prespecification is published as a redacted copy, `../prespec.public.md`, and its hash record as
  `../prespec-hash-record.public.md` (made by `code/publish_prespec.py`): outcome-free counts print as tier letters only.
  The original stays private and unchanged and is not published (step-1 decision 49 item i); `status.json` lists the
  published copies and, under `not_published`, the originals.
- Outside the prespecification the tier prints as its letter only: in this README's tier table, every entry's "How it
  ran" line and every `status.json`. r3-P09's cue-opened column reads its tier letter, D (README and CSV headers).
- The identifier scan reads the published copies; every hash list is refreshed.

## Change by the lead's decision 112

2026-11-26T19:49:16Z (UTC, from the clock). No number changed. The original prespecification's hash is printed in no
published file: it was hashed at 15:27:51Z (UTC), before the pass and before any outcome; the hash is kept privately
(step-1 decision 49 item i).

- Every CSV header cites `../prespec.public.md` with that sentence (rewritten by `code/pubheader.py`; every entry's code
  and `code/battery_post.py` rerun for their headers only; each CSV differs from its earlier version in that one line).
- `status.json` files cite the published copy instead of a hash; `../prespec-hash-record.public.md` keeps the hashing time
  and the hashes of the code fixed with the prespecification (its section 13), not the original's hash.

> No measure in this study can tell whether a non-human source speaks; every measure describes the speech in these
> recordings and how the creators present it.
