"""Clear all opening narration carrier UV regions to fully transparent.
Atlas-only (no MBS modification). Original English narration disappears,
background animation plays unobstructed.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

import numpy as np
from PIL import Image


MBS_TABLE_OFFSET = 0x1940
QUAD_SIZE = 80
VERTEX_SIZE = 20


def quad_offset(idx: int) -> int:
    return MBS_TABLE_OFFSET + idx * QUAD_SIZE


def read_quad(src: bytes, idx: int):
    base = quad_offset(idx)
    return [struct.unpack_from("<Iffff", src, base + i * VERTEX_SIZE) for i in range(4)]


def uv_rect(vs) -> tuple[int, int, int, int]:
    xs = [v[1] for v in vs]; ys = [v[2] for v in vs]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def build_atlas(source_mbs: Path, source_atlas: Path, output: Path) -> dict:
    src = source_mbs.read_bytes()
    atlas = Image.open(source_atlas).convert("RGBA")
    arr = np.array(atlas)

    cleared = 0
    for idx in range(40, 116):
        vs = read_quad(src, idx)
        ux0, uy0, ux1, uy1 = uv_rect(vs)
        if ux0 < 0 or uy0 < 0 or ux1 > 512 or uy1 > 512: continue
        if ux0 == ux1 or uy0 == uy1: continue
        arr[uy0:uy1, ux0:ux1, 3] = 0
        cleared += 1

    Image.fromarray(arr, mode="RGBA").save(output)
    return {"cleared": cleared}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-mbs", default="temp/cpk_extract/_US/GUI/opening01.mbs")
    ap.add_argument("--source-atlas", default="C:/game/vita3k/textures/export/79C935AA47DD1810.png")
    ap.add_argument("--output", default="temp/opening_test/atlas.png")
    args = ap.parse_args()
    info = build_atlas(Path(args.source_mbs), Path(args.source_atlas), Path(args.output))
    print(f"cleared {info['cleared']} carrier UV regions")


if __name__ == "__main__":
    main()
