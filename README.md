# Muramasa Rebirth Korean Patch

`Muramasa Rebirth` PS Vita US판(`PCSE00240`)용 한국어 패치 프로젝트다.

## 소개

정식 한글판(스위치 정발 등)을 기다리다 직접 만든 비공식 한글 패치다. 번역·도구 작업에는 Claude·Codex를 활용했고, 그래픽/텍스처 한글화는 직접 작업했다. **정식 한글판이 출시되면 배포를 중단**할 예정인 한시적 프로젝트다.

이 저장소와 릴리즈는 원본 게임 PKG/CPK를 포함하지 않는다. 사용자는 본인이 합법적으로 보유한 원본 게임을 Vita3K에 먼저 설치한 뒤, 릴리즈에 포함된 로컬 패처로 본인 PC의 원본 CPK에 패치를 적용한다.

## 🖱️ 빠른 시작 — 통합 GUI 도구 (가장 쉬움, 권장)

> **설치가 처음이거나 복잡한 게 싫다면 여기만 보면 된다.** 명령어·파이썬 없이 마우스 클릭만으로 끝난다.

명령어를 칠 필요 없이 **마우스 클릭만으로** Vita3K(에뮬레이터)와 실기(real PS Vita) 패치를 모두 만드는 통합 GUI 도구를 제공한다. 원본 CPK 경로도 자동으로 찾는다.

- **받을 파일**: `muramasa-kor-vX-patcher-windows.zip` (Windows용 `MuramasaPatcher.exe`는 릴리즈에 별도 첨부 — zip 폴더 안에 넣으면 된다)
- **Windows**: `MuramasaPatcher.exe` 더블클릭 — **파이썬 설치가 필요 없다.**
  - 처음 실행 시 SmartScreen 파란 경고가 뜨면 **"추가 정보" → "실행"** 을 누른다.
- **macOS / Linux**: zip을 풀고 `실행_Mac.command`(맥) 또는 `실행_Linux.sh`(리눅스)를 실행 — 파이썬 3.9 이상 필요.
  - macOS에서 "확인되지 않은 개발자" 경고가 뜨면 Finder에서 **우클릭 → 열기**, 또는 터미널에서 `xattr -dr com.apple.quarantine "실행_Mac.command"`.

**사용 순서**

1. 도구를 실행하면 창이 뜬다.
2. 맨 위에서 **설치 대상**을 고른다.
   - **Vita3K 에뮬레이터**: 경로를 자동으로 찾는다. 그대로 **[패치 시작]**.
   - **실기 PS Vita**: 원본 `NinPri.cpk` / `NinPriPatch.cpk`(+DLC) 경로와 결과 저장 폴더를 고른 뒤 **[패치 시작]**.
3. 진행 로그가 끝나고 "완료" 창이 뜨면 성공이다.

- Vita3K는 패치가 곧바로 적용된다(폰트/UI가 안 보이면 Vita3K 설정 `GPU > Import Textures`를 켠다). "원본으로 복원" 체크 후 시작하면 되돌린다.
- 실기는 생성된 결과 폴더의 `ux0` 폴더를 Vita 본체 `ux0:/` 아래에 복사하고 rePatch 플러그인을 켠다. → [실기 쉬운 설치 가이드](docs/실기-쉬운-설치-가이드.md) 참고.

> 아래의 명령어(CLI) 방식은 그대로 유지된다. GUI가 동작하지 않거나 자동화하려는 사용자를 위한 **수동/고급 경로**다.

## 사용자 안내

