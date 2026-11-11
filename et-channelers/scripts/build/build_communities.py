#!/usr/bin/env python3
"""Build /home/claude/etc_site/data/communities.json from the forum research notes.

Transcribed from reddit_wizardforums_balg.md plus the Reddit snippet mentions found by
grepping the other notes. No new facts; every row carries its URL. Prints counts only.
"""
import json, re, collections

OUT = "/home/claude/etc_site/data/communities.json"
ACC = "2026-10-23"
NOTES = "/home/claude/research_notes/ET channelers directory and timeline/"
FORUM_NOTE = NOTES + "reddit_wizardforums_balg.md"

# ---------------------------------------------------------------- URLs (short names)
U = {
    "palladian": "https://forum.becomealivinggod.com/t/palladian-aliens/324",
    "bashar7": "https://forum.becomealivinggod.com/t/bashar-7-steps-to-manifesting-your-chosen-reality/6897",
    "reliability": "https://forum.becomealivinggod.com/t/questioning-the-reliability-of-channeling/11379",
    "extra": "https://forum.becomealivinggod.com/t/extratriestrial-or-interdimentional/76015",
    "anunnaki": "https://forum.becomealivinggod.com/t/channeling-the-anunnaki/86487",
    "whatis": "https://forum.becomealivinggod.com/t/to-those-becoming-a-living-god-what-is-a-extraterrestrial/119265",
    "visited": "https://forum.becomealivinggod.com/t/has-anyone-communicated-been-visited-by-aliens/174478",
    "believe": "https://forum.becomealivinggod.com/t/do-you-believe-aliens-are-real-or-not/185298",
    "gfl": "https://forum.becomealivinggod.com/t/galactic-federation-of-light/74116",
    "pleiadians": "https://forum.becomealivinggod.com/t/pleiadians/131604",
    "starseed": "https://forum.becomealivinggod.com/t/anyone-experience-with-being-a-starseed/198706",
    "lucifer": "https://forum.becomealivinggod.com/t/lucifer-wants-me-to-kill-my-spirit-guide/69712",
    "chat": "https://forum.becomealivinggod.com/t/starseed-chat-room/117471",
    "max": "https://forum.becomealivinggod.com/t/max-s-crackhouse-expeditions/89985?page=19",
    "library": "https://forum.becomealivinggod.com/t/library-of-all-knowledge/75657?page=3",
    "william": "https://wizardforums.com/threads/william-message-generation.647/page-9",
    "grace": "https://wizardforums.com/threads/godly-grace.1240/",
    "crawling": "https://wizardforums.com/threads/something-is-crawling-in-the-darkness.3697/post-34280",
    "dee": "https://wizardforums.com/goto/post?id=155247",
}


def q(text, who, date, url, forum, context=None, **extra):
    row = collections.OrderedDict([("text", text), ("who", who), ("date", date), ("url", url), ("forum", forum)])
    if context:
        row["context"] = context
    row.update(extra)
    return row


def thread(date, board, title, url, gist, handles, **extra):
    row = collections.OrderedDict([("date", date), ("board", board), ("title", title), ("url", url),
                                   ("gist", gist), ("handles", handles)])
    row.update(extra)
    return row


# ================================================================ REDDIT
REDDIT_STATUS = ("not retrieved — blocked; snippet-only mentions and leads only")
REDDIT_STATUS_DETAIL = (
    "No Reddit page was read in this project. On 2026-10-23 reddit.com was blocked for every fetch route tried: "
    "WebFetch and Firecrawl scrape were blocked, and two redlib/libreddit mirrors "
    "(https://cal1.lr.ggtyler.dev/r/channeling/top?t=year and https://redlib.catsarch.com/r/channeling/top?t=year) "
    "returned robots_disallowed. WebSearch was unavailable in the forum-research turn, and the Firecrawl search budget "
    "ran out ('Insufficient credits to perform this request') after 7 searches — all spent on BALG and Wizard Forums "
    "site-searches — before any Reddit query could be run. The only Reddit material in the corpus is search-result "
    "titles and snippets captured incidentally while other notes were being researched (ellison_ryok_and_small_channels.md, "
    "youtube_era_channelers.md, anka_bashar.md, entities_and_criticism.md). Each is a single snippet, labelled "
    "'snippet-only': the thread body was never read, so no row below measures thread sentiment, and no tally of "
    "recommended/criticised channelers on Reddit is possible."
)

