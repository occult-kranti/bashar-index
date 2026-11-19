"""Publish ready, locally validated native audio and metadata through one Drive uploader."""
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
import os
import tempfile

try:
    from . import drive_ingest as storage, grouped_publication as grouped
except ImportError:
    import drive_ingest as storage
    import grouped_publication as grouped


@dataclass(frozen=True)
class Member:
    sink: object
    record: dict

    @property
    def bytes(self):
        return self.record['bytes'] + self.record['metadata']['bytes']


@dataclass(frozen=True)
class VerifiedPair:
    member: Member
    remote_proofs: dict
    identities: dict

    def consume(self, sink, record):
        if self.member.sink is not sink or record != self.member.record or sink.job_id not in sink.c.publishing:
            raise ValueError('native_group_pair_binding')
        for role, obj in (('audio', record), ('metadata', record['metadata'])):
            path = storage.local_path(sink.c.root, obj['path'])
            if storage.fingerprint(path) != self.identities[role]:
                raise ValueError('native_group_original_changed')
            storage.verify_remote(self.remote_proofs[role],obj)
        ids = [self.remote_proofs[role].get('ID') for role in ('audio','metadata')]
        if any(not isinstance(i,str) or not i for i in ids) or len(set(ids)) != 2:
            raise ValueError('native_group_pair_remote_identity')
        return self.remote_proofs, self.identities


def _reason(error):
    return getattr(error,'kind',None) or getattr(error,'code',None) or type(error).__name__


class _DriveView:
    """Keep the pinned collector's interface and distinguish recoverable partial copies."""
    def __init__(self, drive):
        self.drive=drive

    def __getattr__(self,name):
        return getattr(self.drive,name)

    def copy_batch(self,*args,**kwargs):
        try:
            return self.drive.copy_batch(*args,**kwargs)
        except Exception as error:
            # A version-isolated collector can load its IngestError class under another module name.
            # Adopt its recorded classification; an unknown or global failure remains an immediate hold.
            kind=getattr(error,'kind',None)
            if not isinstance(error,storage.IngestError) and isinstance(kind,str) and kind in {
                        'drive_conflict','drive_network','drive_server','drive_not_found'}:
                raise storage.IngestError(kind,'The original Drive copy accepted only part of this group') from error
            raise


@contextmanager
def claim(member):
    sink = member.sink
    with sink.c.lock:
        sink.c.guard()
        state = sink.state()
        if (state['state'] not in ('local_validated','publishing') or state['record'] != member.record
                or sink.job_id in sink.c.publishing):
            raise ValueError('native_group_not_ready')
        sink.c.publishing.add(sink.job_id)
    try:
        yield
    finally:
        with sink.c.lock:
            sink.c.publishing.discard(sink.job_id)


@contextmanager
def links(member, files, *, cleanup_errors=None):
    """Use same-filesystem aliases only, then verify against the closed Sink byte hashes.

    Linking can change inode ctime. Take the trusted identity only after linking
    and a full SHA/MD5 check. A local filesystem without hardlinks cannot stage
    a group. The original Sink pair remains usable by its single-item path.
    """
    sink, record = member.sink, member.record
    roles = {}
    created = []
    try:
        for role, obj in (('audio',record),('metadata',record['metadata'])):
            original = storage.local_path(sink.c.root,obj['path'])
            relative = storage.remote_relative(sink.c.remote,obj['remote'])
            if (original.parent != sink.folder.resolve() or not original.is_file() or original.is_symlink()
                    or not isinstance(obj.get('sha256'),str)):
                raise ValueError('native_group_source_scope')
            target = storage.local_path(files,relative)
            target.parent.mkdir(parents=True,exist_ok=True)
            os.link(original,target)
            identity=target.stat()
            created.append((target,original,identity.st_dev,identity.st_ino))
            current = storage.validate_local(target,obj)
            if not target.samefile(original) or storage.fingerprint(original) != current:
                raise ValueError('native_group_hardlink_identity')
            roles[role] = grouped.StagedObject(relative,obj,current)
        yield roles
    finally:
        for target,original,device,inode in reversed(created):
            # The existing Sink may have removed its own name after writing a verified receipt.
            # Only remove aliases in this newly created, bounded staging tree.
            try:
                current=target.lstat()
                if (target.is_symlink() or (current.st_dev,current.st_ino)!=(device,inode)
                        or original.exists() and not target.samefile(original)):
                    raise ValueError('native_group_alias_changed')
                target.unlink()
            except FileNotFoundError:
                continue
            except (ValueError,OSError) as error:
                if cleanup_errors is None:
                    raise
                cleanup_errors[record['video_id']]=_reason(error)


