#!/usr/bin/env python3
"""Search the stored texts and titles for a theme: a lexicon kept as data (pipeline/themes/<theme>.json), its
hits per person with their dates, markers and target windows, a tier's priority queue, a blinded sample for
coders and the score of their labels.

The lexicon: include patterns, each with a topic, and exclude patterns for the false senses, each scoped to
include ids or topics (see "format" in the theme file). A sentence (or a title) is a hit when an include matches
it and no exclude in that include's scope voids the match. Sentences come from prediction_timeline's splitters
(a blog's reader comments cut). Four kinds of text stay apart in every count and table: texts from the source
("source"), speech-to-text made here ("made"), YouTube captions ("captions", from the catalogue's captions_path,
read when present) and titles ("title"). Near-copies are collapsed per person and kind by
prediction_timeline.copy_groups (on the letters and digits of each sentence, so a repeat that differs only in
punctuation is a copy), so a repeat counts once ("distinct"). In scope all a twin's title that repeats its video's
title (same letters and digits) is read once, as the video's.

Per hit: person, item, kind, via_twin (the YouTube video id when the item is a podcast episode or page that twins
a video: in a tier, a queued one), published and date said (prediction_timeline.date_said; --listing and
--dates-from give approximate upload dates; an undated item whose text opens with a calendar date takes that
date), the sentence and the sentences before and after (each cut to 30 words; the sentence around its matched
terms), topics, the includes and the terms matched, the future, prediction and hedge words of prediction_timeline,
whether its rules pass would keep the sentence as a candidate (candidate(); a title's " | " is read as a comma), a
warning marker (the theme's advice words: prepare, stock up, candles ...), the time expression and target window
(prediction_timeline.time_window) and its copy group. A window is a past reference, not a target, when
prediction_timeline's screens say so (a dated header, "since" or "back in" a year, "ago", a past verb governing the
date), when it is the date the text opens with, or when it ends before the year said (or the person's undated
floor).

    python3 -I pipeline/theme_search.py search --root ~/et-channelers-private --theme blackouts --scope all \\
        --dates-from jobs/queue_newest50.csv --publish-counts
    python3 -I pipeline/theme_search.py search --root ~/et-channelers-private --theme blackouts \\
        --scope newest10 --queue jobs/queue_newest10.csv --publish-counts
    python3 -I pipeline/theme_search.py sample --root ~/et-channelers-private --theme blackouts --from all \\
        --per-person 10 --ensure-twins newest10 --out <root>/analysis/themes/blackouts/sample_<date>
    python3 -I pipeline/theme_search.py score --out <sample folder> labels_a.jsonl labels_b.jsonl
    python3 -I pipeline/theme_search.py measure --root ~/et-channelers-private --theme blackouts --scope all \\
        --labels <labels.csv> [--coded <sample folder>] [--write-lexicon]
    python3 -I pipeline/theme_search.py leaks --root ~/et-channelers-private --theme blackouts \\
        [--check pipeline/tests/test_theme_search.py]

Scopes: --scope all reads every catalogue item (its texts and its title). A tier: --queue <tier queue CSV>
(repeatable) with --scope <name>; an item is in the tier when its item_id is a queued video or its twin_of is
one, and the queued videos' titles (from the queue, so also those not yet in the catalogue) are the tier's
titles. A queued video's own captions or speech-to-text count as soon as the catalogue lists them, so the same
command works when the owner's downloads arrive.

Writes, inside the private folder only (it quotes the texts):
    <root>/analysis/themes/<theme>/<scope>/<person>.jsonl   every hit
    <root>/analysis/themes/<theme>/<scope>/<person>.md      by date said, then by target; quotes cut to 30 words
    <root>/analysis/themes/<theme>/<scope>/counts.csv       per person and kind (no text); person "all" totals
    <root>/analysis/themes/<theme>/<scope>/titles.csv       tiers: the queued videos whose title is a hit
    <root>/jobs/queue_<theme>_<scope>.csv                   tiers (and scope all with --priority-from): the
                                                            videos whose title is a hit or whose text here (a
                                                            twin's, or their own) has one, as the tier queue's
                                                            own lines (header and rows copied byte for byte, in
                                                            its order), for download_audio.py /
                                                            fetch_captions.py --queue on the owner's computer
--publish-counts also copies counts.csv to plan/theme_<theme>.csv (scope all) or plan/theme_<theme>_<scope>.csv:
counts only (no text, no item ids, no titles); it is refused with --only or --kinds (partial counts). In counts.csv
the marker, window and topic columns count distinct hits, and the "all" row of every kind is written even when it
is all zeros (captions not stored yet reads 0, not missing); the tier columns (videos queued, with a twin, with a
source text, a transcript made here or captions here, titles matching, with a text hit, in the priority queue)
are per person and sit on the person's title row.

sample: a seeded draw of up to --per-person distinct hits (per person and kind) from each person of one or more
scopes (--from, repeatable), shuffled; sample.jsonl holds uid, sentence, context and matched terms only (no
person, item, title or date; the person's names inside a unit show as [name]: the words of the id, the name,
channel title and handle in plan/channel_inventory.csv, the queues' entity column and --aliases), key.jsonl the
rest, strata.json the distinct hits per person, meta.json the seed and what was added. --ensure-twins <scope> adds
every hit of that scope that came through a twin and the draw missed; --ensure-scope <scope> every hit of that
scope (its titles too). score: two coders' labels (JSONL: uid, on_topic yes/no/unclear, type one of
prediction_pilot.TYPES when on topic, topic optional) -> score.json: agreement and Cohen's kappa, the on-topic
share (Wilson interval; weighted by person with prediction_pilot.weighted_interval) and the share of on-topic hits
both coders call prediction-like (warnings included) or warnings, by person, kind, topic and include. measure:
labels of earlier reading (CSV: item_id, kind, idx, label on/edge/off; or key, a sentence hash, with no item) against
the lexicon now, kinds apart: per include and kind its precision, per exclude what it removed, and how many
on-topic labels the lexicon finds (a hash-only "on" label that is no hit now counts as missed); --coded <sample
folder> adds the two coders' labels of a sample per include and kind; with --write-lexicon into the theme file
(counts only). leaks: the theme file's free text (examples, keeps, notes, why, history, description, format and the
words in its patterns) and any --check file's quoted strings against the stored texts and titles: shared runs of 5
words (4 with 3 content words for titles) and stored item or video ids, printed as counts and ids only; it exits 1
when a run of 7 or more words, a run covering most of a short string, or an id is found.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime
import hashlib
import io
import json
import random
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, atomic_write_text, ensure_outside_git, read_csv, read_jsonl,  # noqa: E402
                    utc_now, write_csv)
import prediction_pilot as pp  # noqa: E402
import prediction_timeline as pt  # noqa: E402

THEMES = ET_ROOT / "pipeline" / "themes"
FLAGS = re.I | re.S
KINDS = ("source", "made", "captions", "title")
QUOTE_WORDS = pt.QUOTE_WORDS
# a pattern that must be tried sentence by sentence: an anchor, or a look-ahead over .* (as pipeline/keywords.py)
SLOW = re.compile(r"(?<![\\\[])\^|(?<![\\\[])\$|\\[AZ]|\(\?[=!][^)]*\.[*+{]")
# advice to prepare (not "warning" or "supplies" alone: in titles those are topic words, "Food Supplies")
DEFAULT_ADVICE = (r"\b(?:prepar\w*|be ready|get ready|stock(?:ing)? up|stockpil\w*|candles?|flashlights?|"
                  r"batter(?:y|ies)|generators?|emergency (?:kits?|supplies|plans?)|precautions?|beware)\b")
TITLE_KINDS = {"title", "title_youtube", "title_other", "title_yt"}
ON, OFF = {"yes", "y", "on", "true", "1"}, {"no", "n", "off", "false", "0"}
# a calendar date at the top of a text ("Transcript October 5 2021 ..."): the date of the text, not a target
LEAD_DATE = re.compile(rf"^\W*(?:\S+\s+){{0,4}}?(?P<date>{pt._DATE})")
MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov",
                                      "dec"), 1)}
TITLE_SEPARATORS = re.compile(r"\s+[|∞•]\s+")


# ---------------------------------------------------------------------------------------------------- the theme
def norm(text, kind="source"):
    """The unit the patterns read: NFKC, one space between words; titles read '_' as a space (saved YouTube titles
    put '_' for ':', which would hide a word edge)."""
    text = unicodedata.normalize("NFKC", text or "")
    if kind == "title":
        text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def key_form(sentence):
    """The sentence's letters and digits, lower case, one space between: what sentence_key hashes and what the copy
    groups compare (prediction_timeline.shingles deletes punctuation without a space, so "Event_Coming" and
    "Event: Coming" would not share their five-word runs)."""
    return re.sub(r"[^a-z0-9]+", " ", (sentence or "").lower()).strip()


def sentence_key(sentence):
    """A hash of the sentence's letters and digits: the same sentence in two items has the same key (no text)."""
    return hashlib.sha1(key_form(sentence).encode()).hexdigest()[:16]


