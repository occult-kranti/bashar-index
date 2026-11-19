"""Fresh, exact-selected-row audio receipts before an owner's new Source work.

This supplies a per-item skip, never a provider stop or permission to fetch.
Construct inside the existing collector owner and share its journal mutex.
"""
from __future__ import annotations

import errno
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import threading

JOURNALS=('publisher_mirror_manifest.jsonl','drive_ingest_manifest.jsonl',
          'progressive_audio_extracts_manifest.jsonl','publisher_variant_manifest.jsonl')


class ReceiptSnapshotChanged(ValueError):
    pass


def _stamp(path):
    if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
        raise ValueError('linked_receipt_journal_rejected')
    try:value=path.stat()
    except FileNotFoundError as error:
        if error.errno!=errno.ENOENT or error.filename is not None and Path(error.filename)!=path:raise
        return None
    return (value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns)


def _native_file(value):
    return (isinstance(value,dict) and type(value.get('bytes')) is int and value['bytes']>0
        and isinstance(value.get('drive_id'),str) and bool(value['drive_id'])
        and re.fullmatch(r'[a-f0-9]{32}',str(value.get('md5'))) is not None
        and re.fullmatch(r'[a-f0-9]{64}',str(value.get('sha256'))) is not None)


def _status_module():
    if __package__:
        from . import ingestion_status
    else:
        import ingestion_status
    return ingestion_status


