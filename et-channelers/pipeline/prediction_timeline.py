#!/usr/bin/env python3
"""Find the statements about the future in each channel's texts and lay them out as a timeline.

This is the rules pass of ANALYSIS_PLAN 12.4 (the first of its steps): rules flag sentences that speak of
the future and carry a time expression, a prediction word or a prophecy theme, and code turns each time
expression into a target window counted from the date the text was said (TimeML-style: "in two years" from
a 2021 recording is 2023; "by 2030" keeps one bound; "soon" gets no invented bounds). A later model pass
checks each candidate (is it the entity's claim, is it a prediction or future-tense teaching); until then
every row is a candidate, not a finding. Filters measured on the labelled samples leave out what passes the
gates without being the entity's dated claim: promotion, page furniture, editors' notes, questions, reports,
lists of any-time spans, and a time expression that is a date header or a past date. Their counts on those
samples are in-sample (the rules were written on them); only a fresh sample measures them.

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
    <root>/analysis/predictions/counts.csv          counts per person and kind (no text); near-copies are
                                                    collapsed by shared five-word runs (12.4) and counted apart
--publish-counts also copies counts.csv to plan/prediction_counts.csv (counts only, never text).
"""
from __future__ import annotations

import argparse
import collections
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
COPY_RESEMBLANCE = 0.5    # Broder 1997: near-copies share at least half their five-word runs
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

# Filters on what passed the gates (design set of 2026-11-15: 275 candidates of three samples, each labelled by two
# coders). Each filter below dropped at least 3 of the 112 that neither coder took for a prediction, in at least two
# of the three samples, and none of the 156 that both did. Those counts are in-sample: the rules were written on
# these rows. A phrase that matched one labelled sentence and no other candidate is left out as tailored to it, and
# on the windowed candidates never sampled every filter but FURNITURE fires well below its design rate.
_Y = r"(?:19|20)\d\d"
_MON = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|"
        r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?")
_DAY = r"\d{1,2}(?:st|nd|rd|th)?"
# a calendar date: "4 June 2019", "June 4 2019", "June 4, 2019", "4th of June 2019", "2019 June", "2019-06-04"
_DATE = (rf"(?i:\b(?:{_DAY}\s+(?:of\s+)?)?{_MON},?\s+(?:{_DAY},?\s+)?(?:of\s+)?{_Y}|\b{_Y}\s+{_MON}(?:\s+{_DAY})?|"
         rf"\b{_Y}-\d\d-\d\d)")
# a date, a year or a decade as the object of "since", "back in", "from ... until now"
_DATEISH = (rf"(?:(?:the\s+)?(?:year\s+(?:of\s+)?)?(?:(?:{_DAY}\s+(?:of\s+)?)?{_MON},?\s+(?:{_DAY},?\s+)?(?:of\s+)?)?{_Y}|"
            rf"(?:the\s+)?(?:19|20)\d0['’]?s)")
# page furniture: translation listings (translator, date, links to read or download), "Related Posts"
# blocks, a post's title and byline ("<title> ∞<council> <title> ∞<council>, Channeled by <name>"), shop sidebars,
# " | " lists of video titles. Other pages' titles, not the entity's speech (design: 8; of the 37 windowed drops in
# the full set none is a claim, about 4 are post titles worded as headlines, and those posts are read on their own).
# "channeled by" and "translated by" count only in their page forms: a byline after ∞ or after a title (capitalised,
# with a capitalised name: "... Will Be Gentle Channeled by Jo Doe"), or a listing line ("by <name> · 2024-03-02");
# in a body sentence ("the message channelled by the council says ...") they are the source's own words
_BY = r"(?:channel+ed|translated) by"
FURNITURE = re.compile(r"\bread translation\b|\bdownload (?:the )?pdf\b|\brelated posts\b|"
                       r"\bbuy it here\b|∞[^∞]*∞| \| |"
                       rf"∞[^∞]*?\b{_BY}\b|(?-i:\b(?:Channel+ed|CHANNEL+ED|Translated|TRANSLATED) (?:by|By|BY) [A-Z])|"
                       rf"\b{_BY}\s+[^·]{{1,60}}?\s·\s+{_Y}-\d\d-\d\d\b", re.I)
