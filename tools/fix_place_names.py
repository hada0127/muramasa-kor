"""Place-name-fix Phase 3.6 revision: use half-width Arabic digits.

Previous v1 replaced 전각 숫자 (２-７) with 한글 음독 (이-칠) for OOR avoidance,
but user preferred '제2막' natural style. Half-width ASCII digits (2-7) route
through build_patch.py ASCII_SJIS_MAP → cell 960+ which font_import overlays,
so numerals render correctly while keeping natural Korean typography.

This script is idempotent: runs on either '제이막' or '제２막' inputs and
produces '제2막'.
"""
from __future__ import annotations

import json
from pathlib import Path


REPLACEMENTS = {
    # Previous 한글 음독 version → ASCII half-width
    "제이막": "제2막",
    "제삼막": "제3막",
    "제사막": "제4막",
    "제오막": "제5막",
    "제육막": "제6막",
    "제칠막": "제7막",
    # Also normalize leftover full-width forms (idempotent safety)
    "제２막": "제2막",
    "제３막": "제3막",
    "제４막": "제4막",
    "제５막": "제5막",
    "제６막": "제6막",
    "제７막": "제7막",
}


def main() -> None:
    path = Path("translations/jp_messages.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    total_replacements = 0
    affected_sections: dict[str, int] = {}

    def walk(obj, section_name=""):
        nonlocal total_replacements
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    new_v = v
                    for old, new in REPLACEMENTS.items():
                        count = new_v.count(old)
                        if count > 0:
                            new_v = new_v.replace(old, new)
                            total_replacements += count
                            affected_sections[section_name] = affected_sections.get(section_name, 0) + count
                    if new_v != v:
                        obj[k] = new_v
                else:
                    walk(v, section_name or k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if isinstance(v, str):
                    new_v = v
                    for old, new in REPLACEMENTS.items():
                        count = new_v.count(old)
                        if count > 0:
                            new_v = new_v.replace(old, new)
                            total_replacements += count
                            affected_sections[section_name] = affected_sections.get(section_name, 0) + count
                    if new_v != v:
                        obj[i] = new_v
                else:
                    walk(v, section_name)

    walk(data)

    print(f"Total replacements: {total_replacements}")
    print(f"Sections affected:")
    for s, c in affected_sections.items():
        print(f"  {s}: {c}")

    if total_replacements > 0:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nSaved: {path}")
    else:
        print("No changes made.")


if __name__ == "__main__":
    main()
