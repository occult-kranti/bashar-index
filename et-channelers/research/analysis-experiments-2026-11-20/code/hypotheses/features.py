"""Per-unit timing and word features (H1, H4) and per-recording token counts (H9), joined to the voice label units.

The label files hold no time stamps and no words (produce.light drops them). The analysis therefore needs, per unit of
the voice label file, what the transcript gives: start and end time, estimated syllables, letters, inter-word pauses, and
the contracted and full members of H4's closed list (prep.contractible_pairs, the pairs the contraction-neutral table
rewrites, R12); and per recording the token counts of H9. The functions below compute these from a word list
({"t", "start", "end"}) and the units of prep.build_units, so that unit ids match the label files.

Opening transcripts goes through prep.load_units, whose hold-out guard (R20) refuses every creator outside the seen group
unless produce.py has checked freeze 1. The command below additionally refuses any group but "seen". Feature files of
hold-out recordings must be written by a step that the guard admits after freeze 2 (README, open items). The command was
run on the seen transcripts only (features-2, features-3 and features-4, 2026-11-21; the private features note records
the runs).

    python -I features.py seen OUTDIR [--names NAMES.json] [--families FAMILIES.json]
"""
import json
from pathlib import Path
import re
import sys

try:
    from . import wording
except ImportError:                                  # run as a script: python -I features.py seen OUTDIR
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from hypotheses import wording                   # noqa: E402

# features-2 (2026-11-21): each unit also carries "self_name", the fallback self-naming flag of H5's exclusion
# (registry 02:50, M9; constants.SELF_NAMING_PATTERNS), used only where a voice label file carries no cue
# features-3 (2026-11-21, registry 11:08 (3)): h9_counts counts a contraction whose parts are function words as those
# function words (h9_parts), and tests the function-word list on the same form that keys a content word; the units are
# unchanged. The names input of the seen run also holds every token of every family variant (registry 11:08 (2)).
# features-4 (2026-11-21, registry 12:52 (3)): h9_parts also splits ain't (is + not, one of its function-word readings in
# prep.contractible_pairs) and y'all (you + all) into function words; the units and every other token are unchanged.
FEATURE_VERSION = "features-4"
VOWELS = re.compile(r"[aeiouy]+")
TOKEN = re.compile(r"[A-Za-z][A-Za-z'’]*")
FP_SING = ("i", "me", "my", "mine", "myself")
FP_PLUR = ("we", "us", "our", "ours", "ourselves")
HEDGE_WORDS = ("maybe", "perhaps", "probably", "possibly", "might", "may", "could", "seems", "somewhat", "apparently")
HEDGE_PHRASES = ("i think", "i believe", "i guess", "kind of", "sort of", "i feel like")
# Closed list of English function words for H9's style representation (CHOICE: pronouns, determiners, prepositions,
# conjunctions, auxiliaries and common adverbs; frozen with the code).
FUNCTION_WORDS = tuple(sorted(set("""
a about above after again against all am an and any are as at be because been before being below between both but by can
cannot could did do does doing down during each few for from further had has have having he her here hers herself him
himself his how i if in into is it its itself just me more most my myself no nor not now of off on once only or other our
ours ourselves out over own same she should so some such than that the their theirs them themselves then there these they
this those through to too under until up very was we were what when where which while who whom why will with would you
your yours yourself yourselves also however although though yet still even ever never always often again already rather
quite much many every either neither whether upon within without toward towards across around among along
""".split())))
NOT_NAMES = {"i", "the", "a", "an", "and", "but", "or", "so", "if", "then", "yes", "no", "oh", "well", "now", "okay", "ok"}
# H9's reading of a clitic after an apostrophe (h9_parts; registry 11:08 (3), CHOICE 9): one full form each. 's can also
# stand for "has" or a possessive and 'd for "had"; all are function words, so the reading decides only which function
# word is counted, never whether a token is a content word.
CLITICS = {"s": "is", "re": "are", "m": "am", "ve": "have", "ll": "will", "d": "would"}
# can't, won't, ain't: the host before n't is written differently. prep.contractible_pairs reads ain't as am, are, is, have
# or has not, all function words; h9_parts gives it one reading, "is not", prep.neutral's reading where no subject or
# participle decides (features-4, registry 12:52 (3)). Like 's and 'd, the reading chooses only which function word counts.
NEGATIVE_HOSTS = {"ca": "can", "wo": "will", "ai": "is"}
# A spelled host and its first clitic that read as two function words together (features-4, registry 12:52 (3)): y'all is
# "you all", its full form in prep.contractible_pairs (prep.SPECIAL).
JOINED = {("y", "all"): ("you", "all")}


