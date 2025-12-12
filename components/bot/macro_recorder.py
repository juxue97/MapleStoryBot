import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import keyboard

from exception import CustomException
from logger import logging
from utils import write_yaml_file


class MacroRecorder:
    """
    Keyboard macro recorder.

    - start(): begin recording (non-blocking, uses keyboard's internal threads)
    - stop(): stop recording
    - save(): save to YAML
    - stop_and_save(): convenience helper

    The recorder itself doesn't need a custom Thread loop, because
    keyboard.hook() already runs asynchronously.
    """

    def __init__(self, dir_name: str, keys: List[str]) -> None:
        try:
            self.dir_name: str = dir_name
            self.keys: List[str] = keys

            self.events: List[Dict[str, Any]] = []
            self.hook: Optional[Any] = None
            self.start_time: Optional[float] = None
            self.is_recording: bool = False
            self.last_saved_path: Optional[str] = None

            logging.info(f"MacroRecorder initialized. dir_name='{self.dir_name}'")
        except Exception as e:
            raise CustomException(e, sys) from e

    def _callback(self, event: keyboard.KeyboardEvent) -> None:
        """
        Keyboard hook callback. It is active only while recording is enabled.
        """
        try:
            if not self.is_recording:
                return

            if event.event_type not in ("down", "up"):
                return

            name = event.name

            if name in self.keys:
                return

            if name is None:
                return

            if self.start_time is None:
                self.start_time = event.time

            rel_time = event.time - self.start_time

            self.events.append(
                {
                    "time": round(rel_time, 4),
                    "key": str(name),
                    "type": str(event.event_type),
                }
            )

        except Exception as e:
            logging.error(f"[MacroRecorder] Error in keyboard callback: {e}")

    def start(self) -> None:
        """
        Begin macro recording. Non-blocking.
        """
        try:
            if self.is_recording:
                logging.warning("[MacroRecorder] Recording already in progress.")
                return

            print("=== Macro recording started (F9 to stop) ===")
            self.events = []
            self.start_time = None
            self.hook = keyboard.hook(self._callback)
            self.is_recording = True

        except Exception as e:
            raise CustomException(e, sys) from e

    def stop(self) -> None:
        """
        Stop macro recording but do not save automatically.
        """
        try:
            if not self.is_recording:
                logging.warning("[MacroRecorder] stop() called but not recording.")
                return

            if self.hook:
                keyboard.unhook(self.hook)
                self.hook = None

            self.is_recording = False
            print("=== Macro recording stopped ===")

        except Exception as e:
            raise CustomException(e, sys) from e

    def save(self) -> str:
        """
        Persist recorded events to a YAML file.
        Returns the full file path.
        """
        try:
            if not self.events:
                logging.warning("[MacroRecorder] No events to save.")
                return ""

            now_str = datetime.now().strftime("%d%m%y_%H%M%S")
            filename = f"record_{now_str}.yaml"
            full_path = os.path.join(self.dir_name, filename)

            data = {
                "meta": {
                    "description": "Recorded keyboard macro",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
                "events": self.events,
            }

            write_yaml_file(full_path, data, replace=True)
            self.last_saved_path = full_path
            print("=== Macro recording saved ===")
            logging.info(f"[MacroRecorder] Saved macro: {full_path}")
            return full_path

        except Exception as e:
            raise CustomException(e, sys) from e

    def stop_and_save(self) -> Optional[str]:
        """
        Convenience helper: stop recording and immediately save.
        """
        try:
            if not self.is_recording:
                logging.warning("[MacroRecorder] stop_and_save() called but not recording.")
                return None

            self.stop()
            path = self.save()

            return path or None
        except Exception as e:
            raise CustomException(e, sys) from e
