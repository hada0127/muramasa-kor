"""Build Korean opening atlas using multi-carrier-per-line.

For each narration line, use ALL aspect-matched 1:1 carriers on that line
together. Render the Korean sentence onto a paragraph canvas that spans
the line's screen x-range union. Each carrier crops its screen bbox from
the paragraph and pastes at its UV rect (1:1, no resize needed).

This spreads the sentence across multiple carriers on a line, giving a
larger overall font size.

MBS is NOT modified.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20
ATLAS_SIZE = (512, 512)

MAIN_COLOR = 0xFFFFFFFF
SHADOW_COLOR = 0xFF402000
RED_COLOR = 0xFF0000FF
LARGE_CONTAINER_CARRIERS = {90, 96, 111, 114}

KOREAN_SENTENCES = [
    "헤아릴 수 없이 흩어진 마검들",
    "칼집에서 뽑히는 순간",
    "피에 굶주린 듯 생명을 탐한다",
    "스러진 이들의 운명을 보라",
]

MIN_FONT_SIZE = 22
MAX_FONT_SIZE = 48


def quad_offset(idx: int) -> int:
    return MBS_TABLE_OFFSET + idx * QUAD_SIZE


def read_quad(src: bytes, idx: int):
    base = quad_offset(idx)
    return [struct.unpack_from("<Iffff", src, base + i * VERTEX_SIZE) for i in range(4)]


def uv_rect(vs) -> tuple[int, int, int, int]:
    xs = [v[1] for v in vs]; ys = [v[2] for v in vs]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def screen_rect(vs) -> tuple[int, int, int, int]:
    sxs = [v[3] + 480.0 for v in vs]
    sys_ = [272.0 - v[4] for v in vs]
    return int(min(sxs)), int(min(sys_)), int(max(sxs)), int(max(sys_))


def is_rectangular(vs) -> bool:
    f1s = {round(v[1], 1) for v in vs}
    f2s = {round(v[2], 1) for v in vs}
    return len(f1s) == 2 and len(f2s) == 2


def is_aspect_matched(sc, uv, tol: float = 0.15) -> bool:
    """True if screen and UV rects have matching aspect (within tolerance)."""
    sc_w = sc[2] - sc[0]; sc_h = sc[3] - sc[1]
    uv_w = uv[2] - uv[0]; uv_h = uv[3] - uv[1]
    if sc_h == 0 or uv_h == 0: return False
    sa = sc_w / sc_h; ua = uv_w / uv_h
    if max(sa, ua) / max(min(sa, ua), 0.001) > 1 + tol:
        return False
    # Also require same orientation (both landscape, both portrait, or both square)
    return (sc_w > sc_h) == (uv_w > uv_h) or abs(sa - ua) < 0.3


def assign_line(cy: float) -> int:
    if cy < 220: return 0
    if cy < 300: return 1
    if cy < 370: return 2
    return 3


def fit_text_to_width(text: str, max_w: int, max_h: int, font_path: Path,
                      max_size: int, min_size: int) -> ImageFont.FreeTypeFont:
    size = max_size
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size=size)
        stroke = max(2, size // 10)
        box = font.getbbox(text, stroke_width=stroke)
        w = box[2] - box[0]; h = box[3] - box[1]
        if w <= max_w - 8 and h <= max_h - 6:
            return font
        size -= 1
    return ImageFont.truetype(str(font_path), size=min_size)


def build_atlas(source_mbs: Path, source_atlas: Path, font_path: Path,
                output: Path) -> dict:
    src = source_mbs.read_bytes()
    atlas = Image.open(source_atlas).convert("RGBA")
    arr = np.array(atlas)
    original_alpha = arr[:, :, 3].copy()

    # Gather candidates per line: rectangular + aspect-matched main carriers
    line_carriers: dict[int, list] = {0: [], 1: [], 2: [], 3: []}
    stats = {"kept": 0, "cleared": 0}

    for idx in range(40, 116):
        vs = read_quad(src, idx)
        color = vs[0][0]
        ux0, uy0, ux1, uy1 = uv_rect(vs)
        if ux0 < 0 or uy0 < 0 or ux1 > 512 or uy1 > 512: continue
        if ux0 == ux1 or uy0 == uy1: continue

        def clear():
            arr[uy0:uy1, ux0:ux1, 3] = 0
            stats["cleared"] += 1

        if idx in LARGE_CONTAINER_CARRIERS:
            clear(); continue
        if color in (SHADOW_COLOR, RED_COLOR):
            clear(); continue
        if color != MAIN_COLOR:
            continue

        sx0, sy0, sx1, sy1 = screen_rect(vs)
        if not (0 <= sx0 and sx1 <= 960 and 0 <= sy0 and sy1 <= 544):
            clear(); continue
        if not (160 <= sy0 and sy1 <= 420):
            clear(); continue

        region = original_alpha[uy0:uy1, ux0:ux1]
        coverage = float(np.mean(region > 30)) if region.size else 0.0
        if coverage < 0.15:
            clear(); continue

        if not is_rectangular(vs):
            clear(); continue
        if not is_aspect_matched((sx0, sy0, sx1, sy1), (ux0, uy0, ux1, uy1)):
            clear(); continue

        cy = (sy0 + sy1) / 2.0
        line = assign_line(cy)
        line_carriers[line].append({
            "idx": idx,
            "screen": (sx0, sy0, sx1, sy1),
            "uv": (ux0, uy0, ux1, uy1),
        })
        stats["kept"] += 1

    # Clear all candidate UV regions (will redraw)
    for carriers in line_carriers.values():
        for c in carriers:
            ux0, uy0, ux1, uy1 = c["uv"]
            arr[uy0:uy1, ux0:ux1, 3] = 0

    atlas = Image.fromarray(arr, mode="RGBA")

    # For each line, build a paragraph canvas at screen resolution and draw
    # Korean text centered across the line's x-range union. Each carrier
    # crops its part.
    font_sizes = {}
    for line_idx, carriers in line_carriers.items():
        if not carriers: continue
        text = KOREAN_SENTENCES[line_idx]

        # Line x-range = union of carrier screen x
        x0_union = min(c["screen"][0] for c in carriers)
        x1_union = max(c["screen"][2] for c in carriers)
        y0_union = min(c["screen"][1] for c in carriers)
        y1_union = max(c["screen"][3] for c in carriers)
        w_union = x1_union - x0_union
        h_union = y1_union - y0_union

        # Fit font to full line width (much larger than single carrier)
        font = fit_text_to_width(text, w_union, h_union, font_path,
                                 max_size=MAX_FONT_SIZE, min_size=MIN_FONT_SIZE)
        font_sizes[line_idx] = font.size
        stroke = max(2, font.size // 10)

        # Draw text into a 960x544 full-screen canvas at the line's y range
        para = Image.new("RGBA", (960, 544), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(para)
        tbox = pdraw.textbbox((0, 0), text, font=font, stroke_width=stroke)
        tw = tbox[2] - tbox[0]; th = tbox[3] - tbox[1]
        tx = x0_union + (w_union - tw) // 2 - tbox[0]
        ty = y0_union + (h_union - th) // 2 - tbox[1]
        pdraw.text((tx, ty), text, font=font,
                   fill=(255, 255, 255, 255),
                   stroke_width=stroke, stroke_fill=(255, 255, 255, 255))

        # Each carrier crops its screen bbox from paragraph and pastes at
        # its UV rect (1:1 since aspect matched).
        for c in carriers:
            sx0, sy0, sx1, sy1 = c["screen"]
            ux0, uy0, ux1, uy1 = c["uv"]
            crop = para.crop((sx0, sy0, sx1, sy1))
            # Resize to UV rect dims (should be ~1:1 since aspect matched)
            uv_w = ux1 - ux0; uv_h = uy1 - uy0
            if (crop.width, crop.height) != (uv_w, uv_h):
                crop = crop.resize((max(1, uv_w), max(1, uv_h)), Image.LANCZOS)
            atlas.alpha_composite(crop, (ux0, uy0))

    output.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output)
    per_line_count = {k: len(v) for k, v in line_carriers.items()}
    return {
        "kept": stats["kept"],
        "cleared": stats["cleared"],
        "per_line_count": per_line_count,
        "font_sizes": font_sizes,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", default="temp/cpk_extract/_US/GUI/opening01.mbs")
    ap.add_argument("--source-atlas", default="C:/game/vita3k/textures/export/79C935AA47DD1810.png")
    ap.add_argument("--output", default="temp/opening_test/atlas.png")
    ap.add_argument("--font", default="fonts/Griun_PolSensibility-Rg.ttf")
    args = ap.parse_args()
    info = build_atlas(Path(args.source_mbs), Path(args.source_atlas),
                       Path(args.font), Path(args.output))
    print(f"kept: {info['kept']}  cleared: {info['cleared']}")
    print(f"per line: {info['per_line_count']}")
    print(f"font sizes: {info['font_sizes']}")


if __name__ == "__main__":
    main()
