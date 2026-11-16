#!/usr/bin/env python3
"""Keywords of each channel's newest videos: what is distinctive now, what is new against the channel's own past,
what many channels share now, and how often the newest titles and texts name blackouts.

ANALYSIS_PLAN 5.11 (TF-IDF and keyness) and 12.4.1 (blackouts of the grid and the internet), for a tier of the
newest videos (jobs/queue_newest10.csv, 20, 50) against each channel's other listed videos (the history:
jobs/queue_youtube_all.csv minus the tier). The history takes only the listing tabs that the tier has (videos for
the newest tiers; --history-tabs all adds shorts and streams, whose newest rows are as recent as the tier). Four
kinds of text stay apart in every table: titles (public YouTube metadata), texts from the source, speech-to-text
made here and YouTube captions. Texts reach a tier through the catalogue: a queued video's own row and the podcast
episodes and pages whose twin_of is the video; of several texts of one kind for one recording the longest is
kept. A text kind is compared with the channel's other texts of the same kind. A text's sentences that the
prediction timeline's filters call page furniture, cross-links, promotion or editors' notes are left out and
counted, and a blog post's date header is cut (--keep-furniture keeps them all): on a web page they carry the
site's book and event notices and other posts' titles.

Per channel and kind:
1. Distinctive now: TF-IDF of the channel's tier document, the IDF over all channels' tier documents of the kind
   (smoothed, idf = ln((1 + N) / (1 + df)) + 1; tf = 1 + ln(count); each document L2-normalised, as
   scikit-learn's TfidfVectorizer(sublinear_tf=True)). It describes; it is not a test.
2. New against its own history: the log-odds ratio with an informative Dirichlet prior (Monroe, Colaresi and
   Quinn 2008, "Fightin' Words"), tier against history, unigrams and bigrams as separate vocabularies:
       delta = ln((y_t + a) / (n_t + a0 - y_t - a)) - ln((y_h + a) / (n_h + a0 - y_h - a)),
       var ~= 1 / (y_t + a) + 1 / (y_h + a),  z = delta / sqrt(var),
   with a = a0 * pi, pi the term's share in the channel's own pooled corpus of the kind ((y_t + y_h) / (n_t +
   n_h)), and a0 = --prior-scale, by default the tier's own token count. Both sides are then drawn toward the
   channel's pooled rate, so the sign of delta is always the sign of the tier's rate minus the history's (a prior
   pooled over other channels drew the small tier to the other channels' rate instead, and made a word common in
   the channel "fall" when it rose). A term is significant when z > 1.96 (rising) or z < -1.96 (falling) and it
   occurs at least --min-significant-count times on its side; the count that also survives Benjamini-Hochberg at
   q = .05 (over the same terms) is kept beside it. Dates (years, months, weekdays and pairs of them) are flagged
   and counted apart. A text kind whose tier has fewer than --min-text-tokens tokens is not tested.
3. Across channels: how many channels use a term now and in their history, the mean share of a channel's titles
   (or texts) that use it now and before, how many channels rose or fell, and a stratified test: the
   Mantel-Haenszel z over the channels' 2x2 tables of items (tier or history, using the term or not), each channel
   against its own history, so that large histories do not set it.
4. Blackouts: titles (or texts with a matching sentence) that the lexicon matches, strong and weak groups apart (a
   title with both counts in both), counts and rates per 100, with the tier against the history by Fisher's exact
   test (and a two-proportion z; across channels also the Mantel-Haenszel z). The lexicon is
   pipeline/themes/blackouts.json when it is there (include patterns with a topic, exclude patterns for the false
   senses, scoped to include ids), else a built-in list of literal terms. Solar flares, storms and CMEs are only
   the weak group.

Tokens: NFKC, lower case, Unicode letters, years 1900-2099 kept as tokens, and 3d/5d/5g; URLs, emoji, the "#" of
hashtags, other numbers and single letters dropped; an English stopword list ("may" kept beside a date, "will"
after "free", "U.S." as "usa"); Chinese and Japanese runs cut into character pairs. Each channel's own name is
dropped (accents folded): the whole name and its alias as phrases, and a person's name words one by one unless
they are ordinary words of these titles (NAME_WORDS_IN_USE: April, Rose, Gold, Council ...); a name in Chinese or
Japanese letters is cut out of the text. The channel's title furniture is dropped too: a word or pair in more than
half of the channel's titles (--furniture-share; only with at least --furniture-min-titles titles), such as a
channeler's name or a series name in every title. Bigrams do not cross punctuation, "#", "&" or a dropped word.

    python3 -I pipeline/keywords.py --root ~/et-channelers-private --scope newest10 \\
        --queue jobs/queue_newest10.csv --history jobs/queue_youtube_all.csv --publish-counts

Writes, inside the private folder only (it lists terms and titles; quotes are cut to 30 words):
    <root>/analysis/keywords/<scope>/<channel>.md     top terms of 1, 2 and 4, with counts
    <root>/analysis/keywords/<scope>/summary.md       the cross-channel view
    <root>/analysis/keywords/<scope>/keywords.json    everything
    <root>/analysis/keywords/<scope>/counts.csv       counts per channel and kind (no text)
--publish-counts also copies counts.csv to plan/keywords_<scope>.csv: counts only, no terms, titles or ids, until
the owner decides D16. The output is deterministic: no clock, sorted keys, fixed rounding.
"""
from __future__ import annotations

import argparse
import collections
import functools
import json
import math
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, atomic_write_text, ensure_outside_git, read_csv,  # noqa: E402
                    sha256_file, write_csv)
import prediction_timeline  # noqa: E402
from prediction_timeline import (BOILERPLATE, EDITORIAL, FURNITURE, PROMOTION, quote,  # noqa: E402
                                 read_item_texts, sentences_of_text)

# sentences of a text that are not the source's words: page furniture, cross-links, promotion and editors' notes,
# as the prediction timeline leaves them out (on a web page they also glue other posts' titles onto the last line);
# and a blog's notice of its own new video
VIDEO_NOTICE = re.compile(r"\bmy (?:new|latest) video\b|\bnew video (?:is |has been )?(?:out|up|posted)\b", re.I)
NOT_CONTENT = (BOILERPLATE, FURNITURE, PROMOTION, EDITORIAL, VIDEO_NOTICE)
# cut out of a sentence, the rest kept: a blog post's date header ("Saturday, May 30, 2015 ...", the prediction
# timeline's pattern; its "Posted by" line is BOILERPLATE's)
POST_HEADER = getattr(prediction_timeline, "POST_HEADER", None) or re.compile(
    r"^(monday|tuesday|wednesday|thursday|friday|saturday|sunday),? [a-z]+\.? \d{1,2},? (19|20)\d\d\b", re.I)

KINDS = ("titles", "source", "made", "captions")
TEXT_KINDS = KINDS[1:]
KIND_NAMES = {"titles": "titles (public YouTube metadata)", "source": "texts from the source",
              "made": "speech-to-text made here", "captions": "YouTube captions"}
KIND_PATH = {"source": "publisher_text_path", "made": "asr_path", "captions": "captions_path"}
Z = 1.96
LEXICON = ET_ROOT / "pipeline" / "themes" / "blackouts.json"
TARGETS = ET_ROOT / "plan" / "targets.csv"
ORGANISATIONS = {"organisation", "organization", "publisher"}   # their names are phrases, not first and last names

# ---------------------------------------------------------------------------------------------------- tokens
STOPWORDS = frozenset("""
a about above after again against all almost along already also although always am among amongst an and another
any anybody anyone anything anyway anywhere are aren't around as at be became because become becomes been before
below beside besides between both but by can can't cannot could couldn't did didn't do does doesn't doing
don't done during each either else enough etc even ever every everyone everything for from further get gets
getting got had hadn't has hasn't have haven't having he he'd he'll her here hers herself him himself his how
however i i'd i'll i'm i've if in into is isn't it it'll its itself just let ll may me might mightn't mine more
most much must mustn't my myself needn't neither no nor not now of often on once only onto or other others
otherwise ought our ours ourselves out over own per perhaps quite rather re really same shall shan't she she'd
she'll should shouldn't since so some somebody someone something sometimes somewhat still such than that the
their theirs them themselves then there therefore these they they'd they'll they're they've this those though
through thus till to too toward towards under unless until up upon us ve very via vs was wasn't we we'd we'll
we're we've were weren't what whatever when whenever where wherever whether which while who whoever whom whose
why will with within won't would wouldn't y'all yet you you'd you'll you're you've your yours yourself
yourselves ain't amp quot nbsp gt lt
shorts ytshorts youtubeshorts shortsfeed
um uh uhm erm hmm mm mhm yeah yep okay ok oh ah gonna wanna gotta kinda sorta
""".split())
# the last lines: YouTube's "#shorts" tags and the fillers of speech
# kept on purpose: "down" and "off" (grid down, shut down, off grid, cut off), "without" (without power), "being"
# (light being, human being); "may" is kept beside a date ("May 2026", "15 May") and "will" after "free" (free will);
# "us" and "am" stay stopwords: the pronoun and the verb outnumber the US and "I AM" by far in speech and posts

APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "`": "'", "´": "'"})
_TLD = r"\.(?:com|org|net|io|tv|me|co|uk|info|link|ly|gl|be|shop|store|app)\b"
URL = re.compile(rf"(?:https?://|www\.)\S+|[\w.-]+{_TLD}(?:/\S*)?", re.I)
URL_HINT = re.compile(rf"://|www\.|{_TLD}", re.I)      # cheap: most sentences have no address
USA = re.compile(r"(?<![\w.])u\.s\.(?:a\.?)?(?!\w)")     # in lower case; "us" without dots stays the pronoun
# a bigram never crosses these: punctuation, a spaced dash, "#" and "&", symbols and emoji
BREAK = re.compile("[|•·:;!?.,()\\[\\]{}\"“”«»„–—…/\\\\=+*~<>@#&、。，．！？：；「」『』【】（）〈〉《》・"
                   "←-⯿☀-➿️\U0001F000-\U0001FAFF]+|\\s-+\\s|\\s-+$|^-+\\s|\\n")
TOKEN = re.compile(r"(?P<year>(?<!\w)(?:19|20)\d\d(?!\w))|(?P<dim>(?<!\w)[1-9][dg](?!\w))|"
                   r"(?P<word>[^\W\d_]+(?:'[^\W\d_]+)*)|(?P<num>\d+(?:[^\W\d_]{1,2}(?![^\W\d_]))?)")
# a number takes up to two letters after it with it ("11th", "4pm", "1960s"): they are not words
CJK = re.compile("[぀-ヿ㐀-䶿一-鿿豈-﫿ｦ-ﾟ]+")


DATEISH = re.compile(r"(?:[12]?\d|3[01])(?:st|nd|rd|th)?|(?:19|20)\d\d")    # a day of the month or a year
YEAR = re.compile(r"(?:19|20)\d\d")
# dates, flagged and counted apart in the rising and falling lists: they say when, not what
CALENDAR = frozenset("""
january february march april may june july august september october november december
jan feb apr jun jul aug sep sept oct nov dec
monday tuesday wednesday thursday friday saturday sunday
janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro
enero febrero marzo mayo junio julio septiembre octubre noviembre diciembre
""".split())


def is_calendar(term):
    """A year, month or weekday, or a pair of them ("october 2026")."""
    return all(w in CALENDAR or YEAR.fullmatch(w) for w in term.split())


def normalise(text):
    return unicodedata.normalize("NFKC", text or "").translate(APOSTROPHES)


@functools.lru_cache(maxsize=None)
def fold(t):
    """A token without its accents (NFKD, combining marks dropped), to compare names: "król" as "krol"."""
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


def _fold(t):
    return t if t is None or t.isascii() else fold(t)


def _word(t):
    if t.endswith("'s"):
        t = t[:-2]
    return None if len(t) < 2 or t in STOPWORDS else t


def _cjk(word):
    """A word with Chinese or Japanese letters: those runs as overlapping character pairs, each standing alone
    (None between them, so no word bigram forms), the rest as words."""
    out, pos = [], 0
    for m in CJK.finditer(word):
        if m.start() > pos:
            out.append(_word(word[pos:m.start()]))
        run = m.group(0)
        for pair in ([run[i:i + 2] for i in range(len(run) - 1)] or [run]):
            out += [None, pair]
        out.append(None)
        pos = m.end()
    if pos < len(word):
        out.append(_word(word[pos:]))
    return out


def tokens(text):
    """A text's tokens in order, as runs that a bigram does not cross: [[token or None, ...], ...]. None marks a
    dropped token (a stopword, a number other than a year, a single letter), which a bigram does not cross either."""
    return _tokens(normalise(text).lower())


def _tokens(text):
    """tokens() of a text already normalised and in lower case."""
    if URL_HINT.search(text):
        text = URL.sub(" | ", text)
    if "u.s." in text:
        text = USA.sub("usa", text)
    cjk = CJK.search(text) is not None
    runs = []
    for segment in BREAK.split(text):
        run, raw, kept, special = [], [], False, False
        for year, dim, t, num in TOKEN.findall(segment):
            if t:
                if cjk and CJK.search(t):
                    pairs = _cjk(t)
                    run += pairs
                    raw += [""] * len(pairs)
                    kept = True
                    continue
                if t.endswith("'s"):
                    t = t[:-2]
                raw.append(t)
                if len(t) < 2 or t in STOPWORDS:
                    special = special or t in ("may", "will")
                    t = None
            else:
                raw.append(year or dim or num)
                t = None if num else (year or dim)
            run.append(t)
            kept = kept or t is not None
        if special:
            # "may" beside a day or a year is the month; "will" after "free" is the noun
            for i, r in enumerate(raw):
                if r == "may" and any(0 <= j < len(raw) and DATEISH.fullmatch(raw[j]) for j in (i - 1, i + 1)):
                    run[i] = "may"
                elif r == "will" and i and raw[i - 1] == "free":
                    run[i] = "will"
            kept = kept or any(t is not None for t in run)
        if kept:
            runs.append(run)
    return runs


def _without_phrases(run, phrases):
    """The run with the phrases (folded token sequences) set to None, compared without accents."""
    f, out = None, None
    for p in phrases:
        if f is None:
            f = [_fold(t) for t in run]
        if p[0] not in f:
            continue
        for i in range(len(f) - len(p) + 1):
            if tuple(f[i:i + len(p)]) == p:
                out = out or list(run)
                out[i:i + len(p)] = [None] * len(p)
                f[i:i + len(p)] = [None] * len(p)
    return out or run


def terms(runs, drop=frozenset(), phrases=(), drop_pairs=frozenset()):
    """(unigrams, bigrams) of tokenised runs, without the tokens in drop, the token sequences in phrases (a
    channel's name) and the pairs in drop_pairs; drop, phrases and drop_pairs hold folded forms (fold()), and a
    token is compared without its accents."""
    uni, bi = [], []
    for run in runs:
        if phrases:
            run = _without_phrases(run, phrases)
        prev = None
        for t in run:
            if t is None or (drop and (t if t.isascii() else fold(t)) in drop):
                prev = None
                continue
            uni.append(t)
            if prev is not None:
                pair = f"{prev} {t}"
                if not drop_pairs or (pair if pair.isascii() else fold(pair)) not in drop_pairs:
                    bi.append(pair)
            prev = t
    return uni, bi


# words of the channels' names that are also ordinary words of these titles (English or the field's own): they are
# dropped only inside the whole name ("Elizabeth April", "Pleiadian Council Whispers"), never alone, so that the
# month, the colour or the council stay in the other titles
NAME_WORDS_IN_USE = frozenset("""
april may june july august rose white gold golden eagle young ray aurora lie price royal ash blossom magenta pixie
nobel teller butler channeler channeling pleiadian council whispers ashtar command lower decks lightworkers
lightworker sound sounds waves heal true cosmic agency prime disclosure blue star light love grace hope joy faith
king queen angel sky sun moon river stone
""".split())


class NameDrops(tuple):
    """(single, phrases, strings): name words dropped alone, name phrases (folded token tuples) and names in
    Chinese or Japanese letters (cut out of the text before it is tokenised)."""

    def __new__(cls, single=frozenset(), phrases=(), strings=()):
        return super().__new__(cls, (frozenset(single), list(phrases), tuple(strings)))


def _trim(p):
    lo, hi = 0, len(p)
    while lo < hi and p[lo] is None:
        lo += 1
    while hi > lo and p[hi - 1] is None:
        hi -= 1
    return tuple(p[lo:hi])


def name_drops(channel, name="", role=""):
    """NameDrops of a channel's own name: its folder name, display name and the alias in brackets as phrases
    (accents folded, no stopword at their edges); each word of a person's display name alone unless it is in
    NAME_WORDS_IN_USE (an organisation's words only as a phrase); a one-word name or alias alone likewise; the
    name's runs of Chinese or Japanese letters as strings to cut out."""
    name = normalise(name or "")
    bare = re.sub(r"\([^)]*\)", " ", name)
    forms = [channel.replace("-", " "), bare, *re.findall(r"\(([^)]*)\)", name)]
    strings = sorted({m for form in forms for m in CJK.findall(form)}, key=lambda s: (-len(s), s))
    forms = [CJK.sub(" | ", form) for form in forms]
    phrases = {_trim([_fold(t) for t in run]) for form in forms for run in tokens(form)}
    phrases = sorted((p for p in phrases if p), key=lambda p: (-len(p), [t or "" for t in p]))
    single = set()
    if bare.strip() and (role or "").lower() not in ORGANISATIONS:
        single = {_fold(t) for run in tokens(CJK.sub(" | ", bare)) for t in run if t is not None}
    single |= {p[0] for p in phrases if len(p) == 1}
    single -= NAME_WORDS_IN_USE
    return NameDrops(single, [p for p in phrases if len(p) > 1], strings)


