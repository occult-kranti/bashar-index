# Chromium and yt-dlp recovery investigation

Observation window: November 16 evening Eastern / November 17 00:40–01:14 UTC, 2026. The owner explicitly requested supported browser automation and new repair attempts. This report records failures as well as successful diagnostics; it does not claim all-video recovery.

## Result

Anonymous Chrome 157 playback succeeded for the previously failing public recording. Two fresh browser-backed WPC range probes returned exactly 1 MiB with HTTP 206 and the expected complete resource length. Full native downloads still returned media 403 using the ordinary collector, a browser kept alive through streaming, and yt-dlp's native downloader. A bounded first attempt on a different channel, Dreemtime Academy, also returned media 403. No new full audio pair was verified during this investigation; the total remains 47.

Small range success therefore did not establish whole-file recovery. Browser lifetime was a plausible engineering issue, not a demonstrated cause of these failures. The latest source deadline is retained in private receipts, and the four-worker supervisor preserves its existing retry budget. English caption 429 state remains independent. No personal browser profile, persistent account cookies, account rotation or proxy rotation was used. A shared-browser token-service prototype failed its live test and was stopped and removed from the proposed change.

## Sources and what they established

| Source | Finding and treatment |
|---|---|
| [Official yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide) | Documents distinct media/player/subtitle token contexts, the recommended mweb/provider setup, and browser-backed WPC as an alternative. Supplying a token is not proof every request will succeed. |
| [Official nightly release](https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/tag/2026.11.16.232655) | Installed this newer release, including post-live completeness/status fixes. Those changes did not establish recovery for the tested media 403. |
| [WPC provider repository](https://github.com/coletdjnz/yt-dlp-getpot-wpc) | Installed upstream 1.1.2, inspected its source, and used its WebPoClient implementation in fresh anonymous headless Chromium. Its own description labels it experimental. |
| [Upstream bgutil issue 188](https://github.com/Brainicism/bgutil-ytdlp-pot-provider/issues/188) | A user reports WPC succeeding where bgutil failed. This was a useful alternative-provider lead, not evidence the same repair would work here. |
| [yt-dlp issue 17368](https://github.com/yt-dlp/yt-dlp/issues/17368) | Documents video-dependent token/media failures and the importance of provider/runtime versions. Historical fixes are not assumed applicable to the current source. |
| [Stack Overflow: pytube 403](https://stackoverflow.com/questions/79226520/pytube-throws-http-error-403-forbidden-since-a-few-days) | Community answers suggest different libraries and browser cookies. These are troubleshooting leads; no account-cookie export was adopted and switching library does not prove media or caption recovery. |
| [Stack Overflow: requested headers](https://stackoverflow.com/questions/62447887/how-to-download-mpeg-dash-mpd-file-using-youtube-dl-when-headers-are-requested) | Explains preserving relevant request headers in a different site's manifest workflow. The collector already retains allowed media headers; the answer does not demonstrate a current YouTube fix. |

The lead made five Exa searches with 25 requested result slots, including two Reddit-oriented queries. Returned slots overlap and are not independently verified sources. The Reddit queries returned upstream repository pages rather than a usable Reddit discussion; no Reddit solution was validated. Primary documentation/source code, local package metadata and the actual bounded request outcomes took precedence over snippets. The separate Dreemtime owner records its own four searches/20 slots in its [intake note](cross-channel-events-2026-11-16.md).

## Code delivered

- [browser_source_probe.py](../pipeline/browser_source_probe.py): an explicitly invoked, bounded anonymous Chromium playback diagnostic. It emits only allowlisted fields and never signed media URLs, token contents or cookie data.
- [browser_audio.py](../pipeline/browser_audio.py): lazy optional dependencies, entered yt-dlp/WPC contexts retained until owner-thread lease cleanup, up to four concurrent sessions, finite admission/socket waits, safe error classes, owned-profile cleanup and a process-local cleanup breaker. Full extraction has no hard wall-clock kill and full-file recovery remains unproven.
- [drive_ingest.py](../pipeline/drive_ingest.py): opt-in browser integration, browser lifetime cleanup after success or failure, CLI-only metadata backfills, and actual stream-start/elapsed receipt fields. Browser mode requires at most four workers and at most 16 GB private storage to reserve extra scratch headroom; the active ordinary lane keeps its 17 GB private cap. The browser option is not enabled in the supervisor.
- [collection_eta.py](../pipeline/collection_eta.py): offline queue/receipt/progress estimation with missing-duration scenarios and separate audio/caption bottlenecks. It starts no collector or model.

Focused tests check context lifetime, error cleanup, slot bounds, profile/loop cleanup, source-error preservation, metadata-only behavior, option forwarding and private-state exclusion. They demonstrate implementation behavior under fixtures, not current upstream accessibility. The [ETA report](collection-eta-2026-11-16.md) supplies conditional capacity estimates; recurring refusals prevent a guaranteed completion date. Transcription, embeddings and corpus analysis remain deferred.
