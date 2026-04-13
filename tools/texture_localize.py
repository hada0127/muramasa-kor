"""텍스처 한글화 도구

JSON 설정 파일의 텍스트 영역 정의를 읽어서
원본 텍스처 위에 한글 텍스트를 렌더링한다.

사용법:
  python tools/texture_localize.py                    # 전체 빌드
  python tools/texture_localize.py ADE2B8B5998887A9   # 특정 해시만
  python tools/texture_localize.py --preview           # 미리보기 (검은 배경 합성)
"""

import json
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

PROJECT_DIR = Path(__file__).parent.parent
EXPORT_DIR = Path("C:/game/vita3k/textures/export/PCSE00240")
IMPORT_DIR = Path("C:/game/vita3k/textures/import/PCSE00240")
REPO_KR_DIR = PROJECT_DIR / "kr_textures" / "ui"
CONFIG_PATH = PROJECT_DIR / "translations" / "texture_localize_config.json"
PREVIEW_DIR = PROJECT_DIR / "output" / "texture_preview"

DEFAULT_FONT = str(PROJECT_DIR / "fonts" / "Griun_PolSensibility-Rg.ttf")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def render_text_to_image(width, height, text, font_path, font_size,
                         color=(255, 255, 255, 255), align="left",
                         line_spacing=4, bold=False):
    """텍스트를 RGBA 이미지로 렌더링"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)

    lines = text.split("\n")
    y = 0
    for line in lines:
        bbox = font.getbbox(line)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        if align == "center":
            x = (width - text_w) // 2
        elif align == "right":
            x = width - text_w
        else:
            x = 0

        # bold: draw slightly offset copies
        if bold:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    draw.text((x + dx, y + dy), line, font=font, fill=color)
        else:
            draw.text((x, y), line, font=font, fill=color)

        y += text_h + line_spacing

    return img


def process_texture(hash_id, tex_config, preview=False):
    """하나의 텍스처를 처리"""
    # 수동 편집 텍스처는 kr_textures/ui/에 이미 커밋되어 있음 → 덮어쓰기 금지
    if not tex_config.get("regions"):
        print(f"  SKIP {hash_id}: manual edit (no regions) — already in kr_textures/ui/")
        return False

    src_path = EXPORT_DIR / f"{hash_id}.png"
    if not src_path.exists():
        print(f"  SKIP {hash_id}: export 파일 없음")
        return False

    original = Image.open(src_path).convert("RGBA")
    result = original.copy()

    for region in tex_config.get("regions", []):
        x = region["x"]
        y = region["y"]
        w = region["w"]
        h = region["h"]
        text = region["text"]
        font_path = region.get("font", DEFAULT_FONT)
        font_size = region.get("font_size", 24)
        color = tuple(region.get("color", [255, 255, 255, 255]))
        align = region.get("align", "left")
        bold = region.get("bold", False)
        clear = region.get("clear", True)

        # 1. 영역 클리어 (원본 텍스트 제거)
        if clear:
            clear_area = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            # RGB를 원본과 동일하게 유지하되 alpha만 0으로
            orig_region = result.crop((x, y, x + w, y + h))
            orig_arr = np.array(orig_region)
            orig_arr[:, :, 3] = 0  # alpha to 0
            result.paste(Image.fromarray(orig_arr), (x, y))

        # 2. 한글 텍스트 렌더링
        text_img = render_text_to_image(w, h, text, font_path, font_size,
                                         color=color, align=align, bold=bold)

        # 3. 합성
        result.paste(text_img, (x, y), text_img)

    # 출력
    if preview:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        # 검은 배경에 합성해서 보기 쉽게
        bg = Image.new("RGBA", result.size, (0, 0, 0, 255))
        preview_img = Image.alpha_composite(bg, result)
        out_path = PREVIEW_DIR / f"{hash_id}_preview.png"
        preview_img.save(str(out_path))
        print(f"  PREVIEW {hash_id} → {out_path}")
    else:
        IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = IMPORT_DIR / f"{hash_id}.png"
        result.save(str(out_path))
        print(f"  IMPORT {hash_id} → {out_path}")

        # 리포 사본도 저장 (버전 관리·협업용)
        REPO_KR_DIR.mkdir(parents=True, exist_ok=True)
        repo_path = REPO_KR_DIR / f"{hash_id}.png"
        result.save(str(repo_path))
        print(f"  REPO   {hash_id} → {repo_path}")

    return True


def main():
    preview = "--preview" in sys.argv
    target_hash = None
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            target_hash = arg
            break

    config = load_config()

    processed = 0
    skipped = 0
    for tex in config.get("textures", []):
        hash_id = tex["hash"]
        if target_hash and target_hash not in hash_id:
            continue

        status = tex.get("status", "pending")
        if status == "skip":
            continue

        print(f"Processing {hash_id} ({tex.get('description', '')})...")
        if process_texture(hash_id, tex, preview=preview):
            processed += 1
        else:
            skipped += 1

    print(f"\nDone: {processed} processed, {skipped} skipped")


if __name__ == "__main__":
    main()
