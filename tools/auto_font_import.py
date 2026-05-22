#!/usr/bin/env python
"""Auto-detect Vita3K font texture hashes and create Korean import textures.
Run this AFTER the game has started (textures exported) but BEFORE dialogue.

Safety: only touches font-specific imports, never deletes HD pack textures."""

import json, os, sys, time, platform, numpy as np
from PIL import Image, ImageFont, ImageDraw


def _default_vita3k_root():
    sysname = platform.system()
    if sysname == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Vita3K/Vita3K")
    if sysname == "Linux":
        return os.path.expanduser("~/.local/share/Vita3K/Vita3K")
    return "C:/game/vita3k"


def _default_hd_pack_dir():
    sysname = platform.system()
    if sysname == "Darwin":
        return os.path.expanduser("~/Downloads/Muramasa Complete 2.0/PCSE00240/Best")
    if sysname == "Linux":
        return os.path.expanduser("~/Downloads/Muramasa Complete 2.0/PCSE00240/Best")
    return "C:/Users/taro1/Downloads/Muramasa Complete 2.0/PCSE00240/Best"


VITA3K_ROOT = os.environ.get("VITA3K_ROOT", _default_vita3k_root())
EXPORT_DIR = os.environ.get("VITA3K_EXPORT_DIR", os.path.join(VITA3K_ROOT, "textures", "export", "PCSE00240"))
IMPORT_DIR = os.environ.get("VITA3K_IMPORT_DIR", os.path.join(VITA3K_ROOT, "textures", "import", "PCSE00240"))
HD_PACK_DIR = os.environ.get("HD_PACK_DIR", _default_hd_pack_dir())

# Glyph outline: 1.5px black stroke at 50% opacity (alpha=128). Since PIL only
# accepts integer stroke widths, fractional strokes are rendered via 2x
# supersampling (glyph drawn at 2x with stroke=3, then LANCZOS-downsampled to
# the target cell size). 1.5px sits between the too-thick 2px and too-thin 1px
# in small-cell rendering. Body kept at 20pt (Hangul) / 16pt (ASCII).
STROKE_WIDTH = 0
STROKE_FILL = (0, 0, 0, 128)

WHITESTROKE_FONT_HASHES = set()
WHITESTROKE_FILL = (255, 255, 255, 200)
KR_BODY_PT = 20
ASCII_BODY_PT = 16
MENU_FONT_HASHES = {"A8E6FDD162258699"}
MENU_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                              'fonts', 'Griun_PolSensibility-Rg.ttf')
MENU_STROKE_WIDTH = 0
MENU_KR_BODY_PT = 20
MENU_ASCII_BODY_PT = 18
MENU_PRESERVE_ASCII_HASHES = {"A8E6FDD162258699"}

_FONT_CACHE = {}

