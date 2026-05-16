# SUCCESS - 성공한 작업 기록

## 2026-05-16: battle-result-time-fix — 결과창 hh:mm:ss 콜론 깨짐 수정 ("봐" SJIS 재배치)

### 배경
이슈 #2 (v0.7.0) 항목 3: DLC 1 바케네코편 전투 결과창 첫 줄 "시간" 값이 "0봐 0 0봐 1 9" 형태로 깨짐.

### 원인 진단 (PDCA)
- 화면 분석: 정상 의도 `"0:00:19"` (hh:mm:ss) 시간 표시
- 게임 코드(eboot.bin)가 시간 출력 포맷 `"%d：%d：%d"`에 **전각 콜론(`：`, SJIS 0x8146) hardcoded**
- raw 0x8146 → 폰트 KANJI 페이지 local cell 6+448=454로 매핑
- cell 454 = 한글 "봐" (SJIS 0x8C5E)와 동일 위치 → "봐" 글리프 표시
- success.md 2026-04-13 fullwidth-normalize와 동일 메커니즘이지만 NMS가 아닌 게임 바이너리 hardcoded라 `_normalize_text()` 적용 불가

### 검증
- 빌드된 NMS 전체에 raw 0x8146 = 0회 (정규화 완벽)
- 원본 NinPri _itemdata 595회, sysmsg 4회 — 모두 정규화됨
- eboot.bin 검색은 압축으로 직접 식별 어려움 — 메커니즘으로 단정

### 해결: A안 (success.md "덴 글자 복구" 패턴 차용)
1. **"봐" SJIS 재배치**: `kr_sjis_mapping.json`에서 [140, 94] (0x8C5E) → [142, 239] (0x8EEF, local 974, ASCII zone period skip slot)
2. **cell 454 콜론 오버레이**: `auto_font_import.py`/`hd_font_import.py`에 `FULLWIDTH_OVERLAY = {454: ':'}` 추가
   - 게임 raw 0x8146 출력 → cell 454 → ":" 글리프 표시 (정상!)
3. NMS의 "봐" (216회 출현)은 새 SJIS 0x8EEF로 인코딩 → cell 974에 자동 그려진 "봐" 글리프 표시

### 검증 (빌드 후)
- 빌드된 NMS의 봐(SJIS 0x8EEF) = 216회 (예상치 일치)
- 옛 봐(SJIS 0x8C5E) = 0회 (완전 마이그레이션)
- 폰트 텍스처 cell 454 = 콜론 ":" 글리프 (시각 확인)
- 폰트 텍스처 cell 974 = "봐" 한글 글리프 (시각 확인)

### 적용된 폰트 텍스처
- A8E6FDD162258699 (메뉴 KANJI 폰트) — auto_font_import 재생성, 959 글리프
- 8665CE082D339B33 (일반 KANJI 폰트) — auto_font_import 재생성, 959 글리프
- 6706A53E1D94C16E (HD 폰트) — hd_font_import 재생성, 1024x1024 dark format

### 빌드/패치
- `python3 tools/build_patch.py` 재빌드 — sysmsg 574+963, _itemdata 878+1426 매칭 유지
- `python3 tools/cpk_patch.py` 적용 — NinPri +149KB, NinPriPatch +282KB
- macOS Vita3K 경로 설치: `~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/`
- 폰트 textures: macOS 경로 (`~/.../textures/import/PCSE00240/`) + 리포 `kr_textures/font/` 동기화

### 백업
- `translations/kr_sjis_mapping.json.bak_bwa`

### 남은 검증 (사용자)
- 결과창 시간: "0:00:19" 정상 표시 확인 (cell 454 콜론 적용)
- NMS의 "봐" 73회 정상 표시 확인 (cell 974 새 봐 위치)
- 전각 콜론(`：`)이 추가로 hardcoded인 다른 화면도 동일하게 정상화될 것
- 다른 전각 punctuation (`！？（）％`) hardcoded 영향은 사용자 보고 발견 시 동일 방식으로 추가 (`FULLWIDTH_OVERLAY`)

---

## 2026-05-15: currency-unify — 화폐 단위 통일 (A안: 냥/문 + 백분율 %)

### 배경
이슈 #3 (v0.7.1) 보고: 가마꾼 대사에서 금액 호칭이 "돈"으로 나오는데 다른 곳은 "문"으로 표시되어 불일치.

### 전수조사 결과 (temp/currency_audit/summary.md)
- 일본 원작 화폐: 両(큰)/文(작은)/分(백분율 1%)/金(money 의미)
- 한국어 현재: 냥 5건(両, 일관) / 문 4건(文 포맷) / 푼 9건(分 백분율) + 1건(文 관용구) / 돈 25건(金) / % 2건(分)
- 텍스처 4개(247C/547720/2E2003/1D6742BB): 모두 "냥/문" 통일 완료

### 핵심 오번역 식별
- `sysmsg #205, sysmsg_main[153]` 원문 `文を支払い利用しますか？` → "돈을 지불하고 이용하시겠습니까?" (오번역)
- 이게 사용자가 본 가마꾼 화면 시스템 메시지의 정체

### 외부 AI 협의
- codex: 사용량 한도 초과로 응답 실패
- gemini: A안(냥/문 + 백분율 %) 추천. 근거: '푼'은 돈/비율 두 의미로 모호, '문'은 조선 상평통보 단위로 한국 사극 친숙, 텍스처 4개 보존
- 사용자 결정: A안 채택 + 추상적 '돈'(金) 25건은 현행 유지

### 수정 항목 (총 14건)
1. `sysmsg #205, sysmsg_main` 2건: "돈을 지불하고" → "문을 지불하고"
2. `_itemdata` 백분율 8건: "1푼/2푼/5푼" → "1%/2%/5%"
3. 조사 자연화 4건: "1%을" → "1%를" (생명력의 X%를 회복/X%를 흡수)

### 보존
- 관용구 `ビタ一文` → "한 푼도 안" — 한국어 자연스러움
- 일반 대화 25건 "돈" → 그대로 (자연스러운 의역, 시스템 메시지가 아님)

### 빌드/패치
- `python3 tools/build_patch.py` 재빌드 — sysmsg 574+963, _itemdata 878+1426 매칭 유지
- `python3 tools/cpk_patch.py` 적용 — NinPri +149KB, NinPriPatch +282KB
- macOS Vita3K 경로 설치: `~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/`

### 남은 검증 (사용자)
- 가마꾼 화면 진입 → "문을 지불하고 이용하시겠습니까?" 표시 확인
- DLC 어빌리티 화면 → 효과 텍스트에 "1%를 흡수한다", "5% 상승한다" 등 정상 표시 확인
- 백업: `translations/jp_messages.json.bak_currency`

### 영향 받지 않는 곳
- 텍스처 4개 (소바집/식당/찻집/상인 메뉴 UI) — 변경 없음 (이미 "냥/문" 통일)

---

## 2026-05-15: period-glyph-fix — 시스템 대사 마침표가 가운뎃점처럼 보이던 문제 수정

### 증상
IMG_3111 대사 "넘어가 주지 ·뒤는 나라에 / 맡기는 걸로 해두마 ·" — 마침표가 가운뎃점(·)처럼 글자 라인 중앙에 떠 있음.

### 원인
HD 폰트 텍스처 `6706A53E1D94C16E` (1024 KANJI 페이지)의 cell 238 (= 192 + 0x2E '.') 글리프가 import에서 (14,14)-(16,16) — cell 정중앙에 size 7픽셀 작은 점으로 그려짐. 게임이 raw byte 0x2E를 이 cell에서 가져와 렌더 → 가운뎃점 시각.

