#!/usr/bin/env python3
"""Merge youtube_index/group_{A,B,C}.json into /home/claude/etc_site/data/youtube_index.json.

Compiler only: no new facts. Adds canonical person ids, integer counts parsed from the
provider/notes text, a four-value status, and two derived rollups. Prints counts only.
"""
import json, re, sys, collections

SRC = "/home/claude/research_notes/ET channelers directory and timeline/youtube_index/"
OUT = "/home/claude/etc_site/data/youtube_index.json"
OBSERVED = "2026-10-23"

# ---- person name (as used in the group files) -> canonical person id (CANONICAL_IDS.md) ----
PERSON_IDS = {
    "Darryl Anka": "darryl-anka", "Athina Król": "athina-krol", "Tyler Ellison": "tyler-ellison",
    "Lyssa Royal Holt": "lyssa-royal-holt", "Barbara Marciniak": "barbara-marciniak",
    "Barbara Hand Clow": "barbara-hand-clow", "Lee Carroll": "lee-carroll", "Sheldan Nidle": "sheldan-nidle",
    "Blossom Goodchild": "blossom-goodchild", "Suzanne Ward": "suzanne-ward", "Mike Quinsey": "mike-quinsey",
    "Wendy Kennedy": "wendy-kennedy", "Patricia Cori": "patricia-cori", "Tom Kenyon": "tom-kenyon",
    "Laura Knight-Jadczyk": "laura-knight-jadczyk", "Alex Collier": "alex-collier",
    "Shaun Swanson": "shaun-swanson", "Andrew Bayuk": "andrew-bayuk", "Daniel Scranton": "daniel-scranton",
    "Pamela Aaralyn": "pamela-aaralyn", "Jamye Price": "jamye-price", "Aaron Abke": "aaron-abke",
    "Billy Meier": "billy-meier", "Robert Shapiro": "robert-shapiro", "Nancy Lieder": "nancy-lieder",
    "Judy Satori": "judy-satori", "Steve Nobel": "steve-nobel", "Elizabeth April": "elizabeth-april",
    "Sam the Illusionist": "sam-the-illusionist",
    # group B
    "Riz Mirza": "riz-mirza", "Aurora Ray": "aurora-ray", "Grace Solaris": "grace-solaris",
    "Aluna Ash": "aluna-ash", "Lorie Ladd": "lorie-ladd", "Megan Rose": "megan-rose",
    "Elena Danaan": "elena-danaan", "Gosia Duszak (Cosmic Agency)": "cosmic-agency-gosia",
    "Ismael Perez": "ismael-perez", "Micheila Sheldan": "micheila-sheldan", "Debbie Solaris": "debbie-solaris",
    "Gigi Young": "gigi-young", "Lauren Galey": "lauren-galey", "Tracey Milne": "tracey-milne",
    "Erin Lyons": "erin-lyons", "Toni Ghazi": "toni-ghazi", "Ashley Cunningham": "ashley-cunningham",
    "Wieteke Koolhof": "wieteke-koolhof", "Nora Herold": "nora-herold", "Rob Gauthier": "rob-gauthier",
    "Louise Kay": "louise-kay", "Anrita Melchizedek": "anrita-melchizedek", "Suzanne Lie": "suzanne-lie-ph-d",
    "Brad Johnson": "brad-johnson", "Magenta Pixie": "magenta-pixie", "Ivan Teller": "ivan-teller",
    "Tolec": "tolec", "Kayleigh O'Keefe": "kayleigh-o-keefe", "Leslie Muller": "leslie-muller",
    "Pleiadian Council Whispers": "pleiadian-council-whispers",
    "Ashtar Command: Lower Decks": "ashtar-command-lower-decks",
    # group C
    'Susan Leland ("Ashtar On The Road")': "susan-leland", "Sharon Stewart": "sharon-stewart",
    "Erena Velazquez": "erena-velazquez", "James McConnell (Ancient Awakenings)": "james-mcconnell",
    "Neva Gabriel (Brazil)": "neva-gabriel", "Elizabeth Trutwin": "elizabeth-trutwin",
    "Pavlina Klemm": "pavlina-klemm", "Elsa Farrús Rusiñol": "elsa-farrus-rusinol",
    "Juan Manuel Giordano (Argentina; Tameana)": "juan-manuel-giordano", "Edson Tozzi (Brazil)": "edson-tozzi",
    "Mônica de Medeiros": "monica-de-medeiros", "チャネラー純子 Channeler Junko": "channeler-junko",
    "Krista Raisa": "krista-raisa", "Rachel Chamness (Sound Waves Heal)": "rachel-chamness",
    "Sarah Evans (Into the Blue Channeling)": "sarah-evans", "Paul Hamden": "paul-hamden",
    "Paul White Gold Eagle (Prime Disclosure)": "paul-white-gold-eagle",
    "Fernanda and Flavia (Lightworkers613)": "fernanda-and-flavia",
    '"Channeling Arcturians" (Erica of the Sassani)': "channeling-arcturians",
    "LiquidLightCodes": "liquidlightcodes", "Arcturus SIGNAL": "arcturus-signal",
    "Yafi Channeling": "yafi-channeling", "Jordan Younger (The Balanced Blonde)": "jordan-younger",
    "Ivo A. Benda (Universe People / Vesmírní lidé)": "ivo-a-benda", "Corey Goode": "corey-goode",
    "JZ Knight / Ramtha": "j-z-knight", "Seth material / Jane Roberts": "jane-roberts",
}
# Names with no entry in CANONICAL_IDS.md. A slug is assigned with the file's own rule
# (lowercase ASCII, hyphens) and flagged in id_mapping so the parent can add them or null them.
NEW_IDS = {
    "L/L Research": {"id": "l-l-research", "related_canonical_ids": ["carla-l-rueckert", "don-elkins", "jim-mccarty", "gary-l-bean-and-austin-bridges"]},
    "Aetherius Society": {"id": "aetherius-society", "related_canonical_ids": ["george-king"], "related_entity_ids": ["aetherius"]},
    "Ashtar Command Crew": {"id": "ashtar-command-crew", "related_canonical_ids": ["james-mcconnell"], "related_entity_ids": ["ashtar"]},
    "Abraham-Hicks (Esther Hicks)": {"id": "esther-hicks", "related_canonical_ids": [], "related_entity_ids": ["abraham"]},
    "Paul Selig": {"id": "paul-selig", "related_canonical_ids": [], "related_entity_ids": ["the-guides-selig"]},
}

