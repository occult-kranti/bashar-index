"""Refresh the regular Videos tab of each primary channel once per dated run."""
from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_channel_formats import MAX_BYTES, observe
from collect_uploads_catalog import manifest, reject_redirect, write_json
from common import RateLimiter, ensure_outside_git, utc_now
from drive_ingest import MAX_LOCAL_BYTES, MIN_FREE_BYTES, managed_roots, reserved_project_growth, storage_usage
from feeds import get_bytes
from fetch_publisher_text import Robots


def refresh(root, channels, output, workers=3):
    """Store small listing pages separately from media. Reuse saved responses on restart."""
    root, output = ensure_outside_git(root), ensure_outside_git(output)
    if not output.is_relative_to(root) or not 1 <= workers <= 6:
        raise ValueError('Expected a dated private output directory and one to six metadata workers')
    output.mkdir(parents=True, exist_ok=True)
    # Each outstanding response can create at most one gzip of a bounded HTML body and a small index.
    per_request = MAX_BYTES + 256_000
    _, used = storage_usage(root, managed_roots(root))
    reserved = reserved_project_growth(root)
    room = min(MAX_LOCAL_BYTES - used - reserved, shutil.disk_usage(root).free - MIN_FREE_BYTES - reserved)
    room = min(room, 96_000_000)
    limiter = RateLimiter(1, jitter=0)
    def robots_get(url, **options):
        limiter.wait()
        return get_bytes(url, **options, before_redirect=reject_redirect)
    robots = Robots(get=robots_get)
    roster = [(name, channel) for name, channel in channels if not (output/name/'videos.json').exists()]
    queue = iter(roster)
    pending = {}
    stopped = ''
    consumed = 0
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while True:
            while not stopped and len(pending) < workers:
                if consumed + (len(pending) + 1) * per_request > room:
                    if not pending:
                        stopped = 'storage_reserve'
                    break
                item = next(queue, None)
                if item is None:
                    break
                name, channel = item
                future = pool.submit(observe, output/name, name, channel, 'videos', robots, limiter)
                pending[future] = name
            if not pending:
                break
            finished, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in finished:
                name = pending.pop(future)
                try:
                    record = future.result()
                except (OSError, ValueError) as exc:
                    print(f'{name}: {type(exc).__name__}: {exc}', file=sys.stderr, flush=True)
                    continue
                completed += 1
                consumed += sum(path.stat().st_size for path in (output/name).iterdir() if path.is_file())
                if record['state'] == 'provider_pause':
                    stopped = 'provider_pause'
                if completed % 10 == 0 or stopped:
                    print(f'{completed} channel pages processed, {consumed:,} private bytes', flush=True)
    result = {'observed_at': utc_now(), 'scheduled_channels': len(roster), 'completed_requests': completed,
              'new_listing_bytes_including_metadata': consumed, 'stop': stopped or None,
              'workers': workers, 'shared_request_start_interval_s': 1}
    write_json(output/'sweep-status.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('fetch', 'index'))
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--channels', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--index-name', help='versioned JSON filename for a reparse')
    parser.add_argument('--per-channel', type=int, choices=(20, 50), default=20, help='number of public Videos-tab uploads in the index')
    args = parser.parse_args(argv)
    channels = manifest(args.channels)
    if args.command == 'fetch':
        print(json.dumps(refresh(args.root, channels, args.out, args.workers)), flush=True)
    else:
        from regular_video_index import assemble
        name = args.index_name or ('fresh-videos.json' if args.per_channel == 20 else 'fresh-videos-50.json')
        print(json.dumps(assemble(channels, args.out, name, per_channel=args.per_channel)), flush=True)


if __name__ == '__main__':
    main()