# ---------------------------------------------------------------- words

def syllables(text):
    """Estimated syllables of one word as transcribed (CHOICE): vowel groups, a silent final e removed, at least one for a
    word with letters; one per digit for numbers written in digits. The registry asks for a check on HR excerpts, with
    words and letters per minute as sensitivity rows (H1 does both)."""
    lower = text.lower()
    letters = re.sub(r"[^a-z]", "", lower)
    digits = len(re.findall(r"\d", lower))
    if not letters:
        return digits
    groups = len(VOWELS.findall(letters))
    if letters.endswith("e") and not letters.endswith(("le", "ee", "ye")) and groups > 1:
        groups -= 1
    elif letters.endswith("ed") and not letters.endswith(("ted", "ded")) and groups > 1:
        groups -= 1                                  # a silent -ed: "loved", "channelled"
    return max(1, groups) + digits


def letters(text):
    return sum(character.isalpha() for character in text)


def tokens(text):
    return [token.lower().replace("’", "'") for token in TOKEN.findall(text)]


# ---------------------------------------------------------------- H4's closed list

def contraction_patterns(pairs):
    """Regular expressions for the contracted and the full members of the closed list of pairs."""
    contracted = sorted({pair[0] for pair in pairs}, key=len, reverse=True)
    full = sorted({pair[1] for pair in pairs}, key=len, reverse=True)
    form = lambda text: re.escape(text).replace("'", "['’]").replace(r"\ ", r"\s+")
    return (re.compile(r"(?<!\w)(?:" + "|".join(form(item) for item in contracted) + r")(?!\w)", re.I),
            re.compile(r"(?<![\w'’])(?:" + "|".join(form(item) for item in full) + r")(?![\w'’])", re.I))


def contraction_counts(text, patterns):
    """(contracted, full) members of the closed list in a text. Full forms are counted as non-overlapping leftmost-longest
    matches, so "it is not" counts once (CHOICE)."""
    contracted, full = patterns
    return len(contracted.findall(text)), len(full.findall(text))


# ---------------------------------------------------------------- units

def unit_features(words, units, patterns, pause_seconds=0.25):
    out = []
    for unit in units:
        span = words[unit["first"]:unit["last"] + 1]
        text = " ".join(word["t"] for word in span)
        toks = tokens(text)
        gaps = sum(max(0.0, b["start"] - a["end"]) for a, b in zip(span, span[1:]) if b["start"] - a["end"] >= pause_seconds)
        c, f = contraction_counts(text, patterns)
        joined = " " + " ".join(toks) + " "
        out.append({"id": unit["id"], "start": span[0]["start"], "end": span[-1]["end"], "words": len(span),
                    "syllables": sum(syllables(word["t"]) for word in span), "letters": sum(letters(word["t"]) for word in span),
                    "pauses": round(gaps, 3), "contracted": c, "full": f,
                    "fp_sing": sum(token.split("'")[0] in FP_SING for token in toks),
                    "fp_plur": sum(token.split("'")[0] in FP_PLUR for token in toks),
                    "hedges": sum(token in HEDGE_WORDS for token in toks) + sum(joined.count(" " + phrase + " ") for phrase in HEDGE_PHRASES),
                    "self_name": bool(wording.self_naming(text))})
    return out


# ---------------------------------------------------------------- H9

