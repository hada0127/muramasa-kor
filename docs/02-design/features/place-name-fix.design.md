# Design: Place Name & Story Select Rendering Fix

- Feature: `place-name-fix`
- Selected Architecture: **Option C — Pragmatic Hybrid**
- Created: 2026-04-13
- PDCA Phase: Design

## Context Anchor

| 항목 | 내용 |
|------|------|
| **WHY** | 한글 패치 품질의 기본선. 반복 노출되는 장면 헤더/스토리 선택이 깨지면 패치 전체가 불안정해 보임. |
| **WHO** | 하다(패처), 한글판 플레이어 (DLC 포함 본편 진행자). |
| **RISK** | OOR(Out-Of-Range) 바이트는 전체 3,328개 메시지로 파급된 시스템 이슈. 폰트 매핑 확장은 아틀라스 재생성을 유발하므로 이번 스코프에서는 **데이터 수정만**. |
| **SUCCESS** | (1) 장면 헤더 정상, (2) Act 라벨 정상, (3) 회귀 없음, (4) 유사 버그 재발 방지 감사 도구 동작. |
| **SCOPE** | `translations/jp_messages.json` 수정 + `tools/audit_oor.py` 신규 + wii 교차검증 리포트. sysmsg NMS만 재빌드·재설치. |

## 1. Overview

세 가지 수정을 하나의 PR로 묶는다:

1. **번역 오류 제거** — `武蔵`의 잘못된 번역 "사무라이시"(5자)를 "무사시"(3자)로 일괄 교체. 추가로 `wii/messages/kr` 자료와 지명 전체 교차검증.
2. **Act 라벨 재인코딩** — `제2막~제7막` 안의 ASCII 숫자 `2~7`을 한글 매핑 내 syllable로 교체 (예: `이막, 삼막, 사막…` 또는 `제이막, 제삼막…`).
3. **OOR 감사 도구** — 빌드 산출물(패치 NMS)을 스캔하여 매핑 범위 밖 바이트를 가진 메시지를 보고하는 `tools/audit_oor.py`. 회귀 방지·후속 과제 가시성.

폰트·매핑·빌드 로직은 **건드리지 않는다**.

## 2. Architecture Decision (Option C)

### 2.1 왜 C인가

| 항목 | 판단 |
|------|------|
| 이번 문제 규모 | 지명 9곳 + Act 라벨 6곳 = **~15 엔트리** — JSON 수정으로 충분 |
| 시스템 이슈(OOR 3,328건) | 원인 별도, 이번 PR로 해결 불가. 감사 도구가 있어야 **가시화**됨 |
| 폰트 건드림 | HD 팩 오버레이 규칙(`auto_font_import.py`)·ASCII 매핑(`_build_ascii_sjis_map`) 변경은 회귀 위험 크고, DLC/본편/시스템 메시지 전체 재검증 필요 |
| 사용자 요구 우선순위 | "지명·스토리 선택 깨짐 해결" — 데이터 수정이 가장 직접적 |

### 2.2 핵심 설계 원칙

- **데이터 우선(Data-first)**: 렌더링 파이프라인은 안정됨이 검증됨(다른 텍스트 정상 출력). 문제는 데이터(번역/인코딩 선택).
- **한글 매핑 내 기호만 사용**: "제2막"의 ASCII 숫자 2는 `_build_ascii_sjis_map`이 cell 2622(OOR)로 내보냄. 대체안: 한글 "이/삼/사/오/육/칠"(in-range, cells 1644~2603 내).
- **후속 과제는 분리**: ASCII 숫자의 in-range 재매핑, 전체 OOR 치환, 폰트 페이지 확장은 다른 feature로.

## 3. Module Map

