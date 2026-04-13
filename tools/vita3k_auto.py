"""
Vita3K 에뮬레이터 자동화 스크립트
- Vita3K 실행 및 게임 로드
- 스크린샷 캡처 (윈도우 단위)
- 키 입력 자동화
- 테스트 파이프라인

pip install:
    pip install pyautogui pillow pywin32

사용법:
    python tools/vita3k_auto.py                # 기본 테스트 파이프라인 실행
    python tools/vita3k_auto.py --screenshot   # 스크린샷만 찍기
    python tools/vita3k_auto.py --run-only     # 게임 실행만
"""

import argparse
import ctypes
import ctypes.wintypes
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pyautogui
import win32gui
import win32con
import win32ui
from PIL import Image

# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

VITA3K_EXE = r"C:\game\vita3k\Vita3K.exe"
GAME_TITLE_ID = "PCSE00240"
GAME_PATH = rf"C:\game\vita3k\ux0\app\{GAME_TITLE_ID}"

SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "screenshots"

# Vita3K 윈도우를 찾을 때 사용할 키워드 (윈도우 타이틀에 포함)
WINDOW_KEYWORDS = ["Vita3K", "Muramasa"]

# Vita3K 기본 키매핑 (키보드 -> PS Vita 버튼)
# https://vita3k.org/ 기본 설정 기준
VITA_KEYMAP = {
    "cross": "z",        # X 버튼 (결정)
    "circle": "x",       # O 버튼 (취소)
    "square": "a",       # □ 버튼
    "triangle": "s",     # △ 버튼
    "start": "enter",    # Start
    "select": "backspace",  # Select
    "up": "up",          # D-Pad 위
    "down": "down",      # D-Pad 아래
    "left": "left",      # D-Pad 왼쪽
    "right": "right",    # D-Pad 오른쪽
    "l_trigger": "q",    # L 트리거
    "r_trigger": "e",    # R 트리거
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("vita3k_auto")

# ---------------------------------------------------------------------------
# 윈도우 핸들 유틸리티
# ---------------------------------------------------------------------------


def find_vita3k_window() -> int | None:
    """Vita3K 윈도우 핸들(HWND)을 찾아 반환한다. 없으면 None."""
    result = []

    def _enum_cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        for kw in WINDOW_KEYWORDS:
            if kw.lower() in title.lower():
                result.append(hwnd)
                return True
        return True

    win32gui.EnumWindows(_enum_cb, None)
    if result:
        return result[0]
    return None


def wait_for_window(timeout: float = 60, poll: float = 2) -> int:
    """Vita3K 윈도우가 나타날 때까지 대기. 타임아웃 시 RuntimeError."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        hwnd = find_vita3k_window()
        if hwnd:
            log.info("Vita3K 윈도우 발견: hwnd=0x%X  title='%s'",
                     hwnd, win32gui.GetWindowText(hwnd))
            return hwnd
        time.sleep(poll)
    raise RuntimeError(f"Vita3K 윈도우를 {timeout}초 안에 찾지 못했습니다.")


def bring_to_front(hwnd: int):
    """윈도우를 포그라운드로 가져온다."""
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.3)

# ---------------------------------------------------------------------------
# 에뮬레이터 실행
# ---------------------------------------------------------------------------


def launch_vita3k(wait: bool = True, timeout: float = 60) -> subprocess.Popen:
    """Vita3K를 실행하고 게임을 로드한다."""
    if not os.path.isfile(VITA3K_EXE):
        raise FileNotFoundError(f"Vita3K 실행 파일을 찾을 수 없습니다: {VITA3K_EXE}")

    cmd = [VITA3K_EXE, GAME_PATH]
    log.info("Vita3K 실행: %s", " ".join(cmd))
    proc = subprocess.Popen(cmd)

    if wait:
        wait_for_window(timeout=timeout)

    return proc

# ---------------------------------------------------------------------------
# 스크린샷
# ---------------------------------------------------------------------------


def capture_window(hwnd: int) -> Image.Image:
    """Win32 API로 특정 윈도우의 클라이언트 영역을 캡처하여 PIL Image로 반환."""
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    w = right - left
    h = bottom - top

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
    save_dc.SelectObject(bitmap)

    # PrintWindow 로 캡처 (PW_CLIENTONLY=1, PW_RENDERFULLCONTENT=2)
    ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)

    bmp_info = bitmap.GetInfo()
    bmp_bits = bitmap.GetBitmapBits(True)

    img = Image.frombuffer(
        "RGB",
        (bmp_info["bmWidth"], bmp_info["bmHeight"]),
        bmp_bits,
        "raw",
        "BGRX",
        0,
        1,
    )

    # 정리
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)
    win32gui.DeleteObject(bitmap.GetHandle())

    return img


def take_screenshot(hwnd: int, tag: str = "") -> Path:
    """스크린샷을 찍어 screenshots/ 폴더에 저장하고 경로를 반환."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    img = capture_window(hwnd)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{tag}" if tag else ""
    filename = f"vita3k_{ts}{suffix}.png"
    filepath = SCREENSHOT_DIR / filename
    img.save(filepath)
    log.info("스크린샷 저장: %s (%dx%d)", filepath, img.width, img.height)
    return filepath

# ---------------------------------------------------------------------------
# 키 입력
# ---------------------------------------------------------------------------


def send_key(hwnd: int, vita_button: str, hold: float = 0.1):
    """Vita 버튼 이름으로 키 입력을 전송한다.

    vita_button: VITA_KEYMAP의 키 (예: 'cross', 'up', 'start')
    """
    key = VITA_KEYMAP.get(vita_button)
    if key is None:
        raise ValueError(
            f"알 수 없는 버튼: {vita_button}. "
            f"사용 가능: {list(VITA_KEYMAP.keys())}"
        )

    bring_to_front(hwnd)
    log.info("키 입력: %s -> '%s' (hold=%.2fs)", vita_button, key, hold)
    pyautogui.keyDown(key)
    time.sleep(hold)
    pyautogui.keyUp(key)


def send_keys_sequence(hwnd: int, sequence: list[tuple[str, float]], gap: float = 0.3):
    """버튼 시퀀스를 차례로 입력한다.

    sequence: [(vita_button, hold_time), ...]
    gap: 각 입력 사이 대기 시간(초)
    """
    bring_to_front(hwnd)
    for btn, hold in sequence:
        send_key(hwnd, btn, hold=hold)
        time.sleep(gap)

# ---------------------------------------------------------------------------
# 테스트 파이프라인
# ---------------------------------------------------------------------------


def run_pipeline(
    capture_interval: float = 5.0,
    capture_count: int = 5,
    key_sequence: list[tuple[str, float]] | None = None,
):
    """기본 테스트 파이프라인.

    1. Vita3K 실행 & 게임 로드
    2. 초기 대기 (게임 로딩)
    3. 스크린샷 -> 키 입력 -> 스크린샷 반복
    """
    if key_sequence is None:
        # 기본 시퀀스: 시작 화면에서 X 버튼 몇 번 누르기
        key_sequence = [
            ("cross", 0.1),
            ("cross", 0.1),
            ("cross", 0.1),
        ]

    log.info("=" * 60)
    log.info("Vita3K 자동화 파이프라인 시작")
    log.info("=" * 60)

    # 1) 실행
    proc = launch_vita3k(wait=True, timeout=90)
    hwnd = find_vita3k_window()
    if hwnd is None:
        log.error("윈도우를 찾을 수 없습니다.")
        return

    # 2) 게임 로딩 대기
    log.info("게임 로딩 대기 (15초)...")
    time.sleep(15)

    # 3) 반복: 스크린샷 -> 키입력 -> 대기
    for i in range(capture_count):
        log.info("--- 사이클 %d/%d ---", i + 1, capture_count)

        # 스크린샷 (키 입력 전)
        take_screenshot(hwnd, tag=f"cycle{i+1}_before")

        # 키 시퀀스 전송
        send_keys_sequence(hwnd, key_sequence, gap=0.4)

        # 잠시 대기 후 스크린샷 (키 입력 후)
        time.sleep(1.0)
        take_screenshot(hwnd, tag=f"cycle{i+1}_after")

        # 다음 사이클 전 대기
        if i < capture_count - 1:
            time.sleep(capture_interval)

    log.info("=" * 60)
    log.info("파이프라인 완료. 스크린샷: %s", SCREENSHOT_DIR)
    log.info("=" * 60)

    return proc

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Vita3K 에뮬레이터 자동화")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--run-only", action="store_true",
                       help="게임 실행만 (자동화 없음)")
    group.add_argument("--screenshot", action="store_true",
                       help="이미 실행 중인 Vita3K의 스크린샷만 찍기")
    parser.add_argument("--interval", type=float, default=5.0,
                        help="스크린샷 간격 (초, 기본 5)")
    parser.add_argument("--count", type=int, default=5,
                        help="캡처 사이클 횟수 (기본 5)")
    args = parser.parse_args()

    if args.run_only:
        proc = launch_vita3k(wait=True)
        log.info("게임 실행 완료. PID=%d", proc.pid)
        log.info("Ctrl+C 로 종료하세요.")
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()

    elif args.screenshot:
        hwnd = find_vita3k_window()
        if hwnd is None:
            log.error("실행 중인 Vita3K 윈도우를 찾을 수 없습니다.")
            sys.exit(1)
        path = take_screenshot(hwnd, tag="manual")
        log.info("저장 완료: %s", path)

    else:
        run_pipeline(
            capture_interval=args.interval,
            capture_count=args.count,
        )


if __name__ == "__main__":
    main()
