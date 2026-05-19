# 지명 텍스처 번역 노트

각 텍스처별로 원본 일본어 텍스트와 권장 한글 번역, detect된 영역 좌표 정보를 정리.
사용자가 Krita 등에서 `kr_textures/ui/<hash>.png`를 편집할 때 참고용.

## 폰트
- 본문/지명: `fonts/Griun_PolSensibility-Rg.ttf` (그리운 경찰감성체)

## 영역 종류
- **B(banner)**: 빨간 배너, 검은 일본어 글자, 게임에서 회전되어 표시 (텍스처상 가로로 누워있음)
- **K(box)**: 흰 frame + 검은 fill + 흰 일본어 글자, 국명 박스
- **C(character)**: brush stroke + 큰 흰 일본어 글자, 캐릭터 이름

## 텍스처별 정보

### `00B61B564A5FD289.png` (2048×2048)

- 원본: `kr_textures/ui/00B61B564A5FD289.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/00B61B564A5FD289.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- banner: `杉林 大きな蜘蛛の巣` → `삼나무 숲 커다란 거미집`
- banner: `鬼の潜む洞窟` → `귀신이 숨은 동굴`
- banner: `鬼の潜む洞窟前` → `귀신이 숨은 동굴 앞`
- banner: `花街海蓮座敷` → `하나마치 카이렌자시키`
- banner: `祝言の場` → `혼례식 장`
- banner: `花嫁行列` → `신부 행렬`
- banner: `茶店前` → `찻집 앞`
- box: `何処かの国` → `어딘가의 나라`
- box: `武蔵` → `무사시`
- box: `伊豆` → `이즈`
- character: `唐木清兵衛宅` → `가라키 세이베에 댁`
- character: `鬼助` → `키스케`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 茶店前 | 차야마에 | top left | red bg / black text | horizontal left to right |
| banner | 唐木清兵衛宅 | 가라키 세이베에타쿠 | top right | red bg / black text | vertical top to bottom |
| banner | 鬼の潜む洞窟 | 오니노 히소무 도쿠츠 | top right | red bg / black text | vertical top to bottom |
| banner | 鬼の潜む洞窟前 | 오니노 히소무 도쿠츠마에 | top right | red bg / black text | vertical top to bottom |
| banner | 杉林 大きな蜘蛛の巣 | 스기바야시 오오키나 쿠모노스 | top right | red bg / black text | vertical top to bottom |
| banner | 祝言の場 | 슈겐노바 | middle left | red bg / black text | horizontal left to right |
| character | 鬼助 | 키스케 | middle left | transparent bg / white text | horizontal left to right |
| banner | 花嫁行列 | 하나요메 교레츠 | bottom left | red bg / black text | horizontal left to right |
| box | 伊豆 | 이즈 | bottom center | black bg / white text | horizontal left to right |
| box | 何処かの国 | 도코카노 쿠니 | bottom right | black bg / white text | horizontal left to right |
| box | 武蔵 | 무사시 | bottom center | black bg / white text | horizontal left to right |
| banner | 花街海蓮座敷 | 하나마치 카이렌자시키 | bottom right | red bg / black text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1677, 15, 1849, 984]`
- B1: `[1397, 1446, 1569, 2008]`
- B2: `[15, 15, 1370, 187]`
- B3: `[1009, 1499, 1181, 2005]`
- B4: `[15, 215, 984, 387]`
- B5: `[15, 415, 892, 587]`
- B6: `[15, 615, 856, 787]`
- B7: `[13, 815, 185, 1413]`
- K0: `[1681, 1013, 1927, 1583]`
- K1: `[1401, 845, 1647, 1416]`
- C0: `[1382, 0, 1946, 1602]`
- C1: `[1669, 1001, 1939, 1595]`
- C2: `[1672, 10, 1854, 988]`
- C3: `[1389, 833, 1658, 1427]`
- C4: `[1412, 29, 1634, 797]`
- C5: `[10, 10, 1374, 1493]`
- C6: `[1009, 208, 1253, 884]`
- C7: `[940, 32, 1069, 165]`
- C8: `[10, 210, 988, 392]`
- C9: `[815, 36, 939, 163]`
- C10: `[10, 409, 896, 592]`
- C11: `[565, 239, 868, 364]`
- C12: `[10, 610, 860, 792]`
- C13: `[307, 649, 559, 758]`

---

### `0AA74C448087838A.png` (2048×1024)

- 원본: `kr_textures/ui/0AA74C448087838A.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/0AA74C448087838A.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `相模` → `사가미`
- banner: `六国見山 鎌倉墓所` → `로쿠코쿠미야마 가마쿠라 묘소`
- character: `州浜` → `스하마`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 鎌倉 | 가마쿠라 | top left | black bg / white text | horizontal left to right |
| banner | 六国見山 鎌倉墓所 | 롯코쿠켄잔 가마쿠라 보쇼 | top right | red bg / black text | vertical top to bottom |
| character | 州浜 | 스하마 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[12, 14, 1364, 186]`
- K0: `[16, 217, 264, 788]`
- C0: `[0, 0, 1852, 806]`
- C1: `[1389, 9, 1836, 682]`
- C2: `[4, 205, 276, 800]`

---

### `3ECF3B0D2C2907BE.png` (2048×1024)

