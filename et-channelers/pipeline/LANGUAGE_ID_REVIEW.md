# Bounded language-ID review

`language_id_review.py` produces language-classifier scores for three explicitly
selected, contiguous source intervals. It does not transcribe, translate, obtain
media, upload results, delete inputs, change metadata holds, or advance ASR or
collection-completion counts. VAD-positive samples authorize examination; they
do not establish lexical speech or a natural language.

## Source lineage and portability

This is a byte-exact copy of the frozen private V2 worker with SHA-256
`cce88fd0e5881f5ef67b45f3a303f2116967739aeb45c6d577963e9f3fc22f28`.
Only its public filename differs; there are no source or runtime-policy changes.
Its `-text` Git attribute preserves bytes across Windows and Linux checkouts.

The V2 three-window scope, model checks, language-only call path, bounds,
thresholds, and output semantics remain unchanged. The input-path gate remains
`<private-root>/research/jamye-audio-triage-v1/input`, with exact input paths,
source bytes, MD5, SHA-256, Drive IDs, proposal, and separate source lease still
required to agree. This is a reproducibility copy of one reviewed trial profile,
not a general batch dispatcher. Different source selections or path layouts
require a new explicit worker version, proposal, and matching leases.

## Admission and resource contract

Imports are inert. `prepare` validates an immutable full-file VAD report,
its retained triage lease and proposal, the selection document, the original
metadata hold, and the pinned model manifest. The report must establish a
complete decoded sample domain beginning at source PTS zero. The selected
windows remain contiguous, including their internal pauses:

| Source sample range at 16 kHz | Input duration |
|---|---:|
| `[181504, 661504)` | 30.000 seconds |
| `[12681472, 13161472)` | 30.000 seconds |
| `[17625088, 18080512)` | 28.464 seconds |

Each window must overlap at least two seconds of the independently recorded VAD
intervals. These ranges total 88.464 seconds of input, not necessarily speech.
All timestamps and VAD overlap are rederived from integer sample boundaries;
no speech concatenation or silent padding is permitted.

`run` uses the existing `gpu_asr.Settings`, managed-storage inventory, exclusive
`sync/asr_gpu_owner.lock`, pinned multilingual `model_proof`, `Runtime.detect`,
and telemetry `Monitor`. The existing large-v3 model and environment must
already be present and hash-verified. No package/model installation or CPU
language-model fallback is provided.

Both the new GPU lease and the separate source lease must carry the identical
`language_review` object containing `proposal_sha256`, `worker_sha256`,
`config_sha256`, `model_manifest_sha256`, `core_sha256`, and
`multilingual_sha256`. The source lease requires profile
`language-id-review-v2`, active state, matching owner and lease ID, unexpired
deadline, exact source audio/metadata proofs and paths, the preceding triage
lease ID, and `text_generation_allowed: false`. The preceding triage lease and
metadata hold remain immutable. This explicit language-review scope does not
authorize recognition, translation, or override of a metadata hold.

Resource limits are three classifier calls, 30 seconds per window, 90 seconds
total selected PCM and 5.76 MB retained PCM, 6.5 GB VRAM, and a ten-minute
cooperative worker deadline. PyAV performs one sequential full-source decode,
retaining only the three selected arrays (5,661,696 bytes). It does not seek,
rerun VAD, construct a full-recording PCM array, or write PCM to disk. All three
windows and the complete decoded extent must pass validation before the CUDA
model loads. The measured sample count must exactly match the immutable VAD
report; source duration is capped at 1,600 seconds with at most a two-second
metadata discrepancy. Source origin must be zero, and frame PTS must remain
within the prior triage's 50 ms continuity tolerance of the cumulative sample
clock. Missing samples, extra samples, or discontinuities hold the job.
The collector remains parked under the existing 16 GB managed
storage policy. The 70% rolling GPU target is soft pacing, not an instantaneous
utilization ceiling; missing telemetry stops work.

```powershell
& <existing-asr-python> -I et-channelers/pipeline/language_id_review.py prepare `
  --pipeline et-channelers/pipeline `
  --triage-proposal <private-triage-proposal.json> `
  --triage-lease <retained-triage-lease.json> --vad-report <vad-report.json> `
  --selection <selection.json> --output <new-proposal.json>

& <existing-asr-python> -I et-channelers/pipeline/language_id_review.py run `
  --pipeline et-channelers/pipeline `
  --proposal <new-proposal.json> --proposal-sha256 <sha256> `
  --settings <private-settings.json> --source-lease <new-source-lease.json> `
  --source-lease-id <lease-id> --output <new-language-review.zip>
```

No private admission, source identifier, source text, credential, or local
operator path is included in this package. Proposal and result files stay
private. Admission and publication remain the responsibility of their owners.

## Output and interpretation

The ZIP contains `review.json`, `provenance.json`, `telemetry.json`, and a
member-hashed `artifact_manifest.json`. It includes source-time windows,
measured VAD overlap, decoded sample coverage, top-five language scores, top-two margins,
model/code/source proofs, lease identities, and telemetry. Output is bounded to
one MB; the serialized members must total under 500 KB. No word or transcript
member exists. Diagnostics contain phase, zero-based window index, decoded
sample count, started/completed language-ID call counts, model/telemetry flags,
exception class, and bounded code locations. They exclude raw exception
messages and source content.

A probability of at least 0.90 and a top-two margin of at least 0.20 set
`strong_window_language_evidence`. These are local classifier thresholds, not
calibrated probabilities of truth. Even a confident result does not establish
lexical meaning, human comprehensibility, a full-recording language, or correct
transcription. Unprobed spans remain unknown. The existing metadata hold stays
in effect, and no `asr_manifest` entry or completion promotion is produced.

The earlier V1 worker (SHA-256
`15ae3481af2478287d6087157d7eeee941978b16ab9536108fbc8b3911c22aef`)
stopped at `seek_preroll_limit` and produced no result ZIP or published language
scores. Its original diagnostics do not establish the failing window index or
whether an earlier language-ID call ran. V1 source and failure evidence remain
immutable. V2 replaces seeking with the single streaming decode described above
and adds explicit progress counters. The V2 trial completed all three language-ID
calls and generated no text. The [research report](../research/held-audio-language-review-2026-11-17.md)
records the interval-only scores, limited telemetry, and unchanged metadata hold.

The tests use synthetic values and an optional in-memory generated waveform.
They cover exact interval accounting, changed admissions, invalid scores,
finite JSON types, safe diagnostics, absence of text-generation calls, and
installed PyAV streaming alignment. A generated frame iterator spans the exact
source sample extent while retaining only the selected windows, and tests
reject mismatched EOF, clock discontinuities, and sample-budget overruns.
The codec fixture skips explicitly if PyAV or
NumPy is unavailable. No corpus audio, model construction, GPU, or network is
used by the tests.
