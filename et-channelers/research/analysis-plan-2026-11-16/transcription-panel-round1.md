# Transcription and compute panel — round 1

Prepared 2026-11-16. **Planning and read-only research only.** No model downloads, ASR jobs, package installation, audio uploads, or runtime changes were performed. The operating policy remains English transcription, original-language evidence, a 20 GB total local project footprint with at least 2 GB free within that allowance, and GPU inference with approximately 70% utilization where practicable.

## Decision proposed for the next phase

Use the already verified English captions when their coverage and text quality pass review; retain published and automatic captions as distinct evidence. Run local ASR for missing, blocked, empty, incomplete, or demonstrably inadequate captions. A caption HTTP refusal must remain an endpoint-specific collection state, not a reason to pretend that captions do not exist or to stop unrelated audio work.

The first ASR candidate is a pinned faster-whisper/CTranslate2 GPU stack, one inference owner, `int8_float16`, and batches starting at 1. Compare a quality reference using `large-v3` against a lighter candidate such as `distil-large-v3` or `turbo`; select only one lighter candidate for the initial pilot. NVIDIA Parakeet TDT 0.6B v2 is an English-specific challenger if the local dependency and memory pilot succeeds. No throughput winner can be selected from published benchmarks alone.

Alignment and diarization are later optional passes. They must not occupy the GPU concurrently with ASR on this machine. Analysis can consume already verified text while the next audio item is fetched, but GPU text models must share the same single-owner GPU scheduler.

## Verified local constraints

Read-only commands: `nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version --format=csv,noheader`, CIM system/processor queries, package metadata inspection, and repository reads.

| Observation | Evidence and implication |
| --- | --- |
| GPU | **NVIDIA GeForce RTX 4070 Laptop GPU, 8,188 MiB VRAM**, not 16 GB. Driver 616.56. Initial sample 0 MiB reported in use and 0% utilization. A later temperature sample was 52°C. These are instantaneous observations, not load tests. |
| Power controls | `power.limit` reported unavailable; default/minimum/maximum fields reported 55/5/140 W. These values do **not** prove a writable power limit on this laptop. No power setting changed. |
| Host | Intel Core i9-14900HX, 24 cores/32 logical processors; 34,053,414,912 bytes RAM, approximately 31.7 GiB. |
| Disk | C: had 47,921,369,088 bytes free at the observation. Physical free disk is separate from the user's much smaller project allowance. |
| Local ASR environment | The collection tools virtual environment contains no installed faster-whisper, CTranslate2, torch, WhisperX, NeMo, PyAV, or NumPy distribution. The repository requirement declarations are not proof of installation. |
| Existing storage policy | Current launcher private-root cap is 17,000,000,000 bytes. The earlier operating audit measured 660,454,569 bytes outside that root for tools and checkouts; that measurement predates any ASR dependencies/models and must be repeated before provisioning. |

GPU inference is feasible to investigate. Literal zero CPU use is not: orchestration, hashing, network transport, demuxing, and ordinary audio decoding use the host. Keep those tasks bounded; require the expensive neural inference stages to report CUDA explicitly and stop on unexpected CPU fallback.

## Current corpus and integration gaps

The active native-audio pipeline stores `sync/drive_ingest_manifest.jsonl` and separate `sync/drive_caption_manifest.jsonl`. Exact remote object IDs, byte lengths, MD5, and local SHA-256 support verified audio/metadata pairs and per-track caption ZIPs. Caption provenance distinguishes published from original automatic tracks, retains language and extraction time, and excludes translated `tlang` variants. Raw JSON3/VTT, timed segments, text, and provenance are bundled together. An empty caption response now remains `caption_empty` pending.

`archive_catalog.py` publishes a private, immutable compressed baseline plus receipt deltas and a manifest. Its schema includes channel/person attribution, source tab, archive location/proofs, caption policy, language inventories, unresolved counts, and per-track bundle proofs. This is the better source for a future transcription queue than recursively scanning whatever files happen to remain locally.

The older `catalog.py` distinguishes `publisher_text_status`, `captions_status`, and `asr_status`; `transcript_audio.py` keeps made/source/captions/any counts separate. Preserve that distinction in the new analysis corpus. Caption confidence, ASR token scores, and human verification must never be merged into one unexplained quality score.

The existing [transcribe.py](../../pipeline/transcribe.py) is useful scaffolding, but needs these changes before reuse:

1. `find_jobs` derives the owner from the immediate parent directory. New native paths include `channel/Videos`, `channel/Shorts`, and `channel/Recorded streams`, so this would mislabel owners. Resolve ownership from the receipt/catalog instead.
2. `decode_audio` captures a complete float32 mono waveform in RAM. At 16 kHz this is 230.4 MB per hour, before copies and features; ten hours is 2.304 GB. Decode bounded windows with absolute source offsets and tested boundary handling. Do not exclude long recordings.
3. Defaults are `device=auto`, `compute_type=auto`, batch 16. The new runner needs explicit CUDA, measured compute type, small initial batches, and a failure on CPU fallback.
4. Model download/cache and transcript writes do not use the current shared storage accountant. The old hold files protect deletion by the old sync tool, not necessarily the new collector. A shared lease and admission mechanism is required before concurrent ingest/ASR.
5. Completion is principally keyed by video ID. A new model/configuration must not silently skip an older transcript. Use `(source SHA-256, model revision, decoder/alignment configuration hash, output schema)` as the derivation identity.
6. Current provenance already records model revision, model weight SHA-256, library version, audio/text/JSON hashes, and elapsed time. Extend it; do not discard it. Add selected compute type, CUDA/runtime versions, hardware, VAD settings, chunk offsets, language evidence, and quality-review state.

## Primary-source comparison

