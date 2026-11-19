"""Publish immutable, already-staged audio/metadata pairs through one Drive owner.

The caller owns the source-independent staging checkpoint and each pair's durable
receipt and cleanup. This module does not acquire media or remove local files.
"""
from dataclasses import dataclass
from inspect import signature
from pathlib import Path
import re
from typing import Callable

try:
    from . import drive_ingest as storage
    from .drive_batch_stat import read_batch
except ImportError:
    import drive_ingest as storage
    from drive_batch_stat import read_batch


@dataclass(frozen=True)
class StagedObject:
    relative: str
    proof: dict
    fingerprint: tuple | None = None


@dataclass(frozen=True)
class StagedPair:
    key: str
    audio: StagedObject
    metadata: StagedObject
    commit: Callable
    trace: Callable | None = None


@dataclass(frozen=True)
class PairPublication:
    key: str
    state: str
    receipt: object = None
    reason: str | None = None


def _reason(error):
    return getattr(error, 'kind', None) or getattr(error, 'code', None) or type(error).__name__


def _trace(pairs, phase):
    for pair in pairs:
        if pair.trace is not None:
            pair.trace(phase)


def _stat_available(drive, remote, paths, manifest):
    if 'allow_missing' in signature(drive.stat_batch).parameters:
        return drive.stat_batch(remote, paths, manifest, allow_missing=True)
    if hasattr(drive, 'execute') and hasattr(drive, 'RETRY_FLAGS'):
        # Older pinned collectors expose the same command runner and cooldown.
        return read_batch(drive, remote, paths, manifest, allow_missing=True, error=storage.IngestError)
    return drive.stat_batch(remote, paths, manifest)


def _validate_local(files, obj):
    relative = storage.remote_relative('stage:', 'stage:' + obj.relative)
    path = storage.local_path(files, relative)
    proof = obj.proof
    if (not path.is_file() or type(proof.get('bytes')) is not int or proof['bytes'] <= 0 or
            path.stat().st_size != proof['bytes'] or not re.fullmatch('[a-f0-9]{32}', str(proof.get('md5'))) or
            not re.fullmatch('[a-f0-9]{64}', str(proof.get('sha256')))):
        raise storage.IngestError('local_changed', 'A staged object does not match its accepted extent or proof')
    fingerprint = storage.validate_local(path, proof, obj.fingerprint)
    return path, fingerprint


def publish_staged_pairs(pairs, *, files_root, control_root, remote, drive, guard, transfers=3):
    """Return an outcome for each of one to six pairs. Use one bounded copy/stat.

    A partial copy can still produce independently verifiable pairs. A Drive
    refusal stops new I/O. On a later call the same staging checkpoints and
    rclone's immutable checksum comparison allow only remaining files to transfer.
    ``commit`` receives the two verified, unmodified rclone stat records by role.
    It must persist a per-item receipt before its existing owned cleanup.
    """
    pairs = tuple(pairs)
    keys = [pair.key for pair in pairs]
    relatives = [obj.relative for pair in pairs for obj in (pair.audio, pair.metadata)]
    if (not 1 <= len(pairs) <= 6 or len(keys) != len(set(keys)) or len(relatives) != len(set(relatives)) or
            type(transfers) is not int or not 1 <= transfers <= 3 or not callable(guard)):
        raise ValueError('Expected one to six distinct staged pairs and one to three file transfers')
    files = Path(files_root).resolve()
    eligible, completed, identities = [], {}, {}
    for pair in pairs:
        try:
            if not callable(pair.commit):
                raise ValueError('Receipt callback required')
            identities[pair.key] = [_validate_local(files, obj) for obj in (pair.audio, pair.metadata)]
        except (OSError, ValueError, storage.IngestError) as error:
            completed[pair.key] = PairPublication(pair.key, 'retained', reason=_reason(error))
        else:
            eligible.append(pair)
    paths = [obj.relative for pair in eligible for obj in (pair.audio, pair.metadata)]
    copy_error = None
    if paths:
        try:
            guard()
            with storage.batch_manifest(Path(control_root), paths) as manifest:
                _trace(eligible, 'copy_start')
                try:
                    drive.copy_batch(files, remote, manifest, transfers=min(transfers, len(paths)))
                except storage.IngestError as error:
                    if error.kind not in {'drive_conflict', 'drive_network', 'drive_server', 'drive_not_found'}:
                        raise
                    copy_error = error.kind
                finally:
                    _trace(eligible, 'copy_finish')
                guard()
                _trace(eligible, 'stat_start')
                try:
                    observed = _stat_available(drive, remote, set(paths), manifest)
                finally:
                    _trace(eligible, 'stat_finish')
            if not isinstance(observed, dict) or not set(observed).issubset(paths):
                raise storage.IngestError('drive_verify', 'Unexpected objects in the bounded Drive read')
            ids = [entry.get('ID') for entry in observed.values()]
            if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
                raise storage.IngestError('drive_verify', 'Missing or duplicate Drive object identities')
        except Exception as error:
            for pair in eligible:
                completed[pair.key] = PairPublication(pair.key, 'retained', reason=_reason(error))
            return [completed[key] for key in keys]

    for pair in eligible:
        try:
            proofs = {}
            for role, obj, (path, fingerprint) in zip(('audio','metadata'), (pair.audio, pair.metadata), identities[pair.key]):
                if obj.relative not in observed:
                    raise storage.IngestError(copy_error or 'drive_missing', 'The pair is incomplete on Drive')
                if storage.fingerprint(path) != fingerprint:
                    raise storage.IngestError('local_changed', 'A staged file changed during publication')
                storage.verify_remote(observed[obj.relative], obj.proof)
                proofs[role] = observed[obj.relative]
            guard()
            receipt = pair.commit(proofs)
            if receipt is None:
                raise ValueError('A durable per-item receipt is required')
            completed[pair.key] = PairPublication(pair.key, 'verified', receipt)
        except Exception as error:
            receipt = getattr(error, 'record', None)
            completed[pair.key] = PairPublication(pair.key, 'verified_cleanup_held' if receipt is not None else 'retained',
                                                  receipt, _reason(error))
    return [completed[key] for key in keys]


def drain_ready(ready, publish_group, publish_one, *, max_pairs=6):
    """Consume only already-ready items, without waiting for another download."""
    if type(max_pairs) is not int or not 1 <= max_pairs <= 6:
        raise ValueError('Invalid publication flush size')
    count = min(len(ready), max_pairs)
    if count == 1:
        return [publish_one(ready.popleft())]
    if count:
        return publish_group([ready.popleft() for _ in range(count)])
    return []
