#!/usr/bin/env python3
"""Rewrap all Korean scemsg entries to <=3 lines, <=18 chars where possible.

Allows gradual width relaxation (18 -> 29) when the text can't fit
3 lines at narrower widths. Never exceeds 3 lines.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'tools'))
from apply_wii_translations import wrap_korean


def main():
    path = BASE / 'translations/jp_messages.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    total, rewrapped = 0, 0
    over_count = 0
    max_w = 0
    for m in data['scemsg']['messages']:
        ko = m.get('ko', '')
        if not ko:
            continue
        total += 1
        new_ko = wrap_korean(ko, 18, 3)
        # Collect stats
        for l in new_ko.split('\n'):
            if len(l) > 18:
                over_count += 1
            if len(l) > max_w:
                max_w = len(l)
        if new_ko != ko:
            m['ko'] = new_ko
            rewrapped += 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'scemsg total: {total}, rewrapped: {rewrapped}')
    print(f'Lines > 18 chars after wrap: {over_count}')
    print(f'Max line chars: {max_w}')


if __name__ == '__main__':
    main()
