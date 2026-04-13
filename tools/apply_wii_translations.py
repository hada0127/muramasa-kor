#!/usr/bin/env python3
"""Apply Wii Korean patch translations to Vita jp_messages.json.

Matching rules:
  - Build Wii JP -> KR map, but SKIP any JP values that appear more than once
    in the Wii file. Those are context-dependent and unsafe to blindly
    remap. Rejected JP values are reported so they can be handled manually
    if needed.
  - For scemsg (dialogue), rewrap Wii KR into <=3 lines / <=18 chars.
  - For sysmsg / _itemdata / scename, preserve the Wii line structure
    as-is (these are short labels or fixed descriptions; forcing a 3-line
    wrap would break save slots, menus, item grids).

Also harvests proper-noun polish set for DLC scemsg via polish_dlc.py.
"""
import json
import re
import sys
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent.parent
DIALOGUE_WIDTH = 18
DIALOGUE_LINES = 3


def wrap_korean(text: str, max_width: int = DIALOGUE_WIDTH,
                max_lines: int = DIALOGUE_LINES) -> str:
    """Wrap Korean text into <= max_lines lines. Used for dialogue only."""
    flat = text.replace('\n', ' ').replace('\r', ' ')
    flat = re.sub(r'\s+', ' ', flat).strip()
    if not flat:
        return ''
    if len(flat) <= max_width:
        return flat
    for w in range(max_width, max_width + 12):
        lines = _greedy_wrap(flat, w)
        if lines is None:
            continue
        if len(lines) <= max_lines:
            return _balance(flat, len(lines), w)
    lines = _greedy_wrap(flat, max_width + 12) or [flat]
    return '\n'.join(lines[:max_lines])


def _greedy_wrap(text: str, width: int):
    words = text.split(' ')
    lines, cur = [], ''
    for word in words:
        if len(word) > width:
            sub = _break_on_punct(word, width)
            if sub is None:
                return None
            for piece in sub:
                if not cur:
                    cur = piece
                elif len(cur) + 1 + len(piece) <= width:
                    cur += ' ' + piece
                else:
                    lines.append(cur); cur = piece
            continue
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += ' ' + word
        else:
            lines.append(cur); cur = word
    if cur:
        lines.append(cur)
    return lines


def _break_on_punct(word: str, width: int):
    out, cur = [], ''
    for ch in word:
        cur += ch
        if ch in '…、．.,!?？！':
            if len(cur) > width:
                return None
            out.append(cur); cur = ''
    if cur:
        if len(cur) > width:
            return None
        out.append(cur)
    return out or None


def _balance(flat: str, n_lines: int, max_w: int) -> str:
    words = flat.split(' ')
    if n_lines <= 1 or len(words) <= 1:
        return flat
    target = len(flat) / n_lines
    lines, wi = [], 0
    for li in range(n_lines):
        remaining = n_lines - li
        rest = words[wi:]
        if not rest:
            break
        if remaining == 1:
            lines.append(' '.join(rest)); wi = len(words); break
        line_words = []
        for w in rest:
            t = ' '.join(line_words + [w])
            if len(t) > max_w:
                break
            if line_words and len(t) > target + 2:
                break
            line_words.append(w)
        if not line_words:
            line_words = [rest[0]]
        lines.append(' '.join(line_words)); wi += len(line_words)
    if wi < len(words):
        lines[-1] += ' ' + ' '.join(words[wi:])
    if all(len(l) <= max_w for l in lines) and len(lines) <= n_lines:
        return '\n'.join(lines)
    return '\n'.join(_greedy_wrap(flat, max_w) or [flat])


def sanitize_wii_kr(text: str) -> str:
    """Normalize Wii KR punctuation to chars known to render on Vita."""
    replacements = {
        '？': '?', '！': '!', '、': ',',
        '『': '「', '』': '」',
        '（': '(', '）': ')',
    }
    for s, d in replacements.items():
        text = text.replace(s, d)
    return text


def build_wii_map(jp_name: str, kr_name: str = None):
    """Return (map_safe, ambiguous_keys).

    map_safe: dict of JP -> KR for JP values that appear EXACTLY once.
    ambiguous_keys: set of JP values appearing >1 (skipped).
    """
    if kr_name is None:
        kr_name = jp_name
    jp = json.loads((BASE / 'wii/messages/jp' / jp_name).read_text(encoding='utf-8'))['strings']
    kr = json.loads((BASE / 'wii/messages/kr' / kr_name).read_text(encoding='utf-8'))['strings']
    counts = Counter(w['shift_jis'] for w in jp)
    ambiguous = {k for k, c in counts.items() if c > 1}
    out = {}
    # For ambiguous JP that always maps to the same KR (e.g. "なし"->"없음" repeated),
    # it's still safe: check if all duplicate KRs agree.
    for idx, w in enumerate(jp):
        jtext = w['shift_jis']
        ktext = kr[idx].get('korean', '')
        if not ktext:
            continue
        if jtext in ambiguous:
            # Only keep if all duplicates agree on the same KR
            continue
        out[jtext] = ktext
    # Second pass: include ambiguous keys whose KR values are all identical
    for jtext in ambiguous:
        idxs = [i for i, v in enumerate(jp) if v['shift_jis'] == jtext]
        ktexts = [kr[i].get('korean', '') for i in idxs if kr[i].get('korean')]
        if ktexts and len(set(ktexts)) == 1:
            out[jtext] = ktexts[0]
    return out, ambiguous


