# YouTube index — output schema (one JSON file per agent group)

Write a JSON array. One object per person/channel:

{
  "person": "Athina Król",                       // exactly the person name used in the research notes
  "role": "channeler" | "contactee" | "context" | "clip-channel" | "organisation",
  "status": "ok" | "no_youtube" | "not_found" | "credits_exhausted" | "skipped",
  "channel": {
    "title": "Athina Król",
    "handle": "@AthinaKrol",
    "channel_id": "UCuXxdyss-NVCA3PQIAklk3g",
    "url": "https://www.youtube.com/@AthinaKrol",
    "subscriber_count_text": "5.41K subscribers",
    "video_count_text": "152 videos",
    "description_short": "first ~200 chars of the channel description",
    "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC...",
    "observed_at": "2026-10-23",
    "source": "youtube-com/channel_videos" | "firecrawl_scrape channel page" | "research notes"
  },
  "secondary_channels": [ {"title": "...", "url": "...", "note": "clip/re-upload channel, subs if known"} ],
  "videos": [
    {
      "video_id": "MDdyY1WYmHY",
      "title": "How to know your SOUL PURPOSE: Channeling Ashtar About Why You Came to Earth",
      "url": "https://www.youtube.com/watch?v=MDdyY1WYmHY",
      "view_count_text": "4.2K views",
      "published_text": "3 weeks ago",            // relative, as displayed on 2026-10-23
      "published_date": null,                     // ISO date only if known from another source
      "length_text": "53:26",
      "is_channeling": true,                      // true if the title/description indicates a channeled session/transmission/message
      "entity": "Ashtar",                         // the entity named in the title, or null
      "note": ""                                  // optional
    }
  ],
  "summary": {
    "recent_videos_read": 30,
    "channeling_videos_in_recent": 12,
    "entities_seen": ["Ashtar", "Andromedan Angelic Collective", "Lyrans"],
    "top_channeling_video_ids": ["MDdyY1WYmHY", "SZQpsemRYYc"],   // by view count, up to 8
    "earliest_known_video": {"video_id": "...", "title": "...", "date": "2019-05-25", "url": "...", "source": "research notes"}  // optional, if the notes give one
  },
  "sources": ["https://..."]
}

Rules: keep every video the provider returned (up to 30) — do not trim; classify each one. Use null where unknown. Do not invent counts or dates. Report relative dates verbatim.
