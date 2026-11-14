#!/usr/bin/env python3
"""Say what kind of podcast interview each listed interview episode is.

An interview show's episode with a channeler is one of several things, and its title does not say which
(an episode called "Bashar's Channeled Message to Humanity" turned out to be a conversation with Darryl
Anka in which nothing is channeled):

  live channeling      the entity speaks during the episode
  unclear              the transcript has many marks of an entity addressing humans, but nothing that
                       settles it: a conversation with channeled passages, or one about channeling
  conversation         the person talks as themselves, about their work
  commentary or clip   the person is not a guest: the host comments, or plays an excerpt
  not classified       no transcript is held and the show notes do not say

What counts as evidence, and the label always says which was used:
  transcript   the text of the episode (the publisher's own transcript, or speech-to-text made here).
               "Live channeling" needs the entity's own signature: Bashar's greeting ("this day of your
               time"), or the entity naming itself or being greeted by name. Marks of an entity's voice
               ("your planet", "as you call it", "dear ones") alone make an episode "unclear", because a
               channeler describing their work uses the same words. A sentence such as "I am going to
               channel" is not used: in the transcripts read it was always part of a story.
  show notes   the episode's description in the feed says the session is channeled live, in those words
  title        only for "commentary or clip" (short, and the person's own name is not in it). A title
               never makes an episode "live channeling".
  a reading    someone, or a model given the whole transcript, read the episode and said what it is
               (<root>/sources/interview_readings.jsonl: video_id, kind, reader, evidence). A reading
               outranks the phrase rules above, which only look for marks.

Only episodes of kind "live channeling" are queued by default (select_episodes.py --interview-types);
everything stays listed with its kind.

Reads   the listed interview episodes, the texts held for them, and (--notes) the shows' feeds again
Writes  <root>/sources/interview_types.jsonl    one line per episode: kind, basis, which marks were found
        No transcript text and no show notes are kept: marks are named, not quoted.

    python3 pipeline/interview_types.py              # from the texts already held
    python3 pipeline/interview_types.py --notes      # also read each show's feed for its episode notes
"""
from __future__ import annotations

import argparse
import collections
import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, append_jsonl, ensure_outside_git, latest_by_key, layout, read_csv,  # noqa: E402
                    read_jsonl, utc_now)
from feeds import FetchError, episode_key, get_bytes  # noqa: E402
from find_feeds import INDEX, fold  # noqa: E402

KINDS = ("live channeling", "unclear", "conversation", "commentary or clip", "not classified")
EXTRA_TARGETS = ET_ROOT / "sources" / "extra_targets.csv"
# An entity's own signature. Bashar opens every session with the same greeting, and nobody else uses it.
SIGNATURES = {"the entity's own greeting": r"\bday of your time\b"}
# The marks of an entity addressing humans. Any one of them is ordinary speech; many of them are not.
ENTITY_VOICE = [
    r"\byour (?:planet|world|species|civilization|society|dimension|timeline|collective consciousness)\b",
    r"\b(?:as|what) you (?:call|would call|say|term)\b", r"\bof your time\b", r"\bin your (?:terms|language|reality|years)\b",
    r"\bdear ones?\b", r"\bbeloved ones?\b", r"\bwe (?:perceive|observe|sense) (?:that|you|your)\b",
    r"\bwe are here (?:to|with|for)\b", r"\bthe guides (?:say|are saying)\b", r"\bwe (?:greet|bless|honou?r) you\b",
    r"\bwe are (?:the|a) (?:collective|council|group|ones who)\b", r"\byou humans\b", r"\bhumans? (?:of|on) (?:earth|your planet)\b",
]
# What show notes say when a session is channeled in the episode itself. "Channeled message" or
# "channeling session" alone is not enough: both stand in many a guest's standing description.
NOTES_SAY = {"live channeling": r"\blive[- ](?:trance[- ])?channel(?:ing|led|ed)\b",
             "channels live": r"\bchannel(?:s|ed|led|ing) (?:[a-z]+ ){0,3}live\b",
             "goes into trance": r"\b(?:goes|go|went|enters?) into (?:a |the )?(?:deep )?trance\b",
             "live transmission": r"\blive (?:transmission|light language|reading from)\b"}
