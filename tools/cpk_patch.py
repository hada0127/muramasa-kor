#!/usr/bin/env python3
"""
CPK patcher for Muramasa Rebirth.
Supports in-place and append patching with CRILAYLA LZ compression.

Key format details (from CRI CPK specification):
- FileOffset in TOC is RELATIVE: actual_pos = FileOffset + add_offset
- add_offset = min(ContentOffset, TocOffset)
- FileSize = total CRILAYLA block size (header + compressed + raw 0x100)
- ExtractSize = decompressed file size = CRILAYLA.uncomp_size + 0x100
"""
import struct
import sys
import os

def xor_crypt(data):
    """XOR encrypt/decrypt CRI UTF table (symmetric)."""
    c, m = 0x5F, 0x15
    result = bytearray(len(data))
    for i in range(len(data)):
        result[i] = data[i] ^ (c & 0xFF)
        c = (c * m) & 0xFF
    return bytes(result)


def compress_crilayla(data):
    """CRILAYLA compress with LZ back-references."""
    from collections import defaultdict

    if len(data) <= 0x100:
        raw = data + b'\x00' * (0x100 - len(data))
        return b'CRILAYLA' + struct.pack('<II', 0, 0) + raw

    raw_header = data[:0x100]
    payload = data[0x100:]
    N = len(payload)

    hash_table = defaultdict(list)
    bits = []

    def emit_bits(value, num_bits):
        for j in range(num_bits - 1, -1, -1):
            bits.append((value >> j) & 1)

    pos = N - 1
    while pos >= 0:
        best_offset = 0
        best_length = 0

        if pos >= 2:
            key = (payload[pos], payload[pos - 1], payload[pos - 2])
            candidates = hash_table.get(key, [])
            # Search last 32 candidates for speed (most recent = best locality)
            for cand in candidates[-32:]:
                offset = cand - pos
                if offset < 3 or offset > 8194:
                    continue
                length = 0
                while pos - length >= 0 and (pos - length + offset) < N:
                    if payload[pos - length] != payload[pos - length + offset]:
                        break
                    length += 1
                if length > best_length:
                    best_length = length
                    best_offset = offset
                    if best_length >= 256:
                        break

        if best_length >= 3:
            bits.append(1)
            emit_bits(best_offset - 3, 13)
            remaining = best_length - 3
            vle_lens = [2, 3, 5, 8]
            for level in range(4):
                max_val = (1 << vle_lens[level]) - 1
                if remaining < max_val:
                    emit_bits(remaining, vle_lens[level])
                    break
                emit_bits(max_val, vle_lens[level])
                remaining -= max_val
            else:
                while remaining >= 255:
                    emit_bits(255, 8)
                    remaining -= 255
                emit_bits(remaining, 8)
            for i in range(min(best_length, 256)):
                p = pos - i
                if p >= 2:
                    k = (payload[p], payload[p - 1], payload[p - 2])
                    chain = hash_table[k]
                    chain.append(p)
                    if len(chain) > 64:
                        hash_table[k] = chain[-64:]
            pos -= best_length
        else:
            bits.append(0)
            emit_bits(payload[pos], 8)
            if pos >= 2:
                key = (payload[pos], payload[pos - 1], payload[pos - 2])
                hash_table[key].append(pos)
            pos -= 1

    num_bytes = (len(bits) + 7) // 8
    comp = bytearray(num_bytes)
    for i, b in enumerate(bits):
        if b:
            comp[i // 8] |= (1 << (7 - (i % 8)))
    comp.reverse()

    return b'CRILAYLA' + struct.pack('<II', N, len(comp)) + bytes(comp) + raw_header


class UTFReader:
    """Minimal UTF reader that also tracks byte offsets of row fields."""

    TYPE_SIZES = {0:1, 1:1, 2:2, 3:2, 4:4, 5:4, 6:8, 7:8, 8:4, 9:8, 0xA:4, 0xB:8}

    def __init__(self, data):
        self.data = data
        assert data[:4] == b'@UTF'
        self.rows_off = struct.unpack('>I', data[8:12])[0] + 8
        self.str_off = struct.unpack('>I', data[12:16])[0] + 8
        self.data_off = struct.unpack('>I', data[16:20])[0] + 8
        self.num_cols = struct.unpack('>H', data[24:26])[0]
        self.row_len = struct.unpack('>H', data[26:28])[0]
        self.num_rows = struct.unpack('>I', data[28:32])[0]
        self._parse_columns()

    def _parse_columns(self):
        self.columns = []
        off = 32
        for _ in range(self.num_cols):
            flags = self.data[off]; off += 1
            if flags == 0:
                flags = self.data[off]; off += 1
            name_off = struct.unpack('>I', self.data[off:off+4])[0]; off += 4
            name = self._read_string(name_off)
            col_type = flags & 0x0F
            storage = flags & 0xF0
            const_val = None
            const_off = None
            if storage == 0x30:  # constant
                const_off = off
                const_val, off = self._read_value(col_type, off)
            self.columns.append({
                'name': name, 'type': col_type, 'storage': storage,
                'constant': const_val, 'const_off': const_off,
            })

    def _read_string(self, offset):
        abs_off = self.str_off + offset
        end = self.data.index(b'\x00', abs_off)
        return self.data[abs_off:end].decode('utf-8', errors='replace')

    def _read_value(self, t, off):
        d = self.data
        if t in (0,1): return d[off], off+1
        elif t in (2,3): return struct.unpack('>H', d[off:off+2])[0], off+2
        elif t in (4,5): return struct.unpack('>I', d[off:off+4])[0], off+4
        elif t in (6,7): return struct.unpack('>Q', d[off:off+8])[0], off+8
        elif t == 8: return struct.unpack('>f', d[off:off+4])[0], off+4
        elif t == 9: return struct.unpack('>d', d[off:off+8])[0], off+8
        elif t == 0xA: return struct.unpack('>I', d[off:off+4])[0], off+4
        elif t == 0xB:
            do = struct.unpack('>I', d[off:off+4])[0]
            ds = struct.unpack('>I', d[off+4:off+8])[0]
            return (do, ds), off+8
        return None, off

    def get_row_field_offset(self, row_idx, field_name):
        """Get the byte offset of a specific field in a row."""
        row_start = self.rows_off + row_idx * self.row_len
        off = row_start
        for col in self.columns:
            if col['storage'] == 0x10:
                if col['name'] == field_name:
                    return None
                continue
            elif col['storage'] == 0x30:
                if col['name'] == field_name:
                    return col['const_off']
                continue
            elif col['storage'] == 0x50:
                if col['name'] == field_name:
                    return off
                off += self.TYPE_SIZES[col['type']]
        return None

    def get_row(self, row_idx):
        """Read a row as dict."""
        row = {}
        off = self.rows_off + row_idx * self.row_len
        for col in self.columns:
            if col['storage'] == 0x10:
                row[col['name']] = 0
            elif col['storage'] == 0x30:
                val = col['constant']
                if col['type'] == 0xA and isinstance(val, int):
                    val = self._read_string(val)
                row[col['name']] = val
            elif col['storage'] == 0x50:
                val, off = self._read_value(col['type'], off)
                if col['type'] == 0xA and isinstance(val, int):
                    val = self._read_string(val)
                row[col['name']] = val
            else:
                row[col['name']] = None
        return row


def _update_toc_field(toc_dec, toc_reader, row_idx, field_name, value):
    """Update a single field in the TOC."""
    off = toc_reader.get_row_field_offset(row_idx, field_name)
    if off is None:
        return
    for col in toc_reader.columns:
        if col['name'] == field_name:
            if col['type'] == 4:
                struct.pack_into('>I', toc_dec, off, value)
            elif col['type'] == 6:
                struct.pack_into('>Q', toc_dec, off, value)
            break


def patch_cpk(cpk_path, output_path, file_replacements):
    """Patch a CPK file in-place by replacing compressed file data."""
    with open(cpk_path, 'rb') as f:
        cpk = bytearray(f.read())

    cpk_table_size = struct.unpack('<I', cpk[8:12])[0]
    cpk_utf_dec = xor_crypt(bytes(cpk[0x10:0x10+cpk_table_size]))
    cpk_reader = UTFReader(cpk_utf_dec)
    cpk_row = cpk_reader.get_row(0)

    toc_offset = cpk_row.get('TocOffset', 0)
    content_offset = cpk_row.get('ContentOffset', 0)
    align = cpk_row.get('Align', 2048)
    add_offset = min(content_offset, toc_offset)

    toc_enc_start = toc_offset + 0x10
    toc_table_size = struct.unpack('<I', cpk[toc_offset+8:toc_offset+12])[0]
    toc_dec = bytearray(xor_crypt(bytes(cpk[toc_enc_start:toc_enc_start+toc_table_size])))
    toc_reader = UTFReader(bytes(toc_dec))

    print(f"CPK: {os.path.basename(cpk_path)}")
    print(f"  Files: {toc_reader.num_rows}, Align: {align}, add_offset: 0x{add_offset:X}")

    replaced = 0
    for row_idx in range(toc_reader.num_rows):
        row = toc_reader.get_row(row_idx)
        dirname = row.get('DirName', '')
        filename = row.get('FileName', '')
        path = f"{dirname}/{filename}" if dirname else filename

        if path not in file_replacements:
            continue

        new_raw = file_replacements[path]
        rel_offset = row['FileOffset']
        orig_file_size = row['FileSize']
        abs_offset = rel_offset + add_offset

        # Verify CRILAYLA at absolute offset
        if cpk[abs_offset:abs_offset+8] != b'CRILAYLA':
            print(f"  SKIP: {path} (no CRILAYLA at 0x{abs_offset:X})")
            continue

        new_compressed = compress_crilayla(new_raw)
        new_comp_size = len(new_compressed)

        if new_comp_size <= orig_file_size:
            cpk[abs_offset:abs_offset+new_comp_size] = new_compressed
            if new_comp_size < orig_file_size:
                cpk[abs_offset+new_comp_size:abs_offset+orig_file_size] = b'\x00' * (orig_file_size - new_comp_size)

            _update_toc_field(toc_dec, toc_reader, row_idx, 'FileSize', new_comp_size)
            _update_toc_field(toc_dec, toc_reader, row_idx, 'ExtractSize', len(new_raw))

            print(f"  OK: {path} (comp: {orig_file_size}->{new_comp_size}, raw: {len(new_raw)})")
            replaced += 1
        else:
            print(f"  SKIP: {path} (need {new_comp_size}, have {orig_file_size})")

    cpk[toc_enc_start:toc_enc_start+toc_table_size] = xor_crypt(bytes(toc_dec))

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(cpk)

    print(f"  Replaced: {replaced}, Output: {output_path} ({len(cpk)} bytes)")
    return replaced


def patch_cpk_append(cpk_path, output_path, file_replacements):
    """Patch CPK by inserting new data before ETOC and shifting ETOC to end."""
    with open(cpk_path, 'rb') as f:
        cpk = bytearray(f.read())
    original_size = len(cpk)
    cpk_ts = struct.unpack('<I', cpk[8:12])[0]
    cpk_dec = xor_crypt(bytes(cpk[0x10:0x10+cpk_ts]))
    cpk_reader = UTFReader(cpk_dec)
    cpk_row = cpk_reader.get_row(0)
    toc_offset = cpk_row['TocOffset']
    align = cpk_row['Align']
    content_offset = cpk_row['ContentOffset']
    add_offset = min(content_offset, toc_offset)
    etoc_offset = cpk_row.get('EtocOffset', 0)
    etoc_size = cpk_row.get('EtocSize', 0)
    toc_enc_start = toc_offset + 0x10
    toc_ts = struct.unpack('<I', cpk[toc_offset+8:toc_offset+12])[0]
    toc_dec = bytearray(xor_crypt(bytes(cpk[toc_enc_start:toc_enc_start+toc_ts])))
    toc_reader = UTFReader(bytes(toc_dec))

    print(f"CPK: {os.path.basename(cpk_path)}")
    print(f"  add_offset: 0x{add_offset:X}, EtocOffset: 0x{etoc_offset:X}")

    # Save ETOC data
    etoc_data = bytes(cpk[etoc_offset:etoc_offset + etoc_size + 0x10]) if etoc_offset else b''

    # Truncate at ETOC position
    insert_point = etoc_offset if etoc_offset else len(cpk)
    cpk = cpk[:insert_point]
    while len(cpk) % align:
        cpk.append(0)

    replaced = 0
    for ri in range(toc_reader.num_rows):
        row = toc_reader.get_row(ri)
        dn = row.get('DirName', '')
        fn = row.get('FileName', '')
        path = f"{dn}/{fn}" if dn else fn
        if path not in file_replacements:
            continue
        new_raw = file_replacements[path]
        new_comp = compress_crilayla(new_raw)
        abs_offset = len(cpk)
        rel_offset = abs_offset - add_offset  # Store RELATIVE offset in TOC
        cpk.extend(new_comp)
        while len(cpk) % align:
            cpk.append(0)

        _update_toc_field(toc_dec, toc_reader, ri, 'FileOffset', rel_offset)
        _update_toc_field(toc_dec, toc_reader, ri, 'FileSize', len(new_comp))
        _update_toc_field(toc_dec, toc_reader, ri, 'ExtractSize', len(new_raw))

        print(f"  OK: {path} (comp={len(new_comp)}, raw={len(new_raw)}, relOff=0x{rel_offset:X})")
        replaced += 1

    cpk[toc_enc_start:toc_enc_start+toc_ts] = xor_crypt(bytes(toc_dec))

    # Update CPK header: ContentSize and EtocOffset
    new_content_size = len(cpk) - content_offset
    new_etoc_offset = len(cpk)

    cpk_dec_header = bytearray(xor_crypt(bytes(cpk[0x10:0x10+cpk_ts])))
    cpk_hdr_reader = UTFReader(bytes(cpk_dec_header))
    for field, value in [('ContentSize', new_content_size), ('EtocOffset', new_etoc_offset)]:
        off = cpk_hdr_reader.get_row_field_offset(0, field)
        if off is None:
            continue
        for col in cpk_hdr_reader.columns:
            if col['name'] == field:
                if col['type'] == 6:
                    struct.pack_into('>Q', cpk_dec_header, off, value)
                elif col['type'] == 4:
                    struct.pack_into('>I', cpk_dec_header, off, value)
                break
    cpk[0x10:0x10+cpk_ts] = xor_crypt(bytes(cpk_dec_header))

    # Re-append ETOC
    if etoc_data:
        cpk.extend(etoc_data)

    print(f"  ContentSize: {new_content_size:,}, EtocOffset: 0x{new_etoc_offset:X}")

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(cpk)
    print(f"  Replaced: {replaced}, Size: {len(cpk):,} (+{len(cpk)-original_size:,})")
    return replaced


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: cpk_patch.py <original.cpk> <mod_dir> <output.cpk> [--append]")
        sys.exit(1)

    cpk_path = sys.argv[1]
    mod_dir = sys.argv[2]
    output_path = sys.argv[3]
    use_append = '--append' in sys.argv

    replacements = {}
    for root, dirs, files in os.walk(mod_dir):
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, mod_dir).replace('\\', '/')
            with open(full, 'rb') as f:
                replacements[rel] = f.read()

    if use_append:
        patch_cpk_append(cpk_path, output_path, replacements)
    else:
        patch_cpk(cpk_path, output_path, replacements)
