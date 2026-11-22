"""The one module that reads label files. Every other module works on the normalised records built here.

Formats: llm/design/label-files.md (the data dictionary written by produce.py's freeze integration, 2026-11-21), the
contract between labelling and analysis. The earlier pilot layouts are still read, so that old synthetic files and the
pilot files keep working, but the production layouts below are the ones the confirmatory run reads.
  voice     labels/<group>/voice/<audio>.json (produce.voice_record). Per unit: id, first, last, n_words, map, small and
            middle views {label, label_b, detail, cue, flags, own_broad} (None where that model did not label), and the
            label of record; per recording the map fields (format, claimant, main_kind, opening_end_unit,
            closing_start_unit) and label_of_record ("middle" on hold-out and other, "small" on seen).
  asks      labels/<group>/asks/<audio>.json (produce.run_asks): "asks" with first_unit, last_unit, class, final (ask,
            not_ask, unclear, unchecked), final_class, final_from, final_small_fallback.
  forecasts labels/<group>/forecasts/<audio>.json: "statements" with key, verified, duplicate, statement_words, markers,
            coded, inclusion_p (weights 1 / p), fc (record: middle model; {values, where} or {failed}), fc_second (the
            small model, read here as the source "small"), fd (commitment: committed true/false/null, four_way). Other
            keys fc_<name> / fd_<name> (robustness rows written beside the record) are further sources. The pilot mapping
            {audio: {"statements": [...]}} and valve_p / candidate_p are still read.
  sentences labels/<group>/sentences/<audio>.json: "units" {unit id: {primary, secondary, group, weight} or {failed,
            weight}}, coded_whole (weights are words), too_short, points. Config key "sentences" (or the older "content").
  titles    labels/<group>/titles/<creator file>.json, one per creator: "titles" entries with video_id, audio, primary
            (middle model), second (small model), large (where adjudicated), record (the code of record: the large
            model's where adjudicated and valid, else the middle model's), record_from. Read as the sources "final"
            (record), "middle", "small" and "large". Config key "titles": that folder (or one pilot file
            {"final" | "middle" | "small" | "large": {video id: reading}}).
  features  this package's features.py: one JSON per recording with per-unit timing, syllables, letters and contraction
            counts, and per-recording token counts for H9 (README, "Feature files").

Files that label-files.md says never to analyse are refused: a real file with "smoke": true, a non-null "run_limit", or
a null "frozen_utc" (smoke and limited runs; files from labels-smoke/).

Registry 2026-11-21 12:52 (2) and (4), in the analysis (the instrument is frozen and unchanged): asks of one class whose
unit ranges overlap are counted once (merge_overlapping_asks, in parse_asks; each asks record carries the counts as
"ask_overlaps", summed per group by ask_overlap_counts for counts.json); and a bundle whose feature files carry more
than one feature_version is refused, naming the versions (require_one_feature_version, in bundle).

Recognizer (ASR) model: every parsed record carries "asr_model", the model its file states (info.model_role, which
produce.py copies from the bundle's provenance compute.text_model_role, the same value the run report's ledger holds;
None where the file states none). apply_asr_rule keeps only the recordings whose resolved model is the required one
(constants.ASR_MODEL_REQUIRED) and counts the others per group; load_bundle refuses to return real records without it.
The optional hold-out cross-check (crosscheck) compares each hold-out recording's model with TABLE's resolved model,
reading the id and model columns only, and only after freeze 2.

Wording rules (registry 02:50, M9; wording.py): a forecast statement carries "shared_wording", the ids of the scenario and
withdrawal patterns found in its wording (H2's flag); a voice unit view carries its span's cue (type, unit) for H5's
self-naming exclusion; a feature unit may carry "self_name" (features.py's fallback pattern list). Only ids and flags are
kept, never the wording.

Guard (rule against estimates during development): a record read from a file that does not carry "synthetic": true is
real. require_permission() refuses real records unless the freeze-2 record passes (freeze2_problem) and the FREEZE2
constants are set. Nothing here prints or returns text from a label file.
Freeze 2 (registry 2026-11-21 02:45 and 06:44 (2)): one record, llm/freeze2.json (FREEZE2), with the six keys of 02:45
(FREEZE2_KEYS, as produce.py's fc_common.FREEZE2_KEYS); produce.freeze2_problem checks it for the label side and
freeze2_problem below for this code: every key present, analysis_code_sha256 covers every module of this folder with
its current hash, constants_sha256 is the hash of constants.py; a record that lacks a key fails closed. No second
record beside the modules is read.
Registry 2026-11-21 04:55 (f): the permission check runs before any file is opened (open_problem). Before freeze 2 a
label file, a per-recording model file or TABLE's file is opened only from a folder that holds the marker the synthetic
generator writes (SYNTHETIC_MARKER), never from labels/holdout or labels/other (marked or not). A label file in a marked
folder that is not marked "synthetic": true is refused as soon as it is parsed: only its markers are read first
(not_for_analysis reads "synthetic", "smoke", "run_limit" and "frozen_utc"), and no label field of it is read. Per-
recording model files and TABLE's CSV carry no synthetic mark; only their folder's marker gates them. Every loader below
calls the check (json_files before a folder is listed, read_json before a file is opened, load_model_map and the
cross-check before their files are opened); load_bundle computes the freeze-2 status once and passes it on.
Seen-only path (registry 2026-11-21 06:44 (1)): before freeze 2, load_seen_bundle opens labels/seen of the production
label tree only (PRODUCTION_LABELS; seen_open_problem resolves links and refuses labels/holdout, labels/other and every
other path before a folder is listed or a file opened), and refuses a file whose group field is not "seen" before any
other field of it is read (read_seen_json). It serves the FREEZE2 constants, the A10.7 null-mean check and CAL part (f)
(run.py constants); no hypothesis estimate reads it (they read the hold-out only, common.confirmatory).

Recognizer-model-stratified row (registry 03:08; 04:55 (b)): apply_asr_rule also keeps, beside the primary list, the
recordings of another stated model and of unknown model (conflicting sources and cross-check mismatches stay out), each
tagged with its model; model_stratified_view() gives the bundle of that one sensitivity row.
"""
import csv
import hashlib
import json
from pathlib import Path
import re

from . import constants as K
from . import wording

HERE = Path(__file__).resolve().parent
# The run's private labelling folder (produce.py's llm folder; label-files.md). Freeze 2 is one record there (registry
# 2026-11-21 06:44 (2)); the production label tree is llm/labels/<group>/<instrument>/.
LLM = Path.home() / "et-channelers-private" / "provisioning" / "claude-cohort-asr-20261120-v1" / "llm"
FREEZE2 = LLM / "freeze2.json"
PRODUCTION_LABELS = LLM / "labels"
# The six keys of the freeze-2 record (registry 2026-11-21 02:45; produce.py's fc_common.FREEZE2_KEYS).
FREEZE2_KEYS = ("freeze1_frozen_utc", "sha256", "analysis_code_sha256", "constants_sha256", "registry_commit", "written_at_utc")
HEX64, COMMIT = re.compile(r"[0-9a-f]{64}"), re.compile(r"[0-9a-f]{7,40}")