REDDIT_THREADS = [
    thread("2022-04", "r/Bashar_Essassani", "Has anyone here gotten a reading from Tyler Ellison/Ryok? Was it worth $200?",
           "https://www.reddit.com/r/Bashar_Essassani/comments/txaoaa/has_anyone_here_gotten_a_reading_from_tyler/",
           "Reading price ($200) questioned; a commenter doubts the channeling is still authentic and calls it very commercialized. "
           "The $200 figure matches the 2020 Wix-site price recorded in the notes.",
           [], evidence="snippet-only", date_precision="month", date_basis="approximate; derived from thread ID in the notes",
           snippet="I don't think his channeling is still authentic, but only very very commercialized",
           people=["tyler-ellison"], stance="criticised", found_in="ellison_ryok_and_small_channels.md"),
    thread("2024-08", "r/Bashar_Essassani", "A channeling with Sage of Sassani",
           "https://www.reddit.com/r/Bashar_Essassani/comments/1exwrmc/a_channeling_with_sage_of_sassani/",
           "Thread about another Sassani-type channeled being ('Sage of Sassani', 2024); a commenter recommends Ryok as channeled by Tyler Ellison.",
           [], evidence="snippet-only", date_precision="month", date_basis="'c. Aug 2024' in the notes",
           title_basis="URL slug", snippet="I also highly recommend Ryok of the Sessani as channeled by Tyler Ellison",
           people=["tyler-ellison"], stance="recommended", found_in="ellison_ryok_and_small_channels.md"),
    thread("2026", "r/Bashar_Essassani", "Who are the best channels other than Bashar",
           "https://www.reddit.com/r/Bashar_Essassani/comments/1tc8x1p/who_are_the_best_channels_other_than_bashar/",
           "Ryok / Tyler Ellison listed among the 'best channels other than bashar'.",
           [], evidence="snippet-only", date_precision="year", date_basis="'2026' in the notes", title_basis="URL slug",
           people=["tyler-ellison", "darryl-anka"], stance="recommended", found_in="ellison_ryok_and_small_channels.md"),
    thread(None, "r/Bashar_Essassani", "How to follow excitement when you are sick and… (title truncated in URL)",
           "https://www.reddit.com/r/Bashar_Essassani/comments/1qpezra/how_to_follow_excitement_when_you_are_sick_and/",
           "Passing remark that Tyler Ellison's livestreams sometimes start up to 15 minutes late.",
           [], evidence="snippet-only", date_basis="not given in the notes", title_basis="URL slug",
           snippet="(Sometimes the channeler, Tyler Ellison starts up to 15 minutes late.)",
           people=["tyler-ellison"], stance="neutral", found_in="ellison_ryok_and_small_channels.md"),
    thread("2026-02", "r/Bashar_Essassani", "Join the Ryokah of the Sassani livestream today",
           "https://www.reddit.com/r/Bashar_Essassani/comments/1qxn5ho/join_the_ryokah_of_the_sassani_livestream_today/",
           "Promotional post claiming Darryl Anka and Tyler Ellison have channeled at a number of the same events (unverified in the notes).",
           [], evidence="snippet-only", date_precision="month", date_basis="'c. Feb 2026' in the notes", title_basis="URL slug",
           snippet="Darryl Anka, and Ryokah's channeler, Tyler Ellison, have channeled at a number of the same events",
           people=["tyler-ellison", "darryl-anka"], stance="neutral", found_in="ellison_ryok_and_small_channels.md"),
    thread("2024-12-14", "r/Bashar_Essassani", "Ryokah - A Sassani Response Explaining About the Drones in New Jersey Dec 14, 2024",
           "https://www.reddit.com/r/Bashar_Essassani/comments/1hg371g/ryokah_a_sassani_response_explaining_about_the/",
           "Event-reactive Ryokah session ('Sassani Event 3' with Tyler Ellison and StarShine) on the December 2024 New Jersey drone sightings.",
           [], evidence="snippet-only", date_precision="day", date_basis="event date in the title; thread date not separately given",
           people=["tyler-ellison"], stance="neutral", found_in="ellison_ryok_and_small_channels.md"),
    thread(None, "r/Bashar_Essassani", "Not Bashar but another Sassani being, Elan's very… (title truncated in URL)",
           "https://www.reddit.com/r/Bashar_Essassani/comments/1pdx3vm/not_bashar_but_another_sassani_being_elans_very/",
           "Claims Andrew Bayuk 'did channel Bashar at the beginning to learn how to channel' before channeling Elan (unverified).",
           [], evidence="snippet-only", date_basis="not given in the notes", title_basis="URL slug",
           people=["andrew-bayuk", "darryl-anka"], stance="neutral", found_in="anka_bashar.md"),
    thread(None, "r/cults", "I woke up and left a cult, now I'm asking others to… (title truncated in URL)",
           "https://www.reddit.com/r/cults/comments/1t0okgv/i_woke_up_and_left_a_cult_now_im_asking_others_to/",
           "Cited as a secondary source for fan commentators placing Bashar in a Jane Roberts (Seth) → Tom Massari → Darryl Anka lineage.",
           [], evidence="snippet-only", date_basis="not given in the notes", title_basis="URL slug",
           people=["darryl-anka", "jane-roberts", "thomas-massari"], stance="neutral", found_in="anka_bashar.md"),
    thread(None, "r/awakened", "Elizabeth April: what is your impression on this… (title truncated in URL)",
           "https://www.reddit.com/r/awakened/comments/1tqchak/elizabeth_april_what_is_your_impression_on_this/",
           "Critique of Elizabeth April's self-directed remote viewing as confirmation bias.",
           [], evidence="snippet-only", date_basis="not given in the notes", title_basis="URL slug",
           snippet="Her remote viewing is self directed. She has no feedback from her peers. It's confirmation bias.",
           people=["elizabeth-april"], stance="criticised", found_in="youtube_era_channelers.md"),
    thread(None, "r/starseeds", "Gigi Young anyone? She's a mystic/psychic turned… (title truncated in URL)",
           "https://www.reddit.com/r/starseeds/comments/17r5p02/gigi_young_anyone_shes_a_mysticpsychic_turned/",
           "Fans discuss Gigi Young's pivot from starseed/ET content toward esoteric Christianity; the notes also record the "
           "phrase 'Gigi Young Says Aliens Don't Exist. But didn't Gigi…' from the snippet.",
           [], evidence="snippet-only", date_basis="not given in the notes", title_basis="URL slug",
           people=["gigi-young"], stance="mixed", found_in="youtube_era_channelers.md"),
    thread("2025", "r/starseeds", "What are your thoughts on Gosia and Robert (Cosmic Agency)… (title truncated in URL)",
           "https://www.reddit.com/r/starseeds/comments/1n3bxwy/what_are_your_thoughts_on_gosia_and_robert_cosmic/",
           "A commenter says the Taygetan contact ceased months earlier and the channel has since produced fake content; "
           "the notes pair this with a 2025 Facebook summary that the Swaruu-linked Taygetans were described as 'infiltrated'.",
           [], evidence="snippet-only", date_precision="year", date_basis="'2025' in the notes", title_basis="URL slug",
           snippet="The alleged contact ceased some months ago, and they have been doing massive fake content ever since",
           people=["cosmic-agency-gosia"], stance="criticised", found_in="youtube_era_channelers.md"),
    thread(None, "r/Soulnexus", "Recent channeling from Blossom Goodchild saying… (title truncated in URL)",
           "https://www.reddit.com/r/Soulnexus/comments/c5zwn4/recent_channeling_from_blossom_goodchild_saying/",
           "Calls Goodchild's 14 October 2008 Federation of Light craft-appearance announcement 'a famous failed prediction of a mass landing'.",
           [], evidence="snippet-only", date_basis="not given in the notes", title_basis="URL slug",
           snippet="a famous failed prediction of a mass landing",
           people=["blossom-goodchild"], stance="criticised", found_in="youtube_era_channelers.md"),
]

REDDIT_LEADS = [
    "Subreddits named in the assignment, never searched: r/channeling, r/starseeds, r/lawofone, r/Experiencers, r/Bashar_Essassani, r/aliens, r/Psychic (entry URLs of the form https://www.reddit.com/r/channeling/ — not fetched).",
    "Planned queries never executed: \"r/channeling Bashar\", \"r/starseeds channeler recommend\", \"r/lawofone Q'uo channeling\", \"r/Experiencers channeling Pleiadians\", \"r/Bashar_Essassani Ryok\", \"r/aliens channeling fake\", \"r/Psychic channeling extraterrestrials\", \"reddit Elizabeth April grift\", \"reddit Elena Danaan Galactic Federation\", \"reddit Cosmic Agency Swaruu\", \"reddit Daniel Scranton Arcturian\", \"reddit Sam the Illusionist Pleiadian\".",
    "Open question: whether r/channeling and r/starseeds treat Elizabeth April, Cosmic Agency/Swaruu, Daniel Scranton or Sam the Illusionist as recommended or as grifters (only single snippets exist for April and Cosmic Agency; nothing for Scranton or Sam the Illusionist).",
    "A Reddit thread titled \"Why do people trust Swaruu?\" is noted in entities_and_criticism.md as existing, but its URL was not captured and reddit was blocked.",
    "Thread bodies for every snippet-only row above (all 12 URLs) — none has been read.",
    "Alternative access ideas, all untested: Pushshift-style archives; the Wayback Machine (web.archive.org/web/*/reddit.com/r/channeling*); a search engine with Reddit coverage.",
]

REDDIT_NOT_FOUND = [
    {"person": "athina-krol", "note": "No Reddit threads, forum critiques or journalistic coverage of Athina Król surfaced in WebSearch or Firecrawl search (krol_ashtar_lineage.md, 2026-10-23)."},
]

