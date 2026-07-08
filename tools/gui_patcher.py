#!/usr/bin/env python3
"""Muramasa Rebirth 한글 패치 — 통합 GUI 설치 도구 (Vita3K 에뮬레이터 + 실기 PS Vita).

Tkinter 기반 단일 창. 입력은 항상 "Vita3K 설치 폴더"(복호화된 원본 CPK의 유일한
출처) 하나이고, 출력만 에뮬레이터/실기로 분기한다. 실기 본체의 앱 데이터는 암호화돼
직접 쓸 수 없으므로, 사용자는 CPK 파일을 직접 찾을 필요 없이 Vita3K 폴더만 고르면 된다.
  - 에뮬레이터: 그 Vita3K에 바로 설치(바이너리 패치 + import 텍스처, HD 보존)
  - 실기: 복호화 CPK에서 베이크 → ux0/rePatch + ux0/reAddcont 폴더 생성(→ Vita SD로 복사)

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
# 엔진 모듈(apply_realhw_patch/realhw_bake/realhw_font_bake/font_mapping)이 데이터 루트를
# __file__ 기준으로 잡으면 frozen exe 에서 빗나간다. 올바른 패키지 루트를 env 로 넘긴다.
os.environ["MURAMASA_ROOT"] = str(PKG_ROOT)


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


def detect_cpk_dir_from_root(root_str: str):
    """Vita3K 폴더(빈 값=기본 위치 자동)에서 app/PCSE00240 CPK 폴더를 해석.

    실기 흐름은 '복호화된' CPK만 써야 하므로, 암호화된 실기 SD카드를 잡을 수 있는
    드라이브 스캔을 쓰지 않고 Vita3K 설치(resolve_content_root)만 본다. 이 결과는
    run_realhw 의 resolve_cpks_from_vita3k 와 동일 경로로 해석돼 항상 일치한다."""
    try:
        import apply_release_patch as arp
        cr = arp.resolve_content_root(root_str or None, TITLE_ID)
    except Exception:
        return None
    d = Path(cr) / "ux0" / "app" / TITLE_ID
    return d if _cpk_dir_has_game(d) else None


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
    except SystemExit as e:
        # 엔진은 검증 실패 시 SystemExit(메시지)로 중단한다(예: ASCII 검증, CPK 매직).
        # SystemExit 는 Exception 이 아니므로 따로 잡지 않으면 스레드가 조용히 죽어 GUI가 멈춘다.
        log_queue.put(("log", "\n" + (str(e) or "작업이 중단되었습니다.") + "\n"))
        log_queue.put(("error", None))
    except Exception:
        log_queue.put(("log", "\n" + traceback.format_exc()))
        log_queue.put(("error", None))
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def _install_xbutton_textures(arp, content_root, user_path=None):
    """Vita3K ✕ 버튼: ui_xbutton PNG를 import 폴더에 덮어쓴다(기존 ✕ 추가팩과 동일 방식)."""
    import shutil
    src = PKG_ROOT / "textures" / "kr" / "ui_xbutton"
    if not src.is_dir():
        return 0
    pngs = sorted(src.glob("*.png"))
    n = 0
    for base in arp.texture_import_roots(content_root, user_path):
        dest = base / "textures" / "import" / TITLE_ID
        dest.mkdir(parents=True, exist_ok=True)
        for png in pngs:
            shutil.copy2(png, dest / png.name)
            n += 1
    return n


def _remove_installed_textures(arp, asset_root, content_root, user_path=None):
    """복원: 우리가 설치한 import 텍스처(한글 + ✕버튼)를 import 폴더에서 제거한다.

    번들에 들어 있는 정확한 파일명만 지우므로, 사용자가 따로 둔 다른 텍스처는 건드리지 않는다.
    (단 우리가 HD 베이스 위에 오버레이한 폰트 텍스처는 같은 이름이라 제거된다 — HD팩 사용자는 재설치 필요.)"""
    names = set()
    for d in (asset_root / "textures" / "import" / TITLE_ID,
              PKG_ROOT / "textures" / "kr" / "ui_xbutton"):
        if d.is_dir():
            names |= {p.name for p in d.glob("*.png")}
    n = 0
    for base in arp.texture_import_roots(content_root, user_path):
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
    user_path = content_root or None  # 사용자가 입력한 Vita3K 폴더(비면 자동)

    def job():
        import apply_release_patch as arp
        root = VITA3K_ASSETS if VITA3K_ASSETS.is_dir() else PKG_ROOT
        manifest = arp.load_manifest(root)
        cr = arp.resolve_content_root(user_path, TITLE_ID)
        print(f"Muramasa Korean Patch v{manifest['version']}")
        print(f"Vita3K 게임(ux0) 폴더: {cr}\n")
        if restore:
            n = arp.restore_originals(cr, manifest, False)
            removed = _remove_installed_textures(arp, root, cr, user_path)
            print(f"\n완료 — 원본 CPK {n}개 복원, import 텍스처 {removed}개 제거.")
            print("(HD 텍스처 팩을 쓰던 분은 팩을 다시 설치하세요.)")
            return
        for entry in manifest["files"]:
            print(arp.apply_file_patch(root, cr, manifest, entry, False))
        print(arp.install_textures(root, cr, TITLE_ID, False, user_path))
        if enter_button == "cross":
            n = _install_xbutton_textures(arp, cr, user_path)
            print(f"✕ 버튼 텍스처 {n}개 설치 — Vita3K 설정에서 Enter Button = Cross 로 맞추세요.")
        print("\n완료 — 폰트/UI 텍스처가 안 보이면 Vita3K 설정에서 GPU > Import Textures 를 켜세요.")
        if sys.platform == "win32" and not user_path:
            print(
                "\n[안내] Windows Vita3K 는 텍스처를 보통 'Vita3K.exe 가 있는 폴더'에서 읽습니다.\n"
                "  게임은 한글이 나오는데 UI/폰트만 안 바뀌면, 위 'Vita3K 경로'에\n"
                "  Vita3K.exe 가 있는 폴더를 지정하고 다시 '패치 시작' 을 누르세요.")

    threading.Thread(target=_run_capturing, args=(log_queue, job), daemon=True).start()


def run_realhw(log_queue, vita3k_root, out_dir, enter_button):
    """실기용 파일 생성: Vita3K 설치 폴더의 복호화 CPK에서 베이크 → ux0/rePatch+reAddcont."""
    def job():
        import apply_realhw_patch as arh
        ninpri, ninpripatch, packs = arh.resolve_cpks_from_vita3k(vita3k_root or None)
        print("Vita3K 복호화 CPK 사용:")
        print(f"  {ninpri}")
        print(f"  {ninpripatch}")
        found = [k for k, v in packs.items() if v]
        print(f"  DLC: {', '.join(found) if found else '(없음 — 본편만 패치)'}\n")
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
        text="원본 CPK는 포함돼 있지 않습니다. Vita3K에 설치된(=복호화된) 게임 파일로 패치를 만듭니다.",
        foreground="#555",
    ).pack(anchor="w", pady=(0, 8))

    # --- 공유 입력: Vita3K 설치 폴더 ---------------------------------------
    # 실기 본체의 앱 데이터는 암호화돼 직접 못 쓰므로, 복호화된 원본 CPK의 유일한
    # 출처인 Vita3K 설치 폴더를 입력으로 받는다(에뮬/실기 공통).
    src_box = ttk.LabelFrame(main, text="① 원본 위치 — Vita3K 설치 폴더", padding=8)
    src_box.pack(fill="x", pady=4)
    v3k_root = tk.StringVar()
    rowv = ttk.Frame(src_box); rowv.pack(fill="x", pady=2)
    ttk.Label(rowv, text="Vita3K 경로:", width=12).pack(side="left")
    ttk.Entry(rowv, textvariable=v3k_root).pack(side="left", fill="x", expand=True, padx=4)
    ttk.Button(rowv, text="찾아보기",
               command=lambda: _pick_dir(v3k_root)).pack(side="left")
    ttk.Label(src_box,
              text="비워두면 자동으로 찾습니다. (게임이 Vita3K에 설치돼 있어야 합니다.)\n"
                   "※ 한글이 일부만 적용되면 Vita3K.exe 가 있는 폴더를 직접 지정하세요 "
                   "— Windows 는 텍스처를 exe 폴더에서 읽습니다.",
              foreground="#777", justify="left").pack(anchor="w")

    # --- 설치 대상 선택 ----------------------------------------------------
    mode_box = ttk.LabelFrame(main, text="② 설치 대상", padding=8)
    mode_box.pack(fill="x", pady=4)
    ttk.Radiobutton(mode_box, text="Vita3K 에뮬레이터 (이 PC)", value="vita3k",
                    variable=mode_var, command=lambda: _switch()).pack(side="left", padx=6)
    ttk.Radiobutton(mode_box, text="실기 PS Vita (rePatch)", value="realhw",
                    variable=mode_var, command=lambda: _switch()).pack(side="left", padx=6)

    # --- Vita3K(에뮬) 패널 -------------------------------------------------
    v3k = ttk.LabelFrame(main, text="Vita3K 에뮬레이터 설정", padding=8)
    ttk.Checkbutton(v3k, text="원본으로 복원 (패치 되돌리기)",
                    variable=restore_var).pack(anchor="w", pady=(0, 0))
    ttk.Label(v3k, text="위 Vita3K 폴더에 바로 설치합니다. 폰트/UI가 안 보이면 Vita3K의 "
                        "GPU > Import Textures 옵션을 켜고 재시작하세요.",
              foreground="#777").pack(anchor="w")

    # --- 실기 패널 ---------------------------------------------------------
    rhw = ttk.LabelFrame(main, text="실기 PS Vita 설정", padding=8)
    out_var = tk.StringVar()
    ttk.Label(rhw, text="원본 CPK는 위 Vita3K 폴더에서 자동으로 읽습니다 (복호화된 파일).",
              foreground="#555").pack(anchor="w", pady=(0, 4))
    ro = ttk.Frame(rhw); ro.pack(fill="x", pady=2)
    ttk.Label(ro, text="결과 저장 폴더:", width=12).pack(side="left")
    ttk.Entry(ro, textvariable=out_var).pack(side="left", fill="x", expand=True, padx=4)
    ttk.Button(ro, text="찾아보기", command=lambda: _pick_dir(out_var)).pack(side="left")
    ttk.Label(rhw, text="생성된 ux0 폴더를 Vita의 ux0:/ 아래에 복사하고 rePatch 플러그인을 켜세요. "
                        "(DLC는 Vita3K에 설치돼 있으면 함께 패치됩니다.)",
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
        # Vita3K 설치 폴더(복호화 CPK의 출처) 자동 탐지
        cr = detect_vita3k_content_root()
        if cr:
            v3k_root.set(cr)
        # 실기 결과 기본 출력 폴더 = 바탕화면/MuramasaPatchOut
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
            # 실기: 위 Vita3K 폴더에서 복호화 CPK를 자동 해석한다.
            cpk_dir = detect_cpk_dir_from_root(v3k_root.get().strip())
            if cpk_dir is None:
                messagebox.showerror(
                    "원본을 찾지 못함",
                    "Vita3K 설치 폴더에서 NinPri.cpk / NinPriPatch.cpk 를 찾지 못했습니다.\n"
                    "① 위에서 올바른 Vita3K 폴더를 지정했는지,\n"
                    "② 게임이 Vita3K에 설치돼 있는지 확인하세요.")
                return
            out_dir = out_var.get().strip() or str(Path.home() / "MuramasaPatchOut")
            _set_busy(True)
            run_realhw(log_queue, v3k_root.get().strip(), out_dir, enter_var.get())

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
