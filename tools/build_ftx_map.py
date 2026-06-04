#!/usr/bin/env python3
"""
hash → FTX(서브텍스처) 매핑 매니페스트 빌더 (실기 패치 Phase 2).

우리 한글 텍스처는 Vita3K hash 이름(textures/kr/ui/<hash>.png)으로만 존재한다. 실기 베이크엔
"이 해시가 CPK 내부 어느 FTX/GXT 서브텍스처인가"가 필요하다.

★ 정확 매핑 키 = Vita3K 텍스처 해시의 상위 32비트
- Vita3K 텍스처 해시 = XXH3_64(메모리상 텍스처 데이터=swizzled base payload). 파일명 16hex.
- 시스템 xxhash(0.8.x)는 Vita3K 번들 구버전과 XXH3 finalizer 리비전이 달라 **하위 32비트만 상수
  패턴(0x02000100류)으로 어긋나고 상위 32비트는 정확히 일치**(실측 확인). 따라서 상위 8 hex를
  매칭 키로 쓰면 NCC·HD리페인트 영향 없이 정확히 매핑된다(32비트=43억 공간, 후보 수백 → 사실상 유일).
- 다중 후보(동일 high32)는 NCC로 tiebreak. NCC는 참고로만 기록(HD팩 리페인트라 낮을 수 있음).

소스 CPK: NinPri, NinPriPatch (rePatch 대상) + DLC 팩 Pack1~4 (reAddcont, place/엔딩 아틀라스).

Usage:
    python3 tools/build_ftx_map.py            # 매니페스트 생성 + 리포트
    python3 tools/build_ftx_map.py --report   # 기존 매니페스트 커버리지만 출력
"""

import sys
import os
import glob
import json
import argparse
import numpy as np
import xxhash
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import ftx_encode as fe

# 소스 CPK 추출본 (있는 것만 사용)
EXTRACT_DIRS = {
    'NinPri': os.path.join(ROOT, 'extracted', 'NinPri'),
    'NinPriPatch': os.path.join(ROOT, 'extracted', 'NinPriPatch'),
    'Pack1': '/tmp/dlc_extract/Pack1',
    'Pack2': '/tmp/dlc_extract/Pack2',
    'Pack3': '/tmp/dlc_extract/Pack3',
    'Pack4': '/tmp/dlc_extract/Pack4',
}
# Pack* 의 reAddcont 산출 파일명 (사용자 패처가 어디에 쓸지)
DLC_PACK_FILE = {
    'Pack1': 'OBOROMURAMASAPK1/NinPriPack1.cpk',
    'Pack2': 'OBOROMURAMASAPK2/NinPriPack2.cpk',
    'Pack3': 'OBOROMURAMASAPK3/NinPriPack3.cpk',
    'Pack4': 'OBOROMURAMASAPK4/NinPriPack4.cpk',
}
ORIGINALS = os.path.join(ROOT, 'textures', 'originals')
KR_UI = os.path.join(ROOT, 'textures', 'kr', 'ui')
MANIFEST = os.path.join(ROOT, 'translations', 'ftx_texture_map.json')


def _is_ui_ftx(path):
    """UI/place 텍스트 텍스처가 들어있을 FTX만 후보로(bg/chara 등 대량 제외, GUI/other 한정)."""
    p = path.replace('\\', '/')
    name = os.path.basename(p).lower()
    if name.startswith('font'):
        return False  # 폰트는 Phase 4에서 별도 처리
    return '/GUI/' in p


def vita3k_high32(payload):
    """Vita3K 텍스처 해시 상위 32비트(8 hex). XXH3_64 상위 절반 = 버전 무관 안정."""
    return ('%016X' % xxhash.xxh3_64(payload).intdigest())[:8]


def collect_subtextures():
    """후보 FTX 전체 → 서브텍스처 목록(디코드 + high32).

    Returns list of dict: cpk, ftx_path(rel), gxt_index, w,h,fmt,mipmaps, high32, alpha, rgb
    """
    subs = []
    for cpk, base in EXTRACT_DIRS.items():
        if not os.path.isdir(base):
            continue
        for fpath in sorted(glob.glob(os.path.join(base, '**', '*.ftx'), recursive=True)):
            if not _is_ui_ftx(fpath):
                continue
            rel = os.path.relpath(fpath, base).replace('\\', '/')
            data = open(fpath, 'rb').read()
            for e in fe.parse_all_gxt(data):
                if e['fmt'] not in (fe.DXT5, fe.DXT3):
                    continue
                w, h = e['width'], e['height']
                bw, bh = w // 4, h // 4
                base_sz = bw * bh * 16
                pay = data[e['abs_off']:e['abs_off'] + base_sz]
                if len(pay) < base_sz:
                    continue
                lin = fe.unswizzle_blocks(pay, bw, bh, 16)
                rgba = fe.decode_dxt_image_vec(lin, w, h, e['fmt'])
                subs.append({
                    'cpk': cpk,
                    'ftx_path': rel,
                    'block_ord': e['block_ord'],
                    'gxt_index': e['index'],
                    'w': w, 'h': h, 'fmt': e['fmt'], 'mipmaps': e['mipmaps'],
                    'high32': vita3k_high32(pay),
                    'alpha': rgba[:, :, 3].astype(np.float32),
                    'rgb': rgba[:, :, :3].astype(np.float32),
                })
    return subs