# ================================================================ WIZARD FORUMS
WF_THREADS = [
    thread("2022-01-12", "The Order > Journals, Thanksgiving & Success Stories", "Journal - William Message Generation", U["william"],
           "Member William (joined 2022-01-11) posts daily 'Generated Messages' produced by a word-shuffle procedure ('SCLx14+last LE per shuffle') "
           "which he attributes to a 'Creator'/'over-mind'; outputs include 'The Ancient Grey Entity', 'Spirit Beings From Saturn', 'Extraterrestrial', "
           "'Aligning With WingMakers', 'Lyricus designs... galactic Tributary Zones'. He quotes the WingMakers 'Neruda Interview Five' on beings that "
           "'present themselves as god through a human channel' and 'how humans and aliens are one' (2022-03-06). DiLoco_DelEted tests a concordance "
           "variant and finds it 'quite interesting'; Just Jim suggests Burroughs cut-ups. Not trance channeling: a bibliomancy-style oracle with ET content.",
           ["William", "DiLoco_DelEted", "Just Jim"],
           date_precision="day", date_basis="journal start; page 9 (read) covers 2022-03-02 to 2022-03-06", date_end="2022-03-06",
           pages="28 pages by 2026; page 9 read", fetched="full page", people=["william"], et_relevance="ET-themed generated messages; WingMakers source"),
    thread("2022-06-12", "The Order > Right Hand Path, White Magic and Divination", "Godly Grace", U["grace"],
           "OP Amur: humanity will get 'Godly Grace' on ascending to 'galactic consciousness'; describes a galactic 'internet-like' network of species; "
           "says Sirians are humble and Pleiadians 'mostly 4 dimensional beings' with a 'vast library' (2022-06-13); claims to have physically met Sirians "
           "reincarnated as humans but not Pleiadians (2022-06-14); says 'Jebus' told him Judgment Day timing; says he is on a 'military assignment' working "
           "as a shaman and has a '40 reincarnation streak' / 'I am really 777' (2022-06-17). Roma mocks ('Not like needing the right TV antenna?') and asks "
           "'Do you meet them physically?' (2022-06-13); DiLoco_DelEted sarcastic; 8Lou1 advises looking inward.",
           ["Amur", "Roma", "DiLoco_DelEted", "8Lou1", "Lord"],
           date_precision="day", date_end="2022-06-17", pages="2 pages; page 1 read", fetched="full page", people=["amur"],
           et_relevance="Sirian/Pleiadian contact claims by a member; mocked"),
    thread("2023-09-20", "The Order > General Occult Discussion", "Something is crawling in the darkness", U["crawling"],
           "Ouija-board contact with an entity 'Danhe' (Ithir). ET content only in stalkinghyena's aside listing current claims: 'extraterrestrial metal spheres' "
           "on the ocean floor and 'Alien babies brought before a legislature' (2023-09-20; evidently the September 2023 Mexican congress 'Nazca mummies' hearing — "
           "the note-taker's inference, not stated in-thread). stalkinghyena: 'melodramatic myth making'; Roma: 'Low level entity' with a 'supervisor'. "
           "William describes homemade boards used via the ideomotor effect (2023-09-22). Marginal to ETs.",
           ["Ithir", "stalkinghyena", "Roma", "8Lou1", "William"],
           date_precision="day", date_end="2023-10-21", fetched="full page", people=["william"], et_relevance="marginal"),
    thread("2026-09-14", "The Order > General Occult Discussion", "[Opinion] What really happened to John Dee and Edward Kelley?", U["dee"],
           "Mostly on Enochian angels vs demons. arbatel83 (Benefactor) describes observing a medium for three years whose channeled answers 'never exceeded the "
           "medium's own knowledge' and became 'spiritually absurd' (~2026-10-19); then an experiment with a Korean shaman who used ancestral spirits as "
           "intermediaries to reach 'higher-dimensional extraterrestrial beings' (a New Age 'starseed' concept); the shaman's narrative mixed Buddhism, starseed lore, "
           "shamanism and Christian Gnosticism and began 'the day Neptune entered Aries'; arbatel83 recited the Shurangama Mantra as banishing and ended contact. "
           "Firetree: whether beings are 'spirits, angels, demons, or projections' 'does not matter' (2026-09-16).",
           ["Mashreqi", "arbatel83", "Frater M.M.", "Firetree", "r4zorenigma", "dcwilson"],
           date_precision="day", date_end="2026-10-19", date_end_basis="approximate ('Monday' relative date)", fetched="full page",
           people=["unnamed-korean-shaman"], et_relevance="second-hand account of ET-channeling experiment; medium criticised"),
]

WF_TALLY = collections.OrderedDict([
    ("recommended", collections.OrderedDict()),  # none found
    ("criticised", collections.OrderedDict([
        ("unnamed-medium-observed-by-arbatel83", {"id": None, "name": "unnamed medium observed for three years by arbatel83", "threads": 1,
            "mentions": [{"who": "arbatel83", "date": "2026-10-19", "date_precision": "approximate", "stance": "criticised",
                          "gist": "'shared delusion'; channeled answers bounded by the medium's own knowledge", "url": U["dee"]}]}),
        ("unnamed-korean-shaman", {"id": "unnamed-korean-shaman", "name": "unnamed Korean shaman channeling 'higher-dimensional extraterrestrial beings' via ancestors", "threads": 1,
            "mentions": [{"who": "arbatel83", "date": "2026-10-19", "date_precision": "approximate", "stance": "criticised",
                          "gist": "experiment abandoned as unreliable; contact ended after Shurangama Mantra", "url": U["dee"]}]}),
        ("amur", {"id": "amur", "name": "Amur (member; Sirian/Pleiadian/galactic-consciousness claims)", "threads": 1,
            "mentions": [{"who": "Roma", "date": "2022-06-13", "stance": "mocked", "gist": "'Not like needing the right TV antenna?' / 'Do you meet them physically?'", "url": U["grace"]},
                         {"who": "DiLoco_DelEted", "date": "2022-06-13", "stance": "sarcastic", "gist": "sarcastic reply", "url": U["grace"]}]}),
    ])),
    ("sources_used_approvingly", [
        {"source": "WingMakers / 'Dr. Neruda' interviews (Neruda Interview Five)", "who": "William", "date": "2022-03-06", "url": U["william"]},
    ]),
    ("public_channelers_named", []),
    ("not_found", ["Bashar/Darryl Anka", "Ashtar (as a named entity)", "Elena Danaan", "Elizabeth April", "Cosmic Agency/Swaruu", "Daniel Scranton", "Galactic Federation"]),
    ("caveat", "Only 2 Firecrawl site-searches completed before credits ran out and the forum's own search requires login; a general 'Bashar / Ashtar / Galactic Federation' site-search could not be run. Treat absence as 'not found', not 'not present'."),
])

WF_QUOTES = [
    q("The Ancient Grey Entity", "William", "2022-03-05", U["william"], "wizardforums", "generated-message item (word-shuffle oracle), not a trance statement"),
    q("Spirit Beings From Saturn", "William", "2022-03-06", U["william"], "wizardforums", "generated-message item (word-shuffle oracle)"),
    q("mostly 4 dimensional beings", "Amur", "2022-06-13", U["grace"], "wizardforums", "describing Pleiadians"),
    q("Do you meet them physically?", "Roma", "2022-06-13", U["grace"], "wizardforums", "challenging Amur's contact claims"),
    q("Not like needing the right TV antenna?", "Roma", "2022-06-13", U["grace"], "wizardforums", "mocking Amur's 'galactic consciousness' network"),
    q("Alien babies brought before a legislature - all happening.", "stalkinghyena", "2023-09-20", U["crawling"], "wizardforums", "listing current ET claims as 'melodramatic myth making'"),
    q("higher-dimensional extraterrestrial beings", "arbatel83", "2026-10-19", U["dee"], "wizardforums", "stated goal of the Korean-shaman experiment; date approximate"),
    q("never exceeded the medium's own knowledge", "arbatel83", "2026-10-19", U["dee"], "wizardforums", "on three years observing a medium's channeled answers; date approximate"),
]

