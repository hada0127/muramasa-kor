# Muramasa Rebirth Korean Patch

`Muramasa Rebirth` PS Vita US판(`PCSE00240`)용 한국어 패치 프로젝트다.

이 저장소와 릴리즈는 원본 게임 PKG/CPK를 포함하지 않는다. 사용자는 본인이 합법적으로 보유한 원본 게임을 Vita3K에 먼저 설치한 뒤, 릴리즈에 포함된 로컬 패처로 본인 PC의 원본 CPK에 패치를 적용한다.

## 사용자 안내

- 지원 대상: Vita3K Windows/macOS, Android 수동 복사
- 대상 타이틀 ID: `PCSE00240`
- 대상 게임: `Muramasa Rebirth` US판 (영문)
- 현재 릴리즈: `v0.7.6`
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

예를 들어 v0.7.6에서 처음 패치했다면 다음 파일이 생긴다.

```text
<Vita3K content root>/ux0/app/PCSE00240/.muramasa-kor-backup/NinPri.cpk.v0.7.6.original
<Vita3K content root>/ux0/app/PCSE00240/.muramasa-kor-backup/NinPriPatch.cpk.v0.7.6.original
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

1. [Releases](../../releases) 페이지에서 최신 `muramasa-kor-v0.7.6-vita3k-patcher.zip`을 받는다.
2. 같은 릴리즈의 `muramasa-kor-v0.7.6-vita3k-patcher-sha256.txt`로 zip 무결성을 검증한다.

```powershell
# Windows
Get-FileHash -Algorithm SHA256 .\muramasa-kor-v0.7.6-vita3k-patcher.zip
```

```bash
# macOS / Linux
shasum -a 256 muramasa-kor-v0.7.6-vita3k-patcher.zip
shasum -a 256 -c muramasa-kor-v0.7.6-vita3k-patcher-sha256.txt
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

- `muramasa-kor-v0.7.6-vita3k-patcher.zip`
- `muramasa-kor-v0.7.6-vita3k-patcher-manifest.json`
- `muramasa-kor-v0.7.6-vita3k-patcher-sha256.txt`
- `muramasa-kor-v0.7.6-vita3k-patcher-release-notes.txt`

## 주의

- 이 패치는 Vita3K 전용이다.
- 실기용 PKG나 VPK가 아니다.
- 원본 `pkg`, `cpk`, DLC 데이터는 릴리즈에 포함하지 않는다.
- 패처는 US판 `PCSE00240` 본편 1.00 + 업데이트 1.06의 원본 CPK 해시와 일치할 때만 적용된다.
- 텍스처 import는 Vita3K의 해시 기반 교체 기능을 사용한다.

## 기여 및 개발

기여자용 빌드/배포/워크플로 문서는 [CONTRIBUTING.md](CONTRIBUTING.md)를 본다.
