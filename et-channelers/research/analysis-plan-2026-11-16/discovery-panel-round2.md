# Channeler and claimed-entity discovery: panel round 2

Research date: 2026-11-17 UTC, continuing the 2026-11-16 planning session. Research owner: discovery panel. Queue changes: none.

[Normalized relationship table](discovery-relationships.csv) contains **115 claim records for 28 human profiles**: 8 humans linked to existing collections and 20 proposed new profiles. There are 21 profiles with an attributable owned/shared-project channel link; 7 still lack adequate channel ownership evidence. Nineteen people have more than one sourced relationship after the parent-reviewed round-3 additions. These are statements about practitioners' own claims, not confirmation of supernatural entities, historic assertions, credentials, or healing effects.

Akanksshaa is an additional reviewed host profile, kept outside the relationship table because a named personal entity claim has not been established. The parent registered the supplied Multidimensional Soul channel separately under `multidimensional-soul` and reported 1,417 listed items. Guest claims must attach to an identified guest and episode; those items do not imply 1,417 channelings or host-entity relationships.

## What changed from round 1

The exact spelling **Quantamo** is supported by [Pia Orleane's own event page](https://www.piaorleane.com/spring-2025-cosmic-guidance) and the [Laarkmaa project's corresponding recording page](https://www.laarkmaa.com/product-page/voices-from-the-light-cosmic-guidance). Both attribute the listed communications to Pia and distinguish the final joint Laarkmaa session with Cullen. The former unresolved round-1 name is therefore resolved as a claimed source of Pia's communications. It is not Q'uo, Quan Yin, or a generic quantum term.

Five unresolved ownership checks now have primary evidence:

| Profile | Owned channel evidence | Attribution boundary |
| --- | --- | --- |
| Amanda Ellis | Her [main site](https://www.amandaellis.co.uk/) links her [official shop](https://www.angeliccelestialcolours.co.uk/), which links [@AmandaEllis](https://www.youtube.com/@AmandaEllis). | Her broader list of figures she works with does not automatically prove she channels each figure. |
| Althea Lucrezia Avanzo | Her [canonical channel page](https://www.youtube.com/channel/UCKjxsD8Yj3hT3bKwswTPi6A) identifies Althea and links her own domain. | A self-description of working with a Pleiadian self and a Mantis being is not upgraded to a separately reviewed entity-channeling claim. |
| Dawn Katar | [Her official video page](https://www.openchannelresources.com/dawn-and-the-masters-youtube-videos) explicitly links [her channel](https://www.youtube.com/channel/UCzJx47nSplU0y6QM1k0TdGw). | Several recording descriptions are historical; current availability remains untested. |
| Judi Weaver | The own-channel button on [her biography](https://judiweaver.com/about-2/) links [this canonical channel](https://www.youtube.com/channel/UCzL4OaUQD9pEmNUUu8vvUWQ). | Its separate Portal to Ascension link is a host/platform link. |
| Solara An-Ra | The explicitly labeled own-channel link on [her site](https://www.solara.org.uk/) identifies [this canonical channel](https://www.youtube.com/channel/UC3wjMuxPWEXqeg1-uAgXuFg). | The other canonical ID belongs to testimonial author Mindy Mekemson, not Solara. |

Of round 1's original 18 new candidates, the requested host is now registered. The other 17 remain proposed profiles; 12 have ownership evidence and 5 remain unresolved. This round adds Mercedes Kirkel, Melanie Beckler, and Ellen Mahloy as proposed profiles, plus existing Kelly Kolodney for comparison. Ellen's evidence supports reported guidance, not a verified spoken-channeling corpus.

## Comparisons now supportable

| Comparison label | Explicit channeling attributions in this table | Qualification |
| --- | --- | --- |
| Archangel Michael | Daniel Scranton, Joan Walker, Saratoga Ocean, Dawn Katar, Anjie Hipple | Saratoga's [Telstar page](https://saratogaocean.com/telstar/) explicitly names Michael among six channeled members. Melanie Beckler separately reports contact; that edge is not counted as reviewed Michael channeling. |
| Archangel Raphael | Kelly Kolodney | [Ellen Mahloy](https://www.reikiwithangels.com/about-reiki-with-angels) reports Raphael-derived guidance. A second independently established spoken-channeling corpus is still missing. |
| Jesus / Yeshua | Daniel Scranton, Lea Chapin, Gina Lake, Mercedes Kirkel | [Lea's biography](https://leachapin.com/about-lea/) and [Mercedes's introduction](https://mercedeskirkel.com/) explicitly support the local Jesus/Yeshua comparison alias. This is a label mapping, not evidence that speakers share an external source. |
| Mary Magdalene | Lea Chapin, Merriam Joan Handy, Alexis Cartwright, Pia Orleane, Mercedes Kirkel | Alexis has series-level attribution; Pia has an event source list. Neither supplies a reviewed per-episode speaker assignment yet. |
| Gods and spiritual teachers | Isis, Thoth, Quan Yin, Buddha, Kuthumi, Osho and others | Dawn's [Kuthumi event](https://www.dawnkatar.com/june-5-2018-kuthumi-restoring-the-role-of-divine-masculine.html) and [Osho/Saint Germain release page](https://www.dawnkatar.com/new-channeled-releases.html) are explicit. Alexis's [official series schedule](https://landingi.transferencehealing.com/godsandgoddesses) is an event-level source. |
| ET collectives and councils | Scranton's individually named councils; Lori's four represented collectives; Solara's councils; Lyssa's Sasha and Germane; Barbara's Pleiadians; Pia/Cullen's Laarkmaa | Generic civilizational labels remain scoped to each source. Xanadu is a spokesperson for Lori's collectives, not four demonstrated independent speaker tracks. |

After the round-3 predicate correction and 14 parent-requested source-backed additions, the 115 rows include 86 channeling claims, 21 series/event-level channeling claims, 4 code-channeling claims, 1 light-language claim, 1 reported-contact claim, 1 reported-guidance claim and 1 reported guide association. Rob Gauthier's Metatron row now preserves only the guide association supported by its cited page; Aridif and Treb have separate personal-channeling-session support. These categories must not be pooled as 115 verbal speakers or independently sampled entities. Riya's codes and Andréa's light-language attribution require their own analysis treatment.

## Record contract

- One row represents one **person–claimed source–claim type–supporting page** relationship. It does not represent a video, quotation span, or proof that an entity spoke in every item on a channel.
- `person_id` names the human. `collection_id` preserves the existing repository collection key where one exists. Pia and Cullen have separate human IDs with shared collection `laarkmaa`; Anjie Hipple has human ID `anjie-hipple` with collection `the-judah-channel`.
- `entity_concept_id` is a comparison label, not an ontological verdict. Generic councils, civilizational groups, common personal names and newly introduced sources are scoped to the claimant or named collective. `comparison_family` permits broader grouping without asserting identity.
- `claim_instance_id` identifies this sourced relationship record: a deterministic FNV-1a 64-bit identifier over person ID, entity concept, role, claim type and exact source URL. Display-name or paraphrase edits preserve it; a different evidence page produces a different relationship-record ID. This is not the analysis `claimed_entity_instance_id` (speaker/lineage identity) or `claim_mention_id` (an individual transcript claim). Map those separately using item-level speaker evidence; do not join them by display name or comparison family.
- `role` is relationship-specific: `channeler` or `contactee`. Host-only and teacher-only candidates stay in the unresolved table below rather than receiving fabricated entity rows.
- `profile_verified` means the named practitioner's self-presentation was found on a primary source. It does not verify identity documents, qualifications, supernatural claims, current activity, or language coverage.
- `channel_ownership_verified` separately records an explicit own-channel link or matching first-person channel/domain evidence. A channel name, guest appearance, embedded interview or unrelated link alone is insufficient.
- `source_section` gives a locatable page section; `evidence_paraphrase` contains original summaries. No additional quoted excerpts are copied from round 1. Necessary entity labels and identifiers retain source spelling.
- `source_review_state` separately records the parent's source acceptance. This agent creates rows as `agent_primary_source_reviewed_parent_pending`; the parent sets its own acceptance after independently opening the sources. `evidence_round` and `retrieved_at` distinguish rounds 1?3. Timestamps identify research sessions, not asserted page-update times.

## Profile inventory

| Human profile | Existing/new | Relationship rows | Channel ownership |
| --- | --- | ---: | --- |
| Amanda Ellis | new | 2 | [Verified source link](https://www.youtube.com/@AmandaEllis) |
| Daniel Scranton | existing | 14 | [Verified source link](https://www.youtube.com/channel/UCb6-5YT9N1EWA4c_yXBQE1w) |
| Joan Walker | new | 5 | Unresolved |
| Saratoga Ocean | new | 7 | Unresolved |
| Althea Lucrezia Avanzo | new | 1 | [Verified source link](https://www.youtube.com/channel/UCKjxsD8Yj3hT3bKwswTPi6A) |
| Rob Gauthier | existing | 3 | [Verified source link](https://www.youtube.com/channel/UC8JooeMCjTYIKhO7UXLbMtg) |
| Alexis Cartwright | new | 20 | Unresolved |
| Amma Ventelä | new | 2 | [Verified source link](https://www.youtube.com/@ammaventela) |
| Lea Chapin | new | 3 | [Verified source link](https://www.youtube.com/channel/UCZKJpkyjqvT5Y9ACDh-LBYg) |
| Merriam Joan Handy | new | 7 | Unresolved |
| Lori (My Wife Talks to Aliens) | new | 5 | [Verified source link](https://www.youtube.com/channel/UCiR-ufoxZgD78Z4iLO2rEuw) |
| Solara An-Ra | new | 5 | [Verified source link](https://www.youtube.com/channel/UC3wjMuxPWEXqeg1-uAgXuFg) |
| Lyssa Royal Holt | existing | 2 | [Verified source link](https://www.youtube.com/channel/UCeuLbnOjJBUfqqm2KEqkpLA) |
| Barbara Marciniak | existing | 1 | [Verified source link](https://www.youtube.com/channel/UCSffF5wKtHDCezvV5tUm68w) |
| Riya Loveguard | new | 4 | Unresolved |
| Dawn Katar | new | 7 | [Verified source link](https://www.youtube.com/channel/UCzJx47nSplU0y6QM1k0TdGw) |
| Anjie Hipple | existing | 2 | [Verified source link](https://www.youtube.com/channel/UCIEhmD3vyaZXWHfx3opQ-IA) |
| Gina Lake | new | 1 | [Verified source link](https://www.youtube.com/c/GinaLakeChannelingJesus) |
| Andréa Luizari | new | 1 | [Verified source link](https://www.youtube.com/channel/UCtgPv-Yylk3ynNzb5oBKVRA) |
| Alessa / AEISIS | new | 5 | [Verified source link](https://www.youtube.com/channel/UC0wUibB7NB3W8xNJ-qpUjgQ) |
| Bonnie Vent | new | 1 | [Verified source link](https://www.youtube.com/@connectionchannelingBonnieVent) |
| Judi Weaver | new | 1 | [Verified source link](https://www.youtube.com/channel/UCzL4OaUQD9pEmNUUu8vvUWQ) |
| Pia Orleane | existing | 9 | [Verified source link](https://www.youtube.com/channel/UCwB7FHwwaHYML6uFqulHMtg) |
| Cullen Baird Smith | existing | 1 | [Verified source link](https://www.youtube.com/channel/UCwB7FHwwaHYML6uFqulHMtg) |
| Kelly Kolodney | existing | 1 | [Verified source link](https://www.youtube.com/channel/UCEH8R46KVsdNtxH3OS_vGUA) |
| Mercedes Kirkel | new | 2 | Unresolved |
| Melanie Beckler | new | 2 | [Verified source link](https://www.youtube.com/c/askangels) |
| Ellen Mahloy | new | 1 | Unresolved |

Current-profile and channel counts are snapshot counts; they are not download instructions. The CSV intentionally preserves the evidence available for profiles whose YouTube ownership remains unresolved.

## Unverified candidates and unresolved attributions

| Candidate or attribution | Established evidence | What remains unresolved |
| --- | --- | --- |
| Akanksshaa / Multidimensional Soul | Parent verified supplied channel ID and @Akanksshaa; registered as interview host. | Named entities must be attributed to the actual guest or to an explicit personal channeling statement by Akanksshaa. No host-entity edge added. |
| Joan Walker | [Official biography](https://ascendingmasters.net/about/) names Kuthumi and four archangels. | Exact owned YouTube destination not found. John Walker is a teaching partner, not automatically a channel for her sources. |
| Saratoga Ocean | Own biography and Telstar page establish channeling attribution. | Exact owned channel URL not resolved; main-site HTML returned 403, and cached pages lacked an ownership link. |
| Alexis Cartwright | Official series identifies her own channelings and scheduled sources. | Owned YouTube channel not established; one embedded video is insufficient. Series-level attribution needs item-level review. |
| Merriam Joan Handy | Official event page and its own introduction attribute the channeling event to her. | Introduction uploader is Wise Woman On Tour, but exact owned channel URL was not recovered. |
| Riya Loveguard | Own site describes civilizationally attributed channeled codes. | Its YouTube link names Aeron Lazar. Shared ownership must be independently established before associating that channel with Riya. |
| Mercedes Kirkel | Own site explicitly identifies Mary Magdalene and Yeshua. | Embedded Mariam Agency TV interview belongs to a host platform; personal channel not verified. |
| Ellen Mahloy | Own account attributes guidance to Raphael. | Own channel and a spoken-channeling corpus remain unverified. Preserve contactee/guidance type. |
| Elemental Beings | [Official topic page](https://www.elementalbeings.co.uk/ascended-masters) lists courses described collectively as channeled with named gods and masters. | The page uses a collective author voice. Do not assign these claims to a guessed individual without the team's authorship and session evidence. |
| Amanda's other named spiritual associates | Own site says she works with them. | A relationship verb such as working with does not alone establish a channeling claim. |
| Althea's Pleiadian self and Mantis being; Alessa's past-life deity associations | Own biographies mention these connections. | Association and past-life narratives are not substituted for explicit channeling-source attribution. |
| Quantamo | Exact primary-source match to Pia is now found. | User referent confirmation remains separate from source matching; no link to Q'uo or Quan Yin is inferred. |

## Search and opening audit

Five targeted search angles were executed successfully. **55 result slots requested, 55 result entries returned, 54 distinct result URLs.** Search results alone did not verify a relationship.

| Search | Target angle | Requested | Returned |
| --- | --- | ---: | ---: |
| 1 | Official channeler websites for Amanda Ellis, Saratoga Ocean, Althea Lucrezia Avanzo and Joan Walker Ascending Masters that identify their own YouTube channels and the beings they personally channel | 15 | 15 |
| 2 | Kelly Kolodney Raphael official channeling website and other channelers who personally channel Archangel Raphael and Archangel Michael with named first person biography | 10 | 10 |
| 3 | Official websites of channelers who channel Jesus Yeshua and Mary Magdalene together, including Lea Chapin Gina Lake and Joan Walker | 10 | 10 |
| 4 | Alexis Cartwright Dawn Katar Merriam Joan Handy Amma Ventela official websites channeling Isis Thoth Kuthumi Saint Germain divine mother Sophia YouTube | 15 | 15 |
| 5 | "quantamo" spiritual channeling medium entity council | 5 | 5 |

There were **26 Exa source-fetch URL attempts, with content returned for 22**. Four canonical YouTube pages returned no content; the official sites' explicit links remain the ownership evidence. Two additional web-open fallbacks read Amanda's and Saratoga's own pages. There were 22 supplementary first-party HTML link inspections, 19 successful and 3 refused; these include revisits to inspect anchor labels and Dawn's official-site link to Open Channel Resources. Across those methods, **28 distinct source URLs were successfully opened** in round 2. This is separate from the 54 search-result URLs.

The source-opening fallbacks were needed because extracted text omitted hyperlink targets or anchor context. No authenticated browsing, source refusal bypass, source-media download or active queue modification was performed. Two fetched video pages returned transcript text; that text was not copied into these research artifacts.

## Parent's final review checklist

1. Reopen the exact relationship page and ownership page separately before changing `source_review_state`.
2. Verify that the named person is the claimant or performer; distinguish a guest, interviewer, teacher, event organizer and channel owner.
3. Preserve collective-member, spokesperson, event-series, contact and code/light-language qualifications.
4. Treat Raphael's second spoken-channeler comparison and the seven missing ownership links as gaps, not negative findings.
5. Register any newly accepted person/channel through the repository's canonical registry before acquisition. Keep private media inventories and transcripts outside this research directory.

## Parent-reviewed additions after the round-2 snapshot

The parent independently read all 30 primary relationship-source pages. At its request, the table now also includes Anjie Hipple's explicitly attributed Michael message, Moiyra in Pia's event listing, and Alexis Cartwright's remaining 12 scheduled figures (20 total). Moiyra retains an unspecified source category and an event-level sound-healing qualification; no mermaid identity or spoken performance is inferred. The search/opening audit above describes round 2 only and is unchanged by these no-new-search additions. See the [grouped person table](channeler-entity-table.md) for the current 115-record view.
