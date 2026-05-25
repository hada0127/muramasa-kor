# TODO — 진행 예정 작업

> 완료 작업 상세 기록은 [success.md](success.md), 실패·한계 기록은 [fail.md](fail.md) 참고.
> 현재 릴리스: **v0.9.3** (2026-05-25)
> 텍스처 편집: 웹 UI 에디터 `python tools/ui_editor/server.py` (http://127.0.0.1:8765)
> 텍스처 구조: `textures/{originals, place_originals, kr/ui, kr/font}`

---

## 🔴 미해결 이슈 (인-게임 검증 / 외부 데이터 필요)

### Task #1 — 찻집 메뉴 가격 "10"의 "1" 누락 + 메뉴 헤더 폰트
- 증상: 찻집 메뉴에서 가격 "10문"의 "1"이 안 보이고 "0문"만 표시. 메뉴 헤더 한글이 그리운경찰체(텍스처) 대신 RIDIBatang(동적 폰트)로 표시.
- 핵심 의문: c8322ee(2026-05-13) 시점엔 정상이었는데(동일 텍스처 MD5) 이후 RIDIBatang dynamic으로 바뀐 환경 요인.
- 관련: 텍스처 `2E2003777A770327`, 폰트 `A8E6FDD162258699`(메뉴 항목명 동적 렌더 트리거).
- 메모리: `memory/project_price_one_invisible.md`
- 다음: c8322ee 빌드 인-게임 검증 → 깨짐 시점 이분 검색 → 폰트 텍스처 dump 비교.

### Task #2 — DLC1 바케네코(化猫)편 결말 컷씬 멈춤
- 증상: 결말 컷씬에서 음성/음악은 진행되나 화면 정지, X 입력에도 진행 안 됨.
- 가설(codex/gemini 확정): `build_patch.py` jp_index 매칭이 JP 음성 placeholder(`　（…ボイス）`)를 한국어로 매핑 → 영문판이 자동진행하던 자리에 일반 대사가 들어가 X 대기로 멈춤. (JP[1339] = scemsg#1354)
- 제안 해결: build_patch에서 음성 placeholder 패턴(`^[　\s]*[（(].*(ボイス|ＳＥ|SE|効果|声|音).*[）)]…`) 매칭 시 매핑 skip.
- 비슷한 위험: 본편 보스 후 컷씬, 엔딩 크레딧 직전, sysmsg "(Don't translate)".
- 메모리: `memory/project_dlc_cutscene_freeze.md`
- 다음: skip 로직 추가 → US scemsg.nms #1339 원문 유지 검증 → 인-게임 확인.

---

## 🟡 진행 중

### Phase 3 후속 — DLC 대사 번역
- [ ] DLC 대사 ~1,062개 번역 추가 (본편 1,116개는 완료)

### Phase 4 — UI 그래픽 텍스처 한글화 (남은 항목)
- [ ] `7DC6CF5A` — 아이템 이름 (Ability Boost, Sage Elixir 등)
- [ ] `E8E01EAF` — 스킬 이름 (Hazy Slash, Divine Blade 등)
- [ ] `74EEEC23` — 스토리 제목 + 라벨 혼합
- [ ] `04110A0F` — 지명 한자 아틀라스 (尾張/武蔵/伊賀)
- [ ] `9F518FC3` — 상점/툴팁 UI 패널 (開/罠 한자 + 아이콘)
- [ ] `2E88068C` — ASCII 폰트 아틀라스 (메뉴 동적 렌더)
- [ ] `FFFFD99D` — 상점 노렌/간판 한자 사인 (MED)
- [ ] `15CF7505` — 鬼 한자 + UI 심볼 (MED, 한글화 여부 검토)
- [ ] `17BBEF37` — Hashimoto/Basiscape 크레딧 (MED)
- [ ] `ECB62833` — UI 버튼 (Clear 영문, MED)
- [ ] `EDA6F03E` — PS 컨트롤러 SELECT/START (LOW, 보통 영문 유지)

### OOR 전수 감사 (별도 feature)
- [ ] 패치 NMS 전체 범위 밖 SJIS 바이트 감사 (현재 ~707개 baseline)

---

## ✅ 최근 완료 (요약, 상세는 success.md)
- v0.9.3: 결과 화면 '평가' 텍스처 클리핑 수정
- v0.9.2: 보스 전용 무기 아이템명 한자 깨짐 수정(BOSS→보스)
- 텍스처 폴더 단일 트리 통합 + Krita 폐기, 미사용 스크립트·JSON 56개 정리
- README/기여자 문서 갱신
