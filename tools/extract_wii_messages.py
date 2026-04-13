"""Extract Wii NMS messages to wii/messages/{jp,kr}/*.json with full Korean decode."""
import json, sys
from pathlib import Path
sys.path.insert(0, 'tools')
from fcmp_decompress import decompress_fcmp
from wii_hangul_decode import decode as decode_korean


def find_text_start(data, window=32, min_high=16):
    for i in range(0x18, len(data) - window, 16):
        if sum(1 for b in data[i:i+window] if b >= 0x80) >= min_high:
            while i > 0x18 and data[i-1] != 0:
                i -= 1
            return i
    return 0x18


def find_strings(data, min_len=2):
    start = find_text_start(data)
    out = []; i = start
    while i < len(data):
        if data[i] == 0:
            i += 1; continue
        s = i
        while i < len(data) and data[i] != 0: i += 1
        if i - s >= min_len:
            out.append((s, bytes(data[s:i])))
    return out


def try_decode(b):
    res = {'hex': b.hex()}
    for enc in ['shift_jis']:
        try: res[enc] = b.decode(enc)
        except Exception: pass
    return res


def process(nms_file, out_path, is_kr):
    data = Path(nms_file).read_bytes()
    if data[:4] == b'FCMP':
        data = decompress_fcmp(data)
    strings = find_strings(data)
    entries = []
    for off, b in strings:
        e = {'offset': off, **try_decode(b)}
        if is_kr:
            e['korean'] = decode_korean(b)
        entries.append(e)
    result = {
        'source': str(nms_file),
        'decomp_size': len(data),
        'num_strings': len(strings),
        'strings': entries,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return len(strings)


if __name__ == '__main__':
    src_root = Path('extracted_wii/musarama_kor/files')
    out_root = Path('wii/messages')
    total = 0
    for nms in sorted(src_root.rglob('*.nms')):
        is_kr = '_US' in str(nms.parent)
        region = 'kr' if is_kr else 'jp'
        out = (out_root / region / nms.name).with_suffix('.json')
        n = process(nms, out, is_kr)
        rel = nms.relative_to(src_root)
        print(f'  {rel}: {n} strings')
        total += n
    print(f'\nTotal: {total} strings')
