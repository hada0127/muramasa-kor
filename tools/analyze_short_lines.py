#!/usr/bin/env python3
"""3줄 메시지 중 각 줄이 짧은(=합치면 더 적은 줄에 들어가는) 케이스 분석.

목표: 1차 condense_dialogs.py 적용 후에도 남아있는 3줄 메시지 중,
각 줄 글자수가 너무 적어서 더 줄일 여지가 있는 케이스를 찾는다.

기본 가설: 1차에서 max_width=22 / DLC relaxed 24를 썼는데, 이 기준에서
3줄로 유지된 케이스는 (적어도 한 줄이 22 초과 + 합산이 44 이상)인 경우
대부분이다. 그런데 다음 조건이면 추가 압축 여지가 있다:
- 합산 폭이 작아 1줄로 가능 (≤ 22)
- 단어 경계 split에서 2줄 후보가 존재 (각 줄 ≤ 22, max_w_relaxed에 따라)
- 각 줄이 어쩌다 짧은(평균 ≤ 10) 케이스
"""

import json
import re
import sys
from pathlib import Path
from statistics import median

PROJECT = Path(__file__).resolve().parent.parent
JP_MSG = PROJECT / "translations" / "jp_messages.json"

PLACEHOLDER_RE = re.compile(r"@#?[c#]?\([\d,]+\)|@/[#c]|%[sd]")


def line_width(s: str) -> float:
    s_clean = PLACEHOLDER_RE.sub("X", s)
    w = 0.0
    for c in s_clean:
        w += 0.5 if ord(c) < 0x80 else 1.0
    return w


def can_fit_2_lines(words, max_w):
    """단어 리스트를 두 줄로 자를 수 있는지 (max_w 내). True/False"""
    space = 0.5
    word_w = [line_width(w) for w in words]
    n = len(words)
    for split in range(1, n):
        w1 = sum(word_w[:split]) + space * (split - 1)
        w2 = sum(word_w[split:]) + space * (n - split - 1)
        if w1 <= max_w and w2 <= max_w:
            return True, (w1, w2)
    return False, None


