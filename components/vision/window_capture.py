import sys
import time
import ctypes
from threading import Thread, Lock
from typing import Optional, Tuple

import win32gui
import win32ui
import win32con
import numpy as np

from configs import constants
from exception import CustomException
from logger import logging


class WindowCapture:
    """
    Handles capturing screenshots of a specific window using Win32 APIs.
    Thread-safe access to the latest screenshot via `self.screenshot`.
    """

    def __init__(self, window_name: Optional[str] = None) -> None:
        try:
            # config
            self.window_name: str = window_name
            self.buffer_time: float = 0.1

            # threading / shared state
            self.lock: Lock = Lock()
            self.stopped: bool = True
            self.screenshot: Optional[np.ndarray] = None

            # window / geometry
            self.hwnd: Optional[int] = None
            self.w: int = 0
            self.h: int = 0
            self.cropped_x: int = 0
            self.cropped_y: int = 0
            self.offset_x: int = 0
            self.offset_y: int = 0

            # border configuration (you can move these to constants if you want)
            self._border_pixels: int = 8
            self._titlebar_pixels: int = 30

            self._set_dpi_awareness()
            self._init_window_handle()
            self._init_window_metrics()

            logging.info(
                f"WindowCapture initialized for window '{self.window_name}' "
                f"({self.w}x{self.h} at offset ({self.offset_x}, {self.offset_y}))"
            )

        except Exception as e:
            raise CustomException(e, sys) from e

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _set_dpi_awareness(self) -> None:
        """Set process DPI awareness for clearer captures on high DPI screens."""
        try:
            try:
                # Windows 10 and later
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                logging.debug("DPI awareness set using shcore.SetProcessDpiAwareness.")
            except AttributeError:
                # Windows 8.1 and earlier
                ctypes.windll.user32.SetProcessDPIAware()
                logging.debug("DPI awareness set using user32.SetProcessDPIAware.")
        except Exception as e:
            # Non-fatal – log and continue
            logging.warning(f"Failed to set DPI awareness: {e}")

    def _init_window_handle(self) -> None:
        """Find and store the window handle by name."""
        self.hwnd = win32gui.FindWindow(None, self.window_name)
        if not self.hwnd:
            msg = f"Window not found: {self.window_name}"
            logging.error(msg)
            raise CustomException(msg, sys)

    def _init_window_metrics(self) -> None:
        """Compute window size, cropped region, and screen offsets."""
        if not self.hwnd:
            msg = "HWND is not initialized before computing window metrics."
            logging.error(msg)
            raise CustomException(msg, sys)

        window_rect = win32gui.GetWindowRect(self.hwnd)
        logging.debug(f"Raw window rect for '{self.window_name}': {window_rect}")

        # (left, top, right, bottom)
        raw_w = window_rect[2] - window_rect[0]
        raw_h = window_rect[3] - window_rect[1]

        # Remove border + titlebar
        self.w = raw_w - (self._border_pixels * 2)
        self.h = raw_h - self._titlebar_pixels - self._border_pixels
        self.cropped_x = self._border_pixels
        self.cropped_y = self._titlebar_pixels

        # Screen coordinate offsets
        self.offset_x = window_rect[0] + self.cropped_x
        self.offset_y = window_rect[1] + self.cropped_y

        logging.debug(
            f"Cropped window size: {self.w}x{self.h}, "
            f"crop offset: ({self.cropped_x}, {self.cropped_y}), "
            f"screen offset: ({self.offset_x}, {self.offset_y})"
        )

    # -------------------------------------------------------------------------
    # Public methods
    # -------------------------------------------------------------------------

    def track_window_closed(self) -> bool:
        """
        Check if the window is still available.
        Returns True if the window is gone (e.g., closed), False otherwise.
        """
        try:
            hwnd = win32gui.FindWindow(None, self.window_name)
            if not hwnd:
                logging.warning(f"Window '{self.window_name}' no longer found.")
                self.hwnd = None
                return True

            # window still valid, update handle in case it changed
            self.hwnd = hwnd
            return False

        except Exception as e:
            raise CustomException(e, sys) from e

    def get_screenshot(self) -> np.ndarray:
        """
        Capture a screenshot of the target window's client area.
        Returns a BGR numpy array (h, w, 3).
        """
        try:
            if not self.hwnd:
                msg = "Cannot capture screenshot: window handle is None."
                logging.error(msg)
                raise CustomException(msg, sys)

            wdc = win32gui.GetWindowDC(self.hwnd)
            dc_obj = win32ui.CreateDCFromHandle(wdc)
            cdc = dc_obj.CreateCompatibleDC()

            data_bitmap = win32ui.CreateBitmap()
            data_bitmap.CreateCompatibleBitmap(dc_obj, self.w, self.h)
            cdc.SelectObject(data_bitmap)

            # BitBlt from the window DC into our memory DC
            cdc.BitBlt(
                (0, 0),
                (self.w, self.h),
                dc_obj,
                (self.cropped_x, self.cropped_y),
                win32con.SRCCOPY,
            )

            # Convert raw data to numpy array
            signed_ints_array = data_bitmap.GetBitmapBits(True)
            img = np.frombuffer(signed_ints_array, dtype=np.uint8)
            img.shape = (self.h, self.w, 4)  # BGRA

            # Cleanup GDI objects
            dc_obj.DeleteDC()
            cdc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, wdc)
            win32gui.DeleteObject(data_bitmap.GetHandle())

            # Drop alpha channel -> BGR
            img = img[..., :3]
            img = np.ascontiguousarray(img)

            return img

        except Exception as e:
            raise CustomException(e, sys) from e

    @staticmethod
    def list_window_names() -> None:
        """Log all visible window names (for debugging / finding correct title)."""
        try:
            def win_enum_handler(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        logging.info(f"{hex(hwnd)} - {title}")

            win32gui.EnumWindows(win_enum_handler, None)
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_screen_position(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Convert a window-relative position (x, y) into absolute screen coordinates.
        """
        try:
            return pos[0] + self.offset_x, pos[1] + self.offset_y
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_window_size(self) -> Tuple[int, int]:
        """Return the cropped window width and height."""
        try:
            return self.w, self.h
        except Exception as e:
            raise CustomException(e, sys) from e

    # -------------------------------------------------------------------------
    # Threading interface
    # -------------------------------------------------------------------------

    def start(self, interval_sec: float = 0.01) -> None:
        """
        Start a background thread that keeps updating `self.screenshot`.
        """
        try:
            if not self.stopped:
                logging.warning("WindowCapture thread already running.")
                return

            self.stopped = False
            thread = Thread(target=self._run, args=(interval_sec,), daemon=True)
            thread.start()
            logging.info("WindowCapture thread started.")
            time.sleep(self.buffer_time)
        except Exception as e:
            raise CustomException(e, sys) from e

    def stop(self) -> None:
        """Signal the capture thread to stop."""
        try:
            self.stopped = True
            logging.info("WindowCapture thread stop requested.")
        except Exception as e:
            raise CustomException(e, sys) from e

    def _run(self, interval_sec: float) -> None:
        """
        Internal thread loop: grabs screenshots at the given interval
        and stores them in `self.screenshot` (thread-safe).
        """
        try:
            while not self.stopped:
                # optional: break if window disappears
                if self.track_window_closed():
                    logging.warning("Stopping capture: window closed.")
                    self.stopped = True
                    break

                img = self.get_screenshot()
                with self.lock:
                    self.screenshot = img

                time.sleep(interval_sec)
        except Exception as e:
            # log and wrap
            logging.error(f"Error in WindowCapture thread: {e}")
            raise CustomException(e, sys) from e
