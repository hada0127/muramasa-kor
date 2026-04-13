# SUCCESS - 성공한 작업 기록

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

