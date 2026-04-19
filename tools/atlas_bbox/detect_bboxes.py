"""Auto-detect label bboxes in a text atlas via alpha connected components.

Strategy:
- Binarize alpha > threshold
- Horizontal dilate to connect letters within a label
- Run connected-components, discard tiny noise
- Group components into rows (by y midpoint)
- Sort each row left-to-right, write a JSON draft
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

def detect(src_png: Path, out_json: Path, overlay_png: Path,
           alpha_thr=40, h_dilate=5, v_dilate=1, min_area=30):
    img = Image.open(src_png).convert('RGBA')
    W, H = img.size
    a = np.array(img)[:, :, 3]
    mask = (a > alpha_thr).astype(np.uint8)
    # Horizontal dilation so letters of one label merge
    kernel = np.ones((1 + 2*v_dilate, 1 + 2*h_dilate), dtype=np.uint8)
    from scipy.ndimage import binary_dilation
    dil = binary_dilation(mask, structure=kernel).astype(np.uint8)
    lbl, n = ndimage.label(dil)
    boxes = []
    for i in range(1, n+1):
        ys, xs = np.where(lbl == i)
        if len(xs) < min_area:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        w, h = x1-x0+1, y1-y0+1
        if w < 8 or h < 6:
            continue
        boxes.append({'x': x0, 'y': y0, 'w': w, 'h': h})

    # Group by row: sort by y0, cluster with tolerance
    boxes.sort(key=lambda b: (b['y'] + b['h']/2))
    rows = []
    for b in boxes:
        cy = b['y'] + b['h']/2
        placed = False
        for row in rows:
            ry = sum((r['y']+r['h']/2) for r in row)/len(row)
            avg_h = sum(r['h'] for r in row)/len(row)
            if abs(cy - ry) < avg_h*0.6:
                row.append(b); placed = True; break
        if not placed:
            rows.append([b])
    for row in rows:
        row.sort(key=lambda b: b['x'])

    # Flatten with row index
    labels = []
    for ri, row in enumerate(rows):
        for ci, b in enumerate(row):
            labels.append({
                'row': ri, 'col': ci,
                'x': b['x'], 'y': b['y'], 'w': b['w'], 'h': b['h'],
                'en': '', 'ko': ''
            })

    out = {
        'image': str(src_png.name),
        'src_size': [W, H],
        'labels': labels,
    }
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    # Overlay preview
    bg = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    comp = Image.alpha_composite(bg, img).convert('RGB')
    draw = ImageDraw.Draw(comp)
    for i, lab in enumerate(labels):
        x, y, w, h = lab['x'], lab['y'], lab['w'], lab['h']
        draw.rectangle([x, y, x+w-1, y+h-1], outline=(255, 255, 0), width=1)
        draw.text((x+1, y+1), str(i), fill=(255, 80, 80))
    comp.resize((W*4, H*4), Image.NEAREST).save(overlay_png)

    print(f'{src_png.name}: {len(labels)} boxes in {len(rows)} rows -> {out_json.name}')

if __name__ == '__main__':
    for h in ['7DC6CF5A87DB1312','E8E01EAF5D41DB52']:
        detect(
            Path(f'textures/originals/{h}.png'),
            Path(f'tools/atlas_bbox/{h}.json'),
            Path(f'temp/preview/{h}_bboxes.png'),
        )
