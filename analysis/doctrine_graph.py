"""doctrine_graph.py — Q2 structural half. DESCRIPTIVE ONLY.

This module measures genre discipline, not truth. It characterizes the internal
structure and consistency of the corpus (concept graph, term-rank stability,
candidate contradiction flags). Consistency results are descriptive corpus
science and never carry origin-language (advisor ruling 2b).

Outputs: results/doctrine_results.json, results/doctrine_graph.graphml,
figures/fig_f6_network.png, figures/fig_f6b_term_movers.png
Seed 42.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict

import numpy as np
from scipy import stats
import networkx as nx

import common
from common import SEED, RESULTS, FIGURES
import report

RNG = np.random.default_rng(SEED)
BANNER = "measures genre discipline, not truth"
FREQ_SCORE = {"high": 3.0, "medium": 2.0, "low": 1.0}
TOP_K_W = 15        # terms in the Kendall's W ranking
TOP_N_NODES = 40    # digest key_terms added to the graph
COOC_MIN = 3        # minimum co-document count for a co-occurrence edge


def norm(t: str) -> str:
    t = t.lower()
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def build_graph(glossary, digests):
    gmap = {}  # norm -> canonical glossary term
    for g in glossary:
        gmap.setdefault(norm(g["term"]), g["term"])
        for part in re.split(r"/", g["term"]):
            gmap.setdefault(norm(part), g["term"])

    # digest key_term stats
    doc_count = Counter()
    canonical = {}
    for d in digests:
        seen = set()
        for k in d.get("key_terms") or []:
            n = norm(k["term"])
            if n in seen:
                continue
            seen.add(n)
            doc_count[n] += 1
            canonical.setdefault(n, k["term"])
    top_terms = [t for t, _ in doc_count.most_common(TOP_N_NODES)]

    G = nx.Graph()
    for g in glossary:
        G.add_node(g["term"], source="glossary", docs=0)
    for t in top_terms:
        name = gmap.get(t, canonical[t])
        if not G.has_node(name):
            G.add_node(name, source="digests", docs=doc_count[t])
        else:
            G.nodes[name]["docs"] = doc_count[t]

    # glossary related-term edges
    gloss_edges = 0
    for g in glossary:
        for r in g.get("related") or []:
            tgt = gmap.get(norm(r))
            if tgt and G.has_node(tgt) and tgt != g["term"]:
                G.add_edge(g["term"], tgt, kind="glossary_related")
                gloss_edges += 1
    # digest co-occurrence edges among graphed terms
    node_norms = {norm(n): n for n in G.nodes}
    cooc = Counter()
    for d in digests:
        terms = {node_norms[norm(k["term"])] for k in (d.get("key_terms") or [])
                 if norm(k["term"]) in node_norms}
        for a in sorted(terms):
            for b in sorted(terms):
                if a < b:
                    cooc[(a, b)] += 1
    cooc_edges = 0
    for (a, b), c in cooc.items():
        if c >= COOC_MIN:
            if G.has_edge(a, b):
                G.edges[a, b]["cooc"] = c
            else:
                G.add_edge(a, b, kind="cooccurrence", cooc=c)
                cooc_edges += 1
    return G, doc_count, gmap, gloss_edges, cooc_edges


def kendall_w(ratings: np.ndarray) -> float:
    """Kendall's W with tie correction. ratings: m raters x k objects."""
    m, k = ratings.shape
    R = ratings.sum(axis=0)
    S = np.sum((R - R.mean()) ** 2)
    tie_sum = 0.0
    for row in ratings:
        _, counts = np.unique(row, return_counts=True)
        tie_sum += np.sum(counts ** 3 - counts)
    denom = m ** 2 * (k ** 3 - k) - m * tie_sum
    return float(12 * S / denom) if denom > 0 else 0.0


