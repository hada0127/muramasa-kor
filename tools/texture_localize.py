"""텍스처 한글화 도구

JSON 설정 파일의 텍스트 영역 정의를 읽어서
원본 텍스처 위에 한글 텍스트를 렌더링한다.

기본 모드: region 좌표에 직접 한글 렌더 (regions 좌표 = 한글 배치 박스).
auto_align 모드(텍스처 레벨 "auto_align": true): clear_rect 안의 영문 alpha
bbox를 자동 측정해서 한글 alpha bbox를 거기에 정확히 정렬하고, sprite-mask
픽셀(가로 띠 같은 UI 그래픽)은 보존한 채로 영문만 지운다.

사용법:
  python tools/texture_localize.py                    # 전체 빌드
  python tools/texture_localize.py ADE2B8B5998887A9   # 특정 해시만
  python tools/texture_localize.py --preview           # 미리보기 (검은 배경 합성)
"""

import json
import sys
import os
import platform
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

try:
    from scipy.ndimage import label as _scipy_label
except ImportError:
    _scipy_label = None

PROJECT_DIR = Path(__file__).parent.parent

# Vita3K 텍스처 폴더 (OS별 기본 경로)
if platform.system() == "Darwin":
    _VITA3K_BASE = Path.home() / "Library/Application Support/Vita3K/Vita3K/textures"
elif platform.system() == "Linux":
    _VITA3K_BASE = Path.home() / ".local/share/Vita3K/Vita3K/textures"
else:
    _VITA3K_BASE = Path("C:/game/vita3k/textures")

EXPORT_DIR = Path(os.environ.get("VITA3K_EXPORT_DIR", _VITA3K_BASE / "export" / "PCSE00240"))
IMPORT_DIR = Path(os.environ.get("VITA3K_IMPORT_DIR", _VITA3K_BASE / "import" / "PCSE00240"))
REPO_KR_DIR = PROJECT_DIR / "kr_textures" / "ui"
CONFIG_PATH = PROJECT_DIR / "translations" / "texture_localize_config.json"
PREVIEW_DIR = PROJECT_DIR / "output" / "texture_preview"

DEFAULT_FONT = str(PROJECT_DIR / "fonts" / "Griun_PolSensibility-Rg.ttf")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _spaced_width(font, line, ls):
    """자간(ls) 포함 라인 폭."""
    if not line:
        return 0
    return sum(font.getlength(ch) for ch in line) + ls * (len(line) - 1)


def _draw_spaced(draw, x, y, line, font, fill, ls, bold=False):
    """글자별로 자간(ls)을 두며 그린다."""
    cx = x
    for ch in line:
        if bold:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    draw.text((cx + dx, y + dy), ch, font=font, fill=fill)
        else:
            draw.text((cx, y), ch, font=font, fill=fill)
        cx += font.getlength(ch) + ls


