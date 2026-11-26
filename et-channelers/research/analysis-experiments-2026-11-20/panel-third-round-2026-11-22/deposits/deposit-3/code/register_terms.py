"""Terms of the r3-P41 sense and collision register (step 2, third-round programme).

Written from the literature only, blind to the corpus: no transcript, label, feature, ledger, result or private file was
opened. Every term, sense, collision and rule below comes from dictionaries, published scholarship and reference works
(register_sources.py), or from the class definitions of the programme (cited as PROGRAMME, never as evidence of use).

Form syntax (expanded by build_register.py): {a|b} alternatives; word[s] an optional suffix. Forms are matched on
normalised recognizer text (see the register README, rule G1). Collision codes: E everyday sense; H homograph; R
religious, devotional or New Age sense outside the programme's meaning; Y sense common in YouTube speech generally.
"""

# ---------------------------------------------------------------------------------------------------------------------
# Lists (one per planned use). Visibility: public unless marked.
LISTS = {
    "L01": ("r3-P43-dated-strata", "r3-P43 / r4-P26 (also feeds r3-P44 / r4-P27 through L02)",
            "Co-presence of historically dated vocabularies: one joint table of thematic-historical layers, each with an "
            "entry date and per-term dates where a source gives one"),
    "L02": ("r3-P44-strata-pairs", "r3-P44 / r4-P27",
            "Pairs of L01 layers (and of L05 with L06) tested against the fixed-margin null; the decisive pair marked"),
    "L03": ("r3-P45-density-dimension", "r3-P45", "Density scale against dimension scale (a title-free lineage marker)"),
    "L04": ("r3-P46-source-name-classes", "r3-P46",
            "Source names in titles by class: open (kind or collective names) and franchise-like (individual names used "
            "by many channels in the published record); the unnamed class is a residual rule; the single-channel class "
            "is not written (see README)"),
    "L05": ("r3-P48-control-register-v2", "r3-P48 (also r3-P49, r3-P50, r4-P18, r4-P27 adversary side, r4-P28, r4-P29 base)",
            "Control talk by sub-register, adversary classes split by valence, bridge terms apart"),
    "L06": ("r3-P49-shift-terms", "r3-P49 / r4-P18 (shift curve); r3-P44 conspirituality pair",
            "Shift-of-consciousness vocabulary (the second conviction of conspirituality)"),
    "L07": ("r3-P51-named-actor-classes", "r3-P51 / r4-P28",
            "Named institutions by class, disclosure split into institutional and consciousness-based, contested "
            "public-health content, criminal-law process words"),
    "L08": ("r4-P29-defanging", "r4-P29", "How an adversary's threat is resolved: by inner means or by an outside agent"),
    "L09": ("r3-P52-plural-self-reference", "r3-P52 / r4-P12",
            "First-person plural and singular forms; self-naming and address frames that remove units from the ratio"),
    "L10": ("r3-P53-self-described-modes", "r3-P53 / r4-P30 (groups for r3-P16; received-text class for r3-P14)",
            "Cues of self-described modes of mediation"),
    "L11": ("r3-P55-endorsement", "r3-P55", "References to the creator as the channel, and endorsement predicates"),
    "L12": ("r3-P56-commerce-idiom-dissemination", "r3-P56",
            "Insider idiom of payment as exchange or gift; asks to share a message"),
    "L13": ("r3-P60-destinations-suppression", "r3-P60",
            "Off-platform destination classes (link domains) with funnel depth; suppression talk split into platform "
            "moderation and hidden-actor suppression"),
    "L14": ("r3-P61-persuasion-devices", "r3-P61 (pilot; instrument for the comparison set only)",
            "Persuasion and monetisation devices with devotional twins; price cues for the priced-or-unpriced rule"),
    "L15": ("r3-P40-passed-years", "r3-P40 / r4-P25",
            "Retrospective cue families (fulfilment, timeline split, deferral) near target years; year roles"),
}

# Thematic-historical layers of L01 (r3-P43). entry: when the layer became current; first-currency wording only.
STRATA = {
    "S01": ("Christian end-time (dispensational) vocabulary", "1830s-1852",
            "EO 'rapture' (The Rapture by 1852, after Darby); SANDEEN1970; BOYER1992", "certain for the rapture doctrine; "
            "most terms are biblical and older", "no"),
    "S02": ("Spiritualist vocabulary", "1848", "BRAUDE1989 (Spiritualism from 1848); EO 'medium' (spiritualist sense by "
            "1853), 'aura' (1870)", "certain", "no"),
    "S03": ("Theosophical and early Western esoteric vocabulary", "1875", "CAMPBELL1980; GODWIN1994; EOP; MW 'chakra' 1888",
            "certain for the layer; uncertain for several terms", "no"),
    "S04": ("New Thought vocabulary", "1875-1906", "SATTER1999 (1875-1920); ATKINSON1906; ALBANESE2007",
            "certain for the layer; the New Age sense of 'manifest' is not dated by any dictionary", "no"),
    "S05": ("Ascended-master (I AM) vocabulary", "1934", "KING1934; EAR 'I AM Groups'; EOP 'Ascended Masters'",
            "certain for the layer; the compound 'ascended master' is dated 1924 or 1934 (uncertain)", "no"),
    "S06": ("Contact and federation vocabulary (with evacuation lore that needs ship collocates)", "1947-1952",
            "MW 'flying saucer' 1947; VANTASSEL1952; WRSP2016 (Ashtar 1952; evacuation 1982); FESTINGER1956 (Sananda 1954)",
            "certain", "no"),
    "S07": ("Abduction and ancient-astronaut vocabulary", "1966-1976", "FULLER1966; HOPKINS1981; SITCHIN1976; PARTRIDGE2004",
            "certain for the layer; 'greys' uncertain", "no"),
    "S08": ("Channelling and New Age vocabulary of the 1970s-1980s", "1971", "MW 'New Age' 1971; MW 'channeler' 1983; "
            "LAWOFONE (1981); EOP 'Walk-ins' (1979); DRINKWATER2023 (starseed 1973/1976)", "certain", "no"),
    "S09": ("2012 and ascension vocabulary", "1975-1987", "HOOPES2011; SITLER2006; JENKINS1998; STONE1994",
            "certain for the layer; the planetary sense of 'ascension' uncertain", "no"),
    "S10a": ("Post-2012 non-political end-time hopes", "2005-2011", "TOLLE2005; CANNON2011; COHEN2023",
             "uncertain: the layer's best-known terms have no findable scholarly source (see README)", "no"),
    "S10b": ("Post-2012 political fusion vocabulary", "2017", "AMARASINGAM2020 (QAnon 2017); NAZAR2021; WEF2020; BRUNTON2024",
             "certain for QAnon terms; others per term", "no"),
    "S11": ("Institutional disclosure (narrow layer)", "2001", "ABC2001; NYT2017; DOD2022", "certain", "no"),
    "S12": ("Anti-Masonic and secret-society vocabulary (imported)", "1797", "ROBISON1797; BARRUEL1797; VAUGHN1983; "
            "ROBERTS1972JM", "certain", "yes (imported; kept apart, programme section 5)"),
    "S13": ("Timeline language", "1934 (alternate history) / 1972 (probable realities)", "LEINSTER1934; ROBERTS1972; PRASAD2022",
            "uncertain for the word 'timeline' itself", "no"),
    "S14": ("Devotional names (undated column)", "undated", "PROGRAMME section 5: devotional names are undated", "undated", "no"),
    "S15": ("UFO-conspiracy fusion of the 1990s (New World Order, adversary-being lore)", "1990s",
            "BARKUN2013 (ch. 6); LEWISKAHN2005 (Icke 1999); DEAN1998; AJC2024", "certain for the layer; per-term uncertain", "no"),
}

# Gate sets: a gated term counts only if a gate word occurs within +/- window tokens. A gate word must not be a counted
# term of any OTHER list (programme r3-P41: no list term may serve as another list's sense collocate); build_register.py
# checks this.
GATES = {
    "G-SHIP": ("L01", 15, ["ship", "ships", "craft", "crafts", "spacecraft", "mothership", "motherships", "mother ship",
                           "mother ships", "fleet", "fleets", "starship", "starships", "lift off", "liftoff"]),
    "G-2012": ("L01", 15, ["mayan", "maya", "mayans", "mayan calendar", "maya calendar", "long count", "end date",
                           "december 21st", "21st of december", "december twenty first", "winter solstice"]),
    "G-DISC-INST": ("L07", 10, ["government", "governments", "pentagon", "congress", "congressional", "senate", "hearing",
                                "hearings", "official", "officials", "military", "nasa", "uap", "uaps", "aaro",
                                "declassified", "declassify", "declassification"]),
    "G-DISC-CONSC": ("L07", 10, ["within", "inner", "spiritual", "consciousness", "soul", "souls", "heart", "hearts", "self"]),
    "G-PLATFORM": ("L11", 10, ["subscribe", "subscribed", "subscribing", "subscriber", "subscribers", "video", "videos",
                               "upload", "uploads", "notification", "notifications", "bell", "playlist"]),
    "G-SUPP-PLATFORM": ("L13", 10, ["youtube", "platform", "platforms", "video", "videos", "channel", "algorithm",
                                    "instagram", "tiktok"]),
}

# ---------------------------------------------------------------------------------------------------------------------
TERMS = []


def T(term, lists, forms, senses, psense, coll, rule, src, *, excl=(), gate=None, kind="counted", first="",
      dsrc="", cert="", strand="", trope="no", check="", reason="", blind=""):
    TERMS.append(dict(term=term, lists=lists, forms=list(forms), senses=list(senses), psense=psense, coll=coll,
                      rule=rule, src=list(src), excl=list(excl), gate=gate, kind=kind, first=first, dsrc=dsrc,
                      cert=cert, strand=strand, trope=trope, check=check, reason=reason, blind=blind))


PREC = "cue count; precision unknown until r3-P42's precision band (or a funded read)"

# ===================================================== L01 =============================================================
# S01 Christian end-time
T("rapture", {"L01": "S01"}, ["the rapture"],
  ["ecstatic joy (E)", "the dispensational catching-up of believers before the tribulation (R doctrine)",
   "titles of songs, films and games (Y)"], [2],
  "E: 'in rapture', 'enraptured'. R: New Age writers also apply the word to ascension or evacuation. Y: media titles.",
  "Count only the definite form 'the rapture'; bare 'rapture' and 'raptured' are not counted (sense not resolvable by form). "
  "Kept in S01, never in S06 with evacuation lore (programme section 5).",
  ["EO", "SANDEEN1970", "BOYER1992"], first="by 1852", dsrc="EO 'rapture': The Rapture by 1852, after Darby", cert="certain",
  reason="Marker of the dispensational end-time layer the domain members added.")
T("tribulation (eschatological)", {"L01": "S01"}, ["the tribulation", "great tribulation", "the great tribulation"],
  ["distress or trial (E; 'trials and tribulations')", "the eschatological period of distress before the end (R)"], [2],
  "E: plural idiom 'trials and tribulations' is common in any speech.",
  "Count only the definite or 'great' forms; plural 'tribulations' excluded (E idiom).",
  ["MW", "BOYER1992"], first="biblical (old)", dsrc="MW 'tribulation' 13th century (general sense); end-time use biblical",
  cert="old", reason="End-time marker.")
T("antichrist", {"L01": "S01"}, ["antichrist", "antichrists", "anti christ"],
  ["the eschatological adversary (R)", "a figurative label for a person or institution (E, political)"], [1, 2],
  "E: political insult use. Both senses are end-time vocabulary for a cue count.",
  "Count all forms; " + PREC + ".", ["MW", "BOYER1992"], first="before 12th century", dsrc="MW 'Antichrist'",
  cert="old", trope="no source checked", reason="End-time marker.")
T("armageddon", {"L01": "S01"}, ["armageddon"],
  ["the final battle of Revelation (R)", "any catastrophe (E; film titles, 'financial armageddon')"], [1],
  "E/Y: figurative catastrophe and film title (1998).", "Count all; " + PREC + ".", ["MW", "BOYER1992"],
  first="before 12th century", dsrc="MW 'Armageddon'", cert="old", reason="End-time marker.")
T("end times", {"L01": "S01"}, ["end times"],
  ["the last days before the end (R eschatology)", "scheduling 'end time' of an event (E/Y)"], [1],
  "Y: 'end time' of a stream or event; singular excluded for that reason.", "Count plural 'end times' only.",
  ["MW", "BOYER1992"], first="1917", dsrc="MW 'end-time' 1917", cert="certain", reason="End-time marker.")
T("mark of the beast", {"L01": "S01"}, ["mark of the beast"],
  ["the mark of Revelation 13 (R)", "figurative application to technologies (E/conspiracy)"], [1, 2],
  "Both senses are end-time vocabulary; the second also touches L07's contested content (no shared tokens).",
  "Count all.", ["BOYER1992"], first="biblical (old)", dsrc="Revelation 13 (KJV 1611); BOYER1992 for modern use",
  cert="old", reason="End-time marker.")
T("second coming", {"L01": "S01"}, ["the second coming"],
  ["the return of Christ (R)", "figurative revival ('the second coming of X', E/Y)"], [1],
  "E/Y: figurative use.", "Count the definite form; " + PREC + ".", ["BOYER1992"], first="old",
  dsrc="biblical; BOYER1992", cert="old", reason="End-time marker.")
T("book of revelation", {"L01": "S01"}, ["book of revelation[s]"],
  ["the last book of the New Testament (R)"], [1],
  "Bare 'revelation' is excluded (E, and L07's consciousness-based disclosure collides).", "Count the phrase only.",
  ["BOYER1992"], first="old", dsrc="biblical", cert="old", reason="End-time marker.")
