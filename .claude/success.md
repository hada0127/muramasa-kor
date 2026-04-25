# SUCCESS - 성공한 작업 기록

## 2026-04-25: E8E01EAF5D41DB52 스킬 아틀라스 라벨 번역 재검수 (27건 수정)

### 문제
`textures/work/E8E01EAF5D41DB52.json`의 라벨 영어→일본어 매핑이 추정(confidence med/low)으로 되어 있어 27건이 잘못됨. 예: Hazy Slash와 Misty Slash가 서로 뒤바뀜.

### 근거
- `extracted/NinPriPatch_full/{msgsheet,_US/msgsheet}/_itemdata.nms`를 nms_parser로 JSON export
- US↔JP 인덱스 정렬: 스킬 블록은 **US[595]=JP[1638], offset=1043**. 아이템 블록은 1:1 (US[40]=JP[40]=青銅の鏡 등)
- 일본어명을 `translations/proper_nouns.json` items 섹션(edit 필드 우선)으로 한국어로 변환 → 시스템 번역과 자동 일체화
- `朧→오보로`, `家老→가신` 등 의도적 오버라이드는 `edit` 필드로 이미 proper_nouns에서 관리되므로 영향 없음

### 주요 수정
- Hazy Slash ↔ Misty Slash 스왑 복구 (霞斬り=Misty=안개자르기, 分身霞斬り=Hazy=안개자르기 2)
- Vengeance ↔ Retribution, Tornado ↔ Vortex, Faerie Inferno ↔ Faerie Assault 스왑 복구
- Soaring Lark 雲雀→飛燕丸鋸 (종달새→톱날리기)
- Falling Moon/Mirrored Moon 弧月계→月ノ輪계 (고월→달무리 2, 십육야→달무리 3)
- Divine Blade 必殺の刃→星天風車 (필살의 검→나선은하)
- Focus Slash 月下一閃→八丁斬り (달빛베기→채썰기)
- Hell's Gate 地獄独楽→天地一閃 (지옥팽이→천지베기)
- Ground Runner 地走り→地虫 (땅달리기→땅벌레)
- Mountain Gale 烈風走破→巌おろし (강풍→바위치기)
- Tempest 鬼火嵐→烈風走破 (화염폭풍→강풍)
- Chaos Roar 百鬼乱閃 省エネ→幻影雷光 (백귀난섬 절약→섬광)
- 기타 Faerie/Moon 시리즈 넘버링 바로잡음, Sake→般若湯→반야탕

### 검증
수정 후 모든 `src_ja` 값이 `proper_nouns.json` 매핑과 정확히 일치함 (Monster Cat, Demon Child 2개만 PN 미등록이지만 직역 괴묘/귀자 유지).

---

## 2026-04-15: UI 텍스처 수동 한글화 (사용자 직접 편집)

### 완료 텍스처 (kr_textures/ui/)
| 해시 | 내용 | 크기 | 비고 |
|---|---|---|---|
| 73420FAEA9F664FD | 본편 타이틀 "오보로 무라마사" | 1024x512 | 이전 완료 |
| 8EFF960FC088FDD7 | 게임 로고 그림자 제거 | 1024x512 | 이전 완료 |
| ADE2B8B5998887A9 | DLC 부제 "겐로쿠 괴기담" | 256x128 | 이전 완료 |
| DF66CADDABE022E3 | 메인 UI 텍스트 (Victory, Save, Load, Cooking 등) | 512x512 | 신규 |
| A3BE57CE9854B5CC | 스토리/DLC 제목 (영문 부제 한글화) | 1024x1024 | 신규 |
| 3B58B76CBA15E487 | 시스템 UI (Please, Return, 시작, 새게임, Store 등) | 2048x1024 | 카탈로그 미등록, 신규 발견 |
| E4A9FD9D2047280B | 엔딩 "완 결" 텍스트 | 2048x1024 | 카탈로그 미등록, 신규 발견 |

