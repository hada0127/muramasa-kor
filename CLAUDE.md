# Muramasa Rebirth 한글 패치 프로젝트

협업자를 위한 입문 문서는 [README.md](README.md)에서 시작할 것.
이 파일(CLAUDE.md)은 Claude/AI 에이전트가 작업 시 반드시 따라야 할 절차·규칙·기술 상세를 담는다.

## 참고 문서
- [README.md](README.md) — 프로젝트 소개·셋업·빌드 (협업자용)
- [한글패치 대안 방법 연구](.claude/research_korean_patch_methods.md) — Vita3K 텍스처 교체, psxtools FTX 추출, Wii 패치 참고 등
- [Wii 한글 패치 참고 자료](wii/README.md) — Wii USA판 한글 패치 추출물 (메시지/폰트/UI 텍스처)
- [PDCA Plan 문서](docs/01-plan/features/) — 기능별 계획서 (korean-localization, place-name-fix, scemsg-font-fix)
- [PDCA Design 문서](docs/02-design/features/) — 구현 설계
- [PDCA Analysis 문서](docs/03-analysis/) — OOR baseline, Wii 교차검증

## 작업 기록 (필수 준수)
- 모든 작업 시작 전 [todo.md](.claude/todo.md)에 계획 기록
- 작업 성공 시 [success.md](.claude/success.md)에 결과 기록
- 작업 실패 시 [fail.md](.claude/fail.md)에 원인과 시도 내용 기록
- 매 대화 시작 시 세 파일을 읽고 현재 상태를 파악할 것

## Wii 한글 패치 참고 자료 (필수 활용)

번역/용어/폰트 관련 작업 시 `wii/` 폴더의 Wii USA판 한글 패치 자료를 **먼저 참고할 것**.

### 언제 참고해야 하는지
- **번역 문구 고민 시** → `wii/messages/kr/*.json`에서 같은 문맥의 번역 예시 찾기
- **용어/고유명사(인물·지명·아이템)** → `wii/messages/kr/_itemdata.json`, `scename_US.json`
- **UI/메뉴 번역** → `wii/messages/kr/sysmsg.json`, `wii/textures/kr/*.png` (시각 레퍼런스)
- **한글 폰트 디자인 참고** → `wii/fonts/kr/font_p0-3.png` (이롭게 계열 폰트 글리프)
- **JP 원문 대조** → `wii/messages/jp/*.json` (같은 인덱스 매칭)

### wii/ 폴더 구조
```
wii/
├── messages/jp/  (5개 JSON) — 일본어 원본, 각 엔트리 hex+shift_jis
├── messages/kr/  (5개 JSON) — 한글, 각 엔트리 hex+korean(완전 디코드됨)
├── fonts/jp/     (12개 PNG) — 일본어 폰트 아틀라스
├── fonts/kr/     (12개 PNG) — 한글 폰트 아틀라스 (2,350자 KS X 1001)
├── textures/jp/  (160개 PNG) — UI 원본
└── textures/kr/  (115개 PNG) — 한글 UI
```

### 주의사항
- DLC(4개 에피소드)는 Wii에 없음 — 본편 1,117개 scemsg 대사만 참고 가능
- Wii 한글 디코딩 공식은 역공학 완료 (`tools/wii_hangul_decode.py`)
  - `wii/messages/kr/*.json`의 `korean` 필드에 완전 디코드된 텍스트 있음
- PS Vita 번역과 직접 충돌 가능 — Wii는 참고용, 최종 결정은 PS Vita 맥락 우선

## 작업 규칙

- 각 작업(기능 구현, 버그 수정, 리팩토링 등)이 완료되면 즉시 git commit 할 것
- 여러 작업을 묶지 말고, 완료된 작업 단위로 바로바로 커밋
- **패치 작업 후 반드시 직접 Vita3K를 실행하여 결과를 확인할 것. 사용자에게 확인을 요청하지 말 것.**
  - 빌드 → 설치 → Vita3K 실행 → 게임 시작 → 스크린샷 캡처 → 결과 확인까지 자동으로 수행
  - 문제가 있으면 스스로 수정하고 다시 테스트. 해결될 때까지 반복

