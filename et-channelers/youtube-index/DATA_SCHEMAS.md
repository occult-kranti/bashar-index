# Compiled dataset schemas (all files UTF-8 JSON, written to /home/claude/etc_site/data/)

Shared rules: ids from CANONICAL_IDS.md; dates ISO "YYYY", "YYYY-MM" or "YYYY-MM-DD" with a `precision` field where relevant; every factual field that came from a source carries a URL in `sources` (array of {"url","title","accessed":"2026-10-23"}); unknown = null; nothing invented; claims phrased as claims ("claims to channel", "is described by X as"); quotes ≤30 words with url. Confidence: "high" | "medium" | "low".

## people.json — array of Person
{
  "id": "athina-krol",
  "name": "Athina Król",
  "aliases": ["Athina Bailey"],
  "role": "channeler" | "contactee" | "organisation" | "context" | "forum-member" | "interpreter",
  "tier": "deep" | "card",                 // deep = full profile page (the ~15 majors incl. Anka, Król, Ellison); card = directory card
  "et_focus": true,                         // false for non-ET context figures
  "entities": ["ashtar", "lyrans"],         // entity ids
  "species_tags": ["Pleiadian-connected", "Lyran", "Andromedan"],   // free text tags for filters
  "era": "pre-ra" | "ra-era-1981-1990" | "1990s" | "2000s" | "youtube-era-2012-2019" | "2020s",
  "start_year": 2016, "start_year_basis": "claimed: trance channeling publicly 'by twenty' (self-report)", "start_confidence": "low",
  "public_year": 2020, "public_year_basis": "first podcast episode 2020-08-02", "public_confidence": "high",
  "active": true, "end_year": null,
  "location": "Australia (Brisbane/Sydney; sources conflict)",
  "method": "trance channeling",
  "platforms": {
    "youtube": {"handle": "@AthinaKrol", "channel_id": "UCuXxdyss-NVCA3PQIAklk3g", "url": "...", "subscribers": 5410, "subscribers_text": "5.41K subscribers", "videos": 152, "observed": "2026-10-23"},
    "website": "https://www.athinakrol.com/", "podcast": {"name": "Spirit Channel with Athina Król", "url": "..."},
    "patreon": null, "instagram": null, "tiktok": null, "other": ["Insight Timer: https://insighttimer.com/athinakrol"]
  },
  "books": [{"title": "Soulfire", "year": 2025, "url": "..."}],
  "summary": "two-sentence neutral summary",
  "claims": ["..."],                        // 3–6 bullets, phrased as claims
  "quotes": [{"text": "...", "url": "...", "context": "..."}],
  "controversies": ["..."],                 // attributed, with URLs inline
  "predictions": [{"date_predicted": "2027", "what": "...", "status": "pending" | "failed" | "revised" | "fulfilled", "url": "..."}],
  "related_people": ["darryl-anka"],
  "communities": ["balg", "wizardforums", "reddit"],   // where discussed
  "confidence": "medium", "unverified": ["birth year", "exact rebrand date"],
  "profile": ["paragraph 1", "paragraph 2", "..."],   // deep tier only: 4–8 paragraphs of neutral prose with inline markdown links; card tier: []
  "sources": [{"url": "...", "title": "...", "accessed": "2026-10-23"}]
}

## entities.json — array of Entity
{ "id": "ashtar", "name": "Ashtar / Ashtar Command", "type": "individual/command", "et": true,
  "claimed_origin": "...", "claimed_density": "...", "description_claimed": "...",
  "first_appearance": {"year": 1952, "date": "1952-07-18", "by": "george-van-tassel", "url": "...", "confidence": "high"},
  "channelers": [{"person": "athina-krol", "from": 2026, "to": null, "note": "..."}],
  "distinguishing_claims": ["..."], "change_over_time": "paragraph", "sources": [...] }

## timeline.json — array of Event (target 250–400 events, 1848–2026, deduplicated)
{ "id": "1981-01-15-ra-first-session", "date": "1981-01-15", "precision": "day" | "month" | "year",
  "title": "First Ra session", "description": "one or two sentences", 
  "category": "ra-lineage" | "pre-ra" | "bashar" | "ashtar" | "pleiadian" | "galactic-federation" | "other-channel" | "species-first" | "prediction" | "criticism" | "context-non-et" | "youtube-era" | "platform",
  "people": ["carla-l-rueckert"], "entities": ["ra"], "url": "...", "confidence": "high", "focus": true }   // focus = true for the three focus figures' events and the Ra anchor

## criticism.json
{ "predictions": [{"date_predicted": "1996-12-17", "what": "...", "by": "sheldan-nidle", "entity": "galactic-federation", "outcome": "did not occur", "status": "failed", "url": "..."}],
  "explanations": [{"author": "...", "year": 1997, "position": "≤30 words", "url": "..."}],
  "journalism": [{"outlet": "...", "date": "...", "title": "...", "gist": "...", "url": "..."}],
  "commercial": [{"person": "darryl-anka", "item": "...", "price": "...", "date": "...", "url": "..."}],
  "harm": [{"case": "...", "year": 2021, "gist": "...", "url": "..."}],
  "how_to_read": ["paragraph", "..."] }

## communities.json
{ "reddit": {"status": "not retrieved — blocked; leads only", "threads": [], "leads": ["..."]},
  "wizardforums": {"threads": [{"date": "...", "board": "...", "title": "...", "url": "...", "gist": "...", "handles": []}], "tally": {"recommended": {}, "criticised": {}}, "quotes": []},
  "balg": {...same...},
  "framing": [{"position": "...", "who": "handle", "date": "...", "url": "..."}],
  "people_found": ["mulberry", "amur", ...] }

## youtube_index.json
{ "observed": "2026-10-23", "coverage": {"fully_indexed": 16, "metadata_only": 70, "no_youtube": n, "not_found": n},
  "channels": [ { "person": "athina-krol", "role": "channeler", "status": "ok" | "metadata-only" | "no_youtube" | "not_found",
                  "channel": {...as in youtube_index/SCHEMA.md...}, "secondary_channels": [...], "videos": [...], "summary": {...} } ] }
