from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20
ATLAS_SIZE = (2048, 2048)
TARGET_INDICES = list(range(80, 116))


def quad_vertices(blob: bytes, index: int) -> list[tuple[int, float, float, float, float]]:
    out = []
    base = MBS_TABLE_OFFSET + index * QUAD_SIZE
    for i in range(4):
        off = base + i * VERTEX_SIZE
        out.append(struct.unpack_from("<Iffff", blob, off))
    return out


def screen_bbox(verts: list[tuple[int, float, float, float, float]]) -> tuple[int, int, int, int]:
    pts = [(x + 480.0, 272.0 - y) for _, _, _, x, y in verts]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def fit_font(text: str, font_path: Path, max_w: int, max_h: int, start_size: int) -> ImageFont.FreeTypeFont:
    size = start_size
    while size >= 24:
        font = ImageFont.truetype(str(font_path), size=size)
        box = font.getbbox(text, stroke_width=max(2, size // 14))
        w = box[2] - box[0]
        h = box[3] - box[1]
        if w <= max_w and h <= max_h:
            return font
        size -= 2
    return ImageFont.truetype(str(font_path), size=24)


def draw_paragraph(font_path: Path) -> Image.Image:
    canvas = Image.new("RGBA", (960, 544), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    lines = [
        ("수많은 요도들이 세상에 흩어져 있다.", (118, 165, 828, 206)),
        ("그 칼집에서 뽑히는 순간,", (182, 220, 756, 259)),
        ("피에 굶주린 칼날은 곧바로 희생양을 찾기 시작한다.", (95, 272, 860, 316)),
        ("그 힘에 삼켜진 자들의 운명을 지켜보라.", (155, 327, 808, 366)),
    ]
    for text, (x0, y0, x1, y1) in lines:
        font = fit_font(text, font_path, x1 - x0 - 8, y1 - y0 - 8, y1 - y0)
        stroke = max(2, font.size // 14)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        tx = x0 + ((x1 - x0) - (box[2] - box[0])) // 2 - box[0]
        ty = y0 + ((y1 - y0) - (box[3] - box[1])) // 2 - box[1]
        draw.text(
            (tx, ty),
            text,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=stroke,
            stroke_fill=(255, 255, 255, 255),
        )
    return canvas


def pack_tiles(tiles: list[tuple[int, Image.Image]]) -> dict[int, tuple[int, int, int, int]]:
    atlas_w, atlas_h = ATLAS_SIZE
    x = 8
    y = 8
    row_h = 0
    placements: dict[int, tuple[int, int, int, int]] = {}
    for idx, tile in tiles:
        w, h = tile.size
        w = max(2, w)
        h = max(2, h)
        if x + w + 8 > atlas_w:
            x = 8
            y += row_h + 8
            row_h = 0
        if y + h + 8 > atlas_h:
            raise RuntimeError("atlas full")
        placements[idx] = (x, y, x + w, y + h)
        x += w + 8
        row_h = max(row_h, h)
    return placements


def remap_uv(blob: bytearray, index: int, new_rect: tuple[int, int, int, int]) -> None:
    base = MBS_TABLE_OFFSET + index * QUAD_SIZE
    x0, y0, x1, y1 = new_rect
    old = []
    for i in range(4):
        off = base + i * VERTEX_SIZE
        color, u, v, sx, sy = struct.unpack_from("<Iffff", blob, off)
        old.append((color, u, v, sx, sy))
    us = [v[1] for v in old]
    vs = [v[2] for v in old]
    u_min, u_max = min(us), max(us)
    v_min, v_max = min(vs), max(vs)
    for i, (color, u, v, sx, sy) in enumerate(old):
        nu = x0 if abs(u - u_min) <= abs(u - u_max) else x1
        nv = y0 if abs(v - v_min) <= abs(v - v_max) else y1
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, color, float(nu), float(nv), sx, sy)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", required=True)
    ap.add_argument("--output-mbs", required=True)
    ap.add_argument("--output-texture", required=True)
    ap.add_argument("--font", required=True)
    args = ap.parse_args()

    src = Path(args.source_mbs).read_bytes()
    blob = bytearray(src)
    paragraph = draw_paragraph(Path(args.font))

    tiles: list[tuple[int, Image.Image]] = []
    for idx in TARGET_INDICES:
        verts = quad_vertices(src, idx)
        x0, y0, x1, y1 = screen_bbox(verts)
        x0 = max(0, min(959, x0))
        y0 = max(0, min(543, y0))
        x1 = max(x0 + 1, min(960, x1))
        y1 = max(y0 + 1, min(544, y1))
        crop = paragraph.crop((x0, y0, x1, y1))
        tiles.append((idx, crop))

    placements = pack_tiles(tiles)
    atlas = Image.new("RGBA", ATLAS_SIZE, (0, 0, 0, 0))
    for idx, crop in tiles:
        x0, y0, x1, y1 = placements[idx]
        atlas.alpha_composite(crop, (x0, y0))
        remap_uv(blob, idx, (x0, y0, x1, y1))

    out_mbs = Path(args.output_mbs)
    out_tex = Path(args.output_texture)
    out_mbs.parent.mkdir(parents=True, exist_ok=True)
    out_tex.parent.mkdir(parents=True, exist_ok=True)
    out_mbs.write_bytes(blob)
    atlas.save(out_tex)


if __name__ == "__main__":
    main()
