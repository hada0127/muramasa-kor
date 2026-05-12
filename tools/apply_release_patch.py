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


def default_pref_candidates(title_id: str) -> list[Path]:
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
    unique = []
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def content_root_candidates(paths: list[Path]) -> list[Path]:
    candidates: list[Path] = []
    for path in paths:
        expanded = path.expanduser()
        candidates.append(expanded)
        if expanded.name != "fs":
            candidates.append(expanded / "fs")

    seen: set[Path] = set()
    unique = []
    for candidate in candidates:
        if candidate not in seen:
            unique.append(candidate)
            seen.add(candidate)
    return unique


def resolve_content_root(arg_path: str | None, title_id: str) -> Path:
    raw_candidates = [Path(arg_path).expanduser()] if arg_path else default_pref_candidates(title_id)
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


def texture_import_roots(content_root: Path) -> list[Path]:
    roots = [content_root]
    if content_root.name == "fs":
        roots.append(content_root.parent)

    seen: set[Path] = set()
    unique = []
    for root in roots:
        if root not in seen:
            unique.append(root)
            seen.add(root)
    return unique


def install_textures(root: Path, content_root: Path, title_id: str, dry_run: bool) -> str:
    source_dir = root / "textures" / "import" / title_id
    if not source_dir.exists():
        return "SKIP  texture import files not included"

    files = sorted(source_dir.glob("*.png"))
    if dry_run:
        dests = ", ".join(str(base / "textures" / "import" / title_id) for base in texture_import_roots(content_root))
        return f"WOULD copy {len(files)} texture imports -> {dests}"

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
    return "COPY  texture imports: " + "; ".join(parts)


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
        print(install_textures(root, content_root, title_id, args.dry_run))

    print("Done. Enable Vita3K GPU texture import if UI/font textures do not appear.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
