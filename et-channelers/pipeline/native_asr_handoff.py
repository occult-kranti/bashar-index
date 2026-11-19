"""Leased native-audio hardlinks; no network, GPU, or collector-journal writes.

Integration (only after the collector frame is re-admitted with this pin):
  retain_before_cleanup(settings, record, remote_proofs, trusted=known)
  finalize_after_cleanup(settings, handoff_id, canonical_deleted_record)

The first call must succeed before deleting the collector's source names. A
``handoff_capacity`` error means retain those names and pause new dispatch.
The second call publishes readiness last. Only the separate ASR queue lock is
used, so a consumer can drain while the collector owns its lifetime lock.
"""
from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import zipfile

try:
    from . import drive_ingest as storage, gpu_asr_queue as queue
    from .common import ensure_outside_git, utc_now
except ImportError:
    import drive_ingest as storage
    import gpu_asr_queue as queue
    from common import ensure_outside_git, utc_now

PROFILE = 'native-asr-handoff-v1'
MAX_BYTES = 1_000_000_000
MAX_PAIRS = 3
CONTROL_RESERVE = 1_000_000
MAX_DOCUMENT = 20_000_000
HERE = Path(__file__).resolve().parent


def need(condition, kind):
    if not condition:
        raise storage.IngestError(kind, kind.replace('_', ' '))


def read(path):
    need(path.stat().st_size <= MAX_DOCUMENT, 'handoff_document_size')
    return json.loads(path.read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(queue.encoded(value)).hexdigest()


@dataclass(frozen=True)
class Settings:
    root: Path
    owner: str
    lease_id: str
    remote: str
    cap_bytes: int = MAX_BYTES
    max_pairs: int = MAX_PAIRS
    retain_policy: str = 'explicit_original_english_v1'

    def __post_init__(self):
        object.__setattr__(self, 'root', ensure_outside_git(Path(self.root).resolve()))
        need(type(self.cap_bytes) is int and CONTROL_RESERVE < self.cap_bytes <= MAX_BYTES and
             type(self.max_pairs) is int and 1 <= self.max_pairs <= MAX_PAIRS, 'handoff_limits')
        need(all(isinstance(v, str) and v for v in (self.owner, self.lease_id, self.remote)), 'handoff_identity')
        need(self.retain_policy == 'explicit_original_english_v1', 'handoff_retain_policy')

    def path(self, relative):
        return storage.local_path(self.root, relative)


def admission_lease(s):
    lease = read(s.path('sync/native_asr_handoff_lease.json'))
    need(lease.get('schema_version') == 1 and lease.get('profile') == PROFILE and lease.get('state') == 'active' and
         lease.get('owner') == s.owner and lease.get('lease_id') == s.lease_id and
         lease.get('remote') == s.remote and lease.get('cap_bytes') == s.cap_bytes and
         lease.get('max_pairs') == s.max_pairs and lease.get('retain_policy') == s.retain_policy, 'handoff_lease')
    expiry = lease.get('expires_at_epoch')
    need(type(expiry) in (int, float) and math.isfinite(expiry) and expiry > dt.datetime.now(dt.timezone.utc).timestamp(),
         'handoff_lease_expired')
    plan = read(s.path('sync/analysis_resource_plan.json'))
    active = [r for r in plan.get('reservations', []) if r.get('state') == 'active' and
              r.get('lease_id') == s.lease_id and r.get('owner') == s.owner]
    need(plan.get('collector_dispatch_allowed') is False and len(active) == 1 and
         type(active[0].get('max_bytes')) is int and active[0]['max_bytes'] >= s.cap_bytes and
         type(plan.get('accounting_cap_bytes')) is int and 0 < plan['accounting_cap_bytes'] <= storage.MAX_LOCAL_BYTES,
         'handoff_reservation')
    need(shutil.disk_usage(s.root).free >= storage.MIN_FREE_BYTES, 'handoff_disk_reserve')
    # The owner still performs the six-root/global-growth admission. This helper
    # only enforces its nested staging allowance, never expands that allowance.
    return dt.datetime.fromtimestamp(expiry, dt.timezone.utc).isoformat()


def state_path(s, key):
    need(re.fullmatch(r'handoff-[a-f0-9]{32}', key) is not None, 'handoff_key')
    return s.path(f'asr/jobs/native-handoff/{key}/handoff.json')


def save(s, state):
    queue.atomic(state_path(s, state['handoff_id']), state)
    storage.journal(s.path('sync/native_asr_handoff_manifest.jsonl'), state)


def source_proofs(s, record, observed):
    ident = record.get('video_id', '')
    need(re.fullmatch(r'[A-Za-z0-9_-]{11}', ident) is not None, 'handoff_video_id')
    need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', record.get('channel_dir', '')) is not None and
         record.get('tab') in storage.SOURCE_FOLDERS, 'handoff_channel_scope')
    objects = {}
    for kind, expected in (('audio', record), ('metadata', record.get('metadata', {}))):
        storage.verify_remote(observed.get(kind), expected)
        proof = dict(queue.proof(expected), drive_id=observed[kind].get('ID'))
        need(queue.valid_proof(proof), 'handoff_drive_proof')
        objects[kind] = proof
    need(objects['audio']['drive_id'] != objects['metadata']['drive_id'], 'handoff_drive_identity')
    suffix = Path(record['path']).suffix.lstrip('.')
    need(storage.valid_recorded_remote(s.remote, record, suffix, objects['audio']['remote']) and
         objects['metadata']['remote'] == objects['audio']['remote'].rpartition('/')[0] + f'/{ident}.info.json',
         'handoff_remote_scope')
    return objects