## 이미지 읽기 규칙 (필수 준수)

- **Read 툴로 이미지를 직접 읽으면 안 됨** — PNG/JPG가 2000px 또는 8000px를 초과하면 API 에러 발생
- **항상 먼저 리사이즈 후 읽을 것**:
  1. Python(PIL)로 이미지 크기 확인
  2. 긴 변이 **1500px 초과**이면 긴 변을 1500px로 축소한 임시본을 `temp/preview/` 에 저장
  3. 그 임시 파일을 Read 툴로 읽기
- 원본 분석이 필요하면 numpy/PIL로 수치 분석하고, 시각 확인용으로만 리사이즈본을 Read
- 예시 스니펫:
  ```python
  from PIL import Image
  from pathlib import Path
  src = Path("screenshots/xxx.png")
  img = Image.open(src)
  if max(img.size) > 1500:
      img.thumbnail((1500, 1500))
      out = Path("temp/preview") / src.name
      out.parent.mkdir(parents=True, exist_ok=True)
      img.save(out)
      # Read 툴은 out 경로 사용
  ```

## Vita3K 게임 실행 자동화 (필수 준수)

### 게임 실행 절차
패치 테스트 시 항상 아래 절차를 따라 **직접 게임을 실행**할 것. 사용자에게 수동 실행을 요청하지 말 것.

```
1. python tools/vita3k_ctrl.py close     # 안전 종료
2. (패치 설치)
3. Vita3K.exe 실행 (GUI 모드, -r 플래그 사용 금지)
4. Esc 키로 ImGui 앱 목록 열기
5. 이미지 분석으로 green dot(호환성 표시) 찾아서 Muramasa 행 더블클릭
6. LiveArea에서 이미지 분석으로 "시작" 흰색 텍스트 찾아서 클릭
7. 타이틀바에 "Muramasa Rebirth" + "FPS" 나올 때까지 대기
8. 게임 로딩 후 mss로 스크린샷 캡처
```

### 자동 실행 코드 패턴
```python
# 1. Esc로 ImGui 열기
pyautogui.click(window_center_x, window_center_y)
time.sleep(0.5)
pyautogui.press('escape')
time.sleep(2)

# 2. 스크린샷 → green dot 찾기 → 더블클릭 (리스트 최하단)
arr = np.array(Image.open(screenshot))
for y in range(ih//2, ih):
    for x in range(iw//10, iw//4):
        r,g,b = arr[y,x,:3]
        if g > 100 and r < 80 and b < 80:  # green dot
            pyautogui.doubleClick(window_left + iw//2, window_top + y)
            break

# 3. LiveArea 스크린샷 → 시작 흰색 텍스트 찾기 → 클릭
arr2 = np.array(Image.open(livearea_screenshot))
for sy in range(h*35//100, h*65//100):
    for sx in range(w*60//100, w*85//100):  # 오른쪽 영역만 탐색!
        r,g,b = arr2[sy,sx,:3]
        if r > 200 and g > 200 and b > 200:  # white text
            pyautogui.click(window_left + sx, window_top + sy)
            break
```

### 주의사항
- **절대 금지**: `taskkill /f /im Vita3K.exe` → 좀비 프로세스 발생. `vita3k_ctrl.py close` 사용
- **절대 금지**: `-r PCSE00240` CLI 실행 → 검정 화면 발생. GUI에서 실행
- **절대 금지**: 셰이더 캐시 삭제 → 게임 복구 불가
- Vita3K 내에서는 **한번 클릭**으로 선택 (더블클릭은 ImGui 앱 목록에서만)
- 게임은 리스트 **최하단**에 있음
- "콘텐츠 관리" 화면에 실수로 들어가지 않도록: **오른쪽 절반(x>60%)의 중간 높이(y 35-65%)만** 클릭
- LiveArea "시작" 버튼은 **cyan 색상** (RGB ~20,168,222). white가 아님! 감지 조건: `b>150 and g>150 and r<120`
- LiveArea 작은 팝업 → 먼저 중앙 상단(y=35%) 클릭으로 펼친 후 → 시작 클릭
- 화면 배율 150%: GetWindowRect 좌표를 pyautogui에 그대로 사용, mss도 동일 좌표 사용
- 스크린 캡처는 `mss` 라이브러리 사용. **mss 캡처는 Vulkan 렌더링을 정확히 감지함** - 검정 화면이 보이면 실제로 검정 화면인 것

