#!/usr/bin/env python3
"""대사/메시지 번역 품질 검수기 (lint).

jp_messages.json의 ko 필드를 규칙별로 검사해 error/warning으로 리포트한다.
재번역 파이프라인의 자동 게이트 + 현재 번역의 회귀 추적용.

폭/인코딩 기준은 기존 도구와 일관:
- line_width: ASCII 0.5, 그 외 전각 1.0 (analyze_jp_width.py와 동일)
- 인코딩 가능 = 한글 음절이 kr_sjis_mapping.korean_to_sjis(완성형 2350자)에 있음

사용:
  python tools/lint_dialogs.py                      # 전체 요약
  python tools/lint_dialogs.py --section scemsg      # 특정 섹션
  python tools/lint_dialogs.py --severity error      # error만
  python tools/lint_dialogs.py --rule width --limit 20   # 특정 규칙 샘플
  python tools/lint_dialogs.py --json temp/lint.json # 전체 결과 JSON
"""
import json
import re
import os
import argparse
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 대사창 박스 한도(전각). 원작(ja) 폭 분포 p99=29·max=31, success.md "박스 추정 한도 29.5"
# 기준. 초과 = 게임에서 잘릴 위험(error). 미관 목표(여백)는 27이지만 그건 재번역 권장사항이라
# lint에서 강제하지 않는다.
WIDTH_LIMIT = {'scemsg': 29.5, 'scemsg_patch': 29.5}   # 대사창. 그 외 섹션은 박스 미상 → 폭 검사 생략
LINE_LIMIT = {'scemsg': 3, 'scemsg_patch': 3}          # 대사창 최대 3줄
SOFT_WIDTH = 27.0  # 미관 목표(초과는 info, 재번역 시 여백 권장)

HANGUL = re.compile(r'[가-힣]')
KANA = re.compile(r'[぀-ヿ]')
JP_PUNCT_HARD = re.compile(r'[。、]')        # 일본 마침표/쉼표 → 한국어는 . ,
JP_QUOTE = re.compile(r'[「」『』]')          # 일본 인용부호 (스타일)
CJK = re.compile(r'[㐀-鿿豈-﫿]')  # 한자 잔존


def line_width(s):
    return sum(0.5 if ord(c) < 0x80 else 1.0 for c in s)


def load():
    kr = json.load(open(f'{BASE}/translations/kr_sjis_mapping.json',
                        encoding='utf-8'))['korean_to_sjis']
    return kr