def caption_decision(s, record, paths):
    """Only a cached, hashed, usable native ZIP can suppress ASR. No pulls."""
    cap = storage.load_state(s.path('sync/drive_caption_manifest.jsonl')).get(record['video_id'], {})
    tracks = [t for t in cap.get('tracks', []) if storage.caption_track_verified(t, record, s.remote)]
    decision = {'state': 'caption_inventory_unknown', 'receipt_sha256': digest(cap), 'speech_coverage_validated': False}
    if not tracks:
        decision['state'] = 'no_usable_verified_english_caption'
        return decision
    decision['state'] = 'caption_coverage_review'
    if cap.get('video_id') != record['video_id'] or not storage.caption_receipt_complete(cap, record, s.remote):
        return decision
    for track in tracks:
        path_value = paths.get(track['track_id'])
        if not path_value or not queue.english(track.get('language')) or track.get('machine_translated') is not False:
            continue
        path = s.path(path_value)
        expected = track['bundle']
        need(path.stat().st_size <= MAX_DOCUMENT and storage.hash_file(path) ==
             {k: expected[k] for k in ('bytes', 'md5', 'sha256')}, 'handoff_caption_hash')
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            need(len(set(names)) == len(names) and sum(x.file_size for x in archive.infolist()) <= MAX_DOCUMENT,
                 'handoff_caption_zip')
            detail = json.loads(archive.read('provenance.json'))
            segments = json.loads(archive.read('segments.json')).get('segments', [])
            text = archive.read('transcript.txt').decode('utf-8')
        if (detail.get('video_id') == record['video_id'] and detail.get('provider') == 'youtube' and
                detail.get('track_id') == track['track_id'] and detail.get('policy') == storage.CAPTION_POLICY and
                detail.get('machine_translated') is False and queue.english(detail.get('language')) and
                text.strip() and any(isinstance(x.get('text'), str) and x['text'].strip() and
                    type(x.get('start')) in (int, float) and type(x.get('end')) in (int, float) and
                    math.isfinite(x['start']) and math.isfinite(x['end']) and 0 <= x['start'] < x['end'] for x in segments)):
            return dict(decision, state='usable_english_caption', track_id=track['track_id'],
                        bundle=queue.proof(expected), source_binding='same_provider_video_id_not_audio_hash')
    return decision