# ---------------------------------------------------------------- guard

def code_files():
    """The package's code files that freeze 2 hashes (tests and outputs excluded)."""
    return sorted(path.name for path in HERE.glob("*.py"))


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_hashes():
    return {name: _sha(HERE / name) for name in code_files()}


def freeze2_entry():
    """The two keys of the freeze-2 record that describe this code, as run.py hashes prints them for llm/freeze2.json:
    analysis_code_sha256 ({module: sha256}, every .py file of this folder) and constants_sha256 (constants.py)."""
    return {"analysis_code_sha256": code_hashes(), "constants_sha256": _sha(HERE / "constants.py")}


def freeze2_record_problem(record):
    """None if the record holds the six keys of registry 2026-11-21 02:45 in their forms, else what is wrong (fails
    closed: a missing or empty key is a problem)."""
    if not isinstance(record, dict):
        return "freeze2.json is not a JSON object with the keys " + ", ".join(FREEZE2_KEYS)
    missing = [key for key in FREEZE2_KEYS if not record.get(key)]
    if missing:
        return ("freeze2.json lacks " + ", ".join(missing) + " (the freeze-2 record of registry 2026-11-21 02:45 holds "
                + ", ".join(FREEZE2_KEYS) + ")")
    for key in ("sha256", "analysis_code_sha256"):
        if not isinstance(record[key], dict):
            return f"freeze2.json lacks {key} as a dict ({{path: sha256}})"
    if not HEX64.fullmatch(str(record["constants_sha256"])):
        return "freeze2.json: constants_sha256 is not a sha256"
    if not COMMIT.fullmatch(str(record["registry_commit"])):
        return "freeze2.json: registry_commit is not a commit hash (7 to 40 hexadecimal digits)"
    return None


def freeze2_problem(path=None):
    """None if freeze 2 holds for this code, else what is wrong. The one record llm/freeze2.json (registry 2026-11-21
    06:44 (2)): the six keys present (freeze2_record_problem); analysis_code_sha256 ({path: sha256}, a relative path read
    under this folder, as produce.freeze2_problem reads it) lists every module of this folder and every listed file still
    has its hash; constants_sha256 is the hash of constants.py as it is now; and the FREEZE2 constants are set. The other
    keys (the llm file hashes, freeze 1, the registry commit) are produce.freeze2_problem's, which gates every hold-out
    label; this check reads only this record. path: another record (tests)."""
    path = Path(path) if path is not None else FREEZE2
    if not path.is_file():
        return "llm/freeze2.json does not exist (freeze 2 has not been entered)"
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return "llm/freeze2.json is not JSON"
    problem = freeze2_record_problem(record)
    if problem:
        return problem
    table = record["analysis_code_sha256"]
    target = {name: (Path(name) if Path(name).is_absolute() else HERE / name) for name in table}
    changed = sorted(str(name) for name, value in table.items() if not target[name].is_file() or _sha(target[name]) != value)
    if changed:
        return "changed since freeze 2 (analysis_code_sha256): " + ", ".join(changed)
    listed = {item.resolve() for item in target.values()}
    uncovered = [name for name in code_files() if (HERE / name).resolve() not in listed]
    if uncovered:
        return "freeze2.json does not hash these modules (analysis_code_sha256): " + ", ".join(uncovered)
    if _sha(HERE / "constants.py") != record["constants_sha256"]:
        return "freeze2.json: constants_sha256 is not the sha256 of constants.py as it is now"
    if K.H4_YARDSTICK is None or K.H2_LENGTH_BANDS is None or K.H2_PARTS_RETAINED is None:
        return "FREEZE2 constants are not set (H4_YARDSTICK, H2_LENGTH_BANDS, H2_PARTS_RETAINED)"
    return None


def require_permission(records):
    real = [record for record in records if not record.get("synthetic")]
    if not real:
        return
    problem = freeze2_problem()
    if problem:
        raise PermissionError("rule against estimates during development: no hypothesis quantity on real labels before "
                              "freeze 2 (" + problem + ")")


# ---------------------------------------------------------------- the permission check before a file is opened

SYNTHETIC_MARKER = "SYNTHETIC-LABELS.json"   # written by simulate.mark_synthetic beside synthetic files only
ASK = object()                               # sentinel: compute the freeze-2 status here
PRODUCTION_GROUPS = ("holdout", "other")     # labels/<group>/ of label-files.md that stay closed before freeze 2


def synthetic_folder(folder):
    """True where the folder holds the synthetic generator's marker ({"synthetic": true}). Only the marker is read."""
    marker = Path(folder) / SYNTHETIC_MARKER
    if not marker.is_file():
        return False
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except ValueError:
        return False
    return isinstance(data, dict) and data.get("synthetic") is True


def production_tree(path):
    """True for a path inside labels/holdout or labels/other (the production layout of label-files.md)."""
    parts = [part.lower() for part in Path(path).resolve().parts]
    return any(a == "labels" and b in PRODUCTION_GROUPS for a, b in zip(parts, parts[1:]))


def open_problem(path, problem=ASK):
    """The permission check that runs before a file is opened (registry 2026-11-21 04:55 (f)); None if the file (or the
    folder, before it is listed) may be opened. After freeze 2 (freeze2.json matches the code and the FREEZE2 constants
    are set) everything may be opened. Before it, only files in a folder that holds the synthetic marker, and never a
    path under labels/holdout or labels/other. problem: the freeze-2 status if the caller has it (None: freeze 2 holds)."""
    problem = freeze2_problem() if problem is ASK else problem
    if problem is None:
        return None
    path = Path(path)
    if production_tree(path):
        return f"{path.name} lies under labels/holdout or labels/other, which stay closed until freeze 2 ({problem})"
    folder = path if path.is_dir() else path.parent
    if not synthetic_folder(folder):
        return f"{path.name}: its folder holds no synthetic marker, and freeze 2 has not been entered ({problem})"
    return None


def require_open_permission(path, problem=ASK):
    reason = open_problem(path, problem)
    if reason:
        raise PermissionError("rule against estimates during development: the permission check refuses to open "
                              + reason)


# ---------------------------------------------------------------- files

def not_for_analysis(data):
    """label-files.md: smoke runs, limited runs and files without a freeze record are never analysed. Synthetic files
    are exempt (they carry no freeze record)."""
    if not isinstance(data, dict) or data.get("synthetic"):
        return None
    if data.get("smoke"):
        return "a smoke run's file"
    if data.get("run_limit") is not None:
        return "a limited run's file (run_limit set)"
    if "frozen_utc" in data and not data.get("frozen_utc"):
        return "a file without a freeze 1 record (frozen_utc null)"
    return None


