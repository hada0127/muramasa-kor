from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import math
import shutil
import subprocess
import time
from pathlib import Path

import mss
import mss.tools
import numpy as np
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
VITA3K_APP = Path(r"C:\game\vita3k\ux0\app\PCSE00240")
VITA3K_IMPORT = Path(r"C:\game\vita3k\textures\import\PCSE00240")
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
SCANCODE_X = 45
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
user32 = ctypes.windll.user32


def find_vita3k_window() -> tuple[int, wt.RECT] | None:
    matches: list[int] = []

    def cb(hwnd: int, lparam: int) -> bool:
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if "Vita3K" in buf.value:
                matches.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(cb), 0)
    if not matches:
        return None
    hwnd = matches[0]
    rect = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return hwnd, rect


def focus_window(hwnd: int, rect: wt.RECT) -> None:
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    x = (rect.left + rect.right) // 2
    y = (rect.top + rect.bottom) // 2
    user32.SetCursorPos(x, y)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.3)


def press_scancode(scancode: int, hold: float = 0.08) -> None:
    user32.keybd_event(0, scancode, KEYEVENTF_SCANCODE, 0)
    time.sleep(hold)
    user32.keybd_event(0, scancode, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0)


def capture_frames(rect: wt.RECT, out_dir: Path, frames: int, interval: float) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    shot_paths: list[Path] = []
    monitor = {
        "left": rect.left,
        "top": rect.top,
        "width": rect.right - rect.left,
        "height": rect.bottom - rect.top,
    }
    with mss.mss() as sct:
        for idx in range(frames):
            img = sct.grab(monitor)
            path = out_dir / f"cap_{idx:02d}.png"
            mss.tools.to_png(img.rgb, img.size, output=str(path))
            shot_paths.append(path)
            time.sleep(interval)
    return shot_paths


def grab_array(rect: wt.RECT) -> np.ndarray:
    monitor = {
        "left": rect.left,
        "top": rect.top,
        "width": rect.right - rect.left,
        "height": rect.bottom - rect.top,
    }
    with mss.mss() as sct:
        img = sct.grab(monitor)
        arr = np.frombuffer(img.rgb, dtype=np.uint8)
        return arr.reshape((img.height, img.width, 3))


def looks_like_split_title(arr: np.ndarray) -> bool:
    flat = arr.reshape((-1, 3))
    white_ratio = float(np.mean(np.all(flat > 170, axis=1)))
    dark_ratio = float(np.mean(np.all(flat < 45, axis=1)))
    return white_ratio > 0.28 and dark_ratio < 0.42


def wait_for_split_title(rect: wt.RECT, timeout: float) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        arr = grab_array(rect)
        if looks_like_split_title(arr):
            time.sleep(0.4)
            return
        time.sleep(0.5)
    raise TimeoutError("split title was not detected in time")


def make_contact_sheet(paths: list[Path], out_path: Path, columns: int = 4) -> None:
    images = [Image.open(path).convert("RGB") for path in paths]
    if not images:
        return
    thumb_w = 320
    scale = thumb_w / images[0].width
    thumb_h = max(1, int(images[0].height * scale))
    rows = math.ceil(len(images) / columns)
    canvas = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + 24)), (24, 24, 24))
    draw = ImageDraw.Draw(canvas)
    for idx, image in enumerate(images):
        thumb = image.resize((thumb_w, thumb_h), Image.Resampling.BILINEAR)
        col = idx % columns
        row = idx // columns
        x = col * thumb_w
        y = row * (thumb_h + 24)
        canvas.paste(thumb, (x, y))
        draw.text((x + 8, y + thumb_h + 2), f"{idx:02d}", fill=(255, 255, 255))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def ensure_cpk(exp_dir: Path, cpk_path: Path) -> None:
    if cpk_path.exists():
        return
    subprocess.run(
        [
            "python",
            "tools/cpk_patch.py",
            "backup/NinPri.cpk",
            str(exp_dir),
            str(cpk_path),
            "--append",
        ],
        cwd=ROOT,
        check=True,
    )


def install_experiment(exp_dir: Path) -> tuple[Path, Path]:
    cpk_path = exp_dir.with_suffix(".cpk")
    ensure_cpk(exp_dir, cpk_path)
    texture_path = exp_dir / "79C935AA47DD1810.png"
    if not texture_path.exists():
        raise FileNotFoundError(texture_path)
    shutil.copy2(cpk_path, VITA3K_APP / "NinPri.cpk")
    VITA3K_IMPORT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(texture_path, VITA3K_IMPORT / texture_path.name)
    return cpk_path, texture_path


def launch_game() -> None:
    subprocess.run(["python", "tools/vita3k_ctrl.py", "run"], cwd=ROOT, check=True)


def close_game() -> None:
    subprocess.run(["python", "tools/vita3k_ctrl.py", "close"], cwd=ROOT, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--capture-dir", required=True)
    ap.add_argument("--contact", required=True)
    ap.add_argument("--startup-wait", type=float, default=14.0)
    ap.add_argument("--title-detect-timeout", type=float, default=18.0)
    ap.add_argument("--post-press-wait", type=float, default=0.25)
    ap.add_argument("--frames", type=int, default=18)
    ap.add_argument("--interval", type=float, default=0.5)
    ap.add_argument("--keep-open", action="store_true")
    args = ap.parse_args()

    exp_dir = Path(args.experiment)
    install_experiment(exp_dir)
    launch_game()
    found = find_vita3k_window()
    if not found:
        raise RuntimeError("Vita3K window not found after launch")
    hwnd, rect = found
    focus_window(hwnd, rect)
    time.sleep(args.startup_wait)
    wait_for_split_title(rect, args.title_detect_timeout)
    focus_window(hwnd, rect)
    press_scancode(SCANCODE_X)
    time.sleep(args.post_press_wait)
    shots = capture_frames(rect, Path(args.capture_dir), args.frames, args.interval)
    make_contact_sheet(shots, Path(args.contact))
    if not args.keep_open:
        close_game()


if __name__ == "__main__":
    main()
