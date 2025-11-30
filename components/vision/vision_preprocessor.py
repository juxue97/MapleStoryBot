import sys
import time
from threading import Thread, Lock
from typing import Optional

import cv2 as cv
import numpy as np

from configs.filter_configs import FilterConfig
from exception import CustomException
from logger import logging


class VisionPreprocessor:
    CONTROL_PANEL_WINDOW: str = "Vision Control Panel"
    buffer_time: float = 0.1

    stopped: bool = True
    lock: Lock = None

    input_frame: Optional[np.ndarray] = None
    output_frame: Optional[np.ndarray] = None

    filter_settings: FilterConfig = None

    roi_enabled: bool = False
    roi_x: int = 0
    roi_y: int = 0
    roi_w: int = 0
    roi_h: int = 0

    def __init__(self) -> None:
        try:
            self.lock = Lock()
            self.filter_settings = FilterConfig()
        except Exception as e:
            raise CustomException(e, sys) from e

    def create_trackbar(self, name: str, init: int, maxv: int, target, field: str, is_bool: bool = False) -> None:
        try:
            def on_change(val: int, attr=field, tgt=target, flag=is_bool) -> None:
                val = bool(val) if flag else val
                setattr(tgt, attr, val)
                logging.debug(f"[trackbar] {attr} -> {val}")

            cv.createTrackbar(name, self.CONTROL_PANEL_WINDOW, init, maxv, on_change)
            on_change(init)

        except Exception as e:
            raise CustomException(e, sys) from e

    def init_control_panel(self) -> None:
        try:
            cv.namedWindow(self.CONTROL_PANEL_WINDOW, cv.WINDOW_NORMAL)
            cv.resizeWindow(self.CONTROL_PANEL_WINDOW, 350, 1200)

            # HSV
            self.create_trackbar("HMin", 0, 179, self.filter_settings, "hMin")
            self.create_trackbar("SMin", 0, 255, self.filter_settings, "sMin")
            self.create_trackbar("VMin", 0, 255, self.filter_settings, "vMin")
            self.create_trackbar("HMax", 179, 179, self.filter_settings, "hMax")
            self.create_trackbar("SMax", 255, 255, self.filter_settings, "sMax")
            self.create_trackbar("VMax", 50, 255, self.filter_settings, "vMax")

            # Processing
            self.create_trackbar("Gaussian Kernel XY", 3, 15, self.filter_settings, "gaussian")
            self.create_trackbar("Canny Low", 50, 500, self.filter_settings, "canny_low_threshold")
            self.create_trackbar("Canny High", 150, 500, self.filter_settings, "canny_high_threshold")
            self.create_trackbar("Kernel D", 3, 50, self.filter_settings, "kernelXY_d")
            self.create_trackbar("Kernel E", 3, 50, self.filter_settings, "kernelXY_e")
            self.create_trackbar("Dilate Iter", 1, 10, self.filter_settings, "dilation_iterations")
            self.create_trackbar("Erode Iter", 1, 10, self.filter_settings, "erosion_iterations")

            # ROI
            self.create_trackbar("ROI Enabled", 1, 1, self, "roi_enabled", is_bool=True)
            self.create_trackbar("ROI X", 695, 1920, self, "roi_x")
            self.create_trackbar("ROI Y", 152, 1080, self, "roi_y")
            self.create_trackbar("ROI W", 498, 1920, self, "roi_w")
            self.create_trackbar("ROI H", 123, 1080, self, "roi_h")

            # Grayscale threshold fallback
            self.create_trackbar("Use Grayscale Threshold", 0, 1, self.filter_settings, "use_grayscale", is_bool=True)
            self.create_trackbar("Brightness", 0, 100, self.filter_settings, "brightness")
            self.create_trackbar("Contrast", 30, 100, self.filter_settings, "contrast")
            self.create_trackbar("Thresh Min", 90, 255, self.filter_settings, "thresh_min")
            self.create_trackbar("Thresh Max", 255, 255, self.filter_settings, "thresh_max")

            logging.info("Vision control panel initialized.")

        except Exception as e:
            raise CustomException(e, sys) from e

    def set_roi(self, x: int, y: int, w: int, h: int, enabled: bool = True) -> None:
        try:
            self.roi_x, self.roi_y = x, y
            self.roi_w, self.roi_h = w, h
            self.roi_enabled = enabled
            logging.info(f"VisionPreprocessor ROI set: enabled={enabled}, x={x}, y={y}, w={w}, h={h}")
        except Exception as e:
            raise CustomException(e, sys) from e

    def set_input(self, frame: np.ndarray) -> None:
        try:
            with self.lock:
                self.input_frame = frame.copy()
        except Exception as e:
            raise CustomException(e, sys) from e

    def get_output(self) -> Optional[np.ndarray]:
        try:
            with self.lock:
                return None if self.output_frame is None else self.output_frame.copy()
        except Exception as e:
            raise CustomException(e, sys) from e

    def process_frame(self, img: np.ndarray) -> np.ndarray:
        cfg = self.filter_settings

        # Apply ROI
        if self.roi_enabled and self.roi_w > 0 and self.roi_h > 0:
            x1, y1 = self.roi_x, self.roi_y
            x2, y2 = x1 + self.roi_w, y1 + self.roi_h
            h, w = img.shape[:2]
            x1, x2 = max(0, min(x1, w)), max(0, min(x2, w))
            y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))
            if x2 > x1 and y2 > y1:
                img = img[y1:y2, x1:x2]

        # Choose processing path
        if getattr(cfg, "use_grayscale", False):
            gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            alpha = 1.0 + (cfg.contrast / 100.0)
            adjusted = cv.convertScaleAbs(gray, alpha=alpha, beta=cfg.brightness)
            mask = cv.inRange(adjusted, cfg.thresh_min, cfg.thresh_max)
            result = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
        else:
            hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
            lower = np.array([cfg.hMin, cfg.sMin, cfg.vMin])
            upper = np.array([cfg.hMax, cfg.sMax, cfg.vMax])
            mask = cv.inRange(hsv, lower, upper)
            result = cv.bitwise_and(hsv, hsv, mask=mask)

        # Blur
        k = max(1, cfg.gaussian)
        k += (k % 2 == 0)
        blurred = cv.GaussianBlur(result, (k, k), 0) if k > 1 else result

        # Edges
        edges = cv.Canny(blurred, cfg.canny_low_threshold, cfg.canny_high_threshold)

        # Morphology
        kernel_d = np.ones((cfg.kernelXY_d, cfg.kernelXY_d), np.uint8)
        kernel_e = np.ones((cfg.kernelXY_e, cfg.kernelXY_e), np.uint8)
        dilated = cv.dilate(edges, kernel_d, cfg.dilation_iterations)
        eroded = cv.erode(dilated, kernel_e, cfg.erosion_iterations)

        return eroded

    def start(self) -> None:
        try:
            self.stopped = False
            t = Thread(target=self.run, daemon=True)
            t.start()
            logging.info("VisionPreprocessor thread started.")
            time.sleep(self.buffer_time)
        except Exception as e:
            raise CustomException(e, sys) from e

    def stop(self) -> None:
        try:
            self.stopped = True
            logging.info("VisionPreprocessor thread stop requested.")
        except Exception as e:
            raise CustomException(e, sys) from e

    def run(self) -> None:
        try:
            while not self.stopped:
                frame_to_process: Optional[np.ndarray] = None
                with self.lock:
                    if self.input_frame is not None:
                        frame_to_process = self.input_frame.copy()
                if frame_to_process is not None:
                    processed = self.process_frame(frame_to_process)
                    with self.lock:
                        self.output_frame = processed
                time.sleep(0.01)
        except Exception as e:
            logging.error(f"VisionPreprocessor error: {e}")
            raise CustomException(e, sys) from e
