#!/usr/bin/env python3
"""
Build a versioned Vita3K patch release into dist/.

This wraps the existing patch pipeline:
1. build_patch.py
2. cpk_patch.py for NinPri.cpk
3. cpk_patch.py for NinPriPatch.cpk
4. Package the patched CPKs into a Vita3K overwrite zip
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
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
MAIN_CPK = PROJECT_DIR / "backup" / "NinPri.cpk"
PATCH_CPK = PROJECT_DIR / "backup" / "NinPriPatch.cpk"


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
        rel = file_path.relative_to(mod_dir).as_posix()
        replacements[rel] = file_path.read_bytes()
    return replacements


def require_inputs() -> None:
    required = [
        VERSION_FILE,
        MAIN_CPK,
        PATCH_CPK,
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


def write_release_notes(notes_path: Path, version: str, zip_name: str) -> None:
    notes = (
        f"Muramasa Rebirth Korean patch {version}\n"
        f"\n"
        f"Install target: Vita3K\n"
        f"Title ID: {TITLE_ID}\n"
        f"\n"
        f"Usage:\n"
        f"1. Back up your Vita3K files.\n"
        f"2. Extract `{zip_name}` into your Vita3K pref path.\n"
        f"3. Allow overwrite for `ux0/app/{TITLE_ID}/NinPri.cpk` and `NinPriPatch.cpk`.\n"
    )
    notes_path.write_text(notes, encoding="utf-8")


def package_release(version: str, main_cpk: Path, patch_cpk_path: Path) -> tuple[Path, Path, Path]:
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    base_name = f"muramasa-kor-v{version}-vita3k"
    zip_path = DIST_DIR / f"{base_name}.zip"
    manifest_path = DIST_DIR / f"{base_name}-manifest.json"
    checksums_path = DIST_DIR / f"{base_name}-sha256.txt"
    notes_path = DIST_DIR / f"{base_name}-release-notes.txt"

    write_release_notes(notes_path, version, zip_path.name)

    manifest = {
        "name": "muramasa-kor",
        "version": version,
        "title_id": TITLE_ID,
        "built_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "artifacts": {
            "zip": zip_path.name,
            "notes": notes_path.name,
        },
        "files": [
            {
                "source": str(main_cpk.relative_to(PROJECT_DIR)).replace("\\", "/"),
                "archive_path": f"ux0/app/{TITLE_ID}/NinPri.cpk",
                "sha256": sha256_file(main_cpk),
                "size": main_cpk.stat().st_size,
            },
            {
                "source": str(patch_cpk_path.relative_to(PROJECT_DIR)).replace("\\", "/"),
                "archive_path": f"ux0/app/{TITLE_ID}/NinPriPatch.cpk",
                "sha256": sha256_file(patch_cpk_path),
                "size": patch_cpk_path.stat().st_size,
            },
        ],
    }

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(main_cpk, f"ux0/app/{TITLE_ID}/NinPri.cpk")
        archive.write(patch_cpk_path, f"ux0/app/{TITLE_ID}/NinPriPatch.cpk")
        archive.writestr("release/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        archive.writestr("release/version.txt", version + "\n")
        archive.write(notes_path, "release/README.txt")

    zip_sha = sha256_file(zip_path)
    manifest["artifacts"]["zip_sha256"] = zip_sha
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checksums_path.write_text(
        "\n".join(
            [
                f"{zip_sha}  {zip_path.name}",
                f"{manifest['files'][0]['sha256']}  NinPri.cpk",
                f"{manifest['files'][1]['sha256']}  NinPriPatch.cpk",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return zip_path, manifest_path, checksums_path


def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a versioned Vita3K release zip into dist/.")
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