class Theme:
    """A theme file: include patterns (id, topic, group, kinds, screen, terms) and exclude patterns (scope, mode,
    kinds). evaluate() gives, for one unit, the includes kept and those voided by an exclude."""

    def __init__(self, data, source=""):
        self.source = str(source)
        self.data = data
        self.name = data.get("theme") or Path(source).stem or "theme"
        self.description = data.get("description", "")
        self.generic = set(data.get("generic_topics") or [])
        self.advice = re.compile((data.get("markers") or {}).get("advice") or DEFAULT_ADVICE, FLAGS)
        self.includes, self.excludes = [], []
        for i, e in enumerate(data.get("include") or []):
            if not e.get("pattern") or e.get("active") is False:
                continue
            self.includes.append({
                "id": str(e.get("id") or f"include_{i}"), "topic": str(e.get("topic") or ""),
                "group": str(e.get("group") or "strong"), "kinds": set(e["kinds"]) if e.get("kinds") else None,
                "rx": re.compile(e["pattern"], FLAGS), "slow": bool(SLOW.search(e["pattern"])),
                "screen": re.compile(e["screen"], FLAGS) if e.get("screen") else None,
                "terms": re.compile(e["terms"], FLAGS) if e.get("terms") else None})
        for i, e in enumerate(data.get("exclude") or []):
            if not e.get("pattern") or e.get("active") is False:
                continue
            scope = e.get("scope")
            scope = None if scope in (None, "", "all", "*") else set([scope] if isinstance(scope, str) else scope)
            self.excludes.append({
                "id": str(e.get("id") or f"exclude_{i}"), "rx": re.compile(e["pattern"], FLAGS), "scope": scope,
                "mode": "overlap" if str(e.get("mode") or "unit").lower() in {"overlap", "match", "span"} else "unit",
                "kinds": set(e["kinds"]) if e.get("kinds") else None})
        ids = {x["id"] for x in self.includes} | {x["topic"] for x in self.includes}
        for x in self.excludes:
            if x["scope"] and not x["scope"] <= ids:
                raise ValueError(f"exclude {x['id']}: scope names no include: {sorted(x['scope'] - ids)}")
        # the screen: a sentence that it does not match cannot be a hit. The plain includes join it as they are, a
        # slow one by its screen (which every match of it contains); a slow include without one opens it to all
        parts = [x["screen"].pattern if x["screen"] else x["rx"].pattern for x in self.includes
                 if x["screen"] or not x["slow"]]
        opened = any(x["slow"] and not x["screen"] for x in self.includes)
        self.screen = None if opened or not parts else re.compile("|".join(f"(?:{p})" for p in parts), FLAGS)
        self.topic_of = {x["id"]: x["topic"] for x in self.includes}

    def topics(self):
        seen = list(self.data.get("topics") or [])
        return seen + [t for t in dict.fromkeys(x["topic"] for x in self.includes) if t and t not in seen]

    def candidate(self, unit):
        return self.screen is None or bool(self.screen.search(unit))

    def evaluate(self, unit, kind):
        """(kept, voided): kept {include id: [(start, end)]} of the includes that match the unit and that no
        exclude in their scope voids (all their matches void); voided {include id: [exclude ids]}. A look-ahead
        include's match is empty: it counts as the whole unit for an overlap exclude."""
        kept, voided, found = {}, {}, None
        for inc in self.includes:
            if inc["kinds"] and kind not in inc["kinds"]:
                continue
            if inc["screen"] is not None and not inc["screen"].search(unit):
                continue
            spans = [(m.start(), m.end()) if m.end() > m.start() else (0, len(unit)) for m in inc["rx"].finditer(unit)]
            if not spans:
                continue
            if found is None:
                found = [(x, [(m.start(), m.end()) for m in x["rx"].finditer(unit)]) for x in self.excludes
                         if not x["kinds"] or kind in x["kinds"]]
            ok, by = [], set()
            for s, e in spans:
                void = [x["id"] for x, xs in found
                        if xs and (x["scope"] is None or inc["id"] in x["scope"] or inc["topic"] in x["scope"])
                        and (x["mode"] == "unit" or any(a < e and s < b for a, b in xs))]
                (by.update(void) if void else ok.append((s, e)))
            if ok:
                kept[inc["id"]] = ok
            else:
                voided[inc["id"]] = sorted(by)
        return kept, voided

    def term_matches(self, unit, kept):
        """[(start, text)] of the matched terms in order of appearance (an include with a terms pattern reports what
        that pattern finds; a look-ahead include without one, its whole unit)."""
        out = []
        for inc in self.includes:
            if inc["id"] not in kept:
                continue
            if inc["terms"] is not None:
                out += [(m.start(), m.group(0)) for m in inc["terms"].finditer(unit) if m.group(0).strip()]
            else:
                out += [(s, unit[s:e]) for s, e in kept[inc["id"]] if e > s]
        return sorted(out)

    def terms(self, unit, kept):
        """The matched terms, lower case, at most six words each, in order of appearance, at most eight."""
        seen = []
        for _, t in self.term_matches(unit, kept):
            t = " ".join(t.lower().split()[:6])
            if t not in seen:
                seen.append(t)
        return seen[:8]

    def hit_topics(self, kept):
        topics = {self.topic_of[i] for i in kept if self.topic_of[i]}
        specific = topics - self.generic
        return sorted(specific or topics)


def theme_path(name):
    p = Path(name)
    return p if p.suffix == ".json" or p.exists() else THEMES / f"{name}.json"


def load_theme(name):
    path = theme_path(name)
    return Theme(json.loads(path.read_text(encoding="utf-8")), path)


# ---------------------------------------------------------------------------------------------------- reading
def item_texts(root, row, kinds):
    """[(kind, [(offset, sentence)])] for one catalogue row: prediction_timeline.read_item_texts (speech-to-text made
    here, texts from the source with a blog's comments cut) and the captions, kinds apart."""
    out = []
    if (row.get("asr_path") or row.get("publisher_text_path")) and kinds & {"made", "source"}:
        out = [(k, s) for k, s in pt.read_item_texts(root, row) if k in kinds]
    cap = row.get("captions_path") or ""
    if "captions" in kinds and cap and (root / cap).exists():
        out.append(("captions", pt.sentences_of_text((root / cap).read_text(encoding="utf-8", errors="replace"))))
    return out


def text_kinds(root, row):
    """The kinds of text stored for one catalogue row: source, made (speech-to-text made here), captions."""
    out = set()
    if row.get("publisher_text_path") and (root / row["publisher_text_path"]).exists():
        out.add("source")
    asr = row.get("asr_path") or ""
    if asr and ((root / asr).exists() or (root / Path(asr).with_suffix(".json")).exists()):
        out.add("made")
    if row.get("captions_path") and (root / row["captions_path"]).exists():
        out.add("captions")
    return out