def read_json(path, problem=ASK):
    """One label file, after the permission check (open_problem). Before freeze 2 a file that is not marked synthetic is
    refused as soon as it is parsed: only its markers are read first (not_for_analysis: "synthetic", "smoke", "run_limit",
    "frozen_utc"), no label field of it."""
    problem = freeze2_problem() if problem is ASK else problem
    require_open_permission(path, problem)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    refused = not_for_analysis(data)
    if refused:
        raise ValueError(f"refused: {Path(path).name} is {refused}; label-files.md says never to analyse it")
    if problem is not None and not (isinstance(data, dict) and data.get("synthetic")):
        raise PermissionError(f"rule against estimates during development: {Path(path).name} is not marked synthetic and "
                              f"freeze 2 has not been entered ({problem})")
    return data


def json_files(folder, problem=ASK):
    """The JSON files of a folder, or of a list of folders (labels/holdout/<instrument> and labels/seen/<instrument>);
    the permission check runs before a folder is listed. The synthetic marker is not a label file."""
    if isinstance(folder, (list, tuple)):
        problem = freeze2_problem() if problem is ASK else problem
        return [path for item in folder for path in json_files(item, problem)]
    folder = Path(folder)
    if not folder.is_dir():
        return []
    require_open_permission(folder, problem)
    return sorted(path for path in folder.glob("*.json") if path.is_file() and path.name != SYNTHETIC_MARKER)


# ---------------------------------------------------------------- recognizer (ASR) model of a transcript

NOT_STATED = ("", "none", "null", "not_recorded", "unknown")     # values that name no model
UNKNOWN_MODEL, CONFLICTING_MODELS = "unknown", "conflict"


def model_name(value):
    """A stated recognizer model in lower case, or None for a value that states none."""
    if value is None or isinstance(value, (dict, list)):
        return None
    name = str(value).strip().lower()
    return None if name in NOT_STATED else name


def asr_model_of(data):
    """The recognizer model a file states for its transcript, or None: an explicit asr_model_resolved or asr_model,
    else info.model_role (label files: the bundle's compute.text_model_role; "english_only" for the run's English-only
    model, empty where the bundle names no role)."""
    if not isinstance(data, dict):
        return None
    info = data.get("info") if isinstance(data.get("info"), dict) else {}
    for value in (data.get("asr_model_resolved"), data.get("asr_model"), info.get("asr_model_resolved"), info.get("model_role")):
        if model_name(value):
            return model_name(value)
    return None


# ---------------------------------------------------------------- voice

def _cue(value):
    """The cue of the unit's span as voice.py writes it ([cue type, cue unit]); None where the file holds none."""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            return (str(value[0]), int(value[1] or 0))
        except (TypeError, ValueError):
            return None
    return None


def _view(view):
    if view is None:
        return None
    return {"A": view["label"], "B": view["label_b"], "detail": view.get("detail", "none"), "own_broad": bool(view["own_broad"]),
            "flags": sorted(view.get("flags") or []), "cue": _cue(view.get("cue"))}


def parse_voice(data):
    record_model = data.get("label_of_record") or ("small" if data.get("group") == "seen" else "middle")
    mapped = data.get("map") or {}
    units = []
    for unit in data["units"]:
        units.append({"id": int(unit["id"]), "first": unit.get("first"), "last": unit.get("last"), "n_words": int(unit["n_words"]),
                      "labels": {"small": _view(unit.get("small")), "middle": _view(unit.get("middle"))}})
    return {"kind": "voice", "audio": data["audio"], "creator": data["creator"], "video_id": data.get("video_id"),
            "group": data.get("group"), "language": (data.get("info") or {}).get("language", "en"),
            "publisher_audio": bool(data.get("publisher_audio")), "words": data.get("words"),
            "format": mapped.get("format"), "claimant": mapped.get("claimant"), "main_kind": mapped.get("main_kind"),
            "opening_end_unit": mapped.get("opening_end_unit"), "closing_start_unit": mapped.get("closing_start_unit"),
            "label_of_record": record_model, "units": units, "asr_model": asr_model_of(data), "synthetic": bool(data.get("synthetic"))}


def load_voice(folder, problem=ASK):
    problem = freeze2_problem() if problem is ASK else problem
    return [parse_voice(read_json(path, problem)) for path in json_files(folder, problem)]


# ---------------------------------------------------------------- asks

# Registry 2026-11-21 12:52 (2): the verdict a merged ask carries is its members' first in this order (an ask if any
# member is one; unknown if any member's check failed; then unclear; then not_ask; any other value last).
MERGED_VERDICT_ORDER = ("ask", "unchecked", "unclear", "not_ask")
OVERLAP_COUNT_KEYS = ("asks_as_filed", "asks_counted", "asks_merged_away", "groups", "groups_on_one_range",
                      "groups_on_overlapping_ranges", "groups_with_two_or_more_final_asks")


def _verdict_rank(verdict):
    return MERGED_VERDICT_ORDER.index(verdict) if verdict in MERGED_VERDICT_ORDER else len(MERGED_VERDICT_ORDER)


def merge_overlapping_asks(asks):
    """Registry 2026-11-21 12:52 (2): asks of one class whose unit ranges overlap count once. The find is the union of two
    draws (asks.py, FIND_DRAWS), and two draws can return one ask with different unit ranges (10..10 and 10..11), which
    the frozen instrument keeps apart; the analysis, not the instrument, counts such asks once, so T, a, b, the MH strata
    and H6's clusters count them once. The class is the candidate's class ("class"; final_class where it has none); ranges
    overlap when they share a unit, and overlaps chain (10..11, 11..12 and 12..12 are one ask). CHOICE (the decision's
    words, not its example): two asks of one class on the same range overlap too, so the instrument's "two offers of one
    class" on one range (a draw that returns them twice) count once as well; the check reads a range once and cannot
    tell them apart. The merged ask spans the union of the ranges and carries its members' first verdict in
    MERGED_VERDICT_ORDER (an ask if any member is one, with that member's final_class and final_from); where it is
    "unchecked", the small model's fallback of an unchecked member, an ask of the class first. So under the primary rule
    and under the fallback row the merged ask counts exactly when one of its members would. Asks without a class are
    never merged. Returns (asks in the order of each group's first member, counts with no ids: OVERLAP_COUNT_KEYS and
    groups_by_class)."""
    by_class, groups = {}, []
    for index, ask in enumerate(asks):
        kind = ask.get("class") or ask.get("final_class")
        if kind is None:
            groups.append([index])
        else:
            by_class.setdefault(kind, []).append(index)
    for kind, members in by_class.items():
        members.sort(key=lambda i: (asks[i]["first_unit"], asks[i]["last_unit"], i))
        current, last = [], None
        for index in members:
            if current and asks[index]["first_unit"] <= last:
                current.append(index)
                last = max(last, asks[index]["last_unit"])
            else:
                if current:
                    groups.append(current)
                current, last = [index], asks[index]["last_unit"]
        if current:
            groups.append(current)
    counts = {key: 0 for key in OVERLAP_COUNT_KEYS}
    counts["groups_by_class"] = {}
    out = []
    for group in sorted(groups, key=min):
        members = [asks[index] for index in sorted(group)]
        if len(members) == 1:
            out.append(members[0])
            continue
        kind = members[0].get("class") or members[0].get("final_class")
        chosen = min(members, key=lambda ask: (_verdict_rank(ask.get("final")),
                                               ask.get("final") == "ask" and ask.get("final_class") not in (kind, None)))
        merged = {"first_unit": min(ask["first_unit"] for ask in members), "last_unit": max(ask["last_unit"] for ask in members),
                  "class": members[0].get("class"), "final": chosen.get("final"), "final_class": chosen.get("final_class"),
                  "final_from": chosen.get("final_from"), "fallback": None, "merged_from": len(members)}
        if merged["final"] == "unchecked":
            fallbacks = [ask["fallback"] for ask in members if ask.get("final") == "unchecked" and ask.get("fallback")]
            if fallbacks:
                merged["fallback"] = min(fallbacks, key=lambda item: (_verdict_rank(item.get("verdict")), item.get("class") != kind))
        out.append(merged)
        counts["groups"] += 1
        same = len({(ask["first_unit"], ask["last_unit"]) for ask in members}) == 1
        counts["groups_on_one_range" if same else "groups_on_overlapping_ranges"] += 1
        counts["groups_with_two_or_more_final_asks"] += sum(1 for ask in members if ask.get("final") == "ask") >= 2
        counts["groups_by_class"][kind] = counts["groups_by_class"].get(kind, 0) + 1
    counts["asks_as_filed"], counts["asks_counted"] = len(asks), len(out)
    counts["asks_merged_away"] = len(asks) - len(out)
    return out, counts


