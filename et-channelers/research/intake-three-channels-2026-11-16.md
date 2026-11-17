# Charlie Wilde, Infini Global and Odyssey of Ascension intake

Requested and researched on 2026-11-16, America/New_York. The three metadata-only intakes committed on 2026-11-17 at approximately 03:27 UTC. No media or captions were requested by this intake. Research used ordinary web search and first-party pages; no Exa queries were made.

## Channel identities and scope

| Collection | Canonical channel | Listed Videos / recorded streams / Shorts | Attribution |
|---|---|---:|---|
| `charlie-wilde` | [Charlie Wilde // Channeling SEVEN](https://www.youtube.com/channel/UCcaCZEavb84-wVo_D6JipTg), `@CharlieWIldeSEVEN` | 86 / 19 / 63 | Charlie's [official site](https://ascensionseven.org/) links the account. |
| `infini-global` | [BASHAR AYAKO](https://www.youtube.com/channel/UC1IaSPbXaOC0KVcqPW9hSDw), `@InfiniGlobal` | 29 / 0 / 0 | Publisher collection. Its uploads name Ayako Sekino, but current account ownership is not independently established. |
| `roxanne-swainhart` | [Odyssey of Ascension](https://www.youtube.com/channel/UCoxINFqPqOU6W8OOTi1nqeQ), `@OdysseyofAscension` | 704 / 247 / 0 | Roxanne's [official biography](https://www.odysseyofascension.com/about.html) links this channel. |

Canonical IDs, handles, channel descriptions and tab listings came from one completed flat extraction per channel, with zero retries and three seconds between requests. None reached the 20,000-entry per-tab ceiling or returned a source access refusal. These are observations of available listings at capture time, not guarantees that every historical or private upload is included.

Sixteen ordinary search phrases supported discovery. Unrelated namesakes, repost pages and search snippets were not accepted as ownership evidence; the three channel extractions and linked first-party pages supplied the identity checks.

The Roxanne collection maps to the existing Atlas discovery person `person-05fde1a08a4e` and historical profile `em-roxanne`; this intake does not create a second baseline Atlas person. The collection slug, discovery person identifier and historical profile route belong to separate existing namespaces.

## Relationship evidence and limitations

**Charlie Wilde → Pleiadian SEVEN.** Her [first-party About page](https://ascensionseven.org/about/) identifies Charlie, describes her connection with the Pleiadian SEVEN, and identifies her as a channeler. The channel's own title also presents channeling of SEVEN. This supports a self-reported relationship. It does not establish the speaker or claimed source of every upload, and it does not equate this collective with similarly named groups elsewhere.

**Ayako Sekino → Bashar, historical self-report.** The [Japanese official profile](https://www.sekinoayako.art/profilenew), in the passage following the reported 1987 contact, explicitly describes a subsequent period of channeling with Bashar. The [official English version](https://www.sekinoayako.art/en/profilenew) likewise describes channeling and identifies her development of Infini. This is a channeling claim, not an inference that she was merely interpreting Darryl Anka. The official profile describes two years; an [interview-producer biography](https://www.interviewwithed.org/ayako-sekino) describes five and says she later stopped that form of expression. The chronology remains unreconciled; no present-day channeling frequency is asserted.

The [current official English site](https://www.sekinoayako.art/en/english) links a different YouTube route, `youtube.com/c/AyakoSekinoClass/videos`. Its subject association does not prove ownership of `@InfiniGlobal`. Accordingly, `infini-global` is registered as a **publisher**, with `primary_person_basis=channel_publisher_not_speaker`. Ayako remains a separately sourced relationship subject; she is not assigned as every upload's performer. No second Ayako channel was added.

**Roxanne Swainhart → Ocyphius and Sylvester.** The [channel's own description](https://www.youtube.com/channel/UCoxINFqPqOU6W8OOTi1nqeQ) names Roxanne and these claimed sources. Her [biography](https://www.odysseyofascension.com/about.html) describes conscious channeling. These remain claims about the practice, not independent proof of the claimed beings or validation of their statements.

The [intake relationship CSV](intake-three-channels-relationships-proposed.csv) separates four accepted profile relationships from the unresolved video attribution below. The parent research lead independently read the official Charlie, Ayako and Odyssey source pages and accepted only those four relationships; see the [acceptance audit](intake-three-channels-source-review.json). They were appended to the [normalized evidence table](analysis-plan-2026-11-16/discovery-relationships.csv), preserving all previous 115 rows. The updated table and public Atlas projection contain **119 relationship records, 31 people and 90 source labels**. These are counts of attributed claims, not independently verified beings or speech samples. Medical or therapeutic claims are not endorsed by this intake.

## Explicitly requested Bashar reference

The supplied [video `Rcemlb-WPPY`](https://www.youtube.com/watch?v=Rcemlb-WPPY) appears in Odyssey's Videos listing with the title *A conversation with Bashar*, duration 3,400 seconds and original listing rank **698**. Its title and uploader establish a useful research lead; they do not, by themselves, identify the human performer. The user's proposed alternative-human Bashar attribution remains a candidate pending description or performance evidence.

The video is present once in the full queue and is also preserved in the separate private `jobs/queue_requested_videos.csv` priority supplement. Its original rank remains 698. The supplement must be dispatched with `--entire-queue`; it must not be treated as a fabricated newest-20 row. Its companion metadata records the explicit request and unresolved performer. A future dispatcher should consider this pinned supplement before ordinary priority work without replacing the newest-20 queue.

## Published queue changes

| Scope | Before | After | Added |
|---|---:|---:|---:|
| Tracked YouTube channels | 71 | 74 | 3 |
| Newest 20 Videos | 1,360 | 1,420 | 60 |
| Newest 50 Videos | 3,320 | 3,449 | 129 |
| Full unique-video inventory | 66,446 | 67,594 | 1,148 |
| Remaining after newest 50 | 63,126 | 64,145 | 1,019 |

Infini Global has 29 listed Videos, so its newest-50 contribution is 29. No missing entries were invented. The full inventory spans 112 source directories, including linked historical sources; this is distinct from 74 tracked channels. The collection registry now has 113 entries, including publishers and organizations.

All pre-existing queue row dictionaries and their order were preserved. New entries retain source tab and listing rank, with no duration filter. Per-item `entity` and `channeling` fields remain empty. The source registry CSVs preserve their previous byte prefixes and append three rows.

Publication used the existing [intake helper](../pipeline/intake_channel.py) under one collector lock, with a separate durable before/after backup and receipt for each channel. The private `jobs/intake_three_channels_receipt.json` records source hashes, registry hashes, queue totals, preservation checks and the pinned reference. Backups remain under private `jobs/queue_backups/`; generated listings and metadata stay outside Git.

The separate nine-item English ASR frame uses a frozen copy of the previous 1,360-row newest-20 CSV. This intake changes neither that frame's membership nor its admitted source proofs.