def render_text_to_image(width, height, text, font_path, font_size,
                         color=(255, 255, 255, 255), align="left",
                         line_spacing=4, bold=False, v_align="top",
                         fit_to_box=False, letter_spacing=0,
                         outline_width=0, outline_color=(0, 0, 0, 255)):
    """텍스트를 RGBA 이미지로 렌더링"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    ls = letter_spacing

    if fit_to_box:
        while font_size > 8:
            font = ImageFont.truetype(font_path, font_size)
            lines = text.split("\n")
            widths = []
            total_h = 0
            for i, line in enumerate(lines):
                bbox = font.getbbox(line)
                widths.append(_spaced_width(font, line, ls) if ls else bbox[2] - bbox[0])
                total_h += bbox[3] - bbox[1]
                if i < len(lines) - 1:
                    total_h += line_spacing
            if (not widths or max(widths) <= width) and total_h <= height:
                break
            font_size -= 1

    font = ImageFont.truetype(font_path, font_size)

    lines = text.split("\n")
    line_metrics = []
    total_h = 0
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        text_w = _spaced_width(font, line, ls) if ls else bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        line_metrics.append((bbox, text_w, text_h))
        total_h += text_h
        if i < len(lines) - 1:
            total_h += line_spacing

    if v_align == "center":
        y = max(0, (height - total_h) // 2)
    elif v_align == "bottom":
        y = max(0, height - total_h)
    else:
        y = 0

    for line, (bbox, text_w, text_h) in zip(lines, line_metrics):
        if align == "center":
            x = (width - text_w) // 2 - bbox[0]
        elif align == "right":
            x = width - text_w - bbox[0]
        else:
            x = -bbox[0]
        draw_y = y - bbox[1]

        sw = max(0, int(outline_width or 0))
        sfill = tuple(outline_color) if sw else None
        if ls:
            _draw_spaced(draw, x, draw_y, line, font, color, ls, bold=bold)
            # 자간 모드는 stroke 별도 처리 필요 — 글자별 stroke
            if sw:
                cx = x
                for ch in line:
                    draw.text((cx, draw_y), ch, font=font, fill=color,
                              stroke_width=sw, stroke_fill=sfill)
                    cx += font.getlength(ch) + ls
        elif bold:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    draw.text((x + dx, draw_y + dy), line, font=font, fill=color)
        elif sw:
            draw.text((x, draw_y), line, font=font, fill=color,
                      stroke_width=sw, stroke_fill=sfill)
        else:
            draw.text((x, draw_y), line, font=font, fill=color)

        y += text_h + line_spacing

    return img


def compute_sprite_mask(alpha_arr, min_area=400, min_dim=30, min_aspect=3.0,
                        alpha_thr=100):
    """큰 sprite (가로 띠, 원형 등) 영역을 자동 식별하는 boolean 마스크 반환.
    - aspect ratio (긴 변/짧은 변) >= min_aspect AND 긴 변 >= min_dim → 가로/세로 sprite
    - 또는 area >= min_area → 큰 원형/덩어리 sprite
    영문 글자(작은 stroke)는 제외됨.
    scipy가 없으면 None 반환 (auto_align 비활성).
    """
    if _scipy_label is None:
        return None
    labels, n = _scipy_label(alpha_arr > alpha_thr)
    mask = np.zeros_like(alpha_arr, dtype=bool)
    for i in range(1, n + 1):
        region = labels == i
        area = int(region.sum())
        ys, xs = np.where(region)
        w = int(xs.max() - xs.min() + 1)
        h = int(ys.max() - ys.min() + 1)
        aspect = max(w / h, h / w) if h and w else 0
        if (aspect >= min_aspect and max(w, h) >= min_dim) or area >= min_area:
            mask |= region
    return mask


def _alpha_bbox(arr_alpha, thr=32):
    ys, xs = np.where(arr_alpha > thr)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def _process_region_auto(region, orig_arr, sprite_mask, result_arr):
    """auto_align 모드 region 처리.
    1. clear_rect 안의 영문 alpha bbox 측정 (sprite 제외)
    2. 한글 렌더 후 alpha bbox 측정
    3. align/v_align/nudge에 따라 한글 alpha bbox를 영문 alpha bbox에 정렬
    4. clear 시 sprite 마스크 픽셀은 보존
    """
    cr = region.get("clear_rect") or {
        "x": region["x"], "y": region["y"],
        "w": region["w"], "h": region["h"],
    }
    cx, cy, cw, ch = cr["x"], cr["y"], cr["w"], cr["h"]

    # 영문 alpha bbox (sprite 픽셀 제외)
    sub = orig_arr[cy:cy + ch, cx:cx + cw, 3].copy()
    sub[sprite_mask[cy:cy + ch, cx:cx + cw]] = 0
    bb = _alpha_bbox(sub)
    if bb is None:
        return False
    en_bb = (bb[0] + cx, bb[1] + cy, bb[2] + cx, bb[3] + cy)
    en_w = en_bb[2] - en_bb[0] + 1
    en_h = en_bb[3] - en_bb[1] + 1

    text = region["text"]
    font_path = region.get("font", DEFAULT_FONT)
    font_size = region.get("font_size", 24)
    color = tuple(region.get("color", [255, 255, 255, 255]))
    align = region.get("align", "left")
    v_align = region.get("v_align", "center")
    nudge_x = int(region.get("nudge_x", 0))
    nudge_y = int(region.get("nudge_y", 0))
    bold = region.get("bold", False)
    ls = int(region.get("letter_spacing", 0))

    # 한글을 큰 캔버스에 렌더 후 alpha bbox 측정
    big = Image.new("RGBA", (400, 200), (0, 0, 0, 0))
    big_draw = ImageDraw.Draw(big)
    font = ImageFont.truetype(font_path, font_size)
    if ls:
        _draw_spaced(big_draw, 50, 50, text, font, color, ls, bold=bold)
    elif bold:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                big_draw.text((50 + dx, 50 + dy), text, font=font, fill=color)
    else:
        big_draw.text((50, 50), text, font=font, fill=color)
    big_arr = np.array(big)
    kr_bb = _alpha_bbox(big_arr[..., 3])
    if kr_bb is None:
        return False
    kx0, ky0, kx1, ky1 = kr_bb
    kr_w = kx1 - kx0 + 1
    kr_h = ky1 - ky0 + 1
    kr_crop = big.crop((kx0, ky0, kx1 + 1, ky1 + 1))

    if align == "left":
        px = en_bb[0]
    elif align == "right":
        px = en_bb[2] - kr_w + 1
    else:
        px = en_bb[0] + (en_w - kr_w) // 2
    if v_align == "top":
        py = en_bb[1]
    elif v_align == "bottom":
        py = en_bb[3] - kr_h + 1
    else:
        py = en_bb[1] + (en_h - kr_h) // 2

    px += nudge_x
    py += nudge_y

    # 영문 alpha bbox 영역만 clear (sprite 보존)
    eb_y0, eb_x0 = en_bb[1], en_bb[0]
    eb_y1, eb_x1 = en_bb[3] + 1, en_bb[2] + 1
    zone_sprite = sprite_mask[eb_y0:eb_y1, eb_x0:eb_x1]
    crop = result_arr[eb_y0:eb_y1, eb_x0:eb_x1].copy()
    crop[..., 3] = np.where(~zone_sprite, 0, crop[..., 3])
    result_arr[eb_y0:eb_y1, eb_x0:eb_x1] = crop

    # 한글 paste (alpha max로 sprite 영역과 안전하게 합성)
    kr_arr = np.array(kr_crop)
    H, W = result_arr.shape[:2]
    h_k, w_k = kr_arr.shape[:2]
    for ky in range(h_k):
        for kx in range(w_k):
            ta = int(kr_arr[ky, kx, 3])
            if ta == 0:
                continue
            ty, tx = py + ky, px + kx
            if 0 <= ty < H and 0 <= tx < W:
                cur = int(result_arr[ty, tx, 3])
                result_arr[ty, tx, 3] = max(cur, ta)
                if ta > 128:
                    result_arr[ty, tx, :3] = 255
    return True


def process_texture(hash_id, tex_config, preview=False):
    """하나의 텍스처를 처리"""
    # 수동 편집 텍스처는 kr_textures/ui/에 이미 커밋되어 있음 → 덮어쓰기 금지
    if not tex_config.get("regions"):
        print(f"  SKIP {hash_id}: manual edit (no regions) — already in kr_textures/ui/")
        return False

    source = tex_config.get("source")
    src_path = PROJECT_DIR / source if source else EXPORT_DIR / f"{hash_id}.png"
    if not src_path.exists():
        print(f"  SKIP {hash_id}: export 파일 없음 ({src_path})")
        return False

    original = Image.open(src_path).convert("RGBA")
    result = original.copy()

    auto_align = bool(tex_config.get("auto_align", False))
    if auto_align:
        if _scipy_label is None:
            print(f"  WARN {hash_id}: auto_align=true이지만 scipy 미설치 → 기본 모드로 fallback")
            auto_align = False

    if auto_align:
        orig_arr = np.array(original)
        sprite_mask = compute_sprite_mask(orig_arr[..., 3])
        result_arr = orig_arr.copy()
        for region in tex_config.get("regions", []):
            _process_region_auto(region, orig_arr, sprite_mask, result_arr)
        result = Image.fromarray(result_arr)
    else:
        for region in tex_config.get("regions", []):
            x = region["x"]
            y = region["y"]
            w = region["w"]
            h = region["h"]
            text = region["text"]
            font_path = region.get("font", DEFAULT_FONT)
            # font_size 가 명시되어 있으면 절대값. 없거나 0이면 font_ratio 기반 자동 계산.
            font_size_raw = region.get("font_size")
            font_ratio = float(region.get("font_ratio") or 0)
            if font_size_raw and int(font_size_raw) > 0:
                font_size = int(font_size_raw)
            elif font_ratio > 0:
                # 가로/세로 박스 짧은 변 × ratio
                font_size = max(8, int(min(w, h) * font_ratio))
            else:
                font_size = 24  # legacy default
            color = tuple(region.get("color", [255, 255, 255, 255]))
            align = region.get("align", "left")
            v_align = region.get("v_align", "top")
            bold = region.get("bold", False)
            clear = region.get("clear", True)

            # 1. 영역 클리어 (원본 텍스트 제거)
            if clear:
                clear_rect = region.get("clear_rect")
                if clear_rect:
                    cx = clear_rect["x"]
                    cy = clear_rect["y"]
                    cw = clear_rect["w"]
                    ch = clear_rect["h"]
                else:
                    cx, cy, cw, ch = x, y, w, h
                # RGB를 원본과 동일하게 유지하되 alpha만 0으로
                orig_region = result.crop((cx, cy, cx + cw, cy + ch))
                orig_arr = np.array(orig_region)
                orig_arr[:, :, 3] = 0  # alpha to 0
                result.paste(Image.fromarray(orig_arr), (cx, cy))

            # 2. 한글 텍스트 렌더링 — layout 이 rotated/vertical 이면 place 의 render_text 위임
            layout = region.get("layout")
            rotation = int(region.get("rotation") or 0)
            if layout in ("rotated", "vertical", "vertical_columns") or rotation != 0:
                import render_place_texture_job as PJ
                # localize 의 align→place 의 align/valign 매핑
                v_to_valign = {"top":"top","center":"center","bottom":"bottom"}
                PJ.render_text(
                    result,
                    [x, y, x+w, y+h],
                    text,
                    color,
                    Path(font_path),
                    padding=0.0,
                    fr=float(region.get("font_ratio") or 0.85),
                    layout=layout,
                    letter_spacing=int(region.get("letter_spacing") or 0),
                    align=align if align in ("left","center","right") else "center",
                    valign=v_to_valign.get(v_align, "center"),
                    font_px=font_size if region.get("font_size") else None,
                    rotation=rotation,
                    outline_width=int(region.get("outline_width", 0) or 0),
                    outline_fill=tuple(region.get("outline_color") or (0,0,0,255)) if region.get("outline_width") else None,
                )
            else:
                text_img = render_text_to_image(
                    w, h, text, font_path, font_size,
                    color=color, align=align, bold=bold, v_align=v_align,
                    fit_to_box=bool(region.get("fit_to_box", False)),
                    letter_spacing=int(region.get("letter_spacing") or 0),
                    outline_width=int(region.get("outline_width", 0) or 0),
                    outline_color=tuple(region.get("outline_color") or (0, 0, 0, 255)),
                )
                # 3. 합성
                result.paste(text_img, (x, y), text_img)

    output_scale = int(tex_config.get("output_scale", 1))
    if output_scale > 1:
        result = result.resize(
            (result.width * output_scale, result.height * output_scale),
            Image.Resampling.LANCZOS,
        )
    # 출력 크기는 항상 source(UHD originals)와 동일해야 함 (정책).
    # output_size를 명시한 경우에만 그쪽으로 resize. size 메타데이터는 무시.
    target = tex_config.get("output_size")
    if target and (result.width, result.height) != tuple(target):
        result = result.resize(tuple(target), Image.Resampling.LANCZOS)

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
