"""Command line of the hypothesis analysis. Run with python -I from any folder.

    python -I run.py simulate [--quick] [--workers N] [--out DIR] [--expect-fingerprint FP] [--estimate]
        the simulation battery on synthetic creators, in parallel worker processes, with progress and ETA on stderr;
        writes simulation-results.json and simulation-results.md (default: sim_out/ beside this file); the ETA of a running
        battery is kept in simulation-status.json. --expect-fingerprint FP (the task fingerprint that run.py hashes
        prints, in full or its first 12 digits) refuses to start unless the modules of simulate.TASK_MODULES are the
        frozen ones. --estimate prints the planned CPU and wall time on N workers from sim_cost.py and runs nothing
    python -I run.py e2e [--workers N] [--out DIR]
        one synthetic dataset written as label files, then the full analysis through the adapter (every hypothesis,
        every multiverse row, in parallel, with ETA), the report and a determinism check (a second run must match)
    python -I run.py analyse CONFIG.json [--workers N]
        the confirmatory analysis; progress and ETA on stderr and in OUT/analysis-status.json. CONFIG: {"out": dir, "sources": {"primary": {"voice": dir, "asks": dir, "features": dir,
        "forecasts": dir, "content": dir, "titles": file}, "<row name>": {...}}, "gates": {...}, "creator_sd": {...},
        "verification": {"all" or "<H>": {"third_model": ..., "known_answer": ..., "cross_vendor": ...}},
        "asr_model_required": "english_only", "asr_models": file, "holdout_model_crosscheck": {"table": file, "enabled":
        true}}; analyse-config.template.json is the confirmatory template (cross-check on). Real label files are refused
        until freeze2.json matches (adapter.require_permission). The ASR-model rule (adapter.apply_asr_rule) keeps only
        recordings of the required recognizer model in every source; "asr_model_required" defaults to
        constants.ASR_MODEL_REQUIRED and real labels are refused under any other value; "asr_models" is an optional
        per-recording model file; "holdout_model_crosscheck" compares each hold-out recording's model with TABLE's
        resolved model (id and model columns only; refused before freeze 2). The eligible counts and the rule's exclusions
        per group and per label source (every extra multiverse source too) are computed and written (counts.json) before
        any outcome is computed (A10.2, CAL-A9).
    python -I run.py constants [--labels DIR] [--draws N] [--out FILE]
        registry 2026-11-21 06:44 (1): the FREEZE2 constants (H4_YARDSTICK with its middle-model version, H2_LENGTH_BANDS,
        H2_PARTS_RETAINED with its prevalence table) and the A10.7 null means, from labels/seen only (the seen-only path,
        adapter.load_seen_bundle, permitted before freeze 2), printed with counts and derived numbers only. DIR: a folder
        named labels; the default is the production label tree (llm/labels); any other is read only where its seen
        folders hold the synthetic marker (tests)
    python -I run.py hashes
        analysis_code_sha256 (every module) and constants_sha256, the two keys of llm/freeze2.json that describe this code
        (registry 2026-11-21 02:45 and 06:44 (2)), the simulation task fingerprint, and the freeze-2 status
    python -I run.py selftest
        the unit tests in tests/
"""
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from hypotheses import a10_checks  # noqa: E402
from hypotheses import adapter  # noqa: E402
from hypotheses import constants as K  # noqa: E402
from hypotheses import h1_rate, h2_hedging, h4_contraction, h5_world_claims, h6_asks, h9_family  # noqa: E402
from hypotheses import progress  # noqa: E402
from hypotheses import report  # noqa: E402
from hypotheses import verdicts  # noqa: E402
from hypotheses import voice_sets as vs  # noqa: E402

MODULES = {"H1": h1_rate, "H2": h2_hedging, "H4": h4_contraction, "H5": h5_world_claims, "H6": h6_asks, "H9": h9_family}
ALTERNATIVE = dict(K.SIDEDNESS)
TEMPLATE = HERE / "analyse-config.template.json"
_BUNDLES = {}


def option(argv, name, default=None, cast=str):
    return cast(argv[argv.index(name) + 1]) if name in argv else default


# ---------------------------------------------------------------- one analysis task (runs in a worker)

def _bundle(paths_json, rule=None):
    """The bundle of one source under the run's ASR-model rule (cached per worker)."""
    rule = rule or {}
    key = (paths_json, json.dumps(rule, sort_keys=True))
    if key not in _BUNDLES:
        _BUNDLES[key] = adapter.load_bundle(json.loads(paths_json), rule.get("required"), rule.get("models"), rule.get("crosscheck"))
    return _BUNDLES[key]


