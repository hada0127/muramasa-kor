from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20
TARGET_INDICES = list(range(55, 64))
HIDE_INDICES = [54, 64] + list(range(80, 116))
STORAGE_RECT = (0, 158, 355, 459)
PARAGRAPH_BBOX = (277, 233, 685, 330)
LINES = [
    "\ud5e4\uc544\ub9b4 \uc218 \uc5c6\uc774 \ud769\uc5b4\uc9c4 \ub9c8\uac80\ub4e4.",
    "\uce7c\uc9d1\uc5d0\uc11c \ubf51\ud788\ub294 \uc21c\uac04,",
    "\ud53c\uc5d0 \uad76\uc8fc\ub9b0 \ub4ef \uace7\uc7a5 \uc0dd\uba85\uc744 \ud0d0\ud55c\ub2e4.",
    "\uadf8 \ud798\uc5d0 \uc2a4\ub7ec\uc9c4 \uc774\ub4e4\uc758 \uc6b4\uba85\uc744 \ubcf4\ub77c.",
]


def quad_offset(index: int) -> int:
    return MBS_TABLE_OFFSET + index * QUAD_SIZE


def quad_vertices(blob: bytes, index: int) -> list[tuple[int, float, float, float, float]]:
    out = []
    base = quad_offset(index)
    for i in range(4):
        out.append(struct.unpack_from("<Iffff", blob, base + i * VERTEX_SIZE))
    return out


def screen_bbox(verts: list[tuple[int, float, float, float, float]]) -> tuple[float, float, float, float]:
    xs = [sx + 480.0 for _, _, _, sx, _ in verts]
    ys = [272.0 - sy for _, _, _, _, sy in verts]
    return min(xs), min(ys), max(xs), max(ys)


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


def remap_uv(blob: bytearray, index: int, rect: tuple[float, float, float, float]) -> None:
    base = quad_offset(index)
    x0, y0, x1, y1 = rect
    old = []
    for i in range(4):
        off = base + i * VERTEX_SIZE
        old.append(struct.unpack_from("<Iffff", blob, off))

    u_min = min(v[1] for v in old)
    u_max = max(v[1] for v in old)
    v_min = min(v[2] for v in old)
    v_max = max(v[2] for v in old)

    for i, (color, u, v, sx, sy) in enumerate(old):
        nu = x0 if abs(u - u_min) <= abs(u - u_max) else x1
        nv = y0 if abs(v - v_min) <= abs(v - v_max) else y1
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, color, float(nu), float(nv), sx, sy)


def fit_font(lines: list[str], font_path: Path, box_w: int, box_h: int) -> ImageFont.FreeTypeFont:
    size = min(52, box_h // len(lines))
    while size >= 18:
        font = ImageFont.truetype(str(font_path), size=size)
        stroke = max(2, size // 14)
        line_boxes = [font.getbbox(line, stroke_width=stroke) for line in lines]
        width = max(box[2] - box[0] for box in line_boxes)
        heights = [box[3] - box[1] for box in line_boxes]
        total_h = sum(heights) + (len(lines) - 1) * max(4, size // 5)
        if width <= box_w and total_h <= box_h:
            return font
        size -= 2
    return ImageFont.truetype(str(font_path), size=18)


def build_paragraph(font_path: Path) -> Image.Image:
    x0, y0, x1, y1 = STORAGE_RECT
    width = x1 - x0
    height = y1 - y0
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = fit_font(LINES, font_path, width - 20, height - 20)
    stroke = max(2, font.size // 14)
    gap = max(4, font.size // 5)
    boxes = [draw.textbbox((0, 0), line, font=font, stroke_width=stroke) for line in LINES]
    heights = [box[3] - box[1] for box in boxes]
    total_h = sum(heights) + (len(LINES) - 1) * gap
    cy = (height - total_h) // 2
    for line, box, line_h in zip(LINES, boxes, heights):
        line_w = box[2] - box[0]
        cx = (width - line_w) // 2 - box[0]
        draw.text(
            (cx, cy - box[1]),
            line,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=stroke,
            stroke_fill=(255, 255, 255, 255),
        )
        cy += line_h + gap
    return img


def map_screen_to_storage(
    bbox: tuple[float, float, float, float],
    paragraph_bbox: tuple[int, int, int, int],
    storage_rect: tuple[int, int, int, int],
) -> tuple[float, float, float, float]:
    px0, py0, px1, py1 = paragraph_bbox
    sx0, sy0, sx1, sy1 = storage_rect
    bw = px1 - px0
    bh = py1 - py0
    sw = sx1 - sx0
    sh = sy1 - sy0
    x0, y0, x1, y1 = bbox
    rx0 = (x0 - px0) / bw
    ry0 = (y0 - py0) / bh
    rx1 = (x1 - px0) / bw
    ry1 = (y1 - py0) / bh
    return (
        sx0 + rx0 * sw,
        sy0 + ry0 * sh,
        sx0 + rx1 * sw,
        sy0 + ry1 * sh,
    )


def patch_texture(src_path: Path, out_path: Path, paragraph: Image.Image) -> None:
    image = Image.open(src_path).convert("RGBA")
    ImageDraw.Draw(image).rectangle(STORAGE_RECT, fill=(0, 0, 0, 0))
    image.alpha_composite(paragraph, (STORAGE_RECT[0], STORAGE_RECT[1]))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def patch_mbs(src_path: Path, out_path: Path) -> None:
    blob = bytearray(src_path.read_bytes())
    for idx in HIDE_INDICES:
        hide_quad(blob, idx)
    for idx in TARGET_INDICES:
        bbox = screen_bbox(quad_vertices(blob, idx))
        remap_uv(blob, idx, map_screen_to_storage(bbox, PARAGRAPH_BBOX, STORAGE_RECT))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(blob)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", required=True)
    ap.add_argument("--source-texture", required=True)
    ap.add_argument("--output-mbs", required=True)
    ap.add_argument("--output-texture", required=True)
    ap.add_argument("--font", required=True)
    args = ap.parse_args()

    paragraph = build_paragraph(Path(args.font))
    patch_texture(Path(args.source_texture), Path(args.output_texture), paragraph)
    patch_mbs(Path(args.source_mbs), Path(args.output_mbs))


if __name__ == "__main__":
    main()
