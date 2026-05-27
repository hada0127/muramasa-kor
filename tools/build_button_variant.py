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
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
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
        if not base_path.exists():
            print(f"  ! 기본 텍스처 없음: {base_path}")
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
        out_path = out_dir / f"{h}.png"
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
