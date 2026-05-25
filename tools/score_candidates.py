#!/usr/bin/env python3
"""재번역 후보 점수화.

대사(scemsg)에서 "원문 대비 번역이 짧거나 정보가 빠졌을" 가능성이 큰 메시지를 점수순으로
정렬한다. 재번역 우선순위 산정 + 샘플 추출용.

점수 요소:
- 길이비(ratio = ko_content / ja_content): 낮을수록 축약 의심 (가장 큰 가중)
- 원문에 감탄사/줄임표/접속·종결 뉘앙스가 있는데 번역에 대응이 없을 가능성(러프 신호)
- ja에 있던 줄임표(…) 개수 대비 ko 줄임표 부족
주: ja는 한자로 정보가 압축돼 ko보다 짧을 수 있어, ratio는 절대값보다 "상대 순위"로 본다.

사용:
  python tools/score_candidates.py --top 30
  python tools/score_candidates.py --json temp/retrans_candidates.json
"""
import json
import re
import os
import argparse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUNCT = re.compile(r'[\s。、！？…・「」『』（）()\.\,\!\?\-—~■□●○◆◇★☆※♪→←↑↓]')


def content_len(s):
    """공백·부호 제외 내용 글자수."""
    return len(PUNCT.sub('', s or ''))


def load():
    return json.load(open(f'{BASE}/translations/jp_messages.json', encoding='utf-8'))


def score_msg(ja, ko):
    ja1 = (ja or '').replace('\r\n', '').replace('\n', '')
    ko1 = (ko or '').replace('\n', '')
    jl, kl = content_len(ja1), content_len(ko1)
    if jl == 0:
        return None
    ratio = kl / jl
    # 축약 점수: 한글은 보통 일본어보다 길어 ratio>1이 정상. ratio<1.0이면 축약 의심.
    shrink = max(0.0, 1.0 - ratio)
    if jl < 6:
        shrink = 0.0  # 짧은 감탄사/단답(あい·ハッ 등)은 길이비가 무의미 → 축약 대상 아님
    # 줄임표 손실: ja의 … 개수보다 ko가 적으면 뉘앙스(말끝 흐림) 손실 가능
    ja_ell = ja1.count('…') + ja1.count('・・・')
    ko_ell = ko1.count('…')
    ell_loss = max(0, ja_ell - ko_ell)
    # 종합 점수
    score = round(shrink * 100 + ell_loss * 5, 1)
    return {'ja_len': jl, 'ko_len': kl, 'ratio': round(ratio, 2),
            'ell_loss': ell_loss, 'score': score}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sections', default='scemsg,scemsg_patch')
    ap.add_argument('--top', type=int, default=30)
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    d = load()
    rows = []
    for sec in a.sections.split(','):
        msgs = d[sec]['messages'] if isinstance(d.get(sec), dict) and 'messages' in d[sec] else d.get(sec, [])
        for i, m in enumerate(msgs):
            if not isinstance(m, dict):
                continue
            s = score_msg(m.get('ja'), m.get('ko'))
            if not s:
                continue
            s.update({'section': sec, 'id': i,
                      'ja': (m.get('ja') or '').replace('\r\n', '⏎').replace('\n', '⏎')[:55],
                      'ko': (m.get('ko') or '').replace('\n', '⏎')[:60]})
            rows.append(s)
    rows.sort(key=lambda r: -r['score'])

    pos = sum(1 for r in rows if r['score'] > 0)
    print(f'대사 {len(rows)}개 / 축약 의심(score>0) {pos}개')
    if a.json:
        json.dump(rows, open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'→ {a.json}')
    print(f'\n=== 상위 {a.top} (재번역 우선) ===')
    for r in rows[:a.top]:
        print(f"  {r['section']}#{r['id']:<4} score={r['score']:<6} ratio={r['ratio']} (ja{r['ja_len']}/ko{r['ko_len']})")
        print(f"     ja={r['ja']!r}\n     ko={r['ko']!r}")


if __name__ == '__main__':
    main()
