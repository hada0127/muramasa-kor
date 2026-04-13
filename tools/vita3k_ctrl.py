#!/usr/bin/env python3
"""
Vita3K GUI controller for Muramasa Rebirth Korean patch testing.
Launches/closes Vita3K properly through GUI, avoiding zombie processes.
"""

import subprocess
import time
import ctypes
import ctypes.wintypes as wt
import sys
import os

user32 = ctypes.windll.user32

# Vita3K paths
VITA3K_EXE = r"C:\game\vita3k\Vita3K.exe"
VITA3K_CONFIG = r"C:\game\vita3k\config.yml"
GAME_ID = "PCSE00240"

# Win32 constants
WM_CLOSE = 0x0010
SW_RESTORE = 9
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)


def find_vita3k_windows():
    """Find all Vita3K windows."""
    windows = []
    def callback(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            if 'Vita3K' in buf.value:
                windows.append((hwnd, buf.value))
        return True
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return windows


def close_vita3k_gui():
    """Close Vita3K gracefully via WM_CLOSE message (same as clicking X button)."""
    windows = find_vita3k_windows()
    if not windows:
        print("Vita3K is not running.")
        return True

    print(f"Found {len(windows)} Vita3K window(s)")
    for hwnd, title in windows:
        print(f"  Sending WM_CLOSE to: {title[:60]}...")
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    # Wait for graceful shutdown
    for i in range(15):
        time.sleep(1)
        remaining = find_vita3k_windows()
        if not remaining:
            print("Vita3K closed gracefully.")
            return True

    # If still running after 15 seconds, force kill
    remaining = find_vita3k_windows()
    if remaining:
        print("Graceful close timed out. Force killing...")
        subprocess.run(['taskkill', '/f', '/im', 'Vita3K.exe'],
                       capture_output=True)
        time.sleep(2)
        print("Force killed.")
    return True


def clear_autostart():
    """Clear Vita3K's auto-start setting so it opens to app list."""
    if os.path.exists(VITA3K_CONFIG):
        with open(VITA3K_CONFIG, 'r') as f:
            lines = f.readlines()
        with open(VITA3K_CONFIG, 'w') as f:
            for line in lines:
                if 'installed-path:' in line:
                    f.write('installed-path: ""\n')
                else:
                    f.write(line)


def launch_vita3k(run_game=False):
    """Launch Vita3K. If run_game=True, auto-start the game."""
    # Close any existing instance first
    close_vita3k_gui()
    time.sleep(2)

    if run_game:
        cmd = [VITA3K_EXE, '-r', GAME_ID]
        print(f"Launching Vita3K with game {GAME_ID}...")
    else:
        clear_autostart()
        cmd = [VITA3K_EXE]
        print("Launching Vita3K GUI (app list)...")

    subprocess.Popen(cmd, cwd=os.path.dirname(VITA3K_EXE))
    print("Launched. Waiting for window...")

    # Wait for window to appear
    for i in range(30):
        time.sleep(1)
        windows = find_vita3k_windows()
        if windows:
            print(f"  Window found: {windows[0][1][:60]}")
            return True

    print("  WARNING: Window not found after 30 seconds")
    return False


def status():
    """Check Vita3K status."""
    windows = find_vita3k_windows()
    if windows:
        print(f"Vita3K is RUNNING ({len(windows)} window(s))")
        for hwnd, title in windows:
            print(f"  {title}")
    else:
        print("Vita3K is NOT running")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: vita3k_ctrl.py <command>")
        print("  launch     - Launch Vita3K GUI (app list)")
        print("  run        - Launch and auto-start game")
        print("  close      - Close Vita3K gracefully")
        print("  kill       - Force kill Vita3K")
        print("  status     - Check if Vita3K is running")
        print("  restart    - Close and relaunch")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'launch':
        launch_vita3k(run_game=False)
    elif cmd == 'run':
        launch_vita3k(run_game=True)
    elif cmd == 'close':
        close_vita3k_gui()
    elif cmd == 'kill':
        subprocess.run(['taskkill', '/f', '/im', 'Vita3K.exe'], capture_output=True)
        print("Force killed.")
    elif cmd == 'status':
        status()
    elif cmd == 'restart':
        close_vita3k_gui()
        time.sleep(2)
        launch_vita3k(run_game='--run' in sys.argv)
    else:
        print(f"Unknown command: {cmd}")