def stable_file(path):
    # Creating/removing hardlinks changes ctime on Unix. Track byte-relevant
    # identity separately; the existing worker still hashes its admitted input.
    stat = path.stat()
    return [stat.st_size, stat.st_mtime_ns, stat.st_ino, stat.st_dev]


def language_route(metadata):
    selection = metadata.get('native_selection', {})
    original = selection.get('original_audio_evidence', {})
    primary, fallback = metadata.get('languages', {}).get('audio'), metadata.get('metadata', {}).get('language')
    declared = primary or fallback
    english = (original.get('original_explicitly_verified') is True and original.get('origin_inferred') is False and
               original.get('original_label_present') is True and original.get('language_preference') == 10 and
               original.get('source_language') == original.get('language') == declared and queue.english(declared) and
               (not primary or not fallback or primary == fallback))
    return {'declared_language': declared, 'explicit_original_english': bool(english),
            'original_audio_evidence': original, 'metadata_content_flags': metadata.get('metadata_content_flags', {}),
            'duration_seconds': selection.get('format', {}).get('duration') or metadata.get('metadata', {}).get('duration')}


def check_links(s, state, *, missing_ok=False):
    for kind, item in state['links'].items():
        name = state['sources'][kind]['remote'].rsplit('/', 1)[-1]
        expected = f"asr/input/{state['video_id']}/{state['sources']['audio']['sha256']}/{name}"
        need(item['path'] == expected, 'handoff_link_scope')
        path = s.path(item['path'])
        if not path.exists():
            need(missing_ok, 'handoff_input_missing')
            continue
        need(stable_file(path) == item['fingerprint'], 'handoff_input_changed')
        if item.get('finalized_fingerprint'):
            need(list(storage.fingerprint(path)) == item['finalized_fingerprint'], 'handoff_input_changed')


def capacity(s, additional):
    total = pairs = 0
    directory = s.path('asr/jobs/native-handoff')
    for file in directory.glob('*/handoff.json'):
        state = read(s.path(file.relative_to(s.root)))
        if state.get('status') != 'released' and state.get('links'):
            pairs += 1
            total += sum(p['bytes'] for p in state['sources'].values())
    need(pairs < s.max_pairs and total + additional + CONTROL_RESERVE <= s.cap_bytes, 'handoff_capacity')