### 키 매핑 (Vita3K 기준)

| PS Vita 버튼 | 키보드 키 | Scancode | 용도 |
|---|---|---|---|
| Cross (×) | `X` | 45 | 결정/선택/대화 진행 |
| Circle (○) | `Z` | 44 | 취소/뒤로가기 |
| Triangle (△) | `S` | 31 | 메뉴/특수 |
| Square (□) | `A` | 30 | 공격/특수 |
| D-Pad ↑ | `↑` | 72 | 위 이동/메뉴 선택 |
| D-Pad ↓ | `↓` | 80 | 아래 이동/메뉴 선택 |
| D-Pad ← | `←` | 75 | 왼쪽 이동 |
| D-Pad → | `→` | 77 | 오른쪽 이동 |
| L Trigger | `Q` | 16 | L 버튼 (도 전환 등) |
| R Trigger | `E` | 18 | R 버튼 |
| Start | `Enter` | 28 | 일시정지/메뉴 |
| Select | `Space` | 57 | 맵/기타 |
| Left Stick | `WASD` | W=17,A=30,S=31,D=32 | 이동 (D-Pad과 동일) |

- **주의**: 모든 게임 내 선택은 **키보드**로 조작 (방향키 + X/Z). 마우스 클릭/터치 사용 금지.
- **자동화 입력**: `keybd_event(0, scancode, KEYEVENTF_SCANCODE, 0)` 사용
- **Yes/No 다이얼로그**: 방향키(←→)로 항목 선택 → **X키**(scancode 45)로 확인. 터치/마우스 금지.
- **대화 진행**: X키 반복 입력으로 대화 텍스트 넘김
- **게임 내 이동**: 방향키 ←→ (좌우 이동), ↑ (점프), ↓ (웅크리기)

### 자동화 입력 방법
- `pyautogui`로 Vita3K 윈도우 클릭, 키보드 입력 가능 (Vita3K 포커스 후)
- `mss`로 스크린샷 캡처 (Vulkan 렌더링도 정상 감지)
- 자동화 가능: Vita3K 실행/종료, ImGui 조작, LiveArea 진입, 스크린샷 캡처, 파일 설치, 게임 내 키 입력(pyautogui)

### 대사(scemsg) 테스트 팁
- DLC 첫 번째 게임(化猫 Demon Cat 등)에 진입하면 바로 대사가 시작됨
- 대사 폰트 출력 확인에 적합 (메인 스토리보다 진입이 빠름)

### Vita3K 세이브
- 게임 내 세이브만 지원 (에뮬레이터 세이브 스테이트 없음)
- 세이브 위치: `C:/game/vita3k/ux0/user/00/savedata/PCSE00240/`
- 세이브 파일: `NinPri_PSV.dat`, `SlotParam_0.bin`
- 세이브 파일 백업/복원으로 빠른 테스트 가능

## 실행/종료 도구
```bash
python tools/vita3k_ctrl.py launch   # GUI 모드 실행
python tools/vita3k_ctrl.py close    # 안전 종료 (WM_CLOSE)
python tools/vita3k_ctrl.py status   # 상태 확인
```

## 패치 빌드 & 적용