- 원본: `kr_textures/ui/3ECF3B0D2C2907BE.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/3ECF3B0D2C2907BE.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `武蔵` → `무사시`
- banner: `江戸 綱釜藩邸 上屋敷` → `에도 츠나가마 번주 저택`
- banner: `証城寺跡` → `쇼조지 절터`
- character: `お化け屋敷` → `요괴 저택`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 駿府 | 슨푸 | top left | black bg / white text | horizontal left to right |
| banner | 駿州宗岡 | 슨슈 무네오카 | middle left | red bg / black text | horizontal left to right |
| banner | 江戸 細倉藩邸上屋敷 | 에도 호소쿠라 한테이 카미야시키 | top right | red bg / black text | vertical top to bottom |
| character | 妖刀村正 | 요토 무라마사 | bottom left | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[10, 12, 1364, 185]`
- B1: `[292, 206, 464, 803]`
- K0: `[17, 213, 263, 783]`
- C0: `[0, 0, 1835, 868]`
- C1: `[6, 7, 1368, 189]`
- C2: `[1062, 34, 1313, 162]`
- C3: `[5, 201, 275, 795]`

---

### `7E0669E71FCD7B64.png` (1024×1024)

- 원본: `kr_textures/ui/7E0669E71FCD7B64.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/7E0669E71FCD7B64.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `信濃` → `시나노`
- banner: `大根芋畑村` → `다이콘 이모바타케 마을`
- banner: `大根藩馬蕗城` → `다이콘 번 마후키성`
- character: `大根` → `다이콘`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 大根芋畑村 | 다이콘이모바타케무라 | middle left | red bg / black text | vertical top to bottom |
| box | 信濃 | 시나노 | top middle | black bg / white text | vertical top to bottom |
| character | 鴫の藪 | 시기노야부 | top right | transparent bg / white text | vertical top to bottom |
| banner | 大益謝油源井 | 오마스샤유겐이 | bottom middle | red bg / black text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[797, 15, 969, 800]`
- B1: `[15, 775, 752, 947]`
- K0: `[16, 499, 586, 744]`
- C0: `[792, 10, 974, 804]`
- C1: `[817, 419, 946, 668]`
- C2: `[0, 7, 792, 762]`
- C3: `[10, 770, 756, 952]`
- C4: `[4, 486, 597, 756]`

---

### `464E370EF865D0AC.png` (2048×2048)

- 원본: `kr_textures/ui/464E370EF865D0AC.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/464E370EF865D0AC.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- banner: `大根藩馬路城` → `다이콘 번 마지성`
- banner: `大根藩馬路城跡` → `다이콘 번 마지성 옛터`
- banner: `馬路城 大天守` → `마지성 대천수`
- banner: `大根芋畑村` → `다이콘 이모바타케 마을`
- banner: `西馬路口` → `니시 마지구치`
- banner: `鬼ヶ島 大蛇` → `오니가시마 오로치`
- box: `茶屋` → `찻집`
- box: `船屋` → `배집`
- box: `鍛冶` → `대장간`
- character: `鳴野豆太夫` → `나루노 마메다유`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 馬路城 | 마지성 | top right | red bg / black text | vertical top to bottom |
| banner | 大天守 | 다이텐슈 | top right | red bg / black text | vertical top to bottom |
| banner | 大根藩馬路城跡 | 다이콘한 마지성터 | top right | red bg / black text | vertical top to bottom |
| character | 鳴野豆太夫 | 나루노마메다유 | top right | transparent bg / white text | vertical top to bottom |
| banner | 西馬路口 | 니시마지구치 | middle left | red bg / black text | horizontal left to right |
| banner | 大根芋畑村 | 다이콘 이모바타케무라 | middle left | red bg / black text | vertical top to bottom |
| box | 茶屋 | 차야 | middle right | black bg / white text | horizontal left to right |
| box | 船屋 | 후나야 | middle right | black bg / white text | horizontal left to right |
| box | 鍛冶 | 가지 | bottom right | black bg / white text | horizontal left to right |
| banner | 大根藩馬路城 | 다이콘한 마지성 | middle right | red bg / black text | vertical top to bottom |
| banner | 鬼ヶ島 大蛇 | 오니가시마 오로치 | bottom right | red bg / black text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1849, 225, 2021, 1011]`
- B1: `[975, 15, 1760, 187]`
- B2: `[1010, 831, 1748, 1003]`
- B3: `[15, 227, 984, 399]`
- B4: `[15, 427, 984, 599]`
- B5: `[709, 626, 881, 1226]`
- K0: `[1573, 229, 1819, 799]`
- K1: `[1292, 229, 1538, 797]`
- K2: `[1012, 229, 1258, 797]`
- C0: `[1844, 222, 2026, 1016]`
- C1: `[1876, 255, 2002, 501]`
- C2: `[0, 0, 1837, 818]`
- C3: `[1561, 217, 1831, 811]`
- C4: `[1006, 826, 1752, 1008]`
- C5: `[1379, 37, 1627, 144]`
- C6: `[1280, 216, 1549, 809]`
- C7: `[1000, 216, 1269, 809]`
- C8: `[10, 222, 988, 404]`
- C9: `[10, 422, 988, 604]`
- C10: `[8, 619, 683, 863]`
- C11: `[347, 246, 599, 353]`
- C12: `[67, 447, 315, 554]`

---

### `864BD9CBCC496F78.png` (2048×1024)

