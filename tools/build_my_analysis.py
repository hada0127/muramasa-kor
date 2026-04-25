"""Build my analysis JSON of 28 problem textures based on prior visual inspection."""
import json
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

my_data = {
    "0AA74C448087838A": [
        {"kind":"box", "ja_text":"相模", "ko":"사가미", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"六国見山 鎌倉墓所", "ko":"로쿠코쿠미야마 가마쿠라 묘소", "color":"red_bg_black_text", "matched":"「相模」六国見山鎌倉墓所"},
    ],
    "3ECF3B0D2C2907BE": [
        {"kind":"box", "ja_text":"武蔵", "ko":"무사시", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"江戸 網釜藩邸 上屋敷", "ko":"에도 아미가마 번저 가미야시키", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"証城寺跡", "ko":"쇼조지 옛터", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"綱釜千代子", "ko":"쓰나가마 치요코", "color":"transparent_bg_white_text"},
    ],
    "7E0669E71FCD7B64": [
        {"kind":"box", "ja_text":"信濃", "ko":"시나노", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"大根芋畑村", "ko":"다이콘 이모하타 마을", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"大根藩馬蕗城", "ko":"다이콘 번 마후키성", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"大根", "ko":"다이콘", "color":"transparent_bg_white_text"},
    ],
    "864BD9CBCC496F78": [
        {"kind":"box", "ja_text":"伊賀", "ko":"이가", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"暗夜城広間の場", "ko":"암야성 넓은 방의 장", "color":"red_bg_black_text", "matched":"「伊賀」暗夜城広間の場"},
    ],
    "0912E45A567A41C9": [
        {"kind":"box", "ja_text":"武蔵", "ko":"무사시", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"新吉原 衣紋坂", "ko":"신요시와라 에몬자카", "color":"red_bg_black_text", "matched":"「武蔵」新吉原衣紋坂"},
    ],
    "5882EA68BABF3C63": [
        {"kind":"box", "ja_text":"何処かの国", "ko":"어딘가의 나라", "color":"black_bg_white_text"},
        {"kind":"box", "ja_text":"武蔵", "ko":"무사시", "color":"black_bg_white_text"},
        {"kind":"box", "ja_text":"美濃", "ko":"미노", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"日本堤 新吉原", "ko":"니혼즈츠미 신요시와라", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"菩提寺 虎姫の墓前", "ko":"보리사 토라히메의 묘 앞", "color":"red_bg_black_text"},
    ],
    "7053B8FFC8B89807": [
        {"kind":"box", "ja_text":"信濃", "ko":"시나노", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"信濃山奥狐のお宿の場", "ko":"시나노 산속 여우의 여인숙 장", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"八幡原 修羅の戦場", "ko":"하치만바라 수라의 전장", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"血狂毘沙門", "ko":"치구루이비샤몬", "color":"transparent_bg_white_text"},
    ],
    "7282AD29CF433DA0": [
        {"kind":"box", "ja_text":"何処かの国", "ko":"어딘가의 나라", "color":"black_bg_white_text"},
        {"kind":"box", "ja_text":"大和", "ko":"야마토", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"峠の茶屋", "ko":"고갯마루 찻집", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"金剛山山頂高天原入口", "ko":"곤고산 산정 다카마가하라 입구", "color":"red_bg_black_text"},
    ],
    "7358BEAA2EF5F8A8": [
        {"kind":"box", "ja_text":"美濃", "ko":"미노", "color":"black_bg_white_text"},
        {"kind":"box", "ja_text":"大和", "ko":"야마토", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"柳生城広間の場", "ko":"야규성 넓은 방의 장", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"鳴神城 大手門前", "ko":"나루카미성 오테문 앞", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"金剛山山頂高天原入口", "ko":"곤고산 산정 다카마가하라 입구", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"大神徳川綱吉", "ko":"이누가미 도쿠가와 쓰나요시", "color":"transparent_bg_white_text"},
    ],
    "8098AD7E2C438C22": [
        {"kind":"box", "ja_text":"大和", "ko":"야마토", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"柳生城広間の場", "ko":"야규성 넓은 방의 장", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"金剛山山腹大仏殿", "ko":"곤고산 산허리 대불전", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"金剛山山頂高天原入口", "ko":"곤고산 산정 다카마가하라 입구", "color":"red_bg_black_text"},
    ],
    "31710FB73B2686EF": [
        {"kind":"box", "ja_text":"地獄", "ko":"지옥", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"地獄八景 大焦熱", "ko":"지옥팔경 대초열", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"地獄八景 等活", "ko":"지옥팔경 등활", "color":"red_bg_black_text"},
    ],
    "615858B46587A60E": [
        {"kind":"box", "ja_text":"美濃", "ko":"미노", "color":"black_bg_white_text"},
        {"kind":"box", "ja_text":"武蔵", "ko":"무사시", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"鳴神城広間の場", "ko":"나루카미성 넓은 방의 장", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"江戸城天守", "ko":"에도성 천수각", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"大神徳川綱吉", "ko":"이누가미 도쿠가와 쓰나요시", "color":"transparent_bg_white_text"},
    ],
    "2611666E71A8181A": [
        {"kind":"box", "ja_text":"武蔵", "ko":"무사시", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"武蔵街道 祠の場", "ko":"무사시 가도 사당의 장", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"天門の先", "ko":"천문의 너머", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"仏界", "ko":"불계", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"大神徳川綱吉", "ko":"이누가미 도쿠가와 쓰나요시", "color":"transparent_bg_white_text"},
    ],
    "A8486C49F76167C3": [
        {"kind":"box", "ja_text":"伊勢", "ko":"이세", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"伊勢天神高天原入口", "ko":"이세 천신 다카마가하라 입구", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"二見浦", "ko":"후타미우라", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"伊勢街道", "ko":"이세 가도", "color":"red_bg_black_text"},
    ],
    "C8C4589102431759": [
        {"kind":"box", "ja_text":"大和", "ko":"야마토", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"奈良善祷寺 金堂", "ko":"나라 젠토지 금당", "color":"red_bg_black_text"},
    ],
    "C84B5B3A51547DF0": [
        {"kind":"box", "ja_text":"遠江", "ko":"토토미", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"秋葉山山腹", "ko":"아키바산 산허리", "color":"red_bg_black_text"},
    ],
    "C3848C8E5ED70F7A": [
        {"kind":"box", "ja_text":"美濃", "ko":"미노", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"伊吹山 不破関", "ko":"이부키산 후와노세키", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"鬼助", "ko":"키스케", "color":"transparent_bg_white_text", "uncertain": True},
    ],
    "E9F2EC8557984A58": [
        {"kind":"box", "ja_text":"駿河", "ko":"스루가", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"三保之松原", "ko":"미호노마츠바라", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"駿府の旅籠", "ko":"슨푸의 여인숙", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"雪之丞", "ko":"유키노조", "color":"transparent_bg_white_text"},
    ],
    "00B61B564A5FD289": [
        {"kind":"unknown", "ja_text":"large 2048x2048 atlas - manual review needed", "ko":"수동 검토 필요", "uncertain": True}
    ],
    "464E370EF865D0AC": [
        {"kind":"unknown", "ja_text":"DLC 大根藩 atlas - manual review needed", "ko":"수동 검토 필요", "uncertain": True}
    ],
    "4633B92FBA1371F4": [
        {"kind":"unknown", "ja_text":"DLC complex atlas - manual review needed", "ko":"수동 검토 필요", "uncertain": True}
    ],
    "4709F3E364671D89": [
        {"kind":"box", "ja_text":"美濃", "ko":"미노", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"中仙道間道", "ko":"나카센도 사잇길", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"鳴神城内座敷", "ko":"나루카미성 내 거실", "color":"red_bg_black_text"},
    ],
    "6605F569D9389F9C": [
        {"kind":"unknown", "ja_text":"large 2048x2048 atlas - manual review needed", "ko":"수동 검토 필요", "uncertain": True}
    ],
    "72165D43344F3190": [
        {"kind":"unknown", "ja_text":"large 2048x2048 atlas - manual review needed", "ko":"수동 검토 필요", "uncertain": True}
    ],
    "C8B2975F2A629F4B": [
        {"kind":"box", "ja_text":"駿河", "ko":"스루가", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"富士山頂龍脈", "ko":"후지산 정상 용맥", "color":"red_bg_black_text"},
    ],
    "C8E42A56480DB818": [
        {"kind":"banner", "ja_text":"江戸 大根藩邸下屋敷", "ko":"에도 다이콘 번저 시모야시키", "color":"red_bg_black_text"},
    ],
    "E9E834DE4BAFDAB2": [
        {"kind":"box", "ja_text":"甲斐", "ko":"카이", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"甲府の街道", "ko":"코후의 가도", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"山の中の一軒家", "ko":"산속의 외딴집", "color":"red_bg_black_text"},
        {"kind":"character", "ja_text":"山姥", "ko":"야마우바", "color":"transparent_bg_white_text"},
    ],
    "FFC64B053648525E": [
        {"kind":"box", "ja_text":"飛騨", "ko":"히다", "color":"black_bg_white_text"},
        {"kind":"banner", "ja_text":"白川郷 白銀ヶ淵 廃れ社", "ko":"시라카와고 시로가네가후치 폐사", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"飛騨街道", "ko":"히다 가도", "color":"red_bg_black_text"},
        {"kind":"banner", "ja_text":"美濃国 境木峠", "ko":"미노국 사카이기 고개", "color":"red_bg_black_text"},
    ],
}

with open('translations/my_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(my_data, f, ensure_ascii=False, indent=2)
print(f'Saved my analysis: {len(my_data)} textures')
uncertain = [h for h, v in my_data.items() if any(r.get('uncertain') for r in v)]
print('Uncertain (need manual review):', uncertain)