def asr_rule_of(config):
    """The run's ASR-model rule: "asr_model_required" (default constants.ASR_MODEL_REQUIRED, the lead's decision; null
    switches it off, accepted on synthetic data only), "asr_models" (optional per-recording model file) and
    "holdout_model_crosscheck" (optional; on in the confirmatory template: {"table": TABLE's recordings.csv, "enabled":
    true}; id and model columns only, refused before freeze 2). The adapter refuses real labels under any value but the
    frozen one."""
    rule = {"required": adapter.model_name(config.get("asr_model_required", K.ASR_MODEL_REQUIRED)), "models": config.get("asr_models")}
    check = adapter.crosscheck_spec(config.get("holdout_model_crosscheck"))
    if check:
        rule["crosscheck"] = dict(check, groups=list(check["groups"]))
    return rule


def run_row(task):
    """task: (hypothesis, row name, paths as JSON, options as JSON, settings as JSON). Returns (hypothesis, row, result).
    The option "asr_stratified" runs the row on the recognizer-model-stratified view of the source (registry 03:08)."""
    hypothesis, row, paths_json, options_json, settings_json = task
    options, settings = json.loads(options_json), json.loads(settings_json)
    stratified = bool(options.pop("asr_stratified", False))
    bundle = _bundle(paths_json, settings.get("asr_rule"))
    if stratified:
        bundle = adapter.model_stratified_view(bundle)
    label = (hypothesis, row)
    draws = settings.get("draws", K.BOOTSTRAP_DRAWS)
    permutations = settings.get("permutations", K.PERMUTATION_DRAWS)
    if hypothesis in ("H1", "H4", "H6"):
        # the hypothesis's claimed side (H1, H6: V2 + V3; H4: V2, registry 04:55 (a)) unless the row names it
        how = vs.primary_definition(hypothesis, **{k: (tuple(v) if isinstance(v, list) else v) for k, v in options.items()})
        if hypothesis == "H1":
            result = h1_rate.analyse(bundle, how, label=label, draws=draws)
        elif hypothesis == "H4":
            result = h4_contraction.analyse(bundle, how, yardstick=settings.get("yardstick"), label=label, draws=draws)
        else:
            result = h6_asks.analyse(bundle, how, label=label, draws=draws)
    elif hypothesis == "H2":
        opts = {k: (tuple(v) if isinstance(v, list) else v) for k, v in options.items()}
        if "parts" not in opts and settings.get("parts") is not None:
            opts["parts"] = tuple(settings["parts"])
        result = h2_hedging.analyse(bundle, label=label, draws=draws, permutations=permutations,
                                    bands=tuple(settings["bands"]) if settings.get("bands") else None, **opts)
    elif hypothesis == "H5":
        result = h5_world_claims.analyse(bundle, label=label, draws=draws, **options)
    else:
        opts = {k: (tuple(v) if isinstance(v, list) else v) for k, v in options.items()}
        result = h9_family.analyse(bundle, label=label, draws=draws, permutations=permutations, **opts)
    return hypothesis, row, result


def row_specs(bundle, extra_sources):
    """(hypothesis, row name, source name, options) for the primary source and every extra source."""
    # the large model reads only the adjudicated titles, so it is no source for a whole row
    title_sources = sorted(k for k in (bundle.get("titles") or {}) if not k.startswith("_") and k != "large")
    statements = [st for item in bundle["recordings"] if item.get("forecasts") for st in item["forecasts"]["statements"]]
    fc_sources = sorted({name for st in statements for name in st["parts"]})
    fd_sources = sorted({name for st in statements for name in st["commitment"]})
    routing = any(st.get("routed_final") is not None for st in statements)
    specs = []
    for hypothesis in ("H1", "H4", "H6"):      # claimed side per hypothesis: H1, H6 V2 + V3 (02:55); H4 V2 (04:55 (a))
        for name, how in vs.standard_rows(K.CLAIMED_BY_HYPOTHESIS[hypothesis]):
            specs.append((hypothesis, name, "primary", {k: v for k, v in how.items()}))
    specs += [("H2", name, "primary", opts) for name, opts in h2_hedging.rows(fc_sources, fd_sources, routing)]
    specs += [("H5", name, "primary", opts) for name, opts in h5_world_claims.rows(title_sources or ("final",))]
    specs += [("H9", name, "primary", opts) for name, opts in h9_family.rows(title_sources or ("final",))]
    if "asr_rule" in bundle:                   # the one recognizer-model-stratified sensitivity row (registry 03:08)
        for hypothesis in K.THIS_TRACK:
            specs.append((hypothesis, K.ASR_STRATIFIED_ROW, "primary", {"asr_stratified": True}))
    for source in extra_sources:
        for hypothesis in K.THIS_TRACK:
            specs.append((hypothesis, f"source: {source}", source, {}))
    return specs


def counts(bundle, settings):
    """A10.2 (CAL-A9): eligibility from labels only, before any outcome. H4 counts its embodied primary (V2)."""
    out = {"H1": h1_rate.eligible(bundle, vs.primary_definition("H1")), "H4": h4_contraction.eligible(bundle, vs.primary_definition("H4")),
           "H6": h6_asks.eligible(bundle, vs.primary_definition("H6")), "H5": h5_world_claims.eligible(bundle)}
    bands = settings.get("bands") or K.H2_LENGTH_BANDS
    parts = settings.get("parts") if settings.get("parts") is not None else K.H2_PARTS_RETAINED
    if bands and parts is not None:
        out["H2"] = h2_hedging.eligible(bundle, bands=tuple(bands), parts=tuple(parts))
    out["H9"] = h9_family.eligible(bundle)
    return out


