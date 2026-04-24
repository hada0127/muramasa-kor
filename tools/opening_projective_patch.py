from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20
HIDE_VERTS = [
    (0x00000000, 0.0, 0.0, -2080.0, 1872.0),
    (0x00000000, 0.0, 1.0, -2078.0, 1872.0),
    (0x00000000, 1.0, 1.0, -2078.0, 1870.0),
    (0x00000000, 1.0, 0.0, -2080.0, 1870.0),
]


def quad_offset(index: int) -> int:
    return MBS_TABLE_OFFSET + index * QUAD_SIZE


def read_quad(blob: bytes, index: int) -> list[tuple[int, float, float, float, float]]:
    base = quad_offset(index)
    return [struct.unpack_from("<Iffff", blob, base + i * VERTEX_SIZE) for i in range(4)]


def hide_quad(blob: bytearray, index: int) -> None:
    base = quad_offset(index)
    for i, vert in enumerate(HIDE_VERTS):
        struct.pack_into("<Iffff", blob, base + i * VERTEX_SIZE, *vert)


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


def barycentric(
    p: tuple[float, float],
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> tuple[float, float, float] | None:
    den = ((b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]))
    if abs(den) < 1e-6:
        return None
    w0 = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) / den
    w1 = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) / den
    w2 = 1.0 - w0 - w1
    return w0, w1, w2


def sample_bilinear(img: Image.Image, x: float, y: float) -> tuple[int, int, int, int]:
    w, h = img.size
    x = max(0.0, min(w - 1.001, x))
    y = max(0.0, min(h - 1.001, y))
    x0 = int(math.floor(x))
    y0 = int(math.floor(y))
    x1 = min(x0 + 1, w - 1)
    y1 = min(y0 + 1, h - 1)
    dx = x - x0
    dy = y - y0
    p00 = img.getpixel((x0, y0))
    p10 = img.getpixel((x1, y0))
    p01 = img.getpixel((x0, y1))
    p11 = img.getpixel((x1, y1))
    out = []
    for i in range(4):
        top = p00[i] * (1.0 - dx) + p10[i] * dx
        bot = p01[i] * (1.0 - dx) + p11[i] * dx
        out.append(int(round(top * (1.0 - dy) + bot * dy)))
    return tuple(out)  # type: ignore[return-value]


def clear_uv_bbox(tex: Image.Image, uv_pts: list[tuple[float, float]]) -> None:
    draw = ImageDraw.Draw(tex)
    xs = [p[0] for p in uv_pts]
    ys = [p[1] for p in uv_pts]
    draw.rectangle((min(xs), min(ys), max(xs), max(ys)), fill=(0, 0, 0, 0))


def clear_target_region(tex: Image.Image, quads: list[list[tuple[int, float, float, float, float]]]) -> None:
    xs: list[float] = []
    ys: list[float] = []
    for quad in quads:
        xs.extend(v[1] for v in quad)
        ys.extend(v[2] for v in quad)
    if not xs or not ys:
        return
    ImageDraw.Draw(tex).rectangle((min(xs), min(ys), max(xs), max(ys)), fill=(0, 0, 0, 0))


def bake_quad(
    dest: Image.Image,
    screen: Image.Image,
    uv_pts: list[tuple[float, float]],
    sc_pts: list[tuple[float, float]],
) -> None:
    tris = [(0, 1, 2), (0, 2, 3)]
    for ia, ib, ic in tris:
        ua, ub, uc = uv_pts[ia], uv_pts[ib], uv_pts[ic]
        sa, sb, sc = sc_pts[ia], sc_pts[ib], sc_pts[ic]
        min_x = max(0, int(math.floor(min(ua[0], ub[0], uc[0]))))
        max_x = min(dest.width - 1, int(math.ceil(max(ua[0], ub[0], uc[0]))))
        min_y = max(0, int(math.floor(min(ua[1], ub[1], uc[1]))))
        max_y = min(dest.height - 1, int(math.ceil(max(ua[1], ub[1], uc[1]))))
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                bc = barycentric((x + 0.5, y + 0.5), ua, ub, uc)
                if bc is None:
                    continue
                w0, w1, w2 = bc
                if w0 < -1e-4 or w1 < -1e-4 or w2 < -1e-4:
                    continue
                sx = sa[0] * w0 + sb[0] * w1 + sc[0] * w2
                sy = sa[1] * w0 + sb[1] * w1 + sc[1] * w2
                px = sample_bilinear(screen, sx, sy)
                if px[3]:
                    dest.putpixel((x, y), px)


def make_screen_text(font_path: Path) -> Image.Image:
    screen = Image.new("RGBA", (960, 544), (0, 0, 0, 0))
    draw = ImageDraw.Draw(screen)
    lines = [
        ("헤아릴 수 없이 흩어진 마검들.", (120, 170, 836, 210)),
        ("칼집에서 뽑히는 순간,", (168, 216, 792, 252)),
        ("피에 굶주린 듯 곧장 생명을 탐한다.", (100, 258, 860, 300)),
        ("그 힘에 스러진 이들의 운명을 보라.", (140, 304, 820, 342)),
    ]
    size = 40
    while size >= 18:
        font = ImageFont.truetype(str(font_path), size=size)
        ok = True
        for text, (x0, y0, x1, y1) in lines:
            stroke = max(2, size // 14)
            box = font.getbbox(text, stroke_width=stroke)
            if box[2] - box[0] > (x1 - x0 - 8) or box[3] - box[1] > (y1 - y0 - 6):
                ok = False
                break
        if ok:
            break
        size -= 2
    font = ImageFont.truetype(str(font_path), size=size)
    stroke = max(2, size // 14)
    for text, (x0, y0, x1, y1) in lines:
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
    return screen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", required=True)
    ap.add_argument("--source-texture", required=True)
    ap.add_argument("--output-mbs", required=True)
    ap.add_argument("--output-texture", required=True)
    ap.add_argument("--font", required=True)
    ap.add_argument("--target-indices", default="65-79")
    ap.add_argument("--hide-indices", default="80-115")
    args = ap.parse_args()

    src_blob = Path(args.source_mbs).read_bytes()
    out_blob = bytearray(src_blob)
    tex = Image.open(args.source_texture).convert("RGBA")
    screen = make_screen_text(Path(args.font))

    target_quads = [(idx, read_quad(src_blob, idx)) for idx in parse_index_list(args.target_indices)]
    clear_target_region(tex, [quad for _, quad in target_quads])
    for idx, quad in target_quads:
        uv_pts = [(v[1], v[2]) for v in quad]
        sc_pts = [(v[3] + 480.0, 272.0 - v[4]) for v in quad]
        bake_quad(tex, screen, uv_pts, sc_pts)

    for idx in parse_index_list(args.hide_indices):
        hide_quad(out_blob, idx)

    out_mbs = Path(args.output_mbs)
    out_tex = Path(args.output_texture)
    out_mbs.parent.mkdir(parents=True, exist_ok=True)
    out_tex.parent.mkdir(parents=True, exist_ok=True)
    out_mbs.write_bytes(out_blob)
    tex.save(out_tex)


if __name__ == "__main__":
    main()
