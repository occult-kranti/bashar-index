"""Build the r3-P41 sense and collision register from register_terms.py and register_sources.py.

Writes, into step2/r3-P41/: register.csv (one row per term), register-sources.csv, register-strata.csv,
register-gates.csv, register-lists.csv and checks.txt. No corpus file is read; no network or model call is made.
Run: analysis-venv python -I build_register.py
"""
import csv
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "r3-P41")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S = _load("register_sources")
R = _load("register_terms")

_BRACE = re.compile(r"\{([^{}]*)\}")
_OPT = re.compile(r"(\w)\[(\w+)\]")


def norm(f):
    f = f.lower().replace("’", "'").replace("-", " ") if not _is_domain(f) else f.lower()
    return re.sub(r"\s+", " ", f).strip()


def _is_domain(f):
    return bool(re.search(r"\.[a-z]{2,}(/|$)", f)) and " " not in f


def expand(form):
    """Expand {a|b} alternatives and word[s] optional suffixes into explicit forms."""
    m = _BRACE.search(form)
    if m:
        out = []
        for alt in m.group(1).split("|"):
            out += expand(form[:m.start()] + alt + form[m.end():])
        return out
    m = _OPT.search(form)
    if m:
        return expand(form[:m.start(1) + 1] + form[m.end():]) + expand(form[:m.start(1) + 1] + m.group(2) + form[m.end():])
    return [norm(form)]


def is_pattern(f):
    return "<" in f


