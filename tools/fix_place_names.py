"""Place-name-fix Phase 3.6 M1: replace 전각 숫자 in '제N막' with 한글 음독.

Target: translations/jp_messages.json
Changes:
  제２막 → 제이막
  제３막 → 제삼막
  제４막 → 제사막
  제５막 → 제오막
  제６막 → 제육막
  제７막 → 제칠막

Validate: every syllable in the replacement set must be in kr_sjis_mapping.
"""
from __future__ import annotations

import json
from pathlib import Path


REPLACEMENTS = {
    "제２막": "제이막",
    "제３막": "제삼막",
    "제４막": "제사막",
    "제５막": "제오막",
    "제６막": "제육막",
    "제７막": "제칠막",
}


def main() -> None:
    # Validate syllables against kr mapping
    kr_map = json.loads(Path("translations/kr_sjis_mapping.json").read_text(encoding="utf-8"))
    # kr_map structure: {"char": 0xNNNN} or similar
    all_mapped_chars = set()
    if isinstance(kr_map, dict):
        for k in kr_map.keys():
            if isinstance(k, str) and len(k) == 1:
                all_mapped_chars.add(k)
        # If nested: check "mapping" key
        if "mapping" in kr_map and isinstance(kr_map["mapping"], dict):
            for k in kr_map["mapping"].keys():
                if isinstance(k, str) and len(k) == 1:
                    all_mapped_chars.add(k)

    needed = set("제이삼사오육칠막")
    missing = needed - all_mapped_chars
    if missing:
        print(f"WARNING: chars missing from kr mapping: {missing}")
    else:
        print(f"all {len(needed)} needed syllables present in kr mapping ✓")

    # Load translations
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

    print(f"\nTotal replacements: {total_replacements}")
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
