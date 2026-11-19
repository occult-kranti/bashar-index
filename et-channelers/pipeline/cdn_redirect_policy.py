"""Validate one server-issued HTTPS redirect for an already selected media asset.

The downloader checks the final HTTP response before opening the local sink.
Declared URL length is optional. An absent length on both sides requires the
same duration and media type as well as the same asset, format and version.
"""
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import parse_qs, urljoin, urlsplit


CONTRACT = "qualified18_one_checked_googlevideo_redirect_v2"
IDENTITY_QUERY = ("id", "itag", "clen", "lmt", "mime", "dur", "xtags", "expire")
REDIRECT_STATUSES = (301, 302, 303, 307, 308)
HEX = re.compile(r"[0-9a-f]{64}")
HOST = re.compile(r"[a-zA-Z0-9.-]{1,253}")


class Hold(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def need(condition, code):
    if not condition:
        raise Hold(code)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def artifact():
    # Git checkouts may represent the same Python source with CRLF on Windows.
    # Runtime admission separately pins the actual installed file.
    raw = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    return {"sha256": sha(raw), "bytes": len(raw)}


def safe_host(host):
    return (isinstance(host, str) and HOST.fullmatch(host) is not None
            and host.endswith(".googlevideo.com") and all(label and len(label) <= 63 for label in host.split(".")))


def original_identity(uri, *, now_epoch):
    need(isinstance(uri, str) and 0 < len(uri) <= 32768 and not any(ord(c) < 32 for c in uri),
         "selected_public_URI_required")
    try:
        parts = urlsplit(uri)
        port = parts.port
        query = parse_qs(parts.query, keep_blank_values=True, max_num_fields=256)
    except ValueError:
        raise Hold("invalid_selected_URI") from None
    need(parts.scheme == "https" and safe_host(parts.hostname) and parts.path == "/videoplayback"
         and parts.username is None and parts.password is None and port in (None, 443) and not parts.fragment,
         "selected_public_URI_required")
    need(all(len(query.get(key, [])) == 1 and query[key][0] for key in ("id", "itag", "lmt", "expire")),
         "unique_selected_asset_version_required")
    need(all(len(query.get(key, [])) <= 1 for key in IDENTITY_QUERY), "ambiguous_selected_version")
    need(query["itag"] == ["18"] and query.get("mime") in (None, ["video/mp4"]),
         "selected18_MIME_required")
    numbers = ("lmt", "expire", "clen") if "clen" in query else ("lmt", "expire")
    need(all(re.fullmatch(r"[0-9]{1,22}", query[key][0]) for key in numbers),
         "selected18_numeric_version_required")
    length = int(query["clen"][0]) if "clen" in query else None
    if length is None:
        duration = query.get("dur", [""])[0]
        need(query.get("mime") == ["video/mp4"] and re.fullmatch(r"[0-9]{1,10}(?:\.[0-9]{1,12})?", duration)
             and float(duration) > 0, "missing_URI_extent_requires_duration_and_media_type")
    else:
        need(0 < length <= 2**63 - 1, "selected18_extent_required")
    expiry = int(query["expire"][0])
    need(type(now_epoch) in (int, float) and math.isfinite(now_epoch) and expiry > now_epoch, "selected_URI_expired")
    identity = {k: query.get(k) for k in IDENTITY_QUERY}
    evidence = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return {"declared_source_bytes": length, "expires_at_epoch": expiry, "identity_query_sha256": sha(evidence)}


def approve(original, current, location, *, status, retry_after_values, now_epoch):
    need(type(status) is int and status in REDIRECT_STATUSES, "ordinary_redirect_status_required")
    need(type(retry_after_values) is list and not retry_after_values, "Retry_After_directive_requires_hold")
    need(current == original, "one_redirect_only")
    need(isinstance(location, str) and 0 < len(location) <= 32768 and not any(ord(c) < 32 for c in location),
         "unsafe_redirect_Location")
    source = original_identity(original, now_epoch=now_epoch)
    target = urljoin(current, location)
    need(target != current, "redirect_loop")
    need(original_identity(target, now_epoch=now_epoch) == source, "redirect_asset_version_changed")
    witness = {"schema_version": 1, "status": status, "request_url_sha256": sha(current.encode()),
               "location_sha256": sha(location.encode()), "final_url_sha256": sha(target.encode()),
               "destination_hostname": urlsplit(target).hostname, "retry_after_header_count": 0,
               "retry_after_present": False, "same_selected_asset_version": True,
               "identity_query_fields": list(IDENTITY_QUERY), **source, "observed_at_epoch": now_epoch,
               "observed_before_follow": True, "maximum_redirects": 1}
    if source["declared_source_bytes"] is None:
        witness.update(schema_version=2, extent_basis="final_http_content_length")
    return target, witness


def validate_safe_proof(proof, *, original_sha256, final_sha256, content_length=None):
    need(type(proof) is dict and type(proof.get("schema_version")) is int and proof["schema_version"] in (1, 2)
         and type(proof.get("status")) is int and proof["status"] in REDIRECT_STATUSES
         and proof.get("request_url_sha256") == original_sha256 and proof.get("final_url_sha256") == final_sha256
         and original_sha256 != final_sha256, "redirect_hash_binding")
    digests = ("request_url_sha256", "location_sha256", "final_url_sha256", "identity_query_sha256")
    need(all(isinstance(proof.get(key), str) and HEX.fullmatch(proof[key]) for key in digests),
         "redirect_digest_required")
    need(safe_host(proof.get("destination_hostname")), "redirect_CDN_hostname_required")
    need(proof.get("retry_after_present") is False and proof.get("same_selected_asset_version") is True
         and proof.get("observed_before_follow") is True and proof.get("observation_durable_before_follow") is True
         and proof.get("follow_only_after_approval") is True and proof.get("identity_query_fields") == list(IDENTITY_QUERY)
         and type(proof.get("maximum_redirects")) is int and proof["maximum_redirects"] == 1,
         "one_checked_redirect_required")
    need(all(type(proof.get(k)) is int and proof[k] == 0 for k in (
        "retry_after_header_count", "explicit_redirect_body_reads", "redirect_body_writes")), "unexpected_redirect_data")
    at, expiry = proof.get("observed_at_epoch"), proof.get("expires_at_epoch")
    need(type(at) in (float, int) and math.isfinite(at) and type(expiry) is int and expiry > at, "redirect_expired")
    size = proof.get("declared_source_bytes")
    if proof["schema_version"] == 1:
        need(type(size) is int and 0 < size <= 2**63 - 1 and "extent_basis" not in proof, "redirect_extent_required")
        if content_length is not None:
            need(type(content_length) is int and content_length == size, "redirect_ContentLength_asset_extent_changed")
    else:
        need("declared_source_bytes" in proof and size is None and proof.get("extent_basis") == "final_http_content_length",
             "final_HTTP_extent_basis_required")
        if content_length is not None:
            need(type(content_length) is int and 0 < content_length <= 2**63 - 1, "final_positive_HTTP_extent_required")
    return True
