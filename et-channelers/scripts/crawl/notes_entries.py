"""Generate per-channel JSON entries for channels that could not be fetched (Firecrawl credits exhausted),
using only what the research notes record."""
import json, os, sys

out_dir = sys.argv[1]
OBS = "2026-10-23"


def ch(title=None, handle=None, channel_id=None, url=None, subs=None, vids=None, desc=None, note=None, source="research notes"):
    rss = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}" if channel_id else None
    if url is None:
        if handle:
            url = f"https://www.youtube.com/{handle}"
        elif channel_id:
            url = f"https://www.youtube.com/channel/{channel_id}"
    d = {
        "title": title, "handle": handle, "channel_id": channel_id, "url": url,
        "subscriber_count_text": subs, "video_count_text": vids, "description_short": desc,
        "rss_url": rss, "observed_at": OBS, "source": source,
    }
    if note:
        d["note"] = note
    return d


def vid(video_id, title, is_ch, entity, note, views=None, published=None, date=None, length=None):
    return {
        "video_id": video_id, "title": title, "url": f"https://www.youtube.com/watch?v={video_id}",
        "view_count_text": views, "published_text": published, "published_date": date, "length_text": length,
        "is_channeling": is_ch, "entity": entity, "note": note,
    }


def entry(out, person, role, status, channel, videos=None, secondary=None, earliest=None, sources=None, top=None):
    videos = videos or []
    ents = []
    for v in videos:
        if v["entity"] and v["entity"] not in ents:
            ents.append(v["entity"])
    e = {
        "person": person, "role": role, "status": status, "channel": channel,
        "secondary_channels": secondary or [],
        "videos": videos,
        "summary": {
            "recent_videos_read": len(videos),
            "channeling_videos_in_recent": sum(1 for v in videos if v["is_channeling"]),
            "entities_seen": ents,
            "top_channeling_video_ids": top if top is not None else [v["video_id"] for v in videos if v["is_channeling"]][:8],
        },
        "sources": sources or [],
    }
    if earliest:
        e["summary"]["earliest_known_video"] = earliest
    with open(os.path.join(out_dir, out), "w", encoding="utf-8") as f:
        json.dump(e, f, ensure_ascii=False, indent=1)
    print("wrote", out, status)


CE = "credits_exhausted"
CE_NOTE = "Firecrawl credits ran out before this channel could be fetched; "

# 01 Darryl Anka / Bashar
entry("01_anka.json", "Darryl Anka", "channeler", CE,
      ch(title="Bashar Channeled by Darryl Anka", handle="@BasharChanneledbyDarrylAnka", channel_id="UCiDZy_rfSodwFaVL_imGWgQ",
         subs="229,000 subscribers", vids="322 videos",
         desc="Official Bashar Communications channel: 'Highlights' excerpts and Shorts from Bashar sessions channeled by Darryl Anka; full sessions sold on BasharTV (per research notes).",
         note=CE_NOTE + "handle/ID from bashar.org links (corpus official_channels.md); 229,000 subs / 9,676,276 views / 322 videos from us.youtubers.me stats page (undated, seen 2026-10-23); thoughtleaders.io shows 258K subs in FAQ but 'nearing 190,000' in description text; first upload 2017-06-19."),
      videos=[
          vid("fZmY4xS_qXE", "Official highlights clip, January 2026 (title not recorded): 'Welcome to the first transmission of your new year of 2026, the year of disclosure.'", True, "Bashar",
              "from research notes via youtubetotranscript.com; metadata not available", date=None),
          vid("T5QtncJq1Jc", "Official highlights clip, 2025 (title not recorded): open contact 'imminent within two years'; hybrids and Pleiadians to be introduced first", True, "Bashar",
              "from research notes via youtubetotranscript.com; metadata not available"),
      ],
      secondary=[
          {"title": "Bashar Channeled by Darryl Anka 2025", "url": "https://www.youtube.com/@bashardarrylanka2025", "note": "look-alike/clip channel; 30 subscribers, 17 uploads, created 2024-01-16, no longer tracked (Social Blade, data to 2026-07-28)"},
          {"title": "Divine Light Vibes", "url": None, "note": "third-party Bashar clip channel named in corpus official_channels.md; URL/subs not retrieved (credits exhausted)"},
          {"title": "Path of Knowledge", "url": None, "note": "third-party Bashar clip channel named in corpus official_channels.md; URL/subs not retrieved (credits exhausted)"},
          {"title": "Divine Insights", "url": None, "note": "re-upload/clip channel named in task brief; not verified (credits exhausted)"},
          {"title": "Bashar Spiritual Insights", "url": None, "note": "re-upload/clip channel named in task brief; not verified (credits exhausted)"},
          {"title": "Mammoth Awakening", "url": None, "note": "re-upload/clip channel named in task brief; not verified (credits exhausted)"},
      ],
      earliest={"video_id": None, "title": "Finding your highest excitement (first Bashar video on YouTube per Baroni 2012; not on the official channel, which began uploading 2017-06-19)", "date": "2006-09", "url": None, "source": "research notes (https://www.cesnur.org/2012/el-baroni.htm)"},
      sources=["https://www.bashar.org/", "https://us.youtubers.me/bashar-channeled-by-darryl-anka/youtuber-stats", "https://app.thoughtleaders.io/youtube/bashar-channeled-by-darryl-anka", "https://socialblade.com/youtube/handle/bashardarrylanka2025", "https://youtubetotranscript.com/transcript?v=fZmY4xS_qXE", "https://youtubetotranscript.com/transcript?v=T5QtncJq1Jc"])