# ================================================================ BALG
BALG_THREADS = [
    thread("2012-08-01", "General Discussion", "Palladian Aliens?", U["palladian"],
           "OP Brutus: a reiki/crystal healer who 'channels guides and helpers' told him his higher guide was a hooded 'palladian alien' (sic, Pleiadian). "
           "Darkness raises Darryl Anka/Bashar; DKM calls Anka possibly 'only HALF fake'; DKM: Pleiadians described as tall blond 'ascended master' types, "
           "'I don't doubt they exist' but most lore fabricated by New Age authors for profit (2012-08-04). Brutus notes the healer never had his birth date yet matched Pleiades/Taurus — 'mystery' (2012-08-04).",
           ["Brutus", "DKM", "Darkness", "GodParty"], date_precision="day", date_end="2012-08-04", fetched="full page",
           people=["unnamed-reiki-crystal-healer", "darryl-anka"], public_channelers=["darryl-anka"]),
    thread("2015-12-24", "Black Magick & The Left Hand Path", "Bashar: 7 steps to manifesting your chosen reality", U["bashar7"],
           "Rygill-85 compares Bashar's method to E.A. Koetting's sigil-less manifesting; debate on whether Anka is a fraud; The_Cusp 'declare[s] shinannigans on the "
           "channeling' (2015-12-31) but says the content is still useful; moderator Lady_Eva splits off-topic replies 'to keep this on-topic about Bashar's work' (2016-01-02); "
           "jackson_caulfield: 'I think it's genius!' (2016-03-05). Replies run to 2021-07-23.",
           ["Rygill-85", "TheDark", "the_magician", "Lady_Eva", "The_Cusp", "jackson_caulfield"], date_precision="day", date_end="2021-07-23",
           pages="page 2 not read", fetched="full page", people=["darryl-anka"], public_channelers=["darryl-anka"]),
    thread("2017-05-15", "General Discussion", "Questioning the reliability of channeling", U["reliability"],
           "Lola describes an obscure non-English blogger (about ten years of contact, c. 2007) who channels (automatic writing) Egyptian gods, archangels, 'the Grey' and Anunnaki "
           "who will 'land in spaceships'; Kazama: 'What a nutjob' (2017-05-15); FraterMagni: possibly a deceptive lower spirit (2017-05-16); Lady_Eva: bad practitioners should not "
           "deter learning (2017-05-18). Blog removed by 2017-05-16.",
           ["Lola", "Kazama", "Fallen_Angel", "FraterMagni", "Lady_Eva"], date_precision="day", date_end="2017-05-18", fetched="full page",
           people=["unnamed-non-english-blogger"]),
    thread("2019-06-07", "General Discussion", "Lucifer wants me to kill my spirit guide", U["lucifer"],
           "OP DankGod (self-described 16-year-old in Sweden) uses a pendulum; says his spirit guide is a Pleiadian and 'lucifer hates my spirit guide because she is a pleiadian'. "
           "Repliers unanimously call it an imposter spirit: Eeikmem 'You have an imposter spirit who is very bored toying with you' (2019-06-08); Manosman: if it misbehaves "
           "'it's not a Pleiadian' (2019-06-08); Faustus links the forum guide 'How to detect imposter spirits'. Shows BALG's standard 'imposter/parasite' test applied to an ET guide.",
           ["DankGod", "Eeikmem", "Manosman", "Lady_Eva", "Faustus", "anon48957109"], date_precision="day", date_end="2019-06-08",
           pages="20+ posts; page 2 not read", fetched="full page", people=[]),
    thread("2019-07-18", "General Discussion", "Galactic federation of light", U["gfl"],
           "anon84896414: 'I was inducted into the galactic federation of light by archangel Ariel' (no method/detail). Sole reply anon48079295: "
           "\"I've only heard new age things about that 'group'\". Only 2 posts visible.",
           ["anon84896414", "anon48079295"], date_precision="day", fetched="full page", people=["anon84896414", "anon48079295"]),
    thread("2019-08-04", "General Discussion", "Extratriestrial or Interdimentional?", U["extra"],
           "OP TheBrokenMold cites E.A. Koetting (Lucifer may be ET) and V.K. Jehannum ('Extratriestrial Shamanism'); consensus of repliers: visiting ETs are interdimensional. "
           "Several posters claim personal encounters (PrinceX: Greys and Pleiadians; anon48079295: Pleiadians, Greys, reptilians 'from another plane'; anon64752597: Greys, "
           "reptilians, mantis-like beings, out-of-body). anon64752597 recommends John Keel, Allen Greenfield, Crowley's Liber Lam, Kenneth Grant and calls the 'alien' frame a "
           "marketing tool / possible egregore (2020-04-09). Knot proposes 'ultra-terrestrial/ultra-temporal' (2020-04-08). Revived 2020-04-07 to 2020-04-15.",
           ["TheBrokenMold", "itsnathanm7", "PrinceX", "anon48079295", "Knot", "anon64752597", "Mind_Seeker20"], date_precision="day", date_end="2020-04-15",
           fetched="full page", people=["thebrokenmold", "princex", "anon48079295", "anon64752597"]),
    thread("2019-11-09", "General Discussion", "Channeling the Anunnaki", U["anunnaki"],
           "TheBrokenMold: Anunnaki '100% extratriestrial' from Nibiru, asks how to reach them (proposes evocation 'as I could evoke any god, demon, or human being'); "
           "anon48079295 reached them 'through projection' in the etheric — 'a race of Gods' with technology, not aliens. No specific Anunnaki deity named; Sitchin not cited.",
           ["TheBrokenMold", "anon48079295", "Bloodwarrior"], date_precision="day", fetched="full page", people=["thebrokenmold", "anon48079295"]),
    thread("2020-06-27", "General Discussion", "'Starseed' chat room", U["chat"],
           "John_Wick opens a chat on chakras, Kybalion, Law of One. MagickBeginner: tarot readings identified them as a 'Star seed Palladian', asks who has contacted them "
           "(2020-06-29); Xendrath: 'You've been lied, sorry' (2020-06-29). anon48079295 lists starseed origins (Pleiadians, Reptilians, Greys, Dracos, Sirians, Arcturians); "
           "NeoFightTheNyophite identifies as starseed/'starborn' as personal gnosis (2020-06-30); Knot reads 'starseeding' psychologically ('about building gravity'). "
           "Page-2 snippet mentions a starseed group's 'pleiadians'.",
           ["John_Wick", "MagickBeginner", "Xendrath", "anon48079295", "NeoFightTheNyophite", "Knot"], date_precision="day", date_end="2020-06-30",
           pages="20+ posts; page 2 not read", fetched="full page", people=["anon48079295"]),
    thread("2020-07-14", "General Discussion", "To (those) becoming a living god, what is a extraterrestrial?", U["whatis"],
           "Cryptic OP ('10,000 earths / One Spaceforce'); Vaynord describes a white-light flash during meditation and a ribbon-shaped craft, vows to Lucifer to defend Earth "
           "from invasion; Nashoba_Eloym: Merkaba 'said to be the pleidians light body and Vehicle'.",
           ["KnowingtheSource", "Lady_Eva", "Vaynord", "Nashoba_Eloym"], date_precision="day", fetched="full page", people=["vaynord"]),
    thread("2020-11-17", "General Discussion", "Pleiadians", U["pleiadians"],
           "OP S_vi_Britannia claims telepathic contact with Pleiadians who 'live on unmapped lands on Earth' and said he will never see them; heard better after banishing "
           "six times a day. anon97554939 questions discernment ('What makes you believe what they say?'); Emeraldtablets asks if egregore; Dralukmun suggests thoughtform and "
           "prescribes 10 evocations with 5 recorded test questions each; anon48079295: the Pleiadians name is Greek myth 'twisted new age lol'; ReyCuervo flags the wording "
           "'advanced race'; OP admits 'I don't know how to test them'.",
           ["S_vi_Britannia", "anon97554939", "Dralukmun", "Emeraldtablets", "anon48079295", "John_Wick", "ReyCuervo"], date_precision="day",
           pages="20+ posts; page 2+ not read", fetched="full page", people=["s-vi-britannia", "anon48079295"]),
    thread("2022-11-19", "Spirits, Evocation & Possession", "Has anyone communicated/been visited by aliens?", U["visited"],
           "Newbie Jtusa27 asks; Mulberry (staff) says the forum prefers initiating contact over waiting, frames it as physical vs astral, suggests searching 'alien', 'et', 'ce5'. No contact claims.",
           ["Jtusa27", "DarkestKnight", "Mulberry"], date_precision="day", fetched="full page", people=["mulberry"]),
    thread("2023-12-15", "General Discussion", "Do you believe aliens are real or not?", U["believe"],
           "OP ANGELS cites the book *A Gift From the Stars* (title matches Elena Danaan's 2020 book; author not named in thread — the note-taker's inference) and says its author "
           "'says she is a Pleaidean' (2023-12-16). Mulberry (staff): 'BALG is not a UFO forum' — alien spirits OK as UPG, physical-ET/political talk may be closed (2023-12-15). "
           "L1zard: ETs are demons/fallen angels, Greys are 'avatars or suits' (cites Whitley Strieber, Joseph Jordan's *Unholy Communion*). DarkestKnight: 'zero factual evidence' for "
           "visitation; astral Grey-like entities per Glenn Morris and Joseph McMoneagle. Ragepanda: the book's claims lack 'evidence or even robust rationales' (2023-12-16). Emissary: "
           "Anunnaki enslaved humans, cites Carl Nagel's *Book of the Old Ones*, *Grimoire of Tiamat*, Clif High/Sarah Westall. nohearth: works with Yog-Sothoth for 'alien magic'. "
           "Prophet: 'study from afar' (2023-12-16).",
           ["ANGELS", "StoicMagus", "Mulberry", "L1zard", "LvxMferre", "DarkestKnight", "CyberLord", "Ragepanda", "nohearth", "Emissary", "SullaFelix", "Prophet"],
           date_precision="day", date_end="2023-12-17", fetched="full page", people=["mulberry", "elena-danaan"],
           public_channelers=["elena-danaan"], public_channelers_note="Elena Danaan link rests on the book title only; the thread never names her."),
    thread("2025-08-12", "General Discussion", "Anyone experience with being a starseed", U["starseed"],
           "UmbraSui asks about conflicting Arcturian lore. Staff member Mulberry: 'UPG alert' — claims Grey, Sirian and Arcturian past lives; says Goetic spirits (Sitri, Agares and "
           "others) told them they are Arcturian; calls the starseed scene 'fluffy', 'scammy', 'hopium'; advises treating ET lore as 'fun fiction'/'working theories' pending astral "
           "corroboration. Mr.Black: ETs are modern shamanic animal-masks; reports meditation contact with a 'Luminous Being'/Hybrid Progenitor (Lyran, Saurian, Crystal race DNA) "
           "(2025-08-13). UmbraSui reports an astral meeting with a four-armed mantis being (2025-08-15). Named sources: Farsight remote viewing, Typically Topical (Draconian starseed article), Gaia, CuriosityStream.",
           ["UmbraSui", "Mulberry", "Mr.Black"], date_precision="day", date_end="2025-08-15", pages="20+ posts; page 2 not read", fetched="full page",
           people=["umbrasui", "mulberry", "mr-black"]),
    thread(None, "unknown", "Max's Crackhouse Expeditions (page 19)", U["max"],
           "Search snippet only: a woman who 'channels Pleiadians... shows how to call a Pleiadian into your life... Personally, the Pleiadians seem nice but it can all be a cover up'.",
           [], fetched="search-only", date_basis="not fetched; date unknown", people=[]),
    thread(None, "unknown", "Library of ALL Knowledge (page 3)", U["library"],
           "Search snippet only: 'Pleiadians have their own individual views and beliefs like any other race'.",
           [], fetched="search-only", date_basis="not fetched; date unknown", people=[]),
]

