# 받침 누락 잔여 54자 — 폰트 확장 PoC 종합 분석

> ## ⚠ 2026-05-25 후기 — 이 문서의 "옵션 1 불가" 결론은 뒤집혔다 (해결됨)
>
> 실제 게임 폰트는 GXT **16페이지**로 나뉘어 있고, SJIS 한자 페이지가 **3개**다:
> Page0 河(0x89CD) / Page1 重(0x8F64) / Page2 隼(0x94B9). 아래 PoC는 **"한 페이지(河)를
> 세로로 1024×2048로 늘리는" 잘못된 접근**만 시도해서 실패한 것이다. 늘릴 필요 없이, 이미
> **별도로 존재하는** 重·隼 페이지 텍스처(export hash E690E190, 5F01AD86)에 한글을
> 오버레이하니 정상 작동 → **완성형 2350자 전부 직접 글리프 달성**(char_substitutions 폐기).
> **eboot 패치 불필요.** 상세: `success.md` 2026-05-25 항목, `CLAUDE.md` "한글 폰트 텍스처
> 파이프라인", 커밋 `b6a58eb`. 아래 본문은 역사 기록으로 보존.

**작성일**: 2026-05-23
**대상 커밋 범위**: `c08f5fa`(폰트 확장 PoC 시작) ~ `486e7aa`(현재 HEAD)
**결론**: ~~옵션 1(CPK + import 텍스처) 한계 확정~~ → **틀림(위 후기 참조)**. 문제는 옵션 1 자체가
아니라, 한 페이지를 늘리려 한 것. 다른 페이지(重/隼)를 쓰면 옵션 1로 해결됨.
**현재 처분**: 워킹 트리를 `d9cad6b`(폰트 확장 직전, 매핑 1001자) 상태로 복원하여 빌드/배포. 커밋은 보존.

---

## 1. 배경

폰트 cell 965~1023(0x8EE6~0x8F23) 빈 슬롯에 받침 누락 38자를 채우는 4차 패치(`6684c96`)는 성공. 매핑이 960자 → 1001자가 되어 RUNTIME_OVERLAY 충돌(뜯/뜸)도 동시 해소.

**잔여**: 받침 54자(괄/굶/귈/꿇/끕/낀/낄/낚/닳/댈/댐/댔/덧/덫/렷/롬/릎/멎/뱃/벴/빴/뺌/뿟/삐/삥/섰/솟/쉼/슥/슷/쌔/쎄/쏙/씐/압/얄/왠/잣/줌/짊/짙/쫌/쫙/쭐/칩/캤/탔/탱/틴/폐/픕/햐/홱/휴)가 매핑 영역 0x89CD~0x8F63(1024 cell)을 모두 소진한 상태에서 추가 불가. **다음 SJIS 페이지 0x8F64+(cell 1024+)에 슬롯이 필요**.

---

## 2. PoC 시퀀스 (전체 11개 커밋)

### 옵션 1: CPK + import 텍스처 확장 (실패)

#### PoC #1 — Import 텍스처만 1024x2048 확장 (`c08f5fa`)
- **변경**:
  - `tools/auto_font_import.py`: cell range `0..1024` → `0..2048`. 원본 1024x1024 위쪽 paste, 아래쪽(y=1024~2048) 신규 영역.
  - 빡 → SJIS 0x8F64 (cell 1024) PoC 매핑.
  - `textures/kr/font/{18747565,A8E6FDD1,8665CE08}.png` 모두 1024x2048 생성. 6706A53E HD는 4096x4096 유지(미적용).
- **검증**:
  - cell 1024 빡 글리프 정상 그려짐 (alpha mean 26~42).
  - NMS 인코딩 빡 0x8F64 = 3회 정상.
- **결과 빌드**: `NinPri_final.cpk` md5 `0af5df11fa0da306b00546af6f8e0e38`, `NinPriPatch_final.cpk` md5 `630893c4d09e9c57aff63592b15aaecd`.

#### PoC #2 — 본편/DLC 선택 메시지에 빡/칙/맘/뜯/뜸 임시 삽입 (`a7dbaff`, `c297ad6`)
- sysmsg #267("오보로 무라마사 선택"), #268("겐로쿠 괴기담 선택") ko에 `[빡칙맘뜯뜸]` (a7dbaff) → 한 줄 압축(c297ad6).
- 5글자 모두 cell 1024~1028 매핑.

#### PoC #1+2 결과 (`d8946ac` revert)
- **인게임 결과**: "오보로 무라마사(빡칙맘뜯뜸)" → **"평잎 켄영찛드 ... 틱올 청앉좀)" 깨짐**.
- **원인 추정**: 게임 코드가 cell index → UV 변환 시 텍스처 크기를 1024 hardcoded로 가정. 1024x2048 import에서 실제 GPU 텍스처는 2048 size지만, 게임 셰이더의 UV 계산은 1024 기준 → cell N의 UV.y = N*32/1024가 실제 pixel y = UV.y*2048 = N*64 → 의도 (N*32) 대비 **2배 어긋남** → 인접 cell sample.
- **롤백**: cell range 1024 + 텍스처 1024x1024 복원. 매핑 사이클 2 시점(960자) + substitutions 95자. sysmsg #267/#268 ko 원본 복원.
- **빌드**: `NinPri_final.cpk` md5 `8680992e73717e8c693c596261379636`, `NinPriPatch_final.cpk` md5 `5690aa7cdd490d2c41cf091834233469`.