def parse_asks(data):
    asks = []
    for ask in data.get("asks", []):
        fallback = ask.get("final_small_fallback")
        asks.append({"first_unit": int(ask["first_unit"]), "last_unit": int(ask["last_unit"]), "class": ask.get("class"),
                     "final": ask.get("final"), "final_class": ask.get("final_class"), "final_from": ask.get("final_from"),
                     "fallback": ({"verdict": fallback.get("verdict"), "class": fallback.get("class")} if fallback else None)})
    asks, overlaps = merge_overlapping_asks(asks)             # registry 2026-11-21 12:52 (2)
    return {"kind": "asks", "audio": data["audio"], "creator": data["creator"], "video_id": data.get("video_id"),
            "group": data.get("group"), "asks": asks, "ask_overlaps": overlaps, "middle_checked": data.get("middle_checked"),
            "asr_model": asr_model_of(data), "synthetic": bool(data.get("synthetic"))}


def ask_overlap_counts(bundle):
    """Registry 2026-11-21 12:52 (2): per group of the bundle's recordings, how often asks of one class on overlapping unit
    ranges were counted once (merge_overlapping_asks): ask files, those with a merge, and the sums of the per-file counts.
    Labels only, counts only (no id), for counts.json before any outcome."""
    out = {}
    for item in bundle["recordings"]:
        record = item.get("asks")
        if not record:
            continue
        counts = record.get("ask_overlaps")
        if counts is None:                           # a record built without parse_asks: nothing was merged
            counts = {"asks_as_filed": len(record.get("asks") or []), "asks_counted": len(record.get("asks") or [])}
        group = out.setdefault(item.get("group") or "none", dict({key: 0 for key in OVERLAP_COUNT_KEYS}, ask_files=0,
                                                                   ask_files_with_a_merge=0, groups_by_class={}))
        group["ask_files"] += 1
        group["ask_files_with_a_merge"] += bool(counts.get("groups"))
        for key in OVERLAP_COUNT_KEYS:
            group[key] += counts.get(key, 0)
        for kind, number in (counts.get("groups_by_class") or {}).items():
            group["groups_by_class"][kind] = group["groups_by_class"].get(kind, 0) + number
    return dict(sorted(out.items()))


def load_asks(folder, problem=ASK):
    problem = freeze2_problem() if problem is ASK else problem
    return [parse_asks(read_json(path, problem)) for path in json_files(folder, problem)]


# ---------------------------------------------------------------- features (this package's own format)

def parse_features(data):
    units = {}
    for unit in data["units"]:
        units[int(unit["id"])] = {key: unit[key] for key in ("start", "end", "syllables", "letters", "words", "pauses", "contracted",
                                                              "full", "fp_sing", "fp_plur", "hedges", "self_name") if key in unit}
    return {"kind": "features", "audio": data["audio"], "creator": data["creator"], "group": data.get("group"),
            "units": units, "h9": data.get("h9"), "synthetic": bool(data.get("synthetic")), "feature_version": data.get("feature_version"),
            "asr_model": asr_model_of(data)}


def load_features(folder, problem=ASK):
    problem = freeze2_problem() if problem is ASK else problem
    return [parse_features(read_json(path, problem)) for path in json_files(folder, problem)]


# ---------------------------------------------------------------- forecasts

SECOND_SOURCE = {"fc": "small"}         # label-files.md: fc_second is the small model's reading beside the record


def _sources(statement, prefix):
    """{source name: block}: plain prefix is the record, prefix_<name> another labelling (fc_second -> "small")."""
    out = {}
    for key, value in statement.items():
        if key == prefix:
            out["record"] = value
        elif key.startswith(prefix + "_") and isinstance(value, dict):
            name = key[len(prefix) + 1:]
            out[SECOND_SOURCE.get(prefix, name) if name == "second" else name] = value
    return out


def _inclusion_p(statement):
    """Weights are 1 / p: inclusion_p of the production files; the pilot's valve_p or candidate_p otherwise."""
    for key in ("inclusion_p", "valve_p", "candidate_p"):
        value = statement.get(key)
        if value is not None and float(value) > 0:
            return float(value)
    return 1.0


def parse_statement(statement):
    parts = {}
    for name, block in _sources(statement, "fc").items():
        if not block or "values" not in block:
            parts[name] = None
            continue
        parts[name] = {part: (block["values"].get(part), (block.get("where") or {}).get(part)) for part in K.H2_PARTS}
    commitment = {}
    for name, block in _sources(statement, "fd").items():
        commitment[name] = None if not block or "committed" not in block else {"committed": block["committed"], "four_way": block.get("four_way")}
    coded = statement.get("coded")
    return {"verified": bool(statement.get("verified")) and coded is not False, "duplicate": bool(statement.get("duplicate")),
            "words": int(statement.get("statement_words") or 0), "markers": statement.get("markers") or {},
            "parts": parts, "commitment": commitment, "weight": 1.0 / _inclusion_p(statement),
            "routed_final": statement.get("middle_final"), "shared_wording": shared_wording_of(statement)}


SENTENCE_KEYS = ("statement_quote", "sentence_quote", "sentence")    # wording fields the H2 flag rule reads, if present


