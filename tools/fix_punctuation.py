#!/usr/bin/env python3
"""대사 문장부호 보정 (Step 1+2 통합).

Step 1: 마침표/문장종결 누락 복구
- JP 원문에서 줄 말미 부호(。！？…)를 KO 대응 위치에 추가
- 한 줄 내 두 문장(중간 종결어미 + 새 문장 시작) — 매핑 확실 시 `. ` 삽입
- 의심 케이스는 자동 수정 보류 → temp/punctuation_audit_unclear.txt 리포트

Step 2: 부호 뒤 공백 1개 추가
- `.` `…` `!` `?` `,` 뒤에 한국어/숫자가 바로 오면 공백 1개 삽입
- 줄 끝 부호 / 따옴표 직전 / 이중 공백 / 소수점(숫자.숫자) 제외
- 연속 부호 `!?` `?!` `...` `…!` 는 마지막 부호 뒤에만 공백

외부 AI 협의 (codex + gemini 수렴) 룰 준수.

사용법:
  python tools/fix_punctuation.py                  # dry-run + 리포트만
  python tools/fix_punctuation.py --apply          # 실제 저장
  python tools/fix_punctuation.py --sections scemsg,scemsg_patch
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
JP_MSG = PROJECT / "translations" / "jp_messages.json"
AUDIT_DIR = PROJECT / "temp"

# JP 줄 말미 부호 → KO 대응
JP_TO_KO_PUNCT = {
    "。": ".",
    "．": ".",
    "！": "!",
    "!!": "!!",
    "？": "?",
    "？？": "??",
    "?!": "?!",
    "！？": "!?",
    "？！": "?!",
    "…": "…",
    "‥": "…",
    "・・・": "…",
}

# KO 의문 종결어미 (정확한 의문형 — か 자동 매핑 안전)
KO_Q_ENDINGS_STRICT = (
    "더냐",
    "느냐",
    "는가",
    "는고",
    "런가",
    "인가",
    "인고",
    "는지",
    "을까",
    "을꼬",
    "리오",
    "이오",
    "이뇨",
    "느뇨",
    "으랴",
    "이랴",
    "리까",
    "리이까",
    "ㅂ니까",
    "습니까",
    "ㅂ니다",  # 정중 종결 아님 — 후처리에서 제거
)

# 정중 의문 종결 (입니까/습니까)
# 정중 평서 (입니다/습니다) — 마침표 후보
KO_Q_POLITE = ("입니까", "습니까", "ㅂ니까")
KO_DECL_POLITE = ("입니다", "습니다", "ㅂ니다")

# 한국어 의문 종결어미 — か 매핑 시 ? 후보 (단어 경계 우선)
KO_Q_ENDINGS_FOR_KA = [
    "더냐",
    "느냐",
    "는가",
    "는고",
    "런가",
    "인가",
    "인고",
    "을까",
    "을꼬",
    "리오",
    "이오",
    "리까",
    "리이까",
    "는지",
    "런지",
    "느뇨",
    "이뇨",
    "으랴",
    "냐",
    "랴",
    "까",
]

# 평서/감탄 종결 (의문 아님 — か가 와도 . 또는 !)
# - 줄 끝 매칭(마지막 줄 부호 추가)에는 모두 사용
# - 줄 중간 마침표 삽입(intra-line)에는 매우 보수적인 화이트리스트만 사용
KO_DECL_ENDINGS = [
    "이로다",
    "이다",
    "한다",
    "있다",
    "없다",
    "같다",
    "구나",
    "로다",
    "니라",
    "구려",
    "오라",
    "아라",
    "어라",
    "주거라",
    "거라",
    "되었다",
    "하였다",
    "되었더라",
    "하였더라",
    "되었더냐",
    "겠다",
    "리라",
    "으리라",
    "되리라",
    "하리라",
    "있더라",
    "없더라",
    "같더라",
    "하더라",
    "노라",
    "도다",
    "구먼",
    "게나",
    "게다",
    "오너라",
    "이라네",
    "이라오",
]

# 줄 중간 마침표 삽입에 안전한 종결어미 (강한 종결, 보수적)
# - "어라/아라/오라"는 명령형이라 종결로 보이나 "어라"는 감탄사로도 쓰임 → 제외
# - "있다/없다/한다/이다" 등은 "있다고/있다면/한다고" 같은 연결어미 충돌 → 제외
# - 결과적으로 명확한 종결 형태만 사용
KO_INTRA_SAFE_DECL_ENDINGS = [
    "이로다",
    "되었다",
    "하였다",
    "되었더라",
    "하였더라",
    "되었더냐",  # 이것 자체는 의문이지만 사용자 예시 케이스
    "주거라",
    "구나",
    "도다",
    "노라",
    "오너라",
]
# 의문 + 줄 중간 (Q-Q-...) 보존
KO_INTRA_SAFE_Q_ENDINGS = [
    "더냐",
    "느냐",
    "는가",
    "런가",
    "인가",
    "리오",
    "이오",
]


# ===== KO-only 분류 (JP 원문과 무관하게 자동 부호 추가) =====
# codex + gemini 협의 수렴 (2026-05-17): 줄바꿈 재배치 후 종결어미만 명확하면 자동 추가.
# Q 의문(?)/DECL 평서(.)/CMD 명령(.). 명사·호칭·짧은 감탄사는 SKIP.

# 자동 의문(?) — 의문 종결어미가 매우 강한 케이스
AUTO_Q_KO_ENDINGS = [
    # 기존 strict
    "더냐", "느냐", "는가", "는고", "런가", "인가", "인고",
    "을까", "을꼬", "는지", "런지", "리오", "이오",
    "리까", "리이까", "ㅂ니까", "습니까", "쏘냐", "이뇨", "느뇨",
    # 협의 확장
    "이냐", "거냐", "것이냐", "겠나", "잖나", "라니",
    "이랴", "으랴", "랴",
    # 어말 단음절 (보수적 — 분류 우선순위 마지막에 둠)
    "까",
    "느뇨", "이뇨",
]

# 자동 평서(.) — 명확한 평서 종결
AUTO_DECL_KO_ENDINGS = [
    # 기존 strict
    "이로다", "되었다", "하였다", "되었더라", "하였더라", "되었더냐",
    "구나", "도다", "노라", "리라", "이라네", "이라오",
    "구먼", "구려", "ㅂ니다", "습니다", "니라", "이니라", "느니라",
    # 협의 확장: 정중 평서
    "합니다", "옵니다", "입니다", "답니다", "였답니다", "이옵니다",
    "이올시다", "올시다",
    # 의지·약속·추측·확인
    "주마", "리다", "이리다", "겠지", "겠소", "겠어요",
    "이로군", "로군", "이로세", "로세",
    # 감탄·반어·존속어미
    "지요", "이지요", "잖아", "지롱",
    "다오", "거다", "이거다",
    # 과거형
    "는다", "었다",  # "있었다", "갔었다" 등
    # 명령형 평서 (목적어 + 끝)
    "마라", "해라",
    # 단정
    "었네", "였네", "다네", "이라네",
]

# 자동 명령(.)
AUTO_CMD_KO_ENDINGS = [
    "주거라", "거라", "어라", "아라", "오라",
    "오너라", "셔라", "옵소서", "하라", "가라",
    "있거라", "보거라", "들거라",
]

# 명사형 종결 SKIP — 인명·고유명사 어말 (호칭은 마침표 어색)
HONORIFIC_NAMES_NOPUNCT = set([
    # 인물 (이름 끝 마침표 어색)
    "모모히메", "토라히메", "키스케", "오코이", "오보로",
    "젠고로", "토모에", "단자부로", "야지로", "키치베에",
    "마타이치", "사덴", "이치베에", "후타바", "쿠즈류",
    "스이세이", "텐류", "타이로", "쇼군", "타이코",
    # 호칭
    "님", "씨", "공", "전",
])

# 평서로 자동 적용 시 false-positive 위험 — 길이 가드 적용 (10자 이상에서만)
RISKY_DECL_ENDINGS = set([
    "이다", "한다", "있다", "없다", "같다", "겠다", "이라",
])

# 명사/조사로 끝나는 경우 → SKIP (어절 마지막 글자 검사)
KO_PARTICLES_END = set(["을", "를", "은", "는", "이", "가", "에", "의",
                         "도", "만", "와", "과", "로", "랑", "께", "께서"])

# 줄 중간/한 줄 두 문장 결합용 — 매우 보수적 강한 종결만
# 연결어미·인용 충돌 가능한 어미(까/라니/이라/는다/었다)는 제외
KO_INTRA_AUTO_DECL = [
    "이로다", "되었다", "하였다", "되었더라", "하였더라", "되었더냐",
    "주거라", "구나", "도다", "노라", "오너라",
    "합니다", "옵니다", "입니다", "ㅂ니다", "습니다",
    "리라", "이라오", "이라네",
    "하라", "셔라", "옵소서",
]

KO_INTRA_AUTO_Q = [
    "더냐", "느냐", "는가", "런가", "인가", "리오", "이오",
    "습니까", "ㅂ니까",
]


def classify_ko_ending(line: str):
    """KO 줄 끝 종결어미 분류. ('Q'|'DECL'|'CMD'|'RISKY_DECL'|None, end_str).

    - 가장 긴 어미 우선 매칭
    - 부호 이미 있으면 None
    - 짧은 메시지 (1-2글자) 감탄사면 None
    - 명사/조사 끝이면 None
    """
    s = line.rstrip()
    if not s:
        return (None, None)
    last_ch = s[-1]
    # 부호 이미 있음
    if last_ch in ".!?…,)」』]":
        return (None, None)
    # 한글 아니면 SKIP
    if not ("가" <= last_ch <= "힣"):
        return (None, None)
    # 너무 짧은 (1-2글자) — 보수적 SKIP
    if len(s.replace(" ", "")) < 3:
        return (None, None)
    # 조사 끝
    if last_ch in KO_PARTICLES_END:
        return (None, None)
    # 호칭/이름 끝 (마지막 어절이 화이트리스트)
    last_word = s.split()[-1] if s.split() else ""
    if last_word in HONORIFIC_NAMES_NOPUNCT:
        return (None, None)
    # 종결어미 매칭 (가장 긴 것 우선)
    # CMD 우선 (가장 명확)
    for end in sorted(AUTO_CMD_KO_ENDINGS, key=len, reverse=True):
        if s.endswith(end):
            return ("CMD", end)
    for end in sorted(AUTO_Q_KO_ENDINGS, key=len, reverse=True):
        if s.endswith(end):
            return ("Q", end)
    for end in sorted(AUTO_DECL_KO_ENDINGS, key=len, reverse=True):
        if s.endswith(end):
            return ("DECL", end)
    for end in sorted(RISKY_DECL_ENDINGS, key=len, reverse=True):
        if s.endswith(end):
            # 길이 가드 (10자 이상) — 짧은 단일 단어 명사 종결 회피
            if len(s.replace(" ", "")) >= 10:
                return ("RISKY_DECL", end)
            return (None, None)
    return (None, None)

# Placeholder 패턴
PLACEHOLDER_RE = re.compile(r"@#?[c#]?\([\d,]+\)|@/[#c]|%[sd]")

# 한국어 글자 + 숫자
HANGUL_CLASS = r"가-힣"
DIGIT_CLASS = r"0-9"


def line_width(s: str) -> float:
    s_clean = PLACEHOLDER_RE.sub("X", s)
    w = 0.0
    for c in s_clean:
        w += 0.5 if ord(c) < 0x80 else 1.0
    return w


def strip_trailing_ws(s: str) -> str:
    return s.rstrip(" \t")


# ----- Step 1: 종결 부호 보정 -----


def ja_line_end_punct(line: str) -> str:
    """JP 줄 말미 부호 추출 (가장 긴 매칭)."""
    line = line.rstrip()
    if not line:
        return ""
    # 연속 부호 케이스
    for cand in ("！？", "？！", "・・・"):
        if line.endswith(cand):
            return cand
    # 끝 1글자
    c = line[-1]
    if c in "。．！？…‥":
        return c
    return ""


def ja_line_ends_with_ka(line: str) -> bool:
    """JP 줄이 부호 없이 「か」로 끝나는지."""
    line = line.rstrip()
    return bool(line) and line[-1] == "か"


# 일본어 평서 종결 패턴 (부호 없음) — KO에 `.` 추가 후보
JA_DECL_SUFFIXES = ("じゃ", "だ", "ぞ", "ぜ", "な", "ね", "わ", "のだ", "のじゃ",
                    "る", "た", "い", "ない", "らん", "ます", "ません",
                    "けり", "けれ", "なり", "たり")


def ja_line_decl_terminal(line: str) -> bool:
    """JP 줄이 명백한 평서 종결로 끝나는지. 매우 보수적."""
    line = line.rstrip()
    if not line:
        return False
    # 평서 종결 어미 — 다만 줄 중간일 수도 있음. KO 마지막 종결 후보로만 사용
    # 보수적으로 매우 특징적인 종결만 매칭
    for suf in ("のじゃ", "じゃ", "のだ", "だぞ", "だぜ", "だな", "だね", "だわ"):
        if line.endswith(suf):
            return True
    return False


def ko_line_end_punct(line: str) -> str:
    """KO 줄 말미 부호 (있으면 가장 긴 매칭)."""
    line = line.rstrip()
    if not line:
        return ""
    # 연속 부호
    for cand in ("!?", "?!", "...", "!!", "??"):
        if line.endswith(cand):
            return cand
    c = line[-1]
    if c in ".!?…":
        return c
    return ""


def ko_line_is_question(line: str) -> bool:
    """KO 줄이 의문 종결어미로 끝나는지."""
    line = line.rstrip().rstrip(".!?… \t")
    if not line:
        return False
    for end in KO_Q_ENDINGS_FOR_KA:
        if line.endswith(end):
            return True
    return False


def ko_line_is_polite_q(line: str) -> bool:
    line = line.rstrip().rstrip(".!?… \t")
    return any(line.endswith(e) for e in KO_Q_POLITE)


def ko_line_is_polite_decl(line: str) -> bool:
    line = line.rstrip().rstrip(".!?… \t")
    return any(line.endswith(e) for e in KO_DECL_POLITE)


def ko_line_is_decl(line: str) -> bool:
    line = line.rstrip().rstrip(".!?… \t")
    if not line:
        return False
    for end in KO_DECL_ENDINGS:
        if line.endswith(end):
            return True
    return False


def has_unmatched_quote(line: str) -> bool:
    """따옴표가 열렸으나 닫히지 않았으면 True. 부호 추가 시 위험."""
    opens = line.count("「") + line.count("『") + line.count('"')
    closes = line.count("」") + line.count("』")
    return opens != closes


# 연결어미/조사로 끝나면 부호 추가 보류
# (다음 줄로 이어지는 의미라 부호 어색)
KO_CONNECTORS_LAST_CHAR = set("고면니네지만랑라고서며거든도는은이가을를에의도만")
KO_CONNECTORS_SUFFIX = (
    "그리고",
    "그러나",
    "그래도",
    "그러니",
    "그래서",
    "그러므로",
    "허나",
    "하지만",
    "하면서",
    "한데",
    "하고",
    "라며",
    "라면",
    "라도",
    "라도록",
    "되어",
    "되어서",
    "하여",
    "하여서",
    "면서",
    "지만",
    "는데",
    "은데",
    "거든",
    "더라도",
    "려면",
    "려고",
    "려는",
    "려면",
    "려니",
    "이지만",
    "이라서",
    "이라며",
    "이라고",
    "라며",
)


def line_ends_with_connector(line: str) -> bool:
    s = line.rstrip()
    if not s:
        return False
    for suf in KO_CONNECTORS_SUFFIX:
        if s.endswith(suf):
            return True
    return False


def safe_append_punct_to_line(line: str, punct: str) -> str:
    """라인 끝에 부호 추가. 이미 부호 있으면 그대로."""
    stripped = line.rstrip()
    if not stripped:
        return line
    # 이미 부호 있으면 SKIP (보존)
    if stripped[-1] in ".!?…」』)":
        return line
    # 따옴표 닫는 자리 직전 부호 추가? 안전을 위해 SKIP
    if has_unmatched_quote(stripped):
        return line
    # 연결어미로 끝나면 부호 추가 보류 (의미 어색)
    if line_ends_with_connector(stripped):
        return line
    trailing = line[len(stripped) :]
    return stripped + punct + trailing


# 한 줄 내 두 문장 결합 패턴
# 종결어미 + 공백 + 한국어 새 문장 시작
# 보수적 화이트리스트만 사용 (false positive 회피)
INTRA_LINE_PATTERNS = []
# 기존 strict + 확장 AUTO 종결어미 모두 결합
_intra_decl = list(dict.fromkeys(KO_INTRA_SAFE_DECL_ENDINGS + KO_INTRA_AUTO_DECL))
_intra_q = list(dict.fromkeys(KO_INTRA_SAFE_Q_ENDINGS + KO_INTRA_AUTO_Q))
for end in _intra_decl:
    pat = re.compile(r"(?<![가-힣])(" + re.escape(end) + r") +(?=[가-힣])")
    INTRA_LINE_PATTERNS.append(("D", end, pat))
for end in _intra_q:
    pat = re.compile(r"(?<![가-힣])(" + re.escape(end) + r") +(?=[가-힣])")
    INTRA_LINE_PATTERNS.append(("Q", end, pat))


def fix_punct_for_message(ko: str, ja: str, audit_log: list, msg_key: str):
    """메시지 단위 부호 보정. 변경된 KO 반환. 변경 없으면 None.

    audit_log: (msg_key, kind, before, after, reason) 튜플로 의심 케이스 기록
    """
    if not ko:
        return None
    ko_norm = ko.replace("\r\n", "\n").replace("\r", "\n")
    ja_norm = (ja or "").replace("\r\n", "\n").replace("\r", "\n")

    ko_lines = ko_norm.split("\n")
    ja_lines = ja_norm.split("\n")

    # Placeholder 포함하면 의심 처리, 자동 수정 보류
    if any(PLACEHOLDER_RE.search(l) for l in ko_lines):
        return None  # 보수적

    changed = False
    new_lines = list(ko_lines)

    # 케이스 A: 마지막 줄 종결 부호 (메시지 끝)
    # JP 마지막 줄 부호 → KO 마지막 줄에 적용
    if ja_lines:
        ja_last = ja_lines[-1].rstrip()
        ja_punct = ja_line_end_punct(ja_last)
        ja_last_ends_ka = ja_line_ends_with_ka(ja_last)
        ko_last_idx = len(new_lines) - 1
        # 마지막 비어있지 않은 줄 찾기
        while ko_last_idx >= 0 and not new_lines[ko_last_idx].strip():
            ko_last_idx -= 1
        if ko_last_idx >= 0:
            ko_last = new_lines[ko_last_idx]
            ko_last_stripped = ko_last.rstrip()
            ko_punct = ko_line_end_punct(ko_last_stripped)
            if not ko_punct:  # KO에 부호 없음
                target_punct = None
                if ja_punct:
                    target_punct = JP_TO_KO_PUNCT.get(ja_punct)
                elif ja_last_ends_ka:
                    if ko_line_is_question(ko_last_stripped):
                        target_punct = "?"
                    elif ko_line_is_decl(ko_last_stripped):
                        target_punct = "."
                elif ja_line_decl_terminal(ja_last):
                    # JA 줄 끝이 평서 종결 패턴 (のじゃ/だ 등)
                    if ko_line_is_decl(ko_last_stripped) or ko_line_is_polite_decl(ko_last_stripped):
                        target_punct = "."
                    # 명령형 끝 (주거라/오라/아라/어라/하라)
                    elif any(ko_last_stripped.endswith(e) for e in ("주거라", "오라", "아라", "어라", "거라", "하라", "오너라")):
                        target_punct = "."

                # 케이스 A-2: KO-only 분류 (codex+gemini 협의 수렴)
                # JP 부호 없거나 줄 수 불일치라도 KO 종결어미만 명확하면 자동 추가
                if not target_punct:
                    kind, end = classify_ko_ending(ko_last_stripped)
                    if kind == "Q":
                        target_punct = "?"
                    elif kind in ("DECL", "CMD", "RISKY_DECL"):
                        target_punct = "."

                if target_punct:
                    new_l = safe_append_punct_to_line(ko_last, target_punct)
                    if new_l != ko_last:
                        new_lines[ko_last_idx] = new_l
                        changed = True

    # 케이스 B: KO 중간 줄 (개행 직전) 부호 — JP/KO 줄 수가 같을 때 정렬
    if (
        len(ja_lines) == len(ko_lines)
        and len(ja_lines) >= 2
        and any(new_lines[i].strip() and not ko_line_end_punct(new_lines[i].rstrip()) for i in range(len(new_lines) - 1))
    ):
        # 한 줄씩 정렬해 마지막 제외하고 부호 보정
        for i in range(len(new_lines) - 1):
            ja_l = ja_lines[i].rstrip()
            ko_l = new_lines[i]
            ko_l_stripped = ko_l.rstrip()
            if not ko_l_stripped or not ja_l:
                continue
            if ko_line_end_punct(ko_l_stripped):
                continue
            ja_punct = ja_line_end_punct(ja_l)
            ja_ka = ja_line_ends_with_ka(ja_l)
            target = None
            if ja_punct:
                target = JP_TO_KO_PUNCT.get(ja_punct)
            elif ja_ka:
                if ko_line_is_question(ko_l_stripped):
                    target = "?"
                elif ko_line_is_decl(ko_l_stripped):
                    target = "."
            if target:
                new_l = safe_append_punct_to_line(ko_l, target)
                if new_l != ko_l:
                    new_lines[i] = new_l
                    changed = True

    # 케이스 B-2: KO-only 중간 줄 — 매우 보수적
    # KO_INTRA_AUTO_DECL/Q 강한 종결어미만 자동 추가 (연결어미 충돌 회피)
    # JP/KO 줄 수 무관, 다음 줄이 한글로 시작 + 조사/연결구가 아닐 때만
    _intra_auto_set = set(KO_INTRA_AUTO_DECL + KO_INTRA_AUTO_Q)
    for i in range(len(new_lines) - 1):
        ko_l = new_lines[i]
        ko_l_stripped = ko_l.rstrip()
        if not ko_l_stripped:
            continue
        if ko_line_end_punct(ko_l_stripped):
            continue
        # 다음 비어있지 않은 줄 찾기
        next_line = ""
        for j in range(i + 1, len(new_lines)):
            if new_lines[j].strip():
                next_line = new_lines[j].lstrip()
                break
        if not next_line:
            continue
        first_ch = next_line[0]
        if not ("가" <= first_ch <= "힣"):
            continue
        # 조사·연결어미로 시작하면 SKIP (의미상 줄 끝이 절 끝이 아님)
        if any(next_line.startswith(p) for p in
               ("그리고", "그러나", "그래도", "그러니", "그래서", "그러므로",
                "허나", "하지만", "라면", "라도", "이라도",
                "만큼", "처럼", "보다", "한테", "에게", "에서",
                # 종결-연결 충돌 회피용 추가
                "말", "생각", "이야기")):
            continue
        if next_line[:1] in KO_PARTICLES_END:
            continue
        # 종결어미 일치 + intra_auto 화이트리스트 안에 있어야 자동 추가
        kind, end = classify_ko_ending(ko_l_stripped)
        if not kind or end not in _intra_auto_set:
            continue
        target = "?" if kind == "Q" else "."
        new_l = safe_append_punct_to_line(ko_l, target)
        if new_l != ko_l:
            new_lines[i] = new_l
            changed = True

    # 케이스 C: 한 줄 내 두 문장 (종결어미 + 공백 + 새 한글)
    # 보수적: D-패턴(평서)만 자동 적용. Q-패턴(의문)은 보류 (false positive 위험)
    for i, l in enumerate(new_lines):
        if not l.strip():
            continue
        # 따옴표 안 / placeholder 있으면 SKIP
        if has_unmatched_quote(l) or PLACEHOLDER_RE.search(l):
            continue
        new_l = l
        for kind, end, pat in INTRA_LINE_PATTERNS:
            # 매칭 후 → "{end}{punct} " 으로 치환. 단 false positive 방지를 위해
            # 매칭된 종결어미 다음 시작 단어가 조사/연결어미 등이면 SKIP.
            punct = "?" if kind == "Q" else "."

            def _repl(m, _p=punct):
                # 종결어미 매칭 뒤 단어 시작 검사
                start_after = m.end()
                rest = new_l[start_after : start_after + 4]
                first_after = rest[0:1]
                # false positive 단어 시작은 SKIP: "있다고/이라며/이라고/한다면 ..."
                if first_after in ("고", "면", "니", "네", "지", "도", "만", "랑", "라", "구", "랴", "오"):
                    return m.group(0)
                return m.group(1) + _p + " "

            replaced = pat.sub(_repl, new_l)
            new_l = replaced
        if new_l != l:
            new_lines[i] = new_l
            changed = True

    if not changed:
        return None
    new_ko = "\n".join(new_lines)
    if new_ko == ko_norm:
        return None
    return new_ko


# ----- Step 2: 부호 뒤 공백 -----

# 부호 그룹 + 한국어/숫자 시작 → 부호 그룹 + 공백 + 글자
# 부호: . , ; … ! ?
# 단 줄 끝 / 다음 글자 공백 / 따옴표 / 숫자.숫자 (소수점) 제외
SPACE_AFTER_PATTERNS = [
    # 마침표 (소수점 제외) — 앞이 숫자 아니거나 뒤가 숫자 아닐 때
    # 가장 안전: 한글 다음 . + 한글
    (
        re.compile(r"(?<=[가-힣)\]」』])([.!?])(?=[가-힣])"),
        r"\1 ",
    ),
    # 마침표/느낌표/물음표 (영문/숫자 뒤 + 한글 다음)
    (
        re.compile(r"([.!?]+)(?=[가-힣])(?<![0-9][.!?])"),
        r"\1 ",
    ),
    # 말줄임표 뒤 한글 — 의도적으로 붙임 허용도 있으나, 사용자 요청은 "추가"
    (
        re.compile(r"(…+|\.\.\.)(?=[가-힣0-9])"),
        r"\1 ",
    ),
    # 쉼표 뒤
    (
        re.compile(r"(,)(?=[가-힣0-9])"),
        r"\1 ",
    ),
]


def add_space_after_punct(ko: str, overflow_threshold: float = 28.0):
    """부호 뒤 공백 추가. 변경된 KO 반환 (변경 없으면 None).

    Returns: (new_ko, overflow_lines_after)
    overflow_lines_after: 변경 후 폭이 threshold 초과한 라인 인덱스 목록
    """
    if not ko:
        return None, []
    ko_norm = ko.replace("\r\n", "\n").replace("\r", "\n")
    lines = ko_norm.split("\n")
    new_lines = []
    changed = False
    overflow_after = []

    for li, line in enumerate(lines):
        # placeholder 라인은 SKIP (포맷 깨질 위험)
        if PLACEHOLDER_RE.search(line):
            new_lines.append(line)
            continue
        nl = line
        # 1) 연속 부호 그룹 처리: "다." "다." "다." 등
        # 마침표/느낌표/물음표 시퀀스 추출 후 처리
        # 마침표/말줄임표: (?<![0-9])\.(?=[가-힣]) 만 매칭, 소수점 제외
        # 우리는 한글 사이 부호만 다룬다 (안전)

        # 패턴 1: 한글 + . + 한글 → . 공백
        nl = re.sub(r"(?<=[가-힣])\.(?=[가-힣])", ". ", nl)
        # 패턴 2: 한글 + ! + 한글
        nl = re.sub(r"(?<=[가-힣])!(?=[가-힣])", "! ", nl)
        # 패턴 3: 한글 + ? + 한글
        nl = re.sub(r"(?<=[가-힣])\?(?=[가-힣])", "? ", nl)
        # 패턴 4: 한글 + … (한개 이상) + 한글
        nl = re.sub(r"(?<=[가-힣])(…+)(?=[가-힣])", r"\1 ", nl)
        # 패턴 5: 한글 + ... + 한글 (3개 점)
        nl = re.sub(r"(?<=[가-힣])(\.\.\.)(?=[가-힣])", r"\1 ", nl)
        # 패턴 6: 한글 + , + 한글/숫자
        nl = re.sub(r"(?<=[가-힣])(,)(?=[가-힣0-9])", r"\1 ", nl)
        # 패턴 7: 연속 부호 마지막 + 한글  ("!?", "?!", "!!" 등)
        nl = re.sub(r"(?<=[가-힣])([!?]{2,})(?=[가-힣])", r"\1 ", nl)
        # 패턴 8: 닫는 따옴표 뒤 부호 + 한글
        nl = re.sub(r"([」』])([.!?…]+)?(?=[가-힣])", lambda m: m.group(0)[: -1] + " " + m.group(0)[-1] if False else None or m.group(0), nl)
        # 위 패턴 8은 noop placeholder. 따옴표 뒤 부호는 일단 후속 처리 안 함 (보존)

        # 패턴 9: 닫는 따옴표 뒤 한글 → 공백
        nl = re.sub(r"(?<=[」』])(?=[가-힣])", " ", nl)
        # 패턴 10: 마침표/점3개 뒤 숫자 (예: …7년 후, ... 1만년)
        nl = re.sub(r"(?<=[가-힣])(…+|\.\.\.)(?=[0-9])", r"\1 ", nl)

        # 이중 공백 정리
        nl = re.sub(r"  +", " ", nl)

        if nl != line:
            changed = True
        new_lines.append(nl)

        # overflow 검사
        if line_width(nl) > overflow_threshold:
            overflow_after.append(li)

    if not changed:
        return None, overflow_after
    return "\n".join(new_lines), overflow_after


# ----- 메인 처리 -----


def process(data, sections, audit_log, overflow_log, overflow_threshold):
    stats = {}
    for sec in sections:
        sd = data.get(sec)
        if not sd or "messages" not in sd:
            continue
        s = {
            "total": 0,
            "step1_changed": 0,
            "step2_changed": 0,
            "both_changed": 0,
            "overflow_after": 0,
        }
        for idx, m in enumerate(sd["messages"]):
            ko = m.get("ko", "")
            ja = m.get("ja", "")
            if not ko:
                continue
            s["total"] += 1
            mid = m.get("id")
            msg_key = f"{sec}#{mid if mid is not None else f'idx{idx}'}"

            step1_ko = fix_punct_for_message(ko, ja, audit_log, msg_key)
            cur = step1_ko if step1_ko else ko
            step2_ko, overflows = add_space_after_punct(cur, overflow_threshold)
            final = step2_ko if step2_ko else cur

            if step1_ko:
                s["step1_changed"] += 1
            if step2_ko:
                s["step2_changed"] += 1
            if step1_ko and step2_ko:
                s["both_changed"] += 1

            if overflows:
                s["overflow_after"] += 1
                overflow_log.append((msg_key, overflows, final))

            if final != ko:
                m["_new_ko"] = final

        stats[sec] = s
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--sections",
        default="scemsg,scemsg_patch",
        help="쉼표 구분 (default: 대사 섹션만)",
    )
    ap.add_argument(
        "--overflow-threshold",
        type=float,
        default=28.0,
        help="공백 추가 후 이 폭 초과 라인은 overflow 리포트 (default: 28.0)",
    )
    args = ap.parse_args()

    raw = JP_MSG.read_bytes()
    crlf = b"\r\n" in raw[:200]
    data = json.loads(raw.decode("utf-8"))

    sections = [s.strip() for s in args.sections.split(",") if s.strip()]

    audit_log = []
    overflow_log = []

    stats = process(data, sections, audit_log, overflow_log, args.overflow_threshold)

    print("=== Step 1+2 결과 ===")
    for sec, s in stats.items():
        print(f"\n[{sec}]")
        for k, v in s.items():
            print(f"  {k}: {v}")

    # 샘플 출력
    print("\n--- 변환 샘플 ---")
    shown = 0
    for sec in sections:
        sd = data.get(sec, {})
        for idx, m in enumerate(sd.get("messages", [])):
            new_ko = m.get("_new_ko")
            if not new_ko or shown >= 10:
                continue
            print(f"\n[{sec}#{m.get('id') or f'idx{idx}'}]")
            print(f"  JA: {m.get('ja','')}")
            print(f"  OLD: {repr(m.get('ko',''))}")
            print(f"  NEW: {repr(new_ko)}")
            shown += 1

    # Audit / overflow 리포트
    AUDIT_DIR.mkdir(exist_ok=True)
    overflow_path = AUDIT_DIR / "punctuation_overflow.txt"
    if overflow_log:
        with overflow_path.open("w", encoding="utf-8") as f:
            f.write(f"# 부호 추가 후 폭 {args.overflow_threshold} 초과 라인\n")
            f.write(f"# 총 {len(overflow_log)} 메시지\n\n")
            for msg_key, lines, text in overflow_log:
                f.write(f"[{msg_key}] overflow lines={lines}\n")
                for li, l in enumerate(text.split("\n")):
                    mark = " ← OVF" if li in lines else ""
                    f.write(f"  {li}: {l}  (w={line_width(l):.1f}){mark}\n")
                f.write("\n")
        print(f"\n[OVERFLOW] {len(overflow_log)}개 메시지 → {overflow_path}")

    if args.apply:
        applied = 0
        for sec in sections:
            sd = data.get(sec, {})
            for m in sd.get("messages", []):
                new_ko = m.pop("_new_ko", None)
                if new_ko is None:
                    continue
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
        # _new_ko 정리
        for sec in sections:
            sd = data.get(sec, {})
            for m in sd.get("messages", []):
                m.pop("_new_ko", None)
        print(f"\n[DRY-RUN] --apply 옵션으로 실제 저장")


if __name__ == "__main__":
    main()