# an editor's note, not the source: transcript footnotes (L/L Research ends each with ↩: past sessions, editions,
# events) and citations of print ("reprinted from", "the June/July 2012 issue") (design: 6)
EDITORIAL = re.compile(rf"↩|\b(?:adapted|reprinted|excerpted) from\b|\b{_MON}/{_MON}\s+{_Y}\b|\b{_Y} issue\b", re.I)
# the speaker's own events and products, which BOILERPLATE misses: workshops, fund raisers, services streamed,
# editions of a book or calendar (design: 8). Left out as they also serve predictions: "will be held" (trials),
# bare "launch", "available until", clock times and prices, "the 2012 Mayan calendar"
PROMOTION = re.compile(r"\b(?:workshops?|seminars?|master ?class(?:es)?|intensives|fund ?rais\w*|live[- ]?stream\w*|"
                       r"streamed live)\b|"
                       r"\b(?:print(?:ed)?|digital|paperback|hardcover|kindle|e-?book|audio ?book|downloadable) "
                       r"(?:version|edition|copy|copies|format)s?\b|"
                       r"\b(?:version|edition|translation)s? of (?:the|my|our|this|his|her) (?:new )?"
                       r"(?:book|calendar|album|course|deck|cards)\b|"
                       rf"\b(?:the|our|my|this|a|new) {_Y} (?!maya)(?:\S+ ){{0,2}}(?:calendars?|editions?|planners?|"
                       r"almanacs?)\b", re.I)
# three or more spans of time in a list ("today, next month or next year", "in a month, or two, or three"): any time
# at all, not the date of a coming event; kept when a prophecy theme or a prediction word is named (design: 6; a
# strong marker is no exception: "rain falls today, next month or next year, and surely" is no forecast). Every
# item needs a number or next/this, so years and bare "days, weeks and months" are not lists here
_NUMW = (r"(?:\d{1,3}|a|an|one|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|twenty|thirty|fifty|"
         r"a hundred|a thousand|a million|hundred|thousand|million|a few|few|several)")
_UNITW = r"(?:moments?|minutes?|hours?|days?|weeks?|months?|years?|decades?|lifetimes?|life|lives|centur(?:y|ies)|millenni(?:um|a))"
_PREP = r"(?:(?:in|within|over|for|until|after) )?(?:(?:your|the|this|a) )?"
_SPAN = rf"(?:tomorrow|today|tonight|{_PREP}(?:next |coming )?{_NUMW} {_UNITW}|{_PREP}(?:next|this) {_UNITW})"
_LIST_SEP = r"(?:,\s*(?:or\s+)?(?:even\s+)?|\s+or\s+(?:even\s+)?)"
TIME_LIST = re.compile(rf"\b{_SPAN}{_LIST_SEP}(?:{_SPAN}|{_NUMW}){_LIST_SEP}(?:{_SPAN}|{_NUMW})\b", re.I)

# The filters below look at the time expression itself (the first match of RULES) and drop the sentence only when
# it is that expression which is a date header or a past date, so a sentence dated by another expression is kept.
# None of them drops a sentence whose year said is known and earlier than every year in that expression: a date
# ahead of the speaker is not a past reference or the date of the session (see future_dated).
YEAR_IN = re.compile(r"(?<!\d)(?:19|20)\d\d(?!\d)")
# a transcript's date header or speaker line ("4 June 2019 Lumi (2):", "---------- LATER - JUNE 9 2019", a heading
# "AUGUST 2019 Our circle ..."): the date of the session, not a target (design: 12)
DATED_HEADER = re.compile(rf"{_DATE}\s*[-–—:]?\s*[A-Z][\w’'.-]*(?:\s+[A-Z0-9][\w’'.-]*){{0,2}}\s*(?:\([^()]{{1,25}}\))?:"
                          rf"(?=\s|$)|^\W*(?:{_DAY}\s+)?(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|"
                          rf"OCTOBER|NOVEMBER|DECEMBER)\s+(?:{_DAY},?\s+)?{_Y}\b|-{{3,}}\s*(?:[A-Za-z ]{{1,30}}?\s[-–]\s*)?"
                          rf"{_DATE}")
