"""Export unresolved acquisition failures from the latest-20+ recording roster and closed work."""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import math
from pathlib import Path
import re

from . import collection_coverage, common, ingestion_status


COLUMNS = {
    "url": "Video URL", "creator": "Creator", "title": "Video title", "rank": "Newest rank",
    "video_id": "Video ID", "channel_dir": "Creator archive name", "format": "Format",
    "duration_s": "Duration (seconds)", "category": "Failure category", "reason": "What happened",
    "http_status": "HTTP status", "attempt_count": "Recorded attempts", "last_attempt_utc": "Last attempt started (UTC)",
    "last_refusal_utc": "Last provider refusal (UTC)", "next_step": "Next step",
}
LABELS = {"provider_refusal": "Provider refusal", "local_failure": "Local worker failure",
          "transfer_failure": "Incomplete transfer", "needs_review": "Needs review"}
PENDING_CODES = {"native_route_pending", "provider_policy_dispatch_held", "source_dispatch_held",
                 "target_already_archived", "target_already_covered", "dispatch_held"}
LOCAL_STATES = {"local_or_administrative_hold", "ordinary_ready_scoped_local_recovery"}
RECOVER = "Eligible for another download on the current worker queue."


def utc(epoch):
    if type(epoch) not in (int, float) or not math.isfinite(epoch) or epoch <= 0:
        return ""
    return dt.datetime.fromtimestamp(epoch, dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def attempt_clock(attempt):
    return attempt.get("source_started_at_epoch") or attempt.get("attempt_at_epoch") or 0


def failed_outcome(row):
    state = row["disposition"]
    attempts = sorted(row.get("closed_attempt_history", []), key=attempt_clock)
    refusals = [r for r in row.get("current_source_refusals", [])
                if type(r.get("status")) is int and 400 <= r["status"] <= 599 and utc(r.get("at_epoch"))]
    latest_refusal = max(refusals, key=lambda r: r["at_epoch"], default={})
    if state == "current_source_refusal":
        status = latest_refusal["status"]
        reason = f"The media provider returned HTTP {status}."
        next_step = "Check for an independently published full edition from the creator."
        if status == 429:
            next_step = "Resume when the provider permits another request."
        allowed_at = utc(latest_refusal.get("retry_not_before_epoch"))
        if allowed_at:
            next_step += " Earliest recorded retry time is " + allowed_at + "."
        category = "provider_refusal"
    else:
        failures = [a for a in attempts if (a.get("source_response") or {}).get("body_complete") is False
                    or (a.get("error_class") and a["error_class"] not in PENDING_CODES
                        and a.get("new_wire_attempts") != 0)
                    or (a.get("status") == "held" and a.get("error_class") not in PENDING_CODES)]
        if not failures and not (attempts and state in LOCAL_STATES):
            return None
        last = (failures or attempts)[-1]
        http = last.get("source_response") or {}
        status = http.get("status")
        status = status if type(status) is int and 100 <= status < 600 else None
        cause = last.get("error_class")
        if status in {200, 206} and http.get("body_complete") is False:
            category = "transfer_failure"
            reason = "The server accepted the request, but the audio transfer ended before completion."
            received, expected = http.get("received_bytes"), http.get("content_length")
            if type(received) is int and type(expected) is int and expected > 0 and 0 <= received <= expected:
                reason += f" Received {received:,} of {expected:,} bytes."
        elif cause == "wpc_browser_start_failed":
            category, reason = "local_failure", "The local browser worker failed to start."
        elif cause == "gpu_owner_busy":
            category, reason = "local_failure", "The local worker could not acquire its processing slot."
        elif cause == "qualified_downloader_failed":
            category, reason = "transfer_failure", "The download worker stopped before it verified a complete file."
        else:
            category, reason = "needs_review", "The recorded attempt ended without a verified complete audio file."
        next_step = RECOVER if state == "ordinary_ready_scoped_local_recovery" else "Review the attempt and retry when eligible."
    # Handoffs can describe the same attempt more than once. Do not count queue entries as new requests.
    unique = set()
    for a in attempts:
        if a.get("error_class") in PENDING_CODES and (a.get("new_wire_attempts") == 0 or not a.get("source_started_at_epoch")):
            continue
        key = (a.get("attempt") or {}).get("sha256")
        stamp = attempt_clock(a)
        if key or stamp:
            unique.add(key or (a.get("route"), stamp))
    for r in refusals:
        if r.get("attempt_sha256"):
            unique.add(r["attempt_sha256"])
    return {"category": category, "reason": reason, "next_step": next_step, "http_status": status,
            "attempt_count": len(unique), "last_attempt_utc": utc(max(map(attempt_clock, attempts), default=0)),
            "last_refusal_utc": utc(latest_refusal.get("at_epoch"))}


def assemble(frame, durations, closed, proof, saved):
    selected = {r["video_id"]: r for r in frame}
    available = {r["video_id"] for r in saved}
    if (len(selected) != len(frame) or not available <= selected.keys()
            or proof["summary"]["latest20_target"] != len(frame) or proof["summary"]["audio_available"] != len(available)):
        raise ValueError("The receipt coverage must identify the same selected recordings")
    failures = []
    for outcome in closed["rows"]:
        ident = outcome["video_id"]
        if ident in available or outcome["disposition"] == "verified_audio_receipt":
            continue
        incident = failed_outcome(outcome)
        if incident is None:
            continue
        source = selected[ident]
        failures.append({"video_id": ident, "url": "https://www.youtube.com/watch?v=" + ident,
                         "creator": source["source_channel_name"], "channel_dir": source["channel_dir"],
                         "title": source["title"], "format": source["tab"], "rank": int(source["listing_rank"]) + 1,
                         "duration_s": durations.get(ident), **incident})
    failures.sort(key=lambda r: (r["creator"].casefold(), r["rank"], r["video_id"]))
    remaining = len(frame) - len(available)
    return {"schema_version": 1, "scope": "latest20plus_public_regular", "generated_at": proof["generated_at"],
            "closed_at": utc(closed["at_epoch"]), "selected": len(frame), "creators": proof["summary"]["channels"],
            "verified": len(available), "remaining": remaining, "other_pending": remaining-len(failures),
            "failures": failures}


def report(root, selection, dispositions):
    data = Path(selection).read_bytes()
    parsed = ingestion_status.selection_rows(selection, content=data)
    if parsed["basis"] != "latest20plus_public_regular":
        raise ValueError("A latest-20+ public regular recording selection is required")
    raw = json.loads(data)
    details = {r["video_id"]: r for r in raw["rows"] if r.get("fresh_public_regular")}
    frame = parsed["rows"]
    durations = {v: r.get("duration_s") for v, r in details.items()}
    # The normalized selection already validates owners, format and unique per-creator ranks.
    for row in frame:
        row["source_channel_name"] = details[row["video_id"]].get("source_channel_name") or row["source_channel_name"]
    now = dt.datetime.now(dt.timezone.utc)
    closed = collection_coverage.read_closed_dispositions(dispositions, frame, now)
    proof, saved = collection_coverage.coverage(root, selection=selection, now=now)
    if proof["selection_sha256"] != parsed["sha256"]:
        raise ValueError("Selection changed while preparing the report")
    result = assemble(frame, durations, closed, proof, saved)
    result.update(selection_sha256=parsed["sha256"])
    return result


def csv_content(result):
    rows = []
    for item in result["failures"]:
        record = {label: item[key] for key, label in COLUMNS.items()}
        record["Failure category"] = LABELS[item["category"]]
        rows.append(record)
    return collection_coverage.csv_bytes(rows, list(COLUMNS.values())).decode("utf-8")


def md_cell(value):
    value = " ".join(str(value).split())
    value = html.escape(value, quote=False)
    return re.sub(r"([\\|\[\]`*_])", r"\\\1", value)


def markdown(result):
    rows = result["failures"]
    lines = ["# Latest 20+ recordings with unresolved download failures", "",
             f"At {result['generated_at']}, {result['verified']:,} of {result['selected']:,} selected recordings across "
             f"{result['creators']} creators had verified audio. **{len(rows)} recordings had an unsuccessful attempt "
             f"and still needed audio.** Another {result['other_pending']} remained in the queue without a documented failure "
             "in the closed work covered here.", "",
             f"The attempt history closes at {result['closed_at']}. Newer Drive receipts take precedence. "
             "The rank is the recording’s position among the creator’s selected public Videos-tab uploads, newest first.", "",
             "[Search and filter the dashboard](index.html) · [Download the CSV](failed-links.csv)", ""]
    for category, label in LABELS.items():
        group = [r for r in rows if r["category"] == category]
        if not group:
            continue
        lines.extend([f"## {label} ({len(group)})", "",
                      "| Creator | Rank | Recording | What happened | Next step |", "| --- | ---: | --- | --- | --- |"])
        for row in group:
            lines.append(f"| {md_cell(row['creator'])} | {row['rank']} | [{md_cell(row['title'] or row['video_id'])}]({row['url']}) "
                         f"| {md_cell(row['reason'])} | {md_cell(row['next_step'])} |")
        lines.append("")
    if not rows:
        lines.extend(["There are no documented unresolved download failures in this checkpoint.", ""])
    return "\n".join(lines)


def write_reports(result, out, *, with_dashboard=True):
    out = Path(out)
    outputs = {"failed-links.csv": csv_content(result), "failed-links.md": markdown(result)}
    if with_dashboard:
        from . import collection_failure_dashboard
        outputs["index.html"] = collection_failure_dashboard.render(result)
    out.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        common.atomic_write_text(out / name, content)
    return list(outputs)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "selection", "dispositions", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args(argv)
    result = report(args.root, args.selection, args.dispositions)
    files = write_reports(result, args.out)
    print(json.dumps({"verified": result["verified"], "remaining": result["remaining"],
                      "failures": len(result["failures"]), "other_pending": result["other_pending"], "files": files}))


if __name__ == "__main__":
    main()
