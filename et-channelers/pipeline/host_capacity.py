"""Measure Windows host memory and budget new concurrent download workers.

Sample before launching a browser. Count each in-flight bootstrap once and
pass running media workers separately. Existing transfers can always drain.
Disk figures use decimal GB, matching the archive's working-set ledger.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass
from functools import lru_cache
import os


MIB = 1024**2
GIB = 1024**3
MIN_DISK_SPARE = 12_000_000_000
MAX_MANAGED_BYTES = 23_000_000_000


@dataclass(frozen=True)
class MemorySnapshot:
    physical_total: int
    physical_available: int
    commit_limit: int
    commit_used: int

    def __post_init__(self):
        if (any(type(n) is not int or n < 0 for n in
                (self.physical_total, self.physical_available, self.commit_limit, self.commit_used))
                or self.physical_total == 0 or self.physical_available > self.physical_total
                or self.commit_limit == 0):
            raise ValueError("Invalid host memory sample")


class _PerformanceInformation(ctypes.Structure):
    # Windows PERFORMANCE_INFORMATION. All memory counters are in pages.
    _fields_ = [("cb", ctypes.c_uint32)] + [
        (name, ctypes.c_size_t) for name in
        ("commit_total", "commit_limit", "commit_peak", "physical_total", "physical_available",
         "system_cache", "kernel_total", "kernel_paged", "kernel_nonpaged", "page_size")
    ] + [(name, ctypes.c_uint32) for name in ("handle_count", "process_count", "thread_count")]


@lru_cache(maxsize=1)
def _performance_query():
    if os.name != "nt":
        raise OSError("GetPerformanceInfo is available on Windows")
    query = ctypes.WinDLL("psapi", use_last_error=True).GetPerformanceInfo
    query.argtypes = [ctypes.POINTER(_PerformanceInformation), ctypes.c_uint32]
    query.restype = ctypes.c_int
    return query


def windows_memory():
    """One system-wide query, independent of other users' process identities."""
    info = _PerformanceInformation()
    info.cb = ctypes.sizeof(info)
    if not _performance_query()(ctypes.byref(info), info.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return MemorySnapshot(info.physical_total * info.page_size, info.physical_available * info.page_size,
                          info.commit_limit * info.page_size, info.commit_total * info.page_size)


def additional_bootstraps(sample, *, active_bootstraps=0, active_media=0, upload_transfers=0, maximum_bootstraps=2):
    """Bound additional simultaneous launches by available physical memory and commit.

    Reserve 768 MiB of working set and 1 GiB of commit per starting browser.
    Charge additional buffer headroom for workers already transferring or
    uploading. All reservations are estimates of future growth beyond the
    measured sample. Re-sample when a worker changes phase or RAM frees up.
    """
    if (not isinstance(sample, MemorySnapshot) or type(maximum_bootstraps) is not int
            or maximum_bootstraps not in (1, 2)
            or any(type(n) is not int or n < 0 for n in (active_bootstraps, active_media, upload_transfers))):
        raise ValueError("Invalid memory admission input")
    memory_floor = max(2 * GIB, sample.physical_total // 20)
    future_upload = upload_transfers * 40 * MIB
    available = sample.physical_available - memory_floor - active_media * 64 * MIB - future_upload
    commit = sample.commit_limit - sample.commit_used - 3 * GIB - active_media * 96 * MIB - future_upload
    possible = min(maximum_bootstraps, available // (768 * MIB), commit // GIB)
    return max(0, possible - active_bootstraps)


def disk_headroom(free_bytes, reserved_growth, new_growth=0):
    """Physical bytes still spendable after reservations and the 12 GB reserve."""
    if any(type(n) is not int or n < 0 for n in (free_bytes, reserved_growth, new_growth)):
        raise ValueError("Invalid disk headroom input")
    return free_bytes - reserved_growth - new_growth - MIN_DISK_SPARE