# 02 Athina Krol
entry("02_krol.json", "Athina Król", "channeler", CE,
      ch(title="Athina Król", handle="@AthinaKrol", channel_id="UCuXxdyss-NVCA3PQIAklk3g", subs="5.41K subscribers", vids="152 videos",
         desc="Multidimensional trance channel (Ashtar, Goddess Isis, Galactic Councils, Atlantean Council of Light); Australia; channel joined 2007-06-10; 116,294 views (About tab, 2026-10-23).",
         note="Channel metadata copied from research notes (earlier youtube-com provider call + About-tab scrape, 2026-10-23); the 30-video list could not be re-fetched because Firecrawl credits ran out. Videos below are the ones the notes record with IDs."),
      videos=[
          vid("MDdyY1WYmHY", "How to know your SOUL PURPOSE: Channeling Ashtar About Why You Came to Earth", True, "Ashtar", "metadata as recorded in SCHEMA.md example / notes (podcast release 2026-09-30)", views="4.2K views", published="3 weeks ago", length="53:26"),
          vid("8pG8QV-18xQ", "Ashtar Live: The Return of the Sovereign Human: Breaking Free from Energetic Interference", True, "Ashtar", "live trance channelling; published 2026-09-02T12:43:42Z per earlier video_details call", date="2026-09-02"),
          vid("mf80ocecqnU", "Pleiadian Light Codes", True, "Pleiadians", "title as recorded in notes (~2026-10-17); channeled light-code transmission", date=None),
          vid("EhoFej0S6QY", "This is What 'ALWAYS' Happens Before Reality Splits! The Next 3 Years Will Reveal UNTHINKABLE…", False, None, "Aug 2026 teaching/prediction video; channeling not indicated in title"),
      ],
      earliest={"video_id": "8pG8QV-18xQ", "title": "Ashtar Live: The Return of the Sovereign Human (first Ashtar-branded public content found; channel's older uploads not enumerated)", "date": "2026-09-02", "url": "https://www.youtube.com/watch?v=8pG8QV-18xQ", "source": "research notes"},
      sources=["https://www.youtube.com/@AthinaKr%C3%B3l/about", "https://www.youtube.com/@AthinaKrol", "https://athinakrol.podbean.com/", "https://www.youtube.com/watch?v=8pG8QV-18xQ"])

# 05 Barbara Marciniak
entry("05_marciniak.json", "Barbara Marciniak", "channeler", CE,
      ch(note=CE_NOTE + "research notes list pleiadians.com (books, Pleiadian Times newsletter, workshop recordings, Sellfy store) and no YouTube channel; likely no official channel, unverified."),
      sources=["https://www.pleiadians.com/"])

