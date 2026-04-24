"""Inspect current state of place-name-related entries for Phase 3.6."""
import json
import sys
from pathlib import Path

out = Path("temp/place_name_inspect.txt")
out.parent.mkdir(parents=True, exist_ok=True)

with open("translations/jp_messages.json", "r", encoding="utf-8") as f:
    data = json.load(f)

lines = []
lines.append("=== sysmsg entries #60-75 ===")
for section_name in ["sysmsg", "sysmsg_main"]:
    if section_name not in data: continue
    lines.append(f"\n--- section: {section_name} ---")
    section = data[section_name]
    msgs = section.get("messages") if isinstance(section, dict) else section
    if not msgs: continue
    lines.append(f"total: {len(msgs)}")
    for i in range(60, 76):
        if i >= len(msgs): break
        m = msgs[i]
        if isinstance(m, dict):
            jp = m.get('jp', '')
            ko = m.get('ko', '')
        else:
            jp, ko = '', str(m)
        lines.append(f"  #{i}: jp={jp!r:<40} ko={ko!r}")

lines.append("\n=== '무사시' / '사무라이시' counts ===")
total_musashi = 0
total_samurai = 0
def walk(obj):
    global total_musashi, total_samurai
    if isinstance(obj, str):
        total_musashi += obj.count("무사시")
        total_samurai += obj.count("사무라이시")
    elif isinstance(obj, dict):
        for v in obj.values(): walk(v)
    elif isinstance(obj, list):
        for v in obj: walk(v)
walk(data)
lines.append(f"무사시 (correct):   {total_musashi}")
lines.append(f"사무라이시 (wrong): {total_samurai}")

lines.append("\n=== Search for '막' entries in sysmsg ===")
for section_name in ["sysmsg", "sysmsg_main"]:
    if section_name not in data: continue
    section = data[section_name]
    msgs = section.get("messages") if isinstance(section, dict) else section
    if not msgs: continue
    lines.append(f"\n--- {section_name} ---")
    for i, m in enumerate(msgs):
        if isinstance(m, dict):
            ko = m.get('ko', '')
            jp = m.get('jp', '')
        else:
            ko = str(m); jp = ''
        if '막' in ko or '幕' in jp:
            lines.append(f"  #{i}: jp={jp!r:<30} ko={ko!r}")

out.write_text("\n".join(lines), encoding="utf-8")
print(f"Written {len(lines)} lines to {out}")
