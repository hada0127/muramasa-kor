"""Build Korean opening atlas by detecting English word bounding boxes
via connected-component labeling, then drawing a Korean word at each box
with auto-fit font size. Carriers sample the same UV positions as before,
but instead of English glyphs they see Korean words.

MBS is NOT modified. Only the atlas is replaced.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


KOREAN_WORDS = [
    # Line 1
    "헤아릴", "수", "없이", "흩어진", "마검들",
    # Line 2
    "칼집에서", "뽑히는", "순간",
    # Line 3
    "피에", "굶주린", "듯", "곧장", "생명을", "탐한다",
    # Line 4
    "그", "힘에", "스러진", "이들의", "운명을", "보라",
]


def detect_word_boxes(atlas_path: Path) -> tuple[Image.Image, list[tuple[int, int, int, int]]]:
    atlas = Image.open(atlas_path).convert("RGBA")
    arr = np.array(atlas)
    alpha = arr[:, :, 3]
    binary = alpha > 30
    h_struct = np.ones((1, 5), dtype=bool)
    dilated = ndimage.binary_dilation(binary, structure=h_struct, iterations=1)
    labeled, _ = ndimage.label(dilated)
    slices = ndimage.find_objects(labeled)
    words: list[tuple[int, int, int, int]] = []
    for sl in slices:
        if sl is None: continue
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        w, h = x1 - x0, y1 - y0
        if w < 12 or h < 10: continue
        if w > 300 or h > 80: continue
        words.append((x0, y0, x1, y1))
    # Sort by y-row (rough), then x
    words.sort(key=lambda b: (b[1] // 20, b[0]))
    return atlas, words


def fit_text(word: str, max_w: int, max_h: int,
             font_path: Path, start_size: int, min_size: int = 6) -> ImageFont.FreeTypeFont:
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size=size)
        stroke = max(1, size // 16)
        box = font.getbbox(word, stroke_width=stroke)
        w = box[2] - box[0]; h = box[3] - box[1]
        if w <= max_w - 2 and h <= max_h - 2:
            return font
        size -= 1
    return ImageFont.truetype(str(font_path), size=min_size)


def build_atlas(source_atlas: Path, font_path: Path, output: Path,
                preserve_english: bool = False) -> dict:
    atlas, words = detect_word_boxes(source_atlas)
    if preserve_english:
        new_atlas = atlas.copy()
    else:
        new_atlas = Image.new("RGBA", atlas.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(new_atlas)
    for i, (x0, y0, x1, y1) in enumerate(words):
        word = KOREAN_WORDS[i % len(KOREAN_WORDS)]
        w = x1 - x0; h = y1 - y0
        # If not preserving English, clear the box first (transparent)
        if not preserve_english:
            # already transparent; nothing to clear on blank canvas
            pass
        else:
            # Clear original English so Korean is not overlaid on top
            clear = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            new_atlas.paste(clear, (x0, y0))
            draw = ImageDraw.Draw(new_atlas)  # refresh

        font = fit_text(word, w, h, font_path, start_size=h)
        stroke = max(1, font.size // 16)
        box = draw.textbbox((0, 0), word, font=font, stroke_width=stroke)
        tw = box[2] - box[0]; th = box[3] - box[1]
        tx = x0 + (w - tw) // 2 - box[0]
        ty = y0 + (h - th) // 2 - box[1]
        draw.text((tx, ty), word, font=font,
                  fill=(255, 255, 255, 255),
                  stroke_width=stroke, stroke_fill=(255, 255, 255, 255))

    output.parent.mkdir(parents=True, exist_ok=True)
    new_atlas.save(output)
    return {"word_count": len(words), "korean_word_cycle": len(KOREAN_WORDS)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-atlas", default="C:/game/vita3k/textures/export/79C935AA47DD1810.png")
    ap.add_argument("--output", default="temp/opening_test/atlas.png")
    ap.add_argument("--font", default="fonts/Griun_PolSensibility-Rg.ttf")
    ap.add_argument("--preserve-english", action="store_true")
    args = ap.parse_args()
    info = build_atlas(Path(args.source_atlas), Path(args.font),
                       Path(args.output), args.preserve_english)
    print(f"detected words: {info['word_count']}, cycling {info['korean_word_cycle']} Korean words")


if __name__ == "__main__":
    main()
