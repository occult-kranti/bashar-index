"""Bounded, sanitized crash evidence. Never a worker result or source authority."""
from __future__ import annotations
import builtins
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import threading
import time

PREFIX = b'NATIVE_FATAL_V1 '
CAP = 32768
LINE_CAP = 8192
CLASSES = {name for name, value in vars(builtins).items()
           if isinstance(value, type) and issubclass(value, BaseException)} | {
    'Held', 'QualityHold', 'IngestError', 'DownloadError', 'ExtractorError',
    'UnavailableVideoError', 'HTTPError', 'MaxDownloadsReached'}
STAGES = {'create', 'write_fsync', 'replace', 'encode', 'outer_worker', 'fatal_persist'}


def exception_rows(error):
    rows = []; seen = set()
    while error is not None and id(error) not in seen and len(rows) < 8:
        seen.add(id(error)); name = type(error).__name__
        row = {'exception_class': name if name in CLASSES else 'OtherException'}
        for key in ('errno', 'winerror'):
            value = getattr(error, key, None)
            if type(value) is int and 0 <= value <= 65535: row[key] = value
        if isinstance(error, SystemExit) and type(error.code) is int and 0 <= error.code <= 255:
            row['exit_code'] = error.code
        control = getattr(error, 'control_diagnostic', None)
        if isinstance(control, dict):
            row['control'] = {key: value for key, value in control.items()
                              if (key == 'stage' and value in STAGES) or
                              (key == 'retry_attempts' and type(value) is int and 0 <= value <= 10) or
                              (key == 'target' and value in {'result.json', 'progress.json', 'other_control'})}
        rows.append(row); error = error.__cause__ or error.__context__
    return rows


def sanitized_event(value):
    """Accept only fields that this pinned worker itself emits; discard all text."""
    if not isinstance(value, dict) or value.get('kind') != 'native_worker_fatal': return None
    rows = value.get('exceptions')
    if not isinstance(rows, list): return None
    clean = []
    for row in rows[:8]:
        if not isinstance(row, dict): continue
        item = {'exception_class': row.get('exception_class') if row.get('exception_class') in CLASSES else 'OtherException'}
        for key in ('errno', 'winerror'):
            number = row.get(key)
            if type(number) is int and 0 <= number <= 65535: item[key] = number
        number = row.get('exit_code')
        if row.get('exception_class') == 'SystemExit' and type(number) is int and 0 <= number <= 255:
            item['exit_code'] = number
        control = row.get('control')
        if isinstance(control, dict):
            item['control'] = {key: val for key, val in control.items()
                               if (key == 'stage' and val in STAGES) or
                               (key == 'retry_attempts' and type(val) is int and 0 <= val <= 10) or
                               (key == 'target' and val in {'result.json', 'progress.json', 'other_control'})}
        clean.append(item)
    return {'schema_version': 1, 'kind': 'native_worker_fatal', 'exceptions': clean,
            'source_access': 'unknown', 'worker_result_authority': False,
            'fatal_file_written': value.get('fatal_file_written') is True}


def report_fatal(error, argv=None):
    """Independent exclusive fatal file plus stderr, even when result replace fails."""
    event = {'kind': 'native_worker_fatal', 'exceptions': exception_rows(error), 'fatal_file_written': False}
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        index = args.index('--config'); config_path = Path(args[index + 1]).resolve()
        config = json.loads(config_path.read_bytes()); folder = Path(config['run_root']).resolve()
        if folder != config_path.parent or config_path.name != 'config.json' or not re.fullmatch(r'[A-Za-z0-9_-]{11}', folder.name):
            raise ValueError('scope')
        descriptor = sanitized_event(event)
        descriptor.pop('fatal_file_written', None)
        descriptor['fatal_file_write_attempted'] = True
        raw = json.dumps(descriptor, sort_keys=True, separators=(',', ':')).encode() + b'\n'
        if len(raw) > LINE_CAP: raise ValueError('diagnostic size')
        with (folder / 'worker-fatal.json').open('xb') as output:
            output.write(raw); output.flush(); os.fsync(output.fileno())
        event['fatal_file_written'] = True
    except BaseException as persist_error:
        event['exceptions'] += exception_rows(persist_error)[:1]
    raw = PREFIX + json.dumps(sanitized_event(event), sort_keys=True, separators=(',', ':')).encode() + b'\n'
    try: os.write(2, raw[:LINE_CAP])
    except OSError: pass  # Parent still retains missing-final/exit/owned-closure evidence.
    return sanitized_event(event)


class StderrCapture:
    """Drain every byte, retain only whitelisted records, fixed disk/memory bounds."""
    def __init__(self, folder):
        self.folder = Path(folder); self.path = self.folder / 'child-stderr.jsonl'
        self.output = self.path.open('xb'); self.written = 0; self.seen = 0
        self.events = 0; self.discarded = 0; self.oversized_lines = 0; self.failure = None; self.thread = None

    def _commit(self, value, final=False):
        raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode() + b'\n'
        if self.written + len(raw) > (CAP if final else CAP - 1024): self.discarded += len(raw); return
        self.output.write(raw); self.output.flush(); os.fsync(self.output.fileno()); self.written += len(raw)

    def consume(self, stream):
        pending = bytearray(); oversized = False
        try:
            while True:
                chunk = stream.read(1024)
                if not chunk: break
                self.seen += len(chunk)
                for byte in chunk:
                    if byte == 10:
                        if oversized: self.oversized_lines += 1
                        if not oversized and pending.startswith(PREFIX):
                            try: event = sanitized_event(json.loads(bytes(pending[len(PREFIX):])))
                            except (ValueError, UnicodeError): event = None
                            if event is not None: self._commit(event); self.events += 1
                        pending.clear(); oversized = False
                    elif len(pending) < LINE_CAP and not oversized: pending.append(byte)
                    else: pending.clear(); oversized = True
            if oversized: self.oversized_lines += 1
            # Partial/unstructured lines are intentionally never retained.
        except BaseException as error: self.failure = exception_rows(error)
        finally:
            try: stream.close()
            except OSError: pass

    def start(self, stream):
        self.thread = threading.Thread(target=self.consume, args=(stream,), daemon=True)
        self.thread.start()

    def finish(self):
        if self.thread is not None:
            self.thread.join(timeout=5)
            if self.thread.is_alive(): raise RuntimeError('diagnostic_pipe_not_closed')
        try:
            summary = {'schema_version': 1, 'kind': 'sanitized_stderr_capture', 'raw_bytes_observed': self.seen,
                       'structured_events': self.events, 'raw_text_retained': False, 'disk_cap_bytes': CAP,
                       'source_access': 'unknown', 'worker_result_authority': False,
                       'capture_failure': self.failure, 'discarded_structured_bytes': self.discarded}
            summary.update(retention_truncated=self.discarded > 0, oversized_lines_discarded=self.oversized_lines)
            self._commit(summary, final=True)
            if self.failure is not None: raise RuntimeError('diagnostic_capture_failed')
            summary['stderr_file'] = {'filename': self.path.name, 'bytes': self.path.stat().st_size,
                                      'sha256': hashlib.sha256(self.path.read_bytes()).hexdigest()}
            return summary
        finally: self.output.close()
