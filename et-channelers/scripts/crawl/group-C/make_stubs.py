#!/usr/bin/env python3
"""Generate credits_exhausted stub files for Group C channels that could not be fetched.
Usage: python3 -I make_stubs.py <channels_dir>
All facts below come from the research notes in
/home/claude/research_notes/ET channelers directory and timeline/*.md (accessed 2026-10-23)."""
import json
import os
import sys

EXH = ("Firecrawl credits ran out before this channel could be queried (no search or provider call "
       "was executed for it). Channel fields below come only from the research notes; videos not read.")


def ch(title=None, handle=None, channel_id=None, url=None, subs=None, vids=None, desc=None,
       observed="2026-10-23", source="research notes"):
    if not any([title, handle, channel_id, url, subs, vids]):
        return None
    rss = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}" if channel_id else None
    return {
        "title": title, "handle": handle, "channel_id": channel_id, "url": url,
        "subscriber_count_text": subs, "video_count_text": vids, "description_short": desc,
        "rss_url": rss, "observed_at": observed, "source": source,
    }


STUBS = [
    ("01_leland", "Susan Leland (\"Ashtar On The Road\")", "channeler", None,
     "Entities per notes: Ashtar 'and the Mentors' (Sananda, Sekhmet, St. Germain). Voice of Ashtar May 2004–Oct 2017; died 2017-10-24. Output was bi-monthly teleconferences with transcripts; no YouTube handle recorded in the notes. " + EXH,
     ["http://www.ashtarontheroad.com/susan_leland_the_voice.html", "https://sananda.website/ashtar-via-susan-leland-november-15th/"], None),
    ("02_stewart", "Sharon Stewart", "channeler", None,
     "Entities per notes: Ashtar Sheran; Ivo of Vega ('Sharon and Ivo'). Site sharonandivo.weebly.com; Twitter @SharonandIvo; book 'Ashtar Sheran: Your Future on Eden' (2020-03-24). No YouTube handle recorded in the notes (listed as a text channeler). " + EXH,
     ["https://awesomegang.com/sharon-stewart/", "https://en.wikipedia.org/wiki/Ashtar_Sheran"], None),
    ("03_velazquez", "Erena Velazquez", "channeler", None,
     "Entities per notes: Ashtar ('commander of the Galactic Federation of Light'), Galactic Federation. Text channeler (messages mirrored on blogs). No YouTube handle recorded in the notes. " + EXH,
     ["https://bgrigolia.wordpress.com/2021/03/19/commander-ashtar-update-freedom-channeled-by-erena-velazquez-scroll-text-down-geo-ru-eng-it/"], None),
    ("04_mcconnell", "James McConnell (Ancient Awakenings)", "channeler", None,
     "Entities per notes: Ashtar, Sananda, 'One Who Serves', St. Germain, Archangel Michael, 'Shoshanna' (JoAnna McConnell), via the weekly Ancient Awakenings Sunday conference call; transcripts republished on Ashtar Command Crew (active Oct 2026). No YouTube handle recorded in the notes. " + EXH,
     ["https://www.ashtarcommandcrew.net/members/JamesMcConnell/content?type=DiscussionEntry&context=all", "https://www.ashtarcommandcrew.net/"], None),
    ("05_gabriel", "Neva Gabriel (Brazil)", "channeler", None,
     "Entity per notes: Ashtar (signs 'Your brother, Ashtar. Adonai.'); Portuguese source site sementesdasestrelas.com.br, English syndication on eraoflight.com (message dated 2026-02-22). No YouTube handle recorded in the notes. " + EXH,
     ["https://eraoflight.com/2026/02/22/a-message-from-ashtar-present-and-future-events/"], None),
    ("06_trutwin", "Elizabeth Trutwin", "channeler", None,
     "Entity per notes: Ashtar / Galactic Federation (book 'Lord Ashtar and the Galactic Federation', 2011-08-09). Biography and platforms are a gap in the notes; no YouTube handle recorded. " + EXH,
     ["https://en.wikipedia.org/wiki/Ashtar_Sheran", "https://hatch.kookscience.com/wiki/Ashtar_Command"], None),
    ("07_acc", "Ashtar Command Crew", "organisation", None,
     "Ning community (ashtarcommandcrew.net, 'The Awakening Movement') syndicating Ashtar/GFL channelings by many authors (James McConnell, Octavia Vasile, etc.); founder/founding year not stated on site (attributed to 'Ben-Arion', unverified). No YouTube channel recorded in the notes. " + EXH,
     ["https://www.ashtarcommandcrew.net/"], None),
    ("10_giordano", "Juan Manuel Giordano (Argentina; Tameana)", "channeler", None,
     "Entity per notes: 'Tamanae', a Pleiadian being who dictated the 'Tameana' crystal-healing technique (automatic writing, later 'direct contact'); Funes/Rosario, Argentina; Instagram @juanmanuelgiordano (125K followers, embed date unknown). No YouTube handle recorded in the notes. " + EXH,
     ["https://www.clarin.com/astrologia/canalizadores-pleyadianos-youtube-nueva-espiritualidad-inunda-redes_0_TBbgjDJOR.html"], None),
    ("11_tozzi", "Edson Tozzi (Brazil)", "channeler", None,
     "Entities per notes: Pleiadians (live 'Conexão REAL com PLEIADIANOS' sessions, e.g. https://www.youtube.com/watch?v=fv14iQ8BPq0) and Arcturians ('Imersão Arcturiana' events); Instagram @edsontozziterapeuta (18K). YouTube handle unresolved in the notes. " + EXH,
     ["https://www.youtube.com/watch?v=fv14iQ8BPq0", "https://www.instagram.com/edsontozziterapeuta/"], None),
    ("14_raisa", "Krista Raisa", "channeler",
     ch(title="Ezoterra", handle="@orioncouncil", url="https://www.youtube.com/@orioncouncil",
        subs="25.2K subscribers", vids="256 videos",
        desc="Trance medium for 'The Orion Council' — 'messages of light from amphibious, spiritual ascension guides' (kristaraisa.com). Channel created 2010-09-30 (legacy user URL /user/staycurly); 1,192,654 total views per Socialblade."),
     "Entity per notes: the Orion Council. Counts (25.2K subscribers, 256 videos, 1,192,654 views) are from the Socialblade page cited in the notes, not from YouTube directly; channel_id not recorded. " + EXH,
     ["https://socialblade.com/youtube/user/staycurly", "https://www.kristaraisa.com/", "https://youtu.be/dcoSl38P5Qs"],
     {"video_id": "dcoSl38P5Qs", "title": "Orion Council Channeled Message June 15 2015", "date": "2015-06-15",
      "url": "https://youtu.be/dcoSl38P5Qs", "source": "research notes"}),
    ("15_chamness", "Rachel Chamness (Sound Waves Heal)", "channeler",
     ch(title="Sound Waves Heal", handle="@soundwavesheal", url="https://www.youtube.com/@soundwavesheal",
        desc="Podcast '5D Channels and Chats with Rachel Chamness'; trance-channels the Blue Avian 'Alpar-a-be-am' (Alparabeam) from planet Kir."),
     "Entity per notes: Alpar-a-be-am, a Blue Avian ('Kir' being). Notes cite the playlist https://www.youtube.com/playlist?list=PLd6XKP8MGvLg2Ea6rKRMwUn1VVEkrgrAX (an Alpar episode showed 285 views); subscriber/video counts not recorded. " + EXH,
     ["https://www.soundwavesheal.com/message-from-blue-avian/", "https://www.youtube.com/playlist?list=PLd6XKP8MGvLg2Ea6rKRMwUn1VVEkrgrAX", "https://sites.libsyn.com/486576"], None),
    ("16_evans", "Sarah Evans (Into the Blue Channeling)", "channeler",
     ch(title="Sarah Evans", handle="@sarahevansandco", url="https://www.youtube.com/@sarahevansandco",
        desc="Sheffield (UK) coach/Akashic reader channeling the 'Pleiadian Group of 9' (aka Pleiadian Council of Light); podcast 'Into the Blue Channeling'."),
     "Entity per notes: Pleiadian Group of 9 / Pleiadian Council of Light (9th–11th dimensions). YouTube counts not recorded in the notes. " + EXH,
     ["https://www.sarahevans.co/intothebluechanneling", "https://open.spotify.com/show/0ybsycLpUWVqmlbe2PdbId"], None),
    ("17_hamden", "Paul Hamden", "channeler", None,
     "Entity per notes: the Zetas ('the Zeta beings who spoke through the medium, Paul Hamden'); books 'The Zeta Interviews' (2022) and 'The Zeta Interviews II' with William Treurniet; interview video https://www.youtube.com/watch?v=6tmpnbEl_vg (channel unknown). No own YouTube handle recorded in the notes. " + EXH,
     ["https://www.amazon.com/Zeta-Interviews-Paul-Hamden/dp/B0B93LSTBV", "https://www.youtube.com/watch?v=6tmpnbEl_vg"], None),
    ("18_whitegoldeagle", "Paul White Gold Eagle (Prime Disclosure)", "channeler",
     ch(title="Paul White Gold Eagle", handle="@PaulWhiteGoldEagle", url="https://www.youtube.com/@PaulWhiteGoldEagle",
        desc="Prime Disclosure: daily 'Galactics / Earth Alliance / Ashtar Command / Motherships' energy updates and 'Transmission from the Arcturian High Council of Light' posts; Patreon since 2017-12-23 (245 paid / 1,466 members)."),
     "Entities per notes: Arcturian High Council of Light; Galactics / Earth Alliance / Ashtar Command (compiled updates — whether channeled vs. compiled is a gap). YouTube counts not recorded. " + EXH,
     ["https://primedisclosure.com/", "https://graphtreon.com/creator/primedisclosure", "https://www.patreon.com/primedisclosure/posts/transmission-of-133040862"], None),
    ("19_lightworkers613", "Fernanda and Flavia (Lightworkers613)", "channeler",
     ch(title="Lightworkers613", channel_id="UCg6ojvQWvbiAomEtV7ruxLA",
        url="https://www.youtube.com/channel/UCg6ojvQWvbiAomEtV7ruxLA",
        desc="Two-woman Patreon community (launched 2019-03-30) offering '120 channelings, 45 classes, 45 ceremonies'."),
     "Entities per notes: 'Arcturian Ambassador… Master Halu'; 'Reptilian Renegade Regulus'; also Yeshua and Mary Magdalene. Channel ID from the Patreon page; counts not recorded. " + EXH,
     ["https://www.patreon.com/lightworkers613", "https://graphtreon.com/creator/lightworkers613"], None),
    ("20_channelingarcturians", "\"Channeling Arcturians\" (Erica of the Sassani)", "channeler", None,
     "Entities per notes: 'Erica of the Essassani / Sassani Representative', 'Arcturian & Pleiadian Council of 7', '9th Dimension Pleiadian', 'Lyrian Council of One', Mantis Beings, 'Krynon's, our Hybrid Family', '9th Dimensional Hybrid Dragons Reptilian'. Channeler unnamed; site channelingarcturians.com; Patreon since 2024-04-04. No YouTube handle recorded in the notes. " + EXH,
     ["https://channelingarcturians.com/", "https://graphtreon.com/creator/ChannelingArcturians", "https://channelingarcturians.com/2026/10/11/conversation-with-erica-october-10-2026-part-2/"], None),
    ("21_liquidlightcodes", "LiquidLightCodes", "channeler", None,
     "Entity per notes: Sirians ('EXTENDED – Sirian Channeled Transmission' in an Akashic series); anonymous Patreon brand launched 2025-07-09. No YouTube handle recorded in the notes. " + EXH,
     ["https://graphtreon.com/creator/LiquidLightCodes", "https://www.patreon.com/LiquidLightCodes/posts/extended-akashic-158721763"], None),
    ("22_arcturussignal", "Arcturus SIGNAL", "channeler", None,
     "Entity per notes: Arcturians ('frequency transmissions for Arcturian starseeds — activations'); anonymous Patreon brand launched 2026-05-21 (58 paid / 327 members, 150 posts); Facebook page linked. No YouTube handle recorded in the notes. " + EXH,
     ["https://graphtreon.com/creator/ArcturusSIGNAL", "https://www.patreon.com/ArcturusSIGNAL"], None),
    ("23_yafi", "Yafi Channeling", "channeler", None,
     "Entity per notes: the Hathors ('Channeling Transmissions, Hathor Sacred Sound, Light Language'); Patreon launched 2025-11-24 (17 paid / 125 members). No YouTube handle recorded in the notes. " + EXH,
     ["https://graphtreon.com/creator/YafiChanneling", "https://www.patreon.com/cw/YafiChanneling/sitemap?l=nl-NL"], None),
    ("24_younger", "Jordan Younger (The Balanced Blonde)", "context", None,
     "Entity per notes: the Pleiadians ('cosmic light beings'), via paid Substack posts from 2025-10-30 ('confessions of a reluctant pleiadian channel'). Wellness influencer; YouTube presence not recorded in the notes. " + EXH,
     ["https://thebalancedblonde.substack.com/p/confessions-of-a-reluctant-pleiadian", "https://thebalancedblonde.substack.com/p/a-message-from-the-pleiadians-about"], None),
    ("25_benda", "Ivo A. Benda (Universe People / Vesmírní lidé)", "organisation", None,
     "Entity per notes: fleet 'led by Ashtar Galactic Command' / 'Cosmic People of the Forces of Light' (Vesmírní lidé sil světla); Czech Republic, contacts from Oct 1997; sites universe-people.com (archived), andele-nebe.cz. No YouTube channel recorded in the notes. " + EXH,
     ["https://en.wikipedia.org/wiki/Universe_People", "https://hatch.kookscience.com/wiki/Cosmic_People_of_the_Forces_of_Light", "https://web.archive.org/web/20201126212624/http://www.universe-people.com/"], None),
    ("26_goode", "Corey Goode", "contactee", None,
     "Entity per notes: 'Blue Avians' / 'Sphere Being Alliance' (trademarked 2018-03-06), '20 and Back' secret-space-program claims; Gaia 'Cosmic Disclosure' 2015–2018; sued Gaia March 2020. Notes state 'Official YouTube handle not resolved' (search results showed e.g. 'Corey Goode Blue Avians - Liberation Of Humanity', '10 years ago'). " + EXH,
     ["https://www.thedailybeast.com/ufo-community-explodes-in-lawsuit-drama-accusations-of-luciferianism", "https://www.govinfo.gov/content/pkg/USCOURTS-cod-1_20-cv-00947/pdf/USCOURTS-cod-1_20-cv-00947-1.pdf"], None),
    ("27_abrahamhicks", "Abraham-Hicks (Esther Hicks)", "context",
     ch(title=None, subs="741,000 subscribers (as reported by Skeptical Inquirer, 2023-08-23)", observed="2023-08-23",
        desc="Esther Hicks channels 'Abraham', 'a collective consciousness'; began 1985 after reading the Seth material."),
     "Non-ET context figure. The only YouTube figure in the notes is '741,000 YouTube subscribers' from the Skeptical Inquirer article of 2023-08-23 (observed_at set to that date); handle/channel_id not recorded (the official channel is believed to be @AbrahamHicks — unverified). " + EXH,
     ["https://skepticalinquirer.org/2023/08/abraham-hicks-motivational-speaking-spirits/", "https://en.wikipedia.org/wiki/Esther_Hicks"], None),
    ("28_jzknight", "JZ Knight / Ramtha", "context", None,
     "Non-ET context figure. Entity per notes: Ramtha, 'the 35,000-year-old warrior from Lemuria'; first appeared 1977 (Tacoma), first public channeling Nov 1978; Ramtha's School of Enlightenment, Yelm WA (1987). No YouTube channel recorded in the notes. " + EXH,
     ["https://en.wikipedia.org/wiki/JZ_Knight", "https://www.encyclopedia.com/science/encyclopedias-almanacs-transcripts-and-maps/mediums-and-channelers"], None),
    ("29_seth", "Seth material / Jane Roberts", "context", None,
     "Non-ET context figure. Entity per notes: Seth, 'an energy personality essence no longer focused in physical matter'; sessions 1963-12-02 to 1984; Roberts died 1984-09-05, so any YouTube presence is an archive/estate channel — none recorded in the notes. " + EXH,
     ["https://en.wikipedia.org/wiki/Jane_Roberts", "https://en.wikipedia.org/wiki/Seth_Material"], None),
    ("30_selig", "Paul Selig", "context", None,
     "Non-ET context figure. Entity per notes: 'the Guides'; clairvoyant since a 1987 experience; books 'I Am the Word' etc.; lives in Maui; appears in Gaia's 'Channeling Conference 2026'. No YouTube channel recorded in the notes. " + EXH,
     ["https://www.paulselig.com/about", "https://en.wikipedia.org/wiki/Paul_Selig"], None),
]


def main():
    out_dir = sys.argv[1]
    for key, person, role, channel, note, sources, earliest in STUBS:
        obj = {
            "person": person,
            "role": role,
            "status": "credits_exhausted",
            "note": note,
            "channel": channel,
            "secondary_channels": [],
            "videos_compact": [],
            "sources": sources,
        }
        if earliest:
            obj["earliest_known_video"] = earliest
        path = os.path.join(out_dir, f"ch_{key}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2)
        print("wrote", path)


if __name__ == "__main__":
    main()
