#!/usr/bin/env python3
"""대사 줄바꿈 재배치 도구 — 구두점 인지 top-fill.

사용자 요구: "첫 줄이 너무 비고 아래로 몰리는" 균형분배를 버리고, 윗줄부터
채우되(top-fill) 문장 호흡(구두점)을 존중하는 하이브리드 방식으로 재배치한다.

알고리즘 (codex+gemini 협의 수렴):
  - 기본은 top-fill: 다음 단어를 넣어도 max_width 이하이면 현재 줄에 채운다.
  - 강한 구두점(. ! ? … 」 』 ）)으로 끝나고 현재 줄이 충분히 찼으면(>= 임계폭)
    여백이 남아도 그 자리에서 조기 줄바꿈 → '고아 단어'(다음 문장 첫 단어만
    윗줄에 붙는 현상) 방지.
  - 표현/단어는 절대 변형하지 않고 공백 기준 단어 단위로만 이동.

전각=1.0, 반각=0.5, '…'=1.5(빌드 시 '...'로 전개), @#(N)=1.0.

사용법:
  python tools/reflow_dialogs.py                 # 미리보기(통계+샘플)
  python tools/reflow_dialogs.py --apply         # jp_messages.json에 적용
  python tools/reflow_dialogs.py --max-width 29  # 폭 조정
"""

import json
import re
import sys
import argparse
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
JP_MSG = PROJECT / "translations" / "jp_messages.json"

# 강한 구두점: 이 문자로 끝나는 단어 뒤는 (줄이 충분히 찼다면) 조기 줄바꿈 선호.
STRONG_PUNCT = set("。.!?…」』）)！？")
# max_width 대비 이 비율 이상 찼을 때만 강한 구두점 조기 줄바꿈 허용.
FILL_RATIO = 0.78


def line_width(s):
    """전각=1.0, 반각=0.5, '…'=1.5(→'...'), @#(N)=1.0"""
    s_clean = re.sub(r'@#[（(]\d+[)）]', 'X', s)
    w = 0.0
    for c in s_clean:
        if c == '…':       # … → 빌드 시 '...' (반각 3개)
            w += 1.5
        elif ord(c) < 0x80:
            w += 0.5
        else:
            w += 1.0
    return w


def topfill(ko, max_width=29.0):
    """ko를 구두점 인지 top-fill로 재배치한 문자열을 반환."""
    full = " ".join(ko.replace("\r\n", "\n").split("\n")).strip()
    full = re.sub(r' +', ' ', full)
    if not full:
        return ko
    words = full.split(" ")
    threshold = max_width * FILL_RATIO

    lines = []
    cur = ""
    curw = 0.0
    n = len(words)
    for idx, w in enumerate(words):
        ww = line_width(w)
        add = ww + (0.5 if cur else 0.0)
        if cur and curw + add > max_width:
            lines.append(cur)
            cur, curw = w, ww
        else:
            cur = (cur + " " + w) if cur else w
            curw += add
        # 강한 구두점으로 끝나고 줄이 충분히 찼으면 조기 줄바꿈(남은 단어 있을 때).
        if idx < n - 1 and cur and cur[-1] in STRONG_PUNCT and curw >= threshold:
            lines.append(cur)
            cur, curw = "", 0.0
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def count_lines(text):
    return text.replace("\r\n", "\n").count("\n") + 1 if text else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--max-width", type=float, default=29.5)
    ap.add_argument("--sample", type=int, default=12)
    ap.add_argument("--sections", default="scemsg,scemsg_patch")
    args = ap.parse_args()

    data = json.loads(JP_MSG.read_text())
    sections = args.sections.split(",")

    stats = {"total": 0, "changed": 0, "over_width": 0, "over4_lines": 0}
    samples = []
    over_lines = []
    over_width = []

    for section in sections:
        if section not in data:
            continue
        for msg in data[section].get("messages", []):
            ko = msg.get("ko", "")
            if not ko:
                continue
            stats["total"] += 1
            new_ko = topfill(ko, args.max_width)
            new_lines = new_ko.split("\n")
            maxw = max((line_width(l) for l in new_lines), default=0)
            nlines = len(new_lines)
            if maxw > args.max_width + 0.01:
                stats["over_width"] += 1
                over_width.append((section, msg.get("id"), maxw, new_ko))
            if nlines >= 4:
                stats["over4_lines"] += 1
                if nlines > 4:
                    over_lines.append((section, msg.get("id"), nlines, new_ko))
            if new_ko != ko:
                stats["changed"] += 1
                if len(samples) < args.sample:
                    samples.append((section, msg.get("id"), ko, new_ko))
            if args.apply:
                msg["ko"] = new_ko

    print("--- 통계 ---")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\n--- 변환 샘플 ({len(samples)}) ---")
    for s, mid, ko, new_ko in samples:
        print(f"\n[{s}#{mid}]")
        print("  before:")
        for l in ko.split("\n"):
            print(f"    | {l}  (w={line_width(l):.1f})")
        print("  after:")
        for l in new_ko.split("\n"):
            print(f"    | {l}  (w={line_width(l):.1f})")

    if over_width:
        print(f"\n*** max_width({args.max_width}) 초과 {len(over_width)}건 (단어 1개가 너무 김):")
        for s, mid, mw, t in over_width[:10]:
            print(f"  [{s}#{mid}] w={mw:.1f}: {t!r}")
    if over_lines:
        print(f"\n*** 4줄 초과 {len(over_lines)}건:")
        for s, mid, nl, t in over_lines[:10]:
            print(f"  [{s}#{mid}] {nl}줄: {t!r}")

    if args.apply:
        text = json.dumps(data, ensure_ascii=False, indent=2)
        with open(JP_MSG, "rb") as f:
            head = f.read(64)
        if b"\r\n" in head:
            with open(JP_MSG, "wb") as f:
                f.write(text.replace("\n", "\r\n").encode("utf-8"))
        else:
            JP_MSG.write_text(text)
        print(f"\n[APPLIED] {JP_MSG}")
    else:
        print("\n[DRY-RUN] --apply 로 실제 적용")


if __name__ == "__main__":
    main()
