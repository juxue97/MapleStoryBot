import sys
import time
from threading import Thread, Lock
from typing import List, Dict, Optional

import cv2 as cv
import numpy as np

from logger import logging
from exception import CustomException


class ObjectDetector:
    """
    Template-based object detector running in a background thread.

    Usage:
        detector = ObjectDetector(template_path="images/obj.png", threshold=0.8)
        detector.start()

        while True:
            screenshot = ...  # BGR numpy array from your WindowCapture
            detector.update(screenshot)

            coords = detector.get_coordinates()
            if coords:
                # do something with coords[0]['center_x'], coords[0]['center_y']
                pass
    """

    def __init__(
        self,
        template_path: str,
        threshold: float = 0.8,
        draw_color: tuple = (0, 255, 0),
        sleep_interval: float = 0.01,
    ):
        try:
            self.lock: Lock = Lock()
            self.stopped: bool = True

            self.template_path: str = template_path
            self.threshold: float = threshold
            self.draw_color: tuple = draw_color
            self.sleep_interval: float = sleep_interval

            self._screenshot: Optional[np.ndarray] = None
            self._coords: List[Dict[str, int]] = []

            self.template_gray, self.w, self.h = self._load_template(template_path)

            logging.info(f"ObjectDetector initialized with template: {template_path}")
        except Exception as e:
            raise CustomException(e, sys) from e

    def _load_template(self, template_path: str):
        """Load the template, convert to grayscale, and get its width and height."""
        template_bgr = cv.imread(template_path, cv.IMREAD_COLOR)
        if template_bgr is None:
            raise FileNotFoundError(f"Template image not found: {template_path}")

        template_gray = cv.cvtColor(template_bgr, cv.COLOR_BGR2GRAY)
        h, w = template_gray.shape[:2]
        return template_gray, w, h

    def preprocess_image(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Preprocess screenshot before matching.
        For now: BGR -> Grayscale. You can extend with blur, CLAHE, etc. if needed.
        """
        try:
            gray = cv.cvtColor(img_bgr, cv.COLOR_BGR2GRAY)
            # Example optional pre-processing:
            # gray = cv.GaussianBlur(gray, (3, 3), 0)
            return gray
        except Exception as e:
            raise CustomException(e, sys) from e

    def _match_template(self, img_gray: np.ndarray) -> List[Dict[str, int]]:
        """
        Perform template matching on a grayscale image and return coordinates list.
        """
        result = cv.matchTemplate(img_gray, self.template_gray, cv.TM_CCOEFF_NORMED)
        ys, xs = np.where(result >= self.threshold)

        coords: List[Dict[str, int]] = []
        for x, y in zip(xs, ys):
            center_x = x + self.w // 2
            center_y = y + self.h // 2
            coords.append(
                {
                    "x": int(x),
                    "y": int(y),
                    "w": int(self.w),
                    "h": int(self.h),
                    "center_x": int(center_x),
                    "center_y": int(center_y),
                }
            )

        return coords

    # TODO - move to util / main 
    def _draw_debug_rectangles(self, img_bgr: np.ndarray, coords: List[Dict[str, int]]):
        """Draw rectangles around detected regions to visualize the detection."""
        for c in coords:
            x, y, w, h = c["x"], c["y"], c["w"], c["h"]
            cv.rectangle(img_bgr, (x, y), (x + w, y + h), self.draw_color, 2)

        cv.imshow("ObjectDetector Debug", img_bgr)
        cv.waitKey(1)

    def update(self, screenshot: np.ndarray) -> None:
        """
        Update the latest screenshot (BGR image from your WindowCapture).
        This is thread-safe.
        """
        try:
            with self.lock:
                self._screenshot = screenshot.copy()
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_coordinates(self) -> List[Dict[str, int]]:
        """
        Safely retrieve the latest detection results.
        Returns a shallow copy of the internal list to avoid race conditions.
        """
        try:
            with self.lock:
                return list(self._coords)
        except Exception as e:
            raise CustomException(e, sys) from e

    def start(self) -> None:
        """
        Start the detector thread. Safe to call once.
        """
        try:
            with self.lock:
                if not self.stopped:
                    logging.warning("ObjectDetector is already running.")
                    return
                self.stopped = False

            t = Thread(target=self.run, daemon=True)
            t.start()
            logging.info("ObjectDetector thread started.")
        except Exception as e:
            raise CustomException(e, sys) from e

    def stop(self) -> None:
        """
        Request the background thread to stop.
        """
        try:
            self.stopped = True
            logging.info("ObjectDetector stop requested.")
        except Exception as e:
            raise CustomException(e, sys) from e

    def run(self) -> None:
        """
        Background loop:
        - Takes latest screenshot (if any),
        - Preprocesses,
        - Runs template matching,
        - Updates latest coordinates.
        """
        try:
            while not self.stopped:
                local_img = None

                # Copy screenshot under lock, then release lock while processing
                with self.lock:
                    if self._screenshot is not None:
                        local_img = self._screenshot.copy()

                if local_img is not None:
                    try:
                        img_gray = self.preprocess_image(local_img)
                        coords = self._match_template(img_gray)

                        # if self.debug:
                        #     debug_img = local_img.copy()
                        #     self._draw_debug_rectangles(debug_img, coords)

                        # Save results
                        with self.lock:
                            self._coords = coords

                    except Exception as inner_e:
                        logging.error(f"Error during template matching: {inner_e}")

                time.sleep(self.sleep_interval)

        except Exception as e:
            raise CustomException(e, sys) from e
        finally:
            self.stopped = True
            logging.info("ObjectDetector thread finished.")
