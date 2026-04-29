# Muramasa Rebirth Korean Patch

`Muramasa Rebirth` PS Vita US판(`PCSE00240`)용 한국어 패치 프로젝트다.

이 저장소는 원본 게임 데이터를 포함하지 않는다. 배포물은 Vita3K 기준으로 만든 패치 zip이며, 사용자는 합법적으로 보유한 원본 게임이 필요하다.

## 사용자 안내

- 지원 대상: Vita3K
- 대상 타이틀 ID: `PCSE00240`
- 대상 게임: `Muramasa Rebirth` US판 (영문)
- 배포 형식: Vita3K 폴더에 덮어쓰는 zip

패치 zip 내부 구조:

```text
ux0/app/PCSE00240/NinPri.cpk
ux0/app/PCSE00240/NinPriPatch.cpk
```

## 원본 게임 준비

이 패치는 본인이 합법적으로 보유한 원본 게임에 적용하는 용도다. 저장소나 릴리즈에는 원본 PKG/CPK가 포함되지 않는다.

### 필요한 PKG 파일

본편 + 업데이트 PKG는 필수, DLC PKG는 4개 에피소드를 추가로 즐기려면 필요하다. 모든 PKG는 정품 소유자가 합법적으로 확보한 파일을 사용할 것.

> 본편만 설치하고 업데이트를 적용하지 않으면 한글 패치가 정상 동작하지 않는다. 본편 + 업데이트 PKG를 모두 설치한 뒤 한글 패치를 덮어쓸 것.

### 해시 검증

원본 PKG가 정상 파일인지 확인하려면 SHA-256 해시를 비교한다.

#### 본편 (PCSE00240)

| 파일 | 버전 | 크기 | SHA-256 |
|---|---|---|---|
| `Muramasa Rebirth.pkg` | 1.00 (App) | 450 MB | `339cd06ec0f19bea3c9ce40fe47d4873b365d8ad6f78845f9819edeb0d5d9b71` |
| `update.pkg` | **1.06** (Patch) | 33 MB | `1396e08a04a28a41f64f10cc762546139df1eed29cce9ca87363696d13a9388b` |
| `work.bin` | — | 512 B | `49e2550c82fe5a61e873682e84cd22b32229d0482150185abc25087b08b6ba48` |

> 한글 패치는 **본편 1.00 + 업데이트 1.06** 조합 기준으로 검증되었다. 업데이트는 1.06이 마지막 버전이며, 다른 버전이 들어오면 동작이 보장되지 않는다.

#### DLC — Genroku Legends (선택)

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
Get-FileHash -Algorithm SHA256 .\Muramasa Rebirth.pkg
Get-FileHash -Algorithm SHA256 .\update.pkg
```

```bash
# macOS / Linux
shasum -a 256 "Muramasa Rebirth.pkg"
shasum -a 256 update.pkg
```

해시가 위 표와 다르면 손상된 파일이거나 다른 리전판일 수 있다. 한글 패치는 US판(`PCSE00240`) 전용이며, JP판(`PCSH00211` 등)에는 적용되지 않는다.

## 설치 방법

### 1단계 — Vita3K에 원본 게임 설치

1. Vita3K를 실행한다.
2. 메뉴 `File > Install .pkg` 로 본편 `Muramasa Rebirth.pkg` (v1.00)를 설치한다 (`work.bin` 또는 zRIF 필요).
3. 같은 메뉴로 `update.pkg` (v1.06)를 설치한다 (필수).
4. (선택) DLC PKG 4개(각 v1.00)를 같은 방법으로 설치한다.
5. Vita3K 앱 목록에 `Muramasa Rebirth`가 나타나고 정상 부팅되는지 확인한다.

설치 후 다음 경로에 원본 CPK가 생긴다.

```text
<Vita3K pref_path>/ux0/app/PCSE00240/NinPri.cpk
<Vita3K pref_path>/ux0/app/PCSE00240/NinPriPatch.cpk
```

Windows 기본 경로 예시:

```text
C:/Users/<username>/AppData/Roaming/Vita3K/Vita3K
```

> 한글 패치를 덮어쓰기 전에 위 두 CPK의 원본 백업을 권장한다. 문제가 생기면 그대로 복원하면 된다.

### 2단계 — 한글 패치 zip 다운로드 및 검증

1. [Releases](../../releases) 페이지에서 최신 `muramasa-kor-vX.Y.Z-vita3k.zip`을 받는다.
2. 같은 릴리즈의 `muramasa-kor-vX.Y.Z-vita3k-sha256.txt`로 zip 무결성을 검증한다.

```powershell
# Windows
Get-FileHash -Algorithm SHA256 .\muramasa-kor-vX.Y.Z-vita3k.zip
```

```bash
# macOS / Linux
shasum -a 256 muramasa-kor-vX.Y.Z-vita3k.zip
# 또는
shasum -a 256 -c muramasa-kor-vX.Y.Z-vita3k-sha256.txt
```

### 3단계 — 패치 적용

1. Vita3K가 실행 중이면 종료한다.
2. zip을 Vita3K `pref_path` 폴더에 풀어 **덮어쓴다**.
3. 다음 두 파일이 한글 패치 버전으로 교체되었는지 확인한다.

```text
ux0/app/PCSE00240/NinPri.cpk
ux0/app/PCSE00240/NinPriPatch.cpk
```

### 4단계 — 동작 확인

1. Vita3K를 실행하고 `Muramasa Rebirth`를 시작한다.
2. 타이틀 화면, 메뉴, 대사가 한글로 표시되는지 확인한다.
3. 폰트가 깨져 보이면 Vita3K를 한 번 재시작한다 (텍스처 import 적용).

### 원본 복원

문제가 생기면 백업해 둔 원본 CPK를 다시 덮어쓰면 된다.

```text
ux0/app/PCSE00240/NinPri.cpk        ← 원본 본편 CPK 복사
ux0/app/PCSE00240/NinPriPatch.cpk   ← 원본 업데이트 CPK 복사
```

PKG부터 다시 설치하는 방법도 동일하게 동작한다.

## 릴리즈 파일

릴리즈에는 보통 다음 파일이 포함된다.

- `muramasa-kor-vX.Y.Z-vita3k.zip`
- `muramasa-kor-vX.Y.Z-vita3k-manifest.json`
- `muramasa-kor-vX.Y.Z-vita3k-sha256.txt`

## 주의

- 원본 `pkg`, `cpk`, DLC 데이터는 포함하지 않는다.
- 실기용 패키지 설치본이 아니라 Vita3K 덮어쓰기용 배포를 기준으로 한다.
- 문제가 생기면 원본 `NinPri.cpk`, `NinPriPatch.cpk`로 복원하면 된다.

## 기여 및 개발

기여자용 빌드/배포/워크플로 문서는 [CONTRIBUTING.md](CONTRIBUTING.md)를 본다.