def retain_before_cleanup(s, record, remote_proofs, *, trusted=None, caption_bundle_paths=None):
    """Raise on full staging; caller MUST retain its original names on any error."""
    with queue.queue_lock(s.root):
        expires = admission_lease(s)
        proofs = source_proofs(s, record, remote_proofs)
        key = 'handoff-' + digest({'video_id': record['video_id'], 'sources': proofs})[:32]
        file = state_path(s, key)
        if file.exists():
            state = read(file)
            need(state['sources'] == proofs and state['allocation_lease_id'] == s.lease_id, 'handoff_conflict')
            if state['status'] != 'link_intent':
                if state['status'] != 'released': check_links(s, state)
                return state
        else:
            paths = {'audio': s.path(record['path']), 'metadata': s.path(record['metadata']['path'])}
            for kind, path in paths.items():
                storage.validate_local(path, proofs[kind], (trusted or {}).get(kind))
            metadata = read(paths['metadata'])
            need(metadata.get('source', {}).get('video_id') == record['video_id'], 'handoff_metadata_identity')
            bound_audio = metadata.get('archive_audio', {})
            need(bound_audio.get('video_id') == record['video_id'] and
                 all(bound_audio.get(k) == proofs['audio'][k] for k in ('bytes', 'md5', 'sha256')),
                 'handoff_metadata_audio_binding')
            caption = caption_decision(s, record, caption_bundle_paths or {})
            route = language_route(metadata)
            links = {}
            if route['explicit_original_english'] and caption['state'] != 'usable_english_caption':
                capacity(s, sum(p['bytes'] for p in proofs.values()))
                for kind, source in paths.items():
                    name = proofs[kind]['remote'].rsplit('/', 1)[-1]
                    need(name == source.name, 'handoff_source_filename')
                    target = s.path(f"asr/input/{record['video_id']}/{proofs['audio']['sha256']}/{name}")
                    need(not target.exists(), 'handoff_path_conflict')
                    links[kind] = {'path': target.relative_to(s.root).as_posix(),
                                   'source_path': source.relative_to(s.root).as_posix(), 'fingerprint': stable_file(source)}
            state = {'schema_version': 1, 'profile': PROFILE, 'handoff_id': key, 'status': 'link_intent',
                'video_id': record['video_id'], 'channel_dir': record['channel_dir'], 'tab': record.get('tab', ''),
                'allocation_lease_id': s.lease_id, 'owner': s.owner, 'expires_at': expires,
                'sources': proofs, 'links': links, 'caption': caption, 'language_route': route,
                'retain_policy': s.retain_policy, 'created_at': utc_now(),
                'source_lease_id': key, 'source_lease': f'asr/leases/{key}.json',
                'canonical_record_path': record['path'], 'consumer_dispatch_allowed': False}
            save(s, state)  # intent and reserved bytes precede the first hardlink
        for item in state['links'].values():
            source, target = s.path(item['source_path']), s.path(item['path'])
            need(source.exists() and stable_file(source) == item['fingerprint'], 'handoff_input_changed')
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists(): need(os.path.samefile(source, target), 'handoff_path_conflict')
            else: os.link(source, target)
            need(os.path.samefile(source, target) and stable_file(target) == item['fingerprint'], 'handoff_link_failed')
        state['status'] = 'retained_waiting_archive'
        # Link creation can alter source ctime. The collector can use these
        # refreshed fingerprints with the already verified stream hashes.
        state['collector_trusted'] = {k: list(storage.fingerprint(s.path(v['source_path'])))
                                      for k, v in state['links'].items()}
        source_lease = {'schema_version': 1, 'profile': PROFILE, 'lease_id': key, 'video_id': state['video_id'],
            'owner': s.owner, 'status': 'retained_waiting_archive', 'phase': 'canonical_receipt_pending',
            'expires_at': state['expires_at'], 'consumers_active': False, 'handoff_id': key}
        queue.atomic(s.path(state['source_lease']), source_lease)
        save(s, state)
        return state


def canonical(s, state, record):
    durable = storage.load_state(s.path('sync/drive_ingest_manifest.jsonl')).get(state['video_id'], {})
    need(durable == record and storage.receipt_complete(record, record, s.remote), 'handoff_canonical_not_durable')
    need(record.get('video_id') == state['video_id'] and
         queue.proof(record) == state['sources']['audio'] and
         queue.proof(record.get('metadata', {})) == state['sources']['metadata'], 'handoff_canonical_source')


def publish_ready(s, state):
    lease = read(s.path(state['source_lease']))
    ready = state['status'] == 'ready' and lease.get('status') == 'active' and lease.get('phase') == 'input_verified_waiting_gpu_lease'
    queue.atomic(state_path(s, state['handoff_id']).with_name('ready.json'),
                 {'schema_version': 1, 'gpu_activation_allowed': False,
                  'admissions': [state['admission_path']] if ready else []})