TITLE_HINT = re.compile(r"\bchannel(?:s|ed|led|ing)?\b|\bspeaks\b|\bmessage from\b|\btrance\b", re.I)
VOICE_MIN, VOICE_PER_1000 = 6, 0.4     # "unclear" from this many marks, and this many per thousand words


def entity_names():
    """{person_id: [lower-case names of what the person channels]} from the index and the alias list."""
    out = collections.defaultdict(list)
    if INDEX.exists():
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            for name in (channel.get("summary") or {}).get("entities_seen") or []:
                if isinstance(name, str) and len(name) >= 4:
                    out[channel["person"]].append(fold(name))
    for row in read_csv(EXTRA_TARGETS) if EXTRA_TARGETS.exists() else []:
        for alias in (row.get("aliases") or "").split("|"):
            if len(alias.strip()) >= 4 and fold(alias.strip()) != fold(row.get("name") or ""):
                out[row["person_id"]].append(fold(alias.strip()))
    return {person: sorted(set(names)) for person, names in out.items()}


def from_transcript(text: str, entities=()):
    """(kind, marks found). `text` is the whole transcript of one episode."""
    low = fold(text).replace("’", "'")
    words = max(1, len(low.split()))
    marks = [name for name, pattern in SIGNATURES.items() if re.search(pattern, low)]
    names = "|".join(re.escape(n) for n in entities if n)
    if names:
        if re.search(rf"\b(?:i am|this is) (?:{names})\b", low):
            marks.append("the entity names itself")
        if re.search(rf"\b(?:welcome|hello|greetings|goodbye|farewell),? (?:{names})\b", low):
            marks.append("the entity is greeted by name")
    if marks:
        return "live channeling", sorted(set(marks))
    voice = sum(len(re.findall(pattern, low)) for pattern in ENTITY_VOICE)
    if voice >= VOICE_MIN and 1000 * voice / words >= VOICE_PER_1000:
        return "unclear", [f"{voice} marks of an entity's voice, no signature"]
    return "conversation", []


# Words around "live channeling" that make it an advertisement or a line of the guest's standing
# description, not a statement about this episode ("attend Gaia's live channeling event", "classes,
# retreats and live channeling experiences").
NOT_THIS_EPISODE_BEFORE = re.compile(r"\b(?:attend|register|tickets?|join (?:us|me)|upcoming|book (?:a|your)|sign up|offers?|through|retreats?,? and)\b[^.!?]{0,60}$")
NOT_THIS_EPISODE_AFTER = re.compile(r"^\s*(?:events?|experiences?|conference|workshops?|class(?:es)?|retreats?|series|sessions? (?:at|on|every|with))\b")


def from_notes(notes: str):
    """Names of the marks in an episode's description that say the session is channeled in the episode."""
    low = fold(re.sub(r"<[^>]+>", " ", html.unescape(notes or "")))
    found = set()
    for name, pattern in NOTES_SAY.items():
        for match in re.finditer(pattern, low):
            if NOT_THIS_EPISODE_BEFORE.search(low[max(0, match.start() - 90):match.start()]) \
                    or NOT_THIS_EPISODE_AFTER.search(low[match.end():match.end() + 40]):
                continue
            found.add(name)
    return sorted(found)


def from_title(title: str, person_names, seconds):
    """'commentary or clip' for a short episode whose title carries only what the person channels, never
    their own name; otherwise nothing: a title does not settle what kind of interview it is."""
    low = fold(title or "")
    named = any(re.search(rf"\b{re.escape(fold(name))}\b", low) for name in person_names if name)
    if not named and seconds and seconds < 25 * 60:
        return "commentary or clip"
    return ""


