# Shared spec for video/session digests (all research agents use this)

## How to get a transcript-based digest for a YouTube video
Use WebFetch on:  https://youtubetotranscript.com/transcript?v=<VIDEO_ID>
(The shell has NO internet access — never use curl/pip for web. youtube.com watch pages often return 429; YouTube RSS feeds are blocked by robots.txt. Playlist pages return only counts.)

WebFetch runs a small model over the page and will NOT return a long transcript verbatim (it declines for length/copyright). So do NOT ask for the full transcript. Ask for a STRUCTURED DIGEST using exactly this prompt (fill VIDEO_ID):

---
This page holds the auto-transcript of a Bashar channeling video (Bashar is channeled by Darryl Anka). Produce a structured analytical digest as JSON with these keys:
"title": video title on the page;
"author": channel/uploader shown;
"approx_word_count": your estimate of the transcript length in words;
"session_date_or_event": any date, city, event or occasion mentioned (else null);
"format": one of "monologue+Q&A", "Q&A only", "monologue only", "interview with Darryl Anka", "clip";
"opening_summary": 120-200 word summary of the opening talk/monologue (or of the whole clip);
"qa_topics": array of up to 20 objects {"question": short paraphrase of what was asked, "answer_gist": 1-2 sentence paraphrase of Bashar's reply};
"topic_percentages": object mapping EACH of these fixed tag names to an integer percent of the session spent on it (must sum to ~100): "formula_excitement", "beliefs_emotions_fear", "parallel_realities_shifting", "physical_vs_higher_mind", "permission_slips_tools", "et_contact_disclosure_2027", "essassani_hybrids_other_civilizations", "earth_shift_timelines_ascension", "abundance_money_career", "relationships_family_sexuality", "health_body_healing_death", "time_simultaneity_reincarnation", "channeling_mechanics_darryl", "consciousness_oversoul_higherself", "synchronicity_dreams_meditation", "politics_society_economy_ai", "physics_energy_frequency_dimensions", "spirituality_god_love_service", "ancient_history_atlantis_orion_sirius", "misc_life_guidance";
"key_terms": array of 25-40 Bashar-specific terms/phrases actually used in the transcript (e.g. "permission slip", "highest excitement", "physical mind", "higher mind", "parallel reality", "definition", "hybrid children", "Contact Fulcrum"), each as {"term": string, "freq": "high"|"medium"|"low"};
"quotes": array of 5-8 short verbatim quotes, each at most 30 words, chosen because they are memorable or capture a teaching, each as {"quote": string, "context": <8 words};
"predictions_and_dates": array of any years/dates/predictions mentioned (e.g. 2027 contact, 2033, 2050) with one-line context;
"tools_or_exercises": array of named techniques, games, meditations or handouts referenced;
"named_entities": array of civilizations, beings, places, people mentioned (Yahyel, Sassani, Orion, Sirius, Anunnaki, Pleiadians, Darryl, etc.).
Output ONLY the JSON.
---

Save each digest with Write to: /home/claude/bashar/research/digests/<VIDEO_ID>.json
Also append one line per video to your own manifest file (path given in your task) with: video_id, title, channel, url, upload_date if known, duration if known, status (ok / no_transcript / error).

If the transcript page errors (400/429/blocked), record status and move on; do not retry more than once.
Work through videos ONE AT A TIME (WebFetch calls in sequence), and Write each digest immediately after receiving it.
Do not spawn sub-agents. Do not use curl. Never fabricate a digest — if the page had no transcript, say so in the manifest.
