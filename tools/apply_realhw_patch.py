#!/usr/bin/env python3
"""
실기(real PS Vita) 한글 패처 — 사용자 원본 CPK에 한글 텍스처+폰트+텍스트를 직접 베이크.

배포 zip에 동봉되어 사용자 PC에서 실행된다. 사용자의 원본 CPK로부터 한글 패치 CPK를 생성하므로
원본 게임 데이터를 배포하지 않는다(저작권 안전, 버전 견고). rePatch 플러그인 방식으로 적용.

처리:
1. 사용자 CPK(NinPri/NinPriPatch[/DLC Pack1~4])에서 FTX·NMS만 선택 추출
2. NMS 대사/메뉴 한글 텍스트 빌드(build_patch — 사용자 추출본 템플릿 사용)
3. 한글 텍스처(매니페스트 기반) + 폰트 글리프를 base FTX에 베이크(원본 해상도, 다운스케일)
4. NMS + 베이크 FTX를 CPK에 append(실기용 ETOC 무력화)
5. ux0/rePatch/PCSE00240/ (+ ux0/reAddcont/.../DLC) 구조로 출력

사용:
    python3 apply_realhw_patch.py \
        --ninpri /path/NinPri.cpk --ninpripatch /path/NinPriPatch.cpk \
        [--pack1 ... --pack2 ... --pack3 ... --pack4 ...] \
        --out ./out [--enter-button circle|cross]

출력을 Vita의 ux0:/ 아래에 복사하고 rePatch 플러그인을 활성화할 것.
"""

import sys
import os
import shutil
import glob
import argparse
import tempfile