def finalize_after_cleanup(s, key, canonical_record):
    """No GPU activation: returns a ready English admission or disabled review."""
    with queue.queue_lock(s.root):
        state = read(state_path(s, key))
        need(state['allocation_lease_id'] == s.lease_id and state['owner'] == s.owner, 'handoff_owner')
        canonical(s, state, canonical_record)
        if state['status'] not in {'retained_waiting_archive', 'ready', 'pending_language_review', 'caption_coverage_review'}:
            need(state['status'] in {'caption_satisfied', 'deferred_language_review', 'released'}, 'handoff_not_retained')
            return state
        check_links(s, state)
        if not state['links']:
            state['status'] = 'caption_satisfied' if state['language_route']['explicit_original_english'] else 'deferred_language_review'
            if state['status'] == 'deferred_language_review':
                model = read(HERE / 'gpu_asr_multilingual_provenance.json')['model']
                proposal = {'schema_version': 1, 'state': 'disabled_pending_language_review',
                    'video_id': state['video_id'], 'sources': state['sources'], 'language_evidence': state['language_route'],
                    'requested_views': ['original', 'english_translation_or_explicit_alias'],
                    'desired_model': {k: model[k] for k in ('repository', 'revision')},
                    'execute_allowed': False, 'text_generation_allowed': False, 'local_inputs_retained': False,
                    'preserves_original_metadata': True, 'human_reviewed': False}
                target = state_path(s, key).with_name('review-proposal.json')
                queue.atomic(target, proposal)
                state['admission_path'] = str(target)
            lease = read(s.path(state['source_lease']))
            lease.update(status='released', phase=state['status'] + '_no_input_links', consumers_active=False)
            queue.atomic(s.path(state['source_lease']), lease)
            save(s, state)
            publish_ready(s, state)
            return state
        if state['status'] != 'retained_waiting_archive':
            publish_ready(s, state)  # recover a lost readiness ACK, not a new job
            return state
        admission_lease(s)
        for item in state['links'].values():
            item['finalized_fingerprint'] = list(storage.fingerprint(s.path(item['path'])))
        metadata = read(s.path(state['links']['metadata']['path']))
        route = language_route(metadata)
        need(route == state['language_route'] and route['explicit_original_english'], 'handoff_language_route_changed')
        declared, english = route['declared_language'], True
        duration = route['duration_seconds'] or canonical_record.get('duration_s')
        need(type(duration) in (int, float) and math.isfinite(duration) and duration > 0, 'handoff_duration')
        model = read(HERE / ('gpu_asr_provenance.json' if english else 'gpu_asr_multilingual_provenance.json'))['model']
        language = {'code': declared if english else None, 'basis': 'verified_explicit_original_archived_metadata' if english else 'pending_language_review'}
        job_id = 'asr-' + digest({'video_id': state['video_id'], 'audio_sha256': state['sources']['audio']['sha256'],
                                'task': 'transcribe-original-speech-v1'})[:24]
        job = {'job_id': job_id, 'video_id': state['video_id'], 'source': {'channel_dir': state['channel_dir'], 'tab': state['tab']},
               **state['sources'], 'duration_seconds': duration, 'caption': state['caption'], 'language': language,
               'desired_model': {k: model[k] for k in ('repository', 'revision')},
               'requested_output': {'task': 'transcribe', 'translate': False}}
        job['desired_model']['device'] = 'cuda'
        admission = {'schema_version': 1, 'state': 'input_verified_waiting_gpu_lease', 'job_id': job_id,
            'video_id': state['video_id'], 'job': job, 'language': language,
            'source_lease': str(s.path(state['source_lease'])), 'source_lease_id': key,
            'verified_input_objects': [{'kind': k, 'private_path': str(s.path(v['path'])), 'source': state['sources'][k],
                'local': {p: state['sources'][k][p] for p in ('bytes', 'md5', 'sha256')}} for k, v in state['links'].items()]}
        # Unusable/unavailable/partial caption evidence is retained as an
        # alternative; it does not occupy a permanently disabled English slot.
        state['status'] = 'ready'
        if state['status'] != 'ready':
            admission.update(state='disabled_pending_review', execute_allowed=False, text_generation_allowed=False,
                             preserves_original_metadata=True, metadata_content_flags=metadata.get('metadata_content_flags', {}),
                             requested_views=['original', 'english_translation_or_explicit_alias'])
        target = state_path(s, key).with_name('admission.json' if state['status'] == 'ready' else 'review-proposal.json')
        queue.atomic(target, admission)
        lease = read(s.path(state['source_lease']))
        lease.update(status='active' if state['status'] == 'ready' else 'held',
            phase='input_verified_waiting_gpu_lease' if state['status'] == 'ready' else state['status'],
            private_path=str(s.path(state['links']['audio']['path'])),
            metadata_private_path=str(s.path(state['links']['metadata']['path'])),
            sourceDriveID=job['audio']['drive_id'], expected_bytes=job['audio']['bytes'],
            expected_hashes={k: job['audio'][k] for k in ('md5', 'sha256')}, frame_id=PROFILE,
            admission_path=str(target), ready_at=utc_now())
        queue.atomic(s.path(state['source_lease']), lease)
        state.update(admission_path=str(target), consumer_dispatch_allowed=False)
        save(s, state)
        # This per-job marker is the only readiness publication, written last.
        publish_ready(s, state)
        return state


