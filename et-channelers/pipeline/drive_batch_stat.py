"""One bounded readback for named Google Drive objects, including partial groups."""
import json


def read_batch(drive, remote, paths, manifest, *, allow_missing, error):
    result = drive.execute(['lsjson', remote, '--recursive', '--files-only', '--hash-type', 'MD5',
                            '--no-modtime', '--no-mimetype', '--files-from-raw', str(manifest),
                            '--no-traverse', '--checkers', '2', *drive.RETRY_FLAGS], 600,
                           'bounded batch metadata read')
    try:
        entries = json.loads(result.stdout)
        if not isinstance(entries, list):
            raise ValueError
        found, identities = {}, set()
        for entry in entries:
            path, identity = entry.get('Path'), entry.get('ID')
            if path not in paths or path in found or (identity and identity in identities):
                raise ValueError
            found[path] = entry
            if identity:
                identities.add(identity)
        if not allow_missing and set(found) != set(paths):
            raise ValueError
        return found
    except (ValueError, AttributeError, TypeError) as exc:
        raise error('drive_verify', 'Batch metadata is missing, ambiguous, or invalid; local pairs retained') from exc
