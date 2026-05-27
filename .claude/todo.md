# TODO — 진행 예정 / 미해결 작업

> 완료 작업 상세는 [success.md](success.md), 실패·한계는 [fail.md](fail.md).
> 이 파일은 **열린/보류/예정** 항목만 둔다. 완료되면 success.md로 옮기고 여기선 지운다.
> 현재 릴리스: **v1.2.1** 🎉 (2026-05-27 — ✕ 추가팩에 메인 메뉴 DF66CADD 포함, 이슈 #15)
> 텍스처 편집: `python tools/ui_editor/server.py` (http://127.0.0.1:8765)

---

## 보류 — DLC 엔딩 "完" → "완 결" 한글화 (이슈 후속, 2026-05-27 위치 확정)

- **출처 확정(codex+직접 조사)**: DLC 엔딩 完은 export/originals 텍스처가 아니라, 설치된 DLC 팩
  CPK 내부 `GUI/Ending_P1~P4.ftx`(에피소드별). 각 1024×1024 캐릭터 일러스트 + 좌하단 큰 붓글씨
  完(bbox≈x1-320,y430-850). 본편 엔딩 The End(`E4A9FD9D`)와 별개.
  - CPK: `~/Library/Application Support/Vita3K/Vita3K/fs/ux0/addcont/PCSE00240/OBOROMURAMASAPK1~4/NinPriPackN.cpk`
  - 추출본/미리보기(temp/): `temp/dlc_ftx_png/pack{1..4}/GUI/Ending_P*.png`, `temp/preview/DLC_endings_all4.png`
  - export 폴더(747개) 전수 — 일치 텍스처 없음 → **Vita3K import hash 미확보**.
- **방법(택1, 다음 작업)**:
  (A) 인게임에서 각 DLC 엔딩을 texture export 켜고 띄워 4개 hash 확보 → 完 자리에 완 결 오버레이.
  (B) DLC 팩 CPK의 `Ending_P*.ftx` 직접 교체(hash 불필요·전 사용자 적용). 단 **FTX 재인코더(DXT5+스위즐)
     신규 제작 필요** — 현재 repo엔 decoder `ftx_extract.py`만 있음.
- 사용자 결정: **이번 릴리스 보류.** 상세는 `docs/03-analysis/export-texture-audit-2026-05-20.md` "Ending 完 Handling".
- 참고: sysmsg 엔딩 텍스트(#255 본편·#279~282 DLC)는 이미 "완결"로 번역됨(텍스트는 정상).

## 의도적으로 하지 않는 항목 (사용자 결정)

- **#9-3 무기명 변수 치환**: 원작은 무기명을 런타임 변수(`##（무기）`)로 출력하나 US 엔진이 토큰을
  제거("this blade") → 텍스트/폰트 패치로 복원 불가(eboot 역공학 필요). **진행하지 않음.**

## 추후 필요 시 (현재 미예정)

- `_itemdata`/`sysmsg` 등 비대사 섹션 재번역 (필요해지면 대사와 같은 파이프라인으로).
- 손글씨체 重/隼 폰트 페이지(`font2a/2b` 계열)는 해당 화면 export 시 `auto_font_import` 재실행으로 자동 커버.
- 이슈 #11 후속(선택): UI 에디터에 실제 PIL 라이브렌더 표시(서버 `render_live` 연동)로 WYSIWYG화.
- 이슈 #10 borderline 1건: scemsg#941 "기치를 발휘"(頓智) — 사용자 확인 후 "재치를 발휘" 검토.

---
새 작업·이슈가 생기면 이 파일에 추가하고, 끝나면 success.md로 옮긴다.
