"""UI 텍스처 편집 도구용 통합 인덱스 JSON 생성기.

기존 두 렌더 시스템(texture_localize_config.json, place_texture_jobs.json)과
수동 편집 파일을 한데 모아 kr_textures/ui 전체 목록을 만든다.
편집 웹도구(tools/ui_editor)가 이 인덱스를 읽고, 저장 시 다시 네이티브
config에 역기록한다.

- 각 항목: hash, png, source(원본), size, system, description, memo, regions
- regions 에는 canvas 편집용 box[x,y,w,h] 와 네이티브 필드를 함께 담는다.
- memo 는 인덱스에만 존재하며, 재생성 시 기존 인덱스의 memo 를 보존한다.

사용법:
  python tools/build_ui_index.py            # 인덱스 (재)생성
"""
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
KR_DIR = ROOT / "kr_textures" / "ui"
LOCALIZE_CONFIG = ROOT / "translations" / "texture_localize_config.json"
PLACE_JOBS = ROOT / "translations" / "place_texture_jobs.json"
INDEX_PATH = ROOT / "translations" / "ui_editor_index.json"


def _img_size(path: Path):
    try:
        with Image.open(path) as im:
            return [im.width, im.height]
    except Exception:
        return None


def _resolve_source(value, hash_id):
    """source 경로(레포 상대) → 존재하면 상대경로 문자열, 없으면 None."""
    candidates = []
    if value:
        candidates.append(ROOT / value)
    candidates += [
        ROOT / "textures" / "originals" / f"{hash_id}.png",
        ROOT / "textures" / "place_name_originals" / f"{hash_id}.png",
    ]
    for c in candidates:
        if c.exists():
            return str(c.relative_to(ROOT))
    return None


def localize_regions(tex):
    """texture_localize 스키마 region → 통합 region (box + native)."""
    out = []
    for r in tex.get("regions", []):
        box = [r.get("x", 0), r.get("y", 0), r.get("w", 0), r.get("h", 0)]
        out.append({
            "box": box,
            "text": r.get("text", ""),
            "font_size": r.get("font_size", 24),
            "color": r.get("color", [255, 255, 255, 255]),
            "align": r.get("align", "left"),
            "v_align": r.get("v_align", "top"),
            "clear": r.get("clear", True),
            "fit_to_box": r.get("fit_to_box", False),
            "orient": r.get("orient"),
            "native": r,
        })
    return out


def _place_bg_enum(r):
    """네이티브 place region 의 배경/클리어 모드를 단일 enum 으로 정규화."""
    bg = r.get("background")
    if bg in ("red", "black"):
        return bg
    clear = r.get("clear")
    if clear == "alpha":
        return "clear_alpha"
    if clear == "white":
        return "clear_white"
    return "transparent"


def place_regions(job):
    """place_texture_jobs 스키마 region → 통합 region (box + native)."""
    out = []
    for r in job.get("regions", []):
        x0, y0, x1, y1 = r.get("bbox", [0, 0, 0, 0])
        box = [x0, y0, x1 - x0, y1 - y0]
        out.append({
            "box": box,
            "id": r.get("id"),
            "ja": r.get("ja", ""),
            "text": r.get("ko", ""),
            "background": _place_bg_enum(r),
            "text_color": r.get("text_color", "black"),
            "layout": r.get("layout"),
            "padding": r.get("padding", 0.08),
            "font_ratio": r.get("font_ratio", 0.85),
            "render": r.get("render", True),
            "native": r,
        })
    return out


def build():
    # 기존 memo 보존
    existing_memo = {}
    if INDEX_PATH.exists():
        old = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        for t in old.get("textures", []):
            if t.get("memo"):
                existing_memo[t["hash"]] = t["memo"]

    localize = json.loads(LOCALIZE_CONFIG.read_text(encoding="utf-8"))
    place = json.loads(PLACE_JOBS.read_text(encoding="utf-8"))

    loc_by_hash = {t["hash"]: t for t in localize.get("textures", [])}
    place_by_hash = place.get("textures", {})

    kr_hashes = sorted(p.stem for p in KR_DIR.glob("*.png"))

    entries = []
    for h in kr_hashes:
        png_rel = str((KR_DIR / f"{h}.png").relative_to(ROOT))
        size = _img_size(KR_DIR / f"{h}.png")

        if h in loc_by_hash:
            tex = loc_by_hash[h]
            entry = {
                "hash": h,
                "system": "localize",
                "png": png_rel,
                "source": _resolve_source(tex.get("source"), h),
                "size": size,
                "description": tex.get("description", ""),
                "output_scale": tex.get("output_scale", 1),
                "auto_align": tex.get("auto_align", False),
                "regions": localize_regions(tex),
            }
        elif h in place_by_hash:
            job = place_by_hash[h]
            entry = {
                "hash": h,
                "system": "place",
                "png": png_rel,
                "source": _resolve_source(job.get("source"), h),
                "size": size,
                "description": job.get("description", ""),
                "status": job.get("status", ""),
                "output_scale": job.get("output_scale", 1),
                "regions": place_regions(job),
            }
        else:
            entry = {
                "hash": h,
                "system": "manual",
                "png": png_rel,
                "source": _resolve_source(None, h),
                "size": size,
                "description": "수동 편집 텍스처 (생성 스크립트 미정의)",
                "regions": [],
            }

        entry["memo"] = existing_memo.get(h, "")
        entries.append(entry)

    index = {
        "_description": "UI 텍스처 편집 도구용 통합 인덱스. build_ui_index.py가 생성.",
        "_note": "memo는 이 파일에만 존재하며 재생성 시 보존됨. regions는 네이티브 config의 미러.",
        "_systems": {
            "localize": "texture_localize_config.json + texture_localize.py",
            "place": "place_texture_jobs.json + render_place_texture_job.py",
            "manual": "kr_textures/ui에 직접 편집된 파일 (자동 생성 없음)",
        },
        "count": len(entries),
        "textures": entries,
    }
    INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    by_sys = {}
    for e in entries:
        by_sys[e["system"]] = by_sys.get(e["system"], 0) + 1
    print(f"인덱스 생성: {INDEX_PATH.relative_to(ROOT)}  ({len(entries)}개)")
    print("  시스템별:", by_sys)


if __name__ == "__main__":
    build()
