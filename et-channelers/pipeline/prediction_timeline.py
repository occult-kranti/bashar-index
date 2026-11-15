#!/usr/bin/env python3
"""Find the statements about the future in each channel's texts and lay them out as a timeline.

This is the rules pass of ANALYSIS_PLAN 12.4 (the first of its steps): rules flag sentences that speak of
the future and carry a time expression, a prediction word or a prophecy theme, and code turns each time
expression into a target window counted from the date the text was said (TimeML-style: "in two years" from
a 2021 recording is 2023; "by 2030" keeps one bound; "soon" gets no invented bounds). A later model pass
checks each candidate (is it the entity's claim, is it a prediction or future-tense teaching); until then
every row is a candidate, not a finding.

Texts from the source and speech-to-text made here are read separately and every row says which it is.
The date said is the item's published date in the catalogue, else the approximate upload date of a
channel listing given with --listing (YouTube rows), else an ISO date in the title (L/L Research), else a
year and month in the source address (/2014/07/ on a blog, /1980/0827 at L/L Research), else unknown: a
row without it has no target window for relative expressions, and a window of its that ends before 2000
(--undated-floor), or before the person's oldest dated item when that is older (L/L Research), is taken as
a past reference: the web sources still undated began publishing after 2000.

    python3 -I pipeline/prediction_timeline.py --root ~/et-channelers-private
    python3 -I pipeline/prediction_timeline.py --root ~/et-channelers-private --only darryl-anka \\
        --listing /workspaces/et-yt-newest/discover/videos_all.jsonl

Writes, inside the private folder only (it quotes the texts):
    <root>/analysis/predictions/<person>.jsonl      every candidate, with its sentence
    <root>/analysis/predictions/<person>.md         the timeline: by target window, quotes cut to 30 words
    <root>/analysis/predictions/counts.csv          counts per person and kind (no text)
--publish-counts also copies counts.csv to plan/prediction_counts.csv (counts only, never text).
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, atomic_write_text, ensure_outside_git, read_csv,  # noqa: E402
                    read_jsonl, utc_now, write_csv)

QUOTE_WORDS = 30          # the project's limit for any quote
UNDATED_FLOOR = 2000      # the web sources still undated (Blossom Goodchild, Swaruu, Sam, Jamie Butler) began after
#                           it; a person with older dated items (L/L Research, 1974) gets their earliest year instead
NUM = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
       "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "fifty": 50,
       "a couple of": 2, "a few": 3, "several": 3}
NUMBER = r"(\d{1,3}|a couple of|a few|several|an?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|fifty)"
UNIT = r"(years?|months?|decades?)"

FUTURE = re.compile(r"\b(will|won't|shall|going to|gonna|about to|is coming|are coming|on (its|the) way|"
                    r"in the (near |coming |not too distant )?future|coming (years|months|decades)|"
                    r"upcoming|approaching|ahead of (you|us))\b", re.I)
PREDICT = re.compile(r"\b(predict\w*|prophec\w*|prophes\w*|forecast\w*|foresee\w*|warn\w*|expect(ed)? to|"
                     r"timeline for|window of)\b", re.I)
THEMES = re.compile(r"\b(shift|ascension|harvest|the event|solar flash|disclosure|first contact|open contact|"
                    r"pole shift|cataclysm\w*|collapse|golden age|new earth|great awakening|reset|"
                    r"earthquake\w*|war|economic|financial crash|landing|mass awakening)\b", re.I)
HEDGE = re.compile(r"\b(may|might|could|possibly|probably|likely|perhaps|potentially|probable|"
                   r"most likely|it is possible|we sense|it seems)\b", re.I)
STRONG = re.compile(r"\b(definitely|certainly|absolutely|without (a )?doubt|guaranteed|for sure|inevitabl\w*)\b", re.I)
CONDITIONAL = re.compile(r"\b(if|unless|provided that|as long as|depending on)\b", re.I)
# a channel's own promotion and page furniture: sign-ups, shop offers, links. Never a prediction.
BOILERPLATE = re.compile(r"(register|subscribe|sign up|signup|newsletter|email list|my store|% off|discount|coupon|"
                         r"pay what you want|tickets?|webinar|zoom|livestream (on|at)|click|link (in|below)|"
                         r"https?://|www\.|\b(am|pm) (pacific|eastern)|pacific/|eastern\b.*\bregister|"
                         r"free guided meditation|join (me|us) (for|at|on)|patreon|paypal|venmo|donat\w+|"
                         # page furniture and cross-links (pilot of 2026-11-15: 11 dropped, no prediction among them)
                         r"\bon amazon\b|continue reading|posted by|share to (x|facebook|pinterest)|"
                         r"\b(\d+|one|no) comments?\b|listen to the podcast|all transcripts|watch the original video|"
                         r"\b\S+@\S+\.[a-z]{2,}\b|spell caster|\bpodcast\b.*\b(ep|episode|s\d\d)\b|"
                         r"(look|explore) .* in the book)", re.I)
# a question is a questioner's guess, not the entity's claim (12.4); the pilot found no prediction among 7
QUESTION = re.compile(r"\?\s*[\"”’']?\s*$")
# a report of an earlier statement or of the writing itself ("you said this was going to happen in 2008")
PAST_REPORT = re.compile(r"\b(you|they|he|she|we|i) (said|told|spoke|explained|predicted|mentioned|asked|wrote)\b|"
                         r"\b(was|were) (going to|to)\b|\bas i (edit|write|type)\b|\bcame across\b|\breminisce", re.I)
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9])")

# time expressions, most specific first; each gives (lo, hi, label) from the year said (None when unknown)
YEAR = r"((?:19|20)\d{2})"
RULES = [
    ("between", re.compile(rf"\bbetween {YEAR} and {YEAR}\b", re.I)),
    ("range", re.compile(rf"\b{YEAR}\s*(?:-|–|to|through)\s*{YEAR}\b", re.I)),
    ("by_year", re.compile(rf"\b(?:by|before|no later than|until) (?:the year |the end of )?{YEAR}\b", re.I)),
    ("decade", re.compile(rf"\b(?:the )?((?:19|20)\d0)'?s\b", re.I)),
    ("within", re.compile(rf"\bwithin (?:the next |the coming )?{NUMBER} {UNIT}\b", re.I)),
    ("in_n", re.compile(rf"\b(?:in|over) (?:the next |the coming |about |roughly |around )?{NUMBER} {UNIT}\b", re.I)),
    ("next_unit", re.compile(r"\bnext (year|decade|few years|couple of years)\b", re.I)),
    ("this_unit", re.compile(r"\bthis (year|decade)\b", re.I)),
    ("end_of", re.compile(r"\b(?:by )?the end of (?:this|the) (year|decade)\b", re.I)),
    ("year", re.compile(rf"\b(?:in |during |around |by )?{YEAR}\b", re.I)),
    ("soon", re.compile(r"\b(soon|very soon|shortly|imminent\w*|any (day|time) now|near future)\b", re.I)),
]


def number(word):
    word = word.lower()
    return int(word) if word.isdigit() else NUM.get(word)


def span(n, unit):
    unit = unit.lower()
    return n * 10 if unit.startswith("decade") else (n / 12 if unit.startswith("month") else n)


def time_window(sentence, said_year):
    """(lo, hi, label, matched text) for the first time expression in the sentence, or None. lo and hi are
    years (hi may equal lo); either may be None when the expression gives no bound or the year said is
    unknown. "soon" gets (None, None)."""
    for label, rx in RULES:
        m = rx.search(sentence)
        if not m:
            continue
        g = m.groups()
        if label in ("between", "range"):
            lo, hi = sorted((int(g[0]), int(g[1])))
            return lo, hi, label, m.group(0)
        if label == "by_year":
            return said_year, int(g[0]), label, m.group(0)
        if label == "decade":
            d = int(g[0])
            return d, d + 9, label, m.group(0)
        if label == "year":
            y = int(g[0])
            return y, y, label, m.group(0)
        if label == "soon":
            return None, None, label, m.group(0)
        if said_year is None:
            return None, None, label, m.group(0)
        if label == "within":
            n = number(g[0])
            return (said_year, said_year + round(span(n, g[1])), label, m.group(0)) if n else None
        if label == "in_n":
            n = number(g[0])
            if not n:
                return None
            t = said_year + round(span(n, g[1]))
            return t, t, label, m.group(0)
        if label == "next_unit":
            w = g[0].lower()
            if w == "year":
                return said_year + 1, said_year + 1, label, m.group(0)
            if w == "decade":
                return said_year + 1, said_year + 10, label, m.group(0)
            return said_year + 1, said_year + (2 if "couple" in w else 3), label, m.group(0)
        if label in ("this_unit", "end_of"):
            w = g[0].lower()
            return (said_year, said_year, label, m.group(0)) if w == "year" else (said_year, said_year + 9, label, m.group(0))
    return None


def candidate(sentence, said_year, undated_floor=UNDATED_FLOOR):
    """A dict for a sentence that speaks of the future with a time, a prediction word or a prophecy theme;
    None otherwise. A window that ends before the year said is a past reference, future marker or not ("he
    will assume it is still 1945"): not kept. With no year said, a window that ends before undated_floor
    is taken as a past reference too."""
    # cheapest tests first: most sentences have no future, prediction or hedging word and stop here
    future, predict, hedge = FUTURE.search(sentence), PREDICT.search(sentence), HEDGE.search(sentence)
    if not (future or predict or hedge):
        return None
    window = time_window(sentence, said_year)
    # "may come by 2030" is a hedged statement about the future: a hedging modal with a time counts too
    if not (future or predict or (hedge and window)):
        return None
    theme = THEMES.search(sentence)
    if not (window or predict or theme):
        return None
    if BOILERPLATE.search(sentence) or QUESTION.search(sentence) or PAST_REPORT.search(sentence):
        return None
    lo, hi, label, expr = window if window else (None, None, "", "")
    floor = said_year if said_year else undated_floor
    if floor and hi is not None and hi < floor:
        return None
    return {"markers": sorted({x.group(0).lower() for x in (future, predict, theme) if x}),
            "time_expr": expr, "time_rule": label, "window_lo": lo, "window_hi": hi,
            "conditional": bool(CONDITIONAL.search(sentence)), "hedged": bool(hedge),
            "strong": bool(STRONG.search(sentence))}


def sentences_of_segments(segments):
    """(offset_s, sentence) from timed segments: the segments are joined and split again into sentences,
    each keeping the start of the segment it begins in."""
    out, buf, start = [], "", None
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        if start is None:
            start = seg.get("start")
        buf = f"{buf} {text}".strip()
        parts = SENTENCE.split(buf)
        for p in parts[:-1]:
            out.append((start, p.strip()))
            start = seg.get("start")
        buf = parts[-1]
    if buf.strip():
        out.append((start, buf.strip()))
    return out


def sentences_of_text(text):
    text = re.sub(r"\s+", " ", text)
    return [(None, s.strip()) for s in SENTENCE.split(text) if s.strip()]


def quote(sentence, limit=QUOTE_WORDS):
    words = sentence.split()
    return " ".join(words) if len(words) <= limit else " ".join(words[:limit]) + " …"


def year_of(date):
    m = re.match(r"((?:19|20)\d{2})", date or "")
    return int(m.group(1)) if m else None


TITLE_DATE = re.compile(r"(?<!\d)((?:19|20)\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?!\d)")
# a year and month as path segments of the source address: blogspot /2014/07/..., llresearch /1980/0827
ADDRESS_DATE = re.compile(r"/((?:19|20)\d{2})/(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])?(?=[/_.?#]|$)")


def text_date(row):
    """(date, basis) from the title (an ISO date) or the source address (/YYYY/MM or /YYYY/MMDD); ("", "")
    when neither has one."""
    m = TITLE_DATE.search(row.get("title") or "")
    if m:
        return "-".join(m.groups()), "title"
    m = ADDRESS_DATE.search(row.get("source_url") or "")
    if m:
        return "-".join(g for g in m.groups() if g), "source address"
    return "", ""


def date_said(row, approx):
    """(date, basis): published, else the listing's approximate date, else the title's or address's."""
    if row.get("published"):
        return row["published"], "published"
    if approx.get(row["item_id"]):
        return approx[row["item_id"]], "listing, approximate"
    return text_date(row)


def undated_floors(catalogue, approx, floor):
    """Per person, the year before which an undated item's window is a past reference: the earlier of floor
    and the person's earliest dated item (an undated item is taken to be no older than that). 0 keeps all."""
    if not floor:
        return {}
    out = {}
    for row in catalogue:
        y = year_of(date_said(row, approx)[0])
        out[row["person_id"]] = min(out.get(row["person_id"], floor), y or floor)
    return out


def listing_dates(paths):
    dates = {}
    for p in paths or []:
        for rec in read_jsonl(Path(p)):
            if rec.get("video_id") and rec.get("upload_date_approx"):
                d = rec["upload_date_approx"]
                dates[rec["video_id"]] = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return dates


def read_item_texts(root, row):
    """[(kind, [(offset, sentence)])] for one catalogue row: speech-to-text made here and texts from the
    source, kept apart."""
    out = []
    asr = row.get("asr_path") or ""
    if asr:
        js = root / Path(asr).with_suffix(".json")
        if js.exists():
            try:
                out.append(("made", sentences_of_segments(json.loads(js.read_text(encoding="utf-8")).get("segments") or [])))
            except (ValueError, OSError):
                pass
        elif (root / asr).exists():
            out.append(("made", sentences_of_text((root / asr).read_text(encoding="utf-8", errors="replace"))))
    src = row.get("publisher_text_path") or ""
    if src and (root / src).exists():
        out.append(("source", sentences_of_text((root / src).read_text(encoding="utf-8", errors="replace"))))
    return out


def timeline_md(person, rows, items_read):
    dated = sorted((r for r in rows if r["window_lo"] is not None or r["window_hi"] is not None),
                   key=lambda r: ((r["window_lo"] if r["window_lo"] is not None else r["window_hi"]),
                                  r["window_hi"] or 0, r["date_said"] or "", r["item_id"]))
    undated = [r for r in rows if r["window_lo"] is None and r["window_hi"] is None]
    lines = [f"# Statements about the future: {person}", "",
             f"Rules pass of ANALYSIS_PLAN 12.4, made {utc_now()}. {items_read} items read; {len(rows)} candidates, "
             f"{len(dated)} with a target window. These are candidates, not findings: a model pass is still to check "
             "each one. Private: the quotes are from the texts (at most 30 words).", "",
             "| Target | Said | Kind | Item | Time | Cues | Quote |", "|---|---|---|---|---|---|---|"]
    for r in dated:
        lo, hi = r["window_lo"], r["window_hi"]
        target = f"{lo}" if lo == hi else f"{lo if lo is not None else '…'}–{hi if hi is not None else '…'}"
        cues = ", ".join(c for c, on in (("if", r["conditional"]), ("hedged", r["hedged"]), ("strong", r["strong"])) if on)
        when = f" @{int(r['offset_s'] // 60)}:{int(r['offset_s'] % 60):02d}" if r["offset_s"] is not None else ""
        lines.append(f"| {target} | {r['date_said'] or '?'} | {r['kind']} | {r['item_id']}{when} | {r['time_expr']} | "
                     f"{cues} | {quote(r['sentence']).replace('|', '/')} |")
    lines += ["", f"## Without a target window ({len(undated)})", "",
              "\"Soon\" and statements with a prediction word or theme but no time; and relative times in items "
              "whose date is unknown.", ""]
    for r in sorted(undated, key=lambda r: (r["date_said"] or "", r["item_id"])):
        lines.append(f"- {r['date_said'] or '?'} · {r['kind']} · {r['item_id']}: {quote(r['sentence'])}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--only", help="comma-separated person ids")
    ap.add_argument("--kinds", default="made,source", help="made (speech-to-text here), source (texts from the source)")
    ap.add_argument("--listing", action="append", type=Path,
                    help="a channel listing (videos_all.jsonl) whose approximate upload dates date YouTube rows")
    ap.add_argument("--out", type=Path, help="default <root>/analysis/predictions")
    ap.add_argument("--publish-counts", action="store_true", help="also copy counts.csv to plan/prediction_counts.csv")
    ap.add_argument("--undated-floor", type=int, default=UNDATED_FLOOR,
                    help=f"with no date said, a window that ends before this year is a past reference (default "
                         f"{UNDATED_FLOOR}; 0 keeps them)")
    args = ap.parse_args()

    root = Path(args.root)
    out = ensure_outside_git(args.out or root / "analysis" / "predictions")
    out.mkdir(parents=True, exist_ok=True)
    kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    only = {x.strip() for x in (args.only or "").split(",") if x.strip()}
    approx = listing_dates(args.listing)
    everything = read_csv(root / "catalog" / "catalog.csv")
    floors = undated_floors(everything, approx, args.undated_floor)      # dated items with no text count too
    catalogue = [r for r in everything
                 if (r.get("asr_path") or r.get("publisher_text_path")) and (not only or r["person_id"] in only)]

    by_person, read = {}, {}
    for row in catalogue:
        said, basis = date_said(row, approx)
        for kind, sentences in read_item_texts(root, row):
            if kind not in kinds:
                continue
            read[(row["person_id"], kind)] = read.get((row["person_id"], kind), 0) + 1
            for offset, sentence in sentences:
                c = candidate(sentence, year_of(said), floors.get(row["person_id"], 0))
                if c:
                    by_person.setdefault(row["person_id"], []).append(
                        {"person_id": row["person_id"], "item_id": row["item_id"], "kind": kind, "title": row.get("title", ""),
                         "date_said": said, "date_basis": basis, "offset_s": offset, "sentence": sentence, **c})

    counts = []
    people = sorted({p for p, _ in read})
    for person in people:
        rows = by_person.get(person, [])
        text = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        atomic_write_text(out / f"{person}.jsonl", text)
        items = sum(read.get((person, k), 0) for k in kinds)
        atomic_write_text(out / f"{person}.md", timeline_md(person, rows, items))
        for kind in sorted(kinds):
            mine = [r for r in rows if r["kind"] == kind]
            if not read.get((person, kind)) and not mine:
                continue
            dated = [r for r in mine if r["window_lo"] is not None or r["window_hi"] is not None]
            years = sorted(y for r in dated for y in (r["window_lo"], r["window_hi"]) if y is not None)
            counts.append({"person_id": person, "kind": kind, "items_read": read.get((person, kind), 0),
                           "candidates": len(mine), "with_window": len(dated), "without_window": len(mine) - len(dated),
                           "conditional": sum(r["conditional"] for r in mine), "hedged": sum(r["hedged"] for r in mine),
                           "earliest_target": years[0] if years else "", "latest_target": years[-1] if years else ""})
    fields = ["person_id", "kind", "items_read", "candidates", "with_window", "without_window", "conditional",
              "hedged", "earliest_target", "latest_target"]
    write_csv(out / "counts.csv", counts, fields)
    if args.publish_counts:
        shutil.copyfile(out / "counts.csv", ET_ROOT / "plan" / "prediction_counts.csv")
    total = sum(c["candidates"] for c in counts)
    print(f"{len(catalogue)} items with text for {len(people)} people; {total} candidates "
          f"({sum(c['with_window'] for c in counts)} with a target window) -> {out}")


if __name__ == "__main__":
    main()
