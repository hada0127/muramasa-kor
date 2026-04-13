# Plan: Muramasa Rebirth 전체 한글화

- Feature: korean-localization
- Created: 2026-04-10
- Phase: Plan

## Executive Summary

| 관점 | 내용 |
|------|------|
| **Problem** | PS Vita Muramasa Rebirth (US) 영문판에 한국어 지원이 없어 한국어 사용자가 스토리와 시스템을 이해하기 어려움 |
| **Solution** | NMS 텍스트 파일의 SJIS 인코딩 활용 + Vita3K 텍스처 교체로 한글 폰트 렌더링, 전체 대사/시스템/아이템 한글화 |
| **기능 UX 효과** | 게임 시작부터 엔딩까지 모든 텍스트가 한글로 표시되어 플레이에 지장 없는 수준의 한글 로컬라이제이션 |
| **Core Value** | Vita3K 에뮬레이터 환경에서 Muramasa Rebirth를 완전히 한국어로 플레이 가능 |

## Context Anchor

| 항목 | 내용 |
|------|------|
| **WHY** | 한국어 사용자가 Muramasa Rebirth를 모국어로 즐길 수 있도록 |
| **WHO** | 한국어 사용자, Vita3K 에뮬레이터 플레이어 |
| **RISK** | 한글 699자 제한(SJIS 매핑), 폰트 텍스처 page 2 미확보, DLC 선택 화면 텍스트가 텍스처인지 NMS인지 확인 필요 |
| **SUCCESS** | DLC 선택 화면 + 본편 대사 + 시스템 메시지 + 아이템 설명 모두 한글 정상 출력 |
| **SCOPE** | 본편(키스케/모모히메) + DLC 4편 + 시스템/아이템 텍스트. 스태프롤 제외, 볼드 폰트 제외 |

---

## 1. 요구사항

### 1.1 텍스트 추출 및 번역 (전체 범위)

**목표**: 게임 내 모든 텍스트를 빠짐없이 추출하여 번역

| 카테고리 | NMS 파일 | 메시지 수 | 번역 상태 |
|----------|----------|-----------|-----------|
| **본편 대사** (scemsg) | NinPri/msgsheet/scemsg.nms | 1,116 | JP 추출 완료, KO 번역 완료 |
| **본편 시스템** (sysmsg) | NinPri/msgsheet/sysmsg.nms | 575 | JP 추출 필요 |
| **본편 아이템** (_itemdata) | NinPri/msgsheet/_itemdata.nms | ? | JP 추출 필요 |
| **본편 씬이름** (scename) | NinPri/msgsheet/scename.nms | ? | JP 추출 필요 |
| **DLC 대사** (scemsg) | NinPriPatch/msgsheet/scemsg.nms | ? | JP 추출 완료, KO 번역 완료 |
| **DLC 시스템** (sysmsg) | NinPriPatch/msgsheet/sysmsg.nms | 966 | JP 추출 완료, KO 번역 완료 |
| **DLC 아이템** (_itemdata) | NinPriPatch/msgsheet/_itemdata.nms | ? | JP 추출 완료, KO 번역 완료 |
| **DLC 씬이름** (scename) | NinPriPatch/msgsheet/scename.nms | ? | JP 추출 완료, KO 번역 완료 |
| **DLC 가사** (lyricmsg) | NinPriPatch/msgsheet/lyricmsg.nms | ? | JP 추출 완료, KO 번역 완료 |

**US 버전 (_US/) 처리**:
- 게임은 PCSE00240 (US 버전)이므로 `_US/msgsheet/` 경로 파일이 우선 적용됨
- `_US/` 파일과 기본 파일 모두 패치 필요 (jp_messages.json에 둘 다 포함)

**스태프롤**: 번역 대상에서 제외

### 1.2 폰트 시스템

