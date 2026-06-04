#!/usr/bin/env python3
"""
실기 한글 텍스처 베이크 (Phase 3) — 매니페스트 기반으로 한글 텍스처를 FTX payload에 in-place 베이크.

ftx_texture_map.json 의 각 한글 해시 → CPK 내부 FTX 서브텍스처 위치(block_ord)로,
textures/kr/ui/<hash>.png 를 base 치수로 다운스케일(실기는 업스케일 불요) → DXT 재인코딩
→ Vita swizzle → 원본 payload와 동일 길이로 교체. FTX 구조/치수/포맷 보존.

사용자 패처(apply_realhw_patch.py)와 빌드 검증에서 공용으로 쓰는 핵심 모듈.

함수:
    group_locations(manifest)          → {(cpk, ftx_path): [(hash, loc), ...]}
    bake_ftx(ftx_bytes, items, kr_dir) → 수정된 FTX bytes, 베이크 로그
    bake_cpk_ftx(manifest, src_dir, cpk, kr_dir, out_dir) → 수정 FTX 파일 산출

CLI(검증용):
    python3 tools/realhw_bake.py --verify-ftx NinPriPatch _US/GUI/ChrSelect.ftx
       → 해당 FTX를 베이크 후 재디코드해 한글 렌더 미리보기 PNG 저장
"""

import sys
import os
import json
import glob
import argparse
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import ftx_encode as fe

MANIFEST = os.path.join(ROOT, 'translations', 'ftx_texture_map.json')
KR_UI = os.path.join(ROOT, 'textures', 'kr', 'ui')


def load_manifest(path=MANIFEST):
    with open(path) as f:
        return json.load(f)


def group_locations(manifest):
    """매니페스트 → {(cpk, ftx_path): [(hash, loc), ...]} 그룹화."""
    groups = {}
    for h, info in manifest.items():
        for loc in info['locations']:
            groups.setdefault((loc['cpk'], loc['ftx_path']), []).append((h, loc))
    return groups


def _load_kr_resized(kr_dir, hsh, w, h, overrides=None):
    """한글 텍스처 PNG → (h,w,4) RGBA, base 치수로 알파인지 다운스케일.

    overrides: {hash: png_path} 가 있으면 그 경로를 우선 사용(✕버튼 변형 등).
    """
    p = None
    if overrides and hsh in overrides:
        p = overrides[hsh]
    else:
        cand = os.path.join(kr_dir, hsh + '.png')
        if os.path.exists(cand):
            p = cand
    if not p or not os.path.exists(p):
        return None
    im = Image.open(p).convert('RGBA')
    if im.size != (w, h):
        im = im.resize((w, h), Image.LANCZOS)
    return np.array(im)


