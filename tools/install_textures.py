"""kr_textures/ui/ 의 수동 편집 텍스처를 Vita3K import 폴더에 복사

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
SRC_DIR = PROJECT_DIR / "kr_textures" / "ui"
TITLE_ID = "PCSE00240"


def resolve_import_dir() -> Path:
    explicit = os.environ.get("VITA3K_TEXTURE_IMPORT_DIR")
    if explicit:
        return Path(explicit)

    pref_path = os.environ.get("VITA3K_PREF_PATH")
    if pref_path:
        return Path(pref_path) / "textures" / "import" / TITLE_ID

    candidates = [
        Path.home() / "Library" / "Application Support" / "Vita3K" / "Vita3K" / "textures" / "import" / TITLE_ID,
        Path("C:/game/vita3k/textures/import") / TITLE_ID,
    ]
    for candidate in candidates:
        if candidate.exists() or candidate.parent.exists():
            return candidate
    return candidates[0] if sys.platform == "darwin" else candidates[-1]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dry_run = "--dry-run" in sys.argv

    if not SRC_DIR.exists():
        print(f"ERROR: {SRC_DIR} not found")
        return 1

    import_dir = resolve_import_dir()
    import_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(SRC_DIR.glob("*.png"))
    if args:
        prefix = args[0].upper()
        files = [f for f in files if f.stem.upper().startswith(prefix)]

    if not files:
        print("No matching textures found.")
        return 0

    copied, skipped = 0, 0
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