def retire_after_result(s, key, result_receipt, observed_result, *, consumer_terminal):
    """Caller passes the publisher's one readback; this helper never re-stats Drive.

    consumer_terminal is an owner-produced record, not PID expiry: exact source
    lease, terminal process, and result publication must all be established.
    """
    with queue.queue_lock(s.root):
        state = read(state_path(s, key))
        need(state['owner'] == s.owner and state['allocation_lease_id'] == s.lease_id, 'handoff_owner')
        if state['status'] == 'released': return state
        need(state['status'] in {'ready', 'retiring'}, 'handoff_result_not_ready')
        expected_admission = state_path(s, key).with_name('admission.json')
        need(Path(state['admission_path']) == expected_admission, 'handoff_admission_scope')
        admission = read(expected_admission)
        lease = read(s.path(state['source_lease']))
        lease_retired = (state['status'] == 'retiring' and lease.get('status') == 'released' and
                         lease.get('phase') == 'owned_handoff_links_retired')
        need(lease.get('lease_id') == key and (lease.get('status') in {'active', 'result_verified_on_drive'} or lease_retired) and
             consumer_terminal.get('source_lease_id') == key and consumer_terminal.get('process_exited') is True and
             consumer_terminal.get('consumers_active') is False and consumer_terminal.get('run_id') == result_receipt.get('run_id'),
             'handoff_consumer_active')
        need(lease.get('sourceDriveID') == state['sources']['audio']['drive_id'] and
             lease.get('expected_bytes') == state['sources']['audio']['bytes'] and
             lease.get('expected_hashes') == {k: state['sources']['audio'][k] for k in ('md5', 'sha256')} and
             Path(lease.get('private_path', '')) == s.path(state['links']['audio']['path']) and
             Path(lease.get('metadata_private_path', '')) == s.path(state['links']['metadata']['path']), 'handoff_source_lease_changed')
        need(queue.result_matches(result_receipt, admission['job'], key) and
             result_receipt.get('source_metadata') == state['sources']['metadata'], 'handoff_result_source')
        durable = storage.load_state(s.path('sync/asr_manifest.jsonl')).get(state['video_id'], {})
        need(durable == result_receipt, 'handoff_result_not_durable')
        storage.verify_remote(observed_result, result_receipt)
        need(observed_result.get('ID') == result_receipt['drive_id'], 'handoff_result_drive_identity')
        check_links(s, state, missing_ok=state['status'] == 'retiring')
        state.update(status='retiring', result_proof=queue.proof(result_receipt), consumer_terminal=consumer_terminal)
        save(s, state)  # durable proof and exact deletion intent before unlink
        for item in state['links'].values(): s.path(item['path']).unlink(missing_ok=True)
        lease.update(status='released', phase='owned_handoff_links_retired', consumers_active=False, released_at=utc_now())
        queue.atomic(s.path(state['source_lease']), lease)
        state.update(status='released', released_at=utc_now())
        save(s, state)
        return state
