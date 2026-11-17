"""Retain reviewed ASR holds without occupying active consumer slots.

Explicit invocation only. This helper performs no inference, source requests,
Drive calls or deletion. A durable transaction precedes a same-filesystem
directory rename; interrupted moves can be completed with the same lease ID.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gpu_asr_queue as queue
from gpu_asr import kernel_lock
from drive_ingest import IngestError, is_link

MAX_DOCUMENT_BYTES = 1_000_000


def require(ok, code):
    if not ok:
        raise IngestError(code, code)


def root_path(root):
    supplied = Path(root).absolute()
    require(not any(is_link(p) for p in (supplied, *supplied.parents)), 'quarantine_link')
    return queue.ensure_outside_git(supplied)


def document(path):
    require(path.is_file() and path.stat().st_size <= MAX_DOCUMENT_BYTES, 'quarantine_document')
    raw = path.read_bytes()
    return raw, json.loads(raw)


def immutable(path, raw):
    """Never overwrite an existing history file, even during recovery."""
    require(len(raw) <= MAX_DOCUMENT_BYTES, 'quarantine_document')
    if path.exists():
        require(path.read_bytes() == raw, 'quarantine_history_changed')
        return
    with path.open('xb') as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())


def hold_record(root, lease, job):
    path = queue.local_path(root, 'sync/asr_language_manifest.jsonl')
    require(path.is_file(), 'quarantine_hold_missing')
    chosen = None
    with path.open('rb') as source:
        for raw in source:
            require(len(raw) <= MAX_DOCUMENT_BYTES, 'quarantine_document')
            if not raw.strip():
                continue
            row = json.loads(raw)
            if row.get('video_id') == lease['video_id']:
                chosen = raw, row
    require(chosen is not None, 'quarantine_hold_missing')
    raw, row = chosen
    require(row.get('status') == 'held' and row.get('semantic_text_generated') is False and
            row.get('source_delete_allowed') is False and row.get('source_lease_id') == lease['lease_id'] and
            row.get('job_id') == lease['job_id'] and row.get('source_audio_sha256') == job['audio']['sha256'] and
            row.get('source_audio_drive_id') == job['audio']['drive_id'] and
            row.get('proposal_sha256') == lease.get('proposal_sha256') and
            row.get('decision', {}).get('reason') == lease.get('hold_reason'), 'quarantine_hold_mismatch')
    return raw, row


def inspect(root, video_id, lease_id):
    require(queue.ID_RE.fullmatch(video_id or '') and
            re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}', lease_id or ''), 'quarantine_identity')
    lease_path = queue.local_path(root, f'asr/leases/{video_id}.json')
    lease_raw, current = document(lease_path)
    require(current.get('lease_id') == lease_id and current.get('video_id') == video_id, 'quarantine_lease_mismatch')
    folder = queue.local_path(root, f'asr/held/{lease_id}')
    transaction = folder/'transaction.json'
    prior = document(transaction)[1] if transaction.exists() else None
    if prior:
        require(prior.get('source_lease_id') == lease_id and prior.get('video_id') == video_id, 'quarantine_history_changed')
        original_raw, original = document(folder/'lease.before.json')
        require(queue.sha(original_raw) == prior.get('original_lease_sha256'), 'quarantine_history_changed')
    else:
        original_raw, original = lease_raw, current
    require(original.get('status') == 'active' and original.get('phase') == 'held_language_review', 'quarantine_not_held')
    admission_path = queue.safe_asr(root, original.get('admission_path', ''), 'jobs')
    admission_raw, admission = document(admission_path)
    require(admission.get('source_lease_id') == lease_id and admission.get('job_id') == original.get('job_id') and
            admission.get('video_id') == video_id and
            queue.safe_asr(root, admission.get('source_lease', ''), 'leases') == lease_path, 'quarantine_admission_mismatch')
    job = admission.get('job', {})
    require(job.get('video_id') == video_id and job.get('job_id') == original['job_id'], 'quarantine_admission_mismatch')
    require(all(queue.valid_proof(job.get(k)) for k in ('audio', 'metadata')), 'quarantine_source_proof')
    require(original.get('sourceDriveID') == job['audio']['drive_id'] and
            original.get('expected_bytes') == job['audio']['bytes'] and
            original.get('expected_hashes') == {k: job['audio'][k] for k in ('md5', 'sha256')}, 'quarantine_source_proof')
    source = queue.local_path(root, f'asr/input/{video_id}')
    target = queue.local_path(root, f'asr/held/{lease_id}/input')
    objects = admission.get('verified_input_objects', [])
    require(len(objects) == 2 and {v.get('kind') for v in objects} == {'audio', 'metadata'}, 'quarantine_source_proof')
    files = []
    for item in objects:
        kind = item['kind']
        path = queue.safe_asr(root, item.get('private_path', ''), 'input')
        key = 'private_path' if kind == 'audio' else 'metadata_private_path'
        require(path.parent == source and str(path) == original.get(key) and
                item.get('source') == queue.proof(job[kind]) and item.get('source_drive_id_rechecked') is True and
                item.get('local') == {k: job[kind][k] for k in ('bytes', 'md5', 'sha256')}, 'quarantine_source_proof')
        files.append({'kind':kind, 'name':path.name, 'source':queue.proof(job[kind])})
    require(len({f['name'] for f in files}) == 2, 'quarantine_source_proof')
    hold_raw, held = hold_record(root, original, job)
    evidence = {'schema_version':1, 'video_id':video_id, 'job_id':original['job_id'], 'source_lease_id':lease_id,
                'original_lease_sha256':queue.sha(original_raw), 'original_admission_sha256':queue.sha(admission_raw),
                'held_decision_sha256':queue.sha(hold_raw), 'hold_reason':held['decision']['reason'],
                'source_dir':source.relative_to(root).as_posix(), 'held_dir':target.relative_to(root).as_posix(),
                'files':files, 'completion_claimed':False, 'source_delete_allowed':False}
    if prior:
        require(all(prior.get(k) == v for k, v in evidence.items()), 'quarantine_history_changed')
        require(document(folder/'admission.before.json')[0] == admission_raw and
                document(folder/'hold.before.json')[0] == hold_raw, 'quarantine_history_changed')
    if current.get('status') == 'quarantined_hold':
        require(prior and current.get('quarantine_original_lease_sha256') == evidence['original_lease_sha256'] and
                current.get('quarantine_manifest') == str(transaction), 'quarantine_lease_mismatch')
    else:
        require(lease_raw == original_raw, 'quarantine_lease_changed')
    require(source.exists() != target.exists(), 'quarantine_ambiguous_location')
    existing = source if source.exists() else target
    require(existing.is_dir() and not is_link(existing), 'quarantine_link')
    contents = list(existing.iterdir())
    require({p.name for p in contents} == {f['name'] for f in files} and
            all(p.is_file() and not is_link(p) for p in contents), 'quarantine_unexpected_files')
    for item in files:
        actual = queue.hash_file(queue.local_path(existing, item['name']))
        require(actual == {k:item['source'][k] for k in ('bytes', 'md5', 'sha256')}, 'quarantine_input_changed')
    return {'root':root, 'lease_path':lease_path, 'lease_raw':lease_raw, 'lease':current,
            'original':original, 'original_raw':original_raw, 'admission_raw':admission_raw, 'hold_raw':hold_raw,
            'folder':folder, 'transaction':transaction, 'prior':prior, 'source':source, 'target':target, 'evidence':evidence}


def plan_quarantine(root, video_id, lease_id):
    """Read-only proof check; caller still must explicitly invoke quarantine_hold."""
    state = inspect(root_path(root), video_id, lease_id)
    return {**state['evidence'], 'state':'quarantine_planned',
            'workspace_bytes':queue.tree_bytes(state['root']/'asr'), 'workspace_limit_bytes':queue.MAX_INPUT_BYTES}


def finish_index(root, receipt, frame_id):
    path = queue.local_path(root, 'sync/asr_quarantine_manifest.jsonl')
    prior, _, warnings = queue.read_receipts(path)
    require(not any(warnings.values()), 'quarantine_index_malformed')
    if prior.get(receipt['video_id']) != receipt:
        queue.journal(path, receipt)
    queue.refresh_ready(root, frame_id=frame_id)
    if frame_id and (root/'asr/jobs/ready.json').exists():
        queue.refresh_ready(root)


def quarantine_hold(root, video_id, lease_id, *, operator, max_input_bytes=queue.MAX_INPUT_BYTES):
    """No deletion: retire one terminal hold's consumer lease and retain its data."""
    root = root_path(root)
    require(isinstance(operator, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,80}', operator), 'quarantine_operator')
    require(type(max_input_bytes) is int and 0 < max_input_bytes <= queue.MAX_INPUT_BYTES, 'quarantine_budget')
    # Same order as an ASR worker: GPU owner lock, then source queue lock.
    with kernel_lock(queue.local_path(root, 'sync/asr_gpu_owner.lock')), queue.queue_lock(root):
        state = inspect(root, video_id, lease_id)
        if state['prior'] and state['prior'].get('state') == 'quarantined_hold':
            require(state['lease'].get('status') == 'quarantined_hold' and
                    queue.sha(state['lease_raw']) == state['prior'].get('updated_lease_sha256'), 'quarantine_lease_changed')
            finish_index(root, state['prior'], state['lease'].get('frame_id'))
            return state['prior']
        overhead = sum(len(state[k]) for k in ('original_raw', 'admission_raw', 'hold_raw'))
        require(queue.tree_bytes(root/'asr') + overhead + queue.RESERVE <= max_input_bytes, 'quarantine_storage_limit')
        folder, transaction = state['folder'], state['transaction']
        if not state['prior']:
            require(not folder.exists(), 'quarantine_existing_folder')
            folder.mkdir(parents=True)
            immutable(folder/'lease.before.json', state['original_raw'])
            immutable(folder/'admission.before.json', state['admission_raw'])
            immutable(folder/'hold.before.json', state['hold_raw'])
            queue.atomic(transaction, {**state['evidence'], 'state':'prepared', 'operator':operator, 'prepared_at':queue.utc_now()})
        if state['source'].exists():
            require(not state['target'].exists() and state['source'].stat().st_dev == folder.stat().st_dev,
                    'quarantine_cross_filesystem')
            # Both resolved absolute paths were checked within explicit input/held
            # scopes, including every existing parent link, before this rename.
            state['source'].rename(state['target'])
        moved = inspect(root, video_id, lease_id)
        updated = dict(moved['original'], status='quarantined_hold', phase='held_language_review',
                       active_consumer=False, quarantine_manifest=str(transaction),
                       quarantine_original_lease_sha256=moved['evidence']['original_lease_sha256'],
                       quarantine_at=queue.utc_now(), quarantine_operator=operator,
                       quarantine_previous_paths={'audio':moved['original']['private_path'],
                                                  'metadata':moved['original']['metadata_private_path']})
        for item in moved['evidence']['files']:
            updated['private_path' if item['kind'] == 'audio' else 'metadata_private_path'] = str(moved['target']/item['name'])
        queue.atomic(moved['lease_path'], updated)
        receipt = {**moved['evidence'], 'state':'quarantined_hold', 'operator':operator,
                   'quarantined_at':updated['quarantine_at'], 'updated_lease_sha256':queue.sha(queue.encoded(updated)),
                   'workspace_counted':True, 'active_consumer':False}
        queue.atomic(transaction, receipt)
        finish_index(root, receipt, updated.get('frame_id'))
        return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--video-id', required=True)
    parser.add_argument('--lease-id', required=True)
    parser.add_argument('--operator', default='root')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    result = (quarantine_hold(args.root, args.video_id, args.lease_id, operator=args.operator) if args.apply
              else plan_quarantine(args.root, args.video_id, args.lease_id))
    print(json.dumps({k:result[k] for k in ('state', 'video_id', 'source_lease_id', 'completion_claimed')}))


if __name__ == '__main__':
    main()