def cut(text, limit=QUOTE_WORDS, at=None, tail=False):
    """At most `limit` words: covering the char positions `at` (one, or a list: from the first, as many as fit),
    else the first (or with tail, the last) ones."""
    words = (text or "").split()
    if len(words) <= limit:
        return " ".join(words)
    if at is not None and at != []:
        idx = sorted(len(text[:p].split()) for p in (at if isinstance(at, (list, tuple, set)) else [at]))
        lo = idx[0]
        hi = max(i for i in idx if i - lo < limit)
        start = max(0, min(lo - (limit - (hi - lo + 1)) // 3, len(words) - limit))
    else:
        start = len(words) - limit if tail else 0
    return ("… " if start else "") + " ".join(words[start:start + limit]) + (" …" if start + limit < len(words) else "")


def lead_date(sentence):
    """(iso date, (start, end)) of a full calendar date (day, month and year) among the first five words of a text's
    first sentence, not governed by a preposition ("We met on June 4, 2019" is not a header), or ("", None)."""
    m = LEAD_DATE.search(sentence or "")
    if not m:
        return "", None
    before = sentence[:m.start("date")].split()
    if before and before[-1].lower().strip(",") in {"on", "in", "since", "by", "until", "till", "before", "after", "from",
                                                     "of", "to", "at", "during", "around", "about", "till", "for"}:
        return "", None
    d = m.group("date")
    iso = re.search(r"\b((?:19|20)\d\d)-(\d\d)-(\d\d)\b", d)
    if iso:
        return "-".join(iso.groups()), m.span("date")
    year = re.search(r"(?:19|20)\d\d", d).group(0)
    mon = re.search(r"[a-z]{3}", d.lower())
    month = MONTHS.get(mon.group(0)) if mon else None
    day = re.search(r"(?<!\d)(\d{1,2})(?:st|nd|rd|th)?(?!\d)", re.sub(r"(?:19|20)\d\d", " ", d))
    if not (month and day and 1 <= int(day.group(1)) <= 31):
        return "", None
    return f"{year}-{month:02d}-{int(day.group(1)):02d}", m.span("date")


def past_reason(unit, found, year, floor, lead_span=None):
    """Why the window of the time expression found is a past reference, not a target ("" when it is a target):
    prediction_timeline's screens (a dated header, "since" or "back in" a date, "ago", a past verb governing the
    date), the date the text opens with, or a window that ends before the year said (or the undated floor)."""
    if not found:
        return ""
    label, m = found
    window = pt.time_window(unit, year, found)
    if not window:
        return ""
    if lead_span and m.start() < lead_span[1] and lead_span[0] < m.end():
        return "date of the text"
    if not pt.future_dated(m, year):
        if pt.overlaps(pt.DATED_HEADER, unit, m):
            return "dated header"
        if pt.overlaps(pt.PAST_ANCHOR, unit, m) or pt.back_anchor(unit, m) or pt.AGO.match(unit, m.end()):
            return "past anchor"
        if pt.past_verb_governs(unit, label, m):
            return "past verb"
    base = year or floor
    if base and window[1] is not None and window[1] < base:
        return "before the year said"
    return ""


def approx_date(d):
    d = (d or "").strip()
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if re.fullmatch(r"\d{8}", d) else d


def load_queue(paths, root):
    """(rows, fields) of one or more tier queue CSVs; all must have the same columns."""
    rows, fields = [], None
    for p in paths or []:
        p = Path(p)
        p = p if p.is_absolute() or p.exists() else Path(root) / p
        with open(p, newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if fields is None:
                fields = reader.fieldnames
            elif reader.fieldnames != fields:
                raise SystemExit(f"{p}: its columns differ from the first queue's")
            rows += list(reader)
    seen, out = set(), []
    for r in rows:
        if r.get("video_id") and r["video_id"] not in seen:
            seen.add(r["video_id"])
            out.append(r)
    return out, fields


def make_hit(theme, scope, row, kind, idx, sentences, said, basis, floor, via_twin, unit, kept, lead_span=None):
    """One hit's record (the full sentence stays in memory as _full, for the copy groups, and is not written).
    lead_span: where the text's opening date is in this sentence (its first), when the date said comes from it."""
    raw = sentences[idx][1] if sentences else unit
    year = pt.year_of(said)
    at = [s for s, _ in theme.term_matches(unit, kept)]
    found = pt.time_expression(unit)
    window = pt.time_window(unit, year, found)
    lo, hi, rule, expr = window if window else (None, None, "", "")
    reason = past_reason(unit, found, year, floor, lead_span)
    # a title's " | " parts are its phrases, not a page's link list (prediction_timeline.FURNITURE)
    cand = pt.candidate(TITLE_SEPARATORS.sub(", ", unit) if kind == "title" else unit, year, floor)
    groups = {i["group"] for i in theme.includes if i["id"] in kept}
    rec = {"theme": theme.name, "scope": scope, "person_id": row["person_id"], "item_id": row["item_id"], "kind": kind,
           "lane": row.get("lane", ""), "via_twin": via_twin, "idx": idx,
           "offset_s": sentences[idx][0] if sentences else None, "title": cut(norm(row.get("title", ""), "title")),
           "published": row.get("published", ""), "date_said": said, "date_basis": basis,
           "sentence": cut(unit, at=at), "sentence_words": len(unit.split()),
           "context_before": cut(norm(sentences[idx - 1][1]), tail=True) if sentences and idx > 0 else "",
           "context_after": cut(norm(sentences[idx + 1][1])) if sentences and idx + 1 < len(sentences) else "",
           "key": sentence_key(unit), "includes": [i["id"] for i in theme.includes if i["id"] in kept],
           "topics": theme.hit_topics(kept), "terms": theme.terms(unit, kept),
           "group": "strong" if "strong" in groups else "weak",
           "future": sorted({m.group(0).lower() for m in pt.FUTURE.finditer(unit)}),
           "predict": sorted({m.group(0).lower() for m in pt.PREDICT.finditer(unit)}),
           "hedged": bool(pt.HEDGE.search(unit)),
           "warning": sorted({m.group(0).lower() for m in theme.advice.finditer(unit)}),
           "prediction_candidate": bool(cand),
           "time_expr": expr, "time_rule": rule, "window_lo": lo, "window_hi": hi, "past_window": bool(reason),
           "past_reason": reason, "_full": raw}
    for k in ("listing_rank", "upload_date_approx"):
        if row.get(k) is not None and kind == "title" and k in row:
            rec[k] = row[k]
    return rec


def targets(rec):
    """The target years of a hit: its window, unless that is a past reference."""
    if rec.get("past_window"):
        return []
    return [y for y in (rec.get("window_lo"), rec.get("window_hi")) if y is not None]


def collapse(rows):
    """prediction_timeline.copy_groups on the full sentences, per person and kind (kinds stay apart)."""
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["person_id"], r["kind"])].append(r)
    for group in by.values():
        proxies = [{"sentence": key_form(r["_full"]), "date_said": r["date_said"], "item_id": r["item_id"],
                    "offset_s": r["offset_s"], "_i": i} for i, r in enumerate(group)]
        pt.copy_groups(proxies)
        for p in proxies:
            group[p["_i"]]["copy_group"], group[p["_i"]]["copy"] = p["copy_group"], p["copy"]
    return rows


# ---------------------------------------------------------------------------------------------------- outputs
def person_md(theme, scope, person, rows, read):
    times = collections.Counter((r["kind"], r["copy_group"]) for r in rows)
    shown = sorted((r for r in rows if not r["copy"]),
                   key=lambda r: (r["date_said"] or "9999", (targets(r) or [9999])[0], r["kind"], r["item_id"], r["idx"]))
    reads = ", ".join(f"{read[k]} {k}" for k in KINDS if read.get(k))
    lines = [f"# Theme {theme.name}: {person}, scope {scope}", "",
             f"Made {utc_now()} by theme_search.py from {Path(theme.source).name}. Read: {reads or 'nothing'}. "
             f"{len(rows)} hits, {len(shown)} once near-copies are collapsed (each shown once, with how often it was "
             "said), by date said and then by target. Hits are matches of the lexicon, not findings: a coder or a "
             "model pass still has to read each one. Private: quotes are from the texts (at most 30 words).", "",
             "| Said | Kind | Item | Times | Topics | Terms | Marks | Target | Quote |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in shown:
        ts = targets(r)
        target = "" if not ts else (f"{ts[0]}" if len(set(ts)) == 1 else f"{min(ts)}–{max(ts)}")
        if r["window_lo"] is None and r["window_hi"] is not None and not r["past_window"]:
            target = f"…–{r['window_hi']}"
        marks = ", ".join(m for m, on in (("future", r["future"] or r["predict"]), ("warning", r["warning"]),
                                          ("hedged", r["hedged"]), ("candidate", r["prediction_candidate"]),
                                          (f"past date ({r.get('past_reason') or 'before the year said'})",
                                           r["past_window"])) if on)
        when = f" @{int(r['offset_s'] // 60)}:{int(r['offset_s'] % 60):02d}" if r.get("offset_s") is not None else ""
        twin = f" (twin of {r['via_twin']})" if r["via_twin"] else ""
        lines.append(f"| {r['date_said'] or '?'} | {r['kind']} | {r['item_id']}{when}{twin} | "
                     f"{times[(r['kind'], r['copy_group'])]} | {', '.join(r['topics'])} | {'; '.join(r['terms'])} | "
                     f"{marks} | {target} | {r['sentence'].replace('|', '/')} |")
    return "\n".join(lines) + "\n"


TIER_FIELDS = ("videos_queued", "videos_with_twin", "videos_with_source_text", "videos_with_made_text",
               "videos_with_captions", "titles_matching", "videos_with_text_hit", "videos_prioritised")


def count_rows(theme, scope, rows, read, with_hit, tier=None):
    """Counts per person and kind, and the totals as person "all" (no text, no ids). The "all" row of every kind is
    written even when it is all zeros; a person's row only when that person has something of that kind."""
    topics = theme.topics()
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["person_id"], r["kind"])].append(r)
    keys = sorted(set(read) | set(by))
    people = sorted({p for p, _ in keys})
    out = []
    for person in people + ["all"]:
        for kind in KINDS:
            if person == "all":
                mine = [r for r in rows if r["kind"] == kind]
                n_read = sum(v for (p, k), v in read.items() if k == kind)
                n_with = sum(len(v) for (p, k), v in with_hit.items() if k == kind)
            else:
                mine, n_read = by.get((person, kind), []), read.get((person, kind), 0)
                n_with = len(with_hit.get((person, kind), ()))
            has_tier_row = tier is not None and kind == "title" and (person == "all" or person in tier)
            if not (n_read or mine or has_tier_row or person == "all"):
                continue
            distinct = [r for r in mine if not r["copy"]]
            years = sorted(y for r in distinct for y in targets(r))
            said = sorted(y for y in (pt.year_of(r["date_said"]) for r in distinct) if y)
            row = {"scope": scope, "person_id": person, "kind": kind, "items_read": n_read, "items_with_hit": n_with,
                   "hits": len(mine), "distinct": len(distinct),
                   "future_marked": sum(bool(r["future"] or r["predict"]) for r in distinct),
                   "warning_marked": sum(bool(r["warning"]) for r in distinct),
                   "prediction_candidates": sum(r["prediction_candidate"] for r in distinct),
                   "with_window": sum(bool(targets(r)) for r in distinct),
                   "earliest_target": years[0] if years else "", "latest_target": years[-1] if years else "",
                   "earliest_said": said[0] if said else "", "latest_said": said[-1] if said else ""}
            for t in topics:
                row[f"topic_{t}"] = sum(t in r["topics"] for r in distinct)
            if tier is not None:
                if has_tier_row:
                    vals = tier.values() if person == "all" else [tier[person]]
                    for k in TIER_FIELDS:
                        row[k] = sum(v[k] for v in vals)
                else:
                    row.update({k: "" for k in TIER_FIELDS})
            out.append(row)
    fields = ["scope", "person_id", "kind", "items_read", "items_with_hit", "hits", "distinct", "future_marked",
              "warning_marked", "prediction_candidates", "with_window", "earliest_target", "latest_target",
              "earliest_said", "latest_said"] + [f"topic_{t}" for t in topics]
    if tier is not None:
        fields += list(TIER_FIELDS)
    return out, fields