# ---- video `entity` text -> canonical entity id (CANONICAL_IDS.md), only where obvious ----
ENTITY_IDS = {
    "Ryokah": "ryokah", "Val Nek": "val-nek", "Federation of Light": "federation-of-light",
    "Sasha": "germane-sasha", "Germane": "germane-sasha", "Hamón": "germane-sasha",
    "9D Pleiadian Collective": "pleiadian-collective-9d", "The 9D Arcturian Council": "arcturian-council",
    "Galactic Federation": "galactic-federation", "Galactic Federation High Council": "galactic-federation",
    "Yahyel": "yahyel", "Ishuwa": "ishuwa", "Red Eagle": "red-eagle",
    "Pleiadians": "pleiadians", "The Pleiadians": "pleiadians", "The Pleiadian Collective": "pleiadians",
    "Neela and Luka (Pleiadian twins)": "pleiadians", "Lyran ETs": "lyrans",
    "Andromeda Council": "andromedans", "Ashtar": "ashtar", "Bashar": "bashar",
}
ENTITY_NAMES = {  # display names from CANONICAL_IDS.md
    "ryokah": "Ryok / Ryokah (Tyler Ellison)", "val-nek": "Val Nek (Megan Rose)",
    "federation-of-light": "The Federation of Light (Blossom Goodchild)",
    "germane-sasha": "Germane / Sasha / Hamón (Lyssa Royal)",
    "pleiadian-collective-9d": "9th Dimensional Pleiadian Collective (\"The Ps\", Wendy Kennedy)",
    "arcturian-council": "9D Arcturian Council (Daniel Scranton)",
    "galactic-federation": "Galactic Federation (of Light / of Worlds)", "yahyel": "Yahyel / Shalanaya",
    "ishuwa": "Ishuwa of the Yahyel (Shaun Swanson)", "red-eagle": "Red Eagle (Riz Mirza)",
    "pleiadians": "Pleiadians (Marciniak lineage and general)", "lyrans": "Lyrans / Vega",
    "andromedans": "Andromedans (Alex Collier; Andromeda Council/Tolec)",
    "ashtar": "Ashtar / Ashtar Command (Ashtar Sheran; Ashtar Galactic Command)", "bashar": "Bashar",
}

