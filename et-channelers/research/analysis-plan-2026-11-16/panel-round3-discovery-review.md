# Discovery and ontology review: panel round 3

Reviewed 2026-11-17 UTC. The initial critique covered all 101 relationship rows then present, their saved first-party evidence, and the [round-2 interpretation](discovery-panel-round2.md). The [current CSV](discovery-relationships.csv) contains 115 rows after the parent's source-backed additions described below. This is a separate critique pass by the discovery artifact's author; the parent's independently opened sources remain the acceptance authority. No new searches, source downloads, queue edits, or changes to parent review states were made.

**Verdict:** suitable as a qualified discovery register; the predicate issue below was corrected in the requested follow-up. It is not yet a verified speaker corpus. The table preserves the main host/guest boundaries, Pia/Cullen distinction, and contact-versus-channeling distinctions. No evidence supports calling its 115 relationships 115 independently verified entities or speakers.

## Prioritized findings

| Priority | Finding and affected record | Required fix or acceptance condition |
| --- | --- | --- |
| P1, corrected | **Rob Gauthier–Metatron initially overstated the cited predicate.** Superseded record `claim-acefee5de16a91af` used `claims_channeling`; the [cited homepage](https://www.etwhisperer.com/) identifies Metatron as a principal guide and course subject. Its personal channeling-session description names Aridif and Treb specifically, but not Metatron. | Resolved as `reports_guide_association`, role `contactee`, under new record ID `claim-753d18f77e0045a0`. Direct Metatron-channeling attribution would still need additional evidence. Do not add Raphael, Michael or Uriel from the course topic list. Aridif and Treb have additional session-context support on the same page and should not be blanket-downgraded. |
| P1 | **General channeling attribution is not spoken-performance evidence.** Althea–Metatron (`claim-f7c892f33dc2d3db`) is a passage attributed on her site; Riya's four rows concern codes; Andréa's row concerns light language. None establishes a reviewed conventional-language audio segment. | Before selecting a speech corpus, record per-item modality, language, actual performer and evidence span. Keep written attribution, code/light-language, series-level and contact/guidance relationships distinct. The 86 generic channeling rows are not a ready-made speech filter. |
| P1 | **Relationship count is not an independence count.** Pia and Cullen have two human rows for one explicitly joint Laarkmaa practice. Lori's five rows comprise Xanadu plus four represented collectives. Saratoga's seven rows comprise Telstar plus its six named members. Solara likewise has an umbrella group plus member collectives. | Model the joint practice, group membership and spokesperson relationships before statistical sampling. Do not treat these rows as independent speakers, independent traditions or independent observations. Use work/recording families and shared lineage when splitting comparisons. |
| P2, fixed | **Solara's four member groups were all categorized as councils.** The [source](https://www.solara.org.uk/) describes Pleiadian, Arcturian, Lyran and Sirian star collectives participating in an umbrella council structure. | Changed only those four `entity_category` values to `et_collective`. The umbrella remains `et_council`. IDs and parent review states are preserved; an identifier containing “councils” must not override the explicit category field. |
| P2 | **Twenty-one ownership-checked profiles do not mean 21 distinct channels.** Pia and Cullen share one channel. Current rows contain 20 distinct channel URL strings: 15 canonical-ID URLs and 5 handle/custom-URL destinations. | Report profile ownership and distinct canonical-channel counts separately. Resolve the five aliases to canonical IDs before registry insertion/deduplication. The alias destinations belong to Amanda Ellis, Amma Ventelä, Bonnie Vent, Gina Lake and Melanie Beckler. |
| P2 | **Series-level evidence can be mistaken for a direct performance.** Alexis's 20 rows derive from a [series description and scheduled beings](https://landingi.transferencehealing.com/godsandgoddesses); Merriam and Pia also have event-level source lists. | Preserve Alexis's `claims_series_channeling` type. Require a particular session or item and speaker evidence before asserting that a named source appears in a recording. A course about a figure and channeling attributed to that figure are different predicates. |
| P2 | **Review booleans are easy to overread.** `profile_verified` concerns self-presentation; `channel_ownership_verified` concerns an explicit channel link. Neither confirms credentials, external source identity, current availability or transcript attribution. | Display full evidence states. Keep the parent's source acceptance separate from channel ownership and item-level speaker acceptance. Do not label the graph simply “verified entities.” |

The first finding is a precision issue in this discovery table, not a claim that Rob does not channel Metatron. The available cited passage supports a narrower assertion. The parent may close it with a more direct official source.

Amanda's Metatron row also uses contextual evidence: her own site identifies her main guide, describes hearing that guide and says her channel presents messages from her guides. Accept it as self-reported guide/message attribution; a direct item-level Metatron performance still needs review. Her list of other figures she works with was correctly excluded.

## Michael and Raphael: what is independent?

| Question | Current evidence | Decision |
| --- | --- | --- |
| Are there two distinct people independently claiming Michael channeling on their own sites? | Daniel Scranton, Joan Walker, Saratoga Ocean, Dawn Katar and Anjie Hipple have separate first-party source pages after the parent-requested addition. Saratoga explicitly includes Michael in her six-member Telstar group; Dawn lists a source-named channeling recording. | **Yes, as a discovery comparison of attributed claims.** These are five distinct human profiles and five first-party domains, not five corroborations that an external being exists. |
| Are two independently reviewed Michael speech samples ready for comparison? | This discovery pass reviewed source pages and ownership links, not actual audio segments or speaker spans. | **Not yet.** Choose and verify at least two recordings, preserve differing collective/session contexts, and avoid shared interview/repost families. |
| Are there two distinct confirmed Raphael channelers here? | Kelly Kolodney's [official page](https://theangelraphael.com/) explicitly identifies her channeling. Ellen Mahloy's [own account](https://www.reikiwithangels.com/about-reiki-with-angels) describes receiving guidance. | **No.** Ellen is correctly `contactee` / `reports_guidance_from`; she cannot supply a second spoken-channeler count. |
| Can Rob's archangel course fill the Raphael gap? | The course lists Raphael among figures discussed and invited into questions. The cited homepage does not explicitly identify a Raphael-channeling performance by Rob. | **No automatic promotion.** A direct first-party performance attribution is required. |
| Does shared Michael/Raphael naming establish the same claimed source instance? | Names identify a comparison concept. Speakers may present different traditions, roles or group contexts. | **No.** Keep person-specific claimed-source instances and a separate comparison-label graph. |

## Identity and equivalence checks

- **Akanksshaa stays a host until a personal named-source attribution is established.** Multidimensional Soul guests must be linked to the actual interview performer and episode. The registered channel does not inherit guest entities.
- **Pia and Cullen remain separate humans with a shared collection.** The [joint-practice description](https://www.piaorleane.com/) supports Laarkmaa through them together. The [Voices from the Light event](https://www.piaorleane.com/spring-2025-cosmic-guidance) attributes Quantamo and other listed sources to Pia; the final joint session is specifically distinguished. Cullen must not inherit Pia's other relationships.
- **Quantamo is an exact source match, not a fuzzy merge.** Its source-specific ID remains separate from Quan Yin, Q'uo, other Arcturians and generic quantum language.
- **Jesus/Yeshua is a comparison alias with explicit support in Lea's and Mercedes's descriptions.** Preserve each source's actual label and person-specific claimed-source instance. Alexis's Cosmic Christ remains separate; no historical or theological identity conclusion is implied.
- **Civilization labels are not individual speakers.** Sasha is a named claimed being; Barbara's Pleiadians are a collective; Scranton's Pleiadian High Council is a named council; Alessa names broad cosmic races; Riya names attributed codes. Their shared family label enables a broad comparison without making them one source instance.
- **Generic Council of Light labels remain source-scoped.** Lori's and Melanie's labels are not automatically the same council.
- **Common personal names remain scoped.** Telstar's Adam and John are not equated with historical figures or with Joan's partner John Walker.
- **Human identity is only as specific as the source.** Lori's surname and Alessa/AEISIS's legal identity are not supplied. The stable discovery IDs identify the sourced public persona, not a verified legal identity.
- **Owner/guest links already excluded are correct:** Solara's testimonial-author channel, Judi's Portal to Ascension link, Riya's Aeron Lazar link, Mercedes's Mariam Agency interview, and Lyssa's separately linked Ronald Holt channel.

## Ownership still unresolved

| Profile | Missing evidence | Acceptable closure |
| --- | --- | --- |
| Joan Walker | Exact own-channel destination | Explicit own-site/channel cross-link, or equivalent first-person channel identity evidence |
| Saratoga Ocean | Exact own-channel destination | First-party link to the creator's channel; an inferred same-name search result is insufficient |
| Alexis Cartwright | Personal/project channel ownership | Official site identifying its own channel, not an isolated embedded event video |
| Merriam Joan Handy | Canonical destination for Wise Woman On Tour | Official page linking the channel or channel self-description linking the official project |
| Riya Loveguard | Relationship to linked Aeron Lazar channel | Explicit shared-project ownership evidence; otherwise preserve it as another person's channel |
| Mercedes Kirkel | Own channel distinct from interview hosts | Own-site or first-person channel evidence, not an embedded Mariam Agency appearance |
| Ellen Mahloy | Any owned channel and a relevant speech corpus | Separate ownership proof and explicit item-level channeling evidence; guidance alone remains guidance |

A missing owned channel does not invalidate the attributed personal claim or prevent later use of an authorized, correctly attributed guest appearance. It prevents automatically treating a same-name channel as that person's archive.

## Acceptance criteria before analysis or acquisition

1. Parent source review must verify the exact relationship predicate, human claimant and page section. If a predicate changes, recompute the relationship-record ID under the documented hashing contract; do not silently reuse the old ID for a different claim type.
2. Ownership acceptance must establish a canonical channel ID independently of the relationship claim. Deduplicate by canonical ID and preserve joint/shared-project ownership.
3. Item acceptance must identify the actual human performer, claimed source label, modality, language and supporting item/span. Leave uncertain assignments unclassified.
4. Comparison eligibility must require at least two separately attributed human performances for the chosen source concept. Contact, guidance, light-language codes and shared joint sessions do not silently satisfy that requirement.
5. Create distinct mappings for `claim_instance_id` (this sourced relationship record), `claimed_entity_instance_id` (person/lineage-specific claimed source), `claim_mention_id` (a specific assertion), and the recording/work family. Never join all four by a display name.
6. Preserve group, member, spokesperson and joint-practice relations so umbrella and member rows cannot double-count a sample.
7. Show eligible, provisional and excluded counts with denominators. Maintain the seven ownership gaps and missing second Raphael speech corpus as explicit limitations.

The initial critique changed only four Solara categories. In the requested follow-up, Rob's Metatron predicate and relationship ID were corrected and 14 explicitly supported relationships were added, bringing the current table to 115 rows across the same 28 humans. No parent review states, channel URLs or active acquisition queues were changed by this agent. The opening 101-row scope describes the original review snapshot; the [grouped table](channeler-entity-table.md) presents the current batch.
