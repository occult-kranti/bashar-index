"""Add completed creator listings to a pinned Latest 20+ selection without refreshing established creators."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from additive_video_selection import artifact, build_selection, read_retained, apply_publication_overlay, write_artifacts, verified_counts
from collect_channel_formats import MAX_BYTES
from collect_uploads_catalog import write_json
from common import ensure_outside_git
from drive_ingest import exclusive_lock


def private(root, path):
    value = Path(path).resolve()
    if not value.is_relative_to(root):
        raise ValueError('Recording inputs must belong to the private archive')
    return value


def pinned(root, proof):
    path = private(root, proof['path'])
    if artifact(path) != proof:
        raise ValueError('Source changed since the previous selection')
    return path


def join_listings(old, prior_source, additions, root):
    groups = list(old['channels'])
    owners = {g['channel_id']: g['creator'] for g in groups}
    by_slug = {g['creator']: g['channel_id'] for g in groups}
    sources = {slug: old.get('listing_sources_by_channel', {}).get(slug, prior_source) for slug in by_slug}
    duplicates, added = [], []
    for path in additions:
        path = private(root, path)
        source = artifact(path)
        document = json.loads(path.read_bytes())
        batch = document.get('channels', [document])
        for group in batch:
            slug, channel = group['creator'], group['channel_id']
            if slug in by_slug and by_slug[slug] != channel:
                raise ValueError('Existing creator was assigned a different channel')
            if channel in owners:
                duplicates.append({'submitted_creator': slug, 'canonical_creator': owners[channel], 'channel_id': channel})
                continue
            if not group.get('listing_complete') or not group.get('public_listing_complete'):
                raise ValueError('Submitted creator needs a complete public regular Videos listing')
            base = path.parent/slug if 'channels' in document else path.parent
            with gzip.open(private(root, base/'videos.html.gz'), 'rb') as body:
                raw = body.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES or hashlib.sha256(raw).hexdigest() != group['page_sha256']:
                raise ValueError('Submitted listing does not match its captured Videos page')
            groups.append(group)
            owners[channel], by_slug[slug], sources[slug] = slug, channel, source
            added.append({'channel_dir': slug, 'channel_id': channel, 'public_regular': len(group['public_items']),
                          'page_sha256': group['page_sha256'], 'source': source})
    summary = {'channels': len(groups), 'states': dict(Counter(g['state'] for g in groups)),
               'completed_channel_listings': sum(g['listing_complete'] for g in groups),
               'completed_public_channel_listings': sum(g['public_listing_complete'] for g in groups),
               'priority_regular_videos': sum(len(g['items']) for g in groups),
               'public_regular_targets': sum(len(g['public_items']) for g in groups),
               'observed_regular_videos': sum(len(g['observed_items']) for g in groups),
               'member_only_in_literal_latest20': sum(row.get('access_status') == 'members_only' for g in groups for row in g['items'])}
    return {**old, 'channels': groups, 'observed_at': max(g['observed_at'] for g in groups), 'summary': summary,
            'listing_sources_by_channel': sources}, added, duplicates


def expand(root, base_path, base_sha256, additions, out):
    root = ensure_outside_git(root)
    base_path, out = private(root, base_path), private(root, out)
    base_proof = artifact(base_path)
    if base_proof['sha256'] != base_sha256:
        raise ValueError('Base selection hash does not match')
    previous = json.loads(base_path.read_bytes())
    original, = [s for s in previous['sources'] if s['kind'] == 'fresh_regular']
    old = json.loads(pinned(root, original['artifact']).read_bytes())
    fresh, added, duplicates = join_listings(old, original['artifact'], additions, root)
    roster = {'channels': [{'creator': g['creator'], 'channel_id': g['channel_id'], 'channel_name': g.get('channel_name')}
                           for g in fresh['channels']]}
    retained = []
    for rec in previous['sources']:
        if rec['kind'] != 'fresh_regular':
            obj = read_retained(pinned(root, rec['artifact']), rec['kind'])
            retained.append(dict(obj, observed_at=rec.get('observed_at')))
    out.mkdir(parents=True, exist_ok=True)
    with exclusive_lock(out):
        complete = out/'expansion-proof.json'
        inputs = [artifact(private(root, name)) for name in additions]
        if complete.is_file():
            proof = json.loads(complete.read_bytes())
            if proof['previous'] != base_proof or proof['input_indexes'] != inputs:
                raise ValueError('Expansion directory already records a different input')
            for key in ('fresh_index','primary_channels','selection'):
                pinned(root, proof[key])
            return proof
        grid_path, roster_path = out/'fresh-videos.json', out/'primary-channels.json'
        write_json(grid_path, fresh)
        write_json(roster_path, roster)
        selected = build_selection(retained, fresh, fresh_artifact=artifact(grid_path), primary_channels=roster)
        names = {g['creator']: g.get('channel_name') for g in fresh['channels']}
        for row in selected['rows']:
            if names[row['channel_dir']]:
                row['source_channel_name'] = names[row['channel_dir']]
        if previous.get('date_overlay'):
            pin = previous['date_overlay']
            rows = (json.loads(line) for line in pinned(root, pin).read_text(encoding='utf-8').splitlines() if line.strip())
            selected = apply_publication_overlay(selected, rows, pin)
        before = {(r['channel_dir'],r['video_id']): r for r in previous['rows']}
        after = {(r['channel_dir'],r['video_id']): r for r in selected['rows']}
        if any(key not in after or any(after[key][k] != row[k] for k in
               ('memberships','scope_memberships','expected_channel_id','tab','fresh_public_regular','access_status'))
               for key,row in before.items()):
            raise ValueError('Expansion displaced a previously indexed recording or changed its source membership')
        result = write_artifacts(selected, out/'selection', verified_counts(selected, root))
        proof = {'schema_version': 1, 'kind': 'additive_creator_roster_expansion', 'previous': base_proof,
                 'input_indexes': inputs, 'fresh_index': artifact(grid_path), 'primary_channels': artifact(roster_path),
                 'selection': result['selection'], 'added_channels': added, 'duplicates': duplicates,
                 'prior_recordings_preserved':len(before), 'cumulative_recordings': len(after),
                 'creator_count': len(roster['channels']), 'public_regular_target': fresh['summary']['public_regular_targets'],
                 'eligibility_date_or_duration_cutoff':False}
        write_json(complete, proof)
        return proof


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--base-selection', type=Path, required=True)
    ap.add_argument('--base-sha256', required=True)
    ap.add_argument('--add-index', type=Path, action='append', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    proof = expand(args.root, args.base_selection, args.base_sha256, args.add_index, args.out)
    print(json.dumps({k: proof[k] for k in ('creator_count','public_regular_target','cumulative_recordings','selection')}))


if __name__ == '__main__':
    main()