def shared_wording_of(statement):
    """H2's flag (registry 02:50, M9): the ids of wording.shared_wording on the statement's wording. A file may carry the
    ids itself ("shared_wording": [...]); otherwise the rule reads statement_quote (label-files.md) and a sentence field
    where one exists. Only the ids are kept; the wording is not stored in the parsed record."""
    given = statement.get("shared_wording")
    if isinstance(given, (list, tuple)):
        return sorted(str(item) for item in given)
    return wording.shared_wording(*(statement.get(key) for key in SENTENCE_KEYS if isinstance(statement.get(key), str)))


def parse_forecasts(data, index):
    """data: one recording ({"audio", "statements"}) or the pilot mapping {audio: {"statements"}}. index: audio -> (creator,
    group, synthetic) from the voice files."""
    items = [data] if "statements" in data and "audio" in data else [dict(value, audio=audio) for audio, value in data.items()
                                                                    if isinstance(value, dict) and "statements" in value]
    out = []
    for item in items:
        creator, group, synthetic = index.get(item["audio"], (item.get("creator"), item.get("group"), bool(item.get("synthetic"))))
        out.append({"kind": "forecasts", "audio": item["audio"], "creator": item.get("creator", creator), "group": item.get("group", group),
                    "statements": [parse_statement(s) for s in item["statements"]], "asr_model": asr_model_of(item),
                    "synthetic": bool(item.get("synthetic", synthetic))})
    return out


def load_forecasts(folder, index, problem=ASK):
    problem = freeze2_problem() if problem is ASK else problem
    out = []
    for path in json_files(folder, problem):
        out += parse_forecasts(read_json(path, problem), index)
    return out


# ---------------------------------------------------------------- content (sentence codes for H5)

def parse_content(data, index):
    items = [data] if "units" in data and "audio" in data else [dict(value, audio=audio) for audio, value in data.items()
                                                               if isinstance(value, dict) and "units" in value]
    out = []
    for item in items:
        creator, group, synthetic = index.get(item["audio"], (item.get("creator"), item.get("group"), bool(item.get("synthetic"))))
        units, failed = {}, 0
        for unit_id, unit in item["units"].items():
            if not isinstance(unit, dict) or "failed" in unit or unit.get("primary") is None:
                failed += 1                                  # a failed reading is no code: left out, counted
                continue
            units[int(unit_id)] = {"primary": unit.get("primary"), "secondary": unit.get("secondary"), "group": unit.get("group"),
                                   "weight": float(unit.get("weight", 1))}
        mode = item.get("mode")
        if mode is None and "coded_whole" in item:
            mode = "whole" if item.get("coded_whole") else "systematic"
        out.append({"kind": "content", "audio": item["audio"], "creator": item.get("creator", creator), "group": item.get("group", group),
                    "units": units, "failed_units": failed, "mode": mode, "points": item.get("points"),
                    "too_short": bool(item.get("too_short")), "asr_model": asr_model_of(item),
                    "synthetic": bool(item.get("synthetic", synthetic))})
    return out


def load_content(folder, index, problem=ASK):
    problem = freeze2_problem() if problem is ASK else problem
    out = []
    for path in json_files(folder, problem):
        out += parse_content(read_json(path, problem), index)
    return out


# ---------------------------------------------------------------- titles

def parse_title(record):
    return {"presentation": record.get("presentation"), "voiced_by": record.get("voiced_by"), "cues": sorted(record.get("cues") or []),
            "source_families": sorted(code[3:] if str(code).startswith("FAM") else str(code) for code in record.get("source_families") or []),
            "kind_cues": sorted(record.get("kind_cues") or []), "language": record.get("language")}


def usable_title(reading):
    """produce.usable: a reading that is not {"failed": reason}."""
    return isinstance(reading, dict) and "presentation" in reading


def parse_titles(data):
    """Pilot layout {source: {video id: title record}}; the "vote" block of the pilot (a count, not a record) is skipped."""
    out = {}
    for source, records in data.items():
        if source in ("vote", "synthetic") or not isinstance(records, dict):
            continue
        out[source] = {video: parse_title(record) for video, record in records.items() if usable_title(record)}
    out["_synthetic"] = bool(data.get("synthetic"))
    return out


TITLE_SOURCES = (("final", "record"), ("middle", "primary"), ("small", "second"), ("large", "large"))


def parse_title_files(files):
    """Production layout: one file per creator with "titles" entries (label-files.md). A failed reading is left out
    of its source; a title without a record is absent from "final"."""
    out = {source: {} for source, _ in TITLE_SOURCES}
    synthetic = bool(files) and all(data.get("synthetic") for data in files)
    for data in files:
        for entry in data.get("titles", []):
            video = entry.get("video_id")
            if not video:
                continue
            for source, key in TITLE_SOURCES:
                if usable_title(entry.get(key)):
                    out[source][video] = parse_title(entry[key])
    out["_synthetic"] = synthetic
    return out


def load_titles(path, problem=ASK):
    problem = freeze2_problem() if problem is ASK else problem
    if isinstance(path, (list, tuple)):
        return parse_title_files([read_json(item, problem) for item in json_files(path, problem)])
    path = Path(path)
    if path.is_dir():
        return parse_title_files([read_json(item, problem) for item in json_files(path, problem)])
    return parse_titles(read_json(path, problem))


# ---------------------------------------------------------------- the analysis bundle

def index_of(voice):
    return {record["audio"]: (record["creator"], record["group"], record["synthetic"]) for record in voice}


NO_FEATURE_VERSION = "none stated"


def feature_versions(features):
    """{feature_version: number of feature files} of parsed feature records (NO_FEATURE_VERSION where a file states none)."""
    out = {}
    for record in features:
        version = record.get("feature_version")
        key = NO_FEATURE_VERSION if version is None else str(version)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def require_one_feature_version(features):
    """Registry 2026-11-21 12:52 (4): a bundle whose feature files carry more than one feature_version is refused, naming
    the versions (a file that states none counts as a version of its own), so that no estimate mixes the counts of two
    features.py rules (H9's seen partners with hold-out files of another rule, say)."""
    versions = feature_versions(features)
    if len(versions) > 1:
        named = ", ".join(f"{version} ({count} file{'' if count == 1 else 's'})" for version, count in versions.items())
        raise ValueError("refused: the feature files of this bundle carry more than one feature_version: " + named
                         + "; one analysis reads the feature files of one features.py rule (registry 2026-11-21 12:52 (4))")
    return versions


