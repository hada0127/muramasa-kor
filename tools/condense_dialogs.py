#!/usr/bin/env python3
"""대사 메시지를 띄어쓰기 기반으로 압축/재정리.

규칙 (codex + gemini 협의 결과, max_width=22 전각):
1. 2줄 → 1줄: 합친 폭 <= 22 이면 합친다.
2. 3줄 → 2줄: 단어 경계 모든 split 후보 중
   - (a) 두 줄 모두 <= 22
   - (b) 길이 차 최소
   - (c) tie-break: 앞 줄 끝이 문장부호일 때 선호
3. 2줄 균형 재분배: abs(w1-w2) > 6 또는 line1이 매우 짧으면 재분배
4. 보존 조건 (수정 안 함):
   - `@#(N)` placeholder, `%s`/`%d`/`@c(N)` 류 포함 줄
   - 5글자 미만 짧은 강조 단독 라인 (의도적 짧음)
   - 화자명 콜론 패턴 (`^[가-힣]{1,4}:\\s*$` 첫 줄)
   - 단어 중간 자르기 절대 금지 (split은 단어 경계만)
5. 적용 섹션: scemsg, sysmsg, sysmsg_main, _itemdata, _itemdata_main
   - 단, scemsg가 본편+DLC 대사 — 메인 타겟
   - sysmsg 등은 좌측 짧음 케이스만 (상자 작을 수 있어 보수적)

2차 협의 (gemini, codex 부분 의견):
- 무라마사 대사 박스는 전각 24까지 안전 (JP 원문도 p95≈28자)
- 3줄→2줄 압축은 페이싱 손상 거의 없음 (3줄 동시 표시 박스)
- "의도적 페이싱" 보존: 모든 줄 < 8자 (짧은 외침 연속, 예: "죽어라!/사라져라!/으아악!")
- `--aggressive-short-lines`: 3줄 메시지에 한해 max_w 상한을 aggressive_max_w(기본 24)로
  공격적 압축. 단어 중간 자르기는 여전히 절대 금지.

사용법:
  python tools/condense_dialogs.py                          # 미리보기
  python tools/condense_dialogs.py --apply                  # 적용
  python tools/condense_dialogs.py --sections scemsg        # 특정 섹션만
  python tools/condense_dialogs.py --max-width 22           # 폭 조정
  python tools/condense_dialogs.py --aggressive-short-lines # 3줄 짧은 라인 공격적 압축
  python tools/condense_dialogs.py --greedy-fill --greedy-max-width 40 --apply
                                                            # Greedy 위쪽부터 채우기
                                                            # overflow 리포트는 temp/condense_overflow.txt
  python tools/condense_dialogs.py --sample 30              # 샘플 출력 개수
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
JP_MSG = PROJECT / "translations" / "jp_messages.json"

PUNCT_STRONG = set("。.!?…」』）)〕】")
PUNCT_WEAK = set(",、—–-")
PUNCT_ANY = PUNCT_STRONG | PUNCT_WEAK | set("·・")

# Placeholder 패턴 — 이 줄에 포함되면 자동 수정 보류 (수동 처리 영역)
PLACEHOLDER_RE = re.compile(r"@#?[c#]?\([\d,]+\)|@/[#c]|%[sd]")


def line_width(s: str) -> float:
    """전각=1.0, 반각=0.5. placeholder는 1자(전각 1.0) 폭으로 계산."""
    s_clean = PLACEHOLDER_RE.sub("X", s)
    w = 0.0
    for c in s_clean:
        w += 0.5 if ord(c) < 0x80 else 1.0
    return w


def count_lines(s: str) -> int:
    if not s:
        return 0
    return s.replace("\r\n", "\n").count("\n") + 1


def split_words(line: str) -> list:
    """공백 단위 분할 (placeholder는 하나의 단어로 유지)."""
    return [w for w in re.split(r" +", line) if w]


def break_penalty(prev_word: str) -> int:
    """줄 끝(앞 줄의 마지막 단어) 페널티 — 작을수록 분할 위치 선호."""
    if not prev_word:
        return 5
    c = prev_word[-1]
    if c in PUNCT_STRONG:
        return 0
    if c in PUNCT_WEAK:
        return 1
    if c in "·・":
        return 2
    return 5


def try_combine_to_n(words: list, target_n: int, max_w: float):
    """단어 리스트를 target_n 줄로 합치되 각 줄 폭 <= max_w 만족하는 후보 중
    (1) 최대 폭 최소 (2) 길이 차 최소 (3) 분할 페널티 최소 후보를 반환.

    반환: (lines, max_w_used, abs_diff, penalty) 또는 None
    """
    n = len(words)
    if n == 0:
        return None
    space = 0.5  # 공백 폭 (반각)
    word_w = [line_width(w) for w in words]

    def line_w(i, j):
        if i >= j:
            return 0.0
        w = sum(word_w[i:j]) + space * (j - i - 1)
        return w

    if target_n == 1:
        w = line_w(0, n)
        if w <= max_w:
            return ([" ".join(words)], w, 0.0, 0)
        return None

    if target_n == 2:
        best = None
        for split in range(1, n):
            w1 = line_w(0, split)
            w2 = line_w(split, n)
            if w1 > max_w or w2 > max_w:
                continue
            mw = max(w1, w2)
            diff = abs(w1 - w2)
            pen = break_penalty(words[split - 1])
            cand = (mw, diff, pen, split, (w1, w2))
            if best is None or cand < best:
                best = cand
        if best is None:
            return None
        _, diff, pen, split, (w1, w2) = best
        lines = [" ".join(words[:split]), " ".join(words[split:])]
        return (lines, max(w1, w2), diff, pen)

    if target_n == 3:
        best = None
        for s1 in range(1, n - 1):
            w1 = line_w(0, s1)
            if w1 > max_w:
                break
            for s2 in range(s1 + 1, n):
                w2 = line_w(s1, s2)
                w3 = line_w(s2, n)
                if w2 > max_w or w3 > max_w:
                    continue
                mw = max(w1, w2, w3)
                diff = max(w1, w2, w3) - min(w1, w2, w3)
                pen = break_penalty(words[s1 - 1]) + break_penalty(words[s2 - 1])
                cand = (mw, diff, pen, s1, s2, (w1, w2, w3))
                if best is None or cand < best:
                    best = cand
        if best is None:
            return None
        _, diff, pen, s1, s2, ws = best
        lines = [
            " ".join(words[:s1]),
            " ".join(words[s1:s2]),
            " ".join(words[s2:]),
        ]
        return (lines, max(ws), diff, pen)

    # target_n >= 4: 게임 대사에 거의 없으니 그대로 반환
    return None


def greedy_fill_words(words: list, max_w: float):
    """Greedy fill: 첫 줄부터 max_w까지 단어를 채워 다음 줄로.

    반환: list of lines. 항상 결과를 만들고, 단어 단위 split만 사용.
    placeholder는 하나의 word로 들어와 있으므로 그대로 보존됨.
    """
    if not words:
        return []
    space = 0.5
    word_w = [line_width(w) for w in words]

    lines = []
    cur = []
    cur_w = 0.0
    for i, w in enumerate(words):
        # 현재 줄에 추가 가능?
        add_w = word_w[i] if not cur else word_w[i] + space
        if cur and cur_w + add_w > max_w:
            # 현재 줄 종료
            lines.append(" ".join(cur))
            cur = [w]
            cur_w = word_w[i]
        else:
            cur.append(w)
            cur_w += add_w
    if cur:
        lines.append(" ".join(cur))
    return lines


def is_intentional_pacing(lines: list, threshold: float = 8.0) -> bool:
    """의도적 페이싱(짧은 외침 연속) 판정.

    모든 줄이 threshold 미만이고, 각 줄이 강조 부호(!?…)로 끝나면
    의도적 짧은 라인으로 간주하여 보존한다.
    예: "죽어라!/사라져라!/으아악!", "그래!/좋다!/가자!"
    """
    if not lines or len(lines) < 2:
        return False
    if not all(line_width(l) < threshold for l in lines):
        return False
    # 강조 부호 (!?…)로 끝나는 라인이 다수면 의도적 페이싱
    emphasis_count = 0
    for l in lines:
        stripped = l.rstrip()
        if not stripped:
            continue
        if stripped[-1] in "!?！？…":
            emphasis_count += 1
    return emphasis_count >= max(2, len(lines) - 1)


def should_skip(orig: str, max_w: float, preserve_pacing: bool = True) -> bool:
    """수정 보류해야 할 메시지인지 판단.

    - placeholder 포함 줄은 단어 분할 시 안전 — 단, 줄 사이 placeholder가
      양 줄에 등장하는 등 의미 변할 수 있는 케이스만 위험.
      여기서는 일단 placeholder 있으면 수정 보류 (보수적).
      → 너무 강하면 변환 후보가 줄어드므로 placeholder를 단어 토큰으로
        취급해 변환 허용하되, 단순 boolean SKIP은 아래 케이스만:
    - 빈 줄 / 모든 줄이 너무 짧음 (모두 5글자 미만)
    - 의도적 페이싱(preserve_pacing=True 시): 모든 줄 < 8자 + 강조 부호 종결
    """
    norm = orig.replace("\r\n", "\n").replace("\r", "\n")
    lines = [l for l in norm.split("\n") if l.strip()]
    if not lines:
        return True
    # 짧은 강조 단독 라인 (전체가 한 줄 + 5글자 미만 + 마침표/감탄으로 끝)
    if len(lines) == 1:
        l = lines[0]
        # 이미 1줄이면 압축 대상 아님
        return True
    # 모든 줄이 매우 짧음 → 의도적 짧은 줄 가능성, 합치지 않음
    if all(line_width(l) <= 4.0 for l in lines):
        return True
    # 의도적 페이싱 (짧은 외침 연속) — preserve_pacing 옵션 시 보존
    if preserve_pacing and is_intentional_pacing(lines):
        return True
    # 화자명 라벨 (라인1이 `이름:` 패턴) — 보존
    if re.match(r"^[가-힣A-Za-z]{1,8}\s*[:：]\s*$", lines[0]):
        return True
    # placeholder-only 또는 거의 placeholder뿐인 메시지 보존 (포맷 정의)
    text_only = "".join(PLACEHOLDER_RE.sub("", l) for l in lines).strip()
    if line_width(text_only) <= 2.0:
        return True
    return False


def reformat(
    orig: str,
    max_w: float,
    max_w_relaxed: float = None,
    aggressive_3line_max_w: float = None,
    preserve_pacing: bool = True,
    greedy_fill: bool = False,
    greedy_max_w: float = None,
):
    """원본 ko 문자열을 압축/재정리한 새 문자열 반환. 변경 없으면 None.

    규칙:
    - placeholder/특수 케이스 보존 (should_skip).
    - 가능한 한 target_n=1 시도 → 안되면 원래 줄 수 - 1 시도 → 균형 재분배.
    - max_w_relaxed: 원본이 max_w를 초과하는 경우(예: DLC) 한정해 더 넓은
      max_w_relaxed로 재시도. 원본보다 늘리지는 않음(원본 max를 상한으로).
    - aggressive_3line_max_w: 원본이 3줄(이상)일 때 줄 수 축소 시도에서만
      max_w 상한을 이 값까지 공격적으로 늘린다. 균형 재분배에는 적용 안 함.
      None이면 비활성. 일반적으로 24~26 권장.
    - preserve_pacing: 의도적 페이싱(모든 줄 짧음 + 강조부호) 보존 여부.
    """
    if should_skip(orig, max_w, preserve_pacing=preserve_pacing):
        return None

    norm = orig.replace("\r\n", "\n").replace("\r", "\n")
    lines = [l for l in norm.split("\n")]
    n_lines = len([l for l in lines if l.strip()])
    if n_lines < 2:
        return None

    # 단어 추출 (줄바꿈 제거 + 단어 분리)
    flat = " ".join(l.strip() for l in lines if l.strip()).strip()
    flat = re.sub(r" +", " ", flat)
    words = flat.split(" ")
    if not words:
        return None

    # Greedy fill 모드: 첫 줄을 greedy_max_w까지 채우는 단순 wrap
    if greedy_fill:
        target_max = greedy_max_w if greedy_max_w is not None else max_w
        # 너무 큰 단어가 있으면 한 줄에 못 넣음 → 그래도 그 단어는 자체 줄에 둠
        greedy_lines = greedy_fill_words(words, target_max)
        if not greedy_lines:
            return None
        chosen = "\n".join(greedy_lines)
        if chosen == norm:
            return None
        # 변경 없는데 줄 수만 늘었다면 거부 (예: 첫 줄이 단어 1개라 늘어남)
        if len(greedy_lines) > n_lines:
            return None
        return chosen

    # 원본 줄 폭 측정 (relaxed 한도 결정용)
    orig_widths = [line_width(l) for l in lines if l.strip()]
    orig_max = max(orig_widths)

    # 사용할 max_w 결정: 원본이 이미 max_w 초과 시 (DLC 케이스),
    # 원본 max까지 허용 (단, max_w_relaxed 상한 적용)
    effective_max_w = max_w
    if orig_max > max_w:
        if max_w_relaxed is None or max_w_relaxed <= max_w:
            # relaxed 비활성 시 원본 그대로 두기 → None 반환은 아래 균형 재분배로 처리
            effective_max_w = orig_max
        else:
            effective_max_w = min(max_w_relaxed, max(orig_max, max_w_relaxed))

    # 3줄 공격적 압축 — 원본이 3줄 이상일 때만 줄 수 축소 시도에서 한도 상향
    # (균형 재분배에는 적용 안 함 — 새로운 라인이 원본 max를 초과하지 않도록 보존)
    aggressive_max_w = effective_max_w
    if aggressive_3line_max_w is not None and n_lines >= 3:
        aggressive_max_w = max(effective_max_w, aggressive_3line_max_w)

    # 목표: 가능한 최소 줄 수로
    target_orig = n_lines
    chosen = None

    for tn in range(1, target_orig):
        result = try_combine_to_n(words, tn, aggressive_max_w)
        if result is not None:
            chosen = "\n".join(result[0])
            break

    if chosen is None:
        # 줄 수 축소 불가 → 같은 줄 수에서 균형 재분배 시도
        result = try_combine_to_n(words, target_orig, effective_max_w)
        if result is None:
            return None
        chosen_lines, mw, diff, pen = result
        orig_diff = max(orig_widths) - min(orig_widths)
        new_max = max(line_width(l) for l in chosen_lines)
        # 새 max가 원본 max 이하이고, diff가 충분히 줄어야 채택
        if new_max <= orig_max + 0.5 and diff + 2.0 < orig_diff:
            chosen = "\n".join(chosen_lines)
        else:
            return None

    if chosen is None:
        return None
    if chosen == norm:
        return None
    return chosen


def process_data(
    data,
    sections,
    max_w,
    sample_limit=20,
    max_w_relaxed=None,
    aggressive_3line_max_w=None,
    preserve_pacing=True,
    greedy_fill=False,
    greedy_max_w=None,
    overflow_threshold=29.5,
):
    stats = {}
    samples = []
    overflow = []  # (section, id, max_w_in_msg, lines)
    for section in sections:
        sd = data.get(section)
        if not sd or "messages" not in sd:
            continue
        sec_stats = {
            "total": 0,
            "modified": 0,
            "3to2": 0,
            "3to1": 0,
            "2to1": 0,
            "balance_2": 0,
            "balance_3": 0,
            "skipped": 0,
        }
        for m in sd["messages"]:
            ko = m.get("ko", "")
            if not ko:
                continue
            sec_stats["total"] += 1
            orig_n = count_lines(ko)
            if orig_n < 2:
                continue

            new_ko = reformat(
                ko,
                max_w,
                max_w_relaxed=max_w_relaxed,
                aggressive_3line_max_w=aggressive_3line_max_w,
                preserve_pacing=preserve_pacing,
                greedy_fill=greedy_fill,
                greedy_max_w=greedy_max_w,
            )
            if new_ko is None:
                sec_stats["skipped"] += 1
                continue
            new_n = count_lines(new_ko)
            if new_n == orig_n:
                if orig_n == 2:
                    sec_stats["balance_2"] += 1
                elif orig_n == 3:
                    sec_stats["balance_3"] += 1
                else:
                    sec_stats["skipped"] += 1
                    continue
            else:
                if orig_n == 3 and new_n == 2:
                    sec_stats["3to2"] += 1
                elif orig_n == 3 and new_n == 1:
                    sec_stats["3to1"] += 1
                elif orig_n == 2 and new_n == 1:
                    sec_stats["2to1"] += 1
                else:
                    sec_stats["skipped"] += 1
                    continue
            sec_stats["modified"] += 1
            # overflow 검사
            new_lines = new_ko.split("\n")
            new_widths = [line_width(l) for l in new_lines if l.strip()]
            if new_widths and max(new_widths) > overflow_threshold:
                overflow.append(
                    (section, m.get("id"), max(new_widths), new_lines)
                )
            if len(samples) < sample_limit:
                samples.append((section, m.get("id"), m.get("ja", ""), ko, new_ko))
            m["_new_ko"] = new_ko  # apply 단계에서 사용
        stats[section] = sec_stats
    return stats, samples, overflow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="jp_messages.json에 적용")
    ap.add_argument("--max-width", type=float, default=22.0)
    ap.add_argument(
        "--max-width-relaxed",
        type=float,
        default=24.0,
        help="원본이 max-width 초과 시 허용할 상한 (DLC 케이스 등)",
    )
    ap.add_argument(
        "--aggressive-short-lines",
        action="store_true",
        help="3줄 메시지 한정으로 max_w 상한을 aggressive-max-width까지 늘려 공격적 압축",
    )
    ap.add_argument(
        "--aggressive-max-width",
        type=float,
        default=24.0,
        help="--aggressive-short-lines 모드에서 사용할 max_w 상한 (default: 24)",
    )
    ap.add_argument(
        "--no-preserve-pacing",
        dest="preserve_pacing",
        action="store_false",
        default=True,
        help="의도적 페이싱(짧은 외침 + 강조부호) 보존 규칙 해제",
    )
    ap.add_argument(
        "--sections",
        default="scemsg,scemsg_patch",
        help="쉼표로 구분된 섹션 목록 (default: 대사 섹션만)",
    )
    ap.add_argument(
        "--greedy-fill",
        action="store_true",
        help="Greedy 위쪽부터 채움 모드 (첫 줄을 max까지 채우고 다음 줄로). 균형 분배 대신 사용.",
    )
    ap.add_argument(
        "--greedy-max-width",
        type=float,
        default=None,
        help="--greedy-fill 모드의 한 줄 max 폭 (기본: --max-width-relaxed)",
    )
    ap.add_argument(
        "--overflow-threshold",
        type=float,
        default=29.5,
        help="이 폭 초과 줄은 별도 리포트로 기록 (default: 29.5, 박스 추정 한도)",
    )
    ap.add_argument("--sample", type=int, default=15)
    args = ap.parse_args()

    raw = JP_MSG.read_bytes()
    crlf = b"\r\n" in raw[:200]
    data = json.loads(raw.decode("utf-8"))
    sections = [s.strip() for s in args.sections.split(",") if s.strip()]

    aggressive_3line = args.aggressive_max_width if args.aggressive_short_lines else None

    greedy_max_w = args.greedy_max_width
    if args.greedy_fill and greedy_max_w is None:
        greedy_max_w = args.max_width_relaxed

    stats, samples, overflow = process_data(
        data, sections, args.max_width, args.sample,
        max_w_relaxed=args.max_width_relaxed,
        aggressive_3line_max_w=aggressive_3line,
        preserve_pacing=args.preserve_pacing,
        greedy_fill=args.greedy_fill,
        greedy_max_w=greedy_max_w,
        overflow_threshold=args.overflow_threshold,
    )

    print(f"=== max_width={args.max_width}, sections={sections} ===")
    for sec, s in stats.items():
        print(f"\n[{sec}]")
        for k, v in s.items():
            print(f"  {k}: {v}")

    print(f"\n--- 변환 샘플 ({len(samples)}개) ---")
    for sec, mid, ja, ko, new_ko in samples:
        print(f"\n[{sec}#{mid}]")
        if ja:
            print(f"  ja:")
            for l in ja.replace("\r\n", "\n").split("\n"):
                print(f"    | {l}")
        print(f"  ko old ({count_lines(ko)}줄):")
        for l in ko.replace("\r\n", "\n").split("\n"):
            print(f"    | {l}  (w={line_width(l):.1f})")
        print(f"  ko new ({count_lines(new_ko)}줄):")
        for l in new_ko.split("\n"):
            print(f"    | {l}  (w={line_width(l):.1f})")

    # Overflow 리포트
    if overflow:
        ovf_path = PROJECT / "temp" / "condense_overflow.txt"
        ovf_path.parent.mkdir(exist_ok=True)
        with ovf_path.open("w", encoding="utf-8") as f:
            f.write(f"# condense_dialogs overflow report (threshold={args.overflow_threshold})\n")
            f.write(f"# 총 {len(overflow)}개 메시지의 변환 결과가 box 한도 초과\n\n")
            for sec, mid, mw, lines in overflow:
                f.write(f"[{sec}#{mid}] max_w={mw:.1f}\n")
                for l in lines:
                    if not l.strip():
                        continue
                    w = line_width(l)
                    mark = " ← OVF" if w > args.overflow_threshold else ""
                    f.write(f"  | {l}  (w={w:.1f}){mark}\n")
                f.write("\n")
        print(f"\n[OVERFLOW] {len(overflow)}개 메시지 → {ovf_path}")

    if args.apply:
        applied = 0
        for section in sections:
            sd = data.get(section)
            if not sd or "messages" not in sd:
                continue
            for m in sd["messages"]:
                new_ko = m.pop("_new_ko", None)
                if new_ko is None:
                    continue
                # CRLF 보존
                if crlf:
                    new_ko = new_ko.replace("\n", "\r\n")
                m["ko"] = new_ko
                applied += 1
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if crlf:
            text = text.replace("\n", "\r\n")
            JP_MSG.write_bytes(text.encode("utf-8"))
        else:
            JP_MSG.write_text(text, encoding="utf-8")
        print(f"\n[APPLIED] {applied} entries → {JP_MSG}")
    else:
        # _new_ko 마커 제거 (메모리만)
        for section in sections:
            sd = data.get(section)
            if not sd:
                continue
            for m in sd.get("messages", []):
                m.pop("_new_ko", None)
        print(f"\n[DRY-RUN] --apply 옵션으로 실제 저장")


if __name__ == "__main__":
    main()