| Candidate | Verified capability | Evidence boundary / role |
| --- | --- | --- |
| OpenAI Whisper | General multilingual recognition with English transcription options; official approximate VRAM table lists large near 10 GB and turbo near 6 GB. | Those estimates and relative speeds are not measurements on this laptop. Use as reference architecture; stock large is a poor initial 8 GB configuration. [Maintainer repository](https://github.com/openai/whisper). |
| faster-whisper/CTranslate2 | GPU quantization, batched inference, VAD, and optional word timestamps. | Preferred first pilot because the project already has an adapter and upstream publishes memory/precision comparisons. [Maintainer repository](https://github.com/SYSTRAN/faster-whisper). |
| WhisperX | Forced alignment plus optional speaker diarization; model unloading is documented. | Conditional second pass for selected recordings. Alignment can fail on dictionary-unsupported tokens; overlapping speech and speaker assignment remain imperfect. Alignment does not correct an incorrect transcript. [Maintainer repository](https://github.com/m-bain/whisperX). |
| Parakeet TDT 0.6B v2 | English ASR, punctuation/capitalization, native timestamps, mono 16 kHz WAV/FLAC input. | A challenger, not a promised speedup. Model-card leaderboard average WER is 6.05; its reported RTFx 3380 uses batch 128. Neither transfers to an 8 GB laptop or this vocabulary. [NVIDIA model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2). |
| Parakeet TDT 0.6B v3 | Extends the family to 25 European languages; documented full-attention long-audio example uses an A100 80 GB, with local attention for longer recordings. | Current English-only scope gives no automatic reason to prefer v3. Its listed English benchmark average WER, 6.34, is a separate evaluation result, not a corpus ranking. [NVIDIA model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3), [NeMo checkpoints](https://docs.nvidia.com/nemo/speech/latest/asr/asr_checkpoints.html). |

The faster-whisper README's **published** large-v2 benchmark uses 13 minutes of audio, beam 5, CUDA 12.4, an RTX 3070 Ti 8 GB, and identified software versions. It reports 59 seconds/2,926 MB for unbatched INT8 and 16 seconds/4,500 MB for batch-8 INT8; FP16 batch 8 reports 17 seconds/6,090 MB. These are upstream measurements, not ours, not large-v3 results, and not a 70%-utilization run. Match decoding settings and quality when comparing. [Benchmark and methodology](https://github.com/SYSTRAN/faster-whisper).

A compatibility issue remains unresolved: the fetched CTranslate2 installation page says CUDA 12.x plus cuDNN 8 for speech models, while faster-whisper's current README specifies CUDA 12 plus cuDNN 9 for current CTranslate2 releases. Pin a tested wheel/runtime set and verify supported CUDA compute types in a later isolated smoke test; do not combine these instructions blindly. Windows GPU wheels and Visual C++ runtime requirements are documented. [CTranslate2 installation](https://opennmt.net/CTranslate2/installation.html), [quantization](https://opennmt.net/CTranslate2/quantization.html).

## Scheduling and the approximately 70% target

Proposed topology: one bounded Drive reader → one bounded decode producer → **one GPU model owner** → result validator → one existing quota-aware verified uploader. Prefetch at most one next item initially. CPU-only text normalization and indexing can proceed concurrently with bounded workers. Share the current Drive transfer/rate limits rather than starting a competing uploader.

Start with batch 1, then test 2 and 4. Increase only after measured VRAM headroom and quality checks; never make batch 8/16 the starting assumption. A provisional 6 GiB peak-VRAM target leaves approximately 2 GiB for the display, allocator variation, and other applications. Treat this as an admission target to validate, not a hard allocator guarantee. Unload ASR before alignment/diarization. CTranslate2 documents that same-device parallel streams do not necessarily improve throughput. [Parallel execution guidance](https://opennmt.net/CTranslate2/parallel.html).

Sample utilization, VRAM, temperature, and process activity every second. Control a 30–60 second rolling average around 60–70% using batch size and inter-batch idle time; reduce admission or pause when sustained utilization exceeds the target, memory headroom falls, or the desktop becomes unresponsive. Record both the mean and excursions. Kernel execution can momentarily report 100% even with a lower duty cycle: a strict instantaneous 70% ceiling is not promised. NVIDIA defines utilization as time with kernels executing during the sampling window, not the fraction of GPU capacity reserved. Power limits are watts, not utilization percentages. [NVIDIA monitoring/control documentation](https://docs.nvidia.com/deploy/nvidia-smi/index.html).

Do not run a large local analysis LLM alongside ASR on 8 GB. The future analysis coordinator should queue GPU embedding/LLM passes between ASR blocks, or begin with CPU-bounded lexical indexing and deterministic extraction. Keep review/interpretation separate from machine-generated transcripts.

## Storage, provenance, and recovery design

Place the active model cache, temporary decoding artifacts, fetched media, caption bundles, and generated results under the accounted private root where possible. Recompute the usable ceiling before provisioning:

`private_cap = min(17 GB, 18 GB - measured project files outside private root - outstanding external-install reservations)`

The 18 GB working limit reserves 2 GB within the user's 20 GB allowance. Model weights **consume** the private cap; they are not 17 GB of additional storage. Package installers, wheels, CUDA libraries, and temporary model copies also count. Download one candidate at a time only in the authorized pilot phase. Keep an independent physical-disk free-space floor.

For each item, resolve an immutable Drive object from verified receipts; reserve local bytes first; stream into `.part` while hashing; require the receipt length and SHA-256 before promoting it to an ASR input. Source metadata remains linked by video ID and hashes. Direct Drive-to-decoder piping may be experimented with later, but results must remain provisional until EOF, expected length, and the complete source hash have been checked. A stream failing after partial decoding must not produce a completed transcript.

Prefer bounded local spool files for restartability. `rclone rcat` can stream but overwrites an existing destination and cannot retry an unstored input stream as a whole; it is not the default evidence-preserving uploader. [rclone streaming behavior](https://rclone.org/commands/rclone_rcat/). Reuse exact destination manifests and verify remote size plus hash after uploading each versioned transcript bundle. Rclone `check` compares sizes/hashes and supports downloaded comparison when hashes are unavailable; size-only is insufficient here. [rclone check](https://rclone.org/commands/rclone_check/), [Drive backend](https://rclone.org/drive/), [Drive file metadata](https://developers.google.com/workspace/drive/api/reference/rest/v3/files).

Suggested immutable result bundle: `segments.json`, `words.json` when available, `transcript.txt`, `provenance.json`, `quality.json`; optional alignment/diarization in separately identified derived bundles. Preserve original source words alongside any normalized search text. Record null/unaligned timing explicitly. Do not label a diarized speaker as a person or a claimed entity without separate evidence. Published captions are not automatically a human gold reference.

Use durable states `reserved → source_verified → inference_complete → local_result_verified → remote_verified → local_released`, plus explicit retryable/deferred/quarantined outcomes. Persist chunk checkpoints with source offsets and hashes. Simulate termination at every transition. OOM reduces the next batch and retries a bounded number of times on GPU; failure becomes deferred rather than a silent CPU run. Drive errors retain local results and respect the existing shared cooldown. Release source/result leases only after the corresponding proofs are durable; never delete the authoritative Drive audio as a consequence of successful ASR.

For optional diarization, pyannote's Community-1 card documents local/offline use after model access/setup; its pipeline defaults to CPU and must explicitly move to CUDA. Accept the relevant model conditions separately, keep its credential private, and choose the local pipeline rather than the hosted service. Review telemetry behavior in the pinned dependency before execution. [Model author documentation](https://huggingface.co/pyannote/speaker-diarization-community-1).

## Proposed pilot and acceptance gates

These thresholds are **proposals for review**, not measured results or universal ASR guarantees.

| Gate | Reproducible method / pass condition |
| --- | --- |
| Sample | Freeze 18 five-minute excerpts (90 minutes) from independent recordings: clean monologue, poor audio/music, multiple speakers, accents, domain names, dates/numbers, and silence. Add two long recordings for memory/recovery testing. Freeze source hashes and offsets before comparing candidates. |
| Gold text | Human transcription with explicit uncertainty/inaudible labels; second reviewer checks at least 10% and all disputed names/numbers. Keep held-out excerpts separate from prompt/glossary tuning. Target at least 100 annotated domain-name mentions. |
| Accuracy | Report corpus and per-recording WER `(S+D+I)/N`, exact normalized name-mention accuracy, number/date accuracy, and hallucinated words per silent minute. Preserve a punctuation-sensitive companion score. Provisional gates: ≤15% aggregate WER, ≥90% name accuracy, ≥95% number/date accuracy, and no substantive invented sentence in silence. Failed strata go to human review, not aggregate concealment. |
| Caption reuse | Compare caption coverage and quality against the same human reference. Test beginning/middle/end and long gaps. An existing caption ZIP or low WER on one clip cannot establish full-session coverage. |
| Performance | Same audio, model revision, decoding/VAD configuration, precision, and warm-up policy. Three timed repeats per candidate; separately record cold load, decode, inference, alignment, upload, and total wall time. Report RTF and its reciprocal, peak VRAM/RAM, utilization distribution, and end-to-end audio-hours/day under the throttle. Initial practical gate: sustained end-to-end processing faster than real time while meeting quality/resource limits. |
| Timestamp/speaker quality | On a manually timed subset, report median/p95 word-boundary error and unaligned fraction; provisional p95 ≤0.5 seconds for quotation navigation. For diarization, report DER/JER, overlap handling, and speaker-count errors separately; speaker identity remains unverified. |
| Reliability | Zero unverified deletions or silent CPU fallback; interrupted download/ASR/upload resumes without accepting a partial artifact; wrong hash and duplicate/different-source ID fixtures fail closed; 17 GB private and 20 GB total limits remain enforced with the 2 GB reserve. |

Use a fixed metadata-derived glossary for a separate prompted experiment if the chosen decoder supports it. Do not inject gold-reference names into the test condition. Include model/hardware/environment lockfiles and the measurement script in the pilot record; no corpus ETA until duration totals and local measured throughput exist.

## Owners and round-2 questions

| Owner | Next responsibility / deliverable |
| --- | --- |
| Compute/transcription owner | Resolve the CUDA/cuDNN version conflict, design a pinned minimal environment, measure model/package disk footprints, and propose the two-model pilot. No execution before the pilot phase is authorized. |
| Ingestion/storage owner | Specify cross-process budget reservations and source/result leases; verified Drive fetch/release adapter; scoped cooldown and crash fixtures. |
| Corpus/provenance owner | Join native receipts and caption bundle manifests to existing corpus schema, repair folder-derived ownership, and version derivation IDs without rewriting original metadata. |
| Evaluation owner | Freeze representative samples and blinded human references; score names/numbers, silence, timing, overlap, and quality strata. |
| Analysis owner | Define downstream claims/quotation records that cite source hashes and time spans, distinguish speaker attribution from identity, and retain disagreement/uncertainty. |
| Research lead | Reconcile resource budgets and quality gates in round 2; decide whether alignment/diarization justifies its additional model/storage cost. |

Open questions: exact remaining audio hours and duration distribution; caption coverage/quality; true laptop sustained performance and thermal behavior; Windows compatibility of the selected pinned stacks; final model-cache/install footprint; decoder vocabulary performance on this corpus; necessary speaker separation; and the shared lease/budget implementation. None was resolved by installing or running a model in this round.

## Search and source audit

Five independent Exa searches requested **5 results each: 25 requested, 25 returned, 25 distinct result URLs**. This is discovery breadth, not 25 fully read or validated sources. **15 distinct primary pages were successfully opened**: Whisper; faster-whisper; WhisperX; three CTranslate2 pages (installation, quantization, parallel execution); two NVIDIA Parakeet cards; NeMo checkpoints; rclone check/Drive/rcat; Google Drive file metadata; NVIDIA nvidia-smi; and pyannote Community-1. NVIDIA nvidia-smi was fetched a second time with a larger text allowance. A separate obsolete NVML structure URL failed in Exa and the permitted direct-fetch fallback; it supports no claim.

| Search angle | Requested / returned | Quality treatment |
| --- | --- | --- |
| Whisper implementation/memory benchmarks | 5 / 5 | Maintainer repositories opened. Excluded generated DeepWiki synthesis and old package-release examples as current benchmark authority. |
| CTranslate2 installation/quantization/concurrency | 5 / 5 | Runtime-maintainer docs; exact version conflict retained as unresolved. |
| WhisperX alignment/diarization limitations | 5 / 5 | Maintainer README opened; individual issue timings treated as anecdotes, not benchmarks. |
| NeMo/Parakeet English alternatives | 5 / 5 | Model-author cards and toolkit docs opened. Vendor measurements retain dataset/batch caveats. |
| Drive streaming/integrity | 5 / 5 | Maintained rclone docs; additional direct Google metadata reference. No third-party storage advice used. |

Primary maintainers have direct implementation knowledge but also an incentive to show favorable performance. Their capability descriptions are useful; performance claims require local replication on the fixed evaluation sample. No content from private media, captions, account metadata, or credentials was sent in research queries.
