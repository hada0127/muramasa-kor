# Plan — Font Mapping Repair

- Feature: `font-mapping-repair`
- Author: Claude (자율 실행 모드)
- Date: 2026-04-14
- Status: Plan 단계 (구현·검증은 이후 단계)

## Executive Summary

| Problem | Solution | Function / UX Effect | Core Value |
|---|---|---|---|
| 어빌리티 화면 Skill/Effect 열, 식당 메뉴, 대장간/장비 창의 칼 이름, 대사 중 "등" 치환 등 **여러 UI 화면에서 한글이 엉뚱한 글자로 표시**됨 | 각 깨짐 영역의 실제 렌더 경로(NMS 엔트리·SJIS 바이트·폰트 아틀라스 위치)를 **바이트 단위 추적**으로 식별 후, 인코더·오버레이·번역 데이터를 부위별 최소 수정 | 유저가 가장 자주 보는 메인 메뉴 3종(어빌리티·장비·대장간)과 식사/대사에서 텍스트가 **제대로 된 한글**로 표시됨 | 지금까지 쌓아둔 한글화 엔드-투-엔드 파이프라인의 **잔여 결함을 제거**해 게임 전반의 가독성 확보 |

## Context Anchor

| Axis | Value |
|---|---|
| WHY | 기존 패치는 대사·시스템 메시지는 정상 렌더하지만, 어빌리티/식당/대장간 UI와 일부 대사 구간에서 비(非)한글 글리프가 섞여 "번역이 안 된 것처럼 보이는" 치명적 UX 문제가 남아 있음 |
| WHO | 모모히메(백희) 스토리를 진행하는 한국인 플레이어. 특히 Ability 화면은 세이브 로드 직후 곧바로 접근 가능한 핵심 정보창 |
| RISK | 폰트 오버레이/인코더를 잘못 건드리면 지금 정상인 화면도 깨질 수 있음 → 수정 전후 **스크린샷 기반 회귀 검증** 필수 |
| SUCCESS | Ability/Equip/Forge/Soba Shop/대사 총 5개 대표 화면에서 스크린샷 비교 시, **사용자 리포트된 깨짐이 완전히 사라지고** 기존 정상 영역에 회귀 없음 |
| SCOPE | `tools/build_patch.py`, `tools/auto_font_import.py`, `tools/hd_font_import.py`, `translations/*.json` 선에서 해결. eboot.bin 바이너리 패치는 범위 외 |

## 1. 배경 및 문제 정의

사용자가 2026-04-14 스크린샷(`C:/Users/taro1/OneDrive/Pictures/스크린샷/`)으로 다음 5종 깨짐 사례를 보고:

1. **Ability 화면 Skill/Effect 열 완전 깨짐** — 하세베쿠니시게 / 무명도[히스이] / [모란]무라마사 3개 행 모두 비정상 한글 글리프 (예: `닷맽않딸돕맒 담햝맣`, `묘혔떏뗄맶 땀맒`)
2. **식당(소바 가게) 메뉴 — 일본어 한자 그대로 노출** (`栗黃緩河苦 蝦軽減渋` 형태)
3. **장비 화면 Before 열 — `묘혔떏뗄맶 땀` 깨짐**
4. **Forge 화면 검 이름 — `뜬대태도롫뗊뗄뗒뗒뗒뗒뗒뗒뗒` (정상 접두 + 스팸 꼬리)**
5. **대사 일부에 `등`, `들`, `뒤` 등 런타임 숫자 치환 잔재**

사용자 지시: **개입 없이** 스크린샷·자동화·빌드·Vita3K 실행을 전부 직접 수행해 테스트/수정할 것.

## 2. 범위 (In-Scope / Out-of-Scope)

### In-Scope
- 어빌리티/장비/대장간/식당 메뉴 스킬·아이템·검 이름 렌더 수정
- 대사 중 런타임 숫자 치환으로 남은 `등/들/뒤` 등 해결
- 폰트 아틀라스 오버레이(`auto_font_import.py`, `hd_font_import.py`)의 누락 셀 보완
- `build_patch.py`의 인코딩 경로 보완 (OOR 바이트, 매칭 모드, 미번역 항목 식별)

### Out-of-Scope
- eboot.bin 바이너리 수정
- HD 텍스처 팩 자체 교체
- 새로운 UI 텍스처 한글화(별도 Phase 4)
- DLC 대사 전면 번역(별도 feature)

## 3. 조사 결과 (2026-04-14 현재)

### 3.1 어빌리티 Skill/Effect 열의 데이터 소스 — **ROOT CAUSE 확정 (2026-04-14)**

