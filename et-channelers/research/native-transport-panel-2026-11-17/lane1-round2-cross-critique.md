# Native transport panel — lane 1, round 2 and cross-critique

Reviewed 2026-11-17 after the independent lane-2 review. This round challenges the conclusions in [round 1](lane1-round1.md); it does not authorize or execute source requests.

## Independent checks and conclusions

| Challenge | Evidence and decision |
| --- | --- |
| Could the old audio-only restore defect still be active? | The exact saved V5 build manifest and frozen bundle hash agree. Its compiled snapshot path conditionally checks video, and this trial used no snapshot. Rejected as the cause of the saved fresh-start stall. |
| Could old protobuf names silently select the wrong track? | Installed generated field numbers and `buildRequestBody` match the newer upstream semantics. Actual diagnostic requests report one selected audio format matching output, no selected video, and one initialized format. No concrete field-mapping failure found. |
| Could a nonadvancing playhead impose the prefix ceiling? | The trace reaches player time69,892ms and buffered extent69,892ms. Later requests retain that correct completed-prefix position while media stops arriving. Fabricating later positions would neither prove continuity nor acceptance. |
| Could a server-requested reload have been ignored? | Saved reload count is zero. The current adapter has no reload callback, which is a conditional long-session limitation; it is not an observed cause here. Any future reload support would need renewed public metadata and the same complete media identity, not silent substitution. |
| Does the token callback actually refresh an accepted token? | No. `browser_sabr_adapter.mjs` captures one byte array, and `currentToken` returns a clone of those original bytes. The SDK callback name must not be presented as proof of refresh. No token values were inspected or exported. This is a conditional stale-snapshot limitation, not a demonstrated explanation for the saved failure; V6 was refused before this callback could matter. |
| Could a partial prefix be resumed to evade the hold? | No. The local sink requires a verified persisted prefix and segment boundary under the same complete format identity; ordinary SDK snapshots do not authorize resume. The current source refusal and spent-attempt history remain authoritative. |

The callback's fixed snapshot is worth documenting because SDK token-generation counters can change even when the returned bytes do not. This review does **not** recommend minting, manufacturing, changing, or repeatedly refreshing attestation. Under the present stopped scope, fail and retain is the appropriate behavior when the accepted context is unavailable or expires. A future ordinary-player integration would need evidence of a legitimate current context before any engineering admission; no such work was run here.

## Lane-2 cross-critique

Lane2 independently agreed that the modern installed SDK plus the progressed69.892-second playhead rule out presenting the historical restore/playhead change as a newly discovered fix. Its inspection identified a different concrete integration gap: our `extract_info(download=False)` followed by a custom HTTPS stream skipped the upstream downloader's selected-format `available_at` wait.

The narrow patch was reviewed without a source trial. It examines the selected `requested_formats` rather than unrelated format candidates, validates finite timestamps, waits interruptibly for at most30seconds, and defers longer waits with an item-specific availability deadline. It rechecks storage admission before GET. A prior future deadline prevents another extraction request. It does not modify shared source-refusal cooldowns or request an ad bypass.

No blocking issue was found in that scoped review. Lane2 reported18 focused offline tests, including browser-lease behavior. Those results belong to the timing contract; they are not a successful YouTube download benchmark. It remains unknown whether the failed native trials had any selected-format availability deadline, and that field has no demonstrated connection to their SPS3 response.

## Required evidence before a future full-file batch claim

1. For the experimental SABR route, a separately admitted, unexpired source context supplies the existing complete matching SPS1 proof. An independently admitted ordinary HTTPS format uses its own upstream preconditions and complete-transport validation; SPS1 is a SABR-specific signal. Current refusals, deadlines, STOP markers, and attempt lineage remain preserved.
2. One file completes with ordered original-format segments, valid declared segment lengths, matching hashes, protocol EOS, and source-duration coverage. No fabricated seek, guessed snapshot, or prefix-only promotion.
3. Full-file validation and exact Drive object ID/size/MD5 succeed before owned spool deletion. Only then may bounded concurrency be considered under the shared storage cap.
4. Any later availability wait, context expiry, or reload is distinguished from source refusal in diagnostics; no generic retry loop treats it as success.

These are acceptance criteria for future authorized work, not permission to launch it. This two-round review found no additional source request justified by a newly proven native-transport repair. Qualified publisher mirrors remain separately useful and retain their association caveats; they do not increase native YouTube completion counts.

The finding about the captured SABR callback does not evaluate a supported browser-backed PO-provider running within the full upstream downloader. That separate lane-2/lane-3 candidate remains unproven and needs its own bounded parent admission; it must not be described as a demonstrated repair of this SABR stall.
