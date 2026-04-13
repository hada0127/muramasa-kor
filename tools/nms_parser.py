#!/usr/bin/env python3
"""
NMS (NMSB) file parser for Muramasa Rebirth.
Extracts and reimports Shift-JIS text messages.
"""

import struct
import json
import glob
import os
from pathlib import Path


def parse_nms(filepath: str) -> dict:
    """Parse an NMSB file and extract all messages."""
    with open(filepath, 'rb') as f:
        data = f.read()

    if data[:4] != b'NMSB':
        raise ValueError(f"Not an NMSB file: {filepath}")

    # Header structure (little-endian):
    # 0x00: "NMSB" signature
    # 0x04: data section size (from after some header to FEOC)
    # 0x08: header size / offset (0x20 = 32)
    # 0x14: entry count
    data_size = struct.unpack('<I', data[0x04:0x08])[0]
    header_size = struct.unpack('<I', data[0x08:0x0C])[0]
    entry_count = struct.unpack('<I', data[0x14:0x18])[0]

    # Find text section start (first non-zero after header/index area)
    text_start = header_size
    while text_start < len(data) and data[text_start] == 0:
        text_start += 1

    # Extract null-terminated Shift-JIS strings
    messages = []
    msg_offsets = []
    i = text_start
    while i < len(data):
        if data[i:i+4] == b'FEOC':
            break
        if data[i] != 0:
            start = i
            while i < len(data) and data[i] != 0:
                i += 1
            raw = data[start:i]
            try:
                msg = raw.decode('shift_jis', errors='replace')
                messages.append(msg)
                msg_offsets.append(start)
            except:
                pass
        i += 1

    return {
        'filepath': str(filepath),
        'data_size': data_size,
        'header_size': header_size,
        'entry_count': entry_count,
        'text_start': text_start,
        'messages': messages,
        'offsets': msg_offsets,
        'raw_data': data,
    }


def rebuild_nms(parsed: dict, new_messages: list, encoding: str = 'shift_jis') -> bytes:
    """Rebuild an NMSB file with new messages.

    Args:
        parsed: Original parsed NMS data
        new_messages: List of new message strings (same length as original)
        encoding: Target encoding (shift_jis for JP, can be changed for KR)

    Returns:
        New NMSB file bytes
    """
    original = parsed['raw_data']
    header_size = parsed['header_size']
    text_start = parsed['text_start']

    if len(new_messages) != len(parsed['messages']):
        raise ValueError(
            f"Message count mismatch: {len(new_messages)} != {len(parsed['messages'])}"
        )

    # Build new text section
    new_text_parts = []
    for msg in new_messages:
        encoded = msg.encode(encoding, errors='replace')
        new_text_parts.append(encoded + b'\x00')

    new_text_data = b''.join(new_text_parts)

    # Rebuild the file:
    # 1. Keep header up to text_start (with zero padding between header_size and text_start)
    # 2. Replace text section
    # 3. Add FEOC footer

    # Header (keep original, it includes the index/pointer area)
    header = bytearray(original[:text_start])

    # FEOC footer (16 bytes)
    feoc = b'FEOC' + b'\x00' * 4 + b'\x10\x00\x00\x00' + b'\x00' * 4

    # Pad text data to align
    while len(new_text_data) % 16 != 0:
        new_text_data += b'\x00'

    # Calculate new data size
    new_data_size = text_start + len(new_text_data) + len(feoc) - header_size

    # Update header data_size field
    struct.pack_into('<I', header, 0x04, new_data_size)

    result = bytes(header) + new_text_data + feoc
    return result


def export_messages_json(nms_files: list, output_path: str):
    """Export all messages from NMS files to a JSON file for translation."""
    export = {}

    for nms_file in nms_files:
        try:
            parsed = parse_nms(nms_file)
            rel_path = str(nms_file)
            export[rel_path] = {
                'entry_count': parsed['entry_count'],
                'messages': parsed['messages'],
            }
        except Exception as e:
            print(f"Error parsing {nms_file}: {e}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    total = sum(len(v['messages']) for v in export.values())
    print(f"Exported {total} messages from {len(export)} files to {output_path}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Parse Muramasa NMSB files')
    parser.add_argument('action', choices=['export', 'import', 'info'])
    parser.add_argument('--input', '-i', nargs='+', help='Input NMS files or glob pattern')
    parser.add_argument('--output', '-o', help='Output file')
    parser.add_argument('--translation', '-t', help='Translation JSON file (for import)')
    args = parser.parse_args()

    if args.action == 'export':
        files = []
        for pattern in args.input:
            files.extend(glob.glob(pattern, recursive=True))
        export_messages_json(files, args.output or 'messages.json')

    elif args.action == 'info':
        for pattern in args.input:
            for f in glob.glob(pattern, recursive=True):
                parsed = parse_nms(f)
                print(f"{f}: {parsed['entry_count']} entries, "
                      f"{len(parsed['messages'])} messages")

    elif args.action == 'import':
        print("Import not yet implemented - use rebuild_nms() programmatically")