def _ncc(a, b):
    a = a.ravel() - a.mean()
    b = b.ravel() - b.mean()
    da = np.sqrt((a * a).sum())
    db = np.sqrt((b * b).sum())
    if da < 1e-6 or db < 1e-6:
        return 1.0 if da < 1e-6 and db < 1e-6 else 0.0
    return float((a * b).sum() / (da * db))


def _ncc_to_sub(orig_img, s):
    """원본(HD)을 서브텍스처 크기로 다운스케일 후 알파 NCC (참고/타이브레이크용)."""
    w, h = s['w'], s['h']
    if orig_img.width * h != orig_img.height * w or orig_img.width < w:
        return 0.0
    ds = np.array(orig_img.resize((w, h), Image.LANCZOS).convert('RGBA'))
    return _ncc(ds[:, :, 3].astype(np.float32), s['alpha'])


def build():
    print("후보 FTX 서브텍스처 디코드/해시 중...")
    subs = collect_subtextures()
    by_high = {}
    for s in subs:
        by_high.setdefault(s['high32'], []).append(s)
    nftx = len(set((s['cpk'], s['ftx_path']) for s in subs))
    print(f"  후보 서브텍스처 {len(subs)}개 ({nftx} FTX, {len(by_high)} unique high32)")

    kr_hashes = sorted(os.path.splitext(os.path.basename(p))[0]
                       for p in glob.glob(os.path.join(KR_UI, '*.png')))
    manifest = {}
    cov = {'mapped': [], 'unmapped': [], 'multi': []}

    for h in kr_hashes:
        cand = by_high.get(h[:8], [])
        op = os.path.join(ORIGINALS, h + '.png')
        orig = Image.open(op) if os.path.exists(op) else None
        if not cand:
            cov['unmapped'].append((h, 'no-high32-match'))
            continue
        # 다중후보면 NCC로 정렬(동일 high32는 보통 동일 아트가 여러 CPK에 = 전부 베이크)
        scored = []
        for s in cand:
            ncc = _ncc_to_sub(orig, s) if orig is not None else 0.0
            scored.append((ncc, s))
        scored.sort(key=lambda x: -x[0])
        locs = []
        for ncc, s in scored:
            loc = {
                'cpk': s['cpk'], 'ftx_path': s['ftx_path'],
                'block_ord': s['block_ord'], 'gxt_index': s['gxt_index'],
                'w': s['w'], 'h': s['h'], 'fmt': '0x%08X' % s['fmt'], 'mipmaps': s['mipmaps'],
                'alpha_ncc': round(ncc, 4),
            }
            if s['cpk'] in DLC_PACK_FILE:
                loc['dlc_out'] = DLC_PACK_FILE[s['cpk']]
            locs.append(loc)
        manifest[h] = {
            'orig_size': list(orig.size) if orig is not None else None,
            'locations': locs,
        }
        cov['mapped'].append(h)
        if len(locs) > 1:
            cov['multi'].append((h, len(locs)))

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, 'w') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print(f"\n매니페스트 저장: {os.path.relpath(MANIFEST, ROOT)}")
    print(f"  매핑됨: {len(cov['mapped'])}/{len(kr_hashes)}")
    print(f"  다중위치(_US/DLC 등): {len(cov['multi'])}")
    print(f"  미매핑: {len(cov['unmapped'])}")
    # CPK별 분포
    from collections import Counter
    cpkc = Counter(l['cpk'] for v in manifest.values() for l in v['locations'])
    print("  위치 CPK 분포:", dict(cpkc))
    if cov['unmapped']:
        print("  [미매핑 — 수동 리뷰]")
        for h, why in cov['unmapped']:
            sz = Image.open(os.path.join(ORIGINALS, h + '.png')).size if os.path.exists(os.path.join(ORIGINALS, h + '.png')) else '?'
            print(f"    {h}  ({why}, orig {sz})")
    return manifest, cov


def report():
    if not os.path.exists(MANIFEST):
        print("매니페스트 없음 — 먼저 빌드"); return
    m = json.load(open(MANIFEST))
    kr = sorted(os.path.splitext(os.path.basename(p))[0]
                for p in glob.glob(os.path.join(KR_UI, '*.png')))
    mapped = set(m.keys())
    print(f"매핑 {len(mapped)}/{len(kr)}, 미매핑 {len(set(kr) - mapped)}")
    for h in kr:
        if h in m:
            paths = ', '.join(f"{l['cpk']}/{l['ftx_path']}#{l['gxt_index']}({l['w']}x{l['h']},ncc{l['alpha_ncc']})"
                              for l in m[h]['locations'])
            print(f"  ✓ {h}: {paths}")
        else:
            print(f"  ✗ {h}: 미매핑")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', action='store_true')
    args = ap.parse_args()
    report() if args.report else build()


if __name__ == '__main__':
    main()
