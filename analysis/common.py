"""common.py — shared loaders, frozen lexicon, figure style, provenance helpers.

Bashar-Index evidence-honest panel, round 3 (implementation), seed 42.
Design frozen at git HEAD cff3988 (design round 2, loop 1); all lexicon/scoring
decisions below are verbatim from /mnt/agents/lab2/panel/r2_design.md §1(a).
"""
from __future__ import annotations

import json
import os
import re
import glob
import hashlib
from datetime import datetime, timezone

import numpy as np

REPO = "/mnt/agents/lab2/bashar-index"
DATA = os.path.join(REPO, "data")
GIT_HEAD = "cff3988"   # pinned freeze point (advisor amendment: absolute, not relative)
SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
FIGURES = os.path.join(HERE, "figures")

# ---------------------------------------------------------------- frozen lexicon
# Verbatim from r2_design.md §1(a). This list may not be edited after the first
# scoring run (frozen at git HEAD cff3988).
LEXICON = [
    "probable", "probability", "probable realities", "probable reality",
    "most probable", "likely", "window", "window of", "depends on",
    "dependent on", "up to you", "up to humanity", "collective choice",
    "collective decision", "your choice", "if you", "should you",
    "as long as", "provided that", "conditional", "vibrational",
    "vibrationally", "frequency", "energy reading", "reading of the energy",
    "current energy", "at this time", "as of now", "timeline", "timelines",
    "parallel reality", "parallel realities", "shift", "sensitive to",
    "subject to change", "may change", "can change", "not set in stone",
    "no such thing as a prediction", "potential", "potentially", "possible",
    "possibly", "we sense", "we perceive", "our sensing", "approximate",
    "approximately", "around", "give or take",
]
# NOTE: the verbatim frozen list contains 50 phrases (task shorthand said 47);
# verbatim fidelity to r2_design.md §1(a) is what is frozen, so we keep all 50.
assert len(LEXICON) == 50, f"lexicon drift: {len(LEXICON)} != 50"

# Precompile longest-match-first patterns (whole-phrase, case-insensitive).
_LEX_PATTERNS = sorted(
    [(p, re.compile(r"(?<![A-Za-z])" + re.escape(p) + r"(?![A-Za-z])", re.I))
     for p in LEXICON],
    key=lambda t: -len(t[0]),
)


def lexicon_hits(text: str) -> tuple[int, list[str]]:
    """Count lexicon phrase occurrences, longest match wins on overlap.

    Returns (hit_count, list_of_matched_phrases).
    """
    if not text:
        return 0, []
    spans = []  # (start, end, phrase)
    for phrase, pat in _LEX_PATTERNS:
        for m in pat.finditer(text):
            spans.append((m.start(), m.end(), phrase))
    # longest match wins: sort by start, then longest first; greedily keep
    # non-overlapping.
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    kept, occupied = [], []
    for s, e, p in spans:
        if all(e <= os_ or s >= oe for os_, oe in occupied):
            kept.append(p)
            occupied.append((s, e))
    return len(kept), kept


def token_count(text: str) -> int:
    return len(text.split()) if text else 0


# ---------------------------------------------------------------- loaders

def load_json(name: str):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def load_analysis() -> dict:
    return load_json("analysis.json")


def load_videos() -> list[dict]:
    return load_json("videos.json")


def load_digests() -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(DATA, "digests", "*.json"))):
        with open(path) as f:
            out.append(json.load(f))
    return out


def load_glossary() -> list[dict]:
    return load_json("glossary.json")


# ---------------------------------------------------------------- style
AMBER = "#e8a33d"
COPPER = "#b5713a"
BG = "#191715"
GRID = "#3a352f"
TEXT = "#ede6da"


def apply_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "axes.edgecolor": GRID,
        "axes.labelcolor": TEXT,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": TEXT,
        "ytick.color": TEXT,
        "text.color": TEXT,
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "axes.prop_cycle": matplotlib.cycler(color=[AMBER, COPPER, TEXT]),
    })
    return plt


def badge(fig, digest_level: str, grade: str, exploratory: bool, extra: str = ""):
    """Every figure embeds its badge (design §5)."""
    label = f"digest_level: {digest_level} | grade: {grade}"
    if exploratory:
        label = "EXPLORATORY — " + label
    if extra:
        label += " | " + extra
    fig.text(0.99, 0.01, label, ha="right", va="bottom", fontsize=7,
             color=TEXT, alpha=0.85, style="italic")


# ---------------------------------------------------------------- provenance

def provenance(inputs: list[str], reverification: str = "n/a") -> dict:
    return {"inputs": inputs, "reverification": reverification}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
