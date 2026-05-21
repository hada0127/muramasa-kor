"""크리타(.kra) 파일에서 텍스트 레이어의 좌표·내용을 추출.

.kra = ZIP. 내부 maindoc.xml(레이어 구조) + 각 shapelayer의 content.svg(텍스트).
각 <text> 요소의 transform(translate 또는 matrix), font-size, fill, 내용을 파싱해
텍스처 좌표 공간 기준 위치·유효 글씨크기·회전을 계산한다.

출력: translations/kra_extracted/<hash>.json (원시 추출 결과)
사용: python tools/kra_extract.py            # textures/work/*.kra 전부
"""
import json
import math
import re
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = ROOT / "textures" / "work"
OUT_DIR = ROOT / "translations" / "kra_extracted"
KR_DIR = ROOT / "kr_textures" / "ui"

_TEXT_RE = re.compile(r"<text\b([^>]*)>(.*?)</text>", re.S)
_VIEWBOX_RE = re.compile(r'viewBox="([\d.\s]+)"')


def _attr(tag, name):
    m = re.search(name + r'="([^"]*)"', tag)
    return m.group(1) if m else None


def _style(tag, key):
    m = re.search(r"style=\"([^\"]*)\"", tag)
    if not m:
        return None
    sm = re.search(key + r"\s*:\s*([^;]+)", m.group(1))
    return sm.group(1).strip() if sm else None


def _parse_transform(tag):
    """transform → (tx, ty, scale, rotation_deg)."""
    tr = _attr(tag, "transform")
    if not tr:
        return 0.0, 0.0, 1.0, 0.0
    m = re.search(r"translate\(([-\d.eE]+),\s*([-\d.eE]+)\)", tr)
    if m:
        return float(m.group(1)), float(m.group(2)), 1.0, 0.0
    m = re.search(r"matrix\(([^)]+)\)", tr)
    if m:
        a, b, c, d, e, f = [float(v) for v in re.split(r"[,\s]+", m.group(1).strip())]
        scale = math.hypot(a, b) or 1.0
        rot = round(math.degrees(math.atan2(b, a)))
        return e, f, scale, rot
    return 0.0, 0.0, 1.0, 0.0


def _text_content(inner):
    """<tspan> 등 태그 제거, 줄바꿈 보존."""
    inner = re.sub(r"<tspan[^>]*>", "", inner)
    inner = inner.replace("</tspan>", "")
    inner = re.sub(r"<[^>]+>", "", inner)
    return inner.strip()


def extract_kra(kra_path):
    z = zipfile.ZipFile(kra_path)
    svgs = [n for n in z.namelist() if n.endswith("content.svg")]
    elements = []
    viewbox = None
    for n in svgs:
        s = z.read(n).decode("utf-8", errors="replace")
        if viewbox is None:
            vm = _VIEWBOX_RE.search(s)
            if vm:
                vals = [float(x) for x in vm.group(1).split()]
                viewbox = [vals[2], vals[3]]
        for m in _TEXT_RE.finditer(s):
            tag, inner = m.group(1), m.group(2)
            text = _text_content(inner)
            if not text:
                continue
            tx, ty, scale, rot = _parse_transform(tag)
            fs_raw = _style(tag, "font-size") or _attr(tag, "font-size") or "0"
            font_size = float(re.sub(r"[^\d.]", "", fs_raw) or 0)
            fill = _style(tag, "fill") or _attr(tag, "fill") or "#ffffff"
            stroke_w = _style(tag, "stroke-width") or _attr(tag, "stroke-width") or "0"
            ls = _style(tag, "letter-spacing") or "0"
            elements.append({
                "text": text,
                "x": round(tx, 2),
                "y": round(ty, 2),
                "font_size": round(font_size, 2),
                "scale": round(scale, 4),
                "font_px": round(font_size * scale, 2),
                "rotation": rot,
                "color": fill,
                "stroke_width": stroke_w,
                "letter_spacing": ls,
            })
    return viewbox, elements


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for kra in sorted(WORK_DIR.glob("*.kra")):
        h = kra.stem
        viewbox, elements = extract_kra(kra)
        kr_path = KR_DIR / f"{h}.png"
        kr_size = list(Image.open(kr_path).size) if kr_path.exists() else None
        doc = {
            "hash": h,
            "source_kra": str(kra.relative_to(ROOT)),
            "viewbox": viewbox,
            "kr_size": kr_size,
            "count": len(elements),
            "elements": elements,
        }
        out = OUT_DIR / f"{h}.json"
        out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        rots = sorted(set(e["rotation"] for e in elements))
        summary.append((h, len(elements), viewbox, rots))
        print(f"{h}: {len(elements)}개 텍스트, viewbox={viewbox}, 회전={rots} → {out.relative_to(ROOT)}")
    print(f"\n총 {len(summary)}개 .kra 추출 완료 → {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