### 진행 상태
- Phase 4 텍스처 한글화: **카탈로그 9개 중 5개 완료 + 신규 2개 = 총 7개 완료**
- 미완료 (카탈로그): 7DC6 (아이템명), E8E0 (스킬명), 74EE (스토리 제목+라벨), 1823 (지역명), 79C9 (오프닝 나레이션)
- 원본 텍스처 정리: textures/text/ 폴더에 10개 텍스트 텍스처 원본 복사 완료

---

## 2026-04-14: 어빌리티 화면 Skill/Effect 깨짐 1차 수정 (font-mapping-repair)

### 문제
어빌리티 화면의 Skill / Effect 열이 `닷맽않딸돕맒 담햝맣`, `묘혔떏뗄맶 땀맒` 형태로 완전 깨짐.
동시에 식당 메뉴·대장간 칼 이름·대사 런타임 치환도 잔재.

### 근본 원인 (RCA)
US 버전 `NinPriPatch/_US/msgsheet/_itemdata.nms`는 EU/JP 파일과 **완전히 다른 인덱스 레이아웃**을 가짐:
- 0-369: 아이템 + 설명 (JP 인덱스와 정렬됨)
- 370-593: 칼 이름(짝수) + 칼 설명(홀수) 쌍
- 594: separator `-`
- 595-1176: **영문 컴팩트 스킬명 테이블** (JP에는 없음)

기존 `tools/build_patch.py`가 US 파일을 `_itemdata` (3565-entry) 번역 테이블로 index-mode 패치 →
영문 스킬명 슬롯에 한글 "금강 팔찌" 등 accessory 이름이 덮여쓰여 **엉뚱한 위치에 Korean bytes 주입**.
어빌리티 화면은 칼 설명(홀수 인덱스) 안에서 "Secret Art:" / "Effect:" 마커를 파싱해
Skill / Effect 열을 추출하는데, 칼 설명이 한글로 바뀌면서 파서가 **랜덤 byte offset**을 읽어 깨짐 발생.

### 수정 (commit ccfdcbc)
`tools/build_patch.py`:
- `rebuild_nms`에 `index_range=(start,end)`, `skip_indices=set(...)` 파라미터 추가
- 새 매치 모드 `index_range` + `copy` 추가
- US `_itemdata` 패치 범위: `index_range=(0, 594)`, `skip_indices={371, 373, …, 593}` (홀수 칼 설명)
- 결과: `_itemdata_US: 482/1177 matched (index_range)`

### 검증 (데이터 레벨)
`patch_patch/_US/msgsheet/_itemdata.nms` 디코드:
| idx | 원문 (EN) | 패치 후 |
|---|---|---|
| 2 | Bamboo Flask | `대나무수통` (Korean) |
| 384 | Peony Blade | `「모란」무라마사` (Korean) |
| 385 | `Attack: 18 / Secret Art: Soaring Lark I / Effect: Attack Boost I` | **영문 원본 유지** |
| 388 | Celestial Origins | `하세베쿠니시게` (Korean) |
| 389 | `Attack: 17 / Secret Art: Divine Blade I / …` | **영문 원본 유지** |
| 608 | Divine Moon I | **영문 원본 유지** (594+ 범위 외) |

### 검증 (라이브 인게임 - 1회 성공 후 Windows 포커스 문제로 반복 실패)
첫 실행에서 어빌리티 화면 Equipment 열이 `하세베쿠니시게 / [아야메] 무라마사 / [모란] 무라마사` 한글 정상 표시 확인.
Skill / Effect 열은 영문 원본이 Korean-overlay 아틀라스로 렌더되어 여전히 읽기 어려움 → Phase 2로 분리.

### 남은 트레이드오프
- ✅ Equipment 열 (칼 이름): 한글
- ✅ 대부분 아이템 이름 (0-369): 한글
- ⚠️ 칼 상세 설명 바닥 텍스트 `공: 18 오의: 비연환톱 …` → **영문으로 되돌아감** (홀수 skip)
- ⚠️ Skill/Effect 열: 영문 원본 (읽기 가능, 깨짐 없음)

### Phase 4-6 완료 (2026-04-14)

