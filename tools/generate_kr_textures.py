"""한글 텍스처 일괄 생성 도구

모든 UI/메뉴 텍스처를 한글화하여 Vita3K import 폴더에 생성한다.

사용법:
  python tools/generate_kr_textures.py              # 전체 빌드
  python tools/generate_kr_textures.py --preview     # 미리보기만
  python tools/generate_kr_textures.py 1823D39C      # 특정 해시만
"""

import sys
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

PROJECT_DIR = Path(__file__).parent.parent
BACKUP_DIR = PROJECT_DIR / "backup" / "texture_imports"
EXPORT_DIR = Path("C:/game/vita3k/textures/export/PCSE00240")
IMPORT_DIR = Path("C:/game/vita3k/textures/import/PCSE00240")
PREVIEW_DIR = PROJECT_DIR / "output" / "texture_preview"
FONT_PATH = str(PROJECT_DIR / "fonts" / "Griun_PolSensibility-Rg.ttf")


# === 유틸리티 ===

def backup_original(hash_id):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bp = BACKUP_DIR / f"{hash_id}_original.png"
    if not bp.exists():
        src = EXPORT_DIR / f"{hash_id}.png"
        if src.exists():
            shutil.copy2(str(src), str(bp))
    return bp

def load_original(hash_id):
    bp = backup_original(hash_id)
    for p in [bp, EXPORT_DIR / f"{hash_id}.png"]:
        if p.exists():
            return Image.open(str(p)).convert("RGBA")
    return None

