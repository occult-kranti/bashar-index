# Leased GPU caption fallback

## Complete a frozen collection

Run the following commands from the `et-channelers` directory. The inventory reads local receipts and writes an immutable proposal. It accepts native YouTube audio, qualified YouTube audio and independently published editions. It checks existing English text and previous language decisions, then groups identical verified audio bytes across listings.

For an individually reviewed set of inconclusive language decisions, pass the same `--speech-review PATH --speech-review-sha256 SHA256` to both commands. Each entry binds the original hold, the archived audio and the metadata object. The local worker examines consecutive ten-second intervals through the end of each admitted recording. It keeps inconclusive speech or language evidence available for individual review.

```powershell
& $asrPython -m pipeline.gpu_asr_editions inventory `
  --root $privateRoot --selection $selection --selection-sha256 $selectionSha --plan $proposal
```

Use the printed proposal digest for the GPU lease. Once every selected recording has a verified audio pair, the collector has parked, and the GPU lease is active, the same proposal can be run or resumed. Supply each managed project root with a separate `--managed-root` argument.

```powershell
& $asrPython -m pipeline.gpu_asr_editions run `
  --root $privateRoot --selection $selection --selection-sha256 $selectionSha `
  --plan $proposal --plan-sha256 $proposalSha --gpu-lease-id $leaseId --gpu-owner $leaseOwner `
  --model-dir "$privateRoot/models/large-v3" `
  --model-receipt "$privateRoot/provisioning/asr/multilingual-model-receipt.json" `
  --managed-root $privateRoot --managed-root $toolsRoot --managed-root $repositoryRoot `
  --rclone $rclone
```

One CUDA model serves the batch. The 30-second utilization window carries across recordings. Each completed speech window is checkpointed against its audio, model and task. A restart decodes the source clock again and reuses those results. Non-English speech produces separately identified original and English views. English speech reuses its original text for the English view. Drive verification precedes local input cleanup. The append-only `sync/edition_asr_manifest.jsonl` records each video association and its edition clock. An optional `--limit N` bounds a single execution. An active pause, an incomplete collection or a mismatched lease holds execution.

`gpu_asr.py` transcribes admitted, already archived English audio with one local
CUDA model. It does not acquire YouTube media, replace captions, infer speakers,
or delete source files. Imports are inert; inference requires the explicit `run`
command, an active GPU lease, and an active source lease for each input.

The currently running private batch is a separate pilot implementation. The
tracked worker has offline integrity/lease tests; its streaming-window decode
path still needs a separate admitted CUDA acceptance run before replacing that
batch. The earlier 63-second private pilot demonstrated CUDA execution, not
transcription accuracy or this worker's end-to-end production readiness.
The active private runner records its own source hash in each result's
provenance. Archive that exact runner source and dependency lock alongside its
private run record before retiring it; a later tracked worker revision is not
bit-identical evidence for an earlier private run.

## Reproduce the environment without duplicating models

The lock targets **Windows x86_64 / Python 3.12**. It contains exact binary-wheel
hashes for all 29 resolved packages. `gpu_asr_provenance.json` records their
public wheel URLs and the exact CTranslate2 model revision and file hashes.
Reuse the existing verified environment/model when their hashes match.

Only after the resource coordinator has reserved the installation space:

```powershell
py -3.12 -m venv <private-tools>/asr-venv
& <private-tools>/asr-venv/Scripts/python.exe -m pip install --require-hashes --only-binary=:all: --no-cache-dir -r et-channelers/pipeline/requirements-gpu-asr-win-py312.lock
```

Use one copy of `Systran/faster-distil-whisper-large-v3` at revision
`c3058b475261292e64a0412df1d2681c06260fab`. The five required files are listed in
the provenance JSON; `model.bin` is 1,512,927,867 bytes, SHA-256
`b79368e19b6623813609431a6e5ee309a71506701ebc49fd7820e692dec7c5f5`.
The model receipt must state `status=model_verified`, repeat the pinned public
repository/revision, and provide the exact byte sizes and SHA-256 values under
`files`. The worker rehashes all five local files before loading them. It never
downloads models automatically. Model and package provenance are available at
the [pinned model source](https://huggingface.co/Systran/faster-distil-whisper-large-v3/tree/c3058b475261292e64a0412df1d2681c06260fab)
and in the checked-in public wheel manifest.

Inference is CUDA `int8_float16`, one model worker, batch size one. CUDA DLL
directories are process-scoped on Windows. No Torch package, second model, or
CPU ASR fallback is introduced. PyAV decoding, feature preparation, and the
bundled ONNX VAD perform host-side preparation.

## Admission and storage contract

The coordinator creates `sync/gpu_lease.json`. It must have the supplied owner
and lease ID, `state=active`, `exclusive_owner=true`, `device_index=0`, an
unexpired timestamp, `cpu_fallback_allowed=false`, and
`additional_models_allowed=false`. The VRAM ceiling cannot exceed 6.5 GB and
the rolling utilization target cannot exceed 0.70. The existing persistent OS
lock at `sync/asr_gpu_owner.lock` enforces one worker process.

Each admission comes from `gpu_asr_queue.prepare_inputs`. It identifies one
audio object and its metadata, with source Drive IDs, byte sizes, MD5, SHA-256,
and the exact private input paths. The worker independently rehashes both files,
checks the source lease and hashed metadata's English language declaration, and
claims the source under the queue lock before inference. Expiry or changed
hashes leave the inputs retained for owner review.

Until shared storage reservations coordinate concurrent collection, all runs
require `sync/STOP_DRIVE_INGEST` and an analysis resource plan with
`collector_dispatch_allowed=false`. Pass **all** managed private, tools/cache,
and repository roots. Missing coverage for the current environment, model,
private root, or worker checkout is rejected. The hard admission ceiling is
16 GB across these roots, below the user's 20 GB total allowance and 2 GB spare
space requirement. Inventory conservatively adds every active reservation as
extra headroom, plus 60 MB for result/control writes. It does not silently lower
another owner's allocation. Unknown symlinks fail admission.

## Execute a bounded ready set

The queue supplies at most three admitted input copies. One model stays loaded
for that explicit ready set. Absolute paths below are caller inputs, not stored
defaults:

```powershell
& <private-tools>/asr-venv/Scripts/python.exe et-channelers/pipeline/gpu_asr.py run `
  --root <private-root> `
  --ready <private-root>/asr/jobs/ready.json `
  --model-dir <private-root>/models/distil-large-v3 `
  --model-receipt <private-root>/provisioning/asr/model-receipt.json `
  --gpu-lease-id <coordinator-issued-id> --gpu-owner <coordinator-owner> `
  --managed-root <private-root> --managed-root <private-tools> `
  --managed-root <repository-root> --managed-root <other-managed-checkout>
```