def detect_contradictions(digests, glossary):
    """Programmatic candidate-contradiction flags. Descriptive only."""
    flags = []

    def digest_blob(d):
        parts = [d.get("opening_summary") or "", d.get("researcher_note") or "",
                 d.get("title") or ""]
        for q in d.get("qa_topics") or []:
            parts.append(q.get("question", ""))
            parts.append(q.get("answer_gist", ""))
        for p in d.get("predictions_and_dates") or []:
            parts.append(str(p))
        for k in d.get("key_terms") or []:
            parts.append(str(k))
        parts.append(json.dumps(d.get("named_entities") or ""))
        parts.append(json.dumps(d.get("quotes") or ""))
        return " ".join(parts)

    blobs = {d["video_id"]: digest_blob(d) for d in digests}
    # teachings.md is the repo's canonical doctrine summary — a first-class
    # source for doctrinal statements (source-tagged separately from digests).
    with open(os.path.join(common.DATA, "teachings.md")) as f:
        teachings_blob = f.read()
    years = {d["video_id"]: None for d in digests}
    vmap = {v["video_id"]: v for v in common.load_videos()}
    for d in digests:
        v = vmap.get(d["video_id"], {})
        if v.get("year_reliable"):
            years[d["video_id"]] = v.get("year")

    # (1) arity conflict: Four Laws vs Five Laws
    pat4 = re.compile(r"\b(four|4)\s+laws\b", re.I)
    pat5 = re.compile(r"\b(five|5)\s+laws\b", re.I)
    hits4 = [vid for vid, b in blobs.items() if pat4.search(b)]
    hits5 = [vid for vid, b in blobs.items() if pat5.search(b)]
    t4 = len(pat4.findall(teachings_blob))
    t5 = len(pat5.findall(teachings_blob))
    g4 = next((g for g in glossary if g["term"] == "Four Laws of Creation"), None)
    g5 = next((g for g in glossary if g["term"] == "Five Laws of Creation"), None)
    if (hits4 or g4 or t4) and (hits5 or g5 or t5):
        flags.append({
            "id": "arity-laws-4-vs-5",
            "kind": "arity_conflict",
            "terms": ["Four Laws of Creation", "Five Laws of Creation"],
            "digests_citing_4": sorted(hits4),
            "digests_citing_5": sorted(hits5),
            "teachings_md_mentions_4": t4,
            "teachings_md_mentions_5": t5,
            "years_4": sorted({years[v] for v in hits4 if years[v]}),
            "years_5": sorted({years[v] for v in hits5 if years[v]}),
            "glossary_documents_conflict": bool(g4 and g5),
            "detail": ("The corpus carries both arities: the glossary lists "
                       "'Four Laws of Creation' (the older/parallel form) and "
                       "'Five Laws of Creation' (the stated immutable set) as "
                       "separate entries; teachings.md and digests cite both. "
                       "This is the known 4-vs-5-Laws conflict, flagged "
                       "programmatically."),
        })

    # (2) alias/identity conflict: Shalanaya vs Yahyel
    psh = re.compile(r"shalanaya|shalinaya", re.I)
    pya = re.compile(r"yahyel|ya'yel", re.I)
    hsh = [vid for vid, b in blobs.items() if psh.search(b)]
    hya = [vid for vid, b in blobs.items() if pya.search(b)]
    tsh = len(psh.findall(teachings_blob))
    tya = len(pya.findall(teachings_blob))
    both = sorted(set(hsh) & set(hya))
    gy = next((g for g in glossary if g["term"].startswith("Yahyel")), None)
    if (hsh or tsh) and (hya or tya):
        flags.append({
            "id": "alias-shalanaya-yahyel",
            "kind": "alias_conflict",
            "terms": ["Shalanaya (Shalinaya)", "Yahyel (Ya'yel)"],
            "digests_citing_shalanaya": sorted(hsh),
            "digests_citing_yahyel": sorted(hya),
            "teachings_md_mentions_shalanaya": tsh,
            "teachings_md_mentions_yahyel": tya,
            "digests_citing_both": both,
            "glossary_note": (gy["definition"][:220] if gy else None),
            "detail": ("The corpus uses both names: digests cite 'Yahyel' "
                       "broadly while 'Shalanaya/Shalinaya' survives in "
                       "teachings.md and the glossary. The glossary records "
                       "them as one race while noting fan sources that split "
                       "them — the known Shalanaya/Yahyel identity conflict, "
                       "flagged programmatically."),
        })

    # (3) window polarity flip: later-stated contact-window lower bound exceeds
    # an earlier-stated upper bound (the window moved entirely past itself).
    from predictions import parse_bounds
    win_rows = []
    for d in digests:
        t = years.get(d["video_id"])
        if not t:
            continue
        for p in d.get("predictions_and_dates") or []:
            txt = " ".join([str(p.get("prediction") or ""),
                            str(p.get("context") or "")])
            if not re.search(r"contact", txt, re.I):
                continue
            lo, hi = parse_bounds(str(p.get("date") or p.get("year")
                                      or p.get("year_or_date") or ""))
            if lo and hi >= t:
                win_rows.append((t, lo, hi))
    win_rows.sort()
    flips = []
    for i in range(len(win_rows)):
        for j in range(i + 1, len(win_rows)):
            ti, loi, hii = win_rows[i]
            tj, loj, hij = win_rows[j]
            if tj > ti and loj > hii:
                flips.append({"earlier": {"made": ti, "window": [loi, hii]},
                              "later": {"made": tj, "window": [loj, hij]}})
    if flips:
        flags.append({
            "id": "window-polarity-flips",
            "kind": "polarity_flip",
            "n_flips": len(flips),
            "examples": flips[:6],
            "detail": ("Later-stated contact window lies entirely beyond an "
                       "earlier-stated window: the promised event moved past "
                       "its own previously stated deadline. Descriptive ledger "
                       "fact, not inference."),
        })

    # (4) glossary related-term asymmetry (order/alias bookkeeping conflicts)
    terms = {g["term"] for g in glossary}
    asym = []
    for g in glossary:
        for r in g.get("related") or []:
            tgt = next((x for x in glossary if x["term"] == r), None)
            if tgt and g["term"] not in (tgt.get("related") or []):
                asym.append([g["term"], r])
    flags.append({
        "id": "glossary-related-asymmetry",
        "kind": "order_alias_conflict",
        "n_asymmetric_pairs": len(asym),
        "examples": asym[:10],
        "detail": ("related-term edges that are not reciprocated in the "
                   "glossary itself; bookkeeping-level inconsistency."),
    })
    return flags


