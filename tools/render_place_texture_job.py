"""Render place-name textures from explicit per-file JSON jobs.

The job file is intentionally file-oriented: fix one hash entry, render only
that hash, inspect the preview, then apply/install if it is correct.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JOBS = ROOT / "translations/place_texture_jobs.json"
DEFAULT_OUT = ROOT / "kr_textures/ui"
DEFAULT_FONT = ROOT / "fonts/Griun_PolSensibility-Rg.ttf"
DEFAULT_SOURCE_DIR = ROOT / "textures/place_name_originals"
DEFAULT_APPLY_DIR = ROOT / "kr_textures/ui"
TITLE_ID = "PCSE00240"

BACKGROUND_COLORS = {
    "red": (204, 66, 58, 255),
    "black": (0, 0, 0, 255),
}

TEXT_COLORS = {
    "black": (0, 0, 0, 255),
    "white": (255, 255, 255, 255),
}


def repo_path(value: str | None, fallback: Path) -> Path:
    if not value:
        return fallback
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def load_jobs(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def clear_region(img: Image.Image, bbox: list[int], color: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = bbox
    arr = np.array(img)
    region = arr[y0:y1, x0:x1].copy()
    mask = region[:, :, 3] > 128
    for c, v in enumerate(color[:3]):
        region[:, :, c] = np.where(mask, v, region[:, :, c])
    arr[y0:y1, x0:x1] = region
    return Image.fromarray(arr, "RGBA")


def fill_region(img: Image.Image, bbox: list[int], color: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = bbox
    d = ImageDraw.Draw(img)
    d.rectangle((x0, y0, x1, y1), fill=color)
    return img


def kill_white_in_bbox(img: Image.Image, bbox: list[int]) -> Image.Image:
    x0, y0, x1, y1 = bbox
    arr = np.array(img)
    region = arr[y0:y1, x0:x1]
    r, g, b, a = region[:, :, 0], region[:, :, 1], region[:, :, 2], region[:, :, 3]
    white_mask = (r > 70) & (g > 70) & (b > 70) & (a > 0)
    region[:, :, 3] = np.where(white_mask, 0, a)
    return Image.fromarray(arr, "RGBA")


def clear_alpha_in_bbox(img: Image.Image, bbox: list[int]) -> Image.Image:
    x0, y0, x1, y1 = bbox
    arr = np.array(img)
    arr[y0:y1, x0:x1, 3] = 0
    return Image.fromarray(arr, "RGBA")


def _sp_width(font, text, ls):
    """자간(ls) 포함 가로 텍스트 폭."""
    if not text:
        return 0
    return sum(font.getlength(ch) for ch in text) + ls * (len(text) - 1)


def _draw_sp(d, x, y, text, font, fill, ls):
    """글자별 자간(ls)을 두며 가로로 그린다."""
    cx = x
    for ch in text:
        d.text((cx, y), ch, font=font, fill=fill)
        cx += font.getlength(ch) + ls


def _off(mode, avail, size, lo="left", hi="right"):
    """정렬 오프셋: lo=0, center=가운데, hi=끝. (넘침 시 음수 허용 → 캔버스가 클리핑)"""
    if mode == lo:
        return 0
    if mode == hi:
        return avail - size
    return (avail - size) // 2


def render_text(
    base_img: Image.Image,
    bbox: list[int],
    text: str,
    fill: tuple[int, int, int, int],
    font_path: Path,
    padding: float = 0.08,
    fr: float = 0.85,
    layout: str | None = None,
    letter_spacing: int = 0,
    align: str = "center",
    valign: str = "center",
    pad_x: float | None = None,
    pad_y: float | None = None,
    font_px: int | None = None,
) -> None:
    ls = int(letter_spacing)
    # 정렬/패딩/자간/픽셀폰트 지정이 없으면 기존(비율 자동맞춤) 경로 → 기존 렌더 보존
    if (font_px is None and align == "center" and valign == "center"
            and pad_x is None and pad_y is None and ls == 0):
        _render_legacy(base_img, bbox, text, fill, font_path, padding, fr, layout, ls)
    else:
        _render_aligned(base_img, bbox, text, fill, font_path, padding, fr, layout,
                        ls, align, valign, pad_x, pad_y, font_px)


def _render_aligned(base_img, bbox, text, fill, font_path, padding, fr, layout,
                    ls, align, valign, pad_x, pad_y, font_px):
    """픽셀 폰트 + H/V 정렬 + 상하/좌우 패딩(px) 기반 렌더.
    세로/회전에서 자간(ls)은 글자 사이 추가 간격(px)으로 깔끔히 동작."""
    x0, y0, x1, y1 = bbox
    rw, rh = x1 - x0, y1 - y0
    fp = str(font_path)

    is_rot = layout == "rotated" or (layout is None and rw > rh)
    is_horiz = layout == "horizontal"
    chars = [c for c in text if c != " "]
    n = max(1, len(chars))

    # 방향별 패딩 기본값 (legacy와 동일: 글자가 채우는 축만 padding, 교차축은 0)
    if is_horiz:
        dpx, dpy = rw * padding, rh * padding
    elif is_rot:
        dpx, dpy = rw * padding, 0          # 가로배너: 좌우(길이) padding, 상하(교차) 0
    else:
        dpx, dpy = 0, rh * padding          # 세로: 좌우(교차) 0, 상하(길이) padding
    pxl = int(pad_x) if pad_x is not None else int(dpx)
    pyl = int(pad_y) if pad_y is not None else int(dpy)
    inner_w = max(1, rw - 2 * pxl)
    inner_h = max(1, rh - 2 * pyl)

    if is_horiz:
        d = ImageDraw.Draw(base_img)
        if font_px:
            fs = int(font_px)
        else:
            fs = max(8, int(inner_h * fr))
            while fs > 8:
                f = ImageFont.truetype(fp, fs)
                bb = f.getbbox(text)
                tw = _sp_width(f, text, ls) if ls else bb[2] - bb[0]
                if tw <= inner_w and (bb[3] - bb[1]) <= inner_h:
                    break
                fs -= 1
        font = ImageFont.truetype(fp, max(4, fs))
        bb = font.getbbox(text)
        tw = _sp_width(font, text, ls) if ls else bb[2] - bb[0]
        th = bb[3] - bb[1]
        tx = x0 + pxl + _off(align, inner_w, tw) - bb[0]
        ty = y0 + pyl + _off(valign, inner_h, th, "top", "bottom") - bb[1]
        if ls:
            _draw_sp(d, tx, ty, text, font, fill, ls)
        else:
            d.text((tx, ty), text, font=font, fill=fill)
        return

    # 세로/회전 모두 박스 크기 캔버스에 그린 뒤 합성 → 박스 밖 넘침은 클리핑(편집창과 동일)
    if is_rot:
        # 회전 캔버스: width=rh(최종 높이=cross), height=rw(최종 너비=length)
        canvas = Image.new("RGBA", (rh, rw), (0, 0, 0, 0))
        len_avail, cross_avail = inner_w, inner_h  # length=rw축, cross=rh축
        len_pad, cross_pad = pxl, pyl
    else:
        # 세로 캔버스 = 박스 크기 (rw x rh)
        canvas = Image.new("RGBA", (rw, rh), (0, 0, 0, 0))
        len_avail, cross_avail = inner_h, inner_w  # length=rh축(세로), cross=rw축
        len_pad, cross_pad = pyl, pxl
    d = ImageDraw.Draw(canvas)

    # 셀(slot) 기반: 글자를 길이축에 균등 분배. 공백도 한 셀 차지(띄어쓰기 반영).
    # 자간 0이면 박스를 채움(=기존), 자간은 셀 간격에 가산, 글자 크기는 자간과 무관.
    cells = list(text)
    ncells = max(1, len(cells))
    cell0 = max(1, len_avail // ncells)
    if font_px:
        fs = int(font_px)
    else:
        fs = max(8, int(min(cross_avail, cell0) * fr))
    font = ImageFont.truetype(fp, max(4, fs))
    metrics = [font.getbbox(c) for c in cells if c != " "] or [font.getbbox("가")]
    gw = max(m[2] - m[0] for m in metrics)
    pitch = cell0 + ls
    block_len = (ncells - 1) * pitch + cell0
    len_mode = align if is_rot else valign
    cross_mode = valign if is_rot else align
    start_len = len_pad + _off(len_mode, len_avail, block_len,
                               "left" if is_rot else "top", "right" if is_rot else "bottom")
    cross_left = cross_pad + _off(cross_mode, cross_avail, gw, "left", "right")
    cross_cx = cross_left + gw // 2
    for i, ch in enumerate(cells):
        if ch == " ":
            continue  # 공백 셀은 비우고 슬롯만 차지
        m = font.getbbox(ch)
        cw, chh = m[2] - m[0], m[3] - m[1]
        cx = cross_cx - (cw // 2 + m[0])
        cy = start_len + i * pitch + cell0 // 2 - (chh // 2 + m[1])
        d.text((cx, cy), ch, font=font, fill=fill)

    if is_rot:
        layer = canvas.rotate(90, expand=True)
        if layer.size != (rw, rh):
            layer = layer.resize((rw, rh))
    else:
        layer = canvas
    region = base_img.crop(tuple(bbox)).convert("RGBA")
    region = Image.alpha_composite(region, layer)
    base_img.paste(region, (x0, y0))


def _render_legacy(base_img, bbox, text, fill, font_path, padding, fr, layout, ls):
    """기존 비율(fr) 자동맞춤 렌더 (정렬/패딩 미지정 시) — 기존 출력 보존."""
    x0, y0, x1, y1 = bbox
    rw, rh = x1 - x0, y1 - y0

    if layout == "vertical_columns":
        d = ImageDraw.Draw(base_img)
        words = [w for w in text.split(" ") if w]
        if not words:
            words = [text]
        pad_x = int(rw * padding)
        pad_y = int(rh * padding)
        max_w = max(1, rw - 2 * pad_x)
        max_h = max(1, rh - 2 * pad_y)
        fs = max(8, int(min(max_h, max_w) * fr))
        chosen = None
        while fs > 8:
            font = ImageFont.truetype(str(font_path), fs)
            chars = [c for w in words for c in w]
            metrics = [font.getbbox(ch) for ch in chars]
            max_cw = max((bb[2] - bb[0] for bb in metrics), default=fs)
            max_ch = max((bb[3] - bb[1] for bb in metrics), default=fs)
            row_h = max(1, int(max_ch * 1.18) + ls)
            col_w = max(1, int(max_cw * 1.28))
            rows = max(1, max_h // row_h)
            columns: list[str] = []
            for word in words:
                if not word:
                    continue
                for i in range(0, len(word), rows):
                    columns.append(word[i : i + rows])
            cols = max(1, len(columns))
            if cols * col_w <= max_w:
                chosen = (font, row_h, col_w, rows, cols, columns)
                break
            fs -= 1
        if chosen is None:
            font = ImageFont.truetype(str(font_path), max(8, fs))
            flat = "".join(words)
            row_h = max(1, max_h // max(1, len(flat)))
            col_w = max(1, max_w)
            rows = max(1, len(flat))
            columns = [flat]
            cols = 1
        else:
            font, row_h, col_w, rows, cols, columns = chosen
        block_w = cols * col_w
        block_h = max((len(col) for col in columns), default=1) * row_h
        start_x = x0 + pad_x + (max_w - block_w) // 2 + (cols - 1) * col_w
        start_y = y0 + pad_y + (max_h - block_h) // 2
        for col, column_text in enumerate(columns):
            col_y = start_y + (block_h - len(column_text) * row_h) // 2
            for row, ch in enumerate(column_text):
                bb = font.getbbox(ch)
                cw, chh = bb[2] - bb[0], bb[3] - bb[1]
                cx = start_x - col * col_w + col_w // 2 - (cw // 2 + bb[0])
                cy = col_y + row * row_h + row_h // 2 - (chh // 2 + bb[1])
                d.text((cx, cy), ch, font=font, fill=fill)
        return

    if layout == "horizontal":
        d = ImageDraw.Draw(base_img)
        pad_x = int(rw * padding)
        pad_y = int(rh * padding)
        max_w = max(1, rw - 2 * pad_x)
        max_h = max(1, rh - 2 * pad_y)
        fs = max(8, int(max_h * fr))
        while fs > 8:
            font = ImageFont.truetype(str(font_path), fs)
            bb = d.textbbox((0, 0), text, font=font)
            tw = _sp_width(font, text, ls) if ls else bb[2] - bb[0]
            th = bb[3] - bb[1]
            if tw <= max_w and th <= max_h:
                break
            fs -= 1
        font = ImageFont.truetype(str(font_path), fs)
        bb = d.textbbox((0, 0), text, font=font)
        tw = _sp_width(font, text, ls) if ls else bb[2] - bb[0]
        th = bb[3] - bb[1]
        tx = x0 + (rw - tw) // 2 - bb[0]
        ty = y0 + (rh - th) // 2 - bb[1]
        if ls:
            _draw_sp(d, tx, ty, text, font, fill, ls)
        else:
            d.text((tx, ty), text, font=font, fill=fill)
        return

    rotated = layout == "rotated" or (layout is None and rw > rh)
    n = max(1, len(text))   # 공백 포함 (띄어쓰기 반영)

    if rotated:
        canvas = Image.new("RGBA", (rh, rw), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        pad = int(rw * padding)
        cell = max(1, (rw - 2 * pad - ls * (n - 1)) // n)
        fs = max(8, int(min(rh, cell) * fr))
        font = ImageFont.truetype(str(font_path), fs)
        for i, ch in enumerate(text):
            if ch == " ":
                continue
            bb = font.getbbox(ch)
            cw, chh = bb[2] - bb[0], bb[3] - bb[1]
            cx = rh // 2 - (cw // 2 + bb[0])
            cy = pad + i * (cell + ls) + cell // 2 - (chh // 2 + bb[1])
            d.text((cx, cy), ch, font=font, fill=fill)
        rot = canvas.rotate(90, expand=True)
        if rot.size != (rw, rh):
            rot = rot.resize((rw, rh))
        region = base_img.crop(tuple(bbox)).convert("RGBA")
        region = Image.alpha_composite(region, rot)
        base_img.paste(region, (x0, y0))
        return

    d = ImageDraw.Draw(base_img)
    pad = int(rh * padding)
    cell = max(1, (rh - 2 * pad - ls * (n - 1)) // n)
    fs = max(8, int(min(rw, cell) * fr))
    font = ImageFont.truetype(str(font_path), fs)
    yt = y0 + pad
    for i, ch in enumerate(text):
        if ch == " ":
            continue
        bb = font.getbbox(ch)
        cw, chh = bb[2] - bb[0], bb[3] - bb[1]
        cx = x0 + rw // 2 - (cw // 2 + bb[0])
        cy = yt + i * (cell + ls) + cell // 2 - (chh // 2 + bb[1])
        d.text((cx, cy), ch, font=font, fill=fill)


def render_job(hash_id: str, job: dict, out_dir: Path, apply_dir: Path | None, font_path: Path) -> Path:
    source = repo_path(job.get("source"), DEFAULT_SOURCE_DIR / f"{hash_id}.png")
    if not source.exists():
        raise FileNotFoundError(f"missing source for {hash_id}: {source}")

    img = Image.open(source).convert("RGBA")
    for region in job.get("regions", []):
        if not region.get("render", True):
            continue
        bbox = region["bbox"]
        background = region.get("background")
        if background in BACKGROUND_COLORS:
            if region.get("background_mode") == "fill":
                img = fill_region(img, bbox, BACKGROUND_COLORS[background])
            else:
                img = clear_region(img, bbox, BACKGROUND_COLORS[background])
        elif region.get("clear") == "white":
            img = kill_white_in_bbox(img, bbox)
        elif region.get("clear") == "alpha":
            img = clear_alpha_in_bbox(img, bbox)

        text = region.get("ko", "")
        if text:
            text_color = TEXT_COLORS[region.get("text_color", "black")]
            render_text(
                img,
                bbox,
                text,
                text_color,
                font_path,
                padding=float(region.get("padding", 0.08)),
                fr=float(region.get("font_ratio", 0.85)),
                layout=region.get("layout"),
                letter_spacing=int(region.get("letter_spacing", 0)),
                align=region.get("align", "center"),
                valign=region.get("valign", "center"),
                pad_x=region.get("pad_x"),
                pad_y=region.get("pad_y"),
            )

    scale = int(job.get("output_scale", 1))
    if scale > 1:
        img = img.resize((img.width * scale, img.height * scale), Image.Resampling.LANCZOS)

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{hash_id}.png"
    img.save(out)
    if apply_dir is not None:
        apply_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(out, apply_dir / out.name)
    return out


def make_compare(hash_id: str, rendered: Path, preview_dir: Path) -> Path:
    preview_dir.mkdir(parents=True, exist_ok=True)
    panels = []
    for label, p in [
        ("original", DEFAULT_SOURCE_DIR / f"{hash_id}.png"),
        ("current", DEFAULT_APPLY_DIR / f"{hash_id}.png"),
        ("rendered", rendered),
    ]:
        panel = Image.new("RGBA", (720, 760), (28, 28, 28, 255))
        d = ImageDraw.Draw(panel)
        d.text((16, 12), label, fill=(255, 255, 255, 255))
        if p.exists():
            im = Image.open(p).convert("RGBA")
            im.thumbnail((700, 710), Image.Resampling.LANCZOS)
            panel.alpha_composite(im, ((720 - im.width) // 2, 42))
        panels.append(panel)
    sheet = Image.new("RGBA", (2160, 760), (18, 18, 18, 255))
    for i, panel in enumerate(panels):
        sheet.alpha_composite(panel, (i * 720, 0))
    out = preview_dir / f"{hash_id}_compare.jpg"
    sheet.convert("RGB").save(out, quality=92)
    return out


def install_to_vita3k(rendered_files: list[Path]) -> None:
    targets = [
        Path.home() / "Library/Application Support/Vita3K/Vita3K/textures/import" / TITLE_ID,
        Path.home() / "Library/Application Support/Vita3K/Vita3K/fs/textures/import" / TITLE_ID,
    ]
    for target in targets:
        target.mkdir(parents=True, exist_ok=True)
        for src in rendered_files:
            shutil.copy2(src, target / src.name)
        print(f"installed {len(rendered_files)} texture(s) to {target}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("hashes", nargs="*", help="Texture hash ids or prefixes to render")
    ap.add_argument("--jobs", type=Path, default=DEFAULT_JOBS)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--all", action="store_true", help="Render every ready job")
    ap.add_argument("--include-needs-review", action="store_true", help="Also render jobs marked needs_review")
    ap.add_argument("--apply", action="store_true", help="Copy rendered output into kr_textures/ui")
    ap.add_argument("--install", action="store_true", help="Copy rendered output into local Vita3K import folders")
    ap.add_argument("--compare", action="store_true", help="Write original/current/rendered comparison sheets")
    args = ap.parse_args()

    jobs_doc = load_jobs(args.jobs)
    jobs = jobs_doc.get("textures", {})
    selected: list[str] = []
    if args.all:
        selected = sorted(jobs)
    else:
        for prefix in args.hashes:
            matches = [h for h in jobs if h.startswith(prefix)]
            if not matches:
                raise SystemExit(f"no job matches prefix: {prefix}")
            selected.extend(matches)
    selected = sorted(set(selected))
    if not selected:
        raise SystemExit("provide hash prefix(es), or use --all")

    font_path = repo_path(jobs_doc.get("font"), DEFAULT_FONT)
    apply_dir = DEFAULT_APPLY_DIR if args.apply else None
    rendered_files: list[Path] = []
    for hash_id in selected:
        job = jobs[hash_id]
        status = job.get("status", "ready")
        if status == "needs_review" and not args.include_needs_review:
            print(f"SKIP {hash_id}: needs_review")
            continue
        if status == "preserve":
            print(f"SKIP {hash_id}: preserve")
            continue
        rendered = render_job(hash_id, job, args.out_dir, apply_dir, font_path)
        rendered_files.append(rendered)
        msg = f"RENDER {hash_id}: {rendered}"
        if args.compare:
            compare = make_compare(hash_id, rendered, args.out_dir / "_compare")
            msg += f" compare={compare}"
        print(msg)

    if args.install and rendered_files:
        install_to_vita3k(rendered_files)


if __name__ == "__main__":
    main()