원본 export 글리프는 (4,17)-(12,25) — cell 좌측 중하단에 size 65픽셀의 정상 마침표.

비교:
- 6706A53E IMPORT cell 238: (14,14)-(16,16) MIDDLE (잘못)
- 6706A53E EXPORT cell 238: (4,17)-(12,25) BOTTOM-LEFT (정상)
- 8665CE08 IMPORT cell 238: (2,25)-(4,27) BOTTOM-LEFT (정상, auto_font_import.py 결과)

8665CE08은 정상인데 6706A53E만 잘못된 이유는 미상 (hd_font_import.py가 의도와 다른 위치에 그림). 코드상으로는 `gy = y + cs - gh - 4*scale - bbox[1]` 좌측 하단 정렬 로직.

### 처리
1. `~/Library/.../import/PCSE00240/6706A53E1D94C16E.png`의 cell 238 영역 (448,224)-(480,256)을 export 원본의 동일 영역으로 덮어쓰기 (다른 한글 글리프는 그대로 유지)
2. `kr_textures/font/6706A53E1D94C16E.png`도 동기화
3. `tools/hd_font_import.py`의 `RUNTIME_OVERLAY_CODES`에서 0x2E '.', 0x2C ',' 제거 — 향후 재빌드 시 export 원본 글리프 보존
4. /tmp/6706A53E_import_backup.png에 이전 import 백업

### 검증
`temp/preview/period_glyph_fix.png`에서 OLD/EXPORT/NEW 12배 확대 비교: NEW가 EXPORT와 동일한 정상 마침표 모양.

### 남은 확인 (사용자)
Vita3K 재시작 후 시스템 대사에서 마침표 위치 검증. 만약 여전히 가운뎃점처럼 보이면 (a) 마침표 글리프가 다른 폰트(예: 2E88068C58DD36D5 ASCII 페이지)에서 오는 것 (b) NMSB 텍스트에 실제 ・(U+30FB)가 남아있음 — 어느 쪽인지 추가 분석 필요.

### 외부 AI 협의
gemini CLI 호출했으나 응답 지연. codex CLI 사용량 한도 도달. 가설이 명확하고 export/import 비교 픽셀 증거가 결정적이라 단독 진행.

---

## 2026-05-15: digit-0-sprite-fix v8 — 1D6742BB 진짜 원본 베이스로 디지트 0 복구 완료

### 추가 진단
v7 패치 적용 후 사용자가 Vita3K 상인 화면 스크린샷 재제출. 가격 컬럼에서 끝자리 0이 비어있음 (예: 50푼이 "5 ?"). v7 수정으로도 부족함.

### 핵심 원인
이전 1D6742BB 빌드는 `upscaled/1D6742BBC0DDB7EC.png` (1024x1024 HD 팩) → LANCZOS 256x256 다운스케일을 베이스로 사용. 그런데 HD 팩 텍스처에는 원본 256x256의 **디지트 0 sprite (140,168)-(157,186)·(160,168)-(171,181) 두 군데가 없음**(또는 다른 형태). 다운스케일 결과에는 그 자리가 비어 있어, 게임이 그 위치에서 디지트 0을 가져올 때 투명 픽셀만 가져옴 → 끝자리 0 누락.

### 해결
macOS Vita3K export 폴더 `~/Library/Application Support/Vita3K/Vita3K/textures/export/PCSE00240/1D6742BBC0DDB7EC.png`에서 진짜 256x256 원본 발견 → `textures/originals/`에 추가 → 동일 config로 재빌드.

### 검증 (clear 영역 밖 손상)
`(원본 알파 > 30) & (kr 알파 < 10)` 마스크로 디지트 후보 손상 클러스터 추출 후 우리 clear 영역과 교차.
- 247C255A: 22개 후보 모두 [정상-clear내]
- 547720A3: 24개 후보 모두 [정상-clear내]
- 1D6742BB: 17개 후보 모두 [정상-clear내] (v7까지는 2개 경계밖 손상, v8에서 해결)

### 동기화
`kr_textures/ui/1D6742BBC0DDB7EC.png` + macOS Vita3K import 폴더 모두 갱신. 사용자 측 Vita3K 재시작 후 상인 화면 검증 부탁 (가격 표시의 끝자리 0 정상 출력 확인).

---

## 2026-05-14: digit-0-sprite-fix — 소바집/식당/상점 UI 디지트 sprite 손상 복구

### 배경
사용자 보고: 소바집 화면에서 가격의 "0"이 출력 안 됨 (예: "80"이 "8"로만 보이는 듯). 상점·찻집도 동일 의심.

### 원인
247C255A·547720A3·1D6742BBC0DDB7EC 텍스처의 한글화 작업에서 사전 렌더 디지트 sprite (0-9) 영역까지 clear가 침범:
- **247C255A** 가격 clear_rect (0,163,72,32) → 디지트 0 sprite (32,189)-(52,209)의 상단 6px 잘림
- **547720A3** 가격 region (30,124,100,28) → 디지트 sprite (96,126)-(116,146)와 (38,126)-(52,146) 잘림
- **547720A3** 냥 region (0,184,60,26) → 우측 디지트/장식 sprite (38,186)-(56,205) 잘림
- **1D6742BB** 냥 region (138,145,40,44) → 안에 ryo 영문/所 한자/디지트 0이 모두 있는 큰 박스가 모두 클리어됨

### 조사 방법
- `textures/originals/`의 원본 알파 connected-component 분석으로 디지트 sprite bbox 정밀 측정 (scipy.ndimage)
- 손상 = `(원본 알파 > 30) & (kr 알파 < 10)` 마스크로 클러스터 분석
- 1D6742BB는 원본 부재 → `upscaled/1D6742BBC0DDB7EC.png` (1024x1024)을 LANCZOS 256x256 다운스케일로 추정 베이스 사용
- 시각 검증: `temp/preview/{hash}_price_zone.png`, `_ryo_zone.png` 에 박스 오버레이로 영문/디지트 분리

### 처리
`translations/texture_localize_config.json` 수정:
- **247C255A** 가격: text h 32→22, clear_rect h 32→25 (y=163-188까지만 클리어, 디지트 y=189 보호)
- **547720A3** 가격: x 30→38, w 100→56, clear_rect 신규 추가 (영문 Price만 클리어, x=96+ 디지트 보호)
- **547720A3** 냥: w 60→38, clear_rect 신규 추가 (디지트/장식 x=38+ 보호)
- **1D6742BB** 가격: text h 32→22, clear_rect h 32→25 (안전 마진)
- **1D6742BB** 냥: h 44→25, clear_rect 신규 추가 (y=170+ 所 한자/디지트 0 보호)

### 결과
- `kr_textures/ui/247C255A400261FF.png` — 디지트 0 링 온전히 복원
- `kr_textures/ui/547720A3B20C12AB.png` — 가격 옆 디지트들 + 냥 옆 sprite 복원
- `kr_textures/ui/1D6742BBC0DDB7EC.png` — upscaled 베이스로 디지트/한자 복원
- 미리보기: `temp/preview/{hash}_after_fix.png` 3개

### 남은 검증 (사용자 측 Windows Vita3K 필요)
- 실제 게임에서 소바집/식당/상점 가격 표시 "80", "30" 등 디지트 0 출력 확인
- 1D6742BB는 upscaled 추정 베이스라 인게임 실제 export 원본과 미세 차이 가능 — 차이 발견 시 사용자가 Vita3K export 후 textures/originals/에 저장 → 재빌드

