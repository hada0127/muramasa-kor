#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

# jp_messages.json 로드
with open('translations/jp_messages.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 비율 표현 변환
changed = 0
changes = []

def process_text(text):
    global changed
    if text is None or not isinstance(text, str):
        return text
    original = text
    # Replace ratio expressions
    text = text.replace('일할 ', '10% ')
    text = text.replace('일할\n', '10%\n')
    text = text.replace('일할', '10%')
    text = text.replace('오분 ', '5% ')
    text = text.replace('오분\n', '5%\n')
    text = text.replace('오분', '5%')
    if text != original:
        changed += 1
        changes.append((original[:60], text[:60]))
    return text

# 모든 섹션 순회
for section in ['scemsg', 'sysmsg', 'itemdata', 'skilldata', 'scename']:
    if section in data and isinstance(data[section], list):
        for entry in data[section]:
            if 'ko' in entry:
                entry['ko'] = process_text(entry['ko'])

# 저장
with open('translations/jp_messages.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 결과 출력
print(f"Total {changed} entries modified")
for orig, new in changes[:5]:
    print(f"  {orig} → {new}")
if len(changes) > 5:
    print(f"  ... and {len(changes)-5} more")
