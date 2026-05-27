#!/usr/bin/env python3
"""○(기본) → ✕(변형) 버튼 텍스처 변형팩 생성기.

`translations/button_variants.json` 정의를 읽어, 기본(○) 한글 텍스처(`textures/kr/ui/`)
위에 op를 적용한 ✕판 PNG를 `textures/kr/ui_xbutton/`에 만든다. 이 출력물이 '추가 덮어쓰기
팩'(이슈 #12)의 본체로, 기존 한글패치 설치 위에 같은 해시 파일명으로 덮어쓰면 ✕가 표시된다.

게임은 텍스처의 알파 채널만 사용하므로 op는 알파 보존을 우선한다.

지원 op:
  - restore_original: 원본 텍스처의 box 영역을 그대로 base 위에 덮어 글리프를 원본으로 복원.
  - clear_box:        box 영역의 알파를 0으로(글리프 제거).
  - paste_original_cc: 원본에서 seed 좌표가 속한 연결성분(글리프)을 추출해 dst_center에 중앙 배치.

사용:
  python tools/build_button_variant.py            # 전체 생성
  python tools/build_button_variant.py EDA6F03E    # 해시 프리픽스로 일부만
  python tools/build_button_variant.py --preview   # 검은 배경 합성 미리보기도 temp/preview/에 저장
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "translations" / "button_variants.json"
LOCALIZE_CONFIG = ROOT / "translations" / "texture_localize_config.json"

if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def save_config(cfg: dict) -> None:
    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_variant(cfg: dict, hash_id: str) -> dict | None:
    return next((v for v in cfg.get("variants", []) if v["hash"] == hash_id), None)


def set_memo(hash_id: str, memo: str) -> dict:
    cfg = load_config()
    v = find_variant(cfg, hash_id)
    if v is None:
        return {"ok": False, "error": "변형 목록에 없는 해시"}
    v["memo"] = memo
    save_config(cfg)
    return {"ok": True}


def base_regions_ui(hash_id: str, system: str):
    """기본(일반용) 텍스처의 region을 UI 편집 포맷으로 반환 (ui_editor_index 기준)."""
    import json as _json
    idx_path = ROOT / "translations" / "ui_editor_index.json"
    idx = _json.loads(idx_path.read_text(encoding="utf-8"))
    tex = next((t for t in idx["textures"] if t["hash"] == hash_id), None)
    return list((tex or {}).get("regions", []))


def set_variant_regions(hash_id: str, ui_regions: list, system: str) -> dict:
    """✕용 텍스처의 독립 region 세트(UI 편집 포맷)를 button_variants.json에 저장.

    '같은 파일'을 일반용(→textures/kr/ui)과 ✕용(→textures/kr/ui_xbutton)으로 분리하는 개념.
    """
    cfg = load_config()
    v = find_variant(cfg, hash_id)
    if v is None:
        v = {"hash": hash_id, "label": hash_id, "memo": "", "ops": []}
        cfg.setdefault("variants", []).append(v)
    v["system"] = system
    # native 중복은 저장 시 떼어내 파일 크기를 줄인다(렌더 시 top-level에서 재구성).
    v["regions"] = [{k: rr for k, rr in r.items() if k != "native"} for r in ui_regions]
    v.setdefault("ops", [])
    v.pop("exclude_region_ids", None)  # 구버전 정리
    save_config(cfg)
    return {"ok": True}


def render_region_variant(hash_id: str, system: str, ui_regions: list, out_dir: Path | None = None) -> Path:
    """✕용 region 세트로 텍스처를 렌더해 ui_xbutton(또는 out_dir)에 저장.

    localize / place 둘 다 지원. 원본(source)은 일반용과 동일, region만 ✕용 세트로 교체.
    """
    import json as _json
    from localize_region_io import to_native_localize, to_native_place

    out_dir = out_dir or (ROOT / load_config()["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    if system == "place":
        import render_place_texture_job as PJ
        doc = _json.loads((ROOT / "translations" / "place_texture_jobs.json").read_text(encoding="utf-8"))
        base = doc["textures"].get(hash_id)
        if base is None:
            raise ValueError(f"place config에 {hash_id} 없음")
        job = dict(base)
        job["regions"] = [to_native_place(r) for r in ui_regions]
        font = PJ.repo_path(doc.get("font"), PJ.DEFAULT_FONT)
        return PJ.render_job(hash_id, job, out_dir, None, font)

    # localize
    import texture_localize as TL
    cfg = _json.loads(LOCALIZE_CONFIG.read_text(encoding="utf-8"))
    base = next((t for t in cfg["textures"] if t["hash"] == hash_id), None)
    if base is None:
        raise ValueError(f"localize config에 {hash_id} 없음")
    tmp = dict(base)
    tmp["regions"] = [to_native_localize(r) for r in ui_regions]
    if not tmp["regions"]:
        raise ValueError("렌더할 region이 없습니다")
    orig_imp, orig_repo = TL.IMPORT_DIR, TL.REPO_KR_DIR
    TL.IMPORT_DIR = out_dir
    TL.REPO_KR_DIR = out_dir
    try:
        TL.process_texture(hash_id, tmp, preview=False)
    finally:
        TL.IMPORT_DIR, TL.REPO_KR_DIR = orig_imp, orig_repo
    return out_dir / f"{hash_id}.png"


def toggle(hash_id: str, include: bool, label: str = "") -> dict:
    """해시를 ✕ 변형 대상 목록에 넣거나 뺀다. 새로 넣을 땐 ops 비움(수동 ui_xbutton PNG 사용)."""
    cfg = load_config()
    v = find_variant(cfg, hash_id)
    if include and v is None:
        cfg.setdefault("variants", []).append(
            {"hash": hash_id, "label": label or hash_id, "memo": "", "ops": []}
        )
    elif not include and v is not None:
        cfg["variants"] = [x for x in cfg["variants"] if x["hash"] != hash_id]
    save_config(cfg)
    return {"ok": True}


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def op_restore_original(base: Image.Image, original: Image.Image, op: dict) -> None:
    x, y, w, h = op["box"]
    region = original.crop((x, y, x + w, y + h))
    base.paste(region, (x, y))  # 원본 픽셀(RGBA) 그대로 복원


def op_clear_box(base: Image.Image, op: dict) -> None:
    x, y, w, h = op["box"]
    arr = np.array(base)
    arr[y : y + h, x : x + w, 3] = 0  # 알파만 0으로 (RGB는 보존)
    base.frombytes(Image.fromarray(arr, "RGBA").tobytes())


def _extract_cc(original: Image.Image, seed, threshold: int):
    """seed 좌표가 속한 알파 연결성분을 추출해 (masked RGBA crop, bbox) 반환."""
    from scipy import ndimage

    arr = np.array(original)
    mask = arr[:, :, 3] > threshold
    labeled, _ = ndimage.label(mask)
    sx, sy = seed
    cid = labeled[sy, sx]
    if cid == 0:
        raise ValueError(f"seed {seed} 위치에 글리프(알파>{threshold})가 없습니다")
    comp = labeled == cid
    ys, xs = np.where(comp)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    out = arr[y0:y1, x0:x1].copy()
    # 연결성분 밖 픽셀은 투명 처리(이웃 글리프 혼입 방지)
    local = comp[y0:y1, x0:x1]
    out[~local, 3] = 0
    return Image.fromarray(out, "RGBA"), (x0, y0, x1, y1)


def op_paste_original_cc(base: Image.Image, original: Image.Image, op: dict) -> None:
    sprite, (x0, y0, x1, y1) = _extract_cc(original, op["seed"], op.get("alpha_threshold", 60))
    cx, cy = op["dst_center"]
    w, h = sprite.size
    px, py = int(cx - w / 2), int(cy - h / 2)
    base.alpha_composite(sprite, (px, py))


OPS = {
    "restore_original": lambda base, orig, op: op_restore_original(base, orig, op),
    "clear_box": lambda base, orig, op: op_clear_box(base, op),
    "paste_original_cc": lambda base, orig, op: op_paste_original_cc(base, orig, op),
}


def build(prefix: str | None = None, preview: bool = False) -> list[Path]:
    cfg = load_config()
    base_dir = ROOT / cfg["base_dir"]
    orig_dir = ROOT / cfg["original_dir"]
    out_dir = ROOT / cfg["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for v in cfg["variants"]:
        h = v["hash"]
        if prefix and not h.startswith(prefix):
            continue
        base_path = base_dir / f"{h}.png"
        orig_path = orig_dir / f"{h}.png"
        out_path = out_dir / f"{h}.png"
        if not base_path.exists():
            print(f"  ! 기본 텍스처 없음: {base_path}")
            continue
        if v.get("regions") is not None:
            # localize/place 변형: ✕용 독립 region 세트로 렌더 → ui_xbutton
            render_region_variant(h, v.get("system", "localize"), v["regions"], out_dir)
            print(f"  ✓ {h}  ({v.get('label','')}) → {v.get('system','localize')} 변형 렌더 ({len(v['regions'])} region)")
            written.append(out_path)
            continue
        if not v.get("ops"):
            # ops가 없으면: 수동 편집한 ✕ PNG가 이미 있으면 보존, 없으면 ○ 복제(편집 시작점)
            if out_path.exists():
                print(f"  · {h}  (수동 ✕ PNG 보존, ops 없음)")
                written.append(out_path)
            else:
                load_rgba(base_path).save(out_path)
                print(f"  · {h}  (ops 없음 → ○ 복제 생성. ui_xbutton PNG를 직접 ✕로 편집하세요)")
                written.append(out_path)
            continue
        base = load_rgba(base_path)
        original = load_rgba(orig_path) if orig_path.exists() else None
        if original is not None and original.size != base.size:
            original = original.resize(base.size)
        for op in v["ops"]:
            t = op["type"]
            if t not in OPS:
                raise ValueError(f"알 수 없는 op: {t}")
            if t != "clear_box" and original is None:
                raise FileNotFoundError(f"{t}에 원본 필요: {orig_path}")
            OPS[t](base, original, op)
        base.save(out_path)
        written.append(out_path)
        print(f"  ✓ {h}  ({v.get('label','')}) → {out_path.relative_to(ROOT)}")
        if preview:
            bg = Image.new("RGBA", base.size, (30, 30, 30, 255))
            comp = Image.alpha_composite(bg, base).convert("RGB")
            comp.thumbnail((1400, 1400))
            pv = ROOT / "temp" / "preview" / f"xbtn_{h[:8]}.png"
            pv.parent.mkdir(parents=True, exist_ok=True)
            comp.save(pv)
    return written


def main(argv: list[str]) -> int:
    prefix = None
    preview = "--preview" in argv
    for a in argv:
        if not a.startswith("-"):
            prefix = a.upper()
    print("○→✕ 버튼 변형팩 생성:")
    written = build(prefix, preview)
    print(f"완료: {len(written)}개 텍스처 → {ROOT / json.loads(CONFIG.read_text(encoding='utf-8'))['out_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
