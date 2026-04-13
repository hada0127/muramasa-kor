"""Decode Vanillaware Wii FTX files to PNG images.

Handles FCMP decompression + FTEX container + TPL texture formats.
Supported TPL formats: C4, C8, RGB5A3, RGBA8, CMPR, I8, IA8.
"""
import struct, sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from fcmp_decompress import decompress_fcmp


def rgb5a3(c):
    if c & 0x8000:
        return (((c >> 10) & 0x1F) * 255 // 31,
                ((c >> 5) & 0x1F) * 255 // 31,
                (c & 0x1F) * 255 // 31, 255)
    return (((c >> 8) & 0xF) * 255 // 15,
            ((c >> 4) & 0xF) * 255 // 15,
            (c & 0xF) * 255 // 15,
            ((c >> 12) & 0x7) * 255 // 7)


def decode_c4(data, palette, W, H):
    img = Image.new('RGBA', (W, H)); pix = img.load(); off = 0
    for ty in range(0, H, 8):
        for tx in range(0, W, 8):
            for py in range(8):
                for px in range(0, 8, 2):
                    if off >= len(data): return img
                    b = data[off]; off += 1
                    pix[tx+px, ty+py] = palette[(b >> 4) & 0xF]
                    pix[tx+px+1, ty+py] = palette[b & 0xF]
    return img


def decode_c8(data, palette, W, H):
    img = Image.new('RGBA', (W, H)); pix = img.load(); off = 0
    for ty in range(0, H, 4):
        for tx in range(0, W, 8):
            for py in range(4):
                for px in range(8):
                    if off >= len(data): return img
                    pix[tx+px, ty+py] = palette[data[off]]; off += 1
    return img


def decode_rgb5a3(data, W, H):
    img = Image.new('RGBA', (W, H)); pix = img.load(); off = 0
    for ty in range(0, H, 4):
        for tx in range(0, W, 4):
            for py in range(4):
                for px in range(4):
                    c = struct.unpack('>H', data[off:off+2])[0]; off += 2
                    pix[tx+px, ty+py] = rgb5a3(c)
    return img


def decode_rgba8(data, W, H):
    img = Image.new('RGBA', (W, H)); pix = img.load(); off = 0
    for ty in range(0, H, 4):
        for tx in range(0, W, 4):
            ar = [(data[off+k*2], data[off+k*2+1]) for k in range(16)]; off += 32
            gb = [(data[off+k*2], data[off+k*2+1]) for k in range(16)]; off += 32
            for k in range(16):
                py, px = k // 4, k % 4
                pix[tx+px, ty+py] = (ar[k][1], gb[k][0], gb[k][1], ar[k][0])
    return img


def decode_cmpr(data, W, H):
    def u565(c): return (((c>>11)&0x1F)*255//31, ((c>>5)&0x3F)*255//63, (c&0x1F)*255//31)
    img = Image.new('RGBA', (W, H)); pix = img.load(); off = 0
    for my in range(0, H, 8):
        for mx in range(0, W, 8):
            for sy in range(2):
                for sx in range(2):
                    c0, c1 = struct.unpack('>HH', data[off:off+4])
                    idx = struct.unpack('>I', data[off+4:off+8])[0]; off += 8
                    p0, p1 = u565(c0), u565(c1)
                    if c0 > c1:
                        p2 = tuple((2*p0[i]+p1[i])//3 for i in range(3))
                        p3 = tuple((p0[i]+2*p1[i])//3 for i in range(3))
                        pal = [p0+(255,), p1+(255,), p2+(255,), p3+(255,)]
                    else:
                        p2 = tuple((p0[i]+p1[i])//2 for i in range(3))
                        pal = [p0+(255,), p1+(255,), p2+(255,), (0,0,0,0)]
                    for py in range(4):
                        for px in range(4):
                            i = (idx >> ((15-(py*4+px))*2)) & 0x3
                            pix[mx+sx*4+px, my+sy*4+py] = pal[i]
    return img


def decode_tpl(data, tpl_off):
    """Return list of (filename_hint, PIL.Image) for all textures in the TPL."""
    results = []
    if struct.unpack('>I', data[tpl_off:tpl_off+4])[0] != 0x0020AF30:
        return results
    tcount = struct.unpack('>I', data[tpl_off+4:tpl_off+8])[0]
    for ti in range(tcount):
        desc = tpl_off + 0x0C + ti*8
        img_hdr = tpl_off + struct.unpack('>I', data[desc:desc+4])[0]
        pal_hdr_rel = struct.unpack('>I', data[desc+4:desc+8])[0]
        H = struct.unpack('>H', data[img_hdr:img_hdr+2])[0]
        W = struct.unpack('>H', data[img_hdr+2:img_hdr+4])[0]
        fmt = struct.unpack('>I', data[img_hdr+4:img_hdr+8])[0]
        tex_off = tpl_off + struct.unpack('>I', data[img_hdr+8:img_hdr+12])[0]
        img = None
        if fmt in (8, 9):
            pal_hdr = tpl_off + pal_hdr_rel
            ncolors = struct.unpack('>H', data[pal_hdr:pal_hdr+2])[0]
            pd = tpl_off + struct.unpack('>I', data[pal_hdr+8:pal_hdr+12])[0]
            pal = [rgb5a3(struct.unpack('>H', data[pd+k*2:pd+k*2+2])[0]) for k in range(ncolors)]
            if fmt == 8: img = decode_c4(data[tex_off:tex_off+W*H//2], pal, W, H)
            else:        img = decode_c8(data[tex_off:tex_off+W*H], pal, W, H)
        elif fmt == 5:  img = decode_rgb5a3(data[tex_off:tex_off+W*H*2], W, H)
        elif fmt == 6:  img = decode_rgba8(data[tex_off:tex_off+W*H*4], W, H)
        elif fmt == 14: img = decode_cmpr(data[tex_off:tex_off+W*H//2], W, H)
        if img: results.append((f'{W}x{H}_fmt{fmt}', img))
    return results


def process_ftx(ftx_path, out_dir):
    data = Path(ftx_path).read_bytes()
    if data[:4] == b'FCMP':
        data = decompress_fcmp(data)
    if data[:4] != b'FTEX':
        return 0
    cnt = struct.unpack('<I', data[12:16])[0]
    hdsz = struct.unpack('<I', data[8:12])[0]
    names = [data[0x20+i*0x30:0x20+i*0x30+0x20].rstrip(b'\x00').decode('latin1', errors='replace')
             for i in range(cnt)]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ftx0_off = hdsz
    saved = 0
    for i in range(cnt):
        if ftx0_off + 12 >= len(data) or data[ftx0_off:ftx0_off+4] != b'FTX0':
            break
        sz1 = struct.unpack('<I', data[ftx0_off+4:ftx0_off+8])[0]
        sz2 = struct.unpack('<I', data[ftx0_off+8:ftx0_off+12])[0]
        for desc, img in decode_tpl(data, ftx0_off + sz2):
            safe_name = names[i].replace('/', '_') if i < len(names) else f'tex{i}'
            img.save(out_dir / f'{i:02d}_{safe_name}.png')
            saved += 1
        ftx0_off += sz1 + sz2
    return saved


if __name__ == '__main__':
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix('')
    n = process_ftx(src, dst)
    print(f'{src.name}: {n} textures saved to {dst}/')
