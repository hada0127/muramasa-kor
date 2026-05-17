#!/usr/bin/env python
"""Create HD Korean font import textures from HD texture pack base.
Draws Korean glyphs at full 4096x4096 resolution, then downscales to 2048x2048."""

import json, os, sys, platform, subprocess
import numpy as np
from PIL import Image, ImageFont, ImageDraw

# Reuse the shared glyph helper (supports fractional stroke via supersampling)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auto_font_import import draw_centered_glyph


def _default_vita3k_root():
    sysname = platform.system()
    if sysname == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Vita3K/Vita3K")
    if sysname == "Linux":
        return os.path.expanduser("~/.local/share/Vita3K/Vita3K")
    return "C:/game/vita3k"


def _default_hd_pack_dir():
    sysname = platform.system()
    if sysname in ("Darwin", "Linux"):
        return os.path.expanduser("~/Downloads/Muramasa Complete 2.0/PCSE00240/Best")
    return "C:/Users/taro1/Downloads/Muramasa Complete 2.0/PCSE00240/Best"


VITA3K_ROOT = os.environ.get("VITA3K_ROOT", _default_vita3k_root())
EXPORT_DIR = os.environ.get("VITA3K_EXPORT_DIR", os.path.join(VITA3K_ROOT, "textures", "export", "PCSE00240"))
IMPORT_DIR = os.environ.get("VITA3K_IMPORT_DIR", os.path.join(VITA3K_ROOT, "textures", "import", "PCSE00240"))
HD_PACK_DIR = os.environ.get("HD_PACK_DIR", _default_hd_pack_dir())

# Glyph outline: 1.5px black stroke at 50% opacity (alpha=128). Fractional
# strokes (1024 base, scale=1 → stroke=1.5) are rendered via 2x supersampling
# inside draw_centered_glyph. HD bases get integer strokes (2048→3, 4096→6).
# Body 20pt KR / 16pt ASCII at 1x.
STROKE_FILL = (0, 0, 0, 128)
KR_BODY_PT = 20
ASCII_BODY_PT = 16
STROKE_BASE_PT = 1.5  # scaled with texture (1.5px at 1024, 3px at 2048, 6px at 4096)


def sjis_to_cell(b1, b2):
    if b2 < 0x80:
        b2_offset = b2 - 0x40
    else:
        b2_offset = b2 - 0x41
    return (b1 - 0x81) * 188 + b2_offset


