#!/usr/bin/env python3
"""gemini 배치 검증 워커 (재번역 결과 최종 검증).

jp_messages의 [원문 ja + 현재 번역 ko(재번역됨)]를 배치로 gemini에 주고,
원문 의미 왜곡/누락·말투 부적합·인명 오류가 있는 것만 {id: 수정안} JSON으로 받는다.
정상은 생략. 결과는 claude가 검토 후 폭/lint 재확인하여 선별 반영한다.

사용:
  python tools/verify_batch.py --section scemsg --start 0 --count 2187 --chunk 40 --out temp/batch/verify.json
"""
import json
import os
import re
import argparse
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retranslate_batch import GUIDE, GLOSSARY, call_gemini, extract_json, BASE


def build_prompt(batch):
    lines = [GUIDE, GLOSSARY,
             "아래는 [원문]과 그 한국어 [번역]이야. 게임 문맥·위키 기준으로 검토해서,",
             "**원문 의미 왜곡/정보 누락, 화자 말투 부적합, 인명·용어 오류**가 있는 항목만 골라",
             '수정안을 주되, 폭(줄당 29.5전각)·최대 3줄·줄바꿈(\\n) 규칙을 지켜.',
             '반드시 {"<id>": "<수정안>", ...} JSON으로만(설명 금지). 문제없는 항목은 빼고, 전부 정상이면 {}.',
             ""]
    for i, ja, ko in batch:
        ja1 = ja.replace('\r\n', '\\n').replace('\n', '\\n')
        ko1 = ko.replace('\n', '\\n')
        lines.append(f'id {i} | 원문: {ja1} | 번역: {ko1}')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--section', default='scemsg')
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--count', type=int, default=2187)
    ap.add_argument('--chunk', type=int, default=40)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    d = json.load(open(f'{BASE}/translations/jp_messages.json', encoding='utf-8'))
    msgs = d[a.section]['messages']
    end = min(a.start + a.count, len(msgs))
    result = {}
    if os.path.exists(a.out):
        result = json.load(open(a.out, encoding='utf-8'))

    i = a.start
    while i < end:
        batch = []
        j = i
        while j < min(i + a.chunk, end):
            m = msgs[j]
            if isinstance(m, dict) and m.get('ja') and m.get('ko'):
                batch.append((j, m['ja'], m['ko']))
            j += 1
        if batch:
            out = call_gemini(build_prompt(batch))
            parsed = extract_json(out)
            if parsed is not None:
                for k, v in parsed.items():
                    result[f'{a.section}#{re.sub(chr(92)+"D","",str(k))}'] = v
                print(f'  [{i}~{j-1}] 지적 {len(parsed)}건')
            else:
                print(f'  [{i}~{j-1}] ★ 파싱 실패')
        i = j
        json.dump(result, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        time.sleep(1)
    print(f'검증 완료: 지적 {len(result)}건 → {a.out}')


if __name__ == '__main__':
    main()