def cut_names(text, strings):
    """The text without the names in Chinese or Japanese letters (NameDrops' strings)."""
    if strings:
        text = normalise(text)
        for s in strings:
            text = text.replace(s, " | ")
    return text


def furniture(title_terms, share=0.5, min_titles=10):
    """{term: share} of the words and pairs in more than share of a channel's titles: title furniture, such as a
    series name or the channeler's name in every title. None when the channel has fewer than min_titles titles."""
    n = len(title_terms)
    if n < max(1, min_titles):
        return {}
    df = collections.Counter()
    for uni, bi in title_terms:
        df.update(set(uni) | set(bi))
    return {t: c / n for t, c in df.items() if c / n > share}


# ---------------------------------------------------------------------------------------------------- statistics
def tfidf(docs):
    """({doc: {term: weight}}, df, idf) for docs {doc: Counter}: tf = 1 + ln(count), idf = ln((1 + N) / (1 + df))
    + 1, each document's weights L2-normalised."""
    n = len(docs)
    df = collections.Counter()
    for c in docs.values():
        df.update(t for t, k in c.items() if k > 0)
    idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
    out = {}
    for name, c in docs.items():
        w = {t: (1 + math.log(k)) * idf[t] for t, k in c.items() if k > 0}
        norm = math.sqrt(sum(v * v for v in w.values())) or 1.0
        out[name] = {t: v / norm for t, v in w.items()}
    return out, df, idf


def log_odds(a, b, scale=None, prior=None):
    """{term: (delta, z)}: Monroe, Colaresi and Quinn's (2008) log-odds ratio of a against b with an informative
    Dirichlet prior, a_w = a0 * prior[w], and their approximate variance 1 / (y_a + a_w) + 1 / (y_b + a_w).
    prior: shares that cover every term of a and b; by default the pooled shares of a and b themselves, (y_a +
    y_b) / (n_a + n_b), so that each side is drawn toward the pooled rate and the sign of delta is the sign of
    y_a / n_a - y_b / n_b. scale: a0, a number, or None for n_a (the prior weighs as much as the first side)."""
    na, nb = sum(a.values()), sum(b.values())
    a0 = float(na if scale is None else scale)
    out = {}
    for t in set(a) | set(b):
        ya, yb = a.get(t, 0), b.get(t, 0)
        al = a0 * (prior[t] if prior is not None else (ya + yb) / (na + nb))
        d = (math.log((ya + al) / max(na + a0 - ya - al, 1e-12))
             - math.log((yb + al) / max(nb + a0 - yb - al, 1e-12)))
        out[t] = (d, d / math.sqrt(1 / (ya + al) + 1 / (yb + al)))
    return out


def stratified_z(strata):
    """The Mantel-Haenszel z (with the 0.5 continuity correction, sign kept) over 2x2 tables [(x, n1, y, n2)]: x
    of n1 items now and y of n2 before use the term, each table one channel against its own history; positive when
    the tiers use it more than each channel's own pooled rate leads to expect. None when no table varies."""
    o = e = v = 0.0
    for x, n1, y, n2 in strata:
        n, m = n1 + n2, x + y
        if n < 2 or m == 0 or m == n or not n1 or not n2:
            continue
        o += x
        e += n1 * m / n
        v += n1 * n2 * m * (n - m) / (n * n * (n - 1))
    if v <= 0:
        return None
    d = o - e
    return math.copysign(max(0.0, abs(d) - 0.5), d) / math.sqrt(v)


def p_two_sided(z):
    return math.erfc(abs(z) / math.sqrt(2))


def bh_threshold(pvalues, q=0.05):
    """The largest p-value that Benjamini-Hochberg at q keeps (0.0 when none)."""
    ranked, m, keep = sorted(pvalues), len(pvalues), 0.0
    for i, p in enumerate(ranked, 1):
        if p <= q * i / m:
            keep = p
    return keep


def _lchoose(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher(k1, n1, k2, n2):
    """(p_rise, p_two_sided) of Fisher's exact test of k1 of n1 against k2 of n2; p_rise is one-sided, that the
    first share is the larger. (None, None) when a side is empty."""
    if n1 <= 0 or n2 <= 0:
        return None, None
    big_k, big_n = k1 + k2, n1 + n2
    lo, hi = max(0, n1 - (big_n - big_k)), min(big_k, n1)
    p = {x: math.exp(_lchoose(big_k, x) + _lchoose(big_n - big_k, n1 - x) - _lchoose(big_n, n1))
         for x in range(lo, hi + 1)}
    rise = sum(v for x, v in p.items() if x >= k1)
    two = sum(v for v in p.values() if v <= p[k1] * (1 + 1e-7))
    return min(1.0, rise), min(1.0, two)


def two_proportion_z(k1, n1, k2, n2):
    if n1 <= 0 or n2 <= 0:
        return None
    p = (k1 + k2) / (n1 + n2)
    if p <= 0 or p >= 1:
        return None
    return (k1 / n1 - k2 / n2) / math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))


def rnd(x, n=4):
    return None if x is None else round(x, n)


def per100(k, n):
    return round(100 * k / n, 2) if n else None


# ---------------------------------------------------------------------------------------------------- the lexicon
# an include whose file declares no group is weak when its id or topic names flares, storms or CMEs (or its topic
# is "solar" alone); a "solar flash" include stays strong unless the file says otherwise
WEAK_HINT = re.compile(r"flare|storm|(?<![a-z])cmes?(?![a-z])|coronal|geo-?magnetic|space.?weather|^solar$", re.I)
FLAGS = re.I | re.S
SLOW = re.compile(r"(?<![\\\[])\^|(?<![\\\[])\$|\\[AZ]|\(\?[=!][^)]*\.[*+{]")   # anchors, look-aheads over .*

FALLBACK = {
    "include": [
        {"id": "blackout", "topic": "power_grid", "pattern": r"\bblack-?outs?\b"},
        {"id": "power_grid", "topic": "power_grid", "pattern": r"\b(?:power|electric(?:al|ity)?) grids?\b"},
        {"id": "power_outage", "topic": "power_grid",
         "pattern": r"\b(?:power|electric(?:al|ity)?) (?:outages?|cuts?|failures?)\b"},
        {"id": "grid_down", "topic": "power_grid",
         "pattern": r"\bgrid[- ]down\b|\bgrids? (?:is |are |goes |going |will go |went |could go |coming )?down\b"},
        {"id": "internet_down", "topic": "internet",
         "pattern": r"\binternet (?:is |goes |going |will go |went |could go |will be |being )?(?:down|off(?:line)?)\b|"
                    r"\binternet (?:shut-?downs?|outages?|blackouts?)\b|"
                    r"\b(?:shut|shutting|shuts|turn|turning|turns|switch|switching)(?:ed)? (?:down|off) "
                    r"(?:the |of the )?internet\b"},
        {"id": "kill_switch", "topic": "internet", "pattern": r"\bkill[- ]?switch(?:es)?\b"},
        {"id": "emp", "topic": "power_grid", "pattern": r"\bE\.?M\.?P\.?s?\b|\belectro-?magnetic pulses?\b"},
        {"id": "carrington", "topic": "power_grid", "pattern": r"\bcarrington\b"},
        {"id": "cyber_attack", "topic": "internet",
         "pattern": r"\bcyber[- ]?(?:attacks?|warfare|war|strikes?|threats?|risks?)\b"},
        {"id": "days_of_darkness", "topic": "darkness_event",
         "pattern": r"\b(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten) days? of (?:total |complete )?"
                    r"dark(?:ness)?\b"},
        {"id": "without_power", "topic": "power_grid", "pattern": r"\bwithout (?:power|electricity)\b"},
        {"id": "solar_flare", "topic": "solar", "group": "weak", "pattern": r"\bsolar flares?\b|\bx-?class flares?\b"},
        {"id": "solar_storm", "topic": "solar", "group": "weak",
         "pattern": r"\b(?:solar|geo-?magnetic|magnetic) storms?\b"},
        {"id": "cme", "topic": "solar", "group": "weak", "pattern": r"\bCMEs?\b|\bcoronal mass ejections?\b"},
    ],
    "exclude": [
        {"id": "metaphysical_grid", "mode": "overlap", "scope": ["power_grid", "grid_down"],
         "pattern": r"\b(?:crystal(?:line)?|planetary|earth'?s|gaia'?s|light|christ(?:ed)?|ascension|unity|"
                    r"consciousness|ley|morphogenetic|etheric|heart|love|diamond|golden|energetic|spiritual|cosmic|"
                    r"galactic|lightworker|ancient)[- ](?:power |energy )?grids?\b(?: (?:is |are |goes |going )?down)?|"
                    r"\bgrid ?work(?:ers?|ing)?\b"},
        # a day of the Dreamspell calendar ("Kin 79: Blue Magnetic Storm"), not the weather of the sun
        {"id": "dreamspell_storm", "mode": "overlap", "scope": ["solar_storm"],
         "pattern": r"\b(?:blue|red|white|yellow) (?:magnetic|lunar|electric|self-existing|overtone|rhythmic|resonant|"
                    r"galactic|solar|planetary|spectral|crystal|cosmic) storms?\b"},
        {"id": "media_blackout", "mode": "overlap", "scope": ["blackout"],
         "pattern": r"\b(?:media|news|information|press|social media)[- ]black-?outs?\b"},
        {"id": "schumann", "mode": "unit", "scope": ["blackout", "solar_flare", "solar_storm", "cme"],
         "pattern": r"\bschumann\b"},
        {"id": "fainting", "mode": "unit", "scope": ["blackout"],
         "pattern": r"\b(?:faint\w*|passed out|pass out|drunk|seizures?)\b"},
        {"id": "carrington_person", "mode": "overlap", "scope": ["carrington"],
         "pattern": r"\b(?:hereward|leonora) carrington\b"},
        {"id": "not_without_power", "mode": "overlap", "scope": ["without_power"],
         "pattern": r"\b(?:not|never) without power\b"},
    ],
}


