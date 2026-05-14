#!/usr/bin/env python3
"""
Build a versioned Vita3K local-patcher release into dist/.

The release zip intentionally does not contain full CPK files. It contains:
1. small binary patch data generated from original CPK -> patched CPK
2. a standalone Python patcher for Windows/macOS/Linux
3. Vita3K texture import PNGs
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import build_patch
import cpk_patch

PROJECT_DIR = Path(__file__).resolve().parent.parent
TITLE_ID = "PCSE00240"
VERSION_FILE = PROJECT_DIR / "release" / "version.json"
DIST_DIR = PROJECT_DIR / "dist"
OUTPUT_DIR = PROJECT_DIR / "output"
PATCH_MAIN_DIR = PROJECT_DIR / "patch_main"
PATCH_PATCH_DIR = PROJECT_DIR / "patch_patch"
TEXTURE_DIRS = [
    PROJECT_DIR / "kr_textures" / "ui",
    PROJECT_DIR / "kr_textures" / "font",
]
PATCHER_TEMPLATE = PROJECT_DIR / "tools" / "apply_release_patch.py"
MAIN_CPK = PROJECT_DIR / "backup" / "NinPri.cpk"
PATCH_CPK = PROJECT_DIR / "backup" / "NinPriPatch.cpk"
PATCH_FORMAT = "muramasa-kor-binary-patch-v1"


def load_version() -> str:
    data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    version = str(data["version"]).strip()
    if not version:
        raise ValueError(f"Empty version in {VERSION_FILE}")
    return version


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_replacements(mod_dir: Path) -> dict[str, bytes]:
    replacements: dict[str, bytes] = {}
    for file_path in sorted(p for p in mod_dir.rglob("*") if p.is_file()):
        if file_path.name == ".DS_Store":
            continue
        rel = file_path.relative_to(mod_dir).as_posix()
        replacements[rel] = file_path.read_bytes()
    return replacements


def collect_texture_files() -> list[Path]:
    texture_by_name: dict[str, Path] = {}
    for texture_dir in TEXTURE_DIRS:
        if not texture_dir.exists():
            continue
        for texture in sorted(texture_dir.glob("*.png")):
            existing = texture_by_name.get(texture.name)
            if existing is not None:
                raise ValueError(f"Duplicate texture import name: {texture.name} in {existing} and {texture}")
            texture_by_name[texture.name] = texture
    return [texture_by_name[name] for name in sorted(texture_by_name)]


def require_inputs() -> None:
    required = [
        VERSION_FILE,
        MAIN_CPK,
        PATCH_CPK,
        PATCHER_TEMPLATE,
        PROJECT_DIR / "translations" / "jp_messages.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {item}" for item in missing)
        raise FileNotFoundError(f"Missing required inputs:\n{missing_list}")


def build_cpks() -> tuple[Path, Path]:
    print("== Building NMS patch files ==")
    build_patch.build_korean_patch()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    main_out = OUTPUT_DIR / "NinPri_final.cpk"
    patch_out = OUTPUT_DIR / "NinPriPatch_final.cpk"

    print("\n== Building patched CPKs ==")
    cpk_patch.patch_cpk_append(str(MAIN_CPK), str(main_out), collect_replacements(PATCH_MAIN_DIR))
    cpk_patch.patch_cpk_append(str(PATCH_CPK), str(patch_out), collect_replacements(PATCH_PATCH_DIR))
    return main_out, patch_out


def _flush_chunk(chunks: list[dict[str, int]], blob, offset: int | None, data: bytearray) -> int | None:
    if offset is None or not data:
        return None
    blob_offset = blob.tell()
    blob.write(data)
    chunks.append({"offset": offset, "length": len(data), "blob_offset": blob_offset})
    return None


def build_binary_patch(source: Path, target: Path, patch_json: Path, blob_path: Path) -> dict[str, object]:
    """Create a simple sparse binary patch: write target bytes at changed offsets."""
    source_size = source.stat().st_size
    target_size = target.stat().st_size
    min_size = min(source_size, target_size)
    chunks: list[dict[str, int]] = []
    changed_bytes = 0
    active_offset: int | None = None
    active_data = bytearray()
    max_chunk = 1024 * 1024

    patch_json.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as old, target.open("rb") as new, blob_path.open("wb") as blob:
        pos = 0
        while pos < min_size:
            old_block = old.read(max_chunk)
            new_block = new.read(max_chunk)
            if old_block == new_block:
                active_offset = _flush_chunk(chunks, blob, active_offset, active_data)
                active_data.clear()
                pos += len(old_block)
                continue

            for index, (old_byte, new_byte) in enumerate(zip(old_block, new_block)):
                current = pos + index
                if old_byte != new_byte:
                    if active_offset is None:
                        active_offset = current
                    active_data.append(new_byte)
                    changed_bytes += 1
                elif active_offset is not None:
                    active_offset = _flush_chunk(chunks, blob, active_offset, active_data)
                    active_data.clear()
            pos += len(old_block)

        active_offset = _flush_chunk(chunks, blob, active_offset, active_data)
        active_data.clear()

        if target_size > source_size:
            new.seek(source_size)
            offset = source_size
            blob_offset = blob.tell()
            remaining = target_size - source_size
            while remaining:
                data = new.read(min(max_chunk, remaining))
                if not data:
                    break
                blob.write(data)
                remaining -= len(data)
            length = target_size - source_size
            chunks.append({"offset": offset, "length": length, "blob_offset": blob_offset})
            changed_bytes += length

    patch = {
        "format": PATCH_FORMAT,
        "source_name": source.name,
        "source_size": source_size,
        "source_sha256": sha256_file(source),
        "target_name": target.name,
        "target_size": target_size,
        "target_sha256": sha256_file(target),
        "blob_file": blob_path.name,
        "blob_size": blob_path.stat().st_size,
        "blob_sha256": sha256_file(blob_path),
        "changed_bytes": changed_bytes,
        "chunks": chunks,
    }
    patch_json.write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"  {source.name}: {len(chunks)} chunks, "
        f"{changed_bytes:,} changed bytes, blob {blob_path.stat().st_size:,} bytes"
    )
    return patch


def write_release_notes(notes_path: Path, version: str, zip_name: str) -> None:
    notes = (
        f"Muramasa Rebirth Korean Patch v{version}\n"
        f"\n"
        f"설치 대상: Vita3K\n"
        f"타이틀 ID: {TITLE_ID}\n"
        f"배포 형식: 로컬 패처. 원본 CPK/PKG/DLC 데이터는 포함하지 않음\n"
        f"\n"
        f"주요 변경 사항:\n"
        f"- 상점·식당·소바집 가격 표시에서 숫자 0이 출력되지 않던 문제를 해결했습니다.\n"
        f"  - 247C255A(소바집)·547720A3(식당)·1D6742BB(상점) UI 텍스처의 한글화 영역이\n"
        f"    사전 렌더 디지트 sprite를 침범하지 않도록 영역 좌표를 조정했습니다.\n"
        f"  - 1D6742BB는 그동안 HD 팩 업스케일 다운스케일을 베이스로 사용해 일부\n"
        f"    디지트 sprite가 누락되어 있었습니다. 진짜 원본 export 기준으로 재빌드.\n"
        f"- 시스템 대사 마침표가 가운뎃점(·)처럼 가운데에 떠 있던 문제를 해결했습니다.\n"
        f"  - HD 폰트 텍스처 6706A53E의 cell 192+0x2E ('.') 글리프를 export 원본의\n"
        f"    정상 위치로 복원, 향후 재빌드 시에도 깨지지 않도록 도구도 함께 수정.\n"
        f"- 본편·DLC 대사 중 388개를 자연스러운 줄바꿈으로 개선했습니다.\n"
        f"  - 일본어 원본의 줄 수에 맞춰 3줄→2줄로 압축. 마침표·쉼표·말줄임표·물음표\n"
        f"    위치를 우선 분리점으로 잡는 DP 알고리즘 적용.\n"
        f"  - 줄당 최대 폭 20(전각 기준)으로 화면 폭 안전 마진 유지.\n"
        f"\n"
        f"설치 방법:\n"
        f"1. Vita3K에 원본 US판 본편과 1.06 업데이트를 먼저 설치합니다.\n"
        f"2. 기존 한글 패치 적용본이 있다면, 같은 릴리즈 폴더에서\n"
        f"   `python3 apply_patch.py --restore`를 먼저 실행해 원본 CPK를 복원합니다.\n"
        f"   원본 백업은 `ux0/app/{TITLE_ID}/.muramasa-kor-backup/`에 있습니다.\n"
        f"   예: `NinPri.cpk.v{version}.original`, `NinPriPatch.cpk.v{version}.original`\n"
        f"   패처는 다른 버전명의 `v*.original` 백업도 원본 해시가 맞으면 복원합니다.\n"
        f"3. 백업이 없을 때만 본편/업데이트를 다시 설치한 뒤 진행합니다. 패치된 CPK 위에\n"
        f"   바로 덮어씌우면 원본 해시가 맞지 않아 패처가 중단됩니다.\n"
        f"4. `{zip_name}`을 원하는 위치에 압축 해제합니다.\n"
        f"5. Windows: `apply_windows.bat`을 실행합니다.\n"
        f"6. macOS/Linux: `python3 apply_patch.py`를 실행합니다. macOS에서는\n"
        f"   `apply_macos.command`를 실행해도 됩니다.\n"
        f"7. 패처는 원본 CPK 해시 확인, 원본 백업 생성, CPK 바이너리 패치 적용,\n"
        f"   Vita3K 텍스처 import 설치를 순서대로 수행합니다. content root가 `fs`이면\n"
        f"   `fs/textures/import/{TITLE_ID}/`와 `textures/import/{TITLE_ID}/`를 함께 갱신합니다.\n"
        f"\n"
        f"Android 수동 복사:\n"
        f"1. Windows 또는 macOS의 Vita3K에서 처음 설치한 원본 CPK 기준으로 패처를 먼저 실행합니다.\n"
        f"2. 패치된 `ux0/app/{TITLE_ID}/NinPri.cpk`와 `NinPriPatch.cpk`를 Android Vita3K의\n"
        f"   같은 `ux0/app/{TITLE_ID}/` 폴더에 복사합니다.\n"
        f"3. `textures/import/{TITLE_ID}/` 폴더도 Android Vita3K의 같은\n"
        f"   `textures/import/{TITLE_ID}/` 폴더에 복사합니다.\n"
        f"4. Android Vita3K의 기본 content root는 보통 다음 위치입니다.\n"
        f"   `Android/data/org.vita3k.emulator/files`.\n"
    )
    notes_path.write_text(notes, encoding="utf-8")


def _write_zip_file(archive: zipfile.ZipFile, source: Path, arcname: str, executable: bool = False) -> None:
    if not executable:
        archive.write(source, arcname)
        return
    info = zipfile.ZipInfo.from_file(source, arcname)
    info.external_attr = (stat.S_IFREG | 0o755) << 16
    with source.open("rb") as handle:
        archive.writestr(info, handle.read())


def _write_zip_text(archive: zipfile.ZipFile, arcname: str, text: str, executable: bool = False) -> None:
    info = zipfile.ZipInfo(arcname)
    info.external_attr = (stat.S_IFREG | (0o755 if executable else 0o644)) << 16
    archive.writestr(info, text)


def package_release(version: str, main_cpk: Path, patch_cpk_path: Path) -> tuple[Path, Path, Path]:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    patch_work_dir = DIST_DIR / "_patch_work"
    if patch_work_dir.exists():
        shutil.rmtree(patch_work_dir)
    patch_work_dir.mkdir(parents=True)

    base_name = f"muramasa-kor-v{version}-vita3k-patcher"
    zip_path = DIST_DIR / f"{base_name}.zip"
    manifest_path = DIST_DIR / f"{base_name}-manifest.json"
    checksums_path = DIST_DIR / f"{base_name}-sha256.txt"
    notes_path = DIST_DIR / f"{base_name}-release-notes.txt"

    print("\n== Building binary patch data ==")
    main_patch = build_binary_patch(
        MAIN_CPK,
        main_cpk,
        patch_work_dir / "NinPri.cpk.patch.json",
        patch_work_dir / "NinPri.cpk.patch.bin",
    )
    update_patch = build_binary_patch(
        PATCH_CPK,
        patch_cpk_path,
        patch_work_dir / "NinPriPatch.cpk.patch.json",
        patch_work_dir / "NinPriPatch.cpk.patch.bin",
    )

    texture_files = collect_texture_files()
    texture_size = sum(path.stat().st_size for path in texture_files)
    write_release_notes(notes_path, version, zip_path.name)

    manifest = {
        "name": "muramasa-kor",
        "version": version,
        "title_id": TITLE_ID,
        "release_type": "vita3k-local-patcher",
        "built_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "artifacts": {
            "zip": zip_path.name,
            "notes": notes_path.name,
        },
        "requirements": {
            "python": "3.9+",
            "vita3k_game": "PCSE00240 app v1.00 + patch v1.06",
        },
        "files": [
            {
                "name": "NinPri.cpk",
                "install_path": f"ux0/app/{TITLE_ID}/NinPri.cpk",
                "patch_file": "patches/NinPri.cpk.patch.json",
                "blob_file": "patches/NinPri.cpk.patch.bin",
                "source_sha256": main_patch["source_sha256"],
                "source_size": main_patch["source_size"],
                "target_sha256": main_patch["target_sha256"],
                "target_size": main_patch["target_size"],
                "changed_bytes": main_patch["changed_bytes"],
                "chunk_count": len(main_patch["chunks"]),
            },
            {
                "name": "NinPriPatch.cpk",
                "install_path": f"ux0/app/{TITLE_ID}/NinPriPatch.cpk",
                "patch_file": "patches/NinPriPatch.cpk.patch.json",
                "blob_file": "patches/NinPriPatch.cpk.patch.bin",
                "source_sha256": update_patch["source_sha256"],
                "source_size": update_patch["source_size"],
                "target_sha256": update_patch["target_sha256"],
                "target_size": update_patch["target_size"],
                "changed_bytes": update_patch["changed_bytes"],
                "chunk_count": len(update_patch["chunks"]),
            },
        ],
        "textures": {
            "archive_path": f"textures/import/{TITLE_ID}",
            "count": len(texture_files),
            "size": texture_size,
        },
    }

    windows_bat = (
        "@echo off\r\n"
        "cd /d \"%~dp0\"\r\n"
        "where py >nul 2>nul\r\n"
        "if %errorlevel%==0 (\r\n"
        "  py -3 apply_patch.py %*\r\n"
        "  goto end\r\n"
        ")\r\n"
        "where python >nul 2>nul\r\n"
        "if %errorlevel%==0 (\r\n"
        "  python apply_patch.py %*\r\n"
        "  goto end\r\n"
        ")\r\n"
        "echo Python 3 was not found. Install Python 3.9 or later, then run this again.\r\n"
        ":end\r\n"
        "pause\r\n"
    )
    mac_command = (
        "#!/bin/sh\n"
        "cd \"$(dirname \"$0\")\"\n"
        "if command -v python3 >/dev/null 2>&1; then\n"
        "  python3 apply_patch.py \"$@\"\n"
        "else\n"
        "  echo \"Python 3 was not found. Install Python 3.9 or later, then run this again.\"\n"
        "fi\n"
        "printf 'Press Enter to close...'\n"
        "read _\n"
    )

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        _write_zip_file(archive, PATCHER_TEMPLATE, "apply_patch.py", executable=True)
        _write_zip_text(archive, "apply_windows.bat", windows_bat)
        _write_zip_text(archive, "apply_macos.command", mac_command, executable=True)
        archive.write(notes_path, "README.txt")
        archive.writestr("release/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        archive.writestr("release/version.txt", version + "\n")
        for patch_file in sorted(patch_work_dir.iterdir()):
            archive.write(patch_file, f"patches/{patch_file.name}")
        for texture in texture_files:
            archive.write(texture, f"textures/import/{TITLE_ID}/{texture.name}")

    zip_sha = sha256_file(zip_path)
    manifest["artifacts"]["zip_sha256"] = zip_sha
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checksums_path.write_text(
        "\n".join(
            [
                f"{zip_sha}  {zip_path.name}",
                f"{sha256_file(manifest_path)}  {manifest_path.name}",
                f"{sha256_file(notes_path)}  {notes_path.name}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    shutil.rmtree(patch_work_dir)
    return zip_path, manifest_path, checksums_path


def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a versioned Vita3K local patcher release into dist/.")
    parser.add_argument("--version", help="Override release/version.json for this build only.")
    parser.add_argument("--keep-dist", action="store_true", help="Keep existing dist/ contents.")
    args = parser.parse_args()

    require_inputs()
    version = args.version or load_version()
    if not args.keep_dist:
        clean_dist()

    main_cpk, patch_cpk_path = build_cpks()
    zip_path, manifest_path, checksums_path = package_release(version, main_cpk, patch_cpk_path)

    print("\n== Release artifacts ==")
    print(f"Version: {version}")
    print(f"Zip: {zip_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Checksums: {checksums_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
