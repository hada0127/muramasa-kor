#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 분석 기반 현대 표현 수정
"""
import json

# 수정할 항목들 (ID -> {ko_current, ko_new})
FIXES = {
    365: {
        'current': '새벽 2시',
        'new': '축시(丑時)',
        'reason': '시대적 배경에 맞는 시간 단위'
    },
    371: {
        'current': '퇴직금',
        'new': '전별금',
        'reason': '현대 기업 용어 → 전별금'
    },
    18: {
        'current': '감동했습니다',
        'new': '감탄하였사옵니다',
        'reason': '현대적 경어 → 에도 시대 경어'
    },
    6: {
        'current': '소란 떨기는',
        'new': '호들갑이구려',
        'reason': '현대 구어 → 시대극 톤'
    },
    11: {
        'current': '사양이야',
        'new': '사양하겠노라',
        'reason': '현대 일상어 → 문어체 강화'
    },
    139: {
        'current': '기분 나쁜',
        'new': '흉측한',
        'reason': '현대 형용사 → 시대적 표현'
    },
    324: {
        'current': '취급하면 곤란하다',
        'new': '취급하지 마라',
        'reason': '일본어 직역 → 한국어 고어체'
    },
    127: {
        'current': '가지 않으면 안돼',
        'new': '가야만 한다',
        'reason': '일본어 직역 부정 → 한국어 고어'
    },
    20: {
        'current': '만담',
        'new': '재담',
        'reason': '근현대 용어 → 에도 시대 용어'
    },
    113: {
        'current': '울 거야',
        'new': '울게 될 터',
        'reason': '현대 구어 → 고어체'
    },
}

with open('translations/jp_messages.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

changed = 0

# scemsg 섹션 수정
if 'scemsg' in data and 'messages' in data['scemsg']:
    for entry in data['scemsg']['messages']:
        entry_id = entry.get('id')
        if entry_id in FIXES:
            fix = FIXES[entry_id]
            ko = entry.get('ko', '')

            # 현재 값에서 수정할 부분을 찾아 교체
            if fix['current'] in ko:
                original = ko
                new_ko = ko.replace(fix['current'], fix['new'])
                entry['ko'] = new_ko
                changed += 1
                print(f"[scemsg #{entry_id}]")
                print(f"  Before: {original[:80]}")
                print(f"  After:  {new_ko[:80]}")
                print(f"  Reason: {fix['reason']}\n")

# 저장
with open('translations/jp_messages.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nTotal: {changed} entries modified")
