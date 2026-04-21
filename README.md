# Muramasa Rebirth Korean Patch

`Muramasa Rebirth` PS Vita US판(`PCSE00240`)용 한국어 패치 프로젝트다.

이 저장소는 원본 게임 데이터를 포함하지 않는다. 배포물은 Vita3K 기준으로 만든 패치 zip이며, 사용자는 합법적으로 보유한 원본 게임이 필요하다.

## 사용자 안내

- 지원 대상: Vita3K
- 대상 타이틀 ID: `PCSE00240`
- 배포 형식: Vita3K 폴더에 덮어쓰는 zip

패치 zip 내부 구조:

```text
ux0/app/PCSE00240/NinPri.cpk
ux0/app/PCSE00240/NinPriPatch.cpk
```

## 설치 방법

1. Vita3K에 원본 게임과 업데이트를 설치한다.
2. 릴리즈에서 최신 `muramasa-kor-vX.Y.Z-vita3k.zip`을 받는다.
3. Vita3K `pref_path` 기준으로 압축을 풀어 덮어쓴다.

Windows 기본 경로 예시:

```text
C:/Users/<username>/AppData/Roaming/Vita3K/Vita3K
```

덮어써지는 대상:

```text
ux0/app/PCSE00240/NinPri.cpk
ux0/app/PCSE00240/NinPriPatch.cpk
```

## 릴리즈 파일

릴리즈에는 보통 다음 파일이 포함된다.

- `muramasa-kor-vX.Y.Z-vita3k.zip`
- `muramasa-kor-vX.Y.Z-vita3k-manifest.json`
- `muramasa-kor-vX.Y.Z-vita3k-sha256.txt`

## 주의

- 원본 `pkg`, `cpk`, DLC 데이터는 포함하지 않는다.
- 실기용 패키지 설치본이 아니라 Vita3K 덮어쓰기용 배포를 기준으로 한다.
- 문제가 생기면 원본 `NinPri.cpk`, `NinPriPatch.cpk`로 복원하면 된다.

## 기여 및 개발

기여자용 빌드/배포/워크플로 문서는 [CONTRIBUTING.md](CONTRIBUTING.md)를 본다.