def capitalised_only(words):
    """Words that the recording writes only with a capital and never in lower case: masked as names (CHOICE, after
    prep.mask_names)."""
    seen_lower, seen_upper = set(), set()
    for word in words:
        for token in TOKEN.findall(word["t"]):
            base = token.split("'")[0].split("’")[0]
            (seen_upper if base[:1].isupper() else seen_lower).add(base.lower())
    return {token for token in seen_upper - seen_lower if token not in NOT_NAMES}


def h9_mask_forms(list_forms, families):
    """The names input of h9_counts (registry 2026-11-21 11:08 (2)): the list forms as given (the NAMES v2 list forms)
    and every token of every variant of the family table ({code: [variants]}), each token as `tokens` writes it with its
    apostrophes removed (the form h9_counts compares), as one sorted list without repeats. Tokens that are function words
    or have fewer than three letters are kept; h9_counts never counts them as content words in any case."""
    forms = set(list_forms)
    for variants in families.values():
        for variant in variants:
            forms.update(token.replace("'", "") for token in tokens(variant))
    return sorted(forms)


def formula_ngrams(token_lists, n=4, share=0.5):
    """Word n-grams that occur in at least `share` of a creator's recordings (two or more): the creator's formulas."""
    if len(token_lists) < 2:
        return set()
    counts = {}
    for toks in token_lists:
        for gram in {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}:
            counts[gram] = counts.get(gram, 0) + 1
    need = max(2, share * len(token_lists))
    return {gram for gram, count in counts.items() if count >= need}


def h9_parts(token):
    """The forms under which h9_counts counts one token of `tokens` (features-3 and features-4; registry 2026-11-21 11:08
    (3) and 12:52 (3), CHOICE 9).

    The exact rule:
    1. A token without an apostrophe is one form, itself.
    2. A token with apostrophes is cut at each apostrophe into a host (the part before the first) and clitics (the parts
       after). If the first clitic is "t" and the host ends in "n", the two are n't: the host loses that final "n"
       ("don" -> "do", "isn" -> "is", "couldn" -> "could"), the stems "ca", "wo" and "ai" become "can", "will" and "is"
       (can't, won't, ain't), and n't reads "not". If the host and the first clitic are a pair of JOINED, the two read as
       its two words (y'all: "you", "all"). Every other clitic reads as its full form in CLITICS: 's "is", 're "are",
       'm "am", 've "have", 'll "will", 'd "would"; an empty or other clitic has no reading.
    3. If the host and every reading are function words (FUNCTION_WORDS), the token is those function words, in order:
       "it's" -> it, is; "we're" -> we, are; "i'm" -> i, am; "you'll" -> you, will; "don't" -> do, not; "won't" -> will,
       not; "ain't" -> is, not; "y'all" -> you, all; "i'd've" -> i, would, have. A contraction then counts as its full form
       does ("it's" as "it is", "y'all" as "you all").
    4. Otherwise the token is one form, the token without its apostrophes ("god's" -> gods, "let's" -> lets, "might've" ->
       mightve, "shan't" -> shant: "let", "might" and "shall" are not on the list). This same form is the one h9_counts
       tests against FUNCTION_WORDS, the mask and the length rule, and the content key.
    `tokens` has already lower-cased the token and written a curly apostrophe as "'"."""
    if "'" not in token:
        return [token]
    host, *clitics = token.split("'")
    if clitics[0] == "t" and host.endswith("n"):
        stem = host[:-1]
        parts = [NEGATIVE_HOSTS.get(stem, stem), "not"]
        clitics = clitics[1:]
    elif (host, clitics[0]) in JOINED:
        parts = list(JOINED[(host, clitics[0])])
        clitics = clitics[1:]
    else:
        parts = [host]
    parts += [CLITICS.get(clitic, "") for clitic in clitics]
    if all(part in FUNCTION_WORDS for part in parts):
        return parts
    return [token.replace("'", "")]


