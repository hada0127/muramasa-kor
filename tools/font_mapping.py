#!/usr/bin/env python3
"""SJIS 셀 변환 + ASCII 오버플로 배치표 (단일 진실 원본).

build_patch.py / auto_font_import.py / hd_font_import.py 세 곳이 ASCII를 SJIS
코드포인트로 인코딩하거나 폰트 텍스처에 ASCII 글리프를 그릴 때, 반드시 같은
배치표를 써야 한다. 과거에는 build_patch는 pos=960부터 고정 배치, font_import
계열은 한글 점유 셀을 skip — **배치표 불일치**로 '!'(0x21)이 河-local cell 961에
인코딩되는데 그 셀에는 한글 '딱'이 그려져 있어 '!'가 '딱'으로 보였다.

이 모듈이 한글 매핑(kr_sjis_mapping)을 읽어 河 페이지(base 1644)의 빈 셀
(960~1023 중 한글 미점유)에 ASCII를 배치하는 표를 만들고, 세 곳이 이 표만
참조하게 한다. 실제 번역에 등장하는 ASCII를 우선 배정하므로 등장 문자는
모두 河 빈 셀에 들어간다(미등장 문자는 공백 글리프로 폴백).
"""

import json
import os

PAGE0_BASE = 1644  # 河 (0x89CD) — ASCII/runtime 오버레이가 있는 기본 페이지

# 반각 그대로 두는 코드: 게임이 cell 192+code 위치에서 반각으로 렌더.
#   0x20 (space) — cell 224, 투명 클리어
#   0x2E (period) — cell 238, RUNTIME_OVERLAY가 '.' 그림
HALFWIDTH_CODES = {0x20, 0x2E}

# 공백 글리프로 쓰는 미사용 한글 '빕' (0x8C6D). 오버플로에 안 들어간 미등장
# ASCII는 이 코드로 폴백 → 화면에 안 보임(엉뚱한 글리프 대신 공백).
SPACE_SJIS = (0x8C, 0x6D)

_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_JP_MSG = os.path.join(_PROJECT, "translations", "jp_messages.json")
_MAPPING = os.path.join(_PROJECT, "translations", "kr_sjis_mapping.json")


def sjis_to_cell(b1, b2):
    """SJIS 2바이트 → 선형 글리프 셀 인덱스 (0x7F skip 반영)."""
    b2_offset = (b2 - 0x40) if b2 < 0x80 else (b2 - 0x41)
    return (b1 - 0x81) * 188 + b2_offset


def cell_to_sjis(cell):
    """선형 셀 인덱스 → SJIS 2바이트 (sjis_to_cell의 역함수)."""
    b1 = 0x81 + cell // 188
    b2_offset = cell % 188
    b2 = (0x40 + b2_offset) if b2_offset < 63 else (0x41 + b2_offset)
    return (b1, b2)


def load_korean_map(mapping_path=None):
    with open(mapping_path or _MAPPING, "r", encoding="utf-8") as f:
        return json.load(f)["korean_to_sjis"]


def korean_occupied_locals(kr_map, page_base=PAGE0_BASE):
    """주어진 페이지에서 한글이 점유한 local 셀 집합."""
    occ = set()
    for ch, (b1, b2) in kr_map.items():
        local = sjis_to_cell(b1, b2) - page_base
        if 0 <= local < 1024:
            occ.add(local)
    return occ


def free_overflow_cells(kr_map, lo=960, hi=1024, page_base=PAGE0_BASE):
    """河 페이지 [lo, hi) 중 한글이 점유하지 않은 빈 셀(오름차순)."""
    occ = korean_occupied_locals(kr_map, page_base)
    return [c for c in range(lo, hi) if c not in occ]


def used_ascii_chars(jp_path=None):
    """번역(ko)에 실제 등장하는 반각 ASCII 문자 집합 (0x21~0x7E).

    개행/포맷지정자(%s 등)/제어코드는 제외하지 않고 단순 문자 단위로 스캔한다.
    실사용 문자를 우선 배정해 河 빈 셀을 확보하기 위한 용도이므로 과대 추정해도
    안전하다(빈 셀이 충분).
    """
    data = json.load(open(jp_path or _JP_MSG, encoding="utf-8"))
    used = set()
    for sec in data.values():
        if not isinstance(sec, dict):
            continue
        for msg in sec.get("messages", []):
            ko = msg.get("ko", "")
            for ch in ko:
                o = ord(ch)
                if 0x21 <= o <= 0x7E:
                    used.add(ch)
    return used