# 06 Barbara Hand Clow
entry("06_clow.json", "Barbara Hand Clow", "channeler", CE,
      ch(note=CE_NOTE + "research notes record a Gaia TV profile (https://www.gaia.com/person/barbara-hand-clow) and publisher pages; no YouTube channel recorded."),
      sources=["https://www.gaia.com/person/barbara-hand-clow", "https://www.innertraditions.com/books/the-pleiadian-agenda"])

# 07 Lee Carroll / Kryon
entry("07_carroll.json", "Lee Carroll", "channeler", CE,
      ch(note=CE_NOTE + "research notes record kryon.com (free transcription index of 224 channellings 2003-2022, livestreams 2020-2022) but no YouTube handle; an official 'Kryon' channel was to be located by search."),
      sources=["https://www.kryon.com/k_25.html", "https://en.wikipedia.org/wiki/Lee_Carroll"])

# 08 Sheldan Nidle / PAO
entry("08_nidle.json", "Sheldan Nidle", "channeler", CE,
      ch(note=CE_NOTE + "research notes record paoweb.com (weekly updates, Galactic Activation Webinars, DVD catalog; monthly webinars continue after Nidle's death on 2025-08-26 under Colleen Marshall and Miles Simons) but no YouTube handle."),
      sources=["https://www.paoweb.com/", "https://www.paoweb.com/paointro.htm", "https://en.wikipedia.org/wiki/Ground_Crew_Project"])

# 10 Suzanne Ward
entry("10_ward.json", "Suzanne Ward", "channeler", CE,
      ch(note=CE_NOTE + "matthewbooks.com lists a YouTube channel among its platforms (per research notes) but the handle/ID was not recorded; monthly Matthew messages are text-first."),
      sources=["https://www.matthewbooks.com/", "https://www.matthewbooks.com/matthews-messages/"])

# 11 Mike Quinsey
entry("11_quinsey.json", "Mike Quinsey", "channeler", CE,
      ch(note=CE_NOTE + "research notes record treeofthegoldenlight.com, galacticchannelings.com syndication and BBS Radio; no YouTube channel recorded; whether he is still living/when messages ceased is unverified."),
      sources=["https://galacticchannelings.com/english/interview-mike.html", "https://goldenageofgaia.com/2011/07/14/arraiel-biography-of-mike-quinsey/"])

# 13 Patricia Cori
entry("13_cori.json", "Patricia Cori", "channeler", CE,
      ch(note=CE_NOTE + "research notes record patriciacori.com, Inner Traditions author page, Coast to Coast AM/CNN appearances and a Project Camelot interview (2018-01-05); no YouTube channel recorded."),
      sources=["https://www.innertraditions.com/author/patricia-cori", "https://www.patriciacori.com/wp-content/uploads/2018/05/pcoribio2018.pdf"])

# 14 Tom Kenyon
entry("14_kenyon.json", "Tom Kenyon", "channeler", CE,
      ch(note=CE_NOTE + "research notes record tomkenyon.com (store, Hathor Planetary Messages) and workshops; no YouTube channel recorded."),
      sources=["https://tomkenyon.com/who-are-the-hathors", "https://tomkenyon.com/store/hathor-material/"])

# 15 Laura Knight-Jadczyk
entry("15_knight_jadczyk.json", "Laura Knight-Jadczyk", "channeler", CE,
      ch(note=CE_NOTE + "research notes record cassiopaea.org, the Cassiopaea Forum session-transcript board, cassiopaea.substack.com and SOTT; no YouTube channel recorded (text/board-based 'superluminal communication')."),
      sources=["https://cassiopaea.org/", "https://cassiopaea.substack.com/about"])

# 16 Alex Collier
entry("16_collier.json", "Alex Collier", "contactee", CE,
      ch(note=CE_NOTE + "research notes record alexcollier.org paid webinars (Webinar 266 on 2026-10-09; Q&A 85-87) and 1994-98 video/TV interviews; no YouTube handle recorded."),
      sources=["https://www.alexcollier.org/", "https://www.bibliotecapleyades.net/andromeda/esp_andromedacom_0.htm"])

