# Plan: Texture Upscale to FHD (Local-only)

- Feature: `texture-upscale`
- Created: 2026-05-10
- Owner: 하다
- PDCA Phase: Plan

## Executive Summary

| 관점 | 내용 |
|------|------|
| **Problem** | Vita3K 가 export 한 게임 텍스처는 PS Vita 원본 해상도(대부분 256~1024px) 그대로라 FHD(1920×1080) 출력 환경에서 흐릿하게 표시됨. Muramasa Complete 2.0 HD 팩이 있지만 export 텍스처(폰트·UI·일부 인게임 에셋)는 그 범위 밖이라 흐려 보이는 자산이 남아 있음. |
| **Solution** | Vita3K export 폴더의 모든 PNG를 Real-ESRGAN ncnn-vulkan으로 일괄 업스케일하여 최대 변 1920px 로 리사이즈. 결과물은 배포 안 함(라이선스/용량) — repo 내 `upscaled/` 에 저장하고 `.gitignore` 로 제외. 이미 한글화된 UI 텍스처(`kr_textures/ui/`) 와 한글 글리프가 들어간 폰트 hash 는 자동 제외. |
| **Function UX Effect** | export 된 273개 텍스처 중 폰트/한글 UI 제외분이 FHD에서 선명하게 표시. 사용자 본인 PC에서만 적용(import 폴더 수동 복사 권장 절차 포함). |
| **Core Value** | 한글 패치 외에 **개인 플레이 품질** 향상 트랙을 분리. 배포 패치(repo)에는 영향 없음 → 저작권/용량 리스크 없이 로컬 화질 개선. |

## Context Anchor

| 항목 | 내용 |
|------|------|
| **WHY** | HD 팩(Muramasa Complete 2.0)이 커버하지 못하는 export 텍스처에 대해 개인 플레이 품질을 끌어올린다. 동시에 결과물의 비배포 원칙(저작권 + 4GB+ 용량)을 코드/repo 구조로 강제. |
| **WHO** | 하다(패처) 본인. 다른 협업자/플레이어에게는 절차만 공개. |
| **RISK** | (1) 폰트 텍스처가 업스케일되면 한글 매핑 cell 좌표가 흐트러져 글자 깨짐 → 폰트 hash 자동 제외 필수. (2) 이미 수동 편집된 `kr_textures/ui/` 텍스처를 덮어쓰면 한글 UI 손상 → 같은 hash 자동 제외. (3) 알파 전용 텍스처가 RGB 보정으로 손상 가능성 → Real-ESRGAN 의 RGBA 처리 검증 필요. |
| **SUCCESS** | (1) 모든 비제외 텍스처가 max 변 1920px 로 출력. (2) `upscaled/` 폴더가 git status 에 안 잡힘. (3) Vita3K import 로 적용 시 게임이 정상 실행되고 UI 한글/폰트가 깨지지 않음. |
| **SCOPE** | Vita3K `~/Library/Application Support/Vita3K/Vita3K/textures/export/` 의 PNG 만. DLC CPK 내부 텍스처(별도 추출 불가) 는 out-of-scope. 배포 자동화도 out-of-scope. |

## 1. Problem Description

### 1.1 증상
- HD 팩 적용 후에도 일부 export 텍스처(특히 UI 오버레이/이펙트/메뉴 일부)가 FHD 화면에서 픽셀 보임.
- export 폴더에 273개 PNG 가 누적되어 있는데 본인 화면에서 흐릿하게 출력.

### 1.2 영향 범위
- export/PCSE00240/ — 203개 (DLC 포함 인게임 텍스처)
- export/ 루트 — 73개 (시스템/타이틀 화면 부근에서 캡처된 텍스처)

## 2. 제외 정책 (필수)

| 카테고리 | 제외 사유 | 식별 방법 |
|----------|----------|----------|
| 폰트 텍스처 | 32px 그리드 + 셀 좌표 의존 → 업스케일 시 한글 깨짐 | `auto_font_import.py` 의 `.font_hashes.json`, 알려진 hash (`6706A53E1D94C16E`, `8665CE082D339B33`) |
| 한글 UI 텍스처 | `kr_textures/ui/` 에 수동 편집본 존재 | 파일명(hash.png) 이 `kr_textures/ui/` 에 있으면 skip |
| 1024 미만 작은 ASCII 폰트/유틸 | font.png 류 | `batch_upscale.py` 기존 skip 패턴 유지 |

## 3. 엔진 선택 근거

| 후보 | 결정 | 이유 |
|------|------|------|
| **Real-ESRGAN ncnn-vulkan** ✅ | 채택 | 이미 repo의 `tools/batch_upscale.py` 통합. macOS arm64 universal binary 존재. realesr-animevideov3 모델이 게임/애니 텍스처에 검증됨 |
| Real-CUGAN | 보류 | 신규 통합 비용 + 일부 하드 엣지 텍스처에서 과도한 부드럽힘 보고 사례 |
| 클라우드 (Topaz/Magnific) | 거부 | 273장 X 비용 + 비공개 데이터 송신 |

## 4. 출력 정책

- 최대 변 1920px (FHD 단축 대응) → 1024 → 1920 (≈2x), 512 → 1920 (≈4x → 1920 cap), 256 → 1024 (4x cap)
- 알파 채널 보존 (Real-ESRGAN ncnn-vulkan 의 `-f png` 는 RGBA 유지)
- pngquant 압축은 옵션 (Mac 에 바이너리 없으면 스킵)
- 출력 경로: `upscaled/PCSE00240/<hash>.png` (export 의 PCSE00240/ 구조 유지) + `upscaled/_root/<hash>.png` (export 루트 텍스처)

## 5. .gitignore 정책

- 신규 라인 추가: `upscaled/` (repo root 명시적 등록)
- `temp/` 와 별개로 유지: 의도가 다름 (temp = 임시 작업, upscaled = 영구 보관 로컬 자산)

## 6. 검증 방법

1. 샘플 5장 (캐릭터 1, UI 1, 배경 1, 폰트 1[skip 검증용], 알파 1) 업스케일 결과 시각 확인
2. 폰트 hash 가 출력에 포함 안 되는지 로그 확인
3. `upscaled/` 가 `git status` 에 안 잡히는지 확인
4. (선택) Vita3K import 폴더에 일부 복사 후 게임 실행하여 UI/폰트 회귀 없음 확인 — Mac 에서는 import 경로 = `~/Library/Application Support/Vita3K/Vita3K/textures/import/PCSE00240/`

## 7. 마일스톤

- [x] Plan 문서 (이 파일)
- [ ] Real-ESRGAN macOS 바이너리 확보
- [ ] batch_upscale.py Mac/1920 적응
- [ ] upscaled/ + .gitignore
- [ ] 샘플 5장 검증
- [ ] 전체 배치 실행
- [ ] Report 작성

## 8. Out of Scope (명시)

- 배포용 통합 (HD 팩처럼 CPK/import 자동 설치) — 라이선스 검토 필요
- 다른 게임으로 일반화
- AI 모델 비교 벤치 (Real-ESRGAN 채택으로 진행)
