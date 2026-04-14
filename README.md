# Muramasa Rebirth — 한글 패치 프로젝트

**PS Vita** 『Muramasa Rebirth』 (PCSE00240, US 영문판)의 비공식 한글화 프로젝트.
번역 데이터, 빌드 도구, 폰트/텍스처 리소스, PDCA 작업 기록이 포함되어 있다.

- **게임**: Muramasa Rebirth (PS Vita, Aksys 배급 US 영문판)
- **대상 에뮬레이터**: Vita3K
- **언어**: 한국어
- **기반**: Wii USA판 한글 패치(RSFE7U)의 공식 검수 번역 + DLC 추가 번역

> ⚠️ **저작권 안내**: 원본 게임 에셋(CPK, PKG)은 리포에 포함되지 않는다.
> **정품 소유자가 합법적으로 확보한 파일**을 `backup/`에 직접 배치해야 한다.
> **상업적 배포·재판매 금지**. HD 텍스처 팩도 별도로 확보해야 한다.

---

## 목차
1. [빠른 시작](#빠른-시작)
2. [필요한 것](#필요한-것)
3. [환경 셋업](#환경-셋업)
4. [패치 빌드 & 적용](#패치-빌드--적용)
5. [프로젝트 구조](#프로젝트-구조)
6. [기술 스택](#기술-스택)
7. [개발 워크플로 (PDCA)](#개발-워크플로-pdca)
8. [기여 가이드](#기여-가이드)
9. [라이선스](#라이선스)

---

## 빠른 시작

```bash
# 1. 리포 클론
git clone <this-repo> muramasa-kor
cd muramasa-kor

# 2. Python 의존성 설치
pip install -r requirements.txt        # Pillow, numpy, mss, pyautogui 등

# 3. 원본 CPK 준비 (아래 '원본 게임 파일' 섹션 참고)
#    Vita3K에 PKG 설치 후 CPK를 backup/에 복사
#    VITA3K_DIR은 자신의 Vita3K 설치 경로로 변경
VITA3K_DIR="C:/game/vita3k"  # ← 본인 경로에 맞게 수정
mkdir -p backup
cp "$VITA3K_DIR/ux0/app/PCSE00240/NinPri.cpk"      backup/
cp "$VITA3K_DIR/ux0/app/PCSE00240/NinPriPatch.cpk"  backup/

# 4. 번역 → NMS 빌드
python tools/build_patch.py

# 5. CPK 재패킹
python tools/cpk_patch.py backup/NinPri.cpk      patch_main  output/NinPri_final.cpk      --append
python tools/cpk_patch.py backup/NinPriPatch.cpk patch_patch output/NinPriPatch_final.cpk --append

# 6. Vita3K에 설치
cp output/NinPri_final.cpk      "$VITA3K_DIR/ux0/app/PCSE00240/NinPri.cpk"
cp output/NinPriPatch_final.cpk "$VITA3K_DIR/ux0/app/PCSE00240/NinPriPatch.cpk"

# 7. 한글 폰트 오버레이 생성 (한 번만)
python tools/vita3k_ctrl.py launch     # 게임 진입 → 폰트 텍스처 export 유도
python tools/auto_font_import.py       # 자동 해시 감지 + 한글 import PNG 생성
python tools/vita3k_ctrl.py close && python tools/vita3k_ctrl.py launch
```

---

## 필요한 것

### 소프트웨어
- **Python 3.10+** (Windows)
- **Vita3K** 최신 버전 (https://vita3k.org/)
- **Git**

### 게임 자산

| 자원 | 위치 | 비고 |
|---|---|---|
| **원본 CPK** | `backup/NinPri.cpk`, `backup/NinPriPatch.cpk` | 별도 확보 필요 — 아래 PKG 해시 참고 |
| **HD 텍스처 팩** (선택) | Plaidray/xibalva "Muramasa Complete 2.0" | 커뮤니티 배포 — 별도 다운로드 |
| **Korean 폰트** | `fonts/` | 리포 포함 (RIDIBatang, 그리운 경찰감성체) |

### Python 패키지
```
Pillow
numpy
mss
pyautogui
pywin32          # Windows 키 입력 자동화
```

---

## 환경 셋업

### 1) 디렉토리 준비
Vita3K 설치 경로는 사람마다 다를 수 있다. 아래는 예시이며, 본인 경로에 맞게 읽을 것.
```
<VITA3K_DIR>/                     # 예: C:/game/vita3k, D:/emulators/vita3k 등
├── Vita3K.exe
├── ux0/app/PCSE00240/            # 게임 앱
└── textures/
    ├── export/PCSE00240/         # 게임 실행 시 자동 dump
    └── import/PCSE00240/         # 한글 폰트/텍스처 overlay
```

Vita3K 설정에서 **Texture Import/Export** 옵션을 활성화해야 한다.

### 2) 원본 CPK 준비
원본 CPK는 리포에 포함되지 않는다 (용량 459MB). Vita3K에 PKG를 설치한 뒤 복사한다:
```bash
mkdir -p backup
cp C:/game/vita3k/ux0/app/PCSE00240/NinPri.cpk      backup/
cp C:/game/vita3k/ux0/app/PCSE00240/NinPriPatch.cpk  backup/
```
올바른 원본인지 아래 '원본 게임 파일' 섹션의 해시 표로 확인할 것.

### 3) HD 팩 적용 (선택)
HD 팩은 `<VITA3K_DIR>/textures/import/PCSE00240/`에 PNG들을 배치하면 자동 적용된다.
리사이즈 + 최적화는 `tools/hd_font_import.py` 참고.

---

## 패치 빌드 & 적용

### 전체 파이프라인

```bash
# 0. Vita3K 안전 종료
python tools/vita3k_ctrl.py close

# 1. 번역 JSON → NMS 바이너리 빌드
python tools/build_patch.py
#   → patch_main/*.nms, patch_patch/*.nms 생성

# 2. CPK 재패킹 (append 방식 — 원본 데이터 뒤에 추가)
python tools/cpk_patch.py backup/NinPri.cpk      patch_main  output/NinPri_final.cpk      --append
python tools/cpk_patch.py backup/NinPriPatch.cpk patch_patch output/NinPriPatch_final.cpk --append

# 3. Vita3K에 설치
cp output/NinPri_final.cpk      C:/game/vita3k/ux0/app/PCSE00240/NinPri.cpk
cp output/NinPriPatch_final.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPriPatch.cpk

# 4. 한글 폰트 텍스처 import 갱신 (최초 1회 + 폰트 커버리지 변경 시)
python tools/auto_font_import.py
#   또는 HD 팩 베이스로 한글 렌더링:
python tools/hd_font_import.py

# 5. UI 그래픽 텍스처 한글화
python tools/texture_localize.py

# 6. Vita3K 실행
python tools/vita3k_ctrl.py launch
```

### 원본 복원
```bash
cp backup/NinPri.cpk      "$VITA3K_DIR/ux0/app/PCSE00240/NinPri.cpk"
cp backup/NinPriPatch.cpk "$VITA3K_DIR/ux0/app/PCSE00240/NinPriPatch.cpk"
```

### 트러블슈팅

| 증상 | 원인 | 대처 |
|---|---|---|
| 게임 부팅은 되는데 한글이 □로 표시 | 폰트 텍스처 import 미적용 | `auto_font_import.py` 재실행 후 Vita3K 재시작 |
| 공백이 한 칸 크게 렌더링 | `auto_font_import.py` 구버전 (cell 224 투명 처리 누락) | 최신 버전 확인 |
| 대사가 영문으로 나옴 | NinPri만 패치, NinPriPatch 미적용 | 반드시 **두 CPK 모두** 패치 |
| LiveArea에서 `-r CLI`로 실행 시 검정 화면 | Vita3K 알려진 이슈 | GUI에서 실행 (자동화 스크립트 사용) |
| Vita3K가 `taskkill`로 강제 종료 후 좀비 | 셰이더 캐시 락 | `vita3k_ctrl.py close`만 사용 (WM_CLOSE) |

---

## 프로젝트 구조

```
muramasa-kor/
├── README.md                    # 이 문서
├── CLAUDE.md                    # AI 에이전트 작업 규칙 (기술 상세 풍부)
├── tools/                       # Python 빌드/자동화 스크립트
│   ├── build_patch.py           # 번역 JSON → NMS
│   ├── cpk_extract.py           # CPK → 파일 추출
│   ├── cpk_patch.py             # 파일 → CPK 재패킹
│   ├── crilayla_compress.py     # CRILAYLA LZ 압축
│   ├── nms_parser.py            # NMSB 메시지 파일 파서
│   ├── auto_font_import.py      # 폰트 텍스처 자동 감지 + 한글 오버레이
│   ├── hd_font_import.py        # HD 팩 폰트 위에 한글 오버레이
│   ├── texture_localize.py      # UI 텍스처 한글화
│   ├── audit_oor.py             # OOR SJIS 바이트 감사
│   ├── vita3k_ctrl.py           # Vita3K 프로세스 제어
│   ├── genroku_test.py          # 겐로쿠 에피소드 자동 진입 테스트
│   └── ...                      # (총 28개)
├── translations/                # 번역 데이터
│   ├── jp_messages.json         # 전체 메시지 (6,124개)
│   ├── kr_sjis_mapping.json     # 한글↔SJIS 매핑 (960자)
│   ├── proper_nouns.json        # 고유명사 사전
│   └── texture_localize_*.json  # 텍스처 한글화 설정·카탈로그
├── fonts/                       # 한글 TTF/OTF
│   ├── RIDIBatang.otf           # 본문 폰트 (22px, 폰트 아틀라스용)
│   └── Griun_PolSensibility-Rg.ttf  # 그리운 경찰감성체 (UI 텍스처용)
├── textures/                    # 텍스처 소스 리소스
│   ├── originals/               # Vita3K export 원본 (로컬화 작업 소스)
│   └── work/                    # PSD 작업 파일
├── kr_textures/                 # 한글화된 텍스처 (Vita3K import용 배포본)
│   └── ui/                      # UI 텍스처 한글판 (타이틀, 로고, DLC 부제 등)
├── docs/                        # PDCA 문서
│   ├── 01-plan/features/        # 기능별 계획서
│   ├── 02-design/features/      # 구현 설계
│   ├── 03-analysis/             # OOR baseline, Wii 교차검증
│   └── 04-report/
├── patch_main/                  # build_patch.py 출력 (NinPri.cpk용 NMS)
│   ├── msgsheet/                # JP 메시지
│   └── _US/msgsheet/            # US 메시지
├── patch_patch/                 # build_patch.py 출력 (NinPriPatch.cpk용 NMS)
├── .claude/                     # 작업 로그
│   ├── todo.md                  # 진행 예정
│   ├── success.md               # 완료 기록
│   ├── fail.md                  # 실패 기록
│   └── research_korean_patch_methods.md
├── backup/                      # 원본 CPK (NinPri.cpk, NinPriPatch.cpk — 459MB, gitignored)
└── [gitignored — 로컬 전용]
    ├── extracted/               # 추출된 게임 NMS (msgsheet만, 빌드 시 생성)
    ├── extracted_wii/           # Wii msgsheet NMS (참고)
    ├── output/                  # 빌드된 패치 CPK 산출물
    ├── temp/                    # 업스케일 · 빌드 임시 도구 (realesrgan, pngquant)
    └── screenshots/             # 자동화 디버그 캡처
```

---

## 기술 스택

### 파일 포맷
- **NMSB**: Nintendo Message Script Binary — 메시지 파일 (Shift-JIS)
- **CPK**: CRI Middleware 압축 아카이브 — CRILAYLA LZ + XOR 암호화 (c=0x5F, m=0x15)
- **FTX / GXT**: PS Vita 텍스처 컨테이너 — DXT5/BC3 + Morton swizzle
- **FCMP**: Vanillaware Wii 전용 LZSS 압축 (12+4 비트, LSB)

### 한글 렌더링 방식
1. NMS 바이너리 안의 한글을 사용하지 않는 **SJIS 한자 슬롯(0x89CD~0x8EE0)**에 매핑
2. Vita3K 텍스처 export로 폰트 아틀라스 해시 확인
3. KANJI 페이지(1024×1024) 위에 한글 글리프를 렌더링한 PNG를
   `C:/game/vita3k/textures/import/PCSE00240/<hash>.png`로 배치
4. Vita3K 재시작 시 import PNG가 원본 폰트 텍스처를 대체

### 셀 매핑 공식
```
cell  = 224 + (b1 - 0x81) * 188 + b2_offset
b2_offset = b2 - 0x40       (b2 < 0x80)
b2_offset = b2 - 0x41       (b2 >= 0x80, 0x7F skip)
한글 local = cell - 1644    (0~959)
```

### CPK 패치 이슈 (해결)
- **FileOffset 상대값**: `add_offset = min(ContentOffset, TocOffset)` (둘 다 0x800)
- **append 방식**: ETOC 앞에 새 파일 삽입 → ETOC 이동 → ContentSize/EtocOffset 헤더 갱신
- **ExtractSize**: `CRILAYLA.uncomp_size + 0x100`

자세한 내용은 [CLAUDE.md](CLAUDE.md) 참고.

---

## 개발 워크플로 (PDCA)

이 프로젝트는 **PDCA 방식**으로 진행한다. 새 작업은 다음 순서를 따른다:

1. **Plan** — `.claude/todo.md`에 계획 기록, `docs/01-plan/features/<feature>.plan.md` 작성
2. **Design** — `docs/02-design/features/<feature>.design.md`에 설계
3. **Do** — 구현, 빌드, Vita3K 실행으로 **자체 검증** (사용자에게 수동 검증 요청 금지)
4. **Check/Act** — 스크린샷 캡처로 결과 검증, `docs/03-analysis/`에 분석 기록, `.claude/success.md` 또는 `fail.md`에 결과 기록, 즉시 git commit

### 작업 로그
- [.claude/todo.md](.claude/todo.md) — 진행 예정
- [.claude/success.md](.claude/success.md) — 성공한 작업
- [.claude/fail.md](.claude/fail.md) — 실패한 작업 및 원인

### 참고 자료
- [한글패치 대안 방법 연구](.claude/research_korean_patch_methods.md)

---

## 기여 가이드

### 번역 품질 기준
- **Wii USA 한글 패치**가 1차 레퍼런스 (번역 기반)
- 고유명사는 `translations/proper_nouns.json`에 정의 후 `polish_dlc.py`로 일괄 적용
- 1줄 ≤ 18자 (scemsg), 아이템 설명 2줄, 지명 1줄 캡

### 커밋 규칙
- 작업 단위로 즉시 커밋 (`패치 이후 모아서 커밋` 금지)
- 커밋 메시지: 영문·한글 모두 가능, **왜**를 중심으로 기술
- 관련 작업 기록 파일(`.claude/*.md`) 업데이트 포함

### 코드 스타일
- Python: PEP 8 + type hints
- 도구 스크립트에는 헤더 docstring 작성 (사용법 포함)
- 외부 경로는 `PROJECT_DIR / "fonts" / ...` 스타일로 pathlib 사용

### 새 도구 추가 시
1. `tools/` 하위에 추가
2. `CLAUDE.md`의 **주요 도구** 표에 등재
3. 필요시 `README.md`의 **빠른 시작** / **파이프라인**에 명령 추가
4. 의존성은 `requirements.txt`에 추가

---

## 원본 게임 파일 (PKG)

빌드에 필요한 원본 CPK를 얻으려면 아래 PKG를 Vita3K에 설치한 뒤 `backup/`에 복사한다.
정품 소유자가 합법적으로 확보한 파일만 사용할 것.

### 본편 (PCSE00240)

| 파일 | 크기 | SHA-256 |
|---|---|---|
| `Muramasa Rebirth.pkg` | 450 MB | `339cd06ec0f19bea3c9ce40fe47d4873b365d8ad6f78845f9819edeb0d5d9b71` |
| `update.pkg` | 33 MB | `1396e08a04a28a41f64f10cc762546139df1eed29cce9ca87363696d13a9388b` |
| `work.bin` | 512 B | `49e2550c82fe5a61e873682e84cd22b32229d0482150185abc25087b08b6ba48` |

### DLC — Genroku Legends

| DLC | PKG SHA-256 | work.bin SHA-256 |
|---|---|---|
| **A Cause to Daikon For** (69 MB) | `62f46a334f79054a76b4b2644942c2a2ccb4a8271bb553f5208d60f77f922f84` | `9a6ebb5121110ad2f01ca0d0cf05e93b9b742a463746b8eb4c69ec57687b24f0` |
| **A Spirited Seven Nights' Haunting** (84 MB) | `9c018a639cf631b6babbe2ba48e14a06bca866f752c53a86f9436e39a236a84c` | `9d39ed0c09e446cd852715f87160f0af6882a00504d7ae455089361a879b9d89` |
| **Fishy Tales of the Nekomata** (76 MB) | `03e660dbf4fbeb848de1650bfe900db346fe711265e42f01a07042a421b657ba` | `9498bd7f4ed205564a46a7f3dbdb8484e156b06ee037030e1b6ab352b57f2439` |
| **Hell's Where the Heart Is** (83 MB) | `2af2a4de7fd1b1e1233eee86e8a039ae834d015c9ca293e217a047e5292aaf82` | `1ede67a4e510b94682937ca49c1cd7400d0b553a7c5932eac6d3c2a2ef30baa3` |

### 설치 후 CPK 복사
```bash
# Vita3K GUI에서 본편 PKG → update.pkg → DLC 4개 순서로 설치
# 설치 완료 후 (VITA3K_DIR은 본인 Vita3K 경로):
mkdir -p backup
cp "$VITA3K_DIR/ux0/app/PCSE00240/NinPri.cpk"      backup/
cp "$VITA3K_DIR/ux0/app/PCSE00240/NinPriPatch.cpk"  backup/
```

---

## 라이선스

- **번역 데이터** (`translations/*.json`): 기여자 동의 하에 비영리 공유
- **도구 스크립트** (`tools/*.py`): MIT (별도 LICENSE 파일 참고)
- **폰트** (`fonts/`):
  - RIDIBatang — RIDI 배포, 개인 사용 허용
  - 그리운 경찰감성체 (Griun_PolSensibility-Rg.ttf) — 저작자 확인 후 사용
- **원본 게임 에셋** (CPK, HD 팩): **포함되지 않음** — 각자 합법적으로 확보

이 프로젝트는 마무리시 비공식 팬 번역으로 배포 예정이며, 상업적 이용을 금지한다.

---

## 문의 / 기여

이슈·풀리퀘스트 환영. 참여 전 `.claude/todo.md`와 `docs/01-plan/features/` 문서를 먼저 확인하기 바란다.
