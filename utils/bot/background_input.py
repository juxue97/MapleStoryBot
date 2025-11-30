# background_input.py
import time
import win32gui # type: ignore
import win32con # type: ignore
import win32api # type: ignore
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


def _build_lparam(vk_code, is_keyup=False):
    scan_code = win32api.MapVirtualKey(vk_code, 0)
    if not is_keyup:
        return 0x00000001 | (scan_code << 16)
    else:
        return 0xC0000001 | (scan_code << 16)


class BackgroundInput:
    """
    Sends keyboard events directly to a specific window via PostMessage.
    Can work on minimized/unfocused windows (if the app accepts messages).
    """
    def __init__(self, window_name: str):
        self.hwnd = find_window_by_title(window_name)
        if not self.hwnd:
            raise RuntimeError(f"Window with title containing '{window_name}' not found")

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
        lparam = _build_lparam(vk, is_keyup=False)
        win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, vk, lparam)

    def key_up(self, key: str):
        vk = self._vk(key)
        lparam = _build_lparam(vk, is_keyup=True)
        win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, vk, lparam)

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