T("apocalypse", {}, ["apocalypse"], ["the revelation genre (R)", "any catastrophe; film and game titles (E/Y)"], [1],
  "E/Y dominate (zombie apocalypse; game titles).", "excluded: everyday and media senses dominate; not resolvable by form.",
  ["MW"], kind="excluded", reason="Listed so reviewers see it was considered.")
# S02 Spiritualist
T("mediumship", {"L01": "S02"}, ["mediumship", "mediums", "psychic medium[s]", "trance medium[s]", "spiritualist medium[s]"],
  ["a means or channel of communication (E; plural usually 'media')", "a middle size or degree (E; 'medium heat')",
   "a person who conveys messages from spirits (Spiritualist)"], [3],
  "E: singular 'medium' is dominated by s1 and s2; Y: 'Medium' the blogging platform.",
  "Count the listed forms only; bare singular 'medium' is excluded (sense not resolvable by form).",
  ["EO", "BRAUDE1989", "WOOFFITT2006"], first="by 1853", dsrc="EO 'medium': spiritualist sense by 1853", cert="certain",
  reason="Spiritualist layer marker.")
T("seance", {"L01": "S02"}, ["seance[s]", "séance[s]"],
  ["a session or sitting (E, MW sense 1, 1803)", "a Spiritualist sitting to contact the dead"], [2],
  "E: rare general sense.", "Count all forms.", ["MW", "BRAUDE1989"], first="1848 (layer)",
  dsrc="MW 1803 dates only the general sense; the Spiritualist sense follows the layer", cert="sense undated",
  reason="Spiritualist layer marker.")
T("spirit guide", {"L01": "S02", "L04": "OPEN"}, ["spirit guide[s]"],
  ["a discarnate guide of a medium or person (Spiritualist and later)", "a character type in games or films (Y)"], [1],
  "Y: games.", "Count all forms.", ["BRAUDE1989", "WAHBEHMILLER"], first="1848 (layer)",
  dsrc="no dictionary entry; dated by layer only", cert="term undated", reason="Spiritualist layer; open source name in titles.")
T("ectoplasm", {"L01": "S02"}, ["ectoplasm", "ectoplasmic"],
  ["outer cytoplasm (biology)", "a substance said to issue from a medium (Spiritualist)", "pop-culture slime (Y)"], [2],
  "E: biology lectures; Y: film references.", "Count all; " + PREC + ".", ["MW", "BRAUDE1989"], first="1883 (biology)",
  dsrc="MW 1883 dates the biological sense only", cert="sense undated", reason="Spiritualist layer marker.")
T("spirit world", {"L01": "S02"}, ["spirit world", "spirit realm[s]", "world of spirit"],
  ["the realm of spirits (Spiritualist and broader religious use)"], [1],
  "R: Indigenous and Christian uses; Y: game worlds.", "Count all; " + PREC + ".", ["BRAUDE1989", "TOMLINSON2019"],
  first="1848 (layer)", dsrc="dated by layer only", cert="term undated", reason="Spiritualist layer marker.")
T("aura", {"L01": "S02"}, ["auric", "auric field", "aura field", "auras", "{your|my|her|his|their|the} aura"],
  ["a distinctive atmosphere (E; 'an aura of mystery')", "a subtle emanation around living beings (Spiritualist, later "
   "New Age)", "a migraine aura (medical)"], [2],
  "E: 'aura of'; medical: migraine.", "Count listed forms; exclude any form followed by 'of'.",
  ["EO", "MW"], excl=["{the|an} aura of", "aura of"], first="1870", dsrc="EO 'aura': 1870 in spiritualism", cert="certain",
  reason="Spiritualist layer marker.")
# S03 Theosophical
T("akashic", {"L01": "S03"}, ["akashic", "akashic record[s]", "akasha"],
  ["a Theosophical record of all events, readable by clairvoyance"], [1], "Few collisions; 'Akasha' also a game name (Y).",
  "Count all forms.", ["WIKIAKASHIC", "HAMMER2001"], first="1881-1899", dsrc="WIKIAKASHIC citing Brandt and Hammer 2013",
  cert="uncertain", reason="Theosophical marker.")
T("root race", {"L01": "S03"}, ["root race[s]"], ["Blavatsky's evolutionary stages of humanity"], [1],
  "The phrase may be heard as racial; the register keeps the doctrinal sense and the neutral class name.",
  "Count all.", ["BLAVATSKY1888", "BERENDT2025"], first="1888", dsrc="BLAVATSKY1888 (primary)",
  cert="certain (primary work)", reason="Theosophical marker.")
T("lemuria", {"L01": "S03"}, ["lemuria", "lemurian[s]"],
  ["a hypothetical sunken land of 19th-century zoogeography", "a lost continent of occult lore", "crystal-trade names "
   "('Lemurian seed crystals', commercial)"], [2],
  "Commercial: crystal names collide with L12/L14 offer talk (no shared tokens).", "Count all.", ["EO"],
  first="1864 (zoology)", dsrc="EO: name given by Sclater 1864; occult use not dated", cert="uncertain (occult sense)",
  reason="Theosophical lost-continent marker.")
T("atlantis", {"L01": "S03"}, ["atlantis", "atlantean[s]"],
  ["Plato's island", "an occult lost civilisation", "names of hotels, films and series (E/Y)"], [2],
  "Y: film and series names.", "Count all; " + PREC + ".", ["MW"], first="1602 (word)",
  dsrc="MW 'Atlantis' 1602; occult currency follows the layer, not dated here", cert="uncertain (occult sense)",
  reason="Lost-continent marker.")
T("chakra", {"L01": "S03"}, ["chakra[s]", "chakric"],
  ["a subtle-body centre (yoga, Tantra; Western esotericism)", "an energy resource in anime and games (Y)"], [1],
  "Y: anime and games.", "Count all; " + PREC + ".", ["MW", "LEADBEATER1927"], first="1888",
  dsrc="MW 'chakra' 1888; LEADBEATER1927", cert="certain", reason="Early Western esoteric marker.")
T("kundalini", {"L01": "S03"}, ["kundalini"],
  ["coiled energy of Tantric yoga", "a brand of yoga classes (commercial)"], [1], "Commercial classes collide with offers.",
  "Count all.", ["AVALON1919"], first="1919", dsrc="AVALON1919 (The Serpent Power)", cert="certain (Western currency)",
  reason="Early Western esoteric marker.")
T("karma", {"L01": "S03"}, ["karma", "karmic", "karmically"],
  ["the doctrine of action and consequence", "everyday payback ('instant karma', E)", "points or song titles (Y)"], [1],
  "E/Y collisions frequent.", "Count all; " + PREC + ".", ["MW"], first="1827", dsrc="MW 'karma' 1827 (pre-Theosophy)",
  cert="certain", reason="Popularised in English by the Theosophical layer.")
T("reincarnation", {"L01": "S03"}, ["reincarnation", "reincarnate", "reincarnated", "reincarnating"],
  ["rebirth of a soul in a new body", "figurative revival (E)"], [1], "E: figurative.", "Count all.", ["MW"],
  first="1845", dsrc="MW 'reincarnation' 1845", cert="certain", reason="Theosophical-layer doctrine word.")
T("astral", {"L01": "S03"}, ["astral", "astral plane", "astral body", "astral projection", "astral travel", "astral realm[s]"],
  ["of the stars (archaic)", "a Theosophical plane or subtle body", "names in games (Y)"], [2],
  "Y: game titles.", "Count all; the longest form wins inside L01.", ["MW"], first="1605 (word)",
  dsrc="MW 'astral' 1605 dates sense 1; the Theosophical sense is undated", cert="uncertain (sense)",
  reason="Theosophical marker.")
T("etheric", {"L01": "S03"}, ["etheric"], ["ethereal (E, rare)", "a Theosophical subtle body or plane"], [2],
  "Few collisions.", "Count all.", ["MW"], first="c1681 (word)", dsrc="MW 'etheric' c1681 (= ethereal)",
  cert="uncertain (sense)", reason="Theosophical marker.")
T("great white brotherhood", {"L01": "S03"}, ["great white brotherhood", "white brotherhood"],
  ["the masters as a collective in Theosophical and I AM doctrine ('white' as spiritual light)"], [1],
  "The word 'white' may be heard racially; the register records the doctrinal sense only.", "Count all.",
  ["EOP", "EAR"], first="1920s-1934", dsrc="EOP; EAR; dates conflict (Leadbeater 1925 or Ballard 1934)", cert="uncertain",
  reason="Theosophical and I AM marker.")
T("el morya", {"L01": "S03", "L04": "FRANCHISE"}, ["el morya", "master morya", "morya"],
  ["a Theosophical Master, later channelled by many groups"], [1], "Few collisions.", "Count all.", ["EOP"],
  first="1880s (layer)", dsrc="EOP: special role in the formation of the Theosophical Society", cert="certain (layer)",
  reason="Theosophical master name; franchise-like source name.")
T("kuthumi", {"L01": "S03", "L04": "FRANCHISE"}, ["kuthumi", "koot hoomi", "koothoomi", "kut humi"],
  ["a Theosophical Master, later channelled by many groups"], [1], "Few collisions.", "Count all.", ["EOP"],
  first="1880s (layer)", dsrc="EOP", cert="certain (layer)", reason="Theosophical master name.")
T("djwhal khul", {"L01": "S03", "L04": "FRANCHISE"}, ["djwhal khul", "djwal khul", "djwal kul"],
  ["the Master Alice Bailey called 'the Tibetan'"], [1], "'The Tibetan' is excluded (E).", "Count listed forms.",
  ["EOP"], first="1919-1949 (Bailey)", dsrc="EOP", cert="certain (layer)", reason="Theosophical lineage name.")
T("maitreya", {"L01": "S03", "L04": "FRANCHISE"}, ["maitreya", "lord maitreya"],
  ["the future Buddha (R, Buddhist)", "an office in the Theosophical hierarchy"], [2],
  "R: Buddhist teaching talk.", "Count all; " + PREC + ".", ["EOP"], first="Theosophical (layer)",
  dsrc="EOP: Jesus said to hold the office of Maitreya", cert="certain (layer)", reason="Theosophical hierarchy name.")
# S04 New Thought
T("law of attraction", {"L01": "S04"}, ["law of attraction"],
  ["the New Thought principle that thought attracts its like", "a physics law (rare)"], [1], "Physics: rare.",
  "Count all.", ["ATKINSON1906", "ALBANESE2007"], first="1906", dsrc="ATKINSON1906 (title)", cert="certain (title use)",
  reason="New Thought marker.")
T("manifesting", {"L01": "S04"}, ["manifesting", "manifestor[s]", "manifest {your|it|that|this|what}"],
  ["obvious (adjective, E)", "to show or become evident (E)", "to bring about by intention (New Thought, New Age)",
   "a shipping manifest (H)", "a being's appearing (R; 'the being manifests')"], [3],
  "E, H and R senses; R collides with channelling talk itself.",
  "Count the listed forms only; bare 'manifest' and 'manifestation' are excluded (sense not resolvable by form).",
  ["CROCKFORD2022", "ALBANESE2007"], first="not dated", dsrc="no dictionary lists the sense", cert="undated",
  reason="New Thought marker in contemporary use (Crockford 2022).", blind="precision decided by r3-P42's checks, not by reading")
T("abundance", {"L01": "S04"}, ["abundance"],
  ["plenty (E; 'an abundance of')", "prosperity consciousness (New Thought, New Age)"], [2],
  "E: 'an abundance of caution'.", "Count 'abundance' except in the excluded 'of' forms.", ["CROCKFORD2022"],
  excl=["{an|the} abundance of", "abundance of"], first="not dated", dsrc="no dictionary lists the sense",
  cert="undated", reason="Prosperity vocabulary (Crockford 2022: manifest abundance).")
T("affirmation", {"L01": "S04"}, ["affirmation[s]"],
  ["assent or confirmation (E)", "a repeated positive self-statement (New Thought practice; also I AM decrees)",
   "a legal affirmation (H)"], [2], "E and legal senses.", "Count all; " + PREC + ".", ["MW", "EAR"],
  first="not dated", dsrc="MW 15th century dates sense 1a only", cert="undated", reason="New Thought practice word.")
T("vibration (spiritual)", {"L01": "S04"},
  ["vibrational", "{high|higher|low|lower} vibration[s]"],
  ["mechanical oscillation (E, physics)", "a phone's vibrate mode (Y)", "the spiritual quality of thought or person "
   "(New Thought, New Age)"], [3],
  "E/Y: physics and phones; bare 'vibration' and 'vibes' excluded.", "Count the listed forms only.",
  ["ATKINSON1906", "CROCKFORD2021"], first="1906", dsrc="ATKINSON1906 (title 'Thought Vibration')",
  cert="certain (title use)", reason="New Thought marker still current (Crockford 2021).")
# S05 I AM
T("ascended master", {"L01": "S05", "L04": "OPEN"}, ["ascended master[s]"],
  ["beings said to have passed beyond rebirth who guide humanity (Theosophy; I AM)"], [1], "Few collisions.",
  "Count all.", ["EOP", "EAR", "KING1934"], first="1924 or 1934", dsrc="EOP; compound dated 1924 or 1934 (sources conflict)",
  cert="uncertain", reason="I AM marker; open collective source name.")
T("violet flame", {"L01": "S05"}, ["violet flame", "violet fire", "violet consuming flame"],
  ["the transmuting flame invoked in I AM practice"], [1], "Few collisions.", "Count all.", ["EAR"], first="1934 (layer)",
  dsrc="EAR (I AM Groups)", cert="certain (layer)", reason="I AM marker.")
T("i am presence", {"L01": "S05"}, ["i am presence", "mighty i am", "mighty i am presence"],
  ["the individualised presence of God in I AM doctrine"], [1],
  "Shares tokens with L09's first-person forms and self-naming frame 'I am'; the full phrase is required.",
  "Count the full phrase only.", ["EAR", "KING1934"], first="1934", dsrc="EAR; KING1934", cert="certain",
  reason="I AM marker.")