# 데이터 루트: 프로즌 exe(PyInstaller)는 데이터를 exe 옆에 동봉하므로 __file__ 기준이
# 빗나간다. gui_patcher 가 MURAMASA_ROOT 로 올바른 패키지 루트를 넘겨준다(없으면 소스 기준).
REPO = os.environ.get('MURAMASA_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, 'tools'))

import cpk_extract
import cpk_patch
import build_patch
import realhw_bake as rb
import realhw_font_bake as rfb

TRANSLATIONS = os.path.join(REPO, 'translations')
KR_UI = os.path.join(REPO, 'textures', 'kr', 'ui')
XBUTTON_DIR = os.path.join(REPO, 'textures', 'kr', 'ui_xbutton')
TITLE_ID = 'PCSE00240'

# DLC 팩: manifest cpk 키 → (입력 인자, reAddcont 출력 상대경로)
DLC_PACKS = {
    'Pack1': ('OBOROMURAMASAPK1/NinPriPack1.cpk', 'pack1'),
    'Pack2': ('OBOROMURAMASAPK2/NinPriPack2.cpk', 'pack2'),
    'Pack3': ('OBOROMURAMASAPK3/NinPriPack3.cpk', 'pack3'),
    'Pack4': ('OBOROMURAMASAPK4/NinPriPack4.cpk', 'pack4'),
}


def _need_file(path):
    """패처가 필요로 하는 CPK 내부 파일(FTX/NMS)만 추출."""
    return path.endswith('.ftx') or path.endswith('.nms')


def _collect_tree(root):
    """디렉토리 트리 → {상대경로(posix): bytes}."""
    out = {}
    for p in glob.glob(os.path.join(root, '**', '*'), recursive=True):
        if not os.path.isfile(p):
            continue
        rel = os.path.relpath(p, root).replace('\\', '/')
        with open(p, 'rb') as f:
            out[rel] = f.read()
    return out


def _xbutton_overrides():
    """✕버튼 변형: {hash: ui_xbutton/<hash>.png}."""
    ov = {}
    for p in glob.glob(os.path.join(XBUTTON_DIR, '*.png')):
        h = os.path.splitext(os.path.basename(p))[0]
        ov[h] = p
    return ov


def _check_decrypted_cpk(path, label):
    """복호화된 CPK인지 최소 검증.

    실기(real Vita) 본체의 앱 데이터는 PFS 암호화돼 직접 읽을 수 없고, 복호화된
    CPK는 Vita3K가 게임 설치 시 풀어 둔 ux0/app·ux0/addcont 에만 존재한다.
    여기서는 파일 선두 매직(b'CPK ')만 확인해, 엉뚱한/암호화 파일을 빨리 걸러낸다.
    """
    try:
        with open(path, 'rb') as f:
            sig = f.read(4)
    except OSError as e:
        raise SystemExit(f"[오류] {label} 를 열 수 없습니다: {path}\n  {e}")
    if sig != b'CPK ':
        raise SystemExit(
            f"[오류] {label} 가 올바른 CPK가 아닙니다(매직 {sig!r}): {path}\n"
            "  파일이 손상됐거나 엉뚱한 파일일 수 있습니다. 또한 실기 본체의 암호화 파일은\n"
            "  쓸 수 없습니다 — Vita3K에 게임을 설치하면 ux0/app/PCSE00240/ 에 생기는\n"
            "  복호화된 CPK를 사용하세요.")


def resolve_cpks_from_vita3k(vita3k_root):
    """Vita3K 설치 폴더(또는 content root)에서 복호화된 CPK 경로들을 해석.

    반환: (ninpri, ninpripatch, {'Pack1': path|None, ...})
    실기 패치 재료(복호화 CPK)의 신뢰 가능한 단일 출처는 Vita3K 설치본이다.
    """
    sys.path.insert(0, os.path.join(REPO, 'tools'))
    import apply_release_patch as arp
    content_root = arp.resolve_content_root(vita3k_root or None, TITLE_ID)
    app_dir = content_root / 'ux0' / 'app' / TITLE_ID
    ninpri = str(app_dir / 'NinPri.cpk')
    ninpripatch = str(app_dir / 'NinPriPatch.cpk')
    addcont = content_root / 'ux0' / 'addcont' / TITLE_ID
    packs = {}
    for key, (rel, _) in DLC_PACKS.items():
        cand = addcont / rel
        packs[key] = str(cand) if cand.exists() else None
    return ninpri, ninpripatch, packs


def patch(ninpri, ninpripatch, packs, out_dir, enter_button='circle'):
    _check_decrypted_cpk(ninpri, 'NinPri.cpk')
    _check_decrypted_cpk(ninpripatch, 'NinPriPatch.cpk')
    for key, cpk in packs.items():
        if cpk:
            _check_decrypted_cpk(cpk, f'{key} ({os.path.basename(cpk)})')
    manifest = rb.load_manifest()
    overrides = _xbutton_overrides() if enter_button == 'cross' else None
    work = tempfile.mkdtemp(prefix='realhw_')
    ext = os.path.join(work, 'extracted')
    baked = os.path.join(work, 'baked')
    print(f"[작업 디렉토리] {work}")

    # 1) 선택 추출 -------------------------------------------------------------
    print("\n[1/5] 원본 CPK에서 FTX·NMS 추출")
    cpk_extract.extract_cpk(ninpri, os.path.join(ext, 'NinPri'), path_filter=_need_file)
    cpk_extract.extract_cpk(ninpripatch, os.path.join(ext, 'NinPriPatch'), path_filter=_need_file)
    pack_paths = {}
    for key, cpk in packs.items():
        if cpk:
            cpk_extract.extract_cpk(cpk, os.path.join(ext, key),
                                    path_filter=lambda p: p.endswith('.ftx'))
            pack_paths[key] = cpk

    # NinPriPatch_full 템플릿(= NinPriPatch scemsg.nms 복사)
    for sub in ('_US/msgsheet', 'msgsheet'):
        src = os.path.join(ext, 'NinPriPatch', sub, 'scemsg.nms')
        if os.path.exists(src):
            dst_dir = os.path.join(ext, 'NinPriPatch_full', sub)
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy(src, os.path.join(dst_dir, 'scemsg_full.nms'))

    # 2) NMS 텍스트 패치 빌드 --------------------------------------------------
    print("\n[2/5] NMS 대사/메뉴 한글 텍스트 빌드")
    build_patch.build_korean_patch(base_dir=work, translations_dir=TRANSLATIONS)

    # 3) 텍스처·폰트 베이크 ----------------------------------------------------
    print("\n[3/5] 한글 텍스처·폰트를 base FTX에 베이크")
    bake_log = {}
    bake_log['NinPri'] = rb.bake_cpk_ftx(manifest, os.path.join(ext, 'NinPri'),
                                         'NinPri', KR_UI, os.path.join(baked, 'NinPri'), overrides)
    rfb.bake_all_fonts(os.path.join(ext, 'NinPri'), os.path.join(baked, 'NinPri'))
    bake_log['NinPriPatch'] = rb.bake_cpk_ftx(manifest, os.path.join(ext, 'NinPriPatch'),
                                              'NinPriPatch', KR_UI, os.path.join(baked, 'NinPriPatch'), overrides)
    for key in pack_paths:
        bake_log[key] = rb.bake_cpk_ftx(manifest, os.path.join(ext, key),
                                        key, KR_UI, os.path.join(baked, key), overrides)
    _print_bake_summary(bake_log)

    # 4) 조립: NMS + 베이크 FTX → CPK append ----------------------------------
    print("\n[4/5] CPK 재패킹 (ETOC 무력화 — 실기 호환)")
    rep_dir = os.path.join(out_dir, 'ux0', 'rePatch', TITLE_ID)
    os.makedirs(rep_dir, exist_ok=True)

    main_repl = _collect_tree(os.path.join(work, 'patch_main'))
    main_repl.update(_collect_tree(os.path.join(baked, 'NinPri')))
    cpk_patch.patch_cpk_append(ninpri, os.path.join(rep_dir, 'NinPri.cpk'),
                               main_repl, disable_etoc=True)

    patch_repl = _collect_tree(os.path.join(work, 'patch_patch'))
    patch_repl.update(_collect_tree(os.path.join(baked, 'NinPriPatch')))
    cpk_patch.patch_cpk_append(ninpripatch, os.path.join(rep_dir, 'NinPriPatch.cpk'),
                               patch_repl, disable_etoc=True)

    # 5) DLC 팩(reAddcont) -----------------------------------------------------
    for key, cpk in pack_paths.items():
        rel, _ = DLC_PACKS[key]
        dlc_repl = _collect_tree(os.path.join(baked, key))
        if not dlc_repl:
            continue
        out_cpk = os.path.join(out_dir, 'ux0', 'reAddcont', TITLE_ID, rel)
        os.makedirs(os.path.dirname(out_cpk), exist_ok=True)
        cpk_patch.patch_cpk_append(cpk, out_cpk, dlc_repl, disable_etoc=True)

    print("\n[5/5] 완료")
    print(f"  출력: {os.path.join(out_dir, 'ux0')}")
    print("  → Vita의 ux0:/ 아래에 ux0/ 내용을 복사하고 rePatch 플러그인을 활성화하세요.")
    if enter_button == 'cross':
        print("  → ✕ 결정 버튼: Vita 설정에서 Enter Button = Cross 로 맞추세요.")
    shutil.rmtree(work, ignore_errors=True)


def _print_bake_summary(bake_log):
    total_ok = 0
    issues = []
    for cpk, ftxs in bake_log.items():
        for ftx, log in ftxs.items():
            for l in log:
                if l.get('status') == 'ok':
                    total_ok += 1
                elif l.get('status') not in (None,):
                    issues.append(f"{cpk}/{ftx}: {l}")
    print(f"  베이크 성공 텍스처: {total_ok}")
    if issues:
        print(f"  ⚠ 경고 {len(issues)}건:")
        for i in issues[:20]:
            print("    ", i)


def main():
    ap = argparse.ArgumentParser(description='Muramasa 실기(real Vita) 한글 패처')
    ap.add_argument('--vita3k', help='Vita3K 설치 폴더(또는 content root). 지정 시 복호화 CPK를 '
                                     '여기서 자동 해석한다(권장). 실기 본체의 암호화 파일 대신 사용.')
    ap.add_argument('--ninpri', help='원본 NinPri.cpk 경로 (--vita3k 미사용 시 필수)')
    ap.add_argument('--ninpripatch', help='원본 NinPriPatch.cpk 경로 (--vita3k 미사용 시 필수)')
    ap.add_argument('--pack1', help='원본 NinPriPack1.cpk (DLC, 선택)')
    ap.add_argument('--pack2', help='원본 NinPriPack2.cpk (DLC, 선택)')
    ap.add_argument('--pack3', help='원본 NinPriPack3.cpk (DLC, 선택)')
    ap.add_argument('--pack4', help='원본 NinPriPack4.cpk (DLC, 선택)')
    ap.add_argument('--out', default='./realhw_out', help='출력 디렉토리')
    ap.add_argument('--enter-button', choices=['circle', 'cross'], default='circle',
                    help='결정 버튼 표시: circle(○, 기본) / cross(✕, Vita Enter=Cross 필요)')
    args = ap.parse_args()

    if args.vita3k:
        if args.ninpri or args.ninpripatch:
            ap.error("--vita3k 와 --ninpri/--ninpripatch 는 함께 쓸 수 없습니다. 하나만 지정하세요.")
        try:
            ninpri, ninpripatch, packs = resolve_cpks_from_vita3k(args.vita3k)
        except FileNotFoundError:
            ap.error(f"Vita3K 설치에서 게임을 찾지 못했습니다: {args.vita3k}\n"
                     "  Vita3K 폴더가 맞는지, 게임이 설치돼 있는지 확인하세요.")
    else:
        if not (args.ninpri and args.ninpripatch):
            ap.error("--vita3k 또는 (--ninpri 와 --ninpripatch)를 지정하세요.")
        ninpri, ninpripatch = args.ninpri, args.ninpripatch
        packs = {'Pack1': args.pack1, 'Pack2': args.pack2, 'Pack3': args.pack3, 'Pack4': args.pack4}

    for label, p in [('NinPri', ninpri), ('NinPriPatch', ninpripatch)]:
        if not os.path.exists(p):
            ap.error(f"{label} 파일 없음: {p}\n  Vita3K에 게임이 설치돼 있는지 확인하세요.")

    patch(ninpri, ninpripatch, packs, args.out, args.enter_button)


if __name__ == '__main__':
    main()
