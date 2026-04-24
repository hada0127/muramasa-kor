"""Minimal MBS change to make Korean narration larger: for 4 winning
carriers, only rewrite the sx/sy per vertex to stretch to a full-width
screen rect. Keep color, f1, f2 (UV) unchanged — this preserves the
original vertex-to-corner pairing so GPU rendering behaves identically,
just at a larger scale.

All other narration carriers (40..115) are hidden.
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

# Line layout: (carrier_idx, new_screen_rect_top_left_origin)
LINE_LAYOUT = {
    0: (109, (60, 165, 900, 215)),
    1: (97,  (60, 225, 900, 275)),
    2: (91,  (60, 295, 900, 350)),
    3: (88,  (60, 365, 900, 420)),
}

# Korean texts (for atlas drawing)
KOREAN_SENTENCES = [
    "헤아릴 수 없이 흩어진 마검들",
    "칼집에서 뽑히는 순간",
    "피에 굶주린 듯 생명을 탐한다",
    "스러진 이들의 운명을 보라",
]


def quad_offset(idx: int) -> int:
    return MBS_TABLE_OFFSET + idx * QUAD_SIZE


def read_quad(blob: bytes, idx: int):
    base = quad_offset(idx)
    return [struct.unpack_from("<Iffff", blob, base + i * VERTEX_SIZE) for i in range(4)]


def hide_quad(blob: bytearray, idx: int) -> None:
    verts = [
        (0x00000000, 0.0, 0.0, -2080.0, 1872.0),
        (0x00000000, 0.0, 1.0, -2078.0, 1872.0),
        (0x00000000, 1.0, 1.0, -2078.0, 1870.0),
        (0x00000000, 1.0, 0.0, -2080.0, 1870.0),
    ]
    base = quad_offset(idx)
    for i, v in enumerate(verts):
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, *v)


def stretch_carrier_screen(blob: bytearray, idx: int,
                            new_screen_rect: tuple[int, int, int, int]) -> None:
    """Replace each vertex's sx/sy with the new corresponding corner, keeping
    color/f1/f2 unchanged. The corner role of each vertex is detected from
    its original screen coordinates (which corner of the original screen
    bbox it sat at)."""
    base = quad_offset(idx)
    vs = read_quad(bytes(blob), idx)

    # Original screen corners (top-left origin)
    screens = [(v[3] + 480.0, 272.0 - v[4]) for v in vs]
    orig_sx_min = min(s[0] for s in screens)
    orig_sx_max = max(s[0] for s in screens)
    orig_sy_min = min(s[1] for s in screens)
    orig_sy_max = max(s[1] for s in screens)

    nsx0, nsy0, nsx1, nsy1 = new_screen_rect
    # Vita center-origin
    nvsx0 = nsx0 - 480.0
    nvsx1 = nsx1 - 480.0
    nvsy_top = 272.0 - nsy0   # large positive ≡ screen top
    nvsy_bot = 272.0 - nsy1   # smaller positive ≡ screen bottom

    for i, (color, f1, f2, sx, sy) in enumerate(vs):
        sx_tl = sx + 480.0
        sy_tl = 272.0 - sy
        is_sx_min = abs(sx_tl - orig_sx_min) <= abs(sx_tl - orig_sx_max)
        is_sy_min = abs(sy_tl - orig_sy_min) <= abs(sy_tl - orig_sy_max)
        new_sx = nvsx0 if is_sx_min else nvsx1
        new_sy = nvsy_top if is_sy_min else nvsy_bot
        struct.pack_into(
            "<Iffff", blob, base + i * VERTEX_SIZE,
            color, f1, f2, new_sx, new_sy,
        )


def uv_rect(vs) -> tuple[int, int, int, int]:
    xs = [v[1] for v in vs]; ys = [v[2] for v in vs]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def build(source_mbs: Path, output_mbs: Path, output_tex: Path,
          source_atlas: Path, font_path: Path) -> dict:
    src = source_mbs.read_bytes()
    blob = bytearray(src)

    # 1. Hide all narration-range carriers
    for idx in range(40, 116):
        hide_quad(blob, idx)

    # 2. Restore & stretch the 4 winners
    for line_idx, (idx, screen_rect) in LINE_LAYOUT.items():
        # First put back the original vertex data (we just overwrote with hide)
        # by reading from source
        base = quad_offset(idx)
        for i in range(4):
            orig_verts = struct.unpack_from("<Iffff", src, base + i * VERTEX_SIZE)
            struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, *orig_verts)
        # Then stretch only sx/sy
        stretch_carrier_screen(blob, idx, screen_rect)

    # 3. Build atlas: start from ORIGINAL atlas, clear the UV region of each
    # winning carrier, redraw Korean sentence at max size that fits the UV rect.
    atlas = Image.open(source_atlas).convert("RGBA")
    arr = np.array(atlas)

    for line_idx, (idx, _) in LINE_LAYOUT.items():
        vs = [struct.unpack_from("<Iffff", src, quad_offset(idx) + i * VERTEX_SIZE)
              for i in range(4)]
        ux0, uy0, ux1, uy1 = uv_rect(vs)
        arr[uy0:uy1, ux0:ux1, 3] = 0

    atlas = Image.fromarray(arr, mode="RGBA")
    draw = ImageDraw.Draw(atlas)
    font_sizes = {}
    for line_idx, (idx, _) in LINE_LAYOUT.items():
        vs = [struct.unpack_from("<Iffff", src, quad_offset(idx) + i * VERTEX_SIZE)
              for i in range(4)]
        ux0, uy0, ux1, uy1 = uv_rect(vs)
        w = ux1 - ux0; h = uy1 - uy0
        text = KOREAN_SENTENCES[line_idx]
        size = h
        font = None
        while size >= 12:
            f = ImageFont.truetype(str(font_path), size=size)
            stroke = max(2, size // 8)
            b = f.getbbox(text, stroke_width=stroke)
            tw = b[2] - b[0]; th = b[3] - b[1]
            if tw <= w - 4 and th <= h - 2:
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
        font_sizes[line_idx] = size

    output_mbs.parent.mkdir(parents=True, exist_ok=True)
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_mbs.write_bytes(blob)
    atlas.save(output_tex)
    return {"font_sizes": font_sizes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", default="temp/cpk_extract/_US/GUI/opening01.mbs")
    ap.add_argument("--output-mbs", default="temp/opening_test/opening01.mbs")
    ap.add_argument("--output-texture", default="temp/opening_test/atlas.png")
    ap.add_argument("--source-atlas", default="C:/game/vita3k/textures/export/79C935AA47DD1810.png")
    ap.add_argument("--font", default="fonts/Griun_PolSensibility-Rg.ttf")
    args = ap.parse_args()
    info = build(Path(args.source_mbs), Path(args.output_mbs),
                 Path(args.output_texture), Path(args.source_atlas),
                 Path(args.font))
    print(f"font sizes: {info['font_sizes']}")


if __name__ == "__main__":
    main()
