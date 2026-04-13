#!/usr/bin/env python3
"""
Batch upscale textures using Real-ESRGAN ncnn-vulkan.
Targets max 2048px output, applies pngquant compression.

Usage:
    python tools/batch_upscale.py <input_dir> <output_dir>
    python tools/batch_upscale.py temp/output/dlc_textures temp/output/dlc_hd
"""

import subprocess
import sys
import os
import glob
import time
from PIL import Image
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
REALESRGAN = os.path.join(TEMP_DIR, 'realesrgan', 'realesrgan-ncnn-vulkan.exe')
MODELS_DIR = os.path.join(TEMP_DIR, 'realesrgan', 'models')
PNGQUANT = os.path.join(TEMP_DIR, 'pngquant.exe')

# Model config
MODEL = 'realesr-animevideov3'
TILE = 64
MAX_OUTPUT = 2048


def get_scale(width, height):
    """Choose upscale ratio to target max ~2048px."""
    max_dim = max(width, height)
    if max_dim >= 2048:
        return 2  # already large, 2x then downscale
    elif max_dim >= 1024:
        return 2  # 1024->2048
    elif max_dim >= 512:
        return 4  # 512->2048
    else:
        return 4  # small textures, 4x


def upscale_one(input_path, output_path, scale):
    """Run Real-ESRGAN on a single image."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = [
        REALESRGAN,
        '-i', input_path,
        '-o', output_path,
        '-n', MODEL,
        '-s', str(scale),
        '-t', str(TILE),
        '-m', MODELS_DIR,
        '-f', 'png',
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        # Try with smaller tile
        cmd[cmd.index(str(TILE))] = '32'
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            return False

    # Downscale if exceeds max
    if os.path.exists(output_path):
        img = Image.open(output_path)
        if max(img.width, img.height) > MAX_OUTPUT:
            ratio = MAX_OUTPUT / max(img.width, img.height)
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            img.save(output_path)
        img.close()

    return os.path.exists(output_path)


def compress_png(path):
    """Apply pngquant compression if available."""
    if not os.path.exists(PNGQUANT):
        return
    try:
        subprocess.run(
            [PNGQUANT, '--force', '--quality', '70-95', '--strip',
             '--output', path, path],
            capture_output=True, timeout=30
        )
    except OSError:
        pass  # pngquant binary incompatible, skip compression


def batch_upscale(input_dir, output_dir):
    """Batch upscale all PNG files."""
    pngs = sorted(glob.glob(os.path.join(input_dir, '**', '*.png'), recursive=True))
    total = len(pngs)

    # Filter out font/shadow textures
    skip_patterns = ['font.png', 'font2a.png', 'font2b.png', 'shadow.png', 'common_tex.png']
    pngs = [p for p in pngs if not any(p.endswith(s) for s in skip_patterns)]

    print(f"Upscaling {len(pngs)} textures (skipped {total - len(pngs)} font/util)")
    print(f"Model: {MODEL}, tile: {TILE}, max output: {MAX_OUTPUT}")
    print()

    success = 0
    errors = 0
    start_time = time.time()

    for idx, png_path in enumerate(pngs, 1):
        rel = os.path.relpath(png_path, input_dir)
        out_path = os.path.join(output_dir, rel)

        # Skip if already done
        if os.path.exists(out_path):
            img = Image.open(out_path)
            if img.width > 100:  # valid output
                img.close()
                success += 1
                print(f"  [{idx}/{len(pngs)}] {rel} (cached)")
                continue
            img.close()

        # Get source dimensions
        src = Image.open(png_path)
        w, h = src.width, src.height
        src.close()

        scale = get_scale(w, h)
        result_dim = f"{w}x{h} -> {min(w*scale, MAX_OUTPUT)}x{min(h*scale, MAX_OUTPUT)}"

        ok = upscale_one(png_path, out_path, scale)

        if ok:
            compress_png(out_path)
            out_img = Image.open(out_path)
            result_dim = f"{w}x{h} -> {out_img.width}x{out_img.height}"
            out_sz = os.path.getsize(out_path) // 1024
            out_img.close()
            success += 1
            print(f"  [{idx}/{len(pngs)}] {rel}: {result_dim} ({out_sz}KB)")
        else:
            errors += 1
            print(f"  [{idx}/{len(pngs)}] {rel}: FAILED")

        # ETA
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            rate = elapsed / idx
            remaining = rate * (len(pngs) - idx)
            print(f"  --- {idx}/{len(pngs)} done, ETA: {remaining:.0f}s ({remaining/60:.1f}min) ---")

    elapsed = time.time() - start_time
    print()
    print(f"Done: {success} success, {errors} errors in {elapsed:.0f}s ({elapsed/60:.1f}min)")

    # Total output size
    total_size = sum(
        os.path.getsize(f) for f in glob.glob(os.path.join(output_dir, '**', '*.png'), recursive=True)
    )
    print(f"Output size: {total_size // 1024 // 1024}MB")


def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/batch_upscale.py <input_dir> <output_dir>")
        sys.exit(1)

    batch_upscale(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()