NUM_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*([KkMm])?")


def parse_count(text):
    """'5.41K subscribers' -> 5410; '229,000 subscribers' -> 229000; '8 subscribers' -> 8; None -> None."""
    if not text:
        return None
    m = NUM_RE.search(text)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    mult = {"k": 1_000, "m": 1_000_000}.get((m.group(2) or "").lower(), 1)
    return int(round(num * mult))


META_KEYS = ("title", "handle", "channel_id", "url", "subscriber_count_text", "video_count_text")
# notes phrases meaning "a YouTube presence seems to exist but was never identified" -> not_found
PRESENCE_HINTS = ("youtube presence exists", "lists a youtube channel", "not resolved", "unresolved",
                  "handle unverified", "was to be located")


def derive_status(rec):
    """Return (status, note). ok/not_found pass through; credits_exhausted splits by metadata."""
    orig = rec["status"]
    ch = rec.get("channel") if isinstance(rec.get("channel"), dict) else {}
    has_meta = any(ch.get(k) for k in META_KEYS)
    if orig == "ok":
        return "ok", None
    if orig == "not_found":
        return "not_found", "Search run on 2026-10-23 found no channel (see sources)."
    if orig == "no_youtube":
        return "no_youtube", None
    if orig != "credits_exhausted":
        raise ValueError("unexpected status %r for %s" % (orig, rec["person"]))
    if has_meta:
        return "metadata-only", ("Firecrawl credits exhausted on 2026-10-23 before the channel could be fetched; "
                                 "channel fields are copied from the research notes and the video list was not read "
                                 "(any videos listed are the ones the notes record).")
    note_text = " ".join(filter(None, [ch.get("note"), rec.get("note"), (rec.get("sources") or [""])[0]])).lower()
    if rec.get("videos") or rec.get("secondary_channels") or any(h in note_text for h in PRESENCE_HINTS):
        return "not_found", ("A YouTube presence is indicated in the research notes but no channel handle/ID was "
                             "identified, and the planned search was not run on 2026-10-23 (credits exhausted).")
    return "no_youtube", ("No YouTube channel recorded in the research notes; the planned search was not run on "
                          "2026-10-23 (credits exhausted), so absence is unverified.")


