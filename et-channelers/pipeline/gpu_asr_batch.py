"""Bounded local state for a post-collection CUDA batch with a parked collector."""

import hashlib
import json
import math
import os
import shutil
import sqlite3
import tempfile
import time
from types import SimpleNamespace
import warnings
import zlib

from . import gpu_asr as base, host_capacity


def paired_limit(duration):
    """Bound the expanded result independently of small control documents."""
    base.require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0,
                 "invalid_duration")
    return min(256_000_000, max(base.MAX_RESULT_BYTES, 4_000_000 + math.ceil(duration * 3_000)))


def write_review(path, value):
    """Keep a completed review decision across a process or machine restart."""
    data = base.encoded(value)
    base.require(len(data) <= base.MAX_RESULT_BYTES, "result_size")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".part", delete=False) as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    os.replace(output.name, path)


class StorageBudget:
    """Account for inputs, checkpoints and results between full inventories.

    Charges remain conservative until a periodic measurement or reservation change.
    Physical free space is checked against the live volume at each admission/write.
    """

    def __init__(self, settings):
        self.settings = settings
        self.plan_path = settings.root / "sync/analysis_resource_plan.json"
        self.measurement = None
        self.stamp = None
        self.charged = 0
        self.jobs = 0
        self.measured_at = 0
        self.current_growth = 0

    def plan_stamp(self):
        plan = self.plan_path.stat()
        return plan.st_size, plan.st_mtime_ns, plan.st_ino

    def admit(self, amount):
        base.require(type(amount) is int and amount >= 0, "invalid_storage_growth")
        stamp = self.plan_stamp()
        current = self.measurement
        if (current is None or self.stamp != stamp or self.jobs >= 32
                or time.monotonic() - self.measured_at >= 1_800
                or current["managed_bytes"] + current["active_reservation_headroom_bytes"]
                    + self.charged + amount > current["cap_bytes"]):
            self.measurement = base.inventory(self.settings, extra=amount)
            self.stamp = stamp
            self.measured_at = time.monotonic()
            self.charged = 0
            self.jobs = 0
        self.current_growth = amount
        self.physical(amount)
        self.charged += amount
        self.jobs += 1

    def physical(self, amount=0):
        stamp = self.plan_stamp()
        if self.stamp != stamp:
            # A reservation can change during a long recording. Re-admit its remaining
            # worst-case growth against the new plan before writing another checkpoint.
            self.measurement = base.inventory(self.settings, extra=max(amount, self.current_growth))
            self.stamp = stamp
            self.measured_at = time.monotonic()
            self.charged = self.current_growth
            self.jobs = 1
        reserved = self.measurement["active_reservation_headroom_bytes"]
        free = shutil.disk_usage(self.settings.root).free
        base.require(host_capacity.disk_headroom(free, reserved, amount) >= 0, "physical_disk_reserve")


class PublicationIndex:
    """Index new journal lines under the publisher's existing append lock."""

    def __init__(self):
        self.records = {}
        self.position = 0
        self.file_identity = None

    def refresh(self, path):
        if not path.exists():
            base.require(self.position == 0, "asr_journal_disappeared")
            return self.records
        with path.open("rb") as journal:
            stat = os.fstat(journal.fileno())
            identity = stat.st_dev, stat.st_ino
            base.require(self.file_identity in (None, identity) and self.position <= stat.st_size,
                         "asr_journal_replaced")
            journal.seek(self.position)
            for line in journal:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line.decode("utf-8-sig"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    # append_jsonl preserves a torn write and separates the next record.
                    # Only a complete receipt can release its source or satisfy an association.
                    warnings.warn(f"Skipping incomplete ASR journal record at byte {journal.tell() - len(line)}", RuntimeWarning)
                    continue
                base.require(isinstance(record, dict), "invalid_asr_journal_record")
                key = record.get("source_key"), record.get("run_id")
                base.require(key not in self.records or self.records[key] == record, "asr_journal_conflict")
                self.records[key] = record
            self.file_identity = identity
            self.position = journal.tell()
        return self.records


class WindowStore:
    """Persist one fully consumed model window per source/model/task binding."""

    MAX_WINDOW_BYTES = 4_000_000

    def __init__(self, path, binding, capacity_check=None, max_bytes=None):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.binding = binding
        self.capacity_check = capacity_check
        self.path = path
        self.max_bytes = max_bytes
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS windows "
            "(binding TEXT, task TEXT, idx INTEGER, digest TEXT, payload BLOB, PRIMARY KEY (binding,task,idx))"
        )
        self.db.commit()

    def load(self, task, index):
        where = " FROM windows WHERE binding=? AND task=? AND idx=?"
        key = self.binding, task, index
        row = self.db.execute("SELECT digest, length(payload)" + where, key).fetchone()
        if row is None:
            return None
        digest, size = row
        base.require(0 < size <= self.MAX_WINDOW_BYTES, "asr_window_size")
        packed = self.db.execute("SELECT payload" + where, key).fetchone()[0]
        decoder = zlib.decompressobj()
        raw = decoder.decompress(packed, self.MAX_WINDOW_BYTES + 1)
        base.require(len(raw) <= self.MAX_WINDOW_BYTES and decoder.eof and not decoder.unused_data
                     and hashlib.sha256(raw).hexdigest() == digest, "asr_window_checksum")
        return json.loads(raw)

    def save(self, task, index, value):
        raw = base.encoded(value)
        base.require(len(raw) <= self.MAX_WINDOW_BYTES, "asr_window_size")
        packed = zlib.compress(raw, level=1)
        base.require(len(packed) <= self.MAX_WINDOW_BYTES, "asr_window_size")
        growth = 2 * len(packed) + 65_536
        if self.max_bytes is not None:
            base.require(self.path.stat().st_size + growth <= self.max_bytes, "asr_checkpoint_budget")
        if self.capacity_check is not None:
            # SQLite can briefly hold both the new pages and their rollback journal.
            self.capacity_check(growth)
        with self.db:
            self.db.execute("INSERT INTO windows VALUES (?,?,?,?,?)",
                            (self.binding, task, index, hashlib.sha256(raw).hexdigest(), packed))

    def close(self):
        self.db.close()


def _segment_value(segment):
    fields = ("start", "end", "text", "avg_logprob", "no_speech_prob", "compression_ratio")
    value = {key: getattr(segment, key) for key in fields}
    value["words"] = [{key: getattr(word, key) for key in ("start", "end", "probability", "word")}
                      for word in segment.words or ()]
    return value


class CheckpointedTask:
    """Decode the same clock on resume and reuse previously validated model windows."""

    def __init__(self, task, store, key):
        self.task = task
        self.store = store
        self.key = key

    def windows(self, path, duration):
        for self.index, (start, audio) in enumerate(self.task.windows(path, duration)):
            self.start = start
            self.samples = len(audio)
            yield start, audio

    def transcribe(self, audio):
        cached = self.store.load(self.key, self.index)
        if cached is not None:
            base.require(cached["start"] == self.start and cached["samples"] == self.samples,
                         "asr_window_timebase")

            def restore():
                for value in cached["segments"]:
                    words = [SimpleNamespace(**word) for word in value["words"]]
                    yield SimpleNamespace(**{**value, "words": words})

            return restore(), SimpleNamespace(duration_after_vad=cached["vad"])

        iterator, info = self.task.transcribe(audio)

        def persist():
            segments = []
            for segment in iterator:
                segments.append(_segment_value(segment))
                yield segment
            self.store.save(self.key, self.index, {"start": self.start, "samples": self.samples,
                            "vad": info.duration_after_vad, "segments": segments})

        return persist(), info
