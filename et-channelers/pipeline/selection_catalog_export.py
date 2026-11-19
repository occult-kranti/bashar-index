"""Export dated selection memberships, public metadata observations and verified archive references.

Run with python -m pipeline.selection_catalog_export --help. Every input is local.
A preview can be made during acquisition. A final export requires a complete listing
and verified audio for every current recording. Earlier selections preserve their own
positions and identifiers when a creator's display name or channel handle changes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from . import (additive_video_selection, archive_catalog, drive_ingest, gpu_asr_editions,
               ingestion_status, media_metadata, native_public_metadata, stage_archived_text)
from .common import ensure_outside_git
from .gpu_asr import kernel_lock
from .host_capacity import MAX_MANAGED_BYTES, MIN_DISK_SPARE


VIDEO = re.compile(r"[A-Za-z0-9_-]{11}\Z")
OWNER = re.compile(r"UC[A-Za-z0-9_-]{22}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
LANG = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")
SENSITIVE = re.compile(r"(?i)\b(?:access_token|refresh_token|client_secret|api_key|password|cookie|authorization)\s*[:=]\s*[^,\s]+")
LOCAL = re.compile(r"(?i)(?:[a-z]:[\\/]|\\\\[^\\\s]+\\|file://|/(?:home|Users|workspaces|tmp|mnt|var|etc)/)[^\s<>]+")
EMAIL = re.compile(r"(?i)\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b")
EXTRA = {"public_thumbnails", "format_characteristics", "subtitles_languages_listed", "automatic_captions_languages_listed"}
FIELDS = ("title", "description", "duration", "upload_date", "timestamp", "release_date", "release_timestamp",
          "language", "license", "view_count", "like_count", "comment_count", "categories", "tags", "chapters",
          "public_thumbnails", "format_characteristics", "subtitles_languages_listed", "automatic_captions_languages_listed")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def clean_text(value):
    if not isinstance(value, str):
        return None
    safe = media_metadata._clean(value)
    return (EMAIL.sub("[contact omitted]", LOCAL.sub("[local path omitted]", SENSITIVE.sub("[credential omitted]", safe)))
            if isinstance(safe,str) else None)


def pinned_sha(value):
    return value if isinstance(value,str) and SHA.fullmatch(value) else None


def channel_handle(value):
    if not isinstance(value,str):
        return None
    if value.startswith("https://"):
        link=urlsplit(value)
        if link.hostname not in ("youtube.com","www.youtube.com") or link.query or link.fragment:
            return None
        value=link.path.strip("/")
    return value if re.fullmatch(r"@[\w.\-·]{1,100}",value) else None


def numeric(value):
    return value if type(value) in (int,float) and math.isfinite(value) and value>=0 else None


def time_value(value, precision):
    try:
        if precision == "instant":
            if type(value) in (int, float):
                v = datetime.fromtimestamp(value, timezone.utc)
            else:
                v = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return v.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if v.tzinfo else None
        if precision == "date" and isinstance(value, str) and re.fullmatch(r"\d{4}-?\d{2}-?\d{2}", value):
            return date.fromisoformat(value).isoformat()
    except (AttributeError, ValueError, TypeError, OverflowError, OSError):
        pass
    return None


def clean_value(value):
    if isinstance(value, dict):
        return {k: clean_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_value(v) for v in value]
    return clean_text(value) if isinstance(value, str) else value


def rich_fields(meta, wrapper, video, owner):
    """Keep public research fields, dropping transport URLs, request headers and paths."""
    require(isinstance(meta, dict) and meta.get("channel_id", owner) == owner and
            meta.get("id", video) == video, "Metadata has a different owner or video")
    fields = {k: v for k, v in meta.items() if k in native_public_metadata.PUBLIC_FIELDS | EXTRA}
    cleaned = media_metadata.build_metadata(fields, {"video_id": video}, "retained")["metadata"]
    for key, short, stored in (("subtitles", "manual_subtitles", "subtitles_languages_listed"),
                               ("automatic_captions", "automatic_captions", "automatic_captions_languages_listed")):
        value = cleaned.pop(key, None)
        if isinstance(value, dict):
            cleaned[stored] = sorted(k for k in value if LANG.fullmatch(k))
        elif isinstance(wrapper.get("languages"), dict) and isinstance(wrapper["languages"].get(short), list):
            cleaned[stored] = sorted({x for x in wrapper["languages"][short] if isinstance(x, str) and LANG.fullmatch(x)})
    if "formats" in cleaned:
        values = cleaned.pop("formats")
        if isinstance(values, list):
            cleaned["format_characteristics"] = [
                {k: val for k, val in fmt.items() if k in (
                    "format_id", "format_note", "ext", "audio_ext", "video_ext", "acodec", "vcodec", "language",
                    "resolution", "width", "height", "fps", "tbr", "abr", "vbr", "asr", "audio_channels",
                    "audio_track_id", "filesize", "filesize_approx", "container", "audio_is_default", "has_drm")}
                for fmt in values if isinstance(fmt, dict)]
    if "thumbnails" in cleaned:
        cleaned["public_thumbnails"] = cleaned.pop("thumbnails")
    return clean_value(cleaned)


def row_identity(row):
    v, owner, slug = row["video_id"], row["expected_channel_id"], row["channel_dir"]
    require(isinstance(v, str) and VIDEO.fullmatch(v) and isinstance(owner, str) and OWNER.fullmatch(owner)
            and archive_catalog.valid_channel(slug), "Invalid recording, creator or channel directory")
    return v, owner


def memberships(path, fresh_path=None):
    data = Path(path).read_bytes()
    doc, key = json.loads(data), digest(data)
    current, evidence = {}, {}
    if doc.get("cohort") == "Latest 50 public regular uploads":
        require(fresh_path is not None and digest(fresh_path.read_bytes()) == doc.get("fresh_index_sha256"),
                "A prepared 50 requires its original, checksum-matched Videos index")
        info, current, evidence = memberships(fresh_path)
        rows = doc.get("rows", [])
        expected = {(v, r["expected_channel_id"], r["channel_dir"], r["listing_rank"], r["tab"]) for v, r in current.items()}
        observed = {(r["video_id"], r["channel_id"], r["channel_dir"], r["listing_rank"], r["tab"]) for r in rows}
        require(info["requested_per_creator"] == 50 and len(rows) == len(expected) == doc.get("target") and expected == observed,
                "Prepared 50 disagrees with its original public listing")
        return {**info, "selection_sha256": key, "listing_sha256": info["selection_sha256"]}, current, evidence
    if doc.get("per_channel") in (20, 50) and doc.get("index_revision") is not None:
        limit = doc["per_channel"]; complete = True; owners = set(); slugs = set()
        for g in doc["channels"]:
            slug, owner = g["channel_dir"], g["channel_id"]
            require(archive_catalog.valid_channel(slug) and OWNER.fullmatch(owner) and owner not in owners and slug not in slugs,
                    "Duplicate or invalid channel in public listing")
            owners.add(owner); slugs.add(slug)
            items = g.get("public_items", [])
            require(len(items) <= limit, "Public listing exceeds the requested cohort")
            complete &= g.get("public_listing_complete") is True and (len(items) == limit or g.get("exhausted") is True)
            for rank, item in enumerate(items):
                v, item_owner = row_identity(item)
                require(v not in current and item_owner == owner == item.get("observed_primary_channel_id") and
                        item["channel_dir"] == slug and item.get("public_listing_rank") == rank and
                        item.get("tab") == "videos" and item.get("access_status") == "public_listing",
                        "Unbound or duplicate public listing membership")
                current[v] = {**item, "listing_rank": rank, "source_channel_name": g.get("channel_name") or slug,
                              "observed_channel_handle":channel_handle(item.get("channel_handle") or g.get("handle"))}
                evidence[v] = {**item, "listing_observed_at": g.get("observed_at"), "listing_document_sha256": g.get("page_sha256")}
        return {"selection_sha256": key, "requested_per_creator": limit, "creators": len(owners),
                "listing_complete": bool(owners) and complete}, current, evidence
    parsed = ingestion_status.selection_rows(path, content=data)
    source_items = {r["video_id"]: r for r in doc.get("rows", [])}
    for g in doc.get("channels", []):
        if isinstance(g, dict):
            source_items.update({r["video_id"]: r for r in g.get("items", [])})
    for row in parsed["rows"]:
        v, owner = row_identity(row)
        original = source_items[v]; witness = original.get("current_access_evidence") or {}
        current[v] = {**original, **row}
        evidence[v] = {**original, "listing_observed_at": witness.get("observed_at") or original.get("observed_at"),
                       "listing_document_sha256": witness.get("page_sha256") or original.get("page_sha256")}
    complete = all(g["scope"] in ("all_requested_positions_observed", "short_complete_displayed_list")
                   for g in parsed["creators"].values())
    return {"selection_sha256": key, "requested_per_creator": 20, "creators": len(parsed["creators"]),
            "listing_complete": bool(parsed["creators"]) and complete}, current, evidence


def add_date(out, v, field, precision, value, proof):
    val = time_value(value, precision)
    if val is not None and isinstance(proof, str) and SHA.fullmatch(proof):
        out[v].add((field, precision, val, proof))


def build(root, selections, *, remote, fresh_index=None, locator=None, projections=None,
          delta=None, sidecars=(), overlays=(), prior_catalogs=(), caption_evidence=None, final=False):
    """Build private ZIP bytes from local saved evidence. The last selection is current."""
    frames = []; recordings = {}; current = {}; historical = []; dates = defaultdict(set)
    flags = defaultdict(lambda: {"published_english": set(), "original_auto_english": set(), "ambiguous_auto_english": set()})
    membership_keys = set(); selected_source = {}
    for index, path in enumerate(selections):
        frame, rows, raw = memberships(path, fresh_index if index == len(selections)-1 else None)
        require(frame["selection_sha256"] not in membership_keys, "Repeated selection snapshot")
        membership_keys.add(frame["selection_sha256"]); frames.append(frame)
        for v, r in rows.items():
            if v in recordings:
                require(recordings[v]["expected_channel_id"] == r["expected_channel_id"], "Recording changes canonical channel")
            recordings[v] = r; selected_source[v] = raw[v]
            s = raw[v]; sel_sha = frame["selection_sha256"]
            historical.append({"video_id": v, "channel_id": r["expected_channel_id"], "channel_dir": r["channel_dir"],
                "selection_sha256": sel_sha, "listing_position_one_based": r["listing_rank"]+1, "media_type": r["tab"],
                "channel_name": clean_text(r.get("source_channel_name")), "title": clean_text(r.get("title")),
                "observed_channel_handle":channel_handle(r.get("observed_channel_handle") or r.get("channel_handle") or r.get("handle")),
                "duration_seconds": numeric(s.get("duration_s")), "date_display": clean_text(s.get("publication_display") or s.get("date_display") or s.get("upload_date_approx")),
                "listing_observed_at": time_value(s.get("listing_observed_at"), "instant"),
                "listing_document_sha256": s.get("listing_document_sha256") if SHA.fullmatch(str(s.get("listing_document_sha256"))) else None})
            ref = s.get("publication_date_evidence") or {}
            if ((ref.get("row_video_id"), ref.get("row_channel_dir")) == (v, r["channel_dir"]) and
                    s.get("publication_date_quality") in ("instant","date","exact")):
                fp = ref.get("public_watch_sha256") or (ref.get("overlay") or {}).get("sha256")
                add_date(dates, v, "selected_publication", "date", s.get("publication_date"), fp)
                add_date(dates, v, "selected_publication", "instant", s.get("published_at"), fp)
            if s.get("date_quality") == "exact":
                add_date(dates, v, "selected_publication", "date", s.get("publication_date"), s.get("exact_date_evidence_sha256"))
        current = rows
    require(bool(frames), "At least one dated selection is required")
    artifacts = {}; seen = {}; inputs = {}
    def observe(v, owner, meta, wrapper, source, nbytes, stamp, public_sha=None):
        if v not in recordings:
            return
        require(owner == recordings[v]["expected_channel_id"] and SHA.fullmatch(str(source)) and type(nbytes) is int and nbytes>0,
                "Unbound source observation")
        safe = rich_fields(meta, wrapper, v, owner)
        fp = digest(encoded(safe))
        obj = {"video_id": v, "input_sha256": source, "input_bytes": nbytes, "capture_time_utc": time_value(stamp, "instant"),
               "projection_sha256": fp}
        if public_sha:
            obj["retained_projection_sha256"] = public_sha
        old = seen.setdefault((v, source), obj)
        require(old["projection_sha256"] == fp, "One source has conflicting metadata projections")
        artifacts.setdefault(fp, safe)
        for field, precision in (("upload_date","date"),("timestamp","instant"),("release_date","date"),("release_timestamp","instant")):
            add_date(dates, v, field, precision, safe.get(field), source)

    require(bool(locator) == bool(projections), "A locator and its projected metadata archive belong together")
    if locator:
        locator_bytes = locator.read_bytes(); base = json.loads(locator_bytes); packed = projections.read_bytes()
        require(digest(packed) == base["public_projection_archive"]["sha256"] and len(packed)==base["public_projection_archive"]["bytes"],
                "Stored metadata archive differs from its locator")
        inputs["locator_sha256"] = digest(locator_bytes); inputs["projection_archive_sha256"] = digest(packed)
        by_pair = {}
        for line in gzip.GzipFile(fileobj=io.BytesIO(packed)):
            d = json.loads(line); v = d["video_id"]
            if v in recordings:
                require(d["expected_channel_id"] == recordings[v]["expected_channel_id"] and
                        digest(encoded(d["metadata"])) == d["projection_sha256"], "Stored public projection is unbound")
                by_pair[v, d["projection_sha256"]] = d["metadata"]
        for v, entry in base["per_video"].items():
            if v not in recordings:
                continue
            for d in entry["documents"]:
                fp = d["public_projection_sha256"]
                require((v,fp) in by_pair, "Metadata locator cannot resolve its stored observation")
                observe(v, recordings[v]["expected_channel_id"], by_pair[v,fp], {}, d["input_sha256"], d["input_bytes"],
                        d.get("capture_time_utc"), fp)
            if entry["documents"]:
                flags[v]["published_english"].update(entry.get("declared_published_english", []))
                flags[v]["original_auto_english"].update(entry.get("declared_original_automatic_english", []))
    if delta:
        data = delta.read_bytes(); source = json.loads(data)
        if locator:
            require(source.get("baseline_sha256")==inputs["locator_sha256"], "Delta belongs to another metadata locator")
        inputs["delta_sha256"] = digest(data)
        for key, d in source["observations"].items():
            v = d["video_id"]
            if v not in recordings:
                continue
            require(key == d["source_sha256"] and digest(encoded(d["metadata"])) == d["public_sha256"] and
                    d["metadata"].get("channel_id") == recordings[v]["expected_channel_id"], "Unbound delta observation")
            observe(v, d["metadata"]["channel_id"], d["metadata"], {}, key, d["source_bytes"], d.get("observed_at"), d["public_sha256"])
            for role,k in (("published_english","published_english"),("original_auto_english","original_english_automatic"),("ambiguous_auto_english","uncertain_english_automatic")):
                flags[v][role].update(d.get(k, []))
    if caption_evidence:
        data = caption_evidence.read_bytes(); prior = json.loads(data)
        inputs["caption_declaration_evidence_sha256"] = digest(data)
        for row in prior["records"]:
            v = row["video_id"]
            if v not in recordings or row.get("channel_dir") != recordings[v]["channel_dir"]:
                continue
            for k, name in (("published_english","published_english_evidence"),("original_auto_english","original_auto_english_evidence"),
                            ("ambiguous_auto_english","ambiguous_automatic_english_alias")):
                flags[v][k].update(row.get(name, []))
    for path in sidecars:
        data = path.read_bytes(); wrapper = json.loads(data)
        meta = wrapper.get("metadata", wrapper); v = meta.get("id"); source = wrapper.get("source", {})
        if v not in recordings:
            continue
        require((source.get("platform") == "youtube" and source.get("video_id") == v) or
                (not source and str(meta.get("extractor_key") or meta.get("extractor")).lower() == "youtube"),
                "Sidecar has no recording-specific YouTube provenance")
        observe(v, meta.get("channel_id"), meta, wrapper, digest(data), len(data), wrapper.get("captured_at", meta.get("epoch")))
        for src, kind in (("subtitles", "published_english"),("automatic_captions", "ambiguous_auto_english")):
            for lang, options in (meta.get(src) or {}).items():
                if not re.fullmatch(r"en(?:[-_][a-z0-9]+)*", lang, re.I) or not isinstance(options, list):
                    continue
                for part in options:
                    if not isinstance(part, dict):
                        continue
                    query=parse_qs(urlsplit(part.get("url") or "").query)
                    if "tlang" in query:
                        continue
                    original=(lang.lower().endswith("-orig") or "original" in str(part.get("name", "")).lower()
                              or query.get("kind")==["asr"] and query.get("lang", [""])[0].lower().startswith("en"))
                    flags[v]["original_auto_english" if src=="automatic_captions" and original else kind].add(lang)
    for overlay in overlays:
        data = overlay.read_bytes(); proof = digest(data)
        inputs.setdefault("date_overlay_sha256", []).append(proof)
        for line in data.splitlines():
            d = json.loads(line); v = d["video_id"]
            if v not in recordings:
                continue
            require(d.get("channel_id") == recordings[v]["expected_channel_id"], "Date observation belongs to a different channel")
            event = d.get("publication_or_upload") or {}; source = d.get("public_watch_evidence") or {}
            if d.get("date_quality") in ("instant","date","exact"):
                add_date(dates, v, "publication_or_upload", event.get("precision"), event.get("value"), source.get("sha256") or proof)
            for x in source.get("first_party_fields", []):
                if x.get("field") in {"datePublished","uploadDate","publishDate","startTimestamp","endTimestamp"}:
                    add_date(dates, v, x["field"], x.get("precision"), x.get("value"), source.get("sha256"))
                    if x["field"]=="uploadDate" and isinstance(x.get("source_value"),str):
                        add_date(dates,v,"uploadDate_original_calendar_day","date",x["source_value"].split("T",1)[0],source.get("sha256"))
    refs = defaultdict(dict); coverage_rows = list(recordings.values())
    def add_ref(v, role, item, **extra):
        historical_md5=(extra.get("prior_catalog_sha256") and item.get("sha256") is None and
                        isinstance(item.get("drive_id"),str) and type(item.get("bytes")) is int and item["bytes"]>0 and
                        isinstance(item.get("md5"),str) and re.fullmatch(r"[a-f0-9]{32}",item["md5"]))
        if (not (historical_md5 or ingestion_status.publisher_object_proof(item)) or
                not re.fullmatch(r"[A-Za-z0-9_-]+",item["drive_id"])):
            return
        identity = {"video_id": v, "kind": role, **{k:item.get(k) for k in ("drive_id","bytes","md5","sha256")}}
        if "member_sha256" in extra:
            identity["member_sha256"]=extra["member_sha256"]
        data = refs[v].setdefault(digest(encoded(identity)), identity.copy())
        history=extra.pop("prior_catalog_sha256",None)
        if history:
            previous=data.setdefault("prior_catalogs_sha256",[])
            if history not in previous:
                previous.append(history)
        data.update(extra)
    for prior_path in prior_catalogs:
        prior_raw = prior_path.read_bytes(); prior_sha = digest(prior_raw)
        inputs.setdefault("prior_catalog_sha256", []).append(prior_sha)
        with ZipFile(io.BytesIO(prior_raw)) as archive:
            def members(name):
                info=archive.getinfo(name)
                require(info.file_size <= 256_000_000, "Archived catalog member is too large")
                with archive.open(info) as lines:
                    for line in lines:
                        yield json.loads(line)
            old={r["video_id"]:r for r in members("catalog/listings.jsonl") if r["video_id"] in recordings}
            for v,r in old.items():
                require(r["channel_id"]==recordings[v]["expected_channel_id"], "Earlier archive associates a video with another owner")
                for role, name in (("published_english","declared_published_english"),("original_auto_english","declared_original_automatic_english"),
                                   ("ambiguous_auto_english","automatic_english_alias_without_original_evidence")):
                    flags[v][role].update(r.get(name,[]))
            old_rich={}
            for d in members("catalog/public-metadata-snapshots.jsonl"):
                fp=d["projection_sha256"]
                require(fp==digest(encoded(d["metadata"])), "Earlier catalog public projection changed")
                old_rich[fp]=d["metadata"]
            for o in members("catalog/source-observations.jsonl"):
                v=o["video_id"]
                if v in old:
                    fp=o["projection_sha256"]
                    observe(v,old[v]["channel_id"],old_rich[fp],{},o["input_sha256"],o["input_bytes"],o.get("capture_time_utc"),fp)
            for item in members("private/verified-drive-edition-references.jsonl"):
                v=item["video_id"]
                if v not in old:
                    continue
                proof={**item,"sha256":item.get("sha256") or item.get("local_sha256_at_verification")}
                kind=item.get("kind")
                if isinstance(kind,str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",kind):
                    details={}
                    member=item.get("private_archive_member")
                    if isinstance(member,str):
                        elements=member.split("/")
                        require(v in elements and all(re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9._-]*", x) for x in elements)
                                and pinned_sha(item.get("member_sha256")) and type(item.get("member_bytes")) is int and
                                item["member_bytes"]>0 and digest(member.encode())==item.get("zip_member_identifier_sha256"),
                                "Historical archive member has invalid path or evidence")
                        details.update(private_archive_member=member,member_bytes=item["member_bytes"],member_sha256=item["member_sha256"],
                                       zip_member_identifier_sha256=item["zip_member_identifier_sha256"])
                    for field in ("source_edition_kind","source_timebase","timebase","association_basis","association","edition","provider"):
                        if isinstance(item.get(field),str):
                            details[field]=clean_text(item[field])
                    add_ref(v,kind,proof,prior_catalog_sha256=prior_sha,**details)
            if "catalog/date-evidence.jsonl" in archive.namelist():
                for d in members("catalog/date-evidence.jsonl"):
                    if d["video_id"] in old:
                        add_date(dates,d["video_id"],d["field"],d["precision"],d["value"],d["source_sha256"])
    native = ingestion_status.latest_records(root/"sync/drive_ingest_manifest.jsonl")
    for r in coverage_rows:
        v = r["video_id"]; rec = native.get(v,{})
        if rec.get("channel_dir") == r["channel_dir"] and ingestion_status.proof(drive_ingest.receipt_complete, rec, r, remote):
            add_ref(v, "youtube_native_audio", rec); add_ref(v, "youtube_native_sidecar", rec["metadata"])
    for v, editions in gpu_asr_editions.source_catalogue(root, coverage_rows, remote).items():
        for e in editions.values():
            for role in ("audio","metadata"):
                add_ref(v, e["source_type"]+"_"+role, e[role], timebase=e["source_timebase"],
                        receipt_sha256=e["source_receipt_sha256"], association=e["recording_association_method"])
    for job in stage_archived_text.input_rows(root,coverage_rows,remote):
        add_ref(job["row"]["video_id"],"existing_text_archive",job["proof"],edition=job["kind"])
    if final:
        require(frames[-1]["listing_complete"] and current, "The current public listing is incomplete")
        checkrows=[dict(r,tabs_observed=list(dict.fromkeys([r["tab"],*r.get("tabs_observed",[])])),
                        fresh_regular=True,fresh_public_regular=True,public_media_dispatch_excluded=False) for r in current.values()]
        saved=additive_video_selection.verified_counts({"rows":checkrows,"channels":[{"channel_dir":c} for c in sorted({r["channel_dir"] for r in current.values()})]},root,remote)
        require(all(r["verified_audio"] for r in saved["rows"]) and len(saved["rows"])==len(current),
                "The current cohort still needs verified audio")
    observation_counts=Counter(v for v,_ in seen)
    observed_by_video=defaultdict(set)
    for (v,_),d in seen.items():
        observed_by_video[v].add(d["projection_sha256"])
    listings=[]; counts=Counter(); present=Counter()
    for v,r in sorted(recordings.items()):
        projections_for_video=[artifacts[fp] for fp in observed_by_video[v]]
        for k in FIELDS:
            if any(k in x for x in projections_for_video):
                counts[k]+=1
            if any(x.get(k) not in (None,"",[],{}) for x in projections_for_video):
                present[k]+=1
        s=selected_source[v]; receipt=s.get("publication_date_evidence") or {}
        upload_days=defaultdict(set); watch_calendar_days=defaultdict(set); handle_evidence=defaultdict(set)
        for field,precision,val,fp in dates.get(v,set()):
            if field=="upload_date" and precision=="date":
                upload_days[val].add(fp)
            if field in ("uploadDate","uploadDate_original_calendar_day") and precision=="date":
                watch_calendar_days[val].add(fp)
        for fp in observed_by_video[v]:
            public=artifacts[fp]
            handle=channel_handle(public.get("uploader_id")) or channel_handle(public.get("channel_url"))
            if handle:
                handle_evidence[handle].add(fp)
        bound=((receipt.get("row_video_id"),receipt.get("row_channel_dir"))==(v,r["channel_dir"]) and
               s.get("publication_date_quality") in ("instant","date","exact"))
        date_fp=pinned_sha(receipt.get("public_watch_sha256") or (receipt.get("overlay") or {}).get("sha256")) if bound else None
        selected_day=time_value(s.get("publication_date"),"date") if date_fp or s.get("date_quality")=="exact" else None
        state=("multiple_observed_days" if len(upload_days)>1 else "selection_and_observed_upload_day_disagree" if
               upload_days and selected_day and selected_day not in upload_days else "single_observed_upload_day" if upload_days else "no_observed_upload_day")
        listings.append({"video_id":v,"channel_id":r["expected_channel_id"],"channel_dir":r["channel_dir"],"media_type":r["tab"],
            "regular_listing_position_one_based":r["listing_rank"]+1 if r["tab"]=="videos" else None,
            "youtube_watch_url":"https://www.youtube.com/watch?v="+v,"in_current_selection":v in current,
            "public_listing_url":"https://www.youtube.com/channel/"+r["expected_channel_id"]+"/"+r["tab"] if r["tab"]!="unknown" else None,
            "title":clean_text(r.get("title")),"duration_seconds_from_listing":numeric(s.get("duration_s")),"duration_as_shown":clean_text(s.get("duration_as_shown")),
            "listing_observed_at":time_value(s.get("listing_observed_at"),"instant"),"listing_document_sha256":pinned_sha(s.get("listing_document_sha256")),
            "publication_date":selected_day,"publication_instant":time_value(s.get("published_at"),"instant") if date_fp else None,
            "publication_date_quality":clean_text(s.get("publication_date_quality") or s.get("date_quality") or "unknown"),
            "publication_date_basis":clean_text(s.get("publication_date_basis")),"publication_as_displayed":clean_text(s.get("publication_display") or s.get("date_display")),
            "date_source_sha256":date_fp or pinned_sha(s.get("exact_date_evidence_sha256")),"date_overlay_sha256":pinned_sha((receipt.get("overlay") or {}).get("sha256")) if bound else None,
            "observed_upload_day_evidence":{k:sorted(vals) for k,vals in sorted(upload_days.items())},
            "watch_page_upload_calendar_days":{k:sorted(vals) for k,vals in sorted(watch_calendar_days.items())},
            "observed_channel_handles":{k:sorted(vals) for k,vals in sorted(handle_evidence.items())},
            "single_observed_upload_day":next(iter(upload_days)) if len(upload_days)==1 else None,"upload_day_evidence_state":state,
            "source_observation_count":observation_counts[v],"public_projection_count":len(projections_for_video),
            "verified_reference_count":len(refs[v]),"declared_published_english":safe_languages(flags[v]["published_english"]),
            "declared_original_automatic_english":safe_languages(flags[v]["original_auto_english"]),
            "automatic_english_alias_without_original_evidence":safe_languages(flags[v]["ambiguous_auto_english"])})
    dated=[dict(video_id=v,field=f,precision=p,value=val,source_sha256=fp) for v,items in sorted(dates.items()) for f,p,val,fp in sorted(items)]
    summary={"schema_version":1,"state":"verified_current_cohort" if final else "private_metadata_preview",
             "current_selection_sha256":frames[-1]["selection_sha256"],"selections":frames,
             "current_recordings":len(current),"recordings_across_selections":len(recordings),"memberships":len(historical),
             "source_observations":len(seen),"distinct_public_snapshots":len(artifacts),
             "verified_archive_references":sum(map(len,refs.values())),"recordings_with_date_evidence":len(dates),
             "evidence_inputs":inputs,"rich_field_coverage":{k:{"absent":len(recordings)-counts[k],"declared_empty":counts[k]-present[k],
                                                             "present":present[k]} for k in FIELDS}}
    entries={"catalog/listings.jsonl":listings,"catalog/selection-memberships.jsonl":historical,
             "catalog/date-evidence.jsonl":dated,"catalog/source-observations.jsonl":[seen[k] for k in sorted(seen)],
             "catalog/public-metadata-snapshots.jsonl":[{"projection_sha256":k,"metadata":artifacts[k]} for k in sorted(artifacts)],
             "private/verified-drive-edition-references.jsonl":[obj for v in sorted(refs) for _,obj in sorted(refs[v].items())]}
    stream=io.BytesIO()
    with ZipFile(stream,"w") as archive:
        for name,rows in entries.items():
            archive.writestr(ZipInfo(name),b"".join(encoded(row)+b"\n" for row in rows),compress_type=ZIP_DEFLATED)
        archive.writestr(ZipInfo("summary.json"),encoded(summary)+b"\n",compress_type=ZIP_DEFLATED)
    return stream.getvalue(),summary


def safe_languages(values):
    return sorted(x for x in values if isinstance(x,str) and LANG.fullmatch(x) and re.match(r"^en(?:[-_]|$)",x,re.I))


def publish_catalog(path, data, summary, *, root, remote, executable, config=None):
    """Copy one closed immutable catalog and record its Drive checksum and ID before reuse."""
    require(summary["state"]=="verified_current_cohort", "Only a verified final catalog can be published")
    fp=archive_catalog.digest(data); selection=summary["current_selection_sha256"]
    relative=f"_catalog/youtube/selections/{selection}/{fp['sha256']}/regular-catalog.zip"
    destination=archive_catalog.join_remote(remote,relative)
    expected={"receipt_type":"metadata_catalog","status":"verified","selection_sha256":selection,
              "remote":destination,"recordings":summary["current_recordings"],**fp}
    receipt=path.with_suffix(path.suffix+".drive.json")
    if receipt.is_file():
        record=json.loads(receipt.read_bytes())
        require(all(record.get(k)==v for k,v in expected.items()) and isinstance(record.get("drive_id"),str)
                and re.fullmatch(r"[A-Za-z0-9_-]+",record["drive_id"]),"The existing Drive receipt belongs to another catalog")
        return record
    cooldown=root/"sync/drive_ingest_cooldown.json"
    require(not (root/"sync/STOP_DRIVE_UPLOAD").exists() and not drive_ingest.read_drive_cooldown(cooldown),"Drive upload is on hold")
    drive=drive_ingest.Rclone(executable, config, cooldown_path=cooldown)
    drive.copy(path,destination)
    with drive_ingest.batch_manifest(path.parent,[relative]) as names:
        observed=drive.stat_batch(remote,{relative},names)[relative]
    drive_ingest.verify_remote(observed,fp)
    drive_id=observed.get("ID")
    require(isinstance(drive_id,str) and re.fullmatch(r"[A-Za-z0-9_-]+",drive_id),"Drive catalog has no object ID")
    record={**expected,"drive_id":drive_id}
    drive_ingest.control_file(receipt,encoded(record)+b"\n",atomic=True)
    return record


def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root",required=True,type=Path,help="Private archive containing verified receipt journals")
    cli.add_argument("--selection",required=True,action="append",type=Path,help="Dated snapshot, oldest first; last is current")
    cli.add_argument("--fresh-index",type=Path,help="Original Videos index required for a prepared latest-50 selection")
    cli.add_argument("--locator",type=Path,help="Verified locator JSON for previously captured public metadata")
    cli.add_argument("--projections",type=Path,help="Its content-addressed gzip JSON Lines partner")
    cli.add_argument("--delta",type=Path,help="Incremental public observation cache bound to the locator")
    cli.add_argument("--caption-evidence",type=Path,help="Saved per-video inventory separating published, original automatic and ambiguous English")
    cli.add_argument("--prior-catalog",action="append",type=Path,default=[],help="Prior private rich ZIP; reuse its metadata and archive-reference handles")
    cli.add_argument("--sidecar",action="append",type=Path,default=[],help="One saved YouTube metadata observation")
    cli.add_argument("--date-overlay",action="append",type=Path,default=[],help="Saved first-party publication-date JSON Lines")
    cli.add_argument("--out",required=True,type=Path,help="Private output ZIP inside --root; choose a new name if inputs change")
    cli.add_argument("--remote",default=ingestion_status.DEFAULT_REMOTE,help="Match local receipts for this archive")
    cli.add_argument("--final",action="store_true",help="Require the complete current listing and verified audio")
    cli.add_argument("--publish",action="store_true",help="Upload the verified final ZIP and retain its checksum receipt")
    cli.add_argument("--rclone",default="rclone",help="Installed rclone executable")
    cli.add_argument("--rclone-config",type=Path,help="Existing private rclone configuration, when needed")
    args=cli.parse_args(argv);root=ensure_outside_git(args.root);out=ensure_outside_git(args.out)
    require(not args.publish or args.final,"Publishing requires --final")
    require(out.is_relative_to(root) and out!=root,"Output must be inside the private archive")
    out.parent.mkdir(parents=True,exist_ok=True)
    with kernel_lock(out.with_suffix(out.suffix+".lock")):
        data,summary=build(root,args.selection,remote=args.remote,fresh_index=args.fresh_index,locator=args.locator,
                           projections=args.projections,delta=args.delta,sidecars=args.sidecar,overlays=args.date_overlay,
                           prior_catalogs=args.prior_catalog,caption_evidence=args.caption_evidence,final=args.final)
        archive_catalog.atomic_bytes(out,data,root,MAX_MANAGED_BYTES,MIN_DISK_SPARE)
        if args.publish:
            publish_catalog(out,data,summary,root=root,remote=args.remote,executable=args.rclone,config=args.rclone_config)
    print(json.dumps({"output":str(out),"bytes":len(data),"sha256":digest(data),**summary},ensure_ascii=False))
    return 0


if __name__=="__main__":
    main()
