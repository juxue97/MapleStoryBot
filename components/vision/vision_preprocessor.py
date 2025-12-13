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
            cv.resizeWindow(self.CONTROL_PANEL_WINDOW, 350, 600)

            # 0 = H, 1 = S, 2 = V, 3 = S+V mix
            self.create_trackbar("HSV Channel", 2, 3, self.filter_settings, "hsv_channel")

            self.create_trackbar("H_MIN", 0, 179, self.filter_settings, "h_min")
            self.create_trackbar("H_MAX", 179, 179, self.filter_settings, "h_max")

            self.create_trackbar("S_MIN", 147, 255, self.filter_settings, "s_min")
            self.create_trackbar("S_MAX", 255, 255, self.filter_settings, "s_max")

            self.create_trackbar("V_MIN", 190, 255, self.filter_settings, "v_min")
            self.create_trackbar("V_MAX", 255, 255, self.filter_settings, "v_max")

            self.create_trackbar("Brightness", 100, 100, self.filter_settings, "brightness")
            self.create_trackbar("Contrast", 100, 100, self.filter_settings, "contrast")

            # --- Blur (median) ---
            self.create_trackbar("Blur Kernel", 0, 15, self.filter_settings, "gaussian")

            # --- Threshold mode & value ---
            # Use Adaptive = 1 -> adaptiveThreshold
            # Use Adaptive = 0 -> global threshold with Thresh Min
            self.create_trackbar("Use Adaptive", 0, 1, self.filter_settings, "use_adaptive", is_bool=True)
            # Global threshold minimum (only used if Use Adaptive == 0)
            self.create_trackbar("Thresh Min", 0, 255, self.filter_settings, "thresh_min")

            # --- Morphology ---
            # Kernel size for OPEN/CLOSE ops
            self.create_trackbar("Kernel Size", 0, 15, self.filter_settings, "kernel_size")
            # Number of dilation iterations in the CLOSE step
            self.create_trackbar("Dilate Iter", 0, 10, self.filter_settings, "dilation_iterations")
            # Number of erosion iterations in the OPEN step
            self.create_trackbar("Erode Iter", 0, 10, self.filter_settings, "erosion_iterations")

            # --- ROI ---
            self.create_trackbar("ROI Enabled", 1, 1, self, "roi_enabled", is_bool=True)
            self.create_trackbar("ROI X", 498, 1920, self, "roi_x")
            self.create_trackbar("ROI Y", 257, 1080, self, "roi_y")
            self.create_trackbar("ROI W", 477, 1920, self, "roi_w")
            self.create_trackbar("ROI H", 123, 1080, self, "roi_h")

            logging.info("Vision control panel initialized (HSV + adaptive/global threshold).")

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
        """
        HSV + threshold preprocessing.

        Steps:
        1) Apply ROI
        2) Convert to HSV
        3) Apply HSV color range (H/S/V min/max) to build a mask
        4) Select an HSV channel (H / S / V / S+V) as gray base
        5) Apply mask to gray base
        6) Median blur + brightness/contrast + histogram equalization
        7) Threshold (adaptive or manual)
        8) Morphological open/close
        9) Return binary BGR image (0/255)
        """
        try:
            cfg = self.filter_settings

            if self.roi_enabled and self.roi_w > 0 and self.roi_h > 0:
                x1, y1 = self.roi_x, self.roi_y
                x2, y2 = x1 + self.roi_w, y1 + self.roi_h
                h, w = img.shape[:2]

                x1 = max(0, min(x1, w))
                x2 = max(0, min(x2, w))
                y1 = max(0, min(y1, h))
                y2 = max(0, min(y2, h))

                if x2 > x1 and y2 > y1:
                    img = img[y1:y2, x1:x2]

            hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
            h_ch, s_ch, v_ch = cv.split(hsv)

            h_min = int(np.clip(cfg.h_min, 0, 179))
            h_max = int(np.clip(cfg.h_max, 0, 179))
            s_min = int(np.clip(cfg.s_min, 0, 255))
            s_max = int(np.clip(cfg.s_max, 0, 255))
            v_min = int(np.clip(cfg.v_min, 0, 255))
            v_max = int(np.clip(cfg.v_max, 0, 255))

            lower = np.array([h_min, s_min, v_min], dtype=np.uint8)
            upper = np.array([h_max, s_max, v_max], dtype=np.uint8)

            hsv_mask = cv.inRange(hsv, lower, upper)

            mode = int(getattr(cfg, "hsv_channel", 2))  

            if mode == 0:
                base_gray = h_ch
            elif mode == 1:
                base_gray = s_ch
            elif mode == 2:
                base_gray = v_ch
            else:
                base_gray = cv.addWeighted(s_ch, 0.4, v_ch, 0.6, 0)

            gray = cv.bitwise_and(base_gray, base_gray, mask=hsv_mask)

            k = max(1, cfg.gaussian)
            if k % 2 == 0:
                k += 1 
            if k >= 3:
                gray = cv.medianBlur(gray, k)

            brightness = int(np.clip(cfg.brightness, 0, 100))
            alpha = 1.0 + (cfg.contrast / 50.0) 
            gray = cv.convertScaleAbs(gray, alpha=alpha, beta=brightness)

            gray = cv.equalizeHist(gray)

            if cfg.use_adaptive:
                mask = cv.adaptiveThreshold(
                    gray,
                    255,
                    cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv.THRESH_BINARY,
                    31,  
                    2
                )
            else:
                t_min = int(np.clip(cfg.thresh_min, 0, 255))
                _, mask = cv.threshold(gray, t_min, 255, cv.THRESH_BINARY)

            ksz = max(1, cfg.kernel_size)
            kernel = np.ones((ksz, ksz), np.uint8)

            mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel, iterations=max(1, cfg.erosion_iterations))
            mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=max(1, cfg.dilation_iterations))

            processed_bgr = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
            return processed_bgr

        except Exception as e:
            raise CustomException(e, sys) from e

    def detect_arrow_contours(self, processed_bgr: np.ndarray):
        """
        processed_bgr: output from process_frame (ROI, grayscale as 3-channel)
        Returns:
            boxes: list of (x, y, w, h) for each arrow, sorted left->right
            debug_img: copy of processed_bgr with rectangles drawn
        """
        try:
            gray = cv.cvtColor(processed_bgr, cv.COLOR_BGR2GRAY)

            edges = cv.Canny(gray, 50, 150)

            kernel = np.ones((3, 3), np.uint8)
            edges = cv.dilate(edges, kernel, iterations=1)

            contours, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

            boxes = []
            for cnt in contours:
                area = cv.contourArea(cnt)
                if area < 50: 
                    continue

                x, y, w, h = cv.boundingRect(cnt)

                aspect = w / float(h)
                if not (0.5 <= aspect <= 2.0):
                    continue
                if not (10 <= w <= 200 and 10 <= h <= 200):
                    continue

                boxes.append((x, y, w, h))

            boxes.sort(key=lambda b: b[0])

            debug_img = processed_bgr.copy()
            for idx, (x, y, w, h) in enumerate(boxes):
                cv.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 1)
                cv.putText(
                    debug_img,
                    str(idx + 1),
                    (x, y - 5),
                    cv.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 0),
                    1,
                )

            return boxes, debug_img

        except Exception as e:
            raise CustomException(e, sys) from e

    def start(self) -> None:
        try:
            self.stopped = False
            t = Thread(target=self._run, daemon=True)
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

    def _run(self) -> None:
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
