"""Enlarge the 4 chosen narration carriers so Korean text renders at
full readable size.

Unlike atlas-only approaches, this also MODIFIES opening01.mbs:
- Hide every carrier in range 40..115 except the 4 winners.
- For each winner, rewrite its 4 vertices so it paints a FULL-WIDTH
  screen strip at the line's y position, sampled from a generous atlas
  region (preserves corner pairing: atlas TL ↔ screen TL).
- Generate an atlas where each strip is drawn large and crisp.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20
ATLAS_SIZE = (512, 512)

# Per-line final layout: which carrier to keep, the new screen rect
# (top-left origin), and the new atlas UV rect. UV rects fit into 512×512
# and don't overlap.
LINE_LAYOUT = {
    0: {  # narration line 1 — top row
        "carrier": 109,
        "text": "헤아릴 수 없이 흩어진 마검들",
        "screen": (60, 165, 900, 215),      # (x0, y0, x1, y1) top-left origin
        "uv":     (4, 4, 500, 54),          # (x0, y0, x1, y1) atlas
    },
    1: {  # narration line 2
        "carrier": 97,
        "text": "칼집에서 뽑히는 순간",
        "screen": (60, 225, 900, 285),
        "uv":     (4, 64, 500, 114),
    },
    2: {  # narration line 3
        "carrier": 91,
        "text": "피에 굶주린 듯 곧장 생명을 탐한다",
        "screen": (60, 295, 900, 355),
        "uv":     (4, 124, 500, 174),
    },
    3: {  # narration line 4
        "carrier": 88,
        "text": "그 힘에 스러진 이들의 운명을 보라",
        "screen": (60, 365, 900, 425),
        "uv":     (4, 184, 500, 234),
    },
}


def quad_offset(idx: int) -> int:
    return MBS_TABLE_OFFSET + idx * QUAD_SIZE


def read_quad(blob: bytes, idx: int):
    base = quad_offset(idx)
    return [struct.unpack_from("<Iffff", blob, base + i * VERTEX_SIZE) for i in range(4)]


def hide_quad(blob: bytearray, idx: int) -> None:
    """Move the quad off-screen and make it transparent."""
    verts = [
        (0x00000000, 0.0, 0.0, -2080.0, 1872.0),
        (0x00000000, 0.0, 1.0, -2078.0, 1872.0),
        (0x00000000, 1.0, 1.0, -2078.0, 1870.0),
        (0x00000000, 1.0, 0.0, -2080.0, 1870.0),
    ]
    base = quad_offset(idx)
    for i, v in enumerate(verts):
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, *v)


def rewrite_quad(blob: bytearray, idx: int,
                 screen_rect: tuple[int, int, int, int],
                 uv_rect: tuple[int, int, int, int],
                 color: int = 0xFFFFFFFF) -> None:
    """Write a full rectangular quad mapping screen_rect ↔ uv_rect with
    the SAME corner pairing as original opening01 carriers:
      v0: (u_min, v_min) ↔ (x_min, y_top)   [screen TL]
      v1: (u_min, v_max) ↔ (x_max, y_top)   [screen TR]
      v2: (u_max, v_max) ↔ (x_max, y_bot)   [screen BR]
      v3: (u_max, v_min) ↔ (x_min, y_bot)   [screen BL]
    Wait — for opening01, the actual pairing observed in probe data is:
      atlas TL (f1_min, f2_min) ↔ screen TL
      atlas BL (f1_min, f2_max) ↔ screen BL
      atlas BR (f1_max, f2_max) ↔ screen BR
      atlas TR (f1_max, f2_min) ↔ screen TR
    That is, f1 = atlas x = screen x axis, f2 = atlas y = screen y axis.
    Straight pairing, no rotation."""
    sx0, sy0, sx1, sy1 = screen_rect        # top-left origin
    ux0, uy0, ux1, uy1 = uv_rect             # atlas pixel coords
    # Vita center-origin: vsx = sx - 480, vsy = 272 - sy
    vsx0 = sx0 - 480.0; vsx1 = sx1 - 480.0
    vsy_top = 272.0 - sy0
    vsy_bot = 272.0 - sy1

    # Preserve original opening01 vertex pairing (diagonal UV↔screen swap):
    #   v0: atlas TL   (ux0, uy0) ↔ screen TL   (sx0, sy0)
    #   v1: atlas BL   (ux0, uy1) ↔ screen TR   (sx1, sy0)
    #   v2: atlas BR   (ux1, uy1) ↔ screen BR   (sx1, sy1)
    #   v3: atlas TR   (ux1, uy0) ↔ screen BL   (sx0, sy1)
    verts = [
        (color, float(ux0), float(uy0), vsx0, vsy_top),
        (color, float(ux0), float(uy1), vsx1, vsy_top),
        (color, float(ux1), float(uy1), vsx1, vsy_bot),
        (color, float(ux1), float(uy0), vsx0, vsy_bot),
    ]
    base = quad_offset(idx)
    for i, v in enumerate(verts):
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, *v)


def fit_text(text: str, max_w: int, max_h: int, font_path: Path,
             start_size: int, min_size: int) -> ImageFont.FreeTypeFont:
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size=size)
        stroke = max(2, size // 10)
        box = font.getbbox(text, stroke_width=stroke)
        w = box[2] - box[0]; h = box[3] - box[1]
        if w <= max_w - 6 and h <= max_h - 4:
            return font
        size -= 1
    return ImageFont.truetype(str(font_path), size=min_size)


def build(source_mbs: Path, output_mbs: Path, output_tex: Path,
          font_path: Path) -> dict:
    src = source_mbs.read_bytes()
    blob = bytearray(src)

    # 1. Hide all narration-range carriers first
    for idx in range(40, 116):
        hide_quad(blob, idx)

    # 2. Rewrite winners with expanded screen + atlas rects
    for line_idx, layout in LINE_LAYOUT.items():
        rewrite_quad(blob, layout["carrier"], layout["screen"], layout["uv"],
                     color=0xFFFFFFFF)

    # 3. Build atlas: draw Korean text in each uv rect, large and crisp
    atlas = Image.new("RGBA", ATLAS_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(atlas)
    chosen_sizes = {}
    for line_idx, layout in LINE_LAYOUT.items():
        ux0, uy0, ux1, uy1 = layout["uv"]
        w = ux1 - ux0; h = uy1 - uy0
        font = fit_text(layout["text"], w, h, font_path,
                        start_size=h, min_size=16)
        stroke = max(2, font.size // 10)
        tbox = draw.textbbox((0, 0), layout["text"], font=font, stroke_width=stroke)
        tw = tbox[2] - tbox[0]; th = tbox[3] - tbox[1]
        tx = ux0 + (w - tw) // 2 - tbox[0]
        ty = uy0 + (h - th) // 2 - tbox[1]
        draw.text((tx, ty), layout["text"], font=font,
                  fill=(255, 255, 255, 255),
                  stroke_width=stroke, stroke_fill=(255, 255, 255, 255))
        chosen_sizes[line_idx] = font.size

    output_mbs.parent.mkdir(parents=True, exist_ok=True)
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_mbs.write_bytes(blob)
    atlas.save(output_tex)
    return {"font_sizes": chosen_sizes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", default="temp/cpk_extract/_US/GUI/opening01.mbs")
    ap.add_argument("--output-mbs", default="temp/opening_test/opening01.mbs")
    ap.add_argument("--output-texture", default="temp/opening_test/atlas.png")
    ap.add_argument("--font", default="fonts/Griun_PolSensibility-Rg.ttf")
    args = ap.parse_args()
    info = build(Path(args.source_mbs), Path(args.output_mbs),
                 Path(args.output_texture), Path(args.font))
    print(f"font sizes per line: {info['font_sizes']}")


if __name__ == "__main__":
    main()
