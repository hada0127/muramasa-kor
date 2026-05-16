#!/usr/bin/env python3
"""Vita3K English/Korean mode toggle.

Used after a re-patch to switch the installed game (CPK + texture import)
between:
  - english: original CPK from backup/ + Korean fonts/textures hidden
  - korean:  Korean-patched CPK from output/ + Korean fonts/textures restored

Korean assets are not deleted — they are moved to .vita3k_mode_backup/ inside
the import directory so the toggle is reversible.

For one-off English-text verification (e.g. tracing NMS lookups), prefer
renaming the whole import/PCSE00240 dir to .disabled directly — that hides
ALL imports including HD pack overrides this script doesn't track.

Usage:
    python3 tools/vita3k_mode.py status      # show current mode + asset counts
    python3 tools/vita3k_mode.py english     # restore original CPK + hide Korean assets
    python3 tools/vita3k_mode.py korean      # restore patched CPK + restore Korean assets
"""

import argparse
import glob
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VITA = Path.home() / "Library/Application Support/Vita3K/Vita3K"
APP = VITA / "fs/ux0/app/PCSE00240"
IMPORT = VITA / "textures/import/PCSE00240"
CACHE_SHADERS = VITA / "cache/shaders/PCSE00240"
SHADERLOG = VITA / "shaderlog/PCSE00240"
BACKUP_DIR = IMPORT / ".vita3k_mode_backup"

CPKS = ["NinPri.cpk", "NinPriPatch.cpk"]
ORIG_DIR = REPO / "backup"
KOR_OUTPUT_DIR = REPO / "output"
KOR_OUTPUT_SUFFIX = "_final.cpk"

KR_FONT_HASHES = ["6706A53E1D94C16E.png", "8665CE082D339B33.png", "A8E6FDD162258699.png"]


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def kr_ui_textures() -> list[str]:
    return [os.path.basename(p) for p in glob.glob(str(REPO / "kr_textures/ui/*.png"))]


def kr_assets() -> list[str]:
    """All Korean-patched assets (fonts + UI textures)."""
    return sorted(set(KR_FONT_HASHES + kr_ui_textures()))


def kill_vita3k():
    subprocess.run(["pkill", "-9", "-f", "Vita3K"], capture_output=True)


def clear_cache():
    for p in [CACHE_SHADERS, SHADERLOG]:
        if p.exists():
            shutil.rmtree(p)


def install_cpk(src_dir: Path, name_template: str | None = None) -> dict[str, str]:
    """Copy CPKs from src_dir to game directory. Returns MD5 map."""
    md5s = {}
    for cpk in CPKS:
        src = src_dir / (cpk if not name_template else name_template.format(stem=cpk[:-4]))
        dst = APP / cpk
        if not src.exists():
            print(f"  MISSING: {src}")
            continue
        shutil.copy2(src, dst)
        m = md5(dst)
        md5s[cpk] = m
        print(f"  Installed {cpk} ({src.stat().st_size:,}B) md5={m}")
    return md5s


def to_english():
    print("=== Switching to ENGLISH mode ===")
    kill_vita3k()
    print("\n[1/4] Restore original CPK from backup/")
    install_cpk(ORIG_DIR)
    print("\n[2/4] Hide Korean assets from import/")
    BACKUP_DIR.mkdir(exist_ok=True)
    moved = 0
    for name in kr_assets():
        src = IMPORT / name
        if src.exists():
            shutil.move(str(src), str(BACKUP_DIR / name))
            moved += 1
    print(f"  Moved {moved} Korean assets to {BACKUP_DIR.name}/")
    print("\n[3/4] Clear shader cache")
    clear_cache()
    print("  Done")
    print("\n[4/4] Status")
    status()


def to_korean():
    print("=== Switching to KOREAN mode ===")
    kill_vita3k()
    print("\n[1/4] Install Korean-patched CPK from output/")
    install_cpk(KOR_OUTPUT_DIR, name_template="{stem}_final.cpk")
    print("\n[2/4] Restore Korean assets to import/")
    restored = 0
    if BACKUP_DIR.exists():
        for src in BACKUP_DIR.iterdir():
            if src.is_file() and src.name.endswith(".png"):
                shutil.move(str(src), str(IMPORT / src.name))
                restored += 1
    print(f"  Restored {restored} Korean assets")
    print("\n[3/4] Clear shader cache")
    clear_cache()
    print("  Done")
    print("\n[4/4] Status")
    status()


def status():
    print(f"  IMPORT dir: {IMPORT}")
    # CPK MD5 vs backup / output
    for cpk in CPKS:
        installed = APP / cpk
        if not installed.exists():
            print(f"  {cpk}: NOT INSTALLED")
            continue
        m = md5(installed)
        orig = ORIG_DIR / cpk
        patched = KOR_OUTPUT_DIR / (cpk[:-4] + KOR_OUTPUT_SUFFIX)
        flag = "?"
        if orig.exists() and md5(orig) == m:
            flag = "ORIGINAL (English)"
        elif patched.exists() and md5(patched) == m:
            flag = "PATCHED (Korean)"
        else:
            flag = "OTHER/CUSTOM"
        print(f"  {cpk}: md5={m} → {flag}")

    # Korean asset presence in import vs backup
    in_import = [n for n in kr_assets() if (IMPORT / n).exists()]
    in_backup = [n for n in kr_assets() if (BACKUP_DIR / n).exists()] if BACKUP_DIR.exists() else []
    print(f"  Korean assets: {len(in_import)} in import, {len(in_backup)} hidden in backup")


def main():
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("mode", choices=["english", "korean", "status"],
                        help="Target mode (or 'status' to inspect current state)")
    args = parser.parse_args()

    if args.mode == "status":
        status()
    elif args.mode == "english":
        to_english()
    elif args.mode == "korean":
        to_korean()


if __name__ == "__main__":
    main()
