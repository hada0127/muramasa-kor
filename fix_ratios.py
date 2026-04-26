#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re

# jp_messages.json 로드
with open('translations/jp_messages.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 비율 표현 변환
def fix_ratios(text):
    if text is None:
        return text
    # 일할 → 10%, 오분 → 5%
    text = re.sub(r'일할\s', '10% ', text)
    text = re.sub(r'일할$', '10%', text)
    text = re.sub(r'오분\s', '5% ', text)
    text = re.sub(r'오분$', '5%', text)
    return text

# 모든 섹션 순회
changed = 0
changes = []
for section in ['scemsg', 'sysmsg', 'itemdata', 'skilldata', 'scename']:
    if section in data and isinstance(data[section], list):
        for entry in data[section]:
            if 'ko' in entry:
                original = entry['ko']
                entry['ko'] = fix_ratios(entry['ko'])
                if entry['ko'] != original:
                    changed += 1
                    changes.append(f"Changed: {original[:60]} → {entry['ko'][:60]}")

# 저장
with open('translations/jp_messages.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 결과 출력
for change in changes[:10]:
    print(change)
if len(changes) > 10:
    print(f"... and {len(changes)-10} more")
print(f"\nTotal {changed} entries modified")
