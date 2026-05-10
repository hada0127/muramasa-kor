# FAIL - 실패한 작업 기록

## 2026-04-13: 1차 Wii 번역 적용 — 시스템 메시지 깨짐

### 증상
- 세이브 슬롯 화면의 "時間" → "장시간의 대난투" 등 엉뚱한 번역
- @#(17)키스케@#(18) 같은 캐릭터 라벨이 "힘", "체력"으로 뒤섞임
- 일부 아이템 설명이 2줄 → 4줄로 넘쳐서 UI 깨짐

### 원인
1. **Wii sysmsg 파일 오정렬**: Wii JP = 635 entries, Wii KR = 677 entries.
   파일별 인덱스 기준으로 동일하지 않은데 zip(jp, kr)로 매칭 시도.
   → sysmsg 전체에서 잘못된 번역 주입
2. **중복 JP 키 92개**: sysmsg에서 같은 JP 텍스트가 여러 컨텍스트에 등장.
   dict 매핑이 마지막 값을 덮어써서 컨텍스트 무시한 번역 적용
3. **아이템 설명 줄 수 확장**: Wii KR이 더 긴 문장인데 20자 단위로 쪼개 원래 2줄이던 게 4줄로 늘어남

### 해결
- sysmsg는 Wii 매칭 SKIP (파일 정렬 보장 못함)
- scemsg, _itemdata, scename만 매칭 (각각 JP/KR 인덱스 수 일치 확인됨)
- 중복 JP 키는 모든 KR 값이 동일한 경우만 안전하게 사용
- _itemdata 설명은 원래 라인 수 초과하면 SKIP (173 entries 스킵됨)
- scename은 1줄 캡, 아이템은 2줄 캡


## 2026-05-10 21:30 — auto_font_import이 시스템 폰트 깨뜨림
### 증상
- DLC 선택 화면 하단 정보(去/拭/担/抉/抗 등 한자처럼 보이는 깨진 글자) 출력
- 사용자 스크린샷 s4 (2026-05-10 21:27)
- 백희전(모모히메) / 귀조전(키스케) 캐릭터 카드의 통계 텍스트가 모두 한자 깨짐

### 원인 추정
1. `tools/.font_hashes.json`에 A8E6FDD162258699 추가 후 auto_font_import 실행
2. 6706A53E1D94C16E가 HD pack 베이스(2048x2048, 9.4MB)로 재처리됨 → 게임이 인식 못 한 가능성
3. A8E6FDD1는 cell layout이 6706A53E와 동일하지 않을 수 있음 → 한글 글리프가 잘못된 cell에 들어감
4. cleanup 단계에서 8665CE08가 export에 있음에도 일시적으로 import에서 제거됐을 수 있음

### 시도 (성공)
- 임시 백업: `temp/font_emergency_backup/` (9.4MB 6706A53E + 269KB A8E6FDD1 + 295KB 8665CE08 + 894KB 2E88068C + 936KB 87B72F6D)
- 6706A53E + 8665CE08를 `kr_textures/font/`의 안정 백업(295KB each)으로 교체
- A8E6FDD1는 import에서 제거 (rollback)
- `.font_hashes.json`을 ["6706A53E", "8665CE08"]로 복원

### 미해결 / 추후 검증
- A8E6FDD1 cell layout이 정말 SJIS 0x89CD부터 시작하는지 별도 분석 필요
- HD pack 6706A53E.png(2048x2048, 10.9MB)에 한글 오버레이를 입혀도 게임이 정상 인식하는지 미확인
- 247C255A/547720A3 메뉴 UI 한글 텍스처는 폰트가 아니므로 이번 깨짐과 무관 — 그대로 유지

### 교훈
- auto_font_import 실행 전에 import 폴더 전체 백업 필수
- `.font_hashes.json`에 새 폰트 추가 시, 한 번에 하나씩 검증 후 추가
- HD pack 베이스 vs export 베이스 결과가 다르므로 사이즈 변동 모니터링
