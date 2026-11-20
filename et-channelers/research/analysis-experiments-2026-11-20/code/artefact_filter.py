"""Artefact filter, version 1: removes text the speech recognizer appears to invent (rule R5 of the catalogue).

The rules come from the reading of 42 transcripts on 2026-11-20. Their precision and recall have not been
measured against listening. Every result is reported with and without this filter.

A segment is a dict with start, end, text, avg_logprob and words (each word: start, end, word).
"""
import re

WINDOW = 30.0                      # the worker decodes fixed, non-overlapping 30-second windows
THANKS = {"thank you"}
STOCK = {"thank you for watching", "thanks for watching", "see ya", "i'm going to do", "you're going to be"}
CREDIT = re.compile(r"subtitles? by|subtitled by|captions? by|amara\.org|www\.|https?:|\.com\b", re.I)
VERSION = "artefact-filter-v1"


def plain(text):
    """Lower case, apostrophes straightened, punctuation dropped, spaces collapsed."""
    text = text.lower().replace("’", "'").replace("‘", "'")
    return " ".join(re.sub(r"[^a-z0-9' ]+", " ", text).split())


def collapse(words):
    """Drop immediate repeats of the same unit of 1 to 8 words beyond the third occurrence (recognizer loops)."""
    kept, tokens = [], []
    for word in words:
        token = plain(word["word"])
        kept.append(word)
        tokens.append(token)
        for size in range(1, 9):
            if len(tokens) >= 4 * size and tokens[-size:] == tokens[-2 * size:-size] == tokens[-3 * size:-2 * size] == tokens[-4 * size:-3 * size]:
                del kept[-size:]
                del tokens[-size:]
                break
    return kept


def clean(segments, duration):
    """Return (kept segments with their words collapsed, counts of what each rule removed)."""
    removed = {"thanks_inserted": 0, "isolated_short": 0, "stock_text": 0, "repeated_segment": 0, "looped_words": 0}
    kept, run_text, run_length = [], None, 0
    for index, part in enumerate(segments):
        text = plain(part.get("text", ""))
        words = part.get("words") or []
        before = part["start"] - (segments[index - 1]["end"] if index else 0.0)
        after = (segments[index + 1]["start"] if index + 1 < len(segments) else duration) - part["end"]
        isolated = before >= 5.0 and after >= 5.0
        if text in THANKS and (part["start"] % WINDOW > 27.0 or (part.get("avg_logprob") or 0.0) < -0.5 or isolated):
            removed["thanks_inserted"] += 1
            continue
        if isolated and len(text.split()) <= 3:
            removed["isolated_short"] += 1
            continue
        if text in STOCK or (len(text.split()) <= 8 and CREDIT.search(part.get("text", ""))):
            removed["stock_text"] += 1
            continue
        run_length = run_length + 1 if text and text == run_text else 1
        run_text = text
        if run_length > 3:
            removed["repeated_segment"] += 1
            continue
        collapsed = collapse(words)
        removed["looped_words"] += len(words) - len(collapsed)
        kept.append({**part, "words": collapsed})
    return kept, removed