def queue_records(path):
    """(header line, {video_id: line}) of a queue CSV, each line as it is in the file (its line ending, a byte-order
    mark on the header, its quoting), so a priority queue can copy them byte for byte. A quoted field may hold a
    line break: a record ends where the quotes so far are balanced."""
    text = Path(path).read_bytes().decode("utf-8")
    records, buf = [], ""
    # split on "\n" only (str.splitlines also splits on U+2028, U+0085 ..., which a title may hold unquoted)
    for line in re.findall(r"[^\n]*\n|[^\n]+$", text):
        buf += line
        if buf.count('"') % 2 == 0:
            records.append(buf)
            buf = ""
    if buf:
        records.append(buf)
    if not records:
        return "", {}
    header = next(csv.reader([records[0].lstrip("﻿")]))
    col = header.index("video_id")
    out = {}
    for rec in records[1:]:
        fields = next(csv.reader(io.StringIO(rec)), [])
        if len(fields) > col and fields[col] and fields[col] not in out:
            out[fields[col]] = rec if rec.endswith(("\n", "\r")) else rec + ("\r\n" if "\r\n" in records[0] else "\n")
    return records[0], out


def write_priority_queue(path, sources, wanted):
    """The lines of the queue CSVs `sources` (header from the first, rows in their order) for the video ids
    `wanted`, byte for byte; the files must share one header."""
    header, lines, seen = None, [], set()
    for src in sources:
        h, recs = queue_records(src)
        if header is None:
            header = h
        elif h.lstrip("﻿").rstrip("\r\n") != header.lstrip("﻿").rstrip("\r\n"):
            raise SystemExit(f"{src}: its header differs from the first queue's")
        for v, rec in recs.items():
            if v in wanted and v not in seen:
                seen.add(v)
                lines.append(rec)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(((header or "") + "".join(lines)).encode("utf-8"))
    tmp.replace(path)
    return len(lines)


def resolve(root, p):
    p = Path(p)
    return p if p.is_absolute() or p.exists() else Path(root) / p


def search(args):
    root = Path(args.root)
    theme = load_theme(args.theme)
    if args.queue and args.scope == "all":
        raise SystemExit("--queue makes a tier: give it a name with --scope (e.g. --scope newest10)")
    if not args.queue and args.scope != "all":
        raise SystemExit(f"--scope {args.scope} needs its tier queue: --queue <queue CSV>")
    if args.priority_from and args.queue:
        raise SystemExit("--priority-from is for scope all: a tier's priority queue comes from its own --queue")
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    only = {x.strip() for x in (args.only or "").split(",") if x.strip()}
    if args.publish_counts and (only or kinds != set(KINDS)):
        raise SystemExit("--publish-counts would publish partial counts: leave out --only and --kinds")
    scope = args.scope
    out = ensure_outside_git(args.out or root / "analysis" / "themes" / theme.name / scope)
    out.mkdir(parents=True, exist_ok=True)
    approx = pt.listing_dates(args.listing)
    for r in load_queue(args.dates_from, root)[0]:
        if r.get("upload_date_approx"):
            approx.setdefault(r["video_id"], approx_date(r["upload_date_approx"]))
    queue, fields = load_queue(args.queue, root)
    queued = {r["video_id"]: r for r in queue}
    for v, r in queued.items():
        if r.get("upload_date_approx"):
            approx.setdefault(v, approx_date(r["upload_date_approx"]))
    catalogue = read_csv(root / "catalog" / "catalog.csv")
    floors = pt.undated_floors(catalogue, approx, pt.UNDATED_FLOOR)
    by_id = {r["item_id"]: r for r in catalogue}
    if queued:
        items = [r for r in catalogue if r["item_id"] in queued or (r.get("twin_of") or "") in queued]
    else:
        items = catalogue
    items = [r for r in items if not only or r["person_id"] in only]

    hits, read, with_hit = [], collections.Counter(), collections.defaultdict(set)
    dated = {}          # item id -> (date, basis) for the items dated by the date their text opens with

    def scan(row, kind, sentences, said, basis, via, lead_span):
        floor = floors.get(row["person_id"], 0)
        units = [norm(s) for _, s in sentences]
        if theme.screen is not None and not theme.screen.search(" ".join(units)):
            return
        for idx, unit in enumerate(units):
            if not unit or not theme.candidate(unit):
                continue
            kept, _ = theme.evaluate(unit, kind)
            if kept:
                hits.append(make_hit(theme, scope, row, kind, idx, sentences, said, basis, floor, via, unit, kept,
                                     lead_span if idx == 0 else None))
                with_hit[(row["person_id"], kind)].add(row["item_id"])

    for row in items:
        if not (row.get("asr_path") or row.get("publisher_text_path") or row.get("captions_path")):
            continue
        said, basis = pt.date_said(row, approx)
        texts = item_texts(root, row, kinds)
        lead = None
        for kind, sentences in texts:
            if kind == "source" and sentences:
                d, lead = lead_date(norm(sentences[0][1]))
                if d and not said:
                    said, basis = d, "date the text opens with"
                    dated[row["item_id"]] = (said, basis)
        twin = row.get("twin_of") or ""
        via = twin if twin and (not queued or twin in queued) else ""
        for kind, sentences in texts:
            read[(row["person_id"], kind)] += 1
            scan(row, kind, sentences, said, basis, via, lead if kind == "source" else None)

    title_rows, repeats = [], 0
    if "title" in kinds:
        if queued:
            for v, q in queued.items():
                row = dict(by_id.get(v) or {"item_id": v, "person_id": q.get("channel_dir", ""), "lane": "youtube",
                                            "published": ""})
                row.update(title=q.get("title") or row.get("title", ""), listing_rank=q.get("listing_rank", ""),
                           upload_date_approx=q.get("upload_date_approx", ""))
                if not only or row["person_id"] in only:
                    title_rows.append(row)
        else:
            for r in items:
                if not (r.get("title") or "").strip():
                    continue
                video = by_id.get(r.get("twin_of") or "")
                # a twin's title that repeats its video's title is the same title: read once, as the video's
                if (video and video["person_id"] == r["person_id"]
                        and key_form(norm(video.get("title"), "title")) == key_form(norm(r["title"], "title"))):
                    repeats += 1
                    continue
                title_rows.append(r)
    for row in title_rows:
        said, basis = dated.get(row["item_id"]) or pt.date_said(row, approx)
        read[(row["person_id"], "title")] += 1
        unit = norm(row["title"], "title")
        if unit and theme.candidate(unit):
            kept, _ = theme.evaluate(unit, "title")
            if kept:
                hits.append(make_hit(theme, scope, row, "title", 0, [], said, basis,
                                     floors.get(row["person_id"], 0), "", unit, kept))
                with_hit[(row["person_id"], "title")].add(row["item_id"])

    collapse(hits)
    by_person = collections.defaultdict(list)
    for r in hits:
        by_person[r["person_id"]].append(r)
    people = sorted({p for p, _ in read} | set(by_person))
    for person in people:
        rows = sorted(by_person.get(person, []), key=lambda r: (r["date_said"] or "9999", r["kind"], r["item_id"], r["idx"]))
        atomic_write_text(out / f"{person}.jsonl", "".join(
            json.dumps({k: v for k, v in r.items() if not k.startswith("_")}, ensure_ascii=False) + "\n" for r in rows))
        atomic_write_text(out / f"{person}.md", person_md(theme, scope, person, rows,
                                                          {k: read.get((person, k), 0) for k in KINDS}))

    # the videos to fetch first: a title that is a hit, or a text here (a twin's, or the video's own) with a hit
    title_hits = {r["item_id"]: r for r in hits if r["kind"] == "title"}
    text_hit_videos = collections.defaultdict(list)
    for r in hits:
        if r["kind"] != "title":
            v = r["via_twin"] or (r["item_id"] if r["item_id"] in queued or by_id.get(r["item_id"], {}).get("lane")
                                  == "youtube" else "")
            if v:
                text_hit_videos[v].append(r["kind"])
    tier, prio_path, n_prio = None, None, 0
    if queued:
        tier = {}
        twins = collections.defaultdict(list)
        for r in catalogue:
            if (r.get("twin_of") or "") in queued:
                twins[r["twin_of"]].append(r)
        for row in title_rows:
            v, person = row["item_id"], row["person_id"]
            t = tier.setdefault(person, {k: 0 for k in TIER_FIELDS})
            present = set().union(*[text_kinds(root, r) for r in twins.get(v, []) + ([by_id[v]] if v in by_id else [])])
            t["videos_queued"] += 1
            t["videos_with_twin"] += bool(twins.get(v))
            t["videos_with_source_text"] += "source" in present
            t["videos_with_made_text"] += "made" in present
            t["videos_with_captions"] += "captions" in present
            t["titles_matching"] += v in title_hits
            t["videos_with_text_hit"] += v in text_hit_videos
            t["videos_prioritised"] += v in title_hits or v in text_hit_videos
        rows = []
        for row in title_rows:
            h = title_hits.get(row["item_id"])
            if h:
                rows.append({"video_id": row["item_id"], "channel_dir": queued[row["item_id"]].get("channel_dir", ""),
                             "person_id": row["person_id"], "listing_rank": row.get("listing_rank", ""),
                             "upload_date_approx": approx_date(row.get("upload_date_approx", "")),
                             "topics": " ".join(h["topics"]), "includes": " ".join(h["includes"]),
                             "terms": "; ".join(h["terms"]), "future": " ".join(h["future"] + h["predict"]),
                             "warning": " ".join(h["warning"]), "title": h["sentence"]})
        write_csv(out / "titles.csv", rows, ["video_id", "channel_dir", "person_id", "listing_rank",
                                             "upload_date_approx", "topics", "includes", "terms", "future", "warning",
                                             "title"])
        prio_sources = [resolve(root, p) for p in args.queue]
    else:
        prio_sources = [resolve(root, p) for p in args.priority_from]
    if prio_sources:
        wanted = set(title_hits) | set(text_hit_videos)
        prio_path = ensure_outside_git(root / "jobs") / f"queue_{theme.name}_{scope}.csv"
        n_prio = write_priority_queue(prio_path, prio_sources, wanted)
        listed = {r["video_id"]: r for r in load_queue(prio_sources, root)[0]}
        why = [{"video_id": v, "channel_dir": q.get("channel_dir", ""), "listing_rank": q.get("listing_rank", ""),
                "upload_date_approx": approx_date(q.get("upload_date_approx", "")),
                "title_hit": int(v in title_hits),
                **{f"text_hits_{k}": text_hit_videos.get(v, []).count(k) for k in ("source", "made", "captions")}}
               for v, q in listed.items() if v in wanted]
        write_csv(out / "priority.csv", why, ["video_id", "channel_dir", "listing_rank", "upload_date_approx",
                                              "title_hit", "text_hits_source", "text_hits_made", "text_hits_captions"])

    counts, cfields = count_rows(theme, scope, hits, read, with_hit, tier)
    write_csv(out / "counts.csv", counts, cfields)
    if args.publish_counts:
        name = f"theme_{theme.name}.csv" if scope == "all" else f"theme_{theme.name}_{scope}.csv"
        shutil.copyfile(out / "counts.csv", ET_ROOT / "plan" / name)
    total = [c for c in counts if c["person_id"] == "all"]
    print(f"{theme.name}/{scope}: " + "; ".join(f"{c['kind']} {c['items_read']} read, {c['hits']} hits "
                                               f"({c['distinct']} distinct)" for c in total)
          + (f"; {repeats} twin titles that repeat their video's read once" if repeats else "")
          + (f"; {len(dated)} undated items dated by the date their text opens with" if dated else "")
          + (f"; {sum(t['titles_matching'] for t in tier.values())} queued titles match" if tier is not None else "")
          + (f"; {n_prio} videos -> {prio_path}" if prio_path else "") + f" -> {out}")
    return hits


