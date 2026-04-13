# Plan: 대사(scemsg) 폰트 미출력 버그 수정

> Feature: `scemsg-font-fix`
> Created: 2026-04-11
> Status: Draft

## Executive Summary

| 관점 | 설명 |
|------|------|
| **Problem** | 대사(scemsg) 장면에서 한글이 빈 칸/투명으로 출력됨. 시스템 메시지(sysmsg)는 정상 |
| **Solution** | 대사 장면 전용 폰트 텍스처 해시를 감지하여 한글 import 생성 |
| **기능/UX 효과** | 게임 대사가 한글로 표시되어 스토리를 한국어로 플레이 가능 |
| **Core Value** | 한글 패치의 핵심 기능 완성 (전체 1,152개 대사 메시지 출력) |

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | 대사가 투명 글자로 출력되어 게임 스토리를 읽을 수 없음 |
| **WHO** | 한국어 유저 (Muramasa Rebirth 한글 패치 사용자) |
| **RISK** | sysmsg(시스템 메시지) 정상 동작에 영향을 주면 안 됨 |
| **SUCCESS** | 겐로쿠 괴기담 에피소드 1 대사가 한글로 렌더링됨 |
| **SCOPE** | auto_font_import.py 개선 + 대사 장면 폰트 해시 감지/import |

---

## 1. 문제 분석

### 1.1 현상
- **sysmsg** (시스템 메시지, 메뉴/전투/튜토리얼): 한글 정상 출력 ✅
- **scemsg** (대사, 캐릭터 대화): 빈 칸/투명 글자로 출력 ❌
- NMS 파일 인코딩 자체는 정상 (scemsg 1,116개 + 36개 한글 인코딩 확인 완료)

### 1.2 원인 분석

게임의 폰트 렌더링 파이프라인:
```
NMS 파일 (SJIS 인코딩 한글) → 게임 엔진 → 폰트 텍스처 참조 → 화면 렌더링
```

- SJIS 코드 → 셀 번호 변환 (cell = (b1-0x81)*188 + b2_offset)
- 셀 번호 → 폰트 텍스처의 32px 그리드 위치에서 글리프 로드
- **한글 매핑 범위 (셀 1644~2608)는 KANJI 페이지에 위치**

현재 import된 폰트 해시 3개:
| 해시 | 용도 | 출처 |
|------|------|------|
| `6706A53E1D94C16E` | 볼드/아웃라인 폰트 | 메뉴/시스템 |
| `8665CE082D339B33` | 일반 폰트 | 메뉴/시스템 |
| `E690E190AA5C798F` | 추가 폰트 페이지 | 메뉴/시스템 |

**가설**: 대사 장면은 별도의 폰트 텍스처(다른 해시)를 로드함.
- Vita3K는 세션마다 텍스처 해시가 바뀔 수 있음
- 대사 장면 진입 시 새로운 폰트 텍스처가 export 폴더에 나타날 가능성
- 현재 auto_font_import.py는 타이틀/메뉴 시점의 export만으로 감지

### 1.3 검증 방법
1. 현재 export 폴더의 폰트 텍스처 해시 기록 (baseline)
2. 대사 장면 진입 (genroku_test.py)
3. export 폴더에 새로 추가된 텍스처 확인
4. 새 텍스처 중 폰트 패턴(`is_font_grid`) 매칭되는 것 식별
5. 해당 해시에 한글 import 생성 → Vita3K 재시작 → 대사 출력 확인

## 2. 요구사항

### 2.1 기능 요구사항
| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| FR-1 | 대사 장면 폰트 텍스처 해시 감지 | Critical |
| FR-2 | 감지된 해시에 한글 import 텍스처 자동 생성 | Critical |
| FR-3 | genroku_test.py로 대사 한글 출력 검증 | Critical |
| FR-4 | 기존 sysmsg 폰트 import에 영향 없음 | Critical |

### 2.2 비기능 요구사항
| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| NFR-1 | auto_font_import.py의 기존 로직 보존 (sysmsg 안전) | Critical |
| NFR-2 | HD 팩 텍스처와 해시 충돌 방지 유지 | High |
| NFR-3 | 세션마다 바뀌는 해시에 대응 가능한 구조 | High |

