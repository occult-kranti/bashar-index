# Caption-gap review

`caption_gap_review.py` is the byte-exact source of the executed V3 private
gap-review worker, SHA-256
`04b3cd6e86abd2b5df0f9ea6914eb2c0565b5fcee11633385d51498d5f0197ca`.
Its Git attribute disables line-ending conversion so that the published source
matches the executed artifact on Windows and Linux. This reproducibility copy
retains the original single-candidate scope guard; it is not a general batch
dispatcher. Changing that guard or any other source requires a new plan and
matching resource/source leases.

The worker reviews timeline gaps in existing verified captions. It preserves
manual and automatic versions, acquires no source media, and does not upload or
delete input files. Its output is a separate `caption_gap_review` artifact,
labelled `unreviewed_gap_asr`; it is neither a full-recording transcript nor
evidence that missing words or complete speech coverage have been established.

## Execution contract

Imports are inert. `plan` verifies the immutable proposal and locally cached
caption/metadata hashes, reconstructs the cue union, and computes a bounded
plan. A proposal supplies exact source audio/metadata Drive proofs and caption
ZIP proofs, explicit cue intervals in integer milliseconds, and the requested
gap intervals. It must use actual cue ends; unknown ends are rejected.

```powershell
& <existing-asr-python> et-channelers/pipeline/caption_gap_review.py plan `
  --pipeline et-channelers/pipeline `
  --proposal <private-proposal.json> --proposal-sha256 <sha256> `
  --output <new-private-plan.json>

& <existing-asr-python> et-channelers/pipeline/caption_gap_review.py run `
  --pipeline et-channelers/pipeline `
  --proposal <private-proposal.json> --proposal-sha256 <sha256> `
  --settings <private-settings.json> --admission <verified-input-admission.json>

python et-channelers/pipeline/caption_gap_review.py verify --bundle <private-result.zip>
```

`run` requires both an active exclusive GPU lease and a verified source-input
admission. Each must carry the identical `gap_review` binding: proposal, worker,
core-worker, configuration, and plan SHA-256 values. Settings use the existing
[`gpu_asr.Settings`](gpu_asr.py) contract and pinned English Distil environment.
Source audio/metadata, source lease, cached captions, and model files are checked
before inference. No package or model download is performed. The collector must
remain parked; the same GPU ownership lock and managed-storage inventory apply.

| Resource or operation | Bound |
|---|---|
| Managed private/tools/repository storage | Existing 16 GB accounting cap |
| Shared ASR workspace | 200 MB, including input and output |
| Source duration / total cue gaps | 4,600 seconds / 240 seconds |
| Retained decoded PCM | At most 64 MB in RAM; no PCM files |
| VAD context | Two seconds around merged gaps |
| ASR work | Speech-bearing gap cores up to 24 seconds, plus two seconds of context per side |
| Aggregate ASR input | At most 900 seconds including context |
| Output ZIP and expansion | At most 20 MB |
| Wall / GPU | 30-minute cooperative worker bound; shorter owner lease may apply; one CUDA owner |

Audio is decoded sequentially, retaining only gap/context windows. PTS
discontinuities or a decoded-duration discrepancy over two seconds hold the
job. Within that tolerance, the measured EOF clips retained PCM, VAD, and ASR
context; the worker never pads missing audio. It preserves the original metadata
duration and reports the unobserved tail explicitly as unreviewed.

The existing bundled Silero VAD runs as CPU preprocessing. Only speech detected
inside the actual uncued intervals can trigger CUDA `int8_float16` ASR. Model
loading is lazy; recognition has no CPU fallback. The existing 70% rolling GPU
governor is a soft pacing target, not an instantaneous utilization ceiling.
Missing or stale telemetry stops work rather than relaxing the policy.

## Results and limitations

The ZIP contains `gap_review.json`, `segments.json`, `transcript.txt`,
`telemetry.json`, `provenance.json`, and a hashed `artifact_manifest.json`.
It retains source-time word estimates and separate context evidence. Selected
words require their midpoint to lie inside an uncued, VAD-positive core;
boundary-crossing words remain labelled. These timing rules do not establish
whether an adjacent caption already expresses the same word.

Empty VAD evidence means only that this model detected no speech in the tested
uncued samples. It is not proof of silence or complete coverage. Result receipts
do not advance normal ASR, caption-completion, or collection counts. Upload and
source release require a separate owner-reviewed workflow with Drive proofs.

The first completed private run reviewed 186.163 seconds of cue gaps in a
75-minute recording. It found 4.459 seconds of VAD-positive gap audio and used
32.459 seconds of ASR input including context. It produced five unreviewed word
candidates; a lexical comparison found three exact matches in adjacent captions
and left two unresolved. This is not a human-validated finding of missing words.
The measured source ended 0.4746875 seconds before rounded metadata duration;
that tail remains explicitly unreviewed. No provider caption was replaced.

Failure diagnostics contain a bounded phase, exception class, code-location
frames, and model/telemetry start flags. They omit raw exception messages,
locals, transcript text, URLs, and credentials. Source input remains retained
on failure; existing run directories prevent automatic replay.

## Offline verification

`tests/test_caption_gap_review.py` covers interval geometry, EOF clipping,
source-time mapping, lease binding, typed scalar serialization, safe diagnostics,
empty-evidence semantics, and the exact published worker hash. Optional installed
NumPy/faster-whisper API checks are honestly skipped when unavailable. Tests use
synthetic scalars and arrays only: no corpus audio, VAD/ASR inference, model load,
GPU execution, network access, or private identifiers are needed.
