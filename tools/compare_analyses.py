"""Compare my analysis vs codex analysis. Build diff report."""
import json
import io
import sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Re-aggregate codex results (incl. retries)
TMP = Path('C:/Users/taro1/AppData/Local/Temp')
problems_28 = ["00B61B564A5FD289","0AA74C448087838A","3ECF3B0D2C2907BE","7E0669E71FCD7B64",
    "464E370EF865D0AC","864BD9CBCC496F78","0912E45A567A41C9","4633B92FBA1371F4",
    "4709F3E364671D89","5882EA68BABF3C63","6605F569D9389F9C","7053B8FFC8B89807",
    "7282AD29CF433DA0","7358BEAA2EF5F8A8","8098AD7E2C438C22","31710FB73B2686EF",
    "72165D43344F3190","615858B46587A60E","2611666E71A8181A","A8486C49F76167C3",
    "C8B2975F2A629F4B","C8C4589102431759","C8E42A56480DB818","C84B5B3A51547DF0",
    "C3848C8E5ED70F7A","E9E834DE4BAFDAB2","E9F2EC8557984A58","FFC64B053648525E"]

codex = {}
for h in problems_28:
    p = TMP / f'codex_a_{h}.txt'
    if not p.exists() or p.stat().st_size == 0:
        continue
    txt = p.read_text(encoding='utf-8', errors='replace')
    for i in range(len(txt)):
        if txt[i] in '{[':
            try:
                obj, end = json.JSONDecoder().raw_decode(txt[i:])
                if isinstance(obj, (dict, list)) and len(json.dumps(obj)) > 100:
                    codex[h] = obj
                    break
            except:
                continue

with open('translations/codex_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(codex, f, ensure_ascii=False, indent=2)

with open('translations/my_analysis.json', 'r', encoding='utf-8') as f:
    mine = json.load(f)

# Compare
print(f'My analysis: {len(mine)} textures, Codex: {len(codex)} textures\n')

diff_report = {}
for h in problems_28:
    my_regions = mine.get(h, [])
    codex_data = codex.get(h, {})
    codex_regions = codex_data.get('regions', []) if isinstance(codex_data, dict) else []

    my_ja = sorted(r.get('ja_text', '') for r in my_regions if r.get('ja_text'))
    codex_ja = sorted(r.get('ja_text', '') for r in codex_regions if r.get('ja_text'))

    diff_report[h] = {
        'my_count': len(my_regions),
        'codex_count': len(codex_regions),
        'my_ja': my_ja,
        'codex_ja': codex_ja,
    }

print('='*100)
print('DIFF REPORT')
print('='*100)
for h, d in diff_report.items():
    print(f'\n{h} (my:{d["my_count"]} codex:{d["codex_count"]})')
    my_set = set(d['my_ja'])
    codex_set = set(d['codex_ja'])
    common = my_set & codex_set
    only_mine = my_set - codex_set
    only_codex = codex_set - my_set
    if common:
        print(f'  AGREE ({len(common)}): {sorted(common)}')
    if only_mine:
        print(f'  ONLY MINE ({len(only_mine)}): {sorted(only_mine)}')
    if only_codex:
        print(f'  ONLY CODEX ({len(only_codex)}): {sorted(only_codex)}')

# Save diff report
with open('translations/analysis_diff.json', 'w', encoding='utf-8') as f:
    json.dump(diff_report, f, ensure_ascii=False, indent=2)
print('\nSaved diff to translations/analysis_diff.json')
