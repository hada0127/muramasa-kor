# Plan: Place Name & Story Select Rendering Fix

- Feature: `place-name-fix`
- Created: 2026-04-13
- Owner: 하다
- PDCA Phase: Plan

## Executive Summary

| 관점 | 내용 |
|------|------|
| **Problem** | DLC 진입 후 첫 주인공 시작 시 장면 전환 지명 헤더("「武蔵」 江戸城 大手門前" 등)가 이상한 한글로 출력됨. 스토리 선택 화면 오른쪽(Act 번호 라벨)도 깨짐. |
| **Solution** | (1) `武蔵` 오역 "사무라이시" → "무사시" 일괄 교체. (2) 스토리 선택 "제N막"의 SJIS 범위 밖 바이트(0x8EF3~0x8EF8)를 한글 매핑 내 바이트 또는 ASCII 숫자로 재작성. (3) Vita3K 재현 후 「」 꺾쇠 렌더링 확인. |
| **Function UX Effect** | 지명 헤더가 정상 한글(예: "「무사시」 에도성 오테문 앞")로 표시. 스토리 선택 Act 라벨이 올바른 "제2막~제7막"으로 표시. 장면 전환의 몰입감 회복. |
| **Core Value** | 한글 패치의 **기초 신뢰성** 확보 — 장면 전환 헤더는 게임 진행 내내 반복 노출되는 핵심 UI. 여기가 깨지면 전체 패치 품질이 저하되어 보임. |

## Context Anchor

| 항목 | 내용 |
|------|------|
| **WHY** | 한글 패치 품질의 기본선. 반복 노출되는 장면 헤더/스토리 선택이 깨지면 패치 전체가 불안정해 보임. |
| **WHO** | 하다(패처), 한글판 플레이어 (DLC 포함 본편 진행자). |
| **RISK** | 근본 원인이 SJIS 매핑 범위(960자) 초과 시 **전체 3,328개 메시지**에 파급. 범위 확장은 폰트 텍스처 재생성까지 유발할 수 있음. 이번 스코프는 장면 헤더/스토리 선택만, 시스템 이슈는 별도 과제. |
| **SUCCESS** | (1) 장면 전환 시 지명 헤더가 한글로 정상 표시, (2) 스토리 선택 Act 라벨이 "제2막~제7막"으로 표시, (3) 회귀 없음(기존 정상 대사 유지). |
| **SCOPE** | `sysmsg.nms` (patch_main, patch_patch, `_US` 포함) 내 지명 엔트리 및 Act 라벨 엔트리만. DLC 대사(scemsg) 번역은 out-of-scope. |

## 1. Problem Description

### 1.1 증상
- **증상 A**: DLC 첫 주인공(키스케) 진입 후 장면 전환 화면의 지명 헤더 `「무사시」 에도성 오테문 앞`가 이상한 한글로 렌더링.
- **증상 B**: 스토리 선택 화면 오른쪽(Act 번호 영역)이 이상한 글자로 깨짐.
- **참조**: JP 설정에서는 정상 출력 → 별도 번역 시스템이 아님, 같은 NMS 패치 파이프라인에서 생긴 손상.

### 1.2 정적 분석 (Plan 단계 조사 결과)

#### 원인 1 — `武蔵` 오역
- 위치: `patch_main/_US/msgsheet/sysmsg.nms`, `patch_main/msgsheet/sysmsg.nms` (+ patch_patch 동일)
- 원문/영문/현재 한글:
  - JP `武蔵` (Musashi) → 현재 **"사무라이시"** (5자, 잘못됨) → 정답 **"무사시"** (3자)