# ---------------------------------------------------------------------------------------------------- sample, score
def scope_hits(base, scope):
    return [r for f in sorted((Path(base) / scope).glob("*.jsonl")) for r in read_jsonl(f)]


def draw(rows, per_person, seed, exclude=()):
    """Up to per_person rows from each person, seeded; rows whose sentence key is in exclude are never drawn."""
    exclude = set(exclude)
    by = collections.defaultdict(list)
    for r in rows:
        if r["key"] not in exclude:
            by[r["person_id"]].append(r)
    rng = random.Random(seed)
    picked = []
    for person in sorted(by):
        rs = sorted(by[person], key=lambda r: (r["item_id"], r["kind"], r["idx"]))
        picked += rng.sample(rs, min(per_person, len(rs)))
    return picked, rng


KEY_FIELDS = ("person_id", "item_id", "kind", "lane", "via_twin", "scope", "date_said", "includes", "topics", "terms",
              "future", "predict", "warning", "hedged", "prediction_candidate", "window_lo", "window_hi", "time_expr",
              "past_window", "key")


def sample_cmd(args):
    root = Path(args.root)
    theme = load_theme(args.theme)
    base = root / "analysis" / "themes" / theme.name
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    pool, seen = [], set()
    for scope in args.from_:
        for r in sorted(scope_hits(base, scope), key=lambda r: (r["person_id"], r["item_id"], r["kind"], r["idx"])):
            # one unit per sentence within a person and kind (kinds stay apart; scopes overlap)
            if r.get("copy") or r["kind"] not in kinds or (r["person_id"], r["kind"], r["key"]) in seen:
                continue
            seen.add((r["person_id"], r["kind"], r["key"]))
            pool.append(r)
    excluded = {k["key"] for d in args.exclude for k in read_jsonl(Path(d) / "key.jsonl") if k.get("key")}
    picked, rng = draw(pool, args.per_person, args.seed, excluded)
    for r in picked:
        r["_ensured"] = False
    in_sample = {r["key"] for r in picked}
    ensured = {"twins": {}, "scope": {}}
    for what, scopes, wanted in (("twins", args.ensure_twins, lambda r: bool(r.get("via_twin"))),
                                 ("scope", args.ensure_scope, lambda r: True)):
        for scope in scopes:
            must = sorted((r for r in scope_hits(base, scope) if wanted(r) and r["kind"] in kinds),
                          key=lambda r: (r["person_id"], r["item_id"], r["kind"], r["idx"]))
            keys = {r["key"] for r in must}
            info = {"hits": len(must), "distinct_sentences": len(keys), "in_draw": len(keys & in_sample), "added": 0,
                    "by_kind": dict(sorted(collections.Counter(r["kind"] for r in must).items()))}
            for r in must:
                if r["key"] not in in_sample:
                    in_sample.add(r["key"])
                    picked.append(dict(r, _ensured=f"{what}:{scope}"))
                    info["added"] += 1
            ensured[what][scope] = info
    rng.shuffle(picked)
    out = ensure_outside_git(args.out)
    out.mkdir(parents=True, exist_ok=True)
    names = person_names(root, args.aliases)
    key, blind = [], []
    for i, r in enumerate(picked, 1):
        uid = f"u{i:03d}"
        key.append({"uid": uid, **{k: r.get(k) for k in KEY_FIELDS}, "ensured": r["_ensured"]})
        hide = masker(r["person_id"], names.get(r["person_id"], ()))
        blind.append({"uid": uid, "sentence": hide(r["sentence"]),
                      "context": {"before": hide(r.get("context_before", "")), "after": hide(r.get("context_after", ""))},
                      "matched_terms": r["terms"]})
    atomic_write_text(out / "key.jsonl", "".join(json.dumps(k, ensure_ascii=False) + "\n" for k in key))
    atomic_write_text(out / "sample.jsonl", "".join(json.dumps(b, ensure_ascii=False) + "\n" for b in blind))
    strata = collections.Counter(r["person_id"] for r in pool)
    atomic_write_text(out / "strata.json", json.dumps(dict(sorted(strata.items())), indent=1))
    added = sum(v["added"] for group in ensured.values() for v in group.values())
    notes = [f"--ensure-twins {s}: {v['hits']} hit(s) came through a twin of a queued video; {v['in_draw']} were in "
             f"the draw and {v['added']} were added." for s, v in ensured["twins"].items()]
    notes += [f"--ensure-scope {s}: {v['hits']} hit(s) in that scope; {v['in_draw']} were in the draw and "
              f"{v['added']} were added." for s, v in ensured["scope"].items()]
    if added:
        notes.append("Added units are beyond --per-person (key.jsonl: ensured); the weighted shares treat them as "
                     "part of their person's draw.")
    meta = {"name": out.name, "theme": theme.name, "lexicon": Path(theme.source).name, "purpose": args.purpose,
            "seed": args.seed, "per_person": args.per_person, "from": args.from_, "kinds": sorted(kinds),
            "excluded": [Path(d).name for d in args.exclude], "units": len(picked),
            "drawn": len(picked) - added, "added": added, "people": len({k["person_id"] for k in key}),
            "pool_distinct": len(pool), "by_kind": dict(sorted(collections.Counter(k["kind"] for k in key).items())),
            "ensure_twins": ensured["twins"], "ensure_scope": ensured["scope"],
            "blinding": "sample.jsonl holds no person, item, title or date; the person's names inside a unit (the "
                        "words of the id, the name, channel title and handle of plan/channel_inventory.csv, the "
                        "queues' entity column, --aliases) are shown as [name]. Other names in the text (a "
                        "collaborator, a place) stay. A title unit is the hit itself (the title), with no context.",
            "note": " ".join(notes),
            "labels": {"file": "labels_a.jsonl and labels_b.jsonl, one line per uid",
                       "on_topic": "yes, no or unclear: is the sentence about the theme (see the theme's description)",
                       "type": "when on topic, one of " + ", ".join(pp.TYPES),
                       "topic": "optional, one of " + ", ".join(t for t in theme.topics() if t not in theme.generic)},
            "description": theme.description}
    atomic_write_text(out / "meta.json", json.dumps(meta, indent=1, ensure_ascii=False))
    print(f"{len(picked)} units ({len(picked) - added} drawn, {added} added) from {meta['people']} people -> {out}")
    return meta