### 전체 파이프라인
```bash
cd C:\Users\taro1\project\muramasa-kor

# 1. Vita3K 종료
python tools/vita3k_ctrl.py close

# 2. NMS 파일 빌드 (번역 JSON → NMS)
python tools/build_patch.py

# 3. CPK 패치 (append 방식 - 원본 끝에 데이터 추가, ContentSize 자동 업데이트)
python tools/cpk_patch.py backup/NinPri.cpk patch_main output/NinPri_final.cpk --append
python tools/cpk_patch.py backup/NinPriPatch.cpk patch_patch output/NinPriPatch_final.cpk --append

# 4. 설치
cp output/NinPri_final.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPri.cpk
cp output/NinPriPatch_final.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPriPatch.cpk

# 5. 게임 실행 (위의 자동화 절차 따르기)
```

### 원본 복원
```bash
cp backup/NinPri.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPri.cpk
cp backup/NinPriPatch.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPriPatch.cpk
```

## 프로젝트 구조

```
muramasa-kor/
├── README.md                    # 협업자 입문
├── CLAUDE.md                    # AI 에이전트 작업 규칙 (이 파일)
├── tools/                       # Python 빌드/자동화 스크립트 (28개)
├── translations/                # 번역 데이터 (JSON)
├── fonts/                       # 한글 TTF/OTF (3종)
├── textures/                    # 게임 텍스처 소스 (Vita3K export 원본 + PSD 작업)
│   ├── originals/               # Vita3K export 원본 (로컬화 소스)
│   └── work/                    # PSD 작업 파일
├── kr_textures/                 # 한글화된 텍스처 (Vita3K import용 PNG) — 별도 관리
│   └── ui/                      # 한글 UI 텍스처 (73420, 8EFF, ADE2 등)
├── wii/                         # Wii USA판 한글 패치 참고 자료
├── docs/                        # PDCA 문서 (01-plan, 02-design, 03-analysis, 04-report)
├── patch_main/                  # NinPri.cpk용 NMS 빌드 결과 (build_patch.py 출력)
├── patch_patch/                 # NinPriPatch.cpk용 NMS 빌드 결과 (build_patch.py 출력)
├── backup/                      # 원본 CPK (NinPri.cpk + NinPriPatch.cpk, 459MB, 리포 포함)
├── .claude/                     # 작업 로그 (todo/success/fail)
└── [gitignored 로컬 전용]
    ├── extracted/               # 추출된 게임 NMS (msgsheet만)
    ├── extracted_wii/           # Wii msgsheet NMS
    ├── output/                  # 빌드된 패치 CPK 산출물
    ├── temp/                    # realesrgan, pngquant 등 빌드 도구
    └── screenshots/             # 자동화 디버그 캡처
```

### 주요 번역 데이터 (`translations/`)
| 파일 | 설명 |
|---|---|
| `jp_messages.json` | 전체 번역 데이터 (6,124개 메시지) |
| `kr_sjis_mapping.json` | 한글↔Shift-JIS 매핑 테이블 (960자) |
| `proper_nouns.json` | 고유명사 통일 사전 |
| `texture_localize_config.json` | 텍스처 한글화 영역/번역 설정 |
| `texture_localize_catalog.json` | 전수조사 카탈로그 (379개 중 12개 텍스트 텍스처) |

