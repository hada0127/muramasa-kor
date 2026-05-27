"""UI 에디터 region(편집 포맷) → texture_localize 네이티브 region 변환.

UI 에디터(server.py)와 ✕ 변형 빌드(build_button_variant.py)가 같은 변환을 쓰도록 공유.
이전엔 server.py에 _to_native_localize로 있던 로직을 그대로 옮긴 것.
"""
from __future__ import annotations


def color_list(c):
    if isinstance(c, list):
        return c
    return [255, 255, 255, 255]


def upd(d, key, value, default):
    """기존 키는 항상 갱신, 없던 키는 비기본값일 때만 추가 (무변경 round-trip 보장)."""
    if key in d or value != default:
        d[key] = value


def to_native_localize(r):
    """편집 region → texture_localize 네이티브 region."""
    x, y, w, h = [int(round(v)) for v in r["box"]]
    nr = dict(r.get("native") or {})
    nr.update({"x": x, "y": y, "w": w, "h": h, "text": r.get("text", "")})
    fs = r.get("font_size")
    if fs is not None and fs != "" and int(fs) > 0:
        nr["font_size"] = int(fs)
    else:
        nr.pop("font_size", None)
    upd(nr, "color", color_list(r.get("color")), [255, 255, 255, 255])
    upd(nr, "align", r.get("align", "left"), "left")
    upd(nr, "v_align", r.get("v_align", "top"), "top")
    upd(nr, "clear", bool(r.get("clear", True)), True)
    upd(nr, "fit_to_box", bool(r.get("fit_to_box", False)), False)
    upd(nr, "letter_spacing", int(r.get("letter_spacing") or 0), 0)
    if r.get("orient"):
        nr["orient"] = r["orient"]
    for k in ("layout", "rotation", "font_ratio", "font_px",
              "pad_x", "pad_y", "background", "render", "blur"):
        v = r.get(k)
        if v is None or v == "" or v == 0:
            nr.pop(k, None)
        else:
            nr[k] = v
    ow = int(r.get("outline_width") or 0)
    oc = r.get("outline_color")
    if ow > 0:
        nr["outline_width"] = ow
        nr["outline_color"] = list(oc) if isinstance(oc, list) and len(oc) >= 3 else [0, 0, 0, 255]
    else:
        nr.pop("outline_width", None)
        nr.pop("outline_color", None)
    nr.pop("clear_rect", None)
    return nr