def person_names(root, aliases=None):
    """{person_id: [names]} for the masker: plan/channel_inventory.csv (person name, channel title, handle), the
    entity column of the queues in <root>/jobs, and an optional aliases JSON ({person_id: [names]}, kept private)."""
    out = collections.defaultdict(set)
    inv = ET_ROOT / "plan" / "channel_inventory.csv"
    for r in (read_csv(inv) if inv.exists() else []):
        for k in ("person_name", "channel_title", "handle"):
            v = (r.get(k) or "").strip().lstrip("@")
            if len(v) >= 3:
                out[r["person_id"]].add(v)
    for q in sorted(Path(root, "jobs").glob("queue_*.csv")):
        try:
            with open(q, newline="", encoding="utf-8-sig") as handle:
                for r in csv.DictReader(handle):
                    for e in re.split(r"[;,/]|\(|\)", r.get("entity") or ""):
                        e = e.strip()
                        if len(e) >= 4 and r.get("channel_dir"):
                            out[r["channel_dir"]].add(e)
        except (OSError, csv.Error, UnicodeDecodeError):
            continue
    if aliases:
        for p, names in json.loads(Path(aliases).read_text(encoding="utf-8")).items():
            out[p].update(n for n in names if n)
    return {p: sorted(v) for p, v in out.items()}


def masker(person_id, names=()):
    """A function that shows the person's names as [name]: the full name from the id ("zed-quorn" -> Zed Quorn) and
    any of `names` (whole words, any case, spaces or hyphens between their words)."""
    pats = []
    for n in [" ".join(w for w in re.split(r"[-_]+", person_id or "") if w)] + list(names):
        words = [w for w in re.split(r"[\s\-_.]+", n) if w]
        if words:
            pats.append(r"[\s\-_.]*".join(re.escape(w) for w in words))
    if not pats:
        return lambda s: s
    pats.sort(key=len, reverse=True)
    rx = re.compile(r"(?<!\w)(?:" + "|".join(pats) + r")(?!\w)", re.I)
    return lambda s: rx.sub("[name]", s or "")