BALG_TALLY = collections.OrderedDict([
    ("recommended", collections.OrderedDict([
        ("darryl-anka", {"id": "darryl-anka", "name": "Darryl Anka / Bashar", "threads": 2, "net": "mixed — content valued, mediumship doubted",
            "mentions": [
                {"who": "Darkness", "date": "2012-08-01", "stance": "content genuine, channeling unvouched", "gist": "'I cannot vouch for the authenticity of the channeling, but what he says seems to be genuine.'", "url": U["palladian"]},
                {"who": "Rygill-85", "date": "2015-12-27", "stance": "leans genuine", "gist": "'I used to think that Daryl Anka aka Bashar was a fraud…' then leans genuine", "url": U["bashar7"]},
                {"who": "The_Cusp", "date": "2015-12-31", "stance": "content useful", "gist": "content still useful even though he 'declare[s] shinannigans on the channeling'", "url": U["bashar7"]},
                {"who": "jackson_caulfield", "date": "2016-03-05", "stance": "recommended", "gist": "'I think it's genius!'", "url": U["bashar7"]},
            ]}),
    ])),
    ("criticised", collections.OrderedDict([
        ("darryl-anka", {"id": "darryl-anka", "name": "Darryl Anka / Bashar", "threads": 2, "net": "mixed — content valued, mediumship doubted",
            "mentions": [
                {"who": "DKM", "date": "2012-08-01", "stance": "doubted", "gist": "Anka possibly 'only HALF fake'", "url": U["palladian"]},
                {"who": "The_Cusp", "date": "2015-12-31", "stance": "channeling called fraud", "gist": "'I declare shinannigans on the channeling.'", "url": U["bashar7"]},
            ]}),
        ("elena-danaan", {"id": "elena-danaan", "name": "Elena Danaan (via the book *A Gift From the Stars*; identification inferred from the title, author not named in thread)", "threads": 1, "net": "criticised/doubted",
            "mentions": [{"who": "Ragepanda", "date": "2023-12-16", "stance": "criticised", "gist": "claims lack 'evidence or even robust rationales'", "url": U["believe"]}]}),
        ("unnamed-non-english-blogger", {"id": "unnamed-non-english-blogger", "name": "unnamed non-English blogger channeling Egyptian gods / Greys / Anunnaki", "threads": 1, "net": "criticised",
            "mentions": [{"who": "Kazama", "date": "2017-05-15", "stance": "criticised", "gist": "'What a nutjob'", "url": U["reliability"]},
                         {"who": "FraterMagni", "date": "2017-05-16", "stance": "criticised", "gist": "'basket case'; possibly a deceptive lower spirit", "url": U["reliability"]}]}),
        ("s-vi-britannia", {"id": "s-vi-britannia", "name": "S_vi_Britannia (member; telepathic Pleiadian contact)", "type": "forum-member", "threads": 1, "net": "challenged as imposter/thoughtform/egregore",
            "mentions": [{"who": "anon97554939", "date": "2020-11-17", "stance": "challenged", "gist": "'What makes you believe what they say?'", "url": U["pleiadians"]},
                         {"who": "Dralukmun", "date": "2020-11-17", "stance": "challenged", "gist": "suggests thoughtform; prescribes 10 evocations with 5 recorded test questions", "url": U["pleiadians"]},
                         {"who": "Emeraldtablets", "date": "2020-11-17", "stance": "challenged", "gist": "asks if egregore", "url": U["pleiadians"]},
                         {"who": "anon48079295", "date": "2020-11-17", "stance": "dismissive", "gist": "Pleiadians name is Greek myth 'twisted new age lol'", "url": U["pleiadians"]}]}),
        ("dankgod-pleiadian-spirit-guide", {"id": None, "name": "DankGod's Pleiadian spirit guide (member claim)", "type": "forum-member", "threads": 1, "net": "judged an imposter spirit",
            "mentions": [{"who": "Eeikmem", "date": "2019-06-08", "stance": "imposter", "gist": "'You have an imposter spirit who is very bored toying with you'", "url": U["lucifer"]},
                         {"who": "Manosman", "date": "2019-06-08", "stance": "imposter", "gist": "if it misbehaves 'it's not a Pleiadian'", "url": U["lucifer"]}]}),
        ("magickbeginner-star-seed-palladian", {"id": None, "name": "MagickBeginner's tarot-derived 'Star seed Palladian' identity (member claim)", "type": "forum-member", "threads": 1, "net": "dismissed",
            "mentions": [{"who": "Xendrath", "date": "2020-06-29", "stance": "dismissed", "gist": "'You've been lied, sorry'", "url": U["chat"]}]}),
    ])),
    ("sources_cited", [
        {"source": "V.K. Jehannum ('Extratriestrial Shamanism')", "threads": 2, "note": "cited as a source in 2019 threads; itsnathanm7 has 'negative views' of him (2019-08-04). Not a channeler per se.", "urls": [U["extra"], U["anunnaki"]]},
        {"source": "E.A. Koetting (Lucifer may be ET)", "threads": 1, "note": "cited 2019-08-04; disputed by anon64752597 (2020-04-09).", "urls": [U["extra"]]},
        {"source": "WingMakers (not on BALG; see wizardforums)", "threads": 0, "note": "listed for cross-reference only", "urls": []},
    ]),
    ("not_found", ["Elizabeth April", "Daniel Scranton", "Cosmic Agency/Swaruu", "Lee Carroll/Kryon", "Q'uo / L/L Research", "Sam the Illusionist", "Paul Selig", "Ashtar (as a named entity)", "Sheldan Nidle", "Barbara Marciniak", "Billy Meier"]),
    ("caveat", "Searched 2026-10-23 with 5 Firecrawl site-searches before credits ran out; pages beyond page 1 of multi-page threads were not read. Absence reflects limited search coverage as much as community disinterest."),
])