# a date anchored in the past or the present: "since 2001" (not "since 2031 will be", where since means because),
# "back in March 2019", "back to 2015" (time travel), "from June of 2014 until now"; then "<n> years ago" (design: 7)
PAST_ANCHOR = re.compile(rf"\bsince\s+(?:(?:early|late|mid|about|around|at least|roughly)[- ]\s*)?{_DATEISH}\b"
                         r"(?!,?\s+(?:is|was|will|shall|would|has|had|are)\b)|"
                         rf"\bfrom\s+{_DATEISH}\s+(?:until|till|to|up to|through)\s+(?:now|today|the present|this day)\b",
                         re.I)
BACK_ANCHOR = re.compile(rf"\bback\s+(?:in|to)\s+(?:(?:early|late|mid)[- ]\s*)?{_DATEISH}\b", re.I)
# ... but "back in 2027" after a return still to come is a target: "the ships will come back in 2027", "they are
# coming back", "be back", "return", "go back", or a future marker within the three words before "back"
# ("came back in 2019" stays a past date)
RETURNING = re.compile(r"\b(?:come|coming|be|return\w*|go|going|will|won['’]t|shall|gonna|about to)\b|['’]ll\b", re.I)
AGO = re.compile(r"\s+ago\b", re.I)
# a past-tense verb governs the dated clause (design: 15): (a) it comes just before the date ("the bridge they built
# in 2015", "which was on 4 June 2010") with no auxiliary or modal among the three words before it, read back to a
# clause edge, and no "to" right before it ("will soon be completed in 2027" is not past; "this is what happened in
# 2019" and "next to the house built in 2015" are); (b) the date is
# its subject ("2009 was a hard year"); (c) a fronted date ("On June 4, 2019, ...", "At the start of March 2020 ...")
# is followed by a past or present-perfect main verb and by no future marker or modal, neither in the next 20 words
# nor anywhere in the main clause (to MAIN_CLAUSE_END).
# Only for a date, a decade, "this year" and "in two years": "by 2030",
# ranges and "the next two years" reach forward. "left", "set" and "put" are left out: they are also presents
_PAST_VERB = (r"(?:was|were|had|did|began|became|came|went|saw|took|gave|got|made|met|lost|found|felt|heard|told|said|"
              r"wrote|bought|brought|thought|knew|grew|fell|rose|ran|won|sent|spent|built|held|stood|kept|paid|sold|chose|"
              r"broke|drove|flew|meant|struck|taught|threw|understood|woke|wore|entered|started|ended|happened|occurred|"
              r"arrived|landed|appeared|visited|joined|returned|received|learned|learnt|offered|invited|decided|realized|"
              r"realised|noticed|experienced|passed|moved|changed|opened|closed|died|published|released|recorded|reached|"
              r"showed|asked|answered|talked|spoke|stopped|continued|finished|completed|signed|lived|worked|tried|stayed|"
              r"remained|purchased|predicted|foretold|prophesied)")
PAST_BEFORE = re.compile(rf"(?:^|[\w'’]\s+)\b(?P<verb>{_PAST_VERB})(?P<rest>(?:\s+[\w,'’-]+){{0,3}}?)\s*$", re.I)
NON_FINITE = re.compile(r"(?:will|won['’]t|shall|would|could|should|may|might|must|can|to|be|been|being|have|has|having|"
                        r"is|are|am|\w*['’]ll)", re.I)
# where the words before a verb stop being its own: a relative or a conjunction, or the end of a clause
CLAUSE_EDGE = re.compile(r"(?:who|whom|whose|which|that|what|when|where|while|and|but|or|as|because|if|since)", re.I)
FORWARD = re.compile(r"\b(?:will|won['’]t|shall|going to|gonna|about to|would|could|should|can|must|may|might|coming|"
                     r"upcoming|approaching|next|future)\b|['’]ll\b", re.I)