def create_hd_korean_font(hd_base_path, import_path, mapping_path, font_path, max_dim=2048):
    """Create HD Korean font by overlaying glyphs on HD base texture."""
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    kr_map = mapping['korean_to_sjis']

    img = Image.open(hd_base_path).convert("RGBA")
    w, h = img.size
    # Cell size scales with texture: 1024->32px, 2048->64px, 4096->128px
    scale = w // 1024
    cs = 32 * scale
    font_size_kr = int(KR_BODY_PT * scale)
    font_size_ascii = int(ASCII_BODY_PT * scale)
    stroke_width = STROKE_BASE_PT * scale

    print(f"  Base: {w}x{h}, scale={scale}x, cell={cs}px, font_kr={font_size_kr}px, stroke={stroke_width}px")

    # font_kr/font_ascii no longer used directly — draw_centered_glyph caches fonts.

    # Space glyph slot
    SPACE_SJIS = (0x8C, 0x6D)
    space_cell = sjis_to_cell(*SPACE_SJIS)
    space_local = space_cell - 1644

    # Build Korean cell map
    korean_cells = {}
    for char, (b1, b2) in kr_map.items():
        cell = sjis_to_cell(b1, b2)
        local = cell - 1644
        if 0 <= local < 1024:
            if local == space_local:
                continue
            korean_cells[local] = char

    # Detect format (white RGB + alpha vs dark RGBA)
    arr = np.array(img)
    rgb_mean = arr[:, :, :3].mean()
    fmt = "white" if rgb_mean > 200 else "dark"
    print(f"  Format: {fmt} (RGB mean={rgb_mean:.0f})")

    draw = ImageDraw.Draw(img)
    cols = w // cs

    # Draw Korean glyphs
    for local_idx, kr_char in korean_cells.items():
        row = local_idx // cols
        col = local_idx % cols
        x, y = col * cs, row * cs

        if fmt == "white":
            draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(255, 255, 255, 0))
            color = (255, 255, 255, 255)
        else:
            draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(0, 0, 0, 0))
            color = (247, 247, 247, 255)

        draw_centered_glyph(img, x, y, cs, kr_char, font_path, font_size_kr,
                            color, stroke_width, STROKE_FILL)

    # Clear space glyph slot
    if 0 <= space_local < 1024:
        sr = space_local // cols
        sc = space_local % cols
        sx, sy = sc * cs, sr * cs
        draw.rectangle([sx, sy, sx + cs - 1, sy + cs - 1], fill=(0, 0, 0, 0))

    # Clear ASCII-space cell at local 224 (192 + 0x20). Game renders raw 0x20
    # at this position at half-width; must be transparent.
    ASCII_SPACE_LOCAL = 224
    if 0 <= ASCII_SPACE_LOCAL < 1024:
        asr = ASCII_SPACE_LOCAL // cols
        asc = ASCII_SPACE_LOCAL % cols
        ax, ay = asc * cs, asr * cs
        draw.rectangle([ax, ay, ax + cs - 1, ay + cs - 1], fill=(0, 0, 0, 0))

    # Render ASCII glyphs at positions 960+. Skip cells that Korean was
    # relocated into (cells 993-1003 for 둔/둘/둠/둥/둬/뒤/뒷/드/득/든) so
    # their Korean glyphs (drawn above) survive.
    pos = 960
    for code in range(0x20, 0x7F):
        if pos >= 1024:
            break
        if pos in korean_cells:
            pos += 1
            continue
        row = pos // cols
        col = pos % cols
        x, y = col * cs, row * cs
        ch = chr(code)
        if ch == ' ':
            draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(0, 0, 0, 0))
        else:
            if fmt == "white":
                draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(255, 255, 255, 0))
                acolor = (255, 255, 255, 255)
            else:
                draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(0, 0, 0, 0))
                acolor = (247, 247, 247, 255)
            align = "bottom-left" if ch in '.,' else "center"
            draw_centered_glyph(img, x, y, cs, ch, font_path, font_size_ascii,
                                acolor, stroke_width, STROKE_FILL, align=align)
        pos += 1

    # Runtime-ASCII overlay at cells 192+code: digits 0-9, plus ':', '?', '[',
    # ']', '-', '/' — characters the game emits as raw bytes (e.g.
    # "힘: 3", hidden blade-name "????", "[Sword]", "Effect -", time formatting
    # "1/13"). Cells originally held Korean glyphs we relocated in
    # kr_sjis_mapping.json.
    # NOTE: 0x2E '.' and 0x2C ',' EXCLUDED — RIDIBatang's tiny dot rendered
    # at cell center looks like middle-dot (·). Game export already has
    # proper dot at (4,17)-(12,25) in this cell; preserving export base.
    # 'F', 'o', 'r', 'm' added 2026-05-16 for DLC bakeneko equipment "Form:%s"
    # hardcoded in game binary. Korean SJIS for 딱/량/럴/랴 relocated to ASCII
    # zone (0x8EE2-0x8EE5) so cells 262/303/306/301 can hold English glyphs.
    RUNTIME_OVERLAY_CODES = list(range(0x30, 0x3A)) + [0x3A, 0x3F, 0x5B, 0x5D, 0x2D, 0x2F,
        0x46, 0x6F, 0x72, 0x6D,  # F, o, r, m
    ]
    for code in RUNTIME_OVERLAY_CODES:
        cell = 192 + code
        row = cell // cols
        col = cell % cols
        x, y = col * cs, row * cs
        if fmt == "white":
            draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(255, 255, 255, 0))
            dcolor = (255, 255, 255, 255)
        else:
            draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(0, 0, 0, 0))
            dcolor = (247, 247, 247, 255)
        ch = chr(code)
        if ch in '.,':
            align = "bottom-left"
        elif ch == ':':
            align = "colon-left"
        else:
            align = "center"
        draw_centered_glyph(img, x, y, cs, ch, font_path, font_size_ascii,
                            dcolor, stroke_width, STROKE_FILL, align=align)

    # Fullwidth-punctuation overlay: when the game emits raw SJIS 0x81xx bytes
    # (e.g. battle result hh:mm:ss timer hardcoded in eboot.bin using 0x8146
    # full-width colon) it reads KANJI texture local cell (b2 - 0x40) + 448.
    # Cell 454 originally held Korean "봐" — relocated to 0x8EEF (local 974)
    # in kr_sjis_mapping.json so we can draw the ASCII colon glyph here.
    FULLWIDTH_OVERLAY = {
        454: ':',  # 0x8146 fullwidth colon → battle result timer "0:00:19"
    }
    for local_cell, ch in FULLWIDTH_OVERLAY.items():
        row = local_cell // cols
        col = local_cell % cols
        x, y = col * cs, row * cs
        if fmt == "white":
            draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(255, 255, 255, 0))
            dcolor = (255, 255, 255, 255)
        else:
            draw.rectangle([x, y, x + cs - 1, y + cs - 1], fill=(0, 0, 0, 0))
            dcolor = (247, 247, 247, 255)
        draw_centered_glyph(img, x, y, cs, ch, font_path, font_size_ascii,
                            dcolor, stroke_width, STROKE_FILL)

    # Downscale to max_dim if needed
    if w > max_dim or h > max_dim:
        ds = max_dim / max(w, h)
        nw, nh = int(w * ds), int(h * ds)
        img = img.resize((nw, nh), Image.LANCZOS)
        print(f"  Downscaled: {nw}x{nh}")

    img.save(import_path, optimize=True)

    # Try pngquant
    quant_path = import_path + ".quant.png"
    result = subprocess.run(
        ["pngquant", "--quality=80-100", "--speed=1", "--force", "-o", quant_path, import_path],
        capture_output=True
    )
    if result.returncode == 0 and os.path.exists(quant_path):
        os.replace(quant_path, import_path)
        print(f"  pngquant applied")
    elif os.path.exists(quant_path):
        os.remove(quant_path)

    final_size = os.path.getsize(import_path)
    print(f"  Output: {final_size / 1024:.0f}KB, {len(korean_cells)} Korean glyphs")
    return len(korean_cells)


