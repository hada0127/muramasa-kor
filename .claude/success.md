# SUCCESS - 성공한 작업 기록

## [2026-05-27] GitHub 이슈 #15 — DF66CADD ✕ 누락 + UI에디터 ✕ 편집 모드
- 신고: ✕ 추가팩에 DF66CADD(메인 UI 아틀라스)의 X판이 빠짐. 사용자: "내가 O로 바꾼 게 남아있는 듯".
- **원인**: DF66CADD는 `localize` 텍스처. 원본엔 ✕ 2곳(우측 Items 옆·좌하단 Settings 옆)이 있는데,
  kr이 region **K45·K46**(text='O', clear=true)로 그 ✕를 지우고 'O'를 그려 ○가 됨. (중앙 嵐丸 옆 ✕는 유지)
  → 그 2 region을 빼면 원본 ✕가 그대로 드러남(사용자가 정확히 파악).
- **구현(사용자 요청 = UI에디터에서 ✕용 별도 편집 + ui_xbutton 저장)**:
  - `exclude_region_ids` 방식: localize 변형은 base config에서 지정 _id를 빼고 texture_localize로
    `ui_xbutton/`에 렌더(작고 재현 가능). DF66CADD exclude=[K45,K46].
  - `tools/localize_region_io.py`(server의 _to_native_localize 공유 분리),
    build_button_variant(set_variant_exclude/render_localize_variant/localize_regions),
    server(/api/variant_regions GET, /api/save_variant_regions: kept_ids→exclude 계산·렌더).
  - UI에디터: 좌측 '✕변형' 뱃지 + '✕변형만' 필터, 변형 패널의 **✕ 편집 모드**(기본 ○ region 띄움→
    text='O' region 삭제·저장→exclude 저장+ui_xbutton 렌더, 상단 배너·종료). 저장은 변형용으로 라우팅.
- 검증: end-to-end(kept_ids→exclude=[K45,K46]) ✕ 렌더, 우/좌 글리프 원본 ✕와 alpha diff≈0(3024).
  전체 재빌드 idempotent(git clean), 추가팩 zip 3텍스처 포함(14.3MB). 전 엔드포인트 curl 통과.
  (브라우저 시각검증은 원격 Chrome이 로컬 미도달로 막힘 → 사용자 로컬 에디터에서 확인.)
- **✅ v1.2.1 발행·클로즈**: '일반용/✕용 분리 항목' 모델로 재구성(사용자 피드백 — region diff 아닌 별도 행).
  같은 해시가 목록에 일반용(→ui)+✕용(별도 행 key=`<hash>#x`, →ui_xbutton) 2줄, 파일명순 나란히, 패널 단순화.
  3B58B76C는 place라 'O를'→'X를'(사용자가 ✕ 붓글씨도 복원 편집). DF66CADD는 localize O region 2개 제거.
  build_release가 ✕ 추가팩 3종 묶음. tag v1.2.1 + gh release(--latest) + 이슈 #15 댓글·클로즈.
  https://github.com/hada0127/muramasa-kor/releases/tag/v1.2.1
- **DLC 엔딩 完(보류)**: codex+조사로 DLC 팩 CPK `GUI/Ending_P1~4.ftx`(1024² 일러스트+좌하단 完) 확정.
  export에 없어 import hash 미확보. 사용자 결정으로 이번 릴리스 보류. 상세 todo.md/audit doc/memory.

## [2026-05-27] GitHub 이슈 #12 — ○/✕ 선택 버튼 ✕ 추가팩 (구현 완료, 미발행)
- 신고: 선택/확인 버튼이 ○로 보여 헷갈림. ✕도 골라 쓰게 해달라.
- **원인/이력**: 커밋 ee37270(EDA6F03E 확인 글리프)·354bbc6/1db34e5(3B58B76C 시작화면)에서
  의도적 X→O 변경. 메인테이너 환경이 ○ 확인이라 추정.
- **codex+gemini 병렬 협의(정책)** — 수렴: 게임이 글리프를 자체 텍스처로 직접 그림
  (codex가 Vita3K 소스 `SCE_SYSTEM_PARAM_ID_ENTER_BUTTON`/`sys_button` 직접 확인).
  텍스처 교체는 '표시'만 바꾸고 '입력 의미'는 안 바뀜 → ✕판은 **Vita3K Enter Button=Cross**와
  세트로 써야 함. 스왑(○↔✕)이 단방향 덮기보다 안전. 결론을 패처·릴리스 노트에 명시.
- **사용자 결정**: 추가 덮어쓰기 팩(작은 별도 zip, 본편은 ○ 유지) + EDA6F03E·3B58B76C 둘 다.
- **대상 텍스처(픽셀 정밀 분석, 게임은 알파만 사용)**:
  - EDA6F03E: 확인 글리프 셀(x4-79,y256-351)만 ○로 덮였음 → ✕판=원본 ✕ 복원(box[0,254,82,100]).
    확인=✕, 취소=○. (큰 ○/✕ 글리프는 원본·kr 동일, 작은 확인 슬롯만 변경됐던 것)
  - 3B58B76C: ○ 엔소 링 슬롯(x1922-2165,y14-255)이 시작 글리프. 원본엔 ○·✕ 붓글씨 둘 다 있는데
    kr이 ✕(CC x1977-2190,y281-520)를 지웠음. ✕판=○ 링 slot clear + 원본 ✕ CC를 중앙배치.
    '누르세요' 텍스트엔 ○ 문자 베이크 없음(글리프 슬롯만 교체). 변경이 ○링 bbox에만 국한 검증.
- **구현(커밋 4개)**:
  - `translations/button_variants.json` 레지스트리 + `tools/build_button_variant.py` 데이터기반 생성기
    (restore_original/clear_box/paste_original_cc, 빈 ops면 수동 PNG 보존/○복제).
  - `textures/kr/ui_xbutton/` ✕판 2개(main 릴리스 미포함=격리).
  - `tools/build_release.py` package_button_variant_addon()(--xbutton-only/--no-xbutton) +
    `tools/apply_xbutton_patch.py` 독립 설치기(✕설치 / --restore로 ○복원, Cross 안내).
    addon zip=xbutton/(✕)+restore-o/(○)+패처+README, dry-run 검증 OK.
  - UI에디터 우측 '✕ 버튼 변형' 패널(포함토글·메모·○/✕미리보기·재생성·내보내기) + API 4종.
  - 문서: CLAUDE.md 섹션/트리/표, README 릴리즈 안내, release/NOTES_xbutton.md.
- 검증: 생성기 재실행 idempotent(git diff 0), py compile/json valid, 서버 API curl 통과.
  브라우저 시각검증은 원격 Chrome이 로컬 127.0.0.1 미도달로 막힘(기능은 curl로 갈음).
  인게임 최종 확인은 사용자(macOS Vita3K 자동화 불가).
- **✅ v1.2.0 발행 완료**: 사용자 결정(v1.2.0 새 릴리스). version 1.1.1→1.2.0, NOTES_v1.2.0.md,
  publish_release.py가 ✕ 추가팩 zip 자동 첨부. build_release(본편+추가팩) → tag v1.2.0 push →
  gh release(--latest). 자산 5종: 본편 zip(68MB)+manifest+sha256+xbutton zip(3.88MB)+NOTES.
  URL: https://github.com/hada0127/muramasa-kor/releases/tag/v1.2.0
  본편 번역/폰트/텍스처는 v1.1.1과 동일(텍스처 추가팩만 신규).

## [2026-05-27] 타이틀 화면 텍스처 HD화 (이슈 #11, 커밋 dad8e10)
- 신고: 오보로 무라마사/겐로쿠 괴기담 타이틀의 한문 배경·로고가 저화질. 8EFF960FC088FDD7이 HD팩과 같은 4096×2048인데 화질 떨어짐.
- **원인**: 초기에 non-UHD 베이스에 한글을 합성한 잔재. HD팩(Muramasa Complete 2.0, ~/Downloads) 선명본 대신 저화질 업스케일본을 originals로 썼음.
- **수정**:
  - 8EFF: originals를 HD팩 선명본으로 교체 + region 방식 전환. 블러 한글(겐로쿠 괴기담/오보로 무라마사) 재합성, OBOROMURAMASA 영어 의도적 유지.
  - 73420(본편 타이틀): 1024→UHD 4096 베이스, 오보로 무라마사 한글 재렌더(manual_regions→regions 활성화).
  - 1823D39C(도토미 지명) 갱신.
- **도구 추가(재사용)**: texture_localize region `blur`(가우시안 글로우, 알파만 블러+RGB 글자색 고정으로 헤일로 제거),
  ui_editor 속성에 블러(px)·글씨 투명도(%) 슬라이더, build_ui_index blur top-level(리로드 초기화 방지), index.html 캐시버스트.
- **교훈/한계**: 편집기 미리보기는 브라우저 canvas(measureText) 기반이라 실제 PIL 렌더와 폰트 메트릭이 달라 100% 일치 불가
  (미세 위치차·박스경계 글로우 잘림). **위치 정밀 확인은 저장 및 미리보기(실제 PIL 렌더) 기준**. 렌더 출력은 정상.
  렌더러/미리보기 위치는 "박스(w,h) 표준 렌더 → 패딩+블러 → 제자리 합성"으로 단순 통일(fit_to_box로 글자 박스맞춤).
- 워크플로: HD 베이스↔OLD 배경 스왑으로 위치참고, originals 스왑 후 texture_localize.py 재렌더 + import 복사 → Vita3K 확인.

## [2026-05-26] 아이템명 텍스처↔시스템(itemdata) 불일치 통일 (커밋 fabd992)
- 오의명 통일에 이어, 아이템명 아틀라스 텍스처(7DC6CF5A)가 itemdata와 어긋난 것 전수 통일.
- **원인**: 원본은 영어판. 영어→추측일본어(src_ja, confidence low 다수)→한글로 번역해 곡옥/장신구가 대거 오매칭.
- **검증법(사용자 지시)**: 원본 텍스처 크롭으로 영어 확정 → US itemdata(_US/_itemdata.nms) 효과설명 → JP itemdata 효과 매칭 → 우리 ko=정답. (JP/US nms 인덱스는 곡옥구간 비정렬 → 효과내용 매칭 필수.)
- **codex+gemini 2차 교차검증**: A 9건 양쪽 O 수렴. gemini 조건부(곡옥 전부 띄움/닌자발 대사참조 0건 안전/이중파일/오버플로) → 모두 해소.
- **단어 오류 9건**: 곡옥 5종(Amber→호박/Hellish→황천/Agate→마노/Ritual→제사/Ghostly→영혼 곡옥),
  Divine Panacea→영방반혼단·Soul Salvation→영력소비 없음(뒤바뀜), White Lightning(どぶろく)→탁주, Vitality Boost(持久強化)→지구 강화.
- **표기 통일**: 곡옥 7종 띄어쓰기 통일(수정/비취곡옥도 띄움), 닌자발→닌자술(itemdata 양쪽), 텍스처 형태소 공백 정규화 18건.
- **JSON 3종 동기화**(직접수정 시 누락 주의): texture_localize_config + ui_editor_index + kr/ui 라벨. CLAUDE.md에 규칙 추가.
- 적용: config 27건 + itemdata(_itemdata 3565/_itemdata_main 878) 12건 → texture_localize.py 재렌더 + build_patch.py(main/patch). UI 에디터 시각확인 OK.
- 조사/목록: temp/item_survey/{survey.md, fix_list_final.md}.

## [2026-05-25] v1.0.3 릴리즈 발행
- 이번 세션 작업(대사 '['/']' 깨짐 수정 + 오의명 일본어판 기준 통일 + UI 텍스처 폰트맞춤/문구 보정)을 묶어 배포.
- version.json 1.0.2→1.0.3, 쉬운 설명 노트 release/NOTES_v1.0.3.md.
- build_release(dist 패처 zip 64MB + manifest + sha256, 텍스처/폰트 88개 포함) → 4개 세션 커밋 push → tag v1.0.3 push → gh release(--latest).
- URL: https://github.com/hada0127/muramasa-kor/releases/tag/v1.0.3

## [2026-05-25] 사용자 보고 2종 — 대사 '['/']' 깨짐 + 오의명/텍스처 일괄 통일

### #1 대사 '['/']' 깨짐 — 뜯/뜸 RUNTIME_OVERLAY 충돌 재발 (해결)
- 증상: "물어뜯어"→"물어[어"(스샷), "손님이 뜸해서"→"손님이 ]해서". 뜯/뜸이 '['/']'로 렌더.
- 원인: 뜯 0x8B6F(河 local 283='[' 오버레이)·뜸 0x8B71(local 285=']'). 2350자 확장 때
  자연 완성형 위치로 회귀해 RUNTIME_OVERLAY와 재충돌(과거 relocate 유실).
- 수정: 뜯→0x8EE9(local 968)·뜸→0x8EEA(local 969) 양방향 relocate. 폰트 6종 재생성.
  픽셀검증 cell283=[ /285=] /968=뜯 /969=뜸, SJIS-aware 디코드 뜯/뜸 정상, 0x8B6F/71 비움.
- 명백한 회귀라 협의 생략(딱/량/럴/랴/봐 relocate 연장). 커밋 별도.

### #2 奧義(오의)명 ↔ 오의 텍스처 일본어판 기준 일괄 통일
- 배경: 무기 설명(itemdata) 오의명과 기술도감 텍스처(E8E01EAF/7DC6CF5A)가 서로 다르고,
  itemdata 자체도 어간 불일치 多(八丁斬り 채썰기 vs 팔정 베기, 地走り 땅질주 vs 지달리기,
  星天彗星 별똥별 vs 성천 혜성, 숫자 '이/삼/셋/넷/삼연' 혼용 등). 텍스처는 영어판 의역명
  (별똥별/채썰기/십자베기/나선은하/천지베기) 사용.
- 검수: codex+gemini 병렬(프로젝트 정책). 수렴: 妖炎→요괴불꽃(요염✗), 怨み返し→원한 되갚기,
  숫자 아라비아화, 영어의역 텍스처명을 JP충실명으로 덮어쓰기, 띄어쓰기 통일.
  발산은 사용자 결정: ①연타 'N연'(妖雷三ツ→요괴벼락 3연) ②雷光 계열 뇌광(雷光連→뇌광 N연,
  幻影雷光→환영 뇌광) ③迅雷→질풍 번개(gemini '신뢰'는 信賴 동음이라 기각) ④鬼火嵐→도깨비불 폭풍.
- 규칙: 단계(弐/参/四)→"이름 N", 연타(三ツ/四ツ/五ツ/二連/三連/四連)→"이름 N연"(공백).
  canonical 60어간 = tools(temp)/ougi_canonical.py. 弧月→호월(고월 정정), 旋風→선풍/竜巻→용오름/
  大竜巻→대용오름(태풍 충돌 해소), 飛天 계열 통일(飛天月光→비천 월광, 飛天輝夜→비천 카구야).
- 적용 표면(전부 동일 canonical): jp_messages itemdata 무기설명 142개 + 독립 오의명 184개,
  texture_localize_config E8E01EAF 45 region·7DC6CF5A 7 region, proper_nouns ko 92, ui_editor_index 재생성.
- 텍스처 region→JP 매핑: 정확한 EN 크롭 + 2023 검증앵커(K49/54/63/65/82) + 현재 KO + 위력 티어 교차.
  비기술(化身/아이템/스탯) 23 region 제외. 焔三連·雷光三連은 7DC6CF5A가 담당(E8E01EAF 2연/4연과 합쳐 완성).
- 검증: itemdata NMS에 canonical 전부 존재·구명(채썰기/요염/섬광/별똥별/나선은하/십자베기/강풍) 0회.
  텍스처 렌더 그리드 육안 확인(긴 이름도 박스 fit). itemdata 어간 불일치 0·JP↔KO 충돌 0.
- 빌드+CPK append+설치 완료. 인게임 최종 확인은 사용자(macOS 자동화 불가).



스크린샷 3장 기반. codex+gemini 협의(세 제안 모두 수렴 → 승인/조건부승인).

### #1 메뉴 아이템명 한자 혼입 ("홍시"→"省시")
- 원인: 홍=SJIS 0x8FC8(重 페이지). 메뉴 손글씨폰트 A8E6FDD1은 河만 import →
  重 글자가 동일 코드포인트의 원본 한자(省)로 렌더. 본문폰트는 重(E690E190) import라 정상.
- 진단: 메뉴(짧은 _itemdata 이름)에 쓰인 重 글자 = 11자(똥 썰 픔 홍 쥐 찜 챵 녁 섣 믐 렛).
- 수정: kr_sjis_mapping에서 11자를 번역 미사용 河 글자 11자(곯 깹 꺽 껍 낌 땀 뚱 맵 뱌 벙 빵)와
  코드포인트 swap(korean_to_sjis+sjis_to_korean 양방향). 11자가 河로 이동 → 메뉴/본문 모두 정상.
- 검증: 메뉴폰트 홍 신규 河셀 NCC 1.00, 重 옛 홍셀(0x8FC8)은 이제 껍 NCC 1.00.
- 참고: sysmsg 대사형 重 글자(냠/윽/닦/뺏)는 본문폰트 렌더라 안 깨짐 → 메뉴 대상 아님.

### #2 문장 끝 "!"가 "딱"으로 (전체 '!' 314건, '"' 2건)
- 근본 원인: build_patch는 ASCII를 河-local 960+에 pos=code+928 고정 배치, font_import는
  한글 점유 셀을 skip — **두 배치표 불일치**. 河-local 960~1023에 옛 한글 21자(덴 딱 량…등)가
  점유 → '!'(0x21)=cell961=딱, '"'=962=량로 인코딩됨(둘 다 같은 셀).
  21자 다수가 메뉴 아이템명에도 등장(두부/둘째칼/획득량)→重 이동 불가, 河 유지 필수.
