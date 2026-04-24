from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20
ATLAS_SIZE = (512, 512)


def quad_offset(index: int) -> int:
    return MBS_TABLE_OFFSET + index * QUAD_SIZE


def write_quad(
    blob: bytearray,
    index: int,
    *,
    screen_rect: tuple[float, float, float, float],
    uv_rect: tuple[float, float, float, float],
    color: int,
) -> None:
    """Write a narration-carrier quad using the ORIGINAL opening01.mbs vertex
    pairing, which implements a 90° UV-to-screen rotation:

        v0: (u_min, v_min)  ↔  screen TL
        v1: (u_min, v_max)  ↔  screen TR
        v2: (u_max, v_max)  ↔  screen BR
        v3: (u_max, v_min)  ↔  screen BL

    UV u-axis drives screen y-axis, UV v-axis drives screen x-axis.
    Atlas tiles meant for this carrier must be stored rotated 90° in the atlas.
    """
    x0, y0, x1, y1 = screen_rect     # top-left origin, y0=top, y1=bottom
    u0, v0, u1, v1 = uv_rect          # pixel coords in atlas, v0<v1, u0<u1
    sx0, sx1 = x0 - 480.0, x1 - 480.0
    sy_top = 272.0 - y0
    sy_bot = 272.0 - y1
    verts = [
        (color, u0, v0, sx0, sy_top),   # v0: UV TL ↔ screen TL
        (color, u0, v1, sx1, sy_top),   # v1: UV BL ↔ screen TR
        (color, u1, v1, sx1, sy_bot),   # v2: UV BR ↔ screen BR
        (color, u1, v0, sx0, sy_bot),   # v3: UV TR ↔ screen BL
    ]
    base = quad_offset(index)
    for i, vert in enumerate(verts):
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, *vert)


def hide_quad(blob: bytearray, index: int) -> None:
    write_quad(
        blob,
        index,
        screen_rect=(-1600.0, -1600.0, -1598.0, -1598.0),
        uv_rect=(0.0, 0.0, 1.0, 1.0),
        color=0x00000000,
    )


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


def render_horizontal_text_tile(text: str, font: ImageFont.FreeTypeFont) -> Image.Image:
    stroke = max(2, font.size // 14)
    dummy = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    box = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font, stroke_width=stroke)
    pad_x = 10
    pad_y = 8
    tile_w = (box[2] - box[0]) + pad_x * 2
    tile_h = (box[3] - box[1]) + pad_y * 2
    tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)
    draw.text(
        (pad_x - box[0], pad_y - box[1]),
        text,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=stroke,
        stroke_fill=(255, 255, 255, 255),
    )
    return tile


def build_texture(font_path: Path, output_path: Path, rotate: int = -90) -> dict[str, tuple[int, int, int, int]]:
    """Render 4 narration lines into a 512x512 atlas.

    Each line is rendered horizontally first, then rotated 90° so the
    carrier's rotated UV-mapping produces a horizontal line on screen.
    `rotate` is the PIL rotation angle: -90 means clockwise 90°.
    """
    atlas = Image.new("RGBA", ATLAS_SIZE, (0, 0, 0, 0))
    texts = {
        "line1": ("헤아릴 수 없이 흩어진 마검들.", 58),
        "line2": ("칼집에서 뽑히는 순간,", 54),
        "line3": ("피에 굶주린 듯 곧장 생명을 탐한다.", 54),
        "line4": ("그 힘에 스러진 이들의 운명을 보라.", 54),
    }
    rects: dict[str, tuple[int, int, int, int]] = {}
    x = 8
    y = 8
    row_w = 0
    for key, (text, start_size) in texts.items():
        font = fit_font(text, font_path, 460, 88, start_size)
        h_tile = render_horizontal_text_tile(text, font)
        v_tile = h_tile.rotate(rotate, expand=True)  # rotate to vertical
        if y + v_tile.height > ATLAS_SIZE[1] - 8:
            y = 8
            x += row_w + 12
            row_w = 0
        atlas.alpha_composite(v_tile, (x, y))
        rects[key] = (x, y, x + v_tile.width, y + v_tile.height)
        y += v_tile.height + 12
        row_w = max(row_w, v_tile.width)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output_path)
    return rects


