from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20
DEFAULT_ATLAS_SIZE = (512, 512)
DEFAULT_TARGET_INDICES = list(range(40, 80))
DEFAULT_HIDE_INDICES = list(range(80, 116))
LINES = [
    ("\ud5e4\uc544\ub9b4 \uc218 \uc5c6\uc774 \ud769\uc5b4\uc9c4 \ub9c8\uac80\ub4e4.", (120, 170, 836, 210)),
    ("\uce7c\uc9d1\uc5d0\uc11c \ubf51\ud788\ub294 \uc21c\uac04,", (168, 216, 792, 252)),
    ("\ud53c\uc5d0 \uad76\uc8fc\ub9b0 \ub4ef \uace7\uc7a5 \uc0dd\uba85\uc744 \ud0d0\ud55c\ub2e4.", (100, 258, 860, 300)),
    ("\uadf8 \ud798\uc5d0 \uc2a4\ub7ec\uc9c4 \uc774\ub4e4\uc758 \uc6b4\uba85\uc744 \ubcf4\ub77c.", (140, 304, 820, 342)),
]


def quad_offset(index: int) -> int:
    return MBS_TABLE_OFFSET + index * QUAD_SIZE


def quad_vertices(blob: bytes, index: int) -> list[tuple[int, float, float, float, float]]:
    out = []
    base = quad_offset(index)
    for i in range(4):
        out.append(struct.unpack_from("<Iffff", blob, base + i * VERTEX_SIZE))
    return out


def screen_bbox(verts: list[tuple[int, float, float, float, float]]) -> tuple[int, int, int, int]:
    pts = [(sx + 480.0, 272.0 - sy) for _, _, _, sx, sy in verts]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def hide_quad(blob: bytearray, index: int) -> None:
    verts = [
        (0x00000000, 0.0, 0.0, -2080.0, 1872.0),
        (0x00000000, 0.0, 1.0, -2078.0, 1872.0),
        (0x00000000, 1.0, 1.0, -2078.0, 1870.0),
        (0x00000000, 1.0, 0.0, -2080.0, 1870.0),
    ]
    base = quad_offset(index)
    for i, vert in enumerate(verts):
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, *vert)


