"""Build translation notes file for 28 problem textures.
For each texture, output: filename, ja_text per region, suggested ko_translation.
User can edit textures (textures/kr/ui/*.png) directly with this guide.
"""
import json
import io
import sys
from pathlib import Path
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

problems_28 = ["00B61B564A5FD289","0AA74C448087838A","3ECF3B0D2C2907BE","7E0669E71FCD7B64",
    "464E370EF865D0AC","864BD9CBCC496F78","0912E45A567A41C9","4633B92FBA1371F4",
    "4709F3E364671D89","5882EA68BABF3C63","6605F569D9389F9C","7053B8FFC8B89807",
    "7282AD29CF433DA0","7358BEAA2EF5F8A8","8098AD7E2C438C22","31710FB73B2686EF",
    "72165D43344F3190","615858B46587A60E","2611666E71A8181A","A8486C49F76167C3",
    "C8B2975F2A629F4B","C8C4589102431759","C8E42A56480DB818","C84B5B3A51547DF0",
    "C3848C8E5ED70F7A","E9E834DE4BAFDAB2","E9F2EC8557984A58","FFC64B053648525E"]

# Load all data sources
with open('translations/integrated_mapping.json', encoding='utf-8') as f:
    integrated = json.load(f)
with open('translations/codex_analysis.json', encoding='utf-8') as f:
    codex = json.load(f)
with open('translations/detect_v5.json', encoding='utf-8') as f:
    detect = json.load(f)

# Build markdown notes file
md_lines = [
    "# 지명 텍스처 번역 노트",
    "",
    "각 텍스처별로 원본 일본어 텍스트와 권장 한글 번역, detect된 영역 좌표 정보를 정리.",
    "사용자가 Krita 등에서 `textures/kr/ui/<hash>.png`를 편집할 때 참고용.",
    "",
    "## 폰트",
    "- 본문/지명: `fonts/Griun_PolSensibility-Rg.ttf` (그리운 경찰감성체)",
    "",
    "## 영역 종류",
    "- **B(banner)**: 빨간 배너, 검은 일본어 글자, 게임에서 회전되어 표시 (텍스처상 가로로 누워있음)",
    "- **K(box)**: 흰 frame + 검은 fill + 흰 일본어 글자, 국명 박스",
    "- **C(character)**: brush stroke + 큰 흰 일본어 글자, 캐릭터 이름",
    "",
    "## 텍스처별 정보",
    "",
]

for h in problems_28:
    img_path = Path('textures/kr/ui') / f'{h}.png'
    img_size = (0, 0)
    if img_path.exists():
        with Image.open(img_path) as im:
            img_size = im.size

    integ = integrated.get(h, [])
    codex_data = codex.get(h, {})
    codex_regions = codex_data.get('regions', []) if isinstance(codex_data, dict) else []
    det = detect.get(h, {})

    md_lines.append(f"### `{h}.png` ({img_size[0]}×{img_size[1]})")
    md_lines.append("")
    md_lines.append(f"- 원본: `textures/kr/ui/{h}.png` (현재 일본어 원본 상태)")
    md_lines.append(f"- 백업: `textures/place_originals/{h}.png`")
    md_lines.append("")

    # Mapping (mine integrated)
    md_lines.append("**번역 매핑 (kind / 일본어 → 한글)**:")
    md_lines.append("")
    for r in integ:
        kind = r.get('kind', '?')
        ja = r.get('ja', r.get('ja_text', '?'))
        ko = r.get('ko', '?')
        md_lines.append(f"- {kind}: `{ja}` → `{ko}`")
    md_lines.append("")

    # codex extra info (positions)
    if codex_regions:
        md_lines.append("**codex 추가 정보 (위치 힌트, 색상, 방향)**:")
        md_lines.append("")
        md_lines.append("| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |")
        md_lines.append("|---|---|---|---|---|---|")
        for r in codex_regions:
            kind = r.get('kind', '?')
            ja = r.get('ja_text', '?')
            ko = r.get('ko', '?')
            pos = r.get('position_hint', '?')
            color = r.get('color', '?').replace('_bg_', ' bg / ').replace('_text', ' text')
            orient = r.get('orientation', '?').replace('_', ' ')
            md_lines.append(f"| {kind} | {ja} | {ko} | {pos} | {color} | {orient} |")
        md_lines.append("")

    # detect bboxes
    md_lines.append("**자동 detect bbox 좌표 (참고용)**:")
    md_lines.append("")
    if det.get('banners'):
        for b in det['banners']:
            md_lines.append(f"- B{b['idx']}: `{b['bbox']}`")
    if det.get('boxes'):
        for b in det['boxes']:
            md_lines.append(f"- K{b['idx']}: `{b['bbox']}`")
    if det.get('characters'):
        for b in det['characters']:
            md_lines.append(f"- C{b['idx']}: `{b['bbox']}`")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

# Write markdown
out_md = Path('textures/kr/ui/_translation_notes.md')
with open(out_md, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md_lines))
print(f'Saved markdown: {out_md}')

# Also write a concise per-texture txt file for quick reference next to each png
notes_dir = Path('textures/kr/ui/_notes')
notes_dir.mkdir(parents=True, exist_ok=True)
for h in problems_28:
    integ = integrated.get(h, [])
    codex_data = codex.get(h, {})
    codex_regions = codex_data.get('regions', []) if isinstance(codex_data, dict) else []
    det = detect.get(h, {})

    lines = [f'=== {h}.png ===', '']
    lines.append('번역 매핑:')
    for r in integ:
        kind = r.get('kind', '?')
        ja = r.get('ja', r.get('ja_text', '?'))
        ko = r.get('ko', '?')
        lines.append(f'  [{kind}] {ja} -> {ko}')
    lines.append('')
    if codex_regions:
        lines.append('codex 위치 정보:')
        for r in codex_regions:
            kind = r.get('kind', '?')
            ja = r.get('ja_text', '?')
            ko = r.get('ko', '?')
            pos = r.get('position_hint', '?')
            color = r.get('color', '?')
            orient = r.get('orientation', '?')
            lines.append(f'  [{kind}] {ja} -> {ko} | pos={pos} | {color} | {orient}')
        lines.append('')
    lines.append('detect bbox:')
    for b in det.get('banners', []):
        lines.append(f'  B{b["idx"]}: {b["bbox"]}')
    for b in det.get('boxes', []):
        lines.append(f'  K{b["idx"]}: {b["bbox"]}')
    for b in det.get('characters', []):
        lines.append(f'  C{b["idx"]}: {b["bbox"]}')

    txt_p = notes_dir / f'{h}.txt'
    with open(txt_p, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
print(f'Saved per-texture notes: {notes_dir}')

# Build a single JSON file with all data for programmatic use
unified = {}
for h in problems_28:
    unified[h] = {
        'png': f'textures/kr/ui/{h}.png',
        'backup': f'textures/place_originals/{h}.png',
        'integrated_mapping': integrated.get(h, []),
        'codex_analysis': codex.get(h, {}),
        'detect_v5': detect.get(h, {}),
    }
with open('textures/kr/ui/_translation_data.json', 'w', encoding='utf-8') as f:
    json.dump(unified, f, ensure_ascii=False, indent=2)
print(f'Saved unified JSON: textures/kr/ui/_translation_data.json')