def render_text(text, font_size, color=(255,255,255,255), bold=False, vertical=False):
    font = ImageFont.truetype(FONT_PATH, font_size)
    if vertical:
        chars = []
        for ch in text:
            bbox = font.getbbox(ch)
            cw, ch_h = bbox[2]-bbox[0]+2, bbox[3]-bbox[1]+2
            ci = Image.new("RGBA", (cw, ch_h), (0,0,0,0))
            ImageDraw.Draw(ci).text((-bbox[0]+1, -bbox[1]+1), ch, font=font, fill=color)
            chars.append(ci)
        tw = max(c.width for c in chars)
        th = sum(c.height for c in chars) + len(chars) - 1
        out = Image.new("RGBA", (tw, th), (0,0,0,0))
        y = 0
        for ci in chars:
            out.paste(ci, ((tw-ci.width)//2, y), ci)
            y += ci.height + 1
        return out

    bbox = font.getbbox(text)
    tw, th = bbox[2]-bbox[0]+4, bbox[3]-bbox[1]+4
    out = Image.new("RGBA", (tw, th), (0,0,0,0))
    d = ImageDraw.Draw(out)
    if bold:
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                d.text((-bbox[0]+2+dx, -bbox[1]+2+dy), text, font=font, fill=color)
    else:
        d.text((-bbox[0]+2, -bbox[1]+2), text, font=font, fill=color)
    return out

def clear_region(img, x, y, w, h):
    arr = np.array(img)
    y2 = min(y+h, arr.shape[0])
    x2 = min(x+w, arr.shape[1])
    arr[y:y2, x:x2, 3] = 0
    return Image.fromarray(arr)

def paste_at(img, text_img, x, y, fit_w=None, fit_h=None):
    if fit_w and text_img.width > fit_w:
        r = fit_w / text_img.width
        text_img = text_img.resize((fit_w, max(1,int(text_img.height*r))), Image.LANCZOS)
    if fit_h and text_img.height > fit_h:
        r = fit_h / text_img.height
        text_img = text_img.resize((max(1,int(text_img.width*r)), fit_h), Image.LANCZOS)
    img.paste(text_img, (x, y), text_img)

def save_result(img, hash_id, preview=False):
    if preview:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        bg = Image.new("RGBA", img.size, (0,0,0,255))
        Image.alpha_composite(bg, img).save(str(PREVIEW_DIR / f"{hash_id}_kr.png"))
        print(f"  PREVIEW → {PREVIEW_DIR / f'{hash_id}_kr.png'}")
    else:
        IMPORT_DIR.mkdir(parents=True, exist_ok=True)
        img.save(str(IMPORT_DIR / f"{hash_id}.png"))
        print(f"  IMPORT → {IMPORT_DIR / f'{hash_id}.png'}")


# =============================================================================
# 1823D39C - 지역명 (256x128) alpha_text
# =============================================================================
def generate_1823D39C(preview=False):
    hash_id = "1823D39C0279886B"
    print(f"[{hash_id}] 지역명...")
    orig = load_original(hash_id)
    if not orig: return print("  SKIP")

    # 전체 클리어하고 새로 렌더링
    result = orig.copy()
    result = clear_region(result, 0, 0, 256, 128)
    c = (255,255,255,255)

    # 수평 (상단 3줄)
    for y, text, sz in [(1,"야마시로",15), (19,"시나노",15), (37,"무사시",15)]:
        paste_at(result, render_text(text, sz, c, bold=True), 1, y)

    # 수직 (우측 열들) - 각 열은 약 16px 폭, 위에서 아래로
    vcols = [
        (76,  37, "사가미", 11),
        (96,  1,  "스루가", 11),
        (96,  55, "카와치", 11),
        (114, 1,  "미노",   11),
        (114, 35, "오와리", 11),
        (131, 1,  "이즈",   11),
        (131, 35, "카이",   11),
        (131, 70, "이세",   11),
        (148, 1,  "도토미", 11),
    ]
    for x, y, text, sz in vcols:
        paste_at(result, render_text(text, sz, c, bold=True, vertical=True), x, y)

    # 하단 수직
    for x, y, text, sz in [(1,55,"야마토",11), (20,55,"미카와",11), (38,55,"오미",11)]:
        paste_at(result, render_text(text, sz, c, bold=True, vertical=True), x, y)

    save_result(result, hash_id, preview)


# =============================================================================
# A3BE57CE - 스토리/DLC 제목 (1024x1024) alpha_text
# 한자 보존, 영문 부제만 한글로 교체
# =============================================================================
def generate_A3BE57CE(preview=False):
    hash_id = "A3BE57CE9854B5CC"
    print(f"[{hash_id}] 스토리 제목...")
    orig = load_original(hash_id)
    if not orig: return print("  SKIP")
    result = orig.copy()
    c = (255,255,255,255)

    # 실측 좌표 기반 영문 교체
    regions = [
        # (clear_x, clear_y, clear_w, clear_h, text, size, tx, ty)
        # "The Story of" + "Legend" (y=178-240, x=398-690)
        (398, 178, 300, 62, "이야기", 26, 420, 190),
        # "Legend" is part of the same region or slightly below
        # Additional labels at y=240-270, x=525-675
        (525, 238, 155, 35, "전설", 22, 545, 245),

        # Labels in the second kanji row (y=400-470, x=380-700)
        (380, 398, 325, 72, "대소동", 28, 440, 430),

        # "A Spirited Seven Nights' Haunting" (y=470-522, x=0-700)
        (0, 468, 710, 56, "칠야의 괴담", 32, 100, 478),
        # "Fishy Tales of the Nekomata" (y=524-580, x=0-700)
        (0, 522, 710, 60, "화묘 괴이담", 32, 100, 538),

        # "Hell's Where the Heart Is" (y=720-780, x=0-500)
        (0, 718, 510, 62, "내세의 안식처", 30, 30, 730),
        # "A Cause to Daikon For[aka]" (y=776-835, x=0-500)
        (0, 774, 510, 62, "대의를 위한 무", 30, 30, 790),

        # Bottom section: "White Serpent" + "Ninja Scroll" + "Demon Blade" etc.
        # Clear entire bottom English area (y=870-1000, x=0-600)
        (0, 870, 610, 60, "백사전", 24, 140, 880),
        (160, 870, 200, 60, "인법첩", 24, 310, 880),
        # "Demon Blade" + "Pandemonium" + "Oboro Blade" (y=920-1000)
        (0, 920, 610, 80, "", 0, 0, 0),  # clear only
    ]

    # Additional specific items in the bottom cleared area
    bottom_items = [
        (20, 930, "요도", 22),
        (160, 930, "백귀야행", 22),
        (340, 960, "오보로 무라마사", 20),
    ]

    for cx, cy, cw, ch, text, sz, tx, ty in regions:
        result = clear_region(result, cx, cy, cw, ch)
        if text and sz > 0:
            ti = render_text(text, sz, c, bold=True)
            paste_at(result, ti, tx, ty)

    for tx, ty, text, sz in bottom_items:
        ti = render_text(text, sz, c, bold=True)
        paste_at(result, ti, tx, ty)

    save_result(result, hash_id, preview)


# =============================================================================
# 74EEEC23 - 스토리 제목+라벨 (1024x512) alpha_text
# 한자 보존, 영문 라벨만 교체
# =============================================================================
def generate_74EEEC23(preview=False):
    hash_id = "74EEEC230BEE120C"
    print(f"[{hash_id}] 스토리 라벨...")
    orig = load_original(hash_id)
    if not orig: return print("  SKIP")
    result = orig.copy()
    c = (255,255,255,255)

    # 실측 좌표:
    # Revolution: x=300-599, y=1-79
    # Demon Cat: x=1-199, y=50-119
    # Wild Child: x=2-199, y=100-169
    # Title: x=600-764, y=390-459
    # Kisuke: x=500-694, y=440-489
    regions = [
        (300, 0, 310, 82, "변혁", 40, 350, 15),
        (0, 48, 205, 75, "화묘", 35, 20, 60),
        (0, 98, 205, 75, "야생아", 35, 20, 110),
        (598, 388, 170, 75, "제목", 35, 620, 400),
        (498, 438, 200, 55, "키스케", 28, 520, 448),
    ]

    for cx, cy, cw, ch, text, sz, tx, ty in regions:
        result = clear_region(result, cx, cy, cw, ch)
        ti = render_text(text, sz, c, bold=True)
        paste_at(result, ti, tx, ty)

    save_result(result, hash_id, preview)


# =============================================================================
# DF66CADD - 메인 UI (512x512) alpha_text
# 좌측 x=0-148은 한자 캘리그래피 → 보존
# 우측 x=148-511은 영문 UI 텍스트 → 전체 클리어 후 한글 렌더링
# =============================================================================
def generate_DF66CADD(preview=False):
    hash_id = "DF66CADDABE022E3"
    print(f"[{hash_id}] 메인 UI...")
    orig = load_original(hash_id)
    if not orig: return print("  SKIP")
    result = orig.copy()
    c = (255,255,255,255)

    # 우측 영문 영역 전체 클리어 (한자 영역 보존)
    result = clear_region(result, 148, 0, 364, 512)

    # UI 텍스트를 행별로 렌더링 (각 행 높이 약 20px)
    # 실측: 영문 텍스트는 x=150-510에 밀집, 행 높이 ~16-20px
    sz = 13  # 작은 폰트 (밀집 배치)
    row_h = 18

    ui_items = [
        # y, x, text (원본 배치 순서 근사)
        # Row 0-5: 게임 기본 메뉴
        (2,  150, "불러오기"),  (2, 240, "새 게임"),  (2, 320, "랭크"),
        (20, 150, "계속하기"),  (20, 240, "갤러리"),   (20, 320, "크레딧"),
        (38, 150, "타이틀"),    (38, 240, "종료"),

        # 전투/결과 관련
        (60, 150, "이기다"),  (60, 240, "싸우다"),    (60, 320, "도망"),
        (78, 150, "공격"),    (78, 220, "특기"),      (78, 290, "아이템"),  (78, 370, "도감"),
        (96, 150, "평가"),    (96, 230, "랭크"),      (96, 300, "기록"),
        (114, 150, "로드"),    (114, 220, "세이브"),    (114, 300, "설정"),

        # 메뉴 항목
        (136, 150, "무기"),    (136, 210, "방어구"),    (136, 290, "아이템"),  (136, 370, "장신구"),
        (154, 150, "확인"),    (154, 220, "취소"),     (154, 290, "돌아가기"),
        (172, 150, "기본값"),  (172, 230, "도감"),     (172, 310, "플레이"),   (172, 390, "요리"),
        (190, 150, "조작법"),  (190, 240, "기술"),     (190, 310, "가게"),     (190, 380, "대화"),

        # 승리/전투
        (212, 150, "승리!"),   (212, 230, "전투!"),
        (230, 150, "재시도"),  (230, 230, "이동"),     (230, 300, "경험치"),

        # 시스템
        (252, 150, "설정"),    (252, 220, "소리"),     (252, 290, "밝기"),
        (270, 150, "예"),      (270, 190, "아니오"),   (270, 260, "확인"),    (270, 330, "뒤로"),

        # 상태/정보
        (292, 150, "상태"),    (292, 220, "능력"),     (292, 290, "장비"),    (292, 370, "스킬"),
        (310, 150, "저장"),    (310, 220, "불러오기"), (310, 310, "시스템"),
        (328, 150, "진행"),    (328, 220, "임무"),     (328, 290, "지도"),

        # 아이템/요리
        (350, 150, "재료"),    (350, 220, "요리"),     (350, 290, "도구"),    (350, 370, "소지품"),
        (368, 150, "레시피"),  (368, 230, "조리"),     (368, 310, "시식"),
        (386, 150, "자동"),    (386, 220, "수동"),     (386, 290, "선택"),
        (404, 150, "구입"),    (404, 220, "판매"),     (404, 290, "장착"),    (404, 370, "해제"),
        (422, 150, "사용"),    (422, 220, "버리기"),   (422, 300, "정보"),
        (440, 150, "노래"),    (440, 220, "가을"),     (440, 290, "봄"),      (440, 360, "여름"),  (440, 420, "겨울"),
        (458, 150, "전체"),    (458, 220, "완료"),     (458, 290, "미완료"),
        (476, 150, "단계"),    (476, 220, "HP"),       (476, 270, "공격력"),  (476, 340, "방어력"),
        (494, 150, "이름"),    (494, 220, "시간"),     (494, 290, "점수"),    (494, 360, "최고"),
    ]

    for y, x, text in ui_items:
        ti = render_text(text, sz, c, bold=True)
        paste_at(result, ti, x, y)

    save_result(result, hash_id, preview)


# =============================================================================
# 7DC6CF5A - 아이템 이름 (512x512)
# 좌측은 줄무늬 텍스처 보존, 우측 텍스트만 교체
# =============================================================================
def generate_7DC6CF5A(preview=False):
    hash_id = "7DC6CF5A87DB1312"
    print(f"[{hash_id}] 아이템 이름...")
    orig = load_original(hash_id)
    if not orig: return print("  SKIP")
    result = orig.copy()
    c = (255,255,255,255)

    # 텍스트 영역 클리어 (x=155-511, y=0-500)
    # 좌측 줄무늬 영역(x=0-154) 보존
    result = clear_region(result, 155, 0, 357, 510)
    # 좌하단 텍스트도 클리어
    result = clear_region(result, 0, 195, 155, 315)

    sz = 12
    row_h = 21

    # 아이템 이름 목록 (행별 배치)
    items = [
        # (y, [(x, text), ...])
        (1,   [(158,"근력 증강"), (258,"능력 증강"), (358,"현자의 영약"), (458,"연막탄")]),
        (22,  [(258,"용의 영약"), (358,"이가라시 숫돌"), (458,"숫돌")]),
        (43,  [(258,"이요 숫돌"), (358,"영기 회복")]),
        (64,  [(258,"사쓰마 밀감"), (358,"밀짚"), (428,"백만장자 I")]),
        (87,  [(158,"완전면역"), (258,"근력증강제")]),
        (110, [(158,"황금 망치"), (278,"지옥 곡옥"), (398,"폭탄")]),
        (135, [(158,"활력 증강"), (278,"회복 환약"), (398,"한방 약재")]),
        (156, [(158,"백뢰"), (258,"장수 영약"), (378,"죠칸 숫돌")]),
        (177, [(158,"호담환"), (258,"호박 곡옥"), (378,"마노 곡옥")]),
        (200, [(0,"영혼 구제"), (110,"유령 곡옥"), (230,"검 수리"), (340,"생명 흡수")]),
        (221, [(110,"의식 곡옥 5"), (240,"업화 부적"), (360,"지혜의 거울"), (468,"닌자 기술")]),
        (242, [(0,"웅담환 4"), (110,"구운 고구마"), (230,"구운 생선"), (340,"숫돌")]),
        (263, [(0,"축복의 술 3"), (110,"치유 환약"), (230,"신성 만병통치약"), (380,"공격 증강")]),
        (284, [(0,"오누라 숫돌 2")]),
        (305, [(0,"감주 II")]),
        (326, [(0,"신성 혜성"), (110,"마무리")]),
        (347, [(0,"신성 축복")]),
        (368, [(0,"자동 회복"), (110,"신성 축복기도")]),
        (389, [(158,"구운 오징어"), (278,"자동 회복"), (398,"신성 환영")]),
        (410, [(158,"말벌떼"), (258,"그림자 벌"), (378,"삼중 번개")]),
        (431, [(158,"죽창"), (258,"삼중 화염"), (378,"대양의 고리")]),
        (452, [(158,"성배"), (258,"지옥 회전")]),
        (473, [(158,"신성 사면")]),
    ]

    for y, row_items in items:
        for x, text in row_items:
            ti = render_text(text, sz, c, bold=True)
            paste_at(result, ti, x, y)

    save_result(result, hash_id, preview)


# =============================================================================
# E8E01EAF - 스킬 이름 (512x512)
# 전체 클리어 후 새로 렌더링
# =============================================================================
def generate_E8E01EAF(preview=False):
    hash_id = "E8E01EAF5D41DB52"
    print(f"[{hash_id}] 스킬 이름...")
    orig = load_original(hash_id)
    if not orig: return print("  SKIP")
    result = orig.copy()
    c = (255,255,255,255)

    # 전체 클리어
    result = clear_region(result, 0, 0, 512, 512)

    sz = 15
    row_h = 27

    # 스킬 이름 목록 (행별 배치)
    skills = [
        (1,   [(1,"안개베기"), (100,"사방뇌"), (190,"청동거울"), (290,"안개참"), (380,"낫")]),
        (28,  [(1,"혼탁참"), (95,"낙월"), (180,"사화염"), (275,"비월"), (370,"섬광")]),
        (55,  [(1,"비상종달새"), (110,"은폐안개"), (230,"거울달"), (335,"암흑십자")]),
        (82,  [(1,"쌍뢰"), (75,"심연화"), (170,"요정타격"), (280,"백귀야행")]),
        (109, [(1,"태양의 고리"), (115,"도박사의 선택")]),
        (136, [(1,"복수"), (65,"요정화염"), (175,"신성검"), (275,"응보")]),
        (163, [(1,"잠자리"), (70,"집중참"), (165,"요정뢰"), (255,"괴묘")]),
        (190, [(1,"지옥문"), (85,"요정업화"), (200,"질풍참"), (300,"요정습격")]),
        (217, [(1,"뇌우"), (60,"망령격"), (165,"지행자"), (270,"선풍")]),
        (244, [(1,"찬월"), (70,"황월"), (150,"저주의 달"), (270,"천벌"), (350,"해골")]),
        (271, [(1,"폭풍"), (60,"산바람"), (150,"쌍화 III"), (255,"초승달")]),
        (298, [(1,"삭월"), (65,"혼돈포효"), (175,"천야"), (265,"카마이타치"), (390,"쿠나이")]),
        (325, [(1,"뇌명"), (65,"하현월"), (165,"번개도롱뇽"), (300,"무적"), (380,"감")]),
        (352, [(1,"업화"), (60,"경험치증가"), (175,"지행자의 힘"), (310,"분쇄"), (385,"유성")]),
        (379, [(1,"와류"), (60,"회오리"), (145,"매복괭이"), (270,"악동")]),
        (406, [(1,"주먹밥"), (75,"성인"), (140,"분신"), (205,"술"), (255,"두꺼비기름"), (370,"신월")]),
        (433, [(1,"미이케"), (70,"바람"), (135,"포만"), (200,"질풍"), (270,"기술"), (340,"복숭아")]),
    ]

    # 수직 텍스트 (우측 열)
    verticals = [
        (420, 1, "분광격"),
        (448, 1, "신성달"),
        (476, 1, "대나무통"),
        (420, 130, "요정업화"),
        (448, 130, "달"),
        (476, 130, "후광"),
        (420, 240, "역주"),
        (448, 240, "월광"),
    ]

    for y, row_items in skills:
        for x, text in row_items:
            ti = render_text(text, sz, c, bold=True)
            paste_at(result, ti, x, y)

    for x, y, text in verticals:
        ti = render_text(text, 11, c, bold=True, vertical=True)
        paste_at(result, ti, x, y)

    save_result(result, hash_id, preview)


# =============================================================================
# 메인
# =============================================================================
GENERATORS = {
    "1823D39C": generate_1823D39C,
    "A3BE57CE": generate_A3BE57CE,
    "74EEEC23": generate_74EEEC23,
    "DF66CADD": generate_DF66CADD,
    "7DC6CF5A": generate_7DC6CF5A,
    "E8E01EAF": generate_E8E01EAF,
}

def main():
    preview = "--preview" in sys.argv
    target = None
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            target = arg.upper()
            break

    for key, gen_func in GENERATORS.items():
        if target and target not in key:
            continue
        gen_func(preview=preview)

    print("\nDone!")

if __name__ == "__main__":
    main()
