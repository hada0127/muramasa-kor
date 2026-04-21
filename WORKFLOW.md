# Workflow

이 문서는 이 저장소에서 자주 반복하는 작업 절차만 빠르게 확인하기 위한 실행 요약이다. 세부 규칙과 배경은 `CLAUDE.md`, Codex용 동작 규칙은 `AGENTS.md`를 따른다.

## 시작 전

1. `CLAUDE.md` 읽기
2. `.claude/todo.md`, `.claude/success.md`, `.claude/fail.md` 읽기
3. `git status --short` 확인
4. 관련 문서 확인
   - 번역/용어: `wii/`, `translations/`
   - UI 텍스처: `translations/texture_localize_config.json`, `kr_textures/ui/`
   - 분석/회귀 이력: `docs/03-analysis/`

## 텍스트 패치 작업

1. 번역 데이터 수정
   - 주 대상: `translations/*.json`
2. 빌드
   ```powershell
   python tools/build_patch.py
   ```
3. CPK 생성
   ```powershell
   python tools/cpk_patch.py backup/NinPri.cpk patch_main output/NinPri_final.cpk --append
   python tools/cpk_patch.py backup/NinPriPatch.cpk patch_patch output/NinPriPatch_final.cpk --append
   ```
4. 배포용 zip 생성
   ```powershell
   python tools/build_release.py
   ```
5. 필요 시 설치
   ```powershell
   Copy-Item output/NinPri_final.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPri.cpk -Force
   Copy-Item output/NinPriPatch_final.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPriPatch.cpk -Force
   ```
6. 검증
   - `NinPriPatch.cpk`가 대사/시스템 메시지를 우선 덮는 구조를 항상 고려
   - 가능하면 Vita3K 자동 실행까지 포함해 확인

## 릴리즈 배포

1. `release/version.json` 갱신
2. `python tools/build_release.py`
3. Git 태그 생성
   ```powershell
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
4. GitHub Release 업로드
   ```powershell
   python tools/publish_release.py --latest
   ```

## UI 텍스처 작업

1. 대상 확인
   - 원본/참고: `textures/`, `textures/work/`
   - 결과물: `kr_textures/ui/`
   - 설정: `translations/texture_localize_config.json`
2. 자동 생성 작업이면
   ```powershell
   python tools/texture_localize.py
   ```
3. 특정 텍스처만 작업하면
   ```powershell
   python tools/texture_localize.py <HASH_PREFIX>
   ```
4. 미리보기 확인이 필요하면
   ```powershell
   python tools/texture_localize.py --preview
   ```
5. 수동 편집 텍스처는 기존 `kr_textures/ui/` 결과를 우선 기준으로 취급

## 폰트/텍스처 import 작업

1. 일반 폰트 import 생성
   ```powershell
   python tools/auto_font_import.py
   ```
2. HD 폰트/텍스처 반영
   ```powershell
   python tools/hd_font_import.py
   ```
3. 주의
   - ASCII 페이지는 건드리지 않기
   - KANJI 페이지에만 한글 오버레이
   - 알파 전용 텍스처 여부 확인

## Vita3K 작업

1. 상태 확인
   ```powershell
   python tools/vita3k_ctrl.py status
   ```
2. 안전 종료
   ```powershell
   python tools/vita3k_ctrl.py close
   ```
3. 실행
   ```powershell
   python tools/vita3k_ctrl.py launch
   ```
4. 게임 자동 실행 보조
   ```powershell
   python tools/vita3k_run_game.py
   ```
5. 금지 사항
   - `taskkill /f /im Vita3K.exe` 사용 금지
   - `-r PCSE00240` 방식 실행 금지

## 스크린샷/이미지 확인

1. 큰 이미지는 바로 읽지 말고 먼저 축소본 생성
2. 축소본 저장 위치: `temp/preview/`
3. 원본 수치 분석이 필요하면 PIL/numpy 사용, 시각 확인은 축소본 사용

## 작업 종료 전

1. `git status --short` 재확인
2. 관련 빌드/생성 스크립트 실행 여부 점검
3. 가능하면 Vita3K 검증 수행
4. 검증을 못 했으면 이유를 명시
5. 로그 파일 `.claude/*.md`는 명시적으로 요구받은 경우만 수정
