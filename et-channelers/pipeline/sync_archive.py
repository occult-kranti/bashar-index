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
  dir:/some/folder     any folder outside a Git checkout that is not the private folder itself: an
                       external disk, or a folder your Drive or OneDrive client syncs. Files keep the
                       same layout as the private folder.

What counts as finished: audio whose manifest line says "ok" and whose file is on disk with the
recorded size; machine transcripts, publisher texts and caption tracks whose manifest line says "ok".

When a local file is deleted. Only when all of these hold:
  * the ledger has a line for it for this store, written after its copy was checked
    (dir: every file read back and compared by SHA-256; gh: the bundle's size, and GitHub's own
    SHA-256 digest where it reports one);
  * the file on disk is still byte for byte the one that line describes (its SHA-256 is taken again
    just before deleting; a file that changed is uploaded again as a new version instead);
  * the store still holds it (dir: the files are there with the recorded sizes; gh: the bundle is
    still on the release). If it does not, the item is sent again and nothing is deleted first.
By default only audio is deleted (--delete audio), which is what fills the disk. Manifests are never
deleted; a copy of them travels with every push. The ledger is <root>/sync/sync_manifest.jsonl: the
downloaders read it too, so an item that is safely stored is never fetched again.

    python3 pipeline/sync_archive.py status --store gh:you/private-archive@audio-v1
    python3 pipeline/sync_archive.py push   --store gh:you/private-archive@audio-v1 --delete audio
    python3 pipeline/sync_archive.py push   --store dir:/mnt/disk/et-archive --delete audio --watch 60
    python3 pipeline/sync_archive.py pull   --store gh:you/private-archive@audio-v1 --only athina-krol
