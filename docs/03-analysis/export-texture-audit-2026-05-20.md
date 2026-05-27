# Vita3K Export Texture Audit - 2026-05-20

- Export dir: `/Users/tarucy/Library/Application Support/Vita3K/Vita3K/textures/export/PCSE00240`
- Downloads copy dir: `/Users/tarucy/Downloads/new`
- Export total: 746
- Existing localized: 21
- No localization needed: 724
- Additional localization needed: 1

## Additional Localization Needed
- `FFFFD99DCD90D546` (256x128) - 지명/간판 텍스처. 메시지 표기 `峠の茶屋 → 고갯마루 찻집`에 맞춰 한글화 완료.

## Font Review
- `2E88068C58DD36D5`는 폰트형 텍스처지만 `auto_font_import.py`의 KANJI 32px 격자 판정에 맞지 않고 기존 `6706A53E`/`8665CE08`/`A8E6FDD1` 오버레이와 같은 구조가 아니다. 임의 오버라이드는 위험하므로 import 대상에서 제외했다.
- 원본은 `textures/originals/2E88068C58DD36D5.png` 및 `textures/originals/2E88068C58DD36D5.png`에 보관한다.

## Existing Localized
- `1823D39C0279886B` (256x128) -> `textures/kr/ui/1823D39C0279886B.png`
- `1D6742BBC0DDB7EC` (256x256) -> `textures/kr/ui/1D6742BBC0DDB7EC.png`
- `247C255A400261FF` (256x256) -> `textures/kr/ui/247C255A400261FF.png`
- `2E2003777A770327` (256x256) -> `textures/kr/ui/2E2003777A770327.png`
- `3B58B76CBA15E487` (512x256) -> `textures/kr/ui/3B58B76CBA15E487.png`
- `4AEC2546371FFF47` (1024x512) -> `textures/kr/ui/4AEC2546371FFF47.png`
- `547720A3B20C12AB` (256x256) -> `textures/kr/ui/547720A3B20C12AB.png`
- `6706A53E1D94C16E` (1024x1024) -> `textures/kr/font/6706A53E1D94C16E.png`
- `73420FAEA9F664FD` (1024x512) -> `textures/kr/ui/73420FAEA9F664FD.png`
- `74EEEC230BEE120C` (1024x512) -> `textures/kr/ui/74EEEC230BEE120C.png`
- `779C5ABBFCE00424` (512x256) -> `textures/kr/ui/779C5ABBFCE00424.png`
- `7DC6CF5A87DB1312` (512x512) -> `textures/kr/ui/7DC6CF5A87DB1312.png`
- `8725F040AEE76DFC` (512x256) -> `textures/kr/ui/8725F040AEE76DFC.png`
- `88A7A10233A61E85` (512x512) -> `textures/kr/ui/88A7A10233A61E85.png`
- `8EFF960FC088FDD7` (1024x512) -> `textures/kr/ui/8EFF960FC088FDD7.png`
- `A3BE57CE9854B5CC` (1024x1024) -> `textures/kr/ui/A3BE57CE9854B5CC.png`
- `A3CBE285F1E92FCA` (512x256) -> `textures/kr/ui/A3CBE285F1E92FCA.png`
- `A8E6FDD162258699` (1024x1024) -> `textures/kr/font/A8E6FDD162258699.png`
- `ADE2B8B5998887A9` (256x128) -> `textures/kr/ui/ADE2B8B5998887A9.png`
- `DF66CADDABE022E3` (512x512) -> `textures/kr/ui/DF66CADDABE022E3.png`
- `E8E01EAF5D41DB52` (512x512) -> `textures/kr/ui/E8E01EAF5D41DB52.png`

## Full Lists
전체 3분류 명단은 `translations/export_texture_audit_2026-05-20.json`에 저장했다. Markdown에는 긴 `no_localization_needed` 목록을 반복하지 않는다.

## Ending 完 Handling
- `2E88068C58DD36D5`에 임시로 넣었던 `完→완` 오버레이는 구조 불일치로 제거했다.
- DLC 엔딩의 `完`이 다시 확인되면 실제 해당 텍스처/hash 기준으로 처리해야 한다. 현재 export 기준 독립 엔딩 `完` UI 텍스처는 확인되지 않았다.

### 2026-05-27 출처 확정 (codex+직접 조사)
- DLC 엔딩 `完`은 export/originals 텍스처가 **아니라**, 설치된 DLC 팩 CPK 내부의 Pack별 GUI 텍스처다.
  - `OBOROMURAMASAPK1~4/NinPriPackN.cpk` → `GUI/Ending_P1~P4.ftx` (+ `Ending_P*.mbs`)
  - 경로: `~/Library/Application Support/Vita3K/Vita3K/fs/ux0/addcont/PCSE00240/OBOROMURAMASAPKn/`
  - 각 1024×1024 캐릭터 일러스트 + 좌하단 큰 흰 붓글씨 `完`(bbox≈x1-320, y430-850). 단일 글리프 아님.
- export 폴더(747개) 전수 + md5/NCC 매칭 — 일치 텍스처 없음 → **Vita3K import hash 미확보**.
- 본편 엔딩은 별개: `E4A9FD9D2047280B`(2048×1024) 원본 "The End" → "완 결"로 한글화 완료.
- sysmsg 엔딩 텍스트(#255 본편, #279~282 DLC)는 이미 "완결" 번역됨(텍스트 OK).
- **한글화 미완(보류, 2026-05-27 사용자 결정)**. 방법 2가지:
  (A) 게임에서 각 DLC 엔딩을 texture export 켜고 띄워 4개 hash 확보 → `완 결` 오버레이.
  (B) DLC 팩 CPK의 `Ending_P*.ftx` 직접 교체 — hash 불필요·전 사용자 적용. 단 **FTX 재인코더(DXT5+PS Vita 스위즐) 신규 제작 필요**(현 repo엔 decoder `ftx_extract.py`만 있음).
  - FTX SHA-256: P1 `0a88723820badd83…`, P2 `1222f3f0ea4cecb2…`, P3 `b0148bd8f76aaa1e…`, P4 `85e27daa7e03003c…`
