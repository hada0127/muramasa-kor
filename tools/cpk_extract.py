#!/usr/bin/env python3
"""
CPK (CRI Middleware) Archive Extractor
Supports encrypted CPK files used in PS Vita games like Muramasa Rebirth.
"""

import struct
import os
import sys
import zlib
from pathlib import Path


def decrypt_data(data: bytes) -> bytes:
    """Decrypt CRI UTF table data using XOR cipher (c=0x5F, m=0x15)."""
    c, m = 0x5F, 0x15
    result = bytearray(len(data))
    for i in range(len(data)):
        result[i] = data[i] ^ (c & 0xFF)
        c = (c * m) & 0xFF
    return bytes(result)


def decompress_crilayla(data: bytes, uncompressed_size: int) -> bytes:
    """Decompress CRILAYLA compressed data."""
    # CRILAYLA uses a custom compression scheme
    # The compressed data is read in reverse bit order
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
            # Literal byte
            val = get_next_bits(8)
            result[output_pos] = val
            output_pos -= 1
        else:
            # Back reference
            offset = get_next_bits(13) + 3
            length = 3
            for vle_level in range(len(vle_lens)):
                this_level = get_next_bits(vle_lens[vle_level])
                length += this_level
                if this_level != ((1 << vle_lens[vle_level]) - 1):
                    break
            else:
                # Overflow
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


class UTFTable:
    """Parser for CRI @UTF tables."""

    TYPE_BYTE = 0
    TYPE_SBYTE = 1
    TYPE_USHORT = 2
    TYPE_SHORT = 3
    TYPE_UINT = 4
    TYPE_INT = 5
    TYPE_ULONG = 6
    TYPE_LONG = 7
    TYPE_FLOAT = 8
    TYPE_DOUBLE = 9
    TYPE_STRING = 0xA
    TYPE_DATA = 0xB

    COLUMN_STORAGE_MASK = 0xF0
    COLUMN_STORAGE_PERROW = 0x50
    COLUMN_STORAGE_CONSTANT = 0x30
    COLUMN_STORAGE_ZERO = 0x10
    COLUMN_TYPE_MASK = 0x0F

    def __init__(self, data: bytes, encrypted: bool = False):
        if encrypted:
            data = decrypt_data(data)

        if data[:4] != b'@UTF':
            raise ValueError(f"Invalid UTF signature: {data[:4]}")

        self.data = data
        self._parse()

    def _parse(self):
        d = self.data
        table_size = struct.unpack_from('>I', d, 4)[0]
        self.rows_offset = struct.unpack_from('>I', d, 8)[0] + 8
        self.string_offset = struct.unpack_from('>I', d, 12)[0] + 8
        self.data_offset = struct.unpack_from('>I', d, 16)[0] + 8
        self.table_name_offset = struct.unpack_from('>I', d, 20)[0]
        self.num_columns = struct.unpack_from('>H', d, 24)[0]
        self.row_length = struct.unpack_from('>H', d, 26)[0]
        self.num_rows = struct.unpack_from('>I', d, 28)[0]

        # Parse columns
        self.columns = []
        offset = 32
        for _ in range(self.num_columns):
            flags = d[offset]
            offset += 1
            if flags == 0:
                flags = d[offset]
                offset += 1
            name_offset = struct.unpack_from('>I', d, offset)[0]
            offset += 4
            name = self._read_string(name_offset)
            col_type = flags & self.COLUMN_TYPE_MASK
            storage = flags & self.COLUMN_STORAGE_MASK

            constant_value = None
            if storage == self.COLUMN_STORAGE_CONSTANT:
                constant_value, offset = self._read_value(col_type, offset)

            self.columns.append({
                'name': name,
                'type': col_type,
                'storage': storage,
                'constant': constant_value,
            })

        # Parse rows
        self.rows = []
        for row_idx in range(self.num_rows):
            row = {}
            row_offset = self.rows_offset + row_idx * self.row_length
            for col in self.columns:
                if col['storage'] == self.COLUMN_STORAGE_ZERO:
                    row[col['name']] = 0
                elif col['storage'] == self.COLUMN_STORAGE_CONSTANT:
                    row[col['name']] = col['constant']
                elif col['storage'] == self.COLUMN_STORAGE_PERROW:
                    val, row_offset = self._read_value(col['type'], row_offset)
                    row[col['name']] = val
                else:
                    row[col['name']] = None
            self.rows.append(row)

    def _read_string(self, offset):
        abs_offset = self.string_offset + offset
        end = self.data.index(b'\x00', abs_offset)
        return self.data[abs_offset:end].decode('utf-8', errors='replace')

    def _read_value(self, col_type, offset):
        d = self.data
        if col_type == self.TYPE_BYTE:
            return d[offset], offset + 1
        elif col_type == self.TYPE_SBYTE:
            return struct.unpack_from('>b', d, offset)[0], offset + 1
        elif col_type == self.TYPE_USHORT:
            return struct.unpack_from('>H', d, offset)[0], offset + 2
        elif col_type == self.TYPE_SHORT:
            return struct.unpack_from('>h', d, offset)[0], offset + 2
        elif col_type == self.TYPE_UINT:
            return struct.unpack_from('>I', d, offset)[0], offset + 4
        elif col_type == self.TYPE_INT:
            return struct.unpack_from('>i', d, offset)[0], offset + 4
        elif col_type == self.TYPE_ULONG:
            return struct.unpack_from('>Q', d, offset)[0], offset + 8
        elif col_type == self.TYPE_LONG:
            return struct.unpack_from('>q', d, offset)[0], offset + 8
        elif col_type == self.TYPE_FLOAT:
            return struct.unpack_from('>f', d, offset)[0], offset + 4
        elif col_type == self.TYPE_DOUBLE:
            return struct.unpack_from('>d', d, offset)[0], offset + 8
        elif col_type == self.TYPE_STRING:
            str_offset = struct.unpack_from('>I', d, offset)[0]
            return self._read_string(str_offset), offset + 4
        elif col_type == self.TYPE_DATA:
            data_offset = struct.unpack_from('>I', d, offset)[0]
            data_size = struct.unpack_from('>I', d, offset + 4)[0]
            abs_offset = self.data_offset + data_offset
            return self.data[abs_offset:abs_offset + data_size], offset + 8
        else:
            raise ValueError(f"Unknown type: {col_type}")