def bundle(voice=(), asks=(), features=(), forecasts=(), content=(), titles=None):
    """Joins the normalised records by audio hash (and titles by video id). Returns a dict the hypothesis modules read.
    Refuses feature files of more than one feature_version (require_one_feature_version, registry 2026-11-21 12:52 (4))."""
    require_one_feature_version(features)
    by_audio = {}
    for record in voice:
        by_audio.setdefault(record["audio"], {})["voice"] = record
    for kind, records in (("asks", asks), ("features", features), ("forecasts", forecasts), ("content", content)):
        for record in records:
            by_audio.setdefault(record["audio"], {})[kind] = record
    for audio, item in by_audio.items():
        base = item.get("voice") or item.get("asks") or item.get("features") or item.get("forecasts") or item.get("content")
        item["creator"], item["group"], item["audio"] = base["creator"], base.get("group"), audio
        item["video_id"] = (item.get("voice") or {}).get("video_id") or (item.get("asks") or {}).get("video_id")
    every = list(voice) + list(asks) + list(features) + list(forecasts) + list(content)
    if titles is not None:
        every.append({"synthetic": titles.get("_synthetic", False)})
    return {"recordings": [by_audio[audio] for audio in sorted(by_audio)], "titles": titles, "records": every}


# ---------------------------------------------------------------- the ASR-model rule (lead's decision before any label)

RECORD_KINDS = ("voice", "asks", "features", "forecasts", "content")
MAP_ID_COLUMNS = ("audio", "video_id")
MAP_MODEL_COLUMNS = ("asr_model_resolved", "asr_model", "model_role", "model")      # the first present column is read


def _clean_id(value):
    """TABLE's id repair: a leading apostrophe is not part of a video id."""
    value = "" if value is None else str(value).strip()
    return value[1:] if value.startswith("'") else value


def load_model_map(path, audios, videos):
    """{"audio": {audio: model}, "video_id": {video id: model}} from a per-recording model file, for the given recordings
    only. CSV (lines starting with # are comments; TABLE's private recordings.csv has video_id and asr_model_resolved) or
    JSON (a list of rows, {"recordings": [rows]} as the run report's per-recording.json, or {id: model or row}). Of a
    row only an id column and the model column are kept; a row of a recording outside the bundle is dropped as it is
    read. Nothing else of the file is kept, printed or returned. Called at analysis time only, after the guard; the
    permission check (open_problem) runs before the file is opened."""
    require_open_permission(path)
    wanted = {"audio": {str(audio) for audio in audios if audio}, "video_id": {_clean_id(video) for video in videos if video}}
    out = {"audio": {}, "video_id": {}}

    def keep(row):
        if not isinstance(row, dict):
            return
        model = next((model_name(row[column]) for column in MAP_MODEL_COLUMNS if column in row), None)
        for column in MAP_ID_COLUMNS:
            key = _clean_id(row.get(column))
            if key and key in wanted[column]:
                out[column][key] = model

    path = Path(path)
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("recordings"), list):
            data = data["recordings"]
        if isinstance(data, dict):
            for key, value in data.items():
                row = dict(value) if isinstance(value, dict) else {"asr_model_resolved": value}
                row.setdefault("audio", key)
                row.setdefault("video_id", key)
                keep(row)
        else:
            for row in data:
                keep(row)
    else:
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(line for line in handle if not line.startswith("#")):
                keep(row)
    return out


def crosscheck_spec(value):
    """The config entry of the hold-out cross-check: {"table": path, "enabled": true, "synthetic": false} (or a path).
    None where it is absent or switched off."""
    if not value:
        return None
    spec = {"table": value} if isinstance(value, str) else dict(value)
    if not spec.get("enabled", True) or not spec.get("table"):
        return None
    return {"table": str(spec["table"]), "synthetic": bool(spec.get("synthetic")), "groups": tuple(spec.get("groups") or ("holdout",))}


def crosscheck_permitted(records, spec):
    """TABLE's file is read only after freeze 2 (freeze2.json matches the code), or in a synthetic run whose table the
    config marks synthetic and whose folder holds the synthetic marker (open_problem). The file itself is not opened to
    decide this."""
    problem = freeze2_problem()
    if problem is None:
        return
    if spec.get("synthetic") and records and all(record.get("synthetic") for record in records):
        require_open_permission(spec["table"], problem)
        return
    raise PermissionError("hold-out cross-check: TABLE's model column is read only after freeze 2 (" + str(problem) + ")")


def load_table_models(path, audios, videos):
    """{"audio": {...}, "video_id": {...}} of the given recordings from TABLE's file, reading an id column and the model
    column only. CSV: the header names the columns (video_id or audio; asr_model_resolved, else asr_model, model_role or
    model); of every row only those two cells are taken, and a row of a recording outside the given set is dropped as it
    is read. JSON: as load_model_map. Nothing else is kept."""
    path = Path(path)
    if path.suffix.lower() == ".json":
        return load_model_map(path, audios, videos)
    require_open_permission(path)                    # registry 04:55 (f): every loader, before the file is opened
    wanted = {"audio": {str(audio) for audio in audios if audio}, "video_id": {_clean_id(video) for video in videos if video}}
    out = {"audio": {}, "video_id": {}}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(line for line in handle if not line.startswith("#"))
        header = next(reader, None) or []
        names = [name.strip() for name in header]
        ids = [(column, names.index(column)) for column in MAP_ID_COLUMNS if column in names]
        model_index = next((names.index(column) for column in MAP_MODEL_COLUMNS if column in names), None)
        if not ids or model_index is None:
            raise ValueError("hold-out cross-check: the table names no id column or no model column")
        for row in reader:
            for column, index in ids:
                key = _clean_id(row[index]) if index < len(row) else ""
                if key and key in wanted[column]:
                    out[column][key] = model_name(row[model_index]) if model_index < len(row) else None
    return out


def _table_lookup(table, item):
    """(found, model) of one recording in the cross-check table."""
    for column, key in (("audio", item.get("audio")), ("video_id", _clean_id(item.get("video_id")))):
        if key and key in table[column]:
            return True, table[column][key]
    return False, None


def resolved_model(item, model_map=None):
    """The recognizer model of one recording: the one model that every source stating a model agrees on (its label
    and feature files and, when given, the model file); UNKNOWN_MODEL when none states one; CONFLICTING_MODELS when
    two sources differ."""
    stated = {item[kind].get("asr_model") for kind in RECORD_KINDS if isinstance(item.get(kind), dict)}
    if model_map:
        stated.add(model_map["audio"].get(item.get("audio")))
        stated.add(model_map["video_id"].get(_clean_id(item.get("video_id"))))
    stated.discard(None)
    if not stated:
        return UNKNOWN_MODEL
    return stated.pop() if len(stated) == 1 else CONFLICTING_MODELS


