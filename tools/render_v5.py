"""V5 renderer with improved detection."""
import json
import io
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy import ndimage

FONT_PATH = 'fonts/Griun_PolSensibility-Rg.ttf'
SRC_ORIG = Path('textures/place_originals')
SRC_KR = Path('textures/kr/ui')
OUT = Path('temp/render_v5')


def frame_score(arr, bbox, frame_width=10):
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
        r, g, bch, a = b[:, :, 0], b[:, :, 1], b[:, :, 2], b[:, :, 3]
        white = (r > 220) & (g > 220) & (bch > 220) & (a > 180)
        total_white += white.sum()
        total_pixels += white.size
    if total_pixels == 0: return 0.0
    return total_white / total_pixels


def detect_all_regions(img):
    arr = np.array(img)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

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
        margin = 12
        ox0, oy0 = max(0, x0 - margin), max(0, y0 - margin)
        ox1, oy1 = min(arr.shape[1], x1 + margin), min(arr.shape[0], y1 + margin)
        outer_bbox = [ox0, oy0, ox1, oy1]
        fs = frame_score(arr, [x0, y0, x1, y1])
        ar = max(bw, bh) / min(bw, bh)
        is_box = fs >= 0.10 and ar < 3.0 and fill >= 0.55
        if is_box:
            real_boxes.append({'bbox': outer_bbox, 'inner': [x0, y0, x1, y1],
                               'area': len(ys), 'fill': fill, 'frame_score': fs,
                               'cx': (x0 + x1) // 2, 'cy': (y0 + y1) // 2})
        else:
            brushes.append({'bbox': [x0, y0, x1, y1], 'area': len(ys), 'fill': fill,
                            'frame_score': fs,
                            'cx': (x0 + x1) // 2, 'cy': (y0 + y1) // 2})

    excl = np.zeros_like(red, dtype=bool)
    for r_ in banners + real_boxes:
        x0, y0, x1, y1 = r_['bbox']
        excl[y0:y1, x0:x1] = True
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

    characters = []
    used_whites = set()
    for br in brushes:
        bx0, by0, bx1, by1 = br['bbox']
        merged_bbox = [bx0, by0, bx1, by1]
        merged_with = []
        for j, w in enumerate(white_blobs):
            if j in used_whites: continue
            wx0, wy0, wx1, wy1 = w['bbox']
            x_overlap = max(0, min(bx1, wx1) - max(bx0, wx0))
            y_overlap = max(0, min(by1, wy1) - max(by0, wy0))
            cx_dist = abs(br['cx'] - w['cx'])
            cy_dist = abs(br['cy'] - w['cy'])
            if x_overlap > 30 or y_overlap > 30 or (cx_dist < 250 and cy_dist < 250):
                merged_bbox[0] = min(merged_bbox[0], wx0)
                merged_bbox[1] = min(merged_bbox[1], wy0)
                merged_bbox[2] = max(merged_bbox[2], wx1)
                merged_bbox[3] = max(merged_bbox[3], wy1)
                merged_with.append(j)
        for j in merged_with: used_whites.add(j)
        if merged_with:
            characters.append({'bbox': merged_bbox, 'brush_area': br['area'],
                               'cx': (merged_bbox[0] + merged_bbox[2]) // 2,
                               'cy': (merged_bbox[1] + merged_bbox[3]) // 2})

    for j, w in enumerate(white_blobs):
        if j in used_whites: continue
        characters.append({'bbox': w['bbox'], 'brush_area': 0,
                           'cx': w['cx'], 'cy': w['cy']})

    return banners, real_boxes, characters


def sort_game_view_top(regions):
    return sorted(regions, key=lambda r: (-r['bbox'][2], r['bbox'][1]))


def sort_by_area_desc(regions):
    return sorted(regions, key=lambda r: -r.get('area', 0))


def sort_by_brush_area_desc(regions):
    return sorted(regions, key=lambda r: -(r.get('brush_area', 0)))


def sort_boxes_best_first(regions):
    """Real boxes first: high frame_score, high fill, then area."""
    return sorted(regions, key=lambda r: (-r.get('frame_score', 0), -r.get('fill', 0), -r.get('area', 0)))


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
    x0, y0, x1, y1 = bbox
    arr = np.array(img)
    region = arr[y0:y1, x0:x1]
    r, g, b, a = region[:, :, 0], region[:, :, 1], region[:, :, 2], region[:, :, 3]
    white_mask = (r > 200) & (g > 200) & (b > 200) & (a > 100)
    region[:, :, 3] = np.where(white_mask, 0, a)
    return Image.fromarray(arr, 'RGBA')


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    OUT.mkdir(parents=True, exist_ok=True)
    with open('translations/integrated_mapping.json', encoding='utf-8') as f:
        mapping = json.load(f)
    # Optional: load manual mapping that overrides bbox indices
    manual_path = Path('translations/manual_bbox_mapping.json')
    manual = {}
    if manual_path.exists():
        with open(manual_path, encoding='utf-8') as f:
            manual = json.load(f)
    count = 0
    for h, regions in mapping.items():
        p = SRC_ORIG / f'{h}.png' if (SRC_ORIG / f'{h}.png').exists() else SRC_KR / f'{h}.png'
        if not p.exists():
            print(f'NO SOURCE: {h}')
            continue
        img = Image.open(p).convert('RGBA')
        detected_banners, detected_boxes, detected_chars = detect_all_regions(img)
        db_sorted = sort_game_view_top(detected_banners)
        # Boxes: prefer high frame_score (real boxes), then by area
        # When mapping has multiple boxes, sort by game-view top among the top-rated ones
        dk_best = sort_boxes_best_first(detected_boxes)
        # If mapping has multiple boxes, take top-N best, then re-sort by game-view top
        map_boxes_count = sum(1 for r in regions if r['kind'] == 'box')
        if map_boxes_count > 1 and len(dk_best) >= map_boxes_count:
            dk_sorted = sort_game_view_top(dk_best[:map_boxes_count])
        else:
            dk_sorted = dk_best
        dc_sorted = sort_by_brush_area_desc(detected_chars) if any(c.get('brush_area', 0) > 0 for c in detected_chars) else sort_by_area_desc(detected_chars)

        map_banners = [r for r in regions if r['kind'] == 'banner']
        map_boxes = [r for r in regions if r['kind'] == 'box']
        map_chars = [r for r in regions if r['kind'] == 'character']

        for b in detected_banners:
            img = clear_region(img, tuple(b['bbox']), (204, 66, 58, 255))
        for b in detected_boxes:
            img = clear_region(img, tuple(b['bbox']), (0, 0, 0, 255))
        for c in detected_chars:
            img = kill_white_in_bbox(img, tuple(c['bbox']))

        # Get manual override for this hash
        m_h = manual.get(h, {})
        manual_banners_idx = m_h.get('banner_idx')  # list of detect indices
        manual_banner_bbox = m_h.get('banner_bbox')
        manual_boxes_idx = m_h.get('box_idx')
        manual_chars_idx = m_h.get('char_idx')
        manual_box_bbox = m_h.get('box_bbox')  # explicit bboxes for boxes
        manual_char_bbox = m_h.get('char_bbox')

        # Render banners (background)
        for i, mb in enumerate(map_banners):
            if manual_banner_bbox is not None and i < len(manual_banner_bbox):
                bbox = tuple(manual_banner_bbox[i])
                img = clear_region(img, bbox, (204, 66, 58, 255))
            elif manual_banners_idx is not None and i < len(manual_banners_idx):
                idx = manual_banners_idx[i]
                if idx is None or idx >= len(db_sorted): continue
                bbox = tuple(db_sorted[idx]['bbox'])
            else:
                if i >= len(db_sorted): break
                bbox = tuple(db_sorted[i]['bbox'])
            render_text(img, bbox, mb['ko'], (0, 0, 0, 255), padding=0.08, fr=0.80)

        # Render characters FIRST (on brush stroke) - so boxes can overwrite if overlap
        rendered_box_bboxes = []
        for i, mb in enumerate(map_boxes):
            if manual_box_bbox is not None and i < len(manual_box_bbox):
                bbox = tuple(manual_box_bbox[i])
            elif manual_boxes_idx is not None and i < len(manual_boxes_idx):
                idx = manual_boxes_idx[i]
                if idx is None or idx >= len(dk_sorted): continue
                bbox = tuple(dk_sorted[idx]['bbox'])
            else:
                if i >= len(dk_sorted): break
                bbox = tuple(dk_sorted[i]['bbox'])
            rendered_box_bboxes.append(bbox)

        # Render characters first, but skip if their bbox overlaps with any box bbox
        def overlaps_any_box(cbb, boxes_list, threshold=0.3):
            cx0, cy0, cx1, cy1 = cbb
            for bb in boxes_list:
                bx0, by0, bx1, by1 = bb
                ox = max(0, min(cx1, bx1) - max(cx0, bx0))
                oy = max(0, min(cy1, by1) - max(cy0, by0))
                ov = ox * oy
                cba = (cx1 - cx0) * (cy1 - cy0)
                if cba and ov / cba > threshold:
                    return True
            return False

        for i, mc in enumerate(map_chars):
            if manual_char_bbox is not None and i < len(manual_char_bbox):
                bbox = tuple(manual_char_bbox[i])
            elif manual_chars_idx is not None and i < len(manual_chars_idx):
                idx = manual_chars_idx[i]
                if idx is None or idx >= len(dc_sorted): continue
                bbox = tuple(dc_sorted[idx]['bbox'])
            else:
                if i >= len(dc_sorted): break
                bbox = tuple(dc_sorted[i]['bbox'])
            # Skip character if it overlaps with a box bbox (avoid covering box text)
            if overlaps_any_box(bbox, rendered_box_bboxes):
                # Try next un-overlapping detect char
                fallback = None
                for j in range(i + 1, len(dc_sorted)):
                    cand = tuple(dc_sorted[j]['bbox'])
                    if not overlaps_any_box(cand, rendered_box_bboxes):
                        fallback = cand; break
                if fallback is not None:
                    bbox = fallback
                else:
                    continue
            render_text(img, bbox, mc['ko'], (255, 255, 255, 255), padding=0.10, fr=0.85)

        # Render boxes LAST so they take priority
        for bbox, mb in zip(rendered_box_bboxes, map_boxes):
            # If manual_box_bbox path was used, ensure we cleared first
            if manual_box_bbox is not None:
                img = clear_region(img, bbox, (0, 0, 0, 255))
            render_text(img, bbox, mb['ko'], (255, 255, 255, 255), padding=0.12, fr=0.92)

        img.save(OUT / f'{h}.png')
        count += 1
        print(f'{h}: B={len(db_sorted)}/{len(map_banners)} K={len(dk_sorted)}/{len(map_boxes)} C={len(dc_sorted)}/{len(map_chars)}')
    print(f'\nv5 rendered {count} textures')


if __name__ == '__main__':
    main()