BALG_QUOTES = [
    q("I cannot vouch for the authenticity of the channeling, but what he says seems to be genuine.", "Darkness", "2012-08-01", U["palladian"], "balg", "on Darryl Anka/Bashar"),
    q("only HALF fake", "DKM", "2012-08-01", U["palladian"], "balg", "on Darryl Anka (fragment)"),
    q("I used to think that Daryl Anka aka Bashar was a fraud…", "Rygill-85", "2015-12-27", U["bashar7"], "balg", "truncated in the notes; goes on to lean genuine"),
    q("I declare shinannigans on the channeling.", "The_Cusp", "2015-12-31", U["bashar7"], "balg", "on Bashar; says the content is still useful"),
    q("I think it's genius!", "jackson_caulfield", "2016-03-05", U["bashar7"], "balg", "on Bashar's 7 steps"),
    q("What a nutjob", "Kazama", "2017-05-15", U["reliability"], "balg", "on the unnamed non-English blogger channeling gods/Greys/Anunnaki"),
    q("You have an imposter spirit who is very bored toying with you", "Eeikmem", "2019-06-08", U["lucifer"], "balg", "to DankGod about a 'Pleiadian' spirit guide"),
    q("I was inducted into the galactic federation of light by archangel Ariel", "anon84896414", "2019-07-18", U["gfl"], "balg", "sole claim in a two-post thread"),
    q("I've only heard new age things about that 'group'", "anon48079295", "2019-07-18", U["gfl"], "balg", "reply to anon84896414 on the Galactic Federation of Light"),
    q("pretty much all extraterrestrials are interdimensional", "itsnathanm7", "2019-08-04", U["extra"], "balg"),
    q("I believe they are 100% extratriestrial.", "TheBrokenMold", "2019-11-09", U["anunnaki"], "balg", "on the Anunnaki"),
    q("Im not gonna say ets dont exist, im going to say we haven't encountered them yet", "anon64752597", "2020-04-09", U["extra"], "balg"),
    q("Interdimensional is what they are.", "anon64752597", "2020-04-09", U["extra"], "balg"),
    q("You've been lied, sorry", "Xendrath", "2020-06-29", U["chat"], "balg", "to MagickBeginner's 'Star seed Palladian' tarot identification"),
    q("I can hear these baby beings even better.", "S_vi_Britannia", "2020-11-17", U["pleiadians"], "balg", "on hearing Pleiadians after banishing six times a day"),
    q("BALG is not a UFO forum.", "Mulberry", "2023-12-15", U["believe"], "balg", "staff; physical-ET/political threads may be closed"),
    q("They are not extraterrestrial but Interdimentional beings.", "L1zard", "2023-12-15", U["believe"], "balg"),
    q("there is zero factual evidence for such.", "DarkestKnight", "2023-12-15", U["believe"], "balg", "on physical ET visitation"),
]

# ================================================================ FRAMING (attributed)
def f(theme_id, theme, position, who, date, url, forum, **extra):
    row = collections.OrderedDict([("theme_id", theme_id), ("theme", theme), ("position", position), ("who", who), ("date", date), ("url", url), ("forum", forum)])
    row.update(extra)
    return row

T1 = "Interdimensional, not extraterrestrial (dominant on BALG)"
T2 = "Spirits to be tested like any other spirit (BALG house method)"
T3 = "Egregores / thoughtforms / marketing constructs"
T4 = "Demons / fallen angels / old fairies in new costume"
T5 = "Gods with technology (Anunnaki case)"
T6 = "Physical ETs — minority view, often mocked or ruled off-topic"
T7 = "Starseed identity as UPG / 'living mythology'"
T8 = "Lovecraftian / Typhonian crossover"
T9 = "Attitude to public channelers: content separated from mediumship"

