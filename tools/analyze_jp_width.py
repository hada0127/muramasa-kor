#!/usr/bin/env python3
"""JP 원문 라인 폭 분포 — 게임 대사 박스의 한 줄 최대 폭 추정."""

import json
import re
from pathlib import Path
from statistics import median, quantiles

PROJECT = Path(__file__).resolve().parent.parent
JP_MSG = PROJECT / "translations" / "jp_messages.json"

PLACEHOLDER_RE = re.compile(r"@#?[c#]?\([\d,]+\)|@/[#c]|%[sd]")


def line_width(s: str) -> float:
    s_clean = PLACEHOLDER_RE.sub("X", s)
    w = 0.0
    for c in s_clean:
        w += 0.5 if ord(c) < 0x80 else 1.0
    return w


def main():
    data = json.loads(JP_MSG.read_text(encoding="utf-8"))
    sections = ["scemsg", "scemsg_patch"]

    jp_widths = []
    jp_line_counts = []
    ko_widths = []
    ko_line_counts = []

    for sec in sections:
        sd = data.get(sec, {})
        for m in sd.get("messages", []):
            ja = m.get("ja", "")
            ko = m.get("ko", "")
            if ja:
                lines = [l for l in ja.replace("\r\n", "\n").split("\n") if l.strip()]
                if lines:
                    jp_line_counts.append(len(lines))
                    for l in lines:
                        jp_widths.append(line_width(l))
            if ko:
                lines = [l for l in ko.replace("\r\n", "\n").split("\n") if l.strip()]
                if lines:
                    ko_line_counts.append(len(lines))
                    for l in lines:
                        ko_widths.append(line_width(l))

    def stat(name, vals):
        if not vals:
            return
        q = quantiles(vals, n=20)
        print(f"\n{name}: n={len(vals)}")
        print(f"  min={min(vals):.1f}, p50={median(vals):.1f}, p90={q[17]:.1f}, p95={q[18]:.1f}, p99={q[-1]:.1f}, max={max(vals):.1f}")

    stat("JP line widths (전각 단위, ASCII 0.5)", jp_widths)
    stat("KO line widths (현재)", ko_widths)

    print()
    print("JP line count 분포:")
    from collections import Counter
    print(f"  {sorted(Counter(jp_line_counts).items())}")
    print("KO line count 분포:")
    print(f"  {sorted(Counter(ko_line_counts).items())}")

    # JP 라인 폭 23 이상 (=한 줄 한도의 단서)
    over_22 = sum(1 for w in jp_widths if w > 22.0)
    over_23 = sum(1 for w in jp_widths if w > 23.0)
    over_24 = sum(1 for w in jp_widths if w > 24.0)
    over_25 = sum(1 for w in jp_widths if w > 25.0)
    print(f"\nJP 라인 폭 분포 (게임 한 줄 박스 폭의 단서):")
    print(f"  > 22 전각: {over_22}개")
    print(f"  > 23 전각: {over_23}개")
    print(f"  > 24 전각: {over_24}개")
    print(f"  > 25 전각: {over_25}개")


if __name__ == "__main__":
    main()
