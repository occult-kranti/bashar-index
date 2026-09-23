"""report.py — the multiple-comparison enforcer.

Rules (r2_design.md §2, frozen at git HEAD cff3988):
  * Exactly four primary tests (P1..P4), Holm-corrected as a family at alpha=0.05.
  * Every other test is exploratory: labeled in code, output JSON and figures.
  * No p-value appears in any artifact without an EXPLORATORY banner — this module
    REFUSES to format/serialize an unbadged p-value (build error).
  * Effect sizes with CIs are mandatory; p-only reporting is a build error.
"""
from __future__ import annotations

import json
import os

from common import GIT_HEAD, SEED, RESULTS, now_iso

ALPHA = 0.05
PRIMARY_IDS = ("P1", "P2", "P3", "P4")


class BadgeError(RuntimeError):
    """Raised when a p-value would be reported without a badge, or a test
    is reported p-only without effect size and CI."""


def holm_adjust(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, returned in original order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [None] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        adj[i] = min(running, 1.0)
    return adj


def make_test(test_id, statistic, p, effect, ci95, exploratory, note="",
              family=None, extra=None):
    """Build a validated test record. Enforcement lives here."""
    if family is None:
        family = "primary" if test_id in PRIMARY_IDS and not exploratory else "exploratory"
    if family == "primary":
        if test_id not in PRIMARY_IDS:
            raise BadgeError(f"primary-family test with unknown id {test_id!r}")
        if exploratory:
            raise BadgeError(f"primary test {test_id} cannot be exploratory")
    else:
        if not exploratory:
            raise BadgeError(
                f"test {test_id!r}: p-value without EXPLORATORY badge refused")
    if p is not None:
        if effect is None or ci95 is None:
            raise BadgeError(
                f"test {test_id!r}: p-only reporting is a build error "
                "(effect size and CI are mandatory)")
        if not (0.0 <= p <= 1.0):
            raise BadgeError(f"test {test_id!r}: p={p} out of range")
    rec = {
        "id": test_id,
        "family": family,
        "exploratory": bool(exploratory),
        "statistic": statistic,
        "p": p,
        "p_holm": None,  # filled by finalize() for the primary family
        "effect": effect,
        "ci95": list(ci95) if ci95 is not None else None,
        "note": note,
    }
    if extra:
        rec.update(extra)
    return rec


def finalize(module: str, tests: list[dict], provenance: dict, grade: str,
             digest_level: str, extra: dict | None = None) -> dict:
    """Assemble a results document: apply Holm to the primary family and
    validate the schema before anything is written."""
    primaries = [t for t in tests if t["family"] == "primary"]
    ids = [t["id"] for t in primaries]
    if len(set(ids)) != len(ids):
        raise BadgeError(f"duplicate primary ids: {ids}")
    with_p = [t for t in primaries if t["p"] is not None]
    if with_p:
        adj = holm_adjust([t["p"] for t in with_p])
        for t, a in zip(with_p, adj):
            t["p_holm"] = a
            t["significant_holm"] = bool(a < ALPHA)
    doc = {
        "module": module,
        "git_head": GIT_HEAD,
        "seed": SEED,
        "digest_level": digest_level,
        "tests": tests,
        "provenance": provenance,
        "grade": grade,
        "generated": now_iso(),
        "multiple_comparison_policy": (
            "4 primary tests (P1-P4), Holm-corrected as a family at alpha=0.05; "
            "all other tests EXPLORATORY, hypothesis-generating only."),
    }
    if extra:
        doc.update(extra)
    validate(doc)
    return doc


SCHEMA_REQUIRED = ["module", "git_head", "seed", "digest_level", "tests",
                   "provenance", "grade", "generated"]
TEST_REQUIRED = ["id", "family", "exploratory", "statistic", "p", "p_holm",
                 "effect", "ci95"]


def validate(doc: dict) -> None:
    for k in SCHEMA_REQUIRED:
        if k not in doc:
            raise BadgeError(f"results doc missing key {k!r}")
    if doc["git_head"] != GIT_HEAD:
        raise BadgeError("git_head mismatch against frozen cff3988")
    for t in doc["tests"]:
        for k in TEST_REQUIRED:
            if k not in t:
                raise BadgeError(f"test {t.get('id')!r} missing key {k!r}")
        if t["p"] is not None:
            if t["family"] != "primary" and not t["exploratory"]:
                raise BadgeError(
                    f"unbadged p-value in test {t['id']!r} refused")
            if t["effect"] is None or t["ci95"] is None:
                raise BadgeError(f"p-only reporting in test {t['id']!r} refused")
    fam = [t["id"] for t in doc["tests"] if t["family"] == "primary"]
    unknown = [i for i in fam if i not in PRIMARY_IDS]
    if unknown:
        raise BadgeError(f"unknown primary ids {unknown}")


def format_p(test: dict) -> str:
    """The only sanctioned way to render a p-value as text."""
    if test["p"] is None:
        return "p=n/a"
    if test["family"] == "primary":
        return f"p={test['p']:.4g} (Holm p={test['p_holm']:.4g}, primary {test['id']})"
    if not test["exploratory"]:
        raise BadgeError("refusing to format unbadged exploratory p-value")
    return f"p={test['p']:.4g} (EXPLORATORY)"


def write_results(doc: dict, filename: str) -> str:
    validate(doc)
    os.makedirs(RESULTS, exist_ok=True)
    path = os.path.join(RESULTS, filename)
    with open(path, "w") as f:
        json.dump(doc, f, indent=2, default=float)
    return path


def family_summary(results_dir: str = RESULTS) -> dict:
    """Cross-module Holm correction over the global primary family P1-P4.

    Reads every *_results.json, collects primary tests, applies Holm across the
    whole family (not per module), and writes family_holm.json. P2 is CI-based
    (p=None) and enters the family with its CI verdict, per design §2.
    """
    import glob
    prim = []
    for p in sorted(glob.glob(os.path.join(results_dir, "*_results.json"))):
        doc = json.load(open(p))
        for t in doc["tests"]:
            if t["family"] == "primary":
                prim.append({"module": doc["module"], "id": t["id"],
                             "p": t["p"], "ci95": t["ci95"],
                             "effect": t["effect"], "note": t["note"]})
    ids = sorted(t["id"] for t in prim)
    if ids != sorted(PRIMARY_IDS):
        raise BadgeError(f"global primary family incomplete/mismatched: {ids}")
    with_p = [t for t in prim if t["p"] is not None]
    adj = holm_adjust([t["p"] for t in with_p])
    for t, a in zip(with_p, adj):
        t["p_holm_global"] = a
        t["significant_holm_global"] = bool(a < ALPHA)
    for t in prim:
        if t["p"] is None:
            t["p_holm_global"] = None
            lo = t["ci95"][0] if t["ci95"] else None
            t["ci_verdict"] = ("CI lower bound >= 1.0 (ratchet signature)"
                               if (lo is not None and lo >= 1.0)
                               else "CI does not certify drift >= 1.0")
    out = {"family": "P1-P4", "alpha": ALPHA, "git_head": GIT_HEAD,
           "generated": now_iso(), "tests": prim,
           "policy": ("Holm step-down across the 4 primary tests; P2 is "
                      "CI-based and enters with its CI verdict (design §2).")}
    path = os.path.join(results_dir, "family_holm.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, default=float)
    return out