def source_rule_counts(name, paths, rule):
    """The ASR-model rule's counts of one label source (counts only), read under the run's rule before any outcome."""
    loaded = adapter.load_bundle(paths, rule.get("required"), rule.get("models"), rule.get("crosscheck"))
    return dict(loaded["asr_rule"], applied=True) if "asr_rule" in loaded else {"required": None, "applied": False}


def analyse(config, workers):
    sources = config["sources"]
    rule = asr_rule_of(config)
    primary = adapter.load_bundle(sources["primary"], rule["required"], rule["models"], rule.get("crosscheck"))
    synthetic = all(record.get("synthetic") for record in primary["records"])
    settings = {"yardstick": K.H4_YARDSTICK, "bands": K.H2_LENGTH_BANDS, "parts": K.H2_PARTS_RETAINED, "draws": K.BOOTSTRAP_DRAWS,
                "permutations": K.PERMUTATION_DRAWS}
    if config.get("settings"):
        if not synthetic:
            raise PermissionError("settings may be overridden on synthetic data only; real runs use the frozen constants")
        settings.update(config["settings"])
    settings["asr_rule"] = rule                      # every source's bundle is read under the same rule (run_row)
    out_dir = Path(config["out"])
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    eligible = counts(primary, settings)
    detectable = {}
    for hypothesis, elig in eligible.items():
        sd = (config.get("creator_sd") or {}).get(hypothesis)
        # registry 2026-11-21 11:08 (1): H6's note comes from the battery and needs no creator SD
        detectable[hypothesis] = (verdicts.detectable_note(hypothesis, elig["creators"], sd, ALTERNATIVE[hypothesis])
                                  if sd or hypothesis == "H6" else None)
    asr = dict(primary["asr_rule"], applied=True) if "asr_rule" in primary else {"required": None, "applied": False}
    # the rule's exclusion counts of every label source, the extra multiverse sources too, before any outcome
    by_source = {"primary": asr}
    for name in sorted(source for source in sources if source != "primary"):
        by_source[name] = source_rule_counts(name, sources[name], rule)
    (out_dir / "counts.json").write_text(json.dumps({"eligible": eligible, "detectable": detectable, "asr_model_rule": asr,
                                                     "asr_model_rule_by_source": by_source,
                                                     "written_before_outcomes": True}, indent=1, sort_keys=True), encoding="utf-8")
    for name, counted in sorted(by_source.items()):
        print(f"ASR-model rule (before outcomes), source {name}:", counted.get("required"),
              {g: (c["kept"], c["excluded"]) for g, c in sorted((counted.get("by_group") or {}).items())}, file=sys.stderr, flush=True)
    if asr.get("applied"):
        print("model-stratified row (before outcomes):",
              {g: c.get("model_stratified_row_by_model") for g, c in sorted((asr.get("by_group") or {}).items())}, file=sys.stderr, flush=True)
    print("eligible creators (labels only, before outcomes):",
          {h: (e["creators"], e["minimum"], e["determinable"]) for h, e in sorted(eligible.items())}, file=sys.stderr, flush=True)
    null_check = a10_checks.null_means(primary, settings, draws=min(settings["permutations"], 999))
    specs = row_specs(primary, [name for name in sources if name != "primary"])
    tasks = [(h, row, json.dumps(sources[src], sort_keys=True), json.dumps(opts, sort_keys=True), json.dumps(settings, sort_keys=True))
             for h, row, src, opts in specs]
    weight = {"H1": 1.0, "H2": 3.0, "H4": 1.0, "H5": 0.5, "H6": 1.5, "H9": 4.0}
    results, summary = progress.parallel_map(run_row, tasks, workers, "analysis", cost=lambda t: weight[t[0]],
                                             status_path=out_dir / "analysis-status.json")
    primary_results, rows = {}, {}
    for hypothesis, row, result in results:
        if row == "primary":
            primary_results[hypothesis] = result
        rows.setdefault(hypothesis, []).append((row, result))
    final, holm = verdicts.finalise(primary_results, rows, config.get("gates"), config.get("verification"), detectable,
                                    config.get("cross_vendor_voice"))      # VG-6 (registry 2026-11-21 03:21)
    meta = {"title": config.get("title", "analysis"), "synthetic": synthetic, "workers": workers,
            "cross_vendor_voice_VG6": config.get("cross_vendor_voice") or "not entered",
            "seconds": round(time.time() - started, 1), "progress": summary, "settings": settings if synthetic else "frozen constants",
            "asr_model_rule": asr, "asr_model_rule_by_source": by_source, "a10_7_null_means_on_seen_creators": null_check}
    return report.write(out_dir, primary_results, final, holm, meta)