T("saint germain", {"L01": "S05", "L04": "FRANCHISE"},
  ["saint germain", "st germain", "comte de saint germain", "count saint germain", "count of saint germain"],
  ["the 18th-century Count of St Germain (historical)", "the Ascended Master Saint Germain", "Paris Saint-Germain "
   "football club (Y/E)", "Saint-Germain-des-Pres (place)"], [2],
  "Y/E: football club and Paris place names.", "Count listed forms except the excluded ones.",
  ["EOP", "EAR", "KING1934"], excl=["paris saint germain", "saint germain des pres", "st germain des pres"],
  first="1934 (I AM; earlier Theosophical claims)", dsrc="EOP; EAR", cert="uncertain (earlier Theosophical use)",
  reason="I AM master name; franchise-like source name.")
T("christ consciousness", {"L01": "S05"}, ["christ consciousness"],
  ["a state of spiritual realisation (I AM lineage and wider New Age)"], [1], "R: Christian mystical talk.", "Count all.",
  ["EAR"], first="not dated", dsrc="EAR (Church Universal and Triumphant entry)", cert="undated",
  reason="I AM-lineage phrase.")
# S06 contact and federation
T("flying saucer", {"L01": "S06"}, ["flying saucer[s]"], ["a disc-shaped aerial craft reported from 1947"], [1],
  "Few collisions.", "Count all.", ["MW"], first="1947", dsrc="MW 'flying saucer' 1947", cert="certain",
  reason="Contact-layer marker.")
T("ufo", {"L01": "S06"}, ["ufo", "ufos", "u f o", "u f os"],
  ["an unidentified flying object", "band, brand and toy names (Y)"], [1], "Y: names.", "Count all.", ["MW"],
  first="1952", dsrc="MW 'UFO' 1952", cert="certain", reason="Contact-layer marker.")
T("extraterrestrial", {"L01": "S06"}, ["extraterrestrial[s]", "extra terrestrial[s]"],
  ["a being from beyond Earth", "adjective in astrobiology ('extraterrestrial life')"], [1, 2],
  "'ET' is excluded: it collides with the time-zone abbreviation (Y) and Latin 'et'.", "Count listed forms only.",
  ["MW"], first="1950", dsrc="MW noun 1950", cert="certain", reason="Contact-layer marker.")
T("space brothers", {"L01": "S06"}, ["space brother[s]", "space brothers and sisters"],
  ["benevolent beings of 1950s contactee lore"], [1], "Few collisions.", "Count all.", ["LEWIS1995"], first="1950s",
  dsrc="LEWIS1995 publisher description", cert="certain (period)", strand="federation", reason="Federation strand.")
T("ashtar", {"L01": "S06", "L04": "FRANCHISE"},
  ["ashtar", "ashtar command", "ashtar galactic command", "ashtar sheran"],
  ["a commander channelled from 1952 and by many channels since", "an ancient deity name (Ishtar, Ashtart; H)"], [1],
  "H: ancient Near Eastern deity in history talk.", "Count all; the longest form wins inside a list.",
  ["WRSP2016", "VANTASSEL1952"], first="1952", dsrc="WRSP2016 (messages from 1952; Ashtar Command 1952)", cert="certain",
  strand="federation", reason="Federation strand; franchise-like source name.")
T("sananda", {"L01": "S06", "L04": "FRANCHISE"}, ["sananda"],
  ["a figure presented as the contemporary identity of Jesus (1954 group; later many channels)"], [1], "Few collisions.",
  "Count all.", ["FESTINGER1956"], first="1954", dsrc="FESTINGER1956 ch. II", cert="certain",
  reason="Contact-layer name; franchise-like source name.")
T("galactic federation", {"L01": "S06", "L04": "OPEN"},
  ["galactic federation", "galactic federation of light", "federation of light"],
  ["a benevolent federation of star nations in channelled lore", "fictional federations (Y; games, series)"], [1],
  "Bare 'the federation' is excluded (Star Trek, sports federations).", "Count listed forms.",
  ["LANDES", "BERENDT2025"], first="by 1994", dsrc="LANDES (Nidle); BERENDT2025 cites Essene and Nidle 1995",
  cert="uncertain", strand="federation", reason="Federation strand; open collective name.")
T("confederation of planets", {"L01": "S06"},
  ["confederation of planets", "confederation of planets in the service of the infinite creator"],
  ["the Law of One's benevolent confederation"], [1],
  "Bare 'confederation' excluded (E: Confederate, Canadian Confederation).", "Count the phrase only.", ["LAWOFONE"],
  first="1981", dsrc="LAWOFONE session 1 (15 Jan 1981)", cert="certain (primary)", strand="federation",
  reason="Federation strand.")
T("mothership", {"L01": "S06"}, ["mothership[s]", "mother ship[s]"],
  ["a large craft carrying smaller ones (E, science fiction)", "a ship of contact or evacuation lore"], [2],
  "E/Y: science-fiction and metaphor ('the mothership of all...').", "Count all; " + PREC + ".", ["MW"],
  first="not dated", dsrc="no source dates the contact sense", cert="undated",
  reason="Contact-layer vocabulary; also a gate word of 'evacuation' inside L01.",
  check="MW headword cited for the everyday sense, not fetched")
T("evacuation (contact lore)", {"L01": "S06"},
  ["evacuation[s]", "world evacuation", "planetary evacuation", "mass evacuation"],
  ["leaving a place of danger (E: fire, flood, war)", "a planetary lift-off by ships in contact lore"], [2],
  "E dominates; the ship gate selects s2.", "Count only with a G-SHIP word within 15 tokens; never in S01.",
  ["WRSP2016"], gate="G-SHIP", kind="gated", first="1982", dsrc="WRSP2016 (Tuella, Project World Evacuation, 1982)",
  cert="certain", strand="federation", reason="Programme: evacuation lore with ship collocates stays in the contact layer.")
# S07 abduction and ancient astronaut
T("alien abduction", {"L01": "S07"},
  ["alien abduction[s]", "abductee[s]", "abduction experience[s]", "abduction phenomenon"],
  ["kidnapping (E, legal)", "a reported taking by non-human beings"], [2],
  "E: 'abductee' also in crime news; bare 'abduction' excluded.", "Count listed forms.",
  ["FULLER1966", "BULLARD1987", "MW"], first="1966", dsrc="FULLER1966; MW 'abductee' 1832 dates the general sense",
  cert="certain (layer)", strand="adversarial", reason="Abduction-layer marker.")
T("missing time", {"L01": "S07"}, ["missing time"],
  ["time unaccounted for (E)", "amnesia reported in abduction accounts"], [2], "E: everyday.",
  "Count all; " + PREC + ".", ["HOPKINS1981"], first="1981", dsrc="HOPKINS1981 (title)", cert="certain (title use)",
  reason="Abduction-layer marker.")
T("greys (beings)", {"L01": "S07", "L04": "OPEN", "L05": "ADV-AMB"},
  ["the greys", "the grays", "grey alien[s]", "gray alien[s]", "the zetas", "zeta reticuli", "reticulan[s]"],
  ["the colour (E)", "a type of non-human being in abduction lore"], [2],
  "E: colour words; only the listed phrases are counted.", "Count listed forms.", ["BERENDT2025", "WIKIGREY", "PARTRIDGE2004"],
  first="1961-1987", dsrc="WIKIGREY (popular by 1987); BERENDT2025", cert="uncertain", strand="adversarial",
  reason="Adversary-capable beings of mixed valence.")
T("anunnaki", {"L01": "S07", "L05": "ADV-AMB"}, ["anunnaki", "anunaki", "annunaki"],
  ["Mesopotamian deities (H; Assyriology)", "Sitchin's ancient astronauts"], [2], "H: scholarly history talk.",
  "Count all.", ["SITCHIN1976"], first="1976", dsrc="SITCHIN1976", cert="certain", strand="adversarial",
  reason="Ancient-astronaut marker; mixed valence.")
T("nibiru", {"L01": "S07"}, ["nibiru", "planet x"],
  ["a Babylonian astronomical name (H)", "Sitchin's twelfth planet", "a doomsday planet (from 1995)",
   "a hypothetical outer planet in astronomy ('Planet X', E)"], [2, 3],
  "E: astronomy news on a hypothetical planet.", "Count all; " + PREC + ".", ["SITCHIN1976", "WIKINIBIRU"],
  first="1976 / 1995", dsrc="SITCHIN1976; WIKINIBIRU (Lieder 1995)", cert="certain", reason="Ancient-astronaut marker.")
T("ancient astronaut", {"L01": "S07"}, ["ancient astronaut[s]"],
  ["beings said to have visited Earth in antiquity"], [1], "Few collisions.", "Count all.", ["ELKINS1984", "SITCHIN1976"],
  first="by 1984", dsrc="ELKINS1984 (title)", cert="uncertain (earliest use)", reason="Ancient-astronaut marker.")
# S08 New Age 1970s-1980s
T("new age", {"L01": "S08"}, ["new age", "new ager[s]", "new agey"],
  ["a new era (E; 'a new age of')", "the spiritual movement", "a coming astrological or biblical age (R)"], [2],
  "E: 'a new age of X' is common.", "Count listed forms except the excluded ones.",
  ["MW", "SUTCLIFFE2003", "HANEGRAAFF1996"], excl=["a new age", "new age of", "the new age of"], first="1971",
  dsrc="MW 'New Age' noun 1971; SUTCLIFFE2003 (from the 1930s)", cert="certain", reason="Layer name word.")
T("age of aquarius", {"L01": "S08"}, ["age of aquarius", "aquarian age"],
  ["an astrological age", "the song (Y)"], [1], "Y: song title.", "Count all.", ["CAMPION2015"],
  first="20th century", dsrc="CAMPION2015 (dating quoted only secondhand)", cert="uncertain",
  reason="New Age marker.")
T("starseed", {"L01": "S08"}, ["starseed[s]", "star seed[s]", "star people"],
  ["people who say they came from other worlds or dimensions to help Earth"], [1], "Few collisions ('star people' rare).",
  "Count all.", ["DRINKWATER2023", "STEIGER1981", "BERENDT2025"], first="1973 / 1976",
  dsrc="DRINKWATER2023 (Leary 1973 title; Steiger 1976 concept)", cert="certain (1970s)", reason="New Age marker.")
T("walk-in", {"L01": "S08"}, ["walk ins", "walk in soul[s]", "walk in being[s]"],
  ["a walk-in closet, clinic or appointment (E/Y)", "a soul said to replace another in an adult body"], [2],
  "E/Y: 'walk-ins welcome' (salons, clinics). Singular 'a walk in' excluded (idiom 'a walk in the park').",
  "Count listed forms; " + PREC + ".", ["EOP", "MONTGOMERY1979"], first="1979", dsrc="EOP 'Walk-ins'; MONTGOMERY1979",
  cert="certain", reason="New Age marker.")
T("wanderer (Law of One)", {"L01": "S08"}, ["wanderers"],
  ["people who wander (E)", "souls of higher density incarnated on Earth (Law of One)"], [2],
  "E/Y: songs and games.", "Count the plural; " + PREC + ".", ["LAWOFONE"], first="1981",
  dsrc="LAWOFONE sessions 2 and 12 (Jan 1981)", cert="uncertain (as first use)", reason="Law of One marker.",
  blind="precision decided by r3-P42's checks, not by reading")
T("indigo children", {"L01": "S08"}, ["indigo child", "indigo children", "indigo kids"],
  ["children said to show a special aura colour and gifts"], [1], "Bare 'indigo' excluded (colour).", "Count phrases.",
  ["WHEDON2009", "CARROLL1999"], first="1982 / 1999", dsrc="WHEDON2009 (Tappe 1982); CARROLL1999", cert="certain",
  reason="New Age marker.")
T("social memory complex", {"L01": "S08"}, ["social memory complex", "social memory complexes"],
  ["a collective consciousness in Law of One terms"], [1], "Few collisions.", "Count all.", ["LAWOFONE"], first="1981",
  dsrc="LAWOFONE session 2 (20 Jan 1981)", cert="certain (primary)", reason="Law of One marker.")
T("service to others", {"L01": "S08", "L05": "BRIDGE"},
  ["service to others", "service to other", "service to self"],
  ["volunteering or caring ethic (E)", "the two polarities of the Law of One"], [2],
  "E: charity talk. Acronyms STS and STO are excluded (other meanings).",
  "Count all; in L05 these are BRIDGE terms (cosmology by default; bridge only near a CR-A or CR-B term).",
  ["LAWOFONE"], first="1981", dsrc="LAWOFONE (site keyword 'Service to Others')", cert="uncertain (first use)",
  reason="Polarity cosmology (programme section 5).")
T("gaia", {"L01": "S08"}, ["gaia"],
  ["the Greek earth goddess (R, myth)", "Lovelock's Gaia hypothesis (science)", "Earth as a living being (New Age)",
   "a streaming platform for spiritual content of the same name (Y)"], [3],
  "Y: the platform name; science: the hypothesis.", "Count all; " + PREC + ".", ["MW", "LOVELOCK1979"], first="1972",
  dsrc="MW 'Gaia' 1972; LOVELOCK1979", cert="certain", reason="New Age Earth-being name.")
# S09 2012 and ascension
T("2012 (end-date sense)", {"L01": "S09", "L15": "YEAR-LIT"}, ["2012"],
  ["the calendar year (E)", "the 2012 end-date of New Age lore"], [2],
  "E: any date talk.", "Count only with a G-2012 word within 15 tokens (L01); in L15 the year is a literature target year.",
  ["HOOPES2011", "SITLER2006"], gate="G-2012", kind="gated", first="1975-1987",
  dsrc="HOOPES2011; SITLER2006", cert="certain", reason="2012 layer marker; literature target year.")
