"""Write the step-2 lists as projections of the hashed r3-P41 register.

Reads only step2/r3-P41/*.csv (after checking register.csv against the hash recorded in step2/hash-record.md) and
writes step2/lists/<list-id>.csv. No corpus file is read; no network or model call is made.
Run: analysis-venv python -I build_lists.py
"""
import csv
import hashlib
import itertools
import os
import re
import sys

STEP2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(STEP2, "r3-P41")
OUT = os.path.join(STEP2, "lists")
KEEP = {"counted", "gated", "counted-unless-gate", "flagged", "frame", "domain", "class row"}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rows(name):
    return list(csv.DictReader(open(os.path.join(REG, name), encoding="utf-8")))


def main():
    rec = open(os.path.join(STEP2, "hash-record.md"), encoding="utf-8").read()
    m = re.search(r"`r3-P41/register.csv` \| `([0-9a-f]{64})`", rec)
    got = sha(os.path.join(REG, "register.csv"))
    if not m or m.group(1) != got:
        sys.exit("register.csv does not match the recorded hash; stop")
    reg = rows("register.csv")
    src = {r["source_key"]: r for r in rows("register-sources.csv")}
    strata = {r["stratum"]: r for r in rows("register-strata.csv")}
    lists = {r["list_id"]: r for r in rows("register-lists.csv")}
    gates = {r["gate_id"]: r for r in rows("register-gates.csv")}
    os.makedirs(OUT, exist_ok=True)
    cols = ["list_id", "entry", "term_id", "term", "class_or_stratum", "sense_ids", "forms", "exclusion_forms", "gate",
            "gate_words", "rule_kind", "rule", "first_current", "dating_source", "dating_certainty", "layer_entry_date",
            "layer_imported", "strand", "trope_adjacent", "also_on_lists", "blind_note", "source_keys", "citations"]
    summary = []
    for lid, meta in lists.items():
        if lid == "L02":
            continue
        out = []
        for r in reg:
            if r["rule_kind"] not in KEEP:
                continue
            cls = dict(x.split(":", 1) for x in r["list_classes"].split("|") if x)
            if lid not in cls:
                continue
            gate = r["gate"]
            gid = gate.split(" ")[0] if gate else ""
            gw = gates[gid]["gate_words"] if gid and gates[gid]["applies_in_list"] == lid else ""
            if gid and gates[gid]["applies_in_list"] != lid:
                gate = ""  # gates apply only in their own list (register rule G5)
            st = strata.get(cls[lid]) if lid == "L01" else None
            cites = " || ".join("%s <%s>" % (src[k]["full_reference"], src[k]["url"]) if src[k]["url"] else
                                src[k]["full_reference"] for k in r["sources"].split("|") if k in src)
            out.append([lid, 0, r["term_id"], r["term"], cls[lid], r["programme_sense_ids"], r["forms_expanded"],
                        r["exclusion_forms"], gate, gw, r["rule_kind"], r["disambiguation_rule"],
                        r["stratum_first_current"] if lid == "L01" else "",
                        r["stratum_dating_source"] if lid == "L01" else "",
                        r["dating_certainty"] if lid == "L01" else "",
                        st["entry_date"] if st else "", st["imported"] if st else "",
                        r["strand"] if lid == "L01" else "", r["trope_adjacent"],
                        "|".join(k for k in cls if k != lid), r["blind_note"], r["sources"], cites])
        for i, row in enumerate(out, 1):
            row[1] = i
        path = os.path.join(OUT, meta["file_stem"] + ".csv")
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(out)
        nforms = sum(len(r[6].split("|")) for r in out if r[6])
        summary.append((lid, meta["file_stem"], len(out), nforms))
    # L02: pairs
    meta = lists["L02"]
    layer_ids = list(strata)
    pcols = ["list_id", "pair_id", "side_a", "side_b", "role", "registered_predictions", "rule", "citations"]
    prs = []
    prs.append(["L02", "P000", "L01 strand=federation (S06 rows marked federation)",
                "L01 strand=adversarial (S07 and S15 rows marked adversarial)", "decisive pair",
                "et: at or below chance; occult and emic: at or above chance in the 2020s (programme r3-P44, as stated "
                "there; account attribution not stated in the programme)",
                "Creator-level co-use against the blocked curveball null with fixed margins and against r3-P42's placebo "
                "pseudo-strata; a pair counts as structure only outside both; strata by audience size and economy type "
                "(den-soc's audience-capture reading, N26). Adversarial terms are subject to register G10 (decision D1).",
                "PROGRAMME (r3-P44); WRSP2016; PARTRIDGE2004; LEWISKAHN2005"])
    prs.append(["L02", "P001", "L05 (CR-A to CR-E, ADV-NEG, ADV-AMB; BRIDGE only where it passes its rule)", "L06 (SHIFT)",
                "conspirituality pair", "not registered in the programme (descriptive)",
                "As P000. Ward and Voas define conspirituality by these two convictions.", "WARDVOAS2011; ASPREM2015"])
    n = 2
    for a, b in itertools.combinations(layer_ids, 2):
        prs.append(["L02", "P%03d" % n, "L01 %s (%s)" % (a, strata[a]["name"]), "L01 %s (%s)" % (b, strata[b]["name"]),
                    "layer pair", "none", "As P000; heat-map cell.", "register-strata.csv"])
        n += 1
    path = os.path.join(OUT, meta["file_stem"] + ".csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(pcols)
        w.writerows(prs)
    summary.append(("L02", meta["file_stem"], len(prs), 0))
    for s in sorted(summary):
        print("%s %-40s rows=%4d forms=%5d" % s)


if __name__ == "__main__":
    main()
