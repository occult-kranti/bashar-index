#!/usr/bin/env python3
"""Fail if the repository holds raw media, caption or transcript dumps, or secrets. Standard library only.

    python3 et-channelers/scripts/guard_no_raw_media.py              # et-channelers/: tracked + untracked, not ignored
    python3 et-channelers/scripts/guard_no_raw_media.py --all        # the whole repository
    python3 et-channelers/scripts/guard_no_raw_media.py --staged     # only what is staged (for a pre-commit hook)
    python3 et-channelers/scripts/guard_no_raw_media.py --paths DIR_OR_FILE ...

Exit 0 = clean, 1 = findings. It prints the file and the rule that matched, never the matched text.
Rules: audio/video files, caption files, JSON that looks like a speech-to-text dump, files over 5 MB,
scratch folders, credential patterns (GitHub, Google, AWS, Slack tokens and private keys), and what the
collection lanes write to the private folder: files named after an item id, saved page sources, the
private catalogue, download queues, collection manifests and archive bundles.
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
# What the pipeline's lanes write under the private root. None of it belongs in the repository.
LANE_ID = re.compile(r"^(?:pod|web|ia)-[0-9a-f]{16}$")
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ITEM_SUFFIXES = {".txt", ".json", ".source", ".vtt", ".srt", ".opus"}
ITEM_DIRS = {"audio", "transcripts", "captions", "transcripts_publisher"}
TEXT_DIRS = {"transcripts_publisher", "captions"}
BUNDLE = re.compile(r"^(?:(?:audio|asr|pubtext|captions)-\d{8}T\d{6}-[0-9a-f]{8}|manifests)\.tar$")
MANIFEST_NAME = re.compile(r"(?:_manifest(?:\.part-\d+)?\.jsonl|^apple_candidates\.jsonl)$")
PRIVATE_CSV_HEADERS = (("item_id,person_id,lane,relation,title", "private-catalogue"),
                       ("video_id,url,channel_dir", "download-queue"))
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
    stem = path.name.split(".")[0]                       # 'pod-…​.en.vtt' and 'abc.en-orig.vtt' keep the id first
    parts = set(path.parts[:-1])
    if suffix == ".source" or path.name.endswith(".source.gz"):
        hits.append("saved-page-source")
    if LANE_ID.match(stem) or (YOUTUBE_ID.match(stem) and suffix in ITEM_SUFFIXES and parts & ITEM_DIRS):
        hits.append("collected-item-file")
    elif parts & TEXT_DIRS and suffix in ITEM_SUFFIXES:
        hits.append("collected-item-file")
    if BUNDLE.match(path.name):
        hits.append("archive-bundle")
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
    if suffix == ".csv":
        first = text.lstrip("\ufeff").split("\n", 1)[0].strip()
        for header, name in PRIVATE_CSV_HEADERS:
            if first.startswith(header):
                hits.append(name)
    if MANIFEST_NAME.search(path.name) and ('"video_id"' in text[:200_000] or '"feed_url"' in text[:200_000]
                                            or '"feed_key"' in text[:200_000]):
        hits.append("collection-manifest")
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
