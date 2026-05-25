"""textures/kr/ 의 수동 편집 텍스처를 Vita3K import 폴더에 복사

사용법:
  python tools/install_textures.py            # 전체 복사
  python tools/install_textures.py DF66       # 해시 prefix 매칭만
  python tools/install_textures.py --dry-run  # 복사 없이 목록만 표시
"""

import shutil
import sys
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
SRC_DIRS = [
    PROJECT_DIR / "textures/kr" / "ui",
    PROJECT_DIR / "textures/kr" / "font",
]
TITLE_ID = "PCSE00240"


def resolve_import_dirs() -> list[Path]:
    explicit = os.environ.get("VITA3K_TEXTURE_IMPORT_DIR")
    if explicit:
        return [Path(explicit)]

    pref_path = os.environ.get("VITA3K_PREF_PATH")
    if pref_path:
        pref = Path(pref_path)
        return [
            pref / "textures" / "import" / TITLE_ID,
            pref / "fs" / "textures" / "import" / TITLE_ID,
        ]

    candidates = [
        Path.home() / "Library" / "Application Support" / "Vita3K" / "Vita3K" / "textures" / "import" / TITLE_ID,
        Path.home() / "Library" / "Application Support" / "Vita3K" / "Vita3K" / "fs" / "textures" / "import" / TITLE_ID,
        Path("C:/game/vita3k/textures/import") / TITLE_ID,
        Path("C:/game/vita3k/fs/textures/import") / TITLE_ID,
    ]
    existing = [candidate for candidate in candidates if candidate.exists() or candidate.parent.exists()]
    if existing:
        # Keep order and de-duplicate paths that resolve to the same location.
        seen = set()
        result = []
        for candidate in existing:
            key = candidate.resolve() if candidate.exists() else candidate
            if key in seen:
                continue
            seen.add(key)
            result.append(candidate)
        return result
    return candidates[:2] if sys.platform == "darwin" else candidates[2:]


def collect_texture_files() -> list[Path]:
    files_by_name = {}
    for src_dir in SRC_DIRS:
        if not src_dir.exists():
            continue
        for texture in sorted(src_dir.glob("*.png")):
            if texture.name in files_by_name:
                raise RuntimeError(f"duplicate texture name: {texture.name}")
            files_by_name[texture.name] = texture
    return [files_by_name[name] for name in sorted(files_by_name)]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dry_run = "--dry-run" in sys.argv

    files = collect_texture_files()
    if not files:
        print("ERROR: no textures/kr/*.png files found")
        return 1

    if args:
        prefix = args[0].upper()
        files = [f for f in files if f.stem.upper().startswith(prefix)]

    if not files:
        print("No matching textures found.")
        return 0

    import_dirs = resolve_import_dirs()
    copied, skipped = 0, 0
    for import_dir in import_dirs:
        import_dir.mkdir(parents=True, exist_ok=True)
        print(f"Target: {import_dir}")
        for src in files:
            dst = import_dir / src.name
            # skip if identical
            if dst.exists() and dst.stat().st_size == src.stat().st_size and dst.stat().st_mtime >= src.stat().st_mtime:
                print(f"  SKIP  {src.stem} (up to date)")
                skipped += 1
                continue
            if dry_run:
                print(f"  COPY  {src.stem} -> {dst}")
            else:
                shutil.copy2(src, dst)
                print(f"  COPY  {src.stem}")
            copied += 1

    print(f"\n{copied} copied, {skipped} skipped" + (" (dry-run)" if dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
