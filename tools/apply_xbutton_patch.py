#!/usr/bin/env python3
"""Muramasa 한글 패치 — ✕ 버튼 추가팩 설치기 (이슈 #12).

기존 한글 패치가 설치된 Vita3K 위에, 선택/확인 버튼 표시를 ○ → ✕ 로 바꾸는
텍스처 2개만 덮어쓴다. 본편 패치(CPK/폰트/다른 UI)는 건드리지 않는다.

  설치:  python3 apply_xbutton.py
  복원:  python3 apply_xbutton.py --restore   (○ 버튼 텍스처로 되돌림)

★ 중요: 게임이 버튼 글리프를 자체 텍스처로 그리므로, 이 팩은 화면 '표시'만 ✕로 바꾼다.
   실제로 ✕가 '확인'이 되게 하려면 Vita3K 설정에서
       Settings → Controls(또는 System) → Enter Button Assignment = Cross
   로 두어야 한다. (○ 확인을 쓰던 분은 굳이 이 팩을 쓰지 않아도 된다.)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_pref_candidates() -> list[Path]:
    candidates: list[Path] = []
    env_pref = os.environ.get("VITA3K_PREF_PATH")
    if env_pref:
        candidates.append(Path(env_pref).expanduser())
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidates.append(Path(appdata) / "Vita3K" / "Vita3K")
    elif sys.platform == "darwin":
        candidates.append(Path.home() / "Library" / "Application Support" / "Vita3K" / "Vita3K")
    else:
        candidates.append(Path.home() / ".local" / "share" / "Vita3K")
    seen: set[Path] = set()
    unique: list[Path] = []
    for c in candidates:
        r = c.expanduser()
        if r not in seen:
            unique.append(r)
            seen.add(r)
    return unique


def content_root_candidates(paths: list[Path]) -> list[Path]:
    candidates: list[Path] = []
    for path in paths:
        expanded = path.expanduser()
        candidates.append(expanded)
        if expanded.name != "fs":
            candidates.append(expanded / "fs")
    seen: set[Path] = set()
    unique: list[Path] = []
    for c in candidates:
        if c not in seen:
            unique.append(c)
            seen.add(c)
    return unique


def resolve_content_root(arg_path: str | None, title_id: str) -> Path:
    raw = [Path(arg_path).expanduser()] if arg_path else default_pref_candidates()
    candidates = content_root_candidates(raw)
    installed = [p for p in candidates if (p / "ux0" / "app" / title_id / "NinPri.cpk").exists()]
    if installed:
        return installed[0]
    listed = "\n".join(f"  - {p}" for p in candidates)
    raise FileNotFoundError(
        "Muramasa Rebirth가 설치된 Vita3K를 찾지 못했습니다.\n"
        "Vita3K 루트(또는 content root)를 직접 지정하세요:\n"
        "  python3 apply_xbutton.py --vita3k /path/to/Vita3K/Vita3K/fs\n"
        f"\n확인한 경로:\n{listed}"
    )


def texture_import_roots(content_root: Path) -> list[Path]:
    roots = [content_root]
    if content_root.name == "fs":
        roots.append(content_root.parent)
    seen: set[Path] = set()
    unique: list[Path] = []
    for r in roots:
        if r not in seen:
            unique.append(r)
            seen.add(r)
    return unique


def load_manifest(root: Path) -> dict:
    p = root / "xbutton-manifest.json"
    if not p.exists():
        raise FileNotFoundError(f"매니페스트 없음: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def copy_textures(root: Path, content_root: Path, title_id: str, src_subdir: str, dry_run: bool) -> str:
    source_dir = root / src_subdir
    files = sorted(source_dir.glob("*.png"))
    if not files:
        return f"SKIP  {src_subdir}에 텍스처 없음"
    if dry_run:
        dests = ", ".join(str(b / "textures" / "import" / title_id) for b in texture_import_roots(content_root))
        return f"WOULD copy {len(files)} textures ({src_subdir}) -> {dests}"
    parts = []
    for base in texture_import_roots(content_root):
        dest_dir = base / "textures" / "import" / title_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        copied = 0
        for source in files:
            dest = dest_dir / source.name
            if dest.exists() and sha256_file(dest) == sha256_file(source):
                continue
            shutil.copy2(source, dest)
            copied += 1
        parts.append(f"{copied}/{len(files)} -> {dest_dir}")
    return "COPY  " + "; ".join(parts)


REMINDER = (
    "\n────────────────────────────────────────────────────────\n"
    "★ 화면 표시만 ✕로 바뀝니다. 실제 '확인' 버튼까지 ✕로 쓰려면\n"
    "  Vita3K 설정 → Enter Button Assignment = Cross 로 변경하세요.\n"
    "  (게임 자체가 버튼 글리프를 그리므로 텍스처만으로는 입력이 안 바뀝니다.)\n"
    "────────────────────────────────────────────────────────"
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Muramasa 한글 패치 ✕ 버튼 추가팩 설치/복원.")
    parser.add_argument("--vita3k", help="Vita3K 루트 또는 content root. 생략 시 플랫폼 기본값 탐색.")
    parser.add_argument("--restore", action="store_true", help="○ 버튼 텍스처로 되돌립니다.")
    parser.add_argument("--dry-run", action="store_true", help="경로만 확인하고 쓰지 않습니다.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    manifest = load_manifest(root)
    title_id = manifest["title_id"]
    content_root = resolve_content_root(args.vita3k, title_id)

    print(f"Muramasa 한글 패치 — ✕ 버튼 추가팩 v{manifest.get('version','?')}")
    print(f"Vita3K content root: {content_root}")

    subdir = "restore-o" if args.restore else "xbutton"
    print(copy_textures(root, content_root, title_id, subdir, args.dry_run))

    if args.restore:
        print("완료. ○ 버튼 텍스처로 되돌렸습니다.")
    else:
        print("완료. Vita3K를 재시작하면 버튼이 ✕로 보입니다.")
        print(REMINDER)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