# ---------------------------------------------------------------- the FREEZE2 constants from seen labels (06:44 (1))

def seen_constants(bundle, draws=999):
    """Registry 2026-11-21 06:44 (1): the FREEZE2 constants and the A10.7 null means of a seen-only bundle
    (adapter.load_seen_bundle, read under the ASR-model rule), with counts. Counts, constants and means only: no creator,
    recording or label value is returned."""
    if not bundle.get("seen_only"):
        raise ValueError("the FREEZE2 constants are computed from the seen-only path (adapter.load_seen_bundle)")
    yardstick, yardstick_creators = h4_contraction.yardstick_from_seen(bundle)
    middle, middle_creators = h4_contraction.yardstick_from_seen(bundle, vs.primary_definition("H4", model="middle"))
    bands = h2_hedging.length_bands_from_seen(bundle)
    parts, prevalence, counted = h2_hedging.parts_from_seen(bundle)
    band_statements = sum(1 for item in bundle["recordings"] if item.get("forecasts") for st in item["forecasts"]["statements"]
                          if st["verified"] and not st["duplicate"])
    settings = {"bands": list(bands) if bands else None, "parts": list(parts) if parts is not None else None}
    rule = bundle.get("asr_rule") or {}
    seen_rule = (rule.get("by_group") or {}).get("seen", {})
    return {"FREEZE2": {"H4_YARDSTICK": yardstick, "H2_LENGTH_BANDS": list(bands) if bands else None,
                        "H2_PARTS_RETAINED": list(parts) if parts is not None else None},
            "beside": {"H4_yardstick_middle_model": middle,
                       "H2_part_prevalence": prevalence, "H2_part_prevalence_minimum": K.H2_PART_PREVALENCE_MIN},
            "counts": {"files_read": bundle.get("seen_files"),
                       "recordings": len(bundle["recordings"]),
                       "asr_model_rule": {key: seen_rule.get(key) for key in ("recordings", "kept", "excluded", "excluded_other_model",
                                                                              "excluded_unknown_model", "excluded_conflicting_sources",
                                                                              "creators", "creators_with_no_recording_left")},
                       "creators": len({item["creator"] for item in bundle["recordings"]}),
                       "H4_yardstick_creators": yardstick_creators, "H4_yardstick_middle_model_creators": middle_creators,
                       "H2_band_statements": band_statements, "H2_prevalence_statements": counted},
            "a10_7_null_means_on_seen_creators": a10_checks.null_means(bundle, settings, draws=draws),
            "how": "seen-only path (registry 2026-11-21 06:44 (1)): labels/seen only, every file's group checked first; "
                   "ASR-model rule " + str(rule.get("required")),
            "synthetic": all(record.get("synthetic") for record in bundle["records"])}


def cmd_constants(argv):
    labels = option(argv, "--labels")
    bundle = adapter.load_seen_bundle(Path(labels) if labels else None)
    out = seen_constants(bundle, draws=option(argv, "--draws", 999, int))
    text = json.dumps(out, indent=1, sort_keys=True, default=list)
    if option(argv, "--out"):
        Path(option(argv, "--out")).write_text(text + "\n", encoding="utf-8")
    print(text)


# ---------------------------------------------------------------- commands

