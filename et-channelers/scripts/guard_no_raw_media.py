#!/usr/bin/env python3
"""Fail if the repository holds raw media, caption or transcript dumps, or secrets. Standard library only.

    python3 et-channelers/scripts/guard_no_raw_media.py              # et-channelers/: tracked + untracked, not ignored
    python3 et-channelers/scripts/guard_no_raw_media.py --all        # the whole repository
    python3 et-channelers/scripts/guard_no_raw_media.py --staged     # only what is staged (for a pre-commit hook)
    python3 et-channelers/scripts/guard_no_raw_media.py --paths DIR_OR_FILE ...

Exit 0 = clean, 1 = findings. It prints the file and the rule that matched, never the matched text.
Rules: audio/video files, caption files, JSON that looks like a speech-to-text dump, files over 5 MB,
scratch folders, and credential patterns (GitHub, Google, AWS, Slack tokens and private keys).
Run it before every push. As a Git hook:  echo 'python3 et-channelers/scripts/guard_no_raw_media.py --staged' > .git/hooks/pre-commit
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ET_ROOT = HERE.parents[1]
REPO = HERE.parents[2]

MEDIA = {".opus", ".m4a", ".mp3", ".wav", ".flac", ".webm", ".ogg", ".oga", ".aac", ".wma", ".mp4", ".mkv",
         ".mov", ".avi", ".m4v", ".part", ".ytdl"}
CAPTIONS = {".vtt", ".srt", ".ttml", ".srv1", ".srv2", ".srv3", ".json3", ".sbv", ".ass", ".lrc"}
SCRATCH_DIRS = {".work", "private_data", "captions_raw"}
MAX_BYTES = 5_000_000
SCAN_BYTES = 2_000_000
SECRETS = [
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("github-token", re.compile(r"github_pat_[A-Za-z0-9_]{22,}")),
    ("google-api-key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----")),
    ("slack-token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
]


def git_files(args_):
    out = subprocess.run(["git", "-C", str(REPO), *args_, "-z"], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        sys.exit(f"git failed: {out.stderr.strip()}")
    return [REPO / p for p in out.stdout.split("\0") if p]


def walk(paths):
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += [f for f in p.rglob("*") if f.is_file() and ".git" not in f.relative_to(p).parts]
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"no such path: {p}")
    return files


def check(path: Path):
    """Rules that matched this file (names only)."""
    hits = []
    suffix = path.suffix.lower()
    if suffix in MEDIA:
        hits.append("audio-or-video-file")
    if suffix in CAPTIONS:
        hits.append("caption-file")
    if any(part in SCRATCH_DIRS for part in path.parts):
        hits.append("scratch-or-private-folder")
    try:
        size = path.stat().st_size
    except OSError:
        return hits
    if size > MAX_BYTES:
        hits.append("file-over-5MB")
    if suffix in MEDIA or size > SCAN_BYTES or size == 0:
        return hits
    try:
        head = path.read_bytes()
    except OSError:
        return hits
    if b"\0" in head[:4096]:
        return hits  # binary: no text rules
    text = head.decode("utf-8", errors="ignore")
    if suffix in (".json", ".jsonl") and '"avg_logprob"' in text[:200_000]:
        hits.append("speech-to-text-json")
    for name, pattern in SECRETS:
        if pattern.search(text):
            hits.append(name)
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="scan the whole repository, not only et-channelers/")
    ap.add_argument("--staged", action="store_true", help="scan only staged files")
    ap.add_argument("--paths", nargs="+", help="scan these files or folders instead of using Git")
    args = ap.parse_args()

    if args.paths:
        files = walk(args.paths)
    elif args.staged:
        files = git_files(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    else:
        files = git_files(["ls-files", "--cached", "--others", "--exclude-standard"])
        if not args.all:
            files = [f for f in files if ET_ROOT in f.parents]
    findings = [(f, hit) for f in sorted(set(files)) if f.exists() for hit in check(f)]
    for f, hit in findings:
        try:
            shown = f.relative_to(REPO)
        except ValueError:
            shown = f
        print(f"{shown}: {hit}")
    print(f"checked {len(set(files))} files, {len(findings)} finding(s)")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