T("mayan calendar", {"L01": "S09"}, ["mayan calendar", "maya calendar", "mayan long count", "long count"],
  ["the Maya calendar systems (scholarly)", "the calendar read as ending in 2012 (New Age)"], [1, 2],
  "Archaeology talk shares the words.", "Count all.", ["SITLER2006", "HOOPES2011"], first="1975-1987",
  dsrc="SITLER2006; HOOPES2011", cert="certain", reason="2012 layer marker.")
T("galactic alignment", {"L01": "S09"}, ["galactic alignment"], ["Jenkins's solstice alignment with the galactic centre"],
  [1], "Few collisions.", "Count all.", ["HOOPES2011", "JENKINS1998"], first="1990s", dsrc="HOOPES2011; JENKINS1998",
  cert="uncertain (exact year)", reason="2012 layer marker.")
T("harmonic convergence", {"L01": "S09"}, ["harmonic convergence"], ["the event of 16-17 August 1987"], [1],
  "Few collisions.", "Count all.", ["HOOPES2011"], first="1987", dsrc="HOOPES2011", cert="certain",
  reason="2012 layer marker; also a literature target year in L15.")
T("photon belt", {"L01": "S09"}, ["photon belt"], ["a band of light Earth is said to enter"], [1], "Few collisions.",
  "Count all.", ["NEXUS1991"], first="1991 or earlier", dsrc="NEXUS1991 (secondary access)", cert="uncertain",
  reason="Pre-2012 lore.")
T("ascension", {"L01": "S09", "L06": "SHIFT"}, ["ascension"],
  ["rising (E)", "the Ascension of Jesus (R, Christian)", "individual ascension of I AM doctrine (1930s)",
   "a collective or planetary ascension (New Age, 1990s on)", "game and product titles (Y)"], [3, 4],
  "R: Christian feast; Y: titles.", "Count 'ascension' except the excluded feast and place forms; " + PREC + ".",
  ["EOP", "EAR", "STONE1994", "CROCKFORD2021"], excl=["ascension day", "ascension island", "ascension thursday"],
  first="1930s / 1994", dsrc="EAR; EOP (I AM); STONE1994 (planetary manuals)", cert="uncertain (planetary sense)",
  reason="2012 and ascension layer; shift vocabulary.")
# S10a post-2012 non-political end-time hopes
T("new earth", {"L01": "S10a", "L06": "SHIFT"}, ["new earth", "the new earth"],
  ["the new heaven and new earth of Revelation 21 (R)", "a planetary transition in New Age lore",
   "an Earth-like exoplanet (E, science news)"], [2],
  "R and science collisions.", "Count listed forms except 'new earth like'; " + PREC + ".",
  ["TOLLE2005", "CANNON2011"], excl=["new earth like"], first="2005-2011", dsrc="TOLLE2005; CANNON2011 (titles)",
  cert="uncertain", reason="Post-2012 non-political hopes; shift vocabulary.")
T("three waves of volunteers", {"L01": "S10a"},
  ["three waves of volunteers", "{first|second|third} wave of volunteers"],
  ["Cannon's souls who volunteered to incarnate"], [1], "Few collisions.", "Count all.", ["CANNON2011"], first="2011",
  dsrc="CANNON2011", cert="certain (title)", reason="Post-2012 non-political hopes.")
# S10b political fusion
T("qanon", {"L01": "S10b"}, ["qanon", "q anon"], ["the conspiracy movement named after 'Q'"], [1],
  "Bare 'q' excluded (letter).", "Count all.", ["AMARASINGAM2020"], first="2017", dsrc="AMARASINGAM2020", cert="certain",
  trope="possible; not checked for this term", reason="Political fusion marker.")
T("deep state", {"L01": "S10b", "L05": "CR-A"}, ["deep state"],
  ["entrenched unelected power (political science; Turkish derin devlet)", "a hidden controlling group (conspiracy)"], [1, 2],
  "Both senses are control vocabulary for a cue count.", "Count all.", ["MW", "AMARASINGAM2020"], first="1997",
  dsrc="MW 'deep state' 1997 (translation of Turkish)", cert="certain", trope="possible; not checked for this term",
  reason="Political fusion; control register.")
T("nesara", {"L01": "S10b"}, ["nesara", "gesara", "nesara gesara"],
  ["a 1990s reform proposal recast as a promised financial reset"], [1], "Few collisions.", "Count all.",
  ["BRUNTON2024", "BELLINGCAT2022"], first="1990s / mid-2010s", dsrc="BELLINGCAT2022; BRUNTON2024",
  cert="certain (NESARA); uncertain (GESARA)", reason="Political fusion marker.")
T("med bed", {"L01": "S10b"}, ["med bed[s]", "medbed[s]"], ["a promised healing device of 2020s lore"], [1],
  "Few collisions.", "Count all.", ["LEADSTORIES2021"], first="by Feb 2021", dsrc="LEADSTORIES2021", cert="uncertain",
  reason="Political fusion marker.")
T("plandemic", {"L01": "S10b", "L07": "CONTEST-PH"}, ["plandemic"], ["the claim that the COVID-19 pandemic was planned"],
  [1], "Few collisions.", "Count all.", ["NAZAR2021"], first="2020", dsrc="NAZAR2021", cert="certain",
  reason="Political fusion marker; contested public-health content.")
T("great reset", {"L01": "S10b"}, ["great reset", "the great reset"],
  ["the World Economic Forum's 2020 initiative (institutional)", "a conspiracy reading of it"], [1, 2],
  "The two senses cannot be told apart by form.", "Count all as a cue.", ["WEF2020"], first="2020", dsrc="WEF2020",
  cert="certain", reason="Political fusion marker.")
T("red pill", {"L01": "S10b"}, ["red pill", "red pilled", "redpilled", "red pilling"],
  ["a reference to the 1999 film", "a political awakening (2010s)", "a gender-politics usage (Y)", "a medicine (E, rare)"],
  [2], "Y: manosphere sense.", "Count all; " + PREC + ".", ["MW"], first="1999 / 2015",
  dsrc="MW 'red pill' noun 1999, verb 2015", cert="certain", reason="Political fusion marker.")
# S11 institutional disclosure
T("uap", {"L01": "S11", "L07": "DISC-INST"},
  ["uap", "uaps", "unidentified anomalous {phenomena|phenomenon}", "unidentified aerial {phenomena|phenomenon}"],
  ["the US government's term for unidentified phenomena"], [1], "Few collisions.", "Count all.", ["DOD2022", "NYT2017"],
  first="2017-2022", dsrc="NYT2017; DOD2022", cert="certain", reason="Institutional disclosure layer.")
T("aaro", {"L01": "S11", "L07": "DISC-INST"}, ["aaro", "all domain anomaly resolution office"],
  ["the US office established in 2022"], [1], "Few collisions.", "Count all.", ["DOD2022"], first="2022", dsrc="DOD2022",
  cert="certain", reason="Institutional disclosure layer.")
T("disclosure project", {"L01": "S11"}, ["disclosure project"], ["the 2001 campaign for UFO disclosure"], [1],
  "Few collisions.", "Count all.", ["ABC2001"], first="2001", dsrc="ABC2001", cert="certain",
  reason="Institutional disclosure layer.")
T("ufo disclosure (phrase)", {"L01": "S11", "L07": "DISC-INST"},
  ["{ufo|uap|alien|government|official} disclosure"],
  ["official release of information on unidentified phenomena"], [1],
  "Nested: contains 'ufo' (L01 S06) and 'disclosure' (L07 gated); the longest form wins inside a list.", "Count all.",
  ["ABC2001", "NYT2017"], first="2001", dsrc="ABC2001", cert="certain", reason="Institutional disclosure layer.")
# S12 anti-Masonic (imported)
T("freemason", {"L01": "S12"}, ["freemason[s]", "freemasonry", "masonic", "free mason[s]"],
  ["the fraternal order (E)", "a hidden actor in conspiracy narratives"], [1, 2],
  "Bare 'mason(s)' excluded (stonemasons; surname).", "Count listed forms.", ["VAUGHN1983", "ROBERTS1972JM"],
  first="1797 / 1826", dsrc="ROBISON1797; VAUGHN1983 (Antimasonic Party 1826-1843)", cert="certain",
  trope="possible; not checked for this term", reason="Imported layer (programme section 5).")
T("illuminati", {"L01": "S12", "L05": "CR-A"}, ["illuminati", "illuminatus", "bavarian illuminati"],
  ["religious-enlightenment groups (MW sense 1, 1599)", "the Bavarian order of 1776", "a hidden controlling group "
   "(conspiracy, from 1797)", "music-industry meme talk (Y)"], [3],
  "Y: meme talk.", "Count all.", ["MW", "ROBISON1797", "BARRUEL1797", "ROBERTS1972JM", "AJC2024"], first="1797",
  dsrc="ROBISON1797; BARRUEL1797", cert="certain", trope="yes (AJC2024 lists it under 'when it's antisemitic')",
  reason="Imported layer; control register.")
T("secret society", {"L01": "S12", "L05": "CR-A"}, ["secret societ{y|ies}"],
  ["a fraternal or student society (E)", "a hidden controlling group (conspiracy)"], [2], "E: fiction and fraternities.",
  "Count all; " + PREC + ".", ["ROBERTS1972JM"], first="1797 (layer)", dsrc="ROBERTS1972JM", cert="certain (layer)",
  reason="Imported layer; control register.")
# S13 timeline language
T("timeline split", {"L01": "S13", "L15": "SPLIT"},
  ["timeline split", "timelines split", "split timeline[s]", "split of the timelines", "parallel timeline[s]",
   "alternate timeline[s]", "alternative timeline[s]", "timeline jump[s]", "timeline jumping", "jump timelines",
   "jumped timelines", "shifted timelines", "timeline shift"],
  ["a chronology (E)", "branching or parallel histories (science fiction; New Age lore)"], [2],
  "E: 'project timeline'; only the listed branching forms are counted.", "Count listed forms.",
  ["LEINSTER1934", "ROBERTS1972"], first="1934 / 1972", dsrc="LEINSTER1934 (alternate history); ROBERTS1972",
  cert="uncertain (the word 'timeline' itself)", reason="Timeline language (programme: older than it looks); split cue family.")
T("timeline (evaluative)", {"L01": "S13"},
  ["{new|old|higher|lower|positive|negative|best|original} timeline[s]", "collaps{ing|ed} timeline[s]"],
  ["a chronology (E; 'the new timeline for the project')", "a branch of possible history (New Age lore)"], [2],
  "E: planning talk.", "Count listed forms; " + PREC + ".", ["LEINSTER1934", "ROBERTS1972"], first="1934 / 1972",
  dsrc="as above", cert="uncertain", reason="Timeline language.", blind="precision decided by r3-P42's checks, not by reading")
T("parallel reality", {"L01": "S13"},
  ["parallel realit{y|ies}", "parallel universe[s]", "parallel world[s]", "probable realit{y|ies}", "probable self",
   "probable selves"],
  ["physics or science-fiction parallel worlds (E)", "co-existing realities (Seth material; New Age)"], [2],
  "E: physics talk.", "Count all; " + PREC + ".", ["ROBERTS1972", "LEINSTER1934"], first="1934 / 1972",
  dsrc="ROBERTS1972 (introduced 'probable realities', publisher)", cert="certain (probable realities, 1972)",
  reason="Timeline language.")
T("mandela effect", {"L01": "S13"}, ["mandela effect"], ["shared false memories read as evidence of shifted timelines"],
  [1], "Few collisions.", "Count all.", ["PRASAD2022"], first="2009-2010", dsrc="PRASAD2022", cert="uncertain (2009 or 2010)",
  reason="Timeline language.")
# S14 devotional names (undated)
T("jesus", {"L01": "S14", "L04": "FRANCHISE"}, ["jesus"],
  ["the historical and religious figure (R)", "an interjection (E; 'Jesus!')", "a channelled source name"], [1, 3],
  "E: interjection.", "Count all; " + PREC + ".", ["PROGRAMME", "EAR"], first="undated", dsrc="programme rule",
  cert="undated", reason="Devotional name (undated column); franchise-like source name in titles.")
T("christ", {"L01": "S14"}, ["christ", "jesus christ"],
  ["the title of Jesus (R)", "an interjection (E)"], [1], "E: interjection.", "Count all; the longest form wins.",
  ["PROGRAMME"], first="undated", dsrc="programme rule", cert="undated", reason="Devotional name.")
T("yeshua", {"L01": "S14", "L04": "FRANCHISE"}, ["yeshua", "jeshua"],
  ["the Hebrew-Aramaic name of Jesus, used by many channels"], [1], "Few collisions.", "Count all.", ["PROGRAMME"],
  first="undated", dsrc="programme rule", cert="undated", reason="Devotional name; franchise-like source name.")
T("mother mary", {"L01": "S14", "L04": "FRANCHISE"}, ["mother mary", "virgin mary", "blessed mother"],
  ["the mother of Jesus (R)", "a channelled source name"], [1, 2], "R: Catholic devotion.", "Count all.",
  ["PROGRAMME", "EAR"], first="undated", dsrc="programme rule", cert="undated", reason="Devotional name.")
T("archangel michael", {"L01": "S14", "L04": "FRANCHISE"},
  ["archangel michael", "michael the archangel", "saint michael", "st michael"],
  ["the archangel (R)", "a channelled source name", "place and church names (E)"], [1, 2], "E: place names.",
  "Count all; a person named Michael is not matched (phrase forms only).", ["PROGRAMME"], first="undated",
  dsrc="programme rule", cert="undated", reason="Devotional name.")
