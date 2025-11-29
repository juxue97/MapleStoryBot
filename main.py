import time
import sys
from typing import Optional
import numpy as np
import cv2
import keyboard

from configs import constants
from exception import CustomException
from logger import logging
from components.vision.window_capture import WindowCapture
from components.vision.vision_preprocessor import VisionPreprocessor

class RunTasks():
    def __init__(self):
        try:
            self.window_name: str = constants.WINDOW_NAME
            self.is_running: bool = True
            self.loop_start_time: float = 0.0
            self.loop_end_time: float = 0.0

            self.wc: WindowCapture = None
            self.p: VisionPreprocessor = None


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

    def run_bot(self):
        print("bot logic running...")
        # TODO

    def run_ai(self):
        print("ai logic running...")
        # TODO

    def start_program(self, debug: True):
        try:
            logging.info("Starting program...")
            self.run_vision(window_name=self.window_name)

            # TODO - run other thread with their functions
            self.run_bot()
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

                # static_image = cv2.imread(r"C:\Users\User\Desktop\bot\MapleStoryBot\data\Screenshot 2025-11-29 232832.jpg")

                self.p.set_input(screenshot)
                processed: Optional[np.ndarray] = self.p.get_output()

                if debug:
                    if self.p.roi_enabled and screenshot is not None:
                        x = self.p.roi_x
                        y = self.p.roi_y
                        w = self.p.roi_w
                        h = self.p.roi_h
                        cv2.rectangle(screenshot, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    cv2.imshow("Tracking Image", screenshot)
                    if processed is not None:
                        cv2.imshow("Preprocessed Image", processed)
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