def main():
    data = json.loads(JP_MSG.read_text(encoding="utf-8"))
    sections = ["scemsg", "scemsg_patch"]

    print("=" * 80)
    print("3줄 메시지 추가 압축 후보 분석")
    print("=" * 80)

    total_3line = 0
    # 1줄 후보 (합산 <= 22 단어 join 시)
    bucket_1line_strict = []   # max_w 22
    bucket_1line_24 = []       # max_w 24 (DLC relaxed)
    bucket_1line_orig = []     # 원본 max를 상한으로

    # 2줄 후보 (단어 경계 split 시 둘 다 <= max_w)
    bucket_2line_strict = []   # max_w 22
    bucket_2line_24 = []       # max_w 24
    bucket_2line_orig = []     # 원본 max를 상한으로

    bucket_widths = []

    for sec in sections:
        sd = data.get(sec, {})
        msgs = sd.get("messages", [])
        for i, m in enumerate(msgs):
            ko = m.get("ko", "")
            if not ko:
                continue
            norm = ko.replace("\r\n", "\n")
            lines = norm.split("\n")
            if len(lines) != 3:
                continue
            stripped = [l.strip() for l in lines]
            if any(not l for l in stripped):
                continue
            widths = [line_width(l) for l in lines]
            total_3line += 1
            orig_max = max(widths)
            mn, md, mx = min(widths), median(widths), max(widths)
            avg = sum(widths) / 3

            flat = " ".join(stripped)
            flat = re.sub(r" +", " ", flat)
            words = flat.split(" ")
            joined_w = line_width(flat)

            entry = {
                "section": sec,
                "id": m.get("id"),
                "ja": m.get("ja", ""),
                "ko": ko,
                "lines": lines,
                "widths": widths,
                "min": mn,
                "max": mx,
                "avg": avg,
                "joined_w": joined_w,
                "orig_max": orig_max,
            }
            bucket_widths.append((mn, md, mx, avg, joined_w))

            # 1줄 후보
            if joined_w <= 22.0:
                bucket_1line_strict.append(entry)
            if joined_w <= 24.0:
                bucket_1line_24.append(entry)
            if joined_w <= max(orig_max, 22.0):
                bucket_1line_orig.append(entry)

            # 2줄 후보 (단어 경계 split 가능?)
            ok, _ = can_fit_2_lines(words, 22.0)
            if ok:
                bucket_2line_strict.append(entry)
            ok24, _ = can_fit_2_lines(words, 24.0)
            if ok24:
                bucket_2line_24.append(entry)
            okorig, _ = can_fit_2_lines(words, max(orig_max, 22.0))
            if okorig:
                bucket_2line_orig.append(entry)

    print(f"\n총 3줄 메시지: {total_3line}개 (scemsg + scemsg_patch)")
    print()

    if bucket_widths:
        avgs = [w[3] for w in bucket_widths]
        maxs = [w[2] for w in bucket_widths]
        joins = [w[4] for w in bucket_widths]
        mins_ = [w[0] for w in bucket_widths]
        print("폭 분포:")
        print(f"  최소 폭(line min):  min={min(mins_):.1f}, median={median(mins_):.1f}, max={max(mins_):.1f}")
        print(f"  평균 폭(line avg):  min={min(avgs):.1f}, median={median(avgs):.1f}, max={max(avgs):.1f}")
        print(f"  최대 폭(line max):  min={min(maxs):.1f}, median={median(maxs):.1f}, max={max(maxs):.1f}")
        print(f"  합산 폭(joined):    min={min(joins):.1f}, median={median(joins):.1f}, max={max(joins):.1f}")

    print()
    print("[1줄로 합칠 후보]")
    print(f"  max_w=22 strict:     {len(bucket_1line_strict)}개")
    print(f"  max_w=24 relaxed:    {len(bucket_1line_24)}개")
    print(f"  원본 max 상한:        {len(bucket_1line_orig)}개")
    print()
    print("[2줄로 합칠 후보 (단어 경계 split 가능)]")
    print(f"  max_w=22 strict:     {len(bucket_2line_strict)}개")
    print(f"  max_w=24 relaxed:    {len(bucket_2line_24)}개")
    print(f"  원본 max 상한:        {len(bucket_2line_orig)}개")

    # 핵심: 원본 max 상한으로 했을 때 2줄 가능한 케이스가 가장 많을 것 — 왜 1차에서 안 잡혔는지 확인
    not_yet_2line = []
    for e in bucket_2line_orig:
        # 1차 reformat이 어떤 이유로 SKIP했는지 봐야 함
        not_yet_2line.append(e)

    print()
    print("=" * 80)
    print(f"원본 max 상한으로 2줄 가능 케이스: {len(bucket_2line_orig)}개 — 왜 1차에 안 잡혔나?")
    print("=" * 80)

    # 1차 reformat 로직 시뮬레이션
    # condense_dialogs.py의 reformat는 max_w=22 기본 + max_w_relaxed=24 (orig_max > 22 시)
    # 즉 max effective = max(orig_max, 24) 까지는 안 되고 min(24, max(orig_max, 24)) = 24가 상한.
    # 그래서 원본 max가 24 초과인 경우 → effective_max_w = 24 → 그 폭으로 합쳐서 OK인 케이스 없으면 SKIP.
    over_24 = sum(1 for e in bucket_widths if e[2] > 24.0)
    print(f"원본 max > 24 인 메시지 수: {over_24}개 (1차 effective_max_w=24 상한 케이스)")
    print()

    # 샘플: 합산 ≤ 44 + 원본 max > 24 인 케이스 → 더 공격적으로 한 줄 폭을 24~28 정도로 늘리면 2줄에 들어갈 수도
    targets = []
    for e in bucket_2line_orig:
        if e["orig_max"] > 24.0:
            targets.append(e)
    print(f"orig_max > 24 + 2줄 가능 (orig_max 상한): {len(targets)}개")

    def show_samples(bucket, name, k=20):
        print()
        print("-" * 80)
        print(f"{name} 샘플 (최대 {k}개)")
        print("-" * 80)
        for e in bucket[:k]:
            print(f"\n[{e['section']}#{e['id']}]  widths={[round(w,1) for w in e['widths']]}, joined={e['joined_w']:.1f}, orig_max={e['orig_max']:.1f}")
            if e["ja"]:
                ja_norm = e["ja"].replace("\r\n", "\n")
                print(f"  ja: {ja_norm[:60].replace(chr(10), ' | ')}")
            for l, w in zip(e["lines"], e["widths"]):
                print(f"    | {l}  (w={w:.1f})")

    show_samples(bucket_1line_orig, "1줄 후보 (orig_max 상한)", 15)
    show_samples(targets, "2줄 가능 + orig_max > 24 (relaxed 한도 초과 케이스)", 25)


if __name__ == "__main__":
    main()