def check(section, ja, ko, kr_map):
    """한 메시지의 ko에 대한 (severity, rule, message) 리스트."""
    issues = []
    def add(sev, rule, msg): issues.append((sev, rule, msg))
    if not ko:
        return issues
    lines = ko.split('\n')

    # 줄 수 / 폭 (대사창 섹션만; 그 외는 박스 미상 → 생략) / 공백
    llim = LINE_LIMIT.get(section)
    wlim = WIDTH_LIMIT.get(section)
    if llim and len(lines) > llim:
        add('error', 'line_count', f'{len(lines)}줄 (최대 {llim})')
    for i, l in enumerate(lines, 1):
        w = line_width(l)
        if wlim and w > wlim:
            add('error', 'width', f'{i}번째 줄 {w:g}전각 (>{wlim:g} 잘림위험)')
        elif wlim and w > SOFT_WIDTH:
            add('info', 'width_soft', f'{i}번째 줄 {w:g}전각 (>{SOFT_WIDTH:g} 미관여백)')
        if wlim and l and l != l.rstrip():   # 공백 검사는 대사창 섹션만 (sysmsg 등 정렬 제외)
            add('warning', 'trailing_space', f'{i}번째 줄 끝 공백')
        if wlim and l.strip() and l != l.lstrip():
            add('warning', 'leading_space', f'{i}번째 줄 시작 공백')

    # 인코딩: 매핑(2350자) 밖 한글 → SJIS 인코딩 불가
    bad = sorted({c for c in ko if HANGUL.match(c) and c not in kr_map})
    if bad:
        add('error', 'encoding', f'매핑 외 글자: {"".join(bad)}')

    # 일본어 잔존
    if KANA.search(ko):
        add('error', 'jp_kana', f'가나 잔존: {"".join(KANA.findall(ko)[:6])}')
    if JP_PUNCT_HARD.search(ko):
        add('error', 'jp_punct', f'일본 부호(。、): {"".join(sorted(set(JP_PUNCT_HARD.findall(ko))))}')
    if JP_QUOTE.search(ko):
        add('warning', 'jp_quote', f'일본 인용부호: {"".join(sorted(set(JP_QUOTE.findall(ko))))}')
    cjk = sorted(set(CJK.findall(ko)))
    if cjk:
        add('warning', 'cjk_kanji', f'한자 잔존: {"".join(cjk)[:12]}')

    # 줄임표(…)·마침표(.) 뒤 같은 줄에 문장이 이어지면 공백 1칸 규칙.
    # 단 줄 맨 앞 줄임표/마침표(…말줄임으로 시작하는 문장)는 제외.
    for i, l in enumerate(lines, 1):
        for mt in re.finditer(r'[….]', l):
            ch = mt.group(); s = mt.start()
            nxt = l[s+1:s+2]; prev = l[s-1] if s > 0 else ''
            if not nxt or nxt.isspace():
                continue            # 뒤 공백/줄끝 — 정상
            if not (nxt.isalnum() or '가' <= nxt <= '힣'):
                continue            # 뒤가 글자가 아니면(부호·괄호: …! …? …）) 공백 불필요
            if s == 0 or prev.isspace():
                continue            # 문장 시작 줄임표/마침표 (…말 / . …말) — 정상
            if ch == '.' and (nxt.isdigit() or nxt == '.' or prev.isdigit()):
                continue            # 소수점 / '...' 연속
            if ch == '…' and nxt in '….':
                continue            # 나무…. / …… 류
            add('warning', 'punct_space', f'{i}번째 줄 "{ch}" 뒤 공백 없음')
            break

    # 비표준 부호 / 부호 앞 공백
    if re.search(r'(?<!\.)\.\.(?!\.)|！！|？？|，|．', ko):
        add('warning', 'bad_punct', '비표준/연속 부호 의심')
    if re.search(r'[ \t][.,!?](?!\.)', ko):   # 마침표/쉼표/느낌표/물음표 앞 공백 (줄임표 … 제외)
        add('warning', 'space_before_punct', '부호 앞 공백')

    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--section', default='all', help='섹션명 또는 all')
    ap.add_argument('--severity', choices=['error', 'warning', 'info', 'all'], default='all')
    ap.add_argument('--rule', default=None, help='특정 규칙만')
    ap.add_argument('--limit', type=int, default=0, help='샘플 출력 개수')
    ap.add_argument('--json', default=None, help='전체 결과 JSON 경로')
    a = ap.parse_args()

    kr_map = load()
    d = json.load(open(f'{BASE}/translations/jp_messages.json', encoding='utf-8'))
    rows = []
    for sec, c in d.items():
        if a.section != 'all' and sec != a.section:
            continue
        msgs = c['messages'] if isinstance(c, dict) and 'messages' in c else (c if isinstance(c, list) else [])
        for i, m in enumerate(msgs):
            if not isinstance(m, dict):
                continue
            for sev, rule, msg in check(sec, m.get('ja'), m.get('ko'), kr_map):
                if a.severity != 'all' and sev != a.severity:
                    continue
                if a.rule and rule != a.rule:
                    continue
                rows.append({'section': sec, 'id': i, 'severity': sev, 'rule': rule,
                             'message': msg, 'ja': (m.get('ja') or '')[:40],
                             'ko': (m.get('ko') or '').replace('\n', '⏎')[:70]})

    by = Counter((r['severity'], r['rule']) for r in rows)
    cnt = Counter(r['severity'] for r in rows)
    print(f"총 {len(rows)}건 (error {cnt['error']} / warning {cnt['warning']} / info {cnt['info']})")
    order = {'error': 0, 'warning': 1, 'info': 2}
    for (sev, rule), n in sorted(by.items(), key=lambda x: (order.get(x[0][0], 9), -x[1])):
        print(f'  [{sev:7}] {rule:18} {n}')
    if a.json:
        json.dump(rows, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'→ {a.json} ({len(rows)}건)')
    if a.limit:
        print('\n샘플:')
        for r in rows[:a.limit]:
            print(f"  {r['section']}#{r['id']} [{r['severity']}] {r['rule']}: {r['message']}")
            print(f"     ja={r['ja']!r}\n     ko={r['ko']!r}")


if __name__ == '__main__':
    main()
