# 무라마사 리버스 한글패치 v1.3.0

**실제 PS Vita 본체(실기)에서도 한글이 나오는 [베타] 패치**가 새로 추가됐습니다. 🎮

## 🆕 실기(real PS Vita) 패치 [베타]

지금까지 한글 패치는 Vita3K 에뮬레이터 전용이었습니다. 이번 버전부터 **실제 Vita 본체에서도**
한글을 볼 수 있는 패치를 별도 zip(`muramasa-kor-v1.3.0-realhw-patcher-beta.zip`)으로 제공합니다.

- **방식**: rePatch 플러그인용. 한글 텍스처/폰트를 게임 CPK 내부에 직접 구워 넣습니다
  (실기엔 Vita3K의 텍스처 교체 기능이 없기 때문).
- **저작권**: 원본 CPK는 배포하지 않습니다. 동봉된 도구로 **본인의 원본 CPK에서 패치를 생성**합니다.
- **커버리지**: 한글 UI 텍스처 82종 전부 + 폰트 완성형 2,350자를 CPK에 매핑·베이크(누락 없음).
- **○/✕ 버튼**: `--enter-button cross` 로 ✕ 선택 가능(Vita 설정 Enter Button = Cross 와 함께).

### 사용법 (요약)
1. `pip install pillow numpy xxhash`
2. 본인 원본 CPK로 패치 생성:
   ```
   python3 tools/apply_realhw_patch.py \
     --ninpri NinPri.cpk --ninpripatch NinPriPatch.cpk \
     --pack1 NinPriPack1.cpk ... --out ./out
   ```
3. 생성된 `out/ux0/` 내용을 Vita의 `ux0:/` 아래에 복사 → rePatch 활성화 → 실행.

자세한 안내는 zip 안의 `README_실기패치.txt` 또는 저장소 README의 "실기 패치" 섹션을 참고하세요.

### ⚠️ 베타 주의
실기 부팅·표시는 아직 **Vita3K 기준으로만 검증**된 베타입니다(개발 환경에 실기가 없음).
실기 호환을 위해 CPK의 ETOC를 무력화했습니다(실기에서 동작하는 기존 rePatch 패치와 동일 방식).
실기에서 문제가 있으면 제보 부탁드립니다.

## Vita3K 패치 (기존)

기존 Vita3K용 패처(`muramasa-kor-v1.3.0-vita3k-patcher.zip`)와 ✕ 버튼 추가팩은 그대로 제공됩니다.
번역·폰트(완성형 2,350자)·표기 통일 등 **v1.2.3까지의 내용은 그대로** 포함됩니다.

> 참고: 실기용 CPK는 Vita3K에서도 로드됩니다. HD 텍스처 팩을 쓰지 않는 Vita3K 사용자는 실기용 CPK를
> 앱 폴더에 넣으면 텍스처 import 복사 없이 한글이 표시됩니다. 단 HD 팩 사용자는 기존 Vita3K 패처(import 방식)를
> 그대로 쓰는 것이 화질상 유리합니다.

즐겁게 플레이하세요! 🗡️