**Phase 4 — 대사 "등" 치환 제거 (commit 865dbdf)**
mapping에 없는 95개 한글 syllable이 SJIS 인코딩 실패 → `?` (0x3F) →
런타임 오버레이 셀 255(=등)에서 렌더 → `따윈`→`따등` 깨짐.
`translations/char_substitutions.json` 생성 (unmapped → phonetic nearest: 윈→위, 똥→또, 맘→마 등)
+ `build_patch.py` encoder fallback 단계에 사전 매치 추가.
결과: `따위 요만큼도` 정상 표시.

**Phase 5 — 소바 가게 JP kanji → 한글 (commit 865dbdf 일부)**
가게 메뉴는 폰트 atlas `A8E6FDD162258699` 사용 (기존 overlay 미적용).
`auto_font_import.py` 세션 detect에 걸려 이번에 overlay 생성.

**Phase 6a — sysmsg 오번역 수정 (commit 140409d)**
sysmsg[770-778] 항목이 Wii scemsg 병합 잔재로 **장소/캐릭터 이름**(『이누가미 겐시로』, 「무사시」에도 성곽 해자 등)이 음식명 자리에 들어가 있었음. `sysmsg_main[495-515]`의 정상 번역으로 8 entry 재동기화.
결과: `쌀밥 / 자루 소바 / 청어 소바 / 키츠네 우동` 정상.

**Phase 6b — 덴 글자 복구 (commit d08e145)**
`덴`=0x8AF1 → 로컬 셀 224. 그런데 이 셀은 ASCII space(0x20)가 렌더되는 위치라 hd_font_import이 **transparent로 클리어** → 덴 글리프 증발. `덴푸라 우동` → `푸라 우동`, `덴고로` → ` 고로`.
덴을 로컬 960 (0x8EE1, ASCII zone 선두, 실제로 아무 글리프 미사용)으로 재배치.
`kr_sjis_mapping.json` 수정 + auto_font_import / hd_font_import 재생성.
결과: `덴푸라 우동` 정상 표시.

---

### Phase 3 완료 (commit 9cfc94d, 사용자 확인 2026-04-14)
블레이드 설명(홀수 371-593) 한글 복구 — `skip_indices` 제거.
스킬명 테이블이 Korean이라 Ability 파서가 description 대신 skill-ID로 조회.
결과: Forge/Equipment 상세 하단 `공: 18 오의: 비연환톱 효: 공격 강화…` 한글 정상 + Ability 화면 유지.
매치 건수 773 → 885 (+112 description).

### Phase 2 완료 (commit 673cf8f, 사용자 확인 2026-04-14)
NinPriPatch US의 스킬명 테이블(595-1176)과 `_itemdata_main`(878 entries) 사이의
**+8 인덱스 시프트를 경험적으로 확증** (22개 샘플 - Misty Slash→안개자르기, Divine Moon→월광 등).

`build_patch.py`에 `custom_idx` 매치 모드 + `us_itemdata_hybrid` 빌더 추가:
- `[0, 594)` ∩ ¬(홀수 371-593): `_itemdata[i].ko`
- `[595, 1177)`: `_itemdata_main[i-8].ko`

결과: `US[662] = 나선은하`, `US[608] = 월광`, `US[595] = 안개자르기` 등.
사용자 실기 확인: **어빌리티 화면 Skill/Effect 열 정상 한글 표시**.

---

## 2026-04-13: 전각 문자 렌더링 깨짐 수정 (fullwidth-normalize)

### 문제
사용자 스크린샷에서 무기 설명·상태 화면의 전각 문자가 한글 글리프로 깨짐:
- `：` (full-width colon) → `봐`
- `（` → `사`, `）` → `삭`
- `\u3000` (전각 공백) → `볶` (`붐`처럼 보임)
- `１２３...` (전각 숫자) → `웨`, `위`, `윗`, `유` 등

