"""Date evidence and calendar distributions for the selected public Videos-tab cohort."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from zipfile import ZipFile

from . import common, dataset_timeline, ingestion_status


FIELDS = ("video_id","channel_dir","creator","rank","title","url","date_method","exact_day","date_min","date_max",
          "year_bin","month_bin","publication_day","availability_day","upload_day","relative_label","observed_at",
          "relative_min","relative_max","method_detail","source_url","evidence_sha256","listing_sha256")
DAYS = {"second":1/86400, "minute":1/1440, "hour":1/24, "day":1, "week":7, "month":365.2425/12, "year":365.2425}
METHOD = {"publication":"Watch-page publication date", "availability":"YouTube availability timestamp",
          "upload":"Metadata upload day", "relative":"Relative channel listing", "unknown":"Unresolved"}
PROOF_FIELDS = {"datePublished":"publication", "publishDate":"publication", "timestamp":"availability", "upload_date":"upload"}


def instant(value):
    stamp = datetime.fromisoformat(value.replace("Z","+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("A date observation needs its timezone")
    return stamp.astimezone(timezone.utc)


def relative_interval(label, observed_at):
    """Whole elapsed label units. UTC day padding allows for display rounding on day-or-longer labels."""
    match = re.fullmatch(r"(?:streamed |premiered )?(\d+|a|an) (second|minute|hour|day|week|month|year)s? ago",
                         (label or "").strip(), re.I)
    if not match or not observed_at:
        return None, None
    age = 1 if match[1].lower() in ("a","an") else int(match[1])
    unit = DAYS[match[2].lower()]
    observed = instant(observed_at)
    if age > 100000 or age * unit > 36525:
        return None, None
    padding = timedelta(days=1 if unit >= 1 else 0)
    lo = observed - timedelta(days=(age+1)*unit) - padding
    hi = min(observed, observed - timedelta(days=age*unit) + padding)
    return lo.date().isoformat(), hi.date().isoformat()


def calendar_day(value):
    if type(value) in (float,int):
        if not math.isfinite(value) or value <= 0:
            return None
        return datetime.fromtimestamp(value, timezone.utc).date().isoformat()
    if not isinstance(value,str) or not value:
        return None
    if "T" in value:
        return instant(value).date().isoformat()
    return dataset_timeline.calendar_date(value,"metadata day")


def collect_catalog(path, digest, expected, frame):
    evidence = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    if sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError("The metadata catalog differs from its supplied hash")
    with ZipFile(path) as archive:
        if len(set(archive.namelist())) != len(archive.namelist()):
            raise ValueError("Duplicate members in the metadata catalog")
        summary = json.loads(archive.read("summary.json"))
        if (summary.get("current_selection_sha256") != expected or summary.get("current_recordings") != len(frame)
                or summary.get("state") not in ("private_metadata_preview","verified_current_cohort")):
            raise ValueError("The catalog must cover this dated collection membership")
        seen = set()
        with archive.open("catalog/listings.jsonl") as stream:
            for line in stream:
                row = json.loads(line)
                if not row.get("in_current_selection"):
                    continue
                vid = row["video_id"]
                if (vid not in frame or vid in seen or (row["channel_id"],row["channel_dir"],row["media_type"]) !=
                        (frame[vid]["expected_channel_id"],frame[vid]["channel_dir"],frame[vid]["tab"])):
                    raise ValueError("Recording or channel differs between the catalog and selection")
                seen.add(vid)
        if seen != frame.keys():
            raise ValueError("Catalog listings omit a selected recording")
        with archive.open("catalog/date-evidence.jsonl") as stream:
            for line in stream:
                item = json.loads(line)
                kind = PROOF_FIELDS.get(item["field"])
                if item["video_id"] in frame and kind:
                    key = item["source_sha256"]
                    if not dataset_timeline.SHA.fullmatch(key):
                        raise ValueError("A catalog observation has no source hash")
                    day = calendar_day(item["value"])
                    if day:
                        evidence[item["video_id"]][kind][day].add(key)
    return evidence


def supplement(evidence, frame, root):
    """Read one retained metadata sidecar per job, without opening audio or issuing source requests."""
    files = {}
    for name in ("private-metadata.json","selected-metadata.info.json"):
        for path in Path(root).glob("*/jobs/*/"+name):
            if path.parent.name in frame:
                files[path.parent] = path
    counts = Counter()
    for folder,path in sorted(files.items()):
        vid = folder.name
        raw = path.read_bytes()
        if not raw or len(raw) > 16_000_000:
            continue
        try:
            doc = json.loads(raw)
        except ValueError:
            counts["incomplete_local_metadata"] += 1
            continue
        meta, source = doc.get("metadata") or {}, doc.get("source") or {}
        if (source.get("platform") != "youtube" or source.get("video_id") != vid or meta.get("id") != vid
                or meta.get("channel_id") != frame[vid]["expected_channel_id"]):
            continue
        key = sha256(raw).hexdigest()
        counts["matched_job_sidecars"] += 1
        for field, kind in (("timestamp","availability"),("upload_date","upload")):
            day = calendar_day(meta.get(field))
            if day:
                evidence[vid][kind][day].add(key)
    return dict(counts)


def build_row(selected, grid, evidence):
    video = selected["video_id"]
    label, observed = grid.get("publication_display"), grid["observed_at"]
    low_rel, high_rel = relative_interval(label,observed)
    days = {kind: next(iter(options)) if len(options)==1 else None for kind,options in evidence.items()}
    kind, day, key = "unknown", None, grid["page_sha256"]
    detail = "A usable date could not be assigned from this listing."
    for field in ("publication","availability","upload"):
        if len(evidence.get(field,{})) > 1:
            detail = "Conflicting " + METHOD[field].lower() + " observations."
            break
        if days.get(field):
            kind, day = field, days[field]
            key = min(evidence[field][day])
            detail = {"publication":"YouTube watch metadata supplied datePublished or publishDate, normalized to a UTC day.",
                      "availability":"The saved extractor timestamp records when the video became available, normalized to a UTC day.",
                      "upload":"The saved extractor upload_date supplies a calendar day."}[field]
            break
    else:
        if low_rel:
            kind, detail = "relative", "Estimated from the displayed age and UTC channel-list capture time."
    lo,hi = (low_rel,high_rel) if kind=="relative" else (day,day)
    return {"video_id":video, "channel_dir":selected["channel_dir"], "creator":selected["source_channel_name"],
            "rank":int(selected["listing_rank"])+1, "title":selected["title"], "url":"https://www.youtube.com/watch?v="+video,
            "date_method":kind, "method_detail":detail, "exact_day":day, "date_min":lo, "date_max":hi,
            "year_bin":lo[:4] if lo and lo[:4]==hi[:4] else None, "month_bin":lo[:7] if lo and lo[:7]==hi[:7] else None,
            "publication_day":days.get("publication"),"availability_day":days.get("availability"),"upload_day":days.get("upload"),
            "relative_label":label,"observed_at":observed,"relative_min":low_rel,"relative_max":high_rel,
            "evidence_sha256":key,"listing_sha256":grid["page_sha256"],
            "source_url":grid["source_url"] if kind in ("relative","unknown") else "https://www.youtube.com/watch?v="+video}


def report(selection, catalog, catalog_sha, *, root=None):
    raw = selection.read_bytes()
    parsed = ingestion_status.selection_rows(selection,content=raw)
    if parsed["basis"] != "latest20plus_public_regular":
        raise ValueError("Use the frozen latest-20+ regular recordings")
    frame = {r["video_id"]:r for r in parsed["rows"]}
    all_rows = json.loads(raw)
    cards = {}
    for card in all_rows["observed_primary_grid_index"]:
        vid = card["video_id"]
        if vid not in frame:
            continue
        row = frame[vid]
        if (vid in cards or card["channel_dir"] != row["channel_dir"] or card["observed_primary_channel_id"] != row["expected_channel_id"]
                or card["tab"] != "videos" or card["access_status"] != "public_listing"
                or not dataset_timeline.SHA.fullmatch(card["page_sha256"])):
            raise ValueError("The visible channel listing does not match the selected recording")
        cards[vid] = card
    if cards.keys() != frame.keys():
        raise ValueError("Missing selected channel listing")
    evidence = collect_catalog(catalog,catalog_sha,parsed["sha256"],frame)
    stats = supplement(evidence,frame,root) if root else {}
    records = [build_row(row,cards[vid],evidence[vid]) for vid,row in frame.items()]
    records.sort(key=lambda r:(r["creator"].casefold(),r["rank"],r["video_id"]))
    comparison = [r for r in records if r["exact_day"] and r["relative_min"]]
    fits = sum(r["relative_min"] <= r["exact_day"] <= r["relative_max"] for r in comparison)
    return {"scope":"latest20plus_public_regular_dates","schema_version":1,
            "generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z"),
            "selection_sha256":parsed["sha256"],"catalog_sha256":catalog_sha,"selected":len(records),"creators":len(parsed["creators"]),
            "calibration":{"compared":len(comparison),"within_interval":fits},"local_inventory":stats,
            "date_methods":dict(Counter(r["date_method"] for r in records)),"records":records}


def period_counts(records, period):
    counts = defaultdict(Counter)
    for row in records:
        bucket = row[period+"_bin"] or ("Ambiguous "+period if row["date_method"]=="relative" else "Unresolved")
        counts[bucket][row["date_method"]] += 1
    return [{period:k, **{m:v[m] for m in METHOD}, "total":sum(v.values())} for k,v in sorted(counts.items())]


def write(result,out):
    out.mkdir(parents=True,exist_ok=True)
    common.atomic_write_text(out/"recording-dates.json", dataset_timeline.safe_json(result)+"\n")
    common.atomic_write_text(out/"recording-dates.csv", dataset_timeline.csv_bytes(result["records"],FIELDS).decode("utf-8"))
    for period in ("year","month"):
        counts = period_counts(result["records"],period)
        common.atomic_write_text(out/("dates-by-"+period+".csv"),
            dataset_timeline.csv_bytes(counts,(period,*METHOD,"total")).decode("utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("selection","catalog","out"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--catalog-sha256",required=True)
    parser.add_argument("--root",type=Path,help="Also include verified-identity metadata from newer local collection jobs")
    args=parser.parse_args(argv)
    result=report(args.selection,args.catalog,args.catalog_sha256,root=args.root)
    write(result,args.out)
    print(json.dumps({k:v for k,v in result.items() if k!="records"}))


if __name__=="__main__":
    main()
