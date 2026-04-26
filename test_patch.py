#!/usr/bin/env python3
# Test patch in Vita3K
import time
import pyautogui
import mss
from PIL import Image
import numpy as np

print("Waiting for Vita3K to fully load...")
time.sleep(5)

# Get window info
from ctypes import windll, Structure, c_int32

class RECT(Structure):
    _fields_ = [("left", c_int32), ("top", c_int32), ("right", c_int32), ("bottom", c_int32)]

def get_vita3k_window():
    hwnd = windll.user32.FindWindowW(None, "Vita3K v0.2.1 3962-0e9e3a2c")
    if not hwnd:
        return None
    rect = RECT()
    windll.user32.GetWindowRect(hwnd, ref=rect)
    return {
        'left': rect.left,
        'top': rect.top,
        'width': rect.right - rect.left,
        'height': rect.bottom - rect.top
    }

window = get_vita3k_window()
if not window:
    print("Vita3K window not found")
    exit(1)

print(f"Vita3K window found: {window}")

# Click on window and press Esc to open ImGui
pyautogui.click(window['left'] + window['width']//2, window['top'] + window['height']//2)
time.sleep(1)
pyautogui.press('escape')
print("Opened ImGui app list...")
time.sleep(2)

# Take screenshot to find green dot
with mss.mss() as sct:
    monitor = sct.monitors[1]
    screenshot = sct.grab(monitor)
    img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

# Save for debugging
img.save('temp/vita3k_app_list.png')
print("Saved app list screenshot")

# Find green dot (Muramasa) and double-click
arr = np.array(img)
h, w = arr.shape[:2]

found = False
for y in range(h//2, h):
    for x in range(w//10, w//4):
        try:
            r, g, b = arr[y, x, :3]
            if g > 100 and r < 80 and b < 80:  # green
                print(f"Found green dot at ({x}, {y})")
                click_x = window['left'] + x
                click_y = window['top'] + y
                pyautogui.doubleClick(click_x, click_y)
                print(f"Double-clicked at game ({click_x}, {click_y})")
                found = True
                break
        except:
            pass
    if found:
        break

if found:
    print("Launching Muramasa...")
    time.sleep(3)
    pyautogui.press('escape')  # Close any dialog

    # Game should be loading, wait for it
    time.sleep(5)

    # Take screenshot of game
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[1])
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        img.save('temp/vita3k_game_loaded.png')
        print("Game loaded! Screenshot saved")
else:
    print("Could not find Muramasa in app list")