def _flush(callbacks, *, once, finish, drive, guard, staging, remote):
    if len(callbacks) == 1:
        return [once(*callbacks[0])]
    results, cleanup_errors = {}, {}
    control = None
    try:
        guard()
        staging.mkdir(exist_ok=True)
        control = Path(tempfile.mkdtemp(prefix='flush-',dir=staging))
        with ExitStack() as stack:
            files = control/'files'
            files.mkdir()
            pairs = []
            for item, acquired, trace in callbacks:
                owner = acquired.value
                member = owner.group_member
                try:
                    stack.enter_context(claim(member))
                    objects = stack.enter_context(links(member,files,cleanup_errors=cleanup_errors))
                except Exception as error:
                    results[item.key] = owner(trace,group_error=_reason(error))
                    continue
                def commit(proofs, *, item=item, member=member, owner=owner, objects=objects, trace=trace):
                    verified = VerifiedPair(member,proofs,{role:obj.fingerprint for role,obj in objects.items()})
                    result = owner(trace,group_evidence=verified)
                    results[item.key] = result
                    if result['status'] not in ('paired_verified_deleted','paired_verified_cleanup_held'):
                        raise ValueError('native_canonical_receipt_missing')
                    return result
                pairs.append(grouped.StagedPair(item.key,objects['audio'],objects['metadata'],commit,trace.mark))
            if pairs:
                bykey = {item.key:(acquired.value,trace) for item,acquired,trace in callbacks}
                outcomes = grouped.publish_staged_pairs(pairs,files_root=files,control_root=control,
                               remote=remote,drive=_DriveView(drive),guard=guard,transfers=3)
                for outcome in outcomes:
                    if outcome.key not in results:
                        owner, trace = bykey[outcome.key]
                        results[outcome.key] = owner(trace,group_error=outcome.reason or 'native_group_unverified')
    except Exception as error:
        for item,acquired,trace in callbacks:
            if item.key not in results:
                results[item.key] = acquired.value(trace,group_error=_reason(error))
    finally:
        # Remove empty directories only. Keep foreign or changed files for reconciliation.
        if control is not None:
            for path, _, _ in os.walk(control,topdown=False,followlinks=False):
                try:
                    Path(path).rmdir()
                except OSError:
                    pass
            if control.exists() and not cleanup_errors:
                cleanup_errors.update((item.key,'native_group_unexpected_staging_file') for item,_,_ in callbacks)
    for key,error in cleanup_errors.items():
        result=results[key]
        result.update(group_staging_cleanup_held=True,group_cleanup_error=error,known_byte_envelope_retained=True)
        if result['status']=='paired_verified_deleted':
            result['status']='paired_verified_cleanup_held'
    return [finish(item,results[item.key]) for item,_,_ in callbacks]


def publish_callbacks(callbacks, *, once, finish, drive, guard, staging, remote, headroom):
    """Flush only already-ready pairs within the caller's existing staging envelope."""
    callbacks = tuple(callbacks)
    if type(headroom) is not int or headroom <= 0 or not 1 <= len(callbacks) <= 6:
        raise ValueError('invalid_native_publication_scope')
    parts, current, amount = [], [], 0
    for entry in callbacks:
        size = entry[1].value.group_member.bytes
        if type(size) is not int or size <= 0:
            raise ValueError('invalid_native_publication_extent')
        if current and amount+size > headroom:
            parts.append(current)
            current,amount = [],0
        current.append(entry)
        amount += size
    if current:
        parts.append(current)
    results = []
    stopped = False
    for part in parts:
        if stopped:
            for item,acquired,trace in part:
                result = acquired.value(trace,group_error='native_group_previous_flush_held')
                results.append(finish(item,result))
            continue
        batch = _flush(part,once=once,finish=finish,drive=drive,guard=guard,staging=Path(staging),remote=remote)
        results.extend(batch)
        stopped = any(not result.verified or result.proof.get('status') == 'paired_verified_cleanup_held' for result in batch)
    return results