- 원본: `kr_textures/ui/864BD9CBCC496F78.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/864BD9CBCC496F78.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `伊賀` → `이가`
- banner: `暗夜城広間の場` → `암야성 넓은 방의 장`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 云中 | 운추 | top left | black bg / white text | horizontal left to right |
| banner | 暗夜城云間の場 | 안야조 운칸노바 | top right | red bg / black text | vertical top to bottom |
| character | 云中 | 운추 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[12, 15, 1064, 187]`
- K0: `[16, 217, 263, 788]`
- C0: `[0, 0, 1547, 806]`
- C1: `[8, 10, 1068, 192]`
- C2: `[4, 204, 275, 800]`

---

### `0912E45A567A41C9.png` (2048×1024)

- 원본: `kr_textures/ui/0912E45A567A41C9.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/0912E45A567A41C9.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `武蔵` → `무사시`
- banner: `新吉原 衣紋坂` → `신요시와라 에몬자카`
- character: `百姫×鬼助` → `모모히메×키스케`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 駿府 | 슨푸 | top left | black bg / white text | horizontal left to right |
| banner | 新吉原 大紋坂 | 신요시와라 오몬자카 | top right | red bg / black text | vertical top to bottom |
| character | 百姫く鬼助 | 모모히메 < 키스케 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[12, 15, 1064, 187]`
- K0: `[16, 217, 264, 788]`
- C0: `[0, 0, 1557, 806]`
- C1: `[8, 10, 1068, 192]`
- C2: `[4, 205, 276, 800]`

---

### `4633B92FBA1371F4.png` (2048×2048)

- 원본: `kr_textures/ui/4633B92FBA1371F4.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/4633B92FBA1371F4.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `相模` → `사가미`
- banner: `戸塚宿観念寺` → `도쓰카주쿠 간넨지`
- banner: `綱谷藩勝尾城` → `츠나야 번 가쓰오성`
- banner: `綱谷藩勝尾城回廊` → `츠나야 번 가쓰오성 회랑`
- banner: `綱谷藩葛銀字庭` → `츠나야 번 갈은자 정원`
- banner: `由比ヶ浜` → `유이가하마`
- banner: `釣船川船着場` → `쓰리부네강 선착장`
- box: `当川` → `도가와`
- box: `荒益` → `아라마스`
- character: `堺港町` → `사카이 항구마을`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 相模 | 사가미 | top left | black bg / white text | horizontal left to right |
| banner | 戸塚宿観念寺 | 도쓰카주쿠 간넨지 | top right | red bg / black text | vertical top to bottom |
| banner | 綱谷藩勝尾城 | 쓰나야번 가쓰오성 | top right | red bg / black text | vertical top to bottom |
| banner | 綱谷藩勝尾城回廊 | 쓰나야번 가쓰오성 회랑 | middle right | red bg / black text | vertical top to bottom |
| banner | 綱谷藩葛銀字庭 | 쓰나야번 갈은자 정원 | top right | red bg / black text | vertical top to bottom |
| box | 当川 | 도가와 | middle right | black bg / white text | horizontal left to right |
| banner | 由比ヶ浜 | 유이가하마 | bottom left | red bg / black text | horizontal left to right |
| banner | 釣船川船着場 | 쓰리부네강 선착장 | bottom right | red bg / black text | horizontal left to right |
| box | 荒益 | 아라마스 | bottom left | black bg / white text | horizontal left to right |
| character | 堺港町 | 사카이 항구마을 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1253, 11, 1425, 981]`
- B1: `[1253, 1003, 1425, 1738]`
- B2: `[11, 13, 1227, 185]`
- B3: `[11, 208, 1127, 381]`
- B4: `[11, 406, 850, 578]`
- B5: `[11, 607, 850, 779]`
- K0: `[1457, 1041, 1703, 1611]`
- K1: `[881, 409, 1127, 978]`
- K2: `[20, 808, 266, 1378]`
- C0: `[1645, 9, 1889, 682]`
- C1: `[1248, 7, 1721, 1630]`
- C2: `[1445, 1029, 1715, 1623]`
- C3: `[2, 0, 1640, 1397]`
- C4: `[1249, 1000, 1430, 1742]`
- C5: `[870, 397, 1139, 991]`
- C6: `[7, 203, 1131, 385]`
- C7: `[7, 401, 854, 583]`
- C8: `[7, 601, 854, 783]`
- C9: `[434, 624, 651, 753]`
- C10: `[8, 797, 275, 1390]`

---

### `4709F3E364671D89.png` (1024×1024)

- 원본: `kr_textures/ui/4709F3E364671D89.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/4709F3E364671D89.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `美濃` → `미노`
- banner: `中仙道間道` → `나카센도 사잇길`
- banner: `鳴神城内座敷` → `나루카미성 내 거실`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 中仙道間道 | 나카센도 간도 | middle left | red bg / black text | vertical top to bottom |
| banner | 鳴神城内座敷 | 나루카미 성내 좌敷 | middle right | red bg / black text | vertical top to bottom |
| box | 稲城 | 이나기 | bottom middle | black bg / white text | horizontal left to right |
| character | 城内 | 조나이 | top middle | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[12, 15, 954, 187]`
- B1: `[12, 819, 798, 991]`
- K0: `[712, 217, 960, 788]`
- C0: `[0, 10, 978, 806]`
- C1: `[700, 204, 971, 800]`
- C2: `[8, 814, 802, 996]`
- C3: `[9, 207, 682, 451]`

---

