# Publisher companions and audio editions, 17 November 2026

Official publisher sources can supply useful material while YouTube's native-audio lane is held. These records keep their own origin and edition labels. They do not increase native YouTube acquisition, caption completion or full-ASR counts.

## Written companions for 16 queued videos

Two pages of [Daniel Scranton's official feed](https://danielscranton.com/feed/) yielded author-written articles with exact links to 16 videos in the frozen latest-20 queue. The archive preserves each article's author content, source URL, exact video association, publisher date, original fragment and text hashes. Reader comments and sidebar content are excluded. These are publisher-written companions, not verified verbatim spoken transcripts or YouTube captions.

The [110,520-byte batch](https://drive.google.com/file/d/1sr2f-E3x3ueY6_fIZp4ftTazOxM11YRI/view) is verified on Drive with exact identity, size and MD5. SHA-256: `bf0305919897682f3f61dbb31705c08d86d27147b0f9b359c7fb99332c50d6af`. Item paths retain the channel, exact queued ID and `PublisherText` role. No full article text is published in this repository.

## Linked podcast edition

Lee Harris's [November 2026 update page](https://www.leeharrisenergy.com/nov-2026-energy-update) embeds the queued video. His [official podcast feed](https://feeds.captivate.fm/impact-the-world/) links that page and supplies a free MP3 for the update. This is an explicit two-hop publisher association. The MP3 measures 1,401.533333 seconds; the feed declares 1,402 seconds and the YouTube queue lists 1,417 seconds. The difference remains an edition caveat, not a claim about what was cut.

The [33,962,733-byte MP3](https://drive.google.com/file/d/1NDSvNeitPq146KqeOiFnjVxsLcgpgJ-8/view) and [separate provenance](https://drive.google.com/file/d/1Lp3uggUiVI9qSzJFgUVBB91n6k9hTtDK/view) have exact Drive identity, size and MD5 receipts. Audio SHA-256: `23bb8d0c7493f5d0959db765eca9fd6c8aeb1e949e3db404229a1c4c202a67ed`. Native MP3 bytes were retained without re-encoding, under the linked video's `PublisherVariants` directory.

The collector uploaded one exact three-object batch. Durable proofs preceded removal of only 34,076,039 newly owned temporary bytes. Source records remain in separate publisher-companion and publisher-variant journals. Current-journal deduplication is recorded explicitly; an earlier legacy source-URL index was not established, so no claim of global newness is made. Content hashes permit later reconciliation.

## Search scope and limits

The first bounded pass covered four actually tracked channels: Daniel Scranton, Lee Carroll/Kryon, Steve Nobel and Lee Harris. Kryon's public MP3 archive had no established queued-ID match; Steve Nobel's examined feed items did not establish one. The earlier Dreemtime/other-channel fallback audit remains in [its own report](official-audio-fallbacks-2026-11-17.md).

A second bounded pass covered Aaron Abke, Sounds True, Elizabeth April and Lauren Galey. Sounds True has public audio/transcripts, but examined publisher data did not establish queued-ID links. Elizabeth April's examined feed similarly supplied no exact match; Lauren Galey's public links did not establish an accessible enclosure. These bounded searches are not proof that no alternative source exists.

## Qualified publisher source-context edition

An Aaron Abke episode in [the official Jesus Way podcast feed](https://anchor.fm/s/1016db968/podcast/rss) carries an exact queued video ID in three publisher-description source-reference parameters. It has no direct watch/embed link. This is qualified publisher source-context evidence; the association and edition have not been human- or waveform-verified.

The [126,972,655-byte audio](https://drive.google.com/file/d/1TX_pBUiRu7wRExXL9lv-dd-SpEDSh5VP/view) and [10,274-byte provenance](https://drive.google.com/file/d/1ekKIs6QtmMnrANTZNiLe16Ipze7drz1v/view) are exact-Drive verified. Measured duration is 7,935.722676 seconds, compared with the queue's 7,936 seconds and the feed's declared 7,935 seconds. Audio SHA-256: `232b6215eeecd71ff3991ad4872df9a54b3ceef2cc78012e1f50302985164b03`. Duration agreement does not replace the source-association caveat. The file remains a publisher edition and does not complete a native YouTube item.

The publisher RSS declares `en-us`; this is feed-scoped metadata, not independent verification of every spoken interval. A separate metadata-only snapshot establishes Lee's official feed language as `en`, preserving its earlier provenance unchanged. These declarations can support explicitly typed publisher-edition ASR admission using the existing English model. Any such transcript must remain in its edition's own path and journal, separately from native YouTube ASR.

## Exact-linked publisher transcript

The [official Cosmic Agency transcript page](https://swaruu.org/en/transcripts/extra-bits-on-extraterrestrial-races-conversations-and-descriptions) identifies Cosmic Agency/Gosia and explicitly links the original queued video. Its English-page content was preserved as a publisher-declared, untimed transcript, with publisher translation status unspecified and spoken coverage unverified. It is distinct from the 16 author-written companions and from YouTube captions.

The [27,539-byte transcript ZIP](https://drive.google.com/file/d/1RPNiamDG7lq3-QRb-di4-u5parfJyVOQ/view) is exact-Drive verified. SHA-256: `b3a0c0be79a07cc863fb8c6e6529e74f50939011c9d1ce9c157dfb51919a2840`. It retains the exact original-video link, author/date/language evidence and body/text hashes, with no reader comments or unrelated transcript bodies. Newly owned temporary bytes were removed after proof. Legacy duplication remains unknown; no global-newness claim is made.

This final bounded source class examined four current channels. Magenta Pixie's official site established its Rumble ownership, but exact episode mapping was not established and a listing returned 403; no retry or media capture followed. Blossom Goodchild's current page embedded other IDs, and Nora Herold had no established exact-ID transcript/mirror. These outcomes do not justify title-only substitutions or a new source retry loop.

## Full publisher-edition ASR

A separate [publisher-edition adapter](../pipeline/PUBLISHER_VARIANT_ASR.md) reused the already installed English Distil model and existing transcription/verification helpers. Its admission binds the actual publisher audio/provenance proofs and feed-language evidence. Publisher provenance is not reshaped into native YouTube metadata, and association/edition caveats remain in the output. One exclusive CUDA model processed both complete editions sequentially; there is no duration exclusion for the longer program.

| Edition | Decoded seconds | Unreviewed words | Segments | Run seconds |
|---|---:|---:|---:|---:|
| Aaron Abke | 7,935.7226875 | 22,280 | 1,736 | 280.703 |
| Lee Harris | 1,401.528 | 3,700 | 295 | 48.578 |

The [Aaron result](https://drive.google.com/file/d/1eq4yrCengg398nejNdSVetFTkdqmwRIN/view) is 573,990 bytes, SHA-256 `aadb3e6cc5aa4332fc2dd31bc4459106d88d5232f8e76844871f56706b30eafa`. The [Lee result](https://drive.google.com/file/d/10-WWHxcDKVAJznShEMceAEaVRP2n6LwE/view) is 99,509 bytes, SHA-256 `ebb658a80143905a471600eaee333a0ff0504472499fce29bb2082fba4679045`. Their decoded/container duration differences remain explicit; neither was padded or presented as native YouTube time alignment.

The [124,221-byte runtime/source supplement](https://drive.google.com/file/d/1HbNnKMBG61fmELfqJMWZA737zb6JFK0k/view) was Drive-verified before result publication. Exact Drive identity, size and MD5 proofs preceded separate publisher-variant ASR receipts and retirement of only four newly owned input copies (160,948,448 bytes). Source Drive objects, original metadata, feed snapshots and earlier held inputs remain untouched.

Both results remain unreviewed. The two runs recorded 320 fresh GPU samples without telemetry error/fallback. Maximum observed 30-second utilization was 45.07% and 61.67%, instantaneous utilization reached 100%, peak VRAM was 1,596,682,240 bytes and maximum temperatures were 71/72 C. The GPU was released. The 70% governor is a soft rolling target. Ordinary native-source ASR remains 28; the two full publisher-edition results have their own journal and dashboard counter.