if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hd_dir = HD_PACK_DIR
    import_dir = IMPORT_DIR
    mapping_path = os.path.join(base_dir, "translations", "kr_sjis_mapping.json")
    font_path = os.path.join(base_dir, "fonts", "RIDIBatang.otf")

    # Font texture hashes that need Korean overlay.
    # NOTE: 87B72F6DB3C3FBDC was previously listed here but turned out to be a
    # foliage/plant background texture — overwriting it caused the DLC
    # difficulty screen to render our font atlas as background. Removed.
    font_hashes = ["6706A53E1D94C16E"]

    # Also handle font hashes from Vita3K export (session-dependent)
    export_dir = EXPORT_DIR

    print("=== HD Korean Font Import ===\n")

    for fhash in font_hashes:
        hd_path = os.path.join(hd_dir, f"{fhash}.png")
        if os.path.exists(hd_path):
            print(f"Processing HD base: {fhash}.png")
            import_path = os.path.join(import_dir, f"{fhash}.png")
            create_hd_korean_font(hd_path, import_path, mapping_path, font_path)
            print()
        else:
            print(f"HD base not found: {fhash}.png")

    # Check for additional font textures in export (session-specific hashes)
    if os.path.exists(export_dir):
        known = set(font_hashes)
        for fn in sorted(os.listdir(export_dir)):
            if not fn.endswith('.png'):
                continue
            fhash = fn.replace('.png', '')
            if fhash in known:
                continue
            img = Image.open(os.path.join(export_dir, fn))
            w, h = img.size
            if w < 1024 or h < 1024:
                continue
            arr = np.array(img.convert("RGBA"))
            alpha = arr[:, :, 3]
            # Check 32px grid pattern
            row_alpha = alpha.mean(axis=1)
            boundaries = [row_alpha[r] for r in range(0, min(512, h), 32)]
            inners = [row_alpha[r] for r in range(16, min(512, h), 32)]
            b_mean = sum(boundaries) / max(len(boundaries), 1)
            i_mean = sum(inners) / max(len(inners), 1)
            if b_mean < 5 and i_mean > 20:
                cell0_alpha = alpha[0:32, 0:32].mean()
                cell1_alpha = alpha[0:32, 32:64].mean()
                if cell0_alpha < 5 and cell1_alpha > 0 and cell1_alpha < 20:
                    continue  # ASCII page
                print(f"Processing export font: {fn}")
                # Use export as base (no HD version available)
                import_path = os.path.join(import_dir, fn)
                create_hd_korean_font(
                    os.path.join(export_dir, fn), import_path,
                    mapping_path, font_path, max_dim=1024
                )
                print()

    print("Done! Restart Vita3K for changes to take effect.")