DATE_SUBJECT = re.compile(r",?\s+(?:was|were|had been|had|became|began|ended|saw|brought)\b", re.I)
FRONTED = re.compile(r"\b(?:on|in|at|during|of)\s+(?:the\s+)?(?:[\w,]+\s+){0,3}$", re.I)
PAST_MAIN = re.compile(rf"\b(?:{_PAST_VERB}|(?:has|have)\s+(?:\w+\s+)?\w+(?:ed|en|wn|ght))\b", re.I)
FUTURE_OR_MODAL = re.compile(r"\b(?:will|won['’]t|shall|going to|gonna|about to)\b|['’]ll\b|"
                             r"\b(?:may|might|could|would|can|should)\s+(?!not\b)\w+", re.I)
# the end of the main clause after a fronted date: a future marker beyond its first 20 words still counts up to here
# ("On May 3, 2027, after the long years ... and on the hills, the ships will land"), but not in a clause after
# ", however" ("In this year the valley became a lake, however, ... what you would call ..." is a past account)
MAIN_CLAUSE_END = re.compile(r"[;:]|,\s+(?:however|but|and|yet|so|whereas)\b", re.I)


def number(word):
    word = word.lower()
    return int(word) if word.isdigit() else NUM.get(word)


def span(n, unit):
    unit = unit.lower()
    return n * 10 if unit.startswith("decade") else (n / 12 if unit.startswith("month") else n)


def time_expression(sentence):
    """(label, match) for the first time expression in the sentence, the rules tried most specific first; or None."""
    for label, rx in RULES:
        m = rx.search(sentence)
        if m:
            return label, m
    return None


def time_window(sentence, said_year, found=False):
    """(lo, hi, label, matched text) for the first time expression in the sentence, or None. lo and hi are
    years (hi may equal lo); either may be None when the expression gives no bound or the year said is
    unknown. "soon" gets (None, None). found: time_expression(sentence) when the caller has it already."""
    found = time_expression(sentence) if found is False else found
    if found:
        label, m = found
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


def overlaps(rx, sentence, m):
    """True when a match of rx overlaps the matched time expression m."""
    return any(x.start() < m.end() and m.start() < x.end() for x in rx.finditer(sentence))


def future_dated(m, said_year):
    """True when the year said is known and the smallest year in the time expression m is later than it."""
    years = [int(y) for y in YEAR_IN.findall(m.group(0))]
    return bool(said_year and years and min(years) > said_year)


def auxiliary_before(text, n=3):
    """True when an auxiliary or a modal is among the last n words of text, read back to a clause edge, or "to" is
    the last word ("next to the house built in 1990" is a preposition, not "to" + verb)."""
    for i, word in enumerate(reversed(text.split()[-n:])):
        w = word.strip("\"“”‘’'()[]").rstrip(",")
        if NON_FINITE.fullmatch(w) and (i == 0 or w.lower() != "to"):
            return True
        if CLAUSE_EDGE.fullmatch(w) or w[-1:] in (";", ":", ".", "!", "?") or not re.search(r"\w", w):
            return False
    return False


def back_anchor(sentence, m):
    """True when "back in/to <date>" covers the time expression m and no return to come precedes "back"."""
    return any(x.start() < m.end() and m.start() < x.end() and not RETURNING.search(" ".join(sentence[:x.start()].split()[-3:]))
               for x in BACK_ANCHOR.finditer(sentence))


def past_verb_governs(sentence, label, m):
    """True when a past-tense verb governs the time expression m (see PAST_BEFORE, DATE_SUBJECT, FRONTED)."""
    if not (label in ("year", "decade", "this_unit") or (label == "in_n" and not FORWARD.search(m.group(0)))):
        return False
    before, after = sentence[:m.start()], sentence[m.end():]
    v = PAST_BEFORE.search(before)
    if v and not auxiliary_before(before[:v.start("verb")]) and not FORWARD.search(v.group("rest")):
        return True
    if DATE_SUBJECT.match(after):
        return True
    if len(before.split()) <= 8 and (re.match(r"(?:in|during|around|on|at)\b", m.group(0), re.I) or FRONTED.search(before)):
        main = " ".join(after.split()[:20])
        clause = MAIN_CLAUSE_END.split(after, 1)[0]
        return bool(PAST_MAIN.search(main)) and not (FUTURE_OR_MODAL.search(main) or FUTURE_OR_MODAL.search(clause))
    return False


