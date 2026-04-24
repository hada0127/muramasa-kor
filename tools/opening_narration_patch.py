"""Patch opening01.mbs + opening01 atlas for Korean narration.

Strategy (based on parallel codex+gemini review 2026-04-25):
- PRESERVE each carrier's original screen vertices and UV-to-screen pairing.
- ONLY remap UV coordinates to point into a new Korean atlas region.
- opening01 carriers use a 90° rotated UV mapping: u drives screen y, v drives
  screen x. `remap_uv` preserves this by matching each vertex's original corner
  role (u/v min/max) to the new atlas rect corner.

Korean text is first drawn onto a 960x544 "paragraph canvas" at positions that
match the original narration's line y-coords. Each active carrier's screen
bbox is then cropped from that canvas, packed into the atlas, and the
carrier's UV is remapped to address the packed tile.

Red-highlight carriers (word emphasis) are hidden; we skip the red-word
effect per user request to keep the layout simple.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20
DEFAULT_ATLAS_SIZE = (512, 512)

KOREAN_LINES = [
    "헤아릴 수 없이 흩어진 마검들.",
    "칼집에서 뽑히는 순간,",
    "피에 굶주린 듯 곧장 생명을 탐한다.",
    "그 힘에 스러진 이들의 운명을 보라.",
]

CARRIER_RANGE = range(80, 116)
RED_CARRIERS = {85, 86, 102, 106, 107}   # color FF0000FF — English word-emphasis
LINE_Y_ROWS = [(170, 213), (240, 278), (314, 347), (384, 417)]
MAX_CARRIER_AREA = 30000                  # larger carriers likely container/fill; hide


def quad_offset(idx: int) -> int:
    return MBS_TABLE_OFFSET + idx * QUAD_SIZE


def quad_vertices(blob: bytes, idx: int) -> list[tuple[int, float, float, float, float]]:
    base = quad_offset(idx)
    return [struct.unpack_from("<Iffff", blob, base + i * VERTEX_SIZE) for i in range(4)]


def screen_bbox(verts) -> tuple[int, int, int, int]:
    pts = [(sx + 480.0, 272.0 - sy) for _, _, _, sx, sy in verts]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


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


def remap_uv(blob: bytearray, idx: int, new_rect: tuple[int, int, int, int]) -> None:
    """Replace UV coords with the matching corner of new_rect while preserving
    the carrier's original screen vertices and the u-min↔u-max / v-min↔v-max
    pairing. opening01's rotated mapping means u-axis becomes screen y and
    v-axis becomes screen x."""
    base = quad_offset(idx)
    x0, y0, x1, y1 = new_rect
    old = [struct.unpack_from("<Iffff", blob, base + i * VERTEX_SIZE) for i in range(4)]
    u_vals = [v[1] for v in old]
    v_vals = [v[2] for v in old]
    u_min, u_max = min(u_vals), max(u_vals)
    v_min, v_max = min(v_vals), max(v_vals)
    for i, (color, u, v, sx, sy) in enumerate(old):
        nu = y0 if abs(u - u_min) <= abs(u - u_max) else y1
        nv = x0 if abs(v - v_min) <= abs(v - v_max) else x1
        struct.pack_into(
            "<Iffff", blob, base + i * VERTEX_SIZE,
            color, float(nu), float(nv), sx, sy,
        )


def assign_line_by_y(y_min: float) -> int:
    if y_min < 220: return 0
    if y_min < 300: return 1
    if y_min < 370: return 2
    return 3


def classify_carriers(blob: bytes) -> tuple[list[int], list[int]]:
    """Return (active, to_hide). Active = carriers we show Korean on.
    to_hide = red carriers we force invisible."""
    active: list[int] = []
    to_hide: list[int] = []
    for idx in CARRIER_RANGE:
        if idx in RED_CARRIERS:
            to_hide.append(idx)
            continue
        vs = quad_vertices(blob, idx)
        bbox = screen_bbox(vs)
        # skip off-screen carriers (they were already invisible in-game)
        if bbox[0] < 0 or bbox[2] > 960 or bbox[1] < 0 or bbox[3] > 544:
            continue
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if area > MAX_CARRIER_AREA:
            to_hide.append(idx)
            continue
        active.append(idx)
    return active, to_hide


def compute_line_boxes(blob: bytes, active_indices: list[int]) -> list[tuple[int, int, int, int]]:
    per_line: dict[int, list[tuple[int, int, int, int]]] = {0: [], 1: [], 2: [], 3: []}
    for idx in active_indices:
        bbox = screen_bbox(quad_vertices(blob, idx))
        line = assign_line_by_y(bbox[1])
        per_line[line].append(bbox)

    boxes = []
    for i in range(4):
        bs = per_line[i]
        y0, y1 = LINE_Y_ROWS[i]
        if bs:
            x0 = min(b[0] for b in bs) - 4
            x1 = max(b[2] for b in bs) + 4
        else:
            x0, x1 = 50, 910
        boxes.append((max(0, x0), y0, min(960, x1), y1))
    return boxes


def fit_font(line_boxes: list[tuple[int, int, int, int]], font_path: Path,
             max_size: int = 30, min_size: int = 16) -> ImageFont.FreeTypeFont:
    size = max_size
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size=size)
        stroke = max(2, size // 14)
        ok = True
        for text, (x0, y0, x1, y1) in zip(KOREAN_LINES, line_boxes):
            box = font.getbbox(text, stroke_width=stroke)
            w = box[2] - box[0]; h = box[3] - box[1]
            if w > (x1 - x0 - 10) or h > (y1 - y0 - 4):
                ok = False
                break
        if ok:
            return font
        size -= 1
    return ImageFont.truetype(str(font_path), size=min_size)


def draw_paragraph(line_boxes: list[tuple[int, int, int, int]], font_path: Path) -> tuple[Image.Image, int]:
    font = fit_font(line_boxes, font_path)
    stroke = max(2, font.size // 14)
    canvas = Image.new("RGBA", (960, 544), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    for text, (x0, y0, x1, y1) in zip(KOREAN_LINES, line_boxes):
        box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        tw = box[2] - box[0]; th = box[3] - box[1]
        tx = x0 + ((x1 - x0) - tw) // 2 - box[0]
        ty = y0 + ((y1 - y0) - th) // 2 - box[1]
        draw.text((tx, ty), text, font=font,
                  fill=(255, 255, 255, 255),
                  stroke_width=stroke, stroke_fill=(255, 255, 255, 255))
    return canvas, font.size


def pack_tiles(tiles: list[tuple[int, Image.Image]],
               atlas_size: tuple[int, int]) -> dict[int, tuple[int, int, int, int]]:
    x, y, row_h = 4, 4, 0
    placements: dict[int, tuple[int, int, int, int]] = {}
    for idx, tile in tiles:
        w = max(2, tile.size[0])
        h = max(2, tile.size[1])
        if x + w + 4 > atlas_size[0]:
            x = 4; y += row_h + 4; row_h = 0
        if y + h + 4 > atlas_size[1]:
            raise RuntimeError(f"atlas full while packing quad {idx}")
        placements[idx] = (x, y, x + w, y + h)
        x += w + 4
        row_h = max(row_h, h)
    return placements


def build(source_mbs: Path, output_mbs: Path, output_tex: Path,
          font_path: Path, atlas_size=DEFAULT_ATLAS_SIZE) -> dict:
    src = source_mbs.read_bytes()
    blob = bytearray(src)

    active, to_hide = classify_carriers(src)
    line_boxes = compute_line_boxes(src, active)
    paragraph, chosen_size = draw_paragraph(line_boxes, font_path)

    tiles: list[tuple[int, Image.Image]] = []
    for idx in active:
        x0, y0, x1, y1 = screen_bbox(quad_vertices(src, idx))
        x0 = max(0, min(959, x0))
        y0 = max(0, min(543, y0))
        x1 = max(x0 + 1, min(960, x1))
        y1 = max(y0 + 1, min(544, y1))
        tile = paragraph.crop((x0, y0, x1, y1))
        tiles.append((idx, tile))

    placements = pack_tiles(tiles, atlas_size)
    atlas = Image.new("RGBA", atlas_size, (0, 0, 0, 0))
    for idx, tile in tiles:
        px0, py0, px1, py1 = placements[idx]
        atlas.alpha_composite(tile, (px0, py0))
        remap_uv(blob, idx, (px0, py0, px1, py1))

    for idx in to_hide:
        hide_quad(blob, idx)

    output_mbs.parent.mkdir(parents=True, exist_ok=True)
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_mbs.write_bytes(blob)
    atlas.save(output_tex)
    return {
        "active": active,
        "hidden": to_hide,
        "line_boxes": line_boxes,
        "font_size": chosen_size,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", default="temp/cpk_extract/_US/GUI/opening01.mbs")
    ap.add_argument("--output-mbs", default="temp/opening_test/opening01.mbs")
    ap.add_argument("--output-texture", default="temp/opening_test/atlas.png")
    ap.add_argument("--font", default="fonts/Griun_PolSensibility-Rg.ttf")
    args = ap.parse_args()
    info = build(Path(args.source_mbs), Path(args.output_mbs),
                 Path(args.output_texture), Path(args.font))
    print(f"font size: {info['font_size']}px")
    print(f"active carriers ({len(info['active'])}): {info['active']}")
    print(f"hidden  carriers ({len(info['hidden'])}): {info['hidden']}")
    for i, b in enumerate(info['line_boxes']):
        print(f"  line{i+1} box: {b}")


if __name__ == "__main__":
    main()
