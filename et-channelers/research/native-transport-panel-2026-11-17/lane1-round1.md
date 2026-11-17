# Native transport panel — lane 1, round 1

Reviewed 2026-11-17. Scope: saved native-browser observations, vendored SDK source, and primary upstream source/discussion. No YouTube request, browser activation, media decode, token generation, credential access, package change, or retry occurred.

## Finding

The known audio-only resume and old protobuf-name defects do not provide a new explanation or repair for this project's saved failure. The failed V5 bundle already contains the newer implementation, its playhead advances correctly, and it never establishes server acceptance. A complete native file remains unproved.

## Exact implementation comparison

The V5 build manifest identifies `googlevideo` 5.0.1. Its frozen bundle SHA256 is `62f3519ba617880aeaf1e7e915966ba73f0a0bc8fa08ea3eda4eb2f0cea594af`; the file on disk matches. V6 uses the same SDK core inputs, adding the passive acceptance gate and parser export.

| Input used by both saved builds | Bytes | SHA256 |
| --- | ---: | --- |
| `SabrStream.js` | 41,665 | `906cbcfd13f6b7d902f6e0d16d93d8cf6a0e550f78d5e15c1c8833227304c729` |
| `video_playback_abr_request.js` | 14,759 | `f1d2d335c569835283f10d71ed132b074c740502f24ae2a93c478f17b414c8f3` |
| `TrackCollection.js` | 3,539 | `624c9a9c108ffbce61ab706374933b6dd672a06d5f4e9ce4a28952d2ff0a6653` |

The local request encoder uses initialization formats on field 2, selected audio on 16, selected video on 17, and selected captions on 18. `buildRequestBody` populates those newer semantic names; the adapter supplies the complete selected audio format. These agree with the [current upstream protobuf](https://github.com/LuanRT/googlevideo/blob/main/protos/video_streaming/video_playback_abr_request.proto).

The local snapshot branch checks a video-format match only when a video format was selected, restores track state, then restores the saved playhead. `maxRetries: 0` still permits the initial request because the loop allows `maxRetries + 1` attempts. Current upstream reports version 5.0.1 and has these same targeted paths. This is a targeted source comparison, not a claim that every upstream TypeScript byte equals the compiled distribution. [Package](https://github.com/LuanRT/googlevideo/blob/main/package.json), [stream implementation](https://github.com/LuanRT/googlevideo/blob/main/src/core/SabrStream.ts).

The historical issue distinguishes two problems: an audio-only restore bug and an independently persistent server-pending condition. Its author reported that fixing restoration did not obtain subsequent media. The maintainer later linked PR54. Notably, the exact PR54 merge still checks both snapshot formats; the current distributed implementation has a later conditional video guard. Therefore issue closure alone would have been insufficient evidence; the installed code was checked directly. [Issue52](https://github.com/LuanRT/googlevideo/issues/52), [author's distinction](https://github.com/LuanRT/googlevideo/issues/52#issuecomment-5328546465), [PR54 merge source](https://github.com/LuanRT/googlevideo/blob/3cfeff043facb734c178a5b2ef1d8152ffb46bb4/src/core/SabrStream.ts).

## What this project's saved evidence establishes

V5 diagnostic SHA256 `59ff425cf999eb2eb1a5dd509633e480e950ef02594ee8db0272d90215e25f16` records 1,133,713 retained bytes, seven media segments plus initialization, and a 69.892-second buffered extent. It records 51 HTTP200 responses with stream-protection status 2, correct selected-audio identity, player time equal to the buffered end, zero reloads, and zero observer errors. The final state is `sdk_stalled`, not EOS. No snapshot resume was requested in this trial.

V6 result SHA256 `892b50cd18b457c50fc6e774caee2d7796b8e7efecba479725fed5324c05bdd6` records stream-protection status 3 during passive normal-player observation; the custom native producer never began. Its duration was 31.59 seconds. The resulting source-refusal deadline and all earlier attempt histories remain intact.

HTTP200, a token-presence boolean, or a valid prefix do not establish stream acceptance or completeness. A zero context-count does not independently prove a missing-context bug: the saved diagnostics do not establish that the server supplied a context update which the client discarded.

## Round 1 decisions

- Reject “upgrade for PR54” and “advance the stuck playhead” as new repairs: the relevant implementation is already present and the saved playhead progressed.
- Preserve the requirement for a complete matching normal-response SPS1 proof before a separately admitted native producer can begin. No such proof exists for the refused trial.
- Keep the existing segment ledger, exact binding, EOS/time-coverage gate, full-file validation, and Drive-proof-before-deletion lifecycle. The 69.892-second prefix is incomplete evidence and must not become a completed recording.
- Treat the separate `available_at` repair in the direct HTTPS downloader as a useful timing-contract correction. It does not establish an explanation for SPS2/SPS3 or justify another native attempt.

There is no newly demonstrated full-file native approach in this round. Changes to attestation, fingerprint, proxy, cookies, or repeated profile creation are outside this review and were not proposed as recovery actions.
