"""V5 renderer with improved detection:
1. Real box: solid black + WHITE FRAME around (frame check via outer pixels)
2. Brush stroke: solid black WITHOUT frame
3. Character region: brush + nearby large white kanji (merged)
4. Banner: red rectangles
5. Sequential mapping with proper game-view ordering
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
SRC_ORIG = Path('textures/place_name_originals')
SRC_KR = Path('kr_textures/ui')
OUT = Path('temp/render_v5')
OUT.mkdir(parents=True, exist_ok=True)

with open('translations/integrated_mapping.json', encoding='utf-8') as f:
    mapping = json.load(f)


def frame_score(arr, bbox, frame_width=10):
    """Return frame strength as ratio of white pixels in outer ring (0..1)."""
    x0, y0, x1, y1 = bbox
    H, W = arr.shape[:2]
    fx0, fy0 = max(0, x0 - frame_width), max(0, y0 - frame_width)
    fx1, fy1 = min(W, x1 + frame_width), min(H, y1 + frame_width)
    borders = []
    borders.append(arr[fy0:fy0 + frame_width, fx0:fx1])
    borders.append(arr[fy1 - frame_width:fy1, fx0:fx1])
    borders.append(arr[fy0:fy1, fx0:fx0 + frame_width])
    borders.append(arr[fy0:fy1, fx1 - frame_width:fx1])
    total_white = 0
    total_pixels = 0
    for b in borders:
        if b.size == 0: continue
        r, g, b_ch, a = b[:, :, 0], b[:, :, 1], b[:, :, 2], b[:, :, 3]
        white = (r > 220) & (g > 220) & (b_ch > 220) & (a > 180)
        total_white += white.sum()
        total_pixels += white.size
    if total_pixels == 0: return 0.0
    return total_white / total_pixels


def has_white_frame(arr, bbox):
    return frame_score(arr, bbox) > 0.05


def detect_all_regions(img):
    """Returns banners (red), real_boxes (frame+black), characters (brush + nearby white kanji)."""
    arr = np.array(img)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

    # 1. Red banners
    red = (r > 120) & (g < 100) & (b < 100) & (a > 128)
    red_lbl, n_red = ndimage.label(red)
    banners = []
    for i in range(1, n_red + 1):
        ys, xs = np.where(red_lbl == i)
        if len(ys) < 5000: continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        banners.append({'bbox': [x0, y0, x1, y1], 'area': len(ys),
                        'cx': (x0 + x1) // 2, 'cy': (y0 + y1) // 2})

    # 2. All solid-black blobs (candidates for real box OR brush stroke)
    black_solid = (r < 60) & (g < 60) & (b < 60) & (a > 200)
    bs_lbl, n_bs = ndimage.label(black_solid)
    real_boxes = []
    brushes = []
    for i in range(1, n_bs + 1):
        ys, xs = np.where(bs_lbl == i)
        if len(ys) < 8000: continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        bw, bh = x1 - x0, y1 - y0
        if bw < 80 or bh < 80: continue
        bbox_area = bw * bh
        fill = len(ys) / bbox_area
        # Real box: rectangular shape (fill >= 0.7) and has white frame
        # Add small margin for outer bbox
        margin = 12
        ox0, oy0 = max(0, x0 - margin), max(0, y0 - margin)
        ox1, oy1 = min(arr.shape[1], x1 + margin), min(arr.shape[0], y1 + margin)
        outer_bbox = [ox0, oy0, ox1, oy1]
        fs = frame_score(arr, [x0, y0, x1, y1])
        ar = max(bw, bh) / min(bw, bh)
        # Real box: must have visible white frame and reasonable shape
        is_box = fs >= 0.10 and ar < 3.0 and fill >= 0.55
        if is_box:
            real_boxes.append({'bbox': outer_bbox, 'inner': [x0, y0, x1, y1],
                               'area': len(ys), 'fill': fill, 'frame_score': fs,
                               'cx': (x0 + x1) // 2, 'cy': (y0 + y1) // 2})
        else:
            brushes.append({'bbox': [x0, y0, x1, y1], 'area': len(ys), 'fill': fill,
                            'frame_score': fs,
                            'cx': (x0 + x1) // 2, 'cy': (y0 + y1) // 2})

    # 3. White kanji blobs (large white outside any box/banner)
    excl = np.zeros_like(red, dtype=bool)
    for r_ in banners + real_boxes:
        x0, y0, x1, y1 = r_['bbox']
        excl[y0:y1, x0:x1] = True
    # IMPORTANT: do NOT exclude inside boxes for white kanji of inside-box text;
    # but the box has its own white kanji that would map to box text not character
    white = (r > 220) & (g > 220) & (b > 220) & (a > 200) & ~excl
    white_d = ndimage.binary_dilation(white, iterations=15)
    w_lbl, n_w = ndimage.label(white_d)
    white_blobs = []
    for i in range(1, n_w + 1):
        ys, xs = np.where(w_lbl == i)
        if len(ys) < 5000: continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        bw, bh = x1 - x0, y1 - y0
        if bw < 100 or bh < 100: continue
        ar = max(bw, bh) / min(bw, bh)
        if ar > 8: continue
        white_blobs.append({'bbox': [x0, y0, x1, y1], 'area': len(ys),
                            'cx': (x0 + x1) // 2, 'cy': (y0 + y1) // 2})

    # 4. Merge brush strokes with nearby white kanji blobs => characters
    # If a brush is close to a white blob (overlap or center distance < threshold), merge
    characters = []
    used_whites = set()
    for br in brushes:
        bx0, by0, bx1, by1 = br['bbox']
        # Find white blob that overlaps or is adjacent to brush
        merged_bbox = [bx0, by0, bx1, by1]
        merged_with = []
        for j, w in enumerate(white_blobs):
            if j in used_whites: continue
            wx0, wy0, wx1, wy1 = w['bbox']
            # Adjacent: bboxes overlap by at least 50px in either x or y
            x_overlap = max(0, min(bx1, wx1) - max(bx0, wx0))
            y_overlap = max(0, min(by1, wy1) - max(by0, wy0))
            # Or close: centers within 200px
            cx_dist = abs(br['cx'] - w['cx'])
            cy_dist = abs(br['cy'] - w['cy'])
            if x_overlap > 30 or y_overlap > 30 or (cx_dist < 250 and cy_dist < 250):
                merged_bbox[0] = min(merged_bbox[0], wx0)
                merged_bbox[1] = min(merged_bbox[1], wy0)
                merged_bbox[2] = max(merged_bbox[2], wx1)
                merged_bbox[3] = max(merged_bbox[3], wy1)
                merged_with.append(j)
        for j in merged_with: used_whites.add(j)
        characters.append({'bbox': merged_bbox, 'brush_area': br['area'],
                           'cx': (merged_bbox[0] + merged_bbox[2]) // 2,
                           'cy': (merged_bbox[1] + merged_bbox[3]) // 2})

    # Add isolated white blobs not merged with brush as standalone characters
    for j, w in enumerate(white_blobs):
        if j in used_whites: continue
        characters.append({'bbox': w['bbox'], 'brush_area': 0,
                           'cx': w['cx'], 'cy': w['cy']})

    return banners, real_boxes, characters


def sort_game_view_top(regions):
    """In game view (image rotated 270 CCW), the rightmost x in original = top.
    Sort by x_right desc (right first), then y asc."""
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
        fs = max(8, int(min(rh, cell) * fr))
        font = ImageFont.truetype(FONT_PATH, fs)
        i = 0
        for ch in text:
            if ch == ' ': continue
            bb = font.getbbox(ch)
            cw, chh = bb[2] - bb[0], bb[3] - bb[1]
            cx = rh // 2 - (cw // 2 + bb[0])
            cy = pad + i * cell + cell // 2 - (chh // 2 + bb[1])
            d.text((cx, cy), ch, font=font, fill=fill)
            i += 1
        rot = canvas.rotate(90, expand=True)
        if rot.size != (rw, rh): rot = rot.resize((rw, rh))
        region = base_img.crop(bbox).convert('RGBA')
        region = Image.alpha_composite(region, rot)
        base_img.paste(region, (x0, y0))
    else:
        d = ImageDraw.Draw(base_img)
        pad = int(rh * padding)
        cell = max(1, (rh - 2 * pad) // n)
        fs = max(8, int(min(rw, cell) * fr))
        font = ImageFont.truetype(FONT_PATH, fs)
        yt = y0 + pad
        i = 0
        for ch in text:
            if ch == ' ': continue
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


def kill_white_in_bbox(img, bbox):
    """Remove white character glyphs (set their alpha to 0) within bbox."""
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
        print(f'NO SOURCE: {h}'); continue
    img = Image.open(p).convert('RGBA')
    detected_banners, detected_boxes, detected_chars = detect_all_regions(img)
    db_sorted = sort_game_view_top(detected_banners)
    dk_sorted = sort_game_view_top(detected_boxes)
    dc_sorted = sort_game_view_top(detected_chars)

    map_banners = [r for r in regions if r['kind'] == 'banner']
    map_boxes = [r for r in regions if r['kind'] == 'box']
    map_chars = [r for r in regions if r['kind'] == 'character']

    # CLEAR all detected regions FIRST
    for b in detected_banners:
        img = clear_region(img, tuple(b['bbox']), (204, 66, 58, 255))
    for b in detected_boxes:
        img = clear_region(img, tuple(b['bbox']), (0, 0, 0, 255))
    for c in detected_chars:
        # Kill white glyphs within character bbox
        img = kill_white_in_bbox(img, tuple(c['bbox']))

    # RENDER banners
    for i, mb in enumerate(map_banners):
        if i >= len(db_sorted): break
        bbox = tuple(db_sorted[i]['bbox'])
        render_text(img, bbox, mb['ko'], (0, 0, 0, 255), padding=0.08, fr=0.80)

    # RENDER real boxes (white text, no rotation since already upright)
    for i, mb in enumerate(map_boxes):
        if i >= len(dk_sorted): break
        bbox = tuple(dk_sorted[i]['bbox'])
        render_text(img, bbox, mb['ko'], (255, 255, 255, 255), padding=0.12, fr=0.92)

    # RENDER characters (white text, on top of brush stroke)
    for i, mc in enumerate(map_chars):
        if i >= len(dc_sorted): break
        bbox = tuple(dc_sorted[i]['bbox'])
        render_text(img, bbox, mc['ko'], (255, 255, 255, 255), padding=0.10, fr=0.85)

    img.save(OUT / f'{h}.png')
    count += 1
    print(f'{h}: B={len(db_sorted)}/{len(map_banners)} K={len(dk_sorted)}/{len(map_boxes)} C={len(dc_sorted)}/{len(map_chars)}')

print(f'\nv5 rendered {count} textures')