### `5882EA68BABF3C63.png` (2048×1024)

- 원본: `kr_textures/ui/5882EA68BABF3C63.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/5882EA68BABF3C63.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `何処かの国` → `어딘가의 나라`
- box: `武蔵` → `무사시`
- box: `美濃` → `미노`
- banner: `日本堤 新吉原` → `니혼즈츠미 신요시와라`
- banner: `菩提寺 虎姫の墓前` → `보리사 토라히메의 묘 앞`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 武蔵 | 무사시 | top left | black bg / white text | vertical top to bottom |
| box | 美濃 | 미노 | middle left | black bg / white text | vertical top to bottom |
| banner | 日本堤 | 니혼즈쓰미 | top middle | red bg / black text | vertical top to bottom |
| banner | 新吉原 | 신요시와라 | middle left | red bg / black text | vertical top to bottom |
| banner | 菩提寺 | 보다이지 | top middle | red bg / black text | vertical top to bottom |
| banner | 虎姫の墓前 | 도라히메노 보젠 | middle right | red bg / black text | vertical top to bottom |
| box | 何処かの国 | 도코카노쿠니 | top right | black bg / white text | vertical top to bottom |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1853, 12, 2025, 380]`
- B1: `[1389, 12, 1561, 954]`
- B2: `[12, 295, 1364, 467]`
- B3: `[14, 497, 1068, 669]`
- K0: `[620, 701, 1192, 948]`
- K1: `[17, 701, 588, 948]`
- C0: `[1384, 8, 2048, 958]`
- C1: `[1589, 9, 1833, 684]`
- C2: `[8, 290, 1368, 471]`
- C3: `[0, 0, 1241, 966]`
- C4: `[28, 31, 1210, 252]`
- C5: `[608, 688, 1203, 960]`
- C6: `[10, 492, 1072, 674]`
- C7: `[5, 688, 599, 960]`

---

### `6605F569D9389F9C.png` (2048×2048)

- 원본: `kr_textures/ui/6605F569D9389F9C.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/6605F569D9389F9C.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- banner: `白川郷 白銀ヶ淵 廃れ社` → `시라카와고 시로가네가후치 폐사`
- banner: `飛騨国` → `히다국`
- banner: `飛騨街道` → `히다 가도`
- banner: `飛騨川` → `히다강`
- banner: `美濃国 境木峠` → `미노국 사카이기 고개`
- box: `関所` → `관문`
- box: `峠道` → `고갯길`
- character: `大雪山` → `다이세쓰잔`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 関所 | 세키쇼 | top middle | black bg / white text | horizontal left to right |
| banner | 白川郷 白銀ヶ淵 廃れ社 | 시라카와고 시로가네가후치 스타레야시로 | top right | red bg / black text | vertical top to bottom |
| banner | 飛騨街道 | 히다카이도 | bottom left | red bg / black text | horizontal left to right |
| character | 大雪山 | 다이세쓰잔 | middle right | transparent bg / white text | horizontal left to right |
| banner | 飛騨川 | 히다가와 | bottom middle | red bg / black text | horizontal left to right |
| banner | 飛騨国 | 히다노쿠니 | bottom right | red bg / black text | horizontal left to right |
| banner | 美濃国 境木峠 | 미노노쿠니 사카이기토게 | middle right | red bg / black text | vertical top to bottom |
| box | 峠道 | 토게미치 | bottom middle | black bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1720, 11, 1893, 978]`
- B1: `[1486, 983, 1657, 1579]`
- B2: `[13, 15, 1462, 187]`
- B3: `[1267, 210, 1439, 715]`
- B4: `[10, 213, 977, 386]`
- B5: `[11, 413, 977, 585]`
- B6: `[11, 608, 977, 780]`
- K0: `[1729, 1005, 1974, 1574]`
- K1: `[17, 808, 263, 1379]`
- C0: `[0, 0, 1993, 1593]`
- C1: `[1717, 993, 1986, 1587]`
- C2: `[9, 10, 1466, 192]`
- C3: `[1001, 208, 1245, 883]`
- C4: `[7, 208, 982, 390]`
- C5: `[7, 407, 982, 589]`
- C6: `[7, 603, 982, 785]`
- C7: `[547, 39, 674, 167]`
- C8: `[5, 797, 275, 1391]`

---

### `7053B8FFC8B89807.png` (2048×1024)

- 원본: `kr_textures/ui/7053B8FFC8B89807.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/7053B8FFC8B89807.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `信濃` → `시나노`
- banner: `信濃山奥狐のお宿の場` → `시나노 산속 여우의 여인숙 장`
- banner: `八幡原 修羅の戦場` → `하치만바라 수라의 전장`
- character: `血狂毘沙門` → `치구루이비샤몬`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| character | 血狂毘沙門 | 혈광비사문 | middle left | transparent bg / white text | vertical top to bottom |
| box | 鍛冶 | 가지 | bottom left | black bg / white text | horizontal left to right |
| banner | 八幡原 修羅の戦場 | 하치만바라 수라의 전장 | middle right | red bg / black text | vertical top to bottom |
| banner | 信濃山奥狐のお宿の場 | 시나노 산속 여우 여관의 장 | top right | red bg / black text | vertical top to bottom |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[8, 11, 1514, 183]`
- B1: `[9, 203, 1361, 375]`
- K0: `[1046, 401, 1292, 971]`
- C0: `[1528, 5, 1773, 680]`
- C1: `[0, 5, 1519, 990]`
- C2: `[4, 197, 1364, 380]`
- C3: `[1034, 388, 1304, 984]`
- C4: `[762, 228, 888, 349]`

