#!/usr/bin/env python3
"""Check this machine before a long run. Prints what is installed, what is missing and how to fix it.

    python3 pipeline/doctor.py                    # checks only; nothing is downloaded or sent anywhere
    python3 pipeline/doctor.py --root D:\\et-private   # also checks the data folder and its free space

Exit code 0 when everything needed is present (warnings allowed), 1 when something required is missing.
"""
from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import add_root_arg, ensure_outside_git, run_cmd  # noqa: E402

OK, WARN, MISSING = "ok", "WARN", "MISSING"


def version_of(module):
    try:
        mod = importlib.import_module(module)
        return getattr(mod, "__version__", None) or getattr(getattr(mod, "version", None), "__version__", "installed")
    except Exception as exc:  # noqa: BLE001 - a broken install is reported, not raised
        return f"import failed: {type(exc).__name__}"


def check(root, need_gb):
    rows = []

    def add(name, status, detail, fix=""):
        rows.append((name, status, detail, fix))

    py = sys.version_info
    add("python", OK if py >= (3, 9) else MISSING, f"{py.major}.{py.minor}.{py.micro}", "Python 3.9 or newer")
    for tool in ("ffmpeg", "ffprobe"):
        found = shutil.which(tool)
        add(tool, OK if found else MISSING, found or "not on PATH",
            "Windows: winget install Gyan.FFmpeg | macOS: brew install ffmpeg | Linux: apt install ffmpeg")
    if shutil.which("ffmpeg"):
        code, out, _ = run_cmd(["ffmpeg", "-hide_banner", "-encoders"], 30)
        add("ffmpeg libopus", OK if code == 0 and "libopus" in out else MISSING,
            "encoder present" if "libopus" in out else "no libopus encoder", "use a full ffmpeg build")
    ytdlp = shutil.which("yt-dlp")
    if ytdlp:
        code, out, _ = run_cmd([ytdlp, "--version"], 30)
        add("yt-dlp", OK, out.strip() if code == 0 else "found", "")
    else:
        add("yt-dlp", MISSING, "not on PATH", "pip install -r pipeline/requirements.txt (and activate that environment)")
    js = [name for name in ("deno", "node", "bun") if shutil.which(name)]
    add("JavaScript runtime", OK if "deno" in js else WARN if js else MISSING, ", ".join(js) or "none found",
        "pip install deno   (yt-dlp uses deno by default; node/bun need --js-runtimes)")
    add("yt-dlp-ejs", OK if version_of("yt_dlp_ejs") and "failed" not in str(version_of("yt_dlp_ejs")) else WARN,
        str(version_of("yt_dlp_ejs")), "pip install yt-dlp-ejs")
    fw = version_of("faster_whisper")
    add("faster-whisper", OK if "failed" not in str(fw) else MISSING, str(fw), "pip install faster-whisper")
    add("numpy", OK if "failed" not in str(version_of("numpy")) else MISSING, str(version_of("numpy")), "pip install numpy")
    try:
        ct2 = importlib.import_module("ctranslate2")
        gpus = ct2.get_cuda_device_count()
        add("GPU for transcription", OK if gpus else WARN, f"{gpus} CUDA device(s) visible to CTranslate2",
            "without a GPU, large models are far too slow; see the GPU section of the faster-whisper README "
            "(cuBLAS for CUDA 12 and cuDNN 9)")
    except Exception:  # noqa: BLE001
        add("GPU for transcription", WARN, "ctranslate2 not importable", "pip install faster-whisper")
    smi = shutil.which("nvidia-smi")
    if smi:
        code, out, _ = run_cmd([smi, "--query-gpu=name,memory.total", "--format=csv,noheader"], 30)
        add("nvidia-smi", OK, out.strip().replace("\n", " | ") if code == 0 else "found")
    if root is not None:
        try:
            resolved = ensure_outside_git(root)
            add("data folder", OK, f"{resolved} (outside any Git checkout)")
        except SystemExit as exc:
            add("data folder", MISSING, str(exc).split(":")[0], "pass --root with a folder outside the repository")
            resolved = None
        probe = Path(root).expanduser()
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        free = shutil.disk_usage(probe).free / 1e9
        add("free disk", OK if free > need_gb else WARN, f"{free:.0f} GB free, about {need_gb:.0f} GB needed",
            "choose another drive with --root")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_root_arg(ap)
    ap.add_argument("--need-gb", type=float, default=50, help="space you plan to use (Bashar-75 needs about 2 GB; the full list about 160 GB)")
    args = ap.parse_args()
    rows = check(args.root, args.need_gb)
    width = max(len(r[0]) for r in rows)
    for name, status, detail, fix in rows:
        print(f"{status:<8}{name:<{width}}  {detail}" + (f"\n{'':<{8 + width + 2}}-> {fix}" if status != OK and fix else ""))
    sys.exit(1 if any(r[1] == MISSING for r in rows) else 0)


if __name__ == "__main__":
    main()
