"""Leased publisher audio/caption batches from already accepted private metadata.

No discovery, browser automation, YouTube access, token handling, ASR or imports
of optional media libraries. Importing starts nothing. See PUBLISHER_MIRROR.md.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import zipfile

try:
    from . import drive_ingest as storage, gpu_asr as controls, native_audio_sink as native, media_metadata
    from .youtube_captions import normalize_caption
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import drive_ingest as storage
    import gpu_asr as controls
    import native_audio_sink as native
    import media_metadata
    from youtube_captions import normalize_caption

MAX_MANAGED = storage.MAX_LOCAL_BYTES
DISK_FLOOR = storage.MIN_FREE_BYTES
CONTROL = 4 * 1024 * 1024
KIND = "qualified_publisher_mirror_audio_variant"
EXACT_KIND = "publisher_mirror_audio_variant"
HASH = re.compile(r"[0-9a-f]{64}\Z")
SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\Z")
NATIVE_FLAGS = {"native_youtube_bytes": False, "changes_native_audio_count": False,
                "changes_native_asr_count": False, "changes_native_caption_count": False}


class MirrorError(RuntimeError):
    def __init__(self, kind):
        self.kind = kind
        super().__init__(kind)


def need(value, code):
    if not value:
        raise MirrorError(code)


def encoded(value):
    return controls.encoded(value)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    need(Path(path).stat().st_size <= CONTROL, "control_document_size")
    return json.loads(Path(path).read_bytes())


def local(root, relative):
    need(isinstance(relative, str) and relative and not any(c in relative for c in "\r\n\\"), "local_path")
    path = (root / relative).resolve()
    need(path.is_relative_to(root.resolve()) and path != root.resolve(), "local_path")
    current = path
    while current != root.resolve():
        need(not current.is_symlink() and not getattr(current, "is_junction", lambda: False)(), "storage_link")
        current = current.parent
    return path


def safe_url(url, hosts):
    """Only exact owner-accepted public HTTPS hosts; no YouTube/session route."""
    try:
        u = urlsplit(url)
        hostname = u.hostname or ""
        need(u.scheme == "https" and hostname in hosts and u.port in (None, 443) and
             not u.username and not u.password and not u.fragment and
             not any(ord(c) < 32 for c in url), "publisher_url")
        need(not any(hostname == x or hostname.endswith("." + x) for x in
                     ("youtube.com", "youtu.be", "googlevideo.com", "youtubei.googleapis.com", "localhost")), "publisher_host")
        try:
            need(ipaddress.ip_address(hostname).is_global, "publisher_host")
        except ValueError:
            need("." in hostname, "publisher_host")
        need("tlang" not in parse_qs(u.query), "translated_caption")
        return url
    except (TypeError, ValueError):
        raise MirrorError("publisher_url") from None


def pointer(value, keys):
    need(isinstance(keys, list) and 1 <= len(keys) <= 12, "metadata_pointer")
    try:
        for key in keys:
            need(type(key) in (str, int), "metadata_pointer")
            value = value[key]
        need(isinstance(value, str), "metadata_pointer")
        return value
    except (KeyError, IndexError, TypeError):
        raise MirrorError("metadata_pointer") from None


def public_metadata(value):
    """Reuse credential/path cleanup, then omit all publisher transport URLs."""
    value = media_metadata._clean(value)
    if value is media_metadata._OMIT:
        return None
    if isinstance(value, dict):
        return {k: public_metadata(v) for k, v in value.items()}
    if isinstance(value, list):
        return [public_metadata(v) for v in value]
    if isinstance(value, str):
        return re.sub(r"https?://[^\s<>\"']+", "[URL omitted]", value, flags=re.I)
    return value


def exact_youtube_link(value, expected_id):
    """Validate a publisher's explicit public source link, without fetching it."""
    try:
        url = urlsplit(value)
        query = parse_qs(url.query, keep_blank_values=True)
        need(url.scheme == "https" and not url.username and not url.password and url.port in (None, 443) and
             not url.fragment and not any(ord(c) < 32 for c in value), "exact_youtube_reference")
        need(set(query) <= {"v", "t", "start", "feature", "si"} and all(len(v) == 1 for v in query.values()), "exact_youtube_reference")
        if url.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
            need(url.path == "/watch" and query.get("v") == [expected_id], "exact_youtube_reference")
        elif url.hostname == "youtu.be":
            need(url.path == "/" + expected_id and "v" not in query, "exact_youtube_reference")
        else:
            raise MirrorError("exact_youtube_reference")
        return value
    except (TypeError, ValueError):
        raise MirrorError("exact_youtube_reference") from None


def kind_for(item):
    return EXACT_KIND if item.get("association_method") == "publisher_rss_exact_youtube_id" else KIND


def adts_lc_duration(path, stream, packets):
    """Prove complete constant-rate ADTS LC frames; never use bitrate duration.

    Restrict to one raw-data block per frame and an LC probe with matching header
    rate/channels. Other profiles/framing are held instead of guessed.
    """
    rates = (96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000, 7350)
    channel_counts = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 8}
    need(stream.get("profile") == "LC", "publisher_adts_profile")
    before = storage.fingerprint(path)
    size = Path(path).stat().st_size
    count, rate, channels = 0, None, None
    with Path(path).open("rb") as source:
        while source.tell() < size:
            start = source.tell()
            header = source.read(7)
            need(len(header) == 7 and header[0] == 255 and header[1] & 0xF6 == 0xF0, "publisher_adts_header")
            frequency_index = (header[2] >> 2) & 15
            configuration = ((header[2] & 1) << 2) | (header[3] >> 6)
            need(header[2] >> 6 == 1 and frequency_index < len(rates) and configuration in channel_counts and
                 header[6] & 3 == 0, "publisher_adts_frame_policy")
            current_rate, current_channels = rates[frequency_index], channel_counts[configuration]
            if rate is None:
                rate, channels = current_rate, current_channels
            need(current_rate == rate and current_channels == channels, "publisher_adts_configuration_change")
            frame_length = ((header[3] & 3) << 11) | (header[4] << 3) | (header[5] >> 5)
            header_length = 7 if header[1] & 1 else 9
            need(frame_length > header_length and start + frame_length <= size, "publisher_adts_truncated")
            source.seek(start + frame_length)
            count += 1
    need(count == packets and count > 0 and int(stream.get("sample_rate", 0)) == rate and
         int(stream.get("channels", 0)) == channels and storage.fingerprint(path) == before, "publisher_adts_probe_disagreement")
    return {"duration_seconds": count * 1024 / rate, "sample_count": count * 1024, "sample_rate": rate,
            "channels": channels, "complete_adts_frames": count, "samples_per_frame": 1024,
            "duration_basis": "complete_single_block_adts_aac_lc_frames", "zero_padding": False}


