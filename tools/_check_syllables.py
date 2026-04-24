"""Verify needed syllables are in kr_sjis_mapping.json."""
import json
from pathlib import Path

km = json.loads(Path("translations/kr_sjis_mapping.json").read_text(encoding="utf-8"))
k2s = km.get("korean_to_sjis", {})

needed = list("제이삼사오육칠막")
print(f"Checking {len(needed)} needed syllables against {len(k2s)} mapped chars:\n")
for ch in needed:
    if ch in k2s:
        code = k2s[ch]
        if isinstance(code, list):
            hex_str = "".join(f"{b:02X}" for b in code)
        else:
            hex_str = f"{code:04X}" if isinstance(code, int) else str(code)
        print(f"  '{ch}' = {hex_str} OK")
    else:
        print(f"  '{ch}' = MISSING")
