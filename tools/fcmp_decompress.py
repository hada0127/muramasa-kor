"""FCMP decompressor for Muramasa Wii (Vanillaware LZSS with circular window)."""
import struct
import sys
from pathlib import Path


def decompress_fcmp(data: bytes, N: int = 4096) -> bytes:
    if data[:4] != b'FCMP':
        raise ValueError("Not FCMP")
    uncomp_size = struct.unpack('<I', data[4:8])[0]
    buf = bytearray([0] * N)
    R = N - 18  # Okumura LZSS standard initial position (N-F, F=18)
    out = bytearray()
    pos = 12
    while len(out) < uncomp_size and pos < len(data):
        flag = data[pos]; pos += 1
        for i in range(8):
            if len(out) >= uncomp_size or pos >= len(data): break
            bit = (flag >> i) & 1
            if bit == 1:
                c = data[pos]; pos += 1
                out.append(c); buf[R] = c; R = (R + 1) % N
            else:
                if pos + 2 > len(data): break
                b1 = data[pos]; b2 = data[pos+1]; pos += 2
                offset = b1 | ((b2 & 0xF0) << 4)
                length = (b2 & 0x0F) + 3
                for k in range(length):
                    c = buf[(offset + k) % N]
                    out.append(c); buf[R] = c; R = (R + 1) % N
    return bytes(out[:uncomp_size])


if __name__ == '__main__':
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(src.suffix + '.bin')
    data = src.read_bytes()
    out = decompress_fcmp(data)
    dst.write_bytes(out)
    print(f"{src.name}: {len(data)} -> {len(out)} bytes | magic={out[:4]!r}")