### 원인 (경험적 발견)
게임이 SJIS 0x81xx/0x82xx 바이트를 폰트 텍스처의 `local_cell = sjis_cell + 448` 위치에서 렌더링.
Korean 글리프가 해당 위치에 있어 엉뚱한 한글로 표시됨.
- `：` (0x8146) → cell 6 → local 454 = 봐
- `（` (0x8169) → cell 41 → local 489 = 사
- `）` (0x816A) → cell 42 → local 490 = 삭

Python `c.encode('shift_jis')` fallback이 이 raw SJIS 바이트를 출력한 것이 문제.

### 수정 (`tools/build_patch.py`)
- `FULLWIDTH_NORMALIZE` 딕셔너리 추가 — 전각→ASCII 반각 매핑
- `_normalize_text()` 전처리로 encode 전에 변환
- 대상: 전각 ASCII (`：（）！？％＋－＝／＊＃…`), 전각 숫자 `０-９`, 일본 문장부호 (`、。・「」『』`), 전각 공백, 특수기호 `…◆`
- 결과: 모든 전각 문자가 `ASCII_SJIS_MAP` (pos 960+) 경로로 encode → 폰트 텍스처의 ASCII 영역에서 정상 렌더링

### 검증 (Vita3K 실행 + 스크린샷 비교)
- Before: `상태붐정상`, `공격봐 1 2`, `사용조건 사 힘봐3 체력봐3`
- After:  `상태 정상`, `생명력 50 회복 생기 10 획득` — 깨짐 없음

### 부산물
- `@#（81）` 형태 제어 코드: 전각→반각 정규화 후 기존 `@#(\d+)` 정규식에 매칭 → 올바르게 raw bytes로 보존

### 알려진 남은 이슈 (deferred)
게임 런타임 `%D` 포맷 치환 (세이브 시간 등): 게임이 raw ASCII 0x30-0x39를 출력 → 폰트 텍스처 cell 240-249에서 렌더링 → 한글 `둔/둘/둠/둥/둬/뒤/뒷/드/득/든` 표시.
해당 한글은 사용빈도 매우 높음 (`들` 459회, `득` 227회, `드` 181회, `든` 139회) — 텍스처 overlay로 교체하면 번역 손상.
증상: "Time 둘시간 드분" (= "1시간 7분"), 세이브 메뉴의 "Blades Owned" 숫자.
해결은 게임 바이너리 분석 or alt font texture 탐색 필요.

### 빌드 결과
- `build_patch.py`: 전 NMS 정상 빌드 (match rate 변화 없음, 인코딩 교체만)
- `cpk_patch.py`: NinPri +149KB, NinPriPatch +264KB
- Vita3K 부팅/세이브 로드/메뉴 탐색 정상

---

## 2026-04-13: 지명·Act 라벨·오역 대량 수정 (place-name-fix feature)

### 문제 요약
- DLC 진입 시 장면 전환 지명 헤더 깨짐
- 스토리 선택 Act 라벨 깨짐 (범위 밖 SJIS 바이트)
- 일부 번역이 다른 텍스트로 표시 (CRLF/LF 불일치)
- `武蔵` → "사무라이시"(5자) 오역, `無事` → "사무라이히/하" 오역

### PDCA 진행 (Option C — 데이터 수정 + 감사 도구)
- **Plan**: `docs/01-plan/features/place-name-fix.plan.md`
- **Design**: `docs/02-design/features/place-name-fix.design.md`
- **Do**: 5단계 구현 완료

### 구체 수정
1. **오역 제거**
   - 武蔵 → 무사시 일괄 치환 (32 엔트리, scemsg/sysmsg)
   - 無事 → 무사히/무사하/무사했 (12 엔트리, scemsg)
2. **Act 라벨 재인코딩**
   - ASCII 숫자(0x8EF3~8EF8 OOR) → 전각 숫자(0x8251~0x8256, JP 기호 페이지)
   - "제2막~제7막" → "제２막~제７막"
   - 줄거리 요약 내 Act 참조도 동일 교체 (28 엔트리)
3. **DLC 지명 번역 추가**
   - sysmsg #703~778 `ko=""` → 76개 엔트리 Korean 추가
   - `「미카와」 도카이도 후지카와・아카사카 간 가도` 등 새 전환 헤더
