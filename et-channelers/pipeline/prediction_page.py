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
HASH_KEYS = ("p", "k", "f", "s", "d", "e", "b", "q", "x", "w", "g", "v", "o", "i")
BASIS_KEYS = (("published", "catalogue date"), ("title", "from the title"), ("address", "from the page address"),
              ("none", "not known"))
CERT_LABELS = {"strong": "strong wording", "plain": "plain", "hedged": "hedged", "conditional": "conditional"}


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


def cert_of(r):
    """One certainty key per statement: strong, else conditional, else hedged, else plain (the JS mirrors it)."""
    if r["strong"]:
        return "strong"
    if r["conditional"]:
        return "conditional"
    if r["hedged"]:
        return "hedged"
    return "plain"


def basis_key(r):
    b = r.get("date_basis") or "none"
    return "address" if b == "source address" else (b if b in ("published", "title") else "none")


def said_decade(r):
    y = year_of(r.get("date_said"))
    return str(y // 10 * 10) if y else "none"


def decade_rank(k):
    return -1 if k == "pre" else (10 ** 6 if k == "post" else int(k))


def mark_svg(r, size=14):
    """The statement's mark as a small inline svg with the chart's classes: circle for a source text, diamond for
    speech-to-text, a left triangle for an upper bound only; hollow when hedged or conditional; a ring when strong."""
    cls = f"m-{r['kind']}" + (" hollow" if r["hedged"] or r["conditional"] else "") + (" m-suspect" if suspect(r) else "")
    if r["window_lo"] is None:
        shape = f'<path d="M12 2L3 7l9 5z" class="{cls}"/>'
    elif r["kind"] == "source":
        shape = f'<circle cx="7" cy="7" r="4" class="{cls}"/>'
    else:
        shape = f'<path d="M7 2l5 5-5 5-5-5z" class="{cls}"/>'
    ring = '<circle cx="7" cy="7" r="6.3" class="ring"/>' if r["strong"] else ""
    return f'<svg class="mk" viewBox="0 0 14 14" width="{size}" height="{size}" aria-hidden="true">{shape}{ring}</svg>'


def sparkline_svg(group):
    """A 72 by 14 sparkline of the group's start years in five-year bins (counts only)."""
    starts = [start_year(r) for r in group]
    targets = [y for r in group for y in (r["window_lo"], r["window_hi"]) if y is not None]
    lo, hi = min(starts) // 5 * 5, max(starts) // 5 * 5 + 5
    nbins = (hi - lo) // 5
    counts = [0] * nbins
    for s in starts:
        counts[(s - lo) // 5] += 1
    peak = max(counts)
    bw = 72 / nbins
    rects = []
    for j, c in enumerate(counts):
        if c:
            h = max(1, round(12 * c / peak))
            rects.append(f'<rect x="{j * bw:.1f}" y="{14 - h}" width="{max(1, bw - 1):.1f}" height="{h}"/>')
    return (f'<svg class="mini" viewBox="0 0 72 14" width="72" height="14" role="img" '
            f'aria-label="{len(group)} statements, targets {min(targets)} to {max(targets)}">{"".join(rects)}</svg>')


def card_html(i, r):
    kind = "source text" if r["kind"] == "source" else "speech-to-text"
    flags = [f for f, on in (("conditional", r["conditional"]), ("hedged", r["hedged"]), ("strong wording", r["strong"])) if on]
    if suspect(r):
        flags.append(suspect(r))
    flag_html = f'<span class="flags">{" · ".join(flags)}</span>' if flags else ""
    if r["quote"]:
        body = f'<blockquote class="q">“{esc(r["quote"])}”</blockquote>'
    else:
        body = (f'<p class="q q-withheld"><em>{esc(r["time_expr"]) or "(time expression)"}</em> '
                f'<span class="muted">quote withheld, item share limit</span></p>')
    meta = [f'<span>{esc(said_label(r))}</span>', f'<code>{esc(r["item_id"])}</code>']
    if r["link"]:
        label = "public page" if r["public_page_kind"] == "page" else "episode page"
        if r["kind"] == "made" and r["offset_s"] is not None:
            label += f" · at {fmt_offset(r['offset_s'])}"
        meta.append(f'<a href="{esc(r["link"])}" rel="noopener">{esc(label)}</a>')
    elif r["kind"] == "made" and r["offset_s"] is not None:
        meta.append(f"<span>at {fmt_offset(r['offset_s'])} of the recording, no public page known</span>")
    else:
        meta.append("<span>no public page known</span>")
    meta.append(f'<button type="button" class="loc needs-js" data-i="{i}" aria-label="show on the timeline">on the timeline</button>')
    return (f'<li class="st" id="s{i}" data-i="{i}" data-start="{start_year(r)}" data-end="{end_year(r)}" '
            f'data-person="{esc(r["person_id"])}" data-kind="{r["kind"]}" data-said="{said_decade(r)}" '
            f'data-cert="{cert_of(r)}" data-basis="{basis_key(r)}">'
            f'{mark_svg(r)}<div class="st-body">'
            f'<div class="st-head"><span class="badge num">{esc(window_label(r))}</span>'
            f'<span class="st-person">{esc(r["person_name"])}</span>'
            f'<span class="chip chip-{r["kind"]}">{kind}</span>{flag_html}</div>{body}'
            f'<p class="meta">{" ".join(meta)}</p></div></li>')


def count_line(group):
    hedged = sum(r["hedged"] for r in group)
    cond = sum(r["conditional"] for r in group)
    src = sum(r["kind"] == "source" for r in group)
    made = len(group) - src
    targets = [y for r in group for y in (r["window_lo"], r["window_hi"]) if y is not None]
    return (f"{len(group)} statements · {hedged} hedged · {cond} conditional · earliest target {min(targets)} · "
            f"latest {max(targets)} · {src} from source texts, {made} from speech-to-text")


def person_sections(records):
    out, i = [], 0
    for pid, group in group_by_person(records):
        r0 = group[0]
        cards = []
        for r in group:
            cards.append(card_html(i, r))
            i += 1
        sid = f"p-{esc(pid)}"
        out.append(f'<section class="group" id="{sid}" data-key="{esc(pid)}">'
                   f'<h3 class="ghead"><button type="button" class="gtoggle" aria-expanded="true" aria-controls="{sid}-cards">'
                   f'<span class="gname">{esc(r0["person_name"])}</span> <span class="role">{esc(r0["role"])}</span></button>'
                   f'<span class="gcount num">{len(group)}</span>{sparkline_svg(group)}'
                   f'<button type="button" class="gonly needs-js" aria-label="only this group">only</button></h3>'
                   f'<p class="gsub countline muted" data-n="{len(group)}">{count_line(group)}</p>'
                   f'<ol class="cards" id="{sid}-cards">{"".join(cards)}</ol>'
                   f'<button type="button" class="more needs-js" hidden>show all {len(group)}</button></section>')
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
    keys = sorted(by_year, key=decade_rank)
    rows = []
    for k in keys:
        label = EDGE_LABELS.get(k, k)
        chips = " ".join(f'<span class="pchip">{esc(n)} <b>{c}</b></span>' for n, c in by_year[k].most_common())
        rows.append(f'<li><button type="button" class="year" data-year="{esc(k)}">{label}</button> '
                    f'<span class="ycount">{sum(by_year[k].values())}</span> {chips}</li>')
    return "\n".join(rows)


def decade_key_or_year(year):
    return "pre" if year < 1950 else ("post" if year > AXIS_END else str(year))


def _chip(name, value, label, count, kind="checkbox", checked=False, bar=None):
    extra = f'<span class="pbtn-bar"><span class="pbar" style="width:{bar:.0f}%"></span></span>' if bar is not None else ""
    return (f'<li><label class="chip-check{" radio" if kind == "radio" else ""}">'
            f'<input type="{kind}" name="{name}" value="{esc(value)}"{" checked" if checked else ""}>'
            f'<span class="cname">{esc(label)}</span><span class="ccount num">{count}</span>{extra}</label></li>')


def _facet(key, name, chips, buttons=True):
    btns = ('<div class="fbtns"><button type="button" class="fall">all</button>'
            '<button type="button" class="fnone">none</button></div>' if buttons else "")
    return (f'<details class="facet" data-facet="{key}"><summary><span class="fname">{name}</span>'
            f'<span class="fsel"></span></summary><div class="fpanel">{btns}<ul class="chips">{chips}</ul></div></details>')


def filters_html(records):
    counts = collections.Counter(r["person_id"] for r in records)
    names = {r["person_id"]: r["person_name"] for r in records}
    order = [p for p, _ in group_by_person(records)]
    peak = max(counts.values()) if counts else 1
    people = "".join(_chip("p", p, names[p], counts[p], bar=100 * counts[p] / peak) for p in order)
    n_src = sum(r["kind"] == "source" for r in records)
    kinds = (_chip("k", "all", "all", len(records), "radio", True) + _chip("k", "source", "source text", n_src, "radio")
             + _chip("k", "made", "speech-to-text made here", len(records) - n_src, "radio"))
    n_h, n_c = sum(r["hedged"] for r in records), sum(r["conditional"] for r in records)
    n_fl = sum(r["hedged"] or r["conditional"] for r in records)
    n_sus = sum(1 for r in records if suspect(r))
    strong = sum(r["strong"] for r in records)
    certs = (_chip("f", "all", "all", len(records), "radio", True) + _chip("f", "hedged", "hedged", n_h, "radio")
             + _chip("f", "conditional", "conditional", n_c, "radio") + _chip("f", "flagged", "hedged or conditional", n_fl, "radio")
             + _chip("f", "plain", "neither hedged nor conditional", len(records) - n_fl, "radio")
             + _chip("f", "suspect", "target before the date said", n_sus, "radio")
             + _chip("s", "1", "strong wording only", strong))
    decades = sorted({d for r in records for d in decades_of(r)}, key=decade_rank)
    dec_counts = collections.Counter(d for r in records for d in decades_of(r))
    decade_chips = "".join(_chip("d", d, decade_label(d), dec_counts[d]) for d in decades)
    said_counts = collections.Counter(said_decade(r) for r in records)
    said_keys = (["none"] if "none" in said_counts else []) + sorted((k for k in said_counts if k != "none"), key=int)
    said_chips = "".join(_chip("e", k, "date not known" if k == "none" else f"{k}s", said_counts[k]) for k in said_keys)
    basis_counts = collections.Counter(basis_key(r) for r in records)
    basis_chips = "".join(_chip("b", k, label, basis_counts[k]) for k, label in BASIS_KEYS if k in basis_counts)
    facets = (_facet("p", "People", people) + _facet("k", "Kind", kinds, False) + _facet("f", "Certainty", certs, False)
              + _facet("d", "Target decade", decade_chips) + _facet("e", "Decade said", said_chips)
              + _facet("b", "Date basis", basis_chips))
    return f"""
<form id="toolbar" class="toolbar needs-js" autocomplete="off">
  <div class="trow trow-1">
    <div class="qwrap"><label class="sr-only" for="q">Search</label>
      <input type="search" id="q" name="q" placeholder="person, quote, time expression, item id" spellcheck="false">
      <button type="button" id="q-clear" aria-label="clear the search" hidden>×</button></div>
    <output id="count" class="count" for="q" aria-live="polite">{len(records)} of {len(records)} statements · {len(counts)} people</output>
    <button type="button" id="clear-all" class="btn" hidden>Clear all</button>
    <fieldset class="seg" id="view" role="radiogroup" aria-label="view">
      <label><input type="radio" name="view" value="chart" checked><span>Chart</span></label>
      <label><input type="radio" name="view" value="table"><span>Table</span></label>
    </fieldset>
    <button type="button" id="filters-toggle" class="btn" aria-expanded="false" aria-controls="facets">Filters <b id="filters-n"></b></button>
  </div>
  <div class="trow trow-2" id="facets">{facets}</div>
  <div class="trow trow-3">
    <p id="caveat-mini" title="Labelled candidates, not confirmed predictions: about 56% of windowed candidates are real predictions (95% interval about 47% to 65%).">Labelled candidates, not confirmed predictions: about 56% of windowed candidates are real predictions (95% interval about 47% to 65%). <a href="#caveat">Details</a></p>
    <ul id="active" class="active" aria-label="active filters"></ul>
  </div>
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


def now_fraction(built):
    """The build date as a decimal year, two decimals, for the chart's now line (BUILD_YEAR + 0.5 as fallback)."""
    try:
        import datetime
        d = datetime.date.fromisoformat(str(built)[:10])
        return f"{d.year + (d.timetuple().tm_yday - 1) / 365:.2f}"
    except (ValueError, TypeError):
        return f"{BUILD_YEAR + 0.5:.2f}"

LIGHT_TOKENS = (
    "--bg:#fbfbfa;--fg:#1a1a19;--fg-muted:#5c5b57;--fg-faint:#8b8a85;--border:#d9d8d3;--border-strong:#b4b3ad;"
    "--surface:#ffffff;--surface-2:#f3f3f0;--accent:#1f5fb0;--focus:#4f46e5;--focus-halo:#fbfbfa;"
    "--series-source:#2b5fb3;--series-made:#b05a1a;--series-source-soft:#a9bfe6;--series-made-soft:#e3b89a;--flag:#8a8984;"
    "--band:#f4f4f1;--past:#ecece8;--grid:#e6e5e0;--grid-strong:#cfcec8;--stack:#e9e9e4;--stack-border:#8f8e89;"
    "--brush:rgba(31,95,176,.18);--hot:#1f5fb0;--hist:#c9c8c2;--now:#5c5b57;--shadow-1:0 2px 8px rgba(0,0,0,.12);"
    "--shadow-2:0 8px 24px rgba(0,0,0,.14);color-scheme:light")
DARK_TOKENS = (
    "--bg:#17191d;--fg:#eceae4;--fg-muted:#b2b0a8;--fg-faint:#80828a;--border:#3a3d44;--border-strong:#555962;"
    "--surface:#1f2228;--surface-2:#1a1d22;--accent:#7fa8ee;--focus:#a5b4fc;--focus-halo:#17191d;"
    "--series-source:#4f86de;--series-made:#c97c30;--series-source-soft:#2c4a80;--series-made-soft:#7a4a1c;--flag:#8a8d94;"
    "--band:#1c1f24;--past:#23262c;--grid:#2b2e35;--grid-strong:#40444c;--stack:#2a2e35;--stack-border:#8a8e97;"
    "--brush:rgba(127,168,238,.22);--hot:#7fa8ee;--hist:#3f434b;--now:#b2b0a8;--shadow-1:0 2px 10px rgba(0,0,0,.5);"
    "--shadow-2:0 8px 24px rgba(0,0,0,.6);color-scheme:dark")
BASE_TOKENS = (
    "--r-sm:4px;--r-md:8px;--r-lg:12px;--r-pill:999px;--sp-1:4px;--sp-2:8px;--sp-3:12px;--sp-4:16px;--sp-5:24px;"
    "--sp-6:32px;--sp-7:48px;--sp-8:64px;--fs-2xs:.7rem;--fs-xs:.78rem;--fs-sm:.875rem;--fs-md:1rem;--fs-lg:1.125rem;"
    "--fs-xl:1.35rem;--fs-2xl:clamp(1.75rem,1.2rem + 2vw,2.25rem);"
    "--font-ui:system-ui,-apple-system,\"Segoe UI\",Roboto,Helvetica,Arial,sans-serif;"
    "--font-mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
    "--font-quote:Georgia,\"Iowan Old Style\",\"Palatino Linotype\",Palatino,serif;--dur:160ms")

CSS = ":root{" + LIGHT_TOKENS + "}\n:root{" + BASE_TOKENS + "}\n" + \
    '@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){' + DARK_TOKENS + "}}\n" + \
    ':root[data-theme="dark"]{' + DARK_TOKENS + "}\n" + r"""
@media (prefers-reduced-motion: reduce){:root{--dur:0ms}html{scroll-behavior:auto}}
*{box-sizing:border-box}
html{overflow-x:clip;scroll-padding-top:6.5rem}
body{margin:0;background:var(--bg);color:var(--fg);font:var(--fs-md)/1.5 var(--font-ui);overflow-wrap:anywhere;-webkit-text-size-adjust:100%}
svg{max-width:100%;display:block}
.wrap{max-width:76rem;margin:0 auto;padding:0 16px}
code,.mono,.num,.badge{font-family:var(--font-mono);font-size:.92em;font-variant-numeric:tabular-nums}
a{color:var(--accent)}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px;box-shadow:0 0 0 2px var(--focus-halo)}
.skip{position:absolute;left:16px;top:-4rem;z-index:40;background:var(--surface);color:var(--fg);border:1px solid var(--border-strong);border-radius:var(--r-md);padding:.4rem .8rem}
.skip:focus{top:8px}
h1{font-size:var(--fs-2xl);line-height:1.15;margin:.2rem 0 .6rem;font-weight:600;letter-spacing:-.01em}
h2{font-size:var(--fs-xl);margin:var(--sp-6) 0 var(--sp-3);line-height:1.25}
h3{font-size:var(--fs-lg);margin:0}
.muted,.meta,.flags,.role,.countline,.eyebrow{color:var(--fg-muted)}
.eyebrow{font-size:var(--fs-xs);text-transform:uppercase;letter-spacing:.06em;margin:var(--sp-6) 0 0}
.lead{max-width:62ch;font-size:var(--fs-lg);margin:.4rem 0 .6rem}
.facts{font-family:var(--font-mono);font-size:var(--fs-xs);color:var(--fg-muted);margin:0 0 var(--sp-4)}
.caveat{border:1px solid var(--border-strong);border-left:4px solid var(--flag);border-radius:var(--r-md);padding:var(--sp-4) var(--sp-5);background:var(--surface);max-width:80ch;margin:var(--sp-4) 0 var(--sp-5)}
.caveat h2{font-size:var(--fs-lg);margin:0 0 .4rem}
.caveat-p{margin:.4rem 0;font-size:var(--fs-sm)}
.caveat-figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,11rem),1fr));gap:var(--sp-2);margin:var(--sp-3) 0}
.fig{background:var(--surface-2);border-radius:var(--r-md);padding:.5rem .7rem}
.fig b{display:block;font-size:var(--fs-xl);font-weight:600;font-variant-numeric:tabular-nums;line-height:1.2}
.fig span{font-size:var(--fs-xs);color:var(--fg-muted)}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.no-js .needs-js,.no-js .needs-d3,.no-d3 .needs-d3{display:none!important}
.no-js .gtoggle{pointer-events:none}
.no-js .gtoggle::before{display:none}
.btn,.more,.year,.tok,.edge,.wpreset,.zoomctl button,.fall,.fnone,.loc,.gonly,#download,#expand-all,#collapse-all,#empty button{font:inherit;font-size:var(--fs-sm);color:var(--fg);background:var(--surface);border:1px solid var(--border);border-radius:var(--r-pill);padding:.2rem .7rem;cursor:pointer;line-height:1.4}
.btn:hover,.more:hover,.year:hover,.tok:hover,.wpreset:hover,.zoomctl button:hover,.loc:hover,.gonly:hover{border-color:var(--border-strong);background:var(--surface-2)}
.wpreset[aria-pressed="true"],.rowlabel[aria-pressed="true"]{border-color:var(--fg);box-shadow:inset 0 0 0 1px var(--fg)}
/* toolbar */
.toolbar{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--border);margin:0 -16px;padding:.5rem 16px .4rem}
@supports (backdrop-filter:blur(8px)) or (-webkit-backdrop-filter:blur(8px)){.toolbar{background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}}
.trow{display:flex;flex-wrap:wrap;gap:.4rem .7rem;align-items:center}
.trow+.trow{margin-top:.4rem}
.qwrap{position:relative;flex:1 1 14rem;min-width:0;max-width:26rem}
#q{font:inherit;font-size:var(--fs-sm);color:var(--fg);background:var(--surface);border:1px solid var(--border);border-radius:var(--r-pill);padding:.35rem 2rem .35rem .8rem;width:100%}
#q-clear{position:absolute;right:.3rem;top:50%;transform:translateY(-50%);border:0;background:none;color:var(--fg-muted);font-size:1.1rem;cursor:pointer;padding:0 .4rem;line-height:1}
.count{font-size:var(--fs-sm);color:var(--fg-muted);font-variant-numeric:tabular-nums}
.seg{display:inline-flex;border:1px solid var(--border);border-radius:var(--r-pill);overflow:hidden;margin:0;padding:0;background:var(--surface)}
.seg label{padding:.2rem .9rem;font-size:var(--fs-sm);cursor:pointer;position:relative}
.seg input{position:absolute;opacity:0;width:1px;height:1px;pointer-events:none}
.seg input:checked+span{font-weight:600}
.seg label:has(input:checked){background:var(--border)}
.seg label:has(input:focus-visible){outline:2px solid var(--focus);outline-offset:-2px}
.seg label:has(input:disabled){color:var(--fg-faint);cursor:not-allowed}
#filters-toggle{display:none}
#filters-n:empty{display:none}
#filters-n{background:var(--fg);color:var(--bg);border-radius:var(--r-pill);padding:0 .45rem;font-size:var(--fs-2xs);margin-left:.2rem}
.facet{position:relative}
.facet>summary{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:.35rem;border:1px solid var(--border);border-radius:var(--r-pill);padding:.2rem .75rem;font-size:var(--fs-sm);background:var(--surface);user-select:none}
.facet>summary::-webkit-details-marker{display:none}
.facet>summary::after{content:"";width:.4em;height:.4em;border-right:1.5px solid var(--fg-muted);border-bottom:1.5px solid var(--fg-muted);transform:rotate(45deg) translateY(-.15em);margin-left:.1rem}
.facet[open]>summary{border-color:var(--fg)}
.facet.active>summary{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
.fsel{color:var(--fg-muted);font-variant-numeric:tabular-nums}
.fsel:empty{display:none}
.fpanel{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:.5rem .6rem;margin-top:.3rem}
.fbtns{display:flex;gap:.3rem;margin-bottom:.3rem}
.fall,.fnone{font-size:var(--fs-xs);padding:.05rem .55rem}
.chips{list-style:none;margin:0;padding:0;display:grid;gap:.1rem;max-height:50vh;overflow:auto}
.chip-check{display:grid;grid-template-columns:1rem 1fr auto;align-items:center;gap:.15rem .45rem;padding:.2rem .35rem;border-radius:var(--r-sm);cursor:pointer;font-size:var(--fs-sm);position:relative}
.chip-check:hover{background:var(--surface-2)}
.chip-check input{position:absolute;opacity:0;width:1px;height:1px;margin:0}
.chip-check::before{content:"";width:1rem;height:1rem;border:1px solid var(--border-strong);border-radius:3px;display:inline-grid;place-items:center;font-size:.72rem;line-height:1;color:var(--bg);background:var(--surface)}
.chip-check.radio::before{border-radius:50%}
.chip-check:has(input:checked)::before{content:"✓";background:var(--fg);border-color:var(--fg)}
.chip-check:has(input:focus-visible){outline:2px solid var(--focus);outline-offset:1px}
@supports not selector(:has(a)){.chip-check input:checked+.cname{font-weight:600}.chip-check input:checked+.cname::before{content:"✓ "}.chip-check:focus-within{outline:2px solid var(--focus);outline-offset:1px}}
.ccount{color:var(--fg-muted);font-size:var(--fs-xs)}
.chip-check[data-zero]{color:var(--fg-faint)}
.pbtn-bar{grid-column:2/-1;height:3px;background:var(--surface-2);border-radius:2px;overflow:hidden}
.pbar{display:block;height:100%;background:var(--hist)}
#caveat-mini{margin:0;font-size:var(--fs-xs);color:var(--fg-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1 1 18rem}
.active{list-style:none;display:flex;flex-wrap:wrap;gap:.3rem;margin:0;padding:0}
.active:empty{display:none}
.tok{font-size:var(--fs-xs);padding:.05rem .55rem;background:var(--surface-2)}
@media (min-width:48rem){
  .trow-2{display:flex}
  .fpanel{position:absolute;top:100%;left:0;z-index:25;min-width:17rem;max-width:min(90vw,28rem);box-shadow:var(--shadow-2)}
  .facet.flip .fpanel{left:auto;right:0}
}
@media (max-width:47.99rem){
  .toolbar{max-height:55vh;overflow:auto}
  #filters-toggle{display:inline-flex;align-items:center}
  .trow-2{display:none;flex-direction:column;align-items:stretch}
  .trow-2.open{display:flex}
  .facet>summary{width:100%;justify-content:space-between}
}
/* timeline */
.card-head{display:flex;flex-wrap:wrap;gap:.5rem 1rem;align-items:center;justify-content:space-between;margin:var(--sp-6) 0 var(--sp-2)}
.card-head h2{margin:0}
.chart-head{display:flex;flex-wrap:wrap;gap:.4rem .8rem;align-items:center}
.sel{font-size:var(--fs-sm);display:inline-flex;align-items:center;gap:.4rem}
select{font:inherit;font-size:var(--fs-sm);color:var(--fg);background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:.25rem .4rem;max-width:100%}
.zoomctl{display:inline-flex;gap:.2rem}
.zoomctl button{min-width:36px;min-height:36px;padding:0 .5rem;border-radius:var(--r-md)}
@media (pointer:coarse){.zoomctl button{min-width:40px;min-height:40px}}
.wpresets{display:inline-flex;flex-wrap:wrap;gap:.25rem}
.wpreset{font-size:var(--fs-xs);padding:.1rem .6rem}
.check{display:inline-flex;align-items:center;gap:.35rem;font-size:var(--fs-sm)}
.legend{display:flex;flex-wrap:wrap;gap:.25rem 1rem;list-style:none;padding:0;margin:0 0 var(--sp-2);font-size:var(--fs-xs);color:var(--fg-muted)}
.legend li{display:inline-flex;align-items:center;gap:.4rem}
.legend svg{width:16px;height:16px;overflow:visible;flex:none}
.chartwrap{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:6px 4px}
#chart-axis-wrap{background:var(--surface);border-bottom:1px solid var(--border)}
#chart-scroll{max-height:72vh;overflow-y:auto;overflow-x:hidden;scrollbar-gutter:stable;position:relative}
#chart-axis,#chart-svg,#minimap{width:100%;font-size:12px;font-family:var(--font-ui)}
#chart-svg{cursor:grab;outline:none;height:auto}
#chart-svg:focus-visible{outline:2px solid var(--focus);outline-offset:-2px;box-shadow:none}
#chart-svg.dragging{cursor:grabbing}
.band{fill:var(--band)}
.past{fill:var(--past)}
.zoom-surface{fill:transparent}
.grid line{stroke:var(--grid)}
.grid line.major{stroke:var(--grid-strong)}
.now{stroke:var(--now);stroke-dasharray:3 3;stroke-width:1}
.nowlabel{fill:var(--fg-muted);font-size:10px;text-anchor:middle}
.axis text{fill:var(--fg-muted);font-size:11px}
.axis line{stroke:var(--grid-strong)}
.axis path{stroke:var(--border)}
.axis .minor line{stroke:var(--grid)}
.rowlabel{fill:var(--fg);font-size:12px}
.rowlabel.btn-label{cursor:pointer}
.rowlabel.btn-label:hover,.rowlabel[aria-pressed="true"]{font-weight:600;text-decoration:underline}
.rowlabel[aria-pressed="true"]{box-shadow:none;border:0}
.rowpill{fill:var(--surface);fill-opacity:.9;stroke:var(--border)}
.mark{cursor:pointer;outline:none}
.mark .hit{fill:transparent;stroke:none}
.mark:hover .hit,.mark.is-hot .hit{stroke:var(--hot);stroke-width:1.5}
.mark:focus-visible .hit{stroke:var(--focus);stroke-width:2}
.mark.is-pinned .hit{stroke:var(--hot);stroke-width:2;stroke-dasharray:3 2}
.m-source{fill:var(--series-source);stroke:var(--series-source)}
.m-made{fill:var(--series-made);stroke:var(--series-made)}
.hollow{fill:var(--surface);stroke-width:1.5}
.ring{fill:none;stroke:var(--fg);stroke-width:1}
.m-suspect{fill-opacity:.45}
.bar-source{fill:var(--series-source-soft)}
.bar-made{fill:var(--series-made-soft)}
.leader{stroke:var(--fg-muted);stroke-dasharray:1 2;stroke-width:1}
.lead{stroke:var(--fg-muted);stroke-dasharray:3 3;fill:none}
.lead-dot{fill:var(--surface);stroke:var(--fg-muted)}
.pill{fill:var(--stack);stroke:var(--stack-border);stroke-width:1}
.pill.one-source{stroke:var(--series-source)}
.pill.one-made{stroke:var(--series-made)}
.pill.strong{stroke-width:2}
.count-t{fill:var(--fg);font-size:11px;font-weight:600;text-anchor:middle;pointer-events:none}
.mark.is-hot .count-t{font-weight:800}
.stackbar{fill:var(--fg-faint);opacity:.35}
.edge{position:absolute;top:40%;z-index:3;font-size:var(--fs-xs);padding:.15rem .5rem;box-shadow:var(--shadow-1)}
.edge-left{left:6px}
.edge-right{right:6px}
.minifig{margin:6px 0 0;padding-top:6px;border-top:1px solid var(--border)}
#minimap{height:44px}
.density rect{fill:var(--hist)}
.density-vis rect{fill:var(--fg-muted)}
.mini-axis text{fill:var(--fg-faint);font-size:9px;text-anchor:middle}
.now-mini{stroke:var(--now);stroke-dasharray:2 2}
.brush .selection{fill:var(--brush);stroke:var(--accent);stroke-width:1}
.brush .overlay{cursor:crosshair}
.handle--custom{fill:var(--accent);pointer-events:none}
.tip{position:absolute;z-index:10;max-width:min(22rem,100% - 16px);background:var(--surface);color:var(--fg);border:1px solid var(--border);border-radius:var(--r-md);padding:.5rem .7rem;font-size:var(--fs-sm);box-shadow:var(--shadow-2);pointer-events:none}
.tip b{display:flex;align-items:center;gap:.35rem}
.tip svg{width:10px;height:10px;overflow:visible;flex:none}
.tip .tq{font-family:var(--font-quote);margin:.2rem 0}
.tip .muted{font-size:var(--fs-xs)}
.tip .hint{font-size:var(--fs-2xs);color:var(--fg-faint);margin-top:.2rem}
#chart-help{font-size:var(--fs-xs);margin:.4rem 0 0}
#chart-caption{font-size:var(--fs-sm)}
/* table */
.tablewrap{overflow:auto;border:1px solid var(--border);border-radius:var(--r-lg);background:var(--surface);max-height:70vh;margin-top:var(--sp-3)}
table{border-collapse:collapse;width:100%;font-size:var(--fs-sm);font-variant-numeric:tabular-nums}
th,td{text-align:left;vertical-align:top;padding:.35rem .5rem;border-bottom:1px solid var(--border)}
th{position:sticky;top:0;background:var(--surface);color:var(--fg-muted);font-weight:500;white-space:nowrap;z-index:1;box-shadow:0 1px 0 var(--border)}
th button{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer}
th[aria-sort="ascending"] button::after{content:" \2191"}
th[aria-sort="descending"] button::after{content:" \2193"}
tbody tr:nth-child(even){background:var(--surface-2)}
tbody tr{cursor:pointer}
tbody tr.is-hot td{background:var(--band);box-shadow:inset 2px 0 0 var(--hot)}
tbody tr.is-pinned td{box-shadow:inset 2px 0 0 var(--hot),inset 0 -1px 0 var(--hot)}
td.quote{min-width:22rem;font-family:var(--font-quote)}
td .badge{white-space:nowrap}
tfoot td{color:var(--fg-muted);text-align:center;padding:var(--sp-4)}
.empty{border:1px dashed var(--border-strong);border-radius:var(--r-lg);padding:var(--sp-5);text-align:center;margin:var(--sp-4) 0}
.empty-h{font-size:var(--fs-lg);font-weight:600;margin:0 0 .3rem}
.empty p{margin:.3rem 0}
.empty .ebtns{display:flex;flex-wrap:wrap;gap:.4rem;justify-content:center;margin-top:.6rem}
/* statements */
#results-tools{display:flex;flex-wrap:wrap;gap:.4rem .8rem;align-items:center;margin:0 0 var(--sp-3)}
.group{margin:var(--sp-5) 0;padding-top:var(--sp-3);border-top:1px solid var(--border)}
.ghead{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;margin:0 0 .2rem;font-size:var(--fs-lg)}
.gtoggle{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer;text-align:left;font-weight:600}
.gtoggle::before{content:"";display:inline-block;width:.45em;height:.45em;border-right:2px solid var(--fg-muted);border-bottom:2px solid var(--fg-muted);transform:rotate(45deg);margin:0 .5rem .15em .1rem;transition:transform var(--dur)}
.gtoggle[aria-expanded="false"]::before{transform:rotate(-45deg)}
.gcount{font-size:var(--fs-sm);color:var(--fg-muted)}
.mini{width:72px;height:14px;flex:none}
.mini rect{fill:var(--hist)}
.gonly{font-size:var(--fs-2xs);padding:0 .5rem}
.group.collapsed .cards,.group.collapsed .more,.group.collapsed .gsub{display:none}
.countline{font-size:var(--fs-sm);margin:0 0 .5rem}
.cards{list-style:none;padding:0;margin:0;display:grid;gap:var(--sp-2)}
.st{display:grid;grid-template-columns:14px minmax(0,1fr);gap:.6rem;background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--flag);border-radius:var(--r-md);padding:.6rem .8rem .6rem .7rem;transition:border-color var(--dur),box-shadow var(--dur)}
.st[data-kind="source"]{border-left-color:var(--series-source)}
.st[data-kind="made"]{border-left-color:var(--series-made)}
.st.is-hot{border-color:var(--hot)}
.st.is-pinned{box-shadow:0 0 0 2px var(--hot)}
.st>.mk{margin-top:.3rem}
.st-body{min-width:0}
.st-head{display:flex;flex-wrap:wrap;gap:.3rem .6rem;align-items:center;font-size:var(--fs-xs)}
.st-person{display:none;font-weight:600;color:var(--fg)}
#groups:not([data-group="person"]) .st-person{display:inline}
.badge{border:1px solid var(--border);border-radius:var(--r-sm);padding:0 .4rem;background:var(--surface-2);color:var(--fg)}
.chip{padding-left:.45rem;border-left:3px solid var(--flag);color:var(--fg)}
.chip-source{border-left-color:var(--series-source)}
.chip-made{border-left-color:var(--series-made)}
blockquote.q{margin:.35rem 0 .35rem .45em;font-family:var(--font-quote);font-size:var(--fs-lg);line-height:1.4;text-indent:-.45em}
.q-withheld{margin:.35rem 0}
.q-withheld .muted{font-size:var(--fs-xs)}
.meta{font-size:var(--fs-xs);margin:0;display:flex;flex-wrap:wrap;gap:.2rem .6rem;align-items:baseline}
.loc{font-size:var(--fs-2xs);padding:0 .5rem}
.more{margin-top:.5rem}
#years summary{cursor:pointer;list-style:revert}
#years summary h2{display:inline;margin:0}
#yearlist{list-style:none;padding:0;margin:var(--sp-3) 0 0;display:grid;gap:.25rem;font-size:var(--fs-sm)}
#yearlist li{display:flex;flex-wrap:wrap;gap:.25rem .4rem;align-items:center}
.year{font-family:var(--font-mono)}
.ycount{color:var(--fg-muted);min-width:2ch}
.pchip{font-size:var(--fs-xs);border:1px solid var(--border);border-radius:var(--r-pill);padding:0 .45rem;color:var(--fg)}
.pchip b{font-weight:500;color:var(--fg-muted)}
.methods{max-width:90ch}
.methods dt{font-weight:600;margin-top:.6rem}
.methods dd{margin:0 0 .2rem}
@media (min-width:48rem){.methods{display:grid;grid-template-columns:14rem 1fr;gap:.5rem 1.4rem}.methods dt{margin:0}}
footer{margin:var(--sp-7) 0 var(--sp-6);color:var(--fg-muted);font-size:var(--fs-sm);border-top:1px solid var(--border);padding-top:var(--sp-4)}
footer p{margin:.3rem 0}
@media (forced-colors: active){
  .m-source,.m-made{fill:CanvasText;stroke:CanvasText}
  .hollow{fill:Canvas}
  .bar-source,.bar-made,.stackbar,.density rect{fill:GrayText}
  .pill,.rowpill{fill:Canvas;stroke:CanvasText}
  .band,.past{fill:Canvas}
  .grid line{stroke:GrayText}
  .brush .selection{fill:Highlight;fill-opacity:.3}
}
@media print{
  .toolbar,.chart-head,.edge,.minifig,.more,.loc,.gonly,#results-tools,#chart-help,.skip{display:none!important}
  .tablewrap,#chart-scroll{max-height:none;overflow:visible}
  .group.collapsed .cards{display:grid}
  .st{break-inside:avoid}
  a[href^="http"]::after{content:" (" attr(href) ")";font-size:.8em}
}
"""

JS = r"""
(function () {
  'use strict';
  var doc = document, root = doc.documentElement;
  root.classList.remove('no-js');
  function $(s, el) { return (el || doc).querySelector(s); }
  function $$(s, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(s)); }
  function el(tag, cls, text) { var e = doc.createElement(tag); if (cls) e.className = cls; if (text !== undefined && text !== null) e.textContent = text; return e; }
  var DATA = JSON.parse($('#data').textContent);
  var AXIS_END = __AXIS_END__, BUILD_YEAR = __BUILD_YEAR__, SHOWN = __CARDS_SHOWN__, NOW_F = __NOW__, PUBLIC_KEYS = __PUBLIC_KEYS__;
  var REDUCED = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var COARSE = !!(window.matchMedia && matchMedia('(hover: none)').matches);
  var DUR = REDUCED ? 0 : 300;

  // ---- derived fields (ids, years and flags only)
  function decadeOf(y) { return y < 1950 ? 'pre' : (y > AXIS_END ? 'post' : String(Math.floor(y / 10) * 10)); }
  function decadeLabel(k) { return k === 'pre' ? 'before 1950' : (k === 'post' ? 'after ' + AXIS_END : k + 's'); }
  function decadeRank(k) { return k === 'pre' ? -1 : (k === 'post' ? 1e6 : +k); }
  function decadesOf(lo, hi) {
    var out = [], y = lo;
    while (y <= hi) { var k = decadeOf(y); if (out.indexOf(k) < 0) out.push(k); if (k === 'post') break; y = k === 'pre' ? 1950 : Math.floor(y / 10) * 10 + 10; }
    return out;
  }
  function yearOf(s) { var m = /^((?:19|20)\d\d)/.exec(s || ''); return m ? +m[1] : null; }
  function fold(s) { s = String(s || '').toLowerCase(); try { s = s.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); } catch (e) { } return s; }
  function basisKey(b) { return b === 'source address' ? 'address' : ((b === 'published' || b === 'title') ? b : 'none'); }
  function cmpStr(a, b) { return a < b ? -1 : (a > b ? 1 : 0); }
  DATA.forEach(function (d, i) {
    d.i = i; d.start = d.window_lo !== null ? d.window_lo : d.window_hi; d.end = d.window_hi !== null ? d.window_hi : d.window_lo;
    d.decades = decadesOf(d.start, d.end); d.saidYear = yearOf(d.date_said);
    d.saidDecade = d.saidYear ? String(Math.floor(d.saidYear / 10) * 10) : 'none'; d.basisKey = basisKey(d.date_basis);
    d.cert = d.strong ? 'strong' : (d.conditional ? 'conditional' : (d.hedged ? 'hedged' : 'plain'));
    d.suspect = d.saidYear ? (d.start < d.saidYear ? 'target before the date said' : '') : (d.start < 1950 ? 'target before 1950' : '');
    d.ahead = d.saidYear ? d.end - d.saidYear : null;
    d.search = fold(d.person_name + ' ' + (d.quote || '') + ' ' + d.time_expr + ' ' + d.item_id);
  });
  var ORDER = DATA.map(function (d) { return d.i; }).sort(function (a, b) {
    a = DATA[a]; b = DATA[b];
    return (a.start - b.start) || (a.end - b.end) || cmpStr(a.date_said || '9999', b.date_said || '9999') || cmpStr(a.item_id, b.item_id) || ((a.offset_s || 0) - (b.offset_s || 0));
  });
  var PEOPLE = [], NAMES = {};
  DATA.forEach(function (d) { if (!(d.person_id in NAMES)) { NAMES[d.person_id] = d.person_name; PEOPLE.push(d.person_id); } });
  function uniq(list) { return list.filter(function (x, j, a) { return a.indexOf(x) === j; }); }
  var DECADES = uniq([].concat.apply([], DATA.map(function (d) { return d.decades; }))).sort(function (a, b) { return decadeRank(a) - decadeRank(b); });
  var SAID_ASC = uniq(DATA.map(function (d) { return d.saidDecade; }).filter(function (k) { return k !== 'none'; })).sort(function (a, b) { return a - b; });
  var HAS_UNDATED = DATA.some(function (d) { return d.saidDecade === 'none'; });
  var SAID = (HAS_UNDATED ? ['none'] : []).concat(SAID_ASC);
  var BASIS = ['published', 'title', 'address', 'none'].filter(function (k) { return DATA.some(function (d) { return d.basisKey === k; }); });
  function quantile(sorted, p) { if (!sorted.length) return NaN; var h = (sorted.length - 1) * p, lo = Math.floor(h), hi = Math.ceil(h); return sorted[lo] + (sorted[hi] - sorted[lo]) * (h - lo); }
  var STARTS = DATA.map(function (d) { return d.start; }).sort(function (a, b) { return a - b; });
  var ENDS = DATA.map(function (d) { return d.end; }).sort(function (a, b) { return a - b; });
  var FULL = [Math.min(1920, Math.floor((STARTS[0] || 1920) / 10) * 10), Math.max(AXIS_END, ENDS[ENDS.length - 1] || AXIS_END)];
  var DEFAULT = (function () {
    if (!DATA.length) return FULL.slice();
    var a = Math.floor((quantile(STARTS, .02) - 1) / 5) * 5, b = Math.ceil((quantile(ENDS, .98) + 1) / 5) * 5;
    a = Math.max(FULL[0], a); b = Math.min(FULL[1], b);
    if (b - a < 20) { var c = (a + b) / 2; a = Math.max(FULL[0], c - 10); b = Math.min(FULL[1], a + 20); a = Math.max(FULL[0], b - 20); }
    return [a, b];
  })();
  var META = { people: PEOPLE, decades: DECADES, said: SAID, basis: BASIS, n: DATA.length, FULL: FULL, DEFAULT: DEFAULT };

  /* @@hash-begin */
  var HASH_KEYS = ['p', 'k', 'f', 's', 'd', 'e', 'b', 'q', 'x', 'w', 'g', 'v', 'o', 'i'];
  var F_VALUES = ['all', 'hedged', 'conditional', 'flagged', 'plain', 'suspect'];
  var G_VALUES = ['person', 'kind', 'said', 'cert', 'target'];
  var SORT_KEYS = ['row', 'person', 'said', 'start', 'span', 'ahead', 'kind', 'cert', 'quote', 'item', 'link'];
  function defaultState(meta) {
    return { q: '', p: [], k: 'all', f: 'all', s: false, d: [], e: [], b: [], x: meta.DEFAULT.slice(), w: false, g: 'person', v: 'chart', o: '', i: null };
  }
  function fmtYear(v) { return String(Math.round(v * 100) / 100); }
  function sameWindow(a, b) { return !!a && !!b && Math.abs(a[0] - b[0]) < .01 && Math.abs(a[1] - b[1]) < .01; }
  function clampWindow(w, FULL) {
    var a = Math.max(FULL[0], Math.min(w[0], w[1])), b = Math.min(FULL[1], Math.max(w[0], w[1]));
    if (b - a < 4) {
      var c = (a + b) / 2; a = c - 2; b = c + 2;
      if (a < FULL[0]) { a = FULL[0]; b = Math.min(FULL[1], a + 4); }
      if (b > FULL[1]) { b = FULL[1]; a = Math.max(FULL[0], b - 4); }
    }
    return [Math.round(a * 100) / 100, Math.round(b * 100) / 100];
  }
  function shiftWindow(w, FULL) {
    var width = Math.min(w[1] - w[0], FULL[1] - FULL[0]), a = w[0], b = w[1];
    if (a < FULL[0]) { a = FULL[0]; b = a + width; }
    if (b > FULL[1]) { b = FULL[1]; a = b - width; }
    return clampWindow([a, b], FULL);
  }
  function parseWindow(v, FULL) {
    var m = /^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(v);
    return m ? clampWindow([+m[1], +m[2]], FULL) : null;
  }
  function serializeHash(st, meta) {
    var parts = [];
    function pick(list, order) { return order.filter(function (k) { return list.indexOf(k) >= 0; }); }
    if (st.p.length) parts.push('p=' + pick(st.p, meta.people).join(','));
    if (st.k !== 'all') parts.push('k=' + st.k);
    if (st.f !== 'all') parts.push('f=' + st.f);
    if (st.s) parts.push('s=1');
    if (st.d.length) parts.push('d=' + pick(st.d, meta.decades).join(','));
    if (st.e.length) parts.push('e=' + pick(st.e, meta.said).join(','));
    if (st.b.length) parts.push('b=' + pick(st.b, meta.basis).join(','));
    if (st.q) parts.push('q=' + encodeURIComponent(st.q));
    if (st.x && !sameWindow(st.x, meta.DEFAULT)) parts.push('x=' + fmtYear(st.x[0]) + '-' + fmtYear(st.x[1]));
    if (st.w) parts.push('w=1');
    if (st.g !== 'person') parts.push('g=' + st.g);
    if (st.v !== 'chart') parts.push('v=' + st.v);
    if (st.o) parts.push('o=' + st.o);
    if (st.i !== null) parts.push('i=' + st.i);
    return parts.length ? '#' + parts.join('&') : '';
  }
  function parseHash(h, meta) {
    var st = defaultState(meta);
    try {
      h = String(h || '').replace(/^#/, '');
      if (!h) return st;
      var m;
      if ((m = /^s(\d+)$/.exec(h))) { if (+m[1] < meta.n) st.i = +m[1]; return st; }
      if ((m = /^p-([\w-]+)$/.exec(h))) { if (meta.people.indexOf(m[1]) >= 0) st.p = [m[1]]; return st; }
      if (h.indexOf('=') < 0) return st;
      h.split('&').forEach(function (kv) {
        var eq = kv.indexOf('='); if (eq < 0) return;
        var k = kv.slice(0, eq), v = decodeURIComponent(kv.slice(eq + 1));
        function list(valid) { return v.split(',').filter(function (x, j, arr) { return valid.indexOf(x) >= 0 && arr.indexOf(x) === j; }); }
        switch (k) {
          case 'p': st.p = list(meta.people); break;
          case 'k': if (v === 'source' || v === 'made') st.k = v; break;
          case 'f': if (F_VALUES.indexOf(v) > 0) st.f = v; break;
          case 's': st.s = v === '1'; break;
          case 'd': st.d = list(meta.decades); break;
          case 'e': st.e = list(meta.said); break;
          case 'b': st.b = list(meta.basis); break;
          case 'q': st.q = v.slice(0, 100); break;
          case 'x': var w = parseWindow(v, meta.FULL); if (w) st.x = w; break;
          case 'w': st.w = v === '1'; break;
          case 'g': if (G_VALUES.indexOf(v) > 0) st.g = v; break;
          case 'v': if (v === 'table') st.v = v; break;
          case 'o': if (/^[a-z]+\.(1|-1)$/.test(v) && SORT_KEYS.indexOf(v.split('.')[0]) >= 0) st.o = v; break;
          case 'i': if (/^\d+$/.test(v) && +v < meta.n) st.i = +v; break;
          default: break;
        }
      });
    } catch (e) { return defaultState(meta); }
    return st;
  }
  /* @@hash-end */

  // ---- labels (every value a count, a date or a field of the public record)
  function windowLabel(d) { return d.window_lo === null ? 'by ' + d.window_hi : (d.window_lo === d.window_hi ? String(d.window_lo) : d.window_lo + ' to ' + d.window_hi); }
  function saidLabel(d) {
    if (!d.date_said) return 'date not known';
    var basis = d.date_basis === 'title' ? ' (from title)' : (d.date_basis === 'source address' ? ' (from address)' : '');
    return 'said ' + d.date_said + basis;
  }
  function kindLabel(d) { return d.kind === 'source' ? 'source text' : 'speech-to-text'; }
  var CERT = { strong: 'strong wording', plain: 'plain', hedged: 'hedged', conditional: 'conditional' };
  var BASIS_LABEL = { published: 'catalogue date', title: 'from the title', address: 'from the page address', none: 'not known' };
  var F_LABEL = { all: 'all', hedged: 'hedged', conditional: 'conditional', flagged: 'hedged or conditional', plain: 'neither hedged nor conditional', suspect: 'target before the date said' };
  var K_LABEL = { all: 'all', source: 'source text', made: 'speech-to-text made here' };
  function flagsOf(d) { var f = []; if (d.conditional) f.push('conditional'); if (d.hedged) f.push('hedged'); if (d.strong) f.push('strong wording'); if (d.suspect) f.push(d.suspect); return f; }
  function certText(d) { var f = flagsOf(d); return f.length ? f.join(', ') : 'plain'; }
  function offset(s) { s = Math.floor(s); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function aheadText(d) { return d.ahead === null ? '' : (d.ahead === 1 ? '1 year ahead' : d.ahead + ' years ahead'); }
  function tipText(d) {
    return [d.person_name, 'target ' + windowLabel(d), d.quote ? '“' + d.quote + '”' : 'quote withheld; time expression: ' + d.time_expr,
      saidLabel(d) + (d.ahead !== null ? ', ' + aheadText(d) : ''), kindLabel(d) + ', ' + certText(d), d.item_id, 'labelled candidate'].join('. ');
  }
  function fmtY(v) { return String(Math.round(v)); }

  // ---- groupings: one partition for the chart rows and the card sections
  var GROUPINGS = {
    person: { key: function (d) { return d.person_id; }, keys: PEOPLE, label: function (k) { return NAMES[k]; } },
    kind: { key: function (d) { return d.kind; }, keys: ['source', 'made'], label: function (k) { return k === 'source' ? 'source text' : 'speech-to-text made here'; } },
    said: { key: function (d) { return d.saidDecade; }, keys: SAID_ASC.concat(HAS_UNDATED ? ['none'] : []), label: function (k) { return k === 'none' ? 'date not known' : k + 's'; } },
    cert: { key: function (d) { return d.cert; }, keys: ['strong', 'plain', 'hedged', 'conditional'], label: function (k) { return CERT[k]; } },
    target: { key: function (d) { return decadeOf(d.start); }, keys: uniq(DATA.map(function (d) { return decadeOf(d.start); })).sort(function (a, b) { return decadeRank(a) - decadeRank(b); }), label: decadeLabel }
  };
  function chartGrouping() { return state.g === 'target' ? 'person' : state.g; }

  // ---- state
  var state = defaultState(META), M = DATA, V = DATA, TOKS = [];
  var expanded = {}, collapsed = {}, chart = null, booting = true, laidOut = '', lastWritten = null, hashTimer = null;
  var form = $('#toolbar'), groupsEl = $('#groups'), LI = DATA.map(function (d) { return $('#s' + d.i); });
  var SECTIONS = { person: {} };
  PEOPLE.forEach(function (p) { SECTIONS.person[p] = $('#p-' + p); });

  function tokens(q) {
    var out = [], re = /(-|−)?"([^"]*)"|(-|−)?(\S+)/g, m;
    while ((m = re.exec(q))) { var t = fold(m[2] !== undefined ? m[2] : m[4]).replace(/"/g, ''); if (t) out.push({ t: t, neg: !!(m[1] || m[3]) }); }
    return out;
  }
  function searchMatch(d) { return TOKS.every(function (tk) { return (d.search.indexOf(tk.t) >= 0) !== tk.neg; }); }
  function facetMatch(d, name) {
    switch (name) {
      case 'p': return !state.p.length || state.p.indexOf(d.person_id) >= 0;
      case 'k': return state.k === 'all' || d.kind === state.k;
      case 'f': return state.f === 'all' || (state.f === 'hedged' ? d.hedged : state.f === 'conditional' ? d.conditional : state.f === 'flagged' ? (d.hedged || d.conditional) : state.f === 'plain' ? !(d.hedged || d.conditional) : !!d.suspect);
      case 's': return !state.s || d.strong;
      case 'd': return !state.d.length || d.decades.some(function (k) { return state.d.indexOf(k) >= 0; });
      case 'e': return !state.e.length || state.e.indexOf(d.saidDecade) >= 0;
      case 'b': return !state.b.length || state.b.indexOf(d.basisKey) >= 0;
      case 'q': return searchMatch(d);
      default: return true;
    }
  }
  var FACETS = ['p', 'k', 'f', 's', 'd', 'e', 'b', 'q'];
  function matchesExcept(d, skip) { for (var j = 0; j < FACETS.length; j++) { if (FACETS[j] !== skip && !facetMatch(d, FACETS[j])) return false; } return true; }
  function matches(d) { return matchesExcept(d, null); }
  function inWindow(d) { return d.start <= state.x[1] && d.end >= state.x[0]; }
  function anyFilter() { return !!(state.p.length || state.k !== 'all' || state.f !== 'all' || state.s || state.d.length || state.e.length || state.b.length || state.q); }
  function recompute() { TOKS = tokens(state.q); M = DATA.filter(matches); V = state.w ? M.filter(inWindow) : M; }

  function update() {
    recompute();
    if (laidOut !== state.g) layoutGroups();
    renderGroups(); renderTable(); renderCount(); renderEmpty(); renderFacets(); renderActive(); renderYears(); writeForm(); renderDownloadLabel();
    if (chart) chart.render();
    applyPin(); scheduleHash();
  }
  function setWindow(win, animate) {
    state.x = clampWindow(win, FULL);
    if (chart) chart.setDomain(state.x, animate); else update();
  }

  // ---- hash: replaceState only, debounced; the view is reproducible from the address
  function scheduleHash() { clearTimeout(hashTimer); hashTimer = setTimeout(writeHash, 250); }
  function isView(h) { return /=/.test(h) || /^#(s\d+|p-[\w-]+)$/.test(h); }
  function writeHash() {
    var h = serializeHash(state, META);
    if (h === location.hash || (!h && !location.hash)) return;
    if (!h && !isView(location.hash)) return;                     // a plain anchor such as #methods is left alone
    lastWritten = h;
    try { history.replaceState(null, '', h || location.pathname + location.search); } catch (e) { }
  }
  function applyState() {
    if (!chart) state.v = 'table';
    writeForm();
    if (chart) chart.setDomain(state.x, false);
    update();
    if (state.i !== null) showPinned(false);
  }
  window.addEventListener('hashchange', function () {
    if (location.hash === lastWritten || (location.hash && !isView(location.hash))) return;
    state = parseHash(location.hash, META); applyState();
  });

  // ---- form <-> state
  function readForm() {
    state.p = $$('input[name=p]:checked', form).map(function (b) { return b.value; });
    state.k = ($('input[name=k]:checked', form) || {}).value || 'all';
    state.f = ($('input[name=f]:checked', form) || {}).value || 'all';
    state.s = !!($('input[name=s]', form) || {}).checked;
    state.d = $$('input[name=d]:checked', form).map(function (b) { return b.value; });
    state.e = $$('input[name=e]:checked', form).map(function (b) { return b.value; });
    state.b = $$('input[name=b]:checked', form).map(function (b) { return b.value; });
    state.q = $('#q').value.slice(0, 100);
    var v = $('input[name=view]:checked', form); if (v && !v.disabled) state.v = v.value;
    state.w = $('#follow').checked;
    state.g = $('#group').value;
  }
  function writeForm() {
    ['p', 'd', 'e', 'b'].forEach(function (n) { $$('input[name=' + n + ']', form).forEach(function (b) { b.checked = state[n].indexOf(b.value) >= 0; }); });
    $$('input[name=k]', form).forEach(function (b) { b.checked = b.value === state.k; });
    $$('input[name=f]', form).forEach(function (b) { b.checked = b.value === state.f; });
    var s = $('input[name=s]', form); if (s) s.checked = state.s;
    if (doc.activeElement !== $('#q')) $('#q').value = state.q;
    $('#q-clear').hidden = !state.q;
    $$('input[name=view]', form).forEach(function (b) { b.checked = b.value === state.v; });
    $('#follow').checked = state.w; $('#group').value = state.g;
    $('#clear-all').hidden = !anyFilter() && state.i === null && !state.w;
    $('#tablewrap').hidden = state.v !== 'table'; groupsEl.hidden = state.v === 'table'; $('#results-tools').hidden = state.v === 'table';
    $('#chart-caption').hidden = chartGrouping() !== 'person';
    $$('.wpreset').forEach(function (b) { b.setAttribute('aria-pressed', sameWindow(state.x, PRESETS[b.dataset.x]()) ? 'true' : 'false'); });
    var n = 0;
    $$('.facet', form).forEach(function (f) {
      var k = f.dataset.facet, on = k === 'p' ? state.p.length : k === 'k' ? state.k !== 'all' : k === 'f' ? (state.f !== 'all' || state.s) : state[k].length;
      f.classList.toggle('active', !!on); if (on) n++;
      var sel = $('.fsel', f), txt = '';
      if (k === 'p') txt = state.p.length ? state.p.length + ' of ' + PEOPLE.length : '';
      else if (k === 'k') txt = state.k === 'all' ? '' : K_LABEL[state.k];
      else if (k === 'f') txt = (state.f === 'all' ? '' : F_LABEL[state.f]) + (state.s ? (state.f === 'all' ? '' : ' · ') + 'strong' : '');
      else txt = state[k].length ? String(state[k].length) : '';
      sel.textContent = txt;
    });
    $('#filters-n').textContent = n ? String(n) : '';
  }
  var qTimer = null;
  form.addEventListener('change', function (e) { if (e.target.id === 'q') return; readForm(); update(); });
  form.addEventListener('input', function (e) { if (e.target.id !== 'q') return; clearTimeout(qTimer); qTimer = setTimeout(function () { readForm(); update(); }, 120); });
  form.addEventListener('submit', function (e) { e.preventDefault(); });
  $('#q-clear').addEventListener('click', function () { state.q = ''; $('#q').value = ''; update(); $('#q').focus(); });
  $('#clear-all').addEventListener('click', clearAll);
  function clearAll() { var d = defaultState(META); ['q', 'p', 'k', 'f', 's', 'd', 'e', 'b'].forEach(function (k) { state[k] = d[k]; }); state.w = false; state.i = null; update(); }
  $('#group').addEventListener('change', function () { readForm(); update(); });
  $('#follow').addEventListener('change', function () { readForm(); update(); });
  form.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    if (b.classList.contains('fall') || b.classList.contains('fnone')) {
      $$('input[type=checkbox]', b.closest('.fpanel')).forEach(function (c) { c.checked = b.classList.contains('fall'); });
      readForm(); update();
    } else if (b.id === 'filters-toggle') {
      var open = !$('#facets').classList.contains('open');
      $('#facets').classList.toggle('open', open); b.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
  });
  // facet popovers: one open at a time on wide screens, Escape closes, a click outside closes
  var wideQuery = window.matchMedia ? window.matchMedia('(min-width:48rem)') : null;
  var wide = function () { return wideQuery ? wideQuery.matches : window.innerWidth >= 768; };
  $$('.facet', form).forEach(function (f) {
    f.addEventListener('toggle', function () {
      if (!f.open) return;
      if (wide()) {
        $$('.facet[open]', form).forEach(function (o) { if (o !== f) o.open = false; });
        var r = f.getBoundingClientRect(); f.classList.toggle('flip', r.left > window.innerWidth / 2);
      }
    });
    f.addEventListener('keydown', function (e) { if (e.key === 'Escape' && f.open) { e.preventDefault(); e.stopPropagation(); f.open = false; $('summary', f).focus(); } });
  });
  doc.addEventListener('click', function (e) {
    if (e.target.closest('.facet')) return;
    $$('.facet[open]', form).forEach(function (o) { o.open = false; });
    if (!e.target.closest('.mark') && chart) chart.unpinTip();
  });
  // active filter tokens, each removable
  function renderActive() {
    var ul = $('#active'); ul.textContent = '';
    function tok(facet, value, text) {
      var li = el('li'), b = el('button', 'tok', text + ' ×'); b.type = 'button'; b.dataset.facet = facet; b.dataset.value = value;
      b.setAttribute('aria-label', 'remove the filter ' + text); li.appendChild(b); ul.appendChild(li);
    }
    state.p.forEach(function (p) { tok('p', p, 'Person: ' + NAMES[p]); });
    if (state.k !== 'all') tok('k', state.k, 'Kind: ' + K_LABEL[state.k]);
    if (state.f !== 'all') tok('f', state.f, 'Certainty: ' + F_LABEL[state.f]);
    if (state.s) tok('s', '1', 'Strong wording only');
    state.d.forEach(function (k) { tok('d', k, 'Target: ' + decadeLabel(k)); });
    state.e.forEach(function (k) { tok('e', k, 'Said: ' + (k === 'none' ? 'date not known' : k + 's')); });
    state.b.forEach(function (k) { tok('b', k, 'Date basis: ' + BASIS_LABEL[k]); });
    if (state.q) tok('q', '', 'Search: ' + state.q);
  }
  $('#active').addEventListener('click', function (e) {
    var b = e.target.closest('.tok'); if (!b) return;
    var k = b.dataset.facet, v = b.dataset.value;
    if (k === 'p' || k === 'd' || k === 'e' || k === 'b') state[k] = state[k].filter(function (x) { return x !== v; });
    else if (k === 'k' || k === 'f') state[k] = 'all'; else if (k === 's') state.s = false; else if (k === 'q') state.q = '';
    update();
  });
  // faceted counts: each chip counted over the data filtered by every other facet and the search
  function renderFacets() {
    var pools = {};
    ['p', 'k', 'f', 's', 'd', 'e', 'b'].forEach(function (f) { pools[f] = DATA.filter(function (d) { return matchesExcept(d, f); }); });
    $$('.chip-check', form).forEach(function (lab) {
      var inp = $('input', lab), n = inp.name, v = inp.value, pool = pools[n] || DATA, c;
      if (n === 'p') c = pool.filter(function (d) { return d.person_id === v; }).length;
      else if (n === 'k') c = v === 'all' ? pool.length : pool.filter(function (d) { return d.kind === v; }).length;
      else if (n === 'f') c = v === 'all' ? pool.length : pool.filter(function (d) { return v === 'hedged' ? d.hedged : v === 'conditional' ? d.conditional : v === 'flagged' ? (d.hedged || d.conditional) : v === 'plain' ? !(d.hedged || d.conditional) : !!d.suspect; }).length;
      else if (n === 's') c = pool.filter(function (d) { return d.strong; }).length;
      else if (n === 'd') c = pool.filter(function (d) { return d.decades.indexOf(v) >= 0; }).length;
      else if (n === 'e') c = pool.filter(function (d) { return d.saidDecade === v; }).length;
      else c = pool.filter(function (d) { return d.basisKey === v; }).length;
      $('.ccount', lab).textContent = String(c);
      if (c) lab.removeAttribute('data-zero'); else lab.setAttribute('data-zero', '');
    });
  }
  function renderCount() {
    var out = $('#count'), people = uniq(V.map(function (d) { return d.person_id; })).length;
    if (state.w && V.length !== M.length) out.textContent = M.length + ' match · ' + V.length + ' in the window ' + fmtY(state.x[0]) + ' to ' + fmtY(state.x[1]);
    else out.textContent = V.length + ' of ' + DATA.length + ' statements · ' + people + (people === 1 ? ' person' : ' people');
  }
  function renderEmpty() {
    var box = $('#empty'), why = $('#empty-why');
    box.hidden = V.length > 0; if (V.length) return;
    $('#empty-q').hidden = !state.q; $('#empty-zoom').hidden = !(state.w && M.length);
    if (M.length) why.textContent = M.length + ' statements match the filters, none between ' + fmtY(state.x[0]) + ' and ' + fmtY(state.x[1]) + '.';
    else if (state.q) { var n = DATA.filter(function (d) { return matchesExcept(d, 'q'); }).length; why.textContent = 'Nothing contains “' + state.q + '”. ' + n + ' statements match the other filters.'; }
    else why.textContent = 'All ' + DATA.length + ' statements are hidden by the current filters.';
  }
  $('#empty-clear').addEventListener('click', clearAll);
  $('#empty-q').addEventListener('click', function () { state.q = ''; update(); });
  $('#empty-zoom').addEventListener('click', function () { state.w = false; setWindow(FULL, true); update(); });

  // ---- groups of cards: li nodes move between sections (never cloned), hidden when they do not match
  function countLine(group) {
    var hedged = 0, cond = 0, src = 0, lo = Infinity, hi = -Infinity;
    group.forEach(function (d) { hedged += d.hedged ? 1 : 0; cond += d.conditional ? 1 : 0; src += d.kind === 'source' ? 1 : 0; lo = Math.min(lo, d.start); hi = Math.max(hi, d.end); });
    return group.length + ' statements · ' + hedged + ' hedged · ' + cond + ' conditional · earliest target ' + lo + ' · latest ' + hi + ' · ' + src + ' from source texts, ' + (group.length - src) + ' from speech-to-text';
  }
  function svgEl(name, attrs, parent) { var e = doc.createElementNS('http://www.w3.org/2000/svg', name); for (var k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  function sparkline(group) {
    var starts = group.map(function (d) { return d.start; }), lo = Math.floor(Math.min.apply(null, starts) / 5) * 5, hi = Math.floor(Math.max.apply(null, starts) / 5) * 5 + 5;
    var nb = (hi - lo) / 5, counts = [], j, peak = 0;
    for (j = 0; j < nb; j++) counts.push(0);
    starts.forEach(function (s) { counts[Math.floor((s - lo) / 5)]++; });
    counts.forEach(function (c) { peak = Math.max(peak, c); });
    var ends = group.map(function (d) { return d.end; });
    var svg = svgEl('svg', { 'class': 'mini', viewBox: '0 0 72 14', width: 72, height: 14, role: 'img', 'aria-label': group.length + ' statements, targets ' + Math.min.apply(null, starts) + ' to ' + Math.max.apply(null, ends) });
    var bw = 72 / nb;
    counts.forEach(function (c, j) { if (c) { var h = Math.max(1, Math.round(12 * c / peak)); svgEl('rect', { x: (j * bw).toFixed(1), y: 14 - h, width: Math.max(1, bw - 1).toFixed(1), height: h }, svg); } });
    return svg;
  }
  function makeSection(g, key, members) {
    var sec = el('section', 'group'), id = 'g-' + g + '-' + key; sec.id = id; sec.dataset.key = key;
    var h = el('h3', 'ghead'), b = el('button', 'gtoggle'); b.type = 'button'; b.setAttribute('aria-expanded', 'true'); b.setAttribute('aria-controls', id + '-cards');
    var name = el('span', 'gname', GROUPINGS[g].label(key)); b.appendChild(name); h.appendChild(b);
    h.appendChild(el('span', 'gcount num', String(members.length)));
    if (members.length) h.appendChild(sparkline(members));
    var only = el('button', 'gonly needs-js', 'only'); only.type = 'button'; only.setAttribute('aria-label', 'only this group'); h.appendChild(only);
    sec.appendChild(h);
    var sub = el('p', 'gsub countline muted', members.length ? countLine(members) : ''); sub.dataset.n = members.length; sec.appendChild(sub);
    var ol = el('ol', 'cards'); ol.id = id + '-cards'; sec.appendChild(ol);
    var more = el('button', 'more needs-js'); more.type = 'button'; more.hidden = true; sec.appendChild(more);
    return sec;
  }
  function membersOf(g, key) {
    var G = GROUPINGS[g], out = [];
    (g === 'person' ? DATA.map(function (d) { return d.i; }) : ORDER).forEach(function (i) { if (G.key(DATA[i]) === key) out.push(DATA[i]); });
    return out;
  }
  function layoutGroups() {
    var g = state.g, G = GROUPINGS[g];
    if (!SECTIONS[g]) { SECTIONS[g] = {}; G.keys.forEach(function (k) { SECTIONS[g][k] = makeSection(g, k, membersOf(g, k)); }); }
    var frag = doc.createDocumentFragment();
    G.keys.forEach(function (k) {
      var sec = SECTIONS[g][k], ol = $('.cards', sec);
      membersOf(g, k).forEach(function (d) { ol.appendChild(LI[d.i]); });
      frag.appendChild(sec);
    });
    groupsEl.textContent = ''; groupsEl.appendChild(frag); groupsEl.dataset.group = g; laidOut = g;
    var nav = $('#group-nav'); nav.textContent = '';
    nav.appendChild(new Option('Jump to group', ''));
    G.keys.forEach(function (k) { nav.appendChild(new Option(G.label(k), 'g:' + k)); });
  }
  function renderGroups() {
    var g = state.g, G = GROUPINGS[g], vis = {}; V.forEach(function (d) { vis[d.i] = true; });
    var nav = $('#group-nav'), shownGroups = {};
    G.keys.forEach(function (k) {
      var sec = SECTIONS[g][k], n = 0, total = 0;
      $$('.st', sec).forEach(function (li) { total++; var on = !!vis[li.dataset.i]; if (on) n++; li.hidden = !on || (!expanded[sec.id] && n > SHOWN); });
      sec.hidden = n === 0; shownGroups[k] = n > 0;
      sec.classList.toggle('collapsed', !!collapsed[sec.id]);
      $('.gtoggle', sec).setAttribute('aria-expanded', collapsed[sec.id] ? 'false' : 'true');
      $('.gcount', sec).textContent = n === total ? String(n) : n + ' of ' + total;
      var btn = $('.more', sec); btn.hidden = n <= SHOWN || !!expanded[sec.id]; btn.textContent = 'show all ' + n;
    });
    Array.prototype.forEach.call(nav.options, function (o) { if (o.value) o.hidden = !shownGroups[o.value.slice(2)]; });
  }
  groupsEl.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    var sec = b.closest('.group');
    if (b.classList.contains('more')) { expanded[sec.id] = true; update(); }
    else if (b.classList.contains('gtoggle')) { if (collapsed[sec.id]) delete collapsed[sec.id]; else collapsed[sec.id] = true; renderGroups(); }
    else if (b.classList.contains('gonly')) {
      var g = state.g, k = sec.dataset.key;
      if (g === 'person') state.p = [k]; else if (g === 'kind') state.k = k; else if (g === 'said') state.e = [k]; else if (g === 'target') state.d = [k];
      else if (g === 'cert') { if (k === 'strong') state.s = true; else state.f = k; }
      update();
    } else if (b.classList.contains('loc')) { locate(+b.dataset.i); }
  });
  $('#group-nav').addEventListener('change', function () {
    var v = this.value; if (!v) return;
    var sec = SECTIONS[state.g][v.slice(2)]; if (sec) { delete collapsed[sec.id]; renderGroups(); sec.scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' }); $('.gtoggle', sec).focus({ preventScroll: true }); }
    this.value = '';
  });
  $('#expand-all').addEventListener('click', function () { collapsed = {}; GROUPINGS[state.g].keys.forEach(function (k) { expanded[SECTIONS[state.g][k].id] = true; }); update(); });
  $('#collapse-all').addEventListener('click', function () { GROUPINGS[state.g].keys.forEach(function (k) { collapsed[SECTIONS[state.g][k].id] = true; }); renderGroups(); });

  // ---- twinning: hover or focus on a mark, a card or a row lights its twins
  var hotI = null;
  function hot(i) {
    unhot(); hotI = i;
    LI[i].classList.add('is-hot');
    var tr = $('#table tr[data-i="' + i + '"]'); if (tr) tr.classList.add('is-hot');
    if (chart) chart.hot(i);
  }
  function unhot() {
    if (hotI === null) return;
    LI[hotI].classList.remove('is-hot');
    var tr = $('#table tr[data-i="' + hotI + '"]'); if (tr) tr.classList.remove('is-hot');
    if (chart) chart.unhot();
    hotI = null;
  }
  groupsEl.addEventListener('mouseover', function (e) { var li = e.target.closest('.st'); if (li) hot(+li.dataset.i); });
  groupsEl.addEventListener('mouseout', function (e) { var li = e.target.closest('.st'); if (li && !li.contains(e.relatedTarget)) unhot(); });
  groupsEl.addEventListener('focusin', function (e) { var li = e.target.closest('.st'); if (li) hot(+li.dataset.i); });
  groupsEl.addEventListener('focusout', function (e) { var li = e.target.closest('.st'); if (li && !li.contains(e.relatedTarget)) unhot(); });

  // ---- pin (hash i=): the card, the mark and the row
  function applyPin() {
    $$('.is-pinned').forEach(function (n) { n.classList.remove('is-pinned'); });
    if (state.i === null) return;
    LI[state.i].classList.add('is-pinned');
    var tr = $('#table tr[data-i="' + state.i + '"]'); if (tr) tr.classList.add('is-pinned');
    if (chart) chart.pin(state.i);
  }
  function showCard(i) {
    var li = LI[i], sec = li.closest('.group');
    if (sec) { delete collapsed[sec.id]; expanded[sec.id] = true; }
    if (state.w && !inWindow(DATA[i]) && chart) chart.panTo(DATA[i].start, false);
    update();
    li.scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'center' });
  }
  function goTo(i) {
    state.i = i;
    if (state.v === 'table') { if (chart && (DATA[i].start < state.x[0] || DATA[i].start > state.x[1])) chart.panTo(DATA[i].start, true); update(); return; }
    showCard(i);
  }
  function showPinned(scroll) {
    var i = state.i, d = DATA[i], sec = LI[i].closest('.group');
    if (sec) { delete collapsed[sec.id]; expanded[sec.id] = true; }
    if (chart && (d.start < state.x[0] || d.start > state.x[1])) chart.panTo(d.start, false);
    update();
    if (scroll) LI[i].scrollIntoView({ behavior: 'auto', block: 'center' });
  }
  groupsEl.addEventListener('click', function (e) { var b = e.target.closest('.badge'); if (b && b.closest('.st') && state.i === +b.closest('.st').dataset.i) { state.i = null; update(); } });
  function locate(i) {
    if (!chart) { $('#timeline-section').scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'start' }); return; }
    if (!matches(DATA[i])) return;
    $('#chartbox').scrollIntoView({ behavior: REDUCED ? 'auto' : 'smooth', block: 'center' });
    chart.locate(i);
  }

  // ---- year index: counts per first target year of the statements shown
  function renderYears() {
    var by = {}, ul = $('#yearlist');
    V.forEach(function (d) { var k = d.start < 1950 ? 'pre' : (d.start > AXIS_END ? 'post' : String(d.start)); (by[k] = by[k] || {})[d.person_name] = ((by[k] || {})[d.person_name] || 0) + 1; });
    var keys = Object.keys(by).sort(function (a, b) { return decadeRank(a) - decadeRank(b); });
    ul.textContent = '';
    keys.forEach(function (k) {
      var li = el('li'), b = el('button', 'year'), n = el('span', 'ycount'), total = 0;
      b.type = 'button'; b.dataset.year = k; b.textContent = k === 'pre' ? 'before 1950' : (k === 'post' ? 'after ' + AXIS_END : k);
      li.appendChild(b);
      Object.keys(by[k]).sort(function (a, c) { return by[k][c] - by[k][a]; }).forEach(function (name) {
        total += by[k][name]; var s = el('span', 'pchip', name + ' '); var bb = el('b', '', String(by[k][name])); s.appendChild(bb); li.appendChild(s);
      });
      n.textContent = String(total); li.insertBefore(n, b.nextSibling); ul.appendChild(li);
    });
  }
  $('#years').addEventListener('click', function (e) {
    var b = e.target.closest('.year'); if (!b) return;
    var k = b.dataset.year, dec = k === 'pre' || k === 'post' ? k : decadeOf(+k);
    state.d = [dec]; update();
    var first = V.filter(function (d) { return d.decades.indexOf(dec) >= 0; })[0];
    if (first) showCard(first.i);
  });

  // ---- table view: every value as a text node, sortable, the sort in the hash
  var COLS = [
    { k: 'row', label: 'row', text: function (d) { return GROUPINGS[state.g].label(GROUPINGS[state.g].key(d)); }, sort: function (d) { return GROUPINGS[state.g].keys.indexOf(GROUPINGS[state.g].key(d)); } },
    { k: 'loc', label: 'timeline' },
    { k: 'person', label: 'person', text: function (d) { return d.person_name; }, sort: function (d) { return PEOPLE.indexOf(d.person_id); } },
    { k: 'said', label: 'date said', sort: function (d) { return d.date_said || '~'; } },
    { k: 'start', label: 'target', sort: function (d) { return d.start * 1e4 + (d.end - d.start); } },
    { k: 'span', label: 'span', text: function (d) { return d.end > d.start ? String(d.end - d.start) : ''; }, sort: function (d) { return d.end - d.start; } },
    { k: 'ahead', label: 'ahead', text: function (d) { return d.ahead === null ? '' : String(d.ahead); }, sort: function (d) { return d.ahead === null ? -1e9 : d.ahead; } },
    { k: 'kind', label: 'kind', sort: function (d) { return d.kind; } },
    { k: 'cert', label: 'certainty', text: certText, sort: certText },
    { k: 'quote', label: 'quote', sort: function (d) { return d.quote ? fold(d.quote) : '~' + fold(d.time_expr); } },
    { k: 'item', label: 'item', text: function (d) { return d.item_id; }, sort: function (d) { return d.item_id; } },
    { k: 'link', label: 'link', sort: function (d) { return d.link ? (d.public_page_kind || '') : '~'; } }
  ];
  function sortedView() {
    if (!state.o) return V;
    var key = state.o.split('.')[0], dir = state.o.split('.')[1] === '-1' ? -1 : 1, col = COLS.filter(function (c) { return c.k === key; })[0];
    if (!col || !col.sort) return V;
    return V.slice().sort(function (a, b) { var x = col.sort(a), y = col.sort(b); return ((x < y ? -1 : (x > y ? 1 : 0)) || (a.i - b.i)) * dir; });
  }
  var lastTableSig = '';
  function cell(tr, text, cls) { var td = tr.insertCell(); if (text !== undefined) td.textContent = text; if (cls) td.className = cls; return td; }
  function renderTable() {
    var table = $('#table'), thead = table.tHead, tbody = table.tBodies[0], tfoot = table.tFoot;
    if (state.v !== 'table') return;
    if (!thead.rows.length) {
      var tr = thead.insertRow();
      COLS.forEach(function (c) {
        var th = el('th'); th.scope = 'col';
        if (c.sort) { var b = el('button', '', c.label); b.type = 'button'; b.dataset.key = c.k; b.addEventListener('click', function () { var cur = state.o.split('.'); state.o = cur[0] === c.k ? (cur[1] === '1' ? c.k + '.-1' : '') : c.k + '.1'; update(); }); th.appendChild(b); }
        else th.textContent = c.label;
        tr.appendChild(th);
      });
    }
    var cur = state.o.split('.');
    $$('th', thead).forEach(function (th) { var b = th.firstChild; if (b && b.dataset && cur[0] === b.dataset.key) th.setAttribute('aria-sort', cur[1] === '-1' ? 'descending' : 'ascending'); else th.removeAttribute('aria-sort'); });
    var rows = sortedView();
    $('caption', table).textContent = 'Statements matching the filters, ' + rows.length + ' rows';
    var sig = state.o + '|' + rows.map(function (d) { return d.i; }).join(',');
    if (sig === lastTableSig && tbody.rows.length === rows.length) return;    // same rows in the same order: keep them (and any focus inside)
    lastTableSig = sig;
    tbody.textContent = ''; tfoot.textContent = '';
    rows.forEach(function (d) {
      var tr = tbody.insertRow(); tr.dataset.i = d.i;
      cell(tr, COLS[0].text(d));
      var lc = cell(tr), lb = el('button', 'loc', 'timeline'); lb.type = 'button'; lb.dataset.i = d.i; lb.setAttribute('aria-label', 'show on the timeline'); lc.appendChild(lb);
      cell(tr, d.person_name);
      var sc = cell(tr, d.date_said || 'not known'); if (d.date_said) { var bs = el('span', 'muted', ' · ' + BASIS_LABEL[d.basisKey]); sc.appendChild(bs); }
      var wc = cell(tr), badge = el('span', 'badge num', windowLabel(d)); wc.appendChild(badge);
      cell(tr, COLS[5].text(d), 'num'); cell(tr, COLS[6].text(d), 'num');
      var kc = cell(tr), chip = el('span', 'chip chip-' + d.kind, kindLabel(d)); kc.appendChild(chip);
      cell(tr, certText(d));
      cell(tr, d.quote ? '“' + d.quote + '”' : '(withheld) ' + d.time_expr, 'quote');
      cell(tr, d.item_id, 'mono');
      var lk = cell(tr);
      if (d.link) { var a = el('a', '', (d.public_page_kind === 'page' ? 'public page' : 'episode page') + (d.kind === 'made' && d.offset_s !== null ? ' · at ' + offset(d.offset_s) : '')); a.href = d.link; a.rel = 'noopener'; lk.appendChild(a); }
      else lk.textContent = d.kind === 'made' && d.offset_s !== null ? 'at ' + offset(d.offset_s) + ' of the recording' : 'no public page known';
    });
    if (!rows.length) { var er = tfoot.insertRow(); er.className = 'empty'; var td = er.insertCell(); td.colSpan = COLS.length; td.textContent = 'No statements match.'; }
  }
  $('#table').addEventListener('click', function (e) {
    var tr = e.target.closest('tr[data-i]'); if (!tr) return;
    if (e.target.closest('a')) return;
    if (e.target.closest('.loc')) { locate(+tr.dataset.i); return; }
    goTo(+tr.dataset.i);
  });
  $('#table').addEventListener('mouseover', function (e) { var tr = e.target.closest('tr[data-i]'); if (tr) hot(+tr.dataset.i); });
  $('#table').addEventListener('mouseout', function (e) { var tr = e.target.closest('tr[data-i]'); if (tr && !tr.contains(e.relatedTarget)) unhot(); });
  $('#table').addEventListener('focusin', function (e) { var tr = e.target.closest('tr[data-i]'); if (tr) hot(+tr.dataset.i); });

  // ---- CSV of the rows shown (public fields only; the data is already in the page)
  function csvCell(v) {
    if (v === null || v === undefined) return '';
    var s = String(v);
    if (/^[=+\-@\t\r]/.test(s)) s = "'" + s;
    return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }
  $('#download').addEventListener('click', function () {
    var rows = sortedView(), lines = [PUBLIC_KEYS.map(csvCell).join(',')];
    rows.forEach(function (d) { lines.push(PUBLIC_KEYS.map(function (k) { var v = d[k]; return csvCell(typeof v === 'boolean' ? (v ? 1 : 0) : v); }).join(',')); });
    var blob = new Blob(['\ufeff' + lines.join('\r\n') + '\r\n'], { type: 'text/csv;charset=utf-8' });
    var url = URL.createObjectURL(blob), a = el('a'); a.href = url; a.download = 'prediction-timelines.' + 'csv'; doc.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  });
  function renderDownloadLabel() { $('#download').textContent = 'Download CSV (' + V.length + ' rows)'; }

  // ---- the chart: d3 v7 only here; null when the library did not load
  var PRESETS = {
    all: function () { return FULL.slice(); },
    past: function () { return clampWindow([FULL[0], BUILD_YEAR], FULL); },
    next5: function () { return clampWindow([BUILD_YEAR - .5, BUILD_YEAR + 5.5], FULL); },
    decade: function () { return clampWindow([Math.floor(BUILD_YEAR / 10) * 10, Math.floor(BUILD_YEAR / 10) * 10 + 10], FULL); },
    '2030s': function () { return clampWindow([2030, 2040], FULL); },
    later: function () { return clampWindow([2040, FULL[1]], FULL); }
  };
  function initChart() {
    if (!window.d3 || root.classList.contains('no-d3')) return null;
    var d3 = window.d3;
    var box = $('#chartbox'), scroll = $('#chart-scroll'), svgNode = $('#chart-svg'), tip = $('#tip'), status = $('#chart-status');
    var svg = d3.select(svgNode), axisSvg = d3.select('#chart-axis'), mini = d3.select('#minimap');
    var W = 800, L = 150, R = 20, plotW = 630, H = 42, rowH = 30, band = 24, narrow = false, miniH = 44;
    var xFull = d3.scaleLinear().domain(FULL), x = xFull, t = d3.zoomIdentity, ready = false, pending = false;
    var syncing = false, armed = false, armTimer = null, rows = [], rowKeys = [], allItems = [], visItems = [], rowAll = [], itemByKey = {}, stackOf = {};
    var B = 1, ppy = 10, roving = null, entered = false, tipPinned = null, statusTimer = null, endTimer = null, lastRows = '', relayout = false;
    svg.append('title').text('Timeline of target years');
    var desc = svg.append('desc').attr('id', 'chart-desc');
    var defs = svg.append('defs'); var clipRect = defs.append('clipPath').attr('id', 'plot-clip').append('rect');
    var bandsG = svg.append('g').attr('class', 'bands'), pastRect = svg.append('rect').attr('class', 'past');
    var gridG = svg.append('g').attr('class', 'grid'), zoomSurface = svg.append('rect').attr('class', 'zoom-surface');
    var nowLine = svg.append('line').attr('class', 'now');
    var plotG = svg.append('g').attr('class', 'plot').attr('clip-path', 'url(#plot-clip)');
    var barsG = plotG.append('g').attr('class', 'bars'), leadsG = plotG.append('g').attr('class', 'leads'), marksG = plotG.append('g').attr('class', 'marks');
    var labelsG = svg.append('g').attr('class', 'rowlabels');
    var axisG = axisSvg.append('g').attr('class', 'axis').attr('transform', 'translate(0,29)');
    var nowLabel = axisSvg.append('text').attr('class', 'nowlabel').attr('y', 9).text('now');
    var miniDensity = mini.append('g').attr('class', 'density'), miniVis = mini.append('g').attr('class', 'density-vis'), miniAxis = mini.append('g').attr('class', 'mini-axis');
    var miniNow = mini.append('line').attr('class', 'now-mini'), miniG = mini.append('g').attr('class', 'brush'), handles = null;

    var zoom = d3.zoom().scaleExtent([1, 40])
      .filter(function (ev) {
        if (ev.type === 'wheel') return ev.ctrlKey || ev.metaKey || armed;
        if (ev.type.indexOf('touch') === 0) return !!(ev.touches && ev.touches.length >= 2);
        return !ev.button && !(ev.target.closest && ev.target.closest('.rowlabel,button'));
      })
      .on('start', function (ev) { if (ev.sourceEvent) { hideTip(); svg.classed('dragging', true); } })
      .on('zoom', function (ev) { t = ev.transform; schedule(); if (!syncing) moveBrush(); })
      .on('end', function () {
        svg.classed('dragging', false);
        var dom = domain(); state.x = [Math.round(dom[0] * 100) / 100, Math.round(dom[1] * 100) / 100];
        if (booting) return;
        renderNow();
        if (relayout) return;                                         // the rows changed inside update(): no second update
        clearTimeout(endTimer); endTimer = setTimeout(function () { update(); announce(); }, 60);
      });
    svg.call(zoom).on('dblclick.zoom', null).style('touch-action', 'pan-y');
    svg.on('dblclick', function (ev) {
      var m = ev.target.closest && ev.target.closest('.mark');
      if (m) { var it = itemByKey[m.getAttribute('data-key')]; var y = it.single ? it.d.start : it.bin + (B - 1) / 2; setDomain([y - 2, y + 2], true); }
      else svg.transition().duration(DUR).call(zoom.scaleBy, 2, d3.pointer(ev, svgNode));
      ev.preventDefault();
    });
    var brush = d3.brushX().handleSize(24).on('brush end', function (ev) {
      if (!ev.sourceEvent || syncing) return;
      if (!ev.selection) {
        if (ev.type === 'end') { var px = d3.pointer(ev.sourceEvent, mini.node())[0], c = xFull.invert(px), half = (state.x[1] - state.x[0]) / 2; setDomain(shiftWindow([c - half, c + half], FULL), false); }
        return;
      }
      syncing = true; setDomain(ev.selection.map(xFull.invert), false); syncing = false;
      drawHandles(ev.selection);
    });
    miniG.call(brush);
    handles = miniG.selectAll('.handle--custom').data([0, 1]).enter().append('rect').attr('class', 'handle--custom').attr('width', 4).attr('rx', 2);
    function drawHandles(sel) { if (!sel) return; handles.attr('x', function (d, j) { return sel[j] - 2; }).attr('y', 4).attr('height', miniH - 16); }

    function domain() { return t.rescaleX(xFull).domain(); }
    function layout() {
      var w = scroll.clientWidth || (box.clientWidth - 8); W = Math.max(320, w || 800); narrow = W < 560;
      if (narrow) { L = 8; R = 8; } else { L = 150; R = 20; }
      plotW = W - L - R;
      var keys = rowKeys.slice();
      rowH = narrow ? (keys.length <= 4 ? 52 : 38) : (keys.length <= 4 ? 48 : 30); band = rowH - 6;
      H = 12 + Math.max(1, keys.length) * rowH;
      var cur = ready ? domain() : state.x;
      xFull.range([L, L + plotW]);
      svg.attr('viewBox', '0 0 ' + W + ' ' + H).attr('width', W).attr('height', H);
      axisSvg.attr('viewBox', '0 0 ' + W + ' 30').attr('width', W).attr('height', 30).style('width', W + 'px');
      miniH = narrow ? 36 : 44; mini.attr('viewBox', '0 0 ' + W + ' ' + miniH).attr('width', W).attr('height', miniH).style('width', W + 'px'); $('#minimap').style.height = miniH + 'px';
      clipRect.attr('x', L - 12).attr('y', 0).attr('width', plotW + 24).attr('height', H);
      zoomSurface.attr('x', L).attr('y', 0).attr('width', plotW).attr('height', H);
      pastRect.attr('y', 0).attr('height', H); nowLine.attr('y1', 0).attr('y2', H);
      zoom.translateExtent([[L, 0], [L + plotW, H]]).extent([[L, 0], [L + plotW, H]]);
      brush.extent([[L, 0], [L + plotW, miniH - 12]]); miniG.call(brush); miniG.selectAll('.handle--custom').raise();
      bandsG.selectAll('rect').data(keys.filter(function (k, j) { return j % 2 === 0; })).join('rect').attr('class', 'band').attr('x', 0).attr('width', W)
        .attr('y', function (k) { return 12 + keys.indexOf(k) * rowH; }).attr('height', rowH);
      drawMini();
      ready = true;
      relayout = true;
      try { setDomain(cur, false); } finally { relayout = false; }
    }
    function drawMini() {
      var years = d3.range(FULL[0], FULL[1] + 1), all = {}, vis = {}, peak = 1;
      DATA.forEach(function (d) { all[d.start] = (all[d.start] || 0) + 1; });
      M.forEach(function (d) { vis[d.start] = (vis[d.start] || 0) + 1; });
      years.forEach(function (y) { peak = Math.max(peak, all[y] || 0); });
      var top = miniH - 12, yw = Math.max(1, xFull(FULL[0] + 1) - xFull(FULL[0]) - .5);
      function bar(sel, counts) {
        sel.selectAll('rect').data(years.filter(function (y) { return counts[y]; }), function (y) { return y; }).join('rect')
          .attr('x', function (y) { return xFull(y); }).attr('width', yw)
          .attr('y', function (y) { return top - Math.max(1, (top - 2) * Math.log(1 + counts[y]) / Math.log(1 + peak)); })
          .attr('height', function (y) { return Math.max(1, (top - 2) * Math.log(1 + counts[y]) / Math.log(1 + peak)); });
      }
      bar(miniDensity, all); bar(miniVis, vis);
      var step = narrow ? 40 : 20, labels = years.filter(function (y) { return y % step === 0; });
      miniAxis.selectAll('text').data(labels).join('text').attr('x', function (y) { return xFull(y); }).attr('y', miniH - 2).text(function (y) { return String(y); });
      miniNow.attr('x1', xFull(NOW_F)).attr('x2', xFull(NOW_F)).attr('y1', 0).attr('y2', top);
    }
    function moveBrush() { if (!ready) return; var sel = domain().map(xFull); syncing = true; miniG.call(brush.move, sel); syncing = false; drawHandles(sel); }
    function setDomain(win, animate) {
      win = clampWindow(win, FULL);
      var k = Math.min(40, Math.max(1, (FULL[1] - FULL[0]) / (win[1] - win[0])));
      var tr = d3.zoomIdentity.translate(L, 0).scale(k).translate(-xFull(win[0]), 0);
      if (animate && DUR) svg.transition().duration(DUR).call(zoom.transform, tr);
      else svg.call(zoom.transform, tr);
    }
    function panTo(year, animate) { var dom = domain(), half = (dom[1] - dom[0]) / 2; setDomain(shiftWindow([year - half, year + half], FULL), animate); }
    function schedule() { if (pending) return; pending = true; requestAnimationFrame(function () { if (pending) render(); }); }
    function renderNow() { pending = false; render(); }

    function rowsFor() {
      var g = chartGrouping(), G = GROUPINGS[g], by = {};
      M.forEach(function (d) { var k = G.key(d); (by[k] = by[k] || []).push(d); });
      return G.keys.filter(function (k) { return by[k]; }).map(function (k) { return { key: k, label: G.label(k), items: by[k] }; });
    }
    function memberCmp(a, b) { return cmpStr(a.date_said || '9999', b.date_said || '9999') || cmpStr(a.item_id, b.item_id) || (a.i - b.i); }
    function render() {
      pending = false; if (!ready) return;
      rows = rowsFor();
      var keys = rows.map(function (r) { return r.key; }), sig = chartGrouping() + ':' + keys.join('|');
      if (sig !== lastRows) { lastRows = sig; rowKeys = keys; layout(); return; }
      x = t.rescaleX(xFull);
      var dom = x.domain(); ppy = plotW / (dom[1] - dom[0]);
      var labelStep = [1, 2, 5, 10, 20, 50].filter(function (s) { return s * ppy >= (narrow ? 44 : 56); })[0] || 50;
      var tickStep = labelStep === 1 ? 1 : ((labelStep === 2 || labelStep === 20) ? labelStep / 2 : labelStep / 5);
      B = ppy >= 12 ? 1 : (ppy >= 6 ? 2 : (ppy >= 2.5 ? 5 : 10));
      var t0 = Math.ceil(dom[0] / tickStep) * tickStep, ticks = d3.range(t0, dom[1] + 1e-9, tickStep).map(function (v) { return Math.round(v * 1e6) / 1e6; });
      axisG.call(d3.axisTop(x).tickValues(ticks).tickFormat(function (v) { return Math.abs(v / labelStep - Math.round(v / labelStep)) < 1e-6 ? String(v) : ''; }).tickSizeOuter(0).tickPadding(4));
      axisG.selectAll('.tick').attr('class', function (v) { return 'tick ' + (Math.abs(v / labelStep - Math.round(v / labelStep)) < 1e-6 ? 'major' : 'minor'); });
      var nowIn = NOW_F >= dom[0] && NOW_F <= dom[1];
      nowLabel.attr('x', x(NOW_F)).style('display', nowIn ? null : 'none');
      nowLine.attr('x1', x(NOW_F)).attr('x2', x(NOW_F)).style('display', nowIn ? null : 'none');
      gridG.selectAll('line').data(ticks.filter(function (v) { return Math.abs(v / labelStep - Math.round(v / labelStep)) < 1e-6; }), function (v) { return v; }).join('line')
        .attr('class', 'major').attr('x1', x).attr('x2', x).attr('y1', 0).attr('y2', H);
      var px0 = Math.max(L, x(FULL[0])), px1 = Math.min(L + plotW, x(Math.min(NOW_F, FULL[1])));
      pastRect.attr('x', px0).attr('width', Math.max(0, px1 - px0));
      // items: singles dodged inside a bin, a stack when a bin overflows
      allItems = []; rowAll = []; stackOf = {}; var left = 0, right = 0;
      var maxDodge = Math.floor(band / 6), cols = (B === 1 && ppy >= 24) ? Math.max(1, Math.min(6, Math.floor((ppy - 2) / 9))) : 1;
      rows.forEach(function (row, r) {
        var cy = 12 + r * rowH + rowH / 2, bins = {}, list = [];
        row.items.forEach(function (d) { var b = Math.floor(d.start / B) * B; (bins[b] = bins[b] || []).push(d); });
        Object.keys(bins).forEach(function (bk) {
          var b = +bk, mem = bins[bk].sort(memberCmp), n = mem.length;
          if (n <= cols * maxDodge) {
            var cu = Math.min(cols, n), ru = Math.ceil(n / cu);
            mem.forEach(function (d, j) { var col = j % cu, rj = Math.floor(j / cu); list.push({ key: 'i' + d.i, single: true, d: d, row: r, year: d.start, cx: x(d.start) + col * 9, cy: cy + (rj - (ru - 1) / 2) * 6 }); });
          } else {
            var lo = Infinity, hi = -Infinity, kinds = {}, strong = false, dense = B === 1 && n > 6 * maxDodge;
            mem.forEach(function (d) { lo = Math.min(lo, d.start); hi = Math.max(hi, d.end); kinds[d.kind] = true; strong = strong || d.strong; });
            var it = { key: 's' + r + '|' + b, stack: true, members: mem, n: n, row: r, bin: b, year: b + (B - 1) / 2, cx: x(b + (B - 1) / 2), cy: cy, w: Math.max(22, B * ppy - 2), lo: lo, hi: hi, kind: Object.keys(kinds).length === 1 ? Object.keys(kinds)[0] : '', strong: strong, dense: dense };
            mem.forEach(function (d) { stackOf[d.i] = it.key; });
            list.push(it);
          }
        });
        list.sort(function (a, b) { return (a.cx - b.cx) || (a.cy - b.cy); });
        rowAll.push(list);
        list.forEach(function (it) { it.off = it.cx < L - 12 || it.cx > L + plotW + 12; if (it.off) { if (it.cx < L) left += it.n || 1; else right += it.n || 1; } allItems.push(it); });
      });
      visItems = allItems.filter(function (it) { return !it.off; });
      itemByKey = {}; allItems.forEach(function (it) { itemByKey[it.key] = it; });
      var sel = marksG.selectAll('g.mark').data(visItems, function (it) { return it.key; });
      sel.exit().remove();
      var enter = sel.enter().append('g').attr('class', function (it) { return 'mark ' + (it.single ? 'single' : 'stack'); }).attr('data-key', function (it) { return it.key; })
        .attr('role', 'button').attr('tabindex', -1).each(function (it) { buildMark(d3.select(this), it); });
      sel.merge(enter).attr('transform', function (it) { return 'translate(' + it.cx + ',' + it.cy + ')'; }).each(function (it) { updateMark(d3.select(this), it); });
      var bars = barsG.selectAll('rect').data(visItems.filter(function (it) { return it.single ? it.d.end > it.d.start : it.hi > it.lo; }), function (it) { return 'b' + it.key; });
      bars.exit().remove();
      bars.enter().append('rect').attr('class', function (it) { return it.single ? 'bar bar-' + it.d.kind : 'stackbar'; }).attr('height', 3).attr('rx', 1.5).merge(bars)
        .attr('x', function (it) { return it.single ? x(it.d.start) : x(it.lo); }).attr('y', function (it) { return it.cy - 1.5; })
        .attr('width', function (it) { return Math.max(1, it.single ? x(it.d.end) - x(it.d.start) : x(it.hi) - x(it.lo)); });
      renderLabels();
      if (roving && !itemByKey[roving]) roving = null;
      marksG.selectAll('g.mark').attr('tabindex', function (it) { return entered && it.key === roving ? 0 : -1; });
      $('.edge-left', box).hidden = !left; $('.edge-left', box).textContent = '◂ ' + left;
      $('.edge-right', box).hidden = !right; $('.edge-right', box).textContent = right + ' ▸';
      desc.text(M.length + ' statements in ' + rows.length + ' rows; the window shows ' + fmtY(dom[0]) + ' to ' + fmtY(dom[1]) + '; ' + visItems.filter(function (it) { return it.stack; }).length + ' stacks');
      if (state.i !== null) pin(state.i);
      if (hotI !== null) chartHot(hotI);
      drawMini();
    }
    function buildMark(g, it) {
      if (it.single) {
        var d = it.d, cls = 'm-' + d.kind + ((d.hedged || d.conditional) ? ' hollow' : '') + (d.suspect ? ' m-suspect' : '');
        g.attr('data-i', d.i).attr('data-row', it.row).attr('aria-label', tipText(d));
        if (d.window_lo === null) { g.append('line').attr('class', 'leader').attr('x1', -18).attr('x2', -8).attr('y1', 0).attr('y2', 0); g.append('path').attr('class', cls).attr('d', 'M0 -5L-8 0L0 5Z'); }
        else if (d.kind === 'source') g.append('circle').attr('class', cls).attr('r', 4);
        else g.append('path').attr('class', cls).attr('d', 'M0 -5l5 5-5 5-5-5z');
        if (d.strong) g.append('circle').attr('class', 'ring').attr('r', 7);
        g.append('circle').attr('class', 'hit').attr('r', 12);
      } else {
        g.attr('data-row', it.row);
        g.append('rect').attr('class', 'pill').attr('height', 16).attr('y', -8).attr('rx', 8);
        g.append('text').attr('class', 'count-t').attr('y', 4);
        g.append('rect').attr('class', 'hit').attr('height', 24).attr('y', -12);
      }
    }
    function updateMark(g, it) {
      if (it.single) return;
      g.attr('aria-label', it.n + ' statements between ' + it.lo + ' and ' + it.hi + ' on this row; press Enter to ' + (it.dense ? 'open the list' : 'zoom in'));
      g.select('.pill').attr('class', 'pill' + (it.kind ? ' one-' + it.kind : '') + (it.strong ? ' strong' : '')).attr('width', it.w).attr('x', -it.w / 2);
      g.select('.count-t').text(String(it.n));
      g.select('.hit').attr('width', Math.max(24, it.w)).attr('x', -Math.max(24, it.w) / 2);
    }
    var labelCache = {};
    function labelAt(r) {
      var row = rows[r]; if (!row) return null;
      return labelsG.selectAll('text.rowlabel.btn-label').filter(function (d) { return d && d.key === row.key; }).node();
    }
    function renderLabels() {
      var isPerson = chartGrouping() === 'person';
      var lab = labelsG.selectAll('g.rl').data(rows, function (r) { return r.key; });
      lab.exit().remove();
      var ent = lab.enter().append('g').attr('class', 'rl');
      ent.append('rect').attr('class', 'rowpill').attr('rx', 4);
      ent.append('text').attr('class', 'rowlabel');
      ent.select('text').append('title');
      ent.select('text').append('tspan');
      var all = lab.merge(ent).order();
      all.each(function (r, j) {
        var g = d3.select(this), txt = g.select('text'), rect = g.select('rect'), span = txt.select('tspan');
        txt.attr('class', 'rowlabel' + (isPerson ? ' btn-label' : '')).attr('data-key', r.key).attr('role', isPerson ? 'button' : null)
          .attr('tabindex', isPerson ? -1 : null).attr('aria-pressed', isPerson ? (state.p.indexOf(r.key) >= 0 ? 'true' : 'false') : null);
        txt.select('title').text(r.label + ': ' + r.items.length + ' statements found');
        var node = txt.node(), full = r.label, maxW = narrow ? Math.min(plotW - 16, 160) : L - 14, ck = full + '|' + maxW, c = labelCache[ck];
        if (c) span.text(c.s);
        else {
          span.text(full);
          var len = node.getComputedTextLength ? node.getComputedTextLength() : full.length * 6.5, s = full;
          while (len > maxW && s.length > 2) { s = s.slice(0, -2); span.text(s + '…'); len = node.getComputedTextLength ? node.getComputedTextLength() : s.length * 6.5; }
          c = labelCache[ck] = { s: s, len: len };
        }
        if (narrow) {
          txt.attr('x', L + 6).attr('y', 12 + j * rowH + 11).attr('text-anchor', 'start');
          rect.attr('x', L + 2).attr('y', 12 + j * rowH + 1).attr('width', c.len + 8).attr('height', 14).style('display', null);
        } else { txt.attr('x', L - 10).attr('y', 12 + j * rowH + rowH / 2 + 4).attr('text-anchor', 'end'); rect.style('display', 'none'); }
      });
    }
    // tooltip (text nodes only) and the lead line from the year said
    function showTip(it, node) {
      tip.textContent = '';
      if (it.single) {
        var d = it.d, b = el('b'), sample = svgEl('svg', { viewBox: '0 0 14 14', 'aria-hidden': 'true' });
        var cls = 'm-' + d.kind + ((d.hedged || d.conditional) ? ' hollow' : '');
        if (d.window_lo === null) svgEl('path', { d: 'M12 2L3 7l9 5z', 'class': cls }, sample); else if (d.kind === 'source') svgEl('circle', { cx: 7, cy: 7, r: 4, 'class': cls }, sample); else svgEl('path', { d: 'M7 2l5 5-5 5-5-5z', 'class': cls }, sample);
        b.appendChild(doc.createTextNode(windowLabel(d) + ' ')); b.appendChild(sample); b.appendChild(doc.createTextNode(' ' + d.person_name)); tip.appendChild(b);
        tip.appendChild(el('div', 'tq', d.quote ? '“' + d.quote + '”' : 'quote withheld; time expression: ' + d.time_expr));
        tip.appendChild(el('div', 'muted', [saidLabel(d) + (d.ahead !== null ? ' · ' + aheadText(d) : ''), kindLabel(d) + ', ' + certText(d), d.item_id, 'labelled candidate'].join(' · ')));
        tip.appendChild(el('div', 'hint', COARSE ? 'tap again: open the card' : 'click: open the card · double-click: zoom here'));
      } else {
        tip.appendChild(el('b', '', it.n + ' statements · ' + (it.lo === it.hi ? String(it.lo) : it.lo + ' to ' + it.hi)));
        tip.appendChild(el('div', 'muted', it.dense ? 'one year; click or press Enter to open the list' : 'zoom in or press Enter to spread them'));
      }
      tip.hidden = false;
      var wrap = box.getBoundingClientRect(), r = node.getBoundingClientRect();
      var left = r.left - wrap.left + 14, top = r.top - wrap.top + 16;
      if (left + tip.offsetWidth > wrap.width - 8) left = Math.max(0, r.left - wrap.left - tip.offsetWidth - 8);
      if (top + tip.offsetHeight > wrap.height - 8) top = Math.max(0, r.top - wrap.top - tip.offsetHeight - 8);
      tip.style.left = left + 'px'; tip.style.top = top + 'px';
    }
    function hideTip() { tip.hidden = true; tipPinned = null; }
    function drawLead(it) {
      leadsG.selectAll('*').remove();
      if (!it || !it.single) return;
      var d = it.d; if (!d.saidYear || d.saidYear < FULL[0] || d.saidYear > FULL[1]) return;
      leadsG.append('line').attr('class', 'lead').attr('x1', x(d.saidYear)).attr('x2', it.cx).attr('y1', it.cy).attr('y2', it.cy);
      leadsG.append('circle').attr('class', 'lead-dot').attr('cx', x(d.saidYear)).attr('cy', it.cy).attr('r', 2.5);
    }
    function nodeFor(i) { var key = stackOf[i] || ('i' + i); return $('.mark[data-key="' + key + '"]', svgNode); }
    function chartHot(i) { marksG.selectAll('.is-hot').classed('is-hot', false); var n = nodeFor(i); if (n) { n.classList.add('is-hot'); var it = itemByKey[n.getAttribute('data-key')]; drawLead(it); } }
    function chartUnhot() { marksG.selectAll('.is-hot').classed('is-hot', false); drawLead(null); if (!tipPinned) hideTip(); }
    function pin(i) { marksG.selectAll('.is-pinned').classed('is-pinned', false); var n = nodeFor(i); if (n) n.classList.add('is-pinned'); }
    svgNode.addEventListener('pointerover', function (e) {
      var m = e.target.closest('.mark'); if (!m) return;
      var it = itemByKey[m.getAttribute('data-key')]; if (!it) return;
      if (it.single) hot(it.d.i); else { unhot(); m.classList.add('is-hot'); }
      if (!COARSE) showTip(it, m);
    });
    svgNode.addEventListener('pointerout', function (e) { var m = e.target.closest('.mark'); if (m && !m.contains(e.relatedTarget)) { unhot(); m.classList.remove('is-hot'); if (!tipPinned) hideTip(); } });
    svgNode.addEventListener('focusin', function (e) {
      var m = e.target.closest('.mark'); armed = true;
      if (!m) return;
      var it = itemByKey[m.getAttribute('data-key')]; if (!it) return;
      if (it.single) hot(it.d.i); else m.classList.add('is-hot');
      showTip(it, m);
    });
    svgNode.addEventListener('focusout', function (e) { var m = e.target.closest('.mark'); if (m) { unhot(); m.classList.remove('is-hot'); hideTip(); } });
    svgNode.addEventListener('click', function (e) {
      var m = e.target.closest('.mark');
      if (!m) { var lbl = e.target.closest('.rowlabel'); if (lbl && chartGrouping() === 'person') togglePerson(lbl.getAttribute('data-key')); return; }
      var it = itemByKey[m.getAttribute('data-key')]; if (!it) return;
      activate(it, m);
    });
    function activate(it, m) {
      if (it.single) {
        if (COARSE && tipPinned !== it.key) { tipPinned = it.key; showTip(it, m); return; }
        tipPinned = null; goTo(it.d.i);
      } else if (it.dense) {
        state.w = true; state.x = clampWindow([it.bin - 1.5, it.bin + 2.5], FULL); setDomain(state.x, false); showCard(it.members[0].i);
      } else setDomain([it.bin - 1, it.bin + B + 1], true);
    }
    function togglePerson(pid) { var j = state.p.indexOf(pid); if (j >= 0) state.p.splice(j, 1); else state.p.push(pid); update(); }
    // keyboard: the svg is one tab stop; Enter enters the marks, which then take real focus
    function focusMark(key) {
      var n = $('.mark[data-key="' + key + '"]', svgNode); if (!n) return false;
      entered = true; roving = key;
      marksG.selectAll('g.mark').attr('tabindex', function (it) { return it.key === key ? 0 : -1; });
      var it = itemByKey[key], rowTop = 12 + it.row * rowH;
      if (rowTop < scroll.scrollTop || rowTop + rowH > scroll.scrollTop + scroll.clientHeight) scroll.scrollTop = Math.max(0, rowTop - scroll.clientHeight / 2);
      n.focus({ preventScroll: true });
      return true;
    }
    function focusItem(it) { if (!it) return; if (it.off) { panTo(it.year, false); renderNow(); } focusMark(it.key); }
    function nearestOnRow(r, cx) { var list = rowAll[r]; if (!list || !list.length) return null; var best = list[0]; list.forEach(function (it) { if (Math.abs(it.cx - cx) < Math.abs(best.cx - cx)) best = it; }); return best; }
    function pan(frac) { var dom = domain(), w = dom[1] - dom[0]; setDomain(shiftWindow([dom[0] + w * frac, dom[1] + w * frac], FULL), false); }
    function zoomBy(k) { svg.transition().duration(DUR).call(zoom.scaleBy, k, [L + plotW / 2, H / 2]); }
    function fit() { if (!M.length) return; var lo = Infinity, hi = -Infinity; M.forEach(function (d) { lo = Math.min(lo, d.start); hi = Math.max(hi, d.end); }); setDomain([lo - 1, hi + 1], true); }
    svgNode.addEventListener('keydown', function (ev) {
      var m = ev.target.closest && ev.target.closest('.mark'), lbl = ev.target.closest && ev.target.closest('.rowlabel');
      if (m) { markKeys(ev, m); return; }
      if (lbl) { labelKeys(ev, lbl); return; }
      if (ev.target !== svgNode) return;
      var k = ev.key;
      if (k === 'ArrowLeft') pan(ev.shiftKey ? -.5 : -.1); else if (k === 'ArrowRight') pan(ev.shiftKey ? .5 : .1);
      else if (k === 'ArrowUp') scroll.scrollTop -= rowH; else if (k === 'ArrowDown') scroll.scrollTop += rowH;
      else if (k === '+' || k === '=') zoomBy(1.5); else if (k === '-' || k === '_') zoomBy(1 / 1.5);
      else if (k === '0') setDomain(DEFAULT, true); else if (k === 'f' || k === 'F') fit(); else if (k === 'n' || k === 'N') panTo(NOW_F, true);
      else if (k === 'Home') setDomain([FULL[0], FULL[0] + 10], true); else if (k === 'End') setDomain([FULL[1] - 10, FULL[1]], true);
      else if (k === 'Enter') { var first = null; for (var r = 0; r < rowAll.length && !first; r++) first = rowAll[r].filter(function (it) { return !it.off; })[0]; if (first) focusItem(first); }
      else if (k === 'Escape') { if (state.i !== null) { state.i = null; update(); } hideTip(); svgNode.blur(); }
      else return;
      ev.preventDefault();
    });
    function markKeys(ev, m) {
      var it = itemByKey[m.getAttribute('data-key')]; if (!it) return;
      var list = rowAll[it.row], idx = list.indexOf(it), k = ev.key;
      if (k === 'ArrowRight') focusItem(list[idx + 1]);
      else if (k === 'ArrowLeft') { if (idx > 0) focusItem(list[idx - 1]); else { var lb = labelAt(it.row); if (lb) lb.focus(); } }
      else if (k === 'ArrowDown') focusItem(nearestOnRow(it.row + 1, it.cx)); else if (k === 'ArrowUp') focusItem(nearestOnRow(it.row - 1, it.cx));
      else if (k === 'Home') focusItem(list[0]); else if (k === 'End') focusItem(list[list.length - 1]);
      else if (k === 'Enter' || k === ' ') { if (ev.shiftKey && it.single) { showCard(it.d.i); m.focus({ preventScroll: true }); } else activate(it, m); }
      else if (k === 'Escape') { hideTip(); svgNode.focus(); }
      else return;
      ev.preventDefault();
    }
    function labelKeys(ev, lbl) {
      var key = lbl.getAttribute('data-key'), r = rows.map(function (x) { return x.key; }).indexOf(key), k = ev.key, lb;
      if (k === 'Enter' || k === ' ') togglePerson(key);
      else if (k === 'ArrowDown' && (lb = labelAt(r + 1))) lb.focus(); else if (k === 'ArrowUp' && (lb = labelAt(r - 1))) lb.focus();
      else if (k === 'ArrowRight') { var first = rowAll[r].filter(function (it) { return !it.off; })[0]; if (first) focusItem(first); }
      else if (k === 'Escape') svgNode.focus();
      else return;
      ev.preventDefault();
    }
    svgNode.addEventListener('focus', function () { armed = true; });
    // wheel zoom only when armed (a click, a drag or keyboard focus inside the box), so plain scrolling never traps
    box.addEventListener('pointerdown', function () { armed = true; clearTimeout(armTimer); });
    box.addEventListener('pointerleave', function () { clearTimeout(armTimer); armTimer = setTimeout(function () { if (!box.contains(doc.activeElement)) armed = false; }, 1500); });
    box.addEventListener('pointerenter', function () { clearTimeout(armTimer); });
    box.addEventListener('focusout', function (e) { if (!box.contains(e.relatedTarget)) { clearTimeout(armTimer); armTimer = setTimeout(function () { if (!box.matches(':hover')) armed = false; }, 1500); } });
    $$('.edge', box).forEach(function (b) {
      b.addEventListener('click', function () {
        var dom = domain(), w = dom[1] - dom[0], leftSide = b.classList.contains('edge-left'), target = null;
        allItems.forEach(function (it) { if (!it.off) return; if (leftSide ? it.cx < L : it.cx > L + plotW) { if (target === null || (leftSide ? it.year > target : it.year < target)) target = it.year; } });
        if (target === null) return;
        setDomain(leftSide ? [target - w * .1, target + w * .9] : [target - w * .9, target + w * .1], true);
      });
    });
    function announce() {
      clearTimeout(statusTimer);
      statusTimer = setTimeout(function () {
        var dom = domain(), n = 0; M.forEach(function (d) { if (d.start <= dom[1] && d.end >= dom[0]) n++; });
        status.textContent = 'window ' + fmtY(dom[0]) + ' to ' + fmtY(dom[1]) + '; ' + n + ' of ' + DATA.length + ' statements in view; ' + visItems.filter(function (it) { return it.stack; }).length + ' collapsed stacks';
      }, 500);
    }
    function locateMark(i) {
      var d = DATA[i], dom = domain(), pad = (dom[1] - dom[0]) * .08;
      function after() {
        renderNow();
        var key = stackOf[i];
        if (key) { var it = itemByKey[key]; if (!it.dense) { setDomain([it.bin - 1, it.bin + B + 1], false); renderNow(); } }
        key = stackOf[i] || ('i' + i);
        if (focusMark(key)) { var n = $('.mark[data-key="' + key + '"]', svgNode); showTip(itemByKey[key], n); tipPinned = key; }
      }
      if (d.start < dom[0] + pad || d.start > dom[1] - pad) { panTo(d.start, true); setTimeout(after, DUR + 30); } else after();
    }
    var resizeTimer = null;
    if (window.ResizeObserver) new ResizeObserver(function () { clearTimeout(resizeTimer); resizeTimer = setTimeout(function () { if (Math.abs(scroll.clientWidth - W) > 2) { layout(); renderNow(); } }, 150); }).observe(scroll);
    else window.addEventListener('resize', function () { clearTimeout(resizeTimer); resizeTimer = setTimeout(function () { layout(); renderNow(); }, 150); });
    return { render: schedule, renderNow: renderNow, setDomain: setDomain, panTo: panTo, zoomBy: zoomBy, fit: fit, hot: chartHot, unhot: chartUnhot, pin: pin,
      locate: locateMark, unpinTip: function () { if (tipPinned) hideTip(); }, layout: layout, drawMini: drawMini, domain: domain };
  }

  // ---- wiring the chart head
  chart = initChart();
  if (!chart) {
    root.classList.add('no-d3'); $('#no-d3').hidden = false;
    var cr = $('input[name=view][value=chart]', form); cr.disabled = true; cr.setAttribute('aria-disabled', 'true'); cr.parentNode.title = 'the chart library did not load';
  }
  $('#zoom-in').addEventListener('click', function () { if (chart) chart.zoomBy(1.5); });
  $('#zoom-out').addEventListener('click', function () { if (chart) chart.zoomBy(1 / 1.5); });
  $('#zoom-fit').addEventListener('click', function () { if (chart) chart.fit(); });
  $('#zoom-now').addEventListener('click', function () { if (chart) chart.panTo(NOW_F, true); });
  $('#zoom-reset').addEventListener('click', function () { setWindow(DEFAULT, true); });
  $$('.wpreset').forEach(function (b) { b.addEventListener('click', function () { state.w = b.dataset.x !== 'all'; setWindow(PRESETS[b.dataset.x](), true); }); });
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && chart) chart.unpinTip(); });

  // ---- boot: the hash is the view
  state = parseHash(location.hash, META);
  if (!chart) state.v = 'table';
  recompute();
  if (chart) { chart.layout(); chart.renderNow(); chart.setDomain(state.x, false); }
  booting = false;
  writeForm(); update();
  if (chart) { chart.renderNow(); chart.drawMini(); }
  if (state.i !== null) showPinned(true);
  if (!wide()) $('#years').open = false;
})();
"""

LEGEND_HTML = """
<ul id="legend" class="legend" aria-label="legend">
 <li><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="4" class="m-source"/></svg> filled circle: source text</li>
 <li><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3l5 5-5 5-5-5z" class="m-made"/></svg> filled diamond: speech-to-text made here</li>
 <li><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="4" class="m-source hollow"/></svg> hollow mark: hedged or conditional</li>
 <li><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="4" class="m-source"/><circle cx="8" cy="8" r="7" class="ring"/></svg> thin ring: strong wording</li>
 <li><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="0" y="6.5" width="16" height="3" rx="1.5" class="bar-source"/><circle cx="2" cy="8" r="3" class="m-source"/></svg> bar: target span</li>
 <li><svg viewBox="0 0 16 16" aria-hidden="true"><line x1="0" x2="7" y1="8" y2="8" class="leader"/><path d="M15 3L7 8l8 5z" class="m-source"/></svg> triangle with a dotted leader: upper bound only (“by …”)</li>
 <li><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="0" y="3" width="16" height="10" rx="5" class="pill"/></svg> rounded pill with a number: several statements in one bin, zoom in or press Enter</li>
 <li><svg viewBox="0 0 16 16" aria-hidden="true"><rect x="0" y="0" width="7" height="16" class="past"/><line x1="7" x2="7" y1="0" y2="16" class="now"/><line x1="9" x2="16" y1="8" y2="8" class="lead"/></svg> dashed line: now (build date); shaded: the past; dotted lead on hover from the year said to the target</li>
</ul>"""


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
    js = (JS.replace("__AXIS_END__", str(AXIS_END)).replace("__BUILD_YEAR__", str(BUILD_YEAR))
          .replace("__CARDS_SHOWN__", str(CARDS_SHOWN)).replace("__NOW__", now_fraction(built))
          .replace("__PUBLIC_KEYS__", json.dumps(PUBLIC_KEYS)))
    body = f"""<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prediction timelines</title>
<meta name="description" content="Candidate statements about the future found by rules in the texts of ET channelers, laid out by target year, with the date said and a short quote linking to the public copy.">
<meta name="color-scheme" content="light dark">
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#timeline-section">Skip to the timeline</a>
<header class="wrap">
<p class="eyebrow">ET channelers · candidate statements about the future</p>
<h1>Prediction timelines</h1>
<p class="lead">{len(records)} statements that name a target year or span, from {len(people)} people and {len(items)} recordings or pages, found by rules in source texts and in speech-to-text made here.</p>
<p id="facts" class="facts">Generated {esc(built)} from {len(items)} items. {counts_text}</p>
<section id="caveat" class="caveat" role="note" aria-labelledby="caveat-h">
<h2 id="caveat-h">These are labelled candidates, not confirmed predictions.</h2>
<p class="caveat-p">Rules flagged them; a third blinded sample put real predictions at about 56% of windowed candidates (95% interval about 47% to 65%), from about a fifth to nine in ten by person. Every figure on this page is a count or a date. Quotes are at most 30 words and link to the public copy; no hit, miss or accuracy is judged here.</p>
<div class="caveat-figs">
 <div class="fig"><b>about 56%</b><span>of windowed candidates are real predictions</span></div>
 <div class="fig"><b>47% to 65%</b><span>95% interval of that share</span></div>
 <div class="fig"><b>a fifth to nine in ten</b><span>the range by person</span></div>
</div>
<p class="caveat-p">Date basis: for {undated} statements no date said is known; for {from_address} the date comes from the address of the page and for {from_title} from its title, both exact only to the day they carry. {len(predate)} windows (earliest {earliest}) begin before the statement's own date, or before 1950 where that date is unknown; a single year there is probably a quoted historical year misread as a target, a span may simply start in the past. They are left in and marked rather than removed. {withheld} statements show their time expression instead of a quote because the item's share or a turn prefix left no room for one.</p>
</section>
</header>
<main class="wrap">
{filters_html(records)}
<section id="timeline-section" aria-labelledby="timeline">
<header class="card-head"><h2 id="timeline">Timeline</h2>
<div class="chart-head needs-js">
 <label class="sel">Rows and groups <select id="group" name="g">
  <option value="person">by person</option><option value="kind">by kind of text</option><option value="said">by decade said</option>
  <option value="cert">by certainty</option><option value="target">cards by target decade</option></select></label>
 <div class="zoomctl needs-d3" role="group" aria-label="zoom">
  <button type="button" id="zoom-out" aria-label="zoom out" title="zoom out">−</button>
  <button type="button" id="zoom-in" aria-label="zoom in" title="zoom in">+</button>
  <button type="button" id="zoom-fit" title="fit the window to the statements shown">fit</button>
  <button type="button" id="zoom-now" title="centre the window on now">now</button>
  <button type="button" id="zoom-reset" title="reset the view">reset view</button>
 </div>
 <div class="wpresets" role="group" aria-label="window presets">
  <button type="button" class="wpreset" data-x="all" aria-pressed="false" title="the whole axis; the list shows every match">all years</button>
  <button type="button" class="wpreset" data-x="past" aria-pressed="false" title="the list follows this window">before now</button>
  <button type="button" class="wpreset" data-x="next5" aria-pressed="false" title="the list follows this window">next five years ({BUILD_YEAR} to {BUILD_YEAR + 4})</button>
  <button type="button" class="wpreset" data-x="decade" aria-pressed="false" title="the list follows this window">this decade</button>
  <button type="button" class="wpreset" data-x="2030s" aria-pressed="false" title="the list follows this window">2030s</button>
  <button type="button" class="wpreset" data-x="later" aria-pressed="false" title="the list follows this window">2040 and later</button>
 </div>
 <label class="check"><input type="checkbox" id="follow" name="w" value="1"> list and table follow the window</label>
</div></header>
{LEGEND_HTML}
<div id="chartbox" class="chartwrap needs-d3">
 <div id="chart-axis-wrap"><svg id="chart-axis" viewBox="0 0 800 30" height="30" aria-hidden="true"></svg></div>
 <div id="chart-scroll"><svg id="chart-svg" viewBox="0 0 800 42" tabindex="0" role="group" aria-roledescription="zoomable timeline" aria-labelledby="timeline" aria-describedby="chart-help chart-status"></svg></div>
 <button type="button" class="edge edge-left" hidden aria-label="statements beyond the left edge; show them"></button>
 <button type="button" class="edge edge-right" hidden aria-label="statements beyond the right edge; show them"></button>
 <figure class="minifig"><figcaption class="sr-only">Mini-map of the whole axis; the zoom buttons, the presets and the arrow keys move the window</figcaption><svg id="minimap" viewBox="0 0 800 44" height="44" aria-hidden="true"></svg></figure>
 <div id="tip" class="tip" role="tooltip" hidden></div>
</div>
<p id="chart-help" class="muted needs-d3">Drag to pan. Ctrl + scroll, pinch or the + and − buttons zoom. In the chart: arrow keys move between statements, Shift+arrows pan, + and − zoom, 0 resets, Enter opens the card, Escape leaves.</p>
<p id="chart-status" class="sr-only" aria-live="polite"></p>
<p id="no-d3" class="muted" hidden>The chart library did not load; the table and the lists below are complete.</p>
<noscript><p class="muted">The chart and the filters need JavaScript. The lists below are complete without it.</p></noscript>
<p id="chart-caption" class="muted">Rows are ordered by statements found, which reflects how much text each person published and how well the rules fit their style, not how often they predict.</p>
<div id="tablewrap" class="tablewrap needs-js" hidden><table id="table"><caption class="sr-only">Statements matching the filters</caption><thead></thead><tbody></tbody><tfoot></tfoot></table></div>
<div id="empty" class="empty needs-js" hidden>
 <p class="empty-h">No statements match.</p>
 <p id="empty-why"></p>
 <div class="ebtns"><button type="button" id="empty-clear">Clear all filters</button><button type="button" id="empty-q" hidden>Clear the search</button><button type="button" id="empty-zoom" hidden>Show all years</button></div>
</div>
</section>
<section aria-labelledby="statements">
<h2 id="statements">Statements</h2>
<div id="results-tools" class="needs-js">
 <button type="button" id="expand-all">Expand all</button>
 <button type="button" id="collapse-all">Collapse all</button>
 <label class="sel"><span class="sr-only">Jump to group</span><select id="group-nav" aria-label="jump to group"></select></label>
 <button type="button" id="download" title="the rows shown, public fields only">Download CSV</button>
</div>
<div id="groups" data-group="person">
{person_sections(records)}
</div>
</section>
<details id="years" open>
<summary><h2 id="years-h">Index by target year</h2></summary>
<nav aria-labelledby="years-h"><ul id="yearlist">
{year_index_html(records)}
</ul></nav>
</details>
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
<dt>Reading the timeline</dt>
<dd>One row per group, one mark per statement at the first year of its target window, a bar to the last year. Marks that would overlap are stacked into a pill with a count; zooming in spreads them. The shaded area is the past and the dashed line is the build date. Hovering or focusing a mark draws a dotted lead from the year the statement was said to its target. The mini-map below the chart shows the density of all target years and the window in view. Every value in the chart is also in the table view.</dd>
<dt>Sharing a view</dt>
<dd>The view lives in the address after the hash sign: the filters (p, k, f, s, d, e, b, q), the window (x) and whether the list follows it (w), the grouping (g), the view (v), the sort (o) and a pinned statement (i). A link's pinned statement refers to this build's numbering.</dd>
<dt>What is withheld and why</dt>
<dd>No transcript and no audio: a quote of at most 30 words per statement (words are whitespace tokens with a letter or digit in them; the closing ellipsis is not a word), at most 5% of an item's words across the page (for speech-to-text, 5% of the transcript's words) and at most {QUOTE_CAP_PER_PERSON:,} quoted words per person; where the share leaves no room, the time expression stands in. No questioner is named: a sentence that opens as someone else's turn, a bare "Questioner" opener included, or that names a person on a private list kept by the owner, shows no quote. No private location: items are named by id and linked to their public page where one is known; a podcast episode known only by its audio file has no link.</dd>
<dt>The guard</dt>
<dd>Before the page is written, a guard recomputes the quote lengths and shares, checks every link, looks for speaker prefixes, addresses and private locations, and compares the whole page against the private texts for any run of more than thirty words anywhere and any five-word run outside the quotes. If any check fails, nothing is written.</dd>
<dt>Build</dt>
<dd>Built {esc(built)} by <code>pipeline/prediction_page.py</code> from the output of <code>pipeline/prediction_timeline.py</code> in the public repository, with the private texts as input. Counts per person are in <code>plan/prediction_timeline_counts</code> (a CSV table).</dd>
</dl>
</main>
<footer id="foot" class="wrap">
<p><a href="index.html">Dashboard index</a> · <a href="https://github.com/occult-kranti/bashar-index/blob/main/et-channelers/ANALYSIS_PLAN.md#129-private-and-public">ANALYSIS_PLAN section 12.9</a></p>
<p>Built {esc(built)}. Only external request: d3 7.9.0 from cdnjs.cloudflare.com. No cookies, no local storage, no analytics; the view is in the address after #, so a link reproduces it.</p>
<p>Links are to the publishers' own pages as known on the build date; they are not checked for liveness.</p>
</footer>
<script type="application/json" id="data">{data}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js" crossorigin="anonymous" referrerpolicy="no-referrer" onerror="document.documentElement.classList.add('no-d3')"></script>
<script>{js}</script>
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
