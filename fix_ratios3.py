#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

with open('translations/jp_messages.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

changed = 0

def process_text(text):
    global changed
    if text is None or not isinstance(text, str):
        return text
    original = text
    # Replace ratio expressions - handle newlines
    text = text.replace('일할 ', '10% ')
    text = text.replace('일할\n', '10%\n')
    text = text.replace('일할', '10%')
    text = text.replace('오분 ', '5% ')
    text = text.replace('오분\n', '5%\n')
    text = text.replace('오분', '5%')
    if text != original:
        changed += 1
        return text
    return text

# Process all sections
for section_name in ['scemsg', 'scemsg_patch', 'sysmsg', '_itemdata', 'scename']:
    if section_name in data:
        section = data[section_name]
        if isinstance(section, dict):
            for key, entry in section.items():
                if isinstance(entry, dict) and 'ko' in entry:
                    entry['ko'] = process_text(entry['ko'])

# Save
with open('translations/jp_messages.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Total {changed} entries modified")
