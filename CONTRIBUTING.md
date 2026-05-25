# Contributing

기여자와 유지보수자를 위한 작업 문서다. 최종사용자 안내는 [README.md](README.md)를 본다.

## 먼저 읽기

1. `CLAUDE.md`
2. `.claude/todo.md`
3. `.claude/success.md`
4. `.claude/fail.md`
5. `AGENTS.md`
6. `WORKFLOW.md`

## 기본 원칙

- 저장소 로컬 문맥을 우선한다.
- `wii/` 레퍼런스와 `translations/` 데이터를 먼저 확인한다.
- 사용자 변경을 되돌리지 않는다.
- `.claude/todo.md`, `.claude/success.md`, `.claude/fail.md`는 명시적 요청이 없으면 수정하지 않는다.

## 주요 경로

- 번역 데이터: `translations/`
- 텍스처(단일 트리):
  - `textures/originals/` — Vita3K export 원본 (UI 로컬화 소스)
  - `textures/place_originals/` — 지명 텍스처 원본
  - `textures/kr/ui/`, `textures/kr/font/` — 한글화 출력 (Vita3K import·릴리스 패키징 단위)
- NMS 빌드 출력: `patch_main/`, `patch_patch/`
- 원본 CPK 로컬 보관: `backup/`
- 중간 산출물: `output/`
- 배포 산출물: `dist/`
- 도구 스크립트: `tools/` (웹 UI 텍스처 편집기: `tools/ui_editor/`)

## 개발 빌드

텍스트 패치 기본 파이프라인:

```powershell
python tools/build_patch.py
python tools/cpk_patch.py backup/NinPri.cpk patch_main output/NinPri_final.cpk --append
python tools/cpk_patch.py backup/NinPriPatch.cpk patch_patch output/NinPriPatch_final.cpk --append
```

Vita3K 설치:

```powershell
Copy-Item output/NinPri_final.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPri.cpk -Force
Copy-Item output/NinPriPatch_final.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPriPatch.cpk -Force
```

## 배포 빌드

버전은 `release/version.json`에서 관리한다.

릴리즈 zip은 `textures/kr/ui/*.png`와 `textures/kr/font/*.png`를 `textures/import/PCSE00240/`로 포장한다. 한글 시스템 메시지는 폰트 import가 없으면 깨지므로, 폰트나 문자 매핑을 바꾼 뒤에는 폰트 import를 갱신하고 repo에 동기화해야 한다.

폰트 import 갱신:

```powershell
python tools/hd_font_import.py
New-Item -ItemType Directory -Path textures/kr/font -Force
Copy-Item C:/game/vita3k/textures/import/PCSE00240/6706A53E1D94C16E.png textures/kr/font/6706A53E1D94C16E.png -Force
Copy-Item C:/game/vita3k/textures/import/PCSE00240/8665CE082D339B33.png textures/kr/font/8665CE082D339B33.png -Force
```

UI 텍스처 편집은 웹 기반 편집기를 사용한다(구 Krita `.kra` 워크플로는 폐기됨).

```powershell
python tools/ui_editor/server.py   # http://127.0.0.1:8765
```

편집기에서 region을 수정하면 config(`texture_localize_config.json` / `place_texture_jobs.json`)에 역기록된다. 이후 `python tools/texture_localize.py`(UI) 또는 `python tools/render_place_texture_job.py`(지명)로 `textures/kr/ui/`를 최신 상태로 만든다.

릴리즈 생성:

```powershell
python tools/build_release.py
```

생성물:

- `dist/muramasa-kor-vX.Y.Z-vita3k-patcher.zip`
- `dist/muramasa-kor-vX.Y.Z-vita3k-patcher-manifest.json`
- `dist/muramasa-kor-vX.Y.Z-vita3k-patcher-sha256.txt`

배포 zip에는 완성 CPK를 넣지 않는다. 사용자의 Vita3K 설치본에 있는 원본 CPK를 검증한 뒤 로컬에서 binary patch를 적용하는 패처와 텍스처 import 파일만 포함한다.

최종 사용자용 클린 설치 검증은 기존 Vita3K 상태에 의존하지 않도록 다음 순서로 수행한다.

```powershell
python tools/vita3k_ctrl.py close
Copy-Item backup/NinPri.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPri.cpk -Force
Copy-Item backup/NinPriPatch.cpk C:/game/vita3k/ux0/app/PCSE00240/NinPriPatch.cpk -Force
if (Test-Path C:/game/vita3k/textures/import/PCSE00240) {
  Remove-Item C:/game/vita3k/textures/import/PCSE00240 -Recurse -Force
}
Expand-Archive dist/muramasa-kor-vX.Y.Z-vita3k-patcher.zip C:/tmp/muramasa-release-test -Force
cd C:/tmp/muramasa-release-test
py -3 apply_patch.py --vita3k C:/game/vita3k
```

검증 기준:

- 패처가 `PATCH NinPri.cpk`, `PATCH NinPriPatch.cpk`, `COPY 87/87 texture imports`를 출력한다 (텍스처 개수는 릴리스마다 다를 수 있다).
- 설치된 CPK SHA-256이 manifest의 `target_sha256`과 일치한다.
- Vita3K 설정의 `import-textures`가 켜져 있다.
- 게임을 실행해 시스템 메시지와 메뉴 글자가 깨지지 않는지 확인한다.

## GitHub Release

`dist/` 생성 후:

```powershell
git tag vX.Y.Z
git push origin vX.Y.Z
python tools/publish_release.py --latest
```

`publish_release.py`는 `gh` CLI가 로그인된 환경을 전제로 한다.

## 검증

- 패치 영향을 준 경우 CPK 재생성까지 확인한다.
- 가능하면 Vita3K 자동 검증까지 수행한다.
- 텍스처/UI 작업은 `translations/texture_localize_config.json`과 `textures/kr/ui/`를 함께 확인한다.

## 참고 문서

- 작업 흐름 요약: [WORKFLOW.md](WORKFLOW.md)
- 상세 프로젝트 규칙: [CLAUDE.md](CLAUDE.md)
- Codex 작업 지침: [AGENTS.md](AGENTS.md)
