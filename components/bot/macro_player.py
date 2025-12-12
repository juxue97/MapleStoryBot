import os
import sys
import time
from threading import Thread, Lock
from typing import Any, Dict, List, Optional, Set

import pydirectinput
import win32gui   # type: ignore
import win32con   # type: ignore
import pywintypes # type: ignore

from exception import CustomException
from logger import logging
from utils import read_yaml_file, find_window_by_title


class MacroPlayer:
    """
    Keyboard macro player.

    Follows same pattern as VisionPreprocessor / WindowCapture:

    - Class-level flags: stopped, lock, buffer_time
    - start()  -> spawn thread(target=self.run)
    - stop()   -> request playback stop via `stopped` and release all keys
    - run()    -> playback loop (currently repeats until stopped)

    Usage:
        player = MacroPlayer("MapleStory")
        player.load("path/to/record_xxx.yaml")
        player.start()   # non-blocking
    """

    buffer_time: float = 0.1

    stopped: bool = True
    lock: Lock = None

    window_name: str
    hwnd: Optional[int] = None

    macro: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = []

    pressed_keys: Set[str] = set()

    def __init__(self, window_name: str) -> None:
        try:
            self.window_name = window_name
            self.lock = Lock()
            self.pressed_keys = set()

            self._resolve_window()

            logging.info(
                f"MacroPlayer initialized for window '{self.window_name}'."
            )
        except Exception as e:
            raise CustomException(e, sys) from e

    def _resolve_window(self) -> None:
        """Find and bind to the target window, best-effort focus."""
        try:
            hwnd = find_window_by_title(self.window_name)
            if not hwnd:
                msg = f"Window not found: {self.window_name}"
                logging.error(msg)
                raise CustomException(msg, sys)

            self.hwnd = hwnd
            title = win32gui.GetWindowText(self.hwnd)

            logging.info(
                f"[MacroPlayer] Bound to window '{title}' (hwnd={self.hwnd})"
            )

            try:
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(self.hwnd)
                time.sleep(0.2)
                logging.debug("[MacroPlayer] Window focused successfully.")
            except pywintypes.error as e:
                logging.warning(
                    f"[MacroPlayer] Failed to SetForegroundWindow: {e}. "
                    "User may need to manually focus the window."
                )
                time.sleep(1)

        except Exception as e:
            raise CustomException(e, sys) from e

    def load(self, path: str) -> None:
        """Load macro YAML file into memory."""
        try:
            if not os.path.exists(path):
                msg = f"[MacroPlayer] Macro file not found: {path}"
                logging.error(msg)
                raise CustomException(msg, sys)

            macro = read_yaml_file(path)
            events = macro.get("events")

            if not isinstance(events, list):
                msg = f"[MacroPlayer] Invalid macro file (missing 'events'): {path}"
                logging.error(msg)
                raise CustomException(msg, sys)

            with self.lock:
                self.macro = macro
                self.events = events

            logging.info(
                f"[MacroPlayer] Macro loaded from '{path}' "
                f"with {len(events)} events."
            )

        except Exception as e:
            raise CustomException(e, sys) from e

    def _press_key(self, key: str) -> None:
        """Press key and track it as held down."""
        pydirectinput.keyDown(key)
        with self.lock:
            self.pressed_keys.add(key)

    def _release_key(self, key: str) -> None:
        """Release key and remove it from the held set."""
        pydirectinput.keyUp(key)
        with self.lock:
            self.pressed_keys.discard(key)

    def _release_all_keys(self) -> None:
        """Release all keys currently held down by this player."""
        with self.lock:
            keys_to_release = list(self.pressed_keys)
            self.pressed_keys.clear()

        for key in keys_to_release:
            try:
                pydirectinput.keyUp(key)
                logging.debug(f"[MacroPlayer] Released key '{key}' on stop.")
            except Exception as e:
                logging.warning(f"[MacroPlayer] Failed to release key '{key}': {e}")

    def _play_once(self) -> None:
        """
        Play the loaded macro once (blocking).
        Uses `self.stopped` as stop flag.
        """
        with self.lock:
            events = list(self.events)

        if not events:
            logging.warning("[MacroPlayer] No events to play.")
            return

        logging.info(
            f"[MacroPlayer] Starting playback ({len(events)} events)..."
        )

        start_time = time.perf_counter()

        try:
            for event in events:
                if self.stopped:
                    logging.info("[MacroPlayer] Stop requested. Ending playback early.")
                    break

                target_t = float(event["time"])
                key = str(event["key"])
                typ = str(event["type"])

                while not self.stopped and (time.perf_counter() - start_time < target_t):
                    time.sleep(0.0005)

                if self.stopped:
                    break

                if typ == "down":
                    self._press_key(key)
                elif typ == "up":
                    self._release_key(key)

        finally:
            self._release_all_keys()
            logging.info("[MacroPlayer] Playback finished.")

    def start(self) -> None:
        """
        Start macro playback in a background thread.
        Matches VisionPreprocessor.start(): sets stopped=False, spins a thread
        that calls self.run().
        """
        try:
            with self.lock:
                if not self.events:
                    msg = "[MacroPlayer] No macro loaded. Call load(path) first."
                    logging.error(msg)
                    raise CustomException(msg, sys)

                if not self.stopped:
                    logging.warning("[MacroPlayer] Playback already running.")
                    return

                self.stopped = False

            t = Thread(target=self.run, daemon=True)
            t.start()
            logging.info("MacroPlayer thread started.")
            time.sleep(self.buffer_time)

        except Exception as e:
            raise CustomException(e, sys) from e

    def stop(self) -> None:
        """
        Request playback stop.
        Also releases all currently held keys.
        """
        try:
            self.stopped = True
            logging.info("MacroPlayer thread stop requested.")
            self._release_all_keys()
        except Exception as e:
            raise CustomException(e, sys) from e

    def run(self) -> None:
        """
        Thread entry point.
        With current while-loop, this will repeat the macro until stopped.
        Change to a single self._play_once() if you want one-shot playback.
        """
        try:
            while not self.stopped:
                self._play_once()
        except Exception as e:
            logging.error(f"MacroPlayer error: {e}")
            raise CustomException(e, sys) from e
        finally:
            self.stopped = True
            self._release_all_keys()
            logging.info("MacroPlayer thread finished.")