def era_movers(digests, gmap, doc_count):
    """Term-score shift between eras (reliable years <=2024 vs >=2025)."""
    vmap = {v["video_id"]: v for v in common.load_videos()}
    era_score = {"early": Counter(), "late": Counter()}
    era_n = {"early": 0, "late": 0}
    for d in digests:
        v = vmap.get(d["video_id"], {})
        if not v.get("year_reliable") or not v.get("year"):
            continue
        era = "early" if v["year"] <= 2024 else "late"
        era_n[era] += 1
        for k in d.get("key_terms") or []:
            era_score[era][norm(k["term"])] += FREQ_SCORE.get(
                str(k.get("freq", "")).lower(), 0.5)
    terms = [t for t, _ in doc_count.most_common(25)]
    out = []
    for t in terms:
        a = era_score["early"][t] / max(1, era_n["early"])
        b = era_score["late"][t] / max(1, era_n["late"])
        out.append({"term": gmap.get(t, t), "early_score": a, "late_score": b,
                    "delta": b - a})
    out.sort(key=lambda r: -abs(r["delta"]))
    return out, era_n


# ------------------------------------------------------------------ figures

def fig_network(G, path):
    plt = common.apply_style()
    fig, ax = plt.subplots(figsize=(11, 9))
    pos = nx.spring_layout(G, seed=SEED, k=1.3)
    sizes = [80 + 30 * G.nodes[n].get("docs", 0) for n in G.nodes]
    ge = [(u, v) for u, v, d in G.edges(data=True)
          if d.get("kind") == "glossary_related"]
    ce = [(u, v) for u, v, d in G.edges(data=True)
          if d.get("kind") == "cooccurrence"]
    nx.draw_networkx_edges(G, pos, edgelist=ge, edge_color=common.AMBER,
                           alpha=0.45, width=1.0, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=ce, edge_color=common.COPPER,
                           alpha=0.35, width=0.8, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=common.AMBER,
                           edgecolors=common.COPPER, linewidths=0.8, ax=ax)
    hub = sorted(G.degree, key=lambda x: -x[1])[:18]
    nx.draw_networkx_labels(G, pos, labels={n: n for n, _ in hub}, font_size=7,
                            font_color=common.TEXT, ax=ax)
    ax.set_title("F6. Doctrine concept graph — glossary related-terms (amber) "
                 "+ digest co-occurrence (copper)\n"
                 f"{G.number_of_nodes()} concepts, {G.number_of_edges()} edges "
                 f"— {BANNER}", fontsize=11)
    ax.axis("off")
    common.badge(fig, "content", "Frontier", exploratory=True)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_movers(movers, era_n, path, top=10):
    plt = common.apply_style()
    sel = movers[:top]
    fig, ax = plt.subplots(figsize=(8, 6))
    for r in sel:
        ax.plot([0, 1], [r["early_score"], r["late_score"]], "-o",
                color=common.AMBER if r["delta"] >= 0 else common.COPPER,
                lw=1.8, ms=5, alpha=0.9)
        ax.text(-0.02, r["early_score"], r["term"], ha="right", va="center",
                fontsize=8, color=common.TEXT)
        ax.text(1.02, r["late_score"], f'{r["term"]} ({r["delta"]:+.2f})',
                ha="left", va="center", fontsize=8, color=common.TEXT)
    ax.set_xlim(-0.9, 1.9)
    ax.set_xticks([0, 1], [f"≤2024 (n={era_n['early']} docs)",
                           f"≥2025 (n={era_n['late']} docs)"])
    ax.set_ylabel("mean salience score per digest (high=3 / med=2 / low=1)")
    ax.set_title("F6b. Top term-salience movers across eras — "
                 f"{BANNER}", fontsize=11)
    common.badge(fig, "content", "Frontier", exploratory=True)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ------------------------------------------------------------------ main

