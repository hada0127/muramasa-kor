#!/usr/bin/env python3
"""Polish DLC scemsg entries with proper nouns/terms harvested from
Wii-based main story edits.

Runs AFTER apply_wii_translations.py. Harvests 1:1 token remaps from
changes in scename_main / _itemdata_main (which are dominated by
proper nouns), then applies them to scemsg DLC entries (those with
no direct Wii match).
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MAX_WIDTH = 18
MAX_LINES = 3

sys.path.insert(0, str(BASE / 'tools'))
from apply_wii_translations import wrap_korean


# Manually curated proper-noun/term dictionary harvested from
# scename_main and _itemdata_main before/after diffs. Longest keys
# first so we don't partially replace inside longer names.
TERM_MAP = [
    # Place / group
    ('해골 골짜기', '해골곡'),
    ('카가미 가문', '카가미가'),
    ('카가미 연고의 무사', '카가미가 무사'),
    # People (romanization harmonized to Wii style)
    ('도쿠가와 츠나요시', '도쿠가와 쓰나요시'),
    ('피에 미친 비사문', '치구루이비샤몬'),
    ('오보로요 센쥬의 영혼', '오보로요 센쥬의 령'),
    ('시카미 단조', '시카미 단죠'),
    ('하치쥬하치', '야소하치'),
    ('세이시 보살', '세지보살'),
    ('관음 보살', '관음보살'),
    ('아미타 여래', '아미타여래'),
    ('호넨', '호우넨'),
    # Common nouns
    ('사무라이', '무사'),
    ('여랑 유령', '유녀귀신'),
    ('기다리는 손님', '대기객'),
    ('소승', '동자승'),
    ('장사 동료', '상인'),
    # Items (from _itemdata_main)
    ('어신주', '신령주'),
    ('막걸리', '도부로쿠'),
    ('치유환', '치료환약'),
    ('회복환', '회복환약'),
    ('웅담환', '곰환약'),
    ('호담환', '호담환약'),
    ('용뇌환', '용뇌환약'),
    ('신선환', '신선환약'),
    # Formal tone softening matching Wii register
    ('주군님', '주군'),
    ('규율', '규칙'),
    ('관념해라', '단념해라'),
]


def apply_terms(text: str) -> str:
    # Longest-first replacement is guaranteed by list order above.
    out = text
    for src, dst in TERM_MAP:
        out = out.replace(src, dst)
    return out


def needs_rewrap(text: str) -> bool:
    lines = text.split('\n')
    if len(lines) > MAX_LINES:
        return True
    return any(len(l) > MAX_WIDTH + 3 for l in lines)


def main():
    path = BASE / 'translations/jp_messages.json'
    data = json.loads(path.read_text(encoding='utf-8'))

    # Wii JP set (already-replaced entries) -- skip those, they came from Wii.
    wii_jp = json.loads((BASE / 'wii/messages/jp/scemsg.json').read_text(encoding='utf-8'))['strings']
    wii_jp_set = set(w['shift_jis'] for w in wii_jp)

    changed = 0
    for m in data['scemsg']['messages']:
        ja = m.get('ja', '')
        if ja in wii_jp_set:
            continue
        ko = m.get('ko', '')
        if not ko:
            continue
        new_ko = apply_terms(ko)
        if new_ko != ko:
            if needs_rewrap(new_ko):
                new_ko = wrap_korean(new_ko, MAX_WIDTH, MAX_LINES)
            m['ko'] = new_ko
            changed += 1

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'DLC scemsg entries polished: {changed}')


if __name__ == '__main__':
    main()
