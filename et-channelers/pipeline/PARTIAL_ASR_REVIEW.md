# Three-window partial-ASR review

`partial_asr_review.py` is a byte-exact copy of the separately admitted private
worker, SHA-256
`572d005fa3aba6157669d0318ac47bb20297eb0cc3146132679ed4d45779fe71`.
Only its filename differs. The `-text` Git attribute preserves its bytes.
No runtime policy or private admission is generalized by this publication.

This profile permits English original transcription of exactly the three
contiguous intervals reviewed by [language-ID V2](LANGUAGE_ID_REVIEW.md):
88.464 seconds in total. It uses the existing pinned multilingual large-v3
CUDA model and the unchanged V2 decoder (source hash
`cce88fd0e5881f5ef67b45f3a303f2116967739aeb45c6d577963e9f3fc22f28`).
It performs no translation, language-ID rerun, VAD rerun, source acquisition,
model installation, or input deletion. Imports start no work.

## Admission and execution

`prepare` verifies the immutable V2 proposal and complete language-review ZIP,
including its member hashes, source/model/code bindings, exact windows, and
three qualifying English language scores. These scores justify the bounded
review scope; they do not remove the original metadata hold or prove that the
full recording contains intelligible English.

Both new source and GPU leases require the identical `partial_review` binding:
proposal, worker, configuration, model manifest, core helper, multilingual
helper, V2 decoder, and V2 result SHA-256 values. The source lease must have
profile `partial-asr-review-v1`, matching owner/ID, active unexpired state,
exact audio/metadata proofs and paths, and the preceding triage lease ID.
It explicitly permits `partial_text_generation_allowed: true` while requiring
`full_asr_allowed: false` and `metadata_hold_override: false`.

The retained inputs remain restricted to
`<private-root>/research/jamye-audio-triage-v1/input`. One sequential source
decode verifies the prior exact sample extent and retains only the three
selected arrays before loading CUDA. Retained PCM is capped at 5.76 MB; no
full-recording PCM array or PCM file is created. The existing exclusive GPU
lock, 16 GB managed-storage inventory, 6.5 GB VRAM bound, and soft 70% rolling
utilization target apply. There is no CPU model fallback. The worker has a
ten-minute cooperative deadline and at most three transcription API calls.

A heartbeat checks the monotonic deadline and cached lease expiry on every
frame. Full source/GPU lease reads occur once per second, with forced checks
at phase boundaries and immediately before each transcription call. A known
expiry is enforced immediately, even inside the cached interval or following
a wall-clock rollback. Revocation is detected within the heartbeat interval.
Guard counters and decode/model/inference timings are included in telemetry.

```powershell
& <existing-asr-python> -I et-channelers/pipeline/partial_asr_review.py prepare `
  --pipeline et-channelers/pipeline --lid-worker <frozen-V2-worker.py> `
  --lid-proposal <private-V2-proposal.json> --lid-proposal-sha256 <sha256> `
  --lid-result <verified-language-review.zip> --lid-result-sha256 <sha256> `
  --output <new-partial-proposal.json>

& <existing-asr-python> -I et-channelers/pipeline/partial_asr_review.py run `
  --pipeline et-channelers/pipeline `
  --proposal <new-partial-proposal.json> --proposal-sha256 <sha256> `
  --settings <private-settings.json> --source-lease <new-source-lease.json> `
  --source-lease-id <lease-id> --output <new-partial-review.zip>

python et-channelers/pipeline/partial_asr_review.py verify --bundle <private-result.zip>
```

## Separate output and interpretation

The ZIP contains `review.json`, `original/segments.json`,
`original/transcript.txt`, `provenance.json`, `telemetry.json`, and a
member-hashed `artifact_manifest.json`. The English view is an explicit alias
of the original English output; no duplicate translation is generated.
Segments and words retain source-time estimates, window identity, and Unicode
code-point offsets. Small model timestamp overruns are explicitly recorded and
clipped to the known input interval; larger overruns hold the result.

The review enumerates every unprocessed interval and any unavailable metadata
tail. Processing a selected interval does not establish transcript coverage or
accuracy. Zero recognized words can mean completed processing with no candidate
text; it is not proof of silence, nonlexical content, or a useful transcript.
All output is `unreviewed_partial_asr`, with the original metadata flags and hold
preserved. Unprocessed spans remain unknown.

The local receipt goes only to `sync/partial_asr_review_manifest.jsonl` with
status `local_partial_review_unreviewed`. It does not write the normal ASR
manifest, claim Drive verification, or advance full-ASR/collection counts.
Result expansion is capped at 2 MB, serialized members at 1 MB, transcript text
at 100,000 characters, segments at 1,000, and words at 15,000. Failed runs retain
inputs; existing result paths prevent automatic replay. Publication and source
release require a separate owner-reviewed workflow.

Focused tests cover heartbeat throttling, revocation and expiry, wall-clock
rollback, source-time and Unicode offsets, explicit timestamp clipping,
unprocessed interval accounting, artifact separation, output limits, and safe
diagnostics. They use synthetic fixtures only, with no corpus audio, GPU, model
construction, or network. This contract makes no partial-trial outcome claim;
observed findings belong in the [research report](../research/held-audio-language-review-2026-11-17.md).