def main():
    groups = {}
    for g in ("A", "B", "C"):
        with open(SRC + "group_%s.json" % g, encoding="utf-8") as fh:
            groups[g] = json.load(fh)
        assert isinstance(groups[g], list), g

    channels, seen_ids, unmapped = [], {}, []
    entity_rollup_c = collections.OrderedDict()
    entity_rollup_raw = collections.OrderedDict()
    per_person = collections.OrderedDict()
    top_mismatch = 0

    for g, recs in groups.items():
        for rec in recs:
            name = rec["person"]
            if name in PERSON_IDS:
                pid, new_id = PERSON_IDS[name], False
            elif name in NEW_IDS:
                pid, new_id = NEW_IDS[name]["id"], True
                unmapped.append({"person_name": name, "assigned_id": pid, "group": g,
                                 "note": "not in CANONICAL_IDS.md; slug assigned by its rule — add to CANONICAL_IDS.md/people.json or set to null",
                                 **{k: v for k, v in NEW_IDS[name].items() if k != "id"}})
            else:
                raise KeyError("no id mapping for person %r" % name)
            if pid in seen_ids:
                raise ValueError("duplicate person id %s (%s / %s)" % (pid, seen_ids[pid], name))
            seen_ids[pid] = name

            status, status_note = derive_status(rec)
            ch = rec.get("channel")
            videos = rec.get("videos") or []
            summary = rec.get("summary") or {}
            subs_text = ch.get("subscriber_count_text") if isinstance(ch, dict) else None
            vids_text = ch.get("video_count_text") if isinstance(ch, dict) else None

            entry = collections.OrderedDict()
            entry["person"] = pid
            entry["person_name"] = name
            entry["person_id_is_new"] = new_id
            entry["role"] = rec.get("role")
            entry["status"] = status
            entry["original_status"] = rec["status"]
            entry["status_note"] = status_note
            entry["subscribers"] = parse_count(subs_text)
            entry["video_count"] = parse_count(vids_text)
            entry["channel"] = ch
            entry["secondary_channels"] = rec.get("secondary_channels") or []
            entry["videos"] = videos
            entry["summary"] = summary
            if rec.get("note") is not None:
                entry["note"] = rec["note"]
            entry["sources"] = rec.get("sources") or []
            entry["group_file"] = "group_%s.json" % g
            channels.append(entry)

            # ---- rollups ----
            n_ch = sum(1 for v in videos if v.get("is_channeling") is True)
            # top channeling videos: by parsed view count (stable sort keeps file order for ties),
            # then channeling videos that have an id but no view count, in file order; max 8
            ch_with_id = [v for v in videos if v.get("is_channeling") is True and v.get("video_id")]
            with_views = [v for v in ch_with_id if parse_count(v.get("view_count_text")) is not None]
            no_views = [v for v in ch_with_id if parse_count(v.get("view_count_text")) is None]
            ranked = sorted(with_views, key=lambda v: -parse_count(v["view_count_text"])) + no_views
            top_ids = [v["video_id"] for v in ranked[:8]]
            if top_ids != (summary.get("top_channeling_video_ids") or []):
                top_mismatch += 1
            ents_seen = list(summary.get("entities_seen") or [])
            ents_canon = sorted({ENTITY_IDS[e] for e in ents_seen if e in ENTITY_IDS})
            per_person[pid] = collections.OrderedDict([
                ("channeling_videos", n_ch),
                ("recent_videos_read", len(videos)),
                ("entities_seen", ents_seen),
                ("entities_canonical", ents_canon),
                ("top_video_ids", top_ids),
                ("status", status),
            ])
            for v in videos:
                e = v.get("entity")
                if not e:
                    continue
                is_ch = v.get("is_channeling") is True
                if e in ENTITY_IDS:
                    eid = ENTITY_IDS[e]
                    slot = entity_rollup_c.setdefault(eid, collections.OrderedDict([
                        ("name", ENTITY_NAMES[eid]), ("videos", 0), ("channeling_videos", 0),
                        ("people", []), ("raw_names", [])]))
                else:
                    slot = entity_rollup_raw.setdefault(e, collections.OrderedDict([
                        ("videos", 0), ("channeling_videos", 0), ("people", [])]))
                slot["videos"] += 1
                slot["channeling_videos"] += 1 if is_ch else 0
                if pid not in slot["people"]:
                    slot["people"].append(pid)
                if "raw_names" in slot and e not in slot["raw_names"]:
                    slot["raw_names"].append(e)

    # order rollups by video count desc, then name
    entity_rollup_c = collections.OrderedDict(sorted(entity_rollup_c.items(), key=lambda kv: (-kv[1]["videos"], kv[0])))
    entity_rollup_raw = collections.OrderedDict(sorted(entity_rollup_raw.items(), key=lambda kv: (-kv[1]["videos"], kv[0])))

    status_counts = collections.Counter(c["status"] for c in channels)
    orig_counts = collections.Counter(c["original_status"] for c in channels)
    total_videos = sum(len(c["videos"]) for c in channels)
    channeling_videos = sum(1 for c in channels for v in c["videos"] if v.get("is_channeling") is True)
    videos_with_entity = sum(1 for c in channels for v in c["videos"] if v.get("entity"))

    out = collections.OrderedDict()
    out["observed"] = OBSERVED
    out["coverage"] = collections.OrderedDict([
        ("fully_indexed", status_counts.get("ok", 0)),
        ("metadata_only", status_counts.get("metadata-only", 0)),
        ("no_youtube", status_counts.get("no_youtube", 0)),
        ("not_found", status_counts.get("not_found", 0)),
        ("total_channels", len(channels)),
        ("total_videos", total_videos),
        ("channeling_videos", channeling_videos),
        ("videos_with_named_entity", videos_with_entity),
        ("by_original_status", dict(orig_counts)),
    ])
    out["status_rules"] = collections.OrderedDict([
        ("ok", "group-file status 'ok': channel page and up to 30 recent videos read via the youtube-com provider on 2026-10-23."),
        ("metadata-only", "group-file status 'credits_exhausted' where the research notes supplied channel metadata (title/handle/ID/URL or counts); the recent-video list was not read. Any videos present are ones the notes recorded."),
        ("not_found", "either a search was run and found nothing (Grace Solaris), or the notes indicate some YouTube presence but no channel was identified and the planned search never ran (credits exhausted). See each entry's status_note."),
        ("no_youtube", "no YouTube channel is recorded anywhere in the research notes and the planned search never ran (credits exhausted) — absence is unverified. See status_note."),
        ("original_status", "the group file's own status is preserved in every entry as original_status."),
    ])
    out["channels"] = channels
    out["entity_rollup"] = collections.OrderedDict([
        ("note", "Built from every video whose `entity` field is set (channeling or not). Names mapped to CANONICAL_IDS.md entity ids only where the mapping is obvious; everything else stays verbatim under `raw`. `raw_names` lists the exact strings folded into each canonical id."),
        ("canonical", entity_rollup_c),
        ("raw", entity_rollup_raw),
    ])
    out["per_person_rollup"] = per_person
    out["id_mapping"] = collections.OrderedDict([
        ("unmapped_to_canonical", unmapped),
        ("name_to_id", collections.OrderedDict((c["person_name"], c["person"]) for c in channels)),
    ])
    out["sources"] = [
        {"url": SRC + "group_A.json", "title": "YouTube index group A (agent output)", "accessed": OBSERVED},
        {"url": SRC + "group_B.json", "title": "YouTube index group B (agent output)", "accessed": OBSERVED},
        {"url": SRC + "group_C.json", "title": "YouTube index group C (agent output)", "accessed": OBSERVED},
        {"url": SRC + "SCHEMA.md", "title": "YouTube index per-group schema", "accessed": OBSERVED},
    ]

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    print("channels by status:", dict(status_counts))
    print("channels by original status:", dict(orig_counts))
    print("total channels:", len(channels), "| total videos:", total_videos, "| channeling videos:", channeling_videos,
          "| videos with entity:", videos_with_entity)
    print("entities in rollup: canonical=%d raw=%d total=%d" % (len(entity_rollup_c), len(entity_rollup_raw), len(entity_rollup_c) + len(entity_rollup_raw)))
    print("per_person_rollup entries:", len(per_person))
    print("subscribers parsed:", sum(1 for c in channels if c["subscribers"] is not None),
          "| video_count parsed:", sum(1 for c in channels if c["video_count"] is not None))
    print("top_video_ids differing from group summaries:", top_mismatch)
    print("unmapped names (new ids assigned):", [u["person_name"] for u in unmapped])
    print("status by person for the no-metadata credits_exhausted cases:",
          {c["person"]: c["status"] for c in channels if c["original_status"] == "credits_exhausted" and c["status"] != "metadata-only"})


if __name__ == "__main__":
    main()
