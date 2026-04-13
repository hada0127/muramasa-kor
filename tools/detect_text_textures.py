"""텍스트가 포함된 텍스처 자동 감지

흰색/밝은 텍스트가 검은 배경 위에 있는 텍스처를 감지한다.
폰트 텍스처(32px 그리드)는 제외. 배경/스프라이트도 필터링.
"""

import os
from pathlib import Path
from PIL import Image
import numpy as np

EXPORT_DIR = Path("C:/game/vita3k/textures/export/PCSE00240")
OUTPUT_DIR = Path("output/texture_survey")

# 이미 알려진 폰트 해시 (제외)
FONT_HASHES = {
    "882CCAF6763B8B59", "09498223CD6E047B",
    "6706A53E1D94C16E", "8665CE082D339B33",
    "E690E190AA5C798F", "87B72F6DB3C3FBDC",
}


def analyze_texture(path):
    """텍스처를 분석해서 텍스트 포함 가능성을 점수로 반환"""
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    w, h = img.size

    result = {
        "hash": path.stem,
        "size": f"{w}x{h}",
        "score": 0,
        "reasons": [],
    }

    r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]

    # 1. 밝은 픽셀 비율 (흰색 텍스트 감지)
    visible = a > 30
    if visible.sum() == 0:
        return result

    bright = (r > 180) & (g > 180) & (b > 180) & visible
    bright_ratio = bright.sum() / visible.sum()

    # 2. 어두운 픽셀 비율
    dark = (r < 50) & (g < 50) & (b < 50) & visible
    dark_ratio = dark.sum() / visible.sum()

    # 3. 텍스트 패턴: 밝은 픽셀이 적당히 있고 (5-60%) 어두운 배경이 많을 때
    if 0.02 < bright_ratio < 0.6 and dark_ratio > 0.3:
        result["score"] += 30
        result["reasons"].append(f"bright_on_dark({bright_ratio:.1%}/{dark_ratio:.1%})")

    # 4. 높은 대비 영역 검사 (텍스트 경계)
    gray = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.float32)
    # horizontal gradient
    h_grad = np.abs(np.diff(gray, axis=1))
    # vertical gradient
    v_grad = np.abs(np.diff(gray, axis=0))
    avg_grad = (h_grad.mean() + v_grad.mean()) / 2

    if avg_grad > 15:
        result["score"] += 20
        result["reasons"].append(f"high_contrast({avg_grad:.1f})")

    # 5. 투명 영역이 많으면 스프라이트 아틀라스 (텍스트 가능성 높음)
    alpha_zero = (a < 10).sum() / (w * h)
    if 0.2 < alpha_zero < 0.85:
        result["score"] += 10
        result["reasons"].append(f"partial_alpha({alpha_zero:.1%})")

    # 6. 색상 다양성이 낮으면 텍스트 가능성 (흑백 위주)
    if visible.sum() > 100:
        vis_r = r[visible]
        vis_g = g[visible]
        vis_b = b[visible]
        color_std = (vis_r.std() + vis_g.std() + vis_b.std()) / 3
        if color_std < 60:
            result["score"] += 15
            result["reasons"].append(f"low_color_var({color_std:.0f})")

    # 7. 작은 크기(64x64 이하)는 아이콘/효과, 점수 감소
    if w <= 64 or h <= 64:
        result["score"] -= 20
        result["reasons"].append("small_texture")

    # 8. 정사각형 1024x1024는 UI atlas 가능성
    if w == 1024 and h == 1024:
        result["score"] += 10
        result["reasons"].append("1024x1024_atlas")

    return result


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pngs = sorted(EXPORT_DIR.glob("*.png"))

    results = []
    for p in pngs:
        if p.stem[:16] in FONT_HASHES:
            continue
        try:
            r = analyze_texture(p)
            results.append(r)
        except Exception as e:
            print(f"ERR {p.stem}: {e}")

    # 점수순 정렬
    results.sort(key=lambda x: x["score"], reverse=True)

    # 결과 출력
    print(f"\n{'='*80}")
    print(f"텍스트 포함 가능성 높은 텍스처 (score >= 30)")
    print(f"{'='*80}")
    for r in results:
        if r["score"] >= 30:
            print(f"  {r['score']:3d}  {r['hash']}  {r['size']:>10s}  {', '.join(r['reasons'])}")

    print(f"\n중간 점수 (20-29):")
    for r in results:
        if 20 <= r["score"] < 30:
            print(f"  {r['score']:3d}  {r['hash']}  {r['size']:>10s}  {', '.join(r['reasons'])}")

    # 고득점 텍스처 contact sheet
    top = [r for r in results if r["score"] >= 30]
    if top:
        cols = 4
        rows_ct = (len(top) + cols - 1) // cols
        thumb = 256
        label_h = 30
        cw = thumb
        ch = thumb + label_h
        margin = 4

        sheet = Image.new("RGBA", (cols*(cw+margin)+margin, rows_ct*(ch+margin)+margin), (32,32,32,255))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(sheet)

        for i, r in enumerate(top):
            col = i % cols
            row = i // cols
            x = margin + col*(cw+margin)
            y = margin + row*(ch+margin)

            try:
                img = Image.open(EXPORT_DIR / f"{r['hash']}.png")
                tw, th = img.size
                scale = min(thumb/tw, thumb/th)
                nw, nh = int(tw*scale), int(th*scale)
                img = img.resize((nw, nh), Image.LANCZOS)
                px = x + (thumb-nw)//2
                py = y + (thumb-nh)//2
                draw.rectangle([x,y,x+thumb,y+thumb], fill=(0,0,0,255))
                if img.mode == "RGBA":
                    sheet.paste(img, (px,py), img)
                else:
                    sheet.paste(img, (px,py))
            except:
                pass

            draw.text((x+2, y+thumb+2), f"{r['hash'][:16]}", fill=(200,200,200))
            draw.text((x+2, y+thumb+14), f"s={r['score']} {r['size']}", fill=(150,150,150))

        out = OUTPUT_DIR / "text_candidates.png"
        sheet.save(str(out))
        print(f"\nCandidate sheet: {out}")


if __name__ == "__main__":
    main()