def h9_counts(words, masked, formulas, families=None, n=4, head=400, tail=200):
    """Token counts of one recording: function words, content words (at least three letters, not masked, not inside a
    formula n-gram), the rest; and per family whether a name variant occurs in the first `head` or last `tail` running
    words (the opening-formula rule of the title protocol).

    Each running token is read through h9_parts (features-3; features-4 adds ain't and y'all). A contraction whose parts
    are all function words adds one count to each of them ("it's" adds "it" and "is", so the recording's token total
    counts it as two words, as "it is").
    Any other token is one form, the token without its apostrophes: it is a function word if that form is on
    FUNCTION_WORDS; else it is "other" if it lies inside a formula n-gram, or that form or the part of the token before its
    first apostrophe is in `masked`, or the form has fewer than three letters; else that form is its content key. So the
    function-word test and the content key use the same form, and no function word is a content key. Function words are
    counted before the mask and the formula test, as before. `masked` holds lower-case forms as `tokens` writes them: for
    the seen run the names input (registry 11:08 (2): the NAMES v2 list forms and every token of every variant of the
    frozen family table, apostrophes removed) and the recording's capitalised_only words."""
    toks = tokens(" ".join(word["t"] for word in words))
    inside = [False] * len(toks)
    for i in range(len(toks) - n + 1):
        if tuple(toks[i:i + n]) in formulas:
            for j in range(i, i + n):
                inside[j] = True
    content, function, other = {}, {}, 0
    for token, covered in zip(toks, inside):
        parts = h9_parts(token)
        form = parts[0]
        if len(parts) > 1 or form in FUNCTION_WORDS:
            for part in parts:
                function[part] = function.get(part, 0) + 1
        elif covered or form in masked or token.split("'")[0] in masked or len(form) < 3:
            other += 1
        else:
            content[form] = content.get(form, 0) + 1
    edges = " " + " ".join(toks[:head] + toks[-tail:]) + " "
    matches = {}
    for family, variants in sorted((families or {}).items()):
        matches[family] = any(" " + " ".join(tokens(variant)) + " " in edges for variant in variants if tokens(variant))
    return {"content": content, "function": function, "other": other, "opening_family_match": matches}


# ---------------------------------------------------------------- command (seen creators only; not run for this track)

def _prep():
    llm = Path.home() / "et-channelers-private" / "provisioning" / "claude-cohort-asr-20261120-v1" / "llm"
    sys.path.insert(0, str(llm))
    import prep                                                    # noqa: E402  (its guard refuses non-seen transcripts)
    return prep


def main(argv):
    if len(argv) < 2 or argv[0] != "seen":
        raise SystemExit(__doc__)
    prep = _prep()
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    names = set(json.loads(Path(argv[argv.index("--names") + 1]).read_text(encoding="utf-8"))) if "--names" in argv else set()
    families = json.loads(Path(argv[argv.index("--families") + 1]).read_text(encoding="utf-8")) if "--families" in argv else {}
    patterns = contraction_patterns(prep.contractible_pairs())
    rows = [row for row in prep.recordings() if row["group"] == "seen" and row.get("language") in ("en", None)]
    by_creator = {}
    for row in rows:
        by_creator.setdefault(row["creator"], []).append(row)
    for creator in sorted(by_creator):
        loaded = []
        for row in sorted(by_creator[creator], key=lambda item: item["audio"]):
            if row["group"] != "seen":
                raise PermissionError("features.py writes seen creators only")
            info, words, units = prep.load_units(row)
            if info["language"] == "en":
                loaded.append((row, words, units, info.get("model_role")))
        formulas = formula_ngrams([tokens(" ".join(word["t"] for word in words)) for _, words, _, _ in loaded])
        for row, words, units, model in loaded:
            record = {"audio": row["audio"], "creator": creator, "group": "seen", "feature_version": FEATURE_VERSION,
                      "asr_model": model,                       # the bundle's recognizer role (ASR-model rule, adapter)
                      "units": unit_features(words, units, patterns),
                      "h9": h9_counts(words, names | capitalised_only(words), formulas, families)}
            (out / (row["audio"] + ".json")).write_text(json.dumps(record), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
