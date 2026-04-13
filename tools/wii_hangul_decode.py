"""Wii Muramasa Korean patch — SJIS to Hangul decoder.

Formula reverse-engineered from the Wii Korean patch:
- Hangul start: SJIS 0x89CD = 가 (KS X 1001 index 0)
- For b1 = 0x89: KS_idx = b2 - 0xCD (valid range: 0xCD-0xFC, 48 chars)
- For b1 >= 0x8A: KS_idx = 48 + (b1 - 0x8A) * 188 + b2_off
    where b2_off = (b2 - 0x40) if b2 < 0x7F else (b2 - 0x41)

Covers all 2350 KS X 1001 precomposed Hangul syllables.
Non-Hangul codepoints fall through to standard Shift-JIS (for punctuation).
"""

_ks_hangul = None


def ks_hangul_list():
    """Return KS X 1001 precomposed Hangul syllables in canonical order."""
    global _ks_hangul
    if _ks_hangul is None:
        chars = []
        for hi in range(0xB0, 0xC9):
            for lo in range(0xA1, 0xFF):
                try:
                    c = bytes([hi, lo]).decode('cp949')
                    if '\uAC00' <= c <= '\uD7A3':
                        chars.append(c)
                except Exception:
                    pass
        _ks_hangul = chars
    return _ks_hangul


def byte_to_ks_index(b1, b2):
    """Return KS X 1001 Hangul index for a Wii custom SJIS byte pair, or None."""
    if b1 == 0x89:
        if 0xCD <= b2 <= 0xFC:
            return b2 - 0xCD
        return None
    if b1 >= 0x8A:
        b2_off = (b2 - 0x40) if b2 < 0x7F else (b2 - 0x41)
        if 0 <= b2_off < 188:
            return 48 + (b1 - 0x8A) * 188 + b2_off
    return None


def decode(data):
    """Decode Wii KR NMS bytes to Korean string.

    Hangul chars come from custom SJIS mapping. ASCII and common SJIS
    punctuation pass through unchanged.
    """
    ks = ks_hangul_list()
    out = []
    i = 0
    while i < len(data):
        if data[i] < 0x80:
            out.append(chr(data[i]))
            i += 1
        elif i + 1 < len(data):
            idx = byte_to_ks_index(data[i], data[i+1])
            if idx is not None and idx < len(ks):
                out.append(ks[idx])
            else:
                try:
                    out.append(data[i:i+2].decode('shift_jis'))
                except Exception:
                    out.append(f'[{data[i]:02x}{data[i+1]:02x}]')
            i += 2
        else:
            i += 1
    return ''.join(out)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        # Decode hex string from argv
        result = decode(bytes.fromhex(sys.argv[1]))
        print(result)
    else:
        # Self-test
        tests = [
            ('89cd', '가'),
            ('91f8', '이'),
            ('8c48', '다'),
            ('8bee', '는'),
            ('959d', '하'),
        ]
        for hex_str, expected in tests:
            got = decode(bytes.fromhex(hex_str))
            ok = '✓' if got == expected else '✗'
            print(f'  {ok} 0x{hex_str} -> {got!r} (expected {expected!r})')