#### PoC #3 — CPK 내 font.ftx GXT header height 변경 (`01e9fbe`, `61f44ee` revert)
- **PoC 3a (`01e9fbe`)**: GXT header height만 `1024 → 2048` 변경, data 그대로. Vita3K 부팅 OK.
  - `NinPri_final.cpk` md5 `134d6e9dcdf7b17584bd8e33acc60a98` (+2.6MB), `NinPriPatch_final.cpk` md5 `bd87679ffd4fa10a9b2f5d62558c0bb5` (+2.6MB).
- **PoC 3b**: GXT data 1MB → 2MB + height 2048 + tex_size `0x200000`.
- **검증 결과** (`61f44ee`):
  - 두 PoC 모두 Vita3K 부팅 OK, AKSYS/Vanillaware 로고 → 타이틀 화면 정상 도달.
  - **export 폴더에 새 해시 등장 안 함**.
  - 게임이 font.ftx 사이즈 변경을 메모리 atlas 재구성에 반영 안 함.
- **결론**: 게임이 font.ftx 로드 시 **하드코딩된 1024 size**로 메모리 atlas를 구성하는 것으로 추정. font.ftx 자체 확장 불가.

### 옵션 1 한계 확정 — Vita3K source 분석 (`a71636d`)

`renderer/src/texture/replacement.cpp` 분석:
- `line 524`: `stbi_load`로 import PNG의 width/height 읽음
- `line 558-559`: import의 실제 size를 그대로 저장
- `line 564`: `import_configure_impl(base_format, width, height)` — GPU upload
- **UV scale 보정 코드 없음**

**결정적 결론**:
- Vita3K는 import 텍스처를 PNG 실제 size로 GPU upload (1024x2048 그대로).
- 게임 코드가 cell→UV에서 1024 hardcoded 사용 시 UV.y = N*32/1024 → 우리 1024x2048 import에서 실제 pixel y = UV.y * 2048 = N*64 → 의도(N*32) 대비 2배 어긋남.
- PoC #1+2의 깨짐 패턴(빡 → 평 등)과 정확 일치.

→ **옵션 1로 cell 추가 불가능 확정**. Cell 추가 = atlas 확장은 **게임 코드(eboot) 패치** 또는 **Vita3K source 패치**만 가능.

### 옵션 2 환경 구축 (eboot.bin 패치 사전 작업)

#### `513bc2d` — macOS Vita3K 자동 제어 도구
- `tools/vita3k_macos.py`: launch / close / status / screenshot / focus (osascript 기반).
- 자동 빌드→배포→실행→캡처 사이클 기반.

#### `a23b8c6` — sceutils (TeamMolecule) + Python 3 변환
- `tools/external/sceutils/`: TeamMolecule sceutils clone, 2to3 자동 변환, `.encode("hex") → .hex()` 수정.
- `self2elf.py` 부분 작동(SCE/SELF header, AppInfo, SegmentInfo 파싱). keys.py 누락으로 마지막 단계 미완.

#### `3c54f2e` — eboot.bin SELF decrypt 성공
- `tools/external/vita3k_sce_utils.cpp`: Vita3K source의 SCE keys 추출 원본.
- `sceutils/keys.py` 자동 생성 (Vita3K cpp에서 56 keys 추출).
- Vita SELF.APP + key_revision 1 + system version 매칭 → AES decrypt 성공.
- **결과**: `eboot.bin (1.8MB SELF, header 0x1000) → eboot.elf (4.3MB)`
  - ELF magic 정상 `7F454C46`, ARM (e_machine `0x28`)
  - entry `0x2DFB60`, PT_LOAD vaddr `0x81000000` (text `0x3F19B8` bytes)
  - **"other/font.ftx" 문자열 VMA `0x81304AE0` 식별**
- decrypted ELF는 .gitignore (저작권 보호).

### 마지막 시도 — 빡 → 0x8F64 (cell 1024) 매핑 (`486e7aa`, 현재 HEAD)

- cell 1024 sample 동작 확인용 PoC. import는 1024x1024 그대로 (cell 1024는 텍스처 밖).
- 변경:
  - 빡 → 0x8F64 매핑 (substitution 제거)
  - sysmsg #40 ja "レベル" ko "레벨" → "레빡벨" (HUD 검증)
  - sysmsg #267: "오보로 무라마사(빡)"
  - sysmsg #268: "겐로쿠 괴기담(빡)"
- **검증 결과**:
  - 자동 진입(X 키) 실패, 타이틀 화면 정지로 인게임 도달 못 함.
  - cell 1024 sample 결과 **미확인**.
