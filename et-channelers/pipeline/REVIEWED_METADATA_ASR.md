# Reviewed-metadata full-source ASR

`reviewed_metadata_asr.py` is a byte-exact public copy of the separately admitted
private adapter, SHA-256
`2d1b31aff5205290145835fb9f5d0dc06bd11c947706ba1d82d9ee1503c40772`.
Only the filename differs; its Git attribute preserves bytes. This is one
explicit reviewed-source profile, not a general exemption from metadata checks.
The ordinary English and multilingual workers and their admission gates remain
unchanged.

## Why the separate admission exists

The original metadata remains `und` and retains its light-language flag. The
ordinary English worker therefore cannot accept it as metadata-declared English,
and the original multilingual frame retains its metadata hold. Neither the
source metadata nor that old frame/hold is rewritten.

A separate root-agent assessment links the full-file VAD report, the completed
three-window language-ID result, and the verified partial-ASR result. The root
agent examined all three partial excerpts and found coherent ordinary English.
This is content evidence for admitting a full-source, unreviewed English pass;
it is not human review, proof of every interval's language or meaning, or a
claim that the resulting transcript will be accurate.

The assessment is immutable, source-specific, and hash-bound into the proposal,
new leases, run identity, and result provenance. It records the original flags
and hold hash, `reviewer_kind: root_agent`, `human_reviewed: false`, and explicit
false values for whole-recording lexical/language confirmation. Original holds
and the earlier LID/partial artifacts remain independently preserved.

## Reused pipeline and limits

The adapter reuses the existing pinned large-v3 CUDA `Runtime`, `TaskRuntime`,
`collect_segments`, original-English-alias `write_pair`/`verify_pair`, and the
partial-review heartbeat. It does not modify those helpers or install packages
or models. Imports are inert. It acquires no source media and deletes no input.

One source of at most 1,600 seconds is decoded in sequential 30-second windows,
with at most 54 transcription API calls. The exact decoded sample count must
match the preceding VAD/LID evidence before a complete result can be sealed.
The known rounded metadata tail is recorded separately. Language is configured
as English for this admitted pass; translation is disabled, and the English
view is an explicit alias of the original output. The existing ASR configuration
uses word timestamps, fixed decoding settings, and bundled VAD preprocessing.

The existing exclusive GPU lock, managed-storage inventory, 6.5 GB VRAM bound,
soft 70% rolling target, and no-CPU-model-fallback policy apply. The cooperative
worker deadline is 30 minutes; a shorter lease still stops it. The heartbeat
checks cached expiry and the monotonic deadline frequently, rereads full leases
once per second, and forces checks at boundaries and before model calls.
Source/model hashes are checked before inference; source bytes and the original
hold are checked again before sealing. Timings and guard counters are retained.

## New lease and provenance contract

The profile is `reviewed-metadata-full-english-asr-v1`. Both the source and GPU
leases require an identical `reviewed_asr` binding containing proposal, worker,
configuration, assessment, model-manifest, core-helper, multilingual-helper,
partial-worker, partial-result, LID-result, and VAD-report hashes. Source leases
also require exact input paths and source proofs, matching owner/ID, active
unexpired state, the preceding triage lease ID,
`full_text_generation_allowed: true`, and
`metadata_flag_mutation_allowed: false`.

The retained source-path gate remains
`<private-root>/research/jamye-audio-triage-v1/input`. Queue-backed channel
identity is read from the original hash-verified metadata during preparation
and rechecked before model loading. No replacement source metadata is created.
Changing source, evidence, model, or policy requires a new explicit proposal
and matching leases.

```powershell
& <existing-asr-python> -I et-channelers/pipeline/reviewed_metadata_asr.py prepare `
  --pipeline et-channelers/pipeline --partial-worker <frozen-partial-worker.py> `
  --partial-proposal <private-partial-proposal.json> --partial-proposal-sha256 <sha256> `
  --partial-result <verified-partial-review.zip> --output <new-full-proposal.json>

& <existing-asr-python> -I et-channelers/pipeline/reviewed_metadata_asr.py run `
  --pipeline et-channelers/pipeline `
  --proposal <new-full-proposal.json> --proposal-sha256 <sha256> `
  --settings <private-settings.json> --source-lease <new-source-lease.json> `
  --source-lease-id <lease-id>
```

The existing `original-and-english-v1` writer stores the private bundle and
local receipt under `asr/results`. The established verifier must pass before
canonical publication through `gpu_asr_multilingual.publish_result`. That
publisher checks the exact remote path, Drive ID, size and MD5 before writing
the ordinary verified ASR manifest. A local result alone does not increment
Drive-verified inventory.

All quality flags remain unreviewed: no accuracy, human review, speaker
identity, or validated speech coverage is claimed. Original metadata and the
assessment's limited evidence scope remain visible in provenance. Existing
output directories prevent automatic replay. This contract makes no claim
about a completed full-source trial; results are reported separately.

Six focused offline tests cover preservation of assessment scope/flags,
assessment identity, full sample accounting, call limits, source-time offsets,
and integration with the unchanged collector and English-alias writer/verifier.
Fixtures use synthetic segment objects and temporary tiny ZIPs, without corpus
audio, model construction, GPU, network, or private admissions.
