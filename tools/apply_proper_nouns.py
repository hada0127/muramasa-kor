#!/usr/bin/env python3
"""Apply user edits from translations/proper_nouns.json back into
translations/jp_messages.json.

For each row where `edit` is non-empty:
  - characters_and_scenes: JP match against scename_main + scename
    -> replace `ko`.
  - items: JP match against _itemdata_main + _itemdata -> replace `ko`,
    and cascade into scemsg entries containing the old Korean term
    (word substitution) so dialogue references stay consistent.
  - common_terms: treat `edit` as a global scemsg substitution target,
    replacing `current`.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    pn_path = BASE / 'translations/proper_nouns.json'
    vita_path = BASE / 'translations/jp_messages.json'
    pn = json.loads(pn_path.read_text(encoding='utf-8'))
    vita = json.loads(vita_path.read_text(encoding='utf-8'))

    edits_applied = {'characters': 0, 'items': 0, 'common_terms': 0,
                     'scemsg_cascade': 0}

    # 1) Characters / scenes
    ch_edits = {e['ja']: e['edit'].strip() for e in pn.get('characters_and_scenes', [])
                if e.get('edit', '').strip()}
    for key in ('scename_main', 'scename'):
        if key not in vita:
            continue
        for m in vita[key]['messages']:
            ja = m.get('ja', '')
            if ja in ch_edits:
                m['ko'] = ch_edits[ja]
                edits_applied['characters'] += 1

    # 2) Items — replace in itemdata AND cascade into scemsg text
    item_edits = {e['ja']: (e.get('ko', ''), e['edit'].strip())
                  for e in pn.get('items', []) if e.get('edit', '').strip()}

    # Apply to itemdata files
    for key in ('_itemdata_main', '_itemdata'):
        if key not in vita:
            continue
        for m in vita[key]['messages']:
            ja = m.get('ja', '')
            if ja in item_edits:
                old_ko, new_ko = item_edits[ja]
                m['ko'] = new_ko
                edits_applied['items'] += 1

    # Cascade item name changes into scemsg (dialogue references).
    # Only replace when old Korean name appears as a whole-substring hit.
    scemsg_keys = [k for k in ('scemsg',) if k in vita]
    for ja, (old_ko, new_ko) in item_edits.items():
        if not old_ko or old_ko == new_ko:
            continue
        for key in scemsg_keys:
            for m in vita[key]['messages']:
                ko = m.get('ko', '')
                if old_ko and old_ko in ko:
                    m['ko'] = ko.replace(old_ko, new_ko)
                    edits_applied['scemsg_cascade'] += 1

    # 3) Common-term edits: global find-and-replace across all Korean
    # text (scemsg dialogue + sysmsg + _itemdata + scename).
    all_keys = [k for k in (
        'scemsg', 'sysmsg', 'sysmsg_main',
        '_itemdata', '_itemdata_main',
        'scename', 'scename_main',
    ) if k in vita]
    for entry in pn.get('common_terms', []):
        new = entry.get('edit', '').strip()
        cur = entry.get('current', '').strip()
        if not new or not cur or new == cur:
            continue
        # When `current` lists multiple variants (slash-separated), split.
        targets = [t.strip() for t in cur.split('/') if t.strip()]
        replacements = [r.strip() for r in new.split('/') if r.strip()]
        if len(targets) != len(replacements):
            # Uneven — treat as single term pair
            targets, replacements = [cur], [new]
        # Also include bare last-token variants so e.g.
        # "도쿠가와 쓰나요시"->"도쿠가와 츠나요시" also rewrites standalone
        # "쓰나요시"->"츠나요시". Only do this when the prefix tokens match.
        extra_pairs = []
        for t, r in zip(targets, replacements):
            t_parts = t.split(' ')
            r_parts = r.split(' ')
            if len(t_parts) == len(r_parts) and len(t_parts) > 1:
                for tp, rp in zip(t_parts, r_parts):
                    if tp != rp and tp and rp:
                        extra_pairs.append((tp, rp))
        targets += [p[0] for p in extra_pairs]
        replacements += [p[1] for p in extra_pairs]
        for key in all_keys:
            for m in vita[key]['messages']:
                ko = m.get('ko', '')
                changed = False
                for t, r in zip(targets, replacements):
                    if t and t in ko:
                        ko = ko.replace(t, r); changed = True
                if changed:
                    m['ko'] = ko
                    edits_applied['common_terms'] += 1

    vita_path.write_text(json.dumps(vita, ensure_ascii=False, indent=2),
                         encoding='utf-8')

    print('Applied edits:')
    for k, v in edits_applied.items():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