"""
from __future__ import annotations

import argparse
import hashlib
import io
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

KINDS = ("audio", "asr", "pubtext", "captions")
MANIFESTS = ("audio/audio_manifest.jsonl", "transcripts/transcripts_manifest.jsonl",
             "transcripts_publisher/publisher_text_manifest.jsonl", "captions/captions_manifest.jsonl",
             "feeds/feeds_manifest.jsonl", "jobs/queue.csv", "jobs/queue_enclosures.csv", "catalog/catalog.csv")


class StoreError(Exception):
    pass


# ---------------------------------------------------------------- what is ready locally
def local_items(paths, only):
    """[{video_id, kind, person, files:[(relative path, absolute Path)], bytes}] for everything finished."""
    out = []

    def add(ident, kind, person, files):
        files = [(rel, p) for rel, p in files if p.is_file()]
        if files:
            out.append({"video_id": ident, "kind": kind, "person": person, "files": files,
                        "bytes": sum(p.stat().st_size for _, p in files)})

    for ident, rec in latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl")).items():
        if rec.get("status") == "ok" and ITEM_RE.match(ident):
            f = paths.audio / rec["path"]
            if f.is_file() and f.stat().st_size == rec.get("bytes"):   # a doubtful file is never moved
                add(ident, "audio", rec["channel_dir"], [(f"audio/{rec['path']}", f)])
    for ident, rec in latest_by_key(read_jsonl(paths.transcripts / "transcripts_manifest.jsonl")).items():
        if rec.get("status") == "ok":
            folder = paths.transcripts / rec["channel_dir"]
            add(ident, "asr", rec["channel_dir"],
                [(f"transcripts/{rec['channel_dir']}/{ident}{ext}", folder / f"{ident}{ext}") for ext in (".json", ".txt")])
    for ident, rec in latest_by_key(read_jsonl(paths.pubtext / "publisher_text_manifest.jsonl")).items():
        if rec.get("status") == "ok":
            folder = paths.pubtext / rec["channel_dir"]
            add(ident, "pubtext", rec["channel_dir"],
                [(f"transcripts_publisher/{rec['channel_dir']}/{ident}{ext}", folder / f"{ident}{ext}")
                 for ext in (".txt", ".source")])
    for ident, rec in latest_by_key(read_jsonl(paths.captions / "captions_manifest.jsonl")).items():
        if rec.get("status") == "ok":
            folder = paths.captions / rec["channel_dir"]
            names = [f"{ident}.{lang}.vtt" for lang in rec.get("tracks") or []] + [f"{ident}.txt"]
            add(ident, "captions", rec["channel_dir"], [(f"captions/{rec['channel_dir']}/{n}", folder / n) for n in names])
    if only:
        out = [i for i in out if i["person"] in only]
    return out


def ledger(paths):
    """{(video_id, kind, store): record} for copies that were checked and not withdrawn since."""
    done = {}
    for rec in read_jsonl(paths.root / "sync" / "sync_manifest.jsonl"):
        key = (rec["video_id"], rec["kind"], rec["store"])
        if rec.get("withdrawn"):
            done.pop(key, None)
        elif rec.get("verified"):
            done[key] = rec
    return done


def sizes_of(item):
    return {rel: p.stat().st_size for rel, p in item["files"]}


def hashes_of(item):
    return {rel: sha256_file(p) for rel, p in item["files"]}


# ---------------------------------------------------------------- stores
class DirStore:
    """A plain folder. Each file is copied to the same relative path and read back to check it."""

    def __init__(self, spec, root):
        self.spec = spec
        self.base = ensure_outside_git(Path(spec.split(":", 1)[1]).expanduser())
        if os.path.realpath(self.base) == os.path.realpath(root):
            raise StoreError(f"the store and the private folder are the same folder ({self.base}). A copy onto itself "
                             "is no copy: choose another disk or folder for --store.")

    def check_private(self):
        return f"folder {self.base}"

    def begin_pass(self):
        pass

    def _copy(self, src, rel):
        dst = self.base / rel
        if dst.exists() and os.path.samefile(src, dst):
            raise StoreError(f"{rel}: the store path is the same file as the local one (a link?). Nothing was copied "
                             "or deleted; choose a store that is really somewhere else.")
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.name + ".part")
        with open(src, "rb") as fin, open(tmp, "wb") as fout:
            shutil.copyfileobj(fin, fout, 1 << 20)
            fout.flush()
            os.fsync(fout.fileno())
        if sha256_file(tmp) != sha256_file(src):
            tmp.unlink(missing_ok=True)
            raise StoreError(f"copy of {rel} does not match the original")
        os.replace(tmp, dst)

    def put_items(self, items, _args):
        """Yield (item, facts) as each item is safely stored."""
        for item in items:
            for rel, src in item["files"]:
                self._copy(src, rel)
            yield item, {"remote": item["files"][0][0], "remote_files": [rel for rel, _ in item["files"]]}

    def put_manifests(self, paths):
        for rel in MANIFESTS:
            src = paths.root / rel
            if src.is_file():
                self._copy(src, rel)

    def has(self, rec):
        sizes = rec.get("sizes") or {}
        for rel in rec.get("remote_files") or [rec["remote"]]:
            f = self.base / rel
            if not f.is_file() or (rel in sizes and f.stat().st_size != sizes[rel]):
                return False
        return True

    def fetch(self, records, paths, overwrite):
        got = skipped = 0
        for rec in records:
            for rel in rec.get("remote_files") or [rec["remote"]]:
                src, dst = self.base / rel, paths.root / rel
                if not src.is_file():
                    raise StoreError(f"{rel} is not in the store")
                if dst.exists() and not overwrite:
                    skipped += 1
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                got += 1
        return got, skipped


class GhStore:
    """Release assets on a private GitHub repository. Items travel in tar bundles."""

    def __init__(self, spec, gh="gh"):
        self.spec, self.gh = spec, gh
        body = spec.split(":", 1)[1]
        if "@" not in body or body.count("/") != 1:
            raise StoreError("gh store must look like gh:OWNER/REPO@TAG")
        self.repo, self.tag = body.split("@", 1)
        self._assets = None

    def _try(self, *args, timeout=3600):
        code, out, err = run_cmd([self.gh, *args], timeout)
        return code, out, (err or out).strip()

    def _run(self, *args, timeout=3600):
        code, out, message = self._try(*args, timeout=timeout)
        if code != 0:
            raise StoreError(f"gh {' '.join(args[:3])}: {message[-300:]}")
        return out

    def check_private(self):
        visibility = self._run("api", f"repos/{self.repo}", "--jq", ".visibility", timeout=60).strip()
        if visibility != "private":
            raise StoreError(
                f"refusing to upload: {self.repo} is {visibility or 'not readable'}, not private. Recordings and "
                "transcripts belong to their makers and must not be published. Make the repository private first "
                "(Settings, General, Danger Zone, Change visibility), then run this again.")
        self.assets(refresh=True)   # makes sure the release exists before anything is downloaded or uploaded
        return f"private repository {self.repo}, release {self.tag}"

    def begin_pass(self):
        self._assets = None

    def assets(self, refresh=False):
        """{asset name: facts}. Creates the release when GitHub says it does not exist; any other failure
        (network, sign-in) is reported as it is and creates nothing."""
        if self._assets is None or refresh:
            view = ("release", "view", self.tag, "-R", self.repo, "--json", "assets")
            code, out, message = self._try(*view, timeout=120)
            if code != 0:
                if "not found" not in message.lower():
                    raise StoreError(f"could not read release {self.tag} of {self.repo}: {message[-300:]}")
                self._run("release", "create", self.tag, "-R", self.repo, "--title", self.tag, "--notes",
                          "Private research archive. Bundles are written by et-channelers/pipeline/sync_archive.py.",
                          timeout=120)
                out = self._run(*view, timeout=120)
            self._assets = {a["name"]: a for a in json.loads(out).get("assets", [])}
        return self._assets

    def _upload(self, path):
        self.assets()
        self._run("release", "upload", self.tag, str(path), "-R", self.repo, "--clobber")
        asset = self.assets(refresh=True).get(Path(path).name)
        if not asset or asset.get("size") != Path(path).stat().st_size:
            raise StoreError(f"{Path(path).name}: the store reports a different size than the local bundle")
        digest = asset.get("digest") or ""
        if digest.startswith("sha256:") and digest[7:] != sha256_file(path):
            raise StoreError(f"{Path(path).name}: the store's SHA-256 differs from the local bundle")

    def _bundle(self, batch, args):
        stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
        members = sorted(rel for item in batch for rel, _ in item["files"])
        tag = hashlib.sha256(("\n".join(members) + stamp).encode()).hexdigest()[:8]
        name = f"{batch[0]['kind']}-{stamp}-{tag}.tar"
        work = args.scratch / name
        work.parent.mkdir(parents=True, exist_ok=True)
        index = {"created": utc_now(), "members": []}
        try:
            with tarfile.open(work, "w") as tar:
                for item in batch:
                    for rel, src in item["files"]:
                        tar.add(src, arcname=rel)
                        index["members"].append({"path": rel, "video_id": item["video_id"], "kind": item["kind"],
                                                 "bytes": src.stat().st_size, "sha256": sha256_file(src)})
                blob = json.dumps(index, indent=1).encode("utf-8")
                info = tarfile.TarInfo("bundle.json")
                info.size, info.mtime = len(blob), int(time.time())
                tar.addfile(info, io.BytesIO(blob))
            facts = {"remote": name, "bundle_sha256": sha256_file(work), "bundle_bytes": work.stat().st_size}
            self._upload(work)
        finally:
            work.unlink(missing_ok=True)
        return facts

    def put_items(self, items, args):
        """Pack items into bundles of about --bundle-mb and yield (item, facts) after each bundle is
        uploaded and checked, so an early bundle is recorded even if a later one fails."""
        limit = args.bundle_mb * 1_000_000
        for kind in KINDS:  # one kind per bundle keeps audio bundles easy to drop or re-encode later
            batch, size = [], 0
            for item in [i for i in items if i["kind"] == kind] + [None]:
                if batch and (item is None or size + item["bytes"] > limit or len(batch) >= args.bundle_items):
                    facts = self._bundle(batch, args)
                    for done in batch:
                        yield done, {**facts, "remote_files": [rel for rel, _ in done["files"]]}
                    batch, size = [], 0
                if item is not None:
                    batch.append(item)
                    size += item["bytes"]

    def put_manifests(self, paths):
        work = paths.root / "sync" / ".scratch" / "manifests.tar"
        work.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(work, "w") as tar:
            for rel in MANIFESTS:
                if (paths.root / rel).is_file():
                    tar.add(paths.root / rel, arcname=rel)
        try:
            self._run("release", "upload", self.tag, str(work), "-R", self.repo, "--clobber")
        finally:
            work.unlink(missing_ok=True)

    def has(self, rec):
        asset = self.assets().get(rec.get("remote", ""))
        return bool(asset) and (rec.get("bundle_bytes") is None or asset.get("size") == rec["bundle_bytes"])

    def fetch(self, records, paths, overwrite):
        scratch = paths.root / "sync" / ".scratch"
        scratch.mkdir(parents=True, exist_ok=True)
        by_bundle, got, skipped = {}, 0, 0
        for rec in records:
            by_bundle.setdefault(rec["remote"], set()).update(rec.get("remote_files") or [])
        root = str(paths.root.resolve()) + os.sep
        for name, wanted in by_bundle.items():
            bundle = scratch / name
            self._run("release", "download", self.tag, "-R", self.repo, "-p", name, "-D", str(scratch), "--clobber")
            try:
                with tarfile.open(bundle) as tar:
                    for member in tar.getmembers():
                        target = (paths.root / member.name).resolve()
                        if member.name not in wanted or not member.isfile() or not str(target).startswith(root):
                            continue
                        if target.exists() and not overwrite:
                            skipped += 1
                            continue
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with tar.extractfile(member) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        got += 1
            finally:
                bundle.unlink(missing_ok=True)
        return got, skipped


def open_store(spec, gh="gh", root=None):
    if spec.startswith("dir:"):
        return DirStore(spec, root if root is not None else Path(os.devnull))
    if spec.startswith("gh:"):
        return GhStore(spec, gh)
    raise StoreError("--store must start with gh: or dir:")


# ---------------------------------------------------------------- commands
def push_once(args, paths, store):
    """One pass. Returns (items uploaded, local copies deleted, items the store had lost)."""
    manifest = paths.root / "sync" / "sync_manifest.jsonl"
    store.check_private()   # every pass: a repository can be made public while a long run is under way
    store.begin_pass()
    done = ledger(paths)
    items = [i for i in local_items(paths, args.only) if i["kind"] in args.kinds]
    transcribed = {i["video_id"] for i in local_items(paths, args.only) if i["kind"] == "asr"} | \
        {v for (v, k, s) in done if k == "asr" and s == store.spec}

    def deletable(item):
        if args.delete == "none" or (args.delete == "audio" and item["kind"] != "audio"):
            return False
        return not (item["kind"] == "audio" and args.hold_untranscribed and item["video_id"] not in transcribed)

    todo, safe, lost = [], [], 0
    for item in items:
        key = (item["video_id"], item["kind"], store.spec)
        rec = done.get(key)
        if rec is None:
            todo.append(item)
            continue
        same = rec.get("sizes", sizes_of(item)) == sizes_of(item)
        if same and (deletable(item) or "sizes" not in rec):
            same = rec.get("sha256") == hashes_of(item)   # the bytes, not only the length, before anything is deleted
        if not same:
            todo.append(item)                              # a newer version of this item: store it as well
            continue
        if not store.has(rec):
            append_jsonl(manifest, {"video_id": item["video_id"], "kind": item["kind"], "store": store.spec,
                                    "withdrawn": True, "at": utc_now(), "why": "no longer in the store"})
            lost += 1
            todo.append(item)
            continue
        safe.append(item)
    if lost:
        print(f"[sync] {lost} item(s) the ledger listed are no longer in the store: sending them again, "
              "nothing is deleted first", file=sys.stderr, flush=True)
    if args.limit:
        todo = todo[:args.limit]

    uploaded = deleted = 0
    try:
        for item, facts in store.put_items(todo, args):
            append_jsonl(manifest, {"video_id": item["video_id"], "kind": item["kind"], "person": item["person"],
                                    "store": store.spec, "bytes": item["bytes"], "uploaded_at": utc_now(),
                                    "verified": True, "sizes": sizes_of(item), "sha256": hashes_of(item), **facts})
            uploaded += 1
            safe.append(item)
    finally:
        if uploaded:
            store.put_manifests(paths)
        current = ledger(paths)
        for item in safe:
            rec = current.get((item["video_id"], item["kind"], store.spec))
            if rec and deletable(item) and all(p.is_file() for _, p in item["files"]) and rec.get("sha256") == hashes_of(item):
                for _, f in item["files"]:
                    f.unlink(missing_ok=True)
                deleted += 1
    return len(todo), uploaded, deleted


def cmd_push(args, paths, store):
    print(f"store: {store.check_private()}", file=sys.stderr)
    args.scratch = paths.root / "sync" / ".scratch"
    while True:
        listed, uploaded, deleted = push_once(args, paths, store)   # raises StoreError if the store stopped being private
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
    got, skipped = store.fetch(wanted, paths, args.overwrite)
    print(f"[sync] {len(wanted)} item(s) asked for from {store.spec}: {got} file(s) written, {skipped} already here "
          "and left alone" + ("" if args.overwrite or not skipped else " (use --overwrite to replace them)"),
          file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("push", "status", "pull"))
    add_root_arg(ap)
    ap.add_argument("--store", required=True, help="gh:OWNER/REPO@TAG (private repository) or dir:/folder")
    ap.add_argument("--kinds", default=",".join(KINDS), help="what to move: " + ", ".join(KINDS))
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--delete", choices=("none", "audio", "all"), default="none",
                    help="local copies to remove once the stored copy has been checked (default none)")
    ap.add_argument("--hold-untranscribed", action="store_true",
                    help="keep the local audio until its machine transcript exists (use while transcribe.py runs)")
    ap.add_argument("--overwrite", action="store_true", help="pull: replace files that already exist locally")
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
        store = open_store(args.store, args.gh, paths.root)
        {"push": cmd_push, "status": cmd_status, "pull": cmd_pull}[args.command](args, paths, store)
    except StoreError as err:
        print(f"STOPPED: {err}", file=sys.stderr)
        sys.exit(5)


if __name__ == "__main__":
    main()