def on_label(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    v = str(value if value is not None else "").strip().lower()
    return "yes" if v in ON else "no" if v in OFF else "unclear"


def score(a_rows, b_rows, key_rows, strata=None):
    a = {r["uid"]: r for r in a_rows}
    b = {r["uid"]: r for r in b_rows}
    key = {r["uid"]: r for r in key_rows}
    uids = [u for u in key if u in a and u in b]
    missing = sorted(set(key) - set(uids))

    def valid(r):
        t = r.get("type")
        return (t in pp.TYPES) if (t or on_label(r.get("on_topic")) == "yes") else True
    bad = sorted(u for u in uids if not (valid(a[u]) and valid(b[u])))
    uids = [u for u in uids if u not in bad]
    on = lambda r: on_label(r.get("on_topic")) == "yes"  # noqa: E731
    like = lambda r: on(r) and r.get("type") in pp.PREDICTION_LIKE  # noqa: E731
    warn = lambda r: on(r) and r.get("type") == "warning"  # noqa: E731

    def share(us):
        n = len(us)
        both = [u for u in us if on(a[u]) and on(b[u])]
        res = {"units": n, "coder_a_on": sum(on(a[u]) for u in us), "coder_b_on": sum(on(b[u]) for u in us),
               "both_on": len(both), "either_on": sum(on(a[u]) or on(b[u]) for u in us),
               "both_on_prediction_like": sum(like(a[u]) and like(b[u]) for u in both),
               "both_on_warning": sum(warn(a[u]) and warn(b[u]) for u in both)}
        res["on_share"] = round(res["both_on"] / n, 3) if n else None
        res["prediction_like_share_of_on"] = round(res["both_on_prediction_like"] / len(both), 3) if both else None
        res["warning_share_of_on"] = round(res["both_on_warning"] / len(both), 3) if both else None
        return res

    def grouped(field):
        groups = collections.defaultdict(list)
        for u in uids:
            vals = key[u].get(field)
            for v in (vals if isinstance(vals, list) else [vals]):
                groups[str(v)].append(u)
        return {g: share(us) for g, us in sorted(groups.items())}

    both_on = [u for u in uids if on(a[u]) and on(b[u])]
    oa, ob = [on_label(a[u].get("on_topic")) for u in uids], [on_label(b[u].get("on_topic")) for u in uids]
    res = {"units": len(uids), "missing": missing, "invalid_type": bad,
           "on_topic_agreement": round(sum(x == y for x, y in zip(oa, ob)) / len(uids), 3) if uids else None,
           "on_topic_kappa": pp.kappa(oa, ob),
           "on_topic_kappa_binary": pp.kappa([x == "yes" for x in oa], [y == "yes" for y in ob]),
           "type_kappa_on": pp.kappa([a[u].get("type") for u in both_on], [b[u].get("type") for u in both_on]),
           "prediction_like_kappa_on": pp.kappa([like(a[u]) for u in both_on], [like(b[u]) for u in both_on]),
           "topic_kappa_on": pp.kappa([a[u].get("topic") or "" for u in both_on],
                                      [b[u].get("topic") or "" for u in both_on]),
           "all": share(uids), "by_kind": grouped("kind"), "by_person": grouped("person_id"),
           "by_topic": grouped("topics"), "by_include": grouped("includes"),
           "disagree_on_topic": [u for u, x, y in zip(uids, oa, ob) if x != y]}
    al = res["all"]
    res["on_share_wilson95"] = pp.wilson(al["both_on"], al["units"])
    res["prediction_like_share_of_on_wilson95"] = pp.wilson(al["both_on_prediction_like"], al["both_on"])
    res["warning_share_of_on_wilson95"] = pp.wilson(al["both_on_warning"], al["both_on"])
    if strata:
        # prediction_pilot's weighting reads "both_prediction_like": here it is the count both coders call on topic
        per = {p: {"units": s["units"], "both_prediction_like": s["both_on"]} for p, s in res["by_person"].items()}
        res["weighted_on_share"] = pp.weighted_share(per, strata)
        res["weighted_on_ci95"] = pp.weighted_interval(per, strata)
        res["weighted_over_hits"] = sum(strata.get(p, 0) for p in per)
        res["distinct_hits"] = sum(strata.values())
    return res


def score_cmd(args):
    out = ensure_outside_git(args.out)
    strata = json.loads((out / "strata.json").read_text()) if (out / "strata.json").exists() else None
    res = score(read_jsonl(args.labels[0]), read_jsonl(args.labels[1]), read_jsonl(out / "key.jsonl"), strata)
    atomic_write_text(out / "score.json", json.dumps(res, indent=1))
    al = res["all"]
    print(f"{res['units']} units; on-topic kappa {res['on_topic_kappa']}; on topic: coder A {al['coder_a_on']}, "
          f"coder B {al['coder_b_on']}, both {al['both_on']} ({al['on_share']}); of those prediction-like "
          f"{al['both_on_prediction_like']}, warnings {al['both_on_warning']}; weighted on-topic share "
          f"{res.get('weighted_on_share')}")
    return res


# ---------------------------------------------------------------------------------------------------- measure
def combine(labels):
    """One label from several readers' (on, edge, off): the majority of on against the rest; a tie is edge."""
    c = collections.Counter(labels)
    if c["on"] > len(labels) - c["on"]:
        return "on"
    if c["off"] > len(labels) - c["off"]:
        return "off"
    return "edge"


def tally(rs, field="label"):
    c = collections.Counter(r[field] for r in rs)
    n = sum(c.values())
    return {"read": n, "on": c["on"], "edge": c["edge"], "off": c["off"],
            "precision": round(c["on"] / n, 3) if n else None, "wilson95": pp.wilson(c["on"], n)}


def lowest(by_kind):
    """The lowest precision among the kinds that have a read (never a figure pooled across kinds)."""
    vals = [t["precision"] for t in by_kind.values() if t.get("precision") is not None]
    return min(vals) if vals else None


def coded_units(sample, hits):
    """[(kind, both_on, either_on, includes now or None)] for the units of a coded sample folder: its key.jsonl and
    two coders' labels (labels_a.jsonl, labels_b.jsonl), joined to the hits now by kind and sentence key."""
    sample = Path(sample)
    a = {r["uid"]: r for r in read_jsonl(sample / "labels_a.jsonl")}
    b = {r["uid"]: r for r in read_jsonl(sample / "labels_b.jsonl")}
    now = {}
    for h in hits:
        now.setdefault((h["kind"], h["key"]), set()).update(h["includes"])
    out = []
    for k in read_jsonl(sample / "key.jsonl"):
        if k["uid"] in a and k["uid"] in b:
            on_a, on_b = on_label(a[k["uid"]].get("on_topic")) == "yes", on_label(b[k["uid"]].get("on_topic")) == "yes"
            out.append((k["kind"], on_a and on_b, on_a or on_b, now.get((k["kind"], k["key"]))))
    return out


def measure_cmd(args):
    root = Path(args.root)
    theme = load_theme(args.theme)
    catalogue = {r["item_id"]: r for r in read_csv(root / "catalog" / "catalog.csv")}
    titles = {q["video_id"]: q for q in load_queue(args.queue, root)[0]}
    hits = scope_hits(root / "analysis" / "themes" / theme.name, args.scope)
    by_key = {}
    for h in sorted(hits, key=lambda h: (bool(h.get("copy")), h["item_id"], h["kind"], h["idx"])):
        by_key.setdefault((h["kind"], h["key"]), (h["item_id"], h["kind"], h["idx"]))
        by_key.setdefault((None, h["key"]), (h["item_id"], h["kind"], h["idx"]))
    units, unresolved = collections.defaultdict(list), collections.Counter()
    for r in read_csv(args.labels):
        label = r["label"].strip().lower()
        kind = ("title" if r["kind"] in TITLE_KINDS else r["kind"]) if (r.get("kind") or "").strip() else None
        if not (r.get("item_id") or "").strip():
            # a label kept by the sentence's hash alone: it is measured when the sentence is one of the hits now;
            # otherwise it is no hit, and an "on" one is a unit the lexicon misses
            unit = by_key.get((kind, (r.get("key") or "").strip()))
            if unit:
                units[unit].append(label)
            else:
                unresolved[label] += 1
            continue
        units[(r["item_id"], kind, int(r.get("idx") or 0))].append(label)
    texts, missing, merged = {}, 0, {}
    for (item, kind, idx), labs in sorted(units.items()):
        row = catalogue.get(item)
        if kind == "title":
            title = (row or {}).get("title") or (titles.get(item) or {}).get("title") or ""
            unit = norm(title, "title")
        else:
            if item not in texts:
                texts[item] = dict(item_texts(root, row, {"source", "made", "captions"})) if row else {}
            sents = texts[item].get(kind) or []
            unit = norm(sents[idx][1]) if idx < len(sents) else ""
        if not unit:
            missing += 1
            continue
        person = (row or {}).get("person_id") or (titles.get(item) or {}).get("channel_dir", "")
        key = (person, kind, sentence_key(unit))
        if key in merged:   # the same sentence labelled in two items of one person and kind (a copy): one unit
            merged[key]["labels"] += labs
            continue
        kept, voided = theme.evaluate(unit, kind)
        merged[key] = {"kind": kind, "labels": list(labs), "kept": kept, "voided": voided}
    results = list(merged.values())
    for r in results:
        r["label"] = combine(r["labels"])
    kinds = [k for k in KINDS if any(r["kind"] == k for r in results) or any(h["kind"] == k for h in hits)]
    matched = collections.Counter((i, h["kind"]) for h in hits for i in h["includes"])
    distinct = collections.Counter((i, h["kind"]) for h in hits if not h.get("copy") for i in h["includes"])
    coded = coded_units(args.coded, hits) if args.coded else []

    def coded_tally(us):
        n = len(us)
        both = sum(u[1] for u in us)
        return {"units": n, "both_on": both, "either_on": sum(u[2] for u in us),
                "precision": round(both / n, 3) if n else None, "wilson95": pp.wilson(both, n)}

    inc_m, exc_m = {}, {}
    for inc in theme.includes:
        mine = [r for r in results if inc["id"] in r["kept"]]
        by_kind = {k: {"hits": matched[(inc["id"], k)], "distinct": distinct[(inc["id"], k)],
                       **tally([r for r in mine if r["kind"] == k])} for k in kinds}
        m = {"scope": args.scope, "by_kind": by_kind, "precision": lowest(by_kind)}
        if coded:
            m["coded"] = {k: coded_tally([u for u in coded if u[0] == k and u[3] and inc["id"] in u[3]])
                          for k in kinds}
        inc_m[inc["id"]] = m
    for x in theme.excludes:
        m = {}
        for k in kinds:
            mine = [r for r in results if r["kind"] == k and any(x["id"] in v for v in r["voided"].values())]
            removed = [r for r in mine if not r["kept"]]
            m[k] = {"voided_read": len(mine), **{a: b for a, b in tally(mine).items() if a in ("on", "edge", "off")},
                    "removed_read": len(removed), "removed_on": sum(r["label"] == "on" for r in removed)}
        exc_m[x["id"]] = {"by_kind": m}
    summary = {"date": datetime.date.today().isoformat(), "scope": args.scope, "labelled_units_missing": missing,
               "labels_not_hits": dict(sorted(unresolved.items())),
               "by_kind": {k: {"labelled_units": sum(r["kind"] == k for r in results),
                               "kept_by_lexicon": tally([r for r in results if r["kind"] == k and r["kept"]]),
                               "on_units": sum(r["kind"] == k and r["label"] == "on" for r in results),
                               "on_units_found": sum(r["kind"] == k and r["label"] == "on" and bool(r["kept"])
                                                     for r in results)} for k in kinds},
               "on_labels_not_hits": unresolved["on"],
               "labels": args.note or Path(args.labels).name}
    if coded:
        summary["coded"] = {"sample": Path(args.coded).name,
                            "by_kind": {k: {**coded_tally([u for u in coded if u[0] == k and u[3]]),
                                            "no_longer_hits": sum(u[0] == k and not u[3] for u in coded),
                                            "no_longer_hits_both_on": sum(u[0] == k and not u[3] and u[1]
                                                                          for u in coded)} for k in kinds}}
    print(f"{len(results)} labelled units ({missing} not found; {sum(unresolved.values())} hash-only labels are no "
          f"hit now, {unresolved['on']} of them on topic: counted as missed)")
    for k, v in summary["by_kind"].items():
        t = v["kept_by_lexicon"]
        print(f"  {k}: {v['labelled_units']} labelled; the lexicon keeps {t['read']}: {t['on']} on, {t['edge']} edge, "
              f"{t['off']} off (precision {t['precision']}); finds {v['on_units_found']} of {v['on_units']} on")
    print(f"{'include':22} " + " ".join(f"{k:>16}" for k in kinds) + "  lowest")
    for i, m in inc_m.items():
        cells = [f"{m['by_kind'][k]['on']}/{m['by_kind'][k]['read']} of {m['by_kind'][k]['distinct']}" for k in kinds]
        print(f"{i:22} " + " ".join(f"{c:>16}" for c in cells) + f"  {m['precision']}")
    for i, m in exc_m.items():
        cells = [f"{m['by_kind'][k]['voided_read']}v {m['by_kind'][k]['removed_on']}on" for k in kinds]
        print(f"{i:22} " + " ".join(f"{c:>16}" for c in cells))
    if args.write_lexicon:
        path = theme_path(args.theme)
        data = json.loads(path.read_text(encoding="utf-8"))
        for e in data.get("include") or []:
            if e.get("id") in inc_m:
                e["precision"] = inc_m[e["id"]]["precision"]
                e["measured"] = inc_m[e["id"]]
        for e in data.get("exclude") or []:
            if e.get("id") in exc_m:
                e["measured"] = exc_m[e["id"]]
        data["measured"] = summary
        atomic_write_text(path, json.dumps(data, indent=1, ensure_ascii=False) + "\n")
        print(f"-> {path}")
    return inc_m, exc_m, summary


# ---------------------------------------------------------------------------------------------------- leaks
STOP = set("the a an of to and in on is are for will be this that with by it as at or from was were has have not "
           "you your we our they their he she his her its i".split())
QUOTED = re.compile(r"""['‘“"]([^'’”"\n]{12,})['’”"]""")


def words_of(text):
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower().replace("’", "'")).split()


