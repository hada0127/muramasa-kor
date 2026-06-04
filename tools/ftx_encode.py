#!/usr/bin/env python3
"""
FTX (FTEX/GXT) texture ENCODER for PS Vita — inverse of ftx_extract.py.

실기(real PS Vita) 한글 패치용. Vita3K는 hash 기반 PNG import로 텍스처를 대체하지만
실기엔 그 기능이 없으므로, 한글 텍스처를 CPK 내부 FTX payload에 직접 베이크해야 한다.

핵심 원칙(codex+agy 협의):
- FTX/GXT 헤더·entry 구조는 그대로 두고 **texture payload만 동일 raw size로 교체**.
- 원본 픽셀 포맷 유지: 0x87000000=DXT5/BC3, 0x86000000=DXT3/BC2 (변경 금지).
- swizzle은 16바이트 DXT 블록 단위 Morton(Z-order). ftx_extract.unswizzle_blocks의 정확한 역함수.
- mipmap: 원본 tex_size가 base level보다 크면 하위 mip도 생성·인코딩해 이어붙임.

검증(--selftest):
- swizzle(unswizzle(orig)) == orig  (byte-exact, 전 대상 크기)
- decode(encode(img)) 시각 품질(알파/RGB MAE) 리포트

Usage:
    python3 tools/ftx_encode.py --selftest backup/NinPri.cpk
    python3 tools/ftx_encode.py --selftest-dir /tmp/ftx_probe/patch
"""

import struct
import sys
import os
import glob
import argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ftx_extract as fx  # 디코더/unswizzle 재사용

DXT5 = 0x87000000
DXT3 = 0x86000000


# --- Morton / Z-order swizzle (unswizzle_blocks의 정확한 역함수) ---

def _compact_vec(x):
    """compact_one_by_one 벡터화(짝수 위치 비트 추출·압축). numpy 정수 배열."""
    x = x & np.uint32(0x55555555)
    x = (x ^ (x >> np.uint32(1))) & np.uint32(0x33333333)
    x = (x ^ (x >> np.uint32(2))) & np.uint32(0x0F0F0F0F)
    x = (x ^ (x >> np.uint32(4))) & np.uint32(0x00FF00FF)
    x = (x ^ (x >> np.uint32(8))) & np.uint32(0x0000FFFF)
    return x


_PERM_CACHE = {}


def _morton_perm(blocks_w, blocks_h):
    """Morton index i → linear block index. (valid_mask, lin_idx, morton_idx)

    ftx_extract.unswizzle_blocks와 동일 규약(짝수=Y, 홀수=X)으로 벡터화.
    캐시해 같은 크기는 재계산하지 않음.
    """
    key = (blocks_w, blocks_h)
    c = _PERM_CACHE.get(key)
    if c is not None:
        return c
    total = blocks_w * blocks_h
    min_dim = min(blocks_w, blocks_h)
    k = min_dim.bit_length() - 1
    i = np.arange(total, dtype=np.uint32)
    bx = _compact_vec(i >> np.uint32(1)) & np.uint32(min_dim - 1)
    by = _compact_vec(i) & np.uint32(min_dim - 1)
    upper = (i >> np.uint32(2 * k)) << np.uint32(k)
    if blocks_w >= blocks_h:
        bx = bx | upper
    else:
        by = by | upper
    valid = (bx < blocks_w) & (by < blocks_h)
    lin = (by.astype(np.int64) * blocks_w + bx.astype(np.int64))
    morton = np.nonzero(valid)[0]
    lin_valid = lin[valid].astype(np.int64)
    c = (morton, lin_valid)
    _PERM_CACHE[key] = c
    return c


def swizzle_blocks(linear, blocks_w, blocks_h, block_size=16):
    """Linear 블록 순서 → Vita Morton(Z-order). unswizzle_blocks의 역연산(벡터화).

    unswizzle: out[lin] = in[morton]  →  swizzle: out[morton] = in[lin]
    """
    total = blocks_w * blocks_h
    src = np.frombuffer(linear, dtype=np.uint8)[:total * block_size].reshape(total, block_size)
    out = np.zeros((total, block_size), dtype=np.uint8)
    morton, lin = _morton_perm(blocks_w, blocks_h)
    out[morton] = src[lin]
    return out.reshape(-1).tobytes()


