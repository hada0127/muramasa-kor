"""textures/kr/ui 의 모든 텍스처에 대해 UHD 원본을 textures/originals/ 에 채운다.

우선순위:
  1) HD팩(Muramasa Complete 2.0/PCSE00240/Best)에 있으면 그 UHD 원본 복사
  2) 없으면 Vita export 를 UHD 비율(기본 4x)로 업스케일
     - Real-ESRGAN(temp/realesrgan) 있으면 사용, 없으면 PIL LANCZOS 폴백

HD팩 원본은 외부 다운로드라 리포에 커밋하지 않고 이 스크립트로 재생성 가능.

사용: python tools/populate_uhd_originals.py
"""
import glob
import os
import platform
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
KR_DIR = ROOT / "textures/kr" / "ui"
ORIG = ROOT / "textures" / "originals"
HD_PACK = Path.home() / "Downloads/Muramasa Complete 2.0/PCSE00240/Best"
REALESRGAN = ROOT / "temp" / "realesrgan" / "realesrgan-ncnn-vulkan"
UPSCALE = 4

if platform.system() == "Darwin":
    EXPORT = Path.home() / "Library/Application Support/Vita3K/Vita3K/textures/export/PCSE00240"
else:
    EXPORT = Path("C:/game/vita3k/textures/export/PCSE00240")


def upscale(src, dst, factor):
    """Real-ESRGAN 있으면 사용, 없으면 PIL LANCZOS."""
    if REALESRGAN.exists():
        subprocess.run([str(REALESRGAN), "-i", str(src), "-o", str(dst),
                        "-s", str(factor), "-n", "realesr-animevideov3"],
                       check=True, capture_output=True)
        return "realesrgan"
    im = Image.open(src).convert("RGBA")
    im.resize((im.width * factor, im.height * factor), Image.Resampling.LANCZOS).save(dst)
    return "lanczos"


def main():
    ORIG.mkdir(parents=True, exist_ok=True)
    hashes = sorted(p.stem for p in KR_DIR.glob("*.png"))
    from_hd = upscaled = missing = 0
    for h in hashes:
        dst = ORIG / f"{h}.png"
        hp = HD_PACK / f"{h}.png"
        if hp.exists():
            shutil.copy2(hp, dst)
            from_hd += 1
        else:
            ex = EXPORT / f"{h}.png"
            if ex.exists():
                eng = upscale(ex, dst, UPSCALE)
                upscaled += 1
                print(f"  {h}: HD팩 없음 → {eng} {UPSCALE}x 업스케일")
            else:
                missing += 1
                print(f"  {h}: HD팩·export 모두 없음 (건너뜀)")
    print(f"\nUHD 원본: HD팩 {from_hd} / 업스케일 {upscaled} / 누락 {missing}  (kr {len(hashes)})")


if __name__ == "__main__":
    main()
