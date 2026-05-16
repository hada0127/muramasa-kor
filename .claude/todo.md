# TODO - 진행 예정 작업

## 2026-05-17 — 지명 텍스처 ↔ 시스템 메시지 표기 일관성 (place-name-consistency)

### 사용자 보고
"시스템 메세지에서는 쇼조지(證城寺) 지명 설명인데 지명 텍스처는 슨푸로 나옴" 등 텍스처/메시지 표기 불일치 다발.

### 외부 AI 협의 결과 (codex; gemini 응답 없음)
- A) 텍스처/매핑을 권위로 메시지를 통일
- B) texture_localize.py로 자동 재생성. 매핑 JSON을 정답으로 사용
- C) 우선순위: 매핑 확정 → 텍스처 재생성 → 메시지 일괄 치환

### 통일 표기 (확정)
| 일본어 | 통일 한글 | 비고 |
|---|---|---|
| 遠江 | 도토미 | 매핑 '토토미'→'도토미' 수정. 표준 한글 표기 |
| 近江 | 오미 | 매핑 유지. 메시지 '오우미'(4건)→'오미' |
| 駿河 | 스루가 | 유지 |
| 駿府 | 슨푸 | 유지 (별개 도시명) |
| 高天原 | 다카마가하라 | 메시지 '타카마가하라'→'다카마가하라' |
| 善祷寺 | 젠토지 | 메시지 '선도사'→'젠토지' |
| 暗夜城 | 암야성 | 메시지 '안야성'→'암야성' |
| 馬蕗城 | 마후키성 | 메시지 '바후쿠 성'→'마후키성' |
| 鳴神城 | 나루카미성 | 메시지 '나루카미 성'→'나루카미성' |
| 金剛山 | 곤고산 | 메시지 '콘고산'→'곤고산' |
| 東海道 | 도카이도 | 메시지 '토카이도'/'동해도'→'도카이도' |
| 大根 | 다이콘 | 메시지 '무'(채소 오역) 13건→'다이콘' (지명) |
| 證城寺/証城寺 | 쇼조지 | 유지 |
| 武蔵 | 무사시 | 유지. scemsg#1105 '伊勢桑名'→'쿠와나' 한정 |
| 鏡見家/鏡見 | 카가미케/카가미 | 메시지 '카미가'→'카가미가' |
| 秋葉山 | 아키바산 | scemsg#104 '치바산'→'아키바산' |
| 駿府 | 슨푸 | scemsg#707 '사가미'→'슨푸' (오역) |

### 작업 항목
- [x] 외부 AI 협의 + 통일안 결정
- [x] 매핑 JSON: 遠江 '토토미'→'도토미' 수정
- [ ] 메시지 JSON: 위 통일 표기로 일괄 치환
- [ ] 텍스처 PNG 검증: 매핑과 실제 PNG 한글 비교
- [ ] 손상된 텍스처 PNG 재생성 (스푸/교조구 등)
- [ ] NMS 재빌드 + CPK 패치 + macOS Vita3K 설치
- [ ] success.md 기록 + commit

## v0.7.1 이슈 후속 (2026-05-15)

### 이슈 #3 (v0.7.1) 가마꾼 돈/문 불일치
- [x] 화폐 단위 전수조사 (텍스트/텍스처) — temp/currency_audit/summary.md
- [x] A안 결정 (냥/문 + 백분율 %)
- [x] sysmsg/sysmsg_main "돈을 지불" → "문을 지불" (2건)
- [x] _itemdata 백분율 "푼" → "%" (8건 + 조사 자연화 4건)
- [x] NMS 재빌드 + CPK 패치 + macOS Vita3K 설치
- [ ] 인-게임 검증 (사용자) — 가마꾼 시스템 메시지 + 효과 % 표시

