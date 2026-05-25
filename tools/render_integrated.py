"""Render 28 textures with integrated mapping.
Detect regions, sort by game-view top-to-bottom, match to mapping sequentially.
"""
import json
import io
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy import ndimage
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

FONT_PATH = 'fonts/Griun_PolSensibility-Rg.ttf'
SRC_ORIG = Path('textures/place_originals')
SRC_KR = Path('textures/kr/ui')
OUT = Path('temp/render_v4')
OUT.mkdir(parents=True, exist_ok=True)

with open('translations/integrated_mapping.json', encoding='utf-8') as f:
    mapping = json.load(f)


def detect_all_regions(img):
    """Detect red banners, black boxes (with white frame), and white kanji blobs."""
    arr = np.array(img)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

    # 1. Red banners
    red = (r > 120) & (g < 100) & (b < 100) & (a > 128)
    red_lbl, n_red = ndimage.label(red)
    banners = []
    for i in range(1, n_red + 1):
        ys, xs = np.where(red_lbl == i)
        if len(ys) < 5000:
            continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        banners.append({'bbox': [x0, y0, x1, y1], 'area': len(ys)})

    # 2. Black boxes (white frame around solid black)
    black_solid = (r < 60) & (g < 60) & (b < 60) & (a > 200)
    bs_lbl, n_bs = ndimage.label(black_solid)
    boxes = []
    for i in range(1, n_bs + 1):
        ys, xs = np.where(bs_lbl == i)
        if len(ys) < 8000:
            continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        bw, bh = x1 - x0, y1 - y0
        if bw < 80 or bh < 80:
            continue
        bbox_area = bw * bh
        fill = len(ys) / bbox_area
        if fill > 0.45:
            margin = 12
            ox0, oy0 = max(0, x0 - margin), max(0, y0 - margin)
            ox1, oy1 = min(arr.shape[1], x1 + margin), min(arr.shape[0], y1 + margin)
            boxes.append({'bbox': [ox0, oy0, ox1, oy1], 'area': len(ys),
                          'is_brush': fill < 0.5,
                          'fill': fill})

    # 3. White kanji blobs (large white areas not in boxes/banners)
    excl_mask = np.zeros_like(red, dtype=bool)
    for r_ in banners + boxes:
        x0, y0, x1, y1 = r_['bbox']
        excl_mask[y0:y1, x0:x1] = True
    white = (r > 220) & (g > 220) & (b > 220) & (a > 200) & ~excl_mask
    white_d = ndimage.binary_dilation(white, iterations=15)
    w_lbl, n_w = ndimage.label(white_d)
    chars = []
    for i in range(1, n_w + 1):
        ys, xs = np.where(w_lbl == i)
        if len(ys) < 5000:
            continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        bw, bh = x1 - x0, y1 - y0
        if bw < 100 or bh < 100:
            continue
        ar = max(bw, bh) / min(bw, bh)
        if ar > 8:
            continue
        chars.append({'bbox': [x0, y0, x1, y1], 'area': len(ys)})

    return banners, boxes, chars


def sort_game_view_top(regions):
    """Sort by game view top: rightmost x first (since rotate 270 makes right -> top)."""
    return sorted(regions, key=lambda r: (-r['bbox'][2], r['bbox'][1]))