def bake_ftx(ftx_bytes, items, kr_dir=KR_UI, overrides=None):
    """FTX bytes 안의 지정 서브텍스처들을 한글로 교체.

    items: [(hash, loc), ...] (loc은 block_ord/w/h/fmt 포함)
    overrides: {hash: png_path} 특정 해시를 다른 PNG로(✕버튼 ui_xbutton 등).
    Returns (new_bytes, log[list of dict]).
    """
    data = ftx_bytes
    entries = {e['block_ord']: e for e in fe.parse_all_gxt(data)}
    log = []
    for hsh, loc in items:
        bo = loc['block_ord']
        e = entries.get(bo)
        if e is None:
            log.append({'hash': hsh, 'status': 'no-block', 'block_ord': bo})
            continue
        # 안전 가드: 치수·포맷·해시 상위32 일치 확인
        if e['width'] != loc['w'] or e['height'] != loc['h']:
            log.append({'hash': hsh, 'status': 'dim-mismatch',
                        'expect': (loc['w'], loc['h']), 'got': (e['width'], e['height'])})
            continue
        base = (e['width'] // 4) * (e['height'] // 4) * 16
        cur_high = ('%016X' % __import__('xxhash').xxh3_64(
            data[e['abs_off']:e['abs_off'] + base]).intdigest())[:8]
        if cur_high != hsh[:8]:
            log.append({'hash': hsh, 'status': 'high32-mismatch', 'got': cur_high})
            continue
        kr = _load_kr_resized(kr_dir, hsh, e['width'], e['height'], overrides)
        if kr is None:
            log.append({'hash': hsh, 'status': 'no-kr-png'})
            continue
        data = fe.replace_subtexture(data, e, kr)
        # 교체 후 entries 무효화 방지: abs_off/구조 동일하므로 재파싱 불필요(길이 보존)
        log.append({'hash': hsh, 'status': 'ok', 'size': (e['width'], e['height']),
                    'fmt': '0x%08X' % e['fmt']})
    return data, log


def bake_cpk_ftx(manifest, src_dir, cpk, kr_dir, out_dir, overrides=None):
    """한 CPK(src_dir 추출본)의 FTX들을 베이크해 out_dir에 동일 상대경로로 저장.

    overrides: {hash: png_path} ✕버튼 변형 등 특정 해시 소스 교체.
    Returns {ftx_path: log} (이 cpk에 해당하는 것만).
    """
    groups = group_locations(manifest)
    results = {}
    for (g_cpk, ftx_path), items in groups.items():
        if g_cpk != cpk:
            continue
        src = os.path.join(src_dir, ftx_path)
        if not os.path.exists(src):
            results[ftx_path] = [{'status': 'src-missing'}]
            continue
        data = open(src, 'rb').read()
        new_data, log = bake_ftx(data, items, kr_dir, overrides)
        out = os.path.join(out_dir, ftx_path)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, 'wb') as f:
            f.write(new_data)
        results[ftx_path] = log
    return results


# --- 검증 CLI ---

def _verify_ftx(cpk, ftx_path):
    manifest = load_manifest()
    src_dir = os.path.join(ROOT, 'extracted', cpk) if cpk in ('NinPri', 'NinPriPatch') \
        else os.path.join('/tmp/dlc_extract', cpk)
    src = os.path.join(src_dir, ftx_path)
    data = open(src, 'rb').read()
    items = [(h, loc) for h, info in manifest.items() for loc in info['locations']
             if loc['cpk'] == cpk and loc['ftx_path'] == ftx_path]
    print(f"{cpk}/{ftx_path}: {len(items)}개 서브텍스처 베이크")
    new_data, log = bake_ftx(data, items)
    for l in log:
        print("  ", l)
    # 베이크된 FTX 재디코드 → 각 교체 서브텍스처 미리보기
    os.makedirs(os.path.join(ROOT, 'temp', 'preview'), exist_ok=True)
    entries = {e['block_ord']: e for e in fe.parse_all_gxt(new_data)}
    for h, loc in items:
        e = entries[loc['block_ord']]
        b = (e['width'] // 4) * (e['height'] // 4) * 16
        lin = fe.unswizzle_blocks(new_data[e['abs_off']:e['abs_off'] + b],
                                  e['width'] // 4, e['height'] // 4, 16)
        rgba = fe.decode_dxt_image_vec(lin, e['width'], e['height'], e['fmt'])
        img = Image.fromarray(rgba)
        bg = Image.new('RGBA', img.size, (40, 40, 40, 255))
        bg.alpha_composite(img)
        if max(bg.size) > 1500:
            bg.thumbnail((1500, 1500))
        out = os.path.join(ROOT, 'temp', 'preview', f'baked_{cpk}_{h[:8]}.png')
        bg.convert('RGB').save(out)
        print(f"  미리보기 {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify-ftx', nargs=2, metavar=('CPK', 'FTX_PATH'),
                    help='한 FTX 베이크 후 재디코드 미리보기')
    args = ap.parse_args()
    if args.verify_ftx:
        _verify_ftx(*args.verify_ftx)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
