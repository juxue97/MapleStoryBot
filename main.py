import time
import sys
from typing import Dict, List, Optional
import numpy as np
import cv2
import keyboard

from configs import constants
from exception import CustomException
from logger import logging

from components.vision.window_capture import WindowCapture
from components.vision.vision_preprocessor import VisionPreprocessor
from components.vision.object_detector import ObjectDetector

from components.bot.macro_player import MacroPlayer
from components.bot.macro_recorder import MacroRecorder

class RunTasks():
    def __init__(self):
        try:
            self.window_name: str = constants.WINDOW_NAME
            self.macro_save_dir: str = constants.MACRO_SAVE_DIR
            self.macro_config_path: str = constants.MACRO_CONFIG_PATH

            self.macro_player_start: str = constants.MACRO_PLAYER_START
            self.macro_player_stop: str = constants.MACRO_PLAYER_STOP
            self.macro_record_start: str = constants.MACRO_RECORD_START
            self.macro_record_stop: str = constants.MACRO_RECORD_STOP

            self.rune_template_path: str = constants.RUNE_TEMPLATE_PATH
            self.player_template_path: str = constants.PLAYER_TEMPLATE_PATH
            self.template_config_list: List[Dict] = [
                {
                    "name": "rune",
                    "path": self.rune_template_path,
                    "threshold": 0.95,
                    "draw_color": (0, 255, 0)
                },
                {
                    "name": "player",
                    "path": self.player_template_path,
                    "threshold": 0.95,
                    "draw_color": (0, 255, 0)
                },
            ]

            self.is_running: bool = True
            self.loop_start_time: float = 0.0
            self.loop_end_time: float = 0.0

            self.wc: WindowCapture = None
            self.p: VisionPreprocessor = None
            self.bmp: MacroPlayer = None
            self.bmr: MacroRecorder = None
            
            # detector
            self.rune_d: ObjectDetector = None
            self.player_d: ObjectDetector = None

        except Exception as e:
            raise CustomException(e, sys) from e

    def run_vision(self, window_name: str):
        try:
            logging.info("Starting vision thread...")
            self.wc: WindowCapture = WindowCapture(window_name=window_name)
            self.p = VisionPreprocessor()
            self.p.init_control_panel()

            self.wc.start()
            self.p.start()
        
        except Exception as e:
            raise CustomException(e, sys) from e

    def run_bot(self, window_name: str, recorder_filename: str):
        try:
            logging.info("Starting AutoBot thread...")
            self.bmp: MacroPlayer = MacroPlayer(window_name=window_name)
            self.bmp.load(recorder_filename)

        except Exception as e:
            raise CustomException(e, sys) from e
        
    def run_object_detector(self):
        try:
            logging.info("Starting Object Detector thread(s)...")

            for obj in self.template_config_list:
                name = obj["name"]
                path = obj["path"]
                threshold = obj.get("threshold", 0.8)
                draw_color = obj.get("draw_color", (0, 255, 0))

                if name == "rune":
                    self.rune_d = ObjectDetector(
                        template_path=path,
                        threshold=threshold,
                        draw_color=draw_color,
                    )
                    self.rune_d.start()
                    logging.info(f"Rune detector started with template: {path}")

                elif name == "player":
                    self.player_d = ObjectDetector(
                        template_path=path,
                        threshold=threshold,
                        draw_color=draw_color,
                    )
                    self.player_d.start()
                    logging.info(f"Player detector started with template: {path}")
            
        except Exception as e:
            raise CustomException(e, sys) from e
        
    def macro_record(self,dir_name:str):
        try:
            keys: List[str] = [self.macro_player_start, self.macro_player_stop, self.macro_record_start, self.macro_record_stop]
            self.bmr: MacroRecorder = MacroRecorder(dir_name=dir_name,
                                                    keys=keys
                                                )

        except Exception as e:
            raise CustomException(e, sys) from e

    def run_ai(self):
        print("ai logic running...")
        # TODO

    def start_program(self, debug: True):
        try:
            logging.info("Starting program...")
            self.macro_record(dir_name=self.macro_save_dir)

            self.run_vision(window_name=self.window_name)

            self.run_object_detector()

            self.run_bot(window_name=self.window_name,
                         recorder_filename=self.macro_config_path
                        )
            self.run_ai()

            logging.info("Starting loop")
            self.loop_start_time: float = time.time()

            while self.is_running:
                screenshot: Optional[np.ndarray] = self.wc.screenshot

                if self.wc is None:
                    logging.error("WindowCapture is not initialized.")
                    break

                with self.wc.lock:
                    screenshot: Optional[np.ndarray] = (
                        None if self.wc.screenshot is None
                        else self.wc.screenshot.copy()
                    )

                if screenshot is None: 
                    print('no detected image')
                    time.sleep(0.01)
                    continue

                if self.rune_d:
                    self.rune_d.update(screenshot)
                    coor_rune = self.rune_d.get_coordinates()
                if self.player_d:
                    self.player_d.update(screenshot)
                    coor_player = self.player_d.get_coordinates()

                # Play
                if self.bmp.stopped and (not self.bmr.is_recording) and keyboard.is_pressed(self.macro_player_start):
                    self.bmp.start()

                # Stop play
                if (not self.bmp.stopped) and keyboard.is_pressed(self.macro_player_stop):
                    self.bmp.stop()

                # Start record
                if self.bmp.stopped and (not self.bmr.is_recording) and keyboard.is_pressed(self.macro_record_start):
                    self.bmr.start()

                # Stop record
                if self.bmr.is_recording and keyboard.is_pressed(self.macro_record_stop):
                    self.bmr.stop_and_save()

                # img_path = r"C:\Users\User\Desktop\bot\MapleStoryBot\data\images\arrows.jpg"
                # static_image = cv2.imread(img_path)

                self.p.set_input(screenshot)
                processed: Optional[np.ndarray] = self.p.get_output()

                arrow_boxes = []
                arrow_debug = None

                if processed is not None:
                    arrow_boxes, arrow_debug = self.p.detect_arrow_contours(processed)

                    # Example: crop each arrow for AI later
                    arrow_crops = []
                    for (x, y, w, h) in arrow_boxes:
                        arrow_crops.append(processed[y:y+h, x:x+w])

                if debug:
                    if self.p.roi_enabled and screenshot is not None:
                        x = self.p.roi_x
                        y = self.p.roi_y
                        w = self.p.roi_w
                        h = self.p.roi_h
                        cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 255, 0), 2)


                    if coor_rune and len(coor_rune) > 0:       # SAFE check
                        r = coor_rune[0]                       # first match only
                        cv2.rectangle(
                            screenshot,
                            (r["x"], r["y"]),
                            (r["x"] + r["w"], r["y"] + r["h"]),
                            (0, 255, 0),
                            2
                        )
                        cv2.putText(screenshot, "Rune", (r["x"], r["y"] - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

                    # =========================
                    # Draw Player Detection Box
                    # =========================
                    if coor_player and len(coor_player) > 0:   # SAFE check
                        p = coor_player[0]
                        cv2.rectangle(
                            screenshot,
                            (p["x"], p["y"]),
                            (p["x"] + p["w"], p["y"] + p["h"]),
                            (255, 0, 0),
                            2
                        )
                        cv2.putText(screenshot, "Player", (p["x"], p["y"] - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 1)


                    cv2.imshow("Tracking Image", screenshot)
                    if processed is not None:
                        cv2.imshow("Preprocessed Image", processed)

                    if arrow_debug is not None:
                        cv2.imshow("Arrow Debug", arrow_debug)

                    cv2.waitKey(1)

                if keyboard.is_pressed('q') or self.wc.track_window_closed():
                    self.stop_program(start_time=self.loop_start_time)
                    break

        except Exception as e:
            raise CustomException(e, sys) from e
        
    def stop_program(self, start_time: float):
        try:
            logging.info("Stopping program...")
            self.is_running = False
            self.wc.stop()
            self.p.stop()
            self.bmp.stop()
            self.rune_d.stop()
            self.player_d.stop()

            cv2.destroyAllWindows()

            loop_duration: float = time.time() - start_time
            logging.info(f"Program stopped. Ran for {loop_duration:.2f}s")

        except Exception as e:
            raise CustomException(e, sys) from e

if __name__ == "__main__":
    try:
        print("quit - press 'q'")
        time.sleep(2)

        entry_point = RunTasks()
        entry_point.start_program(debug=True)

    except Exception as e:
        raise CustomException(e, sys) from e