### 주요 도구 (`tools/`)
| 파일 | 설명 |
|---|---|
| `build_patch.py` | 번역 JSON → NMS 빌드 (`patch_main/`, `patch_patch/` 출력) |
| `cpk_extract.py` | CPK 추출 (XOR c=0x5F, m=0x15, CRILAYLA 디컴프레스) |
| `cpk_patch.py` | CPK 패치 (append 방식, CRILAYLA LZ 재압축) |
| `crilayla_compress.py` | CRILAYLA LZ 압축기 + 라운드트립 검증 |
| `nms_parser.py` | NMSB 메시지 파일 파서 |
| `auto_font_import.py` | Vita3K export에서 폰트 해시 감지 → 한글 import 생성 |
| `hd_font_import.py` | HD 팩 폰트 위에 한글 오버레이 |
| `texture_localize.py` | UI 텍스처 한글화 (config JSON → Vita3K import PNG) |
| `texture_survey.py` | 텍스처 전수조사 컨택시트 |
| `detect_text_textures.py` | 텍스트 포함 텍스처 자동 감지 |
| `ftx_extract.py` | FTX→PNG 디코더 (DXT5/BC3 + Morton unswizzle) |
| `batch_upscale.py` | Real-ESRGAN 일괄 업스케일 |
| `audit_oor.py` | 패치 NMS의 범위 밖 SJIS 바이트 감사 |
| `apply_wii_translations.py` | Wii USA 한글 → Vita 번역 매칭 적용 |
| `polish_dlc.py` | DLC 고유명사 통일 |
| `genroku_test.py` | 겐로쿠 에피소드 대사 장면 자동 진입 |
| `vita3k_ctrl.py` | Vita3K 실행/종료 제어 |
| `vita3k_run_game.py` | Vita3K GUI 자동 게임 실행 |
| `capture_scene.py` | 단계별 장면 전환 캡처 |
| `fcmp_decompress.py` | Wii Vanillaware FCMP 디컴프 |
| `extract_wii_messages.py` | Wii NMS → JSON 변환 |
| `wii_hangul_decode.py` | Wii 한글 SJIS 역매핑 디코더 |

### 폰트 파일 (`fonts/`)
| 파일 | 용도 |
|---|---|
| `RIDIBatang.otf` | 본문 한글 폰트 (22px, 폰트 아틀라스 렌더링) |
| `Griun_PolSensibility-Rg.ttf` | UI 텍스처 한글 (타이틀, 버튼) |
| `IropkeBatangM.ttf` | 이롭게 바탕체 (레퍼런스) |

## 기술 정보

- **게임**: Muramasa Rebirth (PCSE00240, US 영문판)
- **텍스트 파일**: NMSB 형식, Shift-JIS 인코딩
- **한글 방식**: 한글 955자를 Shift-JIS 코드포인트에 매핑 + Vita3K 텍스처 import
- **CPK**: CRI Middleware, CRILAYLA 압축, XOR 암호화
- **CPK FileOffset**: 상대 오프셋. 실제 위치 = `FileOffset + add_offset`, `add_offset = min(ContentOffset, TocOffset)` (두 CPK 모두 0x800)
- **CPK FileSize**: CRILAYLA 블록 전체 크기 (16 + comp_size + 0x100)
- **CPK ExtractSize**: 압축 해제 파일 크기 = `CRILAYLA.uncomp_size + 0x100`
- **폰트**: FTX 컨테이너 내 GXT (DXT5/BC3, 1024x1024, PS Vita 스위즐)
- **US 버전**: `_US/msgsheet/` 경로의 파일을 사용 (JP와 US 모두 패치해야 함)

## 해결 완료 이슈

### CRILAYLA 압축 (2026-04-07 해결)
- **LZ back-reference 압축기** 구현 완료 (`tools/crilayla_compress.py`, `tools/cpk_patch.py`)
- 18개 NMS 파일 전부 라운드트립 검증 통과
- 압축률 21~85% (모두 93.6% 이하 충족)
- 해시 테이블 기반 매칭으로 큰 파일(72KB)도 정상 처리

### CPK 패치 구조 (2026-04-07 해결)
- **FileOffset 상대 오프셋 문제**: `add_offset = min(ContentOffset, TocOffset)` 적용
- **append 방식**: ETOC 앞에 데이터 삽입 → ETOC 뒤로 이동 → ContentSize/EtocOffset 헤더 업데이트
- **ExtractSize**: `uncomp_size + 0x100`으로 정상 업데이트
- **게임 부팅 확인**: AKSYS 로고 + 타이틀 화면까지 정상 도달

## 한글 폰트 텍스처 파이프라인 (2026-04-10 확립)

