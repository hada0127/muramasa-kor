#!/usr/bin/env python3
"""
FTX (FTEX/GXT) texture extractor for PS Vita.
Extracts textures from .ftx files to PNG format.
Supports DXT5/BC3 and DXT3/BC2 with PS Vita Morton-order (Z-order) unswizzle.

Usage:
    python tools/ftx_extract.py <input_ftx_or_dir> <output_dir>
    python tools/ftx_extract.py extracted/NinPriPack1 temp/output/dlc1_textures
"""

import struct
import sys
import os
import glob
import numpy as np
from pathlib import Path
from PIL import Image


# --- Morton / Z-order unswizzle ---

def compact_one_by_one(x):
    """Extract even-positioned bits and compact (Vita3K algorithm)."""
    x &= 0x55555555
    x = (x ^ (x >> 1)) & 0x33333333
    x = (x ^ (x >> 2)) & 0x0F0F0F0F
    x = (x ^ (x >> 4)) & 0x00FF00FF
    x = (x ^ (x >> 8)) & 0x0000FFFF
    return x


def unswizzle_blocks(swizzled, blocks_w, blocks_h, block_size=16):
    """Unswizzle Morton-ordered blocks back to linear order.

    Vita3K convention: even bits = Y, odd bits = X.
    Inverse of font_patch.py swizzle_dxt5_blocks.
    """
    total_blocks = blocks_w * blocks_h
    output = bytearray(total_blocks * block_size)

    min_dim = min(blocks_w, blocks_h)
    k = min_dim.bit_length() - 1  # log2(min_dim)

    for i in range(total_blocks):
        bx = compact_one_by_one(i >> 1) & (min_dim - 1)  # odd bits = X
        by = compact_one_by_one(i) & (min_dim - 1)        # even bits = Y
        upper_bits = (i >> (2 * k)) << k
        if blocks_w >= blocks_h:
            bx |= upper_bits
        else:
            by |= upper_bits
        if bx >= blocks_w or by >= blocks_h:
            continue
        linear_idx = by * blocks_w + bx
        src = i * block_size
        dst = linear_idx * block_size
        output[dst:dst + block_size] = swizzled[src:src + block_size]

    return bytes(output)


# --- DXT decoders ---

