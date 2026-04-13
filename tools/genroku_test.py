#!/usr/bin/env python3
"""
Genroku Legends episode 1 auto-navigator for dialogue (scemsg) testing.
Navigates from title screen to first dialogue scene and takes screenshots.

Usage:
    python tools/genroku_test.py              # Navigate and screenshot
    python tools/genroku_test.py --from-game  # Skip to navigation (game already running)
"""
import pyautogui, time, ctypes, ctypes.wintypes as wt, mss, mss.tools, sys, os
from PIL import Image
import numpy as np

pyautogui.FAILSAFE = False
user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

# Scancode-based input for Vita3K
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
SCANCODES = {
    'x': 45,       # Cross (confirm)
    'z': 44,       # Circle (cancel)
    'right': 77,   # D-Pad right
    'left': 75,    # D-Pad left
    'up': 72,      # D-Pad up
    'down': 80,    # D-Pad down
    'enter': 28,   # Start
}


def press_key(name, hold=0.1):
    """Press a key using scancode for Vita3K."""
    sc = SCANCODES[name]
    flags = KEYEVENTF_SCANCODE
    if sc in (72, 75, 77, 80):  # extended keys (arrows)
        flags |= 0x0001  # KEYEVENTF_EXTENDEDKEY
    ctypes.windll.user32.keybd_event(0, sc, flags, 0)
    time.sleep(hold)
    ctypes.windll.user32.keybd_event(0, sc, flags | KEYEVENTF_KEYUP, 0)


def find_vita3k():
    wins = []
    def cb(h, l):
        if user32.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, b, 256)
            if 'Vita3K' in b.value:
                wins.append(h)
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    if wins:
        h = wins[0]
        r = wt.RECT()
        user32.GetWindowRect(h, ctypes.byref(r))
        return h, r
    return None, None


def get_title(h):
    b = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(h, b, 256)
    return b.value


def game_is_running(h):
    title = get_title(h)
    return 'Muramasa' in title and 'FPS' in title


def capture(r, name):
    os.makedirs('screenshots', exist_ok=True)
    with mss.mss() as sct:
        img = sct.grab({'left': r.left, 'top': r.top,
                        'width': r.right - r.left, 'height': r.bottom - r.top})
        path = f'screenshots/{name}.png'
        mss.tools.to_png(img.rgb, img.size, output=path)
        return path


def ensure_focus(h):
    """Ensure Vita3K window has focus."""
    user32.SetForegroundWindow(h)
    time.sleep(0.3)
    # Click center of window to grab focus
    r = wt.RECT()
    user32.GetWindowRect(h, ctypes.byref(r))
    cx = (r.left + r.right) // 2
    cy = (r.top + r.bottom) // 2
    pyautogui.click(cx, cy)
    time.sleep(0.3)


def navigate_to_genroku_dialogue():
    """
    Navigate from title screen to Genroku Legends Episode 1 dialogue.

    Sequence (from title screen):
    1. 3s wait → X (title screen proceed)
    2. 1s wait → Right arrow (select Genroku Legends)
    3. 3s wait → X (confirm selection)
    4. 2s wait → X (episode select)
    5. 1s wait → X (confirm episode)
    6. 3s wait → X (loading/cutscene skip)
    7. 5s wait → X (dialogue appears)
    """
    h, r = find_vita3k()
    if not h:
        print("ERROR: Vita3K not running")
        return False

    if not game_is_running(h):
        print("ERROR: Game not running (title should contain 'Muramasa' and 'FPS')")
        return False

    ensure_focus(h)
    print("Game is running. Starting navigation to Genroku dialogue...")

    steps = [
        (3.0, 'x',     "Title screen → proceed"),
        (1.0, 'right', "Select Genroku Legends"),
        (3.0, 'x',     "Confirm Genroku Legends"),
        (2.0, 'x',     "Episode select"),
        (1.0, 'x',     "Confirm episode"),
        (3.0, 'x',     "Loading/cutscene"),
        (5.0, 'x',     "Dialogue scene"),
    ]

    for wait, key, desc in steps:
        print(f"  [{wait}s wait] → {key.upper()} : {desc}")
        time.sleep(wait)
        ensure_focus(h)
        press_key(key)

    # Wait for dialogue to render
    print("Waiting 3s for dialogue to render...")
    time.sleep(3)

    # Take screenshots
    h, r = find_vita3k()
    if not h:
        print("ERROR: Vita3K window lost")
        return False

    path = capture(r, 'genroku_dialogue')
    print(f"Screenshot saved: {path}")

    # Take a few more after advancing dialogue
    for i in range(2):
        time.sleep(1)
        press_key('x')
        time.sleep(2)
        path = capture(r, f'genroku_dialogue_{i+2}')
        print(f"Screenshot saved: {path}")

    print("\nDone! Check screenshots/ folder for dialogue test results.")
    return True


if __name__ == '__main__':
    from_game = '--from-game' in sys.argv

    if not from_game:
        # Launch game first using vita3k_run_game
        print("=== Starting game via vita3k_run_game ===")
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from vita3k_run_game import run_game
        if not run_game():
            print("FAILED to start game")
            sys.exit(1)
        print("Game started. Waiting 15s for full load...")
        time.sleep(15)

    print("\n=== Navigating to Genroku Legends Episode 1 ===")
    if navigate_to_genroku_dialogue():
        print("SUCCESS")
    else:
        print("FAILED")
        sys.exit(1)
