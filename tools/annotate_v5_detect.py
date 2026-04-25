"""Annotate all 28 textures with v5 detect results (banner B, box K, character C indices)
to enable manual mapping correction.
"""
import json
import io
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from scipy import ndimage
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import detect functions from render_v5
sys.path.insert(0, 'tools')
from render_v5 import detect_all_regions, sort_game_view_top

problems_28 = ["00B61B564A5FD289","0AA74C448087838A","3ECF3B0D2C2907BE","7E0669E71FCD7B64",
    "464E370EF865D0AC","864BD9CBCC496F78","0912E45A567A41C9","4633B92FBA1371F4",
    "4709F3E364671D89","5882EA68BABF3C63","6605F569D9389F9C","7053B8FFC8B89807",
    "7282AD29CF433DA0","7358BEAA2EF5F8A8","8098AD7E2C438C22","31710FB73B2686EF",
    "72165D43344F3190","615858B46587A60E","2611666E71A8181A","A8486C49F76167C3",
    "C8B2975F2A629F4B","C8C4589102431759","C8E42A56480DB818","C84B5B3A51547DF0",
    "C3848C8E5ED70F7A","E9E834DE4BAFDAB2","E9F2EC8557984A58","FFC64B053648525E"]

src_orig = Path('textures/place_name_originals')
src_kr = Path('kr_textures/ui')
out_dir = Path('temp/preview/annotated_v5')
out_dir.mkdir(parents=True, exist_ok=True)

font = ImageFont.truetype('arial.ttf', 50)
font_small = ImageFont.truetype('arial.ttf', 30)

# Save detect results for use in mapping
detect_results = {}

for h in problems_28:
    p = src_orig / f'{h}.png' if (src_orig / f'{h}.png').exists() else src_kr / f'{h}.png'
    img = Image.open(p).convert('RGBA')
    banners, boxes, chars = detect_all_regions(img)
    bs = sort_game_view_top(banners)
    ks = sort_game_view_top(boxes)
    cs = sort_game_view_top(chars)

    detect_results[h] = {
        'banners': [{'idx': i, 'bbox': b['bbox']} for i, b in enumerate(bs)],
        'boxes': [{'idx': i, 'bbox': b['bbox']} for i, b in enumerate(ks)],
        'characters': [{'idx': i, 'bbox': b['bbox']} for i, b in enumerate(cs)],
    }

    bg = Image.new('RGB', img.size, (30, 30, 30))
    bg.paste(img, mask=img.split()[3])
    d = ImageDraw.Draw(bg)
    for i, b in enumerate(bs):
        x0, y0, x1, y1 = b['bbox']
        d.rectangle([x0, y0, x1, y1], outline=(0, 255, 255), width=5)
        d.text((x0 + 10, y0 + 10), f'B{i}', fill=(0, 255, 255), font=font)
    for i, b in enumerate(ks):
        x0, y0, x1, y1 = b['bbox']
        d.rectangle([x0, y0, x1, y1], outline=(255, 255, 0), width=5)
        d.text((x0 + 10, y0 + 10), f'K{i}', fill=(255, 255, 0), font=font)
    for i, b in enumerate(cs):
        x0, y0, x1, y1 = b['bbox']
        d.rectangle([x0, y0, x1, y1], outline=(255, 100, 200), width=4)
        d.text((x0 + 10, y0 + 10), f'C{i}', fill=(255, 100, 200), font=font)
    rot = bg.rotate(270, expand=True)
    rot.thumbnail((1300, 1300), Image.LANCZOS)
    rot.save(out_dir / f'{h}.png')
    print(f'{h}: B={len(bs)} K={len(ks)} C={len(cs)}')

with open('translations/detect_v5.json', 'w', encoding='utf-8') as f:
    json.dump(detect_results, f, ensure_ascii=False, indent=2)
print(f'\nSaved detect results for {len(problems_28)} textures')