class Lexicon:
    """Include patterns (id, topic, group strong or weak) and exclude patterns. An include match in a unit (a title
    or a sentence) is void when an exclude in its scope (include ids or topics; none means all) matches the unit
    ("unit", the default, as the theme's measured excludes) or overlaps the match ("overlap")."""

    def __init__(self, data, source, weak_precision=None):
        self.source = source
        inc_list = data.get("include") or data.get("includes") or []
        exc_list = data.get("exclude") or data.get("excludes") or []
        use = data.get("use") or data.get("proposed")
        use = set(use) if isinstance(use, list) else None
        self.includes, self.excludes = [], []
        for i, e in enumerate(inc_list):
            if isinstance(e, (list, tuple)):
                e = dict(zip(("id", "topic", "pattern"), e)) if len(e) >= 3 else {"id": e[0], "pattern": e[-1]}
            ident = str(e.get("id") or e.get("name") or f"include_{i}")
            pattern = e.get("pattern") or e.get("regex") or e.get("re")
            if isinstance(e.get("patterns"), list):
                pattern = "|".join(f"(?:{p})" for p in e["patterns"])
            if not pattern or (use is not None and ident not in use):
                continue
            if any(e.get(k) is False for k in ("use", "proposed", "active", "keep")) or \
                    str(e.get("status", "")).lower() in {"dropped", "rejected", "off", "excluded", "unused"}:
                continue
            topic = str(e.get("topic") or "")
            declared = next((str(e[k]).lower() for k in ("group", "strength", "tier", "level") if e.get(k)), "")
            weak = (declared == "weak" or e.get("weak") is True or
                    (declared != "strong" and (bool(WEAK_HINT.search(ident) or WEAK_HINT.search(topic)) or
                                               (weak_precision is not None and
                                                isinstance(e.get("precision"), (int, float)) and
                                                e["precision"] < weak_precision))))
            self.includes.append({"id": ident, "topic": topic, "group": "weak" if weak else "strong",
                                  "pattern": pattern, "rx": re.compile(pattern, FLAGS)})
        for i, e in enumerate(exc_list):
            if isinstance(e, (list, tuple)):
                e = {"id": e[0], "pattern": e[1], "scope": e[2] if len(e) > 2 else None}
            pattern = e.get("pattern") or e.get("regex") or e.get("re")
            if not pattern:
                continue
            scope = e.get("scope")
            scope = None if scope in (None, "", "all", "*") else set([scope] if isinstance(scope, str) else scope)
            mode = str(e.get("mode") or e.get("within") or "unit").lower()
            self.excludes.append({"id": str(e.get("id") or e.get("name") or f"exclude_{i}"), "pattern": pattern,
                                  "scope": scope, "mode": "overlap" if mode in {"overlap", "match", "span"} else "unit",
                                  "rx": re.compile(pattern, FLAGS)})
        # a screen, so that only candidate units go through every pattern and exclude: the plain patterns joined
        # (run once over a whole text, then per unit), and each anchored or look-ahead pattern alone per unit (run
        # over a whole text, "^(?=.*a)(?=.*b)" would cost the square of its length)
        slow = [x for x in self.includes if SLOW.search(x["pattern"])]
        plain = [x for x in self.includes if not SLOW.search(x["pattern"])]
        self.fast, self.slow = None, [x["rx"] for x in slow]
        if plain:
            try:
                self.fast = re.compile("|".join(f"(?:{x['pattern']})" for x in plain), FLAGS)
            except re.error:
                self.slow += [x["rx"] for x in plain]

    def describe(self):
        return {"source": self.source,
                "include": [{k: x[k] for k in ("id", "topic", "group", "pattern")} for x in self.includes],
                "exclude": [{"id": x["id"], "mode": x["mode"], "scope": sorted(x["scope"]) if x["scope"] else "all",
                             "pattern": x["pattern"]} for x in self.excludes]}

    def screen_text(self, text):
        """Whether the plain patterns match anywhere in a whole text (its units are then screened one by one)."""
        return bool(self.fast and self.fast.search(text))

    def candidate(self, unit, text_hit=True):
        return bool((text_hit and self.fast and self.fast.search(unit)) or any(rx.search(unit) for rx in self.slow))

    def match(self, text):
        """{include id: group} of the includes that match the unit and that no exclude voids."""
        hits, found = {}, None
        for inc in self.includes:
            for m in inc["rx"].finditer(text):
                if found is None:
                    found = [(x, [(e.start(), e.end()) for e in x["rx"].finditer(text)]) for x in self.excludes]
                void = any(spans and (x["scope"] is None or inc["id"] in x["scope"] or inc["topic"] in x["scope"]) and
                           (x["mode"] == "unit" or any(s < m.end() and m.start() < e for s, e in spans))
                           for x, spans in found)
                if not void:
                    hits[inc["id"]] = inc["group"]
                    break
        return hits


def load_lexicon(path, weak_precision=None):
    if path and Path(path).exists():
        try:
            lex = Lexicon(json.loads(Path(path).read_text(encoding="utf-8")), str(path), weak_precision)
            if lex.includes:
                return lex
            print(f"warning: {path} has no include patterns; using the built-in list", file=sys.stderr)
        except (ValueError, re.error, AttributeError, TypeError) as exc:
            print(f"warning: cannot use {path} ({exc}); using the built-in list", file=sys.stderr)
    return Lexicon(FALLBACK, "built-in fallback (literal terms)")


# ---------------------------------------------------------------------------------------------------- counting
class Side:
    """Counts for one side (tier or history) of one channel and kind."""

    def __init__(self, lex, drop=frozenset(), phrases=(), drop_pairs=frozenset(), keep_text=True, strings=()):
        self.lex, self.drop, self.phrases, self.drop_pairs, self.keep_text = lex, drop, phrases, drop_pairs, keep_text
        self.strings = tuple(strings)
        self.items, self.uni, self.bi, self.docfreq = 0, collections.Counter(), collections.Counter(), collections.Counter()
        self.strong, self.weak, self.units_matched, self.matches = 0, 0, 0, []
        self.units, self.units_dropped = 0, 0
        self._all = None

    def add(self, item, label, texts, runs=None, dropped=0):
        """One item: a title, or a text as its sentences. runs: the texts' tokens when already made; dropped: the
        sentences of the text left out as furniture or promotion (counted only)."""
        self.items += 1
        self.units += len(texts)
        self.units_dropped += dropped
        self._all = None
        seen = set()
        units = [normalise(t).replace("_", " ") for t in texts]     # "Flares_" would hide a \b from the lexicon
        for i, unit in enumerate(units):
            uni, bi = terms(runs[i] if runs is not None else _tokens(cut_names(unit, self.strings).lower()),
                            self.drop, self.phrases, self.drop_pairs)
            self.uni.update(uni)
            self.bi.update(bi)
            seen.update(uni)
            seen.update(bi)
        self.docfreq.update(seen)
        groups, ids, quotes = set(), set(), []
        text_hit = self.lex.screen_text(" \n ".join(units))
        if text_hit or self.lex.slow:
            for text, unit in zip(texts, units):
                hits = self.lex.match(unit) if self.lex.candidate(unit, text_hit) else {}
                if hits:
                    self.units_matched += 1
                    groups.update(hits.values())
                    ids.update(hits)
                    if self.keep_text and len(quotes) < 5:
                        quotes.append({"quote": quote(text), "ids": sorted(hits)})
        self.strong += "strong" in groups
        self.weak += "weak" in groups
        if groups:
            rec = {"item": item, "groups": sorted(groups), "ids": sorted(ids)}
            if self.keep_text:
                rec.update(label=quote(label or ""), units=quotes)
            self.matches.append(rec)

    def tokens_n(self):
        return sum(self.uni.values())

    def terms_n(self):
        return len(self.uni) + len(self.bi)

    def all_terms(self):
        """Unigrams and bigrams together (made once, after the last add)."""
        if self._all is None:
            self._all = self.uni + self.bi
        return self._all


# ---------------------------------------------------------------------------------------------------- reading
def resolve(root, path):
    p = Path(path)
    return p if p.is_absolute() or p.exists() else Path(root) / p


