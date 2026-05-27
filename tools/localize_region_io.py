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


def to_native_place(r):
    """편집 region → place_texture_jobs 네이티브 region."""
    x, y, w, h = [int(round(v)) for v in r["box"]]
    nr = dict(r.get("native") or {})
    nr["bbox"] = [x, y, x + w, y + h]
    upd(nr, "ko", r.get("text", ""), "")
    upd(nr, "text_color", r.get("text_color", "black"), "black")
    upd(nr, "padding", float(r.get("padding", 0.08)), 0.08)
    upd(nr, "font_ratio", float(r.get("font_ratio", 0.85)), 0.85)
    if r.get("font_px"):
        nr["font_px"] = int(r["font_px"])
    else:
        nr.pop("font_px", None)
    upd(nr, "letter_spacing", int(r.get("letter_spacing") or 0), 0)
    upd(nr, "align", r.get("align", "center"), "center")
    upd(nr, "valign", r.get("valign", "center"), "center")
    upd(nr, "rotation", int(r.get("rotation", 0) or 0), 0)
    for pk in ("pad_x", "pad_y"):
        pv = r.get(pk)
        if pv is None or pv == "":
            nr.pop(pk, None)
        else:
            nr[pk] = int(pv)
    upd(nr, "render", bool(r.get("render", True)), True)
    ow = int(r.get("outline_width") or 0)
    oc = r.get("outline_color")
    if ow > 0:
        nr["outline_width"] = ow
        nr["outline_color"] = list(oc) if isinstance(oc, list) and len(oc) >= 3 else [0, 0, 0, 255]
    else:
        nr.pop("outline_width", None)
        nr.pop("outline_color", None)
    bg = r.get("background")
    if bg in ("red", "black"):
        nr["background"] = bg
        nr.pop("clear", None)
    elif bg == "clear_alpha":
        nr.pop("background", None)
        nr["clear"] = "alpha"
    elif bg == "clear_white":
        nr.pop("background", None)
        nr["clear"] = "white"
    else:
        nr.pop("background", None)
        nr.pop("clear", None)
    if r.get("layout"):
        nr["layout"] = r["layout"]
    else:
        nr.pop("layout", None)
    return nr
