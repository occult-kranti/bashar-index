#!/usr/bin/env python3
"""Copy the archive's texts into a PRIVATE GitHub repository as plain files, then commit and push.

sync_archive.py puts audio (and a copy of every text) on the private repository's release as tar
bundles: safe, but not readable on GitHub. This puts the texts in the repository itself, so they can
be read, searched and diffed there:

    README.md                                 what the repository is (written here)
    texts/<person>/from-source/<id>.txt       texts the publisher wrote, and YouTube caption tracks
    texts/<person>/made-here/<id>.txt         speech-to-text made by this project
    texts/<person>/made-here/<id>.json        the same with timestamps and confidence
    index/<person>.csv                        one row per item: kind, title, date, words, link, audio held
    catalog.csv                               the whole private catalogue

The repository must be private: its visibility is read with `gh` before anything is copied, and the run
stops (exit code 5) if it is not. The checkout must be a clone of that repository and nothing else (in
particular not this public one): its origin must have one fetch address and one push address, both of
that repository (--remote may give another form of its address, never another repository), and nothing
is written through a link that leads out of the checkout. With --push every run starts from the remote's
branch, whatever an earlier run left (a stopped rebase, a commit whose push failed): every file is copied
again from the private folder, so nothing is lost. Audio is never put in Git.

    python3 pipeline/mirror_texts.py --repo you/et-channelers-archive --checkout ~/et-archive-checkout
    python3 pipeline/mirror_texts.py --repo you/et-channelers-archive --checkout ~/et-archive-checkout --push
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import add_root_arg, ensure_outside_git, latest_by_key, layout, read_csv, read_jsonl, utc_now, write_csv  # noqa: E402

INDEX_FIELDS = ["item_id", "kind", "title", "published", "duration_s", "words_from_source", "words_made_here",
                "audio_held", "source_url", "text_file"]
README = """# Private archive: texts

Collected by the et-channelers pipeline of the bashar-index project. **Private: do not make this
repository public.** The recordings and texts belong to their makers.

* `texts/<person>/from-source/` holds texts the publisher wrote (or YouTube caption tracks).
* `texts/<person>/made-here/` holds speech-to-text made by the project, with timestamps in the `.json`.
* `index/<person>.csv` lists every item: its kind, title, date, word counts, source and whether its audio is held.
* Audio is not in Git. It is on this repository's release, in tar bundles written by `sync_archive.py`.