4. **ASCII 구두점 전각화 (sysmsg만)**
   - `-` → `・`, `!` → `！` (38 엔트리)
5. **CRLF/LF 라인엔딩 정규화**
   - NinPri(`\r\n`) vs NinPriPatch_full(`\n` 혼재) 불일치 → 매칭 실패
   - `build_patch.py` 내 `_norm()` 헬퍼로 매칭 시 통일
   - sysmsg 836→899 매칭, scemsg 17개 추가 매칭

### 신규 도구
- `tools/audit_oor.py` — 패치 NMS의 범위 밖 SJIS 바이트 감사
  - `--summary`, `--baseline`, `--output json` 지원
  - baseline: `docs/03-analysis/oor_baseline.json` (전체 17,329 메시지 중 8,143개 OOR)
- `tools/capture_scene.py` — Vita3K 단계별 장면 전환 캡처

### 검증
- 스토리 선택 Play Style 설명 "마음 편히 대폭주하기 위한 유파입니다..." 정상 렌더링
- 타이틀 "오보로 무라마사" 부제 정상
- DLC 진입 후 세이브/로드 UI 정상
- scemsg 2186/2247, sysmsg 899/965 매칭

### 미해결 / 후속 과제
- OOR 시스템 이슈 3,328 메시지 (ASCII `.` `,` `'` 등이 OOR 셀로 매핑)
- 폰트 오버레이 커버리지 1024-1053 (lowercase a-z)
- 더 깊은 DLC 시나리오(2~4) 전수 대사 검증

## 2026-04-13: DLC 난이도 화면 배경 텍스처 깨짐 수정

### 문제
- DLC 난이도 선택 화면(Legend/Chaos) 좌우 배경에 한글 폰트 아틀라스가 그대로 노출
- 원인: `hd_font_import.py`의 `font_hashes` 리스트에 `87B72F6DB3C3FBDC`가 잘못 포함됨
- 해당 해시는 실제로는 폰트가 아니라 **식물/풀숲 배경 텍스처** (HD 팩 원본에서 확인)

### 해결
- `tools/hd_font_import.py`: `font_hashes`에서 `87B72F6DB3C3FBDC` 제거 (`6706A53E1D94C16E`만 남김)
- HD 팩 원본(`87B72F6DB3C3FBDC.png`)을 import 폴더에 복원 (2048 리사이즈 + pngquant → 597KB)
- 실제 폰트 텍스처: `6706A53E1D94C16E` (HD 팩 ASCII+Kanji), `8665CE082D339B33` (세션 Kanji)

### 검증
- DLC 난이도 화면 배경 정상 렌더링 확인 (`screenshots/step5_difficulty_settled.png`)
- 좌우 배경이 폰트 아틀라스 대신 원본 식물/UI 배경으로 표시

## 2026-04-13: 공백 반칸 렌더링 복구

### 문제
- 이전: space(' ')를 ASCII_SJIS_MAP의 960+ 슬롯으로 리맵 → 게임이 한글 셀(32px 풀폭)로 렌더링 → 공백이 한칸 크기
- "오보로  무라마사를  플레이합니다" 형태로 과도한 여백

### 해결
- `tools/build_patch.py`: `_build_ascii_sjis_map()`에서 0x20(space)만 예외 처리, 1-byte 0x20으로 출력
- `tools/auto_font_import.py`, `tools/hd_font_import.py`: KANJI 텍스처 local cell 224 (= 192+0x20, pixel x=0,y=224 32x32 영역) 투명 클리어
- 게임이 raw 0x20을 position=192+0x20=224에서 반폭(16px) 렌더링 → 정상 반칸 공백
- 다른 ASCII 문자(!, ?, 숫자 등)는 여전히 960+ 2-byte 리맵 유지

### 검증
- DLC 선택 화면 하단 시스템 메시지 "오보로 무라마사를 플레이합니다" — 반칸 공백 정상 렌더링
- 이상한 글자 노출 없음 (cell 224가 투명하게 비어 있음)
- `screenshots/dlc_select_spacecheck.png`