- 수정: 단일 진실원본 모듈 `tools/font_mapping.py` 신설(sjis_to_cell/cell_to_sjis/
  build_ascii_overflow_map/ascii_overflow_cells/validate). 한글 점유 셀 제외한 빈 셀(43개)에
  **실사용 ASCII 우선** 배정. build_patch·auto_font_import·hd_font_import 셋이 이 표만 사용.
  build_patch에 ASCII 렌더 검증(위반 시 빌드 중단) 추가. + 'with' 미번역(共々 오역)→'와 함께' 수정.
- 검증: '!'=0x8EE6(local965)/딱=0x8EE2(local961) 분리. 폰트 965셀 NCC('!')=0.96·('딱')=0.37.
  등장 ASCII 36자 전부 河 빈셀 배정, validate 위반 0.

### #3 줄바꿈 위 비고 아래 몰림 → 구두점 인지 top-fill
- 원인: reflow_dialogs가 (a)ko>ja줄일때만 (b)DP가 max폭 최소화=균형분배라 top-fill 아님.
- 수정: reflow_dialogs.py를 구두점 인지 top-fill로 재작성. 윗줄부터 max_width(29.5)까지 채우되
  강한 구두점(.!?…)으로 끝나고 줄이 충분히 찼으면(>=78%) 조기 줄바꿈(고아단어 방지).
  scemsg+scemsg_patch 2223건 적용(1125 변경). **단어 시퀀스 100% 보존**(표현 무변형).
- 검증: over_width 0, 4줄초과 0(전부 ≤3줄), lint error 0. #132·#177 top-fill 확인.