Last updated {updated}: {people} people, {from_source} texts from the source, {made_here} transcripts made here.
"""


class Refused(Exception):
    pass


def git(checkout, *args, check=True):
    """Run git in the checkout. Credentials come from `gh` (the caller's own login), not from the
    environment's token, which may only reach the public repository."""
    cmd = ["git", "-C", str(checkout), "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential", *args]
    done = subprocess.run(cmd, capture_output=True, text=True)
    if check and done.returncode != 0:
        raise Refused(f"git {' '.join(args[:2])} failed: {(done.stderr or done.stdout).strip()[-300:]}")
    return done.stdout.strip()


def repo_is_private(repo: str, gh: str) -> bool:
    done = subprocess.run([gh, "api", f"repos/{repo}", "--jq", ".private"], capture_output=True, text=True)
    if done.returncode != 0:
        raise Refused(f"could not read the visibility of {repo}: {(done.stderr or done.stdout).strip()[-200:]}")
    return done.stdout.strip() == "true"


GITHUB_ADDRESS = re.compile(r"(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?/?",
                            re.I)


def github_repo(url: str) -> str:
    """'owner/repo' (lower case) for an address of a repository on github.com, in its https, ssh or scp form;
    '' for anything else."""
    found = GITHUB_ADDRESS.fullmatch((url or "").strip())
    return found.group(1).lower() if found else ""


def address_key(url: str) -> str:
    """What names a repository: owner/repo for any form of a github.com address, else the address itself."""
    return github_repo(url) or re.sub(r"\.git$", "", (url or "").strip().rstrip("/")).lower()


def same_remote(a: str, b: str) -> bool:
    return bool(address_key(a)) and address_key(a) == address_key(b)


def check_origin(checkout: Path, remote: str):
    """Refuse a checkout whose origin is not `remote` alone, for fetching and for pushing: a push goes to
    every push address (a pushurl, a second url, a pushInsteadOf rule anywhere in git's configuration),
    and `git remote get-url --push --all` lists exactly those."""
    fetch = git(checkout, "remote", "get-url", "--all", "origin", check=False).splitlines()
    push = git(checkout, "remote", "get-url", "--push", "--all", "origin", check=False).splitlines()
    if len(fetch) != 1 or len(push) != 1 or not all(same_remote(u, remote) for u in fetch + push):
        raise Refused(f"{checkout} is not a clone of {remote} that pushes only there (fetch {fetch}, push {push})")


def start_from_remote(checkout: Path) -> str:
    """Put the checkout on the remote's branch, whatever an earlier run left (a rebase stopped by a conflict,
    a commit whose push failed). Returns the branch. mirror() writes every file again from the private folder,
    so a local commit that never reached the remote loses nothing."""
    for stuck in ("rebase", "merge", "cherry-pick"):
        git(checkout, stuck, "--abort", check=False)
    git(checkout, "fetch", "--quiet", "origin")
    # symbolic-ref prints nothing when origin/HEAD is missing (a clone of a repository that was still empty);
    # rev-parse --abbrev-ref printed "origin/HEAD" then, which made the branch "HEAD"
    head = git(checkout, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False)
    branch = head.split("/", 1)[1] if head.startswith("origin/") else ""
    branch = branch or git(checkout, "symbolic-ref", "--quiet", "--short", "HEAD", check=False) or "main"
    if git(checkout, "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}", check=False):
        git(checkout, "checkout", "--quiet", "-f", "-B", branch, f"origin/{branch}")
    return branch


def inside(checkout: Path, path: Path) -> Path:
    """`path`, if writing to it writes inside the checkout. A folder or file in the checkout that is a link to
    somewhere else (the public repository, say) stops the run before anything is written through it."""
    real = Path(path).resolve()
    if not real.is_relative_to(Path(checkout).resolve()):
        raise Refused(f"{path} leads outside the checkout, to {real}: nothing is written through it")
    return Path(path)


def copy_if_changed(src: Path, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size == src.stat().st_size and dst.read_bytes() == src.read_bytes():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return True


def mirror(root: Path, checkout: Path):
    """Copy texts and indexes into the checkout. Returns (files changed, counts)."""
    paths = layout(root)
    catalogue = paths.root / "catalog" / "catalog.csv"
    rows = read_csv(catalogue) if catalogue.exists() else []
    pub = latest_by_key(read_jsonl(paths.pubtext / "publisher_text_manifest.jsonl"))
    caps = latest_by_key(read_jsonl(paths.captions / "captions_manifest.jsonl"))
    asr_lines = read_jsonl(paths.transcripts / "transcripts_manifest.jsonl")
    for part in sorted(paths.transcripts.glob("transcripts_manifest.part-*.jsonl")):
        asr_lines += read_jsonl(part)
    asr = latest_by_key(asr_lines)
    changed, counts = 0, {"from_source": 0, "made_here": 0}
    people = {}
    at = lambda rel: inside(checkout, checkout / rel)  # noqa: E731 - every place written is checked first
    for top in ("texts", "index", "catalog.csv", "README.md"):
        at(top)
    for row in rows:
        person, ident = row.get("person_id") or "unsorted", row["item_id"]
        text_rel = ""
        for manifest, folder, kind in ((pub, paths.pubtext, "from-source"), (caps, paths.captions, "from-source")):
            rec = manifest.get(row.get("text_id") or ident) or manifest.get(ident)
            if rec and rec.get("status") == "ok":
                src = folder / rec["channel_dir"] / f"{rec['video_id']}.txt"
                if src.exists():
                    text_rel = f"texts/{person}/from-source/{rec['video_id']}.txt"
                    changed += copy_if_changed(src, at(text_rel))
                    counts["from_source"] += 1
                    break
        rec = asr.get(ident)
        if rec and rec.get("status") == "ok":
            for ext in (".txt", ".json"):
                src = paths.transcripts / rec["channel_dir"] / f"{ident}{ext}"
                if src.exists():
                    rel = f"texts/{person}/made-here/{ident}{ext}"
                    changed += copy_if_changed(src, at(rel))
                    text_rel = text_rel or (rel if ext == ".txt" else "")
            counts["made_here"] += 1
        if text_rel or row.get("audio_status") == "ok":
            people.setdefault(person, []).append({
                "item_id": ident, "kind": row.get("relation") or row.get("lane") or "", "title": row.get("title") or "",
                "published": row.get("published") or "", "duration_s": row.get("duration_s") or "",
                "words_from_source": row.get("publisher_text_words") or row.get("captions_words") or "",
                "words_made_here": row.get("asr_words") or "", "audio_held": "yes" if row.get("audio_status") == "ok" else "no",
                "source_url": row.get("source_url") or "", "text_file": text_rel})
    # texts that no catalogue row points at (a page whose recording was listed under another id, a text
    # fetched before the catalogue was rebuilt) are copied too: the mirror is of every text held
    copied = {p.name.split(".")[0] for p in (checkout / "texts").rglob("*.txt")} if (checkout / "texts").exists() else set()
    for manifest, folder, kind in ((pub, paths.pubtext, "from-source"), (caps, paths.captions, "from-source"),
                                   (asr, paths.transcripts, "made-here")):
        for ident, rec in manifest.items():
            if rec.get("status") != "ok" or ident in copied:
                continue
            for ext in (".txt", ".json") if kind == "made-here" else (".txt",):
                src = folder / (rec.get("channel_dir") or "unsorted") / f"{ident}{ext}"
                if src.exists():
                    changed += copy_if_changed(src, at(f"texts/{rec.get('channel_dir') or 'unsorted'}/{kind}/{ident}{ext}"))
                    counts["from_source" if kind == "from-source" else "made_here"] += ext == ".txt"
    for person, items in people.items():
        target = at(f"index/{person}.csv")
        before = target.read_bytes() if target.exists() else b""
        write_csv(target, sorted(items, key=lambda r: (r["published"], r["item_id"])), INDEX_FIELDS)
        changed += target.read_bytes() != before
    if catalogue.exists():
        changed += copy_if_changed(catalogue, at("catalog.csv"))
    readme = at("README.md")
    text = README.format(updated=utc_now()[:10], people=len(people), **counts)
    if not readme.exists() or readme.read_text(encoding="utf-8").split("Last updated")[0] != text.split("Last updated")[0] \
            or changed:
        readme.write_text(text, encoding="utf-8")
    return changed, {**counts, "people": len(people)}


def sync(root: Path, checkout: Path, remote: str, push: bool):
    """Copy the texts into the checkout of `remote` and, with `push`, commit and push them. Returns (files
    changed, counts, the address pushed to or ''). The caller has checked that `remote` is the private
    repository; this checks that the checkout fetches from it and pushes to it alone."""
    check_origin(checkout, remote)
    branch = start_from_remote(checkout) if push else ""
    changed, counts = mirror(root, checkout)
    if not (push and changed):
        return changed, counts, ""
    git(checkout, "add", "-A")
    if not git(checkout, "status", "--porcelain"):
        return changed, counts, ""
    git(checkout, "-c", "user.name=et-channelers pipeline", "-c", "user.email=noreply@users.noreply.github.com",
        "commit", "--quiet", "-m", f"Texts as of {utc_now()}")
    check_origin(checkout, remote)                             # again, just before the push
    git(checkout, "push", "--quiet", "origin", f"HEAD:refs/heads/{branch}")
    return changed, counts, f"{git(checkout, 'remote', 'get-url', '--push', 'origin', check=False)} ({branch})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--repo", required=True, help="OWNER/REPO of the private repository")
    ap.add_argument("--checkout", type=Path, required=True, help="a clone of that repository (made if missing)")
    ap.add_argument("--gh", default="gh")
    ap.add_argument("--remote", default="", help="another form of the same repository's address, such as "
                    "git@github.com:OWNER/REPO.git (default https://github.com/OWNER/REPO.git); never another repository")
    ap.add_argument("--push", action="store_true", help="commit and push (without it, only copy and report)")
    args = ap.parse_args()
    root = ensure_outside_git(args.root)
    try:
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo or ""):
            raise Refused(f"--repo must look like OWNER/REPO, not {args.repo!r}")
        remote = args.remote or f"https://github.com/{args.repo}.git"
        if github_repo(remote) != args.repo.lower():
            # the privacy check below is of --repo: an address of anything else would be pushed to unchecked
            raise Refused(f"--remote {remote} is not an address of {args.repo}")
        if not repo_is_private(args.repo, args.gh):
            raise Refused(f"{args.repo} is not private: these texts belong to their makers and are not published")
        checkout = args.checkout.expanduser().resolve()
        public = Path(__file__).resolve().parents[2]          # this repository, which is public
        if checkout == public or checkout.is_relative_to(public) or public.is_relative_to(checkout):
            raise Refused(f"{checkout} is, or holds, the public repository {public.name}")
        if not (checkout / ".git").exists():
            checkout.parent.mkdir(parents=True, exist_ok=True)
            done = subprocess.run(["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
                                   "clone", "--quiet", remote, str(checkout)], capture_output=True, text=True)
            if done.returncode != 0:
                raise Refused(f"could not clone {args.repo}: {done.stderr.strip()[-200:]}")
        changed, counts, pushed = sync(root, checkout, remote, args.push)
        print(f"{changed} file(s) changed: {counts['from_source']} texts from the source and {counts['made_here']} transcripts "
              f"made here, for {counts['people']} people -> {checkout}")
        if pushed:
            print(f"pushed to {pushed}")
    except Refused as err:
        print(f"STOPPED: {err}", file=sys.stderr)
        sys.exit(5)


if __name__ == "__main__":
    main()
