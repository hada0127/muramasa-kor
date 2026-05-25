#!/usr/bin/env python3
"""gemini 배치 재번역 워커 (대사 재번역·현대화, 이슈 #9).

gemini에 [말투 가이드 + 인명 사전 + ja 원문 + 현재 번역]을 배치로 주고 재번역을 받아,
JSON으로 파싱해 candidates 파일에 저장한다. 이후 claude가 lint_dialogs/폭으로 검수·적용한다.

사용:
  python tools/retranslate_batch.py --section scemsg --start 0 --count 30 --out temp/batch/000.json
  python tools/retranslate_batch.py --section scemsg --start 0 --count 2222 --chunk 30 --out temp/batch/all.json
"""
import json
import subprocess
import os
import re
import argparse
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GUIDE = """[말투·표기 가이드 — 무라마사 사극풍 한글 재번역]
- 에도~전국시대 사극풍. 과한 현대어/신조어 금지, 단 가독성 유지. 캐릭터 내 종결어미 일관.
- 폰트 제약이 풀렸으니 원문 정보를 누락 없이 살린다(기존 번역이 줄인 부분 복원).
- 캐릭터 말투:
  · 진쿠로(무사): 거친 반말 ~다/~군/~렷다, "나"
  · 모모히메(공주): 우아·공손 ~어요/~옵니다(진쿠로엔 발끈), "저"
  · 키스케(닌자): 무뚝뚝 반말 ~다/~냐/~군
  · 유녀: 체념 ~지요/~여
  · 시골 평민(オラ/~だべ/~だ): 1인칭 "나/내"(※"이 몸" 금지), ~구먼/~것다/~댜
  · 노인/무사: ~게/~렷다/~노라  · 상인: ~네/~구먼  · 승려/악역: ~니라/~로다
- 시대 용어: 이장→명주(名主), (농사 강조 시)백성→농사꾼(百姓).
- 형식: 한 줄 최대 29.5전각(한글1.0/영숫자0.5), 최대 3줄. 줄바꿈은 \\n.
  마침표 쓰고, 줄임표(…)·마침표(.) 뒤 같은 줄에 문장 이어지면 공백 1칸(문장 시작 …는 공백 없이).
  일본어 문장부호(。、「」)·가나 절대 남기지 말 것.
"""

# 핵심 인명/지명 사전 (gemini가 반드시 따를 표준 표기)
GLOSSARY = """[인명·지명 표준 표기 — 반드시 이대로]
鬼助=키스케, 百姫=모모히메, 陣九朗=진쿠로, 虎姫=토라히메, 雪之丞=유키노조,
弓弦葉=유즈루하, 犬飼剣持/剣持=이누카이 켄모치/켄모치, 油田=아부라다, 権兵衛=곤베에,
お恋=오코이, 鳩野=하토노, 馬蕗=우마부키, せいたか童子=세이타카 동자, 白狐=백여우,
恵比寿=에비스, 数=문/냥(화폐). 일본 한자 인명은 위 표준 외엔 음독 한글로.
"""


def build_prompt(batch):
    lines = [GUIDE, GLOSSARY,
             "아래 대사들을 위 가이드대로 한국어로 재번역해줘. 각 [원문]을 보고, 현재 번역이 줄였거나",
             "어색한 부분을 원문 충실하게 복원·개선해. 화자 말투를 추정해 반영.",
             '반드시 아래 JSON 형식으로만 응답(설명·마크다운 금지). 줄바꿈은 \\n:',
             '{"<id>": "<재번역>", ...}', ""]
    for i, ja, ko in batch:
        ja1 = ja.replace('\r\n', '\\n').replace('\n', '\\n')
        ko1 = ko.replace('\n', '\\n')
        lines.append(f'id {i} | 원문: {ja1} | 현재: {ko1}')
    return '\n'.join(lines)


def call_gemini(prompt, timeout=600):
    r = subprocess.run(['gemini', '-p', prompt], capture_output=True, text=True, timeout=timeout)
    return r.stdout


def extract_json(text):
    # ```json ... ``` 또는 본문 중 최외곽 {} 추출
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.S)
    if m:
        blob = m.group(1)
    else:
        s = text.find('{'); e = text.rfind('}')
        if s < 0 or e < 0:
            return None
        blob = text[s:e+1]
    try:
        return json.loads(blob)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--section', default='scemsg')
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--count', type=int, default=30)
    ap.add_argument('--chunk', type=int, default=30, help='한 gemini 호출당 대사 수')
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
            if parsed:
                got = 0
                for k, v in parsed.items():
                    key = f'{a.section}#{re.sub(chr(92)+"D","",str(k))}'
                    result[key] = v
                    got += 1
                print(f'  [{i}~{j-1}] {got}/{len(batch)} 파싱')
            else:
                print(f'  [{i}~{j-1}] ★ JSON 파싱 실패 (gemini 응답 {len(out)}자)')
        i = j
        json.dump(result, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        time.sleep(1)
    print(f'완료: {len(result)}개 → {a.out}')


if __name__ == '__main__':
    main()