def inspect_publisher_audio(path, selected, executable):
    """Publisher MP3 and framed raw AAC; native codec/source policy is unchanged."""
    if selected["codec"] not in {"mp3", "aac", "mp4a.40.2"}:
        return native.inspect_audio(path, selected, executable)
    try:
        result = subprocess.run([str(executable), "-v", "error", "-count_packets", "-show_entries",
            "stream=codec_type,codec_name,profile,sample_rate,channels,nb_read_packets,duration:format=duration,format_name", "-of", "json", str(path)],
            capture_output=True, text=True, timeout=1800, check=False)
        need(result.returncode == 0 and not result.stderr.strip(), "publisher_audio_probe_failed")
        value = json.loads(result.stdout)
        streams = value.get("streams", [])
        codec = "mp3" if selected["codec"] == "mp3" else "aac"
        need(len(streams) == 1 and streams[0].get("codec_type") == "audio" and streams[0].get("codec_name") == codec, "publisher_audio_only")
        packets = int(streams[0].get("nb_read_packets", 0))
        estimated = float(value.get("format", {}).get("duration") or streams[0].get("duration") or 0)
        framed = adts_lc_duration(path, streams[0], packets) if codec == "aac" and value.get("format", {}).get("format_name") == "aac" else {}
        duration = framed.get("duration_seconds", estimated)
        expected = selected["durationMs"] / 1000
        tolerance = max(2.0, expected * .002)
        need(packets > 0 and math.isfinite(duration) and duration > 0 and abs(duration - expected) <= tolerance, "publisher_audio_duration")
        return {"method": "ffprobe_full_packet_scan", "duration_seconds": duration, "packets": packets, "codec": codec,
                "audio_streams": 1, "video_streams": 0, "duration_tolerance_seconds": tolerance, "decode_accuracy_claimed": False,
                "ffprobe_format_duration_seconds": estimated if math.isfinite(estimated) and estimated > 0 else None,
                "format_estimate_difference_seconds": duration - estimated if math.isfinite(estimated) else None, **framed}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        raise MirrorError("publisher_audio_probe_failed") from None


def load_items(root, plan_path):
    """Resolve URLs only in memory from hash-bound accepted metadata snapshots."""
    root = Path(root).resolve()
    path = Path(plan_path).resolve()
    need(path.is_relative_to(root), "plan_outside_private")
    raw = path.read_bytes()
    need(len(raw) <= CONTROL, "control_document_size")
    plan = json.loads(raw)
    need(plan.get("schema_version") == 1 and isinstance(plan.get("items"), list), "plan_schema")
    items, seen = [], set()
    for original in plan["items"]:
        item = dict(original)
        need(SLUG.fullmatch(item.get("channel_dir", "")) and SLUG.fullmatch(item.get("provider", "")) and
             storage.ID_RE.fullmatch(item.get("associated_youtube_id", "")) and
             SLUG.fullmatch(item.get("watch_page_id", "")), "association_identity")
        need(item.get("human_verified") is False, "association_policy")
        if item.get("association_method") == "publisher_rss_exact_youtube_id":
            need(item.get("exact_youtube_crossreference") is True, "association_policy")
            exact_youtube_link(item.get("original_youtube_link"), item["associated_youtube_id"])
        else:
            need(item.get("association_method") == "publisher_owner_title_date_duration" and item.get("exact_youtube_crossreference") is False,
                 "association_policy")
        need(isinstance(item.get("association_qualification"), str) and 0 < len(item["association_qualification"]) <= 2000,
             "association_qualification")
        pin = item["accepted_metadata"]
        metadata_path = local(root, pin["path"])
        metadata_raw = metadata_path.read_bytes()
        need(len(metadata_raw) <= CONTROL and HASH.fullmatch(pin.get("sha256", "")) and sha(metadata_raw) == pin["sha256"], "accepted_metadata_changed")
        metadata = json.loads(metadata_raw)
        item["public_metadata"] = public_metadata(metadata)
        item["association_qualification"] = public_metadata(item["association_qualification"])
        hosts = item.get("allowed_hosts")
        need(isinstance(hosts, list) and 0 < len(hosts) <= 8 and all(isinstance(h, str) for h in hosts), "publisher_hosts")
        audio = dict(item["audio"])
        need(type(audio.get("maximum_bytes")) is int and 0 < audio["maximum_bytes"] <= MAX_MANAGED, "audio_byte_admission")
        need(audio.get("codec") in {*native.CODECS, "mp3"} and audio.get("extension") in {"aac", "m4a", "webm", "ogg", "opus", "mp3"}, "audio_format")
        need((audio["codec"] == "mp3") == (audio["extension"] == "mp3"), "audio_format")
        duration = audio.get("duration_seconds")
        need(type(duration) in (int, float) and math.isfinite(duration) and duration > 0, "audio_duration")
        audio["url"] = safe_url(pointer(metadata, audio["url_pointer"]), hosts)
        tracks, track_ids = [], set()
        for value in item.get("captions", []):
            track = dict(value)
            need(SLUG.fullmatch(track.get("track_id", "")) and track["track_id"] not in track_ids, "caption_identity")
            publisher_scope = (track.get("kind") == "published" and track.get("translated") is None and
                               track.get("translation_status") == "not_declared" and
                               track.get("language_basis") == "publisher_rss_channel" and track.get("track_language_verified") is False)
            need(re.fullmatch(r"en(?:-[A-Za-z0-9]+)*", track.get("language", ""), re.I) and
                 track.get("kind") in {"published", "automatic_original"} and (track.get("translated") is False or publisher_scope),
                 "caption_language_policy")
            need(track.get("raw_format") in {"vtt", "json3"} and type(track.get("maximum_bytes")) is int and
                 0 < track["maximum_bytes"] <= 64 * 1024 * 1024, "caption_byte_admission")
            track["url"] = safe_url(pointer(metadata, track["url_pointer"]), hosts)
            tracks.append(track)
            track_ids.add(track["track_id"])
        need(len(tracks) <= 16, "caption_inventory_bound")
        item["audio"], item["captions"] = audio, tracks
        identity = {k: item[k] for k in ("provider", "watch_page_id", "associated_youtube_id", "channel_dir")}
        identity["accepted_api_sha256"] = pin["sha256"]
        item["item_id"] = sha(encoded(identity))[:32]
        need(item["item_id"] not in seen, "duplicate_item")
        seen.add(item["item_id"])
        items.append(item)
    return sha(raw), items