def apply_asr_rule(bundle, required, models=None, crosscheck=None):
    """The bundle restricted to the recordings whose resolved model is `required`, the same for every group (seen,
    hold-out, other), so every test (H1, H2, H4, H5, H6, H9, and H9's seen partners) and every eligible count sees
    only them. The others are counted per group: another model (by name), unknown, sources that disagree. models: an
    optional per-recording model file (load_model_map). The counts (no ids) are bundle["asr_rule"]. Titles and the
    guard's record list stay as they are: a title is read only through a kept recording.

    crosscheck (crosscheck_spec; verifier of the ASR fix): each recording of the named groups (hold-out) is compared,
    at analysis time, with TABLE's resolved model (load_table_models: id and model columns only; refused before freeze
    2). A recording the rule keeps but whose table model differs is excluded and counted (excluded_crosscheck_mismatch);
    agreement, absence from the table and a table row stating no model are counted for every checked recording.

    Model-stratified row (registry 03:08; 04:55 (b)): the returned bundle also holds "recordings_model_stratified", the
    kept recordings and those of another stated model or of unknown model (sources that disagree, and hold-out recordings
    whose labels state a model that TABLE contradicts, stay out; labels that state no model dispute nothing and stay in as
    unknown), each a shallow copy tagged "asr_stratum" (its model); counted per group as
    in_model_stratified_row and model_stratified_row_by_model. model_stratified_view() gives that row's bundle."""
    required = model_name(required)
    if not required:
        raise ValueError("the ASR-model rule needs a model name")
    recordings = bundle["recordings"]
    model_map = (load_model_map(models, [item.get("audio") for item in recordings], [item.get("video_id") for item in recordings])
                 if models else None)
    check = crosscheck_spec(crosscheck)
    table = None
    if check:
        crosscheck_permitted(bundle.get("records") or [], check)
        checked = [item for item in recordings if (item.get("group") or "none") in check["groups"]]
        table = load_table_models(check["table"], [item.get("audio") for item in checked], [item.get("video_id") for item in checked])
    kept, stratified, by_group, creators = [], [], {}, {}
    for item in recordings:
        model = resolved_model(item, model_map)
        group = item.get("group") or "none"
        count = by_group.setdefault(group, {"recordings": 0, "kept": 0, "excluded_other_model": 0, "excluded_unknown_model": 0,
                                            "excluded_conflicting_sources": 0, "other_models": {}, "in_model_stratified_row": 0,
                                            "model_stratified_row_by_model": {}})
        tally = creators.setdefault(group, {}).setdefault(item.get("creator"), [0, 0])        # kept, excluded
        count["recordings"] += 1
        mismatch = disputed = False
        if table is not None and group in check["groups"]:
            cross = count.setdefault("crosscheck", {"checked": 0, "agree": 0, "disagree": 0, "not_in_table": 0, "table_states_none": 0,
                                                    "pairs": {}})
            cross["checked"] += 1
            found, table_model = _table_lookup(table, item)
            if not found:
                cross["not_in_table"] += 1
            elif table_model is None:
                cross["table_states_none"] += 1
            elif table_model == model:
                cross["agree"] += 1
            else:
                cross["disagree"] += 1
                pair = f"{model} (labels) / {table_model} (table)"
                cross["pairs"][pair] = cross["pairs"].get(pair, 0) + 1
                mismatch = model == required
                disputed = model != UNKNOWN_MODEL        # labels and TABLE state different models (README (b), item 12)
        if model != CONFLICTING_MODELS and not disputed:                  # the one model-stratified sensitivity row
            stratified.append(dict(item, asr_stratum=model))
            count["in_model_stratified_row"] += 1
            count["model_stratified_row_by_model"][model] = count["model_stratified_row_by_model"].get(model, 0) + 1
        if model == required and not mismatch:
            kept.append(item)
            count["kept"] += 1
            tally[0] += 1
            continue
        tally[1] += 1
        if mismatch:
            count["excluded_crosscheck_mismatch"] = count.get("excluded_crosscheck_mismatch", 0) + 1
        elif model == UNKNOWN_MODEL:
            count["excluded_unknown_model"] += 1
        elif model == CONFLICTING_MODELS:
            count["excluded_conflicting_sources"] += 1
        else:
            count["excluded_other_model"] += 1
            count["other_models"][model] = count["other_models"].get(model, 0) + 1
    for group, count in by_group.items():
        tallies = list(creators[group].values())
        count["excluded"] = count["recordings"] - count["kept"]
        count["creators"] = len(tallies)
        count["creators_with_an_excluded_recording"] = sum(1 for _, excluded in tallies if excluded)
        count["creators_with_no_recording_left"] = sum(1 for left, _ in tallies if not left)
    rule = {"required": required, "applies_to": list(K.THIS_TRACK), "model_file": bool(models), "by_group": by_group,
            "recordings": len(recordings), "kept": len(kept), "excluded": len(recordings) - len(kept),
            "holdout_crosscheck": {"table": bool(check), "groups": list(check["groups"]) if check else []},
            "model_stratified_row": {"row": K.ASR_STRATIFIED_ROW, "recordings": len(stratified),
                                     "added_to_the_primary": len(stratified) - len(kept),
                                     "rule": "other stated models and unknown model included; conflicting sources and "
                                             "cross-check mismatches out; every comparison within one model"}}
    return dict(bundle, recordings=kept, asr_rule=rule, recordings_model_stratified=stratified)


def model_stratified_view(bundle):
    """The bundle of the recognizer-model-stratified sensitivity row (registry 03:08; 04:55 (b)): the recordings of the
    run's English-only model and those of another stated model or of unknown model, each tagged with its model, and
    asr_rule["stratified"] set, which makes H2, H5 and H9 compare within one model (common.stratum)."""
    if "recordings_model_stratified" not in bundle or "asr_rule" not in bundle:
        raise ValueError("the model-stratified row needs a bundle read under the ASR-model rule (apply_asr_rule)")
    return dict(bundle, recordings=bundle["recordings_model_stratified"], asr_rule=dict(bundle["asr_rule"], stratified=True))


def load_bundle(paths, asr_model_required=None, asr_models=None, crosscheck=None):
    """paths: {"voice": dir, "asks": dir, "features": dir, "forecasts": dir, "sentences" (or "content"): dir, "titles":
    dir or file}; any may be missing. The guard runs before anything is returned. asr_model_required: the ASR-model
    rule (apply_asr_rule; asr_models an optional per-recording model file; crosscheck the hold-out cross-check against
    TABLE). Real records are never returned without the rule as frozen (constants.ASR_MODEL_REQUIRED); synthetic records
    may be read with another model or none. The permission check (open_problem, registry 2026-11-21 04:55 (f)) runs before
    any folder is listed or any file is opened; the freeze-2 status is computed once for the whole bundle."""
    problem = freeze2_problem()
    voice = load_voice(paths["voice"], problem) if paths.get("voice") else []
    index = index_of(voice)
    sentences = paths.get("sentences") or paths.get("content")
    out = bundle(voice=voice,
                 asks=load_asks(paths["asks"], problem) if paths.get("asks") else [],
                 features=load_features(paths["features"], problem) if paths.get("features") else [],
                 forecasts=load_forecasts(paths["forecasts"], index, problem) if paths.get("forecasts") else [],
                 content=load_content(sentences, index, problem) if sentences else [],
                 titles=load_titles(paths["titles"], problem) if paths.get("titles") else None)
    require_permission(out["records"])
    require_asr_rule(out["records"], asr_model_required)
    if model_name(asr_model_required):
        return apply_asr_rule(out, asr_model_required, asr_models, crosscheck)
    if crosscheck_spec(crosscheck):
        raise ValueError("the hold-out cross-check runs inside the ASR-model rule; it needs asr_model_required")
    return out