def read_chunk(f, encrypted=False):
    """Read a CPK chunk (header + UTF table)."""
    header = f.read(16)
    if len(header) < 16:
        return None, None
    sig = header[:4]
    # Bytes 4-7: unknown/flags
    table_size = struct.unpack_from('<I', header, 8)[0]
    # Bytes 12-15: padding/unknown

    table_data = f.read(table_size)
    if encrypted and sig in (b'CPK ', b'TOC ', b'ITOC', b'ETOC', b'GTOC'):
        table_data = decrypt_data(table_data)

    return sig, table_data


def extract_cpk(cpk_path: str, output_dir: str, list_only: bool = False):
    """Extract all files from a CPK archive."""
    cpk_path = Path(cpk_path)
    output_dir = Path(output_dir)

    with open(cpk_path, 'rb') as f:
        # Read CPK header
        sig = f.read(4)
        if sig != b'CPK ':
            raise ValueError(f"Not a CPK file: {sig}")
        f.seek(0)

        # Check if encrypted
        f.seek(0x10)
        check = f.read(4)
        encrypted = check != b'@UTF'
        f.seek(0)

        print(f"CPK: {cpk_path.name} (encrypted: {encrypted})")

        # Read CPK header chunk
        f.seek(0)
        chunk_sig, chunk_data = read_chunk(f, encrypted)
        cpk_table = UTFTable(chunk_data)

        # Get TOC offset and content offset
        toc_offset = None
        content_offset = None
        itoc_offset = None
        etoc_offset = None

        for row in cpk_table.rows:
            if 'TocOffset' in row and row['TocOffset']:
                toc_offset = row['TocOffset']
            if 'ContentOffset' in row and row['ContentOffset']:
                content_offset = row['ContentOffset']
            if 'ItocOffset' in row and row['ItocOffset']:
                itoc_offset = row['ItocOffset']
            if 'EtocOffset' in row and row['EtocOffset']:
                etoc_offset = row['EtocOffset']

        print(f"  TOC offset: {toc_offset}")
        print(f"  Content offset: {content_offset}")
        print(f"  ITOC offset: {itoc_offset}")

        files = []

        if toc_offset is not None:
            # Read TOC
            f.seek(toc_offset)
            toc_sig, toc_data = read_chunk(f, encrypted)
            if toc_sig == b'TOC ':
                toc_table = UTFTable(toc_data)
                print(f"  Files in TOC: {toc_table.num_rows}")

                align = 2048  # Default alignment

                for row in cpk_table.rows:
                    if 'Align' in row and row['Align']:
                        align = row['Align']

                for row in toc_table.rows:
                    dirname = row.get('DirName', '')
                    filename = row.get('FileName', '')
                    file_size = row.get('FileSize', 0)
                    extract_size = row.get('ExtractSize', 0)
                    file_offset = row.get('FileOffset', 0)

                    if dirname:
                        full_path = f"{dirname}/{filename}"
                    else:
                        full_path = filename

                    # FileOffset is absolute from file start.
                    # Some files need +align adjustment; detect by checking for CRILAYLA.
                    abs_offset = file_offset

                    files.append({
                        'path': full_path,
                        'offset': abs_offset,
                        'size': file_size,
                        'extract_size': extract_size,
                        'align': align,
                    })

        if itoc_offset is not None and not files:
            # Read ITOC for ID-based archives
            f.seek(itoc_offset)
            itoc_sig, itoc_data = read_chunk(f, encrypted)
            if itoc_sig == b'ITOC':
                itoc_table = UTFTable(itoc_data)
                print(f"  ITOC entries: {itoc_table.num_rows}")

        # List or extract files
        if list_only:
            print(f"\n{'Path':<60} {'Size':>10} {'Extract':>10}")
            print("-" * 82)
            for fi in files:
                print(f"{fi['path']:<60} {fi['size']:>10} {fi['extract_size']:>10}")
            print(f"\nTotal: {len(files)} files")
            return files

        # Extract files
        if not output_dir.exists():
            output_dir.mkdir(parents=True)

        extracted = 0
        for fi in files:
            out_path = output_dir / fi['path']
            out_path.parent.mkdir(parents=True, exist_ok=True)

            align = fi.get('align', 2048)

            # Try reading at offset; if not CRILAYLA, try offset + align
            f.seek(fi['offset'])
            header_check = f.read(8)

            if header_check[:8] == b'CRILAYLA':
                actual_offset = fi['offset']
            else:
                # Try with alignment offset
                f.seek(fi['offset'] + align)
                header_check2 = f.read(8)
                if header_check2[:8] == b'CRILAYLA':
                    actual_offset = fi['offset'] + align
                else:
                    actual_offset = fi['offset']

            f.seek(actual_offset)
            data = f.read(fi['size'])

            # Check for CRILAYLA compression
            if data[:8] == b'CRILAYLA':
                uncomp_size = struct.unpack_from('<I', data, 8)[0]
                comp_size = struct.unpack_from('<I', data, 12)[0]
                # Compressed data starts at offset 0x10
                comp_data = data[0x10:0x10 + comp_size]
                # The last 0x100 bytes of the chunk are uncompressed header
                header_data = data[0x10 + comp_size:0x10 + comp_size + 0x100]
                try:
                    decompressed = decompress_crilayla(comp_data, uncomp_size)
                    data = header_data + decompressed
                except Exception as e:
                    print(f"  WARN: Failed to decompress {fi['path']}: {e}")

            out_path.write_bytes(data)
            extracted += 1

            if extracted % 100 == 0:
                print(f"  Extracted {extracted}/{len(files)} files...")

        print(f"  Extracted {extracted} files to {output_dir}")
        return files


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Extract CRI CPK archives')
    parser.add_argument('input', help='Input CPK file')
    parser.add_argument('-o', '--output', help='Output directory', default=None)
    parser.add_argument('-l', '--list', action='store_true', help='List files only')
    args = parser.parse_args()

    if args.output is None:
        args.output = Path(args.input).stem + '_extracted'

    extract_cpk(args.input, args.output, args.list)
