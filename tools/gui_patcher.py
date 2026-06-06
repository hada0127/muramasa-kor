#!/usr/bin/env python3
"""Muramasa Rebirth 한글 패치 — 통합 GUI 설치 도구 (Vita3K 에뮬레이터 + 실기 PS Vita).

Tkinter 기반 단일 창. 사용자는 모드(에뮬레이터/실기)를 고르고, 자동 탐지된 경로를
확인한 뒤 버튼 한 번으로 패치한다. CLI 인자를 직접 칠 필요가 없다.

- Windows: PyInstaller로 빌드한 MuramasaPatcher.exe 로 더블클릭 실행(파이썬 설치 불필요).
- macOS/Linux: `python3 gui_patcher.py` (또는 동봉된 .command) 로 실행.

자산 레이아웃(배포 zip / 빌드 번들 공통):
    <패키지 루트>/
        gui_patcher.py          (이 파일)
        MuramasaPatcher.exe      (Windows 빌드, 선택)
        tools/*.py               (실기 베이크 엔진 + 이 GUI)
        translations/*.json
        textures/kr/ui/*.png, textures/kr/ui_xbutton/*.png
        fonts/*
        vita3k/                  (Vita3K 패처 자산)
            release/manifest.json
            patches/*.bin, *.json
            textures/import/PCSE00240/*.png

엔진은 새로 만들지 않고 기존 코드를 함수로 호출한다:
    - 실기   : apply_realhw_patch.patch(...)
    - Vita3K : apply_release_patch 의 apply_file_patch / install_textures / restore_originals
"""

from __future__ import annotations

import os
import sys
import threading
import queue
import traceback
from pathlib import Path

TITLE_ID = "PCSE00240"


class _NullStream:
    """console=False(PyInstaller --windowed) 빌드에서 sys.stdout/stderr 가 None 이라
    어디선가 print/traceback 이 호출되면 'NoneType has no attribute write' 로 크래시한다.
    앱 시작 시 None 스트림을 이 더미로 교체해 막는다."""

    def write(self, *_a, **_k):
        return 0

    def flush(self):
        pass


def _ensure_std_streams():
    if sys.stdout is None:
        sys.stdout = _NullStream()
    if sys.stderr is None:
        sys.stderr = _NullStream()


