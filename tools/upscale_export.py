#!/usr/bin/env python3
"""Upscale Vita3K-exported textures to FHD using Real-ESRGAN ncnn-vulkan.

Targets max dimension 1920px (FHD short side). Output is local-only,
gitignored under `upscaled/`. Font hashes and hand-edited Korean UI
textures are skipped automatically.

Usage:
    python tools/upscale_export.py                   # default Vita3K export → upscaled/
    python tools/upscale_export.py --dry-run         # list what would happen
    python tools/upscale_export.py --install         # also copy to Vita3K import/
    python tools/upscale_export.py -i SRC -o OUT     # custom paths
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_EXPORT = Path.home() / "Library/Application Support/Vita3K/Vita3K/textures/export"
DEFAULT_IMPORT = Path.home() / "Library/Application Support/Vita3K/Vita3K/textures/import"
DEFAULT_OUTPUT = REPO_ROOT / "upscaled"

REALESRGAN_DIR = REPO_ROOT / "temp" / "realesrgan"
BIN_NAME = "realesrgan-ncnn-vulkan.exe" if platform.system() == "Windows" else "realesrgan-ncnn-vulkan"
REALESRGAN_BIN = REALESRGAN_DIR / BIN_NAME
MODELS_DIR = REALESRGAN_DIR / "models"

MODEL = "realesr-animevideov3"
TILE = 64
TARGET_MAX = 1920  # FHD short side

KR_UI_DIR = REPO_ROOT / "kr_textures" / "ui"
FONT_HASHES_FILE = REPO_ROOT / "tools" / ".font_hashes.json"


def load_skip_set() -> set[str]:
    """Hashes (with .png) that must NOT be upscaled."""
    skip: set[str] = set()
    if FONT_HASHES_FILE.exists():
        skip.update(json.loads(FONT_HASHES_FILE.read_text()))
    if KR_UI_DIR.exists():
        skip.update(p.name for p in KR_UI_DIR.glob("*.png"))
    return skip


def pick_scale(width: int, height: int) -> int:
    """Choose 2/3/4 so output max-dim is closest to (but <=) TARGET_MAX after cap."""
    cur = max(width, height)
    if cur >= TARGET_MAX:
        return 2  # already large; we'll downscale post
    for s in (4, 3, 2):
        if cur * s <= TARGET_MAX * 1.4:  # accept a bit over to allow downscale-cap
            return s
    return 2


def upscale_one(src: Path, dst: Path, scale: int) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(REALESRGAN_BIN),
        "-i", str(src),
        "-o", str(dst),
        "-n", MODEL,
        "-s", str(scale),
        "-t", str(TILE),
        "-m", str(MODELS_DIR),
        "-f", "png",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        cmd[cmd.index(str(TILE))] = "32"
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if res.returncode != 0:
            return False

    if not dst.exists():
        return False

    img = Image.open(dst)
    if max(img.width, img.height) > TARGET_MAX:
        ratio = TARGET_MAX / max(img.width, img.height)
        new_size = (round(img.width * ratio), round(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        img.save(dst, optimize=True)
    img.close()
    return True


def collect_inputs(src_root: Path) -> list[Path]:
    return sorted(p for p in src_root.rglob("*.png") if p.is_file())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", type=Path, default=DEFAULT_EXPORT)
    ap.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--install-dir", type=Path, default=DEFAULT_IMPORT,
                    help="Vita3K import dir (used with --install)")
    ap.add_argument("--install", action="store_true", help="Also copy outputs to Vita3K import dir")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Process at most N files (sample run)")
    ap.add_argument("--force", action="store_true", help="Re-upscale even if cached output exists")
    args = ap.parse_args()

    if not REALESRGAN_BIN.exists():
        print(f"ERROR: {REALESRGAN_BIN} not found. Place Real-ESRGAN ncnn-vulkan there.", file=sys.stderr)
        return 1
    if not args.input.exists():
        print(f"ERROR: input dir {args.input} missing", file=sys.stderr)
        return 1

    skip = load_skip_set()
    inputs = collect_inputs(args.input)
    print(f"Found {len(inputs)} PNG(s) under {args.input}")
    print(f"Skip list: {len(skip)} hashes (fonts + kr_textures/ui)")

    todo: list[tuple[Path, Path]] = []
    skipped_skip = 0
    skipped_cached = 0
    for src in inputs:
        if src.name in skip:
            skipped_skip += 1
            continue
        rel = src.relative_to(args.input)
        dst = args.output / rel
        if dst.exists() and not args.force:
            skipped_cached += 1
            continue
        todo.append((src, dst))

    if args.limit:
        todo = todo[: args.limit]

    print(f"  skip-listed: {skipped_skip}")
    print(f"  cached     : {skipped_cached}")
    print(f"  to upscale : {len(todo)}")

    if args.dry_run:
        for src, dst in todo[:20]:
            print(f"  DRY {src.name} -> {dst.relative_to(REPO_ROOT)}")
        if len(todo) > 20:
            print(f"  ... and {len(todo) - 20} more")
        return 0

    args.output.mkdir(parents=True, exist_ok=True)

    ok = fail = 0
    start = time.time()
    for idx, (src, dst) in enumerate(todo, 1):
        with Image.open(src) as img:
            w, h = img.size
        scale = pick_scale(w, h)
        success = upscale_one(src, dst, scale)
        if success:
            with Image.open(dst) as out:
                ow, oh = out.size
            size_kb = dst.stat().st_size // 1024
            print(f"  [{idx}/{len(todo)}] {src.name}: {w}x{h} ->{scale}x-> {ow}x{oh} ({size_kb}KB)")
            ok += 1
        else:
            print(f"  [{idx}/{len(todo)}] {src.name}: FAILED")
            fail += 1
        if idx % 10 == 0:
            elapsed = time.time() - start
            eta = elapsed / idx * (len(todo) - idx)
            print(f"  --- {idx}/{len(todo)}, ETA {eta:.0f}s ({eta/60:.1f}min) ---")

    elapsed = time.time() - start
    print(f"\nDone: {ok} ok, {fail} failed in {elapsed:.0f}s")

    if args.install and ok:
        installed = 0
        for _, dst in todo:
            if not dst.exists():
                continue
            rel = dst.relative_to(args.output)
            target = args.install_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, target)
            installed += 1
        print(f"Installed to {args.install_dir}: {installed} file(s)")

    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
