#!/usr/bin/env python3
"""
macOS Vita3K 자동 제어 도구.

Vita3K.app 실행/종료, 게임 자동 진입, 스크린샷 캡처, 윈도우 위치 식별.

기존 tools/vita3k_ctrl.py는 Windows 전용 (ctypes.windll). 이 도구는
macOS의 launchctl/osascript/screencapture 기반.

Usage:
    python tools/vita3k_macos.py launch        # Vita3K 실행 (GUI 모드)
    python tools/vita3k_macos.py close         # 안전 종료
    python tools/vita3k_macos.py status        # 실행 상태
    python tools/vita3k_macos.py screenshot OUT.png    # 윈도우 캡처
    python tools/vita3k_macos.py focus         # 윈도우 포커스
"""
import os
import sys
import time
import subprocess
import shutil
from pathlib import Path


VITA3K_APP = "/Applications/Vita3K.app"
VITA3K_BIN = f"{VITA3K_APP}/Contents/MacOS/Vita3K"


def is_running() -> bool:
    """Vita3K 프로세스 실행 중인지 확인."""
    r = subprocess.run(["pgrep", "-x", "Vita3K"], capture_output=True, text=True)
    return r.returncode == 0


def get_pid() -> int:
    """Vita3K PID (없으면 0)."""
    r = subprocess.run(["pgrep", "-x", "Vita3K"], capture_output=True, text=True)
    if r.returncode != 0:
        return 0
    return int(r.stdout.strip().split('\n')[0])


def launch():
    """Vita3K.app 실행 (백그라운드, GUI 모드)."""
    if is_running():
        print(f"already running (pid={get_pid()})")
        return 0
    if not Path(VITA3K_BIN).exists():
        print(f"ERROR: {VITA3K_BIN} not found")
        return 1
    # `open -a` 또는 직접 binary 실행. -a 가 .app launchctl 방식
    subprocess.Popen(["open", "-a", VITA3K_APP])
    # 부팅 대기
    for _ in range(20):
        time.sleep(0.5)
        if is_running():
            break
    if is_running():
        print(f"launched (pid={get_pid()})")
        return 0
    print("ERROR: launch failed (process not detected)")
    return 1


def close():
    """안전 종료 (SIGTERM, 그 후 SIGKILL fallback)."""
    pid = get_pid()
    if pid == 0:
        print("not running")
        return 0
    # SIGTERM 우선
    subprocess.run(["kill", "-TERM", str(pid)])
    for _ in range(20):
        time.sleep(0.5)
        if not is_running():
            print(f"terminated (pid={pid})")
            return 0
    # SIGKILL
    subprocess.run(["kill", "-KILL", str(pid)])
    time.sleep(1)
    if not is_running():
        print(f"force killed (pid={pid})")
        return 0
    print("ERROR: failed to kill")
    return 1


def status():
    """현재 상태 출력."""
    if is_running():
        pid = get_pid()
        print(f"running (pid={pid})")
        # 윈도우 정보 (osascript via System Events)
        try:
            r = subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to tell process "Vita3K" '
                'to get {position, size} of front window'
            ], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                print(f"window: {r.stdout.strip()}")
        except Exception:
            pass
        return 0
    print("not running")
    return 1


def screenshot(out_path: str = "temp/vita3k_capture.png", window_only: bool = True):
    """Vita3K 윈도우 스크린샷 캡처.

    window_only=True : screencapture -l <window_id> 윈도우만 캡처
    window_only=False : 전체 화면 캡처
    """
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    if not is_running():
        print("ERROR: Vita3K not running")
        return 1
    if window_only:
        # window ID 찾기. CGWindowListCopyWindowInfo 같은 API 필요.
        # 간단한 방법: AppleScript로 윈도우 frame 가져와 screencapture -R 사용
        try:
            r = subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to tell process "Vita3K" '
                'to get {position, size} of front window'
            ], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                # 형식: x, y, w, h
                parts = [int(x.strip()) for x in r.stdout.strip().split(',')]
                if len(parts) == 4:
                    x, y, w, h = parts
                    subprocess.run([
                        "screencapture", "-x", "-R", f"{x},{y},{w},{h}", out_path
                    ])
                    if Path(out_path).exists():
                        print(f"saved: {out_path} ({w}x{h} @ {x},{y})")
                        return 0
        except Exception as e:
            print(f"AppleScript failed: {e}, falling back to full screen")
    # full screen
    subprocess.run(["screencapture", "-x", out_path])
    if Path(out_path).exists():
        print(f"saved: {out_path} (full screen)")
        return 0
    print("ERROR: screencapture failed")
    return 1


def focus():
    """Vita3K 윈도우 포커스."""
    if not is_running():
        print("ERROR: not running")
        return 1
    subprocess.run([
        "osascript", "-e",
        'tell application "Vita3K" to activate'
    ])
    print("activated")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "launch":
        return launch()
    if cmd == "close":
        return close()
    if cmd == "status":
        return status()
    if cmd == "screenshot":
        out = sys.argv[2] if len(sys.argv) > 2 else "temp/vita3k_capture.png"
        return screenshot(out)
    if cmd == "focus":
        return focus()
    print(f"unknown command: {cmd}")
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