@dataclass
class Settings:
    root: Path
    plan_path: Path
    owner: str
    lease_id: str
    managed_roots: list[Path]
    remote: str
    ffprobe: str
    spool_cap_bytes: int
    workers: int = 2


def publisher_stage_projection(staged_actual_bytes, remaining_requested_bytes, *, lease_limit_bytes=None):
    """Project one whole publisher spool, including files retained after failed local processing."""
    values = (staged_actual_bytes, remaining_requested_bytes)
    need(all(type(value) is int and value >= 0 for value in values), "invalid_publisher_staging_bytes")
    total = sum(values)
    if lease_limit_bytes is not None:
        need(type(lease_limit_bytes) is int and lease_limit_bytes >= 0, "invalid_publisher_lease_limit")
        need(total <= lease_limit_bytes, "spool_storage_deferred")
    return total


class PublisherStagingWindow:
    """Reserve growth before starting a whole group. Completed and failed bodies stay in usage."""
    def __init__(self, lease_limit_bytes, measure_staged, *, physical_free=None, minimum_free_bytes=0):
        self.limit = publisher_stage_projection(lease_limit_bytes, 0)
        self.minimum_free = publisher_stage_projection(minimum_free_bytes, 0)
        self.measure_staged = measure_staged
        self.physical_free = physical_free
        self._pending = 0
        self._lock = threading.Lock()

    @contextmanager
    def admit_group(self, requested_bytes):
        with self._lock:
            staged = self.measure_staged()
            pending = publisher_stage_projection(self._pending, requested_bytes)
            projected = publisher_stage_projection(staged, pending, lease_limit_bytes=self.limit)
            if self.physical_free is not None:
                need(self.physical_free() - pending >= self.minimum_free, "disk_buffer")
            self._pending = pending
        try:
            yield projected
        finally:
            with self._lock:
                self._pending -= requested_bytes


def publisher_capacity_projection(*, inactive_managed_bytes, staged_actual_bytes, remaining_requested_bytes,
                                  other_reserved_bytes, other_unspent_bytes, journal_growth_bytes,
                                  free_bytes, managed_limit_bytes, minimum_free_bytes):
    """Inactive usage excludes fully reserved spools; current physical free already reflects every staged file."""
    envelope = publisher_stage_projection(staged_actual_bytes, remaining_requested_bytes)
    values = (inactive_managed_bytes, other_reserved_bytes, other_unspent_bytes, journal_growth_bytes,
              free_bytes, managed_limit_bytes, minimum_free_bytes)
    need(all(type(value) is int and value >= 0 for value in values)
         and other_unspent_bytes <= other_reserved_bytes, "invalid_publisher_capacity")
    managed = inactive_managed_bytes + other_reserved_bytes + journal_growth_bytes + envelope
    free_after = free_bytes - other_unspent_bytes - journal_growth_bytes - remaining_requested_bytes
    need(managed <= managed_limit_bytes, "managed_storage_deferred")
    need(free_after >= minimum_free_bytes, "disk_buffer")
    return {"publisher_envelope_bytes": envelope, "projected_managed_bytes": managed,
            "projected_physical_free_bytes": free_after}


def publish_verified_group(drive, files, remote, manifest, objects, *, transfers=3, copy=True):
    """Publish immutable files and bind all remote IDs in a single grouped readback before returning proof."""
    need(isinstance(objects, dict) and objects and type(transfers) is int and 1 <= transfers <= 4
         and type(copy) is bool and isinstance(remote, str) and remote.rstrip("/")
         and not any(char in remote for char in "\r\n"), "publisher_upload_scope")
    for name, proof in objects.items():
        need(isinstance(name, str) and not re.search(r"[\\:\x00-\x1f]", name)
             and all(piece not in ("", ".", "..") for piece in name.split("/"))
             and isinstance(proof, dict) and type(proof.get("bytes")) is int and proof["bytes"] > 0
             and HASH.fullmatch(str(proof.get("sha256", "")))
             and re.fullmatch(r"[0-9a-f]{32}", str(proof.get("md5", ""))), "invalid_publisher_upload_artifact")
    # The same manifest drives copy and listing. Check its small control file once.
    with Path(manifest).open("rb") as stream:
        manifest_bytes = stream.read(CONTROL + 1)
    need(len(manifest_bytes) <= CONTROL, "publisher_upload_manifest")
    listed = manifest_bytes.decode("utf-8").splitlines()
    need(len(listed) == len(objects) and set(listed) == set(objects), "publisher_upload_manifest")
    if copy:
        drive.copy_batch(files, remote, manifest, transfers=min(transfers, len(objects)))
    observed = drive.stat_batch(remote, set(objects), manifest)
    need(isinstance(observed, dict) and set(observed) == set(objects), "publisher_upload_missing_objects")
    confirmed = {}
    ids = set()
    for path, proof in objects.items():
        entry = observed[path]
        storage.verify_remote(entry, proof)
        drive_id = entry.get("ID")
        need(isinstance(drive_id, str) and drive_id, "drive_id_missing")
        need(drive_id not in ids, "drive_id_duplicate")
        ids.add(drive_id)
        confirmed[path] = {**proof, "remote": remote.rstrip("/") + "/" + path, "drive_id": drive_id}
    return confirmed


