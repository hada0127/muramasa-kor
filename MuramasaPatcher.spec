# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Muramasa 한글 패치 통합 GUI(Windows exe).

빌드:  pyinstaller MuramasaPatcher.spec

이 exe 는 코드 + 파이썬 런타임 + numpy/pillow/xxhash 만 담는다.
번역 JSON·텍스처 PNG·Vita3K 델타 같은 **데이터 자산은 포함하지 않는다**
(저작권상 원본 CPK 없이는 GitHub Actions 에서 만들 수 없고, 데이터는 exe 옆
폴더에 동봉되기 때문). gui_patcher 의 PKG_ROOT 탐색이 exe 옆 데이터를 찾는다.
"""

from PyInstaller.utils.hooks import collect_submodules

hidden = [
    "apply_release_patch",
    "apply_realhw_patch",
    "cpk_extract",
    "cpk_patch",
    "build_patch",
    "realhw_bake",
    "realhw_font_bake",
    "crilayla_compress",
    "nms_parser",
    "font_mapping",
    # realhw 베이크가 간접적으로 끌고 오는 모듈(정적 재귀 분석 누락 대비)
    "ftx_encode",
    "ftx_extract",
    "auto_font_import",
    "hd_font_import",
]
hidden += collect_submodules("PIL")
hidden += collect_submodules("numpy")

a = Analysis(
    ["tools/gui_patcher.py"],
    pathex=["tools"],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "tkinter.test"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MuramasaPatcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,   # GUI 앱 — 콘솔 창 숨김
    disable_windowed_traceback=False,
    icon=None,
)
