#!/usr/bin/env python3
"""
CRILAYLA compressor with LZ back-references.
Replaces the literal-only encoder with actual compression.
"""
import struct
import sys
from collections import defaultdict


def decompress_crilayla(data: bytes, uncompressed_size: int) -> bytes:
    """Decompress CRILAYLA compressed data (reference implementation)."""
    if len(data) == 0:
        return b'\x00' * uncompressed_size

    result = bytearray(uncompressed_size)
    output_end = uncompressed_size - 1
    input_offset = len(data) - 1
    bit_pool = 0
    bits_left = 0
    output_pos = output_end

    def get_next_bits(num_bits):
        nonlocal bit_pool, bits_left, input_offset
        out_bits = 0
        bits_produced = 0
        while bits_produced < num_bits:
            if bits_left == 0:
                if input_offset < 0:
                    return out_bits
                bit_pool = data[input_offset]
                input_offset -= 1
                bits_left = 8
            bits_this_round = min(bits_left, num_bits - bits_produced)
            out_bits |= ((bit_pool >> (bits_left - bits_this_round)) & ((1 << bits_this_round) - 1)) << (num_bits - bits_produced - bits_this_round)
            bits_left -= bits_this_round
            bits_produced += bits_this_round
        return out_bits

    vle_lens = [2, 3, 5, 8]

    while output_pos >= 0:
        if get_next_bits(1) == 0:
            val = get_next_bits(8)
            result[output_pos] = val
            output_pos -= 1
        else:
            offset = get_next_bits(13) + 3
            length = 3
            for vle_level in range(len(vle_lens)):
                this_level = get_next_bits(vle_lens[vle_level])
                length += this_level
                if this_level != ((1 << vle_lens[vle_level]) - 1):
                    break
            else:
                while True:
                    this_level = get_next_bits(8)
                    length += this_level
                    if this_level != 255:
                        break

            for i in range(length):
                if output_pos < 0:
                    break
                result[output_pos] = result[output_pos + offset]
                output_pos -= 1

    return bytes(result)


