"""Bounded private ASR inputs from verified newest20 audio; no YouTube requests.

The queue preserves caption alternatives, admits only declared original English,
and never deletes archived originals. A result proof releases only leased copies.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import io
import csv
import json
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_catalog import read_receipts
from common import ID_RE, ensure_outside_git, utc_now
from drive_ingest import (MAX_LOCAL_BYTES, MIN_FREE_BYTES, Rclone, IngestError, caption_receipt_complete,
                          caption_track_verified, exclusive_lock, hash_file, journal, local_path, managed_roots,
                          receipt_complete, reserved_project_growth, storage_usage, tree_bytes, verify_remote)

MAX_INPUT_BYTES = MAX_LOCAL_BYTES
RESERVE = 128_000
TRANSFER_HEADROOM = 1_048_576  # rclone hard cutoff accounts a final buffered read
PROOF_KEYS = ('remote', 'drive_id', 'bytes', 'md5', 'sha256')
SOURCE_KEYS = ('channel_dir', 'source_channel_name', 'primary_person_id', 'primary_person_name',
               'primary_person_role', 'primary_person_basis', 'tab', 'listing_rank', 'duration_s',
               'channeling', 'entity', 'entity_label_basis', 'queue_provenance')
ELIGIBLE_DECISIONS = {'eligible_original_english', 'eligible_declared_english', 'eligible_native_original_english'}


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + '.' + uuid.uuid4().hex + '.part')
    with part.open('xb') as output:
        output.write(encoded(value))
        output.flush()
        os.fsync(output.fileno())
    os.replace(part, path)


def proof(record):
    return {key: record.get(key) for key in PROOF_KEYS}


def valid_proof(record):
    return bool(isinstance(record, dict) and record.get('remote') and record.get('drive_id') and
                type(record.get('bytes')) is int and record['bytes'] > 0 and
                re.fullmatch(r'[a-f0-9]{32}', str(record.get('md5', ''))) and
                re.fullmatch(r'[a-f0-9]{64}', str(record.get('sha256', ''))))


def english(language):
    return isinstance(language, str) and bool(re.fullmatch(r'en(?:-[A-Za-z0-9]+)*', language))


def native_original_english(record):
    """Candidate evidence only; admission must recheck the archived sidecar."""
    selected = record.get('native_format_binding')
    fields = {'videoId','itag','lastModified','xtags','mimeType','codec','contentLength','durationMs',
              'language','originalBasis','trackId','noDRM','audioOnly','transportKind'}
    if not isinstance(selected, dict) or set(selected) != fields:
        return None
    transport = record.get('native_transport_kind')
    if transport not in {'direct_http','sabr_reassembled'} or selected['transportKind'] != transport or \
            selected['videoId'] != record.get('video_id') or selected['originalBasis'] != 'published_original' or \
            selected['noDRM'] is not True or selected['audioOnly'] is not True or not english(selected['language']):
        return None
    if type(selected['itag']) is not int or not 0 < selected['itag'] < 10000 or \
            not isinstance(selected['lastModified'], str) or not re.fullmatch(r'[0-9]{1,30}', selected['lastModified']) or \
            not isinstance(selected['xtags'], str) or not 0 < len(selected['xtags']) <= 16384 or \
            selected['codec'] not in {'opus','vorbis','aac','mp4a.40.2'} or \
            not isinstance(selected['mimeType'], str) or not re.fullmatch(r'audio/(?:webm|mp4|ogg)(?:;\s*codecs="[A-Za-z0-9., -]+")?', selected['mimeType']) or \
            type(selected['durationMs']) is not int or not 0 < selected['durationMs'] < 2**53 or \
            not (selected['trackId'] is None or isinstance(selected['trackId'], str) and len(selected['trackId']) <= 200):
        return None
    size = selected['contentLength']
    if not (type(size) is int and 0 < size < 2**53 or transport == 'sabr_reassembled' and size is None):
        return None
    identity = {key:value for key,value in selected.items() if key != 'transportKind'}
    digest = sha(json.dumps(identity, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    if record.get('native_format_binding_sha256') != digest:
        return None
    return selected['language']


def result_matches(result, job, lease_id=None):
    """Match durable completion to this source, not just a reused video ID."""
    run = result.get('run_id', '')
    parent = job['audio']['remote'].rpartition('/')[0]
    return bool(result.get('status') == 'verified' and result.get('artifact_kind') == 'asr_bundle' and
                valid_proof(result) and isinstance(run,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,159}', run) and
                result.get('video_id') == job['video_id'] and
                result.get('source_audio_sha256') == job['audio']['sha256'] and
                result.get('source_audio_drive_id') == job['audio']['drive_id'] and
                result.get('job_id', job['job_id']) == job['job_id'] and
                (lease_id is None or result.get('source_lease_id') == lease_id) and
                result['remote'] == f"{parent}/{job['video_id']}/ASR/{run}/{run}.zip")


def metadata_language_evidence(root, record, audio):
    """A review label is insufficient: rehash the exact archived sidecar bytes."""
    if record.get('video_id') != audio['video_id'] or record.get('audio_sha256') != audio['sha256'] or \
            record.get('metadata_proof') != proof(audio['metadata']):
        raise IngestError('language_evidence', 'Language review refers to a different archived source')
    local = record.get('verified_local_metadata', {})
    if local.get('source') != proof(audio['metadata']) or local.get('source_drive_id_rechecked') is not True:
        raise IngestError('language_evidence', 'Language metadata lacks its exact Drive identity proof')
    path = safe_asr(root, local.get('private_path', ''), 'jobs')
    actual = hash_file(path)
    if actual != local.get('local') or any(actual[key] != audio['metadata'][key] for key in ('bytes','md5','sha256')):
        raise IngestError('language_evidence', 'Language metadata bytes differ from the archived proof')
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('source', {}).get('video_id') != audio['video_id']:
        raise IngestError('language_evidence', 'Language metadata video identity differs')
    primary, fallback = data.get('languages', {}).get('audio'), data.get('metadata', {}).get('language')
    if primary and fallback and primary != fallback:
        raise IngestError('language_evidence', 'Saved audio language declarations conflict')
    language = primary or fallback
    return language if english(language) else None


def build_plan(root, queue_path, remote, model_repository, model_revision, *, language_evidence=None, evidence_only=False):
    root, queue_path = Path(root), Path(queue_path)
    raw = queue_path.read_bytes()
    content = raw.decode('utf-8-sig')
    mixed = content.lstrip().startswith('{')
    if mixed:
        from ingestion_status import selection_rows
        selected = selection_rows(queue_path, content=raw)
        rows, scope = selected['rows'], selected['basis']
    else:
        rows = list(csv.DictReader(io.StringIO(content)))
        scope = 'newest20_videos_snapshot'
    tabs = {'videos', 'shorts', 'streams', 'unknown'} if mixed else {'videos'}
    seen, ranks, channels = set(), set(), collections.Counter()
    for row in rows:
        video_id = row.get('video_id', '')
        try:
            rank = int(row.get('listing_rank', ''))
        except ValueError as exc:
            raise ValueError('A strict newest20 listing rank is required') from exc
        key = (row.get('channel_dir'), rank)
        if not ID_RE.fullmatch(video_id) or video_id in seen or row.get('tab') not in tabs or not 0 <= rank < 20 or key in ranks:
            raise ValueError('Queue must contain unique newest20 IDs, permitted formats and per-channel ranks')
        seen.add(video_id)
        ranks.add(key)
        channels[row.get('channel_dir')] += 1
    if any(count > 20 for count in channels.values()):
        raise ValueError('More than 20 items in a channel newest20 frame')
    audio, audio_sha, audio_warnings = read_receipts(root/'sync/drive_ingest_manifest.jsonl')
    captions, caption_sha, caption_warnings = read_receipts(root/'sync/drive_caption_manifest.jsonl')
    completed, _, _ = read_receipts(root/'sync/asr_manifest.jsonl')
    sources = {'queue_sha256': sha(raw), 'audio_journal_sha256': audio_sha, 'caption_journal_sha256': caption_sha}
    if mixed:
        sources['selection_sha256'] = sources['queue_sha256']
    evidence = {}
    if language_evidence:
        evidence_raw = safe_asr(root, language_evidence, 'jobs').read_bytes()
        document = json.loads(evidence_raw)
        records = document.get('records', [])
        if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
            raise ValueError('Language evidence records must be objects')
        evidence = {item.get('video_id'): item for item in records}
        if len(evidence) != len(records):
            raise ValueError('Duplicate language evidence video IDs')
        sources['language_evidence_sha256'] = sha(evidence_raw)
    elif evidence_only:
        raise ValueError('A separate language-evidence frame requires evidence')
    jobs, counts = [], collections.Counter()
    for row in rows:
        video_id = row['video_id']
        rec, cap = audio.get(video_id, {}), captions.get(video_id, {})
        if (rec.get('channel_dir') != row['channel_dir'] or not receipt_complete(rec, rec, remote)
                or not valid_proof(rec) or not valid_proof(rec.get('metadata'))):
            counts['audio_not_verified'] += 1
            continue
        if cap.get('channel_dir') not in (None, row['channel_dir']):
            cap = {}
        tracks = cap.get('tracks', [])
        proven = [track for track in tracks if caption_track_verified(track, rec, remote)]
        complete = caption_receipt_complete(cap, rec, remote)
        origin_en = any(track.get('kind') == 'automatic_original' and english(track.get('language')) and
                        track.get('machine_translated') is False for track in tracks)
        declared_en = metadata_language_evidence(root, evidence[video_id], rec) if video_id in evidence else None
        native_en = native_original_english(rec)
        if evidence_only and not declared_en:
            counts['outside_language_evidence_frame'] += 1
            continue
        decision = ('exclude_complete_english_captions' if proven and complete else
                    'defer_caption_coverage_review' if proven else
                    'eligible_declared_english' if declared_en else
                    'eligible_native_original_english' if native_en else
                    'eligible_original_english' if origin_en else 'hold_language_unconfirmed')
        state = ('complete_receipt' if proven and complete else 'verified_tracks_incomplete_inventory' if proven else
                 'no_english_tracks_reported' if complete and cap.get('status') == 'none' else
                 'pending_caption_source' if cap else 'caption_inventory_unknown')
        job_id = 'asr-' + sha(encoded({'video_id':video_id,'audio_sha256':rec['sha256'],
                                     'task':'transcribe-original-speech-v1'}))[:24]
        job = {'schema_version':1,'job_id':job_id,'video_id':video_id,'decision':decision,
          'scope':scope,'source':{key:row.get(key) for key in SOURCE_KEYS},
          'duration_seconds':rec.get('duration_s') or row.get('duration_s'),
          'audio':proof(rec),'metadata':proof(rec['metadata']),
          'caption':{'state':state,'receipt_status':cap.get('status','unknown'),
            'policy':cap.get('policy'),'inventory_status':cap.get('inventory_status','unknown'),
            'source_error_class':cap.get('source_error_class'),'proven_tracks':len(proven),
            'selected_tracks':len(tracks),'unresolved':cap.get('unresolved',[]),
            'tracks':[{**{key:t.get(key) for key in ('track_id','language','kind','raw_format','machine_translated','status')},
                      **({'verified_bundle':proof(t['bundle'])} if t in proven else {})} for t in tracks],
            'speech_coverage':{'status':'not_measured','ratio':None},'alternatives_remain_distinct':True},
          'language':{'code':declared_en or native_en or ('en' if origin_en else None),
                      'basis':'verified_archived_audio_metadata' if declared_en else
                              'verified_native_original_format_candidate' if native_en else
                              'provider_original_automatic_inventory' if origin_en else 'unconfirmed'},
          'desired_model':{'repository':model_repository,'revision':model_revision,'device':'cuda'},
          'requested_output':{'task':'transcribe','translate':False,'preserve_caption_alternatives':True},
          'provenance':{**sources,'queue_row_sha256':sha(encoded(row)),
                        'audio_receipt_sha256':sha(encoded(rec)),'caption_receipt_sha256':sha(encoded(cap))}}
        if result_matches(completed.get(video_id, {}), job):
            job['decision'] = 'asr_result_already_verified'
        counts[job['decision']] += 1
        jobs.append(job)
    return {'schema_version':1,'scope':'newest20_verified_language_evidence' if evidence_only else scope,'queue_items':len(rows),
            'counts':dict(counts),'jobs':jobs,'input_sources':sources,
            'parse_warnings':{'audio':audio_warnings,'captions':caption_warnings}}


def queue_lock(root):
    # Reuse the proven cross-platform kernel lock in a separate ASR namespace.
    return exclusive_lock(local_path(Path(root), 'asr'))


def safe_asr(root, path, area=''):
    base = local_path(Path(root), 'asr' + ('/'+area if area else ''))
    supplied = Path(path)
    if not supplied.is_absolute():
        supplied = Path(root)/supplied
    return local_path(base, supplied.relative_to(base))


def leases(root):
    folder = local_path(Path(root), 'asr/leases')
    return [json.loads(path.read_text(encoding='utf-8')) for path in folder.glob('*.json')] if folder.exists() else []


def frame_folder(root, frame_id=None):
    if frame_id is not None and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', frame_id):
        raise ValueError('Unsafe ASR frame ID')
    return local_path(Path(root), 'asr/jobs' + ('/frames/'+frame_id if frame_id else ''))


def refresh_ready(root, remaining=None, frame_id=None):
    rows = leases(root)
    ready_path = frame_folder(root, frame_id)/'ready.json'
    previous = json.loads(ready_path.read_text(encoding='utf-8')) if ready_path.exists() else {}
    if remaining is None:
        remaining = previous.get('eligible_remaining')
    ready = [item['admission_path'] for item in rows if item.get('status') == 'active' and
             item.get('phase') == 'input_verified_waiting_gpu_lease' and item.get('admission_path') and
             item.get('frame_id') == frame_id]
    result = {**previous,'schema_version':1,'updated_at':utc_now(),'admissions':sorted(ready),
              'active_inputs':sum(item.get('status') == 'active' for item in rows), 'frame_id':frame_id,
              'eligible_remaining':remaining,'preparation_complete':remaining == 0 if remaining is not None else False}
    atomic(ready_path, result)
    return result


def pull_verified(drive, expected, destination, available_bytes):
    """Exact object lookup, bounded transfer, then size/MD5/SHA256 admission."""
    if not valid_proof(expected) or expected['bytes'] + (0 if destination.exists() else TRANSFER_HEADROOM) > available_bytes:
        raise IngestError('storage_limit', 'Input does not fit its reserved byte allowance')
    observed = drive.stat(expected['remote'])
    verify_remote(observed, expected)
    if observed.get('ID') != expected['drive_id']:
        raise IngestError('drive_verify', 'Drive object identity differs from the archived source')
    if destination.exists():
        actual = hash_file(destination)
    else:
        part = destination.with_name(destination.name+'.part')
        if part.exists():
            raise IngestError('partial_input', 'Existing input partial requires owner recovery')
        destination.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(drive, 'download'):
            drive.download(expected['remote'], part, expected['bytes'])
        else:
            drive.execute(['copyto',expected['remote'],str(part),'--no-traverse','--transfers','1',
                '--checkers','1','--multi-thread-streams','0','--buffer-size','1M','--bwlimit','2M',
                '--max-transfer',str(expected['bytes']+TRANSFER_HEADROOM)+'B','--cutoff-mode','hard',
                '--retries','1','--low-level-retries','1','--contimeout','15s','--timeout','60s',
                '--tpslimit','2','--tpslimit-burst','1'],max(600, 180 + expected['bytes']//(2*1024*1024)),
                'reserved ASR input download')
        actual = hash_file(part)
        if any(actual[key] != expected[key] for key in ('bytes','md5','sha256')):
            raise IngestError('local_changed', 'Downloaded input differs from the archived proof; retained')
        os.replace(part, destination)
    if any(actual[key] != expected[key] for key in ('bytes','md5','sha256')):
        raise IngestError('local_changed', 'Local input differs from the archived proof; retained')
    return {'private_path':str(destination),'source':proof(expected),'local':actual,
            'source_drive_id_rechecked':True,'verified_at':utc_now()}


def room_for_inputs(root, required, max_input_bytes, min_free_bytes):
    if tree_bytes(root/'asr') + required + RESERVE > max_input_bytes:
        return False
    _, used = storage_usage(root, managed_roots(root))
    growth = required + RESERVE + reserved_project_growth(root)
    return used + growth <= MAX_LOCAL_BYTES and shutil.disk_usage(root).free - growth >= min_free_bytes


def prepare_inputs(root, queue_path, remote, drive, *, model_repository, model_revision,
                   max_ready=3, max_input_bytes=MAX_INPUT_BYTES, min_free_bytes=MIN_FREE_BYTES,
                   language_evidence=None, evidence_only=False, frame_id=None):
    root = ensure_outside_git(root)
    if not 1 <= max_ready <= 3 or not 0 < max_input_bytes <= MAX_INPUT_BYTES:
        raise ValueError('At most three active inputs may share the project storage ceiling')
    with queue_lock(root):
        if frame_id:
            primary_ready = local_path(root,'asr/jobs/ready.json')
            primary = json.loads(primary_ready.read_text(encoding='utf-8')) if primary_ready.exists() else {}
            if primary and not primary.get('preparation_complete') or any(
                    item.get('status') == 'active' and item.get('frame_id') != frame_id for item in leases(root)):
                raise IngestError('frame_active','The preceding frame has not released all its inputs')
        plan = build_plan(root, queue_path, remote, model_repository, model_revision,
                          language_evidence=language_evidence, evidence_only=evidence_only)
        digest = sha(encoded(plan))
        folder = frame_folder(root, frame_id)
        snapshot = folder/f'queue-{digest}.json'
        if not snapshot.exists():
            if not room_for_inputs(root, len(encoded(plan)), max_input_bytes, min_free_bytes):
                raise IngestError('storage_limit', 'Queue snapshot exceeds the ASR reservation')
            atomic(snapshot, plan)
        existing = {item['video_id']:item for item in leases(root)}
        candidates = [job for job in plan['jobs'] if job['decision'] in ELIGIBLE_DECISIONS and
                      job['video_id'] not in existing]
        candidates.sort(key=lambda job:(job['audio']['bytes'],job['video_id']))
        for job in candidates:
            if sum(item.get('status') == 'active' for item in existing.values()) >= max_ready:
                break
            required = job['audio']['bytes'] + job['metadata']['bytes'] + TRANSFER_HEADROOM
            if not room_for_inputs(root, required, max_input_bytes, min_free_bytes):
                break
            video_id = job['video_id']
            extension = Path(job['audio']['remote']).suffix
            if extension not in {'.m4a','.webm','.opus','.ogg','.mp3'}:
                raise ValueError('Unsupported native audio extension')
            audio_path = local_path(root,f'asr/input/{video_id}/{video_id}{extension}')
            metadata_path = local_path(root,f'asr/input/{video_id}/{video_id}.info.json')
            lease_path = local_path(root,f'asr/leases/{video_id}.json')
            admission_path = folder/'admissions'/f'{job["job_id"]}.json'
            now = dt.datetime.now(dt.timezone.utc)
            lease = {'schema_version':1,'video_id':video_id,'job_id':job['job_id'],'owner':'queue_audit',
              'sourceDriveID':job['audio']['drive_id'],'expected_bytes':job['audio']['bytes'],
              'expected_hashes':{key:job['audio'][key] for key in ('md5','sha256')},
              'private_path':str(audio_path),'metadata_private_path':str(metadata_path),'pid':os.getpid(),
              'lease_id':'asr-source-'+str(uuid.uuid4()),'status':'active','phase':'retrieving_metadata','frame_id':frame_id,
              'created_at':now.isoformat(),'expires_at':(now+dt.timedelta(hours=24)).isoformat(),
              'expiry_action':'hold_for_owner_review; never delete solely on PID or expiry',
              'admission_path':str(admission_path),'source_queue_snapshot':str(snapshot),
              'release_condition':'verified ASR result and provenance on Drive; preserve archived originals'}
            atomic(lease_path, lease)
            existing[video_id] = lease
            try:
                metadata = pull_verified(drive,job['metadata'],metadata_path,max_input_bytes-tree_bytes(root/'asr')-RESERVE)
                info = json.loads(metadata_path.read_text(encoding='utf-8'))
                primary = info.get('languages',{}).get('audio')
                fallback = info.get('metadata',{}).get('language')
                language = primary or fallback
                if info.get('source',{}).get('video_id') != video_id:
                    raise IngestError('metadata_identity','Metadata source identity differs')
                conflict = bool(primary and fallback and primary != fallback)
                if job['decision'] == 'eligible_native_original_english':
                    conflict = conflict or not primary or primary != job['language']['code']
                if not english(language) or conflict:
                    lease.update(status='language_hold',phase='metadata_language_conflict' if conflict else 'metadata_not_declared_english',
                                 declared_audio_language=language)
                    atomic(lease_path,lease)
                    continue
                lease.update(phase='retrieving_audio',declared_audio_language=language)
                atomic(lease_path,lease)
                audio = pull_verified(drive,job['audio'],audio_path,max_input_bytes-tree_bytes(root/'asr')-RESERVE)
                admission = {'schema_version':1,'job_id':job['job_id'],'video_id':video_id,
                  'state':'input_verified_waiting_gpu_lease','source_lease':str(lease_path),
                  'source_lease_id':lease['lease_id'],'job':job,
                  'verified_input_objects':[dict(metadata,kind='metadata'),dict(audio,kind='audio')],
                  'language':{'code':language,'basis':'verified_source_metadata.languages.audio','auditory_confirmation':False},
                  'created_at':utc_now(),'gpu_job_started':False}
                atomic(admission_path,admission)
                lease.update(phase='input_verified_waiting_gpu_lease',input_verified_at=utc_now())
                atomic(lease_path,lease)
            except Exception as exc:
                lease.update(phase='admission_failed_retained',error_class=getattr(exc,'kind',type(exc).__name__))
                atomic(lease_path,lease)
                refresh_ready(root, frame_id=frame_id)
                raise
        remaining = sum(job['decision'] in ELIGIBLE_DECISIONS and job['video_id'] not in existing for job in plan['jobs'])
        ready = refresh_ready(root, remaining, frame_id)
        ready.update(queue_snapshot=str(snapshot),counts=plan['counts'],asr_bytes=tree_bytes(root/'asr'))
        atomic(folder/'ready.json',ready)
        return ready


def claim_input(root, admission, owner):
    root = ensure_outside_git(root)
    with queue_lock(root):
        path = safe_asr(root, admission['source_lease'], 'leases')
        lease = json.loads(path.read_text(encoding='utf-8'))
        if lease.get('lease_id') != admission['source_lease_id'] or lease.get('status') != 'active' or lease.get('phase') != 'input_verified_waiting_gpu_lease':
            raise IngestError('source_lease','Input is already owned or is not ready')
        if dt.datetime.fromisoformat(lease['expires_at']) <= dt.datetime.now(dt.timezone.utc):
            raise IngestError('source_lease','Expired source lease requires owner renewal')
        lease.update(phase='processing',consumer_owner=owner,claimed_at=utc_now())
        atomic(path,lease)
        refresh_ready(root, frame_id=lease.get('frame_id'))
        return lease


def release_input(root, admission, result_receipt, drive):
    """Durable same-source result proof precedes deletion of exact owned copies."""
    root = ensure_outside_git(root)
    with queue_lock(root):
        lease_path = safe_asr(root,admission['source_lease'],'leases')
        lease = json.loads(lease_path.read_text(encoding='utf-8'))
        if lease.get('lease_id') != admission['source_lease_id'] or lease.get('video_id') != admission['video_id']:
            raise IngestError('source_lease','Source lease identity differs')
        if lease.get('sourceDriveID') != admission['job']['audio']['drive_id'] or \
                lease.get('expected_hashes') != {key:admission['job']['audio'][key] for key in ('md5','sha256')} or \
                lease.get('expected_bytes') != admission['job']['audio']['bytes']:
            raise IngestError('source_lease','Leased source proof differs from the admission')
        if not result_matches(result_receipt,admission['job'],lease['lease_id']):
            raise IngestError('result_proof','ASR result does not prove this leased source')
        durable, _, _ = read_receipts(root/'sync/asr_manifest.jsonl')
        if durable.get(admission['video_id']) != result_receipt:
            raise IngestError('result_proof','Matching ASR result receipt is not durable')
        observed = drive.stat(result_receipt['remote'])
        verify_remote(observed,result_receipt)
        if observed.get('ID') != result_receipt['drive_id']:
            raise IngestError('result_proof','ASR result Drive identity differs')
        paths = []
        if {item['kind'] for item in admission['verified_input_objects']} != {'audio','metadata'} or len(admission['verified_input_objects']) != 2:
            raise IngestError('source_lease','Exactly one audio and metadata input are required')
        for item in admission['verified_input_objects']:
            path = safe_asr(root,item['private_path'],'input/'+admission['video_id'])
            recorded = lease['private_path'] if item['kind'] == 'audio' else lease['metadata_private_path']
            if path.resolve() != Path(recorded).resolve() or proof(item['source']) != proof(admission['job'][item['kind']]):
                raise IngestError('source_lease','Input path or source proof differs from its lease')
            if path.exists():
                actual = hash_file(path)
                if any(actual[key] != item['source'][key] for key in ('bytes','md5','sha256')):
                    raise IngestError('local_changed','Input copy changed; retained for review')
            paths.append(path)
        lease.update(status='result_verified_on_drive',phase='complete_waiting_local_cleanup',
                     result_remote=result_receipt['remote'],result_drive_id=result_receipt['drive_id'],result_verified_at=utc_now())
        atomic(lease_path,lease)
        for path in paths:
            path.unlink(missing_ok=True)
        lease.update(status='released',phase='local_input_copies_deleted',released_at=utc_now())
        atomic(lease_path,lease)
        refresh_ready(root, frame_id=lease.get('frame_id'))
        return lease


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['plan','prepare','release'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--queue', '--selection', dest='queue', type=Path,
                        help='canonical mixed latest-20 selection JSON or legacy Videos-only queue CSV')
    parser.add_argument('--remote',required=True)
    parser.add_argument('--rclone',default='rclone')
    parser.add_argument('--rclone-config',type=Path)
    parser.add_argument('--model-repository',default='Systran/faster-distil-whisper-large-v3')
    parser.add_argument('--model-revision',required=True)
    parser.add_argument('--max-ready',type=int,default=3)
    parser.add_argument('--max-input-bytes',type=int,default=MAX_INPUT_BYTES)
    parser.add_argument('--admission',type=Path)
    parser.add_argument('--result-receipt',type=Path)
    parser.add_argument('--language-evidence',type=Path)
    parser.add_argument('--evidence-only',action='store_true')
    parser.add_argument('--frame-id')
    args = parser.parse_args(argv)
    ensure_outside_git(args.root)
    drive = Rclone(args.rclone,args.rclone_config,args.root/'sync/drive_ingest_cooldown.json')
    if args.command == 'release':
        result = release_input(args.root,json.loads(args.admission.read_text(encoding='utf-8')),
                               json.loads(args.result_receipt.read_text(encoding='utf-8')),drive)
    elif args.command == 'plan':
        result = build_plan(args.root,args.queue,args.remote,args.model_repository,args.model_revision,
                            language_evidence=args.language_evidence,evidence_only=args.evidence_only)
        if args.frame_id:
            snapshot = frame_folder(args.root,args.frame_id)/f'queue-{sha(encoded(result))}.json'
            if not snapshot.exists():
                if not room_for_inputs(args.root, len(encoded(result)), args.max_input_bytes, MIN_FREE_BYTES):
                    raise IngestError('storage_limit', 'Named frame plan exceeds the ASR reservation')
                atomic(snapshot,result)
            atomic(frame_folder(args.root,args.frame_id)/'plan.json',{'schema_version':1,
                'state':'planned_waiting_separate_resource_lease','queue_snapshot':str(snapshot),
                'counts':result['counts'],'frame_id':args.frame_id})
            result['queue_snapshot'] = str(snapshot)
        result = {key:value for key,value in result.items() if key != 'jobs'}
    else:
        result = prepare_inputs(args.root,args.queue,args.remote,drive,model_repository=args.model_repository,
           model_revision=args.model_revision,max_ready=args.max_ready,max_input_bytes=args.max_input_bytes,
           language_evidence=args.language_evidence,evidence_only=args.evidence_only,frame_id=args.frame_id)
    print(json.dumps(result,ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