def text_units(root, row, kinds):
    """{kind: [sentence, ...]} of one catalogue row, kinds apart: texts from the source and speech-to-text made
    here through prediction_timeline.read_item_texts (it cuts a blog's reader comments), YouTube captions from
    the row's captions_path."""
    out = {}
    if {"made", "source"} & set(kinds) and (row.get("asr_path") or row.get("publisher_text_path")):
        for kind, sentences in read_item_texts(root, row):
            if kind in kinds:
                sents = [s for _, s in sentences if s]
                if sents:
                    out[kind] = sents
    cap = row.get("captions_path") or ""
    if "captions" in kinds and cap and (root / cap).exists():
        sents = [s for _, s in sentences_of_text((root / cap).read_text(encoding="utf-8", errors="replace")) if s]
        if sents:
            out["captions"] = sents
    return out


def has_kind(row, kinds):
    return any(row.get(KIND_PATH[k]) for k in kinds)


def content(sentences):
    """(kept, dropped): the sentences without page furniture, promotion and editors' notes (NOT_CONTENT), a blog
    post's date header cut out of the sentence that begins with it (a sentence left without a letter is dropped)."""
    kept = []
    for s in sentences:
        if any(rx.search(s) for rx in NOT_CONTENT):
            continue
        s = s.strip()
        if POST_HEADER.search(s):
            s = POST_HEADER.sub(" ", s, count=1).strip()
        if s and re.search(r"[^\W\d_]", s):
            kept.append(s)
    return kept, len(sentences) - len(kept)


def longest_texts(root, rows, kinds, keep_all=False):
    """{kind: (item_id, sentences, dropped)} over the rows of one recording: per kind the longest text, its
    furniture and promotion sentences left out (unless keep_all) and counted."""
    best = {}
    for row in sorted(rows, key=lambda r: r["item_id"]):
        for kind, sents in text_units(root, row, kinds).items():
            kept, dropped = (sents, 0) if keep_all else content(sents)
            size = sum(len(s) for s in kept)
            if kept and (kind not in best or size > best[kind][0]):
                best[kind] = (size, row["item_id"], kept, dropped)
    return {k: (item, sents, dropped) for k, (_, item, sents, dropped) in best.items()}


# ---------------------------------------------------------------------------------------------------- the analysis
def analyse(root, scope, tier_rows, history_rows, catalogue, lex, opts, names=None):
    """Everything for one scope as a dict (see the module's docstring). opts: an argparse namespace or alike."""
    root = Path(root)
    kinds = [k for k in KINDS if k in opts.kinds]
    only = set(opts.only or [])
    tabs = history_tabs(opts.history_tabs, tier_rows)
    names = names or {}
    tier_channel = {r["video_id"]: r["channel_dir"] for r in tier_rows}
    channels = sorted({r["channel_dir"] for r in tier_rows if not only or r["channel_dir"] in only})
    sides = {}                      # (channel, kind) -> {"tier": Side, "history": Side, "furniture": {...}}
    drops = {ch: name_drops(ch, *names.get(ch, ("", ""))) for ch in channels}

    # titles
    if "titles" in kinds:
        tier_t = collections.defaultdict(list)
        for r in tier_rows:
            if r["channel_dir"] in drops:
                tier_t[r["channel_dir"]].append((r["video_id"], r["title"] or ""))
        hist_t = collections.defaultdict(list)
        for r in history_rows:
            ch = r["channel_dir"]
            if ch in drops and r["video_id"] not in tier_channel and (tabs is None or (r.get("tab") or "") in tabs):
                hist_t[ch].append((r["video_id"], r["title"] or ""))
        for ch in channels:
            single, phrases, strings = drops[ch]
            t_runs = [tokens(cut_names(t, strings)) for _, t in tier_t[ch]]
            h_runs = [tokens(cut_names(t, strings)) for _, t in hist_t[ch]]
            furn = furniture([terms(r, single, phrases) for r in t_runs + h_runs],
                             opts.furniture_share, opts.furniture_min_titles)
            f_uni = frozenset(_fold(t) for t in furn if " " not in t) | single
            f_bi = frozenset(_fold(t) for t in furn if " " in t)
            tier, hist = (Side(lex, f_uni, phrases, f_bi, strings=strings),
                          Side(lex, f_uni, phrases, f_bi, strings=strings))
            for (vid, title), runs in zip(tier_t[ch], t_runs):
                tier.add(vid, title, [title], [runs])
            for (vid, title), runs in zip(hist_t[ch], h_runs):
                hist.add(vid, title, [title], [runs])
            # history titles the same as a tier title (a re-upload, or a title the channel repeats): counted, kept,
            # since the listing has no dates to tell the two apart
            same = {" ".join(normalise(t).casefold().split()) for _, t in tier_t[ch]}
            sides[(ch, "titles")] = {"tier": tier, "history": hist, "furniture": furn,
                                     "same_title": sum(" ".join(normalise(t).casefold().split()) in same
                                                       for _, t in hist_t[ch])}

    # texts, through the catalogue
    tkinds = [k for k in kinds if k in TEXT_KINDS]
    keep_all = bool(getattr(opts, "keep_furniture", False))
    if tkinds and catalogue:
        by_rec = collections.defaultdict(list)
        for row in catalogue:
            rec = row["item_id"] if row["item_id"] in tier_channel else (
                row.get("twin_of") if row.get("twin_of") in tier_channel else None)
            if rec and tier_channel[rec] in drops and has_kind(row, tkinds):
                by_rec[rec].append(row)
        for rec in sorted(by_rec):
            ch = tier_channel[rec]
            for kind, (item, sents, dropped) in sorted(longest_texts(root, by_rec[rec], tkinds, keep_all).items()):
                if (ch, kind) not in sides:
                    single, phrases, strings = drops[ch]
                    sides[(ch, kind)] = {"tier": Side(lex, single, phrases, strings=strings),
                                         "history": Side(lex, single, phrases, keep_text=False, strings=strings),
                                         "furniture": {}}
                sides[(ch, kind)]["tier"].add(f"{rec}/{item}" if item != rec else rec, rec, sents, dropped=dropped)
        need = collections.defaultdict(set)
        for ch, kind in sides:
            if kind in TEXT_KINDS:
                need[ch].add(kind)
        hist_rec = collections.defaultdict(lambda: collections.defaultdict(list))
        for row in catalogue:
            ch = row.get("person_id")
            if ch in need and has_kind(row, need[ch]):
                rec = row.get("twin_of") or row["item_id"]
                if rec not in tier_channel and row["item_id"] not in tier_channel:
                    hist_rec[ch][rec].append(row)
        for ch in sorted(hist_rec):
            for rec in sorted(hist_rec[ch]):
                for kind, (item, sents, dropped) in sorted(
                        longest_texts(root, hist_rec[ch][rec], need[ch], keep_all).items()):
                    sides[(ch, kind)]["history"].add(item, "", sents, dropped=dropped)

    # per kind: TF-IDF, log-odds, across channels, blackouts
    result = {"scope": scope, "history_tabs": sorted(tabs) if tabs else "all", "kinds": {}, "channels": {}}
    for kind in kinds:
        chs = [ch for ch in channels if (ch, kind) in sides and sides[(ch, kind)]["tier"].items]
        if not chs:
            continue
        weights, df, idf = tfidf({ch: sides[(ch, kind)]["tier"].all_terms() for ch in chs})
        for ch in chs:
            result["channels"].setdefault(ch, {})[kind] = channel_view(sides[(ch, kind)], weights[ch], df, kind, opts)
        result["kinds"][kind] = across(kind, chs, sides, df, opts)
    return result


def history_tabs(option, tier_rows):
    """The listing tabs that the history takes: "tier" (the default) the tabs that the tier's rows have (all when
    they name none), "all" every tab, else the comma-separated tabs."""
    if option in (None, "", "tier"):
        return {r.get("tab") for r in tier_rows if r.get("tab")} or None
    if option == "all":
        return None
    return {t.strip() for t in option.split(",") if t.strip()}


def prior_scale(opts, n_tier):
    """a0 of the log-odds: --prior-scale "tier" (the default) is the tier's own token count, else the number."""
    s = getattr(opts, "prior_scale", "tier")
    return float(n_tier) if s in (None, "", "tier") else float(s)


