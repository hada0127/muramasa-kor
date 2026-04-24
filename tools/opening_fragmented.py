"""Split Korean narration across multiple aspect-matched carriers per line.
Each carrier holds 1-3 chars so each char can be drawn at maximum size
within the carrier's UV rect. Atlas-only (no MBS modification).
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20

MAIN_COLOR = 0xFFFFFFFF
SHADOW_COLOR = 0xFF402000
RED_COLOR = 0xFF0000FF
LARGE_CONTAINER_CARRIERS = {90, 96, 111, 114}

# Per-carrier text fragment. Keys are carrier IDs; values are the chunk
# of Korean text to render. Unlisted carriers are cleared.
#
# Text layout (screen x from left to right within each line):
#  Line 0 (y~170-213): 115 (x 196-278 small) | 109 (x 551-762)
#  Line 1 (y~240-278): 97  (x 116-397)       | 100 (685-734) | 103 (tiny)
#  Line 2 (y~314-347): 91  (x 19-233)        | 94  (547-728)
#  Line 3 (y~384-417): 88  (x 529-744)
CARRIER_TEXT = {
    # v38 — embrace height limit: line 1 as title card with carrier 80
    # emphasis, other lines as poetic short supporting fragments.
    # Per codex+gemini review: "마검 무라마사" in carrier 80 gets max size.
    # Line 0 — title card
    115: "흩어진",
    80:  "마검 무라마사",
    109: "피를 찾네",
    # Line 1 — transition
    97:  "칼집을 뽑은",
    100: "순간",
    # Line 2 — core action
    91:  "피에",
    94:  "굶주린다",
    # Line 3 — closer
    88:  "보라",
}


def quad_offset(idx: int) -> int:
    return MBS_TABLE_OFFSET + idx * QUAD_SIZE


def read_quad(src: bytes, idx: int):
    base = quad_offset(idx)
    return [struct.unpack_from("<Iffff", src, base + i * VERTEX_SIZE) for i in range(4)]


def uv_rect(vs) -> tuple[int, int, int, int]:
    xs = [v[1] for v in vs]; ys = [v[2] for v in vs]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def build_atlas(source_mbs: Path, source_atlas: Path, font_path: Path,
                output: Path) -> dict:
    src = source_mbs.read_bytes()
    atlas = Image.open(source_atlas).convert("RGBA")
    arr = np.array(atlas)

    # Clear every narration-range carrier UV region except those in CARRIER_TEXT
    for idx in range(40, 116):
        vs = read_quad(src, idx)
        color = vs[0][0]
        ux0, uy0, ux1, uy1 = uv_rect(vs)
        if ux0 < 0 or uy0 < 0 or ux1 > 512 or uy1 > 512: continue
        if ux0 == ux1 or uy0 == uy1: continue

        # Clear regions we want to hide (everything except winners)
        if idx in LARGE_CONTAINER_CARRIERS:
            arr[uy0:uy1, ux0:ux1, 3] = 0
            continue
        if color in (SHADOW_COLOR, RED_COLOR):
            arr[uy0:uy1, ux0:ux1, 3] = 0
            continue
        if color == MAIN_COLOR and idx not in CARRIER_TEXT:
            arr[uy0:uy1, ux0:ux1, 3] = 0
            continue

    atlas = Image.fromarray(arr, mode="RGBA")
    draw = ImageDraw.Draw(atlas)

    font_sizes = {}
    for idx, text in CARRIER_TEXT.items():
        vs = read_quad(src, idx)
        ux0, uy0, ux1, uy1 = uv_rect(vs)
        w = ux1 - ux0; h = uy1 - uy0
        if w <= 2 or h <= 2: continue

        # Clear this carrier's UV region first
        clear = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        atlas.paste(clear, (ux0, uy0))
        draw = ImageDraw.Draw(atlas)

        # Find max font size that fits the text into this carrier UV rect
        size = h
        font = None
        while size >= 12:
            f = ImageFont.truetype(str(font_path), size=size)
            stroke = max(2, size // 8)
            b = f.getbbox(text, stroke_width=stroke)
            tw = b[2] - b[0]; th = b[3] - b[1]
            if tw <= w - 2 and th <= h - 2:
                font = f; break
            size -= 1
        if font is None:
            font = ImageFont.truetype(str(font_path), size=12)
            size = 12
        stroke = max(2, size // 8)
        b = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        tw = b[2] - b[0]; th = b[3] - b[1]
        tx = ux0 + (w - tw) // 2 - b[0]
        ty = uy0 + (h - th) // 2 - b[1]
        draw.text((tx, ty), text, font=font,
                  fill=(255, 255, 255, 255),
                  stroke_width=stroke, stroke_fill=(255, 255, 255, 255))
        font_sizes[idx] = size

    output.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output)
    return {"font_sizes": font_sizes, "carriers_used": len(CARRIER_TEXT)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", default="temp/cpk_extract/_US/GUI/opening01.mbs")
    ap.add_argument("--source-atlas", default="C:/game/vita3k/textures/export/79C935AA47DD1810.png")
    ap.add_argument("--output", default="temp/opening_test/atlas.png")
    ap.add_argument("--font", default="fonts/Griun_PolSensibility-Rg.ttf")
    args = ap.parse_args()
    info = build_atlas(Path(args.source_mbs), Path(args.source_atlas),
                       Path(args.font), Path(args.output))
    print(f"carriers: {info['carriers_used']}")
    print(f"font sizes: {info['font_sizes']}")


if __name__ == "__main__":
    main()
