#!/usr/bin/env python3
"""Build the public page of prediction timelines (dashboard/predictions.html) from the private candidates.

The input is the rules pass of prediction_timeline.py (ANALYSIS_PLAN 12.4): <root>/analysis/predictions/<person>.jsonl,
one line per candidate statement about the future, with its sentence. This tool keeps the distinct candidates that
have a target window (copies collapsed, the first occurrence shown), builds each one's public address from the
catalogue, cuts each quote to at most 30 words and to at most 5% of its item's words, runs the guard of 12.9 over
the records and over the finished page, and only then writes the page. Nothing else crosses from the private row:
no sentence, no path, no title, no copy group.

    python3 -I pipeline/prediction_page.py --root ~/et-channelers-private --out dashboard/predictions.html --publish-counts

Writes:
    --out                                               the page (one self-contained file; refused with exit 2 when the
                                                        guard fails, and then nothing is written)
    <root>/analysis/predictions/public_page_report.md   private: per person, statements shown and quoted share of each
                                                        item's words; items with no public address; quotes withheld
    <root>/analysis/predictions/public_page_counts.csv  counts per person (no text); --publish-counts copies it to
                                                        plan/prediction_timeline_counts.csv

The owner's decision of 2026-11-16 to publish the timelines supersedes roadmap D16 ("counts only"); 12.9 still rules
what a statement may show: the person, the date said and its basis, the target window, the kind of text, whether it
is conditional or hedged, the item id and its public address, and a quote of at most 30 words. Never a questioner's
name, never more than 5% of an item's words, no audio, no transcript beyond the quotes, no private path.
"""
from __future__ import annotations

import argparse
import collections
import csv
import html
import json
import math
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ET_ROOT, ID_RE, add_root_arg, atomic_write_text, read_csv, read_jsonl, utc_now, write_csv  # noqa: E402
from prediction_timeline import QUOTE_WORDS, quote  # noqa: E402

SHARE = 0.05                    # 12.9: at most 5% of an item's words in quotes
MIN_QUOTE_WORDS = 6             # a shorter cut is no quote: the time expression is shown instead
QUOTE_CAP_PER_PERSON = 3000     # 12.9 asks for a cap per channel; the owner sets it (default 3,000 words)
BUILD_YEAR = 2026
AXIS_END = 2080
CARDS_SHOWN = 12
PAGE_LIMIT = 2 * 1024 * 1024
PUBLIC_KEYS = ("person_id", "person_name", "role", "item_id", "kind", "date_said", "date_basis", "date_precision",
               "window_lo", "window_hi", "span", "conditional", "hedged", "strong", "time_expr", "time_rule", "quote",
               "quote_words", "link", "offset_s", "public_page_kind")
WORD_COLUMNS = ("publisher_text_words", "captions_words", "asr_words")
PATH_COLUMNS = ("audio_path", "asr_path", "captions_path", "publisher_text_path")
PRIVATE_MARKS = ("/workspaces/", "et-channelers-private", "~/", "file:") + PATH_COLUMNS
PRIVATE_PATH = re.compile(r"[\w./~-]*[\w-]\.(?:jsonl|mp3|m4a|wav|opus|json|csv|txt|vtt|srt)\b", re.I)
MEDIA_EXT = (".mp3", ".m4a", ".mp4", ".wav", ".opus", ".ogg", ".xml", ".rss")
DELIVERY_HOSTS = ("dts.podtrac.com", "media.blubrry.com", "mcdn.podbean.com", "chtbl.com", "pdst.fm", "pscrb.fm",
                  "traffic.libsyn.com", "anchor.fm", "mgln.ai", "s3.amazonaws.com", "traffic.megaphone.fm")
DELIVERY_SUFFIXES = (".cloudfront.net", ".spreaker.com", ".podtrac.com", ".blubrry.com", ".podbean.com", ".libsyn.com",
                     ".megaphone.fm", ".anchor.fm")
# A turn prefix: "Jim: ", "JIM: ", "Mary Ann: ", "Robert - "; or a bare "Questioner "/"Question "/"Q " opener as the
# L/L Research transcripts write it, with no punctuation at all.
TURN_PREFIX = re.compile(r"^(?:[A-Z][a-z]+|[A-Z]{2,})(?:\s+[A-Z][a-z]+)?\s*[:\-–—]\s")
BARE_TURN = re.compile(r"^(?:Questioner|Question|Q)\s+(?=\S)")
QUESTIONER = re.compile(r"\b(?:Questioner|Q|Caller|Participant|Audience member|Student|Member)\s*[:\-–—]\s*[A-Z][a-z]+", re.I)
BARE_QUESTIONER = re.compile(r"\bQuestioner\s+[A-Z]")       # case-sensitive: "Questioner Since 2011 ..."
EMAIL = re.compile(r"\S+@\S+\.[a-z]{2,}", re.I)
PHONE = re.compile(r"(?:\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")
FORBIDDEN_TAGS = re.compile(r"<\s*(?:audio|video|iframe)\b|data:[\w/+.-]+;base64,", re.I)
ARCHIVE_FILE = re.compile(r"^https://archive\.org/download/([^/?#]+)/")
EDGE_LABELS = {"pre": f"before 1950", "post": f"after {AXIS_END}"}


class GuardError(Exception):
    """The page or its records break a rule of 12.9; nothing is written."""


# ---------------------------------------------------------------- words and dates
def words_of(text):
    """The words of a quote: the ellipsis that quote() appends is not one."""
    return [w for w in (text or "").split() if re.search(r"\w", w)]


def norm_words(text):
    """Lower-cased words with the punctuation at their ends removed; inner punctuation (don't, 12-21-2012) is kept, so
    a word count here is the same count as str.split() gives."""
    out = []
    for w in (text or "").lower().split():
        w = re.sub(r"^[^\w]+|[^\w]+$", "", w)
        if w:
            out.append(w)
    return out


def runs(words, n):
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def date_precision(date_said):
    return {10: "day", 7: "month", 4: "year"}.get(len(date_said or ""), "unknown")


def year_of(date_said):
    m = re.match(r"((?:19|20)\d{2})", date_said or "")
    return int(m.group(1)) if m else None


def item_words(cat_row, kinds=("source",)):
    """The item's word count for the share: for a source text publisher_text_words, else captions_words, else
    asr_words; for speech-to-text made here the smaller of captions_words and asr_words, else publisher_text_words.
    An item quoted in both kinds takes the smaller count. None when none is known."""
    known = {}
    for col in WORD_COLUMNS:
        v = (cat_row.get(col) or "").strip()
        if v.isdigit() and int(v) > 0:
            known[col] = int(v)
    counts = []
    for kind in set(kinds):
        if kind == "made":
            made = [known[c] for c in ("captions_words", "asr_words") if c in known]
            n = min(made) if made else known.get("publisher_text_words")
        else:
            n = next((known[c] for c in WORD_COLUMNS if c in known), None)
        if n:
            counts.append(n)
    return min(counts) if counts else None


def item_kinds(rows):
    """{item_id: set of kinds quoted from it}, so the share denominator fits the text the quotes come from."""
    kinds = collections.defaultdict(set)
    for r in rows:
        kinds[r["item_id"]].add(r["kind"])
    return kinds


def host_of(url):
    m = re.match(r"https?://([^/?#]+)", url or "", re.I)
    return m.group(1).lower() if m else ""


def delivery_host(host):
    return host in DELIVERY_HOSTS or any(host.endswith(s) for s in DELIVERY_SUFFIXES)


def public_address_ok(url):
    """True for an https page address that is neither a media or feed file nor on a delivery host."""
    if not url or not url.lower().startswith("https://"):
        return False
    path = re.sub(r"[?#].*$", "", url).lower()
    return not path.endswith(MEDIA_EXT) and not delivery_host(host_of(url))


def public_link(cat_row):
    """(link, kind) for an item: its source address when that is a public page; else its YouTube twin's page; else
    the archive.org item page behind a file; else (None, None). Never an audio file or a delivery host."""
    url = (cat_row.get("source_url") or "").strip()
    if public_address_ok(url):
        return url, ("page" if cat_row.get("lane") == "web" and cat_row.get("relation") == "page" else "episode page")
    twin = (cat_row.get("twin_of") or "").strip()
    if ID_RE.match(twin):
        return f"https://www.youtube.com/watch?v={twin}", "episode page"
    m = ARCHIVE_FILE.match(url)
    if m:
        return f"https://archive.org/details/{m.group(1)}", "episode page"
    return None, None


def start_year(r):
    return r["window_lo"] if r["window_lo"] is not None else r["window_hi"]


def end_year(r):
    return r["window_hi"] if r["window_hi"] is not None else r["window_lo"]


def sort_key(r):
    return (start_year(r), end_year(r), r.get("date_said") or "9999", r["item_id"], r.get("offset_s") or 0)


