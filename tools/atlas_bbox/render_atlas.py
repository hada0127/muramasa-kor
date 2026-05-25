"""Render Korean labels onto an atlas texture.

- Starts from the original 512x512 PNG (preserves paper/cloth non-text regions)
- For each label entry: clears its alpha bbox, then renders Korean text
  fit to bbox (including outline) at maximum size
- Outputs at output_size (default 4x = 2048x2048) using Lanczos for base + crisp native-res text rendering
"""
import json
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = Path("fonts/Griun_PolSensibility-Rg.ttf")


def fit_font_size(text: str, font_path: Path, bbox_w: int, bbox_h: int,
                  outline: int, max_size: int = 400):
    """Find the largest font size where (text + outline) fits within bbox_w x bbox_h."""
    lo, hi = 6, max_size
    best = lo
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            font = ImageFont.truetype(str(font_path), mid)
        except Exception:
            hi = mid - 1
            continue
        # measure with getbbox which accounts for ascender/descender
        bb = font.getbbox(text)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        # include outline expansion on both sides
        total_w = tw + outline * 2
        total_h = th + outline * 2
        if total_w <= bbox_w and total_h <= bbox_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def draw_text_with_outline(draw: ImageDraw.ImageDraw, pos, text, font,
                            fill=(255, 255, 255, 255),
                            outline_color=(0, 0, 0, 255),
                            outline: int = 2):
    x, y = pos
    # Multi-pass offset outline for thickness
    for dx in range(-outline, outline + 1):
        for dy in range(-outline, outline + 1):
            if dx == 0 and dy == 0:
                continue
            if dx * dx + dy * dy > outline * outline + 1:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill)


def render_label(base: Image.Image, lab: dict, scale: float, outline: int):
    """Render one label onto base image (already upscaled)."""
    x = lab["x"] * scale
    y = lab["y"] * scale
    w = lab["w"] * scale
    h = lab["h"] * scale
    rot = lab.get("rot", 0)
    text = lab["ko"]
    if not text:
        return

    # Work dimensions for rotated text: render horizontally into a layer sized
    # to (h, w) for rot=90 (label's long axis becomes horizontal during fit),
    # then rotate before pasting.
    if rot == 90:
        fit_w, fit_h = int(h), int(w)
    else:
        fit_w, fit_h = int(w), int(h)

    # Find max font size that fits (including outline)
    fs = fit_font_size(text, FONT_PATH, fit_w, fit_h, outline)
    font = ImageFont.truetype(str(FONT_PATH), fs)

    # Render text centered on a transparent layer of fit dimensions
    layer = Image.new("RGBA", (fit_w, fit_h), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(layer)
    bb = font.getbbox(text)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    tx = (fit_w - tw) // 2 - bb[0]
    ty = (fit_h - th) // 2 - bb[1]
    draw_text_with_outline(ldraw, (tx, ty), text, font,
                           outline=outline)

    if rot == 90:
        # rot=90 means read bottom-to-top; rotate +90 CCW so left edge of
        # horizontal text becomes bottom of vertical strip
        layer = layer.rotate(90, expand=True)  # PIL rotate is CCW
        # Now layer is (w, h) matching label bbox

    # Clear bbox alpha on base (so we replace existing English text)
    clear_box = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    base.paste(clear_box, (int(x), int(y)))
    # Paste new text layer
    base.alpha_composite(layer, dest=(int(x), int(y)))


def render_atlas(catalog_path: Path, src_png: Path, out_png: Path):
    cat = json.loads(catalog_path.read_text(encoding="utf-8"))
    src = Image.open(src_png).convert("RGBA")
    src_w, src_h = cat["src_size"]
    out_w, out_h = cat.get("output_size", [src_w * 4, src_h * 4])
    scale = out_w / src_w
    # Upscale base
    base = src.resize((out_w, out_h), Image.LANCZOS)
    # Outline thickness in output pixels: thin to match original brush style
    outline = cat.get("outline", 2)

    for lab in cat["labels"]:
        render_label(base, lab, scale, outline)

    base.save(out_png)
    print(f"wrote {out_png} ({out_w}x{out_h})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hash", help="texture hash (matches JSON and PNG name)")
    ap.add_argument("--catalog-dir", default="tools/atlas_bbox")
    ap.add_argument("--src-dir", default="textures/originals")
    ap.add_argument("--out-dir", default="textures/kr/ui")
    args = ap.parse_args()

    cat_path = Path(args.catalog_dir) / f"{args.hash}.json"
    src_png = Path(args.src_dir) / f"{args.hash}.png"
    out_png = Path(args.out_dir) / f"{args.hash}.png"
    render_atlas(cat_path, src_png, out_png)


if __name__ == "__main__":
    main()