def render_text(base_img, bbox, text, fill, padding=0.08, fr=0.85):
    x0, y0, x1, y1 = bbox
    rw, rh = x1 - x0, y1 - y0
    rotated = rw > rh
    n = max(1, len([c for c in text if c != ' ']))
    if rotated:
        canvas = Image.new('RGBA', (rh, rw), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        pad = int(rw * padding)
        cell = max(1, (rw - 2 * pad) // n)
        fs = int(min(rh, cell) * fr)
        if fs < 8: fs = 8
        font = ImageFont.truetype(FONT_PATH, fs)
        i = 0
        for ch in text:
            if ch == ' ':
                continue
            bb = font.getbbox(ch)
            cw, chh = bb[2] - bb[0], bb[3] - bb[1]
            cx = rh // 2 - (cw // 2 + bb[0])
            cy = pad + i * cell + cell // 2 - (chh // 2 + bb[1])
            d.text((cx, cy), ch, font=font, fill=fill)
            i += 1
        rot = canvas.rotate(90, expand=True)
        if rot.size != (rw, rh):
            rot = rot.resize((rw, rh))
        region = base_img.crop(bbox).convert('RGBA')
        region = Image.alpha_composite(region, rot)
        base_img.paste(region, (x0, y0))
    else:
        d = ImageDraw.Draw(base_img)
        pad = int(rh * padding)
        cell = max(1, (rh - 2 * pad) // n)
        fs = int(min(rw, cell) * fr)
        if fs < 8: fs = 8
        font = ImageFont.truetype(FONT_PATH, fs)
        yt = y0 + pad
        i = 0
        for ch in text:
            if ch == ' ':
                continue
            bb = font.getbbox(ch)
            cw, chh = bb[2] - bb[0], bb[3] - bb[1]
            cx = x0 + rw // 2 - (cw // 2 + bb[0])
            cy = yt + i * cell + cell // 2 - (chh // 2 + bb[1])
            d.text((cx, cy), ch, font=font, fill=fill)
            i += 1


def clear_region(img, bbox, color):
    x0, y0, x1, y1 = bbox
    arr = np.array(img)
    region = arr[y0:y1, x0:x1].copy()
    mask = region[:, :, 3] > 128
    for c, v in enumerate(color[:3]):
        region[:, :, c] = np.where(mask, v, region[:, :, c])
    arr[y0:y1, x0:x1] = region
    return Image.fromarray(arr, 'RGBA')


def kill_white(img, bbox):
    """Make white pixels transparent in bbox (for character glyph removal on brush)."""
    x0, y0, x1, y1 = bbox
    arr = np.array(img)
    region = arr[y0:y1, x0:x1]
    r, g, b, a = region[:, :, 0], region[:, :, 1], region[:, :, 2], region[:, :, 3]
    white_mask = (r > 200) & (g > 200) & (b > 200) & (a > 100)
    region[:, :, 3] = np.where(white_mask, 0, a)
    return Image.fromarray(arr, 'RGBA')


count = 0
for h, regions in mapping.items():
    p = SRC_ORIG / f'{h}.png' if (SRC_ORIG / f'{h}.png').exists() else SRC_KR / f'{h}.png'
    if not p.exists():
        print(f'NO SOURCE: {h}')
        continue
    img = Image.open(p).convert('RGBA')
    detected_banners, detected_boxes, detected_chars = detect_all_regions(img)
    db_sorted = sort_game_view_top(detected_banners)
    dk_sorted = sort_game_view_top(detected_boxes)
    dc_sorted = sort_game_view_top(detected_chars)

    # Map regions by kind
    map_banners = [r for r in regions if r['kind'] == 'banner']
    map_boxes = [r for r in regions if r['kind'] == 'box']
    map_chars = [r for r in regions if r['kind'] == 'character']

    # Clear all detected regions first
    for b in detected_banners:
        img = clear_region(img, tuple(b['bbox']), (204, 66, 58, 255))
    for b in detected_boxes:
        # Box may be brush (no frame) - clear black
        img = clear_region(img, tuple(b['bbox']), (0, 0, 0, 255))
    for c in detected_chars:
        # Kill white glyphs but preserve brush stroke underneath if any
        img = kill_white(img, tuple(c['bbox']))

    # Render banners (sequential pairing)
    for i, mb in enumerate(map_banners):
        if i >= len(db_sorted):
            break
        bbox = tuple(db_sorted[i]['bbox'])
        render_text(img, bbox, mb['ko'], (0, 0, 0, 255), padding=0.08, fr=0.80)

    # Render boxes
    for i, mb in enumerate(map_boxes):
        if i >= len(dk_sorted):
            break
        bbox = tuple(dk_sorted[i]['bbox'])
        render_text(img, bbox, mb['ko'], (255, 255, 255, 255), padding=0.12, fr=0.92)

    # Render characters
    for i, mc in enumerate(map_chars):
        if i >= len(dc_sorted):
            break
        bbox = tuple(dc_sorted[i]['bbox'])
        render_text(img, bbox, mc['ko'], (255, 255, 255, 255), padding=0.10, fr=0.85)

    img.save(OUT / f'{h}.png')
    count += 1
    print(f'{h}: B={len(db_sorted)}/{len(map_banners)} K={len(dk_sorted)}/{len(map_boxes)} C={len(dc_sorted)}/{len(map_chars)}')

print(f'\nRendered {count} textures to {OUT}')