```
place-name-fix/
├── data/
│   ├── translations/jp_messages.json          [MODIFY]  ← sysmsg 엔트리 9 + 6 수정
│   └── translations/proper_nouns.json         [VERIFY]  ← 武蔵 매핑 확인 (현재 OK)
├── tools/
│   └── tools/audit_oor.py                     [NEW]     ← OOR 바이트 감사 스크립트
├── reports/
│   └── docs/03-analysis/place-name-wii-xcheck.md  [NEW, 임시]  ← wii 교차검증 리포트
└── patch artifacts/
    ├── patch_main/*/sysmsg.nms                [REBUILD]
    ├── patch_main/_US/*/sysmsg.nms            [REBUILD]
    ├── patch_patch/*/sysmsg.nms               [REBUILD]
    └── patch_patch/_US/*/sysmsg.nms           [REBUILD]
```

## 4. Detailed Design

### 4.1 번역 오류 교체

**대상**: `translations/jp_messages.json` 내 `sysmsg.messages` + `scemsg.messages` 등 모든 섹션에서 `"사무라이시"` 문자열.

**전략**:
```python
# 모든 ko 필드에서 "사무라이시" → "무사시"
# grep 기준 10+ 건 확인됨 (sysmsg 9 + scemsg 일부)
for section in data.values():
    if isinstance(section, dict) and 'messages' in section:
        for m in section['messages']:
            if 'ko' in m:
                m['ko'] = m['ko'].replace('사무라이시', '무사시')
```

**검증**: 교체 후 다시 grep `"사무라이시"` = 0건 확인.

### 4.2 Act 라벨 재인코딩

**대상**: `sysmsg.messages` id `65~70`의 `ko` 필드.

**변환 규칙**:
| id | JP | 현재 ko | 교체 ko |
|---|---|---|---|
| 65 | 二幕 | `제2막` | `이막` |
| 66 | 三幕 | `제3막` | `삼막` |
| 67 | 四幕 | `제4막` | `사막` |
| 68 | 五幕 | `제5막` | `오막` |
| 69 | 六幕 | `제6막` | `육막` |
| 70 | 七幕 | `제7막` | `칠막` |

**근거**:
- 한국어에서 "이막/삼막/사막…" 표현이 극·드라마 chapter에 자연스러움.
- JP 원문도 `二幕/三幕…` 순서대로 표기 — 접두 "제"를 유지할 필요 낮음.
- `이/삼/사/오/육/칠/막` 모두 `kr_sjis_mapping.json` 내 존재 확인 필요 (§4.2.1).

**대체안 (if "막" 단독이 어색하면)**: `"제 이 막"` 띄어쓰기 포함 — 공백은 0x20 raw로 정상 렌더링됨.

#### 4.2.1 사전 검증 스크립트

빌드 전 대상 syllable이 매핑 내에 있는지 확인:
```python
needed = set('이삼사오육칠막제')
missing = [c for c in needed if c not in kr_map]
assert not missing, f"Missing syllables: {missing}"
```

### 4.3 OOR 감사 도구 (`tools/audit_oor.py`)

**입력**: 패치 NMS 파일 디렉토리 (`patch_main/`, `patch_patch/`).

**출력**: JSON 리포트 — 엔트리별 OOR 바이트 목록 + 통계.

**매핑 범위**:
- In-range: `0x89CD ~ 0x8EE0` (KR syllables, 960자)
- In-range: `0x20 ~ 0x7E` (ASCII 원문, `@c(...)` 등 컨트롤 코드)
- In-range: `0x8140 ~ 0x829F` (JP 구두점/기호 페이지 — 「」『』 등)
- OOR: 위 범위 밖의 2바이트 SJIS 시퀀스