### 참고
- 사용자 메시지 "소바집, 상점, 찻집 문제는 텍스쳐 문제일 가능성이 제일 큼" → 곧장 정답으로 안내해줌
- Gemini CLI 분석도 동일 가설 (이슈 #1, "UI 텍스처 한글화 과정에서 숫자 스프라이트 영역이 의도치 않게 지워졌을 가능성")로 수렴
- Codex CLI는 사용량 한도 도달, 단독 진행

---

## 2026-05-10: texture-upscale — Vita3K export 텍스처 FHD 업스케일 (로컬 전용)

### 배경
HD 팩(Muramasa Complete 2.0)이 커버하지 못하는 export 텍스처들이 FHD 화면에서 흐림. 273장의 export 자산을 일괄 업스케일하되, 한글 패치를 깨뜨리지 않고 배포에는 영향이 없어야 함.

### 처리
1. PDCA Plan: `docs/01-plan/features/texture-upscale.plan.md` (제외 정책·엔진 근거)
2. Real-ESRGAN ncnn-vulkan v0.2.5.0 (universal binary) → `temp/realesrgan/`, arm64 즉시 동작
3. 신규 도구 `tools/upscale_export.py`:
   - 모델 `realesr-animevideov3`, max 변 1920px cap (LANCZOS 다운샘플)
   - 자동 skip: 폰트 4 hash (`tools/.font_hashes.json`) + `kr_textures/ui/` 81종
   - dry-run / limit / install / force / cache 옵션
4. `.gitignore` 에 `upscaled/` 등록 + 사유 주석
5. 샘플 5장 검증 (45s, 9s/장 페이스, 1920 cap 정상)
6. 본 배치 256장 / 1917s ≈ 32분, 0 실패
7. Report: `docs/04-report/texture-upscale.report.md`

### 결과
- 261장 업스케일 (루트 68 + PCSE00240/ 193), 폰트/한글 UI 15장 자동 skip
- 52MB → 465MB (4x + RGBA + 무손실 PNG)
- `upscaled/` git status 안 잡힘 (gitignored 검증 완료)
- 캐시 동작: 재실행 시 신규분만 처리

### 핵심 결정
- Real-ESRGAN 채택 — 기존 `batch_upscale.py` 통합 경험, universal binary, animevideov3 게임 친화
- 1920px cap (FHD 단축) — 1024→1920 (2x), 512→1920 (4x cap), 256→1024 (4x cap)
- 비배포 정책 강제 — `.gitignore` 라인에 사유 주석으로 의도 고정
- 폰트/한글 UI 자동 제외 — JSON + 디렉토리 글롭 두 소스 활용

### 사용법
```bash
python3 tools/upscale_export.py             # 전체 (캐시 스킵)
python3 tools/upscale_export.py --dry-run   # 사전 확인
python3 tools/upscale_export.py --install   # Vita3K import/ 자동 복사
```

### 커밋
- `a0b235c` Add texture-upscale tool for local FHD upscaling

---

## 2026-04-26: 1823D39C0279886B 지도 화면 로마자 지명 14개 한글화

### 배경
사용자 스크린샷(`OneDrive/Pictures/스크린샷/스크린샷 2026-04-26 061241.png`)에서 지도 메뉴의 라벨이 영어/로마자로 표시됨 발견 — 카테고리: 国名 로마자 (place_names 아틀라스, status: pending in `place_name_textures.json`).

### codex/gemini 병렬 자문 결과
- gemini: 지명은 `place_name_mapping.json`으로 관리. 스탯 라벨은 UI 텍스처 + 폰트.
- codex: 지도 핀 지명 텍스처 아틀라스, 특히 `1823...`와 `place_names` 계열.
- 수렴 → `1823D39C0279886B` 타겟 확정.

### 처리
1. 256x128 원본/1024x512 kr 버전 양쪽에서 라벨 14개 식별:
   - 수평(좌측): YAMASHIRO/SHINANO/MUSASHI/HIDA/YAMATO/TOTOMI/MIKAWA
   - 수직(우측): SAGAMI / SURUGA+OWARI / MINO+KAI / OMIGAISE / IZU
2. 알파 컬럼 분석으로 각 라벨 bbox 정밀 산출 (5개 수직 컬럼 + 7개 수평 행)
3. `Griun_PolSensibility-Rg.ttf`로 한글 렌더링 → 원본 bbox 동일 위치에 배치
4. `kr_textures/ui/1823D39C0279886B.png` 갱신 + `C:/game/vita3k/textures/import/PCSE00240/`로 동기화
5. `texture_localize_config.json`에 regions 14개 + translations 매핑 추가, status="done"
6. `kr_textures/ui/_notes/1823D39C0279886B.txt` 노트 작성
7. Vita3K 부팅 sanity 체크 완료

### 매핑
야마시로 / 시나노 / 무사시 / 히다 / 야마토 / 토토미 / 미카와 / 사가미 / 스루가 / 오와리 / 카이 / 미노 / 오미이세 / 이즈

### 주의
- "OMIGAISE" 8글자가 단일 라벨 vs 2-3개 분리 라벨 여부 미확정 — 일단 "오미이세"(近江·伊勢 합산)로 통합 처리. 게임 내에서 두 곳에 따로 표시되면 후속 분리 필요.
- 게임 내 검증은 사용자 세이브 로드 후 지도 화면에서 확인 필요 (자동 진입 비용 과대).

## 2026-04-25: E8E01EAF5D41DB52 스킬 아틀라스 라벨 번역 재검수 (27건 수정)

### 문제
`textures/work/E8E01EAF5D41DB52.json`의 라벨 영어→일본어 매핑이 추정(confidence med/low)으로 되어 있어 27건이 잘못됨. 예: Hazy Slash와 Misty Slash가 서로 뒤바뀜.

### 근거
- `extracted/NinPriPatch_full/{msgsheet,_US/msgsheet}/_itemdata.nms`를 nms_parser로 JSON export
- US↔JP 인덱스 정렬: 스킬 블록은 **US[595]=JP[1638], offset=1043**. 아이템 블록은 1:1 (US[40]=JP[40]=青銅の鏡 등)
- 일본어명을 `translations/proper_nouns.json` items 섹션(edit 필드 우선)으로 한국어로 변환 → 시스템 번역과 자동 일체화
- `朧→오보로`, `家老→가신` 등 의도적 오버라이드는 `edit` 필드로 이미 proper_nouns에서 관리되므로 영향 없음

### 주요 수정
- Hazy Slash ↔ Misty Slash 스왑 복구 (霞斬り=Misty=안개자르기, 分身霞斬り=Hazy=안개자르기 2)
- Vengeance ↔ Retribution, Tornado ↔ Vortex, Faerie Inferno ↔ Faerie Assault 스왑 복구
- Soaring Lark 雲雀→飛燕丸鋸 (종달새→톱날리기)
- Falling Moon/Mirrored Moon 弧月계→月ノ輪계 (고월→달무리 2, 십육야→달무리 3)
- Divine Blade 必殺の刃→星天風車 (필살의 검→나선은하)
- Focus Slash 月下一閃→八丁斬り (달빛베기→채썰기)
- Hell's Gate 地獄独楽→天地一閃 (지옥팽이→천지베기)
- Ground Runner 地走り→地虫 (땅달리기→땅벌레)
- Mountain Gale 烈風走破→巌おろし (강풍→바위치기)
- Tempest 鬼火嵐→烈風走破 (화염폭풍→강풍)
- Chaos Roar 百鬼乱閃 省エネ→幻影雷光 (백귀난섬 절약→섬광)
- 기타 Faerie/Moon 시리즈 넘버링 바로잡음, Sake→般若湯→반야탕

### 검증
수정 후 모든 `src_ja` 값이 `proper_nouns.json` 매핑과 정확히 일치함 (Monster Cat, Demon Child 2개만 PN 미등록이지만 직역 괴묘/귀자 유지).

---

## 2026-04-15: UI 텍스처 수동 한글화 (사용자 직접 편집)

### 완료 텍스처 (kr_textures/ui/)
| 해시 | 내용 | 크기 | 비고 |
|---|---|---|---|
| 73420FAEA9F664FD | 본편 타이틀 "오보로 무라마사" | 1024x512 | 이전 완료 |
| 8EFF960FC088FDD7 | 게임 로고 그림자 제거 | 1024x512 | 이전 완료 |
| ADE2B8B5998887A9 | DLC 부제 "겐로쿠 괴기담" | 256x128 | 이전 완료 |
| DF66CADDABE022E3 | 메인 UI 텍스트 (Victory, Save, Load, Cooking 등) | 512x512 | 신규 |
| A3BE57CE9854B5CC | 스토리/DLC 제목 (영문 부제 한글화) | 1024x1024 | 신규 |
| 3B58B76CBA15E487 | 시스템 UI (Please, Return, 시작, 새게임, Store 등) | 2048x1024 | 카탈로그 미등록, 신규 발견 |
| E4A9FD9D2047280B | 엔딩 "완 결" 텍스트 | 2048x1024 | 카탈로그 미등록, 신규 발견 |

### 진행 상태
- Phase 4 텍스처 한글화: **카탈로그 9개 중 5개 완료 + 신규 2개 = 총 7개 완료**
- 미완료 (카탈로그): 7DC6 (아이템명), E8E0 (스킬명), 74EE (스토리 제목+라벨), 1823 (지역명), 79C9 (오프닝 나레이션)
- 원본 텍스처 정리: textures/text/ 폴더에 10개 텍스트 텍스처 원본 복사 완료

---

## 2026-04-14: 어빌리티 화면 Skill/Effect 깨짐 1차 수정 (font-mapping-repair)

### 문제
어빌리티 화면의 Skill / Effect 열이 `닷맽않딸돕맒 담햝맣`, `묘혔떏뗄맶 땀맒` 형태로 완전 깨짐.
동시에 식당 메뉴·대장간 칼 이름·대사 런타임 치환도 잔재.

### 근본 원인 (RCA)
US 버전 `NinPriPatch/_US/msgsheet/_itemdata.nms`는 EU/JP 파일과 **완전히 다른 인덱스 레이아웃**을 가짐:
- 0-369: 아이템 + 설명 (JP 인덱스와 정렬됨)
- 370-593: 칼 이름(짝수) + 칼 설명(홀수) 쌍
- 594: separator `-`
- 595-1176: **영문 컴팩트 스킬명 테이블** (JP에는 없음)

기존 `tools/build_patch.py`가 US 파일을 `_itemdata` (3565-entry) 번역 테이블로 index-mode 패치 →
영문 스킬명 슬롯에 한글 "금강 팔찌" 등 accessory 이름이 덮여쓰여 **엉뚱한 위치에 Korean bytes 주입**.
어빌리티 화면은 칼 설명(홀수 인덱스) 안에서 "Secret Art:" / "Effect:" 마커를 파싱해
Skill / Effect 열을 추출하는데, 칼 설명이 한글로 바뀌면서 파서가 **랜덤 byte offset**을 읽어 깨짐 발생.

### 수정 (commit ccfdcbc)
`tools/build_patch.py`:
- `rebuild_nms`에 `index_range=(start,end)`, `skip_indices=set(...)` 파라미터 추가
- 새 매치 모드 `index_range` + `copy` 추가
- US `_itemdata` 패치 범위: `index_range=(0, 594)`, `skip_indices={371, 373, …, 593}` (홀수 칼 설명)
- 결과: `_itemdata_US: 482/1177 matched (index_range)`

### 검증 (데이터 레벨)
`patch_patch/_US/msgsheet/_itemdata.nms` 디코드:
| idx | 원문 (EN) | 패치 후 |
|---|---|---|
| 2 | Bamboo Flask | `대나무수통` (Korean) |
| 384 | Peony Blade | `「모란」무라마사` (Korean) |
| 385 | `Attack: 18 / Secret Art: Soaring Lark I / Effect: Attack Boost I` | **영문 원본 유지** |
| 388 | Celestial Origins | `하세베쿠니시게` (Korean) |
| 389 | `Attack: 17 / Secret Art: Divine Blade I / …` | **영문 원본 유지** |
| 608 | Divine Moon I | **영문 원본 유지** (594+ 범위 외) |

### 검증 (라이브 인게임 - 1회 성공 후 Windows 포커스 문제로 반복 실패)
첫 실행에서 어빌리티 화면 Equipment 열이 `하세베쿠니시게 / [아야메] 무라마사 / [모란] 무라마사` 한글 정상 표시 확인.
Skill / Effect 열은 영문 원본이 Korean-overlay 아틀라스로 렌더되어 여전히 읽기 어려움 → Phase 2로 분리.

### 남은 트레이드오프
- ✅ Equipment 열 (칼 이름): 한글
- ✅ 대부분 아이템 이름 (0-369): 한글
- ⚠️ 칼 상세 설명 바닥 텍스트 `공: 18 오의: 비연환톱 …` → **영문으로 되돌아감** (홀수 skip)
- ⚠️ Skill/Effect 열: 영문 원본 (읽기 가능, 깨짐 없음)

### Phase 4-6 완료 (2026-04-14)

**Phase 4 — 대사 "등" 치환 제거 (commit 865dbdf)**
mapping에 없는 95개 한글 syllable이 SJIS 인코딩 실패 → `?` (0x3F) →
런타임 오버레이 셀 255(=등)에서 렌더 → `따윈`→`따등` 깨짐.
`translations/char_substitutions.json` 생성 (unmapped → phonetic nearest: 윈→위, 똥→또, 맘→마 등)
+ `build_patch.py` encoder fallback 단계에 사전 매치 추가.
결과: `따위 요만큼도` 정상 표시.

**Phase 5 — 소바 가게 JP kanji → 한글 (commit 865dbdf 일부)**
가게 메뉴는 폰트 atlas `A8E6FDD162258699` 사용 (기존 overlay 미적용).
`auto_font_import.py` 세션 detect에 걸려 이번에 overlay 생성.

**Phase 6a — sysmsg 오번역 수정 (commit 140409d)**
sysmsg[770-778] 항목이 Wii scemsg 병합 잔재로 **장소/캐릭터 이름**(『이누가미 겐시로』, 「무사시」에도 성곽 해자 등)이 음식명 자리에 들어가 있었음. `sysmsg_main[495-515]`의 정상 번역으로 8 entry 재동기화.
결과: `쌀밥 / 자루 소바 / 청어 소바 / 키츠네 우동` 정상.

**Phase 6b — 덴 글자 복구 (commit d08e145)**
`덴`=0x8AF1 → 로컬 셀 224. 그런데 이 셀은 ASCII space(0x20)가 렌더되는 위치라 hd_font_import이 **transparent로 클리어** → 덴 글리프 증발. `덴푸라 우동` → `푸라 우동`, `덴고로` → ` 고로`.
덴을 로컬 960 (0x8EE1, ASCII zone 선두, 실제로 아무 글리프 미사용)으로 재배치.
`kr_sjis_mapping.json` 수정 + auto_font_import / hd_font_import 재생성.
결과: `덴푸라 우동` 정상 표시.

---

### Phase 3 완료 (commit 9cfc94d, 사용자 확인 2026-04-14)
블레이드 설명(홀수 371-593) 한글 복구 — `skip_indices` 제거.
스킬명 테이블이 Korean이라 Ability 파서가 description 대신 skill-ID로 조회.
결과: Forge/Equipment 상세 하단 `공: 18 오의: 비연환톱 효: 공격 강화…` 한글 정상 + Ability 화면 유지.
매치 건수 773 → 885 (+112 description).

### Phase 2 완료 (commit 673cf8f, 사용자 확인 2026-04-14)
NinPriPatch US의 스킬명 테이블(595-1176)과 `_itemdata_main`(878 entries) 사이의
**+8 인덱스 시프트를 경험적으로 확증** (22개 샘플 - Misty Slash→안개자르기, Divine Moon→월광 등).

`build_patch.py`에 `custom_idx` 매치 모드 + `us_itemdata_hybrid` 빌더 추가:
- `[0, 594)` ∩ ¬(홀수 371-593): `_itemdata[i].ko`
- `[595, 1177)`: `_itemdata_main[i-8].ko`

결과: `US[662] = 나선은하`, `US[608] = 월광`, `US[595] = 안개자르기` 등.
사용자 실기 확인: **어빌리티 화면 Skill/Effect 열 정상 한글 표시**.

---

## 2026-04-13: 전각 문자 렌더링 깨짐 수정 (fullwidth-normalize)

### 문제
사용자 스크린샷에서 무기 설명·상태 화면의 전각 문자가 한글 글리프로 깨짐:
- `：` (full-width colon) → `봐`
- `（` → `사`, `）` → `삭`
- `\u3000` (전각 공백) → `볶` (`붐`처럼 보임)
- `１２３...` (전각 숫자) → `웨`, `위`, `윗`, `유` 등

### 원인 (경험적 발견)
게임이 SJIS 0x81xx/0x82xx 바이트를 폰트 텍스처의 `local_cell = sjis_cell + 448` 위치에서 렌더링.
Korean 글리프가 해당 위치에 있어 엉뚱한 한글로 표시됨.
- `：` (0x8146) → cell 6 → local 454 = 봐
- `（` (0x8169) → cell 41 → local 489 = 사
- `）` (0x816A) → cell 42 → local 490 = 삭

Python `c.encode('shift_jis')` fallback이 이 raw SJIS 바이트를 출력한 것이 문제.

### 수정 (`tools/build_patch.py`)
- `FULLWIDTH_NORMALIZE` 딕셔너리 추가 — 전각→ASCII 반각 매핑
- `_normalize_text()` 전처리로 encode 전에 변환
- 대상: 전각 ASCII (`：（）！？％＋－＝／＊＃…`), 전각 숫자 `０-９`, 일본 문장부호 (`、。・「」『』`), 전각 공백, 특수기호 `…◆`
- 결과: 모든 전각 문자가 `ASCII_SJIS_MAP` (pos 960+) 경로로 encode → 폰트 텍스처의 ASCII 영역에서 정상 렌더링

### 검증 (Vita3K 실행 + 스크린샷 비교)
- Before: `상태붐정상`, `공격봐 1 2`, `사용조건 사 힘봐3 체력봐3`
- After:  `상태 정상`, `생명력 50 회복 생기 10 획득` — 깨짐 없음

### 부산물
- `@#（81）` 형태 제어 코드: 전각→반각 정규화 후 기존 `@#(\d+)` 정규식에 매칭 → 올바르게 raw bytes로 보존

### 알려진 남은 이슈 (deferred)
게임 런타임 `%D` 포맷 치환 (세이브 시간 등): 게임이 raw ASCII 0x30-0x39를 출력 → 폰트 텍스처 cell 240-249에서 렌더링 → 한글 `둔/둘/둠/둥/둬/뒤/뒷/드/득/든` 표시.
해당 한글은 사용빈도 매우 높음 (`들` 459회, `득` 227회, `드` 181회, `든` 139회) — 텍스처 overlay로 교체하면 번역 손상.
증상: "Time 둘시간 드분" (= "1시간 7분"), 세이브 메뉴의 "Blades Owned" 숫자.
해결은 게임 바이너리 분석 or alt font texture 탐색 필요.

### 빌드 결과
- `build_patch.py`: 전 NMS 정상 빌드 (match rate 변화 없음, 인코딩 교체만)
- `cpk_patch.py`: NinPri +149KB, NinPriPatch +264KB
- Vita3K 부팅/세이브 로드/메뉴 탐색 정상

---

## 2026-04-13: 지명·Act 라벨·오역 대량 수정 (place-name-fix feature)

### 문제 요약
- DLC 진입 시 장면 전환 지명 헤더 깨짐
- 스토리 선택 Act 라벨 깨짐 (범위 밖 SJIS 바이트)
- 일부 번역이 다른 텍스트로 표시 (CRLF/LF 불일치)
- `武蔵` → "사무라이시"(5자) 오역, `無事` → "사무라이히/하" 오역

### PDCA 진행 (Option C — 데이터 수정 + 감사 도구)
- **Plan**: `docs/01-plan/features/place-name-fix.plan.md`
- **Design**: `docs/02-design/features/place-name-fix.design.md`
- **Do**: 5단계 구현 완료

### 구체 수정
1. **오역 제거**
   - 武蔵 → 무사시 일괄 치환 (32 엔트리, scemsg/sysmsg)
   - 無事 → 무사히/무사하/무사했 (12 엔트리, scemsg)
2. **Act 라벨 재인코딩**
   - ASCII 숫자(0x8EF3~8EF8 OOR) → 전각 숫자(0x8251~0x8256, JP 기호 페이지)
   - "제2막~제7막" → "제２막~제７막"
   - 줄거리 요약 내 Act 참조도 동일 교체 (28 엔트리)
3. **DLC 지명 번역 추가**
   - sysmsg #703~778 `ko=""` → 76개 엔트리 Korean 추가
   - `「미카와」 도카이도 후지카와・아카사카 간 가도` 등 새 전환 헤더
4. **ASCII 구두점 전각화 (sysmsg만)**
   - `-` → `・`, `!` → `！` (38 엔트리)
5. **CRLF/LF 라인엔딩 정규화**
   - NinPri(`\r\n`) vs NinPriPatch_full(`\n` 혼재) 불일치 → 매칭 실패
   - `build_patch.py` 내 `_norm()` 헬퍼로 매칭 시 통일
   - sysmsg 836→899 매칭, scemsg 17개 추가 매칭

### 신규 도구
- `tools/audit_oor.py` — 패치 NMS의 범위 밖 SJIS 바이트 감사
  - `--summary`, `--baseline`, `--output json` 지원
  - baseline: `docs/03-analysis/oor_baseline.json` (전체 17,329 메시지 중 8,143개 OOR)
- `tools/capture_scene.py` — Vita3K 단계별 장면 전환 캡처

### 검증
- 스토리 선택 Play Style 설명 "마음 편히 대폭주하기 위한 유파입니다..." 정상 렌더링
- 타이틀 "오보로 무라마사" 부제 정상
- DLC 진입 후 세이브/로드 UI 정상
- scemsg 2186/2247, sysmsg 899/965 매칭

### 미해결 / 후속 과제
- OOR 시스템 이슈 3,328 메시지 (ASCII `.` `,` `'` 등이 OOR 셀로 매핑)
- 폰트 오버레이 커버리지 1024-1053 (lowercase a-z)
- 더 깊은 DLC 시나리오(2~4) 전수 대사 검증

## 2026-04-13: DLC 난이도 화면 배경 텍스처 깨짐 수정

### 문제
- DLC 난이도 선택 화면(Legend/Chaos) 좌우 배경에 한글 폰트 아틀라스가 그대로 노출
- 원인: `hd_font_import.py`의 `font_hashes` 리스트에 `87B72F6DB3C3FBDC`가 잘못 포함됨
- 해당 해시는 실제로는 폰트가 아니라 **식물/풀숲 배경 텍스처** (HD 팩 원본에서 확인)

### 해결
- `tools/hd_font_import.py`: `font_hashes`에서 `87B72F6DB3C3FBDC` 제거 (`6706A53E1D94C16E`만 남김)
- HD 팩 원본(`87B72F6DB3C3FBDC.png`)을 import 폴더에 복원 (2048 리사이즈 + pngquant → 597KB)
- 실제 폰트 텍스처: `6706A53E1D94C16E` (HD 팩 ASCII+Kanji), `8665CE082D339B33` (세션 Kanji)

### 검증
- DLC 난이도 화면 배경 정상 렌더링 확인 (`screenshots/step5_difficulty_settled.png`)
- 좌우 배경이 폰트 아틀라스 대신 원본 식물/UI 배경으로 표시

## 2026-04-13: 공백 반칸 렌더링 복구

### 문제
- 이전: space(' ')를 ASCII_SJIS_MAP의 960+ 슬롯으로 리맵 → 게임이 한글 셀(32px 풀폭)로 렌더링 → 공백이 한칸 크기
- "오보로  무라마사를  플레이합니다" 형태로 과도한 여백

### 해결
- `tools/build_patch.py`: `_build_ascii_sjis_map()`에서 0x20(space)만 예외 처리, 1-byte 0x20으로 출력
- `tools/auto_font_import.py`, `tools/hd_font_import.py`: KANJI 텍스처 local cell 224 (= 192+0x20, pixel x=0,y=224 32x32 영역) 투명 클리어
- 게임이 raw 0x20을 position=192+0x20=224에서 반폭(16px) 렌더링 → 정상 반칸 공백
- 다른 ASCII 문자(!, ?, 숫자 등)는 여전히 960+ 2-byte 리맵 유지

### 검증
- DLC 선택 화면 하단 시스템 메시지 "오보로 무라마사를 플레이합니다" — 반칸 공백 정상 렌더링
- 이상한 글자 노출 없음 (cell 224가 투명하게 비어 있음)
- `screenshots/dlc_select_spacecheck.png`

## 2026-04-13: Wii 한글 패치 기반 번역 전면 교체

### 작업 내용
- Wii USA판 한글 패치(사람이 검수한 번역)를 기준으로 Vita 번역 교체
- JP 원문 매칭으로 1116개 본편 scemsg 대사 전부 Wii 번역으로 대체
- 3줄/18자 제약에 맞춰 자동 재포매팅 (`tools/apply_wii_translations.py`)
- `tools/polish_dlc.py`로 DLC 번역 고유명사 통일 (카가미가, 해골곡, 쓰나요시 등)

### 교체 통계 (최종, sysmsg 안전 스킵 반영)
- scemsg: 1115 entries Wii 번역 + DLC 17 term polish
- sysmsg/sysmsg_main: 0 (SKIP — 파일 정렬 안됨)
- _itemdata: 541, _itemdata_main: 628 entries (설명 줄 수 초과 시 SKIP)
- scename_main: 67 entries (인명/지명 고유명사)

### 고유명사 주요 변경
- 사무라이 → 무사
- 해골 골짜기 → 해골곡
- 카가미 가문 → 카가미가
- 도쿠가와 츠나요시 → 도쿠가와 쓰나요시
- 피에 미친 비사문 → 치구루이비샤몬
- 시카미 단조 → 시카미 단죠
- 막걸리 → 도부로쿠, 감 → 홍시, 귤 → 밀감
- 치유환/회복환/웅담환 → 치료환약/회복환약/곰환약

### 테스트
- 빌드/설치/Vita3K 실행 자동화 성공
- `screenshots/genroku_dialogue.png`: 겐로쿠 Legend 선택 화면 Wii 스타일 한글 렌더링 확인

## 2026-04-11: 대사(scemsg) 미출력 버그 해결

### 근본 원인
- **NinPriPatch.cpk가 NinPri.cpk의 scemsg를 완전히 오버라이드**
- NinPriPatch = 업데이트 패치 (본편+DLC 대사 2,178개 US / 2,252개 JP)
- 기존에 NinPri.cpk만 패치 → 게임이 NinPriPatch의 원본 scemsg를 로드 → 패치 무시
- cpk_extract 버그: NinPriPatch scemsg(268KB)를 480B로만 추출

### 해결
- NinPriPatch에서 전체 scemsg 수동 추출 (CRILAYLA 디컴프레스)
- build_patch.py: NinPriPatch_full/scemsg_full.nms를 템플릿으로 사용
- NinPriPatch.cpk 패치: 본편 대사 1,116개 번역 적용 (DLC ~1,062개 미번역)
- 대사 렌더링 정상 확인 (폰트 텍스처 문제 아님 확인)

### CPK 로딩 우선순위 (확인)
```
NinPriPack1~4.cpk → DLC 에셋 (그래픽/사운드/맵, msgsheet 없음)
NinPriPatch.cpk   → 업데이트 패치 (본편+DLC 대사, NinPri 오버라이드)
NinPri.cpk        → 베이스 게임 (NinPriPatch가 덮어씀)
```

## 2026-04-10: DLC + 본편 미커버 텍스처 397개 AI 업스케일 성공

### 성과
- **FTX 추출 도구** (`tools/ftx_extract.py`): FTEX/GXT → PNG 디코딩 (DXT5/BC3 + Morton unswizzle)
- **일괄 업스케일 도구** (`tools/batch_upscale.py`): Real-ESRGAN ncnn-vulkan 기반
- DLC 4개팩 377개 + 본편 미커버 20개 = **397개 전부 업스케일 완료** (7.7분, 에러 0)
- 출력: max 2048px, 총 902MB

### 비교 분석 결과
- HD 팩(Muramasa Complete 2.0): 2,139개 → 본편 96%(482/502) 커버
- 미커버: 본편 20개 (보스/요괴/GUI) + DLC 377개 (Pack1~4 전체)
- 비교 방식: perceptual hash (16x16 thumbnail, hamming distance ≤ 30)

### 파이프라인
1. `ftx_extract.py` — FTX → PNG (DXT5/DXT3 디코딩 + Vita unswizzle)
2. `batch_upscale.py` — Real-ESRGAN animevideov3 4x/2x → max 2048 → pngquant
3. 출력 위치: `output/dlc_hd/Pack1~4/`, `output/main_hd/`

### 남은 단계
- Vita3K 해시 매핑: DLC 실행 → export 해시 수집 → import 폴더 배치
- 본편 미커버 20개도 동일 방식으로 해시 매핑 필요

## 2026-04-10: HD 텍스처 팩 적용 + 한글 폰트 고화질화 성공

### 성과
- **Muramasa Complete 2.0** (Plaidray/xibalva) HD 텍스처 팩 Vita3K import 적용
- 2139개 텍스처를 **5.2GB → 829MB**로 최적화 (max 2048 다운스케일 + pngquant 8bit 양자화)
- HD 폰트 텍스처(4096x4096) 위에 한글 88px 렌더링 → 2048x2048 다운스케일
- 게임 실행 확인 완료 (60 FPS, HD 텍스처 + 한글 정상 출력)

### 파이프라인
1. HD 팩 원본 (Vita3K 해시 형식) → PIL resize(max 2048) → pngquant(quality 70-95) → import 폴더
2. 폰트 텍스처 2개(87B72F6DB3C3FBDC, 6706A53E1D94C16E)는 HD 베이스 위에 한글 오버레이
3. 나머지 폰트(8665CE082D339B33, E690E190AA5C798F)는 export 기반 1024 처리
4. 도구: `tools/hd_font_import.py`

### 핵심 정보
- HD 팩 위치: `C:/Users/taro1/Downloads/Muramasa Complete 2.0/PCSE00240/Best/`
- import 위치: `C:/game/vita3k/textures/import/PCSE00240/`
- 폰트 해시 충돌: 87B72F6DB3C3FBDC, 6706A53E1D94C16E (HD팩에 포함 → 한글로 교체)

## 2026-04-10: Vita3K 텍스처 교체로 한글 폰트 렌더링 성공

### 핵심 성과
- **한글이 게임 내에서 렌더링됨** - 갈, 감, 곽, 꿈 등 실제 한글 글리프가 게임 대화 창에 표시
- **955자 전체 한글이 2개 폰트 페이지에 수용** (page 0: 48자, page 1: 907자)
- **FTX/DXT5/스위즐 우회** - Vita3K 텍스처 import로 PNG만 수정하면 됨

### 셀 매핑 공식 (확정)
```
cell = 224 + (b1 - 0x81) * 188 + b2_offset
b2_offset = b2 - 0x40 (b2 < 0x80)
b2_offset = b2 - 0x41 (b2 >= 0x80, 0x7F 스킵)
```
- 한글 SJIS 범위: b1=0x85~0x8A (US 버전에서 미사용 확인)
- 가(0x85,0x40) → cell 976 (page 0, local 976)
- 힘(0x8A,0x4E) → cell 1930 (page 1, local 906)

### 폰트 텍스처 (Vita3K export/import)
| 해시 | 용도 | 형식 |
|------|------|------|
| `882CCAF6763B8B59` | 일반 폰트 page 0 (cells 0-1023) | white RGB + alpha glyph |
| `09498223CD6E047B` | 일반 폰트 page 1 (cells 1024-2047) | white RGB + alpha glyph |
| `6706A53E1D94C16E` | 볼드/아웃라인 폰트 | RGBA glyph |

### 검증 방법
1. 녹색 틴트 → 텍스처 import 동작 확인
2. 상하반전 → 6706A53E1D94C16E가 폰트 텍스처 확인
3. 진단 텍스처 → 셀 번호 시각화로 매핑 공식 검증
4. 한글 import → 게임 내 한글 렌더링 확인

### 입력 자동화
- scancode 키 입력: `keybd_event(0, scancode, KEYEVENTF_SCANCODE, 0)`
- X키=scancode 45, Esc=1
- 앱 리스트: Esc → green dot 찾기 → 65% x에서 클릭×2

### 남은 이슈
- **Yes/No 다이아몬드 터치**: 원본 게임에서도 클릭 안 됨 (Vita3K 터치 입력 이슈)
- 볼드 폰트 page 1 해시 미확인 (page 0만 48자 처리)
## 2026-04-12: Wii Muramasa 한글 패치 wbfs 추출

### 성공
- Wiimms ISO Tools(wit) 로 RSFE7U (USA Wii) wbfs 추출 완료
- Vanillaware FCMP 압축 디컴프레서 구현 (LZSS 서큘러 버퍼, 12+4 비트, LSB)
- NMS 메시지 파일 10개 전부 디컴프레스 + 파싱 → 4,920개 메시지 JSON 추출
- Wii JP는 순수 Shift-JIS로 완벽 복원 확인 (히라가나/카타카나 검증)
- `translations/wii_reference/` 디렉토리에 저장

### 부분 완료 (향후 필요)
- FTX 텍스처 103개 (fonts + GUI) FCMP 디컴프 완료하지만
  TPL 텍스처 디코딩 실패 (wimgt 거부, 커스텀 Vanillaware 포맷)
- `extracted_wii/ftx_decomp/` 에 바이너리 보관

### 핵심 발견
- Wii Korean 패치는 PS Vita와 동일하게 커스텀 SJIS 매핑 사용
- DLC는 Wii에 없음 (본편 1,116개 대사만 참고 가능)
- NMS 구조는 PS Vita와 거의 동일 (헤더 레이아웃 동일)

### 새 도구
- `tools/fcmp_decompress.py` - FCMP 디컴프레서
- `tools/extract_wii_messages.py` - NMS → JSON 변환
- `tools/wit/` - Wiimms 툴 (wbfs 추출용)


## 2026-04-25: 지명 텍스처 50장 한글화 완료

### 작업 범위
- `kr_textures/ui` 폴더의 빨간/검은 배경 지명 텍스처 50장 한글화
- 백업: `textures/place_name_originals/` (원본 50장 보관)
- 폰트: 그리운 경찰감성체 (`fonts/Griun_PolSensibility-Rg.ttf`)

### 분류 및 처리
| 분류 | 개수 | 처리 방식 |
|---|---|---|
| Simple (1 banner + 1 box) | 29 | 자동 detect + 매핑 + 렌더링 |
| Complex Group A (1 banner + 1 box, false positive 있음) | 6 | Simple 방식 |
| Complex Group B (multi-banner) | 15 | bbox idx 수동 매핑 + 캐릭터 이름 처리 |

### 주요 매핑 파일
- `translations/place_name_mapping.json` — 텍스처별 한글 매핑
- `translations/place_name_regions.json` — 자동 detect 영역
- `translations/place_name_white_kanji.json` — 캐릭터 이름 흰 글자 영역

### 핵심 규칙
- 빨간 배너: 일본어와 동일 방향 (회전된 상태) → 한글 세로쓰기
- 검은 박스 (frame): 가로/세로 방향 자동 감지하여 그에 맞춰 한글 배치
- brush stroke + 흰 캐릭터 이름: 흰 글자 영역 별도 detect 후 한글 덮어쓰기
- 매핑 없는 영역: 색상 클리어 (일본어 잔존 방지)

### 캐릭터 이름 매핑 (jp_messages/proper_nouns 기반)
- 大神徳川綱吉 → 도쿠가와 쓰나요시
- 雪之丞 → 유키노조
- 血狂毘沙門 → 치구루이비샤몬
- 綱釜千代子 → 쓰나가마 치요코
- 大根 → 다이콘

### codex 검증
- Simple 29장 + Complex A 6장: 모두 OK
- Complex B 15장 v3 (일본어 완전 제거): 게임 내 검증 필요

### 미해결 / 보류
- 매핑 없는 흰 글자 영역 (일부 텍스처): 빈 영역으로 처리됨
- E210275AFFF0A8D8 (이즈): 식별 후 매핑됨

## 2026-05-10 — Vita3K export에서 신규 텍스트 텍스처 6개 발견·이동
- 게임 진행 후 export 폴더에 246개 텍스처 (이전 기준 대비 236개 신규)
- alpha-text 휴리스틱 + 컨택시트 검토로 텍스트 후보 식별
- 사용자 작업 폴더(`textures/originals/` + `textures/text/`)에 복사 완료:
  - **04110A0F74BE6991** (256×256) — 지명 한자 아틀라스 (尾張/武蔵/伊賀 등 16개)
  - **15CF750523FBB7C6** (512×512) — 鬼 한자 + UI 심볼
  - **17BBEF37CC65904A** (512×512) — Hashimoto/Basiscape 크레딧
  - **9F518FC3E233B9DE** (256×256) — 상점/툴팁 UI 패널 (開/罠 한자 + 보물상자/검)
  - **ECB628336E68D6AA** (256×128) — Clear/X UI 버튼 + 한자 심볼
  - **EDA6F03EC4E141EE** (128×128) — PS Vita SELECT/START 라벨
- `translations/texture_localize_catalog.json`에 6개 항목 추가, summary high=12/med=4/low=1로 갱신
- 한글화 불필요 항목 6개도 catalog `_recent_additions.skipped`에 기록 (브랜드 로고, 디지트, 폰트 스프라이트 등)
- 사용자 언급 "식당/상인 메뉴 항목" 자체 텍스트는 미발견 — 동적 폰트 시스템으로 렌더링되는 것으로 추정. 9F518FC3 (상점 UI 패널)이 가장 근접

## 2026-05-10 (2회차) — 식당/상인 메뉴 UI 텍스처 5개 발견·이동
- 사용자가 식당/상인 화면 진입 후 export 갱신 (246→677개, 431개 신규)
- 사용자 스크린샷 3장 (저장 UI, 상인 메뉴, 소바 식당 메뉴) 분석
- 작업 폴더(`textures/originals/` + `textures/text/`)에 복사:
  - **247C255A400261FF** (256×256) — 식당(Soba Shop) 메뉴 UI: Inventory/Sold Out/Money/Meals/Menu/Price/mon/ryo + 売切
  - **547720A3B20C12AB** (256×256) — 상인 메뉴 UI: + Restaurant/料亭
  - **FFFFD99DCD90D546** (256×128) — 상점 외관 노렌/간판 한자 사인
  - **2E88068C58DD36D5** (1024×1024) — ASCII 폰트 아틀라스 (영문/숫자/기호 그리드)
  - **A8E6FDD162258699** (1024×1024) — KANJI 폰트 아틀라스 (수백 한자 그리드)
- catalog summary: high 12→16, med 4→5, total 17→22로 갱신
- 사용자 요청 'sold out 같은 단어'는 247C255A/547720A3 두 아틀라스 모두에 'Sold Out'으로 사전 렌더링되어 있음 — 한글로 교체 가능
- A8E6FDD162258699 폰트가 메뉴 항목 한자 렌더링에 사용되는 것으로 추정 — 기존 한글 SJIS 매핑(0x89CD-0x8EE0) 적용 가능성 검증 필요

## 2026-05-10 (3회차) — 식당/상인 메뉴 UI 한글 번역 + A8E6FDD1 한글 폰트 적용
### 외부 AI 교차 검증 (codex + gemini)
- 결론 일치: 화폐 단위 냥/문 (existing %d냥%d문 포맷), Sold Out → 품절 (existing translation)
- A8E6FDD1 가설 일치: 기존 게임 폰트와 동일 데이터, 메뉴 화면 전용 인스턴스 (auto_font_import 적용 가능)

### 폰트 한글화
- `tools/.font_hashes.json`이 이미 A8E6FDD162258699 포함 → auto_font_import.py 실행으로 한글 글리프 959자 자동 주입
- 메뉴 항목명 한자(자루소바, 청어소바, 덴푸라소바 등)가 NMS의 한글 SJIS 시퀀스를 통해 한글 출력 예정

### 사전 렌더 메뉴 UI 한글 번역
- **247C255A400261FF** (식당/Soba Shop): 9개 영문 단어 → 한글
  - Inventory→보유, Sold Out→품절, Money→소지금, Soba Shop→소바집,
    Meals→식사, Menu→메뉴, Price→가격, mon→문, ryo→냥
- **547720A3B20C12AB** (상인/Restaurant): 9개 영문 단어 → 한글
  - Restaurant→식당, 나머지 247C와 동일 단어는 동일 한글
- 폰트: Griun_PolSensibility-Rg.ttf (붓글씨 스타일)
- texture_localize.py로 영역 클리어 + 한글 렌더링 → import + kr_textures/ui/ 양쪽 저장
- 전체 단어 영역 좌표를 알파 connected-component 검출로 측정 후 v2에서 미세조정

### 구현 위치
- Vita3K import: `~/Library/Application Support/Vita3K/Vita3K/textures/import/PCSE00240/`
  - 247C255A400261FF.png (45KB)
  - 547720A3B20C12AB.png (40KB)
  - A8E6FDD162258699.png (269KB - Korean overlay)
- 리포 사본: `kr_textures/ui/` 동일 파일

### 다음 검증 단계
- 사용자가 Vita3K 재시작 → 식당/상인 메뉴 화면 진입 → 한글 표시 확인
- 미세 위치 조정이 필요하면 사용자 스크린샷 추가 제공 후 좌표 수정

## 2026-05-10 21:53 — codex 위임으로 메뉴 UI 한글 재작업 완료
### 위임 사유
- 247C255A 식당 UI 글씨 잘림 발생 (v2 좌표가 거칠게 측정됨)
- 547720A3가 사용자 상인 화면(s5)에 미적용 — 다른 hash 의심
- 사용자 요청: "이미지 편집은 codex가 더 잘하니까 codex한테 시키자"

### codex 작업 결과
1. **247C255A v3** (식당, Soba Shop): 알파 connected-component bbox 기준 정밀 좌표 + 폰트 재산정. 글씨 잘림 해소. 9개 단어 한글화 유지.
2. **상인 UI 진짜 hash 식별**: `1D6742BBC0DDB7EC` (256x256). 6개 알파-only-white 후보 중 식별. 사용자 스크린샷 s5의 "Money/Item/Inventory/Price/mon"과 일치
3. **1D6742BBC0DDB7EC 한글화**: Inventory→보유, Sold Out→품절, Item→품목, Price→가격, Money→소지금, mon→문, ryo→냥
4. **547720A3 재분류**: Restaurant/Meals 식당류 텍스처(상인 아님)로 description 정정. 한글 번역은 유지(요리집/식당 화면이 등장하면 적용될 예정)

### 출력 파일
- 식당: `kr_textures/ui/247C255A400261FF.png` (42KB) + Vita3K import 동일
- 상인: `kr_textures/ui/1D6742BBC0DDB7EC.png` (35KB) + Vita3K import 동일
- 식당류: `kr_textures/ui/547720A3B20C12AB.png` (40KB) — 변경 없음
- config: `translations/texture_localize_config.json`에 1D6742BBC0DDB7EC 항목 추가, 247C255A regions v3 갱신

### 검증 (codex 자체 검증)
- JSON 파싱 정상
- 모든 PNG 256x256
- repo/import byte 동일
- visible RGB는 흰색 일관, alpha=0 픽셀은 (0,0,0,0)
- macOS의 `tools/vita3k_ctrl.py status`는 windll 의존으로 실패 → 인-게임 검증은 사용자 몫

### 다음 검증
- 사용자가 Vita3K 재시작 → 소바집 식당 화면 (s3/s6 reproduce) → 글씨 잘림 없는지 확인
- 상인 화면 (s2/s5 reproduce) → "보유 | 가격 | 품목 | 소지금 | 문" 한글 출력 확인
