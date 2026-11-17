"""Keep one yt-dlp/WPC browser context alive until the caller finishes its stream.

No optional packages are imported and no browser is started at module import.
Use ``info, lease = open_audio(url, timeout)`` and close the lease in the SAME
worker's finally block. There is no extraction/media retry or provider rotation
here. Timeout bounds admission and each socket operation, not total synchronous
extraction wall time. The caller continues to enforce its source cooldowns.
"""
from __future__ import annotations

import asyncio
import importlib
import inspect
import math
import re
import shutil
import tempfile
import threading
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

MAX_ACTIVE_LEASES = 4
MAX_ADMISSION_WAIT = 30.0
MAX_SOCKET_TIMEOUT = 30.0
_SLOTS = threading.BoundedSemaphore(MAX_ACTIVE_LEASES)
_CLEANUP_FAILED = threading.Event()
_INIT_LOCK = threading.Lock()
_THREAD = threading.local()
_YOUTUBE_DL = None

_MESSAGES = {
    "browser_busy": "Browser audio capacity is busy; item remains pending",
    "browser_thread": "Browser audio lease must close in its owning worker",
    "browser_context": "Browser audio requires a synchronous worker without another active lease",
    "browser_cleanup": "Browser audio cleanup did not complete normally",
    "tool_unavailable": "Browser audio dependencies could not initialize",
    "invalid_source": "Browser audio requires a valid public YouTube video URL",
    "invalid_timeout": "Browser audio timeout must be a finite positive number",
    "metadata": "Browser audio did not return metadata for the requested item",
    "live": "Live or upcoming recording remains pending",
    "bot_check": "YouTube requested an access check",
    "rate_limited": "YouTube requested a source cooldown",
    "forbidden": "YouTube refused the source request",
    "login_required": "YouTube requires authenticated access",
    "no_formats": "YouTube did not provide a selectable audio format",
    "unavailable": "YouTube reported the recording unavailable",
    "network": "Browser audio request did not complete",
    "other": "Browser audio extraction failed",
}


class BrowserAudioError(RuntimeError):
    def __init__(self, kind):
        self.kind = kind if kind in _MESSAGES else "other"
        super().__init__(_MESSAGES[self.kind])


def _classify(message, video_id=""):
    from common import classify_error
    kind = classify_error(message)
    if kind == "other" and video_id and re.search(
        r"(?im)^\s*(?:ERROR:\s*)?\[youtube\]\s+" + re.escape(video_id) +
        r":\s*(?:Premieres in\s+[^\r\n]+|This live event will begin\b[^\r\n]*)$", message or ""
    ):
        return "live"
    return kind


class _QuietLogger:
    """Only constant signals survive; no source messages, tokens or URLs stored."""
    def __init__(self, video_id):
        self.video_id = video_id
        self.error_kind = None
        self.caption_access_warning = False

    def debug(self, message, *args, **kwargs):
        pass

    info = debug
    trace = debug

    def warning(self, message, *args, **kwargs):
        if (re.search(r"(?i)\b(?:subtitles?|subs)\b", message or "") and
                re.search(r"(?i)\bPO[ -]?token\b", message or "") and
                re.search(r"(?i)\b(?:requires?|required|missing|not provided)\b", message or "")):
            self.caption_access_warning = True

    def error(self, message, *args, **kwargs):
        kind = _classify(message, self.video_id)
        if self.error_kind not in {"bot_check", "rate_limited", "forbidden", "login_required"}:
            self.error_kind = kind