**의사코드**:
```python
def scan_oor(path):
    from tools.nms_parser import parse_nms
    msgs = parse_nms(path)['messages']
    report = []
    for i, m in enumerate(msgs):
        b = m.encode('shift_jis', 'replace')
        oor_bytes = []
        j = 0
        while j < len(b):
            c = b[j]
            if (c >= 0x81 and c <= 0x9F) or c >= 0xE0:
                if j+1 < len(b):
                    code = (c<<8) | b[j+1]
                    if not is_in_range(code):
                        oor_bytes.append(f'{code:04X}')
                    j += 2; continue
            j += 1
        if oor_bytes:
            report.append({'idx': i, 'oor': sorted(set(oor_bytes)), 'text': m[:40]})
    return report

def is_in_range(code):
    # KR map
    if 0x89CD <= code <= 0x8EE0: return True
    # JP punctuation/symbols (verified preserved by auto_font_import)
    if 0x8140 <= code <= 0x829F: return True
    return False
```

**CLI**:
```bash
python tools/audit_oor.py patch_main/ patch_patch/ --output audit_report.json
python tools/audit_oor.py patch_main/_US/msgsheet/sysmsg.nms --summary
```

### 4.4 wii 교차검증

**목적**: `武蔵` 외에도 지명/고유명사 번역 오류가 있는지 일괄 탐지.

**방법**:
```python
# 1. jp_messages.json 의 sysmsg #399~470 지명 엔트리 추출
# 2. wii/messages/kr/sysmsg.json 의 같은 idx에서 korean 필드 조회 (정렬 다를 수 있으니 JP 원문 매칭)
# 3. 두 번역이 다르면 diff 리포트 생성
```

**출력**: `docs/03-analysis/place-name-wii-xcheck.md` (임시, 분석 후 삭제)

**자동 적용 금지**: 차이는 리포트만. 수동 검토 후 사용자가 확정 (번역 스타일 차이 가능).

### 4.5 「」 꺾쇠 렌더링 판정 (Phase B)

빌드·설치·Vita3K 실행 후 DLC 1화 첫 장면 헤더 스크린샷 확인:
- 정상 표시 → 종료
- 깨짐 → 별도 이슈로 전환 (이번 스코프 외), todo.md에 기록

SJIS 0x8175(「)/0x8176(」)은 `0x8140~0x829F` JP 기호 페이지이므로 이론상 원본 JP 폰트 페이지 유지됨 → 정상 렌더링 기대.

## 5. Data Flow

```
translations/jp_messages.json (수정)
          ↓
  python tools/build_patch.py
          ↓
  patch_main/*/sysmsg.nms (재생성)
  patch_patch/*/sysmsg.nms (재생성)
          ↓
  python tools/audit_oor.py (검사)
          ↓
  OK? → cpk_patch --append → install → Vita3K 재시작
          ↓
  DLC 1화 진입 (tools/genroku_test.py --from-game)
          ↓
  스크린샷 → 육안 확인 → SC-1~5 판정
```

## 6. Error Handling

| 상황 | 대응 |
|------|------|
| `이/삼/사/...` 중 매핑에 없는 syllable | 사전 검증에서 실패 → ASCII 로마숫자("II/III/IV")로 fallback 검토 |
| wii 교차검증에서 다수 차이 발견 | 이번 PR은 `武蔵` 만 확정 교체, 나머지는 리포트로 별도 검토 |
| 빌드 후 OOR 카운트 증가 | 즉시 롤백, 원인 분석 (ko 필드에 새로운 OOR syllable 혼입 가능성) |
| 「」 여전히 깨짐 | 별도 이슈로 등록(폰트 페이지 감사), 이 feature는 다른 SC 충족 시 완료 처리 |

## 7. Test Plan

### 7.1 정적 검증 (빌드 단계)
- **T1**: `grep -c "사무라이시" translations/jp_messages.json` == 0
- **T2**: 빌드 후 `python tools/audit_oor.py patch_main/ patch_patch/` — sysmsg 엔트리의 `0x8EF3~8EF8` OOR = 0
- **T3**: `sysmsg[65~70]`을 디코드 시 "이막", "삼막", ... "칠막"

