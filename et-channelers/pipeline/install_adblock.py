#!/usr/bin/env python3
"""Install the pinned, unmodified official uBO Lite package outside the repo."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import stat
import urllib.request
import uuid
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

VERSION = '2026.1116.1650'
ARCHIVE_BYTES = 9_099_013
ARCHIVE_SHA256 = '67e084b34470c51c08fa9314b118b8cb73df3a72e90c6a3b536d041c92e61bbc'
SOURCE = f'https://github.com/uBlockOrigin/uBOL-home/releases/download/{VERSION}/uBOLite_{VERSION}.chromium.zip'
MAX_EXPANDED = 64_000_000
MAX_ENTRIES = 4096


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1_048_576), b''):
            result.update(block)
    return result.hexdigest()


def checked_entries(archive):
    entries = archive.infolist()
    if len(entries) > MAX_ENTRIES or sum(item.file_size for item in entries) > MAX_EXPANDED:
        raise ValueError('extension_expansion_budget')
    seen = set()
    for item in entries:
        name = PurePosixPath(item.filename)
        if (not item.filename or '\\' in item.filename or name.is_absolute() or
                any(part in {'.', '..'} or ':' in part or part.endswith(('.', ' ')) or
                    PureWindowsPath(part).is_reserved() for part in name.parts) or
                stat.S_ISLNK(item.external_attr >> 16)):
            raise ValueError('unsafe_extension_entry')
        key = name.as_posix().casefold()
        if key in seen:
            raise ValueError('duplicate_extension_entry')
        seen.add(key)
    if 'manifest.json' not in seen:
        raise ValueError('extension_manifest_missing')
    return entries


def verify_archive(path):
    if path.stat().st_size != ARCHIVE_BYTES or sha256(path) != ARCHIVE_SHA256:
        raise ValueError('official_archive_hash_mismatch')


def download_archive(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + '.part')
    if partial.exists():
        raise ValueError('partial_archive_already_exists')
    with urllib.request.urlopen(SOURCE, timeout=60) as response, partial.open('xb') as output:
        received = 0
        while block := response.read(1_048_576):
            received += len(block)
            if received > ARCHIVE_BYTES:
                raise ValueError('archive_size_limit')
            output.write(block)
    verify_archive(partial)
    partial.rename(path)


def install(archive, tools_root, browser_major):
    archive, tools_root = Path(archive).resolve(), Path(tools_root).resolve()
    verify_archive(archive)
    parent = tools_root / 'extensions' / 'ubol'
    destination = parent / VERSION
    receipt_path = parent / (VERSION + '.receipt.json')
    if destination.exists():
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        if receipt.get('archive_sha256') != ARCHIVE_SHA256 or receipt.get('version') != VERSION:
            raise ValueError('installed_extension_receipt_mismatch')
        for item in receipt['files']:
            file = destination / item['path']
            if file.stat().st_size != item['bytes'] or sha256(file) != item['sha256']:
                raise ValueError('installed_extension_changed')
        return receipt
    parent.mkdir(parents=True, exist_ok=True)
    staging = parent / (VERSION + '.installing-' + uuid.uuid4().hex)
    staging.mkdir()
    files = []
    with zipfile.ZipFile(archive) as bundle:
        for item in checked_entries(bundle):
            target = staging.joinpath(*PurePosixPath(item.filename).parts)
            if not target.resolve().is_relative_to(staging.resolve()):
                raise ValueError('extension_path_escape')
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(item) as source, target.open('xb') as output:
                shutil.copyfileobj(source, output, length=1_048_576)
            if target.stat().st_size != item.file_size:
                raise ValueError('extension_entry_size_mismatch')
            files.append({'path': target.relative_to(staging).as_posix(), 'bytes': item.file_size,
                          'sha256': sha256(target)})
    manifest = json.loads((staging / 'manifest.json').read_text(encoding='utf-8'))
    minimum_major = int(manifest['minimum_chrome_version'].split('.')[0])
    if (manifest.get('manifest_version') != 3 or manifest.get('version') != VERSION or
            manifest.get('author') != 'Raymond Hill' or browser_major < minimum_major):
        raise ValueError('incompatible_extension_manifest')
    staging.rename(destination)
    receipt = {'schema_version': 1, 'version': VERSION, 'source_url': SOURCE,
               'archive_bytes': ARCHIVE_BYTES, 'archive_sha256': ARCHIVE_SHA256,
               'installed_at': dt.datetime.now(dt.timezone.utc).isoformat(),
               'install_path': str(destination), 'manifest_version': 3,
               'manifest_sha256': sha256(destination / 'manifest.json'),
               'minimum_browser_major': minimum_major, 'checked_browser_major': browser_major,
               'expanded_bytes': sum(item['bytes'] for item in files),
               'enabled_rulesets': [item['id'] for item in manifest['declarative_net_request']['rule_resources'] if item['enabled']],
               'permissions': manifest.get('permissions', []),
               'host_permissions': manifest.get('host_permissions', []),
               'package_modified': False, 'files': files}
    temporary = receipt_path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    temporary.replace(receipt_path)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tools-root', type=Path, default=Path.home() / 'et-channelers-tools')
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--browser-major', type=int, required=True)
    parser.add_argument('--download', action='store_true', help='Fetch the pinned official package only if absent')
    args = parser.parse_args()
    archive = args.archive or args.tools_root / 'extensions' / 'archives' / f'uBOLite_{VERSION}.chromium.zip'
    if not archive.exists() and args.download:
        download_archive(archive)
    receipt = install(archive, args.tools_root, args.browser_major)
    print(json.dumps({key: receipt[key] for key in ('version', 'archive_bytes', 'archive_sha256',
                                                  'expanded_bytes', 'manifest_sha256', 'enabled_rulesets', 'package_modified')}))


if __name__ == '__main__':
    main()
