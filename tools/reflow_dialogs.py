#!/usr/bin/env python3
"""대사 줄바꿈 재배치 도구.

ja(일본어 원본)의 줄 수를 목표로 ko(한국어) 줄 수를 압축.
마침표·쉼표 우선 분리 + 균형 분배 (DP 기반).

전각=1.0, 반각=0.5, @#(N) placeholder=1.0 으로 폭 계산.

사용법:
  python tools/reflow_dialogs.py                    # 미리보기 (jp_messages.json은 그대로)
  python tools/reflow_dialogs.py --apply             # 실제 적용
  python tools/reflow_dialogs.py --max-width 22      # max width 조정
  python tools/reflow_dialogs.py --sample 20         # 샘플 N개 출력
"""

import json
import re
import sys
import argparse
from pathlib import Path
from functools import lru_cache

PROJECT = Path(__file__).resolve().parent.parent
JP_MSG = PROJECT / "translations" / "jp_messages.json"

PUNCT_STRONG = set("。.!?…」』）)")
PUNCT_WEAK = set(",、—–-")


def line_width(s):
    """전각=1.0, 반각=0.5, @#(N) = 1.0"""
    s_clean = re.sub(r'@#[（(]\d+[)）]', 'X', s)
    w = 0.0
    for c in s_clean:
        if ord(c) < 0x80:
            w += 0.5
        else:
            w += 1.0
    return w


def reflow(ko, target_n, max_width):
    """ko 텍스트를 target_n 줄 이하로 reflow. 안 되면 None.

    DP로 마침표 우선 + 균형 분배."""
    full = " ".join(ko.replace("\r\n", "\n").split("\n")).strip()
    full = re.sub(r' +', ' ', full)
    if not full:
        return ko

    words = full.split(" ")
    n = len(words)
    if n == 0:
        return ""

    space_w = 0.5
    cum = [0.0]
    for w in words:
        cum.append(cum[-1] + line_width(w) + space_w)

    def slice_width(i, j):
        return cum[j] - cum[i] - space_w

    def break_penalty(j):
        """words[:j]와 words[j:] 사이의 분리 페널티 (작을수록 좋음)."""
        if j <= 0 or j >= n:
            return 0
        last = words[j - 1]
        if not last:
            return 5
        c = last[-1]
        if c in PUNCT_STRONG:
            return 0
        if c in PUNCT_WEAK:
            return 2
        return 5

    INF = float('inf')

    @lru_cache(maxsize=None)
    def solve(start, lines_left):
        if lines_left == 1:
            sw = slice_width(start, n)
            if sw > max_width:
                return None
            return (sw, 0, (n,))
        best = None
        for j in range(start + 1, n):
            sw = slice_width(start, j)
            if sw > max_width:
                break
            sub = solve(j, lines_left - 1)
            if sub is None:
                continue
            sub_max, sub_pen, sub_breaks = sub
            max_w = max(sw, sub_max)
            pen = sub_pen + break_penalty(j)
            cost = (pen, max_w)
            if best is None or cost < (best[1], best[0]):
                best = (max_w, pen, (j,) + sub_breaks)
        return best

    r = solve(0, target_n)
    if r is None:
        return None
    breaks = r[2]
    lines = []
    prev = 0
    for b in breaks:
        lines.append(" ".join(words[prev:b]))
        prev = b
    return "\n".join(lines)


def count_lines(text):
    return text.replace("\r\n", "\n").count("\n") + 1 if text else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="jp_messages.json에 실제 적용")
    ap.add_argument("--max-width", type=float, default=20.0, help="줄당 최대 폭 (전각 단위)")
    ap.add_argument("--sample", type=int, default=10, help="미리보기 샘플 개수")
    ap.add_argument("--sections", default="scemsg,scemsg_patch",
                    help="처리할 섹션 (쉼표 구분)")
    args = ap.parse_args()

    data = json.loads(JP_MSG.read_text())
    sections = args.sections.split(",")

    stats = {
        "total": 0, "skip_empty": 0,
        "unchanged_already_le_target": 0,
        "compressed": 0, "compress_fail": 0,
    }
    samples = []
    failures = []

    for section in sections:
        if section not in data:
            continue
        for msg in data[section].get("messages", []):
            ko = msg.get("ko", "")
            ja = msg.get("ja", "")
            if not ko:
                stats["skip_empty"] += 1
                continue
            stats["total"] += 1

            ko_n = count_lines(ko)
            ja_n = max(1, count_lines(ja))

            if ko_n <= ja_n:
                stats["unchanged_already_le_target"] += 1
                continue

            new_ko = reflow(ko, ja_n, args.max_width)
            if new_ko is None:
                # 그래도 줄임이 가능한지 시도: target_n + 1 (즉 ko_n - 1)
                for tn in range(ja_n + 1, ko_n):
                    new_ko = reflow(ko, tn, args.max_width)
                    if new_ko is not None:
                        break

            if new_ko is None:
                stats["compress_fail"] += 1
                failures.append((section, msg.get("id"), ja, ko))
                continue

            new_n = count_lines(new_ko)
            if new_n >= ko_n:
                stats["compress_fail"] += 1
                continue

            stats["compressed"] += 1
            if args.apply:
                msg["ko"] = new_ko
            if len(samples) < args.sample:
                samples.append((section, msg.get("id"), ja, ko, new_ko))

    print(f"--- 통계 ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\n--- 변환 샘플 ({len(samples)}) ---")
    for s, mid, ja, ko, new_ko in samples:
        print(f"\n[{s}#{mid}]")
        print(f"  ja ({count_lines(ja)}줄):")
        for l in ja.replace("\r\n", "\n").split("\n"):
            print(f"    | {l}")
        print(f"  ko old ({count_lines(ko)}줄):")
        for l in ko.split("\n"):
            print(f"    | {l}  (w={line_width(l):.1f})")
        print(f"  ko new ({count_lines(new_ko)}줄):")
        for l in new_ko.split("\n"):
            print(f"    | {l}  (w={line_width(l):.1f})")

    if args.apply:
        # 원본 line ending 보존 (CRLF)
        text = json.dumps(data, ensure_ascii=False, indent=2)
        # 원본 형식 감지
        with open(JP_MSG, "rb") as f:
            head = f.read(64)
        if b"\r\n" in head:
            text = text.replace("\n", "\r\n")
            with open(JP_MSG, "wb") as f:
                f.write(text.encode("utf-8"))
        else:
            JP_MSG.write_text(text)
        print(f"\n[APPLIED] {JP_MSG}")
    else:
        print(f"\n[DRY-RUN] --apply 로 실제 적용")


if __name__ == "__main__":
    main()