def require_asr_rule(records, required):
    """Real records are read only under the ASR-model rule as frozen; synthetic records under any model or none."""
    if any(not record.get("synthetic") for record in records) and model_name(required) != K.ASR_MODEL_REQUIRED:
        raise PermissionError("ASR-model rule: real labels are read only with asr_model_required = " + K.ASR_MODEL_REQUIRED
                              + " (constants.ASR_MODEL_REQUIRED, the lead's decision before any label existed)")


# ---------------------------------------------------------------- the seen-only path (registry 2026-11-21 06:44 (1))

SEEN_GROUP = "seen"
# labels/seen/<instrument>/ as label-files.md lays them out; "features" holds this package's feature files of the seen
# recordings (features.py seen, written to labels/seen/features; CHOICE: the seen-only path reads nothing outside
# labels/seen, so the feature step writes there)
SEEN_INSTRUMENTS = ("voice", "asks", "features", "forecasts", "sentences", "titles")


def _production_labels(labels):
    return Path(labels).resolve() == Path(PRODUCTION_LABELS).resolve()


def seen_open_problem(path, labels=None):
    """The permission check of the seen-only path, run before a folder is listed or a file is opened: None if `path`
    (links and junctions resolved) lies inside <labels>/seen, where <labels> is the production label tree
    (PRODUCTION_LABELS, llm/labels) or, for tests, another folder named "labels" whose seen folders hold the synthetic
    marker. A path under labels/holdout or labels/other (also through a link), a link that leads out of labels/seen, and
    any other path are refused."""
    labels = Path(PRODUCTION_LABELS if labels is None else labels)
    name = Path(path).name
    if labels.name.lower() != "labels":
        return f"the seen-only path opens a folder named labels/seen only (given {labels.name}/{SEEN_GROUP})"
    root = labels / SEEN_GROUP
    if not root.is_dir():
        return "labels/seen does not exist"
    resolved_root, resolved = root.resolve(), Path(path).resolve()
    if production_tree(resolved_root) or resolved_root.name.lower() != SEEN_GROUP:
        return "labels/seen leads to another folder (a link or junction)"
    if production_tree(resolved):
        return f"{name} lies under labels/holdout or labels/other"
    if resolved != resolved_root and resolved_root not in resolved.parents:
        return f"{name} lies outside labels/seen (links resolved)"
    if not _production_labels(labels):
        folder = resolved if resolved.is_dir() else resolved.parent
        if not synthetic_folder(folder):
            return f"{name}: a labels/seen folder outside the production label tree is opened only where it holds the synthetic marker"
    return None


def require_seen_open(path, labels=None):
    reason = seen_open_problem(path, labels)
    if reason:
        raise PermissionError("seen-only path (registry 2026-11-21 06:44 (1)): the permission check refuses to open " + reason)


def json_seen_files(folder, labels=None):
    """The JSON files of one labels/seen/<instrument> folder (not its refused/ subfolder), after the seen-only check of the
    folder and of every file (a file that is a link out of labels/seen is refused)."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    require_seen_open(folder, labels)
    out = sorted(path for path in folder.glob("*.json") if path.name != SYNTHETIC_MARKER)
    for path in out:
        require_seen_open(path, labels)
    return [path for path in out if path.is_file()]


def read_seen_json(path, labels=None):
    """One file of labels/seen after the seen-only check. The first field read is "group": a file whose group is not
    "seen" is refused before any other field of it is read. Outside the production tree (tests) only files marked
    synthetic are read. Then the refusals of label-files.md (smoke, limited and unfrozen runs)."""
    require_seen_open(path, labels)
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    group = data.get("group") if isinstance(data, dict) else None
    if group != SEEN_GROUP:
        raise PermissionError(f"seen-only path (registry 2026-11-21 06:44 (1)): {Path(path).name} is refused: its group field "
                              "is not 'seen'")
    if not _production_labels(PRODUCTION_LABELS if labels is None else labels) and data.get("synthetic") is not True:
        raise PermissionError(f"seen-only path: {Path(path).name} lies outside the production label tree and is not marked "
                              "synthetic")
    refused = not_for_analysis(data)
    if refused:
        raise ValueError(f"refused: {Path(path).name} is {refused}; label-files.md says never to analyse it")
    return data


def require_seen_records(records):
    """The second layer of the seen-only path: every parsed record is a seen record."""
    wrong = sum(1 for record in records if record.get("kind") and record.get("group") != SEEN_GROUP)
    if wrong:
        raise PermissionError(f"seen-only path: {wrong} parsed records are not of the group 'seen'")


def load_seen_bundle(labels=None, instruments=SEEN_INSTRUMENTS, asr_model_required=K.ASR_MODEL_REQUIRED):
    """The seen-only path of registry 2026-11-21 06:44 (1): the bundle of labels/seen of the production label tree (or
    of a synthetic tree named labels, for tests), for the FREEZE2 constants, the A10.7 null-mean check and CAL part (f).
    Permitted before freeze 2 because it opens nothing but seen labels: the folder check before listing and opening
    (seen_open_problem), the group check of every file before any other field is read (read_seen_json), and every parsed
    record checked again (require_seen_records). Real records only under the frozen ASR-model rule, which is applied as
    for the analysis (apply_asr_rule). The bundle carries "seen_only": True and the file counts per instrument."""
    labels = Path(PRODUCTION_LABELS if labels is None else labels)
    unknown = [name for name in instruments if name not in SEEN_INSTRUMENTS]
    if unknown:
        raise ValueError(f"the seen-only path reads {SEEN_INSTRUMENTS}, not {unknown}")
    root = labels / SEEN_GROUP
    require_seen_open(root, labels)
    loaded, counts = {}, {}
    for name in instruments:
        paths = json_seen_files(root / name, labels)
        loaded[name] = [read_seen_json(path, labels) for path in paths]
        counts[name] = len(paths)
    voice = [parse_voice(data) for data in loaded.get("voice", [])]
    index = index_of(voice)
    out = bundle(voice=voice, asks=[parse_asks(data) for data in loaded.get("asks", [])],
                 features=[parse_features(data) for data in loaded.get("features", [])],
                 forecasts=[item for data in loaded.get("forecasts", []) for item in parse_forecasts(data, index)],
                 content=[item for data in loaded.get("sentences", []) for item in parse_content(data, index)],
                 titles=parse_title_files(loaded["titles"]) if loaded.get("titles") else None)
    require_seen_records(out["records"])
    require_asr_rule(out["records"], asr_model_required)
    if model_name(asr_model_required):
        out = apply_asr_rule(out, asr_model_required)
    out["seen_only"] = True
    out["seen_files"] = counts
    return out