def complete_receipt(record, item, remote):
    """Accept the original three-object publisher receipt as well as batch receipts."""
    if (record.get("kind") != kind_for(item) or record.get("status") != "verified" or
            any(record.get(k) != item.get(k) for k in ("provider", "watch_page_id", "associated_youtube_id", "channel_dir")) or
            record.get("accepted_api_sha256") != item["accepted_metadata"]["sha256"] or
            any(record.get(k) is not False for k in NATIVE_FLAGS)):
        return False
    if item.get("exact_youtube_crossreference") is True:
        try:
            exact_youtube_link(record.get("original_youtube_link"), item["associated_youtube_id"])
        except MirrorError:
            return False
        if record.get("association_method") != "publisher_rss_exact_youtube_id" or record.get("exact_youtube_crossreference") is not True or record.get("original_youtube_link") != item["original_youtube_link"]:
            return False
    audio = record.get("audio", {})
    expected_parent = f"{remote.rstrip('/')}/{item['channel_dir']}/Videos/{item['associated_youtube_id']}/PublisherVariants/{audio.get('sha256', '')}/"
    artifacts = [audio, record.get("provenance", {})]
    caps = record.get("caption_bundles", []) or ([record["caption_bundle"]] if record.get("caption_bundle") else [])
    if len(caps) != len(item["captions"]):
        return False
    for track in item["captions"]:
        if not any(c.get("provider_language_key") == track.get("provider_language_key", track["track_id"]) and c.get("language", "").lower() == track["language"].lower() for c in caps):
            return False
    for artifact in artifacts + caps:
        if not (isinstance(artifact, dict) and type(artifact.get("bytes")) is int and artifact["bytes"] > 0 and
                HASH.fullmatch(artifact.get("sha256", "")) and re.fullmatch(r"[0-9a-f]{32}", artifact.get("md5", "")) and
                isinstance(artifact.get("drive_id"), str) and artifact["drive_id"] and isinstance(artifact.get("remote"), str) and
                artifact["remote"].startswith(expected_parent) and
                all(p not in {"", ".", ".."} for p in artifact["remote"][len(expected_parent):].split("/"))):
            return False
    return True


def bound_legacy_scope(root, legacy_raw):
    """Read an explicit owner binding; missing/stale evidence never lifts a hold.

    The old cooldown is immutable. Only an independently preserved audio-only
    failure, its exact accepted plan, and the original deadline can scope it.
    """
    try:
        binding = read(root / "sync/publisher_mirror_legacy_scope_binding.json")
        need(binding.get("schema_version") == 1 and binding.get("authorization") == "root_agent_explicit_scope_binding" and
             binding.get("endpoint") == "audio" and SLUG.fullmatch(binding.get("provider", "")), "legacy_binding")
        legacy = json.loads(legacy_raw)
        need(binding.get("legacy_cooldown_sha256") == sha(legacy_raw) and
             binding.get("retry_not_before_epoch") == legacy["retry_not_before_epoch"] and
             legacy.get("error_class") in {"forbidden", "rate_limited"}, "legacy_binding")
        def pinned(pin):
            path = local(root, pin["path"])
            need(path.stat().st_size <= CONTROL and HASH.fullmatch(pin.get("sha256", "")), "legacy_binding")
            raw = path.read_bytes()
            need(sha(raw) == pin["sha256"], "legacy_binding")
            return path, json.loads(raw)
        _, evidence = pinned(binding["failure_evidence"])
        _, state = pinned(binding["failure_state_snapshot"])
        need(evidence.get("kind") == "publisher_audio_source_failure_binding" and
             evidence.get("provider") == binding["provider"] and evidence.get("artifact_kind") == "audio" and
             evidence.get("legacy_cooldown", {}).get("sha256") == sha(legacy_raw) and
             evidence.get("retry_not_before_epoch") == legacy["retry_not_before_epoch"] and
             evidence.get("error_class") == legacy["error_class"] and
             evidence.get("failure_state", {}).get("sha256") == binding["failure_state_snapshot"]["sha256"] and
             evidence.get("caption_request_started") is False and evidence.get("source_audio_requests_started") == 1 and
             evidence.get("audio_bytes_completed") == 0, "legacy_binding")
        plan_path, _ = pinned(evidence["plan"])
        plan_sha, items = load_items(root, plan_path)
        matches = [item for item in items if item["item_id"] == evidence.get("item_id")]
        need(len(matches) == 1 and matches[0]["provider"] == binding["provider"] and
             matches[0]["accepted_metadata"] == evidence["accepted_metadata"] and
             state.get("plan_sha256") == plan_sha and state.get("item_id") == evidence["item_id"] and
             state.get("started") == ["audio"] and state.get("downloads") == {} and
             state.get("error_class") == ("publisher_http_403" if legacy["error_class"] == "forbidden" else "publisher_http_429"), "legacy_binding")
        return {"provider": binding["provider"], "endpoint": "audio"}
    except (OSError, ValueError, KeyError, TypeError, AttributeError, MirrorError):
        return None