def build_debug_texture(output_path: Path) -> dict[str, tuple[int, int, int, int]]:
    """Build an atlas with 4 labeled debug tiles — lets us visually confirm
    the UV-to-screen rotation before rendering Korean text.

    Each tile has a big letter + distinct background color in corners so
    the rotation direction is unambiguous on screen.
    """
    atlas = Image.new("RGBA", ATLAS_SIZE, (0, 0, 0, 0))
    tiles = [
        ("line1", "1 TOP", (255, 80, 80, 255)),
        ("line2", "2 MID", (80, 255, 80, 255)),
        ("line3", "3 LOW", (80, 160, 255, 255)),
        ("line4", "4 BOT", (255, 255, 80, 255)),
    ]
    rects: dict[str, tuple[int, int, int, int]] = {}
    tile_w, tile_h = 200, 60
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font = ImageFont.load_default()
    x = 8
    y = 8
    for key, label, color in tiles:
        h_tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(h_tile)
        d.rectangle([0, 0, tile_w - 1, tile_h - 1], outline=(255, 255, 255, 255), width=2)
        d.rectangle([0, 0, 24, 24], fill=(255, 0, 0, 255))      # TL corner marker (red)
        d.rectangle([tile_w - 24, 0, tile_w - 1, 24], fill=(0, 255, 0, 255))  # TR (green)
        d.text((tile_w // 2 - 40, tile_h // 2 - 18), label, font=font, fill=color)
        v_tile = h_tile.rotate(-90, expand=True)
        if y + v_tile.height > ATLAS_SIZE[1] - 8:
            y = 8
            x += tile_w + 20  # tile_w because rotated tile is ~tile_h wide, gap for safety
        atlas.alpha_composite(v_tile, (x, y))
        rects[key] = (x, y, x + v_tile.width, y + v_tile.height)
        y += v_tile.height + 10
    atlas.save(output_path)
    return rects


LINE_LAYOUTS = [
    # (key, shadow_idx, main_idx, screen_rect top-left-origin)
    ("line1", 85, 82, (160.0, 172.0, 800.0, 206.0)),
    ("line2", 88, 91, (180.0, 222.0, 780.0, 258.0)),
    ("line3", 94, 97, (108.0, 272.0, 852.0, 308.0)),
    ("line4", 100, 109, (120.0, 322.0, 840.0, 358.0)),
]


def apply_layouts(blob: bytearray, rects: dict[str, tuple[int, int, int, int]], *, keep: set[int] | None) -> None:
    for idx in range(40, 116):
        if keep is not None and idx not in keep:
            hide_quad(blob, idx)
        elif keep is None:
            hide_quad(blob, idx)
    for key, shadow_idx, main_idx, (x0, y0, x1, y1) in LINE_LAYOUTS:
        u0, v0, u1, v1 = rects[key]
        if keep is None or shadow_idx in keep:
            write_quad(
                blob,
                shadow_idx,
                screen_rect=(x0 + 2.0, y0 + 2.0, x1 + 2.0, y1 + 2.0),
                uv_rect=(u0, v0, u1, v1),
                color=0xFF402000,
            )
        if keep is None or main_idx in keep:
            write_quad(
                blob,
                main_idx,
                screen_rect=(x0, y0, x1, y1),
                uv_rect=(u0, v0, u1, v1),
                color=0xFFFFFFFF,
            )


def build_mbs(
    source_path: Path,
    output_path: Path,
    rects: dict[str, tuple[int, int, int, int]],
    *,
    keep: set[int] | None = None,
) -> None:
    blob = bytearray(source_path.read_bytes())
    apply_layouts(blob, rects, keep=keep)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(blob)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-mbs", required=True)
    parser.add_argument("--output-mbs", required=True)
    parser.add_argument("--output-texture", required=True)
    parser.add_argument("--font")
    parser.add_argument("--keep", nargs="*", type=int)
    parser.add_argument("--debug-tiles", action="store_true",
                        help="Render labeled debug tiles instead of Korean text")
    parser.add_argument("--rotate", type=int, default=-90,
                        help="PIL rotation angle for text tiles (default -90 = CW)")
    args = parser.parse_args()

    out_tex = Path(args.output_texture)
    if args.debug_tiles:
        rects = build_debug_texture(out_tex)
    else:
        if not args.font:
            parser.error("--font is required when not using --debug-tiles")
        rects = build_texture(Path(args.font), out_tex, rotate=args.rotate)

    keep = set(args.keep) if args.keep else None
    build_mbs(Path(args.source_mbs), Path(args.output_mbs), rects, keep=keep)


if __name__ == "__main__":
    main()