T("metatron", {"L01": "S14", "L04": "FRANCHISE"}, ["metatron", "archangel metatron"],
  ["an angel of Jewish mystical lore (R)", "a channelled source name", "film and game characters (Y)"], [1, 2],
  "Y: characters.", "Count all.", ["PROGRAMME"], first="undated", dsrc="programme rule", cert="undated",
  reason="Devotional name.")
T("archangel (generic)", {"L01": "S14"}, ["archangel[s]"], ["a chief angel (R)"], [1], "Few collisions.",
  "Count all; named forms win by longest match.", ["PROGRAMME"], first="undated", dsrc="programme rule", cert="undated",
  reason="Devotional name class.")
T("holy spirit", {"L01": "S14"}, ["holy spirit", "holy ghost"], ["the third person of the Trinity (R)"], [1],
  "Y: 'Holy Ghost' in film titles.", "Count all.", ["PROGRAMME", "EAR"], first="undated", dsrc="programme rule",
  cert="undated", reason="Devotional name.")
T("quan yin", {"L01": "S14", "L04": "FRANCHISE"}, ["quan yin", "kuan yin", "guan yin", "kwan yin"],
  ["the bodhisattva of compassion (R)", "a channelled source name"], [1, 2], "R: Buddhist devotion.", "Count all.",
  ["PROGRAMME"], first="undated", dsrc="programme rule", cert="undated", reason="Devotional name.")
T("mother earth", {"L01": "S14"}, ["mother earth"], ["the Earth personified (E, ecological and devotional)"], [1],
  "E: ecological idiom.", "Count all; " + PREC + ".", ["PROGRAMME"], first="undated", dsrc="programme rule",
  cert="undated", reason="Devotional name.")
T("god (excluded)", {}, ["god"], ["the deity (R)", "an interjection (E; 'oh my god')"], [1],
  "E: interjection dominates.", "excluded: not resolvable by form.", ["MW"], kind="excluded",
  reason="Considered for S14; excluded.")
T("creator (excluded)", {}, ["creator", "the creator", "prime creator"],
  ["the deity (R)", "a content creator (Y, very frequent on the platform)"], [1],
  "Y: 'content creator', 'creator studio'.", "excluded: the platform sense collides.", ["MW"], kind="excluded",
  reason="Considered for S14 and L04; excluded.")
# S15 UFO-conspiracy fusion
T("new world order", {"L01": "S15", "L05": "CR-A"}, ["new world order", "nwo"],
  ["a reordering of international relations (E, political science; 1990 speeches)", "a planned totalitarian world "
   "government (conspiracy)"], [2],
  "E: international-relations talk.", "Count all; " + PREC + ".", ["BARKUN2013", "AJC2024"], first="1990s (layer)",
  dsrc="BARKUN2013 ch. 6", cert="certain (layer)", trope="yes (AJC2024)", reason="UFO-conspiracy fusion; control register.")
T("reptilians", {"L01": "S15", "L05": "ADV-NEG"},
  ["reptilian[s]", "reptoid[s]", "reptilian race", "reptilian agenda"],
  ["of reptiles (E, zoology)", "the 'reptilian brain' of the triune-brain model (E, self-help talk)",
   "adversary beings of 1990s conspiracy lore"], [3],
  "E: 'reptilian brain' is common in self-help speech.", "Count listed forms except the excluded brain forms.",
  ["LEWISKAHN2005", "BARKUN2013", "BERENDT2025"], excl=["reptilian brain", "reptilian mind", "reptilian part"],
  first="1999", dsrc="LEWISKAHN2005 (Icke 1999)", cert="certain (1999); 'reptoid' undated", strand="adversarial",
  trope="possible (et's condition; programme section 5); not checked for this term",
  reason="Adversarial strand; negative valence.")
T("draco", {"L01": "S15", "L05": "ADV-NEG"}, ["draco", "dracos", "draconians", "draconian race", "alpha draconis"],
  ["the constellation (E)", "'draconian' = harsh (E, laws)", "reptilian adversary beings"], [3],
  "E: the adjective 'draconian' (laws, measures) is excluded by form: only the listed forms count.", "Count listed forms.",
  ["BERENDT2025", "LEWISKAHN2005"], first="1990s", dsrc="LEWISKAHN2005 (Alpha Draconis, Icke 1999)", cert="uncertain",
  strand="adversarial", reason="Adversarial strand; negative valence.")
T("archons", {"L01": "S15", "L05": "ADV-NEG"}, ["archon[s]", "archontic"],
  ["Athenian magistrates (H)", "Gnostic rulers of the cosmos (R)", "adversary beings in contemporary conspiritual lore"], [3],
  "H/R: history and Gnosticism talk.", "Count all; " + PREC + ".", ["LASH2006"], first="2006", dsrc="LASH2006",
  cert="uncertain", strand="adversarial", reason="Adversarial strand.")
T("one world government", {"L01": "S15", "L05": "CR-A"}, ["one world government", "one world order"],
  ["a single global government (E, political theory)", "a hidden plan for global control (conspiracy)"], [2],
  "E: political theory.", "Count all.", ["CROCKFORD2021", "BARKUN2013"], first="1990s (layer)", dsrc="CROCKFORD2021",
  cert="uncertain", trope="possible; not checked for this term", reason="UFO-conspiracy fusion; control register.")
# considered and not listed (no source or genre term)
for _t, _why in [
    ("channel / channeling / channelled (genre terms)",
     "excluded: selection terms. The roster was selected on channelling, so the genre words would make the layer present "
     "by construction; MW 'channeler' 1983 dates the sense."),
    ("lightworker", "not listed: no scholarly or reference source dates or documents it (searched 2026-11-26); only "
                    "popular claims (1980s; 1997 book). Would need corpus knowledge to place."),
    ("twin flame", "not listed: no scholarly source found (popular sources attribute it to the 1970s)."),
    ("the Event (predicted planetary event)", "not listed: no findable source; would need corpus knowledge."),
    ("solar flash", "not listed: no findable scholarly source."),
    ("the shift / the great shift (bare)", "not listed: no source for the bare form, and 'shift' is everyday (E); the "
                                           "sourced phrase 'shift in consciousness' sits in L06."),
    ("great awakening", "context-assigned between S10a (spiritual) and S10b (political); also the US religious revivals "
                        "(R). Flagged, never counted."),
    ("golden age (in L01)", "not in L01: everyday sense dominates; kept in L06 only, with a precision band."),
    ("andromedans", "not listed: none of the sources found names them (Berendt 2025 lists other star origins)."),
    ("alien / aliens", "not in L01: undated and general (E: immigration law; film titles)."),
    ("the federation (bare)", "excluded: Star Trek and sports federations (Y/E)."),
    ("harvest (Law of One)", "excluded: crop and seasonal senses dominate (E/Y); no gate available inside L01."),
    ("mahatma", "excluded: the honorific of Gandhi dominates (H)."),
    ("medium (singular, bare)", "excluded: means and size senses dominate (E)."),
    ("the other side", "excluded: everyday spatial and argumentative senses dominate (E)."),
    ("roswell / area 51 / men in black", "not listed: no source verified this session; 'men in black' also a film "
                                         "franchise (Y)."),
]:
    T(_t, {}, [], ["see rule"], [1], "", _why, ["PROGRAMME"], kind="not listed", reason="Considered; reason in rule.")

# ===================================================== L03 =============================================================
_ORD = "{first|second|third|fourth|fifth|sixth|seventh|eighth|1st|2nd|3rd|4th|5th|6th|7th|8th}"
_ORDD = "{third|fourth|fifth|sixth|seventh|eighth|ninth|twelfth|3rd|4th|5th|6th|7th|8th|9th|12th}"
T("density (ordinal)", {"L03": "DEN"}, [_ORD + " densit{y|ies}", "{higher|lower} densities", "the densities"],
  ["mass per volume (E, physics)", "a level of consciousness in the Law of One's seven densities"], [2],
  "E: physics; bare 'density' and 'dense' excluded.", "Count ordinal forms only.", ["LAWOFONE"], first="1981",
  dsrc="LAWOFONE session 12", cert="certain (primary)", reason="Density scale (r3-P45).")
T("dimension (ordinal)", {"L03": "DIM"},
  [_ORDD + " dimension[s]", _ORDD + " dimensional", "{higher|lower} dimension[s]", "higher dimensional",
   "multidimensional", "multi dimensional"],
  ["a measurable extent (E, maths)", "time as the fourth dimension (physics)", "a level of consciousness or reality "
   "(New Age)", "the pop group The 5th Dimension (Y)"], [3],
  "E/physics: 'fourth dimension', 'multidimensional analysis'; Y: band name.", "Count all; " + PREC + ".",
  ["COHEN2023"], first="not dated", dsrc="no source dates the New Age sense", cert="undated",
  reason="Dimension scale (r3-P45).", blind="precision decided by r3-P42's checks, not by reading")
T("numeral-D", {"L03": "DIM"},
  ["5d", "6d", "7d", "9d", "12d", "4d",
   "3d {reality|world|earth|realm|consciousness|plane|existence|experience|density|level|body|human|humans|life}"],
  ["a dimension level written with a numeral (New Age)", "3D printing, models and films (E/Y)",
   "'5D chess' (meme, Y)", "a camera model ('5D Mark', Y)", "4D cinema or ultrasound (E)"], [1],
  "E/Y: technology and media senses; '3d' alone is excluded.", "Count listed forms except the excluded ones.",
  ["COHEN2023"], excl=["5d chess", "5d mark", "4d {movie|movies|cinema|ultrasound|scan|printing}"],
  first="not dated", dsrc="COHEN2023 (2023, '5D consciousness')", cert="undated", reason="Dimension scale.",
  blind="precision decided by r3-P42's checks, not by reading")

# ===================================================== L04 =============================================================
for _name, _forms, _src in [
    ("pleiadians", ["pleiadian[s]"], ["BERENDT2025", "WAHBEHGLICK2026"]),
    ("arcturians", ["arcturian[s]"], ["BERENDT2025", "WAHBEHGLICK2026"]),
    ("sirians", ["sirian[s]"], ["BERENDT2025", "WAHBEHGLICK2026"]),
    ("lyrans", ["lyran[s]"], ["BERENDT2025"]),
]:
    T(_name, {"L04": "OPEN"}, _forms, ["a kind of star being named after a star or cluster, used by many channels"], [1],
      "Few collisions in titles.", "Count all (titles).", _src, first="by 1989",
      dsrc="BERENDT2025 cites Royal Holt and Priest 1989 for star-origin lore", cert="uncertain",
      reason="Open source name (r3-P46).")
T("angels (generic)", {"L04": "OPEN"}, ["angels", "the angels", "angelic realm[s]", "angelic beings"],
  ["messengers of God (R)", "an endearment (E)", "the baseball team and other names (Y)"], [1],
  "E/Y collisions.", "Count all (titles); " + PREC + ".", ["PROGRAMME"], reason="Open source name.")
T("council of nine", {"L04": "OPEN"}, ["council of nine", "the nine"],
  ["a collective source named by experiencers"], [1], "'The nine' is everyday (E); precision band.",
  "Count all (titles).", ["WAHBEHGLICK2026"], reason="Open collective source name.")

# ===================================================== L05 =============================================================
T("cabal", {"L05": "CR-A"}, ["cabal", "the cabal", "dark cabal"],
  ["a small group of plotters (E, from 1614)", "a hidden controlling group (conspiracy)"], [1, 2],
  "E: political journalism.", "Count all.", ["MW", "BARKUN2013", "AJC2024"], trope="yes (AJC2024)",
  reason="Names a hidden controlling group.")
T("elites", {"L05": "CR-A"}, ["the elite[s]", "global elite[s]", "ruling elite[s]", "the elitists"],
  ["a privileged group (E, sociology)", "athletes or forces of top rank (E: 'elite athletes')",
   "a hidden controlling group (conspiracy)"], [3],
  "E: 'elite athletes', 'elite forces'.", "Count the listed forms only; " + PREC + ".", ["BYFORD2011", "WARDVOAS2011"],
  trope="possible; not checked for this term", reason="Names a hidden controlling group.")
T("powers that be", {"L05": "CR-A"}, ["powers that be", "the powers that be"],
  ["those in authority (E idiom)", "a hidden controlling group (conspiracy)"], [1, 2], "E idiom.",
  "Count all; " + PREC + ".", ["BYFORD2011"], reason="Names a controlling group.")
T("shadow government", {"L05": "CR-A"}, ["shadow government", "secret government", "shadow governments"],
  ["the opposition's shadow cabinet (E, UK politics; 'shadow government')", "a hidden government (conspiracy)"], [2],
  "E: UK parliamentary usage.", "Count all; " + PREC + ".", ["BARKUN2013"], reason="Names a hidden controlling group.")
T("the controllers", {"L05": "CR-A"}, ["the controllers"],
  ["air-traffic or game controllers (E/Y)", "a hidden controlling group"], [2], "E/Y collisions.",
  "Count the definite plural only; " + PREC + ".", ["WARDVOAS2011"], reason="Names a hidden controlling group.",
  blind="precision decided by r3-P42's checks, not by reading")
T("globalists", {"L05": "CR-A"}, ["globalist[s]"],
  ["a supporter of globalisation (E, politics)", "a hidden controlling group (conspiracy)"], [1, 2], "E: policy talk.",
  "Count all.", ["MW", "AJC2024"], trope="yes (AJC2024)", reason="Names a controlling group.")
T("mainstream media", {"L05": "CR-B"}, ["mainstream media", "msm"],
  ["established news organisations (E)", "an institution said to control opinion"], [1, 2], "E: media studies.",
  "Count all.", ["BYFORD2011", "BUTTERKNIGHT2020"], reason="Names an institution as controlling.")