Alternatively pass one or more `--admission <json>` arguments. `--output-root`
may select a directory under `<private-root>/asr/results`. No plaintext is
printed. A failure returns exit 3 with a constant error class; partial artifacts
and source copies remain private. `asr/STOP_ASR` prevents the next decode or
inference step. A GPU kernel already executing cannot be preempted by this
wrapper.

Decode streams through PyAV into 30-second, non-overlapping 16 kHz windows;
there is no whole-recording PCM allocation. The declared source duration bounds
decoded samples, and final duration must agree within two seconds. VAD and
word timestamps are enabled. Window boundaries may affect recognition and
need reference evaluation; no quality improvement is claimed over the pilot.

NVML samples every second. The worker waits before more inference while the
trailing 30-second observed average exceeds target minus ten percentage points.
This is pacing toward a **soft 70% rolling target**, not an instantaneous GPU
cap. VRAM, temperature, lease ownership, lease expiry, and STOP are checked
between steps. The retained telemetry includes at most 3,600 samples plus
whole-run count, mean, maxima, and peak rolling utilization.
Missing samples or a last sample older than three seconds stop this worker;
unobserved utilization is never treated as idle GPU time.

## Versioned artifacts and publishing

The run ID fingerprints input proofs, model revision/hash, dependency lock,
worker source, schema, inference settings, and decode-window policy. Changing
any of those creates a distinct result. Existing valid results are reused
without another GPU load. Each private ZIP contains:

- `segments.json`: source-audio timestamps, exact Unicode character offsets,
  word timestamps/probabilities, and unassigned speaker identity.
- `transcript.txt`: generated text, kept private.
- `telemetry.json`: observed utilization and pacing evidence.
- `provenance.json`: source/lease/model/version/configuration evidence and
  explicit unreviewed-quality limitations.
- `artifact_manifest.json`: byte sizes and SHA-256 for every preceding member.

The ZIP is atomically promoted only after member-set, expansion-size, CRC,
manifest-hash, and provenance checks. `verify_bundle(path, expected)` is also
available without GPU dependencies; the CLI equivalent is:

```powershell
python et-channelers/pipeline/gpu_asr.py verify <private-result.zip>
```

`publish_result(receipt_path, remote, drive)` accepts the collector's existing
`Rclone` adapter. Its only valid destination is
`<audio-parent>/<video-id>/ASR/<run-id>/<run-id>.zip`. After upload it requires an
exact Drive ID, byte size, and MD5 readback, then durably appends a
`status=verified`, `artifact_kind=asr_bundle` receipt to
`sync/asr_manifest.jsonl`. The whole ZIP's proof covers its result and provenance.
This method never deletes source inputs. Only
`gpu_asr_queue.release_input(root, admission, verified_record, drive)` may retire
the exact leased local copies after the durable result proof and another source
identity check. Original archived audio and captions remain distinct.

Package installation, inference throughput, and a model-generated transcript do
not establish accuracy, speech coverage, speaker identity, or the truth of any
claim in the recording. Human reference evaluation remains a separate task.

## Dated local acceptance

At the November 17 continuation checkpoint, 25 English bundles for already
verified audio have been uploaded and hash/identity-verified on Drive: 9.65
audio hours and 5,343 segments. The separate runtime archive retains exact
worker revisions, the dependency lock and model provenance. Accuracy remains
unreviewed. Across these batches, peak VRAM was 1.639 GB and the maximum
observed 30-second mean utilization was 67%; brief samples reached 100%.
This is measured soft-target behavior, not an instantaneous utilization cap.

The additional [multilingual adapter](GPU_ASR_MULTILINGUAL.md) uses a separately
pinned large-v3 model and a strict paired original/English output contract.
It does not change this English configuration or verifier. The environment
and both authorized model caches are now provisioned: their bytes count in
actual managed inventory, rather than remaining an unspent installation
reservation. Further model/package growth is disabled during this phase.