def fit_font(lines: list[tuple[str, tuple[int, int, int, int]]], font_path: Path) -> ImageFont.FreeTypeFont:
    size = 42
    while size >= 18:
        font = ImageFont.truetype(str(font_path), size=size)
        ok = True
        for text, (x0, y0, x1, y1) in lines:
            stroke = max(2, size // 14)
            box = font.getbbox(text, stroke_width=stroke)
            if (box[2] - box[0]) > (x1 - x0 - 10) or (box[3] - box[1]) > (y1 - y0 - 8):
                ok = False
                break
        if ok:
            return font
        size -= 2
    return ImageFont.truetype(str(font_path), size=18)


def draw_paragraph(font_path: Path) -> Image.Image:
    canvas = Image.new("RGBA", (960, 544), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    font = fit_font(LINES, font_path)
    stroke = max(2, font.size // 14)
    for text, (x0, y0, x1, y1) in LINES:
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


def make_debug_tile(
    size: tuple[int, int],
    index: int,
    color: tuple[int, int, int, int],
) -> Image.Image:
    w = max(2, size[0])
    h = max(2, size[1])
    tile = Image.new("RGBA", (w, h), color)
    draw = ImageDraw.Draw(tile)
    border = max(1, min(w, h) // 16)
    draw.rectangle((0, 0, w - 1, h - 1), outline=(255, 255, 255, 255), width=border)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", size=max(10, min(h - 2, 18)))
    except OSError:
        font = ImageFont.load_default()
    label = str(index)
    box = draw.textbbox((0, 0), label, font=font)
    tx = (w - (box[2] - box[0])) // 2 - box[0]
    ty = (h - (box[3] - box[1])) // 2 - box[1]
    draw.text((tx, ty), label, font=font, fill=(255, 255, 255, 255))
    return tile


def pack_tiles(
    tiles: list[tuple[int, Image.Image]],
    atlas_size: tuple[int, int],
) -> dict[int, tuple[int, int, int, int]]:
    x = 4
    y = 4
    row_h = 0
    placements: dict[int, tuple[int, int, int, int]] = {}
    for idx, tile in tiles:
        w, h = tile.size
        w = max(2, w)
        h = max(2, h)
        if x + w + 4 > atlas_size[0]:
            x = 4
            y += row_h + 4
            row_h = 0
        if y + h + 4 > atlas_size[1]:
            raise RuntimeError(f"atlas full while packing quad {idx}")
        placements[idx] = (x, y, x + w, y + h)
        x += w + 4
        row_h = max(row_h, h)
    return placements


def remap_uv(blob: bytearray, index: int, new_rect: tuple[int, int, int, int]) -> None:
    base = quad_offset(index)
    x0, y0, x1, y1 = new_rect
    old = []
    for i in range(4):
        off = base + i * VERTEX_SIZE
        old.append(struct.unpack_from("<Iffff", blob, off))
    u_min = min(v[1] for v in old)
    u_max = max(v[1] for v in old)
    v_min = min(v[2] for v in old)
    v_max = max(v[2] for v in old)
    for i, (color, u, v, sx, sy) in enumerate(old):
        # opening01 narration quads store UV axes rotated from the usual
        # convention: `u` tracks vertical placement and `v` tracks horizontal.
        nu = y0 if abs(u - u_min) <= abs(u - u_max) else y1
        nv = x0 if abs(v - v_min) <= abs(v - v_max) else x1
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, color, float(nu), float(nv), sx, sy)


def parse_index_list(raw: str) -> list[int]:
    out: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            out.extend(range(int(start), int(end) + 1))
        else:
            out.append(int(part))
    return sorted(dict.fromkeys(out))


def build_texture_and_mbs(
    source_mbs: Path,
    output_mbs: Path,
    output_tex: Path,
    font_path: Path,
    source_tex: Path | None,
    atlas_size: tuple[int, int] | None,
    target_indices: list[int],
    hide_indices: list[int],
    debug_fill: bool,
) -> None:
    src = source_mbs.read_bytes()
    blob = bytearray(src)
    paragraph = draw_paragraph(font_path)
    tiles: list[tuple[int, Image.Image]] = []
    if atlas_size is None:
        if source_tex is not None:
            atlas_size = Image.open(source_tex).size
        else:
            atlas_size = DEFAULT_ATLAS_SIZE

    for idx in target_indices:
        x0, y0, x1, y1 = screen_bbox(quad_vertices(src, idx))
        x0 = max(0, min(959, x0))
        y0 = max(0, min(543, y0))
        x1 = max(x0 + 1, min(960, x1))
        y1 = max(y0 + 1, min(544, y1))
        if debug_fill:
            hue = (idx * 47) % 255
            color = (hue, (hue * 3) % 255, (hue * 5) % 255, 220)
            tile = make_debug_tile((x1 - x0, y1 - y0), idx, color)
        else:
            tile = paragraph.crop((x0, y0, x1, y1))
        tiles.append((idx, tile))

    placements = pack_tiles(tiles, atlas_size)
    atlas = Image.new("RGBA", atlas_size, (0, 0, 0, 0))
    for idx, crop in tiles:
        x0, y0, x1, y1 = placements[idx]
        atlas.alpha_composite(crop, (x0, y0))
        remap_uv(blob, idx, (x0, y0, x1, y1))

    for idx in hide_indices:
        hide_quad(blob, idx)

    output_mbs.parent.mkdir(parents=True, exist_ok=True)
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_mbs.write_bytes(blob)
    atlas.save(output_tex)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", required=True)
    ap.add_argument("--output-mbs", required=True)
    ap.add_argument("--output-texture", required=True)
    ap.add_argument("--font", required=True)
    ap.add_argument("--source-texture")
    ap.add_argument("--atlas-size")
    ap.add_argument("--target-indices", default="40-79")
    ap.add_argument("--hide-indices", default="80-115")
    ap.add_argument("--debug-fill", action="store_true")
    args = ap.parse_args()

    atlas_size = None
    if args.atlas_size:
        w, h = args.atlas_size.lower().split("x", 1)
        atlas_size = (int(w), int(h))

    build_texture_and_mbs(
        Path(args.source_mbs),
        Path(args.output_mbs),
        Path(args.output_texture),
        Path(args.font),
        Path(args.source_texture) if args.source_texture else None,
        atlas_size,
        parse_index_list(args.target_indices),
        parse_index_list(args.hide_indices),
        args.debug_fill,
    )


if __name__ == "__main__":
    main()
