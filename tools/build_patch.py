#!/usr/bin/env python3
"""
Build Korean patch for Muramasa Rebirth.
Converts translated messages to NMS format using Korean→Shift-JIS remapping.

Creates separate patches for NinPri (main) and NinPriPatch (patch) CPKs,
using the correct original NMS files as templates for each.
"""

import json
import struct
import os
from pathlib import Path


def load_mapping(mapping_path: str) -> dict:
    """Load Korean→Shift-JIS character mapping."""
    with open(mapping_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['korean_to_sjis']


def _build_ascii_sjis_map():
    """Map ASCII chars to SJIS 2-byte codes at texture positions 960+.

    Game renders ASCII from KANJI texture at position=192+code, which overlaps
    Korean glyphs. Remap ASCII to positions 960+ (beyond Korean range 0-959).
    """
    ascii_map = {}
    pos = 960
    # Codes kept as raw 1-byte so the game renders them half-width at
    # cell 192+code. Those cells are drawn by font_import's RUNTIME_OVERLAY.
    # 0x20 (space) — cell 224, cleared transparent.
    # 0x2E (period) — cell 238, overlay draws '.'.
    HALFWIDTH_CODES = {0x20, 0x2E}
    for code in range(0x20, 0x7F):  # space to ~
        if code in HALFWIDTH_CODES:
            pos += 1
            continue
        cell = 1644 + pos
        b1 = 0x81 + cell // 188
        b2_offset = cell % 188
        b2 = (0x40 + b2_offset) if b2_offset < 63 else (0x41 + b2_offset)
        ascii_map[chr(code)] = (b1, b2)
        pos += 1
    return ascii_map

ASCII_SJIS_MAP = _build_ascii_sjis_map()


# Full-width and punctuation chars that would otherwise be encoded to raw SJIS
# 0x81xx/0x82xx — those bytes get rendered at texture cells 448+ where we placed
# Korean glyphs, producing visible garbling (e.g. "："→"봐", "（"→"사", "1"→"웨").
# Normalize to ASCII equivalents so they go through ASCII_SJIS_MAP (pos 960+)
# which has correct glyphs drawn by auto_font_import.py / hd_font_import.py.
FULLWIDTH_NORMALIZE = {
    # Full-width ASCII punctuation
    '\uFF1A': ':', '\uFF08': '(', '\uFF09': ')', '\uFF01': '!', '\uFF1F': '?',
    '\uFF05': '%', '\uFF0B': '+', '\uFF0D': '-', '\uFF1D': '=', '\uFF0F': '/',
    '\uFF0A': '*', '\uFF03': '#', '\uFF06': '&', '\uFF20': '@', '\uFF04': '$',
    '\uFF3E': '^', '\uFF1C': '<', '\uFF1E': '>', '\uFF3B': '[', '\uFF3D': ']',
    '\uFF5B': '{', '\uFF5D': '}', '\uFF5C': '|', '\uFF5E': '~',
    '\uFF0C': ',', '\uFF0E': '.', '\uFF1B': ';', '\uFF40': '`',
    # Full-width digits
    '\uFF10': '0', '\uFF11': '1', '\uFF12': '2', '\uFF13': '3', '\uFF14': '4',
    '\uFF15': '5', '\uFF16': '6', '\uFF17': '7', '\uFF18': '8', '\uFF19': '9',
    # Japanese/CJK punctuation → nearest ASCII
    '\u3001': ',',    # 、 ideographic comma
    '\u3002': '.',    # 。 ideographic period
    '\u30FB': '.',    # ・ katakana middle dot → period
    '\u300C': '[',    # 「 left corner bracket
    '\u300D': ']',    # 」 right corner bracket
    '\u300E': '[',    # 『 left white corner bracket
    '\u300F': ']',    # 』 right white corner bracket
    '\u3000': ' ',    # ideographic space → ASCII space
    '\u2026': '...',  # … horizontal ellipsis → 3 dots
    '\u25C6': '*',    # ◆ black diamond
}


def _normalize_text(text: str) -> str:
    """Apply full-width → ASCII normalization before SJIS encoding."""
    out = []
    for c in text:
        out.append(FULLWIDTH_NORMALIZE.get(c, c))
    return ''.join(out)


# Unmapped Korean syllable → nearest mappable syllable. Generated from
# translations/char_substitutions.json. Without this, unmapped chars fall
# through to `?` (0x3F), which renders as `등` through the Korean atlas at
# cell 255, producing dialogue corruption (e.g. `따윈 요만큼도` → `따등요만큼도`).
_CHAR_SUBS_CACHE = None
def _load_char_subs():
    global _CHAR_SUBS_CACHE
    if _CHAR_SUBS_CACHE is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                            'translations', 'char_substitutions.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                _CHAR_SUBS_CACHE = json.load(f)
        else:
            _CHAR_SUBS_CACHE = {}
    return _CHAR_SUBS_CACHE


def encode_korean_to_sjis(text: str, kr_map: dict) -> bytes:
    """Encode Korean text using the character mapping table.

    Format specifiers (%s, %4s, %2d, %D, etc.) and control codes
    (@#(xx), @c(x)) are kept as raw ASCII so the game engine can parse them.

    Full-width punctuation/digits are normalized to ASCII half-width first so
    they land in the ASCII_SJIS_MAP overflow region (texture cells 960+)
    rather than rendering as Korean glyphs at cells 448+.
    """
    import re
    text = _normalize_text(text)
    result = bytearray()
    i = 0
    while i < len(text):
        c = text[i]

        # Format specifiers: %s, %d, %D, %2d, %4s, %8s, etc.
        if c == '%':
            m = re.match(r'%-?\d*[sdDf]', text[i:])
            if m:
                for ch in m.group():
                    result.append(ord(ch))
                i += len(m.group())
                continue

        # Control codes: @#(xx), @c(r,g,b), @/c, @/# etc.
        # After normalization, full-width '（）' become '()' so the half-width
        # regex covers both original forms.
        if c == '@':
            m = re.match(r'@[#c]\(\d+(?:,\d+)*\)|@/[#c]', text[i:])
            if m:
                for ch in m.group():
                    result.append(ord(ch))
                i += len(m.group())
                continue

        if c in kr_map:
            b1, b2 = kr_map[c]
            result.extend([b1, b2])
        elif c in ASCII_SJIS_MAP:
            b1, b2 = ASCII_SJIS_MAP[c]
            result.extend([b1, b2])
        elif ord(c) < 0x80:
            result.append(ord(c))  # control chars (\n etc.) stay as-is
        else:
            # Try Korean → nearest-mapped substitution before falling back to SJIS
            subs = _load_char_subs()
            if c in subs and subs[c] in kr_map:
                b1, b2 = kr_map[subs[c]]
                result.extend([b1, b2])
            else:
                try:
                    result.extend(c.encode('shift_jis'))
                except:
                    result.extend(b'?')
        i += 1
    return bytes(result)


def parse_nms_raw(filepath: str):
    """Parse NMSB file and return raw bytes for each message + text section bounds."""
    with open(filepath, 'rb') as f:
        data = f.read()

    if data[:4] != b'NMSB':
        raise ValueError(f"Not an NMSB file: {filepath}")

    header_size = struct.unpack('<I', data[0x08:0x0C])[0]
    entry_count = struct.unpack('<I', data[0x14:0x18])[0]

    text_start = header_size + entry_count * 4
    while text_start < len(data) and data[text_start] == 0:
        text_start += 1

    # Extract messages as (raw_bytes, decoded_text) pairs
    messages = []
    i = text_start
    while i < len(data):
        if data[i:i+4] == b'FEOC':
            break
        if data[i] != 0:
            start = i
            while i < len(data) and data[i] != 0:
                i += 1
            raw = data[start:i]
            text = raw.decode('shift_jis', errors='replace')
            messages.append((raw, text))
        i += 1

    # Capture the exact original text section (including null terminators)
    feoc_pos = data.find(b'FEOC')
    if feoc_pos == -1:
        # No FEOC marker - text section goes to end of file
        feoc_pos = len(data)
    original_text_section = data[text_start:feoc_pos]

    return messages, data, text_start, original_text_section


def rebuild_nms(original_path: str, translated_msgs: list, kr_map: dict, output_path: str, match_mode: str = 'content', jp_source_path: str = None, index_range: tuple = None, skip_indices: set = None, custom_idx_to_ko: dict = None):
    """Rebuild NMS file, preserving exact original structure.

    Only replaces messages that have Korean translations.
    Unmatched messages keep their EXACT original bytes (no re-encoding).

    match_mode:
      'content' - match by Japanese text content
      'index' - match by position in translated_msgs list
      'jp_index' - content-match against jp_source_path, apply by matched index
      'copy' - copy original bytes verbatim, no translation applied
      'index_range' - like 'index' but limited to [range_start, range_end)
    """
    if match_mode == 'copy':
        # Pass-through: copy original file to output unchanged
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(original_path, 'rb') as f:
            data = f.read()
        with open(output_path, 'wb') as f:
            f.write(data)
        return 0, 0, len(data)

    # 'index_range' restricts index-mode patching to [start, end)
    range_start = None
    range_end = None
    if match_mode == 'index_range':
        if index_range is None:
            raise ValueError("index_range mode requires index_range=(start, end)")
        range_start, range_end = index_range
        match_mode = 'index'
    # 'custom_idx' uses a pre-built {idx: korean_text} dict
    if match_mode == 'custom_idx':
        if not custom_idx_to_ko:
            raise ValueError("custom_idx mode requires custom_idx_to_ko dict")
        idx_to_ko_override = custom_idx_to_ko
        match_mode = 'index'
    else:
        idx_to_ko_override = None

    messages, original, text_start, orig_text_section = parse_nms_raw(original_path)
    orig_count = len(messages)

    # Build translation lookup based on match mode
    # Normalize CRLF/LF line endings — different NMS sources use different line endings,
    # but our JSON has a single canonical form per entry. Normalize both sides to \n.
    def _norm(s):
        return s.replace('\r\n', '\n') if s else s

    if match_mode == 'jp_index' and jp_source_path:
        # Match translations against JP source by content; then map JP index -> US index
        # by skipping whitespace-only JP entries (US NMS omits those placeholders).
        jp_messages, _, _, _ = parse_nms_raw(jp_source_path)
        ja_to_ko = {}
        for msg in translated_msgs:
            ja = _norm(msg.get('ja', ''))
            ko = msg.get('ko', '')
            if ja and ko:
                ja_to_ko[ja] = ko

        # Build JP index -> US index map by walking JP entries and counting skips
        def _is_empty(s):
            return not s or s.strip('\u3000 \n\r\t') == ''
        jp_to_us = {}
        us_idx = 0
        for jp_i, (_, jp_text) in enumerate(jp_messages):
            if _is_empty(jp_text):
                continue  # US skipped this placeholder
            jp_to_us[jp_i] = us_idx
            us_idx += 1

        # idx_to_ko: US index -> Korean text (via JP content match)
        idx_to_ko = {}
        for jp_i, (_, jp_text) in enumerate(jp_messages):
            key = _norm(jp_text)
            if key in ja_to_ko and jp_i in jp_to_us:
                idx_to_ko[jp_to_us[jp_i]] = ja_to_ko[key]
        match_mode = 'index'  # now use index mode with the correct US-index mapping
    elif match_mode == 'index':
        if idx_to_ko_override is not None:
            idx_to_ko = dict(idx_to_ko_override)
        else:
            # Index-based: translate by position (JP msg[i] → KR for US msg[i])
            idx_to_ko = {}
            for idx, msg in enumerate(translated_msgs):
                ko = msg.get('ko', '')
                if ko:
                    idx_to_ko[idx] = ko
        if range_start is not None:
            idx_to_ko = {k: v for k, v in idx_to_ko.items()
                         if range_start <= k < range_end}
        if skip_indices:
            idx_to_ko = {k: v for k, v in idx_to_ko.items()
                         if k not in skip_indices}
    else:
        # Content-based: match by Japanese text
        ja_to_ko = {}
        for msg in translated_msgs:
            ja = _norm(msg.get('ja', ''))
            ko = msg.get('ko', '')
            if ja and ko:
                ja_to_ko[ja] = ko

    # Rebuild text section: replace only Korean-matched messages
    matched = 0
    new_parts = []
    i = 0
    msg_idx = 0
    while i < len(orig_text_section):
        if orig_text_section[i] == 0:
            new_parts.append(b'\x00')
            i += 1
            continue

        # Found start of a message
        start = i
        while i < len(orig_text_section) and orig_text_section[i] != 0:
            i += 1
        orig_raw = orig_text_section[start:i]

        if msg_idx < orig_count:
            if match_mode == 'index':
                if msg_idx in idx_to_ko:
                    new_parts.append(encode_korean_to_sjis(idx_to_ko[msg_idx], kr_map))
                    matched += 1
                else:
                    new_parts.append(orig_raw)
            else:
                _, decoded_text = messages[msg_idx]
                key = _norm(decoded_text)
                if key in ja_to_ko:
                    new_parts.append(encode_korean_to_sjis(ja_to_ko[key], kr_map))
                    matched += 1
                else:
                    new_parts.append(orig_raw)
            msg_idx += 1
        else:
            new_parts.append(orig_raw)

    new_text = b''.join(new_parts)

    # Check if original had FEOC
    has_feoc = b'FEOC' in original

    # FEOC footer (no alignment padding - match original structure)
    feoc = b'FEOC\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00' if has_feoc else b''

    # Keep original header
    header_size = struct.unpack('<I', original[0x08:0x0C])[0]
    header = bytearray(original[:text_start])

    # Update data_size = offset_table_size + text_section_size (excludes header and FEOC)
    new_data_size = (text_start - header_size) + len(new_text)
    struct.pack_into('<I', header, 0x04, new_data_size)

    result = bytes(header) + new_text + feoc

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(result)

    return orig_count, matched, len(result)


def build_korean_patch():
    """Build the complete Korean patch."""
    base_dir = Path(__file__).parent.parent
    translations_dir = base_dir / 'translations'

    with open(translations_dir / 'jp_messages.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)

    kr_map = load_mapping(translations_dir / 'kr_sjis_mapping.json')

    print("Building Korean patch...")
    print(f"Character mapping: {len(kr_map)} Korean chars")

    # === patch_main: goes into NinPri.cpk ===
    # Use NinPri originals as templates
    main_files = {
        'scemsg': {
            'source': 'extracted/NinPri/msgsheet/scemsg.nms',
            'output': 'patch_main/msgsheet/scemsg.nms',
            'trans_key': 'scemsg',
        },
        'scemsg_US': {
            'source': 'extracted/NinPri/_US/msgsheet/scemsg.nms',
            'output': 'patch_main/_US/msgsheet/scemsg.nms',
            'trans_key': 'scemsg',
            'match_mode': 'index',  # US is English, match by index
        },
        'sysmsg': {
            'source': 'extracted/NinPri/msgsheet/sysmsg.nms',
            'output': 'patch_main/msgsheet/sysmsg.nms',
            'trans_key': 'sysmsg_main',
        },
        'sysmsg_US': {
            'source': 'extracted/NinPri/_US/msgsheet/sysmsg.nms',
            'output': 'patch_main/_US/msgsheet/sysmsg.nms',
            'trans_key': 'sysmsg_main',
            'match_mode': 'index',  # US text ≠ JP text, match by index
        },
        '_itemdata': {
            'source': 'extracted/NinPri/msgsheet/_itemdata.nms',
            'output': 'patch_main/msgsheet/_itemdata.nms',
            'trans_key': '_itemdata_main',
        },
        '_itemdata_US': {
            'source': 'extracted/NinPri/_US/msgsheet/_itemdata.nms',
            'output': 'patch_main/_US/msgsheet/_itemdata.nms',
            'trans_key': '_itemdata_main',
            'match_mode': 'index',
        },
        'scename': {
            'source': 'extracted/NinPri/msgsheet/scename.nms',
            'output': 'patch_main/msgsheet/scename.nms',
            'trans_key': 'scename_main',
        },
        'scename_US': {
            'source': 'extracted/NinPri/_US/msgsheet/scename_US.nms',
            'output': 'patch_main/_US/msgsheet/scename_US.nms',
            'trans_key': 'scename_main',
            'match_mode': 'index',
        },
    }

    # === patch_patch: goes into NinPriPatch.cpk ===
    # NinPriPatch is the UPDATE PATCH that overrides NinPri base files.
    # scemsg: use FULL extracted files (NinPriPatch_full) with 2000+ messages,
    #         NOT the broken small extraction (NinPriPatch).
    # Other files: use NinPriPatch originals as before.
    patch_files = {}
    for name in ['scemsg', 'sysmsg', '_itemdata', 'scename', 'staffroll', 'lyricmsg']:
        # scemsg: use full extraction from NinPriPatch (update patch overrides base)
        if name == 'scemsg':
            src_jp = 'extracted/NinPriPatch_full/msgsheet/scemsg_full.nms'
            src_us = 'extracted/NinPriPatch_full/_US/msgsheet/scemsg_full.nms'
            trans_key = 'scemsg'  # Use main scemsg translations (content match)
        else:
            src_jp = f'extracted/NinPriPatch/msgsheet/{name}.nms'
            src_us = f'extracted/NinPriPatch/_US/msgsheet/{name}.nms'
            trans_key = name
        out_name = name if name != 'scename' else 'scename_US'

        if os.path.exists(str(base_dir / src_jp)):
            patch_files[name] = {
                'source': src_jp,
                'output': f'patch_patch/msgsheet/{name}.nms',
                'trans_key': trans_key,
                'match_mode': 'content',
            }
        # _US: match via JP content → apply by index (jp_index mode for scemsg)
        us_path = str(base_dir / src_us)
        if os.path.exists(us_path):
            us_entry = {
                'source': src_us,
                'output': f'patch_patch/_US/msgsheet/{out_name}.nms',
                'trans_key': trans_key,
            }
            if name == 'scemsg':
                # scemsg: content-match against JP source, apply by matched index
                us_entry['match_mode'] = 'jp_index'
                us_entry['jp_source'] = src_jp
            elif name == '_itemdata':
                # US _itemdata.nms has a hybrid layout:
                #   0-369  : items + descriptions (align with JP _itemdata)
                #   370-593: blade name/description pairs (even=name, odd=desc)
                #   594    : separator '-'
                #   595-1176: COMPACT English skill-name table
                #             (NinPriPatch US[i] = _itemdata_main[i-8], +8 shift)
                # Build explicit idx_to_ko:
                #  • [0, 594) ∩ ¬skip_odd_blade_desc : _itemdata[i].ko
                #  • [595, 1177): _itemdata_main[i-8].ko
                us_entry['match_mode'] = 'custom_idx'
                us_entry['custom_idx_builder'] = 'us_itemdata_hybrid'
            else:
                us_entry['match_mode'] = 'index'
            patch_files[f'{name}_US'] = us_entry
        elif os.path.exists(str(base_dir / src_jp)):
            patch_files[f'{name}_US'] = {
                'source': src_jp,
                'output': f'patch_patch/_US/msgsheet/{out_name}.nms',
                'trans_key': trans_key,
                'match_mode': 'content',
            }

    print("\n=== patch_main (NinPri.cpk) ===")
    for name, info in main_files.items():
        source_path = str(base_dir / info['source'])
        output_path = str(base_dir / info['output'])
        trans_key = info['trans_key']

        if not os.path.exists(source_path):
            print(f"  {name}: SKIP (source not found)")
            continue
        if trans_key not in translations:
            print(f"  {name}: SKIP (no translations)")
            continue

        msgs = translations[trans_key]['messages']
        mode = info.get('match_mode', 'content')
        try:
            count, matched, size = rebuild_nms(source_path, msgs, kr_map, output_path, match_mode=mode)
            print(f"  {name}: {matched}/{count} matched ({mode}), {size} bytes")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")

    print("\n=== patch_patch (NinPriPatch.cpk) ===")
    for name, info in patch_files.items():
        source_path = str(base_dir / info['source'])
        output_path = str(base_dir / info['output'])
        trans_key = info['trans_key']
        mode = info.get('match_mode', 'content')

        if not os.path.exists(source_path):
            continue
        if trans_key not in translations:
            continue

        msgs = translations[trans_key]['messages']
        jp_src = str(base_dir / info['jp_source']) if 'jp_source' in info else None
        idx_range = info.get('index_range')
        skip_idx = info.get('skip_indices')
        custom_idx_ko = None
        if info.get('custom_idx_builder') == 'us_itemdata_hybrid':
            # Build US _itemdata hybrid translation map:
            #  • [0, 594)     : _itemdata[i].ko (all — blade descriptions too)
            #  • [595, 1177)  : _itemdata_main[i-8].ko  (empirically verified +8 shift)
            # Blade descriptions at odd 371-593 used to be skipped because the
            # Ability screen parser found 'Secret Art: …' markers in the English
            # text. After shipping the skill-name table in Korean at 595-1176,
            # the Ability screen reads skills by ID directly (confirmed by user),
            # so Korean blade descriptions are safe and needed for Forge/Equip
            # detail screens.
            main_msgs = translations.get('_itemdata_main', {}).get('messages', [])
            custom_idx_ko = {}
            for i in range(0, 594):
                if i >= len(msgs):
                    continue
                ko = msgs[i].get('ko', '')
                if ko:
                    custom_idx_ko[i] = ko
            for i in range(595, 1177):
                main_i = i - 8
                if 0 <= main_i < len(main_msgs):
                    ko = main_msgs[main_i].get('ko', '')
                    if ko:
                        custom_idx_ko[i] = ko
        try:
            count, matched, size = rebuild_nms(source_path, msgs, kr_map, output_path, match_mode=mode, jp_source_path=jp_src, index_range=idx_range, skip_indices=skip_idx, custom_idx_to_ko=custom_idx_ko)
            print(f"  {name}: {matched}/{count} matched ({mode}), {size} bytes")
        except Exception as e:
            print(f"  {name}: ERROR - {e}")

    print("\nBuild complete!")


if __name__ == '__main__':
    build_korean_patch()
