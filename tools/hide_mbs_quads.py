from __future__ import annotations

import argparse
import struct
from pathlib import Path


QUAD_SIZE = 80
VERTEX_SIZE = 20


def write_hidden(blob: bytearray, offset: int) -> None:
    verts = [
        (0x00000000, 0.0, 0.0, -2080.0, 1872.0),
        (0x00000000, 0.0, 1.0, -2078.0, 1872.0),
        (0x00000000, 1.0, 1.0, -2078.0, 1870.0),
        (0x00000000, 1.0, 0.0, -2080.0, 1870.0),
    ]
    for i, vert in enumerate(verts):
        struct.pack_into("<Iffff", blob, offset + i * VERTEX_SIZE, *vert)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--base-offset", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--indices", nargs="+", type=int, required=True)
    args = ap.parse_args()

    blob = bytearray(Path(args.source).read_bytes())
    for idx in args.indices:
        off = args.base_offset + idx * QUAD_SIZE
        if off + QUAD_SIZE > len(blob):
            raise IndexError(f"quad {idx} out of range")
        write_hidden(blob, off)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)


if __name__ == "__main__":
    main()