def notes_by_episode(feed_xml: bytes, host: str):
    """{item id: description text} for one feed. Only used in memory: nothing of it is saved."""
    from common import item_id
    out = {}
    try:
        root = ET.fromstring(feed_xml)
    except ET.ParseError:
        return out
    for node in root.iter("item"):
        guid = (node.findtext("guid") or "").strip()
        enclosure = node.find("enclosure")
        url = (enclosure.get("url") if enclosure is not None else "") or ""
        text = " ".join(filter(None, [node.findtext("description"),
                                      node.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}summary"),
                                      node.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")]))
        out[item_id("pod", host, episode_key(guid, url))] = text
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--notes", action="store_true", help="read each interview show's feed again for its episode notes")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    args = ap.parse_args()
    paths = layout(ensure_outside_git(args.root))
    from select_episodes import collect
    from fetch_feeds import read_registry, REGISTRY
    rows, _, _ = collect(paths, {"relation": "host"})
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    rows = [r for r in rows if r["relation"] == "host" and (not only or r["channel_dir"] in only)]
    entities = entity_names()
    names = {}
    for row in read_csv(EXTRA_TARGETS) if EXTRA_TARGETS.exists() else []:
        names[row["person_id"]] = [row.get("name") or ""]
    if INDEX.exists():
        for channel in json.loads(INDEX.read_text(encoding="utf-8"))["channels"]:
            names.setdefault(channel["person"], []).append(channel.get("person_name") or "")
    notes = {}
    if args.notes:
        feeds = {r["feed_key"]: r for r in read_registry(REGISTRY, {"verified", "name-match"}) if r["relation"] == "host"}
        for key in sorted({r["feed_key"] for r in rows}):
            feed = feeds.get(key)
            if not feed:
                continue
            time.sleep(1.0)
            try:
                _, _, body = get_bytes(feed["feed_url"], timeout=90, max_bytes=120_000_000)
                notes.update(notes_by_episode(body, feed["person_id"]))
            except FetchError as err:
                print(f"notes not read for {feed['person_id']}: {err}", file=sys.stderr)
    pub = latest_by_key(read_jsonl(paths.pubtext / "publisher_text_manifest.jsonl"))
    asr_lines = read_jsonl(paths.transcripts / "transcripts_manifest.jsonl")
    for part in sorted(paths.transcripts.glob("transcripts_manifest.part-*.jsonl")):
        asr_lines += read_jsonl(part)
    asr = latest_by_key(asr_lines)
    out = paths.sources / "interview_types.jsonl"
    before = latest_by_key(read_jsonl(out))
    readings = {k: v for k, v in latest_by_key(read_jsonl(paths.sources / "interview_readings.jsonl")).items()
                if v.get("kind") in KINDS}
    counts = collections.Counter()
    for row in rows:
        ident, person = row["video_id"], row["channel_dir"]
        text_file, source = None, ""
        if pub.get(ident, {}).get("status") == "ok":
            text_file, source = paths.pubtext / pub[ident]["channel_dir"] / f"{ident}.txt", "the publisher's transcript"
        elif asr.get(ident, {}).get("status") == "ok":
            text_file, source = paths.transcripts / asr[ident]["channel_dir"] / f"{ident}.txt", "speech-to-text made here"
        seconds = float(row["duration_s"]) if row.get("duration_s") else None
        hint = "its title speaks of channeling" if TITLE_HINT.search(row.get("title") or "") else "its title does not speak of channeling"
        clip = from_title(row.get("title") or "", names.get(person, []), seconds)
        if text_file is not None and text_file.exists():
            kind, marks = from_transcript(text_file.read_text(encoding="utf-8", errors="replace"), entities.get(person, ()))
            if kind == "conversation" and clip:
                kind = clip
            basis = f"transcript ({source})"
        else:
            said = from_notes(notes.get(ident, ""))
            if said:
                kind, basis, marks = "live channeling", "show notes", said
            elif clip:
                kind, basis, marks = clip, "title and length", []
            else:
                kind, basis, marks = "not classified", "no transcript yet; " + hint, []
        if ident in readings and text_file is not None:
            reading = readings[ident]
            kind, basis = reading["kind"], f"read in full by {reading.get('reader') or 'a reader'}"
            marks = [str(reading.get("evidence") or "")[:200]] if reading.get("evidence") else []
        counts[(kind, basis.split(" (")[0].split(";")[0])] += 1
        rec = {"video_id": ident, "person_id": person, "feed_key": row["feed_key"], "kind": kind, "basis": basis, "marks": marks}
        old = before.get(ident) or {}
        if {k: old.get(k) for k in ("kind", "basis", "marks")} != {k: rec[k] for k in ("kind", "basis", "marks")}:
            append_jsonl(out, {**rec, "at": utc_now()})
    print(f"{len(rows)} interview episodes: " + ", ".join(f"{n} {kind} ({basis})" for (kind, basis), n in sorted(counts.items(), key=lambda kv: -kv[1]))
          + f" -> {out}")


if __name__ == "__main__":
    main()