### 공통
- 폰트 6종 재생성(auto_font_import+hd_font_import, export/HD base). 隼은 영향없어 동일.
- 빌드+CPK append+설치 완료. 인게임 글리프 조회 시뮬레이션으로 3문제 시각 확인.
- lint: error 0, warning 1(안 나오는 디버그 placeholder sysmsg#431만 잔존). … 공백 2건 정정.
- macOS라 실제 게임 실행 검증은 사용자 몫(vita3k_ctrl는 Windows 전용).

## [2026-05-25] 폰트 외곽선 정책 정리 — 리디 바탕체 전용 + 불투명화 (v1.0.1)

### 배경
글자 외곽선 1.5px가 리디 바탕체(본문/대사)뿐 아니라 그리운경찰체 메뉴 폰트
(식당·찻집·상인, hash `A8E6FDD162258699`)에도 적용되던 문제. 원인은 stroke 분기가
빈 `WHITESTROKE_FONT_HASHES`에 의존 → 메뉴 폰트가 외곽선 분기를 못 타고 기본 외곽선을 받음.

### 수정
- `auto_font_import.py`: stroke 결정을 `MENU_FONT_HASHES` 기준으로 변경. 메뉴 폰트는
  `MENU_STROKE_WIDTH=0`(외곽선 없음), 나머지(리디 바탕체)만 `STROKE_WIDTH=1.5`. 죽은
  변수 `WHITESTROKE_FONT_HASHES`/`WHITESTROKE_FILL` 제거.
- `auto_font_import.py`+`hd_font_import.py`: `STROKE_FILL` alpha 128→255 (외곽선 투명도 제거).
- 폰트 6종 재생성(`auto_font_import.py`) → `textures/kr/font/` 동기화 + import 반영.

### 검증 (픽셀)
- 메뉴 A8E6FDD1: 반투명 외곽선 107,248 → 0 (완전 제거).
- 리디 8665CE08: 반투명 139,564 → 불투명(alpha255) 114,157로 전환.
- 시각: 메뉴 '가' 흰 글자만 / 리디 '가' 흰 글자+또렷한 검정 외곽선 확인.
- v1.0.1 패치로 배포(릴리즈 노트 "폰트 롤백 문제 해결").

## [2026-05-25] 🎉 v1.0.0 릴리즈 발행 (정식판)

이번 세션의 대규모 작업을 묶어 정식 1.0.0 배포.
- **폰트**: 완성형 2350자(河/重/隼 3페이지) — 받침 깨짐/대체표기 완전 해소, char_substitutions 폐기
- **번역**: 본편 대사(scemsg 2187 + scemsg_patch 36) 전수 재번역(원문 복원·사극 말투), gemini 전수 검증
- **통일**: 인명 독법(켄모치/우마부키/세이타카/백여우), 용어/지명(규율/해골 골짜기/도토미), 무기명 텍스처(낫족제비/바케네코/미케)·지도 텍스처(遠江) 통일
- **품질**: lint error/warning 0, 마침표/줄임표 공백 정리
- 배포: `git tag v1.0.0` + `gh release`(dist 패처 zip/manifest/sha256 첨부), 쉬운 말 릴리즈 노트 `release/NOTES_v1.0.0.md`
- URL: https://github.com/hada0127/muramasa-kor/releases/tag/v1.0.0
- 남은 과제(별도): #9-3 무기명 변수 치환(eboot), _itemdata/sysmsg 비대사 섹션 재번역

## [2026-05-25] 본편 대사 전수 재번역 — 원문 복원·사극 말투·이슈 #9 해결

### 배경
폰트 955자 시절 (a)받침 대체표기 (b)박스 폭 제약 축약으로 원문 손실. 완성형 2350자 확보 후
일본어 원문을 살려 전수 재번역 (이슈 #9 "받침/문장 이상/무기명 통칭").

### 파이프라인 (gemini 배치번역 + claude 검수, codex+gemini 전략 수렴)
- `score_candidates.py`: 축약 손실 우선순위(원문 2줄→1줄 누락 등)
- `retranslate_batch.py`: gemini 배치 재번역(말투 가이드 `docs/translation-style-guide.md` + 인명 사전 주입)
- `reflow_dialogs.reflow()`로 폭 29.5전각/3줄 자동 재배치
- `lint_dialogs.py`: 폭/줄수/인코딩(2350 외)/일본어잔존/한자/마침표·공백/인명 검수
- `verify_batch.py`: gemini 전수 검증(5병렬)

### 결과
- scemsg 2187 + scemsg_patch 36 전수 재번역. **lint error/warning 0**.
- 인명 독법 정정(위키/영문판): 剣持 켄지→**켄모치**(Kenmochi), 馬蕗 마후키→**우마부키**, せいたか
  세테카→**세이타카**, 白狐 백호→**백여우**. proper_nouns 갱신.
- 용어 통일: 掟→**규율**(10건), 髑髏谷→**해골 골짜기**.
- 한자병기·가나·일본부호 제거, 줄임표(…) 통일, 마침표/부호 공백 규칙.
- gemini 전수 검증 1116건 지적 → 유사도 중앙값 0.90(대부분 표현 선호). 명백 개선 3건만 반영
  (#1978 そりゃよかった '다행이군' 복원, #1516 과잉의역→직역, #1592 風下 '바람을 마주 선 것이').

### 이슈 #9 대사 항목 해결 현황
- ✅ 받침 누락(2350 커버), 상닌→상급닌자/하닌→하급닌자, 유다→아부라다, 마침표/공백, 화폐 문, 인명 독법
- ✗ **#9-3 무기명 통칭(`##` 토큰 13건)**: 원작은 무기명을 런타임 변수로 출력하나 US 엔진이 토큰 제거
  → 텍스트 패치로 복원 불가. **eboot 역공학 별도 과제(미해결)**.
- 커밋 73c25df / e8013e5 / eddbd8b. 빌드·설치 완료. 인게임 확인은 사용자(macOS 자동화 불가).
- 비대사 섹션(_itemdata/sysmsg 등) 재번역은 범위 밖(추후 별도).

## [2026-05-25] 한글 폰트 확장 — 다중 폰트 페이지 발견 + 완성형 2350자 매핑 (PoC 인게임 검증 성공)

### 핵심 발견 (기존 PoC 결론 뒤집음)
- `docs/03-analysis/jongseong-expansion-poc.md`는 "한 페이지를 늘리는 건 불가, eboot 패치 필요"로
  결론냈으나 **틀렸음**. 실제 폰트 구조를 뜯어보니: FTX 컨테이너에 **GXT 페이지 16장**
  (`font.ftx` 8 = font00~03 + 굵기변형 b, `font2a/2b.ftx` 각 4 = 손글씨체). **SJIS 한자 페이지는
  3개**: Page0 河(0x89CD) / Page1 重(0x8F64) / Page2 隼(0x94B9). 기존엔 **河만** 한글화했음.
- 추출물 `temp/font_pages/`, 페이지 식별은 원본 NCC. export `E690E190` = 重 페이지(NCC 1.00) —
  이미 Vita3K가 GPU 업로드 → import 교체 가능.

### PoC 검증 (사용자 인게임 스크린샷)
- 重 페이지(E690E190)에 0x8F64~ 한글 import + 매핑 + sysmsg #40 "레벨맘빡땡" 마커 → 게임 HUD에
  "레벨**맘빡땡**" 또렷이 출력. **게임이 重 페이지 별도 텍스처의 한글을 읽음을 확정.** 방법 A 성립.

### 본 적용
- 매핑 `kr_sjis_mapping.json`: 960자 → **완성형 2350자(KS X 1001)**. Page0(河) 960 유지 +
  나머지 1390자를 0x8F64~ 순차. **실사용 우선 배치**(번역 1032자 = 河 930 + 重 102 → 100% 직접
  글리프 커버, 隼 0). 남은 미사용 완성형 1288자는 重 뒤쪽(922)+隼(366).
- `char_substitutions.json`: 102자 → **0 (완전 제거)**. 더 이상 대체 표기 없음.
- `auto_font_import.py`: `page_base` 파라미터 + `detect_page_base()` NCC 자동 판별
  (`tools/font_page_refs/{p0_ascii,p1_ha,p2_ju,p3_sun}.png`). 河 페이지는 한글+ASCII/overlay,
  重/隼 페이지는 한글만(early return). **기존 버그 동시 수정**: E690E190(重)에 河 기준 한글이
  잘못 그려져 있던 것(8665CE08과 픽셀 동일)을 重 기준으로 교정.
- import 재생성: 河 4개(959) + 重 E690E190(1024). `textures/kr/font/` 동기화.
- 빌드/설치 완료 (NinPriPatch +284,672, 받침글자 쩨/꿇/뺏/촌 등 0x8F6E~ 인코딩 확인).

### 남은 일
- **隼(Page2) 366자**: 미사용 완성형이라 현재 번역엔 영향 0. 단 "2350 전부 활성"하려면 隼 페이지
  텍스처 export 유도(게임 진입) 후 auto_font_import 재실행 필요. 重 검증 성공으로 메커니즘은 입증됨.
- 인게임 받침글자(쩨/꿇/뺏/갸/겪 등) 정상 표시 최종 확인은 사용자 기기(macOS Vita3K 자동화 불가).
- 6706A53E는 ASCII 페이지(HD)인데 河로 처리 중(현행 유지) — 별도 확인 필요 항목.

## [2026-05-25] README/기여자 문서 갱신 + 작업 로그 정리
- README: 버전 v0.9.0→v0.9.3, 변경 이력 섹션 + 소개/FAQ + UHD 텍스처 팩 호환 안내 추가 (블로그 girldevstudy.tistory.com/173 기반)
- 기여자 문서(CONTRIBUTING/WORKFLOW/AGENTS): 텍스처 단일 트리 구조 반영, 웹 UI 에디터를 텍스처 편집 진입점으로 명시(Krita 폐기), import 텍스처 개수 76→87
- 로그 정리: todo.md를 현재 미해결/진행 항목 중심으로 재작성(완료 이력은 success.md 참조), success.md의 2026-05-25 항목 최신순 정렬, fail.md 경로(kr_textures→textures/kr) 갱신

## [2026-05-25] v0.9.3 — 결과 화면 '평가' 텍스처 클리핑 수정 + 릴리스
- 증상: 전투 결과 화면의 '평가'(Rating) 라벨이 편집기 박스엔 맞는데 게임에서 잘림 (Screenshot_20260524-120927.png)
- 원인: DF66CADD K38(평가) region 박스 과대(h=521)로 글자가 게임 UV 영역 밖으로 넘쳐 잘림
- 수정(사용자 UI 에디터 편집): h=521→203, y=835→1153, background=clear_alpha
- 릴리스: v0.9.2(보스 아이템) → v0.9.3 순차 배포 (gh release, dist 4종 첨부). 미푸시였던 폴더통합·정리 커밋도 함께 push

## [2026-05-25] 미사용 스크립트·JSON 대량 정리 (의존성 분석 기반)
- 방법: 활성 루트(build_release/render/font/ui_editor + 문서화 도구)에서 import/subprocess 도달성 분석 → 도달 불가 + 미문서 후보 추출
- 삭제: 스크립트 42개 + JSON 14개 (총 56)
  - [A] 루트 실험/scratch 10: apply_modern_fixes, fix_ratios×4, modern_expression_patterns, test_patch, _check_syllables, _place_name_inspect, _verify_oor
  - [B] 분석/노트/v4-v5 서브시스템 (UI 에디터로 대체): build_translation_notes, build_my_analysis, build_integrated_mapping, compare_analyses, annotate_v5_detect, render_v5, render_integrated, atlas_bbox/{detect_bboxes,render_atlas} + JSON 12 (my_analysis, integrated_mapping, codex_analysis, analysis_diff, detect_v5, v4/v5_codex_verdicts, manual_bbox_mapping, place_name_{mapping,regions,textures,white_kanji}) + atlas_bbox 고아 json
  - [C] opening_* 나레이션 실험 15 + scene_intros_all.json
  - [E] HD/텍스처 유틸 9: decode_wii_ftx, downscale_hd_pack, generate_kr_textures, hide_mbs_quads, install_textures, localize_hd_textures, migrate_localize_uhd, populate_uhd_originals
- 유지(사용자 지정): [D] 텍스트 가공 도구 9 (fix_punctuation/reflow_dialogs/rewrap_all/condense_dialogs/fix_place_names/apply·export_proper_nouns/analyze_jp_width·short_lines) — 번역 변경 시 재실행. 문서화된 upscale_export·publish_release, 참조 데이터 texture_localize_catalog.json
- 검증: 깨진 import 0, build_release exit 0(텍스처 87 수집), place/localize 렌더 OK, build_ui_index 재생성 동일(82개)
- 결과: tools/ 75→40, 루트 스크립트 7→0, translations JSON 22→9

## [2026-05-25] 텍스처 폴더 단일 트리 통합 + Krita 폐기
- 결정: 단일 textures/ 트리 (사용자 선택 A). codex·gemini는 둘 다 B(분리 유지) 권장했으나 사용자가 정보 확인 후 A 선택 → memory/project_texture_folder_consolidation.md 기록
- 구조: textures/{originals, place_originals, kr/ui, kr/font}
  - kr_textures/ui → textures/kr/ui, kr_textures/font → textures/kr/font
  - textures/place_name_originals → textures/place_originals
- 제거: Krita 자산(.kra 7 + kra_extract.py/kra_to_place.py + kra_extracted/ 7), textures/text/(originals와 100% 중복 23), textures/work/
- 참조 일괄 수정: 36개 텍스트 파일 sed (kr_textures→textures/kr, place_name_originals→place_originals, textures/text/→textures/originals/). .claude 작업로그 3개는 기록 보존 위해 제외
- 문서: CLAUDE.md 구조 트리·도구표(ui_editor 추가, Krita 폐기 명시), WORKFLOW.md
- 검증: render_place_texture_job(place_originals 읽기 OK), texture_localize preview(originals 읽기 OK), build_release(textures/kr에서 87개 텍스처 수집 OK)
- 주의: build_release TEXTURE_DIRS는 textures/kr/{ui,font} 명시 allowlist — textures/ 전체로 넓히면 원본 혼입. provenance 메타 "source":"kra_extract"는 region 출처 라벨이라 렌더 무관, 그대로 둠

## [2026-05-25] 보스 전용 무기 아이템명 한자 깨짐 수정
- 증상: 모모히메/키스케 장비창에서 "珞韓集集모모히메 세번째"처럼 아이템명에 한자가 섞여 출력 (Screenshot_20260524-122353.png)
- 원인: _itemdata 6개(키스케/모모히메 × 첫·두·세번째)의 ko가 "+OSS…" — 원문 "BOSS百姫３本目"의 BOSS가 "+OSS"로 오역됨.
  ASCII '+OSS'가 아이템 목록 폰트 페이지(960+ 위치 ASCII 글리프 미오버레이)에서 원본 한자 글리프(珞韓集集)로 렌더링됨.
  cf. 하단 설명 폰트에서는 ASCII가 정상 출력되어 같은 문자열이 화면마다 다르게 보임.
- 수정: translations/jp_messages.json의 _itemdata·_itemdata_main 12개 엔트리 "+OSS" → "보스 " (순한글, 프로젝트 기존 표기 "보스전" 일치)
- 검증: build_patch 재빌드 후 4개 _itemdata.nms 모두 "보스"(8c568cb5) 6개·"+OSS" 0개. SJIS 리드바이트 파싱 결과 단일 바이트는 공백뿐 → 한자 깨짐 제거 확정.
- CPK append 패치 후 fs/ux0/app/PCSE00240에 설치 완료.
- 미검증: macOS라 Windows용 vita3k_ctrl.py(ctypes.windll) 미동작 + 해당 아이템은 상대전용/사용금지 숨김 아이템이라 인게임 도달 곤란. 인게임 육안 확인 권장.

## 2026-05-23: 奥義(필살기) 명칭 번역 통일 — 妖雷/雷光/幻影雷光

### 문제
- 같은 奥義가 아이템 설명문과 명칭 목록에서 다르게 번역(예: 妖雷 → 설명문 "요뢰" vs 명칭 "요괴벼락").
- 텍스처 E8E01EAF에서 Faerie Assault가 번호 없는 "요괴벼락"이라 Faerie Bolt와 충돌(둘 다 요괴벼락).

### 조사
- 奥義 명칭은 `_itemdata`에만 존재(sysmsg/scemsg엔 없음 — 거기 "요괴"는 일반 대사의 괴물 뜻).
- 영문판(US): 妖雷→Faerie Bolt/Strike/Assault, 雷光二/三/四連→Dual/Triple/Quad Lightning, 幻影雷光→Chaos Roar I/II/III.
- gemini 검토: 일본어 충실(요뢰/뇌광) 권장. **사용자 최종 결정: 익숙한 순우리말(요괴벼락/벼락치기)로 통일**.

### 적용 (최종)
| 일본어 | 한국어 |
| 妖雷 / 三ツ / 四ツ | 요괴벼락 / 요괴벼락 3 / 요괴벼락 4 |
| 雷光 二/三/四連 | 벼락치기 2 / 3 / 4 |
| 幻影雷光 / 弐 / 参 | 섬광 / 섬광 2 / 섬광 3 |
- `_itemdata` 설명문+명칭 36개 통일(jp_messages.json), CPK 재빌드·설치.
- 텍스처 E8E01EAF: `texture_localize_config.json`+`ui_editor_index.json` 5개 region(K49/K54/K63/K65/K82) 갱신, 원본 영문 크롭으로 region↔奥義 정확 매핑(K49=Assault, K54=Bolt, K63=Strike, K65=Dual, K82=Quad). 렌더 확인 완료.

## 2026-05-23: 장비창/UI ASCII 깨짐 근본 해결 — scheme-B 충돌, 매핑 v0.9.0 복원

### 증상
- 장비창 "공격:41" → "공격칸땡음", "사용조건 (힘:13 체력:12)" → "사용조건 뜸 힘칸선 체력칸선 뜸".
- 한글(공격/사용조건/힘/체력)은 정상, **숫자·콜론·괄호 ASCII만 한글 음절로 깨짐**.

### 근본 원인 (전수 진단)
- 게임은 폰트 아틀라스에서 ASCII를 **두 가지 스킴**으로 읽음:
  - Scheme A: `cell = 192 + ascii_code` (대사/메시지) — RUNTIME_OVERLAY가 깨끗한 ASCII 덮어씀(정상)
  - Scheme B: `cell = 960 + (ascii_code - 0x20)` (장비창/스탯 UI) — 셀 960~1023
- **회귀 커밋 6684c96** "받침 누락 38자 일괄 매핑(1001자)"이 scheme-B 셀 960~1023을 **64/64 전부 한글로 잠식**.
  → 장비창이 cell 977(='1')에서 땡, 986(=':')에서 캇 등을 읽어 깨짐.
- v0.8.2/v0.9.0(7085fb6): 960자, scheme-B 21/64만 점유 → 나머지 비워 ASCII 렌더 → 장비창 정상.
- 사용자가 되돌린 d9cad6b는 이미 6684c96 회귀를 포함(=깨진 상태)이었음. 진짜 last-good는 v0.9.0.
- 외부 검토: gemini(하이브리드 재배치 제안), codex(usage limit 실패). 페이지 1024셀이 꽉 차 재배치 공간 없음.

### 해결 (사용자 결정: v0.9.0 매핑 복원)
- `kr_sjis_mapping.json` → v0.9.0(7085fb6) 복원: 1001 → **960자**, scheme-B 64 → 21셀.
- `char_substitutions.json` → v0.9.0(95개) 복원 + 갸/걔/괘/냠/닦/몹/윽 7개 보강 = **102개**.
  → 제거된 41자(빡/칙/맘+받침38)는 대사에서 substitute로 렌더(v0.9.0 동일 동작). '?' 폴백 0건 검증.
- 폰트 재생성: auto_font_import(1024 폰트) + hd_font_import(6706A53E HD만 2048).
  → 5개 폰트 모두 scheme-B 셀에 깨끗한 ASCII 복귀, 한글 정상 (montage 픽셀 검증 완료).
- **stale 리포 폰트 수정**: `kr_textures/font/`의 committed 6706A53E가 4096 한자투성이 stale 아티팩트였음(원래 깨짐 유발). fresh import(2048 한글)로 동기화 + E690E190 신규 추가.
- CPK 재빌드/설치 완료.

### #4 럴럴 — 해결 완료 (별도 수정)
- **근본 원인**: 일본판 sysmsg는 `##（무기）`/`##（유파）` 변수 토큰을 쓰지만, **영문판(US)은 이 토큰을 아예 제거**하고 "this blade" 식으로 일반화함 (US #173 `You cannot forge this blade.`, #178 `You still lack the Strength to equip this blade. Forge it anyway?`). 우리는 _US 경로를 패치하는데 번역에 일본어 `##` 토큰을 그대로 둬서, US 엔진이 치환하지 않고 literal `##` 출력 → '#'(0x23)이 scheme-B 셀 963의 한글 **럴**을 읽어 `럴럴`로 표시.
- **수정**: jp_messages.json의 `##` 토큰 13개 메시지 ko를 자연스러운 한국어로(`##（무기）`→`무기`, `##（유파）`→`유파`). 재빌드 후 US sysmsg에서 `##`(0x23 0x23) 0건·`럴`(0x8EE4) 0건 확인.
- 영향 메시지: sysmsg #212/225/226/230/231/232/265/283/284/285/485/488/490.
- macOS에서 `vita3k_ctrl.py` 실패(ctypes.windll, Windows 전용) → 자동 인게임 검증 불가. 데이터/픽셀 레벨 검증으로 갈음.
- 릴리스 v0.9.1(daf7cc2, tag)은 깨진 1001자 매핑 포함 — **GitHub 미발행 상태**라 재태깅/재발행 필요.

## 2026-05-23: 받침 폰트 확장 PoC 전체 deferred + 워킹 트리 복원

### 사용자 결정
- 받침 누락 잔여 54자 매핑 시도(`c08f5fa`~`486e7aa`)는 모두 인게임 검증 실패 또는 자동 검증 막힘.
- 옵션 1(CPK + import 텍스처) 한계 이론적 확정, 옵션 2(eboot 패치)는 ARM disasm 필요 — 시간 비용 큼.
- 시도 내용은 문서로 남기고, 실제 파일은 폰트 확장 직전(`d9cad6b`) 상태로 복원하여 안정 배포.

### 문서화
- `docs/03-analysis/jongseong-expansion-poc.md` 신규: 11개 커밋 PoC 시퀀스, 옵션 1 한계 메커니즘, 향후 재개 진입점 정리.

### 워킹 트리 복원 (커밋 보존)
- `git checkout d9cad6b -- .gitignore tools/.font_hashes.json translations/{char_substitutions,jp_messages,kr_sjis_mapping}.json patch_main/ patch_patch/`
- 삭제: `tools/external/sceutils/`, `tools/external/vita3k_sce_utils.cpp`, `tools/external/vita3k_src/` (untracked), `tools/vita3k_macos.py`, `translations/*.bak_*` 5개.
- 매핑: 1001자 (받침 38자 직접 매핑 유지) + char_substitutions 54자.
- 8665CE08 폰트 import는 유지(받침 시도 도중 발견한 진짜 버그 수정).
- sysmsg #40/#267/#268 ko 원본 복원.

### 빌드/배포 검증
- `NinPri_final.cpk` md5 `1761fc31eb9015f1af6e3d66370a3440` (사이클 9와 동일)
- `NinPriPatch_final.cpk` md5 `7e72ce68d78b822be20fa2e7a818ca9f` (사이클 9와 동일)
- macOS Vita3K (`~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/`) 설치 완료, 해시 일치 검증.

### 향후
- 받침 잔여 54자는 char_substitutions로 대체 표기 유지. 다른 이슈 우선.
- 옵션 2 환경(eboot.elf decrypt, sceutils + keys, Vita3K source 분석)은 git 커밋(`3c54f2e`, `a23b8c6`, `a71636d`)에 보존되어 있어 향후 재개 가능.

---

## 2026-05-23: 폰트 텍스처 확장 PoC (1024x2048) — 사이클 3+5 롤백 + 확장 영역 시도

### 배경
사이클 5 신규 매핑 41자(0x8EE9~0x8F03)가 폰트 cell 968~994 영역인데, 이게 ASCII positions 960+ overlay 자리(`(`/`)`/`:` 등)와 충돌. 사이클 9에 8665CE08 import 추가하면서 충돌이 노출(무기 대장간 "캇" = `:` 자리 한글 깨짐).

### 사용자 결정
- 옵션 A 롤백 + 받침 누락은 폰트 텍스처 **확장 영역** 사용
- 1024x1024 → 1024x2048로 확장하여 cell 1024~2047 추가 슬롯 1024개 확보

### 진행
1. 사이클 3+5 매핑 롤백: `git checkout 1eecde3 -- translations/kr_sjis_mapping.json translations/char_substitutions.json` (960자 / 95자 substitutions)
2. PoC 매핑: 빡 → SJIS 0x8F64 (cell 1024). char_substitutions 빡 제거
3. `auto_font_import.py` 수정: cell range 0~1024 → 0~2048, 텍스처 1024x1024 로드 후 1024x2048로 확장 (paste 위쪽, 아래쪽 투명)
4. 빌드 + 배포

### 검증
- 폰트 텍스처: 18747565/A8E6FDD1/8665CE08 모두 1024x2048로 생성 (6706A53E HD는 4096x4096 그대로 — 확장 미적용)
- cell 1024 (y=1024~1056, x=0~32) 알파 max=255, mean=26~42 → 빡 글리프 정상 그려짐
- 시각 확인: "빡" 글리프 표시 (활자체, 손글씨체 둘 다)
- NMS 인코딩: 빡 0x8F64 = 3회 (scemsg patch_main + patch_patch)
- NinPri_final.cpk md5 0af5df11fa0da306b00546af6f8e0e38
- NinPriPatch_final.cpk md5 630893c4d09e9c57aff63592b15aaecd

### 인게임 검증 대상
사용자가 Vita3K 재시작 후 백희전 어딘가 "빡빡이들 소행인가" (scemsg#414) 메시지 진행. 빡 한글 표시 = 확장 영역 게임 lookup 가능 → 95자 전체를 확장 영역으로 옮겨 모든 충돌 해소 가능.

### 미해결 (HD 폰트 확장)
6706A53E HD (4096x4096)는 확장 안 됨 — hd_font_import 별도 처리. PoC 검증 성공 후 HD도 4096x8192로 확장.

## 2026-05-23: 8665CE08 폰트 import 누락 발견 + 해결

### 증상 (사용자 보고)
Vita3K 실행 시 게임 메시지가 일본 한자로 표시 (예: "蛾漁撒 芥蛙岩航 字去貢示閧含").
NMS는 정상 한국어 패치 ("겐로쿠 괴기담을 플레이합니다" SJIS bytes).

### 진단
SJIS 디코드로 확인:
- 蛾(0x89E9)/漁(0x8B99)/撒(0x8E54) → 우리 매핑 한글 "겐/로/쿠"
- 芥/蛙/岩 → "괴/기/담"
- 航/字/去/貢/示 → "을/플/레/이/합"
- 모두 우리 매핑 영역 (0x89CD~0x8F60)

결정적 단서: Vita3K export 폴더의 **8665CE08가 07:55 신규 export**됨 (이전에는 없었음).
사용자가 이번 세션에 새 화면(DLC 선택 등)에 진입 → 게임이 8665CE08 폰트 로드 → Vita3K가 처음 export.

이전 auto_font_import 실행 시 8665CE08 export 없어 import 생성 안 됨 → 게임이 그 텍스처로 한글 SJIS 출력 시 원본 일본 한자 글리프 표시.

### 해결
auto_font_import.py 재실행 → 4개 폰트 텍스처 모두 한글 import 생성:
- 18747565A804E292: 1000 글리프
- A8E6FDD162258699: 1000 글리프
- 6706A53E1D94C16E (HD base): 1000 글리프
- **8665CE082D339B33: 1000 글리프 (신규)**

kr_textures/font/ 리포 동기화 (8665CE08 + 18747565 신규 커밋).

### 사용자 작업
- Vita3K 종료
- Vita3K 재시작 + 게임 진입 → import 적용

## 2026-05-23: 폰트 텍스처 분류 분석 + 사용자 export 대기

### 발견
폰트 텍스처 4개 엄밀 식별 (32x32 grid + cell 경계 알파 0 + cell 중심 평균):
- **ASCII 페이지** (cell 0~31에 ! " # $ ... 0-9 : ; < = > ?):
  - 6706A53E1D94C16E (HD 활자체)
  - 2E88068C58DD36D5 (메뉴 동적 손글씨체) — todo.md "신규 발견 (2회차)"
- **KANJI 페이지** (cell 0~31에 河火珂禍禾稼... = SJIS 0x89CD~):
  - 18747565A804E292 (활자체)
  - A8E6FDD162258699 (메뉴 손글씨체)
- **8665CE082D339B33**: 알려진 KANJI 폰트지만 현 export 폴더에 없음. kr_textures/font 리포에만 보관

### 함의
- KANJI 영역 0x89CD~0x8F63 (1024 cell) 모두 매핑 사용 중 — 잔여 54자 매핑 불가
- 사용자 게임 진행 중 추가 KANJI 폰트 export 트리거 가능성 — 그 텍스처가 다음 SJIS 페이지(0x8F64+)를 cover하면 잔여 받침 확장 가능
- 6706A53E HD에 한글 그린 일부 작업은 ASCII 페이지라 게임 lookup에 무용 가능성 (검증 필요)

### 사용자 응답
"일단 대기 게임을 다른 기기에서 하니 export 텍스쳐를 내가 다시 가져올게"
→ 사용자가 게임 진행 후 추가 폰트 텍스처 가져올 예정. 그 시점까지 잔여 받침 작업 대기.

## 2026-05-23: 5건 이슈 종합 진척 정리 (사이클 1~7)

### 해결 예상 (사용자 인게임 검증 대기)
| 이슈 | 핵심 변경 | Commit |
|---|---|---|
| #5 마대로 → 맘대로 | 맘 매핑 0x8EE8 추가 | c3da314 |
| #7 OLkxWc 물어[ 어 → 물어뜯어 | 뜯 0x8B6F→0x8EE9 이동 (cell 283 '[' 충돌 해소) | 6684c96 |
| #7 v3zaOF 짜짜한 → 쩨쩨한 | 쩨 매핑 0x8F44 추가 | 6684c96 |
| #4 럴럴 (사이클 5 빌드 후 영문 'r' 표시) | 18747565 RUNTIME_OVERLAY 정상화 | 6684c96 |
| #8 유다 인명 3건 / 불시말 / 이런 곳을 노리면 | 텍스트 교정 | 9e1b97a |
| #8 상닌/하닌 → 상급닌자/하급닌자 9건 + 줄 재정리 | 조사 보정 + 줄폭 | 1eecde3 |
| #8 받침 누락 38자 (똥/땐/뺏/쩌/썰/쥐/땡/엽/...) | top 38 빈도 매핑 + char_substitutions 92→54 | 6684c96 |

### 미해결 (사용자 정보 또는 추가 작업 필요)
- **#4 둘별** (GfqaJc 화면 상단): NMS 0건, sysmsg#890 보스 진행도 추정. 사용자 추가 정보 필요
- **#4 쿠모키레 이미지 잘림**: 무기 아이콘 텍스처 hash 미식별, HD 팩 또는 원본 게임 이슈 가능성
- **#6 권장 레벨 9**: sysmsg#187/#202 ja 동일 → 게임 데이터 영역. 챕터-ID 매핑 정보 필요
- **#8 잔여 54자 받침** (괄/굶/귈/꿇/...): 폰트 페이지 0x8F64+ 매핑 + auto_font_import 코드 확장 필요. 다음 폰트 텍스처 hash 식별 필요

### 인프라 변화
- kr_sjis_mapping.json: 960 → 1001자 (+41자, 충돌 이동 2 + 신규 39)
- char_substitutions.json: 95 → 54자 (-41건)
- 신규 폰트 텍스처 감지: 18747565A804E292
- RUNTIME_OVERLAY 충돌 전수조사 완료 (뜯/뜸 외 없음)

## 2026-05-23: Issue #4 럴럴 사후 검증 — RUNTIME_OVERLAY 정상화 확인

### 시각 검증
사이클 5 commit 6684c96 빌드 후 18747565 폰트 텍스처 cell 192-318 영역 시각 확인:
- cell 237 '-' / 238 '.' / 239 '/' / 240-249 숫자 / 250 ':' / 255 '?'
- cell 262 'F' / 283 '[' / 285 ']' / 301 'm' / 303 'o' / 306 'r'
- 모두 영문 글리프 정상 표시. cell 283/285는 이번 사이클 뜯/뜸 이동으로 비워졌고 '[' / ']' overlay 정상.

### 알파 비교 (cell 306 'r' 자리)
| 폰트 | center_alpha | 비고 |
|---|---|---|
| A8E6FDD1 | 130.6 | MENU_PRESERVE — 한자 원본 보존 |
| 18747565 | 18.2 | RIDIBatang 16pt + stroke 0 |
| 6706A53E (HD) | 63.1 | HD 4× scale |

18747565는 표시되지만 흐릿. 인게임 가독성 부족 시 ASCII_BODY_PT 16→18 + stroke 보강 검토.

## 2026-05-23: Issue #7/#8 4차 — 충돌 이동 2건 + 받침 누락 38자 일괄 매핑

### 적용
**(a) RUNTIME_OVERLAY 충돌 이동 (2건)**:
- 뜯 0x8B6F → 0x8EE9 (cell 283 '[' 충돌 → 신규 cell 965)
- 뜸 0x8B71 → 0x8EEA (cell 285 ']' 충돌)
이게 Issue #7 OLkxWc "물어[ 어" 직접 원인 해결.

**(b) 받침 누락 직접 매핑 (38건, top 38)**:
- 똥/땐/뺏/쩌/썰/쥐/땡/엽/섣/뤄/믐/픔/촌/윈/믄/캇/랭/돕/겪/턱/꾀/쩨/닮/뭣/줬/짤/삘/꿋/굳/켕/홍/찜/챵/녁/렛/궈/꿨/썼 → SJIS 0x8EEB~0x8F63
- char_substitutions에서 38건 제거 (92 → 54)
- Issue #7 v3zaOF "짜짜한"=쩨 / Issue #6 사용자 보고 "땡중"=땡 등 자동 해결

### 검증
- 신규 매핑 NMS 인코딩 확인 (똥 7회·뜯 21회·맘 9회·쩨 4회·땡 13회 등)
- 구 SJIS 0x8B6F/0x8B71 잔존 0회 (충돌 마이그레이션 완전)
- 폰트 텍스처 3개 (A8E6FDD1 / 6706A53E HD / 18747565) cell 965~1023에 글리프 자동 배치
- NinPri_final.cpk md5 1761fc31eb9015f1af6e3d66370a3440
- NinPriPatch_final.cpk md5 7e72ce68d78b822be20fa2e7a818ca9f

### 미해결
- 받침 누락 54자 (괄/굶/귈/꿇/끕/낀/낄/낚/닳/댈/댐/댔/덧/덫/렷/롬/릎/멎/뱃/벴/빴/뺌/뿟/삐/삥/섰/솟/쉼/슥/슷/쌔/쎄/쏙/씐/압/얄/왠/잣/줌/짊/짙/쫌/쫙/쭐/칩/캤/탔/탱/틴/폐/픕/햐/홱/휴): 추가 폰트 텍스처 슬롯 확보 후 (다음 페이지 0x8F64+) 처리
- Issue #4 럴럴: 18747565 폰트 cell 306 'r' overlay 알파 4.5로 그려지지 않음 → 디버깅 필요
- Issue #4 쿠모키레 무기 이미지 잘림: 텍스처 이슈 (별도)
- Issue #4 둘별 정확 위치 미식별

## 2026-05-23: Issue #4/#5/#7 이미지 분석 + RUNTIME_OVERLAY 충돌 진단

### 이미지 분석
- #5 (ar66hl): "마대로" → PoC c3da314로 '맘' 매핑 추가 → 다음 빌드부터 "맘대로" 정상 (자동)
- #7 (OLkxWc): "이로 물어[ 어 조각내주마" — scemsg#240 ko "물어뜯어"인데 '뜯' SJIS 0x8B6F가 폰트 cell 283 = RUNTIME_OVERLAY '[' (0x5B) 자리. 영문 '[' overlay가 한글 '뜯'을 덮어씀
- #7 (v3zaOF): "짜짜한 거" — scemsg#255 ko "쩨쩨한"인데 char_substitutions '쩨'→'짜'. 매핑 추가로 자동 해결
- #4 (0XPyrT): "이 럴럴 (무기)는 만들 수 없습니다" — sysmsg#225 ## placeholder에 영문 'rm' 등 fill되어 같은 overlay 충돌 메커니즘으로 깨짐
- #4 (GfqaJc): "둘별" — NMS 0건. char_substitutions/매핑 누락으로 다른 단어가 치환된 결과 (정확 위치 미식별)
- #4 (3Tkhcr 상단): 무기 아이콘 텍스처 잘림 — 별도 텍스처 이슈
- #6 (MqQrYf): 레벨 42인데 권장 레벨 9. ja 원본 동일 → 챕터-sysmsg ID 매핑 데이터 영역. 사용자 정보 필요

### RUNTIME_OVERLAY 충돌 메커니즘 일반화
폰트 cell 192+code (RUNTIME_OVERLAY_CODES = `0x2D/2E/2F/30-39/3A/3F/46/5B/5D/6D/6F/72`)에 매핑된 한글은 영문 overlay에 덮여 깨짐.
- 알려진 이동 완료: 딱/량/럴/랴 (0x8EE2-5), 봐 (0x8EEF)
- 신규 발견: 뜯 (0x8B6F → cell 283 = '[' 충돌)
- 전수조사 + 빈 슬롯 일괄 이동 → 다음 사이클 코어

## 2026-05-23: Issue #8 3차 — 받침 매핑 확장 PoC (빡/칙/맘 직접 매핑)

### 분석
- 매핑 슬롯 0x89CD~0x8F60 사용 중, 0x8EE6~0x8F63 영역 빈 슬롯 43개 발견
- char_substitutions.json 95개 글자 빈도 분석 → top 43개 누적 73.5% 커버리지
- auto_font_import.py ASCII overlay 충돌 검토: line 312 `pos in korean_cells` 체크로 자동 회피됨 (안전)
- **추가 폰트 텍스처 자동 감지**: 18747565A804E292 (1024×1024, KANJI page) — 사용자 코멘트 "추가로 발견된 폰트 텍스쳐"와 일치 추정

### PoC 적용 (3글자)
- 빡 → SJIS 0x8EE6 (cell 965)
- 칙 → SJIS 0x8EE7 (cell 966)
- 맘 → SJIS 0x8EE8 (cell 967)
- kr_sjis_mapping.json: 960 → 963 글자
- char_substitutions.json: 95 → 92 글자

### 검증
- NMS 인코딩: 빡 3회 / 칙 8회 / 맘 9회 정상
- 폰트 텍스처 cell 965~967 글리프 그려짐 (A8E6FDD1 / 6706A53E HD / 18747565 신규)
- 8665CE08은 export missing → import 생성 안 됨 (인게임 사용 화면 확인 후 후속)
- NinPri_final.cpk md5 22df3fd2d20f962c8c9a87a763b8a57a
- NinPriPatch_final.cpk md5 8a0bafc5a6546e34b8142cec3a4ba48c

### 인게임 검증 대상 (사용자)
- scemsg#414 "빡빡이들 소행" (빡 표시)
- 규칙 표기 (8회) — 닌자의 규칙, 무사의 규칙 등
- 맘대로 표기 (9회) — 진쿠로 대사 등

### 다음 단계 (확장)
- PoC 인게임 OK 확인 후 top 43개 일괄 매핑 (커버리지 73.5%)
- 8665CE08 분석 (사용 화면 식별)
- 95개 전체는 추가 폰트 텍스처 확보 후

## 2026-05-23: Issue #8 2차 — 상닌/하닌 → 상급닌자/하급닌자 (9건 + 줄 재정리)

### 변경
- 상닌 → 상급닌자 (4건: scemsg + sysmsg#544)
- 하닌 → 하급닌자 (5건: scemsg + sysmsg + sysmsg_main)
- 조사 자동 보정: '하닌을' → '하급닌자를' 등 (자=받침 없음 → 를/는/가)
- 줄 재정리 (수동 4건, 박스 27자 한도 맞추기):
  - scemsg "시라누이…" (29.5→21.5)
  - scemsg "목표는 이가의 노즈치 성…" (28.5→21.5)
  - scemsg "닌자의 우두머리가 되겠다는 놈이…" (31.0→22.5)
  - scemsg "전생의 인연인 카부라타의 위기를…" (30.0→20.0)

### 검증
- 잔존 '상닌'/'하닌': 0건
- 빌드 정상 (sysmsg 574/574, scemsg 1116/1116)
- NinPri_final.cpk md5 8680992e73717e8c693c596261379636
- NinPriPatch_final.cpk md5 5690aa7cdd490d2c41cf091834233469
- macOS Vita3K 배포 완료

## 2026-05-23: Issue #8 1차 — 인명/명백 오타 6건 텍스트 교정

### 변경
- 油田 인명: `유다` → `아부라다` (3건)
  - sysmsg#544 "해골 무리의 상닌, 아부라다 카부라타가 있는"
  - scemsg "아부라다 가의 공주"
  - scemsg "직접 손을 쓴 건 아부라다다 어차피"
- scemsg "이 불시말을 어찌 수습할 셈이냐?" → "이 사태를 어찌 수습할 셈이냐?"
- scemsg "이런 곳을 노리면 버틸 수 없어…" → "이런 상태에 있다가는 버틸 수 없어…"

### 검증
- `유다 카부라타` / `유다 가` / `유다다` / `불시말` / `이런 곳을 노리면` 잔존 0건
- NMS 빌드 정상 (scemsg 1116/1116, sysmsg 574/574 매칭)
- CPK 패치 `NinPri_final.cpk` (md5 4b1bd8c9cc378329854b80b069c32c43), `NinPriPatch_final.cpk` (5e6414d8f67119a1f8e2b6935cfcc2be)
- macOS Vita3K 배포 md5 일치

### 보류 (다음 사이클)
- `상닌`/`하닌` → `상급닌자`/`하급닌자` (폭 변동 검토 후)
- 받침 누락 코어 (빠빠이/규치/마대로/바람아래에): `char_substitutions.json` + 매핑 + 폰트 추가 (codex+gemini 협의 예정)
- Issue #4 럴럴/쿠모키레, #5 마대로(↔ #8 맘), #6 권장 레벨 9, #7 이미지 분석

## 2026-05-17: 마침표 누락 전수 보정 (KO-only 분류 자동화)

### 사용자 보고
"줄바꿈 바뀌면서 아직도 마침표가 안 들어간 곳들이 많이 보임. 전수 조사 및 해결 필요. 여러 번 루프 돌려서 누락되는 게 없도록 철저하게 조사."

### 전수 조사 결과 (KO 종결어미로 끝나면서 부호 없음)
- Q 의문 35건 + DECL 평서 251건 + CMD 명령 44건 + OTHER 미분류 624건 = 954건 후보
- 기존 fix_punctuation.py는 JP/KO 줄 수 같을 때만 또는 JP 부호 있을 때만 처리 → 너무 보수적

### 외부 AI 협의 (codex + gemini 수렴)
- 안전 Auto-Q (?): 까/느냐/더냐/는가/런가/인가/인고/을까/을꼬/는지/런지/리오/이오/리까/리이까/ㅂ니까/습니까 + 이냐/거냐/겠나/잖나/라니
- 안전 Auto-DECL (.): 이로다/되었다/하였다/구나/도다/노라/리라/이라네/이라오/구먼/구려/ㅂ니다/습니다/니라/이니라/느니라 + 합니다/옵니다/입니다/답니다/주마/리다/이로군/로군/지요/다오/는다/었다/마라/해라
- 안전 Auto-CMD (.): 주거라/거라/어라/아라/오라/오너라/셔라/옵소서/하라/가라
- RISKY (10자 이상 길이 가드): 이다/한다/있다/없다/같다/겠다/이라
- SKIP+리포트: 명사형 표제어, 호칭(모모히메/토라히메/키스케/오코이/오보로 등), 조사 끝, placeholder

### 코드 변경 (tools/fix_punctuation.py)
- `classify_ko_ending()` 헬퍼 추가: KO-only 종결어미 분류 (Q/DECL/CMD/RISKY_DECL/None)
- 케이스 A-2 신설: JP 부호/줄 수와 무관하게 KO 종결어미 매칭만으로 마지막 줄 부호 자동 추가
- 케이스 B-2 신설: 줄 중간(KO_INTRA_AUTO_DECL/Q 강한 종결만, 연결구·조사 시작 SKIP)
- INTRA_LINE_PATTERNS: Q 패턴도 자동 적용 (기존 D만)
- AUTO_Q/AUTO_DECL/AUTO_CMD/RISKY_DECL/HONORIFIC_NAMES_NOPUNCT 상수 추가

### Fixed-point 루프
- Loop 1: fix_punctuation → 491건 (DECL 426, Q 67) 적용
- Loop 2: condense → 11건 (한 줄 메시지 2줄 분할, 부호 추가로 폭 변동 보정)
- Loop 3: fix_punctuation → 0건
- Loop 4: condense → 0건 → **Fixed-point 달성**

### 검증·배포
- OOR 감사: 707개 (변경 전후 동일)
- NMS 빌드 정상
- NinPri_final.cpk 455,022,056 bytes (md5 84fd7a0941d2cc0f6035e87ddb2fd9d5)
- NinPriPatch_final.cpk 25,686,408 bytes (md5 6a81945d5aa65bef94f2f36ae759c13c)
- macOS Vita3K 배포 완료

## 2026-05-17: 폰트 외곽선 6차 — 1.5px (supersampling) + 50% opacity

### 사용자 보고
- 60% opacity(alpha=153) 이후 1.5px 두께 + 50% opacity로 시도 요청
- PIL `stroke_width`가 정수 픽셀만 지원 → 2× 슈퍼샘플링으로 시각적 1.5px 구현

### 변경
- `tools/auto_font_import.py`
  - `STROKE_WIDTH=1→1.5`, `STROKE_FILL=(0,0,0,153)→(0,0,0,128)`
  - `_FONT_CACHE` + `draw_centered_glyph()` 헬퍼 추가: float stroke 입력 시 자동으로 2× 슈퍼샘플링 (글리프를 cs*2 캔버스에 그리고 LANCZOS 다운샘플)
  - padding은 cs와 비례(`cs//16`, `cs//8`, `cs//4`)로 처리 → HD scale에서도 동일 의미
  - 4군데 글리프 그리기 모두 `draw_centered_glyph` 호출로 단순화
- `tools/hd_font_import.py`
  - `STROKE_BASE_PT=1→1.5`, `STROKE_FILL` 동일 변경
  - `auto_font_import`에서 `draw_centered_glyph` import해 재사용 (코드 중복 제거)
  - 4군데 호출 모두 헬퍼로 교체
  - HD 4× 스케일은 stroke=6 정수라 슈퍼샘플링 생략, 1024 export는 stroke=1.5 → ss=2

### 재생성 결과
- `6706A53E1D94C16E` (HD 4096→2048, stroke=6.0px): 861KB
- `8665CE082D339B33` (1024, stroke=1.5px, ss=2): 296KB
- `A8E6FDD162258699` (1024, stroke=1.5px, ss=2): 296KB
- 슈퍼샘플링으로 AA가 부드러워져 파일 크기 ~50% 증가 (203→296KB)

### 미리보기 검증
- 1px(60%) 대비 외곽선 두께가 살짝 풍부해지면서 가장자리 부드러움 향상
- 밝은 배경: 안쪽 흰 본체 또렷 + 부드러운 회색조 윤곽
- 어두운 배경: 외곽선 거의 사라지고 흰 본체 또렷

### 다음 단계
- 사용자 인-게임 검증 (상점 메뉴 + 대사창 이름바)

## 2026-05-17: 폰트 외곽선 5차 — 1px 검정 60% opacity (alpha=153) — 슈퍼시드됨

### 사용자 보고
- 풀 alpha(255)는 너무 진해서 작은 메뉴 텍스트가 떡짐
- 30은 너무 약해서 이름바에서 안 보임
- → **60% opacity 시도** = alpha 153

### 변경
- `tools/auto_font_import.py`: `STROKE_FILL=(0,0,0,255)→(0,0,0,153)`
- `tools/hd_font_import.py`: 동일
- stroke-aware 중앙 정렬(4차에서 적용)은 그대로 유지

### 미리보기 검증
- 밝은 배경: 외곽선이 살짝 부드러운 회색조 윤곽으로 표시, 안쪽 흰 본체 또렷
- 어두운 배경: 외곽선이 거의 사라지고 흰 본체가 또렷
- alpha 30(약함) vs 255(떡짐) 사이 절충점으로 양호

### 다음 단계
- 사용자 인-게임 검증 대기

## 2026-05-17: 폰트 외곽선 4차 — 1px 검정 풀 alpha + stroke-aware 중앙 정렬 — 슈퍼시드됨

### 사용자 보고 (alpha=30 적용 후)
- 이름바에서 너무 안 보임 → 검정 풀 alpha로 회귀 요청
- 1px stroke, 본문 크기 그대로 유지
- "외곽선 먼저 그리고 그 위에 하얀 글씨" 방식 — PIL `stroke_width=1, stroke_fill=(0,0,0,255)`가 정확히 그 동작 (stroke 그린 뒤 fill로 본체 덮기)
- **추가 요청**: stroke 추가로 글자가 외곽 확장돼 셀 중앙이 어긋날 수 있으니 중앙 정렬 보정

### 변경
- `tools/auto_font_import.py`: `STROKE_FILL=(0,0,0,30)→(0,0,0,255)`
- `tools/hd_font_import.py`: 동일
- **stroke-aware 중앙 정렬**: 4군데 모두 `font.getbbox(ch)` → `draw.textbbox((0,0), ch, font=font, stroke_width=N)`로 교체
  - Korean main / ASCII overlay / Runtime-ASCII overlay / Fullwidth-punctuation overlay
  - hd_font_import.py도 동일 4군데 수정 (HD 4× 스케일에서 4px stroke 반영)

### 미리보기 검증
- 32px 격자 오버레이로 셀 중앙 정렬 확인 — 글자가 셀 안에서 일관된 위치에 들어감
- 밝은 배경(상점 종이톤 베이지): 흰 본체 + 검정 1px 외곽선 또렷
- 어두운 배경(대사창): 흰 본체 또렷, 외곽선이 윤곽만 잡음

### 다음 단계
- 사용자 인-게임 검증 대기 (대사창 이름바 + 상점 메뉴 두 케이스)

## 2026-05-17: 폰트 외곽선 재조정 — 검정 + alpha=30 — 슈퍼시드됨

### 사용자 보고 (B안 적용 후)
- 크기는 OK
- 검정색 + alpha=30으로 변경 요청
- "연기구슬"만 안쪽이 흰 이유 질문 → **게임이 현재 커서 행만 흰색, 비활성 행은 어두운 색을 곱해서 렌더링**. 폰트 텍스처는 모두 동일 흰색. 외곽선이 두꺼우면 비활성 행 흰 본체가 잠식되어 더 어두워 보임 → alpha를 낮추면 비활성 행에서도 흰 본체가 살아남음

### 변경
- `tools/auto_font_import.py`: `STROKE_FILL=(50,50,50,255)→(0,0,0,30)`
- `tools/hd_font_import.py`: 동일 색 변경 (`STROKE_BASE_PT=1` 유지)
- 폰트 본문 크기·stroke_width 모두 유지

### 재생성 결과
- 3개 폰트 텍스처(`6706A53E1D94C16E` 2048, `8665CE082D339B33` 1024, `A8E6FDD162258699` 1024) 재생성
- 미리보기(활성 vs 비활성 0.5 곱 합성): 활성은 흰색 또렷, 비활성도 외곽선이 거의 사라져 본체 톤이 살아남
- 사용자 인-게임 검증 대기

## 2026-05-17: 폰트 외곽선 완화 (B안: 1px + 진한 회색) — 슈퍼시드됨

### 사용자 보고
- 상점 메뉴 스크린샷에서 외곽선 추가(c3566d9) 이후 글자가 떡으로 두꺼워져 가독성 저하
- "이쪽도 같은 폰트 파일을 쓰고 있어?" → 답: KANJI 페이지(`6706A53E1D94C16E`, `8665CE082D339B33`, `A8E6FDD162258699`)를 대사창/이름표/메뉴/상점 모두 공유. 폰트만 별도 분리 불가

### 선택지 비교 (사용자에게 제시)
| 옵션 | 설명 | 트레이드오프 |
|---|---|---|
| A | stroke 2→1px + 본문 20→22 복원 | 이름바 가독성 중간 |
| **B** | stroke 1px + 색 (50,50,50) 진한 회색 | 어두운 배경 외곽 효과 약화 |
| C | stroke 2px + alpha=128 | 흰 배경 보호 약화 |

→ 사용자 선택: **B**

### 변경 사항
- `tools/auto_font_import.py`: `STROKE_WIDTH=2→1`, `STROKE_FILL=(0,0,0,255)→(50,50,50,255)`
- `tools/hd_font_import.py`: `STROKE_BASE_PT=2→1`, 동일 색 변경 (HD 4096 base에서 stroke 8px→4px)
- 본문 크기(KR 20pt / ASCII 16pt)는 그대로 유지

### 재생성 결과
- `6706A53E1D94C16E` HD 4096 → 2048 다운스케일, 959 한글 글리프, 815KB
- `8665CE082D339B33` 1024 export 기반, 959 글리프, 204KB
- `A8E6FDD162258699` 1024 export 기반, 959 글리프, 203KB (white 포맷)
- 미리보기 합성(밝은/어두운 배경)에서 외곽선이 1px 회색으로 가볍게 들어감 확인

### 다음 단계
- 사용자가 Vita3K 재시작 후 인-게임(상점 메뉴 + 대사창 이름바)에서 두 케이스 모두 검증
- 어두운 배경에서 외곽선이 너무 약하면 색을 (30,30,30) 정도로 짙히는 후속 조정 가능

## 2026-05-17: 대사 정리 7차 — greedy max=27 + 부호 보정 수렴

### 사용자 지시
- 6차(max=26) 결과 검토 후 한도 상향: "27 ㄱㄱ"
- 예시 메시지 "이글이글 타오르는 그 눈 일찍이 나조차 능가하는 괴묘가" = 폭 26.5
  - max=26으로는 "괴묘가"가 둘째 줄로 밀림
  - max=27이면 첫 줄에 포함 (사용자 의도)

### 시작 상태
- HEAD `0820f19` (6차 commit), working tree clean

### 수렴 절차 (3회차에 fixed-point)
| 라운드 | greedy(max=27) | fix_punc |
|---|---|---|
| 1차 | 563건 | 6건 |
| 2차 | 6건 | 0건 |
| 3차 | 0건 | 0건 |
| **누적** | **569건** | **6건** |

CLI:
```bash
python3 tools/condense_dialogs.py --greedy-fill \
  --max-width 27 --greedy-max-width 27 \
  --aggressive-short-lines --aggressive-max-width 27 --apply
python3 tools/fix_punctuation.py --apply
```

### 검증 (scemsg + scemsg_patch)
- 전체 라인: 4,163개 (max=26 대비 -451 — 줄 수 감소)
- 라인 폭: p50=23.0 / p95=27.0 / p99=27.0 / max=27.0 (27 초과 0)
- 줄 수 분포 (6차 → 7차):
  - 1줄 496 → **514** (+18)
  - 2줄 1418 → **1479** (+61)
  - 3줄 308 → **229** (-79)
  - 4줄+ 1 → **1**
- OOR 감사: **707** (변경 전후 동일)

### 예시 메시지 검증 (사용자 의도 일치)
```
이글이글 타오르는 그 눈 일찍이 나조차 능가하는 괴묘가  (w=26.5)  ← 첫 줄에 "괴묘가" 포함
되었더냐. 자 시게마츠 놈에게 뼈저리게 알려 주거라,  (w=25.0)
인간들을 저주하라.  (w=9.0)
```

### 빌드 + 배포
- patch_main → NinPri_final.cpk: 455,022,056 bytes  md5 `0400db32aa8c5bb541d13158d95f3ca6`
- patch_patch → NinPriPatch_final.cpk: 25,682,312 bytes  md5 `ee5c89b8109530048466b4933b791982`
- macOS Vita3K(`~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/`) 배포 후 md5 일치 확인

---

## 2026-05-17: 대사 정리 5단계 (2회차 수렴 패스) — Fixed-point 달성

### 사용자 의도
> "fixed-point 수렴을 위해 2회차(3→1→재빌드)를 한 번 더 돌려야 계산이 정확하다"

1회차에서 마침표가 추가되며 글자 길이가 변동 → 같은 한도(max=40)로 알고리즘 한 번 더 실행하여 줄 분배 정확성을 회복하고, 새 줄 끝에서 발생하는 종결 누락도 다시 보정.

### Step A — greedy max=40 (1차)
`python3 tools/condense_dialogs.py --greedy-fill --aggressive-short-lines --aggressive-max-width 40 --apply`
- **605건 적용** (모두 2줄 메시지의 단어 경계 재분배)
- 줄 수 분포 변동 없음 (1회차에서 3줄→0줄 이미 달성)
- 한 줄 폭 p50: 40.0 → 33.0 (균일화 진행)

### Step B — fix_punctuation
`python3 tools/fix_punctuation.py --apply`
- **21건 적용**
- 패턴: Step A에서 새로 노출된 첫 줄 끝(어절 경계)에 `…` 또는 `?` 추가
- 모든 21건이 문장 흐름상 줄임표 종결이 자연스러운 위치 (의미 변경 X)

### Step A 재실행 (2차) — cascading
- **2건 추가**: Step B가 어절 중간에 부호를 추가하면서 다음 줄로 단어가 밀려 재분배 필요한 케이스
- scemsg#201, scemsg#361 두 건

### 수렴 검증
- Step B 재실행: 0건
- Step A 재실행: 0건
- **Fixed-point 달성** ✅

### 누적 (2회차 전체)
- pre-pass2 vs final: **618개 메시지 변경**
- 줄 수 분포: 1줄 1018 / 2줄 1205 / 3줄 0 (변동 없음)
- 한 줄 폭 분포: p50=33.0, p95=57.0, p99=58.0, max=59.0
- OOR 감사: 707개 (변경 없음)

### 빌드 산출물
- `/Users/tarucy/project/muramasa-kor/output/NinPri_final.cpk` 455,022,056 bytes (MD5 e4ad08f0024d95c583a2290291840930)
- `/Users/tarucy/project/muramasa-kor/output/NinPriPatch_final.cpk` 25,682,312 bytes (MD5 024c76be7ddd80c8aa4f758922c7fd63)
- macOS Vita3K 자동 배포 안 함 (사용자가 직접 적용 — `cp` 명령은 보고에 포함)

### 사용자 직접 배포
```
cp output/NinPri_final.cpk      "$HOME/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/NinPri.cpk"
cp output/NinPriPatch_final.cpk "$HOME/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/NinPriPatch.cpk"
```

### 1회차 경고 그대로 유지
- 박스 추정 한도(29.5) 초과 줄 1,648 → 1,107로 일부 감소했으나 여전히 다수 존재
- 인-게임 검증 시 박스 잘림 발견되면 별도 패스 필요

---

## 2026-05-17: 대사 정리 4단계 — 마침표 보정 + 부호 뒤 공백 + Greedy fill (max=40)

### 사용자 보고 (정확 인용)
> "위와 같이 줄 바뀜이 바뀌면서, 마침표가 없어서 가독성이 떨어지는 경우들이 굉장히 많이 생김. ... 결정 아래 우측 기준까지 닿을려면 한참 더 남아 보임. ... 40 기준으로 위쪽부터 채우는 알고리즘으로 가는게 맞을꺼 같다. 그리고 점 3개(...)뒤와 마침표 뒤에 같은 줄에 문장이 더 있을 경우는 공백 한칸씩 추가해주는게 가독성에 더 좋을듯."

### 외부 AI 협의 결과 (codex + gemini — 수렴)
- 부호 매핑: `。→.` `！→!` `？→?` `…→…`
- `か` 종결: KO 어미가 명확 의문형(까/느냐/더냐/는가/인가/리오/이오 등)일 때만 `?`. 평서면 `.`
- 줄 내 두 문장 결합: 매핑 확실 시 `. ` 삽입. 의심 케이스는 자동 보류 + 별도 리포트
- 부호 뒤 공백: `. ` `… ` `! ` `? ` `, ` 권장. 연속 부호는 마지막 뒤에만
- greedy fill: 새 옵션 `--greedy-fill` 추가. 기본 동작 변경 X
- max_w=40 위험: ≥29.5 줄은 별도 리포트
- orphan: greedy 그대로 유지 (사용자 의도)

### Step 1+2 — 마침표 보정 + 부호 뒤 공백 (`tools/fix_punctuation.py` 신규)
**적용 결과**: scemsg 519개 메시지 변경
- step1_changed: 130 (종결 부호 보정)
- step2_changed: 401 (부호 뒤 공백 추가)
- both_changed: 12
- overflow_after: 47 (공백 추가 후 폭 28 초과) → `temp/punctuation_overflow.txt`

**룰 요약**:
- JP 줄말미 부호 → KO 대응 줄에 부호 추가 (마지막 줄 / JP-KO 줄 수 같을 때 중간 줄)
- JP「か」 종결 + KO 의문 종결어미면 `?`, KO 평서/명령 종결이면 `.`
- JP 평서 종결(のじゃ/だ/だぞ 등) + KO 평서/명령 종결이면 `.`
- 줄 안 두 문장 결합(보수적 화이트리스트): 종결어미 + 공백 + 한글 → `. ` 삽입
- 연결어미(그리고/면서/지만 등)로 끝나는 줄에는 부호 추가 보류
- 따옴표 불균형, placeholder 포함 메시지는 자동 수정 SKIP

**사용자 예시 케이스 정상 처리**:
```
化猫(괴묘) 메시지
OLD: "...되었더냐 자 시게마츠 놈에게... / 저주하라"
NEW: "...되었더냐. 자 시게마츠 놈에게... / 저주하라."
```

### Step 3 — Greedy fill 알고리즘 + max=40 (`tools/condense_dialogs.py` 개선)
**개선 사항**:
- 새 옵션 `--greedy-fill` + `--greedy-max-width 40` 추가
- 기존 균형 분배 대신 첫 줄을 max까지 채우고 다음 줄로 단어 단위 wrap
- `--overflow-threshold 29.5` (박스 추정 한도) 초과 줄은 별도 리포트
- placeholder/화자 라벨/짧은 외침/페이싱 보존 로직 그대로

**적용 결과**: scemsg 1,835개 메시지 변경
- 2→1줄: 630
- 3→2줄: 120
- balance(같은 줄 수, 재분배): 1085

**줄 수 분포** (scemsg):
| 분포 | 적용 전 (2차) | 적용 후 (4차) |
|---|---|---|
| 1줄 | 388 | 982 (+594) |
| 2줄 | 1245 | 1205 (-40) |
| 3줄 | 590 | 0 (-590) |

**라인 폭 분포**:
| 통계 | 적용 전 | 적용 후 |
|---|---|---|
| p50 | 17.0 | 37.0 |
| p95 | 23.5 | 40.0 |
| max | 29.5 | 40.0 |

**위험 (overflow)**: 박스 한도(29.5) 초과 **1648 메시지** → `temp/condense_overflow.txt`
- 사용자가 명시한 max=40 한도 그대로 적용
- 게임 박스 실제 가용 폭은 인-게임 확인 필요

### Step 4 — 빌드 (자동 배포 X)
**OOR 감사**: 707개 (변경 전후 동일)

**CPK 패치 결과**:
- `output/NinPri_final.cpk`: 455,022,056 bytes  
  MD5: `14b092fe835ba697364c00516fff96d4`
- `output/NinPriPatch_final.cpk`: 25,682,312 bytes  
  MD5: `626cce4a590f9c38d51b539b52e411aa`

**macOS Vita3K 배포**: 사용자 직접 (자동 cp 금지)
```bash
cp output/NinPri_final.cpk      "$HOME/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/NinPri.cpk"
cp output/NinPriPatch_final.cpk "$HOME/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/NinPriPatch.cpk"
```

### 산출물
- `tools/fix_punctuation.py` (신규)
- `tools/condense_dialogs.py` (`--greedy-fill` + overflow 리포트)
- `translations/jp_messages.json` (519 + 1835 갱신)
- `output/NinPri_final.cpk`, `output/NinPriPatch_final.cpk`
- `temp/punctuation_overflow.txt` (47 메시지)
- `temp/condense_overflow.txt` (1648 메시지)
- `patch_main/`, `patch_patch/` NMS 갱신

---

## 2026-05-17: place-name-consistency — 지명 텍스처 ↔ 시스템 메시지 한글 표기 통일

### 사용자 보고
> "시스템 메세지에서는 쇼조지(證城寺)라는 지명으로 설명이 나온 거 같은데 지명 텍스트는 슨푸로 나오는 증상이 발생. 대체로 지명 텍스트가 잘 맞긴 하는데 간간히 안 맞는 항목들이 한번씩 나옴."

### 진단
1. **텍스처 PNG 측 손상**: 50개 지명 텍스처 중 7~10개의 박스(국명) 영역이 매핑과 다른 한글로 그려져 있었음.
   - `3ECF3B0D2C2907BE`: 매핑 武蔵=무사시 → 실제 PNG "스푸"
   - `0912E45A567A41C9`: 武蔵=무사시 → "스푸"
   - `615858B46587A60E`: 美濃/武蔵 → "무크/센슈"
   - `E9F2EC8557984A58`: 駿河=스루가 → "교조구"
   - `C84B5B3A51547DF0`: 遠江=토토미 → "몬젠" (또한 매핑 자체도 "도토미"가 표준)
   - `C8C4589102431759`: 大和=야마토 → "요시노"
   - `C3848C8E5ED70F7A`: 美濃=미노 → "오미슈"
   - `7358BEAA2EF5F8A8`: 美濃/大和=미노/야마토 → "오타니/응씨"

2. **메시지 측 표기 불일치 (translations/jp_messages.json)**:
   - 遠江=토토미 vs '도토미' (1건)
   - 近江=오미 vs '오우미' (5건, _itemdata_main 포함)
   - 駿府: scemsg#707 '사가미'로 오역
   - 武蔵: scemsg#1105 伊勢가 '이가'로 오역
   - 高天原 '타카마가하라' vs '다카마가하라' (1건)
   - 善祷寺 '선도사' vs '젠토지' (1건)
   - 暗夜城 '안야성' vs '암야성' (1건)
   - 馬蕗城 '바후쿠 성' vs '마후키성' (2건)
   - 鳴神城 '나루카미 성' vs '나루카미성' (2건)
   - 金剛山 '콘고산' vs '곤고산' (2건)
   - 東海道 '토카이도'(4), '동해도'(1) vs '도카이도'
   - 大根 (마을명) '무'(채소 오역) (5건)
   - 鏡見家 '카미가' vs '카가미가'
   - 秋葉山 scemsg#104 '치바산'으로 오역

### 외부 AI 협의 (codex; gemini 응답 없음)
- A) 텍스처/매핑을 권위로 메시지를 통일 — codex 권장 표기 채택
- B) texture_localize.py 또는 자동 재생성으로 박스 한글 정정
- C) 우선순위: 매핑 확정 → 텍스처 박스 교정 → 메시지 일괄 치환

### 적용
1. **매핑 JSON 수정**: place_name_mapping.json + integrated_mapping.json '토토미'→'도토미'
2. **메시지 통일** (33건 적용): 위 표기 통일안 일괄 치환 + 5건 오역 수동 교정
3. **텍스처 박스 한글 교정** (27개 PNG): tools/render_v5.py 기반 박스 검출 후 박스 영역만 매핑 정답 한글로 덮어씀 (배너/캐릭터 영역은 보존)
   - 스크립트: `/tmp/box_overlay.py` (검출된 흰 프레임+검은 배경 박스의 내부를 검정 클리어 후 매핑된 ko 텍스트를 세로 stack 렌더)
   - 27개 텍스처 갱신, 사용자가 보고한 핵심 케이스 (3ECF3B0D, 0912E45A 등) 박스 한글 정상화

### 검증
- box-only overlay 결과 시각 비교 (`temp/preview/overlay_check/*.png`):
  - 3ECF3B0D 박스: 스푸 → 무사시 ✅
  - 615858B4 박스 2개: 무크/센슈 → 미노/무사시 ✅
  - E9F2EC85 박스: 교조구 → 스루가 ✅
  - C84B5B3A 박스: 몬젠 → 도토미 ✅
  - C8C45891 박스: 요시노 → 야마토 ✅
- 일부 텍스처(00B61B56, 5882EA68, 7282AD29)는 매핑 박스 수 > 검출 박스 수 — 박스 일부만 교정. 7358BEAA의 두번째 박스는 검출 오인식으로 부정확하게 됨. 향후 manual_bbox_mapping.json 정밀화 가능.

### 빌드/배포
- NMS 재빌드: build_patch.py OK (patch_main + patch_patch)
- CPK 패치: cpk_patch.py --append OK
  - NinPri_final.cpk: 455,022,056 bytes
  - NinPriPatch_final.cpk: 25,686,408 bytes
- macOS Vita3K 배포: `~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/` (NinPri.cpk + NinPriPatch.cpk)
- 텍스처 import: `~/Library/Application Support/Vita3K/Vita3K/textures/import/PCSE00240/` (27개 갱신)
- 백업: `temp/backup_kr_ui_2026-05-17/` (변경 전 kr_textures/ui PNG)

### 미해결/판단 보류
1. 배너(가로 붉은 띠) 글자가 거꾸로/회전 깨진 케이스가 다수 — 게임 내에서 회전돼 표시될 수 있으니 인-게임 확인 필요
2. 7358BEAA 박스 2 위치 오인식 — manual override 필요
3. 75B04DBF, 919ABD92 박스 형태(가로형)가 detect_boxes의 aspect 조건에 안 맞아 미처리 — 확인 필요
4. `scemsg#1543, #1549` 외 馬蕗城 다른 표기가 있는지 추가 감사 권장

## 2026-05-17: dialog-condense 2차 — 짧은 라인 공격적 압축 (3줄 → 2줄 376건 추가)

### 배경
1차에서 max_width=22 / DLC relaxed 24로 502건 줄 재정리 완료 후, 사용자가
"3줄인데 각 줄 글자수가 너무 적은 것"을 더 찾으라고 지시.

### 분석
- 남은 3줄 메시지 966개 — 각 줄 폭 p50: min=14.5 / avg=15.8 / max=17.0, joined p50=48
- JP 원문 폭 분포: p50=22, p95=28, max=31 (한 줄 24폭 안전)
- max_w=24로 완화 시 3줄→2줄 가능 후보 **376개** 발견

### 협의 (codex + gemini)
- gemini: "max_width 24 안전, 합산 ≤ 48 + max ≤ 24 대상 약 300~400건 압축 권장"
- codex: "기본 22 유지, 남은 3줄에 한해 24 완화. 짧은 외침 + 모든 줄 짧음 보존"
- 수렴: 3줄 한정 공격 모드 + 페이싱 보존 강화

### 도구 개선 (`tools/condense_dialogs.py`)
- `--aggressive-short-lines`: 3줄 원본일 때만 max_w 상한을 `--aggressive-max-width`(기본 24)로 상향
- `--no-preserve-pacing`: 의도적 페이싱(모든 줄 < 8자 + !?… 종결) 보존 규칙 해제
- 새 함수 `is_intentional_pacing()`: 짧은 외침 연속 판정
- 단어 중간 자르기·placeholder·화자명·5자 미만 강조 보존은 1차 그대로

### 결과
- 적용: 본편 scemsg **376건** 3→2 전환 (단어 경계 split, max_w ≤ 24)
- 줄 수 분포: 1줄 388 / 2줄 1245 (+376) / 3줄 590 (-376)
- KO 라인 폭 p95: 21.5 → 23.5 (JP p95=28 대비 안전 마진 4.5)
- OOR 감사: 707개 (변경 전후 동일 — 우리 변경으로 OOR 증가 없음)
- macOS Vita3K 경로 배포 완료 (NinPri.cpk 455MB / NinPriPatch.cpk 25.7MB)

### 누적 (1차 + 2차)
| 분포 | 원본 | 1차 후 | 2차 후 |
|---|---|---|---|
| 1줄 | 288 | 352 | 388 |
| 2줄 | 626 | 869 | 1245 |
| 3줄 | 1273 | 966 | 590 |
| 총 변경 | - | 502 | +376 (누적 878) |

### 산출물
- `tools/condense_dialogs.py` (옵션 추가)
- `tools/analyze_short_lines.py`, `tools/analyze_jp_width.py`, `tools/check_pacing_preservation.py` (분석/검증)
- `translations/jp_messages.json` (376건 ko 갱신)
- `output/NinPri_final.cpk`, `output/NinPriPatch_final.cpk` (패치 빌드)

## 2026-05-17: dialog-condense — 본편+DLC 대사 띄어쓰기 기반 줄 재정리

### 배경
이전 작업으로 일부 3줄 메시지를 2줄로 줄였으나, 일부 메시지가 좌측에 치우친 채 (line1=짧음, line2/3 비어있거나 짧음) 남아 있어 가독성 저하.
사용자 보고: "충분한 공간 있음에도 좌측에 치우친 메세지를 띄어쓰기 기반으로 재정리. 본편+DLC 전부."

### 협의 (codex + gemini)
동일 프롬프트 병렬 호출 (CLAUDE.md 외부 AI 협의 정책 준수). 두 의견 수렴:
- **max_width = 22.0** (전각 단위) — p95=20, p99=23 통계 기반 안전선
- 2줄 → 1줄: 합친 폭 ≤ 22일 때
- 3줄 → 2줄: 모든 단어 경계 후보 중 (a) 두 줄 ≤ 22, (b) 길이 차 최소
- 균형 재분배: `abs(w1-w2) > 6`이거나 좌측 극히 짧을 때
- 보존: @#(N) placeholder, 화자명 콜론 라벨, 5글자 미만 단독 강조
- 단어 중간 자르기 절대 금지

### 데이터 발견 (DLC 적용 위해 logic 보강)
본편(id 있는 1,116개) max=22.0, DLC(id 없는 1,071개) max=29.5
→ DLC는 게임이 폭 29까지 표시 가능함을 입증. `--max-width-relaxed=24` 옵션으로
원본이 22 초과인 메시지는 24까지 허용 (원본 폭 이내 한정).

### 구현 (`tools/condense_dialogs.py`)
- DP-style 단어 경계 분할 (target_n=1,2,3 케이스별)
- 페널티: 줄 끝 단어가 마침표/문장부호로 끝나면 0, 약한 쉼표 1, 평문 5
- skip 조건: placeholder-only 메시지, 화자 라벨, 모든 줄 매우 짧은 경우

### 결과
- **변환 502건** (본편 287 + DLC 215)
  - 3줄→2줄: 307건
  - 2줄→1줄: 64건
  - balance 재분배(같은 줄 수): 131건
- **줄 수 분포 변화**:
  - Before: 1줄 288 / 2줄 626 / 3줄 1273
  - After:  1줄 352 / 2줄 869 / 3줄 966  (3줄 -307 가독성 개선)
- **줄 폭 분포 변화**:
  - Before: p50=15.5, p90=19.0, p95=20.0
  - After:  p50=16.5, p90=21.0, p95=21.5  (좌측 더 채워짐)
  - p99/max 동일 (23.0 / 29.5) — 원본 긴 줄 보존

### 검증
- OOR 감사 707개로 변경 전후 동일 (변환으로 새 OOR 발생 없음)
- 일본어 원문(ja) 보존, 의미·말투 변경 없음 (줄바꿈/공백만 조정)
- proper_nouns 한글 표기 그대로
- 빌드: NinPri/NinPriPatch 양쪽 정상 패치 (CRILAYLA append 방식)
- macOS Vita3K 배포 완료. 인-게임 검증은 사용자 몫 (macOS 자동 테스트 불가)

### 변환 샘플
```
[scemsg #21]
old (2줄): | 세이슈의 도공,센지        (w=9.0)
           | 무라마사 님이 계십니다.   (w=11.5)
new (1줄): | 세이슈의 도공,센지 무라마사 님이 계십니다.  (w=21.0)

[scemsg #67 본편] 3→2
old: 무슨 낯짝으로 뻔뻔하게 내 면전에 / 왔느냐. 개도 은혜를 잊지 / 않는다는 데 개만도 못한 놈.
new: 무슨 낯짝으로 뻔뻔하게 내 면전에 왔느냐. / 개도 은혜를 잊지 않는다는 데 개만도 못한 놈.

[scemsg DLC #1116] 3→3 balance
old: 도쿠가와에게 금기인 무라마사를 숨기고 있었으니 (w=23.0) / 이유는 충분하지 ... / 칼을 가지고 도망치려 하였던 것이다
new: 도쿠가와에게 금기인 무라마사를 숨기고 / 있었으니 이유는 충분하지 …그대는 어찌된 / 일인지 그 칼을 가지고 도망치려 하였던 것이다
```

### 보존된 특수 케이스 예
- 짧은 외침/감탄: "안돼!", "어째서?" 류 5자 미만 단독 라인은 그대로
- 화자 라벨 패턴 `이름:` 첫줄은 합치지 않음
- @#(0)..@#(8) placeholder-only 포맷 정의 메시지 (sysmsg 일부) 보존
- DLC 원본 폭 29.5인 줄은 max_w_relaxed=24를 넘어서면 그대로 둠

---

## 2026-05-16: form-overlay — DLC 장비란 "Form:" hardcoded 영문 해결

### 배경
이슈 #2 (v0.7.0) 항목 5: DLC 1 바케네코 장비란에서 "**떡량렬랏 오 코 이**" 같은 깨진 글자.
1차 분석에서 NMS 모두 한글 패치 완료 확인 — 게임 외부 hardcoded 의심하고 deferred 처리.

### 영문판 검증 (사용자 통찰)
사용자 제안으로 `tools/vita3k_mode.py english` (스크립트 신규 작성) + import 폴더 전체 임시 rename(`PCSE00240` → `PCSE00240.disabled`)으로 원본 영문판 환경 구성.

영문판 캡처 결과 정확한 원문 확인:
- "**Form:Okoi**" + 15 (오코이 형태)
- "**Form:Miike**" + 11 (미케 형태)
- "**Form:Avatar**" + 17 (화신 형태)

→ 게임 코드(eboot.bin)가 `"Form:%s"` sprintf 포맷으로 출력 (NMS 외부 hardcoded).
`%s` 자리는 sysmsg lookup (Okoi=#85, Miike=#92, Avatar=#93) — 우리 NMS 패치로 한글 정상.

### 해결 (success.md "봐 재배치" 패턴 차용)
**SJIS 재배치 + ASCII overlay**:
1. `kr_sjis_mapping.json`에서 4개 한글 SJIS 이동:
   - 딱 0x8B5A → 0x8EE2 (cell 962 → 961)
   - 량 0x8B84 → 0x8EE3 (cell 303 → 962)
   - 럴 0x8B87 → 0x8EE4 (cell 306 → 963)
   - 랴 0x8B82 → 0x8EE5 (cell 301 → 964)
2. `auto_font_import.py` + `hd_font_import.py` `RUNTIME_OVERLAY_CODES`에 'F','o','r','m' (0x46, 0x6F, 0x72, 0x6D) 추가
3. 한글 cell 262/303/306/301에 영문 'F','o','r','m' 글리프 overlay
4. NMS 재빌드 → 새 SJIS 0x8EE2-5로 한글 인코딩 (61회 모두 새 위치)

### 콜론 위치 미세조정 (3단계)
| 단계 | x 위치 | 사용자 보고 |
|---|---|---|
| 원래 (중앙) | 15-16 | 다음 글자와 겹침 |
| 1차 (좌측) | 3-4 | "m에 너무 붙음" |
| **2차 최종** | **9-10** | "딱 좋다" ✓ |

`if ch == ':':` 분기로 콜론만 좌측 정렬 (x = 8 - bbox[0]).

### 부수 추가
- jp_messages.json `_itemdata #959/#970` 한글 추가 ("화신 잇기 그 일/이") — 다른 화면 또는 향후 효과 가능성
- `tools/vita3k_mode.py` 신규: english/korean/status 모드 전환 (한글 자산 개별 백업 방식, 재패치 시 사용)

### 검증 (인-게임)
- "**Form:오코이**" / "**Form:미케**" / "**Form:화신**" 정상 표시
- NMS의 딱/량/럴/랴 61회 사용 항목들 다른 화면에서 한글 정상 (사용자 확인)

### 학습 포인트
- 1차 분석에서 "다른 폰트 사용" 가설로 시간 낭비. 사용자 통찰 "글이라니까 번역 데이터 확인" + "영문판으로 원문 확인"이 결정적
- 영문 hardcoded 문자열은 `vita3k_mode english`로 원문 확정 → SJIS 재배치 + ASCII overlay 패턴 적용
- 콜론 위치는 게임 cell 너비 처리에 따라 x=8-10 권장 (좌우 균형)

---

## 2026-05-16: dlc-equipment-broken-glyph 분석 — 이미 패치된 상태 확인

### 배경
이슈 #2 (v0.7.0) 항목 5: DLC 1 바케네코편 장비란 진입 시 깨진 글자 ("떡량렬랏 오코이").

### 깨진 글자 패턴 분석
ASCII→한글 매핑 역추적:
- 첫 글자 '떡' ← ASCII 'M' (0x4D, cell 192+77=269 → KANJI cell 1644+269=1913 = SJIS 0x8B61 = 떡)
- 둘째 '량' ← ASCII 'o' (0x6F)
- 셋째 '랜' ← ASCII 'k' (0x6B)
- 넷째 '랄' ← ASCII 'e' (0x65)

→ **"Miike-Okoi"** (5자+하이픈) 영문 라벨이 한글 폰트 매핑으로 깨진 패턴 일치.

### 출처 확인 (NinPriPatch_US/scename_US.nms #116)
- 영문 원본: `Miike-Okoi`
- 한글 패치: `삼색 오코이` (jp_messages.json scename_US #116 = ko="삼색 오코이")
- v0.7.0 시점 git show: 이미 패치되어 있었음 (commit a565de7)

### 현재 빌드 결과 검증
- `patch_patch/_US/msgsheet/scename_US.nms` #116 = "삼색 오코이" (한글 정상)
- macOS Vita3K 설치된 `NinPriPatch.cpk` MD5 `312ebcaddecdbecd857ea94c539dada5` = 빌드 결과와 **완전 일치**
- 즉 **현재 우리 패치는 이미 정상 한글 표시되는 상태**

### v0.7.0 깨짐 원인 추정
- 사용자 v0.7.0 시점에 `NinPriPatch.cpk` 적용 누락 (success.md 2026-04-11 "NinPriPatch 오버라이드" 버그 시기와 유사)
- 또는 Vita3K 게임 캐시 / NinPri only 패치 적용
- 현재 v0.7.5+ 적용 시 자동 해결될 가능성 매우 높음

### DLC Pack1 추가 분석 (참고)
- `extracted_dlc/Pack1/chara/Mike00_Rest.mbs` 등 캐릭터 모델 파일에 "Mike" 영문 발견 (file metadata)
- 게임이 이 파일명을 라벨로 직접 사용하지 않음 (모델 asset name)

### 권고
- **코드 변경 불필요** — NMS 이미 패치됨
- 사용자 검증 가능 시점에 최신 패치 적용 후 인-게임 재확인 → 정상 표시 예상
- 만약 여전히 깨짐 보고 시: DLC pack mbs/asset 데이터 추가 분석 필요

---

## 2026-05-16: dlc-menu-renshu-fix — "연 습" → "단 련" 텍스처 수정

### 배경
이슈 #2 (v0.7.0) 항목 4: DLC 1 바케네코편 메뉴 화면 하단 "연습" 라벨이 게임 내 설명("단련")과 불일치.
1차 분석에서 NMS/mbs/git history 모두 출처 식별 실패 (fail.md 기록) → deferred 처리.

### 사용자 단서
사용자 통찰: "크리타 텍스쳐 파일에 연습 있을꺼야. 중간에 띄어쓰기 되어서 '연 습'으로 되어 있을 수도".

### 발견
`textures/work/DF66CADDABE022E3.kra` (Krita 파일, 7개 .kra 중 1개) 안 layer14:
- `<text id="shape0" ...>연 습</text>` (SVG shape layer, viewBox 4096x4096, position 1876,3086, font size 21pt × 8x scale)
- maindoc.xml에 `name="연 습"` 라벨

같은 파일에 다른 메뉴 라벨도 있음:
- "능 력", "장 비", "결 정", "뒤 로", "저장하기", "불러오기", "새게임", "설정", "기본 설정", "게임 스타일 선택", "아이템 바로가기", "소유한 칼", "승리!", "전투!", "능력 레벨", "장신구", "효 과", "저장", "기술", "조작" 등 → DLC 메인 UI atlas

### 해결
1. **.kra 파일 백업**: `textures/work/DF66CADDABE022E3.kra.bak_renshu`
2. **layer14 SVG 수정**: `<text>연 습</text>` → `<text>단 련</text>`
3. **maindoc.xml name 수정**: `name="연 습"` → `name="단 련"`
4. **Krita CLI export**: `/Applications/krita.app/Contents/MacOS/krita --export ... --export-filename ...` → 4096x4096 RGBA PNG
5. **설치**:
   - `kr_textures/ui/DF66CADDABE022E3.png` (리포 사본)
   - `~/.../Vita3K/textures/import/PCSE00240/DF66CADDABE022E3.png` (게임 import)

### 검증
- 변경 픽셀: 17,333개 (0.1033%) — 의도된 영역만 변경
- 변경 bbox: x=(1876, 2211), y=(2947, 3122) — 정확히 layer14 위치
- 시각 확인: "단 련" 글자 깔끔히 렌더링 (temp/preview/danryeon_check.png)

### 사용자 인-게임 검증 (가능해진 시점에)
- DLC 1 바케네코편 진입 → 메뉴 화면 → "단 련" 라벨 표시 확인
- 메뉴 선택 시 게임 내 설명 (sysmsg #486-488 "단련에 대하여...") 과 용어 일치

### 1차 분석 실패 → 사용자 단서로 성공한 패턴
- NMS/mbs 검색만으로는 .kra Krita 작업 파일의 SVG text layer를 검출할 수 없음
- 사용자가 작업 도구(Krita)에 대한 직관적 단서 제공 → 즉시 발견
- 향후 텍스처 출처 식별 시 `textures/work/*.kra` SVG layer name 검색 추가 고려

---

## 2026-05-16: battle-result-time-fix — 결과창 hh:mm:ss 콜론 깨짐 수정 ("봐" SJIS 재배치)

### 배경
이슈 #2 (v0.7.0) 항목 3: DLC 1 바케네코편 전투 결과창 첫 줄 "시간" 값이 "0봐 0 0봐 1 9" 형태로 깨짐.

### 원인 진단 (PDCA)
- 화면 분석: 정상 의도 `"0:00:19"` (hh:mm:ss) 시간 표시
- 게임 코드(eboot.bin)가 시간 출력 포맷 `"%d：%d：%d"`에 **전각 콜론(`：`, SJIS 0x8146) hardcoded**
- raw 0x8146 → 폰트 KANJI 페이지 local cell 6+448=454로 매핑
- cell 454 = 한글 "봐" (SJIS 0x8C5E)와 동일 위치 → "봐" 글리프 표시
- success.md 2026-04-13 fullwidth-normalize와 동일 메커니즘이지만 NMS가 아닌 게임 바이너리 hardcoded라 `_normalize_text()` 적용 불가

### 검증
- 빌드된 NMS 전체에 raw 0x8146 = 0회 (정규화 완벽)
- 원본 NinPri _itemdata 595회, sysmsg 4회 — 모두 정규화됨
- eboot.bin 검색은 압축으로 직접 식별 어려움 — 메커니즘으로 단정

### 해결: A안 (success.md "덴 글자 복구" 패턴 차용)
1. **"봐" SJIS 재배치**: `kr_sjis_mapping.json`에서 [140, 94] (0x8C5E) → [142, 239] (0x8EEF, local 974, ASCII zone period skip slot)
2. **cell 454 콜론 오버레이**: `auto_font_import.py`/`hd_font_import.py`에 `FULLWIDTH_OVERLAY = {454: ':'}` 추가
   - 게임 raw 0x8146 출력 → cell 454 → ":" 글리프 표시 (정상!)
3. NMS의 "봐" (216회 출현)은 새 SJIS 0x8EEF로 인코딩 → cell 974에 자동 그려진 "봐" 글리프 표시

### 검증 (빌드 후)
- 빌드된 NMS의 봐(SJIS 0x8EEF) = 216회 (예상치 일치)
- 옛 봐(SJIS 0x8C5E) = 0회 (완전 마이그레이션)
- 폰트 텍스처 cell 454 = 콜론 ":" 글리프 (시각 확인)
- 폰트 텍스처 cell 974 = "봐" 한글 글리프 (시각 확인)

### 적용된 폰트 텍스처
- A8E6FDD162258699 (메뉴 KANJI 폰트) — auto_font_import 재생성, 959 글리프
- 8665CE082D339B33 (일반 KANJI 폰트) — auto_font_import 재생성, 959 글리프
- 6706A53E1D94C16E (HD 폰트) — hd_font_import 재생성, 1024x1024 dark format

### 빌드/패치
- `python3 tools/build_patch.py` 재빌드 — sysmsg 574+963, _itemdata 878+1426 매칭 유지
- `python3 tools/cpk_patch.py` 적용 — NinPri +149KB, NinPriPatch +282KB
- macOS Vita3K 경로 설치: `~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/`
- 폰트 textures: macOS 경로 (`~/.../textures/import/PCSE00240/`) + 리포 `kr_textures/font/` 동기화

### 백업
- `translations/kr_sjis_mapping.json.bak_bwa`

### 남은 검증 (사용자)
- 결과창 시간: "0:00:19" 정상 표시 확인 (cell 454 콜론 적용)
- NMS의 "봐" 73회 정상 표시 확인 (cell 974 새 봐 위치)
- 전각 콜론(`：`)이 추가로 hardcoded인 다른 화면도 동일하게 정상화될 것
- 다른 전각 punctuation (`！？（）％`) hardcoded 영향은 사용자 보고 발견 시 동일 방식으로 추가 (`FULLWIDTH_OVERLAY`)

---

## 2026-05-15: currency-unify — 화폐 단위 통일 (A안: 냥/문 + 백분율 %)

### 배경
이슈 #3 (v0.7.1) 보고: 가마꾼 대사에서 금액 호칭이 "돈"으로 나오는데 다른 곳은 "문"으로 표시되어 불일치.

### 전수조사 결과 (temp/currency_audit/summary.md)
- 일본 원작 화폐: 両(큰)/文(작은)/分(백분율 1%)/金(money 의미)
- 한국어 현재: 냥 5건(両, 일관) / 문 4건(文 포맷) / 푼 9건(分 백분율) + 1건(文 관용구) / 돈 25건(金) / % 2건(分)
- 텍스처 4개(247C/547720/2E2003/1D6742BB): 모두 "냥/문" 통일 완료

### 핵심 오번역 식별
- `sysmsg #205, sysmsg_main[153]` 원문 `文を支払い利用しますか？` → "돈을 지불하고 이용하시겠습니까?" (오번역)
- 이게 사용자가 본 가마꾼 화면 시스템 메시지의 정체

### 외부 AI 협의
- codex: 사용량 한도 초과로 응답 실패
- gemini: A안(냥/문 + 백분율 %) 추천. 근거: '푼'은 돈/비율 두 의미로 모호, '문'은 조선 상평통보 단위로 한국 사극 친숙, 텍스처 4개 보존
- 사용자 결정: A안 채택 + 추상적 '돈'(金) 25건은 현행 유지

### 수정 항목 (총 14건)
1. `sysmsg #205, sysmsg_main` 2건: "돈을 지불하고" → "문을 지불하고"
2. `_itemdata` 백분율 8건: "1푼/2푼/5푼" → "1%/2%/5%"
3. 조사 자연화 4건: "1%을" → "1%를" (생명력의 X%를 회복/X%를 흡수)

### 보존
- 관용구 `ビタ一文` → "한 푼도 안" — 한국어 자연스러움
- 일반 대화 25건 "돈" → 그대로 (자연스러운 의역, 시스템 메시지가 아님)

### 빌드/패치
- `python3 tools/build_patch.py` 재빌드 — sysmsg 574+963, _itemdata 878+1426 매칭 유지
- `python3 tools/cpk_patch.py` 적용 — NinPri +149KB, NinPriPatch +282KB
- macOS Vita3K 경로 설치: `~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/`

### 남은 검증 (사용자)
- 가마꾼 화면 진입 → "문을 지불하고 이용하시겠습니까?" 표시 확인
- DLC 어빌리티 화면 → 효과 텍스트에 "1%를 흡수한다", "5% 상승한다" 등 정상 표시 확인
- 백업: `translations/jp_messages.json.bak_currency`

### 영향 받지 않는 곳
- 텍스처 4개 (소바집/식당/찻집/상인 메뉴 UI) — 변경 없음 (이미 "냥/문" 통일)

---

## 2026-05-15: period-glyph-fix — 시스템 대사 마침표가 가운뎃점처럼 보이던 문제 수정

### 증상
IMG_3111 대사 "넘어가 주지 ·뒤는 나라에 / 맡기는 걸로 해두마 ·" — 마침표가 가운뎃점(·)처럼 글자 라인 중앙에 떠 있음.

### 원인
HD 폰트 텍스처 `6706A53E1D94C16E` (1024 KANJI 페이지)의 cell 238 (= 192 + 0x2E '.') 글리프가 import에서 (14,14)-(16,16) — cell 정중앙에 size 7픽셀 작은 점으로 그려짐. 게임이 raw byte 0x2E를 이 cell에서 가져와 렌더 → 가운뎃점 시각.

원본 export 글리프는 (4,17)-(12,25) — cell 좌측 중하단에 size 65픽셀의 정상 마침표.

비교:
- 6706A53E IMPORT cell 238: (14,14)-(16,16) MIDDLE (잘못)
- 6706A53E EXPORT cell 238: (4,17)-(12,25) BOTTOM-LEFT (정상)
- 8665CE08 IMPORT cell 238: (2,25)-(4,27) BOTTOM-LEFT (정상, auto_font_import.py 결과)

8665CE08은 정상인데 6706A53E만 잘못된 이유는 미상 (hd_font_import.py가 의도와 다른 위치에 그림). 코드상으로는 `gy = y + cs - gh - 4*scale - bbox[1]` 좌측 하단 정렬 로직.

### 처리
1. `~/Library/.../import/PCSE00240/6706A53E1D94C16E.png`의 cell 238 영역 (448,224)-(480,256)을 export 원본의 동일 영역으로 덮어쓰기 (다른 한글 글리프는 그대로 유지)
2. `kr_textures/font/6706A53E1D94C16E.png`도 동기화
3. `tools/hd_font_import.py`의 `RUNTIME_OVERLAY_CODES`에서 0x2E '.', 0x2C ',' 제거 — 향후 재빌드 시 export 원본 글리프 보존
4. /tmp/6706A53E_import_backup.png에 이전 import 백업

### 검증
`temp/preview/period_glyph_fix.png`에서 OLD/EXPORT/NEW 12배 확대 비교: NEW가 EXPORT와 동일한 정상 마침표 모양.

### 남은 확인 (사용자)
Vita3K 재시작 후 시스템 대사에서 마침표 위치 검증. 만약 여전히 가운뎃점처럼 보이면 (a) 마침표 글리프가 다른 폰트(예: 2E88068C58DD36D5 ASCII 페이지)에서 오는 것 (b) NMSB 텍스트에 실제 ・(U+30FB)가 남아있음 — 어느 쪽인지 추가 분석 필요.

### 외부 AI 협의
gemini CLI 호출했으나 응답 지연. codex CLI 사용량 한도 도달. 가설이 명확하고 export/import 비교 픽셀 증거가 결정적이라 단독 진행.

---

## 2026-05-15: digit-0-sprite-fix v8 — 1D6742BB 진짜 원본 베이스로 디지트 0 복구 완료

### 추가 진단
v7 패치 적용 후 사용자가 Vita3K 상인 화면 스크린샷 재제출. 가격 컬럼에서 끝자리 0이 비어있음 (예: 50푼이 "5 ?"). v7 수정으로도 부족함.

### 핵심 원인
이전 1D6742BB 빌드는 `upscaled/1D6742BBC0DDB7EC.png` (1024x1024 HD 팩) → LANCZOS 256x256 다운스케일을 베이스로 사용. 그런데 HD 팩 텍스처에는 원본 256x256의 **디지트 0 sprite (140,168)-(157,186)·(160,168)-(171,181) 두 군데가 없음**(또는 다른 형태). 다운스케일 결과에는 그 자리가 비어 있어, 게임이 그 위치에서 디지트 0을 가져올 때 투명 픽셀만 가져옴 → 끝자리 0 누락.

### 해결
macOS Vita3K export 폴더 `~/Library/Application Support/Vita3K/Vita3K/textures/export/PCSE00240/1D6742BBC0DDB7EC.png`에서 진짜 256x256 원본 발견 → `textures/originals/`에 추가 → 동일 config로 재빌드.

### 검증 (clear 영역 밖 손상)
`(원본 알파 > 30) & (kr 알파 < 10)` 마스크로 디지트 후보 손상 클러스터 추출 후 우리 clear 영역과 교차.
- 247C255A: 22개 후보 모두 [정상-clear내]
- 547720A3: 24개 후보 모두 [정상-clear내]
- 1D6742BB: 17개 후보 모두 [정상-clear내] (v7까지는 2개 경계밖 손상, v8에서 해결)

### 동기화
`kr_textures/ui/1D6742BBC0DDB7EC.png` + macOS Vita3K import 폴더 모두 갱신. 사용자 측 Vita3K 재시작 후 상인 화면 검증 부탁 (가격 표시의 끝자리 0 정상 출력 확인).

---

## 2026-05-14: digit-0-sprite-fix — 소바집/식당/상점 UI 디지트 sprite 손상 복구

### 배경
사용자 보고: 소바집 화면에서 가격의 "0"이 출력 안 됨 (예: "80"이 "8"로만 보이는 듯). 상점·찻집도 동일 의심.

### 원인
247C255A·547720A3·1D6742BBC0DDB7EC 텍스처의 한글화 작업에서 사전 렌더 디지트 sprite (0-9) 영역까지 clear가 침범:
- **247C255A** 가격 clear_rect (0,163,72,32) → 디지트 0 sprite (32,189)-(52,209)의 상단 6px 잘림
- **547720A3** 가격 region (30,124,100,28) → 디지트 sprite (96,126)-(116,146)와 (38,126)-(52,146) 잘림
- **547720A3** 냥 region (0,184,60,26) → 우측 디지트/장식 sprite (38,186)-(56,205) 잘림
- **1D6742BB** 냥 region (138,145,40,44) → 안에 ryo 영문/所 한자/디지트 0이 모두 있는 큰 박스가 모두 클리어됨

### 조사 방법
- `textures/originals/`의 원본 알파 connected-component 분석으로 디지트 sprite bbox 정밀 측정 (scipy.ndimage)
- 손상 = `(원본 알파 > 30) & (kr 알파 < 10)` 마스크로 클러스터 분석
- 1D6742BB는 원본 부재 → `upscaled/1D6742BBC0DDB7EC.png` (1024x1024)을 LANCZOS 256x256 다운스케일로 추정 베이스 사용
- 시각 검증: `temp/preview/{hash}_price_zone.png`, `_ryo_zone.png` 에 박스 오버레이로 영문/디지트 분리

### 처리
`translations/texture_localize_config.json` 수정:
- **247C255A** 가격: text h 32→22, clear_rect h 32→25 (y=163-188까지만 클리어, 디지트 y=189 보호)
- **547720A3** 가격: x 30→38, w 100→56, clear_rect 신규 추가 (영문 Price만 클리어, x=96+ 디지트 보호)
- **547720A3** 냥: w 60→38, clear_rect 신규 추가 (디지트/장식 x=38+ 보호)
- **1D6742BB** 가격: text h 32→22, clear_rect h 32→25 (안전 마진)
- **1D6742BB** 냥: h 44→25, clear_rect 신규 추가 (y=170+ 所 한자/디지트 0 보호)

### 결과
- `kr_textures/ui/247C255A400261FF.png` — 디지트 0 링 온전히 복원
- `kr_textures/ui/547720A3B20C12AB.png` — 가격 옆 디지트들 + 냥 옆 sprite 복원
- `kr_textures/ui/1D6742BBC0DDB7EC.png` — upscaled 베이스로 디지트/한자 복원
- 미리보기: `temp/preview/{hash}_after_fix.png` 3개

### 남은 검증 (사용자 측 Windows Vita3K 필요)
- 실제 게임에서 소바집/식당/상점 가격 표시 "80", "30" 등 디지트 0 출력 확인
- 1D6742BB는 upscaled 추정 베이스라 인게임 실제 export 원본과 미세 차이 가능 — 차이 발견 시 사용자가 Vita3K export 후 textures/originals/에 저장 → 재빌드

### 참고
- 사용자 메시지 "소바집, 상점, 찻집 문제는 텍스쳐 문제일 가능성이 제일 큼" → 곧장 정답으로 안내해줌
- Gemini CLI 분석도 동일 가설 (이슈 #1, "UI 텍스처 한글화 과정에서 숫자 스프라이트 영역이 의도치 않게 지워졌을 가능성")로 수렴
- Codex CLI는 사용량 한도 도달, 단독 진행

---

## 2026-05-10: texture-upscale — Vita3K export 텍스처 FHD 업스케일 (로컬 전용)

### 배경
HD 팩(Muramasa Complete 2.0)이 커버하지 못하는 export 텍스처들이 FHD 화면에서 흐림. 273장의 export 자산을 일괄 업스케일하되, 한글 패치를 깨뜨리지 않고 배포에는 영향이 없어야 함.

### 처리
1. PDCA Plan: `docs/01-plan/features/texture-upscale.plan.md` (제외 정책·엔진 근거)
2. Real-ESRGAN ncnn-vulkan v0.2.5.0 (universal binary) → `temp/realesrgan/`, arm64 즉시 동작
3. 신규 도구 `tools/upscale_export.py`:
   - 모델 `realesr-animevideov3`, max 변 1920px cap (LANCZOS 다운샘플)
   - 자동 skip: 폰트 4 hash (`tools/.font_hashes.json`) + `kr_textures/ui/` 81종
   - dry-run / limit / install / force / cache 옵션
4. `.gitignore` 에 `upscaled/` 등록 + 사유 주석
5. 샘플 5장 검증 (45s, 9s/장 페이스, 1920 cap 정상)
6. 본 배치 256장 / 1917s ≈ 32분, 0 실패
7. Report: `docs/04-report/texture-upscale.report.md`

### 결과
- 261장 업스케일 (루트 68 + PCSE00240/ 193), 폰트/한글 UI 15장 자동 skip
- 52MB → 465MB (4x + RGBA + 무손실 PNG)
- `upscaled/` git status 안 잡힘 (gitignored 검증 완료)
- 캐시 동작: 재실행 시 신규분만 처리

### 핵심 결정
- Real-ESRGAN 채택 — 기존 `batch_upscale.py` 통합 경험, universal binary, animevideov3 게임 친화
- 1920px cap (FHD 단축) — 1024→1920 (2x), 512→1920 (4x cap), 256→1024 (4x cap)
- 비배포 정책 강제 — `.gitignore` 라인에 사유 주석으로 의도 고정
- 폰트/한글 UI 자동 제외 — JSON + 디렉토리 글롭 두 소스 활용

### 사용법
```bash
python3 tools/upscale_export.py             # 전체 (캐시 스킵)
python3 tools/upscale_export.py --dry-run   # 사전 확인
python3 tools/upscale_export.py --install   # Vita3K import/ 자동 복사
```

### 커밋
- `a0b235c` Add texture-upscale tool for local FHD upscaling

---

## 2026-04-26: 1823D39C0279886B 지도 화면 로마자 지명 14개 한글화

### 배경
사용자 스크린샷(`OneDrive/Pictures/스크린샷/스크린샷 2026-04-26 061241.png`)에서 지도 메뉴의 라벨이 영어/로마자로 표시됨 발견 — 카테고리: 国名 로마자 (place_names 아틀라스, status: pending in `place_name_textures.json`).

### codex/gemini 병렬 자문 결과
- gemini: 지명은 `place_name_mapping.json`으로 관리. 스탯 라벨은 UI 텍스처 + 폰트.
- codex: 지도 핀 지명 텍스처 아틀라스, 특히 `1823...`와 `place_names` 계열.
- 수렴 → `1823D39C0279886B` 타겟 확정.

### 처리
1. 256x128 원본/1024x512 kr 버전 양쪽에서 라벨 14개 식별:
   - 수평(좌측): YAMASHIRO/SHINANO/MUSASHI/HIDA/YAMATO/TOTOMI/MIKAWA
   - 수직(우측): SAGAMI / SURUGA+OWARI / MINO+KAI / OMIGAISE / IZU
2. 알파 컬럼 분석으로 각 라벨 bbox 정밀 산출 (5개 수직 컬럼 + 7개 수평 행)
3. `Griun_PolSensibility-Rg.ttf`로 한글 렌더링 → 원본 bbox 동일 위치에 배치
4. `kr_textures/ui/1823D39C0279886B.png` 갱신 + `C:/game/vita3k/textures/import/PCSE00240/`로 동기화
5. `texture_localize_config.json`에 regions 14개 + translations 매핑 추가, status="done"
6. `kr_textures/ui/_notes/1823D39C0279886B.txt` 노트 작성
7. Vita3K 부팅 sanity 체크 완료

### 매핑
야마시로 / 시나노 / 무사시 / 히다 / 야마토 / 토토미 / 미카와 / 사가미 / 스루가 / 오와리 / 카이 / 미노 / 오미이세 / 이즈

### 주의
- "OMIGAISE" 8글자가 단일 라벨 vs 2-3개 분리 라벨 여부 미확정 — 일단 "오미이세"(近江·伊勢 합산)로 통합 처리. 게임 내에서 두 곳에 따로 표시되면 후속 분리 필요.
- 게임 내 검증은 사용자 세이브 로드 후 지도 화면에서 확인 필요 (자동 진입 비용 과대).

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

## 2026-05-10 — Vita3K export에서 신규 텍스트 텍스처 6개 발견·이동
- 게임 진행 후 export 폴더에 246개 텍스처 (이전 기준 대비 236개 신규)
- alpha-text 휴리스틱 + 컨택시트 검토로 텍스트 후보 식별
- 사용자 작업 폴더(`textures/originals/` + `textures/text/`)에 복사 완료:
  - **04110A0F74BE6991** (256×256) — 지명 한자 아틀라스 (尾張/武蔵/伊賀 등 16개)
  - **15CF750523FBB7C6** (512×512) — 鬼 한자 + UI 심볼
  - **17BBEF37CC65904A** (512×512) — Hashimoto/Basiscape 크레딧
  - **9F518FC3E233B9DE** (256×256) — 상점/툴팁 UI 패널 (開/罠 한자 + 보물상자/검)
  - **ECB628336E68D6AA** (256×128) — Clear/X UI 버튼 + 한자 심볼
  - **EDA6F03EC4E141EE** (128×128) — PS Vita SELECT/START 라벨
- `translations/texture_localize_catalog.json`에 6개 항목 추가, summary high=12/med=4/low=1로 갱신
- 한글화 불필요 항목 6개도 catalog `_recent_additions.skipped`에 기록 (브랜드 로고, 디지트, 폰트 스프라이트 등)
- 사용자 언급 "식당/상인 메뉴 항목" 자체 텍스트는 미발견 — 동적 폰트 시스템으로 렌더링되는 것으로 추정. 9F518FC3 (상점 UI 패널)이 가장 근접

## 2026-05-10 (2회차) — 식당/상인 메뉴 UI 텍스처 5개 발견·이동
- 사용자가 식당/상인 화면 진입 후 export 갱신 (246→677개, 431개 신규)
- 사용자 스크린샷 3장 (저장 UI, 상인 메뉴, 소바 식당 메뉴) 분석
- 작업 폴더(`textures/originals/` + `textures/text/`)에 복사:
  - **247C255A400261FF** (256×256) — 식당(Soba Shop) 메뉴 UI: Inventory/Sold Out/Money/Meals/Menu/Price/mon/ryo + 売切
  - **547720A3B20C12AB** (256×256) — 상인 메뉴 UI: + Restaurant/料亭
  - **FFFFD99DCD90D546** (256×128) — 상점 외관 노렌/간판 한자 사인
  - **2E88068C58DD36D5** (1024×1024) — ASCII 폰트 아틀라스 (영문/숫자/기호 그리드)
  - **A8E6FDD162258699** (1024×1024) — KANJI 폰트 아틀라스 (수백 한자 그리드)
- catalog summary: high 12→16, med 4→5, total 17→22로 갱신
- 사용자 요청 'sold out 같은 단어'는 247C255A/547720A3 두 아틀라스 모두에 'Sold Out'으로 사전 렌더링되어 있음 — 한글로 교체 가능
- A8E6FDD162258699 폰트가 메뉴 항목 한자 렌더링에 사용되는 것으로 추정 — 기존 한글 SJIS 매핑(0x89CD-0x8EE0) 적용 가능성 검증 필요

## 2026-05-10 (3회차) — 식당/상인 메뉴 UI 한글 번역 + A8E6FDD1 한글 폰트 적용
### 외부 AI 교차 검증 (codex + gemini)
- 결론 일치: 화폐 단위 냥/문 (existing %d냥%d문 포맷), Sold Out → 품절 (existing translation)
- A8E6FDD1 가설 일치: 기존 게임 폰트와 동일 데이터, 메뉴 화면 전용 인스턴스 (auto_font_import 적용 가능)

### 폰트 한글화
- `tools/.font_hashes.json`이 이미 A8E6FDD162258699 포함 → auto_font_import.py 실행으로 한글 글리프 959자 자동 주입
- 메뉴 항목명 한자(자루소바, 청어소바, 덴푸라소바 등)가 NMS의 한글 SJIS 시퀀스를 통해 한글 출력 예정

### 사전 렌더 메뉴 UI 한글 번역
- **247C255A400261FF** (식당/Soba Shop): 9개 영문 단어 → 한글
  - Inventory→보유, Sold Out→품절, Money→소지금, Soba Shop→소바집,
    Meals→식사, Menu→메뉴, Price→가격, mon→문, ryo→냥
- **547720A3B20C12AB** (상인/Restaurant): 9개 영문 단어 → 한글
  - Restaurant→식당, 나머지 247C와 동일 단어는 동일 한글
- 폰트: Griun_PolSensibility-Rg.ttf (붓글씨 스타일)
- texture_localize.py로 영역 클리어 + 한글 렌더링 → import + kr_textures/ui/ 양쪽 저장
- 전체 단어 영역 좌표를 알파 connected-component 검출로 측정 후 v2에서 미세조정

### 구현 위치
- Vita3K import: `~/Library/Application Support/Vita3K/Vita3K/textures/import/PCSE00240/`
  - 247C255A400261FF.png (45KB)
  - 547720A3B20C12AB.png (40KB)
  - A8E6FDD162258699.png (269KB - Korean overlay)
- 리포 사본: `kr_textures/ui/` 동일 파일

### 다음 검증 단계
- 사용자가 Vita3K 재시작 → 식당/상인 메뉴 화면 진입 → 한글 표시 확인
- 미세 위치 조정이 필요하면 사용자 스크린샷 추가 제공 후 좌표 수정

## 2026-05-10 21:53 — codex 위임으로 메뉴 UI 한글 재작업 완료
### 위임 사유
- 247C255A 식당 UI 글씨 잘림 발생 (v2 좌표가 거칠게 측정됨)
- 547720A3가 사용자 상인 화면(s5)에 미적용 — 다른 hash 의심
- 사용자 요청: "이미지 편집은 codex가 더 잘하니까 codex한테 시키자"

### codex 작업 결과
1. **247C255A v3** (식당, Soba Shop): 알파 connected-component bbox 기준 정밀 좌표 + 폰트 재산정. 글씨 잘림 해소. 9개 단어 한글화 유지.
2. **상인 UI 진짜 hash 식별**: `1D6742BBC0DDB7EC` (256x256). 6개 알파-only-white 후보 중 식별. 사용자 스크린샷 s5의 "Money/Item/Inventory/Price/mon"과 일치
3. **1D6742BBC0DDB7EC 한글화**: Inventory→보유, Sold Out→품절, Item→품목, Price→가격, Money→소지금, mon→문, ryo→냥
4. **547720A3 재분류**: Restaurant/Meals 식당류 텍스처(상인 아님)로 description 정정. 한글 번역은 유지(요리집/식당 화면이 등장하면 적용될 예정)

### 출력 파일
- 식당: `kr_textures/ui/247C255A400261FF.png` (42KB) + Vita3K import 동일
- 상인: `kr_textures/ui/1D6742BBC0DDB7EC.png` (35KB) + Vita3K import 동일
- 식당류: `kr_textures/ui/547720A3B20C12AB.png` (40KB) — 변경 없음
- config: `translations/texture_localize_config.json`에 1D6742BBC0DDB7EC 항목 추가, 247C255A regions v3 갱신

### 검증 (codex 자체 검증)
- JSON 파싱 정상
- 모든 PNG 256x256
- repo/import byte 동일
- visible RGB는 흰색 일관, alpha=0 픽셀은 (0,0,0,0)
- macOS의 `tools/vita3k_ctrl.py status`는 windll 의존으로 실패 → 인-게임 검증은 사용자 몫

### 다음 검증
- 사용자가 Vita3K 재시작 → 소바집 식당 화면 (s3/s6 reproduce) → 글씨 잘림 없는지 확인
- 상인 화면 (s2/s5 reproduce) → "보유 | 가격 | 품목 | 소지금 | 문" 한글 출력 확인

## 2026-05-17: Dialog cleanup 6th pass (greedy max=26, box-fit)

### 결과
- 사용자 명시 한도 max_width=26 적용 (예시: "이글이글 타오르는 그 눈 일찍이 나조차 능가하는" = 23폭)
- 1줄→다줄 wrap, 2줄→3줄 overflow wrap 허용 (greedy 모드 한정)
- 수렴 회차: greedy 522+309+4=835건, fix_punc 14+3=17건 (총 852건 변경)
- 라인 폭: p50=22.5 / p95=26.0 / p99=26.0 / **max=26.0** (26 초과 0건)
- 줄 수 분포: 1줄 496 / 2줄 1418 / 3줄 308 / 4줄 1
- OOR: 707 (변동 없음)

### 도구 개선 (`tools/condense_dialogs.py`)
- greedy 모드에서 1줄 메시지의 should_skip 우회 (overflow wrap)
- process_data: `1toN` / `wrap_grow` 통계 (2줄 → 3줄 등 줄 수 증가 허용)
- reformat: greedy + 원본 max > target_max일 때 줄 수 증가 허용

### 배포
- macOS Vita3K: ~/Library/Application Support/Vita3K/Vita3K/fs/ux0/app/PCSE00240/
- NinPri.cpk MD5: da9c971fa01644927e74527ac2cf1f12 (455,022,056 bytes)
- NinPriPatch.cpk MD5: 605f20b49fe820e91d9a3721af773f5b (25,682,312 bytes)
- 배포 MD5 = 빌드 MD5 검증 완료

## 2026-05-22 UI 텍스처 HD 베이스 재한글화 (메뉴 4 + 지명 1)

대상: 247C255A400261FF(소바집), 1D6742BBC0DDB7EC(상인), 547720A3B20C12AB(식당),
2E2003777A770327(찻집), 59015B61BFC0B7BC(相模 지명).

### 문제
- 메뉴 3개(247C/1D67/547)는 256 export를 LANCZOS 4배 확대 → 글자 흐림.
- 지명(59015B)은 K0_CLEAR bbox [183,8,239,120]가 흰 프레임 우측(x≈237)·하단(y≈130)을
  침범해 박스 프레임이 ㄷ자로 열림(확대가 아니라 좌표 데이터 자체 결함).

### 해결
- 신규 `tools/localize_hd_textures.py`: 기존 좌표(texture_localize_config.json /
  place_texture_jobs.json)를 그대로 재사용하되, Plaidray HD팩 베이스(메뉴 1024,
  지명 2048x1024)에 좌표·폰트크기를 (HD크기/원본크기)배 자동 스케일해 직접 렌더.
  렌더 함수는 texture_localize / render_place_texture_job 에서 import 재사용(중복 0).
- HD 베이스 == 원본×4 정렬 수치 검증(alpha IoU 0.83~0.99).
- 지명 박스: connected-component로 프레임(단일 외곽선) vs 글자(相+模, HD y96~480) 분리.
  K0_CLEAR → [184,8,233,122](글자만, 하단 프레임 막대 HD y≈520 보존), K0 → [186,14,232,120].
  결과: 닫힌 사각 프레임 + 相模 완전제거 + 사가미 중앙정렬.
- 설치: kr_textures/ui + Vita3K import + fs/textures/import.

### 외부 협의
- codex: 사용량 한도 초과로 실패. gemini: 라우팅 에러 후 본문 응답 — 접근법은
  기존 렌더러 로직 재사용 권장(신규 스크립트가 import로 충족), font×4 + fit_to_box는
  스케일 좌표계에서 수행(충족), 알파 보존(충족).

### 미검증
- macOS 환경이라 CLAUDE.md의 Windows용 Vita3K 자동 실행 플로우로 in-game 확인 불가.
  텍스처는 import에 설치 완료 → 게임 재시작 시 적용. 인게임 육안 확인 권장.

## [2026-05-22] UI 텍스처 편집 웹도구 완성
- tools/build_ui_index.py → translations/ui_editor_index.json (82개: localize 11 + place 60 + manual 11, 파일별 memo 보존)
- tools/ui_editor/server.py — stdlib http.server (의존성 0). API: /api/index, /api/image, /api/memo, /api/regions, /api/render
- tools/ui_editor/static/{index.html,app.js,style.css} — 3분할 UI (목록·캔버스·속성)
  - 좌: 검색/시스템필터 + 썸네일 + 메모(노란색) + 설명 표시 → 파일 식별 빠르게
  - 중: 배경색(체커/검정/레드/블루) 토글, 원본/kr 토글, 줌, region 박스 8핸들 드래그/리사이즈, ＋영역, 생성 미리보기 모달
  - 우: 텍스트/박스/글씨크기/색/정렬/배경/쓰기방향(가로·세로·회전)/비율 등 시스템별 속성 + 반영
- 검증: 백엔드 전 API curl 통과, 경로탈출 403 차단, 무변경 round-trip = 사실상 0줄(렌더러 무시 필드 1줄 정리만), 실제 렌더러로 localize/place 미리보기 생성 확인(야마시로/시나노 정상)
- 핵심설계: region 지오메트리/텍스트는 네이티브 config 역기록(기존 키 유지+없던 키는 비기본값만 추가 → 무손실), memo는 인덱스 sidecar. 생성은 실제 texture_localize.py/render_place_texture_job.py 호출 → 게임과 동일 출력
- 실행: python tools/ui_editor/server.py → http://127.0.0.1:8765