def screened_out(sentence, found, theme, said_year, undated_floor=UNDATED_FLOOR):
    """The name of the first filter above (FURNITURE to PAST_VERB) that takes a sentence past the gates for
    something other than the entity's dated claim, or "" when none does. found is time_expression(sentence)."""
    m = FURNITURE.search(sentence)
    if m:
        # the splitter does not cut after .” so a post's last line can be glued to the links that follow it: kept
        # when the text before the closing quote ahead of the links is a candidate by itself
        head = sentence[:m.start()]
        q = max(head.rfind("”"), head.rfind('"'))
        if not (q > 0 and candidate(head[:q].strip(), said_year, undated_floor)):
            return "furniture"
    if EDITORIAL.search(sentence):
        return "editorial"
    if PROMOTION.search(sentence):
        return "promotion"
    if not (theme or PREDICT.search(sentence)) and TIME_LIST.search(sentence):
        return "time list"
    if not found:
        return ""
    label, m = found
    if future_dated(m, said_year):
        return ""
    if overlaps(DATED_HEADER, sentence, m):
        return "dated header"
    if overlaps(PAST_ANCHOR, sentence, m) or back_anchor(sentence, m) or AGO.match(sentence, m.end()):
        return "past anchor"
    if past_verb_governs(sentence, label, m):
        return "past verb"
    return ""


def candidate(sentence, said_year, undated_floor=UNDATED_FLOOR):
    """A dict for a sentence that speaks of the future with a time, a prediction word or a prophecy theme;
    None otherwise. A window that ends before the year said is a past reference, future marker or not ("he
    will assume it is still 1945"): not kept. With no year said, a window that ends before undated_floor
    is taken as a past reference too."""
    # cheapest tests first: most sentences have no future, prediction or hedging word and stop here
    future, predict, hedge = FUTURE.search(sentence), PREDICT.search(sentence), HEDGE.search(sentence)
    if not (future or predict or hedge):
        return None
    found = time_expression(sentence)
    window = time_window(sentence, said_year, found)
    # "may come by 2030" is a hedged statement about the future: a hedging modal with a time counts too
    if not (future or predict or (hedge and window)):
        return None
    theme = THEMES.search(sentence)
    if not (window or predict or theme):
        return None
    if (BOILERPLATE.search(sentence) or QUESTION.search(sentence) or PAST_REPORT.search(sentence)
            or POST_HEADER.search(sentence) or screened_out(sentence, found, theme, said_year, undated_floor)):
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


# a blog's reader comments follow the post ("4 comments:", then "ReplyDelete" under each); they are readers'
# words, not the source's (validation of 2026-11-15: 11 of 16 sampled Suzanne Lie candidates were comments)
COMMENTS = re.compile(r"\n\s*\d+ comments?:\s*\n|ReplyDelete")
# a post's date header ("Saturday, May 30, 2015 Title ..."): the year is the date of the post, not a target
POST_HEADER = re.compile(r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday),? [a-z]+\.? \d{1,2},? "
                         r"(19|20)\d\d\b", re.I)


def without_comments(text):
    m = COMMENTS.search(text)
    return text[:m.start()] if m else text


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
        out.append(("source", sentences_of_text(without_comments((root / src).read_text(encoding="utf-8",
                                                                                         errors="replace")))))
    return out


def shingles(sentence, n=5):
    w = re.sub(r"[^a-z0-9 ]", "", sentence.lower()).split()
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}


def copy_groups(rows, threshold=COPY_RESEMBLANCE):
    """Collapse near-copies (12.4: copies first, by shared five-word runs; Broder 1997). In the order said, a row
    whose set of five-word runs resembles (Jaccard) an earlier group's first row by at least threshold joins that
    group: it gets the group's number in copy_group and copy True; any other row starts a group. Families of one
    event in different words are the model pass's work, not this."""
    order = sorted(range(len(rows)), key=lambda i: (rows[i].get("date_said") or "9999", rows[i]["item_id"],
                                                     rows[i].get("offset_s") or 0))
    heads, index = [], collections.defaultdict(set)
    for i in order:
        s = shingles(rows[i]["sentence"])
        best, group = 0.0, None
        for h in set().union(*(index[x] for x in s)):
            r = len(s & heads[h]) / len(s | heads[h])
            if r > best:
                best, group = r, h
        if group is not None and best >= threshold:
            rows[i]["copy_group"], rows[i]["copy"] = group, True
        else:
            heads.append(s)
            rows[i]["copy_group"], rows[i]["copy"] = len(heads) - 1, False
            for x in s:
                index[x].add(len(heads) - 1)
    return rows