---

### `7282AD29CF433DA0.png` (2048×1024)

- 원본: `kr_textures/ui/7282AD29CF433DA0.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/7282AD29CF433DA0.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `何処かの国` → `어딘가의 나라`
- box: `大和` → `야마토`
- banner: `峠の茶屋` → `고갯마루 찻집`
- banner: `金剛山山頂高天原入口` → `곤고산 산정 다카마가하라 입구`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| character | 河内 | 가와치 | top left | transparent bg / white text | horizontal left to right |
| banner | 金剛山山麓高天原入口 | 곤고산 산로쿠 다카마가하라 이리구치 | middle right | red bg / black text | vertical top to bottom |
| box | 何処かの国 | 도코카노쿠니 | top right | black bg / white text | vertical top to bottom |
| box | 大和 | 야마토 | middle right | black bg / white text | vertical top to bottom |
| banner | 剛鉄の岳 | 고테쓰노다케 | bottom left | red bg / black text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1789, 289, 1961, 942]`
- B1: `[9, 291, 1516, 463]`
- K0: `[1256, 17, 1828, 264]`
- C0: `[1784, 284, 1966, 947]`
- C1: `[0, 0, 1846, 282]`
- C2: `[1528, 284, 1773, 960]`
- C3: `[4, 285, 1520, 468]`
- C4: `[0, 7, 1233, 879]`
- C5: `[28, 31, 1210, 252]`

---

### `7358BEAA2EF5F8A8.png` (2048×1024)

- 원본: `kr_textures/ui/7358BEAA2EF5F8A8.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/7358BEAA2EF5F8A8.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `大和` → `야마토`
- banner: `柳生城広間の場` → `야규성 넓은 방의 장`
- banner: `鳴神城 大手門前` → `나루카미성 오테문 앞`
- banner: `金剛山山頂高天原入口` → `곤고산 산정 다카마가하라 입구`
- character: `不動明王` → `부동명왕`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 美濃 | 미노 | top left | black bg / white text | vertical top to bottom |
| banner | 柳生城広間の場 | 야규성 히로마노바 | top middle left | red bg / black text | vertical top to bottom |
| banner | 鳴神城大手門前 | 나루카미성 오테몬 앞 | top middle right | red bg / black text | vertical top to bottom |
| banner | 金剛山山頂高天原入口 | 곤고산 산정 다카마가하라 입구 | top right | red bg / black text | vertical top to bottom |
| box | 大谷 | 오타니 | middle right | black bg / white text | horizontal left to right |
| character | 駿河 | 스루가 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[9, 11, 1516, 183]`
- B1: `[8, 203, 1220, 375]`
- B2: `[9, 395, 1061, 567]`
- K0: `[1244, 209, 1491, 779]`
- K1: `[16, 593, 588, 840]`
- C0: `[0, 0, 1987, 858]`
- C1: `[1528, 5, 1979, 814]`
- C2: `[1232, 196, 1503, 792]`
- C3: `[4, 197, 1224, 380]`
- C4: `[4, 389, 1064, 572]`
- C5: `[4, 580, 600, 852]`

---

### `8098AD7E2C438C22.png` (2048×1024)

- 원본: `kr_textures/ui/8098AD7E2C438C22.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/8098AD7E2C438C22.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `大和` → `야마토`
- banner: `柳生城広間の場` → `야규성 넓은 방의 장`
- banner: `金剛山山腹大仏殿` → `곤고산 산허리 대불전`
- banner: `金剛山山頂高天原入口` → `곤고산 산정 다카마가하라 입구`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 柳生城玄門の場 | 야규성 현문의 장 | top left | red bg / black text | vertical top to bottom |
| banner | 金剛山山腹大仏殿 | 곤고산 산복 대불전 | top middle | red bg / black text | vertical top to bottom |
| banner | 金剛山山麓高天原入口 | 곤고산 산록 다카마가하라 입구 | top right | red bg / black text | vertical top to bottom |
| box | 若木 | 와카기 | middle right | black bg / white text | horizontal left to right |
| character | 出雲嶽寺 | 이즈모다케지 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[9, 11, 1516, 183]`
- B1: `[8, 203, 1220, 375]`
- B2: `[9, 395, 1061, 567]`
- K0: `[1244, 209, 1491, 779]`
- C0: `[4, 0, 1987, 798]`
- C1: `[1528, 5, 1979, 814]`
- C2: `[1232, 196, 1503, 792]`
- C3: `[4, 197, 1224, 380]`
- C4: `[4, 389, 1064, 572]`

---

### `31710FB73B2686EF.png` (2048×1024)