def _configure(timeout):
    global _YOUTUBE_DL
    if _YOUTUBE_DL is not None:
        return _YOUTUBE_DL
    if not _INIT_LOCK.acquire(timeout=min(timeout, MAX_ADMISSION_WAIT)):
        raise BrowserAudioError("browser_busy")
    try:
        if _YOUTUBE_DL is not None:
            return _YOUTUBE_DL
        plugins = importlib.import_module("yt_dlp.plugins")
        plugins.load_all_plugins()
        wpc = importlib.import_module("yt_dlp_plugins.extractor.getpot_wpc")
        provider = importlib.import_module("yt_dlp.extractor.youtube.pot.provider")
        config_type = importlib.import_module("nodriver.core.config").Config
        youtube_dl = importlib.import_module("yt_dlp").YoutubeDL

        def fresh_headless_config(self, proxy=None):
            if proxy:
                raise BrowserAudioError("invalid_source")
            config = config_type(headless=True)
            lease = getattr(_THREAD, "lease", None)
            if lease is not None:
                lease._track_profile(config)
            return config

        wpc.WPCPTP.get_nodriver_config = fresh_headless_config
        provider.register_preference(wpc.WPCPTP)(lambda _provider, _request: 100000)
        _YOUTUBE_DL = youtube_dl
        return _YOUTUBE_DL
    except BrowserAudioError:
        raise
    except Exception:
        raise BrowserAudioError("tool_unavailable") from None
    finally:
        _INIT_LOCK.release()


def _current_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        return None


class BrowserAudioLease:
    """Idempotent owner-thread cleanup; cleanup warnings never mask a source error."""
    def __init__(self, previous_loop):
        self.owner_thread = threading.get_ident()
        self.closed = False
        self.cleanup_error = None
        self._ydl = None
        self._entered = False
        self._previous_loop = previous_loop
        self._loops = []
        self._profiles = set()

    def _track_loop(self, loop):
        if loop is not None and loop is not self._previous_loop and loop not in self._loops:
            # Async cleanup failures must not print websocket URLs or request data.
            loop.set_exception_handler(lambda _loop, _context: None)
            self._loops.append(loop)

    def _track_profile(self, config):
        if not config.uses_custom_data_dir:
            candidate = Path(config.user_data_dir).resolve()
            temporary = Path(tempfile.gettempdir()).resolve()
            if candidate.parent == temporary and candidate.name.startswith("uc_"):
                self._profiles.add(candidate)

    def close(self):
        if self.closed:
            return
        if threading.get_ident() != self.owner_thread:
            raise BrowserAudioError("browser_thread")
        self.closed = True
        self._track_loop(_current_loop())
        browsers = []
        if self._ydl is not None:
            for extractor in getattr(self._ydl, "_ies_instances", {}).values():
                director = getattr(extractor, "_pot_director", None)
                for provider in getattr(director, "providers", {}).values():
                    browser = getattr(provider, "_browser", None)
                    if browser is not None:
                        browser_loop = getattr(provider, "_WPCPTP__loop", None) or _current_loop()
                        browsers.append((browser, browser_loop, getattr(browser, "_process", None)))
                        self._track_loop(browser_loop)
        try:
            if self._ydl is not None:
                try:
                    if self._entered:
                        self._ydl.__exit__(None, None, None)
                    else:
                        self._ydl.close()
                except Exception:
                    self.cleanup_error = "browser_cleanup"
                    # An earlier close hook must not strand the remaining providers.
                    for hook in getattr(self._ydl, "_close_hooks", ()):
                        try:
                            hook()
                        except Exception:
                            pass
            for browser, browser_loop, process in browsers:
                try:
                    if not browser.stopped:
                        browser.stop()
                    # nodriver uses an asyncio subprocess. Let termination finish
                    # before cancelling its loop or removing its Windows profile.
                    if process is not None and getattr(process, "returncode", None) is None:
                        if inspect.iscoroutinefunction(process.wait):
                            asyncio.set_event_loop(browser_loop)
                            browser_loop.run_until_complete(asyncio.wait_for(process.wait(), timeout=2.0))
                        else:
                            process.wait(timeout=2.0)
                except Exception:
                    self.cleanup_error = "browser_cleanup"
            for loop in reversed(self._loops):
                if loop.is_closed():
                    continue
                try:
                    asyncio.set_event_loop(loop)
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.wait(pending, timeout=1.0))
                except Exception:
                    self.cleanup_error = "browser_cleanup"
                finally:
                    loop.close()
            for profile in self._profiles:
                try:
                    # Only exact temporary directories created by this lease qualify.
                    if profile.resolve().parent == Path(tempfile.gettempdir()).resolve() and profile.name.startswith("uc_"):
                        shutil.rmtree(profile)
                except FileNotFoundError:
                    pass
                except OSError:
                    self.cleanup_error = "browser_cleanup"
        finally:
            if self.cleanup_error:
                # Do not mask the original extraction/stream error, but do not
                # admit more browsers after uncertain cleanup in this process.
                _CLEANUP_FAILED.set()
            self._ydl = None
            _THREAD.lease = None
            asyncio.set_event_loop(self._previous_loop if self._previous_loop and not self._previous_loop.is_closed() else None)
            _SLOTS.release()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def _video_url(value):
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        video_id = (parsed.path.strip("/") if host == "youtu.be" else
                    parse_qs(parsed.query).get("v", [""])[0] if parsed.path == "/watch" else "")
        if parsed.scheme != "https" or parsed.username or parsed.password or host not in {
                "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"} or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            raise ValueError
        return f"https://www.youtube.com/watch?v={video_id}", video_id
    except (ValueError, TypeError, AttributeError):
        raise BrowserAudioError("invalid_source") from None