**일반 텍스트 폰트**: 이롭게 바탕체 (IropkeBatangM.ttf) — 이미 보유
- 대사, 시스템 메시지, 아이템 설명 등 모든 인게임 텍스트에 사용
- Vita3K 텍스처 교체 방식 (PNG)
- DXT5/스위즐 불필요 — Vita3K가 자동 처리

**그래픽 텍스처 폰트**: 영남일보 구상시인체 — 다운로드 필요
- 메뉴 타이틀, UI 그래픽 등 텍스처에 직접 베이킹된 텍스트에 사용
- 다운로드: https://noonnu.cc/font_page/1771

**볼드 폰트**: 사용하지 않음
- 볼드 전용 텍스처(6706A53E1D94C16E) 교체 불필요
- 게임이 볼드 참조 시에도 일반 폰트로 표시되도록 처리

### 1.3 폰트 텍스처 현황

| 해시 | 용도 | 상태 | 작업 |
|------|------|------|------|
| `882CCAF6763B8B59` | 일반 page 0 (cells 0-1023) | 48자 처리 | 한글 매핑에 해당하는 셀만 교체 |
| `09498223CD6E047B` | 일반 page 1 (cells 1024-2047) | 508자 완료 | 완료 |
| `???` | 일반 page 2 (cells 2048-3071) | 미확보 | 게임 진행하여 텍스처 export 필요 |
| `6706A53E1D94C16E` | 볼드 폰트 | 사용 안 함 | 교체하지 않음 |

### 1.4 DLC 선택 화면 (최우선 작업)

게임 시작 시 나타나는 본편/DLC 선택 화면:
- **[267] 朧村正をプレイします** → "오보로 무라마사를 플레이합니다"
- **[268] 元禄怪奇譚をプレイします** → "겐로쿠 괴기담을 플레이합니다"

이 화면의 텍스트가 NMS sysmsg에 포함되어 있음을 확인. 
텍스처로 표시되는 타이틀/로고가 있을 수 있으므로 실제 게임 실행으로 확인 필요.

### 1.5 입력 조작 (Yes/No 다이얼로그)

- Yes/No 선택 시: **방향키**로 선택 → **X 키**(scancode 45)로 확인
- 마우스/터치 입력은 사용하지 않음
- 모든 게임 내 조작은 키보드 기반 (방향키 + X/Z)

## 2. 구현 단계 (우선순위순)

### Phase 1: 전체 텍스트 추출 및 번역 데이터 완성
1. 미추출 NMS 파일을 jp_messages.json에 추가 (NinPri sysmsg, _itemdata, scename + _US 전체)
2. 한글 매핑 테이블(kr_sjis_mapping.json) 검증 — 699자로 전체 번역 텍스트 커버 가능한지 확인
3. 부족한 한글 문자가 있으면 매핑 확장

### Phase 2: DLC 선택 화면 한글화 (최우선)
1. sysmsg 번역 (DLC 선택 관련 메시지)
2. 빌드 → 설치 → Vita3K 실행 → DLC 선택 화면 확인
3. 한글 메시지가 정상 출력될 때까지 반복 테스트
4. 텍스처 기반 텍스트가 있다면 영남일보 구상시인체로 교체

### Phase 3: 폰트 텍스처 완성
1. Page 0 한글 셀 교체 (이롭게 바탕체)
2. Page 2 텍스처 확보 (게임 진행하여 export)
3. Page 2 한글 셀 교체
4. 영남일보 구상시인체 다운로드 및 그래픽 텍스처용 도구 준비

### Phase 4: 본편 텍스트 한글화
1. NinPri scemsg (대사) — 이미 번역 완료, 빌드/테스트
2. NinPri sysmsg (시스템) — 번역 + 빌드/테스트
3. NinPri _itemdata (아이템) — 번역 + 빌드/테스트
4. 각 단계마다 게임 실행하여 표시 확인

