"""Measure the inactive files charged to a batch's storage budget."""

import os
from pathlib import Path
import stat

_MOUNT_POINT = getattr(stat, 'IO_REPARSE_TAG_MOUNT_POINT', 0xA0000003)


class LinkedEntry(ValueError):
    pass


def _check_links(info):
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_reparse_tag', None) == _MOUNT_POINT:
        raise LinkedEntry('storage_link')
    return info


def _checked_stat(path):
    return _check_links(os.stat(path, follow_symlinks=False))


def measure(root, *, spool=None, excluded=(), enumeration_sizes=False):
    """Return total inactive bytes and the subset inside spool, in one walk.

    Active directories are charged by their callers' full reservations.
    By default, sample each file at stat time so a growing or retiring spool
    is measured as late as possible. For separately managed tool and checkout
    trees, enumeration_sizes takes the size and link status from the same
    directory entry. Windows already returns these fields during enumeration.
    Each call starts a new walk and checks directories again before descent.
    """
    root = Path(os.path.abspath(root))
    spool = Path(os.path.abspath(spool)) if spool is not None else None
    excluded = {os.path.normcase(os.path.abspath(path)) for path in excluded}
    spool_key = os.path.normcase(str(spool)) if spool is not None else None
    folders = [(str(root), spool is not None and root.is_relative_to(spool))]
    total = spool_total = 0
    while folders:
        folder, in_spool = folders.pop()
        try:
            if not stat.S_ISDIR(_checked_stat(folder).st_mode):
                if folder == str(root):
                    continue
                raise NotADirectoryError(folder)
            entries = os.scandir(folder)
        except FileNotFoundError:
            continue
        with entries:
            for entry in entries:
                try:
                    info = (_check_links(entry.stat(follow_symlinks=False))
                            if enumeration_sizes else _checked_stat(entry.path))
                except FileNotFoundError:
                    continue
                if stat.S_ISDIR(info.st_mode):
                    key = os.path.normcase(entry.path)
                    if key not in excluded:
                        folders.append((entry.path, in_spool or key == spool_key))
                else:
                    total += info.st_size
                    if in_spool:
                        spool_total += info.st_size
    return total, spool_total


def project_usage(private_root, other_roots=()):
    """Return private and total project bytes, counting nested checkouts once."""
    private = Path(os.path.abspath(private_root))
    distinct = {Path(os.path.abspath(path)) for path in other_roots}
    external = [path for path in distinct if not path.is_relative_to(private)]
    outermost = [path for path in external if not any(parent in external for parent in path.parents)]
    private_bytes = measure(private)[0]
    external_bytes = sum(measure(path, excluded=(private,), enumeration_sizes=True)[0] for path in outermost)
    return private_bytes, private_bytes + external_bytes
