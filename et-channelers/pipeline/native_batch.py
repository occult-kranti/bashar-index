"""Two isolated stock-WPC native downloaders under one explicit batch lease.

Importing starts nothing. This does not resume old collectors or clear their
source refusals. See NATIVE_BATCH.md for the separate admission contract.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import hashlib
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

try:
    from . import drive_ingest as storage, native_batch_worker as worker
    from .native_batch_job import OwnedJob
    from .gpu_asr import encoded
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import drive_ingest as storage
    import native_batch_worker as worker
    from native_batch_job import OwnedJob
    from gpu_asr import encoded

MAX_SPOOL = 6_000_000_000
MAX_ASSET = 2_000_000_000
HEADROOM = 240_000_000
MANAGED = 16_000_000_000
FREE = 2_000_000_000
WINDOWS = os.name == 'nt'
SOURCE_FAILURES = {'source_403', 'source_429', 'bot_check', 'protection_failure', 'access_challenge'}
need, read, write, digest = worker.need, worker.read, worker.write, worker.digest


def load_plan(path):
    plan = read(path)
    items = plan.get('items', [])
    need(plan.get('schema_version') == 1 and 1 <= len(items) <= 20, 'plan_size')
    seen = set()
    for item in items:
        ident, channel = item.get('video_id', ''), item.get('channel_dir', '')
        row = item.get('queue_row', {})
        need(re.fullmatch(r'[A-Za-z0-9_-]{11}', ident) and ident not in seen and
             re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', channel) and
             item.get('video_url') == 'https://www.youtube.com/watch?v=' + ident and
             item.get('tab') in storage.SOURCE_FOLDERS and row.get('video_id') == ident and
             row.get('channel_dir') == channel and row.get('tab') == item['tab'] and
             hashlib.sha256(encoded(row)).hexdigest() == item.get('queue_row_sha256'), 'plan_target')
        duration = item.get('duration_seconds')
        need(duration is None or (type(duration) in (int, float) and math.isfinite(duration) and duration > 0), 'plan_duration')
        seen.add(ident)
    return digest(path), items


def source_error(result):
    value = result.get('diagnostics', {}).get('error_class')
    return value if value in SOURCE_FAILURES else None


def capacity_snapshot(root, spool, active_folders):
    """Count inactive files once; active child folders are charged full slots.

    Children cannot share a Python lock. Never combine their bytes measured at
    different instants with a sampled remaining reservation.
    """
    root, spool = Path(root).resolve(), Path(spool).resolve()
    active = {Path(p).resolve() for p in active_folders}
    need(all(p.is_relative_to(spool) and p != spool for p in active), 'capacity_scope')
    private_bytes = spool_bytes = 0
    for folder, directories, files in os.walk(root):
        base = Path(folder)
        for name in list(directories):
            path = base / name
            need(not storage.is_link(path), 'storage_link')
            if path in active: directories.remove(name)
        for name in files:
            path = base / name
            need(not storage.is_link(path), 'storage_link')
            try: size = path.stat().st_size
            except FileNotFoundError: continue
            private_bytes += size
            if path.is_relative_to(spool): spool_bytes += size
    return {'inactive_private_bytes': private_bytes, 'inactive_spool_bytes': spool_bytes}


class SlotBudget(storage.Budget):
    """Reuse reservation checks with the coordinator's partitioned snapshot."""
    inactive_bytes = 0

    def usage(self, reconcile=False):
        return self.inactive_bytes

    def _outstanding(self, omit=None):
        return sum(item['bytes'] for key, item in self.active.items() if key != omit)


def exception_diagnostic(error):
    allowed = {'PermissionError', 'FileNotFoundError', 'OSError', 'TimeoutError', 'RuntimeError', 'Held'}
    result = {'exception_class': type(error).__name__ if type(error).__name__ in allowed else 'OtherError'}
    for field in ('errno', 'winerror'):
        value = getattr(error, field, None)
        if type(value) is int and 0 <= value <= 65535: result[field] = value
    return result