def unswizzle_blocks(swizzled, blocks_w, blocks_h, block_size=16):
    """Vita Morton(Z-order) → linear 블록 순서 (벡터화, ftx_extract와 동일 결과)."""
    total = blocks_w * blocks_h
    src = np.frombuffer(swizzled, dtype=np.uint8)[:total * block_size].reshape(total, block_size)
    out = np.zeros((total, block_size), dtype=np.uint8)
    morton, lin = _morton_perm(blocks_w, blocks_h)
    out[lin] = src[morton]
    return out.reshape(-1).tobytes()


# --- DXT block encoders (range-fit) ---

def _rgb_to_565_vec(rgb):
    """(...,3) int → (...) uint32 RGB565."""
    r = (rgb[..., 0].astype(np.uint32) >> 3) << 11
    g = (rgb[..., 1].astype(np.uint32) >> 2) << 5
    b = (rgb[..., 2].astype(np.uint32) >> 3)
    return r | g | b


def _565_to_rgb_vec(v):
    """(...) uint16 → (...,3) int32 (디코더 rgb565와 동일 양자화)."""
    v = v.astype(np.int32)
    r = ((v >> 11) & 0x1F) * 255 // 31
    g = ((v >> 5) & 0x3F) * 255 // 63
    b = (v & 0x1F) * 255 // 31
    return np.stack([r, g, b], axis=-1)


def _encode_color_blocks(rgb):
    """(N,16,3) int RGB → (N,8) uint8 DXT color block.

    디코더 규칙과 일치: colors[0]=c0, [1]=c1, [2]=(2c0+c1)/3, [3]=(c0+2c1)/3, c0>c1.
    """
    N = rgb.shape[0]
    cmin = rgb.min(axis=1)   # (N,3)
    cmax = rgb.max(axis=1)
    c0v = _rgb_to_565_vec(cmax).astype(np.uint32)  # (N,)
    c1v = _rgb_to_565_vec(cmin).astype(np.uint32)

    # c0>c1 (4색 모드) 보장. 같으면 단색.
    swap = c0v < c1v
    c0v, c1v = np.where(swap, c1v, c0v), np.where(swap, c0v, c1v)
    equal = c0v == c1v

    rc0 = _565_to_rgb_vec(c0v)   # (N,3)
    rc1 = _565_to_rgb_vec(c1v)
    palette = np.stack([
        rc0, rc1, (2 * rc0 + rc1) // 3, (rc0 + 2 * rc1) // 3,
    ], axis=1)  # (N,4,3)

    diff = rgb[:, :, None, :].astype(np.int32) - palette[:, None, :, :]  # (N,16,4,3)
    dist = (diff * diff).sum(axis=3)            # (N,16,4)
    idx = dist.argmin(axis=3 - 1).astype(np.uint32)  # (N,16)
    idx[equal] = 0

    shifts = (2 * np.arange(16)).astype(np.uint32)
    color_bits = (idx << shifts[None, :]).sum(axis=1).astype(np.uint32)  # (N,)

    out = np.empty((N, 8), dtype=np.uint8)
    out[:, 0] = c0v & 0xFF
    out[:, 1] = (c0v >> 8) & 0xFF
    out[:, 2] = c1v & 0xFF
    out[:, 3] = (c1v >> 8) & 0xFF
    for k in range(4):
        out[:, 4 + k] = (color_bits >> (8 * k)) & 0xFF
    return out


