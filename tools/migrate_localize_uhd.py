"""localize 텍스처를 UHD(HD팩) 기반으로 마이그레이션.

각 텍스처: source=HD팩 원본(네이티브 해상도), output_scale=1, 영역 좌표를
배율(HD/현재 coord)로 재스케일. 결과물이 UHD 해상도로 생성됨.

사용:
  python tools/migrate_localize_uhd.py 247C        # 특정 (config 수정 + HD 복사)
  python tools/migrate_localize_uhd.py --all
HD팩이 현재 coord보다 작으면(배율<1) 건너뜀(다운그레이드 방지).
"""
import argparse
import json
import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
HD = Path.home() / "Downloads/Muramasa Complete 2.0/PCSE00240/Best"
CONFIG = ROOT / "translations" / "texture_localize_config.json"
ORIG = ROOT / "textures" / "originals"
INDEX = ROOT / "translations" / "ui_editor_index.json"

_SCALE_KEYS = ("x", "y", "w", "h", "font_size", "letter_spacing", "nudge_x", "nudge_y")


def coord_size(h):
    idx = {t["hash"]: t for t in json.loads(INDEX.read_text(encoding="utf-8"))["textures"]}
    return idx.get(h, {}).get("coord_size")


def scale_region(r, f):
    out = dict(r)
    for k in _SCALE_KEYS:
        if k in out and isinstance(out[k], (int, float)):
            out[k] = int(round(out[k] * f))
    if isinstance(out.get("clear_rect"), dict):
        out["clear_rect"] = {k: int(round(v * f)) for k, v in out["clear_rect"].items()}
    return out


def migrate(hash_id, cfg):
    tex = next((t for t in cfg["textures"] if hash_id in t["hash"]), None)
    if tex is None:
        print(f"  {hash_id}: config 없음"); return False
    h = tex["hash"]
    key = "regions" if tex.get("regions") else ("manual_regions" if tex.get("manual_regions") else None)
    if not key:
        print(f"  {h}: 영역 없음(수동) — 원본만 UHD 교체");
    hd_path = HD / f"{h}.png"
    if not hd_path.exists():
        print(f"  {h}: HD팩 없음 skip"); return False
    hd_size = Image.open(hd_path).size
    coord = coord_size(h)
    if not coord:
        print(f"  {h}: coord_size 없음 skip"); return False
    f = hd_size[0] / coord[0]
    if f < 1:
        print(f"  {h}: HD({hd_size}) < coord({coord}) 배율<1 skip"); return False
    # HD 원본을 textures/originals 에 복사(네이티브 해상도)
    Image.open(hd_path).convert("RGBA").save(ORIG / f"{h}.png")
    tex["source"] = f"textures/originals/{h}.png"
    tex["output_scale"] = 1
    if key:
        tex[key] = [scale_region(r, f) for r in tex[key]]
    print(f"  {h}: source=HD{hd_size}, 영역×{f:g}, output_scale=1 ({key or '수동'})")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hashes", nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    targets = ([t["hash"] for t in cfg["textures"]] if args.all else args.hashes)
    changed = False
    for h in targets:
        if migrate(h, cfg):
            changed = True
    if changed:
        CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("texture_localize_config.json 기록 완료")


if __name__ == "__main__":
    main()