def cleanup_profile(profile, folder, processes_gone, *, remove=shutil.rmtree, sleep=time.sleep):
    """Filesystem-only retries after the owned Job Object is empty."""
    result = {'attempts': 0, 'cleaned': not profile.exists(), 'failures': []}
    if not profile.exists(): return result
    need(processes_gone and profile.resolve().parent == folder.resolve() and not profile.is_symlink() and
         not getattr(profile, 'is_junction', lambda: False)(), 'cleanup_path')
    for delay in (0, .25, .75):
        if delay: sleep(delay)
        result['attempts'] += 1
        try:
            remove(profile)
            result['cleaned'] = not profile.exists()
            if result['cleaned']: return result
        except OSError as error:
            result['failures'].append(exception_diagnostic(error))
            if not profile.exists(): result['cleaned'] = True; return result
    result['retained_for_owner_cleanup'] = True
    return result


def check_pair_proofs(proofs, record):
    for key, expected in (('audio', record), ('metadata', record['metadata'])):
        storage.verify_remote(proofs[key], expected)
        need(bool(proofs[key].get('ID')), 'drive_identity_missing')
    need(proofs['audio']['ID'] != proofs['metadata']['ID'], 'drive_identity_duplicate')


def validate_record(record, item, folder, root, remote, plan_sha):
    ident = item['video_id']
    extension = Path(record.get('path', '')).suffix.lstrip('.')
    metadata = record.get('metadata') or {}
    need(record.get('video_id') == ident and record.get('channel_dir') == item['channel_dir'] and
         record.get('tab') == item['tab'] and record.get('native_batch_profile') == worker.PROFILE and
         record.get('native_batch_plan_sha256') == plan_sha and extension in {'m4a', 'webm'}, 'checkpoint_identity')
    expected_audio = folder / (ident + '.' + extension)
    expected_metadata = folder / (ident + '.info.json')
    need(record.get('path') == expected_audio.relative_to(root).as_posix() and
         metadata.get('path') == expected_metadata.relative_to(root).as_posix() and
         record.get('remote') == storage.remote_path(remote, item, extension) and
         metadata.get('remote') == storage.remote_path(remote, item, 'info.json'), 'checkpoint_paths')
    for proof in (record, metadata):
        need(type(proof.get('bytes')) is int and proof['bytes'] > 0 and
             isinstance(proof.get('md5'), str) and re.fullmatch(r'[0-9a-f]{32}', proof['md5']) and
             isinstance(proof.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', proof['sha256']), 'checkpoint_proof')


class NativeBatch:
    def __init__(self, settings_path, drive=None):
        self.settings_path = Path(settings_path).resolve()
        self.s = read(self.settings_path)
        self.root = Path(self.s['private_root']).resolve()
        self.plan_sha, self.items = load_plan(self.s['plan_path'])
        self.spool = self.root / 'stock_wpc_batch'
        self.jobs = self.spool / 'jobs' / self.plan_sha[:16]
        controls = worker.control_paths(self.root)
        self.lease_path = controls['lease_path']
        self.stop_path = controls['batch_stop_path']
        self.cooldown_path = controls['source_cooldown_path']
        self.state_path = self.root / 'sync/drive_ingest_manifest.jsonl'
        self.batch_journal = self.root / 'sync/stock_wpc_batch_manifest.jsonl'
        self.lock = threading.RLock(); self.source_stop = threading.Event()
        self.last_guard = self.last_inventory = 0; self.lease = None
        self.live_reservations = {}; self.budget = None
        self.external = self.others = 0
        need(type(self.s.get('workers')) is int and 1 <= self.s['workers'] <= 2, 'worker_count')
        need(type(self.s.get('max_asset_bytes')) is int and 0 < self.s['max_asset_bytes'] <= MAX_ASSET and
             type(self.s.get('spool_cap_bytes')) is int and 2 * (self.s['max_asset_bytes'] + HEADROOM) <= self.s['spool_cap_bytes'] <= MAX_SPOOL,
             'spool_admission')
        need(type(self.s.get('job_wall_seconds')) is int and 600 <= self.s['job_wall_seconds'] <= 7200, 'job_deadline')
        roots = [Path(p).resolve() for p in self.s['managed_roots']]
        need(len(roots) == len(set(roots)) == 6 and any('ms-playwright' in p.parts for p in roots) and
             all(not p.is_relative_to(q) for p in roots for q in roots if p != q), 'managed_roots')
        need(all(any(p.is_relative_to(q) for q in roots) for p in (self.root, Path(__file__).resolve(), Path(self.s['python_executable']).resolve())), 'managed_roots')
        self.roots = roots
        required = {Path(__file__).with_name(name).resolve() for name in (
            'native_batch_worker.py', 'native_batch_quality.py', 'native_batch_job.py', 'native_track_policy.py',
            'drive_ingest.py', 'media_metadata.py', 'native_audio_sink.py', 'native_metadata_snapshot.py')}
        supplied = {Path(pin['path']).resolve() for pin in self.s['code_pins']}
        need(required <= supplied, 'required_code_pins')
        need(Path(self.s['pipeline_directory']).resolve() == Path(__file__).parent.resolve(), 'pipeline_directory')
        self.drive = drive or storage.Rclone(self.s['rclone'], self.s.get('rclone_config'), self.root / 'sync/drive_ingest_cooldown.json')

    def guard(self, *, source=False, force=False):
        with self.lock:
            now = time.monotonic()
            if force or now - self.last_guard >= 1:
                lease = read(self.lease_path)
                need(lease.get('schema_version') == 1 and lease.get('state') == 'active' and lease.get('authorized') is True and
                     lease.get('profile') == worker.PROFILE and lease.get('owner') == self.s['owner'] and lease.get('lease_id') == self.s['lease_id'] and
                     lease.get('settings_sha256') == digest(self.settings_path) and lease.get('plan_sha256') == self.plan_sha == digest(self.s['plan_path']) and
                     lease.get('worker_sha256') == digest(worker.__file__) and lease.get('coordinator_sha256') == digest(__file__) and
                     lease.get('preserve_existing_cooldowns') is True and lease.get('max_workers') == self.s['workers'] and
                     lease.get('spool_cap_bytes') == self.s['spool_cap_bytes'] and lease.get('remote') == self.s['remote'], 'batch_lease')
                need(lease.get('source_scope_authorized') is True, 'source_scope_not_admitted')
                for pin in self.s['code_pins'] + self.s['preserved_controls']:
                    need(digest(pin['path']) == pin['sha256'], 'pinned_dependency_or_history_changed')
                need(self.s['preserved_controls'] and (self.root / 'sync/STOP_DRIVE_INGEST').exists(), 'old_collector_not_parked')
                resource = read(self.root / 'sync/analysis_resource_plan.json')
                need(resource.get('collector_dispatch_allowed') is False and 0 < resource.get('accounting_cap_bytes', 0) <= MANAGED, 'resource_policy')
                reservations = resource.get('reservations', [])
                own = [x for x in reservations if x.get('state') == 'active' and x.get('lease_id') == self.s['lease_id'] and x.get('owner') == self.s['owner']]
                need(len(own) == 1 and own[0].get('max_bytes', 0) >= self.s['spool_cap_bytes'], 'resource_reservation')
                self.others = sum(x['max_bytes'] for x in reservations if x.get('state') == 'active' and x.get('lease_id') != self.s['lease_id'])
                self.cap = resource['accounting_cap_bytes']; self.lease = lease; self.last_guard = now
            need(type(self.lease.get('expires_at_epoch')) in (int, float) and time.time() < self.lease['expires_at_epoch'], 'lease_expired')
            if source:
                need(not self.source_stop.is_set() and not self.stop_path.exists(), 'batch_source_stopped')
                if self.cooldown_path.exists():
                    need(read(self.cooldown_path).get('retry_not_before_epoch', 0) <= time.time(), 'batch_source_cooldown')
            if force or now - self.last_inventory >= 12:
                self.external = sum(storage.tree_bytes(p) for p in self.roots if p != self.root)
                self.last_inventory = now
            limit = self.cap - self.external - self.others
            need(limit > storage.JOURNAL_RESERVE and shutil.disk_usage(self.root).free >= FREE, 'managed_storage')
            if self.budget:
                self.budget.cap = limit
                self.capacity = capacity_snapshot(self.root, self.spool,
                    [reservation['folder'] for reservation in self.live_reservations.values()])
                self.budget.inactive_bytes = self.capacity['inactive_private_bytes']
                self.capacity.update(active_reserved_bytes=self.budget._outstanding(),
                    private_limit_bytes=limit - storage.JOURNAL_RESERVE, spool_limit_bytes=self.s['spool_cap_bytes'])
                for projected, ceiling, code in (
                    (self.budget.usage() + self.budget._outstanding(), limit - storage.JOURNAL_RESERVE, 'managed_storage'),
                    (self.capacity['inactive_spool_bytes'] + self.budget._outstanding(), self.s['spool_cap_bytes'], 'spool_storage')):
                    if projected > ceiling:
                        error = worker.Held(code); error.capacity_evidence = dict(self.capacity, projected_bytes=projected)
                        raise error
            return limit

    def refuse(self, result):
        error = source_error(result)
        if not error: return
        with self.lock:
            if self.source_stop.is_set(): return
            self.source_stop.set()
            write(self.cooldown_path, {'schema_version': 1, 'profile': worker.PROFILE,
                'plan_sha256': self.plan_sha, 'error_class': error, 'retry_not_before_epoch': time.time() + 86400,
                'source_scope': 'stock_wpc_native_batch', 'requested_video_id': result.get('video_id'),
                'refusal': result.get('diagnostics', {}).get('source_refusal'),
                'requested_id_does_not_prove_which_page_refused': True})
            self.stop_path.write_bytes(b'native batch source refusal; no automatic retry\n')

    def execute_child(self, item):
        ident = item['video_id']; folder = self.jobs / ident
        while True:
            with self.lock:
                self.guard(source=True)
                need(not folder.exists(), 'attempt_already_exists')
                maximum = item.get('max_audio_bytes', self.s['max_asset_bytes'])
                need(type(maximum) is int and 0 < maximum <= self.s['max_asset_bytes'], 'asset_deferred')
                fits = self.capacity['inactive_spool_bytes'] + self.budget._outstanding() + maximum + HEADROOM <= self.s['spool_cap_bytes']
                if fits:
                    self.budget.reserve_item(ident, folder / 'native-audio.part', maximum, HEADROOM)
                    self.live_reservations[ident] = {'folder': folder, 'bytes': maximum + HEADROOM}
                    folder.mkdir(parents=True)
                    config = {'settings_path': str(self.settings_path), 'video_id': ident, 'item': item, 'run_root': str(folder),
                        'lease_path': str(self.lease_path), 'batch_stop_path': str(self.stop_path)}
                    write(folder / 'config.json', config)
                    write(folder / 'attempt.json', {'schema_version': 1, 'video_id': ident, 'attempts_spent': 1,
                        'plan_sha256': self.plan_sha, 'lease_id': self.s['lease_id'], 'worker_sha256': digest(worker.__file__),
                        'created_at': storage.utc_now(), 'source_history_preserved': True})
                    break
                need(bool(self.live_reservations), 'spool_storage_deferred')
            time.sleep(.5)  # wait for an existing owned worker/upload; no source attempt spent
        job = None; process = None; attached = False; closed = False; error = None
        first_exception = None; first_capacity_failure = None; process_cleanup_errors = []; profile_cleanup = None
        started = time.monotonic(); peak_profile = 0
        try:
            need(WINDOWS, 'windows_child_required')
            job = OwnedJob()
            process = subprocess.Popen([self.s['python_executable'], '-I', str(Path(worker.__file__).resolve()), '--child',
                '--config', str(folder / 'config.json'), '--admission', str(self.lease_path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            job.attach(process); attached = True
            (folder / 'GO').write_bytes(b'owned_job_bound\n')
            while process.poll() is None:
                self.guard(source=True)
                elapsed = time.monotonic() - started
                need(elapsed < self.s['job_wall_seconds'], 'job_deadline')
                status = read(folder / 'progress.json') if (folder / 'progress.json').exists() else {}
                if status.get('phase', 'bootstrap') == 'bootstrap': need(elapsed < 90, 'bootstrap_deadline')
                if status.get('error_class') in SOURCE_FAILURES:
                    self.refuse({'video_id': ident, 'diagnostics': status}); raise worker.Held('source_refusal')
                profile_size = storage.tree_bytes(folder / 'profile-temp'); peak_profile = max(peak_profile, profile_size)
                need(profile_size <= 150_000_000 and storage.tree_bytes(folder) <= maximum + HEADROOM, 'observed_child_spool')
                time.sleep(.5)
        except BaseException as exc:
            error = getattr(exc, 'code', getattr(exc, 'kind', 'native_child_failed'))
            first_exception = exception_diagnostic(exc)
            first_capacity_failure = getattr(exc, 'capacity_evidence', None)
        finally:
            if process and not attached and process.poll() is None: process.kill()
            if job:
                try: closed = job.stop_and_verify()
                except Exception as exc:
                    process_cleanup_errors.append(exception_diagnostic(exc)); error = error or 'owned_cleanup_failed'
                finally: job.close()
            if process:
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired as exc:
                    process_cleanup_errors.append(exception_diagnostic(exc)); process.kill(); process.wait(timeout=5)
                    error = error or 'child_cleanup_failed'
            if not closed or process_cleanup_errors:
                self.source_stop.set()
                self.stop_path.write_bytes(b'owned child cleanup requires review\n')
            if closed:
                profile = folder / 'profile-temp'
                if profile.exists():
                    try: profile_cleanup = cleanup_profile(profile, folder, closed)
                    except Exception as exc:
                        profile_cleanup = {'cleaned': False, 'attempts': 0, 'failures': [exception_diagnostic(exc)]}
                        error = error or 'cleanup_path'; self.source_stop.set()
                        self.stop_path.write_bytes(b'owned profile path requires review\n')
            write(folder / 'parent-audit.json', {'schema_version': 1, 'video_id': ident, 'owned_processes_gone': closed,
                'profile_cleaned': not (folder / 'profile-temp').exists(), 'observed_profile_peak_bytes': peak_profile,
                'browser_disk_limit_is_observed_stop_target': True, 'error_class': error,
                'first_parent_exception': first_exception, 'process_cleanup_errors': process_cleanup_errors,
                'capacity_failure': first_capacity_failure,
                'profile_cleanup': profile_cleanup,
                'child_exit': process.returncode if process else None,
                'elapsed_seconds': time.monotonic() - started})
            with self.lock:
                self.budget.release(ident); self.live_reservations.pop(ident, None)
        result = read(folder / 'result.json') if (folder / 'result.json').exists() else {'status': 'held', 'video_id': ident, 'diagnostics': {'error_class': error or 'child_result_missing'}}
        self.refuse(result)
        if error or not closed: result = dict(result, status='held', parent_error_class=error or 'cleanup_unproven')
        return result

    def publish(self, item, result):
        self.guard()
        ident = item['video_id']; folder = self.jobs / ident
        record_path = folder / 'canonical-record.json'
        if record_path.exists():
            record = read(record_path)
            validate_record(record, item, folder, self.root, self.s['remote'], self.plan_sha)
            trusted = None  # resumed source is hashed once by shared verifier
        else:
            need(result.get('status') == 'local_complete' and result.get('video_id') == ident, 'local_result')
            proof = result['audio']; source = folder / proof['filename']
            need(source.parent == folder and source.suffix in {'.m4a', '.webm'} and
                 storage.fingerprint(source) == tuple(proof['fingerprint']) and source.stat().st_size == proof['bytes'], 'local_audio_changed')
            audio = folder / (ident + source.suffix)
            need(not audio.exists(), 'local_name_conflict')
            metadata_source = folder / result['metadata']['filename']
            need(metadata_source.parent == folder and digest(metadata_source) == result['metadata']['sha256'], 'local_metadata_changed')
            metadata_value = read(metadata_source)
            remote = storage.remote_path(self.s['remote'], item, audio.suffix.lstrip('.'))
            metadata_value['queue'] = item['queue_row']
            metadata_value['archive_audio'] = {k: proof[k] for k in ('bytes', 'md5', 'sha256')}
            metadata_value['archive_audio'].update(video_id=ident, remote=remote, file_name=audio.name, encoding='native audio; no re-encode')
            metadata_value['native_batch_provenance'] = {'profile': worker.PROFILE, 'plan_sha256': self.plan_sha,
                'worker_sha256': digest(worker.__file__), 'coordinator_sha256': digest(__file__), 'lease_id': self.s['lease_id'],
                'quality_state': result['probe']['quality_state'], 'human_reviewed': False}
            metadata = folder / (ident + '.info.json')
            if metadata.exists(): need(read(metadata) == metadata_value, 'local_metadata_conflict')
            else: write(metadata, metadata_value)
            meta_proof = storage.hash_file(metadata)
            record = dict(video_id=ident, channel_dir=item['channel_dir'], tab=item['tab'], status='prepared',
                path=audio.relative_to(self.root).as_posix(), remote=remote, **{k: proof[k] for k in ('bytes', 'md5', 'sha256')},
                metadata={**meta_proof, 'path': metadata.relative_to(self.root).as_posix(), 'remote': remote.rpartition('/')[0] + '/' + metadata.name},
                native_batch_profile=worker.PROFILE, native_batch_plan_sha256=self.plan_sha, native_batch_lease_id=self.s['lease_id'],
                quality_state=result['probe']['quality_state'], native_acquisition_quality=result['probe'])
            validate_record(record, item, folder, self.root, self.s['remote'], self.plan_sha)
            write(record_path, record)  # planned rename survives a crash
            os.replace(source, audio)
            trusted = {'audio': storage.fingerprint(audio), 'metadata': storage.fingerprint(metadata)}
            storage.journal(self.state_path, record)
        audio, metadata = (storage.local_path(self.root, p['path']) for p in (record, record['metadata']))
        if not audio.exists():
            original = folder / ('native-audio' + audio.suffix)
            if original.exists():
                storage.validate_local(original, record)
                os.replace(original, audio)
                trusted = dict(trusted or {}, audio=storage.fingerprint(audio))
        prior = storage.load_state(self.state_path).get(ident, {})
        prior_verified = prior.get('status') in {'verified', 'deleted'} and all(
            prior.get(key) == record.get(key) for key in ('bytes', 'md5', 'sha256', 'remote')) and all(
            prior.get('metadata', {}).get(key) == record['metadata'].get(key) for key in ('bytes', 'md5', 'sha256', 'remote'))
        known = {}
        for key, path, expected in (('audio', audio, record), ('metadata', metadata, record['metadata'])):
            if path.exists(): known[key] = storage.validate_local(path, expected, (trusted or {}).get(key))
            else: need(prior_verified, 'local_missing_without_drive_proof')
        if not prior_verified:
            def preserve_metadata(observed_audio):
                storage.verify_remote(observed_audio, record)
                need(bool(observed_audio.get('ID')), 'drive_identity_missing')
                try: observed_metadata = self.drive.stat(record['metadata']['remote'])
                except storage.IngestError as missing:
                    if missing.kind != 'drive_not_found': raise
                    observed_metadata = None
                try: from .native_metadata_snapshot import preserve_conflicting_metadata
                except ImportError: from native_metadata_snapshot import preserve_conflicting_metadata
                lineage = preserve_conflicting_metadata(self.root, record, self.drive,
                    observed_audio=observed_audio, observed_metadata=observed_metadata, trusted=known)
                if lineage:
                    record['metadata_lineage'] = lineage
                    write(record_path, record)
                    storage.journal(self.state_path, record)

            pending_lineage = storage.load_state(self.root / 'sync/native_metadata_lineage_manifest.jsonl').get(ident, {})
            if (not record.get('metadata_lineage') and
                    pending_lineage.get('kind') == 'native_metadata_snapshot_preservation' and
                    pending_lineage.get('original', {}).get('remote') == record['metadata']['remote'] and
                    pending_lineage.get('new_canonical_expected', {}).get('sha256') == record['metadata']['sha256']):
                # A lost move ACK can leave canonical metadata absent. Read back
                # the exact preserved object before allowing its replacement.
                preserve_metadata(self.drive.stat(record['remote']))
            try:
                self.drive.copy_pair(audio, metadata, record['remote'], record['metadata']['remote'])
            except storage.IngestError as error:
                if error.kind != 'drive_conflict': raise
                # Preserve only conflicting canonical metadata, after the exact
                # new audio is verified remotely. Audio is never replaced.
                try: observed_audio = self.drive.stat(record['remote'])
                except storage.IngestError as missing:
                    if missing.kind != 'drive_not_found': raise
                    self.drive.copy(audio, record['remote'])  # immutable
                    observed_audio = self.drive.stat(record['remote'])
                preserve_metadata(observed_audio)
                self.drive.copy_pair(audio, metadata, record['remote'], record['metadata']['remote'])
        relative = [storage.remote_relative(self.s['remote'], p['remote']) for p in (record, record['metadata'])]
        with storage.batch_manifest(self.root, relative) as manifest:
            remote = self.drive.stat_batch(self.s['remote'], relative, manifest)
        proofs = {'audio': remote[relative[0]], 'metadata': remote[relative[1]]}
        check_pair_proofs(proofs, record)
        done = storage.verify_and_delete(self.root, record, self.drive, self.state_path, require_metadata=True,
            allow_missing=prior_verified, trusted=known, remote_proofs=proofs)
        need(storage.receipt_complete(done, item, self.s['remote']), 'canonical_receipt_incomplete')
        write(record_path, done)
        storage.journal(self.batch_journal, {'schema_version': 1, 'profile': worker.PROFILE, 'video_id': ident,
            'status': 'verified', 'plan_sha256': self.plan_sha, 'quality_state': done['quality_state'],
            'audio_drive_id': done['drive_id'], 'metadata_drive_id': done['metadata']['drive_id']})
        return done

    def run(self):
        self.spool.mkdir(exist_ok=True)
        counts = {'verified': 0, 'skipped': 0, 'held': 0, 'pending': 0}
        with storage.exclusive_lock(self.root):
            self.jobs.mkdir(parents=True, exist_ok=True)
            limit = self.guard(force=True)
            self.budget = SlotBudget(self.root, limit, self.s['max_asset_bytes'], FREE, cached=False)
            previous = storage.load_state(self.state_path)
            pending = []
            for item in self.items:
                if storage.receipt_complete(previous.get(item['video_id'], {}), item, self.s['remote']):
                    counts['skipped'] += 1; continue
                folder = self.jobs / item['video_id']
                if folder.exists():
                    result = read(folder / 'result.json') if (folder / 'result.json').exists() else {}
                    if result.get('status') == 'local_complete' or (folder / 'canonical-record.json').exists():
                        try: self.publish(item, result); counts['verified'] += 1
                        except Exception: counts['held'] += 1
                    else: counts['held'] += 1
                else: pending.append(item)
            with ThreadPoolExecutor(max_workers=self.s['workers']) as pool:
                active = {}
                while active or pending:
                    while pending and len(active) < self.s['workers'] and not self.source_stop.is_set():
                        try: self.guard(source=True)
                        except Exception: counts['pending'] += len(pending); pending.clear(); break
                        item = pending.pop(0); active[pool.submit(self.execute_child, item)] = item
                    if not active:
                        counts['pending'] += len(pending); break
                    complete, _ = wait(active, return_when=FIRST_COMPLETED)
                    for future in complete:
                        item = active.pop(future)
                        try:
                            result = future.result()
                            if result.get('status') == 'local_complete': self.publish(item, result); counts['verified'] += 1
                            else: counts['held'] += 1
                        except Exception as exc:
                            counts['held'] += 1
                            kind = getattr(exc, 'kind', getattr(exc, 'code', 'native_batch_failed'))
                            storage.journal(self.batch_journal, {'schema_version': 1, 'profile': worker.PROFILE, 'video_id': item['video_id'],
                                'status': 'held', 'error_class': kind, 'plan_sha256': self.plan_sha})
                            if kind.startswith('drive_'): self.source_stop.set()
            write(self.jobs / 'summary.json', {'schema_version': 1, 'profile': worker.PROFILE, 'plan_sha256': self.plan_sha, **counts})
        return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', required=True); parser.add_argument('--execute', action='store_true')
    args = parser.parse_args(argv); need(args.execute, 'explicit_execution_required')
    result = NativeBatch(args.settings).run(); print(json.dumps(result))
    return 0 if not result['held'] and not result['pending'] else 3


if __name__ == '__main__':
    try: sys.exit(main())
    except worker.Held as error:
        print(json.dumps({'status': 'held', 'error_class': error.code})); sys.exit(3)
