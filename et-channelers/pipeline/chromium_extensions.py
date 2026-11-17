"""Local-only extension setup for a NEW isolated Chromium profile.

Importing this module installs or launches nothing and grants no source admission.
Package acquisition/hash verification, disk accounting (including the browser
cache), receiver leases and source cooldowns remain the launcher's responsibility.
"""
from __future__ import annotations

import asyncio
import base64
from contextlib import asynccontextmanager
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import time
from typing import Any
from urllib.parse import urlsplit


DOWNLOADER_ID = "egndajoiodmfaakhopchlaikhpdjdcnb"
_ID = re.compile(r"[a-p]{32}\Z")


class ExtensionError(ValueError):
    """A constant diagnostic; never includes page content or session material."""


@dataclass(frozen=True)
class ExtensionSpec:
    directory: Path
    version: str
    name: str
    worker_path: str
    manifest_sha256: str
    keyed_id: str | None


@dataclass(frozen=True)
class ExtensionLaunch:
    downloader: ExtensionSpec
    adblocker: ExtensionSpec
    args: tuple[str, str]


@dataclass(frozen=True)
class LoadedExtension:
    worker: Any
    extension_id: str
    version: str


@dataclass
class ProjectChromiumSession:
    context: Any
    launch: ExtensionLaunch
    downloader_worker: Any
    adblocker: LoadedExtension
    closed: bool = False
    cleanup_error: str | None = None


def _key_id(key: Any) -> str | None:
    if key is None:
        return None
    try:
        raw = base64.b64decode(key, validate=True)
        if not raw:
            raise ValueError
    except (ValueError, TypeError):
        raise ExtensionError("extension_manifest_key") from None
    digest = hashlib.sha256(raw).hexdigest()[:32]
    return "".join(chr(ord("a") + int(c, 16)) for c in digest)


def _read_spec(value: str | Path) -> ExtensionSpec:
    text = str(value)
    if not text or "," in text or any(ord(c) < 32 for c in text):
        raise ExtensionError("extension_path_characters")
    try:
        path = Path(value).resolve(strict=True)
        directory = path.parent if path.name == "manifest.json" and path.is_file() else path
        if not directory.is_dir():
            raise ValueError
        if "," in str(directory) or any(ord(c) < 32 for c in str(directory)):
            raise ValueError
        manifest_path = directory / "manifest.json"
        if manifest_path.stat().st_size > 1_000_000:
            raise ValueError
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw)
    except (OSError, ValueError, TypeError):
        raise ExtensionError("extension_manifest_invalid") from None
    if not isinstance(manifest, dict) or type(manifest.get("manifest_version")) is not int or manifest["manifest_version"] != 3:
        raise ExtensionError("extension_manifest_version")
    version, name = manifest.get("version"), manifest.get("name")
    if not isinstance(version, str) or not re.fullmatch(r"\d+(?:\.\d+){0,3}", version) or not isinstance(name, str) or not name:
        raise ExtensionError("extension_manifest_identity")
    background = manifest.get("background")
    worker = background.get("service_worker") if isinstance(background, dict) else None
    # Chrome also accepts one leading slash relative to the extension root.
    # Normalize only our local lookup; never rewrite the official manifest.
    if isinstance(worker, str) and worker.startswith("/") and not worker.startswith("//"):
        worker = worker[1:]
    if (not isinstance(worker, str) or not worker or "\\" in worker or
            any(c in worker for c in ":?#%,") or any(ord(c) < 32 for c in worker) or
            PurePosixPath(worker).is_absolute() or any(p in {".", "..", ""} for p in worker.split("/"))):
        raise ExtensionError("extension_worker_path")
    try:
        resolved_worker = (directory / worker).resolve(strict=True)
        if not resolved_worker.is_file() or not resolved_worker.is_relative_to(directory):
            raise ValueError
    except (OSError, ValueError):
        raise ExtensionError("extension_worker_path") from None
    return ExtensionSpec(directory, version, name, worker, hashlib.sha256(raw).hexdigest(), _key_id(manifest.get("key")))


