"""kra_extracted/<hash>.json → place_texture_jobs.json 영역으로 변환.

각 텍스트의 SVG transform(translate/matrix: 스케일·회전·이동)을 적용해 실제
잉크 박스를 kr 좌표로 계산하고, place region(절대 글씨크기 font_px + 회전 layout)
으로 변환한다. 변환 후 편집기에서 위치 미세조정 가능.

사용:
  python tools/kra_to_place.py A3BE57CE          # 특정 해시만 (미리보기, 미저장)
  python tools/kra_to_place.py A3BE57CE --write   # place_texture_jobs.json에 기록
  python tools/kra_to_place.py --all --write      # 7개 전부 기록
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_DIR = ROOT / "translations" / "kra_extracted"
PLACE_JOBS = ROOT / "translations" / "place_texture_jobs.json"
ORIG_DIR = ROOT / "textures" / "originals"
FONT = str(ROOT / "fonts" / "Griun_PolSensibility-Rg.ttf")


def _transform_point(x, y, kind, params):
    if kind == "translate":
        tx, ty = params
        return tx + x, ty + y
    a, b, c, d, e, f = params  # matrix
    return a * x + c * y + e, b * x + d * y + f


def element_bbox(el, krscale):
    """SVG transform 적용해 잉크 박스(kr 좌표 AABB)와 회전 반환."""
    text = el["text"]
    fs = max(4, int(round(el["font_size"])))
    font = ImageFont.truetype(FONT, fs)
    asc = font.getmetrics()[0]
    l, t, r, b = font.getbbox(text)
    # SVG 텍스트 원점 = baseline-left(0,0). 잉크 박스(베이스라인 기준) 모서리:
    corners = [(l, t - asc), (r, t - asc), (r, b - asc), (l, b - asc)]

    rot = el["rotation"]
    scale = el.get("scale", 1.0)
    # transform: scale*rotation 후 translate. matrix면 a,b,c,d가 scale·rot 포함.
    if rot in (0, 0.0):
        kind, params = "matrix", (scale, 0, 0, scale, el["x"], el["y"])
    else:
        import math
        rad = math.radians(rot)
        a = scale * math.cos(rad)
        bb = scale * math.sin(rad)
        cc = -scale * math.sin(rad)
        dd = scale * math.cos(rad)
        kind, params = "matrix", (a, bb, cc, dd, el["x"], el["y"])

    pts = [_transform_point(px, py, kind, params) for px, py in corners]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    # kr 좌표로 스케일
    box = [x0 * krscale, y0 * krscale, x1 * krscale, y1 * krscale]
    return [int(round(v)) for v in box], rot


def convert(hash_id, doc):
    vb = doc["viewbox"]
    kr = doc["kr_size"] or vb
    krscale = kr[0] / vb[0] if vb else 1.0
    regions = []
    for i, el in enumerate(doc["elements"]):
        bbox, rot = element_bbox(el, krscale)
        font_px = int(round(el["font_px"] * krscale))
        # 회전 → layout: 0=가로쓰기, ±90=세로쓰기(글자 세움; 한국어 표준). 추후 조정 가능.
        layout = "horizontal" if rot in (0, 0.0) else "vertical"
        color = el.get("color", "#ffffff")
        text_color = "white" if color.lower() in ("#ffffff", "#fff", "white") else "black"
        regions.append({
            "id": f"K{i}",
            "ja": "",
            "ko": el["text"],
            "bbox": bbox,
            "text_color": text_color,
            "layout": layout,
            "font_px": font_px,
            "align": "center",
            "valign": "center",
            "render": True,
            "source": "kra_extract",
        })
    return regions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hashes", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    files = sorted(EXTRACT_DIR.glob("*.json"))
    if not args.all:
        files = [f for f in files if any(h in f.stem for h in args.hashes)]
    if not files:
        raise SystemExit("대상 없음 (해시 지정 또는 --all)")

    doc_jobs = json.loads(PLACE_JOBS.read_text(encoding="utf-8")) if args.write else None
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        h = doc["hash"]
        src = ORIG_DIR / f"{h}.png"
        regions = convert(h, doc)
        print(f"{h}: {len(regions)}개 region 변환 (source={'있음' if src.exists() else '없음'})")
        for r in regions[:3]:
            print(f"   {r['ko']!r} bbox={r['bbox']} layout={r['layout']} font_px={r['font_px']}")
        if args.write:
            doc_jobs["textures"][h] = {
                "source": f"textures/originals/{h}.png" if src.exists() else None,
                "output_scale": 1,
                "status": "needs_review",  # 자동 일괄 재렌더 제외, 편집기 on-demand만
                "_from": "kra_extract (자동 변환 — 위치 미세조정 필요)",
                "regions": regions,
            }
    if args.write:
        PLACE_JOBS.write_text(
            json.dumps(doc_jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nplace_texture_jobs.json 기록 완료")


if __name__ == "__main__":
    main()