class MirrorBatch:
    def __init__(self, settings, drive, *, opener=None, probe=inspect_publisher_audio, disk_free=None):
        self.s = settings
        self.root = Path(settings.root).resolve()
        self.spool = self.root / "publisher_mirror"
        self.files = self.spool / "files"
        self.drive = drive
        self.opener = opener
        self.probe = probe
        self.disk_free = disk_free or (lambda: shutil.disk_usage(self.root).free)
        self.stop = threading.Event()
        self.source_stops = set()
        self._legacy_checked = 0
        self._legacy_raw = self._legacy_scope = None
        self.lock = threading.RLock()
        self._guard_at = self._inventory_at = 0
        self._lease = None
        self._external = 0
        self.budget = None
        self.trusted = {}
        self.plan_sha, self.items = load_items(self.root, settings.plan_path)
        roots = sorted({Path(p).resolve() for p in settings.managed_roots}, key=lambda p: len(p.parts))
        self.roots = [p for i, p in enumerate(roots) if not any(p.is_relative_to(q) for q in roots[:i])]
        need(type(settings.workers) is int and 1 <= settings.workers <= 2, "worker_admission")
        need(0 < settings.spool_cap_bytes <= MAX_MANAGED, "spool_admission")
        need(all(any(p.is_relative_to(q) for q in self.roots) for p in (self.root, Path(sys.prefix).resolve(), Path(__file__).resolve().parents[2])), "managed_roots_incomplete")
        need(settings.remote and not any(c in settings.remote for c in "\r\n"), "remote_destination")

    def guard(self, *, source=False, source_scope=None, force=False):
        with self.lock:
            now = time.time()
            if force or time.monotonic() - self._guard_at >= 1:
                lease = read(self.root / "sync/publisher_mirror_lease.json")
                plan = read(self.root / "sync/analysis_resource_plan.json")
                need(lease.get("state") == "active" and lease.get("owner") == self.s.owner and lease.get("lease_id") == self.s.lease_id, "publisher_lease_inactive")
                need(lease.get("worker_sha256") == sha(Path(__file__).read_bytes()) and lease.get("plan_sha256") == self.plan_sha, "publisher_code_plan_changed")
                need(lease.get("remote") == self.s.remote and lease.get("max_workers") == self.s.workers and
                     lease.get("spool_cap_bytes") == self.s.spool_cap_bytes and
                     {str(Path(p).resolve()) for p in lease.get("managed_roots", [])} == {str(Path(p).resolve()) for p in self.s.managed_roots}, "publisher_lease_scope")
                need(plan.get("collector_dispatch_allowed") is False and (self.root / "sync/STOP_DRIVE_INGEST").exists(), "collector_not_parked")
                need(0 < plan.get("accounting_cap_bytes", 0) <= MAX_MANAGED, "managed_cap")
                reservations = plan.get("reservations", [])
                own = [r for r in reservations if r.get("state") == "active" and r.get("lease_id") == self.s.lease_id and r.get("owner") == self.s.owner]
                need(len(own) == 1 and own[0].get("max_bytes", 0) >= self.s.spool_cap_bytes, "publisher_reservation_missing")
                self._other = sum(r["max_bytes"] for r in reservations if r.get("state") == "active" and r.get("lease_id") != self.s.lease_id)
                self._cap = min(MAX_MANAGED, plan["accounting_cap_bytes"])
                self._lease, self._guard_at = lease, time.monotonic()
            need(type(self._lease.get("expires_at_epoch")) in (int, float) and self._lease["expires_at_epoch"] > now, "publisher_lease_expired")
            need(not (self.root / "sync/STOP_PUBLISHER_MIRROR").exists(), "stopped")
            if source:
                need(not self.stop.is_set(), "publisher_source_stopped")
                need(isinstance(source_scope, dict) and source_scope.get("endpoint") in {"audio", "caption"} and
                     SLUG.fullmatch(source_scope.get("provider", "")), "publisher_source_scope")
                cooldown = self.root / "sync/publisher_mirror_source_cooldown.json"
                if cooldown.exists():
                    raw = cooldown.read_bytes()
                    need(len(raw) <= CONTROL, "control_document_size")
                    if json.loads(raw).get("retry_not_before_epoch", 0) > now:
                        if force or raw != self._legacy_raw or time.monotonic() - self._legacy_checked >= 1:
                            self._legacy_scope = bound_legacy_scope(self.root, raw)
                            self._legacy_raw, self._legacy_checked = raw, time.monotonic()
                        need(self._legacy_scope is not None, "publisher_source_cooldown")
                        need(self.scope_key(self._legacy_scope) != self.scope_key(source_scope), "publisher_endpoint_cooldown")
                # The historical file is never changed or its deadline reset.
                scope_key = self.scope_key(source_scope)
                need(scope_key not in self.source_stops, "publisher_endpoint_stopped")
                scoped = self.root / "sync/publisher_mirror_source_cooldowns.json"
                entry = read(scoped).get("scopes", {}).get(scope_key, {}) if scoped.exists() else {}
                need(entry.get("retry_not_before_epoch", 0) <= now, "publisher_endpoint_cooldown")
            if force or time.monotonic() - self._inventory_at >= 12:
                self._external = sum(native.tree_bytes(p) for p in self.roots) - native.tree_bytes(self.root)
                self._inventory_at = time.monotonic()
            cap = self._cap - self._external - self._other
            need(cap > CONTROL, "managed_storage_deferred")
            if self.budget:
                self.budget.cap = cap
                need(self.budget.usage() + self.budget._outstanding() <= cap - CONTROL, "managed_storage_deferred")
            need(self.disk_free() >= DISK_FLOOR, "disk_buffer")

    def write(self, out, data):
        with self.lock:
            need(native.tree_bytes(self.spool) + len(data) <= self.s.spool_cap_bytes, "spool_storage_deferred")
            need(self.disk_free() - len(data) >= DISK_FLOOR, "disk_buffer")
            self.budget.write(out, data)

    def save(self, path, value):
        raw = encoded(value)
        need(len(raw) <= CONTROL, "control_document_size")
        with self.lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_name(path.name + ".tmp")
            if temporary.exists():
                self.budget.remove(temporary)
            old = path.stat().st_size if path.exists() else 0
            with temporary.open("xb") as out:
                self.write(out, raw)
                os.fsync(out.fileno())
            os.replace(temporary, path)
            self.budget.changed(-old)

    @staticmethod
    def scope_key(scope):
        return sha(encoded({"provider": scope["provider"], "endpoint": scope["endpoint"]}))

    def request_scope(self, item, name, spec):
        scope = {"provider": item["provider"], "endpoint": "audio" if name == "audio" else "caption"}
        scope.update(item_id=item["item_id"], accepted_api_sha256=item["accepted_metadata"]["sha256"],
                     request_binding_sha256=sha(encoded({"accepted_api_sha256": item["accepted_metadata"]["sha256"],
                                                       "pointer": spec["url_pointer"], "request_kind": name})))
        return scope

    def refusal(self, code, scope):
        with self.lock:
            key = self.scope_key(scope)
            self.source_stops.add(key)
            path = self.root / "sync/publisher_mirror_source_cooldowns.json"
            value = read(path) if path.exists() else {"schema_version": 1, "scopes": {}}
            previous = value["scopes"].get(key, {})
            now = time.time()
            record = {"schema_version": 1, **scope, "error_class": code,
                      "first_refusal_epoch": previous.get("first_refusal_epoch", now), "latest_refusal_epoch": now,
                      "retry_not_before_epoch": max(previous.get("retry_not_before_epoch", 0), now + 86400),
                      "refusal_count": previous.get("refusal_count", 0) + 1, "automatic_retry": False}
            value["scopes"][key] = record
            self.save(path, value)
            with (self.root / "sync/publisher_mirror_source_refusals.jsonl").open("ab") as out:
                self.write(out, encoded(record))
                os.fsync(out.fileno())

    def owned(self, relative):
        path = local(self.root, relative)
        need(path.is_relative_to(self.spool), "artifact_outside_owned_spool")
        return path

    def download(self, item, state, state_path, name, spec, destination):
        previous = state.setdefault("downloads", {}).get(name)
        part = destination.with_suffix(destination.suffix + ".part")
        if previous:
            destination = self.owned(previous["relative"])
            move = state.get("audio_move", {})
            if name == "audio" and not destination.exists() and move.get("from") == previous["relative"]:
                candidate = self.owned(move["to"])
                if candidate.exists():
                    destination = candidate
                    previous["relative"] = move["to"]
            part = destination.with_suffix(destination.suffix + ".part")
            found = destination if destination.exists() else part
            need(found.exists() and storage.hash_file(found) == previous["proof"], "completed_local_changed")
            if found == part:
                os.replace(part, destination)
            self.trusted[str(destination)] = storage.fingerprint(destination)
            return previous["proof"]
        need(not destination.exists() and not part.exists() and name not in state.get("started", []), "partial_requires_review")
        scope = self.request_scope(item, name, spec)
        self.guard(source=True, source_scope=scope, force=True)
        state.setdefault("started", []).append(name)
        state.setdefault("source_requests", {})[name] = dict(scope, started_at=storage.utc_now())
        self.save(state_path, state)  # A crash/refusal cannot silently retry the same request.
        hosts, batch = item["allowed_hosts"], self
        class Redirect(HTTPRedirectHandler):
            count = 0
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                self.count += 1
                need(self.count <= 3, "publisher_redirect_limit")
                batch.guard(source=True, source_scope=scope, force=True)
                safe_url(newurl, hosts)
                return super().redirect_request(req, fp, code, msg, headers, newurl)
        opener = self.opener or build_opener(ProxyHandler({}), Redirect())
        try:
            with opener.open(Request(spec["url"], headers={"Accept-Encoding": "identity"}), timeout=30) as response:
                status = response.status
                if status in (403, 429):
                    self.refusal("forbidden" if status == 403 else "rate_limited", scope)
                need(status == 200 and not response.headers.get("Content-Range"), "publisher_response_status")
                need(response.headers.get("Content-Encoding", "identity").lower() in ("", "identity"), "publisher_content_encoding")
                length = response.headers.get("Content-Length", "")
                need(isinstance(length, str) and length.isdigit() and 0 < int(length) <= spec["maximum_bytes"], "publisher_content_length")
                expected = int(length)
                md5, digest, size = hashlib.md5(), hashlib.sha256(), 0
                with part.open("xb") as out:
                    while True:
                        self.guard(source=True, source_scope=scope)
                        block = (getattr(response, "read1", None) or response.read)(1024 * 1024)
                        if not block:
                            break
                        need(size + len(block) <= expected, "publisher_body_overrun")
                        self.write(out, block)
                        size += len(block)
                        md5.update(block)
                        digest.update(block)
                    os.fsync(out.fileno())
                need(size == expected, "publisher_body_truncated")
                proof = {"bytes": size, "md5": md5.hexdigest(), "sha256": digest.hexdigest()}
                state["downloads"][name] = {"proof": proof, "relative": destination.relative_to(self.root).as_posix()}
                self.save(state_path, state)  # hashes precede promotion; crash recovery checks either path
                os.replace(part, destination)
                self.trusted[str(destination)] = storage.fingerprint(destination)
                return proof
        except HTTPError as error:
            if error.code in (403, 429):
                self.refusal("forbidden" if error.code == 403 else "rate_limited", scope)
            raise MirrorError("publisher_http_" + str(error.code)) from None
        except (OSError, TimeoutError):
            raise MirrorError("publisher_network") from None

    def bundle(self, item, track, raw, proof, audio, target):
        normalized = normalize_caption(raw.read_bytes(), track["raw_format"])
        duration = item["audio"]["duration_seconds"]
        intervals = []
        for cue in normalized["segments"]:
            if cue["end"] is not None:
                need(cue["end"] <= duration + max(5, duration * .002), "caption_duration_mismatch")
                if cue["end"] > cue["start"]:
                    intervals.append((max(0, cue["start"]), min(duration, cue["end"])))
        merged = []
        for start, end in sorted(intervals):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        coverage = {"segment_count": len(normalized["segments"]), "cue_union_seconds_clamped": sum(b-a for a,b in merged),
                    "source_declared_duration_s": duration, "every_word_coverage_verified": False, "human_reviewed": False}
        provenance = {"schema_version": 1, "kind": "publisher_english_caption", "language": track["language"],
                      "caption_kind": track["kind"], "raw_format": track["raw_format"], "raw_caption": proof,
                      "source_audio_sha256": audio["sha256"], "accepted_api_sha256": item["accepted_metadata"]["sha256"],
                      "normalization_version": normalized["normalization_version"], "coverage": coverage, **NATIVE_FLAGS}
        provenance["language_evidence"] = {k: track[k] for k in ("language_basis", "track_language_verified", "translation_status", "origin") if k in track}
        members = {"raw." + track["raw_format"]: raw.read_bytes(), "segments.json": encoded(normalized),
                   "transcript.txt": normalized["text"].encode(), "provenance.json": encoded(provenance)}
        need(sum(map(len, members.values())) <= track["maximum_bytes"] * 8 + CONTROL, "caption_output_bound")
        members["manifest.json"] = encoded({k: {"bytes": len(v), "sha256": sha(v)} for k, v in members.items()})
        with target.open("xb") as out:
            with zipfile.ZipFile(storage._BudgetZipWriter(out, self), "w", zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
                for name, value in members.items():
                    archive.writestr(name, value)
            out.flush()
            os.fsync(out.fileno())
        with zipfile.ZipFile(target) as archive:
            need(archive.testzip() is None and set(archive.namelist()) == set(members), "caption_zip_integrity")
            need(all(archive.read(name) == value for name, value in members.items()), "caption_zip_integrity")
        return storage.hash_file(target), coverage

    def receipts(self):
        path = self.root / "sync/publisher_mirror_manifest.jsonl"
        return list(storage.read_jsonl(path)) if path.exists() else []

    def publish(self, item, state, state_path):
        artifacts = state["artifacts"]
        for artifact in artifacts:
            path = self.owned(artifact["path"])
            if not path.exists() and state.get("verified_receipt"):
                continue
            need(path.exists(), "local_artifact_missing")
            if self.trusted.get(str(path)) != storage.fingerprint(path):
                need(storage.hash_file(path) == artifact["proof"], "local_artifact_changed")
                self.trusted[str(path)] = storage.fingerprint(path)
        manifest = state_path.parent / "upload-files.txt"
        lines = [(self.owned(a["path"]).relative_to(self.files).as_posix()) for a in artifacts]
        with self.lock:
            if manifest.exists():
                self.budget.remove(manifest)
            with manifest.open("xb") as out:
                self.write(out, ("\n".join(lines) + "\n").encode())
                os.fsync(out.fileno())
        confirmed = publish_verified_group(self.drive, self.files, self.s.remote, manifest,
                                           {path: artifact["proof"] for path, artifact in zip(lines, artifacts)},
                                           transfers=2, copy=not bool(state.get("verified_receipt")))
        proofs = {artifact["kind"]: confirmed[path] for path, artifact in zip(lines, artifacts)}
        record = {k: item[k] for k in ("provider", "watch_page_id", "associated_youtube_id", "channel_dir", "association_method", "association_qualification", "exact_youtube_crossreference", "human_verified")}
        caps = [{**proofs[a["kind"]], **a["caption"]} for a in artifacts if a.get("caption")]
        record.update(schema_version=1, kind=kind_for(item), status="verified", verified_at=storage.utc_now(), item_id=item["item_id"],
                      variant_id=proofs["audio"]["sha256"], audio=proofs["audio"], provenance=proofs["provenance"],
                      accepted_api_sha256=item["accepted_metadata"]["sha256"], caption_bundles=caps,
                      caption_state="complete" if len(caps) == len(item["captions"]) else "pending",
                      provider_declared_duration_s=item["audio"]["duration_seconds"], actual_probe_duration_s=state["probe"]["duration_seconds"], **NATIVE_FLAGS)
        if item.get("declared_embed_id"):
            record["declared_embed_id"] = item["declared_embed_id"]
        if item.get("original_youtube_link"):
            record["original_youtube_link"] = item["original_youtube_link"]
        record["recording_equivalence_verified"] = False
        record["source_requests"] = state.get("source_requests", {})
        if len(caps) == 1:
            record["caption_bundle"] = caps[0]  # original live receipt compatibility
        with self.lock:
            journal = self.root / "sync/publisher_mirror_manifest.jsonl"
            with journal.open("ab") as out:
                self.write(out, encoded(record))
                os.fsync(out.fileno())
            state.update(status="verified", verified_receipt=record)
            self.save(state_path, state)
        # All remote proofs and a durable receipt precede any owned deletion.
        for artifact in artifacts:
            path = self.owned(artifact["path"])
            if path.exists():
                need(self.trusted.get(str(path)) == storage.fingerprint(path), "cleanup_local_changed")
        for artifact in artifacts:
            path = self.owned(artifact["path"])
            if path.exists():
                self.budget.remove(path)
        for download in state.get("downloads", {}).values():
            path = self.owned(download["relative"])
            if path.exists():
                if self.trusted.get(str(path)) != storage.fingerprint(path):
                    need(storage.hash_file(path) == download["proof"], "cleanup_raw_changed")
                self.budget.remove(path)
        state["status"] = "deleted"
        self.save(state_path, state)
        return record

    def process(self, item):
        job = self.spool / "jobs" / item["item_id"]
        job.mkdir(parents=True, exist_ok=True)
        state_path = job / "state.json"
        state = read(state_path) if state_path.exists() else {"schema_version": 1, "item_id": item["item_id"], "status": "new", "plan_sha256": self.plan_sha}
        need(state.get("item_id") == item["item_id"] and state.get("plan_sha256") == self.plan_sha, "local_plan_changed")
        complete = next((r for r in reversed(self.receipts()) if complete_receipt(r, item, self.s.remote)), None)
        if complete and state.get("status") in {"new", "deleted"}:
            return {"item_id": item["item_id"], "status": "already_verified"}
        audio_path = job / ("audio." + item["audio"]["extension"])
        cap = item["audio"]["maximum_bytes"]
        headroom = 2 * CONTROL + sum(t["maximum_bytes"] * 10 + CONTROL for t in item["captions"])
        key = item["item_id"]
        try:
            self.guard(force=True)
            with self.lock:
                reserved_path = audio_path.with_suffix(audio_path.suffix + ".part")
                if state.get("artifacts"):
                    cap, headroom, reserved_path = CONTROL, 0, job / "upload-files.txt"
                elif state.get("downloads", {}).get("audio"):
                    reserved_path = self.owned(state["downloads"]["audio"]["relative"])
                existing = reserved_path.stat().st_size if reserved_path.exists() else 0
                additional = max(0, cap + headroom - existing)
                publisher_stage_projection(native.tree_bytes(self.spool), self.budget._outstanding() + additional,
                                           lease_limit_bytes=self.s.spool_cap_bytes)
                self.budget.reserve_item(key, reserved_path, cap, headroom)
            if not state.get("artifacts"):
                audio = self.download(item, state, state_path, "audio", item["audio"], audio_path)
                audio_path = self.owned(state["downloads"]["audio"]["relative"])
                self.budget.completed_path(key, audio_path)
                if not state.get("probe"):
                    self.guard(force=True)
                    state["probe"] = self.probe(audio_path, {"codec": item["audio"]["codec"], "durationMs": round(item["audio"]["duration_seconds"] * 1000)}, self.s.ffprobe)
                    self.save(state_path, state)
                folder = self.files / item["channel_dir"] / "Videos" / item["associated_youtube_id"] / "PublisherVariants" / audio["sha256"]
                folder.mkdir(parents=True, exist_ok=True)
                artifacts, pending = [], []
                for track in item["captions"]:
                    raw = job / (track["track_id"] + "." + track["raw_format"])
                    temporary_bundle = job / (track["track_id"] + ".zip")
                    try:
                        previous = state.setdefault("caption_artifacts", {}).get(track["track_id"])
                        if previous:
                            target = self.owned(previous["path"])
                            need(target.exists() and storage.hash_file(target) == previous["proof"], "caption_bundle_changed")
                            artifacts.append(previous)
                            self.trusted[str(target)] = storage.fingerprint(target)
                            continue
                        proof = self.download(item, state, state_path, "caption:" + track["track_id"], track, raw)
                        need(not temporary_bundle.exists(), "caption_bundle_requires_review")
                        bundle_proof, coverage = self.bundle(item, track, raw, proof, audio, temporary_bundle)
                        target = folder / "Captions" / bundle_proof["sha256"] / "captions.zip"
                        target.parent.mkdir(parents=True, exist_ok=True)
                        need(not target.exists(), "caption_bundle_requires_review")
                        os.replace(temporary_bundle, target)
                        artifacts.append({"kind": "caption:" + track["track_id"], "path": target.relative_to(self.root).as_posix(), "proof": bundle_proof,
                                          "caption": {"language": track["language"], "provider_language_key": track.get("provider_language_key", track["track_id"]),
                                                      "provider_label": track.get("provider_label", "English"), "usable_timed_text": True, "coverage": coverage}})
                        artifacts[-1]["caption"].update({k: track[k] for k in ("language_basis", "track_language_verified", "translation_status", "origin") if k in track})
                        state["caption_artifacts"][track["track_id"]] = artifacts[-1]
                        self.save(state_path, state)
                        self.trusted[str(target)] = storage.fingerprint(target)
                    except Exception as error:
                        pending.append({"track_id": track["track_id"], "error_class": safe_error(error)})
                destination = folder / ("publisher-audio." + item["audio"]["extension"])
                if audio_path != destination:
                    need(not destination.exists(), "audio_destination_exists")
                    # Persist relocation before moving. Recovery can find either
                    # the prior completed path or the new destination.
                    state["audio_move"] = {"from": audio_path.relative_to(self.root).as_posix(), "to": destination.relative_to(self.root).as_posix()}
                    self.save(state_path, state)
                    os.replace(audio_path, destination)
                self.budget.completed_path(key, destination)
                self.trusted[str(destination)] = storage.fingerprint(destination)
                state["downloads"]["audio"]["relative"] = destination.relative_to(self.root).as_posix()
                self.save(state_path, state)
                artifacts.insert(0, {"kind": "audio", "path": destination.relative_to(self.root).as_posix(), "proof": audio})
                provenance = {"schema_version": 1, "artifact_kind": kind_for(item), "item_id": key, "association": {k: item[k] for k in
                    ("provider", "watch_page_id", "associated_youtube_id", "channel_dir", "association_method", "association_qualification", "exact_youtube_crossreference", "human_verified")},
                    "accepted_api_sha256": item["accepted_metadata"]["sha256"], "plan_sha256": self.plan_sha,
                    "worker_sha256": sha(Path(__file__).read_bytes()), "audio": audio, "probe": state["probe"],
                    "metadata_declared_audio_bytes": item["audio"].get("metadata_declared_bytes"), "caption_pending": pending, **NATIVE_FLAGS}
                provenance["publisher_metadata"] = item["public_metadata"]
                provenance["source_requests"] = state.get("source_requests", {})
                provenance["recording_equivalence_verified"] = False
                if item.get("original_youtube_link"):
                    provenance["association"]["original_youtube_link"] = item["original_youtube_link"]
                provenance_path = folder / "provenance.json"
                self.save(provenance_path, provenance)
                artifacts.insert(1, {"kind": "provenance", "path": provenance_path.relative_to(self.root).as_posix(), "proof": storage.hash_file(provenance_path)})
                self.trusted[str(provenance_path)] = storage.fingerprint(provenance_path)
                state.update(status="ready", artifacts=artifacts, caption_pending=pending)
                self.save(state_path, state)
            result = self.publish(item, state, state_path)
            return {"item_id": key, "status": "verified", "caption_state": result["caption_state"]}
        except Exception as error:
            state["error_class"] = safe_error(error)
            self.save(state_path, state)
            return {"item_id": key, "status": "held", "error_class": state["error_class"]}
        finally:
            self.budget.release(key)

    def run(self):
        storage.ensure_outside_git(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        with storage.exclusive_lock(self.root):
            self.guard(force=True)
            self.spool.mkdir(exist_ok=True)
            self.files.mkdir(exist_ok=True)
            self.budget = storage.Budget(self.root, self._cap - self._external - self._other, 0, DISK_FLOOR, reserve=CONTROL, cached=True)
            results = []
            with ThreadPoolExecutor(max_workers=self.s.workers) as pool:
                # Each worker must recheck the shared source breaker before GET.
                futures = [pool.submit(self.process, item) for item in self.items]
                for future in as_completed(futures):
                    results.append(future.result())
            return {"schema_version": 1, "items": results, "verified": sum(x["status"] in {"verified", "already_verified"} for x in results),
                    "held": sum(x["status"] == "held" for x in results), "caption_pending": sum(x.get("caption_state") == "pending" for x in results),
                    "native_counts_changed": False}


def safe_error(error):
    value = getattr(error, "kind", "")
    return value if isinstance(value, str) and re.fullmatch(r"[a-z0-9_]{1,80}", value) else "publisher_operation_failed"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--rclone", default="rclone")
    args = parser.parse_args(argv)
    value = read(args.settings)
    settings = Settings(**{**value, "root": Path(value["root"]), "plan_path": Path(value["plan_path"]), "managed_roots": [Path(p) for p in value["managed_roots"]]})
    if args.mode == "plan":
        digest, items = load_items(settings.root, settings.plan_path)
        result = {"plan_sha256": digest, "items": len(items), "workers": settings.workers,
                  "audio_maximum_bytes": sum(x["audio"]["maximum_bytes"] for x in items), "network_requests": 0}
    else:
        drive = storage.Rclone(args.rclone, cooldown_path=settings.root / "sync/drive_ingest_cooldown.json")
        result = MirrorBatch(settings, drive).run()
    print(json.dumps(result))
    return 3 if result.get("held") or result.get("caption_pending") else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"status": "held", "error_class": safe_error(error)}))
        raise SystemExit(3)