- 영향 엔트리: **9곳** (sysmsg #414, 422, 424, 447, 451, 452, 455, 457, 462)
- 엔트리 #451은 이중 오역: "사무라이시 사무라이시 가도" → "무사시 무사시 가도"

#### 원인 2 — Act 라벨 범위 밖 바이트
- 위치: `patch_main/_US/msgsheet/sysmsg.nms` #65~70 ("Act 2~Act 7")
- 원문 바이트 (사례):
  - `[65] Act 2` → `8d96 8ef3 8bb8` (제?막, ? = SJIS 0x8EF3)
  - `[66] Act 3` → `8d96 8ef4 8bb8` (?=0x8EF4)
  - ... `[70]` → `8d96 8ef8 8bb8` (0x8EF8)
- 현재 매핑(`translations/kr_sjis_mapping.json`)은 **0x89CD ~ 0x8EE0** (960자) 범위. 0x8EF3~0x8EF8은 **범위 밖** → 게임이 원본 일본어 폰트 글리프로 폴백 → 이상한 한자 표시.
- 추정: 번역자가 원래 숫자 "2, 3, 4..." 또는 한자 "이, 삼, 사..."를 쓰려 했으나 매핑 미등록 슬롯에 기록.

#### 원인 3 — 꺾쇠 「 」 렌더링 (미확인, 재현 필요)
- sysmsg #415~460에 `「지명」 부제` 패턴 사용.
- 원시 바이트의 「 (SJIS 0x8175) / 」 (SJIS 0x8176)은 우리 KR 매핑 범위(0x89CD~8EE0) **밖의 JP 기호 영역**.
- 이론상 JP 폰트 기호 페이지가 원본 그대로 남아있으면 정상 렌더링되어야 함. 그러나 `auto_font_import.py`/`hd_font_import.py`가 폰트 텍스처 오버라이드 시 기호 페이지도 클리어되었을 가능성.
- **재현 테스트 필요**: Vita3K에서 현재 상태로 실제 렌더링 캡처 → 「」가 어떻게 나오는지 확인 후 판단.

#### 시스템 이슈 (Out-of-Scope, Risk로 기록)
- 전체 patch_* NMS 스캔 결과 **3,328개 메시지**에서 0x8EEF, 0x8EED, 0x8F43 등 범위 밖 바이트 발견.
- 이는 번역자가 960자보다 더 많은 한글 syllable을 쓰고 매핑 확장 없이 초과분을 outside 슬롯에 기록한 구조적 문제.
- 이번 스코프에서는 다루지 않되, **별도 기능(e.g. `oor-encoding-fix`)으로 후속 추진**.

## 2. Requirements

### 2.1 기능 요구사항
- **FR-1**: sysmsg.nms (`patch_main`, `patch_patch` × `(루트, _US)` = 4개 파일)의 모든 "사무라이시" 문자열을 "무사시"로 교체.
- **FR-2**: sysmsg.nms 엔트리 #65~70의 Act 번호 바이트(0x8EF3~0x8EF8)를 유효 범위 내 표현(한글 숫자 "이"~"일곱" 또는 ASCII "2"~"7")으로 재작성.
- **FR-3**: Vita3K에서 DLC 첫 주인공 시나리오 진입 → 첫 장면 헤더 스크린샷으로 결과 검증.
- **FR-4**: 스토리 선택 화면 스크린샷으로 Act 라벨 정상 표시 검증.

### 2.2 비기능 요구사항
- **NFR-1**: 기존 정상 엔트리(e.g. "서막", "야마시로") 회귀 없음.
- **NFR-2**: 빌드·설치·게임 실행 자동화 (CLAUDE.md 규칙 준수).
- **NFR-3**: 수정 단위마다 git commit.

### 2.3 제약
- 한글 매핑 범위는 **건드리지 않음** (확장 시 폰트 아틀라스 재생성 필요 → 큰 변경).
- `wii/messages/kr/*.json` 참고 허용, 직접 적용은 Vita 맥락에 맞게 조정.

## 3. Success Criteria

| # | Criteria | Verification |
|---|---|---|
| SC-1 | sysmsg 내 "사무라이시" 0건 | `grep` / 디코드 스캔 스크립트 |
| SC-2 | sysmsg 내 바이트 0x8EF3~0x8EF8 0건 | 바이트 스캔 스크립트 |
| SC-3 | 장면 헤더 스크린샷에 "「무사시」 에도성 ..." 정상 표시 | mss 캡처 |
| SC-4 | 스토리 선택 화면에 "제2막, 제3막..." 정상 표시 | mss 캡처 |
| SC-5 | 기존 DLC 1화 진입 자동화 (`genroku_test.py`) 회귀 통과 | 자동 실행 |

## 4. Approach (High-Level)

### Phase A — 정적 수정 (Code-only)
1. `translations/jp_messages.json` 또는 번역 소스 JSON에서 "사무라이시" → "무사시" 교체
2. Act 라벨 엔트리 번역 수정: `제2막` 형태를 매핑 내 한글로 재입력
3. `python tools/build_patch.py` 로 NMS 재빌드
4. 빌드 후 diff 확인: OOR 바이트 카운트가 0인지 검증

### Phase B — 동적 검증 (Vita3K 실행)
1. Vita3K 종료 → CPK 패치 → 설치 → 재실행
2. 스토리 선택 화면 진입 → 스크린샷
3. 겐로쿠 괴기담 1화 진입 → 첫 장면 헤더 도달 → 스크린샷
4. 결과 비교: 예상 문자열 vs 실제 렌더링

### Phase C — 「」 꺾쇠 판정
- Phase B 스크린샷에서 「」 렌더링 확인.
- 정상 표시 → 종료.
- 깨짐 → Design 단계에서 폰트 페이지 조사 (auto_font_import가 0x8175/0x8176 페이지를 건드렸는지)

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| "사무라이시" 외에도 비슷한 지명 오역 존재 | 수정 누락 | SC-3 스크린샷 후 JP vs KR 전수 비교 (최소 sysmsg 399~470 전체) |
| OOR 바이트가 Act 라벨 외에도 사용 중 (3,328건) | 대사 전반 깨짐 | 이번 PR은 sysmsg만, 대사 OOR은 별도 feature로 분리 |
| 「」 꺾쇠 폰트 페이지가 오버라이드되어 있음 | 헤더 테두리 깨짐 지속 | Design 단계에서 `auto_font_import.py` / `hd_font_import.py`의 커버리지 감사 후 수정 |
| 매핑 확장 유혹 | 폰트 아틀라스 재생성 유발 → 큰 회귀 | 이번 스코프에서는 확장 금지. 후속 과제로. |
| 빌드 후 다른 엔트리가 OOR로 쓰이는 부작용 | 회귀 | 빌드 산출물 diff (이전 vs 신규) 바이트 수준 확인 |

## 6. Out of Scope

- DLC 대사(scemsg ~1062개) 번역 추가
- 전체 OOR 바이트 제거 (~3,328개 메시지) — 별도 feature로 추진
- 폰트 매핑 범위 확장 (0x8EE0 초과 영역)
- 텍스처 기반 지명 이미지(`1823D39C0279886B`) 한글화 — 별개 Phase 4 과제

## 7. Dependencies

- `tools/build_patch.py` — NMS 재빌드
- `tools/cpk_patch.py` — CPK append 패치
- `tools/vita3k_ctrl.py` — 실행/종료
- `tools/genroku_test.py` — DLC 1화 자동 진입
- `translations/kr_sjis_mapping.json` — 읽기만 (수정 금지)
- `wii/messages/kr/*.json` — 참고 (사무라이시 vs 무사시 교차검증)

## 8. Next Phase

다음: `/pdca design place-name-fix` — 3가지 아키텍처 옵션 제시 후 승인

---

*Generated by /pdca plan on 2026-04-13*
