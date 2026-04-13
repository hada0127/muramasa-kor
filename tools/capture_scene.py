"""Step-by-step scene transition capture for DLC 1 first character scene."""
import sys, time, os, ctypes
import ctypes.wintypes as wt
import pyautogui, mss, mss.tools

pyautogui.FAILSAFE = False
user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002
SCANCODES = {'x': 45, 'z': 44, 'right': 77, 'left': 75, 'up': 72, 'down': 80, 'enter': 28}


def press_key(name, hold=0.15):
    sc = SCANCODES[name]
    flags = KEYEVENTF_SCANCODE
    if sc in (72, 75, 77, 80):
        flags |= 0x0001
    user32.keybd_event(0, sc, flags, 0)
    time.sleep(hold)
    user32.keybd_event(0, sc, flags | KEYEVENTF_KEYUP, 0)


def find_vita3k():
    wins = []
    def cb(h, l):
        if user32.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(256); user32.GetWindowTextW(h, b, 256)
            if 'Vita3K' in b.value: wins.append(h)
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    if wins:
        h = wins[0]; r = wt.RECT(); user32.GetWindowRect(h, ctypes.byref(r))
        return h, r
    return None, None


def capture(r, name):
    os.makedirs('screenshots', exist_ok=True)
    with mss.mss() as sct:
        img = sct.grab({'left': r.left, 'top': r.top,
                        'width': r.right - r.left, 'height': r.bottom - r.top})
        path = f'screenshots/{name}.png'
        mss.tools.to_png(img.rgb, img.size, output=path)
    print(f'  Saved {path}')


def game_running(h):
    b = ctypes.create_unicode_buffer(256); user32.GetWindowTextW(h, b, 256)
    return 'Muramasa' in b.value and 'FPS' in b.value


def ensure_focus(h, r):
    user32.SetForegroundWindow(h); time.sleep(0.3)
    pyautogui.click((r.left + r.right) // 2, (r.top + r.bottom) // 2); time.sleep(0.3)


def main():
    h, r = find_vita3k()
    if not h:
        print('Vita3K not running'); return
    ensure_focus(h, r)

    if not game_running(h):
        print('Game not running. Navigate to game first via ImGui.')
        # Try: Esc → doubleclick
        pyautogui.press('escape'); time.sleep(3)
        ih = r.bottom - r.top; iw = r.right - r.left
        pyautogui.doubleClick(r.left + iw // 2, r.top + int(0.20 * ih))
        time.sleep(8)
        # LiveArea 시작 click
        pyautogui.click(r.left + int(0.72 * iw), r.top + int(0.50 * ih))
        time.sleep(15)

    # Update r in case window moved
    h, r = find_vita3k()
    if not game_running(h):
        print('Game still not running, aborting'); return

    ensure_focus(h, r)
    capture(r, 'step01_title')

    # Title → DLC menu
    time.sleep(2)
    press_key('x'); time.sleep(2); capture(r, 'step02_after_title_x')

    press_key('right'); time.sleep(1); capture(r, 'step03_after_right')
    press_key('x'); time.sleep(3); capture(r, 'step04_genroku_menu')

    # Episode 1 start (first entry, X)
    press_key('x'); time.sleep(3); capture(r, 'step05_ep_confirm')
    press_key('x'); time.sleep(3); capture(r, 'step06_after_ep_confirm')
    press_key('x'); time.sleep(3); capture(r, 'step07_loading')

    # Scene card should appear now
    press_key('x'); time.sleep(3); capture(r, 'step08_scene_card')
    # Wait for scene card to fully render with subtitle
    time.sleep(2); capture(r, 'step09_subtitle_wait')
    # Don't press X here - let subtitle persist
    time.sleep(3); capture(r, 'step10_subtitle_long')


if __name__ == '__main__':
    main()