### Phase 5: DLC 텍스트 한글화
1. NinPriPatch 전체 (이미 번역 완료된 파일들) — 빌드/테스트
2. 게임 내 DLC 4편 진입하여 텍스트 표시 확인

### Phase 6: 그래픽 텍스처 한글화
1. Vita3K export된 텍스처 중 텍스트 포함 텍스처 식별
2. 영남일보 구상시인체로 한글 텍스처 생성
3. import 폴더에 배치 및 테스트

### Phase 7: 통합 테스트
1. 게임 시작 → DLC 선택 → 본편 진입 → 대화 → 메뉴 → 아이템 확인
2. DLC 4편 각각 진입하여 텍스트 확인
3. 누락된 텍스트나 깨진 글자 수정

## 3. 성공 기준

| # | 기준 | 검증 방법 |
|---|------|-----------|
| SC-1 | DLC 선택 화면의 모든 텍스트가 한글로 정상 표시 | Vita3K 스크린샷 확인 |
| SC-2 | 본편 대사(scemsg)가 한글로 정상 표시 | 게임 내 대화 장면 확인 |
| SC-3 | 시스템 메시지(sysmsg)가 한글로 정상 표시 | 메뉴/설정/저장 등 확인 |
| SC-4 | 아이템 설명(_itemdata)이 한글로 정상 표시 | 인벤토리 확인 |
| SC-5 | DLC 4편 텍스트가 한글로 정상 표시 | DLC 진입하여 확인 |
| SC-6 | 글자 깨짐이나 누락 없음 | 전체 플레이 테스트 |
| SC-7 | 한글 699자 매핑으로 모든 번역 텍스트 커버 | 매핑 테이블 검증 |

## 4. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 한글 699자로 부족할 수 있음 | 일부 글자 표시 불가 | 매핑 확장 (SJIS 미사용 코드포인트 추가) |
| Page 2 텍스처 미확보 | 일부 한글 표시 불가 | 게임을 더 진행하여 export 유도 |
| 텍스처 베이킹된 UI 텍스트 | NMS 패치만으로 불충분 | 영남일보 구상시인체로 텍스처 교체 |
| 번역 품질 | 부자연스러운 한국어 | Wii 한글패치 번역 참고 |
| Vita3K 텍스처 해시 변동 | 업데이트 시 폰트 깨짐 | 해시 목록 문서화 |

## 5. 제약사항

- **Vita3K 전용**: 실기(PS Vita) 비호환, Vita3K 에뮬레이터에서만 동작
- **볼드 폰트 미사용**: 볼드 텍스처 교체하지 않음
- **스태프롤 제외**: 원본 유지
- **SJIS 인코딩 제약**: 한글은 미사용 SJIS 코드포인트에 매핑 (최대 ~955자)
- **영남일보 구상시인체**: 그래픽 텍스처 전용, 별도 다운로드 필요
- **이롭게 바탕체**: 대사/시스템 텍스트 전용, 이미 보유

## 6. 파일 구조

```
muramasa-kor/
├── translations/
│   ├── jp_messages.json        # 전체 번역 데이터 (추출+번역)
│   └── kr_sjis_mapping.json    # 한글↔SJIS 매핑 (699자)
├── tools/
│   ├── build_patch.py          # 번역 JSON → NMS 빌드
│   ├── cpk_patch.py            # CPK 패치 (append 방식)
│   ├── font_patch.py           # 한글 폰트 텍스처 생성
│   ├── nms_parser.py           # NMS 파서
│   └── vita3k_ctrl.py          # Vita3K 실행/종료
├── fonts/
│   ├── IropkeBatangM.ttf       # 이롭게 바탕체 (보유)
│   └── YNJBGusangSiinChe.ttf   # 영남일보 구상시인체 (다운로드 필요)
├── patch_main/                  # NinPri 패치 파일
├── patch_patch/                 # NinPriPatch 패치 파일
├── output/                      # 최종 CPK 출력
└── backup/                      # 원본 CPK 백업
```