class ExactOwnerReceiptGate:
    """Cache parsed unchanged journals; recheck all identities under receipt_lock.

    Complete append races get at most three local resamples. Persistent partial,
    malformed or unreadable inventories raise; no stale/empty fallback exists.
    Supplemental text never suppresses audio. No Drive or Source calls occur.
    """
    def __init__(self,root,remote,*,receipt_lock,status=None,selected_ids=None):
        self.root=Path(root).resolve();self.remote=remote;self.lock=receipt_lock
        if not isinstance(remote,str) or ':' not in remote or remote.endswith('/'):
            raise ValueError('receipt_gate_remote_required')
        self.status=status;self._files={};self._decisions={}
        self._index_lock=threading.RLock()
        self.selected_ids=frozenset(selected_ids) if selected_ids is not None else None
        self.journal_parses=0

    def _snapshot(self):
        sync=self.root/'sync'
        if sync.resolve()!=sync.absolute():raise ValueError('linked_receipt_directory_rejected')
        return tuple((name,_stamp(self.root/'sync'/name)) for name in JOURNALS)

    def _index(self,name,stamp):
        # This parse mutex is deliberately distinct from the owner's journal
        # mutex. Slow changed-file indexing cannot block publication appends,
        # and an unchanged ready decision never waits for this parse mutex.
        with self._index_lock:
            saved=self._files.get(name)
            if saved is not None and saved[0]==stamp:return saved[1]
            if stamp is None:return None
            path=self.root/'sync'/name;rows={};digest=hashlib.sha256();size=0
            try:
                with path.open('rb') as stream:
                    for number,line in enumerate(stream):
                        size+=len(line);digest.update(line)
                        if not line.endswith(b'\n'):
                            raise ReceiptSnapshotChanged('incomplete_receipt_snapshot')
                        try:
                            record=json.loads(line.decode('utf-8-sig' if number==0 else 'utf-8'))
                        except (ValueError,UnicodeError):
                            if _stamp(path)!=stamp:raise ReceiptSnapshotChanged('receipt_replaced_during_parse')
                            raise
                        if not isinstance(record,dict):raise ValueError('receipt_row_object_required')
                        video=record.get('video_id',record.get('associated_youtube_id'))
                        if not isinstance(video,str) or (name!=JOURNALS[0] and self.selected_ids is not None and video not in self.selected_ids):
                            continue
                        # Store only receipt fields needed by this frame. The
                        # strict publisher/qualified readers validate originals.
                        fields=('video_id','channel_dir','tab','status','path','remote','bytes','md5','sha256',
                                'drive_id','changes_selected_audio_count','canonical_associated_youtube_id')
                        kept={k:record[k] for k in fields if k in record}
                        kept['_receipt_line_offset']=size-len(line)
                        kept['_receipt_line_bytes']=len(line)
                        if name==JOURNALS[1]:
                            metadata=record.get('metadata')
                            kept['metadata']=({k:metadata[k] for k in fields if k in metadata}
                                if isinstance(metadata,dict) else metadata)
                        rows.setdefault(video,[]).append((kept,hashlib.sha256(line.rstrip(b'\r\n')).hexdigest()))
            except FileNotFoundError:
                if _stamp(path)!=stamp:raise ReceiptSnapshotChanged('receipt_changed_during_open')
                raise
            if _stamp(path)!=stamp or size!=stamp[2]:
                raise ReceiptSnapshotChanged('receipt_changed_during_scan')
            index={'rows':rows,'sha256':digest.hexdigest(),'bytes':size,'stamp':stamp}
            self._files[name]=(stamp,index);self.journal_parses+=1
            return index

    def _records(self,name,index,ids):
        """Seek only matched complete rows; include a shared publisher's anchor."""
        wanted=set(ids)
        if name==JOURNALS[0]:
            wanted.update(record['canonical_associated_youtube_id'] for video in ids
                for record,_ in index['rows'].get(video,[])
                if isinstance(record.get('canonical_associated_youtube_id'),str))
        entries=[(record,digest) for video in wanted for record,digest in index['rows'].get(video,[])
            if record.get('changes_selected_audio_count') is not False]
        entries.sort(key=lambda value:value[0]['_receipt_line_offset'])
        path=self.root/'sync'/name;values=[]
        if _stamp(path)!=index['stamp']:raise ReceiptSnapshotChanged('receipt_changed_before_matched_read')
        with path.open('rb') as stream:
            for record,digest in entries:
                stream.seek(record['_receipt_line_offset']);line=stream.readline()
                if (len(line)!=record['_receipt_line_bytes'] or not line.endswith(b'\n')
                        or hashlib.sha256(line.rstrip(b'\r\n')).hexdigest()!=digest):
                    raise ReceiptSnapshotChanged('matched_receipt_line_changed')
                try:
                    value=json.loads(line.decode('utf-8-sig' if record['_receipt_line_offset']==0 else 'utf-8'))
                except (ValueError,UnicodeError):
                    if _stamp(path)!=index['stamp']:raise ReceiptSnapshotChanged('receipt_replaced_during_matched_read')
                    raise
                values.append(value)
        if _stamp(path)!=index['stamp']:raise ReceiptSnapshotChanged('receipt_changed_after_matched_read')
        return values

    def verified_audio(self,row):
        video=row.get('video_id');channel=row.get('channel_dir');tab=row.get('tab')
        if (not isinstance(video,str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}',video)
                or not isinstance(channel,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}',channel)
                or tab not in {'videos','streams','shorts','unknown',''}):
            raise ValueError('exact_receipt_selection_required')
        if self.selected_ids is not None and video not in self.selected_ids:
            raise ValueError('receipt_gate_foreign_selection')
        for attempt in range(3):
            with self.lock:
                before=self._snapshot();key=(video,channel,tab)
                saved=self._decisions.get(key)
                if saved is not None and all(value in before for value in saved['dependencies']):
                    return deepcopy(saved['value'])
            try:
                indices=((name,self._index(name,stamp)) for name,stamp in before)
                result=self._validate(row,indices)
                dependencies=(tuple(value for value in before if value[0]==result['journal'])
                    if result is not None else before)
                with self.lock:
                    current=self._snapshot()
                    if not all(value in current for value in dependencies):
                        raise ReceiptSnapshotChanged('receipt_changed_during_validation')
                    # A proven positive depends on its own complete audio
                    # journal, not unrelated sibling publication churn.
                    self._decisions={k:v for k,v in self._decisions.items()
                        if all(value in current for value in v['dependencies'])}
                    self._decisions[key]={'dependencies':dependencies,'value':result}
                    return deepcopy(result)
            except ReceiptSnapshotChanged:
                if attempt==2:raise
                continue
        raise AssertionError('bounded_receipt_sampling_exhausted')

    def _validate(self,row,indices):
        video=row['video_id'];status=None;targets={video}
        for name,index in indices:
            if index is None:continue
            matches=[(record,digest) for record,digest in index['rows'].get(video,[])
                if record.get('changes_selected_audio_count') is not False]
            if not matches:continue
            status=status or self.status or _status_module()
            if name==JOURNALS[0]:
                accepted=video in status.publisher_mirror_evidence(self.root,targets,self.remote,target_rows=[row],
                    source_records=self._records(name,index,targets),source_asr_records=())[0]
                kind='publisher_audio'
            elif name==JOURNALS[1]:
                record=matches[-1][0];metadata=record.get('metadata') or {}
                accepted=(record.get('channel_dir')==row['channel_dir']
                    and record.get('tab') in (None,'',row['tab']) and _native_file(record) and _native_file(metadata)
                    and record['drive_id']!=metadata['drive_id'] and status.proof(status.receipt_complete,record,row,self.remote))
                kind='youtube_native'
            elif name==JOURNALS[2]:
                accepted=video in status.qualified_edition_coverage(self.root,targets,self.remote,target_rows=[row],
                    records=self._records(name,index,targets))
                kind='youtube_qualified_edition'
            else:
                accepted=row['tab']=='videos' and video in status.publisher_coverage(self.root,targets,self.remote,target_rows=[row],
                    record_sets={name:self._records(name,index,targets)})[2]
                kind='publisher_audio_variant'
            if accepted:
                return {'schema_version':1,'video_id':video,'channel_dir':row['channel_dir'],'tab':row['tab'],
                    'source_kind':kind,'remote_root':self.remote,'journal':name,'journal_bytes':index['bytes'],
                    'journal_sha256':index['sha256'],'candidate_record_sha256s':[digest for _,digest in matches],
                    'existing_verified_audio':True,'new_Source_requests':0,'new_Drive_requests':0}
        return None
