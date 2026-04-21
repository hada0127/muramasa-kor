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
- NMS 빌드 출력: `patch_main/`, `patch_patch/`
- 원본 CPK 로컬 보관: `backup/`
- 중간 산출물: `output/`
- 배포 산출물: `dist/`
- 도구 스크립트: `tools/`

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

```powershell
python tools/build_release.py
```

생성물:

- `dist/muramasa-kor-vX.Y.Z-vita3k.zip`
- `dist/muramasa-kor-vX.Y.Z-vita3k-manifest.json`
- `dist/muramasa-kor-vX.Y.Z-vita3k-sha256.txt`

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
- 텍스처/UI 작업은 `translations/texture_localize_config.json`과 `kr_textures/ui/`를 함께 확인한다.

## 참고 문서

- 작업 흐름 요약: [WORKFLOW.md](WORKFLOW.md)
- 상세 프로젝트 규칙: [CLAUDE.md](CLAUDE.md)
- Codex 작업 지침: [AGENTS.md](AGENTS.md)
