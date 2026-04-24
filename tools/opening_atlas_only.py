"""Build Korean atlas for opening01 by assigning specific text fragments
to each carrier. Each carrier draws its own text in its own atlas UV rect,
rendered at carrier.screen_bbox size, then scaled/transposed to fit the
UV rect shape.

This avoids the "paragraph crop" approach's problem of gaps between
carriers swallowing parts of a continuous sentence. Instead, each
carrier is a self-contained text fragment that renders fully on screen.
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

# Per-carrier Korean text fragments. Blank/missing carriers remain unchanged
# in atlas (so the original English leaks through — acceptable if we hide
# those carriers via MBS or pick a full set).
#
# Line/x-position comments for reference:
CARRIER_TEXT = {
    # Line 1 (y ~170-213)
    115: "헤아릴",          # x=196..278, small left
    80:  "수 없이 흩어진",   # x=304..610, middle
    109: "마검들.",         # x=551..762, right
    # Line 2 (y ~240-278)
    97:  "칼집에서 뽑히는",  # x=116..397, left
    100: "순간,",           # x=685..734, tiny right
    # Line 3 (y ~314-347)
    91:  "피에 굶주린 듯",   # x=19..233
    94:  "생명을 탐한다.",   # x=547..728
    # Line 4 (y ~384-417)
    112: "그 힘에",         # x=207..302, left
    88:  "스러진 이들의",    # x=529..744, middle-right
}

RED_CARRIERS = {85, 86, 102, 106, 107}
LARGE_CONTAINER_CARRIERS = {90, 96, 111, 114}


def quad_offset(idx: int) -> int:
    return MBS_TABLE_OFFSET + idx * QUAD_SIZE


def read_quad(src: bytes, idx: int):
    base = quad_offset(idx)
    return [struct.unpack_from("<Iffff", src, base + i * VERTEX_SIZE) for i in range(4)]


def screen_bbox_top_left(vs):
    pts = [(sx + 480.0, 272.0 - sy) for _, _, _, sx, sy in vs]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def uv_rect_image_coords(vs):
    xs = [v[1] for v in vs]
    ys = [v[2] for v in vs]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def is_rectangular(vs) -> bool:
    f1s = {round(v[1], 1) for v in vs}
    f2s = {round(v[2], 1) for v in vs}
    return len(f1s) == 2 and len(f2s) == 2


def fit_text(text: str, font_path: Path, max_w: int, max_h: int,
             start_size: int = 28, min_size: int = 10) -> ImageFont.FreeTypeFont:
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size=size)
        stroke = max(1, size // 14)
        box = font.getbbox(text, stroke_width=stroke)
        w = box[2] - box[0]; h = box[3] - box[1]
        if w <= max_w - 6 and h <= max_h - 4:
            return font
        size -= 1
    return ImageFont.truetype(str(font_path), size=min_size)


def render_text_at_screen_size(text: str, screen_size: tuple[int, int],
                                font_path: Path) -> Image.Image:
    w, h = max(4, screen_size[0]), max(4, screen_size[1])
    font = fit_text(text, font_path, w, h)
    stroke = max(1, font.size // 14)
    tile = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    tw = box[2] - box[0]; th = box[3] - box[1]
    tx = (w - tw) // 2 - box[0]
    ty = (h - th) // 2 - box[1]
    draw.text((tx, ty), text, font=font,
              fill=(255, 255, 255, 255),
              stroke_width=stroke, stroke_fill=(255, 255, 255, 255))
    return tile


def warp_rect_to_uv(tile: Image.Image, vs, uv_rect) -> Image.Image:
    """Warp the tile (drawn at screen-bbox size) into the carrier's UV
    rect using PIL's QUAD transform. Handles rectangular carriers —
    including transposed ones — correctly."""
    ux0, uy0, ux1, uy1 = uv_rect
    uv_w = ux1 - ux0; uv_h = uy1 - uy0

    def find(tx, ty):
        return min(vs, key=lambda v: (v[1]-tx)**2 + (v[2]-ty)**2)

    v_tl = find(ux0, uy0); v_bl = find(ux0, uy1)
    v_br = find(ux1, uy1); v_tr = find(ux1, uy0)

    def screen(v): return (v[3] + 480.0, 272.0 - v[4])
    sx_tl, sy_tl = screen(v_tl); sx_bl, sy_bl = screen(v_bl)
    sx_br, sy_br = screen(v_br); sx_tr, sy_tr = screen(v_tr)

    # Shift source coords so they refer to the TILE (which is at origin),
    # not the full 960×544 screen.
    sc_x0, sc_y0, sc_x1, sc_y1 = screen_bbox_top_left(vs)

    def to_tile(sx, sy):
        return (sx - sc_x0, sy - sc_y0)

    t_tl = to_tile(sx_tl, sy_tl); t_bl = to_tile(sx_bl, sy_bl)
    t_br = to_tile(sx_br, sy_br); t_tr = to_tile(sx_tr, sy_tr)
    data = (t_tl[0], t_tl[1], t_bl[0], t_bl[1],
            t_br[0], t_br[1], t_tr[0], t_tr[1])
    return tile.transform((uv_w, uv_h), Image.QUAD, data, Image.BILINEAR)


def build_atlas(source_mbs: Path, output_tex: Path, font_path: Path) -> dict:
    src = source_mbs.read_bytes()
    atlas = Image.new("RGBA", ATLAS_SIZE, (0, 0, 0, 0))
    used: list[int] = []
    skipped: list[tuple[int, str]] = []

    for idx in range(80, 116):
        vs = read_quad(src, idx)
        if idx in RED_CARRIERS:
            skipped.append((idx, "red")); continue
        if idx in LARGE_CONTAINER_CARRIERS:
            skipped.append((idx, "container")); continue
        if idx not in CARRIER_TEXT:
            skipped.append((idx, "no-text-assigned")); continue
        text = CARRIER_TEXT[idx]
        if not text:
            skipped.append((idx, "empty-text")); continue

        sx0, sy0, sx1, sy1 = screen_bbox_top_left(vs)
        if sx0 < 0 or sx1 > 960 or sy0 < 0 or sy1 > 544:
            skipped.append((idx, "off-screen")); continue
        ux0, uy0, ux1, uy1 = uv_rect_image_coords(vs)
        if ux0 < 0 or ux1 > 512 or uy0 < 0 or uy1 > 512:
            skipped.append((idx, "uv-oob")); continue

        sc_w = sx1 - sx0; sc_h = sy1 - sy0
        tile = render_text_at_screen_size(text, (sc_w, sc_h), font_path)

        if is_rectangular(vs):
            warped = warp_rect_to_uv(tile, vs, (ux0, uy0, ux1, uy1))
        else:
            # Fallback: resize (non-rect aspect approximated)
            warped = tile.resize((ux1 - ux0, uy1 - uy0), Image.LANCZOS)

        atlas.alpha_composite(warped, (ux0, uy0))
        used.append(idx)

    output_tex.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output_tex)
    return {"used": used, "skipped": skipped}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", default="temp/cpk_extract/_US/GUI/opening01.mbs")
    ap.add_argument("--output-texture", default="temp/opening_test/atlas.png")
    ap.add_argument("--font", default="fonts/Griun_PolSensibility-Rg.ttf")
    args = ap.parse_args()
    info = build_atlas(Path(args.source_mbs), Path(args.output_texture), Path(args.font))
    print(f"used ({len(info['used'])}): {info['used']}")
    print(f"skipped ({len(info['skipped'])}): {info['skipped']}")


if __name__ == "__main__":
    main()