T("big pharma", {"L05": "CR-B"}, ["big pharma"], ["the pharmaceutical industry, pejoratively"], [1], "Few collisions.",
  "Count all.", ["MW", "BERES2023"], reason="Names an institution as controlling.", check="MW 'Big Pharma' 1994")
T("big tech", {"L05": "CR-B"}, ["big tech"], ["the largest technology firms, pejoratively"], [1], "Few collisions.",
  "Count all.", ["MW"], reason="Names an institution as controlling.", check="MW headword not fetched")
T("the establishment", {"L05": "CR-B"}, ["the establishment"],
  ["a business or venue (E)", "the dominant social group (E, politics)"], [2], "E: venue sense.",
  "Count the definite form; " + PREC + ".", ["MW"], reason="Names an institution as controlling.")
T("mind control", {"L05": "CR-C"}, ["mind control", "mind controlled", "mind controlling"],
  ["coercive persuasion (E, psychology)", "a covert programme of control (conspiracy)"], [1, 2], "E: psychology talk.",
  "Count all.", ["SENATE1977"], reason="Names a technology or programme of control.")
T("mkultra", {"L05": "CR-C"}, ["mkultra", "mk ultra"], ["the CIA programme documented in 1977"], [1], "Few collisions.",
  "Count all.", ["SENATE1977"], reason="Names a programme of control.")
T("chemtrails", {"L05": "CR-C"}, ["chemtrail[s]", "chem trail[s]"], ["aircraft trails said to be spraying"], [1],
  "Few collisions.", "Count all.", ["MW", "TINGLEY2017", "SHEARER2016", "CROCKFORD2021"],
  reason="Names a technology of control.", check="MW 'chemtrail' 1990")
T("geoengineering", {"L05": "CR-C"}, ["geoengineering", "geo engineering"],
  ["climate intervention research (E, science)", "covert weather control (conspiracy)"], [1, 2], "E: science news.",
  "Count all; " + PREC + ".", ["TINGLEY2017"], reason="Names a technology of control.")
T("5g", {"L05": "CR-C"}, ["5g"], ["the mobile network standard (E/Y: phone talk)", "a harmful technology (conspiracy)"],
  [2], "E/Y: phone and network talk dominates in general speech.", "Count all; " + PREC + ".", ["BRUNS2020"],
  reason="Names a technology of control.", blind="precision decided by r3-P42's checks, not by reading")
T("brainwashing", {"L05": "CR-C"}, ["brainwash", "brainwashed", "brainwashing"],
  ["coercive indoctrination (E, from 1950)"], [1], "E: figurative use.", "Count all.", ["MW", "EO"],
  reason="Names a technique of control.")
T("psyop", {"L05": "CR-C"}, ["psyop[s]", "psy op[s]"], ["psychological operations (military, 1965)", "any deception "
  "(conspiracy)"], [1, 2], "Few collisions.", "Count all.", ["MW"], reason="Names a technique of control.")
T("false flag", {"L05": "CR-C"}, ["false flag[s]"], ["a staged attack blamed on others"], [1], "Few collisions.",
  "Count all.", ["MW"], reason="Names a technique of control.", check="MW date 1569 dates sense 2, unclear which")
T("the matrix", {"L05": "CR-D"}, ["the matrix", "3d matrix"],
  ["a mathematical array (E)", "the 1999 film (Y)", "a false reality that holds people (conspiritual)"], [3],
  "E/Y: maths and the film.", "Count listed forms; " + PREC + ".", ["MW"], reason="Names an ontological control system.",
  check="dated through MW 'red pill' (from the 1999 film)", blind="precision decided by r3-P42's checks, not by reading")
T("loosh", {"L05": "CR-D"}, ["loosh"], ["emotional energy said to be harvested from humans"], [1], "Few collisions.",
  "Count all.", ["MONROE1985"], reason="Names an ontological control system.")
T("sheeple", {"L05": "CR-E"}, ["sheeple"], ["people said to follow without thought"], [1], "Few collisions.",
  "Count all.", ["MW"], reason="Describes the population as controlled.", check="MW 'sheeple' 1945")
T("dark forces", {"L05": "ADV-NEG"},
  ["dark forces", "forces of darkness", "dark entit{y|ies}", "negative entit{y|ies}", "dark beings", "negative beings",
   "negative aliens", "the dark ones"],
  ["sinister powers (E idiom; film talk)", "adversary beings or forces"], [2], "E/Y: films and games.",
  "Count all; " + PREC + ".", ["PARTRIDGE2004", "BERENDT2025"], reason="Adversary class, negative valence.",
  check="phrases written by the writer from the class; sources document malevolent beings, not these exact phrases")
T("demons", {"L05": "ADV-NEG"}, ["demon[s]", "demonic", "fallen angel[s]"],
  ["evil spirits (R)", "inner struggles (E; 'my demons')", "names in games and music (Y)"], [1], "E/Y collisions.",
  "Count all; " + PREC + ".", ["PARTRIDGE2004"], reason="Adversary class (Christian roots of malevolent ET lore).")
T("lucifer", {"L05": "ADV-NEG"}, ["lucifer", "luciferian[s]", "satanic", "satanist[s]", "satanism"],
  ["the fallen angel (R)", "a doctrinal-history term", "an accusation against a hidden group (conspiracy)"], [1, 3],
  "R: doctrinal talk.", "Count all; " + PREC + ".", ["PARTRIDGE2004"],
  trope="possible; et's condition applies; not checked for these terms", reason="Adversary class.")
T("orion group", {"L05": "BRIDGE"}, ["orion group", "orion empire"],
  ["a negative-polarity group of Law of One cosmology"], [1], "The constellation (E) is not matched (phrase only).",
  "BRIDGE: counted as cosmology by default; as bridge only within 20 tokens of a CR-A or CR-B term.",
  ["LAWOFONE", "BERENDT2025"], reason="Polarity cosmology (programme section 5).",
  check="phrase occurrence in the sessions not re-checked; BERENDT2025 names 'the Orions'")
T("negative polarity", {"L05": "BRIDGE"}, ["negative polarity", "positive polarity"],
  ["electrical polarity (E)", "Law of One polarity of service"], [2], "E: physics.",
  "BRIDGE rule as for 'orion group'.", ["LAWOFONE"], reason="Polarity cosmology.")
T("they / them (unanchored)", {}, ["they", "them"], ["any third-person plural referent (E)"], [1],
  "PROGRAMME section 5: an unanchored 'they' is mostly generic; in the claimed voice a 'they' for humanity's leaders "
  "is distancing deixis, not coded speech.", "excluded.", ["PROGRAMME"], kind="excluded", reason="Programme rule.")
T("the dark / the light (bare)", {}, ["the dark", "the light"],
  ["darkness or light (E)", "doctrinal light and dark (R)"], [1], "E and R dominate.", "excluded: not resolvable by form.",
  ["PROGRAMME"], kind="excluded", reason="Considered for BRIDGE; excluded.")
T("trope-carrier senses (class row)", {}, [], ["senses that parts of the literature document as carriers of the "
  "antisemitic world-conspiracy trope or the hidden-bloodline trope"], [1],
  "Not enumerated here.",
  "Class row only. No carrier term is listed in any public list. Windows next to such senses are never counted, totalled "
  "or shown by family in public (et's condition, programme section 5); their detection list is r3-P54's, written only "
  "after the owner's ethics act. Until then, counts of L05 and of the lists that read it (L02 adversarial pair, L08 base) "
  "cannot apply the window exclusion (see README, decision D1).", ["PROGRAMME", "AJC2024", "BARKUN2013"],
  kind="class row", reason="et's condition.")

# ===================================================== L06 =============================================================
T("shift in consciousness", {"L06": "SHIFT"},
  ["shift in consciousness", "shift of consciousness", "consciousness shift", "shift in human consciousness"],
  ["humanity's change of consciousness (conspirituality's second conviction)"], [1], "Few collisions.", "Count all.",
  ["WARDVOAS2011", "ASPREM2015"], reason="Ward and Voas's defining phrase.")
T("awakening (collective)", {"L06": "SHIFT"},
  ["spiritual awakening", "{collective|mass|global|planetary} awakening", "awakening of humanity", "humanity's awakening"],
  ["waking (E)", "a religious revival (R)", "a collective spiritual change (New Age)"], [3],
  "Bare 'awakening' excluded (E: 'rude awakening'); 'great awakening' context-assigned (see L01 rows).",
  "Count listed forms.", ["WARDVOAS2011", "TOLLE2005"], reason="Shift vocabulary.")
T("golden age (shift)", {"L06": "SHIFT"}, ["golden age", "the golden age"],
  ["a nostalgic peak (E; 'golden age of television')", "a coming age of happiness (New Age)"], [2],
  "E dominates in general speech.", "Count all; " + PREC + ".", ["DRINKWATER2023"], reason="Shift vocabulary.",
  blind="precision decided by r3-P42's checks, not by reading")
T("raise vibration", {"L06": "SHIFT", "L08": "RES-INNER"},
  ["{raise|raising|raised} {your|our|the|their|my} vibration[s]"],
  ["to raise one's spiritual frequency (New Age)"], [1], "Few collisions.",
  "Count all. In L08 it counts only inside adversary-bearing units (L08 base rule).", ["CROCKFORD2021"],
  reason="Shift vocabulary; inner-means resolution.")
T("higher consciousness", {"L06": "SHIFT"},
  ["higher consciousness", "{raise|raising} {the|our|your} consciousness"],
  ["a higher state of awareness (New Age)", "'consciousness raising' (E, 1970s politics)"], [1],
  "E: political consciousness-raising.", "Count listed forms; " + PREC + ".", ["WARDVOAS2011"],
  reason="Shift vocabulary.", check="phrases written by the writer from the class definition")

# ===================================================== L07 =============================================================
for _t, _forms, _cls, _sense, _src in [
    ("cia", ["cia", "central intelligence agency"], "INST-SEC", "the US intelligence agency", ["SENATE1977"]),
    ("fbi", ["fbi"], "INST-SEC", "the US federal police agency", ["BYFORD2011"]),
    ("nsa", ["nsa", "national security agency"], "INST-SEC", "the US signals-intelligence agency", ["BYFORD2011"]),
    ("pentagon", ["pentagon", "the pentagon", "department of defense"], "INST-SEC", "the US defence department",
     ["NYT2017", "DOD2022"]),
    ("nasa", ["nasa"], "INST-SPACE", "the US space agency", ["DEAN1998"]),
    ("united nations", ["united nations"], "INST-INTL", "the international organisation", ["CROCKFORD2021"]),
    ("world health organization", ["world health organi{z|s}ation"], "INST-INTL", "the UN health agency", ["PARMIGIANI2021"]),
    ("world economic forum", ["world economic forum", "wef"], "INST-INTL", "the Davos foundation", ["WEF2020"]),
    ("imf", ["imf", "international monetary fund"], "INST-INTL", "the international lender", ["BYFORD2011"]),
    ("world bank", ["world bank"], "INST-INTL", "the development bank", ["BYFORD2011"]),
    ("vatican", ["vatican", "the vatican", "catholic church"], "INST-RELIG", "the Catholic Church's seat and institution",
     ["BYFORD2011"]),
    ("named news outlets", ["cnn", "bbc", "fox news", "new york times"], "INST-MEDIA", "named news organisations",
     ["BYFORD2011"]),
    ("named corporations", ["pfizer", "moderna", "google", "facebook", "microsoft"], "INST-CORP",
     "named corporations", ["PARMIGIANI2021", "BYFORD2011"]),
]:
    T(_t, {"L07": _cls}, _forms, [_sense, "an actor in conspiracy narratives"], [1, 2],
      "Few collisions" + ("; E: 'google it' (verb) excluded" if _t == "named corporations" else ""),
      "Count all; description only (the four producers of programme r3-P51 cannot be told apart).", _src,
      excl=(["google it", "googled", "googling"] if _t == "named corporations" else []),
      reason="Names an institution (class from the literature on conspiracy rhetoric).",
      check="institution names are public facts; the source cited supports the class, not each name")
T("the government", {"L07": "INST-GOV"}, ["the government", "governments", "federal government"],
  ["any government (E)", "an actor in control narratives"], [1, 2], "E dominates.", "Count all; " + PREC + ".",
  ["BYFORD2011"], reason="Names a government.")
T("youtube (excluded from L07)", {}, ["youtube"], ["the platform (Y)"], [1], "Y: platform talk dominates on the platform.",
  "excluded from L07; used only as a gate word of L13.", ["SAVOLAINEN2022"], kind="gate-only",
  reason="Platform word.")
T("disclosure (institutional)", {"L07": "DISC-INST"}, ["disclosure"],
  ["financial, legal or medical disclosure (E)", "official release of information on unidentified phenomena",
   "a spiritual or consciousness-based disclosure"], [2],
  "E: 'full disclosure', 'non-disclosure'. A token whose window holds both a G-DISC-INST and a G-DISC-CONSC word is "
  "context-assigned: flagged, never counted.",
  "Count 'disclosure' only with a G-DISC-INST word within 10 tokens and no G-DISC-CONSC word.",
  ["ABC2001", "NYT2017", "DOD2022"], excl=["full disclosure", "non disclosure", "nondisclosure", "disclosure agreement"],
  gate="G-DISC-INST", kind="gated", reason="r4-P28 separates institutional from consciousness-based disclosure.")
T("disclosure (consciousness-based)", {"L07": "DISC-CONSC"}, ["disclosure"],
  ["financial, legal or medical disclosure (E)", "official release of information on unidentified phenomena",
   "a spiritual or consciousness-based disclosure"], [3],
  "E: 'full disclosure', 'non-disclosure'. Same context rule as the institutional class.",
  "Count 'disclosure' only with a G-DISC-CONSC word within 10 tokens and no G-DISC-INST word.",
  ["WAHBEHGLICK2026", "PROGRAMME"], excl=["full disclosure", "non disclosure", "nondisclosure", "disclosure agreement"],
  gate="G-DISC-CONSC", kind="gated", reason="r4-P28's second disclosure class.",
  check="class from the programme; no literature defines it")
