"""Vita3K 텍스처 전수조사 - 컨택시트 생성기

exported 텍스처 379개를 썸네일 그리드로 배치해서
한눈에 영문 텍스트 포함 텍스처를 식별할 수 있게 함.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

EXPORT_DIR = Path("C:/game/vita3k/textures/export/PCSE00240")
OUTPUT_DIR = Path("output/texture_survey")

THUMB_SIZE = 192
COLS = 8
LABEL_H = 20
CELL_W = THUMB_SIZE
CELL_H = THUMB_SIZE + LABEL_H
MARGIN = 4


def make_contact_sheets():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pngs = sorted(EXPORT_DIR.glob("*.png"))
    print(f"Total textures: {len(pngs)}")

    rows_per_page = 8
    per_page = COLS * rows_per_page
    pages = (len(pngs) + per_page - 1) // per_page

    for page_idx in range(pages):
        start = page_idx * per_page
        end = min(start + per_page, len(pngs))
        batch = pngs[start:end]

        rows = (len(batch) + COLS - 1) // COLS
        img_w = COLS * (CELL_W + MARGIN) + MARGIN
        img_h = rows * (CELL_H + MARGIN) + MARGIN

        sheet = Image.new("RGBA", (img_w, img_h), (32, 32, 32, 255))
        draw = ImageDraw.Draw(sheet)

        for i, png_path in enumerate(batch):
            col = i % COLS
            row = i // COLS
            x = MARGIN + col * (CELL_W + MARGIN)
            y = MARGIN + row * (CELL_H + MARGIN)

            try:
                thumb = Image.open(png_path)
                # maintain aspect ratio
                tw, th = thumb.size
                scale = min(THUMB_SIZE / tw, THUMB_SIZE / th)
                new_w = int(tw * scale)
                new_h = int(th * scale)
                thumb = thumb.resize((new_w, new_h), Image.LANCZOS)

                # center in cell
                paste_x = x + (THUMB_SIZE - new_w) // 2
                paste_y = y + (THUMB_SIZE - new_h) // 2

                # dark bg for thumbnail area
                draw.rectangle([x, y, x + THUMB_SIZE, y + THUMB_SIZE], fill=(0, 0, 0, 255))

                if thumb.mode == "RGBA":
                    sheet.paste(thumb, (paste_x, paste_y), thumb)
                else:
                    sheet.paste(thumb, (paste_x, paste_y))
            except Exception as e:
                draw.rectangle([x, y, x + THUMB_SIZE, y + THUMB_SIZE], fill=(64, 0, 0, 255))
                draw.text((x + 4, y + 80), f"ERR", fill="red")

            # label: first 8 chars of hash
            name = png_path.stem[:16]
            draw.text((x + 2, y + THUMB_SIZE + 2), name, fill=(200, 200, 200, 255))

        out_path = OUTPUT_DIR / f"survey_page_{page_idx:02d}.png"
        sheet.save(str(out_path))
        print(f"Page {page_idx}: {len(batch)} textures -> {out_path}")

    print(f"\nDone: {pages} pages, {len(pngs)} textures total")


if __name__ == "__main__":
    make_contact_sheets()