# ---------------------------------------------------------------------------
# 패키지 루트 / 모듈 경로 해석 (frozen exe·소스 양쪽 지원)
# ---------------------------------------------------------------------------
def _candidate_roots():
    cands = []
    if getattr(sys, "frozen", False):
        # PyInstaller: onedir 면 실행파일 폴더, onefile 이면 _MEIPASS 에 데이터가 풀림
        cands.append(Path(sys.executable).resolve().parent)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            cands.append(Path(meipass))
    here = Path(__file__).resolve()
    cands.append(here.parent)         # tools/ 자신 (드물게)
    cands.append(here.parent.parent)  # tools/ 의 부모 = 패키지 루트
    # 중복 제거(순서 보존)
    seen, out = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def resolve_pkg_root():
    """tools/ 와 translations/ 가 함께 있는 디렉토리를 패키지 루트로 본다.

    frozen exe(PyInstaller)는 데이터를 _MEIPASS(임시)가 아니라 exe 옆에 동봉한다.
    따라서 frozen 이면 exe 옆을 우선 확인한다(데이터 폴더 = translations 유무로 판정)."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "translations").is_dir():
            return exe_dir
    for c in _candidate_roots():
        if (c / "tools").is_dir() and (c / "translations").is_dir():
            return c
    # 폴백
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


PKG_ROOT = resolve_pkg_root()
TOOLS_DIR = PKG_ROOT / "tools"
if TOOLS_DIR.is_dir():
    sys.path.insert(0, str(TOOLS_DIR))
VITA3K_ASSETS = PKG_ROOT / "vita3k"


# ---------------------------------------------------------------------------
# 자동 탐지
# ---------------------------------------------------------------------------
def detect_vita3k_content_root():
    """Vita3K content root(ux0/app/PCSE00240/NinPri.cpk 가 있는 곳)를 찾는다."""
    try:
        import apply_release_patch as arp
        return str(arp.resolve_content_root(None, TITLE_ID))
    except Exception:
        return ""


def _cpk_dir_has_game(d: Path) -> bool:
    return (d / "NinPri.cpk").exists() and (d / "NinPriPatch.cpk").exists()


def detect_cpk_dir():
    """본편 CPK가 들어 있는 app/PCSE00240 폴더를 추정한다.

    1) Vita3K content root 아래 ux0/app/PCSE00240
    2) (Windows) 마운트된 드라이브의 [ux0/]app/PCSE00240 (실기 SD카드 직결 대비)
    """
    candidates = []
    cr = detect_vita3k_content_root()
    if cr:
        candidates.append(Path(cr) / "ux0" / "app" / TITLE_ID)

    if sys.platform == "win32":
        for letter in range(ord("D"), ord("Z") + 1):
            drive = Path(f"{chr(letter)}:\\")
            if drive.exists():
                candidates.append(drive / "app" / TITLE_ID)
                candidates.append(drive / "ux0" / "app" / TITLE_ID)
    elif sys.platform == "darwin":
        vols = Path("/Volumes")
        if vols.is_dir():
            try:
                for vol in vols.iterdir():
                    candidates.append(vol / "app" / TITLE_ID)
                    candidates.append(vol / "ux0" / "app" / TITLE_ID)
            except OSError:
                pass

    for d in candidates:
        try:
            if _cpk_dir_has_game(d):
                return d
        except OSError:
            # 빈 카드리더/오프라인 네트워크 드라이브 등 접근 실패는 건너뛴다
            continue
    return None


def detect_dlc_paths(cpk_dir: Path | None):
    """cpk_dir 옆 addcont 또는 같은 위치에서 DLC Pack1~4 cpk를 추정."""
    found = {f"Pack{i}": "" for i in range(1, 5)}
    if cpk_dir is None:
        return found
    # ux0/app/PCSE00240 -> ux0/addcont/PCSE00240/OBOROMURAMASAPKn/NinPriPackn.cpk
    try:
        ux0 = cpk_dir.parent.parent  # .../ux0
    except Exception:
        return found
    addcont = ux0 / "addcont" / TITLE_ID
    for i in range(1, 5):
        cand = addcont / f"OBOROMURAMASAPK{i}" / f"NinPriPack{i}.cpk"
        if cand.exists():
            found[f"Pack{i}"] = str(cand)
    return found


# ---------------------------------------------------------------------------
# 워커: 백그라운드 스레드에서 엔진 실행 + stdout 을 큐로 흘려보냄
# ---------------------------------------------------------------------------
class _QueueWriter:
    def __init__(self, q):
        self.q = q

    def write(self, s):
        if s:
            self.q.put(("log", s))

    def flush(self):
        pass


def _run_capturing(log_queue, fn):
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = _QueueWriter(log_queue)
    try:
        fn()
        log_queue.put(("done", None))
    except Exception:
        log_queue.put(("log", "\n" + traceback.format_exc()))
        log_queue.put(("error", None))
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def _install_xbutton_textures(arp, content_root):
    """Vita3K ✕ 버튼: ui_xbutton PNG를 import 폴더에 덮어쓴다(기존 ✕ 추가팩과 동일 방식)."""
    import shutil
    src = PKG_ROOT / "textures" / "kr" / "ui_xbutton"
    if not src.is_dir():
        return 0
    pngs = sorted(src.glob("*.png"))
    n = 0
    for base in arp.texture_import_roots(content_root):
        dest = base / "textures" / "import" / TITLE_ID
        dest.mkdir(parents=True, exist_ok=True)
        for png in pngs:
            shutil.copy2(png, dest / png.name)
            n += 1
    return n


def _remove_installed_textures(arp, asset_root, content_root):
    """복원: 우리가 설치한 import 텍스처(한글 + ✕버튼)를 import 폴더에서 제거한다.

    번들에 들어 있는 정확한 파일명만 지우므로, 사용자가 따로 둔 다른 텍스처는 건드리지 않는다.
    (단 우리가 HD 베이스 위에 오버레이한 폰트 텍스처는 같은 이름이라 제거된다 — HD팩 사용자는 재설치 필요.)"""
    names = set()
    for d in (asset_root / "textures" / "import" / TITLE_ID,
              PKG_ROOT / "textures" / "kr" / "ui_xbutton"):
        if d.is_dir():
            names |= {p.name for p in d.glob("*.png")}
    n = 0
    for base in arp.texture_import_roots(content_root):
        dest = base / "textures" / "import" / TITLE_ID
        for name in names:
            f = dest / name
            if f.exists():
                try:
                    f.unlink()
                    n += 1
                except OSError:
                    pass
    return n


def run_vita3k(log_queue, content_root, restore=False, enter_button="circle"):
    def job():
        import apply_release_patch as arp
        root = VITA3K_ASSETS if VITA3K_ASSETS.is_dir() else PKG_ROOT
        manifest = arp.load_manifest(root)
        cr = arp.resolve_content_root(content_root or None, TITLE_ID)
        print(f"Muramasa Korean Patch v{manifest['version']}")
        print(f"Vita3K content root: {cr}\n")
        if restore:
            n = arp.restore_originals(cr, manifest, False)
            removed = _remove_installed_textures(arp, root, cr)
            print(f"\n완료 — 원본 CPK {n}개 복원, import 텍스처 {removed}개 제거.")
            print("(HD 텍스처 팩을 쓰던 분은 팩을 다시 설치하세요.)")
            return
        for entry in manifest["files"]:
            print(arp.apply_file_patch(root, cr, manifest, entry, False))
        print(arp.install_textures(root, cr, TITLE_ID, False))
        if enter_button == "cross":
            n = _install_xbutton_textures(arp, cr)
            print(f"✕ 버튼 텍스처 {n}개 설치 — Vita3K 설정에서 Enter Button = Cross 로 맞추세요.")
        print("\n완료 — 폰트/UI 텍스처가 안 보이면 Vita3K 설정에서 GPU > Import Textures 를 켜세요.")

    threading.Thread(target=_run_capturing, args=(log_queue, job), daemon=True).start()


def run_realhw(log_queue, ninpri, ninpripatch, packs, out_dir, enter_button):
    def job():
        import apply_realhw_patch as arh
        arh.patch(ninpri, ninpripatch, packs, out_dir, enter_button)

    threading.Thread(target=_run_capturing, args=(log_queue, job), daemon=True).start()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
def launch_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext

    root = tk.Tk()
    root.title("Muramasa Rebirth 한글 패치 설치 도구")
    root.geometry("760x640")
    root.minsize(720, 600)

    log_queue: "queue.Queue" = queue.Queue()
    busy = {"running": False}

    mode_var = tk.StringVar(value="vita3k")
    enter_var = tk.StringVar(value="circle")
    restore_var = tk.BooleanVar(value=False)

    main = ttk.Frame(root, padding=12)
    main.pack(fill="both", expand=True)

    ttk.Label(main, text="Muramasa Rebirth 한글 패치", font=("", 15, "bold")).pack(anchor="w")
    ttk.Label(
        main,
        text="원본 CPK는 포함돼 있지 않습니다. 본인이 보유한 게임의 원본 파일로 패치를 만듭니다.",
        foreground="#555",
    ).pack(anchor="w", pady=(0, 8))

    # --- 모드 선택 ---------------------------------------------------------
    mode_box = ttk.LabelFrame(main, text="설치 대상", padding=8)
    mode_box.pack(fill="x", pady=4)
    ttk.Radiobutton(mode_box, text="Vita3K 에뮬레이터", value="vita3k",
                    variable=mode_var, command=lambda: _switch()).pack(side="left", padx=6)
    ttk.Radiobutton(mode_box, text="실기 PS Vita (rePatch)", value="realhw",
                    variable=mode_var, command=lambda: _switch()).pack(side="left", padx=6)

    # --- Vita3K 패널 -------------------------------------------------------
    v3k = ttk.LabelFrame(main, text="Vita3K 설정", padding=8)
    v3k_root = tk.StringVar()
    rowv = ttk.Frame(v3k); rowv.pack(fill="x", pady=2)
    ttk.Label(rowv, text="Vita3K 경로:", width=14).pack(side="left")
    ttk.Entry(rowv, textvariable=v3k_root).pack(side="left", fill="x", expand=True, padx=4)
    ttk.Button(rowv, text="찾아보기",
               command=lambda: _pick_dir(v3k_root)).pack(side="left")
    ttk.Checkbutton(v3k, text="원본으로 복원 (패치 되돌리기)",
                    variable=restore_var).pack(anchor="w", pady=(4, 0))
    ttk.Label(v3k, text="비워두면 자동으로 찾습니다. 폰트/UI가 안 보이면 Vita3K의 Import Textures 옵션을 켜세요.",
              foreground="#777").pack(anchor="w")

    # --- 실기 패널 ---------------------------------------------------------
    rhw = ttk.LabelFrame(main, text="실기 PS Vita 설정", padding=8)
    ninpri_var = tk.StringVar()
    ninpripatch_var = tk.StringVar()
    pack_vars = {f"Pack{i}": tk.StringVar() for i in range(1, 5)}
    out_var = tk.StringVar()

    def _file_row(parent, label, var, optional=False):
        r = ttk.Frame(parent); r.pack(fill="x", pady=2)
        ttk.Label(r, text=label, width=16).pack(side="left")
        ttk.Entry(r, textvariable=var).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(r, text="찾아보기",
                   command=lambda: _pick_file(var)).pack(side="left")

    _file_row(rhw, "NinPri.cpk:", ninpri_var)
    _file_row(rhw, "NinPriPatch.cpk:", ninpripatch_var)
    for i in range(1, 5):
        _file_row(rhw, f"DLC Pack{i} (선택):", pack_vars[f"Pack{i}"])
    ro = ttk.Frame(rhw); ro.pack(fill="x", pady=2)
    ttk.Label(ro, text="결과 저장 폴더:", width=16).pack(side="left")
    ttk.Entry(ro, textvariable=out_var).pack(side="left", fill="x", expand=True, padx=4)
    ttk.Button(ro, text="찾아보기", command=lambda: _pick_dir(out_var)).pack(side="left")
    ttk.Label(rhw, text="생성된 ux0 폴더를 Vita의 ux0:/ 아래에 복사하고 rePatch 플러그인을 켜세요.",
              foreground="#777").pack(anchor="w", pady=(2, 0))

    # --- 공통: 결정 버튼 ---------------------------------------------------
    btn_box = ttk.LabelFrame(main, text="결정 버튼 표시", padding=8)
    btn_box.pack(fill="x", pady=4)
    ttk.Radiobutton(btn_box, text="○ 버튼 (기본)", value="circle",
                    variable=enter_var).pack(side="left", padx=6)
    ttk.Radiobutton(btn_box, text="✕ 버튼 (Vita 설정 Enter=Cross 필요)", value="cross",
                    variable=enter_var).pack(side="left", padx=6)

    # --- 실행/진행 --------------------------------------------------------
    action = ttk.Frame(main); action.pack(fill="x", pady=6)
    run_btn = ttk.Button(action, text="패치 시작", command=lambda: _start())
    run_btn.pack(side="left")
    prog = ttk.Progressbar(action, mode="indeterminate")
    prog.pack(side="left", fill="x", expand=True, padx=10)

    log = scrolledtext.ScrolledText(main, height=12, state="disabled", wrap="word")
    log.pack(fill="both", expand=True, pady=(4, 0))

    # --- 헬퍼 -------------------------------------------------------------
    def _pick_file(var):
        p = filedialog.askopenfilename(filetypes=[("CPK", "*.cpk"), ("모든 파일", "*.*")])
        if p:
            var.set(p)

    def _pick_dir(var):
        p = filedialog.askdirectory()
        if p:
            var.set(p)

    def _append(text):
        log.configure(state="normal")
        log.insert("end", text)
        log.see("end")
        log.configure(state="disabled")

    def _switch():
        if mode_var.get() == "vita3k":
            rhw.pack_forget()
            v3k.pack(fill="x", pady=4, after=mode_box)
        else:
            v3k.pack_forget()
            rhw.pack(fill="x", pady=4, after=mode_box)

    def _autodetect():
        # Vita3K
        cr = detect_vita3k_content_root()
        if cr:
            v3k_root.set(cr)
        # 실기 CPK
        cpk_dir = detect_cpk_dir()
        if cpk_dir:
            ninpri_var.set(str(cpk_dir / "NinPri.cpk"))
            ninpripatch_var.set(str(cpk_dir / "NinPriPatch.cpk"))
            for key, p in detect_dlc_paths(cpk_dir).items():
                if p:
                    pack_vars[key].set(p)
        # 기본 출력 폴더 = 바탕화면/MuramasaPatchOut
        desktop = Path.home() / "Desktop"
        base = desktop if desktop.is_dir() else Path.home()
        out_var.set(str(base / "MuramasaPatchOut"))

    def _set_busy(b):
        busy["running"] = b
        run_btn.configure(state="disabled" if b else "normal")
        if b:
            prog.start(12)
        else:
            prog.stop()

    def _start():
        if busy["running"]:
            return
        log.configure(state="normal"); log.delete("1.0", "end"); log.configure(state="disabled")
        if mode_var.get() == "vita3k":
            _set_busy(True)
            run_vita3k(log_queue, v3k_root.get().strip(), restore_var.get(), enter_var.get())
        else:
            ninpri = ninpri_var.get().strip()
            ninpripatch = ninpripatch_var.get().strip()
            if not (ninpri and os.path.exists(ninpri)) or not (ninpripatch and os.path.exists(ninpripatch)):
                messagebox.showerror("경로 오류", "NinPri.cpk 와 NinPriPatch.cpk 경로를 올바르게 지정하세요.")
                return
            bad = [k for k, v in pack_vars.items()
                   if v.get().strip() and not os.path.exists(v.get().strip())]
            if bad:
                messagebox.showerror("DLC 경로 오류",
                                     f"{', '.join(bad)} 경로의 파일을 찾을 수 없습니다.\n경로를 고치거나 비워 두세요.")
                return
            out_dir = out_var.get().strip() or str(Path.home() / "MuramasaPatchOut")
            packs = {k: (v.get().strip() or None) for k, v in pack_vars.items()}
            _set_busy(True)
            run_realhw(log_queue, ninpri, ninpripatch, packs, out_dir, enter_var.get())

    def _poll():
        try:
            while True:
                kind, payload = log_queue.get_nowait()
                if kind == "log":
                    _append(payload)
                elif kind == "done":
                    _set_busy(False)
                    if mode_var.get() == "realhw":
                        msg = ("패치 완료. 결과 저장 폴더 안의 'ux0' 폴더를 PS Vita 본체의 ux0:/ 아래에 "
                               "그대로 복사한 뒤, rePatch 플러그인을 켜고 게임을 실행하세요.")
                    else:
                        msg = "패치 완료. Vita3K 를 실행하면 한글이 표시됩니다."
                    _append("\n\n✅ " + msg + "\n")
                    messagebox.showinfo("완료", msg)
                elif kind == "error":
                    _set_busy(False)
                    _append("\n\n❌ 오류로 중단되었습니다. 위 로그를 확인하세요.\n")
                    messagebox.showerror("오류", "패치 중 오류가 발생했습니다. 로그를 확인하세요.")
        except queue.Empty:
            pass
        root.after(100, _poll)

    def _on_close():
        if busy["running"]:
            if not messagebox.askyesno(
                "종료 확인",
                "패치가 진행 중입니다. 지금 닫으면 패치가 중단됩니다.\n그래도 닫을까요?",
            ):
                return
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    _switch()
    root.after(100, _poll)
    # 창을 먼저 띄운 뒤 탐지(드라이브 스캔 지연이 시작 프리징으로 보이지 않게)
    root.after(50, _autodetect)
    root.mainloop()


def main():
    # console=False(--windowed) 빌드에서 stdout/stderr=None 크래시 방지
    _ensure_std_streams()
    try:
        launch_gui()
    except Exception:
        # GUI 환경이 아닐 때(헤드리스 등)는 에러를 표면화
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
