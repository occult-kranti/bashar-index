"""Fixed wording rules (registry, lead's decisions of 2026-11-21 02:50, meta-review M9). Pure functions: a string goes in,
pattern ids come out. No text is kept, printed or returned; the callers (adapter.py, features.py) store only the ids.

  shared_wording(text)  H2: the scenario and withdrawal wording that both the checkability codebook (forecasts_fc.txt,
                        observable_outcome NO) and the commitment codebook (forecasts_fd.txt, hedge or condition CE)
                        name, so that the same words lower both variables. Patterns: constants.H2_SHARED_WORDING.
  self_naming(text)     H5 fallback: a self-introduction in a unit's words ("I am <Name>", "we are the <Group>", "this is
                        <Name> of the ..."), used only where a voice label file carries no cue. Patterns:
                        constants.SELF_NAMING_PATTERNS (case kept: the name must start with a capital).
"""
import re

from . import constants as K

_SHARED = tuple((pid, kind, re.compile(pattern)) for pid, kind, pattern in K.H2_SHARED_WORDING)
_SELF = tuple((pid, re.compile(pattern)) for pid, pattern in K.SELF_NAMING_PATTERNS)
_SPACE = re.compile(r"\s+")


def normalise(text):
    """Lower case, typographic apostrophes made plain, white space collapsed."""
    return _SPACE.sub(" ", str(text or "").replace("’", "'").replace("‘", "'").lower()).strip()


def shared_wording(*texts):
    """Sorted ids of the H2_SHARED_WORDING patterns found in any of the texts (empty: not flagged)."""
    found = set()
    for text in texts:
        plain = normalise(text)
        if not plain:
            continue
        for pid, _, pattern in _SHARED:
            if pattern.search(plain):
                found.add(pid)
    return sorted(found)


def shared_kinds(ids):
    kinds = {pid: kind for pid, kind, _ in _SHARED}
    return sorted({kinds[pid] for pid in ids if pid in kinds})


def self_naming(text):
    """Sorted ids of the SELF_NAMING_PATTERNS found in the text, case as transcribed."""
    raw = _SPACE.sub(" ", str(text or "")).strip()
    return sorted(pid for pid, pattern in _SELF if raw and pattern.search(raw))
