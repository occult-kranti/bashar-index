#!/usr/bin/env python3
"""Lay out the collected audio and texts as files for Google Drive, in folders by person, ready to upload.

    python3 pipeline/drive_stage.py plan --out /tmp/et-drive/stage --audio-from /tmp/et-drive/pull
    python3 pipeline/drive_stage.py batches --out /tmp/et-drive/stage --n 6
    python3 pipeline/drive_stage.py record --out /tmp/et-drive/stage RESULTS.jsonl ...
    python3 pipeline/drive_stage.py status --out /tmp/et-drive/stage

The upload is done by whoever holds the Drive login: the Claude Google Drive connector (one file per call,
about 7.4 MB at most, which is why big files are cut into parts) or rclone. This tool does everything else:
the names, the folders, the parts, the checksums, and the record of what is already on Drive, so a later run
plans only what is new or changed.

Layout under the archive's top folder on Drive
  04 Audio/<Person>/<group>/<date> <title> [<item id>].opus
      group: "Podcast - <feed title>", "Interviews on other shows", "archive.org sessions",
             "Audio from own website". An interview's name also carries the show and its interview type.
  03 Transcripts/<Person>/<Person> - texts from the source - vol 1 of 3.txt
  03 Transcripts/<Person>/<Person> - speech-to-text made here - vol 1 of 1.txt
Texts from the source and transcripts made here are never mixed in one file. Each text in a volume starts
with a header block: title, date, item id, where it came from.

Audio is never re-encoded. A file larger than --max-mb is cut at packet boundaries with ffmpeg's stream copy
into parts of at most --max-mb, each one playable on its own ("... (part 1 of 3).opus"). The whole files stay
in the private GitHub store (sync_archive.py), byte for byte as downloaded.

Files
  <out>/plan.jsonl        one line per file to upload: key, Drive folder (a path), title, path, sha256, bytes
  <out>/folders.jsonl     the folders the plan needs, parents first, with the Drive id where it is known
  <out>/batches/*.jsonl   `batches`: the pending uploads whose folder ids are known, split for parallel uploaders
  <root>/sync/drive_manifest.jsonl   the ledger: one line per file or folder created on Drive (its Drive id)
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import re
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ET_ROOT, add_root_arg, append_jsonl, ensure_outside_git, latest_by_key, layout,  # noqa: E402
                    probe_duration, read_jsonl, sha256_file, utc_now)

LEDGER = "sync/drive_manifest.jsonl"
AUDIO_TOP, TEXT_TOP = "04 Audio", "03 Transcripts"
# The connector sends a file as base64 inside a request of at most 10,000,000 bytes: 7.3 MB of file fits.
DEFAULT_MAX_MB = 7.3
BAD_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f\x7f]+')
GROUPS = {"host": "Interviews on other shows", "ia": "archive.org sessions", "web": "Audio from own website"}
TEXT_KINDS = {"source": "texts from the source", "made": "speech-to-text made here"}
csv.field_size_limit(1 << 24)


# ---------------------------------------------------------------- names
def clean(text, limit=110) -> str:
    """A name Drive and every desktop system accept: no path or reserved characters, one line, not too long.
    A slash becomes the look-alike '∕' (so "L/L Research" keeps its name) and "a: b" becomes "a - b"."""
    t = re.sub(r"\s*:\s+", " - ", str(text or "")).replace("/", "∕")
    t = re.sub(r"\s+", " ", BAD_CHARS.sub(" ", t)).strip(" .")
    if len(t) > limit:
        t = t[:limit].rstrip(" .,;-") + "…"
    return t


def group_of(row, feed_titles) -> str:
    if row.get("relation") == "host":
        return GROUPS["host"]
    lane = row.get("lane") or ""
    if lane in ("ia", "web"):
        return GROUPS[lane]
    title = clean(feed_titles.get(row.get("feed_key") or "", ""), 70)
    return f"Podcast - {title}" if title else "Podcast"


def audio_name(row, feed_titles) -> str:
    """'<date> <title> [<id>]' (no extension); interviews also name the show and the interview type."""
    date = (row.get("published") or "")[:10] or "undated"
    title = clean(row.get("title"), 110) or "untitled"
    if row.get("relation") == "host":
        show = clean(feed_titles.get(row.get("feed_key") or "", ""), 50)
        kind = clean(row.get("interview_type") or "not classified", 30)
        title = f"{show} - {title} ({kind})" if show else f"{title} ({kind})"
    return f"{date} {title} [{row['item_id']}]"


# ---------------------------------------------------------------- inputs
def person_names() -> dict:
    out = {}
    targets = ET_ROOT / "plan" / "targets.csv"
    if targets.is_file():
        with open(targets, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("person_id"):
                    out[r["person_id"]] = clean(r.get("person_name") or r["person_id"], 80)
    return out


def feed_titles(paths) -> dict:
    out = {}
    for r in read_jsonl(paths.feeds / "feeds_manifest.jsonl"):
        if r.get("feed_key") and r.get("title"):
            out[r["feed_key"]] = r["title"]
    return out


def catalog_rows(paths) -> dict:
    """{item id: row}: the catalogue, and for items it does not list yet, their queue rows (title, date, show)."""
    out = {}
    for q in sorted(paths.jobs.glob("queue*.csv")):
        with open(q, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("video_id") and r.get("title"):
                    out.setdefault(r["video_id"], {**r, "item_id": r["video_id"]})
    cat = paths.root / "catalog" / "catalog.csv"
    if cat.is_file():
        with open(cat, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("item_id"):
                    out[r["item_id"]] = {**out.get(r["item_id"], {}), **{k: v for k, v in r.items() if v}}
    return out


def ledger(paths) -> dict:
    """{key: latest record} of what is on Drive. A record with "trashed" withdraws the key."""
    out = {}
    for rec in read_jsonl(paths.root / LEDGER):
        if rec.get("trashed"):
            out.pop(rec.get("key"), None)
        elif rec.get("key") and rec.get("drive_id"):
            out[rec["key"]] = rec
    return out


def find_audio(rel, places, size):
    """The first copy of audio/<rel> with the recorded size, in the private folder or a pulled copy of it."""
    for base in places:
        f = base / "audio" / rel
        if f.is_file() and (not size or f.stat().st_size == size):
            return f
    return None


# ---------------------------------------------------------------- audio parts
_REV8 = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))
_OGG = struct.Struct("<4sBBqIIIB")   # capture, version, flags, granule, serial, sequence, crc, segments


def ogg_crc(page) -> int:
    """Ogg's CRC-32 (polynomial 0x04C11DB7, start 0, not reflected) over a page whose CRC field is zero.
    zlib's CRC-32 is the reflected form; run on bit-reversed bytes and reversed back, it gives Ogg's at C speed."""
    r = zlib.crc32(bytes(page).translate(_REV8), 0xFFFFFFFF) ^ 0xFFFFFFFF
    return int(f"{r:032b}"[::-1], 2)


def ogg_pages(data: bytes):
    """[(offset, size, flags, granule, data offset, lacing)] for every page; ValueError if it is not Ogg."""
    out, pos = [], 0
    while pos < len(data):
        if data[pos:pos + 4] != b"OggS" or len(data) < pos + 27:
            raise ValueError(f"no Ogg page at byte {pos}")
        _, _, flags, granule, _, _, _, nseg = _OGG.unpack_from(data, pos)
        lacing = data[pos + 27:pos + 27 + nseg]
        size = 27 + nseg + sum(lacing)
        if pos + size > len(data):
            raise ValueError("the last Ogg page is cut short")
        out.append((pos, size, flags, granule, pos + 27 + nseg, lacing))
        pos += size
    return out


def cut_ogg_opus(src: Path, work: Path, stem: str, max_bytes: int) -> list:
    """Cut an Ogg Opus file between pages into parts of at most max_bytes, without decoding anything.

    Each part gets the original OpusHead and OpusTags pages, then a run of whole audio pages whose
    granule positions are counted again from the part's start, page numbers renumbered, the last page
    marked end-of-stream and every checksum recomputed: so each part is a valid stream that plays on its
    own (RFC 7845). A cut is made only before a page that starts a new packet. ValueError if the file is
    not Ogg Opus as expected, so the caller can fall back to ffmpeg."""
    data = src.read_bytes()
    pages = ogg_pages(data)
    if len(pages) < 3 or data[pages[0][4]:pages[0][4] + 8] != b"OpusHead" or \
            data[pages[1][4]:pages[1][4] + 8] != b"OpusTags":
        raise ValueError("not an Ogg Opus file with its two header packets first")
    n_head = 2
    while n_head < len(pages) and pages[n_head - 1][5] and pages[n_head - 1][5][-1] == 255:
        n_head += 1          # the comment header continues on the next page
    head = b"".join(data[p[0]:p[0] + p[1]] for p in pages[:n_head])
    audio = pages[n_head:]
    budget = max_bytes - len(head)
    if budget < 4096 or any(p[1] > budget for p in audio):
        raise ValueError("pages are too large for parts of this size")
    groups, cur, size = [], [], 0
    for p in audio:
        if cur and size + p[1] > budget and not p[2] & 0x01:   # 0x01: the page continues a packet
            groups.append(cur)
            cur, size = [], 0
        cur.append(p)
        size += p[1]
    if cur:
        groups.append(cur)
    if any(sum(p[1] for p in g) > budget for g in groups):
        raise ValueError("a packet spans too many pages to cut within the size")
    out, base = [], 0
    for i, group in enumerate(groups, 1):
        body = bytearray()
        for j, (off, sz, flags, granule, _, _) in enumerate(group):
            page = bytearray(data[off:off + sz])
            last = j == len(group) - 1
            new_flags = (flags & ~0x04) | (0x04 if last else 0)
            new_granule = granule - base if granule != -1 else -1
            struct.pack_into("<BqII", page, 5, new_flags, new_granule,
                             _OGG.unpack_from(data, off)[4], n_head + j)
            struct.pack_into("<I", page, 22, 0)
            struct.pack_into("<I", page, 22, ogg_crc(page))
            body += page
        ends = [p[3] for p in group if p[3] != -1]
        base = ends[-1] if ends else base   # the next part counts its samples from here
        f = work / f"{stem} (part {i} of {len(groups)}).opus"
        f.write_bytes(head + bytes(body))
        out.append(f)
    return out


def split_audio(src: Path, work: Path, stem: str, max_bytes: int, duration: float, ffmpeg="ffmpeg") -> list:
    """Cut src into playable parts of at most max_bytes each, never re-encoding: between Ogg pages when it
    is Ogg Opus (all the pipeline's audio), else at packet boundaries with ffmpeg's stream copy."""
    try:
        return cut_ogg_opus(src, work, stem, max_bytes)
    except ValueError:
        pass
    size = src.stat().st_size
    seconds = max(60, int(duration * max_bytes * 0.88 / size)) if duration else 1800
    tmp = work / f".{stem[-40:]}.parts"
    for _ in range(6):
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        # bitexact: the Ogg muxer otherwise draws a random stream serial number, so the same cut would differ
        # in a few bytes each run and every planned SHA-256 would be stale
        cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y", "-i", str(src), "-map", "0:a:0",
               "-map_metadata", "-1", "-c", "copy", "-fflags", "+bitexact", "-f", "segment",
               "-segment_format_options", "fflags=+bitexact", "-segment_time", str(seconds),
               "-reset_timestamps", "1", str(tmp / "%03d.opus")]
        subprocess.run(cmd, check=True, timeout=900, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        parts = sorted(tmp.glob("*.opus"))
        if parts and all(p.stat().st_size <= max_bytes for p in parts):
            break
        seconds = max(30, int(seconds * 0.8))
    else:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"{src.name}: could not cut into parts of at most {max_bytes} bytes")
    out = []
    for i, p in enumerate(parts, 1):
        final = work / f"{stem} (part {i} of {len(parts)}).opus"
        p.replace(final)
        out.append(final)
    shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------- texts
def text_header(row, item, kind, extra="") -> str:
    lines = [row.get("title") or item, f"{(row.get('published') or '')[:10] or 'undated'} | item {item}"]
    if row.get("source_url"):
        lines.append(f"source: {row['source_url']}")
    lines.append(f"kind: {TEXT_KINDS[kind]}{extra}")
    bar = "=" * 78
    return "\n".join([bar, *lines, bar, ""])


def text_entries(paths, rows, person):
    """[(sort key, kind, header + text)] for one person: texts from the source, then transcripts made here."""
    out = []
    asr = latest_by_key(read_jsonl(paths.transcripts / "transcripts_manifest.jsonl"))
    for kind, folder in (("source", paths.pubtext / person), ("made", paths.transcripts / person)):
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*.txt")):
            item = f.stem
            extra = ""
            if kind == "made":
                rec = asr.get(item) or {}
                if rec.get("status") != "ok":
                    continue
                if rec.get("model"):
                    extra = f" ({rec.get('engine') or 'speech-to-text'}, {rec['model']})"
            row = rows.get(item, {})
            body = f.read_text(encoding="utf-8", errors="replace").strip()
            if body:
                out.append(((row.get("published") or "9999")[:10], kind, item, text_header(row, item, kind, extra) + body + "\n\n"))
    out.sort(key=lambda e: (e[1], e[0], e[2]))
    return out


def write_volumes(entries, work: Path, stem: str, max_bytes: int) -> list:
    """Pack the entries in order into volumes of at most max_bytes (UTF-8); returns the written paths."""
    vols, cur, size = [], [], 0
    for e in entries:
        n = len(e.encode("utf-8"))
        if cur and size + n > max_bytes:
            vols.append(cur)
            cur, size = [], 0
        cur.append(e)
        size += n
    if cur:
        vols.append(cur)
    out = []
    for i, vol in enumerate(vols, 1):
        f = work / f"{stem} - vol {i} of {len(vols)}.txt"
        f.parent.mkdir(parents=True, exist_ok=True)
        data = "".join(vol).encode("utf-8")
        if len(data) > max_bytes:   # one text alone is larger than a volume: cut it, it stays readable
            data = data[:max_bytes].decode("utf-8", errors="ignore").encode("utf-8")
        f.write_bytes(data)
        out.append(f)
    return out


# ---------------------------------------------------------------- plan
def cmd_plan(args, paths):
    out = Path(args.out)
    files = out / "files"
    files.mkdir(parents=True, exist_ok=True)
    max_bytes = int(args.max_mb * 1_000_000)
    names, feeds, rows, done = person_names(), feed_titles(paths), catalog_rows(paths), ledger(paths)
    places = [paths.root] + [Path(p) for p in args.audio_from]
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    plan, missing, failed, folders = [], [], [], set()

    def add(key, folder, path, title, mime, **extra):
        sha = sha256_file(path)
        prev = done.get(key)
        if prev and prev.get("sha256") == sha:
            return   # already on Drive, the same bytes
        folders.update(folder[:i] for i in range(1, len(folder) + 1))
        plan.append({"key": key, "folder": list(folder), "title": title, "path": str(path), "sha256": sha,
                     "bytes": path.stat().st_size, "mime": mime, "replaces": (prev or {}).get("drive_id", ""), **extra})

    if "audio" in args.kinds:
        audio = latest_by_key(read_jsonl(paths.audio / "audio_manifest.jsonl"))
        cuts = []   # big files, cut below in parallel: each cut is one ffmpeg, mostly waiting on the disk
        for item, rec in sorted(audio.items()):
            if rec.get("status") != "ok" or (only and rec.get("channel_dir") not in only):
                continue
            person = rec["channel_dir"]
            row = {**{k: rec.get(k, "") for k in ("lane", "published", "feed_key", "source_url")},
                   **{k: v for k, v in rows.get(item, {}).items() if v}, "item_id": item}
            row.setdefault("relation", "host" if (row.get("feed_key") or "").startswith("host-") else "own")
            src = find_audio(rec["path"], places, rec.get("bytes"))
            if src is None:
                missing.append(item)
                continue
            folder = (AUDIO_TOP, names.get(person, clean(person)), group_of(row, feeds))
            stem = audio_name(row, feeds)
            whole = f"audio:{item}"
            if src.stat().st_size <= max_bytes:
                add(whole, folder, src, f"{stem}.opus", "audio/ogg", item_id=item, person=person, part=1, parts=1)
                continue
            first = done.get(whole + "#1") or {}
            if first.get("source_sha256") and first["source_sha256"] == rec.get("sha256") and \
                    all(f"{whole}#{i}" in done for i in range(1, int(first.get("parts") or 1) + 1)):
                continue   # all its parts are on Drive already, cut from these same bytes
            cuts.append((whole, item, person, folder, stem, src, rec))

        def cut(job):
            _, _, person, _, stem, src, rec = job
            work = files / person
            work.mkdir(parents=True, exist_ok=True)
            try:
                return job, split_audio(src, work, stem, max_bytes, float(rec.get("duration_s") or 0) or
                                        (probe_duration(src) or 0), args.ffmpeg)
            except (OSError, RuntimeError, subprocess.SubprocessError) as err:
                return job, err

        with cf.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            for (whole, item, person, folder, stem, src, rec), parts in pool.map(cut, cuts):
                if isinstance(parts, Exception):
                    failed.append(f"{item}: {str(parts)[-160:]}")
                    continue
                for i, p in enumerate(parts, 1):
                    add(f"{whole}#{i}", folder, p, p.name, "audio/ogg", item_id=item, person=person, part=i,
                        parts=len(parts), source_sha256=rec.get("sha256", ""))

    if "text" in args.kinds:
        people = sorted({p.name for base in (paths.pubtext, paths.transcripts) if base.is_dir()
                         for p in base.iterdir() if p.is_dir()})
        for person in people:
            if only and person not in only:
                continue
            entries = text_entries(paths, rows, person)
            name = names.get(person, clean(person))
            for kind, label in TEXT_KINDS.items():
                mine = [e[3] for e in entries if e[1] == kind]
                if not mine:
                    continue
                work = files / "texts" / person
                for f in work.glob(f"{name} - {label} - vol *.txt"):
                    f.unlink()
                vols = write_volumes(mine, work, f"{name} - {label}", max_bytes)
                for i, f in enumerate(vols, 1):
                    add(f"text:{person}:{kind}:{i}of{len(vols)}", (TEXT_TOP, name), f, f.name, "text/plain",
                        person=person, part=i, parts=len(vols), texts=len(mine))

    # text volumes are rewritten as texts arrive: a volume on Drive that the new plan no longer has is trashed
    planned = {p["key"] for p in plan}
    people = {p.get("person") for p in plan if p["key"].startswith("text:")}
    trash = [{"key": k, "drive_id": v["drive_id"], "title": v.get("title", "")} for k, v in done.items()
             if k.startswith("text:") and k.split(":")[1] in people and k not in planned]
    trash += [{"key": p["key"], "drive_id": p["replaces"], "title": p["title"], "replaced": True}
              for p in plan if p.get("replaces")]
    with open(out / "trash.jsonl", "w", encoding="utf-8") as fh:
        for t in trash:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")

    known = {tuple(r["path"]): r["drive_id"] for r in (v for k, v in done.items() if k.startswith("folder:"))}
    known.update({tuple(k.split("/")): v for k, v in (x.split("=", 1) for x in args.known_folder)})
    with open(out / "folders.jsonl", "w", encoding="utf-8") as fh:
        for f in sorted(folders, key=lambda f: (len(f), f)):
            fh.write(json.dumps({"path": list(f), "title": f[-1], "parent": list(f[:-1]),
                                 "drive_id": known.get(f, "")}, ensure_ascii=False) + "\n")
    with open(out / "plan.jsonl", "w", encoding="utf-8") as fh:
        for p in plan:
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"[drive] plan: {len(plan)} file(s), {sum(p['bytes'] for p in plan) / 1e9:.2f} GB | folders needed "
          f"{len(folders)} ({sum(1 for f in folders if f not in known)} to create) | audio not found here "
          f"{len(missing)}" + (f" (e.g. {', '.join(missing[:3])}: pull them from the store first)" if missing else "")
          + (f" | could not cut {len(failed)}: " + "; ".join(failed[:3]) if failed else ""), file=sys.stderr)


def folder_ids(out: Path, paths) -> dict:
    ids = {}
    for r in read_jsonl(out / "folders.jsonl"):
        if r.get("drive_id"):
            ids[tuple(r["path"])] = r["drive_id"]
    for k, v in ledger(paths).items():
        if k.startswith("folder:"):
            ids[tuple(v["path"])] = v["drive_id"]
    return ids


def cmd_batches(args, paths):
    """Split the pending uploads whose folder exists into --n batch files, about equal in bytes."""
    out = Path(args.out)
    ids, done = folder_ids(out, paths), ledger(paths)
    todo = [p for p in read_jsonl(out / "plan.jsonl")
            if tuple(p["folder"]) in ids and done.get(p["key"], {}).get("sha256") != p["sha256"]]
    waiting = sum(1 for p in read_jsonl(out / "plan.jsonl") if tuple(p["folder"]) not in ids)
    bdir = out / "batches"
    shutil.rmtree(bdir, ignore_errors=True)
    bdir.mkdir(parents=True)
    loads = [[0, []] for _ in range(max(1, args.n))]
    for p in sorted(todo, key=lambda p: -p["bytes"]):
        slot = min(loads, key=lambda s: s[0])
        slot[0] += p["bytes"]
        slot[1].append(p)
    for i, (_, items) in enumerate(loads, 1):
        items.sort(key=lambda p: (p["folder"], p["title"]))
        with open(bdir / f"batch-{i:02d}.jsonl", "w", encoding="utf-8") as fh:
            for p in items:
                fh.write(json.dumps({"key": p["key"], "title": p["title"], "parentId": ids[tuple(p["folder"])],
                                     "ref": f"sha256:{p['sha256']}:{p['path']}", "mime": p["mime"]},
                                    ensure_ascii=False) + "\n")
    print(f"[drive] {len(todo)} upload(s) in {len(loads)} batch file(s) under {bdir}"
          + (f"; {waiting} wait for their folder to be created" if waiting else ""), file=sys.stderr)


def cmd_record(args, paths):
    """Merge uploaders' results ({"key", "id"} or {"path", "id"} for folders) into the ledger."""
    out = Path(args.out)
    plan = {p["key"]: p for p in read_jsonl(out / "plan.jsonl")}
    folders = {tuple(r["path"]): r for r in read_jsonl(out / "folders.jsonl")}
    have = ledger(paths)
    n_files = n_folders = unknown = 0
    for f in args.results:
        for r in read_jsonl(Path(f)):
            drive_id = r.get("id") or r.get("drive_id")
            if not drive_id:
                continue
            if r.get("path") and not r.get("key"):
                path = tuple(r["path"]) if isinstance(r["path"], list) else tuple(str(r["path"]).split("/"))
                key = "folder:" + "/".join(path)
                ours = path in folders or (path and path[0] in (AUDIO_TOP, TEXT_TOP))   # made before the plan ended
                if ours and have.get(key, {}).get("drive_id") != drive_id:
                    append_jsonl(paths.root / LEDGER, {"key": key, "kind": "folder", "path": list(path),
                                                        "drive_id": drive_id, "at": utc_now()})
                    have[key] = {"drive_id": drive_id, "path": list(path)}
                    n_folders += 1
                continue
            p = plan.get(r.get("key"))
            if p is None:
                unknown += 1
                continue
            if have.get(p["key"], {}).get("drive_id") == drive_id:
                continue
            append_jsonl(paths.root / LEDGER, {**{k: v for k, v in p.items() if k != "path"}, "drive_id": drive_id,
                                                "uploaded_at": utc_now()})
            have[p["key"]] = {"drive_id": drive_id}
            n_files += 1
    print(f"[drive] recorded {n_files} file(s) and {n_folders} folder(s)"
          + (f"; {unknown} result line(s) matched nothing in the plan" if unknown else ""), file=sys.stderr)


def cmd_status(args, paths):
    out = Path(args.out)
    done = ledger(paths)
    plan = list(read_jsonl(out / "plan.jsonl"))
    left = [p for p in plan if done.get(p["key"], {}).get("sha256") != p["sha256"]]
    on_drive = [v for k, v in done.items() if not k.startswith("folder:")]
    print(json.dumps({"planned": len(plan), "planned_gb": round(sum(p["bytes"] for p in plan) / 1e9, 2),
                      "left": len(left), "left_gb": round(sum(p["bytes"] for p in left) / 1e9, 2),
                      "on_drive_files": len(on_drive),
                      "on_drive_gb": round(sum(v.get("bytes", 0) for v in on_drive) / 1e9, 2),
                      "folders": sum(1 for k in done if k.startswith("folder:"))}, indent=1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=("plan", "batches", "record", "status"))
    ap.add_argument("results", nargs="*", help="record: result files written by the uploaders")
    add_root_arg(ap)
    ap.add_argument("--out", required=True, help="staging folder (outside any Git checkout)")
    ap.add_argument("--audio-from", action="append", default=[],
                    help="another folder holding audio/<person>/<id>.opus, e.g. one filled by sync_archive.py pull")
    ap.add_argument("--kinds", default="audio,text", help="audio, text")
    ap.add_argument("--only", default="", help="comma-separated person ids")
    ap.add_argument("--max-mb", type=float, default=DEFAULT_MAX_MB, help="largest file to upload (default 7.3)")
    ap.add_argument("--known-folder", action="append", default=[],
                    help='a Drive folder that already exists: "04 Audio=<folder id>" (repeatable)')
    ap.add_argument("--n", type=int, default=6, help="batches: number of batch files")
    ap.add_argument("--jobs", type=int, default=3, help="plan: audio files cut at the same time")
    ap.add_argument("--ffmpeg", default="ffmpeg")
    args = ap.parse_args()
    args.kinds = {k.strip() for k in args.kinds.split(",") if k.strip()}
    paths = layout(ensure_outside_git(args.root))
    ensure_outside_git(args.out)
    {"plan": cmd_plan, "batches": cmd_batches, "record": cmd_record, "status": cmd_status}[args.command](args, paths)


if __name__ == "__main__":
    main()