def decade_of(year):
    if year < 1950:
        return "pre"
    if year > AXIS_END:
        return "post"
    return str(year // 10 * 10)


def decade_label(key):
    return EDGE_LABELS.get(key, f"{key}s")


def fmt_offset(seconds):
    s = int(seconds or 0)
    return f"{s // 60}:{s % 60:02d}"


def window_label(r):
    lo, hi = r["window_lo"], r["window_hi"]
    if lo is None:
        return f"by {hi}"
    return f"{lo}" if lo == hi else f"{lo} to {hi}"


def said_label(r):
    if not r["date_said"]:
        return "date not known"
    basis = {"title": " (from title)", "source address": " (from address)"}.get(r["date_basis"], "")
    return f"said {r['date_said']}{basis}"


# ---------------------------------------------------------------- the records
def read_private(root):
    """Every candidate row of every person, in file order."""
    rows = []
    for p in sorted((Path(root) / "analysis" / "predictions").glob("*.jsonl")):
        rows.extend(read_jsonl(p))
    return rows


def windowed(rows):
    return [r for r in rows if not r.get("copy") and (r.get("window_lo") is not None or r.get("window_hi") is not None)]


def person_order(rows, people):
    counts = collections.Counter(r["person_id"] for r in rows)
    return sorted(counts, key=lambda p: (-counts[p], people.get(p, {}).get("person_name") or p))


def own_names(people, person_id):
    """The words of this person's own name: the only turn prefixes allowed in their texts ("Suzanne Lie: ...")."""
    return {w for w in (people.get(person_id, {}).get("person_name") or "").split() if len(w) >= 3}


def speaker_turn(sentence, allowed_names):
    """The prefix word when a sentence opens as a turn ("Name: ...", "Question: ...") by someone other than the
    people tracked, else ""."""
    m = TURN_PREFIX.match(sentence or "")
    if m:
        first = m.group(0).split()[0].strip(":-–—")
        if first not in allowed_names and first.title() not in allowed_names:
            return m.group(0).strip()
    m = BARE_TURN.match(sentence or "")
    if m:
        return m.group(0).strip()
    return ""


def build_records(private_rows, catalogue, people, cap=QUOTE_CAP_PER_PERSON, questioners=()):
    """The public records in page order, and the builder's notes (quotes withheld and why, links dropped). Quotes
    are allocated within each item's share budget (floor(5% x words), statements in page order, each taking at
    most 30 words, none under MIN_QUOTE_WORDS) and within the per-person cap; a sentence that opens as a turn by
    someone other than the people tracked, or that names a listed questioner, gets no quote."""
    rows = windowed(private_rows)
    order = person_order(rows, people)
    rows.sort(key=lambda r: (order.index(r["person_id"]), sort_key(r)))
    budgets, person_words, notes = {}, collections.Counter(), {"withheld": [], "links_dropped": [], "unknown_length": []}
    kinds = item_kinds(rows)
    records = []
    for r in rows:
        cat = catalogue.get(r["item_id"]) or {}
        words = item_words(cat, kinds[r["item_id"]])
        if r["item_id"] not in budgets:
            budgets[r["item_id"]] = math.floor(SHARE * words) if words else 0
            if words is None:
                notes["unknown_length"].append(r["item_id"])
        link, page_kind = public_link(cat)
        if link is None and cat.get("source_url"):
            notes["links_dropped"].append(r["item_id"])
        sentence = r.get("sentence") or ""
        length = len(words_of(sentence))
        q, why = None, ""
        turn = speaker_turn(sentence, own_names(people, r["person_id"]))
        named = next((n for n in questioners if n and re.search(rf"\b{re.escape(n)}\b", sentence)), "")
        if turn or named:
            why = "speaker turn" if turn else "named questioner"
        else:
            take = min(QUOTE_WORDS, budgets[r["item_id"]], length)
            if words is None:
                why = "unknown length"
            elif person_words[r["person_id"]] + min(take, length) > cap:
                why = "person cap"
            elif take < min(MIN_QUOTE_WORDS, length):      # a short sentence is quoted whole; a short cut is no quote
                why = "item share"
            else:
                q = quote(sentence, take)
                budgets[r["item_id"]] -= len(words_of(q))
                person_words[r["person_id"]] += len(words_of(q))
        if why:
            notes["withheld"].append({"item_id": r["item_id"], "person_id": r["person_id"], "why": why, "turn": turn,
                                      "words": words})
        p = people.get(r["person_id"], {})
        records.append({"person_id": r["person_id"], "person_name": p.get("person_name") or r["person_id"],
                        "role": p.get("role") or "", "item_id": r["item_id"], "kind": r["kind"],
                        "date_said": r.get("date_said") or "", "date_basis": r.get("date_basis") or "none",
                        "date_precision": date_precision(r.get("date_said")),
                        "window_lo": r["window_lo"], "window_hi": r["window_hi"],
                        "span": r["window_lo"] is not None and r["window_hi"] is not None and r["window_lo"] != r["window_hi"],
                        "conditional": bool(r.get("conditional")), "hedged": bool(r.get("hedged")),
                        "strong": bool(r.get("strong")), "time_expr": r.get("time_expr") or "",
                        "time_rule": r.get("time_rule") or "", "quote": q, "quote_words": len(words_of(q)) if q else 0,
                        "link": link, "offset_s": (round(r["offset_s"], 1) if r["kind"] == "made" and r.get("offset_s") is not None
                                                   else None),
                        "public_page_kind": page_kind})
    return records, notes


# ---------------------------------------------------------------- the guard
class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip, self.scripts = [], 0, []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        self.attrs.extend(v for _, v in attrs if v)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        (self.scripts if self.skip else self.parts).append(data)


def page_text(page):
    """(visible text, attribute values, string values of the embedded JSON data) of the page."""
    p = _Text()
    p.feed(page)
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', page, re.S)
    values = []
    if m:
        def walk(x):
            if isinstance(x, str):
                values.append(x)
            elif isinstance(x, dict):
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(json.loads(m.group(1).replace("<\\/", "</")))
    return " ".join(p.parts), p.attrs, values


def guard(records, catalogue, page, private_rows, people=None, questioners=(), cap=QUOTE_CAP_PER_PERSON):
    """Check the records and the finished page against 12.9; raise GuardError naming every breach, else return the
    counts per check. people: {person_id: targets row} for the allowed turn prefixes."""
    bad, report = [], collections.OrderedDict()
    people = people or {}
    private = [r for r in private_rows if r.get("sentence")]
    by_item_sentence = collections.defaultdict(list)
    for r in private:
        by_item_sentence[r["item_id"]].append(r["sentence"])

    # 1. quote length, in the records and anywhere in the page
    long_quotes = [r["item_id"] for r in records if r.get("quote") and len(words_of(r["quote"])) > QUOTE_WORDS]
    text, attrs, values = page_text(page)
    page_words = norm_words(" ".join([text] + attrs + values))
    page_runs = runs(page_words, QUOTE_WORDS + 1)
    leaked = sorted({r["item_id"] for r in private if runs(norm_words(r["sentence"]), QUOTE_WORDS + 1) & page_runs})
    if long_quotes:
        bad.append(f"quote over {QUOTE_WORDS} words: {sorted(set(long_quotes))}")
    if leaked:
        bad.append(f"more than {QUOTE_WORDS} consecutive words of a private sentence on the page: {leaked}")
    report["quotes"] = sum(1 for r in records if r.get("quote"))

    # 2. item share and per-person cap, recomputed from the records
    by_item = collections.defaultdict(int)
    for r in records:
        by_item[r["item_id"]] += len(words_of(r.get("quote"))) if r.get("quote") else 0
    over, unknown = [], []
    kinds = item_kinds(records)
    for item, quoted in by_item.items():
        words = item_words(catalogue.get(item) or {}, kinds[item])
        if words is None:
            if quoted:
                unknown.append(item)
        elif quoted / words > SHARE + 1e-9:
            over.append(f"{item} ({quoted}/{words})")
    if over:
        bad.append(f"item share over {SHARE:.0%}: {over}")
    if unknown:
        bad.append(f"unknown length, quotes present: {unknown}")
    per_person = collections.Counter()
    for r in records:
        per_person[r["person_id"]] += len(words_of(r.get("quote"))) if r.get("quote") else 0
    capped = [f"{p} ({n})" for p, n in per_person.items() if n > cap]
    if capped:
        bad.append(f"quoted words over the per-person cap of {cap}: {capped}")
    report["items"] = len(by_item)
    report["max_share"] = max((by_item[i] / item_words(catalogue[i], kinds[i]) for i in by_item
                               if i in catalogue and item_words(catalogue[i], kinds[i])), default=0.0)

    # 3. private paths and fields
    hits = [m for m in PRIVATE_MARKS if m in page] + sorted(set(PRIVATE_PATH.findall(page)))
    for cat in catalogue.values():
        for col in PATH_COLUMNS:
            v = (cat.get(col) or "").strip()
            if v and v in page:
                hits.append(v)
    if hits:
        bad.append(f"private path or mark on the page: {hits[:10]}")
    extra = sorted({k for r in records for k in r if k not in PUBLIC_KEYS})
    if extra:
        bad.append(f"record key outside the public allow-list: {extra}")
    for r in records:
        for v in r.values():
            if isinstance(v, str) and (any(m in v for m in PRIVATE_MARKS) or PRIVATE_PATH.search(v)):
                bad.append(f"private path in a record of {r['item_id']}: {v[:60]}")
                break
    report["path_marks"] = len(hits)

    # 4. public addresses
    bad_links = sorted({r["link"] for r in records if r.get("link") and not public_address_ok(r["link"])})
    if bad_links:
        bad.append(f"link is not a public https page: {bad_links}")
    report["links"] = sum(1 for r in records if r.get("link"))

    # 5. questioner names, turn prefixes, third parties
    turns = []
    for r in records:
        q = r.get("quote") or ""
        if not q:
            continue
        if (QUESTIONER.search(q) or BARE_QUESTIONER.search(q) or speaker_turn(q, own_names(people, r["person_id"]))
                or EMAIL.search(q) or PHONE.search(q)):
            turns.append(r["item_id"])
        elif any(n and re.search(rf"\b{re.escape(n)}\b", q) for n in questioners):
            turns.append(r["item_id"])
    if QUESTIONER.search(text) or BARE_QUESTIONER.search(text) or EMAIL.search(text) or PHONE.search(text):
        turns.append("page text")
    if turns:
        bad.append(f"a speaker prefix, a questioner, an address or a number in a quote: {sorted(set(turns))}")
    report["turns_checked"] = len(records)

    # 6. structure
    expected = windowed(private_rows)
    if len(records) != len(expected):
        bad.append(f"{len(records)} records for {len(expected)} windowed distinct candidates")
    missing = sorted({r["item_id"] for r in records if r["item_id"] not in catalogue})
    if missing:
        bad.append(f"item not in the catalogue: {missing}")
    not_prefix = []
    for r in records:
        if r.get("quote"):
            qw = words_of(r["quote"])
            if not any(words_of(s)[:len(qw)] == qw for s in by_item_sentence.get(r["item_id"], [])):
                not_prefix.append(r["item_id"])
    if not_prefix:
        bad.append(f"quote is not a word-for-word prefix of a private sentence: {sorted(set(not_prefix))}")
    if FORBIDDEN_TAGS.search(page):
        bad.append("the page embeds media (audio, video, iframe or a base64 data URI)")
    rest = " ".join([text] + attrs + values)
    # the quotes go first, longest first, then the time expressions: a short expression removed early would cut
    # through a quote and leave its pieces for the five-word check to find
    for s in sorted({r["quote"] for r in records if r.get("quote")}, key=len, reverse=True):
        rest = rest.replace(s, " ")
    for s in sorted({r["time_expr"] for r in records if r.get("time_expr")}, key=len, reverse=True):
        rest = rest.replace(s, " ")
    rest_runs = runs(norm_words(rest), 5)
    leak5 = sorted({r["item_id"] for r in private if runs(norm_words(r["sentence"]), 5) & rest_runs})
    if leak5:
        shown = sorted(set().union(*(runs(norm_words(r["sentence"]), 5) & rest_runs for r in private)))
        bad.append(f"a five-word run of a private sentence outside the quotes: {leak5[:5]} e.g. {shown[:5]}")
    size = len(page.encode("utf-8"))
    if size > PAGE_LIMIT:
        bad.append(f"page is {size} bytes, over {PAGE_LIMIT}")
    report["records"] = len(records)
    report["page_bytes"] = size
    if bad:
        raise GuardError("\n".join(bad))
    return report


# ---------------------------------------------------------------- the page
def esc(x):
    return html.escape(str(x), quote=True)


def suspect(r):
    """A note for a window that starts before the statement's own date, or before 1950 when that date is unknown:
    probably a quoted historical year read as a target. Shown and marked, never dropped."""
    said_year = year_of(r["date_said"])
    if said_year and start_year(r) < said_year:
        return "target before the date said"
    if not said_year and start_year(r) < 1950:
        return "target before 1950"
    return ""


def card_html(i, r):
    kind = "source text" if r["kind"] == "source" else "speech-to-text"
    flags = [f for f, on in (("conditional", r["conditional"]), ("hedged", r["hedged"]), ("strong wording", r["strong"])) if on]
    if suspect(r):
        flags.append(suspect(r))
    flag_html = f'<span class="flags">{" · ".join(flags)}</span>' if flags else ""
    if r["quote"]:
        body = f'<p class="q">“{esc(r["quote"])}”</p>'
    else:
        body = (f'<p class="q q-withheld"><em>{esc(r["time_expr"]) or "(time expression)"}</em> '
                f'<span class="muted">quote withheld, item share limit</span></p>')
    meta = [said_label(r), f'<code>{esc(r["item_id"])}</code>']
    if r["link"]:
        label = "public page" if r["public_page_kind"] == "page" else "episode page"
        if r["kind"] == "made" and r["offset_s"] is not None:
            label += f" · at {fmt_offset(r['offset_s'])}"
        meta.append(f'<a href="{esc(r["link"])}" rel="noopener">{esc(label)}</a>')
    elif r["kind"] == "made" and r["offset_s"] is not None:
        meta.append(f"at {fmt_offset(r['offset_s'])} of the recording, no public page known")
    else:
        meta.append("no public page known")
    return (f'<li class="st" id="s{i}" data-i="{i}" data-start="{start_year(r)}" data-end="{end_year(r)}">'
            f'<div class="st-head"><span class="badge">{esc(window_label(r))}</span>'
            f'<span class="chip chip-{r["kind"]}">{kind}</span>{flag_html}</div>{body}'
            f'<p class="meta">{" · ".join(meta)}</p></li>')


def person_sections(records):
    out, i = [], 0
    for pid, group in group_by_person(records):
        r0 = group[0]
        hedged = sum(r["hedged"] for r in group)
        cond = sum(r["conditional"] for r in group)
        src = sum(r["kind"] == "source" for r in group)
        made = len(group) - src
        targets = [y for r in group for y in (r["window_lo"], r["window_hi"]) if y is not None]
        line = (f"{len(group)} statements · {hedged} hedged · {cond} conditional · earliest target {min(targets)} · "
                f"latest {max(targets)} · {src} from source texts, {made} from speech-to-text")
        cards = []
        for r in group:
            cards.append(card_html(i, r))
            i += 1
        out.append(f'<section class="person" id="p-{esc(pid)}" data-person="{esc(pid)}">'
                   f'<h3>{esc(r0["person_name"])} <span class="role">{esc(r0["role"])}</span></h3>'
                   f'<p class="countline" data-n="{len(group)}">{line}</p>'
                   f'<ol class="cards">{"".join(cards)}</ol>'
                   f'<button type="button" class="more" hidden>show all {len(group)}</button></section>')
    return "\n".join(out)


def group_by_person(records):
    groups = collections.OrderedDict()
    for r in records:
        groups.setdefault(r["person_id"], []).append(r)
    return groups.items()


def year_index_html(records):
    by_year = collections.defaultdict(collections.Counter)
    for r in records:
        by_year[decade_key_or_year(start_year(r))][r["person_name"]] += 1
    keys = sorted(by_year, key=lambda k: (-1 if k == "pre" else (10 ** 6 if k == "post" else int(k))))
    rows = []
    for k in keys:
        label = EDGE_LABELS.get(k, k)
        chips = " ".join(f'<span class="pchip">{esc(n)} <b>{c}</b></span>' for n, c in by_year[k].most_common())
        rows.append(f'<li><button type="button" class="year" data-year="{esc(k)}">{label}</button> '
                    f'<span class="ycount">{sum(by_year[k].values())}</span> {chips}</li>')
    return "\n".join(rows)


def decade_key_or_year(year):
    return "pre" if year < 1950 else ("post" if year > AXIS_END else str(year))


def filters_html(records):
    counts = collections.Counter(r["person_id"] for r in records)
    names = {r["person_id"]: r["person_name"] for r in records}
    order = [p for p, _ in group_by_person(records)]
    chips = "".join(f'<button type="button" class="pchip pbtn" data-person="{esc(p)}" aria-pressed="false">'
                    f'{esc(names[p])} <b>{counts[p]}</b></button>' for p in order)
    options = "".join(f'<option value="{esc(p)}">{esc(names[p])} ({counts[p]})</option>' for p in order)
    decades = sorted({d for r in records for d in decades_of(r)}, key=lambda k: (-1 if k == "pre" else (10 ** 6 if k == "post" else int(k))))
    boxes = "".join(f'<label class="check"><input type="checkbox" name="decade" value="{esc(d)}"> {decade_label(d)}</label>'
                    for d in decades)
    strong = sum(r["strong"] for r in records)
    return f"""
<form id="filters" class="needs-js" autocomplete="off">
  <div class="frow">
    <fieldset class="fset fset-people"><legend>Person</legend>
      <div class="chips">{chips}<button type="button" class="pchip pall" id="people-all">all</button></div>
      <label class="sr-only" for="people-select">People</label>
      <select id="people-select" multiple size="3" class="sr-only">{options}</select>
    </fieldset>
    <fieldset class="fset"><legend>Kind of text</legend>
      <label class="check"><input type="radio" name="kind" value="all" checked> all</label>
      <label class="check"><input type="radio" name="kind" value="source"> source text</label>
      <label class="check"><input type="radio" name="kind" value="made"> speech-to-text made here</label>
    </fieldset>
    <fieldset class="fset"><legend>Target decade</legend>
      <div class="checks">{boxes}</div>
      <button type="button" class="pchip" id="next-five">next five years ({BUILD_YEAR} to {BUILD_YEAR + 4})</button>
    </fieldset>
    <fieldset class="fset"><legend>Conditional or hedged</legend>
      <label class="check"><input type="radio" name="flags" value="all" checked> all</label>
      <label class="check"><input type="radio" name="flags" value="flagged"> only conditional or hedged</label>
      <label class="check"><input type="radio" name="flags" value="plain"> only unconditional and unhedged</label>
      <label class="check small"><input type="checkbox" name="strong" value="1"> strong wording only ({strong})</label>
    </fieldset>
    <fieldset class="fset fset-q"><legend>Search</legend>
      <label class="sr-only" for="q">Search person, quote and time expression</label>
      <input type="search" id="q" name="q" placeholder="person, quote or time expression">
      <button type="button" id="reset">reset</button>
    </fieldset>
  </div>
  <p class="status"><span id="showing" aria-live="polite">showing {len(records)} of {len(records)}</span>
  <span id="hidden-people" class="muted"></span></p>
</form>"""


def decades_of(r):
    lo, hi = start_year(r), end_year(r)
    out, y = [], lo
    while y <= hi:
        k = decade_of(y)
        if k not in out:
            out.append(k)
        if k == "post":
            break
        y = 1950 if k == "pre" else y // 10 * 10 + 10
    return out


CSS = """
:root{--bg:#fbfbfa;--fg:#1a1a19;--fg-muted:#5c5b57;--border:#d9d8d3;--surface:#ffffff;--accent:#1f5fb0;
--series-source:#2b5fb3;--series-made:#b05a1a;--series-source-soft:#a9bfe6;--series-made-soft:#e3b89a;--flag:#8a8984;color-scheme:light}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#17191d;--fg:#eceae4;--fg-muted:#b2b0a8;--border:#3a3d44;
--surface:#1f2228;--accent:#7fa8ee;--series-source:#4f86de;--series-made:#c97c30;--series-source-soft:#2c4a80;--series-made-soft:#7a4a1c;--flag:#8a8d94;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#17191d;--fg:#eceae4;--fg-muted:#b2b0a8;--border:#3a3d44;--surface:#1f2228;--accent:#7fa8ee;
--series-source:#4f86de;--series-made:#c97c30;--series-source-soft:#2c4a80;--series-made-soft:#7a4a1c;--flag:#8a8d94;color-scheme:dark}
*{box-sizing:border-box}
html{overflow-x:hidden}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;overflow-wrap:anywhere}
.wrap{max-width:72rem;margin:0 auto;padding:0 16px}
code,.badge,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.92em}
a{color:var(--accent)}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,[tabindex]:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1{font-size:2rem;line-height:1.15;margin:.2rem 0 .6rem;font-weight:600}
h2{font-size:1.35rem;margin:2.2rem 0 .6rem}
h3{font-size:1.1rem;margin:0 0 .2rem}
.eyebrow,.muted,.meta,.flags,.role,.countline,.status{color:var(--fg-muted)}
.eyebrow{font-size:.85rem;text-transform:uppercase;letter-spacing:.04em;margin-top:1.5rem}
.lead{max-width:60ch;font-size:1.05rem}
.gen{font-size:.85rem}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,10rem),1fr));gap:.75rem;margin:1rem 0}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:.8rem 1rem}
.tile b{display:block;font-size:1.8rem;font-weight:600;font-variant-numeric:tabular-nums}
.caveat{border:1px solid var(--flag);border-left-width:4px;border-radius:6px;padding:.7rem 1rem;background:var(--surface);max-width:80ch}
.caveat p{margin:.3rem 0}
#filters{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:.6rem 1rem;margin:1.2rem 0}
@media (min-width:60rem){#filters{position:sticky;top:0;z-index:5;max-height:60vh;overflow:auto}}
.frow{display:grid;gap:.6rem 1.2rem;grid-template-columns:repeat(auto-fit,minmax(min(100%,15rem),1fr))}
.fset{border:0;padding:0;margin:0;min-width:0}
.fset legend{font-size:.8rem;color:var(--fg-muted);padding:0;margin-bottom:.2rem}
.fset-people{grid-column:1/-1}
.chips,.checks{display:flex;flex-wrap:wrap;gap:.3rem .4rem}
.check{display:inline-flex;align-items:center;gap:.3rem;font-size:.9rem;margin-right:.6rem}
.check.small{font-size:.8rem}
.pchip,.year,#reset,.more,.seg label{font:inherit;font-size:.85rem;color:var(--fg);background:transparent;border:1px solid var(--border);border-radius:999px;padding:.15rem .6rem;cursor:pointer}
.pchip b{font-weight:500;color:var(--fg-muted)}
.pbtn[aria-pressed="true"]{border-color:var(--fg);box-shadow:inset 0 0 0 1px var(--fg)}
#q{font:inherit;font-size:.9rem;color:var(--fg);background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:.3rem .5rem;width:min(100%,22rem)}
.status{margin:.5rem 0 0;font-size:.9rem}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.no-js .needs-js{display:none}
.seg{display:inline-flex;border:1px solid var(--border);border-radius:999px;overflow:hidden;margin:0 0 .6rem}
.seg label{border:0;border-radius:0;padding:.2rem .9rem}
.seg input{position:absolute;opacity:0;pointer-events:none}
.seg input:checked+span{font-weight:600}
.seg label:has(input:checked){background:var(--border)}
.seg label:has(input:focus-visible){outline:2px solid var(--accent);outline-offset:-2px}
.legend{display:flex;flex-wrap:wrap;gap:.3rem 1.1rem;list-style:none;padding:0;margin:0 0 .6rem;font-size:.85rem;color:var(--fg-muted)}
.legend li{display:inline-flex;align-items:center;gap:.4rem}
.legend svg{width:14px;height:14px;overflow:visible}
.chartwrap{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:.6rem .4rem}
.chartwrap svg{display:block;width:100%;height:auto;font-size:12px}
.chartwrap text{fill:var(--fg-muted)}
.chartwrap .rowlabel{fill:var(--fg)}
.chartwrap .serieslabel{fill:var(--fg)}
.chartwrap .axis line,.chartwrap .axis path{stroke:var(--border)}
.chartwrap .now{stroke:var(--fg-muted);stroke-dasharray:3 3}
.chartwrap .mark{cursor:pointer}
.chartwrap .mark:focus{outline:none}
.chartwrap .mark:focus .hit,.chartwrap .mark:hover .hit{stroke:var(--accent);stroke-width:1.5;fill:transparent}
.hit{fill:transparent;stroke:none}
.m-source{fill:var(--series-source);stroke:var(--series-source)}
.m-made{fill:var(--series-made);stroke:var(--series-made)}
.hollow{fill:var(--surface)!important;stroke-width:1.5}
.ring{fill:none;stroke:var(--fg);stroke-width:1}
.clip{stroke:var(--fg-muted);stroke-width:1.5}
.bar-source{fill:var(--series-source-soft);opacity:.6}
.bar-made{fill:var(--series-made-soft);opacity:.6}
.badgecount{fill:var(--fg-muted);font-size:10px}
.tip{position:absolute;z-index:10;max-width:22rem;background:var(--surface);color:var(--fg);border:1px solid var(--border);border-radius:6px;padding:.5rem .7rem;font-size:.85rem;box-shadow:0 2px 8px rgba(0,0,0,.12);pointer-events:none}
.tip b{display:block}
.tip .muted{font-size:.8rem}
.tablewrap{overflow:auto;border:1px solid var(--border);border-radius:8px;background:var(--surface);max-height:36rem}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{text-align:left;vertical-align:top;padding:.35rem .5rem;border-bottom:1px solid var(--border)}
th{position:sticky;top:0;background:var(--surface);color:var(--fg-muted);font-weight:500;white-space:nowrap}
th button{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer}
th[aria-sort="ascending"] button::after{content:" \\2191"}
th[aria-sort="descending"] button::after{content:" \\2193"}
.person{margin:1.4rem 0;padding-top:.6rem;border-top:1px solid var(--border)}
.countline{font-size:.9rem;margin:0 0 .5rem}
.cards{list-style:none;padding:0;margin:0;display:grid;gap:.5rem}
.st{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:.6rem .8rem}
.st.flash{outline:2px solid var(--accent);outline-offset:2px}
.st-head{display:flex;flex-wrap:wrap;gap:.4rem .7rem;align-items:center;font-size:.85rem}
.badge{border:1px solid var(--border);border-radius:4px;padding:0 .4rem;background:var(--bg)}
.chip{padding-left:.5rem;border-left:4px solid var(--flag);color:var(--fg)}
.chip-source{border-left-color:var(--series-source)}
.chip-made{border-left-color:var(--series-made)}
.q{margin:.35rem 0}
.q-withheld .muted{font-size:.85rem}
.meta{font-size:.85rem;margin:0}
.more{margin-top:.5rem}
#years ul{list-style:none;padding:0;margin:0;display:grid;gap:.25rem;font-size:.88rem}
#years li{display:flex;flex-wrap:wrap;gap:.25rem .4rem;align-items:center}
.year{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.ycount{color:var(--fg-muted);min-width:2ch}
#years .pchip{font-size:.8rem;padding:0 .45rem;cursor:default}
.methods{max-width:80ch}
.methods dt{font-weight:600;margin-top:.6rem}
.methods dd{margin:0 0 .2rem}
footer{margin:3rem 0 2rem;color:var(--fg-muted);font-size:.9rem;border-top:1px solid var(--border);padding-top:1rem}
"""

JS = r"""
(function () {
  'use strict';
  document.documentElement.classList.remove('no-js');
  var DATA = JSON.parse(document.getElementById('data').textContent);
  var AXIS_END = __AXIS_END__, NOW = __BUILD_YEAR__, SHOWN = __CARDS_SHOWN__;
  DATA.forEach(function (d, i) {
    d.i = i; d.start = d.window_lo !== null ? d.window_lo : d.window_hi; d.end = d.window_hi !== null ? d.window_hi : d.window_lo;
    d.decades = decadesOf(d.start, d.end); d.search = (d.person_name + ' ' + (d.quote || '') + ' ' + d.time_expr).toLowerCase();
  });
  var PEOPLE = [], seen = {};
  DATA.forEach(function (d) { if (!seen[d.person_id]) { seen[d.person_id] = true; PEOPLE.push({ id: d.person_id, name: d.person_name }); } });
  var state = { people: {}, kind: 'all', decades: {}, flags: 'all', strong: false, q: '' };
  var expanded = {}, view = 'chart', sort = { key: '', dir: 0 }, visible = DATA;
  var form = document.getElementById('filters'), chartEl = document.getElementById('chart'), tip = document.getElementById('tip');

  function decadeOf(y) { return y < 1950 ? 'pre' : (y > AXIS_END ? 'post' : String(Math.floor(y / 10) * 10)); }
  function decadesOf(lo, hi) {
    var out = [], y = lo;
    while (y <= hi) { var k = decadeOf(y); if (out.indexOf(k) < 0) out.push(k); if (k === 'post') break; y = k === 'pre' ? 1950 : Math.floor(y / 10) * 10 + 10; }
    return out;
  }
  function has(set) { return Object.keys(set).length > 0; }
  function matches(d) {
    if (has(state.people) && !state.people[d.person_id]) return false;
    if (state.kind !== 'all' && d.kind !== state.kind) return false;
    if (has(state.decades) && !d.decades.some(function (k) { return state.decades[k]; })) return false;
    if (state.flags === 'flagged' && !(d.conditional || d.hedged)) return false;
    if (state.flags === 'plain' && (d.conditional || d.hedged)) return false;
    if (state.strong && !d.strong) return false;
    if (state.q && d.search.indexOf(state.q) < 0) return false;
    return true;
  }
  function windowLabel(d) { return d.window_lo === null ? 'by ' + d.window_hi : (d.window_lo === d.window_hi ? String(d.window_lo) : d.window_lo + ' to ' + d.window_hi); }
  function saidLabel(d) {
    if (!d.date_said) return 'date not known';
    var basis = d.date_basis === 'title' ? ' (from title)' : (d.date_basis === 'source address' ? ' (from address)' : '');
    return 'said ' + d.date_said + basis;
  }
  function kindLabel(d) { return d.kind === 'source' ? 'source text' : 'speech-to-text'; }
  function flagsOf(d) { var f = []; if (d.conditional) f.push('conditional'); if (d.hedged) f.push('hedged'); if (d.strong) f.push('strong wording'); return f; }
  function offset(s) { s = Math.floor(s); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function tipText(d) {
    return [d.person_name, 'target ' + windowLabel(d), d.quote ? '“' + d.quote + '”' : 'quote withheld; time expression: ' + d.time_expr,
      saidLabel(d), kindLabel(d) + (flagsOf(d).length ? ', ' + flagsOf(d).join(', ') : ''), d.item_id, 'labelled candidate'].join('. ');
  }

  // ---- filters -> state -> everything
  function readForm() {
    state.kind = form.querySelector('input[name=kind]:checked').value;
    state.flags = form.querySelector('input[name=flags]:checked').value;
    state.strong = form.querySelector('input[name=strong]').checked;
    state.q = form.querySelector('#q').value.trim().toLowerCase();
    state.decades = {};
    form.querySelectorAll('input[name=decade]:checked').forEach(function (b) { state.decades[b.value] = true; });
    state.people = {};
    Array.prototype.forEach.call(form.querySelector('#people-select').selectedOptions, function (o) { state.people[o.value] = true; });
  }
  function writeForm() {
    form.querySelector('input[name=kind][value="' + state.kind + '"]').checked = true;
    form.querySelector('input[name=flags][value="' + state.flags + '"]').checked = true;
    form.querySelector('input[name=strong]').checked = state.strong;
    form.querySelector('#q').value = state.q;
    form.querySelectorAll('input[name=decade]').forEach(function (b) { b.checked = !!state.decades[b.value]; });
    Array.prototype.forEach.call(form.querySelector('#people-select').options, function (o) { o.selected = !!state.people[o.value]; });
    form.querySelectorAll('.pbtn').forEach(function (b) { b.setAttribute('aria-pressed', state.people[b.dataset.person] ? 'true' : 'false'); });
  }
  function writeHash() {
    var parts = [];
    if (has(state.people)) parts.push('p=' + Object.keys(state.people).join(','));
    if (state.kind !== 'all') parts.push('k=' + state.kind);
    if (has(state.decades)) parts.push('d=' + Object.keys(state.decades).join(','));
    if (state.flags !== 'all') parts.push('f=' + state.flags);
    if (state.strong) parts.push('s=1');
    if (state.q) parts.push('q=' + encodeURIComponent(state.q));
    var h = parts.length ? '#' + parts.join('&') : '';
    if (h !== location.hash) history.replaceState(null, '', h || location.pathname + location.search);
  }
  function readHash() {
    try {
      var h = location.hash.replace(/^#/, ''); if (!h) return;
      h.split('&').forEach(function (kv) {
        var k = kv.split('=')[0], v = decodeURIComponent(kv.slice(k.length + 1) || '');
        if (k === 'p') v.split(',').forEach(function (p) { if (seen[p]) state.people[p] = true; });
        else if (k === 'k' && (v === 'source' || v === 'made')) state.kind = v;
        else if (k === 'd') v.split(',').forEach(function (d) { if (d === 'pre' || d === 'post' || /^\d{4}$/.test(d)) state.decades[d] = true; });
        else if (k === 'f' && (v === 'flagged' || v === 'plain')) state.flags = v;
        else if (k === 's') state.strong = v === '1';
        else if (k === 'q') state.q = v.slice(0, 100).toLowerCase();
      });
    } catch (e) { state = { people: {}, kind: 'all', decades: {}, flags: 'all', strong: false, q: '' }; }
  }
  function applyFilters() {
    visible = DATA.filter(matches);
    document.getElementById('showing').textContent = 'showing ' + visible.length + ' of ' + DATA.length;
    var vis = {}; visible.forEach(function (d) { vis[d.i] = true; });
    var hiddenPeople = 0;
    document.querySelectorAll('.person').forEach(function (sec) {
      var n = 0;
      sec.querySelectorAll('.st').forEach(function (li) {
        var on = !!vis[li.dataset.i]; if (on) n++;
        li.hidden = !on || (!expanded[sec.dataset.person] && n > SHOWN);
      });
      sec.hidden = n === 0; if (n === 0) hiddenPeople++;
      var btn = sec.querySelector('.more');
      btn.hidden = n <= SHOWN || !!expanded[sec.dataset.person]; btn.textContent = 'show all ' + n;
    });
    document.getElementById('hidden-people').textContent = hiddenPeople ? ' · hidden by filters: ' + hiddenPeople + ' people' : '';
    renderYears(); if (view === 'chart') renderChart(visible, chartEl.clientWidth); else renderTable(visible);
    writeHash();
  }
  form.addEventListener('change', function () { readForm(); writeForm(); applyFilters(); });
  form.addEventListener('input', function (e) { if (e.target.id === 'q') { readForm(); applyFilters(); } });
  form.addEventListener('submit', function (e) { e.preventDefault(); });
  form.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    if (b.classList.contains('pbtn')) { readForm(); if (state.people[b.dataset.person]) delete state.people[b.dataset.person]; else state.people[b.dataset.person] = true; }
    else if (b.id === 'people-all') { readForm(); state.people = {}; }
    else if (b.id === 'next-five') { readForm(); state.decades = {}; decadesOf(NOW, NOW + 4).forEach(function (k) { state.decades[k] = true; }); }
    else if (b.id === 'reset') { state = { people: {}, kind: 'all', decades: {}, flags: 'all', strong: false, q: '' }; }
    else return;
    writeForm(); applyFilters();
  });
  document.getElementById('people').addEventListener('click', function (e) {
    var b = e.target.closest('.more'); if (!b) return;
    expanded[b.closest('.person').dataset.person] = true; applyFilters();
  });
  document.querySelectorAll('input[name=view]').forEach(function (r) {
    r.addEventListener('change', function () {
      view = r.value; chartEl.parentNode.hidden = view !== 'chart'; document.getElementById('tablewrap').hidden = view !== 'table';
      if (view === 'chart') renderChart(visible, chartEl.clientWidth); else renderTable(visible);
    });
  });

  // ---- year index
  function renderYears() {
    var by = {}, ul = document.getElementById('yearlist');
    visible.forEach(function (d) { var k = d.start < 1950 ? 'pre' : (d.start > AXIS_END ? 'post' : String(d.start)); (by[k] = by[k] || {})[d.person_name] = ((by[k] || {})[d.person_name] || 0) + 1; });
    var keys = Object.keys(by).sort(function (a, b) { return rank(a) - rank(b); });
    function rank(k) { return k === 'pre' ? -1 : (k === 'post' ? 1e6 : +k); }
    ul.textContent = '';
    keys.forEach(function (k) {
      var li = document.createElement('li'), b = document.createElement('button'), n = document.createElement('span'), total = 0;
      b.type = 'button'; b.className = 'year'; b.dataset.year = k; b.textContent = k === 'pre' ? 'before 1950' : (k === 'post' ? 'after ' + AXIS_END : k);
      li.appendChild(b);
      Object.keys(by[k]).sort(function (a, c) { return by[k][c] - by[k][a]; }).forEach(function (name) {
        total += by[k][name]; var s = document.createElement('span'); s.className = 'pchip'; s.textContent = name + ' ';
        var bb = document.createElement('b'); bb.textContent = by[k][name]; s.appendChild(bb); li.appendChild(s);
      });
      n.className = 'ycount'; n.textContent = total; li.insertBefore(n, b.nextSibling); ul.appendChild(li);
    });
  }
  document.getElementById('years').addEventListener('click', function (e) {
    var b = e.target.closest('.year'); if (!b) return;
    var k = b.dataset.year, dec = k === 'pre' || k === 'post' ? k : decadeOf(+k);
    readForm(); state.decades = {}; state.decades[dec] = true; writeForm(); applyFilters();
    var first = visible.filter(function (d) { return d.decades.indexOf(dec) >= 0; })[0];
    if (first) goTo(first.i);
  });
  function goTo(i) {
    var li = document.getElementById('s' + i), sec = li.closest('.person');
    if (li.hidden) { expanded[sec.dataset.person] = true; applyFilters(); }
    li.scrollIntoView({ behavior: 'smooth', block: 'center' }); li.classList.add('flash');
    setTimeout(function () { li.classList.remove('flash'); }, 2000);
  }

  // ---- table view
  var COLS = [['person_name', 'person'], ['date_said', 'date said'], ['date_basis', 'basis'], ['start', 'target window'], ['kind', 'kind'], ['flags', 'flags'], ['quote', 'quote'], ['link', 'link']];
  function renderTable(rows) {
    var table = document.getElementById('table'), thead = table.tHead, tbody = table.tBodies[0];
    if (!thead.rows.length) {
      var tr = thead.insertRow();
      COLS.forEach(function (c) {
        var th = document.createElement('th'), b = document.createElement('button'); b.type = 'button'; b.textContent = c[1]; b.dataset.key = c[0];
        b.addEventListener('click', function () { sort = sort.key === c[0] ? { key: c[0], dir: sort.dir === 1 ? -1 : (sort.dir === -1 ? 0 : 1) } : { key: c[0], dir: 1 }; renderTable(visible); });
        th.appendChild(b); tr.appendChild(th);
      });
    }
    thead.querySelectorAll('th').forEach(function (th) { var k = th.firstChild.dataset.key; if (sort.dir && k === sort.key) th.setAttribute('aria-sort', sort.dir > 0 ? 'ascending' : 'descending'); else th.removeAttribute('aria-sort'); });
    rows = rows.slice();
    if (sort.dir) rows.sort(function (a, b) { var x = a[sort.key], y = b[sort.key]; if (sort.key === 'flags') { x = flagsOf(a).join(); y = flagsOf(b).join(); } x = x === null ? '' : x; y = y === null ? '' : y; return (x < y ? -1 : (x > y ? 1 : 0)) * sort.dir; });
    tbody.textContent = '';
    rows.forEach(function (d) {
      var tr = tbody.insertRow();
      cell(tr, d.person_name); cell(tr, d.date_said || '—'); cell(tr, d.date_basis);
      var w = cell(tr, ''); var badge = document.createElement('span'); badge.className = 'badge'; badge.textContent = windowLabel(d); w.appendChild(badge);
      var kc = cell(tr, ''); var chip = document.createElement('span'); chip.className = 'chip chip-' + d.kind; chip.textContent = kindLabel(d); kc.appendChild(chip);
      cell(tr, flagsOf(d).join(', ')); cell(tr, d.quote ? '“' + d.quote + '”' : '(withheld) ' + d.time_expr);
      var lc = cell(tr, '');
      if (d.link) { var a = document.createElement('a'); a.href = d.link; a.rel = 'noopener'; a.textContent = (d.public_page_kind === 'page' ? 'public page' : 'episode page') + (d.kind === 'made' && d.offset_s !== null ? ' · at ' + offset(d.offset_s) : ''); lc.appendChild(a); }
      else lc.textContent = d.item_id;
    });
  }
  function cell(tr, text) { var td = tr.insertCell(); td.textContent = text; return td; }

  // ---- chart: one row per person, a mark per statement at its first target year, a bar to its last
  function svgEl(name, attrs, parent) { var el = document.createElementNS('http://www.w3.org/2000/svg', name); for (var k in attrs) el.setAttribute(k, attrs[k]); if (parent) parent.appendChild(el); return el; }
  function renderChart(rows, width) {
    width = Math.max(320, width || 800);
    var narrow = width < 560, labelW = narrow ? 72 : 120, rowH = narrow ? 22 : 28, top = 26, bottom = 34, right = narrow ? 14 : 110;
    var counts = {}; rows.forEach(function (d) { counts[d.person_id] = (counts[d.person_id] || 0) + 1; });
    var people = PEOPLE.filter(function (p) { return counts[p.id]; });
    var height = top + Math.max(1, people.length) * rowH + bottom;
    var minLo = rows.reduce(function (m, d) { return Math.min(m, d.start); }, Infinity);
    var x0 = Math.max(1950, isFinite(minLo) ? minLo : 1950), x1 = AXIS_END;
    x0 = Math.floor(x0 / 10) * 10;
    function x(y) { return labelW + (Math.min(Math.max(y, x0), x1) - x0) / (x1 - x0) * (width - labelW - right); }
    chartEl.textContent = '';
    var years = rows.map(function (d) { return d.start; }).concat(rows.map(function (d) { return d.end; }));
    var svg = svgEl('svg', { viewBox: '0 0 ' + width + ' ' + height, width: '100%', height: height, role: 'group',
      'aria-label': rows.length + ' statements across ' + people.length + ' people, target years from ' + (years.length ? Math.min.apply(null, years) : '') + ' to ' + (years.length ? Math.max.apply(null, years) : '') }, chartEl);
    var axis = svgEl('g', { 'class': 'axis' }, svg), yAxis = top + people.length * rowH;
    svgEl('path', { d: 'M' + labelW + ' ' + yAxis + 'H' + (width - right), fill: 'none' }, axis);
    for (var y = x0; y <= x1; y += 5) {
      var major = y % 10 === 0; if (!major && narrow) continue;
      svgEl('line', { x1: x(y), x2: x(y), y1: yAxis, y2: yAxis + (major ? 6 : 3) }, axis);
      if (major && (!narrow || y % 20 === 0)) svgEl('text', { x: x(y), y: yAxis + 20, 'text-anchor': 'middle' }, axis).textContent = y;
      if (major) svgEl('line', { x1: x(y), x2: x(y), y1: top - 4, y2: yAxis, 'stroke-opacity': .5 }, axis);
    }
    if (NOW >= x0 && NOW <= x1) { svgEl('line', { 'class': 'now', x1: x(NOW), x2: x(NOW), y1: top - 10, y2: yAxis }, svg); svgEl('text', { x: x(NOW), y: top - 12, 'text-anchor': 'middle' }, svg).textContent = 'now'; }
    if (!narrow) { svgEl('text', { 'class': 'serieslabel', x: width - right + 10, y: top + 12 }, svg).textContent = 'source text: circle'; svgEl('text', { 'class': 'serieslabel', x: width - right + 10, y: top + 28 }, svg).textContent = 'speech-to-text: diamond'; }
    people.forEach(function (p, r) {
      var cy = top + r * rowH + rowH / 2, maxChars = narrow ? 9 : 15;
      var label = svgEl('text', { 'class': 'rowlabel', x: labelW - 8, y: cy + 4, 'text-anchor': 'end' }, svg);
      label.textContent = p.name.length > maxChars ? p.name.slice(0, maxChars - 1) + '…' : p.name;
      svgEl('title', {}, label).textContent = p.name + ': ' + counts[p.id] + ' statements found';
      var mine = rows.filter(function (d) { return d.person_id === p.id; }), groups = {};
      mine.forEach(function (d) { (groups[d.start] = groups[d.start] || []).push(d); });
      Object.keys(groups).forEach(function (k) {
        var g = groups[k], n = g.length, stacks = Math.min(n, 5);
        g.forEach(function (d, j) {
          var dy = j < 5 ? (j - (stacks - 1) / 2) * 4 : ((j * 7) % (rowH - 8)) - (rowH - 8) / 2, py = cy + dy, px = x(d.start);
          var mark = svgEl('g', { 'class': 'mark', tabindex: 0, role: 'button', 'aria-label': tipText(d), 'data-i': d.i }, svg);
          if (d.end > d.start) svgEl('rect', { 'class': 'bar-' + d.kind, x: px, y: py - 1.5, width: Math.max(1, x(d.end) - px), height: 3 }, mark);
          var cls = 'm-' + d.kind + ((d.conditional || d.hedged) ? ' hollow' : '');
          if (d.start < x0) { svgEl('line', { 'class': 'clip', x1: px - 8, x2: px - 8, y1: py - 5, y2: py + 5 }, mark); svgEl('path', { 'class': cls, d: 'M' + (px - 6) + ' ' + py + 'l6 -4v8z' }, mark); }
          else if (d.window_lo === null) svgEl('path', { 'class': cls, d: 'M' + (px - 6) + ' ' + py + 'l6 -4v8z' }, mark);
          else if (d.kind === 'source') svgEl('circle', { 'class': cls, cx: px, cy: py, r: 3 }, mark);
          else svgEl('path', { 'class': cls, d: 'M' + px + ' ' + (py - 4) + 'l4 4-4 4-4-4z' }, mark);
          if (d.strong) svgEl('circle', { 'class': 'ring', cx: px, cy: py, r: 5 }, mark);
          svgEl('circle', { 'class': 'hit', cx: px, cy: py, r: 10 }, mark);
          mark.addEventListener('mouseenter', function () { showTip(d, mark); }); mark.addEventListener('focus', function () { showTip(d, mark); });
          mark.addEventListener('mouseleave', hideTip); mark.addEventListener('blur', hideTip);
          mark.addEventListener('click', function () { goTo(d.i); });
          mark.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); goTo(d.i); } });
        });
        if (n > 5) svgEl('text', { 'class': 'badgecount', x: x(+k) + 8, y: cy - rowH / 2 + 9 }, svg).textContent = '×' + n;
      });
    });
    if (!rows.length) svgEl('text', { x: width / 2, y: height / 2, 'text-anchor': 'middle' }, svg).textContent = 'no statements match the filters';
  }
  function showTip(d, mark) {
    tip.textContent = '';
    var b = document.createElement('b'); b.textContent = d.person_name + ' · ' + windowLabel(d); tip.appendChild(b);
    var q = document.createElement('div'); q.textContent = d.quote ? '“' + d.quote + '”' : 'quote withheld; time expression: ' + d.time_expr; tip.appendChild(q);
    var m = document.createElement('div'); m.className = 'muted'; m.textContent = [saidLabel(d), kindLabel(d) + (flagsOf(d).length ? ', ' + flagsOf(d).join(', ') : ''), d.item_id, 'labelled candidate'].join(' · '); tip.appendChild(m);
    tip.hidden = false;
    var wrap = chartEl.parentNode.getBoundingClientRect(), r = mark.getBoundingClientRect();
    var left = Math.min(r.left - wrap.left + 12, wrap.width - tip.offsetWidth - 8), topPx = r.top - wrap.top + 14;
    tip.style.left = Math.max(0, left) + 'px'; tip.style.top = topPx + 'px';
  }
  function hideTip() { tip.hidden = true; }
  var resizeTimer; window.addEventListener('resize', function () { clearTimeout(resizeTimer); resizeTimer = setTimeout(function () { if (view === 'chart') renderChart(visible, chartEl.clientWidth); }, 150); });

  // with JS the person chips do the work; the fallback select leaves the tab order so it is not a blind focus stop
  var sel = form.querySelector('#people-select'); sel.tabIndex = -1; sel.setAttribute('aria-hidden', 'true');
  readHash(); writeForm(); applyFilters();
})();
"""


def render_page(records, counts_text, built):
    people = {r["person_id"] for r in records}
    items = {r["item_id"] for r in records}
    undated = sum(1 for r in records if not r["date_said"])
    from_address = sum(1 for r in records if r["date_basis"] == "source address")
    from_title = sum(1 for r in records if r["date_basis"] == "title")
    predate = [r for r in records if suspect(r)]
    earliest = min(start_year(r) for r in records) if records else ""
    withheld = sum(1 for r in records if not r["quote"])
    data = json.dumps(records, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    legend = """
<ul class="legend" aria-label="legend">
 <li><svg viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="7" r="4" class="m-source"/></svg> filled circle: source text</li>
 <li><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M7 2l5 5-5 5-5-5z" class="m-made"/></svg> filled diamond: speech-to-text made here</li>
 <li><svg viewBox="0 0 14 14" aria-hidden="true"><circle cx="7" cy="7" r="4" class="m-source hollow"/></svg> hollow mark: conditional or hedged</li>
 <li><svg viewBox="0 0 14 14" aria-hidden="true"><rect x="0" y="5" width="14" height="3" class="bar-source" style="opacity:1"/></svg> bar: target span</li>
 <li><svg viewBox="0 0 14 14" aria-hidden="true"><path d="M1 7l7 -4v8z" class="m-source"/></svg> triangle: upper bound only (“by …”)</li>
 <li><svg viewBox="0 0 14 14" aria-hidden="true"><line x1="1" x2="1" y1="2" y2="12" class="clip"/><path d="M3 7l7 -4v8z" class="m-source"/></svg> bar and triangle: starts before the axis, drawn at its left edge</li>
</ul>"""
    body = f"""<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prediction timelines</title>
<meta name="description" content="Candidate statements about the future found by rules in the texts of ET channelers, laid out by target year, with the date said and a short quote linking to the public copy.">
<style>{CSS}</style>
</head>
<body>
<header class="wrap">
<p class="eyebrow">ET channelers · candidate statements about the future</p>
<h1>Prediction timelines</h1>
<p class="lead">{len(records)} statements that name a target year or span, from {len(people)} people and {len(items)} recordings or pages, found by rules in source texts and in speech-to-text made here.</p>
<p class="gen muted">Generated {esc(built)} from {len(items)} items. {counts_text}</p>
<div class="tiles">
 <div class="tile"><b>{len(records)}</b> statements with a target window</div>
 <div class="tile"><b>{len(people)}</b> people</div>
 <div class="tile"><b>{len(items)}</b> recordings or pages</div>
</div>
<div class="caveat" role="note">
<p><strong>These are labelled candidates, not confirmed predictions.</strong> Rules flagged them; a third blinded sample put real predictions at about 56% of windowed candidates (95% interval about 47% to 65%), from about a fifth to nine in ten by person. Every figure on this page is a count or a date. Quotes are at most 30 words and link to the public copy; no hit, miss or accuracy is judged here.</p>
<p>Date basis: for {undated} statements no date said is known; for {from_address} the date comes from the address of the page and for {from_title} from its title, both exact only to the day they carry. {len(predate)} windows (earliest {earliest}) begin before the statement's own date, or before 1950 where that date is unknown; a single year there is probably a quoted historical year misread as a target, a span may simply start in the past. They are left in and marked rather than removed. {withheld} statements show their time expression instead of a quote because the item's share or a turn prefix left no room for one.</p>
</div>
</header>
<main class="wrap">
{filters_html(records)}
<h2 id="timeline">Timeline by person</h2>
<p class="muted">Rows are ordered by statements found, which reflects how much text each person published and how well the rules fit their style, not how often they predict.</p>
<div class="seg" role="radiogroup" aria-label="view">
 <label><input type="radio" name="view" value="chart" checked><span>Chart</span></label>
 <label><input type="radio" name="view" value="table"><span>Table</span></label>
</div>
{legend}
<div class="chartwrap"><div id="chart" aria-live="off"></div><div id="tip" class="tip" role="tooltip" hidden></div>
<noscript><p class="muted">The chart and the filters need JavaScript. The lists below are complete without it.</p></noscript></div>
<div id="tablewrap" class="tablewrap needs-js" hidden><table id="table"><thead></thead><tbody></tbody></table></div>
<h2 id="statements">Statements by person</h2>
<div id="people">
{person_sections(records)}
</div>
<h2 id="years-h">Index by target year</h2>
<nav id="years" aria-labelledby="years-h"><ul id="yearlist">
{year_index_html(records)}
</ul></nav>
<h2 id="methods">Methods</h2>
<dl class="methods">
<dt>How candidates were found</dt>
<dd>Rules over every sentence of the stored texts: a future marker (will, going to, coming), a prediction word (predict, prophecy, forecast, warn) or a prophecy theme (shift, ascension, disclosure, first contact, collapse and the like), together with a time expression. Each time expression becomes a target window counted from the date said: “in two years” from a 2021 text is 2023, “by 2030” keeps one bound only, “soon” gets no bounds and is not on this page. Only candidates with a target window appear here.</dd>
<dt>Date said and its basis</dt>
<dd>The published date of the item where the catalogue has one; else a full date in the title; else a year and month in the address of the page; else unknown. The precision shown is the precision of that source.</dd>
<dt>Copies</dt>
<dd>Near-copies of a statement (shared five-word runs, Jaccard at least one half) are collapsed; the first occurrence is shown.</dd>
<dt>What the blinded sample measured</dt>
<dd>A fresh sample of 99 windowed candidates, labelled blind by two automated (agent) coders who did not see the rules (agreement kappa 0.96), put real predictions at about 56% (weighted by person; 95% interval about 47% to 65%), from about a fifth to nine in ten by person. The rest are misparsed dates, quoted past years or rhetorical futures. No accuracy is scored on this page.</dd>
<dt>What is withheld and why</dt>
<dd>No transcript and no audio: a quote of at most 30 words per statement (words are whitespace tokens with a letter or digit in them; the closing ellipsis is not a word), at most 5% of an item's words across the page (for speech-to-text, 5% of the transcript's words) and at most {QUOTE_CAP_PER_PERSON:,} quoted words per person; where the share leaves no room, the time expression stands in. No questioner is named: a sentence that opens as someone else's turn, a bare "Questioner" opener included, or that names a person on a private list kept by the owner, shows no quote. No private location: items are named by id and linked to their public page where one is known; a podcast episode known only by its audio file has no link.</dd>
<dt>The guard</dt>
<dd>Before the page is written, a guard recomputes the quote lengths and shares, checks every link, looks for speaker prefixes, addresses and private locations, and compares the whole page against the private texts for any run of more than thirty words anywhere and any five-word run outside the quotes. If any check fails, nothing is written.</dd>
<dt>Build</dt>
<dd>Built {esc(built)} by <code>pipeline/prediction_page.py</code> from the output of <code>pipeline/prediction_timeline.py</code> in the public repository, with the private texts as input. Counts per person are in <code>plan/prediction_timeline_counts</code> (a CSV table).</dd>
</dl>
</main>
<footer class="wrap">
<a href="index.html">Dashboard index</a> · <a href="https://github.com/occult-kranti/bashar-index/blob/main/et-channelers/ANALYSIS_PLAN.md#129-private-and-public">ANALYSIS_PLAN section 12.9</a> · Links are to the publishers' own pages as known on the build date; they are not checked for liveness.
</footer>
<script type="application/json" id="data">{data}</script>
<script>{JS.replace("__AXIS_END__", str(AXIS_END)).replace("__BUILD_YEAR__", str(BUILD_YEAR)).replace("__CARDS_SHOWN__", str(CARDS_SHOWN))}</script>
</body>
</html>
"""
    return body


# ---------------------------------------------------------------- counts and report
COUNT_FIELDS = ["person_id", "person_name", "statements", "with_window", "source_text", "speech_to_text", "conditional",
                "hedged", "strong", "earliest_target", "latest_target", "earliest_said", "latest_said", "items"]


def counts_rows(private_rows, records, people=None):
    """One row per person with any distinct candidate, windowed or not (a person with none windowed keeps a row with
    with_window 0, so the sum of statements is the whole count); people with windows first, in page order."""
    people = people or {}
    distinct = collections.Counter(r["person_id"] for r in private_rows if not r.get("copy"))
    out, seen = [], set()
    groups = list(group_by_person(records))
    rest = sorted((p for p in distinct if p not in {pid for pid, _ in groups}),
                  key=lambda p: (-distinct[p], people.get(p, {}).get("person_name") or p))
    for pid, group in groups + [(p, []) for p in rest]:
        seen.add(pid)
        targets = [y for r in group for y in (r["window_lo"], r["window_hi"]) if y is not None]
        said = sorted(r["date_said"] for r in group if r["date_said"])
        name = group[0]["person_name"] if group else (people.get(pid, {}).get("person_name") or pid)
        out.append({"person_id": pid, "person_name": name, "statements": distinct[pid],
                    "with_window": len(group), "source_text": sum(r["kind"] == "source" for r in group),
                    "speech_to_text": sum(r["kind"] == "made" for r in group),
                    "conditional": sum(r["conditional"] for r in group), "hedged": sum(r["hedged"] for r in group),
                    "strong": sum(r["strong"] for r in group), "earliest_target": min(targets) if targets else "",
                    "latest_target": max(targets) if targets else "",
                    "earliest_said": said[0] if said else "", "latest_said": said[-1] if said else "",
                    "items": len({r["item_id"] for r in group})})
    return out


def report_md(records, catalogue, notes, guard_report, built):
    lines = [f"# Public prediction page: build report ({built})", "",
             f"Private. {len(records)} statements shown for {len({r['person_id'] for r in records})} people and "
             f"{len({r['item_id'] for r in records})} items. Guard: " + ", ".join(f"{k} {v:.3f}" if isinstance(v, float) else f"{k} {v}"
                                                                               for k, v in guard_report.items()) + ".", "",
             "| Person | Shown | Quoted | Items | Share max | Share mean | Items with no public address |", "|---|---|---|---|---|---|---|"]
    for pid, group in group_by_person(records):
        quoted = collections.Counter()
        for r in group:
            quoted[r["item_id"]] += r["quote_words"]
        kinds = item_kinds(group)
        shares = [quoted[i] / item_words(catalogue[i], kinds[i]) for i in quoted if item_words(catalogue.get(i, {}), kinds[i])]
        no_link = sorted({r["item_id"] for r in group if not r["link"]})
        lines.append(f"| {group[0]['person_name']} | {len(group)} | {sum(quoted.values())} | {len(quoted)} | "
                     f"{max(shares) if shares else 0:.3f} | {sum(shares) / len(shares) if shares else 0:.3f} | "
                     f"{len(no_link)}{': ' + ', '.join(no_link) if no_link else ''} |")
    lines += ["", f"## Quotes withheld ({len(notes['withheld'])})", "",
              "Each statement still appears with its time expression. A speaker turn is shown with its prefix so a person can check it.", ""]
    for w in notes["withheld"]:
        lines.append(f"- {w['person_id']} · {w['item_id']} · {w['why']}" + (f" · prefix \"{w['turn']}\"" if w["turn"] else "")
                     + (f" · item words {w['words']}, budget {math.floor(SHARE * w['words'])}" if w["why"] == "item share" else ""))
    dropped = sorted(set(notes["links_dropped"]))
    lines += ["", f"## Items whose source address is not a public page ({len(dropped)})", "",
              "Audio files or delivery hosts; linked to a twin's page where known, else shown by id only.", ""]
    lines += [f"- {i}: {catalogue[i].get('source_url', '')[:90]} -> {public_link(catalogue[i])[0] or 'no link'}" for i in dropped]
    if notes["unknown_length"]:
        lines += ["", "## Items with no known word count (no quotes)", ""] + [f"- {i}" for i in sorted(set(notes["unknown_length"]))]
    return "\n".join(lines) + "\n"


def read_questioners(root):
    """Names from the private questioner list, when the owner keeps one (read only, never shipped)."""
    p = Path(root) / "analysis" / "predictions" / "questioner_names.txt"
    if not p.exists():
        return []
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def build(root, out, targets_path=None, publish_counts=False, cap=QUOTE_CAP_PER_PERSON):
    """Read, build, guard, write. Returns (records, guard report). Raises GuardError, writing nothing public."""
    root = Path(root)
    people = {r["person_id"]: r for r in read_csv(targets_path or ET_ROOT / "plan" / "targets.csv")}
    catalogue = {r["item_id"]: r for r in read_csv(root / "catalog" / "catalog.csv")}
    private_rows = read_private(root)
    questioners = read_questioners(root)
    records, notes = build_records(private_rows, catalogue, people, cap=cap, questioners=questioners)
    built = utc_now()
    counts = counts_rows(private_rows, records, people)
    page = render_page(records, f"{sum(c['statements'] for c in counts)} distinct candidates in all over "
                                f"{len(counts)} people, {len(records)} of them with a target window.", built)
    report = guard(records, catalogue, page, private_rows, people, questioners, cap=cap)
    atomic_write_text(Path(out), page)
    analysis = root / "analysis" / "predictions"
    write_csv(analysis / "public_page_counts.csv", counts, COUNT_FIELDS)
    atomic_write_text(analysis / "public_page_report.md", report_md(records, catalogue, notes, report, built))
    if publish_counts:
        shutil.copyfile(analysis / "public_page_counts.csv", ET_ROOT / "plan" / "prediction_timeline_counts.csv")
    return records, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--out", type=Path, default=ET_ROOT / "dashboard" / "predictions.html", help="the page to write")
    ap.add_argument("--targets", type=Path, help="default plan/targets.csv")
    ap.add_argument("--publish-counts", action="store_true", help="also write plan/prediction_timeline_counts.csv (counts only)")
    ap.add_argument("--cap", type=int, default=QUOTE_CAP_PER_PERSON, help="quoted words per person at most")
    args = ap.parse_args()
    try:
        records, report = build(args.root, args.out, args.targets, args.publish_counts, args.cap)
    except GuardError as e:
        print("guard refused; nothing written:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        sys.exit(2)
    print(f"{len(records)} statements for {len({r['person_id'] for r in records})} people and "
          f"{len({r['item_id'] for r in records})} items -> {args.out} ({report['page_bytes']} bytes); "
          f"{report['quotes']} quotes, max item share {report['max_share']:.3f}, {report['links']} links; guard passed")


if __name__ == "__main__":
    main()
