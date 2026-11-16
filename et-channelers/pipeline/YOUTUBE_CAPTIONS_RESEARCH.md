# YouTube captions: collection research and decisions

Reviewed November 16, 2026. This document records the implementation choice and
upstream evidence; it does not claim captions have been collected successfully.
Research used documentation, source code and issue reports, without caption requests.

## Selected scope

For every video whose audio is downloaded, collect **English published captions and
original English automatic captions only**, including `en`, `en-US`, `en-GB` and
other English regional variants. This supersedes the earlier all-language proposal.
Keep English tracks supplied as published captions; do not request machine-translated
English tracks, other languages, live chat, or subtitles for automatically dubbed
audio. Where the provider does not
establish a track's origin, retain that uncertainty rather than inventing a source
language or claiming that a filename proves originality.

Existing captions can avoid later speech recognition. Availability and quality must
be assessed separately: access failures remain pending, and sparse or incomplete
captions do not prove a complete transcript. Downloading and parsing captions uses
network I/O and small CPU operations; it needs no GPU, ASR model, media conversion,
paid browser extension or subscription.

## Tool choice

| Tool | Role | Requirements and limitations |
| --- | --- | --- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp#subtitle-options) | Primary collector; reuse the audio pipeline's extraction where possible and preserve native timed files. | Stable `2026.10.26` requires Python >=3.11. Its default dependency set pins `yt-dlp-ejs==0.8.0`; its Deno extra requires >=2.9.8. The local environment was subsequently observed at nightly `2026.11.15.232800dev`, EJS `0.8.0`, Deno `2.9.8`. A newer version is not proof that a refusal is fixed. |
| [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api) | Optional structured-transcript adapter with explicit manual/ASR selection. | Version `1.2.5`, Python >=3.8,<3.16. Uses an undocumented web interface; no universal availability guarantee. Do not use it to repeat refused requests through another route. |
| [YouTube Data API](https://developers.google.com/youtube/data/reference/rest/v3/captions/download) | Authorized channel-owner workflow. | Caption download requires permission to edit the video; it is not a general public-caption endpoint. |

Version references: [yt-dlp release dependencies](https://github.com/yt-dlp/yt-dlp/blob/2026.10.26/pyproject.toml),
[EJS setup](https://github.com/yt-dlp/yt-dlp/wiki/EJS),
[transcript API requirements](https://github.com/jdepoix/youtube-transcript-api/blob/v1.2.5/pyproject.toml),
[transcript API 1.2.5 release](https://github.com/jdepoix/youtube-transcript-api/releases/tag/v1.2.5).
The latter release announces Python 3.15 support and test changes, not a caption-access fix.

## Track identity and preserved evidence

`--write-subs` selects published subtitles; `--write-auto-subs` adds automatic tracks.
In yt-dlp's [selection implementation](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py),
published subtitles win when both dictionaries have the same language key. A combined
CLI invocation therefore does not guarantee that both originals are preserved.

Avoid `--sub-langs all`. The [YouTube extractor](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/youtube/_video.py)
can enumerate many generated translations; `skip=translated_subs` alone does not
filter every ASR translation. Select track identities explicitly from provider
metadata. Do not infer manual status from a short language code, or original audio
language solely from the `-orig` suffix. An [upstream report about dubbed tracks](https://github.com/yt-dlp/yt-dlp/issues/17659)
was closed for insufficient reproduction evidence, so it is a caution, not a confirmed universal bug.

Prefer one native timed representation per selected track, with JSON3 followed by
VTT as format preferences. `--sub-format json3/vtt/best` chooses one format; it does
not download both. Preserve the original bytes and derive normalized segments/text
locally. Retain timestamps and handle overlapping rolling ASR cues without deleting
legitimate repeated speech. The transcript API's JSON is its parsed segment output,
not raw YouTube JSON3.

A private bundle/receipt should retain video identity, track identity, language,
published/ASR status, original/translated status and provenance, format, retrieval
time, extractor version, cue count and content hashes. Record unknown attributes
explicitly. Store caption text only in the private archive, and remove signed URLs,
request headers, cookies and tokens from archived provenance. Catalog entries contain
track/language counts and artifact proof, not transcript bodies.

## Refusals, retries and token providers

Captions use the separate **Subs** proof-of-origin context. Successful audio download
does not establish caption access. The [yt-dlp PO-token guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide)
describes this distinction; missing-token warnings can accompany omitted tracks.
Treat `blocked`, `rate_limited`, `token_required`, `no_requested_language` and confirmed
`no_captions` as distinct outcomes. An empty response or empty track list with warnings
is not evidence that captions do not exist.

The [transcript API issue 592](https://github.com/jdepoix/youtube-transcript-api/issues/592)
reports an empty-body/token case; the maintainer questioned its reproducibility on
the current release. Preserve defensive classification without assuming that every
video is affected. Its [README](https://github.com/jdepoix/youtube-transcript-api#cookie-authentication)
also states that cookie authentication is currently unavailable. EJS JavaScript
challenge handling and Subs tokens are different mechanisms.

| Optional upstream integration | Verified capability | Operational cost and limitation |
| --- | --- | --- |
| [Bgutil 2.0.2](https://github.com/Brainicism/bgutil-ytdlp-pot-provider/blob/master/plugin/yt_dlp_plugins/extractor/getpot_bgutil.py) | Source declares GVS, Player and Subs support. | Requires matching provider/plugin components and a JavaScript service or script. The [README](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) requires yt-dlp >=2025.05.22 and Node >=22 or Deno >=2.0.0 outside Docker; per-call script mode is discouraged for high concurrency. |
| [WPC 1.1.2](https://github.com/coletdjnz/yt-dlp-getpot-wpc/blob/main/yt_dlp_plugins/extractor/getpot_wpc.py) | Source declares Subs support although its README lists only GVS/Player. | Experimental browser-based integration; requires Chrome/Chromium and yt-dlp >=2025.09.26. More process/memory overhead than a plain caption request. |

These external plugins are featured by yt-dlp but are not affiliated with it. Their
presence is not a guarantee against 403 responses or account/IP restrictions. Do not
install or activate them automatically in response to a refusal. Existing project
source-access controls and cooldowns still apply; this research does not authorize
proxy rotation, cookie harvesting, alternate-client retries or access bypasses.

Start with one caption worker sharing source pacing with audio ingestion. Retry
transient network/5xx failures sparingly; honor server retry delays and stop/cool down
on systemic 403/429 responses. Preserve successful tracks when another fails. Reuse
durable receipts so a resume does not redownload verified tracks. Keep caption
completion separate from audio-pair completion, upload exact files with existing
size/MD5 verification, and delete local caption files only after durable Drive proof.
All local artifacts count toward the same private-root storage budget.

## Existing code and stale examples

The legacy `fetch_captions.py` suppresses warnings, which can turn omitted/token-limited
tracks into a persistent `no_captions` outcome. It also prefers the shortest language
filename without actual type provenance. A new collector must address both cases.

[Older StackOverflow answers](https://stackoverflow.com/questions/76856230/how-to-extract-youtube-video-transcripts-using-youtube-api-on-python/78620356)
use removed `get_transcript` / `list_transcripts` methods. Current upstream usage is
`YouTubeTranscriptApi().list(video_id)`, then explicit track selection and `fetch()`;
`YouTubeTranscriptApi().fetch(video_id)` is the convenience form. Follow the current
[upstream API examples](https://github.com/jdepoix/youtube-transcript-api#list-available-transcripts)
instead of copying those older recipes. Automatic translation is an explicit derived
operation, not an original transcript.