- 원본: `kr_textures/ui/31710FB73B2686EF.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/31710FB73B2686EF.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `地獄` → `지옥`
- banner: `地獄八景 大焦熱` → `지옥팔경 대초열`
- banner: `地獄八景 等活` → `지옥팔경 등활`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 衆合 | 슈고 | top middle | black bg / white text | horizontal left to right |
| banner | 地獄八景 大焦熱 | 지고쿠 핫케이 다이쇼네츠 | top right | red bg / black text | vertical top to bottom |
| banner | 行くは成仏 | 이쿠와 조부츠 | middle left | red bg / black text | horizontal left to right |
| box | 変化 | 헨게 | bottom right | black bg / white text | horizontal left to right |
| character | 大凹 | 다이오 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1249, 12, 1421, 954]`
- B1: `[12, 15, 1224, 187]`
- K0: `[1452, 17, 1700, 587]`
- K1: `[280, 217, 526, 788]`
- C0: `[262, 0, 1923, 806]`
- C1: `[1244, 8, 1426, 958]`
- C2: `[8, 10, 1228, 192]`
- C3: `[268, 204, 538, 800]`
- C4: `[13, 208, 257, 886]`

---

### `72165D43344F3190.png` (2048×2048)

- 원본: `kr_textures/ui/72165D43344F3190.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/72165D43344F3190.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- banner: `二人の刺客` → `두 명의 자객`
- banner: `赤坂宿 旅籠の部屋` → `아카사카주쿠 여인숙 방`
- banner: `東海道 御油吉田間街道` → `도카이도 고유 요시다 사이 가도`
- banner: `東海道 藤川赤坂間街道` → `도카이도 후지카와 아카사카 사이 가도`
- box: `当川` → `도가와`
- character: `参州羅刹助ノ塚` → `산슈 라세쓰스케 무덤`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| character | 二人の刺客 | 두 사람의 자객 | middle right | transparent bg / white text | vertical top to bottom |
| banner | 赤坂宿 旅籠の部屋 | 아카사카슈쿠 하타고노헤야 | top right | red bg / black text | vertical top to bottom |
| banner | 東海道 御油吉田間街道 | 도카이도 고유 요시다 간 가도 | top right | red bg / black text | vertical top to bottom |
| banner | 東海道 藤川赤坂間街道 | 도카이도 후지카와 아카사카 간 가도 | top right | red bg / black text | vertical top to bottom |
| box | 当川 | 도센 | bottom middle | black bg / white text | horizontal left to right |
| banner | 参州羅刹助ノ塚 | 산슈 라세쓰스케노쓰카 | bottom right | red bg / black text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1746, 11, 1918, 850]`
- B1: `[11, 211, 1464, 384]`
- B2: `[11, 15, 1459, 187]`
- B3: `[11, 407, 1227, 581]`
- K0: `[1493, 905, 1739, 1474]`
- C0: `[159, 7, 1923, 854]`
- C1: `[1475, 205, 1758, 1493]`
- C2: `[1482, 893, 1751, 1487]`
- C3: `[7, 207, 1468, 389]`
- C4: `[7, 9, 1463, 191]`
- C5: `[1183, 231, 1435, 363]`
- C6: `[1185, 35, 1430, 165]`
- C7: `[7, 403, 1232, 585]`
- C8: `[931, 435, 1185, 560]`
- C9: `[680, 237, 882, 355]`
- C10: `[553, 432, 762, 561]`

---

### `615858B46587A60E.png` (2048×1024)

- 원본: `kr_textures/ui/615858B46587A60E.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/615858B46587A60E.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `美濃` → `미노`
- box: `武蔵` → `무사시`
- banner: `鳴神城雲間の場` → `나루카미성 구름 사이의 장`
- banner: `江戸城 天守` → `에도성 천수각`
- character: `山州宗山城` → `산슈 소잔성`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 無垢 | 무쿠 | top left | black bg / white text | horizontal left to right |
| banner | 鳴神城雲間の場 | 나루카미성 구모마노바 | middle right | red bg / black text | vertical top to bottom |
| character | 犬神徳川綱吉 | 이누가미 도쿠가와 쓰나요시 | top right | transparent bg / white text | vertical top to bottom |
| banner | 山州宗山城 | 산슈 소잔성 | middle left | red bg / black text | horizontal left to right |
| box | 船州 | 센슈 | bottom right | black bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1265, 12, 1437, 954]`
- B1: `[12, 215, 1064, 387]`
- K0: `[1732, 17, 1980, 587]`
- K1: `[16, 417, 264, 988]`
- C0: `[0, 0, 1998, 1006]`
- C1: `[1465, 9, 1709, 686]`
- C2: `[1260, 8, 1442, 958]`
- C3: `[8, 210, 1068, 392]`
- C4: `[4, 405, 276, 1000]`

---

### `2611666E71A8181A.png` (2048×2048)

- 원본: `kr_textures/ui/2611666E71A8181A.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/2611666E71A8181A.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `天上道` → `천상도`
- box: `武蔵` → `무사시`
- banner: `江戸城 天守` → `에도성 천수각`
- banner: `武蔵街道 祠の場` → `무사시 가도 사당의 장`
- banner: `天門の先` → `천문 너머`
- banner: `仏界` → `불계`
- character: `阿弥陀如来` → `아미타여래`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 天門の先 | 천문의 앞 | top right | red bg / black text | vertical top to bottom |
| banner | 仏界 | 불계 | middle right | red bg / black text | vertical top to bottom |
| banner | 武蔵街道 | 무사시 가도 | top right | red bg / black text | vertical top to bottom |
| banner | 祠の場 | 사당 터 | middle right | red bg / black text | vertical top to bottom |
| character | 犬神徳川綱吉 | 견신 도쿠가와 쓰나요시 | top right | transparent bg / white text | vertical top to bottom |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1753, 11, 1925, 954]`
- B1: `[12, 215, 1224, 387]`
- B2: `[12, 415, 1064, 587]`
- K0: `[1268, 825, 1516, 1396]`
- C0: `[1749, 8, 1930, 958]`
- C1: `[0, 0, 1749, 1414]`
- C2: `[1256, 813, 1528, 1408]`
- C3: `[1280, 29, 1502, 780]`
- C4: `[8, 210, 1228, 391]`
- C5: `[8, 410, 1068, 592]`
- C6: `[9, 607, 682, 851]`