# 18 Andrew Bayuk / Elan
entry("18_bayuk.json", "Andrew Bayuk", "channeler", CE,
      ch(title="Elan Interactions", handle="@ElanInteractions",
         desc="'Elan Interactions' (website created Sept 2020; YouTube @ElanInteractions; podcast) republishing Andrew Bayuk's early-1990s Elan (Essassani) channelings, per research notes.",
         note=CE_NOTE + "handle from research notes (anka_bashar.md, majors_1985_2015.md); subscriber/video counts not recorded. Bayuk 'stepped away from channeling completely' after the early 1990s, so uploads are archival."),
      earliest={"video_id": None, "title": "A rare video from 1992 (Elan session, per infinitelymystical.com)", "date": "1992", "url": "https://www.infinitelymystical.com/elan.html", "source": "research notes"},
      sources=["https://www.youtube.com/@ElanInteractions", "https://www.infinitelymystical.com/elan.html", "https://iasos.com/metaphys/elan/"])

# 21 Jamye Price
entry("21_price.json", "Jamye Price", "channeler", CE,
      ch(title="Jamye Price", handle="@JamyePrice", subs="31.2K subscribers", vids="484 videos",
         desc="Monthly 'Ascension Energies and Light Language' videos (4-7K views each); channels Areon, the Lyran Council of Time (per research notes).",
         note=CE_NOTE + "counts from research notes (YouTube channel page as displayed 2026-10-23); channel ID not recorded."),
      sources=["https://www.youtube.com/@JamyePrice", "https://jamyeprice.com/about-jamye-price/"])

# 22 L/L Research
entry("22_ll_research.json", "L/L Research", "organisation", CE,
      ch(note=CE_NOTE + "research notes record llresearch.org (1,700+ transcripts, Spiral Practice workshops, C/C Channeling Circle transcripts 2024) and lawofone.info; no YouTube handle recorded. Current channels: Jim McCarty, Gary L. Bean, Austin Bridges, Trisha Bean, 'Kathy B.' (Q'uo)."),
      sources=["https://www.llresearch.org/channeling", "https://www.llresearch.org/about/team", "https://www.lawofone.info/"])

# 23 Aaron Abke
entry("23_abke.json", "Aaron Abke", "context", CE,
      ch(title="Aaron Abke", handle="@aaronabke", channel_id="UC867Q451mPjjD52peYqpF4A", subs="374K subscribers", vids="1,195 videos",
         desc="Law of One / Ra Material interpreter and spiritual teacher (not a channel); channel created 2016-11-04; 42,752,720 views (vidIQ stats reported 2026-10-20/22).",
         note=CE_NOTE + "counts from vidIQ via research notes; handle @aaronabke from notes."),
      sources=["https://vidiq.com/youtube-stats/channel/UC867Q451mPjjD52peYqpF4A", "https://know-thyself-conference.heysummit.com/speakers/aaron-abke/"])

# 24 Billy Meier / FIGU
entry("24_meier_figu.json", "Billy Meier", "contactee", CE,
      ch(note=CE_NOTE + "research notes record FIGU (Semjase Silver Star Center, Hinterschmidrueti), Contact Report volumes, photographs/films and the 1987 film 'Contact'; no YouTube channel recorded for FIGU or Meier."),
      sources=["https://en.wikipedia.org/wiki/Billy_Meier"])

# 25 Aetherius Society
entry("25_aetherius_society.json", "Aetherius Society", "organisation", CE,
      ch(note=CE_NOTE + "research notes record books, Cosmic Voice magazine and the Operations (Starlight, Space Power, Sunbeam, Prayer Power); no YouTube channel recorded."),
      sources=["https://en.wikipedia.org/wiki/Aetherius_Society", "https://wrldrels.org/?p=3129"])

# 26 Robert Shapiro
entry("26_shapiro.json", "Robert Shapiro", "channeler", CE,
      ch(note=CE_NOTE + "research notes record explorerrace.com, benevolentmagic.com and Light Technology Publishing (Sedona); no YouTube channel recorded."),
      sources=["http://explorerrace.com/about.php", "https://books.org/books/explorer-race-vol-1/zoosh/9780929385389/"])

