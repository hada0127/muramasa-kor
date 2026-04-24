"""Build Korean opening atlas by classifying carriers by color:
- MAIN (0xFFFFFFFF, white): Korean text is drawn at its atlas UV rect.
- SHADOW (0xFF402000, dark brown): UV rect is cleared (transparent).
- RED (0xFF0000FF, word highlight): UV rect is cleared.
- LARGE overlap carriers (90, 96, 111, 114): UV rect cleared (underlay).

For each MAIN carrier, we try a full Korean sentence first, then phrase,
then single word, fitting into its UV rect. MBS is NOT modified.
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

MAIN_COLOR = 0xFFFFFFFF
SHADOW_COLOR = 0xFF402000
RED_COLOR = 0xFF0000FF
LARGE_CONTAINER_CARRIERS = {90, 96, 111, 114}

KOREAN_SENTENCES = [
    "헤아릴 수 없이 흩어진 마검들.",
    "칼집에서 뽑히는 순간,",
    "피에 굶주린 듯 곧장 생명을 탐한다.",
    "그 힘에 스러진 이들의 운명을 보라.",
]
KOREAN_PHRASES = [
    "헤아릴 수 없이", "흩어진 마검들",
    "칼집에서", "뽑히는 순간,",
    "피에 굶주린", "생명을 탐한다",
    "그 힘에", "스러진 이들의 운명",
]
KOREAN_WORDS = [
    "헤아릴", "마검들", "칼집", "순간",
    "피에", "굶주린", "탐한다", "운명",
    "스러진", "힘에", "보라", "생명",
]

MIN_SENTENCE_SIZE = 14
MIN_PHRASE_SIZE = 16
MIN_WORD_SIZE = 13


def quad_offset(idx: int) -> int:
    return MBS_TABLE_OFFSET + idx * QUAD_SIZE


def read_quad(src: bytes, idx: int):
    base = quad_offset(idx)
    return [struct.unpack_from("<Iffff", src, base + i * VERTEX_SIZE) for i in range(4)]


def uv_rect(vs) -> tuple[int, int, int, int]:
    xs = [v[1] for v in vs]
    ys = [v[2] for v in vs]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def screen_info(vs) -> tuple[float, float, float, float, float]:
    sxs = [v[3] + 480.0 for v in vs]
    sys_ = [272.0 - v[4] for v in vs]
    sx0, sx1 = min(sxs), max(sxs)
    sy0, sy1 = min(sys_), max(sys_)
    cy = (sy0 + sy1) / 2.0
    return sx0, sy0, sx1, sy1, cy


def fit_text(text: str, max_w: int, max_h: int, font_path: Path,
             start_size: int, min_size: int) -> ImageFont.FreeTypeFont | None:
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(str(font_path), size=size)
        stroke = max(1, size // 16)
        box = font.getbbox(text, stroke_width=stroke)
        w = box[2] - box[0]; h = box[3] - box[1]
        if w <= max_w - 2 and h <= max_h - 2:
            return font
        size -= 1
    return None


def assign_line(cy: float) -> int:
    if cy < 220: return 0
    if cy < 300: return 1
    if cy < 370: return 2
    return 3


def build_atlas(source_mbs: Path, source_atlas: Path, font_path: Path,
                output: Path) -> dict:
    src = source_mbs.read_bytes()
    atlas = Image.open(source_atlas).convert("RGBA")
    arr = np.array(atlas)
    # Snapshot of the ORIGINAL alpha, so coverage checks are not disturbed by
    # clears of overlapping carriers processed earlier in the loop.
    original_alpha = arr[:, :, 3].copy()

    main_per_line: dict[int, list] = {0: [], 1: [], 2: [], 3: []}
    stats = {"kept": 0, "cleared": 0}

    for idx in range(40, 116):
        vs = read_quad(src, idx)
        color = vs[0][0]
        ux0, uy0, ux1, uy1 = uv_rect(vs)
        if ux0 < 0 or uy0 < 0 or ux1 > 512 or uy1 > 512:
            continue
        if ux0 == ux1 or uy0 == uy1:
            continue

        def clear():
            arr[uy0:uy1, ux0:ux1, 3] = 0
            stats["cleared"] += 1

        if idx in LARGE_CONTAINER_CARRIERS:
            clear(); continue
        if color in (SHADOW_COLOR, RED_COLOR):
            clear(); continue
        if color != MAIN_COLOR:
            continue

        sx0, sy0, sx1, sy1, cy = screen_info(vs)
        on_screen = 0 <= sx0 and sx1 <= 960 and 0 <= sy0 and sy1 <= 544
        in_narration_y = 160 <= sy0 and sy1 <= 420
        if not (on_screen and in_narration_y):
            clear(); continue

        region = original_alpha[uy0:uy1, ux0:ux1]
        coverage = float(np.mean(region > 30)) if region.size else 0.0
        if coverage < 0.15:
            clear(); continue

        line = assign_line(cy)
        sc_w = sx1 - sx0
        sc_h = sy1 - sy0
        uv_w = ux1 - ux0
        uv_h = uy1 - uy0
        # Penalize aspect mismatch: carriers whose UV rect aspect differs
        # wildly from screen rect aspect compress the sentence into a stripe.
        sc_aspect = sc_w / max(sc_h, 1)
        uv_aspect = uv_w / max(uv_h, 1)
        aspect_ratio = max(sc_aspect, uv_aspect) / max(min(sc_aspect, uv_aspect), 0.001)
        score = sc_w / aspect_ratio
        main_per_line[line].append((score, sc_w, idx, cy, (ux0, uy0, ux1, uy1)))
        stats["kept"] += 1

    # Per line, keep the carrier with the HIGHEST score (screen width
    # divided by aspect mismatch). Clear the rest.
    for line in main_per_line.values():
        if not line: continue
        line.sort(key=lambda t: -t[0])       # highest score first
        for _, _, _, _, (ux0, uy0, ux1, uy1) in line[1:]:
            arr[uy0:uy1, ux0:ux1, 3] = 0
        line[:] = [line[0]]

    # Clear kept carriers' UV regions too (redraw Korean)
    for line_entries in main_per_line.values():
        for _, _, _, _, (ux0, uy0, ux1, uy1) in line_entries:
            arr[uy0:uy1, ux0:ux1, 3] = 0

    atlas = Image.fromarray(arr, mode="RGBA")
    draw = ImageDraw.Draw(atlas)

    tier_counts = {"sentence": 0, "phrase": 0, "word": 0, "skipped": 0}

    for line_idx in sorted(main_per_line):
        carriers = main_per_line[line_idx]
        sentence_text = KOREAN_SENTENCES[line_idx]
        # Seq of phrase/word options for this line
        phrases_for_line = [KOREAN_PHRASES[line_idx * 2], KOREAN_PHRASES[line_idx * 2 + 1]]
        words_for_line = [KOREAN_WORDS[line_idx * 3 + k % 3] for k in range(len(carriers))]

        for seq, (score, sc_w, idx, cy, (ux0, uy0, ux1, uy1)) in enumerate(carriers):
            w = ux1 - ux0; h = uy1 - uy0

            # Widest gets sentence; others get phrase or word
            if seq == 0:
                font = fit_text(sentence_text, w, h, font_path, start_size=h, min_size=MIN_SENTENCE_SIZE)
                if font is not None:
                    text = sentence_text; tier = "sentence"
                else:
                    # fall back to phrase then word
                    phrase = phrases_for_line[0]
                    font = fit_text(phrase, w, h, font_path, start_size=h, min_size=MIN_PHRASE_SIZE)
                    if font: text, tier = phrase, "phrase"
                    else:
                        wtext = words_for_line[seq]
                        font = fit_text(wtext, w, h, font_path, start_size=h, min_size=MIN_WORD_SIZE)
                        if font: text, tier = wtext, "word"
                        else:
                            tier_counts["skipped"] += 1
                            continue
            else:
                phrase = phrases_for_line[min(seq - 1, 1)]
                font = fit_text(phrase, w, h, font_path, start_size=h, min_size=MIN_PHRASE_SIZE)
                if font: text, tier = phrase, "phrase"
                else:
                    wtext = words_for_line[seq]
                    font = fit_text(wtext, w, h, font_path, start_size=h, min_size=MIN_WORD_SIZE)
                    if font: text, tier = wtext, "word"
                    else:
                        tier_counts["skipped"] += 1
                        continue

            tier_counts[tier] += 1
            stroke = max(1, font.size // 16)
            tbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
            tw = tbox[2] - tbox[0]; th = tbox[3] - tbox[1]
            tx = ux0 + (w - tw) // 2 - tbox[0]
            ty = uy0 + (h - th) // 2 - tbox[1]
            draw.text((tx, ty), text, font=font,
                      fill=(255, 255, 255, 255),
                      stroke_width=stroke, stroke_fill=(255, 255, 255, 255))

    output.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output)
    counts = {k: len(v) for k, v in main_per_line.items()}
    return {"kept": stats["kept"], "cleared": stats["cleared"],
            "per_line": counts, "tiers": tier_counts}


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
    print(f"per line: {info['per_line']}")
    print(f"tiers: {info['tiers']}")


if __name__ == "__main__":
    main()
