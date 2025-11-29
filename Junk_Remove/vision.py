import cv2 as cv
import numpy as np
from filter import Filter

class Filter:

    def __init__(self, Gaussian=None):
        self.Gaussian = Gaussian

class Vision:
    TRACKBAR_WINDOW = 'Trackbars'
    filter = None

    def __init__(self):
        #self.filter = Filter()
        pass

    def init_control_gui(self):
        cv.namedWindow(self.TRACKBAR_WINDOW)
        cv.resizeWindow(self.TRACKBAR_WINDOW,350,700)

        def nothing(position):
            pass

        # Create trackbars for adjusting the parameters
        cv.createTrackbar('HMin', self.TRACKBAR_WINDOW, 0, 179, nothing)
        cv.createTrackbar('SMin', self.TRACKBAR_WINDOW, 128, 255, nothing)
        cv.createTrackbar('VMin', self.TRACKBAR_WINDOW, 152, 255, nothing)
        
        cv.createTrackbar('HMax', self.TRACKBAR_WINDOW, 0, 179, nothing)
        cv.createTrackbar('SMax', self.TRACKBAR_WINDOW, 0, 255, nothing)
        cv.createTrackbar('VMax', self.TRACKBAR_WINDOW, 0, 255, nothing)        

        # Set default value for MAX HSV trackbars.
        cv.setTrackbarPos('HMax', self.TRACKBAR_WINDOW, 179)
        cv.setTrackbarPos('SMax', self.TRACKBAR_WINDOW, 255)
        cv.setTrackbarPos('VMax', self.TRACKBAR_WINDOW, 255)

        # image preprocessing
        cv.createTrackbar('Gaussian Kernel XY', self.TRACKBAR_WINDOW, 1, 15, nothing)

        cv.createTrackbar('Canny Low Threshold', self.TRACKBAR_WINDOW, 0, 500, nothing)
        cv.createTrackbar('Canny High Threshold', self.TRACKBAR_WINDOW, 0, 500, nothing)

        cv.createTrackbar('XY-kernel-d', self.TRACKBAR_WINDOW, 10, 50, nothing)
        cv.createTrackbar('XY-kernel-e', self.TRACKBAR_WINDOW, 10, 50, nothing)

        cv.createTrackbar('Dilation Iterations', self.TRACKBAR_WINDOW, 1, 10, nothing)
        cv.createTrackbar('Erosion Iterations', self.TRACKBAR_WINDOW, 1, 10, nothing)
    
    # returns filter based on the slider values
    def get_filter_from_controls(self):
        filter = Filter()
        filter.hMin = cv.getTrackbarPos('HMin', self.TRACKBAR_WINDOW)
        filter.sMin = cv.getTrackbarPos('SMin', self.TRACKBAR_WINDOW)
        filter.vMin = cv.getTrackbarPos('VMin', self.TRACKBAR_WINDOW)
        filter.hMax = cv.getTrackbarPos('HMax', self.TRACKBAR_WINDOW)
        filter.sMax = cv.getTrackbarPos('SMax', self.TRACKBAR_WINDOW)
        filter.vMax = cv.getTrackbarPos('VMax', self.TRACKBAR_WINDOW)

        filter.gaussian = cv.getTrackbarPos('Gaussian Kernel XY', self.TRACKBAR_WINDOW)

        filter.canny_low_threshold = cv.getTrackbarPos('Canny Low Threshold', self.TRACKBAR_WINDOW)
        filter.canny_high_threshold = cv.getTrackbarPos('Canny High Threshold', self.TRACKBAR_WINDOW)

        filter.kernelXY_d = cv.getTrackbarPos('XY-kernel-d', self.TRACKBAR_WINDOW)
        filter.kernelXY_e = cv.getTrackbarPos('XY-kernel-e', self.TRACKBAR_WINDOW)

        filter.dilation_iterations = cv.getTrackbarPos('Dilation Iterations', self.TRACKBAR_WINDOW)
        filter.erosion_iterations = cv.getTrackbarPos('Erosion Iterations', self.TRACKBAR_WINDOW)

        return filter

    def apply_filter(self,original_image):
        # Convert the image to grayscale
        if original_image is not None:
            #gray = cv.cvtColor(original_image, cv.COLOR_BGR2GRAY)
            hsv = cv.cvtColor(original_image, cv.COLOR_BGR2HSV)
        
            if not self.filter:
                filter = self.get_filter_from_controls()

            lower = np.array([filter.hMin, filter.sMin, filter.vMin])
            upper = np.array([filter.hMax, filter.sMax, filter.vMax])
            # Apply the thresholds
            mask = cv.inRange(hsv, lower, upper)
            result = cv.bitwise_and(hsv, hsv, mask=mask)          

            if filter.gaussian % 2 == 1:
                blurred = cv.GaussianBlur(result, (filter.gaussian, filter.gaussian), 0)

                # Perform edge detection on the image using the Canny edge detector
                edges = cv.Canny(blurred, filter.canny_low_threshold, filter.canny_high_threshold)

                # Perform morphological operations on the image to refine the edges of the arrows
                kernel_d = np.ones((filter.kernelXY_d, filter.kernelXY_d), np.uint8)
                dilated = cv.dilate(edges, kernel_d, filter.dilation_iterations)
                
                kernel_e = np.ones((filter.kernelXY_e, filter.kernelXY_e), np.uint8)
                eroded = cv.erode(dilated, kernel_e, filter.erosion_iterations)
                #blue_tinted_image = cv.merge([dilated, np.zeros_like(dilated), np.zeros_like(dilated)])

                return eroded
            else:
                return result
        else: 
            print("Screenshot Not Found.")
            return original_image

