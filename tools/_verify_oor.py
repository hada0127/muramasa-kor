"""Verify specific Act-label and story-summary entries for OOR bytes after patch."""
import sys
from pathlib import Path
sys.path.insert(0, "tools")
from nms_parser import parse_nms

out = Path("temp/verify_oor.txt")
out.parent.mkdir(parents=True, exist_ok=True)

def scan_oor(msg_bytes: bytes):
    oor = []
    j = 0
    while j < len(msg_bytes):
        c = msg_bytes[j]
        if (c >= 0x81 and c <= 0x9F) or c >= 0xE0:
            if j + 1 < len(msg_bytes):
                code = (c << 8) | msg_bytes[j + 1]
                in_kr = 0x89CD <= code <= 0x8EE0
                in_jp_punct = 0x8140 <= code <= 0x829F
                if not (in_kr or in_jp_punct):
                    oor.append(f"{code:04X}")
                j += 2; continue
        j += 1
    return oor

lines = []
for nms_path in [
    "patch_main/_US/msgsheet/sysmsg.nms",
    "patch_main/msgsheet/sysmsg.nms",
    "patch_patch/_US/msgsheet/sysmsg.nms",
    "patch_patch/msgsheet/sysmsg.nms",
]:
    p = Path(nms_path)
    if not p.exists(): continue
    nms = parse_nms(nms_path)
    msgs = nms.get("messages") if isinstance(nms, dict) else nms
    lines.append(f"\n=== {nms_path} ({len(msgs)} msgs) ===")
    targets = [65, 66, 67, 68, 69, 70, 499, 500, 501, 502, 503, 504, 505, 509, 510, 511, 512, 513, 514, 515,
               # patch_main variants (file has 574 msgs instead of 965, so Act story lines shift)
               347, 348, 349, 350, 351, 352, 353, 357, 358, 359, 360, 361, 362, 363]
    for i in targets:
        if i >= len(msgs): continue
        m = msgs[i]
        if isinstance(m, str):
            m_bytes = m.encode("shift_jis", "replace")
        elif isinstance(m, bytes):
            m_bytes = m
        else:
            continue
        oor = scan_oor(m_bytes)
        try:
            text_preview = m_bytes[:30].decode("shift_jis", "replace")
        except Exception:
            text_preview = repr(m_bytes[:30])
        oor_label = f"OOR={oor}" if oor else "OK"
        lines.append(f"  #{i}: [{oor_label}] {text_preview!r}")

out.write_text("\n".join(lines), encoding="utf-8")
print(f"Written to {out}")