T("declassified", {"L07": "DISC-INST"},
  ["declassified", "declassify", "declassification", "congressional hearing[s]", "senate hearing[s]"],
  ["release of classified records (E, government)"], [1], "E: history talk.", "Count all.", ["NYT2017", "DOD2022"],
  reason="Institutional disclosure vocabulary.")
T("vaccines", {"L07": "CONTEST-PH"},
  ["vaccine[s]", "vaccinated", "unvaccinated", "vaccination[s]", "vax", "vaxxed", "anti vax", "anti vaxxer[s]", "the jab",
   "mrna"],
  ["vaccination (E, public health)", "a contested measure in conspiritual talk"], [1, 2],
  "E: health news; 'jab' alone excluded (boxing).", "Count all; description only.",
  ["PARMIGIANI2021", "BERES2023"], reason="Names a public-health measure (contested content).")
T("pandemic", {"L07": "CONTEST-PH"},
  ["covid", "covid 19", "coronavirus", "pandemic", "lockdown[s]", "mask mandate[s]"],
  ["the COVID-19 pandemic and its measures (E)", "a contested event in conspiritual talk"], [1, 2],
  "E: health news; bare 'mask(s)' excluded (devotional and theatrical masks).", "Count all; description only.",
  ["PARMIGIANI2021", "BERES2023", "NAZAR2021"], reason="Names the pandemic (contested content).")
T("promised arrests", {"L07": "LEGAL", "L08": "RES-OUTSIDE"}, ["mass arrest[s]", "military tribunal[s]"],
  ["criminal procedure (E, news)", "promised punishment of a hidden group (conspiracy lore)"], [1, 2],
  "E: news.", "Count all. In L08 counted only inside adversary-bearing units (L08 base rule).", ["AMARASINGAM2020"],
  reason="den-soc's legal-risk rows; outside-agent resolution (r4-P29).",
  check="A&A 2020 supports the QAnon context; these exact words not checked")
T("criminal-law process", {"L07": "LEGAL"}, ["indictment[s]", "indicted", "treason"],
  ["criminal procedure (E, news)", "an accusation against named persons or groups"], [1, 2], "E: news.",
  "Count all; description only; never printed per person.", ["AMARASINGAM2020"], reason="den-soc's legal-risk rows.",
  check="A&A 2020 supports the QAnon context; these exact words not checked")
T("named-person proxy (pattern row)", {"L07": "PERSON-PROXY"}, [],
  ["a person named in speech"], [1], "Persons cannot be listed blind and are never listed.",
  "Pattern row: two or more consecutive capitalised tokens not sentence-initial, minus any span matched by L01 S14 or "
  "L04 names; a description only, never printed per person (programme r3-P51's model-free proxy).", ["PROGRAMME"],
  kind="class row", reason="Model-free named-actor proxy.")

# ===================================================== L08 =============================================================
T("inner-means resolution", {"L08": "RES-INNER"},
  ["{no|have no|has no} power over you", "{cannot|can't|can not} {harm|touch|hurt} you", "fear feeds them",
   "feed on {your|our} fear", "{do not|don't} give {them|it} your energy", "stay in your heart", "your sovereignty",
   "sovereign being[s]", "you are protected", "{light|love} dissolves", "transmute", "transmutation",
   "take back your power", "your inner power"],
  ["reassurance or resolution by the listener's inner state"], [1],
  "E: everyday reassurance ('stay in your heart').",
  "Counted only inside units that hold an L05 ADV-NEG, ADV-AMB or CR-A hit (the base); outside the base, not counted.",
  ["WARDVOAS2011", "ASPREM2015", "CROCKFORD2021"], reason="r4-P29: resolution by inner means (lexical proxy, recall bound).",
  check="phrases written by the writer from the class definition; sources document the optimism of the spiritual side")
T("outside-agent resolution", {"L08": "RES-OUTSIDE"},
  ["being removed", "{have|has|had} been removed", "removed from the planet", "taken off {the|this} planet",
   "off planet", "the light forces", "forces of light", "being arrested"],
  ["resolution by an outside agent (beings, forces, an alliance)"], [1],
  "E: 'being removed' is everyday.", "Counted only inside the base (as above).",
  ["WARDVOAS2011", "ASPREM2015", "AMARASINGAM2020"], reason="r4-P29: resolution by an outside agent.",
  check="phrases written by the writer from the class definition", blind="precision decided by r3-P42's checks, not by reading")

# ===================================================== L09 =============================================================
T("first-person plural", {"L09": "FP-PL"},
  ["we", "us", "our", "ours", "ourselves", "we're", "we've", "we'll", "we'd", "let's"],
  ["inclusive or exclusive 'we' (clusivity unresolved)", "editorial or royal 'we'", "'US' = United States after "
   "lowercasing (H)"], [1, 2],
  "H: 'the US', 'U.S.'; reported speech of others carries 'we' too.",
  "Count all except 'the us' and 'u s'; outside self-naming and address frames (units holding a frame are removed).",
  ["BIBER1999", "QUIRK1985", "LIWC2015", "REHBEIN2022", "PETRYK2016", "PETRYK2019"], excl=["the us", "u s"],
  reason="Numerator of ling's recording-level ratio (N10).")
T("first-person singular", {"L09": "FP-SG"},
  ["i", "me", "my", "mine", "myself", "i'm", "i've", "i'll", "i'd"],
  ["the speaker", "'mine' as a noun (E, 'gold mine')"], [1], "E: 'mine' noun.", "Count all except 'gold mine' forms.",
  ["BIBER1999", "QUIRK1985", "LIWC2015"], excl=["{gold|coal|a|the} mine"], reason="Denominator side of the ratio.")
T("self-naming frame", {"L09": "FRAME-SELFNAME"},
  ["{i am|we are|this is|my name is|we are known as|i am known as|we are called|i am called} <Capitalised name>"],
  ["a speaker naming the presented addresser"], [1], "Cased text needed; 'I am' is very common (E).",
  "Frame pattern on cased text: the phrase followed by a capitalised token that is not a pronoun; the unit is removed from "
  "the ratio.", ["PETRYK2016", "WOOFFITT2001"], kind="frame", reason="Programme: outside self-naming frames.")
T("address frame", {"L09": "FRAME-ADDRESS"},
  ["{we|i} greet you", "greetings", "{we|i} love you", "{we|i} bless you", "blessings", "{we|i} bid you", "{we|i} leave you",
   "farewell", "{we|i} thank you", "dear ones", "beloved ones", "beloveds", "my beloved[s]", "dearest ones",
   "until we speak again", "until next time"],
  ["greeting and leave-taking formulas"], [1], "E: everyday greetings.", "The unit holding a frame is removed from the ratio.",
  ["WOOFFITT2006", "PETRYK2019"], kind="frame", reason="Programme: outside address frames.",
  check="formulas written by the writer; sources document addresser presentation, not these exact formulas")

# ===================================================== L10 =============================================================
T("full trance (mode)", {"L10": "MODE-TRANCE"},
  ["full trance", "deep trance", "trance channel[s]", "trance channeling", "trance channelling", "trance channeler[s]",
   "trance state", "in trance", "unconscious channel[s]", "unconscious channeling", "unconscious channelling"],
  ["self-description of channelling without awareness"], [1], "E: 'trance' music genre (Y).", "Count listed forms.",
  ["WAHBEHMILLER", "KLIMO1987", "WAHBEH2020", "WAHBEH2019"], reason="Mode class (programme section 5).")
T("conscious or blended (mode)", {"L10": "MODE-CONSCIOUS"},
  ["conscious channel[s]", "conscious channeling", "conscious channelling", "conscious channeler[s]", "blended",
   "blending", "blend with", "light trance"],
  ["self-description of channelling with awareness"], [1],
  "E: 'blended' (cooking, families).", "Count listed forms; " + PREC + ".", ["HUGHES1991", "WAHBEHMILLER"],
  reason="Mode class.", check="'light trance' not confirmed as Klimo's label")
T("dictation (mode)", {"L10": "MODE-DICTATION"},
  ["automatic writing", "inner dictation", "dictation", "dictated", "scribe[s]", "scribed", "scribing"],
  ["receiving text by writing or dictation"], [1], "E: office dictation.", "Count all; " + PREC + ".",
  ["WAHBEHMILLER", "KLIMO1987", "WAPNICK1991"], reason="Mode class.")
T("relay (mode)", {"L10": "MODE-RELAY"},
  ["{they are|they're} {telling|showing} me", "{i am|i'm} being {told|shown}", "clairaudien{t|ce}", "clairaudiently",
   "clairvoyan{t|ce}", "clairvoyantly", "clairsentien{t|ce}", "telepath{y|ic|ically}"],
  ["reporting what a source conveys, in one's own voice"], [1], "E: 'they're telling me' in ordinary conversation.",
  "Count listed forms; " + PREC + ".", ["WAHBEHMILLER", "KLIMO1987", "WOOFFITT2001"], reason="Mode class.")
T("higher self or Source (mode)", {"L10": "MODE-HIGHERSELF"}, ["{my|your|our} higher self", "higher self"],
  ["a self-described source that is the speaker's own higher self"], [1], "Few collisions.", "Count all.",
  ["PROGRAMME"], reason="Mode class (programme section 5).", check="no dictionary or scholarly source dates the phrase")
T("received text read aloud (mode)", {"L10": "MODE-READALOUD"},
  ["{i|we} received {this|a|the} message", "{this|the} message {came|was received}", "{i'll|i will|let me} read {the|this} message",
   "the message {i|we} received"],
  ["reading aloud a text the creator says they received"], [1], "E: ordinary message talk.",
  "Count listed forms; feeds r3-P14's self-described attribution.", ["PROGRAMME"], reason="Mode class.",
  check="class from the programme; phrases written by the writer")
T("recitation of another receiver (mode)", {"L10": "MODE-RECITATION"},
  ["channel{ed|led} by", "channel{ed|led} through", "{received|transmitted} by"],
  ["reading a message received by another person"], [1], "E: 'received by' in any context.",
  "Count listed forms; " + PREC + ".", ["PROGRAMME", "WOOFFITT2001"], reason="Mode class.")
T("light language (mode)", {"L10": "MODE-LIGHTLANG"}, ["light language", "language of light"],
  ["vocalisation without recognisable words, self-described as light language"], [1], "Few collisions.", "Count all.",
  ["PARMIGIANI2025", "SAMARIN1972"], reason="Mode class; programme naming rule.")

# ===================================================== L11 =============================================================
T("this channel (creator as channel)", {"L11": "REF-CREATOR"}, ["this channel", "our channel"],
  ["the creator as the channel of a source", "the YouTube channel (Y, dominant on the platform)"], [1],
  "Y: platform sense dominates.", "Count only with no G-PLATFORM word within 10 tokens; " + PREC + ".",
  ["LAWOFONE", "TOMLINSON2019"], reason="Reference to the creator (r3-P55).", gate="G-PLATFORM",
  blind="precision decided by r3-P42's checks, not by reading", kind="counted-unless-gate")
T("this instrument", {"L11": "REF-CREATOR"},
  ["this instrument", "this vessel", "the one known as", "this messenger", "our messenger"],
  ["the medium referred to by the source (Law of One usage)", "a musical instrument or container (E)"], [1],
  "E: music and objects.", "Count all; " + PREC + ".", ["LAWOFONE"], reason="Reference to the creator.")
T("endorsement predicates", {"L11": "ENDORSE"},
  ["{her|his|their|this} work", "the work {she|he|they} {does|is doing|are doing|offers}",
   "support {her|him|them|this work|this channel}", "{her|his|their} offerings",
   "{her|his|their} {book|books|course|courses|sessions|readings|workshop|workshops|retreat|retreats}",
   "trust this channel", "{clear|pure} channel", "we chose this one", "we work through this one"],
  ["the source praising or recommending the creator's work or offers"], [1], "E: 'their work' in any context.",
  "Endorsement co-occurrence = a REF-CREATOR and an ENDORSE hit within 20 tokens in one unit (both on L11).",
  ["TOMLINSON2019", "HUA2022"], reason="r3-P55: endorsement at matched positions (lower bound).",
  check="phrases written by the writer from the class definition")

# ===================================================== L12 =============================================================
T("exchange idiom", {"L12": "IDIOM"},
  ["energy exchange", "exchange of energy", "sacred exchange", "love offering[s]", "pay what you {can|feel|are guided}",
   "pay what feels right", "sliding scale", "by donation", "donation based", "{your|any} contribution",
   "support {this|the|my|our} work", "pay it forward"],
  ["payment framed as exchange, gift or support"], [1], "E: 'pay it forward' idiom; 'contribution' in any context.",
  "Count all; a recall probe of LAB-A, never a precision claim.",
  ["CROCKFORD2022", "LAU2000", "CARRETTE2005", "BOWMAN1999", "HEELAS2008", "YORK2001", "CT1973", "HUA2022"],
  reason="r3-P56: the gentlest wording of payment.",
  check="no scholarly source uses 'energy exchange' or 'love offering' (searched); Crockford 2022 documents money as "
        "spiritual energy")
T("dissemination ask", {"L12": "DISSEM"},
  ["share this {message|video|with}", "please share", "share it with", "share with {others|anyone|those|your friends|your "
   "family|everyone}", "pass {it|this} on", "spread the {word|message}", "spread this message", "forward this",
   "send this to"],
  ["an ask to pass a message on"], [1], "E: 'share your thoughts' (comment ask) is not matched.", "Count listed forms.",
  ["BENNETT2003", "TURVINES2019"], excl=["share your {thoughts|experience|experiences|comments}"],
  reason="r3-P56: dissemination asks.")