def compress_crilayla(data: bytes) -> bytes:
    """
    CRILAYLA compress with LZ back-references.

    Format:
    - First 0x100 bytes stored as raw header
    - Remaining payload compressed with LZ (literals + back-refs)
    - Bitstream read in reverse by decompressor
    - Back-refs: flag=1, 13-bit offset (+3), VLE length (+3)
    - Literals: flag=0, 8-bit value
    """
    if len(data) <= 0x100:
        raw = data + b'\x00' * (0x100 - len(data))
        return b'CRILAYLA' + struct.pack('<II', 0, 0) + raw

    raw_header = data[:0x100]
    payload = data[0x100:]
    N = len(payload)

    # Build hash table for 3-byte sequences (processed right-to-left)
    # Key: 3-byte tuple at (pos, pos-1, pos-2)
    # Value: list of positions with that key
    hash_table = defaultdict(list)

    bits = []

    def emit_bits(value, num_bits):
        for j in range(num_bits - 1, -1, -1):
            bits.append((value >> j) & 1)

    def emit_literal(byte_val):
        bits.append(0)
        emit_bits(byte_val, 8)

    def emit_backref(offset, length):
        bits.append(1)
        emit_bits(offset - 3, 13)
        # VLE length encoding
        remaining = length - 3
        vle_lens = [2, 3, 5, 8]
        for level in range(4):
            max_val = (1 << vle_lens[level]) - 1
            if remaining < max_val:
                emit_bits(remaining, vle_lens[level])
                return
            emit_bits(max_val, vle_lens[level])
            remaining -= max_val
        # Overflow
        while remaining >= 255:
            emit_bits(255, 8)
            remaining -= 255
        emit_bits(remaining, 8)

    pos = N - 1  # Process from end to start

    while pos >= 0:
        best_offset = 0
        best_length = 0

        # Only search if we have enough context for a 3-byte key
        if pos >= 2:
            key = (payload[pos], payload[pos - 1], payload[pos - 2])
            candidates = hash_table.get(key, [])

            # Check candidates (most recent first for better locality)
            for cand in reversed(candidates):
                offset = cand - pos
                if offset < 3 or offset > 8194:
                    continue

                # Extend match
                length = 0
                while pos - length >= 0 and (pos - length + offset) < N:
                    if payload[pos - length] != payload[pos - length + offset]:
                        break
                    length += 1

                if length > best_length:
                    best_length = length
                    best_offset = offset
                    if best_length >= 256:  # Good enough, stop searching
                        break

        if best_length >= 3:
            emit_backref(best_offset, best_length)
            # Add all positions in this match to hash table
            for i in range(best_length):
                p = pos - i
                if p >= 2:
                    k = (payload[p], payload[p - 1], payload[p - 2])
                    hash_table[k].append(p)
            pos -= best_length
        else:
            emit_literal(payload[pos])
            # Add current position to hash table
            if pos >= 2:
                key = (payload[pos], payload[pos - 1], payload[pos - 2])
                hash_table[key].append(pos)
            pos -= 1

    # Pack bits into bytes (MSB first within each byte)
    num_bytes = (len(bits) + 7) // 8
    comp = bytearray(num_bytes)
    for i, b in enumerate(bits):
        if b:
            comp[i // 8] |= (1 << (7 - (i % 8)))
    # Reverse byte order (decompressor reads from end)
    comp.reverse()

    compressed_size = len(comp)
    return b'CRILAYLA' + struct.pack('<II', N, compressed_size) + bytes(comp) + raw_header


def parse_crilayla_container(container: bytes):
    """Parse a CRILAYLA container into compressed data and raw header."""
    assert container[:8] == b'CRILAYLA'
    uncomp_size = struct.unpack('<I', container[8:12])[0]
    comp_size = struct.unpack('<I', container[12:16])[0]
    comp_data = container[16:16 + comp_size]
    raw_header = container[16 + comp_size:16 + comp_size + 0x100]
    return comp_data, raw_header, uncomp_size


def test_roundtrip(filepath):
    """Test compress-decompress round-trip for a file."""
    with open(filepath, 'rb') as f:
        original = f.read()

    print(f"\n{'='*60}")
    print(f"File: {filepath}")
    print(f"Original size: {len(original)} bytes")

    # Compress
    compressed = compress_crilayla(original)
    comp_data, raw_header, uncomp_size = parse_crilayla_container(compressed)

    total_compressed = len(compressed)
    ratio = len(comp_data) / uncomp_size * 100 if uncomp_size > 0 else 0
    print(f"Compressed: {total_compressed} bytes (payload: {len(comp_data)}/{uncomp_size} = {ratio:.1f}%)")

    # Decompress
    decompressed_payload = decompress_crilayla(comp_data, uncomp_size)
    if len(original) <= 0x100:
        reconstructed = raw_header[:len(original)]
    else:
        reconstructed = raw_header + decompressed_payload

    # Compare
    if reconstructed == original:
        print(f"PASS - Round-trip OK")
        return True
    else:
        print(f"FAIL - Mismatch!")
        # Find first difference
        for i in range(min(len(original), len(reconstructed))):
            if original[i] != reconstructed[i]:
                print(f"  First diff at offset {i}: orig=0x{original[i]:02X} got=0x{reconstructed[i]:02X}")
                break
        if len(original) != len(reconstructed):
            print(f"  Length mismatch: orig={len(original)} got={len(reconstructed)}")
        return False


if __name__ == '__main__':
    import glob
    import os

    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        # Test all NMS files in patch directories
        files = []
        for pattern in ['patch_main/**/*.nms', 'patch_patch/**/*.nms']:
            files.extend(glob.glob(pattern, recursive=True))

    if not files:
        print("No files to test")
        sys.exit(1)

    passed = 0
    failed = 0
    for f in sorted(files):
        if test_roundtrip(f):
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    sys.exit(1 if failed > 0 else 0)