**US와 EU의 `_itemdata.nms` 인덱스 구조가 완전히 다름.** 빌드 파이프라인이 이를 무시하고 EU 기반 `_itemdata` 번역 테이블로 US 파일을 index-mode 패치해 **엉뚱한 엔트리에 한글을 덮어쓰고 있음**.

- `extracted/NinPriPatch/msgsheet/_itemdata.nms` (EU/JP): 3565 entries — items+descriptions+accessories+skill names 섞임. Entry 608 = `金剛の腕輪` (Kongou bracelet).
- `extracted/NinPriPatch/_US/msgsheet/_itemdata.nms` (US): 1177 entries — items 0-593 + separator 594 + **컴팩트 스킬명 리스트 595-1176**. Entry 608 = `Divine Moon I` (skill name).
- `translations/jp_messages.json` `_itemdata.messages[608].ko` = `금강 팔찌` (bracelet name).
- `tools/build_patch.py`가 US 파일에 `_itemdata` 번역을 **인덱스 기준**으로 적용 → `US[608] = Divine Moon I` 자리에 `'금강 팔찌'`가 주입됨.
- 결과: 어빌리티 화면에서 2행 Skill 열이 `'금강 팔찌'`로 표시 (실제 Divine Moon I 자리). 1/3행의 엉뚱한 Korean/JP mix은 `_itemdata`의 긴 설명·특수 문자·미매핑 syllable이 짧은 SKILL slot에 덮어써지면서 생긴 바이트 조각.

**검증된 사실**
- `temp/cpk_verify` 비교: 설치된 `NinPriPatch.cpk`가 `patch_patch/_US/msgsheet/_itemdata.nms`와 MD5 일치 → 빌드 결과가 그대로 게임으로 들어감.
- US `_itemdata.nms` 엔트리 600-619 원문 전부 확인 완료 (‘Gale II’, ‘Divine Moon I’, ‘Meteor I’ 등 스킬명).
- JP `_itemdata_main` (NinPri 베이스, 878 entries)도 스킬 테이블이지만 US와 8칸 시프트로 **1:1 매핑 불가**.

**Fix Candidates**
- **C-1 (권장)** — US `_itemdata.nms` 패치 SKIP: 원본 영어 그대로 설치. 어빌리티/장비 화면이 영문 스킬명으로 나오지만 깨짐·덮어쓰기 없음. 즉시 실행 가능, 회귀 위험 0.
- **C-2** — US 영문→한글 수동 매핑 사전 구축: US 원본 1177 엔트리 전수 파싱 → `_itemdata_main` 내 Korean 매칭 → 새 번역 파일. 품질 최고지만 공수 큼.
- **C-3** — `_itemdata_main` content-match 적용: US와 _itemdata_main의 구조가 유사하므로 EN↔JP 매핑을 자동 추정 (8칸 시프트 감안). 중간 품질.

### 3.2 인코딩 경로
- `build_patch.py`의 `ASCII_SJIS_MAP`은 `pos=960+`에 ASCII 글리프를 배치하고, `hd_font_import.py`의 오버레이 루프도 동일 규칙으로 `:` `(` `)` `0-9` 등을 그리고 있어 기본 ASCII는 정상.
- `FULLWIDTH_NORMALIZE`가 전각(`１` `：` `（` 등)을 ASCII로 정규화해 `pos=960+`로 라우팅. 이 경로는 대부분 정상.
- 문제 사례 중 `\u3000` (전각 공백)이 ASCII 공백으로 치환되면서, 게임이 space를 반폭 렌더하는 현재 룰과 **원래 의도한 전각 공간**이 충돌할 수 있음 → 숫자 `:` 사이 간격 이상, "1 8"처럼 벌어지는 증상 확인.

### 3.3 폰트 아틀라스 커버리지
- 한글 글리프는 `kr_sjis_mapping.json`의 960자만 아틀라스에 그림. 맵에 없는 syllable(`맽/맒/맣/돕/햝/뗄/뗒/롫` 등)은 **오버레이되지 않은 원본 HD 팩 JP 글리프**가 노출됨.
- 어빌리티 스킬 칸에 보이는 자형이 "한글 같아 보이는 JP 한자"인지, "OOR 바이트가 cell≥1024 영역(오버레이 사각 지대)에서 렌더된 결과"인지 Design 단계에서 셀-캡처 테스트로 분리 필요.

### 3.4 Forge / Equip 검 이름 꼬리 깨짐
- `뜬대태도롫뗊뗄뗒뗒뗒뗒...` — 앞부분 `[대태도]`는 카테고리 라벨, 뒤의 반복 글리프는 **null 종료자 누락 또는 길이 초과 → 다음 엔트리 바이트 침범** 가능성.
- `scename` 또는 `_itemdata`의 칼 이름 슬롯 길이 제약을 넘어서 인코딩된 경우로 의심.

