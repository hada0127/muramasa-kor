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
    x0, y0, x1, y1 = screen_rect
    u0, v0, u1, v1 = uv_rect
    verts = [
        # For custom direct-line quads we use a normal UV mapping:
        # TL, TR, BR, BL on both screen and atlas.
        (color, u0, v0, x0 - 480.0, 272.0 - y0),
        (color, u1, v0, x1 - 480.0, 272.0 - y0),
        (color, u1, v1, x1 - 480.0, 272.0 - y1),
        (color, u0, v1, x0 - 480.0, 272.0 - y1),
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


def draw_text_line(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    text: str,
    font_path: Path,
) -> None:
    x0, y0, x1, y1 = rect
    max_w = x1 - x0 - 24
    max_h = y1 - y0 - 20
    font = fit_font(text, font_path, max_w, max_h, start_size=max_h)
    stroke = max(2, font.size // 14)
    box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    w = box[2] - box[0]
    h = box[3] - box[1]
    tx = x0 + (x1 - x0 - w) // 2 - box[0]
    ty = y0 + (y1 - y0 - h) // 2 - box[1]
    draw.text(
        (tx, ty),
        text,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=stroke,
        stroke_fill=(255, 255, 255, 255),
    )


def build_texture(font_path: Path, output_path: Path) -> dict[str, tuple[int, int, int, int]]:
    atlas = Image.new("RGBA", ATLAS_SIZE, (0, 0, 0, 0))
    texts = {
        "line1": ("헤아릴 수 없이 흩어진 마검들.", 58),
        "line2": ("칼집에서 뽑히는 순간,", 54),
        "line3": ("피에 굶주린 듯 곧장 생명을 탐한다.", 54),
        "line4": ("그 힘에 스러진 이들의 운명을 보라.", 54),
    }
    rects: dict[str, tuple[int, int, int, int]] = {}
    x = 24
    y = 24
    row_h = 0
    for key, (text, start_size) in texts.items():
        font = fit_font(text, font_path, 460, 88, start_size)
        stroke = max(2, font.size // 14)
        dummy = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        box = ImageDraw.Draw(dummy).textbbox((0, 0), text, font=font, stroke_width=stroke)
        pad_x = 10
        pad_y = 8
        tile_w = (box[2] - box[0]) + pad_x * 2
        tile_h = (box[3] - box[1]) + pad_y * 2
        if x + tile_w > ATLAS_SIZE[0] - 24:
            x = 24
            y += row_h + 20
            row_h = 0
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
        atlas.alpha_composite(tile, (x, y))
        rects[key] = (x, y, x + tile_w, y + tile_h)
        x += tile_w + 20
        row_h = max(row_h, tile_h)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output_path)
    return rects


def build_mbs(source_path: Path, output_path: Path, rects: dict[str, tuple[int, int, int, int]]) -> None:
    blob = bytearray(source_path.read_bytes())
    keep = {82, 85, 88, 91, 94, 97, 100, 109}
    for idx in range(40, 116):
        if idx not in keep:
            hide_quad(blob, idx)

    line_layouts = [
        ("line1", 85, 82, (160.0, 172.0, 800.0, 206.0)),
        ("line2", 88, 91, (180.0, 222.0, 780.0, 258.0)),
        ("line3", 94, 97, (108.0, 272.0, 852.0, 308.0)),
        ("line4", 100, 109, (120.0, 322.0, 840.0, 358.0)),
    ]

    for key, shadow_idx, main_idx, (x0, y0, x1, y1) in line_layouts:
        u0, v0, u1, v1 = rects[key]
        write_quad(
            blob,
            shadow_idx,
            screen_rect=(x0 + 2.0, y0 + 2.0, x1 + 2.0, y1 + 2.0),
            uv_rect=(u0, v0, u1, v1),
            color=0xFF402000,
        )
        write_quad(
            blob,
            main_idx,
            screen_rect=(x0, y0, x1, y1),
            uv_rect=(u0, v0, u1, v1),
            color=0xFFFFFFFF,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(blob)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-mbs", required=True)
    parser.add_argument("--output-mbs", required=True)
    parser.add_argument("--output-texture", required=True)
    parser.add_argument("--font", required=True)
    parser.add_argument("--keep", nargs="*", type=int)
    args = parser.parse_args()

    rects = build_texture(Path(args.font), Path(args.output_texture))
    if args.keep:
        # Override default visible quads for debugging.
        blob = bytearray(Path(args.source_mbs).read_bytes())
        keep = set(args.keep)
        for idx in range(40, 116):
            if idx not in keep:
                hide_quad(blob, idx)

        line_layouts = [
            ("line1", 85, 82, (160.0, 172.0, 800.0, 206.0)),
            ("line2", 88, 91, (180.0, 222.0, 780.0, 258.0)),
            ("line3", 94, 97, (108.0, 272.0, 852.0, 308.0)),
            ("line4", 100, 109, (120.0, 322.0, 840.0, 358.0)),
        ]
        for key, shadow_idx, main_idx, (x0, y0, x1, y1) in line_layouts:
            u0, v0, u1, v1 = rects[key]
            if shadow_idx in keep:
                write_quad(blob, shadow_idx, screen_rect=(x0 + 2.0, y0 + 2.0, x1 + 2.0, y1 + 2.0), uv_rect=(u0, v0, u1, v1), color=0xFF402000)
            if main_idx in keep:
                write_quad(blob, main_idx, screen_rect=(x0, y0, x1, y1), uv_rect=(u0, v0, u1, v1), color=0xFFFFFFFF)
        out = Path(args.output_mbs)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(blob)
    else:
        build_mbs(Path(args.source_mbs), Path(args.output_mbs), rects)


if __name__ == "__main__":
    main()