def probe_strings(data, extra_files=()):
    """[(where, text)]: a theme file's free text and its patterns' literal words, and the quoted strings of extra
    files (a test file's invented sentences)."""
    out = []
    for k in ("description", "history", "format", "after_sample"):
        if isinstance(data.get(k), str):
            out.append((k, data[k]))
    for sec in ("include", "exclude"):
        for e in data.get(sec) or []:
            for k in ("notes", "why", "after_sample"):
                if e.get(k):
                    out.append((f"{e.get('id')}:{k}", e[k]))
            for k in ("examples", "keeps"):
                out += [(f"{e.get('id')}:{k}", x) for x in e.get(k) or []]
            lits = re.findall(r"(?:[a-z']+(?:\\s[+*]?|\s)){2,}[a-z']+", re.sub(r"\\b", " ", e.get("pattern") or ""), re.I)
            out += [(f"{e.get('id')}:pattern", re.sub(r"\\s[+*]?", " ", x)) for x in lits if len(x.split()) >= 3]
    for f in extra_files:
        text = Path(f).read_text(encoding="utf-8")
        out += [(f"{Path(f).name}", m.group(1)) for m in QUOTED.finditer(text) if " " in m.group(1)]
    return out


def leaks_cmd(args):
    """Shared word runs between the theme file (and --check files) and the stored texts and titles; stored ids."""
    root = Path(args.root)
    path = theme_path(args.theme)
    data = json.loads(path.read_text(encoding="utf-8"))
    probes = [(w, x, words_of(x)) for w, x in probe_strings(data, args.check)]
    grams = collections.defaultdict(set)
    for i, (_, _, ws) in enumerate(probes):
        for j in range(len(ws) - 4):
            grams[" ".join(ws[j:j + 5])].add(i)
    tgrams = collections.defaultdict(set)
    for i, (_, _, ws) in enumerate(probes):
        for j in range(len(ws) - 3):
            g = ws[j:j + 4]
            if sum(t not in STOP for t in g) >= 3:
                tgrams[" ".join(g)].add(i)
    found = collections.defaultdict(lambda: {"items": set(), "longest": 0})

    def longest_run(ws, other, pos):
        best = 0
        for i in range(len(ws)):
            for j in pos.get(ws[i], ()):
                n = 0
                while i + n < len(ws) and j + n < len(other) and ws[i + n] == other[j + n]:
                    n += 1
                best = max(best, n)
        return best

    def scan(item, text, title=False):
        ws = words_of(text)
        hit = set()
        for j in range(len(ws) - 4):
            hit |= grams.get(" ".join(ws[j:j + 5]), set())
        if title:
            for j in range(len(ws) - 3):
                hit |= tgrams.get(" ".join(ws[j:j + 4]), set())
        if not hit:
            return
        pos = collections.defaultdict(list)
        for j, w in enumerate(ws):
            pos[w].append(j)
        for i in hit:
            f = found[i]
            f["items"].add(item)
            f["longest"] = max(f["longest"], longest_run(probes[i][2], ws, pos))

    catalogue = read_csv(root / "catalog" / "catalog.csv")
    ids = {r["item_id"] for r in catalogue}
    for r in catalogue:
        scan(r["item_id"], r.get("title") or "", title=True)
        for kind, sents in item_texts(root, r, {"source", "made", "captions"}):
            scan(r["item_id"], " ".join(s for _, s in sents))
    for q in sorted((root / "jobs").glob("queue_*.csv")):
        for r in load_queue([q], root)[0]:
            ids.add(r["video_id"])
            scan(r["video_id"], r.get("title") or "", title=True)
    texts = [path.read_text(encoding="utf-8")] + [Path(f).read_text(encoding="utf-8") for f in args.check]
    tokens = set(re.findall(r"[A-Za-z0-9_-]{8,}", "\n".join(texts)))
    id_hits = sorted(t for t in tokens if t in ids)
    bad = 0
    for i, f in sorted(found.items(), key=lambda kv: -kv[1]["longest"]):
        where, _, ws = probes[i]
        share = f["longest"] / max(1, len(ws))
        flag = f["longest"] >= 7 or (len(ws) >= 5 and share >= 0.6)
        bad += flag
        print(f"{'LEAK ' if flag else 'run  '}{where}: longest shared run {f['longest']} of {len(ws)} words, "
              f"{len(f['items'])} items {sorted(f['items'])[:3]}")
    for t in id_hits:
        print(f"ID   a stored item or video id is in the files: {t}")
    print(f"{len(probes)} strings checked against {len(catalogue)} catalogue rows and the queues: {bad} leaks, "
          f"{len(id_hits)} ids")
    return 1 if bad or id_hits else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="hits of the theme in one scope")
    add_root_arg(s)
    s.add_argument("--theme", default="blackouts", help="a theme in pipeline/themes, or the path of a theme file")
    s.add_argument("--scope", default="all", help="all, or the name of the tier given with --queue")
    s.add_argument("--queue", type=Path, action="append", default=[],
                   help="a tier queue CSV (repeatable; relative to --root when not found as given)")
    s.add_argument("--kinds", default="source,made,captions,title")
    s.add_argument("--only", help="comma-separated person ids")
    s.add_argument("--listing", action="append", type=Path,
                   help="a channel listing (videos_all.jsonl) whose approximate upload dates date YouTube rows")
    s.add_argument("--dates-from", type=Path, action="append", default=[],
                   help="a queue CSV whose upload_date_approx dates YouTube rows, without making the scope a tier")
    s.add_argument("--out", type=Path, help="default <root>/analysis/themes/<theme>/<scope>")
    s.add_argument("--publish-counts", action="store_true",
                   help="also copy counts.csv to plan/theme_<theme>.csv (scope all) or plan/theme_<theme>_<scope>.csv")
    s.add_argument("--priority-from", type=Path, action="append", default=[],
                   help="scope all: a queue CSV (e.g. jobs/queue_youtube_all.csv) whose videos with a title or text "
                        "hit go to jobs/queue_<theme>_all.csv (repeatable)")
    m = sub.add_parser("sample", help="a blinded, seeded sample of distinct hits for coders")
    add_root_arg(m)
    m.add_argument("--theme", default="blackouts")
    m.add_argument("--from", dest="from_", action="append", default=[], help="a scope to draw from (repeatable)")
    m.add_argument("--out", type=Path, required=True)
    m.add_argument("--per-person", type=int, default=10)
    m.add_argument("--seed", type=int, default=20261116)
    m.add_argument("--kinds", default="source,made,captions,title")
    m.add_argument("--ensure-twins", action="append", default=[],
                   help="a scope whose hits through twins must all be in the sample (repeatable)")
    m.add_argument("--ensure-scope", action="append", default=[],
                   help="a scope whose hits (titles too) must all be in the sample (repeatable)")
    m.add_argument("--exclude", type=Path, action="append", default=[],
                   help="an earlier sample folder whose sentences must not be drawn again (repeatable)")
    m.add_argument("--purpose", default="")
    m.add_argument("--aliases", type=Path, help="a private JSON {person_id: [names]} of more names to mask")
    c = sub.add_parser("score", help="two coders' labels -> score.json")
    c.add_argument("--out", type=Path, required=True, help="the sample folder, which holds key.jsonl")
    c.add_argument("labels", nargs=2, type=Path)
    e = sub.add_parser("measure", help="labels of earlier reading against the lexicon now")
    add_root_arg(e)
    e.add_argument("--theme", default="blackouts")
    e.add_argument("--scope", default="all", help="the scope whose hits give each include's matches")
    e.add_argument("--labels", type=Path, required=True, help="CSV: item_id, kind, idx, label (on, edge or off)")
    e.add_argument("--queue", type=Path, action="append", default=[], help="queue CSVs for titles not in the catalogue")
    e.add_argument("--note", default="", help="what the labels are, for the theme file")
    e.add_argument("--coded", type=Path, help="a sample folder with two coders' labels, counted per include and kind")
    e.add_argument("--write-lexicon", action="store_true", help="write precision and counts into the theme file")
    k = sub.add_parser("leaks", help="the theme file's text against the stored texts and titles (counts and ids only)")
    add_root_arg(k)
    k.add_argument("--theme", default="blackouts")
    k.add_argument("--check", type=Path, action="append", default=[],
                   help="another file whose quoted strings are checked too (a test file; repeatable)")
    args = ap.parse_args(argv)
    if args.cmd == "search":
        return search(args)
    if args.cmd == "sample":
        if not args.from_:
            ap.error("sample needs --from <scope>")
        return sample_cmd(args)
    if args.cmd == "score":
        return score_cmd(args)
    if args.cmd == "leaks":
        return leaks_cmd(args)
    return measure_cmd(args)


if __name__ == "__main__":
    result = main()
    sys.exit(result if isinstance(result, int) else 0)