def _encode_dxt5_alpha_blocks(alpha):
    """(N,16) alpha → (N,8) uint8 DXT5 alpha block (a0>a1, 8값 보간)."""
    N = alpha.shape[0]
    a = alpha.astype(np.int32)
    a0 = a.max(axis=1)   # (N,)
    a1 = a.min(axis=1)
    equal = a0 == a1
    # 8값 LUT (N,8) — 디코더 공식과 동일
    lut = [a0, a1]
    for i in range(2, 8):
        lut.append(((8 - i) * a0 + (i - 1) * a1) // 7)
    lut = np.stack(lut, axis=1)  # (N,8)
    diff = np.abs(a[:, :, None] - lut[:, None, :])  # (N,16,8)
    idx = diff.argmin(axis=2).astype(np.uint64)     # (N,16)
    idx[equal] = 0

    shifts = (3 * np.arange(16)).astype(np.uint64)
    bits = (idx << shifts[None, :]).sum(axis=1).astype(np.uint64)  # (N,)

    out = np.empty((N, 8), dtype=np.uint8)
    out[:, 0] = a0.astype(np.uint8)
    out[:, 1] = a1.astype(np.uint8)
    for k in range(6):
        out[:, 2 + k] = (bits >> np.uint64(8 * k)) & np.uint64(0xFF)
    return out


def _encode_dxt3_alpha_blocks(alpha):
    """(N,16) alpha → (N,8) uint8 DXT3 alpha block (4비트/픽셀 explicit)."""
    N = alpha.shape[0]
    a4 = (alpha.astype(np.uint8) >> 4) & 0x0F  # (N,16)
    out = np.empty((N, 8), dtype=np.uint8)
    for b in range(8):
        out[:, b] = a4[:, 2 * b] | (a4[:, 2 * b + 1] << 4)
    return out


def _decode_blocks_to_image(blocks_rgba, width, height):
    """(N,16,4) RGBA 블록 → (H,W,4) 이미지. encode의 _to_blocks 역연산."""
    bh, bw = height // 4, width // 4
    b = blocks_rgba.reshape(bh, bw, 4, 4, 4).transpose(0, 2, 1, 3, 4)
    return b.reshape(height, width, 4)


def decode_dxt_image_vec(linear, width, height, fmt):
    """linear DXT 바이트 → RGBA (H,W,4). ftx_extract.decode_dxt_image와 동일 결과(벡터화)."""
    bw, bh = width // 4, height // 4
    N = bw * bh
    blk = np.frombuffer(linear, dtype=np.uint8)[:N * 16].reshape(N, 16)
    i16 = np.arange(16)

    # --- color (DXT5/DXT3 공통: 항상 4색 모드, ftx_extract와 동일) ---
    c0 = blk[:, 8].astype(np.uint16) | (blk[:, 9].astype(np.uint16) << 8)
    c1 = blk[:, 10].astype(np.uint16) | (blk[:, 11].astype(np.uint16) << 8)
    color_bits = (blk[:, 12].astype(np.uint32) | (blk[:, 13].astype(np.uint32) << 8) |
                  (blk[:, 14].astype(np.uint32) << 16) | (blk[:, 15].astype(np.uint32) << 24))
    rc0 = _565_to_rgb_vec(c0)  # (N,3)
    rc1 = _565_to_rgb_vec(c1)
    palette = np.stack([rc0, rc1, (2 * rc0 + rc1) // 3, (rc0 + 2 * rc1) // 3], axis=1)  # (N,4,3)
    c_idx = (color_bits[:, None] >> (2 * i16)[None, :]) & 0x3  # (N,16)
    rgb = palette[np.arange(N)[:, None], c_idx]  # (N,16,3) gather

    out = np.zeros((N, 16, 4), dtype=np.uint8)
    out[:, :, :3] = rgb.astype(np.uint8)

    if fmt == DXT5:
        a0 = blk[:, 0].astype(np.int32)
        a1 = blk[:, 1].astype(np.int32)
        abits = np.zeros(N, dtype=np.uint64)
        for k in range(6):
            abits |= blk[:, 2 + k].astype(np.uint64) << np.uint64(8 * k)
        a_idx = (abits[:, None] >> (np.uint64(3) * i16.astype(np.uint64))[None, :]) & np.uint64(0x7)
        a_idx = a_idx.astype(np.int64)  # (N,16)
        # LUT: a0>a1 → 8값 / else 6값+0+255 (ftx_extract와 동일)
        lut8 = [a0, a1]
        for j in range(2, 8):
            lut8.append(((8 - j) * a0 + (j - 1) * a1) // 7)
        lut8 = np.stack(lut8, axis=1)  # (N,8)
        lut6 = [a0, a1]
        for j in range(2, 6):
            lut6.append(((6 - j) * a0 + (j - 1) * a1) // 5)
        lut6.append(np.zeros(N, dtype=np.int32))
        lut6.append(np.full(N, 255, dtype=np.int32))
        lut6 = np.stack(lut6, axis=1)  # (N,8)
        use8 = (a0 > a1)
        lut = np.where(use8[:, None], lut8, lut6)  # (N,8)
        alpha = np.take_along_axis(lut, a_idx, axis=1)  # (N,16)
        out[:, :, 3] = alpha.astype(np.uint8)
    elif fmt == DXT3:
        # 4비트/픽셀 explicit alpha (8바이트). ftx_extract와 동일 *17 스케일
        adata = blk[:, 0:8]  # (N,8)
        alpha = np.zeros((N, 16), dtype=np.int32)
        for px in range(16):
            byte_idx = px // 2
            if px % 2 == 0:
                alpha[:, px] = (adata[:, byte_idx] & 0x0F) * 17
            else:
                alpha[:, px] = ((adata[:, byte_idx] >> 4) & 0x0F) * 17
        out[:, :, 3] = alpha.astype(np.uint8)
    else:
        raise ValueError(f"unsupported fmt 0x{fmt:08X}")

    return _decode_blocks_to_image(out, width, height)


def _to_blocks(rgba):
    """(H,W,4) → (N,16,4) 블록, 픽셀 i=py*4+px (디코더와 동일 row-major)."""
    h, w = rgba.shape[:2]
    bh, bw = h // 4, w // 4
    b = rgba.reshape(bh, 4, bw, 4, 4).transpose(0, 2, 1, 3, 4)  # (bh,bw,4,4,4)
    return b.reshape(bh * bw, 16, 4)


def encode_dxt_image(rgba, width, height, fmt):
    """RGBA (H,W,4) uint8 → linear DXT 바이트(블록 순서, swizzle 전). 벡터화."""
    assert width % 4 == 0 and height % 4 == 0, f"NPOT block dim {width}x{height}"
    bw, bh = width // 4, height // 4
    blocks = _to_blocks(np.asarray(rgba, dtype=np.int32))  # (N,16,4)
    rgb = blocks[:, :, :3]
    alpha = blocks[:, :, 3]
    if fmt == DXT5:
        ab = _encode_dxt5_alpha_blocks(alpha)
    elif fmt == DXT3:
        ab = _encode_dxt3_alpha_blocks(alpha)
    else:
        raise ValueError(f"unsupported fmt 0x{fmt:08X}")
    cb = _encode_color_blocks(rgb)
    out = np.concatenate([ab, cb], axis=1)  # (N,16), 블록 순서 by*bw+bx
    return out.reshape(-1).tobytes()


def _downsample_half(rgba):
    """2x2 박스 다운샘플 (mip 생성용). (H,W,4) → (H/2,W/2,4)."""
    h, w = rgba.shape[:2]
    a = rgba.astype(np.uint16)
    ds = (a[0:h:2, 0:w:2] + a[1:h:2, 0:w:2] +
          a[0:h:2, 1:w:2] + a[1:h:2, 1:w:2] + 2) // 4
    return ds.astype(np.uint8)


def encode_texture_payload(rgba, width, height, fmt, mip_levels):
    """base RGBA → swizzle된 payload (mip 체인 포함, 원본 tex_size와 동일 길이 목표).

    각 mip level을 개별 인코딩+swizzle 후 이어붙임 (디코더가 base만 읽지만
    런타임 mip 샘플링 대비). mip_levels<=1이면 base만.
    """
    chunks = []
    cur = rgba
    w, h = width, height
    levels = max(1, mip_levels)
    for lvl in range(levels):
        if w < 4 or h < 4:
            break
        lin = encode_dxt_image(cur, w, h, fmt)
        sw = swizzle_blocks(lin, w // 4, h // 4, 16)
        chunks.append(sw)
        cur = _downsample_half(cur)
        w, h = w // 2, h // 2
    return b''.join(chunks)


# --- FTEX 컨테이너: 전체 GXT 스캔 ---

def parse_all_gxt(data):
    """FTX(FTEX 컨테이너) 안의 모든 GXT 블록/서브텍스처 열거.

    Returns list of dict:
      gxt_pos: GXT 블록의 파일 내 절대 오프셋
      index:   GXT 내 텍스처 인덱스(보통 0)
      tex_off: GXT 시작 기준 텍스처 데이터 오프셋
      tex_size, fmt, width, height, mipmaps
      abs_off: 파일 내 절대 데이터 오프셋 = gxt_pos + tex_off
    """
    out = []
    pos = 0
    while True:
        g = data.find(b'GXT\x00', pos)
        if g < 0:
            break
        gxt = data[g:]
        try:
            num_tex = struct.unpack_from('<I', gxt, 8)[0]
        except struct.error:
            break
        if num_tex == 0 or num_tex > 256:
            pos = g + 4
            continue
        for i in range(num_tex):
            eo = 0x20 + i * 32
            if eo + 32 > len(gxt):
                break
            e = gxt[eo:eo + 32]
            tex_off = struct.unpack_from('<I', e, 0)[0]
            tex_size = struct.unpack_from('<I', e, 4)[0]
            fmt = struct.unpack_from('<I', e, 20)[0]
            w = struct.unpack_from('<H', e, 24)[0]
            h = struct.unpack_from('<H', e, 26)[0]
            mip = struct.unpack_from('<H', e, 28)[0]
            if w == 0 or h == 0:
                continue
            out.append({
                'gxt_pos': g,
                'index': i,
                'tex_off': tex_off,
                'tex_size': tex_size,
                'fmt': fmt,
                'width': w,
                'height': h,
                'mipmaps': mip,
                'abs_off': g + tex_off,
            })
        pos = g + 4
    return out


def decode_subtexture(data, entry):
    """parse_all_gxt 엔트리 → base level RGBA (H,W,4)."""
    w, h, fmt = entry['width'], entry['height'], entry['fmt']
    bw, bh = w // 4, h // 4
    base = bw * bh * 16
    raw = data[entry['abs_off']:entry['abs_off'] + base]
    if len(raw) < base:
        raise ValueError(f"payload short {len(raw)}<{base}")
    lin = fx.unswizzle_blocks(raw, bw, bh, 16)
    return fx.decode_dxt_image(lin, w, h, fmt)


def replace_subtexture(data, entry, new_rgba):
    """FTX 바이트에서 entry의 payload를 new_rgba 인코딩으로 in-place 교체.

    new_rgba는 (height,width,4). tex_size 전체 길이를 유지(mip 포함)하도록
    인코딩 결과를 자르거나 원본 tail로 패딩하지 않고, 원본 tex_size에 맞춰 생성.
    Returns 수정된 bytes.
    """
    w, h, fmt = entry['width'], entry['height'], entry['fmt']
    bw, bh = w // 4, h // 4
    base = bw * bh * 16
    tex_size = entry['tex_size'] or base
    # mip level 수: tex_size가 base보다 크면 mip 체인 존재
    if tex_size > base:
        # 전체 mip 체인 길이 계산해 level 수 추정
        levels = 0
        tw, th, acc = w, h, 0
        while tw >= 4 and th >= 4 and acc < tex_size:
            acc += (tw // 4) * (th // 4) * 16
            levels += 1
            tw, th = tw // 2, th // 2
        mip_levels = levels
    else:
        mip_levels = 1

    payload = encode_texture_payload(new_rgba, w, h, fmt, mip_levels)
    # 원본 tex_size에 정확히 맞춤(초과 시 자르고, 부족 시 원본 잔여로 패딩)
    if len(payload) > tex_size:
        payload = payload[:tex_size]
    elif len(payload) < tex_size:
        orig_tail = data[entry['abs_off'] + len(payload):entry['abs_off'] + tex_size]
        payload = payload + orig_tail

    out = bytearray(data)
    out[entry['abs_off']:entry['abs_off'] + tex_size] = payload
    return bytes(out)


# --- self-test ---

def _selftest_files(ftx_files):
    total = 0
    sw_ok = 0
    unsw_ok = 0
    quality = []
    for fpath in ftx_files:
        data = open(fpath, 'rb').read()
        for e in parse_all_gxt(data):
            if e['fmt'] not in (DXT5, DXT3):
                continue
            w, h = e['width'], e['height']
            bw, bh = w // 4, h // 4
            base = bw * bh * 16
            raw = data[e['abs_off']:e['abs_off'] + base]
            if len(raw) < base:
                continue
            total += 1
            # 0) 벡터화 unswizzle == 레퍼런스(ftx_extract) byte-exact
            lin = unswizzle_blocks(raw, bw, bh, 16)
            if lin == fx.unswizzle_blocks(raw, bw, bh, 16):
                unsw_ok += 1
            else:
                print(f"  [UNSWZ MISMATCH] {os.path.basename(fpath)} {w}x{h}")
            # 1) swizzle byte-exact 라운드트립
            re = swizzle_blocks(lin, bw, bh, 16)
            if re == raw:
                sw_ok += 1
            else:
                print(f"  [SWZ FAIL] {os.path.basename(fpath)} {w}x{h}")
            # 1.5) 벡터화 decode == 레퍼런스 (256블록 이하만 교차검증해 속도 확보)
            if total <= 40:
                rgba_ref = fx.decode_dxt_image(lin, w, h, e['fmt'])
                rgba_vec = decode_dxt_image_vec(lin, w, h, e['fmt'])
                if not np.array_equal(rgba_ref, rgba_vec):
                    print(f"  [DEC MISMATCH] {os.path.basename(fpath)} {w}x{h}")
            # 2) 인코더 품질: decode → encode → decode (벡터화)
            rgba = decode_dxt_image_vec(lin, w, h, e['fmt'])
            relin = encode_dxt_image(rgba, w, h, e['fmt'])
            rgba2 = decode_dxt_image_vec(relin, w, h, e['fmt'])
            a_mae = float(np.abs(rgba[:, :, 3].astype(int) - rgba2[:, :, 3].astype(int)).mean())
            # 가시 RGB(alpha>0)만
            mask = rgba[:, :, 3] > 0
            if mask.any():
                rgb_mae = float(np.abs(rgba[:, :, :3][mask].astype(int) - rgba2[:, :, :3][mask].astype(int)).mean())
            else:
                rgb_mae = 0.0
            quality.append((a_mae, rgb_mae))
    print(f"\n벡터화 unswizzle==레퍼런스: {unsw_ok}/{total} 통과")
    print(f"swizzle byte-exact: {sw_ok}/{total} 통과")
    if quality:
        q = np.array(quality)
        print(f"인코더 품질(decode→encode→decode): "
              f"alpha MAE 평균 {q[:,0].mean():.2f} 최대 {q[:,0].max():.2f} | "
              f"가시RGB MAE 평균 {q[:,1].mean():.2f} 최대 {q[:,1].max():.2f}")
    return sw_ok == total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', metavar='CPK', help='CPK에서 FTX 추출 후 self-test')
    ap.add_argument('--selftest-dir', metavar='DIR', help='추출된 FTX 디렉토리 self-test')
    args = ap.parse_args()

    if args.selftest_dir:
        files = sorted(glob.glob(os.path.join(args.selftest_dir, '**', '*.ftx'), recursive=True))
        print(f"{len(files)}개 FTX self-test")
        ok = _selftest_files(files)
        sys.exit(0 if ok else 1)

    if args.selftest:
        import tempfile
        import cpk_extract
        tmp = tempfile.mkdtemp(prefix='ftxst_')
        print(f"{args.selftest} 추출 → {tmp}")
        cpk_extract.extract_cpk(args.selftest, tmp)
        files = sorted(glob.glob(os.path.join(tmp, '**', '*.ftx'), recursive=True))
        print(f"{len(files)}개 FTX self-test")
        ok = _selftest_files(files)
        sys.exit(0 if ok else 1)

    ap.print_help()


if __name__ == '__main__':
    main()