---

### `A8486C49F76167C3.png` (2048×1024)

- 원본: `kr_textures/ui/A8486C49F76167C3.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/A8486C49F76167C3.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `伊勢` → `이세`
- banner: `伊勢天神高天原入口` → `이세 천신 다카마가하라 입구`
- banner: `二見浦` → `후타미우라`
- banner: `伊勢街道` → `이세 가도`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 殺生 | 셋쇼 | top left | black bg / white text | horizontal left to right |
| banner | 鮮血川 | 센케쓰가와 | top middle | red bg / black text | horizontal left to right |
| banner | 伊勢天神高天原入口 | 이세텐진 다카마가하라 입구 | top right | red bg / black text | vertical top to bottom |
| banner | 啓蟄境中 | 게이칫쿄추 | bottom middle | red bg / black text | horizontal left to right |
| character | 奇崛 | 기굴 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1637, 8, 1809, 662]`
- B1: `[9, 11, 1361, 183]`
- B2: `[289, 200, 461, 706]`
- K0: `[16, 209, 263, 779]`
- C0: `[0, 0, 2018, 798]`
- C1: `[1376, 5, 1621, 680]`
- C2: `[4, 5, 1366, 188]`
- C3: `[4, 196, 275, 792]`

---

### `C8B2975F2A629F4B.png` (1024×1024)

- 원본: `kr_textures/ui/C8B2975F2A629F4B.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/C8B2975F2A629F4B.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `駿河` → `스루가`
- banner: `富士山頂龍脈` → `후지산 정상 용맥`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| character | 山城 | 야마시로 | top left | transparent bg / white text | horizontal left to right |
| box | 駿河 | 스루가 | bottom middle | black bg / white text | horizontal left to right |
| banner | 富士山頂龍脈 | 후지산초 류먀쿠 | middle right | red bg / black text | vertical top to bottom |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[12, 15, 954, 187]`
- K0: `[712, 217, 959, 788]`
- C0: `[0, 10, 977, 875]`
- C1: `[700, 205, 971, 800]`
- C2: `[9, 207, 682, 451]`

---

### `C8C4589102431759.png` (2048×1024)

- 원본: `kr_textures/ui/C8C4589102431759.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/C8C4589102431759.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `大和` → `야마토`
- banner: `奈良善祷寺 金堂` → `나라 젠토지 금당`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 吉野 | 요시노 | top left | black bg / white text | horizontal left to right |
| banner | 奈良善祥寺 金堂 | 나라 젠쇼지 금당 | top right | red bg / black text | vertical top to bottom |
| character | 深雪 | 미유키 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[12, 15, 1224, 187]`
- K0: `[16, 217, 263, 788]`
- C0: `[0, 0, 1714, 806]`
- C1: `[8, 10, 1228, 192]`
- C2: `[4, 204, 274, 800]`

---

### `C8E42A56480DB818.png` (2048×1024)

- 원본: `kr_textures/ui/C8E42A56480DB818.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/C8E42A56480DB818.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- banner: `江戸 大根藩邸下屋敷` → `에도 다이콘 번저 시모야시키`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 江戸 大根藩邸下屋敷 | 에도 다이콘 번저 시모야시키 | top right | red bg / black text | vertical top to bottom |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[15, 15, 1370, 187]`
- B1: `[681, 214, 853, 1000]`
- B2: `[481, 214, 653, 1000]`
- B3: `[279, 214, 451, 1000]`
- K0: `[1617, 17, 1863, 587]`
- C0: `[1377, 0, 1882, 981]`
- C1: `[10, 10, 1374, 192]`
- C2: `[1069, 37, 1319, 165]`
- C3: `[676, 210, 858, 1004]`
- C4: `[476, 210, 658, 1004]`
- C5: `[509, 243, 634, 490]`
- C6: `[274, 210, 456, 1004]`
- C7: `[299, 818, 430, 947]`
- C8: `[13, 208, 257, 882]`

---

### `C84B5B3A51547DF0.png` (1024×1024)

- 원본: `kr_textures/ui/C84B5B3A51547DF0.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/C84B5B3A51547DF0.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `遠江` → `도토미`
- banner: `秋葉山山腹` → `아키바산 산허리`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 秋葉山山腹 | 아키하산 산복 | middle left | red bg / black text | vertical top to bottom |
| character | 社へ | 야시로에 | bottom left | transparent bg / white text | horizontal left to right |
| box | 門前 | 몬젠 | bottom right | black bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[13, 619, 798, 791]`
- K0: `[712, 17, 958, 588]`
- C0: `[694, 0, 1019, 1015]`
- C1: `[8, 614, 802, 796]`
- C2: `[9, 7, 683, 251]`

---

### `C3848C8E5ED70F7A.png` (2048×1024)

