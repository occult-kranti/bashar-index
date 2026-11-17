# Transcription and compute panel — round 2

Date: 2026-11-16. Scope: dependency/source inspection, public package/model metadata, and experimental design. **No installation, wheel/model download, ASR, alignment, diarization, audio upload, or runtime change.** This memo refines [transcription round 1](transcription-panel-round1.md) and follows the work-family and measurement contract in [analysis round 1](analysis-panel-round1.md).

## Decisions

| Decision | Accept or defer | Basis |
| --- | --- | --- |
| First engine | **Accept for a later pilot:** faster-whisper 1.2.1 with CTranslate2 4.9.0, explicit CUDA, one GPU owner. | Current official package metadata satisfies faster-whisper's `ctranslate2>=4,<5` constraint; tagged Windows build evidence is available. This is a source-supported candidate, not a locally tested environment. |
| First model | **Accept for a later pilot:** pinned CTranslate2 `distil-large-v3`, `int8_float16`, batch 1 initially. Compare against pinned `large-v3` in a separate run. | English scope, existing adapter, smaller stored weights; the larger model remains a quality comparator. No claim that the smaller model wins on this corpus. |
| cuDNN | **Do not add a standalone cuDNN package to the initial 4.9 Windows plan.** Verify actual loaded DLLs and GPU kernels in the authorized smoke test. | Current tagged Windows build turns cuDNN off and uses native CUDA convolution. Earlier versions have different requirements; see the evidence below. |
| GPU utilization | **Accept a measured rolling utilization target; defer any claim of a hard instantaneous 70% cap.** | Native Windows does not support NVIDIA MPS; thread provisioning is not equivalent to a GPU busy-time ceiling. |
| Parakeet | **Defer to a challenger pilot after the first engine meets resource and quality gates.** | Native timestamps are useful, but a second NeMo/PyTorch stack has unmeasured local dependency cost and no laptop benchmark. |
| Alignment/diarization | **Defer corpus-wide execution.** Test selective, sequential passes only when navigation or speaker separation needs justify them. | They add models and error modes. Anonymous diarization labels do not establish host, guest, channeler, or claimed-entity identity. |
| Production transcription | **Defer.** | Shared budget/leases, stable derivation IDs, bounded decoding, a frozen gold set, and a CUDA smoke test remain required. |

## 1. Exact compatibility evidence

The inspected collection interpreter is **CPython 3.12.9**, not the Python 3.13 mentioned in an older repository requirements comment. Hardware remains the verified 8,188 MiB RTX 4070 Laptop GPU, driver 616.56; no new load test was performed.

The apparent cuDNN contradiction has a versioned explanation:

| Version/source | What the official source establishes |
| --- | --- |
| CTranslate2 4.5.0 release notes | The Python package changed to cuDNN 9 and ceased compatibility with cuDNN 8. The generic installation page's cuDNN 8 wording cannot be applied to that package family. [Tagged changelog](https://github.com/OpenNMT/CTranslate2/blob/v4.9.0/CHANGELOG.md). |
| CTranslate2 4.6.0 Windows build | Uses CUDA 12.2.2, cuDNN 9.1, `WITH_CUDNN=ON`, and copies a cuDNN 9 shim into the wheel. This is concrete older-build evidence, not the current recipe. [Tagged build script](https://github.com/OpenNMT/CTranslate2/blob/v4.6.0/python/tools/prepare_build_environment_windows.sh). |
| CTranslate2 4.6.3 release notes | Introduces pure-CUDA Conv1D, making cuDNN optional. [Tagged changelog](https://github.com/OpenNMT/CTranslate2/blob/v4.9.0/CHANGELOG.md). |
| CTranslate2 4.9.0 Windows build | Uses CUDA 12.8.1 and explicitly sets `WITH_CUDNN=OFF`; the script still obtains/copies a cuDNN shim, so copying a DLL is not evidence that convolution requires it. The tagged CMake file uses a separate cuDNN convolution source only when enabled. [Windows build](https://github.com/OpenNMT/CTranslate2/blob/v4.9.0/python/tools/prepare_build_environment_windows.sh), [CMake](https://github.com/OpenNMT/CTranslate2/blob/v4.9.0/CMakeLists.txt). |
| Current registry metadata | PyPI reports faster-whisper 1.2.1 and CTranslate2 4.9.0. The latter has a CPython 3.12 Windows x64 wheel. This proves artifact availability and declared constraints, not that this laptop successfully loads it. [faster-whisper metadata](https://pypi.org/pypi/faster-whisper/1.2.1/json), [CTranslate2 metadata](https://pypi.org/pypi/ctranslate2/4.9.0/json). |

**Proposed direct pins for the isolated smoke environment:** faster-whisper 1.2.1, CTranslate2 4.9.0, NumPy 2.3.4, PyAV 16.0.1, ONNX Runtime 1.23.2, tokenizers 0.22.1, huggingface-hub 0.36.0; CUDA runtime 12.8.90 and cuBLAS 12.8.4.1 Windows artifacts. All named artifacts were confirmed through public PyPI metadata. The hub/tokenizer pair satisfies the latter's `<2` hub constraint. The complete transitive lock and hash list are still a pilot-preparation deliverable; this list is not a claim of resolver or runtime validation.

Faster-whisper's tagged requirements permit unbounded newer PyAV versions, while its tagged decoder passes `metadata_errors` to `av.open`. The current local adapter already bypasses that decoder using FFmpeg, with a note about the PyAV 19 incompatibility. Preserve the explicit decoder path and verify it; do not assume installing whatever latest resolver selects reproduces the repository's behavior. [Tagged dependencies](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/requirements.txt), [tagged decoder](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/audio.py).

The later smoke gate must prove: exact package hashes; process-scoped DLL search paths; supported CUDA compute types; explicit `device=cuda`; successful small inference on the pinned model; observed GPU activity; and no CPU fallback. Log loaded CUDA libraries and decoder version. The existing NVIDIA driver number alone does not prove user-space CUDA libraries are installed. Use private runtime libraries/prebuilt wheels rather than compiling CUDA/Intel toolchains inside the small project allowance. No smoke command was executed in this round.

## 2. Model and dependency bytes: measured metadata versus reservations

Only JSON/text metadata was fetched. The following are repository-reported **stored weight bytes**, not downloaded files, installed footprint, or VRAM measurements:

| Artifact | Weight bytes | Immutable revision |
| --- | ---: | --- |
| CTranslate2 large-v3 `model.bin` | 3,087,284,237 | `edaa852ec7e145841d8ffdb056a99866b5f0a478` |
| CTranslate2 distil-large-v3 `model.bin` | 1,512,927,867 | `c3058b475261292e64a0412df1d2681c06260fab` |
| Parakeet TDT 0.6B v2 `.nemo` | 2,472,222,720 | `ae9ad07059c7c739ffaf932226a8fe64ae2620b0` |

Evidence: [large-v3 model-file metadata](https://huggingface.co/api/models/Systran/faster-whisper-large-v3?blobs=true), [distilled model-file metadata](https://huggingface.co/api/models/Systran/faster-distil-whisper-large-v3?blobs=true), [Parakeet model-file metadata](https://huggingface.co/api/models/nvidia/parakeet-tdt-0.6b-v2?blobs=true). Tokenizer/configuration files add several MB to the Whisper snapshots. The converted Whisper repositories store FP16 weights; selecting runtime INT8 does **not** halve their downloaded cache size. [Conversion description](https://huggingface.co/Systran/faster-whisper-large-v3).

Selected Windows compressed wheel sizes: CTranslate2 4.9.0 = 20,408,736 bytes; cuBLAS 12.8.4.1 = 567,544,208; CUDA runtime 12.8.90 = 944,318; PyAV 16.0.1 = 32,296,912. These and the proposed direct Python dependencies total approximately **0.652 GB compressed**, before transitive packages. A cuDNN 9.10.2.21 Windows wheel alone adds 692,992,268 bytes if later required by another stage. [cuBLAS metadata](https://pypi.org/pypi/nvidia-cublas-cu12/12.8.4.1/json), [CUDA runtime metadata](https://pypi.org/pypi/nvidia-cuda-runtime-cu12/12.8.90/json), [PyAV metadata](https://pypi.org/pypi/av/16.0.1/json), [cuDNN metadata](https://pypi.org/pypi/nvidia-cudnn-cu12/9.10.2.21/json).

**Conservative admission proposal, in decimal GB:**

| Reservation inside the private root | Provisioning peak | Steady operation |
| --- | ---: | ---: |
| Isolated environment, DLLs, dependencies | 4.0 | 4.0 |
| Wheel/install temporary cache | 2.0 | 0 after safe cleanup |
| One active model, allowing large-v3 | 3.1 | 3.1 |
| Worst-case second model staging copy | 3.1 | 0 |
| Journals, results and reserve | 0.8 | 0.8 |
| Audio/decoded scratch allowance | At most 4.0 | At most 8.0 initially |
| Total | **17.0** | **15.9** |

These are admission reservations, **not measured installation sizes**. If real bytes exceed a reservation, pause admission and rebudget; do not consume the 2 GB user buffer. The existing 0.660 GB outside-private overhead must be remeasured. Enforce `private_cap=min(17 GB,18 GB−outside_project_bytes−external_reservations)`. A new environment/model cache belongs inside that cap. Count installer caches, incomplete downloads, hard-copy duplicates, logs, and decoding temporaries. Maintain the separate physical-disk free-space floor.

The first distilled model uses less of the reservation; this does not justify keeping every candidate cached. Evaluate candidates serially. Shared content-addressed caches may reduce duplication, but do not assume Windows symlinks or hardlinks eliminate copies without measuring allocation. Avoid adding PyTorch/NeMo or alignment environments to the first footprint before their own metadata and installed-byte budget is approved.

## 3. Operational GPU target

NVIDIA's current MPS documentation restricts MPS to Linux/QNX; native Windows cannot use `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE` as this project's controller. Even where supported, execution-thread provisioning is not the fraction of time reported busy by `nvidia-smi`. [MPS limitations and provisioning](https://docs.nvidia.com/deploy/mps/latest/when-to-use-mps.html). The round-1 laptop readout did not show a writable `power.limit`; watts are not GPU utilization percentages.

Accept this proposed control policy for a future pilot:

- One CUDA owner shared by ASR, later alignment/diarization, and later embedding/LLM work. Two network/housekeeping stages may overlap without loading another neural model.
- Begin at batch 1 with conservative inter-batch idle time; test batch 2 then 4 only on development clips. Observe total GPU utilization at 1-second intervals, a 30-second rolling mean, peak VRAM, temperature, and desktop responsiveness.
- Provisional memory admission: reserve approximately 2 GiB of the 8 GiB GPU for display/variation; reduce batch or defer the model if observed allocation approaches 6 GiB. This is a scheduler threshold, not a guaranteed CUDA memory partition.
- If the rolling mean stays above 70%, extend idle intervals and stop admitting new GPU work. If it stays below 55% for several control periods with ample VRAM, cautiously shorten idle time or increase batch. Pause for other GPU workloads or sustained thermal/interaction problems.
- Benchmark the throttled configuration. Report mean, p95 of rolling windows, fraction of windows above 70%, and peak 1-second samples. Momentary 100% samples are possible while kernels execute. Do not advertise a strict instantaneous cap.

NVIDIA defines utilization in terms of kernel-active time during the sampling window. Therefore a small batch can still report 100%, and a larger batch plus idle time can average less. [Monitoring definition](https://docs.nvidia.com/deploy/nvidia-smi/index.html). CPU audio decoding, hashing, and metadata joins remain bounded host tasks; costly model inference must stay on CUDA.

## 4. Gold set aligned with the analysis panel

Use the analysis panel's validated recording family as the split unit. A caption, repost, clip, publisher rendition, and ASR result from one family stay in the same split. Local held-out status does not establish absence from model pretraining.

Proposed initial allocation: six five-minute development excerpts from the E0 development families (30 minutes), and eighteen five-minute held-out excerpts from distinct E0 evaluation families (90 minutes), where coverage permits. Balance clean/noisy audio, monologue/dialogue, host/guest formats, accents, domain vocabulary, numbers/dates, silence/music, tabs, and periods. Reserve explicit person-held-out and chronological strata; report cells that cannot be filled rather than inventing balance. Long-session memory/recovery fixtures come from development families and do not become additional accuracy observations.

Freeze source hashes, exact offsets, and selection probabilities before candidate runs. Two reviewers independently transcribe the held-out excerpts and adjudicate differences, especially names, quantities, negation, quoted speech, overlapping turns, and inaudible spans. The round-1 10% second-review suggestion is insufficient for a small decisive gold set; use full independent review for these 90 minutes. Tune dictionaries/prompts only on development data.

| Measurement | Definition and handling |
| --- | --- |
| Word errors | Report `(substitutions+deletions+insertions)/reference_words`, pooled and per-family macro scores. Publish normalization code and a punctuation-sensitive companion measure. Use paired family-level intervals, not sentence pseudo-replication. |
| Proper names | At least 100 annotated mentions if feasible, grouped by person/entity/place/name class. Report exact mention accuracy and error counts; freeze spelling aliases from independent identity records, not test outputs. ASR name correction remains a separate derived version. |
| Numbers, dates, negation | Separate exact-value and polarity errors from ordinary WER. A fluent transcript changing a date or removing “not” can reverse a claim despite low average WER. These spans require human confirmation before downstream claim release. |
| Hallucination | Count human-judged invented propositions/utterances, inserted words per silent minute, and repetitions without corresponding speech. Silence-only inputs have no reference-word denominator, so ordinary WER is undefined there; show a separate rate. |
| Coverage | On randomly sampled speech intervals plus start/middle/end checks, report audible speech seconds represented, omitted speech, and unsupported text. Caption cue extent alone is not a coverage measure; distinguish long silence from missing speech. |
| Overlap and attribution | Score overlapping speech separately, report dropped competing turns, speaker-count errors, and anonymous diarization error when labels exist. Host/channel owner metadata is not speaker truth; unidentified guests remain unknown. |
| Timing | Report median/p95 boundary errors, unaligned/missing-time proportions, chunk-boundary omissions/repetitions, and source-offset mapping correctness. A word lacking trustworthy alignment retains null timing. |
| Downstream sensitivity | On fixed reviewed spans, compare name retrieval, numeric/negation preservation, and speaker-attributed claim extraction across caption and ASR versions. Do not select an engine using only aggregate WER. |

Original empirical work finds that hallucination can accompany silence/disfluency and that WER and fabricated content can diverge under distribution shift. These findings motivate the separate audits; their reported incidence is **not** assumed for this corpus. [Careless Whisper](https://arxiv.org/html/2402.08021v2), [Atwany et al., Findings of ACL 2025](https://aclanthology.org/2025.findings-acl.1190/).

Retain the provisional round-1 quality gates as hypotheses to review, not proof: aggregate WER ≤15%, name accuracy ≥90%, number/date accuracy ≥95%, and no substantive invented proposition in reviewed silence controls. Report denominators and uncertainty; a small test with zero observed hallucinations does not establish zero risk. Any failed critical stratum remains flagged even if the pooled score passes. Exact quotations and high-impact claim labels still require evidence inspection.

## 5. Version and attribution interface

Use `work_id` for the reviewed recording family, `item_id` for a platform copy, `text_version_id` for each raw caption or ASR rendition, and `span_id` for immutable offsets within that version. A derivation key includes source SHA-256, model revision/weight hash, decoder/VAD/chunk configuration, and output-schema version. Parser upgrades and rolling-caption cleanup produce new text versions with mappings to original cues.

Retain raw UTF-8 artifact hashes, explicitly defined character/byte offset conventions, original audio offsets, and optional word timing. Do not silently shift spans after normalization. Keep `source_channel_id`, channel owner, host, guest, anonymous speaker label, asserted speaker name, and attributed claimed entity in separate fields with separate evidence/review status. A model's `SPEAKER_01` is local to that recording and never becomes a cross-recording person ID without adjudication.

The old ASR job discovery must be replaced or adapted to the native catalog/receipts; immediate-parent folder labels such as `Videos` are not channeler IDs. Caption bundles remain immutable. Caption availability and verified storage do not imply text fidelity, completeness, or human authorship.

## 6. Comparative benchmark and recovery gates

The primary paired comparison is pinned distilled Whisper versus large-v3 under the same segmentation, language, VAD, beam, and scoring policy. Include a documented exception where a model's recommended decoder settings differ; do not present that as a pure engine comparison. The distilled model card reports favorable long-form results, but these are author benchmarks on its tasks, not expected local scores. [Distil-large-v3 card](https://huggingface.co/distil-whisper/distil-large-v3).

Parakeet v2's native timestamps may avoid a separate alignment pass, but do not imply speaker attribution or verified timing quality. It is a distinct architecture worth evaluating only after its private dependency footprint and GPU admission pass. WhisperX-style alignment is useful when ASR text is adequate and timing is the problem; forced alignment cannot make wrong words correct. Diarization is optional for genuinely multi-speaker material and remains separate from identity adjudication.

For each candidate: one cold-load trial, three warm repeats on development excerpts, then a frozen held-out evaluation. Record decode, inference, optional alignment, hashing, upload, and total wall time; RTF and its reciprocal; peak RAM/VRAM; whole-project bytes; utilization windows; and desktop impact. No hours/day forecast until real durations and throttled local timings exist. None of these timings has been measured here.

Before promotion, inject termination after source fetch, chunk inference, output serialization, upload, proof journaling, and local deletion. Require exact source and result hashes, stable chunk offsets, bounded disk reservations, immutable derivation destinations, and durable remote proof before release. An incomplete Drive stream or partial model/cache download cannot yield a completed transcript. OOM retries are bounded and remain on GPU; unresolved capacity failures are deferred. The authoritative Drive audio is retained regardless of ASR completion.

## 7. Search and evidence audit

Five targeted Exa searches requested **25 candidate slots**, returned **25 entries**, and covered package requirements, Windows GPU build dependencies, model-file sizes, GPU controls, and hallucination/evaluation. These are discovery counts, not validated-source counts.

Exa fetch returned content for **11 distinct primary page/source URLs** and failed on two guessed repository paths; exact paths were subsequently found through the tagged source tree. Additional read-only requests inspected **23 distinct PyPI JSON metadata endpoints**, **3 model-author Hugging Face metadata endpoints**, **2 GitHub tagged-tree endpoints** (also reread), and **7 tagged raw source files**. Registry metadata is an artifact inventory, not a separate independent benchmark. The raw and rendered versions of a source file are the same evidence, not corroborating studies.

Primary-source quality: package registries identify published artifacts and constraints; tagged build scripts establish build configuration; author model cards establish intended capabilities and their own evaluation claims; original papers motivate measurement design. None establishes local runtime performance. No private audio, transcript content, credentials, Drive identifiers, or source-account data was sent in these research requests.

Remaining accept/defer boundary: the dependency-family ambiguity is resolved from source, and exact candidate artifacts/weight sizes are known. **Actual installed sizes, CUDA/DLL loading, model fit, throttled speed, name/claim fidelity, and recovery under concurrent collection remain untested and deferred to the authorized pilot.**
