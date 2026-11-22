"""Report writer. Public files hold counts and derived numbers only: no creator code, transcript text, title or video id
(catalogue rule R15, plan R26). Creator-level values go to a private file beside them.

    report.json         every hypothesis: eligibility, estimate, intervals, raw and Holm-adjusted p, verdict, rows,
                        tipping-point table, the sentences that go with the result; both versions of the A10 guard
                        (registered and amended: p, estimate, intervals, verdict) with the guard's outcome; the
                        uninformative flag; the Holm table; the code hashes
    report.md           the same as tables
    report.private.json creator-level values keyed by creator code (never published)
"""
import json
from pathlib import Path

from . import adapter
from . import common
from . import constants as K

PRIVATE_KEYS = ("creator_values", "private_log_ratios_T5", "registered_creator_values")


def public(result):
    return {key: common.short(value) for key, value in result.items() if key not in PRIVATE_KEYS}


def build(primary, final, holm_table, meta):
    hypotheses = {}
    for name in sorted(primary):
        hypotheses[name] = {"result": public(primary[name]), **{k: common.short(v) for k, v in final[name].items()}}
    return {"meta": meta, "holm": common.short(holm_table), "hypotheses": hypotheses, "code_sha256": adapter.code_hashes(),
            "holm_count": K.HOLM_M, "fixed_p": K.FIXED_P, "unrun": list(K.UNRUN),
            "a10_guard": ("the larger of the registered and the amended p enters Holm; a verdict stands only if both versions give "
                          "it; if either version is not determinable, the result is not determinable (registry 2026-11-21 04:55)"),
            "mh_interval_rule": K.MH_INTERVAL_RULE,
            "uninformative_rule": ("a result is uninformative when its 90% creator interval contains both zero and the smallest "
                                   "effect of interest in either direction, or its verdict is not determinable (registry 02:50)")}


def _first(estimate):
    return next(iter((estimate or {}).items()), (None, None))


def markdown(report):
    lines = [f"# Registered hypotheses: {report['meta'].get('title', 'analysis')}", ""]
    if report["meta"].get("synthetic"):
        lines += ["**Synthetic data.** Every number below comes from simulated creators; none describes the corpus.", ""]
    lines += ["| Hypothesis | Eligible creators (minimum) | Estimate | Interval for A5 | p amended / registered | p (Holm input, the larger) | "
              "Holm-adjusted p | Verdict (A10 guard) | Uninformative | Robust to the labeller |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for name, item in report["hypotheses"].items():
        res = item["result"]
        elig = res.get("eligibility") or {}
        first = _first(res.get("estimate"))
        ints = res.get("intervals") or {}
        a5 = ints.get("hksj_90") or ints.get("t90_OE") or ints.get("bootstrap_90") or ""
        lines.append(f"| {name} | {elig.get('creators')} ({elig.get('minimum')}) | {first[0]} {first[1]} | {a5} | "
                     f"{item.get('holm_input_p_amended')} / {item.get('holm_input_p_registered')} | {item['holm_input_p']} | "
                     f"{item['holm_adjusted_p']} | {item['verdict']} | {item.get('uninformative')} | {item['robust_to_the_labeller']} |")
    lines += ["", "Holm count fixed at 10 (A10.1); H3 and H8 enter at p = 1, H7 and H10 (unrun) at p = 1. A10 guard: " + report["a10_guard"]
              + ". Uninformative: " + report["uninformative_rule"] + ".", ""]
    for name, item in report["hypotheses"].items():
        lines += [f"## {name}", ""]
        if item.get("verdict_statement"):
            lines += [f"**{item['verdict_statement']}**", ""]
        lines += ["- " + sentence for sentence in item["sentences"]]
        versions = item.get("versions") or {}
        if versions.get("registered"):
            lines += ["", "| Version | Eligible creators (minimum) | Estimate | 90% creator interval | p | Verdict | Uninformative |",
                      "|---|---|---|---|---|---|---|"]
            for key in ("amended", "registered"):
                v = versions[key]
                first = _first(v.get("estimate"))
                lines.append(f"| {key} | {v.get('eligible_creators')} ({v.get('minimum')}) | {first[0]} {first[1]} | "
                             f"{v.get('creator_interval_90')} | {v.get('p')} | {v.get('verdict')} | {v.get('uninformative')} |")
            lines += ["", "A10 replaces: " + "; ".join((item.get("a10_guard") or {}).get("replaced") or ["nothing"])]
        if item["rows"]:
            lines += ["", "| Row | Eligible creators | Estimate | p | Holm input p | Holm-adjusted p | Verdict | Uninformative |",
                      "|---|---|---|---|---|---|---|---|"]
            for row in item["rows"]:
                first = _first(row.get("estimate"))
                lines.append(f"| {row['row']} | {row.get('eligible_creators')} | {first[0]} {first[1]} | {row.get('p')} | "
                             f"{row.get('holm_input_p')} | {row.get('holm_adjusted_p')} | {row['verdict']} | {row.get('uninformative')} |")
        noted = {key: value for key, value in ((item["result"].get("secondary") or {}).items())
                 if isinstance(value, dict) and (value.get("flag") or ("verdict" in value and value["verdict"] is None and value.get("note")))}
        for key, value in noted.items():
            flag = f"{value['flag']}; " if value.get("flag") else ""
            lines += ["", f"Secondary estimate '{key}': {flag}no verdict. {value.get('note', '')}"]
        tip = item["result"].get("tipping")
        if tip:
            lines += ["", "Tipping points: " + str(tip.get("note", ""))]
            for key, rows in tip.items():
                if key == "note" or not rows:
                    continue
                lines += ["", f"| {key} | " + " | ".join(rows[0].keys()) + " |", "|---|" + "---|" * len(rows[0])]
                for row in rows:
                    lines.append("| | " + " | ".join(str(v) for v in row.values()) + " |")
        lines.append("")
    return "\n".join(lines)


def write(folder, primary, final, holm_table, meta):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    report = build(primary, final, holm_table, meta)
    (folder / "report.json").write_text(json.dumps(report, indent=1, sort_keys=True), encoding="utf-8")
    (folder / "report.md").write_text(markdown(report), encoding="utf-8")
    private = {name: {key: primary[name].get(key) for key in PRIVATE_KEYS if key in primary[name]} for name in sorted(primary)}
    (folder / "report.private.json").write_text(json.dumps(common.short(private), indent=1, sort_keys=True), encoding="utf-8")
    return report
