from __future__ import annotations

import argparse
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20

LINES = [
    "헤아릴 수 없이 흩어진 마검들.",
    "칼집에서 뽑히는 순간,",
    "피에 굶주린 듯 곧장 생명을 탐한다.",
    "그 힘에 스러진 이들의 운명을 보라.",
]

# Main white text layer. Groups chosen from screen-space probes.
MAIN_ROWS = [
    [41, 44, 52, 53, 40, 43, 47],
    [42, 46, 49, 50, 51, 48, 45],
    [56, 58, 61, 62, 57, 54],
    [60, 55, 59, 63],
]

# Shadow / dark support layer.
SHADOW_ROWS = [
    [65, 66, 67, 68],
    [70, 71, 72, 73],
    [74, 75, 76, 77],
    [69, 78, 79],
]


def read_quad(blob: bytes, index: int) -> list[tuple[int, float, float, float, float]]:
    off = MBS_TABLE_OFFSET + index * QUAD_SIZE
    return [struct.unpack_from("<Iffff", blob, off + i * VERTEX_SIZE) for i in range(4)]


def uv_box(quad: list[tuple[int, float, float, float, float]]) -> tuple[int, int, int, int]:
    us = [v[1] for v in quad]
    vs = [v[2] for v in quad]
    return int(min(us)), int(min(vs)), int(max(us)), int(max(vs))


def parse_groups(raw: str) -> list[list[int]]:
    groups: list[list[int]] = []
    for chunk in raw.split("/"):
        chunk = chunk.strip()
        if not chunk:
            continue
        groups.append([int(part) for part in chunk.split(",") if part.strip()])
    return groups


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    rect: tuple[int, int, int, int],
    font_path: Path,
) -> tuple[ImageFont.FreeTypeFont, int]:
    x0, y0, x1, y1 = rect
    for size in range(44, 15, -2):
        font = ImageFont.truetype(str(font_path), size)
        stroke = max(1, size // 16)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        if box[2] - box[0] <= (x1 - x0 - 6) and box[3] - box[1] <= (y1 - y0 - 4):
            return font, stroke
    size = 16
    return ImageFont.truetype(str(font_path), size), 1


def draw_line_into_union(
    img: Image.Image,
    text: str,
    boxes: list[tuple[int, int, int, int]],
    font_path: Path,
) -> None:
    ux0 = min(b[0] for b in boxes)
    uy0 = min(b[1] for b in boxes)
    ux1 = max(b[2] for b in boxes)
    uy1 = max(b[3] for b in boxes)
    draw = ImageDraw.Draw(img)

    for box in boxes:
        draw.rectangle(box, fill=(0, 0, 0, 0))

    font, stroke = fit_font(draw, text, (ux0, uy0, ux1, uy1), font_path)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    tx = ux0 + ((ux1 - ux0) - (bbox[2] - bbox[0])) // 2 - bbox[0]
    ty = uy0 + ((uy1 - uy0) - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text(
        (tx, ty),
        text,
        font=font,
        fill=(255, 255, 255, 255),
        stroke_width=stroke,
        stroke_fill=(255, 255, 255, 255),
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", required=True)
    ap.add_argument("--source-texture", required=True)
    ap.add_argument("--output-texture", required=True)
    ap.add_argument("--font", required=True)
    ap.add_argument("--lines", nargs=4)
    ap.add_argument("--main-groups")
    ap.add_argument("--shadow-groups")
    ap.add_argument("--skip-main", action="store_true")
    ap.add_argument("--skip-shadow", action="store_true")
    args = ap.parse_args()

    blob = Path(args.source_mbs).read_bytes()
    tex = Image.open(args.source_texture).convert("RGBA")
    font_path = Path(args.font)
    lines = args.lines or LINES
    main_rows = parse_groups(args.main_groups) if args.main_groups else MAIN_ROWS
    shadow_rows = parse_groups(args.shadow_groups) if args.shadow_groups else SHADOW_ROWS

    if not args.skip_main:
        for text, row in zip(lines, main_rows):
            boxes = [uv_box(read_quad(blob, idx)) for idx in row]
            draw_line_into_union(tex, text, boxes, font_path)

    if not args.skip_shadow:
        for text, row in zip(lines, shadow_rows):
            boxes = [uv_box(read_quad(blob, idx)) for idx in row]
            draw_line_into_union(tex, text, boxes, font_path)

    out = Path(args.output_texture)
    out.parent.mkdir(parents=True, exist_ok=True)
    tex.save(out)


if __name__ == "__main__":
    main()
