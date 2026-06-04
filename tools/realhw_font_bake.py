#!/usr/bin/env python3
"""
실기 한글 폰트 베이크 (Phase 4) — 한글 글리프를 base 폰트 FTX 페이지에 직접 베이크.

Vita3K는 폰트 텍스처를 hash PNG import로 대체하지만 실기엔 그 기능이 없으므로,
base 폰트 FTX(other/font*.ftx)의 SJIS 한자 페이지(河/重/隼)에 한글 글리프를 그려넣는다.

US판이 실제로 로드하는 폰트 = NinPri/_US/other/font*.ftx (NinPriPatch엔 _US/other/font가 없어
override 안 됨). 이 페이지들의 high32가 우리가 Vita3K에서 한글화한 6개 폰트 해시와 정확히 일치 →
같은 6개 페이지에 동일 글리프를 베이크(= Vita3K 패치와 1:1 parity).

글리프 드로잉은 auto_font_import.create_korean_import 재사용(1024², cs=32, 河/重/隼 page_base).

함수:
    bake_font_ftx(ftx_bytes) → (new_bytes, log)  # 한 폰트 FTX의 한글 페이지 베이크
    bake_all_fonts(src_dir, out_dir)             # NinPri/_US/other/font*.ftx 일괄

CLI:
    python3 tools/realhw_font_bake.py --verify   # 1페이지 베이크 후 재디코드 미리보기
"""

import sys
import os
import glob
import tempfile
import argparse
import numpy as np
import xxhash
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import ftx_encode as fe
import auto_font_import as af

MAPPING = os.path.join(ROOT, 'translations', 'kr_sjis_mapping.json')
KR_FONT = os.path.join(ROOT, 'fonts', 'RIDIBatang.otf')

# 우리가 한글화한 6개 폰트 페이지 (full hash → page_base). high32로 base 페이지 식별.
KNOWN_FONT_PAGES = {
    '8665CE082D339B33': 1644,  # 河 (본문)
    'A8E6FDD162258699': 1644,  # 河 메뉴(Griun, 외곽선 없음)
    '18747565A804E292': 1644,  # 河 (손글씨 font2b)
    '6706A53E1D94C16E': 1644,  # 河 (HD/ASCII 페이지)
    'E690E190AA5C798F': 2668,  # 重
    '5F01AD869403D330': 3692,  # 隼
}
KNOWN_HIGH32 = {h[:8]: (h, pb) for h, pb in KNOWN_FONT_PAGES.items()}

# US판이 로드하는 폰트 FTX (NinPriPatch는 _US/other/font 없음 → NinPri 사용)
FONT_FTX_RELS = [
    '_US/other/font.ftx',
    '_US/other/font2a.ftx',
    '_US/other/font2b.ftx',
]


def bake_font_ftx(ftx_bytes):
    """한 폰트 FTX의 한글 대상 페이지(high32가 KNOWN인 것)에 한글 글리프 베이크."""
    data = ftx_bytes
    entries = fe.parse_all_gxt(data)
    log = []
    tmp = tempfile.mkdtemp(prefix='fontbake_')
    for e in entries:
        if e['fmt'] not in (fe.DXT5, fe.DXT3):
            continue
        w, h = e['width'], e['height']
        bw, bh = w // 4, h // 4
        base = bw * bh * 16
        pay = data[e['abs_off']:e['abs_off'] + base]
        if len(pay) < base:
            continue
        hi = ('%016X' % xxhash.xxh3_64(pay).intdigest())[:8]
        if hi not in KNOWN_HIGH32:
            continue
        full_hash, page_base = KNOWN_HIGH32[hi]
        # 디코드 → temp PNG(정식 해시명: 메뉴폰트/외곽선 분기용)
        lin = fe.unswizzle_blocks(pay, bw, bh, 16)
        rgba = fe.decode_dxt_image_vec(lin, w, h, e['fmt'])
        export_png = os.path.join(tmp, full_hash + '.png')
        Image.fromarray(rgba).save(export_png)
        kr_png = os.path.join(tmp, full_hash + '_kr.png')
        n = af.create_korean_import(export_png, kr_png, MAPPING, KR_FONT, page_base=page_base)
        # 한글 PNG → DXT 재인코딩 → payload 교체 (동일 치수/포맷)
        kr_rgba = np.array(Image.open(kr_png).convert('RGBA'))
        data = fe.replace_subtexture(data, e, kr_rgba)
        log.append({'hash': full_hash, 'page_base': page_base, 'glyphs': n,
                    'size': (w, h), 'block_ord': e['block_ord']})
    return data, log


def bake_all_fonts(src_dir, out_dir):
    """src_dir(추출본)의 폰트 FTX들을 베이크해 out_dir에 동일 상대경로로 저장."""
    results = {}
    for rel in FONT_FTX_RELS:
        src = os.path.join(src_dir, rel)
        if not os.path.exists(src):
            results[rel] = [{'status': 'src-missing'}]
            continue
        data = open(src, 'rb').read()
        new_data, log = bake_font_ftx(data)
        out = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as f:
            f.write(new_data)
        results[rel] = log
    return results


def _verify():
    src_dir = os.path.join(ROOT, 'extracted', 'NinPri')
    os.makedirs(os.path.join(ROOT, 'temp', 'preview'), exist_ok=True)
    for rel in FONT_FTX_RELS:
        src = os.path.join(src_dir, rel)
        data = open(src, 'rb').read()
        new_data, log = bake_font_ftx(data)
        print(f"{rel}: {len(log)}개 페이지 베이크")
        for l in log:
            print("   ", l)
        # 재디코드 미리보기 (첫 베이크 페이지)
        entries = {e['block_ord']: e for e in fe.parse_all_gxt(new_data)}
        for l in log:
            e = entries[l['block_ord']]
            b = (e['width'] // 4) * (e['height'] // 4) * 16
            lin = fe.unswizzle_blocks(new_data[e['abs_off']:e['abs_off'] + b],
                                      e['width'] // 4, e['height'] // 4, 16)
            rgba = fe.decode_dxt_image_vec(lin, e['width'], e['height'], e['fmt'])
            img = Image.fromarray(rgba)
            bg = Image.new('RGBA', img.size, (40, 40, 40, 255))
            bg.alpha_composite(img)
            out = os.path.join(ROOT, 'temp', 'preview', f'fontbake_{l["hash"][:8]}.png')
            bg.convert('RGB').save(out)
            print(f"    미리보기 {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()
    if args.verify:
        _verify()
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