- 원본: `kr_textures/ui/C3848C8E5ED70F7A.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/C3848C8E5ED70F7A.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `美濃` → `미노`
- banner: `伊吹山 不破関` → `이부키산 후와노세키`
- character: `鬼助` → `키스케`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 近江州 | 오미슈 | top left | black bg / white text | horizontal left to right |
| banner | 伊吹山 | 이부키야마 | top right | red bg / black text | vertical top to bottom |
| banner | 不破関 | 후와노세키 | middle right | red bg / black text | vertical top to bottom |
| character | 前町 | 마에마치 | bottom right | transparent bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[12, 15, 1064, 187]`
- K0: `[16, 217, 264, 788]`
- C0: `[0, 0, 1555, 806]`
- C1: `[8, 10, 1068, 192]`
- C2: `[4, 204, 276, 800]`

---

### `E9E834DE4BAFDAB2.png` (1024×1024)

- 원본: `kr_textures/ui/E9E834DE4BAFDAB2.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/E9E834DE4BAFDAB2.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `甲斐` → `카이`
- banner: `甲府の街道` → `코후의 가도`
- banner: `山の中の一軒家` → `산속의 외딴집`
- character: `山姥` → `야마우바`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 甲府の街道 | 고후노 가이도 | middle left | red bg / black text | vertical top to bottom |
| character | 山姥 | 야마우바 | top middle | transparent bg / white text | vertical top to bottom |
| banner | 山の中の一軒家 | 야마노 나카노 잇켄야 | middle right | red bg / black text | vertical top to bottom |
| box | 俵田 | 다와라다 | bottom middle | black bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[15, 15, 984, 187]`
- B1: `[15, 819, 752, 991]`
- K0: `[716, 217, 962, 787]`
- C0: `[0, 10, 988, 806]`
- C1: `[704, 205, 974, 799]`
- C2: `[10, 814, 756, 996]`
- C3: `[444, 842, 689, 971]`
- C4: `[8, 207, 682, 451]`

---

### `E9F2EC8557984A58.png` (1024×1024)

- 원본: `kr_textures/ui/E9F2EC8557984A58.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/E9F2EC8557984A58.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `駿河` → `스루가`
- banner: `三保之松原` → `미호노마츠바라`
- banner: `駿府の旅籠` → `슨푸의 여인숙`
- character: `雪之丞` → `유키노조`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| banner | 駿府の旅籠 | 슨푸노 하타고 | middle left | red bg / black text | vertical top to bottom |
| banner | 三保之松原 | 미호노 마쓰바라 | middle left | red bg / black text | vertical top to bottom |
| character | 雪之丞 | 유키노조 | top right | transparent bg / white text | vertical top to bottom |
| box | 凶賊 | 교조쿠 | bottom right | black bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[13, 619, 798, 791]`
- B1: `[13, 819, 798, 991]`
- K0: `[712, 17, 959, 588]`
- C0: `[0, 0, 977, 606]`
- C1: `[8, 614, 802, 796]`
- C2: `[8, 814, 802, 996]`
- C3: `[9, 7, 683, 251]`

---

### `FFC64B053648525E.png` (2048×1024)

- 원본: `kr_textures/ui/FFC64B053648525E.png` (현재 일본어 원본 상태)
- 백업: `textures/place_name_originals/FFC64B053648525E.png`

**번역 매핑 (kind / 일본어 → 한글)**:

- box: `飛騨` → `히다`
- banner: `白川郷 白銀ヶ淵 廃れ社` → `시라카와고 시로가네가후치 폐사`
- banner: `飛騨街道` → `히다 가도`
- banner: `美濃国 境木峠` → `미노국 사카이기 고개`

**codex 추가 정보 (위치 힌트, 색상, 방향)**:

| kind | 일본어 | 한글 | 위치 | 색상 | 방향 |
|---|---|---|---|---|---|
| box | 関所 | 세키쇼 | top left | black bg / white text | horizontal left to right |
| banner | 白川郷 白銀ヶ淵 廃れ社 | 시라카와고 시로가네가후치 스타레야시로 | top right | red bg / black text | vertical top to bottom |
| banner | 飛騨街道 | 히다카이도 | middle left | red bg / black text | horizontal left to right |
| character | 大雪山 | 다이세쓰잔 | middle left | transparent bg / white text | horizontal left to right |
| banner | 飛騨川 | 히다가와 | middle left | red bg / black text | horizontal left to right |
| banner | 飛騨国 | 히다노쿠니 | middle left | red bg / black text | horizontal left to right |
| banner | 美濃国 境木峠 | 미노노쿠니 사카이기토게 | bottom left | red bg / black text | horizontal left to right |
| box | 峠道 | 토게미치 | bottom right | black bg / white text | horizontal left to right |

**자동 detect bbox 좌표 (참고용)**:

- B0: `[1486, 10, 1658, 977]`
- B1: `[13, 15, 1462, 187]`
- B2: `[1165, 211, 1337, 715]`
- B3: `[965, 210, 1137, 715]`
- B4: `[555, 211, 728, 945]`
- K0: `[1688, 17, 1934, 587]`
- K1: `[284, 217, 530, 786]`
- C0: `[266, 0, 1952, 805]`
- C1: `[1481, 7, 1663, 982]`
- C2: `[1510, 553, 1640, 683]`
- C3: `[1505, 173, 1637, 426]`
- C4: `[9, 10, 1466, 192]`
- C5: `[551, 207, 733, 950]`
- C6: `[547, 39, 674, 167]`
- C7: `[272, 205, 539, 799]`
- C8: `[13, 208, 257, 883]`

---
