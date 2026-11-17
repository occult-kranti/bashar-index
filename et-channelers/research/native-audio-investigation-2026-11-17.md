# Native audio transfer investigation, 17 November 2026

Checkpoint: **06:12 UTC**. Scope is a native encoded-audio batch transport, with no real-time playback recording. The owner requested automated installation and testing; dedicated Chromium handles extension activation. No further manual reload or toolbar click is required for this research.

**Diagnostic follow-up, 06:29 UTC:** a separately admitted automated Chromium run retained the identical 1,133,713-byte / 69.892-second prefix and stopped with `sdk_stalled` after 104.5 seconds. All 51 SDK responses had HTTP 200; the observed protection events remained status 2 (pending). The last request correctly reported player time and buffered coverage of 69,892 ms, matched the full selected audio format and selected no video. There were no reload requests, diagnostic observer errors or observed media 403/429. Thus missing playhead advancement is not the observed fault; the reason the server remains pending is unresolved. Both spent attempts and partials remain intact. The receiver was stopped after the test.

The owner had already confirmed playback beyond 90 seconds in normal Chrome. That user report is distinguished from the dedicated automated result. Windows UI Automation has now reloaded only the owned helper in that existing browser, without CDP, profile/cookie export or restarting Chrome. A further test would use this materially different context, with its own admission and live video/permission check. Preparation is not a completed native download.

## Observed browser result

A dedicated headful Chromium profile loaded extension v0.3.0 and successfully paired with the root-owned loopback receiver. It observed the normal player's current SABR request, then used googlevideo 5.0.1 for audio-only native transfer. The source session stayed in the page; the driver did not copy a personal profile or export cookies, URLs or tokens.

| Observation | Actual result |
|---|---|
| Native output | 1,133,713 bytes; eight initialization/media segments |
| Source coverage | 69,892 ms of a 1,570,961 ms recording |
| Playback at terminal state | Paused at approximately 2.75 seconds |
| SDK request permits | 51 |
| Media HTTP result | HTTP 200 observed; no media 403 or 429 observed |
| Terminal result | `sabr_stream_failed`, before EOS |
| Full validation / Drive upload | Neither occurred |
| Dedicated browser profile | Peak 71,030,070 bytes; cleaned after test |

The partial and its hash/segment ledger are retained privately. The one admitted attempt is spent; the receiver was stopped after the trial. No counter, source deadline or earlier refusal history was reset. The native inventory remains **47 verified pairs**. This result demonstrates transfer independent of the playback clock, but does not establish full-file access, a batch download rate or a completion ETA.

The same integration exposed and fixed three local problems before native admission: MV3 worker dynamic imports, an unbound browser fetch function, and Chrome omitting Origin on authenticated status GET requests. The last fix is narrowly scoped to that authenticated loopback GET; pairing and mutations retain exact-Origin checks.

## Primary-source findings and next evidence

Upstream [issue 52](https://github.com/LuanRT/googlevideo/issues/52) reports a similar short-media cutoff. The maintainer linked the [SabrStream rewrite, PR 54](https://github.com/LuanRT/googlevideo/pull/54). The installed 5.0.1 already includes that rewrite; it is not a missing patch to reapply. The current [SabrStream implementation](https://github.com/LuanRT/googlevideo/blob/main/src/core/SabrStream.ts) advances the reported player position from buffered media for download use. Paused DOM playback alone is therefore insufficient to explain this failure.

HTTP 200 can contain control messages rather than useful media. The tested adapter replaced the underlying SDK error with a constant code; it did not retain enough safe control diagnostics to identify this failure. No stream-protection rejection, server seek, codec binding failure or successful full-file workaround is inferred from that missing evidence. The next code change should export only bounded numeric/event classifications: protection states, selected/initialized track counts, server seek positions, request/segment progress and allowlisted error categories. Raw URLs, error strings, config, headers, tokens and response bodies must remain excluded.

A new source trial requires a material diagnostic or protocol change, an independently reviewed admission and preservation of prior attempts. One complete EOS, contiguous segment proof, full packet/duration validation and exact Drive pair proof remain required before concurrent batch workers are admitted. The existing direct-media and caption deadlines continue independently. Real-time recording remains parked.

## Storage, processing and delivery

The native spool has an 8 GB reservation inside the shared 16 GB managed cap; the owner's overall 20 GB allowance and 2 GB buffer remain enforced. Models, environments, repositories, retained partials and browser staging all count. Completed pairs are uploaded and checked against exact remote IDs, sizes and MD5 before owned local copies are deleted. The GPU is released; 27 already archived sources have Drive-verified ASR bundles, with accuracy unreviewed.

The [dashboard hub](https://occult-kranti.github.io/bashar-index/dashboards/) links collection, predictions, the channel index and Atlas. Its counts are dated snapshots, not proof that an acquisition process is currently running. [The ETA model](collection-eta-2026-11-17.md) remains conditional on recovered full-file access; this partial trial supplies no reliable finish date.
