"""Audit Out-Of-Range (OOR) SJIS bytes in patched NMS files.

The Korean patch uses a custom SJIS codepoint range (0x89CD..0x8EE0, 960 syllables)
mapped to overlay cells 1644..2603 on the KANJI font page. ASCII chars and JP
punctuation/symbols are expected in specific ranges. Any 2-byte SJIS sequence
outside these ranges will fall back to the original JP font glyph, producing
unexpected kanji in what should be Korean text.

Usage:
    python tools/audit_oor.py patch_main/                 # scan directory
    python tools/audit_oor.py patch_main/ patch_patch/    # multiple
    python tools/audit_oor.py patch_main/_US/msgsheet/sysmsg.nms  # single file
    python tools/audit_oor.py patch_main/ --summary       # counts only
    python tools/audit_oor.py patch_main/ --output report.json
    python tools/audit_oor.py patch_main/ --baseline      # write/update baseline.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Allow module imports
sys.path.insert(0, str(Path(__file__).parent))
from nms_parser import parse_nms  # noqa

# In-range SJIS codepoints (2-byte) considered valid for rendering
KR_MAP_START = 0x89CD
KR_MAP_END = 0x8EE0    # 960 Korean syllables
ASCII_REMAP_START = 0x8EE1  # Some ASCII chars remapped here (excluded — see below)
JP_PUNCT_START = 0x8140     # JP punctuation/symbols page (preserved by font overlay)
JP_PUNCT_END = 0x829F


def is_in_range(code: int) -> bool:
    """A 2-byte SJIS code is in-range if it maps to a glyph the Korean patch
    intends to render (either custom KR syllable, preserved JP punctuation, or
    ASCII remap slot)."""
    if KR_MAP_START <= code <= KR_MAP_END:
        return True
    if JP_PUNCT_START <= code <= JP_PUNCT_END:
        return True
    # ASCII remap: build_patch._build_ascii_sjis_map puts non-space ASCII at
    # cells 2604+. Those bytes are technically OOR for glyph overlay, but they
    # represent intentional encoding. We flag them separately.
    return False


def scan_message(text: str):
    """Return list of OOR codepoints as hex strings for a single message."""
    b = text.encode('shift_jis', 'replace')
    oor = []
    i = 0
    while i < len(b):
        c = b[i]
        if (0x81 <= c <= 0x9F) or c >= 0xE0:
            if i + 1 < len(b):
                code = (c << 8) | b[i + 1]
                if not is_in_range(code):
                    oor.append(f'{code:04X}')
                i += 2
                continue
        i += 1
    return oor


def scan_file(path: str):
    """Return per-message OOR report for a single NMS file."""
    try:
        parsed = parse_nms(path)
    except Exception as e:
        return {'path': path, 'error': str(e), 'messages': []}
    messages = parsed.get('messages', [])
    entries = []
    for idx, msg in enumerate(messages):
        oor = scan_message(msg)
        if oor:
            entries.append({
                'idx': idx,
                'oor_codes': sorted(set(oor)),
                'oor_count': len(oor),
                'text_preview': msg[:60],
            })
    return {
        'path': path,
        'message_count': len(messages),
        'oor_message_count': len(entries),
        'entries': entries,
    }


def iter_nms_files(roots):
    for root in roots:
        p = Path(root)
        if p.is_file() and p.suffix == '.nms':
            yield str(p)
        elif p.is_dir():
            for f in sorted(p.rglob('*.nms')):
                yield str(f)


def main():
    ap = argparse.ArgumentParser(description='Audit OOR SJIS bytes in NMS files.')
    ap.add_argument('paths', nargs='+', help='NMS files or directories')
    ap.add_argument('--summary', action='store_true', help='Print aggregate counts only')
    ap.add_argument('--output', help='Write JSON report to path')
    ap.add_argument('--baseline', action='store_true',
                    help='Write/update docs/03-analysis/oor_baseline.json')
    ap.add_argument('--top', type=int, default=10,
                    help='Top N OOR codes to list in summary (default 10)')
    args = ap.parse_args()

    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    per_file = []
    for f in iter_nms_files(args.paths):
        per_file.append(scan_file(f))

    # Aggregate
    total_msgs = sum(r.get('message_count', 0) for r in per_file)
    total_oor_msgs = sum(r.get('oor_message_count', 0) for r in per_file)
    code_counter = {}
    for r in per_file:
        for e in r.get('entries', []):
            for c in e['oor_codes']:
                code_counter[c] = code_counter.get(c, 0) + 1

    top_codes = sorted(code_counter.items(), key=lambda x: -x[1])[: args.top]

    # Summary
    print(f'Files scanned: {len(per_file)}')
    print(f'Total messages: {total_msgs}')
    print(f'OOR messages: {total_oor_msgs} ({100 * total_oor_msgs / max(total_msgs, 1):.1f}%)')
    print(f'Top {args.top} OOR codes:')
    for code, count in top_codes:
        print(f'  0x{code}  -- {count} msgs')

    if not args.summary:
        print('\nPer-file breakdown:')
        for r in per_file:
            if r.get('oor_message_count', 0):
                print(f"  {r['path']}: {r['oor_message_count']}/{r['message_count']} OOR")

    report = {
        'summary': {
            'files': len(per_file),
            'total_messages': total_msgs,
            'oor_messages': total_oor_msgs,
            'oor_codes': dict(top_codes),
        },
        'files': per_file,
    }

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f'Report written: {args.output}')

    if args.baseline:
        baseline_path = 'docs/03-analysis/oor_baseline.json'
        os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
        baseline = {
            'summary': report['summary'],
            'files': [{k: v for k, v in r.items() if k != 'entries'} for r in per_file],
        }
        with open(baseline_path, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, ensure_ascii=False, indent=2)
        print(f'Baseline written: {baseline_path}')

    # Exit code: 0 if no OOR, 1 if any found (useful for CI gate in future)
    return 0 if total_oor_msgs == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
