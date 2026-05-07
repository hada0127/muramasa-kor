# TODO - 진행 예정 작업

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
- [ ] **HIGH** 79C935AA47DD1810 — 오프닝 나레이션 (Countless Demon Blades...)
- [x] **MED** 8EFF960FC088FDD7 — 그림자 제거 (수동 편집)
- [x] **NEW** 3B58B76CBA15E487 — 시스템 UI (Please, Return, 시작, 새게임, Store 등) — 수동 편집 완료
- [x] **NEW** E4A9FD9D2047280B — 엔딩 "완 결" 텍스트 — 수동 편집 완료
- [x] **NEW** 8725F040AEE76DFC — 수동 편집 완료
- [ ] texture_localize.py 도구 작성

### Phase 5: 통합 테스트
- [ ] 전체 게임 플로우 확인
- [ ] 누락/깨짐 수정

## 핵심 기술 정보
- **폰트**: RIDIBatang.otf 22px
- **한글 매핑**: SJIS 0x89CD-0x8EE0 (960자, 셀 1644-2608)
- **패치 방식**: NMS-only CPK + Vita3K texture import
- **명사 통일**