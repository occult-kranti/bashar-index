# Original-language transcripts and English translations

`gpu_asr_multilingual.py` is an explicit, leased adapter for already archived
audio. It adds a strict paired-output contract and leaves the English worker's
configuration and five-member verifier unchanged. Importing it starts no jobs,
imports no GPU packages, and changes no environment. No model is downloaded by
the adapter, and it never deletes source copies.

The adapter is covered by offline tests. A real multilingual CUDA acceptance
run remains a separate resource-coordinator gate; successful English runs do
not establish multilingual accuracy or translation quality.

## Model, resources and admission

Use the existing Python 3.12 environment and dependency lock from
[GPU_ASR_SETUP.md](GPU_ASR_SETUP.md). The additional disk cache is the official
[Systran CTranslate2 conversion of OpenAI Whisper large-v3](https://huggingface.co/Systran/faster-whisper-large-v3),
pinned at `edaa852ec7e145841d8ffdb056a99866b5f0a478`. The five files and their
SHA-256/size proofs are in
[gpu_asr_multilingual_provenance.json](gpu_asr_multilingual_provenance.json).
The model cache is 3,090,835,702 bytes. Both authorized model caches may exist on
disk; only one model may be loaded on the GPU at a time.

The existing GPU lock, CUDA `int8_float16`, 6.5 GB VRAM maximum, 16 GB managed
storage admission, 20 GB overall allowance with 2 GB spare, collector parking,
and accounting of external tools/cache/repositories apply. No new packages or
CPU ASR fallback are introduced. A bounded set contains at most three leased
inputs. Audio decode streams in 30-second windows; host-side VAD and feature
preparation remain bounded preprocessing.

The coordinator-issued GPU lease must additionally contain:

```json
{
  "input_frame_sha256": "<exact immutable proposal file SHA-256>",
  "model": {
    "repository": "Systran/faster-whisper-large-v3",
    "revision": "edaa852ec7e145841d8ffdb056a99866b5f0a478",
    "model_sha256": "69f74147e3334731bc3a76048724833325d2ec74642fb52620eda87352e3d4f1"
  }
}
```

The five-item proposal has `frame_id=multilingual-v1`. Each admission contains
the proposal hash, an active new source lease, exact audio/metadata Drive IDs,
byte sizes, MD5 and SHA-256 proofs, and the profile
`multilingual_original_and_english_translation`. Its `job_id` equals the
proposal's `proposal_job_id`. Changing a language declaration, metadata review
flag, model revision, source proof, or frame hash fails admission. Earlier
English-language holds are not reused as active leases.

## Speech and language decisions

Before semantic text generation, the worker decodes and validates the full
source duration and probes bounded windows near its beginning, middle and end.
Only VAD-retained speech reaches the same multilingual model's language
detector. A strong result requires probability at least 0.90, a top-two margin
at least 0.20, and at least two seconds of detected speech. Unknown recordings
longer than 30 seconds require agreement in at least two speech probes. A
confident conflict with declared Japanese or Spanish is held for review.

These thresholds are operational gates, not calibrated guarantees. A model's
language score does not prove meaning or whole-recording language coverage.
Mixed/conflicting results, insufficient speech, and low confidence produce a
private held decision, without a semantic transcript or a completion receipt.
Metadata labels for light language, nonverbal material, instrumental material,
or chanting trigger review before semantic transcription. Those labels are
review signals, not automatic interval classifications. The original audio
remains available; no natural-language English meaning is invented.

Held decisions are recorded in `sync/asr_language_manifest.jsonl` and the named
frame's `holds/` directory. Their source leases remain active in
`held_language_review`, retaining the owned input copies for an explicit later
decision. They do not count as completed ASR.

## Paired artifacts and verification

Accepted non-English sources produce one versioned ZIP with exactly:

- `original/segments.json` and `original/transcript.txt`, task `transcribe`.
- `english/segments.json` and `english/transcript.txt`, task `translate`.
- `provenance.json`, `telemetry.json`, and `artifact_manifest.json`.

The original and English views have distinct text kinds, configuration hashes,
text/segment hashes, languages, Unicode code-point offsets and source-audio
timestamps. English translation is model-generated; it is not relabeled as a
publisher caption. Word times, translation semantics, speech coverage, window
boundaries and speaker identity remain unreviewed.

For a reliably detected English source, the English view explicitly aliases
the original text and hashes. No duplicate translation is manufactured. This
strict five-member alias ZIP is a separate contract from the English worker's
legacy ZIP layout.

`verify_pair(path, expected=None)` checks the exact conditional member set,
20 MB expansion limit, CRC, every member's size/SHA-256, text offsets, times,
language/task/configuration identity, run identity, source/model proofs and
unreviewed quality state. Missing translations and non-English aliases fail.
Source audio is counted once in metrics, even when both tasks ran.

`publish_result(receipt_path, remote, drive)` accepts the existing `Rclone`
adapter. It uploads only to the archived source's exact
`<audio-parent>/<video-id>/ASR/<run-id>/<run-id>.zip` path. Exact Drive ID, byte
size and MD5 readback plus a repeated local ZIP verification precede the durable
`asr_manifest.jsonl` entry. That entry has `output_contract=original-and-english-v1`
and both typed views. Only after this proof may the coordinator invoke
`gpu_asr_queue.release_input`; the adapter itself never deletes inputs.

## Explicit use

```powershell
& <private-tools>/asr-venv/Scripts/python.exe -I et-channelers/pipeline/gpu_asr_multilingual.py run `
  --root <private-root> --model-dir <private-root>/models/large-v3 `
  --model-receipt <private-root>/provisioning/asr/multilingual-model-receipt.json `
  --proposal <private-root>/asr/jobs/frames/multilingual-v1/proposal-<sha>.json `
  --gpu-lease-id <new-coordinator-issued-id> --gpu-owner <owner> `
  --managed-root <private-root> --managed-root <private-tools> `
  --managed-root <repository-root> --managed-root <other-managed-checkout> `
  --ready <private-root>/asr/jobs/frames/multilingual-v1/ready.json
```

Alternatively pass one or more `--admission` arguments. `verify <bundle.zip>`
validates a local paired ZIP without GPU imports. Console output contains only
counts and constant status/error classes. The runtime checks fresh NVML data;
a bounded five-second `nvidia-smi` query may supply real telemetry when needed.
Both failing within ten seconds stops inference. Sampling gaps and backend
changes are recorded; missing observations are never treated as zero load.
Pacing targets a soft 70% rolling utilization average, not an instantaneous
kernel limit.
