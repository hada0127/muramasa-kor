#!/usr/bin/env python
"""Auto-detect Vita3K font texture hashes and create Korean import textures.
Run this AFTER the game has started (textures exported) but BEFORE dialogue.

Safety: only touches font-specific imports, never deletes HD pack textures."""

import json, os, sys, time, numpy as np
from PIL import Image, ImageFont, ImageDraw

# HD texture pack location
HD_PACK_DIR = "C:/Users/taro1/Downloads/Muramasa Complete 2.0/PCSE00240/Best"
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

    font = ImageFont.truetype(font_path, 22)
    cs = 32
    # SJIS code for space glyph (unused Korean char '빕' repurposed as blank)
    SPACE_SJIS = (0x8C, 0x6D)
    space_cell = sjis_to_cell(*SPACE_SJIS)
    space_local = space_cell - 1644

    korean_cells = {}
    for char, (b1, b2) in kr_map.items():
        cell = sjis_to_cell(b1, b2)
        local = cell - 1644
        if 0 <= local < 1024:
            if local == space_local:
                continue  # reserve this slot as blank space
            korean_cells[local] = char

    img = Image.open(export_path).convert("RGBA")
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

        bbox = font.getbbox(kr_char)
        gw = bbox[2] - bbox[0]
        gh = bbox[3] - bbox[1]
        gx = x + (cs - gw) // 2 - bbox[0]
        gy = y + (cs - gh) // 2 - bbox[1]
        draw.text((gx, gy), kr_char, font=font, fill=color)

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

    # Render ASCII glyphs at positions 960+ (remapped from Korean overlap zone).
    # Skip cells that Korean was relocated into (e.g. cells 993-1003 for
    # 둔/둘/둠/둥/둬/뒤/뒷/드/득/든). Those Korean glyphs were already drawn
    # above and must not be overwritten by ASCII letters.
    ascii_font = ImageFont.truetype(font_path, 18)  # slightly smaller for ASCII
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
            bbox = ascii_font.getbbox(ch)
            gw = bbox[2] - bbox[0]
            gh = bbox[3] - bbox[1]
            if ch in '.,':
                # Korean punctuation: bottom-left aligned
                gx = x + 2 - bbox[0]
                gy = y + cs - gh - 4 - bbox[1]
            else:
                gx = x + (cs - gw) // 2 - bbox[0]
                gy = y + (cs - gh) // 2 - bbox[1]
            draw.text((gx, gy), ch, font=ascii_font, fill=acolor)
        pos += 1

    # Runtime-ASCII overlay: when the game emits raw ASCII bytes (e.g. %d/%D
    # integers, ':' separators in stat labels, '-' placeholders in empty
    # effect slots) it reads cells 192+code in this texture. Those cells
    # originally held Korean glyphs that we relocated in kr_sjis_mapping.json.
    # We overlay the actual ASCII glyph here so runtime output renders cleanly.
    RUNTIME_OVERLAY_CODES = list(range(0x30, 0x3A)) + [0x3A, 0x2D, 0x2E, 0x2F]
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
        bbox = ascii_font.getbbox(ch)
        gw = bbox[2] - bbox[0]
        gh = bbox[3] - bbox[1]
        if ch in '.,':
            gx = x + 2 - bbox[0]
            gy = y + cs - gh - 4 - bbox[1]
        else:
            gx = x + (cs - gw) // 2 - bbox[0]
            gy = y + (cs - gh) // 2 - bbox[1]
        draw.text((gx, gy), ch, font=ascii_font, fill=dcolor)

    img.save(import_path)
    return len(korean_cells)

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    export_dir = "C:/game/vita3k/textures/export/PCSE00240/"
    import_dir = "C:/game/vita3k/textures/import/PCSE00240/"
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
