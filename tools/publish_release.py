#!/usr/bin/env python3
"""
Create a GitHub release from the latest dist/ artifacts using gh CLI.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VERSION_FILE = PROJECT_DIR / "release" / "version.json"
DIST_DIR = PROJECT_DIR / "dist"


def load_version() -> str:
    data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    return str(data["version"]).strip()


def run(cmd: list[str]) -> None:
    print(" ".join(cmd))
    subprocess.run(cmd, check=True, cwd=PROJECT_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish dist/ artifacts to a GitHub Release.")
    parser.add_argument("--repo", help="Optional OWNER/REPO override for gh.")
    parser.add_argument("--version", help="Override release/version.json for this publish.")
    parser.add_argument("--title", help="Release title. Defaults to 'Muramasa Korean Patch vX.Y.Z'.")
    parser.add_argument("--notes-file", help="Optional release notes file.")
    parser.add_argument("--draft", action="store_true", help="Create the release as a draft.")
    parser.add_argument("--latest", action="store_true", help="Mark this release as the latest.")
    args = parser.parse_args()

    version = args.version or load_version()
    tag = f"v{version}"
    base_name = f"muramasa-kor-v{version}-vita3k-patcher"
    zip_path = DIST_DIR / f"{base_name}.zip"
    manifest_path = DIST_DIR / f"{base_name}-manifest.json"
    checksums_path = DIST_DIR / f"{base_name}-sha256.txt"
    default_notes = DIST_DIR / f"{base_name}-release-notes.txt"
    notes_file = Path(args.notes_file) if args.notes_file else default_notes

    required = [zip_path, manifest_path, checksums_path, notes_file]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {item}" for item in missing)
        raise FileNotFoundError(
            "Missing release artifacts. Run `python tools/build_release.py` first.\n"
            f"{missing_list}"
        )

    cmd = [
        "gh",
        "release",
        "create",
        tag,
        str(zip_path),
        str(manifest_path),
        str(checksums_path),
        str(notes_file),
        "--title",
        args.title or f"Muramasa Korean Patch v{version}",
        "--notes-file",
        str(notes_file),
        "--verify-tag",
    ]
    if args.repo:
        cmd.extend(["--repo", args.repo])
    if args.draft:
        cmd.append("--draft")
    if args.latest:
        cmd.append("--latest")

    run(cmd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