### 동작 원리
1. NMS 텍스트 파일에서 한글을 SJIS 코드포인트(0x8DA4~0x8E45 범위)로 인코딩
2. Vita3K texture export로 현재 세션의 폰트 텍스처 해시를 확인
3. 해당 해시의 KANJI 페이지에만 한글 글리프를 오버레이한 PNG를 import 폴더에 배치
4. Vita3K 재시작 시 import 텍스처가 원본 폰트를 대체

### 핵심 규칙
- **KANJI 페이지에만 import** — ASCII 페이지(cell 0 비어있음, cell 1='!')에는 절대 import 금지 (공백/기호 깨짐)
- **폰트 텍스처 해시는 고정됨** — 같은 게임 데이터(CPK)면 Vita3K 재시작해도 해시가 동일. 한번 import 생성하면 재실행 불필요
- **HD 팩 해시 충돌 방지** — `auto_font_import.py`가 HD 팩 2,139개 해시와 충돌 검사. HD 팩에 있는 해시는 폰트로 오버레이하지 않음 (풀/배경 깨짐 방지). 단, HD 팩 자체가 폰트인 경우 HD 베이스 위에 한글 오버레이
- **import 폴더 전체 삭제 금지** — HD 팩 텍스처가 손실됨. `auto_font_import.py`는 `.font_hashes.json`으로 폰트 전용 해시만 추적/정리
- **FTX 직접 패치(DXT5+swizzle)는 비권장** — 인코딩 문제로 글리프 깨짐 발생
- **셀 공식**: `cell = (b1-0x81)*188 + b2_offset` (offset=0, 0x7F skip)
- **폰트 페이지 시작**: linear 1644 (= SJIS 0x89CD = 河)
- **한글 로컬 위치**: local = cell - 1644 (0~954)

### 폰트 텍스처 감지 방법
```bash
python tools/auto_font_import.py
```
1. export 폴더에서 1024x1024 + 32px 그리드 패턴(boundary alpha=0) 텍스처 검색
2. cell 0이 비어있으면 ASCII 페이지 → SKIP
3. cell 0에 글리프 있으면 KANJI 페이지 → Korean import 생성

### 빠른 테스트 절차
```bash
# 최초 1회만: export에서 폰트 해시 감지 → import 생성
# 1. Vita3K 실행 → 게임 진입 (폰트 텍스처 export 유도)
python tools/vita3k_ctrl.py launch
# 2. auto_font_import 실행
python tools/auto_font_import.py
# 3. Vita3K 재시작 (import 적용)
python tools/vita3k_ctrl.py close && sleep 2 && python tools/vita3k_ctrl.py launch
# 이후에는 import가 유지되므로 재실행 불필요
```

## UI 텍스처 한글화 파이프라인 (Phase 4)

### 도구
- `tools/texture_localize.py` — JSON 설정 기반 텍스처 한글화 (영문 클리어 + 한글 렌더링)
- `tools/texture_survey.py` — 전체 텍스처 컨택시트 생성
- `tools/detect_text_textures.py` — 텍스트 포함 텍스처 자동 감지

### 설정 파일
- `translations/texture_localize_config.json` — 텍스처별 텍스트 영역/번역 정의 (작업 완료 시 status를 "done"으로)
- `translations/texture_localize_catalog.json` — 전수조사 결과 카탈로그 (379개 중 9개 텍스트 텍스처)

### 핵심 규칙
- **게임은 알파 채널만 사용** — RGB는 무시됨. 텍스처는 white RGB(255,255,255) + alpha로 렌더링
- **알파 전용 텍스처 다수** — 뷰어에서 흰색으로 보임. 검은 배경 합성(`Image.alpha_composite`)으로 확인
- **선택/미선택 상태가 별도 텍스처** — 같은 텍스트가 2개 이상 텍스처에 존재할 수 있음 (예: GENROKU LEGENDS → ADE2B8B5998887A9 + 8EFF960FC088FDD7)
- **한자 붓글씨는 보존** — 영문 텍스트만 한글로 교체
- **폰트**: Griun_PolSensibility-Rg.ttf (그리운 폴센서빌리티체)
- **작업 후 반드시 texture_localize_config.json에 기록** — 영역 좌표, 번역 텍스트, 폰트 크기, status 업데이트
- **출력 위치**: Vita3K `import/` 폴더 + 리포 `kr_textures/ui/` 양쪽에 저장 (`texture_localize.py`가 자동 복사)
- **수동 편집 텍스처 (regions 없음)**: `kr_textures/ui/`에 커밋된 버전을 권위로 간주. `texture_localize.py`가 자동 SKIP — 덮어쓰기 금지