### 2.3 제약사항
- **절대 금지**: sysmsg 관련 코드/파일 수정
- **절대 금지**: 기존 3개 폰트 해시 import 로직 변경
- **절대 금지**: import 폴더 전체 삭제 (HD 팩 손실)
- auto_font_import.py 수정 시 기존 동작은 100% 보존해야 함

## 3. 해결 전략

### Phase A: 조사 (Investigation)
1. Vita3K 실행 → 게임 진입 (타이틀 화면)
2. 현재 export 폴더 폰트 해시 목록 기록 (baseline)
3. genroku_test.py로 대사 장면 진입
4. export 폴더에 새로 나타난 텍스처 확인
5. 새 텍스처 중 `is_font_grid()` 패턴 매칭 → 대사 전용 폰트 해시 식별

### Phase B: 수정 (Fix)
**시나리오 1 — 새 폰트 해시 발견됨:**
- auto_font_import.py가 이미 해당 해시를 감지할 수 있는지 확인
- 감지 안 되면: 감지 로직 개선 (is_font_grid 조건 조정 등)
- 한글 import 생성 → Vita3K 재시작 → 대사 출력 확인

**시나리오 2 — 새 해시가 아니라 기존 해시의 다른 페이지:**
- 동일 해시지만 다른 KANJI 페이지에 대사 글리프가 있는 경우
- 페이지 오프셋 조정 필요 여부 확인

**시나리오 3 — export에 새 텍스처가 안 나옴:**
- Vita3K export 설정 확인
- 대사 장면에서 실제로 다른 텍스처를 사용하는지 다른 방법으로 확인
- export 폴더 비우고 대사 장면에서만 export 유도

### Phase C: 검증 (Verification)
1. 한글 import 적용 후 Vita3K 재시작
2. genroku_test.py로 대사 장면 자동 진입
3. 스크린샷으로 한글 대사 출력 확인
4. sysmsg도 여전히 정상인지 확인 (회귀 테스트)

## 4. 성공 기준

| ID | 기준 | 검증 방법 |
|----|------|-----------|
| SC-1 | 겐로쿠 괴기담 에피소드 1 대사가 한글로 표시됨 | genroku_test.py 스크린샷 |
| SC-2 | 시스템 메시지(sysmsg)가 여전히 한글로 정상 출력됨 | 메뉴/튜토리얼 스크린샷 |
| SC-3 | auto_font_import.py가 대사 폰트도 자동 감지/import | 스크립트 실행 로그 |
| SC-4 | sysmsg 관련 코드 변경 0건 | git diff 확인 |

## 5. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 대사 폰트 해시가 세션마다 변경 | auto_font_import.py를 매번 실행해야 함 | 이미 기존 동작이 이렇게 설계됨 (허용 가능) |
| is_font_grid 조건 완화 시 비폰트 텍스처 오감지 | HD 팩/게임 텍스처 깨짐 | channel_spread, ASCII page 필터 유지 |
| 대사 폰트가 다른 셀 매핑을 사용 | 한글 위치 어긋남 | 대사 장면 스크린샷으로 글리프 위치 검증 |

## 6. 수정 대상 파일

| 파일 | 변경 유형 | sysmsg 영향 |
|------|-----------|-------------|
| `tools/auto_font_import.py` | 수정 (대사 폰트 감지 개선) | 없음 (추가 감지만) |
| `tools/genroku_test.py` | 수정 없음 (테스트 도구로만 사용) | 없음 |
| sysmsg 관련 모든 파일 | **수정 금지** | - |
| `patch_main/msgsheet/sysmsg.nms` | **수정 금지** | - |
| `patch_patch/msgsheet/sysmsg.nms` | **수정 금지** | - |

## 7. 작업 순서

```
1. [조사] export 폴더 baseline 기록
2. [조사] 게임 실행 → 대사 장면 진입 → 새 export 텍스처 확인
3. [분석] 새 텍스처 폰트 패턴 분석
4. [수정] auto_font_import.py 개선 (필요 시)
5. [적용] 대사 폰트 한글 import 생성
6. [검증] Vita3K 재시작 → 대사 한글 출력 확인
7. [검증] sysmsg 회귀 테스트
8. [완료] git commit
```