def channel_view(s, weights, df, kind, opts):
    tier, hist = s["tier"], s["history"]
    top = opts.json_top
    ranked = sorted(((t, w) for t, w in weights.items() if tier.all_terms()[t] >= opts.min_count),
                    key=lambda x: (-x[1], x[0]))
    out = {"tier_items": tier.items, "history_items": hist.items,
           "tier_sentences": tier.units, "history_sentences": hist.units,
           "tier_sentences_dropped": tier.units_dropped, "history_sentences_dropped": hist.units_dropped,
           "tier_tokens": tier.tokens_n(), "history_tokens": hist.tokens_n(),
           "tier_terms": tier.terms_n(), "history_terms": hist.terms_n(),
           "furniture": {t: round(v, 3) for t, v in sorted(s["furniture"].items())},
           **({"history_same_title_as_tier": s.get("same_title", 0)} if kind == "titles" else {}),
           "tfidf": [{"term": t, "count": tier.all_terms()[t], "channels": df[t], "weight": rnd(w),
                      "tier_item_share": rnd(tier.docfreq[t] / tier.items, 3)}
                     for t, w in ranked[:top]]}
    least = getattr(opts, "min_text_tokens", 0) if kind != "titles" else 0
    if hist.items and tier.items and tier.tokens_n() < least:
        out["log_odds_skipped"] = f"{tier.tokens_n()} tokens now, fewer than {least}: not tested"
    elif hist.items and tier.items:
        rows, pvals = [], []
        m = opts.min_significant_count
        scales = {}
        for order in ("uni", "bi"):
            a, b = getattr(tier, order), getattr(hist, order)
            na, nb = sum(a.values()), sum(b.values())
            if not na or not nb:
                continue
            scales[order] = prior_scale(opts, na)
            for t, (d, z) in log_odds(a, b, scales[order]).items():
                ya, yb = a.get(t, 0), b.get(t, 0)
                rows.append({"term": t, "now": ya, "before": yb, "per1000_now": rnd(1000 * ya / na, 3),
                             "per1000_before": rnd(1000 * yb / nb, 3), "delta": rnd(d), "z": rnd(z),
                             "calendar": is_calendar(t), "_z": z})
                if (z > 0 and ya >= m) or (z < 0 and yb >= m):      # could be called significant
                    pvals.append(p_two_sided(z))
        cut = bh_threshold(pvals) if pvals else 0.0
        for r in rows:
            r["significant"] = (r["_z"] > Z and r["now"] >= m) or (r["_z"] < -Z and r["before"] >= m)
            r["bh"] = bool(r["significant"] and cut and p_two_sided(r["_z"]) <= cut)
        rising = sorted((r for r in rows if r["_z"] > 0 and r["now"] >= opts.min_count), key=lambda r: (-r["_z"], r["term"]))
        falling = sorted((r for r in rows if r["_z"] < 0 and r["before"] >= opts.min_count), key=lambda r: (r["_z"], r["term"]))

        def n_sig(sign, calendar, key="significant"):
            return sum(1 for r in rows if r[key] and (r["_z"] > 0) == (sign > 0) and r["calendar"] == calendar)
        out.update(prior_scale={k: rnd(v, 1) for k, v in scales.items()},
                   rising_significant=n_sig(1, False), rising_significant_calendar=n_sig(1, True),
                   falling_significant=n_sig(-1, False), falling_significant_calendar=n_sig(-1, True),
                   rising_bh=n_sig(1, False, "bh") + n_sig(1, True, "bh"),
                   falling_bh=n_sig(-1, False, "bh") + n_sig(-1, True, "bh"),
                   bh_family=len(pvals),
                   rising=[{k: v for k, v in r.items() if k != "_z"} for r in rising[:top]],
                   falling=[{k: v for k, v in r.items() if k != "_z"} for r in falling[:top]])
    out["blackouts"] = blackout_view(tier, hist)
    return out


def blackout_view(tier, hist):
    out = {"tier_items": tier.items, "history_items": hist.items,
           "tier_units_matched": tier.units_matched, "history_units_matched": hist.units_matched}
    for g in ("strong", "weak"):
        k1, k2 = getattr(tier, g), getattr(hist, g)
        rise, two = fisher(k1, tier.items, k2, hist.items)
        out[g] = {"tier": k1, "history": k2, "tier_per100": per100(k1, tier.items),
                  "history_per100": per100(k2, hist.items), "fisher_p_rise": rnd(rise), "fisher_p_two_sided": rnd(two),
                  "z": rnd(two_proportion_z(k1, tier.items, k2, hist.items), 3),
                  "rose": bool(hist.items and tier.items and k1 / tier.items > k2 / hist.items)}
    out["tier_matches"] = tier.matches
    out["history_matches"] = hist.matches
    return out


def across(kind, chs, sides, df, opts):
    """The cross-channel view of one kind."""
    tiers = {ch: sides[(ch, kind)]["tier"] for ch in chs}
    hists = {ch: sides[(ch, kind)]["history"] for ch in chs if sides[(ch, kind)]["history"].items}
    hist_df = collections.Counter()
    for h in hists.values():
        hist_df.update(h.docfreq.keys())
    rows = []
    for t, d in df.items():
        if d < opts.min_channels:
            continue
        now = [tiers[ch].docfreq[t] / tiers[ch].items for ch in chs]
        before = [h.docfreq[t] / h.items for h in hists.values()]
        up = sum(1 for ch, h in hists.items() if tiers[ch].docfreq[t] / tiers[ch].items > h.docfreq[t] / h.items)
        down = sum(1 for ch, h in hists.items() if tiers[ch].docfreq[t] / tiers[ch].items < h.docfreq[t] / h.items)
        z = stratified_z([(tiers[ch].docfreq[t], tiers[ch].items, h.docfreq[t], h.items) for ch, h in hists.items()])
        rows.append({"term": t, "channels_now": d, "channels_before": hist_df[t],
                     "count_now": sum(tiers[ch].all_terms()[t] for ch in chs),
                     "share_now_pct": rnd(100 * sum(now) / len(now), 2),
                     "share_before_pct": rnd(100 * sum(before) / len(before), 2) if before else None,
                     "channels_up": up, "channels_down": down, "stratified_z": rnd(z), "calendar": is_calendar(t),
                     "_z": z if z is not None else 0.0})
    by_channels = sorted(rows, key=lambda r: (-r["channels_now"], -r["count_now"], r["term"]))
    rising = sorted((r for r in rows if r["channels_now"] >= max(3, opts.min_channels) and r["_z"] > Z),
                    key=lambda r: (-r["_z"], r["term"]))
    strip = [{k: v for k, v in r.items() if k != "_z"} for r in by_channels[:opts.json_top]]
    tier_items = sum(t.items for t in tiers.values())
    hist_items = sum(h.items for h in hists.values())
    bo = {}
    for g in ("strong", "weak"):
        k1 = sum(getattr(t, g) for t in tiers.values())
        k2 = sum(getattr(h, g) for h in hists.values())
        rise, two = fisher(k1, tier_items, k2, hist_items)
        rates_now = [getattr(tiers[ch], g) / tiers[ch].items for ch in chs]
        rates_before = [getattr(h, g) / h.items for h in hists.values()]
        sz = stratified_z([(getattr(tiers[ch], g), tiers[ch].items, getattr(h, g), h.items) for ch, h in hists.items()])
        bo[g] = {"tier": k1, "history": k2, "tier_per100": per100(k1, tier_items),
                 "history_per100": per100(k2, hist_items), "stratified_z": rnd(sz, 3),
                 "channel_mean_tier_per100": rnd(100 * sum(rates_now) / len(rates_now), 2),
                 "channel_mean_history_per100": rnd(100 * sum(rates_before) / len(rates_before), 2) if rates_before else None,
                 "fisher_p_rise": rnd(rise), "fisher_p_two_sided": rnd(two),
                 "channels_matching_now": sum(1 for t in tiers.values() if getattr(t, g)),
                 "channels_matching_before": sum(1 for h in hists.values() if getattr(h, g)),
                 "channels_rose": sorted(ch for ch, h in hists.items()
                                         if getattr(tiers[ch], g) / tiers[ch].items > getattr(h, g) / h.items)}
    return {"channels": len(chs), "channels_with_history": len(hists), "tier_items": tier_items,
            "history_items": hist_items,
            "tier_sentences_dropped": sum(t.units_dropped for t in tiers.values()),
            "history_sentences_dropped": sum(h.units_dropped for h in hists.values()),
            "tier_tokens": sum(t.tokens_n() for t in tiers.values()),
            "history_tokens": sum(h.tokens_n() for h in hists.values()),
            "terms_by_channels": strip,
            "rising_across": [{k: v for k, v in r.items() if k != "_z"} for r in rising[:opts.json_top]],
            "blackouts": bo}


# ---------------------------------------------------------------------------------------------------- outputs
# rising_significant and falling_significant count the terms other than dates; the _calendar columns the dates;
# both are blank when the kind has no history, or a text kind's tier has fewer than --min-text-tokens tokens
COUNT_FIELDS = ["scope", "channel", "kind", "tier_items", "history_items", "tier_tokens", "history_tokens",
                "tier_terms", "history_terms", "rising_significant", "rising_significant_calendar",
                "falling_significant", "falling_significant_calendar",
                "tier_blackout_strong", "history_blackout_strong", "tier_strong_per100", "history_strong_per100",
                "strong_fisher_p_rise", "tier_blackout_weak", "history_blackout_weak", "tier_weak_per100",
                "history_weak_per100", "weak_fisher_p_rise"]


