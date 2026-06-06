# Muramasa Rebirth 한글 패치 v1.4.0

**파이썬·명령어 없이 마우스 클릭만으로 설치하는 통합 GUI 도구**가 추가됐습니다. 🖱️

## 🆕 통합 GUI 설치 도구

지금까지는 패치를 깔려면 파이썬을 설치하고 터미널에서 긴 명령어를 입력해야 했습니다. 특히
실기(real PS Vita) 설치가 어렵다는 의견이 많았습니다. 이번 버전부터 **창에서 클릭 몇 번으로** 끝납니다.

- **하나의 도구로 Vita3K(에뮬레이터) + 실기(real PS Vita) 모두** 패치를 만듭니다.
- **원본 CPK 경로를 자동으로 찾아줍니다.** 직접 경로를 입력할 필요가 거의 없습니다.
- **Windows: `MuramasaPatcher.exe` 더블클릭 — 파이썬 설치가 필요 없습니다.**
- macOS / Linux: zip 안의 `실행_Mac.command` / `실행_Linux.sh` 실행 (파이썬 3.9+ 필요).

### 받는 법

1. `muramasa-kor-v1.4.0-patcher-windows.zip` 을 받아 압축을 풉니다.
2. (Windows) 같은 릴리즈의 `MuramasaPatcher.exe` 를 받아 그 폴더에 넣고 더블클릭합니다.
   - 파란 SmartScreen 경고 → **"추가 정보" → "실행"**.
   - macOS "확인되지 않은 개발자" → Finder 우클릭 → 열기.
3. 창에서 **설치 대상(Vita3K / 실기)** 을 고르고 **[패치 시작]**.

자세한 안내는 저장소 README의 [빠른 시작](https://github.com/hada0127/muramasa-kor#️-빠른-시작--통합-gui-도구-가장-쉬움-권장)과
실기 사용자는 [실기 쉬운 설치 가이드](https://github.com/hada0127/muramasa-kor/blob/main/docs/실기-쉬운-설치-가이드.md)를 참고하세요.

## 기존 방식도 그대로

기존 명령어(CLI) 패처 zip(`...-vita3k-patcher.zip`, `...-realhw-patcher-beta.zip`)과 ✕ 버튼 추가팩은
그대로 제공됩니다. GUI가 안 되거나 자동화하려는 분을 위한 수동/고급 경로입니다.

## 참고

- 패치 내용 자체(번역·텍스처)는 v1.3.1과 동일합니다. 이번 변경은 **설치 편의성** 개선입니다.
- 실기 표시는 여전히 베타입니다. 문제가 있으면 제보해 주세요.
- 원본 게임 데이터는 포함하지 않습니다. 본인이 보유한 원본 CPK로 패치를 직접 만듭니다.