# 27 Nancy Lieder
entry("27_lieder.json", "Nancy Lieder", "channeler", CE,
      ch(note=CE_NOTE + "research notes record zetatalk.com, the ZetaTalk Newsletter and Ning Q&A chats (poleshift.ning.com); no YouTube channel recorded."),
      sources=["https://www.zetatalk.com/", "https://www.zetatalk.com/nancybio.htm"])

# 28 Judy Satori
entry("28_satori.json", "Judy Satori", "channeler", CE,
      ch(note=CE_NOTE + "research notes: 'YouTube presence exists (videos \"The Different Kinds of Light Language\") but channel handle/subscriber count not verified'; example video https://www.youtube.com/watch?v=bumKPM45uU0."),
      videos=[vid("bumKPM45uU0", "The Different Kinds of Light Language (title as recorded in notes)", False, None, "Light Language explainer; not a channeled session per title; metadata not available")],
      sources=["https://www.eomega.org/people/judy-satori", "https://www.youtube.com/watch?v=bumKPM45uU0"])

# 29 Steve Nobel
entry("29_nobel.json", "Steve Nobel", "channeler", CE,
      ch(title="Steve Nobel", handle="@SteveNobel", subs="198K subscribers", vids="721 videos",
         desc="Guided 'transmissions'/meditations attributed to Pleiadian, Sirian, Arcturian, Venusian star races and angelic sources (The Soul Matrix); recent videos 2K-13K views (per research notes).",
         note=CE_NOTE + "counts from research notes (channel page as displayed 2026-10-23); channel ID not recorded. Notes cite transmission titles 'Pleiadian Frequency Light Shields Transmission', 'Starseeds Receive Ascension Codes from Pleadian Star Races', 'The Venusian Starseed Transmission' (one of them is https://www.youtube.com/watch?v=57oYov3qUXc)."),
      sources=["https://www.youtube.com/@SteveNobel", "https://thesoulmatrix.com/"])

# 30 Elizabeth April
entry("30_april.json", "Elizabeth April", "channeler", CE,
      ch(title="Elizabeth April", handle="@ElizabethApril", subs="564K subscribers", vids="333 videos",
         desc="Remote viewer and conscious channel of 'the Galactic Federation' (Gaia: Heera, a Zeta Reticule being; Khan the Mantis); recent videos 143K-473K views, e.g. 'I Remote Viewed Barack & Michelle Obama…' 473K (per research notes).",
         note=CE_NOTE + "counts from research notes (channel page as displayed 2026-10-23); channel ID not recorded. Notes cite prediction videos https://www.youtube.com/watch?v=YtOm3XP0tTo and https://www.youtube.com/watch?v=50hlRmXD_iM (titles not recorded verbatim)."),
      sources=["https://www.youtube.com/@ElizabethApril", "https://elizabethapril.com/about-us/", "https://www.gaia.com/portal/ea"])

# 31 Sam the Illusionist
entry("31_sam_the_illusionist.json", "Sam the Illusionist", "channeler", CE,
      ch(title="SAM THE ILLUSIONIST", handle="@SAMTHEILLUSIONIST", subs="118K subscribers", vids="548 videos",
         desc="Channels 'Pleiadians', 'Galactic Federation', 'RA', Metatron, Archangel Michael, Buddha; urgency-style titles, e.g. '1 HOUR AGO: Pleiadians ISSUED Emergency Warning in Exclusive Broadcast' (90K views) (per research notes).",
         note=CE_NOTE + "counts from research notes (channel page as displayed 2026-10-23); channel ID not recorded. Notes cite 'How I Woke Up & Started Channeling & RA Tells My Past Lives' (98K views, 5 years ago) and 'The Rise Of The New Planet' (51K, 4 years ago) without IDs; a fan tribute channel exists (UC77sjb1hrR5hqr5ng_nMdyA)."),
      secondary=[{"title": "Sam the Illusionist tribute channel", "url": "https://www.youtube.com/channel/UC77sjb1hrR5hqr5ng_nMdyA", "note": "fan re-upload/tribute channel; subs not recorded"}],
      sources=["https://www.youtube.com/@SAMTHEILLUSIONIST", "https://www.getyourselfoptimized.com/help-from-higher-dimensions-with-sam-the-illusionist/", "https://samtheillusionist.com/session-144"])