def build_ascii_overflow_map(kr_map=None, jp_path=None):
    """ASCII(0x21~0x7E, 반각코드 제외) → SJIS 2바이트 배치표.

    河 빈 셀에 '실사용 문자 우선(코드순) → 나머지(코드순)' 순서로 배정.
    빈 셀을 다 쓰면 공백 글리프(SPACE_SJIS)로 폴백한다(미등장 문자만 해당).
    """
    if kr_map is None:
        kr_map = load_korean_map()
    free = free_overflow_cells(kr_map)
    used = used_ascii_chars(jp_path)
    codes = [c for c in range(0x21, 0x7F) if c not in HALFWIDTH_CODES]
    ordered = ([c for c in codes if chr(c) in used] +
               [c for c in codes if chr(c) not in used])
    out = {}
    fi = 0
    for code in ordered:
        if fi < len(free):
            # free[fi]는 河 페이지 local 셀 → 선형 셀은 page_base + local
            out[chr(code)] = cell_to_sjis(PAGE0_BASE + free[fi])
            fi += 1
        else:
            out[chr(code)] = SPACE_SJIS  # 폴백(미등장 문자)
    return out


def ascii_overflow_cells(kr_map=None, jp_path=None, page_base=PAGE0_BASE):
    """font_import용: 河 페이지에 그릴 {ASCII문자: local_cell} 맵.

    오버플로 배치표 중 이 페이지(960~1023) 안에 떨어지는 항목만 반환.
    공백 폴백(SPACE_SJIS)은 그리지 않는다.
    """
    if kr_map is None:
        kr_map = load_korean_map()
    cells = {}
    for ch, (b1, b2) in build_ascii_overflow_map(kr_map, jp_path).items():
        if (b1, b2) == SPACE_SJIS:
            continue
        local = sjis_to_cell(b1, b2) - page_base
        if 960 <= local < 1024:
            cells[ch] = local
    return cells


def validate_translation_ascii(kr_map=None, jp_path=None, runtime_overlay_codes=None):
    """모든 번역의 ASCII가 안전하게 렌더되는지 검증.

    안전 조건: (a) 반각코드(space/period) (b) 河 오버플로 셀에 배정 (c) RUNTIME_OVERLAY
    화이트리스트. 어디에도 없으면 화면에서 깨질 수 있으므로 위반 문자를 리턴.
    """
    if kr_map is None:
        kr_map = load_korean_map()
    cells = ascii_overflow_cells(kr_map, jp_path)
    safe = set(cells) | {chr(c) for c in HALFWIDTH_CODES}
    if runtime_overlay_codes:
        safe |= {chr(c) for c in runtime_overlay_codes}
    used = used_ascii_chars(jp_path)
    return sorted(used - safe)


if __name__ == "__main__":
    krm = load_korean_map()
    free = free_overflow_cells(krm)
    used = sorted(used_ascii_chars())
    om = build_ascii_overflow_map(krm)
    cells = ascii_overflow_cells(krm)
    print(f"河 빈 오버플로 셀: {len(free)}개")
    print(f"번역 등장 ASCII({len(used)}): {''.join(used)}")
    print(f"河에 그려지는 ASCII: {len(cells)}개")
    print("등장 ASCII 배정 결과:")
    for ch in used:
        if ord(ch) in HALFWIDTH_CODES:
            print(f"  {ch!r} -> 반각(192+code 경로)")
            continue
        sj = om[ch]
        loc = sjis_to_cell(*sj) - PAGE0_BASE
        where = "공백폴백" if sj == SPACE_SJIS else (
            f"河 local{loc}" if 0 <= loc < 1024 else "오프페이지")
        print(f"  {ch!r} -> {sj[0]:02X}{sj[1]:02X}  {where}")
    viol = validate_translation_ascii(krm)
    print(f"\n검증 위반(렌더 불가 ASCII): {viol if viol else '없음 ✓'}")