def main():
    os.makedirs(OUT, exist_ok=True)
    problems, notes = [], []
    terms = R.TERMS
    # ids
    for i, t in enumerate(terms, 1):
        t["id"] = "T%03d" % i
        exp = []
        for f in t["forms"]:
            exp += [f] if (is_pattern(f) or _is_domain(f)) else expand(f)
        # de-duplicate, keep order
        seen = set()
        t["exp"] = [x for x in exp if not (x in seen or seen.add(x))]
        ex = []
        for f in t["excl"]:
            ex += expand(f)
        t["exp_excl"] = ex
    # checks: sources, lists, strata, senses, gates
    for t in terms:
        for k in t["src"]:
            if k not in S.SOURCES:
                problems.append("%s %s: unknown source %s" % (t["id"], t["term"], k))
        for lid, cls in t["lists"].items():
            if lid not in R.LISTS:
                problems.append("%s: unknown list %s" % (t["id"], lid))
            if lid == "L01" and cls not in R.STRATA:
                problems.append("%s: unknown stratum %s" % (t["id"], cls))
        if t["kind"] in ("counted", "gated", "counted-unless-gate", "flagged", "frame", "domain") and not t["lists"]:
            problems.append("%s %s: counted kind with no list" % (t["id"], t["term"]))
        for p in t["psense"]:
            if p < 1 or p > len(t["senses"]):
                problems.append("%s: programme sense %s out of range" % (t["id"], p))
        if t["gate"] and t["gate"] not in R.GATES:
            problems.append("%s: unknown gate %s" % (t["id"], t["gate"]))
        if "L01" in t["lists"] and t["kind"] in ("counted", "gated") and not t["first"]:
            problems.append("%s %s: L01 term without a first-current entry" % (t["id"], t["term"]))
    # counted forms by list
    counted = {}
    for t in terms:
        if t["kind"] in ("excluded", "not listed", "class row", "fixed elsewhere", "gate-only"):
            continue
        for lid in t["lists"]:
            for f in t["exp"]:
                counted.setdefault(lid, {}).setdefault(f, []).append(t["id"])
    # duplicate forms inside one list from different terms (allowed only for the two disclosure classes of L07,
    # which share the surface form and split by gate)
    for lid, d in counted.items():
        for f, ids in d.items():
            if len(set(ids)) > 1:
                names = sorted(set(ids))
                msg = "list %s: form '%s' on terms %s" % (lid, f, ",".join(names))
                if f == "disclosure" and lid == "L07":
                    notes.append(msg + " (intended: one surface form, two gated classes; a token passing both gates "
                                       "is context-assigned and never counted)")
                else:
                    problems.append(msg)
    # gate words must not be counted forms of any other list (unless also counted on the gate's own list)
    for gid, (glist, win, words) in R.GATES.items():
        for w in words:
            w = norm(w)
            for lid, d in counted.items():
                if lid != glist and w in d and w not in counted.get(glist, {}):
                    problems.append("gate %s (list %s): gate word '%s' is a counted form of %s (%s)"
                                    % (gid, glist, w, lid, ",".join(d[w])))
    # shared forms across lists and nested forms across lists
    owner = {}
    for lid, d in counted.items():
        for f, ids in d.items():
            owner.setdefault(f, set()).add(lid)
    shared = {}
    for t in terms:
        if len(t["lists"]) > 1:
            shared[t["id"]] = "term sits on " + " and ".join(sorted(t["lists"]))
    nested = {}
    pron_nest = 0
    forms_by_list = {lid: [f for f in d if not is_pattern(f) and not _is_domain(f)] for lid, d in counted.items()}
    for la, fa_list in forms_by_list.items():
        for fa in fa_list:
            ta = " " + fa + " "
            for lb, fb_list in forms_by_list.items():
                if lb == la:
                    continue
                for fb in fb_list:
                    if fb != fa and len(fb) > len(fa) and ta in " " + fb + " ":
                        if set(counted[la][fa]) & set(counted[lb][fb]):
                            continue  # same term on both lists: the longest form wins inside each list
                        if la == "L09":
                            pron_nest += 1
                            continue
                        for tid in counted[la][fa]:
                            nested.setdefault(tid, set()).add("'%s' inside %s '%s'" % (fa, lb, fb))
    notes.append("pronoun forms of L09 nested inside other lists' phrases: %d form pairs (expected; L09 counts pronoun "
                 "tokens wherever they occur, other lists count their phrases)" % pron_nest)
    # write register.csv
    cols = ["term_id", "term", "rule_kind", "lists", "list_classes", "forms_expanded", "exclusion_forms", "gate",
            "senses", "programme_sense_ids", "programme_sense", "collisions", "disambiguation_rule", "stratum_first_current",
            "stratum_dating_source", "dating_certainty", "strand", "trope_adjacent", "shared_with", "nested_in_other_lists",
            "sources", "source_check", "reason", "blind_note"]
    with open(os.path.join(OUT, "register.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for t in terms:
            senses = "; ".join("%s.s%d: %s" % (t["id"], i, s) for i, s in enumerate(t["senses"], 1))
            ps_ids = "|".join("%s.s%d" % (t["id"], p) for p in t["psense"])
            ps = "; ".join(t["senses"][p - 1] for p in t["psense"])
            gate = ""
            if t["gate"]:
                gl, gw, gwords = R.GATES[t["gate"]]
                gate = "%s (applies in %s; window +/-%d tokens)" % (t["gate"], gl, gw)
            chk = t["check"] or "; ".join("%s: %s" % (k, S.SOURCES[k][3]) for k in t["src"] if k in S.SOURCES)
            w.writerow([t["id"], t["term"], t["kind"], "|".join(sorted(t["lists"])),
                        "|".join("%s:%s" % (k, v) for k, v in sorted(t["lists"].items())),
                        "|".join(t["exp"]), "|".join(t["exp_excl"]), gate, senses, ps_ids, ps, t["coll"], t["rule"],
                        t["first"], t["dsrc"], t["cert"], t["strand"], t["trope"], shared.get(t["id"], ""),
                        "; ".join(sorted(nested.get(t["id"], set()))), "|".join(t["src"]), chk, t["reason"], t["blind"]])
    with open(os.path.join(OUT, "register-sources.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["source_key", "full_reference", "url", "kind", "what_was_seen"])
        used = set(k for t in terms for k in t["src"]) | set(re.findall(r"[A-Z][A-Z0-9]+", " ".join(
            v[2] for v in R.STRATA.values())))
        for k, (ref, url, kind, chk) in S.SOURCES.items():
            if k in used:
                w.writerow([k, ref, url, kind, chk])
        unused = [k for k in S.SOURCES if k not in used]
    with open(os.path.join(OUT, "register-strata.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["stratum", "name", "entry_date", "dating_sources", "certainty", "imported"])
        for k, v in R.STRATA.items():
            w.writerow([k] + list(v))
    with open(os.path.join(OUT, "register-gates.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["gate_id", "applies_in_list", "window_tokens", "gate_words"])
        for k, (gl, gw, words) in R.GATES.items():
            w.writerow([k, gl, gw, "|".join(norm(x) for x in words)])
    with open(os.path.join(OUT, "register-lists.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["list_id", "file_stem", "entries_served", "planned_use"])
        for k, v in R.LISTS.items():
            w.writerow([k] + list(v))
    # summary
    from collections import Counter
    kinds = Counter(t["kind"] for t in terms)
    per_list = Counter(l for t in terms if t["kind"] not in ("excluded", "not listed", "fixed elsewhere", "gate-only")
                       for l in t["lists"])
    nforms = sum(len(t["exp"]) for t in terms)
    with open(os.path.join(OUT, "checks.txt"), "w", encoding="utf-8") as fh:
        fh.write("r3-P41 register build checks\n")
        fh.write("terms: %d; expanded forms: %d\nkinds: %s\nterm rows per list: %s\n" % (
            len(terms), nforms, dict(kinds), dict(sorted(per_list.items()))))
        fh.write("sources used: %d of %d defined; unused: %s\n" % (len(S.SOURCES) - len(unused), len(S.SOURCES),
                                                                    ", ".join(unused) or "none"))
        fh.write("terms on more than one list: %d\nterms with forms nested in another list's forms: %d\n" % (
            len(shared), len(nested)))
        fh.write("PROBLEMS (%d):\n" % len(problems))
        for p in problems:
            fh.write("  " + p + "\n")
        fh.write("NOTES:\n")
        for n in notes:
            fh.write("  " + n + "\n")
    print(open(os.path.join(OUT, "checks.txt"), encoding="utf-8").read())
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
