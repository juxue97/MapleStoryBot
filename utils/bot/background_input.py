# background_input.py
import time
import win32gui  # type: ignore
import win32con  # type: ignore
import win32api  # type: ignore
from contextlib import contextmanager

from configs.constants.vk_keys import VK_MAP


def find_window_by_title(keyword: str):
    result = []

    def enum_handler(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if keyword.lower() in title.lower():
            result.append(hwnd)

    win32gui.EnumWindows(enum_handler, None)
    return result[0] if result else None


class BackgroundInput:
    """
    Sends *real* keyboard events via keybd_event (OS-level).
    We keep hwnd only to bring the target window (e.g. Remote Desktop) to foreground.
    """
    def __init__(self, window_name: str):
        self.hwnd = find_window_by_title(window_name)
        if not self.hwnd:
            raise RuntimeError(f"Window with title containing '{window_name}' not found")

        # Make sure the RDP window is foreground so it receives keyboard events
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(self.hwnd)

    def _vk(self, key: str) -> int:
        key = key.lower()

        # Known names
        if key in VK_MAP:
            return VK_MAP[key]

        # Single char -> ASCII
        if len(key) == 1:
            return ord(key.upper())

        raise ValueError(f"Unknown key: {key}")

    def key_down(self, key: str):
        vk = self._vk(key)
        # scan code 0 is usually fine; flags 0 = key down
        win32api.keybd_event(vk, 0, 0, 0)

    def key_up(self, key: str):
        vk = self._vk(key)
        # KEYEVENTF_KEYUP to release
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)

    def press(self, key: str, presses: int = 1, interval: float = 0.0):
        for _ in range(presses):
            self.key_down(key)
            time.sleep(0.03)
            self.key_up(key)
            if interval > 0:
                time.sleep(interval)

    @contextmanager
    def hold(self, key: str):
        self.key_down(key)
        try:
            yield
        finally:
            self.key_up(key)