- 빌드: `NinPriPatch_final.cpk` md5 `d565ee0d49ba3c8d3bbf71066d0d46e8`.

---

## 3. 시도 요약 표

| # | Commit | 시도 내용 | 결과 |
|---|---|---|---|
| 1 | c08f5fa | Import 텍스처 1024 → 1024x2048, 빡 0x8F64 매핑 | 글리프는 그려짐, 인게임 미검증 |
| 2 | a7dbaff | sysmsg #267/#268에 빡칙맘뜯뜸 5자 cell 1024~1028 매핑 | 인게임 깨짐 (UV 2배 어긋남) |
| 3 | c297ad6 | 박스 폭 위해 한 줄 단축 | 동일 깨짐 |
| 4 | d8946ac | **revert**: 1024x1024 복원 + 매핑 사이클 2(960자) 롤백 | 옵션 1 import 단독 한계 확정 |
| 5 | 513bc2d | macOS Vita3K 자동 제어 도구 | 자동화 기반 구축 |
| 6 | 01e9fbe | font.ftx GXT header height 2048 PoC | 부팅 OK, 게임 무시 |
| 7 | (PoC 3b) | font.ftx data 2MB 확장 PoC | 부팅 OK, 게임 무시 |
| 8 | 61f44ee | **revert**: font.ftx PoC 모두 인식 안 됨 | 옵션 1 CPK side 한계 확정 |
| 9 | a23b8c6 | sceutils 도입 + Python 3 변환 | self2elf 부분 작동 |
| 10 | 3c54f2e | eboot.bin SELF decrypt 성공 | eboot.elf 4.3MB 획득 |
| 11 | a71636d | Vita3K source replacement.cpp 분석 | 옵션 1 한계 이론적 확정 |
| 12 | 486e7aa | 빡 0x8F64 + sysmsg #40/#267/#268 임시 변경 (현재 HEAD) | 자동 진입 실패, 미검증 |

---

## 4. 핵심 학습

### 옵션 1 (CPK + import 텍스처) 불가 — 두 layer 모두 막힘
- **import side**: Vita3K replacement.cpp가 import PNG의 실제 size를 그대로 GPU upload. 게임 셰이더의 cell→UV 매핑은 size-aware 아니라 1024 hardcoded → 텍스처를 늘리면 UV가 비례로 안 늘어남.
- **CPK side**: 원본 font.ftx의 GXT header height/data를 늘려도 게임이 메모리 atlas 재구성 시 1024 size 유지 (export 폴더 새 hash 미등장).

### 사용 가능한 cell 공간
- 0x89CD~0x8F63 (1024 cell) 모두 사용 중 (잔여 54자 매핑 불가).
- 0x8F64+ (cell 1024+)는 게임이 lookup 안 함 — atlas 외부.

### 다음 옵션 (남은 길)
1. **옵션 2 (eboot.bin ARM 패치)**: 환경 구축 완료(eboot.elf 4.3MB). Capstone disasm → 폰트 sample 함수 식별 → 1024 hardcoded 값 패치. 위험: 게임 부팅 실패, 사인 검증 우회 필요할 수 있음.
2. **옵션 3 (Vita3K source 패치)**: replacement.cpp에 UV scale 보정 코드 추가. 사용자별 빌드 필요(배포 어려움).
3. **옵션 4 (한자 영역 직접 한글 교체)**: 사용 중인 SJIS 한자 셀의 glyph만 한글로 BC3 인코딩 + Morton swizzle하여 font.ftx 패치. 위험: 한자가 필요한 다른 영역(인명, 게임 UI)에서 깨짐.
4. **deferred**: 받침 누락 54자 char_substitutions로 대체 표기 유지하고 다른 이슈 우선.

---

## 5. 현재 처분 (2026-05-23)

- 워킹 트리를 `d9cad6b`(폰트 확장 직전) 상태로 복원하여 빌드/배포.
  - 매핑 1001자 + char_substitutions 54자 (받침 38자 직접 매핑 반영).
  - 8665CE08 폰트 import 포함.
  - sysmsg #40/#267/#268 원본 복원.
- 폰트 확장 관련 도구(`tools/external/sceutils`, `tools/vita3k_macos.py`, `tools/external/vita3k_sce_utils.cpp`)는 워킹 트리에서 제거. 커밋 보존.
- 받침 잔여 54자는 **deferred** 처리. 옵션 2 환경은 커밋에 보존되어 향후 재개 가능.

---

## 6. 향후 재개 시 진입점

```bash
# 옵션 2 환경 복원 (sceutils + Vita3K source)
git checkout 3c54f2e -- tools/external/

# eboot.bin decrypt 절차
cd tools/external/sceutils
python3 self2elf.py /path/to/eboot.bin /tmp/eboot.elf

# ARM disasm 시작점
# "other/font.ftx" VMA = 0x81304AE0 참조하는 literal pool 또는 MOVW/MOVT 검색
# 폰트 atlas size hardcoded 1024 → 2048 패치
```