FRAMING = [
    f(1, T1, "pretty much all extraterrestrials are interdimensional", "itsnathanm7", "2019-08-04", U["extra"], "balg", quote=True),
    f(1, T1, "visiting ETs are interdimensional, 'at least the ones who could visit and interact with us'", "PrinceX", "2019-08-04", U["extra"], "balg"),
    f(1, T1, "Interdimensional is what they are.", "anon64752597", "2020-04-09", U["extra"], "balg", quote=True),
    f(1, T1, "proposes 'ultra-terrestrial/ultra-temporal' instead of extraterrestrial", "Knot", "2020-04-08", U["extra"], "balg"),
    f(1, T1, "They are not extraterrestrial but Interdimentional beings.", "L1zard", "2023-12-15", U["believe"], "balg", quote=True),
    f(1, T1, "similar interdimensional framing; StoicMagus: 'spirits of the cosmos'", "CyberLord, SullaFelix, StoicMagus", "2023-12", U["believe"], "balg", date_precision="month"),
    f(1, T1, "hybrid term 'higher-dimensional extraterrestrial beings'", "arbatel83", "2026-10-19", U["dee"], "wizardforums", date_precision="approximate"),
    f(2, T2, "some entities 'can be thought of as' extraterrestrial but most are not approached that way; the frame is physical vs astral", "Mulberry", "2022-11-19", U["visited"], "balg"),
    f(2, T2, "prescribes ten evocations with five recorded test questions each to detect thoughtforms", "Dralukmun", "2020-11-17", U["pleiadians"], "balg"),
    f(2, T2, "the forum's 'imposter spirit' guide applied to a Pleiadian spirit guide", "Eeikmem, Manosman, Faustus", "2019-06-08", U["lucifer"], "balg"),
    f(3, T3, "asks whether the Pleiadian contact is an egregore", "Emeraldtablets", "2020-11-17", U["pleiadians"], "balg"),
    f(3, T3, "thoughtforms 'repeat what the questioner already knows'", "Dralukmun", "2020-11-17", U["pleiadians"], "balg"),
    f(3, T3, "aliens may be egregores 'used for social agendas'; the alien label is a marketing tool", "anon64752597", "2020-04-09", U["extra"], "balg"),
    f(3, T3, "ETs are the modern form of shamanic animal masks; star races map onto human ancestral factions", "Mr.Black", "2025-08-13", U["starseed"], "balg"),
    f(4, T4, "Greys are 'avatars or suits' worn by demons; earlier they appeared as 'Fairies, elves, etc.' (cites Whitley Strieber, Joseph Jordan's *Unholy Communion*)", "L1zard", "2023-12-15", U["believe"], "balg", date_end="2023-12-17"),
    f(4, T4, "the same beings were once called angels and demons", "SullaFelix", "2023-12-17", U["believe"], "balg"),
    f(4, T4, "Enochian angels/demons as the frame; ETs treated as a New Age import", "Dee–Kelley thread participants (Mashreqi, Frater M.M., Firetree and others)", "2026-09", U["dee"], "wizardforums", date_precision="month"),
    f(5, T5, "Anunnaki are 'a race of Gods' whose technology is 'what makes the[m] confused as ETs'; reached 'through projection' in the etheric", "anon48079295", "2019-11-09", U["anunnaki"], "balg"),
    f(5, T5, "Anunnaki '100% extratriestrial' from Nibiru", "TheBrokenMold", "2019-11-09", U["anunnaki"], "balg"),
    f(5, T5, "Anunnaki physically and spiritually present; enslaved humans (cites Carl Nagel's *Book of the Old Ones*, *Grimoire of Tiamat*)", "Emissary", "2023-12-16", U["believe"], "balg"),
    f(6, T6, "BALG is not a UFO forum; physical-ET/political threads may be closed", "Mulberry", "2023-12-15", U["believe"], "balg"),
    f(6, T6, "'zero factual evidence' for physical visitation; astral Grey-like entities per Glenn Morris and Joseph McMoneagle", "DarkestKnight", "2023-12-15", U["believe"], "balg"),
    f(6, T6, "mocks a member's physical-contact claims: 'Do you meet them physically?' / 'Not like needing the right TV antenna?'", "Roma", "2022-06-13", U["grace"], "wizardforums"),
    f(6, T6, "physicalist: white-light flash during meditation, 'ribbon-shaped craft' sighting; vows to defend Earth from invasion", "Vaynord", "2020-07-14", U["whatis"], "balg"),
    f(6, T6, "physicalist: 'study from afar'", "Prophet", "2023-12-16", U["believe"], "balg"),
    f(6, T6, "physicalist: aliens live in a higher dimension (higher-dimension physics)", "UmbraSui", "2025-08-13", U["starseed"], "balg"),
    f(7, T7, "aliens are 'part of living mythology'", "Dralukmun", "2020-11-17", U["pleiadians"], "balg"),
    f(7, T7, "identifies as starseed/'starborn' as personal gnosis", "NeoFightTheNyophite", "2020-06-30", U["chat"], "balg"),
    f(7, T7, "starseed scene is 'fluffy', 'scammy', 'hopium'; own Arcturian/Sirian/Grey past lives flagged 'UPG alert'; treat ET lore as 'fun fiction'/'working theories' until corroborated astrally", "Mulberry", "2025-08-12", U["starseed"], "balg"),
    f(7, T7, "hostile to the starseed term: 'You've been lied, sorry'", "Xendrath", "2020-06-29", U["chat"], "balg"),
    f(8, T8, "links ET work to 'anything Lovecraftian'", "itsnathanm7", "2019-08-04", U["extra"], "balg"),
    f(8, T8, "works 'with yog-sthoth for alien magic'", "nohearth", "2023-12-16", U["believe"], "balg"),
    f(8, T8, "reading list: John Keel, Allen Greenfield, Crowley's Liber Lam, Kenneth Grant", "anon64752597", "2020-04-09", U["extra"], "balg"),
    f(8, T8, "cites Carl Nagel's *Book of the Old Ones*", "Emissary", "2023-12-16", U["believe"], "balg"),
    f(9, T9, "Bashar's manifesting steps valued while the channeling is doubted: 'I declare shinannigans on the channeling.'", "The_Cusp", "2015-12-31", U["bashar7"], "balg"),
    f(9, T9, "Darryl Anka possibly 'only HALF fake'", "DKM", "2012-08-01", U["palladian"], "balg"),
    f(9, T9, "channeled answers 'never exceeded the medium's own knowledge'", "arbatel83", "2026-10-19", U["dee"], "wizardforums", date_precision="approximate"),
]

PEOPLE_FOUND = [
    "mulberry", "s-vi-britannia", "anon84896414", "anon48079295", "anon64752597", "princex", "thebrokenmold", "vaynord",
    "mr-black", "umbrasui",  # BALG
    "amur", "william", "unnamed-korean-shaman",  # Wizard Forums
    "unnamed-non-english-blogger", "unnamed-reiki-crystal-healer",  # reported second-hand on BALG
]
PEOPLE_FOUND_DETAIL = collections.OrderedDict([
    ("mulberry", {"forum": "balg", "role": "staff member", "first_seen": "2022-11-19", "urls": [U["visited"], U["believe"], U["starseed"]]}),
    ("s-vi-britannia", {"forum": "balg", "role": "member", "first_seen": "2020-11-17", "urls": [U["pleiadians"]]}),
    ("anon84896414", {"forum": "balg", "role": "anonymised account", "first_seen": "2019-07-18", "urls": [U["gfl"]]}),
    ("anon48079295", {"forum": "balg", "role": "anonymised account (recurring 2019–2020)", "first_seen": "2019-07-18", "urls": [U["gfl"], U["extra"], U["anunnaki"], U["chat"], U["pleiadians"]]}),
    ("anon64752597", {"forum": "balg", "role": "anonymised account", "first_seen": "2020-04-09", "urls": [U["extra"]]}),
    ("princex", {"forum": "balg", "role": "member", "first_seen": "2019-08-04", "urls": [U["extra"]]}),
    ("thebrokenmold", {"forum": "balg", "role": "member (signs 'C.C. Stallings')", "first_seen": "2019-08-04", "urls": [U["extra"], U["anunnaki"]]}),
    ("vaynord", {"forum": "balg", "role": "member (offers tarot readings)", "first_seen": "2020-07-14", "urls": [U["whatis"]]}),
    ("mr-black", {"forum": "balg", "role": "member", "first_seen": "2025-08-13", "urls": [U["starseed"]]}),
    ("umbrasui", {"forum": "balg", "role": "member", "first_seen": "2025-08-12", "urls": [U["starseed"]]}),
    ("amur", {"forum": "wizardforums", "role": "member", "first_seen": "2022-06-12", "urls": [U["grace"]]}),
    ("william", {"forum": "wizardforums", "role": "member (joined 2022-01-11)", "first_seen": "2022-01-12", "urls": [U["william"], U["crawling"]]}),
    ("unnamed-korean-shaman", {"forum": "wizardforums", "role": "reported second-hand by arbatel83", "first_seen": "2026-10-19", "first_seen_precision": "approximate", "urls": [U["dee"]]}),
    ("unnamed-non-english-blogger", {"forum": "balg", "role": "reported second-hand by Lola; blog removed by 2017-05-16", "first_seen": "2017-05-15", "urls": [U["reliability"]]}),
    ("unnamed-reiki-crystal-healer", {"forum": "balg", "role": "reported second-hand by Brutus", "first_seen": "2012-08-01", "urls": [U["palladian"]]}),
])

HANDLES_SEEN = collections.OrderedDict([
    ("balg", sorted({h for t in BALG_THREADS for h in t["handles"]} | {"Prophet", "ReyCuervo"})),
    ("wizardforums", sorted({h for t in WF_THREADS for h in t["handles"]})),
])