## 2026-04-13: Wii 한글 패치 기반 번역 전면 교체

### 작업 내용
- Wii USA판 한글 패치(사람이 검수한 번역)를 기준으로 Vita 번역 교체
- JP 원문 매칭으로 1116개 본편 scemsg 대사 전부 Wii 번역으로 대체
- 3줄/18자 제약에 맞춰 자동 재포매팅 (`tools/apply_wii_translations.py`)
- `tools/polish_dlc.py`로 DLC 번역 고유명사 통일 (카가미가, 해골곡, 쓰나요시 등)

### 교체 통계 (최종, sysmsg 안전 스킵 반영)
- scemsg: 1115 entries Wii 번역 + DLC 17 term polish
- sysmsg/sysmsg_main: 0 (SKIP — 파일 정렬 안됨)
- _itemdata: 541, _itemdata_main: 628 entries (설명 줄 수 초과 시 SKIP)
- scename_main: 67 entries (인명/지명 고유명사)

### 고유명사 주요 변경
- 사무라이 → 무사
- 해골 골짜기 → 해골곡
- 카가미 가문 → 카가미가
- 도쿠가와 츠나요시 → 도쿠가와 쓰나요시
- 피에 미친 비사문 → 치구루이비샤몬
- 시카미 단조 → 시카미 단죠
- 막걸리 → 도부로쿠, 감 → 홍시, 귤 → 밀감
- 치유환/회복환/웅담환 → 치료환약/회복환약/곰환약

### 테스트
- 빌드/설치/Vita3K 실행 자동화 성공
- `screenshots/genroku_dialogue.png`: 겐로쿠 Legend 선택 화면 Wii 스타일 한글 렌더링 확인

## 2026-04-11: 대사(scemsg) 미출력 버그 해결

### 근본 원인
- **NinPriPatch.cpk가 NinPri.cpk의 scemsg를 완전히 오버라이드**
- NinPriPatch = 업데이트 패치 (본편+DLC 대사 2,178개 US / 2,252개 JP)
- 기존에 NinPri.cpk만 패치 → 게임이 NinPriPatch의 원본 scemsg를 로드 → 패치 무시
- cpk_extract 버그: NinPriPatch scemsg(268KB)를 480B로만 추출

### 해결
- NinPriPatch에서 전체 scemsg 수동 추출 (CRILAYLA 디컴프레스)
- build_patch.py: NinPriPatch_full/scemsg_full.nms를 템플릿으로 사용
- NinPriPatch.cpk 패치: 본편 대사 1,116개 번역 적용 (DLC ~1,062개 미번역)
- 대사 렌더링 정상 확인 (폰트 텍스처 문제 아님 확인)

### CPK 로딩 우선순위 (확인)
```
NinPriPack1~4.cpk → DLC 에셋 (그래픽/사운드/맵, msgsheet 없음)
NinPriPatch.cpk   → 업데이트 패치 (본편+DLC 대사, NinPri 오버라이드)
NinPri.cpk        → 베이스 게임 (NinPriPatch가 덮어씀)
```

## 2026-04-10: DLC + 본편 미커버 텍스처 397개 AI 업스케일 성공

### 성과
- **FTX 추출 도구** (`tools/ftx_extract.py`): FTEX/GXT → PNG 디코딩 (DXT5/BC3 + Morton unswizzle)
- **일괄 업스케일 도구** (`tools/batch_upscale.py`): Real-ESRGAN ncnn-vulkan 기반
- DLC 4개팩 377개 + 본편 미커버 20개 = **397개 전부 업스케일 완료** (7.7분, 에러 0)
- 출력: max 2048px, 총 902MB

### 비교 분석 결과
- HD 팩(Muramasa Complete 2.0): 2,139개 → 본편 96%(482/502) 커버
- 미커버: 본편 20개 (보스/요괴/GUI) + DLC 377개 (Pack1~4 전체)
- 비교 방식: perceptual hash (16x16 thumbnail, hamming distance ≤ 30)

