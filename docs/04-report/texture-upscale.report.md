# Report: Texture Upscale to FHD (Local-only)

- Feature: `texture-upscale`
- Period: 2026-05-10 (single session)
- Owner: 하다
- PDCA Phase: Report

## Executive Summary

| 관점 | 내용 |
|------|------|
| **Problem** | Vita3K export 텍스처(273장)가 PS Vita 원본 해상도(256~1024px) 그대로라 FHD 환경에서 흐림. HD 팩(Muramasa Complete 2.0)이 커버 못 하는 자산이 다수. |
| **Solution** | Real-ESRGAN ncnn-vulkan v0.2.5.0 (universal binary) + realesr-animevideov3 모델로 일괄 업스케일. 최대 변 1920px cap. 폰트 hash 4종 + 이미 한글화된 UI 81종 자동 제외. 결과는 `upscaled/` 에 저장하고 .gitignore 로 비배포. |
| **Function UX Effect** | 261장이 FHD 단축에 맞춰 선명화. 알파 채널(RGBA) 보존, 한글 폰트/UI 회귀 0건. 결과물은 본인 PC 로컬에만 존재 → 저작권/용량 리스크 없음. |
| **Core Value** | 한글 패치 본 트랙과 분리된 **개인 화질 트랙** 확립. 새 export 가 추가되면 캐시 스킵으로 증분 업스케일 가능. |

## Results Summary

| 항목 | 수치 |
|---|---|
| Match Rate | 256/256 = **100%** (실패 0건) |
| Items processed | 261장 (sample 5 + batch 256) |
| Skipped (font/한글 UI) | 15장 |
| Files (output) | 261 (`upscaled/` 68 + `upscaled/PCSE00240/` 193) |
| Size delta | source 52MB → output 465MB (≈ 9× — 4x 업스케일 + RGBA + 무손실 PNG 합리 범위) |
| Lines (code) | `tools/upscale_export.py` 156줄 신규 |
| Total time | 1962s ≈ **33분** (sample 45s + batch 1917s) |
| Avg per image | 약 7.5s/장 (1920 cap + LANCZOS 다운샘플 포함) |

## Value Delivered (4-Perspective)

| 관점 | 내용 |
|---|---|
| **Problem** | 한글 패치는 텍스트만 처리해 왔고 UI/이펙트/배경 텍스처는 PS Vita 해상도 그대로라 FHD 화면에서 흐림. HD 팩 외 자산은 사각지대였음. |
| **Solution** | Real-ESRGAN ncnn-vulkan + 1920 cap + skip-list 정책으로 한글 패치를 깨뜨리지 않으면서 사각지대만 선택적 업스케일. .gitignore 로 비배포 강제. |
| **Function UX Effect** | export 폴더 경로 자동 감지 → repo 안 폴더에 깔끔히 보관 → 옵션으로 import 폴더 자동 설치까지. 캐시 덕분에 다음 실행은 추가분만 처리. |
| **Core Value** | (1) 개인 플레이 화질 향상, (2) 한글 패치 회귀 0 (폰트/한글 UI hash 명시 제외), (3) 라이선스/저장소 청결성 (gitignored). |

## Engine Decision

| 후보 | 결정 | 비고 |
|------|------|------|
| **Real-ESRGAN ncnn-vulkan** | ✅ 채택 | 이미 repo의 `tools/batch_upscale.py` 통합 경험. universal binary → arm64 즉시 동작. realesr-animevideov3 모델이 게임/애니 텍스처에 검증됨 |
| Real-CUGAN | 보류 | 신규 통합 비용. 일부 하드 엣지 텍스처에서 과도한 부드럽힘 보고 |
| Topaz/Magnific (클라우드) | 거부 | 비용 + 비공개 데이터 송신 |

## Skip Policy (회귀 방지의 핵심)

```python
skip = set(json.load("tools/.font_hashes.json"))     # 폰트 4종
skip |= {p.name for p in (kr_textures/ui/).glob("*.png")}  # 한글 UI 81종
```

- 폰트 hash: `6706A53E1D94C16E`, `8665CE082D339B33`, `A8E6FDD162258699`, `E690E190AA5C798F`
  - 32px 그리드 기반 cell 좌표가 깨지면 한글 매핑 전체가 망가짐 → 절대 업스케일 금지
- `kr_textures/ui/`: 사용자가 수동 편집한 한글 UI 텍스처들. AI 업스케일이 한글 글리프를 뭉개거나 색상을 변형시킬 수 있어 제외

실제 export 폴더에서 매치된 skip 수: **15장** (276 입력 - 261 처리 = 15 skip)

## Outputs

```
upscaled/
├── *.png                    # 68 (시스템/타이틀 화면 캡처)
└── PCSE00240/
    └── *.png                # 193 (인게임 텍스처)
```

- 모든 출력 RGBA 보존 (Pillow + Real-ESRGAN ncnn-vulkan PNG 출력)
- 1920x1920 / 1920x960 / 1024x512 / 512x256 등 종횡비 유지 + cap
- pngquant 없이 무손실 PNG (Mac 에 바이너리 없으므로 옵션화)

## Verification

- [x] git status: `upscaled/` 안 잡힘 (`git check-ignore` 검증)
- [x] 샘플 5장 (256~1024 입력) 결과 시각 형태 정상 (RGBA, 1920 cap)
- [x] 폰트/한글 UI hash 출력 폴더에 없음 (스킵 로그 확인)
- [x] 256/256 OK, 0 failed
- [ ] (선택) Vita3K import 폴더에 일부 적용 후 게임 실행 확인 — `--install` 플래그로 사용자 재량

## Reuse Pattern (이후 export 추가 시)

```bash
# 새 캡처가 export 폴더에 추가되었을 때
python3 tools/upscale_export.py
# → 캐시 스킵 자동 작동, 신규분만 처리됨

# 결과를 Vita3K 에 즉시 적용하려면
python3 tools/upscale_export.py --install
```

## Out of Scope

- CPK 내부 텍스처 직접 업스케일 (별도 추출 파이프라인 필요)
- 배포 자동화 (라이선스/용량 검토 별도 트랙)
- 모델 비교 벤치 (Real-CUGAN, SwinIR 등) — 현재 Real-ESRGAN 결과 만족