### 이슈 #2 (v0.7.0) 미해결 항목 — 별도 작업
- [x] DLC 1 바케네코편 전투 결과창 "시간" 표시 깨짐 (issue #2 항목 3) — 2026-05-16 "봐" 재배치 + cell 454 콜론 오버레이로 해결
- [x] DLC 1 옵션 화면 하단 "연습" 용어 불일치 (issue #2 항목 4) — 2026-05-16 DF66CADDABE022E3.kra layer14 "연 습" → "단 련" 수정 완료
- [x] DLC 1 장비란 깨진 글자 (issue #2 항목 5) — 2026-05-16 영문판 검증 후 "Form:%s" hardcoded 확정. 딱/량/럴/랴 SJIS 재배치 + F/o/r/m 영문 overlay + 콜론 위치 조정 (x=9)으로 해결. 사용자 검증 "딱 좋다"
- [ ] X/O 버튼 텍스처 동적 처리 (issue #2 항목 2, 난항 보고됨)

## 전체 한글화 공정

### Phase 1: 전체 텍스트 추출 및 번역 ✅ 완료
- [x] NinPri + NinPriPatch 전체 NMS 추출/번역 (955자 매핑)
- [x] "몽롱 무라마사" → "오보로 무라마사" 교체

### Phase 2: DLC 선택 화면 + 시스템 메시지 한글화 ✅ 완료
- [x] DLC 선택 "오보로 무라마사를 플레이합니다" 정상 출력
- [x] 튜토리얼/전투 시스템 메시지 한글 정상 출력
- [x] Vita3K texture import 파이프라인 확립
- [x] KANJI 페이지만 import (ASCII 페이지 건드리면 공백 깨짐)

### Phase 3.6: 지명/Act 라벨 렌더링 수정 (place-name-fix) — 진행 중
- [x] 정적 분석: `武蔵` → "사무라이시"(5자) 오역, sysmsg 9곳 영향
- [x] 정적 분석: Act #65~70 바이트 0x8EF3~0x8EF8 매핑 범위 밖 → 일본어 폰트 폴백
- [x] 시스템 이슈 발견: 전체 NMS에 OOR 바이트 3,328개 (별도 feature로 분리)
- [x] Plan 문서: `docs/01-plan/features/place-name-fix.plan.md`
- [ ] Design → Do → 검증

### Phase 3: 대사(scemsg) 한글화 — 진행 중
- [x] NMS 패치 정상 (scemsg 1116개 한글 인코딩 확인)
- [x] 대사 번역 전면 다듬기 완료
- [x] 명사 표기 통일 완료
- [x] 인코딩 수정: · → ・ (109개), 누락 한글 5자 추가 (960자 매핑)
- [x] 볼드 폰트(6706A53E1D94C16E) 한글 import — 시스템 메시지 정상
- [x] 일반 폰트(8665CE082D339B33) 한글 import — cell-1644 매핑 동일하게 적용
- [x] **공백 렌더링 해결** — 미사용 한글 '빕'(0x8C6D) 슬롯을 투명 공백 글리프로 활용
  - ASCII 0x20, 전각 0x8140 모두 KANJI 텍스처에서 렌더링되어 깨짐
  - KANJI 페이지 필터 개선: cell0+cell1 알파로 ASCII/KANJI 판별
  - 공백 폭은 전각 고정 (게임 폰트가 고정폭 렌더링)
- [x] **공백 반칸 복구** — space(0x20)만 1-byte 유지 + cell 224 투명 처리
  - build_patch.py: space는 ASCII_SJIS_MAP 리맵에서 제외 (다른 ASCII는 960+ 유지)
  - auto_font_import.py / hd_font_import.py: KANJI 텍스처 local cell 224 투명 클리어
  - 게임이 position=192+0x20=224에서 반폭(16px) 렌더링 → 정상 반칸 공백 복구
- [x] **대사 미출력 버그 해결** — NinPriPatch.cpk가 NinPri.cpk를 오버라이드하는 구조 발견
  - cpk_extract 버그: NinPriPatch scemsg(268KB)가 480B로 잘못 추출됨
  - build_patch.py: NinPriPatch_full/scemsg_full.nms (2178개 US) 사용하도록 수정
  - 본편 대사 1116개 번역 적용 완료, DLC 대사 ~1062개 미번역
- [ ] DLC 대사 ~1062개 번역 추가
- [ ] 보스방 대사 한글 출력 확인

### Phase 3.5: HD 텍스처 팩 적용 ✅ 완료
- [x] Muramasa Complete 2.0 HD 텍스처 팩 (Plaidray/xibalva) 적용
- [x] 2139개 텍스처 최적화 (5.2GB → 829MB, max 2048 + pngquant)
- [x] HD 폰트 텍스처 위에 한글 글리프 오버레이 (4096→2048, 88px→44px)
- [x] 게임 실행 확인 완료
- [x] DLC 4편 텍스처 확인 — HD 팩이 이미 DLC 포함 (별도 업스케일 불필요)
- [x] auto_font_import.py HD 해시 충돌 방지 개선
- [x] FTX 추출 도구 + 일괄 업스케일 도구 작성 (참고용, temp/에 보관)

### Phase 4: 그래픽 텍스처 한글화 — 전수조사 완료 (12/379 텍스처 텍스트 포함)
- [x] ~~영남일보 구상시인체 다운로드~~ → 라이선스 문제로 사용 불가
- [x] 그리운 폴센서빌리티체(Griun_PolSensibility-Rg.ttf) 프로젝트에 추가
- [x] 전수조사 완료: 379개 export 텍스처 → 12개 텍스트 텍스처 식별
- [x] **HIGH** DF66CADDABE022E3 — 메인 UI 텍스트 (Victory, Save, Load, Cooking 등) — 수동 편집 완료
- [ ] **HIGH** 7DC6CF5A87DB1312 — 아이템 이름 (Ability Boost, Sage Elixir 등)
- [ ] **HIGH** E8E01EAF5D41DB52 — 스킬 이름 (Hazy Slash, Divine Blade 등)
- [x] **HIGH** A3BE57CE9854B5CC — 스토리/DLC 제목 (영문 부제) — 수동 편집 완료
- [x] **HIGH** 73420FAEA9F664FD — 본편 타이틀 (오보로 무라마사, 수동 편집)
- [ ] **HIGH** 74EEEC230BEE120C — 스토리 제목+라벨 혼합
- [x] **HIGH** 1823D39C0279886B — 지도 로마자 지명 14개 한글화 완료 (2026-04-26)
  - YAMASHIRO/SHINANO/MUSASHI/HIDA/YAMATO/TOTOMI/MIKAWA → 야마시로/시나노/무사시/히다/야마토/토토미/미카와
  - SAGAMI/SURUGA/OWARI/KAI/MINO/OMIGAISE/IZU → 사가미/스루가/오와리/카이/미노/오미이세/이즈
  - texture_localize_config.json + kr_textures/ui/_notes/1823D39C0279886B.txt 동기화
  - import 폴더 동기화 완료. 사용자 세이브 로드 시 지도에서 한글 라벨 표시 예정
- [x] **HIGH** ADE2B8B5998887A9 — DLC 부제 (겐로쿠 괴기담)
- [x] **HIGH** 79C935AA47DD1810 — 오프닝 나레이션 (Countless Demon Blades...) — **2026-05-13 v0.7.4 적용 완료**
  - 79C935AA47DD1810 나레이션 단어 아틀라스는 투명 처리 유지
  - 4AEC2546371FFF47 오프닝 산 배경 텍스처에 한글 나레이션 직접 렌더링
- [ ] **HIGH** 04110A0F74BE6991 — 지명 한자 아틀라스 (尾張/武蔵/伊賀 등) — **2026-05-10 신규 발견**
- [ ] **HIGH** 9F518FC3E233B9DE — 상점/툴팁 UI 패널 (開/罠 한자 + 보물상자/검 아이콘) — **2026-05-10 신규 발견**
- [ ] **MED** 15CF750523FBB7C6 — 鬼 한자 + UI 심볼 (한글화 여부 검토) — **2026-05-10 신규 발견**
- [ ] **MED** 17BBEF37CC65904A — Hashimoto/Basiscape 크레딧 — **2026-05-10 신규 발견**
- [ ] **MED** ECB628336E68D6AA — UI 버튼 (Clear 영문) — **2026-05-10 신규 발견**
- [ ] **LOW** EDA6F03EC4E141EE — PS 컨트롤러 SELECT/START — **2026-05-10 신규 발견** (보통 영문 유지)
- [x] **HIGH** 247C255A400261FF — 식당(Soba Shop) 메뉴 UI: 보유/품절/소지금/소바집/식사/메뉴/가격/문/냥 — **2026-05-11 v0.7.0 적용 완료**
- [x] **HIGH** 547720A3B20C12AB — 식당류(Restaurant) 메뉴 UI: 위 + 식당 — **2026-05-11 v0.7.0 적용 완료** (s2 상인 화면이 아닌 다른 식당류 화면용으로 확인)
- [x] **HIGH** 1D6742BBC0DDB7EC — 상인(Item/Inventory/Price) 메뉴 UI: 보유/품절/품목/가격/소지금/문/냥 — **2026-05-11 v0.7.0 신규 발견·적용** (codex가 6개 256x256 알파 후보 중 식별)
- [ ] **MED** FFFFD99DCD90D546 — 상점 노렌/간판 한자 사인 — **2026-05-10 신규 발견 (2회차)**
- [ ] **HIGH** 2E88068C58DD36D5 — ASCII 폰트 아틀라스 (메뉴 동적 렌더링) — **2026-05-10 신규 발견 (2회차)**
- [x] **HIGH** A8E6FDD162258699 — KANJI 폰트 아틀라스 (메뉴 항목 한자) — **2026-05-11 v0.7.0 적용 완료** (export 1024x1024 단독 베이스, 6706A53E HD 부풀림 회피, 한글 글리프 959개 주입. 메뉴 항목명 한자가 한글로 동적 렌더링)
- [x] **MED** 8EFF960FC088FDD7 — 그림자 제거 (수동 편집)
- [x] **NEW** 3B58B76CBA15E487 — 시스템 UI (Please, Return, 시작, 새게임, Store 등) — 수동 편집 완료
- [x] **NEW** E4A9FD9D2047280B — 엔딩 "완 결" 텍스트 — 수동 편집 완료
- [x] **NEW** 8725F040AEE76DFC — 수동 편집 완료
- [ ] texture_localize.py 도구 작성

### Phase 5: 통합 테스트
- [ ] 전체 게임 플로우 확인
- [ ] 누락/깨짐 수정

### v0.7.0 릴리스 — 메뉴 UI 한글화 (2026-05-11)
- [x] 식당/상인/식당류 메뉴 UI 사전 렌더 텍스처 3종 한글화 (247C/547720/1D6742BB)
- [x] A8E6FDD1 메뉴 한자 폰트 단독 한글 매핑 (시스템 폰트 격리, HD pack 부풀림 회피)
- [x] codex CLI 위임으로 좌표/폰트 정밀화 — "소지금" 잘림, "가격" 우측 잘림 등 인-게임 검증 후 미세조정
- [x] tools/texture_localize.py에 `clear_rect` 옵션 추가 (한글 박스와 클리어 영역 분리)
- [x] 사용자 인-게임 검증 통과: 메뉴 항목명(자루소바/청어소바/대나무수통 등) 한글 표시, 컬럼 헤더(보유/가격/품목) 한글, 화폐 단위(문/냥) 한글

### 식당 화면 v4/v5 수정 (2026-05-17 사용자 보고)
- [x] 547720A3B20C12AB v4: 식당(34→26), 식사(26→22), 소지금(24→18), 문(20→17) 외 보유/품절/가격/메뉴/냥도 1D6742 패턴과 통일 (sprite UV 범위 안에 한글 fit)
- [x] 547720A3B20C12AB v5: Restaurant region 안의 메뉴 행 강조 박스 흰색 띠 sprite(x=128-229,y=89-129) 보존을 위해 식당 region w=220→126, clear_rect 좁힘 — sprite 픽셀 2077개 100% 보존 검증
- [x] 547720A3B20C12AB v6: v_align 옵션 추가, 식당 fs 26→22, 소지금/문 left align, 가격 region h 28→27 (y=151 sprite 보존)
- [x] 547720A3B20C12AB v7-v8: connected-component sprite mask 자동 보존 + 영문 alpha bbox 자동 측정 → 한글 alpha bbox 정밀 정렬
- [x] 547720A3B20C12AB v9-v10: 잔여 잘림 nudge_x/nudge_y 미세 조정 (식당 fs 22→18 + ny+3, 식사 nx+18 + ny-2, 소지금 ny-3) — 사용자 인-게임 검증 통과
- [x] **auto_align 로직 정식 통합** (2026-05-17): texture_localize.py에 compute_sprite_mask + _process_region_auto 추가, 텍스처 레벨 `auto_align: true` opt-in. nudge_x/nudge_y/v_align region 옵션. macOS/Linux/Windows Vita3K 경로 platform 분기 + VITA3K_EXPORT_DIR/VITA3K_IMPORT_DIR 환경변수 override 지원. 547720A3 통합 빌드 결과 v10 임시 빌드와 byte-for-byte 동일(md5 21cda33d) 검증. requirements.txt에 scipy 추가

## 핵심 기술 정보
- **폰트**: RIDIBatang.otf 22px
- **한글 매핑**: SJIS 0x89CD-0x8EE0 (960자, 셀 1644-2608)
- **패치 방식**: NMS-only CPK + Vita3K texture import
- **명사 통일**

## 2026-05-17: 대사 메시지 띄어쓰기 기반 줄 재정리 ✅ 완료
- [x] 현황 파악: scemsg 2,187개 (1줄 288 / 2줄 626 / 3줄 1273)
- [x] 기존 도구 발견: `tools/rewrap_all.py`, `tools/reflow_dialogs.py`
- [x] 한국어 라인 최대 폭 분석: 본편 max=22.0, DLC max=29.5
- [x] codex+gemini 협의: 두 의견 수렴 → max_width=22 (본편), DLC는 24까지 relaxed
- [x] tools/condense_dialogs.py 작성:
  - 본편: 1줄 우선 → 2줄 → balance 재분배 (max_w=22)
  - DLC: 원본이 22 초과 시 max_w_relaxed=24까지 허용
  - 보존: placeholder(@#(N)), 화자명 라벨, 5글자 미만 짧은 강조, placeholder-only 메시지
- [x] scemsg + scemsg_patch만 적용 (sysmsg/_itemdata는 박스 크기 다양해 보수적 제외)
- [x] 변환 결과: 본편 287건 + DLC 215건 = 총 502건
  - 3→2: 307건, 2→1: 64건, 같은 줄 수 balance 재분배: 131건
  - 줄 수 분포: 1줄 288→352, 2줄 626→869, 3줄 1273→966 (3줄 -307)
  - 줄 폭 분포 p50: 15.5→16.5, p99 동일(23.0), max 동일(29.5)
- [x] OOR 감사: 707개로 변경 전과 동일 (우리 변경으로 OOR 증가 없음)
- [x] 빌드 + macOS Vita3K 배포 완료 (NinPri + NinPriPatch)
- [ ] 인-게임 검증 (사용자 — macOS 자동 테스트 불가)

## 2026-05-17: 대사 줄 재정리 2차 — 짧은 라인 공격적 압축 ✅ 완료
사용자 피드백: "줄 재정리 기준은 3줄인데 각 줄 글자수가 너무 적은 것을 더 찾으면 될 거 같아."

### 분석 (남은 3줄 메시지 966개)
- 각 줄 폭: min p50=14.5, avg p50=15.8, max p50=17.0, joined p50=48.0
- 1차 기준(max_w=22)으로는 3줄→2줄 후보 0개
- max_w=24 완화 시: **376개 가능** ← 핵심 발견
- JP 원문 폭 분포: p50=22, p95=28, max=31 (24폭은 안전 마진 충분)
- JP 원문은 1~2줄만 존재 (3줄 0개) — 한국어도 2줄로 다수 가능

### 외부 AI 협의 (codex + gemini 병렬)
- **gemini**: 24 안전, 합산 ≤ 48 + max_line ≤ 24 후보 약 300~400건 추가 압축 권장.
  의도적 페이싱 보존: 모든 줄 < 8자 시 SKIP. 옵션: `--aggressive`, `--preserve-pacing`.
- **codex**: 24는 렌더링 안전하나 전역 기본값 상승은 X. "남은 3줄에 한정"해 24 적용.
  짧은 외침(!?…)/짧고 모든 줄 짧음은 보존. 옵션: `--aggressive-short-lines`, `--relaxed-max-width 24`.
- **수렴**: 기본 max_w=22 유지, 3줄 메시지에 한해 24로 공격적 압축. 페이싱 보존 강화.

### 도구 개선 (`tools/condense_dialogs.py`)
- `--aggressive-short-lines`: 3줄 메시지에 한해 max_w 상한을 aggressive-max-width(기본 24)로 상향
- `--aggressive-max-width 24`: 공격 모드 상한 (기본 24)
- `--no-preserve-pacing`: 의도적 페이싱 보존 규칙 해제 (기본 활성)
- `is_intentional_pacing()`: 모든 줄 < 8자 + 강조부호(!?…) 종결 → 보존
- 단어 중간 자르기 금지·placeholder 보존·화자명 보존 규칙 유지

### 적용 결과
- 본편 scemsg: 376건 3→2 (전부 단어 경계 split, max_w ≤ 24)
- 줄 수 분포: 1줄 388 (변동 없음), 2줄 869→**1245** (+376), 3줄 966→**590** (-376)
- 한국어 라인 폭 p95: 21.5 → 23.5 (JP p95=28보다 안전)
- 짧은 라인(< 10자) 페이싱 보존 대상: 데이터 내 0건 (1차에서 이미 합쳐짐)
- OOR 감사: 707개 (변경 전후 동일)

### 검증·배포
- [x] NMS 빌드 (build_patch.py) — 정상
- [x] CPK append 패치 (NinPri 455.0MB / NinPriPatch 25.7MB)
- [x] macOS Vita3K 배포 (~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/)
- [x] OOR 감사 동일 확인
- [ ] 인-게임 검증 (macOS 자동 테스트 불가, 사용자 확인 대기)

### 누적 (1차 + 2차)
- 총 변경: 502 + 376 = **878건**
- 줄 수 분포 (원본 → 1차 → 2차):
  - 1줄: 288 → 352 → 388
  - 2줄: 626 → 869 → 1245
  - 3줄: 1273 → 966 → 590
