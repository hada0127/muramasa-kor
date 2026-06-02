# TODO — 진행 예정 / 미해결 작업

> 완료 작업 상세는 [success.md](success.md), 실패·한계는 [fail.md](fail.md).
> 이 파일은 **열린/보류/예정** 항목만 둔다. 완료되면 success.md로 옮기고 여기선 지운다.
> 현재 릴리스: **v1.2.1** 🎉 (2026-05-27 — ✕ 추가팩에 메인 메뉴 DF66CADD 포함, 이슈 #15)
> 텍스처 편집: `python tools/ui_editor/server.py` (http://127.0.0.1:8765)

---

## 적용 완료·인게임 검증 대기 — 이슈 #16 (1.2.1 제보 2건, 2026-06-02)

제보자: mtmate-rgb (HD 텍스처팩 + ✕버튼 패치 동시 적용). 세이브 첨부. macOS라 인게임 검증은 제보자/사용자.

### #16-1 백사전 챕터선택 음영 어긋남 → ✅ 잔상 소거 (원인 확정)
- 원인(데이터 확정): 텍스처 `A3BE57CE9854B5CC`(idx4) K8 백사전. 원본 영문 "White Serpent"가
  K8 박스(x0-1281,y3314-3517)를 우측·하단으로 초과(글리프 x4~1516, y~3611). 한글 박스만 clear→
  박스 밖 영문 꼬리 **10,536px가 안 지워진 잔상**(어떤 clear박스에도 미포함). White Serpent가
  최장 타이틀이라 **백사전만** 발생.
- **codex 의견**: 잔상 미제거. 넓은 단일 rect 말고 행 단위로 안전 클리어 권고. (이미 빈 텍스트 clear-only region 선례 있음)
- **agy 의견**: 가설(a) 잔상 지지(워터마크 정렬 가능성 낮음). 오버플로 영역 알파0 소거, 인접 K4 인법첩 손상 주의.
- **최종 조치**: K8 글리프(x≤870)·K4 인법첩(x≥1647)·K7 요도(x≤721) 사이 빈틈에만 clear-only 헬퍼
  region 추가(`K8_serpent_tail_clear`, clear_rect x1140 y3365 w395 h255). 재렌더 후 잔상 0px, 한글 0px 손실 검증.

### #16-2 닌자주머니 메뉴 "반야탕" vs HUD "술" → ✅ "반야탕"으로 통일
- 원인: 메뉴=NMS텍스트 _itemdata id6 般若湯="반야탕". HUD 퀵슬롯=텍스처 `E8E01EAF5D41DB52`(idx5) K10,
  원본 영문 **"Sake"**→우리 "술". 원본 US부터 메뉴(般若湯)≠HUD(Sake) 이중구조. per-item 슬롯
  확인(hash8 甘酒="Sweet Rice Wine" 등) → "Sake"=般若湯 전용, 변경 안전.
- **codex/agy 의견 수렴**: 둘 다 (a) "반야탕"으로 통일 권장(아이템 정식명 일치로 버그 오인 방지 + 시대극 톤).
- **최종 조치**: K10 "술"→"반야탕"(fit_to_box로 박스 안착). config + ui_editor_index(text·native.text) 동기화.
  kr json 없음(라벨 참조파일 미존재). 재렌더 후 박스(w222) 내 x5-216 안착 검증.

→ 다음: 사용자 인게임 확인 후 이슈 #16 코멘트/클로즈. 확인되면 success.md로 이관.

## 보류 — DLC 엔딩 "完" → "완 결" 한글화 (이슈 후속, 2026-05-27 위치 확정)

- **출처 확정(codex+직접 조사)**: DLC 엔딩 完은 export/originals 텍스처가 아니라, 설치된 DLC 팩
  CPK 내부 `GUI/Ending_P1~P4.ftx`(에피소드별). 각 1024×1024 캐릭터 일러스트 + 좌하단 큰 붓글씨
  完(bbox≈x1-320,y430-850). 본편 엔딩 The End(`E4A9FD9D`)와 별개.
  - CPK: `~/Library/Application Support/Vita3K/Vita3K/fs/ux0/addcont/PCSE00240/OBOROMURAMASAPK1~4/NinPriPackN.cpk`
  - 추출본/미리보기(temp/): `temp/dlc_ftx_png/pack{1..4}/GUI/Ending_P*.png`, `temp/preview/DLC_endings_all4.png`
  - export 폴더(747개) 전수 — 일치 텍스처 없음 → **Vita3K import hash 미확보**.
- **방법(택1, 다음 작업)**:
  (A) 인게임에서 각 DLC 엔딩을 texture export 켜고 띄워 4개 hash 확보 → 完 자리에 완 결 오버레이.
  (B) DLC 팩 CPK의 `Ending_P*.ftx` 직접 교체(hash 불필요·전 사용자 적용). 단 **FTX 재인코더(DXT5+스위즐)
     신규 제작 필요** — 현재 repo엔 decoder `ftx_extract.py`만 있음.
- 사용자 결정: **이번 릴리스 보류.** 상세는 `docs/03-analysis/export-texture-audit-2026-05-20.md` "Ending 完 Handling".
- 참고: sysmsg 엔딩 텍스트(#255 본편·#279~282 DLC)는 이미 "완결"로 번역됨(텍스트는 정상).
- **2026-05-30 RGB 퍼셉추얼 재확인(claude+codex 병행)**: CPK 추출본 `Ending_P1~4.png`(1024², RGB 일러스트)를
  export(741개)+originals(92개)와 32×32 그레이 NCC 비교 → 최고 NCC **0.76**(동일=1.0 기준 한참 미달). 즉
  **export/UHD 어디에도 엔딩 텍스처 없음** 재확인. import hash 미확보 결론 변동 없음 → 인게임 export 캡처(방법 A) 필요.
  매칭 스크립트: `/tmp/rgb_fast.py`, 결과 `temp/ending_rgb_fast.json`.

## 보류 — DLC place 아틀라스 `place59`(pack3) 한글화 (2026-05-30 발견)

- `temp/dlc_ftx_png/pack3/GUI/place59.png`(512×256): 近江·伊賀·筑紫城·骸衆本陣·野鎚城 등 **여러 DLC 지명 묶음 아틀라스**.
- RGB 매칭에서 export/originals 1.0 매치 없음(최고 0.60) → **런타임 import hash 미확보**(엔딩과 동일 한계).
  개별 지명(近江/伊賀/筑紫/骸衆)은 이미 다른 등록 텍스처/대사에 한글 존재. 인게임 export로 hash 확보 시 등록 가능.
- 비교: place52~58·60~63(12개 중 11개)은 등록 originals와 NCC **1.000 동일** → 이미 등록·번역 완료.

## 제보 종결 — 보스 드롭 "인왕의 팔찌→쌍나루코" 의혹 (2026-06-01, 패치 무관 확정)

- 제보: 1회차 클리어 후 스루가 용신 재격파 시 공략의 "인왕의 팔찌"가 아니라 "쌍나루코"가 입수됨 → 패치가 데이터 건드린 것 아니냐.
- 직접 검증: 패치는 msgsheet NMS 텍스트+텍스처(알파)만 1:1 슬롯 치환(`build_patch.py` 구조 보존), eboot/드롭테이블 미수정.
  `_itemdata` 인덱스 확인 — 인왕의 팔찌=576, 쌍나루코=564, 나루코=562, 나루카미 팔찌=574. 뒤바뀜/오프바이원 없음.
- **codex 의견**: 결론 타당. 드롭은 패치로 변경 불가. 확정법=같은 세이브 패치 ON/OFF 비교.
- **agy(antigravity) 의견**: 매우 타당. 포인터 깨졌다면 멀쩡한 "쌍나루코"가 아니라 텍스트 깨짐/크래시로 나타남 → 정상 표시는 오히려 패치 정상 방증. 확정법=순정 영문판 재격파 후 "Twin/Double Naruko" 확인.
- **최종 결정**: 패치 결함 아님. Vita 영문판 실제 드롭이며 공략(Wii/JP·캐릭터/회차 분기)과의 버전 차이. 제보자에겐 순정 ON/OFF 세이브 교차검증 권고.

## 조사 종결 — export/UHD 미번역 지명·신규 텍스트 텍스처 없음 (2026-05-30)

- 계기: 사용자 발견 `FFFFD99DCD90D546` = 茶屋(찻집), 이미 place_jobs 등록·렌더 완료(status needs_review). 신규 아님.
- export(747)+UHD 팩(2139) 전수, 등록 82개 제외 후 텍스트 텍스처 탐지: claude 스코어러(419후보)·codex 스코어러(50후보)
  상위 후보 시트 **육안 검증 → 전부 구름/발광/파티클/이펙트**, 붓글씨 한자 지명 카드 0건. → 미번역 지명 텍스처 없음 확정.

## 의도적으로 하지 않는 항목 (사용자 결정)

- **#9-3 무기명 변수 치환**: 원작은 무기명을 런타임 변수(`##（무기）`)로 출력하나 US 엔진이 토큰을
  제거("this blade") → 텍스트/폰트 패치로 복원 불가(eboot 역공학 필요). **진행하지 않음.**

## 추후 필요 시 (현재 미예정)

- `_itemdata`/`sysmsg` 등 비대사 섹션 재번역 (필요해지면 대사와 같은 파이프라인으로).
- 손글씨체 重/隼 폰트 페이지(`font2a/2b` 계열)는 해당 화면 export 시 `auto_font_import` 재실행으로 자동 커버.
- 이슈 #11 후속(선택): UI 에디터에 실제 PIL 라이브렌더 표시(서버 `render_live` 연동)로 WYSIWYG화.
- 이슈 #10 borderline 1건: scemsg#941 "기치를 발휘"(頓智) — 사용자 확인 후 "재치를 발휘" 검토.

---
새 작업·이슈가 생기면 이 파일에 추가하고, 끝나면 success.md로 옮긴다.