def main():
    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(FIGURES, exist_ok=True)
    glossary = common.load_glossary()
    digests = common.load_digests()

    G, doc_count, gmap, n_ge, n_ce = build_graph(glossary, digests)
    nx.write_graphml(G, os.path.join(RESULTS, "doctrine_graph.graphml"))

    # Kendall's W term-rank stability across digests (top-K terms)
    top_terms = [t for t, _ in doc_count.most_common(TOP_K_W)]
    ratings = np.zeros((len(digests), TOP_K_W))
    for i, d in enumerate(digests):
        score = {norm(k["term"]): FREQ_SCORE.get(str(k.get("freq", "")).lower(), 0.5)
                 for k in (d.get("key_terms") or [])}
        for j, t in enumerate(top_terms):
            ratings[i, j] = score.get(t, 0.0)
    W = kendall_w(ratings)
    boot = []
    for _ in range(2000):
        idx = RNG.integers(0, len(digests), len(digests))
        boot.append(kendall_w(ratings[idx]))
    ci_W = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]

    flags = detect_contradictions(digests, glossary)
    movers, era_n = era_movers(digests, gmap, doc_count)

    fig_network(G, os.path.join(FIGURES, "fig_f6_network.png"))
    fig_movers(movers, era_n, os.path.join(FIGURES, "fig_f6b_term_movers.png"))

    tests = [report.make_test(
        "E6-kendall-W-term-rank-stability",
        statistic={"kendall_W": W, "m_raters": len(digests),
                   "k_terms": TOP_K_W},
        p=None,
        effect={"W": W}, ci95=ci_W,
        exploratory=True,
        note=("Kendall's W (tie-corrected) of within-digest term salience "
              "ranks (high/med/low/absent) across 75 digests for the top-15 "
              "terms; bootstrap CI over digests. Descriptive: low W = salience "
              "ranking varies by document; no p-value by design (descriptive "
              "module)."))]
    extra = {
        "banner": BANNER,
        "advisor_ruling_2b": ("Consistency is descriptive corpus science, not "
                              "evidence about origin; no origin-language "
                              "appears in this output."),
        "graph": {"nodes": G.number_of_nodes(), "edges": G.number_of_edges(),
                  "glossary_related_edges": n_ge,
                  "cooccurrence_edges": n_ce,
                  "graphml": "results/doctrine_graph.graphml",
                  "density": float(nx.density(G)),
                  "n_components": nx.number_connected_components(G)},
        "EXPLORATORY_contradiction_flags": flags,
        "EXPLORATORY_era_movers": movers[:10],
        "era_doc_counts": era_n,
        "known_conflicts_check": {
            "laws_4_vs_5_flagged": any(f["id"] == "arity-laws-4-vs-5"
                                       for f in flags),
            "shalanaya_yahyel_flagged": any(f["id"] == "alias-shalanaya-yahyel"
                                            for f in flags),
        },
    }
    doc = report.finalize(
        "doctrine_graph", tests,
        common.provenance(["data/glossary.json", "data/digests/*.json",
                           "data/teachings.md", "data/videos.json"]),
        grade="Frontier", digest_level="content", extra=extra)
    doc["banner"] = BANNER
    path = report.write_results(doc, "doctrine_results.json")
    print(f"graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges "
          f"(glossary {n_ge}, cooc {n_ce})")
    print(f"Kendall's W = {W:.3f} CI{ci_W} (m={len(digests)}, k={TOP_K_W})")
    print(f"contradiction flags: {[f['id'] for f in flags]}")
    for f in flags:
        if f["id"] == "arity-laws-4-vs-5":
            print("  4-laws digests:", f["digests_citing_4"],
                  "| 5-laws digests:", f["digests_citing_5"])
        if f["id"] == "window-polarity-flips":
            print("  window flips:", f["n_flips"])
    print("wrote", path)


if __name__ == "__main__":
    main()