def fit_label(text: str, max_width: int = 20, max_lines: int = None) -> str:
    """Light-touch fit for labels. Keeps natural line breaks.

    If max_lines is given and the result would exceed it, returns None
    (caller should keep the existing translation rather than overflow).
    """
    lines = text.split('\n')
    out = []
    for l in lines:
        if len(l) <= max_width:
            out.append(l); continue
        words = l.split(' ')
        cur, subout = '', []
        for w in words:
            if not cur:
                cur = w
            elif len(cur) + 1 + len(w) <= max_width:
                cur += ' ' + w
            else:
                subout.append(cur); cur = w
        if cur:
            subout.append(cur)
        out.extend(subout)
    if max_lines is not None and len(out) > max_lines:
        return None
    return '\n'.join(out)


def main():
    print(f'Base: {BASE}')
    vita_path = BASE / 'translations/jp_messages.json'
    vita = json.loads(vita_path.read_text(encoding='utf-8'))

    # IMPORTANT alignment check: Wii JP and KR files are only safe to pair
    # by index when counts match. sysmsg is 635 JP vs 677 KR (NOT aligned),
    # so we skip it entirely -- merging its KR by content match produces
    # wrong labels (e.g. "時間" -> "장시간의 대난투").
    maps = {}
    ambig = {}
    maps['scemsg'], ambig['scemsg'] = build_wii_map('scemsg.json')
    maps['_itemdata'], ambig['_itemdata'] = build_wii_map('_itemdata.json')
    maps['scename'], ambig['scename'] = build_wii_map('scename.json', 'scename_US.json')
    # sysmsg intentionally omitted -- file entry counts don't align.

    for k, a in ambig.items():
        print(f'  {k}: {len(maps[k])} safe keys, {len(a)} ambiguous skipped')
    print('  sysmsg: SKIPPED (JP/KR files not index-aligned on Wii)')

    stats = {}
    # Dialogue: rewrap
    for vkey, wkey in [('scemsg', 'scemsg')]:
        msgs = vita[vkey]['messages']
        wmap = maps[wkey]
        n = 0
        for m in msgs:
            ja = m.get('ja', '')
            if ja in wmap:
                new_ko = wrap_korean(sanitize_wii_kr(wmap[ja]),
                                     DIALOGUE_WIDTH, DIALOGUE_LINES)
                if new_ko != m.get('ko', ''):
                    m['ko'] = new_ko; n += 1
        stats[vkey] = (n, len(msgs))

    # Item data / scene names. Only replace when Wii KR fits within the
    # existing message's line budget (don't expand 2-line descriptions
    # into 4 lines).
    for vkey, wkey, line_cap in [
        ('_itemdata', '_itemdata', 2),
        ('_itemdata_main', '_itemdata', 2),
        ('scename', 'scename', 1),
        ('scename_main', 'scename', 1),
    ]:
        if vkey not in vita:
            continue
        wmap = maps[wkey]
        msgs = vita[vkey]['messages']
        n = skipped = 0
        for m in msgs:
            ja = m.get('ja', '')
            old_ko = m.get('ko', '')
            if ja not in wmap:
                continue
            wii_kr = sanitize_wii_kr(wmap[ja])
            # Compute allowed lines: the larger of the Wii KR natural line
            # count and the existing Vita line count, capped at line_cap
            # if existing is short, else existing.
            old_lines = max(1, old_ko.count('\n') + 1)
            allowed = max(old_lines, line_cap)
            new_ko = fit_label(wii_kr, 20, allowed)
            if new_ko is None:
                skipped += 1
                continue
            if new_ko != old_ko:
                m['ko'] = new_ko; n += 1
        stats[vkey] = (n, len(msgs))
        if skipped:
            print(f'  {vkey}: skipped {skipped} entries (Wii KR too long for line cap)')

    vita_path.write_text(json.dumps(vita, ensure_ascii=False, indent=2),
                         encoding='utf-8')

    print('\nReplacements per Vita key:')
    for k, (r, total) in stats.items():
        print(f'  {k}: {r}/{total}')


if __name__ == '__main__':
    main()
