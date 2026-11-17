# Native format policy: legacy tracks and live-provider callbacks

Reviewed offline on 2026-11-17 against installed yt-dlp `2026.11.16.232655dev`, WPC provider `1.1.2`, and googlevideo `5.0.1`. This is a policy and implementation proposal, not a new source-acceptance result. No source requests or media transfers were made for this review.

## Legacy audio coverage

The pinned YouTube extractor assigns language preference **10** to an explicit original label, **5** to a default-only track, and **−1** with unknown language when `audioTrack` is absent. Therefore a selector requiring preference10 excludes legacy unlabeled audio. Two retained metadata snapshots exhibit the excluded shape: three AAC/Opus representations with unknown language and preference−1. Normalized metadata does not retain enough raw track evidence to prove the complete client inventory. The first two failed cohort jobs did not save that inventory, so their failure causes remain unresolved. [Primary extractor: `get_language_code_and_preference` and `_extract_formats_and_subtitles`](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/youtube/_video.py).

Keep strict explicit-original selection for labeled tracks. A separate legacy branch may accept a single **inferred provider track**, represented at several codecs/bitrates, only from the complete returned-client inventory before missing-URL, SABR, or other format filtering. Require the correct video, a successful player response, untruncated valid format arrays, unique unambiguous base itags, and no exposed audio-track language, default/dub/secondary/descriptive markers, conflicting client inventory, or unresolved variants. Completeness here concerns the returned client response; it does not prove a provider-wide inventory.

Record `origin_basis=provider_single_legacy_track_inference`, `origin_inferred=true`, `original_explicitly_verified=false`, and unknown source language. Preserve sanitized candidate evidence and bind the selected representation to that evidence. Do not manufacture preference10, an original label, or English language. Caption translation-language lists are not audio-track inventories.

| Offline fixture | Required result |
|---|---|
| Unique unlabeled139/140/251 representations, complete raw inventory | Accept only as inferred legacy track; language unknown |
| Default-only preference5 | Hold; default does not establish original |
| Explicit original plus dubbed alternatives | Select the explicit original only |
| Duplicate ambiguous base itag | Hold |
| URL-less/SABR alternative reveals another language or auto-dub | Hold legacy inference |
| Incomplete, malformed, or truncated inventory | Hold |
| No usable audio or DRM-only formats | Hold |
| Only normalized−1/unknown-language metadata available | Diagnostic candidate, insufficient raw inference evidence |

## Separate SABR integration finding

googlevideo calls `onMintPoToken` at startup and on pending/rejected protection responses. The existing project callback returns a copy of one captured token; it is not a live provider refresh. A future supported bridge would retain the WPC provider and downloader lifetime, request through the actual matching client/content-binding context, and return decoded token bytes without logging or persistence. Calling the extractor convenience function again does not guarantee freshness: its installed request sets `bypass_cache=false`; the provider framework supports an explicit fresh request. [SDK callback implementation](https://github.com/LuanRT/googlevideo/blob/main/src/core/SabrStream.ts), [WPC provider](https://github.com/coletdjnz/yt-dlp-getpot-wpc/blob/main/yt_dlp_plugins/extractor/getpot_wpc.py), [provider request contract](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/youtube/pot/provider.py).

The SDK does not await its initial callback before starting streaming and catches callback errors internally. A bridge needs an awaited initial token, bounded serialized refreshes, and an outer abort on provider failure. Preserve the actual visitor/video-binding experiment and client context; do not combine unrelated client credentials or infer acceptance from token presence. Existing refusal stops remain in force. This is a concrete future integration requirement, not an established explanation for the earlier plateau or protection rejection.

Also, SDK `buildSabrFormat().isOriginal` can be inferred from the absence of other flags. It is not equivalent to an explicit original declaration; the existing strict observer correctly checks the published original tag separately. [Primary format normalization](https://github.com/LuanRT/googlevideo/blob/main/src/utils/FormatUtils.ts).