def count_rows(result):
    """Counts per channel and kind: no terms, no titles, no ids."""
    rows = []
    for ch in sorted(result["channels"]):
        for kind in KINDS:
            v = result["channels"][ch].get(kind)
            if not v:
                continue
            b = v["blackouts"]
            rows.append({"scope": result["scope"], "channel": ch, "kind": kind,
                         **{k: v[k] for k in ("tier_items", "history_items", "tier_tokens", "history_tokens",
                                              "tier_terms", "history_terms")},
                         **{k: v.get(k, "") for k in ("rising_significant", "rising_significant_calendar",
                                                      "falling_significant", "falling_significant_calendar")},
                         "tier_blackout_strong": b["strong"]["tier"], "history_blackout_strong": b["strong"]["history"],
                         "tier_strong_per100": b["strong"]["tier_per100"],
                         "history_strong_per100": "" if b["strong"]["history_per100"] is None else b["strong"]["history_per100"],
                         "strong_fisher_p_rise": "" if b["strong"]["fisher_p_rise"] is None else b["strong"]["fisher_p_rise"],
                         "tier_blackout_weak": b["weak"]["tier"], "history_blackout_weak": b["weak"]["history"],
                         "tier_weak_per100": b["weak"]["tier_per100"],
                         "history_weak_per100": "" if b["weak"]["history_per100"] is None else b["weak"]["history_per100"],
                         "weak_fisher_p_rise": "" if b["weak"]["fisher_p_rise"] is None else b["weak"]["fisher_p_rise"]})
    return rows


def _cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def _fmt(x, nd=2):
    return "–" if x is None or x == "" else (f"{x:.{nd}f}" if isinstance(x, float) else f"{x:,}" if isinstance(x, int) else str(x))


