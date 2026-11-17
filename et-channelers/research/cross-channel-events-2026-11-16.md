# Dreemtime Academy intake and future cross-channel event comparison

Research session: 2026-11-16 in America/New_York; intake committed 2026-11-17 at 00:55:54 UTC. This note records metadata discovery and future analysis work. No audio, captions, ASR or corpus analysis was performed by this intake task.

## Verified channel and attribution boundary

[Dreemtime Academy](https://www.youtube.com/channel/UCE6KE5xH13AMUajXvz_w8vA) has canonical channel ID `UCE6KE5xH13AMUajXvz_w8vA` and handle [@DreemtimeAcademy](https://www.youtube.com/@DreemtimeAcademy). One completed, paced, metadata-only flat extraction verified both and the creator's self-introduction as **Hayden Crawford**.

The [current official site](https://www.dreemtime-academy.com/) identifies Hayden as the founder; the [earlier official site](https://dreemtimeacademy.com.au/) identifies him as the person heading the academy. The [creator's Cosmic Conversations podcast page](https://cosmicconversations.buzzsprout.com/) identifies him as its host.

The channel's own description advertises interviews, numerology programming and **Andromedan Council channelings**. This is channel-level content attribution. It does not, by itself, establish that Hayden performs every channeling, that an interview guest's source belongs to him, or that an entity speaks in a particular video. Registry role `interview_host` records the directly established host function; per-item `entity` and `channeling` fields remain empty. The description's named council is a discovery lead for item-level performer review, not a new accepted relationship in the separate 115-record research table.

Self-described spiritual practices and claimed entities are attribution evidence, not independent confirmation of beings or healing effects.

## Intake result

The source snapshot listed **1,101 unique items**: **338 Videos, 117 recorded-stream listings and 646 Shorts**. No currently live/upcoming/post-live item was excluded from this particular snapshot. There is no duration cutoff. The 646 Shorts lack duration in the flat listing; their runtime remains unknown. Other listed durations total approximately **332.6 hours**, not the complete channel runtime.

The first two priority tiers retain the project's established **Videos-tab** order. Shorts and recorded streams are included in the full/final catalog, not mixed into the Videos-tab rank sequence.

| Queue | Before | After | Added |
| --- | ---: | ---: | ---: |
| Newest 20, original and enriched copies | 1,340 | 1,360 | 20 |
| Newest 50, original and enriched copies | 3,270 | 3,320 | 50 |
| Full merged catalog | 65,345 | 66,446 | 1,101 |
| Remaining after newest 50 | 62,075 | 63,126 | 1,051 |

There are now **71 tracked priority channels**, preserving the preceding 70. The full queue has **109 source directories**, including legacy linked-host material; that is not a claim that 109 complete channels were freshly listed. The public target registry now has **110 profiles**, after this intake and the earlier requested Multidimensional Soul host.

The three registry additions use collection key `dreemtime-academy`:

- [Extra people registry](../sources/extra_targets.csv): Hayden Crawford / Dreemtime Academy, host role.
- [Extra channels registry](../sources/extra_channels.csv): canonical ID, handle and identity evidence.
- [Target inventory](../plan/targets.csv): listed tab counts and known duration.

[Intake helper](../pipeline/intake_channel.py) appends only IDs absent from each queue. Every prior queue row, its metadata and its position were compared against the saved before-image after publication. All five input queue copies retained their complete original prefix; their new bytes match the committed receipt hashes. Derived final-round groups and channel mappings were rebuilt. The original release asset `queue_youtube_all.csv` was not changed.

Private provenance is stored under `<private-root>/jobs/dreemtime_academy_intake.json`, including source hash, before/after hashes and the timestamped `jobs/queue_backups/dreemtime-academy_.../` directory. That directory contains before-images, staged after-images and a committed receipt. Registry before-images and hashes are recorded separately in `jobs/dreemtime_registry_provenance.json`. Previous metadata objects remain preserved in queue sidecars as well as backups.

Publication held the same kernel lock used by Drive ingestion. Staging accounts for backups, replacement growth and temporary files against the **17 GB private cap**, with **3 GB disk-free headroom**. Six focused offline checks passed: identity mismatch, source rank/live exclusion, preservation under duplicate IDs, refusal of concurrent input changes, rollback after write failure, and the storage cap. The committed queue hashes and preservation of all prior rows were also checked against the real private backups.

This was catalog intake only. It neither launched workers nor changed source cooldown deadlines. The single YouTube listing invocation used three-second request spacing and zero retries; it finished successfully in approximately 104 seconds. Future additions still require source identity checks and the same protected append workflow.

## Time windows and candidate evidence

The requested calendar window is **November 16–22, 2026**. The additional backweek is **November 10–16, 2026**; these windows overlap on November 16 and must not be counted as independent periods. At this session's local date, most of November 17–22 is still future.

Dates below marked approximate come from flat listings and relative-age conversion. They are not authoritative publication timestamps or event dates. Sam's entries were read from the already saved newest-20/full snapshots; no new Sam source request or media extraction was made.

| Creator / item | Listing date | Metadata available | Research treatment |
| --- | --- | --- | --- |
| Dreemtime: [EliqxbbQoRw](https://www.youtube.com/watch?v=EliqxbbQoRw) | Approx. Nov 16 | Title: “Jellyfish UFOs, Power Outages & The Andromedan Message: Should We Prepare?” | Strongest candidate for the user's recent-event reference. It identifies topic labels, but no specific outage, sighting location or event date was established. |
| Sam: [bMWOuu_Zd-s](https://www.youtube.com/watch?v=bMWOuu_Zd-s) | Approx. Nov 16 | Title describes a discussion and names Galactic Federation; it does not name a concrete event. | Candidate counterpart because of recency and the user's stated connection. The shared-event assertion remains unverified. |
| Dreemtime: [sk-TrtUPKCE](https://www.youtube.com/watch?v=sk-TrtUPKCE) | Approx. Nov 14 | Title describes a supposed end-of-world date and an Andromedan response. | Backweek alternative; no exact event/date claim established from the metadata. |
| Sam: [Vgkbq38gJLs](https://www.youtube.com/watch?v=Vgkbq38gJLs) | Approx. Nov 10 | Title uses broad imminent-change language and names Pleiadians. | Backweek alternative, with insufficient metadata to identify the event or match Dreemtime. |
| Dreemtime: [2CAOL3sBy00](https://www.youtube.com/watch?v=2CAOL3sBy00) | Approx. Nov 11 | Title concerns AI and human evolution. The creator's podcast lists a Nov 11 conversation with Fulcrum Djedi about AI, Neuralink and related themes. | Alternative recent topic. The podcast date is explicit, but the exact YouTube-to-podcast work link was not independently established in this pass. |
| Dreemtime: [8_5ha6dYJ3o](https://www.youtube.com/watch?v=8_5ha6dYJ3o) | Approx. Nov 10 | Title concerns Andromedan starseeds and death. | Within the backweek; not evidence of a shared outage/UFO event. |

The [creator's podcast listing](https://cosmicconversations.buzzsprout.com/) supplies the explicit November 11 episode date and guest. The [creator's blog index](https://www.dreemtime-academy.com/blog) returned content through October 28 in this retrieval; it did not supply a description for the November 16 candidate.

**Current candidate pair:** `EliqxbbQoRw` ↔ `bMWOuu_Zd-s`, status **user-reported connection / temporal candidate / event identity unresolved**. Candidate topics are jellyfish-shaped UFO reports and power-outage claims on Dreemtime's side. Sam's retained metadata does not confirm those referents. The second pair, `sk-TrtUPKCE` ↔ `Vgkbq38gJLs`, has weaker temporal-only support.

No pair is marked as two independent accounts of the same event. Similar channeling vocabulary, entity labels, proximity in upload dates or dramatic titles cannot establish that. Search results concerning outside news events were not substituted for either creator's missing description.

## Future comparison work

This is a future analysis work package, not an active transcription or interpretation job.

1. **Establish the event first.** Read creator-authored descriptions or existing authorized text for the candidate items. Record a concrete referent, place, time range and event aliases; retain `event_unresolved` until both items can be tied to the same referent. If a real-world incident is asserted, add an independent primary record for that incident before assessing factual accuracy.
2. **Separate people, sources and roles.** Identify Hayden, Sam and any guests as actual performers. Record each claimed entity label at the item/span level. Channel ownership and a title's entity label cannot substitute for performer evidence.
3. **Keep event time separate from publication time.** Preserve exact versus approximate publication dates, observation dates, claimed prediction dates and timezone. The overlapping November 16 windows are one observation, not two.
4. **Preserve source versions and families.** Retain `work_id`, `item_id`, `text_version_id` and `span_id` when text becomes available. Link clips, reposts, captions and later ASR to their originating recording so they cannot create false independent corroboration.
5. **Compare explicit claims, not titles.** Distinguish an asserted observation, interpretation, forecast, conditional statement, question and metaphor. Compare the specific event claims, dates and uncertainty only after the underlying source spans are reviewed.
6. **Track dependence and alternatives.** Note common news stories, shared guests, reposts and references to another creator. Similarity may arise from a common public source; it is not automatically independent agreement.
7. **Report uncertainty visibly.** Output candidate, confirmed-same-referent and unresolved pairs separately. A successful same-event match establishes what the creators discuss, not the truth of a claimed supernatural cause.

A minimal future comparison record should contain: pair ID; both item IDs; actual human speakers; claimed source labels and provenance; event ID or unresolved status; publication-date quality; event-date range; supporting source references/spans; statement type; work-family dependence; reviewer decision. This intake creates none of those as inferred transcript facts.

## Search and source audit

Four Exa searches requested **20 result slots**, returned **20 entries**, and produced **17 distinct result URLs**:

| Search angle | Requested | Returned | Result used |
| --- | ---: | ---: | --- |
| Dreemtime identity and official creator sources | 5 | 5 | Official sites and creator identity |
| Creator episodes in the two November windows | 5 | 5 | Official podcast and blog |
| Exact newest Dreemtime title / item | 5 | 5 | No additional accepted event-description source |
| Exact Sam item ID and title / description | 5 | 5 | No matching accepted creator description; unrelated results excluded |

Five Exa source-fetch URL attempts returned four primary pages: the current official site, earlier official site, creator podcast and creator blog. The handle page returned empty content through Exa; the separately authorized, single flat YouTube extraction supplied its direct identity and tab metadata. Thus there were **four successful Exa source pages plus one direct channel listing**, not 20 verified sources or 1,101 opened video pages.

Third-party mirrors, unrelated same-title material, roundup results and news speculation were excluded as relationship/event proof. No creator transcripts or captions were fetched for this task.
