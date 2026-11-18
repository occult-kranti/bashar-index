# Decoded DRC metadata and one proven native recovery

Checkpoint: **18 November 2026, 00:05:09 UTC**. This report contains aggregate
evidence and protocol interpretation, not private source metadata, signed URLs,
credentials, transcript text or source-access authority.

## The representation mismatch

Earlier local format holds recorded normal and dynamic-range-compressed (DRC)
representations of the same audio. The normal rows were unlabeled; the DRC rows
contained `xtags`. Independent diagnostic projections showed that the top-level
and URL values differed, but the old text parser could not determine the
top-level value's semantics. Missing diagnostic fields in older attempts do not
prove that those attempts had the same cause.

The maintained YouTube.js schema defines FormatXTags as a sequence of key/value
messages. Its format parser URL-decodes and Base64-decodes the top-level field
before reading the protobuf. This is different from parsing a transport query
projection as text. The parser recognizes a DRC marker separately from language
and audio-content labels. These are primary implementation references, not a
guarantee about every future response:
[common.proto](https://github.com/LuanRT/YouTube.js/blob/main/protos/misc/common.proto)
and [Format.ts](https://github.com/LuanRT/YouTube.js/blob/main/src/parser/classes/misc/Format.ts).

The project implements only the bounded schema needed for inspection. Inputs
are capped at 512 encoded characters, 256 decoded bytes and eight pairs.
Unknown fields, duplicate keys, malformed lengths, noncanonical varints and
invalid encoding reject. Public diagnostics contain enums, counts and booleans;
they do not retain raw values. The source policy admits the processing exception
only when explicit DRC metadata and every available tag projection agree on the
single known marker. All semantic track checks remain in force.

## Acceptance remains narrow

The complete returned-client catalog must still establish the requested video,
playability, valid bounded arrays and compatible audio representations. A DRC
counterpart needs a unique normal itag/codec base. Only normal audio can be
selected, with exact positive raw/selected byte-size equality before transfer.
DRM, contradictory clients, language/default/dub/descriptive/secondary labels,
unknown tags and ambiguous duplicates remain held. A declared false semantic
field is still a declaration; it is not discarded as missing metadata.

The legacy branch remains explicitly inferred. It does not turn a default track
into a verified original, infer the voice or language, or use subtitle language
as audio evidence. The existing explicit-original branch and HTTP/quality gates
are unchanged. Upstream convenience flags are not substituted for this proof.

## Actual bounded recovery

One previously held target received a separate exact, materially changed-code
admission. Fresh raw metadata contained **13 audio-bearing representations:
7 normal and 6 DRC**. All six DRC counterparts decoded to the known processing
marker. The worker selected normal AAC and transferred it through the same
stock headful WPC / upstream yt-dlp HTTPS route.

| Observed result | Value |
|---|---:|
| Native AAC file | 10,339,840 bytes |
| Container extent | 638.850612 seconds |
| Audio packet count | 27,513 |
| Worker elapsed time | 14.094 seconds |
| Parent source/cleanup elapsed time | 17.937 seconds |
| Coordinator wall time including publication | 36.172 seconds |

Exactly one finished callback matched the selected/final size. The strict packet
probe passed, and exact audio/metadata Drive proofs preceded retirement of the
owned local files. No re-encoding was performed. This is complete native
transport and archival evidence, not a human accuracy review, every-word
coverage claim or full-decode claim. Source language remains unknown/inferred.
An outer cleanup report initially read the wrong process-status field; a
separate local correction used the existing owned-process audit and released
only its matching reservation. The original report remains preserved. No
download, media hash, probe or Drive verification was repeated for that correction.

## Continuation and limits

At the frozen aggregate checkpoint there are **128 native pairs, 77 native ASR
bundles, 156 deduplicated audio entries and 122 audio entries with saved text**.
A separately amended 40-target source run and 42-input English consumer are
active. A retained recording failed word alignment, then a separately versioned
segment-only attempt failed segment timing. The exact cause remains unresolved;
that recording is excluded from the healthy one-input-per-process consumer.

The prepared recovery proposal separates ten detailed-diagnostic holds from
twenty older holds with uncertain causes. It and the finite long-campaign
proposal remain **disabled**. Any later recovery needs an exact reviewed scope
and fresh raw acceptance before media. No denied asset is retried by this change.
Bound-media 403 quarantines, unknown/control 403 holds, all provider 429s,
protection checks and the durable three-item/600-second breaker are unchanged.
