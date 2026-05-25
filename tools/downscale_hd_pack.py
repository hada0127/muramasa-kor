#!/usr/bin/env python3
"""Downscale community HD texture pack (Plaidray/xibalva) to QHD and optimize.

Source : ~/Downloads/Muramasa Complete 2.0/PCSE00240/Best/  (UHD, up to 8K)
Output : <repo>/upscaled/                                   (QHD, max 2560px)

Pipeline per file:
  1. Skip if hash is a font texture (.font_hashes.json) or hand-edited Korean UI.
  2. If max(w,h) > 2560: Lanczos downscale so max dim == 2560 (preserve aspect).
     Otherwise: copy as-is.
  3. Run pngquant (lossy quantization, alpha preserved, RGBA8 output).

Notes:
  - Output overwrites existing files in upscaled/ for the same hash.
  - upscaled/ is gitignored (see .gitignore).
  - Parallelized with ProcessPoolExecutor.

Usage:
    python tools/downscale_hd_pack.py                # full run
    python tools/downscale_hd_pack.py --dry-run      # list actions only
    python tools/downscale_hd_pack.py --limit 20     # quick test
    python tools/downscale_hd_pack.py -j 4           # 4 parallel workers
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SRC = Path.home() / "Downloads" / "Muramasa Complete 2.0" / "PCSE00240" / "Best"
DEFAULT_OUT = REPO_ROOT / "upscaled"

KR_UI_DIR = REPO_ROOT / "textures/kr" / "ui"
FONT_HASHES_FILE = REPO_ROOT / "tools" / ".font_hashes.json"

TARGET_MAX = 2560  # QHD long side cap

# pngquant settings — quality range tuned for game textures with alpha.
PNGQUANT_QUALITY = "70-95"
PNGQUANT_SPEED = "3"


def load_skip_set() -> set[str]:
    skip: set[str] = set()
    if FONT_HASHES_FILE.exists():
        try:
            data = json.loads(FONT_HASHES_FILE.read_text())
            if isinstance(data, list):
                skip.update(data)
            elif isinstance(data, dict):
                skip.update(data.keys())
        except Exception as e:
            print(f"warning: failed to read {FONT_HASHES_FILE}: {e}", file=sys.stderr)
    if KR_UI_DIR.exists():
        skip.update(p.name for p in KR_UI_DIR.glob("*.png"))
    return skip


def downscale_target(w: int, h: int, cap: int) -> tuple[int, int] | None:
    """Return (new_w, new_h) preserving aspect, max dim == cap. None if no downscale needed."""
    m = max(w, h)
    if m <= cap:
        return None
    ratio = cap / m
    return (max(1, round(w * ratio)), max(1, round(h * ratio)))


def process_one(src_path: str, dst_path: str, cap: int, q_range: str, speed: str) -> dict:
    """Returns {status, src_size, dst_size, dims, msg}."""
    src = Path(src_path)
    dst = Path(dst_path)
    src_size = src.stat().st_size

    try:
        with Image.open(src) as img:
            if img.mode not in ("RGBA", "RGB", "LA", "L", "P"):
                img = img.convert("RGBA")
            elif img.mode != "RGBA":
                # Game textures usually need alpha; force RGBA for consistent pngquant output.
                img = img.convert("RGBA")
            w, h = img.size
            tgt = downscale_target(w, h, cap)
            tmp = dst.with_suffix(".tmp.png")
            dst.parent.mkdir(parents=True, exist_ok=True)
            if tgt is None:
                # Save through PIL to a tmp PNG (re-saved baseline before pngquant).
                img.save(tmp, format="PNG", optimize=False)
                final_dims = (w, h)
            else:
                resized = img.resize(tgt, Image.Resampling.LANCZOS)
                resized.save(tmp, format="PNG", optimize=False)
                final_dims = tgt
    except Exception as e:
        return {"status": "error", "src": src.name, "msg": f"PIL: {e}"}

    # pngquant lossy compression (writes to dst). Falls back to renaming tmp on failure.
    try:
        cmd = [
            "pngquant",
            "--force",
            "--strip",
            "--quality", q_range,
            "--speed", speed,
            "--output", str(dst),
            "--",
            str(tmp),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode == 0 and dst.exists():
            tmp.unlink(missing_ok=True)
        else:
            # quality below threshold (returncode 99) or other failure → keep PIL PNG as-is.
            shutil.move(str(tmp), str(dst))
    except FileNotFoundError:
        shutil.move(str(tmp), str(dst))
        return {"status": "error", "src": src.name, "msg": "pngquant not found"}
    except subprocess.TimeoutExpired:
        if tmp.exists():
            shutil.move(str(tmp), str(dst))
        return {"status": "error", "src": src.name, "msg": "pngquant timeout"}

    dst_size = dst.stat().st_size
    return {
        "status": "ok",
        "src": src.name,
        "src_size": src_size,
        "dst_size": dst_size,
        "dims": final_dims,
        "downscaled": downscale_target(*Image.open(src).size, cap) is not None,
    }


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--input", default=str(DEFAULT_SRC), help="HD pack source folder")
    ap.add_argument("-o", "--output", default=str(DEFAULT_OUT), help="Output folder")
    ap.add_argument("--cap", type=int, default=TARGET_MAX, help=f"Long-side cap (default {TARGET_MAX})")
    ap.add_argument("--quality", default=PNGQUANT_QUALITY, help="pngquant quality range")
    ap.add_argument("--speed", default=PNGQUANT_SPEED, help="pngquant speed (1-11, default 3)")
    ap.add_argument("-j", "--jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2),
                    help="Parallel workers")
    ap.add_argument("--limit", type=int, default=0, help="Process only first N files (debug)")
    ap.add_argument("--dry-run", action="store_true", help="List actions only")
    ap.add_argument("--force", action="store_true", help="Reprocess even if dst exists")
    args = ap.parse_args()

    src_dir = Path(args.input)
    out_dir = Path(args.output)

    if not src_dir.is_dir():
        print(f"error: source not found: {src_dir}", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    skip = load_skip_set()

    all_pngs = sorted(p for p in src_dir.iterdir() if p.suffix.lower() == ".png")
    if not all_pngs:
        print(f"error: no PNGs in {src_dir}", file=sys.stderr)
        return 2

    todo: list[tuple[Path, Path]] = []
    skipped_font = skipped_kr = skipped_done = 0
    for p in all_pngs:
        if p.name in skip:
            if p.name in (KR_UI_DIR.glob("*.png") if KR_UI_DIR.exists() else []):
                skipped_kr += 1
            else:
                skipped_font += 1
            continue
        dst = out_dir / p.name
        if dst.exists() and not args.force:
            skipped_done += 1
            continue
        todo.append((p, dst))

    if args.limit:
        todo = todo[: args.limit]

    print(f"source: {src_dir}")
    print(f"output: {out_dir}")
    print(f"cap   : {args.cap}px (QHD long side)")
    print(f"total in source : {len(all_pngs)}")
    print(f"  skipped(font) : {skipped_font}")
    print(f"  skipped(kr_ui): {skipped_kr}")
    print(f"  skipped(exist): {skipped_done}{'  (use --force to redo)' if skipped_done else ''}")
    print(f"  to process    : {len(todo)}")
    if args.dry_run or not todo:
        if todo[:5]:
            print("\nfirst few:")
            for s, d in todo[:5]:
                with Image.open(s) as im:
                    tgt = downscale_target(*im.size, args.cap) or im.size
                print(f"  {s.name} {im.size} -> {tgt}")
        return 0

    t0 = time.time()
    ok = err = 0
    sum_src = sum_dst = 0

    with ProcessPoolExecutor(max_workers=args.jobs) as ex:
        futs = {
            ex.submit(process_one, str(s), str(d), args.cap, args.quality, args.speed): s
            for s, d in todo
        }
        for i, fut in enumerate(as_completed(futs), 1):
            res = fut.result()
            if res["status"] == "ok":
                ok += 1
                sum_src += res["src_size"]
                sum_dst += res["dst_size"]
                if i % 50 == 0 or i == len(futs):
                    pct = 100 * (1 - sum_dst / max(1, sum_src))
                    elapsed = time.time() - t0
                    eta = elapsed / i * (len(futs) - i)
                    print(f"  [{i:4d}/{len(futs)}] ok={ok} err={err}  "
                          f"in={fmt_bytes(sum_src)} out={fmt_bytes(sum_dst)} "
                          f"saved={pct:.1f}%  eta={eta:.0f}s")
            else:
                err += 1
                print(f"  ERR {res['src']}: {res.get('msg', '?')}", file=sys.stderr)

    dt = time.time() - t0
    print()
    print(f"done in {dt:.1f}s  ({ok} ok, {err} err)")
    if sum_src:
        print(f"input total : {fmt_bytes(sum_src)}")
        print(f"output total: {fmt_bytes(sum_dst)}")
        print(f"saved       : {100 * (1 - sum_dst / sum_src):.1f}%")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