def channel_md(ch, scope, views, opts, lexicon_source):
    lines = [f"# Keywords: {ch}, {scope}", "",
             f"Made by pipeline/keywords.py. Private: terms, titles and quotes (at most 30 words) from the stored "
             f"titles and texts. Kinds apart. Blackout lexicon: {lexicon_source}.", ""]
    n = opts.top
    for kind in KINDS:
        v = views.get(kind)
        if not v:
            continue
        unit = "titles" if kind == "titles" else "texts"
        lines += [f"## {KIND_NAMES[kind][:1].upper() + KIND_NAMES[kind][1:]}", "",
                  f"{v['tier_items']:,} {unit} in {scope}, {v['history_items']:,} in the channel's history. Tokens after "
                  f"stopwords and the channel's name{' and title furniture' if kind == 'titles' else ''}: "
                  f"{v['tier_tokens']:,} now, {v['history_tokens']:,} before; {v['tier_terms']:,} distinct terms now.", ""]
        if kind == "titles":
            furn = ", ".join(f"{t} ({100 * s:.0f}%)" for t, s in sorted(v["furniture"].items(), key=lambda x: (-x[1], x[0])))
            lines += [f"Title furniture dropped (in more than {100 * opts.furniture_share:.0f}% of the titles): "
                      f"{furn or 'none'}.", ""]
        else:
            lines += [f"Sentences left out as page furniture, promotion or editors' notes: "
                      f"{v['tier_sentences_dropped']:,} now (kept {v['tier_sentences']:,}), "
                      f"{v['history_sentences_dropped']:,} before (kept {v['history_sentences']:,}).", ""]
        lines += [f"### Distinctive now (TF-IDF over the channels' {scope} {unit})", "",
                  f"\"series?\": in more than half of the {unit} now, perhaps a new series' name.", "",
                  "| Term | Count now | Channels using it now | TF-IDF | |", "|---|---:|---:|---:|---|"]
        lines += [f"| {_cell(r['term'])} | {r['count']} | {r['channels']} | {r['weight']:.3f} | "
                  f"{'series?' if kind == 'titles' and (r.get('tier_item_share') or 0) > 0.5 else ''} |"
                  for r in v["tfidf"][:n]]

        def flags(r):
            return ", ".join(x for x, on in (("significant", r["significant"]), ("date", r.get("calendar"))) if on)
        if "rising" in v:
            scale = ", ".join(f"{k} {x:g}" for k, x in sorted(v.get("prior_scale", {}).items()))
            lines += ["", "### New against its own history (log-odds with an informative Dirichlet prior)", "",
                      f"Prior: the channel's own pooled rate, a0 = {scale}. {v['rising_significant']} terms "
                      f"significantly more frequent now and {v['falling_significant']} less, besides "
                      f"{v['rising_significant_calendar']} and {v['falling_significant_calendar']} dates (|z| > 1.96, "
                      f"at least {opts.min_significant_count} times on their side); after Benjamini-Hochberg (q = .05, "
                      f"{v['bh_family']:,} terms): {v['rising_bh']} and {v['falling_bh']}.", "",
                      "| Rising | Now | Before | Per 1,000 now | Per 1,000 before | z | |", "|---|---:|---:|---:|---:|---:|---|"]
            lines += [f"| {_cell(r['term'])} | {r['now']} | {r['before']} | {r['per1000_now']:.2f} | "
                      f"{r['per1000_before']:.2f} | {r['z']:.2f} | {flags(r)} |"
                      for r in v["rising"][:n]]
            lines += ["", "| Falling | Now | Before | Per 1,000 now | Per 1,000 before | z | |",
                      "|---|---:|---:|---:|---:|---:|---|"]
            lines += [f"| {_cell(r['term'])} | {r['now']} | {r['before']} | {r['per1000_now']:.2f} | "
                      f"{r['per1000_before']:.2f} | {r['z']:.2f} | {flags(r)} |"
                      for r in v["falling"][:max(10, n // 2)]]
        elif v.get("log_odds_skipped"):
            lines += ["", f"No comparison with the history: {v['log_odds_skipped']}."]
        else:
            lines += ["", "No history of this kind: no comparison."]
        b = v["blackouts"]
        lines += ["", "### Blackouts", "",
                  f"A {unit[:-1]} that matches both groups counts in both.", "",
                  f"| Group | Now | Per 100 now | Before | Per 100 before | Fisher p (rise) | z |",
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for g in ("strong", "weak"):
            x = b[g]
            lines.append(f"| {g} | {x['tier']} of {b['tier_items']:,} | {_fmt(x['tier_per100'])} | {x['history']} of "
                         f"{b['history_items']:,} | {_fmt(x['history_per100'])} | {_fmt(x['fisher_p_rise'], 3)} | "
                         f"{_fmt(x['z'])} |")
        if b["tier_matches"]:
            lines += ["", "Matching now:"]
            for m in b["tier_matches"]:
                what = m["label"] if kind == "titles" else " / ".join(u["quote"] for u in m["units"][:2])
                lines.append(f"- {m['item']} ({', '.join(m['groups'])}: {', '.join(m['ids'])}): {_cell(what)}")
        if b["history_matches"]:
            lines += ["", f"Matching before ({len(b['history_matches'])}; the first {min(15, len(b['history_matches']))}):"]
            for m in b["history_matches"][:15]:
                what = f": {_cell(m['label'])}" if m.get("label") else ""
                lines.append(f"- {m['item']} ({', '.join(m['groups'])}: {', '.join(m['ids'])}){what}")
        lines.append("")
    return "\n".join(lines) + "\n"


def summary_md(result, opts, lexicon_source):
    scope = result["scope"]
    lines = [f"# Keywords across channels: {scope}", "",
             f"Made by pipeline/keywords.py. Private: terms and titles. Kinds apart. History tabs: "
             f"{', '.join(result['history_tabs']) if isinstance(result['history_tabs'], list) else 'all'}. "
             f"Per channel, the log-odds prior is the channel's own pooled rate (a0 "
             f"{'= the tier' + chr(39) + 's own token count' if opts.prior_scale == 'tier' else opts.prior_scale}); significance "
             f"|z| > 1.96 with at least {opts.min_significant_count} occurrences. Across channels the z is the "
             f"Mantel-Haenszel z over the channels' tables of items, each channel against its own history. Terms "
             f"listed here are used now by at least {opts.min_channels} channels; \"date\" marks years, months and "
             f"weekdays. Blackout lexicon: {lexicon_source}.", ""]
    for kind in KINDS:
        k = result["kinds"].get(kind)
        if not k:
            continue
        unit = "titles" if kind == "titles" else "texts"
        lines += [f"## {KIND_NAMES[kind][:1].upper() + KIND_NAMES[kind][1:]}", "",
                  f"{k['channels']} channels ({k['channels_with_history']} with a history of this kind): "
                  f"{k['tier_items']:,} {unit} now, {k['history_items']:,} before; {k['tier_tokens']:,} and "
                  f"{k['history_tokens']:,} tokens." + (
                      "" if kind == "titles" else
                      f" Sentences left out as page furniture, promotion or editors' notes: "
                      f"{k['tier_sentences_dropped']:,} now, {k['history_sentences_dropped']:,} before."), "",
                  "### Used by most channels now", "",
                  f"| Term | Channels now (of {k['channels']}) | Channels before | Mean share of a channel's {unit} now, % | "
                  f"before, % | Channels up / down | Stratified z | |", "|---|---:|---:|---:|---:|---|---:|---|"]
        for r in k["terms_by_channels"][:opts.top * 2]:
            lines.append(f"| {_cell(r['term'])} | {r['channels_now']} | {r['channels_before']} | {_fmt(r['share_now_pct'])} | "
                         f"{_fmt(r['share_before_pct'])} | {r['channels_up']} / {r['channels_down']} | "
                         f"{_fmt(r['stratified_z'])} | {'date' if r.get('calendar') else ''} |")
        lines += ["", "### Rising across channels (stratified z > 1.96, used now by at least 3 channels)", "",
                  "| Term | Channels now | Mean share now, % | before, % | Channels up / down | Stratified z | |",
                  "|---|---:|---:|---:|---|---:|---|"]
        for r in k["rising_across"][:opts.top]:
            lines.append(f"| {_cell(r['term'])} | {r['channels_now']} | {_fmt(r['share_now_pct'])} | "
                         f"{_fmt(r['share_before_pct'])} | {r['channels_up']} / {r['channels_down']} | "
                         f"{_fmt(r['stratified_z'])} | {'date' if r.get('calendar') else ''} |")
        lines += ["", f"### Blackouts in {unit}", "", f"A {unit[:-1]} that matches both groups counts in both.", ""]
        for g in ("strong", "weak"):
            x = k["blackouts"][g]
            lines.append(f"- {g}: {x['tier']} of {k['tier_items']:,} {unit} now ({_fmt(x['tier_per100'])} per 100; "
                         f"channel mean {_fmt(x['channel_mean_tier_per100'])}) against {x['history']} of "
                         f"{k['history_items']:,} before ({_fmt(x['history_per100'])}; channel mean "
                         f"{_fmt(x['channel_mean_history_per100'])}); Fisher p (rise) {_fmt(x['fisher_p_rise'], 4)}; "
                         f"stratified z {_fmt(x['stratified_z'])}. "
                         f"Channels matching now {x['channels_matching_now']}, before {x['channels_matching_before']}; "
                         f"share rose in {len(x['channels_rose'])}: {', '.join(x['channels_rose']) or 'none'}.")
        lines += ["", "| Channel | Strong now | per 100 | Strong before | per 100 | p (rise) | Weak now | per 100 | "
                      "Weak before | per 100 | p (rise) |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for ch in sorted(result["channels"]):
            v = result["channels"][ch].get(kind)
            if not v:
                continue
            b = v["blackouts"]
            if not (b["strong"]["tier"] or b["strong"]["history"] or b["weak"]["tier"] or b["weak"]["history"]):
                continue
            cells = []
            for g in ("strong", "weak"):
                x = b[g]
                flag = " ↑" if x["rose"] else ""
                cells.append(f"{x['tier']}{flag} | {_fmt(x['tier_per100'])} | {x['history']} | {_fmt(x['history_per100'])} | "
                             f"{_fmt(x['fisher_p_rise'], 3)}")
            lines.append(f"| {ch} | " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_outputs(result, out, opts, lexicon, inputs):
    out.mkdir(parents=True, exist_ok=True)
    for ch, views in sorted(result["channels"].items()):
        atomic_write_text(out / f"{ch}.md", channel_md(ch, result["scope"], views, opts, lexicon.source))
    atomic_write_text(out / "summary.md", summary_md(result, opts, lexicon.source))
    params = {k: getattr(opts, k) for k in ("min_count", "min_significant_count", "min_channels", "prior_scale",
                                            "furniture_share", "furniture_min_titles", "history_tabs", "json_top",
                                            "keep_furniture", "min_text_tokens", "weak_below_precision")}
    params["prior"] = "the channel's own pooled rate of the kind (tier and history)"
    payload = {"scope": result["scope"], "parameters": params, "history_tabs_used": result["history_tabs"],
               "inputs": inputs, "lexicon": lexicon.describe(),
               "kinds": result["kinds"], "channels": result["channels"]}
    atomic_write_text(out / "keywords.json", json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=1) + "\n")
    rows = count_rows(result)
    write_csv(out / "counts.csv", rows, COUNT_FIELDS)
    return rows


def read_names(path=TARGETS):
    if not Path(path).exists():
        return {}
    return {r["person_id"]: (r.get("person_name") or "", r.get("role") or "") for r in read_csv(path)}


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--scope", default="newest10", help="the tier's name (default newest10)")
    ap.add_argument("--queue", help="the tier's queue (default jobs/queue_<scope>.csv; relative to --root)")
    ap.add_argument("--history", default="jobs/queue_youtube_all.csv",
                    help="the whole listing; the tier is taken out of it (relative to --root)")
    ap.add_argument("--catalog", default="catalog/catalog.csv", help="the catalogue (relative to --root)")
    ap.add_argument("--lexicon", type=Path, default=LEXICON,
                    help="the blackout theme file (default pipeline/themes/blackouts.json; a built-in list without it)")
    ap.add_argument("--kinds", default=",".join(KINDS), help="titles, source, made, captions")
    ap.add_argument("--only", help="comma-separated channels")
    ap.add_argument("--history-tabs", default="tier",
                    help="listing tabs in the history: tier (default: the tabs the tier has), all, or e.g. videos,streams")
    ap.add_argument("--min-count", type=int, default=1, help="least count on its side for a term to be listed")
    ap.add_argument("--min-significant-count", type=int, default=2,
                    help="least count on its side for a term to be called significant (default 2)")
    ap.add_argument("--min-channels", type=int, default=2, help="least channels using a term now for the cross-channel list")
    ap.add_argument("--prior-scale", default="tier",
                    help="a0, the prior's pseudo-counts: tier (default: the tier's own token count) or a number")
    ap.add_argument("--min-text-tokens", type=int, default=500,
                    help="least tokens in a text kind's tier for the log-odds test (default 500; titles always tested)")
    ap.add_argument("--weak-below-precision", type=float, default=None,
                    help="a theme file's include with a measured precision below this counts as weak (default off)")
    ap.add_argument("--furniture-share", type=float, default=0.5)
    ap.add_argument("--furniture-min-titles", type=int, default=10)
    ap.add_argument("--keep-furniture", action="store_true",
                    help="keep the texts' sentences that the prediction timeline's filters call page furniture, "
                         "promotion or editors' notes (left out by default)")
    ap.add_argument("--top", type=int, default=25, help="rows per table in the .md files")
    ap.add_argument("--json-top", type=int, default=200, help="rows per list in keywords.json")
    ap.add_argument("--out", type=Path, help="default <root>/analysis/keywords/<scope>")
    ap.add_argument("--publish-counts", action="store_true", help="also copy counts.csv to plan/keywords_<scope>.csv")
    ap.add_argument("--plan-dir", type=Path, default=ET_ROOT / "plan", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    args.kinds = [k.strip() for k in args.kinds.split(",") if k.strip()]
    args.only = [x.strip() for x in (args.only or "").split(",") if x.strip()]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.scope):
        ap.error("--scope: letters, digits, - and _ only")
    if args.prior_scale != "tier":
        try:
            if float(args.prior_scale) <= 0:
                raise ValueError
        except ValueError:
            ap.error("--prior-scale: tier or a positive number")
    return args


def main(argv=None):
    args = parse_args(argv)
    root = Path(args.root)
    out = ensure_outside_git(args.out or root / "analysis" / "keywords" / args.scope)
    queue = resolve(root, args.queue or f"jobs/queue_{args.scope}.csv")
    history = resolve(root, args.history)
    catalog = resolve(root, args.catalog)
    lexicon = load_lexicon(args.lexicon, args.weak_below_precision)
    tier_rows, history_rows = read_csv(queue), read_csv(history)
    catalogue = read_csv(catalog) if catalog.exists() else []
    inputs = {"queue": {"path": queue.name, "sha256": sha256_file(queue), "rows": len(tier_rows)},
              "history": {"path": history.name, "sha256": sha256_file(history), "rows": len(history_rows)},
              "catalog": {"path": catalog.name, "sha256": sha256_file(catalog) if catalog.exists() else "",
                          "rows": len(catalogue)},
              "lexicon": {"source": lexicon.source,
                          "sha256": sha256_file(args.lexicon) if lexicon.source == str(args.lexicon) else ""}}
    result = analyse(root, args.scope, tier_rows, history_rows, catalogue, lexicon, args, read_names())
    rows = write_outputs(result, out, args, lexicon, inputs)
    if args.publish_counts:
        args.plan_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out / "counts.csv", args.plan_dir / f"keywords_{args.scope}.csv")
    t = result["kinds"].get("titles", {})
    texts = ", ".join(f"{k} {v['tier_items']} now / {v['history_items']} before ({v['channels']} channels)"
                      for k, v in result["kinds"].items() if k != "titles") or "no texts"
    print(f"{args.scope}: {t.get('channels', 0)} channels, {t.get('tier_items', 0)} titles now and "
          f"{t.get('history_items', 0)} before; texts: {texts}; {len(rows)} count rows -> {out}")
    return result


if __name__ == "__main__":
    main()