### 7.2 동적 검증 (Vita3K)
- **T4**: Vita3K 시작 → 스토리 선택 화면 스크린샷 → Act 2~7 라벨 한글 정상 표시
- **T5**: DLC 1화 진입 (`python tools/genroku_test.py --from-game`) → 첫 장면 헤더 스크린샷 → "「무사시」 ..." 정상 표시
- **T6**: 기존 본편 대사 한 장면 스크린샷 (회귀 확인) — `사무라이시` 흔적 없음

### 7.3 회귀 방지
- **T7**: 커밋 전 `python tools/audit_oor.py --diff-against HEAD~1` — 이번 커밋이 OOR 총량을 증가시키지 않음

## 8. Implementation Guide

### 8.1 작업 순서

1. **M1 (데이터 수정)** — `translations/jp_messages.json`
   - "사무라이시" → "무사시" 일괄 치환
   - sysmsg #65~70 `ko` 필드를 "이막"~"칠막"으로 교체
   - 사전 검증: 필요 syllable 전부 매핑 내 존재 확인

2. **M2 (감사 도구)** — `tools/audit_oor.py`
   - `scan_oor()` 구현
   - CLI: 경로/파일 인자, `--summary`, `--output json`
   - 기준선 리포트 생성·커밋 (전체 프로젝트 OOR 베이스라인)

3. **M3 (wii 교차검증)** — 1회성 스크립트
   - `tools/_xcheck_wii.py` (임시) 실행
   - `docs/03-analysis/place-name-wii-xcheck.md` 생성
   - 차이 검토 후 추가 교체 대상 후보 기록 (이번 PR 반영 여부 판단)

4. **M4 (빌드·패치·설치)**
   - `python tools/build_patch.py`
   - `python tools/audit_oor.py patch_main/ patch_patch/ --summary` — OOR 감소 확인
   - `python tools/cpk_patch.py ... --append` × 2
   - CPK 복사

5. **M5 (동적 검증)**
   - Vita3K 종료 → 설치 → 실행
   - 스토리 선택 스크린샷 (T4)
   - DLC 1화 첫 장면 스크린샷 (T5)
   - 기존 장면 회귀 확인 (T6)
   - 실패 시 반복

6. **M6 (커밋·기록)**
   - 성공 시 단위별 커밋 (데이터 / 도구 / 패치 산출물)
   - `.claude/success.md`, `todo.md` 업데이트
   - (선택) 실패 원인 → `.claude/fail.md`

### 8.2 Session Guide

| Session | Modules | 예상 시간 | 독립성 |
|---------|---------|-----------|--------|
| **S1** | M1 + M4 + M5 | 15분 | 이것만으로 핵심 버그 해결 가능 |
| **S2** | M2 | 15분 | 감사 도구 — 독립 개발 가능 |
| **S3** | M3 + 추가 번역 정리 | 20분 | wii 교차검증 후속 — 발견 따라 확장 |

**권장**: S1 → S2 → S3 순차. S1 완료 후 게임이 동작하면 중간 커밋. S2/S3는 가치 있으나 블로킹 아님.

**/pdca do --scope 사용**:
```
/pdca do place-name-fix                 # 전체
/pdca do place-name-fix --scope S1      # 핵심 버그 수정만
/pdca do place-name-fix --scope S1,S2   # 핵심 + 감사 도구
```

## 9. Open Questions

- wii 교차검증에서 "사무라이시" 말고도 다수 오역이 발견되면 스코프 확장? → **기본: 리포트만, 사용자 승인 시 추가 반영.**
- Act 라벨 표기: "이막" vs "제이막" 중 선호? → **기본: "이막" (JP 원문 `二幕` 직역)**. 사용자 피드백에 따라 조정.

## 10. Out of Scope (재확인)

- DLC 대사 번역 추가
- 전체 OOR 메시지(~3,328건) 치환 — 별도 feature
- 폰트 매핑 확장, 폰트 아틀라스 재생성
- ASCII 숫자의 in-range 재매핑 (근본 해결)

---

*Generated by /pdca design on 2026-04-13 — Selected Option C (Pragmatic Hybrid)*
