#!/usr/bin/env python3
"""Export a proper-noun dictionary as JSON for human review.

Output: translations/proper_nouns.json

Layout:
    {
      "_readme": "...",
      "characters_and_scenes": [...],   # from scename
      "items": [...],                   # short entries from _itemdata
      "common_terms": [...]             # places/groups recurring in scemsg
    }

Each entry: { "ja": ..., "ko": ..., "wii_kr": ..., "edit": "" }

Edit the `edit` field to override the current Korean. Run
`tools/apply_proper_nouns.py` to apply edits back into jp_messages.json.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def load_wii_map(jp_file: str, kr_file: str):
    jp = json.loads((BASE / 'wii/messages/jp' / jp_file).read_text(encoding='utf-8'))['strings']
    kr = json.loads((BASE / 'wii/messages/kr' / kr_file).read_text(encoding='utf-8'))['strings']
    out = {}
    for j, k in zip(jp, kr):
        jt = j.get('shift_jis', '')
        kt = k.get('korean', '')
        if jt and kt and jt not in out:
            out[jt] = kt
    return out


def main():
    vita = json.loads((BASE / 'translations/jp_messages.json').read_text(encoding='utf-8'))
    sce_map = load_wii_map('scename.json', 'scename_US.json')
    item_map = load_wii_map('_itemdata.json', '_itemdata.json')

    # 1) Characters / scenes (from scename_main)
    characters = []
    for m in vita['scename_main']['messages']:
        ja = (m.get('ja') or '').strip()
        ko = (m.get('ko') or '').strip()
        if not ja:
            continue
        characters.append({
            'ja': ja,
            'ko': ko,
            'wii_kr': sce_map.get(ja, ''),
            'edit': '',
        })

    # 2) Item names — short _itemdata entries that look like labels
    items = []
    seen = set()
    for m in vita['_itemdata_main']['messages']:
        ja = (m.get('ja') or '').strip()
        ko = (m.get('ko') or '').strip()
        if not ja or ja in seen:
            continue
        if '\n' in ja or len(ja) > 14:
            continue
        if ja.startswith('@#(') or ja in ('なし', '＜説明なし＞'):
            continue
        seen.add(ja)
        items.append({
            'ja': ja,
            'ko': ko,
            'wii_kr': item_map.get(ja, ''),
            'edit': '',
        })

    # 3) Common terms (places/groups/honorifics harvested by hand during
    # Wii merge). Editable by user — applied to DLC scemsg entries.
    common_terms = [
        {'term': '해골 골짜기 vs 해골곡', 'ja_note': '髑髏谷', 'current': '해골곡', 'edit': ''},
        {'term': '카가미 가문 vs 카가미가', 'ja_note': '鏡家', 'current': '카가미가', 'edit': ''},
        {'term': '사무라이 vs 무사', 'ja_note': '侍', 'current': '무사', 'edit': ''},
        {'term': '주군님 vs 주군', 'ja_note': '御館様', 'current': '주군', 'edit': ''},
        {'term': '규율 vs 규칙', 'ja_note': '掟', 'current': '규칙', 'edit': ''},
        {'term': '관념해라 vs 단념해라', 'ja_note': '観念せい', 'current': '단념해라', 'edit': ''},
        {'term': '막걸리 vs 도부로쿠', 'ja_note': 'どぶろく', 'current': '도부로쿠', 'edit': ''},
        {'term': '감 vs 홍시', 'ja_note': '柿', 'current': '홍시', 'edit': ''},
        {'term': '귤 vs 밀감', 'ja_note': '蜜柑', 'current': '밀감', 'edit': ''},
        {'term': '어신주 vs 신령주', 'ja_note': 'お神酒', 'current': '신령주', 'edit': ''},
        {'term': '치유환/회복환/웅담환 vs *환약', 'ja_note': '~丸', 'current': '치료환약/회복환약/곰환약', 'edit': ''},
        {'term': '시카미 단조 vs 시카미 단죠', 'ja_note': '鹿見団蔵', 'current': '시카미 단죠', 'edit': ''},
        {'term': '도쿠가와 츠나요시 vs 쓰나요시', 'ja_note': '徳川綱吉', 'current': '도쿠가와 쓰나요시', 'edit': ''},
        {'term': '피에 미친 비사문 vs 치구루이비샤몬', 'ja_note': '血狂毘沙門', 'current': '치구루이비샤몬', 'edit': ''},
        {'term': '호넨 vs 호우넨', 'ja_note': '法然', 'current': '호우넨', 'edit': ''},
    ]

    out = {
        '_readme': (
            'Proper-noun review file. Edit the `edit` field of any row to '
            'override the Korean translation. Leave blank to keep `ko`. '
            "Run tools/apply_proper_nouns.py after editing."
        ),
        'counts': {
            'characters_and_scenes': len(characters),
            'items': len(items),
            'common_terms': len(common_terms),
        },
        'characters_and_scenes': characters,
        'items': items,
        'common_terms': common_terms,
    }

    out_path = BASE / 'translations/proper_nouns.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                        encoding='utf-8')
    print(f'Wrote {out_path}')
    for k, v in out['counts'].items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