def open_audio(url, timeout, metadata_only=False, caption_intent=False):
    """Return ``(info, lease)``; retain lease until streaming/caption use ends.

    Admission waits at most min(timeout,30) seconds; each socket waits at most
    that amount. This synchronous API does not provide a hard extraction deadline.
    Metadata-only extraction tolerates absent formats and never fetches media.
    """
    try:
        timeout = float(timeout)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise BrowserAudioError("invalid_timeout") from None
    canonical_url, video_id = _video_url(url)
    if _CLEANUP_FAILED.is_set():
        raise BrowserAudioError("browser_cleanup")
    if getattr(_THREAD, "lease", None) is not None:
        raise BrowserAudioError("browser_context")
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise BrowserAudioError("browser_context")
    if not _SLOTS.acquire(timeout=min(timeout, MAX_ADMISSION_WAIT)):
        raise BrowserAudioError("browser_busy")
    if _CLEANUP_FAILED.is_set():
        _SLOTS.release()
        raise BrowserAudioError("browser_cleanup")
    lease = BrowserAudioLease(_current_loop())
    _THREAD.lease = lease
    logger = _QuietLogger(video_id)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        lease._track_loop(loop)
        youtube_dl = _configure(timeout)
        options = {
            "quiet": True, "no_warnings": False, "noprogress": True, "logger": logger,
            "proxy": "", "noplaylist": True, "skip_download": True, "simulate": True,
            "retries": 0, "extractor_retries": 0, "fragment_retries": 0, "file_access_retries": 0,
            "socket_timeout": min(timeout, MAX_SOCKET_TIMEOUT), "sleep_interval_requests": 0.75,
            "cachedir": False, "geo_bypass": False, "extractor_args": {"youtube": {"player_client": ["mweb"]}},
        }
        if metadata_only:
            options["ignore_no_formats_error"] = True
        else:
            options["format"] = "bestaudio[protocol=https][vcodec=none]"
        if metadata_only or caption_intent:
            options.update(writesubtitles=True, writeautomaticsub=True, subtitleslangs=["en.*"], subtitlesformat="json3/vtt")
        lease._ydl = youtube_dl(options)
        lease._ydl.__enter__()
        lease._entered = True
        info = lease._ydl.extract_info(canonical_url, download=False)
        lease._track_loop(_current_loop())
        if not isinstance(info, dict) or info.get("id") != video_id:
            raise BrowserAudioError("metadata")
        if info.get("is_live") or info.get("live_status") in {"is_live", "is_upcoming"}:
            raise BrowserAudioError("live")
        if logger.caption_access_warning:
            info["_caption_access_warning"] = "subtitle_access_requirement"
        return info, lease
    except BaseException as exc:
        lease.close()
        if isinstance(exc, BrowserAudioError):
            raise
        if not isinstance(exc, Exception):
            raise
        kind = _classify(str(exc), video_id)
        if logger.error_kind in {"bot_check", "rate_limited", "forbidden", "login_required"} or kind == "other":
            kind = logger.error_kind or kind
        raise BrowserAudioError(kind) from None
