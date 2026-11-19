"""Source-free mutable telemetry I/O; NEVER an authority/control reader.

The only accepted destination is a job's progress.json.
No retries, ACL changes, HTTP interfaces or immutable-control relaxations exist.
"""
from contextlib import contextmanager
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re

MAX_BYTES = 16 * 1024**2
_NAME = re.compile(r'progress\.json\Z')


class ObservationChanged(ValueError):
    pass


def _checked(path, root):
    path, root = Path(path), Path(root)
    if not root.is_absolute() or not path.is_absolute() or '..' in path.parts:
        raise ValueError('absolute_observation_path_required')
    # The caller supplies the exact owned job directory. Keep this primitive
    # portable; it is not a discovery mechanism or an authority reader.
    if root.resolve() != root.absolute():
        raise ValueError('linked_observation_root_rejected')
    if path.parent != root or not root.is_dir() or not _NAME.fullmatch(path.name):
        raise ValueError('mutable_observation_path_only')
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
            raise ValueError('linked_observation_path_rejected')
        if part == root:
            break
    return path


def _fp(stat):
    return (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino, stat.st_dev)


def _failure(error, stage, path):
    # Raw error text/filename may contain secrets. Only enumerated local facts.
    error.safe_io_failure = {
        'exception_class': type(error).__name__,
        'errno': error.errno if type(error.errno) is int else None,
        'winerror': getattr(error, 'winerror', None) if type(getattr(error, 'winerror', None)) is int else None,
        'stage': stage, 'contained_relative_path': path.name,
        'path_role': 'mutable_observation_snapshot',
        'automatic_retry_allowed': False,
    }
    return error


def atomic_observation(path, value, *, root):
    """Same pending/fsync/replace transaction, with safe actual-stage errors.

    Replacement remains atomic. A failure never removes/retries a retained
    pending file; filesystem partial-failure state requires separate review.
    """
    path = _checked(path, root)
    pending = path.with_name(path.name + '.native.pending')
    if pending.exists():
        raise ValueError('pending_control_requires_review')
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                         allow_nan=False).encode('utf-8')
    if not 0 < len(encoded) <= MAX_BYTES:
        raise ValueError('observation_size_cap')
    stage, stream = 'pending_open', None
    try:
        stream = pending.open('xb')
        stage = 'pending_write'
        if stream.write(encoded) != len(encoded):
            raise OSError('short_observation_write')
        stage = 'pending_flush'
        stream.flush()
        stage = 'pending_fsync'
        os.fsync(stream.fileno())
        stage = 'pending_close'
        stream.close()
        stream = None
        stage = 'replace'
        _replace(pending, path)
    except OSError as error:
        raise _failure(error, stage, path)
    finally:
        if stream is not None:
            try:
                stream.close()
            except OSError:
                # Do not mask the first actual writer failure.
                pass


def _replace(pending, path):
    if os.name != 'nt' or not path.exists():
        os.replace(pending, path)
        return
    # MoveFileEx (Python os.replace) still fails on this PC with a delete-
    # sharing read handle. ReplaceFile is designed for replacing an existing
    # file and uses delete sharing. Flags=0: preserve security/ACL failures.
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    replace = kernel.ReplaceFileW
    replace.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR,
                        wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID]
    replace.restype = wintypes.BOOL
    if not replace(str(path), str(pending), None, 0, None, None):
        raise ctypes.WinError(ctypes.get_last_error())


@contextmanager
def open_observation(path, *, root):
    """Open mutable telemetry with Windows delete sharing, bounded by caller.

    The old file remains readable if atomically replaced. read_observation()
    checks identities afterward and rejects that stale sample.
    """
    path = _checked(path, root)
    if os.name != 'nt':
        with path.open('rb') as stream:
            yield stream
        return
    from ctypes import wintypes
    import msvcrt
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    handle = create(str(path), 0x80000000, 0x1 | 0x2 | 0x4, None, 3, 0x00200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        close(handle)
        raise
    with os.fdopen(fd, 'rb') as stream:
        yield stream


def _read_bounded(stream):
    return stream.read(MAX_BYTES + 1)


def read_observation(path, *, root):
    """Return one unchanged sample, or hold this sample without authority use."""
    path = _checked(path, root)
    before_path = _fp(path.stat())
    with open_observation(path, root=root) as stream:
        before_handle = _fp(os.fstat(stream.fileno()))
        raw = _read_bounded(stream)
        after_handle = _fp(os.fstat(stream.fileno()))
        after_path = _fp(path.stat())
    if not 0 < len(raw) <= MAX_BYTES:
        raise ObservationChanged('observation_size_cap')
    # Windows path.stat and fstat can expose different ctime meanings after
    # ReplaceFile preserves the destination's creation time. Each remains
    # unchanged independently; cross-handle identity uses size/mtime/fileID/dev.
    same_identity = lambda a, b: (a[0], a[1], a[3], a[4]) == (b[0], b[1], b[3], b[4])
    if not (before_path == after_path and before_handle == after_handle
            and same_identity(before_path, before_handle)) or len(raw) != before_path[0]:
        raise ObservationChanged('observation_changed_during_read')
    return json.loads(raw)