### 파이프라인
1. `ftx_extract.py` — FTX → PNG (DXT5/DXT3 디코딩 + Vita unswizzle)
2. `batch_upscale.py` — Real-ESRGAN animevideov3 4x/2x → max 2048 → pngquant
3. 출력 위치: `output/dlc_hd/Pack1~4/`, `output/main_hd/`

### 남은 단계
- Vita3K 해시 매핑: DLC 실행 → export 해시 수집 → import 폴더 배치
- 본편 미커버 20개도 동일 방식으로 해시 매핑 필요

## 2026-04-10: HD 텍스처 팩 적용 + 한글 폰트 고화질화 성공

### 성과
- **Muramasa Complete 2.0** (Plaidray/xibalva) HD 텍스처 팩 Vita3K import 적용
- 2139개 텍스처를 **5.2GB → 829MB**로 최적화 (max 2048 다운스케일 + pngquant 8bit 양자화)
- HD 폰트 텍스처(4096x4096) 위에 한글 88px 렌더링 → 2048x2048 다운스케일
- 게임 실행 확인 완료 (60 FPS, HD 텍스처 + 한글 정상 출력)

### 파이프라인
1. HD 팩 원본 (Vita3K 해시 형식) → PIL resize(max 2048) → pngquant(quality 70-95) → import 폴더
2. 폰트 텍스처 2개(87B72F6DB3C3FBDC, 6706A53E1D94C16E)는 HD 베이스 위에 한글 오버레이
3. 나머지 폰트(8665CE082D339B33, E690E190AA5C798F)는 export 기반 1024 처리
4. 도구: `tools/hd_font_import.py`

### 핵심 정보
- HD 팩 위치: `C:/Users/taro1/Downloads/Muramasa Complete 2.0/PCSE00240/Best/`
- import 위치: `C:/game/vita3k/textures/import/PCSE00240/`
- 폰트 해시 충돌: 87B72F6DB3C3FBDC, 6706A53E1D94C16E (HD팩에 포함 → 한글로 교체)

## 2026-04-10: Vita3K 텍스처 교체로 한글 폰트 렌더링 성공

### 핵심 성과
- **한글이 게임 내에서 렌더링됨** - 갈, 감, 곽, 꿈 등 실제 한글 글리프가 게임 대화 창에 표시
- **955자 전체 한글이 2개 폰트 페이지에 수용** (page 0: 48자, page 1: 907자)
- **FTX/DXT5/스위즐 우회** - Vita3K 텍스처 import로 PNG만 수정하면 됨

### 셀 매핑 공식 (확정)
```
cell = 224 + (b1 - 0x81) * 188 + b2_offset
b2_offset = b2 - 0x40 (b2 < 0x80)
b2_offset = b2 - 0x41 (b2 >= 0x80, 0x7F 스킵)
```
- 한글 SJIS 범위: b1=0x85~0x8A (US 버전에서 미사용 확인)
- 가(0x85,0x40) → cell 976 (page 0, local 976)
- 힘(0x8A,0x4E) → cell 1930 (page 1, local 906)

### 폰트 텍스처 (Vita3K export/import)
| 해시 | 용도 | 형식 |
|------|------|------|
| `882CCAF6763B8B59` | 일반 폰트 page 0 (cells 0-1023) | white RGB + alpha glyph |
| `09498223CD6E047B` | 일반 폰트 page 1 (cells 1024-2047) | white RGB + alpha glyph |
| `6706A53E1D94C16E` | 볼드/아웃라인 폰트 | RGBA glyph |

### 검증 방법
1. 녹색 틴트 → 텍스처 import 동작 확인
2. 상하반전 → 6706A53E1D94C16E가 폰트 텍스처 확인
3. 진단 텍스처 → 셀 번호 시각화로 매핑 공식 검증
4. 한글 import → 게임 내 한글 렌더링 확인

### 입력 자동화
- scancode 키 입력: `keybd_event(0, scancode, KEYEVENTF_SCANCODE, 0)`
- X키=scancode 45, Esc=1
- 앱 리스트: Esc → green dot 찾기 → 65% x에서 클릭×2

