# Publisher-variant English ASR

`publisher_variant_asr.py` is the byte-exact public copy of the frozen private
adapter, SHA-256
`63f776af4a1d7f1ab16d7d50f3e20595624046e2da6a978d5975e656d4d5d0fc`.
Its `-text` Git attribute preserves source bytes. It transcribes verified
publisher audio editions while preserving their source identities, edition
differences, and qualified associations with queued YouTube IDs. It never
promotes them to native YouTube audio or native ASR inventory.

## Evidence and admission

The source is a verified `publisher_podcast_audio_variant` or
`qualified_publisher_podcast_audio_variant`, identified by its audio SHA-256,
publisher episode GUID, and exact archived audio/provenance Drive proofs. Its
associated YouTube ID is a separate relationship. Missing direct watch links,
unreviewed associations, and unverified edition equivalence remain explicit.

English eligibility requires a publisher RSS channel declaration. It may be
present in the original archived publisher provenance or in separate immutable
language evidence bound to the unchanged audio/provenance proofs, episode GUID,
and enclosure URL. Missing or non-English declarations remain pending; they do
not trigger forced English, LID, or partial-ASR work. Feed-level language is not
independent confirmation of every episode's spoken language, and no native
YouTube language assertion or replacement metadata is created.

The initial two-item proposal admits publisher editions measured at
1,401.533333 and 7,935.722676 seconds. The latter is processed at full duration;
there is no arbitrary per-channel duration cutoff. Both publisher declarations
are now evidenced (`en` and `en-us`), with their different association caveats
preserved. This is preparation evidence, not a completed-ASR claim.

`prepare` validates an immutable cohort of at most two sources and caps their
combined input pairs at 256 MB. It records worker/configuration/helper/model,
cohort, archive receipt, provenance, and language-evidence hashes. Runtime
rehashes the actual local input pairs and requires their provenance JSON to
equal the frozen projection. An exact metadata reconstruction is acceptable
only if its bytes reproduce the existing archived SHA; it does not replace
remote proof or authorize an audio pull.

New source and GPU leases carry the same `variant_asr` binding: proposal,
worker, configuration, core helper, multilingual telemetry helper, model
manifest, heartbeat helper, and cohort hashes. Each source lease additionally
requires its exact variant ID, audio/provenance proofs and paths, language
evidence hash, active owner/ID/expiry, profile
`publisher-variant-english-asr-v1`, and `native_youtube_bytes: false`.

## Bounded reuse of the existing worker

The adapter uses the installed, pinned English Distil model through the
existing English `model_proof`, CUDA runtime, segment collector, bundle writer,
and verifier. The multilingual runtime subclass is used only for its fresh
telemetry implementation; it does not select another model or run language ID.
One loaded model serves the eligible cohort sequentially. The ordinary English
and multilingual admission gates remain unchanged.

The existing GPU owner lock, 6.5 GB VRAM limit, soft 70% rolling target,
16 GB managed-storage inventory, and no-CPU-model-fallback policy apply.
Audio is streamed in 30-second windows without a full-recording PCM array or
PCM files. Transcription-call bounds derive from each measured source duration.
The worker has a 45-minute cooperative deadline per item, further restricted
by the actual source/GPU lease expiry. The reused heartbeat caches full lease
checks for one second and forces them at work boundaries; cached expiry and
the monotonic deadline remain enforced between checks.

Decoded samples and duration are recorded independently of the MP3 container
duration. Differences within the established two-second decoder tolerance are
reported as an unreviewed container/encoder-delay difference, not silently
identified with the queued YouTube duration. Timestamp estimates refer to this
publisher edition; native-video alignment is not asserted.

```powershell
& <existing-asr-python> -I et-channelers/pipeline/publisher_variant_asr.py prepare `
  --pipeline et-channelers/pipeline --heartbeat-worker <frozen-partial-worker.py> `
  --cohort <private-variant-cohort.json> --output <new-proposal.json>

& <existing-asr-python> -I et-channelers/pipeline/publisher_variant_asr.py run `
  --pipeline et-channelers/pipeline `
  --proposal <new-proposal.json> --proposal-sha256 <sha256> `
  --settings <private-settings.json> --admissions <private-source-leases.json>
```

The admissions document contains `items` with `variant_id`,
`source_lease_path`, and `source_lease_id`, matching the eligible proposal rows.
Settings use an output directory inside `asr/results`, such as
`asr/results/publisher-variants`. Source IDs used by the reused writer are
`publisher-<audio-sha256>`; associated YouTube IDs remain separate fields.

## Separate results and publication

The existing five-member English ZIP contains segments, transcript, telemetry,
provenance, and a hashed artifact manifest. Full publisher provenance, scoped
language evidence, source/edition caveats, and unreviewed accuracy/timing flags
remain attached. No translation is generated. Ordinary `publish_result`
helpers must not be used for these receipts because they write native ASR
inventory.

This adapter's `publish_result(receipt_path, drive, pipeline)` verifies the
bundle, run identity, receipt, source/model/configuration proofs, and artifact
manifest before upload. The destination is:

`<publisher variant audio directory>/ASR/<run_id>/<run_id>.zip`

Only an exact Drive ID/size/MD5 readback permits a durable record in
`sync/publisher_variant_asr_manifest.jsonl`. It never writes
`sync/asr_manifest.jsonl`. Records explicitly keep native audio and native ASR
count changes false. Source cleanup belongs to the resource owner after
independent proof checks; the adapter deletes no input or result.

Nine focused offline tests cover publisher-language scope and missing evidence,
episode/source binding, long-duration collection, separate result identity,
proof-tampering rejection, variant-only publication, and failed Drive hashes.
They use synthetic segment objects, temporary small ZIPs, and mocked transfers;
no corpus audio, GPU, model construction, network, or source download is used.
