"""Build a Korean opening01 atlas WITHOUT touching opening01.mbs.

Approach: for every visible carrier in 80..115, read its original UV rect
(pixel coords in the 512×512 atlas) and its screen bbox. Crop the Korean
paragraph at the carrier's screen bbox, paint that crop at the carrier's
UV rect in a fresh atlas. Carriers then render the Korean letters at the
exact screen positions the English letters used to occupy.

Vertex format per opening01.mbs convention:
  (color u32, f1 float, f2 float, sx float, sy float)
where f1 is atlas-v (vertical / image y), f2 is atlas-u (horizontal / image x).
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

KOREAN_LINES = [
    "헤아릴 수 없이 흩어진 마검들.",
    "칼집에서 뽑히는 순간,",
    "피에 굶주린 듯 곧장 생명을 탐한다.",
    "그 힘에 스러진 이들의 운명을 보라.",
]
LINE_Y_ROWS = [(170, 213), (240, 278), (314, 347), (384, 417)]
RED_CARRIERS = {85, 86, 102, 106, 107}
# Only carriers whose UV rect aspect ratio matches their screen bbox (no
# significant resize distortion). Other carriers have transposed or severely
# stretched UV rects that reshape the Korean glyphs into illegible blocks.
ASPECT_MATCHED_CARRIERS = {80, 88, 91, 94, 95, 97, 100, 103, 109, 115}


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
    """Return (x0, y0, x1, y1) in atlas image pixel coordinates.
    Hypothesis A (confirmed by atlas inspection): f1 = atlas x,
    f2 = atlas y. Original atlas stores text horizontally, so carrier
    UV rects are horizontal strips matching their screen bboxes."""
    xs = [v[1] for v in vs]   # f1 ↔ atlas x
    ys = [v[2] for v in vs]   # f2 ↔ atlas y
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def compute_line_boxes():
    # Hard-coded line x ranges, just visual guidance for paragraph layout.
    return [
        (100, LINE_Y_ROWS[0][0], 860, LINE_Y_ROWS[0][1]),
        (100, LINE_Y_ROWS[1][0], 860, LINE_Y_ROWS[1][1]),
        (20,  LINE_Y_ROWS[2][0], 940, LINE_Y_ROWS[2][1]),
        (40,  LINE_Y_ROWS[3][0], 920, LINE_Y_ROWS[3][1]),
    ]


def fit_font(line_boxes, font_path: Path, max_size=28, min_size=14):
    size = max_size
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size=size)
        stroke = max(2, size // 14)
        ok = True
        for text, (x0, y0, x1, y1) in zip(KOREAN_LINES, line_boxes):
            box = font.getbbox(text, stroke_width=stroke)
            w = box[2] - box[0]; h = box[3] - box[1]
            if w > (x1 - x0 - 8) or h > (y1 - y0 - 4):
                ok = False; break
        if ok: return font
        size -= 1
    return ImageFont.truetype(str(font_path), size=min_size)


def draw_paragraph(font_path: Path) -> Image.Image:
    line_boxes = compute_line_boxes()
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


def build_atlas(source_mbs: Path, output_tex: Path, font_path: Path) -> dict:
    src = source_mbs.read_bytes()
    paragraph, chosen_size = draw_paragraph(font_path)
    atlas = Image.new("RGBA", ATLAS_SIZE, (0, 0, 0, 0))
    used: list[int] = []
    skipped: list[tuple[int, str]] = []

    for idx in range(80, 116):
        vs = read_quad(src, idx)
        color = vs[0][0]
        if idx in RED_CARRIERS:
            skipped.append((idx, "red-highlight")); continue
        if idx not in ASPECT_MATCHED_CARRIERS:
            skipped.append((idx, "aspect-mismatched")); continue
        # fully transparent carriers
        if (color >> 24) & 0xFF == 0:
            skipped.append((idx, "alpha=0")); continue
        sx0, sy0, sx1, sy1 = screen_bbox_top_left(vs)
        # off-screen
        if sx0 < 0 or sx1 > 960 or sy0 < 0 or sy1 > 544:
            skipped.append((idx, f"off-screen {(sx0,sy0,sx1,sy1)}")); continue
        ux0, uy0, ux1, uy1 = uv_rect_image_coords(vs)
        if ux0 < 0 or ux1 > 512 or uy0 < 0 or uy1 > 512 or ux0 == ux1 or uy0 == uy1:
            skipped.append((idx, f"bad-uv {(ux0,uy0,ux1,uy1)}")); continue

        # Clamp screen bbox
        sx0 = max(0, min(959, sx0)); sy0 = max(0, min(543, sy0))
        sx1 = max(sx0 + 1, min(960, sx1)); sy1 = max(sy0 + 1, min(544, sy1))

        crop = paragraph.crop((sx0, sy0, sx1, sy1))
        target_w = ux1 - ux0
        target_h = uy1 - uy0
        # Normal mapping — no rotation. Resize if screen/UV rect sizes differ.
        if (crop.width, crop.height) != (target_w, target_h):
            crop = crop.resize((max(1, target_w), max(1, target_h)), Image.LANCZOS)
        atlas.alpha_composite(crop, (ux0, uy0))
        used.append(idx)

    output_tex.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output_tex)
    return {
        "used": used,
        "skipped": skipped,
        "font_size": chosen_size,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", default="temp/cpk_extract/_US/GUI/opening01.mbs")
    ap.add_argument("--output-texture", default="temp/opening_test/atlas.png")
    ap.add_argument("--font", default="fonts/Griun_PolSensibility-Rg.ttf")
    args = ap.parse_args()
    info = build_atlas(Path(args.source_mbs), Path(args.output_texture), Path(args.font))
    print(f"font size: {info['font_size']}px")
    print(f"used ({len(info['used'])}): {info['used']}")
    print(f"skipped ({len(info['skipped'])}): {info['skipped']}")


if __name__ == "__main__":
    main()
