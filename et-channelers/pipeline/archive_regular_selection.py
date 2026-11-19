"""Publish a dated regular-video index and its listing evidence to the private media archive."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_uploads_catalog import write_json
from collection_coverage import csv_bytes
from common import ensure_outside_git, utc_now
from drive_ingest import (MAX_LOCAL_BYTES, MIN_FREE_BYTES, Rclone, batch_manifest, exclusive_lock, fingerprint, hash_file,
                          local_path, managed_roots, reserved_project_growth, storage_usage, verify_remote)


NAMES = ('Latest 20+ listing evidence.zip', 'Latest 20+ videos.csv', 'Regular uploads by creator.csv')


def receipt_destination(receipt, expected):
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise ValueError('Archive receipt belongs to a different recording selection or checkpoint')
    files = receipt.get('files')
    if not isinstance(files, dict) or set(files) != set(NAMES):
        raise ValueError('Archive receipt must include all three index objects')
    parents = set()
    ids = set()
    for name in NAMES:
        proof = files[name]
        parent, _, basename = str(proof.get('remote', '')).rpartition('/')
        if (not parent or basename != name or not isinstance(proof.get('drive_id'), str) or not proof['drive_id']
                or type(proof.get('bytes')) is not int or proof['bytes'] <= 0
                or not re.fullmatch(r'[a-f0-9]{32}', str(proof.get('md5')))
                or not re.fullmatch(r'[a-f0-9]{64}', str(proof.get('sha256')))):
            raise ValueError('Invalid index object identity or checksum')
        parents.add(parent)
        ids.add(proof['drive_id'])
    if len(parents) != 1 or len(ids) != len(NAMES):
        raise ValueError('Index objects must have distinct Drive IDs in one destination')
    return parents.pop()


def clean_published(home, files, fingerprints=None):
    for name in NAMES:
        path = local_path(home, 'objects/'+name)
        if path.is_file() and ((fingerprints and fingerprint(path) == fingerprints[name])
                               or hash_file(path)['sha256'] == files[name]['sha256']):
            path.unlink()


def archive_entries(root, sweep, selection, coverage, union, evidence):
    fresh, = [s['artifact'] for s in union['sources'] if s['kind'] == 'fresh_regular']
    index_path = Path(fresh['path']).resolve()
    if not index_path.is_relative_to(sweep.resolve()) or hash_file(index_path)['sha256'] != fresh['sha256']:
        raise ValueError('The fresh index differs from its dated sweep')
    entries = [(selection/name, 'index/'+name) for name in
               ('selection.json', 'recording-index.json', 'summary.json', 'verified-counts.json')]
    entries.extend([(index_path, 'listing/fresh-regular-videos.json'), (coverage, 'coverage/receipt-coverage.json')])
    if (sweep/'sweep-status.json').is_file():
        entries.append((sweep/'sweep-status.json', 'listing/sweep-status.json'))
    if (sweep/'expansion-proof.json').is_file():
        entries.append((sweep/'expansion-proof.json', 'listing/expansion-proof.json'))
    origins = json.loads(index_path.read_bytes()).get('listing_sources_by_channel', {})
    sources = [(s['kind'], s['artifact']) for s in union['sources'] if s['kind'] != 'fresh_regular']
    if union.get('date_overlay'):
        sources.append(('date_overlay', union['date_overlay']))
    included = {index_path}
    for i, (kind, artifact) in enumerate(sources, 1):
        path = Path(artifact['path']).resolve()
        if (kind not in {'retained_mixed', 'retained_regular', 'retained_addition', 'date_overlay'}
                or not path.is_relative_to(root) or path.suffix.lower() not in {'.csv', '.json', '.jsonl'}):
            raise ValueError('Unexpected retained index input')
        if path.stat().st_size != artifact['bytes'] or hash_file(path)['sha256'] != artifact['sha256']:
            raise ValueError('A retained index input differs from the selection')
        entries.append((path, f'index/sources/{i:02d}-{kind}/{path.name}'))
        included.add(path)
    for channel in union['channels']:
        slug = channel['channel_dir']
        if not isinstance(slug, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', slug):
            raise ValueError('Expected a single creator directory')
        folder = sweep/slug
        if origins:
            origin = origins[slug]
            index = Path(origin['path']).resolve()
            if not index.is_relative_to(root):
                raise ValueError('Listing source is outside the private archive')
            if index not in included:
                if index.stat().st_size != origin['bytes'] or hash_file(index)['sha256'] != origin['sha256']:
                    raise ValueError('An original channel listing index changed')
                entries.append((index, 'listing/source-indexes/' + origin['sha256'] + '.json'))
                included.add(index)
            folder = index.parent if index.parent.name == slug and (index.parent/'videos.json').is_file() else index.parent/slug
            if not (folder/'videos.json').is_file():
                raise ValueError('The original creator listing evidence is missing')
        for name in ('videos.json', 'videos.html.gz', 'videos.attempt.json'):
            file = folder/name
            if file.is_file():
                entries.append((file, f'listing/channels/{slug}/{name}'))
        cont = folder.parent/'continuation'/(slug+'.json')
        if cont.is_file():
            entries.append((cont, 'listing/continuations/'+cont.name))
    entries.extend((f, 'publication-evidence/'+f.name) for f in evidence if f.resolve() not in included)
    if len({name for _, name in entries}) != len(entries):
        raise ValueError('The package contains duplicate member names')
    return entries


def publish(root, sweep, selection, coverage, remote, drive, evidence=()):
    root = ensure_outside_git(root)
    for location in (sweep, selection, coverage, *evidence):
        if not location.resolve().is_relative_to(root):
            raise ValueError('Index inputs must belong to the private archive')
    snapshot = json.loads(coverage.read_bytes())
    union = json.loads((selection/'selection.json').read_bytes())
    if (union.get('selection_kind') != 'additive_latest20plus_videos_v1' or
            snapshot.get('selection_basis') != 'latest20plus_public_regular' or
            snapshot['selection_sha256'] != hash_file(selection/'selection.json')['sha256']):
        raise ValueError('The coverage checkpoint and additive list must refer to the same selection')
    day = snapshot['generated_at'][:10]
    version = hashlib.sha256((snapshot['selection_sha256'] + hash_file(coverage)['sha256']).encode()).hexdigest()[:20]
    target = remote.rstrip('/') + f'/_catalog/youtube/selections/{day}/Latest 20+ videos/{version}'
    expected = {'schema_version': 1, 'label': 'Latest 20+ videos', 'coverage_at': snapshot['generated_at'],
                'scope_sha256': snapshot['priority_scope_sha256'], 'priority_recordings': snapshot['summary']['latest20_target'],
                'union_recordings': union['row_count']}
    home = root/'jobs'/f'latest-20-plus-index-{day}'/version
    home.mkdir(exist_ok=True, parents=True)
    with exclusive_lock(home):
        for directory in (home, home / hashlib.sha256(target.encode()).hexdigest()[:20]):
            receipt_path = directory/'verified-drive-files.json'
            if not receipt_path.is_file():
                home = directory
                home.mkdir(exist_ok=True)
                break
            prior = json.loads(receipt_path.read_bytes())
            if receipt_destination(prior, expected) == target:
                clean_published(directory, prior['files'])
                return prior
        else:
            raise ValueError('Archive checkpoint path belongs to a different destination')
        entries = archive_entries(root, sweep, selection, coverage, union, evidence)
        if any(not f.resolve().is_relative_to(root) for f, _ in entries):
            raise ValueError('A listing input resolves outside the private archive')
        # Deflate may slightly expand incompressible data. Include two CSVs, ZIP headers and scratch space.
        uncompressed = sum(f.stat().st_size for f, _ in entries)
        budget = uncompressed + uncompressed//100 + 1024*len(entries) + (selection/'priority.csv').stat().st_size + coverage.stat().st_size + 1_048_576
        _, managed = storage_usage(root, managed_roots(root))
        growth = reserved_project_growth(root) + budget
        if managed + growth > MAX_LOCAL_BYTES or shutil.disk_usage(root).free - growth < MIN_FREE_BYTES:
            raise ValueError('Insufficient headroom for the index package')
        work = home/'objects'
        work.mkdir(exist_ok=True)
        archive = work/'Latest 20+ listing evidence.zip'
        with ZipFile(archive, 'w', compression=ZIP_DEFLATED, compresslevel=4) as z:
            for file, name in entries:
                z.write(file, name, compress_type=ZIP_STORED if name.endswith('.gz') else ZIP_DEFLATED)
        shutil.copyfile(selection/'priority.csv', work/'Latest 20+ videos.csv')
        channel_fields = ('channel', 'channel_dir', 'target', 'audio_total', 'remaining_audio', 'with_saved_text',
                          'youtube_audio', 'publisher_only_audio', 'qualified_youtube_only_audio', 'selection_scope')
        (work/'Regular uploads by creator.csv').write_bytes(csv_bytes(
            [{key: row[key] for key in channel_fields} for row in snapshot['channels']], channel_fields))
        before = {name: fingerprint(work/name) for name in NAMES}
        proofs = {name: hash_file(work/name) for name in NAMES}
        if (root/'sync/STOP_DRIVE_UPLOAD').exists():
            raise ValueError('Drive uploads are paused; the local package is ready')
        with batch_manifest(home, NAMES) as listing:
            drive.copy_batch(work, target, listing, transfers=1)
            remote_files = drive.stat_batch(target, set(NAMES), listing)
        for name in NAMES:
            verify_remote(remote_files[name], proofs[name])
            proofs[name].update(drive_id=remote_files[name].get('ID'), remote=target+'/'+name)
        receipt = {**expected, 'verified_at': utc_now(), 'files': proofs}
        receipt_destination(receipt, expected)
        write_json(receipt_path, receipt)
        clean_published(home, proofs, before)
        return receipt


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for opt in ('root', 'sweep', 'selection', 'coverage'):
        ap.add_argument('--'+opt, required=True, type=Path)
    ap.add_argument('--date-evidence', type=Path, action='append', default=[])
    ap.add_argument('--remote', required=True)
    ap.add_argument('--rclone', default='rclone')
    args = ap.parse_args()
    drive = Rclone(args.rclone, cooldown_path=args.root/'sync/drive_ingest_cooldown.json')
    drive.UPLOAD_CHUNK = '8M'
    print(json.dumps(publish(args.root, args.sweep, args.selection, args.coverage, args.remote, drive, args.date_evidence)))


if __name__ == '__main__':
    main()
