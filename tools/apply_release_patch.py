#!/usr/bin/env python3
"""Apply the Muramasa Korean patch release to a local Vita3K installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

PATCH_FORMAT = "muramasa-kor-binary-patch-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Vita3K 데이터 루트 탐지 (config.yml / portable / 플랫폼 기본) — 이슈 #19
#
# Vita3K 는 서로 다를 수 있는 두 종류의 루트를 쓴다:
#   - VitaFS 루트 : ux0/app/<TITLE>/*.cpk 가 사는 곳 (SDL pref path). config.yml 의
#                   pref-path(신빌드 vita_fs_path)로 재지정 가능. 비어 있으면 플랫폼 기본값.
#   - shared 루트 : textures/import, config.yml, cache 가 사는 곳 (SDL base path).
#                   Windows 일반 빌드는 Vita3K.exe 가 있는 폴더라서 VitaFS(%APPDATA%)와
#                   다를 수 있다. macOS/Linux 는 대개 VitaFS 의 부모(=config.yml 폴더).
# 그래서 CPK 는 VitaFS 루트에 패치하고, 텍스처는 알아낼 수 있는 모든 shared 루트 후보에
# 전부 복사해(어느 환경이든 덮이도록) 한다.
# ---------------------------------------------------------------------------

_CONFIG_DATA_KEYS = ("pref-path", "vita_fs_path")


def _dedup_paths(paths) -> list[Path]:
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        try:
            path = path.expanduser()
        except Exception:
            pass
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def parse_config_data_root(config_file: Path) -> Path | None:
    """Vita3K config.yml 에서 VitaFS 데이터 루트(pref-path / vita_fs_path)를 읽는다.

    상대경로(., ./, 또는 상대 경로 문자열)면 config.yml 이 있는 폴더 기준으로 해석한다.
    파싱 실패/키 없음이면 None."""
    try:
        text = config_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        for key in _CONFIG_DATA_KEYS:
            if stripped.startswith(key + ":"):
                value = stripped[len(key) + 1:].strip().strip('"').strip("'")
                if not value or value in (".", "./", ".\\"):
                    return config_file.parent
                path = Path(value).expanduser()
                if not path.is_absolute():
                    path = config_file.parent / path
                try:
                    return path.resolve()
                except OSError:
                    return path
    return None


def platform_config_dirs() -> list[Path]:
    """config.yml 이 있을 만한 플랫폼 기본 폴더들."""
    dirs: list[Path] = []
    if sys.platform == "win32":
        for env in ("APPDATA", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base:
                dirs.append(Path(base) / "Vita3K" / "Vita3K")
    elif sys.platform == "darwin":
        support = Path.home() / "Library" / "Application Support" / "Vita3K"
        dirs += [support / "Vita3K", support]
    else:
        dirs += [
            Path.home() / ".local" / "share" / "Vita3K" / "Vita3K",
            Path.home() / ".local" / "share" / "Vita3K",
            Path.home() / ".config" / "Vita3K",
        ]
    return dirs


def user_path_dirs(user_path: str | None) -> list[Path]:
    """사용자가 고른 폴더가 데이터 폴더/Vita3K.exe 설치 폴더/portable 상위 중
    무엇이든 커버하도록 관련 폴더 후보를 만든다."""
    if not user_path:
        return []
    base = Path(user_path).expanduser()
    return [base, base / "portable", base / "Vita3K", base / "Vita3K" / "Vita3K", base.parent]


def config_search_dirs(user_path: str | None) -> list[Path]:
    return _dedup_paths(user_path_dirs(user_path) + platform_config_dirs())


def default_pref_candidates(title_id: str, user_path: str | None = None) -> list[Path]:
    """VitaFS 루트 후보(우선순위 순). config.yml 의 pref-path 를 최우선으로 신뢰한다."""
    candidates: list[Path] = []
    env_pref = os.environ.get("VITA3K_PREF_PATH")
    if env_pref:
        candidates.append(Path(env_pref).expanduser())
    # 1) config.yml 이 가리키는 실제 데이터 루트 (실행 중인 에뮬레이터가 쓰는 폴더)
    for cfg_dir in config_search_dirs(user_path):
        cfg = cfg_dir / "config.yml"
        if cfg.is_file():
            data_root = parse_config_data_root(cfg)
            if data_root:
                candidates.append(data_root)
            candidates.append(cfg_dir)
    # 2) 사용자가 직접 준 폴더 및 관련 폴더
    candidates += user_path_dirs(user_path)
    # 3) 플랫폼 기본 위치
    candidates += platform_config_dirs()
    return _dedup_paths(candidates)


def content_root_candidates(paths: list[Path]) -> list[Path]:
    candidates: list[Path] = []
    for path in paths:
        expanded = path.expanduser()
        candidates.append(expanded)
        if expanded.name != "fs":
            candidates.append(expanded / "fs")
    return _dedup_paths(candidates)


def resolve_content_root(arg_path: str | None, title_id: str) -> Path:
    raw_candidates = default_pref_candidates(title_id, arg_path)
    candidates = content_root_candidates(raw_candidates)
    installed = [
        path for path in candidates
        if (path / "ux0" / "app" / title_id / "NinPri.cpk").exists()
    ]
    if installed:
        return installed[0]

    listed = "\n".join(f"  - {path}" for path in candidates)
    raise FileNotFoundError(
        "Could not find a Vita3K installation with Muramasa Rebirth installed.\n"
        "Pass the Vita3K root or content root explicitly:\n"
        "  python3 apply_patch.py --vita3k /path/to/Vita3K/Vita3K/fs\n"
        f"\nChecked:\n{listed}"
    )


def load_manifest(root: Path) -> dict:
    manifest_path = root / "release" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing release manifest: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def backup_path_for(target: Path, version: str) -> Path:
    backup_dir = target.parent / ".muramasa-kor-backup"
    return backup_dir / f"{target.name}.v{version}.original"


def backup_candidates_for(target: Path, version: str) -> list[Path]:
    exact = backup_path_for(target, version)
    candidates = [exact]
    if exact.parent.exists():
        for path in sorted(exact.parent.glob(f"{target.name}.v*.original"), reverse=True):
            if path != exact:
                candidates.append(path)
    return candidates


def find_original_backup(target: Path, file_entry: dict, version: str) -> Path | None:
    expected_sha = file_entry["source_sha256"]
    for candidate in backup_candidates_for(target, version):
        if not candidate.exists():
            continue
        if sha256_file(candidate) == expected_sha:
            return candidate
    return None


def apply_file_patch(root: Path, content_root: Path, manifest: dict, file_entry: dict, dry_run: bool) -> str:
    version = manifest["version"]
    target_path = content_root / file_entry["install_path"]
    if not target_path.exists():
        raise FileNotFoundError(f"Missing installed file: {target_path}")

    current_sha = sha256_file(target_path)
    if current_sha == file_entry["target_sha256"]:
        return f"SKIP  {file_entry['name']} already patched"
    if current_sha != file_entry["source_sha256"]:
        backup_dir = target_path.parent / ".muramasa-kor-backup"
        raise RuntimeError(
            f"{file_entry['name']} hash mismatch.\n"
            f"  path: {target_path}\n"
            f"  expected original: {file_entry['source_sha256']}\n"
            f"  expected patched : {file_entry['target_sha256']}\n"
            f"  actual          : {current_sha}\n"
            "Restore the original CPK backup before applying this release:\n"
            "  python3 apply_patch.py --restore\n"
            f"Backup folder:\n  {backup_dir}\n"
            "If no matching original backup exists, reinstall the original US game + update 1.06."
        )

    patch_path = root / file_entry["patch_file"]
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    if patch.get("format") != PATCH_FORMAT:
        raise RuntimeError(f"Unsupported patch format in {patch_path}: {patch.get('format')}")
    if patch["source_sha256"] != file_entry["source_sha256"]:
        raise RuntimeError(f"Patch/source hash mismatch in {patch_path}")

    blob_path = patch_path.parent / patch["blob_file"]
    if sha256_file(blob_path) != patch["blob_sha256"]:
        raise RuntimeError(f"Patch blob hash mismatch: {blob_path}")

    backup_path = backup_path_for(target_path, version)
    if dry_run:
        return f"WOULD {file_entry['name']} -> {target_path}"

    tmp_path = target_path.with_name(f"{target_path.name}.muramasa-kor.tmp")
    if tmp_path.exists():
        tmp_path.unlink()
    shutil.copy2(target_path, tmp_path)

    try:
        with tmp_path.open("r+b") as out, blob_path.open("rb") as blob:
            for chunk in patch["chunks"]:
                blob.seek(chunk["blob_offset"])
                data = blob.read(chunk["length"])
                if len(data) != chunk["length"]:
                    raise RuntimeError(f"Unexpected end of patch blob: {blob_path}")
                out.seek(chunk["offset"])
                out.write(data)
            out.truncate(patch["target_size"])

        patched_sha = sha256_file(tmp_path)
        if patched_sha != file_entry["target_sha256"]:
            raise RuntimeError(
                f"Patched file verification failed for {file_entry['name']}.\n"
                f"  expected: {file_entry['target_sha256']}\n"
                f"  actual  : {patched_sha}"
            )

        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if not backup_path.exists():
            shutil.copy2(target_path, backup_path)
        os.replace(tmp_path, target_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    return f"PATCH {file_entry['name']} -> {target_path}"


def _looks_like_vita3k_root(path: Path) -> bool:
    """실제 Vita3K 데이터/shared 폴더처럼 보이는지(엉뚱한 폴더에 텍스처를 뿌리지 않도록)."""
    try:
        return path.is_dir() and any((path / name).exists()
                                     for name in ("config.yml", "ux0", "textures"))
    except OSError:
        return False


def _running_vita3k_dirs() -> list[Path]:
    """실행 중인 Vita3K 프로세스의 실행파일 폴더(=Windows shared 루트)를 best-effort 로 찾는다.

    사용자가 실제로 쓰는 설치본을 가장 확실히 알려주는 신호다. 실패는 조용히 무시한다."""
    dirs: list[Path] = []
    import subprocess
    if sys.platform == "win32":
        # wmic 는 최신 Windows 11 에서 제거될 수 있어 PowerShell CIM 폴백을 함께 시도한다.
        cmds = [
            ["wmic", "process", "where", "name='Vita3K.exe'", "get", "ExecutablePath"],
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"name='Vita3K.exe'\" "
             "| Select-Object -ExpandProperty ExecutablePath"],
        ]
        for cmd in cmds:
            try:
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
            except Exception:
                continue
            for line in out.splitlines():
                line = line.strip()
                if line.lower().endswith("vita3k.exe"):
                    dirs.append(Path(line).parent)
            if dirs:
                break
    else:
        try:
            out = subprocess.run(["pgrep", "-af", "Vita3K"], capture_output=True, text=True, timeout=8).stdout
            for line in out.splitlines():
                for token in line.split():
                    if token.endswith("Vita3K") or token.endswith("Vita3K.exe"):
                        p = Path(token)
                        if p.exists():
                            dirs.append(p.parent)
        except Exception:
            pass
    return dirs


def _common_vita3k_install_dirs() -> list[Path]:
    """Vita3K.exe 가 있을 법한 흔한 설치 폴더들(존재하고 실제 exe가 있는 것만). Windows 위주."""
    guesses: list[Path] = []
    if sys.platform == "win32":
        home = Path.home()
        env = os.environ
        bases = [
            env.get("LOCALAPPDATA"), env.get("PROGRAMFILES"), env.get("PROGRAMFILES(X86)"),
            str(home), str(home / "Desktop"), str(home / "Downloads"), str(home / "Documents"),
            "C:/", "D:/",
        ]
        names = ["Vita3K", "vita3k", "Programs/Vita3K", "emulators/Vita3K", "Emulators/Vita3K"]
        for base in filter(None, bases):
            for name in names:
                guesses.append(Path(base) / name)
    result: list[Path] = []
    for d in _dedup_paths(guesses):
        try:
            if (d / "Vita3K.exe").exists():
                result.append(d)
        except OSError:
            pass
    return result


def texture_import_roots(content_root: Path, user_path: str | None = None) -> list[Path]:
    """텍스처(import) 를 설치할 shared 루트 후보 전체 — 이슈 #19.

    Vita3K 는 VitaFS(ux0) 루트와 textures 루트가 다를 수 있다(특히 Windows 일반 빌드는
    textures 를 Vita3K.exe 옆에서 읽는다). 알아낼 수 있는 모든 후보에 텍스처를 복사해
    어떤 환경이든 덮이게 한다. content_root 는 항상 포함하고, 나머지는 실제 Vita3K
    폴더처럼 보이는 것만 채택한다."""
    roots: list[Path] = [content_root]
    # content_root 기준 변형 (fs 상호 변환)
    if content_root.name == "fs":
        roots.append(content_root.parent)
    else:
        roots.append(content_root / "fs")
        roots.append(content_root.parent)
    # config.yml 이 있는 폴더(=shared 루트) 및 그 config 가 가리키는 데이터 루트
    for cfg_dir in config_search_dirs(user_path):
        roots.append(cfg_dir)
        cfg = cfg_dir / "config.yml"
        if cfg.is_file():
            data_root = parse_config_data_root(cfg)
            if data_root:
                roots.append(data_root)
                if data_root.name == "fs":
                    roots.append(data_root.parent)
    # 사용자가 직접 준 폴더(Vita3K.exe 폴더 등) 및 관련 폴더
    roots += user_path_dirs(user_path)
    # 실행 중인 Vita3K 프로세스 폴더 + 흔한 설치 위치(Windows shared 루트 자동 커버)
    roots += _running_vita3k_dirs()
    roots += _common_vita3k_install_dirs()

    result: list[Path] = []
    for candidate in _dedup_paths(roots):
        if candidate == content_root or _looks_like_vita3k_root(candidate):
            result.append(candidate)
    return result


def install_textures(root: Path, content_root: Path, title_id: str, dry_run: bool,
                     user_path: str | None = None) -> str:
    source_dir = root / "textures" / "import" / title_id
    if not source_dir.exists():
        return "SKIP  texture import files not included"

    files = sorted(source_dir.glob("*.png"))
    dests = texture_import_roots(content_root, user_path)
    if dry_run:
        listed = ", ".join(str(base / "textures" / "import" / title_id) for base in dests)
        return f"WOULD copy {len(files)} texture imports -> {listed}"

    parts = []
    for base in dests:
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
    return "COPY  texture imports:\n      " + "\n      ".join(parts)


def restore_originals(content_root: Path, manifest: dict, dry_run: bool) -> int:
    restored = 0
    version = manifest["version"]
    for file_entry in manifest["files"]:
        target_path = content_root / file_entry["install_path"]
        backup_path = find_original_backup(target_path, file_entry, version)
        if backup_path is None:
            backup_dir = target_path.parent / ".muramasa-kor-backup"
            print(f"SKIP  no matching original backup for {file_entry['name']}: {backup_dir}")
            continue
        if dry_run:
            print(f"WOULD restore {backup_path} -> {target_path}")
        else:
            shutil.copy2(backup_path, target_path)
            print(f"RESTORE {file_entry['name']} -> {target_path}")
        restored += 1
    return restored


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Muramasa Rebirth Korean patch to Vita3K.")
    parser.add_argument(
        "--vita3k",
        help="Vita3K root or content root. Uses platform defaults when omitted.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate paths and hashes without writing files.")
    parser.add_argument("--no-textures", action="store_true", help="Patch CPK files only.")
    parser.add_argument("--restore", action="store_true", help="Restore original CPK backups.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    manifest = load_manifest(root)
    title_id = manifest["title_id"]
    content_root = resolve_content_root(args.vita3k, title_id)

    print(f"Muramasa Korean Patch v{manifest['version']}")
    print(f"Vita3K content root: {content_root}")

    if args.restore:
        restored = restore_originals(content_root, manifest, args.dry_run)
        print(f"Done. Restored {restored} file(s).")
        return 0

    for file_entry in manifest["files"]:
        print(apply_file_patch(root, content_root, manifest, file_entry, args.dry_run))

    if not args.no_textures:
        print(install_textures(root, content_root, title_id, args.dry_run, args.vita3k))

    print("Done. Enable Vita3K GPU texture import if UI/font textures do not appear.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