# ===================================================== L13 =============================================================
for _t, _cls, _depth, _domains, _src in [
    ("messaging-app broadcast", "DEST-MSG", 2, ["t.me", "telegram.me", "chat.whatsapp.com", "whatsapp.com/channel",
                                                 "signal.group"], ["ROGERS2020"]),
    ("alternative video platforms", "DEST-ALTVID", 1, ["rumble.com", "bitchute.com", "odysee.com", "brighteon.com"],
     ["BALLARD2022", "ROGERS2020"]),
    ("membership and donation", "DEST-MEMB", 3, ["patreon.com", "ko-fi.com", "buymeacoffee.com", "paypal.me", "paypal.com",
                                                 "gofundme.com", "subscribestar.com", "locals.com"], ["HUA2022", "BALLARD2022"]),
    ("booking and courses", "DEST-SERVICE", 4, ["calendly.com", "acuityscheduling.com", "as.me", "setmore.com",
                                                "kajabi.com", "mykajabi.com", "teachable.com", "thinkific.com", "podia.com",
                                                "gumroad.com", "eventbrite.com"], ["HUA2022"]),
    ("merchandise and affiliate", "DEST-SHOP", 3, ["amazon.com", "amzn.to", "etsy.com", "teespring.com",
                                                   "creator-spring.com", "myshopify.com", "redbubble.com"],
     ["BALLARD2022", "HUA2022"]),
    ("other social platforms", "DEST-SOCIAL", 1, ["instagram.com", "facebook.com", "tiktok.com", "twitter.com", "x.com",
                                                  "threads.net"], ["ROGERS2020"]),
    ("newsletter and email", "DEST-EMAIL", 2, ["substack.com", "mailchi.mp", "list-manage.com", "convertkit.com",
                                               "beehiiv.com"], ["HUA2022"]),
    ("podcast platforms", "DEST-AUDIO", 1, ["open.spotify.com", "podcasts.apple.com"], ["HUA2022"]),
    ("link aggregators", "DEST-LINKHUB", 2, ["linktr.ee", "beacons.ai"], ["HUA2022"]),
]:
    T(_t, {"L13": _cls}, _domains, ["a link destination of this kind (page text)"], [1],
      "A link is a link, not a verdict (programme r3-P60).",
      "Match link domains in page text (description fields); funnel depth %d (writer's order: 1 follow elsewhere, 2 "
      "contact capture, 3 payment, 4 one-to-one service or paid teaching). Residual domains are OWNSITE (rule)." % _depth,
      _src, kind="domain", reason="r3-P60 destination class.",
      check="the source names the platform kind; individual domains and the depth order are the writer's classification")
T("platform moderation talk", {"L13": "SUPP-PLATFORM"},
  ["shadowban[s]", "shadowbanned", "shadow ban[s]", "shadow banned", "demonetized", "demonetised", "demonetization",
   "demonetisation", "community guidelines", "community guidelines strike", "copyright strike", "deplatformed",
   "deplatforming", "age restricted", "the algorithm", "unalive"],
  ["talk about a platform's moderation of the creator's content"], [1], "E: 'the algorithm' in any software talk.",
  "Count listed forms; " + PREC + ".", ["SAVOLAINEN2022", "ARE2022", "ROGERS2020", "STEEN2023", "MW"],
  reason="r3-P60 suppression talk, platform half.")
T("censored (context-assigned)", {"L13": "SUPP-FLAG"}, ["censored", "censorship", "censoring"],
  ["moderation by a platform", "suppression by a hidden actor", "censorship by a state (E)"], [1, 2],
  "Splits between the two suppression halves only by context.",
  "Context-assigned: flagged and reported as a flagged count, never counted in either half (programme r3-P41). A "
  "G-SUPP-PLATFORM word within 10 tokens is recorded beside the flag, for r3-P42's description only.",
  ["SAVOLAINEN2022", "BARKUN2013"], gate="G-SUPP-PLATFORM", kind="flagged", reason="r3-P41's context rule.")
T("hidden-actor suppression talk", {"L13": "SUPP-HIDDEN"},
  ["suppressed {knowledge|information|technology|technologies|truth|history}", "{they|they do} {don't|not} want you to know",
   "hidden from {us|you|humanity}", "kept from {us|you|humanity}", "cover up", "coverup", "forbidden knowledge",
   "kept secret"],
  ["talk of knowledge withheld by a hidden actor"], [1], "E: 'cover up' (make-up, blankets).", "Count listed forms; "
  + PREC + ".", ["BARKUN2013"], reason="r3-P60 suppression talk, hidden-actor half (stigmatized knowledge).",
  check="phrases written by the writer; Barkun's 'suppressed knowledge' seen only through secondary commentary")

# ===================================================== L14 =============================================================
for _t, _cls, _forms, _src, _twin in [
    ("urgency (commercial)", "URGENCY-C", ["limited time", "ends {tonight|today|soon}", "last chance", "don't miss",
                                           "hurry", "deadline", "countdown"], ["MATHUR2019", "CIALDINI1984"], False),
    ("urgency (devotional twin)", "URGENCY-D", ["now is the time", "the time is now", "time is running out",
                                                "this is the moment"], ["CIALDINI1984"], True),
    ("scarcity (commercial)", "SCARCITY-C", ["limited spots", "spots {left|remaining}", "seats left", "sold out",
                                             "limited {availability|seats|space}", "while supplies last", "almost full"],
     ["MATHUR2019", "CIALDINI1984"], False),
    ("scarcity (devotional twin)", "SCARCITY-D", ["for those who are ready", "not everyone is ready", "only a few {are|will}"],
     ["CIALDINI1984"], True),
    ("social proof (commercial)", "SOCIAL-C", ["testimonial[s]", "{thousands|hundreds} of {people|students|clients}",
                                               "five star[s]", "reviews"], ["MATHUR2019", "CIALDINI1984"], False),
    ("social proof (devotional twin)", "SOCIAL-D", ["many of you {have|are}", "so many of you", "many souls are"],
     ["CIALDINI1984"], True),
    ("authority", "AUTHORITY-C", ["certified", "certification", "accredited", "licensed", "years of experience",
                                  "as seen on", "best selling", "bestselling"], ["CIALDINI1984", "BOWMAN1999"], False),
    ("reciprocity (commercial)", "RECIP-C", ["free gift", "free {training|webinar|ebook|e book|guide|meditation|masterclass|"
                                             "class|session|download}", "bonus", "complimentary"],
     ["CIALDINI1984"], False),
    ("reciprocity (devotional twin)", "RECIP-D", ["a gift {for|to} you", "our gift to you", "we gift you"],
     ["CIALDINI1984"], True),
    ("commitment (commercial)", "COMMIT-C", ["sign up", "enroll", "enrol", "register {now|today|here}", "book {now|your}",
                                             "invest in yourself", "say yes to yourself"], ["CIALDINI1984"], False),
    ("commitment (devotional twin)", "COMMIT-D", ["make the choice", "set your intention", "choose {love|light}"],
     ["CIALDINI1984"], True),
    ("discount", "DISCOUNT-C", ["percent off", "% off", "discount", "coupon", "promo code", "use {the|my} code",
                                "early bird", "special offer"], ["HUA2022", "MATHUR2019"], False),
    ("guarantee", "GUARANTEE-C", ["money back", "money back guarantee", "risk free", "full refund"], ["CIALDINI1984"], False),
    ("unity (devotional)", "UNITY-D", ["{our|your} {soul|star|galactic} family", "one of us", "fellow starseeds"],
     ["CIALDINI2021"], True),
]:
    T(_t, {"L14": _cls}, _forms, ["a persuasion device of this family" + (" in a devotional form" if _twin else "")], [1],
      "E: everyday uses of each phrase.",
      "Count listed forms; each hit is coded priced if a PRICE hit sits in the same unit, unpriced otherwise; "
      "a pilot, an instrument for the comparison set only (programme r3-P61).", _src, reason="r3-P61 device family.",
      check="families from the sources; phrases written by the writer")
T("price cue", {"L14": "PRICE"},
  ["$ <number>", "<number> {dollars|euros|pounds|usd|eur|gbp}", "price", "priced", "pricing", "cost[s]", "fee[s]",
   "payment", "purchase", "checkout", "per month", "monthly membership"],
  ["a stated price or payment"], [1], "E: 'cost' in any context.", "Pattern and word cues; defines 'priced'.",
  ["HUA2022", "MATHUR2019"], kind="counted", reason="Priced-or-unpriced rule (r3-P61).",
  check="cues written by the writer")

# ===================================================== L15 =============================================================
for _y, _src, _what in [("1844", ["FESTINGER1956"], "the Millerite expectation (Festinger 1956 discusses the Millerites; "
                                                   "not re-checked); R: also a Baha'i founding year"),
                        ("1954", ["FESTINGER1956"], "the Seekers' expected flood of 21 December 1954"),
                        ("1987", ["HOOPES2011"], "the Harmonic Convergence, 16-17 August 1987")]:
    T(_y, {"L15": "YEAR-LIT"}, [_y], [_what, "the calendar year (E)"], [1], "E: any date talk.",
      "A literature target year: cue families count within 30 tokens of it.", _src, reason="Historical milieu target year.")
T("year roles from the frozen ledger (class row)", {"L15": "YEAR-LEDGER"}, [],
  ["passed target years of the seen creators' dated statements"], [1], "Not a list: corpus-derived.",
  "Class row: the passed prophesied years are read from the frozen ledger (deposit 1), by rule, by the counting step; "
  "they cannot be written blind. Control years are matched on anniversary demand by rule; the contested year is the "
  "lead's ruling (K10).", ["PROGRAMME"], kind="class row", reason="r3-P40's three classes of year.")
T("fulfilment framing", {"L15": "FULFIL"},
  ["it did happen", "it happened {energetically|on an energetic level|on a higher level|in the higher realms}",
   "came to pass", "{was|has been} fulfilled", "it already happened"],
  ["a passed target framed as fulfilled (Melton's spiritualization)"], [1],
  "Shares senses with the ledger's frozen 'energetic predicate' family (deposit 2), whose terms this writer has not seen.",
  "Count within 30 tokens of a target-year token; the programme's timing rule applies (energetic-level statement goes to "
  "the hedge entry if the target was open at upload, to this entry if it had passed).",
  ["MELTON1985", "DAWSON1999", "FESTINGER1956"], reason="r3-P40 cue family.",
  check="phrases written by the writer from the cited response categories")
T("deferral framing", {"L15": "DEFER"},
  ["{was|has been|got} {postponed|delayed|pushed back}", "not yet", "{still|yet} to come", "will still happen",
   "divine timing", "the date {moved|changed|shifted}", "{wasn't|was not} {the|its} time",
   "humanity {wasn't|was not} ready"],
  ["a passed target framed as deferred"], [1], "E: 'not yet' everywhere; the year window limits it.",
  "Count within 30 tokens of a target-year token.", ["DAWSON1999", "TUMMINIA2005", "KELLY2026"],
  reason="r3-P40 cue family.", check="phrases written by the writer")

# ===================================================== class rows ======================================================
T("unnamed source (residual rule)", {"L04": "UNNAMED"}, [], ["a source presented without a proper name"], [1], "",
  "Residual rule, not a list: a title with the title label's channelling marker and no OPEN or FRANCHISE name of L04 is "
  "UNNAMED (programme section 5: unnamed sources are a class of their own).", ["PROGRAMME"], kind="class row",
  reason="r3-P46 name class.")
T("single-channel names (class not written)", {}, [], ["a source name the record ties to one human channel"], [1], "",
  "Not written blind: whether a name is tied to one channel is a fact about the corpus's channels. The literature gives "
  "only historical ties (for example Seth and Jane Roberts, ROBERTS1972; Ra and L/L Research, LAWOFONE). The programme "
  "keeps any such list private; the lead decides whether a private list of historical ties is wanted (README D4).",
  ["PROGRAMME", "ROBERTS1972", "LAWOFONE"], kind="class row", reason="r3-P46 name class.")
T("own site (residual rule)", {"L13": "DEST-OWNSITE"}, [], ["any other linked domain"], [1], "",
  "Residual rule: a linked domain not on any DEST class is OWNSITE; funnel depth undetermined.", ["PROGRAMME"],
  kind="class row", reason="r3-P60 destination class.")
for _fam in ["time-hedge", "probability doctrine", "collective-choice conditional", "outcome-booster",
             "energetic predicate", "prevention or obstruction"]:
    T("ledger qualifier family: " + _fam + " (fixed in deposit 2)", {}, [], ["see deposit 2"], [1],
      "Possible collisions with L06, L08 and L15 cannot be checked by this writer (the coder is private and unread).",
      "Fixed elsewhere: emic's qualifier family, coded by the ledger's rule coder (code/rule_coder.py, SHA-256 "
      "4fe41740...5aef71, deposit 2). r3-P38 / r4-P24 count with these frozen families; no new list is written. The "
      "collision check against them is a step for the counting agent, who may read the coder (README D2).",
      ["PROGRAMME"], kind="fixed elsewhere", reason="r3-P38 / r4-P24 lists were hashed with the ledger (ruling 11).")
for _fld in ["date refusal flag (D)", "conditional flag (C)", "contact class (et's five strata)", "deixis typing (ling)"]:
    T("ledger field: " + _fld + " (fixed in deposit 2)", {}, [], ["see deposit 2"], [1], "",
      "Fixed elsewhere: rule-based field of the frozen ledger (deposit 2, code/rule_coder.py); r4-P23 uses it as cue "
      "strata with no member-written list. Not rewritten.", ["PROGRAMME"], kind="fixed elsewhere",
      reason="Ledger fields are fixed.")
