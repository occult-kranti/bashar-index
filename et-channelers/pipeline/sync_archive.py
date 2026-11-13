#!/usr/bin/env python3
"""Move finished audio and transcripts to a private store, check the copy, then free the local disk.

Run it next to the downloaders: they fill the private folder, this empties it. One command does
upload, verify and delete, and with --watch it keeps doing so until you stop it.

Stores (--store):
  gh:OWNER/REPO@TAG    release assets on a PRIVATE GitHub repository, through the `gh` command you are
                       logged in with. Items are packed into plain tar bundles (default 400 MB each).
                       The repository's visibility is read first and the upload is refused unless it
                       is private: these recordings and texts belong to their makers and must not be
                       published. There is no flag to override that.
  dir:/some/folder     any folder outside a Git checkout: an external disk, or a folder your Drive or
                       OneDrive client syncs. Files keep the same layout as the private folder.

What counts as finished: audio whose manifest line says "ok" and whose file is on disk with the
recorded size; machine transcripts and publisher texts whose manifest line says "ok".

Deleting: only after the copy has been checked (size and SHA-256 for dir:, size and GitHub's own
SHA-256 digest for gh:), and by default only the audio, which is what fills the disk. Texts are small
and stay unless --delete all. Manifests are never deleted; a copy of them travels with every push.
The ledger <root>/sync/sync_manifest.jsonl records where each item went, so later runs skip it and
`pull` can bring it back.

    python3 pipeline/sync_archive.py status --store gh:you/private-archive@audio-v1
    python3 pipeline/sync_archive.py push   --store gh:you/private-archive@audio-v1 --delete audio
    python3 pipeline/sync_archive.py push   --store dir:/mnt/disk/et-archive --delete audio --watch 60
    python3 pipeline/sync_archive.py pull   --store gh:you/private-archive@audio-v1 --only athina-krol
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ITEM_RE, add_root_arg, append_jsonl, ensure_outside_git, latest_by_key, layout,  # noqa: E402
                    read_jsonl, run_cmd, sha256_file, utc_now)

KINDS = ("audio", "asr", "pubtext")
MANIFESTS = ("audio/audio_manifest.jsonl", "transcripts/transcripts_manifest.jsonl",
             "transcripts_publisher/publisher_text_manifest.jsonl", "feeds/feeds_manifest.jsonl",
             "jobs/queue.csv", "jobs/queue_enclosures.csv", "catalog/catalog.csv")


class StoreError(Exception):
    pass


# ---------------------------------------------------------------- what is ready locally
def local_items(paths, only):
    """[{video_id, kind, person, files:[(relative path, absolute Path)], bytes}] for everything finished."""
    out = []
    audio = latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl"))
    for ident, rec in audio.items():
        if rec.get("status") != "ok" or not ITEM_RE.match(ident):
            continue
        f = paths.audio / rec["path"]
        if f.exists() and f.stat().st_size == rec.get("bytes"):
            out.append({"video_id": ident, "kind": "audio", "person": rec["channel_dir"], "bytes": f.stat().st_size,
                        "files": [(f"audio/{rec['path']}", f)]})
    asr = latest_by_key(read_jsonl(paths.transcripts / "transcripts_manifest.jsonl"))
    for ident, rec in asr.items():
        if rec.get("status") != "ok":
            continue
        files = [(f"transcripts/{rec['channel_dir']}/{ident}{ext}", paths.transcripts / rec["channel_dir"] / f"{ident}{ext}")
                 for ext in (".json", ".txt")]
        files = [(rel, p) for rel, p in files if p.exists()]
        if files:
            out.append({"video_id": ident, "kind": "asr", "person": rec["channel_dir"], "files": files,
                        "bytes": sum(p.stat().st_size for _, p in files)})
    pub = latest_by_key(read_jsonl(paths.pubtext / "publisher_text_manifest.jsonl"))
    for ident, rec in pub.items():
        if rec.get("status") != "ok":
            continue
        files = [(f"transcripts_publisher/{rec['channel_dir']}/{ident}{ext}", paths.pubtext / rec["channel_dir"] / f"{ident}{ext}")
                 for ext in (".txt", ".source")]
        files = [(rel, p) for rel, p in files if p.exists()]
        if files:
            out.append({"video_id": ident, "kind": "pubtext", "person": rec["channel_dir"], "files": files,
                        "bytes": sum(p.stat().st_size for _, p in files)})
    if only:
        out = [i for i in out if i["person"] in only]
    return out


def ledger(paths):
    """{(video_id, kind, store): record} for verified uploads."""
    done = {}
    for rec in read_jsonl(paths.root / "sync" / "sync_manifest.jsonl"):
        key = (rec["video_id"], rec["kind"], rec["store"])
        if rec.get("verified"):
            done[key] = rec
        elif rec.get("withdrawn"):
            done.pop(key, None)
    return done


# ---------------------------------------------------------------- stores
class DirStore:
    """A plain folder. Each file is copied to the same relative path and re-read to check it."""

    def __init__(self, spec):
        self.spec = spec
        self.base = ensure_outside_git(Path(spec.split(":", 1)[1]).expanduser())

    def check_private(self):
        return f"folder {self.base}"

    def put_items(self, items, _args):
        results = []
        for item in items:
            names = []
            for rel, src in item["files"]:
                dst = self.base / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                tmp = dst.with_name(dst.name + ".part")
                shutil.copyfile(src, tmp)
                if sha256_file(tmp) != sha256_file(src):
                    tmp.unlink(missing_ok=True)
                    raise StoreError(f"copy of {rel} does not match the original")
                os.replace(tmp, dst)
                names.append(rel)
            results.append((item, {"remote": names[0], "remote_files": names}))
        return results

    def put_manifests(self, paths):
        for rel in MANIFESTS:
            src = paths.root / rel
            if src.exists():
                dst = self.base / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)

    def fetch(self, rec, paths):
        for rel in rec.get("remote_files") or [rec["remote"]]:
            src, dst = self.base / rel, paths.root / rel
            if not src.exists():
                raise StoreError(f"{rel} is not in the store")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)


class GhStore:
    """Release assets on a private GitHub repository. Items travel in tar bundles."""

    def __init__(self, spec, gh="gh"):
        self.spec, self.gh = spec, gh
        body = spec.split(":", 1)[1]
        if "@" not in body or body.count("/") != 1:
            raise StoreError("gh store must look like gh:OWNER/REPO@TAG")
        self.repo, self.tag = body.split("@", 1)
        self._assets = None

    def _run(self, *args, timeout=3600):
        code, out, err = run_cmd([self.gh, *args], timeout)
        if code != 0:
            raise StoreError(f"gh {' '.join(args[:3])}...: {(err or out).strip()[-300:]}")
        return out

    def check_private(self):
        visibility = self._run("api", f"repos/{self.repo}", "--jq", ".visibility", timeout=60).strip()
        if visibility != "private":
            raise StoreError(
                f"refusing to upload: {self.repo} is {visibility or 'not readable'}, not private. Recordings and "
                "transcripts belong to their makers and must not be published. Make the repository private first "
                "(Settings, General, Danger Zone, Change visibility), then run this again.")
        return f"private repository {self.repo}, release {self.tag}"

    def assets(self, refresh=False):
        if self._assets is None or refresh:
            code, out, _ = run_cmd([self.gh, "release", "view", self.tag, "-R", self.repo, "--json", "assets"], 120)
            if code != 0:
                self._run("release", "create", self.tag, "-R", self.repo, "--title", self.tag, "--notes",
                          "Private research archive. Bundles are written by et-channelers/pipeline/sync_archive.py.",
                          timeout=120)
                out = self._run("release", "view", self.tag, "-R", self.repo, "--json", "assets", timeout=120)
            self._assets = {a["name"]: a for a in json.loads(out).get("assets", [])}
        return self._assets

    def _upload(self, path):
        self._run("release", "upload", self.tag, str(path), "-R", self.repo, "--clobber")
        asset = self.assets(refresh=True).get(Path(path).name)
        if not asset or asset.get("size") != Path(path).stat().st_size:
            raise StoreError(f"{Path(path).name}: the store reports a different size than the local bundle")
        digest = (asset.get("digest") or "")
        if digest.startswith("sha256:") and digest[7:] != sha256_file(path):
            raise StoreError(f"{Path(path).name}: the store's SHA-256 differs from the local bundle")

    def put_items(self, items, args):
        """Pack items into bundles of about --bundle-mb, upload each, and return (item, facts) pairs."""
        results, batch, size = [], [], 0
        limit = args.bundle_mb * 1_000_000

        def flush():
            nonlocal batch, size
            if not batch:
                return
            stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
            members = sorted(rel for item in batch for rel, _ in item["files"])
            tag = hashlib.sha256("\n".join(members).encode()).hexdigest()[:8]
            name = f"{batch[0]['kind']}-{stamp}-{tag}.tar"
            work = args.scratch / name
            work.parent.mkdir(parents=True, exist_ok=True)
            index = {"created": utc_now(), "members": []}
            with tarfile.open(work, "w") as tar:
                for item in batch:
                    for rel, src in item["files"]:
                        tar.add(src, arcname=rel)
                        index["members"].append({"path": rel, "video_id": item["video_id"], "kind": item["kind"],
                                                 "bytes": src.stat().st_size, "sha256": sha256_file(src)})
                blob = json.dumps(index, indent=1).encode("utf-8")
                info = tarfile.TarInfo("bundle.json")
                info.size, info.mtime = len(blob), int(time.time())
                import io
                tar.addfile(info, io.BytesIO(blob))
            try:
                self._upload(work)
            finally:
                bundle_sha, bundle_bytes = sha256_file(work), work.stat().st_size
                work.unlink(missing_ok=True)
            for item in batch:
                results.append((item, {"remote": name, "remote_files": [rel for rel, _ in item["files"]],
                                       "bundle_sha256": bundle_sha, "bundle_bytes": bundle_bytes}))
            batch, size = [], 0

        for kind in KINDS:  # one kind per bundle keeps audio bundles easy to drop or re-encode later
            for item in (i for i in items if i["kind"] == kind):
                if batch and (size + item["bytes"] > limit or len(batch) >= args.bundle_items):
                    flush()
                batch.append(item)
                size += item["bytes"]
            flush()
        return results

    def put_manifests(self, paths):
        work = paths.root / "sync" / ".scratch" / "manifests.tar"
        work.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(work, "w") as tar:
            for rel in MANIFESTS:
                if (paths.root / rel).exists():
                    tar.add(paths.root / rel, arcname=rel)
        try:
            self._run("release", "upload", self.tag, str(work), "-R", self.repo, "--clobber")
        finally:
            work.unlink(missing_ok=True)

    def fetch(self, rec, paths):
        scratch = paths.root / "sync" / ".scratch"
        scratch.mkdir(parents=True, exist_ok=True)
        bundle = scratch / rec["remote"]
        if not bundle.exists():
            self._run("release", "download", self.tag, "-R", self.repo, "-p", rec["remote"], "-D", str(scratch), "--clobber")
        wanted = set(rec.get("remote_files") or [])
        with tarfile.open(bundle) as tar:
            for member in tar.getmembers():
                target = (paths.root / member.name).resolve()
                if member.name in wanted and member.isfile() and str(target).startswith(str(paths.root.resolve()) + os.sep):
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with tar.extractfile(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)


def open_store(spec, gh="gh"):
    if spec.startswith("dir:"):
        return DirStore(spec)
    if spec.startswith("gh:"):
        return GhStore(spec, gh)
    raise StoreError("--store must start with gh: or dir:")


# ---------------------------------------------------------------- commands
def push_once(args, paths, store):
    done = ledger(paths)
    items = [i for i in local_items(paths, args.only) if i["kind"] in args.kinds]
    todo = [i for i in items if (i["video_id"], i["kind"], store.spec) not in done]
    if args.limit:
        todo = todo[:args.limit]
    deleted = 0
    uploaded = store.put_items(todo, args) if todo else []
    for item, facts in uploaded:
        append_jsonl(paths.root / "sync" / "sync_manifest.jsonl",
                     {"video_id": item["video_id"], "kind": item["kind"], "person": item["person"],
                      "store": store.spec, "bytes": item["bytes"], "uploaded_at": utc_now(), "verified": True,
                      "sha256": {rel: sha256_file(p) for rel, p in item["files"]}, **facts})
    if uploaded:
        store.put_manifests(paths)
    # delete what is safely stored: items uploaded now and items uploaded by an earlier run
    done = ledger(paths)
    transcribed = {i["video_id"] for i in items if i["kind"] == "asr"} | \
        {v for (v, k, s) in done if k == "asr" and s == store.spec}
    for item in items:
        if (item["video_id"], item["kind"], store.spec) not in done:
            continue
        if item["kind"] == "audio" and args.hold_untranscribed and item["video_id"] not in transcribed:
            continue  # stored, but the transcriber still needs the local file
        if args.delete == "all" or (args.delete == "audio" and item["kind"] == "audio"):
            for _, f in item["files"]:
                f.unlink(missing_ok=True)
            deleted += 1
    return len(todo), len(uploaded), deleted


def cmd_push(args, paths, store):
    print(f"store: {store.check_private()}", file=sys.stderr)
    args.scratch = paths.root / "sync" / ".scratch"
    while True:
        listed, uploaded, deleted = push_once(args, paths, store)
        free = shutil.disk_usage(paths.root).free / 1e9
        print(f"[sync] to upload {listed} | uploaded and checked {uploaded} | local copies deleted {deleted} | "
              f"{free:.1f} GB free", file=sys.stderr, flush=True)
        if not args.watch:
            return
        if args.stop_file and Path(args.stop_file).exists():
            print("[sync] stop file found, leaving", file=sys.stderr)
            return
        time.sleep(args.watch)


def cmd_status(args, paths, store):
    done = ledger(paths)
    local = local_items(paths, args.only)
    rows = {}
    for kind in KINDS:
        mine = [i for i in local if i["kind"] == kind]
        stored = [r for (v, k, s), r in done.items() if k == kind and s == store.spec]
        rows[kind] = {"on_disk": len(mine), "on_disk_gb": round(sum(i["bytes"] for i in mine) / 1e9, 2),
                      "in_store": len(stored), "in_store_gb": round(sum(r.get("bytes", 0) for r in stored) / 1e9, 2),
                      "on_disk_not_stored": sum(1 for i in mine if (i["video_id"], kind, store.spec) not in done)}
    print(json.dumps({"store": store.spec, "kinds": rows}, indent=1))


def cmd_pull(args, paths, store):
    wanted = [r for (v, k, s), r in ledger(paths).items()
              if s == store.spec and k in args.kinds and (not args.only or r.get("person") in args.only)]
    if args.limit:
        wanted = wanted[:args.limit]
    for rec in wanted:
        store.fetch(rec, paths)
    print(f"[sync] brought back {len(wanted)} item(s) from {store.spec}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("push", "status", "pull"))
    add_root_arg(ap)
    ap.add_argument("--store", required=True, help="gh:OWNER/REPO@TAG (private repository) or dir:/folder")
    ap.add_argument("--kinds", default="audio,asr,pubtext", help="what to move: audio, asr, pubtext")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--delete", choices=("none", "audio", "all"), default="none",
                    help="local copies to remove once the stored copy has been checked (default none)")
    ap.add_argument("--hold-untranscribed", action="store_true",
                    help="keep the local audio until its machine transcript exists (use while transcribe.py runs)")
    ap.add_argument("--watch", type=float, default=0, help="repeat every N seconds until interrupted")
    ap.add_argument("--stop-file", default="", help="with --watch: leave when this file exists")
    ap.add_argument("--bundle-mb", type=int, default=400, help="gh store: target size of one bundle")
    ap.add_argument("--bundle-items", type=int, default=400, help="gh store: most items in one bundle")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--gh", default="gh")
    args = ap.parse_args()
    args.kinds = [k.strip() for k in args.kinds.split(",") if k.strip() in KINDS]
    args.only = {x.strip() for x in args.only.split(",") if x.strip()}
    paths = layout(ensure_outside_git(args.root))
    try:
        store = open_store(args.store, args.gh)
        {"push": cmd_push, "status": cmd_status, "pull": cmd_pull}[args.command](args, paths, store)
    except StoreError as err:
        print(f"STOPPED: {err}", file=sys.stderr)
        sys.exit(5)


if __name__ == "__main__":
    main()