def build_extension_launch(downloader: str | Path, adblocker: str | Path) -> ExtensionLaunch:
    """Validate two local MV3 directories (or manifest.json paths) and flags."""
    first, second = _read_spec(downloader), _read_spec(adblocker)
    if first.directory == second.directory:
        raise ExtensionError("duplicate_extension_path")
    if first.keyed_id != DOWNLOADER_ID:
        raise ExtensionError("downloader_identity_mismatch")
    if second.keyed_id == DOWNLOADER_ID:
        raise ExtensionError("duplicate_extension_identity")
    joined = ",".join(str(spec.directory) for spec in (first, second))
    return ExtensionLaunch(first, second, (f"--disable-extensions-except={joined}", f"--load-extension={joined}"))


def _bounds(timeout_seconds: float, poll_interval_seconds: float) -> None:
    if any(type(x) not in (int, float) or not math.isfinite(x) for x in (timeout_seconds, poll_interval_seconds)):
        raise ExtensionError("extension_wait_bounds")
    if not 0 < timeout_seconds <= 60 or not 0 < poll_interval_seconds <= 1:
        raise ExtensionError("extension_wait_bounds")


def _worker_id(worker: Any, path: str) -> str | None:
    try:
        url = urlsplit(worker.url)
        if (url.scheme == "chrome-extension" and _ID.fullmatch(url.netloc) and
                url.path == "/" + path and not url.query and not url.fragment):
            return url.netloc
    except (AttributeError, ValueError, TypeError):
        pass
    return None


async def select_downloader_worker(context: Any, spec: ExtensionSpec, *, timeout_seconds: float = 20,
                                   poll_interval_seconds: float = .05) -> Any:
    """Find the exact downloader ID AND declared worker path, independent of order."""
    _bounds(timeout_seconds, poll_interval_seconds)
    if spec.keyed_id != DOWNLOADER_ID:
        raise ExtensionError("downloader_identity_mismatch")
    deadline = time.monotonic() + timeout_seconds
    while True:
        matches = [w for w in context.service_workers if _worker_id(w, spec.worker_path) == DOWNLOADER_ID]
        if len(matches) > 1:
            raise ExtensionError("ambiguous_downloader_worker")
        if matches:
            return matches[0]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ExtensionError("downloader_worker_timeout")
        await asyncio.sleep(min(poll_interval_seconds, remaining))


async def select_adblock_worker(context: Any, spec: ExtensionSpec, *, timeout_seconds: float = 20,
                               poll_interval_seconds: float = .05) -> LoadedExtension:
    """Read the other worker's actual manifest; never guess an unpacked ID.

    A localized manifest name is deliberately not used as identity. The exact
    loaded version/MV3/worker path, and public-key ID when supplied, must match.
    """
    _bounds(timeout_seconds, poll_interval_seconds)
    deadline = time.monotonic() + timeout_seconds
    while True:
        matches = []
        for worker in context.service_workers:
            actual_id = _worker_id(worker, spec.worker_path)
            if not actual_id or actual_id == DOWNLOADER_ID or (spec.keyed_id and actual_id != spec.keyed_id):
                continue
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ExtensionError("adblock_worker_timeout")
            try:
                manifest = await asyncio.wait_for(worker.evaluate("chrome.runtime.getManifest()"), remaining)
            except asyncio.TimeoutError:
                raise ExtensionError("adblock_worker_timeout") from None
            except Exception:
                continue  # A worker may terminate while Chromium is starting it.
            if (isinstance(manifest, dict) and type(manifest.get("manifest_version")) is int and
                    manifest["manifest_version"] == 3 and manifest.get("version") == spec.version and
                    isinstance(manifest.get("background"), dict) and
                    manifest["background"].get("service_worker") in (spec.worker_path, "/" + spec.worker_path) and
                    (not spec.keyed_id or _key_id(manifest.get("key")) == spec.keyed_id)):
                matches.append(LoadedExtension(worker, actual_id, spec.version))
        if len(matches) > 1:
            raise ExtensionError("ambiguous_adblock_worker")
        if matches:
            return matches[0]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ExtensionError("adblock_worker_timeout")
        await asyncio.sleep(min(poll_interval_seconds, remaining))