def word_count(s):
    return len(re.findall(r"\S+", s))


def main():
    for row in WF_QUOTES + BALG_QUOTES:
        assert word_count(row["text"]) <= 25, ("quote too long", row["text"])
    for t in REDDIT_THREADS:
        if t.get("snippet"):
            assert word_count(t["snippet"]) <= 25, ("snippet too long", t["snippet"])
    date_re = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
    for coll in (REDDIT_THREADS, WF_THREADS, BALG_THREADS, FRAMING, WF_QUOTES, BALG_QUOTES):
        for row in coll:
            for k in ("date", "date_end"):
                if row.get(k) is not None:
                    assert date_re.match(row[k]), ("bad date", k, row[k])
            assert row.get("url"), ("missing url", row)

    # people referenced anywhere -> make sure every canonical id in people lists is in PEOPLE_FOUND or a public figure
    public = {"darryl-anka", "elena-danaan", "tyler-ellison", "andrew-bayuk", "jane-roberts", "thomas-massari",
              "elizabeth-april", "gigi-young", "cosmic-agency-gosia", "blossom-goodchild", "athina-krol"}
    for coll in (REDDIT_THREADS, WF_THREADS, BALG_THREADS):
        for t in coll:
            for pid in t.get("people", []):
                assert pid in PEOPLE_FOUND or pid in public, ("unknown person id", pid)

    def tally_count(tally):
        return {k: len(v) for k, v in tally.items() if isinstance(v, dict)}

    all_urls = sorted({t["url"] for coll in (REDDIT_THREADS, WF_THREADS, BALG_THREADS) for t in coll})

    out = collections.OrderedDict()
    out["meta"] = collections.OrderedDict([
        ("accessed", ACC),
        ("compiled_from", [FORUM_NOTE, NOTES + "ellison_ryok_and_small_channels.md", NOTES + "youtube_era_channelers.md",
                           NOTES + "anka_bashar.md", NOTES + "entities_and_criticism.md", NOTES + "krol_ashtar_lineage.md"]),
        ("method", "7 Firecrawl site-searches (then 'Insufficient credits'); 20 WebFetch page reads (11 BALG, 4 Wizard Forums, 2 failed Reddit mirrors, 3 BALG follow-ups). "
                   "Pages beyond page 1 of multi-page threads (Pleiadians, Starseed chat room, Lucifer/spirit guide, Godly Grace, Bashar 7 steps p.2) were not read. "
                   "Reddit rows come from search-result snippets captured by other research notes."),
        ("stance_rule", "Opinions are attributed to handles and are those users' views, not established facts. Nothing here is a forum-wide verdict."),
        ("coverage_caveats", [
            "Reddit: zero pages read; snippet-only mentions only. Highest-priority gap.",
            "Not found anywhere in fetched forum material: Elizabeth April, Daniel Scranton, Cosmic Agency/Swaruu, Sam the Illusionist, Lee Carroll/Kryon, Q'uo/L/L Research, Paul Selig, Ashtar (as a named entity), Sheldan Nidle, Barbara Marciniak, Billy Meier. Absence reflects limited search coverage as much as community disinterest.",
            "BALG and Wizard Forums are occult-practitioner forums with a different baseline from Reddit's channeling/starseed subreddits; do not generalise their tallies.",
            "The Elena Danaan link on BALG rests on the book title *A Gift From the Stars* only; the thread never names her.",
        ]),
    ])
    out["reddit"] = collections.OrderedDict([
        ("status", REDDIT_STATUS),
        ("status_detail", REDDIT_STATUS_DETAIL),
        ("evidence_level", "snippet-only"),
        ("threads", REDDIT_THREADS),
        ("snippet_tally", collections.OrderedDict([
            ("caveat", "Counts of single search-result snippets, not thread sentiment; no thread body was read."),
            ("recommended", {"tyler-ellison": 2}),
            ("criticised", {"tyler-ellison": 1, "elizabeth-april": 1, "cosmic-agency-gosia": 1, "blossom-goodchild": 1}),
            ("mixed", {"gigi-young": 1}),
            ("neutral_mentions", {"tyler-ellison": 3, "darryl-anka": 4, "andrew-bayuk": 1, "jane-roberts": 1, "thomas-massari": 1}),
        ])),
        ("tally", {"recommended": {}, "criticised": {}, "note": "No tally possible from the dedicated forum-research session (nothing retrieved); see snippet_tally for the incidental snippets."}),
        ("quotes", []),
        ("not_found", REDDIT_NOT_FOUND),
        ("leads", REDDIT_LEADS),
    ])
    out["wizardforums"] = collections.OrderedDict([
        ("site", "https://wizardforums.com/ (XenForo; 'The Order' sub-forums)"),
        ("status", "4 threads read in full; 2 site-searches only; forum search requires login"),
        ("threads", WF_THREADS),
        ("tally", WF_TALLY),
        ("quotes", WF_QUOTES),
    ])
    out["balg"] = collections.OrderedDict([
        ("site", "https://forum.becomealivinggod.com/ (Become A Living God; Discourse; built around E.A. Koetting's brand)"),
        ("status", "13 threads read in full (page 1 only where multi-page); 2 search-only snippets; 5 site-searches"),
        ("threads", BALG_THREADS),
        ("tally", BALG_TALLY),
        ("quotes", BALG_QUOTES),
    ])
    out["framing"] = FRAMING
    out["framing_themes"] = [collections.OrderedDict([("theme_id", i), ("theme", t)]) for i, t in enumerate([T1, T2, T3, T4, T5, T6, T7, T8, T9], start=1)]
    out["people_found"] = PEOPLE_FOUND
    out["people_found_detail"] = PEOPLE_FOUND_DETAIL
    out["public_channelers_discussed"] = collections.OrderedDict([
        ("balg", ["darryl-anka", "elena-danaan"]),
        ("wizardforums", []),
        ("reddit_snippets", ["tyler-ellison", "darryl-anka", "andrew-bayuk", "elizabeth-april", "gigi-young", "cosmic-agency-gosia", "blossom-goodchild", "jane-roberts", "thomas-massari"]),
    ])
    out["handles_seen"] = HANDLES_SEEN
    out["sources"] = [{"url": u, "title": None, "accessed": ACC} for u in all_urls] + [
        {"url": FORUM_NOTE, "title": "ET channeling on Reddit, Wizard Forums and BALG — dated, sourced notes", "accessed": ACC}]
    # fill titles for thread URLs from the thread rows
    titles = {t["url"]: t["title"] for coll in (REDDIT_THREADS, WF_THREADS, BALG_THREADS) for t in coll}
    for s in out["sources"]:
        if s["title"] is None:
            s["title"] = titles.get(s["url"])

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("reddit threads (snippet-only):", len(REDDIT_THREADS), "| leads:", len(REDDIT_LEADS))
    print("wizardforums threads:", len(WF_THREADS), "| quotes:", len(WF_QUOTES), "| tally:", tally_count(WF_TALLY))
    print("balg threads:", len(BALG_THREADS), "(full:", sum(1 for t in BALG_THREADS if t["fetched"] == "full page"), ") | quotes:", len(BALG_QUOTES), "| tally:", tally_count(BALG_TALLY))
    print("framing rows:", len(FRAMING), "across", len(set(r["theme_id"] for r in FRAMING)), "themes")
    print("people_found:", len(PEOPLE_FOUND), "| handles seen: balg", len(HANDLES_SEEN["balg"]), "wf", len(HANDLES_SEEN["wizardforums"]))
    print("max quote words:", max(word_count(r["text"]) for r in WF_QUOTES + BALG_QUOTES))


if __name__ == "__main__":
    main()