- 지원 대상: Vita3K Windows/macOS, Android 수동 복사, **실기(real PS Vita) [베타]** — [실기 패치 안내](#실기real-ps-vita-패치-베타) 참조
- 대상 타이틀 ID: `PCSE00240`
- 대상 게임: `Muramasa Rebirth` US판 (영문)
- 현재 릴리즈: `v1.3.1` (**액세서리 아이템명 표시 버그 수정** — 보스 재격파 보상 등 일부 액세서리의 이름·효과가 다른 아이템 것으로 밀려 표시되던 문제 해결. 실기(real PS Vita) 패치 [베타]는 [실기 패치 안내](#실기real-ps-vita-패치-베타) 참조. ○ 대신 ✕ 버튼을 원하는 분을 위한 선택형 [✕ 버튼 추가팩](#-버튼-추가팩-선택) 포함)
- 배포 형식: Windows/macOS 공용 로컬 패처 zip, Android용 수동 복사 안내

릴리즈 zip에는 다음만 포함된다.

```text
apply_patch.py
apply_windows.bat
apply_macos.command
patches/*.patch.json
patches/*.patch.bin
textures/import/PCSE00240/*.png
release/manifest.json
```

`textures/import/PCSE00240/*.png`에는 한글 폰트와 UI 텍스처 import가 포함된다.

`NinPri.cpk`, `NinPriPatch.cpk`, 원본 PKG, DLC 데이터는 포함하지 않는다.

## 원본 게임 준비

영문판 본편 + 1.06 업데이트 PKG, DLC PKG는 4개를 전부 설치가 필요하다. 모든 PKG는 정품 소유자가 합법적으로 확보한 파일을 사용할 것.

> 본편만 설치하고 업데이트를 적용하지 않으면 한글 패치가 정상 동작하지 않는다. 본편 + 업데이트 PKG를 모두 설치한 뒤 패처를 실행할 것.

### 해시 검증

원본 PKG가 정상 파일인지 확인하려면 SHA-256 해시를 비교한다.

#### 본편 (PCSE00240)

| 파일 | 버전 | 크기 | SHA-256 |
|---|---|---|---|
| `Muramasa Rebirth.pkg` | 1.00 (App) | 450 MB | `339cd06ec0f19bea3c9ce40fe47d4873b365d8ad6f78845f9819edeb0d5d9b71` |
| `update.pkg` | **1.06** (Patch) | 33 MB | `1396e08a04a28a41f64f10cc762546139df1eed29cce9ca87363696d13a9388b` |
| `work.bin` | - | 512 B | `49e2550c82fe5a61e873682e84cd22b32229d0482150185abc25087b08b6ba48` |

> 한글 패치는 **본편 1.00 + 업데이트 1.06** 조합 기준으로 검증되었다. 다른 리전판이나 다른 버전에서는 패처가 원본 해시 불일치로 중단된다.

#### DLC - Genroku Legends (선택)

DLC는 모두 v1.00이며 추가 업데이트는 없다.

| DLC 에피소드 | 버전 | PKG SHA-256 | work.bin SHA-256 |
|---|---|---|---|
| **A Cause to Daikon For** (69 MB) | 1.00 | `62f46a334f79054a76b4b2644942c2a2ccb4a8271bb553f5208d60f77f922f84` | `9a6ebb5121110ad2f01ca0d0cf05e93b9b742a463746b8eb4c69ec57687b24f0` |
| **A Spirited Seven Nights' Haunting** (84 MB) | 1.00 | `9c018a639cf631b6babbe2ba48e14a06bca866f752c53a86f9436e39a236a84c` | `9d39ed0c09e446cd852715f87160f0af6882a00504d7ae455089361a879b9d89` |
| **Fishy Tales of the Nekomata** (76 MB) | 1.00 | `03e660dbf4fbeb848de1650bfe900db346fe711265e42f01a07042a421b657ba` | `9498bd7f4ed205564a46a7f3dbdb8484e156b06ee037030e1b6ab352b57f2439` |
| **Hell's Where the Heart Is** (83 MB) | 1.00 | `2af2a4de7fd1b1e1233eee86e8a039ae834d015c9ca293e217a047e5292aaf82` | `1ede67a4e510b94682937ca49c1cd7400d0b553a7c5932eac6d3c2a2ef30baa3` |

해시 계산 방법:

```powershell
# Windows PowerShell
Get-FileHash -Algorithm SHA256 ".\Muramasa Rebirth.pkg"
Get-FileHash -Algorithm SHA256 ".\update.pkg"
```

```bash
# macOS / Linux
shasum -a 256 "Muramasa Rebirth.pkg"
shasum -a 256 update.pkg
```

## 설치 방법

### 0단계 - Python 준비

패처 실행에는 Python 3.9 이상이 필요하다.

- Windows: Python 3.9 이상을 설치하고 `py -3 --version` 또는 `python --version`으로 확인한다.
- macOS: `python3 --version`으로 Python 3.9 이상인지 확인한다.

### 1단계 - Vita3K에 원본 게임 설치

1. Vita3K를 실행한다.
2. 메뉴 `File > Install .pkg` 로 본편 `Muramasa Rebirth.pkg` (v1.00)를 설치한다 (`work.bin` 또는 zRIF 필요).
3. 같은 메뉴로 `update.pkg` (v1.06)를 설치한다 (필수).
4. (선택) DLC PKG 4개(각 v1.00)를 같은 방법으로 설치한다.
5. Vita3K 앱 목록에 `Muramasa Rebirth`가 나타나고 정상 부팅되는지 확인한다.

설치 후 다음 경로에 원본 CPK가 생긴다.

```text
<Vita3K content root>/ux0/app/PCSE00240/NinPri.cpk
<Vita3K content root>/ux0/app/PCSE00240/NinPriPatch.cpk
```

기존 한글 패치를 이미 적용한 상태에서 새 버전을 설치할 때도, 패처는 처음 Vita3K에 원본 게임과 1.06 업데이트를 설치했을 때 생성된 원본 CPK를 기준으로 적용한다. 패처는 최초 적용 시 원본 CPK를 다음 폴더에 백업한다.

```text
<Vita3K content root>/ux0/app/PCSE00240/.muramasa-kor-backup/
```

백업 파일명은 패치를 처음 적용한 버전에 따라 달라진다.

```text
NinPri.cpk.v<version>.original
NinPriPatch.cpk.v<version>.original
```

예를 들어 v1.0.0에서 처음 패치했다면 다음 파일이 생긴다.

```text
<Vita3K content root>/ux0/app/PCSE00240/.muramasa-kor-backup/NinPri.cpk.v1.0.0.original
<Vita3K content root>/ux0/app/PCSE00240/.muramasa-kor-backup/NinPriPatch.cpk.v1.0.0.original
```

이전 버전의 패치가 적용된 `NinPri.cpk` / `NinPriPatch.cpk` 위에 새 패처를 바로 덮어씌우지 말고, 같은 릴리즈 폴더에서 `python3 apply_patch.py --restore`를 먼저 실행한다. 패처는 `.muramasa-kor-backup` 폴더의 `*.v*.original` 백업 중 원본 해시가 맞는 파일을 찾아 복원한다. 백업이 없거나 원본 해시가 맞지 않는 경우에만 Vita3K에서 본편과 업데이트를 다시 설치해 원본 CPK를 만든 뒤 새 패처를 실행한다.

기본 `content root` 예시:

```text
Windows: C:/Users/<username>/AppData/Roaming/Vita3K/Vita3K/fs
macOS:   ~/Library/Application Support/Vita3K/Vita3K/fs
Android: Android/data/org.vita3k.emulator/files
```

패처는 `.../Vita3K/Vita3K`와 `.../Vita3K/Vita3K/fs` 형식을 모두 자동으로 처리한다.

### 2단계 - 한글 패치 zip 다운로드 및 검증

1. [Releases](../../releases) 페이지에서 최신 `muramasa-kor-vX.Y.Z-vita3k-patcher.zip`을 받는다 (`X.Y.Z`는 최신 버전, 예: `1.2.1`).
2. 같은 릴리즈의 `...-sha256.txt`로 zip 무결성을 검증한다.

```powershell
# Windows (파일명은 받은 버전에 맞춘다)
Get-FileHash -Algorithm SHA256 .\muramasa-kor-v1.2.1-vita3k-patcher.zip
```

```bash
# macOS / Linux
shasum -a 256 muramasa-kor-v1.2.1-vita3k-patcher.zip
shasum -a 256 -c muramasa-kor-v1.2.1-vita3k-patcher-sha256.txt
```

### 3단계 - 로컬 패처 실행

패처 실행 전 Vita3K를 종료한다.

Windows:

```text
apply_windows.bat
```

macOS:

```bash
python3 apply_patch.py
```

또는 Finder에서 `apply_macos.command`를 실행한다.

패처가 Vita3K 경로를 자동으로 찾지 못하면 직접 지정한다. `--vita3k`에는 `ux0`가 들어 있는 content root 또는 그 상위 Vita3K 루트를 넣을 수 있다.

```powershell
# Windows
py -3 apply_patch.py --vita3k "C:\Users\<username>\AppData\Roaming\Vita3K\Vita3K\fs"
```

```bash
# macOS
python3 apply_patch.py --vita3k "$HOME/Library/Application Support/Vita3K/Vita3K/fs"
```

패처는 다음 작업을 수행한다.

1. `NinPri.cpk`, `NinPriPatch.cpk` 원본 SHA-256 확인
2. 원본 백업 생성: `ux0/app/PCSE00240/.muramasa-kor-backup/`
3. binary patch 적용 후 결과 SHA-256 재검증
4. `textures/import/PCSE00240/` 아래로 Vita3K 텍스처 import 복사

Vita3K 설치가 `fs` content root를 쓰는 경우, 패처는 `fs/textures/import/PCSE00240/`와 상위 Vita3K root의 `textures/import/PCSE00240/`를 함께 갱신한다.

폰트/UI 텍스처가 보이지 않으면 Vita3K 설정에서 `Configuration > Settings > GPU > Import Textures`를 켠 뒤 Vita3K를 재시작한다.

### 4단계 - Android Vita3K에 수동 적용

Android에서는 릴리즈 패처를 직접 실행하지 않는다. Windows 또는 macOS에서 3단계까지 먼저 완료한 뒤, 패치가 적용된 결과 파일을 Android Vita3K 저장소로 복사한다.

복사 전 Android Vita3K를 종료하고, Android 쪽 원본 CPK를 따로 백업한다.

PC/macOS에서 가져올 파일:

```text
<PC/macOS content root>/ux0/app/PCSE00240/NinPri.cpk
<PC/macOS content root>/ux0/app/PCSE00240/NinPriPatch.cpk
<릴리즈 압축 해제 폴더>/textures/import/PCSE00240/
```

Android Vita3K에 덮어쓸 위치:

```text
<Android content root>/ux0/app/PCSE00240/NinPri.cpk
<Android content root>/ux0/app/PCSE00240/NinPriPatch.cpk
<Android content root>/textures/import/PCSE00240/
```

기본 Android content root는 보통 다음 위치다.

```text
Android/data/org.vita3k.emulator/files
```

따라서 기본 설치라면 최종 경로는 다음처럼 된다.

```text
Android/data/org.vita3k.emulator/files/ux0/app/PCSE00240/NinPri.cpk
Android/data/org.vita3k.emulator/files/ux0/app/PCSE00240/NinPriPatch.cpk
Android/data/org.vita3k.emulator/files/textures/import/PCSE00240/*.png
```

Android Vita3K의 저장소 위치를 바꿨다면, Android 기기에서 `ux0/app/PCSE00240` 폴더를 찾아 그 상위 폴더를 content root로 사용한다. `textures/import/PCSE00240` 폴더가 없으면 직접 만든다.

복사 후 Android Vita3K에서 `Import Textures` 옵션을 켜고 게임을 실행한다. Android 빌드에서 텍스처 import 옵션이 없거나 동작하지 않으면 CPK 텍스트 패치는 적용되지만 한글 폰트/UI 텍스처가 정상 표시되지 않을 수 있다.

### 원본 복원

같은 릴리즈 폴더에서 다음 명령을 실행한다.

```bash
python3 apply_patch.py --restore
```

Windows에서는 다음처럼 실행할 수 있다.

```powershell
py -3 apply_patch.py --restore
```

복원에 사용하는 원본 백업 위치는 다음과 같다.

```text
<Vita3K content root>/ux0/app/PCSE00240/.muramasa-kor-backup/NinPri.cpk.v<version>.original
<Vita3K content root>/ux0/app/PCSE00240/.muramasa-kor-backup/NinPriPatch.cpk.v<version>.original
```

패처는 현재 릴리즈 버전명과 다른 `v*.original` 백업도 원본 해시가 맞으면 복원한다. 복원이 되지 않거나 백업이 없다면, Vita3K에서 원본 PKG와 업데이트 PKG를 다시 설치하면 된다.

## 릴리즈 파일

릴리즈에는 보통 다음 파일이 포함된다.

- `muramasa-kor-v1.0.0-vita3k-patcher.zip`
- `muramasa-kor-v1.0.0-vita3k-patcher-manifest.json`
- `muramasa-kor-v1.0.0-vita3k-patcher-sha256.txt`
- `muramasa-kor-v1.0.0-vita3k-patcher-release-notes.txt`
- `muramasa-kor-vX-realhw-patcher-beta.zip` — [실기(real PS Vita) 패치](#실기real-ps-vita-패치-베타) (`v1.3.0`부터)

### ✕ 버튼 추가팩 (선택)

선택/확인 버튼을 ○ 대신 **✕로 보고 싶은 분**을 위한 선택형 추가팩 `muramasa-kor-xbutton-vX.zip`이 함께 제공될 수 있다.
기본 패치는 ○를 그대로 쓰고, 이 팩을 추가로 덮어쓰면 버튼 표시가 ✕로 바뀐다.

- 게임이 버튼 모양을 직접 그리므로 이 팩은 **화면 표시만** 바꾼다. 실제로 ✕가 "확인"이 되게 하려면
  Vita3K 설정에서 **Enter Button Assignment = Cross** 로도 바꿔야 한다.
- 설치: 기본 패치 적용 후 `apply_xbutton.py`(또는 `apply_xbutton_windows.bat` / `apply_xbutton_macos.command`) 실행.
- 되돌리기: `python3 apply_xbutton.py --restore`.

## 실기(real PS Vita) 패치 [베타]

에뮬레이터(Vita3K)가 아닌 **실제 PS Vita 본체**에서도 한글이 표시되도록 하는 패치다. `v1.3.0`부터
별도 zip `muramasa-kor-vX-realhw-patcher-beta.zip` 으로 제공한다.

### Vita3K판과 무엇이 다른가

Vita3K판은 한글 텍스처/폰트를 hash 이름 PNG로 만들어 Vita3K의 텍스처 import 기능으로 덮어쓴다.
**실기에는 그 기능이 없으므로**, 한글 텍스처/폰트를 **CPK 내부 FTX(게임 텍스처 컨테이너)에 직접
구워 넣는다**. 실기는 업스케일(HD)이 불필요해 원본 해상도로 베이크한다. 저작권상 원본 CPK는
배포하지 않으므로, **사용자 본인의 원본 CPK로부터 패치 CPK를 생성**한다(무거운 인코딩은 사용자 PC에서 수행).

> **참고 — 이 CPK는 Vita3K에서도 로드된다.** 따라서 HD 텍스처 팩을 쓰지 않는 Vita3K 사용자는 이
> 실기용 CPK를 `ux0/app/PCSE00240/`에 넣으면 **import 폴더로 PNG를 복사하는 절차 없이** 한글이
> 표시된다. 다만 **HD 팩 사용자**는 import 방식(현행 Vita3K 패처)을 써야 한다. CPK에 한글을 베이크하면
> 해당 텍스처의 hash가 바뀌어 HD 팩(원본 hash 기준 import)이 그 텍스처엔 더 이상 적용되지 않아 한글
> 텍스처가 **원본 해상도로 떨어지기** 때문이다. 그래서 Vita3K 기본 배포는 HD 화질 지원을 위해 import
> 방식을 유지한다.

> 💡 **가장 쉬운 방법은 [통합 GUI 도구](#️-가장-쉬운-설치--통합-gui-도구-권장)다.** 아래 명령어(CLI) 방식은
> GUI가 안 되거나 자동화하려는 사용자를 위한 수동 경로다. GUI를 쓰면 아래 "요구 사항"의 파이썬/패키지
> 설치(Windows exe 기준)와 긴 명령어 입력이 필요 없다.
>
> 📘 **처음이라 막막하다면** → [실기 쉬운 설치 가이드](docs/실기-쉬운-설치-가이드.md) (rePatch 설치부터 Vita 복사까지 단계별).

### 요구 사항

- **rePatch 플러그인** (실기에 설치·활성화). CPK 파일을 통째로 override 하는 방식이다.
- Python 3.8+ 와 패키지: `pip install pillow numpy xxhash` *(GUI Windows exe를 쓰면 불필요)*
- **PC의 Vita3K에 게임이 설치돼 있어야 한다.** 패치는 *복호화된* 원본 CPK로 만드는데, 그 복호화본은
  Vita3K가 게임 설치 시 풀어 둔 `ux0/app/PCSE00240/` (+ DLC는 `ux0/addcont/...`)에 있다. 실기 본체의
  앱 데이터는 암호화돼 있어 그대로는 쓸 수 없다.

### 패치 생성·적용 (CLI — 수동/고급)

```bash
# 1) Vita3K 설치 폴더만 지정하면 복호화 CPK(본편+DLC)를 자동으로 찾아 패치 생성 (권장)
python3 tools/apply_realhw_patch.py \
  --vita3k "/path/to/Vita3K/Vita3K" \
  --out ./out
#   (직접 경로를 주려면 --ninpri/--ninpripatch[/--pack1~4] 사용 — MaiDump 등으로 뽑은 복호화 CPK)

# 2) 생성된 out/ux0/ 내용을 Vita의 ux0:/ 아래에 그대로 복사
#    ux0:/rePatch/PCSE00240/NinPri.cpk, NinPriPatch.cpk
#    ux0:/reAddcont/PCSE00240/OBOROMURAMASAPK1~4/NinPriPack1~4.cpk
# 3) rePatch 플러그인 활성화 후 게임 실행
```

- **○/✕ 버튼**: 기본은 ○. ✕로 하려면 `--enter-button cross` (+ Vita 설정 `Enter Button = Cross`).
- **커버리지**: 한글 텍스처 82종 전부 + 폰트 완성형 2350자를 CPK FTX에 매핑·베이크(누락 0).

### 베타 주의

- 실기 부팅·표시 검증은 아직 **Vita3K 기준**으로만 이뤄진 베타다. 실기 호환을 위해 CPK의 ETOC를
  무력화했다(실기에서 동작하는 기존 rePatch 패치와 동일 방식). 실기에서 문제가 있으면 제보 바란다.

## 주의

- 기본 패처는 Vita3K용이다. **실기(real PS Vita)는 별도 [실기 패치(베타)](#실기real-ps-vita-패치-베타)로 지원한다.**
- 원본 `pkg`, `cpk`, DLC 데이터는 릴리즈에 포함하지 않는다.
- 패처는 US판 `PCSE00240` 본편 1.00 + 업데이트 1.06의 원본 CPK 해시와 일치할 때만 적용된다.
- 텍스처 import는 Vita3K의 해시 기반 교체 기능을 사용한다.
- 구글에서 찾을 수 있는 `muramasa rebirth uhd` HD 텍스처 팩과 함께 사용할 수 있다 (한글 폰트/UI는 HD 베이스 위에 오버레이된다).

## 변경 이력

전체 변경 내역과 각 버전 다운로드는 [Releases](../../releases)를 본다. 최근 변경 요약:

- **v1.0.0** — 정식판 🎉 한글 폰트 완성형 2350자 확장으로 받침 깨짐·대체표기 완전 해소, 본편·DLC 대사 전수 재번역(원문 복원·사극 말투 정리), 인명·지명·용어·텍스처 표기 통일.
- **v0.9.3** — 전투 결과 화면 `평가`(Rating) 텍스처가 잘려 보이던 문제 수정.
- **v0.9.2** — 보스 전용 무기 아이템명이 한자와 섞여 깨지던 문제 수정(`BOSS` → `보스`) + UI 텍스처 편집.
- **v0.9.1** — 장비창 숫자·기호 깨짐 긴급 수정, 무기/필살기 명칭 정리, `Yes/No` 잔상 제거 등.
- **v0.9.0** — 웹 기반 UI 텍스처 편집기 도입, 지명 텍스처 60개 매칭 검수, 박스 단위 한글화 재구축.

## 자주 묻는 질문

- **실기(PS Vita)에서도 되나요?** — 된다(베타). `v1.3.0`부터 rePatch 방식 [실기 패치(베타)](#실기real-ps-vita-패치-베타)를 제공한다. 단 실기 부팅·표시는 아직 Vita3K 기준으로만 검증됐다.
- **본편만 설치하면 되나요?** — 아니다. 본편 1.00 + **업데이트 1.06**을 모두 설치해야 한다.
- **다른 리전(JP/EU)판도 되나요?** — 아니다. US판 `PCSE00240` 전용이다.
- **Android는요?** — PC/macOS에서 먼저 패치한 결과 파일을 Android Vita3K로 복사한다(위 4단계 참고).
- **글자가 깨져 보여요.** — Vita3K 설정의 `Import Textures`가 켜져 있는지 확인하고 재시작한다.
- **정식 한글판이 나오면요?** — 배포를 중단할 예정이다.

## 기여 및 개발

기여자용 빌드/배포/워크플로 문서는 [CONTRIBUTING.md](CONTRIBUTING.md)를 본다.