def cmd_simulate(argv):
    from hypotheses import simulate
    workers = option(argv, "--workers", progress.default_workers(), int)
    quick = "--quick" in argv
    if option(argv, "--expect-fingerprint"):         # the freeze: refuse before anything is written or run
        simulate.require_fingerprint(option(argv, "--expect-fingerprint"))
    if "--estimate" in argv:
        plan = simulate.plan_estimate(workers, quick=quick)
        plan["wall_clock"] = progress._clock(plan["wall_seconds"])
        print(json.dumps(plan, indent=1, sort_keys=True))
        return
    out_dir = Path(option(argv, "--out", str(HERE / "sim_out")))
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    hashes_at_start = adapter.code_hashes()          # the code the workers load; files edited during a run do not change it
    name = "simulation-results-quick" if quick else "simulation-results"
    checkpoint = None if "--no-checkpoint" in argv else out_dir / (name.replace("results", "checkpoint") + ".jsonl")
    table, summary = simulate.run(workers, quick=quick, status_path=out_dir / (name.replace("results", "status") + ".json"),
                                  checkpoint_path=checkpoint)
    boundary = simulate.boundary_table()
    hashes_at_end = adapter.code_hashes()
    result = {"synthetic": True, "quick": quick, "workers": workers, "seconds": round(time.time() - started, 1), "progress": summary,
              "experiments": table, "boundary": boundary, "code_sha256": hashes_at_start,
              "h9_bootstrap_draws": simulate.H9_BATTERY_BOOTSTRAP_DRAWS,
              "code_changed_during_run": sorted(k for k in set(hashes_at_start) | set(hashes_at_end)
                                                if hashes_at_start.get(k) != hashes_at_end.get(k)),
              "note": "Synthetic creators only. No real label, transcript or API call was used."}
    (out_dir / (name + ".json")).write_text(json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")
    (out_dir / (name + ".md")).write_text(simulation_markdown(result), encoding="utf-8")
    print(json.dumps({"seconds": result["seconds"], "file": str(out_dir / (name + ".json"))}))


def _fmt(value, digits=4):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def simulation_markdown(result):
    lines = ["# Simulation battery (synthetic creators only)", "",
             f"Workers {result['workers']}, wall time {result['seconds']} s, CPU time in tasks {result['progress'].get('cpu_seconds_in_tasks')} s.", "",
             "Null rows: rejection rate of the p that enters Holm, at the first Holm step (0.005) and at 0.05, with the Monte Carlo SE. "
             "Planted rows: mean estimate against the large-sample target (label error included) and the planted value, coverage of the "
             "90% interval used for A5 and of the registered 95% interval, and the share of sets that reach 'supported' at the first Holm step.", "",
             "Guarded columns (A10 guard, registry 03:08): the larger of the registered and the amended p, and support only where both "
             "versions meet the support conditions.", "",
             "Coverage 90%: HKSJ for H1, H2 and H4; for H5 and H6 the interval the MH estimate carries (the wider of the creator-bootstrap "
             "percentile and the jackknife t interval, registry 2026-11-21 04:55 (j)), with the bootstrap percentile alone beside it; the "
             "creator bootstrap for H9 (creators, then recordings, cells re-rarefied in every draw, registry 2026-11-21 06:44 (4); "
             f"{result.get('h9_bootstrap_draws', 'the battery')} draws in the battery). Supported needs, for H5 and H6, both the t "
             "interval on OE and the MH interval to exclude zero (06:44 (5)).", "",
             "| H | scenario | creators | planted | reps | reject 0.005 (SE) | reject 0.05 (SE) | reject 0.005 guarded | reject 0.05 guarded | "
             "mean estimate | target | planted value | coverage 90% | coverage 90% MH bootstrap only | coverage 95% | supported at first step | "
             "supported, both versions |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for row in result["experiments"]:
        lines.append(f"| {row['hypothesis']} | {row['scenario']} | {row['creators']} | {_fmt(row['planted_parameter'])} | {row['reps']} | "
                     f"{_fmt(row['reject_0.005'])} ({_fmt(row['mc_se_0.005'], 2)}) | {_fmt(row['reject_0.05'])} ({_fmt(row['mc_se_0.05'], 2)}) | "
                     f"{_fmt(row.get('reject_0.005_guarded'))} | {_fmt(row.get('reject_0.05_guarded'))} | "
                     f"{_fmt(row['mean_estimate'])} | {_fmt(row['target'])} | {_fmt(row.get('planted_value'))} | {_fmt(row.get('coverage_a5'))} | "
                     f"{_fmt(row.get('coverage_a5_bootstrap_only'))} | {_fmt(row.get('coverage_registered95'))} | "
                     f"{_fmt(row['supported_at_first_holm_step'])} | {_fmt(row.get('supported_at_first_holm_step_guarded'))} |")
    h6_rows = [row for row in result["experiments"] if row.get("hypothesis") == "H6"]
    if h6_rows:
        from hypotheses import simulate
        draws = f"{simulate.H6_BATTERY_REFERENCE_DRAWS:,}"
        # registry 2026-11-21 11:08 (1): the amended p and, on the same sets, its two halves and the references it replaced
        columns = (("amended p", ""), ("cluster p", "_cluster_conditional"), ("sign-flip of OE", "_signflip_oe"),
                   ("ask-level p", "_ask_level_conditional_0919"), ("pooled OE", "_pooled_oe_before_0644"),
                   ("amended p, window 1 (11:08)", "_amended_window_1_1108"), ("amended p, window 10", "_amended_window_10"),
                   ("guarded", "_guarded"))
        lines += ["", "## H6: the amended p, its two halves and the references it replaced", "",
                  "Same sets, rejection rates at 0.005 / 0.05. Amended p (registry 2026-11-21 11:08 (1), the row's p in the table "
                  "above): the larger of the cluster p and the sign-flip of OE. Cluster p: the conditional Monte Carlo "
                  "reference that draws each cluster of asks (asks within 5 units of each other, chaining, registry "
                  "2026-11-21 12:52 (1)) as one unit with the recording's claimed share (11:08 (1)). Sign-flip of OE: the "
                  "creator sign-flip of the OE centred per recording (06:44 (3) to 09:19 (1)). Ask-level p: the "
                  "conditional reference that draws asks one by one (09:19 (1) to 11:08 (1)). Pooled OE: the sign-flip of "
                  "CAL-A11's pooled OE (before 06:44 (3)). Amended p, window 1 (11:08) and window 10: the amended p with "
                  "the clusters of 11:08 (the same, overlapping or adjacent units) and of the 10-unit sensitivity row "
                  "(12:52 (1)). Guarded: "
                  f"the larger of the amended and the registered p (A10 guard). {draws} Monte Carlo draws of each "
                  "conditional reference in the battery (99,999 in the analysis). Scenarios: null_heterogeneous, ask "
                  "rates that differ between a creator's recordings with their claimed share; null_sparse_low_share, "
                  "claimed shares below one half and "
                  "1 to 3 asks a creator; null_burst, 1 or 2 bursts of 2 to 4 asks a creator in one voice at claimed shares "
                  "0.3 to 0.7; null_gapped, one burst of 2 to 4 asks a creator in one voice whose consecutive asks lie 1 "
                  "to 3 units apart, at claimed shares below one half (12:52 (1)); no difference inside any recording in "
                  "the null scenarios.", "",
                  "| scenario | creators | reps | " + " | ".join(name for name, _ in columns) + " | mean largest cluster |",
                  "|---|---|---|" + "---|" * len(columns) + "---|"]
        for row in h6_rows:
            cells = [f"{_fmt(row.get('reject_0.005' + key))} / {_fmt(row.get('reject_0.05' + key))}" for _, key in columns]
            lines.append(f"| {row['scenario']} | {row['creators']} | {row['reps']} | " + " | ".join(cells)
                         + f" | {_fmt(row.get('mean_largest_cluster'), 3)} |")
    lines += ["", "## The 'not determinable' boundary", "",
              "| H | generated | eligible | minimum | determinable | raw p | registered-version p | Holm input p | verdict | uninformative |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for row in result["boundary"]:
        lines.append(f"| {row['hypothesis']} | {row['generated_creators']} | {row['eligible']} | {row['minimum']} | {row['determinable']} | "
                     f"{_fmt(row['raw_p'])} | {_fmt(row.get('registered_version_p'))} | {_fmt(row['holm_input_p'])} | {row['verdict']} | "
                     f"{row.get('uninformative')} |")
    return "\n".join(lines) + "\n"


def plant_asr_models(files):
    """The ASR-model rule in the end-to-end test: of the synthetic recordings (all from the English-only model), the
    first hold-out recording is given another model, the last hold-out creator's first recording two sources that
    disagree (voice English-only, asks another model), and the first seen recording no model. Returns the counts
    counts.json must show."""
    asks = {record["audio"]: record for record in files["asks"]}

    def set_model(record, model):
        info = {key: value for key, value in (record.get("info") or {}).items() if key != "model_role"}
        record["info"] = dict(info, model_role=model) if model else info

    holdout = [record for record in files["voice"] if record["group"] == "holdout"]
    seen = [record for record in files["voice"] if record["group"] == "seen"]
    other, conflict = holdout[0], next(record for record in holdout if record["creator"] == holdout[-1]["creator"])
    for record, voice_model, asks_model in ((other, "multilingual", "multilingual"), (conflict, K.ASR_MODEL_REQUIRED, "multilingual"),
                                            (seen[0], None, None)):
        set_model(record, voice_model)
        if record["audio"] in asks:
            set_model(asks[record["audio"]], asks_model)
    return {"holdout": {"excluded_other_model": 1, "excluded_conflicting_sources": 1, "excluded_unknown_model": 0,
                        "other_models": {"multilingual": 1}, "kept": len(holdout) - 2},
            "seen": {"excluded_other_model": 0, "excluded_conflicting_sources": 0, "excluded_unknown_model": 1,
                     "other_models": {}, "kept": len(seen) - 1}}


def plant_crosscheck(files, folder):
    """The hold-out cross-check in the end-to-end test: a synthetic TABLE file (video_id and asr_model_resolved, plus a
    column the reader must ignore) that lists every hold-out recording with its label model, except that one
    English-only recording is listed under another model (excluded as a mismatch) and one is missing (kept, counted).
    Returns the path and the cross-check counts counts.json must show."""
    holdout = [record for record in files["voice"] if record["group"] == "holdout"]
    asks = {record["audio"]: record for record in files["asks"]}
    english = [record for record in holdout if (record.get("info") or {}).get("model_role") == K.ASR_MODEL_REQUIRED
               and (asks.get(record["audio"], {}).get("info") or {}).get("model_role") in (None, K.ASR_MODEL_REQUIRED)]
    mismatch, missing = english[1], english[2]
    lines = ["# synthetic table for the end-to-end test", "video_id,group,asr_model_resolved,ignored"]
    for record in holdout:
        if record is missing:
            continue
        model = (record.get("info") or {}).get("model_role") or ""
        listed = "multilingual_inferred" if record is mismatch else (model or K.ASR_MODEL_REQUIRED)
        lines.append(f"{record['video_id']},holdout,{listed},x")
    path = Path(folder) / "table-recordings.synthetic.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path, {"checked": len(holdout), "not_in_table": 1, "excluded_crosscheck_mismatch": 1}


def write_extra_source(files, folder, paths):
    """A second label source for the multiverse (an altered input stands in): the voice files with the small model as
    the record on the hold-out, and one more hold-out recording whose voice file states another model than its asks
    file (excluded as conflicting). Returns its paths and the extra exclusion counts.json must show for it."""
    from hypotheses import simulate
    target = Path(folder) / "voice-altered"
    target.mkdir(parents=True, exist_ok=True)
    simulate.mark_synthetic(target)                  # the permission check opens only marked folders before freeze 2
    holdout = [record for record in files["voice"] if record["group"] == "holdout"]
    changed = holdout[3]["audio"]
    for record in files["voice"]:
        copy = json.loads(json.dumps(record))
        if copy["group"] == "holdout":
            copy["label_of_record"] = "small"
        if copy["audio"] == changed:
            copy["info"] = dict(copy.get("info") or {}, model_role="multilingual")
        (target / (copy["audio"] + ".json")).write_text(json.dumps(copy), encoding="utf-8")
    return dict(paths, voice=str(target)), {"excluded_conflicting_sources": 1}


def cmd_e2e(argv):
    from hypotheses import simulate
    workers = option(argv, "--workers", progress.default_workers(8), int)
    out_dir = Path(option(argv, "--out", str(HERE / "sim_out" / "e2e")))
    effects = {"mu1": -0.15, "mu4": 1.0, "rr": 0.25, "beta": -0.7, "theta": 0.8, "h9_content": 0.12, "exact": True}
    bundle, files = simulate.cohort(20261120, 17, effects, n_seen=40, raw=True)
    planted_asr = plant_asr_models(files)
    # the FREEZE2 constants come from seen recordings under the same ASR-model rule, through the seen-only path of
    # registry 2026-11-21 06:44 (1): the synthetic seen cohort is written as labels/seen/<instrument> and read back by
    # adapter.load_seen_bundle (run.py constants), and must give what the in-memory cohort gives
    seen_memory, seen_files = simulate.cohort(20261121, 0, {"exact": True}, n_seen=40, parts=("voice", "features", "forecasts"),
                                              raw=True)
    seen_only = adapter.apply_asr_rule(seen_memory, K.ASR_MODEL_REQUIRED)
    yardstick, _ = h4_contraction.yardstick_from_seen(seen_only)
    bands = h2_hedging.length_bands_from_seen(seen_only)
    parts, prevalence, _ = h2_hedging.parts_from_seen(seen_only)
    seen_tree = out_dir / "seen-tree" / "labels"
    simulate.write_files(seen_tree / adapter.SEEN_GROUP, seen_files)
    from_path = seen_constants(adapter.load_seen_bundle(seen_tree), draws=99)
    seen_path_check = {"files_read": from_path["counts"]["files_read"],
                       "constants_match_in_memory": from_path["FREEZE2"] == {"H4_YARDSTICK": yardstick, "H2_LENGTH_BANDS": list(bands),
                                                                              "H2_PARTS_RETAINED": list(parts)}}
    paths = simulate.write_files(out_dir / "labels", files)
    table, planted_cross = plant_crosscheck(files, out_dir / "labels")
    extra_paths, planted_extra = write_extra_source(files, out_dir / "labels", paths)
    config = {"out": str(out_dir / "report"), "title": "end-to-end, synthetic",
              "sources": {"primary": paths, "altered input: voice record small (synthetic)": extra_paths},
              "settings": {"yardstick": yardstick, "bands": list(bands), "parts": list(parts), "draws": 999, "permutations": 1999},
              "creator_sd": {"H1": 0.10, "H2": 0.15, "H4": 0.8}, "asr_model_required": K.ASR_MODEL_REQUIRED,
              "holdout_model_crosscheck": {"table": str(table), "enabled": True, "synthetic": True},
              "verification": {"all": {"third_model": "synthetic run: not computed", "known_answer": "synthetic run: not computed",
                                       "cross_vendor": "synthetic run: not computed"}}}
    report_one = analyse(config, workers)
    config["out"] = str(out_dir / "report-repeat")
    report_two = analyse(config, max(1, workers // 2))
    strip = lambda r: json.dumps({k: v for k, v in r.items() if k != "meta"}, sort_keys=True)
    same = strip(report_one) == strip(report_two)
    summary = {h: {"verdict": item["verdict"], "verdict_statement": item.get("verdict_statement"),
                   "eligible": item["result"]["eligibility"]["creators"], "estimate": item["result"].get("estimate"),
                   "rows": len(item["rows"]), "robust": item["robust_to_the_labeller"], "uninformative": item.get("uninformative"),
                   "p_amended": item.get("holm_input_p_amended"), "p_registered": item.get("holm_input_p_registered"),
                   "holm_input_p": item.get("holm_input_p"),
                   "registered_verdict": ((item.get("versions") or {}).get("registered") or {}).get("verdict"),
                   "amended_verdict": ((item.get("versions") or {}).get("amended") or {}).get("verdict")}
               for h, item in report_one["hypotheses"].items()}
    written = json.loads((out_dir / "report" / "counts.json").read_text(encoding="utf-8"))
    counted = written["asr_model_rule"]
    counted_asr = {group: {key: counted["by_group"].get(group, {}).get(key) for key in planted_asr[group]} for group in planted_asr}
    # the cross-check moves one more hold-out recording out of "kept"
    planted_asr = json.loads(json.dumps(planted_asr))
    planted_asr["holdout"]["kept"] -= planted_cross["excluded_crosscheck_mismatch"]
    holdout_counts = counted["by_group"].get("holdout", {})
    cross = holdout_counts.get("crosscheck", {})
    cross_counted = {"checked": cross.get("checked"), "not_in_table": cross.get("not_in_table"),
                     "excluded_crosscheck_mismatch": holdout_counts.get("excluded_crosscheck_mismatch")}
    # the model-stratified row (registry 03:08): the kept recordings plus the other-model and unknown-model ones; the
    # conflicting one and the cross-check mismatch stay out
    stratified_planted = {group: planted_asr[group]["kept"] + planted_asr[group]["excluded_other_model"]
                          + planted_asr[group]["excluded_unknown_model"] for group in planted_asr}
    stratified_counted = {group: counted["by_group"].get(group, {}).get("in_model_stratified_row") for group in planted_asr}
    stratified_rows = {h: next(({"verdict": row["verdict"], "eligible_creators": row.get("eligible_creators"),
                                 "primary_eligible": item["result"]["eligibility"]["creators"]}
                                for row in item["rows"] if row["row"] == K.ASR_STRATIFIED_ROW), None)
                       for h, item in report_one["hypotheses"].items()}
    by_source = written.get("asr_model_rule_by_source", {})
    extra = by_source.get("altered input: voice record small (synthetic)", {}).get("by_group", {}).get("holdout", {})
    extra_ok = (extra.get("excluded_conflicting_sources") == holdout_counts.get("excluded_conflicting_sources", 0)
                + planted_extra["excluded_conflicting_sources"])
    texts = (out_dir / "report" / "report.json").read_text(encoding="utf-8") + (out_dir / "report" / "report.md").read_text(encoding="utf-8")
    h2 = report_one["hypotheses"].get("H2", {})
    h5 = report_one["hypotheses"].get("H5", {})
    out = {"planted": effects, "yardstick": yardstick, "bands": bands, "h2_parts_retained": parts, "h2_part_prevalence": prevalence,
           "seen_only_path": seen_path_check, "summary": summary,
           "asr_model_rule": {"required": counted.get("required"), "planted": planted_asr, "counted": counted_asr,
                              "counts_match_the_plant": counted_asr == planted_asr},
           "holdout_crosscheck": {"planted": planted_cross, "counted": cross_counted, "counts_match_the_plant": cross_counted == planted_cross},
           "model_stratified_row": {"planted_recordings": stratified_planted, "counted_recordings": stratified_counted,
                                    "counts_match_the_plant": stratified_planted == stratified_counted,
                                    "row_in_every_hypothesis": all(stratified_rows.values()), "rows": stratified_rows},
           "counts_by_source": {"sources": sorted(by_source), "extra_source_exclusion_matches_the_plant": extra_ok},
           "h2_flagged_statements": (h2.get("result") or {}).get("eligibility", {}).get("flagged_statements"),
           "h5_self_naming_exclusion": (h5.get("result") or {}).get("eligibility", {}).get("self_naming_exclusion"),
           "the_word_validated_absent": "validat" not in texts.lower(),
           "a10_7_null_means": report_one["meta"].get("a10_7_null_means_on_seen_creators"),
           "identical_on_repeat_with_other_worker_count": same, "seconds": report_one["meta"]["seconds"]}
    (out_dir / "e2e-summary.json").write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps(out, indent=1, sort_keys=True))


def main(argv):
    command = argv[0] if argv else ""
    if command == "simulate":
        cmd_simulate(argv[1:])
    elif command == "e2e":
        cmd_e2e(argv[1:])
    elif command == "analyse":
        config = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        analyse(config, option(argv, "--workers", progress.default_workers(8), int))
    elif command == "constants":
        cmd_constants(argv[1:])
    elif command == "hashes":
        from hypotheses import simulate
        print(json.dumps(adapter.freeze2_entry(), indent=1, sort_keys=True))
        print("simulation task fingerprint (simulate.TASK_MODULES; run.py simulate --expect-fingerprint):",
              simulate.task_fingerprint())
        print("freeze 2 status (llm/freeze2.json):", adapter.freeze2_problem() or "matches this code")
    elif command == "selftest":
        import unittest
        suite = unittest.defaultTestLoader.discover(str(HERE / "tests"), top_level_dir=str(HERE.parent))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
