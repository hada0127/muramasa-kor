#!/usr/bin/env python3
"""
Vita3K game launcher - automatically navigates GUI to start a game.
Handles: Lock screen → ImGui app list → LiveArea → Game start.
"""
import pyautogui, time, ctypes, ctypes.wintypes as wt, mss, mss.tools, sys, os
from PIL import Image
import numpy as np

pyautogui.FAILSAFE = False
user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)


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


def capture(r, name=None):
    with mss.mss() as sct:
        img = sct.grab({'left': r.left, 'top': r.top,
                        'width': r.right - r.left, 'height': r.bottom - r.top})
        if name:
            os.makedirs('screenshots', exist_ok=True)
            mss.tools.to_png(img.rgb, img.size, output=f'screenshots/{name}.png')
        # Save and reload to avoid pixel format issues
        path = f'screenshots/{name or "temp"}.png'
        mss.tools.to_png(img.rgb, img.size, output=path)
        return Image.open(path)


def find_text_in_image(img, search_region=None, threshold=300):
    """Find bright text clusters in an image region."""
    arr = np.array(img)
    if search_region:
        y1, y2, x1, x2 = search_region
        region = arr[y1:y2, x1:x2]
        offset_y, offset_x = y1, x1
    else:
        region = arr
        offset_y, offset_x = 0, 0

    brightness = region[:, :, :3].sum(axis=2)
    mask = brightness > threshold
    if not mask.any():
        return None

    ys, xs = np.where(mask)
    cy = int(np.median(ys)) + offset_y
    cx = int(np.median(xs)) + offset_x
    return cx, cy


def game_is_running(h):
    title = get_title(h)
    return 'Muramasa' in title and 'FPS' in title


def run_game():
    h, r = find_vita3k()
    if not h:
        print("ERROR: Vita3K not running")
        return False

    user32.SetForegroundWindow(h)
    time.sleep(0.5)
    l, t, ri, b = r.left, r.top, r.right, r.bottom
    w, ht = ri - l, b - t

    # Step 1: Click center to ensure focus
    pyautogui.click((l + ri) // 2, (t + b) // 2)
    time.sleep(0.5)

    # Step 2: Press Esc to open ImGui app list
    print("Opening ImGui app list...")
    pyautogui.press('escape')
    time.sleep(2)

    # Step 3: Capture and find Muramasa row
    img = capture(r, 'auto_imgui')
    ih, iw = np.array(img).shape[:2]

    # Find green compatibility dot in lower 40% of image
    arr = np.array(img)
    for y in range(int(ih * 0.6), int(ih * 0.95)):
        for x in range(int(iw * 0.05), int(iw * 0.15)):
            rr, gg, bb = arr[y, x, :3]
            if gg > 150 and rr < 100 and bb < 100:
                # Found green dot - Muramasa row
                click_x = l + iw // 2
                click_y = t + y
                print(f"Found Muramasa at y={y} ({y/ih:.0%})")
                pyautogui.doubleClick(click_x, click_y)
                time.sleep(5)

                if game_is_running(h):
                    print("Game started directly!")
                    return True

                # Step 4: Now in LiveArea - find 시작 button
                print("In LiveArea, finding 시작...")
                img2 = capture(r, 'auto_livearea')
                arr2 = np.array(img2)
                ih2, iw2 = arr2.shape[:2]

                # 시작 is white text in right half, upper-middle area
                for sy in range(int(ih2 * 0.35), int(ih2 * 0.65)):
                    for sx in range(int(iw2 * 0.55), int(iw2 * 0.85)):
                        r2, g2, b2 = arr2[sy, sx, :3]
                        if r2 > 220 and g2 > 220 and b2 > 220:
                            # Found white pixel - potential 시작 text
                            click_x2 = l + sx
                            click_y2 = t + sy
                            print(f"Found 시작 at ({sx},{sy})")
                            pyautogui.click(click_x2, click_y2)
                            time.sleep(10)

                            if game_is_running(h):
                                print("Game started!")
                                return True
                            else:
                                print("시작 click failed, trying more...")
                                # Break inner loops
                                break
                    else:
                        continue
                    break

                # If still not started, try a few more positions
                if not game_is_running(h):
                    for sx_pct in [0.70, 0.72, 0.74, 0.68]:
                        for sy_pct in [0.48, 0.50, 0.52, 0.54]:
                            pyautogui.click(l + int(iw2 * sx_pct), t + int(ih2 * sy_pct))
                            time.sleep(3)
                            if game_is_running(h):
                                print(f"Game started at ({sx_pct},{sy_pct})!")
                                return True
                break
        else:
            continue
        break

    if game_is_running(h):
        return True

    print("Could not start game automatically")
    return False


if __name__ == '__main__':
    wait_time = int(sys.argv[1]) if len(sys.argv) > 1 else 40

    if run_game():
        print(f"Waiting {wait_time}s for game to load...")
        time.sleep(wait_time)
        h, r = find_vita3k()
        if h:
            capture(r, 'game_result')
            print(f"Title: {get_title(h)[:80]}")
            print("Screenshot saved: screenshots/game_result.png")
    else:
        print("FAILED to start game")