### 남은 이슈
- **Yes/No 다이아몬드 터치**: 원본 게임에서도 클릭 안 됨 (Vita3K 터치 입력 이슈)
- 볼드 폰트 page 1 해시 미확인 (page 0만 48자 처리)
## 2026-04-12: Wii Muramasa 한글 패치 wbfs 추출

### 성공
- Wiimms ISO Tools(wit) 로 RSFE7U (USA Wii) wbfs 추출 완료
- Vanillaware FCMP 압축 디컴프레서 구현 (LZSS 서큘러 버퍼, 12+4 비트, LSB)
- NMS 메시지 파일 10개 전부 디컴프레스 + 파싱 → 4,920개 메시지 JSON 추출
- Wii JP는 순수 Shift-JIS로 완벽 복원 확인 (히라가나/카타카나 검증)
- `translations/wii_reference/` 디렉토리에 저장

### 부분 완료 (향후 필요)
- FTX 텍스처 103개 (fonts + GUI) FCMP 디컴프 완료하지만
  TPL 텍스처 디코딩 실패 (wimgt 거부, 커스텀 Vanillaware 포맷)
- `extracted_wii/ftx_decomp/` 에 바이너리 보관

### 핵심 발견
- Wii Korean 패치는 PS Vita와 동일하게 커스텀 SJIS 매핑 사용
- DLC는 Wii에 없음 (본편 1,116개 대사만 참고 가능)
- NMS 구조는 PS Vita와 거의 동일 (헤더 레이아웃 동일)

### 새 도구
- `tools/fcmp_decompress.py` - FCMP 디컴프레서
- `tools/extract_wii_messages.py` - NMS → JSON 변환
- `tools/wit/` - Wiimms 툴 (wbfs 추출용)


## 2026-04-25: 지명 텍스처 50장 한글화 완료

### 작업 범위
- `kr_textures/ui` 폴더의 빨간/검은 배경 지명 텍스처 50장 한글화
- 백업: `textures/place_name_originals/` (원본 50장 보관)
- 폰트: 그리운 경찰감성체 (`fonts/Griun_PolSensibility-Rg.ttf`)

### 분류 및 처리
| 분류 | 개수 | 처리 방식 |
|---|---|---|
| Simple (1 banner + 1 box) | 29 | 자동 detect + 매핑 + 렌더링 |
| Complex Group A (1 banner + 1 box, false positive 있음) | 6 | Simple 방식 |
| Complex Group B (multi-banner) | 15 | bbox idx 수동 매핑 + 캐릭터 이름 처리 |

### 주요 매핑 파일
- `translations/place_name_mapping.json` — 텍스처별 한글 매핑
- `translations/place_name_regions.json` — 자동 detect 영역
- `translations/place_name_white_kanji.json` — 캐릭터 이름 흰 글자 영역

### 핵심 규칙
- 빨간 배너: 일본어와 동일 방향 (회전된 상태) → 한글 세로쓰기
- 검은 박스 (frame): 가로/세로 방향 자동 감지하여 그에 맞춰 한글 배치
- brush stroke + 흰 캐릭터 이름: 흰 글자 영역 별도 detect 후 한글 덮어쓰기
- 매핑 없는 영역: 색상 클리어 (일본어 잔존 방지)

### 캐릭터 이름 매핑 (jp_messages/proper_nouns 기반)
- 大神徳川綱吉 → 도쿠가와 쓰나요시
- 雪之丞 → 유키노조
- 血狂毘沙門 → 치구루이비샤몬
- 綱釜千代子 → 쓰나가마 치요코
- 大根 → 다이콘

### codex 검증
- Simple 29장 + Complex A 6장: 모두 OK
- Complex B 15장 v3 (일본어 완전 제거): 게임 내 검증 필요

### 미해결 / 보류
- 매핑 없는 흰 글자 영역 (일부 텍스처): 빈 영역으로 처리됨
- E210275AFFF0A8D8 (이즈): 식별 후 매핑됨