def _get_font(font_path, size):
    key = (font_path, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(font_path, size)
    return _FONT_CACHE[key]


def draw_centered_glyph(img, x, y, cs, ch, font_path, body_pt, fill, stroke_fp,
                        stroke_fill, align="center"):
    """Draw a glyph centered in cell (x..x+cs, y..y+cs) on RGBA img.

    align:
      "center"       — centered in cell
      "bottom-left"  — Korean punctuation '.'/',' (2px from left, 4px from bottom)
      "colon-left"   — ':' slightly left of center (8px from left edge)

    Fractional stroke_fp is rendered via 2x supersampling so non-integer
    strokes like 1.5px get a clean AA edge after downsample.
    """
    ss = 1 if float(stroke_fp).is_integer() else 2
    s_cs = int(cs * ss)
    s_pt = int(round(body_pt * ss))
    s_stroke = int(round(stroke_fp * ss))

    glyph = Image.new("RGBA", (s_cs, s_cs), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glyph)
    f = _get_font(font_path, s_pt)
    tb = gd.textbbox((0, 0), ch, font=f, stroke_width=s_stroke)
    gw = tb[2] - tb[0]
    gh = tb[3] - tb[1]
    # Padding scales with cs so HD bases (cs=128) match 1x semantics (cs=32)
    if align == "bottom-left":
        pad_l = (cs // 16) * ss   # 2px@32 / 8px@128
        pad_b = (cs // 8) * ss    # 4px@32 / 16px@128
        gx = pad_l - tb[0]
        gy = s_cs - gh - pad_b - tb[1]
    elif align == "colon-left":
        pad_l = (cs // 4) * ss    # 8px@32 / 32px@128
        gx = pad_l - tb[0]
        gy = (s_cs - gh) // 2 - tb[1]
    else:
        gx = (s_cs - gw) // 2 - tb[0]
        gy = (s_cs - gh) // 2 - tb[1]
    gd.text((gx, gy), ch, font=f, fill=fill, stroke_width=s_stroke,
            stroke_fill=stroke_fill)
    if ss > 1:
        glyph = glyph.resize((cs, cs), Image.LANCZOS)
    img.alpha_composite(glyph, (x, y))

# File to track which imports are font textures (so we only clean those)
FONT_HASH_RECORD = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".font_hashes.json")


def sjis_to_cell(b1, b2):
    if b2 < 0x80:
        b2_offset = b2 - 0x40
    else:
        b2_offset = b2 - 0x41
    return (b1 - 0x81) * 188 + b2_offset


def load_hd_hashes():
    """Load set of HD pack texture hashes for collision check."""
    hashes = set()
    if os.path.isdir(HD_PACK_DIR):
        for fn in os.listdir(HD_PACK_DIR):
            if fn.endswith('.png'):
                hashes.add(fn)
    return hashes


def load_old_font_hashes():
    """Load previous session's font hash record."""
    if os.path.exists(FONT_HASH_RECORD):
        with open(FONT_HASH_RECORD, 'r') as f:
            return set(json.load(f))
    return set()


def save_font_hashes(hashes):
    """Save current session's font hashes for cleanup next time."""
    with open(FONT_HASH_RECORD, 'w') as f:
        json.dump(sorted(hashes), f)


def is_font_grid(img_path):
    """Check if an image has 32px grid font pattern. Returns (is_font, info_dict)."""
    try:
        img = Image.open(img_path).convert("RGBA")
        w, h = img.size
        if w < 1024 or h < 1024:
            return False, {}
        arr = np.array(img)
        alpha = arr[:,:,3]

        # Font signature: 32px grid with alpha=0 boundary rows
        row_alpha = alpha.mean(axis=1)
        boundaries = [row_alpha[r] for r in range(0, 512, 32)]
        inners = [row_alpha[r] for r in range(16, 512, 32)]
        b_mean = sum(boundaries) / len(boundaries)
        i_mean = sum(inners) / len(inners)

        if not (b_mean < 5 and i_mean > 20):
            return False, {}

        rgb_mean = arr[:,:,:3].mean()
        cell0_alpha = alpha[0:32, 0:32].mean()
        cell1_alpha = alpha[0:32, 32:64].mean()

        # Check glyph color uniformity: sample opaque pixels only
        opaque = alpha > 30
        if opaque.sum() > 100:
            opaque_rgb = arr[:,:,:3][opaque]
            # Font glyphs are monochrome (R≈G≈B, all similar values)
            channel_spread = opaque_rgb.std(axis=1).mean()  # per-pixel RGB spread
        else:
            channel_spread = 0

        info = {
            'rgb': rgb_mean,
            'cell0': cell0_alpha,
            'cell1': cell1_alpha,
            'channel_spread': channel_spread,
        }

        # ASCII page: cell 0 empty (space) AND cell 1 has simple glyph ('!')
        if cell0_alpha < 5 and cell1_alpha > 0 and cell1_alpha < 20:
            return False, info  # ASCII page, skip

        # Game textures have colorful pixels (high channel spread, R≠G≠B)
        # Font glyphs are monochrome white/gray (low channel spread, R≈G≈B)
        if channel_spread > 30:
            return False, info  # colorful = not a font

        return True, info
    except:
        return False, {}


def find_font_textures(export_dir, hd_hashes):
    """Find font textures from exports. Handles HD pack fonts specially."""
    fonts = []       # (filename, rgb_mean, source) — source: 'export' or 'hd'

    for fn in sorted(os.listdir(export_dir)):
        if not fn.endswith('.png'):
            continue

        export_path = os.path.join(export_dir, fn)

        if fn in hd_hashes:
            # Hash exists in HD pack — check if the EXPORT is a font
            # (HD pack might have an HD version of the same font)
            is_font, info = is_font_grid(export_path)
            if is_font:
                # Both HD pack and export are fonts → use HD as base, overlay Korean
                fonts.append((fn, info.get('rgb', 0), 'hd'))
                print(f"  Font: {fn} RGB={info['rgb']:.0f} cell0={info['cell0']:.0f} cell1={info['cell1']:.0f} (KANJI, HD base)")
            # If export is NOT a font, the HD pack has a non-font texture for this hash → skip
            continue

        # Not in HD pack — normal font detection
        is_font, info = is_font_grid(export_path)
        if is_font:
            fonts.append((fn, info.get('rgb', 0), 'export'))
            print(f"  Font: {fn} RGB={info['rgb']:.0f} cell0={info['cell0']:.0f} cell1={info['cell1']:.0f} (KANJI page)")
        elif info:
            reason = "ASCII page" if info.get('cell0', 10) < 5 else f"spread={info.get('channel_spread',0):.0f}"
            print(f"  Skip: {fn} RGB={info.get('rgb',0):.0f} ({reason})")

    return fonts

def create_korean_import(export_path, import_path, mapping_path, font_path):
    """Create Korean font import texture."""
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    kr_map = mapping['korean_to_sjis']

    # 폰트 hash별 stroke 적용 여부 결정
    fhash = os.path.splitext(os.path.basename(export_path))[0]
    if fhash in WHITESTROKE_FONT_HASHES:
        # 메뉴 폰트: 흰색 stroke로 본체 두께만 증가 (외곽선 시각효과 없음)
        stroke_w = MENU_STROKE_WIDTH if fhash in MENU_FONT_HASHES else STROKE_WIDTH
        stroke_f = WHITESTROKE_FILL
    else:
        stroke_w = STROKE_WIDTH
        stroke_f = STROKE_FILL
    render_font_path = MENU_FONT_PATH if fhash in MENU_FONT_HASHES else font_path
    kr_body_pt = MENU_KR_BODY_PT if fhash in MENU_FONT_HASHES else KR_BODY_PT
    ascii_body_pt = MENU_ASCII_BODY_PT if fhash in MENU_FONT_HASHES else ASCII_BODY_PT

    # font/ascii_font no longer used directly — draw_centered_glyph caches them.
    cs = 32
    # SJIS code for space glyph (unused Korean char '빕' repurposed as blank)
    SPACE_SJIS = (0x8C, 0x6D)
    space_cell = sjis_to_cell(*SPACE_SJIS)
    space_local = space_cell - 1644

    korean_cells = {}
    protected_cells = set()
    if fhash in MENU_PRESERVE_ASCII_HASHES:
        protected_cells.update(192 + code for code in range(0x30, 0x3A))
    for char, (b1, b2) in kr_map.items():
        cell = sjis_to_cell(b1, b2)
        local = cell - 1644
        # Extended atlas: top half (cell 0..1023) = original KANJI page 1;
        # bottom half (cell 1024..2047) = expansion area for jamo overflow,
        # ASCII-collision Korean glyphs, hardcoded-kanji refuge slots.
        if 0 <= local < 2048:
            if local == space_local:
                continue  # reserve this slot as blank space
            if local in protected_cells:
                continue  # menu price digits must keep the original glyphs
            korean_cells[local] = char

    # Load original 1024x1024 font texture and expand height to 1024x2048
    # so cell index 1024..2047 maps to pixel rows 1024..2047. New SJIS slots
    # (0x8F64+) land in the expansion area without colliding with ASCII overlay
    # zone (cell 960..1023) or hardcoded-kanji cells.
    _src = Image.open(export_path).convert("RGBA")
    if _src.size[1] == 1024:
        img = Image.new('RGBA', (_src.size[0], 2048), (0, 0, 0, 0))
        img.paste(_src, (0, 0))
    else:
        img = _src
    arr = np.array(img)
    rgb_mean = arr[:,:,:3].mean()
    fmt = "white" if rgb_mean > 200 else "dark"

    draw = ImageDraw.Draw(img)
    cols = img.width // cs

    for local_idx, kr_char in korean_cells.items():
        row = local_idx // cols
        col = local_idx % cols
        x, y = col * cs, row * cs

        if fmt == "white":
            draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(255,255,255,0))
            color = (255,255,255,255)
        else:
            draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(0,0,0,0))
            color = (247,247,247,255)

        draw_centered_glyph(img, x, y, cs, kr_char, render_font_path, kr_body_pt,
                            color, stroke_w, stroke_f)

    # Clear the space glyph slot (make it transparent = blank space)
    if 0 <= space_local < 1024:
        sr = space_local // cols
        sc = space_local % cols
        sx, sy = sc * cs, sr * cs
        draw.rectangle([sx, sy, sx+cs-1, sy+cs-1], fill=(0, 0, 0, 0))

    # Clear the ASCII-space cell at local 224 (game renders raw 0x20 at
    # texture position 192+0x20 = 224, half-width). This must be transparent
    # so spaces don't show garbled glyphs from overlapping Korean data.
    ASCII_SPACE_LOCAL = 224  # 192 + 0x20
    if 0 <= ASCII_SPACE_LOCAL < 1024:
        asr = ASCII_SPACE_LOCAL // cols
        asc = ASCII_SPACE_LOCAL % cols
        ax, ay = asc * cs, asr * cs
        draw.rectangle([ax, ay, ax+cs-1, ay+cs-1], fill=(0, 0, 0, 0))

    if fhash not in MENU_PRESERVE_ASCII_HASHES:
        # Render ASCII glyphs at positions 960+ (remapped from Korean overlap zone).
        # Skip cells that Korean was relocated into (e.g. cells 993-1003 for
        # 둔/둘/둠/둥/둬/뒤/뒷/드/득/든). Those Korean glyphs were already drawn
        # above and must not be overwritten by ASCII letters.
        pos = 960
        for code in range(0x20, 0x7F):
            if pos >= 1024:
                break
            if pos in korean_cells:
                # Reserved for a relocated Korean glyph — do not overwrite.
                pos += 1
                continue
            row = pos // cols
            col = pos % cols
            x, y = col * cs, row * cs
            ch = chr(code)
            if ch == ' ':
                # Space: clear cell (transparent) — kept for safety even though
                # build_patch.py no longer emits the 2-byte remapped space.
                draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(0, 0, 0, 0))
            else:
                if fmt == "white":
                    draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(255,255,255,0))
                    acolor = (255,255,255,255)
                else:
                    draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(0,0,0,0))
                    acolor = (247,247,247,255)
                align = "bottom-left" if ch in '.,' else "center"
                draw_centered_glyph(img, x, y, cs, ch, render_font_path, ascii_body_pt,
                                    acolor, stroke_w, stroke_f, align=align)
            pos += 1

    # Runtime-ASCII overlay: when the game emits raw ASCII bytes (e.g. %d/%D
    # integers, ':' separators in stat labels, '?' placeholders in hidden blade
    # names, square brackets in blade category labels, '-' placeholders in empty
    # effect slots) it reads cells 192+code in this texture. Those cells
    # originally held Korean glyphs that we relocated in kr_sjis_mapping.json.
    # We overlay the actual ASCII glyph here so runtime output renders cleanly.
    # 'F', 'o', 'r', 'm' added 2026-05-16 for DLC bakeneko equipment "Form:%s"
    # hardcoded in game binary. Korean SJIS for 딱/량/럴/랴 relocated to ASCII
    # zone (0x8EE2-0x8EE5) so cells 262/303/306/301 can hold English glyphs.
    RUNTIME_OVERLAY_CODES = [] if fhash in MENU_PRESERVE_ASCII_HASHES else (
        list(range(0x30, 0x3A)) + [0x3A, 0x3F, 0x5B, 0x5D, 0x2D, 0x2E, 0x2F,
            0x46, 0x6F, 0x72, 0x6D,  # F, o, r, m
        ]
    )
    for code in RUNTIME_OVERLAY_CODES:
        cell = 192 + code
        row = cell // cols
        col = cell % cols
        x, y = col * cs, row * cs
        if fmt == "white":
            draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(255,255,255,0))
            dcolor = (255,255,255,255)
        else:
            draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(0,0,0,0))
            dcolor = (247,247,247,255)
        ch = chr(code)
        if ch in '.,':
            align = "bottom-left"
        elif ch == ':':
            # Position colon slightly left of cell center: 'Form:%s' game text
            # uses raw byte output where the colon's neighbor glyph is rendered
            # close. Pure left-align made ':' touch 'm'; centered made the
            # next Hangul touch ':'. ~8px offset balances both sides.
            align = "colon-left"
        else:
            align = "center"
        draw_centered_glyph(img, x, y, cs, ch, render_font_path, ascii_body_pt,
                            dcolor, stroke_w, stroke_f, align=align)

    # Fullwidth-punctuation overlay: when the game emits raw SJIS 0x81xx bytes
    # (e.g. battle result hh:mm:ss timer hardcoded in game binary using 0x8146
    # full-width colon) it reads KANJI texture local cell (b2 - 0x40) + 448.
    # Cell 454 originally held Korean "봐" — relocated to 0x8EEF (local 974)
    # in kr_sjis_mapping.json so we can draw the ASCII colon glyph here.
    FULLWIDTH_OVERLAY = {} if fhash in MENU_PRESERVE_ASCII_HASHES else {
        454: ':',  # 0x8146 fullwidth colon → battle result timer "0:00:19"
    }
    for local_cell, ch in FULLWIDTH_OVERLAY.items():
        row = local_cell // cols
        col = local_cell % cols
        x, y = col * cs, row * cs
        if fmt == "white":
            draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(255,255,255,0))
            dcolor = (255,255,255,255)
        else:
            draw.rectangle([x, y, x+cs-1, y+cs-1], fill=(0,0,0,0))
            dcolor = (247,247,247,255)
        draw_centered_glyph(img, x, y, cs, ch, render_font_path, ascii_body_pt,
                            dcolor, stroke_w, stroke_f)

    img.save(import_path)
    return len(korean_cells)

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    export_dir = EXPORT_DIR
    import_dir = IMPORT_DIR
    mapping_path = os.path.join(base_dir, "translations", "kr_sjis_mapping.json")
    font_path = os.path.join(base_dir, "fonts", "RIDIBatang.otf")

    os.makedirs(import_dir, exist_ok=True)

    # Load HD pack hashes for collision avoidance
    hd_hashes = load_hd_hashes()
    print(f"HD pack: {len(hd_hashes)} textures loaded for collision check")

    # Clean up ONLY previous session's font imports (not HD pack!)
    old_font_hashes = load_old_font_hashes()
    removed = 0
    for old_hash in old_font_hashes:
        old_path = os.path.join(import_dir, old_hash)
        if os.path.exists(old_path):
            # Restore HD pack version if it exists
            hd_path = os.path.join(HD_PACK_DIR, old_hash)
            if os.path.exists(hd_path):
                from shutil import copy2
                img = Image.open(hd_path)
                if max(img.width, img.height) > 2048:
                    ratio = 2048 / max(img.width, img.height)
                    img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
                img.save(old_path)
                img.close()
                print(f"  Restored HD: {old_hash}")
            else:
                os.remove(old_path)
                removed += 1
    if old_font_hashes:
        print(f"  Cleaned {len(old_font_hashes)} old font imports ({removed} removed, rest restored to HD)")

    print("\nScanning for font textures...")
    fonts = find_font_textures(export_dir, hd_hashes)

    if not fonts:
        print("No font textures found! Make sure the game is running and textures are exported.")
        save_font_hashes(set())
        sys.exit(1)

    print(f"\nFound {len(fonts)} font textures. Creating Korean imports...")
    new_font_hashes = set()
    for fn, rgb, source in fonts:
        if source == 'hd':
            # Use HD pack texture as base (higher resolution)
            hd_path = os.path.join(HD_PACK_DIR, fn)
            base_path = hd_path
        else:
            base_path = os.path.join(export_dir, fn)
        import_path = os.path.join(import_dir, fn)
        count = create_korean_import(base_path, import_path, mapping_path, font_path)
        new_font_hashes.add(fn)
        tag = " (HD base)" if source == 'hd' else ""
        print(f"  {fn}: {count} Korean glyphs{tag}")

    # Save current font hashes for next session cleanup
    save_font_hashes(new_font_hashes)

    print(f"\nDone! {len(fonts)} import textures created.")
    print(f"Safety: {len(hd_hashes)} HD hashes excluded from font detection.")
    print("Restart Vita3K for imports to take effect.")