def timeline_md(person, rows, items_read):
    times = collections.Counter(r["copy_group"] for r in rows)
    all_rows, rows = rows, [r for r in rows if not r.get("copy")]
    dated = sorted((r for r in rows if r["window_lo"] is not None or r["window_hi"] is not None),
                   key=lambda r: ((r["window_lo"] if r["window_lo"] is not None else r["window_hi"]),
                                  r["window_hi"] or 0, r["date_said"] or "", r["item_id"]))
    undated = [r for r in rows if r["window_lo"] is None and r["window_hi"] is None]
    lines = [f"# Statements about the future: {person}", "",
             f"Rules pass of ANALYSIS_PLAN 12.4, made {utc_now()}. {items_read} items read; {len(all_rows)} candidates, "
             f"{len(rows)} once near-copies are collapsed (each shown once, with how often it was said), {len(dated)} "
             "of these with a target window. These are candidates, not findings: a model pass is still to check "
             "each one. Private: the quotes are from the texts (at most 30 words).", "",
             "| Target | Said | Kind | Item | Times | Time | Cues | Quote |", "|---|---|---|---|---|---|---|---|"]
    for r in dated:
        lo, hi = r["window_lo"], r["window_hi"]
        target = f"{lo}" if lo == hi else f"{lo if lo is not None else '…'}–{hi if hi is not None else '…'}"
        cues = ", ".join(c for c, on in (("if", r["conditional"]), ("hedged", r["hedged"]), ("strong", r["strong"])) if on)
        when = f" @{int(r['offset_s'] // 60)}:{int(r['offset_s'] % 60):02d}" if r["offset_s"] is not None else ""
        lines.append(f"| {target} | {r['date_said'] or '?'} | {r['kind']} | {r['item_id']}{when} | "
                     f"{times[r['copy_group']]} | {r['time_expr']} | "
                     f"{cues} | {quote(r['sentence']).replace('|', '/')} |")
    lines += ["", f"## Without a target window ({len(undated)})", "",
              "\"Soon\" and statements with a prediction word or theme but no time; and relative times in items "
              "whose date is unknown.", ""]
    for r in sorted(undated, key=lambda r: (r["date_said"] or "", r["item_id"])):
        more = f" (said {times[r['copy_group']]} times)" if times[r["copy_group"]] > 1 else ""
        lines.append(f"- {r['date_said'] or '?'} · {r['kind']} · {r['item_id']}{more}: {quote(r['sentence'])}")
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
        rows = copy_groups(by_person.get(person, []))
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
                           "candidates": len(mine), "distinct": sum(not r["copy"] for r in mine),
                           "with_window": len(dated), "distinct_with_window": sum(not r["copy"] for r in dated),
                           "without_window": len(mine) - len(dated),
                           "conditional": sum(r["conditional"] for r in mine), "hedged": sum(r["hedged"] for r in mine),
                           "earliest_target": years[0] if years else "", "latest_target": years[-1] if years else ""})
    fields = ["person_id", "kind", "items_read", "candidates", "distinct", "with_window", "distinct_with_window",
              "without_window", "conditional",
              "hedged", "earliest_target", "latest_target"]
    write_csv(out / "counts.csv", counts, fields)
    if args.publish_counts:
        shutil.copyfile(out / "counts.csv", ET_ROOT / "plan" / "prediction_counts.csv")
    total = sum(c["candidates"] for c in counts)
    print(f"{len(catalogue)} items with text for {len(people)} people; {total} candidates, "
          f"{sum(c['distinct'] for c in counts)} distinct "
          f"({sum(c['with_window'] for c in counts)} with a target window) -> {out}")


if __name__ == "__main__":
    main()
