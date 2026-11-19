"""Reuse a pure projection only within an unchanged, freshly validated snapshot.

This cache supplies no Source permission. The caller must still check current
STOP, lease/resource state, clock/deadlines and authority on every gate. Its key
must cover the mutable input and every immutable authority/history dependency;
current_key must observe those fingerprints again, not return a saved token.
"""
from copy import deepcopy
from dataclasses import dataclass
import math
from pathlib import Path
from threading import RLock


class ProjectionChanged(ValueError):
    pass


@dataclass(frozen=True)
class _Entry:
    key: object
    observed_at: float
    value: object


class ValidatedProjectionCache:
    """One bounded snapshot; no request retry or stale fallback."""
    def __init__(self,*,maximum_age_seconds=1.0):
        if (type(maximum_age_seconds) not in (int,float) or
                not math.isfinite(maximum_age_seconds) or not 0<maximum_age_seconds<=1):
            raise ValueError('bounded_projection_cache_age_required')
        self.maximum_age_seconds=maximum_age_seconds;self._entry=None;self._lock=RLock()
        self.hits=self.computations=0

    def get(self,key,*,now_epoch,current_key,compute):
        if type(now_epoch) not in (int,float) or not math.isfinite(now_epoch) or now_epoch<=0:
            raise ValueError('finite_projection_clock_required')
        with self._lock:
            if current_key()!=key:raise ProjectionChanged('projection_snapshot_changed_before_read')
            saved=self._entry
            if saved is not None and saved.key==key and 0<=now_epoch-saved.observed_at<=self.maximum_age_seconds:
                value=deepcopy(saved.value)
                if current_key()!=key:raise ProjectionChanged('projection_snapshot_changed_during_read')
                self.hits+=1;return value
            # A regressed clock, expired entry or changed snapshot always calls
            # the full mature computation. Exceptions are never cached.
            self._entry=None
            value=compute();self.computations+=1
            if current_key()!=key:raise ProjectionChanged('projection_snapshot_changed_during_computation')
            self._entry=_Entry(deepcopy(key),now_epoch,deepcopy(value))
            return value

    def invalidate(self):
        with self._lock:self._entry=None

    def project(self,paths,*,fingerprint,now_epoch,compute,maximum_snapshot_reads=3):
        """Resample only a changing local snapshot, never retry a request.

        Persistent instability remains an explicit hold. Real validation,
        parsing and policy exceptions propagate immediately without retry.
        """
        paths=tuple(sorted({Path(path).absolute() for path in paths},key=str))
        if not paths or type(maximum_snapshot_reads) is not int or not 1<=maximum_snapshot_reads<=3:
            raise ValueError('complete_bounded_projection_dependencies_required')
        def current_key():return tuple((str(path),fingerprint(path)) for path in paths)
        for attempt in range(maximum_snapshot_reads):
            try:return self.get(current_key(),now_epoch=now_epoch,current_key=current_key,compute=compute)
            except ProjectionChanged:
                if attempt+1==maximum_snapshot_reads:raise