def _launch_args(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        raise ExtensionError("chromium_launch_arguments")
    forbidden = {"--load-extension", "--disable-extensions-except", "--disable-extensions",
                 "--disable-component-extensions-with-background-pages", "--user-data-dir",
                 "--profile-directory", "--app", "--app-id", "--load-and-launch-app",
                 "--homepage", "--new-window", "--restore-last-session", "--url"}
    for value in values:
        if (not isinstance(value, str) or not value.startswith("--") or value == "--" or
                any(ord(c) < 32 for c in value) or value.split("=", 1)[0] in forbidden):
            raise ExtensionError("chromium_launch_arguments")
    return list(values)


@asynccontextmanager
async def launch_project_chromium(playwright: Any, *, owned_profile_path: str | Path,
                                  executable_path: str | Path, downloader_dir: str | Path,
                                  adblocker_dir: str | Path, headless: bool = False,
                                  launch_args: tuple[str, ...] | list[str] = (),
                                  worker_timeout_seconds: float = 20,
                                  service_workers: str = "block",
                                  viewport: dict[str, int] | None = None):
    """Launch both extensions in a fresh explicit profile, without navigation.

    Use INSIDE the caller's async_playwright context. The caller owns resource
    accounting, any network-isolation flags, source admission and profile cleanup.
    Nonempty profiles are refused, including any existing personal profile.
    """
    _bounds(worker_timeout_seconds, .05)
    args = _launch_args(launch_args)
    if type(headless) is not bool or service_workers not in {"block", "allow"}:
        raise ExtensionError("chromium_launch_options")
    if viewport is not None and (not isinstance(viewport, dict) or set(viewport) != {"width", "height"} or
                                 any(type(x) is not int or not 100 <= x <= 4096 for x in viewport.values())):
        raise ExtensionError("chromium_launch_options")
    launch = build_extension_launch(downloader_dir, adblocker_dir)
    try:
        original = Path(owned_profile_path)
        if original.is_symlink() or getattr(original, "is_junction", lambda: False)():
            raise ValueError
        profile = original.resolve()
        executable = Path(executable_path).resolve(strict=True)
        if (profile == profile.parent or not profile.parent.is_dir() or not executable.is_file() or
                (profile.exists() and (not profile.is_dir() or any(profile.iterdir())))):
            raise ValueError
    except (OSError, ValueError, TypeError):
        raise ExtensionError("chromium_owned_paths") from None
    context = await playwright.chromium.launch_persistent_context(
        str(profile), executable_path=str(executable), headless=headless,
        args=[*launch.args, *args], service_workers=service_workers,
        **({"viewport": viewport} if viewport is not None else {}))
    session = None
    failed = False
    try:
        downloader = await select_downloader_worker(context, launch.downloader, timeout_seconds=worker_timeout_seconds)
        try:
            manifest = await asyncio.wait_for(downloader.evaluate("chrome.runtime.getManifest()"), worker_timeout_seconds)
        except Exception:
            raise ExtensionError("downloader_manifest_unavailable") from None
        if (not isinstance(manifest, dict) or type(manifest.get("manifest_version")) is not int or
                manifest["manifest_version"] != 3 or manifest.get("version") != launch.downloader.version or
                not isinstance(manifest.get("background"), dict) or
                manifest["background"].get("service_worker") not in (launch.downloader.worker_path, "/" + launch.downloader.worker_path)):
            raise ExtensionError("downloader_manifest_mismatch")
        blocker = await select_adblock_worker(context, launch.adblocker, timeout_seconds=worker_timeout_seconds)
        session = ProjectChromiumSession(context, launch, downloader, blocker)
        yield session
    except BaseException:
        failed = True
        raise
    finally:
        try:
            await asyncio.wait_for(context.close(), timeout=15)
            if session is not None:
                session.closed = True
        except Exception:
            if session is not None:
                session.cleanup_error = "context_close_unconfirmed"
            if not failed:
                raise ExtensionError("context_close_unconfirmed") from None
