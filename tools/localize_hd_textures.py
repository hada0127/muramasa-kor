"""HD 베이스 기반 UI 텍스처 한글화 도구

기존 한글화 좌표 데이터(translations/texture_localize_config.json,
translations/place_texture_jobs.json)를 **그대로 재사용**하되,
저해상도 원본을 LANCZOS로 확대하던 방식 대신 Plaidray HD 텍스처팩의
선명한 UHD 베이스 위에 좌표를 자동 스케일해서 직접 렌더링한다.

배경:
  - 메뉴류(247C/1D67/547/2E)는 256(혹은 1024) 베이스로 렌더 후 4배 확대 → 흐림.
  - 지명류(59015B)는 512x256 베이스로 렌더 후 4배 확대 → 박스/배너 가장자리 깨짐.
  - HD 팩 베이스는 같은 해시에서 원본×4 레이아웃과 정렬됨(검증: alpha IoU 0.83~0.99).
  => HD 베이스에 좌표·폰트크기를 (HD크기/원본크기)배로 스케일해 렌더하면
     위치는 그대로, 화질은 선명해진다.

좌표/폰트 렌더링 로직은 기존 렌더러 함수를 그대로 import 해서 재사용한다
(중복 구현 금지, 단일 좌표 소스 유지).

사용법:
  python tools/localize_hd_textures.py                 # 대상 5개 전부 빌드
  python tools/localize_hd_textures.py 247C            # 해시 prefix 매칭만
  python tools/localize_hd_textures.py --preview        # 검은 배경 합성 미리보기만(설치 안 함)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

import texture_localize as tl
import render_place_texture_job as place

PROJECT_DIR = Path(__file__).resolve().parent.parent
HD_PACK_DIR = Path.home() / "Downloads" / "Muramasa Complete 2.0" / "PCSE00240" / "Best"
REPO_KR_DIR = PROJECT_DIR / "textures/kr" / "ui"
PREVIEW_DIR = PROJECT_DIR / "output" / "texture_preview"
PLACE_ORIG_DIR = PROJECT_DIR / "textures" / "place_originals"
TEXTURE_ORIG_DIR = PROJECT_DIR / "textures" / "originals"

# texture_localize.py 의 import 경로(OS별 자동 해석)를 그대로 사용
IMPORT_DIR = tl.IMPORT_DIR
FONT_PATH = place.DEFAULT_FONT

# 한글화 대상: 메뉴류 4개(config) + 지명류 1개(place job)
MENU_HASHES = [
    "247C255A400261FF",
    "1D6742BBC0DDB7EC",
    "547720A3B20C12AB",
    "2E2003777A770327",
]
PLACE_HASHES = ["59015B61BFC0B7BC"]


def hd_base(hash_id: str) -> Path | None:
    p = HD_PACK_DIR / f"{hash_id}.png"
    return p if p.exists() else None


def ref_size_for_menu(hash_id: str, tex_cfg: dict) -> int:
    """이 텍스처 region 좌표가 작성된 좌표계의 한 변 크기."""
    src = tex_cfg.get("source")
    ref = (PROJECT_DIR / src) if src else (TEXTURE_ORIG_DIR / f"{hash_id}.png")
    if not ref.exists():
        ref = tl.EXPORT_DIR / f"{hash_id}.png"
    return Image.open(ref).convert("RGBA").width


def scale_region(region: dict, s: float) -> dict:
    """region 좌표/폰트/clear_rect 를 s배로 스케일한 새 dict 반환."""
    r = dict(region)
    for k in ("x", "y", "w", "h"):
        if k in r:
            r[k] = int(round(r[k] * s))
    if "font_size" in r:
        r["font_size"] = max(8, int(round(r["font_size"] * s)))
    if "nudge_x" in r:
        r["nudge_x"] = int(round(r["nudge_x"] * s))
    if "nudge_y" in r:
        r["nudge_y"] = int(round(r["nudge_y"] * s))
    cr = r.get("clear_rect")
    if cr:
        r["clear_rect"] = {k: int(round(v * s)) for k, v in cr.items()}
    return r


def save_result(result: Image.Image, hash_id: str, preview: bool) -> None:
    if preview:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        bg = Image.new("RGBA", result.size, (0, 0, 0, 255))
        out = PREVIEW_DIR / f"{hash_id}_hd_preview.png"
        Image.alpha_composite(bg, result).save(str(out))
        print(f"  PREVIEW → {out}")
        return
    REPO_KR_DIR.mkdir(parents=True, exist_ok=True)
    repo_path = REPO_KR_DIR / f"{hash_id}.png"
    result.save(str(repo_path))
    print(f"  REPO   → {repo_path}")
    if IMPORT_DIR.parent.exists():
        IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        imp = IMPORT_DIR / f"{hash_id}.png"
        result.save(str(imp))
        print(f"  IMPORT → {imp}")


def build_menu(hash_id: str, tex_cfg: dict, preview: bool) -> bool:
    base = hd_base(hash_id)
    if base is None:
        print(f"  SKIP {hash_id}: HD 팩 베이스 없음 ({HD_PACK_DIR / (hash_id + '.png')})")
        return False
    original = Image.open(base).convert("RGBA")
    ref = ref_size_for_menu(hash_id, tex_cfg)
    s = original.width / ref
    print(f"  base={original.size} ref={ref} scale={s:g}")

    regions = [scale_region(r, s) for r in tex_cfg.get("regions", [])]
    auto_align = bool(tex_cfg.get("auto_align", False)) and tl._scipy_label is not None

    if auto_align:
        orig_arr = np.array(original)
        sprite_mask = tl.compute_sprite_mask(orig_arr[..., 3])
        result_arr = orig_arr.copy()
        for region in regions:
            tl._process_region_auto(region, orig_arr, sprite_mask, result_arr)
        result = Image.fromarray(result_arr)
    else:
        result = original.copy()
        for region in regions:
            x, y, w, h = region["x"], region["y"], region["w"], region["h"]
            if region.get("clear", True):
                cr = region.get("clear_rect")
                cx, cy, cw, ch = (cr["x"], cr["y"], cr["w"], cr["h"]) if cr else (x, y, w, h)
                crop = np.array(result.crop((cx, cy, cx + cw, cy + ch)))
                crop[:, :, 3] = 0
                result.paste(Image.fromarray(crop), (cx, cy))
            text_img = tl.render_text_to_image(
                w, h, region["text"], region.get("font", FONT_PATH),
                region.get("font_size", 24),
                color=tuple(region.get("color", [255, 255, 255, 255])),
                align=region.get("align", "left"),
                bold=region.get("bold", False),
                v_align=region.get("v_align", "top"),
                fit_to_box=bool(region.get("fit_to_box", False)),
            )
            result.paste(text_img, (x, y), text_img)

    save_result(result, hash_id, preview)
    return True


def build_place(hash_id: str, job: dict, preview: bool) -> bool:
    base = hd_base(hash_id)
    if base is None:
        print(f"  SKIP {hash_id}: HD 팩 베이스 없음 ({HD_PACK_DIR / (hash_id + '.png')})")
        return False
    img = Image.open(base).convert("RGBA")
    src = place.repo_path(job.get("source"), PLACE_ORIG_DIR / f"{hash_id}.png")
    ref_w = Image.open(src).convert("RGBA").width
    s = img.width / ref_w
    print(f"  base={img.size} ref={ref_w} scale={s:g}")

    font_path = Path(FONT_PATH)
    for region in job.get("regions", []):
        if not region.get("render", True):
            continue
        bbox = [int(round(v * s)) for v in region["bbox"]]
        background = region.get("background")
        if background in place.BACKGROUND_COLORS:
            if region.get("background_mode") == "fill":
                img = place.fill_region(img, bbox, place.BACKGROUND_COLORS[background])
            else:
                img = place.clear_region(img, bbox, place.BACKGROUND_COLORS[background])
        elif region.get("clear") == "white":
            img = place.kill_white_in_bbox(img, bbox)
        elif region.get("clear") == "alpha":
            img = place.clear_alpha_in_bbox(img, bbox)

        text = region.get("ko", "")
        if text:
            text_color = place.TEXT_COLORS[region.get("text_color", "black")]
            # font_ratio 기반이라 폰트는 bbox로부터 자동 스케일됨
            place.render_text(
                img, bbox, text, text_color, font_path,
                padding=float(region.get("padding", 0.08)),
                fr=float(region.get("font_ratio", 0.85)),
                layout=region.get("layout"),
            )

    save_result(img, hash_id, preview)
    return True


def main() -> None:
    preview = "--preview" in sys.argv
    target = None
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            target = arg.upper()
            break

    config = tl.load_config()
    menu_cfg = {t["hash"]: t for t in config.get("textures", [])}
    place_jobs = json.loads((PROJECT_DIR / "translations" / "place_texture_jobs.json").read_text(encoding="utf-8"))
    place_cfg = place_jobs.get("textures", place_jobs)

    done = 0
    for h in MENU_HASHES:
        if target and target not in h:
            continue
        if h not in menu_cfg:
            print(f"  WARN {h}: config 없음")
            continue
        print(f"[{h}] {menu_cfg[h].get('description', '')[:48]}")
        if build_menu(h, menu_cfg[h], preview):
            done += 1

    for h in PLACE_HASHES:
        if target and target not in h:
            continue
        job = place_cfg.get(h) if isinstance(place_cfg, dict) else None
        if job is None:
            print(f"  WARN {h}: place job 없음")
            continue
        print(f"[{h}] 지명 텍스처")
        if build_place(h, job, preview):
            done += 1

    print(f"\nDone: {done} processed")


if __name__ == "__main__":
    main()