### 빌드 & 테스트
```bash
# 전체 빌드
python tools/texture_localize.py

# 특정 텍스처만
python tools/texture_localize.py ADE2B8B5

# 미리보기 (검은 배경 합성)
python tools/texture_localize.py --preview
```

## 현재 진행 상황 (2026-04-13)

### 완료된 Phase
- ✅ **Phase 1**: NMS 텍스트 추출·번역 인프라 (955자 매핑, CRILAYLA 재압축)
- ✅ **Phase 2**: DLC 선택 / 시스템 메시지 한글 출력 (Vita3K texture import 파이프라인 확립)
- ✅ **Phase 3**: 본편 대사 1,116개 scemsg 번역 (Wii USA 한글 기반, NinPriPatch.cpk 오버라이드 해결)
- ✅ **Phase 3.5**: HD 텍스처 팩(Muramasa Complete 2.0) 적용 + 한글 폰트 고화질 오버레이
- ✅ **Phase 3.6**: 지명·Act 라벨·`武蔵`/`無事` 오역 대량 수정 (place-name-fix)
- ✅ 공백 반칸 렌더링 복구 (cell 224 투명 처리)
- ✅ DLC 난이도 화면 배경 텍스처 깨짐 수정 (87B72F6DB3C3FBDC 제외)

### 진행 중
- 🔄 **Phase 3 후속**: DLC 대사 ~1,062개 번역 추가
- 🔄 **Phase 4**: UI 그래픽 텍스처 한글화 (12개 중 3개 완료 — 73420, 8EFF, ADE2)
- 🔄 **OOR 전수**: 패치 NMS 전체에 범위 밖 SJIS 바이트 3,328개 감사 (별도 feature)

### 기술 부채 / 미해결
- **LiveArea 자동 조작**: green dot 위치가 세션마다 달라서 전체 범위 검색 필요 (부분 해결)
- **폰트 오버레이 커버리지**: cell 1024~1053 (lowercase a-z 영역 미처리)
- **Yes/No 다이얼로그 터치**: 원본 게임에서도 반응 없음 (Vita3K 터치 입력 이슈). 키보드 X 키로 우회

## CPK 로딩 우선순위 (반드시 숙지)

```
NinPriPack1~4.cpk → DLC 에셋 (그래픽/사운드/맵, msgsheet 없음)
NinPriPatch.cpk   → 업데이트 패치 (본편+DLC 대사, NinPri 오버라이드)
NinPri.cpk        → 베이스 게임 (NinPriPatch가 덮어씀)
```

- scemsg/sysmsg는 NinPriPatch.cpk의 파일이 우선 로드됨
- 따라서 `patch_main/`(NinPri용)과 `patch_patch/`(NinPriPatch용) **둘 다** 빌드·설치해야 함
- `build_patch.py`는 NinPriPatch_full/scemsg_full.nms를 템플릿으로 사용 (2,178개 US 메시지)

## 외부 의존 자원

리포에 포함:
- 원본 CPK: `backup/NinPri.cpk`, `backup/NinPriPatch.cpk` (459MB, 정품 사적 이용)

별도 확보 필요 (로컬 전용):
- HD 텍스처 팩: Plaidray/xibalva "Muramasa Complete 2.0" (외부 다운로드)
- Wiimms ISO Tools (wit): `tools/wit/` (Wii 참고 자료 재생성용, 선택)
- Real-ESRGAN ncnn-vulkan: `temp/realesrgan/` (업스케일용, 선택)