def decode_dxt5_block(block):
    """Decode a 16-byte DXT5 block to 4x4 RGBA pixels."""
    # Alpha
    alpha0 = block[0]
    alpha1 = block[1]
    alpha_bits = int.from_bytes(block[2:8], 'little')

    alphas = [alpha0, alpha1]
    if alpha0 > alpha1:
        for i in range(2, 8):
            alphas.append(((8 - i) * alpha0 + (i - 1) * alpha1) // 7)
    else:
        for i in range(2, 6):
            alphas.append(((6 - i) * alpha0 + (i - 1) * alpha1) // 5)
        alphas.append(0)
        alphas.append(255)

    # Color
    c0_raw = struct.unpack_from('<H', block, 8)[0]
    c1_raw = struct.unpack_from('<H', block, 10)[0]
    color_bits = struct.unpack_from('<I', block, 12)[0]

    def rgb565(v):
        r = ((v >> 11) & 0x1F) * 255 // 31
        g = ((v >> 5) & 0x3F) * 255 // 63
        b = (v & 0x1F) * 255 // 31
        return r, g, b

    c0 = rgb565(c0_raw)
    c1 = rgb565(c1_raw)
    colors = [c0, c1]
    colors.append(tuple((2 * c0[i] + c1[i]) // 3 for i in range(3)))
    colors.append(tuple((c0[i] + 2 * c1[i]) // 3 for i in range(3)))

    pixels = np.zeros((4, 4, 4), dtype=np.uint8)
    for py in range(4):
        for px in range(4):
            idx = py * 4 + px
            a_idx = (alpha_bits >> (idx * 3)) & 0x7
            c_idx = (color_bits >> (idx * 2)) & 0x3
            pixels[py, px, 0] = colors[c_idx][0]
            pixels[py, px, 1] = colors[c_idx][1]
            pixels[py, px, 2] = colors[c_idx][2]
            pixels[py, px, 3] = alphas[a_idx]

    return pixels


def decode_dxt3_block(block):
    """Decode a 16-byte DXT3 block to 4x4 RGBA pixels."""
    # Alpha: 4 bits per pixel, 8 bytes total
    alpha_data = block[:8]

    # Color
    c0_raw = struct.unpack_from('<H', block, 8)[0]
    c1_raw = struct.unpack_from('<H', block, 10)[0]
    color_bits = struct.unpack_from('<I', block, 12)[0]

    def rgb565(v):
        r = ((v >> 11) & 0x1F) * 255 // 31
        g = ((v >> 5) & 0x3F) * 255 // 63
        b = (v & 0x1F) * 255 // 31
        return r, g, b

    c0 = rgb565(c0_raw)
    c1 = rgb565(c1_raw)
    colors = [c0, c1]
    colors.append(tuple((2 * c0[i] + c1[i]) // 3 for i in range(3)))
    colors.append(tuple((c0[i] + 2 * c1[i]) // 3 for i in range(3)))

    pixels = np.zeros((4, 4, 4), dtype=np.uint8)
    for py in range(4):
        for px in range(4):
            idx = py * 4 + px
            # 4-bit alpha
            byte_idx = idx // 2
            if idx % 2 == 0:
                a = (alpha_data[byte_idx] & 0x0F) * 17  # scale 0-15 to 0-255
            else:
                a = ((alpha_data[byte_idx] >> 4) & 0x0F) * 17
            c_idx = (color_bits >> (idx * 2)) & 0x3
            pixels[py, px, 0] = colors[c_idx][0]
            pixels[py, px, 1] = colors[c_idx][1]
            pixels[py, px, 2] = colors[c_idx][2]
            pixels[py, px, 3] = a

    return pixels


def decode_dxt_image(data, width, height, fmt):
    """Decode a full DXT-compressed image to RGBA numpy array."""
    blocks_w = width // 4
    blocks_h = height // 4
    block_size = 16  # Both DXT3 and DXT5 use 16 bytes per block

    if fmt == 0x87000000:
        decoder = decode_dxt5_block
    elif fmt == 0x86000000:
        decoder = decode_dxt3_block
    else:
        raise ValueError(f"Unsupported format: 0x{fmt:08X}")

    image = np.zeros((height, width, 4), dtype=np.uint8)

    for by in range(blocks_h):
        for bx in range(blocks_w):
            block_idx = by * blocks_w + bx
            offset = block_idx * block_size
            block = data[offset:offset + block_size]
            if len(block) < block_size:
                break
            pixels = decoder(block)
            y = by * 4
            x = bx * 4
            image[y:y+4, x:x+4] = pixels

    return image


# --- FTX/GXT parser ---

def parse_ftx(filepath):
    """Parse an FTX file and return list of texture entries.

    Returns list of dicts with keys:
        width, height, format, data (raw swizzled bytes)
    """
    with open(filepath, 'rb') as f:
        data = f.read()

    # Find GXT header
    gxt_pos = data.find(b'GXT\x00')
    if gxt_pos < 0:
        return []

    gxt = data[gxt_pos:]
    version = struct.unpack_from('<I', gxt, 4)[0]
    num_tex = struct.unpack_from('<I', gxt, 8)[0]
    data_offset = struct.unpack_from('<I', gxt, 0xC)[0]
    total_tex_size = struct.unpack_from('<I', gxt, 0x10)[0]

    textures = []
    for i in range(num_tex):
        entry_off = 0x20 + i * 32
        if entry_off + 32 > len(gxt):
            break
        entry = gxt[entry_off:entry_off + 32]

        tex_offset = struct.unpack_from('<I', entry, 0)[0]
        tex_size = struct.unpack_from('<I', entry, 4)[0]
        fmt = struct.unpack_from('<I', entry, 20)[0]
        width = struct.unpack_from('<H', entry, 24)[0]
        height = struct.unpack_from('<H', entry, 26)[0]
        mipmaps = struct.unpack_from('<H', entry, 28)[0]

        if width == 0 or height == 0:
            continue

        # Calculate expected size
        blocks_w = width // 4
        blocks_h = height // 4
        block_size = 16
        expected_size = blocks_w * blocks_h * block_size

        if tex_size == 0:
            tex_size = expected_size

        tex_data = gxt[tex_offset:tex_offset + tex_size]

        textures.append({
            'width': width,
            'height': height,
            'format': fmt,
            'mipmaps': mipmaps,
            'data': tex_data,
            'offset': tex_offset,
            'size': tex_size,
        })

    return textures


def extract_ftx_to_png(ftx_path, output_dir, prefix=None):
    """Extract all textures from an FTX file to PNG files.

    Returns list of output file paths.
    """
    textures = parse_ftx(ftx_path)
    if not textures:
        return []

    os.makedirs(output_dir, exist_ok=True)

    if prefix is None:
        prefix = Path(ftx_path).stem

    outputs = []
    for i, tex in enumerate(textures):
        w, h, fmt = tex['width'], tex['height'], tex['format']

        if fmt not in (0x87000000, 0x86000000):
            print(f"  [SKIP] {prefix} tex{i}: unsupported format 0x{fmt:08X}")
            continue

        blocks_w = w // 4
        blocks_h = h // 4
        block_size = 16
        expected = blocks_w * blocks_h * block_size

        raw = tex['data']
        if len(raw) < expected:
            print(f"  [SKIP] {prefix} tex{i}: data too short ({len(raw)}<{expected})")
            continue

        # Only use first mipmap level
        raw = raw[:expected]

        # Unswizzle Morton order → linear
        linear = unswizzle_blocks(raw, blocks_w, blocks_h, block_size)

        # Decode DXT → RGBA
        rgba = decode_dxt_image(linear, w, h, fmt)

        # Save PNG
        suffix = f"_{i}" if len(textures) > 1 else ""
        out_path = os.path.join(output_dir, f"{prefix}{suffix}.png")
        Image.fromarray(rgba, 'RGBA').save(out_path)
        outputs.append(out_path)

    return outputs


def extract_directory(input_dir, output_dir):
    """Extract all FTX files in a directory tree."""
    ftx_files = glob.glob(os.path.join(input_dir, '**', '*.ftx'), recursive=True)
    ftx_files.sort()

    total = len(ftx_files)
    success = 0
    skipped = 0
    errors = 0

    print(f"Found {total} FTX files in {input_dir}")
    print(f"Output: {output_dir}")
    print()

    for idx, ftx_path in enumerate(ftx_files, 1):
        rel = os.path.relpath(ftx_path, input_dir)
        rel_dir = os.path.dirname(rel)
        stem = Path(ftx_path).stem

        out_sub = os.path.join(output_dir, rel_dir)

        try:
            results = extract_ftx_to_png(ftx_path, out_sub, prefix=stem)
            if results:
                success += 1
                sizes = []
                for r in results:
                    img = Image.open(r)
                    sizes.append(f"{img.width}x{img.height}")
                    img.close()
                print(f"  [{idx}/{total}] {rel} → {', '.join(sizes)}")
            else:
                skipped += 1
                print(f"  [{idx}/{total}] {rel} → (no textures)")
        except Exception as e:
            errors += 1
            print(f"  [{idx}/{total}] {rel} → ERROR: {e}")

    print()
    print(f"Done: {success} extracted, {skipped} skipped, {errors} errors (total {total})")
    return success, skipped, errors


def main():
    if len(sys.argv) < 3:
        print("Usage: python ftx_extract.py <input_ftx_or_dir> <output_dir>")
        print()
        print("Examples:")
        print("  python tools/ftx_extract.py extracted/NinPriPack1/bg/P1_bg00_00.ftx output/test")
        print("  python tools/ftx_extract.py extracted/NinPriPack1 output/dlc1_textures")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]

    if os.path.isfile(input_path):
        results = extract_ftx_to_png(input_path, output_dir)
        if results:
            print(f"Extracted {len(results)} texture(s):")
            for r in results:
                img = Image.open(r)
                print(f"  {r} ({img.width}x{img.height})")
                img.close()
        else:
            print("No textures extracted.")
    elif os.path.isdir(input_path):
        extract_directory(input_path, output_dir)
    else:
        print(f"Error: {input_path} not found")
        sys.exit(1)


if __name__ == '__main__':
    main()