### 3.5 대사 런타임 치환 잔재
- 이전 `e1480af`·`4149a51` 커밋으로 cells 240-249, 192+`:-./` 오버레이 도입 — 대부분 해결.
- 남은 "등"은 ASCII `0x3E` (>) 또는 `0x3D` (=) 근처 치환. 대사 내 제어코드 잔여로 추정.

## 4. 요구사항

- [FR-1] Ability 화면에서 현재 장착한 3개 칼 각각의 Skill/Effect가 **사용자 번역에 맞는 한글**로 표시.
- [FR-2] 소바(식당) 메뉴 리스트의 한자가 한글 번역(`자루소바`, `청어소바`, `튀김소바`, `유부우동`)으로 표시.
- [FR-3] Forge/Equip 창에서 칼 이름이 `뜬…뗒` 같은 꼬리 없이 깨끗하게 표시.
- [FR-4] 스토리 대사 지문에 `등/들/뒤` 런타임 치환 잔재 없음 (세이브 시간 "1시간 45분" 정상 렌더).
- [NFR-1] 기존 정상 영역(타이틀·DLC·보스 등) 회귀 없음.
- [NFR-2] 전 과정 자동화 — 빌드·설치·Vita3K 실행·ImGui/LiveArea 조작·스크린샷까지 사용자 개입 불필요.

## 5. 접근 전략 (3안)

| Option | 핵심 | 장점 | 리스크 |
|---|---|---|---|
| A. 데이터만 수정 | translations/jp_messages.json 내 Korean 필드 전수 조정 (OOR 유발 문자 제거, 길이 제한 준수) | 도구 변경 없음, 회귀 최소 | 근본 원인(게임의 parse 규칙)을 모르면 반복 노력 |
| B. 폰트 커버리지 확장 | 960자 → 2350자로 오버레이 확대, 모든 Korean syllable에 글리프 부여 | 미매핑 문자 출현 시 "한글답게" 표시 | 아틀라스 크기·렌더 비용 증가, 잘못된 문자도 한글로 보여 "자연스러운 오류" 유발 |
| C. 표적 수술 (권장) | 각 증상별 root cause 식별 → 최소 수정: (1) 스킬 이름 테이블을 US NMS에 직접 주입, (2) 길이 초과 엔트리 트리밍, (3) 대사 제어코드 재확인 | 수정 범위가 정확, 검증 용이 | 조사 단계가 선행됨 — 이번 Plan의 핵심 |

→ **C 권장**. Design 단계에서 세 개 단위 수술을 Module 1/2/3으로 쪼개 Session Guide화.

## 6. Success Criteria

- [SC-1] `screenshots/before_*.png` vs `screenshots/after_*.png` 5종 비교에서 깨짐 0건 (시각 확인)
- [SC-2] `tools/audit_oor.py --summary`로 패치 NMS의 OOR 바이트가 기준치 이하
- [SC-3] Vita3K 자동화 스크립트가 Ability/Equip/Forge/Soba/대사까지 중단 없이 도달 후 캡처
- [SC-4] `git diff`가 translations + tools 범위 내에서만 변경, eboot.bin 수정 없음

## 7. 리스크 & 대응

- **폰트 오버레이 변경 후 기존 화면 회귀** → 수정 전 폰트 아틀라스 PNG 백업 → 후 스크린샷 회귀 비교.
- **Vita3K 자동화 중 창 포커스 상실/LiveArea 팝업 변동** → `vita3k_ctrl.py status` 주기 확인 + 좌표 탐색을 절대치 대신 이미지 기반으로.
- **CPK append 반복으로 파일 비대화** → 매 빌드마다 `backup/` 에서 복사해 fresh input으로 패치.

## 8. 의존성

- 정상 동작 도구: `build_patch.py`, `cpk_patch.py`, `auto_font_import.py`, `hd_font_import.py`, `vita3k_ctrl.py`, `capture_scene.py`
- 참고 자료: `wii/messages/kr/_itemdata.json` (Wii 한글 번역 레퍼런스), `docs/03-analysis/oor_baseline.json`
- 실행 환경: Vita3K 0.2.1 3949, 현재 모모히메 세이브 로드된 상태

## 9. 다음 단계

1. `/pdca design font-mapping-repair` — Architecture 3안 중 Option C 기반 모듈 분할 설계
2. 모듈별 `/pdca do font-mapping-repair --scope module-N` 점진 구현
3. `/pdca analyze font-mapping-repair` — gap-detector + Vita3K 런타임 회귀
4. `/pdca report font-mapping-repair`

---

_이 문서는 Claude 자동 실행 중 즉시 갱신될 수 있음. 최종 결과는 `docs/04-report/font-mapping-repair.report.md`에 기록 예정._
